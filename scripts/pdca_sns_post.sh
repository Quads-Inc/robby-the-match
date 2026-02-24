#!/bin/bash
# ===========================================
# ナースロビー SNS自動投稿 v4.0
# cron: 30 17 * * 1-6（月-土 17:30）
#
# v4.0: 完全自動投稿（Instagram自動 + TikTok通知）
# - auto_post.py でInstagramに自動投稿
# - TikTokはSlack通知して手動アップ待ち
# - キュー枯渇時はコンテンツ自動生成をトリガー
# ===========================================

source "$(dirname "$0")/utils.sh"
init_log "sns_post"

echo "[INFO] SNS自動投稿 v4.0 開始" >> "$LOG"

# エージェント状態更新
update_agent_state "sns_poster" "running"

# 指示確認
check_instructions "sns_poster"

# Step 1: content/ready/ に投稿素材があるか確認
READY_COUNT=$(ls -d "$PROJECT_DIR/content/ready"/*/ 2>/dev/null | wc -l | tr -d ' ')
echo "[INFO] 準備済みコンテンツ: ${READY_COUNT}件" >> "$LOG"

if [ "$READY_COUNT" -eq 0 ]; then
    echo "[INFO] 準備済みコンテンツなし → sns_workflow.py で準備" >> "$LOG"
    python3 "$PROJECT_DIR/scripts/sns_workflow.py" --prepare-next >> "$LOG" 2>&1
fi

# Step 2: Instagram自動投稿
echo "[INFO] Instagram自動投稿..." >> "$LOG"
python3 "$PROJECT_DIR/scripts/auto_post.py" --instagram >> "$LOG" 2>&1
IG_EXIT=$?

if [ $IG_EXIT -eq 0 ]; then
    echo "[INFO] Instagram投稿処理完了" >> "$LOG"
else
    echo "[WARN] Instagram投稿失敗 (exit=$IG_EXIT)" >> "$LOG"
fi

# Step 3: TikTokカルーセル自動投稿（Upload-Post.com API）
echo "[INFO] TikTokカルーセル投稿..." >> "$LOG"
python3 "$PROJECT_DIR/scripts/tiktok_carousel.py" --post-next >> "$LOG" 2>&1
TK_EXIT=$?

if [ $TK_EXIT -eq 0 ]; then
    echo "[INFO] TikTokカルーセル投稿処理完了" >> "$LOG"
else
    echo "[WARN] TikTokカルーセル投稿失敗 (exit=$TK_EXIT)" >> "$LOG"
    # フォールバック: 旧方式のSlack通知
    echo "[INFO] フォールバック: TikTok投稿通知..." >> "$LOG"
    python3 "$PROJECT_DIR/scripts/auto_post.py" --tiktok >> "$LOG" 2>&1
fi

# Step 4: 投稿ステータス確認
echo "[INFO] 投稿ステータス:" >> "$LOG"
python3 "$PROJECT_DIR/scripts/auto_post.py" --status >> "$LOG" 2>&1

# Step 5: キュー枯渇チェック
READY_REMAINING=$(ls -d "$PROJECT_DIR/content/ready"/*/ 2>/dev/null | wc -l | tr -d ' ')
POSTED_COUNT=$(python3 -c "
import json
from pathlib import Path
log_file = Path('$PROJECT_DIR/data/post_log.json')
if log_file.exists():
    log = json.loads(log_file.read_text())
    posted = set(e['dir'] for e in log if e.get('status') == 'success' and e.get('platform') == 'instagram')
    print(len(posted))
else:
    print(0)
" 2>/dev/null || echo "0")

echo "[INFO] 投稿済み: ${POSTED_COUNT}件 / 残りready: ${READY_REMAINING}件" >> "$LOG"

# 未投稿が3件未満ならコンテンツ生成をトリガー
UNPOSTED=$(python3 -c "
import json
from pathlib import Path
log_file = Path('$PROJECT_DIR/data/post_log.json')
ready_dir = Path('$PROJECT_DIR/content/ready')
posted = set()
if log_file.exists():
    log = json.loads(log_file.read_text())
    posted = set(e['dir'] for e in log if e.get('status') == 'success' and e.get('platform') == 'instagram')
dirs = [d.name for d in sorted(ready_dir.iterdir()) if d.is_dir() and d.name not in posted]
print(len(dirs))
" 2>/dev/null || echo "0")

if [ "$UNPOSTED" -lt 3 ]; then
    echo "[WARN] 未投稿コンテンツ残り${UNPOSTED}件 → 追加生成が必要" >> "$LOG"
    # コンテンツ生成パイプラインをトリガー
    python3 "$PROJECT_DIR/scripts/sns_workflow.py" --prepare-next >> "$LOG" 2>&1
    create_agent_task "sns_poster" "content_creator" "generate_batch" "未投稿コンテンツ残り${UNPOSTED}件。追加生成が必要。"
    slack_notify "[SNS] 未投稿コンテンツ残り${UNPOSTED}件。追加コンテンツ生成を要請しました。"
fi

# Step 6: 進捗記録
update_progress "sns_post" "SNS自動投稿: IG済${POSTED_COUNT}件 / 未投稿${UNPOSTED}件"
update_agent_state "sns_poster" "completed"

write_heartbeat "sns_post" $?
echo "=== [$TODAY $NOW] sns_post 完了 ===" >> "$LOG"
