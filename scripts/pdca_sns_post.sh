#!/bin/bash
# ===========================================
# ROBBY THE MATCH SNS投稿準備 v3.0
# cron: 30 17 * * 1-6（月-土 17:30）
#
# このスクリプトは次のpending投稿をBufferアップロード用に準備する。
# 自動アップロード（tiktok_post.py）は廃止。
# 手動でBufferからアップロードした後、
#   python3 scripts/sns_workflow.py --mark-posted <ID>
# で完了マークをつける。
# ===========================================

source "$(dirname "$0")/utils.sh"
init_log "sns_post"

echo "[INFO] SNS投稿準備 v3.0 開始" >> "$LOG"

# エージェント状態更新
update_agent_state "sns_poster" "running"

# 指示確認
check_instructions "sns_poster"

# Step 1: キューファイル存在確認
if [ ! -f "$PROJECT_DIR/data/posting_queue.json" ]; then
    echo "[ERROR] 投稿キューが見つかりません" >> "$LOG"
    slack_notify "[SNS] 投稿キューが見つかりません。初期化が必要です。"
    update_agent_state "sns_poster" "failed"
    echo "=== [$TODAY $NOW] sns_post 終了（エラー） ===" >> "$LOG"
    exit 1
fi

# Step 2: 次の投稿を準備（スライド確認→readyフォルダ作成→Slack通知）
echo "[INFO] 次の投稿を準備中..." >> "$LOG"
python3 "$PROJECT_DIR/scripts/sns_workflow.py" --prepare-next >> "$LOG" 2>&1
PREP_EXIT=$?

if [ $PREP_EXIT -eq 0 ]; then
    echo "[INFO] 投稿準備成功" >> "$LOG"
    update_agent_state "sns_poster" "completed"
else
    echo "[WARN] 投稿準備失敗 (exit=$PREP_EXIT)" >> "$LOG"
    update_agent_state "sns_poster" "failed"
fi

# Step 3: キュー状態をログに記録
python3 "$PROJECT_DIR/scripts/sns_workflow.py" --status >> "$LOG" 2>&1

# Step 4: 進捗記録
QUEUE_STATUS=$(python3 -c "
import json
with open('$PROJECT_DIR/data/posting_queue.json') as f:
    q = json.load(f)
posted = sum(1 for p in q['posts'] if p['status'] == 'posted')
ready = sum(1 for p in q['posts'] if p['status'] == 'ready')
failed = sum(1 for p in q['posts'] if p['status'] == 'failed')
pending = sum(1 for p in q['posts'] if p['status'] == 'pending')
total = len(q['posts'])
print(f'投稿済み: {posted} / 準備済み: {ready} / 待機: {pending} / 失敗: {failed} / 合計: {total}')
" 2>/dev/null || echo "状態取得失敗")

update_progress "sns_post" "SNS投稿: $QUEUE_STATUS"

# Step 5: キュー枯渇警告
PENDING_COUNT=$(python3 -c "
import json
with open('$PROJECT_DIR/data/posting_queue.json') as f:
    q = json.load(f)
print(sum(1 for p in q['posts'] if p['status'] in ('pending', 'ready')))
" 2>/dev/null || echo "0")

if [ "$PENDING_COUNT" -lt 5 ]; then
    echo "[WARN] キュー残り${PENDING_COUNT}件 → コンテンツ追加生成が必要" >> "$LOG"
    create_agent_task "sns_poster" "content_creator" "generate_batch" "キュー残り${PENDING_COUNT}件。7本追加生成が必要。"
    slack_notify "[SNS] 投稿キュー残り${PENDING_COUNT}件。コンテンツ生成を要請しました。"
fi

echo "=== [$TODAY $NOW] sns_post 完了 ===" >> "$LOG"
