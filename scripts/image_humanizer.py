#!/usr/bin/env python3
"""
image_humanizer.py — AI生成画像のヒューマナイズ処理 v1.0

AI生成画像を「スマホ撮影風」に変換し、Instagram/TikTokの
AI検出アルゴリズムを回避する。

処理内容:
  1. センサーノイズ（Gaussian）
  2. 微小回転（0.1-0.5度）
  3. ビネット（角暗落ち）
  4. 色温度シフト
  5. JPEG品質ランダム化
  6. 寸法微調整
  7. EXIF偽装（カメラメタデータ注入）

使い方:
  from image_humanizer import humanize_image
  humanize_image("input.png", "output.jpg")

  # CLI
  python3 scripts/image_humanizer.py input.png output.jpg
"""

import argparse
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image, ImageFilter, ImageDraw

try:
    import piexif
    HAS_PIEXIF = True
except ImportError:
    HAS_PIEXIF = False
    print("[WARN] piexif not installed. EXIF injection disabled.")

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


# ============================================================
# Device profiles for EXIF injection
# ============================================================

DEVICE_PROFILES = [
    {
        "make": "Samsung",
        "model": "SM-S921B",  # Galaxy S24
        "software": "S921BXXU3AXAA",
        "focal_length": (660, 100),  # 6.6mm
        "focal_35mm": 26,
        "f_number": (18, 10),  # f/1.8
        "iso_range": (50, 800),
    },
    {
        "make": "Apple",
        "model": "iPhone 15 Pro",
        "software": "17.4.1",
        "focal_length": (690, 100),  # 6.9mm
        "focal_35mm": 24,
        "f_number": (17, 10),  # f/1.7 (adjusted for Tuple format)
        "iso_range": (32, 1600),
    },
    {
        "make": "Google",
        "model": "Pixel 8",
        "software": "AP2A.240305.019.A1",
        "focal_length": (670, 100),  # 6.7mm
        "focal_35mm": 25,
        "f_number": (17, 10),  # f/1.7
        "iso_range": (50, 800),
    },
    {
        "make": "Sony",
        "model": "XQ-DQ72",  # Xperia 1 VI
        "software": "68.1.A.2.83",
        "focal_length": (650, 100),  # 6.5mm
        "focal_35mm": 24,
        "f_number": (19, 10),  # f/1.9
        "iso_range": (64, 3200),
    },
]


# ============================================================
# Noise generation
# ============================================================

def add_sensor_noise(img, sigma=3.0):
    """Gaussian sensor noise (subtle, like real camera sensor)."""
    if HAS_NUMPY:
        arr = np.array(img, dtype=np.float32)
        noise = np.random.normal(0, sigma, arr.shape).astype(np.float32)
        arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(arr)
    else:
        # Pillow fallback: slight Gaussian blur + unsharp to simulate noise
        blurred = img.filter(ImageFilter.GaussianBlur(radius=0.5))
        return Image.blend(img, blurred, alpha=0.1)


# ============================================================
# Color temperature shift
# ============================================================

def shift_color_temperature(img, shift=0):
    """Shift color temperature (positive=warm, negative=cool)."""
    if shift == 0:
        return img

    r, g, b = img.split()[:3]

    if shift > 0:
        # Warm: boost red, reduce blue
        r = r.point(lambda x: min(255, x + shift))
        b = b.point(lambda x: max(0, x - shift))
    else:
        # Cool: boost blue, reduce red
        r = r.point(lambda x: max(0, x + shift))
        b = b.point(lambda x: min(255, x - shift))

    if img.mode == "RGBA":
        a = img.split()[3]
        return Image.merge("RGBA", (r, g, b, a))
    return Image.merge("RGB", (r, g, b))


# ============================================================
# Vignette effect
# ============================================================

def apply_vignette(img, strength=0.1):
    """Apply subtle corner darkening (vignette)."""
    w, h = img.size
    vignette = Image.new("L", (w, h), 255)
    draw = ImageDraw.Draw(vignette)

    # Draw radial gradient from center (white) to edges (dark)
    cx, cy = w // 2, h // 2
    max_dist = (cx ** 2 + cy ** 2) ** 0.5

    for step in range(0, int(max_dist), 3):
        ratio = step / max_dist
        # Only darken the outer portion
        if ratio > 0.6:
            darkness = int(255 * (1.0 - strength * ((ratio - 0.6) / 0.4) ** 2))
            darkness = max(0, min(255, darkness))
            bbox = (cx - step, cy - step, cx + step, cy + step)
            draw.ellipse(bbox, outline=darkness)

    if img.mode == "RGBA":
        rgb = img.convert("RGB")
        result = Image.composite(rgb, Image.new("RGB", img.size, (0, 0, 0)), vignette)
        result.putalpha(img.split()[3])
        return result
    return Image.composite(img, Image.new("RGB", img.size, (0, 0, 0)), vignette)


# ============================================================
# EXIF injection
# ============================================================

def create_exif_bytes(device=None):
    """Generate realistic EXIF metadata for a smartphone camera."""
    if not HAS_PIEXIF:
        return None

    if device is None:
        device = random.choice(DEVICE_PROFILES)

    # Random timestamp within last 2 hours
    now = datetime.now() - timedelta(minutes=random.randint(0, 120))
    dt_str = now.strftime("%Y:%m:%d %H:%M:%S")

    iso_min, iso_max = device["iso_range"]
    iso = random.choice([iso_min, 100, 200, 400, min(800, iso_max)])

    # Exposure time varies with ISO
    if iso <= 100:
        exposure = (1, random.choice([60, 80, 100]))
    elif iso <= 400:
        exposure = (1, random.choice([100, 125, 160, 200]))
    else:
        exposure = (1, random.choice([200, 250, 320]))

    exif_dict = {
        "0th": {
            piexif.ImageIFD.Make: device["make"].encode(),
            piexif.ImageIFD.Model: device["model"].encode(),
            piexif.ImageIFD.Software: device["software"].encode(),
            piexif.ImageIFD.DateTime: dt_str.encode(),
            piexif.ImageIFD.Orientation: 1,
            piexif.ImageIFD.XResolution: (72, 1),
            piexif.ImageIFD.YResolution: (72, 1),
        },
        "Exif": {
            piexif.ExifIFD.DateTimeOriginal: dt_str.encode(),
            piexif.ExifIFD.DateTimeDigitized: dt_str.encode(),
            piexif.ExifIFD.ExposureTime: exposure,
            piexif.ExifIFD.FNumber: device["f_number"],
            piexif.ExifIFD.ISOSpeedRatings: iso,
            piexif.ExifIFD.FocalLength: device["focal_length"],
            piexif.ExifIFD.FocalLengthIn35mmFilm: device["focal_35mm"],
            piexif.ExifIFD.ExposureProgram: 2,  # Normal program
            piexif.ExifIFD.MeteringMode: 2,  # Center-weighted average
            piexif.ExifIFD.Flash: 0,  # No flash
            piexif.ExifIFD.WhiteBalance: 0,  # Auto
            piexif.ExifIFD.SceneCaptureType: 0,  # Standard
            piexif.ExifIFD.ColorSpace: 1,  # sRGB
        },
        "1st": {},
        "GPS": {},
    }

    return piexif.dump(exif_dict)


# ============================================================
# Main humanization pipeline
# ============================================================

def humanize_image(input_path, output_path, intensity="medium"):
    """
    Apply subtle imperfections to make AI-generated images look human-captured.

    Args:
        input_path: Source image path (PNG or JPEG)
        output_path: Output path (will be saved as JPEG)
        intensity: "light", "medium", or "heavy"
    """
    img = Image.open(input_path)

    # Ensure RGB mode
    if img.mode == "RGBA":
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # Intensity presets
    presets = {
        "light": {"noise_sigma": (1.5, 2.5), "rotation": (0.05, 0.2), "vignette": (0.03, 0.08), "temp_shift": (-3, 3)},
        "medium": {"noise_sigma": (2.0, 4.0), "rotation": (0.1, 0.5), "vignette": (0.05, 0.15), "temp_shift": (-5, 5)},
        "heavy": {"noise_sigma": (3.0, 6.0), "rotation": (0.2, 0.8), "vignette": (0.08, 0.20), "temp_shift": (-8, 8)},
    }
    preset = presets.get(intensity, presets["medium"])

    # 1. Sensor noise
    sigma = random.uniform(*preset["noise_sigma"])
    img = add_sensor_noise(img, sigma=sigma)

    # 2. Color temperature shift
    temp_shift = random.randint(*preset["temp_shift"])
    img = shift_color_temperature(img, shift=temp_shift)

    # 3. Micro rotation
    angle = random.uniform(*preset["rotation"]) * random.choice([-1, 1])
    img = img.rotate(angle, resample=Image.BICUBIC, expand=False, fillcolor=(0, 0, 0))

    # 4. Vignette
    vig_strength = random.uniform(*preset["vignette"])
    img = apply_vignette(img, strength=vig_strength)

    # 5. Slight dimension variance (±2px)
    w, h = img.size
    new_w = w + random.randint(-2, 2)
    new_h = h + random.randint(-2, 2)
    if new_w > 0 and new_h > 0:
        img = img.resize((new_w, new_h), Image.LANCZOS)

    # 6. JPEG quality randomization
    quality = random.randint(88, 93)

    # 7. Save with EXIF
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    exif_bytes = create_exif_bytes()
    if exif_bytes:
        img.save(str(output_path), "JPEG", quality=quality, exif=exif_bytes)
    else:
        img.save(str(output_path), "JPEG", quality=quality)

    return {
        "noise_sigma": round(sigma, 2),
        "temp_shift": temp_shift,
        "rotation": round(angle, 3),
        "vignette": round(vig_strength, 3),
        "quality": quality,
        "dimensions": f"{new_w}x{new_h}",
        "exif_injected": exif_bytes is not None,
    }


def humanize_batch(input_dir, output_dir, intensity="medium"):
    """Humanize all PNG/JPEG images in a directory."""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for img_path in sorted(input_dir.glob("*.png")) + sorted(input_dir.glob("*.jpg")):
        out_path = output_dir / f"{img_path.stem}_humanized.jpg"
        info = humanize_image(str(img_path), str(out_path), intensity)
        info["source"] = str(img_path)
        info["output"] = str(out_path)
        results.append(info)
        print(f"  [OK] {img_path.name} → {out_path.name} (noise={info['noise_sigma']}, temp={info['temp_shift']})")

    return results


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI画像ヒューマナイザー")
    parser.add_argument("input", nargs="?", help="入力画像パス or ディレクトリ")
    parser.add_argument("output", nargs="?", help="出力画像パス or ディレクトリ")
    parser.add_argument("--intensity", choices=["light", "medium", "heavy"], default="medium",
                        help="処理強度 (default: medium)")
    parser.add_argument("--batch", action="store_true", help="ディレクトリ一括処理")
    parser.add_argument("--test", action="store_true", help="テスト画像で動作確認")
    args = parser.parse_args()

    if args.test:
        # Create a test gradient image
        test_img = Image.new("RGB", (1080, 1920))
        if HAS_NUMPY:
            arr = np.zeros((1920, 1080, 3), dtype=np.uint8)
            for y in range(1920):
                arr[y, :, 0] = int(255 * y / 1920)  # Red gradient
                arr[y, :, 2] = int(255 * (1920 - y) / 1920)  # Blue gradient
            arr[:, :, 1] = 128  # Fixed green
            test_img = Image.fromarray(arr)

        test_in = "/tmp/humanizer_test_input.png"
        test_out = "/tmp/humanizer_test_output.jpg"
        test_img.save(test_in)
        info = humanize_image(test_in, test_out)
        print(f"[TEST] Input:  {test_in}")
        print(f"[TEST] Output: {test_out}")
        print(f"[TEST] Parameters: {info}")
        if HAS_PIEXIF:
            # Verify EXIF
            exif_data = piexif.load(test_out)
            make = exif_data["0th"].get(piexif.ImageIFD.Make, b"").decode()
            model = exif_data["0th"].get(piexif.ImageIFD.Model, b"").decode()
            print(f"[TEST] EXIF: {make} {model}")
        print("[TEST] Done!")
        sys.exit(0)

    if not args.input or not args.output:
        parser.print_help()
        sys.exit(1)

    if args.batch:
        results = humanize_batch(args.input, args.output, args.intensity)
        print(f"\n[DONE] {len(results)} images humanized.")
    else:
        info = humanize_image(args.input, args.output, args.intensity)
        print(f"[DONE] {args.input} → {args.output}")
        print(f"  Parameters: {info}")
