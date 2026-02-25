#!/usr/bin/env python3
"""
病棟票Excelから神奈川県対象エリアの全病院の病棟データを集約するスクリプト。

入力: data/public_data/bed_function_ward_kanto.xlsx
出力: data/public_data/kanagawa_ward_data.json
"""

import json
import re
import unicodedata
from collections import OrderedDict
from pathlib import Path

import openpyxl

# ── 設定 ──────────────────────────────────────────────
INPUT_FILE = Path(__file__).resolve().parent.parent / "data" / "public_data" / "bed_function_ward_kanto.xlsx"
OUTPUT_FILE = Path(__file__).resolve().parent.parent / "data" / "public_data" / "kanagawa_ward_data.json"
SHEET_NAME = "報告様式１病棟票"
HEADER_ROWS = 6  # 行0-5がヘッダー、データは行6(0-indexed)以降

PREF_CODE_KANAGAWA = "14"

TARGET_CITIES = {
    "小田原市", "平塚市", "秦野市", "伊勢原市", "南足柄市",
    "藤沢市", "茅ヶ崎市", "厚木市", "海老名市",
    "大磯町", "二宮町", "開成町", "松田町", "山北町",
    "箱根町", "中井町", "大井町", "寒川町",
}

# ── 看護配置基準の判定ルール ────────────────────────────
# (パターン, ラベル, 優先度) — 優先度が小さいほど高配置
# NOTE: パターンはNFKC正規化後の文字列に対してマッチするため半角数字を使用
NURSING_RATIO_RULES = [
    (r"急性期一般入院料1$",                        "7:1",         10),
    (r"急性期一般入院料[234]",                      "10:1",        20),
    (r"急性期一般入院料[56]",                       "13:1",        30),
    (r"地域一般入院料",                             "15:1",        40),
    (r"回復期.?リハビリテーション病棟入院料1$",      "回復期13:1",  25),
    (r"回復期.?リハビリテーション病棟入院料[2-9]",   "回復期15:1",  35),
    (r"地域包括ケア病棟入院料",                     "地域包括ケア", 28),
    (r"療養病棟入院料",                             "療養20:1",    50),
    (r"障害者施設等",                               "障害者7:1",   12),
]


def zen_to_han(s: str) -> str:
    """全角数字を半角に変換する。"""
    if not isinstance(s, str):
        return s
    return unicodedata.normalize("NFKC", s)


def safe_float(v) -> float:
    """値を安全にfloatに変換する。"""
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = zen_to_han(str(v)).strip()
    if s in ("", "-", "−", "―"):
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def safe_int(v) -> int:
    """値を安全にintに変換する。"""
    return int(safe_float(v))


def determine_nursing_ratio(admission_fees: list[str]) -> str:
    """入院基本料リストから最上位の看護配置基準を判定する。"""
    best_label = None
    best_priority = 9999

    for fee in admission_fees:
        if not fee or fee in ("-", "−", "―"):
            continue
        fee_normalized = zen_to_han(fee)
        for pattern, label, priority in NURSING_RATIO_RULES:
            if re.search(pattern, fee_normalized):
                if priority < best_priority:
                    best_priority = priority
                    best_label = label
                break  # 一つの入院料に対して最初にマッチしたルールを適用

    return best_label or "不明"


def is_closed_ward(function_str: str) -> bool:
    """休棟中かどうかを判定する。"""
    if not function_str:
        return False
    return "休棟" in str(function_str)


def main():
    print(f"入力ファイル: {INPUT_FILE}")
    wb = openpyxl.load_workbook(str(INPUT_FILE), read_only=True, data_only=True)
    ws = wb[SHEET_NAME]

    # データ読み込み（ヘッダー行をスキップ）
    facilities = {}  # medicalCode -> facility dict

    row_count = 0
    skip_count = 0
    for i, row in enumerate(ws.iter_rows(min_row=HEADER_ROWS + 1, values_only=True)):
        vals = list(row)

        # 都道府県コードチェック
        pref_code = str(vals[2]).strip() if vals[2] is not None else ""
        if pref_code != PREF_CODE_KANAGAWA:
            continue

        # 市区町村チェック
        city_name = str(vals[8]).strip() if vals[8] is not None else ""
        if city_name not in TARGET_CITIES:
            skip_count += 1
            continue

        row_count += 1

        medical_code = str(vals[0]).strip() if vals[0] else ""
        facility_name = str(vals[1]).strip() if vals[1] else ""
        ward_name = str(vals[12]).strip() if vals[12] else ""
        function_str = str(vals[15]).strip() if vals[15] else ""
        admission_fee = str(vals[32]).strip() if vals[32] else ""
        beds = safe_int(vals[33])
        nurses_ft = safe_float(vals[39])
        nurses_pt = safe_float(vals[40])

        # 入院基本料が"-"の場合はクリーンアップ
        if admission_fee in ("-", "−", "―"):
            admission_fee = "-"

        ward_data = {
            "name": ward_name,
            "function": function_str,
            "admissionFee": admission_fee,
            "beds": beds,
            "nursesFT": nurses_ft,
            "nursesPT": nurses_pt,
        }

        if medical_code not in facilities:
            facilities[medical_code] = {
                "medicalCode": medical_code,
                "name": facility_name,
                "cityName": city_name,
                "wards": [],
            }

        facilities[medical_code]["wards"].append(ward_data)

    wb.close()

    print(f"対象行数: {row_count}")
    print(f"神奈川県だが対象外市区町村: {skip_count}")

    # 集約処理
    result = OrderedDict()
    for code, fac in sorted(facilities.items(), key=lambda x: x[1]["cityName"]):
        wards = fac["wards"]

        # admission fees（休棟中除く、"-"除く）
        admission_fees = []
        for w in wards:
            if w["admissionFee"] and w["admissionFee"] != "-" and not is_closed_ward(w["function"]):
                if w["admissionFee"] not in admission_fees:
                    admission_fees.append(w["admissionFee"])

        # 看護配置基準
        nursing_ratio = determine_nursing_ratio(admission_fees)

        # 看護師合計（全病棟）— 浮動小数点誤差を丸める
        total_ward_nurses = round(sum(w["nursesFT"] + w["nursesPT"] for w in wards), 1)

        # 病棟数（休棟中を除く）
        ward_count = sum(1 for w in wards if not is_closed_ward(w["function"]))

        # 医療機能リスト（休棟中を除く、ユニーク）
        functions = []
        for w in wards:
            if not is_closed_ward(w["function"]):
                # 機能名を正規化（括弧内の補足を除去）
                func = w["function"].split("（")[0].strip()
                if func and func not in functions:
                    functions.append(func)

        # 施設名の短縮キー（法人形態を除去して短い名前にする）
        short_name = fac["name"]
        # 法人形態を除去して簡潔なキーに
        for prefix in ["医療法人社団", "医療法人財団", "医療法人", "社会医療法人",
                       "独立行政法人国立病院機構", "独立行政法人", "社会福祉法人",
                       "地方独立行政法人", "公益財団法人", "一般財団法人",
                       "一般社団法人", "学校法人"]:
            short_name = short_name.replace(prefix, "")
        # さらにクリーンアップ
        short_name = re.sub(r"^[\s　]+", "", short_name)
        short_name = re.sub(r"[\s　]+$", "", short_name)
        # 法人名（〜会 等）を除去
        short_name = re.sub(r"^[^\s　]*[会][\s　]+", "", short_name)
        short_name = short_name.strip()
        if not short_name:
            short_name = fac["name"]

        # nursesFT, nursesPT を適切に出力（整数なら整数、小数なら小数）
        clean_wards = []
        for w in wards:
            cw = {
                "name": w["name"],
                "function": w["function"],
                "admissionFee": w["admissionFee"],
                "beds": w["beds"],
                "nursesFT": w["nursesFT"] if w["nursesFT"] != int(w["nursesFT"]) else int(w["nursesFT"]),
                "nursesPT": w["nursesPT"] if w["nursesPT"] != int(w["nursesPT"]) else int(w["nursesPT"]),
            }
            clean_wards.append(cw)

        total_nurses_clean = total_ward_nurses if total_ward_nurses != int(total_ward_nurses) else int(total_ward_nurses)

        result[short_name] = {
            "medicalCode": fac["medicalCode"],
            "name": fac["name"],
            "cityName": fac["cityName"],
            "nursingRatio": nursing_ratio,
            "admissionFees": admission_fees,
            "totalWardNurses": total_nurses_clean,
            "wardCount": ward_count,
            "functions": functions,
            "wards": clean_wards,
        }

    # JSON出力
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n出力ファイル: {OUTPUT_FILE}")
    print(f"対象施設数: {len(result)}")

    # 市区町村別の施設数
    city_counts = {}
    for fac in result.values():
        city = fac["cityName"]
        city_counts[city] = city_counts.get(city, 0) + 1

    print("\n--- 市区町村別施設数 ---")
    for city in sorted(city_counts.keys()):
        print(f"  {city}: {city_counts[city]}")

    # 小田原市の全施設サマリ
    print("\n--- 小田原市の全施設サマリ ---")
    for name, fac in result.items():
        if fac["cityName"] == "小田原市":
            print(f"\n  {name}")
            print(f"    正式名称: {fac['name']}")
            print(f"    医療機関コード: {fac['medicalCode']}")
            print(f"    看護配置: {fac['nursingRatio']}")
            print(f"    入院基本料: {', '.join(fac['admissionFees']) if fac['admissionFees'] else 'なし'}")
            print(f"    看護師合計: {fac['totalWardNurses']}")
            print(f"    病棟数: {fac['wardCount']}（休棟含む全体: {len(fac['wards'])}）")
            print(f"    医療機能: {', '.join(fac['functions'])}")
            for w in fac["wards"]:
                closed = " [休棟中]" if is_closed_ward(w["function"]) else ""
                print(f"      - {w['name']}: {w['function']}{closed} | {w['admissionFee']} | {w['beds']}床 | 常勤{w['nursesFT']} 非常勤{w['nursesPT']}")


if __name__ == "__main__":
    main()
