"""Generate v1 placeholder icons for LexiFlow packaging."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _repo_assets() -> Path:
    return Path(__file__).resolve().parents[1] / "assets"


def generate_icons() -> None:
    assets = _repo_assets()
    assets.mkdir(parents=True, exist_ok=True)
    size = 256
    image = Image.new("RGBA", (size, size), (45, 106, 178, 255))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((24, 24, 232, 232), radius=32, fill=(255, 255, 255, 255))
    font = None
    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    ]
    for path in font_paths:
        try:
            font = ImageFont.truetype(path, 96)
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default(size=96)
    draw.text((78, 88), "LF", fill=(45, 106, 178, 255), font=font)

    png_path = assets / "icon.png"
    image.save(png_path)

    ico_path = assets / "icon.ico"
    image.save(ico_path, sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])

    icns_path = assets / "icon.icns"
    image.save(icns_path, format="ICNS")

    print(f"Wrote {png_path}, {ico_path}, {icns_path}")


if __name__ == "__main__":
    generate_icons()
