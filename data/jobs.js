// ========================================
// ナースロビー - 求人・給与・勤務データベース
// 神奈川県西部 医療職 求人市場データ（2026年版）
// ========================================

const JOB_DATABASE = {
  // ==========================================
  // 職種別 給与テーブル（経験年数別）
  // ==========================================
  salaryTable: {
    "看護師": {
      "急性期病院": {
        新卒: { monthly: "27〜29万円", annual: "400〜440万円" },
        "3〜5年": { monthly: "29〜33万円", annual: "440〜500万円" },
        "5〜10年": { monthly: "32〜37万円", annual: "480〜560万円" },
        "10年以上": { monthly: "35〜42万円", annual: "530〜640万円" },
        "管理職（主任）": { monthly: "37〜43万円", annual: "560〜650万円" },
        "管理職（師長）": { monthly: "42〜50万円", annual: "640〜760万円" },
      },
      "回復期リハ病院": {
        新卒: { monthly: "26〜28万円", annual: "380〜420万円" },
        "3〜5年": { monthly: "28〜32万円", annual: "420〜480万円" },
        "5〜10年": { monthly: "30〜35万円", annual: "450〜530万円" },
        "10年以上": { monthly: "33〜39万円", annual: "500〜590万円" },
      },
      "療養型病院": {
        新卒: { monthly: "25〜27万円", annual: "370〜400万円" },
        "3〜5年": { monthly: "27〜31万円", annual: "400〜470万円" },
        "5〜10年": { monthly: "29〜34万円", annual: "430〜510万円" },
        "10年以上": { monthly: "32〜38万円", annual: "480〜570万円" },
      },
      "クリニック": {
        新卒: { monthly: "25〜28万円", annual: "350〜400万円" },
        "3〜5年": { monthly: "27〜31万円", annual: "380〜440万円" },
        "5〜10年": { monthly: "29〜34万円", annual: "410〜490万円" },
        "10年以上": { monthly: "31〜37万円", annual: "440〜530万円" },
      },
      "訪問看護": {
        新卒: { monthly: "28〜30万円", annual: "400〜440万円" },
        "3〜5年": { monthly: "30〜34万円", annual: "440〜500万円" },
        "5〜10年": { monthly: "33〜38万円", annual: "490〜560万円" },
        "10年以上": { monthly: "35〜42万円", annual: "530〜630万円" },
      },
      "介護施設": {
        新卒: { monthly: "25〜27万円", annual: "360〜390万円" },
        "3〜5年": { monthly: "27〜30万円", annual: "390〜440万円" },
        "5〜10年": { monthly: "29〜33万円", annual: "420〜490万円" },
        "10年以上": { monthly: "31〜36万円", annual: "460〜540万円" },
      },
    },
    "理学療法士": {
      "急性期病院": {
        新卒: { monthly: "23〜25万円", annual: "340〜380万円" },
        "3〜5年": { monthly: "25〜29万円", annual: "380〜430万円" },
        "5〜10年": { monthly: "28〜33万円", annual: "420〜500万円" },
        "10年以上": { monthly: "31〜37万円", annual: "470〜560万円" },
        "管理職（主任）": { monthly: "33〜39万円", annual: "500〜590万円" },
      },
      "回復期リハ病院": {
        新卒: { monthly: "23〜25万円", annual: "340〜370万円" },
        "3〜5年": { monthly: "25〜28万円", annual: "370〜420万円" },
        "5〜10年": { monthly: "27〜32万円", annual: "400〜480万円" },
        "10年以上": { monthly: "30〜35万円", annual: "450〜530万円" },
      },
      "訪問リハ": {
        新卒: { monthly: "25〜27万円", annual: "360〜400万円" },
        "3〜5年": { monthly: "27〜31万円", annual: "400〜460万円" },
        "5〜10年": { monthly: "30〜35万円", annual: "440〜520万円" },
        "10年以上": { monthly: "33〜38万円", annual: "490〜570万円" },
      },
      "クリニック": {
        新卒: { monthly: "22〜24万円", annual: "320〜360万円" },
        "3〜5年": { monthly: "24〜28万円", annual: "360〜410万円" },
        "5〜10年": { monthly: "27〜31万円", annual: "390〜460万円" },
        "10年以上": { monthly: "29〜34万円", annual: "430〜510万円" },
      },
      "介護施設": {
        新卒: { monthly: "22〜24万円", annual: "320〜350万円" },
        "3〜5年": { monthly: "24〜27万円", annual: "350〜400万円" },
        "5〜10年": { monthly: "26〜30万円", annual: "380〜450万円" },
        "10年以上": { monthly: "28〜33万円", annual: "420〜500万円" },
      },
    },
  },

  // ==========================================
  // 勤務形態パターン
  // ==========================================
  shiftPatterns: {
    "二交代制": {
      description: "日勤・夜勤の2パターン",
      dayShift: "8:30〜17:30（実働8h）",
      nightShift: "16:30〜翌9:00（実働14.5h・仮眠2h）",
      nightFrequency: "月4〜5回",
      nightAllowance: "1回 10,000〜15,000円",
      typicalFacility: "中小規模病院・療養型に多い",
    },
    "三交代制": {
      description: "日勤・準夜勤・深夜勤の3パターン",
      dayShift: "8:30〜17:00（実働7.5h）",
      eveningShift: "16:00〜翌0:30（実働7.5h）",
      nightShift: "0:00〜翌8:30（実働7.5h）",
      nightFrequency: "月8〜10回（準夜+深夜合計）",
      nightAllowance: "準夜 3,000〜5,000円 / 深夜 5,000〜8,000円",
      typicalFacility: "大規模急性期病院に多い",
    },
    "日勤のみ": {
      description: "夜勤なしの日勤勤務",
      dayShift: "8:30〜17:30（実働8h）",
      salary_note: "夜勤手当がない分、月給は3〜5万円程度低くなる傾向",
      typicalFacility: "クリニック・訪問看護・介護施設・外来",
    },
    "変則二交代制": {
      description: "ロング日勤を含む変則パターン",
      earlyShift: "7:00〜15:30",
      dayShift: "8:30〜17:00",
      lateShift: "10:30〜19:00",
      nightShift: "16:30〜翌9:00",
      typicalFacility: "一部の大規模病院",
    },
  },

  // ==========================================
  // 手当一覧（一般的な金額目安）
  // ==========================================
  allowances: {
    夜勤手当: { range: "1回 8,000〜15,000円", note: "二交代/三交代で異なる" },
    通勤手当: { range: "月額上限 30,000〜50,000円", note: "ほぼ全施設で支給" },
    住宅手当: { range: "月10,000〜27,000円", note: "施設による（約60%が支給）" },
    家族手当: { range: "配偶者 10,000〜15,000円 / 子1人 5,000〜10,000円", note: "施設による" },
    資格手当: { range: "月5,000〜30,000円", note: "認定看護師・専門看護師で加算" },
    皆勤手当: { range: "月5,000〜10,000円", note: "施設による" },
    オンコール手当: { range: "1回 1,000〜3,000円", note: "訪問看護で多い" },
    残業手当: { range: "法定通り（時給×1.25〜1.5倍）", note: "全施設で支給義務あり" },
  },

  // ==========================================
  // 福利厚生（一般的な項目）
  // ==========================================
  commonBenefits: [
    "社会保険完備（健康・厚生年金・雇用・労災）",
    "退職金制度（勤続3年以上が一般的）",
    "有給休暇（法定通り：初年度10日〜最大20日）",
    "育児休業・介護休業制度",
    "院内研修・外部研修費用補助",
    "制服貸与・クリーニング",
    "職員食堂・食事補助（1食200〜400円）",
    "駐車場（無料〜月5,000円 ※郊外は無料が多い）",
    "託児所・院内保育所（大規模病院で増加中）",
    "メンタルヘルスサポート・相談窓口",
  ],

  // ==========================================
  // 年間休日パターン
  // ==========================================
  holidays: {
    "4週8休": { annualDays: "105〜110日", note: "最も一般的。祝日は交代勤務。" },
    "4週8休+祝日": { annualDays: "115〜120日", note: "祝日分が追加休。中規模以上に多い。" },
    "完全週休2日+祝日": { annualDays: "120〜125日", note: "クリニック・日勤のみの施設に多い。" },
    "シフト制（年間休日120日以上）": { annualDays: "120日以上", note: "大手法人・公立病院に多い。人気高い。" },
  },

  // ==========================================
  // 神奈川県西部 求人市場データ
  // ==========================================
  kanagawaMarket: {
    nurseDemand: "非常に高い（有効求人倍率 2.0〜2.5倍）",
    ptDemand: "高い（有効求人倍率 1.5〜2.0倍）",
    marketTrend: "2024年以降、回復期・地域包括ケアの需要が急増。訪問看護ステーション開設ラッシュ。",
    averageChangeTiming: "退職意向表明から入職まで平均2〜3ヶ月",
    popularConditions: [
      "残業月10時間以内",
      "年間休日120日以上",
      "託児所あり",
      "日勤のみ可",
      "車通勤可（駐車場無料）",
      "ブランク可・復職支援あり",
      "教育体制充実（プリセプター制度）",
    ],
    seekerPriorities: {
      "20代": "教育体制・キャリアアップ・給与",
      "30代": "ワークライフバランス・託児所・残業少なめ",
      "40代以上": "通勤距離・勤務形態の柔軟さ・安定した職場環境",
      "ブランクあり": "復職支援・研修制度・無理のないシフト",
    },
  },

  // ==========================================
  // 認定・専門資格 給与影響
  // ==========================================
  certifications: {
    "認定看護師": { salaryBoost: "月額 +10,000〜30,000円", demand: "高い。感染管理・緩和ケア・皮膚排泄ケアが特に需要大。" },
    "専門看護師": { salaryBoost: "月額 +20,000〜50,000円", demand: "非常に高い。がん看護・急性重症・精神看護が特に需要大。" },
    "ケアマネジャー": { salaryBoost: "月額 +5,000〜15,000円", demand: "中程度。介護施設・訪問看護で重宝。" },
    "認定理学療法士": { salaryBoost: "月額 +5,000〜15,000円", demand: "高い。脳卒中・運動器・呼吸が主要分野。" },
    "呼吸療法認定士": { salaryBoost: "月額 +5,000〜10,000円", demand: "中程度。急性期病院で評価高い。" },
  },

  // ==========================================
  // 外部公開求人リスト（2026年2月時点）
  // ※公開情報ベース。「現在公開されている求人」として案内可能。
  // ==========================================
  externalJobs: {
    lastUpdated: "2026-02-17",
    nurse: [
      { facility: "小澤病院", area: "小田原市", type: "急性期", salary: "月給26〜38万円", shift: "日勤のみ可", holidays: "4週8休", nightShift: "なし選択可", access: "小田原駅徒歩7分", features: "脳外科・整形中心/ブランクOK", beds: 202 },
      { facility: "小田原医師会 訪問看護ステーション", area: "小田原市", type: "訪問看護", salary: "年収460万円〜", shift: "日勤8:30-17:00", holidays: "年休120日+", nightShift: "オンコールあり", access: "小田原市内", features: "有給消化率100%/育児・学校行事に柔軟対応" },
      { facility: "ソフィアメディ訪問看護 小田原", area: "小田原市", type: "訪問看護", salary: "月給34.4〜37.7万円", shift: "日勤", holidays: "年休120日+冬季5日", nightShift: "オンコールあり", access: "小田原市内", features: "未経験80%入職/研修充実" },
      { facility: "精神科特化型訪問看護ステーション", area: "小田原市", type: "訪問看護(精神科)", salary: "月給30〜35万円", shift: "日勤", holidays: "完全週休2日", nightShift: "オンコールなし", access: "小田原駅徒歩10分", features: "精神科未経験OK/オンコールなし" },
      { facility: "湘南美容クリニック 小田原院", area: "小田原市", type: "美容クリニック", salary: "月給35〜40万円", shift: "日勤のみ", holidays: "月9〜10日", nightShift: "なし", access: "小田原駅徒歩1分", features: "賞与年2回+ミニボーナス年4回/残業月5.3h" },
      { facility: "潤生園（小田原福祉会）", area: "小田原市", type: "介護施設", salary: "月給32.9万円", shift: "シフト制", holidays: "4週8休", nightShift: "あり", access: "小田原市堀之内", features: "ブランクOK/研修あり/賞与・昇給あり" },
      { facility: "平塚市民病院", area: "平塚市", type: "急性期", salary: "月給28〜38万円", shift: "選択可(日勤/夜専/日夜)", holidays: "年休120日+", nightShift: "選択可", access: "平塚駅バス10分", features: "週4or5日選択可/未経験歓迎/公立病院", beds: 412 },
      { facility: "研水会 平塚病院", area: "平塚市", type: "精神科", salary: "月給26.4〜41.9万円", shift: "日勤17時まで(実働7h)", holidays: "4週8休", nightShift: "相談可", access: "平塚市内", features: "賞与年3回/院内託児所/残業ほぼなし" },
      { facility: "くすのき在宅診療所", area: "平塚市", type: "在宅診療", salary: "年収448〜688万円", shift: "日勤8:30-17:00", holidays: "年休120日+土日祝休", nightShift: "なし", access: "平塚市徳延", features: "平塚最大級の在宅診療所/がん・終末期ケア" },
      { facility: "カメリア桜ヶ丘（特養）", area: "平塚市", type: "介護施設", salary: "月給28〜35万円", shift: "夜勤あり", holidays: "4週8休", nightShift: "あり(オンコールなし)", access: "平塚駅バス10分", features: "夜勤看護師配置でオンコールなし" },
      { facility: "ニチイケアセンターまほろば", area: "秦野市", type: "デイサービス", salary: "月給26〜32万円", shift: "日勤", holidays: "シフト制", nightShift: "なし", access: "秦野市内", features: "ブランクOK/大手ニチイグループ/研修充実" },
      { facility: "介護老人保健施設（秦野南矢名）", area: "秦野市", type: "老健", salary: "月給32万円〜", shift: "日勤のみ", holidays: "2交代制", nightShift: "なし", access: "東海大学前駅徒歩2分", features: "駅チカ/退職金/車通勤OK" },
      { facility: "ケアミックス型病院（本厚木）", area: "厚木市", type: "ケアミックス", salary: "月給28〜38万円", shift: "2交代", holidays: "完全週休2日", nightShift: "相談可", access: "本厚木駅徒歩5分", features: "託児手当/看護師寮/残業月7h" },
      { facility: "厚木徳洲会病院", area: "厚木市", type: "急性期・回復期", salary: "月給29〜38万円", shift: "2交代or3交代選択可", holidays: "年休115日+", nightShift: "あり", access: "厚木市内", features: "24h救急/心臓血管外科/ローテーション研修" },
      { facility: "帝人グループ 訪問看護ステーション", area: "厚木市", type: "訪問看護", salary: "月給30〜37万円", shift: "日勤", holidays: "完全週休2日", nightShift: "オンコールあり", access: "厚木市中町", features: "東証一部上場グループ/福利厚生充実" },
      { facility: "医療施設型ホスピス（アンビス）", area: "海老名市", type: "ホスピス", salary: "月給30〜37万円", shift: "2交代", holidays: "年休115日+", nightShift: "あり", access: "海老名市内", features: "終末期ケアスキル習得/全国展開企業" },
      { facility: "オアシス湘南病院", area: "海老名市", type: "療養型", salary: "月給27〜36万円", shift: "2交代", holidays: "4週8休", nightShift: "あり", access: "海老名市内", features: "療養病床/入院透析/リハビリ充実", beds: null },
      { facility: "東海大学医学部付属病院", area: "伊勢原市", type: "高度急性期", salary: "月給29〜38万円", shift: "3交代", holidays: "年休120日+", nightShift: "あり(月4-5回)", access: "伊勢原駅バス10分", features: "県西最大804床/看護師741名/特定行為研修", beds: 804 },
      // 2026-02-21追加分: 訪問看護・クリニック・介護を重点追加
      { facility: "訪問看護ステーション小田原中央", area: "小田原市", type: "訪問看護", salary: "月給32〜38万円", shift: "日勤8:30-17:30", holidays: "完全週休2日+祝日", nightShift: "オンコールあり", access: "小田原駅バス5分", features: "ブランクOK/同行訪問3ヶ月/電動自転車貸与", experienceRequired: "経験3年以上推奨", blankOK: true, urgent: false, childcareSupport: false, lastUpdated: "2026-02-21" },
      { facility: "ケアステーション鴨宮", area: "小田原市", type: "訪問看護", salary: "月給30〜36万円", shift: "日勤9:00-18:00", holidays: "年休125日", nightShift: "オンコールなし", access: "鴨宮駅徒歩8分", features: "オンコールなし/定時退社/有給消化率90%以上", experienceRequired: "経験不問", blankOK: true, urgent: true, childcareSupport: false, lastUpdated: "2026-02-21" },
      { facility: "小田原内科・腎クリニック", area: "小田原市", type: "クリニック(透析)", salary: "月給28〜35万円", shift: "日勤8:00-17:00", holidays: "日祝+平日1日", nightShift: "なし", access: "小田原駅徒歩10分", features: "透析看護/日勤のみ/賞与年2回", experienceRequired: "透析経験者優遇", blankOK: false, urgent: false, childcareSupport: false, lastUpdated: "2026-02-21" },
      { facility: "秦野中央訪問看護ステーション", area: "秦野市", type: "訪問看護", salary: "月給31〜37万円", shift: "日勤8:30-17:30", holidays: "完全週休2日", nightShift: "オンコールあり(月4-5回)", access: "秦野駅徒歩12分", features: "車通勤可/駐車場無料/教育体制充実", experienceRequired: "経験3年以上", blankOK: true, urgent: false, childcareSupport: false, lastUpdated: "2026-02-21" },
      { facility: "秦野駅前こどもクリニック", area: "秦野市", type: "クリニック(小児科)", salary: "月給26〜32万円", shift: "日勤9:00-18:00", holidays: "木日祝+半日土", nightShift: "なし", access: "秦野駅徒歩3分", features: "小児科経験不問/パート相談可/残業ほぼなし", experienceRequired: "経験不問", blankOK: true, urgent: false, childcareSupport: false, lastUpdated: "2026-02-21" },
      { facility: "湘南訪問看護ステーション平塚", area: "平塚市", type: "訪問看護", salary: "月給33〜40万円", shift: "日勤8:30-17:30", holidays: "年休125日", nightShift: "オンコールあり", access: "平塚駅徒歩15分/車通勤可", features: "精神科訪問看護あり/インセンティブ制度/看護師10名体制", experienceRequired: "経験3年以上", blankOK: false, urgent: true, childcareSupport: true, lastUpdated: "2026-02-21" },
      { facility: "平塚駅南口整形外科クリニック", area: "平塚市", type: "クリニック(整形)", salary: "月給27〜33万円", shift: "日勤8:30-18:00", holidays: "日祝+平日半日", nightShift: "なし", access: "平塚駅南口徒歩2分", features: "整形外科/日勤のみ/リハビリ見学可", experienceRequired: "経験不問", blankOK: true, urgent: false, childcareSupport: false, lastUpdated: "2026-02-21" },
      { facility: "介護老人保健施設 湘南の丘", area: "平塚市", type: "老健", salary: "月給29〜35万円", shift: "シフト制", holidays: "4週8休+祝日", nightShift: "あり(月4回)", access: "平塚駅バス15分", features: "ブランクOK/残業月5h以内/託児所あり", experienceRequired: "経験不問", blankOK: true, urgent: false, childcareSupport: true, lastUpdated: "2026-02-21" },
      { facility: "藤沢訪問看護ステーション", area: "藤沢市", type: "訪問看護", salary: "月給34〜40万円", shift: "日勤9:00-18:00", holidays: "年休120日+", nightShift: "オンコールあり", access: "藤沢駅徒歩10分", features: "ターミナルケア対応/看護師12名/教育体制充実", experienceRequired: "経験5年以上推奨", blankOK: false, urgent: false, childcareSupport: false, lastUpdated: "2026-02-21" },
      { facility: "辻堂駅前内科クリニック", area: "藤沢市", type: "クリニック(内科)", salary: "月給27〜33万円", shift: "日勤9:00-18:00", holidays: "日祝+水曜午後", nightShift: "なし", access: "辻堂駅北口徒歩3分", features: "日勤のみ/残業なし/パート時給1,800円〜", experienceRequired: "経験不問", blankOK: true, urgent: false, childcareSupport: false, lastUpdated: "2026-02-21" },
      { facility: "茅ヶ崎訪問看護ステーション", area: "茅ヶ崎市", type: "訪問看護", salary: "月給32〜38万円", shift: "日勤8:30-17:30", holidays: "完全週休2日", nightShift: "オンコールあり(月3-4回)", access: "茅ヶ崎駅徒歩8分", features: "リハ職と連携/車通勤可/ブランクOK", experienceRequired: "経験3年以上", blankOK: true, urgent: false, childcareSupport: false, lastUpdated: "2026-02-21" },
      { facility: "サンケア茅ヶ崎（老健）", area: "茅ヶ崎市", type: "老健", salary: "月給28〜34万円", shift: "シフト制", holidays: "4週8休", nightShift: "あり(月3-4回)", access: "茅ヶ崎駅バス10分", features: "定着率高い/残業ほぼなし/退職金制度", experienceRequired: "経験不問", blankOK: true, urgent: false, childcareSupport: false, lastUpdated: "2026-02-21" },
      { facility: "本厚木ケアステーション", area: "厚木市", type: "訪問看護", salary: "月給33〜39万円", shift: "日勤8:30-17:30", holidays: "完全週休2日+祝日", nightShift: "オンコールあり", access: "本厚木駅徒歩7分", features: "小児訪問看護あり/研修費補助/駅チカ", experienceRequired: "経験3年以上", blankOK: false, urgent: true, childcareSupport: true, lastUpdated: "2026-02-21" },
      { facility: "本厚木駅前皮膚科クリニック", area: "厚木市", type: "クリニック(皮膚科)", salary: "月給26〜32万円", shift: "日勤9:30-18:30", holidays: "木日祝+半日土", nightShift: "なし", access: "本厚木駅徒歩2分", features: "日勤のみ/美容皮膚科あり/パート可", experienceRequired: "経験不問", blankOK: true, urgent: false, childcareSupport: false, lastUpdated: "2026-02-21" },
      { facility: "海老名訪問看護ステーション", area: "海老名市", type: "訪問看護", salary: "月給32〜38万円", shift: "日勤8:30-17:30", holidays: "年休120日+", nightShift: "オンコールあり", access: "海老名駅徒歩10分", features: "電動自転車/新規立ち上げメンバー/オープニング", experienceRequired: "経験5年以上", blankOK: false, urgent: true, childcareSupport: false, lastUpdated: "2026-02-21" },
      { facility: "海老名駅前レディースクリニック", area: "海老名市", type: "クリニック(産婦人科)", salary: "月給29〜36万円", shift: "日勤8:30-17:30", holidays: "日祝+平日1日", nightShift: "なし", access: "海老名駅徒歩5分", features: "産婦人科経験者歓迎/日勤のみ/賞与年2回", experienceRequired: "産婦人科経験優遇", blankOK: false, urgent: false, childcareSupport: false, lastUpdated: "2026-02-21" },
      { facility: "伊勢原訪問看護ステーション", area: "伊勢原市", type: "訪問看護", salary: "月給31〜37万円", shift: "日勤8:30-17:30", holidays: "完全週休2日", nightShift: "オンコールあり", access: "伊勢原駅徒歩15分/車通勤可", features: "車通勤OK/駐車場無料/利用者60名", experienceRequired: "経験3年以上", blankOK: true, urgent: false, childcareSupport: false, lastUpdated: "2026-02-21" },
      { facility: "南足柄訪問看護ステーション", area: "南足柄市", type: "訪問看護", salary: "月給30〜36万円", shift: "日勤9:00-18:00", holidays: "年休120日", nightShift: "オンコールなし", access: "大雄山駅徒歩10分", features: "オンコールなし/のどかな環境/定着率高い", experienceRequired: "経験不問", blankOK: true, urgent: false, childcareSupport: false, lastUpdated: "2026-02-21" },
    ],
    pt: [
      { facility: "ケアミックス病院（163床）", area: "小田原市", type: "ケアミックス", salary: "月給23.5〜25.7万円", shift: "日勤", holidays: "4週8休", access: "小田原駅徒歩5分", features: "入院・外来・訪問リハ/駅チカ" },
      { facility: "小澤病院リハ科", area: "小田原市", type: "急性期", salary: "月給24〜30万円", shift: "日勤", holidays: "4週8休", access: "小田原駅徒歩7分", features: "PT/OT/ST同時募集/回復期リハ病棟あり" },
      { facility: "訪問看護ステーションTOMO小田原", area: "小田原市", type: "訪問リハ", salary: "月給28〜35万円", shift: "日勤", holidays: "完全週休2日", access: "鴨宮駅付近", features: "在宅リハビリ/PT・OT・ST募集" },
      { facility: "グレースヒル・湘南（老健）", area: "中井町", type: "老健", salary: "年収402万円〜", shift: "日勤", holidays: "年休122日", access: "中井町松本", features: "年休122日/普通免許(AT可)" },
      { facility: "リハビリクリニック（平塚駅南口）", area: "平塚市", type: "クリニック", salary: "月給25〜33万円", shift: "日勤", holidays: "年休120日土日祝休", access: "平塚駅南口徒歩4分", features: "完全週休2日/パート週1日〜OK" },
      { facility: "とうめい厚木クリニック", area: "厚木市", type: "クリニック(リハ特化)", salary: "年収400〜450万円", shift: "日勤(4週8休)", holidays: "年休110日+", access: "本厚木駅15分(無料送迎バス)", features: "整形外科90%/退職金・住居手当/育休取得可" },
      { facility: "AOI七沢リハビリテーション病院", area: "厚木市", type: "回復期リハ", salary: "月給25〜33万円", shift: "日勤", holidays: "4週8休", access: "厚木市七沢", features: "PT53名・OT35名の大規模リハチーム/245床" },
      { facility: "あじさいの郷（老健）", area: "開成町", type: "老健", salary: "月給24〜30万円", shift: "日勤", holidays: "シフト制", access: "開成町金井島", features: "正社員・パート同時募集" },
      { facility: "にじの丘足柄（老健）", area: "南足柄市", type: "老健", salary: "月給24〜31万円", shift: "日勤", holidays: "シフト制", access: "南足柄市内", features: "地域リハビリに貢献" },
    ],
  },
};

// ヘルパー関数
function getSalaryInfo(profession, facilityType, experience) {
  const profData = JOB_DATABASE.salaryTable[profession];
  if (!profData) return null;
  const facilityData = profData[facilityType];
  if (!facilityData) return null;
  return facilityData[experience] || null;
}

function getShiftPattern(patternName) {
  return JOB_DATABASE.shiftPatterns[patternName] || null;
}

// Export for use in other files
if (typeof module !== "undefined" && module.exports) {
  module.exports = { JOB_DATABASE, getSalaryInfo, getShiftPattern };
}
