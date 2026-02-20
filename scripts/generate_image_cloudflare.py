#!/usr/bin/env python3
"""
ベース画像生成スクリプト（Cloudflare Workers AI版）
モデル: @cf/stabilityai/stable-diffusion-xl-base-1.0
コスト: 無料枠（1日10,000 Neurons、画像生成約50枚相当）
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
import requests
from PIL import Image
import io

# プロジェクトルートから.envを読み込む
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

# Cloudflare API設定
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")

if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
    print("ERROR: CLOUDFLARE_ACCOUNT_ID または CLOUDFLARE_API_TOKEN が.envに設定されていません。")
    sys.exit(1)

# 出力ディレクトリ
BASE_IMAGES_DIR = project_root / "content" / "base-images"
BASE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Cloudflare Workers AI エンドポイント
API_BASE_URL = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/"
MODEL_NAME = "@cf/stabilityai/stable-diffusion-xl-base-1.0"


def generate_image(prompt: str, output_path: Path):
    """
    Cloudflare Workers AI で画像を生成

    Args:
        prompt: 英語のプロンプト
        output_path: 出力ファイルパス
    """
    print(f"🎨 画像生成中: {output_path.name}")
    print(f"   プロンプト: {prompt[:80]}...")

    try:
        # APIリクエスト
        headers = {
            "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "prompt": prompt,
            "num_steps": 20  # 生成ステップ数（20で十分な品質）
        }

        response = requests.post(
            f"{API_BASE_URL}{MODEL_NAME}",
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code == 200:
            # 画像データを取得
            image_bytes = response.content

            # Pillowで開いて確認
            img = Image.open(io.BytesIO(image_bytes))
            print(f"   📦 生成サイズ: {img.size[0]}×{img.size[1]}px")

            # 9:16にリサイズ（Cloudflare SDXLは1024×1024がデフォルト）
            width, height = img.size
            if width == height:  # 正方形の場合
                # 1024×1024 → 1024×1820（9:16に近い）
                target_height = int(width * 16 / 9)
                new_image = Image.new('RGB', (width, target_height), (0, 0, 0))
                # 中央に配置
                paste_y = (target_height - height) // 2
                new_image.paste(img, (0, paste_y))
                img = new_image
                print(f"   🔄 リサイズ: {img.size[0]}×{img.size[1]}px（9:16）")

            # PNG形式で再保存（ヘッダー破損対策）
            img.save(output_path, "PNG")
            print(f"   ✅ 保存完了: {output_path}")
            return True

        else:
            print(f"   ❌ エラー: HTTP {response.status_code}")
            print(f"   レスポンス: {response.text}")
            return False

    except Exception as e:
        print(f"   ❌ エラー: {type(e).__name__}: {e}")
        return False


def generate_base_images():
    """
    3種類のベース画像を生成（無料枠）
    """
    images = [
        {
            "filename": "base_nurse_station.png",
            "prompt": (
                "Japanese hospital nurse station interior, modern clean design, "
                "warm fluorescent lighting, medical monitors on desk, nursing charts, "
                "no text, no people, professional photography, high quality, photorealistic"
            )
        },
        {
            "filename": "base_ai_chat.png",
            "prompt": (
                "Close-up of smartphone screen showing AI chat interface with glowing text, "
                "soft bokeh background of hospital corridor, modern UI design, "
                "no readable text characters, cinematic lighting, photorealistic"
            )
        },
        {
            "filename": "base_breakroom.png",
            "prompt": (
                "Japanese hospital staff break room, small table with coffee mugs, "
                "lockers in background, warm cozy lighting, window with natural light, "
                "no text, no people, interior photography, peaceful atmosphere, photorealistic"
            )
        }
    ]

    print("\n💰 コスト: 無料枠（Cloudflare Workers AI）")
    print("   1日10,000 Neurons、ベース画像3枚は余裕で無料枠内\n")

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
            output_path=output_path
        )

        if success:
            success_count += 1
            # APIレート制限対策
            time.sleep(2)
        else:
            print(f"❌ 生成失敗: {img_data['filename']}")

    print(f"\n📊 結果: {success_count}/3 枚生成完了")
    print("✅ ベース画像は今後使い回します。二度と生成しません。")

    return success_count == 3


if __name__ == "__main__":
    print("=" * 60)
    print("ベース画像生成スクリプト（Cloudflare Workers AI版）")
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
