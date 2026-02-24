#!/usr/bin/env python3
"""
自己修復ウォッチドッグ v1.0
- 全cronジョブのハートビートを監視
- 失敗・未実行を検出してリカバリ試行
- Slackにアラート通知

cron: */30 * * * * python3 ~/robby-the-match/scripts/watchdog.py
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
HEARTBEAT_DIR = PROJECT_DIR / "data" / "heartbeats"
RECOVERY_LOG = PROJECT_DIR / "data" / "recovery_log.json"
LOG_DIR = PROJECT_DIR / "logs"
ENV_FILE = PROJECT_DIR / ".env"

# 期待されるジョブスケジュール: (時, 分, 最大実行時間(分), スクリプトパス)
EXPECTED_JOBS = {
    "seo_batch":    (4,  0,  30, "scripts/pdca_seo_batch.sh"),
    "healthcheck":  (7,  0,  15, "scripts/pdca_healthcheck.sh"),
    "competitor":   (10, 0,  30, "scripts/pdca_competitor.sh"),
    "content":      (15, 0,  45, "scripts/pdca_content.sh"),
    "sns_post":     (17, 30, 20, "scripts/pdca_sns_post.sh"),
}

MAX_RETRIES = 2


def load_env():
    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())


def slack_notify(message):
    try:
        subprocess.run(
            ["python3", str(PROJECT_DIR / "scripts" / "notify_slack.py"),
             "--message", message],
            capture_output=True, timeout=30
        )
    except Exception:
        pass


def load_recovery_log():
    if RECOVERY_LOG.exists():
        try:
            return json.loads(RECOVERY_LOG.read_text())
        except Exception:
            return {}
    return {}


def save_recovery_log(log):
    RECOVERY_LOG.parent.mkdir(parents=True, exist_ok=True)
    RECOVERY_LOG.write_text(json.dumps(log, indent=2, ensure_ascii=False))


def check_heartbeat(job_name, expected_hour, expected_min, max_duration_min):
    """ジョブのハートビートを確認"""
    now = datetime.now()
    expected_time = now.replace(hour=expected_hour, minute=expected_min, second=0)

    # まだ実行時刻前なら確認不要
    if now < expected_time:
        return "not_due_yet"

    # 実行中の可能性（実行時刻 + 最大実行時間以内）
    deadline = expected_time + timedelta(minutes=max_duration_min)
    if now < deadline:
        return "possibly_running"

    # ハートビートファイル確認
    hb_file = HEARTBEAT_DIR / f"{job_name}.json"
    if not hb_file.exists():
        return "missing"

    try:
        hb = json.loads(hb_file.read_text())
        hb_date = hb.get("date", "")
        today = now.strftime("%Y-%m-%d")

        if hb_date != today:
            return "stale"

        if hb.get("exit_code", 0) != 0:
            return "failed"

        return "ok"
    except Exception:
        return "error"


def attempt_recovery(job_name, script_path):
    """失敗ジョブの再実行を試行"""
    recovery = load_recovery_log()
    today = datetime.now().strftime("%Y-%m-%d")
    key = f"{job_name}_{today}"
    attempts = recovery.get(key, 0)

    if attempts >= MAX_RETRIES:
        return "max_retries"

    recovery[key] = attempts + 1
    save_recovery_log(recovery)

    full_path = PROJECT_DIR / script_path
    if not full_path.exists():
        return "script_not_found"

    try:
        result = subprocess.run(
            ["/bin/bash", str(full_path)],
            capture_output=True, timeout=1800,
            cwd=str(PROJECT_DIR),
            env={**os.environ}
        )
        return "recovered" if result.returncode == 0 else "retry_failed"
    except subprocess.TimeoutExpired:
        return "timeout"
    except Exception as e:
        return f"error: {e}"


def run_watchdog():
    """全ジョブの健全性チェック + 自己修復"""
    now = datetime.now()
    # 月-土のみ動作
    if now.weekday() == 6:  # 日曜
        return

    issues = []
    recovered = []

    for job_name, (hour, minute, max_dur, script) in EXPECTED_JOBS.items():
        status = check_heartbeat(job_name, hour, minute, max_dur)

        if status in ("ok", "not_due_yet", "possibly_running"):
            continue

        if status in ("missing", "stale", "failed"):
            # リカバリ試行
            result = attempt_recovery(job_name, script)
            if result == "recovered":
                recovered.append(f"{job_name}: 自動復旧成功")
            elif result == "max_retries":
                issues.append(f"{job_name}: リトライ上限到達（手動対応必要）")
            else:
                issues.append(f"{job_name}: 復旧失敗 ({result})")

    # ログ記録
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"watchdog_{now.strftime('%Y%m%d')}.log"
    entry = {
        "ts": now.isoformat(),
        "issues": issues,
        "recovered": recovered,
    }
    with open(log_file, 'a') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Slack通知（問題がある場合のみ）
    if issues:
        slack_notify(
            f"🔧 *ウォッチドッグアラート*\n\n"
            + "\n".join(f"❌ {i}" for i in issues)
            + ("\n\n" + "\n".join(f"✅ {r}" for r in recovered) if recovered else "")
        )
    elif recovered:
        slack_notify(
            f"🔧 *ウォッチドッグ: 自動復旧*\n\n"
            + "\n".join(f"✅ {r}" for r in recovered)
        )


if __name__ == "__main__":
    load_env()
    run_watchdog()
