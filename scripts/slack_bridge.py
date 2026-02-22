#!/usr/bin/env python3
"""
Slack Bridge — ナースロビー エージェントチーム双方向連携

エージェントセッション用の統合Slackインターフェース。
起動時に呼び出して受信メッセージを確認、作業中に進捗報告、終了時にサマリ送信。

使い方:
  python3 slack_bridge.py --start              # セッション開始（受信確認+開始通知）
  python3 slack_bridge.py --inbox              # 未読メッセージを表示
  python3 slack_bridge.py --send "メッセージ"   # メッセージ送信
  python3 slack_bridge.py --end "作業サマリ"    # セッション終了通知
  python3 slack_bridge.py --instructions       # 未処理の指示キューを表示
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
import requests

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID", "C09A7U4TV4G")
LAST_TS_FILE = PROJECT_ROOT / "data" / ".slack_last_ts"
INSTRUCTIONS_FILE = PROJECT_ROOT / "data" / "slack_instructions.json"

if not SLACK_BOT_TOKEN:
    print("ERROR: SLACK_BOT_TOKEN が .env に未設定")
    sys.exit(1)


def _headers():
    return {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json",
    }


def _post_message(text: str, blocks: list = None) -> bool:
    """Slackにメッセージ送信"""
    payload = {"channel": SLACK_CHANNEL_ID, "text": text}
    if blocks:
        payload["blocks"] = blocks
    try:
        resp = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers=_headers(),
            json=payload,
            timeout=15,
        )
        data = resp.json()
        if not data.get("ok"):
            print(f"Slack送信エラー: {data.get('error')}", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"Slack接続エラー: {e}", file=sys.stderr)
        return False


def _get_messages(oldest: str = None, limit: int = 20) -> list:
    """チャンネルのメッセージ取得"""
    params = {"channel": SLACK_CHANNEL_ID, "limit": limit}
    if oldest:
        params["oldest"] = oldest
    try:
        resp = requests.get(
            "https://slack.com/api/conversations.history",
            headers=_headers(),
            params=params,
            timeout=10,
        )
        data = resp.json()
        if data.get("ok"):
            return data.get("messages", [])
        print(f"メッセージ取得エラー: {data.get('error')}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"接続エラー: {e}", file=sys.stderr)
        return []


def _get_user_name(user_id: str) -> str:
    """ユーザーIDから表示名を取得"""
    try:
        resp = requests.get(
            "https://slack.com/api/users.info",
            headers=_headers(),
            params={"user": user_id},
            timeout=10,
        )
        data = resp.json()
        if data.get("ok"):
            user = data["user"]
            return user.get("real_name") or user.get("name") or user_id
    except Exception:
        pass
    return user_id


def _load_last_ts() -> str:
    """前回チェック時のタイムスタンプ"""
    LAST_TS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if LAST_TS_FILE.exists():
        return LAST_TS_FILE.read_text().strip()
    return ""


def _save_last_ts(ts: str):
    """タイムスタンプ保存"""
    LAST_TS_FILE.parent.mkdir(parents=True, exist_ok=True)
    LAST_TS_FILE.write_text(ts)


def _load_instructions() -> list:
    """指示キュー読み込み"""
    if INSTRUCTIONS_FILE.exists():
        try:
            data = json.loads(INSTRUCTIONS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data.get("instructions", [])
            if isinstance(data, list):
                return data
            return []
        except (json.JSONDecodeError, Exception):
            return []
    return []


def _save_instructions(instructions: list):
    """指示キュー保存"""
    INSTRUCTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    INSTRUCTIONS_FILE.write_text(
        json.dumps(instructions, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ===================================================================
# コマンド
# ===================================================================


def cmd_inbox():
    """未読メッセージを表示（Bot自身のメッセージは除外）"""
    last_ts = _load_last_ts()
    messages = _get_messages(oldest=last_ts if last_ts else None, limit=30)

    # Bot自身のメッセージを除外、古い順にソート
    human_msgs = [
        m for m in messages
        if not m.get("bot_id") and m.get("subtype") != "bot_message"
    ]
    human_msgs.reverse()  # 古い順

    if not human_msgs:
        print("--- Slack受信: 新規メッセージなし ---")
        # タイムスタンプだけ更新
        if messages:
            _save_last_ts(messages[0].get("ts", ""))
        return []

    print(f"--- Slack受信: {len(human_msgs)}件の新規メッセージ ---")
    result = []
    for msg in human_msgs:
        user = msg.get("user", "?")
        text = msg.get("text", "").strip()
        ts = msg.get("ts", "")
        dt = datetime.fromtimestamp(float(ts)).strftime("%m/%d %H:%M") if ts else "?"
        # メンション除去して表示
        clean_text = text
        for tag in ["<@U09AAL90EGH>", "<@U09AAL90EGH> "]:
            clean_text = clean_text.replace(tag, "").strip()
        print(f"  [{dt}] {clean_text}")
        result.append({"user": user, "text": clean_text, "ts": ts})

    # タイムスタンプ更新（最新のメッセージ）
    if messages:
        _save_last_ts(messages[0].get("ts", ""))

    print("---")
    return result


def cmd_instructions():
    """未処理の指示キューを表示"""
    instructions = _load_instructions()
    pending = [i for i in instructions if i.get("status") == "pending"]

    if not pending:
        print("--- 指示キュー: 未処理なし ---")
        return []

    print(f"--- 指示キュー: {len(pending)}件 ---")
    for inst in pending:
        print(f"  [{inst.get('id')}] {inst.get('text', '')[:80]}")
    print("---")
    return pending


def cmd_send(message: str) -> bool:
    """メッセージ送信"""
    success = _post_message(message)
    if success:
        print(f"Slack送信OK: {message[:50]}...")
    return success


def cmd_start():
    """セッション開始: 受信確認 + 開始通知"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 受信メッセージ確認
    new_msgs = cmd_inbox()

    # 指示キュー確認
    pending = cmd_instructions()

    # 未処理メッセージを指示キューに追加
    instructions = _load_instructions()
    for msg in new_msgs:
        text = msg["text"]
        # 既にキューにある場合はスキップ
        if any(i.get("text") == text for i in instructions):
            continue
        # コマンド(!status等)はキューに入れない
        if text.startswith("!"):
            continue
        if text:
            instructions.append({
                "id": len(instructions) + 1,
                "text": text,
                "user": msg.get("user", "unknown"),
                "timestamp": msg.get("ts", ""),
                "status": "pending",
            })
    _save_instructions(instructions)

    # 開始通知をSlackに送信
    pending_count = len([i for i in instructions if i.get("status") == "pending"])
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "ROBBY参謀 セッション開始"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*開始時刻:* {now}\n"
                    f"*未処理指示:* {pending_count}件\n"
                    f"*新着メッセージ:* {len(new_msgs)}件\n\n"
                    "作業を開始します。完了後にレポートを送信します。"
                ),
            },
        },
    ]
    _post_message("ROBBY参謀 セッション開始", blocks=blocks)

    # 未処理指示をまとめて表示（エージェントが処理できるように）
    if pending_count > 0:
        pending_all = [i for i in instructions if i.get("status") == "pending"]
        print(f"\n=== 処理すべき指示 ({pending_count}件) ===")
        for inst in pending_all:
            print(f"  #{inst['id']}: {inst['text']}")
        print("===")


def cmd_end(summary: str):
    """セッション終了通知"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "ROBBY参謀 セッション完了"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*完了時刻:* {now}\n\n*作業サマリ:*\n{summary}",
            },
        },
    ]
    success = _post_message("ROBBY参謀 セッション完了", blocks=blocks)

    # 処理済み指示をマーク
    instructions = _load_instructions()
    for inst in instructions:
        if inst.get("status") == "pending":
            inst["status"] = "done"
    _save_instructions(instructions)

    if success:
        print("セッション終了通知 送信完了")


def cmd_complete_instruction(instruction_id: int):
    """特定の指示を完了済みにする"""
    instructions = _load_instructions()
    for inst in instructions:
        if inst.get("id") == instruction_id:
            inst["status"] = "done"
            _save_instructions(instructions)
            print(f"指示 #{instruction_id} を完了済みにしました")
            return
    print(f"指示 #{instruction_id} が見つかりません")


# ===================================================================
# メイン
# ===================================================================

def main():
    parser = argparse.ArgumentParser(
        description="ナースロビー Slack Bridge — エージェントチーム双方向連携"
    )
    parser.add_argument("--start", action="store_true", help="セッション開始（受信確認+通知）")
    parser.add_argument("--inbox", action="store_true", help="未読メッセージ表示")
    parser.add_argument("--send", type=str, help="メッセージ送信")
    parser.add_argument("--end", type=str, help="セッション終了（サマリ付き）")
    parser.add_argument("--instructions", action="store_true", help="指示キュー表示")
    parser.add_argument("--complete", type=int, help="指示を完了済みにする（ID指定）")

    args = parser.parse_args()

    if args.start:
        cmd_start()
    elif args.inbox:
        cmd_inbox()
    elif args.send:
        cmd_send(args.send)
    elif args.end:
        cmd_end(args.end)
    elif args.instructions:
        cmd_instructions()
    elif args.complete is not None:
        cmd_complete_instruction(args.complete)
    else:
        # 引数なし → セッション開始として扱う
        cmd_start()


if __name__ == "__main__":
    main()
