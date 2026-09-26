
"""Sentiment composite. Williams %R is one input, not the engine."""

from __future__ import annotations

from ftn.os.contracts import Probe, Sentiment, WilliamsR
from ftn.os.wr import williams_r


def wr_state(value) -> str:
    if value is None:
        return "unavailable"
    if value <= -80:
        return "bullish"
    if value >= -20:
        return "bearish"
    return "neutral"


def build_sentiment(raw: dict, iof_state: str) -> Sentiment:
    s = raw.get("sentiment") or {}
    ind = s.get("indicator") or {}
    bars = raw.get("bars_m15") or (raw.get("evidence") or {}).get("bars_m15") or []
    computed = williams_r(bars) if bars else None
    value = computed["value"] if computed and computed["value"] is not None else ind.get("value")
    state = computed["state"] if computed and computed["value"] is not None else (ind.get("state") or wr_state(value))
    wr = WilliamsR(value=value, state=state)
    asian = s.get("asian_range") or (raw.get("ranges") or {}).get("asian") or {}
    opens = raw.get("opens") or {}
    ref = s.get("reference_open", "gmt0")
    last = raw.get("last")
    open_px = opens.get(ref)
    observed = (s.get("liquidity_probe") or {}).get("observed_side", "none")

    # expected delivery follows daytrade IOF when clear
    if iof_state == "bullish":
        direction, expected, preferred = "bullish", "higher", "sell_side"
    elif iof_state == "bearish":
        direction, expected, preferred = "bearish", "lower", "buy_side"
    else:
        direction = wr.state if wr.state in {"bullish", "bearish"} else "unclear"
        expected = "higher" if direction == "bullish" else "lower" if direction == "bearish" else "unclear"
        preferred = "either"

    return Sentiment(
        direction=direction,
        expected_delivery=expected,
        indicator=wr,
        reference_open=ref,
        asian_range=asian,
        liquidity_probe=Probe(preferred_side=preferred, observed_side=observed),
        judas_side=s.get("judas_side") or observed or "none",
        reaction=s.get("reaction") or {"pd_array_reaction": "none"},
        basis=("williams_r", "pair_iof", "asian_range", "opening_price"),
    )
