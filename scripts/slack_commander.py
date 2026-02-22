#!/usr/bin/env python3
"""
Slack Commander v3.0 — ナースロビー
Slackチャンネルからのメッセージを監視し、コマンド実行 & 指示受けを行う。

対応コマンド:
  !status   → 現在のプロジェクト状態をSlackに報告
  !kpi      → KPIダッシュボードを送信
  !content  → 今日のコンテンツ生成状態を報告
  !seo      → SEOページの状態を報告
  !site     → サイトページ数・リンク数を報告
  !team     → チーム別作業レポートを送信
  !push     → git commit & push を実行
  !deploy   → デプロイ手順を案内
  !generate → コンテンツ生成タスクを作成
  !queue    → 投稿キュー状態を表示
  !agents   → Agent Team状態一覧を表示
  !tasks    → 指示キューの一覧を表示
  !clear    → 指示キューをクリア
  !help     → コマンド一覧を表示

自由文メッセージ:
  !コマンド以外のメッセージ → 指示キューに保存（後でClaude Codeが処理）

使い方:
  python3 slack_commander.py --poll                    # 常駐ポーリング
  python3 slack_commander.py --poll --interval 30      # 30秒間隔
  python3 slack_commander.py --once                    # 1回チェックして終了（cron用）
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path

from dotenv import load_dotenv
import requests

# プロジェクトルート
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

# Slack設定
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID", "C09A7U4TV4G")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN", "")

# 指示キューファイル
INSTRUCTIONS_FILE = project_root / "data" / "slack_instructions.json"
LAST_TS_FILE = project_root / "data" / ".slack_last_ts"

if not SLACK_BOT_TOKEN:
    print("エラー: SLACK_BOT_TOKEN が.envに設定されていません")
    sys.exit(1)


# ===================================================================
# Slack API ヘルパー
# ===================================================================

def post_message(channel: str, text: str = "", blocks: list = None) -> bool:
    """Slackにメッセージを送信"""
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"channel": channel}
    if blocks:
        payload["blocks"] = blocks
        payload["text"] = text or "ナースロビー"
    else:
        payload["text"] = text

    try:
        resp = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers=headers,
            json=payload,
            timeout=15,
        )
        data = resp.json()
        if data.get("ok"):
            return True
        else:
            print(f"Slack APIエラー: {data.get('error')}")
            return False
    except Exception as e:
        print(f"送信エラー: {e}")
        return False


def post_reply(channel: str, thread_ts: str, text: str) -> bool:
    """スレッドに返信"""
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "channel": channel,
        "text": text,
        "thread_ts": thread_ts,
    }
    try:
        resp = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers=headers,
            json=payload,
            timeout=15,
        )
        return resp.json().get("ok", False)
    except Exception:
        return False


def get_conversation_history(channel: str, oldest: str = None, limit: int = 10) -> list:
    """チャンネルの直近メッセージを取得"""
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json",
    }
    params = {"channel": channel, "limit": limit}
    if oldest:
        params["oldest"] = oldest

    try:
        resp = requests.get(
            "https://slack.com/api/conversations.history",
            headers=headers,
            params=params,
            timeout=10,
        )
        data = resp.json()
        if data.get("ok"):
            return data.get("messages", [])
        else:
            print(f"conversations.history エラー: {data.get('error')}")
            return []
    except Exception as e:
        print(f"取得エラー: {e}")
        return []


# ===================================================================
# 指示キュー管理
# ===================================================================

def load_instructions() -> list:
    """指示キューを読み込み（dict/list両対応）"""
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


def save_instructions(instructions: list):
    """指示キューを保存"""
    INSTRUCTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    INSTRUCTIONS_FILE.write_text(
        json.dumps(instructions, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def add_instruction(text: str, user: str = "unknown"):
    """指示をキューに追加"""
    instructions = load_instructions()
    instructions.append({
        "id": len(instructions) + 1,
        "text": text,
        "user": user,
        "timestamp": datetime.now().isoformat(),
        "status": "pending",
    })
    save_instructions(instructions)
    return len(instructions)


def load_last_ts() -> str:
    """最後に処理したタイムスタンプを読み込み"""
    if LAST_TS_FILE.exists():
        return LAST_TS_FILE.read_text().strip()
    return str(time.time())


def save_last_ts(ts: str):
    """最後に処理したタイムスタンプを保存"""
    LAST_TS_FILE.parent.mkdir(parents=True, exist_ok=True)
    LAST_TS_FILE.write_text(ts)


# ===================================================================
# コマンドハンドラー
# ===================================================================

def handle_status(channel: str, **kwargs):
    """!status — 現在のプロジェクト状態を報告"""
    report_script = project_root / "scripts" / "slack_report.py"
    if report_script.exists():
        result = subprocess.run(
            [sys.executable, str(report_script), "--report", "daily"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return
        else:
            post_message(channel, text=f"レポート生成エラー:\n```{result.stderr[:500]}```")
            return

    post_message(channel, text="slack_report.py が見つかりません。")


def handle_kpi(channel: str, **kwargs):
    """!kpi — KPIダッシュボードを送信"""
    _run_report(channel, "kpi")


def handle_content(channel: str, **kwargs):
    """!content — 今日のコンテンツ生成状態を報告"""
    _run_report(channel, "content")


def handle_seo(channel: str, **kwargs):
    """!seo — SEOページの状態を報告"""
    _run_report(channel, "seo")


def handle_team(channel: str, **kwargs):
    """!team — チーム別レポートを送信"""
    _run_report(channel, "team")


def _run_report(channel: str, report_type: str):
    """slack_report.py を呼び出してレポート送信"""
    report_script = project_root / "scripts" / "slack_report.py"
    if report_script.exists():
        result = subprocess.run(
            [sys.executable, str(report_script), "--report", report_type],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return
        else:
            post_message(channel, text=f"{report_type}レポート生成エラー:\n```{result.stderr[:500]}```")
            return
    post_message(channel, text="slack_report.py が見つかりません。")


def handle_site(channel: str, **kwargs):
    """!site — サイトのページ数・構成を報告"""
    counts = {}
    total = 0
    for subdir in ["area", "guide", "blog"]:
        path = project_root / subdir
        if path.exists():
            htmls = list(path.rglob("*.html"))
            counts[subdir] = len(htmls)
            total += len(htmls)

    # ルート直下のHTML
    root_htmls = list(project_root.glob("*.html"))
    counts["root"] = len(root_htmls)
    total += len(root_htmls)

    # sitemap
    sitemap = project_root / "sitemap.xml"
    sitemap_count = 0
    if sitemap.exists():
        content = sitemap.read_text(encoding="utf-8")
        sitemap_count = content.count("<loc>")

    # 指示キュー
    instructions = load_instructions()
    pending = [i for i in instructions if i.get("status") == "pending"]

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "ナースロビー サイト構成レポート"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*HTMLファイル合計:* {total} ページ\n"
                    + "\n".join(f"  - `{k}/`: {v} ページ" for k, v in counts.items())
                    + f"\n\n*sitemap.xml:* {sitemap_count} URL"
                    + f"\n*指示キュー:* {len(pending)} 件 pending"
                ),
            },
        },
    ]
    post_message(channel, blocks=blocks, text="サイト構成レポート")


def handle_push(channel: str, **kwargs):
    """!push — git add, commit, push を実行"""
    try:
        # status確認
        status = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, cwd=str(project_root), timeout=10,
        )
        changes = status.stdout.strip()

        if not changes:
            post_message(channel, text="変更なし。pushするものがありません。")
            return

        # add & commit
        subprocess.run(
            ["git", "add", "-A"],
            cwd=str(project_root), timeout=10,
        )
        commit_msg = f"auto: Slack Commander push ({date.today().isoformat()})"
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            capture_output=True, text=True, cwd=str(project_root), timeout=15,
        )

        # push to both main and master
        push_result = subprocess.run(
            ["git", "push", "origin", "main:master"],
            capture_output=True, text=True, cwd=str(project_root), timeout=30,
        )

        if push_result.returncode == 0:
            file_count = len(changes.splitlines())
            post_message(channel, text=f"git push 完了 ({file_count} ファイル変更)\n```{changes[:500]}```")
        else:
            post_message(channel, text=f"git push エラー:\n```{push_result.stderr[:500]}```")
    except Exception as e:
        post_message(channel, text=f"push エラー: {e}")


def handle_tasks(channel: str, **kwargs):
    """!tasks — 指示キューの一覧を表示"""
    instructions = load_instructions()

    if not instructions:
        post_message(channel, text="指示キューは空です。")
        return

    pending = [i for i in instructions if i.get("status") == "pending"]
    done = [i for i in instructions if i.get("status") == "done"]

    lines = []
    for inst in pending[-10:]:  # 直近10件
        lines.append(f"  [{inst['id']}] {inst['text'][:60]}")

    text = (
        f"*指示キュー*\n"
        f"pending: {len(pending)} 件 / 完了: {len(done)} 件\n\n"
        + ("*直近の未処理指示:*\n" + "\n".join(lines) if lines else "未処理の指示はありません。")
    )

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "指示キュー"},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": text},
        },
    ]
    post_message(channel, blocks=blocks, text="指示キュー")


def handle_clear(channel: str, **kwargs):
    """!clear — 指示キューをクリア"""
    instructions = load_instructions()
    # pending を全て done に
    for inst in instructions:
        if inst.get("status") == "pending":
            inst["status"] = "done"
    save_instructions(instructions)
    post_message(channel, text="指示キューをクリアしました。")


def handle_deploy(channel: str, **kwargs):
    """!deploy — デプロイ手順を案内"""
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "デプロイ手順ガイド"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*GitHub Pages デプロイ:*\n"
                    "```\n"
                    "git add -A && git commit -m 'deploy'\n"
                    "git push origin main:master\n"
                    "```\n"
                    "または Slackで `!push` を送信\n\n"
                    "*確認:*\n"
                    "  https://haruhi-medical.github.io/robby-the-match/"
                ),
            },
        },
    ]
    post_message(channel, blocks=blocks, text="デプロイ手順ガイド")


def handle_generate(channel: str, **kwargs):
    """!generate — コンテンツ生成タスクを作成"""
    agent_state_file = project_root / "data" / "agent_state.json"
    try:
        with open(agent_state_file) as f:
            state = json.load(f)
        tasks = state.setdefault("pendingTasks", {}).setdefault("content_creator", [])
        # 既存のpendingタスクがあるか確認
        has_pending = any(t.get("status") == "pending" for t in tasks)
        if has_pending:
            post_message(channel, text="既にコンテンツ生成タスクがキューにあります。次回cron 15:00で実行されます。")
            return
        tasks.append({
            "from": "slack_user",
            "type": "generate_batch",
            "details": "Slackから手動リクエスト",
            "created": datetime.now().isoformat(),
            "status": "pending",
        })
        with open(agent_state_file, "w") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        post_message(channel, text="コンテンツ生成タスクを作成しました。次回のcron 15:00で実行されます。")
    except Exception as e:
        post_message(channel, text=f"タスク作成エラー: {e}")


def handle_queue(channel: str, **kwargs):
    """!queue — 投稿キューの状態を表示"""
    queue_file = project_root / "data" / "posting_queue.json"
    try:
        with open(queue_file) as f:
            q = json.load(f)
        posts = q.get("posts", [])
        posted = sum(1 for p in posts if p["status"] == "posted")
        pending = sum(1 for p in posts if p["status"] == "pending")
        failed = sum(1 for p in posts if p["status"] == "failed")
        total = len(posts)
        days_remaining = pending  # 1 post/day

        # 直近の投稿
        recent = [p for p in posts if p["status"] == "posted"]
        recent_lines = ""
        for p in recent[-3:]:
            cid = p.get("content_id", "?")
            date = (p.get("posted_at") or "")[:10]
            recent_lines += f"\n  {cid} ({date})"

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "投稿キュー状態"},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*合計:* {total}件\n"
                        f"  :white_check_mark: 投稿済み: {posted}件\n"
                        f"  :hourglass: 待機中: {pending}件\n"
                        f"  :x: 失敗: {failed}件\n\n"
                        f"*残り日数:* 約{days_remaining}日分"
                        + (f"\n\n*直近の投稿:*{recent_lines}" if recent_lines else "")
                        + ("\n\n:warning: *キュー残り少！* `!generate` でコンテンツ追加を" if pending < 5 else "")
                    ),
                },
            },
        ]
        post_message(channel, blocks=blocks, text="投稿キュー状態")
    except Exception as e:
        post_message(channel, text=f"キュー読み込みエラー: {e}")


def handle_agents(channel: str, **kwargs):
    """!agents — 全エージェント状態一覧"""
    agent_state_file = project_root / "data" / "agent_state.json"
    try:
        with open(agent_state_file) as f:
            state = json.load(f)

        status_emoji = {
            "completed": ":white_check_mark:",
            "running": ":arrows_counterclockwise:",
            "failed": ":x:",
            "pending": ":hourglass:",
        }
        agent_names = {
            "seo_optimizer": "SEO Optimizer (04:00)",
            "health_monitor": "Health Monitor (07:00)",
            "competitor_analyst": "Competitor (10:00)",
            "content_creator": "Content Creator (15:00)",
            "sns_poster": "SNS Poster (17:30)",
            "daily_reviewer": "Daily Reviewer (23:00)",
            "weekly_strategist": "Weekly (日曜06:00)",
            "slack_commander": "Slack Commander (*/5分)",
        }

        lines = []
        for agent_id, display_name in agent_names.items():
            s = state.get("status", {}).get(agent_id, "unknown")
            emoji = status_emoji.get(s, ":question:")
            last_run = state.get("lastRun", {}).get(agent_id)
            if last_run:
                last_str = last_run[:16].replace("T", " ")
            else:
                last_str = "未実行"
            lines.append(f"{emoji} *{display_name}*\n      {s} | last: {last_str}")

        # pendingTasks count
        pending_tasks = state.get("pendingTasks", {})
        task_count = sum(
            sum(1 for t in tasks if t.get("status") == "pending")
            for tasks in pending_tasks.values()
        )

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Agent Team 状態"},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "\n".join(lines) + f"\n\n*未処理タスク:* {task_count}件",
                },
            },
        ]
        post_message(channel, blocks=blocks, text="Agent Team 状態")
    except Exception as e:
        post_message(channel, text=f"エージェント状態読み込みエラー: {e}")


def handle_help(channel: str, **kwargs):
    """!help — コマンド一覧を表示"""
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "ナースロビー Commander v3.0"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*レポート系:*\n"
                    "  `!status`  — 日次レポート\n"
                    "  `!kpi`     — KPIダッシュボード\n"
                    "  `!content` — コンテンツ生成状態\n"
                    "  `!seo`     — SEOページ状態\n"
                    "  `!site`    — サイト構成レポート\n"
                    "  `!team`    — チーム別レポート\n\n"
                    "*アクション系:*\n"
                    "  `!push`     — git push を実行\n"
                    "  `!deploy`   — デプロイ手順\n"
                    "  `!generate` — コンテンツ生成を要求\n\n"
                    "*モニタリング:*\n"
                    "  `!queue`   — 投稿キュー状態\n"
                    "  `!agents`  — Agent Team状態一覧\n\n"
                    "*指示キュー:*\n"
                    "  `!tasks`   — 指示一覧\n"
                    "  `!clear`   — 指示キュークリア\n\n"
                    "*自由文メッセージ:*\n"
                    "  `!`なしのメッセージ → 指示キューに保存\n"
                    "  → Claude Code が次回起動時に処理します"
                ),
            },
        },
    ]
    post_message(channel, blocks=blocks, text="コマンド一覧")


# コマンドマップ
COMMANDS = {
    "!status": handle_status,
    "!kpi": handle_kpi,
    "!content": handle_content,
    "!seo": handle_seo,
    "!site": handle_site,
    "!team": handle_team,
    "!push": handle_push,
    "!deploy": handle_deploy,
    "!generate": handle_generate,
    "!queue": handle_queue,
    "!agents": handle_agents,
    "!tasks": handle_tasks,
    "!clear": handle_clear,
    "!help": handle_help,
}


# ===================================================================
# メッセージ処理
# ===================================================================

def process_message(message: dict, channel: str):
    """メッセージを解析してコマンドを実行、または指示キューに保存"""
    text = message.get("text", "").strip()
    user = message.get("user", "unknown")
    ts = message.get("ts", "")

    # Bot自身のメッセージは無視
    if message.get("bot_id") or message.get("subtype") == "bot_message":
        return

    # 空メッセージ無視
    if not text:
        return

    # コマンド検出
    for cmd, handler in COMMANDS.items():
        if text.lower().startswith(cmd):
            print(f"[{datetime.now().strftime('%H:%M:%S')}] コマンド: {cmd} (user={user})")
            handler(channel, user=user, ts=ts)
            return

    # !で始まらない自由文 → 指示キューに保存
    if not text.startswith("!"):
        idx = add_instruction(text, user=user)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 指示保存: #{idx} '{text[:50]}...'")
        post_reply(
            channel, ts,
            f"指示を受け付けました (#{idx})\nClaude Codeが次回処理します。"
        )


# ===================================================================
# ポーリングモード
# ===================================================================

def run_polling(channel: str, interval: int = 30):
    """常駐ポーリングモード"""
    print(f"ナースロビー Commander v3.0 起動 (ポーリング, {interval}秒間隔)")
    print(f"監視チャンネル: {channel}")
    print("終了: Ctrl+C")
    print("---")

    last_ts = load_last_ts()
    processed_ts = set()

    while True:
        try:
            messages = get_conversation_history(channel, oldest=last_ts, limit=10)
            for msg in reversed(messages):
                ts = msg.get("ts", "")
                if ts in processed_ts:
                    continue
                processed_ts.add(ts)
                process_message(msg, channel)

            if len(processed_ts) > 500:
                processed_ts.clear()

            if messages:
                newest_ts = messages[0].get("ts", last_ts)
                last_ts = newest_ts
                save_last_ts(last_ts)

            time.sleep(interval)

        except KeyboardInterrupt:
            print("\nCommander 終了")
            save_last_ts(last_ts)
            break
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] エラー: {e}")
            time.sleep(interval * 2)


def run_once(channel: str):
    """1回チェックして終了（cron用）"""
    last_ts = load_last_ts()
    messages = get_conversation_history(channel, oldest=last_ts, limit=20)

    processed = 0
    for msg in reversed(messages):
        process_message(msg, channel)
        processed += 1

    if messages:
        newest_ts = messages[0].get("ts", last_ts)
        save_last_ts(newest_ts)

    if processed > 0:
        print(f"処理: {processed} メッセージ")
    else:
        print("新規メッセージなし")


# ===================================================================
# メイン
# ===================================================================

def main():
    parser = argparse.ArgumentParser(
        description="ナースロビー Commander v3.0 — Slack監視 & コマンド応答 & 指示受け"
    )
    parser.add_argument("--poll", action="store_true", help="常駐ポーリングモード")
    parser.add_argument("--once", action="store_true", help="1回チェックして終了（cron用）")
    parser.add_argument("--interval", type=int, default=30, help="ポーリング間隔（秒）")
    parser.add_argument("--channel", default=SLACK_CHANNEL_ID, help="監視チャンネルID")

    args = parser.parse_args()

    if args.once:
        run_once(channel=args.channel)
    elif args.poll:
        run_polling(channel=args.channel, interval=args.interval)
    else:
        # デフォルトはポーリングモード
        run_polling(channel=args.channel, interval=args.interval)


if __name__ == "__main__":
    main()
