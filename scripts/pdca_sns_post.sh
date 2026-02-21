#!/bin/bash
# ===========================================
# ROBBY THE MATCH SNS自動投稿
# cron: 30 17 * * 1-6（月-土 17:30）
# ===========================================

source "$(dirname "$0")/utils.sh"
init_log "sns_post"

echo "[INFO] SNS自動投稿開始" >> "$LOG"

# エージェント状態更新
update_agent_state "sns_poster" "running"

# 指示確認
check_instructions "sns_poster"

# Step 1: 投稿キューの確認・初期化
if [ ! -f "$PROJECT_DIR/data/posting_queue.json" ]; then
    echo "[INFO] 投稿キュー未初期化 → 初期化実行" >> "$LOG"
    python3 "$PROJECT_DIR/scripts/tiktok_post.py" --init-queue >> "$LOG" 2>&1
fi

# Step 2: 次の投稿を実行
echo "[INFO] TikTok投稿実行" >> "$LOG"
python3 "$PROJECT_DIR/scripts/tiktok_post.py" --post-next >> "$LOG" 2>&1
POST_EXIT=$?

if [ $POST_EXIT -eq 0 ]; then
    echo "[INFO] 投稿成功" >> "$LOG"
    update_agent_state "sns_poster" "completed"
else
    echo "[WARN] 投稿に問題あり（手動投稿依頼送信済み）" >> "$LOG"
    update_agent_state "sns_poster" "manual_required"
fi

# Step 3: 投稿状態をログに記録
python3 "$PROJECT_DIR/scripts/tiktok_post.py" --status >> "$LOG" 2>&1

# Step 4: 進捗記録
QUEUE_STATUS=$(python3 -c "
import json
with open('$PROJECT_DIR/data/posting_queue.json') as f:
    q = json.load(f)
posted = sum(1 for p in q['posts'] if p['status'] == 'posted')
total = len(q['posts'])
print(f'投稿: {posted}/{total}件完了')
" 2>/dev/null || echo "状態取得失敗")

update_progress "sns_post" "SNS投稿: $QUEUE_STATUS"

# Step 5: git同期
git_sync "sns: $(date +%Y-%m-%d) SNS自動投稿"

echo "=== [$TODAY $NOW] sns_post 完了 ===" >> "$LOG"
