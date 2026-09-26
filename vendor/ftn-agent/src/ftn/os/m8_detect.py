"""Month-8 Slice 2: derive CBDR class + London gate from measurements.

Does not name ict_london_profile. That needs price-behavior evidence (Slice 3+).
"""

from __future__ import annotations

from ftn.os.m8_contracts import (
    CbdrState,
    LondonGate,
    Month8State,
    classify_cbdr,
    parse_month8,
)


def measure_cbdr(block: dict | None) -> CbdrState:
    block = block or {}
    height = block.get("height_pips")
    if height is None and block.get("body_high") is not None and block.get("body_low") is not None:
        height = round((float(block["body_high"]) - float(block["body_low"])) * 10000, 1)
    cls = classify_cbdr(height)
    return CbdrState(
        height_pips=height,
        body_height_pips=block.get("body_height_pips"),
        wick_high=block.get("wick_high"),
        wick_low=block.get("wick_low"),
        body_high=block.get("body_high"),
        body_low=block.get("body_low"),
        classification=cls,
        daytrade_classic=cls == "ideal",
    )


def london_gate_from_measures(cbdr: CbdrState, asian_pips: float | None, adr_remaining=None, news: bool = False) -> LondonGate:
    """Wide (>=50) is ICT-source avoidance. Expanded (40-<50) refuse-classic is Hermes interpretation."""
    if news:
        return LondonGate(allowed=False, reason="news", origin="ict_source")
    if cbdr.classification == "wide":
        return LondonGate(allowed=False, reason="wide_cbdr", origin="ict_source")
    if asian_pips is not None and asian_pips > 40:
        return LondonGate(allowed=False, reason="poor_consolidation", origin="ict_source")
    if adr_remaining is not None and adr_remaining <= 0:
        return LondonGate(allowed=False, reason="adr_spent", origin="ict_source")
    if cbdr.classification == "expanded":
        return LondonGate(allowed=False, reason="expanded_cbdr", origin="hermes_interpretation")
    if cbdr.classification == "ideal":
        return LondonGate(allowed=True, reason=None, origin="ict_source")
    return LondonGate(allowed=False, reason="unknown_cbdr", origin="hermes_interpretation")


def derive_month8_measures(raw: dict) -> Month8State:
    """Fill classification + gate. Leave profile/opportunity/projection as provided or none."""
    base = parse_month8(raw) or Month8State()
    m8 = raw.get("month8") or raw.get("ict_day") or {}
    ranges = raw.get("ranges") or {}
    cb_src = m8.get("cbdr") or ranges.get("cbdr") or {}
    if "height_pips" not in cb_src and cb_src.get("high") is not None:
        cb_src = dict(cb_src)
        cb_src["height_pips"] = round((float(cb_src["high"]) - float(cb_src["low"])) * 10000, 1)
    cbdr = measure_cbdr(cb_src)
    asian = m8.get("asian_height_pips")
    if asian is None:
        ar = ranges.get("asian") or {}
        if ar.get("high") is not None:
            asian = round((float(ar["high"]) - float(ar["low"])) * 10000, 1)
    news = any(str(e.get("impact", "")).lower() == "high" for e in (raw.get("calendar") or []))
    rem = (raw.get("adr5") or {}).get("remaining")
    gate = london_gate_from_measures(cbdr, asian, rem, news)
    # profile / opportunity / projection stay as labeled on known-state fixtures
    # evidence fixtures omit them → none / False / none
    return Month8State(
        ict_true_day=base.ict_true_day,
        cbdr=cbdr,
        asian_height_pips=asian,
        london_session_gate=gate,
        ict_london_profile=base.ict_london_profile,
        daily_extreme_projection=base.daily_extreme_projection,
        daytrade_opportunity=base.daytrade_opportunity,
        htf_entry_overlap=base.htf_entry_overlap,
        ict_guidance=base.ict_guidance,
    )
