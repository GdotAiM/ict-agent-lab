"""Month-1 Slice 2: labeled foundation context.

Does not derive setup_elements.
Does not write profile or liquidity_probe.
Does not inspect raw month2–9.
"""

from __future__ import annotations

from ftn.os.m1_contracts import Month1State, SetupElements, _pres


def _block(raw: dict):
    ev = raw.get("evidence") or {}
    m1 = raw.get("month1") or raw.get("ict_foundation") or {}
    return ev, m1


def derive_month1_context(raw: dict) -> Month1State:
    ev, m1 = _block(raw)
    src = ev.get("month1") or ev or m1
    side = src.get("dealing_range_side") or m1.get("dealing_range_side") or "none"
    if side not in ("premium", "equilibrium", "discount"):
        side = "none"
    return Month1State(
        identified_setup_elements=_pres(
            src.get("identified_setup_elements") or m1.get("identified_setup_elements")
        ),
        dealing_range_side=side,
        conditioning_note=_pres(src.get("conditioning_note") or m1.get("conditioning_note")),
        focus_note=_pres(src.get("focus_note") or m1.get("focus_note")),
        fair_valuation_note=_pres(src.get("fair_valuation_note") or m1.get("fair_valuation_note")),
        liquidity_run_note=_pres(src.get("liquidity_run_note") or m1.get("liquidity_run_note")),
        impulse_note=_pres(src.get("impulse_note") or m1.get("impulse_note")),
        protraction_note=_pres(src.get("protraction_note") or m1.get("protraction_note")),
        setup_elements=SetupElements(flag=False, reason="slice2_context_only"),
    )
