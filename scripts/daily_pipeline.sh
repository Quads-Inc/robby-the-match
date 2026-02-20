#!/bin/bash
# 日次パイプラインスクリプト
# 毎日16:00に自動実行（cronから呼び出される）

set -e

PROJECT_DIR="$HOME/robby-the-match"
cd "$PROJECT_DIR"

TODAY=$(date +%Y%m%d)
DOW=$(date +%u)  # 1=月曜 ... 7=日曜
DOW_NAME=$(date +%A)

echo "========================================"
echo "ROBBY THE MATCH 日次パイプライン"
echo "========================================"
echo "日付: $TODAY ($DOW_NAME)"
echo "時刻: $(date +%H:%M:%S)"
echo ""

# 今日の台本JSONを探す
echo "🔍 今日の台本を検索中..."
JSON_FILE=$(find content/generated/ -name "${TODAY}_*.json" -print -quit)

if [ -z "$JSON_FILE" ]; then
  echo "❌ エラー: 今日（${TODAY}）の台本が見つかりません"
  echo ""
  echo "💡 対処方法:"
  echo "   1. Claude Codeで週次バッチを実行してください"
  echo "   2. content/templates/weekly_batch.md を参照"
  echo ""

  # Slackにアラート
  python3 scripts/notify_slack.py --message "⚠️ 【ROBBY】今日（${TODAY}）の台本がありません。Claude Codeで週次バッチを実行してください。"

  exit 1
fi

echo "✅ 台本発見: $(basename $JSON_FILE)"
echo ""

# Step 1: Slack通知（承認依頼）
echo "📱 Step 1: Slack通知送信"
python3 scripts/notify_slack.py --json "$JSON_FILE"

if [ $? -eq 0 ]; then
  echo "   ✅ Slack通知完了"
else
  echo "   ❌ Slack通知失敗"
  exit 1
fi

echo ""

# Step 2: Postiz下書きアップロード
echo "📤 Step 2: Postiz下書きアップロード"

# 明日17:30 JSTにスケジュール
if command -v gdate &> /dev/null; then
  # GNU date (brew install coreutils)
  SCHEDULE=$(gdate -d "+1 day" +%Y-%m-%dT17:30:00+09:00)
else
  # BSD date (Mac標準)
  SCHEDULE=$(date -v+1d +%Y-%m-%dT17:30:00+09:00 2>/dev/null || echo "2026-02-21T17:30:00+09:00")
fi

echo "   スケジュール: $SCHEDULE"

python3 scripts/post_to_tiktok.py --json "$JSON_FILE" --schedule "$SCHEDULE"

if [ $? -eq 0 ]; then
  echo "   ✅ Postiz投稿完了"
else
  echo "   ⚠️  Postiz投稿に問題がありました（手動アップロードが必要な可能性）"
fi

echo ""

# Step 3: PROGRESS.mdに記録
echo "📝 Step 3: PROGRESS.mdに記録"

# JSONから情報を抽出
CONTENT_ID=$(python3 -c "import json; print(json.load(open('$JSON_FILE'))['id'])")
HOOK=$(python3 -c "import json; print(json.load(open('$JSON_FILE'))['hook'])")

# PROGRESS.mdに追記（既存エントリがなければ）
if ! grep -q "## $(date +%Y-%m-%d)" PROGRESS.md; then
  cat >> PROGRESS.md << EOF

## $(date +%Y-%m-%d)（$(date +%A)）

### 今日やったこと
- 自動パイプライン実行: ${CONTENT_ID} - ${HOOK}
- Slack通知: 送信済み
- Postiz: 下書きアップロード済み（${SCHEDULE}）

### メモ・気づき
-

EOF
  echo "   ✅ PROGRESS.md更新完了"
else
  echo "   ℹ️  PROGRESS.mdは既に更新済み"
fi

echo ""
echo "========================================"
echo "✅ 日次パイプライン完了"
echo "========================================"
echo ""

exit 0
