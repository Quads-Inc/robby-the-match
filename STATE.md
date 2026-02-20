# ROBBY THE MATCH 状態ファイル
# 最終更新: 2026-02-20 by SEOコンテンツ大幅拡充+デプロイ

## 運用ルール
- 全PDCAサイクルはこのファイルを最初に読む（他を探し回るな）
- 作業完了後にこのファイルを更新する（次サイクルへ引き継ぎ）
- PROGRESS.mdには履歴として追記（こちらは状態のスナップショット）

## 現在のフェーズ
- マイルストーン: Week 1
- North Star: 看護師1名をA病院に紹介して成約
- 状態: 基盤構築完了、SEO+コンテンツ運用開始

## KPI
| 指標 | 目標 | 現在 | 更新日 |
|------|------|------|--------|
| SEO子ページ数 | 50 | 50（area/9 + guide/41） | 2026-02-20 |
| ブログ記事数 | 10 | 10 | 2026-02-20 |
| sitemap URL数 | - | 65 | 2026-02-20 |
| 投稿数(TikTok) | Week2:5 | 0 | 2026-02-20 |
| 投稿数(Instagram) | Week2:3 | 0 | 2026-02-20 |
| PV/日 | 100 | 0 | 2026-02-20 |
| LINE登録数 | Month2:5 | 0 | 2026-02-20 |
| 成約数 | Month3:1 | 0 | 2026-02-20 |

## ファイル構成
```
robby-the-match/
├── .env                          # 環境変数（git管理外）
├── .gitignore
├── 404.html
├── CLAUDE.md                     # 戦略プロンプト v8.0
├── PDCA_SETUP.md                 # PDCAシステム構築記録
├── PROGRESS.md                   # 日次進捗ログ
├── STATE.md                      # このファイル
├── index.html                    # メインLP（構造化データ5種）
├── privacy.html                  # プライバシーポリシー
├── terms.html                    # 利用規約
├── sitemap.xml                   # ルートsitemap（65 URL）
├── robots.txt                    # ルートrobots.txt
├── blog/                         # ブログ記事（10記事+index）
│   ├── index.html
│   ├── agent-comparison.html
│   ├── ai-medical-future.html
│   ├── kanagawa-west-guide.html
│   ├── night-shift-health.html
│   ├── nurse-communication.html
│   ├── nurse-market-2026.html
│   ├── nurse-money-guide.html
│   ├── nurse-stress-management.html
│   ├── odawara-living.html
│   └── success-story-template.html
├── lp/
│   ├── analytics.js
│   ├── robots.txt
│   ├── sitemap.xml               # 65 URLエントリ
│   └── job-seeker/
│       ├── index.html            # LP-A（構造化データ4種）
│       ├── area/                 # 地域別9ページ
│       └── guide/                # ガイド41ページ
├── scripts/
│   ├── update_sitemap.py         # sitemap自動更新
│   └── （その他既存スクリプト）
└── （その他既存ファイル）
```

## デプロイ状態
- GitHub Pages: ✅ 公開中
- 公開URL: https://haruhi-medical.github.io/robby-the-match/
- git remote: origin https://github.com/haruhi-medical/robby-the-match.git
- デプロイブランチ: master（mainからpush）
- 最新commit: 6ef63ca feat: SEOコンテンツ大幅拡充

## SEO状態
- 子ページ: area/9ページ + guide/41ページ = 計50ページ
- ブログ: 10記事 + indexページ
- sitemap.xml: 65 URLエントリ（ルート+lp/ 両方）
- robots.txt: あり（ルート直下 + lp/ 配下に各1つ、計2つ）
- GA4: ✅ 設定済み（G-X4G2BYW13B）
- Search Console: ✅ 登録済み（メタタグ検証、サイトマップ送信済み）
- Googleビジネスプロフィール: 未登録
- 構造化データ(JSON-LD):
  - index.html: WebSite, Organization, BreadcrumbList, EmploymentAgency, FAQPage（5種）
  - LP-A: Organization, JobPosting, FAQPage, BreadcrumbList（4種）
  - area子ページ（9ページ）: 各BreadcrumbList + FAQPage（2種）
  - guide子ページ（41ページ）: 各BreadcrumbList + Article（2種）
- 競合ゼロKW: 「神奈川県西部 看護師」「紹介料 10%」

## SNS状態
- TikTokアカウント: 未確認
- Instagramアカウント: 未確認
- Postiz連携: 未設定（POSTIZ_API_KEY=空）
- 今週分素材: 7本生成済み（content/generated/weekly_batch_20260220/）

## Slack状態
- Bot Token: あり（.envにSLACK_BOT_TOKEN設定済み）
- SLACK_CHANNEL_ID: C09A7U4TV4G（#claudecode）
- slack_report.py / slack_commander.py: 作成済み
- 通知テスト: 未テスト

## cron状態
```
# 日次（月〜土）
0  6 * * 1-6 /bin/bash ~/robby-the-match/scripts/pdca_morning.sh
0  7 * * 1-6 /bin/bash ~/robby-the-match/scripts/pdca_healthcheck.sh
0 15 * * 1-6 /bin/bash ~/robby-the-match/scripts/pdca_content.sh
0 23 * * 1-6 /bin/bash ~/robby-the-match/scripts/pdca_review.sh
# 週次（日曜のみ）
0  8 * * 0   /bin/bash ~/robby-the-match/scripts/pdca_weekly.sh
```

## 未完了の手動作業
- [x] GA4測定ID置換 → ✅ G-X4G2BYW13B（2/20）
- [x] LINE URL置換 → ✅ https://lin.ee/HJwmQgp4（2/20）
- [x] Search Console登録 → ✅ メタタグ検証完了+サイトマップ送信（2/20）
- [x] GitHubリポジトリpush → ✅ デプロイ完了（2/20）
- [x] GitHub Pages有効化 → ✅（2/20）
- [x] sitemap.xml URL統一 → ✅ 65 URL、haruhi-medical.github.io に統一（2/20）
- [x] robots.txt URL統一 → ✅ 統一済み（2/20）
- [ ] Googleビジネスプロフィール登録
- [ ] 独自ドメイン取得
- [ ] TikTokアカウント作成/連携
- [ ] Instagramアカウント作成/連携
- [ ] Mac Miniスリープ無効化（sudo pmset -a sleep 0）
- [ ] Search Consoleでsitemap再送信（65 URLに更新したため）

## 次にやるべきこと（優先順）
1. ~~GitHub push + Pages有効化~~ → ✅ 完了
2. ~~GA4設定~~ → ✅ 完了
3. ~~Search Console登録~~ → ✅ 完了
4. ~~LINE URL設定~~ → ✅ 完了
5. ~~sitemap.xml / robots.txt URL統一~~ → ✅ 完了
6. Search Consoleでsitemap再送信（65 URLに更新）
7. TikTok初投稿（素材は準備済み）
8. Googleビジネスプロフィール登録

## 問題・ブロッカー
- ~~sitemap.xmlのURL不一致~~ → ✅ 解決済み（全65 URLをharuhi-medical.github.ioに統一）
- ~~robots.txtのURL不一致~~ → ✅ 解決済み
- **lp/facility/ が空**: LP-B（施設向け）未作成。Phase1では不要。
- **Postiz API Key未設定**: TikTok自動投稿不可。手動アップロードが必要。

## 戦略メモ
- 競合ゼロKW: 「神奈川県西部 看護師」「紹介料 10%」
- 3軸: 手数料破壊(10%) x 地域密着(9市) x 転職品質
- 大手の隙間: TikTokオーガニック未参入
- ロードマップ: 即座→地域KW、1-3ヶ月→高競合KW、12ヶ月→検索1位
