#!/usr/bin/env python3
"""
generate_carousel.py — プロ品質カルーセルスライド生成エンジン

TikTok/Instagram用の9:16縦型カルーセル（7枚セット）を
Pillowのみで生成する。外部画像素材なし、純粋なプログラマティックデザイン。

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
SAFE_BOTTOM = 280
SAFE_RIGHT = 100
SAFE_LEFT = 40

# Derived safe content area
CONTENT_X = SAFE_LEFT
CONTENT_Y = SAFE_TOP
CONTENT_W = CANVAS_W - SAFE_LEFT - SAFE_RIGHT  # 940
CONTENT_H = CANVAS_H - SAFE_TOP - SAFE_BOTTOM  # 1490

# Color palette
COLOR_PRIMARY = (26, 115, 232)       # #1A73E8 trust blue
COLOR_SECONDARY = (0, 191, 165)      # #00BFA5 medical teal
COLOR_ACCENT = (255, 107, 107)       # #FF6B6B warm coral
COLOR_DARK_BG = (26, 26, 46)        # #1A1A2E deep navy
COLOR_DARK_BG2 = (22, 33, 62)       # #16213E dark gradient end
COLOR_LIGHT_BG = (248, 249, 250)    # #F8F9FA clean white
COLOR_LIGHT_BG2 = (232, 240, 254)   # #E8F0FE light gradient end
COLOR_TEXT_WHITE = (255, 255, 255)
COLOR_TEXT_DARK = (45, 45, 45)       # #2D2D2D

# Category-specific accent overrides
CATEGORY_COLORS = {
    "あるある": {
        "accent": COLOR_ACCENT,
        "primary": COLOR_PRIMARY,
    },
    "転職・キャリア": {
        "accent": (76, 175, 80),        # green
        "primary": (33, 150, 243),       # blue
    },
    "給与・待遇": {
        "accent": (255, 152, 0),         # orange
        "primary": (63, 81, 181),        # indigo
    },
    "サービス紹介": {
        "accent": COLOR_SECONDARY,
        "primary": COLOR_PRIMARY,
    },
}

# Font paths
FONT_BOLD_PATH = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"
FONT_REGULAR_PATH = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"
FONT_FALLBACK_PATH = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"

# Text rendering
LINE_HEIGHT_RATIO = 1.5
MAX_HOOK_CHARS_PER_LINE = 16
MAX_BODY_CHARS_PER_LINE = 20

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

def wrap_text_jp(text: str, font: ImageFont.FreeTypeFont, max_width: int, max_chars_hint: int = 20) -> list[str]:
    """
    Wrap Japanese text to fit within max_width pixels.
    Uses character-level breaking (standard for CJK text).
    Respects existing newlines in the input.
    """
    paragraphs = text.split("\n")
    all_lines: list[str] = []

    for para in paragraphs:
        if not para.strip():
            all_lines.append("")
            continue

        current_line = ""
        for char in para:
            test = current_line + char
            bbox = font.getbbox(test)
            w = bbox[2] - bbox[0]
            if w <= max_width:
                current_line = test
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


def text_block_height(lines: list[str], font_size: int) -> int:
    """Total height of a text block with line spacing."""
    if not lines:
        return 0
    line_h = int(font_size * LINE_HEIGHT_RATIO)
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
            a = 255
            for x in range(w):
                pixels[x, y] = (r, g, b, a)
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
    x: int,
    y: int,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple = COLOR_TEXT_WHITE,
    shadow_color: tuple = (0, 0, 0, 128),
    shadow_offset: int = 2,
):
    """Draw text with a subtle drop shadow for readability on dark backgrounds."""
    # Shadow
    draw.text((x + shadow_offset, y + shadow_offset), text, fill=shadow_color, font=font)
    # Main text
    draw.text((x, y), text, fill=fill, font=font)


def draw_centered_text_block(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: ImageFont.FreeTypeFont,
    font_size: int,
    center_x: int,
    start_y: int,
    fill: tuple = COLOR_TEXT_WHITE,
    shadow: bool = False,
    shadow_color: tuple = (0, 0, 0, 128),
    shadow_offset: int = 2,
) -> int:
    """
    Draw multiple lines of text, horizontally centered.
    Returns the Y position after the last line.
    """
    line_h = int(font_size * LINE_HEIGHT_RATIO)
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
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def draw_colored_dot(draw: ImageDraw.ImageDraw, x: int, y: int, radius: int, color: tuple):
    """Draw a small filled circle (bullet point)."""
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)


def add_subtle_noise(img: Image.Image, intensity: int = 8) -> Image.Image:
    """Add very subtle noise for a textured, non-flat feel."""
    import random
    pixels = img.load()
    w, h = img.size
    random.seed(42)  # deterministic for consistency
    for y in range(0, h, 3):
        for x in range(0, w, 3):
            r, g, b, a = pixels[x, y]
            delta = random.randint(-intensity, intensity)
            pixels[x, y] = (
                max(0, min(255, r + delta)),
                max(0, min(255, g + delta)),
                max(0, min(255, b + delta)),
                a,
            )
    return img


def draw_decorative_circles(draw: ImageDraw.ImageDraw, w: int, h: int, color: tuple, count: int = 5):
    """
    Draw subtle decorative circles in the margins/edges only.
    Circles are kept small and very transparent to avoid interfering with content.
    They are placed outside the safe content area (edges and corners).
    """
    import random
    rng = random.Random(12345)

    # Define edge zones where decorations are allowed (outside content area)
    edge_positions = [
        # (cx_range, cy_range) — corners and edges only
        ((-60, 80), (-60, 200)),           # top-left
        ((w - 80, w + 60), (-60, 200)),    # top-right
        ((-60, 80), (h - 200, h + 60)),    # bottom-left
        ((w - 80, w + 60), (h - 200, h + 60)),  # bottom-right
        ((w // 2 - 100, w // 2 + 100), (h - 60, h + 40)),  # bottom center (clipped)
        ((-80, 20), (h // 2 - 100, h // 2 + 100)),  # left-middle
        ((w - 20, w + 80), (h // 2 - 100, h // 2 + 100)),  # right-middle
    ]

    for i in range(min(count, len(edge_positions))):
        xr, yr = edge_positions[i % len(edge_positions)]
        cx = rng.randint(xr[0], xr[1])
        cy = rng.randint(yr[0], yr[1])
        r = rng.randint(20, 60)
        alpha = rng.randint(6, 15)
        c = (*color[:3], alpha)
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=c)


def draw_geometric_accent(draw: ImageDraw.ImageDraw, w: int, h: int, color: tuple):
    """Draw subtle geometric accent lines in corners, well away from content."""
    alpha = 18
    c = (*color[:3], alpha)
    # Top-right corner accents (thin, subtle)
    draw.line([(w - 120, 0), (w, 120)], fill=c, width=1)
    draw.line([(w - 180, 0), (w, 180)], fill=c, width=1)
    # Bottom-left corner accents
    draw.line([(0, h - 120), (120, h)], fill=c, width=1)
    draw.line([(0, h - 180), (180, h)], fill=c, width=1)


# ===========================================================================
# Slide generators
# ===========================================================================

def _build_dark_bg(accent_color: tuple = COLOR_PRIMARY) -> Image.Image:
    """Dark gradient background with decorative elements."""
    bg = create_gradient(CANVAS_W, CANVAS_H, COLOR_DARK_BG, COLOR_DARK_BG2)
    draw = ImageDraw.Draw(bg)
    draw_decorative_circles(draw, CANVAS_W, CANVAS_H, accent_color, count=7)
    draw_geometric_accent(draw, CANVAS_W, CANVAS_H, accent_color)
    return bg


def _build_light_bg(accent_color: tuple = COLOR_PRIMARY) -> Image.Image:
    """Light gradient background with subtle accents."""
    bg = create_gradient(CANVAS_W, CANVAS_H, COLOR_LIGHT_BG, COLOR_LIGHT_BG2)
    draw = ImageDraw.Draw(bg)
    draw_decorative_circles(draw, CANVAS_W, CANVAS_H, accent_color, count=3)
    # Subtle top accent bar
    bar_color = (*accent_color[:3], 30)
    draw.rectangle([(0, 0), (CANVAS_W, 4)], fill=bar_color)
    return bg


def _build_accent_gradient_bg(color_a: tuple, color_b: tuple) -> Image.Image:
    """Bold accent gradient background for reveal/climax slides."""
    bg = create_gradient(CANVAS_W, CANVAS_H, color_a, color_b, direction="diagonal")
    draw = ImageDraw.Draw(bg)
    draw_geometric_accent(draw, CANVAS_W, CANVAS_H, COLOR_TEXT_WHITE)
    return bg


def _build_brand_gradient_bg() -> Image.Image:
    """Blue-to-teal brand gradient for CTA slide."""
    bg = create_gradient(CANVAS_W, CANVAS_H, COLOR_PRIMARY, COLOR_SECONDARY, direction="diagonal")
    draw = ImageDraw.Draw(bg)
    draw_decorative_circles(draw, CANVAS_W, CANVAS_H, COLOR_TEXT_WHITE, count=3)
    draw_geometric_accent(draw, CANVAS_W, CANVAS_H, COLOR_TEXT_WHITE)
    return bg


def _draw_slide_number(draw: ImageDraw.ImageDraw, num: int, total: int, light_bg: bool = False):
    """Draw a small slide number indicator at the bottom of the safe zone."""
    font = load_font(bold=False, size=20)
    text = f"{num}/{total}"
    tw, _ = measure_text(text, font)
    x = CANVAS_W // 2 - tw // 2
    y = CANVAS_H - SAFE_BOTTOM + 20
    color = (150, 150, 150, 180) if light_bg else (255, 255, 255, 100)
    draw.text((x, y), text, fill=color, font=font)


def _draw_brand_watermark(draw: ImageDraw.ImageDraw, light_bg: bool = False):
    """Draw subtle brand watermark in bottom-left of safe zone."""
    font = load_font(bold=False, size=24)
    text = "ナースロビー"
    x = SAFE_LEFT + 10
    y = CANVAS_H - SAFE_BOTTOM - 40
    if light_bg:
        color = (*COLOR_TEXT_DARK[:3], 50)
    else:
        color = (*COLOR_TEXT_WHITE[:3], 50)
    draw.text((x, y), text, fill=color, font=font)


def _draw_progress_dots(draw: ImageDraw.ImageDraw, current: int, total: int, light_bg: bool = False):
    """Draw progress indicator dots at the top of the safe zone."""
    dot_radius = 5
    dot_spacing = 24
    total_width = (total - 1) * dot_spacing
    start_x = CANVAS_W // 2 - total_width // 2
    y = SAFE_TOP - 30

    for i in range(total):
        x = start_x + i * dot_spacing
        if i == current - 1:
            color = COLOR_PRIMARY if light_bg else COLOR_TEXT_WHITE
            draw_colored_dot(draw, x, y, dot_radius + 1, (*color[:3], 255))
        else:
            color = COLOR_TEXT_DARK if light_bg else COLOR_TEXT_WHITE
            draw_colored_dot(draw, x, y, dot_radius, (*color[:3], 60))


def generate_slide_hook(
    hook_text: str,
    accent_color: tuple = COLOR_PRIMARY,
    total_slides: int = 7,
) -> Image.Image:
    """
    Slide 1 - HOOK: Dark gradient, large centered hook text.
    Eye-catching, makes the viewer stop scrolling.
    """
    bg = _build_dark_bg(accent_color)
    draw = ImageDraw.Draw(bg)

    # --- Decorative accent strip at top ---
    strip_y = SAFE_TOP + 60
    strip_color = (*accent_color[:3], 60)
    draw.rectangle([(SAFE_LEFT + 100, strip_y), (CANVAS_W - SAFE_RIGHT - 100, strip_y + 4)], fill=strip_color)

    # --- Hook text: large, bold, upper 40% of safe zone ---
    hook_zone_top = SAFE_TOP + 100
    hook_zone_height = int(CONTENT_H * 0.50)
    max_text_width = CONTENT_W - 60  # extra padding

    # Try font sizes from large to small
    best_font_size = 56
    best_lines = []
    for size in range(56, 36, -2):
        font = load_font(bold=True, size=size)
        lines = wrap_text_jp(hook_text, font, max_text_width, MAX_HOOK_CHARS_PER_LINE)
        block_h = text_block_height(lines, size)
        if block_h <= hook_zone_height:
            best_font_size = size
            best_lines = lines
            break
    else:
        font = load_font(bold=True, size=38)
        best_font_size = 38
        best_lines = wrap_text_jp(hook_text, font, max_text_width, MAX_HOOK_CHARS_PER_LINE)

    font = load_font(bold=True, size=best_font_size)
    block_h = text_block_height(best_lines, best_font_size)

    # Center vertically in hook zone
    text_y = hook_zone_top + (hook_zone_height - block_h) // 2
    center_x = SAFE_LEFT + CONTENT_W // 2

    draw_centered_text_block(
        draw, best_lines, font, best_font_size,
        center_x, text_y,
        fill=COLOR_TEXT_WHITE,
        shadow=True,
        shadow_offset=3,
    )

    # --- Accent underline below text ---
    underline_y = text_y + block_h + 30
    underline_w = min(400, CONTENT_W - 100)
    underline_x = center_x - underline_w // 2
    draw.rounded_rectangle(
        (underline_x, underline_y, underline_x + underline_w, underline_y + 6),
        radius=3, fill=(*accent_color[:3], 180),
    )

    # --- Swipe hint at bottom ---
    hint_font = load_font(bold=False, size=22)
    hint_text = "スワイプして続きを見る  >>>"
    tw, _ = measure_text(hint_text, hint_font)
    hint_x = center_x - tw // 2
    hint_y = CANVAS_H - SAFE_BOTTOM - 100
    draw.text((hint_x, hint_y), hint_text, fill=(*COLOR_TEXT_WHITE[:3], 120), font=hint_font)

    # --- Watermark & indicators ---
    _draw_brand_watermark(draw, light_bg=False)
    _draw_progress_dots(draw, 1, total_slides, light_bg=False)

    return bg.convert("RGB")


def generate_slide_content(
    slide_num: int,
    title: str,
    body: str,
    highlight_number: Optional[str] = None,
    highlight_label: Optional[str] = None,
    dark_theme: bool = True,
    accent_color: tuple = COLOR_PRIMARY,
    primary_color: tuple = COLOR_PRIMARY,
    total_slides: int = 7,
) -> Image.Image:
    """
    Slides 2-5 - CONTENT: Alternating light/dark backgrounds.
    Section header, body text, optional data highlights, bullet points.
    """
    if dark_theme:
        bg = _build_dark_bg(accent_color)
    else:
        bg = _build_light_bg(accent_color)

    draw = ImageDraw.Draw(bg)
    light_bg = not dark_theme
    center_x = SAFE_LEFT + CONTENT_W // 2
    max_text_width = CONTENT_W - 80

    current_y = SAFE_TOP + 80

    # --- Section header ---
    header_font_size = 36
    header_font = load_font(bold=True, size=header_font_size)
    header_color = COLOR_TEXT_WHITE if dark_theme else primary_color
    header_lines = wrap_text_jp(title, header_font, max_text_width)

    # Accent bar before title
    bar_w = 60
    bar_h = 6
    bar_x = center_x - bar_w // 2
    draw.rounded_rectangle(
        (bar_x, current_y, bar_x + bar_w, current_y + bar_h),
        radius=3, fill=(*accent_color[:3], 200),
    )
    current_y += bar_h + 24

    current_y = draw_centered_text_block(
        draw, header_lines, header_font, header_font_size,
        center_x, current_y,
        fill=(*header_color[:3], 255),
        shadow=dark_theme,
        shadow_offset=2,
    )
    current_y += 30

    # --- Highlight number (if provided) ---
    if highlight_number:
        num_font_size = 72
        num_font = load_font(bold=True, size=num_font_size)
        tw, _ = measure_text(highlight_number, num_font)
        nx = center_x - tw // 2

        if dark_theme:
            draw_text_shadow(draw, nx, current_y, highlight_number, num_font, fill=(*accent_color[:3], 255), shadow_offset=3)
        else:
            draw.text((nx, current_y), highlight_number, fill=(*accent_color[:3], 255), font=num_font)

        current_y += int(num_font_size * 1.3)

        # Highlight label
        if highlight_label:
            label_font = load_font(bold=False, size=24)
            tw2, _ = measure_text(highlight_label, label_font)
            lx = center_x - tw2 // 2
            label_color = (200, 200, 200) if dark_theme else (120, 120, 120)
            draw.text((lx, current_y), highlight_label, fill=label_color, font=label_font)
            current_y += 50
        else:
            current_y += 30

    # --- Body text (supports bullet points with "・" prefix) ---
    body_font_size = 30
    body_font = load_font(bold=False, size=body_font_size)
    body_color = COLOR_TEXT_WHITE if dark_theme else COLOR_TEXT_DARK

    body_paragraphs = body.split("\n")
    line_h = int(body_font_size * LINE_HEIGHT_RATIO)

    for para in body_paragraphs:
        para = para.strip()
        if not para:
            current_y += line_h // 2
            continue

        is_bullet = para.startswith("・") or para.startswith("- ") or para.startswith("* ")
        if is_bullet:
            # Remove bullet prefix for wrapping
            clean_text = para.lstrip("・- *").strip()
            bullet_indent = 60
            text_start_x = SAFE_LEFT + 40 + bullet_indent
            text_max_w = max_text_width - bullet_indent - 20

            lines = wrap_text_jp(clean_text, body_font, text_max_w)

            # Draw bullet dot
            dot_x = SAFE_LEFT + 40 + bullet_indent // 2
            dot_y = current_y + body_font_size // 2
            draw_colored_dot(draw, dot_x, dot_y, 6, (*accent_color[:3], 220))

            # Draw wrapped text
            for line in lines:
                if dark_theme:
                    draw_text_shadow(draw, text_start_x, current_y, line, body_font, fill=body_color, shadow_offset=1)
                else:
                    draw.text((text_start_x, current_y), line, fill=body_color, font=body_font)
                current_y += line_h
            current_y += 8  # extra spacing between bullets
        else:
            lines = wrap_text_jp(para, body_font, max_text_width)
            current_y = draw_centered_text_block(
                draw, lines, body_font, body_font_size,
                center_x, current_y,
                fill=body_color,
                shadow=dark_theme,
                shadow_offset=1,
            )
            current_y += 10

    # --- Decorative bottom line ---
    line_y = CANVAS_H - SAFE_BOTTOM - 70
    line_w = 120
    draw.rounded_rectangle(
        (center_x - line_w // 2, line_y, center_x + line_w // 2, line_y + 3),
        radius=2, fill=(*accent_color[:3], 80),
    )

    _draw_brand_watermark(draw, light_bg=light_bg)
    _draw_progress_dots(draw, slide_num, total_slides, light_bg=light_bg)

    return bg.convert("RGB")


def generate_slide_reveal(
    text: str,
    number: Optional[str] = None,
    label: Optional[str] = None,
    accent_color: tuple = COLOR_ACCENT,
    total_slides: int = 7,
) -> Image.Image:
    """
    Slide 6 - REVEAL/CLIMAX: Dramatic accent gradient background.
    Big reveal text with optional large highlight number.
    """
    # Bold accent gradient
    darker_accent = tuple(max(0, c - 60) for c in accent_color[:3])
    bg = _build_accent_gradient_bg(accent_color, darker_accent)
    draw = ImageDraw.Draw(bg)

    center_x = SAFE_LEFT + CONTENT_W // 2
    max_text_width = CONTENT_W - 80

    # Layout from center
    elements_height = 0
    reveal_font_size = 48
    reveal_font = load_font(bold=True, size=reveal_font_size)
    reveal_lines = wrap_text_jp(text, reveal_font, max_text_width)
    reveal_block_h = text_block_height(reveal_lines, reveal_font_size)
    elements_height += reveal_block_h

    num_font_size = 80
    num_font = None
    if number:
        num_font = load_font(bold=True, size=num_font_size)
        elements_height += int(num_font_size * 1.4) + 40  # number + gap

    label_font_size = 26
    label_font = None
    if label:
        label_font = load_font(bold=False, size=label_font_size)
        elements_height += int(label_font_size * 1.5) + 10

    # Start Y centered in content area
    start_y = SAFE_TOP + (CONTENT_H - elements_height) // 2
    current_y = start_y

    # --- Reveal text ---
    current_y = draw_centered_text_block(
        draw, reveal_lines, reveal_font, reveal_font_size,
        center_x, current_y,
        fill=COLOR_TEXT_WHITE,
        shadow=True,
        shadow_offset=3,
    )
    current_y += 40

    # --- Big number ---
    if number and num_font:
        tw, _ = measure_text(number, num_font)
        nx = center_x - tw // 2

        draw_text_shadow(
            draw, nx, current_y, number, num_font,
            fill=COLOR_TEXT_WHITE,
            shadow_color=(0, 0, 0, 150),
            shadow_offset=4,
        )
        current_y += int(num_font_size * 1.3)

    # --- Label ---
    if label and label_font:
        tw, _ = measure_text(label, label_font)
        lx = center_x - tw // 2
        draw.text((lx, current_y), label, fill=(*COLOR_TEXT_WHITE[:3], 200), font=label_font)
        current_y += int(label_font_size * 1.5)

    _draw_brand_watermark(draw, light_bg=False)
    _draw_progress_dots(draw, 6, total_slides, light_bg=False)

    return bg.convert("RGB")


def generate_slide_cta(
    total_slides: int = 7,
) -> Image.Image:
    """
    Slide 7 - CTA: Brand gradient (blue to teal).
    Logo, CTA button, badge, and subtitle.
    """
    bg = _build_brand_gradient_bg()
    draw = ImageDraw.Draw(bg)

    center_x = SAFE_LEFT + CONTENT_W // 2

    # --- "ナースロビー" logo text ---
    logo_font_size = 48
    logo_font = load_font(bold=True, size=logo_font_size)
    logo_text = "ナースロビー"
    tw, _ = measure_text(logo_text, logo_font)
    logo_x = center_x - tw // 2
    logo_y = SAFE_TOP + 200

    draw_text_shadow(
        draw, logo_x, logo_y, logo_text, logo_font,
        fill=COLOR_TEXT_WHITE,
        shadow_offset=3,
    )

    # --- Tagline ---
    tag_font_size = 24
    tag_font = load_font(bold=False, size=tag_font_size)
    tag_text = "NURSE ROBBY"
    tw, _ = measure_text(tag_text, tag_font)
    tag_x = center_x - tw // 2
    tag_y = logo_y + logo_font_size + 20
    draw.text((tag_x, tag_y), tag_text, fill=(*COLOR_TEXT_WHITE[:3], 180), font=tag_font)

    # --- Separator line ---
    sep_y = tag_y + tag_font_size + 40
    sep_w = 200
    draw.rounded_rectangle(
        (center_x - sep_w // 2, sep_y, center_x + sep_w // 2, sep_y + 3),
        radius=2, fill=(*COLOR_TEXT_WHITE[:3], 100),
    )

    # --- Badge: "紹介手数料 業界最安10%" ---
    badge_y = sep_y + 50
    badge_font_size = 26
    badge_font = load_font(bold=True, size=badge_font_size)
    badge_text = "紹介手数料 業界最安10%"
    btw, bth = measure_text(badge_text, badge_font)
    badge_pad_x = 40
    badge_pad_y = 18
    badge_w = btw + badge_pad_x * 2
    badge_h = bth + badge_pad_y * 2
    badge_x = center_x - badge_w // 2

    # Badge background (semi-transparent with clear border)
    draw.rounded_rectangle(
        (badge_x, badge_y, badge_x + badge_w, badge_y + badge_h),
        radius=badge_h // 2, fill=(*COLOR_TEXT_WHITE[:3], 50),
        outline=(*COLOR_TEXT_WHITE[:3], 200), width=2,
    )
    # Badge text
    draw_text_shadow(
        draw, badge_x + badge_pad_x, badge_y + badge_pad_y,
        badge_text, badge_font,
        fill=COLOR_TEXT_WHITE,
        shadow_color=(0, 0, 0, 80),
        shadow_offset=1,
    )

    # --- CTA Button: "LINEで無料相談" ---
    btn_y = badge_y + badge_h + 60
    btn_font_size = 32
    btn_font = load_font(bold=True, size=btn_font_size)
    btn_text = "LINEで無料相談 →"
    btw2, bth2 = measure_text(btn_text, btn_font)
    btn_pad_x = 60
    btn_pad_y = 24
    btn_w = btw2 + btn_pad_x * 2
    btn_h = bth2 + btn_pad_y * 2
    btn_x = center_x - btn_w // 2

    # Button background (solid white)
    draw.rounded_rectangle(
        (btn_x, btn_y, btn_x + btn_w, btn_y + btn_h),
        radius=btn_h // 2, fill=COLOR_TEXT_WHITE,
    )
    # Button text (primary color)
    draw.text(
        (btn_x + btn_pad_x, btn_y + btn_pad_y),
        btn_text, fill=COLOR_PRIMARY, font=btn_font,
    )

    # --- Subtitle ---
    sub_y = btn_y + btn_h + 50
    sub_font_size = 24
    sub_font = load_font(bold=False, size=sub_font_size)
    sub_text = "神奈川県西部の看護師転職"
    tw, _ = measure_text(sub_text, sub_font)
    sub_x = center_x - tw // 2
    draw.text((sub_x, sub_y), sub_text, fill=(*COLOR_TEXT_WHITE[:3], 180), font=sub_font)

    # --- Bottom trust indicators ---
    trust_y = sub_y + sub_font_size + 60
    trust_font = load_font(bold=False, size=20)
    trust_items = ["有料職業紹介許可", "完全無料", "LINEで簡単相談"]
    total_trust_w = sum(measure_text(t, trust_font)[0] for t in trust_items) + 80 * (len(trust_items) - 1)
    tx = center_x - total_trust_w // 2

    for i, item in enumerate(trust_items):
        iw, _ = measure_text(item, trust_font)
        # Small check icon
        check_x = tx - 4
        check_y = trust_y + 2
        draw.text((check_x, check_y), "+", fill=(*COLOR_SECONDARY[:3], 200), font=load_font(bold=True, size=18))
        draw.text((tx + 18, trust_y), item, fill=(*COLOR_TEXT_WHITE[:3], 160), font=trust_font)
        tx += iw + 80

    _draw_brand_watermark(draw, light_bg=False)
    _draw_progress_dots(draw, 7, total_slides, light_bg=False)

    return bg.convert("RGB")


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

    Returns:
        List of saved PNG file paths
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Get color scheme
    colors = CATEGORY_COLORS.get(category, CATEGORY_COLORS["あるある"])
    accent = colors["accent"]
    primary = colors["primary"]

    total_slides_count = 7
    saved_paths: list[str] = []

    print(f"  [{content_id}] Generating {total_slides_count}-slide carousel (category: {category})")

    # --- Slide 1: HOOK ---
    img1 = generate_slide_hook(hook, accent_color=accent, total_slides=total_slides_count)
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
            accent_color=accent,
            primary_color=primary,
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
        accent_color=accent,
        total_slides=total_slides_count,
    )
    p6 = out / f"{content_id}_slide_06_reveal.png"
    img6.save(str(p6), "PNG", quality=95)
    saved_paths.append(str(p6))
    print(f"    slide 06 (REVEAL): {reveal_text[:30]}...")

    # --- Slide 7: CTA ---
    img7 = generate_slide_cta(total_slides=total_slides_count)
    p7 = out / f"{content_id}_slide_07_cta.png"
    img7.save(str(p7), "PNG", quality=95)
    saved_paths.append(str(p7))
    print(f"    slide 07 (CTA)")

    print(f"  [{content_id}] Done: {len(saved_paths)} slides saved to {out}")
    return saved_paths


# ===========================================================================
# Queue integration
# ===========================================================================

def _split_title_body(text: str) -> tuple[str, str]:
    """
    Split a slide text into a short title and longer body.
    Title target: 15 chars or less for clean single-line display.
    """
    MAX_TITLE = 18

    # Priority 1: If there's an explicit newline, use the first line as title
    if "\n" in text:
        parts = text.split("\n", 1)
        candidate = parts[0].strip()
        if len(candidate) <= MAX_TITLE:
            return candidate, parts[1].strip()

    # Priority 2: Split at first sentence ending (。) if short enough
    if "。" in text:
        parts = text.split("。", 1)
        candidate = parts[0].strip()
        if len(candidate) <= MAX_TITLE:
            return candidate + "。", parts[1].strip()

    # Priority 3: Split at first comma/delimiter if short enough
    for delim in ["、", "。", "？", "！", "…", "," ]:
        if delim in text:
            parts = text.split(delim, 1)
            candidate = parts[0].strip()
            if len(candidate) <= MAX_TITLE:
                return candidate + delim, parts[1].strip()

    # Priority 4: Truncate to make a short title, full text as body
    if len(text) > MAX_TITLE:
        return text[:MAX_TITLE] + "...", text
    return text, ""


def _extract_carousel_content(json_path: str) -> Optional[dict]:
    """
    Extract carousel content from a slide JSON file.
    Handles both the simple format (list of strings) and the structured format
    (list of dicts with slide/text/subtext/visual).

    Returns a dict with: content_id, hook, slides, reveal, category
    or None if the file cannot be parsed.
    """
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
    raw_slides = data.get("slides", [])

    if not raw_slides:
        print(f"  WARNING: No slides in {json_path}")
        return None

    # Normalize slides to list of strings
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

    # Map to our 7-slide structure:
    # slide_texts[0] -> hook (slide 1)
    # slide_texts[1:-1] -> content slides 2-5 (take up to 4)
    # slide_texts[-1] -> reveal (slide 6)
    # slide 7 = CTA (always the same)

    hook = data.get("hook", slide_texts[0])

    middle = slide_texts[1:-1] if len(slide_texts) > 2 else [slide_texts[1] if len(slide_texts) > 1 else ""]
    # Pad to 4 content slides
    content_slides: list[dict] = []
    for i in range(4):
        if i < len(middle):
            text = middle[i]
            title, body = _split_title_body(text)
            content_slides.append({"title": title, "body": body})
        else:
            # Duplicate last slide content if not enough
            if content_slides:
                content_slides.append(content_slides[-1].copy())
            else:
                content_slides.append({"title": "...", "body": "..."})

    # Reveal = last slide text
    reveal_text = slide_texts[-1] if slide_texts else ""

    return {
        "content_id": content_id,
        "hook": hook,
        "slides": content_slides,
        "reveal": {"text": reveal_text},
        "category": category,
    }


def generate_from_queue(queue_path: str, output_base: str) -> int:
    """
    Read posting_queue.json, generate carousel slides for all pending items
    that have a json_path.

    Returns number of carousel sets generated.
    """
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
    )


# ===========================================================================
# CLI
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Professional carousel slide generator for TikTok/Instagram (7 slides, 1080x1920)",
    )
    parser.add_argument("--demo", action="store_true", help="Generate a demo carousel set for review")
    parser.add_argument("--queue", help="Path to posting_queue.json")
    parser.add_argument("--output", default="content/generated/", help="Output base directory")
    parser.add_argument(
        "--single-json", help="Generate carousel from a single slide JSON file"
    )

    args = parser.parse_args()

    # Resolve project root
    project_root = Path(__file__).parent.parent

    if args.demo:
        out = project_root / "content" / "generated" / "carousel_demo"
        paths = generate_demo(str(out))
        print(f"\nDemo complete. {len(paths)} slides saved to {out}")

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
            )
        else:
            print("ERROR: Could not extract carousel content from JSON.")
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
