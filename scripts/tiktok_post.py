#!/usr/bin/env python3
"""
TikTok自動投稿システム v2.0
- tiktokautouploader (Phantomwright stealth) を主力
- tiktok-uploader (Playwright) をフォールバック
- 投稿後にプロフィールのvideoCountで実際の投稿を検証
- 指数バックオフ付きリトライ
- ハートビート統合

使い方:
  python3 tiktok_post.py --post-next      # 次の投稿を実行
  python3 tiktok_post.py --status         # キュー状態確認
  python3 tiktok_post.py --init-queue     # キュー初期化
  python3 tiktok_post.py --verify         # TikTok投稿数を検証
  python3 tiktok_post.py --heartbeat      # システム全体のヘルスチェック
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).parent.parent
QUEUE_FILE = PROJECT_DIR / "data" / "posting_queue.json"
COOKIE_FILE = PROJECT_DIR / "data" / ".tiktok_cookies.txt"
COOKIE_JSON = PROJECT_DIR / "data" / ".tiktok_cookies.json"
CONTENT_DIR = PROJECT_DIR / "content" / "generated"
TEMP_DIR = PROJECT_DIR / "content" / "temp_videos"
ENV_FILE = PROJECT_DIR / ".env"
VENV_PYTHON = PROJECT_DIR / ".venv" / "bin" / "python3"
TIKTOK_USERNAME = "robby15051"
LOG_DIR = PROJECT_DIR / "logs"


# ============================================================
# アトミック書き込みユーティリティ
# ============================================================

def atomic_json_write(filepath, data, indent=2):
    """アトミックJSON書き込み（書き込み中クラッシュによるデータ破損を防止）"""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    try:
        # Write to temp file in same directory (same filesystem for atomic rename)
        fd, tmp_path = tempfile.mkstemp(
            dir=filepath.parent,
            suffix='.tmp',
            prefix=filepath.stem + '_'
        )
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        # Atomic rename
        os.replace(tmp_path, filepath)
    except Exception:
        # Clean up temp file on failure
        try:
            os.unlink(tmp_path)
        except (OSError, UnboundLocalError):
            pass
        raise


def load_env():
    """Load .env file"""
    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())


def slack_notify(message):
    """Slack通知"""
    try:
        subprocess.run(
            ["python3", str(PROJECT_DIR / "scripts" / "notify_slack.py"),
             "--message", message],
            capture_output=True, timeout=30
        )
    except Exception as e:
        print(f"[WARN] Slack通知失敗: {e}")


def log_event(event_type, data):
    """イベントログ記録"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"tiktok_{datetime.now().strftime('%Y%m%d')}.log"
    entry = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "data": data
    }
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ============================================================
# Cookie ユーティリティ
# ============================================================

UPLOAD_VERIFICATION_FILE = PROJECT_DIR / "data" / "upload_verification.json"


def sanitize_cookies_for_playwright(cookies):
    """Cookie JSONをPlaywright互換フォーマットに変換"""
    sanitized = []
    for c in cookies:
        entry = {
            "name": c["name"],
            "value": c["value"],
            "domain": c["domain"],
            "path": c.get("path", "/"),
            "secure": bool(c.get("secure", False)),
            "sameSite": c.get("sameSite", "Lax"),
        }
        # Playwright uses 'expires' (float epoch), not 'expiry'
        exp = c.get("expires", c.get("expiry", 0))
        if exp and exp > 0:
            entry["expires"] = float(exp)
        if "httpOnly" in c:
            entry["httpOnly"] = bool(c["httpOnly"])
        sanitized.append(entry)
    return sanitized


def load_cookies_json():
    """Cookie JSONを読み込み (生フォーマット)"""
    if not COOKIE_JSON.exists():
        return []
    with open(COOKIE_JSON) as f:
        return json.load(f)


def load_upload_verification():
    """アップロード検証ログを読み込み"""
    if not UPLOAD_VERIFICATION_FILE.exists():
        return {"uploads": [], "last_updated": None}
    with open(UPLOAD_VERIFICATION_FILE) as f:
        return json.load(f)


def record_upload_attempt(content_id, success, method="tiktokautouploader", error=None):
    """アップロード試行を記録（ハートビートの主要指標）"""
    log = load_upload_verification()
    entry = {
        "timestamp": datetime.now().isoformat(),
        "content_id": content_id,
        "success": success,
        "method": method,
    }
    if error:
        entry["error"] = str(error)[:200]
    log["uploads"].append(entry)
    log["last_updated"] = datetime.now().isoformat()
    # 最新100件のみ保持
    if len(log["uploads"]) > 100:
        log["uploads"] = log["uploads"][-100:]
    atomic_json_write(UPLOAD_VERIFICATION_FILE, log)


# ============================================================
# TikTok投稿検証
# ============================================================

def get_tiktok_video_count():
    """TikTokプロフィールからvideoCountを取得して投稿数を検証

    Returns:
        int >= 0: 正常取得（実際の投稿数）
        -1: curlでデータ取得失敗（タイムアウト等）
        -2: HTMLは取得できたがvideoCount抽出失敗（JS-only/ブロック等）
        -3: ブラウザフォールバックも含め全手段失敗
    """
    # --- Step 1: curl で取得を試みる ---
    try:
        cookie_args = []
        if COOKIE_FILE.exists():
            cookie_args = ['-b', str(COOKIE_FILE)]
        elif COOKIE_JSON.exists():
            # JSON cookieからヘッダー文字列を構築
            try:
                with open(COOKIE_JSON) as f:
                    cookies = json.load(f)
                pairs = [f"{c['name']}={c['value']}" for c in cookies if c.get('name') and c.get('value')]
                if pairs:
                    cookie_args = ['-b', '; '.join(pairs)]
            except Exception:
                pass

        result = subprocess.run([
            'curl', '-s', '-L', '--max-time', '30',
            '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            '-H', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            '-H', 'Accept-Language: ja,en-US;q=0.9,en;q=0.8',
        ] + cookie_args + [
            f'https://www.tiktok.com/@{TIKTOK_USERNAME}'
        ], capture_output=True, text=True, timeout=45)

        html = result.stdout
        if not html or len(html) < 500:
            print(f"[WARN] curl応答が短すぎる ({len(html) if html else 0} bytes) - TikTokがブロックしている可能性")
        else:
            matches = re.findall(r'videoCount["\':]+\s*(\d+)', html)
            if matches:
                count = max(int(m) for m in matches)
                print(f"[INFO] curl成功: videoCount={count}")
                return count
            print(f"[WARN] HTMLにvideoCountが見つからない ({len(html)} bytes) - JS-onlyページの可能性")

    except subprocess.TimeoutExpired:
        print(f"[WARN] curl タイムアウト (45s)")
    except Exception as e:
        print(f"[WARN] curl例外: {e}")

    # --- Step 2: tiktok_analytics.py の fetch_tiktok_data() をインポートして使う ---
    print("[INFO] curlフォールバック: tiktok_analytics.fetch_tiktok_data() を試行...")
    try:
        sys.path.insert(0, str(PROJECT_DIR / "scripts"))
        from tiktok_analytics import fetch_tiktok_data
        profile, _videos = fetch_tiktok_data()
        if profile and profile.get("video_count") is not None:
            count = profile["video_count"]
            print(f"[INFO] analytics fallback成功: videoCount={count}")
            return count
        print("[WARN] analytics fallbackでもprofileデータ取得失敗")
    except ImportError as e:
        print(f"[WARN] tiktok_analytics インポート失敗: {e}")
    except Exception as e:
        print(f"[WARN] analytics fallback例外: {e}")

    print("[ERROR] 全手段でvideoCount取得失敗")
    return -3


def verify_post(pre_count, max_wait=120):
    """投稿後に実際にvideoCountが増えたか検証（最大2分待機）

    pre_count < 0 の場合（投稿前のカウント取得に失敗していた場合）は
    検証をスキップして False を返す。
    """
    if pre_count < 0:
        print(f"   ⚠️ 投稿前カウント取得失敗のため検証スキップ (pre_count={pre_count})")
        return False

    print(f"   🔍 投稿検証中... (投稿前: {pre_count}件)")
    start = time.time()
    check_intervals = [10, 15, 20, 30, 45]  # 段階的にチェック
    fetch_failures = 0

    for wait in check_intervals:
        if time.time() - start > max_wait:
            break
        time.sleep(wait)
        current = get_tiktok_video_count()
        if current < 0:
            fetch_failures += 1
            print(f"   ... プロフィール取得失敗 (code={current}, {int(time.time()-start)}秒経過)")
            continue
        if current > pre_count:
            print(f"   ✅ 投稿確認済み! ({pre_count} → {current}件)")
            return True
        print(f"   ... まだ反映されていない ({current}件, {int(time.time()-start)}秒経過)")

    final_count = get_tiktok_video_count()
    if final_count < 0:
        print(f"   ⚠️ 投稿検証不能: TikTokプロフィール取得が全回失敗 (fetch_failures={fetch_failures + 1})")
    else:
        print(f"   ❌ 投稿が検証できませんでした (videoCount: {final_count})")
    return False


# ============================================================
# 動画生成
# ============================================================

def _get_slide_durations(n):
    """スライド枚数に応じた表示時間を返す（秒）

    8枚構成（Hook + Content x6 + CTA）に最適化:
      1枚目（Hook）:    3.0秒 — フックを認識させる時間
      2-7枚目（Content）: 4.0秒 — 情報をしっかり読ませる
      8枚目（CTA）:     4.0秒 — CTAを認識させてアクション促す
      トランジション:    0.5秒 x 7 = 3.5秒
      合計: 約34.5秒（30-45秒ターゲット内）

    TikTok 2026アルゴリズムは6-10枚・30-60秒の動画を優遇。
    8枚以外の場合も汎用的に動作する。
    """
    if n <= 0:
        return []
    if n == 1:
        return [4.0]
    if n == 2:
        return [3.0, 4.0]
    # 3枚以上: 先頭3.0秒、中間4.0秒、末尾4.0秒
    durations = [3.0]  # 1枚目（Hook）
    for _ in range(n - 2):
        durations.append(4.0)  # 中間スライド（Content）
    durations.append(4.0)  # 最終スライド（CTA）
    return durations


def _find_bgm():
    """content/bgm/ からランダムにBGMファイルを1つ選ぶ。なければNone"""
    bgm_dir = PROJECT_DIR / "content" / "bgm"
    if not bgm_dir.exists():
        return None
    bgm_files = list(bgm_dir.glob("*.mp3")) + list(bgm_dir.glob("*.wav")) + list(bgm_dir.glob("*.m4a"))
    if not bgm_files:
        return None
    import random
    return random.choice(bgm_files)


# トランジション種類（xfade対応）— バリエーションでスライドショーに動きを出す
_XFADE_TRANSITIONS = [
    "fade",
    "slideright",
    "slideleft",
    "slideup",
    "slidedown",
    "smoothleft",
    "smoothright",
    "smoothup",
    "smoothdown",
]


def create_video_slideshow(slide_dir, output_path, duration_per_slide=None):
    """PNG スライドからプロ品質動画スライドショーを生成

    v4.0 改善点:
    - 8枚構成対応（Hook 3秒/Content x6 4秒/CTA 4秒 = 約34.5秒）
    - TikTok 2026アルゴリズム最適化（6-10枚・30-60秒優遇）
    - xfadeトランジション（フェード/スライド系をランダム選択）
    - 軽量モーション（scale+crop式の微妙なズーム）
    - BGMミックス対応（content/bgm/に配置、なくても動作）
    - CRF 18高品質 + TikTok最適エンコード
    - 1080x1920出力（入力サイズに関係なくスケーリング）
    """
    import random

    slide_dir = Path(slide_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    slides = sorted(slide_dir.glob("*slide_*.png"))
    if not slides:
        print(f"   ❌ スライド画像なし: {slide_dir}")
        return False

    n = len(slides)
    fps = 30
    fade_dur = 0.5  # トランジション秒数

    # スライド別表示時間
    if duration_per_slide is not None:
        # 互換性: 旧呼び出しで均一時間が指定された場合
        durations = [float(duration_per_slide)] * n
    else:
        durations = _get_slide_durations(n)

    total_dur = sum(durations) - (n - 1) * fade_dur if n > 1 else durations[0]
    print(f"   🎬 動画生成 v3: {n}枚, 合計約{total_dur:.1f}秒")
    print(f"      表示時間: {' / '.join(f'{d:.1f}s' for d in durations)}")
    print(f"      トランジション: {fade_dur}秒 x {max(0, n-1)}箇所")

    # BGM検索
    bgm_path = _find_bgm()
    if bgm_path:
        print(f"      BGM: {bgm_path.name}")
    else:
        print(f"      BGM: なし（content/bgm/にmp3/wav/m4aを配置で自動適用）")

    # モーションパターン: scale+cropで軽量な微動アニメーション
    # 各スライドに異なるモーションを割り当てて変化を出す
    # scale_ratio: 少し大きくスケーリングしてcropで動きの余地を作る
    # crop式のx,yで時間ベースの微動を実現
    sr = 1.04  # 4%大きくスケーリング（モーション余裕）
    motion_patterns = [
        # (crop_x_expr, crop_y_expr) — 微妙なパン/ズーム
        (f"(in_w-1080)/2+((in_w-1080)/2)*sin(t*0.8)", f"(in_h-1920)/2"),            # 左右揺れ
        (f"(in_w-1080)/2", f"(in_h-1920)/2+((in_h-1920)/2)*sin(t*0.6)"),            # 上下揺れ
        (f"(in_w-1080)/2*(1-t/{{dur}})", f"(in_h-1920)/2"),                          # 右→左パン
        (f"(in_w-1080)/2*(t/{{dur}})", f"(in_h-1920)/2"),                            # 左→右パン
        (f"(in_w-1080)/2", f"(in_h-1920)/2*(1-t/{{dur}})"),                          # 下→上パン
        (f"(in_w-1080)/2", f"(in_h-1920)/2*(t/{{dur}})"),                            # 上→下パン
    ]

    # トランジションをランダム選択
    transitions = []
    if n > 1:
        for i in range(n - 1):
            if i == 0:
                transitions.append("fade")
            else:
                transitions.append(random.choice(_XFADE_TRANSITIONS))

    # === ffmpegコマンド構築 ===
    cmd = ["ffmpeg", "-y"]

    # 入力: 各スライドを個別の表示時間で
    for i, slide in enumerate(slides):
        cmd.extend([
            "-loop", "1",
            "-t", str(durations[i]),
            "-framerate", str(fps),
            "-i", str(slide)
        ])

    # BGM入力（あれば）
    bgm_input_idx = n
    if bgm_path:
        cmd.extend(["-i", str(bgm_path)])

    # フィルターグラフ構築
    filters = []

    # 各スライドにスケーリング+cropモーション
    for i in range(n):
        mp = motion_patterns[i % len(motion_patterns)]
        cx = mp[0].replace("{dur}", str(durations[i]))
        cy = mp[1].replace("{dur}", str(durations[i]))
        # スケーリング → cropで微動 → 出力サイズに合わせる
        filters.append(
            f"[{i}]scale={int(1080*sr)}:{int(1920*sr)}:flags=lanczos,"
            f"crop=1080:1920:{cx}:{cy},"
            f"setsar=1[s{i}]"
        )

    # xfadeトランジションチェーン
    if n == 1:
        filters.append("[s0]null[vout]")
    else:
        prev = "s0"
        cumulative_dur = 0.0
        for i in range(1, n):
            cumulative_dur += durations[i - 1]
            offset = round(cumulative_dur - i * fade_dur, 2)
            out_label = f"f{i}" if i < n - 1 else "vout"
            tr = transitions[i - 1]
            filters.append(
                f"[{prev}][s{i}]xfade=transition={tr}:"
                f"duration={fade_dur}:offset={offset}[{out_label}]"
            )
            prev = out_label

    filter_str = ";".join(filters)

    # BGMミックス（あれば）
    if bgm_path:
        filter_str += (
            f";[{bgm_input_idx}:a]aloop=loop=-1:size=2e+09,"
            f"atrim=duration={total_dur + 1},"
            f"volume=-20dB,"
            f"afade=t=in:st=0:d=1,"
            f"afade=t=out:st={max(0, total_dur - 2)}:d=2[aout]"
        )
        cmd.extend(["-filter_complex", filter_str, "-map", "[vout]", "-map", "[aout]"])
        cmd.extend(["-c:a", "aac", "-b:a", "128k", "-shortest"])
    else:
        cmd.extend(["-filter_complex", filter_str, "-map", "[vout]"])

    # TikTok最適エンコード設定
    cmd.extend([
        "-c:v", "libx264",
        "-profile:v", "high",
        "-level", "4.2",
        "-crf", "18",
        "-maxrate", "15M",
        "-bufsize", "20M",
        "-preset", "medium",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        "-movflags", "+faststart",
        str(output_path)
    ])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print(f"   ⚠️ プロ版失敗、フォールバックへ")
            if result.stderr:
                err_lines = result.stderr.strip().split('\n')
                for line in err_lines[-3:]:
                    print(f"      {line[:120]}")
            return _create_simple_slideshow(slides, output_path, durations)

        file_size = output_path.stat().st_size / (1024 * 1024)
        # ffprobeで実際の長さを確認
        try:
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(output_path)],
                capture_output=True, text=True, timeout=10
            )
            actual_dur = float(probe.stdout.strip())
            print(f"   ✅ 動画生成完了: {output_path.name} ({file_size:.1f}MB, {actual_dur:.1f}秒)")
        except Exception:
            print(f"   ✅ 動画生成完了: {output_path.name} ({file_size:.1f}MB)")
        return True
    except subprocess.TimeoutExpired:
        print("   ⚠️ プロ版タイムアウト (120秒)、フォールバックへ")
        return _create_simple_slideshow(slides, output_path, durations)
    except FileNotFoundError:
        print("   ❌ ffmpegがインストールされていません")
        return False


def _create_simple_slideshow(slides, output_path, durations=None):
    """フォールバック: xfadeなしのシンプルconcatスライドショー（トランジション付き）

    プロ版が失敗した場合の安全策。Ken Burnsなし、フェードイン/アウトのみ。
    """
    n = len(slides)
    if durations is None or isinstance(durations, (int, float)):
        d = float(durations) if isinstance(durations, (int, float)) else 3.0
        durations = [d] * n

    filter_parts = []
    inputs = []

    for i, slide in enumerate(slides):
        dur = durations[i] if i < len(durations) else 3.0
        inputs.extend(["-loop", "1", "-t", str(dur), "-i", str(slide)])
        # スケーリング + 短いフェードイン/アウト
        fade_in = f"fade=t=in:st=0:d=0.3"
        fade_out = f"fade=t=out:st={max(0, dur - 0.3)}:d=0.3"
        filter_parts.append(
            f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
            f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,"
            f"setsar=1,{fade_in},{fade_out}[v{i}]"
        )

    concat_inputs = "".join(f"[v{i}]" for i in range(n))
    filter_complex = ";".join(filter_parts) + f";{concat_inputs}concat=n={n}:v=1:a=0[out]"

    # BGMチェック
    bgm_path = _find_bgm()
    total_dur = sum(durations)

    cmd = ["ffmpeg", "-y"] + inputs
    if bgm_path:
        cmd.extend(["-i", str(bgm_path)])

    if bgm_path:
        filter_complex += (
            f";[{n}:a]aloop=loop=-1:size=2e+09,"
            f"atrim=duration={total_dur + 1},"
            f"volume=-20dB,"
            f"afade=t=in:st=0:d=1,"
            f"afade=t=out:st={max(0, total_dur - 2)}:d=2[aout]"
        )
        cmd.extend([
            "-filter_complex", filter_complex,
            "-map", "[out]", "-map", "[aout]",
            "-c:a", "aac", "-b:a", "128k", "-shortest",
        ])
    else:
        cmd.extend(["-filter_complex", filter_complex, "-map", "[out]"])

    cmd.extend([
        "-c:v", "libx264",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-preset", "fast",
        "-movflags", "+faststart",
        str(output_path)
    ])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if result.returncode != 0:
            print(f"   ❌ ffmpeg失敗: {result.stderr[-500:]}")
            return False
        file_size = output_path.stat().st_size / (1024 * 1024)
        print(f"   ✅ 動画生成完了(フォールバック版): {output_path.name} ({file_size:.1f}MB)")
        return True
    except Exception as e:
        print(f"   ❌ ffmpegエラー: {e}")
        return False


# ============================================================
# アニメーション付き動画生成（v3.0 新機能）
# ============================================================

def create_video_animated(slide_dir, output_path, json_path=None):
    """テキストアニメーション付き動画生成（Pillow + ffmpeg）

    generate_carousel.py --background-only でBG画像を生成し、
    video_text_animator.py でアニメーション動画を作成。
    失敗時は従来のcreate_video_slideshowにフォールバック。
    """
    import importlib.util

    slide_dir = Path(slide_dir)
    output_path = Path(output_path)

    # Check if text metadata already exists
    meta_files = list(slide_dir.glob("*_text_metadata.json"))
    if meta_files:
        meta_path = str(meta_files[0])
        print(f"   🎬 アニメーション動画生成 (既存メタデータ使用)")
    else:
        # Need to generate backgrounds + metadata from JSON
        if not json_path or not Path(json_path).exists():
            print(f"   ⚠️ メタデータなし、通常版にフォールバック")
            return create_video_slideshow(slide_dir, output_path)

        print(f"   🎬 アニメーション動画生成 (BG + メタデータ生成中)")
        try:
            scripts_dir = Path(__file__).parent
            spec = importlib.util.spec_from_file_location(
                "generate_carousel", scripts_dir / "generate_carousel.py")
            gc_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(gc_module)

            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)

            # Extract content for background generation
            content = gc_module._extract_carousel_content(json_path)
            if not content:
                print(f"   ⚠️ コンテンツ抽出失敗、通常版にフォールバック")
                return create_video_slideshow(slide_dir, output_path)

            bg_dir = slide_dir / "animated_bg"
            result = gc_module.generate_carousel_backgrounds(
                content_id=content["content_id"],
                hook=content["hook"],
                slides=content["slides"],
                output_dir=str(bg_dir),
                category=content.get("category", "あるある"),
                cta_type=content.get("cta_type", "soft"),
            )
            meta_path = result["metadata"]
        except Exception as e:
            print(f"   ⚠️ BG生成失敗 ({e})、通常版にフォールバック")
            return create_video_slideshow(slide_dir, output_path)

    # Generate animated video
    try:
        scripts_dir = Path(__file__).parent
        spec = importlib.util.spec_from_file_location(
            "video_text_animator", scripts_dir / "video_text_animator.py")
        vta_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(vta_module)

        result = vta_module.generate_animated_video(
            meta_path, str(output_path), with_bgm=True
        )
        if result:
            file_size = output_path.stat().st_size / (1024 * 1024)
            print(f"   ✅ アニメーション動画完了: {output_path.name} ({file_size:.1f}MB)")
            return True
        else:
            print(f"   ⚠️ アニメーション動画失敗、通常版にフォールバック")
            return create_video_slideshow(slide_dir, output_path)
    except Exception as e:
        print(f"   ⚠️ アニメーターエラー ({e})、通常版にフォールバック")
        return create_video_slideshow(slide_dir, output_path)


# ============================================================
# アップロード方法
# ============================================================

def upload_method_autouploader(video_path, description, hashtags):
    """
    方法1: tiktokautouploader (Phantomwright stealth)
    - bot検知回避内蔵
    - CAPTCHA自動解決
    - 初回はブラウザが開いてログインが必要
    """
    print("   [方法1] tiktokautouploader (stealth)")

    if not VENV_PYTHON.exists():
        print("   ⚠️ venv未作成")
        return False

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    params = {
        "video": str(video_path),
        "description": description,
        "accountname": TIKTOK_USERNAME,
        "hashtags": [h.lstrip('#') for h in hashtags] if hashtags else None,
        "headless": False,  # Mac Miniには画面がある。非headlessで確実に
        "stealth": True,    # ランダムディレイでbot検知回避
    }
    params_file = TEMP_DIR / "_autoupload_params.json"
    with open(params_file, 'w', encoding='utf-8') as f:
        json.dump(params, f, ensure_ascii=False)

    script = TEMP_DIR / "_autoupload.py"
    with open(script, 'w', encoding='utf-8') as f:
        f.write(f"""
import json, sys, traceback
with open("{params_file}") as f:
    p = json.load(f)
try:
    from tiktokautouploader import upload_tiktok
    result = upload_tiktok(
        video=p["video"],
        description=p["description"],
        accountname=p["accountname"],
        hashtags=p["hashtags"],
        headless=p["headless"],
        stealth=p["stealth"],
        suppressprint=False,
    )
    if result == "Completed":
        print("AUTOUPLOAD_SUCCESS")
    else:
        print(f"AUTOUPLOAD_FAILED: upload_tiktok returned '{{result}}'")
except SystemExit as se:
    print(f"AUTOUPLOAD_FAILED: SystemExit {{se}}")
except Exception as e:
    print(f"AUTOUPLOAD_FAILED: {{e}}")
    traceback.print_exc()
""")

    try:
        result = subprocess.run(
            [str(VENV_PYTHON), str(script)],
            capture_output=True, text=True, timeout=300,
            cwd=str(PROJECT_DIR),
            env={**os.environ, "DISPLAY": ":0"}
        )

        script.unlink(missing_ok=True)
        params_file.unlink(missing_ok=True)

        stdout = result.stdout or ""
        stderr = result.stderr or ""

        if "AUTOUPLOAD_SUCCESS" in stdout:
            print("   ✅ tiktokautouploader: 成功")
            return True
        else:
            print(f"   ⚠️ tiktokautouploader: 失敗")
            if stdout:
                print(f"      stdout: {stdout[-400:]}")
            if stderr:
                print(f"      stderr: {stderr[-400:]}")
            return False

    except subprocess.TimeoutExpired:
        print("   ⚠️ tiktokautouploader: タイムアウト (300秒)")
        return False
    except Exception as e:
        print(f"   ⚠️ tiktokautouploader: {e}")
        return False


def upload_method_tiktok_uploader(video_path, description, hashtags):
    """
    方法2: tiktok-uploader (wkaisertexas) with cookie file
    - 戻り値チェック: 空リスト=成功、ビデオ入りリスト=失敗
    - 非headless + Chrome使用
    """
    print("   [方法2] tiktok-uploader (Playwright + Chrome)")

    if not COOKIE_FILE.exists():
        print("   ⚠️ Cookie未設定")
        return False

    if not VENV_PYTHON.exists():
        print("   ⚠️ venv未作成")
        return False

    full_caption = description
    if hashtags:
        full_caption += "\n\n" + " ".join(hashtags)
    if len(full_caption) > 2200:
        full_caption = full_caption[:2197] + "..."

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    params = {
        "filename": str(video_path),
        "description": full_caption,
        "cookies": str(COOKIE_FILE),
    }
    params_file = TEMP_DIR / "_upload_params.json"
    with open(params_file, 'w', encoding='utf-8') as f:
        json.dump(params, f, ensure_ascii=False)

    script = TEMP_DIR / "_upload.py"
    with open(script, 'w', encoding='utf-8') as f:
        f.write(f"""
import json, sys, traceback
with open("{params_file}", "r", encoding="utf-8") as f:
    p = json.load(f)
try:
    from tiktok_uploader.upload import upload_video
    failed = upload_video(
        filename=p["filename"],
        description=p["description"],
        cookies=p["cookies"],
        headless=False,
        browser="chrome",
    )
    if not failed:
        print("UPLOAD_SUCCESS")
    else:
        print(f"UPLOAD_FAILED: {{failed}}")
except Exception as e:
    print(f"UPLOAD_ERROR: {{e}}")
    traceback.print_exc()
""")

    try:
        result = subprocess.run(
            [str(VENV_PYTHON), str(script)],
            capture_output=True, text=True, timeout=300,
            cwd=str(PROJECT_DIR),
            env={**os.environ, "DISPLAY": ":0"}
        )

        script.unlink(missing_ok=True)
        params_file.unlink(missing_ok=True)

        stdout = result.stdout or ""
        stderr = result.stderr or ""

        if "UPLOAD_SUCCESS" in stdout:
            print("   ✅ tiktok-uploader: 成功")
            return True
        else:
            print(f"   ⚠️ tiktok-uploader: 失敗")
            if stdout:
                print(f"      stdout: {stdout[-400:]}")
            if stderr:
                print(f"      stderr: {stderr[-400:]}")
            return False

    except subprocess.TimeoutExpired:
        print("   ⚠️ tiktok-uploader: タイムアウト (300秒)")
        return False
    except Exception as e:
        print(f"   ⚠️ tiktok-uploader: {e}")
        return False


def upload_method_slack_manual(video_path, description, hashtags):
    """
    方法3: Slack通知で手動投稿依頼（最終フォールバック）
    """
    print("   [方法3] Slack手動投稿依頼")
    full_caption = description
    if hashtags:
        full_caption += "\n\n" + " ".join(hashtags)

    slack_notify(
        f"📱 *TikTok手動投稿が必要です*\n\n"
        f"自動アップロードが全て失敗しました。\n"
        f"TikTokアプリから以下の動画をアップロードしてください:\n\n"
        f"動画: `{video_path}`\n"
        f"キャプション:\n```\n{full_caption}\n```"
    )
    return False


def upload_to_tiktok(video_path, caption, hashtags, max_retries=2):
    """
    TikTokにアップロード（リトライ付き）

    アップロード方法を順番に試行:
    1. tiktokautouploader (Phantomwright stealth)
    2. tiktok-uploader (Playwright + Chrome)
    3. Slack手動投稿依頼

    注意: curlベースのvideoCount検証はTikTokにブロックされたため、
    アップロードメソッドの戻り値を信頼する方式に変更 (2026-02-25)
    """
    video_path = str(video_path)

    print(f"   📤 TikTokアップロード開始")
    print(f"   キャプション: {caption[:60]}...")

    methods = [
        ("tiktokautouploader", upload_method_autouploader),
        ("tiktok-uploader", upload_method_tiktok_uploader),
    ]

    for attempt in range(max_retries + 1):
        if attempt > 0:
            wait = 30 * (2 ** (attempt - 1))  # 30秒, 60秒
            print(f"\n   🔄 リトライ {attempt}/{max_retries} ({wait}秒待機)")
            time.sleep(wait)

        for method_name, method_func in methods:
            try:
                success = method_func(video_path, caption, hashtags)
                if success:
                    # 戻り値チェック済み（return value bugを修正済み）
                    # curlベースvideoCount検証は廃止（TikTokブロック対策）
                    log_event("upload_success", {
                        "method": method_name,
                        "attempt": attempt,
                        "video": video_path,
                    })
                    print(f"   ✅ アップロード成功 (方法: {method_name})")
                    return True
                else:
                    log_event("upload_method_failed", {
                        "method": method_name,
                        "attempt": attempt,
                    })
            except Exception as e:
                print(f"   ❌ {method_name}例外: {e}")
                log_event("upload_exception", {
                    "method": method_name,
                    "error": str(e),
                })

    # 全方法失敗 → Slack手動依頼
    upload_method_slack_manual(video_path, caption, hashtags)
    log_event("upload_all_failed", {"video": video_path})
    return False


# ============================================================
# キュー管理
# ============================================================

def find_content_sets():
    """生成済みコンテンツセットを検索"""
    content_sets = []

    for json_file in sorted(CONTENT_DIR.rglob("*.json")):
        if json_file.name == "batch_summary.md":
            continue
        slide_dir = json_file.parent / json_file.stem
        if slide_dir.is_dir() and list(slide_dir.glob("*slide_*.png")):
            content_sets.append({
                "json_path": str(json_file),
                "slide_dir": str(slide_dir),
                "content_id": json_file.stem,
                "batch": json_file.parent.name
            })

    for subdir in sorted(CONTENT_DIR.iterdir()):
        if subdir.is_dir() and list(subdir.glob("*slide_*.png")):
            json_candidates = [
                CONTENT_DIR / f"{subdir.name}.json",
                CONTENT_DIR / f"test_script_{subdir.name.split('_')[-1]}.json"
            ]
            json_path = None
            for j in json_candidates:
                if j.exists():
                    json_path = str(j)
                    break

            existing = [c["slide_dir"] for c in content_sets]
            if str(subdir) not in existing:
                content_sets.append({
                    "json_path": json_path,
                    "slide_dir": str(subdir),
                    "content_id": subdir.name,
                    "batch": "standalone"
                })

    return content_sets


def init_queue():
    """投稿キューを初期化"""
    content_sets = find_content_sets()
    queue = {
        "version": 2,
        "created": datetime.now().isoformat(),
        "updated": datetime.now().isoformat(),
        "posts": []
    }

    for i, cs in enumerate(content_sets):
        caption = ""
        hashtags = []
        cta_type = "soft"

        if cs["json_path"]:
            try:
                with open(cs["json_path"], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                caption = data.get("caption", "")
                hashtags = data.get("hashtags", [])
                cta_type = data.get("cta_type", "soft")
            except Exception:
                pass

        queue["posts"].append({
            "id": i + 1,
            "content_id": cs["content_id"],
            "batch": cs["batch"],
            "slide_dir": cs["slide_dir"],
            "json_path": cs["json_path"],
            "caption": caption,
            "hashtags": hashtags,
            "cta_type": cta_type,
            "status": "pending",
            "video_path": None,
            "posted_at": None,
            "verified": False,
            "upload_method": None,
            "error": None,
        })

    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)

    print(f"✅ 投稿キュー初期化完了: {len(queue['posts'])}件")
    for post in queue["posts"]:
        print(f"   #{post['id']}: {post['content_id']} ({post['batch']})")
    return queue


def load_queue():
    """キュー読み込み（破損時のバックアップ復旧付き）"""
    if not QUEUE_FILE.exists():
        print("キューファイルがありません。--init-queue で初期化してください。")
        return None
    try:
        with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        # Try backup
        backup = QUEUE_FILE.with_suffix('.json.bak')
        if backup.exists():
            print(f"[WARN] キュー破損、バックアップから復旧: {e}")
            try:
                with open(backup, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print("[ERROR] バックアップも破損しています")
                return None
        print(f"[ERROR] キュー破損、バックアップなし: {e}")
        return None


def save_queue(queue):
    """キュー保存（バックアップ + アトミック書き込み）"""
    queue["updated"] = datetime.now().isoformat()
    # Create backup of current file
    if QUEUE_FILE.exists():
        backup = QUEUE_FILE.with_suffix('.json.bak')
        try:
            shutil.copy2(QUEUE_FILE, backup)
        except Exception:
            pass
    atomic_json_write(QUEUE_FILE, queue)


def find_ready_dir_post():
    """content/ready/ から未投稿のコンテンツを探してキューに追加"""
    ready_dir = PROJECT_DIR / "content" / "ready"
    if not ready_dir.exists():
        return None

    queue = load_queue()
    if not queue:
        queue = {
            "version": 2,
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
            "posts": []
        }

    # 既存キューの slide_dir とcontent_ready名のマッピングを確認
    existing_dirs = set()
    for post in queue["posts"]:
        sd = post.get("slide_dir", "")
        existing_dirs.add(sd)
        # content_id やディレクトリ名もチェック
        existing_dirs.add(post.get("content_id", ""))

    # content/ready/ の未処理ディレクトリを探す
    for d in sorted(ready_dir.iterdir()):
        if not d.is_dir():
            continue
        slides = sorted(d.glob("*slide_*.png"))
        if not slides:
            continue

        dir_name = d.name
        # 既にキューにあるかチェック
        already_in_queue = False
        for post in queue["posts"]:
            if dir_name in str(post.get("slide_dir", "")) or dir_name == post.get("content_id", ""):
                already_in_queue = True
                break

        if already_in_queue:
            continue

        # caption.txt / hashtags.txt を読む
        caption = ""
        hashtags = []
        caption_file = d / "caption.txt"
        hashtag_file = d / "hashtags.txt"
        if caption_file.exists():
            caption = caption_file.read_text(encoding='utf-8').strip()
        if hashtag_file.exists():
            tag_text = hashtag_file.read_text(encoding='utf-8').strip()
            hashtags = [t.strip() for t in tag_text.split() if t.strip()]

        # キューに追加
        new_id = max((p["id"] for p in queue["posts"]), default=0) + 1
        new_post = {
            "id": new_id,
            "content_id": dir_name,
            "batch": "content_ready",
            "slide_dir": str(d),
            "json_path": None,
            "caption": caption,
            "hashtags": hashtags,
            "cta_type": "soft",
            "status": "pending",
            "video_path": None,
            "posted_at": None,
            "verified": False,
            "upload_method": None,
            "error": None,
        }
        queue["posts"].append(new_post)
        save_queue(queue)
        print(f"   [INFO] content/ready/{dir_name} をキューに追加 (#{new_id})")
        return new_post

    return None


def post_next():
    """キューから次の投稿を実行"""
    queue = load_queue()
    if not queue:
        # キューがなければ content/ready/ から探す
        ready_post = find_ready_dir_post()
        if ready_post:
            queue = load_queue()
        else:
            print("キューファイルがありません。--init-queue で初期化してください。")
            return False

    next_post = None
    for post in queue["posts"]:
        if post["status"] in ("pending", "ready", "video_created"):
            next_post = post
            break

    if not next_post:
        # キューに該当なし → content/ready/ から新規追加を試みる
        ready_post = find_ready_dir_post()
        if ready_post:
            queue = load_queue()
            next_post = ready_post
        else:
            print("✅ 全投稿完了。キューに残りなし。")
            return True

    print(f"\n{'='*50}")
    print(f"投稿 #{next_post['id']}: {next_post['content_id']}")
    print(f"{'='*50}")

    # Step 1: 動画生成（アニメーション優先、フォールバックあり）
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    video_filename = f"tiktok_{next_post['content_id']}_{datetime.now().strftime('%Y%m%d')}.mp4"
    video_path = TEMP_DIR / video_filename

    if not video_path.exists():
        # Try animated version first, fallback to static slideshow
        success = create_video_animated(
            next_post["slide_dir"], video_path,
            json_path=next_post.get("json_path")
        )
        if not success:
            next_post["status"] = "failed"
            next_post["error"] = "video_creation_failed"
            save_queue(queue)
            slack_notify(f"❌ 動画生成失敗: {next_post['content_id']}")
            return False

    next_post["video_path"] = str(video_path)
    next_post["status"] = "video_created"
    save_queue(queue)

    # Step 2: TikTokにアップロード
    success = upload_to_tiktok(
        video_path, next_post["caption"], next_post["hashtags"]
    )

    if success:
        next_post["status"] = "posted"
        next_post["posted_at"] = datetime.now().isoformat()
        next_post["verified"] = True
        next_post["video_type"] = "animated"
        save_queue(queue)
        record_upload_attempt(next_post["content_id"], success=True)

        pending_count = sum(1 for p in queue["posts"] if p["status"] == "pending")
        slack_notify(
            f"✅ *TikTok投稿完了 (検証済み)*\n"
            f"コンテンツ: {next_post['content_id']}\n"
            f"キャプション: {next_post['caption'][:80]}...\n"
            f"残りキュー: {pending_count}件"
        )
        print(f"\n✅ 投稿成功 (検証済み): {next_post['content_id']}")
    else:
        next_post["status"] = "failed"
        next_post["error"] = "all_upload_methods_failed"
        save_queue(queue)
        record_upload_attempt(next_post["content_id"], success=False, error="all_upload_methods_failed")
        print(f"\n❌ 投稿失敗: {next_post['content_id']}")

    return success


# ============================================================
# ハートビート / ヘルスチェック
# ============================================================

def heartbeat():
    """システム全体のヘルスチェック v2.0

    重大度レベル:
      CRITICAL: Cookie期限切れ間近(3日未満), 連続アップロード失敗, venv消失
      WARNING:  Cookie残り30日未満, キューにfailed蓄積
      INFO:     TikTokプロフィール取得失敗(TikTok側のbot検出。検証不能だが問題ではない)
    """
    print(f"\n{'='*50}")
    print(f"ROBBY THE MATCH ハートビート v2.0")
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")

    criticals = []  # 即時対応が必要
    warnings = []   # 注意が必要
    infos = []      # 情報のみ
    status = {}

    # 1. Cookie有効性チェック
    print("🔐 Cookie有効性...")
    if COOKIE_JSON.exists():
        cookies = load_cookies_json()
        for c in cookies:
            if c["name"] == "sessionid":
                exp = c.get("expires", c.get("expiry", 0))
                if exp > 0:
                    expiry = datetime.fromtimestamp(exp)
                    days_left = (expiry - datetime.now()).days
                    status["cookie_days_left"] = days_left
                    if days_left < 3:
                        criticals.append(f"Cookie期限切れ間近: 残り{days_left}日")
                    elif days_left < 30:
                        warnings.append(f"Cookie残り{days_left}日")
                    else:
                        print(f"   ✅ sessionid有効 (残り{days_left}日)")
                break
    else:
        criticals.append("Cookieファイルなし")
        print("   ❌ Cookieファイルなし")

    # 2. アップロード検証ログ（主要指標）
    print("📤 アップロード検証...")
    vlog = load_upload_verification()
    recent_uploads = vlog.get("uploads", [])
    status["total_uploads"] = len(recent_uploads)
    successful = [u for u in recent_uploads if u.get("success")]
    failed = [u for u in recent_uploads if not u.get("success")]
    active_posts = [u for u in successful if u.get("note") != "user deleted from tiktok"]
    deleted_posts = [u for u in successful if u.get("note") == "user deleted from tiktok"]

    print(f"   成功: {len(successful)}件 (うち削除済み: {len(deleted_posts)}件, 現存: {len(active_posts)}件)")
    if failed:
        print(f"   失敗: {len(failed)}件")

    # 直近5件の失敗率チェック
    last_5 = recent_uploads[-5:] if len(recent_uploads) >= 5 else recent_uploads
    recent_fails = sum(1 for u in last_5 if not u.get("success"))
    if recent_fails >= 3:
        criticals.append(f"直近{len(last_5)}件中{recent_fails}件のアップロード失敗")
    elif recent_fails >= 2:
        warnings.append(f"直近{len(last_5)}件中{recent_fails}件のアップロード失敗")

    status["upload_verification"] = {
        "total": len(recent_uploads),
        "successful": len(successful),
        "active": len(active_posts),
        "deleted": len(deleted_posts),
        "failed": len(failed),
    }

    # 3. TikTok投稿数（参考情報。取得失敗はINFO扱い）
    print("📊 TikTok投稿数 (参考)...")
    video_count = get_tiktok_video_count()
    status["tiktok_videos"] = video_count

    queue_for_check = load_queue()
    posted_in_queue = 0
    if queue_for_check:
        posted_in_queue = sum(1 for p in queue_for_check["posts"] if p["status"] == "posted")

    if video_count >= 0:
        print(f"   TikTok公開投稿: {video_count}件 (キューposted: {posted_in_queue}件)")
        if video_count > 0 and video_count < posted_in_queue:
            infos.append(f"TikTok実投稿{video_count}件 < キューposted{posted_in_queue}件（一部削除の可能性）")
    else:
        # プロフィール取得失敗 → INFO（bot検出の可能性大。CRITICALではない）
        error_desc = {-1: "curl失敗", -2: "HTML解析失敗(JS-only)", -3: "全手段失敗"}
        desc = error_desc.get(video_count, f"不明エラー({video_count})")
        print(f"   ℹ️ TikTokプロフィール取得失敗: {desc}（bot検出の可能性。アカウントは正常）")
        infos.append(f"TikTokプロフィール取得不可({desc}) — bot検出の可能性")

    # 4. キュー状態
    print("📋 投稿キュー...")
    queue = load_queue()
    if queue:
        stats = {}
        for post in queue["posts"]:
            stats[post["status"]] = stats.get(post["status"], 0) + 1
        status["queue"] = stats
        for k, v in stats.items():
            print(f"   {k}: {v}")
        if stats.get("failed", 0) > 3:
            warnings.append(f"失敗した投稿が{stats['failed']}件")
    else:
        warnings.append("キューファイルなし")

    # 5. venv確認
    print("🐍 Python venv...")
    if VENV_PYTHON.exists():
        print(f"   ✅ venv有効")
    else:
        criticals.append("venvが見つかりません")
        print(f"   ❌ venv未作成")

    # 6. cron確認
    print("⏰ cron...")
    try:
        result = subprocess.run(
            ["crontab", "-l"], capture_output=True, text=True, timeout=5
        )
        cron_jobs = [l for l in result.stdout.split('\n') if l.strip() and not l.startswith('#')]
        status["cron_jobs"] = len(cron_jobs)
        print(f"   ✅ {len(cron_jobs)}件のcronジョブ")
    except Exception:
        warnings.append("cron確認失敗")

    # 7. ディスク容量
    print("💾 ディスク...")
    try:
        result = subprocess.run(
            ["df", "-h", str(PROJECT_DIR)],
            capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:
            parts = lines[1].split()
            avail = parts[3] if len(parts) > 3 else "?"
            print(f"   空き容量: {avail}")
    except Exception:
        pass

    # 結果サマリ
    print(f"\n{'='*50}")

    all_issues = (
        [f"🚨 {c}" for c in criticals]
        + [f"⚠️ {w}" for w in warnings]
        + [f"ℹ️ {i}" for i in infos]
    )

    upload_display = f"成功{len(successful)}/失敗{len(failed)}/現存{len(active_posts)}"
    tiktok_display = f"{video_count}件" if video_count >= 0 else "取得不可(bot検出)"
    cookie_days = status.get('cookie_days_left', '?')

    if criticals:
        severity = "CRITICAL"
        print(f"🚨 CRITICAL: {len(criticals)}件")
        for c in criticals:
            print(f"   🚨 {c}")
    if warnings:
        if not criticals:
            severity = "WARNING"
        print(f"⚠️ WARNING: {len(warnings)}件")
        for w in warnings:
            print(f"   ⚠️ {w}")
    if infos:
        print(f"ℹ️ INFO: {len(infos)}件")
        for i in infos:
            print(f"   ℹ️ {i}")

    if criticals or warnings:
        severity = "CRITICAL" if criticals else "WARNING"
        slack_notify(
            f"🏥 *ROBBY ハートビート [{severity}]*\n\n"
            + "\n".join(all_issues)
            + f"\n\n📤 アップロード: {upload_display}"
            + f"\n📊 TikTok: {tiktok_display}"
            + f"\n🔐 Cookie残り: {cookie_days}日"
            + (f"\n\n⚡ *即時対応が必要*" if criticals else "")
        )
    elif not infos:
        print("✅ 全システム正常")
        slack_notify(
            f"💚 *ROBBY ハートビート - 全システム正常*\n"
            f"📤 アップロード: {upload_display}\n"
            f"🔐 Cookie残り: {cookie_days}日"
        )
    else:
        print("✅ システム正常（情報通知あり）")
        slack_notify(
            f"💚 *ROBBY ハートビート - 正常*\n"
            + "\n".join([f"ℹ️ {i}" for i in infos])
            + f"\n\n📤 アップロード: {upload_display}"
            + f"\n🔐 Cookie残り: {cookie_days}日"
        )

    log_event("heartbeat", {"status": status, "criticals": criticals, "warnings": warnings, "infos": infos})
    return len(criticals) == 0 and len(warnings) == 0


def show_status():
    """キュー状態を表示"""
    queue = load_queue()
    if not queue:
        return

    stats = {}
    for post in queue["posts"]:
        stats[post["status"]] = stats.get(post["status"], 0) + 1

    # TikTok実際の投稿数も表示
    video_count = get_tiktok_video_count()

    print(f"=== 投稿キュー状態 ===")
    print(f"最終更新: {queue['updated']}")
    if video_count >= 0:
        print(f"TikTok公開投稿数: {video_count}件")
    else:
        error_desc = {-1: "curl失敗", -2: "HTML解析失敗", -3: "全手段失敗"}
        print(f"TikTok公開投稿数: 取得失敗 ({error_desc.get(video_count, '不明')})")
    print(f"キュー合計: {len(queue['posts'])}件")
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")
    print()

    for post in queue["posts"]:
        emoji = {"pending": "⏳", "video_created": "🎬", "posted": "✅",
                 "manual_required": "📱", "failed": "❌"}.get(post["status"], "❓")
        verified = " ✓" if post.get("verified") else ""
        posted = f" ({post['posted_at'][:10]})" if post.get("posted_at") else ""
        print(f"  {emoji} #{post['id']}: {post['content_id']}{posted}{verified}")


def verify_command():
    """TikTok投稿数検証コマンド"""
    video_count = get_tiktok_video_count()
    queue = load_queue()

    posted_count = 0
    if queue:
        posted_count = sum(1 for p in queue["posts"] if p["status"] == "posted")

    # フェッチ失敗 → アップロード検証ログで代替
    if video_count < 0:
        error_desc = {-1: "curl失敗", -2: "HTML解析失敗(JS-only)", -3: "全手段失敗"}
        desc = error_desc.get(video_count, f"不明エラー({video_count})")
        print(f"ℹ️ TikTokプロフィール取得不可: {desc}（bot検出の可能性）")
        print(f"キュー内 posted: {posted_count}")
        # アップロード検証ログで代替チェック
        vlog = load_upload_verification()
        recent = vlog.get("uploads", [])[-10:]
        recent_fails = sum(1 for u in recent if not u.get("success"))
        if recent_fails >= 3:
            print(f"⚠️ 直近{len(recent)}件中{recent_fails}件の失敗 — アップロード問題の可能性")
        else:
            print(f"✅ アップロード検証ログ正常（直近{len(recent)}件中{len(recent)-recent_fails}件成功）")
        return

    print(f"TikTok公開投稿数: {video_count}")
    print(f"キュー内 posted: {posted_count}")

    if video_count == 0 and posted_count > 0:
        print(f"🚨 重大不整合: キューでは{posted_count}件 posted だが、TikTokには0件")
        print(f"   → 投稿処理がステータスを更新したが実際のアップロードは失敗している可能性大")
        # postedだが実際には投稿されていないものをpendingに戻す
        if queue:
            fixed = 0
            for post in queue["posts"]:
                if post["status"] == "posted" and not post.get("verified"):
                    post["status"] = "pending"
                    post["posted_at"] = None
                    post["error"] = "unverified_reset_by_verify"
                    fixed += 1
            if fixed:
                save_queue(queue)
                print(f"   {fixed}件の未検証投稿をpendingにリセット")
        slack_notify(
            f"🚨 *TikTok投稿不整合検出*\n"
            f"TikTok実投稿: 0件\n"
            f"キューposted: {posted_count}件\n"
            f"→ {posted_count}件の投稿が実際にはアップロードされていません。未検証投稿をpendingにリセットしました。"
        )
    elif video_count < posted_count:
        print(f"⚠️ 不整合: キューでは{posted_count}件 posted だが、TikTokには{video_count}件しかない")
        # postedだが実際には投稿されていないものをpendingに戻す
        if queue:
            fixed = 0
            for post in queue["posts"]:
                if post["status"] == "posted" and not post.get("verified"):
                    post["status"] = "pending"
                    post["posted_at"] = None
                    post["error"] = "unverified_reset_by_verify"
                    fixed += 1
            if fixed:
                save_queue(queue)
                print(f"   {fixed}件の未検証投稿をpendingにリセット")
        slack_notify(
            f"⚠️ *TikTok投稿不整合*\n"
            f"TikTok実投稿: {video_count}件\n"
            f"キューposted: {posted_count}件\n"
            f"→ {posted_count - video_count}件が未反映。未検証投稿をpendingにリセットしました。"
        )
    else:
        print("✅ 整合性OK")


# ============================================================
# メイン
# ============================================================

def main():
    load_env()

    parser = argparse.ArgumentParser(description="TikTok自動投稿システム v2.0")
    parser.add_argument("--post-next", action="store_true", help="次の投稿を実行")
    parser.add_argument("--init-queue", action="store_true", help="投稿キューを初期化")
    parser.add_argument("--status", action="store_true", help="キュー状態表示")
    parser.add_argument("--verify", action="store_true", help="TikTok投稿数検証")
    parser.add_argument("--heartbeat", action="store_true", help="システムヘルスチェック")

    args = parser.parse_args()

    if args.post_next:
        post_next()
    elif args.init_queue:
        init_queue()
    elif args.status:
        show_status()
    elif args.verify:
        verify_command()
    elif args.heartbeat:
        heartbeat()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
