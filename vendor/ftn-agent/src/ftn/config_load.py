from __future__ import annotations

from pathlib import Path
from typing import Any


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_config() -> dict[str, Any]:
    path = repo_root() / "config.yaml"
    cfg: dict[str, Any] = {"mode": "paper", "live_enabled": False, "path": str(path)}
    if not path.is_file():
        return cfg
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.split("#", 1)[0].strip()
        if not stripped or ":" not in stripped or stripped.startswith("-"):
            continue
        k, v = stripped.split(":", 1)
        key = k.strip()
        val = v.strip().strip("\"'")
        if key in ("mode", "symbol_default", "timezone"):
            cfg[key] = val
        elif key in ("live_enabled", "live_data_enabled"):
            cfg[key] = val.lower() in ("true", "yes", "1")
        elif key == "scale_out_after_levels":
            cfg[key] = int(val) if val else 4
        elif key == "runner_pct":
            cfg[key] = float(val) if val else 0.25
        elif key == "min_atr_pips":
            cfg["min_atr_pips"] = float(val)
        elif key == "overlap_tolerance_pips":
            cfg["overlap_tolerance_pips"] = float(val)
        elif key == "compress_blocks_trade":
            cfg[key] = val.lower() in ("true", "yes", "1")
        elif key == "require_pd_overlap":
            cfg[key] = val.lower() in ("true", "yes", "1")
    cfg.setdefault("min_atr_pips", 20)
    cfg.setdefault("overlap_tolerance_pips", 8)
    cfg.setdefault("scale_out_after_levels", 4)
    cfg.setdefault("runner_pct", 0.25)
    cfg.setdefault("require_pd_overlap", True)
    cfg.setdefault("compress_blocks_trade", True)
    return cfg
