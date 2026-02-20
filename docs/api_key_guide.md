# APIキー取得ガイド

## 1️⃣ Google Gemini API（最優先・無料）

**用途:** 画像生成（gemini-2.0-flash、9:16縦型対応）

### 取得手順:

1. **Google AI Studioにアクセス**
   - https://ai.google.dev/ を開く
   - 右上の「Get API key in Google AI Studio」をクリック

2. **Googleアカウントでログイン**
   - 既存のGoogleアカウントでログイン
   - 初めての場合は利用規約に同意

3. **APIキーを作成**
   - 左メニュー「Get API key」をクリック
   - 「Create API key」をクリック
   - 既存のGoogle Cloud ProjectがあればそれをSELECT、なければ「Create API key in new project」を選択

4. **APIキーをコピー**
   - 生成されたAPIキーをコピー
   - **重要:** 一度しか表示されないので、必ず安全な場所に保存
   - `~/robby-the-match/.env` の `GOOGLE_API_KEY=` の後に貼り付け

5. **無料枠の確認**
   - Google AI Studio > Quota で確認
   - gemini-2.0-flash: 1日あたり一定枚数無料
   - 画像生成は1リクエストあたり約1-2秒

### 料金:
- **無料枠あり**（月間制限あり、詳細はGoogle AI Studioで確認）
- 超過後も従量課金は非常に安価

---

## 2️⃣ Slack Webhook（次に必要・無料）

**用途:** コンテンツ承認通知

### 取得手順:

1. https://api.slack.com/apps にアクセス
2. "Create New App" → "From scratch"
3. App名: "ROBBY Content Approval"（任意）
4. ワークスペース選択
5. 左メニュー > "Incoming Webhooks"
6. "Activate Incoming Webhooks" をオンにする
7. ページ下部 "Add New Webhook to Workspace" をクリック
8. 通知先チャンネル選択（例: #robby-approval または DM）
9. "Allow" をクリック
10. 生成されたWebhook URL（https://hooks.slack.com/services/...）をコピー
11. `~/robby-the-match/.env` の `SLACK_WEBHOOK_URL=` の後に貼り付け

### 料金: 無料

---

## 3️⃣ Postiz API（Phase 3で必要）

**用途:** TikTok投稿自動化

### 取得手順:

1. https://postiz.com/ にアクセス
2. アカウント作成 or ログイン
3. TikTokアカウントを連携:
   - Settings > Integrations > TikTok > Connect
4. API Key取得:
   - Settings > API Keys > "Generate API Key"
5. 生成されたキーをコピー
6. `~/robby-the-match/.env` の `POSTIZ_API_KEY=` の後に貼り付け

### 料金: 無料〜$5/月

---

## 優先順位

**今すぐ取得:**
1. ✅ GOOGLE_API_KEY（画像生成に必須）
2. ✅ SLACK_WEBHOOK_URL（通知に必須）

**後で取得可能:**
- POSTIZ_API_KEY（Phase 4で使用）
