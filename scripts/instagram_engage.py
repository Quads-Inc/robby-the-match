#!/usr/bin/env python3
"""
instagram_engage.py — Instagram日常エンゲージメント自動化 v1.0

看護師系ハッシュタグの投稿にいいね・コメントを行い、
アカウントの「人間らしさ」を維持する。

cron: 毎日12:00-13:00（ランダム遅延付き）
  0 12 * * * sleep $((RANDOM \% 3600)) && python3 ~/robby-the-match/scripts/instagram_engage.py --daily

使い方:
  python3 scripts/instagram_engage.py --daily        # 日次エンゲージメント
  python3 scripts/instagram_engage.py --daily --dry-run  # ドライラン
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

PROJECT_DIR = Path(__file__).parent.parent
SESSION_FILE = PROJECT_DIR / "data" / ".instagram_session.json"
ENGAGE_LOG_FILE = PROJECT_DIR / "data" / "engagement_log.json"
ENV_FILE = PROJECT_DIR / ".env"

# Target hashtags (nursing community)
TARGET_HASHTAGS = [
    "看護師あるある",
    "ナース",
    "看護師転職",
    "夜勤あるある",
    "看護師の日常",
    "神奈川看護師",
    "病棟あるある",
    "看護師ママ",
    "ナースライフ",
    "看護師",
]

# Comment templates (Robby character voice - casual, empathetic)
COMMENT_TEMPLATES = [
    "わかる...!",
    "夜勤お疲れさまです!",
    "共感しすぎて保存した",
    "これ本当にそう",
    "めちゃくちゃわかる",
    "応援してます!",
    "素敵な投稿ですね",
    "がんばってますね!",
]

# Safety limits
MAX_ACTIONS_PER_SESSION = 15
MAX_LIKES_PER_SESSION = 12
MAX_COMMENTS_PER_SESSION = 3
LIKE_PROBABILITY = 0.8
COMMENT_PROBABILITY = 0.08


def load_env():
    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())


def load_engage_log() -> List[Dict]:
    if ENGAGE_LOG_FILE.exists():
        with open(ENGAGE_LOG_FILE) as f:
            return json.load(f)
    return []


def save_engage_log(log: List[Dict]):
    with open(ENGAGE_LOG_FILE, "w") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)


def slack_notify(message: str):
    try:
        import subprocess
        subprocess.run(
            ["python3", str(PROJECT_DIR / "scripts" / "notify_slack.py"),
             "--message", message],
            capture_output=True, timeout=30
        )
    except Exception:
        pass


def instagram_login():
    """Login with session reuse."""
    from instagrapi import Client

    cl = Client()
    cl.delay_range = [2, 5]

    if SESSION_FILE.exists():
        try:
            cl.load_settings(str(SESSION_FILE))
            cl.login(
                os.environ.get("INSTAGRAM_USERNAME", "robby.for.nurse"),
                os.environ.get("INSTAGRAM_PASSWORD", "")
            )
            return cl
        except Exception:
            pass

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
    return cl


def daily_engagement(dry_run: bool = False) -> Dict:
    """Spend ~15-30 min engaging with nursing community content."""
    print(f"[ENGAGE] Starting daily engagement ({datetime.now().strftime('%H:%M')})")

    session_log = {
        "date": datetime.now().isoformat(),
        "actions": [],
        "total_likes": 0,
        "total_comments": 0,
        "hashtags_browsed": [],
        "dry_run": dry_run,
    }

    if dry_run:
        print("[ENGAGE] DRY RUN mode")
        # Simulate planning
        hashtags = random.sample(TARGET_HASHTAGS, min(3, len(TARGET_HASHTAGS)))
        for tag in hashtags:
            print(f"  [DRY] Would browse #{tag}, like ~{int(5*LIKE_PROBABILITY)} posts")
        session_log["hashtags_browsed"] = hashtags
        return session_log

    try:
        cl = instagram_login()
    except Exception as e:
        print(f"[ENGAGE] Login failed: {e}")
        return {"error": str(e)}

    total_actions = 0
    total_likes = 0
    total_comments = 0

    # Browse 2-3 random hashtags
    hashtags = random.sample(TARGET_HASHTAGS, min(random.randint(2, 3), len(TARGET_HASHTAGS)))

    for tag in hashtags:
        if total_actions >= MAX_ACTIONS_PER_SESSION:
            break

        print(f"[ENGAGE] Browsing #{tag}...")
        session_log["hashtags_browsed"].append(tag)

        try:
            medias = cl.hashtag_medias_recent(tag, amount=10)
            time.sleep(random.uniform(2, 5))
        except Exception as e:
            print(f"[ENGAGE] Failed to fetch #{tag}: {e}")
            continue

        for media in medias:
            if total_actions >= MAX_ACTIONS_PER_SESSION:
                break

            # Like
            if total_likes < MAX_LIKES_PER_SESSION and random.random() < LIKE_PROBABILITY:
                try:
                    cl.media_like(media.id)
                    total_likes += 1
                    total_actions += 1
                    session_log["actions"].append({
                        "type": "like",
                        "hashtag": tag,
                        "media_id": str(media.id),
                    })
                    print(f"  [LIKE] #{tag} ({total_likes}/{MAX_LIKES_PER_SESSION})")
                    time.sleep(random.uniform(15, 45))
                except Exception as e:
                    print(f"  [LIKE] Failed: {e}")
                    if "blocked" in str(e).lower():
                        print("[ENGAGE] Action blocked! Stopping session.")
                        break

            # Comment (rare)
            if total_comments < MAX_COMMENTS_PER_SESSION and random.random() < COMMENT_PROBABILITY:
                comment = random.choice(COMMENT_TEMPLATES)
                try:
                    cl.media_comment(media.id, comment)
                    total_comments += 1
                    total_actions += 1
                    session_log["actions"].append({
                        "type": "comment",
                        "hashtag": tag,
                        "media_id": str(media.id),
                        "text": comment,
                    })
                    print(f"  [COMMENT] \"{comment}\" on #{tag}")
                    time.sleep(random.uniform(30, 90))
                except Exception as e:
                    print(f"  [COMMENT] Failed: {e}")

        # Pause between hashtags
        time.sleep(random.uniform(10, 30))

    session_log["total_likes"] = total_likes
    session_log["total_comments"] = total_comments

    # Save session and session file
    cl.dump_settings(str(SESSION_FILE))

    # Persist log
    log = load_engage_log()
    log.append(session_log)
    # Keep only last 30 days
    if len(log) > 30:
        log = log[-30:]
    save_engage_log(log)

    summary = f"[ENGAGE] Done: {total_likes} likes, {total_comments} comments across {len(hashtags)} hashtags"
    print(summary)

    return session_log


def main():
    parser = argparse.ArgumentParser(description="Instagram エンゲージメント自動化")
    parser.add_argument("--daily", action="store_true", help="日次エンゲージメント実行")
    parser.add_argument("--dry-run", action="store_true", help="ドライラン")
    args = parser.parse_args()

    load_env()

    if args.daily:
        result = daily_engagement(dry_run=args.dry_run)
        if "error" not in result:
            print(f"Total: {result.get('total_likes', 0)} likes, {result.get('total_comments', 0)} comments")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
