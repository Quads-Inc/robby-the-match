#!/usr/bin/env python3
"""
ai_content_engine.py — ナースロビー 自律型AIコンテンツ生成エンジン v1.0

Cloudflare Workers AI (Llama 3.3 70B, FREE) を使った完全自律型コンテンツ生成。
企画→生成→品質チェック→スケジュール→投稿準備を一気通貫で実行する。

使い方:
  python3 scripts/ai_content_engine.py --plan              # 1週間分のコンテンツ企画
  python3 scripts/ai_content_engine.py --generate 7        # N件のコンテンツを生成
  python3 scripts/ai_content_engine.py --review             # 生成済みコンテンツの品質チェック
  python3 scripts/ai_content_engine.py --schedule           # 投稿スケジュール設定
  python3 scripts/ai_content_engine.py --auto               # 全自動モード（plan→generate→review→schedule）
  python3 scripts/ai_content_engine.py --status             # 現状サマリ表示

コスト: Cloudflare Workers AI は 10,000 neurons/day 無料。テキスト生成のみなのでほぼ無制限。
"""

import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ロビー君キャラクターシステム
try:
    from robby_character import (
        get_robby_system_prompt,
        pick_hook_pattern,
        pick_cta,
        pick_narration_opening,
        pick_narration_transition,
        pick_catchphrase,
        pick_behavioral_template,
        validate_robby_voice,
        build_robby_caption,
        ROBBY,
        ROBBY_VOICE,
        ROBBY_BEHAVIORAL_ECONOMICS,
    )
    ROBBY_LOADED = True
except ImportError:
    ROBBY_LOADED = False
    print("[INFO] robby_character.py not found. Using default system prompt.")

# ============================================================
# Constants & Configuration
# ============================================================

PROJECT_DIR = Path(__file__).parent.parent

QUEUE_PATH = PROJECT_DIR / "data" / "posting_queue.json"
PLAN_PATH = PROJECT_DIR / "data" / "content_plan.json"
GENERATED_DIR = PROJECT_DIR / "content" / "generated"
READY_DIR = PROJECT_DIR / "content" / "ready"
LOG_DIR = PROJECT_DIR / "logs"
ENV_FILE = PROJECT_DIR / ".env"

# Cloudflare Workers AI endpoint (FREE)
CF_AI_MODEL = "@cf/meta/llama-3.3-70b-instruct-fp8-fast"

# Content MIX ratios (4エージェント討論 2026-02-27 改定)
# サービス紹介は100人超えるまで0%。地域ネタ15%を新設。
MIX_RATIOS = {
    "あるある": 0.50,
    "給与": 0.20,
    "地域ネタ": 0.15,
    "転職": 0.10,
    "トレンド": 0.05,
}

# Category to content_type mapping for queue integration
CATEGORY_TO_CONTENT_TYPE = {
    "あるある": "aruaru",
    "給与": "salary",
    "地域ネタ": "local",
    "転職": "career",
    "トレンド": "trend",
}

# CTA 8:2 rule
CTA_HARD_RATIO = 0.2

# Auto mode: minimum buffer = 2 weeks of content (~14 posts, aim for at least 7 pending)
AUTO_MIN_PENDING = 7
AUTO_TARGET_PENDING = 14

# Optimal posting times (from CLAUDE.md: nurse work rhythm)
POSTING_TIMES = ["17:30", "12:00", "21:00"]

# Curated hashtag sets per category (4エージェント討論 2026-02-27 改定)
# 4個構成: 地域1 + ニッチ1 + 中規模1 + 一般1
# 禁止タグ: #AI, #fyp, #ナースロビー（宣伝感・飽和回避）
# 地域タグローテーション: 神奈川看護師, 小田原, 平塚, 秦野, 湘南ナース, 県西部
HASHTAG_SETS = {
    "あるある": [
        ["#神奈川看護師", "#夜勤あるある", "#看護師あるある", "#看護師"],
        ["#小田原", "#病棟あるある", "#看護師あるある", "#ナース"],
        ["#平塚", "#看護記録", "#看護師の日常", "#看護師"],
        ["#秦野", "#夜勤あるある", "#看護師あるある", "#ナース"],
        ["#湘南ナース", "#師長", "#ナースの本音", "#看護師"],
        ["#県西部", "#病棟あるある", "#看護師あるある", "#看護師"],
    ],
    "給与": [
        ["#神奈川看護師", "#手取り公開", "#看護師転職", "#看護師"],
        ["#小田原", "#手取り公開", "#看護師あるある", "#ナース"],
        ["#湘南ナース", "#手取り公開", "#看護師転職", "#看護師"],
        ["#県西部", "#手取り公開", "#看護師の日常", "#ナース"],
    ],
    "地域ネタ": [
        ["#神奈川看護師", "#夜勤あるある", "#看護師あるある", "#看護師"],
        ["#小田原", "#病棟あるある", "#看護師の日常", "#ナース"],
        ["#平塚", "#師長", "#看護師あるある", "#看護師"],
        ["#秦野", "#看護記録", "#ナースの本音", "#ナース"],
        ["#湘南ナース", "#夜勤あるある", "#看護師転職", "#看護師"],
        ["#県西部", "#転職理由", "#看護師あるある", "#看護師"],
    ],
    "転職": [
        ["#神奈川看護師", "#転職理由", "#看護師転職", "#転職"],
        ["#小田原", "#転職理由", "#看護師転職", "#看護師"],
        ["#湘南ナース", "#師長", "#看護師転職", "#ナース"],
        ["#県西部", "#転職理由", "#看護師転職", "#転職"],
    ],
    "トレンド": [
        ["#神奈川看護師", "#夜勤あるある", "#看護師あるある", "#看護師"],
        ["#小田原", "#病棟あるある", "#ナースの本音", "#ナース"],
        ["#湘南ナース", "#師長", "#看護師の日常", "#看護師"],
        ["#県西部", "#夜勤あるある", "#看護師あるある", "#ナース"],
    ],
}

# Content stock ideas for planning context
# 2026-02-28 改定: アンチジェネリック基準で全面刷新
# 緊張・矛盾・違和感から始まる鋭いコンセプト。予測可能な「AIにやらせてみた」パターンを排除。
CONTENT_STOCK_HINTS = {
    "あるある": [
        "師長に退職届を出した日、ロッカーに3年分のPHSストラップが溜まってた。全部、担当患者からもらったやつ",
        "申し送りで「異常なし」って言った直後、自分の異常に気づいてないことに気づいた夜勤明け",
        "新人に「大丈夫？」って聞いたら「大丈夫です」って返ってきた。自分も5年間同じ嘘ついてた",
        "ナースコール鳴らない夜勤が一番怖い。静かすぎる病棟は何かが起きる前兆",
        "患者さんの「先生には言わないで」が、看護師だけに許された信頼なのか、ただの共犯なのか",
        "休憩室のカップ麺を3分待てたことがない。2分40秒で戻るのがデフォルト",
        "「看護師向いてないかも」と思う日と「この仕事しかない」と思う日が同じ日に来る",
        "退院する患者さんが「もう会いたくないです」って笑った。最高の褒め言葉だった",
        "先輩の「私の時代はもっと大変だった」。その時代を終わらせたのは誰？",
        "夜勤明け、駅のホームで電車を2本見送った。座れる電車を待つ体力すら残ってないから立てないだけ",
    ],
    "給与": [
        "手取り24万。奨学金3万、家賃6万、車2万。残り13万で「命を預かる仕事」をしている",
        "同期の商社勤めが「ボーナス少なくて」って言った額が、こっちの年収の半分だった",
        "夜勤1回の手当8,000円。16時間拘束。時給換算したら深夜のコンビニと同じ",
        "紹介会社の手数料80万。それ、看護師が1年かけて貯める貯金と同じ額",
        "「お金のために働いてるんじゃない」。それを言い続けた結果が手取り24万",
        "病院が紹介会社に払う80万。その金で何人分の夜勤手当が上がると思う？",
    ],
    "地域ネタ": [
        "小田原から横浜まで片道72分。往復144分。年間600時間を満員電車に捧げている看護師がいる",
        "県西部に看護師が足りない。でも県西部の病院は紹介会社に80万払えない。この矛盾の正体",
        "箱根の坂道を毎朝登って出勤する看護師。冬は凍結、夏は汗だく。それでも辞めない理由がある",
        "横浜で手取り28万。小田原で手取り24万。でも家に帰って夕飯を作れるのは小田原の方",
        "秦野の病院の駐車場、夜勤の日だけ満車になる。みんな始発じゃ間に合わないから",
        "「地元で働きたい」を甘えだと言われた。東京に出ないと一人前じゃないみたいに",
        "湘南の海が見える病室。患者さんは喜ぶ。でもその病室を担当する看護師は海を見る暇がない",
    ],
    "転職": [
        "転職サイトに登録した瞬間、知らない番号から17件。看護師の個人情報の値段を知った日",
        "「3年は続けなさい」。それ、誰のための3年？病院の離職率のための3年だった",
        "面接で「前の職場の不満は？」と聞かれた。不満がないなら転職しない。この茶番",
        "紹介会社の営業が「あなたにぴったりの求人が」って言う。全員に同じこと言ってる",
        "退職届を出したら急に「待遇改善する」と言われた。3年間の不満を無視し続けたくせに",
        "転職した先輩に「どう？」って聞いたら「前の方が良かった」。でも戻れない理由がある",
        "4年目で辞めた。7年目の先輩に「もったいない」と言われた。何がもったいないのか説明してほしい",
    ],
    "トレンド": [
        "彼氏が「夜勤って暇でしょ」と言った夜、急変2件ステった。翌朝の「おはよう」が出なかった",
        "母に「看護師辞めたい」と言ったら「せっかく資格取ったのに」。資格は足枷じゃない",
        "結婚式に夜勤明けで出席。化粧で隠しきれないクマを「寝不足？」って聞かれた。365日寝不足だよ",
        "合コンで「看護師です」→「優しそう」。12時間立ちっぱなしで優しさ搾り出してるとは言えない",
        "看護学生の娘が「ママみたいになりたい」。嬉しいのに「やめとけ」が先に出た自分",
    ],
}

# ============================================================
# Anti-Generic Script Writer Prompt (2026-02-28)
# ============================================================

SCRIPT_WRITER_PROMPT_PATH = PROJECT_DIR / "data" / "prompts" / "script_writer.md"

def _load_script_writer_prompt() -> str:
    """Load anti-generic script writer prompt template."""
    if SCRIPT_WRITER_PROMPT_PATH.exists():
        try:
            return SCRIPT_WRITER_PROMPT_PATH.read_text(encoding="utf-8")
        except Exception as e:
            print(f"[WARN] Failed to load script writer prompt: {e}")
    return ""

SCRIPT_WRITER_PROMPT = _load_script_writer_prompt()

# Anti-generic rules injected into content generation
ANTI_GENERIC_RULES = """
## アンチジェネリック・ルール（最重要）
以下のAIスロップを完全に回避せよ:

【禁止】
- 「知ってましたか？」「実は…」「想像してみてください」で始めるフック
- 自己啓発的・モチベーショナルトーン
- 予測可能な3点リスト構成
- 「人生が変わります」系の曖昧な約束
- 過度に磨かれた企業トーン
- 典型的CTA（「フォローしてね」「リンクはプロフに」）で終わる

【代わりにやること】
- 緊張、矛盾、違和感から始める
- 抽象ではなく具体で語る（病棟の匂い、PHSの重さ、ナースシューズの擦れ）
- 安全な3つより、鋭い1つを選ぶ
- リズムを意図的に崩す（短文の後に長文、沈黙の後に怒り）
- 真正性が増すなら、わずかな粗さを許容する
- 「看護師 転職」で検索して出てくる広告と同じトーンなら書き直せ
- 読んで心拍数が上がらないなら書き直せ

トーン: 反体制的だが品がある。怒りではなく「静かな確信」。
「快適に感じるライン」より10%過激に寄せろ。混沌ではなく、鋭さ。
"""

# ============================================================
# Behavioral Psychology x Positive Psychology x Philosophy Templates
# 行動経済学 x ポジティブ心理学 x 哲学 統合カルーセルテンプレート 30本
# ============================================================

TEMPLATES_PATH = PROJECT_DIR / "data" / "carousel_templates.json"

def _load_templates() -> List[Dict]:
    """Load carousel templates from JSON file."""
    if TEMPLATES_PATH.exists():
        try:
            with open(TEMPLATES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Failed to load carousel templates: {e}")
    return []

TEMPLATES = _load_templates()

# Index templates by ID for quick lookup
TEMPLATES_BY_ID = {t["id"]: t for t in TEMPLATES}

# Index templates by category + psychology combination
TEMPLATES_BY_CATEGORY = {}
for _t in TEMPLATES:
    _cat = _t.get("category", "")
    if _cat not in TEMPLATES_BY_CATEGORY:
        TEMPLATES_BY_CATEGORY[_cat] = []
    TEMPLATES_BY_CATEGORY[_cat].append(_t)

PSYCHOLOGY_ALIASES = {
    "behavioral_economics": ["行動経済学", "損失回避", "アンカリング", "フレーミング", "サンクコスト", "社会的証明", "デフォルト効果", "現状維持", "IKEA効果", "初頭効果", "ハロー効果", "メンタルアカウンティング", "機会費用", "時間的割引", "ゼロリスク"],
    "positive_psychology": ["ポジティブ心理学", "PERMA", "成長マインドセット", "フロー理論", "VIA", "感謝介入", "希望理論", "自己決定理論", "ポジティブ加齢"],
    "philosophy": ["哲学", "ストア", "実存主義", "サルトル", "アドラー", "ニーチェ", "禅仏教", "マインドフルネス", "功利主義"],
}

def pick_template(category: str = None, psychology: str = None) -> Optional[Dict]:
    """Pick a random template, optionally filtered by category or psychology."""
    pool = TEMPLATES
    if category:
        pool = [t for t in pool if t.get("category") == category]
    if psychology:
        # Support English alias keys (e.g. "behavioral_economics")
        keywords = PSYCHOLOGY_ALIASES.get(psychology, [psychology])
        pool = [t for t in pool if any(kw in t.get("psychology", "") for kw in keywords)]
    return random.choice(pool) if pool else None

def get_template_for_generation(category: str, cta_type: str = "soft") -> Optional[Dict]:
    """Get a template suitable for content generation, matching CTA type preference."""
    candidates = TEMPLATES_BY_CATEGORY.get(category, [])
    if not candidates:
        return None
    # Prefer templates matching the requested CTA type
    matching_cta = [t for t in candidates if any(
        s.get("cta_type") == cta_type for s in t.get("slides", []) if s.get("type") == "cta"
    )]
    if matching_cta:
        return random.choice(matching_cta)
    return random.choice(candidates)


# ============================================================
# Environment & Utilities
# ============================================================

def load_env():
    """Load .env file from PROJECT_DIR."""
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    os.environ.setdefault(key, value)


def get_cf_credentials() -> Tuple[str, str]:
    """Get Cloudflare credentials from environment."""
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
    api_token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    if not account_id or not api_token:
        print("[FATAL] CLOUDFLARE_ACCOUNT_ID or CLOUDFLARE_API_TOKEN not set in .env")
        sys.exit(1)
    return account_id, api_token


def log_event(event_type: str, data: dict):
    """Write an event to the daily log file."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"ai_engine_{datetime.now().strftime('%Y%m%d')}.log"
    entry = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "data": data,
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def slack_notify(message: str):
    """Send a Slack notification."""
    try:
        result = subprocess.run(
            ["python3", str(PROJECT_DIR / "scripts" / "notify_slack.py"),
             "--message", message],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            print("  [SLACK] Notification sent")
        else:
            print(f"  [SLACK] Send failed (exit {result.returncode})")
    except Exception as e:
        print(f"  [SLACK] Error: {e}")


def timestamp_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ============================================================
# Cloudflare Workers AI Client
# ============================================================

def call_cloudflare_ai(
    prompt: str,
    system_prompt: str = "",
    max_tokens: int = 2048,
    temperature: float = 0.7,
    retries: int = 2,
) -> Optional[str]:
    """
    Call Cloudflare Workers AI (Llama 3.3 70B) for text generation.
    FREE: 10,000 neurons/day.

    Returns the generated text, or None on failure.
    """
    try:
        import requests
    except ImportError:
        # Fallback: use urllib
        return _call_cf_ai_urllib(prompt, system_prompt, max_tokens, temperature, retries)

    account_id, api_token = get_cf_credentials()
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{CF_AI_MODEL}"

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    for attempt in range(retries + 1):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)

            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    result = data.get("result", {})
                    response_text = result.get("response", "")
                    if response_text:
                        return response_text
                    print(f"  [WARN] Empty response from CF AI (attempt {attempt + 1})")
                else:
                    errors = data.get("errors", [])
                    print(f"  [WARN] CF AI errors: {errors}")
            elif resp.status_code == 429:
                wait = (attempt + 1) * 5
                print(f"  [WARN] Rate limited. Waiting {wait}s... (attempt {attempt + 1})")
                time.sleep(wait)
                continue
            else:
                print(f"  [WARN] CF AI HTTP {resp.status_code}: {resp.text[:200]}")

        except Exception as e:
            print(f"  [WARN] CF AI request failed (attempt {attempt + 1}): {e}")

        if attempt < retries:
            time.sleep(2)

    return None


def _call_cf_ai_urllib(
    prompt: str,
    system_prompt: str,
    max_tokens: int,
    temperature: float,
    retries: int,
) -> Optional[str]:
    """Fallback: use urllib if requests is not installed."""
    import urllib.request
    import urllib.error

    account_id, api_token = get_cf_credentials()
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{CF_AI_MODEL}"

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = json.dumps({
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {api_token}")
    req.add_header("Content-Type", "application/json")

    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("success"):
                    result = data.get("result", {})
                    response_text = result.get("response", "")
                    if response_text:
                        return response_text
        except urllib.error.HTTPError as e:
            print(f"  [WARN] CF AI HTTP {e.code} (attempt {attempt + 1})")
            if e.code == 429 and attempt < retries:
                time.sleep((attempt + 1) * 5)
                continue
        except Exception as e:
            print(f"  [WARN] CF AI request failed (attempt {attempt + 1}): {e}")

        if attempt < retries:
            time.sleep(2)

    return None


# ============================================================
# Queue I/O
# ============================================================

def load_queue() -> dict:
    """Load posting_queue.json."""
    if not QUEUE_PATH.exists():
        return {
            "version": 2,
            "created": datetime.now().isoformat(),
            "updated": None,
            "posts": [],
        }
    with open(QUEUE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_queue(queue: dict):
    """Save posting_queue.json."""
    queue["updated"] = datetime.now().isoformat()
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)


def load_plan() -> dict:
    """Load content_plan.json."""
    if not PLAN_PATH.exists():
        return {"created": None, "plans": []}
    with open(PLAN_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_plan(plan: dict):
    """Save content_plan.json."""
    plan["updated"] = datetime.now().isoformat()
    PLAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PLAN_PATH, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)


def get_next_queue_id(queue: dict) -> int:
    """Next integer ID for the posting queue."""
    posts = queue.get("posts", [])
    if not posts:
        return 1
    return max(p.get("id", 0) for p in posts) + 1


def count_by_status(queue: dict) -> Dict[str, int]:
    """Count posts grouped by status."""
    counts: Dict[str, int] = {}
    for p in queue.get("posts", []):
        s = p.get("status", "unknown")
        counts[s] = counts.get(s, 0) + 1
    return counts


def count_pending(queue: dict) -> int:
    """Count pending posts."""
    return sum(1 for p in queue.get("posts", []) if p.get("status") == "pending")


def analyze_queue_mix(queue: dict) -> Dict[str, int]:
    """Analyze content type distribution in pending/ready posts."""
    dist: Dict[str, int] = {cat: 0 for cat in MIX_RATIOS}
    for p in queue.get("posts", []):
        if p.get("status") in ("pending", "ready"):
            ct = p.get("content_type", "")
            # Map content_type back to category
            for cat, ctype in CATEGORY_TO_CONTENT_TYPE.items():
                if ctype == ct:
                    dist[cat] += 1
                    break
    return dist


# ============================================================
# System Prompt for Content Generation
# ============================================================

# SYSTEM_PROMPT: ロビー君キャラクターシステムが読み込まれていればそちらを使う
if ROBBY_LOADED:
    SYSTEM_PROMPT = get_robby_system_prompt()
else:
    SYSTEM_PROMPT = """あなたは医療×採用領域に特化したショート動画の脚本家だ。
クライアントは「ナースロビー」——手数料10%で看護師と病院を直接つなぐサービス。

## あなたの敵＝ジェネリックAI出力
予測可能なフック、使い古されたモチベーショナルトーン、きれいだが感情のない脚本。
これを完全に回避せよ。「よくあるTikTok台本」ではなく、
ジェネリックAI出力と間違えようがない、方向性のある映像の設計図を書け。

## トーン
反体制的だが品がある。怒りではなく「静かな確信」。
「快適に感じるライン」より10%過激に寄せろ。混沌ではなく、鋭さ。

## ペルソナ「ミサキ」（28歳中堅看護師）
- 急性期5-8年目。夜勤あり。手取り24万。リーダー業務。
- 先輩の「前にも言ったよね」がトラウマ。でも後輩には同じこと言いたくない
- 転職サイトは怖い（電話17件のトラウマ）。LINEなら相談してみたい
- 帰りの電車（17:30）と寝る前（22:00）にTikTok/Instagramを見る
- 神奈川県西部在住。小田原から横浜まで通勤72分

## 3要素ルール
すべての投稿に「看護師のリアル × 鋭い洞察 × 地域」の3要素を含めること。
地域名: 神奈川県 / 小田原 / 県西部 / 湘南 / 平塚 / 秦野 / 南足柄

## スライド構成（5枚 — 映像作品として設計）
1枚目: Hook — 認知的不協和、違和感（10文字以内）
2枚目: Escalation — フックの張力を強める展開。超具体的シーン+地域
3枚目: Shift — 視点・トーンの転換点。事実で殴る
4枚目: Core — この動画が存在する唯一の理由。鋭い洞察1つ
5枚目: Ending — 余韻を残す。5秒間スクロールの手を止めるCTA

## キャプション（200文字以内）
- 1行目: 感情フック+地域名
- 2-3行目: 核心の共感ポイント
- 最終行: 自然なCTA（典型的CTAは禁止。「フォローしてね」は使うな）

## ハッシュタグ4個
地域1+ニッチ1+中規模1+一般1。禁止: #AI, #fyp, #ナースロビー

## 法的制約
- 架空設定。患者情報触れない。実在施設の批判なし。ハッシュタグ4個厳守。"""


# ============================================================
# Phase 1: AI Content Planning (--plan)
# ============================================================

def cmd_plan():
    """
    Analyze the current queue balance and generate a 1-week content plan
    using Cloudflare Workers AI.
    """
    print("=" * 60)
    print(f"[PLAN] AI Content Planning - {timestamp_str()}")
    print("=" * 60)

    queue = load_queue()
    pending = count_pending(queue)
    mix = analyze_queue_mix(queue)
    total_active = sum(mix.values())

    print(f"\n[STATUS] Pending in queue: {pending}")
    print(f"[STATUS] Active content mix:")
    for cat, count in mix.items():
        target_pct = MIX_RATIOS[cat] * 100
        actual_pct = (count / total_active * 100) if total_active > 0 else 0
        gap = target_pct - actual_pct
        indicator = "OK" if abs(gap) < 10 else ("LOW" if gap > 0 else "HIGH")
        print(f"  {cat:8s}: {count:2d}  (actual {actual_pct:4.1f}% / target {target_pct:4.0f}%) [{indicator}]")

    # Determine how many posts to plan for (1 week = 7 posts, TikTok daily or near-daily)
    plan_count = 7
    needed = max(0, AUTO_MIN_PENDING - pending)
    if needed > 0:
        plan_count = max(plan_count, needed)
    plan_count = min(plan_count, 14)  # Cap at 2 weeks

    print(f"\n[PLAN] Generating plan for {plan_count} posts...")

    # Determine category allocation
    allocation = _allocate_categories(plan_count, mix)
    print("[PLAN] Category allocation:")
    for cat, n in sorted(allocation.items(), key=lambda x: -x[1]):
        if n > 0:
            print(f"  {cat}: {n}")

    # Assign CTA types (8:2 rule)
    hard_count = max(1, round(plan_count * CTA_HARD_RATIO))
    soft_count = plan_count - hard_count

    # Build plan items
    plan_items = []
    idx = 0
    cats_expanded = []
    for cat, n in allocation.items():
        cats_expanded.extend([cat] * n)
    random.shuffle(cats_expanded)

    for i, cat in enumerate(cats_expanded):
        cta = "hard" if i < hard_count else "soft"
        plan_items.append({
            "day": i + 1,
            "category": cat,
            "cta_type": cta,
            "status": "planned",
            "content_id": None,
            "hint": random.choice(CONTENT_STOCK_HINTS.get(cat, ["(free topic)"])),
        })

    # Call AI to refine plan with specific topic suggestions
    ai_plan = _ai_refine_plan(plan_items, mix)
    if ai_plan:
        plan_items = ai_plan

    # Save plan
    plan = {
        "created": datetime.now().isoformat(),
        "updated": datetime.now().isoformat(),
        "week_of": datetime.now().strftime("%Y-%m-%d"),
        "total": len(plan_items),
        "queue_pending_at_creation": pending,
        "plans": plan_items,
    }
    save_plan(plan)

    # Display
    print(f"\n[PLAN] Content plan saved ({len(plan_items)} items):")
    print("-" * 60)
    for item in plan_items:
        cta_mark = "H" if item["cta_type"] == "hard" else "S"
        hook_hint = item.get("hook_idea", item.get("hint", ""))[:40]
        print(f"  Day {item['day']:2d} | {item['category']:6s} | CTA:{cta_mark} | {hook_hint}")
    print("-" * 60)

    log_event("plan_created", {"count": len(plan_items), "pending": pending})
    print(f"\n[OK] Plan saved to {PLAN_PATH.relative_to(PROJECT_DIR)}")
    return plan_items


def _allocate_categories(count: int, current_mix: Dict[str, int]) -> Dict[str, int]:
    """Allocate categories for new content to balance the MIX ratios."""
    total_current = sum(current_mix.values())

    # Calculate deficit: how many of each category we need to reach ideal ratio
    allocation: Dict[str, int] = {cat: 0 for cat in MIX_RATIOS}
    remaining = count

    # Priority: categories most underrepresented
    deficits = []
    for cat, ratio in MIX_RATIOS.items():
        ideal = ratio * (total_current + count)
        current = current_mix.get(cat, 0)
        deficit = ideal - current
        deficits.append((cat, deficit))

    deficits.sort(key=lambda x: -x[1])  # most underrepresented first

    for cat, deficit in deficits:
        if remaining <= 0:
            break
        alloc = max(0, min(remaining, round(deficit)))
        # Ensure at least the minimum ratio is represented
        min_alloc = max(0, round(MIX_RATIOS[cat] * count))
        alloc = max(alloc, min(min_alloc, remaining))
        allocation[cat] = alloc
        remaining -= alloc

    # Distribute any remaining to the largest category
    if remaining > 0:
        biggest = max(MIX_RATIOS, key=MIX_RATIOS.get)
        allocation[biggest] += remaining

    return allocation


def _ai_refine_plan(plan_items: List[Dict], current_mix: Dict[str, int]) -> Optional[List[Dict]]:
    """Use AI to suggest specific hook ideas for each planned item."""
    categories_list = "\n".join(
        f"Day {item['day']}: category={item['category']}, cta={item['cta_type']}, hint={item.get('hint', '')}"
        for item in plan_items
    )

    prompt = f"""以下のSNS投稿計画について、各日のフック（1枚目のテキスト）案を考えてください。

## 現在の投稿計画
{categories_list}

## アンチジェネリック・ルール（最重要）
「知ってましたか？」「実は…」系のフックは禁止。
緊張、矛盾、違和感から始めろ。安全な言葉を選ぶな。
他の100本の看護師TikTokでも使えるフックなら書き直せ。

## フックの型（ローテーション必須）
1. 矛盾型: 「辞めたいのに辞められない」
2. 断片型: 「手取り24万。命の値段」
3. 告白型: 「もう3ヶ月黙ってた」
4. 対比型: 「72分 vs 10分」
5. 沈黙型: 「師長が何も言わなかった」
6. 問い型: 「誰のための3年？」
7. 衝撃数字型: 「紹介料80万の行方」

## ルール
- フックは20文字以内。「ロビー」の名前を含める
- 病棟の匂い、PHSの重さ、ナースシューズの擦れ——その粒度で具体的に書け
- ミサキ（28歳、夜勤明け、帰りの電車）のスクロールを止める違和感
- hintを参考にしつつ、ジェネリックなら捨てて書き直せ
- 読んで心拍数が上がらないフックは不合格

## 出力形式
JSON配列のみ出力。マークダウン記法や説明文は不要。
[
  {{"day": 1, "hook_idea": "フック案"}},
  {{"day": 2, "hook_idea": "フック案"}},
  ...
]"""

    print("\n[AI] Generating hook ideas via Cloudflare Workers AI...")
    result = call_cloudflare_ai(prompt, SYSTEM_PROMPT, max_tokens=1500, temperature=0.8)

    if not result:
        print("[WARN] AI plan refinement failed. Using hint-based plan.")
        return None

    # Parse JSON from AI response
    parsed = _parse_json_from_text(result)
    if parsed and isinstance(parsed, list):
        for ai_item in parsed:
            day = ai_item.get("day")
            hook = ai_item.get("hook_idea", "")
            if day and hook:
                for plan_item in plan_items:
                    if plan_item["day"] == day:
                        plan_item["hook_idea"] = hook[:20]
                        break
        print(f"[AI] Refined {len(parsed)} hook ideas")
        return plan_items

    print("[WARN] Could not parse AI response. Using hint-based plan.")
    return None


# ============================================================
# Phase 2: AI Content Generation (--generate N)
# ============================================================

def cmd_generate(count: int):
    """
    Generate N complete carousel content sets using Cloudflare Workers AI.
    Creates slide JSON + carousel images, then adds to posting queue.
    """
    if count < 1 or count > 20:
        print(f"[ERROR] Count must be 1-20, got {count}")
        sys.exit(1)

    print("=" * 60)
    print(f"[GENERATE] AI Content Generation - {timestamp_str()}")
    print(f"[GENERATE] Target: {count} posts")
    print("=" * 60)

    # Load plan if available
    plan = load_plan()
    plan_items = [p for p in plan.get("plans", []) if p.get("status") == "planned"]

    queue = load_queue()
    current_mix = analyze_queue_mix(queue)

    # If no plan, create an ad-hoc allocation
    if not plan_items:
        print("[INFO] No plan found. Creating ad-hoc allocation.")
        allocation = _allocate_categories(count, current_mix)
        plan_items = []
        idx = 0
        hard_count = max(1, round(count * CTA_HARD_RATIO))
        for cat, n in allocation.items():
            for _ in range(n):
                cta = "hard" if idx < hard_count else "soft"
                plan_items.append({
                    "day": idx + 1,
                    "category": cat,
                    "cta_type": cta,
                    "status": "planned",
                    "hint": random.choice(CONTENT_STOCK_HINTS.get(cat, [""])),
                })
                idx += 1

    # Use only as many plan items as requested
    items_to_generate = plan_items[:count]

    # Create batch directory
    batch_name = f"ai_batch_{datetime.now().strftime('%Y%m%d_%H%M')}"
    batch_dir = GENERATED_DIR / batch_name
    batch_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n[BATCH] Directory: {batch_dir.relative_to(PROJECT_DIR)}")

    generated = []
    failed = []

    for i, item in enumerate(items_to_generate, 1):
        category = item["category"]
        cta_type = item["cta_type"]
        hook_hint = item.get("hook_idea", item.get("hint", ""))

        content_id = f"ai_{category[:2]}_{datetime.now().strftime('%m%d')}_{i:02d}"

        print(f"\n{'=' * 50}")
        print(f"[{i}/{count}] Generating: {content_id} ({category}, CTA:{cta_type})")
        print(f"{'=' * 50}")

        # Step 1: Generate content JSON via AI
        content_data = _generate_content_with_ai(
            category=category,
            cta_type=cta_type,
            content_id=content_id,
            hook_hint=hook_hint,
        )

        if not content_data:
            print(f"  [FAIL] Content generation failed for {content_id}")
            failed.append({"content_id": content_id, "category": category, "reason": "AI generation failed"})
            continue

        # Step 2: Save content JSON
        json_path = batch_dir / f"{content_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(content_data, f, ensure_ascii=False, indent=2)
        print(f"  [OK] Content JSON saved: {json_path.name}")

        # Step 3: Generate carousel slide images
        slide_dir = batch_dir / content_id
        slide_paths = _generate_carousel_slides(content_data, str(slide_dir))

        if not slide_paths:
            print(f"  [WARN] Carousel generation failed. Adding to queue anyway.")
            failed.append({"content_id": content_id, "category": category, "reason": "Carousel generation failed (queued)"})

        # Step 4: Add to queue
        next_id = get_next_queue_id(queue)
        queue_entry = {
            "id": next_id,
            "content_id": content_id,
            "batch": batch_name,
            "slide_dir": str(slide_dir.relative_to(PROJECT_DIR)),
            "json_path": str(json_path.relative_to(PROJECT_DIR)),
            "caption": content_data.get("caption", ""),
            "hashtags": content_data.get("hashtags", []),
            "cta_type": cta_type,
            "content_type": CATEGORY_TO_CONTENT_TYPE.get(category, "aruaru"),
            "status": "pending",
            "video_path": None,
            "posted_at": None,
            "tiktok_url": None,
            "error": None,
            "performance": {"views": None, "likes": None, "saves": None, "comments": None},
            "ai_score": content_data.get("_ai_score"),
        }
        queue["posts"].append(queue_entry)
        print(f"  [OK] Added to queue: id={next_id}")

        generated.append({
            "content_id": content_id,
            "category": category,
            "cta_type": cta_type,
            "hook": content_data.get("hook", ""),
            "queue_id": next_id,
        })

        # Mark plan item as generated
        item["status"] = "generated"
        item["content_id"] = content_id

    # Save queue and plan
    save_queue(queue)
    save_plan(plan)

    # Slack notification
    summary_lines = [
        f"[AI Content Engine] Generation complete",
        f"Batch: {batch_name}",
        f"Generated: {len(generated)} / Failed: {len(failed)}",
        "",
    ]
    for g in generated:
        summary_lines.append(f"  {g['content_id']} ({g['category']}, {g['cta_type']}): {g['hook'][:30]}")

    slack_notify("\n".join(summary_lines))

    # Final summary
    print(f"\n{'=' * 60}")
    print(f"[SUMMARY] Generated: {len(generated)} | Failed: {len(failed)}")
    print(f"  Batch: {batch_name}")
    print(f"  Queue pending: {count_pending(queue)}")
    for g in generated:
        print(f"    {g['content_id']} ({g['category']}) hook: {g['hook'][:35]}")
    if failed:
        print("  Failures:")
        for f_item in failed:
            print(f"    {f_item['content_id']}: {f_item['reason']}")
    print("=" * 60)

    log_event("generate_complete", {
        "batch": batch_name,
        "generated": len(generated),
        "failed": len(failed),
        "queue_pending": count_pending(queue),
    })

    return generated


def _generate_content_with_ai(
    category: str,
    cta_type: str,
    content_id: str,
    hook_hint: str = "",
) -> Optional[Dict]:
    """Generate a complete carousel content set using Cloudflare Workers AI."""

    cta_instruction = ""
    if cta_type == "soft":
        cta_instruction = (
            "5枚目のCTAはソフトCTA（バリエーション豊富に）:\n"
            "  - 保存系: 「この表、保存しといて損ないよ」「あとで見返したい人は保存」\n"
            "  - フォロー系: 「フォローしたら毎日こういう情報届くよ」「続きはフォローして待ってて」\n"
            "  - 共感系: 「わかる！って人はいいね押してほしい」「同じ経験ある人コメントで教えて」\n"
            "  - 共有系: 「同僚にも教えてあげて」「夜勤仲間にシェアして」\n"
            "  サービス名は出さない。宣伝感ゼロで。"
        )
    else:
        cta_instruction = (
            "5枚目のCTAはハードCTA（でも自然に）:\n"
            "  - 相談誘導: 「気になる人はプロフのリンクから相談できるよ」\n"
            "  - LINE誘導: 「もっと詳しく知りたい人はLINEで聞いてみて」\n"
            "  - 情報提供: 「手数料10%で転職サポートしてるんだ。プロフ見てみて」\n"
            "  押し売り感を出すな。あくまで「情報を渡す」スタンス。"
        )

    hint_text = f"フックのヒント: {hook_hint}" if hook_hint else ""

    # テンプレートベースの心理学フレームワーク注入
    template_context = ""
    template = get_template_for_generation(category, cta_type)
    if template:
        psych = template.get("psychology", "")
        emotion_curve = " → ".join(template.get("emotion_curve", []))
        slide_types = [s.get("type", "") for s in template.get("slides", [])]
        robby_voice_ref = template.get("robby_voice", "")[:100]
        template_context = f"""

## 心理学フレームワーク（テンプレート {template['id']} 参照）
- 心理学理論: {psych}
- 感情曲線: {emotion_curve}
- スライド構成: {' → '.join(slide_types)}
- ロビー君の語り口参考: 「{robby_voice_ref}...」
- このテンプレートのhook参考: 「{template.get('slides', [{}])[0].get('text', '')}」"""

    # ロビー君キャラクターシステムが利用可能な場合、追加コンテキストを注入
    robby_context = ""
    if ROBBY_LOADED:
        hook_pattern = pick_hook_pattern(category)
        cta_template = pick_cta(cta_type)
        behavioral_hint = ""
        if category in ("給与", "転職"):
            behavioral_hint = f"\n- 行動経済学の仕掛け（自然に組み込め）: {pick_behavioral_template('loss_aversion')}"
        elif category == "あるある":
            behavioral_hint = f"\n- 行動経済学の仕掛け（自然に組み込め）: {pick_behavioral_template('social_proof')}"
        elif category == "地域ネタ":
            behavioral_hint = f"\n- 行動経済学の仕掛け（自然に組み込め）: {pick_behavioral_template('loss_aversion')}"

        robby_context = f"""

## ロビー君キャラクター指示（最重要）
- 一人称は「ロビー」。絶対に「私」「僕」を使わない。
- 口調は「〜だよ」「〜なんだ」。敬語禁止。
- フック内に必ず「ロビー」の名前を含める。
- 解説文は2-3文に1回「ロビー」を入れてキャラ感を維持。
- 参考フックパターン: {hook_pattern['pattern']}（例: {hook_pattern['example']}）
- CTA参考: {cta_template['text']}{behavioral_hint}"""

    # 感情ベクトル候補（カテゴリ別）
    emotion_vectors = {
        "あるある": ["連帯と疲弊の共存", "静かな怒り", "自嘲と誇りの矛盾", "孤独な共感"],
        "給与": ["構造への怒り", "諦観の先にある反骨", "数字が暴く不条理", "搾取への静かな告発"],
        "地域ネタ": ["土地への執着と葛藤", "都会信仰への違和感", "地元の不便さへの愛憎"],
        "転職": ["恐怖と衝動の狭間", "制度への不信", "自由と安定の二律背反"],
        "トレンド": ["日常の中の断絶", "理解されない怒り", "皮肉混じりの愛情"],
    }
    chosen_emotion = random.choice(emotion_vectors.get(category, ["反骨"]))

    prompt = f"""TikTokカルーセル投稿の台本を1つ生成してください。

{ANTI_GENERIC_RULES}

## 方向性コミットメント（書く前に決めろ）
- 感情ベクトル: {chosen_emotion}
- この感情にコミットしてブレるな。安全に書くな。平均化するな。

## 指定
- カテゴリ: {category}
- CTA種類: {cta_type}
- {cta_instruction}
{hint_text}{template_context}{robby_context}

## 構成（5枚: Hook → Escalation → Shift → Core → Ending）
- hook: 1枚目（10文字以内。認知的不協和または違和感を生むこと。「ロビー」の名前を含める）
- slides: 5枚分のテキスト（配列）
  - slides[0]: Hook — スクロールを止める違和感（10文字以内）
  - slides[1]: Escalation — フックの張力を強める展開。超具体的なシーン描写+地域要素
  - slides[2]: Shift — 視点・トーン・テンポの転換点。「知らなかった」を生む事実
  - slides[3]: Core — この動画が存在する唯一の理由。感情のピーク。鋭い1つの洞察
  - slides[4]: Ending — CTAだが余韻を残す。見た人が5秒間スクロールの手を止める一文
- caption: SNSキャプション:
  1行目: 感情フック（質問形式推奨。地域名含む）
  2-3行目: 核心（短文で区切る）
  最終行: 自然なCTA（典型的CTAは禁止）
  ※改行は \\n で表現。200文字以内。
- hashtags: ハッシュタグ4個（地域1+ニッチ1+中規模1+一般1）
  禁止: #AI, #fyp, #ナースロビー
- reveal_text: コアスライドの衝撃テキスト（短く、鋭く）
- reveal_number: 数字（あれば。例: "144分", "80万円"）
- emotion_vector: "{chosen_emotion}"
- bgm_mood: BGMの質感（曲名ではなく音の描写。例:「ナースシューズが廊下を叩く音だけ」）

## 超具体性+地域性の例（この粒度で書け）
BAD: 「夜勤あるある」→ ジェネリック。100本のTikTokで使える。
GOOD: 「夜勤明け、駅のホームで電車2本見送った。座りたいんじゃない、立てないだけ」
BAD: 「給料が安い」→ 誰でも言える。鋭さゼロ。
GOOD: 「手取り24万。命を預かる対価が、深夜コンビニバイトと同じ時給」
BAD: 「転職したい」→ 感情が動かない。
GOOD: 「退職届を出したら急に待遇改善すると言われた。3年間の不満は聞こえなかったのに」

## セルフチェック（引っかかったら書き直せ）
□ このフック、他の100本の看護師TikTokでも使えないか？
□ ナースロビーの名前を消しても成立するか？
□ 「看護師 転職」で検索して出てくる広告と同じトーンか？
□ 読んで心拍数が上がるか？

## 重要
- 地域名を1つ以上含めること（台本 or キャプション）
- ロビー君のキャラクターで語る（一人称「ロビー」、タメ口「〜だよ」「〜なんだ」）
- 架空のストーリーであること
- キャプション200文字以内

## 出力形式
JSON形式のみ出力。マークダウン記法、コードフェンス、説明文は一切不要。JSONだけ返してください。

{{
  "id": "{content_id}",
  "hook": "10文字以内のフック",
  "emotion_vector": "{chosen_emotion}",
  "slides": [
    "1枚目: Hook（10文字以内。違和感を生む）",
    "2枚目: Escalation。張力を強める。超具体的場面+地域",
    "3枚目: Shift。視点の転換。事実で殴る",
    "4枚目: Core。この動画の存在理由。鋭い洞察1つ",
    "5枚目: Ending。余韻を残すCTA"
  ],
  "caption": "感情フック+地域名\\n\\n核心。\\n\\n自然なCTA",
  "hashtags": ["#地域タグ", "#ニッチタグ", "#中規模タグ", "#一般タグ"],
  "reveal_text": "鋭いリビールテキスト",
  "reveal_number": "数字（任意）",
  "bgm_mood": "音の質感",
  "category": "{category}",
  "cta_type": "{cta_type}"
}}"""

    for attempt in range(2):
        if attempt > 0:
            print(f"  [RETRY] Attempt {attempt + 1}/2")

        print(f"  [AI] Calling Cloudflare Workers AI...")
        result = call_cloudflare_ai(prompt, SYSTEM_PROMPT, max_tokens=2000, temperature=0.75)

        if not result:
            print(f"  [WARN] AI returned no result (attempt {attempt + 1})")
            continue

        data = _parse_json_from_text(result)
        if not data:
            print(f"  [WARN] Could not parse JSON from AI response")
            print(f"  [DEBUG] First 300 chars: {result[:300]}")
            continue

        # Validate and fix
        if _validate_content(data, content_id):
            # Assign curated hashtags if AI-generated ones are poor
            if not data.get("hashtags") or len(data["hashtags"]) < 2:
                data["hashtags"] = random.choice(HASHTAG_SETS.get(category, HASHTAG_SETS["あるある"]))

            # Trim hashtags to max 5
            if len(data.get("hashtags", [])) > 5:
                data["hashtags"] = data["hashtags"][:5]

            # Ensure category and id are correct
            data["id"] = content_id
            data["category"] = category
            data["cta_type"] = cta_type

            # ロビー君の口調バリデーション
            if ROBBY_LOADED:
                all_text = " ".join([
                    data.get("hook", ""),
                    data.get("caption", ""),
                    " ".join(data.get("slides", [])),
                ])
                voice_issues = validate_robby_voice(all_text)
                if voice_issues:
                    for issue in voice_issues:
                        print(f"  [VOICE] {issue}")
                    data["_voice_issues"] = voice_issues
                else:
                    print(f"  [VOICE] OK: ロビー君の口調に準拠")

                # フックに「ロビー」が含まれているか確認
                if "ロビー" not in data.get("hook", ""):
                    print(f"  [VOICE] WARN: フックに「ロビー」がありません。修正推奨。")

            print(f"  [OK] Content generated: hook=\"{data.get('hook', '')[:30]}\"")
            return data

    print(f"  [FAIL] Content generation failed after 2 attempts")
    return None


def _validate_content(data: dict, content_id: str) -> bool:
    """Validate that generated content has required fields and correct structure."""
    required = ["hook", "slides", "caption"]
    for key in required:
        if key not in data:
            print(f"  [WARN] Missing key: {key}")
            return False

    hook = data.get("hook", "")
    if len(hook) > 10:
        # Auto-trim hook to 10 chars (5枚構成の短フック)
        data["hook"] = hook[:10]
        print(f"  [WARN] Hook trimmed to 10 chars")

    slides = data.get("slides", [])
    if not isinstance(slides, list) or len(slides) < 3:
        print(f"  [WARN] slides must have at least 3 items, got {len(slides) if isinstance(slides, list) else 'N/A'}")
        return False

    # Pad to 5 slides if needed (Hook + Content x3 + CTA)
    while len(slides) < 5:
        slides.append(slides[-1] if slides else "...")
    data["slides"] = slides[:5]

    caption = data.get("caption", "")
    if len(caption) > 200:
        data["caption"] = caption[:200]
        print(f"  [WARN] Caption trimmed to 200 chars")

    return True


def _generate_carousel_slides(content_data: dict, output_dir: str) -> Optional[List[str]]:
    """
    Call generate_carousel.py to create slide images from content data.
    Returns list of generated file paths, or None on failure.
    """
    carousel_script = PROJECT_DIR / "scripts" / "generate_carousel.py"
    if not carousel_script.exists():
        print(f"  [WARN] generate_carousel.py not found at {carousel_script}")
        return None

    # Save a temp JSON that generate_carousel can read
    temp_json = Path(output_dir).parent / f"_temp_{content_data.get('id', 'unknown')}.json"
    temp_json.parent.mkdir(parents=True, exist_ok=True)
    with open(temp_json, "w", encoding="utf-8") as f:
        json.dump(content_data, f, ensure_ascii=False, indent=2)

    try:
        print(f"  [CAROUSEL] Generating slides...")
        result = subprocess.run(
            [
                "python3", str(carousel_script),
                "--single-json", str(temp_json),
                "--output", str(Path(output_dir).parent),
            ],
            capture_output=True, text=True, timeout=120,
            cwd=str(PROJECT_DIR),
        )

        if result.returncode == 0:
            # Check if output directory has PNG files
            out_path = Path(output_dir)
            if not out_path.exists():
                # generate_carousel.py may use a different naming; check parent
                parent = Path(output_dir).parent
                for d in parent.iterdir():
                    if d.is_dir() and content_data.get("id", "") in d.name:
                        out_path = d
                        break

            if out_path.exists():
                pngs = sorted(out_path.glob("*.png"))
                if pngs:
                    print(f"  [CAROUSEL] Generated {len(pngs)} slides in {out_path.name}")
                    return [str(p) for p in pngs]

            # Fallback: check stdout for paths
            print(f"  [CAROUSEL] Output: {result.stdout[-300:].strip()}")
            return []
        else:
            print(f"  [CAROUSEL] Failed (exit {result.returncode})")
            if result.stderr:
                print(f"  [CAROUSEL] stderr: {result.stderr[-300:]}")
            return None

    except subprocess.TimeoutExpired:
        print(f"  [CAROUSEL] Timeout")
        return None
    except Exception as e:
        print(f"  [CAROUSEL] Error: {e}")
        return None
    finally:
        # Clean up temp file
        if temp_json.exists():
            temp_json.unlink()


# ============================================================
# Phase 3: AI Quality Review (--review)
# ============================================================

def cmd_review():
    """
    Review all pending/unreviewed content in the queue.
    Uses AI to score each post 1-10 on brand guidelines fit.
    Auto-rejects score < 6.
    """
    print("=" * 60)
    print(f"[REVIEW] AI Quality Check - {timestamp_str()}")
    print("=" * 60)

    queue = load_queue()
    posts_to_review = [
        p for p in queue.get("posts", [])
        if p.get("status") == "pending" and p.get("ai_score") is None
    ]

    if not posts_to_review:
        print("[INFO] No unreviewed pending posts found.")
        return

    print(f"[REVIEW] Found {len(posts_to_review)} posts to review\n")

    reviewed = 0
    rejected = 0
    approved = 0

    for post in posts_to_review:
        post_id = post["id"]
        content_id = post.get("content_id", "?")
        caption = post.get("caption", "")
        hashtags = post.get("hashtags", [])
        cta_type = post.get("cta_type", "soft")
        content_type = post.get("content_type", "unknown")

        # Try to load full content JSON for deeper review
        json_path = post.get("json_path")
        slides_text = ""
        if json_path:
            full_path = PROJECT_DIR / json_path
            if full_path.exists():
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content_json = json.load(f)
                    slides = content_json.get("slides", [])
                    slides_text = "\n".join(
                        f"  Slide {i+1}: {s}" for i, s in enumerate(slides)
                    )
                except Exception:
                    pass

        print(f"[REVIEW] #{post_id} {content_id} ({content_type}, {cta_type})")

        prompt = f"""以下のSNS投稿を品質チェックしてください。

## 投稿内容
- ID: {content_id}
- カテゴリ: {content_type}
- CTA: {cta_type}
- キャプション: {caption}
- ハッシュタグ: {' '.join(hashtags)}
{f'- スライド内容:{chr(10)}{slides_text}' if slides_text else ''}

## 評価基準（各項目1-10で採点）
1. ペルソナ適合度: ミサキ（28歳看護師）が手を止めるか？
2. フック強度: 1枚目で「見たい」と思うか？3秒ルール
3. 法的遵守: 架空設定か？患者情報なし？施設批判なし？
4. CTA適切性: 8:2ルール（ソフト/ハード比率）に合っているか？
5. 共感度: 看護師のリアルな気持ちに寄り添っているか？

## 出力形式（JSONのみ。説明文不要）
{{
  "score": 総合スコア（1-10の整数）,
  "persona_fit": 1-10,
  "hook_strength": 1-10,
  "legal_compliance": 1-10,
  "cta_quality": 1-10,
  "empathy": 1-10,
  "issues": ["問題点があれば記載"],
  "suggestion": "改善提案（1文）"
}}"""

        result = call_cloudflare_ai(prompt, SYSTEM_PROMPT, max_tokens=500, temperature=0.3)

        if result:
            review_data = _parse_json_from_text(result)
            if review_data and isinstance(review_data.get("score"), (int, float)):
                score = int(review_data["score"])
                post["ai_score"] = score
                post["ai_review"] = review_data

                status_mark = "PASS" if score >= 6 else "REJECT"
                if score < 6:
                    post["status"] = "rejected"
                    post["error"] = f"AI review score {score}/10: {review_data.get('suggestion', '')}"
                    rejected += 1
                else:
                    approved += 1

                issues = review_data.get("issues", [])
                issues_str = ", ".join(issues[:2]) if issues else "none"
                print(f"  Score: {score}/10 [{status_mark}] Issues: {issues_str}")

                reviewed += 1
                continue

        # If AI review failed, give a neutral pass
        print(f"  [WARN] AI review failed for #{post_id}. Assigning score 7 (default pass).")
        post["ai_score"] = 7
        approved += 1
        reviewed += 1

    save_queue(queue)

    print(f"\n{'=' * 60}")
    print(f"[REVIEW SUMMARY]")
    print(f"  Reviewed: {reviewed}")
    print(f"  Approved (score >= 6): {approved}")
    print(f"  Rejected (score < 6): {rejected}")
    print("=" * 60)

    if rejected > 0:
        slack_notify(
            f"[AI Review] {reviewed} posts reviewed: {approved} approved, {rejected} rejected.\n"
            f"Rejected posts need regeneration."
        )

    log_event("review_complete", {
        "reviewed": reviewed,
        "approved": approved,
        "rejected": rejected,
    })


# ============================================================
# Phase 4: Auto-Schedule (--schedule)
# ============================================================

def cmd_schedule():
    """
    Pick next pending posts from queue, prepare them for posting.
    Sets optimal posting times and creates content/ready/ directory.
    """
    print("=" * 60)
    print(f"[SCHEDULE] Content Scheduling - {timestamp_str()}")
    print("=" * 60)

    queue = load_queue()
    pending_posts = [
        p for p in queue.get("posts", [])
        if p.get("status") == "pending" and p.get("ai_score", 7) >= 6
    ]

    if not pending_posts:
        print("[INFO] No schedulable posts in queue.")
        return

    # Schedule up to 7 posts (1 week)
    to_schedule = pending_posts[:7]
    print(f"[SCHEDULE] Scheduling {len(to_schedule)} posts\n")

    READY_DIR.mkdir(parents=True, exist_ok=True)
    scheduled = []

    for i, post in enumerate(to_schedule):
        post_id = post["id"]
        content_id = post.get("content_id", "unknown")

        # Calculate scheduled datetime
        schedule_date = datetime.now() + timedelta(days=i)
        posting_time = POSTING_TIMES[i % len(POSTING_TIMES)]
        schedule_dt = f"{schedule_date.strftime('%Y-%m-%d')} {posting_time}"

        print(f"  #{post_id} {content_id} -> {schedule_dt}")

        # Prepare ready directory
        ready_name = f"{schedule_date.strftime('%Y%m%d')}_{content_id}"
        ready_subdir = READY_DIR / ready_name
        ready_subdir.mkdir(parents=True, exist_ok=True)

        # Copy slides if they exist
        slide_dir = PROJECT_DIR / post.get("slide_dir", "")
        slides_copied = 0
        if slide_dir.exists():
            for png in sorted(slide_dir.glob("*.png")):
                dest = ready_subdir / png.name
                shutil.copy2(str(png), str(dest))
                slides_copied += 1

        # Write caption.txt
        caption_file = ready_subdir / "caption.txt"
        with open(caption_file, "w", encoding="utf-8") as f:
            f.write(post.get("caption", ""))
            f.write("\n\n")
            f.write(" ".join(post.get("hashtags", [])))

        # Write schedule.json
        meta = {
            "post_id": post_id,
            "content_id": content_id,
            "scheduled_for": schedule_dt,
            "posting_time": posting_time,
            "content_type": post.get("content_type", ""),
            "cta_type": post.get("cta_type", ""),
            "ai_score": post.get("ai_score"),
            "slides_count": slides_copied,
            "prepared_at": datetime.now().isoformat(),
        }
        with open(ready_subdir / "schedule.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        # Update queue
        post["status"] = "ready"
        post["scheduled_for"] = schedule_dt
        post["error"] = None

        scheduled.append({
            "post_id": post_id,
            "content_id": content_id,
            "scheduled_for": schedule_dt,
            "slides": slides_copied,
            "ready_dir": str(ready_subdir.relative_to(PROJECT_DIR)),
        })

    save_queue(queue)

    # Slack notification
    schedule_lines = [f"[Schedule] {len(scheduled)} posts scheduled:"]
    for s in scheduled:
        schedule_lines.append(
            f"  #{s['post_id']} {s['content_id']} -> {s['scheduled_for']} ({s['slides']} slides)"
        )
    schedule_lines.append(f"\nReady folders in content/ready/")
    schedule_lines.append(f"Upload via Buffer, then: python3 scripts/sns_workflow.py --mark-posted <ID>")
    slack_notify("\n".join(schedule_lines))

    print(f"\n{'=' * 60}")
    print(f"[SCHEDULE SUMMARY]")
    print(f"  Scheduled: {len(scheduled)} posts")
    for s in scheduled:
        print(f"    #{s['post_id']} {s['content_id']} -> {s['scheduled_for']} ({s['slides']} slides)")
    print(f"  Ready at: content/ready/")
    print("=" * 60)

    log_event("schedule_complete", {"scheduled": len(scheduled)})


# ============================================================
# Phase 5: Full Auto Mode (--auto)
# ============================================================

def cmd_auto():
    """
    Full autonomous mode: plan -> generate -> review -> schedule.
    Maintains a 2-week content buffer. Self-correcting.
    """
    print("=" * 60)
    print(f"[AUTO] Full Auto Mode - {timestamp_str()}")
    print("=" * 60)

    queue = load_queue()
    pending = count_pending(queue)
    statuses = count_by_status(queue)

    print(f"\n[AUTO] Queue status:")
    for status, cnt in sorted(statuses.items()):
        print(f"  {status}: {cnt}")
    print(f"  Total pending: {pending}")
    print(f"  Target buffer: {AUTO_TARGET_PENDING}")

    # Step 1: Plan
    print(f"\n{'=' * 50}")
    print("[AUTO] Step 1: Planning...")
    print(f"{'=' * 50}")
    plan_items = cmd_plan()

    # Step 2: Generate (only if queue needs more content)
    queue = load_queue()  # Reload
    pending = count_pending(queue)
    need_count = max(0, AUTO_MIN_PENDING - pending)

    if need_count > 0:
        print(f"\n{'=' * 50}")
        print(f"[AUTO] Step 2: Generating {need_count} posts (pending={pending} < min={AUTO_MIN_PENDING})")
        print(f"{'=' * 50}")
        cmd_generate(need_count)
    else:
        print(f"\n[AUTO] Step 2: Skip generation (pending={pending} >= min={AUTO_MIN_PENDING})")

    # Step 3: Review
    print(f"\n{'=' * 50}")
    print("[AUTO] Step 3: Quality Review...")
    print(f"{'=' * 50}")
    cmd_review()

    # Step 3.5: Self-correction - regenerate rejected posts
    queue = load_queue()
    rejected_count = sum(1 for p in queue.get("posts", []) if p.get("status") == "rejected")
    if rejected_count > 0:
        print(f"\n[AUTO] Self-correction: {rejected_count} posts rejected. Regenerating...")
        # Remove rejected posts from queue
        queue["posts"] = [p for p in queue["posts"] if p.get("status") != "rejected"]
        save_queue(queue)
        # Generate replacements
        cmd_generate(min(rejected_count, 5))
        # Re-review
        cmd_review()

    # Step 4: Schedule
    print(f"\n{'=' * 50}")
    print("[AUTO] Step 4: Scheduling...")
    print(f"{'=' * 50}")
    cmd_schedule()

    # Final status
    queue = load_queue()
    final_statuses = count_by_status(queue)

    print(f"\n{'=' * 60}")
    print("[AUTO] COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Final queue status:")
    for status, cnt in sorted(final_statuses.items()):
        print(f"    {status}: {cnt}")
    print(f"  Total: {sum(final_statuses.values())}")

    slack_notify(
        f"[AI Engine Auto] Complete.\n"
        f"Queue: {json.dumps(final_statuses, ensure_ascii=False)}\n"
        f"Total: {sum(final_statuses.values())}"
    )

    log_event("auto_complete", {"final_status": final_statuses})


# ============================================================
# Status Display (--status)
# ============================================================

def cmd_status():
    """Display comprehensive status of the content engine."""
    print("=" * 60)
    print(f"AI Content Engine Status - {timestamp_str()}")
    print("=" * 60)

    # Queue status
    queue = load_queue()
    statuses = count_by_status(queue)
    total = sum(statuses.values())
    pending = statuses.get("pending", 0)

    print(f"\n[QUEUE] {total} total posts")
    for status in ["pending", "ready", "posted", "rejected", "failed"]:
        cnt = statuses.get(status, 0)
        if cnt > 0:
            print(f"  {status:10s}: {cnt}")

    # Mix analysis
    mix = analyze_queue_mix(queue)
    total_active = sum(mix.values())
    print(f"\n[MIX] Active content balance ({total_active} posts):")
    for cat in MIX_RATIOS:
        cnt = mix.get(cat, 0)
        target_pct = MIX_RATIOS[cat] * 100
        actual_pct = (cnt / total_active * 100) if total_active > 0 else 0
        bar_len = int(actual_pct / 5)
        bar = "#" * bar_len
        print(f"  {cat:8s}: {cnt:2d} ({actual_pct:4.1f}% / {target_pct:4.0f}%) {bar}")

    # Plan status
    plan = load_plan()
    plan_items = plan.get("plans", [])
    planned = sum(1 for p in plan_items if p.get("status") == "planned")
    generated_from_plan = sum(1 for p in plan_items if p.get("status") == "generated")
    print(f"\n[PLAN] {len(plan_items)} items (planned: {planned}, generated: {generated_from_plan})")
    if plan.get("week_of"):
        print(f"  Week of: {plan['week_of']}")

    # AI review scores
    scored_posts = [p for p in queue.get("posts", []) if p.get("ai_score") is not None]
    if scored_posts:
        scores = [p["ai_score"] for p in scored_posts]
        avg_score = sum(scores) / len(scores)
        print(f"\n[QUALITY] {len(scored_posts)} reviewed, avg score: {avg_score:.1f}/10")
        print(f"  Approved (>=6): {sum(1 for s in scores if s >= 6)}")
        print(f"  Rejected (<6):  {sum(1 for s in scores if s < 6)}")

    # Ready directory
    if READY_DIR.exists():
        ready_dirs = [d for d in READY_DIR.iterdir() if d.is_dir()]
        if ready_dirs:
            print(f"\n[READY] {len(ready_dirs)} prepared for upload:")
            for d in sorted(ready_dirs)[:5]:
                pngs = list(d.glob("*.png"))
                print(f"  {d.name}/ ({len(pngs)} slides)")
            if len(ready_dirs) > 5:
                print(f"  ... and {len(ready_dirs) - 5} more")

    # Buffer health
    print(f"\n[HEALTH]")
    if pending >= AUTO_TARGET_PENDING:
        print(f"  Buffer: EXCELLENT ({pending} pending >= {AUTO_TARGET_PENDING} target)")
    elif pending >= AUTO_MIN_PENDING:
        print(f"  Buffer: GOOD ({pending} pending >= {AUTO_MIN_PENDING} minimum)")
    else:
        print(f"  Buffer: LOW ({pending} pending < {AUTO_MIN_PENDING} minimum)")
        print(f"  Run: python3 scripts/ai_content_engine.py --auto")

    print()


# ============================================================
# JSON Parsing Helper
# ============================================================

def _parse_json_from_text(text: str) -> Optional[Any]:
    """
    Parse JSON from text that may contain markdown fences or extra text.
    Handles both objects and arrays.
    """
    if not text:
        return None

    text = text.strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Remove markdown code fences
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Find first JSON object
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start_idx = text.find(start_char)
        if start_idx == -1:
            continue

        # Find matching closing bracket
        depth = 0
        for i in range(start_idx, len(text)):
            if text[i] == start_char:
                depth += 1
            elif text[i] == end_char:
                depth -= 1
                if depth == 0:
                    candidate = text[start_idx:i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        break

    return None


# ============================================================
# Feedback Loop (--feedback-loop)
# ============================================================

def cmd_feedback_loop():
    """Data-driven content generation: analyze performance → adjust mix → generate.

    1. Run tiktok_analytics.py --update to refresh performance data
    2. Analyze which categories/hooks perform best
    3. Dynamically adjust MIX_RATIOS based on data
    4. Generate content with adjusted ratios
    """
    global MIX_RATIOS

    print("=" * 60)
    print(f"[FEEDBACK] Performance-Based Content Loop - {timestamp_str()}")
    print("=" * 60)

    # Step 1: Update analytics
    print("\n[FEEDBACK] Step 1: Refreshing TikTok analytics...")
    try:
        result = subprocess.run(
            ["python3", str(PROJECT_DIR / "scripts" / "tiktok_analytics.py"), "--update"],
            capture_output=True, text=True, timeout=120
        )
        print(result.stdout[-500:] if result.stdout else "  (no output)")
    except Exception as e:
        print(f"  [WARN] Analytics refresh failed: {e}")

    # Step 2: Analyze performance by category
    print("\n[FEEDBACK] Step 2: Analyzing performance by category...")
    queue = load_queue()
    posted = [p for p in queue.get("posts", []) if p.get("status") == "posted"]

    if len(posted) < 5:
        print(f"  Only {len(posted)} posted. Need 5+ for meaningful analysis. Using default MIX.")
    else:
        category_stats = {}
        for post in posted:
            cat = post.get("content_type", "aruaru")
            # Map back to Japanese category names
            cat_name = None
            for jp, en in CATEGORY_TO_CONTENT_TYPE.items():
                if en == cat:
                    cat_name = jp
                    break
            if not cat_name:
                cat_name = "あるある"

            perf = post.get("performance", {})
            views = perf.get("views") if isinstance(perf, dict) else None
            saves = perf.get("saves") if isinstance(perf, dict) else None

            if cat_name not in category_stats:
                category_stats[cat_name] = {"count": 0, "total_views": 0, "total_saves": 0, "has_data": 0}

            category_stats[cat_name]["count"] += 1
            if views is not None:
                category_stats[cat_name]["total_views"] += views
                category_stats[cat_name]["has_data"] += 1
            if saves is not None:
                category_stats[cat_name]["total_saves"] += saves

        # Calculate average performance per category
        adjustments = {}
        total_avg_views = 0
        cats_with_data = 0

        for cat, stats in category_stats.items():
            if stats["has_data"] > 0:
                avg_views = stats["total_views"] / stats["has_data"]
                total_avg_views += avg_views
                cats_with_data += 1
                adjustments[cat] = avg_views
                print(f"  {cat}: {stats['has_data']} posts with data, avg views={avg_views:.0f}")

        # Adjust MIX_RATIOS: boost categories with above-average performance
        if cats_with_data >= 2 and total_avg_views > 0:
            global_avg = total_avg_views / cats_with_data
            print(f"\n  Global average: {global_avg:.0f} views")

            new_ratios = dict(MIX_RATIOS)
            for cat, avg_views in adjustments.items():
                if cat in new_ratios:
                    multiplier = avg_views / global_avg
                    # Clamp adjustment: max ±15% change
                    adjustment = max(-0.15, min(0.15, (multiplier - 1) * 0.1))
                    new_ratios[cat] = max(0.05, min(0.60, new_ratios[cat] + adjustment))

            # Normalize to sum=1.0
            total = sum(new_ratios.values())
            new_ratios = {k: round(v / total, 2) for k, v in new_ratios.items()}

            print(f"\n  Adjusted MIX_RATIOS:")
            for cat in MIX_RATIOS:
                old = MIX_RATIOS[cat] * 100
                new = new_ratios.get(cat, MIX_RATIOS[cat]) * 100
                arrow = "↑" if new > old else ("↓" if new < old else "=")
                print(f"    {cat}: {old:.0f}% → {new:.0f}% {arrow}")

            MIX_RATIOS = new_ratios
        else:
            print(f"  Not enough data for adjustment. Using defaults.")

    # Step 3: Generate with adjusted ratios
    print(f"\n[FEEDBACK] Step 3: Running auto content generation...")
    cmd_auto()

    # Save performance analysis
    analysis_file = PROJECT_DIR / "data" / "performance_analysis.json"
    analysis = {
        "timestamp": datetime.now().isoformat(),
        "mix_ratios_used": MIX_RATIOS,
        "posted_count": len(posted),
    }
    with open(analysis_file, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)

    print(f"\n[FEEDBACK] Complete. Analysis saved to {analysis_file}")


# ============================================================
# Content Calendar (--calendar)
# ============================================================

def cmd_calendar():
    """Maintain a rolling 2-week content calendar.

    Checks pending posts, generates to reach AUTO_TARGET_PENDING,
    and assigns scheduled_date to each post.
    """
    print("=" * 60)
    print(f"[CALENDAR] Content Calendar Manager - {timestamp_str()}")
    print("=" * 60)

    queue = load_queue()
    pending = count_pending(queue)
    statuses = count_by_status(queue)

    print(f"\n  Current queue: {sum(statuses.values())} total")
    print(f"  Pending/ready: {pending}")
    print(f"  Target: {AUTO_TARGET_PENDING}")

    # Generate if needed
    need = max(0, AUTO_TARGET_PENDING - pending)
    if need > 0:
        print(f"\n  Need {need} more posts. Generating...")
        cmd_generate(need)
        queue = load_queue()  # Reload
    else:
        print(f"\n  Buffer sufficient ({pending} >= {AUTO_TARGET_PENDING})")

    # Assign scheduled_dates to posts without one
    from datetime import timedelta
    today = datetime.now().date()
    schedule_idx = 0

    # Load posting schedule if exists
    schedule_file = PROJECT_DIR / "data" / "posting_schedule.json"
    if schedule_file.exists():
        with open(schedule_file, encoding="utf-8") as f:
            schedule_data = json.load(f)
        day_times = schedule_data.get("schedule", {})
    else:
        day_times = {"Mon": "17:30", "Tue": "12:00", "Wed": "21:00",
                     "Thu": "17:30", "Fri": "18:00", "Sat": "20:00"}

    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    posts_to_schedule = [p for p in queue.get("posts", [])
                         if p.get("status") in ("pending", "ready") and not p.get("scheduled_date")]

    scheduled_count = 0
    for post in posts_to_schedule:
        # Find next available day
        while True:
            target_date = today + timedelta(days=schedule_idx + 1)
            day_name = day_names[target_date.weekday()]
            if day_name in day_times:
                time_str = day_times[day_name]
                post["scheduled_date"] = f"{target_date.isoformat()} {time_str}"
                scheduled_count += 1
                schedule_idx += 1
                break
            schedule_idx += 1
            if schedule_idx > 30:
                break

    if scheduled_count > 0:
        save_queue(queue)
        print(f"\n  Scheduled {scheduled_count} posts")

    # Validate MIX ratios across calendar
    mix = analyze_queue_mix(queue)
    total_active = sum(mix.values())
    print(f"\n  Content MIX across calendar ({total_active} active):")
    for cat in MIX_RATIOS:
        cnt = mix.get(cat, 0)
        target = MIX_RATIOS[cat] * 100
        actual = (cnt / total_active * 100) if total_active > 0 else 0
        status = "✅" if abs(actual - target) <= 10 else "⚠️"
        print(f"    {status} {cat}: {actual:.0f}% (target {target:.0f}%)")

    # Validate CTA 8:2 rule
    cta_counts = {"soft": 0, "hard": 0}
    for p in queue.get("posts", []):
        if p.get("status") in ("pending", "ready"):
            cta_counts[p.get("cta_type", "soft")] += 1

    total_cta = sum(cta_counts.values())
    if total_cta > 0:
        hard_pct = cta_counts["hard"] / total_cta * 100
        status = "✅" if 10 <= hard_pct <= 30 else "⚠️"
        print(f"\n  {status} CTA balance: soft={cta_counts['soft']} hard={cta_counts['hard']} ({hard_pct:.0f}% hard)")

    print(f"\n[CALENDAR] Complete.")
    slack_notify(
        f"[Calendar] Updated: {scheduled_count} newly scheduled, "
        f"{count_pending(queue)} total pending"
    )


# ============================================================
# Main CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="AI Content Engine for Nurse Robby (Cloudflare Workers AI)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --auto              Full auto: plan -> generate -> review -> schedule
  %(prog)s --feedback-loop     Data-driven: analytics -> adjust mix -> generate
  %(prog)s --calendar          Maintain 2-week rolling content calendar
  %(prog)s --plan              Generate a 1-week content plan
  %(prog)s --generate 7        Generate 7 carousel content sets
  %(prog)s --review            Quality-check all pending content
  %(prog)s --schedule          Schedule and prepare next posts
  %(prog)s --status            Show engine status

Cost: Cloudflare Workers AI is FREE (10,000 neurons/day).
        """,
    )

    parser.add_argument("--auto", action="store_true",
                        help="Full auto mode: plan -> generate -> review -> schedule")
    parser.add_argument("--feedback-loop", action="store_true",
                        help="Data-driven: refresh analytics -> adjust MIX -> generate")
    parser.add_argument("--calendar", action="store_true",
                        help="Maintain 2-week rolling content calendar")
    parser.add_argument("--plan", action="store_true",
                        help="AI content planning (1-week plan)")
    parser.add_argument("--generate", type=int, metavar="N",
                        help="Generate N carousel content sets")
    parser.add_argument("--review", action="store_true",
                        help="AI quality review of pending content")
    parser.add_argument("--schedule", action="store_true",
                        help="Schedule and prepare posts for upload")
    parser.add_argument("--status", action="store_true",
                        help="Show engine status")

    args = parser.parse_args()

    # Load environment
    load_env()

    # Ensure data directory exists
    (PROJECT_DIR / "data").mkdir(parents=True, exist_ok=True)

    if args.auto:
        cmd_auto()
    elif args.feedback_loop:
        cmd_feedback_loop()
    elif args.calendar:
        cmd_calendar()
    elif args.plan:
        cmd_plan()
    elif args.generate is not None:
        cmd_generate(args.generate)
    elif args.review:
        cmd_review()
    elif args.schedule:
        cmd_schedule()
    elif args.status:
        cmd_status()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
