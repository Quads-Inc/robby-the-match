#!/usr/bin/env python3
"""
guide全ページ + blog全記事に出典セクションを一括追加するスクリプト。
YMYL領域のE-E-A-T向上のため、統計データの出典を明記する。

挿入位置の優先順位:
  1. <section class="related-guides" があればその直前
  2. <div class="related-articles" があればその直前
  3. <footer があればその直前
  4. </body の直前

重複防止: 既に「参考文献」「出典」が含まれているページはスキップ。
"""

import os
import re
import sys

CITATION_BLOCK = '''<div style="margin-top:40px;padding:24px;background:rgba(255,255,255,0.03);border-radius:12px;border:1px solid rgba(255,255,255,0.06);">
  <p style="font-size:0.8rem;color:var(--text-secondary,#999);line-height:1.8;margin:0;">
    <strong style="color:var(--text-heading,#e8e6e3);">参考文献・出典</strong><br>
    本記事の情報は以下の公的データ等を参考にしています。<br>
    ・厚生労働省「賃金構造基本統計調査」<br>
    ・日本看護協会「看護職員実態調査」<br>
    ・神奈川県「衛生統計年報」<br>
    ・厚生労働省「職業安定業務統計」<br>
    ※掲載情報は執筆時点のものであり、最新の状況と異なる場合があります。具体的な条件は各医療機関にご確認ください。
  </p>
</div>
'''

# Insertion point patterns in priority order
INSERTION_PATTERNS = [
    (r'(\s*<section\s+class="related-guides")', 'related-guides'),
    (r'(\s*<div\s+class="related-articles")', 'related-articles'),
    (r'(\s*<footer[\s>])', 'footer'),
    (r'(\s*</body[\s>])', 'body-close'),
]


def process_file(filepath):
    """Process a single HTML file. Returns (success, reason)."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Skip if already has citation
    if '参考文献' in content or '出典' in content:
        return False, 'already has citation'

    # Try each insertion pattern in priority order
    for pattern, label in INSERTION_PATTERNS:
        match = re.search(pattern, content)
        if match:
            insert_pos = match.start()
            # Determine proper indentation from the matched line
            line_start = content.rfind('\n', 0, insert_pos)
            if line_start == -1:
                line_start = 0
            else:
                line_start += 1
            # Extract leading whitespace
            existing_line = content[line_start:insert_pos + len(match.group(0))]
            indent = ''
            for ch in existing_line:
                if ch in (' ', '\t'):
                    indent += ch
                else:
                    break

            # Build the citation block with proper indentation
            citation_lines = CITATION_BLOCK.strip().split('\n')
            indented_citation = '\n'.join(indent + line for line in citation_lines)

            # Insert citation before the matched element
            new_content = content[:insert_pos] + '\n' + indented_citation + '\n\n' + content[insert_pos:]

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)

            return True, f'inserted before {label}'

    return False, 'no insertion point found'


def main():
    base_dir = os.path.expanduser('~/robby-the-match')

    guide_dir = os.path.join(base_dir, 'lp', 'job-seeker', 'guide')
    blog_dir = os.path.join(base_dir, 'blog')

    # Collect target files (exclude index.html)
    guide_files = sorted([
        os.path.join(guide_dir, f)
        for f in os.listdir(guide_dir)
        if f.endswith('.html') and f != 'index.html'
    ])

    blog_files = sorted([
        os.path.join(blog_dir, f)
        for f in os.listdir(blog_dir)
        if f.endswith('.html') and f != 'index.html'
    ])

    print(f"=== 出典セクション一括追加スクリプト ===\n")
    print(f"Guide対象ファイル数: {len(guide_files)}")
    print(f"Blog対象ファイル数:  {len(blog_files)}")
    print()

    total_processed = 0
    total_skipped = 0
    total_failed = 0

    for category, files in [("Guide", guide_files), ("Blog", blog_files)]:
        cat_processed = 0
        cat_skipped = 0
        cat_failed = 0

        print(f"--- {category} ---")
        for filepath in files:
            filename = os.path.basename(filepath)
            success, reason = process_file(filepath)
            if success:
                print(f"  [OK] {filename} ({reason})")
                cat_processed += 1
            elif reason == 'already has citation':
                print(f"  [SKIP] {filename} ({reason})")
                cat_skipped += 1
            else:
                print(f"  [FAIL] {filename} ({reason})")
                cat_failed += 1

        print(f"  => 処理: {cat_processed}, スキップ: {cat_skipped}, 失敗: {cat_failed}")
        print()

        total_processed += cat_processed
        total_skipped += cat_skipped
        total_failed += cat_failed

    print(f"=== 完了 ===")
    print(f"合計処理: {total_processed}ファイル")
    print(f"合計スキップ: {total_skipped}ファイル")
    print(f"合計失敗: {total_failed}ファイル")

    if total_failed > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
