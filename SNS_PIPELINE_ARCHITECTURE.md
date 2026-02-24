# ナースロビー SNS完全自動化パイプライン 最終設計図

> 設計日: 2026-02-24
> ステータス: 設計書（実装前レビュー用）

---

## 1. 全体フローチャート

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SNS完全自動化パイプライン                           │
│                  cron駆動 + Slack人間インターフェース                    │
└─────────────────────────────────────────────────────────────────────┘

 [Phase 1: 企画]        [Phase 2: 生成]        [Phase 3: レビュー]
 日曜 05:00             日曜 05:30             日曜 06:00
 ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
 │ トレンド収集   │      │ 台本生成(AI)  │      │ AI品質スコア  │
 │ ↓             │      │ ↓             │      │   ↓           │
 │ MIX計算       │──→  │ カルーセル7枚  │──→  │ >=8: 自動承認  │
 │ ↓             │      │ ↓             │      │ 6-7: Slack通知 │
 │ テンプレ選択   │      │ キャプション   │      │ <=5: 自動却下  │
 │ ↓             │      │ ↓             │      │   ↓           │
 │ 台本JSON      │      │ ハッシュタグ   │      │ 却下→再生成    │
 └──────────────┘      └──────────────┘      └──────────────┘
                                                      │
                                                      ▼
 [Phase 5: 分析]        [Phase 4: 投稿]        ┌──────────────┐
 投稿24h後              月-土 17:30             │ 承認済みキュー │
 ┌──────────────┐      ┌──────────────┐      └───────┬──────┘
 │ KPI自動収集   │      │ ready/に配置  │              │
 │ ↓             │◀──  │ ↓             │◀─────────────┘
 │ スコアリング   │      │ Slackに送信   │
 │ ↓             │      │ ↓             │
 │ 勝ちパターン   │      │ 人間がアップ   │
 │ ↓             │      │ ↓             │
 │ テンプレ更新   │      │ mark-posted   │
 └──────────────┘      └──────────────┘
```

---

## 2. 詳細フロー（5フェーズ）

### Phase 1: 企画（AI自律）

```
入力:
  - data/performance_analysis.json（過去実績）
  - data/posting_queue.json（現在のキュー状態）
  - data/trend_insights.json（トレンド情報）[新規]
  - content/stock.csv（コンテンツストック）
  - data/template_scores.json（テンプレート評価）[新規]

処理:
  1. トレンド分析
     - TikTok Creative Center RSS/公開API → 看護師系トレンドワード収集
     - Google Trends API（pytrends）→ 看護師+転職の検索トレンド
     - 競合アカウント公開投稿のフック文パターン収集（手動入力 → JSON蓄積）
     ※ Webスクレイピング不要: 公開API + 手動インプットのハイブリッド

  2. コンテンツMIX計算
     - 現在のキュー内カテゴリ分布を取得
     - MIX_RATIOS（40:25:20:5:10）との乖離を計算
     - 不足カテゴリに重み付けして生成数を決定
     → 既存: ai_content_engine.py の _allocate_categories() をそのまま活用

  3. 行動経済学テンプレート選択
     - data/template_scores.json から過去スコアを参照
     - テンプレートプール:
       ・損失回避型:「知らないと損する」「○○しないと年収が下がる」
       ・社会的証明型:「○○人がやってる」「みんなが保存した」
       ・希少性型:「神奈川限定」「今だけ」
       ・好奇心ギャップ型:「○○したら意外な結果に」
       ・自己参照型:「あなたの年収、適正？」
     - 同じテンプレートの連続使用を回避（最低3投稿空ける）
     - スコア上位テンプレートの出現頻度を高める（重み付き抽選）

  4. 台本JSON生成
     - カテゴリ + テンプレート + トレンドワード → プロンプト組み立て
     - Cloudflare Workers AI（Llama 3.3 70B）で台本生成
     → 既存: ai_content_engine.py の _generate_content_with_ai() を拡張

出力:
  - data/content_plan.json（企画済み台本リスト）
```

### Phase 2: 生成（完全自動）

```
入力:
  - data/content_plan.json（Phase 1の出力）

処理:
  1. 台本JSON → カルーセル画像7枚
     → 既存: generate_carousel.py をそのまま使用
     - Slide 1: フック（ダークBG、大文字）
     - Slide 2-5: コンテンツ（ダーク/ライト交互）
     - Slide 6: リビール（アクセントグラデーション）
     - Slide 7: CTA（ブランドグラデーション）

  2. ロビー君キャラクターテキスト自動挿入 [新規]
     - 各スライドの左下に「ロビー」の一言コメント追加
     - キャラクター設定:
       ・1枚目: 「えっ...」「まじ？」（驚き系）
       ・2-5枚目: 「それな」「わかる」（共感系）
       ・6枚目: 「！！」「知らなかった...」（リビール系）
     - generate_carousel.py の各スライド関数末尾にテキスト追加

  3. キャプション生成
     → 既存: ai_content_engine.py の台本JSONにcaptionフィールドあり

  4. ハッシュタグ選択
     → 既存: HASHTAG_SETS からカテゴリ別に選択

  5. 品質スコアリング [新規]
     - テキストチェック:
       ・フック20文字以内 ✓
       ・キャプション200文字以内 ✓
       ・スライド6枚以上 ✓
       ・ハッシュタグ5個以内 ✓
     - ビジュアルチェック:
       ・PNG生成成功（7ファイル存在）✓
       ・ファイルサイズ異常なし（10KB以上、5MB以下）✓
     - 心理学チェック（AI審査）:
       ・ペルソナ適合度
       ・フック強度
       ・法的遵守
       ・CTA適切性
       ・共感度
     → 既存: ai_content_engine.py の cmd_review() を拡張

  6. 不合格時の自動再生成（最大3回リトライ）
     - スコア5以下 → 再生成
     - 3回失敗 → status="failed"としてスキップ、Slack警告
     → 既存: cmd_auto() 内の self-correction ロジックを拡張

出力:
  - content/generated/<batch_name>/<content_id>.json（台本）
  - content/generated/<batch_name>/<content_id>/（スライドPNG 7枚）
  - data/posting_queue.json（キューに追加）
```

### Phase 3: レビュー（自動+人間）

```
入力:
  - data/posting_queue.json（status="pending"のエントリ）
  - AIレビュースコア（Phase 2で付与）

処理:
  1. スコア判定による自動振り分け
     ┌─────────────────────────────────────────────┐
     │ スコア 8-10: 自動承認 → status="approved"     │
     │ スコア 6-7:  Slack通知 → 人間レビュー待ち      │
     │ スコア 1-5:  自動却下 → 再生成キューへ          │
     └─────────────────────────────────────────────┘

  2. Slack通知（スコア6-7の場合）[新規拡張]
     - カルーセル1枚目のPNG画像をSlackにアップロード
     - キャプション全文 + ハッシュタグをテキスト表示
     - AIレビューのissues/suggestionを表示
     - Slack上でのリアクション操作:
       ・承認ボタン（Slackコマンド: !approve <id>）
       ・却下ボタン（Slackコマンド: !reject <id>）
       ・修正指示（自由文で返信 → 指示キューに保存）
     → 既存: slack_commander.py にコマンド追加

  3. タイムアウト処理
     - 6時間以内に人間レビューなし → 自動承認
     - （看護師ターゲットなので即時性より品質を担保）

出力:
  - data/posting_queue.json（status更新: approved / rejected）
```

### Phase 4: 投稿（半自動）

```
入力:
  - data/posting_queue.json（status="approved"のエントリ）

処理:
  1. 投稿準備（毎日 17:30 cron）
     → 既存: pdca_sns_post.sh → sns_workflow.py --prepare-next

  2. content/ready/ にスライド+テキスト配置
     → 既存: sns_workflow.py の prepare_next()
     配置内容:
       content/ready/YYYYMMDD_<content_id>/
         ├── slide_1.png ... slide_7.png
         ├── caption.txt（キャプション + ハッシュタグ）
         ├── hashtags.txt
         └── meta.json（投稿メタデータ）

  3. Slackに投稿用コンテンツ送信 [新規拡張]
     - 1枚目画像のサムネイルをSlackアップロード
     - キャプション全文（コピペ可能な形式）
     - ハッシュタグ（コピペ可能な形式）
     - 投稿先プラットフォーム指示
     - 投稿完了コマンド: `!posted <id>`

  4. 人間がTikTok/Instagramにアップロード
     - Buffer経由 or 直接アップ
     - 音楽選択は人間が担当

  5. 投稿完了マーク
     → 既存: sns_workflow.py --mark-posted <ID>
     → Slackコマンド: !posted <ID>

出力:
  - data/posting_queue.json（status="posted", posted_at更新）
```

### Phase 5: 分析（自動）

```
入力:
  - data/posting_queue.json（status="posted"のエントリ）
  - TikTok/Instagram パフォーマンスデータ（手動入力 or API）

処理:
  1. パフォーマンスデータ収集（投稿24h後）[新規]
     - 手動入力ルート:
       Slackコマンド: !perf <id> views=1000 likes=50 saves=30 comments=5
     - 自動入力ルート（Phase2以降）:
       TikTok Business API（アカウント成長後に申請）

  2. スコアリング [新規]
     - エンゲージメント率 = (likes + saves + comments) / views * 100
     - 保存率 = saves / views * 100
     - コメント率 = comments / views * 100
     - 総合スコア = 加重平均（保存率 x 0.4 + エンゲージメント率 x 0.3 + views正規化 x 0.3）

  3. テンプレート評価更新 [新規]
     - 投稿に使用したテンプレートIDを紐付け
     - テンプレートごとの平均スコアを計算
     - data/template_scores.json を更新
     - 上位テンプレートの出現頻度を自動引き上げ

  4. 勝ちパターン検出 [新規]
     - 保存率3%以上 → ★勝ちパターン
     - 再生数1万以上 → ★★バズパターン
     - パターンの特徴を抽出:
       ・カテゴリ、テンプレートタイプ、フックの主語、投稿時間、曜日
     - data/agent_state.json の agentMemory に蓄積
     - 次回のPhase 1で参照

  5. 失敗パターン記録
     - 再生数500未満 → 失敗フラグ
     - 失敗原因のAI分析（Cloudflare Workers AI）
     - 同じパターンの繰り返しを防ぐ

出力:
  - data/performance_analysis.json（更新）
  - data/template_scores.json（更新）
  - data/agent_state.json の agentMemory（更新）
  - content/stock.csv（パフォーマンスデータ追記）
```

---

## 3. 各Pythonスクリプトの責務と連携

### 既存スクリプト（拡張）

| スクリプト | 現在の責務 | 拡張内容 |
|-----------|-----------|---------|
| `ai_content_engine.py` | AI台本生成、品質レビュー、スケジュール、全自動モード | テンプレート選択ロジック追加、トレンド情報の取り込み、スコア閾値による3段階振り分け、リトライ回数の制御強化 |
| `generate_carousel.py` | 7枚カルーセル画像生成（Pillow） | ロビー君コメント自動挿入メソッド追加 |
| `sns_workflow.py` | キュー管理、投稿準備、mark-posted | パフォーマンスデータ入力コマンド追加（`--perf`）、approve/rejectコマンド追加 |

### 新規スクリプト

| スクリプト | 責務 | 主要関数 |
|-----------|------|---------|
| `trend_collector.py` | トレンド情報収集 | `collect_google_trends()`, `load_manual_trends()`, `save_trend_insights()` |
| `template_manager.py` | テンプレートスコア管理 | `select_template()`, `update_scores()`, `get_anti_repeat_filter()` |
| `performance_tracker.py` | 投稿パフォーマンス追跡・分析 | `record_performance()`, `calculate_scores()`, `detect_patterns()`, `update_template_feedback()` |
| `pipeline_orchestrator.py` | 5フェーズ統合オーケストレーター | `run_full_pipeline()`, `run_phase()`, `check_health()` |

### スクリプト連携図

```
pipeline_orchestrator.py（統合制御）
  │
  ├─→ Phase 1: trend_collector.py → template_manager.py → ai_content_engine.py --plan
  │
  ├─→ Phase 2: ai_content_engine.py --generate → generate_carousel.py
  │
  ├─→ Phase 3: ai_content_engine.py --review → slack_bridge.py（通知）
  │                                            → slack_commander.py（コマンド受信）
  │
  ├─→ Phase 4: sns_workflow.py --prepare-next → slack_bridge.py（投稿テキスト送信）
  │
  └─→ Phase 5: performance_tracker.py → template_manager.py → agent_state.json
```

---

## 4. cron実行タイムライン（1日の全自動スケジュール）

```
時刻    スクリプト                          内容
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[毎日]
04:00   pdca_seo_batch.sh                  SEO改善（既存）
05:00   (日曜のみ) pdca_weekly_content.sh   週次コンテンツバッチ生成（既存）
06:00   pdca_ai_marketing.sh               日次AIマーケティングPDCA（既存）
        └→ pipeline_orchestrator.py          統合パイプライン実行
           ├→ Phase 1: 企画                  トレンド収集 + MIX計算 + テンプレート選択
           ├→ Phase 2: 生成                  台本生成 + カルーセル画像 + 品質スコア
           └→ Phase 3: レビュー              自動承認/却下/Slack通知
07:00   pdca_healthcheck.sh                障害監視（既存）
10:00   pdca_competitor.sh                 競合分析（既存）
12:00   (新規) performance_tracker.py       前日投稿のパフォーマンスデータ確認
        └→ Slackで手動入力を促すリマインダー送信
15:00   pdca_content.sh                    コンテンツ生成補充（既存）
17:30   pdca_sns_post.sh                   投稿準備（既存）
        └→ sns_workflow.py --prepare-next
        └→ Slackにコピペ用テキスト送信
18:00   (想定) 人間がTikTok/Instagramにアップロード
23:00   pdca_review.sh                     日次レビュー（既存）

[5分間隔]
*/5     slack_commander.py --once           Slack監視（既存）
        └→ !approve, !reject, !posted,
           !perf コマンドを処理

[日曜のみ]
05:00   pdca_weekly_content.sh             週次バッチ（Phase 1-3を一括実行）
06:00   pdca_weekly.sh                     週次総括レポート
```

### 新規cronエントリ（追加分）

```crontab
# パフォーマンスリマインダー（毎日12:00 — 前日投稿の24h後チェック）
0 12 * * 1-6 cd ~/robby-the-match && /usr/bin/python3 scripts/performance_tracker.py --remind >> logs/performance_tracker.log 2>&1
```

---

## 5. 新規作成ファイル一覧と概要設計

### 5.1 `scripts/pipeline_orchestrator.py` — 統合オーケストレーター

```
責務: 5フェーズのパイプラインを統合制御する司令塔

主要クラス/関数:
  class PipelineOrchestrator:
      def __init__(self):
          # 各フェーズのスクリプトパスを保持
          # ログ設定

      def run_full_pipeline(self, mode="daily"):
          """全フェーズ実行（daily or weekly）"""
          # daily: Phase 1-3 のみ（投稿準備はcron 17:30で別途）
          # weekly: Phase 1-3 を7件分一括実行

      def run_phase(self, phase_num: int, **kwargs):
          """特定フェーズのみ実行"""

      def check_health(self) -> dict:
          """パイプライン全体のヘルス状態を返す"""
          # キュー残量、生成失敗率、レビュー通過率、等

      def _phase1_plan(self) -> list:
          """Phase 1: 企画"""
          # trend_collector → template_manager → ai_content_engine --plan
          # 戻り値: 企画済みコンテンツプランのリスト

      def _phase2_generate(self, plan: list) -> list:
          """Phase 2: 生成"""
          # ai_content_engine --generate
          # リトライロジック（最大3回、スコア5以下の場合）
          # 戻り値: 生成済みコンテンツIDのリスト

      def _phase3_review(self, content_ids: list) -> dict:
          """Phase 3: レビュー"""
          # ai_content_engine --review
          # スコア別振り分け（8+自動承認、6-7 Slack、5-却下）
          # 戻り値: {approved: [], needs_review: [], rejected: []}

      def _send_review_to_slack(self, post_data: dict):
          """Slack通知でレビュー依頼"""
          # 1枚目画像 + キャプション + AIレビュー結果を送信

CLI:
  --daily         日次パイプライン（Phase 1-3）
  --weekly        週次パイプライン（7件一括）
  --phase N       特定フェーズのみ実行
  --health        ヘルスチェック
  --status        全フェーズの状態表示

依存:
  - ai_content_engine.py（importして直接呼び出し）
  - generate_carousel.py（ai_content_engine経由で呼び出し）
  - trend_collector.py（importして直接呼び出し）
  - template_manager.py（importして直接呼び出し）
  - slack_bridge.py（subprocessで呼び出し）
```

### 5.2 `scripts/trend_collector.py` — トレンド情報収集

```
責務: 看護師系SNSトレンドを収集し、コンテンツ企画に活用する

主要関数:
  def collect_google_trends(keywords: list) -> dict:
      """Google Trends API（pytrends）で検索トレンドを取得"""
      # キーワード: ["看護師 転職", "看護師 あるある", "看護師 給料"]
      # 直近7日間のトレンド推移を取得
      # 注意: pytrends は非公式、レート制限あり。1日1回で十分

  def load_manual_trends(file_path: str) -> list:
      """手動入力のトレンド情報をJSONから読み込み"""
      # data/manual_trends.json
      # フォーマット: [{"topic": "...", "source": "tiktok/instagram", "date": "..."}]
      # 人間がSlackで「!trend <トレンドワード>」で追加

  def analyze_trending_hooks(queue_path: str) -> list:
      """過去の投稿キューから高パフォーマンスなフックパターンを抽出"""
      # posting_queue.json の posted エントリからhookパターンを分析

  def save_trend_insights(insights: dict, output_path: str):
      """トレンド分析結果をJSONに保存"""
      # data/trend_insights.json

CLI:
  --collect        全ソースからトレンド収集
  --manual "word"  手動でトレンドワード追加
  --show           現在のトレンド情報表示

データ出力:
  data/trend_insights.json:
  {
    "collected_at": "2026-02-24T06:00:00",
    "google_trends": {...},
    "manual_trends": [...],
    "high_performing_hooks": [...],
    "recommended_topics": [
      {"topic": "...", "category": "あるある", "reason": "...", "score": 8}
    ]
  }

コスト: 無料（pytrends + ローカルデータ分析のみ）
```

### 5.3 `scripts/template_manager.py` — テンプレートスコア管理

```
責務: 行動経済学テンプレートの選択と評価更新

主要クラス/関数:
  PSYCHOLOGY_TEMPLATES = {
      "loss_aversion": {
          "name": "損失回避型",
          "patterns": [
              "知らないと損する{topic}",
              "{topic}しないと{negative_outcome}",
              "まだ{old_way}してるの？",
          ],
          "base_score": 7,
      },
      "social_proof": {
          "name": "社会的証明型",
          "patterns": [
              "{number}人がやってる{topic}",
              "みんなが保存した{topic}",
              "看護師{number}人に聞いた{topic}",
          ],
          "base_score": 7,
      },
      "scarcity": {
          "name": "希少性型",
          "patterns": [
              "神奈川限定{topic}",
              "{topic}は今だけ",
          ],
          "base_score": 6,
      },
      "curiosity_gap": {
          "name": "好奇心ギャップ型",
          "patterns": [
              "{action}したら意外な結果に",
              "{person}に{topic}見せたら{reaction}",
              "AIに{topic}聞いたら{unexpected}",
          ],
          "base_score": 8,
      },
      "self_reference": {
          "name": "自己参照型",
          "patterns": [
              "あなたの{metric}、適正？",
              "{experience_years}年目の{topic}",
          ],
          "base_score": 7,
      },
  }

  def select_template(
      category: str,
      recent_history: list,
      template_scores: dict,
  ) -> dict:
      """テンプレートを重み付き抽選で選択"""
      # 1. 直近3投稿で使ったテンプレートを除外
      # 2. カテゴリとの相性を考慮
      # 3. スコアに比例した確率で抽選
      # 戻り値: {"template_id": "...", "pattern": "...", "variables": {...}}

  def update_scores(template_id: str, performance_score: float):
      """投稿結果に基づいてテンプレートスコアを更新"""
      # 指数移動平均: new_score = 0.7 * old_score + 0.3 * performance_score

  def get_anti_repeat_filter(queue_path: str, lookback: int = 3) -> list:
      """直近N投稿で使ったテンプレートIDリストを返す"""

  def load_scores() -> dict:
      """data/template_scores.json を読み込み"""

  def save_scores(scores: dict):
      """data/template_scores.json に保存"""

CLI:
  --select <category>   テンプレートを1つ選択して表示
  --scores              全テンプレートのスコア一覧
  --update <id> <score> スコアを手動更新

データ出力:
  data/template_scores.json:
  {
    "updated_at": "...",
    "templates": {
      "loss_aversion": {
        "score": 7.2,
        "uses": 5,
        "avg_performance": 6.8,
        "last_used": "2026-02-22"
      },
      ...
    }
  }
```

### 5.4 `scripts/performance_tracker.py` — パフォーマンス追跡

```
責務: 投稿パフォーマンスの収集・分析・フィードバックループ

主要関数:
  def record_performance(
      post_id: int,
      views: int,
      likes: int,
      saves: int,
      comments: int,
  ):
      """投稿のパフォーマンスデータを記録"""
      # posting_queue.json の performance フィールドを更新
      # content/stock.csv にもデータ追記

  def calculate_scores(post_data: dict) -> dict:
      """パフォーマンススコアを計算"""
      # engagement_rate = (likes + saves + comments) / views * 100
      # save_rate = saves / views * 100
      # comment_rate = comments / views * 100
      # total_score = save_rate * 0.4 + engagement_rate * 0.3 + normalized_views * 0.3
      # 戻り値: {"total": 7.5, "engagement_rate": 3.2, "save_rate": 2.1, ...}

  def detect_patterns(min_posts: int = 5) -> dict:
      """勝ちパターン・負けパターンを検出"""
      # 条件: 最低5投稿のデータが蓄積してから実行
      # 分析軸:
      #   - カテゴリ別平均スコア
      #   - テンプレート別平均スコア
      #   - フックの主語別（師長、彼氏、先輩、AI等）
      #   - 投稿時間帯別
      #   - 曜日別
      # 戻り値: {"winners": [...], "losers": [...], "insights": [...]}

  def update_template_feedback(post_id: int, performance_score: float):
      """テンプレートスコアにフィードバック"""
      # template_manager.update_scores() を呼び出し

  def send_performance_reminder():
      """Slackでパフォーマンス入力リマインダーを送信"""
      # 投稿済み & パフォーマンス未入力のエントリをリスト
      # 入力方法のガイドテキストをSlack送信

  def generate_weekly_report() -> str:
      """週次パフォーマンスレポートを生成"""
      # 今週の投稿数、平均スコア、勝ちパターン、改善点

CLI:
  --record <id> --views N --likes N --saves N --comments N
  --remind          パフォーマンス入力リマインダー送信
  --analyze         勝ちパターン分析
  --report          週次レポート生成
  --status          未入力の投稿一覧

データ入出力:
  入力: data/posting_queue.json, data/template_scores.json
  出力: data/performance_analysis.json（更新）
        data/template_scores.json（フィードバック）
        data/agent_state.json の agentMemory（パターン蓄積）
```

### 5.5 新規データファイル

| ファイルパス | 用途 | 作成タイミング |
|-------------|------|--------------|
| `data/trend_insights.json` | トレンド分析結果 | trend_collector.py 実行時 |
| `data/template_scores.json` | テンプレート評価スコア | template_manager.py 初回実行時に初期化 |
| `data/manual_trends.json` | 手動入力トレンドワード | Slackコマンド `!trend` で追加 |

---

## 6. 既存スクリプトへの変更点

### 6.1 `ai_content_engine.py` への変更

```python
# 変更1: _generate_content_with_ai() にテンプレート情報を渡す
# 現在: category, cta_type, content_id, hook_hint のみ
# 追加: template_type, trend_keywords パラメータ

# 変更2: cmd_review() のスコア閾値を3段階に
# 現在: score < 6 → rejected
# 新規: score >= 8 → approved (自動承認)
#        score 6-7 → needs_review (Slack通知)
#        score <= 5 → rejected (自動却下+再生成)

# 変更3: cmd_auto() のリトライ制御
# 現在: rejected → 再生成1回
# 新規: rejected → 最大3回リトライ、3回失敗でfailed

# 変更4: 生成時にtemplate_idをメタデータに記録
# content_data["_template_id"] = selected_template["template_id"]
```

### 6.2 `generate_carousel.py` への変更

```python
# 変更1: 各スライド関数にロビー君コメント表示オプション追加
# generate_slide_hook() に robby_comment パラメータ追加
# generate_slide_content() に robby_comment パラメータ追加
# generate_slide_reveal() に robby_comment パラメータ追加

# 実装: スライド左下（SAFE_LEFT + 20, CANVAS_H - SAFE_BOTTOM - 80）に
#        小さめフォント（20px）で吹き出し風テキストを描画
#        半透明背景の角丸矩形 + テキスト
```

### 6.3 `sns_workflow.py` への変更

```python
# 変更1: --perf コマンド追加（パフォーマンスデータ入力）
# parser.add_argument("--perf", type=int, metavar="ID")
# parser.add_argument("--views", type=int)
# parser.add_argument("--likes", type=int)
# parser.add_argument("--saves", type=int)
# parser.add_argument("--comments", type=int)

# 変更2: --approve / --reject コマンド追加
# parser.add_argument("--approve", type=int, metavar="ID")
# parser.add_argument("--reject", type=int, metavar="ID")
```

### 6.4 `slack_commander.py` への変更

```python
# 変更1: 新規Slackコマンド追加
# !approve <id>    → sns_workflow.py --approve <id>
# !reject <id>     → sns_workflow.py --reject <id>
# !posted <id>     → sns_workflow.py --mark-posted <id>
# !perf <id> views=N likes=N saves=N comments=N
#                  → performance_tracker.py --record <id> ...
# !trend <keyword> → trend_collector.py --manual "<keyword>"
# !pipeline        → pipeline_orchestrator.py --status
```

### 6.5 `pdca_ai_marketing.sh` への変更

```bash
# 変更: DO Phase で content_pipeline.py の代わりに
#        pipeline_orchestrator.py --daily を呼び出す
# 現在: python3 "$PROJECT_DIR/scripts/content_pipeline.py" --auto
# 新規: python3 "$PROJECT_DIR/scripts/pipeline_orchestrator.py" --daily
```

---

## 7. データフロー図

```
                    ┌───────────────────────────────────┐
                    │        data/ ディレクトリ           │
                    └───────────────────────────────────┘

  [入力データ]                                    [出力データ]

  posting_queue.json ◄───────────────────────────► posting_queue.json
  (キュー状態)          全フェーズが読み書き          (ステータス更新)

  content_plan.json ◄─── Phase 1 で書き込み ───► Phase 2 で読み込み

  trend_insights.json ◄─ trend_collector.py ───► Phase 1 で参照

  template_scores.json ◄─ template_manager.py ─► Phase 1 で参照
                         Phase 5 で更新            Phase 5 でフィードバック

  performance_analysis.json ◄─ Phase 5 ────────► Phase 1 で参照

  agent_state.json ◄── 全エージェントが読み書き ──► 共有コンテキスト

  stock.csv ◄───── Phase 5 でパフォーマンス追記 ──► Phase 1 で参照

  manual_trends.json ◄── Slackコマンド !trend ──► Phase 1 で参照


                    ┌───────────────────────────────────┐
                    │      content/ ディレクトリ          │
                    └───────────────────────────────────┘

  content/generated/<batch>/<id>.json ── Phase 2 出力
  content/generated/<batch>/<id>/*.png ── Phase 2 出力（カルーセル画像）
  content/ready/<date>_<id>/ ─────────── Phase 4 出力（投稿準備済み）
```

---

## 8. エラーハンドリング設計

```
[Cloudflare Workers AI障害]
  → 検出: call_cloudflare_ai() のリトライ失敗（3回）
  → 対応: Slack警告送信 + 生成をスキップ + 既存キュー在庫で運用
  → 復旧: 次回cron実行時に自動リトライ

[カルーセル画像生成失敗]
  → 検出: generate_carousel.py の戻り値が空
  → 対応: キューにはJSON情報で登録（status="pending"）
  → 復旧: 次回 --prepare-next 時に再生成を試行

[キュー枯渇（pending < 3）]
  → 検出: pdca_ai_marketing.sh の最後のチェック
  → 対応: 緊急生成タスクを発行 + Slack警告
  → 復旧: 次回パイプライン実行で補充

[Slack通知失敗]
  → 検出: subprocess の戻り値チェック
  → 対応: ログに記録、処理は継続（Slackは補助）
  → 復旧: 次回の通知で回復

[全自動パイプライン全体障害]
  → 検出: pipeline_orchestrator.py の各フェーズ戻り値
  → 対応: 失敗フェーズの特定 + Slack詳細レポート + agent_state更新
  → 復旧: --phase N で特定フェーズだけ再実行可能
```

---

## 9. 実装優先順位

```
[Sprint 1: 最小動作版] — 1-2日
  1. pipeline_orchestrator.py の骨格（Phase 1-3の統合呼び出しのみ）
  2. ai_content_engine.py のスコア3段階振り分け修正
  3. sns_workflow.py に --approve / --reject 追加
  4. slack_commander.py に !approve / !reject / !posted 追加

[Sprint 2: テンプレートシステム] — 1-2日
  5. template_manager.py（テンプレート定義 + 選択ロジック）
  6. ai_content_engine.py にテンプレート連携追加
  7. data/template_scores.json 初期化

[Sprint 3: パフォーマンス追跡] — 1-2日
  8. performance_tracker.py（データ入力 + スコアリング）
  9. sns_workflow.py に --perf 追加
  10. slack_commander.py に !perf 追加
  11. cron に 12:00 リマインダー追加

[Sprint 4: トレンド収集] — 1日
  12. trend_collector.py（Google Trends + 手動入力）
  13. slack_commander.py に !trend 追加
  14. pipeline_orchestrator.py にトレンド統合

[Sprint 5: ロビー君キャラ強化] — 0.5日
  15. generate_carousel.py にロビー君コメント追加

[Sprint 6: 分析・学習ループ完成] — 1日
  16. performance_tracker.py のパターン検出
  17. template_manager.py のフィードバックループ
  18. 週次レポートの自動生成
```

---

## 10. コスト見積もり

```
[変わらないもの]
  Cloudflare Workers AI: 無料（10,000 neurons/day — テキスト生成のみ）
  Pillow画像生成: 無料（ローカルCPU）
  cron実行: 無料（Mac Mini常時稼働前提）
  Slack通知: 無料（Bot Token既存）
  Google Trends (pytrends): 無料（非公式、レート制限注意）

[追加コスト]
  pytrends pip install: 無料
  新規JSONファイル: ディスク容量のみ（無視できる）

[合計追加コスト: 0円/月]

※ 全て既存の無料インフラ（Cloudflare Workers AI + Pillow + cron）の上に構築。
   新たな外部サービス契約は不要。
```

---

## 11. ディレクトリ構成（変更後）

```
~/robby-the-match/
├── scripts/
│   ├── ai_content_engine.py      ← 拡張（テンプレート連携、3段階スコア）
│   ├── generate_carousel.py      ← 拡張（ロビー君コメント）
│   ├── sns_workflow.py           ← 拡張（--perf, --approve, --reject）
│   ├── slack_commander.py        ← 拡張（新コマンド5種）
│   ├── pipeline_orchestrator.py  ← [新規] 統合オーケストレーター
│   ├── trend_collector.py        ← [新規] トレンド情報収集
│   ├── template_manager.py       ← [新規] テンプレートスコア管理
│   ├── performance_tracker.py    ← [新規] パフォーマンス追跡
│   ├── pdca_ai_marketing.sh      ← 変更（pipeline_orchestrator呼び出し）
│   ├── slack_bridge.py           ← 既存（変更なし）
│   ├── slack_report.py           ← 既存（変更なし）
│   └── ... (その他既存スクリプト)
│
├── data/
│   ├── posting_queue.json        ← 既存（フィールド追加: _template_id）
│   ├── content_plan.json         ← 既存（変更なし）
│   ├── agent_state.json          ← 既存（agentMemoryにパターン蓄積）
│   ├── performance_analysis.json ← 既存（Phase 5で更新）
│   ├── template_scores.json      ← [新規] テンプレート評価
│   ├── trend_insights.json       ← [新規] トレンド分析結果
│   ├── manual_trends.json        ← [新規] 手動トレンド入力
│   └── stock.csv                 ← 既存（パフォーマンスデータ追記）
│
├── content/
│   ├── generated/                ← 既存（変更なし）
│   ├── ready/                    ← 既存（変更なし）
│   ├── base-images/              ← 既存（変更なし）
│   └── templates/                ← 既存（変更なし）
│
└── logs/
    ├── pipeline_orchestrator_YYYYMMDD.log  ← [新規]
    ├── performance_tracker.log             ← [新規]
    └── ... (既存ログ)
```

---

## 12. Slackコマンド一覧（統合版）

```
[既存コマンド]
  !status          キュー状態 + KPI表示
  !kpi             KPIサマリ
  !push            git push実行

[新規コマンド]
  !approve <id>    投稿を承認（status → approved）
  !reject <id>     投稿を却下（status → rejected → 再生成キュー）
  !posted <id>     投稿完了マーク（status → posted）
  !perf <id> views=N likes=N saves=N comments=N
                   パフォーマンスデータ入力
  !trend <keyword> トレンドワード手動追加
  !pipeline        パイプライン全体ステータス
  !templates       テンプレートスコア一覧
  !next            次に投稿予定のコンテンツプレビュー
```

---

## 13. 設計判断の根拠

### なぜ新規フレームワークを使わないか
既存の `ai_content_engine.py` + `generate_carousel.py` + `sns_workflow.py` が
既に動作しており、データ構造（posting_queue.json）も安定している。
ゼロから作り直すとデータ移行の手間とリグレッションリスクが発生する。
既存コードを拡張する形が最もコスト効率が良い。

### なぜSlackを中心にしたか
- 平島禎之が日常的にSlackを使っている
- 画像プレビュー、ボタン操作、コマンド入力が1箇所で完結する
- 既に slack_bridge.py / slack_commander.py のインフラが稼働中
- 新たなUI開発コストがゼロ

### なぜTikTok APIを使わないか（Phase 4）
- TikTok Creator APIはビジネスアカウント要件がある
- 現在フォロワー0のため、API申請が通らない可能性が高い
- 手動アップロード（1日1回、2分程度）で十分回る規模
- フォロワー1,000名超えてからAPI連携を検討

### なぜpytrendsを選んだか（Phase 1）
- 無料
- 看護師系キーワードのトレンド推移が取れる
- 非公式APIだがレート制限を守れば安定（1日1回の実行で十分）
- pip install pytrends だけで導入完了
