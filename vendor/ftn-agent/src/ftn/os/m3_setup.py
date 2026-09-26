"""Month-3 Slice 3: next_setup derivation.

selected_timeframe != none AND anticipated_setup == present.
IOF / sponsorship / structure / traps do not mint the flag.
"""

from __future__ import annotations

from dataclasses import replace

from ftn.os.m3_context import derive_month3_context
from ftn.os.m3_contracts import Month3State, NextSetup


def classify_next_setup(st: Month3State) -> NextSetup:
    if st.selected_timeframe != "none" and st.anticipated_setup == "present":
        return NextSetup(True, "timeframe_plus_anticipated_setup")
    if st.anticipated_setup != "present":
        return NextSetup(False, "no_anticipated_setup")
    return NextSetup(False, "no_selected_timeframe")


def derive_month3(raw: dict) -> Month3State:
    base = derive_month3_context(raw)
    return replace(base, next_setup=classify_next_setup(base))
