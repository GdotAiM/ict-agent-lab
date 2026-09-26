
"""FTN as objectives only. Never an entry producer."""

from __future__ import annotations

from ftn.engine.levels import build_families, count_four
from ftn.os.contracts import Candidate, MarketState


def _pack(ctx) -> dict | None:
    r = ctx.ranges or {}
    prev = r.get("previous_day")
    if not prev:
        return None
    return {
        "previous_day": prev,
        "cbdr": r.get("cbdr") or {"high": prev["high"], "low": prev["low"]},
        "asian": r.get("asian") or ctx.sentiment.asian_range or prev,
        "flout": r.get("flout") or prev,
        "swings": r.get("swings_3d") or {},
        "pd_arrays": [],
        "htf_bias": ctx.pair_institutional.state
        if ctx.pair_institutional.state in {"bullish", "bearish"}
        else "bullish",
    }


def annotate_ftn(state: MarketState) -> dict:
    ctx = state.context
    pack = _pack(ctx)
    cand = Candidate("FTN", "annotate", False, "objectives_only", "hermes_governance")
    if not pack or ctx.last is None:
        return {"candidate": cand, "families": None, "four": [], "family": None}
    families = build_families(pack)
    bias = pack["htf_bias"]
    four = count_four(families, bias=bias, price=float(ctx.last), family="cbdr")
    if len(four) < 4:
        four = count_four(families, bias=bias, price=float(ctx.last), family="pivots")
        family = "pivots"
    else:
        family = "cbdr"
    return {
        "candidate": cand,
        "families": {
            "pivots": families["pivots"],
            "cbdr": {"eq": families["cbdr"]["eq"], "sd_up": families["cbdr"]["sd_up"], "sd_down": families["cbdr"]["sd_down"]},
            "asian": {"eq": families["asian"]["eq"], "sd_up": families["asian"]["sd_up"], "sd_down": families["asian"]["sd_down"]},
            "flout": {"eq": families["flout"]["eq"], "sd_up": families["flout"]["sd_up"], "sd_down": families["flout"]["sd_down"]},
        },
        "four": four,
        "family": family,
        "bias": bias,
        "fingerprint": state.fingerprint,
    }
