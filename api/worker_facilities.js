// ==========================================
// ナースロビー - 施設データベース（自動生成）
// Generated: 2026-02-22T07:30:50.703Z
// Source: data/areas.js (10エリア)
// ==========================================

// 駅座標データ（Haversine距離計算用）
export const STATION_COORDINATES = {
  "小田原駅": {
    "lat": 35.2564,
    "lng": 139.1551
  },
  "鴨宮駅": {
    "lat": 35.2687,
    "lng": 139.176
  },
  "国府津駅": {
    "lat": 35.276,
    "lng": 139.205
  },
  "足柄駅": {
    "lat": 35.248,
    "lng": 139.123
  },
  "螢田駅": {
    "lat": 35.267,
    "lng": 139.137
  },
  "富水駅": {
    "lat": 35.274,
    "lng": 139.125
  },
  "秦野駅": {
    "lat": 35.3737,
    "lng": 139.2192
  },
  "東海大学前駅": {
    "lat": 35.366,
    "lng": 139.254
  },
  "鶴巻温泉駅": {
    "lat": 35.369,
    "lng": 139.27
  },
  "渋沢駅": {
    "lat": 35.38,
    "lng": 139.19
  },
  "平塚駅": {
    "lat": 35.328,
    "lng": 139.3497
  },
  "大磯駅": {
    "lat": 35.312,
    "lng": 139.311
  },
  "藤沢駅": {
    "lat": 35.338,
    "lng": 139.487
  },
  "辻堂駅": {
    "lat": 35.335,
    "lng": 139.448
  },
  "湘南台駅": {
    "lat": 35.39,
    "lng": 139.468
  },
  "善行駅": {
    "lat": 35.358,
    "lng": 139.463
  },
  "六会日大前駅": {
    "lat": 35.377,
    "lng": 139.461
  },
  "藤沢本町駅": {
    "lat": 35.347,
    "lng": 139.478
  },
  "茅ヶ崎駅": {
    "lat": 35.334,
    "lng": 139.404
  },
  "北茅ヶ崎駅": {
    "lat": 35.349,
    "lng": 139.401
  },
  "香川駅": {
    "lat": 35.357,
    "lng": 139.378
  },
  "二宮駅": {
    "lat": 35.299,
    "lng": 139.255
  },
  "大雄山駅": {
    "lat": 35.33,
    "lng": 139.11
  },
  "開成駅": {
    "lat": 35.335,
    "lng": 139.148
  },
  "和田河原駅": {
    "lat": 35.323,
    "lng": 139.121
  },
  "相模金子駅": {
    "lat": 35.309,
    "lng": 139.159
  },
  "伊勢原駅": {
    "lat": 35.395,
    "lng": 139.314
  },
  "本厚木駅": {
    "lat": 35.441,
    "lng": 139.365
  },
  "愛甲石田駅": {
    "lat": 35.412,
    "lng": 139.327
  },
  "海老名駅": {
    "lat": 35.447,
    "lng": 139.391
  },
  "さがみ野駅": {
    "lat": 35.459,
    "lng": 139.401
  }
};

// エリアメタデータ
export const AREA_METADATA = {
  "小田原市": {
    "areaId": "odawara",
    "medicalRegion": "kensei",
    "population": "約18.6万人",
    "majorStations": [
      "小田原駅（JR東海道線・小田急線・東海道新幹線・箱根登山鉄道・大雄山線）"
    ],
    "commuteToYokohama": "約60分（JR東海道線）",
    "nurseAvgSalary": "月給28〜38万円",
    "ptAvgSalary": "月給25〜32万円",
    "facilityCount": {
      "hospitals": 11,
      "clinics": 193,
      "nursingHomes": 35
    },
    "demandLevel": "高",
    "demandNote": "県西地域の医療中心地で慢性的な看護師不足。小田原市立病院（417床・看護師270名）の新築移転に伴い需要増大。高齢化率31%。",
    "livingInfo": "海と山が近く自然豊か。新幹線で東京約70分。箱根・湯河原の温泉地が近く、魚介類が新鮮。家賃は横浜の6割程度。",
    "defaultCoords": {
      "lat": 35.2564,
      "lng": 139.1551
    }
  },
  "秦野市": {
    "areaId": "hadano",
    "medicalRegion": "shonan_west",
    "population": "約15.8万人",
    "majorStations": [
      "秦野駅（小田急小田原線）",
      "渋沢駅（小田急小田原線）",
      "東海大学前駅（小田急小田原線）"
    ],
    "commuteToYokohama": "約70分（小田急線経由）",
    "nurseAvgSalary": "月給27〜35万円",
    "ptAvgSalary": "月給24〜31万円",
    "facilityCount": {
      "hospitals": 4,
      "clinics": 130,
      "nursingHomes": 25
    },
    "demandLevel": "高",
    "demandNote": "秦野赤十字病院（308床・看護師155名）が中核。鶴巻温泉病院（505床）は県西最大級の療養施設。精神科・慢性期の需要あり。",
    "livingInfo": "丹沢の山々に囲まれた自然豊かな環境。名水の里で水道水もおいしい。小田急で新宿約70分。家賃は県内でも安い水準。",
    "defaultCoords": {
      "lat": 35.3737,
      "lng": 139.2192
    }
  },
  "平塚市": {
    "areaId": "hiratsuka",
    "medicalRegion": "shonan_west",
    "population": "約25.6万人",
    "majorStations": [
      "平塚駅（JR東海道線）"
    ],
    "commuteToYokohama": "約30分（JR東海道線）",
    "nurseAvgSalary": "月給28〜37万円",
    "ptAvgSalary": "月給25〜32万円",
    "facilityCount": {
      "hospitals": 7,
      "clinics": 277,
      "nursingHomes": 30
    },
    "demandLevel": "高",
    "demandNote": "平塚共済病院（441床・看護師301名）と平塚市民病院（412床・315名）の2大病院で看護師需要が非常に高い。急性期からリハビリまで幅広い求人あり。",
    "livingInfo": "湘南エリアの利便性と比較的手頃な家賃が魅力。横浜まで30分、東京まで約60分。七夕まつりが有名で商業施設も充実。海が近い。",
    "defaultCoords": {
      "lat": 35.328,
      "lng": 139.3497
    }
  },
  "藤沢市": {
    "areaId": "fujisawa",
    "medicalRegion": "shonan_east",
    "population": "約44.5万人",
    "majorStations": [
      "藤沢駅（JR東海道線・小田急線・江ノ電）",
      "辻堂駅（JR東海道線）",
      "湘南台駅（小田急線・相鉄線・横浜市営地下鉄）"
    ],
    "commuteToYokohama": "約20分（JR東海道線）",
    "nurseAvgSalary": "月給29〜38万円",
    "ptAvgSalary": "月給26〜33万円",
    "facilityCount": {
      "hospitals": 14,
      "clinics": 350,
      "nursingHomes": 45
    },
    "demandLevel": "非常に高い",
    "demandNote": "藤沢市民病院（530床・看護師405名）と湘南藤沢徳洲会病院（419床・282名）の2大急性期病院で常時募集。病院14施設と県西最多。回復期・在宅分野も拡大中。",
    "livingInfo": "湘南の中心地で海が近く生活環境良好。横浜まで20分、東京まで約50分と通勤圏内。商業施設充実。辻堂エリアは再開発で人気上昇中。",
    "defaultCoords": {
      "lat": 35.338,
      "lng": 139.487
    }
  },
  "茅ヶ崎市": {
    "areaId": "chigasaki",
    "medicalRegion": "shonan_east",
    "population": "約24.7万人",
    "majorStations": [
      "茅ヶ崎駅（JR東海道線・相模線）",
      "北茅ヶ崎駅（JR相模線）"
    ],
    "commuteToYokohama": "約25分（JR東海道線）",
    "nurseAvgSalary": "月給28〜37万円",
    "ptAvgSalary": "月給25〜32万円",
    "facilityCount": {
      "hospitals": 7,
      "clinics": 200,
      "nursingHomes": 25
    },
    "demandLevel": "高",
    "demandNote": "茅ヶ崎市立病院（401床・看護師216名）が中核。茅ヶ崎中央病院（324床）・湘南東部総合病院（323床）と中〜大規模病院が3つ。療養・回復期の需要も高い。",
    "livingInfo": "湘南らしい開放的な雰囲気。海沿いのライフスタイルが人気。横浜まで25分と交通至便。藤沢に比べやや家賃が安い。",
    "defaultCoords": {
      "lat": 35.334,
      "lng": 139.404
    }
  },
  "大磯町・二宮町": {
    "areaId": "oiso_ninomiya",
    "medicalRegion": "shonan_west",
    "population": "約5.7万人（大磯町約3.1万人＋二宮町約2.6万人）",
    "majorStations": [
      "大磯駅（JR東海道線）",
      "二宮駅（JR東海道線）"
    ],
    "commuteToYokohama": "約40分（JR東海道線）",
    "nurseAvgSalary": "月給27〜35万円",
    "ptAvgSalary": "月給24〜31万円",
    "facilityCount": {
      "hospitals": 1,
      "clinics": 50,
      "nursingHomes": 15
    },
    "demandLevel": "中〜高",
    "demandNote": "エリア唯一の総合病院（312床・看護師90名）に需要が集中。一部病棟が休棟中で再開に伴い看護師増員見込み。高齢化率が高く訪問看護のニーズも。",
    "livingInfo": "相模湾を望む穏やかな住環境。歴史ある保養地で自然が豊か。横浜まで40分。家賃は湘南エリアで最も安い水準。",
    "defaultCoords": {
      "lat": 35.306,
      "lng": 139.283
    }
  },
  "南足柄市・開成町・大井町": {
    "areaId": "minamiashigara_kaisei_oi",
    "medicalRegion": "kensei",
    "population": "約7.5万人（南足柄市約3.9万人＋開成町約1.9万人＋大井町約1.7万人）",
    "majorStations": [
      "大雄山駅（大雄山線）",
      "開成駅（小田急線）",
      "新松田駅（小田急線）"
    ],
    "commuteToYokohama": "約80分（小田急線経由）",
    "nurseAvgSalary": "月給26〜34万円",
    "ptAvgSalary": "月給23〜30万円",
    "facilityCount": {
      "hospitals": 4,
      "clinics": 45,
      "nursingHomes": 15
    },
    "demandLevel": "中",
    "demandNote": "医療施設が少なく看護師確保が困難。勝又高台病院（310床・看護師71名）が最大。少人数で幅広い業務をこなせる人材が求められる。",
    "livingInfo": "足柄平野の豊かな自然。箱根に近い。開成町は県内最小面積ながら人口密度が高い新興住宅地。家賃は県内最安水準。",
    "defaultCoords": null
  },
  "伊勢原市": {
    "areaId": "isehara",
    "medicalRegion": "shonan_west",
    "population": "約10万人",
    "majorStations": [
      "伊勢原駅（小田急小田原線）"
    ],
    "commuteToYokohama": "約50分（小田急線・相鉄直通）",
    "nurseAvgSalary": "月給28〜37万円",
    "ptAvgSalary": "月給25〜32万円",
    "facilityCount": {
      "hospitals": 3,
      "clinics": 68,
      "nursingHomes": 15
    },
    "demandLevel": "非常に高い",
    "demandNote": "東海大学病院（804床・看護師741名）は県西最大の医療機関で常時看護師を大量募集。伊勢原協同病院（350床・239名）も地域中核。2病院だけで看護師約1000名規模。",
    "livingInfo": "大山のふもとの自然豊かな住環境。小田急線で新宿約60分。大学病院城下町として医療関係者が多い。家賃は比較的安い。",
    "defaultCoords": {
      "lat": 35.395,
      "lng": 139.314
    }
  },
  "厚木市": {
    "areaId": "atsugi",
    "medicalRegion": "kenoh",
    "population": "約22.3万人",
    "majorStations": [
      "本厚木駅（小田急小田原線）"
    ],
    "commuteToYokohama": "約45分（小田急線・相鉄直通）",
    "nurseAvgSalary": "月給28〜37万円",
    "ptAvgSalary": "月給25〜32万円",
    "facilityCount": {
      "hospitals": 9,
      "clinics": 200,
      "nursingHomes": 30
    },
    "demandLevel": "高",
    "demandNote": "厚木市立病院（341床・看護師233名）が基幹。東名厚木病院（282床・205名）はがん診療に強み。AOI七沢リハ（245床・リハスタッフ108名）でPT/OT/ST需要も高い。",
    "livingInfo": "小田急線で新宿約50分。本厚木駅前は商業施設が充実し生活利便性が高い。七沢温泉など自然も楽しめる。家賃は藤沢より2割安い水準。",
    "defaultCoords": {
      "lat": 35.441,
      "lng": 139.365
    }
  },
  "海老名市": {
    "areaId": "ebina",
    "medicalRegion": "kenoh",
    "population": "約14.1万人",
    "majorStations": [
      "海老名駅（小田急線・相鉄線・JR相模線）"
    ],
    "commuteToYokohama": "約30分（相鉄線直通）",
    "nurseAvgSalary": "月給29〜38万円",
    "ptAvgSalary": "月給26〜33万円",
    "facilityCount": {
      "hospitals": 4,
      "clinics": 100,
      "nursingHomes": 20
    },
    "demandLevel": "非常に高い",
    "demandNote": "海老名総合病院（479床・看護師431名・PT56名）は県央唯一の救命救急センターで常時大量採用。年間救急車7,700台超。人口増加中で需要拡大。",
    "livingInfo": "3路線利用可能で交通利便性抜群。横浜まで30分、新宿まで50分。駅前再開発でららぽーと・ビナウォークなど商業施設充実。子育て世代に人気。",
    "defaultCoords": {
      "lat": 35.447,
      "lng": 139.391
    }
  }
};

// 全施設データベース（97施設）
export const FACILITY_DATABASE = {
  "小田原市": [
    {
      "name": "小田原市立病院",
      "type": "高度急性期・急性期",
      "beds": 417,
      "wardCount": 16,
      "functions": [
        "高度急性期",
        "急性期"
      ],
      "nurseCount": 270,
      "ptCount": null,
      "features": "地域医療支援病院・救命救急センター・災害拠点病院・地域がん診療連携拠点病院。2026年新築移転予定。県西地域の基幹病院。ICU・NICU完備。",
      "access": "小田原駅バス10分",
      "nightShiftType": "三交代制",
      "annualHolidays": 120,
      "salaryMin": 280000,
      "salaryMax": 380000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "充実",
      "matchingTags": [
        "高度急性期",
        "急性期",
        "救命救急",
        "災害拠点",
        "がん診療",
        "ICU",
        "NICU",
        "公立病院",
        "教育体制充実",
        "新築移転"
      ],
      "lat": 35.2564,
      "lng": 139.1551,
      "nearestStation": "小田原駅"
    },
    {
      "name": "小澤病院",
      "type": "急性期",
      "beds": 202,
      "wardCount": 4,
      "functions": [
        "急性期"
      ],
      "nurseCount": 96,
      "ptCount": null,
      "features": "脳外科・整形外科を中心とした混合病棟を持つ地域密着型総合病院。看護師96名体制。",
      "access": "小田原駅バス15分",
      "nightShiftType": "二交代制",
      "annualHolidays": 115,
      "salaryMin": 280000,
      "salaryMax": 370000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "急性期",
        "脳外科",
        "整形外科",
        "地域密着"
      ],
      "lat": 35.2564,
      "lng": 139.1551,
      "nearestStation": "小田原駅"
    },
    {
      "name": "小林病院",
      "type": "急性期・回復期・慢性期",
      "beds": 150,
      "wardCount": 3,
      "functions": [
        "急性期",
        "回復期",
        "慢性期"
      ],
      "nurseCount": 40,
      "ptCount": null,
      "features": "100年以上の歴史を持つ地域密着型病院。一般病棟・回復期リハビリテーション病棟・療養病棟を併設。",
      "access": "小田原駅バス15分",
      "nightShiftType": "二交代制",
      "annualHolidays": 115,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "急性期",
        "回復期",
        "慢性期",
        "ケアミックス",
        "回復期リハビリ",
        "地域密着"
      ],
      "lat": 35.2564,
      "lng": 139.1551,
      "nearestStation": "小田原駅"
    },
    {
      "name": "山近記念総合病院",
      "type": "急性期",
      "beds": 108,
      "wardCount": 2,
      "functions": [
        "急性期"
      ],
      "nurseCount": 59,
      "ptCount": null,
      "features": "救急病院指定。人間ドック対応。看護師59名体制。",
      "access": "小田原駅バス12分",
      "nightShiftType": "二交代制",
      "annualHolidays": 115,
      "salaryMin": 280000,
      "salaryMax": 370000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "急性期",
        "救急",
        "人間ドック"
      ],
      "lat": 35.2564,
      "lng": 139.1551,
      "nearestStation": "小田原駅"
    },
    {
      "name": "小田原循環器病院",
      "type": "高度急性期・急性期",
      "beds": 97,
      "wardCount": 3,
      "functions": [
        "高度急性期",
        "急性期"
      ],
      "nurseCount": 60,
      "ptCount": null,
      "features": "循環器専門病院。心臓カテーテル治療に強み。ハイケアユニット完備。",
      "access": "小田原駅車10分",
      "nightShiftType": "二交代制",
      "annualHolidays": 110,
      "salaryMin": 290000,
      "salaryMax": 380000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "なし",
      "matchingTags": [
        "高度急性期",
        "急性期",
        "循環器",
        "心臓カテーテル",
        "HCU",
        "専門病院"
      ],
      "lat": 35.2564,
      "lng": 139.1551,
      "nearestStation": "小田原駅"
    },
    {
      "name": "間中病院",
      "type": "急性期・回復期",
      "beds": 90,
      "wardCount": 2,
      "functions": [
        "急性期",
        "回復期"
      ],
      "nurseCount": 43,
      "ptCount": 25,
      "features": "地域包括ケア病棟・回復期リハビリテーション病棟併設。PT25名・OT9名・ST7名のリハスタッフ充実。",
      "access": "小田原駅車8分",
      "nightShiftType": "二交代制",
      "annualHolidays": 110,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": 250000,
      "ptSalaryMax": 320000,
      "educationLevel": "なし",
      "matchingTags": [
        "急性期",
        "回復期",
        "地域包括ケア",
        "回復期リハビリ",
        "リハビリ充実"
      ],
      "lat": 35.2564,
      "lng": 139.1551,
      "nearestStation": "小田原駅"
    },
    {
      "name": "箱根病院",
      "type": "慢性期",
      "beds": 199,
      "wardCount": 4,
      "functions": [
        "慢性期"
      ],
      "nurseCount": 93,
      "ptCount": null,
      "features": "国立病院機構。慢性期医療に特化。看護師93名体制。",
      "access": "小田原駅バス20分",
      "nightShiftType": "二交代制",
      "annualHolidays": 120,
      "salaryMin": 270000,
      "salaryMax": 360000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "慢性期",
        "療養",
        "国立病院機構",
        "公的病院"
      ],
      "lat": 35.2564,
      "lng": 139.1551,
      "nearestStation": "小田原駅"
    },
    {
      "name": "西湘病院",
      "type": "急性期・慢性期",
      "beds": 102,
      "wardCount": 2,
      "functions": [
        "急性期",
        "慢性期"
      ],
      "nurseCount": 30,
      "ptCount": null,
      "features": "一般病棟・療養病棟を併設。救急病院指定。",
      "access": "鴨宮駅徒歩10分",
      "nightShiftType": "二交代制",
      "annualHolidays": 115,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "急性期",
        "慢性期",
        "療養",
        "救急",
        "駅近"
      ],
      "lat": 35.2687,
      "lng": 139.176,
      "nearestStation": "鴨宮駅"
    },
    {
      "name": "丹羽病院",
      "type": "急性期",
      "beds": 51,
      "wardCount": 1,
      "functions": [
        "急性期"
      ],
      "nurseCount": 33,
      "ptCount": null,
      "features": "急性期機能病床51床。地域密着型。",
      "access": "小田原駅車10分",
      "nightShiftType": "二交代制",
      "annualHolidays": 110,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "なし",
      "matchingTags": [
        "急性期",
        "地域密着",
        "少人数"
      ],
      "lat": 35.2564,
      "lng": 139.1551,
      "nearestStation": "小田原駅"
    },
    {
      "name": "小田原市訪問看護ステーション",
      "type": "訪問看護",
      "beds": null,
      "wardCount": null,
      "functions": [
        "訪問看護"
      ],
      "nurseCount": 12,
      "ptCount": null,
      "features": "小田原市直営の訪問看護ステーション。地域包括ケアの中核として在宅医療を支える。24時間オンコール対応。",
      "access": "小田原駅バス8分",
      "nightShiftType": "オンコール",
      "annualHolidays": 125,
      "salaryMin": 310000,
      "salaryMax": 380000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "訪問看護",
        "日勤のみ",
        "オンコール",
        "公的機関",
        "ブランクOK"
      ],
      "lat": 35.2564,
      "lng": 139.1551,
      "nearestStation": "小田原駅"
    },
    {
      "name": "ケアステーション鴨宮",
      "type": "訪問看護",
      "beds": null,
      "wardCount": null,
      "functions": [
        "訪問看護"
      ],
      "nurseCount": 8,
      "ptCount": null,
      "features": "鴨宮エリアを中心に在宅療養支援を展開。小児から高齢者まで幅広く対応。スタッフ間の連携が密で働きやすい環境。",
      "access": "鴨宮駅徒歩7分",
      "nightShiftType": "オンコール",
      "annualHolidays": 120,
      "salaryMin": 300000,
      "salaryMax": 370000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "訪問看護",
        "日勤のみ",
        "オンコール",
        "駅近",
        "残業少なめ"
      ],
      "lat": 35.2687,
      "lng": 139.176,
      "nearestStation": "鴨宮駅"
    },
    {
      "name": "小田原内科・循環器クリニック",
      "type": "クリニック",
      "beds": null,
      "wardCount": null,
      "functions": [
        "外来診療"
      ],
      "nurseCount": 6,
      "ptCount": null,
      "features": "内科・循環器科を中心とした外来クリニック。心エコー・ホルター心電図等の検査対応。日勤のみで残業少なめ。",
      "access": "小田原駅徒歩5分",
      "nightShiftType": "なし",
      "annualHolidays": 125,
      "salaryMin": 260000,
      "salaryMax": 330000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "クリニック",
        "日勤のみ",
        "残業少なめ",
        "駅近",
        "パート可"
      ],
      "lat": 35.2564,
      "lng": 139.1551,
      "nearestStation": "小田原駅"
    },
    {
      "name": "足柄上クリニック",
      "type": "クリニック",
      "beds": null,
      "wardCount": null,
      "functions": [
        "外来診療"
      ],
      "nurseCount": 5,
      "ptCount": null,
      "features": "内科・小児科・皮膚科の一般外来クリニック。予防接種・健康診断にも対応。アットホームな雰囲気。",
      "access": "小田原駅車10分",
      "nightShiftType": "なし",
      "annualHolidays": 120,
      "salaryMin": 260000,
      "salaryMax": 320000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "クリニック",
        "日勤のみ",
        "残業少なめ",
        "ブランクOK",
        "パート可"
      ],
      "lat": 35.2564,
      "lng": 139.1551,
      "nearestStation": "小田原駅"
    },
    {
      "name": "介護老人保健施設こゆるぎ",
      "type": "介護老人保健施設",
      "beds": 100,
      "wardCount": null,
      "functions": [
        "介護・リハビリ"
      ],
      "nurseCount": 10,
      "ptCount": null,
      "features": "入所定員100名の介護老人保健施設。在宅復帰を目指したリハビリテーションに注力。看護・介護の連携体制が充実。",
      "access": "小田原駅バス15分",
      "nightShiftType": "オンコール",
      "annualHolidays": 115,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "介護施設",
        "日勤のみ",
        "オンコール",
        "ブランクOK",
        "残業少なめ"
      ],
      "lat": 35.2564,
      "lng": 139.1551,
      "nearestStation": "小田原駅"
    },
    {
      "name": "小田原東訪問看護ステーション",
      "type": "訪問看護",
      "beds": null,
      "wardCount": null,
      "functions": [
        "訪問看護"
      ],
      "nurseCount": 7,
      "ptCount": null,
      "features": "小田原市東部エリアの在宅医療を支える訪問看護ステーション。ターミナルケア・精神科訪問看護にも対応。",
      "access": "鴨宮駅車5分",
      "nightShiftType": "オンコール",
      "annualHolidays": 120,
      "salaryMin": 300000,
      "salaryMax": 380000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "訪問看護",
        "日勤のみ",
        "オンコール",
        "ターミナルケア",
        "精神科訪問看護"
      ],
      "lat": 35.2687,
      "lng": 139.176,
      "nearestStation": "鴨宮駅"
    }
  ],
  "秦野市": [
    {
      "name": "秦野赤十字病院",
      "type": "高度急性期・急性期・回復期",
      "beds": 308,
      "wardCount": 8,
      "functions": [
        "高度急性期",
        "急性期",
        "回復期"
      ],
      "nurseCount": 155,
      "ptCount": null,
      "features": "地域医療支援病院・救急告示病院・災害拠点病院・臨床研修指定病院。秦野市に市民病院がないため市民病院的役割を担う。HCU完備。",
      "access": "秦野駅バス10分",
      "nightShiftType": "三交代制",
      "annualHolidays": 120,
      "salaryMin": 280000,
      "salaryMax": 360000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "充実",
      "matchingTags": [
        "高度急性期",
        "急性期",
        "回復期",
        "救急",
        "災害拠点",
        "HCU",
        "臨床研修",
        "赤十字",
        "教育体制充実"
      ],
      "lat": 35.3737,
      "lng": 139.2192,
      "nearestStation": "秦野駅"
    },
    {
      "name": "鶴巻温泉病院",
      "type": "急性期・回復期・慢性期",
      "beds": 505,
      "wardCount": 10,
      "functions": [
        "急性期",
        "回復期",
        "慢性期"
      ],
      "nurseCount": 168,
      "ptCount": null,
      "features": "10病棟505床の大規模ケアミックス病院。回復期リハビリテーション・慢性期医療に強み。地域最大級の療養病院。",
      "access": "鶴巻温泉駅徒歩5分",
      "nightShiftType": "二交代制",
      "annualHolidays": 120,
      "salaryMin": 260000,
      "salaryMax": 340000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "充実",
      "matchingTags": [
        "急性期",
        "回復期",
        "慢性期",
        "ケアミックス",
        "回復期リハビリ",
        "療養",
        "大規模",
        "駅近"
      ],
      "lat": 35.369,
      "lng": 139.27,
      "nearestStation": "鶴巻温泉駅"
    },
    {
      "name": "神奈川病院",
      "type": "急性期・回復期・慢性期",
      "beds": 300,
      "wardCount": 6,
      "functions": [
        "急性期",
        "回復期",
        "慢性期"
      ],
      "nurseCount": 111,
      "ptCount": null,
      "features": "国立病院機構。呼吸器疾患・神経難病を中心とした専門医療。6病棟300床。",
      "access": "秦野駅バス15分",
      "nightShiftType": "三交代制",
      "annualHolidays": 120,
      "salaryMin": 270000,
      "salaryMax": 360000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "充実",
      "matchingTags": [
        "急性期",
        "回復期",
        "慢性期",
        "呼吸器",
        "神経難病",
        "専門医療",
        "国立病院機構",
        "公的病院"
      ],
      "lat": 35.3737,
      "lng": 139.2192,
      "nearestStation": "秦野駅"
    },
    {
      "name": "八木病院",
      "type": "急性期・回復期",
      "beds": 88,
      "wardCount": 2,
      "functions": [
        "急性期",
        "回復期"
      ],
      "nurseCount": 43,
      "ptCount": 11,
      "features": "障害者施設等入院基本料病棟・回復期リハビリテーション病棟。PT11名・OT3名のリハビリ体制。",
      "access": "秦野駅車12分",
      "nightShiftType": "二交代制",
      "annualHolidays": 110,
      "salaryMin": 260000,
      "salaryMax": 340000,
      "ptSalaryMin": 240000,
      "ptSalaryMax": 310000,
      "educationLevel": "なし",
      "matchingTags": [
        "急性期",
        "回復期",
        "回復期リハビリ",
        "障害者病棟"
      ],
      "lat": 35.3737,
      "lng": 139.2192,
      "nearestStation": "秦野駅"
    },
    {
      "name": "秦野訪問看護ステーション",
      "type": "訪問看護",
      "beds": null,
      "wardCount": null,
      "functions": [
        "訪問看護"
      ],
      "nurseCount": 10,
      "ptCount": null,
      "features": "秦野市中心部を拠点とする訪問看護ステーション。秦野赤十字病院との連携で退院後の在宅ケアを支援。",
      "access": "秦野駅徒歩10分",
      "nightShiftType": "オンコール",
      "annualHolidays": 120,
      "salaryMin": 300000,
      "salaryMax": 370000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "訪問看護",
        "日勤のみ",
        "オンコール",
        "駅近",
        "ブランクOK"
      ],
      "lat": 35.3737,
      "lng": 139.2192,
      "nearestStation": "秦野駅"
    },
    {
      "name": "ケアステーション渋沢",
      "type": "訪問看護",
      "beds": null,
      "wardCount": null,
      "functions": [
        "訪問看護"
      ],
      "nurseCount": 7,
      "ptCount": null,
      "features": "渋沢駅周辺エリアの在宅療養者を支援。呼吸器疾患・神経難病の訪問看護に実績あり。神奈川病院との連携体制。",
      "access": "渋沢駅徒歩8分",
      "nightShiftType": "オンコール",
      "annualHolidays": 120,
      "salaryMin": 300000,
      "salaryMax": 380000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "訪問看護",
        "日勤のみ",
        "オンコール",
        "駅近",
        "呼吸器",
        "神経難病"
      ],
      "lat": 35.38,
      "lng": 139.19,
      "nearestStation": "渋沢駅"
    },
    {
      "name": "秦野駅前クリニック",
      "type": "クリニック",
      "beds": null,
      "wardCount": null,
      "functions": [
        "外来診療"
      ],
      "nurseCount": 5,
      "ptCount": null,
      "features": "内科・消化器科の外来クリニック。内視鏡検査に対応。日勤のみで残業少なめ。駅前の好立地。",
      "access": "秦野駅徒歩3分",
      "nightShiftType": "なし",
      "annualHolidays": 125,
      "salaryMin": 260000,
      "salaryMax": 330000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "クリニック",
        "日勤のみ",
        "残業少なめ",
        "駅近",
        "パート可"
      ],
      "lat": 35.3737,
      "lng": 139.2192,
      "nearestStation": "秦野駅"
    },
    {
      "name": "秦野中央介護老人保健施設",
      "type": "介護老人保健施設",
      "beds": 80,
      "wardCount": null,
      "functions": [
        "介護・リハビリ"
      ],
      "nurseCount": 8,
      "ptCount": null,
      "features": "入所定員80名の介護老人保健施設。在宅復帰支援に注力。リハビリスタッフとの連携が密。デイケア併設。",
      "access": "秦野駅バス10分",
      "nightShiftType": "オンコール",
      "annualHolidays": 115,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "介護施設",
        "日勤のみ",
        "オンコール",
        "ブランクOK",
        "残業少なめ"
      ],
      "lat": 35.3737,
      "lng": 139.2192,
      "nearestStation": "秦野駅"
    },
    {
      "name": "秦野南訪問看護ステーション",
      "type": "訪問看護",
      "beds": null,
      "wardCount": null,
      "functions": [
        "訪問看護"
      ],
      "nurseCount": 6,
      "ptCount": null,
      "features": "秦野市南部・東海大学前駅周辺を中心に活動。小児訪問看護にも対応。子育て中のスタッフが多く働きやすい環境。",
      "access": "東海大学前駅徒歩10分",
      "nightShiftType": "オンコール",
      "annualHolidays": 122,
      "salaryMin": 300000,
      "salaryMax": 370000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "訪問看護",
        "日勤のみ",
        "オンコール",
        "託児所あり",
        "ブランクOK"
      ],
      "lat": 35.366,
      "lng": 139.254,
      "nearestStation": "東海大学前駅"
    }
  ],
  "平塚市": [
    {
      "name": "平塚共済病院",
      "type": "高度急性期・急性期",
      "beds": 441,
      "wardCount": 11,
      "functions": [
        "高度急性期",
        "急性期"
      ],
      "nurseCount": 301,
      "ptCount": null,
      "features": "地域医療支援病院・救急告示病院・災害拠点指定病院。心臓センター・救急センター・脳卒中センター・周産期センター併設。看護師301名は平塚最大。",
      "access": "平塚駅バス8分",
      "nightShiftType": "三交代制",
      "annualHolidays": 120,
      "salaryMin": 290000,
      "salaryMax": 380000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "充実",
      "matchingTags": [
        "高度急性期",
        "急性期",
        "救急",
        "災害拠点",
        "心臓センター",
        "脳卒中",
        "周産期",
        "教育体制充実",
        "公的病院"
      ],
      "lat": 35.328,
      "lng": 139.3497,
      "nearestStation": "平塚駅"
    },
    {
      "name": "平塚市民病院",
      "type": "高度急性期・急性期",
      "beds": 412,
      "wardCount": 13,
      "functions": [
        "高度急性期",
        "急性期"
      ],
      "nurseCount": 315,
      "ptCount": null,
      "features": "救急告示病院・災害拠点指定病院。ICU/CCU・HCU完備。看護師315名。平塚市の基幹病院。産科・小児科も充実。",
      "access": "平塚駅バス10分",
      "nightShiftType": "三交代制",
      "annualHolidays": 120,
      "salaryMin": 290000,
      "salaryMax": 380000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "充実",
      "matchingTags": [
        "高度急性期",
        "急性期",
        "救急",
        "災害拠点",
        "ICU",
        "CCU",
        "HCU",
        "産科",
        "小児科",
        "公立病院",
        "教育体制充実"
      ],
      "lat": 35.328,
      "lng": 139.3497,
      "nearestStation": "平塚駅"
    },
    {
      "name": "済生会湘南平塚病院",
      "type": "急性期・回復期",
      "beds": 176,
      "wardCount": 4,
      "functions": [
        "急性期",
        "回復期"
      ],
      "nurseCount": 76,
      "ptCount": 10,
      "features": "一般病棟・地域包括ケア病棟・回復期リハビリテーション病棟を併設。急性期病院と在宅をつなぐハブ機能。PT10名・OT6名。",
      "access": "平塚駅バス12分",
      "nightShiftType": "二交代制",
      "annualHolidays": 115,
      "salaryMin": 270000,
      "salaryMax": 360000,
      "ptSalaryMin": 250000,
      "ptSalaryMax": 320000,
      "educationLevel": "あり",
      "matchingTags": [
        "急性期",
        "回復期",
        "地域包括ケア",
        "回復期リハビリ",
        "済生会"
      ],
      "lat": 35.328,
      "lng": 139.3497,
      "nearestStation": "平塚駅"
    },
    {
      "name": "高根台病院",
      "type": "慢性期",
      "beds": 236,
      "wardCount": 4,
      "functions": [
        "慢性期"
      ],
      "nurseCount": 57,
      "ptCount": null,
      "features": "療養型4病棟236床。慢性期医療に特化。",
      "access": "平塚駅バス15分",
      "nightShiftType": "二交代制",
      "annualHolidays": 115,
      "salaryMin": 250000,
      "salaryMax": 340000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "慢性期",
        "療養"
      ],
      "lat": 35.328,
      "lng": 139.3497,
      "nearestStation": "平塚駅"
    },
    {
      "name": "平塚十全病院",
      "type": "慢性期",
      "beds": 230,
      "wardCount": 4,
      "functions": [
        "慢性期"
      ],
      "nurseCount": 48,
      "ptCount": null,
      "features": "慢性期療養病院。230床。",
      "access": "平塚駅バス20分",
      "nightShiftType": "二交代制",
      "annualHolidays": 115,
      "salaryMin": 250000,
      "salaryMax": 340000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "慢性期",
        "療養"
      ],
      "lat": 35.328,
      "lng": 139.3497,
      "nearestStation": "平塚駅"
    },
    {
      "name": "ふれあい平塚ホスピタル",
      "type": "回復期・慢性期",
      "beds": 125,
      "wardCount": 3,
      "functions": [
        "回復期",
        "慢性期"
      ],
      "nurseCount": 39,
      "ptCount": 32,
      "features": "回復期リハビリテーション病棟・慢性期病棟。PT32名・OT12名・ST5名のリハスタッフ充実。",
      "access": "平塚駅バス10分",
      "nightShiftType": "二交代制",
      "annualHolidays": 115,
      "salaryMin": 260000,
      "salaryMax": 350000,
      "ptSalaryMin": 250000,
      "ptSalaryMax": 320000,
      "educationLevel": "あり",
      "matchingTags": [
        "回復期",
        "慢性期",
        "回復期リハビリ",
        "リハビリ充実"
      ],
      "lat": 35.328,
      "lng": 139.3497,
      "nearestStation": "平塚駅"
    },
    {
      "name": "平塚訪問看護ステーション",
      "type": "訪問看護",
      "beds": null,
      "wardCount": null,
      "functions": [
        "訪問看護"
      ],
      "nurseCount": 11,
      "ptCount": null,
      "features": "平塚市中心部の訪問看護ステーション。平塚共済病院・平塚市民病院からの退院患者を中心にフォロー。ターミナルケアの実績豊富。",
      "access": "平塚駅徒歩12分",
      "nightShiftType": "オンコール",
      "annualHolidays": 120,
      "salaryMin": 310000,
      "salaryMax": 380000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "訪問看護",
        "日勤のみ",
        "オンコール",
        "ターミナルケア",
        "ブランクOK"
      ],
      "lat": 35.328,
      "lng": 139.3497,
      "nearestStation": "平塚駅"
    },
    {
      "name": "湘南ケアステーション平塚",
      "type": "訪問看護",
      "beds": null,
      "wardCount": null,
      "functions": [
        "訪問看護"
      ],
      "nurseCount": 8,
      "ptCount": null,
      "features": "平塚市西部エリアを中心に展開。リハビリ職も在籍し、訪問看護と訪問リハビリを一体的に提供。",
      "access": "平塚駅バス10分",
      "nightShiftType": "オンコール",
      "annualHolidays": 120,
      "salaryMin": 300000,
      "salaryMax": 370000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "訪問看護",
        "日勤のみ",
        "オンコール",
        "残業少なめ",
        "ブランクOK"
      ],
      "lat": 35.328,
      "lng": 139.3497,
      "nearestStation": "平塚駅"
    },
    {
      "name": "平塚駅南口クリニック",
      "type": "クリニック",
      "beds": null,
      "wardCount": null,
      "functions": [
        "外来診療"
      ],
      "nurseCount": 6,
      "ptCount": null,
      "features": "内科・整形外科の外来クリニック。リハビリテーション科併設。駅南口徒歩2分の好立地。日勤のみ。",
      "access": "平塚駅南口徒歩2分",
      "nightShiftType": "なし",
      "annualHolidays": 125,
      "salaryMin": 265000,
      "salaryMax": 340000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "クリニック",
        "日勤のみ",
        "残業少なめ",
        "駅近",
        "パート可"
      ],
      "lat": 35.328,
      "lng": 139.3497,
      "nearestStation": "平塚駅"
    },
    {
      "name": "介護老人保健施設湘南の丘",
      "type": "介護老人保健施設",
      "beds": 100,
      "wardCount": null,
      "functions": [
        "介護・リハビリ"
      ],
      "nurseCount": 12,
      "ptCount": null,
      "features": "入所定員100名。在宅復帰率が高く、リハビリプログラムが充実。通所リハビリ・ショートステイも併設。",
      "access": "平塚駅バス15分",
      "nightShiftType": "オンコール",
      "annualHolidays": 115,
      "salaryMin": 275000,
      "salaryMax": 360000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "介護施設",
        "日勤のみ",
        "オンコール",
        "ブランクOK",
        "残業少なめ"
      ],
      "lat": 35.328,
      "lng": 139.3497,
      "nearestStation": "平塚駅"
    },
    {
      "name": "湘南訪問看護ステーション平塚",
      "type": "訪問看護",
      "beds": null,
      "wardCount": null,
      "functions": [
        "訪問看護"
      ],
      "nurseCount": 9,
      "ptCount": null,
      "features": "平塚市北部・金目エリアを中心にサービス提供。精神科訪問看護にも対応。直行直帰制度あり。",
      "access": "平塚駅バス20分",
      "nightShiftType": "オンコール",
      "annualHolidays": 120,
      "salaryMin": 305000,
      "salaryMax": 375000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "訪問看護",
        "日勤のみ",
        "オンコール",
        "精神科訪問看護",
        "直行直帰"
      ],
      "lat": 35.328,
      "lng": 139.3497,
      "nearestStation": "平塚駅"
    }
  ],
  "藤沢市": [
    {
      "name": "藤沢市民病院",
      "type": "高度急性期・急性期",
      "beds": 530,
      "wardCount": 15,
      "functions": [
        "高度急性期",
        "急性期"
      ],
      "nurseCount": 405,
      "ptCount": null,
      "features": "地域医療支援病院・救命救急センター・災害医療拠点病院・地域がん診療連携拠点病院。ICU/CCU・NICU完備。看護師405名。湘南東部保健医療圏の基幹病院。",
      "access": "藤沢本町駅徒歩15分、藤沢駅バス10分",
      "nightShiftType": "三交代制",
      "annualHolidays": 120,
      "salaryMin": 300000,
      "salaryMax": 390000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "充実",
      "matchingTags": [
        "高度急性期",
        "急性期",
        "救命救急",
        "災害拠点",
        "がん診療",
        "ICU",
        "CCU",
        "NICU",
        "公立病院",
        "教育体制充実"
      ],
      "lat": 35.338,
      "lng": 139.487,
      "nearestStation": "藤沢駅"
    },
    {
      "name": "湘南藤沢徳洲会病院",
      "type": "高度急性期・急性期",
      "beds": 419,
      "wardCount": 11,
      "functions": [
        "高度急性期",
        "急性期"
      ],
      "nurseCount": 282,
      "ptCount": null,
      "features": "2012年新築移転。24時間365日救急対応。心臓病センター・ICU完備。看護師282名。",
      "access": "辻堂駅徒歩7分",
      "nightShiftType": "三交代制",
      "annualHolidays": 120,
      "salaryMin": 290000,
      "salaryMax": 380000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "充実",
      "matchingTags": [
        "高度急性期",
        "急性期",
        "救急",
        "心臓病センター",
        "ICU",
        "24時間救急",
        "徳洲会",
        "駅近"
      ],
      "lat": 35.335,
      "lng": 139.448,
      "nearestStation": "辻堂駅"
    },
    {
      "name": "藤沢湘南台病院",
      "type": "高度急性期・急性期・回復期・慢性期",
      "beds": 330,
      "wardCount": 8,
      "functions": [
        "高度急性期",
        "急性期",
        "回復期",
        "慢性期"
      ],
      "nurseCount": 169,
      "ptCount": null,
      "features": "急性期一般病棟・回復期リハビリ病棟・緩和ケア病棟・療養病棟の4機能併設。看護師169名。",
      "access": "湘南台駅バス5分",
      "nightShiftType": "三交代制",
      "annualHolidays": 120,
      "salaryMin": 280000,
      "salaryMax": 370000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "充実",
      "matchingTags": [
        "高度急性期",
        "急性期",
        "回復期",
        "慢性期",
        "ケアミックス",
        "回復期リハビリ",
        "緩和ケア"
      ],
      "lat": 35.39,
      "lng": 139.468,
      "nearestStation": "湘南台駅"
    },
    {
      "name": "湘南慶育病院",
      "type": "急性期・回復期",
      "beds": 230,
      "wardCount": 5,
      "functions": [
        "急性期",
        "回復期"
      ],
      "nurseCount": 87,
      "ptCount": 16,
      "features": "回復期リハビリ100床・地域包括ケア50床・療養50床・一般30床。先進的医療ICT活用。PT16名・OT9名。",
      "access": "湘南台駅バス15分",
      "nightShiftType": "二交代制",
      "annualHolidays": 115,
      "salaryMin": 280000,
      "salaryMax": 370000,
      "ptSalaryMin": 260000,
      "ptSalaryMax": 330000,
      "educationLevel": "あり",
      "matchingTags": [
        "急性期",
        "回復期",
        "回復期リハビリ",
        "地域包括ケア",
        "ICT活用"
      ],
      "lat": 35.39,
      "lng": 139.468,
      "nearestStation": "湘南台駅"
    },
    {
      "name": "湘南中央病院",
      "type": "急性期・回復期・慢性期",
      "beds": 199,
      "wardCount": 5,
      "functions": [
        "急性期",
        "回復期",
        "慢性期"
      ],
      "nurseCount": 83,
      "ptCount": null,
      "features": "急性期・回復期リハビリ・緩和ケア・地域包括ケア・療養の5病棟。PT7名・OT7名。",
      "access": "藤沢駅バス10分",
      "nightShiftType": "二交代制",
      "annualHolidays": 115,
      "salaryMin": 280000,
      "salaryMax": 370000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "急性期",
        "回復期",
        "慢性期",
        "ケアミックス",
        "緩和ケア",
        "地域包括ケア"
      ],
      "lat": 35.338,
      "lng": 139.487,
      "nearestStation": "藤沢駅"
    },
    {
      "name": "クローバーホスピタル",
      "type": "回復期・慢性期",
      "beds": 170,
      "wardCount": 4,
      "functions": [
        "回復期",
        "慢性期"
      ],
      "nurseCount": 66,
      "ptCount": 35,
      "features": "回復期リハビリ60床・地域包括ケア46床・特殊疾患33床。PT35名・OT14名・ST8名のリハスタッフ非常に充実。",
      "access": "藤沢駅バス15分",
      "nightShiftType": "二交代制",
      "annualHolidays": 115,
      "salaryMin": 270000,
      "salaryMax": 360000,
      "ptSalaryMin": 260000,
      "ptSalaryMax": 330000,
      "educationLevel": "あり",
      "matchingTags": [
        "回復期",
        "慢性期",
        "回復期リハビリ",
        "地域包括ケア",
        "リハビリ充実"
      ],
      "lat": 35.338,
      "lng": 139.487,
      "nearestStation": "藤沢駅"
    },
    {
      "name": "山内病院",
      "type": "回復期・慢性期",
      "beds": 152,
      "wardCount": 2,
      "functions": [
        "回復期",
        "慢性期"
      ],
      "nurseCount": 38,
      "ptCount": null,
      "features": "障害者施設等入院基本料病棟・地域包括ケア病棟。",
      "access": "藤沢駅バス20分",
      "nightShiftType": "二交代制",
      "annualHolidays": 115,
      "salaryMin": 270000,
      "salaryMax": 360000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "回復期",
        "慢性期",
        "障害者病棟",
        "地域包括ケア",
        "徳洲会"
      ],
      "lat": 35.338,
      "lng": 139.487,
      "nearestStation": "藤沢駅"
    },
    {
      "name": "藤沢訪問看護ステーション",
      "type": "訪問看護",
      "beds": null,
      "wardCount": null,
      "functions": [
        "訪問看護"
      ],
      "nurseCount": 14,
      "ptCount": null,
      "features": "藤沢市中心部の大規模訪問看護ステーション。藤沢市民病院との連携体制が充実。がん末期・難病の在宅ケアに強み。",
      "access": "藤沢駅徒歩10分",
      "nightShiftType": "オンコール",
      "annualHolidays": 122,
      "salaryMin": 320000,
      "salaryMax": 400000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "充実",
      "matchingTags": [
        "訪問看護",
        "日勤のみ",
        "オンコール",
        "駅近",
        "ターミナルケア"
      ],
      "lat": 35.338,
      "lng": 139.487,
      "nearestStation": "藤沢駅"
    },
    {
      "name": "湘南台ケアステーション",
      "type": "訪問看護",
      "beds": null,
      "wardCount": null,
      "functions": [
        "訪問看護"
      ],
      "nurseCount": 9,
      "ptCount": null,
      "features": "湘南台駅周辺を中心に活動。小児から高齢者まで幅広く対応。藤沢湘南台病院との病診連携あり。",
      "access": "湘南台駅徒歩5分",
      "nightShiftType": "オンコール",
      "annualHolidays": 120,
      "salaryMin": 310000,
      "salaryMax": 385000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "訪問看護",
        "日勤のみ",
        "オンコール",
        "駅近",
        "ブランクOK"
      ],
      "lat": 35.39,
      "lng": 139.468,
      "nearestStation": "湘南台駅"
    },
    {
      "name": "辻堂駅前クリニック",
      "type": "クリニック",
      "beds": null,
      "wardCount": null,
      "functions": [
        "外来診療"
      ],
      "nurseCount": 7,
      "ptCount": null,
      "features": "内科・呼吸器科・アレルギー科の外来クリニック。辻堂駅前の再開発エリアに立地。日勤のみで残業ほぼなし。",
      "access": "辻堂駅徒歩3分",
      "nightShiftType": "なし",
      "annualHolidays": 125,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "クリニック",
        "日勤のみ",
        "残業少なめ",
        "駅近",
        "パート可"
      ],
      "lat": 35.335,
      "lng": 139.448,
      "nearestStation": "辻堂駅"
    },
    {
      "name": "介護老人保健施設ハートケア藤沢",
      "type": "介護老人保健施設",
      "beds": 120,
      "wardCount": null,
      "functions": [
        "介護・リハビリ"
      ],
      "nurseCount": 15,
      "ptCount": null,
      "features": "入所定員120名の大規模介護老人保健施設。在宅復帰支援プログラムが充実。通所リハビリ・訪問リハビリも併設。託児所完備。",
      "access": "藤沢駅バス12分",
      "nightShiftType": "オンコール",
      "annualHolidays": 118,
      "salaryMin": 280000,
      "salaryMax": 360000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "介護施設",
        "日勤のみ",
        "オンコール",
        "ブランクOK",
        "託児所あり",
        "残業少なめ"
      ],
      "lat": 35.338,
      "lng": 139.487,
      "nearestStation": "藤沢駅"
    },
    {
      "name": "湘南訪問看護ステーション藤沢",
      "type": "訪問看護",
      "beds": null,
      "wardCount": null,
      "functions": [
        "訪問看護"
      ],
      "nurseCount": 8,
      "ptCount": null,
      "features": "藤沢市南部・鵠沼エリアを中心に活動。精神科訪問看護にも注力。直行直帰制度あり。週休2日制。",
      "access": "藤沢駅バス8分",
      "nightShiftType": "オンコール",
      "annualHolidays": 120,
      "salaryMin": 305000,
      "salaryMax": 380000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "訪問看護",
        "日勤のみ",
        "オンコール",
        "精神科訪問看護",
        "直行直帰"
      ],
      "lat": 35.338,
      "lng": 139.487,
      "nearestStation": "藤沢駅"
    }
  ],
  "茅ヶ崎市": [
    {
      "name": "茅ヶ崎市立病院",
      "type": "高度急性期・急性期",
      "beds": 401,
      "wardCount": 10,
      "functions": [
        "高度急性期",
        "急性期"
      ],
      "nurseCount": 216,
      "ptCount": null,
      "features": "地域医療支援病院・災害拠点病院・DMAT指定病院。ICU・NICU完備。人工関節手術支援ロボットMako導入。看護師216名。",
      "access": "北茅ヶ崎駅徒歩10分",
      "nightShiftType": "三交代制",
      "annualHolidays": 120,
      "salaryMin": 290000,
      "salaryMax": 380000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "充実",
      "matchingTags": [
        "高度急性期",
        "急性期",
        "災害拠点",
        "DMAT",
        "ICU",
        "NICU",
        "ロボット手術",
        "公立病院",
        "教育体制充実"
      ],
      "lat": 35.334,
      "lng": 139.404,
      "nearestStation": "茅ヶ崎駅"
    },
    {
      "name": "茅ヶ崎中央病院",
      "type": "急性期・回復期・慢性期",
      "beds": 324,
      "wardCount": 6,
      "functions": [
        "急性期",
        "回復期",
        "慢性期"
      ],
      "nurseCount": 135,
      "ptCount": 20,
      "features": "一般268床・療養・回復期のケアミックス型。救急告示病院。PT20名・OT9名。茅ヶ崎駅徒歩6分の好立地。",
      "access": "茅ヶ崎駅徒歩6分",
      "nightShiftType": "二交代制",
      "annualHolidays": 120,
      "salaryMin": 280000,
      "salaryMax": 370000,
      "ptSalaryMin": 250000,
      "ptSalaryMax": 320000,
      "educationLevel": "充実",
      "matchingTags": [
        "急性期",
        "回復期",
        "慢性期",
        "ケアミックス",
        "救急",
        "駅近"
      ],
      "lat": 35.334,
      "lng": 139.404,
      "nearestStation": "茅ヶ崎駅"
    },
    {
      "name": "湘南東部総合病院",
      "type": "高度急性期・急性期・回復期・慢性期",
      "beds": 323,
      "wardCount": 9,
      "functions": [
        "高度急性期",
        "急性期",
        "回復期",
        "慢性期"
      ],
      "nurseCount": 176,
      "ptCount": 10,
      "features": "ICU完備。回復期病棟40床・緩和病棟20床併設。4機能すべてを持つ総合病院。看護師176名。",
      "access": "茅ヶ崎駅バス10分",
      "nightShiftType": "三交代制",
      "annualHolidays": 120,
      "salaryMin": 280000,
      "salaryMax": 370000,
      "ptSalaryMin": 250000,
      "ptSalaryMax": 320000,
      "educationLevel": "充実",
      "matchingTags": [
        "高度急性期",
        "急性期",
        "回復期",
        "慢性期",
        "ケアミックス",
        "ICU",
        "緩和ケア"
      ],
      "lat": 35.334,
      "lng": 139.404,
      "nearestStation": "茅ヶ崎駅"
    },
    {
      "name": "茅ヶ崎徳洲会病院",
      "type": "高度急性期・急性期",
      "beds": 132,
      "wardCount": 4,
      "functions": [
        "高度急性期",
        "急性期"
      ],
      "nurseCount": 70,
      "ptCount": null,
      "features": "急性期・HCU完備。PT7名・OT3名。",
      "access": "茅ヶ崎駅バス5分",
      "nightShiftType": "二交代制",
      "annualHolidays": 115,
      "salaryMin": 280000,
      "salaryMax": 370000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "高度急性期",
        "急性期",
        "HCU",
        "徳洲会"
      ],
      "lat": 35.334,
      "lng": 139.404,
      "nearestStation": "茅ヶ崎駅"
    },
    {
      "name": "長岡病院",
      "type": "慢性期",
      "beds": 162,
      "wardCount": 3,
      "functions": [
        "慢性期"
      ],
      "nurseCount": 30,
      "ptCount": null,
      "features": "療養型3病棟162床。慢性期医療に特化。",
      "access": "茅ヶ崎駅車15分",
      "nightShiftType": "二交代制",
      "annualHolidays": 115,
      "salaryMin": 250000,
      "salaryMax": 340000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "慢性期",
        "療養"
      ],
      "lat": 35.334,
      "lng": 139.404,
      "nearestStation": "茅ヶ崎駅"
    },
    {
      "name": "茅ヶ崎新北陵病院",
      "type": "回復期・慢性期",
      "beds": 152,
      "wardCount": 3,
      "functions": [
        "回復期",
        "慢性期"
      ],
      "nurseCount": 41,
      "ptCount": null,
      "features": "回復期リハビリ・慢性期療養。",
      "access": "香川駅徒歩16分",
      "nightShiftType": "二交代制",
      "annualHolidays": 115,
      "salaryMin": 260000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "回復期",
        "慢性期",
        "回復期リハビリ",
        "療養"
      ],
      "lat": 35.357,
      "lng": 139.378,
      "nearestStation": "香川駅"
    },
    {
      "name": "茅ヶ崎訪問看護ステーション",
      "type": "訪問看護",
      "beds": null,
      "wardCount": null,
      "functions": [
        "訪問看護"
      ],
      "nurseCount": 10,
      "ptCount": null,
      "features": "茅ヶ崎市中心部の訪問看護ステーション。茅ヶ崎市立病院からの退院患者フォローに実績あり。がん末期の在宅ケアに強み。",
      "access": "茅ヶ崎駅徒歩8分",
      "nightShiftType": "オンコール",
      "annualHolidays": 120,
      "salaryMin": 310000,
      "salaryMax": 385000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "訪問看護",
        "日勤のみ",
        "オンコール",
        "駅近",
        "ターミナルケア"
      ],
      "lat": 35.334,
      "lng": 139.404,
      "nearestStation": "茅ヶ崎駅"
    },
    {
      "name": "湘南ケアステーション茅ヶ崎",
      "type": "訪問看護",
      "beds": null,
      "wardCount": null,
      "functions": [
        "訪問看護"
      ],
      "nurseCount": 7,
      "ptCount": null,
      "features": "茅ヶ崎市北部・香川エリアを中心に展開。認知症ケア・精神科訪問看護にも対応。少人数で風通しの良い職場。",
      "access": "香川駅徒歩10分",
      "nightShiftType": "オンコール",
      "annualHolidays": 120,
      "salaryMin": 300000,
      "salaryMax": 375000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "訪問看護",
        "日勤のみ",
        "オンコール",
        "精神科訪問看護",
        "残業少なめ"
      ],
      "lat": 35.357,
      "lng": 139.378,
      "nearestStation": "香川駅"
    },
    {
      "name": "茅ヶ崎南口クリニック",
      "type": "クリニック",
      "beds": null,
      "wardCount": null,
      "functions": [
        "外来診療"
      ],
      "nurseCount": 5,
      "ptCount": null,
      "features": "内科・糖尿病内科・生活習慣病外来のクリニック。患者指導・療養相談が中心。日勤のみ。",
      "access": "茅ヶ崎駅南口徒歩3分",
      "nightShiftType": "なし",
      "annualHolidays": 125,
      "salaryMin": 265000,
      "salaryMax": 340000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "クリニック",
        "日勤のみ",
        "残業少なめ",
        "駅近",
        "パート可"
      ],
      "lat": 35.334,
      "lng": 139.404,
      "nearestStation": "茅ヶ崎駅"
    },
    {
      "name": "介護老人保健施設サンケア茅ヶ崎",
      "type": "介護老人保健施設",
      "beds": 90,
      "wardCount": null,
      "functions": [
        "介護・リハビリ"
      ],
      "nurseCount": 10,
      "ptCount": null,
      "features": "入所定員90名。在宅復帰率が高い。リハビリ・デイケア・ショートステイを併設。湘南の海が近く明るい環境。",
      "access": "茅ヶ崎駅バス12分",
      "nightShiftType": "オンコール",
      "annualHolidays": 115,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "介護施設",
        "日勤のみ",
        "オンコール",
        "ブランクOK",
        "残業少なめ"
      ],
      "lat": 35.334,
      "lng": 139.404,
      "nearestStation": "茅ヶ崎駅"
    },
    {
      "name": "茅ヶ崎東訪問看護ステーション",
      "type": "訪問看護",
      "beds": null,
      "wardCount": null,
      "functions": [
        "訪問看護"
      ],
      "nurseCount": 6,
      "ptCount": null,
      "features": "茅ヶ崎市東部・湘南東部総合病院との連携で在宅医療を支援。リハビリスタッフも在籍。",
      "access": "北茅ヶ崎駅徒歩12分",
      "nightShiftType": "オンコール",
      "annualHolidays": 120,
      "salaryMin": 300000,
      "salaryMax": 370000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "訪問看護",
        "日勤のみ",
        "オンコール",
        "ブランクOK",
        "残業少なめ"
      ],
      "lat": 35.334,
      "lng": 139.404,
      "nearestStation": "茅ヶ崎駅"
    }
  ],
  "大磯町・二宮町": [
    {
      "name": "湘南大磯病院",
      "type": "高度急性期・急性期",
      "beds": 312,
      "wardCount": 8,
      "functions": [
        "高度急性期",
        "急性期"
      ],
      "nurseCount": 90,
      "ptCount": null,
      "features": "中郡（大磯・二宮）唯一の総合病院。24時間救急対応。8病棟312床。一部休棟中で看護師需要あり。",
      "access": "大磯駅・二宮駅よりシャトルバス運行",
      "nightShiftType": "二交代制",
      "annualHolidays": 120,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "充実",
      "matchingTags": [
        "高度急性期",
        "急性期",
        "24時間救急",
        "徳洲会",
        "看護師増員中"
      ],
      "lat": 35.312,
      "lng": 139.311,
      "nearestStation": "大磯駅"
    },
    {
      "name": "大磯訪問看護ステーション",
      "type": "訪問看護",
      "beds": null,
      "wardCount": null,
      "functions": [
        "訪問看護"
      ],
      "nurseCount": 6,
      "ptCount": null,
      "features": "大磯町・二宮町エリアの在宅医療を支える訪問看護ステーション。高齢化率の高い地域で在宅ケアの需要大。湘南大磯病院との連携体制あり。",
      "access": "大磯駅徒歩8分",
      "nightShiftType": "オンコール",
      "annualHolidays": 120,
      "salaryMin": 300000,
      "salaryMax": 370000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "訪問看護",
        "日勤のみ",
        "オンコール",
        "駅近",
        "ブランクOK"
      ],
      "lat": 35.312,
      "lng": 139.311,
      "nearestStation": "大磯駅"
    },
    {
      "name": "二宮クリニック",
      "type": "クリニック",
      "beds": null,
      "wardCount": null,
      "functions": [
        "外来診療"
      ],
      "nurseCount": 4,
      "ptCount": null,
      "features": "内科・老年内科の外来クリニック。地域のかかりつけ医として高齢者の健康管理に注力。アットホームな職場。",
      "access": "二宮駅徒歩5分",
      "nightShiftType": "なし",
      "annualHolidays": 120,
      "salaryMin": 260000,
      "salaryMax": 320000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "クリニック",
        "日勤のみ",
        "残業少なめ",
        "駅近",
        "ブランクOK",
        "パート可"
      ],
      "lat": 35.299,
      "lng": 139.255,
      "nearestStation": "二宮駅"
    },
    {
      "name": "介護老人保健施設湘南大磯",
      "type": "介護老人保健施設",
      "beds": 60,
      "wardCount": null,
      "functions": [
        "介護・リハビリ"
      ],
      "nurseCount": 7,
      "ptCount": null,
      "features": "入所定員60名。相模湾を望む環境の良い介護老人保健施設。在宅復帰支援とデイケアを併設。少人数で家庭的な雰囲気。",
      "access": "大磯駅バス10分",
      "nightShiftType": "オンコール",
      "annualHolidays": 115,
      "salaryMin": 270000,
      "salaryMax": 345000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "介護施設",
        "日勤のみ",
        "オンコール",
        "ブランクOK",
        "残業少なめ",
        "少人数"
      ],
      "lat": 35.312,
      "lng": 139.311,
      "nearestStation": "大磯駅"
    }
  ],
  "南足柄市・開成町・大井町": [
    {
      "name": "勝又高台病院",
      "type": "慢性期",
      "beds": 310,
      "wardCount": 6,
      "functions": [
        "慢性期"
      ],
      "nurseCount": 71,
      "ptCount": null,
      "features": "6病棟310床の大規模療養型病院。慢性期医療に特化。看護師71名。",
      "access": "開成駅車5分",
      "nightShiftType": "二交代制",
      "annualHolidays": 115,
      "salaryMin": 250000,
      "salaryMax": 340000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "充実",
      "matchingTags": [
        "慢性期",
        "療養",
        "大規模"
      ],
      "lat": 35.335,
      "lng": 139.148,
      "nearestStation": "開成駅"
    },
    {
      "name": "北小田原病院",
      "type": "慢性期",
      "beds": 55,
      "wardCount": 1,
      "functions": [
        "慢性期"
      ],
      "nurseCount": 14,
      "ptCount": null,
      "features": "療養型病院。",
      "access": "大雄山駅車5分",
      "nightShiftType": "二交代制",
      "annualHolidays": 110,
      "salaryMin": 250000,
      "salaryMax": 330000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "なし",
      "matchingTags": [
        "慢性期",
        "療養",
        "少人数"
      ],
      "lat": 35.33,
      "lng": 139.11,
      "nearestStation": "大雄山駅"
    },
    {
      "name": "大内病院",
      "type": "急性期",
      "beds": 53,
      "wardCount": 1,
      "functions": [
        "急性期"
      ],
      "nurseCount": 15,
      "ptCount": 5,
      "features": "南足柄市唯一の急性期病院。53床。PT5名。",
      "access": "和田河原駅徒歩5分",
      "nightShiftType": "二交代制",
      "annualHolidays": 110,
      "salaryMin": 260000,
      "salaryMax": 340000,
      "ptSalaryMin": 230000,
      "ptSalaryMax": 300000,
      "educationLevel": "なし",
      "matchingTags": [
        "急性期",
        "少人数",
        "駅近"
      ],
      "lat": 35.323,
      "lng": 139.121,
      "nearestStation": "和田河原駅"
    },
    {
      "name": "佐藤病院",
      "type": "慢性期",
      "beds": 60,
      "wardCount": 1,
      "functions": [
        "慢性期"
      ],
      "nurseCount": 13,
      "ptCount": null,
      "features": "療養型病院60床。",
      "access": "上大井駅車5分",
      "nightShiftType": "二交代制",
      "annualHolidays": 110,
      "salaryMin": 250000,
      "salaryMax": 330000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "なし",
      "matchingTags": [
        "慢性期",
        "療養",
        "少人数"
      ],
      "lat": null,
      "lng": null,
      "nearestStation": null
    },
    {
      "name": "南足柄訪問看護ステーション",
      "type": "訪問看護",
      "beds": null,
      "wardCount": null,
      "functions": [
        "訪問看護"
      ],
      "nurseCount": 6,
      "ptCount": null,
      "features": "南足柄市を中心に足柄平野エリアの在宅医療を支援。山間部への訪問にも対応。車通勤必須。",
      "access": "大雄山駅徒歩10分",
      "nightShiftType": "オンコール",
      "annualHolidays": 120,
      "salaryMin": 300000,
      "salaryMax": 370000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "訪問看護",
        "日勤のみ",
        "オンコール",
        "ブランクOK",
        "残業少なめ"
      ],
      "lat": 35.33,
      "lng": 139.11,
      "nearestStation": "大雄山駅"
    },
    {
      "name": "ケアステーション開成",
      "type": "訪問看護",
      "beds": null,
      "wardCount": null,
      "functions": [
        "訪問看護"
      ],
      "nurseCount": 5,
      "ptCount": null,
      "features": "開成町・大井町エリアの訪問看護ステーション。新興住宅地の高齢者を中心にサービス提供。少人数でアットホーム。",
      "access": "開成駅徒歩7分",
      "nightShiftType": "オンコール",
      "annualHolidays": 120,
      "salaryMin": 295000,
      "salaryMax": 365000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "訪問看護",
        "日勤のみ",
        "オンコール",
        "駅近",
        "少人数",
        "ブランクOK"
      ],
      "lat": 35.335,
      "lng": 139.148,
      "nearestStation": "開成駅"
    },
    {
      "name": "南足柄クリニック",
      "type": "クリニック",
      "beds": null,
      "wardCount": null,
      "functions": [
        "外来診療"
      ],
      "nurseCount": 4,
      "ptCount": null,
      "features": "内科・外科・整形外科の外来クリニック。地域のかかりつけ医として幅広い症例に対応。日勤のみ。",
      "access": "和田河原駅徒歩3分",
      "nightShiftType": "なし",
      "annualHolidays": 120,
      "salaryMin": 255000,
      "salaryMax": 320000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "クリニック",
        "日勤のみ",
        "残業少なめ",
        "駅近",
        "パート可",
        "ブランクOK"
      ],
      "lat": 35.323,
      "lng": 139.121,
      "nearestStation": "和田河原駅"
    },
    {
      "name": "介護老人保健施設あしがら",
      "type": "介護老人保健施設",
      "beds": 80,
      "wardCount": null,
      "functions": [
        "介護・リハビリ"
      ],
      "nurseCount": 8,
      "ptCount": null,
      "features": "入所定員80名。足柄平野の自然豊かな環境。在宅復帰支援に注力。デイケア併設。車通勤可。",
      "access": "開成駅車5分",
      "nightShiftType": "オンコール",
      "annualHolidays": 115,
      "salaryMin": 265000,
      "salaryMax": 345000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "介護施設",
        "日勤のみ",
        "オンコール",
        "ブランクOK",
        "残業少なめ"
      ],
      "lat": 35.335,
      "lng": 139.148,
      "nearestStation": "開成駅"
    }
  ],
  "伊勢原市": [
    {
      "name": "東海大学医学部付属病院",
      "type": "高度急性期",
      "beds": 804,
      "wardCount": 23,
      "functions": [
        "高度急性期"
      ],
      "nurseCount": 741,
      "ptCount": null,
      "features": "大学病院。高度救命救急センター（3次救急）・ドクターヘリ完備。23病棟804床。看護師741名は県西最大。がん診療連携拠点病院。EICU/BURN・MFICU・NICU・GCU完備。",
      "access": "伊勢原駅バス10分",
      "nightShiftType": "三交代制",
      "annualHolidays": 120,
      "salaryMin": 300000,
      "salaryMax": 400000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "充実",
      "matchingTags": [
        "高度急性期",
        "大学病院",
        "救命救急",
        "3次救急",
        "ドクターヘリ",
        "がん診療",
        "ICU",
        "NICU",
        "教育体制充実",
        "キャリアアップ"
      ],
      "lat": 35.395,
      "lng": 139.314,
      "nearestStation": "伊勢原駅"
    },
    {
      "name": "伊勢原協同病院",
      "type": "高度急性期・急性期・回復期",
      "beds": 350,
      "wardCount": 10,
      "functions": [
        "高度急性期",
        "急性期",
        "回復期"
      ],
      "nurseCount": 239,
      "ptCount": null,
      "features": "地域中核病院。10病棟350床。HCU・緩和ケア病棟・回復期リハビリ病棟併設。看護師239名。開設50年以上の実績。",
      "access": "伊勢原駅バス8分",
      "nightShiftType": "三交代制",
      "annualHolidays": 120,
      "salaryMin": 280000,
      "salaryMax": 370000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "充実",
      "matchingTags": [
        "高度急性期",
        "急性期",
        "回復期",
        "HCU",
        "緩和ケア",
        "回復期リハビリ",
        "教育体制充実"
      ],
      "lat": 35.395,
      "lng": 139.314,
      "nearestStation": "伊勢原駅"
    },
    {
      "name": "伊勢原日向病院",
      "type": "慢性期",
      "beds": 202,
      "wardCount": 1,
      "functions": [
        "慢性期"
      ],
      "nurseCount": 37,
      "ptCount": null,
      "features": "療養型病院202床。慢性期医療に特化。",
      "access": "伊勢原駅バス20分",
      "nightShiftType": "二交代制",
      "annualHolidays": 115,
      "salaryMin": 250000,
      "salaryMax": 340000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "慢性期",
        "療養"
      ],
      "lat": 35.395,
      "lng": 139.314,
      "nearestStation": "伊勢原駅"
    },
    {
      "name": "伊勢原訪問看護ステーション",
      "type": "訪問看護",
      "beds": null,
      "wardCount": null,
      "functions": [
        "訪問看護"
      ],
      "nurseCount": 9,
      "ptCount": null,
      "features": "伊勢原市の在宅医療を支える訪問看護ステーション。東海大学病院からの退院患者を中心にフォロー。高度医療後の在宅ケアに実績。",
      "access": "伊勢原駅徒歩12分",
      "nightShiftType": "オンコール",
      "annualHolidays": 120,
      "salaryMin": 310000,
      "salaryMax": 385000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "訪問看護",
        "日勤のみ",
        "オンコール",
        "ブランクOK",
        "ターミナルケア"
      ],
      "lat": 35.395,
      "lng": 139.314,
      "nearestStation": "伊勢原駅"
    },
    {
      "name": "ケアステーション伊勢原",
      "type": "訪問看護",
      "beds": null,
      "wardCount": null,
      "functions": [
        "訪問看護"
      ],
      "nurseCount": 7,
      "ptCount": null,
      "features": "伊勢原市南部エリアを中心に活動。小児訪問看護にも対応。リハビリスタッフ在籍で訪問リハビリも提供。",
      "access": "伊勢原駅バス8分",
      "nightShiftType": "オンコール",
      "annualHolidays": 120,
      "salaryMin": 300000,
      "salaryMax": 375000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "訪問看護",
        "日勤のみ",
        "オンコール",
        "残業少なめ",
        "託児所あり"
      ],
      "lat": 35.395,
      "lng": 139.314,
      "nearestStation": "伊勢原駅"
    },
    {
      "name": "伊勢原駅前クリニック",
      "type": "クリニック",
      "beds": null,
      "wardCount": null,
      "functions": [
        "外来診療"
      ],
      "nurseCount": 6,
      "ptCount": null,
      "features": "内科・腎臓内科・透析クリニック。人工透析40床。東海大学病院からの紹介患者多数。日勤のみ。",
      "access": "伊勢原駅徒歩2分",
      "nightShiftType": "なし",
      "annualHolidays": 120,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "クリニック",
        "日勤のみ",
        "透析",
        "駅近",
        "パート可"
      ],
      "lat": 35.395,
      "lng": 139.314,
      "nearestStation": "伊勢原駅"
    },
    {
      "name": "介護老人保健施設いせはら",
      "type": "介護老人保健施設",
      "beds": 80,
      "wardCount": null,
      "functions": [
        "介護・リハビリ"
      ],
      "nurseCount": 9,
      "ptCount": null,
      "features": "入所定員80名。大山のふもとの自然豊かな環境。在宅復帰支援プログラムが充実。デイケア・ショートステイ併設。",
      "access": "伊勢原駅バス15分",
      "nightShiftType": "オンコール",
      "annualHolidays": 115,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "介護施設",
        "日勤のみ",
        "オンコール",
        "ブランクOK",
        "残業少なめ"
      ],
      "lat": 35.395,
      "lng": 139.314,
      "nearestStation": "伊勢原駅"
    }
  ],
  "厚木市": [
    {
      "name": "厚木市立病院",
      "type": "高度急性期・急性期",
      "beds": 341,
      "wardCount": 10,
      "functions": [
        "高度急性期",
        "急性期"
      ],
      "nurseCount": 233,
      "ptCount": null,
      "features": "救急告示病院・災害拠点指定病院。県立病院から市立に転換。ICU・HCU完備。看護師233名。地域の基幹病院。",
      "access": "本厚木駅バス15分",
      "nightShiftType": "三交代制",
      "annualHolidays": 120,
      "salaryMin": 290000,
      "salaryMax": 380000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "充実",
      "matchingTags": [
        "高度急性期",
        "急性期",
        "救急",
        "災害拠点",
        "ICU",
        "HCU",
        "公立病院",
        "教育体制充実"
      ],
      "lat": 35.441,
      "lng": 139.365,
      "nearestStation": "本厚木駅"
    },
    {
      "name": "東名厚木病院",
      "type": "急性期",
      "beds": 282,
      "wardCount": 7,
      "functions": [
        "急性期"
      ],
      "nurseCount": 205,
      "ptCount": null,
      "features": "神奈川県がん診療連携指定病院。救急告示病院。7病棟282床。看護師205名（全員常勤）。緩和ケア病床あり。",
      "access": "本厚木駅バス10分",
      "nightShiftType": "二交代制",
      "annualHolidays": 115,
      "salaryMin": 280000,
      "salaryMax": 370000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "急性期",
        "がん診療",
        "救急",
        "緩和ケア"
      ],
      "lat": 35.441,
      "lng": 139.365,
      "nearestStation": "本厚木駅"
    },
    {
      "name": "神奈川リハビリテーション病院",
      "type": "急性期・回復期・慢性期",
      "beds": 324,
      "wardCount": 9,
      "functions": [
        "急性期",
        "回復期",
        "慢性期"
      ],
      "nurseCount": 195,
      "ptCount": 18,
      "features": "県立リハビリ専門病院。9病棟324床。脊髄損傷・脳神経疾患・骨関節疾患・小児リハビリ・神経難病に対応。全国初の県立リハビリ専門病院。看護師195名。",
      "access": "本厚木駅バス30分（七沢エリア）",
      "nightShiftType": "三交代制",
      "annualHolidays": 120,
      "salaryMin": 280000,
      "salaryMax": 370000,
      "ptSalaryMin": 250000,
      "ptSalaryMax": 320000,
      "educationLevel": "充実",
      "matchingTags": [
        "急性期",
        "回復期",
        "慢性期",
        "リハビリ専門",
        "脊髄損傷",
        "脳神経",
        "小児リハビリ",
        "公的病院",
        "教育体制充実"
      ],
      "lat": 35.441,
      "lng": 139.365,
      "nearestStation": "本厚木駅"
    },
    {
      "name": "湘南厚木病院",
      "type": "高度急性期・急性期・回復期・慢性期",
      "beds": 253,
      "wardCount": 7,
      "functions": [
        "高度急性期",
        "急性期",
        "回復期",
        "慢性期"
      ],
      "nurseCount": 132,
      "ptCount": null,
      "features": "HCU10床含む4機能ケアミックス。急性期から回復期まで一貫対応。看護師132名。",
      "access": "本厚木駅バス12分",
      "nightShiftType": "二交代制",
      "annualHolidays": 115,
      "salaryMin": 280000,
      "salaryMax": 370000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "高度急性期",
        "急性期",
        "回復期",
        "慢性期",
        "ケアミックス",
        "HCU",
        "徳洲会"
      ],
      "lat": 35.441,
      "lng": 139.365,
      "nearestStation": "本厚木駅"
    },
    {
      "name": "AOI七沢リハビリテーション病院",
      "type": "回復期",
      "beds": 245,
      "wardCount": 5,
      "functions": [
        "回復期"
      ],
      "nurseCount": 83,
      "ptCount": 53,
      "features": "回復期リハビリテーション専門5病棟245床。PT53名・OT35名・ST20名のリハスタッフ計108名は県西最大級。",
      "access": "本厚木駅バス25分",
      "nightShiftType": "二交代制",
      "annualHolidays": 115,
      "salaryMin": 270000,
      "salaryMax": 360000,
      "ptSalaryMin": 250000,
      "ptSalaryMax": 320000,
      "educationLevel": "あり",
      "matchingTags": [
        "回復期",
        "回復期リハビリ",
        "リハビリ専門",
        "リハビリ充実"
      ],
      "lat": 35.441,
      "lng": 139.365,
      "nearestStation": "本厚木駅"
    },
    {
      "name": "厚木佐藤病院",
      "type": "急性期・回復期・慢性期",
      "beds": 130,
      "wardCount": 3,
      "functions": [
        "急性期",
        "回復期",
        "慢性期"
      ],
      "nurseCount": 44,
      "ptCount": null,
      "features": "一般・回復期・療養の3機能併設。",
      "access": "本厚木駅バス10分",
      "nightShiftType": "二交代制",
      "annualHolidays": 115,
      "salaryMin": 270000,
      "salaryMax": 360000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "急性期",
        "回復期",
        "慢性期",
        "ケアミックス"
      ],
      "lat": 35.441,
      "lng": 139.365,
      "nearestStation": "本厚木駅"
    },
    {
      "name": "近藤病院",
      "type": "慢性期",
      "beds": 111,
      "wardCount": 1,
      "functions": [
        "慢性期"
      ],
      "nurseCount": 28,
      "ptCount": null,
      "features": "障害者施設等入院基本料病棟111床。",
      "access": "本厚木駅バス15分",
      "nightShiftType": "二交代制",
      "annualHolidays": 115,
      "salaryMin": 250000,
      "salaryMax": 340000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "慢性期",
        "障害者病棟"
      ],
      "lat": 35.441,
      "lng": 139.365,
      "nearestStation": "本厚木駅"
    },
    {
      "name": "厚木訪問看護ステーション",
      "type": "訪問看護",
      "beds": null,
      "wardCount": null,
      "functions": [
        "訪問看護"
      ],
      "nurseCount": 12,
      "ptCount": null,
      "features": "厚木市中心部の大規模訪問看護ステーション。厚木市立病院・東名厚木病院との連携体制が充実。がんターミナルケアに強み。",
      "access": "本厚木駅徒歩10分",
      "nightShiftType": "オンコール",
      "annualHolidays": 122,
      "salaryMin": 315000,
      "salaryMax": 390000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "訪問看護",
        "日勤のみ",
        "オンコール",
        "駅近",
        "ターミナルケア"
      ],
      "lat": 35.441,
      "lng": 139.365,
      "nearestStation": "本厚木駅"
    },
    {
      "name": "本厚木ケアステーション",
      "type": "訪問看護",
      "beds": null,
      "wardCount": null,
      "functions": [
        "訪問看護"
      ],
      "nurseCount": 8,
      "ptCount": null,
      "features": "本厚木駅周辺エリアの在宅療養者を支援。神経難病・呼吸器疾患の訪問看護に実績。直行直帰制度あり。",
      "access": "本厚木駅徒歩8分",
      "nightShiftType": "オンコール",
      "annualHolidays": 120,
      "salaryMin": 305000,
      "salaryMax": 380000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "訪問看護",
        "日勤のみ",
        "オンコール",
        "駅近",
        "直行直帰",
        "神経難病"
      ],
      "lat": 35.441,
      "lng": 139.365,
      "nearestStation": "本厚木駅"
    },
    {
      "name": "本厚木駅前クリニック",
      "type": "クリニック",
      "beds": null,
      "wardCount": null,
      "functions": [
        "外来診療"
      ],
      "nurseCount": 7,
      "ptCount": null,
      "features": "内科・消化器科・肝臓内科の外来クリニック。内視鏡検査・腹部エコー対応。駅前ビル内で通勤便利。日勤のみ。",
      "access": "本厚木駅徒歩2分",
      "nightShiftType": "なし",
      "annualHolidays": 125,
      "salaryMin": 270000,
      "salaryMax": 345000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "クリニック",
        "日勤のみ",
        "残業少なめ",
        "駅近",
        "パート可"
      ],
      "lat": 35.441,
      "lng": 139.365,
      "nearestStation": "本厚木駅"
    },
    {
      "name": "介護老人保健施設あつぎの丘",
      "type": "介護老人保健施設",
      "beds": 100,
      "wardCount": null,
      "functions": [
        "介護・リハビリ"
      ],
      "nurseCount": 12,
      "ptCount": null,
      "features": "入所定員100名。七沢エリアの自然豊かな環境に立地。在宅復帰支援・認知症ケアに注力。通所リハビリ・ショートステイ併設。",
      "access": "本厚木駅バス20分",
      "nightShiftType": "オンコール",
      "annualHolidays": 115,
      "salaryMin": 275000,
      "salaryMax": 355000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "介護施設",
        "日勤のみ",
        "オンコール",
        "ブランクOK",
        "残業少なめ",
        "認知症ケア"
      ],
      "lat": 35.441,
      "lng": 139.365,
      "nearestStation": "本厚木駅"
    },
    {
      "name": "厚木南訪問看護ステーション",
      "type": "訪問看護",
      "beds": null,
      "wardCount": null,
      "functions": [
        "訪問看護"
      ],
      "nurseCount": 6,
      "ptCount": null,
      "features": "厚木市南部・愛甲石田エリアを中心に活動。精神科訪問看護にも対応。子育て中のスタッフが多くワークライフバランス重視。",
      "access": "愛甲石田駅徒歩12分",
      "nightShiftType": "オンコール",
      "annualHolidays": 120,
      "salaryMin": 300000,
      "salaryMax": 370000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "訪問看護",
        "日勤のみ",
        "オンコール",
        "精神科訪問看護",
        "託児所あり",
        "ブランクOK"
      ],
      "lat": 35.412,
      "lng": 139.327,
      "nearestStation": "愛甲石田駅"
    }
  ],
  "海老名市": [
    {
      "name": "海老名総合病院",
      "type": "高度急性期・急性期",
      "beds": 479,
      "wardCount": 14,
      "functions": [
        "高度急性期",
        "急性期"
      ],
      "nurseCount": 431,
      "ptCount": 56,
      "features": "地域医療支援病院。県央保健医療圏唯一の救命救急センター（3次救急）。ICU・HCU・EHCU・SCU完備。手術室14室。年間救急車7,731台。看護師431名・PT56名。24時間365日断らない救急。",
      "access": "海老名駅東口徒歩12分、シャトルバスあり",
      "nightShiftType": "三交代制",
      "annualHolidays": 120,
      "salaryMin": 300000,
      "salaryMax": 390000,
      "ptSalaryMin": 260000,
      "ptSalaryMax": 330000,
      "educationLevel": "充実",
      "matchingTags": [
        "高度急性期",
        "急性期",
        "救命救急",
        "3次救急",
        "ICU",
        "HCU",
        "SCU",
        "24時間救急",
        "教育体制充実"
      ],
      "lat": 35.447,
      "lng": 139.391,
      "nearestStation": "海老名駅"
    },
    {
      "name": "湘陽かしわ台病院",
      "type": "急性期・回復期・慢性期",
      "beds": 199,
      "wardCount": 4,
      "functions": [
        "急性期",
        "回復期",
        "慢性期"
      ],
      "nurseCount": 79,
      "ptCount": 20,
      "features": "一般・回復期・療養の3機能併設。PT20名・OT13名・ST6名。看護師79名。",
      "access": "さがみ野駅徒歩圏",
      "nightShiftType": "二交代制",
      "annualHolidays": 115,
      "salaryMin": 280000,
      "salaryMax": 370000,
      "ptSalaryMin": 260000,
      "ptSalaryMax": 330000,
      "educationLevel": "あり",
      "matchingTags": [
        "急性期",
        "回復期",
        "慢性期",
        "ケアミックス",
        "リハビリ充実",
        "駅近"
      ],
      "lat": 35.459,
      "lng": 139.401,
      "nearestStation": "さがみ野駅"
    },
    {
      "name": "オアシス湘南病院",
      "type": "慢性期",
      "beds": 158,
      "wardCount": 3,
      "functions": [
        "慢性期"
      ],
      "nurseCount": 27,
      "ptCount": null,
      "features": "療養型3病棟158床。慢性期医療に特化。",
      "access": "海老名駅車10分",
      "nightShiftType": "二交代制",
      "annualHolidays": 115,
      "salaryMin": 260000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "慢性期",
        "療養"
      ],
      "lat": 35.447,
      "lng": 139.391,
      "nearestStation": "海老名駅"
    },
    {
      "name": "さがみ野中央病院",
      "type": "急性期・回復期",
      "beds": 96,
      "wardCount": 2,
      "functions": [
        "急性期",
        "回復期"
      ],
      "nurseCount": 29,
      "ptCount": null,
      "features": "一般・回復期2病棟。",
      "access": "さがみ野駅徒歩圏",
      "nightShiftType": "二交代制",
      "annualHolidays": 110,
      "salaryMin": 280000,
      "salaryMax": 370000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "なし",
      "matchingTags": [
        "急性期",
        "回復期",
        "少人数",
        "駅近"
      ],
      "lat": 35.459,
      "lng": 139.401,
      "nearestStation": "さがみ野駅"
    },
    {
      "name": "海老名訪問看護ステーション",
      "type": "訪問看護",
      "beds": null,
      "wardCount": null,
      "functions": [
        "訪問看護"
      ],
      "nurseCount": 10,
      "ptCount": null,
      "features": "海老名市中心部の訪問看護ステーション。海老名総合病院からの退院患者を中心にフォロー。3路線利用可能で通勤便利。",
      "access": "海老名駅徒歩8分",
      "nightShiftType": "オンコール",
      "annualHolidays": 122,
      "salaryMin": 315000,
      "salaryMax": 390000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "訪問看護",
        "日勤のみ",
        "オンコール",
        "駅近",
        "ターミナルケア"
      ],
      "lat": 35.447,
      "lng": 139.391,
      "nearestStation": "海老名駅"
    },
    {
      "name": "ケアステーション海老名",
      "type": "訪問看護",
      "beds": null,
      "wardCount": null,
      "functions": [
        "訪問看護"
      ],
      "nurseCount": 7,
      "ptCount": null,
      "features": "海老名市北部・さがみ野エリアを中心に展開。認知症ケア・精神科訪問看護にも対応。直行直帰制度あり。",
      "access": "さがみ野駅徒歩10分",
      "nightShiftType": "オンコール",
      "annualHolidays": 120,
      "salaryMin": 305000,
      "salaryMax": 380000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "訪問看護",
        "日勤のみ",
        "オンコール",
        "精神科訪問看護",
        "直行直帰",
        "ブランクOK"
      ],
      "lat": 35.459,
      "lng": 139.401,
      "nearestStation": "さがみ野駅"
    },
    {
      "name": "海老名駅前クリニック",
      "type": "クリニック",
      "beds": null,
      "wardCount": null,
      "functions": [
        "外来診療"
      ],
      "nurseCount": 6,
      "ptCount": null,
      "features": "内科・循環器科・呼吸器科の外来クリニック。心エコー・肺機能検査対応。再開発エリアの駅前ビル内。日勤のみ。",
      "access": "海老名駅徒歩3分",
      "nightShiftType": "なし",
      "annualHolidays": 125,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "クリニック",
        "日勤のみ",
        "残業少なめ",
        "駅近",
        "パート可"
      ],
      "lat": 35.447,
      "lng": 139.391,
      "nearestStation": "海老名駅"
    },
    {
      "name": "介護老人保健施設さがみ野",
      "type": "介護老人保健施設",
      "beds": 100,
      "wardCount": null,
      "functions": [
        "介護・リハビリ"
      ],
      "nurseCount": 11,
      "ptCount": null,
      "features": "入所定員100名。在宅復帰支援に注力。リハビリプログラムが充実。デイケア・ショートステイ併設。子育て支援制度あり。",
      "access": "さがみ野駅車5分",
      "nightShiftType": "オンコール",
      "annualHolidays": 118,
      "salaryMin": 275000,
      "salaryMax": 360000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "介護施設",
        "日勤のみ",
        "オンコール",
        "ブランクOK",
        "託児所あり",
        "残業少なめ"
      ],
      "lat": 35.459,
      "lng": 139.401,
      "nearestStation": "さがみ野駅"
    }
  ]
};
