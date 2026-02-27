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

# Content stock ideas for planning context (from CLAUDE.md)
# 2026年最適化: 超具体的なシーン描写でフック強度を上げる
# 2026-02-27 改定: 地域ネタカテゴリ追加、紹介カテゴリ削除（100人超えるまで）
CONTENT_STOCK_HINTS = {
    "あるある": [
        "師長に「辞めたい」3ヶ月言えなかった→AIに退職の切り出し方を聞いたら台本が完璧だった",
        "夜勤明け16時間後の顔をAIに年齢判定させたら+10歳→夜勤前と比較して絶望",
        "夜勤中ナースコール3連続+急変対応をAIに同時処理させたら処理落ちした",
        "先輩の「それ昨日も言ったよね？」をAIに100回言ったら「何度でもどうぞ」って返された",
        "看護記録2時間分をAIに書かせたら形式完璧→でも「患者さんの表情が和らいだ」は書けなかった",
        "申し送り15分をAIに30秒に要約させたら「バイタル正常」しか残らなかった",
        "患者さんの「大丈夫です（全然大丈夫じゃない顔）」をAIに本音翻訳させた",
        "夜勤中の仮眠を科学的に最適化→AIの回答「仮眠取れる前提が間違い」",
        "プリセプターに怒られた新人がAIに愚痴ったら「あなたは悪くない」って全肯定された",
        "休憩中にコンビニ行く時間をAIに計算させたら「往復で休憩終わります」",
    ],
    "給与": [
        "神奈川の看護師年収、横浜と県西部で60万差→家賃込みで再計算したら意外な結果",
        "夜勤手当の施設別相場→大学病院と療養型で1回4,000円差。年間20万の差",
        "5年目看護師の手取り24万を全国平均と比較→実は平均以下だった都道府県ランキング",
        "転職で年収50万上がった看護師の共通点3つをAIに分析させた",
        "手数料30% vs 10%→病院の負担が60万も違う。それが採用のされやすさに直結する話",
        "ボーナスカット3年連続の病院→AIに辞めるべきか計算させたら衝撃の損失額が出た",
    ],
    "地域ネタ": [
        "小田原の看護師あるある→車通勤が常識、箱根の坂道で冬は毎朝ドキドキ",
        "神奈川は看護師不足ワースト3位→県西部の人口あたり看護師数をAIに調べさせたら衝撃",
        "県西部なら通勤10分→横浜で通勤1時間の生活と比較したら自由時間が年間365時間違った",
        "横浜vs県西部の手取り比較→年収60万差でも家賃と通勤費で逆転する計算をAIにさせた",
        "小田原で車通勤の看護師が横浜に転職→満員電車に耐えられず3ヶ月で戻ってきた話",
        "平塚・秦野の看護師が「都内に通うのやめた理由」をAIにまとめさせた",
        "湘南エリアの看護師、海が近い生活を手放せない→AIに「幸福度と通勤時間の関係」を聞いた",
    ],
    "転職": [
        "同じ5年目なのに年収100万差→AIにデータ分析させたら「施設選びが全て」だった",
        "「転職したいけど怖い」を夜中3時にAIに相談→「怖いのは情報不足」でハッとした",
        "経験年数別の市場価値をAIに算出→4-7年目が最も価値高い。8年超えると管理職前提で選択肢激減",
        "面接の「退職理由」をAIに添削→ネガティブな本音が前向きな志望動機に変わった",
        "転職エージェントの手数料30%→1人採用に80-120万。病院が「すぐ辞めないで」と言う理由これ",
        "「3年は続けなさい」と親に言われた→AIにデータで反論させたら親が黙った",
        "転職サイト3社に登録したら電話17件→AIに対処法を聞いた",
    ],
    "トレンド": [
        "お母さんに「看護師辞めたい」→まさかのAIで論破「辞めたいのは看護師？今の職場？」",
        "彼氏の「夜勤って寝てるだけでしょ」→AIに夜勤の中身を説明させたら彼氏が泣いた",
        "友達の結婚式に夜勤明けで参加→AIに「夜勤明けの身体への影響」を説明させたら友達がドン引き",
        "合コンで「看護師です」→「注射上手そう」って毎回言われる件をAIに統計取らせた",
        "看護学生の実習レポートをAIに添削させたら赤入れ200箇所",
    ],
}

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
    SYSTEM_PROMPT = """あなたはナースロビー（NURSE ROBBY）のSNSコンテンツクリエイターAIです。
TikTok/Instagramカルーセル（5枚スライドショー）の台本を生成します。

## 3要素ルール（毎投稿で必須）
すべての投稿に「AI × 看護師 × 地域」の3要素を含めること。
地域名は以下から毎回1つ以上を必ず台本またはキャプションに含める:
  神奈川県 / 小田原 / 県西部 / 湘南 / 平塚 / 秦野 / 南足柄

## ペルソナ（超具体的にイメージしろ）
ターゲットは「ミサキ」（28歳中堅看護師）:
- 経験5-8年、急性期病院で夜勤あり。リーダー業務も任される立場
- 今月も3連続夜勤のあとに日勤。体力的に限界を感じ始めている
- 先輩の「前にも言ったよね」がトラウマ。でも後輩には同じこと言いたくない
- 手取り24万。同期の一般企業の友達は32万。この差に毎月モヤモヤ
- 転職サイトは怖い（しつこい電話のイメージ）。でもLINEなら相談してみたい
- TikTok、Instagramを帰りの電車（17:30頃）と寝る前（22:00頃）に見る
- 神奈川県西部在住。小田原から横浜の病院まで通勤1時間

## フック公式（7パターンをローテーション）
1枚目のフックは「10文字以内の疑問文か未完了文」にすること。
1. 質問型: 「県西部の手取り？」「小田原あるある」
2. 対立型: 「横浜vs県西部」「師長に見せたら」
3. 数字型: 「年収60万の差」「通勤10分の真実」
4. 告白型: 「転職が怖い理由」
5. 衝撃型: 「知らないと損」
6. 共感型: 「夜勤明けの朝」
7. 比較型: 「都内vs地元」

## コンテンツ公式
[看護師の超具体的な場面] + [AIにやらせてみた] + [地域要素] → [予想外の結果・感情が動く展開]
※「夜勤あるある」ではなく「小田原の夜勤明け3連続ナースコールあるある」レベルの具体性+地域性

## スライド構成（5枚 — Hook + Content x3 + CTA）
1枚目(Hook): フック（10文字以内の疑問文か未完了文。3秒で止める）
2枚目(Content1): 共感（「あるある」で「自分のことだ」と思わせる。具体的シーン描写+地域要素）
3枚目(Content2): 展開+深掘り（AIに聞いた/やらせた。データや事実。「知らなかった」を生む）
4枚目(Content3): クライマックス（衝撃の結果。感情のピーク）
5枚目(CTA): オチ+CTA（余韻を残す。次のアクションへ自然に誘導）

## キャプション構造（2026年TikTok最適化）
- 1行目: 感情フック（質問形式が最も効果的。改行で分離）
- 2-3行目: ストーリーの核心（共感ポイント。改行で区切る。地域名を含める）
- 最終行: CTA（自然に。押し売り厳禁）
- 改行を積極的に使え（視認性が大幅に上がる）
- 200文字以内

## ハッシュタグルール
- 4個構成: 地域タグ1個 + ニッチタグ1個 + 中規模タグ1個 + 一般タグ1個
- 禁止タグ: #AI, #fyp, #ナースロビー（飽和タグ・宣伝感回避）
- 地域タグ: #神奈川看護師, #小田原, #平塚, #秦野, #湘南ナース, #県西部 からローテーション
- ニッチタグ: #夜勤あるある, #病棟あるある, #看護記録, #手取り公開, #転職理由, #師長
- 中規模タグ: #看護師あるある, #看護師転職, #看護師の日常, #ナースの本音
- 一般タグ: #看護師, #ナース, #転職

## 法的制約（絶対遵守）
- すべて架空設定で作成（※このストーリーはフィクションです）
- 患者の個人情報に触れない
- 実在施設の批判をしない
- ハッシュタグ4個（厳守。スパム判定回避）

## 品質基準
- 1枚目フックは10文字以内の疑問文か未完了文。パターンインタラプト必須
- 毎投稿に地域名を1つ以上含めること（台本 or キャプション）
- キャプション1行目は質問形式が理想
- ミサキが帰りの電車でスクロールを止めるか？を常に問え
- 「夜勤」「申し送り」「ナースコール」等の看護師用語を自然に使え
- 押し売り感は厳禁。共感→信頼→導線の順
- 完走率70%以上を狙え：最後まで読みたくなる展開設計"""


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

## フック7パターン（必ずローテーションで使え。同じパターン連続禁止）
1. 質問型: 「○○な人、正直に手挙げて」
2. 対立型: 「師長に○○見せたら黙った」
3. 数字型: 「看護師○年目、年収○○万の差」
4. 告白型: 「正直に言う。○○」
5. 衝撃型: 「これ知らない看護師、損してる」
6. 共感型: 「わかる人だけわかって。○○」
7. 比較型: 「○○ vs ○○」

## ルール
- フックは20文字以内。「ロビー」の名前を含める
- 超具体的に書け（「夜勤あるある」ではなく「夜勤明け仮眠0分あるある」）
- ペルソナ「ミサキ（28歳看護師、夜勤あり、手取り24万）」が電車で止まるフック
- hintを参考にしつつ、新しいアイデアも可
- 同じフックパターンの連続を避ける（質問→対立→数字→共感のようにローテーション）
- 「パターンインタラプト」を意識（予想を裏切る言葉選び）

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

    prompt = f"""TikTokカルーセル投稿の台本を1つ生成してください。

## 指定
- カテゴリ: {category}
- CTA種類: {cta_type}
- {cta_instruction}
{hint_text}{template_context}{robby_context}

## 構成（5枚: Hook + Content x3 + CTA）
- hook: 1枚目のフック文（10文字以内の疑問文か未完了文。「ロビー」の名前を含める。スクロール停止力が命）
- slides: 5枚分のテキスト（配列）
  - slides[0]: 1枚目 Hook（hookと同じでOK。10文字以内。パターンインタラプト=予想を裏切る一言）
  - slides[1]: 2枚目 Content1（共感+地域要素。「あるある」で「自分のことだ」と思わせる。超具体的なシーン描写）
  - slides[2]: 3枚目 Content2（展開+深掘り。AIに聞いた/やらせた。データや事実。「知らなかった…」を生む）
  - slides[3]: 4枚目 Content3（クライマックス。衝撃の結果。感情のピーク。一番シェアしたくなる瞬間）
  - slides[4]: 5枚目 CTA（オチ+CTA。余韻+次のアクション。ロビーのまとめ）
- caption: SNSキャプション。以下の構造を厳守:
  1行目: 感情フック（質問形式推奨。例:「県西部の看護師、通勤何分？」）
  （改行）
  2-3行目: 核心の共感ポイント（短文で区切る。地域名を含める）
  （改行）
  最終行: CTA（自然に。保存/フォロー/コメント誘導）
  ※改行は \\n で表現。合計200文字以内。
- hashtags: ハッシュタグ4個（地域1+ニッチ1+中規模1+一般1）
  禁止: #AI, #fyp, #ナースロビー
- reveal_text: 5枚目の衝撃テキスト（短く印象的に。ロビーのまとめ）
- reveal_number: 5枚目に表示する数字（あれば。例: "+10歳", "100万円"）

## フック7パターン（10文字以内でローテーション）
1. 質問型: 「県西部の手取り？」
2. 対立型: 「師長に見せたら」
3. 数字型: 「年収60万の差」
4. 告白型: 「転職が怖い理由」
5. 衝撃型: 「知らないと損」
6. 共感型: 「夜勤明けの朝」
7. 比較型: 「都内vs地元」

## 超具体性+地域性の例（この粒度で書け）
BAD: 「夜勤あるある」
GOOD: 「小田原の夜勤明け、ナースコール3連続で仮眠0分」
BAD: 「先輩が怖い」
GOOD: 「県西部の病院で『それ昨日も言ったよね？』って言われた時の背筋」
BAD: 「給料が安い」
GOOD: 「横浜vs県西部、手取り比較。家賃込みで逆転する計算」

## 重要
- 1枚目フックは絶対10文字以内の疑問文か未完了文。「ロビー」の名前入り必須。
- 毎投稿に地域名を1つ以上含めること（台本 or キャプション）
- 看護師が「わかる！」となる超具体的なあるある（抽象的なのは禁止）
- ロビー君のキャラクターで一貫して語る（一人称「ロビー」、タメ口）
- 架空のストーリーであること
- キャプション1行目は必ず質問形式か感情フック。改行(\\n)で区切る
- キャプションは200文字以内

## 出力形式
JSON形式のみ出力。マークダウン記法、コードフェンス、説明文は一切不要。JSONだけ返してください。

{{
  "id": "{content_id}",
  "hook": "10文字以内のフック",
  "slides": [
    "1枚目: Hook（10文字以内）",
    "2枚目: Content1。共感+地域要素。超具体的な場面描写",
    "3枚目: Content2。展開+深掘り。AIに聞いた結果+データ",
    "4枚目: Content3。クライマックス。衝撃の結果",
    "5枚目: CTA。オチ+次のアクション"
  ],
  "caption": "1行目フック（質問形式+地域名）\\n\\n共感ポイント。\\n核心の一言。\\n\\nCTA",
  "hashtags": ["#地域タグ", "#ニッチタグ", "#中規模タグ", "#一般タグ"],
  "reveal_text": "リビールテキスト",
  "reveal_number": "数字（任意）",
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
# Main CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="AI Content Engine for Nurse Robby (Cloudflare Workers AI)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --auto              Full auto: plan -> generate -> review -> schedule
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
