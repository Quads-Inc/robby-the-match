#!/usr/bin/env python3
"""
Slack報告スクリプト — ナースロビー
6チームのエージェント作業結果をSlackに報告
PROGRESS.mdの内容をフォーマットして送信
SEO子ページの作成状況を報告
KPIダッシュボードの自動送信
Block Kit形式でリッチな表示
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, date
from pathlib import Path

from dotenv import load_dotenv
import requests

# プロジェクトルート
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

# Slack設定
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID", "C09A7U4TV4G")

if not SLACK_BOT_TOKEN:
    print("エラー: SLACK_BOT_TOKEN が.envに設定されていません")
    sys.exit(1)

PROGRESS_MD = project_root / "PROGRESS.md"
KPI_LOG_CSV = project_root / "data" / "kpi_log.csv"
CONTENT_DIR = project_root / "content" / "generated"
SEO_DIR = project_root / "lp"


# ===================================================================
# ユーティリティ
# ===================================================================

def post_to_slack(blocks: list, text: str = "ナースロビー レポート") -> bool:
    """Block Kit形式でSlackにメッセージを送信"""
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "channel": SLACK_CHANNEL_ID,
        "text": text,
        "blocks": blocks,
    }
    try:
        resp = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers=headers,
            json=payload,
            timeout=15,
        )
        data = resp.json()
        if data.get("ok"):
            print(f"Slack送信成功 (channel={SLACK_CHANNEL_ID})")
            return True
        else:
            print(f"Slack APIエラー: {data.get('error', 'unknown')}")
            return False
    except Exception as e:
        print(f"送信エラー: {type(e).__name__}: {e}")
        return False


def truncate(text: str, max_len: int = 2900) -> str:
    """Block Kitのテキスト上限を超えないようにトリミング"""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


# ===================================================================
# PROGRESS.md パーサー
# ===================================================================

def parse_progress_md() -> dict:
    """PROGRESS.mdを読み込み、構造化して返す"""
    if not PROGRESS_MD.exists():
        return {"kpi_table": "", "today_section": "", "raw": ""}

    raw = PROGRESS_MD.read_text(encoding="utf-8")
    today_str = date.today().strftime("%Y-%m-%d")

    # KPIダッシュボード抽出
    kpi_match = re.search(
        r"## KPIダッシュボード\n(.*?)(?=\n---|\n## \d)", raw, re.DOTALL
    )
    kpi_table = kpi_match.group(1).strip() if kpi_match else ""

    # 今日のセクション抽出
    pattern = rf"## {re.escape(today_str)}.*?(?=\n---|\n## \d|\Z)"
    today_match = re.search(pattern, raw, re.DOTALL)
    today_section = today_match.group(0).strip() if today_match else ""

    return {
        "kpi_table": kpi_table,
        "today_section": today_section,
        "raw": raw,
    }


# ===================================================================
# SEOページ状況チェック
# ===================================================================

def check_seo_pages() -> list[dict]:
    """lp/ 以下のHTMLファイルを走査し、SEO状況を返す"""
    results = []
    if not SEO_DIR.exists():
        return results

    for html_file in sorted(SEO_DIR.rglob("*.html")):
        rel = html_file.relative_to(project_root)
        content = html_file.read_text(encoding="utf-8", errors="replace")

        has_title = bool(re.search(r"<title>.+?</title>", content, re.IGNORECASE))
        has_meta_desc = bool(
            re.search(r'<meta\s+name=["\']description["\']', content, re.IGNORECASE)
        )
        has_h1 = bool(re.search(r"<h1[^>]*>.+?</h1>", content, re.IGNORECASE))
        has_schema = bool(
            re.search(r"application/ld\+json", content, re.IGNORECASE)
        )
        has_ga4 = bool(
            re.search(r"gtag|G-[A-Z0-9]+|googletagmanager", content, re.IGNORECASE)
        )

        results.append(
            {
                "file": str(rel),
                "title": has_title,
                "meta_desc": has_meta_desc,
                "h1": has_h1,
                "schema": has_schema,
                "ga4": has_ga4,
            }
        )
    return results


# ===================================================================
# コンテンツ生成状況チェック
# ===================================================================

def check_content_status() -> dict:
    """content/generated/ 以下を確認し、今日の生成状況を返す"""
    today_str = date.today().strftime("%Y-%m-%d")
    total_dirs = 0
    today_dirs = 0
    total_images = 0
    today_images = 0

    if CONTENT_DIR.exists():
        for d in CONTENT_DIR.iterdir():
            if d.is_dir():
                total_dirs += 1
                imgs = list(d.glob("*.png")) + list(d.glob("*.jpg"))
                total_images += len(imgs)
                if d.name.startswith(today_str):
                    today_dirs += 1
                    today_images += len(imgs)

    return {
        "total_sets": total_dirs,
        "today_sets": today_dirs,
        "total_images": total_images,
        "today_images": today_images,
    }


# ===================================================================
# レポート送信コマンド
# ===================================================================

def send_daily_report():
    """日次レポート: PROGRESS.mdの今日のセクション + KPI + コンテンツ状況"""
    progress = parse_progress_md()
    content = check_content_status()
    seo_pages = check_seo_pages()

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "ナースロビー 日次レポート",
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"*{date.today().strftime('%Y-%m-%d')}* | 自動生成",
                }
            ],
        },
        {"type": "divider"},
    ]

    # --- KPIダッシュボード ---
    if progress["kpi_table"]:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*KPIダッシュボード*\n```\n"
                    + truncate(progress["kpi_table"])
                    + "\n```",
                },
            }
        )
        blocks.append({"type": "divider"})

    # --- 今日の進捗 ---
    if progress["today_section"]:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*今日の進捗*\n"
                    + truncate(progress["today_section"], 2800),
                },
            }
        )
    else:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*今日の進捗*\nPROGRESS.mdに今日のエントリはまだありません。",
                },
            }
        )

    blocks.append({"type": "divider"})

    # --- コンテンツ生成状況 ---
    blocks.append(
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*コンテンツ生成状況*\n"
                    f"今日のセット: *{content['today_sets']}* セット "
                    f"({content['today_images']} 枚)\n"
                    f"累計: *{content['total_sets']}* セット "
                    f"({content['total_images']} 枚)"
                ),
            },
        }
    )

    # --- SEO子ページ状況（サマリのみ） ---
    if seo_pages:
        total = len(seo_pages)
        ok_count = sum(
            1 for p in seo_pages if p["title"] and p["meta_desc"] and p["h1"]
        )
        schema_count = sum(1 for p in seo_pages if p["schema"])
        ga4_count = sum(1 for p in seo_pages if p["ga4"])
        # 問題のあるページだけ表示（最大5件）
        ng_pages = [p for p in seo_pages if not (p["title"] and p["meta_desc"] and p["h1"])]

        summary = (
            f"*SEOページ状況*\n"
            f"  総ページ数: *{total}* ページ\n"
            f"  SEO最適化済み: *{ok_count}/{total}*\n"
            f"  構造化データ: *{schema_count}/{total}*\n"
            f"  GA4設置: *{ga4_count}/{total}*"
        )
        if ng_pages:
            ng_list = "\n".join(f"  - `{p['file']}`" for p in ng_pages[:5])
            if len(ng_pages) > 5:
                ng_list += f"\n  ...他 {len(ng_pages) - 5} ページ"
            summary += f"\n\n*要改善:*\n{ng_list}"

        blocks.append({"type": "divider"})
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": summary,
                },
            }
        )

    return post_to_slack(blocks, text="ナースロビー日次レポート")


def send_kpi_dashboard():
    """KPIダッシュボードをSlackに送信"""
    progress = parse_progress_md()

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "KPIダッシュボード",
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"*{date.today().strftime('%Y-%m-%d %H:%M')}* 時点",
                }
            ],
        },
        {"type": "divider"},
    ]

    if progress["kpi_table"]:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "```\n" + truncate(progress["kpi_table"]) + "\n```",
                },
            }
        )
    else:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "PROGRESS.mdにKPIダッシュボードが見つかりません。",
                },
            }
        )

    # KPIログCSVがあれば直近データを追加
    if KPI_LOG_CSV.exists():
        try:
            lines = KPI_LOG_CSV.read_text(encoding="utf-8").strip().splitlines()
            if len(lines) > 1:
                recent = lines[-5:]  # 直近5行
                blocks.append({"type": "divider"})
                blocks.append(
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*直近パフォーマンスデータ*\n```\n"
                            + "\n".join(recent)
                            + "\n```",
                        },
                    }
                )
        except Exception:
            pass

    return post_to_slack(blocks, text="KPIダッシュボード")


def send_content_report():
    """コンテンツ生成状況レポート"""
    content = check_content_status()

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "コンテンツ生成レポート",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*本日 ({date.today().strftime('%Y-%m-%d')})*\n"
                    f"  生成セット数: *{content['today_sets']}*\n"
                    f"  生成画像数: *{content['today_images']}*\n\n"
                    f"*累計*\n"
                    f"  総セット数: *{content['total_sets']}*\n"
                    f"  総画像数: *{content['total_images']}*"
                ),
            },
        },
    ]

    # generated以下の各ディレクトリの一覧
    if CONTENT_DIR.exists():
        dirs = sorted(
            [d.name for d in CONTENT_DIR.iterdir() if d.is_dir()], reverse=True
        )
        if dirs:
            listing = "\n".join(f"  - `{d}`" for d in dirs[:10])
            if len(dirs) > 10:
                listing += f"\n  ...他 {len(dirs) - 10} セット"
            blocks.append({"type": "divider"})
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*直近のコンテンツセット*\n" + listing,
                    },
                }
            )

    return post_to_slack(blocks, text="コンテンツ生成レポート")


def send_seo_report():
    """SEOページ状況レポート"""
    seo_pages = check_seo_pages()

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "SEOページ状況レポート",
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"*{date.today().strftime('%Y-%m-%d %H:%M')}* 時点",
                }
            ],
        },
        {"type": "divider"},
    ]

    if not seo_pages:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "lp/ 以下にHTMLファイルが見つかりません。",
                },
            }
        )
    else:
        total = len(seo_pages)
        ok_count = sum(1 for p in seo_pages if p["title"] and p["meta_desc"] and p["h1"])
        schema_count = sum(1 for p in seo_pages if p["schema"])
        ga4_count = sum(1 for p in seo_pages if p["ga4"])

        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*サマリ*\n"
                        f"  総ページ数: *{total}*\n"
                        f"  SEO最適化済み（title+meta+h1）: *{ok_count}/{total}*\n"
                        f"  構造化データあり: *{schema_count}/{total}*\n"
                        f"  GA4あり: *{ga4_count}/{total}*"
                    ),
                },
            }
        )

        # 問題のあるページのみ詳細表示（最大10件）
        ng_pages = [p for p in seo_pages if not (p["title"] and p["meta_desc"] and p["h1"])]
        if ng_pages:
            blocks.append({"type": "divider"})
            ng_lines = []
            for p in ng_pages[:10]:
                status_items = [
                    ("title", p["title"]),
                    ("meta", p["meta_desc"]),
                    ("h1", p["h1"]),
                ]
                issues = " ".join(f"~~{label}~~" for label, ok in status_items if not ok)
                ng_lines.append(f"  `{p['file']}` : {issues}")
            if len(ng_pages) > 10:
                ng_lines.append(f"  ...他 {len(ng_pages) - 10} ページ")
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*要改善ページ:*\n" + "\n".join(ng_lines),
                    },
                }
            )

    return post_to_slack(blocks, text="SEOページ状況レポート")


def send_team_report():
    """6チームのエージェント作業結果を報告"""
    teams = [
        {
            "name": "SEO / LP チーム",
            "desc": "LP-AのSEO最適化、ローカルキーワード配置、構造化データ",
            "check_fn": lambda: _team_seo_status(),
        },
        {
            "name": "コンテンツ生成チーム",
            "desc": "TikTok/Instagram向け台本生成、画像生成パイプライン",
            "check_fn": lambda: _team_content_status(),
        },
        {
            "name": "SNS運用チーム",
            "desc": "投稿スケジュール管理、パフォーマンス分析",
            "check_fn": lambda: _team_sns_status(),
        },
        {
            "name": "LINE導線チーム",
            "desc": "LINE公式自動応答、リード管理",
            "check_fn": lambda: _team_line_status(),
        },
        {
            "name": "インフラ / DevOpsチーム",
            "desc": "cron管理、スクリプト保守、Git同期",
            "check_fn": lambda: _team_infra_status(),
        },
        {
            "name": "分析 / KPIチーム",
            "desc": "パフォーマンスデータ収集、A/Bテスト管理",
            "check_fn": lambda: _team_analytics_status(),
        },
    ]

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "ナースロビー チーム別作業レポート",
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"*{date.today().strftime('%Y-%m-%d %H:%M')}*",
                }
            ],
        },
        {"type": "divider"},
    ]

    for team in teams:
        status = team["check_fn"]()
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{team['name']}*\n{team['desc']}\n{status}",
                },
            }
        )
        blocks.append({"type": "divider"})

    return post_to_slack(blocks, text="チーム別作業レポート")


# --- チーム別ステータス関数 ---

def _team_seo_status() -> str:
    pages = check_seo_pages()
    if not pages:
        return "  HTMLページ: 未作成"
    total = len(pages)
    ok_count = sum(
        1 for p in pages if p["title"] and p["meta_desc"] and p["h1"]
    )
    return f"  HTMLページ: {total} ページ (SEO最適化済み: {ok_count}/{total})"


def _team_content_status() -> str:
    cs = check_content_status()
    return (
        f"  今日の生成: {cs['today_sets']} セット ({cs['today_images']} 枚)\n"
        f"  累計: {cs['total_sets']} セット ({cs['total_images']} 枚)"
    )


def _team_sns_status() -> str:
    progress = parse_progress_md()
    section = progress.get("today_section", "")
    post_count = section.count("投稿") if section else 0
    return f"  今日の進捗セクション: {'あり' if section else 'なし'}"


def _team_line_status() -> str:
    return "  LINE公式: 設定済み (詳細はPROGRESS.md参照)"


def _team_infra_status() -> str:
    cron_ok = (project_root / "scripts" / "pdca_healthcheck.sh").exists()
    utils_ok = (project_root / "scripts" / "utils.sh").exists()
    return (
        f"  utils.sh: {'OK' if utils_ok else 'NG'}\n"
        f"  healthcheck: {'OK' if cron_ok else 'NG'}"
    )


def _team_analytics_status() -> str:
    csv_exists = KPI_LOG_CSV.exists()
    ab_exists = (project_root / "data" / "ab_test_log.csv").exists()
    return (
        f"  kpi_log.csv: {'あり' if csv_exists else 'なし'}\n"
        f"  ab_test_log.csv: {'あり' if ab_exists else 'なし'}"
    )


# ===================================================================
# メイン
# ===================================================================

def main():
    parser = argparse.ArgumentParser(
        description="ナースロビー Slack報告スクリプト"
    )
    parser.add_argument(
        "--report",
        choices=["daily", "kpi", "content", "seo", "team"],
        default="daily",
        help="レポートの種類 (default: daily)",
    )
    args = parser.parse_args()

    dispatch = {
        "daily": send_daily_report,
        "kpi": send_kpi_dashboard,
        "content": send_content_report,
        "seo": send_seo_report,
        "team": send_team_report,
    }

    fn = dispatch[args.report]
    success = fn()

    if success:
        print(f"\n{args.report} レポート送信完了")
        sys.exit(0)
    else:
        print(f"\n{args.report} レポート送信失敗")
        sys.exit(1)


if __name__ == "__main__":
    main()
