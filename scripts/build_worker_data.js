#!/usr/bin/env node
/**
 * areas.js の全97施設データを worker.js 用の FACILITY_DATABASE 形式に変換
 *
 * Usage: node scripts/build_worker_data.js > api/worker_facilities.js
 */

const { AREA_DATABASE } = require('../data/areas.js');

// 各エリアの主要駅の概略座標（Haversine距離計算用）
const STATION_COORDINATES = {
  // 小田原
  "小田原駅": { lat: 35.2564, lng: 139.1551 },
  "鴨宮駅": { lat: 35.2687, lng: 139.1760 },
  "国府津駅": { lat: 35.2760, lng: 139.2050 },
  "足柄駅": { lat: 35.2480, lng: 139.1230 },
  "螢田駅": { lat: 35.2670, lng: 139.1370 },
  "富水駅": { lat: 35.2740, lng: 139.1250 },
  // 秦野
  "秦野駅": { lat: 35.3737, lng: 139.2192 },
  "東海大学前駅": { lat: 35.3660, lng: 139.2540 },
  "鶴巻温泉駅": { lat: 35.3690, lng: 139.2700 },
  "渋沢駅": { lat: 35.3800, lng: 139.1900 },
  // 平塚
  "平塚駅": { lat: 35.3280, lng: 139.3497 },
  "大磯駅": { lat: 35.3120, lng: 139.3110 },
  // 藤沢
  "藤沢駅": { lat: 35.3380, lng: 139.4870 },
  "辻堂駅": { lat: 35.3350, lng: 139.4480 },
  "湘南台駅": { lat: 35.3900, lng: 139.4680 },
  "善行駅": { lat: 35.3580, lng: 139.4630 },
  "六会日大前駅": { lat: 35.3770, lng: 139.4610 },
  "藤沢本町駅": { lat: 35.3470, lng: 139.4780 },
  // 茅ヶ崎
  "茅ヶ崎駅": { lat: 35.3340, lng: 139.4040 },
  "北茅ヶ崎駅": { lat: 35.3490, lng: 139.4010 },
  "香川駅": { lat: 35.3570, lng: 139.3780 },
  // 大磯・二宮
  "二宮駅": { lat: 35.2990, lng: 139.2550 },
  // 南足柄・開成・大井
  "大雄山駅": { lat: 35.3300, lng: 139.1100 },
  "開成駅": { lat: 35.3350, lng: 139.1480 },
  "和田河原駅": { lat: 35.3230, lng: 139.1210 },
  "相模金子駅": { lat: 35.3090, lng: 139.1590 },
  // 伊勢原
  "伊勢原駅": { lat: 35.3950, lng: 139.3140 },
  // 厚木
  "本厚木駅": { lat: 35.4410, lng: 139.3650 },
  "愛甲石田駅": { lat: 35.4120, lng: 139.3270 },
  // 海老名
  "海老名駅": { lat: 35.4470, lng: 139.3910 },
  "さがみ野駅": { lat: 35.4590, lng: 139.4010 },
};

// access文字列から最寄り駅名を推定
function extractStation(access) {
  if (!access) return null;
  for (const station of Object.keys(STATION_COORDINATES)) {
    const stationBase = station.replace("駅", "");
    if (access.includes(stationBase)) return station;
  }
  return null;
}

// エリアのデフォルト座標（最寄り駅が特定できない場合）
const AREA_DEFAULT_COORDS = {
  "odawara": { lat: 35.2564, lng: 139.1551 },
  "hadano": { lat: 35.3737, lng: 139.2192 },
  "hiratsuka": { lat: 35.3280, lng: 139.3497 },
  "fujisawa": { lat: 35.3380, lng: 139.4870 },
  "chigasaki": { lat: 35.3340, lng: 139.4040 },
  "oiso_ninomiya": { lat: 35.3060, lng: 139.2830 },
  "minamiashigara": { lat: 35.3270, lng: 139.1150 },
  "isehara": { lat: 35.3950, lng: 139.3140 },
  "atsugi": { lat: 35.4410, lng: 139.3650 },
  "ebina": { lat: 35.4470, lng: 139.3910 },
};

// メイン変換
const facilityDB = {};
const areaMetadata = {};

for (const area of AREA_DATABASE) {
  const areaName = area.name;

  // エリアメタデータ
  areaMetadata[areaName] = {
    areaId: area.areaId,
    medicalRegion: area.medicalRegion,
    population: area.population,
    majorStations: area.majorStations,
    commuteToYokohama: area.commuteToYokohama,
    nurseAvgSalary: area.nurseAvgSalary,
    ptAvgSalary: area.ptAvgSalary,
    facilityCount: area.facilityCount,
    demandLevel: area.demandLevel,
    demandNote: area.demandNote,
    livingInfo: area.livingInfo,
    defaultCoords: AREA_DEFAULT_COORDS[area.areaId] || null,
  };

  // 施設データ変換
  facilityDB[areaName] = area.majorFacilities.map(f => {
    const station = extractStation(f.access);
    const coords = station ? STATION_COORDINATES[station] : (AREA_DEFAULT_COORDS[area.areaId] || null);

    return {
      name: f.name,
      type: f.type,
      beds: f.beds,
      wardCount: f.wardCount,
      functions: f.functions,
      nurseCount: f.nurseCount,
      ptCount: f.ptCount || null,
      features: f.features,
      access: f.access,
      nightShiftType: f.nightShiftType,
      annualHolidays: f.annualHolidays,
      salaryMin: f.nurseMonthlyMin,
      salaryMax: f.nurseMonthlyMax,
      ptSalaryMin: f.ptMonthlyMin || null,
      ptSalaryMax: f.ptMonthlyMax || null,
      educationLevel: f.educationLevel,
      matchingTags: f.matchingTags,
      // 座標（距離計算用）
      lat: coords ? coords.lat : null,
      lng: coords ? coords.lng : null,
      nearestStation: station,
    };
  });
}

// 出力
console.log("// ==========================================");
console.log("// ナースロビー - 施設データベース（自動生成）");
console.log("// Generated: " + new Date().toISOString());
console.log("// Source: data/areas.js (" + AREA_DATABASE.length + "エリア)");
console.log("// ==========================================");
console.log("");
console.log("// 駅座標データ（Haversine距離計算用）");
console.log("const STATION_COORDINATES = " + JSON.stringify(STATION_COORDINATES, null, 2) + ";");
console.log("");
console.log("// エリアメタデータ");
console.log("const AREA_METADATA = " + JSON.stringify(areaMetadata, null, 2) + ";");
console.log("");
console.log("// 全施設データベース（" + Object.values(facilityDB).flat().length + "施設）");
console.log("const FACILITY_DATABASE = " + JSON.stringify(facilityDB, null, 2) + ";");

// サマリ出力 to stderr
let totalFacilities = 0;
for (const [area, facilities] of Object.entries(facilityDB)) {
  totalFacilities += facilities.length;
  process.stderr.write(`  ${area}: ${facilities.length}施設\n`);
}
process.stderr.write(`\n合計: ${totalFacilities}施設\n`);
