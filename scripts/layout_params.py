"""Read the layout parameters (layout_params.json) as {"name": value}."""

import json
from pathlib import Path

_PATH = Path(__file__).resolve().parent / "layout_params.json"


def load(path=None):
    data = json.loads(Path(path or _PATH).read_text(encoding="utf-8"))
    return {k: v["value"] for k, v in data.items() if not k.startswith("_")}


P = load()
