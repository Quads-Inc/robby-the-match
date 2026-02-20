#!/usr/bin/env python3
"""
ベース画像生成スクリプト（Imagen 4 Fast版）
モデル: imagen-4.0-fast-generate-001
コスト: $0.02/枚 × 3枚 = $0.06（9円）— 一度だけ
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from PIL import Image
import io

# プロジェクトルートから.envを読み込む
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

# Google API設定
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("ERROR: GOOGLE_API_KEY が.envに設定されていません。")
    sys.exit(1)

# クライアント作成
client = genai.Client(api_key=GOOGLE_API_KEY)

# 出力ディレクトリ
BASE_IMAGES_DIR = project_root / "content" / "base-images"
BASE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def generate_image(prompt: str, output_path: Path, aspect_ratio: str = "9:16"):
    """
    Imagen 4 Fast で画像を生成

    Args:
        prompt: 英語のプロンプト
        output_path: 出力ファイルパス
        aspect_ratio: アスペクト比（"9:16" = TikTok縦型）
    """
    print(f"🎨 画像生成中: {output_path.name}")
    print(f"   プロンプト: {prompt[:80]}...")
    print(f"   アスペクト比: {aspect_ratio}")

    try:
        # Imagen 4 Fastモデル
        model_name = "imagen-4.0-fast-generate-001"

        # 画像生成リクエスト
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )

        # レスポンスから画像データを取得
        if hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and candidate.content:
                    content = candidate.content
                    if hasattr(content, 'parts'):
                        for part in content.parts:
                            # inline_data（画像データ）をチェック
                            if hasattr(part, 'inline_data'):
                                inline_data = part.inline_data

                                # 画像データを取得
                                image_bytes = inline_data.data
                                img = Image.open(io.BytesIO(image_bytes))

                                print(f"   📦 生成サイズ: {img.size[0]}×{img.size[1]}px")

                                # 9:16にリサイズ（必要な場合）
                                if aspect_ratio == "9:16":
                                    width, height = img.size
                                    target_ratio = 9 / 16
                                    current_ratio = width / height

                                    if abs(current_ratio - target_ratio) > 0.01:
                                        # 正方形または16:9の場合、9:16に変換
                                        if current_ratio > target_ratio:
                                            # 横長 → 縦長に変換
                                            target_height = int(width / target_ratio)
                                            new_image = Image.new('RGB', (width, target_height), (0, 0, 0))
                                            paste_y = (target_height - height) // 2
                                            new_image.paste(img, (0, paste_y))
                                            img = new_image
                                            print(f"   🔄 リサイズ: {img.size[0]}×{img.size[1]}px")

                                # PNG形式で保存
                                img.save(output_path, "PNG")
                                print(f"   ✅ 保存完了: {output_path}")
                                return True

        print("   ❌ 画像が生成されませんでした")
        return False

    except Exception as e:
        print(f"   ❌ エラー: {type(e).__name__}: {e}")
        return False


def generate_base_images():
    """
    3種類のベース画像を生成（一度だけ）
    コスト: 3枚 × $0.02 = $0.06（9円）
    """
    images = [
        {
            "filename": "base_nurse_station.png",
            "prompt": (
                "Japanese hospital nurse station interior, modern clean design, "
                "warm fluorescent lighting, medical monitors on desk, nursing charts, "
                "no text, no people, professional photography, vertical composition 9:16, "
                "high quality, photorealistic"
            )
        },
        {
            "filename": "base_ai_chat.png",
            "prompt": (
                "Close-up of smartphone screen showing AI chat interface with glowing text, "
                "soft bokeh background of hospital corridor, modern UI design, "
                "no readable text characters, vertical composition 9:16, "
                "cinematic lighting, photorealistic"
            )
        },
        {
            "filename": "base_breakroom.png",
            "prompt": (
                "Japanese hospital staff break room, small table with coffee mugs, "
                "lockers in background, warm cozy lighting, window with natural light, "
                "no text, no people, interior photography, vertical composition 9:16, "
                "peaceful atmosphere, photorealistic"
            )
        }
    ]

    print("\n💰 コスト見積もり: 3枚 × $0.02 = $0.06（約9円）")
    print("   ベース画像は使い回すため、この支出は一度だけです。\n")

    success_count = 0
    total_cost = 0.0

    for img_data in images:
        output_path = BASE_IMAGES_DIR / img_data["filename"]

        # すでに存在する場合はスキップ
        if output_path.exists():
            print(f"✅ すでに存在: {img_data['filename']}")
            success_count += 1
            continue

        success = generate_image(
            prompt=img_data["prompt"],
            output_path=output_path,
            aspect_ratio="9:16"
        )

        if success:
            success_count += 1
            total_cost += 0.02
            print(f"   💸 累計コスト: ${total_cost:.2f}")
            # APIレート制限対策
            time.sleep(2)
        else:
            print(f"❌ 生成失敗: {img_data['filename']}")

    print(f"\n📊 結果: {success_count}/3 枚生成完了")
    print(f"💰 実際のコスト: ${total_cost:.2f}（約{int(total_cost * 150)}円）")
    print("\n✅ ベース画像は今後使い回します。二度と生成しません。")

    return success_count == 3


if __name__ == "__main__":
    print("=" * 60)
    print("ベース画像生成スクリプト（Imagen 4 Fast版）")
    print("=" * 60)
    print(f"出力先: {BASE_IMAGES_DIR}")
    print()

    success = generate_base_images()

    if success:
        print("\n🎉 すべてのベース画像が生成されました！")
        print("   これでPhase 2-1完了。Phase 2-2（テキスト焼き込み）に進めます。")
        sys.exit(0)
    else:
        print("\n⚠️  一部の画像生成に失敗しました。")
        sys.exit(1)
