// ==========================================
// ナースロビー - 施設データベース（自動生成）
// Generated: 2026-02-25T13:54:00.784Z
// Source: data/areas.js (10エリア)
// ==========================================

// 駅座標データ（Haversine距離計算用）
const STATION_COORDINATES = {
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
const AREA_METADATA = {
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
      "hospitals": 12,
      "clinics": 0,
      "nursingHomes": 0
    },
    "demandLevel": "非常に高い",
    "demandNote": "県西の基幹病院が集中。小田原市立病院（417床）の新築移転予定に伴い人材需要が高まる。",
    "livingInfo": "新幹線停車駅で都心通勤も可能。箱根・湯河原の温泉地にも近く生活環境が魅力。",
    "defaultCoords": {
      "lat": 35.2564,
      "lng": 139.1551
    }
  },
  "秦野市": {
    "areaId": "hadano",
    "medicalRegion": "shonan_west",
    "population": "約16万人",
    "majorStations": [
      "秦野駅（小田急小田原線）",
      "東海大学前駅（小田急小田原線）",
      "渋沢駅（小田急小田原線）"
    ],
    "commuteToYokohama": "約50分（小田急線）",
    "nurseAvgSalary": "月給27〜36万円",
    "ptAvgSalary": "月給24〜31万円",
    "facilityCount": {
      "hospitals": 4,
      "clinics": 0,
      "nursingHomes": 0
    },
    "demandLevel": "高い",
    "demandNote": "秦野赤十字病院（312床）を中心に安定した看護師需要。地域密着型の医療機関が多い。",
    "livingInfo": "丹沢山系の自然環境と住宅地が共存。物価が比較的安く、子育て環境に人気。",
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
      "clinics": 0,
      "nursingHomes": 0
    },
    "demandLevel": "非常に高い",
    "demandNote": "平塚共済病院（441床）を筆頭に急性期病院が充実。人口規模に比して看護師需要が大きい。",
    "livingInfo": "海と山の両方にアクセスでき、自然と都市機能のバランスが良い。横浜通勤も現実的。",
    "defaultCoords": {
      "lat": 35.328,
      "lng": 139.3497
    }
  },
  "藤沢市": {
    "areaId": "fujisawa",
    "medicalRegion": "shonan_east",
    "population": "約44万人",
    "majorStations": [
      "藤沢駅（JR東海道線・小田急江ノ島線・江ノ電）",
      "辻堂駅（JR東海道線）",
      "湘南台駅（小田急・相鉄・横浜市営地下鉄）"
    ],
    "commuteToYokohama": "約20分（JR東海道線）",
    "nurseAvgSalary": "月給29〜38万円",
    "ptAvgSalary": "月給26〜33万円",
    "facilityCount": {
      "hospitals": 14,
      "clinics": 0,
      "nursingHomes": 0
    },
    "demandLevel": "非常に高い",
    "demandNote": "藤沢市民病院（530床）・湘南藤沢徳洲会病院（419床）など大規模病院が集中。看護師需要が県内屈指。",
    "livingInfo": "湘南のブランドエリア。海沿いのライフスタイルが人気。東京・横浜通勤も便利。",
    "defaultCoords": {
      "lat": 35.338,
      "lng": 139.487
    }
  },
  "茅ヶ崎市": {
    "areaId": "chigasaki",
    "medicalRegion": "shonan_east",
    "population": "約24.4万人",
    "majorStations": [
      "茅ヶ崎駅（JR東海道線・相模線）",
      "北茅ヶ崎駅（JR相模線）"
    ],
    "commuteToYokohama": "約25分（JR東海道線）",
    "nurseAvgSalary": "月給28〜37万円",
    "ptAvgSalary": "月給25〜32万円",
    "facilityCount": {
      "hospitals": 7,
      "clinics": 0,
      "nursingHomes": 0
    },
    "demandLevel": "高い",
    "demandNote": "茅ヶ崎市立病院（401床）が地域の中核。市内の高齢化に伴い訪問看護需要も増加。",
    "livingInfo": "海辺の穏やかな暮らし。サーフィン文化。駅前は商業施設も充実しバランスの良い環境。",
    "defaultCoords": {
      "lat": 35.334,
      "lng": 139.404
    }
  },
  "大磯町・二宮町": {
    "areaId": "oiso_ninomiya",
    "medicalRegion": "shonan_west",
    "population": "約6万人（合計）",
    "majorStations": [
      "大磯駅（JR東海道線）",
      "二宮駅（JR東海道線）"
    ],
    "commuteToYokohama": "約40分（JR東海道線）",
    "nurseAvgSalary": "月給27〜35万円",
    "ptAvgSalary": "月給24〜31万円",
    "facilityCount": {
      "hospitals": 1,
      "clinics": 0,
      "nursingHomes": 0
    },
    "demandLevel": "やや高い",
    "demandNote": "大磯プリンスホテル跡地の再開発を含め、高齢者向け医療施設の需要が増加傾向。",
    "livingInfo": "湘南発祥の地。海と山の自然環境。閑静な住宅地で子育てにも適する。東海道線で通勤可。",
    "defaultCoords": {
      "lat": 35.306,
      "lng": 139.283
    }
  },
  "南足柄市・開成町・大井町・松田町・山北町": {
    "areaId": "minamiashigara_kaisei_oi",
    "medicalRegion": "kensei",
    "population": "約9.5万人（合計）",
    "majorStations": [
      "大雄山駅（伊豆箱根鉄道大雄山線）",
      "開成駅（小田急小田原線）",
      "松田駅（JR御殿場線・小田急小田原線）",
      "山北駅（JR御殿場線）"
    ],
    "commuteToYokohama": "約70分（大雄山線+小田急線）",
    "nurseAvgSalary": "月給26〜35万円",
    "ptAvgSalary": "月給24〜30万円",
    "facilityCount": {
      "hospitals": 6,
      "clinics": 0,
      "nursingHomes": 0
    },
    "demandLevel": "高い",
    "demandNote": "足柄上病院（199床）が地域の中核。中山間地域の医療アクセス確保のため看護師需要が安定。",
    "livingInfo": "豊かな自然と低い生活コスト。小田原・新松田から小田急線で都心アクセスも可能。子育て支援充実。",
    "defaultCoords": null
  },
  "伊勢原市": {
    "areaId": "isehara",
    "medicalRegion": "shonan_west",
    "population": "約10.1万人",
    "majorStations": [
      "伊勢原駅（小田急小田原線）"
    ],
    "commuteToYokohama": "約45分（小田急線）",
    "nurseAvgSalary": "月給28〜38万円",
    "ptAvgSalary": "月給25〜32万円",
    "facilityCount": {
      "hospitals": 3,
      "clinics": 0,
      "nursingHomes": 0
    },
    "demandLevel": "非常に高い",
    "demandNote": "東海大学医学部付属病院（804床・看護師741名）は県西最大の医療機関。常時大量採用。",
    "livingInfo": "大山の自然と大学のある学園都市。小田急線で新宿60分、物価も手頃。",
    "defaultCoords": {
      "lat": 35.395,
      "lng": 139.314
    }
  },
  "厚木市": {
    "areaId": "atsugi",
    "medicalRegion": "kenoh",
    "population": "約22.4万人",
    "majorStations": [
      "本厚木駅（小田急小田原線）",
      "愛甲石田駅（小田急小田原線）"
    ],
    "commuteToYokohama": "約40分（小田急線）",
    "nurseAvgSalary": "月給28〜37万円",
    "ptAvgSalary": "月給25〜32万円",
    "facilityCount": {
      "hospitals": 9,
      "clinics": 0,
      "nursingHomes": 0
    },
    "demandLevel": "非常に高い",
    "demandNote": "厚木市立病院（347床）と東名厚木病院（271床）を中心に看護師需要が旺盛。リハビリ系施設も多い。",
    "livingInfo": "本厚木駅周辺は商業施設充実。新宿まで55分。丹沢の自然も近く子育て環境も良好。",
    "defaultCoords": {
      "lat": 35.441,
      "lng": 139.365
    }
  },
  "海老名市": {
    "areaId": "ebina",
    "medicalRegion": "kenoh",
    "population": "約14万人",
    "majorStations": [
      "海老名駅（小田急線・相鉄線・JR相模線）"
    ],
    "commuteToYokohama": "約30分（相鉄線）",
    "nurseAvgSalary": "月給29〜38万円",
    "ptAvgSalary": "月給26〜33万円",
    "facilityCount": {
      "hospitals": 4,
      "clinics": 0,
      "nursingHomes": 0
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

// 全施設データベース（67施設）
const FACILITY_DATABASE = {
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
      "nurseCount": 386,
      "ptCount": 22,
      "features": "公立。看護配置7:1。三次救急。年間救急車6,675台。DPC標準病院群。看護師386名。医師114名。PT22名。CT2台・MRI2台。HCU・ICU・NICU完備。退院支援部門あり。2026年新築移転予定。県西地域の基幹病院。",
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
        "三次救急",
        "救命救急",
        "公立病院",
        "DPC標準病院群",
        "退院支援充実",
        "7対1看護",
        "大規模病院",
        "HCU",
        "ICU",
        "NICU",
        "リハビリ充実",
        "災害拠点",
        "がん診療",
        "教育体制充実",
        "新築移転"
      ],
      "lat": 35.2564,
      "lng": 139.1551,
      "nearestStation": "小田原駅"
    },
    {
      "name": "医療法人 同愛会 小澤病院",
      "type": "急性期",
      "beds": 202,
      "wardCount": 4,
      "functions": [
        "急性期"
      ],
      "nurseCount": 139,
      "ptCount": 7,
      "features": "医療法人。看護配置10:1。二次救急。年間救急車1,960台。看護師139名。医師28名。PT7名。CT1台・MRI1台。退院支援部門あり。脳外科・整形外科を中心とした混合病棟を持つ地域密着型総合病院。",
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
        "二次救急",
        "退院支援充実",
        "中規模病院",
        "脳外科",
        "整形外科",
        "地域密着"
      ],
      "lat": 35.2564,
      "lng": 139.1551,
      "nearestStation": "小田原駅"
    },
    {
      "name": "独立行政法人国立病院機構箱根病院",
      "type": "慢性期",
      "beds": 199,
      "wardCount": 3,
      "functions": [
        "慢性期"
      ],
      "nurseCount": 108,
      "ptCount": 9,
      "features": "国立。看護配置障害者7:1。看護師108名。医師9名。PT9名。CT1台・MRI1台。国立病院機構。慢性期医療に特化。",
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
        "国立病院",
        "療養",
        "国立病院機構",
        "公的病院"
      ],
      "lat": 35.2564,
      "lng": 139.1551,
      "nearestStation": "小田原駅"
    },
    {
      "name": "医療法人尽誠会 山近記念総合病院",
      "type": "急性期",
      "beds": 152,
      "wardCount": 2,
      "functions": [
        "急性期"
      ],
      "nurseCount": 93,
      "ptCount": 2,
      "features": "医療法人。看護配置7:1。二次救急。年間救急車909台。DPC標準病院群。看護師93名。医師16名。PT2名。CT1台・MRI1台。退院支援部門あり。救急病院指定。人間ドック対応。",
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
        "二次救急",
        "DPC標準病院群",
        "退院支援充実",
        "7対1看護",
        "救急",
        "人間ドック"
      ],
      "lat": 35.2564,
      "lng": 139.1551,
      "nearestStation": "小田原駅"
    },
    {
      "name": "医療法人 小林病院",
      "type": "急性期・回復期・慢性期",
      "beds": 150,
      "wardCount": 3,
      "functions": [
        "急性期",
        "回復期",
        "慢性期"
      ],
      "nurseCount": 54,
      "ptCount": 9,
      "features": "医療法人。看護配置13:1。二次救急。年間救急車200台。看護師54名。医師45名。PT9名。CT1台。退院支援部門あり。100年以上の歴史を持つ地域密着型病院。一般病棟・回復期リハビリテーション病棟・療養病棟を併設。",
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
        "二次救急",
        "退院支援充実",
        "回復期リハビリ",
        "ケアミックス",
        "地域密着"
      ],
      "lat": 35.2564,
      "lng": 139.1551,
      "nearestStation": "小田原駅"
    },
    {
      "name": "特定医療法人社団研精会 箱根リハビリテーション病院",
      "type": "回復期・慢性期",
      "beds": 109,
      "wardCount": 2,
      "functions": [
        "慢性期",
        "回復期"
      ],
      "nurseCount": 38,
      "ptCount": 16,
      "features": "医療法人。看護配置回復期13:1。看護師38名。医師7名。PT16名。CT1台。退院支援部門あり。",
      "access": "",
      "nightShiftType": "二交代制",
      "annualHolidays": 110,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "慢性期",
        "回復期",
        "退院支援充実",
        "回復期リハビリ",
        "リハビリ充実"
      ],
      "lat": 35.2564,
      "lng": 139.1551,
      "nearestStation": null
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
      "nurseCount": 78,
      "ptCount": 7,
      "features": "医療法人。看護配置15:1。二次救急。看護師78名。医師11名。PT7名。CT1台・MRI2台。退院支援部門あり。一般病棟・療養病棟を併設。救急病院指定。",
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
        "二次救急",
        "退院支援充実",
        "療養",
        "救急",
        "駅近"
      ],
      "lat": 35.2687,
      "lng": 139.176,
      "nearestStation": "鴨宮駅"
    },
    {
      "name": "医療法人邦友会 小田原循環器病院",
      "type": "高度急性期・急性期",
      "beds": 97,
      "wardCount": 3,
      "functions": [
        "急性期",
        "高度急性期"
      ],
      "nurseCount": 104,
      "ptCount": null,
      "features": "医療法人。看護配置7:1。救急告示。年間救急車584台。看護師104名。医師15名。CT1台・MRI1台。退院支援部門あり。循環器専門病院。心臓カテーテル治療に強み。ハイケアユニット完備。",
      "access": "小田原駅車10分",
      "nightShiftType": "二交代制",
      "annualHolidays": 110,
      "salaryMin": 290000,
      "salaryMax": 380000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "なし",
      "matchingTags": [
        "急性期",
        "高度急性期",
        "退院支援充実",
        "7対1看護",
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
      "name": "医療法人社団綾和会 間中病院",
      "type": "急性期・回復期",
      "beds": 90,
      "wardCount": 2,
      "functions": [
        "急性期",
        "回復期"
      ],
      "nurseCount": 54,
      "ptCount": 29,
      "features": "医療法人。看護配置回復期13:1。二次救急。年間救急車721台。看護師54名。医師10名。PT29名。CT1台・MRI2台。退院支援部門あり。地域包括ケア病棟・回復期リハビリテーション病棟併設。",
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
        "二次救急",
        "退院支援充実",
        "回復期リハビリ",
        "リハビリ充実",
        "地域包括ケア"
      ],
      "lat": 35.2564,
      "lng": 139.1551,
      "nearestStation": "小田原駅"
    },
    {
      "name": "医療法人社団 帰陽会 丹羽病院",
      "type": "急性期",
      "beds": 51,
      "wardCount": 1,
      "functions": [
        "急性期"
      ],
      "nurseCount": 41,
      "ptCount": null,
      "features": "医療法人。二次救急。年間救急車317台。看護師41名。医師6名。CT1台。地域密着型。",
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
        "二次救急",
        "地域密着",
        "少人数"
      ],
      "lat": 35.2564,
      "lng": 139.1551,
      "nearestStation": "小田原駅"
    },
    {
      "name": "医療法人社団三暉会 永井病院",
      "type": "急性期",
      "beds": 45,
      "wardCount": 1,
      "functions": [
        "急性期"
      ],
      "nurseCount": 9,
      "ptCount": null,
      "features": "医療法人。救急告示。看護師9名。医師5名。",
      "access": "",
      "nightShiftType": "二交代制",
      "annualHolidays": 110,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "急性期"
      ],
      "lat": 35.2564,
      "lng": 139.1551,
      "nearestStation": null
    },
    {
      "name": "太陽の門",
      "type": "慢性期",
      "beds": 0,
      "wardCount": 1,
      "functions": [
        "慢性期"
      ],
      "nurseCount": 16,
      "ptCount": 2,
      "features": "社会福祉法人。看護師16名。医師4名。PT2名。",
      "access": "",
      "nightShiftType": "二交代制",
      "annualHolidays": 110,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "慢性期"
      ],
      "lat": 35.2564,
      "lng": 139.1551,
      "nearestStation": null
    }
  ],
  "秦野市": [
    {
      "name": "医療法人社団三喜会 鶴巻温泉病院",
      "type": "回復期・慢性期",
      "beds": 505,
      "wardCount": 10,
      "functions": [
        "慢性期",
        "回復期"
      ],
      "nurseCount": 193,
      "ptCount": 72,
      "features": "医療法人。看護配置障害者7:1。救急告示。看護師193名。医師26名。PT72名。CT1台。退院支援部門あり。回復期リハビリテーション・慢性期医療に強み。地域最大級の療養病院。",
      "access": "鶴巻温泉駅徒歩5分",
      "nightShiftType": "二交代制",
      "annualHolidays": 120,
      "salaryMin": 260000,
      "salaryMax": 340000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "充実",
      "matchingTags": [
        "慢性期",
        "回復期",
        "退院支援充実",
        "大規模病院",
        "回復期リハビリ",
        "リハビリ充実",
        "急性期",
        "ケアミックス",
        "療養",
        "大規模",
        "駅近"
      ],
      "lat": 35.369,
      "lng": 139.27,
      "nearestStation": "鶴巻温泉駅"
    },
    {
      "name": "独立行政法人国立病院機構神奈川病院",
      "type": "急性期・慢性期",
      "beds": 330,
      "wardCount": 5,
      "functions": [
        "急性期",
        "慢性期"
      ],
      "nurseCount": 166,
      "ptCount": 9,
      "features": "国立。看護配置障害者7:1。二次救急。年間救急車1,305台。DPC標準病院群。看護師166名。医師22名。PT9名。CT1台・MRI1台。退院支援部門あり。国立病院機構。呼吸器疾患・神経難病を中心とした専門医療。",
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
        "慢性期",
        "二次救急",
        "国立病院",
        "DPC標準病院群",
        "退院支援充実",
        "中規模病院",
        "回復期",
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
      "name": "秦野赤十字病院",
      "type": "高度急性期・急性期・回復期",
      "beds": 308,
      "wardCount": 7,
      "functions": [
        "回復期",
        "急性期",
        "高度急性期"
      ],
      "nurseCount": 243,
      "ptCount": 8,
      "features": "日赤。看護配置10:1。二次救急。年間救急車3,872台。DPC標準病院群。看護師243名。医師57名。PT8名。CT2台・MRI1台。HCU完備。退院支援部門あり。地域医療支援病院・救急告示病院・災害拠点病院・臨床研修指定病院。秦野市に市民病院がないため市民病院的役割を担う。",
      "access": "秦野駅バス10分",
      "nightShiftType": "三交代制",
      "annualHolidays": 120,
      "salaryMin": 280000,
      "salaryMax": 360000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "充実",
      "matchingTags": [
        "回復期",
        "急性期",
        "高度急性期",
        "二次救急",
        "DPC標準病院群",
        "退院支援充実",
        "中規模病院",
        "回復期リハビリ",
        "HCU",
        "救急",
        "災害拠点",
        "臨床研修",
        "赤十字",
        "教育体制充実"
      ],
      "lat": 35.3737,
      "lng": 139.2192,
      "nearestStation": "秦野駅"
    },
    {
      "name": "医療法人杏林会 八木病院",
      "type": "急性期・回復期",
      "beds": 94,
      "wardCount": 2,
      "functions": [
        "急性期",
        "回復期"
      ],
      "nurseCount": 29,
      "ptCount": 11,
      "features": "医療法人。看護配置障害者7:1。二次救急。年間救急車621台。看護師29名。医師14名。PT11名。CT1台・MRI1台。退院支援部門あり。障害者施設等入院基本料病棟・回復期リハビリテーション病棟。",
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
        "二次救急",
        "退院支援充実",
        "回復期リハビリ",
        "障害者病棟"
      ],
      "lat": 35.3737,
      "lng": 139.2192,
      "nearestStation": "秦野駅"
    }
  ],
  "平塚市": [
    {
      "name": "平塚市民病院",
      "type": "高度急性期・急性期",
      "beds": 416,
      "wardCount": 12,
      "functions": [
        "急性期",
        "高度急性期"
      ],
      "nurseCount": 447,
      "ptCount": 9,
      "features": "公立。看護配置7:1。三次救急。年間救急車10,703台。DPC標準病院群。看護師447名。医師98名。PT9名。CT5台・MRI2台。ICU・CCU完備。退院支援部門あり。救急告示病院・災害拠点指定病院。平塚市の基幹病院。産科・小児科も充実。",
      "access": "平塚駅バス10分",
      "nightShiftType": "三交代制",
      "annualHolidays": 120,
      "salaryMin": 290000,
      "salaryMax": 380000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "充実",
      "matchingTags": [
        "急性期",
        "高度急性期",
        "三次救急",
        "救命救急",
        "公立病院",
        "DPC標準病院群",
        "退院支援充実",
        "7対1看護",
        "大規模病院",
        "ICU",
        "救急",
        "災害拠点",
        "CCU",
        "HCU",
        "産科",
        "小児科",
        "教育体制充実"
      ],
      "lat": 35.328,
      "lng": 139.3497,
      "nearestStation": "平塚駅"
    },
    {
      "name": "国家公務員共済組合連合会 平塚共済病院",
      "type": "高度急性期・急性期",
      "beds": 400,
      "wardCount": 10,
      "functions": [
        "急性期",
        "高度急性期"
      ],
      "nurseCount": 429,
      "ptCount": 11,
      "features": "公的。看護配置7:1。二次救急。年間救急車7,080台。DPC特定病院群。看護師429名。医師122名。PT11名。CT2台・MRI2台。ICU完備。退院支援部門あり。地域医療支援病院・救急告示病院・災害拠点指定病院。心臓センター・救急センター・脳卒中センター・周産期センター併設。",
      "access": "平塚駅バス8分",
      "nightShiftType": "三交代制",
      "annualHolidays": 120,
      "salaryMin": 290000,
      "salaryMax": 380000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "充実",
      "matchingTags": [
        "急性期",
        "高度急性期",
        "二次救急",
        "公的病院",
        "DPC特定病院群",
        "退院支援充実",
        "7対1看護",
        "大規模病院",
        "ICU",
        "リハビリ充実",
        "救急",
        "災害拠点",
        "心臓センター",
        "脳卒中",
        "周産期",
        "教育体制充実"
      ],
      "lat": 35.328,
      "lng": 139.3497,
      "nearestStation": "平塚駅"
    },
    {
      "name": "医療法人研水会 高根台病院",
      "type": "慢性期",
      "beds": 236,
      "wardCount": 4,
      "functions": [
        "慢性期"
      ],
      "nurseCount": 62,
      "ptCount": 8,
      "features": "医療法人。看護配置療養20:1。看護師62名。医師9名。PT8名。CT1台。退院支援部門あり。慢性期医療に特化。",
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
        "退院支援充実",
        "中規模病院",
        "療養"
      ],
      "lat": 35.328,
      "lng": 139.3497,
      "nearestStation": "平塚駅"
    },
    {
      "name": "社会福祉法人 恩賜財団済生会支部 神奈川県済生会湘南平塚病院",
      "type": "急性期・回復期",
      "beds": 176,
      "wardCount": 4,
      "functions": [
        "急性期",
        "回復期"
      ],
      "nurseCount": 104,
      "ptCount": 38,
      "features": "公的。看護配置10:1。救急告示。年間救急車124台。看護師104名。医師15名。PT38名。CT1台・MRI1台。退院支援部門あり。一般病棟・地域包括ケア病棟・回復期リハビリテーション病棟を併設。急性期病院と在宅をつなぐハブ機能。",
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
        "公的病院",
        "退院支援充実",
        "回復期リハビリ",
        "リハビリ充実",
        "地域包括ケア",
        "済生会"
      ],
      "lat": 35.328,
      "lng": 139.3497,
      "nearestStation": "平塚駅"
    },
    {
      "name": "医療法人社団健齢会 ふれあい平塚ホスピタル",
      "type": "急性期・回復期・慢性期",
      "beds": 125,
      "wardCount": 3,
      "functions": [
        "急性期",
        "回復期",
        "慢性期"
      ],
      "nurseCount": 46,
      "ptCount": 35,
      "features": "医療法人。看護配置障害者7:1。看護師46名。医師10名。PT35名。CT1台・MRI1台。退院支援部門あり。回復期リハビリテーション病棟・慢性期病棟。",
      "access": "平塚駅バス10分",
      "nightShiftType": "二交代制",
      "annualHolidays": 115,
      "salaryMin": 260000,
      "salaryMax": 350000,
      "ptSalaryMin": 250000,
      "ptSalaryMax": 320000,
      "educationLevel": "あり",
      "matchingTags": [
        "急性期",
        "回復期",
        "慢性期",
        "退院支援充実",
        "回復期リハビリ",
        "リハビリ充実"
      ],
      "lat": 35.328,
      "lng": 139.3497,
      "nearestStation": "平塚駅"
    },
    {
      "name": "くらた病院",
      "type": "慢性期",
      "beds": 79,
      "wardCount": 2,
      "functions": [
        "慢性期"
      ],
      "nurseCount": 27,
      "ptCount": 12,
      "features": "医療法人。看護配置療養20:1。看護師27名。医師8名。PT12名。CT1台。退院支援部門あり。",
      "access": "",
      "nightShiftType": "二交代制",
      "annualHolidays": 110,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "慢性期",
        "退院支援充実"
      ],
      "lat": 35.328,
      "lng": 139.3497,
      "nearestStation": null
    },
    {
      "name": "医療法人社団水野会 平塚十全病院",
      "type": "慢性期",
      "beds": 0,
      "wardCount": 4,
      "functions": [
        "慢性期"
      ],
      "nurseCount": 54,
      "ptCount": 2,
      "features": "医療法人。看護配置障害者7:1。看護師54名。医師7名。PT2名。CT1台。退院支援部門あり。慢性期療養病院。",
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
        "退院支援充実",
        "療養"
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
      "beds": 536,
      "wardCount": 15,
      "functions": [
        "高度急性期",
        "急性期"
      ],
      "nurseCount": 603,
      "ptCount": 9,
      "features": "公立。看護配置7:1。三次救急。年間救急車9,607台。DPC標準病院群。看護師603名。医師184名。PT9名。CT5台・MRI2台。ICU・CCU・NICU完備。退院支援部門あり。湘南東部保健医療圏の基幹病院。",
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
        "三次救急",
        "救命救急",
        "公立病院",
        "DPC標準病院群",
        "退院支援充実",
        "7対1看護",
        "大規模病院",
        "ICU",
        "NICU",
        "災害拠点",
        "がん診療",
        "CCU",
        "教育体制充実"
      ],
      "lat": 35.338,
      "lng": 139.487,
      "nearestStation": "藤沢駅"
    },
    {
      "name": "医療法人徳洲会 湘南藤沢徳洲会病院",
      "type": "高度急性期・急性期",
      "beds": 419,
      "wardCount": 11,
      "functions": [
        "急性期",
        "高度急性期"
      ],
      "nurseCount": 409,
      "ptCount": 29,
      "features": "医療法人。看護配置7:1。二次救急。年間救急車10,839台。DPC特定病院群。看護師409名。医師155名。PT29名。CT2台・MRI3台。ICU完備。退院支援部門あり。2012年新築移転。24時間365日救急対応。",
      "access": "辻堂駅徒歩7分",
      "nightShiftType": "三交代制",
      "annualHolidays": 120,
      "salaryMin": 290000,
      "salaryMax": 380000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "充実",
      "matchingTags": [
        "急性期",
        "高度急性期",
        "二次救急",
        "DPC特定病院群",
        "退院支援充実",
        "7対1看護",
        "大規模病院",
        "ICU",
        "リハビリ充実",
        "救急",
        "心臓病センター",
        "24時間救急",
        "徳洲会",
        "駅近"
      ],
      "lat": 35.335,
      "lng": 139.448,
      "nearestStation": "辻堂駅"
    },
    {
      "name": "一般財団法人同友会藤沢湘南台病院",
      "type": "高度急性期・急性期・回復期",
      "beds": 320,
      "wardCount": 7,
      "functions": [
        "急性期",
        "高度急性期",
        "回復期"
      ],
      "nurseCount": 236,
      "ptCount": 19,
      "features": "公益法人。看護配置7:1。二次救急。年間救急車3,514台。DPC標準病院群。看護師236名。医師90名。PT19名。CT2台・MRI1台。緩和ケア完備。退院支援部門あり。急性期一般病棟・回復期リハビリ病棟・緩和ケア病棟・療養病棟の4機能併設。",
      "access": "湘南台駅バス5分",
      "nightShiftType": "三交代制",
      "annualHolidays": 120,
      "salaryMin": 280000,
      "salaryMax": 370000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "充実",
      "matchingTags": [
        "急性期",
        "高度急性期",
        "回復期",
        "二次救急",
        "DPC標準病院群",
        "退院支援充実",
        "7対1看護",
        "中規模病院",
        "回復期リハビリ",
        "緩和ケア",
        "リハビリ充実",
        "慢性期",
        "ケアミックス"
      ],
      "lat": 35.39,
      "lng": 139.468,
      "nearestStation": "湘南台駅"
    },
    {
      "name": "医療法人社団 健育会 湘南慶育病院",
      "type": "急性期・回復期",
      "beds": 230,
      "wardCount": 5,
      "functions": [
        "急性期",
        "回復期"
      ],
      "nurseCount": 122,
      "ptCount": 73,
      "features": "医療法人。看護配置10:1。救急告示。年間救急車243台。看護師122名。医師32名。PT73名。CT1台・MRI1台。退院支援部門あり。先進的医療ICT活用。",
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
        "退院支援充実",
        "中規模病院",
        "回復期リハビリ",
        "リハビリ充実",
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
        "回復期",
        "急性期",
        "慢性期"
      ],
      "nurseCount": 128,
      "ptCount": 15,
      "features": "医療法人。看護配置10:1。二次救急。年間救急車1,062台。看護師128名。医師23名。PT15名。CT1台・MRI1台。緩和ケア完備。退院支援部門あり。急性期・回復期リハビリ・緩和ケア・地域包括ケア・療養の5病棟。",
      "access": "藤沢駅バス10分",
      "nightShiftType": "二交代制",
      "annualHolidays": 115,
      "salaryMin": 280000,
      "salaryMax": 370000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "回復期",
        "急性期",
        "慢性期",
        "二次救急",
        "退院支援充実",
        "回復期リハビリ",
        "緩和ケア",
        "リハビリ充実",
        "ケアミックス",
        "地域包括ケア"
      ],
      "lat": 35.338,
      "lng": 139.487,
      "nearestStation": "藤沢駅"
    },
    {
      "name": "クローバーホスピタル",
      "type": "回復期・慢性期",
      "beds": 173,
      "wardCount": 4,
      "functions": [
        "回復期",
        "慢性期"
      ],
      "nurseCount": 81,
      "ptCount": 40,
      "features": "医療法人。二次救急。看護師81名。医師18名。PT40名。CT1台。退院支援部門あり。",
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
        "二次救急",
        "退院支援充実",
        "回復期リハビリ",
        "リハビリ充実",
        "地域包括ケア"
      ],
      "lat": 35.338,
      "lng": 139.487,
      "nearestStation": "藤沢駅"
    },
    {
      "name": "藤沢御所見病院",
      "type": "急性期・慢性期",
      "beds": 154,
      "wardCount": 3,
      "functions": [
        "慢性期",
        "急性期"
      ],
      "nurseCount": 50,
      "ptCount": 5,
      "features": "医療法人。看護配置地域包括ケア。二次救急。年間救急車96台。看護師50名。医師9名。PT5名。CT1台。退院支援部門あり。",
      "access": "",
      "nightShiftType": "二交代制",
      "annualHolidays": 110,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "慢性期",
        "急性期",
        "二次救急",
        "退院支援充実"
      ],
      "lat": 35.338,
      "lng": 139.487,
      "nearestStation": null
    },
    {
      "name": "湘南長寿園病院",
      "type": "慢性期",
      "beds": 120,
      "wardCount": 2,
      "functions": [
        "慢性期"
      ],
      "nurseCount": 24,
      "ptCount": 2,
      "features": "医療法人。看護師24名。医師6名。PT2名。退院支援部門あり。",
      "access": "",
      "nightShiftType": "二交代制",
      "annualHolidays": 110,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "慢性期",
        "退院支援充実"
      ],
      "lat": 35.338,
      "lng": 139.487,
      "nearestStation": null
    },
    {
      "name": "医療法人長谷川会湘南ホスピタル",
      "type": "回復期・慢性期",
      "beds": 104,
      "wardCount": 2,
      "functions": [
        "慢性期",
        "回復期"
      ],
      "nurseCount": 48,
      "ptCount": 7,
      "features": "医療法人。看護配置地域包括ケア。年間救急車60台。看護師48名。PT7名。CT1台。退院支援部門あり。",
      "access": "",
      "nightShiftType": "二交代制",
      "annualHolidays": 110,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "慢性期",
        "回復期",
        "退院支援充実",
        "回復期リハビリ"
      ],
      "lat": 35.338,
      "lng": 139.487,
      "nearestStation": null
    },
    {
      "name": "医療法人 山内龍馬財団 山内病院",
      "type": "急性期・慢性期",
      "beds": 99,
      "wardCount": 2,
      "functions": [
        "急性期",
        "慢性期"
      ],
      "nurseCount": 52,
      "ptCount": 4,
      "features": "医療法人。看護配置障害者7:1。二次救急。年間救急車83台。看護師52名。医師10名。PT4名。CT1台・MRI1台。障害者施設等入院基本料病棟・地域包括ケア病棟。",
      "access": "藤沢駅バス20分",
      "nightShiftType": "二交代制",
      "annualHolidays": 115,
      "salaryMin": 270000,
      "salaryMax": 360000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "急性期",
        "慢性期",
        "二次救急",
        "回復期",
        "障害者病棟",
        "地域包括ケア",
        "徳洲会"
      ],
      "lat": 35.338,
      "lng": 139.487,
      "nearestStation": "藤沢駅"
    },
    {
      "name": "村田会湘南大庭病院",
      "type": "回復期・慢性期",
      "beds": 99,
      "wardCount": 2,
      "functions": [
        "回復期",
        "慢性期"
      ],
      "nurseCount": 22,
      "ptCount": 5,
      "features": "医療法人。看護配置療養20:1。看護師22名。医師5名。PT5名。CT1台。退院支援部門あり。",
      "access": "",
      "nightShiftType": "二交代制",
      "annualHolidays": 110,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "回復期",
        "慢性期",
        "退院支援充実",
        "回復期リハビリ"
      ],
      "lat": 35.338,
      "lng": 139.487,
      "nearestStation": null
    },
    {
      "name": "医療法人社団正拓会湘南太平台病院",
      "type": "慢性期",
      "beds": 79,
      "wardCount": 2,
      "functions": [
        "慢性期"
      ],
      "nurseCount": 29,
      "ptCount": 3,
      "features": "医療法人。看護配置障害者7:1。二次救急。看護師29名。医師6名。PT3名。CT1台。退院支援部門あり。",
      "access": "",
      "nightShiftType": "二交代制",
      "annualHolidays": 110,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "慢性期",
        "二次救急",
        "退院支援充実"
      ],
      "lat": 35.338,
      "lng": 139.487,
      "nearestStation": null
    },
    {
      "name": "湘南第一病院",
      "type": "急性期",
      "beds": 55,
      "wardCount": 2,
      "functions": [
        "急性期"
      ],
      "nurseCount": 59,
      "ptCount": 12,
      "features": "医療法人。看護配置10:1。二次救急。年間救急車264台。看護師59名。医師10名。PT12名。CT1台。退院支援部門あり。",
      "access": "",
      "nightShiftType": "二交代制",
      "annualHolidays": 110,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "急性期",
        "二次救急",
        "退院支援充実"
      ],
      "lat": 35.338,
      "lng": 139.487,
      "nearestStation": null
    },
    {
      "name": "藤沢脳神経外科病院",
      "type": "急性期",
      "beds": 55,
      "wardCount": 1,
      "functions": [
        "急性期"
      ],
      "nurseCount": 22,
      "ptCount": 3,
      "features": "医療法人。看護配置13:1。二次救急。年間救急車985台。看護師22名。医師5名。PT3名。CT1台・MRI1台。退院支援部門あり。",
      "access": "",
      "nightShiftType": "二交代制",
      "annualHolidays": 110,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "急性期",
        "二次救急",
        "退院支援充実"
      ],
      "lat": 35.338,
      "lng": 139.487,
      "nearestStation": null
    }
  ],
  "茅ヶ崎市": [
    {
      "name": "茅ヶ崎中央病院",
      "type": "急性期・回復期・慢性期",
      "beds": 476,
      "wardCount": 8,
      "functions": [
        "急性期",
        "慢性期",
        "回復期"
      ],
      "nurseCount": 186,
      "ptCount": 40,
      "features": "医療法人。看護配置障害者7:1。二次救急。年間救急車480台。看護師186名。医師37名。PT40名。CT2台・MRI1台。退院支援部門あり。救急告示病院。茅ヶ崎駅徒歩6分の好立地。",
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
        "慢性期",
        "回復期",
        "二次救急",
        "退院支援充実",
        "大規模病院",
        "回復期リハビリ",
        "リハビリ充実",
        "ケアミックス",
        "救急",
        "駅近"
      ],
      "lat": 35.334,
      "lng": 139.404,
      "nearestStation": "茅ヶ崎駅"
    },
    {
      "name": "茅ヶ崎市立病院",
      "type": "高度急性期・急性期",
      "beds": 401,
      "wardCount": 10,
      "functions": [
        "急性期",
        "高度急性期"
      ],
      "nurseCount": 310,
      "ptCount": 6,
      "features": "公立。看護配置7:1。二次救急。年間救急車5,037台。DPC標準病院群。看護師310名。医師104名。PT6名。CT2台・MRI2台。退院支援部門あり。地域医療支援病院・災害拠点病院・DMAT指定病院。人工関節手術支援ロボットMako導入。",
      "access": "北茅ヶ崎駅徒歩10分",
      "nightShiftType": "三交代制",
      "annualHolidays": 120,
      "salaryMin": 290000,
      "salaryMax": 380000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "充実",
      "matchingTags": [
        "急性期",
        "高度急性期",
        "二次救急",
        "公立病院",
        "DPC標準病院群",
        "退院支援充実",
        "7対1看護",
        "大規模病院",
        "災害拠点",
        "DMAT",
        "ICU",
        "NICU",
        "ロボット手術",
        "教育体制充実"
      ],
      "lat": 35.334,
      "lng": 139.404,
      "nearestStation": "茅ヶ崎駅"
    },
    {
      "name": "湘南東部総合病院",
      "type": "高度急性期・急性期・回復期・慢性期",
      "beds": 327,
      "wardCount": 9,
      "functions": [
        "急性期",
        "高度急性期",
        "慢性期",
        "回復期"
      ],
      "nurseCount": 243,
      "ptCount": 74,
      "features": "医療法人。看護配置7:1。二次救急。年間救急車3,343台。DPC標準病院群。看護師243名。医師46名。PT74名。CT3台・MRI2台。ICU完備。退院支援部門あり。4機能すべてを持つ総合病院。",
      "access": "茅ヶ崎駅バス10分",
      "nightShiftType": "三交代制",
      "annualHolidays": 120,
      "salaryMin": 280000,
      "salaryMax": 370000,
      "ptSalaryMin": 250000,
      "ptSalaryMax": 320000,
      "educationLevel": "充実",
      "matchingTags": [
        "急性期",
        "高度急性期",
        "慢性期",
        "回復期",
        "二次救急",
        "DPC標準病院群",
        "退院支援充実",
        "7対1看護",
        "中規模病院",
        "ICU",
        "回復期リハビリ",
        "リハビリ充実",
        "ケアミックス",
        "緩和ケア"
      ],
      "lat": 35.334,
      "lng": 139.404,
      "nearestStation": "茅ヶ崎駅"
    },
    {
      "name": "医療法人社団湘南健友会 長岡病院",
      "type": "慢性期",
      "beds": 162,
      "wardCount": 3,
      "functions": [
        "慢性期"
      ],
      "nurseCount": 31,
      "ptCount": null,
      "features": "医療法人。看護配置療養20:1。看護師31名。CT1台。慢性期医療に特化。",
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
      "nurseCount": 51,
      "ptCount": 25,
      "features": "医療法人。看護配置障害者7:1。看護師51名。医師8名。PT25名。CT1台。回復期リハビリ・慢性期療養。",
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
        "リハビリ充実",
        "療養"
      ],
      "lat": 35.357,
      "lng": 139.378,
      "nearestStation": "香川駅"
    },
    {
      "name": "医療法人徳洲会 茅ヶ崎徳洲会病院",
      "type": "急性期",
      "beds": 144,
      "wardCount": 5,
      "functions": [
        "急性期"
      ],
      "nurseCount": 113,
      "ptCount": 11,
      "features": "医療法人。看護配置10:1。二次救急。年間救急車1,914台。DPC標準病院群。看護師113名。医師25名。PT11名。CT1台・MRI1台。HCU完備。退院支援部門あり。",
      "access": "茅ヶ崎駅バス5分",
      "nightShiftType": "二交代制",
      "annualHolidays": 115,
      "salaryMin": 280000,
      "salaryMax": 370000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "急性期",
        "二次救急",
        "DPC標準病院群",
        "退院支援充実",
        "HCU",
        "高度急性期",
        "徳洲会"
      ],
      "lat": 35.334,
      "lng": 139.404,
      "nearestStation": "茅ヶ崎駅"
    },
    {
      "name": "宗教法人寒川神社 寒川病院",
      "type": "急性期",
      "beds": 99,
      "wardCount": 2,
      "functions": [
        "急性期"
      ],
      "nurseCount": 76,
      "ptCount": 8,
      "features": "その他。看護配置10:1。救急告示。年間救急車448台。看護師76名。医師12名。PT8名。CT1台・MRI1台。退院支援部門あり。",
      "access": "",
      "nightShiftType": "二交代制",
      "annualHolidays": 110,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "急性期",
        "退院支援充実"
      ],
      "lat": 35.334,
      "lng": 139.404,
      "nearestStation": null
    }
  ],
  "大磯町・二宮町": [
    {
      "name": "徳洲会湘南大磯病院",
      "type": "高度急性期・急性期",
      "beds": 312,
      "wardCount": 3,
      "functions": [
        "急性期",
        "高度急性期"
      ],
      "nurseCount": 132,
      "ptCount": 6,
      "features": "医療法人。看護配置7:1。二次救急。年間救急車801台。DPC標準病院群。看護師132名。医師33名。PT6名。CT1台・MRI1台。退院支援部門あり。中郡（大磯・二宮）唯一の総合病院。24時間救急対応。一部休棟中で看護師需要あり。",
      "access": "大磯駅・二宮駅よりシャトルバス運行",
      "nightShiftType": "二交代制",
      "annualHolidays": 120,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "充実",
      "matchingTags": [
        "急性期",
        "高度急性期",
        "二次救急",
        "DPC標準病院群",
        "退院支援充実",
        "7対1看護",
        "中規模病院",
        "24時間救急",
        "徳洲会",
        "看護師増員中"
      ],
      "lat": 35.312,
      "lng": 139.311,
      "nearestStation": "大磯駅"
    }
  ],
  "南足柄市・開成町・大井町・松田町・山北町": [
    {
      "name": "医療法人社団明芳会北小田原病院",
      "type": "慢性期",
      "beds": 345,
      "wardCount": 1,
      "functions": [
        "慢性期"
      ],
      "nurseCount": 84,
      "ptCount": 4,
      "features": "医療法人。看護配置療養20:1。看護師84名。医師9名。PT4名。CT1台。療養型病院。",
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
        "中規模病院",
        "療養",
        "少人数"
      ],
      "lat": 35.33,
      "lng": 139.11,
      "nearestStation": "大雄山駅"
    },
    {
      "name": "神奈川県立足柄上病院",
      "type": "高度急性期・急性期・回復期",
      "beds": 296,
      "wardCount": 6,
      "functions": [
        "高度急性期",
        "回復期",
        "急性期"
      ],
      "nurseCount": 242,
      "ptCount": 10,
      "features": "公立。看護配置7:1。二次救急。年間救急車2,677台。DPC標準病院群。看護師242名。医師58名。PT10名。CT2台・MRI1台。HCU完備。退院支援部門あり。",
      "access": "",
      "nightShiftType": "二交代制",
      "annualHolidays": 110,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "高度急性期",
        "回復期",
        "急性期",
        "二次救急",
        "公立病院",
        "DPC標準病院群",
        "退院支援充実",
        "7対1看護",
        "中規模病院",
        "HCU",
        "回復期リハビリ"
      ],
      "lat": null,
      "lng": null,
      "nearestStation": null
    },
    {
      "name": "佐藤病院",
      "type": "慢性期",
      "beds": 184,
      "wardCount": 1,
      "functions": [
        "慢性期"
      ],
      "nurseCount": 33,
      "ptCount": null,
      "features": "医療法人。看護師33名。医師26名。CT1台。",
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
      "name": "大内病院",
      "type": "急性期",
      "beds": 53,
      "wardCount": 1,
      "functions": [
        "急性期"
      ],
      "nurseCount": 25,
      "ptCount": 4,
      "features": "医療法人。看護配置15:1。二次救急。年間救急車48台。看護師25名。医師4名。PT4名。CT1台。退院支援部門あり。南足柄市唯一の急性期病院。",
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
        "二次救急",
        "退院支援充実",
        "少人数",
        "駅近"
      ],
      "lat": 35.323,
      "lng": 139.121,
      "nearestStation": "和田河原駅"
    },
    {
      "name": "医療法人 陽風会 高台病院",
      "type": "慢性期",
      "beds": 0,
      "wardCount": 6,
      "functions": [
        "慢性期"
      ],
      "nurseCount": 70,
      "ptCount": 3,
      "features": "医療法人。看護配置療養20:1。看護師70名。医師7名。PT3名。CT1台。退院支援部門あり。",
      "access": "",
      "nightShiftType": "二交代制",
      "annualHolidays": 110,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "慢性期",
        "退院支援充実"
      ],
      "lat": null,
      "lng": null,
      "nearestStation": null
    },
    {
      "name": "日野原記念ピースハウス病院",
      "type": "慢性期",
      "beds": 0,
      "wardCount": 1,
      "functions": [
        "慢性期"
      ],
      "nurseCount": 32,
      "ptCount": null,
      "features": "その他。看護師32名。医師4名。緩和ケア完備。",
      "access": "",
      "nightShiftType": "二交代制",
      "annualHolidays": 110,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "慢性期",
        "緩和ケア"
      ],
      "lat": null,
      "lng": null,
      "nearestStation": null
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
      "nurseCount": 1038,
      "ptCount": 11,
      "features": "学校法人。三次救急。年間救急車6,800台。看護師1038名。医師550名。PT11名。CT5台・MRI6台。HCU・ICU・NICU完備。退院支援部門あり。大学病院。がん診療連携拠点病院。",
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
        "三次救急",
        "救命救急",
        "退院支援充実",
        "大規模病院",
        "HCU",
        "ICU",
        "NICU",
        "大学病院",
        "3次救急",
        "ドクターヘリ",
        "がん診療",
        "教育体制充実",
        "キャリアアップ"
      ],
      "lat": 35.395,
      "lng": 139.314,
      "nearestStation": "伊勢原駅"
    },
    {
      "name": "神奈川県厚生農業協同組合連合会 伊勢原協同病院",
      "type": "高度急性期・急性期・回復期",
      "beds": 350,
      "wardCount": 10,
      "functions": [
        "急性期",
        "回復期",
        "高度急性期"
      ],
      "nurseCount": 349,
      "ptCount": 36,
      "features": "公的。二次救急。年間救急車3,236台。DPC標準病院群。看護師349名。医師81名。PT36名。CT2台・MRI2台。HCU・緩和ケア完備。退院支援部門あり。地域中核病院。開設50年以上の実績。",
      "access": "伊勢原駅バス8分",
      "nightShiftType": "三交代制",
      "annualHolidays": 120,
      "salaryMin": 280000,
      "salaryMax": 370000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "充実",
      "matchingTags": [
        "急性期",
        "回復期",
        "高度急性期",
        "二次救急",
        "公的病院",
        "DPC標準病院群",
        "退院支援充実",
        "中規模病院",
        "回復期リハビリ",
        "HCU",
        "緩和ケア",
        "リハビリ充実",
        "教育体制充実"
      ],
      "lat": 35.395,
      "lng": 139.314,
      "nearestStation": "伊勢原駅"
    },
    {
      "name": "医療法人社団三井会 伊勢原日向病院",
      "type": "慢性期",
      "beds": 202,
      "wardCount": 1,
      "functions": [
        "慢性期"
      ],
      "nurseCount": 46,
      "ptCount": 4,
      "features": "医療法人。看護配置療養20:1。看護師46名。医師7名。PT4名。退院支援部門あり。慢性期医療に特化。",
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
        "退院支援充実",
        "中規模病院",
        "療養"
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
      "beds": 347,
      "wardCount": 9,
      "functions": [
        "急性期",
        "高度急性期"
      ],
      "nurseCount": 352,
      "ptCount": 7,
      "features": "公立。看護配置7:1。二次救急。年間救急車4,811台。DPC標準病院群。看護師352名。医師94名。PT7名。CT3台・MRI2台。HCU・ICU完備。退院支援部門あり。救急告示病院・災害拠点指定病院。県立病院から市立に転換。地域の基幹病院。",
      "access": "本厚木駅バス15分",
      "nightShiftType": "三交代制",
      "annualHolidays": 120,
      "salaryMin": 290000,
      "salaryMax": 380000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "充実",
      "matchingTags": [
        "急性期",
        "高度急性期",
        "二次救急",
        "公立病院",
        "DPC標準病院群",
        "退院支援充実",
        "7対1看護",
        "中規模病院",
        "HCU",
        "ICU",
        "救急",
        "災害拠点",
        "教育体制充実"
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
        "慢性期",
        "回復期",
        "急性期"
      ],
      "nurseCount": 240,
      "ptCount": 56,
      "features": "公立。看護配置障害者7:1。看護師240名。医師38名。PT56名。CT1台・MRI1台。退院支援部門あり。県立リハビリ専門病院。脊髄損傷・脳神経疾患・骨関節疾患・小児リハビリ・神経難病に対応。全国初の県立リハビリ専門病院。",
      "access": "本厚木駅バス30分（七沢エリア）",
      "nightShiftType": "三交代制",
      "annualHolidays": 120,
      "salaryMin": 280000,
      "salaryMax": 370000,
      "ptSalaryMin": 250000,
      "ptSalaryMax": 320000,
      "educationLevel": "充実",
      "matchingTags": [
        "慢性期",
        "回復期",
        "急性期",
        "公立病院",
        "退院支援充実",
        "中規模病院",
        "回復期リハビリ",
        "ICU",
        "リハビリ充実",
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
      "name": "東名厚木病院",
      "type": "急性期",
      "beds": 289,
      "wardCount": 7,
      "functions": [
        "急性期"
      ],
      "nurseCount": 285,
      "ptCount": 17,
      "features": "医療法人。二次救急。年間救急車4,446台。DPC標準病院群。看護師285名。医師69名。PT17名。CT2台・MRI1台。HCU完備。退院支援部門あり。神奈川県がん診療連携指定病院。救急告示病院。緩和ケア病床あり。",
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
        "二次救急",
        "DPC標準病院群",
        "退院支援充実",
        "中規模病院",
        "HCU",
        "リハビリ充実",
        "がん診療",
        "救急",
        "緩和ケア"
      ],
      "lat": 35.441,
      "lng": 139.365,
      "nearestStation": "本厚木駅"
    },
    {
      "name": "医療法人徳洲会 湘南厚木病院",
      "type": "高度急性期・急性期・回復期",
      "beds": 253,
      "wardCount": 7,
      "functions": [
        "急性期",
        "回復期",
        "高度急性期"
      ],
      "nurseCount": 167,
      "ptCount": 26,
      "features": "医療法人。看護配置10:1。二次救急。年間救急車2,334台。DPC標準病院群。看護師167名。医師50名。PT26名。CT2台・MRI1台。HCU完備。退院支援部門あり。急性期から回復期まで一貫対応。",
      "access": "本厚木駅バス12分",
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
        "高度急性期",
        "二次救急",
        "DPC標準病院群",
        "退院支援充実",
        "中規模病院",
        "回復期リハビリ",
        "HCU",
        "リハビリ充実",
        "慢性期",
        "ケアミックス",
        "徳洲会"
      ],
      "lat": 35.441,
      "lng": 139.365,
      "nearestStation": "本厚木駅"
    },
    {
      "name": "医療法人社団葵会 AOI七沢リハビリテーション病院",
      "type": "回復期",
      "beds": 245,
      "wardCount": 5,
      "functions": [
        "回復期"
      ],
      "nurseCount": 75,
      "ptCount": 57,
      "features": "医療法人。看護師75名。PT57名。CT1台。退院支援部門あり。",
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
        "退院支援充実",
        "中規模病院",
        "回復期リハビリ",
        "リハビリ充実",
        "リハビリ専門"
      ],
      "lat": 35.441,
      "lng": 139.365,
      "nearestStation": "本厚木駅"
    },
    {
      "name": "厚木佐藤病院",
      "type": "急性期・回復期・慢性期",
      "beds": 184,
      "wardCount": 3,
      "functions": [
        "急性期",
        "回復期",
        "慢性期"
      ],
      "nurseCount": 67,
      "ptCount": 9,
      "features": "医療法人。看護配置10:1。看護師67名。医師11名。PT9名。CT1台・MRI1台。退院支援部門あり。",
      "access": "",
      "nightShiftType": "二交代制",
      "annualHolidays": 110,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "急性期",
        "回復期",
        "慢性期",
        "退院支援充実",
        "回復期リハビリ",
        "リハビリ充実"
      ],
      "lat": 35.441,
      "lng": 139.365,
      "nearestStation": null
    },
    {
      "name": "仁厚会病院",
      "type": "急性期・慢性期",
      "beds": 131,
      "wardCount": 3,
      "functions": [
        "慢性期",
        "急性期"
      ],
      "nurseCount": 60,
      "ptCount": 5,
      "features": "医療法人。看護配置療養20:1。二次救急。年間救急車568台。看護師60名。医師15名。PT5名。CT1台・MRI1台。退院支援部門あり。",
      "access": "",
      "nightShiftType": "二交代制",
      "annualHolidays": 110,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "慢性期",
        "急性期",
        "二次救急",
        "退院支援充実"
      ],
      "lat": 35.441,
      "lng": 139.365,
      "nearestStation": null
    },
    {
      "name": "医療法人仁愛会近藤病院",
      "type": "慢性期",
      "beds": 111,
      "wardCount": 2,
      "functions": [
        "慢性期"
      ],
      "nurseCount": 30,
      "ptCount": null,
      "features": "医療法人。看護配置障害者7:1。二次救急。年間救急車36台。看護師30名。医師5名。CT1台。",
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
        "二次救急",
        "障害者病棟"
      ],
      "lat": 35.441,
      "lng": 139.365,
      "nearestStation": "本厚木駅"
    },
    {
      "name": "医療法人鉄蕉会 亀田森の里病院",
      "type": "急性期",
      "beds": 60,
      "wardCount": 2,
      "functions": [
        "急性期"
      ],
      "nurseCount": 38,
      "ptCount": 6,
      "features": "医療法人。看護配置10:1。二次救急。年間救急車142台。看護師38名。医師11名。PT6名。CT1台・MRI1台。退院支援部門あり。",
      "access": "",
      "nightShiftType": "二交代制",
      "annualHolidays": 110,
      "salaryMin": 270000,
      "salaryMax": 350000,
      "ptSalaryMin": null,
      "ptSalaryMax": null,
      "educationLevel": "あり",
      "matchingTags": [
        "急性期",
        "二次救急",
        "退院支援充実"
      ],
      "lat": 35.441,
      "lng": 139.365,
      "nearestStation": null
    }
  ],
  "海老名市": [
    {
      "name": "社会医療法人ジャパンメディカルアライアンス 海老名総合病院",
      "type": "高度急性期・急性期",
      "beds": 479,
      "wardCount": 14,
      "functions": [
        "急性期",
        "高度急性期"
      ],
      "nurseCount": 473,
      "ptCount": 54,
      "features": "医療法人。看護配置7:1。三次救急。年間救急車8,998台。DPC標準病院群。看護師473名。医師148名。PT54名。CT3台・MRI3台。HCU・ICU・SCU完備。退院支援部門あり。地域医療支援病院。手術室14室。24時間365日断らない救急。",
      "access": "海老名駅東口徒歩12分、シャトルバスあり",
      "nightShiftType": "三交代制",
      "annualHolidays": 120,
      "salaryMin": 300000,
      "salaryMax": 390000,
      "ptSalaryMin": 260000,
      "ptSalaryMax": 330000,
      "educationLevel": "充実",
      "matchingTags": [
        "急性期",
        "高度急性期",
        "三次救急",
        "救命救急",
        "DPC標準病院群",
        "退院支援充実",
        "7対1看護",
        "大規模病院",
        "HCU",
        "ICU",
        "SCU",
        "リハビリ充実",
        "3次救急",
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
        "回復期",
        "急性期",
        "慢性期"
      ],
      "nurseCount": 93,
      "ptCount": 34,
      "features": "医療法人。看護配置10:1。二次救急。年間救急車344台。看護師93名。医師14名。PT34名。CT1台・MRI1台。退院支援部門あり。一般・回復期・療養の3機能併設。",
      "access": "さがみ野駅徒歩圏",
      "nightShiftType": "二交代制",
      "annualHolidays": 115,
      "salaryMin": 280000,
      "salaryMax": 370000,
      "ptSalaryMin": 260000,
      "ptSalaryMax": 330000,
      "educationLevel": "あり",
      "matchingTags": [
        "回復期",
        "急性期",
        "慢性期",
        "二次救急",
        "退院支援充実",
        "回復期リハビリ",
        "リハビリ充実",
        "ケアミックス",
        "駅近"
      ],
      "lat": 35.459,
      "lng": 139.401,
      "nearestStation": "さがみ野駅"
    },
    {
      "name": "医療法人社団神愛会オアシス湘南病院",
      "type": "慢性期",
      "beds": 158,
      "wardCount": 3,
      "functions": [
        "慢性期"
      ],
      "nurseCount": 30,
      "ptCount": 1,
      "features": "医療法人。看護配置療養20:1。看護師30名。医師5名。PT1名。CT1台。退院支援部門あり。慢性期医療に特化。",
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
        "退院支援充実",
        "療養"
      ],
      "lat": 35.447,
      "lng": 139.391,
      "nearestStation": "海老名駅"
    },
    {
      "name": "医療法人社団 さがみ野中央病院",
      "type": "急性期・回復期",
      "beds": 96,
      "wardCount": 2,
      "functions": [
        "急性期",
        "回復期"
      ],
      "nurseCount": 42,
      "ptCount": 20,
      "features": "医療法人。看護配置13:1。二次救急。年間救急車438台。看護師42名。医師9名。PT20名。CT1台・MRI1台。一般・回復期2病棟。",
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
        "二次救急",
        "回復期リハビリ",
        "リハビリ充実",
        "少人数",
        "駅近"
      ],
      "lat": 35.459,
      "lng": 139.401,
      "nearestStation": "さがみ野駅"
    }
  ]
};
