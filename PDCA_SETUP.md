# ROBBY THE MATCH — 自律PDCAシステム構築+起動プロンプト

> Claude Codeに投入する。YOLO 40ターンで環境構築→そのまま自動稼働。

---

## 投入方法

```bash
cd ~/robby-the-match
claude -p "$(cat PDCA_SETUP.md)" \
  --dangerously-skip-permissions \
  --max-turns 40
```

---

## ↓ ここからがプロンプト本文（PDCA_SETUP.md として保存）↓

```markdown
お前はROBBY THE MATCHの経営参謀だ。CLAUDE.mdを読め。

# ═══════════════════════════════════════════════════════
# ピーター・ティールの問い
# ═══════════════════════════════════════════════════════

「賛成する人がほとんどいない、大切な真実は何か？」

看護師紹介業界の隠れた真実:

1. 大手が手数料20-30%を取れるのは「マッチングの質が高い」からではない。
   営業人件費が高いからだ。求人開拓に1人月100万円かかる。
   → AIでオペレーションコストをゼロに近づければ、10%で黒字になる。
   → これは既にCLAUDE.mdに書いてある。実行するだけだ。

2. だが、もっと深い真実がある。
   看護師が転職エージェントに求めているのは「求人紹介」ではない。
   「この病院、本当はどうなの？」という内部情報だ。
   人間関係、残業の実態、有給消化率、師長の性格、離職率。
   大手はこれを「営業担当の人脈」で集めている。だからコストが高い。

3. ロビーの本当の勝ち筋:
   「内部情報をAIで集約・匿名化して提供する」仕組みを作れば、
   大手の人的ネットワークをコストゼロで代替できる。
   ただし、これはPhase2以降の話だ。

4. 今（Phase1）の真実:
   看護師は転職を「考え始めた瞬間」に情報を探す。
   その瞬間にいるのはGoogleとTikTokだ。
   TikTokで「あ、これ私のことだ」と思わせ、
   Googleで「小田原 看護師 転職」で見つけてもらう。
   この2つの入口を同時に回すことが全て。
   大手はTikTokのオーガニック運用をやっていない。ここが隙間だ。

この思考を全ての判断の背景に持て。
ただし今やることはシンプルだ。
SNSとSEOの自律PDCAパイプラインを構築して起動しろ。

# ═══════════════════════════════════════════════════════
# ミッション: 40ターン以内で以下を全て完了させろ
# ═══════════════════════════════════════════════════════

Phase A: 基盤構築（ターン1-15）
Phase B: PDCAスクリプト構築（ターン16-30）
Phase C: cron登録+初回実行テスト（ターン31-40）

失敗したステップは3回リトライ。3回失敗したら代替案を実行。
全ステップの結果をPROGRESS.mdに記録しろ。

---

## Phase A: 基盤構築

### A-1. Git + GitHub連携

確認項目:
- git init済みか → 未なら実行
- .gitignoreに以下が含まれるか → なければ追加:
  .env
  logs/
  content/generated/
  __pycache__/
  *.pyc
  node_modules/
- git remote -v でGitHubリモートが設定されているか
  → 未設定なら案内を出せ:
    「GitHubにプライベートリポジトリ robby-the-match を作成してください。
     作成後、以下を実行:
     git remote add origin https://github.com/{ユーザー名}/robby-the-match.git」
  → 設定済みなら git push -u origin main を実行

リモート未設定でも先に進め。ローカルgitは機能させる。
GitHub連携はYOSHIYUKIが後から設定できる。

### A-2. LP公開準備（GitHub Pages用）

lp/ ディレクトリを確認。
LP-A（求職者向）が存在するか確認。

存在する場合:
- lp/job-seeker/index.html のSEO状態を診断
- 不足があれば即修正:
  □ <title> に「小田原 看護師 転職 | ROBBY THE MATCH」
  □ <meta name="description" content="..."> 160文字以内
  □ <h1> にメインキーワード
  □ OGP設定（og:title, og:description, og:image）
  □ JSON-LD構造化データ（JobPosting）
  □ viewport meta tag

存在しない場合:
- 最低限のLP-Aを作成しろ（HTML + CSS、1ページ）
- 内容: 手数料10%の価値提案、LINE登録CTA、ローカルキーワード配置

lp/sitemap.xml を作成:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://placeholder.github.io/robby-the-match/job-seeker/</loc>
    <lastmod>今日の日付</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
```

### A-3. 共通ユーティリティスクリプト作成

scripts/utils.sh を作成:

```bash
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
    echo "## ${TODAY}" >> PROGRESS.md
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
```

chmod +x scripts/utils.sh

### A-4. PROGRESS.md整備

PROGRESS.mdが存在するか確認。存在する場合は既存内容を保持。
なければ以下で作成:

```markdown
# ROBBY THE MATCH 進捗ログ

## 運用ルール
- 各PDCAサイクルが自動で追記する
- パフォーマンスデータはYOSHIYUKIが手動追記 or 自動取得
- 週次レビューで1週間分を総括
- Slack通知は本ファイルの当日セクションを引用して送信

## KPIダッシュボード
| 指標 | 目標 | 現在 | 更新日 |
|------|------|------|--------|
| 累計投稿数 | Week2: 5本 | 0 | - |
| 平均再生数 | Week4: 500 | - | - |
| LINE登録数 | Month2: 5名 | 0 | - |
| 成約数 | Month3: 1名 | 0 | - |
| SEO施策数 | 週3回 | 0 | - |

---
```

---

## Phase B: PDCAスクリプト構築

### B-1. SEO朝サイクル（毎日06:00）

scripts/pdca_morning.sh を作成:

```bash
#!/bin/bash
source ~/robby-the-match/scripts/utils.sh
init_log "pdca_morning"

run_claude "
お前はROBBY THE MATCHの経営参謀だ。CLAUDE.mdを読め。

【SEO改善PDCAサイクル】

■ Plan
1. PROGRESS.mdのKPIダッシュボードとSEO施策履歴を確認
2. lp/job-seeker/index.html のSEO診断:
   - title/meta description/h1/h2キーワード最適化
   - JobPosting JSON-LD
   - ローカルキーワード密度（小田原、神奈川県西部、湘南）
   - OGP設定
   - 内部リンク
   - ページ速度（不要なリソースがないか）
3. 改善点を優先順位付きで最大3つリストアップ

■ Do
4. 優先度1の改善を実施
5. 可能なら優先度2も実施
6. sitemap.xmlのlastmodを今日に更新

■ Check
7. git diffで変更内容確認
8. HTML構文にエラーがないか確認
9. 問題があればgit checkout -- で戻す

■ Act
10. PROGRESS.mdに追記（update_progress関数を使え）:
    施策内容、変更ファイル、次回改善候補
11. KPIダッシュボードの「SEO施策数」をインクリメント

完了報告は不要。スクリプト側でSlack通知する。
"

git_sync "seo: ${TODAY} SEO改善"
update_progress "🔍 SEO朝サイクル" "$(git log -1 --pretty=%s 2>/dev/null || echo '変更なし')"
slack_report "🔍 SEO朝サイクル"
echo "[$TODAY] pdca_morning完了" >> "$LOG"
```

chmod +x scripts/pdca_morning.sh

### B-2. コンテンツ生成（毎日15:00）

scripts/pdca_content.sh を作成:

```bash
#!/bin/bash
source ~/robby-the-match/scripts/utils.sh
init_log "pdca_content"

run_claude "
お前はROBBY THE MATCHの経営参謀だ。CLAUDE.mdを読め。
今日は$(date +%A)（曜日${DOW}）。

【コンテンツPDCAサイクル】

■ Plan
1. PROGRESS.mdから直近の投稿パフォーマンスを確認
2. content/generated/ に今日分の素材があるか確認
   → あれば品質チェックのみ、なければ新規生成
3. 過去の高パフォーマンス投稿パターンをPROGRESS.mdから抽出
4. カテゴリMIX（40%あるある/25%転職/20%給与/5%紹介/10%トレンド）と
   過去7日の実績を照合して今日のカテゴリを決定

■ Do
5. 台本JSON生成（prompt_template.mdに従え）
   - ペルソナ「ミサキ」が3秒で止まるか自問
   - フック20文字以内、各スライド30文字以内
   - CTA 8:2ルール（過去7日分のCTA比率を確認して調整）
6. content/generated/${TODAY}_台本.json に保存
7. python3 scripts/generate_slides.py で6枚スライド生成
8. Slack通知: フック文+キャプション+投稿予定時間
9. Postiz下書きアップロード（17:30 JSTスケジュール）
   失敗時: ffmpegでMP4 → それもダメならSlackに画像+キャプション送信

■ Check
10. スライド6枚の存在確認
11. JSON必須フィールド（id, hook, slides, caption, hashtags）検証
12. フック文20文字チェック

■ Act
13. PROGRESS.mdに追記:
    コンテンツID、カテゴリ、フック文、投稿スケジュール時間
14. KPIダッシュボードの「累計投稿数」をインクリメント
15. 技術的問題があればCLAUDE.mdの失敗ログに追記

完了報告は不要。スクリプト側でSlack通知する。
"

git_sync "content: ${TODAY} コンテンツ生成"
update_progress "📱 コンテンツ生成" "$(cat content/generated/${TODAY}_*.json 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); print(f"ID:{d.get(\"id\",\"?\")} カテゴリ:{d.get(\"category\",\"?\")} フック:{d.get(\"hook\",\"?\")}")' 2>/dev/null || echo '生成情報取得失敗')"
slack_report "📱 コンテンツ生成"
echo "[$TODAY] pdca_content完了" >> "$LOG"
```

chmod +x scripts/pdca_content.sh

### B-3. 日次レビュー（毎日23:00）

scripts/pdca_review.sh を作成:

```bash
#!/bin/bash
source ~/robby-the-match/scripts/utils.sh
init_log "pdca_review"

run_claude "
お前はROBBY THE MATCHの経営参謀だ。CLAUDE.mdを読め。

【日次レビューPDCAサイクル】

■ Plan
1. PROGRESS.mdの今日の全記録を読め
2. logs/pdca_morning_${TODAY}.log と logs/pdca_content_${TODAY}.log を読め
3. 今日の全アクションの成否を整理

■ Do（データ収集）
4. Postiz CLIでアナリティクス取得を試みろ（失敗してもOK）
5. git log --since='1 day ago' で今日のコミット一覧取得
6. content/generated/ の今日分ファイル数を確認

■ Check（自己診断）
7. チェックリスト:
   □ コンテンツは生成されたか
   □ SEO改善は実施されたか
   □ git pushは成功したか（GitHub Pagesにデプロイされたか）
   □ Slack通知は送信されたか
   □ エラーが発生していないか（ログにERROR/WARNをgrep）
   □ CLAUDE.mdの禁止事項に違反していないか
   □ コスト発生していないか
8. パフォーマンスデータがあれば分析

■ Act（改善実行+明日準備）
9. 改善点があれば即時修正（スクリプトバグ、CLAUDE.md更新）
10. 明日のコンテンツ素材があるか確認 → なければSlack警告
11. PROGRESS.mdに日次サマリを追記:
    - 今日の成果（投稿数、SEO施策、エラー数）
    - パフォーマンスデータ（あれば）
    - 発見した改善点
    - 明日やること
12. KPIダッシュボードの数値を更新

完了報告は不要。スクリプト側でSlack通知する。
"

git_sync "review: ${TODAY} 日次レビュー"

# 日次レポートをSlack送信（PROGRESS.mdの今日セクション全体）
TODAY_REPORT=$(sed -n "/## ${TODAY}/,/## [0-9]/p" PROGRESS.md 2>/dev/null | head -50)
if [ -n "$TODAY_REPORT" ]; then
  slack_notify "📊 ${TODAY} 日次レポート
━━━━━━━━━━━━━━━━━━
${TODAY_REPORT}
━━━━━━━━━━━━━━━━━━"
else
  slack_notify "📊 ${TODAY} 日次レビュー完了。詳細はPROGRESS.md参照。"
fi

echo "[$TODAY] pdca_review完了" >> "$LOG"
```

chmod +x scripts/pdca_review.sh

### B-4. 週次振り返り（日曜08:00）

scripts/pdca_weekly.sh を作成:

```bash
#!/bin/bash
source ~/robby-the-match/scripts/utils.sh
init_log "pdca_weekly"

run_claude "
お前はROBBY THE MATCHの経営参謀だ。CLAUDE.mdを読め。

【週次PDCAサイクル】

■ Plan（今週の分析）
1. PROGRESS.mdの今週分（月曜〜土曜）の全記録を読め
2. 集計:
   - 投稿数（目標: 週4本以上）
   - カテゴリ別本数+偏りチェック
   - パフォーマンスデータ（再生数、保存率、コメント数）
   - SEO施策の実施数
   - エラー発生数
   - Slack通知の成功率
3. git log --oneline --since='7 days ago' で全コミット確認
4. 高パフォーマンスと低パフォーマンスの特徴を分析
5. ピーター・ティールの問いを自問:
   「今週やったことで、本当に看護師の行動を変えた施策はあるか？
    数字の改善ではなく、1人の看護師の意思決定に影響を与えたか？」

■ Do（次週計画+一括生成）
6. CLAUDE.mdのマイルストーンと照合:
   - Week 1-2: 最初の5投稿完了？
   - Week 3-4: 累計20投稿、平均再生数500以上？
   - Month 2: LINE登録5名以上？
   - Month 3: 初回成約？
7. 未達の場合、未達時判断基準に従って方針修正を提案
   ※ 戦略変更はSlackでYOSHIYUKIに確認。勝手に変えるな。
8. 来週7日分の台本を一括生成:
   - 月曜:あるある 火曜:あるある 水曜:転職
   - 木曜:あるある 金曜:給与 土曜:トレンド 日曜:転職
   - CTA 8:2ルール（月〜金:ソフト 土:ソフト 日:ハード）
   - 今週の高パフォーマンスパターンを優先
9. content/generated/{各曜日の日付}_台本.json で保存
10. 全42枚のスライド画像を生成

■ Check（品質+戦略確認）
11. 7本の台本+42枚の画像が全て存在するか
12. CTA比率が設計通りか
13. 今週との差別化ができているか（同じフックの使い回しはないか）

■ Act（自己改善+記録）
14. CLAUDE.mdに反映:
    - 効いたフックパターン → ★マーク付きでストック追加
    - 失敗パターン → ✕マーク付きで失敗ログ追加
    - MIX比率調整が必要なら提案（Slack確認必須）
15. PROGRESS.mdにWeek Xサマリを追記:
    - 週間KPI（投稿数、再生数、LINE登録、SEO施策）
    - 最もインパクトがあった施策
    - 来週の重点施策
    - マイルストーン進捗
16. KPIダッシュボードを最新に更新

完了報告は不要。スクリプト側でSlack通知する。
" 45

git_sync "weekly: Week${WEEK_NUM} 振り返り+来週分生成"

# 週次レポートSlack送信
WEEKLY_KPI=$(grep -A 10 'KPIダッシュボード' PROGRESS.md 2>/dev/null | head -12)
slack_notify "📈 Week${WEEK_NUM} 週次レポート
━━━━━━━━━━━━━━━━━━
${WEEKLY_KPI}
━━━━━━━━━━━━━━━━━━
来週7本のコンテンツ生成済み。
詳細はPROGRESS.md参照。"

echo "[$TODAY] pdca_weekly完了" >> "$LOG"
```

chmod +x scripts/pdca_weekly.sh

### B-5. 障害監視（毎日07:00 — 朝サイクルの後）

scripts/pdca_healthcheck.sh を作成:

```bash
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
```

chmod +x scripts/pdca_healthcheck.sh

---

## Phase C: cron登録+起動

### C-1. cron登録

以下を実行:

```bash
(crontab -l 2>/dev/null | grep -v "robby-the-match"; cat << 'CRON'
# ============================================
# ROBBY THE MATCH 自律PDCAループ
# ============================================
# 日次（月〜土）
0  6 * * 1-6 /bin/bash ~/robby-the-match/scripts/pdca_morning.sh
0  7 * * 1-6 /bin/bash ~/robby-the-match/scripts/pdca_healthcheck.sh
0 15 * * 1-6 /bin/bash ~/robby-the-match/scripts/pdca_content.sh
0 23 * * 1-6 /bin/bash ~/robby-the-match/scripts/pdca_review.sh
# 週次（日曜のみ）
0  8 * * 0   /bin/bash ~/robby-the-match/scripts/pdca_weekly.sh
# ============================================
CRON
) | crontab -
```

crontab -l で設定を確認して出力しろ。

### C-2. Mac Miniスリープ無効化

```bash
# 管理者権限が必要。子ユーザーの場合はスキップしてSlack通知。
sudo pmset -a sleep 0 2>/dev/null \
  && sudo pmset -a disablesleep 1 2>/dev/null \
  || echo "[WARN] スリープ設定は管理者ユーザーで実行してください: sudo pmset -a sleep 0 && sudo pmset -a disablesleep 1"
```

### C-3. 初回テスト実行

以下を順番に実行して動作確認:

1. scripts/utils.sh の関数テスト:
   source scripts/utils.sh && slack_notify "🚀 ROBBY自律PDCAシステム起動テスト"

2. git_sync テスト:
   source scripts/utils.sh && git_sync "test: 自律PDCAシステム初期セットアップ"

3. pdca_healthcheck.sh を手動実行:
   bash scripts/pdca_healthcheck.sh

4. pdca_content.sh を手動実行（実際にコンテンツ1本生成）:
   bash scripts/pdca_content.sh

全テスト完了後、Slackに最終通知:

slack_notify "🚀 ROBBY THE MATCH 自律PDCAシステム起動完了。
━━━━━━━━━━━━━━━━━━
スケジュール:
  06:00 SEO改善 → git push → GitHub Pages自動デプロイ
  07:00 ヘルスチェック
  15:00 コンテンツ生成 → Slack通知 → Postiz下書き
  17:30 YOSHIYUKI投稿ボタン（手動60秒）
  23:00 日次レビュー → PROGRESS.md更新 → Slackレポート
  日曜 週次振り返り → 来週7本生成 → CLAUDE.md自己改善
━━━━━━━━━━━━━━━━━━
全アクションはSlackに通知されます。
全変更はgit pushされGitHubにバックアップされます。
全記録はPROGRESS.mdに蓄積されます。"

### C-4. PROGRESS.mdに初期セットアップ記録

PROGRESS.mdに以下を追記:

## {今日の日付}
### 🚀 自律PDCAシステム起動
- Phase A: 基盤構築完了（Git, LP, utils.sh, PROGRESS.md）
- Phase B: PDCAスクリプト5本作成
  - pdca_morning.sh（SEO）
  - pdca_content.sh（コンテンツ）
  - pdca_review.sh（日次レビュー）
  - pdca_weekly.sh（週次振り返り）
  - pdca_healthcheck.sh（障害監視）
- Phase C: cron登録+初回テスト実行
- 状態: ✅ 自律稼働開始

---

全ステップを順番に実行しろ。
各ステップの結果を報告しながら進め。
エラーがあれば3回リトライし、ダメなら代替案を実行して先に進め。
40ターン以内で全て完了させろ。
```
