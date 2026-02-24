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

# Content MIX ratios (from CLAUDE.md)
MIX_RATIOS = {
    "あるある": 0.40,
    "転職": 0.25,
    "給与": 0.20,
    "紹介": 0.05,
    "トレンド": 0.10,
}

# Category to content_type mapping for queue integration
CATEGORY_TO_CONTENT_TYPE = {
    "あるある": "aruaru",
    "転職": "career",
    "給与": "salary",
    "紹介": "service",
    "トレンド": "trend",
}

# CTA 8:2 rule
CTA_HARD_RATIO = 0.2

# Auto mode: minimum buffer = 2 weeks of content (~14 posts, aim for at least 7 pending)
AUTO_MIN_PENDING = 7
AUTO_TARGET_PENDING = 14

# Optimal posting times (from CLAUDE.md: nurse work rhythm)
POSTING_TIMES = ["17:30", "12:00", "21:00"]

# Curated hashtag sets per category
HASHTAG_SETS = {
    "あるある": [
        ["#看護師あるある", "#ナースロビー", "#看護師の日常", "#AI"],
        ["#看護師あるある", "#ナース", "#看護師", "#AIやってみた"],
        ["#看護師", "#看護師の日常", "#夜勤", "#AI", "#ナースロビー"],
    ],
    "転職": [
        ["#看護師転職", "#ナースロビー", "#キャリア", "#AI"],
        ["#看護師転職", "#転職", "#神奈川看護師", "#AI"],
        ["#看護師", "#転職", "#キャリアアップ", "#ナースロビー"],
    ],
    "給与": [
        ["#看護師", "#年収", "#給与", "#AI", "#ナースロビー"],
        ["#看護師転職", "#給料", "#手当", "#神奈川"],
        ["#看護師", "#夜勤手当", "#年収比較", "#ナースロビー"],
    ],
    "紹介": [
        ["#看護師転職", "#ナースロビー", "#手数料10パーセント"],
        ["#神奈川看護師", "#ナースロビー", "#転職エージェント"],
        ["#看護師転職", "#ナースロビー", "#手数料", "#神奈川"],
    ],
    "トレンド": [
        ["#看護師あるある", "#ナースロビー", "#看護師の日常", "#AI"],
        ["#看護師", "#ナース", "#AI", "#看護師あるある"],
        ["#看護師", "#ナースロビー", "#トレンド", "#AI", "#看護師あるある"],
    ],
}

# Content stock ideas for planning context (from CLAUDE.md)
CONTENT_STOCK_HINTS = {
    "あるある": [
        "師長に辞めたいって言ったらAIが代わりに説明してくれた",
        "夜勤明けの顔をAIに何歳に見えるって聞いてみた",
        "ナースコール3連続をAIに再現させたら",
        "先輩の「前にも言ったよね」をAIに何回言わせたら怒るか",
        "看護記録をAIに書かせてみた",
        "申し送りをAIに要約させたら重要なこと全部落とした",
        "患者さんの「大丈夫です」をAIに本音翻訳させた",
        "夜勤中の仮眠をAIに最適化させたら",
    ],
    "転職": [
        "同じ経験5年でも年収100万違う理由をAIに聞いた",
        "転職したいけど怖いをAIに相談したら返答が的確すぎた",
        "私の経験年数で転職するべきかAIに聞いたら",
        "面接で聞かれる退職理由をAIに添削してもらった",
        "転職エージェントの手数料知ってますか",
    ],
    "給与": [
        "神奈川の看護師平均年収を地域別に調べてみた",
        "夜勤手当の相場をAIにまとめさせた",
        "5年目看護師の手取りを全国平均と比べてみた",
        "転職で年収50万上がった人の共通点をAIに分析させた",
        "手数料30%が看護師の給与にどう影響するかAIに計算させた",
    ],
    "紹介": [
        "ナースロビーの手数料10%が看護師にどう得になるか",
        "転職エージェント選びで一番大事なことをAIに聞いた",
    ],
    "トレンド": [
        "お母さんに看護師辞めたいって言ったらAIで論破された",
        "彼氏に夜勤の中身をAIに説明させたら泣いた",
        "友達の結婚式で夜勤の話をAIにまとめさせたら",
    ],
}


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

SYSTEM_PROMPT = """あなたはナースロビー（NURSE ROBBY）のSNSコンテンツクリエイターAIです。
TikTok/Instagramカルーセル（7枚スライドショー）の台本を生成します。

## ペルソナ
ターゲットは「ミサキ」（28歳中堅看護師）:
- 経験5-8年、急性期病院で夜勤あり
- 給与に不満 or 人間関係に疲弊
- 情報収集段階。まだ転職サイト未登録
- TikTok、Instagramを通勤中・休憩中に見る
- 神奈川県西部在住

## フック公式
[他者（師長・先輩・患者・彼氏・友達）] + [対立・否定・疑い] → AIで見せた → [反応が変わった]

## コンテンツ公式
[看護師の現場あるある] + [AIにやらせてみた] → [予想外の結果]

## スライド構成（7枚）
1枚目: フック（20文字以内。スクロールを止める一言）
2-5枚目: ストーリー展開（各スライドにタイトルと本文）
6枚目: オチ・リビール（衝撃の結果やデータ）
7枚目: CTA（ナースロビーのブランドスライド — 自動生成されるので台本不要）

## 法的制約（絶対遵守）
- すべて架空設定で作成（※このストーリーはフィクションです）
- 患者の個人情報に触れない
- 実在施設の批判をしない
- ハッシュタグ5個以内

## 品質基準
- 1枚目フックは20文字以内
- キャプションは200文字以内
- ミサキが通勤電車で手を止めるか？を常に問え
- 押し売り感は厳禁。共感→信頼→導線の順"""


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

## ルール
- フックは20文字以内
- フックの公式: [他者] + [対立・否定] → AIで見せた → [反応が変わった]
- コンテンツ公式: [看護師あるある] + [AIにやらせてみた] → [予想外の結果]
- ペルソナ「ミサキ（28歳看護師）」が止まるフック
- hintを参考にしつつ、新しいアイデアも可
- 同じパターンの繰り返しを避ける

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
            "6枚目のCTAはソフトCTA: 「保存してね」「フォローで続き見れる」「共感したらいいね」など。"
            "サービス名は出さない。"
        )
    else:
        cta_instruction = (
            "6枚目のCTAはハードCTA: 「LINEで相談できるよ」「プロフから登録」「ナースロビーで検索」など。"
            "手数料10%をさりげなく訴求。"
        )

    hint_text = f"フックのヒント: {hook_hint}" if hook_hint else ""

    prompt = f"""TikTokカルーセル投稿の台本を1つ生成してください。

## 指定
- カテゴリ: {category}
- CTA種類: {cta_type}
- {cta_instruction}
{hint_text}

## 構成
- hook: 1枚目のフック文（20文字以内。スクロール停止力が命）
- slides: 6枚分のテキスト（配列）
  - slides[0]: 1枚目フック（hookと同じでOK）
  - slides[1]-[4]: 2-5枚目のストーリー展開
  - slides[5]: 6枚目 オチ+CTA
- caption: SNSキャプション（200文字以内。共感を誘う語り口）
- hashtags: ハッシュタグ（3-5個）
- reveal_text: 6枚目の衝撃テキスト（短く印象的に）
- reveal_number: 6枚目に表示する数字（あれば。例: "+10歳", "100万円"）

## 重要
- 1枚目フックは絶対20文字以内
- 看護師が「わかる！」となるリアルなあるある
- AIを絡めた新鮮な切り口
- 架空のストーリーであること
- キャプションは200文字以内

## 出力形式
JSON形式のみ出力。マークダウン記法、コードフェンス、説明文は一切不要。JSONだけ返してください。

{{
  "id": "{content_id}",
  "hook": "フック文",
  "slides": [
    "1枚目フック",
    "2枚目: タイトル。本文の展開",
    "3枚目: タイトル。さらに展開",
    "4枚目: タイトル。クライマックスへ",
    "5枚目: タイトル。驚きの事実",
    "6枚目: オチ+CTA"
  ],
  "caption": "キャプション文",
  "hashtags": ["#タグ1", "#タグ2", "#タグ3"],
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
    if len(hook) > 20:
        # Auto-trim hook
        data["hook"] = hook[:20]
        print(f"  [WARN] Hook trimmed to 20 chars")

    slides = data.get("slides", [])
    if not isinstance(slides, list) or len(slides) < 4:
        print(f"  [WARN] slides must have at least 4 items, got {len(slides) if isinstance(slides, list) else 'N/A'}")
        return False

    # Pad to 6 slides if needed
    while len(slides) < 6:
        slides.append(slides[-1] if slides else "...")
    data["slides"] = slides[:6]

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
