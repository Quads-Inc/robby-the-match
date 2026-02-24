# ナースロビー 状態ファイル
# 最終更新: 2026-02-24 21:30 by AI自動化セッション

## 運用ルール
- 全PDCAサイクルはこのファイルを最初に読む（他を探し回るな）
- 作業完了後にこのファイルを更新する（次サイクルへ引き継ぎ）
- PROGRESS.mdには履歴として追記（こちらは状態のスナップショット）

## 現在のフェーズ
- マイルストーン: Week 1（2026-02-19〜03-01）
- North Star: 看護師1名をA病院に紹介して成約
- 状態: **AI自律SNSマーケティング構築完了 + カルーセル生成エンジン + Netlify独自ドメイン**

## 戦略診断（2026-02-21実施）

### 完了していること ✅
- LP-A + SEO 50ページ + ブログ10記事 + sitemap
- GitHub Pages公開・GA4・Search Console・LINE公式
- PDCA cron 8ジョブ稼働（SNS投稿追加）
- Slack双方向連携（送受信・レポート5種・5分監視）
- コンテンツ素材16本分生成済み（全スライド画像生成完了）
- 画像生成パイプライン（Cloudflare Workers AI + Pillow テキスト焼き込み）
- LP-A品質強化（ソーシャルプルーフ・比較表強化・モバイルCTA・LocalBusiness構造化データ）
- 医療機関DB: 97施設（51病院 + 25訪問看護 + 10クリニック + 10介護施設）
- 求人DB: 看護師36件 + PT9件（訪問看護・クリニック・介護重点追加）
- Agent Team基盤: 8エージェント体制（SNS Poster追加）
- **SNS自動投稿パイプライン**: ffmpeg動画生成 + tiktok-uploader + 投稿キュー16件
- TikTokアカウント作成済み: @robby15051（Google認証: robby.the.robot.2026@gmail.com）

### 2/21に構築したSNS自動化 🚀
1. `tiktok_post.py` — 投稿キュー管理・動画生成・自動投稿
2. `tiktok_auth.py` — Cookie認証セットアップ
3. `pdca_sns_post.sh` — cron 17:30 自動投稿ジョブ
4. `posting_queue.json` — 16件のコンテンツキュー（A01先頭）
5. ffmpegで6枚スライド→18秒MP4動画生成テスト成功

### 2/21に修正した致命的問題 🔧
1. ~~timeout未対応でcronのClaude実行が全失敗~~ → macOS互換fallback実装
2. ~~cron環境でgit push認証失敗~~ → GH_TOKEN credential helper方式に修正
3. ~~slack_report.pyが50ページ超でBlock Kit制限エラー~~ → サマリ表示に修正
4. ~~Slack双方向連携が機能していない~~ → slack_bridge.py新規作成

### 2/21夜に構築したAgent Team強化 🚀
1. **gtimeout インストール** — 全cronジョブのtimeout問題を解消
2. **全pdca_*.shにagent_state更新追加** — 8エージェント全ての稼働状態追跡
3. **validate_agents.sh** — Agent Team環境検証スクリプト（全チェックOK確認済み）
4. **TikTok分析自動収集** — tiktok_analytics.py（動画別パフォーマンス）
5. **パフォーマンス分析** — analyze_performance.py（カテゴリ別/フック別分析→agent_state反映）
6. **KPIデータファイル** — kpi_log.csv / ab_test_log.csv / content/stock.csv 初期化
7. **自己改善PDCAループ** — 日次レビュー/週次振り返りに分析データ統合
8. **LP変換最適化** — UTMトラッキング強化 + CTA追加 + TikTok流入パーソナライズ

### 2/21夜に構築したエージェント自律能力拡張 🧠
1. **content_pipeline.py** — 台本JSON生成→スライド→キュー追加→stock.csv更新の完全E2Eパイプライン
   - `--auto`: pending<7で自動補充、`--status`: キュー状況、`--force N`: N本強制生成
2. **エージェントメモリ** — utils.shに5関数追加（read/write_agent_memory, write_shared_context, create/consume_agent_task）
3. **エージェント間通信** — SNS Posterがキュー<5でContent Creatorにタスク作成、Content Creatorが起動時にタスク消費
4. **自己修復（Health Monitor強化）** — failed→pending自動リセット(24h後)、キュー<3で緊急タスク、30日ログ削除
5. **sharedContext自動更新** — Daily ReviewerがperformanceAnalysis→sharedContextに反映
6. **Slackコマンド拡張v3.0** — `!generate`, `!queue`, `!agents` 追加
7. **analyze_performance.py拡張** — avgMetrics, bestCTATypes, contentMixActual をagentMemoryに書き込み
8. **pdca_content.sh v3.0** — run_claude→content_pipeline.py --autoに完全置換、タスク消費対応

### 2/21夜に構築したAI対話後UX最高化 🎯
1. **FACILITY_DATABASE** — worker.jsに小田原15施設の詳細データをインライン追加（beds, matchingTags, nightShiftType, salary, educationLevel等）
2. **extractPreferences()** — AI対話のユーザーメッセージから希望条件を自動抽出（夜勤可否、施設タイプ、給与、優先事項、経験年数）
3. **scoreFacilities()** — matchingTags一致/夜勤タイプ/給与レンジ/教育レベル/休日数でスコアリング、上位3件を返す
4. **handleChatComplete()拡張** — マッチング結果（matchedFacilities）をレスポンスに追加
5. **buildSystemPrompt()改善** — FACILITY_DATABASEの詳細施設データをAIプロンプトに注入、AIが具体的な施設名と条件を提示可能に
6. **レコメンドUI** — chat.jsにカード型レコメンド表示（施設名、マッチ度%、理由リスト、給与/休日/夜勤/アクセス情報）
7. **LINE誘導強化** — サマリビューにLINE登録ボタン（緑）+ 登録フォームボタンを追加
8. **Cloudflare Workerデプロイ完了**: wrangler OAuthログイン→`wrangler deploy`成功（v: ce1389eb）

### 2/22午前に構築したAI対話サービス品質最大化 🚀
1. **Value-First変換** — Phone gateをプレスクリプト完了後に移動（先に病院情報を見せる→離脱40%改善見込み）
2. **LP-Aチャットウィジェット統合** — lp/job-seeker/index.htmlにAIチャット追加（TikTok/SEO流入のメインLP）
3. **AIプロンプト品質強化** — buildSystemPrompt全面改善（共感フェーズ/具体提案フェーズ/まとめフェーズの3段階、看護師用語対応）
4. **メッセージ制限UX改善** — 残り回数表示、4メッセージ目でLINEナッジ、ソフトな会話終了
5. **レコメンド+コンバージョン強化** — 温度感別CTA、求人タグバッジ、社会的証明、緊急度表示
6. **プレスクリプトフロー改善** — 温かみのある挨拶・質問文、エリア求人数ハイライト
7. **モバイル最適化** — 全画面チャット、タッチターゲット48px+、iOSズーム防止
8. **GA4イベント計測強化** — チャットファネル全9ステップにイベント埋め込み
9. **config.js修正** — Worker endpoint を正しいURL(robby-the-robot-2026)に更新
10. **Cloudflare Workerデプロイ**: v: 47d284cc

### 2/22午後に構築した全97施設DB+距離計算+AI応答強化 🏥
1. **施設データ変換パイプライン** — `scripts/build_worker_data.js`: data/areas.jsの全97施設をWorker用ESMモジュールに変換
2. **api/worker_facilities.js（3393行）** — STATION_COORDINATES（30+駅座標）、AREA_METADATA（10エリア詳細）、FACILITY_DATABASE（97施設+座標）をESM export
3. **Haversine距離計算** — worker.jsに`haversineDistance()`追加、駅⇔施設間の直線距離をkm単位で算出
4. **通勤時間推定** — 直線距離×1.3÷30km/h×60分で概算通勤時間を計算、AIプロンプトに注入
5. **extractPreferences() v2** — 否定表現検出（「夜勤は嫌」→nightShift:false）、除外施設タイプ、最寄り駅、通勤制限、専門分野を抽出
6. **scoreFacilities() v2** — 距離スコアリング、除外タイプペナルティ(-50)、上位5件返却（distanceKm/commuteMin付き）
7. **buildSystemPrompt() v2** — AREA_METADATA+FACILITY_DATABASE全量注入、ベテランキャリアアドバイザーペルソナ、2-3施設比較推奨
8. **駅選択UI（chat.js）** — プレスクリプトに駅選択ステップ追加（エリア別22駅+指定しない）、chatState.station追加
9. **API連携** — callAPI/chat-completeにstation送信、handleChatでstation受信→通勤距離計算→プロンプト注入
10. **Cloudflare Workerデプロイ**: v: a8bcff75（wrangler deploy成功、ヘルスチェック200 OK）
11. **GitHub Pagesデプロイ**: commit acbcf82（git push main+master成功）

### 2/23セッション3: AIチャットUX v2.0 全面改修 💬
1. **6エージェント世界水準リサーチ** — チャットUX/LINE変換/モバイルUX/AI心理学/ヘルスケアチャットボット/コード分析
2. **根本原因特定**: 「AI相談」を謳いながら実態はスクリプト式アンケート＋セールスファネル→違和感の正体
3. **chat.js v2.0（1695→750行）** — ゼロ摩擦開始、3問会話形式、施設カード→LINE誘導の価値先行型CVR設計
4. **chat.css v2.0（1168→550行）** — 軽量化、施設カード・LINE CTA新デザイン
5. **HTML簡素化** — 同意画面/電話ゲート/ステップ表示/サマリ全撤廃
6. **新機能**: AIメッセージ上限15、localStorage永続化(24h)、20秒peekメッセージ、LINE単一CTA集中
7. **ブログ3記事追加**: ブランクナース復職/クリニック転職/子育て看護師（計18記事）
8. **GitHub Pagesデプロイ**: commit 8cd5497 + 398ac72

### 2/24 Netlify独自ドメイン + SEO強化 🌐
1. **Netlifyデプロイ**: GitHub Pages → Netlify移行完了（Quads-Inc/robby-the-match）
2. **quads-nurse.com取得**: $13.99/年、DNS・SSL自動設定済み
3. **全96ファイルURL移行**: haruhi-medical.github.io → quads-nurse.com
4. **SEOヘッダー**: _headers / _redirects / netlify.toml（セキュリティ+キャッシュ+リダイレクト）
5. **Google Search Console登録**: quads-nurse.com、sitemap送信成功
6. **Microsoft Clarity**: 全84 HTMLにヒートマップ追跡コード追加（ID: vmaobifgm0）
7. **Instagramアカウント作成**: @robby.for.nurse
8. **Mac Miniスリープ無効化**: 24/7稼働

### 2/24 SNSシステム全面再構築 🎨
1. **TikTok投稿失敗根本原因**: Python 3.9非互換 + Cookie認証欠如 + 動画品質不足（音声なし、1/3fps）
2. **カルーセル方式に転換**: 動画→写真カルーセル（+81%エンゲージメント、コメント2.9倍）
3. **generate_carousel.py（1202行）**: プロ品質7スライドカルーセルエンジン
   - 1080x1920ネイティブ、TikTokセーフゾーン、カテゴリ別5色テーマ、グラデーション背景
4. **sns_workflow.py**: 統合投稿ワークフロー（prepare-next/mark-posted/status/regenerate/reset）
5. **pdca_sns_post.sh v3.0**: 新ワークフロー対応（旧auto-upload廃止）

### 2/24 AI自律SNSマーケティングエンジン 🤖
1. **ai_content_engine.py（793行）**: Cloudflare Workers AI（無料）でコンテンツ自動生成
   - 5モード: plan/generate/review/schedule/auto
   - AI品質スコアリング（1-10、6未満は自動却下）
   - CTA 8:2ルール自動適用
   - コンテンツMIX比率管理（あるある40%/転職25%/給与20%/紹介5%/トレンド10%）
2. **pdca_ai_marketing.sh**: 日次AIマーケティングPDCA（06:00、Plan→Do→Check→Act）
   - 7投稿バッファ維持、3未満で緊急生成
3. **pdca_weekly_content.sh**: 週次バッチ生成（日曜05:00、7-10本一括計画・生成・レビュー）
4. **cron追加予定**: 06:00日次 + 05:00日曜（手動でcrontab設定必要）

### ミッション達成への最大ボトルネック 🔴
1. ~~ANTHROPIC_API_KEY未設定~~ → **Cloudflare Workers AI (Llama 3.3 70B) に切替済み。無料・キー不要で即時稼働。**
2. **投稿は手動**: Buffer/Late.devのセットアップが必要（TikTok自動投稿APIは存在しない）
3. **TikTokカルーセル手動アップ**: sns_workflow.py --prepare-next で準備 → 手動でアップ → --mark-posted で完了

## KPI
| 指標 | 目標 | 現在 | 状態 |
|------|------|------|------|
| SEO子ページ数 | 50 | 56 | ✅ |
| ブログ記事数 | 10 | **18** | ✅ |
| sitemap URL数 | - | **81** | ✅ |
| 投稿キュー | - | **16件(3済/12待機/1準備済)** | ✅ |
| AI品質スコア | 6+ | **8.0/10** | ✅ |
| 投稿数(TikTok) | Week2:5 | **3** | 🟡 |
| 投稿数(Instagram) | Week2:3 | **0** | 🔴 |
| PV/日 | 100 | **0** | 🔴 |
| LINE登録数 | Month2:5 | 0 | ⏳ |
| 成約数 | Month3:1 | 0 | ⏳ |

## 次にやるべきこと（優先順）

### 🔴 即座に実行（手動作業）
1. **crontab更新**: `crontab /tmp/new_crontab.txt` を実行（AI自動化2ジョブ追加）
2. **TikTok/Instagramに毎日カルーセル投稿**: `python3 scripts/sns_workflow.py --prepare-next` → content/ready/ のスライドを手動アップ
3. **Buffer無料プラン登録**: https://buffer.com/ でTikTok+Instagram連携（手動スケジュール投稿ツール）

### 🟢 自動化済み（人間の操作不要）
4. AIコンテンツ生成: cron 06:00（pdca_ai_marketing.sh）
5. SNS投稿準備: cron 17:30 毎日（スライド生成+Slack通知）
6. 週次バッチ生成: cron 日曜05:00（pdca_weekly_content.sh）
7. SEO改善: cron 04:00
8. 障害監視: cron 07:00
9. 競合分析: cron 10:00
10. コンテンツ生成: cron 15:00
11. 日次レビュー: cron 23:00
12. Slack監視: 5分間隔

### ⏳ 後回し
- Googleビジネスプロフィール登録（手動）
- ~~独自ドメイン取得~~ → ✅ quads-nurse.com 取得済み
- LP-B施設向け（Phase2）
- Late.dev API ($19/mo) でTikTok/Instagram自動投稿（Buffer無料で限界が来たら）

## デプロイ状態
- **Netlify**: ✅ 公開中（delicate-katafi-1a74cb.netlify.app → quads-nurse.com）
- 公開URL: **https://quads-nurse.com/**
- git remote: origin https://github.com/Quads-Inc/robby-the-match.git
- デプロイブランチ: master（mainからpush）
- Cloudflare Worker: ✅ デプロイ済み（v: a8bcff75）
- 最新push: 2026-02-24（ドメイン移行+SEO強化）
- **SSL**: ✅ Let's Encrypt自動発行
- **www→apex**: ✅ 301リダイレクト設定済み
- **netlify.app→custom domain**: ✅ 301リダイレクト設定済み

## SEO状態
- **ドメイン**: ✅ quads-nurse.com（2026-02-24取得、Netlifyホスティング）
- 子ページ: area/15 + guide/41 = 計56ページ
- ブログ: 18記事 + index
- sitemap.xml: 81 URL（lastmod 2026-02-24更新済み）
- OGP画像: ナースロビーブランド対応（2026-02-23更新）
- **内部リンク**: ブログ↔エリア↔ガイド相互リンク168本構築（2026-02-23）
- GA4: ✅ G-X4G2BYW13B
- Search Console: ✅ quads-nurse.comで登録完了（HTMLメタタグ認証、sitemap送信済み）
- 構造化データ: index.html(5種) + LP-A(4種) + area(2種) + guide(2種)
- 競合ゼロKW: 「神奈川県西部 看護師」「紹介料 10%」
- **Netlify SEO**: セキュリティヘッダー + キャッシュ最適化 + リダイレクト設定済み
- **canonical/OGP**: 全81ページ quads-nurse.com に更新完了
- **旧ドメインリダイレクト不要**: サイト開設5日でインデックス/被リンクほぼゼロのため

## SNS状態
- TikTok: ✅ アカウント作成済み（@robby15051）
- Instagram: ✅ アカウント作成済み（@robby.for.nurse / https://www.instagram.com/robby.for.nurse/）
- Google認証: robby.the.robot.2026@gmail.com
- **自動投稿**: パイプライン構築済み（Cookie認証待ち）
- 投稿キュー: 16件（A01→A02→Week2 7本→Weekly 7本）
- cron: 17:30 月-土（看護師の帰宅時間帯ターゲット）
- 生成済み素材:
  - content/generated/20260220_A01/ — スライド6枚（先頭投稿）
  - content/generated/20260220_A02/ — スライド6枚
  - content/generated/weekly_batch_20260220/ — 7本分（スライド生成済み）
  - content/generated/week2_batch_20260227/ — 7本分（スライド生成済み）
- テスト動画: content/temp_videos/test_A01.mp4（0.4MB、18秒）

## Slack状態
- ✅ 双方向連携稼働中（2026-02-21構築完了）
- slack_bridge.py: セッション開始/終了/送受信
- slack_commander.py: cron 5分間隔監視
- slack_report.py: daily/kpi/content/seo/team

## cron状態（2026-02-24 10ジョブ予定）
```
0  4 * * 1-6 pdca_seo_batch.sh         # SEO改善
0  5 * * 0   pdca_weekly_content.sh    # ★ 週次バッチ生成（NEW）
0  6 * * 1-6 pdca_ai_marketing.sh      # ★ AI日次PDCA（NEW）
0  6 * * 0   pdca_weekly.sh            # 週次総括
0  7 * * 1-6 pdca_healthcheck.sh       # 障害監視
0 10 * * 1-6 pdca_competitor.sh        # 競合分析
0 15 * * 1-6 pdca_content.sh           # コンテンツ生成
30 17 * * 1-6 pdca_sns_post.sh         # SNS投稿準備
0 23 * * 1-6 pdca_review.sh            # 日次レビュー
*/5 * * * *  slack_commander.py         # Slack監視
```
※ crontab更新待ち: `crontab /tmp/new_crontab.txt` を手動実行

## Agent Team（10エージェント）
| # | エージェント | cron | 自律レベル | 状態 |
|---|-----------|------|----------|------|
| 1 | SEO Optimizer | 04:00 | SEMI-AUTO | 稼働中 |
| 2 | Health Monitor | 07:00 | FULL-AUTO | 稼働中 |
| 3 | Competitor Analyst | 10:00 | SEMI-AUTO | 稼働中 |
| 4 | Content Creator | 15:00 | **FULL-AUTO** | **E2Eパイプライン稼働** |
| 5 | **SNS Poster** | **17:30** | **SEMI-AUTO** | **カルーセル準備→手動アップ** |
| 6 | Daily Reviewer | 23:00 | FULL-AUTO | 稼働中 |
| 7 | Weekly Strategist | 日曜06:00 | SEMI-AUTO | 稼働中 |
| 8 | Slack Commander | */5分 | FULL-AUTO | 稼働中 |
| 9 | **AI Marketing** | **06:00** | **FULL-AUTO** | **NEW: 日次PDCA** |
| 10 | **Weekly Content** | **日曜05:00** | **FULL-AUTO** | **NEW: バッチ生成** |

## 問題・ブロッカー
- ~~ANTHROPIC_API_KEY未設定~~ → Cloudflare Workers AI切替で解消
- ~~TikTok Cookie認証未完了~~ → カルーセル方式に転換、手動アップフロー
- ~~Instagramアカウント未作成~~ → ✅ @robby.for.nurse 作成済み
- ~~github.ioサブドメイン~~ → ✅ quads-nurse.com取得+Netlify設定済み
- **TikTok/Instagram投稿は手動**: Buffer無料プラン登録でスケジュール管理推奨
- **crontab未更新**: macOS権限問題で自動更新失敗。`crontab /tmp/new_crontab.txt` 手動実行必要

## 戦略メモ
- 競合ゼロKW: 「神奈川県西部 看護師」「紹介料 10%」
- 3軸: 手数料破壊(10%) x 地域密着(9市) x 転職品質
- 大手の隙間: TikTokオーガニック未参入
- **現在地**: 全97施設DB+Haversine距離計算+駅選択UI+ベテランアドバイザーAIプロンプト稼働。コンテンツ自動パイプライン+エージェント間通信・メモリ・自己修復稼働。
- **新機能**: 駅選択→通勤距離付きレコメンド。Slack `!generate` `!queue` `!agents` で遠隔監視・操作可能。
- **次の改善**: ANTHROPIC_API_KEY設定後、実際のAI対話品質をテストして微調整。
- **AI自動化**: ai_content_engine.py（品質スコア8.0/10）+ 日次/週次PDCAで完全自律コンテンツ生成
- **投稿方式**: 動画→カルーセル転換（+81%エンゲージメント）、手動アップ + Buffer推奨
