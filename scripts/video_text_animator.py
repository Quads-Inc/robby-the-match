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

from PIL import Image, ImageDraw, ImageFont

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
    """Wrap text to fit within max_width pixels. Returns list of lines."""
    if not text:
        return []
    # Try single line first
    bbox = font.getbbox(text)
    if (bbox[2] - bbox[0]) <= max_width:
        return [text]
    # Character-by-character wrapping for CJK text
    lines = []
    current = ""
    for ch in text:
        test = current + ch
        bbox = font.getbbox(test)
        if (bbox[2] - bbox[0]) > max_width and current:
            lines.append(current)
            current = ch
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def ease_out_cubic(t):
    """Ease-out cubic for smooth deceleration."""
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    """Ease-in-out for smooth transitions."""
    if t < 0.5:
        return 2 * t * t
    return 1 - (-2 * t + 2) ** 2 / 2


# ============================================================
# Frame renderers for each slide type
# ============================================================

def render_hook_frame(bg_img, slide_meta, font_path, t, duration):
    """Render a single frame of the Hook slide with zoom-in animation."""
    frame = bg_img.copy()
    draw = ImageDraw.Draw(frame)

    text = slide_meta["text"]
    base_size = slide_meta.get("font_size", 120)
    color = tuple(slide_meta.get("color", [255, 255, 255]))
    w, h = frame.size

    # Zoom-in: 1.4x → 1.0x over 0.5s
    zoom_dur = 0.5
    if t < zoom_dur:
        progress = ease_out_cubic(t / zoom_dur)
        scale = 1.4 - 0.4 * progress
    else:
        scale = 1.0

    # Fade-in: 0→255 over 0.4s
    fade_dur = 0.4
    alpha = min(255, int(255 * min(t / fade_dur, 1.0)))

    font_size = max(20, int(base_size * scale))
    font = load_font(font_path, font_size)

    # Safe margin (60px each side)
    max_text_w = w - 120
    lines = wrap_text(text, font, max_text_w)
    line_height = int(font_size * 1.3)
    total_h = line_height * len(lines)

    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)

    for i, line in enumerate(lines):
        bbox = font.getbbox(line)
        tw = bbox[2] - bbox[0]
        x = (w - tw) // 2
        y = (h - total_h) // 2 + i * line_height
        # Shadow
        odraw.text((x + 3, y + 3), line, fill=(0, 0, 0, alpha // 2), font=font)
        # Main text
        odraw.text((x, y), line, fill=(*color, alpha), font=font)

    frame = frame.convert("RGBA")
    frame = Image.alpha_composite(frame, overlay)
    return frame.convert("RGB")


def render_content_frame(bg_img, slide_meta, font_path, t, duration):
    """Render a single frame of Content slide with staggered text reveal."""
    frame = bg_img.copy()

    color = tuple(slide_meta.get("color", [255, 255, 255]))
    card_x = slide_meta.get("card_x", 80)
    card_y = slide_meta.get("card_y", 230)

    title = slide_meta.get("title", "")
    body = slide_meta.get("body", "")
    title_size = slide_meta.get("title_font_size", 64)
    body_size = slide_meta.get("body_font_size", 48)
    hl_num = slide_meta.get("highlight_number")

    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)

    # Available text width (card_w minus padding)
    card_w = slide_meta.get("card_w", 880)
    text_max_w = card_w - 80  # 40px padding each side

    # Title fade in (0 → 0.4s)
    title_fade = 0.4
    title_lines_count = 0
    if title:
        title_alpha = min(255, int(255 * min(t / title_fade, 1.0)))
        font_title = load_font(font_path, title_size)
        tx = card_x + 40
        ty = card_y + 80
        title_lines = wrap_text(title, font_title, text_max_w)
        title_lines_count = len(title_lines)
        for j, tl in enumerate(title_lines):
            tly = ty + j * int(title_size * 1.3)
            odraw.text((tx + 2, tly + 2), tl, fill=(0, 0, 0, title_alpha // 3), font=font_title)
            odraw.text((tx, tly), tl, fill=(*color, title_alpha), font=font_title)

    # Body lines staggered (delay=0.3s, each line +0.2s)
    body_base_delay = 0.3
    line_delay = 0.2
    fade_time = 0.3

    # Split body into lines, then wrap each
    raw_lines = body.split("\n") if "\n" in body else [body] if body else []
    font_body = load_font(font_path, body_size)
    wrapped_body = []
    for rl in raw_lines:
        rl = rl.strip()
        if rl:
            wrapped_body.extend(wrap_text(rl, font_body, text_max_w))

    # Offset body start based on title height
    body_y_start = card_y + 200 + (title_lines_count - 1) * int(title_size * 1.0)

    for i, line in enumerate(wrapped_body[:6]):
        line_start = body_base_delay + i * line_delay
        if t < line_start:
            continue
        line_t = t - line_start
        alpha = min(255, int(255 * min(line_t / fade_time, 1.0)))

        # Slide up effect: start 20px below, move to final position
        slide_progress = ease_out_cubic(min(line_t / fade_time, 1.0))
        y_offset = int(20 * (1 - slide_progress))

        lx = card_x + 40
        ly = body_y_start + i * int(body_size * 1.5) + y_offset

        odraw.text((lx + 2, ly + 2), line, fill=(0, 0, 0, alpha // 3), font=font_body)
        odraw.text((lx, ly), line, fill=(*color, alpha), font=font_body)

    # Highlight number (large, centered, delayed)
    if hl_num:
        hl_delay = 0.6
        if t >= hl_delay:
            hl_t = t - hl_delay
            hl_alpha = min(255, int(255 * min(hl_t / 0.4, 1.0)))
            font_hl = load_font(font_path, 96)
            hl_text = str(hl_num)
            hl_bbox = font_hl.getbbox(hl_text)
            hl_w = hl_bbox[2] - hl_bbox[0]
            hl_x = (frame.size[0] - hl_w) // 2
            hl_y = card_y + 550

            # Scale effect
            scale_progress = ease_out_cubic(min(hl_t / 0.3, 1.0))
            hl_font_size = int(96 * (1.3 - 0.3 * scale_progress))
            font_hl_scaled = load_font(font_path, hl_font_size)

            odraw.text((hl_x, hl_y), hl_text, fill=(*color, hl_alpha), font=font_hl_scaled)

    frame = frame.convert("RGBA")
    frame = Image.alpha_composite(frame, overlay)
    return frame.convert("RGB")


def render_cta_frame(bg_img, slide_meta, font_path, t, duration):
    """Render CTA frame with pulse animation."""
    frame = bg_img.copy()

    texts = slide_meta.get("texts", ["保存してね"])
    base_size = slide_meta.get("font_size", 56)

    # Fade in over 0.4s
    fade_dur = 0.4
    alpha = min(255, int(255 * min(t / fade_dur, 1.0)))

    # Pulse after fade: ±3px at 1.5Hz
    if t > fade_dur:
        pulse = 3 * math.sin(2 * math.pi * 1.5 * (t - fade_dur))
    else:
        pulse = 0

    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    w, h = frame.size

    max_text_w = w - 160  # 80px margin each side
    line_idx = 0
    for text in texts:
        font_size = max(20, int(base_size + pulse))
        font = load_font(font_path, font_size)
        wrapped = wrap_text(text, font, max_text_w)
        for wl in wrapped:
            bbox = font.getbbox(wl)
            tw = bbox[2] - bbox[0]
            x = (w - tw) // 2
            y = 700 + line_idx * int(font_size * 1.6)
            odraw.text((x + 2, y + 2), wl, fill=(0, 0, 0, alpha // 3), font=font)
            odraw.text((x, y), wl, fill=(255, 255, 255, alpha), font=font)
            line_idx += 1

    # Brand watermark
    font_brand = load_font(font_path, 36)
    brand = "ナースロビー"
    brand_bbox = font_brand.getbbox(brand)
    brand_w = brand_bbox[2] - brand_bbox[0]
    odraw.text(((w - brand_w) // 2, 1400), brand, fill=(255, 255, 255, int(alpha * 0.5)), font=font_brand)

    frame = frame.convert("RGBA")
    frame = Image.alpha_composite(frame, overlay)
    return frame.convert("RGB")


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

        # Transition: cross-fade between slides (0.3s overlap)
        xfade_dur = 0.3

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
                # Crossfade: blend current and next slide
                next_idx = slide_idx + 1
                blend_factor = 1.0 - (time_to_end / xfade_dur)

                # Render current frame
                frame1 = _render_slide_frame(bg, sm, font_path, local_t, dur)
                # Render next frame (t=0 for next)
                next_bg = backgrounds[next_idx]
                next_sm = slides_meta[next_idx]
                next_dur = next_sm.get("duration", 3.0)
                frame2 = _render_slide_frame(next_bg, next_sm, font_path, 0, next_dur)

                # Blend
                frame = Image.blend(frame1, frame2, blend_factor)
            else:
                frame = _render_slide_frame(bg, sm, font_path, local_t, dur)

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
            "-preset", "medium",
            "-crf", "18",
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


def _render_slide_frame(bg, slide_meta, font_path, t, duration):
    """Dispatch to the correct renderer based on slide type."""
    slide_type = slide_meta.get("type", "content")
    if slide_type == "hook":
        return render_hook_frame(bg, slide_meta, font_path, t, duration)
    elif slide_type == "cta":
        return render_cta_frame(bg, slide_meta, font_path, t, duration)
    else:
        return render_content_frame(bg, slide_meta, font_path, t, duration)


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
