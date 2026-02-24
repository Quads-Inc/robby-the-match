# ROBBY THE MATCH SNS完全自動化プラン

> 策定日: 2026-02-21
> 策定者: Claude Opus 4.6
> 原則: コスト意識最優先。無料でできることに金を使うな。

---

## 現状サマリ

| 項目 | 状態 |
|------|------|
| TikTokアカウント | @robby15051（Google認証、Cookie取得済み、sessionid確認済み） |
| Cookie有効期限 | sessionid: 2027-08頃まで有効 |
| 投稿キュー | 16件（うち2件manual_required、14件pending） |
| 動画生成 | ffmpegスライドショー（6枚x3秒=18秒MP4）テスト成功 |
| tiktok-uploader | **未インストール**（`pip3 show`でNOT FOUND） |
| cron | 17:30 月-土 pdca_sns_post.sh 設定済み |
| Instagram | 未作成 |
| Mac Mini M4 | 24/7稼働想定 |

---

## A. ブラウザ自動操作 -- 3つのアプローチ比較

### A1. tiktok-uploader (wkaisertexas) -- Selenium + Cookie

| 項目 | 評価 |
|------|------|
| コスト | 無料 |
| 成熟度 | 高（v1.1.5、2025-11月時点でissue活発） |
| フォトカルーセル対応 | **非対応**（動画のみ） |
| bot検知 | 中程度（Selenium検知されやすい） |
| セットアップ難易度 | 低 |
| 推奨度 | **動画投稿のみなら即使える** |

### A2. tiktokautouploader (haziq-exe) -- Playwright + Stealth

| 項目 | 評価 |
|------|------|
| コスト | 無料 |
| 成熟度 | 高（v5.6、2026-02月更新、WORKING確認済み） |
| フォトカルーセル対応 | **不明**（ドキュメント上はビデオのみ） |
| bot検知 | 低（Phantomwright + ステルスプラグイン内蔵） |
| CAPTCHA対応 | 自動解決 |
| 音楽追加 | 対応（名前検索 or お気に入りから選択） |
| スケジュール投稿 | 対応（最大10日先） |
| マルチアカウント | 対応 |
| 推奨度 | **最有力。tiktok-uploaderの上位互換** |

### A3. TikTok Content Posting API（公式）

| 項目 | 評価 |
|------|------|
| コスト | 無料 |
| フォトポスト対応 | **対応**（最大35枚、auto_add_music対応） |
| 制約（未審査） | SELF_ONLY（自分のみ閲覧）、5ユーザー/日 |
| 制約（審査済み） | PUBLIC_TO_EVERYONE可能 |
| 審査要件 | 正式なWebサイト必要（LP-A有り → 条件満たす可能性あり） |
| 審査期間 | 3-4日（公式）、実際は1-2週間の可能性 |
| 推奨度 | **中長期で最良。ただし審査に時間がかかる** |

### A4. Claude Computer Use MCP

| 項目 | 評価 |
|------|------|
| コスト | 無料（ローカル実行） |
| 能力 | ブラウザ起動・操作・スクリーンショット・テキスト入力 |
| TikTokプロフィール設定 | **可能**（ナビゲーション→テキスト入力→ボタンクリック） |
| 投稿自動化 | 理論上可能だが不安定（CAPTCHA対応なし） |
| 推奨度 | **プロフィール設定など一回限りの操作に最適** |

### A5. AppleScript + Chrome DevTools Protocol

| 項目 | 評価 |
|------|------|
| コスト | 無料 |
| 制約 | Mac専用、CAPTCHAバイパス不可、保守性低い |
| 推奨度 | **非推奨。Playwrightの方が優れている** |

### 結論

```
即時投稿:      tiktokautouploader (v5.6) を使う
公式API申請:   並行してTikTok Developer登録を進める
プロフィール設定: Claude Computer Use MCP で1回実行
将来（審査後）:  Content Posting APIに移行（フォトカルーセル対応）
```

---

## B. TikTok投稿の最適化

### B1. ネイティブフォトカルーセル vs 動画スライドショー

| 比較項目 | フォトカルーセル（Photo Mode） | 動画スライドショー（現在の方式） |
|----------|------|------|
| エンゲージメント | **2.5x高い**インタラクション率 | 標準的 |
| アルゴリズム評価 | Swipe-Through Rate（STR）、逆スワイプが強シグナル | Watch Time、リプレイ |
| 音楽追加 | 自動（auto_add_music）or 手動 | ffmpegで事前ミックス or なし |
| スワイプ操作 | ユーザー自身のペースで閲覧 → 滞在時間増 | 自動再生 |
| API投稿 | Content Posting APIで対応 | tiktokautouploader等で対応 |
| 画像枚数 | 4-35枚 | 制限なし（動画秒数による） |
| 現時点での推奨 | **将来的に移行すべき** | **即座に使える（現行パイプライン）** |

**結論: フォトカルーセルの方がエンゲージメントが高い。Content Posting API審査通過後にカルーセルに移行する。当面は動画スライドショーで投稿を開始し、1日でも早くコンテンツを出す。**

### B2. 音楽の自動追加

| 方法 | 実現可能性 |
|------|-----------|
| Content Posting API の auto_add_music=true | API審査後に使用可能。トレンド音楽が自動選択される |
| tiktokautouploader のサウンド機能 | 名前検索 or お気に入りから選択可能 |
| ffmpegで事前ミックス | フリー音源をダウンロード→動画に合成。著作権リスクあり |
| 無音で投稿 | TikTokが自動推薦する場合もある |

**推奨: tiktokautouploaderのサウンド機能を使い、看護師向けトレンド音楽（穏やかなBGM系）を自動追加。Content Posting API移行後はauto_add_music=trueを使用。**

---

## C. 完全自動化ループ設計

### C1. 自動化アーキテクチャ（最終形）

```
┌─────────────────────────────────────────────────────────┐
│                    CONTENT LOOP                          │
│                                                          │
│  1. コンテンツ生成（cron 15:00 pdca_content.sh）          │
│     Claude API → 台本JSON生成                             │
│     ↓                                                     │
│  2. スライド生成（generate_slides.py）                     │
│     Pillow → 6枚PNG生成                                   │
│     ↓                                                     │
│  3. 動画生成（tiktok_post.py → ffmpeg）                   │
│     6枚 x 3秒 = 18秒MP4                                  │
│     ↓                                                     │
│  4. TikTok投稿（cron 17:30 pdca_sns_post.sh）            │
│     tiktokautouploader or Content Posting API             │
│     ↓                                                     │
│  5. Instagram投稿（cron 18:00 pdca_instagram_post.sh）   │
│     instagrapi → 同内容をクロスポスト                      │
│     ↓                                                     │
│  6. パフォーマンス収集（cron 23:00 pdca_review.sh）       │
│     TikTok Analytics → data/kpi_log.csv                   │
│     ↓                                                     │
│  7. 次コンテンツへ反映（週次レビュー pdca_weekly.sh）      │
│     高パフォーマンスパターン → コンテンツストックに★        │
│     低パフォーマンスパターン → 失敗ログに記録              │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### C2. Cookie有効期限の自動管理

```python
# 方針: 期限切れ「前に」検知してSlack通知
# sessionidのexpiry: 現在 2027-08頃（約18ヶ月先）
# → 3日前にSlack警告、手動再ログイン

# tiktok_auth.py --check を cron 07:00（healthcheck）で毎日実行
# 残り3日未満 → Slack警告
# 残り0日 → Slack緊急通知 + 投稿を一時停止
```

**実装:**
- `pdca_healthcheck.sh` に Cookie有効性チェックを追加
- 期限切れ3日前にSlack警告: 「TikTok Cookieが3日後に期限切れです。`python3 scripts/tiktok_auth.py` を実行してください」
- 期限切れ後は投稿をスキップし、manual_requiredステータスに設定

### C3. エラー時の自動復旧

```
エラーパターン          | 自動復旧                          | 手動対応
------------------------|-----------------------------------|------------------
Cookie期限切れ          | 投稿スキップ + Slack通知           | 再ログイン
CAPTCHA失敗            | 3回リトライ → Slack通知            | ブラウザで手動解決
ネットワークエラー      | 5分後にリトライ(最大3回)            | -
ffmpeg失敗             | エラーログ + 次のコンテンツに進む   | -
アカウントBAN/制限      | 即座にSlack緊急通知               | Instagram代替投稿
TikTok UIの変更         | tiktokautouploader更新待ち         | pip upgrade
```

### C4. 週次パフォーマンスレポート

```
毎週日曜 06:00（pdca_weekly.sh）で自動生成:

=== ROBBY THE MATCH 週次SNSレポート ===
期間: 2026-02-24 〜 2026-03-02

■ TikTok
  投稿数: 6本
  総再生数: XX,XXX
  平均再生数: X,XXX
  最高再生: day3（夜勤明けAI年齢判定）XX,XXX再生
  いいね率: X.X%
  保存率: X.X%
  コメント数: XX

■ Instagram（Week2以降）
  投稿数: 3本
  リーチ: X,XXX
  保存率: X.X%

■ LINE登録
  今週: X名
  累計: X名

■ 来週の方針
  - 高パフォーマンスパターン: [自動分析結果]
  - 来週のコンテンツMIX: あるある3本 + 転職2本 + 給与1本
```

---

## D. Instagram連携

### D1. 方式比較

| 方式 | コスト | 安定性 | フォトカルーセル | Reels |
|------|--------|--------|----------------|-------|
| Instagram Graph API（公式） | 無料 | 高 | 対応 | 対応 |
| instagrapi（非公式Private API） | 無料 | 中 | 対応 | 対応 |
| Playwright ブラウザ自動化 | 無料 | 低 | 可能 | 可能 |

**Instagram Graph API の要件:**
- Instagramビジネスアカウント or クリエイターアカウント
- Facebookページとの連携
- Meta Developer App登録
- 24時間で最大25投稿

**instagrapi の利点:**
- ビジネスアカウント不要
- Facebook連携不要
- `client.photo_upload()` / `client.album_upload()` で即投稿
- 2026年2月時点でも活発にメンテナンス

**推奨: instagrapi を使う。Graph APIはFacebookページ連携が必要で手間がかかる。instagrapiなら個人アカウントでもすぐ使える。**

### D2. クロスポスト設計

```
TikTok投稿 (17:30)
    ↓ 30分後
Instagram Reels投稿 (18:00) — 同じ動画
    ↓ 同時
Instagram カルーセル投稿 — 同じ6枚スライド画像

※ 同じコンテンツでもキャプションはプラットフォーム別に最適化:
  - TikTok: 短め、#ハッシュタグ多め（5個）
  - Instagram: やや長め、#ハッシュタグ多め（15-20個）、@メンション
```

---

## 実行計画

### Phase 1: 今日中に実行（2026-02-21）

**所要時間: 2-3時間 | コスト: 0円**

| # | タスク | 方法 | 時間 |
|---|--------|------|------|
| 1 | tiktokautouploader インストール | `pip3 install tiktokautouploader` + Node.js確認 | 10分 |
| 2 | tiktokautouploader テスト投稿 | 既存Cookie使用 or 初回ログイン → A01動画投稿 | 30分 |
| 3 | tiktok_post.py を tiktokautouploader 対応に改修 | upload_video関数差し替え | 30分 |
| 4 | Claude Computer Use MCP インストール | `npm install -g claude-computer-use-mcp` | 10分 |
| 5 | TikTokプロフィール設定（MCP経由） | アイコン、BIO、リンク設定 | 30分 |
| 6 | pdca_sns_post.sh のテスト実行 | 手動で1回実行して成功確認 | 15分 |
| 7 | キューの manual_required を pending にリセット | A01/A02のステータスリセット | 5分 |

**Phase 1 完了条件: TikTokに最初の1投稿が公開されている**

### Phase 2: 今週中（2026-02-22 〜 02-28）

**所要時間: 5-8時間 | コスト: 0円**

| # | タスク | 方法 | 時間 |
|---|--------|------|------|
| 1 | Instagramアカウント作成 | 手動（Google認証） | 15分 |
| 2 | instagrapi インストール・セットアップ | `pip3 install instagrapi` | 10分 |
| 3 | instagram_post.py 新規作成 | instagrapi でカルーセル+Reels投稿 | 2時間 |
| 4 | pdca_instagram_post.sh 作成 | cron 18:00 設定 | 30分 |
| 5 | Cookie有効性チェックをhealthcheckに統合 | tiktok_auth.py --check をcron組み込み | 30分 |
| 6 | エラーリトライ機能追加 | tiktok_post.pyに3回リトライ+指数バックオフ | 1時間 |
| 7 | TikTok Developer Portal 登録申請 | developers.tiktok.com でApp作成 | 1時間 |
| 8 | パフォーマンス収集スクリプト作成 | TikTokプロフィールからデータ取得 | 2時間 |
| 9 | 毎日の投稿確認: cron動作の検証 | 5日間モニタリング | - |

**Phase 2 完了条件: TikTok 5投稿 + Instagram 3投稿が公開されている**

### Phase 3: 来週以降（2026-03-01 〜）

**所要時間: 継続的 | コスト: 0円**

| # | タスク | 方法 | 時間 |
|---|--------|------|------|
| 1 | Content Posting API 審査通過後、フォトカルーセル投稿に移行 | API実装 | 3時間 |
| 2 | コンテンツ自動生成ループ完成 | Claude API → 台本 → スライド → キュー追加 | 3時間 |
| 3 | A/Bテスト自動化 | 同じネタで変数を変えて投稿、結果自動記録 | 2時間 |
| 4 | 週次レポート自動生成 | pdca_weekly.shにSNSパフォーマンス統合 | 2時間 |
| 5 | 音楽自動追加 | tiktokautouploaderのサウンド機能 or API auto_add_music | 1時間 |
| 6 | トレンド音楽の自動選定 | TikTokトレンドAPI or Web scraping | 2時間 |
| 7 | コンテンツストック自動補充 | 週次でClaude APIに新規ネタ生成依頼 | 1時間 |

---

## 各項目の実装方法（具体的なコード方針）

### 1. tiktokautouploader 導入

```bash
# インストール
pip3 install tiktokautouploader
# Node.js確認
node --version  # v18以上必要
# Chromiumインストール
phantomwright_driver install chromium
```

```python
# tiktok_post.py の upload_to_tiktok() を差し替え
from tiktokautouploader import upload_tiktok

def upload_to_tiktok(video_path, caption, hashtags):
    """tiktokautouploaderで投稿"""
    tags = [tag.lstrip('#') for tag in hashtags]

    upload_tiktok(
        video=video_path,
        description=caption,
        hashtags=tags,
        accountname="robby15051",
        sound_name=None,       # 将来: トレンド音楽名
        schedule=None,          # 将来: スケジュール投稿
    )
    return True
```

### 2. Instagram投稿スクリプト

```python
# scripts/instagram_post.py
from instagrapi import Client

cl = Client()
cl.login("robby.the.robot.2026@gmail.com", "PASSWORD")  # .envから読む

# カルーセル投稿（6枚スライド）
def post_carousel(slide_paths, caption):
    cl.album_upload(
        paths=slide_paths,
        caption=caption
    )

# Reels投稿（動画）
def post_reels(video_path, caption):
    cl.clip_upload(
        path=video_path,
        caption=caption
    )
```

### 3. Cookie有効性の自動チェック

```python
# pdca_healthcheck.sh に追加
python3 scripts/tiktok_auth.py --check
# 戻り値で判断:
#   残り3日未満 → Slack警告
#   残り0日    → Slack緊急通知
```

### 4. TikTokプロフィール設定（Claude Computer Use MCP）

```
# Claude Codeで以下の指示を出す:
# 「TikTokにログインして、@robby15051のプロフィールを設定して:
#   - アイコン: content/base-images/robby_icon.png
#   - BIO: 看護師の転職を、手数料10%で。AI×人のハイブリッドサポート。神奈川県西部。
#   - リンク: https://quads-nurse.com/lp/job-seeker/
#   - 名前: ROBBY THE MATCH」
```

### 5. Content Posting API（フォトカルーセル）

```python
# 審査通過後に実装
import httpx

def post_photo_carousel(image_urls, caption, access_token):
    """TikTok Content Posting API でフォトカルーセル投稿"""
    url = "https://open.tiktokapis.com/v2/post/publish/content/init/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "post_info": {
            "title": caption[:90],
            "description": caption,
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "auto_add_music": True  # トレンド音楽自動追加
        },
        "source_info": {
            "source": "PULL_FROM_URL",
            "photo_images": image_urls,  # 最大35枚のURL
            "photo_cover_index": 0
        },
        "post_mode": "DIRECT_POST"
    }
    resp = httpx.post(url, headers=headers, json=data, timeout=30)
    return resp.json()
```

### 6. エラーリトライ

```python
import time

def upload_with_retry(func, *args, max_retries=3, **kwargs):
    """指数バックオフ付きリトライ"""
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            wait = (2 ** attempt) * 30  # 30秒, 60秒, 120秒
            print(f"[WARN] 投稿失敗 (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print(f"[INFO] {wait}秒後にリトライ")
                time.sleep(wait)
            else:
                slack_notify(f"TikTok投稿が{max_retries}回失敗: {e}")
                raise
```

---

## コスト見積もり

### 初期コスト（Phase 1-2）

| 項目 | コスト |
|------|--------|
| tiktokautouploader | 無料 |
| instagrapi | 無料 |
| Claude Computer Use MCP | 無料 |
| Node.js | 無料 |
| Playwright/Chromium | 無料 |
| TikTok Developer登録 | 無料 |
| Instagram Graph API | 無料 |
| **合計** | **0円** |

### 月間運用コスト

| 項目 | コスト | 備考 |
|------|--------|------|
| Claude API（台本生成） | ~3,000-5,000円 | 週7本 x 4週 |
| 画像生成（Cloudflare） | ~500円 | ベース画像使い回し |
| Mac Mini M4 電気代 | ~500円 | 24/7稼働 |
| **合計** | **~4,000-6,000円/月** | |

### 使わないもの（コスト節約）

| 項目 | コスト | 不要な理由 |
|------|--------|-----------|
| Buffer/Later | $6-15/月 | tiktokautouploader + instagrapiで代替 |
| Postiz有料プラン | $29/月 | 自前スクリプトで代替 |
| GeeLark | $10/月 | 単一アカウントなら不要 |
| Lステップ | 2,980円/月 | LINE登録50名超えるまで不要 |
| 独自ドメイン | ~1,500円/年 | SEO効果が出てから検討 |
| **節約額** | **~5,000-10,000円/月** | |

---

## bot検知回避策

### TikTok

1. **tiktokautouploader の内蔵ステルス機能を使う**
   - Phantomwright（Playwrightのフォーク）でフィンガープリントスプーフィング
   - navigator.webdriver プロパティ削除
   - HeadlessChrome UA書き換え

2. **投稿頻度の制御**
   - 1日1投稿（17:30固定）
   - 投稿間隔を最低20時間以上空ける
   - 週末は投稿しない or 時間をずらす

3. **人間らしい操作パターン**
   - ランダムなディレイ（5-15秒のランダムウェイト）
   - マウス移動のシミュレーション（tiktokautouploaderが内蔵）

4. **Cookie管理**
   - 初回ログインは手動（CAPTCHA対応）
   - 以降はCookieで認証（ブラウザ起動不要ではないが検知リスク低）

### Instagram

1. **instagrapi はPrivate APIを使うためブラウザ不要**
   - HTTP直接リクエスト → ブラウザフィンガープリント検知なし
   - ただしレート制限に注意（1日25投稿まで）

2. **対策**
   - 投稿前に5-10分のランダムディレイ
   - セッションを使い回す（毎回ログインしない）
   - 2FA有効化でアカウントセキュリティ強化

---

## Agent Team 統合設計

### 既存8エージェント + 新規2エージェント = 10エージェント体制

| # | エージェント | cron | 役割 | 状態 |
|---|-----------|------|------|------|
| 1 | SEO Optimizer | 04:00 | SEO改善 | 稼働中 |
| 2 | Health Monitor | 07:00 | 障害監視 + Cookie有効性チェック | **拡張** |
| 3 | Competitor Analyst | 10:00 | 競合分析 | 稼働中 |
| 4 | Content Creator | 15:00 | コンテンツ生成 | 稼働中 |
| 5 | **TikTok Poster** | **17:30** | TikTok自動投稿 | **改修** |
| 6 | **Instagram Poster** | **18:00** | Instagram自動投稿 | **新規** |
| 7 | Daily Reviewer | 23:00 | 日次レビュー + パフォーマンス収集 | **拡張** |
| 8 | Weekly Strategist | 日曜06:00 | 週次総括 + SNSレポート | **拡張** |
| 9 | Slack Commander | */5分 | Slack監視 | 稼働中 |
| 10 | **Profile Manager** | 手動 | プロフィール設定（MCP経由） | **新規（1回限り）** |

---

## リスク評価と対策

| リスク | 確率 | 影響 | 対策 |
|--------|------|------|------|
| TikTokアカウントBAN | 低（1日1投稿なら） | 高 | Instagram並行運用で代替。全コンテンツはローカル保存済み |
| tiktokautouploaderが動かなくなる | 中 | 中 | Content Posting APIを並行で準備。手動投稿フォールバック |
| Cookie期限切れ | 低（18ヶ月先） | 低 | 自動検知 + Slack通知 |
| instagrapiのブロック | 中 | 中 | Graph API代替。ブラウザ自動化フォールバック |
| TikTok API審査不通過 | 中 | 低 | tiktokautouploaderで継続 |
| CAPTCHAで投稿失敗 | 中 | 低 | 3回リトライ + Slack通知 → 手動対応 |

---

## まとめ: 優先順位

```
今日:
  1. tiktokautouploader導入 → 初投稿
  2. プロフィール設定
  3. cron投稿テスト成功確認

今週:
  4. Instagram開設 + instagrapi導入
  5. エラーリトライ機能
  6. Cookie自動チェック
  7. TikTok Developer登録

来週以降:
  8. Content Posting API移行（審査通過後）
  9. フォトカルーセル投稿
  10. パフォーマンス分析自動化
  11. コンテンツ自動生成ループ完成
```

**最重要: 今日TikTokに最初の1投稿を出すこと。完璧なシステムより、今日看護師が見るSNS投稿の方が100倍価値がある。**
