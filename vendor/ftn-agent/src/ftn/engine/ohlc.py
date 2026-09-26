from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_bars(fixture: Path | None, symbol: str) -> dict[str, Any]:
    if fixture is None:
        fixture = Path(__file__).resolve().parents[3] / "fixtures" / "sample_eurusd.json"
    data = json.loads(Path(fixture).read_text(encoding="utf-8"))
    data.setdefault("symbol", symbol)
    return data
