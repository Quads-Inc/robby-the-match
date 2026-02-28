#!/usr/bin/env python3
"""
meta情報統一スクリプト
=====================
全HTMLファイルのmeta情報を検証し、以下を統一する:
1. meta robots: index, follow, max-snippet:-1, max-image-preview:large
2. og:image: https://quads-nurse.com/assets/ogp.png
3. twitter:card: summary_large_image
4. og:locale: ja_JP
5. twitter:image: https://quads-nurse.com/assets/ogp.png (欠落なら追加)
"""

import os
import re
import glob
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 対象ディレクトリ
TARGET_DIRS = [
    os.path.join(BASE_DIR, "lp", "job-seeker", "guide"),
    os.path.join(BASE_DIR, "lp", "job-seeker", "area"),
    os.path.join(BASE_DIR, "blog"),
    # トップレベルHTMLも対象
    BASE_DIR,
]

# 理想のメタ値
IDEAL_ROBOTS = 'index, follow, max-snippet:-1, max-image-preview:large'
IDEAL_OG_IMAGE = 'https://quads-nurse.com/assets/ogp.png'
IDEAL_TWITTER_CARD = 'summary_large_image'
IDEAL_OG_LOCALE = 'ja_JP'

# 統計
stats = {
    "scanned": 0,
    "modified": 0,
    "robots_added": 0,
    "robots_updated": 0,
    "og_image_added": 0,
    "og_image_fixed": 0,
    "twitter_card_added": 0,
    "twitter_card_fixed": 0,
    "og_locale_added": 0,
    "og_locale_fixed": 0,
    "twitter_image_added": 0,
    "twitter_image_fixed": 0,
    "files_detail": [],
}

# 除外対象
EXCLUDE = {"404.html", "dashboard.html", "proposal.html"}


def collect_html_files():
    """対象HTMLファイルを収集"""
    files = set()
    for d in TARGET_DIRS:
        if d == BASE_DIR:
            # トップレベルは直下のHTMLのみ（サブディレクトリ除外）
            for f in glob.glob(os.path.join(d, "*.html")):
                fname = os.path.basename(f)
                if fname not in EXCLUDE:
                    files.add(f)
        else:
            for f in glob.glob(os.path.join(d, "*.html")):
                files.add(f)
    return sorted(files)


def find_head_end(content):
    """</head>の位置を返す"""
    m = re.search(r'</head>', content, re.IGNORECASE)
    return m.start() if m else -1


def find_title_end(content):
    """</title>タグの直後の位置を返す"""
    m = re.search(r'</title>', content, re.IGNORECASE)
    return m.end() if m else -1


def has_meta(content, name=None, prop=None):
    """指定のmeta属性が存在するか確認し、マッチオブジェクトを返す"""
    if name:
        pattern = rf'<meta\s+name="{re.escape(name)}"\s+content="([^"]*)"[^>]*/?\s*>'
        m = re.search(pattern, content, re.IGNORECASE)
        if not m:
            # content="..." name="..." の順もある
            pattern = rf'<meta\s+content="([^"]*)"\s+name="{re.escape(name)}"[^>]*/?\s*>'
            m = re.search(pattern, content, re.IGNORECASE)
        return m
    if prop:
        pattern = rf'<meta\s+property="{re.escape(prop)}"\s+content="([^"]*)"[^>]*/?\s*>'
        m = re.search(pattern, content, re.IGNORECASE)
        if not m:
            pattern = rf'<meta\s+content="([^"]*)"\s+property="{re.escape(prop)}"[^>]*/?\s*>'
            m = re.search(pattern, content, re.IGNORECASE)
        return m
    return None


def process_file(filepath):
    """1ファイルを処理する"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content
    changes = []
    relpath = os.path.relpath(filepath, BASE_DIR)

    # ─── 1. meta robots ───
    m = has_meta(content, name="robots")
    if m:
        current_val = m.group(1)
        if current_val != IDEAL_ROBOTS:
            old_tag = m.group(0)
            new_tag = f'<meta name="robots" content="{IDEAL_ROBOTS}">'
            content = content.replace(old_tag, new_tag, 1)
            changes.append(f"robots更新: '{current_val}' -> '{IDEAL_ROBOTS}'")
            stats["robots_updated"] += 1
    else:
        # titleタグの直後に挿入
        title_end = find_title_end(content)
        if title_end > 0:
            insert_tag = f'\n    <meta name="robots" content="{IDEAL_ROBOTS}">'
            content = content[:title_end] + insert_tag + content[title_end:]
            changes.append("robots追加")
            stats["robots_added"] += 1

    # ─── 2. og:image ───
    m = has_meta(content, prop="og:image")
    if m:
        current_val = m.group(1)
        if current_val != IDEAL_OG_IMAGE:
            old_tag = m.group(0)
            new_tag = f'<meta property="og:image" content="{IDEAL_OG_IMAGE}">'
            content = content.replace(old_tag, new_tag, 1)
            changes.append(f"og:image修正: '{current_val}' -> '{IDEAL_OG_IMAGE}'")
            stats["og_image_fixed"] += 1
    else:
        # og:typeの後、またはtitleタグの後に挿入
        m_ogtype = has_meta(content, prop="og:type")
        if m_ogtype:
            insert_pos = m_ogtype.end()
        else:
            insert_pos = find_title_end(content)
        if insert_pos > 0:
            insert_tag = f'\n    <meta property="og:image" content="{IDEAL_OG_IMAGE}">'
            content = content[:insert_pos] + insert_tag + content[insert_pos:]
            changes.append("og:image追加")
            stats["og_image_added"] += 1

    # ─── 3. twitter:card ───
    m = has_meta(content, name="twitter:card")
    if m:
        current_val = m.group(1)
        if current_val != IDEAL_TWITTER_CARD:
            old_tag = m.group(0)
            new_tag = f'<meta name="twitter:card" content="{IDEAL_TWITTER_CARD}">'
            content = content.replace(old_tag, new_tag, 1)
            changes.append(f"twitter:card修正: '{current_val}' -> '{IDEAL_TWITTER_CARD}'")
            stats["twitter_card_fixed"] += 1
    else:
        # robots metaの後に挿入
        m_robots = has_meta(content, name="robots")
        if m_robots:
            insert_pos = m_robots.end()
        else:
            insert_pos = find_title_end(content)
        if insert_pos > 0:
            insert_tag = f'\n    <meta name="twitter:card" content="{IDEAL_TWITTER_CARD}">'
            content = content[:insert_pos] + insert_tag + content[insert_pos:]
            changes.append("twitter:card追加")
            stats["twitter_card_added"] += 1

    # ─── 4. og:locale ───
    m = has_meta(content, prop="og:locale")
    if m:
        current_val = m.group(1)
        if current_val != IDEAL_OG_LOCALE:
            old_tag = m.group(0)
            new_tag = f'<meta property="og:locale" content="{IDEAL_OG_LOCALE}">'
            content = content.replace(old_tag, new_tag, 1)
            changes.append(f"og:locale修正: '{current_val}' -> '{IDEAL_OG_LOCALE}'")
            stats["og_locale_fixed"] += 1
    else:
        # og:site_nameの後に挿入
        m_sitename = has_meta(content, prop="og:site_name")
        if m_sitename:
            insert_pos = m_sitename.end()
        else:
            m_ogimage = has_meta(content, prop="og:image")
            if m_ogimage:
                insert_pos = m_ogimage.end()
            else:
                insert_pos = find_title_end(content)
        if insert_pos > 0:
            insert_tag = f'\n    <meta property="og:locale" content="{IDEAL_OG_LOCALE}">'
            content = content[:insert_pos] + insert_tag + content[insert_pos:]
            changes.append("og:locale追加")
            stats["og_locale_added"] += 1

    # ─── 5. twitter:image ───
    m = has_meta(content, name="twitter:image")
    if m:
        current_val = m.group(1)
        if current_val != IDEAL_OG_IMAGE:
            old_tag = m.group(0)
            new_tag = f'<meta name="twitter:image" content="{IDEAL_OG_IMAGE}">'
            content = content.replace(old_tag, new_tag, 1)
            changes.append(f"twitter:image修正: '{current_val}' -> '{IDEAL_OG_IMAGE}'")
            stats["twitter_image_fixed"] += 1
    else:
        # twitter:cardの後に挿入
        m_tcard = has_meta(content, name="twitter:card")
        if m_tcard:
            # twitter:descriptionがあればその後に
            m_tdesc = has_meta(content, name="twitter:description")
            if m_tdesc:
                insert_pos = m_tdesc.end()
            else:
                # twitter:titleがあればその後に
                m_ttitle = has_meta(content, name="twitter:title")
                if m_ttitle:
                    insert_pos = m_ttitle.end()
                else:
                    insert_pos = m_tcard.end()
        else:
            insert_pos = find_title_end(content)
        if insert_pos > 0:
            insert_tag = f'\n    <meta name="twitter:image" content="{IDEAL_OG_IMAGE}">'
            content = content[:insert_pos] + insert_tag + content[insert_pos:]
            changes.append("twitter:image追加")
            stats["twitter_image_added"] += 1

    # ─── 書き込み ───
    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        stats["modified"] += 1
        stats["files_detail"].append((relpath, changes))

    stats["scanned"] += 1


def main():
    print("=" * 60)
    print("meta情報統一スクリプト")
    print("=" * 60)
    print()

    files = collect_html_files()
    print(f"対象ファイル数: {len(files)}")
    print()

    for f in files:
        process_file(f)

    # ─── レポート ───
    print("=" * 60)
    print("処理結果")
    print("=" * 60)
    print(f"スキャン済み: {stats['scanned']} ファイル")
    print(f"変更済み:     {stats['modified']} ファイル")
    print()

    print("--- タスク1: meta robots ---")
    print(f"  追加: {stats['robots_added']} ファイル")
    print(f"  更新: {stats['robots_updated']} ファイル")
    ok = stats['scanned'] - stats['robots_added'] - stats['robots_updated']
    print(f"  正常: {ok} ファイル")
    print()

    print("--- タスク2: og:image ---")
    print(f"  追加: {stats['og_image_added']} ファイル")
    print(f"  修正: {stats['og_image_fixed']} ファイル")
    ok = stats['scanned'] - stats['og_image_added'] - stats['og_image_fixed']
    print(f"  正常: {ok} ファイル")
    print()

    print("--- タスク3: twitter:card ---")
    print(f"  追加: {stats['twitter_card_added']} ファイル")
    print(f"  修正: {stats['twitter_card_fixed']} ファイル")
    ok = stats['scanned'] - stats['twitter_card_added'] - stats['twitter_card_fixed']
    print(f"  正常: {ok} ファイル")
    print()

    print("--- タスク4: og:locale ---")
    print(f"  追加: {stats['og_locale_added']} ファイル")
    print(f"  修正: {stats['og_locale_fixed']} ファイル")
    ok = stats['scanned'] - stats['og_locale_added'] - stats['og_locale_fixed']
    print(f"  正常: {ok} ファイル")
    print()

    print("--- 追加: twitter:image ---")
    print(f"  追加: {stats['twitter_image_added']} ファイル")
    print(f"  修正: {stats['twitter_image_fixed']} ファイル")
    ok = stats['scanned'] - stats['twitter_image_added'] - stats['twitter_image_fixed']
    print(f"  正常: {ok} ファイル")
    print()

    if stats["files_detail"]:
        print("=" * 60)
        print("変更ファイル詳細")
        print("=" * 60)
        for relpath, changes in stats["files_detail"]:
            print(f"\n  {relpath}:")
            for c in changes:
                print(f"    - {c}")

    print()
    print("=" * 60)
    print(f"完了: {stats['scanned']}ファイルスキャン、{stats['modified']}ファイル修正")
    print("=" * 60)


if __name__ == "__main__":
    main()
