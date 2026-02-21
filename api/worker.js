// ========================================
// ROBBY THE MATCH - Cloudflare Workers API
// フォーム送信プロキシ / Slack通知 / AIチャット / Google Sheets連携
// ========================================

// レート制限ストア（KVが未設定の場合のインメモリフォールバック）
const rateLimitMap = new Map();

// チャットセッション レート制限ストア
const phoneSessionMap = new Map(); // phone → { count, windowStart }
let globalSessionCount = { count: 0, windowStart: 0 }; // global hourly limit

// ---------- AIチャット用システムプロンプト（サーバー側管理） ----------

// エリア別医療機関データベース（病院機能報告 令和6年度ベース）
const AREA_DATABASE = {
  "小田原": { hospitals: 11, majorHospitals: "小田原市立病院（417床・看護師270名）、小澤病院（202床）、小林病院（163床）、山近記念総合病院（108床）、小田原循環器病院（97床）、間中病院（90床）", salary: "月給28〜38万円", demand: "高" },
  "秦野": { hospitals: 4, majorHospitals: "秦野赤十字病院（308床・看護師155名）、鶴巻温泉病院（505床・168名）、神奈川病院（300床・111名）、八木病院（88床）", salary: "月給27〜35万円", demand: "高" },
  "平塚": { hospitals: 7, majorHospitals: "平塚共済病院（441床・看護師301名）、平塚市民病院（412床・315名）、済生会湘南平塚病院（176床）、ふれあい平塚ホスピタル（125床・PT32名）", salary: "月給28〜37万円", demand: "高" },
  "藤沢": { hospitals: 14, majorHospitals: "藤沢市民病院（530床・看護師405名）、湘南藤沢徳洲会病院（419床・282名）、藤沢湘南台病院（330床）、湘南慶育病院（230床）、湘南中央病院（199床）", salary: "月給29〜38万円", demand: "非常に高い" },
  "茅ヶ崎": { hospitals: 7, majorHospitals: "茅ヶ崎市立病院（401床・看護師216名）、茅ヶ崎中央病院（324床・PT20名）、湘南東部総合病院（323床・176名）、茅ヶ崎徳洲会病院（132床）", salary: "月給28〜37万円", demand: "高" },
  "大磯・二宮": { hospitals: 1, majorHospitals: "湘南大磯病院（312床・看護師90名）※中郡唯一の総合病院", salary: "月給27〜35万円", demand: "中〜高" },
  "南足柄・開成・大井": { hospitals: 4, majorHospitals: "勝又高台病院（310床・看護師71名）、大内病院（53床）、北小田原病院（55床）", salary: "月給26〜34万円", demand: "中" },
  "伊勢原": { hospitals: 3, majorHospitals: "東海大学医学部付属病院（804床・看護師741名）※県西最大、伊勢原協同病院（350床・239名）", salary: "月給28〜37万円", demand: "非常に高い" },
  "厚木": { hospitals: 9, majorHospitals: "厚木市立病院（341床・看護師233名）、東名厚木病院（282床・205名）、神奈川リハビリテーション病院（324床・PT18名）、AOI七沢リハ（245床・PT53名・OT35名）", salary: "月給28〜37万円", demand: "高" },
  "海老名": { hospitals: 4, majorHospitals: "海老名総合病院（479床・看護師431名・PT56名）※県央唯一の救命救急センター、湘陽かしわ台病院（199床）", salary: "月給29〜38万円", demand: "非常に高い" },
};

// 職種別 給与・勤務データ（システムプロンプト注入用）
const SALARY_DATA = {
  "看護師": {
    急性期: "新卒27〜29万/3〜5年29〜33万/5〜10年32〜37万/10年以上35〜42万/主任37〜43万/師長42〜50万",
    回復期: "新卒26〜28万/3〜5年28〜32万/5〜10年30〜35万/10年以上33〜39万",
    療養型: "新卒25〜27万/3〜5年27〜31万/5〜10年29〜34万/10年以上32〜38万",
    クリニック: "新卒25〜28万/3〜5年27〜31万/5〜10年29〜34万/10年以上31〜37万",
    訪問看護: "新卒28〜30万/3〜5年30〜34万/5〜10年33〜38万/10年以上35〜42万",
    介護施設: "新卒25〜27万/3〜5年27〜30万/5〜10年29〜33万/10年以上31〜36万",
  },
  "理学療法士": {
    急性期: "新卒23〜25万/3〜5年25〜29万/5〜10年28〜33万/10年以上31〜37万/主任33〜39万",
    回復期: "新卒23〜25万/3〜5年25〜28万/5〜10年27〜32万/10年以上30〜35万",
    訪問リハ: "新卒25〜27万/3〜5年27〜31万/5〜10年30〜35万/10年以上33〜38万",
    クリニック: "新卒22〜24万/3〜5年24〜28万/5〜10年27〜31万/10年以上29〜34万",
    介護施設: "新卒22〜24万/3〜5年24〜27万/5〜10年26〜30万/10年以上28〜33万",
  },
};

const SHIFT_DATA = `【勤務形態パターン】
二交代制: 日勤8:30〜17:30/夜勤16:30〜翌9:00（月4〜5回・1回1〜1.5万円）※中小規模に多い
三交代制: 日勤8:30〜17:00/準夜16:00〜翌0:30/深夜0:00〜8:30（夜勤月8〜10回）※大規模急性期に多い
日勤のみ: 8:30〜17:30 ※クリニック・訪問看護・外来。夜勤手当なし分月3〜5万低め`;

const MARKET_DATA = `【神奈川県西部 求人市場】
看護師求人倍率: 2.0〜2.5倍（非常に高い）/ PT求人倍率: 8.68倍（全国平均4.13倍の2倍以上）
市場動向: 回復期・地域包括ケア需要急増、訪問看護ステーション開設ラッシュ
人気条件: 残業月10h以内/年休120日以上/託児所あり/日勤のみ可/車通勤可/ブランク可
年代別重視: 20代→教育体制・キャリアアップ / 30代→WLB・託児所 / 40代→通勤距離・柔軟シフト`;

// ---------- 外部公開求人データ（2026年2月時点） ----------
const EXTERNAL_JOBS = {
  nurse: {
    "小田原": [
      "小澤病院: 月給26〜38万円/日勤のみ可/小田原駅徒歩7分/ブランクOK",
      "小田原医師会訪問看護ST: 年収460万〜/日勤8:30-17:00/年休120日+/有給消化率100%",
      "ソフィアメディ訪問看護小田原: 月給34.4〜37.7万円/年休120日+冬季5日/未経験80%入職",
      "精神科特化型訪問看護ST: 月給30〜35万円/完全週休2日/オンコールなし/精神科未経験OK",
      "湘南美容クリニック小田原院: 月給35〜40万円/日勤のみ/小田原駅徒歩1分/賞与年2回+ミニボーナス年4回",
      "潤生園(介護施設): 月給32.9万円/ブランクOK/研修あり",
    ],
    "平塚": [
      "平塚市民病院: 月給28〜38万円/日勤・夜専・日夜勤選択可/週4or5日選択可/年休120日+/公立",
      "研水会平塚病院(精神科): 月給26.4〜41.9万円/賞与年3回/院内託児所/実働7h/残業ほぼなし",
      "くすのき在宅診療所: 年収448〜688万円/日勤8:30-17:00/年休120日+土日祝休/平塚最大級の在宅",
      "カメリア桜ヶ丘(特養): 月給28〜35万円/夜勤看護師配置でオンコールなし",
    ],
    "秦野": [
      "ニチイケアセンターまほろば(デイ): 月給26〜32万円/日勤/ブランクOK/大手ニチイ",
      "介護老人保健施設(南矢名): 月給32万〜/日勤のみ/東海大学前駅徒歩2分/退職金あり",
    ],
    "厚木": [
      "ケアミックス型病院(本厚木): 月給28〜38万円/完全週休2日/本厚木駅徒歩5分/託児手当/看護師寮",
      "厚木徳洲会病院: 月給29〜38万円/2交代or3交代選択可/24h救急/心臓血管外科",
      "帝人グループ訪問看護ST: 月給30〜37万円/完全週休2日/東証一部上場グループ",
    ],
    "海老名": [
      "アンビス医療施設型ホスピス: 月給30〜37万円/終末期ケアスキル習得/全国展開",
      "オアシス湘南病院(療養型): 月給27〜36万円/入院透析/リハビリ充実",
    ],
    "伊勢原": [
      "東海大学医学部付属病院: 月給29〜38万円/3交代/年休120日+/県西最大804床/看護師741名",
    ],
  },
  pt: {
    "小田原": [
      "ケアミックス病院(163床): 月給23.5〜25.7万円/日勤/小田原駅徒歩5分/入院・外来・訪問リハ",
      "小澤病院リハ科: 月給24〜30万円/PT・OT・ST同時募集/回復期リハ病棟あり",
      "訪問看護STトモ小田原: 月給28〜35万円/完全週休2日/在宅リハビリ",
      "グレースヒル・湘南(老健): 年収402万〜/年休122日/中井町",
    ],
    "平塚": [
      "リハビリクリニック(平塚駅南口): 月給25〜33万円/年休120日土日祝休/駅徒歩4分",
    ],
    "厚木": [
      "とうめい厚木クリニック: 年収400〜450万円/整形外科90%/無料送迎バス/退職金・住居手当",
      "AOI七沢リハ病院: 月給25〜33万円/PT53名・OT35名の大規模チーム/回復期特化245床",
    ],
    "南足柄・開成": [
      "あじさいの郷(老健): 月給24〜30万円/正社員・パート同時募集",
      "にじの丘足柄(老健): 月給24〜31万円/地域リハビリ",
    ],
  },
};

// ---------- 施設詳細データベース（マッチング用） ----------
const FACILITY_DATABASE = {
  "小田原": [
    { name: "小田原市立病院", type: "高度急性期・急性期", beds: 417, nurseCount: 270, features: "地域医療支援病院・救命救急センター・災害拠点病院。2026年新築移転予定。ICU・NICU完備。", access: "小田原駅バス10分", nightShiftType: "三交代制", annualHolidays: 120, salaryMin: 280000, salaryMax: 380000, educationLevel: "充実", matchingTags: ["高度急性期", "急性期", "救命救急", "災害拠点", "がん診療", "ICU", "NICU", "公立病院", "教育体制充実", "新築移転"] },
    { name: "小澤病院", type: "急性期", beds: 202, nurseCount: 96, features: "脳外科・整形外科を中心とした地域密着型総合病院。", access: "小田原駅バス15分", nightShiftType: "二交代制", annualHolidays: 115, salaryMin: 280000, salaryMax: 370000, educationLevel: "あり", matchingTags: ["急性期", "脳外科", "整形外科", "地域密着"] },
    { name: "小林病院", type: "急性期・回復期・慢性期", beds: 163, nurseCount: 40, features: "100年以上の歴史。一般病棟・回復期リハビリ病棟・療養病棟を併設。", access: "小田原駅バス15分", nightShiftType: "二交代制", annualHolidays: 115, salaryMin: 270000, salaryMax: 350000, educationLevel: "あり", matchingTags: ["急性期", "回復期", "慢性期", "ケアミックス", "回復期リハビリ", "地域密着"] },
    { name: "山近記念総合病院", type: "急性期", beds: 108, nurseCount: 59, features: "救急病院指定。人間ドック対応。", access: "小田原駅バス12分", nightShiftType: "二交代制", annualHolidays: 115, salaryMin: 280000, salaryMax: 370000, educationLevel: "あり", matchingTags: ["急性期", "救急", "人間ドック"] },
    { name: "小田原循環器病院", type: "高度急性期・急性期", beds: 97, nurseCount: 60, features: "循環器専門病院。心臓カテーテル治療に強み。HCU完備。", access: "小田原駅車10分", nightShiftType: "二交代制", annualHolidays: 110, salaryMin: 290000, salaryMax: 380000, educationLevel: "なし", matchingTags: ["高度急性期", "急性期", "循環器", "心臓カテーテル", "HCU", "専門病院"] },
    { name: "間中病院", type: "急性期・回復期", beds: 90, nurseCount: 43, ptCount: 25, features: "地域包括ケア病棟・回復期リハビリ病棟併設。リハスタッフ充実。", access: "小田原駅車8分", nightShiftType: "二交代制", annualHolidays: 110, salaryMin: 270000, salaryMax: 350000, ptSalaryMin: 250000, ptSalaryMax: 320000, educationLevel: "なし", matchingTags: ["急性期", "回復期", "地域包括ケア", "回復期リハビリ", "リハビリ充実"] },
    { name: "箱根病院", type: "慢性期", beds: 199, nurseCount: 93, features: "国立病院機構。慢性期医療に特化。", access: "小田原駅バス20分", nightShiftType: "二交代制", annualHolidays: 120, salaryMin: 270000, salaryMax: 360000, educationLevel: "あり", matchingTags: ["慢性期", "療養", "国立病院機構", "公的病院"] },
    { name: "西湘病院", type: "急性期・慢性期", beds: 102, nurseCount: 30, features: "一般病棟・療養病棟を併設。救急病院指定。", access: "鴨宮駅徒歩10分", nightShiftType: "二交代制", annualHolidays: 115, salaryMin: 270000, salaryMax: 350000, educationLevel: "あり", matchingTags: ["急性期", "慢性期", "療養", "救急", "駅近"] },
    { name: "丹羽病院", type: "急性期", beds: 51, nurseCount: 33, features: "急性期機能病床51床。地域密着型。", access: "小田原駅車10分", nightShiftType: "二交代制", annualHolidays: 110, salaryMin: 270000, salaryMax: 350000, educationLevel: "なし", matchingTags: ["急性期", "地域密着", "少人数"] },
    { name: "小田原市訪問看護ステーション", type: "訪問看護", beds: null, nurseCount: 12, features: "市直営。24時間オンコール対応。在宅医療の中核。", access: "小田原駅バス8分", nightShiftType: "オンコール", annualHolidays: 125, salaryMin: 310000, salaryMax: 380000, educationLevel: "あり", matchingTags: ["訪問看護", "日勤のみ", "オンコール", "公的機関", "ブランクOK"] },
    { name: "ケアステーション鴨宮", type: "訪問看護", beds: null, nurseCount: 8, features: "小児から高齢者まで幅広く対応。働きやすい環境。", access: "鴨宮駅徒歩7分", nightShiftType: "オンコール", annualHolidays: 120, salaryMin: 300000, salaryMax: 370000, educationLevel: "あり", matchingTags: ["訪問看護", "日勤のみ", "オンコール", "駅近", "残業少なめ"] },
    { name: "小田原内科・循環器クリニック", type: "クリニック", beds: null, nurseCount: 6, features: "内科・循環器科の外来クリニック。日勤のみで残業少なめ。", access: "小田原駅徒歩5分", nightShiftType: "なし", annualHolidays: 125, salaryMin: 260000, salaryMax: 330000, educationLevel: "あり", matchingTags: ["クリニック", "日勤のみ", "残業少なめ", "駅近", "パート可"] },
    { name: "足柄上クリニック", type: "クリニック", beds: null, nurseCount: 5, features: "内科・小児科・皮膚科の一般外来。アットホームな雰囲気。", access: "小田原駅車10分", nightShiftType: "なし", annualHolidays: 120, salaryMin: 260000, salaryMax: 320000, educationLevel: "あり", matchingTags: ["クリニック", "日勤のみ", "残業少なめ", "ブランクOK", "パート可"] },
    { name: "介護老人保健施設こゆるぎ", type: "介護老人保健施設", beds: 100, nurseCount: 10, features: "入所定員100名。在宅復帰を目指したリハビリに注力。", access: "小田原駅バス15分", nightShiftType: "オンコール", annualHolidays: 115, salaryMin: 270000, salaryMax: 350000, educationLevel: "あり", matchingTags: ["介護施設", "日勤のみ", "オンコール", "ブランクOK", "残業少なめ"] },
    { name: "小田原東訪問看護ステーション", type: "訪問看護", beds: null, nurseCount: 7, features: "ターミナルケア・精神科訪問看護にも対応。", access: "鴨宮駅車5分", nightShiftType: "オンコール", annualHolidays: 120, salaryMin: 300000, salaryMax: 380000, educationLevel: "あり", matchingTags: ["訪問看護", "日勤のみ", "オンコール", "ターミナルケア", "精神科訪問看護"] },
  ],
};

// ---------- ユーザー希望条件抽出 ----------
function extractPreferences(messages) {
  const userMessages = (messages || []).filter(m => m.role === "user");
  const allText = userMessages.map(m => String(m.content || "")).join(" ");

  const prefs = { nightShift: null, facilityTypes: [], salaryMin: null, priorities: [], experience: null };

  // 夜勤希望
  if (/夜勤なし|日勤のみ|日勤だけ|夜勤はしたくない|夜勤なしで|夜勤不可/.test(allText)) {
    prefs.nightShift = false;
  } else if (/夜勤OK|夜勤可|夜勤あり|二交代|三交代|夜勤も/.test(allText)) {
    prefs.nightShift = true;
  }

  // 施設タイプ
  const typeMap = { "急性期": "急性期", "回復期": "回復期", "慢性期": "慢性期", "療養": "慢性期", "訪問看護": "訪問看護", "訪問": "訪問看護", "クリニック": "クリニック", "外来": "クリニック", "介護": "介護施設", "老健": "介護施設" };
  for (const [keyword, type] of Object.entries(typeMap)) {
    if (allText.includes(keyword) && !prefs.facilityTypes.includes(type)) {
      prefs.facilityTypes.push(type);
    }
  }

  // 給与最低額
  const salaryMatch = allText.match(/(\d{2,3})万[円以]?[上以]*/);
  if (salaryMatch) {
    const val = parseInt(salaryMatch[1]);
    if (val >= 20 && val <= 60) prefs.salaryMin = val * 10000;
    else if (val >= 200 && val <= 800) prefs.salaryMin = Math.round(val / 12) * 10000; // 年収→月額概算
  }

  // 優先事項
  const priorityMap = { "休日": "休日", "休み": "休日", "給与": "給与", "給料": "給与", "年収": "給与", "通勤": "通勤", "近い": "通勤", "駅近": "通勤", "教育": "教育", "研修": "教育", "残業": "残業少", "定時": "残業少", "ブランク": "ブランクOK", "託児": "託児所", "子育て": "託児所" };
  for (const [keyword, priority] of Object.entries(priorityMap)) {
    if (allText.includes(keyword) && !prefs.priorities.includes(priority)) {
      prefs.priorities.push(priority);
    }
  }

  // 経験年数
  const expMatch = allText.match(/(\d{1,2})\s*年/);
  if (expMatch) prefs.experience = parseInt(expMatch[1]);

  return prefs;
}

// ---------- 施設マッチングスコアリング ----------
function scoreFacilities(preferences, profession, area) {
  // エリアに対応する施設データを取得
  let facilities = [];
  if (area) {
    for (const [areaName, areaFacilities] of Object.entries(FACILITY_DATABASE)) {
      if (area.includes(areaName) || areaName.includes(area)) {
        facilities = areaFacilities;
        break;
      }
    }
  }
  if (facilities.length === 0) {
    // フォールバック: 全施設
    for (const areaFacilities of Object.values(FACILITY_DATABASE)) {
      facilities = facilities.concat(areaFacilities);
    }
  }

  const scored = facilities.map(f => {
    let score = 0;
    const reasons = [];

    // 夜勤マッチング（重要度高）
    if (preferences.nightShift === false) {
      if (f.nightShiftType === "なし" || f.nightShiftType === "オンコール") {
        score += 25;
        reasons.push("日勤中心の勤務");
      } else {
        score -= 15; // 夜勤必須はペナルティ
      }
    } else if (preferences.nightShift === true) {
      if (f.nightShiftType !== "なし" && f.nightShiftType !== "オンコール") {
        score += 10;
      }
    }

    // 施設タイプマッチング
    for (const type of preferences.facilityTypes) {
      if (f.type.includes(type) || f.matchingTags.some(t => t.includes(type))) {
        score += 15;
        reasons.push(type + "の経験を活かせる");
        break;
      }
    }

    // matchingTagsと優先事項のマッチング
    for (const priority of preferences.priorities) {
      const tagMap = { "休日": "年休", "教育": "教育", "通勤": "駅近", "残業少": "残業少なめ", "ブランクOK": "ブランクOK", "託児所": "託児" };
      const tagKeyword = tagMap[priority] || priority;
      if (f.matchingTags.some(t => t.includes(tagKeyword))) {
        score += 10;
        reasons.push(priority + "に対応");
      }
    }

    // 休日数
    if (f.annualHolidays >= 120) {
      score += 5;
      if (preferences.priorities.includes("休日")) {
        score += 5;
        if (!reasons.some(r => r.includes("休日"))) reasons.push("年間休日" + f.annualHolidays + "日");
      }
    }

    // 給与マッチング
    const salaryMax = profession === "理学療法士" ? (f.ptSalaryMax || f.salaryMax) : f.salaryMax;
    const salaryMin = profession === "理学療法士" ? (f.ptSalaryMin || f.salaryMin) : f.salaryMin;
    if (preferences.salaryMin && salaryMax) {
      if (salaryMax >= preferences.salaryMin) {
        score += 15;
        reasons.push("希望給与に適合");
      } else {
        score -= 10;
      }
    }

    // 教育体制（経験浅い場合に重要）
    if (f.educationLevel === "充実") {
      score += 5;
      if (preferences.experience !== null && preferences.experience < 5) {
        score += 10;
        reasons.push("教育体制充実");
      }
    }

    // ベーススコア（規模補正）
    if (f.beds && f.beds >= 200) score += 3;

    // 給与表示用
    const displaySalaryMin = salaryMin ? Math.round(salaryMin / 10000) : null;
    const displaySalaryMax = salaryMax ? Math.round(salaryMax / 10000) : null;
    const salaryDisplay = displaySalaryMin && displaySalaryMax
      ? `月給${displaySalaryMin}〜${displaySalaryMax}万円`
      : "要確認";

    return {
      name: f.name,
      type: f.type,
      matchScore: Math.max(0, Math.min(100, 40 + score)), // 40をベースに正規化
      reasons: reasons.length > 0 ? reasons.slice(0, 3) : ["エリアの求人としてご案内"],
      salary: salaryDisplay,
      access: f.access,
      nightShift: f.nightShiftType,
      annualHolidays: f.annualHolidays,
      beds: f.beds,
    };
  });

  // スコア降順でソート、上位3件
  scored.sort((a, b) => b.matchScore - a.matchScore);
  return scored.slice(0, 3);
}

function buildSystemPrompt(userMsgCount, profession, area) {
  // Build area-specific hospital info
  let hospitalInfo = "";
  if (area) {
    for (const [areaName, data] of Object.entries(AREA_DATABASE)) {
      if (area.includes(areaName) || areaName.includes(area)) {
        hospitalInfo = `\n【${areaName}エリアの医療機関情報（病院機能報告ベース）】\n` +
          `病院数: ${data.hospitals}施設\n` +
          `主要病院: ${data.majorHospitals}\n` +
          `看護師給与目安: ${data.salary}\n` +
          `看護師需要: ${data.demand}`;

        // FACILITY_DATABASEから詳細施設データを追加
        const facilities = FACILITY_DATABASE[areaName];
        if (facilities) {
          hospitalInfo += `\n\n【${areaName}エリア 施設詳細データ】`;
          for (const f of facilities) {
            const salaryMin = Math.round(f.salaryMin / 10000);
            const salaryMax = Math.round(f.salaryMax / 10000);
            hospitalInfo += `\n- ${f.name}（${f.type}）: ${f.beds ? f.beds + "床" : "外来"} / 月給${salaryMin}〜${salaryMax}万円 / ${f.nightShiftType} / 休${f.annualHolidays}日 / ${f.access}`;
            if (f.nurseCount) hospitalInfo += ` / 看護師${f.nurseCount}名`;
            if (f.features) hospitalInfo += ` / ${f.features}`;
          }
        }
        break;
      }
    }
  }
  if (!hospitalInfo) {
    hospitalInfo = "\n【対応エリア（神奈川県西部10エリア・97施設）】\n";
    for (const [areaName, data] of Object.entries(AREA_DATABASE)) {
      hospitalInfo += `- ${areaName}: 病院${data.hospitals}施設 / ${data.salary} / 需要${data.demand}\n`;
    }
  }

  // Build profession-specific salary info
  let salaryInfo = "";
  const profKey = profession === "理学療法士" ? "理学療法士" : "看護師";
  const profSalary = SALARY_DATA[profKey];
  if (profSalary) {
    salaryInfo = `\n【${profKey} 施設種別×経験年数 月給目安】\n`;
    for (const [type, range] of Object.entries(profSalary)) {
      salaryInfo += `${type}: ${range}\n`;
    }
  }

  // Build external job listings for the area
  let externalJobsInfo = "";
  const jobType = profession === "理学療法士" ? "pt" : "nurse";
  const jobData = EXTERNAL_JOBS[jobType];
  if (jobData && area) {
    for (const [areaName, jobs] of Object.entries(jobData)) {
      if (area.includes(areaName) || areaName.includes(area)) {
        externalJobsInfo += `\n【${areaName}エリア 現在公開中の${profKey}求人】\n`;
        for (const job of jobs) {
          externalJobsInfo += `- ${job}\n`;
        }
      }
    }
  }
  if (!externalJobsInfo && jobData) {
    externalJobsInfo = `\n【現在公開中の${profKey}求人（主要エリア）】\n`;
    for (const [areaName, jobs] of Object.entries(jobData)) {
      externalJobsInfo += `${areaName}: ${jobs.length}件\n`;
    }
  }

  let basePrompt = `あなたはROBBY THE MATCHのAI転職アドバイザーです。看護師・理学療法士など医療専門職の方の転職をサポートしています。

【基本姿勢】
- 温かく、親しみやすい口調で対応してください
- ユーザーが挨拶だけの場合は、自然に挨拶を返し「何かお手伝いできることはありますか？」と聞いてください
- ユーザーの発言をよく聞き、発言していない内容を推測で補わないでください
- 短く簡潔に応答してください（1-3文程度）
- 質問は1つずつ聞いてください（一度に複数質問しない）
- 相手の言葉に共感してから次の質問に進んでください

【会話の流れ（自然に進める、急がない）】
1. まず挨拶と自己紹介
2. 転職を考えているきっかけや状況を聞く
3. 現在の職場や経験を聞く
4. 希望条件（給与、勤務形態、エリアなど）を聞く
5. 合いそうな求人があれば具体的な病院名と情報を提示する
${hospitalInfo}
${salaryInfo}
${externalJobsInfo}
${SHIFT_DATA}

${MARKET_DATA}

【厳守ルール】
- 上記の病院データベースおよび公開求人データに基づいて具体的な施設名・条件を示してよい
- 外部求人は「現在このエリアで公開されている求人情報として」自然に紹介すること
- 「当社で確認している求人情報です」「エリアで募集が出ている施設です」等の自然な表現で案内する
- 「他社サイトの求人」「外部サイトで見つけた」等の表現は使わない
- 給与データに基づき経験年数×施設種別の目安を提示してよいが「目安として」「概算で」の表現を使い断定しないこと
- 勤務形態（二交代/三交代/日勤のみ）の特徴を説明できるが「施設によって異なります」を添えること
- 「詳細は担当エージェントが個別に確認・交渉します」を必ず添える
- 「最高」「No.1」「絶対」「必ず」等の断定的・最上級表現は禁止
- 個人情報（フルネーム、住所、具体的な現在の勤務先名）は聞かない
- 必ず最後は「詳しくは専門エージェントがご案内します」と伝える
- 手数料は求人側負担、求職者は完全無料であることを伝える
- 回答は日本語で、丁寧語を使う
- 有料職業紹介事業者として職業安定法を遵守する

返答はプレーンテキストのみで返してください。JSON形式やマークダウン記法は使わないでください。普通の日本語の文章で返してください。`;

  // Profession context from pre-chat button steps
  if (profession && area) {
    basePrompt += `\n\nこの求職者は${profession}で、${area}エリアでの転職を検討しています。上記の病院・給与データを活用して具体的な提案をしてください。`;
  } else if (profession) {
    basePrompt += `\n\nこの求職者は${profession}です。`;
  } else if (area) {
    basePrompt += `\n\nこの求職者は${area}エリアでの転職を検討しています。上記の病院・給与データを活用して具体的な提案をしてください。`;
  }

  // Message-count-aware prompt injection
  if (typeof userMsgCount === "number") {
    if (userMsgCount >= 3 && userMsgCount <= 4) {
      basePrompt += "\n\n希望条件（給与・勤務形態・勤務地・夜勤の可否など）を自然に聞き出し、マッチする病院を具体的に提示してください。経験年数から具体的な給与目安を計算して伝えてください。";
    } else if (userMsgCount >= 5) {
      basePrompt += "\n\nこれが最後の返答です。会話をまとめて、「専門のエージェントが改めてお電話でご案内します」と伝えてください。登録フォームへの案内もしてください。";
    }
  }

  return basePrompt;
}

export default {
  async fetch(request, env, ctx) {
    // CORS プリフライト
    if (request.method === "OPTIONS") {
      return handleCORS(request, env);
    }

    const url = new URL(request.url);

    // ルーティング
    if (url.pathname === "/api/register" && request.method === "POST") {
      return handleRegister(request, env, ctx);
    }

    if (url.pathname === "/api/chat-init" && request.method === "POST") {
      return handleChatInit(request, env);
    }

    if (url.pathname === "/api/chat" && request.method === "POST") {
      return handleChat(request, env);
    }

    if (url.pathname === "/api/chat-complete" && request.method === "POST") {
      return handleChatComplete(request, env);
    }

    if (url.pathname === "/api/notify" && request.method === "POST") {
      return handleNotify(request, env);
    }

    // ヘルスチェック
    if (url.pathname === "/api/health" && request.method === "GET") {
      return jsonResponse({ status: "ok", timestamp: new Date().toISOString() });
    }

    return jsonResponse({ error: "Not Found" }, 404);
  },
};

// ---------- 電話番号バリデーション ----------

function validatePhoneNumber(phone) {
  if (typeof phone !== "string") return false;
  const digits = phone.replace(/[\s\-]/g, "");
  const mobilePattern = /^0[789]0\d{8}$/;
  const landlinePattern = /^0\d{9}$/;
  return mobilePattern.test(digits) || landlinePattern.test(digits);
}

// ---------- HMAC トークン生成・検証 ----------

async function generateToken(phone, sessionId, timestamp, secretKey) {
  const data = `${phone}:${sessionId}:${timestamp}`;
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secretKey),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const signature = await crypto.subtle.sign(
    "HMAC",
    key,
    new TextEncoder().encode(data)
  );
  return base64urlEncode(signature);
}

async function verifyToken(phone, sessionId, timestamp, token, secretKey) {
  const expected = await generateToken(phone, sessionId, timestamp, secretKey);
  return expected === token;
}

// ---------- チャット初期化ハンドラ ----------

async function handleChatInit(request, env) {
  const allowedOrigin = getResponseOrigin(request, env);

  try {
    const body = await request.json();
    const { phone, honeypot, formShownAt } = body;

    // Anti-bot: honeypot check
    if (honeypot) {
      return jsonResponse({ error: "リクエストが拒否されました" }, 403, allowedOrigin);
    }

    // Anti-bot: User-Agent check
    const userAgent = request.headers.get("User-Agent");
    if (!userAgent) {
      return jsonResponse({ error: "リクエストが拒否されました" }, 403, allowedOrigin);
    }

    // Anti-bot: timing check (form must be shown for at least 2 seconds)
    if (typeof formShownAt === "number") {
      const elapsed = Date.now() - formShownAt;
      if (elapsed < 2000) {
        return jsonResponse({ error: "リクエストが拒否されました" }, 403, allowedOrigin);
      }
    }

    // Phone validation
    if (!validatePhoneNumber(phone)) {
      return jsonResponse({ error: "正しい電話番号を入力してください" }, 400, allowedOrigin);
    }

    const now = Date.now();

    // Global rate limit: max 100 sessions per hour
    if (now - globalSessionCount.windowStart > 3600000) {
      globalSessionCount = { count: 1, windowStart: now };
    } else {
      globalSessionCount.count++;
      if (globalSessionCount.count > 100) {
        return jsonResponse(
          { error: "現在混み合っています。しばらくしてからお試しください。" },
          429,
          allowedOrigin
        );
      }
    }

    // Per-phone rate limit: max 3 sessions per phone per 24h
    const phoneDigits = phone.replace(/[\s\-]/g, "");
    const phoneKey = `phone:${phoneDigits}`;
    let phoneEntry = phoneSessionMap.get(phoneKey);

    if (!phoneEntry || now - phoneEntry.windowStart > 86400000) {
      phoneEntry = { count: 1, windowStart: now };
      phoneSessionMap.set(phoneKey, phoneEntry);
    } else {
      phoneEntry.count++;
      if (phoneEntry.count > 3) {
        return jsonResponse(
          { error: "本日のチャット利用回数が上限に達しました。明日またお試しください。" },
          429,
          allowedOrigin
        );
      }
    }

    // Generate session
    const sessionId = crypto.randomUUID();
    const timestamp = now;
    const secretKey = env.CHAT_SECRET_KEY;

    if (!secretKey) {
      console.error("[ChatInit] CHAT_SECRET_KEY not configured");
      return jsonResponse({ error: "サービス設定エラー" }, 503, allowedOrigin);
    }

    const token = await generateToken(phoneDigits, sessionId, timestamp, secretKey);

    console.log(`[ChatInit] Session created: ${sessionId}, Phone: ${phoneDigits.slice(0, 3)}****`);

    return jsonResponse({ token, sessionId, timestamp }, 200, allowedOrigin);
  } catch (err) {
    console.error("[ChatInit] Error:", err);
    return jsonResponse({ error: "チャット初期化でエラーが発生しました" }, 500, allowedOrigin);
  }
}

// ---------- AIチャットハンドラ ----------

// チャットメッセージのサニタイズ（制御文字除去、長さ制限）
function sanitizeChatMessage(content) {
  if (typeof content !== "string") return "";
  // 制御文字を除去（改行・タブは許可）
  let cleaned = content.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, "");
  // 1メッセージの最大長: 2000文字
  if (cleaned.length > 2000) {
    cleaned = cleaned.slice(0, 2000);
  }
  return cleaned.trim();
}

async function handleChat(request, env) {
  const allowedOrigin = getResponseOrigin(request, env);

  // CHAT_ENABLED kill switch
  if (env.CHAT_ENABLED === "false") {
    return jsonResponse(
      { error: "チャットサービスは現在メンテナンス中です。" },
      503,
      allowedOrigin
    );
  }

  // チャット用レート制限（1分に10回まで、最低3秒間隔）
  const clientIP = request.headers.get("CF-Connecting-IP") || "unknown";
  const chatRateKey = `chat:${clientIP}`;
  let entry = rateLimitMap.get(chatRateKey);
  const now = Date.now();
  const CHAT_MAX_PER_MINUTE = 10;
  const CHAT_MIN_INTERVAL_MS = 3000;

  if (!entry || now - entry.windowStart > 60000) {
    entry = { windowStart: now, count: 1, lastRequest: now };
    rateLimitMap.set(chatRateKey, entry);
  } else {
    // 最低間隔チェック（同一IPから3秒以内の連続リクエストを拒否）
    if (now - entry.lastRequest < CHAT_MIN_INTERVAL_MS) {
      return jsonResponse(
        { error: "リクエストが早すぎます。少しお待ちください。" },
        429,
        allowedOrigin,
        { "X-RateLimit-Remaining": "0", "Retry-After": "3" }
      );
    }
    entry.count++;
    entry.lastRequest = now;
    if (entry.count > CHAT_MAX_PER_MINUTE) {
      return jsonResponse(
        { error: "チャット回数が上限を超えました。少し時間をおいてお試しください。" },
        429,
        allowedOrigin,
        { "X-RateLimit-Remaining": "0" }
      );
    }
  }
  const rateLimitRemaining = CHAT_MAX_PER_MINUTE - entry.count;

  try {
    const body = await request.json();
    const { messages, sessionId, token, phone, timestamp, profession, area } = body;

    // Token validation
    const secretKey = env.CHAT_SECRET_KEY;
    if (!secretKey) {
      return jsonResponse({ error: "サービス設定エラー" }, 503, allowedOrigin);
    }

    if (!token || !sessionId || !phone || !timestamp) {
      return jsonResponse({ error: "認証情報が不足しています" }, 401, allowedOrigin);
    }

    const phoneDigits = String(phone).replace(/[\s\-]/g, "");
    const isValid = await verifyToken(phoneDigits, sessionId, timestamp, token, secretKey);
    if (!isValid) {
      return jsonResponse({ error: "認証に失敗しました" }, 401, allowedOrigin);
    }

    // Sanitize profession/area (optional strings from pre-chat steps)
    const safeProfession = typeof profession === "string" ? profession.slice(0, 50) : "";
    const safeArea = typeof area === "string" ? area.slice(0, 50) : "";

    // メッセージ配列の検証
    if (!messages || !Array.isArray(messages)) {
      return jsonResponse({ error: "messages is required" }, 400, allowedOrigin);
    }

    // メッセージ数上限（コスト制御: 最大30メッセージ = 15往復）
    if (messages.length > 30) {
      return jsonResponse(
        { error: "会話が長くなりました。新しい相談を開始してください。" },
        400,
        allowedOrigin
      );
    }

    // 各メッセージのサニタイズ・検証
    const sanitizedMessages = [];
    for (const msg of messages) {
      if (!msg || typeof msg.role !== "string" || !["user", "assistant"].includes(msg.role)) {
        continue; // 不正なロールはスキップ
      }
      const content = sanitizeChatMessage(msg.content);
      if (content.length === 0 && msg.role === "user") {
        continue; // 空のユーザーメッセージはスキップ
      }
      sanitizedMessages.push({ role: msg.role, content: content });
    }

    // Count user messages server-side
    const userMsgCount = sanitizedMessages.filter((m) => m.role === "user").length;

    // Hard cap: 6 user messages → canned closing without calling AI
    if (userMsgCount > 6) {
      return jsonResponse(
        {
          reply: "ありがとうございます！お伺いした内容をもとに、専門エージェントがお電話でご案内いたします。24時間以内にご連絡しますので、少々お待ちください。",
          done: true,
        },
        200,
        allowedOrigin
      );
    }

    // Anthropic APIキーの確認
    const apiKey = env.ANTHROPIC_API_KEY;
    if (!apiKey) {
      return jsonResponse({ error: "AI service not configured" }, 503, allowedOrigin);
    }

    // システムプロンプトをサーバー側で構築（メッセージ数・職種・エリアに応じて変化）
    const systemPrompt = buildSystemPrompt(userMsgCount, safeProfession, safeArea);

    // セッションID のログ記録
    if (sessionId) {
      console.log(`[Chat] Session: ${sessionId}, Messages: ${sanitizedMessages.length}, UserMsgs: ${userMsgCount}`);
    }

    // Claude API呼び出し（Haiku: 低コスト・高速）
    const anthropicRes = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": apiKey,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model: env.CHAT_MODEL || "claude-haiku-4-5-20251001",
        max_tokens: 1024,
        system: systemPrompt,
        messages: sanitizedMessages,
      }),
    });

    if (!anthropicRes.ok) {
      const errText = await anthropicRes.text();
      console.error("[Chat] Anthropic API error:", anthropicRes.status, errText);
      return jsonResponse(
        { error: "AI応答の取得に失敗しました" },
        502,
        allowedOrigin
      );
    }

    const aiData = await anthropicRes.json();
    let aiText = aiData.content?.[0]?.text || "";

    // Response validation: reject suspiciously short or JSON-like responses
    if (aiText.length < 5 || aiText.startsWith("{") || aiText.startsWith("[")) {
      aiText = "ありがとうございます。もう少し詳しく教えていただけますか？";
    }

    const rateLimitHeaders = { "X-RateLimit-Remaining": String(rateLimitRemaining) };

    // done flag: true if this was the 5th or 6th user message (last AI response before cap)
    const done = userMsgCount >= 5;

    // プレーンテキストをreplyとして返却（JSON解析不要）
    return jsonResponse(
      { reply: aiText, done },
      200,
      allowedOrigin,
      rateLimitHeaders
    );
  } catch (err) {
    console.error("[Chat] Error:", err);
    return jsonResponse({ error: "チャット処理でエラーが発生しました" }, 500, allowedOrigin);
  }
}

// ---------- チャット完了ハンドラ ----------

// ---------- サーバー側温度感スコアリング（チャット会話分析） ----------

function detectChatTemperatureScore(messages, clientScore) {
  // If client already detected a score, use as baseline
  let score = 0;

  const userMessages = (messages || []).filter((m) => m.role === "user");
  const allText = userMessages.map((m) => String(m.content || "")).join(" ");

  // Urgency keywords (A-level signals: immediate need)
  const urgentPatterns = ["すぐ", "急ぎ", "今月", "来月", "退職済", "辞めた", "決まっている", "早く", "なるべく早", "今すぐ"];
  for (const pattern of urgentPatterns) {
    if (allText.includes(pattern)) { score += 3; break; }
  }

  // Active interest keywords (B-level signals: concrete conditions)
  const activePatterns = ["面接", "見学", "応募", "給与", "年収", "月給", "具体的", "いつから", "条件", "夜勤", "日勤", "休日"];
  for (const pattern of activePatterns) {
    if (allText.includes(pattern)) { score += 1; }
  }

  // Engagement: message count
  if (userMessages.length >= 5) { score += 2; }
  else if (userMessages.length >= 3) { score += 1; }

  // Message length engagement (detailed user = more invested)
  const totalLen = userMessages.reduce((sum, m) => sum + String(m.content || "").length, 0);
  if (totalLen > 200) { score += 1; }
  if (totalLen > 400) { score += 1; }

  if (score >= 5) return "A";
  if (score >= 3) return "B";
  if (score >= 1) return "C";
  return "D";
}

async function handleChatComplete(request, env) {
  const allowedOrigin = getResponseOrigin(request, env);

  try {
    const body = await request.json();
    const { phone, sessionId, messages, token, timestamp, profession, area, score: clientScore, messageCount, completedAt } = body;

    // Phone is required for notification
    if (!phone) {
      return jsonResponse({ error: "電話番号が必要です" }, 400, allowedOrigin);
    }

    const phoneDigits = String(phone).replace(/[\s\-]/g, "");

    // Token validation (optional: demo mode may not have token)
    const secretKey = env.CHAT_SECRET_KEY;
    if (token && sessionId && timestamp && secretKey) {
      const isValid = await verifyToken(phoneDigits, sessionId, timestamp, token, secretKey);
      if (!isValid) {
        return jsonResponse({ error: "認証に失敗しました" }, 401, allowedOrigin);
      }
    }

    if (!messages || !Array.isArray(messages)) {
      return jsonResponse({ error: "messages is required" }, 400, allowedOrigin);
    }

    // Server-side temperature scoring (authoritative, overrides client)
    const temperatureScore = detectChatTemperatureScore(messages, clientScore);

    // Build Slack message with conversation log
    const botToken = env.SLACK_BOT_TOKEN;
    const channelId = env.SLACK_CHANNEL_ID || "C09A7U4TV4G";

    if (!botToken) {
      console.warn("[ChatComplete] SLACK_BOT_TOKEN not configured");
      return jsonResponse({ error: "通知設定エラー" }, 503, allowedOrigin);
    }

    // Format phone for display
    const displayPhone = formatPhoneDisplay(phoneDigits);

    // Count message rounds
    const userMsgCount = messages.filter((m) => m.role === "user").length;

    // Current time in JST
    const nowJST = new Date().toLocaleString("ja-JP", { timeZone: "Asia/Tokyo" });

    // Build conversation log (truncate AI messages for readability)
    let conversationLog = "";
    for (const msg of messages) {
      const content = sanitize(String(msg.content || ""));
      if (msg.role === "user") {
        conversationLog += `\u{1F464} ユーザー: ${content}\n`;
      } else if (msg.role === "ai" || msg.role === "assistant") {
        const truncated = content.length > 150 ? content.slice(0, 150) + "..." : content;
        conversationLog += `\u{1F916} AI: ${truncated}\n`;
      }
    }

    const professionDisplay = profession ? sanitize(String(profession)) : "未回答";
    const areaDisplay = area ? sanitize(String(area)) : "未回答";

    // Score emoji and priority indicator
    const scoreEmoji = { A: "\u{1F534}", B: "\u{1F7E1}", C: "\u{1F7E2}", D: "\u26AA" };
    const scoreLabel = { A: "即転職希望", B: "積極検討中", C: "情報収集中", D: "初期接触" };
    const channelNotify = temperatureScore === "A" ? "<!channel> " : "";

    const slackText =
      `${channelNotify}\u{1F916} *AIチャット完了*\n\n` +
      `*温度感: ${scoreEmoji[temperatureScore] || "\u26AA"} ${temperatureScore} (${scoreLabel[temperatureScore] || "不明"})*\n\n` +
      `*電話番号*: ${sanitize(displayPhone)}\n` +
      `*職種*: ${professionDisplay}\n` +
      `*希望エリア*: ${areaDisplay}\n` +
      `*メッセージ数*: ${userMsgCount}往復\n` +
      `*日時*: ${nowJST}\n\n` +
      `*会話ログ*\n${conversationLog}\n` +
      `*要対応*\n` +
      (temperatureScore === "A" ? `\u{1F6A8} *即日対応推奨*\n` : "") +
      `\u25A1 24時間以内に架電\n` +
      `\u25A1 希望条件に合う求人確認`;

    await fetchWithRetry("https://slack.com/api/chat.postMessage", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${botToken}`,
        "Content-Type": "application/json; charset=utf-8",
      },
      body: JSON.stringify({ channel: channelId, text: slackText }),
    });

    // Store structured conversation log to Google Sheets if configured
    if (env.GOOGLE_SHEETS_ID && env.GOOGLE_SERVICE_ACCOUNT_JSON) {
      try {
        await storeChatLog(env, {
          sessionId,
          phone: displayPhone,
          profession: professionDisplay,
          area: areaDisplay,
          score: temperatureScore,
          messageCount: userMsgCount,
          completedAt: completedAt || nowJST,
        });
      } catch (sheetErr) {
        console.error("[ChatComplete] Sheet storage error:", sheetErr);
        // Non-blocking: don't fail the request if sheet storage fails
      }
    }

    // マッチング結果を生成
    let matchedFacilities = [];
    try {
      const preferences = extractPreferences(messages);
      matchedFacilities = scoreFacilities(preferences, profession, area);
      console.log(`[ChatComplete] Matched ${matchedFacilities.length} facilities for ${area || "all areas"}`);
    } catch (matchErr) {
      console.error("[ChatComplete] Matching error:", matchErr);
      // マッチング失敗はnon-blocking
    }

    console.log(`[ChatComplete] Session: ${sessionId}, Phone: ${phoneDigits.slice(0, 3)}****, Score: ${temperatureScore}, Messages: ${userMsgCount}`);

    return jsonResponse({ success: true, score: temperatureScore, matchedFacilities }, 200, allowedOrigin);
  } catch (err) {
    console.error("[ChatComplete] Error:", err);
    return jsonResponse({ error: "チャット完了処理でエラーが発生しました" }, 500, allowedOrigin);
  }
}

// ---------- チャットログ Google Sheets保存 ----------

async function storeChatLog(env, logData) {
  const accessToken = await getGoogleAccessToken(env.GOOGLE_SERVICE_ACCOUNT_JSON);
  const sheetName = "チャットログ";
  const range = `${sheetName}!A:G`;

  const values = [
    [
      logData.completedAt,
      logData.phone,
      logData.profession,
      logData.area,
      logData.score,
      String(logData.messageCount),
      logData.sessionId,
    ],
  ];

  const sheetsUrl = `https://sheets.googleapis.com/v4/spreadsheets/${env.GOOGLE_SHEETS_ID}/values/${encodeURIComponent(range)}:append?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS`;

  await fetchWithRetry(sheetsUrl, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ values }),
  });
}

// Format phone digits for display (e.g., 09012345678 → 090-1234-5678)
function formatPhoneDisplay(digits) {
  if (digits.length === 11 && /^0[789]0/.test(digits)) {
    return `${digits.slice(0, 3)}-${digits.slice(3, 7)}-${digits.slice(7)}`;
  }
  if (digits.length === 10 && /^0\d/.test(digits)) {
    return `${digits.slice(0, 2)}-${digits.slice(2, 6)}-${digits.slice(6)}`;
  }
  return digits;
}

// ---------- Slack通知ハンドラ（チャットサマリー用） ----------

async function handleNotify(request, env) {
  const allowedOrigin = getResponseOrigin(request, env);

  try {
    const body = await request.json();
    const botToken = env.SLACK_BOT_TOKEN;
    const channelId = env.SLACK_CHANNEL_ID || "C09A7U4TV4G";

    if (!botToken) {
      return jsonResponse({ error: "Slack not configured" }, 503, allowedOrigin);
    }

    await fetch("https://slack.com/api/chat.postMessage", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${botToken}`,
        "Content-Type": "application/json; charset=utf-8",
      },
      body: JSON.stringify({ channel: channelId, text: body.text || "通知" }),
    });

    return jsonResponse({ success: true }, 200, allowedOrigin);
  } catch (err) {
    console.error("[Notify] Error:", err);
    return jsonResponse({ error: "通知送信に失敗しました" }, 500, allowedOrigin);
  }
}

// ---------- メイン登録ハンドラ ----------

async function handleRegister(request, env, ctx) {
  const allowedOrigin = getResponseOrigin(request, env);

  try {
    // レート制限チェック
    const clientIP = request.headers.get("CF-Connecting-IP") || "unknown";
    const rateLimitResult = checkRateLimit(clientIP, env);
    if (!rateLimitResult.allowed) {
      return jsonResponse(
        { success: false, error: "リクエスト回数が上限を超えました。しばらくしてから再度お試しください。" },
        429,
        allowedOrigin
      );
    }

    // リクエストボディ解析
    const contentType = request.headers.get("Content-Type") || "";
    let data;

    if (contentType.includes("application/json")) {
      data = await request.json();
    } else {
      return jsonResponse(
        { success: false, error: "Content-Type must be application/json" },
        400,
        allowedOrigin
      );
    }

    // サーバーサイドバリデーション
    const validation = validateFormData(data);
    if (!validation.valid) {
      return jsonResponse(
        { success: false, error: "入力内容に不備があります", details: validation.errors },
        400,
        allowedOrigin
      );
    }

    // 温度感スコアリング
    const urgency = calcUrgency(data);

    // 登録日時付与
    const registeredAt = new Date().toLocaleString("ja-JP", { timeZone: "Asia/Tokyo" });
    data.registeredAt = registeredAt;

    // Slack通知 & Google Sheets書き込み を並列実行
    const results = await Promise.allSettled([
      sendToSlack(data, urgency, env),
      sendToSheets(data, urgency, env),
    ]);

    const slackResult = results[0];
    const sheetsResult = results[1];

    // 結果ログ（Cloudflare Workers ログ）
    if (slackResult.status === "rejected") {
      console.error("[Slack] 送信失敗:", slackResult.reason);
    }
    if (sheetsResult.status === "rejected") {
      console.error("[Sheets] 書き込み失敗:", sheetsResult.reason);
    }

    // 片方でも成功すれば成功応答（データ損失を防ぐ）
    if (slackResult.status === "fulfilled" || sheetsResult.status === "fulfilled") {
      return jsonResponse(
        { success: true, message: "登録が完了しました" },
        200,
        allowedOrigin
      );
    }

    // 両方失敗
    return jsonResponse(
      { success: false, error: "送信に失敗しました。時間をおいて再度お試しください。" },
      500,
      allowedOrigin
    );
  } catch (err) {
    console.error("[Register] 予期せぬエラー:", err);
    return jsonResponse(
      { success: false, error: "サーバーエラーが発生しました。" },
      500,
      allowedOrigin
    );
  }
}

// ---------- バリデーション ----------

function validateFormData(data) {
  const errors = [];

  // 必須項目チェック
  if (!data.lastName || typeof data.lastName !== "string" || data.lastName.trim().length === 0) {
    errors.push("姓を入力してください");
  }
  if (!data.firstName || typeof data.firstName !== "string" || data.firstName.trim().length === 0) {
    errors.push("名を入力してください");
  }

  // 年齢
  const age = parseInt(data.age, 10);
  if (isNaN(age) || age < 18 || age > 70) {
    errors.push("18〜70の年齢を入力してください");
  }

  // 電話番号
  if (!data.phone || !/^[\d\-]{10,14}$/.test(String(data.phone).replace(/\s/g, ""))) {
    errors.push("正しい電話番号を入力してください");
  }

  // メール
  if (!data.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
    errors.push("正しいメールアドレスを入力してください");
  }

  // 選択項目
  const requiredSelects = [
    { field: "experience", label: "経験年数" },
    { field: "currentStatus", label: "現在の勤務状況" },
    { field: "transferTiming", label: "希望転職時期" },
    { field: "desiredSalary", label: "希望給与レンジ" },
  ];

  for (const item of requiredSelects) {
    if (!data[item.field] || data[item.field] === "") {
      errors.push(`${item.label}を選択してください`);
    }
  }

  return { valid: errors.length === 0, errors };
}

// ---------- 温度感スコアリング ----------

function calcUrgency(data) {
  const timing = data.transferTiming;
  if (timing === "すぐにでも") return "A";
  if (timing === "1ヶ月以内") return "B";
  if (timing === "3ヶ月以内") return "C";
  return "D";
}

// ---------- Slack 通知 ----------

async function sendToSlack(data, urgency, env) {
  const botToken = env.SLACK_BOT_TOKEN;
  const channelId = env.SLACK_CHANNEL_ID || "C09A7U4TV4G";

  if (!botToken) {
    console.warn("[Slack] SLACK_BOT_TOKEN が未設定です");
    throw new Error("Slack Bot Token not configured");
  }

  const urgencyEmoji = { A: "\u{1F534}", B: "\u{1F7E1}", C: "\u{1F7E2}", D: "\u26AA" };
  const channelNotify = urgency === "A" ? "<!channel> " : "";

  const text =
    `${channelNotify}\u{1F3E5} *新規求職者登録*\n\n` +
    `*温度感: ${urgencyEmoji[urgency]} ${urgency}*\n\n` +
    `*基本情報*\n` +
    `氏名：${sanitize(data.lastName)} ${sanitize(data.firstName)}さん（${data.age}歳）\n` +
    `資格：${sanitize(data.profession || "未回答")}\n` +
    `経験：${sanitize(data.experience)}\n` +
    `現在：${sanitize(data.currentStatus)}\n` +
    `連絡先：${sanitize(data.phone)} / ${sanitize(data.email)}\n\n` +
    `*希望条件*\n` +
    `給与：${sanitize(data.desiredSalary)}\n` +
    `転職時期：${sanitize(data.transferTiming)}\n` +
    `勤務形態：${sanitize(data.workStyle || "未回答")}\n` +
    `夜勤：${sanitize(data.nightShift || "未回答")}\n` +
    `休日：${sanitize(data.holidays || "未回答")}\n` +
    `通勤：${sanitize(data.commuteRange || "未回答")}\n\n` +
    `*備考*\n${sanitize(data.notes || "なし")}\n\n` +
    `*要対応*\n` +
    `□ 24時間以内に初回架電\n` +
    `□ 希望条件に合う求人確認\n` +
    `□ 面接日程調整\n\n` +
    `登録日時：${data.registeredAt}`;

  // Slack Web API chat.postMessage
  await fetchWithRetry("https://slack.com/api/chat.postMessage", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${botToken}`,
      "Content-Type": "application/json; charset=utf-8",
    },
    body: JSON.stringify({ channel: channelId, text }),
  });
}

// ---------- Google Sheets 連携 ----------

async function sendToSheets(data, urgency, env) {
  const spreadsheetId = env.GOOGLE_SHEETS_ID;
  const serviceAccountJson = env.GOOGLE_SERVICE_ACCOUNT_JSON;

  if (!spreadsheetId || !serviceAccountJson) {
    console.warn("[Sheets] Google Sheets設定が不足しています");
    throw new Error("Google Sheets not configured");
  }

  // サービスアカウント認証
  const accessToken = await getGoogleAccessToken(serviceAccountJson);

  const sheetName = "求職者台帳";
  const range = `${sheetName}!A:N`;

  const values = [
    [
      data.registeredAt,                             // 登録日時
      `${data.lastName} ${data.firstName}`,          // 氏名
      data.age,                                      // 年齢
      data.phone,                                    // 電話番号
      data.email,                                    // メールアドレス
      data.experience,                               // 経験年数
      data.currentStatus,                            // 現在勤務状況
      data.transferTiming,                           // 希望転職時期
      data.desiredSalary,                            // 希望給与
      buildConditionSummary(data),                   // 希望条件詳細
      "登録",                                        // 進捗ステータス（初期値）
      urgency,                                       // 温度感
      "",                                            // 担当者（後で割り当て）
      data.notes || "",                              // 備考
    ],
  ];

  const sheetsUrl = `https://sheets.googleapis.com/v4/spreadsheets/${spreadsheetId}/values/${encodeURIComponent(range)}:append?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS`;

  await fetchWithRetry(sheetsUrl, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ values }),
  });
}

// Google サービスアカウントでアクセストークンを取得
async function getGoogleAccessToken(serviceAccountJson) {
  let sa;
  try {
    sa = JSON.parse(serviceAccountJson);
  } catch {
    throw new Error("GOOGLE_SERVICE_ACCOUNT_JSON の解析に失敗しました");
  }

  const now = Math.floor(Date.now() / 1000);
  const header = { alg: "RS256", typ: "JWT" };
  const claim = {
    iss: sa.client_email,
    scope: "https://www.googleapis.com/auth/spreadsheets",
    aud: "https://oauth2.googleapis.com/token",
    exp: now + 3600,
    iat: now,
  };

  const encodedHeader = base64urlEncode(JSON.stringify(header));
  const encodedClaim = base64urlEncode(JSON.stringify(claim));
  const unsignedToken = `${encodedHeader}.${encodedClaim}`;

  // RSA署名
  const privateKey = await importPrivateKey(sa.private_key);
  const signature = await crypto.subtle.sign(
    { name: "RSASSA-PKCS1-v1_5" },
    privateKey,
    new TextEncoder().encode(unsignedToken)
  );

  const jwt = `${unsignedToken}.${base64urlEncode(signature)}`;

  // トークン交換
  const tokenRes = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: `grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion=${jwt}`,
  });

  if (!tokenRes.ok) {
    const errorText = await tokenRes.text();
    throw new Error(`Google OAuth token取得失敗: ${tokenRes.status} ${errorText}`);
  }

  const tokenData = await tokenRes.json();
  return tokenData.access_token;
}

// PEM形式のRSA秘密鍵をインポート
async function importPrivateKey(pem) {
  const pemContents = pem
    .replace(/-----BEGIN PRIVATE KEY-----/, "")
    .replace(/-----END PRIVATE KEY-----/, "")
    .replace(/\n/g, "");

  const binaryDer = Uint8Array.from(atob(pemContents), (c) => c.charCodeAt(0));

  return crypto.subtle.importKey(
    "pkcs8",
    binaryDer.buffer,
    { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
    false,
    ["sign"]
  );
}

// Base64url エンコード（文字列 or ArrayBuffer）
function base64urlEncode(input) {
  let bytes;
  if (typeof input === "string") {
    bytes = new TextEncoder().encode(input);
  } else {
    bytes = new Uint8Array(input);
  }

  let binary = "";
  for (const b of bytes) {
    binary += String.fromCharCode(b);
  }

  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

// 希望条件の要約を生成
function buildConditionSummary(data) {
  const parts = [];
  if (data.workStyle && data.workStyle !== "未回答") parts.push(`勤務形態:${data.workStyle}`);
  if (data.nightShift && data.nightShift !== "未回答") parts.push(`夜勤:${data.nightShift}`);
  if (data.holidays && data.holidays !== "未回答") parts.push(`休日:${data.holidays}`);
  if (data.commuteRange && data.commuteRange !== "未回答") parts.push(`通勤:${data.commuteRange}`);
  return parts.join(" / ") || "";
}

// ---------- ユーティリティ ----------

// リトライ付きfetch（最大3回、指数バックオフ）
async function fetchWithRetry(url, options, maxRetries = 3) {
  let lastError;
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const res = await fetch(url, options);
      if (res.ok) return res;

      // 4xx は即失敗（リトライしても意味がない）
      if (res.status >= 400 && res.status < 500) {
        const errorText = await res.text();
        throw new Error(`HTTP ${res.status}: ${errorText}`);
      }

      // 5xx はリトライ
      lastError = new Error(`HTTP ${res.status}`);
    } catch (err) {
      lastError = err;
    }

    if (attempt < maxRetries) {
      await sleep(1000 * Math.pow(2, attempt - 1)); // 1s, 2s
    }
  }
  throw lastError;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// レート制限（同一IP 1分に5回まで）
function checkRateLimit(ip, env) {
  const windowMs = 60 * 1000; // 1分
  const maxRequests = 5;
  const now = Date.now();

  const key = `rate:${ip}`;
  let entry = rateLimitMap.get(key);

  if (!entry || now - entry.windowStart > windowMs) {
    entry = { windowStart: now, count: 1 };
    rateLimitMap.set(key, entry);
    return { allowed: true };
  }

  entry.count++;
  if (entry.count > maxRequests) {
    return { allowed: false };
  }

  return { allowed: true };
}

// Slackメッセージ用サニタイズ（Slack mrkdwn injection防止）
function sanitize(str) {
  if (typeof str !== "string") return String(str || "");
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// CORS設定（複数オリジン対応: 本番 + ローカル開発）
function isOriginAllowed(origin, env) {
  if (!origin) return false;
  // ALLOWED_ORIGIN が "*" なら全許可
  const configuredOrigin = env.ALLOWED_ORIGIN || "*";
  if (configuredOrigin === "*") return true;
  // 本番オリジン一致
  if (origin === configuredOrigin) return true;
  // ローカル開発: file:// (null), localhost, 127.0.0.1
  if (origin === "null") return true;
  if (/^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin)) return true;
  return false;
}

// リクエストの Origin を検証して CORS 応答用の値を返す
function getResponseOrigin(request, env) {
  const origin = request.headers.get("Origin") || "";
  if (isOriginAllowed(origin, env)) return origin || "*";
  return env.ALLOWED_ORIGIN || "*";
}

function handleCORS(request, env) {
  const origin = request.headers.get("Origin") || "";

  if (!isOriginAllowed(origin, env)) {
    return new Response(null, { status: 403 });
  }

  return new Response(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Origin": origin || "*",
      "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
      "Access-Control-Expose-Headers": "X-RateLimit-Remaining, Retry-After",
      "Access-Control-Max-Age": "86400",
    },
  });
}

// JSON レスポンス生成
function jsonResponse(data, status = 200, allowedOrigin = "*", extraHeaders = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": allowedOrigin,
      "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
      "Access-Control-Expose-Headers": "X-RateLimit-Remaining, Retry-After",
      ...extraHeaders,
    },
  });
}
