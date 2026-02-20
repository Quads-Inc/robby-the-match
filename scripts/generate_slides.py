#!/usr/bin/env python3
"""
6枚スライド一括生成スクリプト
台本JSONから6枚のスライド画像を生成
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# プロジェクトルート
project_root = Path(__file__).parent.parent

# 日本語フォント検索パス
FONT_PATHS = [
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴ ProN W6.otf",
    "/Library/Fonts/NotoSansJP-Bold.otf",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
]


def find_japanese_font(size: int):
    """日本語フォントを検索"""
    for font_path in FONT_PATHS:
        if Path(font_path).exists():
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                continue
    print("❌ 日本語フォントが見つかりません")
    sys.exit(1)


def wrap_text(text: str, font: ImageFont, max_width: int):
    """テキストを自動改行"""
    lines = []
    current_line = ""

    for char in text:
        test_line = current_line + char
        bbox = font.getbbox(test_line)
        width = bbox[2] - bbox[0]

        if width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = char

    if current_line:
        lines.append(current_line)

    return lines


def create_slide(
    base_image_path: Path,
    text: str,
    output_path: Path,
    fontsize: int,
    position: str = "center"
):
    """
    1枚のスライドを作成

    Args:
        base_image_path: ベース画像パス
        text: 焼き込むテキスト
        output_path: 出力パス
        fontsize: フォントサイズ
        position: テキスト位置
    """
    # 画像を開く
    img = Image.open(base_image_path).convert('RGB')
    width, height = img.size

    # フォント読み込み
    font = find_japanese_font(fontsize)

    # テキストを自動改行
    max_text_width = width - 80
    lines = wrap_text(text, font, max_text_width)

    # 各行の高さを計算
    line_height = fontsize + 20
    total_text_height = line_height * len(lines)

    # 位置を決定
    if position == "top":
        y_start = 200  # 上部150px避ける + マージン
    elif position == "bottom":
        y_start = height - total_text_height - 100
    else:  # center
        y_start = (height - total_text_height) // 2

    # 背景の半透明黒帯
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    bg_y_start = y_start - 40
    bg_y_end = y_start + total_text_height + 40
    overlay_draw.rectangle(
        [(0, bg_y_start), (width, bg_y_end)],
        fill=(0, 0, 0, 160)
    )

    # 合成
    img_rgba = img.convert('RGBA')
    img_with_overlay = Image.alpha_composite(img_rgba, overlay)

    # テキスト描画
    draw = ImageDraw.Draw(img_with_overlay)
    current_y = y_start

    for line in lines:
        bbox = font.getbbox(line)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        draw.text((x, current_y), line, fill="white", font=font)
        current_y += line_height

    # 保存
    final_img = img_with_overlay.convert('RGB')
    final_img.save(output_path, "PNG")


def generate_slides(json_path: Path):
    """
    台本JSONから6枚のスライドを一括生成

    Args:
        json_path: 台本JSONファイルパス
    """
    print(f"\n📦 台本読み込み: {json_path.name}")

    # JSONを読み込む
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    content_id = data.get("id", "UNKNOWN")
    slides_text = data.get("slides", [])
    base_image = data.get("base_image", "base_nurse_station.png")

    if len(slides_text) != 6:
        print(f"❌ エラー: スライド数が6枚ではありません（{len(slides_text)}枚）")
        sys.exit(1)

    print(f"   ID: {content_id}")
    print(f"   ベース画像: {base_image}")
    print(f"   スライド数: {len(slides_text)}枚")

    # ベース画像パス
    base_image_path = project_root / "content" / "base-images" / base_image
    if not base_image_path.exists():
        print(f"❌ エラー: ベース画像が見つかりません: {base_image_path}")
        sys.exit(1)

    # 出力ディレクトリ
    today = datetime.now().strftime("%Y%m%d")
    output_dir = project_root / "content" / "generated" / f"{today}_{content_id}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"   出力先: {output_dir.relative_to(project_root)}")
    print()

    # 各スライドを生成
    for i, text in enumerate(slides_text, start=1):
        output_path = output_dir / f"slide_{i}.png"

        # 1枚目: フォント160px（フック）
        # 2-6枚目: フォント128px（ストーリー・オチ）
        fontsize = 160 if i == 1 else 128

        # 1枚目は中央やや上、2-6枚目は中央
        position = "center"

        print(f"   🎨 生成中: slide_{i}.png")
        print(f"      テキスト: {text}")
        print(f"      フォントサイズ: {fontsize}px")

        create_slide(
            base_image_path=base_image_path,
            text=text,
            output_path=output_path,
            fontsize=fontsize,
            position=position
        )

        print(f"      ✅ 完了")

    print(f"\n✅ 6枚のスライド生成完了: {output_dir.relative_to(project_root)}")
    return output_dir


def main():
    parser = argparse.ArgumentParser(description="台本JSONから6枚のスライドを生成")
    parser.add_argument("--json", required=True, help="台本JSONファイルパス")

    args = parser.parse_args()
    json_path = Path(args.json)

    if not json_path.exists():
        print(f"❌ エラー: JSONファイルが見つかりません: {json_path}")
        sys.exit(1)

    output_dir = generate_slides(json_path)

    print(f"\n🎉 処理完了")
    print(f"   出力: {output_dir}")


if __name__ == "__main__":
    main()
