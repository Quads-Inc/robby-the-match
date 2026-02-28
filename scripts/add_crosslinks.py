#!/usr/bin/env python3
"""Add cross-links from blog articles to related guide pages."""

import os
import re

BLOG_DIR = os.path.expanduser("~/robby-the-match/blog")

blog_to_guide = {
    "agent-comparison.html": ["fee-comparison.html", "transfer-fee.html", "first-transfer.html"],
    "houmon-kango.html": ["visiting-nurse.html", "visiting-nurse-kanagawa.html", "home-nursing-startup.html"],
    "nurse-money-guide.html": ["salary-comparison.html", "nurse-salary-negotiation.html", "salary-simulator.html"],
    "kanagawa-nurse-salary.html": ["salary-comparison.html", "nurse-salary-odawara.html", "salary-simulator.html"],
    "kanagawa-west-guide.html": ["kanagawa-west-hospitals.html", "hospital-reviews.html", "nurse-commute.html"],
    "night-shift-health.html": ["night-shift.html", "work-life-balance.html", "nurse-burnout.html"],
    "nurse-market-2026.html": ["first-transfer.html", "salary-comparison.html", "fee-comparison.html"],
    "ai-medical-future.html": ["fee-comparison.html", "first-transfer.html", "career-change.html"],
    "blank-nurse-return.html": ["first-transfer.html", "nurse-age-limit.html", "interview-tips.html"],
    "odawara-living.html": ["nurse-commute.html", "nurse-salary-odawara.html", "part-time-odawara.html"],
    "yakin-nashi.html": ["night-shift.html", "clinic-vs-hospital.html", "work-life-balance.html"],
    "tenshoku-timing.html": ["retirement-timing.html", "first-transfer.html", "nurse-transfer-process.html"],
    "nurse-stress-management.html": ["nurse-burnout.html", "work-life-balance.html", "nurse-holidays.html"],
    "kosodate-nurse.html": ["maternity-leave.html", "part-time-odawara.html", "work-life-balance.html"],
    "clinic-tenshoku.html": ["clinic-vs-hospital.html", "first-transfer.html", "interview-tips.html"],
    "success-story-template.html": ["first-transfer.html", "interview-tips.html", "resume-tips.html"],
    "nurse-communication.html": ["nurse-burnout.html", "interview-tips.html", "nurse-manager-career.html"],
    "shoukai-tesuuryou.html": ["fee-comparison.html", "fee-comparison-detail.html", "transfer-fee.html"],
}

guide_titles = {
    "fee-comparison.html": "紹介手数料の比較",
    "transfer-fee.html": "転職にかかる費用まとめ",
    "first-transfer.html": "初めての転職ガイド",
    "visiting-nurse.html": "訪問看護師の仕事",
    "visiting-nurse-kanagawa.html": "神奈川県の訪問看護求人",
    "home-nursing-startup.html": "訪問看護ステーション開業",
    "salary-comparison.html": "看護師の給与比較ガイド",
    "nurse-salary-negotiation.html": "転職時の給与交渉術",
    "salary-simulator.html": "年収シミュレーター",
    "nurse-salary-odawara.html": "小田原市の看護師給与相場",
    "kanagawa-west-hospitals.html": "神奈川県の主要病院一覧",
    "hospital-reviews.html": "神奈川県の病院で働く看護師の声",
    "nurse-commute.html": "神奈川県の通勤事情",
    "night-shift.html": "夜勤の実態と対策",
    "work-life-balance.html": "看護師のワークライフバランス",
    "nurse-burnout.html": "バーンアウト対策",
    "career-change.html": "看護師からの転職",
    "nurse-age-limit.html": "看護師の年齢と転職",
    "interview-tips.html": "面接対策と回答例",
    "retirement-timing.html": "退職のタイミングと手順",
    "nurse-transfer-process.html": "転職の流れと手順",
    "nurse-holidays.html": "看護師の休日・有給事情",
    "maternity-leave.html": "看護師の産休・育休制度",
    "part-time-odawara.html": "小田原のパート看護師求人",
    "clinic-vs-hospital.html": "クリニックと病院の違い",
    "resume-tips.html": "履歴書・職務経歴書の書き方",
    "fee-comparison-detail.html": "手数料の詳細解説",
    "nurse-manager-career.html": "看護師長へのキャリアパス",
}


def build_crosslink_block(guide_files):
    """Build the HTML block for cross-links."""
    li_items = []
    for gf in guide_files:
        title = guide_titles.get(gf, gf.replace(".html", "").replace("-", " ").title())
        li_items.append(
            f'    <li><a href="/lp/job-seeker/guide/{gf}" '
            f'style="color:var(--accent,#a8dadc);font-size:0.9rem;text-decoration:none;">'
            f'{title}</a></li>'
        )
    li_str = "\n".join(li_items)
    return (
        '\n<div style="margin:32px 0;padding:24px;background:rgba(255,255,255,0.04);border-radius:12px;border:1px solid rgba(255,255,255,0.08);">\n'
        '  <h4 style="font-size:0.95rem;color:var(--text-heading,#e8e6e3);margin:0 0 12px;">もっと詳しく知る</h4>\n'
        '  <ul style="list-style:none;padding:0;margin:0;display:grid;gap:6px;">\n'
        f'{li_str}\n'
        '  </ul>\n'
        '</div>\n'
    )


def process_file(filename, guide_files):
    """Insert cross-link block into a blog article."""
    filepath = os.path.join(BLOG_DIR, filename)
    if not os.path.exists(filepath):
        print(f"  SKIP (file not found): {filename}")
        return False

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Skip if already has cross-links
    if "もっと詳しく知る" in content:
        print(f"  SKIP (already has cross-links): {filename}")
        return False

    # Find the insertion point: after the sources section closing </div>, before related-articles
    # Pattern: closing </div> of sources section, then whitespace, then <div class="related-articles">
    pattern = r'(※掲載情報は執筆時点のものであり、最新の状況と異なる場合があります。具体的な条件は各医療機関にご確認ください。\s*</p>\s*</div>)\s*(<div class="related-articles")'

    match = re.search(pattern, content)
    if not match:
        print(f"  WARNING (pattern not found): {filename}")
        return False

    block = build_crosslink_block(guide_files)
    new_content = content[:match.end(1)] + "\n" + block + "\n" + content[match.start(2):]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"  OK: {filename} (added {len(guide_files)} guide links)")
    return True


def main():
    print("Adding cross-links from blog articles to guide pages...")
    print(f"Blog directory: {BLOG_DIR}")
    print()

    success = 0
    fail = 0
    for blog_file, guides in blog_to_guide.items():
        print(f"Processing: {blog_file}")
        if process_file(blog_file, guides):
            success += 1
        else:
            fail += 1

    print()
    print(f"Done. Success: {success}, Skipped/Failed: {fail}")


if __name__ == "__main__":
    main()
