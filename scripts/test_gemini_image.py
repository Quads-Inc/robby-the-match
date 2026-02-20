#!/usr/bin/env python3
"""
Google Gemini 2.0 Flash 画像生成APIテスト
正確なAPI呼び出し方法を確認する
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# .env読み込み
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("❌ GOOGLE_API_KEY が設定されていません")
    sys.exit(1)

print(f"✅ APIキー取得: {GOOGLE_API_KEY[:20]}...")

# API設定
genai.configure(api_key=GOOGLE_API_KEY)

# 利用可能なモデルを確認
print("\n📋 利用可能なモデル:")
try:
    models = genai.list_models()
    for model in models:
        if 'generate' in model.name.lower() or 'imagen' in model.name.lower() or '2.0-flash' in model.name.lower():
            print(f"  - {model.name}")
            if hasattr(model, 'supported_generation_methods'):
                print(f"    サポート: {model.supported_generation_methods}")
except Exception as e:
    print(f"  ⚠️  モデル一覧取得エラー: {e}")

# テスト1: ImageGenerationModel（存在する場合）
print("\n🧪 テスト1: ImageGenerationModel")
try:
    model = genai.ImageGenerationModel('imagen-3.0-generate-001')
    print("  ✅ ImageGenerationModel が利用可能")
except AttributeError:
    print("  ❌ ImageGenerationModel は存在しません")
except Exception as e:
    print(f"  ⚠️  エラー: {e}")

# テスト2: GenerativeModel で画像生成
print("\n🧪 テスト2: GenerativeModel (gemini-2.0-flash-exp)")
try:
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    print("  ✅ モデル読み込み成功")

    # 画像生成プロンプト
    prompt = "Generate a simple test image: a white background with a black circle in the center"

    print(f"  📝 プロンプト: {prompt}")
    print("  ⏳ 生成中...")

    response = model.generate_content(prompt)

    print(f"  📦 レスポンス型: {type(response)}")
    print(f"  📦 レスポンス属性: {dir(response)}")

    if hasattr(response, 'text'):
        print(f"  📝 テキスト: {response.text[:200]}")

    if hasattr(response, 'parts'):
        print(f"  🧩 パーツ数: {len(response.parts)}")
        for i, part in enumerate(response.parts):
            print(f"    Part {i}: {type(part)}")
            if hasattr(part, 'inline_data'):
                print(f"      → inline_data あり!")

    if hasattr(response, 'images'):
        print(f"  🖼️  画像数: {len(response.images)}")

except Exception as e:
    print(f"  ❌ エラー: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# テスト3: 画像生成専用メソッド（存在する場合）
print("\n🧪 テスト3: generate_images メソッド")
try:
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    if hasattr(model, 'generate_images'):
        print("  ✅ generate_images メソッドが存在")
        result = model.generate_images(
            prompt="A simple white background",
            number_of_images=1
        )
        print(f"  📦 結果: {type(result)}")
    else:
        print("  ❌ generate_images メソッドは存在しません")
except Exception as e:
    print(f"  ⚠️  エラー: {e}")

print("\n" + "="*60)
print("テスト完了")
print("="*60)
