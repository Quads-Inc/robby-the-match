#!/usr/bin/env python3
"""
video_text_animator.py — Pillowフレーム生成 + ffmpeg動画化エンジン v2.0

背景PNG + テキストメタデータJSON から、テキストアニメーション付きの
TikTok/Instagram動画を生成する。

方式: Pillow でフレーム画像を生成 → ffmpeg で動画エンコード
（drawtext不要 = 環境依存なし）

アニメーション:
  - Hook: ズームイン（1.5倍→1倍）＋フェードイン
  - Content: 行ごとの時差フェードイン
  - CTA: パルスアニメーション

使い方:
  python3 scripts/video_text_animator.py --metadata path/to/metadata.json
  python3 scripts/video_text_animator.py --test
"""

import argparse
import json
import math
import os
import random
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

PROJECT_DIR = Path(__file__).parent.parent
BGM_DIR = PROJECT_DIR / "content" / "bgm"

# Font paths
FONT_PATHS = [
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴ ProN W6.otf",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
]

FPS = 30
XFADE_TYPES = ["fade", "slideright", "slideleft", "slideup", "smoothleft"]


def find_font():
    for p in FONT_PATHS:
        if os.path.exists(p):
            return p
    return None


def find_bgm():
    if not BGM_DIR.exists():
        return None
    files = list(BGM_DIR.glob("*.mp3")) + list(BGM_DIR.glob("*.wav")) + list(BGM_DIR.glob("*.m4a"))
    return str(random.choice(files)) if files else None


def load_font(font_path, size):
    try:
        return ImageFont.truetype(font_path, size)
    except Exception:
        return ImageFont.load_default()


def wrap_text(text, font, max_width):
    """Wrap text to fit within max_width pixels.
    Breaks at natural Japanese break points (punctuation, particles).
    Returns list of lines."""
    if not text:
        return []
    # Try single line first
    bbox = font.getbbox(text)
    if (bbox[2] - bbox[0]) <= max_width:
        return [text]

    # Characters that should NOT start a line (禁則処理 - 行頭禁止)
    no_start = set("、。！？）」』】〉》〕,.!?):;>}ー〜っゃゅょぁぃぅぇぉ")
    # Characters that should NOT end a line (行末禁止)
    no_end = set("（「『【〈《〔(<{")
    # Good break points (break AFTER these)
    good_break = set("、。！？）」』】〉》〕,.!?):;>}　 ")

    lines = []
    current = ""
    last_good_break = ""  # text up to last good break point

    for ch in text:
        test = current + ch
        bbox = font.getbbox(test)
        width = bbox[2] - bbox[0]

        if width > max_width and current:
            # Try to break at last good break point
            if last_good_break and len(last_good_break) > 1:
                lines.append(last_good_break)
                remaining = current[len(last_good_break):] + ch
                current = remaining
                last_good_break = ""
            else:
                # No good break point - break at current position
                # But avoid breaking before no_start chars
                if ch in no_start and len(current) > 1:
                    lines.append(current[:-1])
                    current = current[-1] + ch
                else:
                    lines.append(current)
                    current = ch
                last_good_break = ""
        else:
            current = test
            if ch in good_break:
                last_good_break = current

    if current:
        lines.append(current)
    return lines


# Paragraph break marker for tracking paragraph gaps in wrapped text
_PARA_BREAK = "\x00"


def ease_out_cubic(t):
    """Ease-out cubic for smooth deceleration."""
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    """Ease-in-out for smooth transitions."""
    if t < 0.5:
        return 2 * t * t
    return 1 - (-2 * t + 2) ** 2 / 2


def ease_out_back(t):
    """Ease-out with overshoot (bouncy pop effect)."""
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)


def ease_out_bounce(t):
    """Ease-out with bounce effect."""
    n1 = 7.5625
    d1 = 2.75
    if t < 1 / d1:
        return n1 * t * t
    elif t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    elif t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    else:
        t -= 2.625 / d1
        return n1 * t * t + 0.984375


# ============================================================
# Glow + Transition helpers
# ============================================================

# Default accent colors for glow by category theme
_GLOW_ACCENT_COLORS = {
    "あるある": (255, 100, 150),      # warm pink
    "転職": (100, 180, 255),          # cool blue
    "給与": (255, 200, 80),           # gold
    "default": (180, 140, 255),       # soft purple
}


def _apply_glow(frame_rgba, overlay, dark=True, accent_color=None):
    """Apply glow effect: colored glow for dark slides, white glow for light.

    Args:
        frame_rgba: Base frame as RGBA
        overlay: Text overlay as RGBA (transparent bg with text)
        dark: Whether the slide is dark-themed
        accent_color: RGB tuple for glow color on dark slides

    Returns:
        Composited RGBA frame with glow + sharp text
    """
    if dark:
        radius = 15
        glow = overlay.copy()
        if accent_color:
            # Use overlay alpha as mask to tint the glow with accent color
            glow = Image.composite(
                Image.new("RGBA", overlay.size, (*accent_color, 255)),
                Image.new("RGBA", overlay.size, (0, 0, 0, 0)),
                glow.split()[3],
            )
        glow = glow.filter(ImageFilter.GaussianBlur(radius=radius))
        frame_rgba = Image.alpha_composite(frame_rgba, glow)
        frame_rgba = Image.alpha_composite(frame_rgba, overlay)
    else:
        radius = 8
        # White glow for light slides
        white_glow = Image.composite(
            Image.new("RGBA", overlay.size, (255, 255, 255, 255)),
            Image.new("RGBA", overlay.size, (0, 0, 0, 0)),
            overlay.split()[3],
        )
        white_glow = white_glow.filter(ImageFilter.GaussianBlur(radius=radius))
        frame_rgba = Image.alpha_composite(frame_rgba, white_glow)
        frame_rgba = Image.alpha_composite(frame_rgba, overlay)
    return frame_rgba


def directional_wipe(frame1, frame2, progress, direction="left"):
    """Directional wipe transition between two frames.

    Args:
        frame1: Outgoing frame (RGB)
        frame2: Incoming frame (RGB)
        progress: 0.0 to 1.0
        direction: 'left' or 'up'

    Returns:
        Blended RGB frame
    """
    w, h = frame1.size
    mask = Image.new("L", (w, h), 0)
    mask_draw = ImageDraw.Draw(mask)
    p = ease_in_out(progress)
    if direction == "left":
        mask_draw.rectangle([(0, 0), (int(w * p), h)], fill=255)
    elif direction == "up":
        mask_draw.rectangle([(0, 0), (w, int(h * p))], fill=255)
    else:
        # fallback to left
        mask_draw.rectangle([(0, 0), (int(w * p), h)], fill=255)
    # Soften the wipe edge
    mask = mask.filter(ImageFilter.GaussianBlur(radius=30))
    return Image.composite(frame2, frame1, mask)


def _color_grade(frame):
    """Apply subtle warmth / saturation boost to final frame."""
    enhancer = ImageEnhance.Color(frame)
    return enhancer.enhance(1.06)


# ============================================================
# Frame renderers for each slide type
# ============================================================

def render_hook_frame(bg_img, slide_meta, font_path, t, duration, slide_index=0):
    """Render a single frame of the Hook slide with smooth zoom-in animation.

    P1b fix: Render text at max size (1.4x) once, then scale layer down
    per frame using LANCZOS to avoid pixel jitter from font-size changes.
    P1a: Glow effect applied to text overlay.
    """
    frame = bg_img.copy()
    w, h = frame.size

    text = slide_meta["text"]
    base_size = slide_meta.get("font_size", 120)
    color = tuple(slide_meta.get("color", [255, 255, 255]))
    dark = slide_meta.get("dark", True)
    category = slide_meta.get("category", "default")
    accent = _GLOW_ACCENT_COLORS.get(category, _GLOW_ACCENT_COLORS["default"])

    # --- Render text at MAXIMUM size on an oversized canvas (once per concept) ---
    max_font_size = int(base_size * 1.4)
    font = load_font(font_path, max_font_size)

    # Oversized canvas (2x) so scaling down keeps quality
    canvas_2w = w * 2
    canvas_2h = h * 2
    max_text_w = canvas_2w - 240  # safe margins scaled up
    lines = wrap_text(text, font, max_text_w)
    line_height = int(max_font_size * 1.3)
    total_text_h = line_height * len(lines)

    text_layer = Image.new("RGBA", (canvas_2w, canvas_2h), (0, 0, 0, 0))
    tdraw = ImageDraw.Draw(text_layer)

    # Fade-in: 0→255 over 0.4s
    fade_dur = 0.4
    alpha = min(255, int(255 * min(t / fade_dur, 1.0)))

    for i, line in enumerate(lines):
        bbox = font.getbbox(line)
        tw = bbox[2] - bbox[0]
        x = (canvas_2w - tw) // 2
        y = (canvas_2h - total_text_h) // 2 + i * line_height
        # Shadow
        tdraw.text((x + 6, y + 6), line, fill=(0, 0, 0, alpha // 2), font=font)
        # Main text
        tdraw.text((x, y), line, fill=(*color, alpha), font=font)

    # --- Zoom-in: scale 1.4 → 1.0 over 0.5s ---
    zoom_dur = 0.5
    if t < zoom_dur:
        progress = ease_out_cubic(t / zoom_dur)
        scale = 1.4 - 0.4 * progress
    else:
        scale = 1.0

    # Scale the pre-rendered text layer
    # At scale=1.4, show full oversized canvas → at scale=1.0, show 1/1.4 of it
    new_w = int(canvas_2w * (1.0 / 1.4) * scale)
    new_h = int(canvas_2h * (1.0 / 1.4) * scale)
    new_w = max(1, new_w)
    new_h = max(1, new_h)
    scaled = text_layer.resize((new_w, new_h), Image.LANCZOS)

    # Center scaled layer onto frame-sized overlay
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ox = (w - new_w) // 2
    oy = (h - new_h) // 2
    overlay.paste(scaled, (ox, oy), scaled)

    # Apply glow
    frame_rgba = frame.convert("RGBA")
    frame_rgba = _apply_glow(frame_rgba, overlay, dark=dark, accent_color=accent)

    # Color grading
    result = _color_grade(frame_rgba.convert("RGB"))
    return result


def _draw_card_bg(odraw, x, y, w, h, dark, alpha):
    """Draw a rounded-corner semi-transparent card background for readability."""
    if dark:
        fill = (0, 0, 0, int(alpha * 0.45))
    else:
        fill = (255, 255, 255, int(alpha * 0.35))
    r = 24  # corner radius
    # Simple rounded rect via rectangles + circles
    odraw.rectangle([(x + r, y), (x + w - r, y + h)], fill=fill)
    odraw.rectangle([(x, y + r), (x + w, y + h - r)], fill=fill)
    odraw.ellipse([(x, y), (x + 2*r, y + 2*r)], fill=fill)
    odraw.ellipse([(x + w - 2*r, y), (x + w, y + 2*r)], fill=fill)
    odraw.ellipse([(x, y + h - 2*r), (x + 2*r, y + h)], fill=fill)
    odraw.ellipse([(x + w - 2*r, y + h - 2*r), (x + w, y + h)], fill=fill)


def render_content_frame(bg_img, slide_meta, font_path, t, duration, slide_index=0):
    """Render a single frame of Content slide with animation variety.

    P2a: Three animation styles selected by slide_index:
      - Style 0: Stagger fade + slide-up (original)
      - Style 1: Slide-in from left
      - Style 2: Scale pop (ease_out_back)
    P1a: Glow effect applied to text overlay.
    """
    frame = bg_img.copy()

    color = tuple(slide_meta.get("color", [255, 255, 255]))
    card_x = slide_meta.get("card_x", 80)
    card_y = slide_meta.get("card_y", 230)

    title = slide_meta.get("title", "")
    body = slide_meta.get("body", "")
    title_size = slide_meta.get("title_font_size", 64)
    body_size = slide_meta.get("body_font_size", 44)  # slightly smaller for readability
    hl_num = slide_meta.get("highlight_number")
    dark = slide_meta.get("dark", True)
    category = slide_meta.get("category", "default")
    accent = _GLOW_ACCENT_COLORS.get(category, _GLOW_ACCENT_COLORS["default"])

    # Select animation style based on slide index
    anim_style = slide_index % 3  # 0=stagger, 1=slide_left, 2=scale_pop

    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)

    # Available text width (card_w minus padding)
    card_w = slide_meta.get("card_w", 880)
    card_pad = 50  # padding inside card
    text_max_w = card_w - card_pad * 2

    # --- Pre-calculate all text layout for card height ---
    font_title = load_font(font_path, title_size)
    font_body = load_font(font_path, body_size)
    title_line_h = int(title_size * 1.4)
    body_line_h = int(body_size * 1.8)  # generous line height for readability
    para_gap = int(body_size * 0.7)     # extra gap between paragraphs

    title_lines = wrap_text(title, font_title, text_max_w) if title else []

    # Split body by \n for paragraph breaks, then wrap each paragraph
    raw_paras = body.split("\n") if "\n" in body else [body] if body else []
    body_items = []  # list of (line_text, is_para_start)
    for pi, para in enumerate(raw_paras):
        para = para.strip()
        if not para:
            continue
        wrapped = wrap_text(para, font_body, text_max_w)
        for li, wl in enumerate(wrapped):
            body_items.append((wl, li == 0 and pi > 0))  # para_start if not first para

    # Calculate total content height for card background
    title_block_h = len(title_lines) * title_line_h if title_lines else 0
    title_body_gap = 30 if title_lines else 0
    body_block_h = 0
    for i, (_, is_para_start) in enumerate(body_items):
        if is_para_start:
            body_block_h += para_gap
        body_block_h += body_line_h
    hl_block_h = 120 if hl_num else 0
    total_content_h = title_block_h + title_body_gap + body_block_h + hl_block_h + card_pad * 2

    # Center card vertically in safe area
    canvas_h = frame.size[1]
    safe_top = 150
    safe_bottom = 250
    available_h = canvas_h - safe_top - safe_bottom
    card_y_centered = safe_top + max(0, (available_h - total_content_h) // 2)

    # --- Draw card background (fades in with title) ---
    card_alpha = min(255, int(255 * min(t / 0.3, 1.0)))
    _draw_card_bg(odraw, card_x, card_y_centered, card_w, total_content_h, dark, card_alpha)

    # --- Title ---
    cursor_y = card_y_centered + card_pad
    title_lines_count = len(title_lines)
    if title_lines:
        title_fade = 0.4
        title_alpha = min(255, int(255 * min(t / title_fade, 1.0)))
        tx = card_x + card_pad
        for j, tl in enumerate(title_lines):
            tly = cursor_y + j * title_line_h
            # Shadow
            odraw.text((tx + 2, tly + 2), tl, fill=(0, 0, 0, title_alpha // 3), font=font_title)
            odraw.text((tx, tly), tl, fill=(*color, title_alpha), font=font_title)
        cursor_y += title_lines_count * title_line_h + title_body_gap

    # Decorative accent line under title
    if title_lines and card_alpha > 50:
        accent_line_color = (*color[:3], min(card_alpha, 120))
        line_y = cursor_y - title_body_gap // 2
        odraw.rectangle(
            [(card_x + card_pad, line_y), (card_x + card_pad + 60, line_y + 3)],
            fill=accent_line_color,
        )

    # --- Body lines with animation variety ---
    body_base_delay = 0.35
    fade_time = 0.3
    body_y = cursor_y
    w = frame.size[0]

    for i, (line, is_para_start) in enumerate(body_items[:8]):
        if is_para_start:
            body_y += para_gap  # extra gap before new paragraph

        if anim_style == 0:
            # Style A: Stagger fade + slide-up (original)
            line_delay = 0.15
            line_start = body_base_delay + i * line_delay
            if t < line_start:
                body_y += body_line_h
                continue
            line_t = t - line_start
            alpha = min(255, int(255 * min(line_t / fade_time, 1.0)))
            slide_progress = ease_out_cubic(min(line_t / fade_time, 1.0))
            y_offset = int(15 * (1 - slide_progress))
            x_offset = 0

            lx = card_x + card_pad + x_offset
            ly = body_y + y_offset

            odraw.text((lx + 2, ly + 2), line, fill=(0, 0, 0, alpha // 3), font=font_body)
            odraw.text((lx, ly), line, fill=(*color, alpha), font=font_body)

        elif anim_style == 1:
            # Style B: Slide-in from left
            line_delay = 0.15
            line_start = body_base_delay + i * line_delay
            if t < line_start:
                body_y += body_line_h
                continue
            line_t = t - line_start
            alpha = min(255, int(255 * min(line_t / fade_time, 1.0)))
            slide_progress = ease_out_cubic(min(line_t / 0.4, 1.0))
            x_offset = int(-200 * (1 - slide_progress))

            lx = card_x + card_pad + x_offset
            ly = body_y

            odraw.text((lx + 2, ly + 2), line, fill=(0, 0, 0, alpha // 3), font=font_body)
            odraw.text((lx, ly), line, fill=(*color, alpha), font=font_body)

        elif anim_style == 2:
            # Style C: Scale pop (ease_out_back)
            line_delay = 0.2
            line_start = body_base_delay + i * line_delay
            if t < line_start:
                body_y += body_line_h
                continue
            line_t = t - line_start
            alpha = min(255, int(255 * min(line_t / fade_time, 1.0)))

            # Scale from 0.5x to 1.0x with overshoot
            scale_progress = min(line_t / 0.35, 1.0)
            scale = 0.5 + 0.5 * ease_out_back(scale_progress)
            # Clamp scale to avoid excessive overshoot
            scale = min(scale, 1.15)

            # Render line on a temporary layer, then scale it
            lx = card_x + card_pad
            line_bbox = font_body.getbbox(line)
            line_w = line_bbox[2] - line_bbox[0]
            line_h_px = line_bbox[3] - line_bbox[1]
            pad = 20
            line_layer = Image.new("RGBA", (line_w + pad * 2, line_h_px + pad * 2), (0, 0, 0, 0))
            ll_draw = ImageDraw.Draw(line_layer)
            ll_draw.text((pad + 2, pad + 2), line, fill=(0, 0, 0, alpha // 3), font=font_body)
            ll_draw.text((pad, pad), line, fill=(*color, alpha), font=font_body)

            # Scale the line layer
            new_lw = max(1, int(line_layer.width * scale))
            new_lh = max(1, int(line_layer.height * scale))
            scaled_line = line_layer.resize((new_lw, new_lh), Image.LANCZOS)

            # Center the scaled line at the original position
            paste_x = lx - (new_lw - line_layer.width) // 2 - pad
            paste_y = body_y - (new_lh - line_layer.height) // 2

            overlay.paste(scaled_line, (paste_x, paste_y), scaled_line)

        body_y += body_line_h

    # --- Highlight number (large, centered, delayed) ---
    if hl_num:
        hl_delay = 0.6
        if t >= hl_delay:
            hl_t = t - hl_delay
            hl_alpha = min(255, int(255 * min(hl_t / 0.4, 1.0)))
            font_hl = load_font(font_path, 96)
            hl_text = str(hl_num)
            hl_bbox = font_hl.getbbox(hl_text)
            hl_w = hl_bbox[2] - hl_bbox[0]
            hl_x = (w - hl_w) // 2
            hl_y = body_y + 20

            # P1b fix: Render at max size and scale down
            max_hl_size = int(96 * 1.3)
            font_hl_max = load_font(font_path, max_hl_size)
            hl_layer = Image.new("RGBA", (w, 200), (0, 0, 0, 0))
            hl_draw = ImageDraw.Draw(hl_layer)
            hl_bbox_max = font_hl_max.getbbox(hl_text)
            hl_w_max = hl_bbox_max[2] - hl_bbox_max[0]
            hl_draw.text(((w - hl_w_max) // 2, 20), hl_text,
                         fill=(*color, hl_alpha), font=font_hl_max)

            scale_progress = ease_out_cubic(min(hl_t / 0.3, 1.0))
            hl_scale = 1.3 - 0.3 * scale_progress  # 1.3 → 1.0
            new_hl_w = max(1, int(w * (1.0 / 1.3) * hl_scale))
            new_hl_h = max(1, int(200 * (1.0 / 1.3) * hl_scale))
            scaled_hl = hl_layer.resize((new_hl_w, new_hl_h), Image.LANCZOS)

            hl_paste_x = (w - new_hl_w) // 2
            hl_paste_y = hl_y - (new_hl_h - 200) // 2
            overlay.paste(scaled_hl, (hl_paste_x, hl_paste_y), scaled_hl)

    # Apply glow + composite
    frame_rgba = frame.convert("RGBA")
    frame_rgba = _apply_glow(frame_rgba, overlay, dark=dark, accent_color=accent)

    # Color grading
    result = _color_grade(frame_rgba.convert("RGB"))
    return result


def render_cta_frame(bg_img, slide_meta, font_path, t, duration, slide_index=0):
    """Render CTA frame with smooth pulse animation.

    P1b fix: Render text at max pulse size, then scale layer for pulse
    instead of changing font size per frame.
    P1a: Glow effect applied.
    """
    frame = bg_img.copy()
    w, h = frame.size

    texts = slide_meta.get("texts", ["保存してね"])
    base_size = slide_meta.get("font_size", 56)
    dark = slide_meta.get("dark", True)
    category = slide_meta.get("category", "default")
    accent = _GLOW_ACCENT_COLORS.get(category, _GLOW_ACCENT_COLORS["default"])

    # Fade in over 0.4s
    fade_dur = 0.4
    alpha = min(255, int(255 * min(t / fade_dur, 1.0)))

    # Pulse after fade: ±3px equivalent scale at 1.5Hz
    max_pulse_font = base_size + 3  # max size during pulse
    if t > fade_dur:
        pulse_val = math.sin(2 * math.pi * 1.5 * (t - fade_dur))
        # scale ranges from (base-3)/max to (base+3)/max
        scale = (base_size + 3 * pulse_val) / max_pulse_font
    else:
        scale = base_size / max_pulse_font

    # Render text at MAX pulse size on a text layer
    font = load_font(font_path, max_pulse_font)
    max_text_w = w - 160
    line_h = int(max_pulse_font * 1.8)

    # Pre-wrap all text lines at max size
    all_lines = []
    para_gaps = []  # indices where paragraph gaps occur
    for ti, text in enumerate(texts):
        wrapped = wrap_text(text, font, max_text_w)
        if ti > 0:
            para_gaps.append(len(all_lines))
        all_lines.extend(wrapped)

    # Calculate total height and center vertically
    total_h = len(all_lines) * line_h + len(para_gaps) * int(line_h * 0.5)
    start_y = (h - total_h) // 2 - 40  # slightly above center

    # Draw on oversized text layer
    text_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    tdraw = ImageDraw.Draw(text_layer)

    current_y = start_y
    for i, wl in enumerate(all_lines):
        if i in para_gaps:
            current_y += int(line_h * 0.5)  # paragraph gap

        bbox = font.getbbox(wl)
        tw = bbox[2] - bbox[0]
        x = (w - tw) // 2

        tdraw.text((x + 2, current_y + 2), wl, fill=(0, 0, 0, alpha // 3), font=font)
        tdraw.text((x, current_y), wl, fill=(255, 255, 255, alpha), font=font)
        current_y += line_h

    # Brand watermark (bottom area)
    font_brand = load_font(font_path, 36)
    brand = "ナースロビー"
    brand_bbox = font_brand.getbbox(brand)
    brand_w = brand_bbox[2] - brand_bbox[0]
    brand_y = h - 520  # above TikTok bottom UI
    tdraw.text(((w - brand_w) // 2, brand_y), brand,
               fill=(255, 255, 255, int(alpha * 0.5)), font=font_brand)

    # Scale the text layer for pulse effect
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    scaled = text_layer.resize((new_w, new_h), Image.LANCZOS)

    # Center scaled layer
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ox = (w - new_w) // 2
    oy = (h - new_h) // 2
    overlay.paste(scaled, (ox, oy), scaled)

    # Apply glow
    frame_rgba = frame.convert("RGBA")
    frame_rgba = _apply_glow(frame_rgba, overlay, dark=dark, accent_color=accent)

    # Color grading
    result = _color_grade(frame_rgba.convert("RGB"))
    return result


# ============================================================
# Main video generation
# ============================================================

def generate_animated_video(metadata_path, output_path=None, with_bgm=True):
    """Generate animated video from background PNGs + text metadata."""
    meta_path = Path(metadata_path)
    with open(meta_path, encoding="utf-8") as f:
        metadata = json.load(f)

    bg_dir = meta_path.parent
    content_id = metadata["content_id"]
    canvas_w = metadata["canvas"]["w"]
    canvas_h = metadata["canvas"]["h"]
    slides_meta = metadata["slides"]

    if output_path is None:
        output_path = bg_dir / f"{content_id}_animated.mp4"
    output_path = Path(output_path)

    font_path = find_font()
    if not font_path:
        print("[ERROR] No Japanese font found")
        return None

    bg_files = sorted(bg_dir.glob(f"{content_id}_bg_*.png"))
    if len(bg_files) != len(slides_meta):
        print(f"[ERROR] bg count ({len(bg_files)}) != slides ({len(slides_meta)})")
        return None

    # Load backgrounds
    backgrounds = [Image.open(f).convert("RGB").resize((canvas_w, canvas_h)) for f in bg_files]

    # Calculate timing
    slide_timings = []
    current = 0.0
    for sm in slides_meta:
        dur = sm.get("duration", 3.0)
        slide_timings.append((current, dur))
        current += dur
    total_duration = current

    total_frames = int(total_duration * FPS)
    print(f"[ANIM] {content_id}: {len(slides_meta)} slides, {total_duration:.1f}s, {total_frames} frames")

    # Render all frames to a temp directory
    with tempfile.TemporaryDirectory(prefix="anim_") as tmpdir:
        tmpdir = Path(tmpdir)
        frame_pattern = tmpdir / "frame_%05d.jpg"

        # Transition: cross-fade / directional wipe between slides (0.3s overlap)
        xfade_dur = 0.3

        # P2b: Transition type per slide boundary
        # Pattern: fade → wipe_left → wipe_up → fade → ...
        _TRANSITION_TYPES = ["fade", "wipe_left", "wipe_up"]

        for frame_idx in range(total_frames):
            t = frame_idx / FPS

            # Find which slide we're on
            slide_idx = 0
            local_t = t
            for i, (start, dur) in enumerate(slide_timings):
                if t >= start and t < start + dur:
                    slide_idx = i
                    local_t = t - start
                    break
            else:
                slide_idx = len(slides_meta) - 1
                local_t = t - slide_timings[-1][0]

            sm = slides_meta[slide_idx]
            bg = backgrounds[slide_idx]
            dur = sm.get("duration", 3.0)

            # Check if we're in a crossfade zone
            _, cur_dur = slide_timings[slide_idx]
            time_to_end = (slide_timings[slide_idx][0] + cur_dur) - t

            if slide_idx < len(slides_meta) - 1 and time_to_end < xfade_dur:
                # Transition zone: blend current and next slide
                next_idx = slide_idx + 1
                blend_factor = 1.0 - (time_to_end / xfade_dur)

                # Render current frame
                frame1 = _render_slide_frame(bg, sm, font_path, local_t, dur,
                                             slide_index=slide_idx)
                # Render next frame (t=0 for next)
                next_bg = backgrounds[next_idx]
                next_sm = slides_meta[next_idx]
                next_dur = next_sm.get("duration", 3.0)
                frame2 = _render_slide_frame(next_bg, next_sm, font_path, 0, next_dur,
                                             slide_index=next_idx)

                # P2b: Select transition type
                trans_type = _TRANSITION_TYPES[slide_idx % len(_TRANSITION_TYPES)]
                if trans_type == "fade":
                    frame = Image.blend(frame1, frame2, blend_factor)
                elif trans_type == "wipe_left":
                    frame = directional_wipe(frame1, frame2, blend_factor, direction="left")
                elif trans_type == "wipe_up":
                    frame = directional_wipe(frame1, frame2, blend_factor, direction="up")
                else:
                    frame = Image.blend(frame1, frame2, blend_factor)
            else:
                frame = _render_slide_frame(bg, sm, font_path, local_t, dur,
                                            slide_index=slide_idx)

            # Save frame
            frame_path = tmpdir / f"frame_{frame_idx:05d}.jpg"
            frame.save(str(frame_path), "JPEG", quality=92)

            if frame_idx % (FPS * 2) == 0:
                print(f"  Frame {frame_idx}/{total_frames} ({t:.1f}s)")

        print(f"  All {total_frames} frames rendered. Encoding...")

        # Encode with ffmpeg
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(FPS),
            "-i", str(tmpdir / "frame_%05d.jpg"),
        ]

        bgm_path = find_bgm() if with_bgm else None
        if bgm_path:
            cmd.extend(["-i", bgm_path])

        cmd.extend([
            "-c:v", "libx264",
            "-profile:v", "high",
            "-level", "4.2",
            "-preset", "medium",
            "-crf", "18",
            "-maxrate", "15M",
            "-bufsize", "20M",
            "-pix_fmt", "yuv420p",
            "-r", str(FPS),
            "-movflags", "+faststart",
        ])

        if bgm_path:
            cmd.extend([
                "-map", "0:v", "-map", "1:a",
                "-af", f"volume=0.15,afade=t=in:d=1,afade=t=out:st={total_duration-1.5}:d=1.5",
                "-shortest",
            ])

        cmd.extend(["-t", str(total_duration), str(output_path)])

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print(f"  [FFMPEG] Error:\n{result.stderr[-300:]}")
            return None

    size_mb = os.path.getsize(str(output_path)) / (1024 * 1024)
    print(f"  [OK] {output_path} ({size_mb:.1f} MB)")
    return str(output_path)


def _render_slide_frame(bg, slide_meta, font_path, t, duration, slide_index=0):
    """Dispatch to the correct renderer based on slide type."""
    slide_type = slide_meta.get("type", "content")
    if slide_type == "hook":
        return render_hook_frame(bg, slide_meta, font_path, t, duration, slide_index=slide_index)
    elif slide_type == "cta":
        return render_cta_frame(bg, slide_meta, font_path, t, duration, slide_index=slide_index)
    else:
        return render_content_frame(bg, slide_meta, font_path, t, duration, slide_index=slide_index)


# ============================================================
# Test
# ============================================================

def generate_test_video():
    """Generate a test video with dummy content."""
    try:
        import numpy as np
        has_np = True
    except ImportError:
        has_np = False

    test_dir = Path("/tmp/video_animator_test")
    test_dir.mkdir(parents=True, exist_ok=True)

    # Create gradient backgrounds
    gradients = [
        ((60, 15, 35), (100, 25, 55)),
        ((15, 30, 65), (30, 55, 100)),
        ((50, 15, 60), (80, 25, 90)),
        ((15, 30, 65), (30, 55, 100)),
        ((26, 60, 120), (50, 100, 200)),
    ]

    for i, (c1, c2) in enumerate(gradients):
        img = Image.new("RGB", (1080, 1920))
        draw = ImageDraw.Draw(img)
        for y in range(1920):
            r = int(c1[0] + (c2[0] - c1[0]) * y / 1920)
            g = int(c1[1] + (c2[1] - c1[1]) * y / 1920)
            b = int(c1[2] + (c2[2] - c1[2]) * y / 1920)
            draw.line([(0, y), (1079, y)], fill=(r, g, b))
        stype = "hook" if i == 0 else ("cta" if i == 4 else "content")
        img.save(test_dir / f"TEST_bg_{i+1:02d}_{stype}.png")

    metadata = {
        "content_id": "TEST",
        "platform": "tiktok",
        "canvas": {"w": 1080, "h": 1920},
        "safe_zones": {"top": 150, "bottom": 250, "left": 60, "right": 100},
        "total_slides": 5,
        "category": "あるある",
        "cta_type": "soft",
        "slides": [
            {"type": "hook", "text": "夜勤明けの顔", "font_size": 120, "color": [255, 255, 255],
             "animation": "zoom_in", "duration": 2.5},
            {"type": "content", "dark": True, "title": "AI年齢判定してみた",
             "title_font_size": 64, "body": "結果は+10歳\n夜勤明けは老ける\nAIは正直すぎ",
             "body_font_size": 48, "color": [255, 255, 255], "card_x": 80, "card_y": 230,
             "card_w": 920, "animation": "fade_in_stagger", "duration": 3.5},
            {"type": "content", "dark": False, "title": "他の看護師も試した",
             "title_font_size": 64, "body": "みんな同じ結果\n夜勤は老化の敵",
             "body_font_size": 48, "color": [255, 255, 255], "card_x": 80, "card_y": 230,
             "card_w": 920, "animation": "fade_in_stagger", "duration": 3.5},
            {"type": "content", "dark": True, "title": "データで見る影響",
             "title_font_size": 64, "body": "平均5歳老けて見える",
             "body_font_size": 48, "color": [255, 255, 255], "card_x": 80, "card_y": 230,
             "card_w": 920, "highlight_number": "+5歳",
             "animation": "fade_in_stagger", "duration": 3.5},
            {"type": "cta", "cta_type": "soft", "texts": ["保存してね", "フォローで続き見れるよ"],
             "font_size": 56, "color": [255, 255, 255], "animation": "pulse", "duration": 3.0},
        ],
    }

    meta_path = test_dir / "TEST_text_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    output = test_dir / "TEST_animated.mp4"
    result = generate_animated_video(str(meta_path), str(output), with_bgm=False)

    if result:
        size_mb = os.path.getsize(result) / (1024 * 1024)
        print(f"\n[TEST] Success! {size_mb:.1f} MB")
        print(f"  open {result}")
    else:
        print("\n[TEST] Failed")

    return result


def main():
    parser = argparse.ArgumentParser(description="テキストアニメーション動画生成 v2.0")
    parser.add_argument("--metadata", help="テキストメタデータJSON")
    parser.add_argument("--output", help="出力MP4パス")
    parser.add_argument("--no-bgm", action="store_true", help="BGMなし")
    parser.add_argument("--test", action="store_true", help="テスト動画生成")
    args = parser.parse_args()

    if args.test:
        generate_test_video()
        return

    if not args.metadata:
        parser.print_help()
        return

    generate_animated_video(args.metadata, args.output, with_bgm=not args.no_bgm)


if __name__ == "__main__":
    main()
