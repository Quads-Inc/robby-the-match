#!/usr/bin/env python3
"""
ROBBY THE MATCH パフォーマンス分析スクリプト
投稿データから高パフォーマンスパターンを抽出し、次のコンテンツ戦略に反映する

使い方:
  python3 analyze_performance.py --analyze    # 全分析実行 + agent_state更新
  python3 analyze_performance.py --summary    # サマリ表示のみ
"""

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
QUEUE_FILE = PROJECT_DIR / "data" / "posting_queue.json"
KPI_LOG = PROJECT_DIR / "data" / "kpi_log.csv"
STOCK_CSV = PROJECT_DIR / "content" / "stock.csv"
AGENT_STATE = PROJECT_DIR / "data" / "agent_state.json"
ANALYSIS_OUTPUT = PROJECT_DIR / "data" / "performance_analysis.json"


def load_queue():
    if not QUEUE_FILE.exists():
        return {"posts": []}
    with open(QUEUE_FILE) as f:
        return json.load(f)


def load_kpi_log():
    if not KPI_LOG.exists():
        return []
    rows = []
    with open(KPI_LOG) as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def load_stock():
    if not STOCK_CSV.exists():
        return []
    rows = []
    with open(STOCK_CSV) as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def analyze_content_performance(queue):
    """投稿パフォーマンスを分析"""
    posted = [p for p in queue["posts"] if p["status"] == "posted"]
    if not posted:
        return {"total_posted": 0, "message": "投稿データなし"}

    results = {
        "total_posted": len(posted),
        "verified": sum(1 for p in posted if p.get("verified")),
        "by_category": {},
        "by_cta_type": {},
        "best_performing": [],
        "worst_performing": [],
        "avg_views": 0,
        "avg_likes": 0,
        "avg_saves": 0,
    }

    # パフォーマンスデータがある投稿を集計
    with_data = []
    for p in posted:
        perf = p.get("performance", {})
        views = perf.get("views")
        if views is not None and views > 0:
            with_data.append({
                "content_id": p.get("content_id", "unknown"),
                "caption": p.get("caption", "")[:50],
                "views": views,
                "likes": perf.get("likes", 0) or 0,
                "saves": perf.get("saves", 0) or 0,
                "comments": perf.get("comments", 0) or 0,
                "cta_type": p.get("cta_type", "soft"),
                "posted_at": p.get("posted_at", ""),
            })

    if with_data:
        # ソート（views降順）
        with_data.sort(key=lambda x: x["views"], reverse=True)
        results["best_performing"] = with_data[:3]
        results["worst_performing"] = with_data[-3:]

        total_views = sum(d["views"] for d in with_data)
        total_likes = sum(d["likes"] for d in with_data)
        total_saves = sum(d["saves"] for d in with_data)
        n = len(with_data)

        results["avg_views"] = round(total_views / n)
        results["avg_likes"] = round(total_likes / n)
        results["avg_saves"] = round(total_saves / n)

        # Save rate（保存率 = TikTokアルゴリズムの重要指標）
        if total_views > 0:
            results["save_rate"] = round(total_saves / total_views * 100, 2)
            results["like_rate"] = round(total_likes / total_views * 100, 2)

        # CTA種別分析
        for d in with_data:
            cta = d["cta_type"]
            if cta not in results["by_cta_type"]:
                results["by_cta_type"][cta] = {"count": 0, "total_views": 0}
            results["by_cta_type"][cta]["count"] += 1
            results["by_cta_type"][cta]["total_views"] += d["views"]
    else:
        results["message"] = "パフォーマンスデータ未収集（tiktok_analytics.py --updateで収集）"

    return results


def analyze_kpi_trend(kpi_rows):
    """KPIトレンド分析"""
    if len(kpi_rows) < 2:
        return {"trend": "データ不足", "days": len(kpi_rows)}

    latest = kpi_rows[-1]
    prev = kpi_rows[-2]

    def diff(key):
        try:
            return int(latest.get(key, 0) or 0) - int(prev.get(key, 0) or 0)
        except (ValueError, TypeError):
            return 0

    return {
        "latest_date": latest.get("date", ""),
        "followers_change": diff("tiktok_followers"),
        "videos_change": diff("tiktok_videos"),
        "views_change": diff("tiktok_total_views"),
        "likes_change": diff("tiktok_total_likes"),
        "current_followers": int(latest.get("tiktok_followers", 0) or 0),
        "current_videos": int(latest.get("tiktok_videos", 0) or 0),
        "days_tracked": len(kpi_rows),
    }


def analyze_content_mix(stock_rows):
    """コンテンツMIX分析（目標: あるある40%/転職25%/給与20%/紹介5%/トレンド10%）"""
    target_mix = {
        "あるある": 40,
        "転職": 25,
        "給与": 20,
        "紹介": 5,
        "トレンド": 10,
    }

    actual = {}
    posted_count = 0
    for row in stock_rows:
        cat = row.get("category", "other")
        if cat not in actual:
            actual[cat] = {"total": 0, "posted": 0}
        actual[cat]["total"] += 1
        if row.get("status") == "posted":
            actual[cat]["posted"] += 1
            posted_count += 1

    mix_analysis = {}
    for cat, target_pct in target_mix.items():
        cat_posted = actual.get(cat, {}).get("posted", 0)
        actual_pct = round(cat_posted / posted_count * 100) if posted_count > 0 else 0
        mix_analysis[cat] = {
            "target": target_pct,
            "actual": actual_pct,
            "gap": actual_pct - target_pct,
            "stock_remaining": actual.get(cat, {}).get("total", 0) - actual.get(cat, {}).get("posted", 0),
        }

    return {
        "total_stock": len(stock_rows),
        "total_posted": posted_count,
        "mix": mix_analysis,
    }


def generate_recommendations(content_perf, kpi_trend, content_mix):
    """分析結果からの改善提案"""
    recommendations = []

    # コンテンツMIXのギャップ
    for cat, data in content_mix.get("mix", {}).items():
        if data["gap"] < -10:
            recommendations.append(f"「{cat}」カテゴリの投稿が目標より不足。次バッチで重点生成。")

    # パフォーマンスベース
    if content_perf.get("avg_views", 0) > 0:
        if content_perf.get("save_rate", 0) < 1:
            recommendations.append("保存率1%未満。情報系（データ/比較表）コンテンツを増やして保存を促進。")
        if content_perf.get("save_rate", 0) > 3:
            recommendations.append("保存率3%超！この方向のコンテンツを継続。")

    # ベストパフォーマー分析
    best = content_perf.get("best_performing", [])
    if best:
        recommendations.append(f"最高パフォーマンス: {best[0].get('content_id')} ({best[0].get('views')}再生)")

    # KPIトレンド
    if kpi_trend.get("followers_change", 0) > 0:
        recommendations.append(f"フォロワー増加中 (+{kpi_trend['followers_change']})")
    elif kpi_trend.get("current_followers", 0) == 0:
        recommendations.append("フォロワー0。投稿頻度を上げ、コメント返信でエンゲージメント向上を。")

    if not recommendations:
        recommendations.append("データ蓄積中。投稿10本以上で本格的な分析が可能になります。")

    return recommendations


def update_agent_memory(analysis):
    """agent_state.jsonのagentMemoryにパフォーマンスデータを書き込み"""
    if not AGENT_STATE.exists():
        return

    with open(AGENT_STATE) as f:
        state = json.load(f)

    # content_creatorのメモリ更新
    memory = state.setdefault("agentMemory", {})
    cc = memory.get("content_creator", {})

    content_perf = analysis.get("content_performance", {})
    best = content_perf.get("best_performing", [])
    cc["highPerformingPatterns"] = [b.get("content_id", "") for b in best]

    # bestHookPatterns: フック文テキスト（台本JSONから取得可能な場合）
    cc["bestHookPatterns"] = [b.get("caption", "")[:30] for b in best if b.get("caption")]

    worst = content_perf.get("worst_performing", [])
    cc["failedPatterns"] = [w.get("content_id", "") for w in worst if w.get("views", 0) < 100]

    # avgMetrics: 平均指標サマリ
    cc["avgMetrics"] = {
        "views": content_perf.get("avg_views", 0),
        "likes": content_perf.get("avg_likes", 0),
        "saves": content_perf.get("avg_saves", 0),
        "saveRate": content_perf.get("save_rate", 0),
        "likeRate": content_perf.get("like_rate", 0),
    }

    # bestCategories: CTA種別ごとの平均再生数
    by_cta = content_perf.get("by_cta_type", {})
    cc["bestCTATypes"] = {
        cta: round(data["total_views"] / data["count"]) if data["count"] > 0 else 0
        for cta, data in by_cta.items()
    }

    # contentMixActual: 実際のカテゴリ分布
    content_mix = analysis.get("content_mix", {})
    cc["contentMixActual"] = {
        cat: data.get("actual", 0)
        for cat, data in content_mix.get("mix", {}).items()
    }

    cc["lastAnalysisDate"] = datetime.now().strftime("%Y-%m-%d")
    memory["content_creator"] = cc

    # sns_posterのメモリ更新
    sp = memory.get("sns_poster", {})
    sp["totalPosted"] = content_perf.get("total_posted", 0)
    sp["averageViews"] = content_perf.get("avg_views", 0)
    sp["lastAnalysisDate"] = datetime.now().strftime("%Y-%m-%d")
    memory["sns_poster"] = sp

    state["agentMemory"] = memory

    with open(AGENT_STATE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

    print("[OK] agent_state.json agentMemory 更新完了")


def run_analysis():
    """全分析実行"""
    print("=== ROBBY THE MATCH パフォーマンス分析 ===\n")

    queue = load_queue()
    kpi_rows = load_kpi_log()
    stock_rows = load_stock()

    content_perf = analyze_content_performance(queue)
    kpi_trend = analyze_kpi_trend(kpi_rows)
    content_mix = analyze_content_mix(stock_rows)
    recommendations = generate_recommendations(content_perf, kpi_trend, content_mix)

    analysis = {
        "analyzed_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "content_performance": content_perf,
        "kpi_trend": kpi_trend,
        "content_mix": content_mix,
        "recommendations": recommendations,
    }

    # ファイルに保存
    with open(ANALYSIS_OUTPUT, "w") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    print(f"[OK] 分析結果保存: {ANALYSIS_OUTPUT}")

    # agent_state更新
    update_agent_memory(analysis)

    return analysis


def print_summary(analysis=None):
    """サマリ表示"""
    if analysis is None:
        if ANALYSIS_OUTPUT.exists():
            with open(ANALYSIS_OUTPUT) as f:
                analysis = json.load(f)
        else:
            analysis = run_analysis()

    perf = analysis["content_performance"]
    kpi = analysis["kpi_trend"]
    mix = analysis["content_mix"]
    recs = analysis["recommendations"]

    print(f"📊 分析日時: {analysis['analyzed_at']}")
    print(f"\n--- コンテンツパフォーマンス ---")
    print(f"  投稿数: {perf['total_posted']} / 検証済み: {perf.get('verified', 0)}")
    print(f"  平均再生: {perf.get('avg_views', 'N/A')} / 平均いいね: {perf.get('avg_likes', 'N/A')}")
    if perf.get("save_rate"):
        print(f"  保存率: {perf['save_rate']}% / いいね率: {perf['like_rate']}%")

    print(f"\n--- KPIトレンド ---")
    print(f"  フォロワー: {kpi.get('current_followers', 0)} / 動画数: {kpi.get('current_videos', 0)}")
    print(f"  トラッキング日数: {kpi.get('days_tracked', 0)}")

    print(f"\n--- コンテンツMIX ---")
    print(f"  在庫: {mix['total_stock']}本 / 投稿済み: {mix['total_posted']}本")
    for cat, data in mix.get("mix", {}).items():
        gap_str = f"+{data['gap']}" if data['gap'] > 0 else str(data['gap'])
        print(f"  {cat}: 目標{data['target']}% / 実績{data['actual']}% ({gap_str}) 残{data['stock_remaining']}本")

    print(f"\n--- 改善提案 ---")
    for r in recs:
        print(f"  • {r}")


def main():
    parser = argparse.ArgumentParser(description="パフォーマンス分析")
    parser.add_argument("--analyze", action="store_true", help="全分析実行")
    parser.add_argument("--summary", action="store_true", help="サマリ表示")
    args = parser.parse_args()

    if args.analyze:
        analysis = run_analysis()
        print_summary(analysis)
    elif args.summary:
        print_summary()
    else:
        # デフォルト: 分析+サマリ
        analysis = run_analysis()
        print_summary(analysis)


if __name__ == "__main__":
    main()
