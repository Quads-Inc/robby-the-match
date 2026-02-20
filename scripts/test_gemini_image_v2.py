#!/usr/bin/env python3
"""
Google Gemini 2.0 Flash 画像生成APIテスト（新パッケージ版）
google.genai を使用
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# .env読み込み
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("❌ GOOGLE_API_KEY が設定されていません")
    sys.exit(1)

print(f"✅ APIキー取得: {GOOGLE_API_KEY[:20]}...")

# クライアント作成
client = genai.Client(api_key=GOOGLE_API_KEY)

print("\n" + "="*60)
print("🧪 テスト: gemini-2.0-flash-exp-image-generation")
print("="*60)

try:
    # 画像生成モデル
    model_name = "gemini-2.0-flash-exp-image-generation"

    # 画像生成リクエスト
    prompt = "A simple test image: white background with a small black circle in the center, minimalist design"

    print(f"📝 プロンプト: {prompt}")
    print("⏳ 生成中...")

    response = client.models.generate_content(
        model=model_name,
        contents=prompt
    )

    print(f"✅ レスポンス受信")
    print(f"📦 レスポンス型: {type(response)}")

    # レスポンスの内容を確認
    if hasattr(response, 'candidates'):
        print(f"🎯 候補数: {len(response.candidates)}")
        for i, candidate in enumerate(response.candidates):
            print(f"\n  候補 {i+1}:")
            if hasattr(candidate, 'content') and candidate.content:
                content = candidate.content
                if hasattr(content, 'parts'):
                    print(f"    パーツ数: {len(content.parts)}")
                    for j, part in enumerate(content.parts):
                        print(f"      Part {j+1}: {type(part)}")

                        # inline_data（画像データ）をチェック
                        if hasattr(part, 'inline_data'):
                            inline_data = part.inline_data
                            print(f"        ✅ 画像データあり!")
                            print(f"           mime_type: {inline_data.mime_type}")
                            print(f"           data size: {len(inline_data.data)} bytes")

                            # 画像を保存
                            output_path = project_root / "content" / "base-images" / "test_gemini_output.png"
                            output_path.parent.mkdir(parents=True, exist_ok=True)

                            with open(output_path, 'wb') as f:
                                f.write(inline_data.data)

                            print(f"        💾 保存: {output_path}")

                            # PIL で確認
                            from PIL import Image
                            import io
                            img = Image.open(io.BytesIO(inline_data.data))
                            print(f"        🖼️  サイズ: {img.size[0]}×{img.size[1]}px")
                            print(f"        🎨 モード: {img.mode}")

                        # text（テキスト）をチェック
                        if hasattr(part, 'text'):
                            print(f"        📝 テキスト: {part.text[:100]}")

    print("\n✅ テスト成功!")

except Exception as e:
    print(f"\n❌ エラー: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("テスト完了")
print("="*60)
