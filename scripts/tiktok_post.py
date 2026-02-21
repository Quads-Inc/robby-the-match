#!/usr/bin/env python3
"""
TikTok自動投稿システム
- 生成済みコンテンツを自動的にTikTokに投稿
- 投稿キュー管理
- ffmpegでスライドショー動画生成
- tiktok-uploaderで自動投稿
- 結果をSlack通知

使い方:
  python3 tiktok_post.py --setup-auth     # 初回認証セットアップ
  python3 tiktok_post.py --post-next      # 次の投稿を実行
  python3 tiktok_post.py --status         # キュー状態確認
  python3 tiktok_post.py --init-queue     # キュー初期化（生成済みコンテンツから）
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).parent.parent
QUEUE_FILE = PROJECT_DIR / "data" / "posting_queue.json"
COOKIE_FILE = PROJECT_DIR / "data" / ".tiktok_cookies.txt"
CONTENT_DIR = PROJECT_DIR / "content" / "generated"
TEMP_DIR = PROJECT_DIR / "content" / "temp_videos"
ENV_FILE = PROJECT_DIR / ".env"


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


def find_content_sets():
    """生成済みコンテンツセットを検索"""
    content_sets = []

    for json_file in sorted(CONTENT_DIR.rglob("*.json")):
        if json_file.name == "batch_summary.md":
            continue
        # JSONと同名ディレクトリ（スライド画像）があるか確認
        slide_dir = json_file.parent / json_file.stem
        if slide_dir.is_dir() and list(slide_dir.glob("slide_*.png")):
            content_sets.append({
                "json_path": str(json_file),
                "slide_dir": str(slide_dir),
                "content_id": json_file.stem,
                "batch": json_file.parent.name
            })

    # A01/A02（ルートレベル）も追加
    for subdir in sorted(CONTENT_DIR.iterdir()):
        if subdir.is_dir() and list(subdir.glob("slide_*.png")):
            # 対応するJSONを探す
            json_candidates = [
                CONTENT_DIR / f"{subdir.name}.json",
                CONTENT_DIR / f"test_script_{subdir.name.split('_')[-1]}.json"
            ]
            json_path = None
            for j in json_candidates:
                if j.exists():
                    json_path = str(j)
                    break

            # 既に追加されていなければ追加
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
        "version": 1,
        "created": datetime.now().isoformat(),
        "updated": datetime.now().isoformat(),
        "posts": []
    }

    for i, cs in enumerate(content_sets):
        # JSONからキャプション・ハッシュタグを読む
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
            "status": "pending",  # pending → video_created → posted → failed
            "video_path": None,
            "posted_at": None,
            "tiktok_url": None,
            "error": None,
            "performance": {
                "views": None,
                "likes": None,
                "saves": None,
                "comments": None
            }
        })

    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)

    print(f"✅ 投稿キュー初期化完了: {len(queue['posts'])}件")
    for post in queue["posts"]:
        print(f"   #{post['id']}: {post['content_id']} ({post['batch']})")

    return queue


def load_queue():
    """キューを読み込む"""
    if not QUEUE_FILE.exists():
        print("キューファイルがありません。--init-queue で初期化してください。")
        return None
    with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_queue(queue):
    """キューを保存"""
    queue["updated"] = datetime.now().isoformat()
    with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)


def create_video_slideshow(slide_dir, output_path, duration_per_slide=3):
    """
    PNG スライドから動画スライドショーを生成（ffmpeg）

    各スライド3秒 × 6枚 = 18秒のMP4動画
    """
    slide_dir = Path(slide_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # スライド画像を確認
    slides = sorted(slide_dir.glob("slide_*.png"))
    if not slides:
        print(f"❌ スライド画像なし: {slide_dir}")
        return False

    print(f"   🎬 動画生成: {len(slides)}枚 × {duration_per_slide}秒")

    # ffmpegで動画生成
    # 各画像をduration秒表示、1080x1920（9:16縦型）にリサイズ
    # concat filterを使用
    filter_parts = []
    inputs = []

    for i, slide in enumerate(slides):
        inputs.extend(["-loop", "1", "-t", str(duration_per_slide), "-i", str(slide)])
        filter_parts.append(
            f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
            f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,"
            f"setsar=1[v{i}]"
        )

    # concat
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
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            print(f"❌ ffmpeg失敗: {result.stderr[-500:]}")
            return False

        file_size = output_path.stat().st_size / (1024 * 1024)
        print(f"   ✅ 動画生成完了: {output_path.name} ({file_size:.1f}MB)")
        return True

    except subprocess.TimeoutExpired:
        print("❌ ffmpegタイムアウト")
        return False
    except FileNotFoundError:
        print("❌ ffmpegがインストールされていません: brew install ffmpeg")
        return False


def upload_to_tiktok(video_path, caption, hashtags):
    """
    TikTokにアップロード

    方法1: tiktok-uploader（Selenium）
    方法2: TikTok Content Posting API（将来実装）
    """
    video_path = str(video_path)

    # ハッシュタグをキャプションに追加
    full_caption = caption
    if hashtags:
        tags = " ".join(hashtags)
        full_caption = f"{caption}\n\n{tags}"

    # キャプション2200文字制限
    if len(full_caption) > 2200:
        full_caption = full_caption[:2197] + "..."

    print(f"   📤 TikTokアップロード開始")
    print(f"   キャプション: {full_caption[:80]}...")

    # 方法1: tiktok-uploader
    if COOKIE_FILE.exists():
        try:
            from tiktok_uploader.upload import upload_video
            upload_video(
                filename=video_path,
                description=full_caption,
                cookies=str(COOKIE_FILE),
                headless=True
            )
            print(f"   ✅ TikTokアップロード完了")
            return True
        except Exception as e:
            print(f"   ⚠️ tiktok-uploader失敗: {e}")
            # フォールバックへ

    # 方法2: TikTok Content Posting API
    access_token = os.environ.get("TIKTOK_ACCESS_TOKEN")
    if access_token:
        try:
            return upload_via_api(video_path, full_caption, access_token)
        except Exception as e:
            print(f"   ⚠️ TikTok API失敗: {e}")

    # フォールバック: Slack通知で手動投稿依頼
    print("   📱 自動投稿不可 → Slack通知で手動投稿依頼")
    slack_notify(
        f"📱 TikTok投稿準備完了（手動アップロード必要）\n\n"
        f"動画: {video_path}\n"
        f"キャプション:\n{full_caption}\n\n"
        f"TikTokアプリから上記動画をアップロードしてください。"
    )
    return False


def upload_via_api(video_path, caption, access_token):
    """TikTok Content Posting API経由でアップロード"""
    import httpx

    # Step 1: Initialize upload
    init_url = "https://open.tiktokapis.com/v2/post/publish/video/init/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    file_size = Path(video_path).stat().st_size

    init_data = {
        "post_info": {
            "title": caption[:150],
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "disable_comment": False,
            "disable_duet": False,
            "disable_stitch": False
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": file_size,
            "chunk_size": file_size
        }
    }

    resp = httpx.post(init_url, headers=headers, json=init_data, timeout=30)
    if resp.status_code != 200:
        raise Exception(f"Init failed: {resp.text}")

    data = resp.json()
    upload_url = data["data"]["upload_url"]

    # Step 2: Upload video
    with open(video_path, "rb") as f:
        video_data = f.read()

    upload_headers = {
        "Content-Type": "video/mp4",
        "Content-Range": f"bytes 0-{file_size - 1}/{file_size}"
    }

    resp = httpx.put(upload_url, content=video_data, headers=upload_headers, timeout=120)
    if resp.status_code not in (200, 201):
        raise Exception(f"Upload failed: {resp.status_code}")

    print(f"   ✅ TikTok API アップロード完了")
    return True


def post_next():
    """キューから次の投稿を実行"""
    queue = load_queue()
    if not queue:
        return False

    # 次のpending投稿を取得
    next_post = None
    for post in queue["posts"]:
        if post["status"] == "pending":
            next_post = post
            break

    if not next_post:
        print("✅ 全投稿完了。キューに残りなし。")
        return True

    print(f"\n=== 投稿 #{next_post['id']}: {next_post['content_id']} ===")

    # Step 1: 動画生成
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    video_filename = f"tiktok_{next_post['content_id']}_{datetime.now().strftime('%Y%m%d')}.mp4"
    video_path = TEMP_DIR / video_filename

    if not video_path.exists():
        success = create_video_slideshow(
            next_post["slide_dir"],
            video_path,
            duration_per_slide=3
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
        video_path,
        next_post["caption"],
        next_post["hashtags"]
    )

    if success:
        next_post["status"] = "posted"
        next_post["posted_at"] = datetime.now().isoformat()
        save_queue(queue)

        # 成功通知
        pending_count = sum(1 for p in queue["posts"] if p["status"] == "pending")
        slack_notify(
            f"✅ TikTok投稿完了!\n"
            f"コンテンツ: {next_post['content_id']}\n"
            f"キャプション: {next_post['caption'][:80]}...\n"
            f"残りキュー: {pending_count}件"
        )
        print(f"\n✅ 投稿成功: {next_post['content_id']}")
    else:
        # Slack通知済み（手動投稿依頼）
        next_post["status"] = "manual_required"
        save_queue(queue)
        print(f"\n📱 手動投稿が必要: {next_post['content_id']}")

    return success


def setup_auth():
    """
    TikTok認証セットアップ

    ブラウザでTikTokにログイン→cookieを保存
    """
    print("=== TikTok認証セットアップ ===")
    print()

    # 方法1: ブラウザでcookie取得
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service

        print("Chromeを起動してTikTokのログインページを開きます...")
        print("ログイン後、このスクリプトに戻ってEnterを押してください。")
        print()

        options = Options()
        options.add_argument("--start-maximized")
        # Mac Chrome path
        options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

        driver = webdriver.Chrome(options=options)
        driver.get("https://www.tiktok.com/login")

        input("ログインが完了したらEnterを押してください...")

        # Cookie保存
        cookies = driver.get_cookies()
        COOKIE_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Netscape cookie format for tiktok-uploader
        with open(COOKIE_FILE, 'w') as f:
            f.write("# Netscape HTTP Cookie File\n")
            for cookie in cookies:
                secure = "TRUE" if cookie.get("secure", False) else "FALSE"
                expiry = str(int(cookie.get("expiry", 0)))
                http_only = "TRUE" if cookie.get("httpOnly", False) else "FALSE"
                domain = cookie.get("domain", "")
                if not domain.startswith("."):
                    domain = "." + domain
                f.write(f"{domain}\tTRUE\t{cookie['path']}\t{secure}\t{expiry}\t{cookie['name']}\t{cookie['value']}\n")

        print(f"✅ Cookie保存完了: {COOKIE_FILE}")
        driver.quit()

    except ImportError:
        print("Seleniumがインストールされていません。")
        print("pip3 install selenium を実行してください。")
    except Exception as e:
        print(f"❌ エラー: {e}")
        print()
        print("手動でcookieを設定する場合:")
        print(f"1. Chromeでhttps://www.tiktok.comにログイン")
        print(f"2. F12 → Application → Cookies → sessionid の値をコピー")
        print(f"3. 以下のコマンドを実行:")
        print(f'   echo "sessionid=YOUR_SESSION_ID" > {COOKIE_FILE}')


def show_status():
    """キュー状態を表示"""
    queue = load_queue()
    if not queue:
        return

    stats = {"pending": 0, "video_created": 0, "posted": 0,
             "manual_required": 0, "failed": 0}

    for post in queue["posts"]:
        stats[post["status"]] = stats.get(post["status"], 0) + 1

    print(f"=== 投稿キュー状態 ===")
    print(f"最終更新: {queue['updated']}")
    print(f"合計: {len(queue['posts'])}件")
    print(f"  待機中: {stats['pending']}")
    print(f"  動画生成済: {stats['video_created']}")
    print(f"  投稿完了: {stats['posted']}")
    print(f"  手動必要: {stats['manual_required']}")
    print(f"  失敗: {stats['failed']}")
    print()

    for post in queue["posts"]:
        status_emoji = {
            "pending": "⏳",
            "video_created": "🎬",
            "posted": "✅",
            "manual_required": "📱",
            "failed": "❌"
        }.get(post["status"], "❓")

        posted = f" ({post['posted_at'][:10]})" if post.get("posted_at") else ""
        print(f"  {status_emoji} #{post['id']}: {post['content_id']}{posted}")


def main():
    load_env()

    parser = argparse.ArgumentParser(description="TikTok自動投稿システム")
    parser.add_argument("--setup-auth", action="store_true",
                        help="TikTok認証セットアップ")
    parser.add_argument("--init-queue", action="store_true",
                        help="投稿キューを初期化")
    parser.add_argument("--post-next", action="store_true",
                        help="次の投稿を実行")
    parser.add_argument("--status", action="store_true",
                        help="キュー状態表示")

    args = parser.parse_args()

    if args.setup_auth:
        setup_auth()
    elif args.init_queue:
        init_queue()
    elif args.post_next:
        post_next()
    elif args.status:
        show_status()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
