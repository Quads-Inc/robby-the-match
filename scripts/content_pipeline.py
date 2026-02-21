#!/usr/bin/env python3
"""
ROBBY THE MATCH — 自律型コンテンツ生成パイプライン

Usage:
  python3 scripts/content_pipeline.py --auto       # pending < 7 なら自動補充
  python3 scripts/content_pipeline.py --status     # キュー・ストック状況表示
  python3 scripts/content_pipeline.py --force 3    # 強制的に3本生成
"""

import argparse
import csv
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# ============================================================
# Constants
# ============================================================

PROJECT_DIR = Path(__file__).parent.parent

QUEUE_PATH = PROJECT_DIR / "data" / "posting_queue.json"
AGENT_STATE_PATH = PROJECT_DIR / "data" / "agent_state.json"
STOCK_CSV_PATH = PROJECT_DIR / "content" / "stock.csv"
PROMPT_TEMPLATE_PATH = PROJECT_DIR / "content" / "templates" / "prompt_template.md"
GENERATED_DIR = PROJECT_DIR / "content" / "generated"

# Target MIX ratios
MIX_RATIOS = {
    "あるある": 0.40,
    "転職": 0.25,
    "給与": 0.20,
    "紹介": 0.05,
    "トレンド": 0.10,
}

# Category prefix mapping (for ID generation: A=あるある, B=転職, etc.)
CATEGORY_PREFIX = {
    "あるある": "A",
    "転職": "B",
    "給与": "C",
    "紹介": "D",
    "トレンド": "T",
}

# Category -> base_image mapping
CATEGORY_BASE_IMAGE = {
    "あるある": "base_nurse_station.png",
    "転職": "base_ai_chat.png",
    "給与": "base_ai_chat.png",
    "紹介": "base_nurse_station.png",
    "トレンド": "base_breakroom.png",
}

# CTA 8:2 rule
CTA_SOFT_RATIO = 0.8

# Minimum pending posts threshold for --auto
AUTO_THRESHOLD = 7

# Claude CLI timeout (seconds)
CLAUDE_TIMEOUT = 120


# ============================================================
# Helpers: File I/O
# ============================================================

def load_env():
    """Load .env file from PROJECT_DIR."""
    env_path = PROJECT_DIR / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    os.environ.setdefault(key, value)


def load_queue() -> dict:
    """Read posting_queue.json. Return full structure."""
    if not QUEUE_PATH.exists():
        return {"version": 1, "created": datetime.now().isoformat(), "updated": None, "posts": []}
    with open(QUEUE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_queue(queue: dict):
    """Write posting_queue.json."""
    queue["updated"] = datetime.now().isoformat()
    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)
    print(f"[OK] posting_queue.json 更新完了 ({len(queue['posts'])}件)")


def load_stock() -> List[Dict]:
    """Read stock.csv and return list of dicts."""
    if not STOCK_CSV_PATH.exists():
        return []
    with open(STOCK_CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_stock(rows: List[Dict]):
    """Write stock.csv."""
    if not rows:
        return
    fieldnames = ["id", "category", "hook", "status", "posted_date",
                  "views", "likes", "saves", "comments", "rating"]
    with open(STOCK_CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print(f"[OK] stock.csv 更新完了 ({len(rows)}行)")


def load_agent_memory() -> dict:
    """Read agent_state.json -> agentMemory.content_creator."""
    if not AGENT_STATE_PATH.exists():
        return {}
    with open(AGENT_STATE_PATH, "r", encoding="utf-8") as f:
        state = json.load(f)
    return state.get("agentMemory", {}).get("content_creator", {})


def load_prompt_template() -> str:
    """Read prompt_template.md."""
    if not PROMPT_TEMPLATE_PATH.exists():
        print(f"[WARN] prompt_template.md が見つかりません: {PROMPT_TEMPLATE_PATH}")
        return ""
    with open(PROMPT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        return f.read()


# ============================================================
# Analysis
# ============================================================

def count_pending(queue: dict) -> int:
    """Count posts with status='pending'."""
    return sum(1 for p in queue.get("posts", []) if p.get("status") == "pending")


def get_next_queue_id(queue: dict) -> int:
    """Get next integer ID for posting queue."""
    posts = queue.get("posts", [])
    if not posts:
        return 1
    return max(p.get("id", 0) for p in posts) + 1


def get_next_content_id(stock: List[Dict], category: str) -> str:
    """
    Determine next content ID for a category.
    e.g., if highest existing is A05, returns A06.
    """
    prefix = CATEGORY_PREFIX.get(category, "X")
    max_num = 0
    for row in stock:
        row_id = row.get("id", "")
        if row_id.startswith(prefix):
            try:
                num = int(row_id[len(prefix):])
                max_num = max(max_num, num)
            except ValueError:
                continue
    return f"{prefix}{max_num + 1:02d}"


def analyze_stock_distribution(stock: List[Dict]) -> Dict:
    """Count stock items per category."""
    dist = {cat: 0 for cat in MIX_RATIOS}
    for row in stock:
        cat = row.get("category", "")
        if cat in dist:
            dist[cat] += 1
    return dist


def determine_needs(stock: List[Dict], count: int) -> List[Dict]:
    """
    Determine which categories and CTA types to generate.
    Returns a list of dicts: [{"category": "...", "cta_type": "..."}, ...]
    """
    dist = analyze_stock_distribution(stock)
    total = sum(dist.values()) or 1

    # Calculate deficit per category relative to ideal MIX
    deficits = []
    for cat, ratio in MIX_RATIOS.items():
        current_ratio = dist[cat] / total if total > 0 else 0
        deficit = ratio - current_ratio
        deficits.append((cat, deficit))

    # Sort by deficit descending — categories most underrepresented first
    deficits.sort(key=lambda x: x[1], reverse=True)

    needs = []
    # Assign CTA types with 8:2 rule
    soft_count = max(1, round(count * CTA_SOFT_RATIO))
    hard_count = count - soft_count

    idx = 0
    for i in range(count):
        cat = deficits[idx % len(deficits)][0]
        cta = "soft" if i < soft_count else "hard"
        needs.append({"category": cat, "cta_type": cta})
        idx += 1

    return needs


# ============================================================
# Content Generation
# ============================================================

def build_claude_prompt(
    category: str,
    cta_type: str,
    content_id: str,
    prompt_template: str,
    agent_memory: dict,
    stock_status: str,
) -> str:
    """Build the prompt to send to Claude CLI for generating one piece of content."""

    high_patterns = agent_memory.get("highPerformingPatterns", [])
    patterns_text = ""
    if high_patterns:
        patterns_text = "\n## 高パフォーマンスパターン（参考にせよ）\n"
        for p in high_patterns:
            patterns_text += f"- {p}\n"

    base_image = CATEGORY_BASE_IMAGE.get(category, "base_nurse_station.png")

    cta_instruction = ""
    if cta_type == "soft":
        cta_instruction = '6枚目のCTAは「保存してね」「フォローで続き見れる」などのソフトCTAにせよ。'
    else:
        cta_instruction = '6枚目のCTAは「LINEで相談できるよ」「プロフから登録」などのハードCTAにせよ。'

    prompt = f"""あなたはTikTokスライドショーの台本を生成する専門AIです。
以下のルールに厳密に従い、JSON形式で1つの台本を出力してください。

=== 台本生成ルール ===
{prompt_template}

=== 今回の指定 ===
- カテゴリ: {category}
- ID: {content_id}
- base_image: {base_image}
- cta_type: {cta_type}
- {cta_instruction}

=== 現在のストック状況 ===
{stock_status}
{patterns_text}

=== 出力形式 ===
以下のJSON形式のみを出力せよ。マークダウンのコードフェンス（```）は絶対に付けるな。説明文も不要。JSONだけ出力せよ。

{{
  "id": "{content_id}",
  "hook": "フック文（20文字以内）",
  "slides": [
    "1枚目フック文",
    "2枚目ストーリー",
    "3枚目ストーリー",
    "4枚目ストーリー",
    "5枚目クライマックス",
    "6枚目オチ+CTA"
  ],
  "caption": "キャプション200文字以内",
  "hashtags": ["#看護師", "#転職", "#AI", "#看護師あるある", "#神奈川"],
  "category": "{category}",
  "base_image": "{base_image}",
  "cta_type": "{cta_type}"
}}

重要: JSON以外のテキストを一切出力するな。"""

    return prompt


def invoke_claude(prompt: str) -> Optional[str]:
    """
    Invoke Claude CLI and return stdout.
    Returns None on failure.
    """
    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--max-turns", "1"],
            capture_output=True,
            text=True,
            timeout=CLAUDE_TIMEOUT,
        )
        if result.returncode != 0:
            print(f"[ERROR] Claude CLI exit code {result.returncode}")
            if result.stderr:
                print(f"  stderr: {result.stderr[:500]}")
            return None
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        print("[ERROR] Claude CLI timeout")
        return None
    except FileNotFoundError:
        print("[ERROR] 'claude' コマンドが見つかりません。Claude CLIをインストールしてください。")
        return None
    except Exception as e:
        print(f"[ERROR] Claude invocation failed: {e}")
        return None


def parse_json_from_output(output: str) -> Optional[Dict]:
    """
    Parse JSON from Claude output, handling possible markdown fences or extra text.
    """
    if not output:
        return None

    # Try direct parse first
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from markdown code fences
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", output, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try to find first { ... } block
    brace_match = re.search(r"\{.*\}", output, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def validate_content_json(data: dict, content_id: str) -> bool:
    """Validate that generated JSON has required fields and correct structure."""
    required_keys = ["id", "hook", "slides", "caption", "hashtags", "category", "base_image", "cta_type"]
    for key in required_keys:
        if key not in data:
            print(f"[WARN] Missing key in generated JSON: {key}")
            return False

    slides = data.get("slides", [])
    if not isinstance(slides, list) or len(slides) != 6:
        print(f"[WARN] slides must be a list of 6 items, got {len(slides) if isinstance(slides, list) else type(slides)}")
        return False

    hashtags = data.get("hashtags", [])
    if not isinstance(hashtags, list) or len(hashtags) > 5:
        print(f"[WARN] hashtags must be <= 5, got {len(hashtags) if isinstance(hashtags, list) else 'N/A'}")
        # Auto-trim instead of failing
        if isinstance(hashtags, list) and len(hashtags) > 5:
            data["hashtags"] = hashtags[:5]

    caption = data.get("caption", "")
    if len(caption) > 200:
        print(f"[WARN] caption exceeds 200 chars ({len(caption)}). Trimming.")
        data["caption"] = caption[:200]

    # Ensure id matches what we requested
    data["id"] = content_id

    return True


def generate_one_content(
    category: str,
    cta_type: str,
    content_id: str,
    prompt_template: str,
    agent_memory: dict,
    stock_status: str,
) -> Optional[Dict]:
    """
    Generate one台本 JSON using Claude CLI.
    Retries once on failure.
    """
    prompt = build_claude_prompt(
        category=category,
        cta_type=cta_type,
        content_id=content_id,
        prompt_template=prompt_template,
        agent_memory=agent_memory,
        stock_status=stock_status,
    )

    for attempt in range(2):
        if attempt > 0:
            print(f"  [RETRY] 再試行 (attempt {attempt + 1}/2)")

        print(f"  Claude CLI 呼び出し中... (category={category}, id={content_id}, cta={cta_type})")
        output = invoke_claude(prompt)

        if output is None:
            continue

        data = parse_json_from_output(output)
        if data is None:
            print(f"  [WARN] JSON解析失敗。出力の先頭200文字: {output[:200]}")
            continue

        if validate_content_json(data, content_id):
            print(f"  [OK] 台本JSON生成成功: {content_id}")
            return data

    print(f"  [FAIL] 台本JSON生成失敗 (2回試行): {content_id}")
    return None


def generate_slides_for_json(json_path: Path) -> Optional[Path]:
    """
    Call generate_slides.py for a single JSON file.
    Returns the output directory path, or None on failure.
    """
    print(f"  スライド生成中: {json_path.name}")
    try:
        result = subprocess.run(
            ["python3", str(PROJECT_DIR / "scripts" / "generate_slides.py"), "--json", str(json_path)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            print(f"  [ERROR] generate_slides.py failed (exit {result.returncode})")
            if result.stderr:
                print(f"    stderr: {result.stderr[:500]}")
            return None

        # Parse output to find the generated directory
        # generate_slides.py prints the output dir path
        stdout = result.stdout
        print(f"    {stdout.strip()[-200:]}" if len(stdout) > 200 else f"    {stdout.strip()}")

        # Determine the output dir from the content_id
        # generate_slides.py creates: content/generated/{date}_{content_id}/
        today = datetime.now().strftime("%Y%m%d")
        # Read the json to get the id
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        cid = data.get("content_id", data.get("id", "UNKNOWN"))
        slide_dir = GENERATED_DIR / f"{today}_{cid}"
        if slide_dir.exists():
            return slide_dir

        # Fallback: try to find the directory from generate_slides output
        # It may have used a different naming pattern
        for line in stdout.splitlines():
            if "出力:" in line or "出力先:" in line:
                path_str = line.split(":", 1)[-1].strip()
                candidate = Path(path_str)
                if candidate.exists():
                    return candidate
                # Try relative to project dir
                candidate = PROJECT_DIR / path_str
                if candidate.exists():
                    return candidate

        print(f"  [WARN] スライド出力ディレクトリが見つかりません。json_pathの親を使用。")
        return json_path.parent

    except subprocess.TimeoutExpired:
        print("  [ERROR] generate_slides.py timeout")
        return None
    except Exception as e:
        print(f"  [ERROR] generate_slides.py exception: {e}")
        return None


# ============================================================
# Pipeline
# ============================================================

def run_pipeline(count: int):
    """
    Main pipeline: generate `count` pieces of content.
    """
    print("=" * 60)
    print(f"ROBBY THE MATCH Content Pipeline - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"生成予定: {count}本")
    print("=" * 60)

    # Load all data
    queue = load_queue()
    stock = load_stock()
    agent_memory = load_agent_memory()
    prompt_template = load_prompt_template()

    pending_count = count_pending(queue)
    print(f"\n[STATUS] 現在のpending: {pending_count}件")
    print(f"[STATUS] ストック総数: {len(stock)}行")

    # Stock distribution
    dist = analyze_stock_distribution(stock)
    stock_status = "カテゴリ別ストック数:\n"
    for cat, cnt in dist.items():
        ideal = round(MIX_RATIOS[cat] * len(stock)) if stock else 0
        stock_status += f"  {cat}: {cnt}本 (理想比率: {MIX_RATIOS[cat]*100:.0f}%, 理想数: {ideal})\n"
    print(f"\n{stock_status}")

    # Determine what to generate
    needs = determine_needs(stock, count)
    print("[PLAN] 生成計画:")
    for i, n in enumerate(needs, 1):
        print(f"  {i}. {n['category']} (CTA: {n['cta_type']})")

    # Create batch directory
    today = datetime.now().strftime("%Y%m%d")
    batch_name = f"batch_{today}"
    batch_dir = GENERATED_DIR / batch_name
    batch_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n[BATCH] ディレクトリ: {batch_dir}")

    # Generate each piece
    generated = []
    failed = []

    for i, need in enumerate(needs, 1):
        category = need["category"]
        cta_type = need["cta_type"]

        # Get next content ID from current stock + already generated in this run
        all_stock = stock + [
            {"id": g["data"]["id"], "category": g["data"]["category"]}
            for g in generated
        ]
        content_id = get_next_content_id(all_stock, category)

        print(f"\n{'─' * 50}")
        print(f"[{i}/{count}] 生成開始: {content_id} ({category}, {cta_type})")
        print(f"{'─' * 50}")

        # Step 1: Generate 台本 JSON via Claude
        data = generate_one_content(
            category=category,
            cta_type=cta_type,
            content_id=content_id,
            prompt_template=prompt_template,
            agent_memory=agent_memory,
            stock_status=stock_status,
        )

        if data is None:
            failed.append({"content_id": content_id, "category": category, "reason": "Claude JSON生成失敗"})
            continue

        # Step 2: Save JSON to batch directory
        json_path = batch_dir / f"{content_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  [OK] JSON保存: {json_path.name}")

        # Step 3: Generate slides
        slide_dir = generate_slides_for_json(json_path)
        if slide_dir is None:
            print(f"  [WARN] スライド生成失敗。キューには追加するが slides は不完全。")
            slide_dir = batch_dir / content_id
            failed.append({"content_id": content_id, "category": category, "reason": "スライド生成失敗(キューには追加)"})

        generated.append({
            "data": data,
            "json_path": str(json_path),
            "slide_dir": str(slide_dir),
        })

    # Step 4: Update posting_queue.json
    print(f"\n{'=' * 60}")
    print("[QUEUE] posting_queue.json 更新中...")
    next_id = get_next_queue_id(queue)

    for g in generated:
        data = g["data"]
        content_id = data["id"]
        batch_content_id = f"{batch_name}_{content_id}"

        entry = {
            "id": next_id,
            "content_id": batch_content_id,
            "batch": batch_name,
            "slide_dir": g["slide_dir"],
            "json_path": g["json_path"],
            "caption": data.get("caption", ""),
            "hashtags": data.get("hashtags", []),
            "cta_type": data.get("cta_type", "soft"),
            "status": "pending",
            "video_path": None,
            "posted_at": None,
            "tiktok_url": None,
            "error": None,
            "performance": {"views": None, "likes": None, "saves": None, "comments": None},
            "verified": False,
        }
        queue["posts"].append(entry)
        print(f"  追加: id={next_id}, content_id={batch_content_id}")
        next_id += 1

    save_queue(queue)

    # Step 5: Update stock.csv
    print("\n[STOCK] stock.csv 更新中...")
    for g in generated:
        data = g["data"]
        stock.append({
            "id": data["id"],
            "category": data.get("category", ""),
            "hook": data.get("hook", ""),
            "status": "pending",
            "posted_date": "",
            "views": "",
            "likes": "",
            "saves": "",
            "comments": "",
            "rating": "",
        })
    save_stock(stock)

    # Step 6: Slack notification
    print("\n[SLACK] Slack通知送信中...")
    notify_slack(generated, failed, batch_name)

    # Summary
    print(f"\n{'=' * 60}")
    print("[SUMMARY]")
    print(f"  生成成功: {len(generated)}本")
    print(f"  生成失敗: {len(failed)}本")
    print(f"  バッチ: {batch_name}")
    print(f"  キュー内pending: {count_pending(queue)}件")
    for g in generated:
        d = g["data"]
        print(f"    - {d['id']} ({d['category']}) hook: {d.get('hook', 'N/A')}")
    if failed:
        print("  失敗:")
        for f_item in failed:
            print(f"    - {f_item['content_id']}: {f_item['reason']}")
    print("=" * 60)


def notify_slack(generated: list, failed: list, batch_name: str):
    """Send Slack notification about generated content."""
    lines = [f"Content Pipeline 完了 [{batch_name}]"]
    lines.append(f"生成: {len(generated)}本 / 失敗: {len(failed)}本")

    if generated:
        lines.append("")
        lines.append("--- 生成コンテンツ ---")
        for g in generated:
            d = g["data"]
            lines.append(f"  {d['id']} ({d['category']}, {d['cta_type']}): {d.get('hook', 'N/A')}")

    if failed:
        lines.append("")
        lines.append("--- 失敗 ---")
        for f_item in failed:
            lines.append(f"  {f_item['content_id']}: {f_item['reason']}")

    lines.append(f"\nQueue pending: {count_pending(load_queue())}件")

    message = "\n".join(lines)

    try:
        result = subprocess.run(
            ["python3", str(PROJECT_DIR / "scripts" / "notify_slack.py"), "--message", message],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            print("  [OK] Slack通知送信完了")
        else:
            print(f"  [WARN] Slack通知失敗 (exit {result.returncode})")
            if result.stderr:
                print(f"    {result.stderr[:300]}")
    except Exception as e:
        print(f"  [WARN] Slack通知例外: {e}")


# ============================================================
# Commands
# ============================================================

def cmd_status():
    """Show queue and stock status."""
    queue = load_queue()
    stock = load_stock()
    posts = queue.get("posts", [])

    total = len(posts)
    pending = sum(1 for p in posts if p.get("status") == "pending")
    posted = sum(1 for p in posts if p.get("status") == "posted")
    other = total - pending - posted

    print("=" * 60)
    print("ROBBY THE MATCH Content Pipeline Status")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    print(f"\n[QUEUE] posting_queue.json")
    print(f"  Total:   {total}")
    print(f"  Pending: {pending}")
    print(f"  Posted:  {posted}")
    if other > 0:
        print(f"  Other:   {other}")

    print(f"\n[STOCK] stock.csv ({len(stock)} rows)")
    dist = analyze_stock_distribution(stock)
    for cat in MIX_RATIOS:
        cnt = dist.get(cat, 0)
        target_pct = MIX_RATIOS[cat] * 100
        actual_pct = (cnt / len(stock) * 100) if stock else 0
        status_mark = "OK" if abs(actual_pct - target_pct) < 10 else "!"
        print(f"  {cat:8s}: {cnt:3d}本  (実績{actual_pct:5.1f}% / 目標{target_pct:4.0f}%) [{status_mark}]")

    # Show recent pending items
    pending_items = [p for p in posts if p.get("status") == "pending"]
    if pending_items:
        print(f"\n[PENDING] 直近のpending ({len(pending_items)}件):")
        for p in pending_items[:10]:
            cid = p.get("content_id", "?")
            batch = p.get("batch", "?")
            cta = p.get("cta_type", "?")
            print(f"  id={p['id']}, content_id={cid}, batch={batch}, cta={cta}")
        if len(pending_items) > 10:
            print(f"  ... 他 {len(pending_items) - 10}件")

    # Agent memory summary
    memory = load_agent_memory()
    high_patterns = memory.get("highPerformingPatterns", [])
    if high_patterns:
        print(f"\n[AGENT MEMORY] 高パフォーマンスパターン:")
        for p in high_patterns[:5]:
            print(f"  - {p}")

    print()
    if pending < AUTO_THRESHOLD:
        print(f"[NOTE] pending ({pending}) < threshold ({AUTO_THRESHOLD}) -- --auto で自動補充が実行されます")
    else:
        print(f"[NOTE] pending ({pending}) >= threshold ({AUTO_THRESHOLD}) -- --auto では生成スキップ")


def cmd_auto():
    """Auto-detect need and generate if pending < threshold."""
    queue = load_queue()
    pending = count_pending(queue)

    print(f"[AUTO] 現在のpending: {pending}件 / 閾値: {AUTO_THRESHOLD}件")

    if pending >= AUTO_THRESHOLD:
        print(f"[AUTO] pending >= {AUTO_THRESHOLD} のため生成不要。終了。")
        return

    need_count = AUTO_THRESHOLD - pending
    print(f"[AUTO] {need_count}本の生成が必要。パイプライン開始。")
    run_pipeline(need_count)


def cmd_force(count: int):
    """Force generate specified number of posts."""
    if count < 1:
        print("[ERROR] --force の値は1以上にしてください。")
        sys.exit(1)
    if count > 20:
        print("[WARN] 一度に20本以上の生成は推奨しません。10本に制限します。")
        count = 10
    print(f"[FORCE] {count}本を強制生成します。")
    run_pipeline(count)


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="ROBBY THE MATCH 自律型コンテンツ生成パイプライン"
    )
    parser.add_argument("--auto", action="store_true",
                        help="pending < 7 なら自動補充")
    parser.add_argument("--status", action="store_true",
                        help="キュー・ストック状況表示")
    parser.add_argument("--force", type=int, metavar="N",
                        help="N本を強制生成")

    args = parser.parse_args()

    # Load environment
    load_env()

    if args.status:
        cmd_status()
    elif args.auto:
        cmd_auto()
    elif args.force is not None:
        cmd_force(args.force)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
