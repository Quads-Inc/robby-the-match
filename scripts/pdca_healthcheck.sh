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

# === TikTokハートビート（v2.0追加 / v2.2: フェッチ失敗検知強化）===
echo "[INFO] TikTokハートビート実行" >> "$LOG"
python3 "$PROJECT_DIR/scripts/tiktok_post.py" --heartbeat >> "$LOG" 2>&1
HEARTBEAT_EXIT=$?

# 投稿検証（キューとTikTok実投稿数の整合性チェック）
echo "[INFO] TikTok投稿検証実行" >> "$LOG"
python3 "$PROJECT_DIR/scripts/tiktok_post.py" --verify >> "$LOG" 2>&1
VERIFY_EXIT=$?

# ハートビート/検証の結果をログ解析してISSUESに追加
# v2.0: プロフィール取得失敗はINFO扱い（bot検出の可能性大）
# CRITICAL/WARNING判定はheartbeat() v2.0内で行う（upload_verification.json基準）
if grep -q "直近.*件.*のアップロード失敗" "$LOG" 2>/dev/null; then
  ISSUES="${ISSUES}\n⚠️ TikTokアップロード失敗が連続中"
fi

# === TikTok分析データ収集 + KPI記録（v2.1追加）===
echo "[INFO] TikTok分析データ収集" >> "$LOG"
python3 "$PROJECT_DIR/scripts/tiktok_analytics.py" --daily-kpi >> "$LOG" 2>&1 || echo "[WARN] TikTok分析スキップ" >> "$LOG"

# === Agent Team稼働状態チェック ===
echo "[INFO] Agent Team稼働状態チェック" >> "$LOG"
python3 -c "
import json
from datetime import datetime, timedelta

# Per-agent staleness thresholds (hours)
# Weekly agents get 192h (8 days), daily agents get 48h
THRESHOLDS = {
    'weekly_strategist': 192,
    'weekly_content_planner': 192,
    'seo_optimizer': 48,
    'health_monitor': 48,
    'competitor_analyst': 48,
    'content_creator': 48,
    'daily_reviewer': 48,
    'sns_poster': 48,
    'ai_marketing_orchestrator': 48,
}

try:
    with open('$PROJECT_DIR/data/agent_state.json') as f:
        state = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f'[ERROR] agent_state.json read failed: {e}')
    exit(0)

now = datetime.now()
for agent, last_run in state.get('lastRun', {}).items():
    threshold = THRESHOLDS.get(agent, 48)
    if last_run:
        last = datetime.fromisoformat(last_run)
        hours_ago = (now - last).total_seconds() / 3600
        if hours_ago > threshold:
            print(f'warning {agent}: {hours_ago:.0f}h since last run (threshold: {threshold}h)')
    else:
        status = state.get('status', {}).get(agent, 'unknown')
        if status == 'pending':
            print(f'info {agent}: not yet executed (pending)')
" >> "$LOG" 2>&1

# === 自己修復アクション ===
echo "[INFO] 自己修復チェック..." >> "$LOG"

# 1. Failed状態のエージェントを24h後にリセット + stale pendingTasks cleanup
python3 -c "
import json
from datetime import datetime, timedelta
try:
    with open('$PROJECT_DIR/data/agent_state.json') as f:
        state = json.load(f)
    now = datetime.now()
    changed = False

    # 1a. Reset failed agents after 24h
    healed = []
    for agent, status in state.get('status', {}).items():
        if status == 'failed':
            last = state.get('lastRun', {}).get(agent)
            if last:
                last_dt = datetime.fromisoformat(last)
                if (now - last_dt).total_seconds() > 86400:
                    state['status'][agent] = 'pending'
                    healed.append(agent)
                    changed = True
    for a in healed:
        print(f'[HEAL] {a}: failed -> pending (>24h)')

    # 1b. Clean up stale pendingTasks (processing > 48h or completed)
    for agent, tasks in state.get('pendingTasks', {}).items():
        cleaned = []
        for t in tasks:
            created = t.get('created', '')
            status = t.get('status', '')
            if status in ('completed', 'done'):
                changed = True
                continue
            if status == 'processing' and created:
                try:
                    created_dt = datetime.fromisoformat(created)
                    if (now - created_dt).total_seconds() > 172800:  # 48h
                        print(f'[HEAL] Removed stale task for {agent}: {t.get(\"type\", \"?\")} (processing >48h)')
                        changed = True
                        continue
                except ValueError:
                    pass
            cleaned.append(t)
        state['pendingTasks'][agent] = cleaned

    if changed:
        with open('$PROJECT_DIR/data/agent_state.json', 'w') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
except Exception as e:
    print(f'[WARN] self-heal failed: {e}')
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

# 3. ログローテーション
# 3a. 日付入りログ（*_YYYY-MM-DD.log, *_YYYYMMDD.log）は7日で削除
OLD_DATED=$(find "$PROJECT_DIR/logs/" \( -name "*_20[0-9][0-9]-[0-9][0-9]-[0-9][0-9].log" -o -name "*_20[0-9][0-9][0-9][0-9][0-9][0-9].log" \) -mtime +7 2>/dev/null | wc -l | tr -d ' ')
if [ "${OLD_DATED:-0}" -gt 0 ]; then
    find "$PROJECT_DIR/logs/" \( -name "*_20[0-9][0-9]-[0-9][0-9]-[0-9][0-9].log" -o -name "*_20[0-9][0-9][0-9][0-9][0-9][0-9].log" \) -mtime +7 -delete 2>/dev/null
    echo "[HEAL] ${OLD_DATED} dated log files deleted (>7 days)" >> "$LOG"
fi

# 3b. 追記型ログ（slack_commander.log, watchdog.log等）は500KB超で切り詰め
for APPEND_LOG in "$PROJECT_DIR/logs/slack_commander.log" "$PROJECT_DIR/logs/watchdog.log"; do
    if [ -f "$APPEND_LOG" ]; then
        FSIZE=$(wc -c < "$APPEND_LOG" 2>/dev/null | tr -d ' ')
        if [ "${FSIZE:-0}" -gt 512000 ]; then
            ARCHIVE="${APPEND_LOG}.$(date +%Y%m%d).bak"
            cp "$APPEND_LOG" "$ARCHIVE" 2>/dev/null
            tail -200 "$APPEND_LOG" > "${APPEND_LOG}.tmp" && mv "${APPEND_LOG}.tmp" "$APPEND_LOG"
            echo "[HEAL] $(basename "$APPEND_LOG") truncated (was ${FSIZE} bytes)" >> "$LOG"
            # Remove old archives beyond the 3 most recent
            ls -t "${APPEND_LOG}".*.bak 2>/dev/null | tail -n +4 | xargs rm -f 2>/dev/null
        fi
    fi
done

# 3c. その他の古いログ（30日超）
OLD_OTHER=$(find "$PROJECT_DIR/logs/" -name "*.log" -not -name "slack_commander.log" -not -name "watchdog.log" -mtime +30 2>/dev/null | wc -l | tr -d ' ')
if [ "${OLD_OTHER:-0}" -gt 0 ]; then
    find "$PROJECT_DIR/logs/" -name "*.log" -not -name "slack_commander.log" -not -name "watchdog.log" -mtime +30 -delete 2>/dev/null
    echo "[HEAL] ${OLD_OTHER} old log files deleted (>30 days)" >> "$LOG"
fi

# 3d. PNG/スクリーンショット等の非ログファイルを14日で削除
OLD_IMGS=$(find "$PROJECT_DIR/logs/" -name "*.png" -mtime +14 2>/dev/null | wc -l | tr -d ' ')
if [ "${OLD_IMGS:-0}" -gt 0 ]; then
    find "$PROJECT_DIR/logs/" -name "*.png" -mtime +14 -delete 2>/dev/null
    echo "[HEAL] ${OLD_IMGS} old image files deleted (>14 days)" >> "$LOG"
fi

# === レポート送信 ===
if [ -n "$ISSUES" ]; then
  slack_notify "🏥 ヘルスチェック問題あり:\n$(echo -e "$ISSUES")" "alert"
else
  echo "[OK] 全システム正常" >> "$LOG"
fi

update_agent_state "health_monitor" "completed"
# heartbeat: 0=正常(問題なし), 1=問題検出(ただしスクリプト自体は正常完了)
if [ -n "$ISSUES" ]; then
  write_heartbeat "healthcheck" 1
else
  write_heartbeat "healthcheck" 0
fi
echo "[$TODAY] healthcheck完了" >> "$LOG"
