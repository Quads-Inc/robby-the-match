#!/usr/bin/env python3
"""
TikTokカルーセル自動投稿 v1.0
Upload-Post.com API経由でTikTokにフォトカルーセルを投稿

使い方:
  python3 scripts/tiktok_carousel.py --post-next          # 次のready投稿をTikTokに投稿
  python3 scripts/tiktok_carousel.py --post-dir <dir>     # 指定ディレクトリのスライドを投稿
  python3 scripts/tiktok_carousel.py --schedule <dir> <datetime>  # スケジュール投稿
  python3 scripts/tiktok_carousel.py --status              # Upload-Post.comアカウント状態確認
  python3 scripts/tiktok_carousel.py --test                # API接続テスト

環境変数(.env):
  UPLOADPOST_API_KEY=your-api-key-here
  UPLOADPOST_USER=nurserobby           # Upload-Post.comで設定したプロフィール名
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import requests
except ImportError:
    print("requestsが必要です: pip install requests")
    sys.exit(1)

# ============================================================
# 定数
# ============================================================

PROJECT_DIR = Path(__file__).parent.parent
ENV_FILE = PROJECT_DIR / ".env"
READY_DIR = PROJECT_DIR / "content" / "ready"
QUEUE_FILE = PROJECT_DIR / "data" / "posting_queue.json"
POST_LOG = PROJECT_DIR / "data" / "tiktok_carousel_log.json"
LOG_DIR = PROJECT_DIR / "logs"

UPLOADPOST_BASE_URL = "https://api.upload-post.com/api"

# TikTokカルーセルは最低4枚必要
MIN_SLIDES = 4
MAX_SLIDES = 35


def load_env():
    """Load .env file"""
    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())


def get_api_key():
    return os.environ.get("UPLOADPOST_API_KEY", "")


def get_user():
    return os.environ.get("UPLOADPOST_USER", "nurserobby")


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


def log_event(event):
    """投稿ログ記録"""
    log_file = POST_LOG
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logs = []
    if log_file.exists():
        try:
            logs = json.loads(log_file.read_text(encoding='utf-8'))
        except Exception:
            logs = []

    event["timestamp"] = datetime.now().isoformat()
    logs.append(event)

    log_file.write_text(json.dumps(logs, ensure_ascii=False, indent=2), encoding='utf-8')


def log_daily(event_type, data):
    """日次イベントログ"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"tiktok_carousel_{datetime.now().strftime('%Y%m%d')}.log"
    entry = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "data": data,
    }
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ============================================================
# Upload-Post.com API
# ============================================================

def api_headers():
    return {"Authorization": f"Apikey {get_api_key()}"}


def test_api_connection():
    """API接続テスト"""
    api_key = get_api_key()
    if not api_key:
        print("UPLOADPOST_API_KEY が .env に設定されていません")
        return False

    try:
        # プロフィール一覧取得でAPIキーの有効性を確認
        r = requests.get(
            f"{UPLOADPOST_BASE_URL}/uploadposts/users",
            headers=api_headers(),
            timeout=15,
        )
        if r.status_code == 200:
            data = r.json()
            print(f"API接続OK")
            if isinstance(data, list):
                print(f"  登録プロフィール: {len(data)}件")
                for profile in data:
                    name = profile.get("username", profile.get("name", "?"))
                    platforms = profile.get("platforms", [])
                    print(f"    - {name} ({', '.join(platforms) if platforms else 'platforms不明'})")
            return True
        else:
            print(f"API接続失敗: HTTP {r.status_code}")
            print(f"  レスポンス: {r.text[:300]}")
            return False
    except requests.exceptions.ConnectionError:
        print("API接続失敗: サーバーに接続できません")
        return False
    except Exception as e:
        print(f"API接続失敗: {e}")
        return False


def post_carousel(slide_dir, caption, hashtags=None, scheduled_date=None):
    """
    Upload-Post.com APIでTikTokカルーセルを投稿

    Args:
        slide_dir: スライド画像があるディレクトリ (slide_1.png, slide_2.png, ...)
        caption: キャプションテキスト
        hashtags: ハッシュタグリスト (オプション)
        scheduled_date: ISO-8601形式のスケジュール日時 (オプション)

    Returns:
        dict: {"success": bool, "url": str or None, "error": str or None}
    """
    slide_dir = Path(slide_dir)
    api_key = get_api_key()

    if not api_key:
        return {"success": False, "url": None, "error": "UPLOADPOST_API_KEY未設定"}

    # スライド画像を収集
    slides = sorted(slide_dir.glob("slide_*.png"))
    if len(slides) < MIN_SLIDES:
        return {
            "success": False,
            "url": None,
            "error": f"スライド不足: {len(slides)}枚 (最低{MIN_SLIDES}枚必要)",
        }

    if len(slides) > MAX_SLIDES:
        slides = slides[:MAX_SLIDES]
        print(f"  [INFO] スライドを{MAX_SLIDES}枚に制限")

    # キャプション組み立て
    full_caption = caption or ""
    if hashtags:
        tag_str = " ".join(h if h.startswith("#") else f"#{h}" for h in hashtags)
        full_caption = f"{full_caption}\n\n{tag_str}"

    # TikTokキャプション上限チェック
    if len(full_caption) > 2200:
        full_caption = full_caption[:2197] + "..."

    print(f"  📸 {len(slides)}枚のスライドをアップロード中...")

    # multipartリクエスト構築
    files = []
    opened_files = []
    try:
        for slide in slides:
            f = open(slide, "rb")
            opened_files.append(f)
            files.append(("photos[]", (slide.name, f, "image/png")))

        data = {
            "user": get_user(),
            "title": full_caption,
            "platform[]": "tiktok",
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "auto_add_music": "true",
            "photo_cover_index": "0",
        }

        if scheduled_date:
            data["scheduled_date"] = scheduled_date
            data["timezone"] = "Asia/Tokyo"

        r = requests.post(
            f"{UPLOADPOST_BASE_URL}/upload_photos",
            headers=api_headers(),
            data=data,
            files=files,
            timeout=120,
        )

    finally:
        for f in opened_files:
            f.close()

    # レスポンス処理
    if r.status_code in (200, 201, 202):
        result = r.json()
        tiktok_result = result.get("results", {}).get("tiktok", {})
        url = tiktok_result.get("url")
        job_id = result.get("job_id")

        if result.get("success") or r.status_code == 202:
            status_msg = "スケジュール済み" if scheduled_date else "投稿完了"
            print(f"  ✅ TikTokカルーセル{status_msg}!")
            if url:
                print(f"  🔗 URL: {url}")
            if job_id:
                print(f"  📋 Job ID: {job_id}")

            return {
                "success": True,
                "url": url,
                "job_id": job_id,
                "error": None,
            }
        else:
            error_msg = result.get("error", result.get("message", "不明なエラー"))
            print(f"  ❌ 投稿失敗: {error_msg}")
            return {"success": False, "url": None, "error": str(error_msg)}
    else:
        error_text = r.text[:500]
        print(f"  ❌ API エラー: HTTP {r.status_code}")
        print(f"  レスポンス: {error_text}")
        return {"success": False, "url": None, "error": f"HTTP {r.status_code}: {error_text}"}


# ============================================================
# ready/ ディレクトリからの投稿
# ============================================================

def load_post_log():
    """投稿ログ読み込み"""
    if POST_LOG.exists():
        try:
            return json.loads(POST_LOG.read_text(encoding='utf-8'))
        except Exception:
            return []
    return []


def get_posted_dirs():
    """投稿済みディレクトリ名のセットを取得"""
    logs = load_post_log()
    return set(
        entry.get("dir_name", "")
        for entry in logs
        if entry.get("success") and entry.get("platform") == "tiktok"
    )


def find_next_ready():
    """次の未投稿readyディレクトリを取得"""
    if not READY_DIR.exists():
        return None

    posted = get_posted_dirs()
    for d in sorted(READY_DIR.iterdir()):
        if d.is_dir() and d.name not in posted:
            slides = list(d.glob("slide_*.png"))
            if len(slides) >= MIN_SLIDES:
                return d
    return None


def post_from_ready_dir(ready_dir):
    """readyディレクトリからカルーセル投稿"""
    ready_dir = Path(ready_dir)
    dir_name = ready_dir.name

    print(f"\n{'='*50}")
    print(f"TikTokカルーセル投稿: {dir_name}")
    print(f"{'='*50}")

    # キャプション読み込み
    caption = ""
    caption_file = ready_dir / "caption.txt"
    if caption_file.exists():
        caption = caption_file.read_text(encoding='utf-8').strip()

    # ハッシュタグ読み込み
    hashtags = []
    hashtag_file = ready_dir / "hashtags.txt"
    if hashtag_file.exists():
        tag_text = hashtag_file.read_text(encoding='utf-8').strip()
        hashtags = [t.strip() for t in tag_text.split() if t.strip()]

    # メタ情報
    meta = {}
    meta_file = ready_dir / "meta.json"
    if meta_file.exists():
        try:
            meta = json.loads(meta_file.read_text(encoding='utf-8'))
        except Exception:
            pass

    print(f"  キャプション: {caption[:80]}...")
    print(f"  ハッシュタグ: {' '.join(hashtags)}")

    # 投稿実行
    result = post_carousel(ready_dir, caption, hashtags)

    # ログ記録
    log_entry = {
        "dir_name": dir_name,
        "platform": "tiktok",
        "method": "upload-post-api",
        "success": result["success"],
        "url": result.get("url"),
        "job_id": result.get("job_id"),
        "error": result.get("error"),
        "caption": caption[:100],
        "slide_count": len(list(ready_dir.glob("slide_*.png"))),
        "meta": meta,
    }
    log_event(log_entry)
    log_daily("carousel_post", log_entry)

    # posting_queue.json も更新（対応するエントリがあれば）
    update_queue_status(dir_name, result)

    # Slack通知
    if result["success"]:
        url_str = f"\nURL: {result['url']}" if result.get("url") else ""
        slack_notify(
            f"✅ *TikTokカルーセル投稿完了*\n"
            f"コンテンツ: {dir_name}\n"
            f"キャプション: {caption[:80]}...{url_str}"
        )
    else:
        slack_notify(
            f"❌ *TikTokカルーセル投稿失敗*\n"
            f"コンテンツ: {dir_name}\n"
            f"エラー: {result.get('error', '不明')}"
        )

    return result


def update_queue_status(dir_name, result):
    """posting_queue.jsonの対応エントリを更新"""
    if not QUEUE_FILE.exists():
        return

    try:
        queue = json.loads(QUEUE_FILE.read_text(encoding='utf-8'))
        updated = False

        for post in queue.get("posts", []):
            # dir_nameからcontent_idを推測（YYYYMMDD_dayN → dayN）
            content_id = dir_name.split("_", 1)[1] if "_" in dir_name else dir_name
            if post.get("content_id") == content_id or dir_name in str(post.get("slide_dir", "")):
                if result["success"]:
                    post["status"] = "posted"
                    post["posted_at"] = datetime.now().isoformat()
                    post["verified"] = True
                    post["upload_method"] = "upload-post-api"
                    if result.get("url"):
                        post["tiktok_url"] = result["url"]
                else:
                    post["error"] = result.get("error", "carousel_upload_failed")
                updated = True
                break

        if updated:
            queue["updated"] = datetime.now().isoformat()
            QUEUE_FILE.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception as e:
        print(f"  [WARN] キュー更新失敗: {e}")


def post_next():
    """次の未投稿コンテンツをTikTokに投稿"""
    api_key = get_api_key()
    if not api_key:
        print("❌ UPLOADPOST_API_KEY が .env に設定されていません")
        print("")
        print("セットアップ手順:")
        print("  1. https://www.upload-post.com/ でアカウント作成")
        print("  2. TikTokアカウント(@robby15051)を接続")
        print("  3. APIキーを取得")
        print("  4. .env に UPLOADPOST_API_KEY=your-key を追加")
        print("  5. .env に UPLOADPOST_USER=your-profile-name を追加")
        return False

    ready_dir = find_next_ready()
    if not ready_dir:
        print("✅ 全コンテンツ投稿済み（未投稿のreadyなし）")
        return True

    result = post_from_ready_dir(ready_dir)
    return result["success"]


def show_status():
    """ステータス表示"""
    print(f"=== TikTokカルーセル投稿ステータス ===\n")

    # API接続確認
    api_key = get_api_key()
    print(f"API Key: {'設定済み' if api_key else '未設定'}")
    print(f"User: {get_user()}")
    print()

    # readyコンテンツ
    posted = get_posted_dirs()
    ready_dirs = sorted(READY_DIR.iterdir()) if READY_DIR.exists() else []
    ready_count = 0
    posted_count = 0

    print("content/ready/ ディレクトリ:")
    for d in ready_dirs:
        if d.is_dir():
            slides = list(d.glob("slide_*.png"))
            if d.name in posted:
                print(f"  ✅ {d.name} ({len(slides)}枚) — 投稿済み")
                posted_count += 1
            elif len(slides) >= MIN_SLIDES:
                print(f"  ⏳ {d.name} ({len(slides)}枚) — 未投稿")
                ready_count += 1
            else:
                print(f"  ⚠️ {d.name} ({len(slides)}枚) — スライド不足")

    print(f"\n投稿済み: {posted_count}件 / 未投稿: {ready_count}件")

    # 投稿ログ
    logs = load_post_log()
    tiktok_logs = [l for l in logs if l.get("platform") == "tiktok"]
    if tiktok_logs:
        print(f"\n最近のTikTok投稿:")
        for entry in tiktok_logs[-5:]:
            status = "✅" if entry.get("success") else "❌"
            ts = entry.get("timestamp", "?")[:16]
            print(f"  {status} {entry.get('dir_name', '?')} ({ts})")


# ============================================================
# メイン
# ============================================================

def main():
    load_env()

    parser = argparse.ArgumentParser(description="TikTokカルーセル自動投稿 v1.0")
    parser.add_argument("--post-next", action="store_true",
                        help="次の未投稿コンテンツをTikTokに投稿")
    parser.add_argument("--post-dir", type=str,
                        help="指定ディレクトリのスライドを投稿")
    parser.add_argument("--schedule", nargs=2, metavar=("DIR", "DATETIME"),
                        help="スケジュール投稿 (ISO-8601形式)")
    parser.add_argument("--status", action="store_true",
                        help="投稿ステータス表示")
    parser.add_argument("--test", action="store_true",
                        help="API接続テスト")

    args = parser.parse_args()

    if args.test:
        test_api_connection()
    elif args.status:
        show_status()
    elif args.post_next:
        post_next()
    elif args.post_dir:
        post_from_ready_dir(args.post_dir)
    elif args.schedule:
        dir_path, sched_dt = args.schedule
        dir_path = Path(dir_path)
        caption = ""
        hashtags = []
        caption_file = dir_path / "caption.txt"
        hashtag_file = dir_path / "hashtags.txt"
        if caption_file.exists():
            caption = caption_file.read_text(encoding='utf-8').strip()
        if hashtag_file.exists():
            hashtags = hashtag_file.read_text(encoding='utf-8').strip().split()
        result = post_carousel(dir_path, caption, hashtags, scheduled_date=sched_dt)
        if result["success"]:
            print(f"✅ スケジュール投稿設定完了: {sched_dt}")
        else:
            print(f"❌ スケジュール投稿失敗: {result.get('error')}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
