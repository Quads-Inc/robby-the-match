#!/usr/bin/env python3
"""
generate_carousel.py -- TikTok/Instagramカルーセルスライド生成エンジン v3.0

1080x1920 (9:16) のカルーセルスライドをPillowのみで生成。
外部画像素材不使用、プログラマティックデザイン。

v3.0 改善点:
  - スライド枚数を5枚（Hook + Content x3 + CTA）に最適化
  - 1枚目フック: 超大文字（120pt+）、10文字以内、完全中央配置
  - カラーパレット刷新（ピンクコーラル系 / クリーンブルー系）
  - NumPyベース高速グラデーション
  - 1行15文字x最大3行制限
  - CTA: 視認性の高い大型ボタン + パルス風リング装飾
  - 幾何学装飾（ドットグリッド、コーナーアクセント、リング、斜線）
  - コンテンツカード: 大きめ角丸 + 多層シャドウ
  - 全スライド統一カラーパレット

使い方:
  python3 scripts/generate_carousel.py --demo
  python3 scripts/generate_carousel.py --queue data/posting_queue.json --output content/generated/
"""

import argparse
import json
import math
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont, ImageFilter

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# ===========================================================================
# Constants
# ===========================================================================

CANVAS_W = 1080
CANVAS_H = 1920

# Platform-specific dimensions
PLATFORM_SIZES = {
    "tiktok": (1080, 1920),     # 9:16
    "instagram": (1080, 1350),  # 4:5 (feed)
    "instagram_story": (1080, 1920),  # 9:16 (stories/reels)
}

# TikTok UI safe zones
SAFE_TOP = 150
SAFE_BOTTOM = 250
SAFE_RIGHT = 100
SAFE_LEFT = 60

# Instagram safe zones (less restrictive)
SAFE_ZONES = {
    "tiktok": {"top": 150, "bottom": 250, "left": 60, "right": 100},
    "instagram": {"top": 60, "bottom": 60, "left": 60, "right": 60},
}

# Derived safe content area
CONTENT_X = SAFE_LEFT
CONTENT_Y = SAFE_TOP
CONTENT_W = CANVAS_W - SAFE_LEFT - SAFE_RIGHT  # 920
CONTENT_H = CANVAS_H - SAFE_TOP - SAFE_BOTTOM  # 1520

# Default slide count (Hook + 3 Content + CTA)
DEFAULT_SLIDE_COUNT = 5

# Text constraints
MAX_HOOK_CHARS = 10           # 1枚目は10文字以内
MAX_BODY_CHARS_PER_LINE = 15  # 1行15文字
MAX_BODY_LINES = 3            # 最大3行

LINE_HEIGHT_RATIO = 1.65

# ===========================================================================
# Category Color Themes v3.0
# ===========================================================================
# 看護師に響くカラーパレット: ピンクコーラル系 / クリーンブルー系

CATEGORY_THEMES = {
    "あるある": {
        "bg_primary": (255, 240, 243),       # soft pink
        "bg_secondary": (255, 220, 230),     # warm pink
        "bg_dark_top": (60, 15, 35),         # dark rose
        "bg_dark_bottom": (100, 25, 55),     # deep pink
        "accent": (255, 92, 120),            # vivid coral
        "accent_light": (255, 160, 175),     # light coral
        "accent_dark": (220, 50, 80),        # dark coral
        "card_bg": (255, 255, 255, 245),     # near-white
        "text_primary": (255, 255, 255),
        "text_on_light": (50, 20, 30),
        "text_secondary": (255, 190, 200),
        "gradient_a": (255, 107, 129),       # coral
        "gradient_b": (255, 154, 180),       # light rose
    },
    "あるある×AI": {
        "bg_primary": (255, 240, 243),
        "bg_secondary": (255, 220, 230),
        "bg_dark_top": (60, 15, 35),
        "bg_dark_bottom": (100, 25, 55),
        "accent": (255, 92, 120),
        "accent_light": (255, 160, 175),
        "accent_dark": (220, 50, 80),
        "card_bg": (255, 255, 255, 245),
        "text_primary": (255, 255, 255),
        "text_on_light": (50, 20, 30),
        "text_secondary": (255, 190, 200),
        "gradient_a": (255, 107, 129),
        "gradient_b": (255, 154, 180),
    },
    "転職・キャリア": {
        "bg_primary": (235, 245, 255),       # ice blue
        "bg_secondary": (210, 230, 255),     # soft blue
        "bg_dark_top": (15, 30, 65),         # deep navy
        "bg_dark_bottom": (30, 55, 100),     # navy
        "accent": (50, 130, 255),            # bright blue
        "accent_light": (130, 185, 255),     # sky blue
        "accent_dark": (20, 80, 200),        # deep blue
        "card_bg": (255, 255, 255, 245),
        "text_primary": (255, 255, 255),
        "text_on_light": (20, 35, 70),
        "text_secondary": (170, 210, 255),
        "gradient_a": (50, 130, 255),
        "gradient_b": (100, 200, 255),
    },
    "給与・待遇": {
        "bg_primary": (235, 250, 240),       # mint
        "bg_secondary": (210, 240, 220),     # soft green
        "bg_dark_top": (15, 40, 25),         # dark forest
        "bg_dark_bottom": (30, 65, 35),      # forest green
        "accent": (40, 180, 100),            # emerald
        "accent_light": (120, 210, 160),     # light green
        "accent_dark": (20, 130, 60),        # deep green
        "card_bg": (255, 255, 255, 245),
        "text_primary": (255, 255, 255),
        "text_on_light": (20, 50, 30),
        "text_secondary": (180, 230, 200),
        "gradient_a": (40, 180, 100),
        "gradient_b": (255, 200, 60),        # gold accent
    },
    "サービス紹介": {
        "bg_primary": (235, 245, 255),
        "bg_secondary": (215, 235, 255),
        "bg_dark_top": (12, 35, 70),         # deep navy
        "bg_dark_bottom": (5, 65, 95),       # teal navy
        "accent": (26, 120, 240),            # brand blue
        "accent_light": (100, 175, 255),
        "accent_dark": (15, 85, 190),
        "card_bg": (255, 255, 255, 245),
        "text_primary": (255, 255, 255),
        "text_on_light": (15, 40, 75),
        "text_secondary": (170, 215, 255),
        "gradient_a": (26, 120, 240),
        "gradient_b": (0, 200, 170),         # teal
    },
}

DEFAULT_THEME = CATEGORY_THEMES["あるある"]

# Common colors
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_BRAND_BLUE = (26, 120, 240)
COLOR_BRAND_TEAL = (0, 200, 170)

# Font paths
FONT_BOLD_PATH = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"
FONT_REGULAR_PATH = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"
FONT_FALLBACK_PATH = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"


# ===========================================================================
# Font loading
# ===========================================================================

_font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def load_font(bold: bool, size: int) -> ImageFont.FreeTypeFont:
    """Load a font with caching. Falls back gracefully."""
    key = ("bold" if bold else "regular", size)
    if key in _font_cache:
        return _font_cache[key]

    paths = [FONT_BOLD_PATH, FONT_FALLBACK_PATH] if bold else [FONT_REGULAR_PATH, FONT_FALLBACK_PATH]
    for p in paths:
        if Path(p).exists():
            try:
                font = ImageFont.truetype(p, size)
                _font_cache[key] = font
                return font
            except Exception:
                continue

    print("FATAL: No Japanese font found. Tried:", paths)
    sys.exit(1)


# ===========================================================================
# Text utilities
# ===========================================================================

_NO_START_CHARS = set("」）】》〉』」、。！？…ー）")


def wrap_text_jp(text: str, font: ImageFont.FreeTypeFont, max_width: int, max_chars_hint: int = 20) -> list[str]:
    """Wrap Japanese text to fit within max_width pixels."""
    paragraphs = text.split("\n")
    all_lines: list[str] = []

    for para in paragraphs:
        if not para.strip():
            all_lines.append("")
            continue

        current_line = ""
        for i, char in enumerate(para):
            test = current_line + char
            bbox = font.getbbox(test)
            w = bbox[2] - bbox[0]
            if w <= max_width:
                current_line = test
            else:
                if char in _NO_START_CHARS and current_line:
                    current_line += char
                    all_lines.append(current_line)
                    current_line = ""
                else:
                    if current_line:
                        all_lines.append(current_line)
                    current_line = char
        if current_line:
            all_lines.append(current_line)

    return all_lines


def measure_text(text: str, font: ImageFont.FreeTypeFont) -> tuple[int, int]:
    """Return (width, height) of a single line of text."""
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def text_block_height(lines: list[str], font_size: int, line_height_ratio: float = LINE_HEIGHT_RATIO) -> int:
    """Total height of a text block with line spacing."""
    if not lines:
        return 0
    line_h = int(font_size * line_height_ratio)
    return line_h * len(lines)


# ===========================================================================
# Drawing primitives
# ===========================================================================

def create_gradient(w: int, h: int, color_top: tuple, color_bottom: tuple, direction: str = "vertical") -> Image.Image:
    """Create a smooth gradient image (RGBA). Uses NumPy when available for speed."""
    if HAS_NUMPY:
        return _create_gradient_np(w, h, color_top, color_bottom, direction)
    return _create_gradient_pil(w, h, color_top, color_bottom, direction)


def _create_gradient_np(w: int, h: int, color_top: tuple, color_bottom: tuple, direction: str) -> Image.Image:
    """NumPy-accelerated gradient generation."""
    ct = np.array(color_top[:3], dtype=np.float32)
    cb = np.array(color_bottom[:3], dtype=np.float32)

    if direction == "vertical":
        ratio = np.linspace(0, 1, h, dtype=np.float32).reshape(-1, 1, 1)
        colors = ct + (cb - ct) * ratio  # (h, 1, 3)
        arr = np.broadcast_to(colors, (h, w, 3)).astype(np.uint8)
        alpha = np.full((h, w, 1), 255, dtype=np.uint8)
        rgba = np.concatenate([arr, alpha], axis=2)
    elif direction == "diagonal":
        x_ratio = np.linspace(0, 1, w, dtype=np.float32).reshape(1, -1)
        y_ratio = np.linspace(0, 1, h, dtype=np.float32).reshape(-1, 1)
        ratio = (x_ratio * 0.5 + y_ratio * 0.5).reshape(h, w, 1)
        colors = ct + (cb - ct) * ratio
        arr = colors.astype(np.uint8)
        alpha = np.full((h, w, 1), 255, dtype=np.uint8)
        rgba = np.concatenate([arr, alpha], axis=2)
    else:
        # fallback to vertical
        return _create_gradient_np(w, h, color_top, color_bottom, "vertical")

    return Image.fromarray(rgba)


def _create_gradient_pil(w: int, h: int, color_top: tuple, color_bottom: tuple, direction: str) -> Image.Image:
    """Pillow-only gradient (slower but no NumPy required)."""
    img = Image.new("RGBA", (w, h))
    pixels = img.load()

    if direction == "vertical":
        for y in range(h):
            ratio = y / max(h - 1, 1)
            r = int(color_top[0] + (color_bottom[0] - color_top[0]) * ratio)
            g = int(color_top[1] + (color_bottom[1] - color_top[1]) * ratio)
            b = int(color_top[2] + (color_bottom[2] - color_top[2]) * ratio)
            for x in range(w):
                pixels[x, y] = (r, g, b, 255)
    elif direction == "diagonal":
        for y in range(h):
            for x in range(w):
                ratio = (x / max(w - 1, 1) * 0.5 + y / max(h - 1, 1) * 0.5)
                r = int(color_top[0] + (color_bottom[0] - color_top[0]) * ratio)
                g = int(color_top[1] + (color_bottom[1] - color_top[1]) * ratio)
                b = int(color_top[2] + (color_bottom[2] - color_top[2]) * ratio)
                pixels[x, y] = (r, g, b, 255)

    return img


def draw_text_shadow(
    draw: ImageDraw.ImageDraw,
    x: int, y: int,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple = COLOR_WHITE,
    shadow_color: tuple = (0, 0, 0, 100),
    shadow_offset: int = 4,
    outline: bool = True,
    outline_color: tuple = (0, 0, 0, 140),
    outline_width: int = 2,
):
    """Draw text with drop shadow + optional outline for maximum readability."""
    # Shadow
    draw.text((x + shadow_offset, y + shadow_offset), text, fill=shadow_color, font=font)
    # Outline
    if outline:
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx == 0 and dy == 0:
                    continue
                draw.text((x + dx, y + dy), text, fill=outline_color, font=font)
    # Main text
    draw.text((x, y), text, fill=fill, font=font)


def draw_centered_text_block(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: ImageFont.FreeTypeFont,
    font_size: int,
    center_x: int,
    start_y: int,
    fill: tuple = COLOR_WHITE,
    shadow: bool = False,
    shadow_color: tuple = (0, 0, 0, 100),
    shadow_offset: int = 4,
    line_height_ratio: float = LINE_HEIGHT_RATIO,
) -> int:
    """Draw multiple lines centered. Returns Y after last line."""
    line_h = int(font_size * line_height_ratio)
    cy = start_y
    for line in lines:
        tw, _ = measure_text(line, font)
        tx = center_x - tw // 2
        if shadow:
            draw_text_shadow(draw, tx, cy, line, font, fill=fill,
                             shadow_color=shadow_color, shadow_offset=shadow_offset)
        else:
            draw.text((tx, cy), line, fill=fill, font=font)
        cy += line_h
    return cy


# ===========================================================================
# Decorative elements v3.0
# ===========================================================================

def _draw_dot_grid(draw: ImageDraw.ImageDraw, theme: dict, alpha: int = 15, spacing: int = 60):
    """Draw a subtle dot grid pattern across the canvas."""
    color = (*theme["accent"][:3], alpha)
    for y in range(0, CANVAS_H, spacing):
        for x in range(0, CANVAS_W, spacing):
            r = 2
            draw.ellipse((x - r, y - r, x + r, y + r), fill=color)


def _draw_corner_accents(draw: ImageDraw.ImageDraw, theme: dict, alpha: int = 40):
    """Draw decorative corner accent lines."""
    color = (*theme["accent"][:3], alpha)
    length = 120
    thickness = 3
    margin = 40

    # Top-left
    draw.line([(margin, margin), (margin + length, margin)], fill=color, width=thickness)
    draw.line([(margin, margin), (margin, margin + length)], fill=color, width=thickness)

    # Top-right
    draw.line([(CANVAS_W - margin, margin), (CANVAS_W - margin - length, margin)], fill=color, width=thickness)
    draw.line([(CANVAS_W - margin, margin), (CANVAS_W - margin, margin + length)], fill=color, width=thickness)

    # Bottom-left
    draw.line([(margin, CANVAS_H - margin), (margin + length, CANVAS_H - margin)], fill=color, width=thickness)
    draw.line([(margin, CANVAS_H - margin), (margin, CANVAS_H - margin - length)], fill=color, width=thickness)

    # Bottom-right
    draw.line([(CANVAS_W - margin, CANVAS_H - margin), (CANVAS_W - margin - length, CANVAS_H - margin)], fill=color, width=thickness)
    draw.line([(CANVAS_W - margin, CANVAS_H - margin), (CANVAS_W - margin, CANVAS_H - margin - length)], fill=color, width=thickness)


def _draw_decorative_rings(img: Image.Image, theme: dict, count: int = 3, alpha: int = 12):
    """Draw decorative translucent rings on the image."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    accent = theme["accent"]

    positions = [
        (CANVAS_W * 0.85, CANVAS_H * 0.15, 180),
        (CANVAS_W * 0.1, CANVAS_H * 0.7, 140),
        (CANVAS_W * 0.75, CANVAS_H * 0.85, 100),
    ]

    for i in range(min(count, len(positions))):
        cx, cy, radius = positions[i]
        cx, cy, radius = int(cx), int(cy), int(radius)
        ring_color = (*accent[:3], alpha)
        for t in range(3):  # ring thickness
            r = radius + t * 3
            d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=ring_color, width=2)

    return Image.alpha_composite(img, overlay)


def _draw_diagonal_stripes(img: Image.Image, theme: dict, alpha: int = 8):
    """Draw subtle diagonal stripe pattern."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    color = (*theme["accent_light"][:3], alpha)
    spacing = 80

    for offset in range(-CANVAS_H, CANVAS_W + CANVAS_H, spacing):
        d.line([(offset, 0), (offset + CANVAS_H, CANVAS_H)], fill=color, width=1)

    return Image.alpha_composite(img, overlay)


# ===========================================================================
# Background builders v3.0
# ===========================================================================

def _build_dark_bg(theme: dict) -> Image.Image:
    """Dark gradient background with glow and decorative elements."""
    bg = create_gradient(CANVAS_W, CANVAS_H, theme["bg_dark_top"], theme["bg_dark_bottom"])

    # Radial glow from center-top
    glow = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    accent = theme["accent"]
    cx, cy = CANVAS_W // 2, CANVAS_H // 4
    for r in range(500, 0, -8):
        a = max(1, int(10 * (1 - r / 500)))
        glow_draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*accent[:3], a))
    bg = Image.alpha_composite(bg, glow)

    # Decorative elements
    bg = _draw_diagonal_stripes(bg, theme, alpha=6)
    bg = _draw_decorative_rings(bg, theme, count=2, alpha=10)

    draw = ImageDraw.Draw(bg)
    _draw_corner_accents(draw, theme, alpha=30)

    return bg


def _build_light_bg(theme: dict) -> Image.Image:
    """Light, clean background with subtle color tint."""
    bg = create_gradient(CANVAS_W, CANVAS_H, theme["bg_primary"], theme["bg_secondary"])

    # Top accent strip
    draw = ImageDraw.Draw(bg)
    draw.rectangle([(0, 0), (CANVAS_W, 5)], fill=(*theme["accent"][:3], 140))

    # Subtle dot grid
    _draw_dot_grid(draw, theme, alpha=12, spacing=80)

    # Corner accents (lighter)
    _draw_corner_accents(draw, theme, alpha=25)

    return bg


def _build_accent_gradient_bg(theme: dict) -> Image.Image:
    """Bold accent gradient for reveal/emphasis slides."""
    bg = create_gradient(CANVAS_W, CANVAS_H, theme["gradient_a"], theme["gradient_b"], direction="diagonal")
    bg = _draw_decorative_rings(bg, theme, count=3, alpha=20)
    return bg


def _build_brand_gradient_bg() -> Image.Image:
    """Brand gradient (blue-to-teal) for CTA slide."""
    bg = create_gradient(CANVAS_W, CANVAS_H, COLOR_BRAND_BLUE, COLOR_BRAND_TEAL, direction="diagonal")

    # Glow
    glow = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    cx, cy = CANVAS_W // 2, CANVAS_H // 2
    for r in range(600, 0, -10):
        a = max(1, int(6 * (1 - r / 600)))
        gd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, a))
    bg = Image.alpha_composite(bg, glow)

    # Rings
    bg = _draw_decorative_rings(
        bg,
        {"accent": (255, 255, 255), "accent_light": (200, 230, 255)},
        count=3, alpha=15,
    )

    return bg


# ===========================================================================
# Slide indicators v3.0
# ===========================================================================

def _draw_slide_indicator(draw: ImageDraw.ImageDraw, current: int, total: int, light_bg: bool = False):
    """Draw slide progress dots at the top."""
    dot_r = 6
    dot_gap = 20
    total_w = total * (dot_r * 2) + (total - 1) * dot_gap
    start_x = (CANVAS_W - total_w) // 2
    y = SAFE_TOP + 30

    for i in range(total):
        cx = start_x + i * (dot_r * 2 + dot_gap) + dot_r
        if i + 1 == current:
            # Active dot (filled, larger)
            if light_bg:
                fill = (*DEFAULT_THEME["accent"][:3], 220)
            else:
                fill = (255, 255, 255, 240)
            draw.ellipse((cx - dot_r - 2, y - dot_r - 2, cx + dot_r + 2, y + dot_r + 2), fill=fill)
        else:
            # Inactive dot
            if light_bg:
                fill = (0, 0, 0, 30)
            else:
                fill = (255, 255, 255, 50)
            draw.ellipse((cx - dot_r, y - dot_r, cx + dot_r, y + dot_r), fill=fill)


def _draw_brand_watermark(draw: ImageDraw.ImageDraw, light_bg: bool = False):
    """Draw subtle brand watermark."""
    font = load_font(bold=False, size=22)
    text = "@robby15051"
    tw, _ = measure_text(text, font)
    x = (CANVAS_W - tw) // 2
    y = CANVAS_H - SAFE_BOTTOM + 15
    color = (0, 0, 0, 35) if light_bg else (255, 255, 255, 35)
    draw.text((x, y), text, fill=color, font=font)


# ===========================================================================
# Slide generators v3.0
# ===========================================================================

def generate_slide_hook(
    hook_text: str,
    theme: dict,
    total_slides: int = DEFAULT_SLIDE_COUNT,
) -> Image.Image:
    """
    Slide 1 - HOOK: Massive text, center of screen.
    Goal: 3-second stop-scroll. 10 chars max, 120pt+ font.
    Dark bg with accent glow behind text.
    """
    bg = _build_dark_bg(theme)
    draw = ImageDraw.Draw(bg)
    accent = theme["accent"]
    center_x = CANVAS_W // 2

    # -- Compute font size for hook --
    # Target: as large as possible, filling ~50% of screen height
    hook_zone_top = SAFE_TOP + 200
    hook_zone_height = int(CONTENT_H * 0.50)
    max_text_width = CONTENT_W - 60

    best_font_size = 60
    best_lines = [hook_text]
    for size in range(140, 56, -2):
        font = load_font(bold=True, size=size)
        lines = wrap_text_jp(hook_text, font, max_text_width, MAX_HOOK_CHARS)
        block_h = text_block_height(lines, size)
        if block_h <= hook_zone_height and len(lines) <= 4:
            best_font_size = size
            best_lines = lines
            break
    else:
        font = load_font(bold=True, size=60)
        best_font_size = 60
        best_lines = wrap_text_jp(hook_text, font, max_text_width, MAX_HOOK_CHARS)

    font = load_font(bold=True, size=best_font_size)
    block_h = text_block_height(best_lines, best_font_size)

    # Center vertically
    text_y = hook_zone_top + (hook_zone_height - block_h) // 2

    # -- Accent glow behind text --
    glow_layer = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    glow_cy = text_y + block_h // 2
    for r in range(400, 0, -6):
        a = max(1, int(18 * (1 - r / 400)))
        gd.ellipse((center_x - r, glow_cy - r, center_x + r, glow_cy + r),
                    fill=(*accent[:3], a))
    bg = Image.alpha_composite(bg, glow_layer)
    draw = ImageDraw.Draw(bg)

    # -- Draw hook text --
    draw_centered_text_block(
        draw, best_lines, font, best_font_size,
        center_x, text_y,
        fill=COLOR_WHITE,
        shadow=True,
        shadow_offset=5,
        shadow_color=(0, 0, 0, 160),
    )

    # -- Accent underline --
    underline_y = text_y + block_h + 50
    underline_w = min(400, CONTENT_W - 100)
    underline_x = center_x - underline_w // 2
    draw.rounded_rectangle(
        (underline_x, underline_y, underline_x + underline_w, underline_y + 6),
        radius=3, fill=(*accent[:3], 180),
    )

    # -- Swipe hint --
    hint_font = load_font(bold=True, size=30)
    hint_text = ">>> スワイプ"
    tw, _ = measure_text(hint_text, hint_font)
    hint_x = center_x - tw // 2
    hint_y = CANVAS_H - SAFE_BOTTOM - 90
    draw.text((hint_x, hint_y), hint_text, fill=(*accent[:3], 140), font=hint_font)

    # -- Indicators --
    _draw_slide_indicator(draw, 1, total_slides, light_bg=False)
    _draw_brand_watermark(draw, light_bg=False)

    return bg.convert("RGB")


def generate_slide_content(
    slide_num: int,
    title: str,
    body: str,
    highlight_number: Optional[str] = None,
    highlight_label: Optional[str] = None,
    dark_theme: bool = True,
    theme: dict = None,
    total_slides: int = DEFAULT_SLIDE_COUNT,
) -> Image.Image:
    """
    Slides 2-4 - CONTENT: Card-based layout.
    Title at top, body in rounded card with left accent bar.
    Alternating dark/light backgrounds.
    """
    if theme is None:
        theme = DEFAULT_THEME
    accent = theme["accent"]

    bg = _build_dark_bg(theme) if dark_theme else _build_light_bg(theme)
    draw = ImageDraw.Draw(bg)
    light_bg = not dark_theme
    center_x = CANVAS_W // 2
    max_text_width = CONTENT_W - 80

    # ============================================================
    # PASS 1: Pre-calculate total content height for vertical centering
    # ============================================================
    title_font_size = 52
    title_font = load_font(bold=True, size=title_font_size)
    title_lines = wrap_text_jp(title, title_font, max_text_width)
    title_block_h = len(title_lines) * int(title_font_size * 1.5) + 30  # + gap

    hl_block_h = 0
    if highlight_number:
        num_font_size = 96
        hl_block_h += int(num_font_size * 1.3)
        if highlight_label:
            hl_block_h += 55
        else:
            hl_block_h += 35

    # Pre-calculate card dimensions
    card_margin = 25
    card_x0 = SAFE_LEFT + card_margin
    card_x1 = CANVAS_W - SAFE_RIGHT - card_margin
    card_inner_pad = 35

    body_font_size = 40
    body_paragraphs = body.split("\n")

    # Estimate body height
    total_lines_est = 0
    for para in body_paragraphs:
        para = para.strip()
        if not para:
            total_lines_est += 0.5
            continue
        total_lines_est += max(1, len(para) / 12)

    max_card_height = CONTENT_H - title_block_h - hl_block_h - 80  # leave margin
    estimated_card_height = int(total_lines_est * body_font_size * LINE_HEIGHT_RATIO) + card_inner_pad * 2 + 10

    if estimated_card_height > max_card_height:
        for try_size in range(38, 26, -2):
            est_h = int(total_lines_est * try_size * LINE_HEIGHT_RATIO) + card_inner_pad * 2 + 10
            if est_h <= max_card_height:
                body_font_size = try_size
                break
        else:
            body_font_size = 28

    body_font = load_font(bold=False, size=body_font_size)
    line_h = int(body_font_size * LINE_HEIGHT_RATIO)

    # Exact card height calculation
    card_content_h = 0
    for para in body_paragraphs:
        para = para.strip()
        if not para:
            card_content_h += line_h // 2
            continue
        is_bullet = para.startswith(("・", "- ", "* "))
        if is_bullet:
            clean = para.lstrip("・- *").strip()
            lines = wrap_text_jp(clean, body_font, card_x1 - card_x0 - card_inner_pad * 2 - 60)
            card_content_h += line_h * len(lines) + 14
        else:
            lines = wrap_text_jp(para, body_font, card_x1 - card_x0 - card_inner_pad * 2)
            card_content_h += line_h * len(lines) + 10

    actual_card_h = card_inner_pad * 2 + card_content_h + 10

    # Total content height
    total_content_h = title_block_h + hl_block_h + actual_card_h

    # ============================================================
    # PASS 2: Draw everything, vertically centered
    # ============================================================
    # Center the entire content block in the safe area
    start_y = SAFE_TOP + max(60, (CONTENT_H - total_content_h) // 2)
    current_y = start_y

    # -- Section title --
    title_color = COLOR_WHITE if dark_theme else theme["text_on_light"]

    # Accent dot
    dot_y = current_y + title_font_size // 2
    draw.ellipse(
        (SAFE_LEFT + 20, dot_y - 10, SAFE_LEFT + 40, dot_y + 10),
        fill=(*accent[:3], 255),
    )

    # Title text
    title_x = SAFE_LEFT + 55
    for tl in title_lines:
        if dark_theme:
            draw_text_shadow(draw, title_x, current_y, tl, title_font,
                             fill=title_color, shadow_offset=2, outline_width=1)
        else:
            draw.text((title_x, current_y), tl, fill=title_color, font=title_font)
        current_y += int(title_font_size * 1.5)

    current_y += 25

    # -- Highlight number --
    if highlight_number:
        num_font_size = 96
        num_font = load_font(bold=True, size=num_font_size)
        tw, _ = measure_text(highlight_number, num_font)
        nx = center_x - tw // 2

        if dark_theme:
            draw_text_shadow(draw, nx, current_y, highlight_number, num_font,
                             fill=(*accent[:3], 255), shadow_offset=4, outline_width=2)
        else:
            draw.text((nx, current_y), highlight_number, fill=(*accent[:3], 255), font=num_font)

        current_y += int(num_font_size * 1.3)

        if highlight_label:
            label_font = load_font(bold=False, size=28)
            tw2, _ = measure_text(highlight_label, label_font)
            lx = center_x - tw2 // 2
            label_color = theme["text_secondary"] if dark_theme else (120, 120, 120)
            draw.text((lx, current_y), highlight_label, fill=label_color, font=label_font)
            current_y += 55
        else:
            current_y += 35

    # -- Body text in card --
    card_top = current_y
    max_body_y = CANVAS_H - SAFE_BOTTOM - 70
    card_bottom = min(card_top + actual_card_h, max_body_y)

    # -- Draw card (multi-layer shadow for depth) --
    if dark_theme:
        shadow_layer = Image.new("RGBA", bg.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow_layer)
        sd.rounded_rectangle(
            (card_x0 + 8, card_top + 10, card_x1 + 8, card_bottom + 10),
            radius=28, fill=(0, 0, 0, 25),
        )
        sd.rounded_rectangle(
            (card_x0 + 4, card_top + 5, card_x1 + 4, card_bottom + 5),
            radius=28, fill=(0, 0, 0, 35),
        )
        bg = Image.alpha_composite(bg, shadow_layer)
        draw = ImageDraw.Draw(bg)

        card_fill = (255, 255, 255, 20)
    else:
        shadow_layer = Image.new("RGBA", bg.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow_layer)
        sd.rounded_rectangle(
            (card_x0 + 5, card_top + 6, card_x1 + 5, card_bottom + 6),
            radius=28, fill=(0, 0, 0, 15),
        )
        bg = Image.alpha_composite(bg, shadow_layer)
        draw = ImageDraw.Draw(bg)

        card_fill = (255, 255, 255, 240)

    # Card body
    draw.rounded_rectangle(
        (card_x0, card_top, card_x1, card_bottom),
        radius=28, fill=card_fill,
    )

    # Card border
    if dark_theme:
        draw.rounded_rectangle(
            (card_x0, card_top, card_x1, card_bottom),
            radius=28, fill=None, outline=(*accent[:3], 35), width=1,
        )

    # Left accent bar
    draw.rounded_rectangle(
        (card_x0, card_top + 28, card_x0 + 7, card_bottom - 28),
        radius=3, fill=(*accent[:3], 200),
    )

    # -- Draw body text --
    current_y = card_top + card_inner_pad
    body_left = card_x0 + card_inner_pad + 12
    body_max_w = card_x1 - card_x0 - card_inner_pad * 2 - 12
    body_color = COLOR_WHITE if dark_theme else theme["text_on_light"]

    for para in body_paragraphs:
        para = para.strip()
        if not para:
            current_y += line_h // 2
            continue
        if current_y >= max_body_y - line_h:
            break

        is_bullet = para.startswith(("・", "- ", "* "))
        if is_bullet:
            clean_text = para.lstrip("・- *").strip()
            text_start_x = body_left + 50
            text_max_w = body_max_w - 60

            lines = wrap_text_jp(clean_text, body_font, text_max_w)

            # Bullet marker
            marker_x = body_left + 10
            marker_y = current_y + body_font_size // 2
            draw.ellipse(
                (marker_x, marker_y - 7, marker_x + 14, marker_y + 7),
                fill=(*accent[:3], 220),
            )

            for line in lines:
                if current_y >= max_body_y - line_h:
                    break
                if dark_theme:
                    draw_text_shadow(draw, text_start_x, current_y, line, body_font,
                                     fill=body_color, shadow_offset=1, outline_width=1)
                else:
                    draw.text((text_start_x, current_y), line, fill=body_color, font=body_font)
                current_y += line_h
            current_y += 14
        else:
            lines = wrap_text_jp(para, body_font, body_max_w)
            for line in lines:
                if current_y >= max_body_y - line_h:
                    break
                if dark_theme:
                    draw_text_shadow(draw, body_left, current_y, line, body_font,
                                     fill=body_color, shadow_offset=1, outline_width=1)
                else:
                    draw.text((body_left, current_y), line, fill=body_color, font=body_font)
                current_y += line_h
            current_y += 10

    # -- Indicators --
    _draw_slide_indicator(draw, slide_num, total_slides, light_bg=light_bg)
    _draw_brand_watermark(draw, light_bg=light_bg)

    return bg.convert("RGB")


def generate_slide_cta(
    cta_type: str = "soft",
    theme: dict = None,
    total_slides: int = DEFAULT_SLIDE_COUNT,
) -> Image.Image:
    """
    Final slide - CTA: Brand gradient background.
    Large CTA button with pulse-ring decoration.
    Soft: save/follow. Hard: LINE invitation.
    """
    if theme is None:
        theme = DEFAULT_THEME

    bg = _build_brand_gradient_bg()
    draw = ImageDraw.Draw(bg)
    center_x = CANVAS_W // 2

    # -- Brand logo --
    logo_font_size = 64
    logo_font = load_font(bold=True, size=logo_font_size)
    logo_text = "ナースロビー"
    tw, _ = measure_text(logo_text, logo_font)
    logo_x = center_x - tw // 2
    logo_y = SAFE_TOP + 140

    draw_text_shadow(
        draw, logo_x, logo_y, logo_text, logo_font,
        fill=COLOR_WHITE, shadow_offset=3,
    )

    # -- English tagline --
    tag_font = load_font(bold=False, size=28)
    tag_text = "NURSE ROBBY"
    tw, _ = measure_text(tag_text, tag_font)
    tag_x = center_x - tw // 2
    tag_y = logo_y + logo_font_size + 18
    draw.text((tag_x, tag_y), tag_text, fill=(*COLOR_WHITE[:3], 150), font=tag_font)

    # -- Separator line --
    sep_y = tag_y + 65
    sep_w = 180
    draw.rounded_rectangle(
        (center_x - sep_w // 2, sep_y, center_x + sep_w // 2, sep_y + 3),
        radius=2, fill=(*COLOR_WHITE[:3], 70),
    )

    if cta_type == "hard":
        # === Hard CTA: LINE invitation ===

        # Badge: 手数料10%
        badge_y = sep_y + 60
        badge_font = load_font(bold=True, size=32)
        badge_text = "紹介手数料 業界最安10%"
        btw, bth = measure_text(badge_text, badge_font)
        badge_pad_x = 45
        badge_pad_y = 20
        badge_w = btw + badge_pad_x * 2
        badge_h = bth + badge_pad_y * 2
        badge_x = center_x - badge_w // 2

        draw.rounded_rectangle(
            (badge_x, badge_y, badge_x + badge_w, badge_y + badge_h),
            radius=badge_h // 2,
            fill=(*COLOR_WHITE[:3], 35),
            outline=(*COLOR_WHITE[:3], 160), width=2,
        )
        draw_text_shadow(
            draw, badge_x + badge_pad_x, badge_y + badge_pad_y,
            badge_text, badge_font, fill=COLOR_WHITE,
            shadow_offset=1, outline_width=1,
        )

        # CTA Button: "LINEで無料相談"
        btn_y = badge_y + badge_h + 80
        btn_font = load_font(bold=True, size=42)
        btn_text = "LINEで無料相談"
        btw2, bth2 = measure_text(btn_text, btn_font)
        btn_pad_x = 70
        btn_pad_y = 32
        btn_w = btw2 + btn_pad_x * 2
        btn_h = bth2 + btn_pad_y * 2
        btn_x = center_x - btn_w // 2

        # Pulse rings behind button
        pulse_layer = Image.new("RGBA", bg.size, (0, 0, 0, 0))
        pd = ImageDraw.Draw(pulse_layer)
        btn_cx = center_x
        btn_cy = btn_y + btn_h // 2
        for ring_i in range(4):
            ring_r = btn_w // 2 + 20 + ring_i * 25
            ring_a = max(5, 30 - ring_i * 8)
            pd.ellipse(
                (btn_cx - ring_r, btn_cy - ring_r, btn_cx + ring_r, btn_cy + ring_r),
                outline=(255, 255, 255, ring_a), width=2,
            )
        bg = Image.alpha_composite(bg, pulse_layer)
        draw = ImageDraw.Draw(bg)

        # Button shadow
        draw.rounded_rectangle(
            (btn_x + 4, btn_y + 5, btn_x + btn_w + 4, btn_y + btn_h + 5),
            radius=btn_h // 2, fill=(0, 0, 0, 30),
        )
        # Button
        draw.rounded_rectangle(
            (btn_x, btn_y, btn_x + btn_w, btn_y + btn_h),
            radius=btn_h // 2, fill=COLOR_WHITE,
        )
        draw.text(
            (btn_x + btn_pad_x, btn_y + btn_pad_y),
            btn_text, fill=COLOR_BRAND_BLUE, font=btn_font,
        )

        # Sub text
        sub_y = btn_y + btn_h + 45
        sub_font = load_font(bold=False, size=28)
        sub_text = "プロフィールのリンクから"
        tw, _ = measure_text(sub_text, sub_font)
        draw.text((center_x - tw // 2, sub_y), sub_text, fill=(*COLOR_WHITE[:3], 170), font=sub_font)

        # Trust indicators
        trust_y = sub_y + 70
        _draw_trust_badges(draw, center_x, trust_y)

    else:
        # === Soft CTA: Save + Follow ===

        # "保存してね" button
        save_y = sep_y + 80
        save_font = load_font(bold=True, size=46)
        save_text = "保存してね"
        stw, sth = measure_text(save_text, save_font)
        save_pad_x = 60
        save_pad_y = 28
        save_w = stw + save_pad_x * 2
        save_h = sth + save_pad_y * 2
        save_x = center_x - save_w // 2

        # Pulse rings
        pulse_layer = Image.new("RGBA", bg.size, (0, 0, 0, 0))
        pd = ImageDraw.Draw(pulse_layer)
        save_cx = center_x
        save_cy = save_y + save_h // 2
        for ring_i in range(3):
            ring_r = save_w // 2 + 15 + ring_i * 22
            ring_a = max(5, 25 - ring_i * 8)
            pd.ellipse(
                (save_cx - ring_r, save_cy - ring_r, save_cx + ring_r, save_cy + ring_r),
                outline=(255, 255, 255, ring_a), width=2,
            )
        bg = Image.alpha_composite(bg, pulse_layer)
        draw = ImageDraw.Draw(bg)

        # Button shadow
        draw.rounded_rectangle(
            (save_x + 4, save_y + 5, save_x + save_w + 4, save_y + save_h + 5),
            radius=save_h // 2, fill=(0, 0, 0, 25),
        )
        # Button
        draw.rounded_rectangle(
            (save_x, save_y, save_x + save_w, save_y + save_h),
            radius=save_h // 2, fill=COLOR_WHITE,
        )
        draw.text(
            (save_x + save_pad_x, save_y + save_pad_y),
            save_text, fill=COLOR_BRAND_BLUE, font=save_font,
        )

        # Follow text
        follow_y = save_y + save_h + 60
        follow_font = load_font(bold=True, size=36)
        follow_text = "フォローで最新情報をチェック"
        tw, _ = measure_text(follow_text, follow_font)
        draw.text((center_x - tw // 2, follow_y), follow_text, fill=COLOR_WHITE, font=follow_font)

        # Subtitle
        prof_y = follow_y + 65
        prof_font = load_font(bold=False, size=28)
        prof_text = "神奈川県西部の看護師転職"
        ptw, _ = measure_text(prof_text, prof_font)
        draw.text((center_x - ptw // 2, prof_y), prof_text, fill=(*COLOR_WHITE[:3], 150), font=prof_font)

        # Trust indicators
        trust_y = prof_y + 70
        _draw_trust_badges(draw, center_x, trust_y)

    _draw_slide_indicator(draw, total_slides, total_slides, light_bg=False)
    _draw_brand_watermark(draw, light_bg=False)

    return bg.convert("RGB")


def _draw_trust_badges(draw: ImageDraw.ImageDraw, center_x: int, y: int):
    """Draw trust indicator badges at the bottom."""
    badge_font = load_font(bold=False, size=24)
    check_font = load_font(bold=True, size=24)
    items = ["有料職業紹介許可", "完全無料", "LINEで簡単相談"]

    check_text = "+"
    check_w, _ = measure_text(check_text, check_font)
    gap = 28
    total_w = 0
    item_widths = []
    for item in items:
        itw, _ = measure_text(item, badge_font)
        item_widths.append(itw)
        total_w += check_w + 8 + itw

    total_w += gap * (len(items) - 1)
    start_x = center_x - total_w // 2

    cx_pos = start_x
    for i, item in enumerate(items):
        draw.text((cx_pos, y), check_text, fill=(100, 255, 210), font=check_font)
        cx_pos += check_w + 8
        draw.text((cx_pos, y + 1), item, fill=(*COLOR_WHITE[:3], 190), font=badge_font)
        cx_pos += item_widths[i] + gap


# ===========================================================================
# Main carousel generator v3.0
# ===========================================================================

def generate_carousel(
    content_id: str,
    hook: str,
    slides: list[dict],
    output_dir: str,
    category: str = "あるある",
    cta_type: str = "soft",
    reveal: dict = None,   # kept for backward compat, merged into last content slide
) -> list[str]:
    """
    Generate a 5-slide carousel set (Hook + 3 Content + CTA).

    Args:
        content_id: Unique ID (e.g. "A01")
        hook: Text for slide 1 (10 chars ideal)
        slides: List of dicts for content slides:
                [{title, body, highlight_number?, highlight_label?}, ...]
                Up to 3 slides used. If 4+ provided, last is merged or truncated.
        output_dir: Directory to save PNG files
        category: Content category for color scheme
        cta_type: "soft" or "hard"
        reveal: (backward compat) If provided, appended as last content slide

    Returns:
        List of saved PNG file paths
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    theme = CATEGORY_THEMES.get(category, DEFAULT_THEME)

    # Merge reveal into slides if provided (backward compat)
    content_slides = list(slides)
    if reveal and reveal.get("text"):
        reveal_title = reveal.get("text", "")
        reveal_body = ""
        if reveal.get("number"):
            reveal_body = reveal["number"]
            if reveal.get("label"):
                reveal_body += "\n" + reveal["label"]
        content_slides.append({
            "title": reveal_title,
            "body": reveal_body,
            "highlight_number": reveal.get("number"),
            "highlight_label": reveal.get("label"),
        })

    # Limit to 3 content slides for 5-slide total
    content_slides = content_slides[:3]

    total_slides_count = 1 + len(content_slides) + 1  # Hook + Content + CTA
    saved_paths: list[str] = []

    print(f"  [{content_id}] Generating {total_slides_count}-slide carousel (category: {category})")

    # --- Slide 1: HOOK ---
    img1 = generate_slide_hook(hook, theme=theme, total_slides=total_slides_count)
    p1 = out / f"{content_id}_slide_01_hook.png"
    img1.save(str(p1), "PNG", quality=95)
    saved_paths.append(str(p1))
    print(f"    slide 01 (HOOK): {hook[:30]}...")

    # --- Slides 2-4: CONTENT (alternating dark/light) ---
    for i, slide_data in enumerate(content_slides):
        slide_num = i + 2
        dark = (i % 2 == 0)  # 2=dark, 3=light, 4=dark

        title = slide_data.get("title", "")
        body = slide_data.get("body", "")
        hl_num = slide_data.get("highlight_number")
        hl_label = slide_data.get("highlight_label")

        img = generate_slide_content(
            slide_num=slide_num,
            title=title,
            body=body,
            highlight_number=hl_num,
            highlight_label=hl_label,
            dark_theme=dark,
            theme=theme,
            total_slides=total_slides_count,
        )
        p = out / f"{content_id}_slide_{slide_num:02d}_content.png"
        img.save(str(p), "PNG", quality=95)
        saved_paths.append(str(p))
        print(f"    slide {slide_num:02d} (CONTENT {'dark' if dark else 'light'}): {title[:30]}...")

    # --- Final slide: CTA ---
    cta_slide_num = total_slides_count
    img_cta = generate_slide_cta(cta_type=cta_type, theme=theme, total_slides=total_slides_count)
    p_cta = out / f"{content_id}_slide_{cta_slide_num:02d}_cta.png"
    img_cta.save(str(p_cta), "PNG", quality=95)
    saved_paths.append(str(p_cta))
    print(f"    slide {cta_slide_num:02d} (CTA: {cta_type})")

    print(f"  [{content_id}] Done: {len(saved_paths)} slides saved to {out}")
    return saved_paths


# ===========================================================================
# Queue integration
# ===========================================================================

def _split_title_body(text: str) -> tuple[str, str]:
    """Split a slide text into a short title and longer body."""
    MAX_TITLE = 18

    if "\n" in text:
        parts = text.split("\n", 1)
        candidate = parts[0].strip()
        if len(candidate) <= MAX_TITLE:
            return candidate, parts[1].strip()

    if "。" in text:
        parts = text.split("。", 1)
        candidate = parts[0].strip()
        if len(candidate) <= MAX_TITLE:
            return candidate + "。", parts[1].strip()

    for delim in ["、", "。", "？", "！", "…", ","]:
        if delim in text:
            parts = text.split(delim, 1)
            candidate = parts[0].strip()
            if len(candidate) <= MAX_TITLE:
                return candidate + delim, parts[1].strip()

    if len(text) > MAX_TITLE:
        return text[:MAX_TITLE] + "...", text

    return text, ""


def _extract_carousel_content(json_path: str) -> Optional[dict]:
    """Extract carousel content from a slide JSON file."""
    path = Path(json_path)
    if not path.exists():
        print(f"  WARNING: JSON not found: {json_path}")
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"  WARNING: Cannot parse {json_path}: {e}")
        return None

    content_id = data.get("content_id", data.get("id", path.stem))
    category = data.get("category", "あるある")
    cta_type = data.get("cta_type", "soft")
    raw_slides = data.get("slides", [])

    if not raw_slides:
        print(f"  WARNING: No slides in {json_path}")
        return None

    slide_texts: list[str] = []
    if isinstance(raw_slides[0], str):
        slide_texts = [s.strip() for s in raw_slides]
    elif isinstance(raw_slides[0], dict):
        for s in raw_slides:
            text = s.get("text", "")
            subtext = s.get("subtext", "")
            if subtext:
                slide_texts.append(f"{text}\n{subtext}")
            else:
                slide_texts.append(text.strip())

    if len(slide_texts) < 2:
        print(f"  WARNING: Need at least 2 slides, got {len(slide_texts)} in {json_path}")
        return None

    hook = data.get("hook", slide_texts[0])

    # Build content slides (up to 3 for 5-slide format)
    middle = slide_texts[1:]
    content_slides: list[dict] = []
    for i in range(min(3, len(middle))):
        text = middle[i]
        title, body = _split_title_body(text)
        content_slides.append({"title": title, "body": body})

    # If no content slides, create at least one
    if not content_slides:
        content_slides.append({"title": "...", "body": "..."})

    return {
        "content_id": content_id,
        "hook": hook,
        "slides": content_slides,
        "category": category,
        "cta_type": cta_type,
    }


def generate_from_queue(queue_path: str, output_base: str) -> int:
    """Read posting_queue.json, generate carousel slides for pending items."""
    qpath = Path(queue_path)
    if not qpath.exists():
        print(f"ERROR: Queue file not found: {queue_path}")
        return 0

    with open(qpath, "r", encoding="utf-8") as f:
        queue = json.load(f)

    posts = queue.get("posts", [])
    pending = [p for p in posts if p.get("status") in ("pending", "failed")]

    if not pending:
        print("No pending posts in queue.")
        return 0

    print(f"Found {len(pending)} pending posts in queue.")
    out_base = Path(output_base)
    generated = 0

    for post in pending:
        json_path = post.get("json_path")
        cid = post.get("content_id", "unknown")
        if not json_path:
            print(f"  [{cid}] Skipping: no json_path")
            continue

        content = _extract_carousel_content(json_path)
        if not content:
            print(f"  [{cid}] Skipping: could not extract content")
            continue

        today = datetime.now().strftime("%Y%m%d")
        output_dir = out_base / f"carousel_{today}_{cid}"

        try:
            paths = generate_carousel(
                content_id=content["content_id"],
                hook=content["hook"],
                slides=content["slides"],
                output_dir=str(output_dir),
                category=content["category"],
                cta_type=content.get("cta_type", "soft"),
            )
            generated += 1
        except Exception as e:
            print(f"  [{cid}] ERROR: {e}")
            import traceback
            traceback.print_exc()

    print(f"\nGenerated {generated}/{len(pending)} carousel sets.")
    return generated


# ===========================================================================
# Demo
# ===========================================================================

def generate_demo(output_dir: str = "content/generated/carousel_demo_v3") -> list[str]:
    """Generate a sample carousel set for review."""
    print("=== Generating demo carousel (v3.0) ===\n")

    return generate_carousel(
        content_id="DEMO_V3",
        hook="手数料\n知ってる？",
        slides=[
            {
                "title": "看護師は無料で使える",
                "body": "でも、病院側は年収の20〜30%を\nエージェントに支払っています。\n\n・年収400万 → 手数料80〜120万\n・年収500万 → 手数料100〜150万",
            },
            {
                "title": "手数料が高いとどうなる？",
                "body": "病院は高い手数料を払った分\n採用のハードルを上げます。\n\n・面接が厳しくなる\n・条件交渉が通りにくい\n・入職後の圧が強くなる",
                "highlight_number": "120万円",
                "highlight_label": "大手の平均手数料（年収400万の場合）",
            },
            {
                "title": "手数料10%で解決",
                "body": "病院の負担が軽い\n→ 採用されやすい\n→ 条件交渉もしやすい\n→ 入職後の関係も良好\n\nつまり、あなたが得をする。",
                "highlight_number": "10%",
                "highlight_label": "ナースロビーの紹介手数料",
            },
        ],
        output_dir=output_dir,
        category="転職・キャリア",
        cta_type="hard",
    )


def generate_demo_aruaru(output_dir: str = "content/generated/carousel_demo_aruaru_v3") -> list[str]:
    """Generate an aruaru-themed demo for review."""
    print("=== Generating aruaru demo carousel (v3.0) ===\n")

    return generate_carousel(
        content_id="DEMO_ARUARU_V3",
        hook="AIは怒らない",
        slides=[
            {
                "title": "先輩の恐怖のセリフ",
                "body": "新人の頃、質問したら\n返ってきたあの一言。\n\n「それ前にも言ったよね？」\n\n心臓止まるかと思った。",
            },
            {
                "title": "AIに100回聞いてみた",
                "body": "「この薬の投与速度は？」\n\n・1回目: 丁寧に説明\n・50回目: まだ丁寧\n・100回目: 変わらず丁寧\n\n全然怒らない。",
            },
            {
                "title": "理想の先輩だった",
                "body": "・何回聞いても怒らない\n・「前にも言ったよね」ゼロ\n・24時間いつでも対応\n・ため息もつかない",
                "highlight_number": "0回",
                "highlight_label": "AIが怒った回数",
            },
        ],
        output_dir=output_dir,
        category="あるある×AI",
        cta_type="soft",
    )


# ===========================================================================
# CLI
# ===========================================================================

def generate_carousel_backgrounds(
    content_id: str,
    hook: str,
    slides: list[dict],
    output_dir: str,
    category: str = "あるある",
    cta_type: str = "soft",
    platform: str = "tiktok",
) -> dict:
    """
    Generate background-only slides (no text) + metadata JSON for animated video.

    Returns dict with 'backgrounds' (list of paths) and 'metadata' (text positioning info).
    Used by video_text_animator.py to create dynamic text animations with ffmpeg.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Platform dimensions
    canvas_w, canvas_h = PLATFORM_SIZES.get(platform, (CANVAS_W, CANVAS_H))
    safe = SAFE_ZONES.get(platform, SAFE_ZONES["tiktok"])

    theme = CATEGORY_THEMES.get(category, DEFAULT_THEME)
    content_slides = list(slides)[:3]
    total = 1 + len(content_slides) + 1

    bg_paths = []
    metadata = {
        "content_id": content_id,
        "platform": platform,
        "canvas": {"w": canvas_w, "h": canvas_h},
        "safe_zones": safe,
        "total_slides": total,
        "category": category,
        "cta_type": cta_type,
        "slides": [],
    }

    # Slide 1: Hook background
    bg1 = _build_dark_bg(theme)
    if canvas_h != CANVAS_H:
        bg1 = bg1.resize((canvas_w, canvas_h), Image.LANCZOS)
    p1 = out / f"{content_id}_bg_01_hook.png"
    bg1.save(str(p1), "PNG")
    bg_paths.append(str(p1))

    font_hook = load_font(bold=True, size=120)
    hook_bbox = font_hook.getbbox(hook[:MAX_HOOK_CHARS])
    hook_w = hook_bbox[2] - hook_bbox[0]
    hook_h = hook_bbox[3] - hook_bbox[1]

    metadata["slides"].append({
        "type": "hook",
        "text": hook[:MAX_HOOK_CHARS],
        "font_size": 120,
        "font_bold": True,
        "color": list(theme["text_primary"]),
        "x": (canvas_w - hook_w) // 2,
        "y": (canvas_h - hook_h) // 2,
        "animation": "zoom_in",
        "duration": 2.5,
    })

    # Content slides
    for i, slide_data in enumerate(content_slides):
        slide_num = i + 2
        dark = (i % 2 == 0)

        if dark:
            bg = _build_dark_bg(theme)
        else:
            bg = _build_light_bg(theme)

        if canvas_h != CANVAS_H:
            bg = bg.resize((canvas_w, canvas_h), Image.LANCZOS)

        p = out / f"{content_id}_bg_{slide_num:02d}_content.png"
        bg.save(str(p), "PNG")
        bg_paths.append(str(p))

        title = slide_data.get("title", "")
        body = slide_data.get("body", "")
        text_color = list(theme["text_primary"]) if dark else list(theme["text_on_light"])

        # Calculate card area for text positioning
        card_x = safe["left"] + 20
        card_y = safe["top"] + 80
        card_w = canvas_w - safe["left"] - safe["right"] - 40

        title_font_size = 64
        body_font_size = 48

        metadata["slides"].append({
            "type": "content",
            "dark": dark,
            "title": title,
            "title_font_size": title_font_size,
            "body": body,
            "body_font_size": body_font_size,
            "color": text_color,
            "card_x": card_x,
            "card_y": card_y,
            "card_w": card_w,
            "highlight_number": slide_data.get("highlight_number"),
            "highlight_label": slide_data.get("highlight_label"),
            "animation": "fade_in_stagger",
            "duration": 3.5,
        })

    # CTA background
    bg_cta = _build_brand_gradient_bg()
    if canvas_h != CANVAS_H:
        bg_cta = bg_cta.resize((canvas_w, canvas_h), Image.LANCZOS)
    p_cta = out / f"{content_id}_bg_{total:02d}_cta.png"
    bg_cta.save(str(p_cta), "PNG")
    bg_paths.append(str(p_cta))

    cta_texts = {
        "soft": ["保存してね", "フォローで続き見れるよ"],
        "hard": ["LINEで相談してみて", "プロフのリンクから"],
    }
    cta = cta_texts.get(cta_type, cta_texts["soft"])

    metadata["slides"].append({
        "type": "cta",
        "cta_type": cta_type,
        "texts": cta,
        "font_size": 56,
        "color": [255, 255, 255],
        "animation": "pulse",
        "duration": 3.0,
    })

    # Save metadata
    meta_path = out / f"{content_id}_text_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"  [{content_id}] Backgrounds: {len(bg_paths)} + metadata saved")
    return {"backgrounds": bg_paths, "metadata": str(meta_path)}


def main():
    parser = argparse.ArgumentParser(
        description="TikTok/Instagram carousel slide generator v3.0 (5 slides)",
    )
    parser.add_argument("--demo", action="store_true", help="Generate a demo carousel set for review")
    parser.add_argument("--demo-aruaru", action="store_true", help="Generate aruaru-themed demo")
    parser.add_argument("--queue", help="Path to posting_queue.json")
    parser.add_argument("--output", default="content/generated/", help="Output base directory")
    parser.add_argument("--single-json", help="Generate carousel from a single slide JSON file")
    parser.add_argument("--background-only", action="store_true",
                       help="Generate background-only PNGs + text metadata JSON (for animated video)")
    parser.add_argument("--platform", choices=["tiktok", "instagram", "instagram_story"],
                       default="tiktok", help="Target platform for dimensions")

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent

    if args.demo:
        out = project_root / "content" / "generated" / "carousel_demo_v3"
        paths = generate_demo(str(out))
        print(f"\nDemo complete. {len(paths)} slides saved to {out}")

    elif args.demo_aruaru:
        out = project_root / "content" / "generated" / "carousel_demo_aruaru_v3"
        paths = generate_demo_aruaru(str(out))
        print(f"\nAruaru demo complete. {len(paths)} slides saved to {out}")

    elif args.queue:
        queue_path = Path(args.queue)
        if not queue_path.is_absolute():
            queue_path = project_root / queue_path
        output = Path(args.output)
        if not output.is_absolute():
            output = project_root / output
        count = generate_from_queue(str(queue_path), str(output))
        print(f"\nQueue processing complete. {count} sets generated.")

    elif args.single_json:
        json_path = Path(args.single_json)
        if not json_path.is_absolute():
            json_path = project_root / json_path
        content = _extract_carousel_content(str(json_path))
        if content:
            output = Path(args.output)
            if not output.is_absolute():
                output = project_root / output
            today = datetime.now().strftime("%Y%m%d")
            out_dir = output / f"carousel_{today}_{content['content_id']}"

            if args.background_only:
                result = generate_carousel_backgrounds(
                    content_id=content["content_id"],
                    hook=content["hook"],
                    slides=content["slides"],
                    output_dir=str(out_dir),
                    category=content["category"],
                    cta_type=content.get("cta_type", "soft"),
                    platform=args.platform,
                )
                print(f"\nBackgrounds: {len(result['backgrounds'])} files")
                print(f"Metadata: {result['metadata']}")
            else:
                generate_carousel(
                    content_id=content["content_id"],
                    hook=content["hook"],
                    slides=content["slides"],
                    output_dir=str(out_dir),
                    category=content["category"],
                    cta_type=content.get("cta_type", "soft"),
                )
        else:
            print("ERROR: Could not extract carousel content from JSON.")
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
