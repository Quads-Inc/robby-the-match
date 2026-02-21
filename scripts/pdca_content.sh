#!/bin/bash
# ===========================================
# ROBBY THE MATCH コンテンツ生成 v3.0
# cron: 0 15 * * 1-6（月-土 15:00）
# ===========================================
source ~/robby-the-match/scripts/utils.sh
init_log "pdca_content"
update_agent_state "content_creator" "running"
check_instructions "content_creator"

# === エージェント間タスク消費 ===
echo "[INFO] タスク確認中..." >> "$LOG"
TASKS=$(consume_agent_tasks "content_creator")
echo "$TASKS" >> "$LOG"

# 緊急タスクがあればバッチサイズを増加
FORCE_COUNT=0
if echo "$TASKS" | grep -q "emergency_generate"; then
    FORCE_COUNT=10
    echo "[INFO] 緊急生成タスク検出 → 10本強制生成" >> "$LOG"
elif echo "$TASKS" | grep -q "generate_batch"; then
    FORCE_COUNT=7
    echo "[INFO] バッチ生成タスク検出 → 7本強制生成" >> "$LOG"
fi

# === コンテンツパイプライン実行 ===
echo "[INFO] Content Pipeline 実行開始" >> "$LOG"

if [ "$FORCE_COUNT" -gt 0 ]; then
    python3 "$PROJECT_DIR/scripts/content_pipeline.py" --force "$FORCE_COUNT" >> "$LOG" 2>&1
    PIPELINE_EXIT=$?
else
    python3 "$PROJECT_DIR/scripts/content_pipeline.py" --auto >> "$LOG" 2>&1
    PIPELINE_EXIT=$?
fi

if [ $PIPELINE_EXIT -eq 0 ]; then
    echo "[OK] Content Pipeline 完了" >> "$LOG"
    update_agent_state "content_creator" "completed"
else
    echo "[ERROR] Content Pipeline 失敗 (exit $PIPELINE_EXIT)" >> "$LOG"
    handle_failure "content_creator" "Content Pipeline exit=$PIPELINE_EXIT"
fi

# === 進捗記録 ===
QUEUE_STATUS=$(python3 "$PROJECT_DIR/scripts/content_pipeline.py" --status 2>/dev/null | tail -5)
update_progress "content" "コンテンツ生成: $QUEUE_STATUS"

# === git同期 ===
git_sync "content: ${TODAY} コンテンツ生成"
update_state "コンテンツ生成"

echo "[$TODAY] pdca_content完了" >> "$LOG"
