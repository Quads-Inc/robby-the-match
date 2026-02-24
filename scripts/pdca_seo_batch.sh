#!/bin/bash
source ~/robby-the-match/scripts/utils.sh
init_log "pdca_seo_batch"
update_agent_state "seo_optimizer" "running"
check_instructions "seo_optimizer"

run_claude "
STATE.mdを読め。これが現状だ。他を探し回るな。CLAUDE.mdも読め。

【SEO高速改善サイクル】サブエージェント最大数で並行実行。

■ Check
1. STATE.mdのKPIとSEO状態を確認
2. lp/job-seeker/area/ と lp/job-seeker/guide/ の全子ページのtitle/h1/meta descriptionを一括診断
3. GA4データがあれば流入ゼロページを特定

■ Plan
4. 改善対象を最大5ページ選定
5. 新規キーワードを2-3個特定（docs/seo_strategy.mdのロードマップ参照）

■ Do（並行実行）
6. 既存ページ改善（title/h1/コンテンツ強化/内部リンク追加）
7. 新規子ページ2-3本作成（area/ or guide/ に追加）
8. sitemap.xml更新（全ページのURLを含めろ）
9. 内部リンク最適化（孤立ページがないか）
10. analytics.jsが全ページに入っているか確認

■ Act
11. STATE.md更新（子ページ数、SEO施策数、sitemap URL数、直近施策、次にやること）
12. PROGRESS.mdに施策詳細を追記
13. Search Consoleにping: curl -s 'https://www.google.com/ping?sitemap=サイトURL/sitemap.xml'
" 30

git_sync "seo: ${TODAY} SEO改善+子ページ追加"
update_state "SEO朝サイクル"
update_progress "🔍 SEO朝サイクル" "$(git log -1 --pretty=%s 2>/dev/null)"
update_agent_state "seo_optimizer" "completed"
slack_notify "🔍 SEO改善完了。STATE.md参照。" "seo"
write_heartbeat "seo_batch" $?
echo "[$TODAY] pdca_seo_batch完了" >> "$LOG"
