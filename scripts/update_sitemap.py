#!/usr/bin/env python3
"""
ROBBY THE MATCH - sitemap.xml 自動更新スクリプト

走査対象:
  - lp/job-seeker/area/*.html
  - lp/job-seeker/guide/*.html
  - blog/*.html
  - ルート直下の主要ページ（index.html, privacy.html, terms.html）
  - lp/job-seeker/index.html
  - lp/facility/（存在する場合）

出力:
  - sitemap.xml（ルート直下）
  - lp/sitemap.xml（同一内容）

実行:
  python3 scripts/update_sitemap.py
"""

import glob
import os
import sys
from datetime import date
from xml.dom.minidom import Document

# === 設定 ===
BASE_URL = "https://haruhi-medical.github.io/robby-the-match/"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 出力先
OUTPUT_ROOT_SITEMAP = os.path.join(PROJECT_ROOT, "sitemap.xml")
OUTPUT_LP_SITEMAP = os.path.join(PROJECT_ROOT, "lp", "sitemap.xml")

# 今日の日付
TODAY = date.today().isoformat()


def file_to_url(filepath):
    """ファイルパスからURLを生成する"""
    rel = os.path.relpath(filepath, PROJECT_ROOT)
    # index.html の場合はディレクトリURLにする
    if rel.endswith("/index.html") or rel == "index.html":
        rel = rel.replace("index.html", "")
    url = BASE_URL + rel
    return url


def get_lastmod(filepath):
    """ファイルの最終更新日を取得する"""
    mtime = os.path.getmtime(filepath)
    return date.fromtimestamp(mtime).isoformat()


def discover_pages():
    """全ページを走査して URL エントリのリストを返す"""
    entries = []

    # --- 固定ページ（トップ、プライバシー、利用規約） ---
    static_pages = {
        "index.html": {"changefreq": "monthly", "priority": "0.8"},
        "privacy.html": {"changefreq": "yearly", "priority": "0.3"},
        "terms.html": {"changefreq": "yearly", "priority": "0.3"},
    }
    for filename, meta in static_pages.items():
        filepath = os.path.join(PROJECT_ROOT, filename)
        if os.path.exists(filepath):
            entries.append({
                "loc": file_to_url(filepath),
                "lastmod": get_lastmod(filepath),
                "changefreq": meta["changefreq"],
                "priority": meta["priority"],
            })

    # --- LP: 求職者向けトップ ---
    job_seeker_index = os.path.join(PROJECT_ROOT, "lp", "job-seeker", "index.html")
    if os.path.exists(job_seeker_index):
        entries.append({
            "loc": file_to_url(job_seeker_index),
            "lastmod": get_lastmod(job_seeker_index),
            "changefreq": "weekly",
            "priority": "1.0",
        })

    # --- LP: 施設向けトップ ---
    facility_index = os.path.join(PROJECT_ROOT, "lp", "facility", "index.html")
    if os.path.exists(facility_index):
        entries.append({
            "loc": file_to_url(facility_index),
            "lastmod": get_lastmod(facility_index),
            "changefreq": "monthly",
            "priority": "0.5",
        })

    # --- 地域別ページ: lp/job-seeker/area/*.html ---
    area_pattern = os.path.join(PROJECT_ROOT, "lp", "job-seeker", "area", "*.html")
    area_files = sorted(glob.glob(area_pattern))
    for filepath in area_files:
        entries.append({
            "loc": file_to_url(filepath),
            "lastmod": get_lastmod(filepath),
            "changefreq": "weekly",
            "priority": "0.8",
        })

    # --- ガイドページ: lp/job-seeker/guide/*.html ---
    guide_pattern = os.path.join(PROJECT_ROOT, "lp", "job-seeker", "guide", "*.html")
    guide_files = sorted(glob.glob(guide_pattern))
    for filepath in guide_files:
        entries.append({
            "loc": file_to_url(filepath),
            "lastmod": get_lastmod(filepath),
            "changefreq": "monthly",
            "priority": "0.7",
        })

    # --- ブログ記事: blog/*.html ---
    blog_pattern = os.path.join(PROJECT_ROOT, "blog", "*.html")
    blog_files = sorted(glob.glob(blog_pattern))
    for filepath in blog_files:
        entries.append({
            "loc": file_to_url(filepath),
            "lastmod": get_lastmod(filepath),
            "changefreq": "weekly",
            "priority": "0.6",
        })

    return entries


def generate_sitemap_xml(entries):
    """エントリリストからsitemap.xmlの文字列を生成する"""
    doc = Document()

    urlset = doc.createElement("urlset")
    urlset.setAttribute("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
    doc.appendChild(urlset)

    for entry in entries:
        url_elem = doc.createElement("url")

        loc = doc.createElement("loc")
        loc.appendChild(doc.createTextNode(entry["loc"]))
        url_elem.appendChild(loc)

        lastmod = doc.createElement("lastmod")
        lastmod.appendChild(doc.createTextNode(entry["lastmod"]))
        url_elem.appendChild(lastmod)

        changefreq = doc.createElement("changefreq")
        changefreq.appendChild(doc.createTextNode(entry["changefreq"]))
        url_elem.appendChild(changefreq)

        priority = doc.createElement("priority")
        priority.appendChild(doc.createTextNode(entry["priority"]))
        url_elem.appendChild(priority)

        urlset.appendChild(url_elem)

    # xml.dom.minidom の toprettyxml は宣言を含む
    xml_str = doc.toprettyxml(indent="  ", encoding="UTF-8")
    # bytes -> str
    return xml_str.decode("utf-8")


def write_sitemap(xml_content, output_path):
    """sitemap.xmlをファイルに書き出す"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(xml_content)
    print(f"  -> {output_path}")


def main():
    print("=" * 60)
    print("ROBBY THE MATCH - sitemap.xml 自動更新")
    print("=" * 60)
    print(f"プロジェクトルート: {PROJECT_ROOT}")
    print(f"ベースURL: {BASE_URL}")
    print(f"実行日: {TODAY}")
    print()

    # ページ走査
    print("[1/3] ページを走査中...")
    entries = discover_pages()
    print(f"  検出ページ数: {len(entries)}")
    print()

    # カテゴリ別の内訳表示
    categories = {
        "トップ/固定ページ": 0,
        "LP 求職者向け": 0,
        "LP 施設向け": 0,
        "地域別ページ": 0,
        "ガイドページ": 0,
        "ブログ記事": 0,
    }
    for entry in entries:
        loc = entry["loc"]
        if "/area/" in loc:
            categories["地域別ページ"] += 1
        elif "/guide/" in loc:
            categories["ガイドページ"] += 1
        elif "/blog/" in loc:
            categories["ブログ記事"] += 1
        elif "/job-seeker/" in loc:
            categories["LP 求職者向け"] += 1
        elif "/facility/" in loc:
            categories["LP 施設向け"] += 1
        else:
            categories["トップ/固定ページ"] += 1

    for cat, count in categories.items():
        if count > 0:
            print(f"  {cat}: {count}ページ")
    print()

    # XML生成
    print("[2/3] sitemap.xml を生成中...")
    xml_content = generate_sitemap_xml(entries)

    # 書き出し
    print("[3/3] ファイルを書き出し中...")
    write_sitemap(xml_content, OUTPUT_ROOT_SITEMAP)
    write_sitemap(xml_content, OUTPUT_LP_SITEMAP)
    print()

    # URLリスト表示
    print("--- 登録URL一覧 ---")
    for i, entry in enumerate(entries, 1):
        print(f"  {i:2d}. {entry['loc']}")
    print()
    print(f"合計: {len(entries)} URL")
    print("=" * 60)
    print("完了!")


if __name__ == "__main__":
    main()
