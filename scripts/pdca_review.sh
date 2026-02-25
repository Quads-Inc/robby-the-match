#!/bin/bash
source ~/robby-the-match/scripts/utils.sh
init_log "pdca_review"
update_agent_state "daily_reviewer" "running"
check_instructions "daily_reviewer"

# === TikTok分析データ収集 ===
echo "[INFO] TikTok分析データ収集中..." >> "$LOG"
python3 "$PROJECT_DIR/scripts/tiktok_analytics.py" --update >> "$LOG" 2>&1 || echo "[WARN] TikTok分析失敗" >> "$LOG"

# === パフォーマンス分析 ===
echo "[INFO] パフォーマンス分析実行中..." >> "$LOG"
python3 "$PROJECT_DIR/scripts/analyze_performance.py" --analyze >> "$LOG" 2>&1 || echo "[WARN] パフォーマンス分析失敗" >> "$LOG"

run_claude "
STATE.mdを読め。data/performance_analysis.jsonも読め（パフォーマンス分析結果）。data/kpi_log.csvも読め。

【日次レビュー+即時改善サイクル】サブエージェントでデータ収集と改善を同時実行。

■ Check
1. 今日の全ログ確認（seo_batch, competitor, content, sns_post）
2. data/performance_analysis.json のパフォーマンス分析結果を確認
3. data/kpi_log.csv のKPIトレンドを確認
4. エラー確認（ログにERROR/WARN/TIMEOUTをgrep）
5. data/agent_state.json で全エージェントの稼働状態を確認

■ Do
6. PROGRESS.mdに日次サマリ追記:
   - 子ページ総数、今日の追加数
   - TikTok: 投稿数/再生数/フォロワー数
   - SEO施策数
   - エラー数
   - Agent Team稼働状況
7. 改善点があればコード修正して即実行
8. 明日のコンテンツ素材があるか確認→なければSlack警告
9. STATE.mdのKPI欄を最新データで更新

■ Act
10. STATE.md全面更新（KPI、全セクション最新化）
11. PROGRESS.mdに「明日やること」記載
" 30

# === sharedContext更新（他エージェント向け） ===
echo "[INFO] sharedContext更新中..." >> "$LOG"
python3 -c "
import json
from pathlib import Path
try:
    project = Path('$PROJECT_DIR')

    # Read analysis
    analysis = {}
    ap = project / 'data' / 'performance_analysis.json'
    if ap.exists():
        with open(ap) as f:
            analysis = json.load(f)

    # Read queue
    pending = 0
    qp = project / 'data' / 'posting_queue.json'
    if qp.exists():
        with open(qp) as f:
            q = json.load(f)
        pending = sum(1 for p in q['posts'] if p['status'] == 'pending')

    # Update shared context
    with open('$AGENT_STATE_FILE') as f:
        state = json.load(f)
    ctx = state.setdefault('sharedContext', {})
    ctx['lastAnalysis'] = analysis.get('analyzed_at', '')
    ctx['recommendations'] = analysis.get('recommendations', [])
    ctx['topPerformingTags'] = [
        p.get('content_id')
        for p in analysis.get('content_performance', {}).get('best_performing', [])
    ]
    ctx['queueRemaining'] = pending
    ctx['totalPostsThisWeek'] = sum(
        1 for p in q.get('posts', [])
        if p.get('status') == 'posted'
    ) if qp.exists() else 0

    with open('$AGENT_STATE_FILE', 'w') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    print(f'[OK] sharedContext更新: queue={pending}, recommendations={len(ctx[\"recommendations\"])}')
except Exception as e:
    print(f'[WARN] sharedContext更新失敗: {e}')
" >> "$LOG" 2>&1

git_sync "review: ${TODAY} 日次レビュー" "true"
update_state "日次レビュー"

TODAY_REPORT=$(sed -n "/## ${TODAY}/,/## [0-9]/p" PROGRESS.md 2>/dev/null | head -50)
update_agent_state "daily_reviewer" "completed"
slack_notify "📊 ${TODAY} 日次レポート
━━━━━━━━━━━━━━━━━━
${TODAY_REPORT:-データなし}
━━━━━━━━━━━━━━━━━━" "daily"
echo "[$TODAY] pdca_review完了" >> "$LOG"
