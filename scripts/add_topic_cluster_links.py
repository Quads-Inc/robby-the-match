#!/usr/bin/env python3
"""
トピッククラスター相互リンク追加スクリプト
各ガイドページに同クラスター内リンク(3-5個) + クロスクラスターリンク(1-2個) を追加する。
"""

import os
import re
import random

GUIDE_DIR = os.path.expanduser("~/robby-the-match/lp/job-seeker/guide")

# === クラスター定義 ===
CLUSTERS = {
    "salary": [
        ("salary-comparison.html", "看護師の給与比較ガイド"),
        ("nurse-salary-odawara.html", "小田原市の看護師給与相場"),
        ("nurse-salary-negotiation.html", "転職時の給与交渉術"),
        ("fee-comparison.html", "紹介手数料の比較"),
        ("fee-comparison-detail.html", "手数料の詳細解説"),
        ("transfer-fee.html", "転職にかかる費用まとめ"),
    ],
    "process": [
        ("first-transfer.html", "初めての転職ガイド"),
        ("nurse-transfer-process.html", "転職の流れと手順"),
        ("interview-tips.html", "面接対策と回答例"),
        ("resume-tips.html", "履歴書・職務経歴書の書き方"),
        ("nurse-interview-questions.html", "よくある面接質問集"),
        ("retirement-timing.html", "退職のタイミングと手順"),
    ],
    "career": [
        ("certified-nurse.html", "認定看護師・専門看護師ガイド"),
        ("operating-room-nurse.html", "手術室看護師のキャリア"),
        ("pediatric-nurse.html", "小児科看護師の働き方"),
        ("hospice-nurse.html", "ホスピス看護師の仕事"),
        ("er-nurse-career.html", "救急看護師のキャリアパス"),
        ("dialysis-nurse.html", "透析看護師の転職ガイド"),
        ("orthopedic-nurse.html", "整形外科看護師の仕事"),
        ("mental-health-nurse.html", "精神科看護師の働き方"),
        ("nurse-manager-career.html", "看護師長へのキャリアパス"),
    ],
    "workstyle": [
        ("night-shift.html", "夜勤の実態と対策"),
        ("part-time-odawara.html", "小田原のパート看護師求人"),
        ("visiting-nurse.html", "訪問看護師の仕事"),
        ("visiting-nurse-kanagawa.html", "神奈川県の訪問看護求人"),
        ("home-nursing-startup.html", "訪問看護ステーション開業"),
        ("day-service-nurse.html", "デイサービス看護師の仕事"),
        ("school-nurse.html", "養護教諭・学校看護師"),
        ("work-life-balance.html", "看護師のワークライフバランス"),
        ("nurse-holidays.html", "看護師の休日・有給事情"),
        ("maternity-leave.html", "看護師の産休・育休制度"),
    ],
    "general": [
        ("nurse-burnout.html", "バーンアウト対策"),
        ("career-change.html", "看護師からの転職"),
        ("nurse-side-job.html", "看護師の副業ガイド"),
        ("nurse-age-limit.html", "看護師の年齢と転職"),
        ("nurse-license-renewal.html", "看護師免許の更新"),
        ("nurse-commute.html", "神奈川県の通勤事情"),
        ("new-grad-transfer.html", "新卒看護師の転職"),
        ("hospital-reviews.html", "神奈川県の病院で働く看護師の声"),
        ("kanagawa-west-hospitals.html", "神奈川県の主要病院一覧"),
        ("rehabilitation-hospital.html", "リハビリ病院の看護師"),
        ("clinic-vs-hospital.html", "クリニックと病院の違い"),
    ],
}

# クロスクラスター関連性マップ: 各クラスターに対して関連性の高い他クラスター
CROSS_CLUSTER_AFFINITY = {
    "salary": ["process", "general"],
    "process": ["salary", "career"],
    "career": ["workstyle", "process"],
    "workstyle": ["career", "general"],
    "general": ["workstyle", "process"],
}

# ファイル→クラスター逆引き辞書を作る
FILE_TO_CLUSTER = {}
FILE_TO_TITLE = {}
for cluster_name, pages in CLUSTERS.items():
    for filename, title in pages:
        FILE_TO_CLUSTER[filename] = cluster_name
        FILE_TO_TITLE[filename] = title


def get_same_cluster_links(filename, max_links=5):
    """同クラスター内の他ページへのリンクを返す（自分自身を除外）"""
    cluster = FILE_TO_CLUSTER[filename]
    candidates = [(f, t) for f, t in CLUSTERS[cluster] if f != filename]
    # クラスターのサイズが5以下ならそのまま全部、6以上なら5個選ぶ
    if len(candidates) <= max_links:
        return candidates
    # ランダムではなく先頭から5個（安定した結果のため）
    return candidates[:max_links]


def get_cross_cluster_links(filename, count=2):
    """別クラスターから関連性の高いリンクを返す"""
    cluster = FILE_TO_CLUSTER[filename]
    affinity_clusters = CROSS_CLUSTER_AFFINITY[cluster]

    candidates = []
    for aff_cluster in affinity_clusters:
        candidates.extend(CLUSTERS[aff_cluster])

    # ファイル固有のシードで安定した選択をする
    random.seed(filename)
    selected = random.sample(candidates, min(count, len(candidates)))
    return selected


def generate_related_section(filename):
    """関連ガイドセクションのHTMLを生成"""
    same_links = get_same_cluster_links(filename)
    cross_links = get_cross_cluster_links(filename, 2)

    all_links = same_links + cross_links

    link_items = []
    for f, title in all_links:
        link_items.append(
            f'    <li><a href="{f}" style="color:var(--accent,#a8dadc);text-decoration:none;font-size:0.95rem;">{title}</a></li>'
        )

    links_html = "\n".join(link_items)

    section_html = f'''<section class="related-guides" style="margin-top:48px;padding:32px 0;border-top:1px solid rgba(255,255,255,0.1);">
  <h3 style="font-size:1.2rem;color:var(--text-heading,#e8e6e3);margin-bottom:20px;">関連するガイド記事</h3>
  <ul style="list-style:none;padding:0;display:grid;grid-template-columns:1fr;gap:8px;">
{links_html}
  </ul>
</section>'''
    return section_html


def find_insertion_point(html):
    """
    挿入位置を見つける。
    最後の cta-band の直前、またはfooterの直前に挿入する。
    インライン形式（改行なし）のHTMLにも対応。
    """
    # footer直前を探す（改行あり/なし両対応）
    footer_match = re.search(r'<footer[\s>]', html)
    if not footer_match:
        return None

    footer_pos = footer_match.start()

    # footer前の最後の cta-band の開始位置を探す（改行あり/なし両対応）
    cta_matches = list(re.finditer(r'<div class="cta-band">', html))

    if cta_matches:
        # 最後のCTAバンドの直前に挿入
        last_cta = cta_matches[-1]
        insert_pos = last_cta.start()
        # 直前の改行位置があればそこを使う
        # 改行がなければ（インライン形式の場合）そのまま
        newline_before = html.rfind('\n', 0, insert_pos)
        if newline_before >= 0 and html[newline_before:insert_pos].strip() == '':
            return newline_before
        return insert_pos

    # CTAバンドがない場合、footer直前に挿入
    newline_before = html.rfind('\n', 0, footer_pos)
    if newline_before >= 0 and html[newline_before:footer_pos].strip() == '':
        return newline_before
    return footer_pos


def insert_related_section(filepath, filename):
    """ファイルに関連セクションを挿入する"""
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    # 既に related-guides が存在する場合はスキップ
    if 'class="related-guides"' in html:
        print(f"  SKIP (already has related-guides): {filename}")
        return False

    section_html = generate_related_section(filename)

    insertion_pos = find_insertion_point(html)
    if insertion_pos is None:
        print(f"  ERROR: Could not find insertion point in {filename}")
        return False

    # 挿入位置にセクションを追加
    new_html = html[:insertion_pos] + "\n\n    " + section_html + "\n" + html[insertion_pos:]

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_html)

    return True


def main():
    print("=== トピッククラスター相互リンク追加 ===\n")

    success_count = 0
    skip_count = 0
    error_count = 0

    all_files = sorted(FILE_TO_CLUSTER.keys())

    for filename in all_files:
        filepath = os.path.join(GUIDE_DIR, filename)

        if not os.path.exists(filepath):
            print(f"  NOT FOUND: {filename}")
            error_count += 1
            continue

        cluster = FILE_TO_CLUSTER[filename]
        same_links = get_same_cluster_links(filename)
        cross_links = get_cross_cluster_links(filename, 2)

        print(f"Processing: {filename} (cluster: {cluster})")
        print(f"  Same-cluster links: {len(same_links)}, Cross-cluster links: {len(cross_links)}")

        result = insert_related_section(filepath, filename)
        if result:
            success_count += 1
            print(f"  OK: inserted related-guides section")
        elif 'related-guides' in open(filepath, 'r').read():
            skip_count += 1
        else:
            error_count += 1

    print(f"\n=== 完了 ===")
    print(f"成功: {success_count}")
    print(f"スキップ: {skip_count}")
    print(f"エラー: {error_count}")
    print(f"合計: {success_count + skip_count + error_count}")


if __name__ == "__main__":
    main()
