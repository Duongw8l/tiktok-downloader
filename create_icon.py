"""Tạo icon TikSnap (.ico + .png) cho Windows."""
from PIL import Image, ImageDraw
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
SIZES = [16, 32, 48, 64, 128, 256]


def make_icon(size: int) -> Image.Image:
    base = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(base)
    margin = max(1, size // 16)
    radius = max(2, size // 4)

    # Gradient pink → cyan
    gradient = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(gradient)
    for y in range(size):
        t = y / max(size - 1, 1)
        r = int(255 * (1 - t) + 0 * t)
        g = int(20 * (1 - t) + 242 * t)
        b = int(80 * (1 - t) + 234 * t)
        gdraw.line([(0, y), (size - 1, y)], fill=(r, g, b, 255))

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [margin, margin, size - margin - 1, size - margin - 1],
        radius=radius,
        fill=255,
    )
    rounded = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    rounded.paste(gradient, mask=mask)
    draw = ImageDraw.Draw(rounded)

    cx, cy = size // 2, size // 2
    stroke = max(2, size // 12)
    shaft_w = max(2, size // 8)
    head_w = max(6, size // 3)
    head_h = max(4, size // 5)
    top = cy - size // 5
    bottom = cy + size // 10

    draw.rounded_rectangle(
        [cx - shaft_w // 2, top, cx + shaft_w // 2, bottom],
        radius=max(1, shaft_w // 2),
        fill=(255, 255, 255, 255),
    )
    draw.polygon(
        [
            (cx, bottom + head_h),
            (cx - head_w // 2, bottom),
            (cx + head_w // 2, bottom),
        ],
        fill=(255, 255, 255, 255),
    )
    tray_y = min(size - margin - stroke - 1, bottom + head_h + max(2, size // 18))
    tray_half = size // 4
    draw.rounded_rectangle(
        [cx - tray_half, tray_y, cx + tray_half, tray_y + stroke],
        radius=max(1, stroke // 2),
        fill=(255, 255, 255, 255),
    )
    return rounded


def main():
    images = [make_icon(s) for s in SIZES]
    ico_path = os.path.join(OUT_DIR, "tiksnap.ico")
    png_path = os.path.join(OUT_DIR, "tiksnap.png")

    images[-1].save(png_path, format="PNG")
    # Windows ICO multi-size
    images[-1].save(
        ico_path,
        format="ICO",
        sizes=[(s, s) for s in SIZES],
    )
    print(f"Created: {ico_path}")
    print(f"Created: {png_path}")


if __name__ == "__main__":
    main()
