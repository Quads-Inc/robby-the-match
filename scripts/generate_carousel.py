#!/usr/bin/env python3
"""
generate_carousel.py — プロ品質カルーセルスライド生成エンジン v2.0

TikTok/Instagram用の9:16縦型カルーセル（7枚セット）を
Pillowのみで生成する。外部画像素材なし、純粋なプログラマティックデザイン。

v2.0 改善点:
  - フック（1枚目）: 文字サイズ大幅拡大、画面1/3占有、感情アクセントカラー
  - 本文（2-5枚目）: 吹き出し風カード、絵文字アイコン、フォント48-72pt
  - CTA（最終枚）: バッジ風「保存してね」「続きはプロフから」、LINE誘導
  - カテゴリ別カラーテーマ統一
  - スライド番号インジケーター（1/6 形式）
  - 余白・行間の改善

使い方:
  python3 scripts/generate_carousel.py --demo
  python3 scripts/generate_carousel.py --queue data/posting_queue.json --output content/generated/
"""

import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ===========================================================================
# Constants
# ===========================================================================

CANVAS_W = 1080
CANVAS_H = 1920

# TikTok UI safe zones
SAFE_TOP = 150
SAFE_BOTTOM = 250
SAFE_RIGHT = 100
SAFE_LEFT = 60

# Derived safe content area
CONTENT_X = SAFE_LEFT
CONTENT_Y = SAFE_TOP
CONTENT_W = CANVAS_W - SAFE_LEFT - SAFE_RIGHT  # 920
CONTENT_H = CANVAS_H - SAFE_TOP - SAFE_BOTTOM  # 1520

# ===========================================================================
# Category Color Themes (v2.0)
# ===========================================================================
# Each category has a complete color scheme for visual consistency

CATEGORY_THEMES = {
    "あるある": {
        "bg_top": (45, 10, 30),           # dark burgundy
        "bg_bottom": (80, 20, 50),         # warm dark pink
        "accent": (255, 107, 129),          # coral pink
        "accent_light": (255, 154, 162),    # light coral
        "accent_dark": (200, 60, 80),       # dark coral
        "card_bg": (255, 255, 255, 25),     # semi-transparent white
        "card_bg_light": (255, 240, 243, 240),  # light pink card
        "text_primary": (255, 255, 255),
        "text_secondary": (255, 200, 210),
        "text_dark": (60, 20, 35),
        "gradient_accent_a": (255, 107, 129),
        "gradient_accent_b": (255, 69, 96),
        "emoji_prefix": "",
    },
    "あるある×AI": {  # alias
        "bg_top": (45, 10, 30),
        "bg_bottom": (80, 20, 50),
        "accent": (255, 107, 129),
        "accent_light": (255, 154, 162),
        "accent_dark": (200, 60, 80),
        "card_bg": (255, 255, 255, 25),
        "card_bg_light": (255, 240, 243, 240),
        "text_primary": (255, 255, 255),
        "text_secondary": (255, 200, 210),
        "text_dark": (60, 20, 35),
        "gradient_accent_a": (255, 107, 129),
        "gradient_accent_b": (255, 69, 96),
        "emoji_prefix": "",
    },
    "転職・キャリア": {
        "bg_top": (12, 25, 55),            # deep navy
        "bg_bottom": (25, 50, 90),          # dark blue
        "accent": (66, 133, 244),            # bright blue
        "accent_light": (130, 177, 255),     # light blue
        "accent_dark": (30, 80, 180),        # dark blue
        "card_bg": (255, 255, 255, 25),
        "card_bg_light": (230, 240, 255, 240),
        "text_primary": (255, 255, 255),
        "text_secondary": (180, 210, 255),
        "text_dark": (20, 35, 70),
        "gradient_accent_a": (66, 133, 244),
        "gradient_accent_b": (30, 80, 180),
        "emoji_prefix": "",
    },
    "給与・待遇": {
        "bg_top": (15, 35, 20),             # dark green
        "bg_bottom": (30, 55, 25),           # forest green
        "accent": (76, 175, 80),             # green
        "accent_light": (129, 199, 132),     # light green
        "accent_dark": (46, 125, 50),        # dark green
        "card_bg": (255, 255, 255, 25),
        "card_bg_light": (232, 245, 233, 240),
        "text_primary": (255, 255, 255),
        "text_secondary": (200, 230, 200),
        "text_dark": (20, 50, 25),
        "gradient_accent_a": (76, 175, 80),
        "gradient_accent_b": (255, 193, 7),   # gold accent
        "emoji_prefix": "",
    },
    "サービス紹介": {
        "bg_top": (10, 30, 60),             # brand navy
        "bg_bottom": (0, 60, 80),            # brand teal-navy
        "accent": (26, 115, 232),            # brand blue
        "accent_light": (100, 170, 255),
        "accent_dark": (15, 80, 180),
        "card_bg": (255, 255, 255, 25),
        "card_bg_light": (230, 245, 255, 240),
        "text_primary": (255, 255, 255),
        "text_secondary": (180, 220, 255),
        "text_dark": (15, 40, 70),
        "gradient_accent_a": (26, 115, 232),
        "gradient_accent_b": (0, 191, 165),
        "emoji_prefix": "",
    },
}

# Default theme fallback
DEFAULT_THEME = CATEGORY_THEMES["あるある"]

# Common colors
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_BRAND_BLUE = (26, 115, 232)
COLOR_BRAND_TEAL = (0, 191, 165)

# Font paths
FONT_BOLD_PATH = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"
FONT_REGULAR_PATH = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"
FONT_FALLBACK_PATH = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"

# Text rendering
LINE_HEIGHT_RATIO = 1.7     # v2.0: wider line spacing for readability
MAX_HOOK_CHARS_PER_LINE = 10  # v2.0: bigger text = fewer chars per line
MAX_BODY_CHARS_PER_LINE = 16

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
    """Wrap Japanese text to fit within max_width pixels.
    Respects kinsoku rules: closing brackets/punctuation are not orphaned to new line.
    """
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
                # Check kinsoku: if char should not start a new line, keep it on current
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
    """Create a smooth gradient image (RGBA)."""
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
    elif direction == "radial":
        cx, cy = w // 2, h // 3
        max_dist = math.sqrt(cx**2 + cy**2) * 1.2
        for y in range(h):
            for x in range(w):
                dist = math.sqrt((x - cx)**2 + (y - cy)**2)
                ratio = min(dist / max_dist, 1.0)
                r = int(color_top[0] + (color_bottom[0] - color_top[0]) * ratio)
                g = int(color_top[1] + (color_bottom[1] - color_top[1]) * ratio)
                b = int(color_top[2] + (color_bottom[2] - color_top[2]) * ratio)
                pixels[x, y] = (r, g, b, 255)

    return img


def draw_text_shadow(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple = COLOR_WHITE,
    shadow_color: tuple = (0, 0, 0, 128),
    shadow_offset: int = 3,
    outline: bool = True,
    outline_color: tuple = (0, 0, 0, 180),
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
    shadow_color: tuple = (0, 0, 0, 128),
    shadow_offset: int = 3,
    line_height_ratio: float = LINE_HEIGHT_RATIO,
) -> int:
    """Draw multiple lines of text, horizontally centered. Returns Y after last line."""
    line_h = int(font_size * line_height_ratio)
    cy = start_y
    for line in lines:
        tw, _ = measure_text(line, font)
        tx = center_x - tw // 2
        if shadow:
            draw_text_shadow(draw, tx, cy, line, font, fill=fill, shadow_color=shadow_color, shadow_offset=shadow_offset)
        else:
            draw.text((tx, cy), line, fill=fill, font=font)
        cy += line_h
    return cy


def draw_rounded_rect(
    draw: ImageDraw.ImageDraw,
    xy: tuple,
    radius: int,
    fill: Optional[tuple] = None,
    outline: Optional[tuple] = None,
    width: int = 1,
):
    """Draw a rounded rectangle."""
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


# ===========================================================================
# Background builders (v2.0)
# ===========================================================================

def _build_dark_bg(theme: dict) -> Image.Image:
    """Dark gradient background with subtle glow effect."""
    bg = create_gradient(CANVAS_W, CANVAS_H, theme["bg_top"], theme["bg_bottom"])
    draw = ImageDraw.Draw(bg)

    # Subtle radial glow from center-top
    glow = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    accent = theme["accent"]
    cx, cy = CANVAS_W // 2, CANVAS_H // 4
    for r in range(400, 0, -5):
        alpha = max(2, int(8 * (1 - r / 400)))
        glow_draw.ellipse(
            (cx - r, cy - r, cx + r, cy + r),
            fill=(*accent[:3], alpha),
        )
    bg = Image.alpha_composite(bg, glow)

    return bg


def _build_light_bg(theme: dict) -> Image.Image:
    """Light background with colored card feel."""
    # White-ish base with a very subtle tint
    accent = theme["accent_light"]
    top = (248, 249, 252)
    bottom = (min(255, accent[0] // 4 + 230), min(255, accent[1] // 4 + 230), min(255, accent[2] // 4 + 230))
    bg = create_gradient(CANVAS_W, CANVAS_H, top, bottom)

    # Subtle accent strip at very top
    draw = ImageDraw.Draw(bg)
    draw.rectangle([(0, 0), (CANVAS_W, 6)], fill=(*theme["accent"][:3], 180))

    return bg


def _build_accent_gradient_bg(theme: dict) -> Image.Image:
    """Bold accent gradient for reveal slides."""
    bg = create_gradient(
        CANVAS_W, CANVAS_H,
        theme["gradient_accent_a"],
        theme["gradient_accent_b"],
        direction="diagonal",
    )
    return bg


def _build_brand_gradient_bg() -> Image.Image:
    """Blue-to-teal brand gradient for CTA slide."""
    bg = create_gradient(CANVAS_W, CANVAS_H, COLOR_BRAND_BLUE, COLOR_BRAND_TEAL, direction="diagonal")

    # Add subtle radial glow
    glow = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    cx, cy = CANVAS_W // 2, CANVAS_H // 2
    for r in range(500, 0, -8):
        alpha = max(1, int(5 * (1 - r / 500)))
        glow_draw.ellipse(
            (cx - r, cy - r, cx + r, cy + r),
            fill=(255, 255, 255, alpha),
        )
    bg = Image.alpha_composite(bg, glow)

    return bg


# ===========================================================================
# Slide indicators (v2.0)
# ===========================================================================

def _draw_slide_indicator(draw: ImageDraw.ImageDraw, current: int, total: int, light_bg: bool = False):
    """Draw '1/6' style slide number indicator at top-right safe area."""
    font = load_font(bold=True, size=26)
    text = f"{current}/{total}"
    tw, th = measure_text(text, font)

    # Position: top-right corner, well inside safe zone
    pad_x, pad_y = 18, 10
    pill_w = tw + pad_x * 2
    pill_h = th + pad_y * 2

    pill_x0 = CANVAS_W - SAFE_RIGHT - pill_w - 20
    pill_y0 = SAFE_TOP + 10
    pill_x1 = pill_x0 + pill_w
    pill_y1 = pill_y0 + pill_h

    x = pill_x0 + pad_x
    y = pill_y0 + pad_y

    if light_bg:
        pill_fill = (0, 0, 0, 30)
        text_color = (60, 60, 60)
    else:
        pill_fill = (0, 0, 0, 60)
        text_color = (255, 255, 255)

    draw.rounded_rectangle(
        (pill_x0, pill_y0, pill_x1, pill_y1),
        radius=pill_h // 2,
        fill=pill_fill,
    )
    draw.text((x, y), text, fill=text_color, font=font)


def _draw_brand_watermark(draw: ImageDraw.ImageDraw, light_bg: bool = False):
    """Draw subtle brand watermark."""
    font = load_font(bold=False, size=22)
    text = "@nurse.robby"
    x = SAFE_LEFT + 10
    y = CANVAS_H - SAFE_BOTTOM + 10
    if light_bg:
        color = (0, 0, 0, 40)
    else:
        color = (255, 255, 255, 40)
    draw.text((x, y), text, fill=color, font=font)


# ===========================================================================
# Speech bubble / card drawing (v2.0)
# ===========================================================================

def _draw_speech_card(
    draw: ImageDraw.ImageDraw,
    img: Image.Image,
    x0: int, y0: int, x1: int, y1: int,
    fill: tuple = (255, 255, 255, 230),
    radius: int = 30,
    shadow: bool = True,
    accent_left: Optional[tuple] = None,
):
    """Draw a card/speech-bubble style container with optional left accent bar and shadow."""
    if shadow:
        # Draw shadow layer
        shadow_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_layer)
        shadow_draw.rounded_rectangle(
            (x0 + 4, y0 + 6, x1 + 4, y1 + 6),
            radius=radius,
            fill=(0, 0, 0, 40),
        )
        # Composite shadow onto main image
        composite = Image.alpha_composite(img, shadow_layer)
        img.paste(composite)

    # Main card
    draw.rounded_rectangle(
        (x0, y0, x1, y1),
        radius=radius,
        fill=fill,
    )

    # Left accent bar
    if accent_left:
        bar_x0 = x0
        bar_y0 = y0 + radius
        bar_x1 = x0 + 6
        bar_y1 = y1 - radius
        draw.rectangle((bar_x0, bar_y0, bar_x1, bar_y1), fill=accent_left)


# ===========================================================================
# Slide generators (v2.0 — major redesign)
# ===========================================================================

def generate_slide_hook(
    hook_text: str,
    theme: dict,
    total_slides: int = 7,
) -> Image.Image:
    """
    Slide 1 - HOOK: Big bold text occupying ~1/3 of screen.
    Dark background with accent color glow. Maximum impact.
    """
    bg = _build_dark_bg(theme)
    draw = ImageDraw.Draw(bg)
    accent = theme["accent"]

    center_x = CANVAS_W // 2

    # --- Hook text: LARGE, filling ~1/3 of the screen ---
    # Target zone: center of safe area, occupying ~40% of content height
    hook_zone_top = SAFE_TOP + 120
    hook_zone_height = int(CONTENT_H * 0.45)
    max_text_width = CONTENT_W - 80

    # Try font sizes from very large to acceptable minimum
    best_font_size = 48
    best_lines = []
    for size in range(96, 44, -2):
        font = load_font(bold=True, size=size)
        lines = wrap_text_jp(hook_text, font, max_text_width, MAX_HOOK_CHARS_PER_LINE)
        block_h = text_block_height(lines, size)
        if block_h <= hook_zone_height:
            best_font_size = size
            best_lines = lines
            break
    else:
        font = load_font(bold=True, size=48)
        best_font_size = 48
        best_lines = wrap_text_jp(hook_text, font, max_text_width, MAX_HOOK_CHARS_PER_LINE)

    font = load_font(bold=True, size=best_font_size)
    block_h = text_block_height(best_lines, best_font_size)

    # Center vertically in hook zone
    text_y = hook_zone_top + (hook_zone_height - block_h) // 2

    # Draw accent glow behind text area
    glow_layer = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    glow_cx = center_x
    glow_cy = text_y + block_h // 2
    for r in range(300, 0, -8):
        alpha = max(1, int(12 * (1 - r / 300)))
        glow_draw.ellipse(
            (glow_cx - r, glow_cy - r, glow_cx + r, glow_cy + r),
            fill=(*accent[:3], alpha),
        )
    bg = Image.alpha_composite(bg, glow_layer)
    draw = ImageDraw.Draw(bg)

    # Draw the hook text with strong shadow
    draw_centered_text_block(
        draw, best_lines, font, best_font_size,
        center_x, text_y,
        fill=COLOR_WHITE,
        shadow=True,
        shadow_offset=4,
        shadow_color=(0, 0, 0, 200),
    )

    # --- Accent underline below text ---
    underline_y = text_y + block_h + 40
    underline_w = min(350, CONTENT_W - 120)
    underline_x = center_x - underline_w // 2
    draw.rounded_rectangle(
        (underline_x, underline_y, underline_x + underline_w, underline_y + 8),
        radius=4, fill=(*accent[:3], 200),
    )

    # --- Swipe hint at bottom (larger, more visible) ---
    hint_font = load_font(bold=True, size=28)
    hint_text = ">>>  スワイプ"
    tw, _ = measure_text(hint_text, hint_font)
    hint_x = center_x - tw // 2
    hint_y = CANVAS_H - SAFE_BOTTOM - 80
    draw.text((hint_x, hint_y), hint_text, fill=(*accent[:3], 160), font=hint_font)

    # --- Indicators ---
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
    total_slides: int = 7,
) -> Image.Image:
    """
    Slides 2-5 - CONTENT: Card-based layout with emoji bullets.
    Alternating dark/light. Speech-card container for body text.
    """
    if theme is None:
        theme = DEFAULT_THEME
    accent = theme["accent"]

    if dark_theme:
        bg = _build_dark_bg(theme)
    else:
        bg = _build_light_bg(theme)

    draw = ImageDraw.Draw(bg)
    light_bg = not dark_theme
    center_x = CANVAS_W // 2
    max_text_width = CONTENT_W - 100

    current_y = SAFE_TOP + 80

    # --- Section title (large) ---
    title_font_size = 48
    title_font = load_font(bold=True, size=title_font_size)
    if dark_theme:
        title_color = COLOR_WHITE
    else:
        title_color = theme["text_dark"]

    title_lines = wrap_text_jp(title, title_font, max_text_width)

    # Accent dot before title
    dot_y = current_y + title_font_size // 2
    accent_dot_color = (*accent[:3], 255)
    draw.ellipse(
        (SAFE_LEFT + 20, dot_y - 8, SAFE_LEFT + 36, dot_y + 8),
        fill=accent_dot_color,
    )

    # Title text (left-aligned for better readability)
    title_x = SAFE_LEFT + 50
    for tl in title_lines:
        if dark_theme:
            draw_text_shadow(draw, title_x, current_y, tl, title_font, fill=title_color, shadow_offset=2, outline_width=1)
        else:
            draw.text((title_x, current_y), tl, fill=title_color, font=title_font)
        current_y += int(title_font_size * 1.5)

    current_y += 20

    # --- Highlight number (if provided) ---
    if highlight_number:
        num_font_size = 88
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
            label_font = load_font(bold=False, size=26)
            tw2, _ = measure_text(highlight_label, label_font)
            lx = center_x - tw2 // 2
            label_color = theme["text_secondary"] if dark_theme else (120, 120, 120)
            draw.text((lx, current_y), highlight_label, fill=label_color, font=label_font)
            current_y += 50
        else:
            current_y += 30

    # --- Body text in a card container ---
    card_margin = 30
    card_x0 = SAFE_LEFT + card_margin
    card_x1 = CANVAS_W - SAFE_RIGHT - card_margin
    card_top = current_y
    card_inner_pad = 30

    # Pre-calculate body content to determine card height
    max_body_y = CANVAS_H - SAFE_BOTTOM - 60

    # Determine body font size based on available space
    body_font_size = 36
    body_paragraphs = body.split("\n")

    # Estimate content height
    total_lines_estimate = 0
    for para in body_paragraphs:
        para = para.strip()
        if not para:
            total_lines_estimate += 0.5
            continue
        total_lines_estimate += max(1, len(para) / 14)

    available_height = max_body_y - card_top - card_inner_pad * 2
    estimated_height = int(total_lines_estimate * body_font_size * LINE_HEIGHT_RATIO)

    if estimated_height > available_height:
        for try_size in range(34, 24, -2):
            est_h = int(total_lines_estimate * try_size * LINE_HEIGHT_RATIO)
            if est_h <= available_height:
                body_font_size = try_size
                break
        else:
            body_font_size = 26

    body_font = load_font(bold=False, size=body_font_size)
    body_font_bold = load_font(bold=True, size=body_font_size)
    line_h = int(body_font_size * LINE_HEIGHT_RATIO)

    # Draw card background
    # First pass: calculate total body height
    temp_y = 0
    for para in body_paragraphs:
        para = para.strip()
        if not para:
            temp_y += line_h // 2
            continue
        is_bullet = para.startswith(("・", "- ", "* "))
        if is_bullet:
            clean = para.lstrip("・- *").strip()
            lines = wrap_text_jp(clean, body_font, card_x1 - card_x0 - card_inner_pad * 2 - 60)
            temp_y += line_h * len(lines) + 12
        else:
            lines = wrap_text_jp(para, body_font, card_x1 - card_x0 - card_inner_pad * 2)
            temp_y += line_h * len(lines) + 8

    card_bottom = min(card_top + card_inner_pad * 2 + temp_y + 10, max_body_y)

    if dark_theme:
        # Semi-transparent dark card -- subtle white tint for glass effect
        card_fill = (255, 255, 255, 18)
    else:
        card_fill = (*theme["card_bg_light"][:3], theme["card_bg_light"][3] if len(theme["card_bg_light"]) > 3 else 230)

    # Draw card with accent left border
    draw.rounded_rectangle(
        (card_x0, card_top, card_x1, card_bottom),
        radius=24,
        fill=card_fill,
    )
    # Card border (subtle)
    if dark_theme:
        draw.rounded_rectangle(
            (card_x0, card_top, card_x1, card_bottom),
            radius=24,
            fill=None,
            outline=(*accent[:3], 40),
            width=1,
        )
    # Left accent bar
    draw.rounded_rectangle(
        (card_x0, card_top + 24, card_x0 + 6, card_bottom - 24),
        radius=3,
        fill=(*accent[:3], 200),
    )

    # Draw body text inside card
    current_y = card_top + card_inner_pad
    body_left = card_x0 + card_inner_pad + 10
    body_max_w = card_x1 - card_x0 - card_inner_pad * 2 - 10

    if dark_theme:
        body_color = COLOR_WHITE
    else:
        body_color = theme["text_dark"]

    # Emoji icons for bullet points
    bullet_emojis = [">>", ">>", ">>", ">>", ">>"]
    bullet_idx = 0

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

            # Draw accent-colored bullet marker
            marker_x = body_left + 8
            marker_y = current_y + body_font_size // 2
            marker_color = (*accent[:3], 220)
            # Filled circle bullet
            draw.ellipse(
                (marker_x, marker_y - 6, marker_x + 12, marker_y + 6),
                fill=marker_color,
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
            current_y += 12
            bullet_idx += 1
        else:
            lines = wrap_text_jp(para, body_font, body_max_w)
            for line in lines:
                if current_y >= max_body_y - line_h:
                    break
                line_x = body_left
                if dark_theme:
                    draw_text_shadow(draw, line_x, current_y, line, body_font,
                                     fill=body_color, shadow_offset=1, outline_width=1)
                else:
                    draw.text((line_x, current_y), line, fill=body_color, font=body_font)
                current_y += line_h
            current_y += 8

    # --- Indicators ---
    _draw_slide_indicator(draw, slide_num, total_slides, light_bg=light_bg)
    _draw_brand_watermark(draw, light_bg=light_bg)

    return bg.convert("RGB")


def generate_slide_reveal(
    text: str,
    number: Optional[str] = None,
    label: Optional[str] = None,
    theme: dict = None,
    total_slides: int = 7,
) -> Image.Image:
    """
    Slide 6 - REVEAL/CLIMAX: Dramatic accent gradient.
    Big reveal text with optional large highlight number.
    """
    if theme is None:
        theme = DEFAULT_THEME

    bg = _build_accent_gradient_bg(theme)
    draw = ImageDraw.Draw(bg)

    center_x = CANVAS_W // 2
    max_text_width = CONTENT_W - 80

    # Calculate total element heights for centering
    elements_height = 0

    reveal_font_size = 60
    reveal_font = load_font(bold=True, size=reveal_font_size)
    reveal_lines = wrap_text_jp(text, reveal_font, max_text_width)
    reveal_block_h = text_block_height(reveal_lines, reveal_font_size)
    elements_height += reveal_block_h

    num_font_size = 100
    num_font = None
    if number:
        num_font = load_font(bold=True, size=num_font_size)
        elements_height += int(num_font_size * 1.4) + 50

    label_font_size = 28
    label_font = None
    if label:
        label_font = load_font(bold=False, size=label_font_size)
        elements_height += int(label_font_size * 1.5) + 10

    # Center vertically
    start_y = SAFE_TOP + (CONTENT_H - elements_height) // 2
    current_y = start_y

    # --- Reveal text ---
    current_y = draw_centered_text_block(
        draw, reveal_lines, reveal_font, reveal_font_size,
        center_x, current_y,
        fill=COLOR_WHITE,
        shadow=True,
        shadow_offset=4,
        shadow_color=(0, 0, 0, 180),
    )
    current_y += 50

    # --- Big number ---
    if number and num_font:
        tw, _ = measure_text(number, num_font)
        nx = center_x - tw // 2

        draw_text_shadow(
            draw, nx, current_y, number, num_font,
            fill=COLOR_WHITE,
            shadow_color=(0, 0, 0, 150),
            shadow_offset=5,
            outline_width=3,
        )
        current_y += int(num_font_size * 1.3)

    # --- Label ---
    if label and label_font:
        tw, _ = measure_text(label, label_font)
        lx = center_x - tw // 2
        draw.text((lx, current_y), label, fill=(*COLOR_WHITE[:3], 200), font=label_font)

    _draw_slide_indicator(draw, total_slides - 1, total_slides, light_bg=False)
    _draw_brand_watermark(draw, light_bg=False)

    return bg.convert("RGB")


def generate_slide_cta(
    cta_type: str = "soft",
    theme: dict = None,
    total_slides: int = 7,
) -> Image.Image:
    """
    Slide 7 - CTA: Brand gradient.
    Soft CTA: 'save & follow' badges.
    Hard CTA: LINE invitation with button.
    """
    if theme is None:
        theme = DEFAULT_THEME

    bg = _build_brand_gradient_bg()
    draw = ImageDraw.Draw(bg)

    center_x = CANVAS_W // 2

    # --- "ナースロビー" logo text ---
    logo_font_size = 56
    logo_font = load_font(bold=True, size=logo_font_size)
    logo_text = "ナースロビー"
    tw, _ = measure_text(logo_text, logo_font)
    logo_x = center_x - tw // 2
    logo_y = SAFE_TOP + 100

    draw_text_shadow(
        draw, logo_x, logo_y, logo_text, logo_font,
        fill=COLOR_WHITE, shadow_offset=3,
    )

    # --- English tagline ---
    tag_font = load_font(bold=False, size=26)
    tag_text = "NURSE ROBBY"
    tw, _ = measure_text(tag_text, tag_font)
    tag_x = center_x - tw // 2
    tag_y = logo_y + logo_font_size + 16
    draw.text((tag_x, tag_y), tag_text, fill=(*COLOR_WHITE[:3], 160), font=tag_font)

    # --- Separator ---
    sep_y = tag_y + 60
    sep_w = 160
    draw.rounded_rectangle(
        (center_x - sep_w // 2, sep_y, center_x + sep_w // 2, sep_y + 3),
        radius=2, fill=(*COLOR_WHITE[:3], 80),
    )

    if cta_type == "hard":
        # --- Hard CTA: LINE invitation ---
        # Badge: 手数料10%
        badge_y = sep_y + 50
        badge_font = load_font(bold=True, size=30)
        badge_text = "紹介手数料 業界最安10%"
        btw, bth = measure_text(badge_text, badge_font)
        badge_pad_x = 40
        badge_pad_y = 18
        badge_w = btw + badge_pad_x * 2
        badge_h = bth + badge_pad_y * 2
        badge_x = center_x - badge_w // 2

        draw.rounded_rectangle(
            (badge_x, badge_y, badge_x + badge_w, badge_y + badge_h),
            radius=badge_h // 2,
            fill=(*COLOR_WHITE[:3], 40),
            outline=(*COLOR_WHITE[:3], 180), width=2,
        )
        draw_text_shadow(
            draw, badge_x + badge_pad_x, badge_y + badge_pad_y,
            badge_text, badge_font, fill=COLOR_WHITE,
            shadow_offset=1, outline_width=1,
        )

        # --- CTA Button: "LINEで無料相談" ---
        btn_y = badge_y + badge_h + 60
        btn_font = load_font(bold=True, size=36)
        btn_text = "LINEで無料相談"
        btw2, bth2 = measure_text(btn_text, btn_font)
        btn_pad_x = 60
        btn_pad_y = 28
        btn_w = btw2 + btn_pad_x * 2
        btn_h = bth2 + btn_pad_y * 2
        btn_x = center_x - btn_w // 2

        draw.rounded_rectangle(
            (btn_x, btn_y, btn_x + btn_w, btn_y + btn_h),
            radius=btn_h // 2, fill=COLOR_WHITE,
        )
        draw.text(
            (btn_x + btn_pad_x, btn_y + btn_pad_y),
            btn_text, fill=COLOR_BRAND_BLUE, font=btn_font,
        )

        # Arrow hint
        arrow_font = load_font(bold=True, size=30)
        draw.text(
            (btn_x + btn_w - btn_pad_x + 5, btn_y + btn_pad_y + 3),
            ">>", fill=COLOR_BRAND_TEAL, font=arrow_font,
        )

        # --- Sub text ---
        sub_y = btn_y + btn_h + 40
        sub_font = load_font(bold=False, size=26)
        sub_text = "プロフィールのリンクから"
        tw, _ = measure_text(sub_text, sub_font)
        draw.text((center_x - tw // 2, sub_y), sub_text, fill=(*COLOR_WHITE[:3], 180), font=sub_font)

        # --- Trust indicators ---
        trust_y = sub_y + 70
        _draw_trust_badges(draw, center_x, trust_y)

    else:
        # --- Soft CTA: Save + Follow badges ---
        # "保存してね" badge (large, prominent)
        save_y = sep_y + 60
        save_font = load_font(bold=True, size=40)
        save_text = "保存してね"
        stw, sth = measure_text(save_text, save_font)
        save_pad_x = 50
        save_pad_y = 24
        save_w = stw + save_pad_x * 2
        save_h = sth + save_pad_y * 2
        save_x = center_x - save_w // 2

        # Bookmark icon shape (white pill with accent border)
        draw.rounded_rectangle(
            (save_x, save_y, save_x + save_w, save_y + save_h),
            radius=save_h // 2,
            fill=COLOR_WHITE,
            outline=None,
        )
        draw.text(
            (save_x + save_pad_x, save_y + save_pad_y),
            save_text, fill=COLOR_BRAND_BLUE, font=save_font,
        )

        # "フォローで続きが見れる" text
        follow_y = save_y + save_h + 50
        follow_font = load_font(bold=True, size=32)
        follow_text = "フォローで最新情報をチェック"
        tw, _ = measure_text(follow_text, follow_font)
        draw.text(
            (center_x - tw // 2, follow_y),
            follow_text, fill=COLOR_WHITE, font=follow_font,
        )

        # Subtitle
        prof_y = follow_y + 60
        prof_font = load_font(bold=False, size=26)
        prof_text = "神奈川県西部の看護師転職"
        ptw, _ = measure_text(prof_text, prof_font)
        draw.text(
            (center_x - ptw // 2, prof_y),
            prof_text, fill=(*COLOR_WHITE[:3], 160), font=prof_font,
        )

        # --- Trust indicators ---
        trust_y = prof_y + 60
        _draw_trust_badges(draw, center_x, trust_y)

    _draw_slide_indicator(draw, total_slides, total_slides, light_bg=False)
    _draw_brand_watermark(draw, light_bg=False)

    return bg.convert("RGB")


def _draw_trust_badges(draw: ImageDraw.ImageDraw, center_x: int, y: int):
    """Draw trust indicator badges at the bottom."""
    badge_font = load_font(bold=False, size=22)
    check_font = load_font(bold=True, size=22)
    items = ["有料職業紹介許可", "完全無料", "LINEで簡単相談"]

    # Draw horizontally on one line with check marks
    # Measure total width
    check_text = "+"
    check_w, _ = measure_text(check_text, check_font)
    gap = 30
    total_w = 0
    item_widths = []
    for item in items:
        itw, _ = measure_text(item, badge_font)
        item_widths.append(itw)
        total_w += check_w + 8 + itw

    total_w += gap * (len(items) - 1)
    start_x = center_x - total_w // 2

    cx = start_x
    for i, item in enumerate(items):
        # Checkmark
        draw.text(
            (cx, y),
            check_text, fill=(100, 255, 210), font=check_font,
        )
        cx += check_w + 8
        # Text
        draw.text(
            (cx, y + 1),
            item, fill=(*COLOR_WHITE[:3], 200), font=badge_font,
        )
        cx += item_widths[i] + gap


# ===========================================================================
# Main carousel generator
# ===========================================================================

def generate_carousel(
    content_id: str,
    hook: str,
    slides: list[dict],
    reveal: dict,
    output_dir: str,
    category: str = "あるある",
    cta_type: str = "soft",
) -> list[str]:
    """
    Generate a complete 7-slide carousel set.

    Args:
        content_id: Unique ID (e.g. "A01")
        hook: Text for slide 1 (hook)
        slides: List of dicts for slides 2-5:
                [{title, body, highlight_number?, highlight_label?}, ...]
        reveal: Dict for slide 6: {text, number?, label?}
        output_dir: Directory to save PNG files
        category: Content category for color scheme
        cta_type: "soft" or "hard"

    Returns:
        List of saved PNG file paths
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Get theme
    theme = CATEGORY_THEMES.get(category, DEFAULT_THEME)

    total_slides_count = 7
    saved_paths: list[str] = []

    print(f"  [{content_id}] Generating {total_slides_count}-slide carousel (category: {category})")

    # --- Slide 1: HOOK ---
    img1 = generate_slide_hook(hook, theme=theme, total_slides=total_slides_count)
    p1 = out / f"{content_id}_slide_01_hook.png"
    img1.save(str(p1), "PNG", quality=95)
    saved_paths.append(str(p1))
    print(f"    slide 01 (HOOK): {hook[:30]}...")

    # --- Slides 2-5: CONTENT (alternating dark/light) ---
    for i, slide_data in enumerate(slides[:4]):
        slide_num = i + 2
        dark = (i % 2 == 0)  # 2=dark, 3=light, 4=dark, 5=light

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

    # --- Slide 6: REVEAL ---
    reveal_text = reveal.get("text", "")
    reveal_number = reveal.get("number")
    reveal_label = reveal.get("label")

    img6 = generate_slide_reveal(
        text=reveal_text,
        number=reveal_number,
        label=reveal_label,
        theme=theme,
        total_slides=total_slides_count,
    )
    p6 = out / f"{content_id}_slide_06_reveal.png"
    img6.save(str(p6), "PNG", quality=95)
    saved_paths.append(str(p6))
    print(f"    slide 06 (REVEAL): {reveal_text[:30]}...")

    # --- Slide 7: CTA ---
    img7 = generate_slide_cta(cta_type=cta_type, theme=theme, total_slides=total_slides_count)
    p7 = out / f"{content_id}_slide_07_cta.png"
    img7.save(str(p7), "PNG", quality=95)
    saved_paths.append(str(p7))
    print(f"    slide 07 (CTA: {cta_type})")

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

    middle = slide_texts[1:-1] if len(slide_texts) > 2 else [slide_texts[1] if len(slide_texts) > 1 else ""]
    content_slides: list[dict] = []
    for i in range(4):
        if i < len(middle):
            text = middle[i]
            title, body = _split_title_body(text)
            content_slides.append({"title": title, "body": body})
        else:
            if content_slides:
                content_slides.append(content_slides[-1].copy())
            else:
                content_slides.append({"title": "...", "body": "..."})

    reveal_text = slide_texts[-1] if slide_texts else ""

    return {
        "content_id": content_id,
        "hook": hook,
        "slides": content_slides,
        "reveal": {"text": reveal_text},
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
                reveal=content["reveal"],
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

def generate_demo(output_dir: str = "content/generated/carousel_demo") -> list[str]:
    """Generate a sample carousel set for review."""
    print("=== Generating demo carousel ===\n")

    return generate_carousel(
        content_id="DEMO",
        hook="転職エージェントの手数料\n知ってますか？",
        slides=[
            {
                "title": "看護師は無料で使える",
                "body": "でも、病院側は年収の20〜30%を\nエージェントに支払っています。\n\n・年収400万 → 手数料80〜120万円\n・年収500万 → 手数料100〜150万円",
            },
            {
                "title": "手数料が高いと何が起きる？",
                "body": "病院は高い手数料を払った分\n採用のハードルを上げます。\n\n・面接が厳しくなる\n・条件交渉が通りにくい\n・「すぐ辞めないで」圧が強い",
                "highlight_number": "120万円",
                "highlight_label": "大手エージェントの平均手数料（年収400万の場合）",
            },
            {
                "title": "AIで調べてみた",
                "body": "看護師転職エージェント15社の\n手数料をAIに比較させた結果:\n\n・大手A社: 年収の35%\n・大手B社: 年収の30%\n・中堅C社: 年収の25%\n・ナースロビー: 年収の10%",
            },
            {
                "title": "手数料が安いメリット",
                "body": "病院の負担が軽い\n→ 採用されやすくなる\n→ 条件交渉もしやすい\n→ 入職後の関係も良好\n\nつまり、あなたが得をする。",
            },
        ],
        reveal={
            "text": "手数料10%の\nエージェントがあります",
            "number": "10%",
            "label": "業界最安クラスの紹介手数料",
        },
        output_dir=output_dir,
        category="転職・キャリア",
        cta_type="hard",
    )


def generate_demo_aruaru(output_dir: str = "content/generated/carousel_demo_aruaru") -> list[str]:
    """Generate an aruaru-themed demo for review."""
    print("=== Generating aruaru demo carousel ===\n")

    return generate_carousel(
        content_id="DEMO_ARUARU",
        hook="「前にも言ったよね」\nAIに何回言わせたら\n怒るか",
        slides=[
            {
                "title": "先輩に言われたあの一言",
                "body": "新人の頃、質問したら返ってきた\nあの恐怖のセリフ。\n\n「それ前にも言ったよね？」\n\n心臓止まるかと思った。",
            },
            {
                "title": "AIに100回聞いてみた",
                "body": "「この薬の投与速度を教えて」\n\nこれをAIに100回聞いてみた。\n\n・1回目: 丁寧に説明\n・50回目: まだ丁寧\n・100回目: 変わらず丁寧",
            },
            {
                "title": "100回目のAIの回答",
                "body": "「何度でもお答えしますね！」\n\n全然怒らない。\nむしろ毎回ちょっと嬉しそう。\n\nこういう先輩がほしかった。",
            },
            {
                "title": "理想の先輩、AIだった",
                "body": "・何回聞いても怒らない\n・「前にも言ったよね」ゼロ\n・24時間いつでも対応\n・ため息もつかない\n\n人間の先輩にも見習ってほしい。",
            },
        ],
        reveal={
            "text": "AIは100回聞いても\n怒らない",
            "number": "0回",
            "label": "AIが「前にも言ったよね」と言った回数",
        },
        output_dir=output_dir,
        category="あるある×AI",
        cta_type="soft",
    )


# ===========================================================================
# CLI
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Professional carousel slide generator for TikTok/Instagram (7 slides, 1080x1920)",
    )
    parser.add_argument("--demo", action="store_true", help="Generate a demo carousel set for review")
    parser.add_argument("--demo-aruaru", action="store_true", help="Generate aruaru-themed demo")
    parser.add_argument("--queue", help="Path to posting_queue.json")
    parser.add_argument("--output", default="content/generated/", help="Output base directory")
    parser.add_argument(
        "--single-json", help="Generate carousel from a single slide JSON file"
    )

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent

    if args.demo:
        out = project_root / "content" / "generated" / "carousel_demo"
        paths = generate_demo(str(out))
        print(f"\nDemo complete. {len(paths)} slides saved to {out}")

    elif args.demo_aruaru:
        out = project_root / "content" / "generated" / "carousel_demo_aruaru"
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
            generate_carousel(
                content_id=content["content_id"],
                hook=content["hook"],
                slides=content["slides"],
                reveal=content["reveal"],
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
