#!/bin/bash
# ===========================================
# ROBBY THE MATCH SNS自動投稿 v2.0
# cron: 30 17 * * 1-6（月-土 17:30）
# ===========================================

source "$(dirname "$0")/utils.sh"
init_log "sns_post"

echo "[INFO] SNS自動投稿 v2.0 開始" >> "$LOG"

# エージェント状態更新
update_agent_state "sns_poster" "running"

# 指示確認
check_instructions "sns_poster"

# venv Python を使用
VENV_PY="$PROJECT_DIR/.venv/bin/python3"
if [ ! -f "$VENV_PY" ]; then
    echo "[WARN] venvなし。システムPythonを使用" >> "$LOG"
    VENV_PY="python3"
fi

# Step 1: 投稿キューの確認・初期化
if [ ! -f "$PROJECT_DIR/data/posting_queue.json" ]; then
    echo "[INFO] 投稿キュー未初期化 → 初期化実行" >> "$LOG"
    python3 "$PROJECT_DIR/scripts/tiktok_post.py" --init-queue >> "$LOG" 2>&1
fi

# Step 2: 投稿前検証（キュー整合性チェック）
echo "[INFO] 投稿前検証" >> "$LOG"
python3 "$PROJECT_DIR/scripts/tiktok_post.py" --verify >> "$LOG" 2>&1

# Step 3: 次の投稿を実行（venv Python で実行されるサブプロセスを使用）
echo "[INFO] TikTok投稿実行" >> "$LOG"
python3 "$PROJECT_DIR/scripts/tiktok_post.py" --post-next >> "$LOG" 2>&1
POST_EXIT=$?

if [ $POST_EXIT -eq 0 ]; then
    echo "[INFO] 投稿成功" >> "$LOG"
    update_agent_state "sns_poster" "completed"
else
    echo "[WARN] 投稿失敗" >> "$LOG"
    update_agent_state "sns_poster" "failed"
fi

# Step 4: 投稿状態をログに記録
python3 "$PROJECT_DIR/scripts/tiktok_post.py" --status >> "$LOG" 2>&1

# Step 5: 進捗記録
QUEUE_STATUS=$(python3 -c "
import json
with open('$PROJECT_DIR/data/posting_queue.json') as f:
    q = json.load(f)
posted = sum(1 for p in q['posts'] if p['status'] == 'posted' and p.get('verified'))
failed = sum(1 for p in q['posts'] if p['status'] == 'failed')
pending = sum(1 for p in q['posts'] if p['status'] == 'pending')
total = len(q['posts'])
print(f'投稿: {posted}件検証済み / {failed}件失敗 / {pending}件待機 / {total}件合計')
" 2>/dev/null || echo "状態取得失敗")

update_progress "sns_post" "SNS投稿: $QUEUE_STATUS"

# Step 6: git同期
git_sync "sns: $(date +%Y-%m-%d) SNS自動投稿"

# === キュー枯渇警告 + エージェント間通信 ===
PENDING_COUNT=$(python3 -c "
import json
with open('$PROJECT_DIR/data/posting_queue.json') as f:
    q = json.load(f)
print(sum(1 for p in q['posts'] if p['status'] == 'pending'))
" 2>/dev/null || echo "0")

if [ "$PENDING_COUNT" -lt 5 ]; then
    echo "[WARN] キュー残り${PENDING_COUNT}件 → content_creatorにタスク作成" >> "$LOG"
    create_agent_task "sns_poster" "content_creator" "generate_batch" "キュー残り${PENDING_COUNT}件。7本追加生成が必要。"
    slack_notify "⚠️ 投稿キュー残り${PENDING_COUNT}件。コンテンツ生成を要請しました。"
fi

echo "=== [$TODAY $NOW] sns_post 完了 ===" >> "$LOG"
