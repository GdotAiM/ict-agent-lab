"""Month-10 Slice 2: labeled multi-asset context.

Does not derive multi_asset_context.
Does not write M5 confirming or M6 gates.
Does not inspect raw month1–9.
"""

from __future__ import annotations

from ftn.os.m10_contracts import (
    ASSETS,
    CARRIES,
    DIRS,
    Month10State,
    MultiAssetContext,
    OIS,
    PRES,
    RSS,
    WATCHES,
    _one,
)


def _block(raw: dict):
    ev = raw.get("evidence") or {}
    m10 = raw.get("month10") or raw.get("ict_multi_asset") or {}
    return ev, m10


def derive_month10_context(raw: dict) -> Month10State:
    ev, m10 = _block(raw)
    src = ev.get("month10") or ev or m10
    return Month10State(
        identified_multi_asset=_one(
            src.get("identified_multi_asset") or m10.get("identified_multi_asset"), PRES
        ),
        cot_reading=_one(src.get("cot_reading") or m10.get("cot_reading"), DIRS),
        relative_strength=_one(src.get("relative_strength") or m10.get("relative_strength"), RSS),
        open_interest=_one(src.get("open_interest") or m10.get("open_interest"), OIS),
        commodity_seasonal_note=_one(
            src.get("commodity_seasonal_note") or m10.get("commodity_seasonal_note"), PRES
        ),
        carrying_charge_note=_one(
            src.get("carrying_charge_note") or m10.get("carrying_charge_note"), CARRIES
        ),
        asset_class=_one(src.get("asset_class") or m10.get("asset_class"), ASSETS),
        asset_session_note=_one(
            src.get("asset_session_note") or m10.get("asset_session_note"), PRES
        ),
        multi_asset_confluence_note=_one(
            src.get("multi_asset_confluence_note") or m10.get("multi_asset_confluence_note"), PRES
        ),
        options_note=_one(src.get("options_note") or m10.get("options_note"), PRES),
        watchlist_note=_one(src.get("watchlist_note") or m10.get("watchlist_note"), WATCHES),
        multi_asset_context=MultiAssetContext(flag=False, reason="slice2_context_only"),
    )
