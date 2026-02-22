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
    phone: "0465-XX-XXXX",         // 電話番号（実番号に置換）
    email: "info@robby-the-match.com",
  },

  // 主要医療機関データ（病院機能報告ベース・全59施設中の代表例）
  HOSPITALS: [
    {
      id: "tokai_univ",
      displayName: "東海大学医学部付属病院（伊勢原市・804床）",
      type: "高度急性期・急性期",
      beds: 804,
      salary: "月給29〜38万円（目安）",
      holidays: "年間休日120日以上",
      nightShift: "あり（三交代制）",
      commute: "伊勢原駅バス10分",
      features: "県西最大規模・看護師741名・救命救急・教育体制充実",
    },
    {
      id: "fujisawa_city",
      displayName: "藤沢市民病院（藤沢市・530床）",
      type: "高度急性期・急性期",
      beds: 530,
      salary: "月給29〜38万円（目安）",
      holidays: "年間休日120日以上",
      nightShift: "あり（三交代制）",
      commute: "藤沢駅バス10分",
      features: "公立病院・看護師405名・地域医療支援病院",
    },
    {
      id: "ebina_general",
      displayName: "海老名総合病院（海老名市・479床）",
      type: "高度急性期・急性期",
      beds: 479,
      salary: "月給29〜38万円（目安）",
      holidays: "年間休日115日以上",
      nightShift: "あり（二交代制）",
      commute: "海老名駅徒歩7分",
      features: "県央唯一の救命救急センター・看護師431名・PT56名",
    },
    {
      id: "hiratsuka_kyosai",
      displayName: "平塚共済病院（平塚市・441床）",
      type: "急性期",
      beds: 441,
      salary: "月給28〜37万円（目安）",
      holidays: "年間休日115日以上",
      nightShift: "あり（二交代制）",
      commute: "平塚駅バス7分",
      features: "地域医療支援病院・看護師301名",
    },
    {
      id: "odawara_city",
      displayName: "小田原市立病院（小田原市・417床）",
      type: "高度急性期・急性期",
      beds: 417,
      salary: "月給28〜38万円（目安）",
      holidays: "年間休日120日以上",
      nightShift: "あり（三交代制）",
      commute: "小田原駅バス10分",
      features: "2026年新築移転予定・看護師270名・救命救急・災害拠点",
    },
    {
      id: "chigasaki_city",
      displayName: "茅ヶ崎市立病院（茅ヶ崎市・401床）",
      type: "急性期",
      beds: 401,
      salary: "月給28〜37万円（目安）",
      holidays: "年間休日120日以上",
      nightShift: "あり（二交代制）",
      commute: "茅ヶ崎駅バス5分",
      features: "公立病院・看護師216名・地域がん拠点",
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
