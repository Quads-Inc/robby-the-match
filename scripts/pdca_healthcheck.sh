#!/bin/bash
# ===========================================
# ROBBY THE MATCH ヘルスチェック + ハートビート v2.0
# cron: 0 7 * * *（毎日07:00）
# ===========================================
source ~/robby-the-match/scripts/utils.sh
init_log "healthcheck"
update_agent_state "health_monitor" "running"

YESTERDAY=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d "yesterday" +%Y-%m-%d)
ISSUES=""

# === 既存のPDCAジョブ監視 ===
for cycle in pdca_seo_batch pdca_content pdca_review pdca_sns_post; do
  if [ -f "logs/${cycle}_${YESTERDAY}.log" ]; then
    if grep -q "ERROR\|TIMEOUT\|FAILED" "logs/${cycle}_${YESTERDAY}.log"; then
      ISSUES="${ISSUES}\n⚠️ ${cycle} にエラー"
    fi
  fi
done

# === サイト死活監視 ===
PUBLIC_URL="https://quads-nurse.com/lp/job-seeker/"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$PUBLIC_URL" 2>/dev/null)
[ "$HTTP_CODE" != "200" ] && ISSUES="${ISSUES}\n❌ サイト応答異常(${HTTP_CODE})"

# === ログ容量チェック ===
LOG_SIZE=$(du -sm logs/ 2>/dev/null | awk '{print $1}')
[ "${LOG_SIZE:-0}" -gt 500 ] && ISSUES="${ISSUES}\n⚠️ logs/ ${LOG_SIZE}MB"

# === TikTokハートビート（v2.0追加）===
echo "[INFO] TikTokハートビート実行" >> "$LOG"
python3 "$PROJECT_DIR/scripts/tiktok_post.py" --heartbeat >> "$LOG" 2>&1

# 投稿検証（キューとTikTok実投稿数の整合性チェック）
python3 "$PROJECT_DIR/scripts/tiktok_post.py" --verify >> "$LOG" 2>&1

# === TikTok分析データ収集 + KPI記録（v2.1追加）===
echo "[INFO] TikTok分析データ収集" >> "$LOG"
python3 "$PROJECT_DIR/scripts/tiktok_analytics.py" --daily-kpi >> "$LOG" 2>&1 || echo "[WARN] TikTok分析スキップ" >> "$LOG"

# === Agent Team稼働状態チェック ===
echo "[INFO] Agent Team稼働状態チェック" >> "$LOG"
python3 -c "
import json
from datetime import datetime, timedelta
with open('$PROJECT_DIR/data/agent_state.json') as f:
    state = json.load(f)
now = datetime.now()
for agent, last_run in state.get('lastRun', {}).items():
    if last_run:
        last = datetime.fromisoformat(last_run)
        hours_ago = (now - last).total_seconds() / 3600
        if hours_ago > 48:
            print(f'⚠️ {agent}: {hours_ago:.0f}時間未実行')
    else:
        status = state.get('status', {}).get(agent, 'unknown')
        if status == 'pending':
            print(f'⚠️ {agent}: 一度も実行されていない')
" >> "$LOG" 2>&1

# === 自己修復アクション ===
echo "[INFO] 自己修復チェック..." >> "$LOG"

# 1. Failed状態のエージェントを24h後にリセット
python3 -c "
import json
from datetime import datetime, timedelta
try:
    with open('$PROJECT_DIR/data/agent_state.json') as f:
        state = json.load(f)
    now = datetime.now()
    healed = []
    for agent, status in state.get('status', {}).items():
        if status == 'failed':
            last = state.get('lastRun', {}).get(agent)
            if last:
                last_dt = datetime.fromisoformat(last)
                if (now - last_dt).total_seconds() > 86400:
                    state['status'][agent] = 'pending'
                    healed.append(agent)
    if healed:
        with open('$PROJECT_DIR/data/agent_state.json', 'w') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        for a in healed:
            print(f'[HEAL] {a}: failed -> pending (>24h)')
except Exception as e:
    print(f'[WARN] 自己修復失敗: {e}')
" >> "$LOG" 2>&1

# 2. キュー枯渇時の緊急タスク作成
python3 -c "
import json
from datetime import datetime
try:
    with open('$PROJECT_DIR/data/posting_queue.json') as f:
        q = json.load(f)
    pending = sum(1 for p in q['posts'] if p['status'] == 'pending')
    if pending < 3:
        with open('$PROJECT_DIR/data/agent_state.json') as f:
            state = json.load(f)
        tasks = state.setdefault('pendingTasks', {}).setdefault('content_creator', [])
        has_pending = any(t['status'] == 'pending' for t in tasks)
        if not has_pending:
            tasks.append({
                'from': 'health_monitor',
                'type': 'emergency_generate',
                'details': f'キュー残り{pending}件。緊急コンテンツ生成必要。',
                'created': datetime.now().isoformat(),
                'status': 'pending'
            })
            with open('$PROJECT_DIR/data/agent_state.json', 'w') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            print(f'[HEAL] content_creatorに緊急生成タスク作成（残{pending}件）')
except Exception as e:
    print(f'[WARN] キューチェック失敗: {e}')
" >> "$LOG" 2>&1

# 3. 古いログファイル削除（30日以上）
OLD_LOGS=$(find "$PROJECT_DIR/logs/" -name "*.log" -mtime +30 2>/dev/null | wc -l)
if [ "$OLD_LOGS" -gt 0 ]; then
    find "$PROJECT_DIR/logs/" -name "*.log" -mtime +30 -delete 2>/dev/null
    echo "[HEAL] ${OLD_LOGS}件の古いログ削除" >> "$LOG"
fi

# === レポート送信 ===
if [ -n "$ISSUES" ]; then
  slack_notify "🏥 ヘルスチェック問題あり:\n$(echo -e "$ISSUES")" "alert"
else
  echo "[OK] 全システム正常" >> "$LOG"
fi

update_agent_state "health_monitor" "completed"
echo "[$TODAY] healthcheck完了" >> "$LOG"
