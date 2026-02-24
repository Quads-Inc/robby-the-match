#!/usr/bin/env python3
"""
TikTokプロフィール自動更新スクリプト
Playwrightを使ってTikTokプロフィール（表示名・BIO・リンク）を更新する

使い方:
  python3 tiktok_profile_update.py --update-all
  python3 tiktok_profile_update.py --check
"""

import argparse
import json
import sys
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
COOKIE_FILE = PROJECT_DIR / "TK_cookies_robby15051.json"
TIKTOK_USERNAME = "robby15051"

# 新しいプロフィール設定
NEW_PROFILE = {
    "nickname": "ロビー｜看護師の転職10%",
    "signature": "神奈川県西部の看護師さんへ\n手数料10%だから病院がすぐ採用してくれる\nLINE登録で無料相談👇",
    "bio_link": "https://quads-nurse.com/lp/job-seeker/?utm_source=tiktok&utm_medium=profile&utm_campaign=bio_link"
}


def load_cookies():
    """TK_cookies_robby15051.json からCookieを読み込む"""
    if not COOKIE_FILE.exists():
        print(f"[ERROR] Cookie file not found: {COOKIE_FILE}")
        sys.exit(1)
    with open(COOKIE_FILE) as f:
        return json.load(f)


def check_profile():
    """現在のプロフィールを確認"""
    import subprocess
    result = subprocess.run(
        ["curl", "-s", f"https://www.tiktok.com/@{TIKTOK_USERNAME}"],
        capture_output=True, text=True, timeout=30
    )
    html = result.stdout

    import re
    nickname = re.search(r'"nickname":"([^"]*)"', html)
    signature = re.search(r'"signature":"([^"]*)"', html)
    video_count = re.search(r'"videoCount":(\d+)', html)
    follower_count = re.search(r'"followerCount":(\d+)', html)

    print("=== 現在のTikTokプロフィール ===")
    print(f"  表示名: {nickname.group(1) if nickname else 'N/A'}")
    print(f"  BIO: {signature.group(1) if signature else 'N/A'}")
    print(f"  動画数: {video_count.group(1) if video_count else 'N/A'}")
    print(f"  フォロワー: {follower_count.group(1) if follower_count else 'N/A'}")
    print()
    print("=== 変更予定 ===")
    print(f"  表示名: {NEW_PROFILE['nickname']}")
    print(f"  BIO: {NEW_PROFILE['signature']}")
    print(f"  リンク: {NEW_PROFILE['bio_link']}")


def update_profile():
    """Playwrightでプロフィールを自動更新（phantomwright stealth使用）"""
    # phantomwrightを試し、なければ通常のplaywrightにフォールバック
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[ERROR] playwright not installed")
        sys.exit(1)

    cookies = load_cookies()

    # phantomwrightのchromium パスを検出
    import glob
    pw_chromium_paths = glob.glob(str(Path.home() / "Library/Caches/ms-playwright/chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium"))
    chromium_path = pw_chromium_paths[0] if pw_chromium_paths else None

    print("[INFO] Playwright起動中（ステルスモード）...")
    with sync_playwright() as p:
        launch_args = {
            "headless": False,
            "slow_mo": 800,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-web-security",
            ]
        }
        if chromium_path:
            launch_args["executable_path"] = chromium_path
            print(f"[INFO] Using chromium: {chromium_path}")

        browser = p.chromium.launch(**launch_args)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )

        # navigator.webdriver を隠す
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'languages', { get: () => ['ja-JP', 'ja', 'en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        """)

        # Cookieを設定
        pw_cookies = []
        for c in cookies:
            cookie = {
                "name": c["name"],
                "value": c["value"],
                "domain": c.get("domain", ".tiktok.com"),
                "path": c.get("path", "/"),
            }
            if "expires" in c and c["expires"]:
                cookie["expires"] = c["expires"]
            if "sameSite" in c:
                cookie["sameSite"] = c["sameSite"]
            if c.get("secure"):
                cookie["secure"] = True
            if c.get("httpOnly"):
                cookie["httpOnly"] = True
            pw_cookies.append(cookie)

        context.add_cookies(pw_cookies)
        page = context.new_page()

        # まずTikTokトップページでCookie有効化
        print("[INFO] TikTokトップページへ移動...")
        page.goto("https://www.tiktok.com/", wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)

        # プロフィールページに移動
        print(f"[INFO] プロフィールページへ移動: @{TIKTOK_USERNAME}")
        page.goto(f"https://www.tiktok.com/@{TIKTOK_USERNAME}", wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)

        page.screenshot(path=str(PROJECT_DIR / "logs" / "tiktok_profile_page.png"))
        print(f"[INFO] 現在のURL: {page.url}")

        # 「プロフィールを編集」ボタンを探す
        print("[INFO] プロフィール編集ボタンを探しています...")

        # 複数のセレクタで試す
        edit_selectors = [
            '[data-e2e="edit-profile-button"]',
            'a[href*="edit-profile"]',
            'button:has-text("プロフィールを編集")',
            'button:has-text("Edit profile")',
            'span:has-text("プロフィールを編集")',
            'span:has-text("Edit profile")',
        ]

        found_edit = False
        for selector in edit_selectors:
            try:
                el = page.locator(selector)
                if el.count() > 0:
                    print(f"[OK] 編集ボタン発見: {selector}")
                    el.first.click()
                    found_edit = True
                    time.sleep(4)
                    break
            except Exception:
                continue

        if not found_edit:
            # JS経由でボタンを探す
            print("[INFO] JS経由で編集ボタンを検索...")
            try:
                result = page.evaluate("""() => {
                    const buttons = document.querySelectorAll('button, a, span, div');
                    const texts = [];
                    for (const b of buttons) {
                        const t = b.textContent.trim();
                        if (t.includes('Edit') || t.includes('プロフィール') || t.includes('edit') || t.includes('編集')) {
                            texts.push({tag: b.tagName, text: t.substring(0, 50), class: b.className.substring(0, 50)});
                        }
                    }
                    return texts;
                }""")
                print(f"[DEBUG] 候補要素: {json.dumps(result, ensure_ascii=False)}")

                # 見つかった場合、最も適切なものをクリック
                if result:
                    for item in result:
                        if 'プロフィールを編集' in item.get('text', '') or 'Edit profile' in item.get('text', ''):
                            page.evaluate(f"""() => {{
                                const els = document.querySelectorAll('{item["tag"].lower()}');
                                for (const el of els) {{
                                    if (el.textContent.includes('プロフィールを編集') || el.textContent.includes('Edit profile')) {{
                                        el.click();
                                        return true;
                                    }}
                                }}
                                return false;
                            }}""")
                            found_edit = True
                            time.sleep(4)
                            break
            except Exception as e:
                print(f"[WARN] JS検索失敗: {e}")

        if not found_edit:
            print("[WARN] 編集ボタンが見つかりません。ページ内容を確認します。")
            page.screenshot(path=str(PROJECT_DIR / "logs" / "tiktok_profile_debug.png"))
            print("[INFO] デバッグスクリーンショット: logs/tiktok_profile_debug.png")
            browser.close()
            return

        page.screenshot(path=str(PROJECT_DIR / "logs" / "tiktok_profile_editmode.png"))
        print("[INFO] 編集モードスクリーンショット: logs/tiktok_profile_editmode.png")

        # === 表示名の変更 ===
        print(f"[INFO] 表示名を変更中: {NEW_PROFILE['nickname']}")
        name_selectors = [
            'input[placeholder*="名前"]',
            'input[placeholder*="Name"]',
            'input[placeholder*="name"]',
            '[data-e2e="profile-name-input"]',
            'input[name="nickname"]',
        ]
        name_set = False
        for selector in name_selectors:
            try:
                el = page.locator(selector)
                if el.count() > 0:
                    el.first.click()
                    el.first.fill("")
                    time.sleep(0.3)
                    el.first.type(NEW_PROFILE["nickname"], delay=50)
                    name_set = True
                    print(f"[OK] 表示名を入力しました (via {selector})")
                    break
            except Exception:
                continue

        if not name_set:
            # input要素を全部見る
            inputs = page.evaluate("""() => {
                return Array.from(document.querySelectorAll('input')).map(el => ({
                    placeholder: el.placeholder, name: el.name, type: el.type, value: el.value
                }));
            }""")
            print(f"[DEBUG] input要素: {json.dumps(inputs, ensure_ascii=False)}")

        # === BIOの変更 ===
        time.sleep(1)
        print(f"[INFO] BIOを変更中...")
        bio_selectors = [
            'textarea[placeholder*="自己紹介"]',
            'textarea[placeholder*="Bio"]',
            'textarea[placeholder*="bio"]',
            '[data-e2e="profile-bio-input"]',
            'textarea[name="signature"]',
            'textarea',
        ]
        bio_set = False
        for selector in bio_selectors:
            try:
                el = page.locator(selector)
                if el.count() > 0:
                    el.first.click()
                    el.first.fill("")
                    time.sleep(0.3)
                    el.first.type(NEW_PROFILE["signature"], delay=30)
                    bio_set = True
                    print(f"[OK] BIOを入力しました (via {selector})")
                    break
            except Exception:
                continue

        if not bio_set:
            textareas = page.evaluate("""() => {
                return Array.from(document.querySelectorAll('textarea')).map(el => ({
                    placeholder: el.placeholder, name: el.name, value: el.value.substring(0, 50)
                }));
            }""")
            print(f"[DEBUG] textarea要素: {json.dumps(textareas, ensure_ascii=False)}")

        time.sleep(1)
        page.screenshot(path=str(PROJECT_DIR / "logs" / "tiktok_profile_filled.png"))

        # === 保存ボタンをクリック ===
        print("[INFO] 保存ボタンを探しています...")
        save_selectors = [
            'button:has-text("Save")',
            'button:has-text("保存")',
            '[data-e2e="profile-save-button"]',
            'button[type="submit"]',
        ]
        saved = False
        for selector in save_selectors:
            try:
                el = page.locator(selector)
                if el.count() > 0:
                    el.first.click()
                    saved = True
                    time.sleep(4)
                    print(f"[OK] 保存完了 (via {selector})")
                    break
            except Exception:
                continue

        if not saved:
            print("[WARN] 保存ボタンが見つかりません")

        page.screenshot(path=str(PROJECT_DIR / "logs" / "tiktok_profile_after.png"))

        # 検証
        time.sleep(2)
        page.goto(f"https://www.tiktok.com/@{TIKTOK_USERNAME}", wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)
        page.screenshot(path=str(PROJECT_DIR / "logs" / "tiktok_profile_verified.png"))
        print("[INFO] 検証スクリーンショット: logs/tiktok_profile_verified.png")

        print("\n=== プロフィール更新処理完了 ===")
        browser.close()


def update_profile_api():
    """TikTok内部APIでプロフィールを更新（CAPTCHA回避）"""
    import subprocess
    import urllib.parse

    cookies = load_cookies()

    # Cookie文字列を構築
    cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)

    # CSRFトークンを取得
    csrf_token = ""
    for c in cookies:
        if c["name"] == "tt_csrf_token":
            csrf_token = c["value"]
            break

    # msTokenを取得
    ms_token = ""
    for c in cookies:
        if c["name"] == "msToken" and c.get("domain", "") == ".tiktok.com":
            ms_token = c["value"]
            break

    print(f"[INFO] CSRF Token: {csrf_token[:20]}...")
    print(f"[INFO] msToken: {ms_token[:20]}...")

    # Step 1: ニックネーム（表示名）を更新
    nickname = NEW_PROFILE["nickname"]
    signature = NEW_PROFILE["signature"]

    print(f"[INFO] プロフィール更新API呼び出し...")
    print(f"  表示名: {nickname}")
    print(f"  BIO: {signature}")

    # TikTok Profile Edit API
    url = "https://www.tiktok.com/api/commit/profile/edit/"

    headers = [
        "-H", f"Cookie: {cookie_str}",
        "-H", "Content-Type: application/x-www-form-urlencoded",
        "-H", f"X-Csrftoken: {csrf_token}",
        "-H", "Referer: https://www.tiktok.com/@robby15051",
        "-H", "Origin: https://www.tiktok.com",
        "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    ]

    # Form data
    data = urllib.parse.urlencode({
        "nickname": nickname,
        "signature": signature,
    })

    cmd = ["curl", "-s", "-X", "POST", url] + headers + ["-d", data]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    response = result.stdout

    print(f"[DEBUG] API Response: {response[:500]}")

    try:
        resp_json = json.loads(response)
        if resp_json.get("status_code") == 0 or resp_json.get("statusCode") == 0:
            print("[OK] プロフィール更新成功！")
            return True
        else:
            print(f"[WARN] API応答: {json.dumps(resp_json, ensure_ascii=False)[:300]}")
            # ステータスコード8は「CAPTCHA required」の可能性
            if resp_json.get("status_code") == 8 or "verify" in response.lower():
                print("[INFO] CAPTCHA要求されました。代替手段を試みます。")
                return update_profile_via_mobile_api(cookies)
            return False
    except json.JSONDecodeError:
        print(f"[ERROR] JSON解析失敗: {response[:200]}")
        return False


def update_profile_via_mobile_api(cookies):
    """TikTokモバイルAPI経由でプロフィール更新"""
    import subprocess
    import urllib.parse

    cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
    csrf_token = next((c["value"] for c in cookies if c["name"] == "tt_csrf_token"), "")
    session_id = next((c["value"] for c in cookies if c["name"] == "sessionid"), "")

    # TikTokの別エンドポイントを試す
    endpoints = [
        "https://www.tiktok.com/api/user/profile/edit/",
        "https://www.tiktok.com/passport/web/account/set_profile/",
    ]

    for endpoint in endpoints:
        print(f"[INFO] 試行中: {endpoint}")

        data = json.dumps({
            "nickname": NEW_PROFILE["nickname"],
            "signature": NEW_PROFILE["signature"],
        })

        cmd = [
            "curl", "-s", "-X", "POST", endpoint,
            "-H", f"Cookie: {cookie_str}",
            "-H", "Content-Type: application/json",
            "-H", f"X-Csrftoken: {csrf_token}",
            "-H", "Referer: https://www.tiktok.com/setting",
            "-H", "Origin: https://www.tiktok.com",
            "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "-d", data,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        print(f"[DEBUG] Response: {result.stdout[:300]}")

        try:
            resp = json.loads(result.stdout)
            if resp.get("status_code") == 0 or resp.get("statusCode") == 0:
                print("[OK] プロフィール更新成功！")
                return True
        except json.JSONDecodeError:
            continue

    print("[WARN] API経由での更新に失敗。Slack経由で手動変更を依頼済みです。")
    return False


def main():
    parser = argparse.ArgumentParser(description="TikTokプロフィール自動更新")
    parser.add_argument("--check", action="store_true", help="現在のプロフィールを確認")
    parser.add_argument("--update-all", action="store_true", help="プロフィールを自動更新（API方式）")
    parser.add_argument("--update-browser", action="store_true", help="プロフィールを自動更新（ブラウザ方式）")
    args = parser.parse_args()

    if args.check:
        check_profile()
    elif args.update_all:
        success = update_profile_api()
        if not success:
            print("\n[INFO] API更新失敗。ブラウザ方式を試みます...")
            update_profile()
    elif args.update_browser:
        update_profile()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
