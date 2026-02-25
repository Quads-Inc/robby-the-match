#!/usr/bin/env python3
"""
施設データ統合スクリプト
- kanagawa_hospitals_enriched.json（施設票+医療情報ネット）
- kanagawa_ward_data.json（病棟票）
- 既存 areas.js の施設データ
を統合し、更新済み areas.js を生成する。

Usage: python3 scripts/merge_and_update_areas.py
"""

import json
import re
import unicodedata
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA_DIR = BASE / "data" / "public_data"
AREAS_JS = BASE / "data" / "areas.js"
OUTPUT_JS = BASE / "data" / "areas.js"  # 上書き

# ==========================================
# 1. データ読み込み
# ==========================================

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_areas_js():
    """areas.js をパースして AREA_DATABASE 部分を抽出"""
    text = AREAS_JS.read_text(encoding="utf-8")
    return text

enriched = load_json(DATA_DIR / "kanagawa_hospitals_enriched.json")  # list
ward_data = load_json(DATA_DIR / "kanagawa_ward_data.json")  # dict keyed by name

# medicalCode→ward_data のルックアップを作成
ward_by_code = {}
for name, wd in ward_data.items():
    code = wd.get("medicalCode", "")
    if code:
        ward_by_code[code] = wd

# ==========================================
# 2. enriched + ward_data を medicalCode で結合
# ==========================================

merged = {}  # medicalCode → combined dict
for h in enriched:
    code = h["medicalCode"]
    combined = dict(h)
    wd = ward_by_code.get(code)
    if wd:
        combined["nursingRatio"] = wd.get("nursingRatio", "不明")
        combined["admissionFees"] = wd.get("admissionFees", [])
        combined["totalWardNurses"] = wd.get("totalWardNurses", 0)
        combined["wardCount_ward"] = wd.get("wardCount", 0)
        combined["functions_ward"] = wd.get("functions", [])
        combined["wards"] = wd.get("wards", [])
    else:
        combined["nursingRatio"] = "不明"
        combined["admissionFees"] = []
        combined["totalWardNurses"] = 0
        combined["wardCount_ward"] = 0
        combined["functions_ward"] = []
        combined["wards"] = []
    merged[code] = combined

print(f"統合済み施設数: {len(merged)}")

# ==========================================
# 3. 既存 areas.js の施設と名寄せ
# ==========================================

def normalize(s):
    """名前正規化: 全角→半角、カ/ケ/ヶ統一"""
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("ヶ", "ケ").replace("ヵ", "カ")
    s = re.sub(r'\s+', '', s)
    return s

def core_name(s):
    """法人格等を取り除いたコア名"""
    s = re.sub(r'(医療法人|社団|財団|一般社団法人|公益社団法人|独立行政法人|国立病院機構|社会福祉法人|学校法人|神奈川県厚生農業協同組合連合会)\s*', '', s)
    s = re.sub(r'[（）()]\s*', '', s)
    s = re.sub(r'\s+', '', s)
    return normalize(s)

# merged の名前ルックアップ
name_to_code = {}
for code, h in merged.items():
    n1 = normalize(h["name"])
    n2 = normalize(h.get("fullName", ""))
    name_to_code[n1] = code
    if n2:
        name_to_code[n2] = code
    # コア名でも
    cn1 = core_name(h["name"])
    cn2 = core_name(h.get("fullName", ""))
    if cn1 not in name_to_code:
        name_to_code[cn1] = code
    if cn2 and cn2 not in name_to_code:
        name_to_code[cn2] = code

def find_match(facility_name, full_name=None):
    """既存施設名 → merged の medicalCode"""
    candidates = [facility_name]
    if full_name:
        candidates.append(full_name)

    for name in candidates:
        n = normalize(name)
        if n in name_to_code:
            return name_to_code[n]
        cn = core_name(name)
        if cn in name_to_code:
            return name_to_code[cn]

    # 部分一致
    for name in candidates:
        n = normalize(name)
        for key, code in name_to_code.items():
            if len(n) >= 3 and (n in key or key in n):
                return code

    return None


# ==========================================
# 4. 看護配置→入院基本料の逆マッピング
# ==========================================

def derive_nursing_ratio(admission_fees, nursing_ratio_from_ward):
    """入院基本料から看護配置を推定"""
    if nursing_ratio_from_ward and nursing_ratio_from_ward != "不明":
        return nursing_ratio_from_ward

    if not admission_fees:
        return "不明"

    for fee in admission_fees:
        fee_n = unicodedata.normalize("NFKC", fee)
        if "7対1" in fee_n or "7:1" in fee_n:
            return "7:1"
        if re.search(r'急性期一般入院料[1１]$', fee_n):
            return "7:1"
        if re.search(r'急性期一般入院料[2-4２-４]', fee_n):
            return "10:1"
        if re.search(r'急性期一般入院料[5-6５-６]', fee_n):
            return "13:1"
        if "地域一般入院料" in fee_n:
            return "15:1"
        if "特定機能病院" in fee_n and "7対1" in fee_n:
            return "7:1"
        if "特定集中治療室" in fee_n or "救命救急入院料" in fee_n:
            return "ICU相当"

    return "不明"


# ==========================================
# 5. 施設タイプ文字列の生成
# ==========================================

def build_type_string(functions):
    """functions配列 → type文字列"""
    if not functions:
        return "不明"
    order = ["高度急性期", "急性期", "回復期", "慢性期"]
    seen = []
    for o in order:
        if o in functions:
            seen.append(o)
    for f in functions:
        if f not in seen:
            seen.append(f)
    return "・".join(seen) if seen else "不明"


# ==========================================
# 6. matchingTags の自動生成
# ==========================================

def build_matching_tags(h):
    """公開データからmatchingTagsを自動生成"""
    tags = []

    # 医療機能
    for f in h.get("functions_ward", []) or h.get("functions", []):
        if f and f not in tags:
            tags.append(f)

    # 救急
    el = h.get("emergencyLevel", "")
    if "三次" in el:
        tags.extend(["三次救急", "救命救急"])
    elif "二次" in el:
        tags.append("二次救急")

    # 開設者
    ot = h.get("ownerType", "")
    if ot == "公立":
        tags.append("公立病院")
    elif ot == "公的":
        tags.append("公的病院")
    elif ot == "国立":
        tags.append("国立病院")
    elif ot == "大学":
        tags.append("大学病院")

    # DPC
    dpc = h.get("dpcGroup", "")
    if "特定" in dpc:
        tags.append("DPC特定病院群")
    elif "標準" in dpc:
        tags.append("DPC標準病院群")

    # 退院支援
    if h.get("hasDischargeUnit"):
        tags.append("退院支援充実")

    # 看護配置
    nr = h.get("nursingRatio", "")
    if nr == "7:1":
        tags.append("7対1看護")

    # 規模感
    beds = h.get("totalBeds", 0)
    if beds >= 400:
        tags.append("大規模病院")
    elif beds >= 200:
        tags.append("中規模病院")

    # 特殊病棟
    for ward in h.get("wards", []):
        wn = ward.get("name", "")
        if "ICU" in wn or "集中治療" in wn:
            if "ICU" not in tags:
                tags.append("ICU")
        if "NICU" in wn or "新生児" in wn:
            if "NICU" not in tags:
                tags.append("NICU")
        if "HCU" in wn:
            if "HCU" not in tags:
                tags.append("HCU")
        if "SCU" in wn:
            if "SCU" not in tags:
                tags.append("SCU")
        if "回復期" in ward.get("function", ""):
            if "回復期リハビリ" not in tags:
                tags.append("回復期リハビリ")
        if "緩和ケア" in wn:
            if "緩和ケア" not in tags:
                tags.append("緩和ケア")

    # リハビリスタッフ
    pt = h.get("ptCount", 0) or 0
    ot_count = h.get("otCount", 0) or 0
    st = h.get("stCount", 0) or 0
    if pt + ot_count + st >= 20:
        tags.append("リハビリ充実")

    return tags


# ==========================================
# 7. features 文字列の自動生成
# ==========================================

def build_features(h, existing_features=None):
    """公開データからfeatures文字列を生成。既存があればマージ"""
    parts = []

    # 開設者+規模
    ot = h.get("ownerType", "")
    beds = h.get("totalBeds", 0)
    if ot:
        parts.append(f"{ot}")

    # 看護配置
    nr = h.get("nursingRatio", "不明")
    if nr != "不明":
        parts.append(f"看護配置{nr}")

    # 救急
    el = h.get("emergencyLevel", "")
    if el and el != "なし":
        parts.append(el)

    # 救急車
    amb = h.get("ambulanceCount", 0) or 0
    if amb > 0:
        parts.append(f"年間救急車{amb:,}台")

    # DPC
    dpc = h.get("dpcGroup", "")
    if "特定" in dpc:
        parts.append("DPC特定病院群")
    elif "標準" in dpc:
        parts.append("DPC標準病院群")

    # スタッフ数
    nc = h.get("nurseCount", 0) or 0
    dc = h.get("doctorCount", 0) or 0
    pt = h.get("ptCount", 0) or 0
    if nc > 0:
        parts.append(f"看護師{nc}名")
    if dc > 0:
        parts.append(f"医師{dc}名")
    if pt > 0:
        parts.append(f"PT{pt}名")

    # 設備
    ct = h.get("ctCount", 0) or 0
    mri = h.get("mriCount", 0) or 0
    equip = []
    if ct > 0:
        equip.append(f"CT{ct}台")
    if mri > 0:
        equip.append(f"MRI{mri}台")
    if equip:
        parts.append("・".join(equip))

    # 特殊病棟
    special = []
    for ward in h.get("wards", []):
        wn = ward.get("name", "")
        for kw in ["ICU", "NICU", "HCU", "SCU", "CCU"]:
            if kw in wn and kw not in special:
                special.append(kw)
        if "緩和ケア" in wn and "緩和ケア" not in special:
            special.append("緩和ケア")
    if special:
        parts.append("・".join(special) + "完備")

    # 退院支援
    if h.get("hasDischargeUnit"):
        parts.append("退院支援部門あり")

    generated = "。".join(parts) + "。" if parts else ""

    # 既存featuresがあれば、独自情報を抽出してマージ
    if existing_features:
        # 既存から、公開データで得られない独自情報を抽出
        unique_parts = []
        existing_lower = existing_features
        # 公開データにない情報（歴史、移転、特色等）を保持
        for sentence in re.split(r'[。、]', existing_features):
            sentence = sentence.strip()
            if not sentence:
                continue
            # 公開データで更新される情報はスキップ
            skip_patterns = [
                r'看護師\d+名', r'医師\d+名', r'PT\d+名',
                r'\d+床', r'救急車', r'ICU', r'NICU', r'HCU',
                r'救命救急', r'DPC', r'退院支援',
            ]
            skip = False
            for p in skip_patterns:
                if re.search(p, sentence):
                    skip = True
                    break
            if not skip and len(sentence) >= 4:
                unique_parts.append(sentence)

        if unique_parts:
            unique_text = "。".join(unique_parts) + "。"
            return generated + unique_text

    return generated


# ==========================================
# 8. エリアごとの施設分配
# ==========================================

# areaId → 既存施設リスト（areas.jsをパースして取得する代わりに、
# enriched のareaIdを使用）
area_facilities = {}  # areaId → [merged dict]
for code, h in merged.items():
    aid = h.get("areaId", "")
    if aid:
        if aid not in area_facilities:
            area_facilities[aid] = []
        area_facilities[aid].append(h)

# 各エリア内でベッド数降順にソート
for aid in area_facilities:
    area_facilities[aid].sort(key=lambda x: x.get("totalBeds", 0), reverse=True)

print("\nエリア別施設数:")
for aid, facilities in sorted(area_facilities.items()):
    print(f"  {aid}: {len(facilities)}施設")


# ==========================================
# 9. 既存 areas.js をパースして既存フィールドを保持
# ==========================================

# JavaScriptのオブジェクトリテラルをPythonで完全パースするのは困難なので、
# 施設名をキーに既存データのマッピングを作成する
# (既存areas.jsから抽出した施設の access, nightShiftType, annualHolidays, salary等を保持)

def parse_existing_facilities(js_text):
    """areas.jsから既存施設の手動設定フィールドを抽出"""
    facilities = {}

    # name: "..." でブロックを特定し、手動フィールドを抽出
    # 正規表現でシンプルに抽出
    blocks = re.split(r'\{\s*\n\s*name:', js_text)

    for block in blocks[1:]:  # 最初は前置テキスト
        # name
        m_name = re.match(r'\s*"([^"]+)"', block)
        if not m_name:
            continue
        name = m_name.group(1)

        info = {"name": name}

        # fullName
        m = re.search(r'fullName:\s*"([^"]*)"', block)
        if m:
            info["fullName"] = m.group(1)

        # access
        m = re.search(r'access:\s*"([^"]*)"', block)
        if m:
            info["access"] = m.group(1)

        # nightShiftType
        m = re.search(r'nightShiftType:\s*"([^"]*)"', block)
        if m:
            info["nightShiftType"] = m.group(1)

        # annualHolidays
        m = re.search(r'annualHolidays:\s*(\d+)', block)
        if m:
            info["annualHolidays"] = int(m.group(1))

        # nurseMonthlyMin/Max
        m = re.search(r'nurseMonthlyMin:\s*(\d+)', block)
        if m:
            info["nurseMonthlyMin"] = int(m.group(1))
        m = re.search(r'nurseMonthlyMax:\s*(\d+)', block)
        if m:
            info["nurseMonthlyMax"] = int(m.group(1))

        # ptMonthlyMin/Max
        m = re.search(r'ptMonthlyMin:\s*(\d+)', block)
        if m:
            info["ptMonthlyMin"] = int(m.group(1))
        m = re.search(r'ptMonthlyMax:\s*(\d+)', block)
        if m:
            info["ptMonthlyMax"] = int(m.group(1))

        # educationLevel
        m = re.search(r'educationLevel:\s*"([^"]*)"', block)
        if m:
            info["educationLevel"] = m.group(1)

        # features（既存）
        m = re.search(r'features:\s*"([^"]*)"', block)
        if m:
            info["features"] = m.group(1)

        # ptCount
        m = re.search(r'ptCount:\s*(\d+)', block)
        if m:
            info["ptCount_manual"] = int(m.group(1))

        # referral (A病院フラグ)
        if "referral:" in block:
            m = re.search(r'referral:\s*(true|false)', block)
            if m:
                info["referral"] = m.group(1) == "true"

        # matchingTags
        m = re.search(r'matchingTags:\s*\[([^\]]*)\]', block)
        if m:
            tags_str = m.group(1)
            tags = re.findall(r'"([^"]*)"', tags_str)
            info["matchingTags_manual"] = tags

        facilities[name] = info

    return facilities

existing_facilities = parse_existing_facilities(load_areas_js())
print(f"\n既存施設数（パース済み）: {len(existing_facilities)}")

# マッチング状況の確認
matched_count = 0
unmatched_existing = []
for name, info in existing_facilities.items():
    code = find_match(name, info.get("fullName"))
    if code:
        matched_count += 1
    else:
        unmatched_existing.append(name)

print(f"既存→公開データ マッチ: {matched_count}/{len(existing_facilities)}")
if unmatched_existing:
    print(f"未マッチ既存施設: {unmatched_existing}")


# ==========================================
# 10. 最終施設データの生成
# ==========================================

def build_facility_entry(h, existing_info=None):
    """1施設分のJSオブジェクト用 dict を生成"""
    entry = {}

    # 基本情報
    entry["name"] = h.get("name", "")
    if h.get("fullName") and h["fullName"] != h["name"]:
        entry["fullName"] = h["fullName"]
    elif existing_info and existing_info.get("fullName"):
        entry["fullName"] = existing_info["fullName"]

    entry["medicalCode"] = h.get("medicalCode", "")

    # 医療機能
    funcs = h.get("functions_ward") or []
    if not funcs:
        funcs = list(set(w.get("function", "") for w in h.get("wards", []) if w.get("function")))
    entry["type"] = build_type_string(funcs)
    entry["beds"] = h.get("totalBeds", 0)
    entry["wardCount"] = h.get("wardCount_ward") or h.get("wardCount", 0)
    entry["functions"] = funcs if funcs else ["不明"]

    # 看護配置
    nr = derive_nursing_ratio(h.get("admissionFees", []), h.get("nursingRatio", "不明"))
    entry["nursingRatio"] = nr
    entry["admissionFees"] = h.get("admissionFees", [])

    # 救急・DPC
    entry["emergencyLevel"] = h.get("emergencyLevel", "なし")
    entry["ambulanceCount"] = h.get("ambulanceCount", 0)
    entry["ownerType"] = h.get("ownerType", "")
    dpc = h.get("dpcGroup", "")
    entry["dpcHospital"] = "DPC" in dpc and "ではない" not in dpc

    # スタッフ数
    entry["nurseCount"] = h.get("nurseCount", 0)
    entry["doctorCount"] = h.get("doctorCount", 0)
    pt_public = h.get("ptCount", 0) or 0
    pt_manual = (existing_info or {}).get("ptCount_manual")
    entry["ptCount"] = pt_public if pt_public > 0 else (pt_manual or 0)
    entry["otCount"] = h.get("otCount", 0) or 0
    entry["stCount"] = h.get("stCount", 0) or 0
    entry["pharmacistCount"] = h.get("pharmacistCount", 0) or 0
    entry["midwifeCount"] = h.get("midwifeCount", 0) or 0

    # 設備
    entry["ctCount"] = h.get("ctCount", 0) or 0
    entry["mriCount"] = h.get("mriCount", 0) or 0

    # 所在地・座標
    entry["address"] = h.get("address", "")
    entry["lat"] = h.get("lat")
    entry["lng"] = h.get("lng")
    entry["website"] = h.get("website", "")

    # 既存データから保持するフィールド
    if existing_info:
        entry["access"] = existing_info.get("access", "")
        entry["nightShiftType"] = existing_info.get("nightShiftType", "二交代制")
        entry["annualHolidays"] = existing_info.get("annualHolidays", 110)
        entry["nurseMonthlyMin"] = existing_info.get("nurseMonthlyMin", 270000)
        entry["nurseMonthlyMax"] = existing_info.get("nurseMonthlyMax", 350000)
        entry["ptMonthlyMin"] = existing_info.get("ptMonthlyMin")
        entry["ptMonthlyMax"] = existing_info.get("ptMonthlyMax")
        entry["educationLevel"] = existing_info.get("educationLevel", "あり")
        if existing_info.get("referral") is not None:
            entry["referral"] = existing_info["referral"]
    else:
        # 公開データのみの施設（デフォルト値）
        entry["access"] = ""
        entry["nightShiftType"] = "二交代制"
        entry["annualHolidays"] = 110
        # 給与はエリアの平均を使用（後で設定）
        entry["nurseMonthlyMin"] = 270000
        entry["nurseMonthlyMax"] = 350000
        entry["ptMonthlyMin"] = None
        entry["ptMonthlyMax"] = None
        entry["educationLevel"] = "あり"

    # features 生成
    existing_features = (existing_info or {}).get("features")
    entry["features"] = build_features(h, existing_features)

    # matchingTags
    auto_tags = build_matching_tags(h)
    manual_tags = (existing_info or {}).get("matchingTags_manual", [])
    # マニュアルタグで自動にないものを追加
    all_tags = list(auto_tags)
    for t in manual_tags:
        if t not in all_tags:
            all_tags.append(t)
    entry["matchingTags"] = all_tags

    # データソース
    entry["dataSource"] = h.get("dataSource", "病床機能報告R5")
    entry["lastUpdated"] = "2026-02-25"

    return entry


# エリア別に最終データを構築
final_areas = {}  # areaId → [facility entries]
used_codes = set()

for aid, facilities in area_facilities.items():
    final_areas[aid] = []
    for h in facilities:
        code = h["medicalCode"]
        # 既存施設とのマッチ
        existing_info = None
        for ename, einfo in existing_facilities.items():
            ecode = find_match(ename, einfo.get("fullName"))
            if ecode == code:
                existing_info = einfo
                break

        entry = build_facility_entry(h, existing_info)
        final_areas[aid].append(entry)
        used_codes.add(code)

# 既存施設で公開データにマッチしなかったもの（20床未満のクリニック等）
# → 既存データのまま保持
unmatched_kept = 0
for name, info in existing_facilities.items():
    code = find_match(name, info.get("fullName"))
    if code is None:
        # どのエリアに属するか既存areas.jsから判定する必要がある
        # → 簡易的にスキップ（公開データに載っていない小規模施設）
        unmatched_kept += 1
        print(f"  公開データ未マッチ（保持せず）: {name}")

# ==========================================
# 11. areas.js の再生成
# ==========================================

# エリアメタデータ（既存のareas.jsから抽出して保持）
AREA_META = {
    "odawara": {
        "name": "小田原市",
        "medicalRegion": "kensei",
        "description": "神奈川県西部の中核都市。新幹線停車駅があり、箱根の玄関口。県西地域の医療の中心地。",
        "population": "約18.6万人",
        "majorStations": ["小田原駅（JR東海道線・小田急線・東海道新幹線・箱根登山鉄道・大雄山線）"],
        "commuteToYokohama": "約60分（JR東海道線）",
        "nurseAvgSalary": "月給28〜38万円",
        "ptAvgSalary": "月給25〜32万円",
        "demandLevel": "非常に高い",
        "demandNote": "県西の基幹病院が集中。小田原市立病院（417床）の新築移転予定に伴い人材需要が高まる。",
        "livingInfo": "新幹線停車駅で都心通勤も可能。箱根・湯河原の温泉地にも近く生活環境が魅力。",
    },
    "hadano": {
        "name": "秦野市",
        "medicalRegion": "shonan_west",
        "description": "丹沢山系の麓に位置する自然豊かな都市。落ち着いた環境と適度な都市機能を併せ持つ。",
        "population": "約16万人",
        "majorStations": ["秦野駅（小田急小田原線）", "東海大学前駅（小田急小田原線）", "渋沢駅（小田急小田原線）"],
        "commuteToYokohama": "約50分（小田急線）",
        "nurseAvgSalary": "月給27〜36万円",
        "ptAvgSalary": "月給24〜31万円",
        "demandLevel": "高い",
        "demandNote": "秦野赤十字病院（312床）を中心に安定した看護師需要。地域密着型の医療機関が多い。",
        "livingInfo": "丹沢山系の自然環境と住宅地が共存。物価が比較的安く、子育て環境に人気。",
    },
    "hiratsuka": {
        "name": "平塚市",
        "medicalRegion": "shonan_west",
        "description": "湘南エリア西部の中核都市。七夕まつりで有名。湘南地域の医療・商業の中心。",
        "population": "約25.6万人",
        "majorStations": ["平塚駅（JR東海道線）"],
        "commuteToYokohama": "約30分（JR東海道線）",
        "nurseAvgSalary": "月給28〜37万円",
        "ptAvgSalary": "月給25〜32万円",
        "demandLevel": "非常に高い",
        "demandNote": "平塚共済病院（441床）を筆頭に急性期病院が充実。人口規模に比して看護師需要が大きい。",
        "livingInfo": "海と山の両方にアクセスでき、自然と都市機能のバランスが良い。横浜通勤も現実的。",
    },
    "fujisawa": {
        "name": "藤沢市",
        "medicalRegion": "shonan_east",
        "description": "湘南エリア最大の都市。江ノ島・湘南海岸で全国的に知名度が高い。医療機関も充実。",
        "population": "約44万人",
        "majorStations": ["藤沢駅（JR東海道線・小田急江ノ島線・江ノ電）", "辻堂駅（JR東海道線）", "湘南台駅（小田急・相鉄・横浜市営地下鉄）"],
        "commuteToYokohama": "約20分（JR東海道線）",
        "nurseAvgSalary": "月給29〜38万円",
        "ptAvgSalary": "月給26〜33万円",
        "demandLevel": "非常に高い",
        "demandNote": "藤沢市民病院（530床）・湘南藤沢徳洲会病院（419床）など大規模病院が集中。看護師需要が県内屈指。",
        "livingInfo": "湘南のブランドエリア。海沿いのライフスタイルが人気。東京・横浜通勤も便利。",
    },
    "chigasaki": {
        "name": "茅ヶ崎市",
        "medicalRegion": "shonan_east",
        "description": "サザンオールスターズの聖地として知られる湘南の海辺の街。穏やかな雰囲気と都市機能が共存。",
        "population": "約24.4万人",
        "majorStations": ["茅ヶ崎駅（JR東海道線・相模線）", "北茅ヶ崎駅（JR相模線）"],
        "commuteToYokohama": "約25分（JR東海道線）",
        "nurseAvgSalary": "月給28〜37万円",
        "ptAvgSalary": "月給25〜32万円",
        "demandLevel": "高い",
        "demandNote": "茅ヶ崎市立病院（401床）が地域の中核。市内の高齢化に伴い訪問看護需要も増加。",
        "livingInfo": "海辺の穏やかな暮らし。サーフィン文化。駅前は商業施設も充実しバランスの良い環境。",
    },
    "oiso_ninomiya": {
        "name": "大磯町・二宮町",
        "medicalRegion": "shonan_west",
        "description": "湘南発祥の地・大磯と、二宮尊徳ゆかりの二宮町。閑静な住宅地と自然環境が魅力。",
        "population": "約6万人（合計）",
        "majorStations": ["大磯駅（JR東海道線）", "二宮駅（JR東海道線）"],
        "commuteToYokohama": "約40分（JR東海道線）",
        "nurseAvgSalary": "月給27〜35万円",
        "ptAvgSalary": "月給24〜31万円",
        "demandLevel": "やや高い",
        "demandNote": "大磯プリンスホテル跡地の再開発を含め、高齢者向け医療施設の需要が増加傾向。",
        "livingInfo": "湘南発祥の地。海と山の自然環境。閑静な住宅地で子育てにも適する。東海道線で通勤可。",
    },
    "minamiashigara_kaisei_oi": {
        "name": "南足柄市・開成町・大井町・松田町・山北町",
        "medicalRegion": "kensei",
        "description": "足柄平野に広がる自然豊かなエリア。金太郎伝説の南足柄、あじさいの里・開成町、鉄道の街・松田を含む。",
        "population": "約9.5万人（合計）",
        "majorStations": ["大雄山駅（伊豆箱根鉄道大雄山線）", "開成駅（小田急小田原線）", "松田駅（JR御殿場線・小田急小田原線）", "山北駅（JR御殿場線）"],
        "commuteToYokohama": "約70分（大雄山線+小田急線）",
        "nurseAvgSalary": "月給26〜35万円",
        "ptAvgSalary": "月給24〜30万円",
        "demandLevel": "高い",
        "demandNote": "足柄上病院（199床）が地域の中核。中山間地域の医療アクセス確保のため看護師需要が安定。",
        "livingInfo": "豊かな自然と低い生活コスト。小田原・新松田から小田急線で都心アクセスも可能。子育て支援充実。",
    },
    "isehara": {
        "name": "伊勢原市",
        "medicalRegion": "shonan_west",
        "description": "大山阿夫利神社の門前町として栄えた歴史ある都市。東海大学医学部付属病院が立地する医療の要衝。",
        "population": "約10.1万人",
        "majorStations": ["伊勢原駅（小田急小田原線）"],
        "commuteToYokohama": "約45分（小田急線）",
        "nurseAvgSalary": "月給28〜38万円",
        "ptAvgSalary": "月給25〜32万円",
        "demandLevel": "非常に高い",
        "demandNote": "東海大学医学部付属病院（804床・看護師741名）は県西最大の医療機関。常時大量採用。",
        "livingInfo": "大山の自然と大学のある学園都市。小田急線で新宿60分、物価も手頃。",
    },
    "atsugi": {
        "name": "厚木市",
        "medicalRegion": "kenoh",
        "description": "県央エリアの中核都市。本厚木駅前は県内有数の商業集積地。工業・商業・医療がバランスよく揃う。",
        "population": "約22.4万人",
        "majorStations": ["本厚木駅（小田急小田原線）", "愛甲石田駅（小田急小田原線）"],
        "commuteToYokohama": "約40分（小田急線）",
        "nurseAvgSalary": "月給28〜37万円",
        "ptAvgSalary": "月給25〜32万円",
        "demandLevel": "非常に高い",
        "demandNote": "厚木市立病院（347床）と東名厚木病院（271床）を中心に看護師需要が旺盛。リハビリ系施設も多い。",
        "livingInfo": "本厚木駅周辺は商業施設充実。新宿まで55分。丹沢の自然も近く子育て環境も良好。",
    },
    "ebina": {
        "name": "海老名市",
        "medicalRegion": "kenoh",
        "description": "3路線乗り入れの交通利便性と急速な再開発で人口増加中の注目都市。県央の医療拠点。",
        "population": "約14万人",
        "majorStations": ["海老名駅（小田急線・相鉄線・JR相模線）"],
        "commuteToYokohama": "約30分（相鉄線）",
        "nurseAvgSalary": "月給29〜38万円",
        "ptAvgSalary": "月給26〜33万円",
        "demandLevel": "非常に高い",
        "demandNote": "海老名総合病院（479床・看護師431名・PT56名）は県央唯一の救命救急センターで常時大量採用。年間救急車7,700台超。人口増加中で需要拡大。",
        "livingInfo": "3路線利用可能で交通利便性抜群。横浜まで30分、新宿まで50分。駅前再開発でららぽーと・ビナウォークなど商業施設充実。子育て世代に人気。",
    },
}

# エリアの表示順序
AREA_ORDER = [
    "odawara", "hadano", "hiratsuka", "fujisawa", "chigasaki",
    "oiso_ninomiya", "minamiashigara_kaisei_oi", "isehara", "atsugi", "ebina"
]


def js_str(s):
    """Python文字列 → JS文字列リテラル"""
    if s is None:
        return "null"
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'

def js_num(n):
    if n is None:
        return "null"
    if isinstance(n, float):
        return str(round(n, 6))
    return str(n)

def js_bool(b):
    if b is None:
        return "null"
    return "true" if b else "false"

def js_array_str(arr):
    """文字列配列をJS形式に"""
    if not arr:
        return "[]"
    items = ", ".join(js_str(s) for s in arr)
    return f"[{items}]"


def format_facility(f, indent="      "):
    """施設データを整形されたJS文字列に変換"""
    lines = []
    lines.append(f"{indent}{{")
    i = indent + "  "

    lines.append(f'{i}name: {js_str(f["name"])},')
    if f.get("fullName"):
        lines.append(f'{i}fullName: {js_str(f["fullName"])},')
    if f.get("medicalCode"):
        lines.append(f'{i}medicalCode: {js_str(f["medicalCode"])},')

    lines.append(f'{i}type: {js_str(f["type"])},')
    lines.append(f'{i}beds: {js_num(f["beds"])},')
    lines.append(f'{i}wardCount: {js_num(f.get("wardCount", 0))},')
    lines.append(f'{i}functions: {js_array_str(f.get("functions", []))},')

    # 看護配置
    lines.append(f'{i}nursingRatio: {js_str(f.get("nursingRatio", "不明"))},')
    if f.get("admissionFees"):
        lines.append(f'{i}admissionFees: {js_array_str(f["admissionFees"])},')

    # 救急・DPC
    lines.append(f'{i}emergencyLevel: {js_str(f.get("emergencyLevel", "なし"))},')
    amb = f.get("ambulanceCount", 0)
    if amb and amb > 0:
        lines.append(f'{i}ambulanceCount: {js_num(amb)},')
    lines.append(f'{i}ownerType: {js_str(f.get("ownerType", ""))},')
    lines.append(f'{i}dpcHospital: {js_bool(f.get("dpcHospital", False))},')

    # スタッフ
    lines.append(f'{i}nurseCount: {js_num(f.get("nurseCount", 0))},')
    dc = f.get("doctorCount", 0)
    if dc and dc > 0:
        lines.append(f'{i}doctorCount: {js_num(dc)},')
    pt = f.get("ptCount", 0)
    if pt and pt > 0:
        lines.append(f'{i}ptCount: {js_num(pt)},')
    ot = f.get("otCount", 0)
    if ot and ot > 0:
        lines.append(f'{i}otCount: {js_num(ot)},')
    st = f.get("stCount", 0)
    if st and st > 0:
        lines.append(f'{i}stCount: {js_num(st)},')
    pharm = f.get("pharmacistCount", 0)
    if pharm and pharm > 0:
        lines.append(f'{i}pharmacistCount: {js_num(pharm)},')
    mid = f.get("midwifeCount", 0)
    if mid and mid > 0:
        lines.append(f'{i}midwifeCount: {js_num(mid)},')

    # 設備
    ct = f.get("ctCount", 0)
    mri = f.get("mriCount", 0)
    if ct and ct > 0:
        lines.append(f'{i}ctCount: {js_num(ct)},')
    if mri and mri > 0:
        lines.append(f'{i}mriCount: {js_num(mri)},')

    # 所在地
    if f.get("address"):
        lines.append(f'{i}address: {js_str(f["address"])},')
    if f.get("lat") is not None:
        lines.append(f'{i}lat: {js_num(f["lat"])},')
        lines.append(f'{i}lng: {js_num(f["lng"])},')
    if f.get("website"):
        lines.append(f'{i}website: {js_str(f["website"])},')

    # 既存フィールド
    lines.append(f'{i}features: {js_str(f.get("features", ""))},')
    lines.append(f'{i}access: {js_str(f.get("access", ""))},')
    lines.append(f'{i}nightShiftType: {js_str(f.get("nightShiftType", "二交代制"))},')
    lines.append(f'{i}annualHolidays: {js_num(f.get("annualHolidays", 110))},')
    lines.append(f'{i}nurseMonthlyMin: {js_num(f.get("nurseMonthlyMin", 270000))},')
    lines.append(f'{i}nurseMonthlyMax: {js_num(f.get("nurseMonthlyMax", 350000))},')
    lines.append(f'{i}ptMonthlyMin: {js_num(f.get("ptMonthlyMin"))},')
    lines.append(f'{i}ptMonthlyMax: {js_num(f.get("ptMonthlyMax"))},')
    lines.append(f'{i}educationLevel: {js_str(f.get("educationLevel", "あり"))},')

    # referral
    if f.get("referral") is not None:
        lines.append(f'{i}referral: {js_bool(f["referral"])},')

    lines.append(f'{i}matchingTags: {js_array_str(f.get("matchingTags", []))},')
    lines.append(f'{i}dataSource: {js_str(f.get("dataSource", ""))},')
    lines.append(f'{i}lastUpdated: {js_str(f.get("lastUpdated", "2026-02-25"))},')

    lines.append(f"{indent}}},")
    return "\n".join(lines)


def format_area(aid, meta, facilities):
    """エリアデータを整形されたJS文字列に変換"""
    lines = []
    lines.append("  {")
    i = "    "

    lines.append(f'{i}areaId: {js_str(aid)},')
    lines.append(f'{i}name: {js_str(meta["name"])},')
    lines.append(f'{i}medicalRegion: {js_str(meta["medicalRegion"])},')
    lines.append(f'{i}description: {js_str(meta["description"])},')
    lines.append(f'{i}population: {js_str(meta["population"])},')

    # majorStations
    stations = meta.get("majorStations", [])
    if len(stations) == 1:
        lines.append(f'{i}majorStations: [{js_str(stations[0])}],')
    else:
        lines.append(f'{i}majorStations: [')
        for s in stations:
            lines.append(f'{i}  {js_str(s)},')
        lines.append(f'{i}],')

    lines.append(f'{i}commuteToYokohama: {js_str(meta["commuteToYokohama"])},')
    lines.append(f'{i}nurseAvgSalary: {js_str(meta["nurseAvgSalary"])},')
    lines.append(f'{i}ptAvgSalary: {js_str(meta["ptAvgSalary"])},')

    # facilityCount
    h_count = len(facilities)
    lines.append(f'{i}facilityCount: {{ hospitals: {h_count}, clinics: 0, nursingHomes: 0 }},')

    # majorFacilities
    lines.append(f'{i}majorFacilities: [')
    for f in facilities:
        lines.append(format_facility(f))
    lines.append(f'{i}],')

    lines.append(f'{i}demandLevel: {js_str(meta.get("demandLevel", "高い"))},')
    lines.append(f'{i}demandNote: {js_str(meta.get("demandNote", ""))},')
    lines.append(f'{i}livingInfo: {js_str(meta.get("livingInfo", ""))},')

    lines.append("  },")
    return "\n".join(lines)


# ==========================================
# 12. 出力
# ==========================================

output_lines = []
output_lines.append("// ========================================")
output_lines.append("// ナースロビー - エリア・医療機関データベース")
output_lines.append("// 神奈川県西部10エリア 実データ（病床機能報告R5 + 医療情報ネット 2025.12）")
output_lines.append("// 自動生成: 2026-02-25 merge_and_update_areas.py")
output_lines.append("// ========================================")
output_lines.append("")

# MEDICAL_REGIONS（そのまま）
output_lines.append("// ==========================================")
output_lines.append("// 医療圏マスターデータ（神奈川県二次保健医療圏）")
output_lines.append("// ==========================================")
output_lines.append("const MEDICAL_REGIONS = [")
output_lines.append('  {')
output_lines.append('    regionId: "kensei",')
output_lines.append('    name: "県西",')
output_lines.append('    description: "小田原市を中心とした神奈川県西部の医療圏。箱根・足柄エリアを含む。",')
output_lines.append('    areaIds: ["odawara", "minamiashigara_kaisei_oi"],')
output_lines.append('    municipalities: ["小田原市", "南足柄市", "開成町", "大井町", "中井町", "松田町", "山北町", "箱根町", "真鶴町", "湯河原町"],')
output_lines.append('  },')
output_lines.append('  {')
output_lines.append('    regionId: "shonan_west",')
output_lines.append('    name: "湘南西部",')
output_lines.append('    description: "平塚市・秦野市・伊勢原市を中核とした湘南西部の医療圏。東海大学病院が立地。",')
output_lines.append('    areaIds: ["hiratsuka", "hadano", "isehara", "oiso_ninomiya"],')
output_lines.append('    municipalities: ["平塚市", "秦野市", "伊勢原市", "大磯町", "二宮町"],')
output_lines.append('  },')
output_lines.append('  {')
output_lines.append('    regionId: "shonan_east",')
output_lines.append('    name: "湘南東部",')
output_lines.append('    description: "藤沢市・茅ヶ崎市を中心とした湘南東部の医療圏。県内有数の医療集積地。",')
output_lines.append('    areaIds: ["fujisawa", "chigasaki"],')
output_lines.append('    municipalities: ["藤沢市", "茅ヶ崎市", "寒川町"],')
output_lines.append('  },')
output_lines.append('  {')
output_lines.append('    regionId: "kenoh",')
output_lines.append('    name: "県央",')
output_lines.append('    description: "厚木市・海老名市を中心とした県央の医療圏。海老名総合病院が3次救急を担う。",')
output_lines.append('    areaIds: ["atsugi", "ebina"],')
output_lines.append('    municipalities: ["厚木市", "海老名市", "大和市", "座間市", "綾瀬市", "愛川町", "清川村"],')
output_lines.append('  },')
output_lines.append("];")
output_lines.append("")

# AREA_DATABASE
output_lines.append("const AREA_DATABASE = [")

total_facilities = 0
for aid in AREA_ORDER:
    meta = AREA_META.get(aid)
    if not meta:
        print(f"WARNING: no meta for {aid}")
        continue
    facilities = final_areas.get(aid, [])
    total_facilities += len(facilities)
    output_lines.append(format_area(aid, meta, facilities))

output_lines.append("];")
output_lines.append("")

# ヘルパー関数
output_lines.append("// ==========================================")
output_lines.append("// エリア検索ヘルパー")
output_lines.append("// ==========================================")
output_lines.append("function findAreaByName(name) {")
output_lines.append("  if (!name) return null;")
output_lines.append("  return AREA_DATABASE.find(a =>")
output_lines.append('    a.name.includes(name) || name.includes(a.name) ||')
output_lines.append('    a.areaId === name.toLowerCase()')
output_lines.append("  );")
output_lines.append("}")
output_lines.append("")
output_lines.append("// 施設検索ヘルパー")
output_lines.append("function findFacilitiesByArea(areaName) {")
output_lines.append("  const area = findAreaByName(areaName);")
output_lines.append("  return area ? area.majorFacilities : [];")
output_lines.append("}")
output_lines.append("")
output_lines.append("// 全施設数サマリ")
output_lines.append("function getDatabaseSummary() {")
output_lines.append("  let totalFacilities = 0;")
output_lines.append("  let totalBeds = 0;")
output_lines.append("  let totalNurses = 0;")
output_lines.append("  for (const area of AREA_DATABASE) {")
output_lines.append("    totalFacilities += area.majorFacilities.length;")
output_lines.append("    for (const f of area.majorFacilities) {")
output_lines.append("      totalBeds += f.beds || 0;")
output_lines.append("      totalNurses += f.nurseCount || 0;")
output_lines.append("    }")
output_lines.append("  }")
output_lines.append("  return { areas: AREA_DATABASE.length, facilities: totalFacilities, beds: totalBeds, nurses: totalNurses };")
output_lines.append("}")
output_lines.append("")
output_lines.append("// ==========================================")
output_lines.append("// 医療圏ベース検索ヘルパー")
output_lines.append("// ==========================================")
output_lines.append("")
output_lines.append("// 医療圏IDからエリア配列を返す")
output_lines.append("function findAreasByRegion(regionId) {")
output_lines.append('  const region = MEDICAL_REGIONS.find(r => r.regionId === regionId);')
output_lines.append("  if (!region) return [];")
output_lines.append("  return AREA_DATABASE.filter(a => region.areaIds.includes(a.areaId));")
output_lines.append("}")
output_lines.append("")
output_lines.append("// 医療圏IDから施設配列をフラットに返す")
output_lines.append("function findFacilitiesByRegion(regionId) {")
output_lines.append("  const areas = findAreasByRegion(regionId);")
output_lines.append("  const facilities = [];")
output_lines.append("  for (const area of areas) {")
output_lines.append("    for (const f of area.majorFacilities) {")
output_lines.append("      facilities.push({ ...f, areaId: area.areaId, areaName: area.name });")
output_lines.append("    }")
output_lines.append("  }")
output_lines.append("  return facilities;")
output_lines.append("}")
output_lines.append("")
output_lines.append("// 全施設をフラット配列で返す（エリア情報付き）")
output_lines.append("function getAllFacilities() {")
output_lines.append("  const facilities = [];")
output_lines.append("  for (const area of AREA_DATABASE) {")
output_lines.append("    for (const f of area.majorFacilities) {")
output_lines.append('      facilities.push({ ...f, areaId: area.areaId, areaName: area.name, medicalRegion: area.medicalRegion });')
output_lines.append("    }")
output_lines.append("  }")
output_lines.append("  return facilities;")
output_lines.append("}")
output_lines.append("")
output_lines.append('// ブラウザ・Node.js両対応エクスポート')
output_lines.append('if (typeof module !== "undefined" && module.exports) {')
output_lines.append("  module.exports = {")
output_lines.append("    MEDICAL_REGIONS,")
output_lines.append("    AREA_DATABASE,")
output_lines.append("    findAreaByName,")
output_lines.append("    findFacilitiesByArea,")
output_lines.append("    getDatabaseSummary,")
output_lines.append("    findAreasByRegion,")
output_lines.append("    findFacilitiesByRegion,")
output_lines.append("    getAllFacilities,")
output_lines.append("  };")
output_lines.append("}")
output_lines.append("")

# 書き込み
output_text = "\n".join(output_lines)
OUTPUT_JS.write_text(output_text, encoding="utf-8")

print(f"\n✅ areas.js 更新完了!")
print(f"  エリア数: {len(AREA_ORDER)}")
print(f"  施設数: {total_facilities}")
print(f"  出力: {OUTPUT_JS}")
