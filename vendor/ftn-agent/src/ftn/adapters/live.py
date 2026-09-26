
"""Live *data* adapters. Never place orders. Dual-flag gated."""

from __future__ import annotations

import os
from typing import Any


def live_data_allowed(cfg: dict | None = None) -> bool:
    cfg = cfg or {}
    env = os.environ.get("FTN_LIVE_DATA", "").strip() == "1"
    flag = bool(cfg.get("live_data_enabled", False))
    # Trading lock (config live_enabled / FTN_LIVE) is a different gate.
    # This function only checks the DATA pair: live_data_enabled + FTN_LIVE_DATA.
    return env and flag


def refuse_live_orders() -> dict:
    return {
        "ok": False,
        "reason": "live_orders_refused",
        "mode": "paper",
        "note": "J adapters may fetch evidence only. Brokers stay closed.",
    }


def fetch_quote(symbol: str, cfg: dict | None = None) -> dict[str, Any]:
    if not live_data_allowed(cfg):
        return {
            "ok": False,
            "source": "off",
            "symbol": symbol,
            "reason": "live_data_disabled",
            "hint": "Set live_data_enabled: true in config AND FTN_LIVE_DATA=1",
        }
    # Opt-in HTTP last-price probe (Yahoo chart). Fail closed.
    import json
    import urllib.request
    ysym = symbol if "=" in symbol else f"{symbol}=X"
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ysym}?interval=15m&range=1d"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ftn-agent-paper"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        result = (data.get("chart") or {}).get("result") or [None]
        meta = (result[0] or {}).get("meta") or {}
        last = meta.get("regularMarketPrice")
        return {
            "ok": last is not None,
            "source": "yahoo",
            "symbol": symbol,
            "last": last,
            "note": "evidence only — does not arm MINT",
        }
    except Exception as exc:
        return {"ok": False, "source": "yahoo", "symbol": symbol, "reason": str(exc)}


def fetch_calendar(cfg: dict | None = None) -> dict[str, Any]:
    if not live_data_allowed(cfg):
        return {"ok": False, "source": "off", "events": [], "reason": "live_data_disabled"}
    return {
        "ok": False,
        "source": "unstubbed",
        "events": [],
        "reason": "no_calendar_provider_configured",
        "note": "Wire a file or vendor later. Do not scrape blindly.",
    }
