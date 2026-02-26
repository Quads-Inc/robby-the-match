#!/usr/bin/env python3
"""
extract_kanagawa_data.py
========================
神奈川県の病院データを国の公開CSVから抽出し、
既存のenriched/ward JSONと突合するスクリプト。

データソース:
  - 医療情報ネット 2025年12月 病院施設情報CSV (7640行)
  - kanagawa_hospitals_enriched.json (67病院)
  - kanagawa_ward_data.json (67病院 病棟別)

出力:
  - data/public_data/kanagawa_csv_extract.json  (全神奈川県病院)
  - data/public_data/kanagawa_west_hospitals.json (神奈川県西部のみ)
  - 標準出力にサマリレポート
"""

from __future__ import annotations

import csv
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional, Tuple

# --- パス設定 ---
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "public_data"
CSV_PATH = DATA_DIR / "hospital_facility" / "01-1_hospital_facility_info_20251201.csv"
ENRICHED_PATH = DATA_DIR / "kanagawa_hospitals_enriched.json"
WARD_PATH = DATA_DIR / "kanagawa_ward_data.json"
OUTPUT_ALL_PATH = DATA_DIR / "kanagawa_csv_extract.json"
OUTPUT_WEST_PATH = DATA_DIR / "kanagawa_west_hospitals.json"

# --- 神奈川県西部の市町村 ---
WEST_CITIES = [
    "小田原市", "秦野市", "平塚市", "藤沢市", "茅ヶ崎市",
    "南足柄市", "伊勢原市",
    "大磯町", "二宮町", "中井町", "大井町", "松田町",
    "山北町", "開成町", "箱根町", "真鶴町", "湯河原町",
]

# 神奈川県の都道府県コード
KANAGAWA_CODE = "14"


def parse_int(val: str) -> int | None:
    """数値文字列を int に変換。空文字は None。"""
    val = val.strip()
    if not val:
        return None
    try:
        return int(val)
    except ValueError:
        return None


def parse_float(val: str) -> float | None:
    """数値文字列を float に変換。空文字や0.0は None。"""
    val = val.strip()
    if not val:
        return None
    try:
        f = float(val)
        return f if f != 0.0 else None
    except ValueError:
        return None


def extract_city(address: str) -> str | None:
    """住所文字列から市区町村名を抽出する。
    郡名を含む町村名（例: 足柄下郡箱根町）は町村名のみ（箱根町）に正規化する。
    """
    # 神奈川県を除去
    addr = address.replace("神奈川県", "")
    # 政令指定都市の区
    m = re.match(r"(横浜市\S+区|川崎市\S+区|相模原市\S+区)", addr)
    if m:
        return m.group(1)
    # 郡+町村パターン（例: 足柄下郡箱根町 -> 箱根町, 中郡大磯町 -> 大磯町）
    m = re.match(r"\S+郡(\S+?[町村])", addr)
    if m:
        return m.group(1)
    # 一般の市
    m = re.match(r"(\S+?市)", addr)
    if m:
        return m.group(1)
    return None


def extract_city_base(address: str) -> str | None:
    """住所文字列から基本市町村名(区なし)を抽出する。"""
    addr = address.replace("神奈川県", "")
    # 政令指定都市
    m = re.match(r"((横浜|川崎|相模原)市)", addr)
    if m:
        return m.group(1)
    # 郡+町村
    m = re.match(r"\S+郡(\S+?[町村])", addr)
    if m:
        return m.group(1)
    # 一般の市
    m = re.match(r"(\S+?市)", addr)
    if m:
        return m.group(1)
    return None


def load_csv() -> list[dict]:
    """CSVを読み込み、神奈川県の病院を辞書リストとして返す。"""
    hospitals = []

    # エンコーディングを試す
    for enc in ["utf-8-sig", "utf-8", "cp932", "shift_jis"]:
        try:
            with open(CSV_PATH, "r", encoding=enc) as f:
                reader = csv.reader(f)
                headers = next(reader)
                # BOM付きUTF-8のヘッダー修正
                headers[0] = headers[0].lstrip("\ufeff").strip('"')

                for row in reader:
                    if len(row) < 65:
                        continue
                    if row[7].strip() != KANAGAWA_CODE:
                        continue

                    city = extract_city(row[9])
                    city_base = extract_city_base(row[9])

                    hospital = {
                        "id": row[0].strip(),
                        "name": row[1].strip(),
                        "name_kana": row[2].strip(),
                        "short_name": row[3].strip(),
                        "english_name": row[5].strip(),
                        "facility_type": row[6].strip(),
                        "prefecture_code": row[7].strip(),
                        "city_code": row[8].strip(),
                        "address": row[9].strip(),
                        "latitude": parse_float(row[10]),
                        "longitude": parse_float(row[11]),
                        "website": row[12].strip() if row[12].strip() else None,
                        "city": city,
                        "city_base": city_base,
                        "is_west": city in WEST_CITIES if city else False,
                        "beds_general": parse_int(row[57]),
                        "beds_therapy": parse_int(row[58]),
                        "beds_therapy_medical": parse_int(row[59]),
                        "beds_therapy_care": parse_int(row[60]),
                        "beds_mental": parse_int(row[61]),
                        "beds_tb": parse_int(row[62]),
                        "beds_infectious": parse_int(row[63]),
                        "beds_total": parse_int(row[64]),
                        "closed_saturday": row[18].strip() == "0",
                        "closed_sunday": row[19].strip() == "0",
                        "holiday_closed": row[55].strip() == "0",
                    }
                    hospitals.append(hospital)
                break  # 成功したらループを抜ける
        except (UnicodeDecodeError, UnicodeError):
            continue

    if not hospitals:
        print("ERROR: CSVの読み込みに失敗しました。エンコーディングを確認してください。", file=sys.stderr)
        sys.exit(1)

    return hospitals


def load_enriched() -> dict:
    """kanagawa_hospitals_enriched.json を name -> dict の辞書で返す。"""
    with open(ENRICHED_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {h["name"]: h for h in data}


def load_ward_data() -> dict:
    """kanagawa_ward_data.json をそのまま返す (name -> dict)。"""
    with open(WARD_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_name(name: str) -> str:
    """病院名の正規化（比較用）。"""
    # 全角英数を半角に
    name = name.translate(str.maketrans(
        "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ０１２３４５６７８９",
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    ))
    # 法人格を除去
    for prefix in ["医療法人社団", "医療法人財団", "医療法人", "社会福祉法人",
                    "社会医療法人", "公益社団法人", "独立行政法人", "国立研究開発法人",
                    "地方独立行政法人", "学校法人", "国家公務員共済組合連合会",
                    "特定医療法人", "一般社団法人", "一般財団法人", "公益財団法人"]:
        name = name.replace(prefix, "")
    # 法人名パターン除去（「XX会」など）
    name = re.sub(r"[\s　]+", "", name)
    # さらにスペース除去
    name = name.strip()
    return name


def find_match(csv_name: str, enriched_names: dict, ward_names: dict) -> tuple[str | None, str | None]:
    """CSV病院名がenriched/wardデータにマッチするか検索する。"""
    norm_csv = normalize_name(csv_name)

    # 1. 完全一致
    if csv_name in enriched_names:
        return csv_name, "enriched_exact"
    if csv_name in ward_names:
        return csv_name, "ward_exact"

    # 2. 正規化後の一致
    for en_name in enriched_names:
        if normalize_name(en_name) == norm_csv:
            return en_name, "enriched_normalized"
    for wn_name in ward_names:
        if normalize_name(wn_name) == norm_csv:
            return wn_name, "ward_normalized"

    # 3. 部分一致（CSV名がenriched名に含まれる or その逆）
    for en_name in enriched_names:
        norm_en = normalize_name(en_name)
        if norm_csv in norm_en or norm_en in norm_csv:
            return en_name, "enriched_partial"
    for wn_name in ward_names:
        norm_wn = normalize_name(wn_name)
        if norm_csv in norm_wn or norm_wn in norm_csv:
            return wn_name, "ward_partial"

    return None, None


def main():
    print("=" * 70)
    print("神奈川県 病院データ抽出・突合レポート")
    print("=" * 70)

    # --- データ読み込み ---
    print("\n[1] CSVデータ読み込み中...")
    csv_hospitals = load_csv()
    print(f"    神奈川県の病院数（CSV）: {len(csv_hospitals)}")

    print("\n[2] Enrichedデータ読み込み中...")
    enriched = load_enriched()
    print(f"    Enriched病院数: {len(enriched)}")

    print("\n[3] 病棟データ読み込み中...")
    ward_data = load_ward_data()
    print(f"    病棟データ病院数: {len(ward_data)}")

    # --- 神奈川県西部のフィルタリング ---
    west_hospitals = [h for h in csv_hospitals if h["is_west"]]
    print(f"\n[4] 神奈川県西部の病院数（CSV）: {len(west_hospitals)}")

    # 市町村別内訳
    city_counts = {}
    for h in west_hospitals:
        city = h["city"] or "不明"
        city_counts[city] = city_counts.get(city, 0) + 1

    print("\n    【市町村別内訳】")
    for city in WEST_CITIES:
        count = city_counts.get(city, 0)
        if count > 0:
            print(f"    {city:10s}: {count:3d} 病院")
    unknown = city_counts.get("不明", 0)
    if unknown:
        print(f"    {'不明':10s}: {unknown:3d} 病院")

    # --- 突合分析 ---
    print("\n" + "=" * 70)
    print("[5] CSV vs Enrichedデータ 突合分析")
    print("=" * 70)

    matched_enriched = set()
    matched_ward = set()
    unmatched_csv = []

    for h in west_hospitals:
        match_name, match_type = find_match(h["name"], enriched, ward_data)
        if match_name:
            h["enriched_match"] = match_name
            h["match_type"] = match_type
            if "enriched" in match_type:
                matched_enriched.add(match_name)
            if "ward" in match_type:
                matched_ward.add(match_name)
        else:
            h["enriched_match"] = None
            h["match_type"] = None
            unmatched_csv.append(h)

    print(f"\n    西部病院のうちEnriched/Wardにマッチ: {len(west_hospitals) - len(unmatched_csv)}")
    print(f"    西部病院のうちマッチしない: {len(unmatched_csv)}")

    if unmatched_csv:
        print("\n    【CSVにあるがEnriched/Wardにない西部病院】")
        for h in unmatched_csv:
            beds = h["beds_total"] or 0
            print(f"    - {h['name']} ({h['city']}, {beds}床)")

    # Enriched/WardにあってCSVにない病院も確認
    csv_west_names_norm = {normalize_name(h["name"]) for h in west_hospitals}

    enriched_not_in_csv = []
    for name, data in enriched.items():
        city = data.get("cityName", "")
        if city in WEST_CITIES:
            if normalize_name(name) not in csv_west_names_norm:
                # 部分一致もチェック
                found = False
                for csv_norm in csv_west_names_norm:
                    if csv_norm in normalize_name(name) or normalize_name(name) in csv_norm:
                        found = True
                        break
                if not found:
                    enriched_not_in_csv.append((name, city))

    if enriched_not_in_csv:
        print("\n    【Enrichedにあるが、CSVの西部データに見つからない病院】")
        for name, city in enriched_not_in_csv:
            print(f"    - {name} ({city})")

    # --- 全神奈川県 市区町村別集計 ---
    print("\n" + "=" * 70)
    print("[6] 全神奈川県 市区町村別病院数")
    print("=" * 70)

    all_city_counts = {}
    for h in csv_hospitals:
        cb = h["city_base"] or h["city"] or "不明"
        all_city_counts[cb] = all_city_counts.get(cb, 0) + 1

    for city, count in sorted(all_city_counts.items(), key=lambda x: -x[1]):
        west_mark = " ★西部" if city in WEST_CITIES else ""
        print(f"    {city:15s}: {count:3d} 病院{west_mark}")

    # --- 小林病院の検索 ---
    print("\n" + "=" * 70)
    print("[7] 小林病院（小田原市）の検索")
    print("=" * 70)

    kobayashi_csv = [h for h in csv_hospitals if "小林" in h["name"] and h.get("city") == "小田原市"]
    if kobayashi_csv:
        for h in kobayashi_csv:
            print(f"\n    【CSV データ】")
            for k, v in h.items():
                print(f"    {k}: {v}")
    else:
        # 小林を名前に含む病院を全県で検索
        kobayashi_all = [h for h in csv_hospitals if "小林" in h["name"]]
        if kobayashi_all:
            print(f"\n    小田原市では見つかりませんでした。")
            print(f"    「小林」を含む神奈川県内の病院:")
            for h in kobayashi_all:
                print(f"    - {h['name']} ({h['city']}, {h['beds_total']}床)")
        else:
            print("\n    「小林」を含む病院は神奈川県内のCSVに見つかりませんでした。")

    # Enriched/Wardでも検索
    kobayashi_enriched = {k: v for k, v in enriched.items() if "小林" in k}
    if kobayashi_enriched:
        print(f"\n    【Enriched データ】")
        for name, data in kobayashi_enriched.items():
            print(f"    病院名: {name}")
            for k, v in data.items():
                print(f"      {k}: {v}")

    kobayashi_ward = {k: v for k, v in ward_data.items() if "小林" in k}
    if kobayashi_ward:
        print(f"\n    【Ward データ】")
        for name, data in kobayashi_ward.items():
            print(f"    病院名: {name}")
            for k, v in data.items():
                print(f"      {k}: {v}")

    # --- 病床規模別分析（西部） ---
    print("\n" + "=" * 70)
    print("[8] 神奈川県西部 病床規模別分析")
    print("=" * 70)

    size_buckets = {"大規模(300床以上)": [], "中規模(100-299床)": [], "小規模(20-99床)": [], "極小(20床未満/不明)": []}
    for h in west_hospitals:
        beds = h["beds_total"] or 0
        if beds >= 300:
            size_buckets["大規模(300床以上)"].append(h)
        elif beds >= 100:
            size_buckets["中規模(100-299床)"].append(h)
        elif beds >= 20:
            size_buckets["小規模(20-99床)"].append(h)
        else:
            size_buckets["極小(20床未満/不明)"].append(h)

    for bucket, hospitals in size_buckets.items():
        print(f"\n    {bucket}: {len(hospitals)} 病院")
        for h in sorted(hospitals, key=lambda x: -(x["beds_total"] or 0)):
            beds = h["beds_total"] or 0
            matched = "  [enriched]" if h.get("enriched_match") else ""
            print(f"      {h['name'][:30]:30s} | {h['city']:8s} | {beds:4d}床{matched}")

    # --- JSON出力 ---
    print("\n" + "=" * 70)
    print("[9] JSON出力")
    print("=" * 70)

    # 全神奈川県
    with open(OUTPUT_ALL_PATH, "w", encoding="utf-8") as f:
        json.dump(csv_hospitals, f, ensure_ascii=False, indent=2)
    print(f"    全神奈川県: {OUTPUT_ALL_PATH} ({len(csv_hospitals)} 病院)")

    # 西部のみ
    with open(OUTPUT_WEST_PATH, "w", encoding="utf-8") as f:
        json.dump(west_hospitals, f, ensure_ascii=False, indent=2)
    print(f"    西部のみ:   {OUTPUT_WEST_PATH} ({len(west_hospitals)} 病院)")

    # --- サマリ ---
    total_beds_west = sum(h["beds_total"] or 0 for h in west_hospitals)
    print("\n" + "=" * 70)
    print("サマリ")
    print("=" * 70)
    print(f"    全国病院数（CSV全体）:          7,640")
    print(f"    神奈川県病院数（CSV）:          {len(csv_hospitals)}")
    print(f"    神奈川県西部病院数（CSV）:      {len(west_hospitals)}")
    print(f"    神奈川県西部 合計病床数:        {total_beds_west:,}")
    print(f"    Enriched データの病院数:        {len(enriched)}")
    print(f"    Ward データの病院数:            {len(ward_data)}")
    print(f"    西部でCSVのみ（未登録）の病院:  {len(unmatched_csv)}")
    print(f"    西部の市町村数（データあり）:    {len([c for c in WEST_CITIES if city_counts.get(c, 0) > 0])}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
