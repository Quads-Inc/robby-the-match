# ROBBY THE MATCH - 統合計画書

## 作成日: 2026-02-20
## 概要

project1（claudecodeproject1）のメインLP・AIチャットウィジェット・Cloudflare Workers API・Slack連携を
robby-the-matchリポジトリに統合し、GitHub Pages + Cloudflare Workersでデプロイ可能な状態にする。

---

## 1. 統合対象コンポーネント

### project1 から統合するもの

| コンポーネント | ファイル | 役割 |
|---|---|---|
| メインLP（総合LP） | index.html | 求職者+医療機関 両面の総合ランディングページ |
| スタイルシート | style.css | メインLPのデザイン（Warm Cream + Teal テーマ） |
| メインスクリプト | script.js | UIアニメーション・フォーム送信・マッチング表示 |
| 設定ファイル | config.js | ブランド名・API URL・病院データ・デザイン設定の一括管理 |
| AIチャットウィジェット | chat.js, chat.css | 電話番号ゲート付きAI転職相談チャット（5ステップ） |
| 病院DBデータ | data/areas.js | 10エリア59施設の詳細データ（病院機能報告ベース） |
| 求人・給与データ | data/jobs.js | 職種別給与テーブル・勤務形態・外部公開求人リスト |
| Cloudflare Workers API | api/worker.js, api/wrangler.toml | フォーム送信・Slack通知・AIチャット・Google Sheets連携 |
| OGP画像 | assets/ogp.svg | ソーシャルメディア共有用画像 |
| Slack Bot | slack-bot.js | Slack経由でClaude Codeを呼び出すブリッジ |
| Slack通知 | slack-notify.js | プロジェクト進捗・メッセージ送信ユーティリティ |
| 法的ページ | privacy.html, terms.html | 個人情報保護方針・利用規約 |
| 404ページ | 404.html | GitHub Pages用カスタム404 |
| SEOファイル | robots.txt, sitemap.xml | 検索エンジン最適化 |
| マーケティング資料 | marketing/ | Indeed・Google Business・SNS計画 |
| レポート | reports/ | AI設計・デザインリサーチ・マーケティング計画・サイト監査 |
| 提案書 | proposal.html, proposal.css | クライアント向け提案書 |
| ダッシュボード | dashboard.html, dashboard.css, dashboard.js | 管理用ダッシュボード |

### robby-the-matchの既存コンポーネント（保持）

| コンポーネント | ファイル | 役割 |
|---|---|---|
| LP-A（求職者向けLP） | lp/job-seeker/index.html | SEO特化の求職者向け簡易LP（LINE CTA） |
| SNSコンテンツ素材 | content/ | ベース画像・テンプレート・生成済みスライド |
| 自動化スクリプト | scripts/ | 画像生成・スライド生成・Slack通知・PDCA自動化 |
| データディレクトリ | data/ | （今後利用予定） |
| 設定ファイル | CLAUDE.md | 戦略・ペルソナ・実行指針 |
| 進捗ログ | PROGRESS.md | 日次進捗管理 |
| 環境変数 | .env | Slack Bot Token等 |

---

## 2. LP役割分担

### メインLP（index.html） = 総合ランディングページ
- **配置**: リポジトリルート `/index.html`
- **URL**: `https://quads-nurse.com/`
- **対象**: 求職者（看護師・PT） + 医療機関（病院事務長）
- **機能**:
  - 登録フォーム（Cloudflare Workers → Slack + Google Sheets）
  - AIチャットウィジェット（Claude Haiku 4.5経由）
  - 病院DB検索・マッチング表示
  - FAQ（構造化データ付き）
  - 利用者の声
  - 手数料比較・ミッション説明
- **SEO**: schema.org構造化データ（WebSite, Organization, EmploymentAgency, FAQPage, BreadcrumbList）
- **GA4**: トラッキングコード設置済み

### LP-A（lp/job-seeker/index.html） = 求職者特化LP
- **配置**: `/lp/job-seeker/index.html`
- **URL**: `https://quads-nurse.com/lp/job-seeker/`
- **対象**: 看護師（TikTok/Instagram広告からの流入）
- **機能**:
  - 手数料比較表（シンプル）
  - 3ステップ説明
  - LINE CTA（友だち追加）
  - FAQ
- **特徴**: 軽量・高速・モバイルファースト・SNS広告用に最適化

### 役割の違い
| 項目 | メインLP | LP-A |
|---|---|---|
| 目的 | 総合ブランディング + 登録 | SNS広告経由のLINE登録 |
| 対象 | 求職者 + 医療機関 | 求職者のみ |
| CTA | 登録フォーム + AIチャット | LINE友だち追加 |
| デザイン | リッチ（アニメーション・パララックス） | シンプル・軽量 |
| 技術 | config.js + chat.js + data/*.js | インラインCSS・自己完結 |
| 流入元 | SEO・直接アクセス・紹介 | TikTok・Instagram・広告 |

---

## 3. ディレクトリ構造（統合後）

```
robby-the-match/
|-- index.html              [NEW] メインLP（project1から）
|-- style.css               [NEW] メインLPスタイル
|-- script.js               [NEW] メインLPスクリプト
|-- config.js               [NEW] 設定ファイル
|-- chat.js                 [NEW] AIチャットウィジェット
|-- chat.css                [NEW] チャットスタイル
|-- privacy.html            [NEW] 個人情報保護方針
|-- terms.html              [NEW] 利用規約
|-- 404.html                [NEW] カスタム404
|-- robots.txt              [NEW] SEO用
|-- sitemap.xml             [EXISTING] 既存（更新予定）
|-- slack-bot.js            [NEW] Slack Claude Codeブリッジ
|-- slack-notify.js         [NEW] Slack通知ユーティリティ
|-- proposal.html           [NEW] 提案書
|-- proposal.css            [NEW] 提案書スタイル
|-- dashboard.html          [NEW] 管理ダッシュボード
|-- dashboard.css           [NEW] ダッシュボードスタイル
|-- dashboard.js            [NEW] ダッシュボードスクリプト
|
|-- data/                   [MERGE] エリア・求人DB
|   |-- areas.js            [NEW] 10エリア59施設DB
|   |-- jobs.js             [NEW] 給与・勤務・求人データ
|
|-- api/                    [NEW] Cloudflare Workers API
|   |-- worker.js           Cloudflare Workers本体
|   |-- wrangler.toml       デプロイ設定
|   |-- README.md           APIドキュメント
|
|-- assets/                 [NEW] 静的アセット
|   |-- ogp.svg             OGP画像
|
|-- marketing/              [NEW] マーケティング資料
|   |-- google-business.md
|   |-- indeed-nurse.md
|   |-- indeed-pt.md
|   |-- sns-plan.md
|
|-- reports/                [NEW] レポート・分析
|   |-- ai-architecture.md
|   |-- design-research.md
|   |-- marketing-plan.md
|   |-- site-audit.md
|
|-- lp/                     [EXISTING] サブLP群
|   |-- job-seeker/         LP-A（求職者向け）
|   |   |-- index.html
|   |   |-- area/           エリア別ページ（予定）
|   |   |-- guide/          ガイドページ（予定）
|   |-- facility/           LP-B（医療機関向け、予定）
|   |-- sitemap.xml         サブLPサイトマップ
|
|-- scripts/                [EXISTING] 自動化スクリプト
|   |-- daily_pipeline.sh
|   |-- generate_slides.py
|   |-- notify_slack.py
|   |-- overlay_text.py
|   |-- post_to_tiktok.py
|   |-- pdca_*.sh
|   |-- utils.sh
|
|-- content/                [EXISTING] SNSコンテンツ
|   |-- base-images/
|   |-- generated/
|   |-- stock/
|   |-- templates/
|
|-- docs/                   [EXISTING] ドキュメント
|   |-- api_key_guide.md
|   |-- integration_plan.md (this file)
|
|-- logs/                   [EXISTING] ログ
|
|-- CLAUDE.md               [EXISTING] 戦略指針
|-- PROGRESS.md             [EXISTING] 進捗ログ
|-- PDCA_SETUP.md           [EXISTING] PDCA設定ガイド
|-- .env                    [EXISTING] 環境変数
|-- .gitignore              [UPDATE] project1のルールを追加
```

---

## 4. デプロイ方法

### GitHub Pages（フロントエンド）
1. `main` ブランチの `/` (root) をソースに設定
2. URL: `https://quads-nurse.com/`
3. カスタムドメイン設定可（将来）: `www.robby-the-match.com`

### Cloudflare Workers（API）
1. `api/` ディレクトリで `wrangler deploy` 実行
2. シークレット設定:
   ```
   wrangler secret put ANTHROPIC_API_KEY
   wrangler secret put SLACK_BOT_TOKEN
   wrangler secret put CHAT_SECRET_KEY
   wrangler secret put GOOGLE_SHEETS_ID
   wrangler secret put GOOGLE_SERVICE_ACCOUNT_JSON
   wrangler secret put ALLOWED_ORIGIN
   ```
3. API URL: `https://robby-the-match-api.haruhi-medical.workers.dev`

### デプロイチェックリスト
- [ ] config.jsのAPI.workerEndpointが正しいURLを指しているか確認
- [ ] Cloudflare WorkersのALLOWED_ORIGINにGitHub PagesのURLを設定
- [ ] ANTHROPIC_API_KEYが有効か確認
- [ ] SLACK_BOT_TOKENが有効か確認
- [ ] Google Sheets IDとサービスアカウントJSONが設定済みか確認
- [ ] OGP画像のURLがGitHub Pagesの正しいパスを指しているか確認
- [ ] GA4の測定IDを実際のものに置き換え（G-X4G2BYW13B）

---

## 5. AIチャットウィジェットの統合方法

### 構成
- `chat.js` — チャットロジック（電話番号ゲート、プリスクリプトフロー、AI API呼び出し）
- `chat.css` — チャットUIスタイル
- `config.js` — API URL・病院データ（chat.jsが参照）
- `data/areas.js` — エリア別病院DB（フロントエンドマッチング用）
- `api/worker.js` — サーバーサイドAIチャット処理

### データフロー
```
ユーザー → chat.js（ブラウザ）
  → Step 1-2: プリスクリプトフロー（職種・エリア選択、APIコストゼロ）
  → Step 3-5: Cloudflare Workers → Claude Haiku 4.5 → レスポンス
  → 完了時: Cloudflare Workers → Slack通知（温度感スコア付き）
  → 完了時: Cloudflare Workers → Google Sheets記録
```

### セキュリティ
- HMACトークンによるセッション認証
- 電話番号バリデーション（クライアント + サーバー）
- ハニーポット + タイミングチェック（bot対策）
- レート制限（IP単位 + 電話番号単位 + グローバル）
- メッセージサニタイズ（制御文字除去、長さ制限）

---

## 6. API統合（Cloudflare Workers）

### エンドポイント一覧
| パス | メソッド | 機能 |
|---|---|---|
| /api/register | POST | 登録フォーム送信 → Slack通知 + Google Sheets |
| /api/chat-init | POST | チャットセッション初期化（トークン発行） |
| /api/chat | POST | AIチャット（Claude Haiku 4.5） |
| /api/chat-complete | POST | チャット完了 → Slack通知 + Google Sheets |
| /api/notify | POST | 汎用Slack通知 |
| /api/health | GET | ヘルスチェック |

### 統合ポイント
- `config.js` の `API.workerEndpoint` でAPI URLを一元管理
- CORS設定で GitHub Pages オリジンを許可
- ローカル開発時は `localhost` / `file://` を自動許可

---

## 7. Slack Bot統合

### 2つのSlack連携システム

#### 7a. project1のSlack Bot（slack-bot.js + slack-notify.js）
- **目的**: Claude Code経由でプロジェクト操作 + 進捗通知
- **チャンネル**: #平島claudecode (C09A7U4TV4G)
- **技術**: @slack/bolt Socket Mode
- **用途**: 開発中のClaude Code操作、プロジェクトステータス送信

#### 7b. robby-the-matchのSlack通知（scripts/notify_slack.py）
- **目的**: SNSコンテンツ生成完了の承認依頼
- **チャンネル**: SNSコンテンツチャンネル (C08SKJBLW7A)
- **技術**: Python requests + Slack Bot Token
- **用途**: 台本JSON通知、カスタムメッセージ送信

#### 7c. Cloudflare Workers経由の通知（api/worker.js）
- **目的**: 求職者登録・チャット完了の即座通知
- **チャンネル**: #平島claudecode (C09A7U4TV4G)
- **技術**: Slack Web API chat.postMessage
- **用途**: フォーム送信通知、AIチャット完了通知（温度感スコア付き）

### 統合方針
- 3つのSlack連携は**チャンネルと用途が異なるため共存**させる
- 環境変数（SLACK_BOT_TOKEN）は共通のものを使用可能
- チャンネルIDは用途に応じて使い分ける

---

## 8. 両プロジェクトの長所を活かす方法

### project1の長所
- 高品質なメインLP（アニメーション、構造化データ、GA4）
- 完成度の高いAIチャットウィジェット（5ステップ、温度感スコアリング）
- 堅牢なCloudflare Workers API（レート制限、HMAC認証、リトライ）
- 59施設の病院DB（病院機能報告ベース）
- 求人市場データ（外部公開求人リスト含む）

### robby-the-matchの長所
- SNSコンテンツパイプライン（画像生成→スライド→Slack通知→投稿）
- PDCA自動化システム（cron + 5つのPDCAスクリプト）
- SEO特化LP-A（SNS広告ランディング用）
- 戦略ドキュメント（CLAUDE.md v8.0 — ペルソナ、戦略、実行指針）
- コスト最適化設計（月額固定費ゼロ維持）

### 統合による相乗効果
1. **2段階ファネル**: SNS広告 → LP-A（LINE CTA） + SEO → メインLP（登録フォーム + AIチャット）
2. **データ統一**: 病院DB（areas.js）をSNSコンテンツテンプレートでも参照可能に
3. **通知統合**: 全チャネル（フォーム・チャット・SNSコンテンツ）をSlackで一元管理
4. **PDCA連携**: メインLPのGA4データ → PDCAレビュースクリプトで自動分析
5. **1リポジトリ管理**: GitHub Pagesで全LP + APIデプロイをワンストップ管理

---

## 9. GA4タグ

メインLP（index.html）には以下のGA4タグが設置済み:
- 測定ID: `G-X4G2BYW13B`（プレースホルダー、実測定IDに要置換）
- カスタムパラメータ: profession, urgency_score, area, source_channel
- 自動追跡イベント: chat_started, generate_lead
- コンバージョン値: 50,000 JPY / リード

LP-A にも同じ測定IDのGA4タグを追加予定。

---

## 10. 実行手順

### Phase 1: ファイル統合（本ドキュメントと同時に実行）
1. project1のキーファイルをrobby-the-matchにコピー
2. 既存ファイル（lp/, scripts/, content/等）は絶対に上書きしない
3. .gitignoreを統合

### Phase 2: 設定調整
1. config.jsのcanonical URL確認
2. sitemap.xmlの更新（全ページ反映）
3. OGP画像URLの確認

### Phase 3: デプロイ
1. GitHub Pages設定（mainブランチ / root）
2. Cloudflare Workers デプロイ（wrangler deploy）
3. シークレット設定

### Phase 4: 動作確認
1. メインLP表示確認
2. LP-A表示確認
3. AIチャット動作確認
4. フォーム送信 → Slack通知確認
5. GA4イベント送信確認
