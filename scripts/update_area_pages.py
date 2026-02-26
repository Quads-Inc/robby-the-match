#!/usr/bin/env python3
"""
エリアページの施設データセクションを公開データで更新する。
areas.jsのデータを読み込み、各エリアページのHTMLに施設テーブルを挿入/更新する。

Usage: python3 scripts/update_area_pages.py
"""

import json
import re
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
AREA_DIR = BASE / "lp" / "job-seeker" / "area"

# areas.js → Node.jsで施設データをJSON出力
def load_areas_data():
    """Node.jsでareas.jsを読み込み、JSON形式で取得"""
    script = """
    const { AREA_DATABASE } = require('./data/areas.js');
    const result = {};
    for (const a of AREA_DATABASE) {
        result[a.areaId] = {
            name: a.name,
            facilityCount: a.facilityCount,
            nurseAvgSalary: a.nurseAvgSalary,
            majorFacilities: a.majorFacilities.map(f => ({
                name: f.name,
                type: f.type,
                beds: f.beds,
                nurseCount: f.nurseCount,
                nursingRatio: f.nursingRatio || '',
                emergencyLevel: f.emergencyLevel || '',
                ownerType: f.ownerType || '',
                dpcHospital: f.dpcHospital || false,
                ambulanceCount: f.ambulanceCount || 0,
                doctorCount: f.doctorCount || 0,
                ptCount: f.ptCount || 0,
                access: f.access || '',
                features: f.features || '',
                referral: f.referral || false,
                address: f.address || '',
                website: f.website || '',
            }))
        };
    }
    console.log(JSON.stringify(result));
    """
    result = subprocess.run(
        ["node", "-e", script],
        capture_output=True, text=True, cwd=str(BASE)
    )
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        return {}
    return json.loads(result.stdout)


# ページファイル名 → areaId のマッピング
PAGE_TO_AREA = {
    "odawara.html": ["odawara"],
    "hadano.html": ["hadano"],
    "hiratsuka.html": ["hiratsuka"],
    "fujisawa.html": ["fujisawa"],
    "chigasaki.html": ["chigasaki"],
    "oiso.html": ["oiso_ninomiya"],
    "ninomiya.html": ["oiso_ninomiya"],
    "minamiashigara.html": ["minamiashigara_kaisei_oi"],
    "kaisei.html": ["minamiashigara_kaisei_oi"],
    "matsuda.html": ["minamiashigara_kaisei_oi"],
    "yamakita.html": ["minamiashigara_kaisei_oi"],
    "hakone.html": ["odawara"],  # 箱根は小田原エリア
    "isehara.html": ["isehara"],
    "atsugi.html": ["atsugi"],
    "ebina.html": ["ebina"],
}


def generate_facility_table(facilities, area_name):
    """施設データからHTMLテーブルを生成"""
    if not facilities:
        return ""

    rows = []
    for f in facilities:
        referral_badge = '<span style="display:inline-block;background:#E8735A;color:#fff;font-size:0.7rem;font-weight:700;padding:1px 6px;border-radius:3px;margin-left:4px;">紹介可能</span>' if f.get("referral") else ""

        amb = f.get("ambulanceCount", 0)
        amb_text = f"年{amb:,}台" if amb > 0 else "—"

        rows.append(f"""                    <tr{"  style='background:rgba(232,115,90,0.06);'" if f.get('referral') else ""}>
                        <td><strong>{f['name']}</strong>{referral_badge}<br><small>{f.get('ownerType', '')}・{f['type']}</small></td>
                        <td>{f.get('nursingRatio', '—')}</td>
                        <td>{f.get('emergencyLevel', '—')}</td>
                        <td>{f.get('nurseCount', 0)}名</td>
                        <td>{f.get('beds', 0)}床</td>
                        <td>{amb_text}</td>
                    </tr>""")

    return f"""
            <div style="overflow-x:auto;">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>医療機関</th>
                        <th>看護配置</th>
                        <th>救急</th>
                        <th>看護師数</th>
                        <th>病床数</th>
                        <th>救急車/年</th>
                    </tr>
                </thead>
                <tbody>
{"".join(rows)}
                </tbody>
            </table>
            </div>
            <p style="font-size:0.8rem;color:#888;margin-top:8px;">データ出典：厚生労働省 病床機能報告（令和5年度）・医療情報ネット（2025年12月時点）</p>"""


def update_page(filepath, areas_data, area_ids):
    """1ページのHTMLを更新"""
    text = filepath.read_text(encoding="utf-8")

    # 対象エリアの施設を集める
    all_facilities = []
    for aid in area_ids:
        if aid in areas_data:
            all_facilities.extend(areas_data[aid]["majorFacilities"])

    if not all_facilities:
        print(f"  SKIP {filepath.name}: 施設データなし")
        return False

    area_name = areas_data[area_ids[0]]["name"] if area_ids[0] in areas_data else ""

    # 施設テーブルHTMLを生成
    table_html = generate_facility_table(all_facilities, area_name)

    # 「主な医療機関」セクションの直後にテーブルを挿入/更新
    # パターン: <h2>...主な医療機関...</h2> の後、次の</section>の前

    # 既存のテーブルがあれば置き換え
    marker_start = "<!-- FACILITY_TABLE_START -->"
    marker_end = "<!-- FACILITY_TABLE_END -->"

    if marker_start in text:
        # 既存テーブルを置き換え
        pattern = re.compile(
            re.escape(marker_start) + r'.*?' + re.escape(marker_end),
            re.DOTALL
        )
        new_block = f"{marker_start}\n{table_html}\n            {marker_end}"
        text = pattern.sub(new_block, text)
    else:
        # 「主な医療機関」セクションを探してテーブルを挿入
        # h2タグで「医療機関」を含むものを探す
        patterns_to_try = [
            r'(<h2[^>]*>.*?医療機関.*?</h2>)',
            r'(<h2[^>]*>.*?病院.*?</h2>)',
        ]

        inserted = False
        for pat in patterns_to_try:
            m = re.search(pat, text, re.DOTALL)
            if m:
                # h2の直後にテーブルを挿入
                insert_pos = m.end()
                # 既存の<p>タグの直後を探す（説明文の後に挿入）
                next_p = text.find("</p>", insert_pos)
                if next_p != -1 and next_p - insert_pos < 500:
                    insert_pos = next_p + len("</p>")

                new_block = f"\n\n            {marker_start}\n{table_html}\n            {marker_end}\n"
                text = text[:insert_pos] + new_block + text[insert_pos:]
                inserted = True
                break

        if not inserted:
            # フォールバック: 最初の</section>の前に挿入
            first_section_end = text.find("</section>", text.find("<section>", text.find("</header>")))
            if first_section_end != -1:
                new_block = f"\n            {marker_start}\n{table_html}\n            {marker_end}\n        </div>\n    "
                text = text[:first_section_end] + new_block + text[first_section_end:]
                inserted = True

        if not inserted:
            print(f"  WARN {filepath.name}: 挿入位置が見つからない")
            return False

    # 施設数の更新: facilityCountを使って記述を更新
    fc = areas_data[area_ids[0]].get("facilityCount", {}) if area_ids[0] in areas_data else {}
    h_count = fc.get("hospitals", 0)
    c_count = fc.get("clinics", 0)

    filepath.write_text(text, encoding="utf-8")
    print(f"  OK {filepath.name}: {len(all_facilities)}施設のテーブル挿入")
    return True


def main():
    print("エリアページ更新開始...")
    areas_data = load_areas_data()
    if not areas_data:
        print("ERROR: areas.jsの読み込みに失敗")
        return

    print(f"areas.jsから{len(areas_data)}エリア読み込み完了")

    updated = 0
    for page_name, area_ids in PAGE_TO_AREA.items():
        filepath = AREA_DIR / page_name
        if not filepath.exists():
            print(f"  SKIP {page_name}: ファイルなし")
            continue

        if update_page(filepath, areas_data, area_ids):
            updated += 1

    print(f"\n✅ {updated}ページ更新完了")


if __name__ == "__main__":
    main()
