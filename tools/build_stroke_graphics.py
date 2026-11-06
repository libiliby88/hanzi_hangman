"""Build the committed stroke-outline data used by the web game.

Source: hanzi-writer-data 2.0.1, derived from Make Me a Hanzi / Arphic fonts.
https://registry.npmjs.org/hanzi-writer-data/-/hanzi-writer-data-2.0.1.tgz
"""

import argparse
import json
import tarfile
import tempfile
import urllib.request
from pathlib import Path


SOURCE_URL = "https://registry.npmjs.org/hanzi-writer-data/-/hanzi-writer-data-2.0.1.tgz"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "hanzi_graphics.json"
DEFAULT_LICENSE = ROOT / "ARPHICPL.txt"


def load_data():
    with open(ROOT / "hanzi_data.json", encoding="utf-8") as fh:
        data = json.load(fh)
    characters = [entry["character"] for entry in data["characters"]]
    strokes = {
        entry["character"]: entry.get("strokes", [])
        for entry in data["characters"]
    }
    return characters, strokes


def read_from_tarball(source, characters):
    with tarfile.open(source, "r:gz") as archive:
        graphics = {}
        for character in characters:
            member_name = f"package/{character}.json"
            try:
                member = archive.extractfile(member_name)
            except KeyError:
                continue
            if member is not None:
                graphics[character] = json.load(member)["strokes"]
        license_text = archive.extractfile("package/ARPHICPL.TXT").read()
    return graphics, license_text


def read_from_directory(source, characters):
    graphics = {}
    for character in characters:
        path = source / f"{character}.json"
        if path.is_file():
            with open(path, encoding="utf-8") as fh:
                graphics[character] = json.load(fh)["strokes"]
    license_path = source / "ARPHICPL.TXT"
    if not license_path.is_file():
        raise SystemExit(f"Missing ARPHICPL.TXT in {source}")
    license_text = license_path.read_bytes()
    return graphics, license_text


def read_source(source, characters):
    if source.is_dir():
        return read_from_directory(source, characters)
    return read_from_tarball(source, characters)


def download_source(directory):
    archive_path = directory / "hanzi-writer-data-2.0.1.tgz"
    print(f"Downloading {SOURCE_URL}")
    urllib.request.urlretrieve(SOURCE_URL, archive_path)
    return archive_path


def build(source, output, license_output):
    characters, data_strokes = load_data()
    graphics, license_text = read_source(source, characters)

    missing = [character for character in characters if character not in graphics]
    if missing:
        raise SystemExit(f"Graphics missing for {len(missing)} characters: {''.join(missing)}")

    for character in characters:
        outline_count = len(graphics[character])
        stroke_count = len(data_strokes[character])
        if outline_count != stroke_count:
            raise SystemExit(
                f"Stroke count mismatch for {character}: "
                f"graphics={outline_count}, data={stroke_count}"
            )

    output.write_text(
        json.dumps(
            {character: graphics[character] for character in characters},
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    license_output.write_bytes(license_text)
    print(f"Wrote {output} ({output.stat().st_size} bytes)")
    print(f"Wrote {license_output} ({license_output.stat().st_size} bytes)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--src",
        type=Path,
        help="Path to hanzi-writer-data-2.0.1.tgz or its extracted package directory",
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--license-out", type=Path, default=DEFAULT_LICENSE)
    args = parser.parse_args()

    if args.src:
        build(args.src, args.out, args.license_out)
    else:
        with tempfile.TemporaryDirectory(prefix="hanzi-writer-data-") as directory:
            build(download_source(Path(directory)), args.out, args.license_out)


if __name__ == "__main__":
    main()
