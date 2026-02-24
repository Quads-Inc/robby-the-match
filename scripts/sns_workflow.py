#!/usr/bin/env python3
"""
SNS統合投稿ワークフロー v1.0
- 投稿キュー管理（ファイルロック付き）
- カルーセル画像生成（generate_slides.py呼び出し）
- Buffer手動アップロード用コンテンツ準備
- Slack通知

使い方:
  python3 scripts/sns_workflow.py --prepare-next     # 次の投稿を準備
  python3 scripts/sns_workflow.py --mark-posted 4    # 投稿#4を完了済みにする
  python3 scripts/sns_workflow.py --status           # キュー状態表示
  python3 scripts/sns_workflow.py --regenerate 4     # #4のスライドを再生成
"""

import argparse
import fcntl
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ============================================================
# 定数
# ============================================================

PROJECT_DIR = Path(__file__).parent.parent
QUEUE_FILE = PROJECT_DIR / "data" / "posting_queue.json"
READY_DIR = PROJECT_DIR / "content" / "ready"
LOCK_FILE = PROJECT_DIR / "data" / ".posting_queue.lock"
LOG_DIR = PROJECT_DIR / "logs"
ENV_FILE = PROJECT_DIR / ".env"

# ============================================================
# キャプションテンプレート & ハッシュタグ
# ============================================================

# ハッシュタグセット
HASHTAGS = {
    "core": ["#看護師転職", "#ナースロビー", "#神奈川看護師"],
    "reach": ["#看護師あるある", "#ナース", "#看護師の日常"],
    "niche": ["#小田原看護師", "#神奈川県西部", "#手数料10パーセント"],
}

# コンテンツタイプ別テンプレート
# content_type: aruaru(40%), career(25%), salary(20%), service(5%), trend(10%)
CAPTION_TEMPLATES = {
    "aruaru": {
        "ratio": 0.40,
        "description": "看護師あるある x AIやってみた",
        "cta_style": "soft",
        "caption_suffix": "\n\n共感したら保存してね",
        "hashtag_pool": [
            "#看護師あるある", "#ナースロビー", "#看護師の日常",
            "#ナース", "#神奈川看護師",
        ],
        "hashtag_count": 4,
    },
    "career": {
        "ratio": 0.25,
        "description": "転職・キャリア x AIシミュレーション",
        "cta_style": "soft",
        "caption_suffix": "\n\n転職の相談はプロフィールのLINEからどうぞ",
        "hashtag_pool": [
            "#看護師転職", "#ナースロビー", "#キャリア",
            "#神奈川看護師", "#転職",
        ],
        "hashtag_count": 4,
    },
    "salary": {
        "ratio": 0.20,
        "description": "給与・待遇 x AIデータ分析",
        "cta_style": "soft",
        "caption_suffix": "\n\nこの表は保存推奨です",
        "hashtag_pool": [
            "#看護師転職", "#ナースロビー", "#給与",
            "#年収", "#神奈川看護師",
        ],
        "hashtag_count": 4,
    },
    "service": {
        "ratio": 0.05,
        "description": "ナースロビー紹介",
        "cta_style": "hard",
        "caption_suffix": "\n\n手数料10%で転職サポート。プロフィールのLINEから無料相談できます",
        "hashtag_pool": [
            "#看護師転職", "#ナースロビー", "#手数料10パーセント",
        ],
        "hashtag_count": 3,
    },
    "trend": {
        "ratio": 0.10,
        "description": "トレンド便乗",
        "cta_style": "soft",
        "caption_suffix": "\n\nしんどい環境にいる人、話聞くよ",
        "hashtag_pool": [
            "#看護師あるある", "#ナースロビー", "#看護師の日常",
            "#ナース", "#神奈川看護師",
        ],
        "hashtag_count": 5,
    },
}


def load_env():
    """Load .env file"""
    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())


# ============================================================
# ファイルロック付きキュー管理
# ============================================================

class QueueManager:
    """ファイルロック付きキュー管理クラス"""

    def __init__(self):
        self.queue = None
        self._lock_fd = None

    def _acquire_lock(self, timeout=10):
        """ファイルロックを取得"""
        LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._lock_fd = open(LOCK_FILE, 'w')
        start = time.time()
        while True:
            try:
                fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            except (IOError, OSError):
                if time.time() - start > timeout:
                    print("[ERROR] キューのロック取得タイムアウト")
                    self._lock_fd.close()
                    self._lock_fd = None
                    return False
                time.sleep(0.5)

    def _release_lock(self):
        """ファイルロックを解放"""
        if self._lock_fd:
            try:
                fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
                self._lock_fd.close()
            except Exception:
                pass
            self._lock_fd = None

    def load(self):
        """キューを読み込み（ロック付き）"""
        if not self._acquire_lock():
            return False

        if not QUEUE_FILE.exists():
            print("[ERROR] キューファイルがありません: %s" % QUEUE_FILE)
            self._release_lock()
            return False

        try:
            with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
                self.queue = json.load(f)
            return True
        except json.JSONDecodeError as e:
            print("[ERROR] キューファイルのJSON解析失敗: %s" % e)
            self._release_lock()
            return False

    def save(self):
        """キューを保存してロック解放"""
        if self.queue is None:
            self._release_lock()
            return False

        try:
            self.queue["updated"] = datetime.now().isoformat()
            with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.queue, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print("[ERROR] キュー保存失敗: %s" % e)
            return False
        finally:
            self._release_lock()

    def release(self):
        """ロック解放のみ（保存なし）"""
        self._release_lock()

    def get_post_by_id(self, post_id):
        """ID指定で投稿を取得"""
        if not self.queue:
            return None
        for post in self.queue["posts"]:
            if post["id"] == post_id:
                return post
        return None

    def get_next_pending(self):
        """次のpending投稿を取得"""
        if not self.queue:
            return None
        for post in self.queue["posts"]:
            if post["status"] == "pending":
                return post
        return None

    def get_stats(self):
        """キューの統計を取得"""
        if not self.queue:
            return {}
        stats = {}
        for post in self.queue["posts"]:
            status = post["status"]
            stats[status] = stats.get(status, 0) + 1
        return stats


# ============================================================
# パス変換ユーティリティ
# ============================================================

def to_absolute(rel_path):
    """相対パスを絶対パスに変換"""
    if rel_path is None:
        return None
    p = Path(rel_path)
    if p.is_absolute():
        return p
    return PROJECT_DIR / rel_path


def to_relative(abs_path):
    """絶対パスを相対パスに変換"""
    if abs_path is None:
        return None
    p = Path(abs_path)
    try:
        return str(p.relative_to(PROJECT_DIR))
    except ValueError:
        return str(p)


# ============================================================
# Slack通知
# ============================================================

def slack_notify(message):
    """Slack通知を送信"""
    try:
        subprocess.run(
            ["python3", str(PROJECT_DIR / "scripts" / "notify_slack.py"),
             "--message", message],
            capture_output=True, timeout=30
        )
    except Exception as e:
        print("[WARN] Slack通知失敗: %s" % e)


# ============================================================
# ログ
# ============================================================

def log_event(event_type, data):
    """イベントログ記録"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / ("sns_workflow_%s.log" % datetime.now().strftime('%Y%m%d'))
    entry = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "data": data
    }
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ============================================================
# キャプション生成
# ============================================================

def get_content_type(post):
    """投稿のcontent_typeを判定"""
    # 明示的にcontent_typeが設定されている場合はそれを使う
    ct = post.get("content_type")
    if ct and ct in CAPTION_TEMPLATES:
        return ct

    # cta_typeから推定
    if post.get("cta_type") == "hard":
        return "service"

    # ハッシュタグやキャプションから推定
    caption = post.get("caption", "")
    hashtags = post.get("hashtags", [])
    all_text = caption + " ".join(hashtags)

    if any(kw in all_text for kw in ["あるある", "の日常", "患者", "先輩", "師長", "ナースコール", "記録"]):
        return "aruaru"
    elif any(kw in all_text for kw in ["年収", "給与", "手当", "相場", "給料"]):
        return "salary"
    elif any(kw in all_text for kw in ["転職", "キャリア", "経験年数", "市場価値"]):
        return "career"
    elif any(kw in all_text for kw in ["彼氏", "お母さん", "トレンド"]):
        return "trend"
    else:
        return "aruaru"


def generate_hashtags_for_type(content_type):
    """コンテンツタイプに基づくハッシュタグを生成"""
    template = CAPTION_TEMPLATES.get(content_type, CAPTION_TEMPLATES["aruaru"])
    pool = template["hashtag_pool"]
    count = min(template["hashtag_count"], len(pool))
    return pool[:count]


def format_caption_for_export(post):
    """投稿用のキャプションをフォーマット"""
    content_type = get_content_type(post)
    template = CAPTION_TEMPLATES.get(content_type, CAPTION_TEMPLATES["aruaru"])

    caption = post.get("caption", "")
    # 既存のハッシュタグを除去（キャプション本文に含まれている場合）
    for tag in post.get("hashtags", []):
        caption = caption.replace(tag, "").strip()

    # CTAサフィックスを追加（キャプションの末尾にまだない場合）
    suffix = template["caption_suffix"]
    if suffix and suffix.strip() not in caption:
        caption = caption.rstrip() + suffix

    return caption


def format_hashtags_for_export(post):
    """投稿用のハッシュタグをフォーマット"""
    # 既存のハッシュタグを使用
    existing = post.get("hashtags", [])
    if existing:
        return " ".join(existing)

    # なければテンプレートから生成
    content_type = get_content_type(post)
    tags = generate_hashtags_for_type(content_type)
    return " ".join(tags)


# ============================================================
# スライド生成
# ============================================================

def ensure_slides_exist(post):
    """スライドPNGが存在するか確認し、なければ生成"""
    slide_dir = to_absolute(post.get("slide_dir"))
    json_path = to_absolute(post.get("json_path"))

    if slide_dir is None:
        print("[ERROR] slide_dirが設定されていません (post #%d)" % post["id"])
        return False

    # スライドが既に存在するか確認
    existing_slides = sorted(slide_dir.glob("slide_*.png")) if slide_dir.exists() else []
    if existing_slides:
        print("[OK] スライド %d枚が既に存在: %s" % (len(existing_slides), slide_dir.name))
        return True

    # JSONファイルからスライド生成
    if json_path and json_path.exists():
        print("[INFO] スライド生成中: %s" % json_path.name)
        generate_script = PROJECT_DIR / "scripts" / "generate_slides.py"
        if not generate_script.exists():
            print("[ERROR] generate_slides.py が見つかりません")
            return False

        try:
            result = subprocess.run(
                ["python3", str(generate_script), "--json", str(json_path)],
                capture_output=True, text=True, timeout=120,
                cwd=str(PROJECT_DIR)
            )
            if result.returncode != 0:
                print("[ERROR] スライド生成失敗:")
                print("  stdout: %s" % result.stdout[-500:] if result.stdout else "")
                print("  stderr: %s" % result.stderr[-500:] if result.stderr else "")
                return False

            # 生成後に再確認
            existing_slides = sorted(slide_dir.glob("slide_*.png")) if slide_dir.exists() else []
            if existing_slides:
                print("[OK] スライド %d枚 生成完了" % len(existing_slides))
                return True
            else:
                print("[ERROR] スライド生成したが、ファイルが見つかりません")
                return False
        except subprocess.TimeoutExpired:
            print("[ERROR] スライド生成タイムアウト")
            return False
    else:
        print("[ERROR] JSONファイルが見つかりません: %s" % json_path)
        return False


# ============================================================
# コマンド: --prepare-next
# ============================================================

def prepare_next():
    """次のpending投稿をBufferアップロード用に準備"""
    qm = QueueManager()
    if not qm.load():
        return False

    post = qm.get_next_pending()
    if not post:
        print("[INFO] 全投稿完了。キューに残りなし。")
        stats = qm.get_stats()
        print("[INFO] 状態: %s" % json.dumps(stats, ensure_ascii=False))
        qm.release()
        return True

    post_id = post["id"]
    content_id = post["content_id"]
    print("\n" + "=" * 50)
    print("投稿準備 #%d: %s" % (post_id, content_id))
    print("=" * 50)

    # Step 1: スライドが存在するか確認/生成
    if not ensure_slides_exist(post):
        post["status"] = "failed"
        post["error"] = "slide_generation_failed"
        qm.save()
        slack_notify(
            "[SNS] スライド生成失敗: #%d %s" % (post_id, content_id)
        )
        log_event("prepare_failed", {"post_id": post_id, "reason": "slide_generation"})
        return False

    # Step 2: ready ディレクトリにコピー
    today = datetime.now().strftime("%Y%m%d")
    ready_subdir = READY_DIR / ("%s_%s" % (today, content_id))
    ready_subdir.mkdir(parents=True, exist_ok=True)

    slide_dir = to_absolute(post.get("slide_dir"))
    slides = sorted(slide_dir.glob("slide_*.png"))

    if not slides:
        print("[ERROR] スライドファイルが見つかりません: %s" % slide_dir)
        post["status"] = "failed"
        post["error"] = "no_slide_files"
        qm.save()
        return False

    # スライドをコピー（slide_1.png, slide_2.png, ...）
    for i, slide_src in enumerate(slides, start=1):
        dest = ready_subdir / ("slide_%d.png" % i)
        shutil.copy2(str(slide_src), str(dest))
    print("[OK] %d枚のスライドをコピー: %s" % (len(slides), ready_subdir.name))

    # Step 3: caption.txt を生成
    caption_text = format_caption_for_export(post)
    caption_file = ready_subdir / "caption.txt"
    with open(caption_file, 'w', encoding='utf-8') as f:
        f.write(caption_text)
    print("[OK] caption.txt 生成完了")

    # Step 4: hashtags.txt を生成
    hashtags_text = format_hashtags_for_export(post)
    hashtags_file = ready_subdir / "hashtags.txt"
    with open(hashtags_file, 'w', encoding='utf-8') as f:
        f.write(hashtags_text)
    print("[OK] hashtags.txt 生成完了")

    # Step 5: 投稿情報のメタデータを保存
    content_type = get_content_type(post)
    meta = {
        "post_id": post_id,
        "content_id": content_id,
        "content_type": content_type,
        "content_type_label": CAPTION_TEMPLATES.get(content_type, {}).get("description", ""),
        "cta_style": CAPTION_TEMPLATES.get(content_type, {}).get("cta_style", "soft"),
        "slide_count": len(slides),
        "prepared_at": datetime.now().isoformat(),
        "batch": post.get("batch", ""),
    }
    meta_file = ready_subdir / "meta.json"
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print("[OK] meta.json 生成完了")

    # Step 6: キューステータスを更新
    post["status"] = "ready"
    post["error"] = None
    qm.save()

    # Step 7: Slack通知
    stats = QueueManager()
    stats.load()
    remaining = sum(1 for p in stats.queue["posts"] if p["status"] == "pending")
    stats.release()

    slack_message = (
        "[SNS投稿準備完了]\n"
        "投稿 #%d: %s\n"
        "タイプ: %s\n"
        "スライド: %d枚\n"
        "キャプション: %s...\n"
        "ハッシュタグ: %s\n"
        "準備フォルダ: content/ready/%s/\n"
        "残りキュー: %d件\n\n"
        "Bufferからアップロードしてください。"
        "完了後: python3 scripts/sns_workflow.py --mark-posted %d"
    ) % (
        post_id, content_id,
        CAPTION_TEMPLATES.get(content_type, {}).get("description", content_type),
        len(slides),
        caption_text[:60],
        hashtags_text,
        ready_subdir.name,
        remaining,
        post_id,
    )
    slack_notify(slack_message)
    print("\n[OK] Slack通知送信完了")

    log_event("prepare_success", {
        "post_id": post_id,
        "content_id": content_id,
        "content_type": content_type,
        "slide_count": len(slides),
        "ready_dir": str(ready_subdir),
    })

    print("\n" + "=" * 50)
    print("[完了] 投稿 #%d の準備が完了しました" % post_id)
    print("  フォルダ: %s" % ready_subdir)
    print("  次のステップ: Bufferでアップロード後、以下を実行")
    print("  python3 scripts/sns_workflow.py --mark-posted %d" % post_id)
    print("=" * 50)

    return True


# ============================================================
# コマンド: --mark-posted
# ============================================================

def mark_posted(post_id):
    """投稿を完了済みにマーク"""
    qm = QueueManager()
    if not qm.load():
        return False

    post = qm.get_post_by_id(post_id)
    if not post:
        print("[ERROR] 投稿 #%d が見つかりません" % post_id)
        qm.release()
        return False

    old_status = post["status"]
    if old_status == "posted":
        print("[INFO] 投稿 #%d は既に posted です" % post_id)
        qm.release()
        return True

    if old_status not in ("ready", "pending", "failed"):
        print("[WARN] 投稿 #%d のステータスは '%s' です。強制的に posted にします。" % (post_id, old_status))

    post["status"] = "posted"
    post["posted_at"] = datetime.now().isoformat()
    post["error"] = None
    qm.save()

    print("[OK] 投稿 #%d を posted に更新しました (%s -> posted)" % (post_id, old_status))

    # 統計
    qm2 = QueueManager()
    qm2.load()
    stats = qm2.get_stats()
    qm2.release()

    posted = stats.get("posted", 0)
    pending = stats.get("pending", 0)
    ready = stats.get("ready", 0)
    total = sum(stats.values())

    slack_notify(
        "[SNS投稿完了] #%d %s\n"
        "投稿済み: %d / %d件\n"
        "待機中: %d件 | 準備済み: %d件"
        % (post_id, post.get("content_id", ""), posted, total, pending, ready)
    )

    log_event("mark_posted", {"post_id": post_id, "content_id": post.get("content_id")})
    return True


# ============================================================
# コマンド: --status
# ============================================================

def show_status():
    """キュー状態サマリを表示"""
    qm = QueueManager()
    if not qm.load():
        return False

    stats = qm.get_stats()
    total = sum(stats.values())

    print("\n=== SNS投稿キュー状態 ===")
    print("最終更新: %s" % qm.queue.get("updated", "不明"))
    print("合計: %d件" % total)
    print()

    # ステータスごとの集計
    status_labels = {
        "posted": "投稿済み",
        "ready": "準備済み（Buffer待ち）",
        "pending": "待機中",
        "failed": "失敗",
    }
    for status_key in ["posted", "ready", "pending", "failed"]:
        count = stats.get(status_key, 0)
        label = status_labels.get(status_key, status_key)
        if count > 0:
            print("  %s: %d件" % (label, count))

    print()

    # コンテンツタイプ別集計
    type_counts = {}
    for post in qm.queue["posts"]:
        ct = get_content_type(post)
        type_counts[ct] = type_counts.get(ct, 0) + 1

    print("--- コンテンツタイプ内訳 ---")
    for ct, count in sorted(type_counts.items()):
        template = CAPTION_TEMPLATES.get(ct, {})
        label = template.get("description", ct)
        target = template.get("ratio", 0) * 100
        actual = (count / total * 100) if total > 0 else 0
        print("  %s: %d件 (%.0f%% / 目標%.0f%%)" % (label, count, actual, target))

    print()

    # 個別リスト
    status_icons = {
        "pending": "[ ]",
        "ready": "[*]",
        "posted": "[v]",
        "failed": "[x]",
    }

    for post in qm.queue["posts"]:
        icon = status_icons.get(post["status"], "[?]")
        posted_info = ""
        if post.get("posted_at"):
            posted_info = " (%s)" % post["posted_at"][:10]
        error_info = ""
        if post.get("error"):
            error_info = " [ERR: %s]" % post["error"]
        ct = get_content_type(post)

        print("  %s #%02d: %-20s [%s]%s%s" % (
            icon, post["id"], post["content_id"], ct, posted_info, error_info
        ))

    qm.release()

    # readyディレクトリの内容
    if READY_DIR.exists():
        ready_dirs = sorted(READY_DIR.iterdir())
        if ready_dirs:
            print("\n--- 準備済みフォルダ (content/ready/) ---")
            for d in ready_dirs:
                if d.is_dir():
                    files = list(d.iterdir())
                    pngs = [f for f in files if f.suffix == ".png"]
                    print("  %s/ (%d枚)" % (d.name, len(pngs)))

    print()
    return True


# ============================================================
# コマンド: --regenerate
# ============================================================

def regenerate_slides(post_id):
    """指定投稿のスライドを再生成"""
    qm = QueueManager()
    if not qm.load():
        return False

    post = qm.get_post_by_id(post_id)
    if not post:
        print("[ERROR] 投稿 #%d が見つかりません" % post_id)
        qm.release()
        return False

    slide_dir = to_absolute(post.get("slide_dir"))
    json_path = to_absolute(post.get("json_path"))

    if not json_path or not json_path.exists():
        print("[ERROR] JSONファイルが見つかりません: %s" % json_path)
        qm.release()
        return False

    # 既存スライドを削除
    if slide_dir and slide_dir.exists():
        for old_slide in slide_dir.glob("slide_*.png"):
            old_slide.unlink()
        print("[INFO] 既存スライドを削除しました")

    # 再生成
    qm.release()
    print("[INFO] スライドを再生成中...")
    generate_script = PROJECT_DIR / "scripts" / "generate_slides.py"
    result = subprocess.run(
        ["python3", str(generate_script), "--json", str(json_path)],
        capture_output=True, text=True, timeout=120,
        cwd=str(PROJECT_DIR)
    )

    if result.returncode == 0:
        print("[OK] スライド再生成完了")
        print(result.stdout)
        return True
    else:
        print("[ERROR] スライド再生成失敗")
        if result.stderr:
            print(result.stderr[-500:])
        return False


# ============================================================
# コマンド: --reset
# ============================================================

def reset_post(post_id):
    """指定投稿をpendingにリセット"""
    qm = QueueManager()
    if not qm.load():
        return False

    post = qm.get_post_by_id(post_id)
    if not post:
        print("[ERROR] 投稿 #%d が見つかりません" % post_id)
        qm.release()
        return False

    old_status = post["status"]
    post["status"] = "pending"
    post["error"] = None
    post["posted_at"] = None
    qm.save()

    print("[OK] 投稿 #%d を pending にリセットしました (%s -> pending)" % (post_id, old_status))
    return True


# ============================================================
# メイン
# ============================================================

def main():
    load_env()

    parser = argparse.ArgumentParser(
        description="SNS統合投稿ワークフロー v1.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s --prepare-next          次の投稿を準備
  %(prog)s --mark-posted 4         投稿#4を完了済みにする
  %(prog)s --status                キュー状態表示
  %(prog)s --regenerate 4          投稿#4のスライドを再生成
  %(prog)s --reset 4               投稿#4をpendingにリセット
        """
    )

    parser.add_argument("--prepare-next", action="store_true",
                        help="次のpending投稿を準備（スライド確認→readyフォルダ作成→Slack通知）")
    parser.add_argument("--mark-posted", type=int, metavar="ID",
                        help="指定IDの投稿を完了済みにする")
    parser.add_argument("--status", action="store_true",
                        help="キュー状態サマリを表示")
    parser.add_argument("--regenerate", type=int, metavar="ID",
                        help="指定IDのスライドを再生成")
    parser.add_argument("--reset", type=int, metavar="ID",
                        help="指定IDの投稿をpendingにリセット")

    args = parser.parse_args()

    if args.prepare_next:
        success = prepare_next()
        sys.exit(0 if success else 1)
    elif args.mark_posted is not None:
        success = mark_posted(args.mark_posted)
        sys.exit(0 if success else 1)
    elif args.status:
        success = show_status()
        sys.exit(0 if success else 1)
    elif args.regenerate is not None:
        success = regenerate_slides(args.regenerate)
        sys.exit(0 if success else 1)
    elif args.reset is not None:
        success = reset_post(args.reset)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
