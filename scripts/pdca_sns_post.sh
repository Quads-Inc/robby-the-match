#!/bin/bash
# ===========================================
# ナースロビー SNS自動投稿 v5.0
# cron: 0 12,17,18,20,21 * * 1-6
#   → 各時間帯でposting_schedule.jsonを確認し、
#     当日の投稿時間でなければ即exit
#
# v5.0: 投稿時間A/Bテスト対応
# - posting_schedule.json で曜日別投稿時間を管理
# - auto_post.py v2.0: humanizer + 行動パターン擬態
# - tiktok_post.py: アニメーション動画優先
# - キュー枯渇時はcalendar自動補充
# ===========================================

source "$(dirname "$0")/utils.sh"
init_log "sns_post"

# Check if now is the scheduled time for today
SCHEDULE_FILE="$PROJECT_DIR/data/posting_schedule.json"
if [ -f "$SCHEDULE_FILE" ]; then
    CURRENT_HOUR=$(date +%H)
    CURRENT_MIN=$(date +%M)
    CURRENT_TIME="${CURRENT_HOUR}:${CURRENT_MIN}"
    DAY_NAME=$(date +%a)

    SCHEDULED_TIME=$(python3 -c "
import json
with open('$SCHEDULE_FILE') as f:
    s = json.load(f)
print(s.get('schedule', {}).get('$DAY_NAME', ''))
" 2>/dev/null)

    if [ -z "$SCHEDULED_TIME" ]; then
        echo "[INFO] 本日(${DAY_NAME})は投稿休止日" >> "$LOG"
        exit 0
    fi

    SCHEDULED_HOUR=$(echo "$SCHEDULED_TIME" | cut -d: -f1)
    if [ "$CURRENT_HOUR" != "$SCHEDULED_HOUR" ]; then
        echo "[INFO] 今は${CURRENT_TIME}。本日の投稿は${SCHEDULED_TIME}。スキップ。" >> "$LOG"
        exit 0
    fi

    echo "[INFO] 投稿時間一致 (${CURRENT_TIME} ≈ ${SCHEDULED_TIME})" >> "$LOG"
fi

echo "[INFO] SNS自動投稿 v5.0 開始" >> "$LOG"

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

# Step 3: TikTok自動投稿（tiktokautouploader主力）
echo "[INFO] TikTok動画投稿 (tiktokautouploader)..." >> "$LOG"
python3 "$PROJECT_DIR/scripts/tiktok_post.py" --post-next >> "$LOG" 2>&1
TK_EXIT=$?

if [ $TK_EXIT -eq 0 ]; then
    echo "[INFO] TikTok動画投稿処理完了" >> "$LOG"
else
    echo "[WARN] TikTok動画投稿失敗 (exit=$TK_EXIT)" >> "$LOG"
    # フォールバック: Upload-Post.com APIキーがあればカルーセル投稿を試行
    if grep -q "UPLOADPOST_API_KEY" "$PROJECT_DIR/.env" 2>/dev/null; then
        echo "[INFO] フォールバック: TikTokカルーセル投稿 (Upload-Post.com API)..." >> "$LOG"
        python3 "$PROJECT_DIR/scripts/tiktok_carousel.py" --post-next >> "$LOG" 2>&1
        TK_EXIT=$?
        if [ $TK_EXIT -eq 0 ]; then
            echo "[INFO] TikTokカルーセル投稿処理完了" >> "$LOG"
        else
            echo "[WARN] TikTokカルーセル投稿も失敗 (exit=$TK_EXIT)" >> "$LOG"
        fi
    else
        echo "[INFO] UPLOADPOST_API_KEY未設定のためカルーセルフォールバックをスキップ" >> "$LOG"
    fi
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
    echo "[WARN] 未投稿コンテンツ残り${UNPOSTED}件 → カレンダー自動補充" >> "$LOG"
    # ai_content_engine --calendar でローリング2週間分を自動補充
    python3 "$PROJECT_DIR/scripts/ai_content_engine.py" --calendar >> "$LOG" 2>&1
    # フォールバック: sns_workflow も実行
    python3 "$PROJECT_DIR/scripts/sns_workflow.py" --prepare-next >> "$LOG" 2>&1
    slack_notify "[SNS] 未投稿コンテンツ残り${UNPOSTED}件。カレンダー自動補充を実行。"
fi

# Step 6: 進捗記録
# Determine overall job exit code from critical steps (IG + TK)
if [ $IG_EXIT -ne 0 ] && [ $TK_EXIT -ne 0 ]; then
  SNS_JOB_EXIT=1
elif [ $IG_EXIT -ne 0 ] || [ $TK_EXIT -ne 0 ]; then
  SNS_JOB_EXIT=2  # partial failure
else
  SNS_JOB_EXIT=0
fi

update_progress "sns_post" "SNS自動投稿: IG済${POSTED_COUNT}件 / 未投稿${UNPOSTED}件 (IG=$IG_EXIT, TK=$TK_EXIT)"
update_agent_state "sns_poster" "completed"

write_heartbeat "sns_post" $SNS_JOB_EXIT
echo "=== [$TODAY $NOW] sns_post 完了 (IG=$IG_EXIT, TK=$TK_EXIT, overall=$SNS_JOB_EXIT) ===" >> "$LOG"
