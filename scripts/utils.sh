#!/bin/bash
# ROBBY THE MATCH 共通関数
# 全PDCAスクリプトはこれをsourceして使う

PROJECT_DIR="$HOME/robby-the-match"
cd "$PROJECT_DIR"
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.npm-global/bin:$PATH"

# cron環境用: gh CLIのトークンをgit認証に使う
export GH_CONFIG_DIR="$HOME/.config/gh"
if command -v gh &>/dev/null; then
  export GH_TOKEN=$(gh auth token 2>/dev/null || true)
  if [ -n "$GH_TOKEN" ]; then
    git config --local credential.helper "!f() { echo username=haruhi-medical; echo password=$GH_TOKEN; }; f"
  fi
fi

# .envから環境変数読み込み（Slack Token等）
if [ -f "$PROJECT_DIR/.env" ]; then
  set -a
  source "$PROJECT_DIR/.env"
  set +a
fi

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
  local do_push="${2:-false}"
  cd "$PROJECT_DIR"
  git add -A
  if ! git diff --cached --quiet; then
    git commit -m "$msg"
    if [ "$do_push" = "true" ]; then
      git push origin main 2>> "$LOG" || echo "[WARN] git push失敗" >> "$LOG"
    else
      echo "[INFO] commit済み（pushは日次レビューで一括）" >> "$LOG"
    fi
  else
    echo "[INFO] 変更なし" >> "$LOG"
  fi
}

slack_notify() {
  local message=$1
  python3 "$PROJECT_DIR/scripts/notify_slack.py" --message "$message" 2>> "$LOG" \
    || echo "[WARN] Slack通知失敗" >> "$LOG"
}

slack_report_structured() {
  local report_type=${1:-"daily"}
  python3 "$PROJECT_DIR/scripts/slack_report.py" --report "$report_type" 2>> "$LOG" \
    || echo "[WARN] Slack構造化レポート失敗" >> "$LOG"
}

update_state() {
  local section=$1
  python3 -c "
import re
with open('STATE.md', 'r') as f: text = f.read()
text = re.sub(r'# 最終更新:.*', '# 最終更新: $(date "+%Y-%m-%d %H:%M") by ${section}', text)
with open('STATE.md', 'w') as f: f.write(text)
" 2>> "$LOG" || echo "[WARN] STATE.md更新失敗" >> "$LOG"
}

update_progress() {
  local cycle=$1
  local content=$2
  if ! grep -q "## ${TODAY}" PROGRESS.md 2>/dev/null; then
    echo -e "\n## ${TODAY}\n" >> PROGRESS.md
  fi
  echo "### ${cycle}（${NOW}）" >> PROGRESS.md
  echo "$content" >> PROGRESS.md
  echo "" >> PROGRESS.md
}

run_claude() {
  local prompt=$1
  local max_minutes=${2:-30}
  local max_seconds=$((max_minutes * 60))

  # macOS互換: gtimeout → timeout → background fallback
  local timeout_cmd=""
  if command -v gtimeout &>/dev/null; then
    timeout_cmd="gtimeout"
  elif command -v timeout &>/dev/null; then
    timeout_cmd="timeout"
  fi
  echo "[DEBUG] timeout_cmd=$timeout_cmd, max=${max_minutes}min" >> "$LOG"

  if [ -n "$timeout_cmd" ]; then
    $timeout_cmd "${max_seconds}s" claude -p "$prompt" \
      --dangerously-skip-permissions \
      --max-turns 40 \
      >> "$LOG" 2>&1
  else
    # timeout系コマンドなし → バックグラウンド+waitで代替
    claude -p "$prompt" \
      --dangerously-skip-permissions \
      --max-turns 40 \
      >> "$LOG" 2>&1 &
    local pid=$!
    local elapsed=0
    while kill -0 $pid 2>/dev/null; do
      sleep 10
      elapsed=$((elapsed + 10))
      if [ $elapsed -ge $max_seconds ]; then
        kill $pid 2>/dev/null
        wait $pid 2>/dev/null
        echo "[TIMEOUT] ${max_minutes}分超過" >> "$LOG"
        slack_notify "⏰ タイムアウト（${max_minutes}分）"
        return 124
      fi
    done
    wait $pid
  fi

  local exit_code=$?
  if [ $exit_code -eq 124 ]; then
    echo "[TIMEOUT] ${max_minutes}分超過" >> "$LOG"
    slack_notify "⏰ タイムアウト（${max_minutes}分）"
  fi
  return $exit_code
}

handle_error() {
  local step=$1
  echo "[ERROR] $step" >> "$LOG"
  slack_notify "⚠️ エラー: $step"
}

# ==========================================
# エージェント状態管理
# ==========================================

AGENT_STATE_FILE="$PROJECT_DIR/data/agent_state.json"

update_agent_state() {
  local agent_name="$1"
  local status="$2"
  python3 -c "
import json
from datetime import datetime
try:
    with open('$AGENT_STATE_FILE', 'r') as f:
        state = json.load(f)
    state['lastRun']['$agent_name'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    state['status']['$agent_name'] = '$status'
    with open('$AGENT_STATE_FILE', 'w') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
except Exception as e:
    print(f'[WARN] agent_state更新失敗: {e}')
" 2>> "$LOG" || echo "[WARN] agent_state更新失敗" >> "$LOG"
}

handle_failure() {
  local agent_name="$1"
  local error_msg="$2"
  echo "[$agent_name] FAILURE: $error_msg" >> "$LOG"
  update_agent_state "$agent_name" "failed"
  slack_notify "⚠️ $agent_name failed: $error_msg"
}

check_instructions() {
  # Slack指示キューに自分宛の指示があるか確認
  local agent_name="$1"
  python3 -c "
import json, sys
try:
    with open('$PROJECT_DIR/data/slack_instructions.json', 'r') as f:
        data = json.load(f)
    instructions = data.get('instructions', []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    pending = [i for i in instructions if isinstance(i, dict) and i.get('to') == '$agent_name' and i.get('status') == 'pending']
    if pending:
        print(f'[INFO] {len(pending)}件の指示あり')
        for i in pending:
            print(f'  - {i.get(\"message\", \"\")}')
except FileNotFoundError:
    pass
except json.JSONDecodeError as e:
    print(f'[WARN] 指示キューJSON解析エラー: {e}', file=sys.stderr)
except Exception as e:
    print(f'[WARN] 指示チェック失敗: {e}', file=sys.stderr)
" 2>> "$LOG" || echo "[WARN] check_instructions python実行失敗 (agent=$agent_name)" >> "$LOG"
}

# ==========================================
# ハートビート（自己修復ウォッチドッグ用）
# ==========================================

write_heartbeat() {
  local job_name="$1"
  local exit_code="${2:-0}"
  if ! mkdir -p "$PROJECT_DIR/data/heartbeats" 2>> "$LOG"; then
    echo "[ERROR] heartbeat: data/heartbeats ディレクトリ作成失敗" >> "$LOG"
    return 1
  fi
  python3 -c "
import json, sys
from datetime import datetime
try:
    hb = {
        'ts': datetime.now().isoformat(),
        'exit_code': $exit_code,
        'job': '$job_name',
        'date': datetime.now().strftime('%Y-%m-%d')
    }
    with open('$PROJECT_DIR/data/heartbeats/${job_name}.json', 'w') as f:
        json.dump(hb, f, indent=2, ensure_ascii=False)
except Exception as e:
    print(f'[ERROR] heartbeat書き込み失敗 ({job_name}): {e}', file=sys.stderr)
    sys.exit(1)
" 2>> "$LOG" || echo "[WARN] heartbeat書き込み失敗: $job_name (exit_code=$exit_code)" >> "$LOG"
}

# ==========================================
# エージェントメモリ・通信・自己修復
# ==========================================

read_agent_memory() {
  local agent_name="$1"
  local key="$2"
  python3 -c "
import json, sys
try:
    with open('$AGENT_STATE_FILE') as f:
        state = json.load(f)
    val = state.get('agentMemory', {}).get('$agent_name', {}).get('$key', '')
    if isinstance(val, (dict, list)):
        print(json.dumps(val, ensure_ascii=False))
    else:
        print(val)
except FileNotFoundError:
    print(f'[WARN] agent_state.json not found', file=sys.stderr)
except Exception as e:
    print(f'[WARN] read_agent_memory failed ({agent_name}/{key}): {e}', file=sys.stderr)
" 2>> "${LOG:-/dev/stderr}"
}

write_agent_memory() {
  local agent_name="$1"
  local key="$2"
  local value="$3"
  python3 -c "
import json, sys
try:
    with open('$AGENT_STATE_FILE') as f:
        state = json.load(f)
    mem = state.setdefault('agentMemory', {}).setdefault('${agent_name}', {})
    try:
        mem['${key}'] = json.loads('''${value}''')
    except (json.JSONDecodeError, ValueError):
        mem['${key}'] = '''${value}'''
    with open('$AGENT_STATE_FILE', 'w') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
except Exception as e:
    print(f'[WARN] write_agent_memory failed: {e}', file=sys.stderr)
" 2>> "$LOG"
}

write_shared_context() {
  local key="$1"
  local value="$2"
  python3 -c "
import json, sys
try:
    with open('$AGENT_STATE_FILE') as f:
        state = json.load(f)
    ctx = state.setdefault('sharedContext', {})
    try:
        ctx['${key}'] = json.loads('''${value}''')
    except (json.JSONDecodeError, ValueError):
        ctx['${key}'] = '''${value}'''
    with open('$AGENT_STATE_FILE', 'w') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
except Exception as e:
    print(f'[WARN] write_shared_context failed: {e}', file=sys.stderr)
" 2>> "$LOG"
}

create_agent_task() {
  local from_agent="$1"
  local to_agent="$2"
  local task_type="$3"
  local details="$4"
  python3 -c "
import json
from datetime import datetime
try:
    with open('$AGENT_STATE_FILE') as f:
        state = json.load(f)
    tasks = state.setdefault('pendingTasks', {}).setdefault('${to_agent}', [])
    tasks.append({
        'from': '${from_agent}',
        'type': '${task_type}',
        'details': '''${details}''',
        'created': datetime.now().isoformat(),
        'status': 'pending'
    })
    with open('$AGENT_STATE_FILE', 'w') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    print(f'[TASK] ${from_agent} -> ${to_agent}: ${task_type}')
except Exception as e:
    print(f'[WARN] create_agent_task failed: {e}')
" 2>> "$LOG"
}

consume_agent_tasks() {
  local agent_name="$1"
  python3 -c "
import json
try:
    with open('$AGENT_STATE_FILE') as f:
        state = json.load(f)
    tasks = state.get('pendingTasks', {}).get('${agent_name}', [])
    pending = [t for t in tasks if t.get('status') == 'pending']
    if pending:
        for t in pending:
            print(f'[TASK] from={t[\"from\"]} type={t[\"type\"]} details={t[\"details\"]}')
            t['status'] = 'processing'
        with open('$AGENT_STATE_FILE', 'w') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    else:
        print('[INFO] タスクなし')
except Exception as e:
    print(f'[WARN] consume_agent_tasks failed: {e}')
" 2>> "$LOG"
}
