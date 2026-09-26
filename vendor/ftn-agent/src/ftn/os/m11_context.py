"""Month-11 Slice 2: labeled mega-trade context.

Does not derive mega_trade.
Does not write M5 quarterly_shift or M6 swing_opportunity.
Does not inspect raw month1–10.
"""

from __future__ import annotations

from ftn.os.m11_contracts import FAMILIES, MegaTrade, Month11State, PRES, _one


def _block(raw: dict):
    ev = raw.get("evidence") or {}
    m11 = raw.get("month11") or raw.get("ict_mega") or {}
    return ev, m11


def derive_month11_context(raw: dict) -> Month11State:
    ev, m11 = _block(raw)
    src = ev.get("month11") or ev or m11
    return Month11State(
        mega_trade_family=_one(src.get("mega_trade_family") or m11.get("mega_trade_family"), FAMILIES),
        identified_mega_trade=_one(
            src.get("identified_mega_trade") or m11.get("identified_mega_trade"), PRES
        ),
        quarterly_shift_overlap=_one(
            src.get("quarterly_shift_overlap") or m11.get("quarterly_shift_overlap"), PRES
        ),
        seasonal_overlap=_one(src.get("seasonal_overlap") or m11.get("seasonal_overlap"), PRES),
        relative_strength_note=_one(
            src.get("relative_strength_note") or m11.get("relative_strength_note"), PRES
        ),
        mega_trade=MegaTrade(flag=False, reason="slice2_context_only"),
    )
