#!/usr/bin/env python3
"""
TikTok Analytics Collection Script
===================================
TikTokプロフィールページをcurlで取得し、埋め込みJSONから
プロフィール指標と動画別パフォーマンスデータを収集する。

使い方:
  python3 tiktok_analytics.py --status        # プロフィール情報を表示
  python3 tiktok_analytics.py --update        # posting_queue.json更新 + KPI追記
  python3 tiktok_analytics.py --daily-kpi     # KPI CSVのみ追記
"""

import argparse
import csv
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
QUEUE_FILE = PROJECT_DIR / "data" / "posting_queue.json"
KPI_FILE = PROJECT_DIR / "data" / "kpi_log.csv"
COOKIE_FILE = PROJECT_DIR / "TK_cookies_robby15051.json"
COOKIE_TXT = PROJECT_DIR / "data" / ".tiktok_cookies.txt"
LOG_DIR = PROJECT_DIR / "logs"
ENV_FILE = PROJECT_DIR / ".env"
TIKTOK_USERNAME = "robby15051"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def load_env():
    """Load .env file."""
    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())


def slack_notify(message):
    """Slack notification."""
    try:
        subprocess.run(
            ["python3", str(PROJECT_DIR / "scripts" / "notify_slack.py"),
             "--message", message],
            capture_output=True, timeout=30
        )
    except Exception as e:
        print(f"[WARN] Slack notification failed: {e}")


def log_event(event_type, data):
    """Write event to daily log file."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"tiktok_analytics_{datetime.now().strftime('%Y%m%d')}.log"
    entry = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "data": data
    }
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ============================================================
# Cookie handling
# ============================================================

def build_cookie_args():
    """Build curl cookie arguments from the best available cookie source.

    Prefers the Netscape-format .txt file (curl -b directly),
    falls back to converting the JSON cookie file to a header string.
    """
    if COOKIE_TXT.exists():
        return ["-b", str(COOKIE_TXT)]

    if COOKIE_FILE.exists():
        try:
            with open(COOKIE_FILE, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            pairs = []
            for c in cookies:
                name = c.get("name", "")
                value = c.get("value", "")
                if name and value:
                    pairs.append(f"{name}={value}")
            if pairs:
                return ["-b", "; ".join(pairs)]
        except Exception:
            pass

    return []


# ============================================================
# Fetch and parse TikTok profile page
# ============================================================

def fetch_profile_html():
    """Curl the TikTok profile page and return the HTML string."""
    cookie_args = build_cookie_args()
    cmd = [
        "curl", "-s", "-L",
        "--max-time", "30",
        "-H", f"User-Agent: {USER_AGENT}",
        "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "-H", "Accept-Language: ja,en-US;q=0.9,en;q=0.8",
    ] + cookie_args + [
        f"https://www.tiktok.com/@{TIKTOK_USERNAME}"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        if result.returncode != 0:
            print(f"[ERROR] curl returned exit code {result.returncode}")
            return None
        html = result.stdout
        if not html or len(html) < 500:
            print(f"[ERROR] Response too short ({len(html) if html else 0} bytes)")
            return None
        return html
    except subprocess.TimeoutExpired:
        print("[ERROR] curl timed out (45s)")
        return None
    except Exception as e:
        print(f"[ERROR] curl exception: {e}")
        return None


def extract_rehydration_json(html):
    """Extract and parse the __UNIVERSAL_DATA_FOR_REHYDRATION__ JSON blob from HTML."""
    # Look for the script tag with the rehydration data
    pattern = r'<script\s+id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>\s*(.*?)\s*</script>'
    match = re.search(pattern, html, re.DOTALL)
    if not match:
        # Fallback: try without id attribute, just look for the variable name in any script
        pattern2 = r'__UNIVERSAL_DATA_FOR_REHYDRATION__\s*=\s*(\{.*?\})\s*;?\s*</script>'
        match = re.search(pattern2, html, re.DOTALL)
        if not match:
            return None

    json_str = match.group(1).strip()
    try:
        data = json.loads(json_str)
        return data
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse rehydration JSON: {e}")
        return None


def extract_profile_data(rehydration_data):
    """Extract profile-level metrics from the rehydration JSON.

    Returns a dict with keys: followers, following, video_count, heart_count, nickname, signature
    or None on failure.
    """
    if not rehydration_data:
        return None

    # Navigate the known path to user detail info
    default_scope = rehydration_data.get("__DEFAULT_SCOPE__", {})

    # Try multiple possible keys for user detail
    user_detail = (
        default_scope.get("webapp.user-detail", {})
        or default_scope.get("webapp.user-detail", None)
    )
    if not user_detail:
        # Try iterating to find a key containing user-detail
        for key in default_scope:
            if "user-detail" in key or "user_detail" in key:
                user_detail = default_scope[key]
                break

    if not user_detail:
        print("[WARN] Could not find user-detail in rehydration data")
        print(f"[DEBUG] Available keys in __DEFAULT_SCOPE__: {list(default_scope.keys())}")
        return None

    user_info = user_detail.get("userInfo", {})
    user = user_info.get("user", {})
    stats = user_info.get("stats", {})

    profile = {
        "nickname": user.get("nickname", ""),
        "signature": user.get("signature", ""),
        "unique_id": user.get("uniqueId", TIKTOK_USERNAME),
        "followers": stats.get("followerCount", 0),
        "following": stats.get("followingCount", 0),
        "video_count": stats.get("videoCount", 0),
        "heart_count": stats.get("heartCount", 0)
            or stats.get("heart", 0)
            or stats.get("diggCount", 0),
    }

    return profile


def extract_video_list(rehydration_data):
    """Extract per-video metrics from the rehydration JSON.

    Returns a list of dicts, each with keys:
    id, desc, views, likes, comments, shares, create_time, cover_url
    """
    if not rehydration_data:
        return []

    default_scope = rehydration_data.get("__DEFAULT_SCOPE__", {})

    # Find user detail section
    user_detail = default_scope.get("webapp.user-detail", {})
    if not user_detail:
        for key in default_scope:
            if "user-detail" in key or "user_detail" in key:
                user_detail = default_scope[key]
                break

    if not user_detail:
        return []

    # Video list can be in different locations depending on TikTok's data structure
    video_list_raw = None

    # Path 1: userInfo.user.videoList (older structure)
    user_info = user_detail.get("userInfo", {})
    video_list_raw = user_info.get("user", {}).get("videoList", None)

    # Path 2: itemList directly under user-detail
    if not video_list_raw:
        video_list_raw = user_detail.get("itemList", None)

    # Path 3: Check webapp.video-detail or similar
    if not video_list_raw:
        for key in default_scope:
            section = default_scope[key]
            if isinstance(section, dict):
                if "itemList" in section:
                    video_list_raw = section["itemList"]
                    break
                # Also check nested structures
                for subkey, subval in section.items():
                    if isinstance(subval, list) and len(subval) > 0:
                        if isinstance(subval[0], dict) and "id" in subval[0]:
                            video_list_raw = subval
                            break

    if not video_list_raw:
        return []

    videos = []
    for item in video_list_raw:
        if not isinstance(item, dict):
            continue

        stats = item.get("stats", {})
        video = {
            "id": item.get("id", ""),
            "desc": item.get("desc", ""),
            "create_time": item.get("createTime", 0),
            "views": stats.get("playCount", 0),
            "likes": stats.get("diggCount", 0),
            "comments": stats.get("commentCount", 0),
            "shares": stats.get("shareCount", 0),
            "cover_url": item.get("video", {}).get("cover", ""),
        }

        # Convert create_time to ISO string if it's a timestamp
        if isinstance(video["create_time"], (int, float)) and video["create_time"] > 0:
            try:
                video["create_time_str"] = datetime.fromtimestamp(
                    video["create_time"]
                ).strftime("%Y-%m-%d %H:%M")
            except (OSError, ValueError):
                video["create_time_str"] = str(video["create_time"])
        else:
            video["create_time_str"] = str(video["create_time"])

        videos.append(video)

    return videos


def fallback_profile_from_html(html):
    """Fallback: scrape profile data directly from HTML using regex patterns
    when the rehydration JSON is not available or incomplete.
    """
    profile = {
        "nickname": "",
        "signature": "",
        "unique_id": TIKTOK_USERNAME,
        "followers": 0,
        "following": 0,
        "video_count": 0,
        "heart_count": 0,
    }

    # videoCount
    matches = re.findall(r'videoCount["\':]+\s*(\d+)', html)
    if matches:
        profile["video_count"] = max(int(m) for m in matches)

    # followerCount
    matches = re.findall(r'followerCount["\':]+\s*(\d+)', html)
    if matches:
        profile["followers"] = max(int(m) for m in matches)

    # followingCount
    matches = re.findall(r'followingCount["\':]+\s*(\d+)', html)
    if matches:
        profile["following"] = max(int(m) for m in matches)

    # heartCount / heart
    matches = re.findall(r'(?:heartCount|"heart")["\':]+\s*(\d+)', html)
    if matches:
        profile["heart_count"] = max(int(m) for m in matches)

    # nickname
    match = re.search(r'"nickname"\s*:\s*"([^"]+)"', html)
    if match:
        profile["nickname"] = match.group(1)

    return profile


# ============================================================
# Full data fetch orchestration
# ============================================================

def fetch_profile_via_browser():
    """Playwright fallback: render TikTok profile with JavaScript for full data.

    TikTok increasingly requires JS rendering. This uses the .venv Playwright
    to fully render the page and extract data.
    """
    VENV_PYTHON = PROJECT_DIR / ".venv" / "bin" / "python3"
    if not VENV_PYTHON.exists():
        print("  [BROWSER] .venv not found")
        return None

    script = PROJECT_DIR / "content" / "temp_videos" / "_analytics_browser.py"
    script.parent.mkdir(parents=True, exist_ok=True)

    with open(script, "w", encoding="utf-8") as f:
        f.write(f"""
import json, sys
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://www.tiktok.com/@{TIKTOK_USERNAME}", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3000)
        html = page.content()
        browser.close()
        print("BROWSER_HTML_START")
        print(html)
        print("BROWSER_HTML_END")
except Exception as e:
    print(f"BROWSER_ERROR: {{e}}", file=sys.stderr)
""")

    try:
        result = subprocess.run(
            [str(VENV_PYTHON), str(script)],
            capture_output=True, text=True, timeout=60,
            env={**os.environ, "DISPLAY": ":0"}
        )
        script.unlink(missing_ok=True)

        stdout = result.stdout or ""
        if "BROWSER_HTML_START" in stdout and "BROWSER_HTML_END" in stdout:
            start = stdout.index("BROWSER_HTML_START") + len("BROWSER_HTML_START")
            end = stdout.index("BROWSER_HTML_END")
            return stdout[start:end].strip()
        return None
    except Exception as e:
        print(f"  [BROWSER] Exception: {e}")
        script.unlink(missing_ok=True)
        return None


def fetch_tiktok_data():
    """Fetch and parse all TikTok data with retry + browser fallback.

    Returns (profile_dict, video_list) or (None, []).

    v2.0: Added retry logic (3 attempts) and Playwright browser fallback.
    """
    import time as _time

    max_retries = 3
    profile = None
    videos = []

    for attempt in range(max_retries):
        if attempt > 0:
            wait = 10 * (2 ** (attempt - 1))  # 10s, 20s
            print(f"  [RETRY] Attempt {attempt + 1}/{max_retries} (waiting {wait}s)")
            _time.sleep(wait)

        print(f"Fetching TikTok profile for @{TIKTOK_USERNAME}... (attempt {attempt + 1})")
        html = fetch_profile_html()
        if not html:
            continue

        rehydration = extract_rehydration_json(html)
        if rehydration:
            profile = extract_profile_data(rehydration)
            videos = extract_video_list(rehydration)
            if profile:
                print(f"  Parsed rehydration JSON successfully")
                break

        # Regex fallback
        profile = fallback_profile_from_html(html)
        if profile and profile.get("video_count", 0) > 0:
            print(f"  Used regex fallback for profile data")
            break

        print(f"  [WARN] Attempt {attempt + 1} yielded no data")

    # Browser fallback if curl failed
    if not profile or (not videos and profile.get("video_count", 0) > 0):
        print("  [BROWSER] Trying Playwright browser fallback...")
        browser_html = fetch_profile_via_browser()
        if browser_html:
            rehydration = extract_rehydration_json(browser_html)
            if rehydration:
                browser_profile = extract_profile_data(rehydration)
                browser_videos = extract_video_list(rehydration)
                if browser_profile:
                    profile = browser_profile
                    videos = browser_videos
                    print(f"  [BROWSER] Success: {len(videos)} videos found")
                else:
                    print("  [BROWSER] Rehydration found but no profile data")
            else:
                # Try regex fallback on browser HTML
                if not profile:
                    profile = fallback_profile_from_html(browser_html)
                print("  [BROWSER] No rehydration JSON in browser output")
        else:
            print("  [BROWSER] Browser fallback failed")

    if not profile:
        print("[ERROR] All methods failed to fetch profile data")
        log_event("analytics_fetch_failed", {"attempts": max_retries, "browser_tried": True})

    # Log match rate if we have queue data
    if videos:
        _log_match_rate(videos)

    return profile, videos


def _log_match_rate(videos):
    """Check how many queue posts can be matched to scraped videos."""
    if not QUEUE_FILE.exists():
        return
    try:
        with open(QUEUE_FILE, encoding="utf-8") as f:
            queue = json.load(f)
        posted = [p for p in queue.get("posts", []) if p.get("status") == "posted"]
        if not posted:
            return

        matched = 0
        for post in posted:
            caption = post.get("caption", "")[:30]
            for v in videos:
                desc = v.get("desc", "")[:30] if isinstance(v, dict) else ""
                if caption and desc and caption[:15] in desc:
                    matched += 1
                    break

        rate = matched / len(posted) * 100 if posted else 0
        print(f"  Match rate: {matched}/{len(posted)} posted ({rate:.0f}%)")

        if rate < 50 and len(posted) >= 3:
            slack_notify(
                f"⚠️ TikTok Analytics: Low match rate ({rate:.0f}%)\n"
                f"Only {matched}/{len(posted)} posted videos could be matched.\n"
                f"Consider adding tiktok_video_id to queue entries."
            )
    except Exception:
        pass


# ============================================================
# --status: Display current profile stats
# ============================================================

def show_status():
    """Display current TikTok profile stats and per-video metrics."""
    profile, videos = fetch_tiktok_data()

    if not profile:
        print("[ERROR] Could not retrieve profile data")
        return False

    print()
    print("=" * 55)
    print(f"  TikTok Profile: @{profile.get('unique_id', TIKTOK_USERNAME)}")
    if profile.get("nickname"):
        print(f"  Nickname: {profile['nickname']}")
    print("=" * 55)
    print(f"  Followers:   {profile['followers']:,}")
    print(f"  Following:   {profile['following']:,}")
    print(f"  Videos:      {profile['video_count']:,}")
    print(f"  Total Likes: {profile['heart_count']:,}")
    print("=" * 55)

    if videos:
        print(f"\n  Per-video metrics ({len(videos)} videos found):")
        print(f"  {'ID':<22} {'Date':<18} {'Views':>10} {'Likes':>8} {'Comments':>8} {'Shares':>8}")
        print(f"  {'-'*22} {'-'*18} {'-'*10} {'-'*8} {'-'*8} {'-'*8}")

        total_views = 0
        total_likes = 0
        total_comments = 0
        total_shares = 0

        for v in videos:
            vid = v["id"][:20] if len(v["id"]) > 20 else v["id"]
            print(
                f"  {vid:<22} {v.get('create_time_str', 'N/A'):<18} "
                f"{v['views']:>10,} {v['likes']:>8,} "
                f"{v['comments']:>8,} {v['shares']:>8,}"
            )
            total_views += v["views"]
            total_likes += v["likes"]
            total_comments += v["comments"]
            total_shares += v["shares"]

        print(f"  {'-'*22} {'-'*18} {'-'*10} {'-'*8} {'-'*8} {'-'*8}")
        print(
            f"  {'TOTAL':<22} {'':<18} "
            f"{total_views:>10,} {total_likes:>8,} "
            f"{total_comments:>8,} {total_shares:>8,}"
        )
    else:
        print("\n  No per-video data available (videos may require scrolling to load)")

    print()
    return True


# ============================================================
# --update: Update posting_queue.json + append KPI
# ============================================================

def update_queue_performance(videos):
    """Match scraped video data back to posting_queue.json entries and update performance.

    Matching strategy:
    1. Match by tiktok_url if set in queue entry
    2. Match by caption substring similarity (first 30 chars of desc vs caption)
    3. Match by posted_at timestamp vs create_time (within 24 hours)
    """
    if not QUEUE_FILE.exists():
        print("  [WARN] posting_queue.json not found, skipping queue update")
        return False

    with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
        queue = json.load(f)

    if not videos:
        print("  No video data to match against queue")
        return False

    posted_entries = [p for p in queue.get("posts", []) if p.get("status") == "posted"]
    if not posted_entries:
        print("  No posted entries in queue to update")
        return False

    updated_count = 0

    for entry in posted_entries:
        caption = entry.get("caption", "")
        # Normalize caption for matching: strip whitespace, take first 30 chars
        caption_prefix = re.sub(r'\s+', '', caption)[:30]

        best_match = None
        best_score = 0

        for video in videos:
            desc = video.get("desc", "")
            desc_normalized = re.sub(r'\s+', '', desc)

            # Check if caption prefix appears in video description or vice versa
            score = 0

            if caption_prefix and caption_prefix[:15] in desc_normalized:
                score = 3
            elif desc_normalized[:15] and desc_normalized[:15] in re.sub(r'\s+', '', caption):
                score = 2

            # Also check time proximity if posted_at is available
            if entry.get("posted_at") and video.get("create_time"):
                try:
                    posted_dt = datetime.fromisoformat(entry["posted_at"])
                    video_dt = datetime.fromtimestamp(video["create_time"])
                    diff_hours = abs((posted_dt - video_dt).total_seconds()) / 3600
                    if diff_hours < 24:
                        score += 1
                except (ValueError, OSError, TypeError):
                    pass

            if score > best_score:
                best_score = score
                best_match = video

        if best_match and best_score >= 1:
            entry["performance"] = {
                "views": best_match["views"],
                "likes": best_match["likes"],
                "comments": best_match["comments"],
                "shares": best_match.get("shares", None),
                "saves": None,  # TikTok public page doesn't expose save count
                "last_checked": datetime.now().isoformat(),
            }
            if best_match.get("id"):
                entry["tiktok_video_id"] = best_match["id"]
            updated_count += 1
            print(f"    Matched #{entry['id']} ({entry['content_id']}) -> "
                  f"views={best_match['views']}, likes={best_match['likes']}")
        else:
            print(f"    No match for #{entry['id']} ({entry['content_id']})")

    if updated_count > 0:
        queue["updated"] = datetime.now().isoformat()
        with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
            json.dump(queue, f, ensure_ascii=False, indent=2)
        print(f"  Updated {updated_count} entries in posting_queue.json")

    return updated_count > 0


def append_kpi(profile):
    """Append today's KPI row to data/kpi_log.csv.

    CSV header: date,tiktok_followers,tiktok_videos,tiktok_total_views,tiktok_total_likes,lp_visitors,line_registrations
    """
    if not profile:
        print("  [ERROR] No profile data, cannot append KPI")
        return False

    KPI_FILE.parent.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")

    # Read existing file to check if today already has an entry
    existing_rows = []
    today_exists = False

    if KPI_FILE.exists():
        with open(KPI_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                existing_rows.append(row)
                if row and row[0] == today:
                    today_exists = True

    # Prepare the new row
    new_row = [
        today,
        str(profile.get("followers", 0)),
        str(profile.get("video_count", 0)),
        str(profile.get("heart_count", 0)),  # total_views approximation from heart
        str(profile.get("heart_count", 0)),  # total_likes
        "0",  # lp_visitors - not tracked here
        "0",  # line_registrations - not tracked here
    ]

    # Note: The CSV header uses tiktok_total_views and tiktok_total_likes.
    # heart_count is total likes. Total views isn't available at profile level
    # without summing per-video data. We'll use 0 for views if we can't sum them.

    if today_exists:
        # Update existing row for today
        with open(KPI_FILE, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            for row in existing_rows:
                if row and row[0] == today:
                    # Preserve lp_visitors and line_registrations if they were set
                    if len(row) >= 6 and row[5] != "0":
                        new_row[5] = row[5]
                    if len(row) >= 7 and row[6] != "0":
                        new_row[6] = row[6]
                    writer.writerow(new_row)
                else:
                    writer.writerow(row)
        print(f"  Updated KPI for {today} in {KPI_FILE.name}")
    else:
        # Append new row
        with open(KPI_FILE, 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            f.write("\n".join([]) if not existing_rows else "")
            writer.writerow(new_row)
        print(f"  Appended KPI for {today} to {KPI_FILE.name}")

    return True


def compute_total_views(profile, videos):
    """If we have per-video data, sum the views for a more accurate total_views.
    Otherwise fall back to 0 (profile-level view count is not exposed by TikTok).
    """
    if videos:
        return sum(v.get("views", 0) for v in videos)
    return 0


def append_kpi_with_videos(profile, videos):
    """Enhanced KPI append that computes total_views from per-video data."""
    if not profile:
        print("  [ERROR] No profile data, cannot append KPI")
        return False

    total_views = compute_total_views(profile, videos)

    KPI_FILE.parent.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")

    # Read existing data
    existing_rows = []
    today_index = -1

    if KPI_FILE.exists():
        with open(KPI_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                existing_rows.append(row)
                if row and row[0] == today:
                    today_index = i

    new_row = [
        today,
        str(profile.get("followers", 0)),
        str(profile.get("video_count", 0)),
        str(total_views),
        str(profile.get("heart_count", 0)),
        "0",  # lp_visitors
        "0",  # line_registrations
    ]

    if today_index >= 0:
        # Preserve lp_visitors and line_registrations from existing row
        old_row = existing_rows[today_index]
        if len(old_row) >= 6 and old_row[5] != "0":
            new_row[5] = old_row[5]
        if len(old_row) >= 7 and old_row[6] != "0":
            new_row[6] = old_row[6]
        existing_rows[today_index] = new_row

        with open(KPI_FILE, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            for row in existing_rows:
                writer.writerow(row)
        print(f"  Updated KPI for {today} in {KPI_FILE.name}")
    else:
        with open(KPI_FILE, 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(new_row)
        print(f"  Appended KPI for {today} to {KPI_FILE.name}")

    print(f"    followers={profile.get('followers', 0)}, "
          f"videos={profile.get('video_count', 0)}, "
          f"total_views={total_views}, "
          f"total_likes={profile.get('heart_count', 0)}")

    return True


def cmd_update():
    """--update: Full update cycle — fetch data, update queue performance, append KPI."""
    profile, videos = fetch_tiktok_data()

    if not profile:
        print("[ERROR] Could not retrieve profile data")
        log_event("analytics_failed", {"reason": "no_profile_data"})
        return False

    print(f"\n  Profile: @{profile.get('unique_id', TIKTOK_USERNAME)}")
    print(f"  Followers: {profile['followers']}, Videos: {profile['video_count']}, "
          f"Hearts: {profile['heart_count']}")
    print(f"  Videos scraped: {len(videos)}")

    # Step 1: Update posting_queue.json
    print(f"\n  Updating posting_queue.json...")
    queue_updated = update_queue_performance(videos)

    # Step 2: Append KPI
    print(f"\n  Appending to kpi_log.csv...")
    kpi_updated = append_kpi_with_videos(profile, videos)

    # Log the event
    log_event("analytics_update", {
        "profile": profile,
        "videos_found": len(videos),
        "queue_updated": queue_updated,
        "kpi_updated": kpi_updated,
    })

    # Slack summary
    total_views = compute_total_views(profile, videos)
    slack_notify(
        f"*TikTok Analytics Update*\n"
        f"Followers: {profile['followers']:,}\n"
        f"Videos: {profile['video_count']}\n"
        f"Total Views: {total_views:,}\n"
        f"Total Likes: {profile['heart_count']:,}\n"
        f"Videos scraped: {len(videos)}"
    )

    print("\nDone.")
    return True


def cmd_daily_kpi():
    """--daily-kpi: Just fetch profile and append KPI row."""
    profile, videos = fetch_tiktok_data()

    if not profile:
        print("[ERROR] Could not retrieve profile data")
        return False

    print(f"\n  Profile: followers={profile['followers']}, "
          f"videos={profile['video_count']}, hearts={profile['heart_count']}")

    result = append_kpi_with_videos(profile, videos)

    log_event("daily_kpi", {
        "profile": profile,
        "videos_found": len(videos),
    })

    print("\nDone.")
    return result


# ============================================================
# Main
# ============================================================

def main():
    load_env()

    parser = argparse.ArgumentParser(
        description="TikTok Analytics Collection - @robby15051"
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Show current TikTok profile stats and per-video metrics"
    )
    parser.add_argument(
        "--update", action="store_true",
        help="Update posting_queue.json performance + append KPI to CSV"
    )
    parser.add_argument(
        "--daily-kpi", action="store_true",
        help="Just append today's KPI row to kpi_log.csv"
    )

    args = parser.parse_args()

    if args.status:
        success = show_status()
        sys.exit(0 if success else 1)
    elif args.update:
        success = cmd_update()
        sys.exit(0 if success else 1)
    elif args.daily_kpi:
        success = cmd_daily_kpi()
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
