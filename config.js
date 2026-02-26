// ========================================
// NURSE ROBBY (ナースロビー) - 設定ファイル
// ブランド名・外部連携・表示設定を一括管理
// ========================================

const CONFIG = {
  // ブランド設定
  BRAND_NAME: "ナースロビー",
  TAGLINE: "採用のインフラを、再発明する",
  SITE_TITLE: "ナースロビー | 看護師の転職を手数料10%でまっすぐつなぐ【神奈川県西部】",
  META_DESCRIPTION: "看護師・理学療法士の転職手数料を一般的な紹介手数料の約半分、10%に。AIと人のハイブリッドで、あなたに最適な職場をご紹介。神奈川県西部の求人情報多数。",

  // 会社情報
  COMPANY: {
    name: "はるひメディカルサービス",
    representative: "平島禎之",
    licenseNumber: "23-ユ-302928",  // 有料職業紹介事業許可番号（厚生労働大臣許可）
    address: "神奈川県小田原市",       // 所在地（実住所に置換）
    email: "info@quads-nurse.com",
  },

  // 主要医療機関データ（病床機能報告R5＋医療情報ネット2025.12ベース・代表7施設）
  // referral: true = ナースロビーが直接紹介可能な契約施設
  HOSPITALS: [
    {
      id: "kobayashi",
      displayName: "小林病院（小田原市・150床）",
      type: "急性期・回復期・慢性期",
      beds: 150,
      nurseCount: 54,
      doctorCount: 45,
      salary: "月給27〜35万円（目安）",
      holidays: "年間休日115日以上",
      nightShift: "あり（二交代制）",
      commute: "小田原駅バス15分",
      nursingRatio: "13:1",
      emergencyLevel: "二次救急",
      ownerType: "医療法人",
      features: "ナースロビー紹介可能・ケアミックス・回復期リハビリ・ブランクOK・地域密着",
      referral: true,
    },
    {
      id: "tokai_univ",
      displayName: "東海大学医学部付属病院（伊勢原市・804床）",
      type: "高度急性期",
      beds: 804,
      nurseCount: 1038,
      doctorCount: 550,
      salary: "月給30〜40万円（目安）",
      holidays: "年間休日120日以上",
      nightShift: "あり（三交代制）",
      commute: "伊勢原駅バス10分",
      nursingRatio: "7:1",
      emergencyLevel: "三次救急",
      ownerType: "学校法人",
      features: "県西最大規模・看護師1038名・救命救急・大学病院・教育体制充実",
      referral: false,
    },
    {
      id: "fujisawa_city",
      displayName: "藤沢市民病院（藤沢市・536床）",
      type: "高度急性期・急性期",
      beds: 536,
      nurseCount: 603,
      doctorCount: 184,
      salary: "月給30〜39万円（目安）",
      holidays: "年間休日120日以上",
      nightShift: "あり（三交代制）",
      commute: "藤沢駅バス10分",
      nursingRatio: "7:1",
      emergencyLevel: "三次救急",
      ownerType: "公立",
      features: "公立病院・看護師603名・三次救急・ICU/NICU完備・地域医療支援病院",
      referral: false,
    },
    {
      id: "ebina_general",
      displayName: "海老名総合病院（海老名市・479床）",
      type: "高度急性期・急性期",
      beds: 479,
      nurseCount: 473,
      doctorCount: 148,
      salary: "月給30〜39万円（目安）",
      holidays: "年間休日120日以上",
      nightShift: "あり（三交代制）",
      commute: "海老名駅東口徒歩12分",
      nursingRatio: "7:1",
      emergencyLevel: "三次救急",
      ownerType: "医療法人",
      features: "県央唯一の救命救急センター・看護師473名・PT54名・24時間救急",
      referral: false,
    },
    {
      id: "hiratsuka_kyosai",
      displayName: "平塚共済病院（平塚市・400床）",
      type: "高度急性期・急性期",
      beds: 400,
      nurseCount: 429,
      doctorCount: 122,
      salary: "月給29〜38万円（目安）",
      holidays: "年間休日120日以上",
      nightShift: "あり（三交代制）",
      commute: "平塚駅バス8分",
      nursingRatio: "7:1",
      emergencyLevel: "二次救急",
      ownerType: "公的",
      features: "地域医療支援病院・看護師429名・心臓センター・災害拠点",
      referral: false,
    },
    {
      id: "odawara_city",
      displayName: "小田原市立病院（小田原市・417床）",
      type: "高度急性期・急性期",
      beds: 417,
      nurseCount: 386,
      doctorCount: 114,
      salary: "月給28〜38万円（目安）",
      holidays: "年間休日120日以上",
      nightShift: "あり（三交代制）",
      commute: "小田原駅バス10分",
      nursingRatio: "7:1",
      emergencyLevel: "三次救急",
      ownerType: "公立",
      features: "2026年新築移転予定・看護師386名・救命救急・災害拠点・ICU/NICU完備",
      referral: false,
    },
    {
      id: "chigasaki_city",
      displayName: "茅ヶ崎市立病院（茅ヶ崎市・401床）",
      type: "高度急性期・急性期",
      beds: 401,
      nurseCount: 310,
      doctorCount: 104,
      salary: "月給29〜38万円（目安）",
      holidays: "年間休日120日以上",
      nightShift: "あり（三交代制）",
      commute: "北茅ヶ崎駅徒歩10分",
      nursingRatio: "7:1",
      emergencyLevel: "二次救急",
      ownerType: "公立",
      features: "公立病院・看護師310名・地域がん拠点・災害拠点・DMAT指定",
      referral: false,
    },
  ],

  // 外部API連携（実運用時に設定）
  API: {
    workerEndpoint: "https://robby-the-match-api.robby-the-robot-2026.workers.dev",        // Cloudflare Workers API URL
    slackWebhookUrl: "",       // Slack Webhook URL（レガシー：workerEndpoint設定後は不要）
    googleSheetsId: "",        // Google Sheets ID（レガシー：workerEndpoint設定後は不要）
  },

  // デザイン設定
  DESIGN: {
    primaryBg: "#FAFAF2",
    secondaryBg: "#F2EFE6",
    accentColor: "#5B787D",
    accentSecondary: "#8FB5A1",
    accentHover: "#4A6368",
    textPrimary: "#4A4A4A",
    textSecondary: "#7A7A7A",
    cardBg: "#FFFFFF",
    borderColor: "#D4CFC2",
  },
};
