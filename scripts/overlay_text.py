#!/usr/bin/env python3
"""
テキスト焼き込みスクリプト
日本語テキストをベース画像に焼き込む（TikTok 9:16対応）
"""

import argparse
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# 日本語フォント検索パス（Mac）
FONT_PATHS = [
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴ ProN W6.otf",
    "/Library/Fonts/NotoSansJP-Bold.otf",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
]


def find_japanese_font(size: int = 72):
    """
    日本語フォントを検索して読み込む

    Args:
        size: フォントサイズ

    Returns:
        ImageFont: フォントオブジェクト
    """
    for font_path in FONT_PATHS:
        if Path(font_path).exists():
            try:
                font = ImageFont.truetype(font_path, size)
                print(f"✅ フォント読み込み: {Path(font_path).name}")
                return font
            except Exception as e:
                print(f"⚠️  フォント読み込み失敗: {font_path} - {e}")
                continue

    print("❌ 日本語フォントが見つかりません。")
    print("   brew install --cask font-noto-sans-cjk-jp を実行してください。")
    sys.exit(1)


def wrap_text(text: str, font: ImageFont, max_width: int):
    """
    テキストを自動改行

    Args:
        text: 改行するテキスト
        font: フォントオブジェクト
        max_width: 最大幅（px）

    Returns:
        list: 改行されたテキスト行のリスト
    """
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


def overlay_text(
    input_path: Path,
    text: str,
    output_path: Path,
    position: str = "center",
    fontsize: int = 128
):
    """
    画像にテキストを焼き込む

    Args:
        input_path: 入力画像パス
        text: 焼き込むテキスト
        output_path: 出力画像パス
        position: テキスト位置（top/center/bottom）
        fontsize: フォントサイズ
    """
    print(f"\n📝 テキスト焼き込み処理")
    print(f"   入力: {input_path.name}")
    print(f"   テキスト: {text}")
    print(f"   位置: {position}")
    print(f"   フォントサイズ: {fontsize}px")

    # 画像を開く
    img = Image.open(input_path).convert('RGB')
    width, height = img.size
    print(f"   画像サイズ: {width}×{height}px")

    # フォント読み込み
    font = find_japanese_font(fontsize)

    # テキストを自動改行（画像幅 - 80px）
    max_text_width = width - 80
    lines = wrap_text(text, font, max_text_width)
    print(f"   改行: {len(lines)}行")

    # 各行の高さを計算
    line_height = fontsize + 20  # 行間20px
    total_text_height = line_height * len(lines)

    # 位置を決定（TikTok仕様: 上部150pxは避ける）
    if position == "top":
        y_start = 200  # 上部150px + マージン50px
    elif position == "bottom":
        y_start = height - total_text_height - 100  # 下部マージン100px
    else:  # center
        y_start = (height - total_text_height) // 2

    # 背景の半透明黒帯を描画
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    # 黒帯の範囲（上下パディング40px）
    bg_y_start = y_start - 40
    bg_y_end = y_start + total_text_height + 40
    overlay_draw.rectangle(
        [(0, bg_y_start), (width, bg_y_end)],
        fill=(0, 0, 0, 160)  # RGBA: 黒、透明度160/255
    )

    # RGBA変換して合成
    img_rgba = img.convert('RGBA')
    img_with_overlay = Image.alpha_composite(img_rgba, overlay)

    # テキストを描画
    draw = ImageDraw.Draw(img_with_overlay)

    current_y = y_start
    for line in lines:
        # テキストの幅を取得（中央配置用）
        bbox = font.getbbox(line)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2

        # 白文字で描画
        draw.text((x, current_y), line, fill="white", font=font)
        current_y += line_height

    # RGB変換して保存
    final_img = img_with_overlay.convert('RGB')
    final_img.save(output_path, "PNG")

    print(f"   ✅ 保存完了: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="画像にテキストを焼き込む")
    parser.add_argument("--input", required=True, help="入力画像パス")
    parser.add_argument("--text", required=True, help="焼き込むテキスト")
    parser.add_argument("--output", required=True, help="出力画像パス")
    parser.add_argument(
        "--position",
        choices=["top", "center", "bottom"],
        default="center",
        help="テキスト位置"
    )
    parser.add_argument(
        "--fontsize",
        type=int,
        default=128,
        help="フォントサイズ（px）"
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"❌ エラー: 入力画像が見つかりません: {input_path}")
        sys.exit(1)

    # 出力ディレクトリを作成
    output_path.parent.mkdir(parents=True, exist_ok=True)

    overlay_text(
        input_path=input_path,
        text=args.text,
        output_path=output_path,
        position=args.position,
        fontsize=args.fontsize
    )

    print("\n✅ 処理完了")


if __name__ == "__main__":
    main()
