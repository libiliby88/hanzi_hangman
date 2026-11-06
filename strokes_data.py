import json as _json
from pathlib import Path as _Path


with _Path(__file__).with_name("hanzi_data.json").open(
    "r", encoding="utf-8"
) as data_file:
    _data = _json.load(data_file)

STROKE_PALETTE = _data["stroke_palette"]
CHARACTERS = _data["characters"]

__all__ = ["STROKE_PALETTE", "CHARACTERS"]
