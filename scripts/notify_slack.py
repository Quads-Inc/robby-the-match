#!/usr/bin/env python3
"""
Slack通知スクリプト
台本JSONの内容をSlackに通知（承認依頼）
Bot Token使用版
"""

import argparse
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests

# プロジェクトルート
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

# Slack Bot Token
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID", "C08SKJBLW7A")

if not SLACK_BOT_TOKEN:
    print("❌ エラー: SLACK_BOT_TOKEN が.envに設定されていません")
    sys.exit(1)


def send_slack_notification(json_path: Path = None, message: str = None):
    """
    Slackに通知を送信

    Args:
        json_path: 台本JSONファイルパス（台本通知の場合）
        message: カスタムメッセージ（シンプル通知の場合）
    """
    if json_path:
        # 台本JSONを読み込んで詳細通知
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        content_id = data.get("id", "UNKNOWN")
        category = data.get("category", "不明")
        hook = data.get("hook", "")
        caption = data.get("caption", "")
        hashtags = " ".join(data.get("hashtags", []))
        slides = data.get("slides", [])
        base_image = data.get("base_image", "")

        # スライドパス
        today = json_path.stem.split('_')[0]  # JSONファイル名から日付を抽出
        slides_dir = project_root / "content" / "generated" / f"{today}_{content_id}"

        # Slack Block Kit形式で通知
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📱 ROBBY 投稿準備完了"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*ID:* {content_id}\n*カテゴリ:* {category}\n*フック:* {hook}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*キャプション:*\n{caption}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*ハッシュタグ:* {hashtags}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*ベース画像:* {base_image}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*スライド:* 6枚生成済み\n📂 `{slides_dir.relative_to(project_root)}`"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*6枚のテキスト:*"
                }
            }
        ]

        # 各スライドのテキストを追加
        for i, slide_text in enumerate(slides, start=1):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"`{i}枚目:` {slide_text}"
                }
            })

        payload = {"blocks": blocks}

    elif message:
        # シンプルなメッセージ通知
        payload = {"text": message}

    else:
        print("❌ エラー: --json または --message のいずれかが必要です")
        sys.exit(1)

    # Slackに送信（Bot Token使用）
    try:
        headers = {
            "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
            "Content-Type": "application/json"
        }

        # chat.postMessage APIエンドポイント
        if "blocks" in payload:
            payload["channel"] = SLACK_CHANNEL_ID

        response = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers=headers,
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            print("✅ Slack通知送信完了")
            if json_path:
                print(f"   ID: {content_id}")
            return True
        else:
            print(f"❌ Slack通知失敗: HTTP {response.status_code}")
            print(f"   レスポンス: {response.text}")
            return False

    except Exception as e:
        print(f"❌ エラー: {type(e).__name__}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Slackに通知を送信")
    parser.add_argument("--json", help="台本JSONファイルパス")
    parser.add_argument("--message", help="カスタムメッセージ")

    args = parser.parse_args()

    json_path = Path(args.json) if args.json else None
    message = args.message

    if json_path and not json_path.exists():
        print(f"❌ エラー: JSONファイルが見つかりません: {json_path}")
        sys.exit(1)

    success = send_slack_notification(json_path=json_path, message=message)

    if success:
        print("\n✅ 処理完了")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
