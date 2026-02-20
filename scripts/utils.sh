#!/bin/bash
# ROBBY THE MATCH — 共通関数

PROJECT_DIR="$HOME/robby-the-match"
cd "$PROJECT_DIR"

export PATH="$PATH:/usr/local/bin:/opt/homebrew/bin:$HOME/.npm-global/bin"

TODAY=$(date +%Y-%m-%d)
NOW=$(date +%H:%M:%S)
DOW=$(date +%u)
WEEK_NUM=$(date +%V)

init_log() {
  local name=$1
  LOG="logs/${name}_${TODAY}.log"
  mkdir -p logs
  echo "=== [$TODAY $NOW] $name 開始 ===" >> "$LOG"
}

git_sync() {
  local msg=$1
  cd "$PROJECT_DIR"
  git add -A
  if ! git diff --cached --quiet; then
    git commit -m "$msg"
    git push origin main 2>> "$LOG" || echo "[WARN] git push失敗" >> "$LOG"
    echo "[OK] git sync: $msg" >> "$LOG"
  else
    echo "[INFO] 変更なし" >> "$LOG"
  fi
}

slack_notify() {
  local message=$1
  if [ -f "$PROJECT_DIR/scripts/notify_slack.py" ]; then
    python3 "$PROJECT_DIR/scripts/notify_slack.py" --message "$message" 2>> "$LOG" \
      || echo "[WARN] Slack通知失敗" >> "$LOG"
  else
    echo "[WARN] notify_slack.py未作成。Slack通知スキップ。" >> "$LOG"
  fi
}

slack_report() {
  # PROGRESS.mdの今日のセクションをSlackに送信
  local section=$1
  local today_section=$(sed -n "/## ${TODAY}/,/## [0-9]/p" PROGRESS.md | head -30)
  if [ -n "$today_section" ]; then
    slack_notify "$section 完了。
---
$today_section"
  else
    slack_notify "$section 完了。PROGRESS.md更新済み。"
  fi
}

update_progress() {
  # PROGRESS.mdに今日のエントリを追記
  local cycle=$1
  local content=$2

  # 今日のセクションがなければ作成
  if ! grep -q "## ${TODAY}" PROGRESS.md 2>/dev/null; then
    echo "" >> PROGRESS.md
    echo "## ${TODAY}" >> PROGRESS.MD
    echo "" >> PROGRESS.md
  fi

  echo "### ${cycle}（${NOW}）" >> PROGRESS.md
  echo "$content" >> PROGRESS.md
  echo "" >> PROGRESS.md
}

run_claude() {
  local prompt=$1
  local max_minutes=${2:-30}
  timeout "${max_minutes}m" claude -p "$prompt" \
    --dangerously-skip-permissions \
    --max-turns 40 \
    >> "$LOG" 2>&1
  local exit_code=$?
  if [ $exit_code -eq 124 ]; then
    echo "[TIMEOUT] ${max_minutes}分超過" >> "$LOG"
    slack_notify "⏰ Claude Code ${max_minutes}分タイムアウト。"
  fi
  return $exit_code
}

handle_error() {
  local step=$1
  echo "[ERROR] $step" >> "$LOG"
  slack_notify "⚠️ エラー: $step"
}
