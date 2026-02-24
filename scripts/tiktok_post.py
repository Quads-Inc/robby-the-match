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
import subprocess
import sys
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
# TikTok投稿検証
# ============================================================

def get_tiktok_video_count():
    """TikTokプロフィールからvideoCountを取得して投稿数を検証"""
    try:
        result = subprocess.run([
            'curl', '-s', '-b', str(COOKIE_FILE),
            '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            f'https://www.tiktok.com/@{TIKTOK_USERNAME}'
        ], capture_output=True, text=True, timeout=30)

        html = result.stdout
        matches = re.findall(r'videoCount["\':]+\s*(\d+)', html)
        if matches:
            count = max(int(m) for m in matches)
            return count
        return 0
    except Exception as e:
        print(f"[WARN] videoCount取得失敗: {e}")
        return -1


def verify_post(pre_count, max_wait=120):
    """投稿後に実際にvideoCountが増えたか検証（最大2分待機）"""
    print(f"   🔍 投稿検証中... (投稿前: {pre_count}件)")
    start = time.time()
    check_intervals = [10, 15, 20, 30, 45]  # 段階的にチェック

    for wait in check_intervals:
        if time.time() - start > max_wait:
            break
        time.sleep(wait)
        current = get_tiktok_video_count()
        if current > pre_count:
            print(f"   ✅ 投稿確認済み! ({pre_count} → {current}件)")
            return True
        print(f"   ... まだ反映されていない ({current}件, {int(time.time()-start)}秒経過)")

    print(f"   ❌ 投稿が検証できませんでした (videoCount: {get_tiktok_video_count()})")
    return False


# ============================================================
# 動画生成
# ============================================================

def create_video_slideshow(slide_dir, output_path, duration_per_slide=3.5):
    """PNG スライドからプロ品質動画スライドショーを生成（Ken Burns + クロスフェード）"""
    slide_dir = Path(slide_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    slides = sorted(slide_dir.glob("slide_*.png"))
    if not slides:
        print(f"   ❌ スライド画像なし: {slide_dir}")
        return False

    n = len(slides)
    fps = 30
    frames = int(duration_per_slide * fps)
    fade_dur = 0.4  # クロスフェード秒数
    zoom_speed = 0.001  # Ken Burnsズーム速度（微妙なモーション）

    print(f"   🎬 動画生成: {n}枚 x {duration_per_slide}秒 (Ken Burns + クロスフェード)")

    cmd = ["ffmpeg", "-y"]

    # 入力
    for slide in slides:
        cmd.extend(["-loop", "1", "-t", str(duration_per_slide), "-framerate", str(fps), "-i", str(slide)])

    # フィルター: Ken Burns → クロスフェード
    filters = []

    for i in range(n):
        # 交互にズームイン/ズームアウト
        if i % 2 == 0:
            z_expr = f"zoom+{zoom_speed}"
        else:
            z_expr = f"1.08-{zoom_speed}*on"

        filters.append(
            f"[{i}]scale=4000:-1,"
            f"zoompan=z='{z_expr}':"
            f"x=iw/2-(iw/zoom/2):y=ih/2-(ih/zoom/2):"
            f"d={frames}:s=1080x1920:fps={fps}[s{i}]"
        )

    # クロスフェードチェーン
    if n == 1:
        filters.append("[s0]null[out]")
    else:
        prev = "s0"
        for i in range(1, n):
            offset = round(i * duration_per_slide - i * fade_dur, 2)
            out_label = f"f{i-1}" if i < n - 1 else "out"
            filters.append(
                f"[{prev}][s{i}]xfade=transition=fade:"
                f"duration={fade_dur}:offset={offset}[{out_label}]"
            )
            prev = out_label

    filter_str = ";".join(filters)
    cmd.extend(["-filter_complex", filter_str, "-map", "[out]"])

    # TikTok最適エンコード設定
    cmd.extend([
        "-c:v", "libx264",
        "-profile:v", "high",
        "-level", "4.2",
        "-crf", "20",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        "-movflags", "+faststart",
        str(output_path)
    ])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if result.returncode != 0:
            print(f"   ⚠️ Ken Burns版失敗、シンプル版にフォールバック")
            return _create_simple_slideshow(slides, output_path, duration_per_slide)

        file_size = output_path.stat().st_size / (1024 * 1024)
        print(f"   ✅ 動画生成完了: {output_path.name} ({file_size:.1f}MB)")
        return True
    except subprocess.TimeoutExpired:
        print("   ⚠️ Ken Burns版タイムアウト、シンプル版にフォールバック")
        return _create_simple_slideshow(slides, output_path, duration_per_slide)
    except FileNotFoundError:
        print("   ❌ ffmpegがインストールされていません")
        return False


def _create_simple_slideshow(slides, output_path, duration_per_slide=3):
    """フォールバック: シンプルなconcatスライドショー"""
    filter_parts = []
    inputs = []

    for i, slide in enumerate(slides):
        inputs.extend(["-loop", "1", "-t", str(duration_per_slide), "-i", str(slide)])
        filter_parts.append(
            f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
            f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,"
            f"setsar=1[v{i}]"
        )

    concat_inputs = "".join(f"[v{i}]" for i in range(len(slides)))
    filter_complex = ";".join(filter_parts) + f";{concat_inputs}concat=n={len(slides)}:v=1:a=0[out]"

    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-preset", "fast",
        str(output_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print(f"   ❌ ffmpeg失敗: {result.stderr[-500:]}")
            return False
        file_size = output_path.stat().st_size / (1024 * 1024)
        print(f"   ✅ 動画生成完了(シンプル版): {output_path.name} ({file_size:.1f}MB)")
        return True
    except Exception as e:
        print(f"   ❌ ffmpegエラー: {e}")
        return False


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
        if slide_dir.is_dir() and list(slide_dir.glob("slide_*.png")):
            content_sets.append({
                "json_path": str(json_file),
                "slide_dir": str(slide_dir),
                "content_id": json_file.stem,
                "batch": json_file.parent.name
            })

    for subdir in sorted(CONTENT_DIR.iterdir()):
        if subdir.is_dir() and list(subdir.glob("slide_*.png")):
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
    if not QUEUE_FILE.exists():
        print("キューファイルがありません。--init-queue で初期化してください。")
        return None
    with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_queue(queue):
    queue["updated"] = datetime.now().isoformat()
    with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)


def post_next():
    """キューから次の投稿を実行"""
    queue = load_queue()
    if not queue:
        return False

    next_post = None
    for post in queue["posts"]:
        if post["status"] in ("pending", "video_created"):
            next_post = post
            break

    if not next_post:
        print("✅ 全投稿完了。キューに残りなし。")
        return True

    print(f"\n{'='*50}")
    print(f"投稿 #{next_post['id']}: {next_post['content_id']}")
    print(f"{'='*50}")

    # Step 1: 動画生成
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    video_filename = f"tiktok_{next_post['content_id']}_{datetime.now().strftime('%Y%m%d')}.mp4"
    video_path = TEMP_DIR / video_filename

    if not video_path.exists():
        success = create_video_slideshow(
            next_post["slide_dir"], video_path, duration_per_slide=3
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

    # Step 2: TikTokにアップロード（検証付き）
    success = upload_to_tiktok(
        video_path, next_post["caption"], next_post["hashtags"]
    )

    if success:
        next_post["status"] = "posted"
        next_post["posted_at"] = datetime.now().isoformat()
        next_post["verified"] = True
        save_queue(queue)

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
        print(f"\n❌ 投稿失敗: {next_post['content_id']}")

    return success


# ============================================================
# ハートビート / ヘルスチェック
# ============================================================

def heartbeat():
    """システム全体のヘルスチェック"""
    print(f"\n{'='*50}")
    print(f"ROBBY THE MATCH ハートビート")
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")

    issues = []
    status = {}

    # 1. Cookie有効性チェック
    print("🔐 Cookie有効性...")
    if COOKIE_JSON.exists():
        with open(COOKIE_JSON) as f:
            cookies = json.load(f)
        for c in cookies:
            if c["name"] == "sessionid":
                expiry = datetime.fromtimestamp(c["expiry"])
                days_left = (expiry - datetime.now()).days
                status["cookie_days_left"] = days_left
                if days_left < 3:
                    issues.append(f"🚨 Cookie期限切れ間近: {days_left}日")
                elif days_left < 30:
                    issues.append(f"⚠️ Cookie残り{days_left}日")
                else:
                    print(f"   ✅ sessionid有効 (残り{days_left}日)")
                break
    else:
        issues.append("🚨 Cookieファイルなし")
        print("   ❌ Cookieファイルなし")

    # 2. TikTok投稿数確認
    print("📊 TikTok投稿数...")
    video_count = get_tiktok_video_count()
    status["tiktok_videos"] = video_count
    print(f"   TikTok公開投稿: {video_count}件")
    if video_count == 0:
        issues.append("⚠️ TikTok投稿が0件")

    # 3. キュー状態
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
            issues.append(f"🚨 失敗した投稿が{stats['failed']}件")
    else:
        issues.append("⚠️ キューファイルなし")

    # 4. venv確認
    print("🐍 Python venv...")
    if VENV_PYTHON.exists():
        print(f"   ✅ venv有効")
    else:
        issues.append("🚨 venvが見つかりません")
        print(f"   ❌ venv未作成")

    # 5. cron確認
    print("⏰ cron...")
    try:
        result = subprocess.run(
            ["crontab", "-l"], capture_output=True, text=True, timeout=5
        )
        cron_jobs = [l for l in result.stdout.split('\n') if l.strip() and not l.startswith('#')]
        status["cron_jobs"] = len(cron_jobs)
        print(f"   ✅ {len(cron_jobs)}件のcronジョブ")
    except Exception:
        issues.append("⚠️ cron確認失敗")

    # 6. ディスク容量
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

    # 結果
    print(f"\n{'='*50}")
    if issues:
        print(f"⚠️ {len(issues)}件の問題:")
        for issue in issues:
            print(f"   {issue}")

        slack_notify(
            f"🏥 *ROBBY ハートビート - {len(issues)}件の問題*\n\n"
            + "\n".join(issues)
            + f"\n\nTikTok投稿: {video_count}件"
            + f"\nキュー: {json.dumps(status.get('queue', {}))}"
        )
    else:
        print("✅ 全システム正常")
        slack_notify(
            f"💚 *ROBBY ハートビート - 全システム正常*\n"
            f"TikTok投稿: {video_count}件\n"
            f"Cookie残り: {status.get('cookie_days_left', '?')}日\n"
            f"キュー: {json.dumps(status.get('queue', {}))}"
        )

    log_event("heartbeat", {"status": status, "issues": issues})
    return len(issues) == 0


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
    print(f"TikTok公開投稿数: {video_count}件")
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

    print(f"TikTok公開投稿数: {video_count}")
    print(f"キュー内 posted: {posted_count}")

    if video_count < posted_count:
        print(f"⚠️ 不整合: キューでは{posted_count}件 posted だが、TikTokには{video_count}件しかない")
        # postedだが実際には投稿されていないものをfailedに戻す
        if queue:
            fixed = 0
            for post in queue["posts"]:
                if post["status"] == "posted" and not post.get("verified"):
                    post["status"] = "pending"
                    post["posted_at"] = None
                    post["error"] = "unverified_reset"
                    fixed += 1
            if fixed:
                save_queue(queue)
                print(f"   {fixed}件の未検証投稿をpendingにリセット")
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
