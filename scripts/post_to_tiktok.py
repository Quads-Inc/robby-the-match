#!/usr/bin/env python3
"""
Postiz投稿スクリプト
6枚の画像をPostiz経由でTikTokに下書きアップロード
"""

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# プロジェクトルート
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

# Postiz API Key
POSTIZ_API_KEY = os.getenv("POSTIZ_API_KEY")

if not POSTIZ_API_KEY:
    print("⚠️  警告: POSTIZ_API_KEY が.envに設定されていません")
    print("   Postiz機能は使用できません")


def post_to_tiktok(json_path: Path, schedule: str = None):
    """
    Postiz経由でTikTokに投稿

    Args:
        json_path: 台本JSONファイルパス
        schedule: スケジュール時刻（ISO8601形式）
    """
    print(f"\n📤 TikTok投稿準備")
    print(f"   台本: {json_path.name}")

    # 台本JSONを読み込む
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    content_id = data.get("id", "UNKNOWN")
    caption = data.get("caption", "")
    hashtags = " ".join(data.get("hashtags", []))

    # キャプション + ハッシュタグ
    full_caption = f"{caption}\n\n{hashtags}"

    print(f"   ID: {content_id}")
    print(f"   キャプション: {caption[:50]}...")

    # スライド画像のパス
    today = json_path.stem.split('_')[0]
    slides_dir = project_root / "content" / "generated" / f"{today}_{content_id}"

    if not slides_dir.exists():
        print(f"❌ エラー: スライドディレクトリが見つかりません: {slides_dir}")
        return False

    # 6枚のスライド画像
    slide_paths = [slides_dir / f"slide_{i}.png" for i in range(1, 7)]

    # すべてのスライドが存在するか確認
    missing = [p for p in slide_paths if not p.exists()]
    if missing:
        print(f"❌ エラー: 一部のスライドが見つかりません:")
        for p in missing:
            print(f"   - {p.name}")
        return False

    print(f"   スライド: 6枚確認済み")

    # Postiz API Keyチェック
    if not POSTIZ_API_KEY:
        print("\n⚠️  Postiz API Keyが未設定のため、手動アップロードが必要です")
        print(f"\n📂 スライド画像:")
        for i, slide_path in enumerate(slide_paths, start=1):
            print(f"   {i}. {slide_path}")
        print(f"\n📝 キャプション:")
        print(f"   {full_caption}")
        print("\n💡 手動アップロード手順:")
        print("   1. TikTokアプリを開く")
        print("   2. 上記6枚の画像を順番に選択")
        print("   3. キャプションを貼り付け")
        print("   4. 音楽を選択")
        print("   5. 投稿ボタンを押す")
        return True

    # Postiz CLI経由でアップロード
    print("\n⏳ Postiz経由でアップロード中...")

    try:
        # Step 1: 画像をPostizにアップロード
        print("   Step 1: 画像アップロード")
        uploaded_urls = []

        for i, slide_path in enumerate(slide_paths, start=1):
            result = subprocess.run(
                ["postiz", "upload", str(slide_path)],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                # アップロード結果からURLを取得
                output = json.loads(result.stdout)
                url = output.get("path")
                uploaded_urls.append(url)
                print(f"      ✅ slide_{i}.png アップロード完了")
            else:
                print(f"      ❌ slide_{i}.png アップロード失敗")
                print(f"         {result.stderr}")
                return False

        # Step 2: 投稿を作成
        print("   Step 2: 投稿作成")

        # スケジュール時刻（デフォルト: 明日17:30 JST）
        if not schedule:
            tomorrow = datetime.now() + timedelta(days=1)
            schedule = tomorrow.replace(hour=17, minute=30, second=0).strftime("%Y-%m-%dT%H:%M:%S+09:00")

        # Postiz投稿コマンド
        media_urls = ",".join(uploaded_urls)

        result = subprocess.run(
            [
                "postiz", "posts:create",
                "-c", full_caption,
                "-m", media_urls,
                "-s", schedule,
                "-i", "tiktok"  # TikTok integration ID（要確認）
            ],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            print(f"   ✅ TikTok下書きアップロード完了")
            print(f"      スケジュール: {schedule}")
            return True
        else:
            print(f"   ❌ 投稿作成失敗")
            print(f"      {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("   ❌ タイムアウト: Postizの応答がありません")
        return False
    except Exception as e:
        print(f"   ❌ エラー: {type(e).__name__}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Postiz経由でTikTokに投稿")
    parser.add_argument("--json", required=True, help="台本JSONファイルパス")
    parser.add_argument("--schedule", help="スケジュール時刻（ISO8601形式）")

    args = parser.parse_args()

    json_path = Path(args.json)

    if not json_path.exists():
        print(f"❌ エラー: JSONファイルが見つかりません: {json_path}")
        sys.exit(1)

    success = post_to_tiktok(json_path=json_path, schedule=args.schedule)

    if success:
        print("\n✅ 処理完了")
        sys.exit(0)
    else:
        print("\n⚠️  処理に問題がありました")
        sys.exit(1)


if __name__ == "__main__":
    main()
