#!/usr/bin/env python3
"""
ベース画像生成スクリプト（Google Gemini 2.0 Flash版）
モデル: gemini-2.0-flash-exp（画像生成対応、無料枠100RPD）
料金: 無料枠内（5 RPM, 100 RPD）、超過後$0.039/枚
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
import io

# プロジェクトルートから.envを読み込む
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

# Google Gemini API設定
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("ERROR: GOOGLE_API_KEY が.envに設定されていません。")
    print("取得方法: https://ai.google.dev/ > Get API key in Google AI Studio")
    sys.exit(1)

genai.configure(api_key=GOOGLE_API_KEY)

# 出力ディレクトリ
BASE_IMAGES_DIR = project_root / "content" / "base-images"
BASE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def generate_image(prompt: str, output_path: Path, aspect_ratio: str = "9:16"):
    """
    Google Gemini 2.0 Flash で画像を生成

    Args:
        prompt: 英語のプロンプト
        output_path: 出力ファイルパス
        aspect_ratio: アスペクト比（"9:16" = TikTok縦型、"1:1" = 正方形）
    """
    print(f"🎨 画像生成中: {output_path.name}")
    print(f"   プロンプト: {prompt[:80]}...")
    print(f"   アスペクト比: {aspect_ratio}")

    try:
        # Gemini 2.0 Flash Expモデル（画像生成対応）
        model = genai.ImageGenerationModel('imagen-3.0-generate-001')

        # アスペクト比の設定
        # Gemini APIでサポートされているアスペクト比を確認
        # サポート外の場合は1:1で生成後にPillowでリサイズ

        # 画像生成リクエスト
        response = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio=aspect_ratio,  # "9:16", "16:9", "1:1" etc.
            safety_filter_level="block_some",
            person_generation="allow_adult"
        )

        # 生成された画像を取得
        if response.images:
            image_data = response.images[0]._pil_image

            # Pillowで開いて再保存（ヘッダー破損対策）
            if aspect_ratio == "9:16":
                # 9:16の場合、1024×1820を期待
                # もし1024×1024の場合はリサイズ
                width, height = image_data.size
                if width == height:  # 正方形の場合
                    print(f"   ⚠️  正方形画像（{width}×{height}）→ 9:16にリサイズ")
                    target_height = int(width * 16 / 9)
                    # 新しいキャンバスを作成（上下に余白）
                    new_image = Image.new('RGB', (width, target_height), (0, 0, 0))
                    # 中央に配置
                    paste_y = (target_height - height) // 2
                    new_image.paste(image_data, (0, paste_y))
                    image_data = new_image

            # PNG形式で保存
            image_data.save(output_path, "PNG")
            print(f"   ✅ 保存完了: {image_data.size[0]}×{image_data.size[1]}px")
            return True
        else:
            print("   ❌ 画像が生成されませんでした")
            return False

    except AttributeError:
        # ImageGenerationModelが存在しない場合の代替実装
        print("   ℹ️  ImageGenerationModel未対応。代替方法を試行...")
        return generate_image_alternative(prompt, output_path, aspect_ratio)

    except Exception as e:
        print(f"   ❌ エラー: {type(e).__name__}: {e}")
        print("   ℹ️  代替方法を試行...")
        return generate_image_alternative(prompt, output_path, aspect_ratio)


def generate_image_alternative(prompt: str, output_path: Path, aspect_ratio: str = "9:16"):
    """
    代替方法: GenerativeModel経由で画像生成
    （Gemini 2.0 Flashの画像生成機能を使用）
    """
    try:
        # Gemini 2.0 Flash（画像生成対応）
        model = genai.GenerativeModel('gemini-2.0-flash-exp')

        # 画像生成プロンプト
        # Gemini 2.0 Flashの画像生成は特定のプロンプトフォーマットが必要
        generation_prompt = f"Generate an image: {prompt}"

        # アスペクト比の指定
        if aspect_ratio == "9:16":
            generation_prompt += " The image should be in 9:16 portrait aspect ratio (1024x1820 pixels)."

        response = model.generate_content(
            generation_prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.7,
            )
        )

        # 応答から画像データを取得
        # 注: 実際のレスポンス形式はAPIバージョンによって異なる可能性あり
        if hasattr(response, 'images') and response.images:
            image_data = response.images[0]

            # PILで開く
            img = Image.open(io.BytesIO(image_data))

            # 9:16にリサイズ（必要な場合）
            if aspect_ratio == "9:16":
                width, height = img.size
                if width == height:  # 正方形の場合
                    target_height = int(width * 16 / 9)
                    new_image = Image.new('RGB', (width, target_height), (0, 0, 0))
                    paste_y = (target_height - height) // 2
                    new_image.paste(img, (0, paste_y))
                    img = new_image

            img.save(output_path, "PNG")
            print(f"   ✅ 保存完了: {img.size[0]}×{img.size[1]}px")
            return True
        else:
            print("   ❌ 画像生成に失敗（レスポンスに画像なし）")
            print(f"   レスポンス: {response}")
            return False

    except Exception as e:
        print(f"   ❌ 代替方法もエラー: {type(e).__name__}: {e}")
        return False


def generate_base_images():
    """
    3種類のベース画像を生成
    """
    images = [
        {
            "filename": "base_nurse_station.png",
            "prompt": (
                "Japanese hospital nurse station interior, modern clean design, "
                "warm fluorescent lighting, medical monitors on desk, nursing charts, "
                "no text, no people, professional photography, vertical composition, "
                "high quality, photorealistic, 9:16 aspect ratio"
            )
        },
        {
            "filename": "base_ai_chat.png",
            "prompt": (
                "Close-up of smartphone screen showing AI chat interface with glowing text, "
                "soft bokeh background of hospital corridor, modern UI design, "
                "no readable text characters, vertical composition, "
                "cinematic lighting, photorealistic, 9:16 aspect ratio"
            )
        },
        {
            "filename": "base_breakroom.png",
            "prompt": (
                "Japanese hospital staff break room, small table with coffee mugs, "
                "lockers in background, warm cozy lighting, window with natural light, "
                "no text, no people, interior photography, vertical composition, "
                "peaceful atmosphere, photorealistic, 9:16 aspect ratio"
            )
        }
    ]

    success_count = 0
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
            print(f"✅ 生成完了: {img_data['filename']}")
            # APIレート制限対策
            time.sleep(2)
        else:
            print(f"❌ 生成失敗: {img_data['filename']}")

    print(f"\n📊 結果: {success_count}/3 枚生成完了")
    return success_count == 3


if __name__ == "__main__":
    print("=" * 60)
    print("ベース画像生成スクリプト（Google Gemini API版）")
    print("=" * 60)
    print(f"出力先: {BASE_IMAGES_DIR}")
    print()

    success = generate_base_images()

    if success:
        print("\n✅ すべてのベース画像が生成されました！")
        sys.exit(0)
    else:
        print("\n⚠️  一部の画像生成に失敗しました。")
        print("   APIキーを確認するか、代替サービスを検討してください。")
        sys.exit(1)
