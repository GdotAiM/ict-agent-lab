"""Month-12 Slice 3: top_down derivation.

identified_top_down == present → flag true.
Horizon notes do not mint the flag.
Missing intermediate does not block an explicit identification.
"""

from __future__ import annotations

from dataclasses import replace

from ftn.os.m12_context import derive_month12_context
from ftn.os.m12_contracts import Month12State, TopDown


def classify_top_down(st: Month12State) -> TopDown:
    if st.identified_top_down == "present":
        return TopDown(True, "identified_top_down")
    return TopDown(False, "no_identified_top_down")


def derive_month12(raw: dict) -> Month12State:
    base = derive_month12_context(raw)
    return replace(base, top_down=classify_top_down(base))
