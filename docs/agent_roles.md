# ROBBY THE MATCH Agent Team ロール定義

## 概要
8エージェント体制でPDCAサイクルを自律運用する。
各エージェントはcronで起動し、STATE.md → agent_state.json を読んで状況を把握してから実行する。

## エージェント一覧

| # | エージェント | cron | 自律レベル | 主な責務 |
|---|------------|------|-----------|---------|
| 1 | SEO Optimizer | 04:00 月-土 | SEMI-AUTO | SEO改善・構造化データ・サイトマップ |
| 2 | Health Monitor | 07:00 月-土 | FULL-AUTO | システム監視・障害検知・自動復旧 |
| 3 | Competitor Analyst | 10:00 月-土 | SEMI-AUTO | 競合分析・トレンド調査 |
| 4 | Content Creator | 15:00 月-土 | SEMI-AUTO | コンテンツ生成・スライド作成 |
| 5 | Daily Reviewer | 23:00 月-土 | FULL-AUTO | 日次KPIレビュー・進捗記録 |
| 6 | Weekly Strategist | 日曜 06:00 | SEMI-AUTO | 週次戦略レビュー・方針調整 |
| 7 | Slack Commander | */5分 | FULL-AUTO | Slack監視・指示受信・ルーティング |
| 8 | SNS Poster | 17:30 月-土 | FULL-AUTO | TikTok/Instagram自動投稿・動画生成 |

## 自律レベルの定義

- **FULL-AUTO**: 人間の承認なしに実行・反映可能
- **SEMI-AUTO**: 実行は自動だが、重要な変更（LP修正、戦略変更）はSlack承認を待つ

## 各エージェントの詳細

### 1. SEO Optimizer（pdca_seo_batch.sh）
- **入力**: STATE.md, Search Console データ, sitemap.xml
- **出力**: SEOページ改善、構造化データ修正、サイトマップ更新
- **権限**: ページ修正可（新規ページ作成はSlack承認後）
- **状態更新**: agent_state.json の seo_optimizer セクション

### 2. Health Monitor（pdca_healthcheck.sh）
- **入力**: GitHub Pages応答、cron実行ログ、Slack API状態
- **出力**: 障害通知、自動復旧試行
- **権限**: 障害検知時に即Slack通知。復旧のためのgit push可。
- **状態更新**: sharedContext.knownIssues

### 3. Competitor Analyst（pdca_competitor.sh）
- **入力**: Web検索結果、競合SNSアカウント
- **出力**: 競合レポート、トレンド情報
- **権限**: data/ への書き込みのみ。LP修正はSEO Optimizerに委任。
- **状態更新**: agentMemory.competitor_analyst

### 4. Content Creator（pdca_content.sh）
- **入力**: CLAUDE.md のコンテンツストック、contentMix進捗
- **出力**: 台本JSON、スライド画像、Slack承認依頼
- **権限**: content/ ディレクトリへの書き込み。投稿はSlack承認後に人間が実行。
- **状態更新**: agentMemory.content_creator, sharedContext.contentMixThisWeek

### 5. Daily Reviewer（pdca_review.sh）
- **入力**: 全ログ、agent_state.json、PROGRESS.md
- **出力**: 日次レポート（Slack送信）、PROGRESS.md更新
- **権限**: PROGRESS.md, STATE.md の更新、Slackレポート送信
- **状態更新**: sharedContext全般

### 6. Weekly Strategist（pdca_weekly.sh）
- **入力**: 週間KPI、全エージェントの実行結果、SNSパフォーマンスデータ
- **出力**: 週次戦略レポート、STATE.md更新、優先順位調整
- **権限**: STATE.md の戦略セクション更新
- **状態更新**: 全セクション見直し

### 7. Slack Commander（slack_commander.py）
- **入力**: Slackメッセージ
- **出力**: 指示の解析・ルーティング、簡易応答
- **権限**: data/slack_instructions.json への書き込み
- **コマンド**: status, report, kpi, help, 自由テキスト指示

### 8. SNS Poster（pdca_sns_post.sh）
- **入力**: data/posting_queue.json、content/generated/ のスライド画像
- **出力**: TikTok投稿（動画スライドショー）、投稿結果ログ
- **権限**: FULL-AUTO — 毎日17:30に自動投稿実行
- **ワークフロー**:
  1. posting_queue.json から次の未投稿コンテンツを取得
  2. ffmpegで6枚スライドからMP4動画を生成（各3秒 = 18秒）
  3. tiktok-uploaderでTikTokにアップロード（Cookie認証）
  4. 投稿結果をSlack通知 + キュー更新
  5. 失敗時はSlackに手動投稿依頼を送信
- **状態更新**: agentMemory.sns_poster
- **投稿スケジュール**: 17:30（日勤後帰宅中の看護師ターゲット）
- **フォールバック**: Cookie期限切れ/認証失敗時 → Slack通知で手動投稿依頼

## エージェント間の連携フロー

```
Content Creator (15:00) → 台本JSON + スライド画像生成
                                    ↓
SNS Poster (17:30) → posting_queue.json確認 → ffmpeg動画生成 → TikTok投稿
                                    ↓
Slack Commander (*/5分) → 指示受信 → data/slack_instructions.json
                                    ↓
各エージェント起動時 → slack_instructions.json 確認 → 指示があれば実行
                                    ↓
実行結果 → agent_state.json 更新 → Slack通知
                                    ↓
Daily Reviewer (23:00) → 全結果集約 → PROGRESS.md + Slackレポート
```

## SNS投稿パイプライン

```
1. Content Creator が台本JSON + スライド6枚を生成
2. tiktok_post.py --init-queue でキューに追加
3. pdca_sns_post.sh (cron 17:30) が次の未投稿を実行:
   a. ffmpegで6枚PNGからMP4動画生成（各3秒=18秒）
   b. tiktok-uploaderでTikTokに投稿
   c. 結果をposting_queue.json + Slackに記録
4. Daily Reviewer が投稿結果を集約してレポート
```

## 障害復旧フロー

```
1. Health Monitor がエラー検知
2. 自動復旧を試行（git pull, cron再起動等）
3. 復旧成功 → Slack通知「✅ 復旧完了」
4. 復旧失敗 → Slack通知「🔴 手動対応必要」+ knownIssues に追記
5. 次回Daily Reviewer が未解決issueを再通知
```
