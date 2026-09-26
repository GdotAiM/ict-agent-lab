"""Month-5 Slice 2: quarterly shift + labeled IPDA.

Does not name institutional swing.
Does not set position_opportunity.
Does not inspect raw month7.
"""

from __future__ import annotations

from ftn.os.m5_contracts import (
    IpdaWindow,
    Month5State,
    PositionOpportunity,
    QuarterlyShift,
)


def _block(raw: dict) -> dict:
    return raw.get("month5") or raw.get("ict_position") or {}


def labeled_quarterly(raw: dict) -> QuarterlyShift:
    b = _block(raw)
    qs = b.get("quarterly_shift") or raw.get("quarterly_shift") or {}
    if isinstance(qs, str):
        qs = {"state": qs}
    ev = raw.get("evidence") or {}
    qs = qs or ev.get("quarterly_shift") or {}
    state = qs.get("state")
    if state not in ("in_progress", "none", "unclear"):
        state = "unclear"
    lb = qs.get("lookback_months", "none")
    if lb not in (3, 4, "none"):
        lb = "none"
    direction = qs.get("direction")
    if direction not in ("bullish", "bearish", "unclear"):
        direction = "unclear"
    return QuarterlyShift(state=state, lookback_months=lb, direction=direction, origin="ict_source")


def labeled_ipda(raw: dict) -> IpdaWindow:
    b = _block(raw)
    ip = b.get("ipda_window") or {}
    if isinstance(ip, int):
        ip = {"days": ip}
    days = ip.get("days") if ip else raw.get("ipda_days")
    if days not in (20, 40, 60):
        return IpdaWindow()
    return IpdaWindow(
        days=days,
        high=ip.get("high"),
        low=ip.get("low"),
        origin="ict_source",
    )


def derive_month5_env(raw: dict) -> Month5State:
    return Month5State(
        quarterly_shift=labeled_quarterly(raw),
        ipda_window=labeled_ipda(raw),
        position_opportunity=PositionOpportunity(flag=False, reason="slice2_env_only"),
    )
