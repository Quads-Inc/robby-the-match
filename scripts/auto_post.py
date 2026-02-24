#!/usr/bin/env python3
"""
auto_post.py — ナースロビー SNS自動投稿エンジン v1.0

Instagram/TikTokへのカルーセル自動投稿を行う。
cron駆動で完全自動化。

使い方:
  # 次の1件をInstagramに投稿
  python3 scripts/auto_post.py --instagram

  # 次の1件をTikTokに投稿（カルーセル画像をSlackに送信、手動アップ待ち）
  python3 scripts/auto_post.py --tiktok

  # Instagram + TikTok両方
  python3 scripts/auto_post.py --all

  # 投稿ステータス確認
  python3 scripts/auto_post.py --status

  # day5を再投稿（失敗リトライ）
  python3 scripts/auto_post.py --retry

  # ドライラン（投稿せず確認のみ）
  python3 scripts/auto_post.py --instagram --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ============================================================
# Constants
# ============================================================

PROJECT_DIR = Path(__file__).parent.parent
QUEUE_FILE = PROJECT_DIR / "data" / "posting_queue.json"
READY_DIR = PROJECT_DIR / "content" / "ready"
TEMP_DIR = PROJECT_DIR / "content" / "temp_instagram"
SESSION_FILE = PROJECT_DIR / "data" / ".instagram_session.json"
POST_LOG_FILE = PROJECT_DIR / "data" / "post_log.json"
ENV_FILE = PROJECT_DIR / ".env"

# Posting intervals (seconds) to avoid rate limiting
POST_INTERVAL = 60  # Between posts on same platform
PLATFORM_INTERVAL = 30  # Between different platforms


# ============================================================
# Utilities
# ============================================================

def load_env():
    """Load .env file."""
    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())


def slack_notify(message: str):
    """Send Slack notification."""
    try:
        subprocess.run(
            ["python3", str(PROJECT_DIR / "scripts" / "notify_slack.py"),
             "--message", message],
            capture_output=True, timeout=30
        )
    except Exception as e:
        print(f"[WARN] Slack notify failed: {e}")


def load_post_log() -> List[Dict]:
    """Load post log."""
    if POST_LOG_FILE.exists():
        with open(POST_LOG_FILE) as f:
            return json.load(f)
    return []


def save_post_log(log: List[Dict]):
    """Save post log."""
    with open(POST_LOG_FILE, "w") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)


def get_ready_dirs() -> List[Path]:
    """Get all content/ready/ directories sorted by name."""
    if not READY_DIR.exists():
        return []
    return sorted([d for d in READY_DIR.iterdir() if d.is_dir()])


def get_next_unposted(platform: str) -> Optional[Path]:
    """Get next unposted content directory for given platform."""
    log = load_post_log()
    posted_dirs = {
        entry["dir"]
        for entry in log
        if entry.get("platform") == platform and entry.get("status") == "success"
    }

    for d in get_ready_dirs():
        if d.name not in posted_dirs:
            return d
    return None


# ============================================================
# Instagram Posting
# ============================================================

def instagram_login():
    """Login to Instagram, reusing session if available."""
    from instagrapi import Client

    cl = Client()
    cl.delay_range = [2, 5]

    # Try loading existing session
    if SESSION_FILE.exists():
        try:
            cl.load_settings(str(SESSION_FILE))
            cl.login(
                os.environ.get("INSTAGRAM_USERNAME", "robby.for.nurse"),
                os.environ.get("INSTAGRAM_PASSWORD", "")
            )
            print(f"[IG] Session loaded. User: {cl.username}")
            return cl
        except Exception as e:
            print(f"[IG] Session expired, re-logging in: {e}")

    # Fresh login
    cl.set_settings({
        "user_agent": "Instagram 302.1.0.36.111 Android (33/13; 420dpi; 1080x2400; Google/google; Pixel 7; panther; panther; en_JP; 533450710)",
        "country": "JP",
        "country_code": 81,
        "locale": "ja_JP",
        "timezone_offset": 32400,
    })

    cl.login(
        os.environ.get("INSTAGRAM_USERNAME", "robby.for.nurse"),
        os.environ.get("INSTAGRAM_PASSWORD", "")
    )
    cl.dump_settings(str(SESSION_FILE))
    print(f"[IG] Fresh login. User: {cl.username}")
    return cl


def convert_to_jpeg(png_paths: List[Path]) -> List[str]:
    """Convert PNG slides to JPEG for Instagram."""
    from PIL import Image

    TEMP_DIR.mkdir(exist_ok=True)
    jpeg_paths = []
    for png in png_paths:
        jpeg_path = TEMP_DIR / png.name.replace(".png", ".jpg")
        img = Image.open(png).convert("RGB")
        img.save(str(jpeg_path), "JPEG", quality=95)
        jpeg_paths.append(str(jpeg_path))
    return jpeg_paths


def post_to_instagram(content_dir: Path, dry_run: bool = False) -> Dict:
    """Post carousel to Instagram."""
    slides = sorted(content_dir.glob("slide_*.png"))
    if not slides:
        return {"status": "error", "error": "No slides found"}

    caption_file = content_dir / "caption.txt"
    hashtags_file = content_dir / "hashtags.txt"

    caption = caption_file.read_text().strip() if caption_file.exists() else ""
    hashtags = hashtags_file.read_text().strip() if hashtags_file.exists() else ""
    full_caption = f"{caption}\n\n{hashtags}" if hashtags else caption

    print(f"[IG] Content: {content_dir.name}")
    print(f"[IG] Slides: {len(slides)}")
    print(f"[IG] Caption: {full_caption[:80]}...")

    if dry_run:
        print("[IG] DRY RUN - skipping actual upload")
        return {"status": "dry_run", "slides": len(slides)}

    try:
        cl = instagram_login()
        jpeg_paths = convert_to_jpeg(slides)

        media = cl.album_upload(paths=jpeg_paths, caption=full_caption)

        url = f"https://www.instagram.com/p/{media.code}/"
        print(f"[IG] SUCCESS: {url}")

        # Save updated session
        cl.dump_settings(str(SESSION_FILE))

        return {
            "status": "success",
            "media_id": str(media.id),
            "code": media.code,
            "url": url,
        }
    except Exception as e:
        error_msg = str(e)
        print(f"[IG] FAILED: {error_msg}")

        # If rate limited or "inactive", wait and retry once
        if "inactive" in error_msg.lower() or "429" in error_msg:
            print("[IG] Rate limited. Waiting 120s and retrying...")
            time.sleep(120)
            try:
                cl = instagram_login()
                jpeg_paths = convert_to_jpeg(slides)
                media = cl.album_upload(paths=jpeg_paths, caption=full_caption)
                url = f"https://www.instagram.com/p/{media.code}/"
                print(f"[IG] RETRY SUCCESS: {url}")
                cl.dump_settings(str(SESSION_FILE))
                return {
                    "status": "success",
                    "media_id": str(media.id),
                    "code": media.code,
                    "url": url,
                }
            except Exception as retry_e:
                return {"status": "error", "error": str(retry_e)}

        return {"status": "error", "error": error_msg}


# ============================================================
# TikTok Posting (Slack通知 + 手動アップ待ち)
# ============================================================

def post_to_tiktok(content_dir: Path, dry_run: bool = False) -> Dict:
    """Prepare TikTok carousel and notify via Slack."""
    slides = sorted(content_dir.glob("slide_*.png"))
    if not slides:
        return {"status": "error", "error": "No slides found"}

    caption_file = content_dir / "caption.txt"
    hashtags_file = content_dir / "hashtags.txt"

    caption = caption_file.read_text().strip() if caption_file.exists() else ""
    hashtags = hashtags_file.read_text().strip() if hashtags_file.exists() else ""
    full_caption = f"{caption}\n\n{hashtags}" if hashtags else caption

    print(f"[TT] Content: {content_dir.name}")
    print(f"[TT] Slides: {len(slides)}")

    if dry_run:
        print("[TT] DRY RUN - skipping")
        return {"status": "dry_run"}

    # Notify Slack with caption and instructions
    msg = (
        f"📱 *TikTok投稿準備完了*\n"
        f"フォルダ: `content/ready/{content_dir.name}/`\n"
        f"スライド: {len(slides)}枚\n\n"
        f"*キャプション:*\n{full_caption}\n\n"
        f"👉 TikTokアプリでカルーセル投稿してください\n"
        f"投稿後: `python3 scripts/auto_post.py --mark-posted {content_dir.name} tiktok`"
    )
    slack_notify(msg)
    print("[TT] Slack notification sent")

    return {"status": "notified", "message": "Slack notification sent for manual upload"}


# ============================================================
# Main Logic
# ============================================================

def post_next(platforms: List[str], dry_run: bool = False) -> List[Dict]:
    """Post next unposted content to specified platforms."""
    results = []
    log = load_post_log()

    for platform in platforms:
        content_dir = get_next_unposted(platform)
        if not content_dir:
            print(f"[{platform.upper()}] No unposted content available")
            results.append({
                "platform": platform,
                "status": "no_content",
            })
            continue

        if platform == "instagram":
            result = post_to_instagram(content_dir, dry_run)
        elif platform == "tiktok":
            result = post_to_tiktok(content_dir, dry_run)
        else:
            result = {"status": "error", "error": f"Unknown platform: {platform}"}

        # Log the result
        entry = {
            "platform": platform,
            "dir": content_dir.name,
            "timestamp": datetime.now().isoformat(),
            **result,
        }
        log.append(entry)
        results.append(entry)

        # Wait between platforms
        if len(platforms) > 1:
            time.sleep(PLATFORM_INTERVAL)

    save_post_log(log)
    return results


def retry_failed(dry_run: bool = False) -> List[Dict]:
    """Retry all failed posts."""
    log = load_post_log()
    failed = [e for e in log if e.get("status") == "error"]

    if not failed:
        print("No failed posts to retry")
        return []

    results = []
    for entry in failed:
        content_dir = READY_DIR / entry["dir"]
        if not content_dir.exists():
            print(f"Content dir not found: {entry['dir']}")
            continue

        platform = entry["platform"]
        print(f"\nRetrying: {entry['dir']} on {platform}")

        if platform == "instagram":
            result = post_to_instagram(content_dir, dry_run)
        elif platform == "tiktok":
            result = post_to_tiktok(content_dir, dry_run)
        else:
            continue

        new_entry = {
            "platform": platform,
            "dir": entry["dir"],
            "timestamp": datetime.now().isoformat(),
            "retry": True,
            **result,
        }
        log.append(new_entry)
        results.append(new_entry)
        time.sleep(POST_INTERVAL)

    save_post_log(log)
    return results


def mark_posted(dir_name: str, platform: str):
    """Manually mark a post as completed (for TikTok manual uploads)."""
    log = load_post_log()
    log.append({
        "platform": platform,
        "dir": dir_name,
        "timestamp": datetime.now().isoformat(),
        "status": "success",
        "manual": True,
    })
    save_post_log(log)
    print(f"Marked {dir_name} as posted on {platform}")


def show_status():
    """Show posting status."""
    log = load_post_log()
    dirs = get_ready_dirs()

    print(f"\n{'='*60}")
    print(f"SNS投稿ステータス ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    print(f"{'='*60}")
    print(f"準備済みコンテンツ: {len(dirs)}")

    for d in dirs:
        ig_status = "⬜"
        tt_status = "⬜"
        for entry in log:
            if entry.get("dir") == d.name:
                if entry["platform"] == "instagram":
                    if entry["status"] == "success":
                        ig_status = f"✅ {entry.get('url', '')}"
                    elif entry["status"] == "error":
                        ig_status = "❌"
                elif entry["platform"] == "tiktok":
                    if entry["status"] == "success":
                        tt_status = "✅"
                    elif entry["status"] == "notified":
                        tt_status = "📱待ち"
                    elif entry["status"] == "error":
                        tt_status = "❌"

        print(f"\n  {d.name}:")
        print(f"    IG: {ig_status}")
        print(f"    TT: {tt_status}")

    print(f"\n{'='*60}")


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="ナースロビー SNS自動投稿")
    parser.add_argument("--instagram", action="store_true", help="Post to Instagram")
    parser.add_argument("--tiktok", action="store_true", help="Post to TikTok")
    parser.add_argument("--all", action="store_true", help="Post to all platforms")
    parser.add_argument("--retry", action="store_true", help="Retry failed posts")
    parser.add_argument("--status", action="store_true", help="Show posting status")
    parser.add_argument("--mark-posted", nargs=2, metavar=("DIR", "PLATFORM"),
                       help="Mark a post as completed")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (no actual posting)")

    args = parser.parse_args()

    load_env()

    if args.status:
        show_status()
        return

    if args.mark_posted:
        mark_posted(args.mark_posted[0], args.mark_posted[1])
        return

    if args.retry:
        results = retry_failed(args.dry_run)
        for r in results:
            print(f"  [{r['platform']}] {r['dir']}: {r['status']}")
        return

    platforms = []
    if args.all:
        platforms = ["instagram", "tiktok"]
    else:
        if args.instagram:
            platforms.append("instagram")
        if args.tiktok:
            platforms.append("tiktok")

    if not platforms:
        parser.print_help()
        return

    results = post_next(platforms, args.dry_run)

    # Summary
    success = sum(1 for r in results if r.get("status") == "success")
    failed = sum(1 for r in results if r.get("status") == "error")
    print(f"\n=== Summary: {success} success, {failed} failed ===")

    # Slack summary
    if success > 0:
        urls = [r.get("url", "") for r in results if r.get("url")]
        slack_notify(
            f"✅ SNS自動投稿完了: {success}件成功\n" +
            "\n".join(urls)
        )


if __name__ == "__main__":
    main()
