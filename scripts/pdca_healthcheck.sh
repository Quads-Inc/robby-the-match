#!/bin/bash
source ~/robby-the-match/scripts/utils.sh
init_log "healthcheck"

ISSUES=""

# 昨日のログを確認
YESTERDAY=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d "yesterday" +%Y-%m-%d)

# 各PDCAが実行されたか確認
for cycle in pdca_morning pdca_content pdca_review; do
  if [ ! -f "logs/${cycle}_${YESTERDAY}.log" ]; then
    ISSUES="${ISSUES}\n❌ ${cycle} が昨日実行されなかった"
  elif grep -q "ERROR\|TIMEOUT" "logs/${cycle}_${YESTERDAY}.log"; then
    ISSUES="${ISSUES}\n⚠️ ${cycle} にエラーあり"
  fi
done

# git pushの状態確認
LAST_PUSH=$(git log --oneline -1 2>/dev/null)
if [ -z "$LAST_PUSH" ]; then
  ISSUES="${ISSUES}\n❌ gitリポジトリが初期化されていない"
fi

# ディスク容量確認（logs/とcontent/generated/が肥大化していないか）
LOG_SIZE=$(du -sm logs/ 2>/dev/null | awk '{print $1}')
if [ "${LOG_SIZE:-0}" -gt 500 ]; then
  ISSUES="${ISSUES}\n⚠️ logs/ が${LOG_SIZE}MB。古いログを削除推奨。"
fi

# 結果通知
if [ -n "$ISSUES" ]; then
  slack_notify "🏥 ヘルスチェック — 問題あり:
$(echo -e "$ISSUES")"
else
  echo "[OK] ヘルスチェック問題なし" >> "$LOG"
fi

echo "[$TODAY] healthcheck完了" >> "$LOG"
