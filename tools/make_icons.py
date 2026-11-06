"""Generate the web app's Home Screen icons."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


BACKGROUND = "#2c3e50"
TEXT = "#ecf0f1"
ROOT = Path(__file__).resolve().parents[1]
ICON_DIR = ROOT / "web" / "icons"
FONT_CANDIDATES = (
    Path("C:/Windows/Fonts/msyh.ttc"),
    Path("C:/Windows/Fonts/simhei.ttf"),
)


def make_icon(size, font_path):
    image = Image.new("RGB", (size, size), BACKGROUND)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(font_path), int(size * 0.63))
    draw.text((size / 2, size / 2), "笔", fill=TEXT, font=font, anchor="mm")
    image.save(ICON_DIR / f"icon-{size}.png", format="PNG")


def main():
    font_path = next((path for path in FONT_CANDIDATES if path.exists()), None)
    if font_path is None:
        raise SystemExit("No Windows CJK font found (tried msyh.ttc and simhei.ttf)")
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    for size in (180, 512):
        make_icon(size, font_path)


if __name__ == "__main__":
    main()
