"""Build the small webfont used for Chinese stroke figures.

Source: Noto Sans CJK SC 2.004, OFL, from
https://github.com/notofonts/noto-cjk/releases/tag/Sans2.004
Release asset:
https://github.com/notofonts/noto-cjk/releases/download/Sans2.004/18_NotoSansSC.zip
"""

import argparse
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont


SOURCE_URL = (
    "https://github.com/notofonts/noto-cjk/releases/download/"
    "Sans2.004/18_NotoSansSC.zip"
)
CODEPOINTS = tuple(
    int(value, 16)
    for value in (
        "31C0 31C1 31C2 31C3 31C4 31C5 31C6 31C7 31C9 31CA "
        "31CB 31CC 31CD 31CF 31D0 31D1 31D2 31D4 31D5 31D6 "
        "31D7 31D9 31DA 31DB 31DC 31DE 31DF 31E0 31E1"
    ).split()
)
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "web" / "fonts" / "hanzi-strokes.woff2"


def find_font(source):
    source = Path(source)
    if source.suffix.lower() != ".zip":
        return source

    extraction_dir = Path(tempfile.mkdtemp(prefix="hanzi-strokes-"))
    with zipfile.ZipFile(source) as archive:
        candidates = [
            name for name in archive.namelist()
            if name.lower().endswith((".otf", ".ttf"))
            and "regular" in Path(name).name.lower()
        ]
        if not candidates:
            raise SystemExit(f"No regular OTF or TTF found in {source}")
        archive.extract(candidates[0], extraction_dir)
    return extraction_dir / candidates[0]


def download_source(directory):
    archive = directory / "NotoSansSC.zip"
    print(f"Downloading {SOURCE_URL}")
    urllib.request.urlretrieve(SOURCE_URL, archive)
    return find_font(archive)


def cmap_codepoints(font):
    return {
        codepoint
        for table in font["cmap"].tables
        for codepoint in table.cmap
    }


def subset_font(source, output):
    options = subset.Options()
    options.flavor = "woff2"
    options.hinting = False
    options.drop_tables += ["DSIG"]
    options.layout_features = []

    font = subset.load_font(str(source), options)
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(unicodes=CODEPOINTS)
    subsetter.subset(font)
    output.parent.mkdir(parents=True, exist_ok=True)
    subset.save_font(font, str(output), options)

    generated = TTFont(str(output))
    mapped = cmap_codepoints(generated)
    missing = set(CODEPOINTS) - mapped
    if missing:
        missing_text = ", ".join(f"U+{value:04X}" for value in sorted(missing))
        raise SystemExit(f"Subset is missing required codepoints: {missing_text}")
    if mapped != set(CODEPOINTS):
        extras = mapped - set(CODEPOINTS)
        extra_text = ", ".join(f"U+{value:04X}" for value in sorted(extras))
        raise SystemExit(f"Subset contains unexpected codepoints: {extra_text}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--src",
        type=Path,
        help="Path to a Noto Sans SC OTF/TTF or its release ZIP",
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if args.src:
        source = find_font(args.src)
        subset_font(source, args.out)
    else:
        with tempfile.TemporaryDirectory(prefix="hanzi-strokes-source-") as directory:
            subset_font(download_source(Path(directory)), args.out)
    print(f"Wrote {args.out} ({args.out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
