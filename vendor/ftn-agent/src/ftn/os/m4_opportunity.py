"""Month-4 Slice 3: generic array_opportunity.

kind != none AND polarity in {bullish, bearish}.
Rates / pattern notes / extra arrays do not gate.
"""

from __future__ import annotations

from dataclasses import replace

from ftn.os.m4_catalog import derive_month4_catalog
from ftn.os.m4_contracts import ArrayOpportunity, Month4State


def classify_opportunity(st: Month4State) -> ArrayOpportunity:
    for a in st.arrays:
        if a.kind != "none" and a.polarity in ("bullish", "bearish"):
            return ArrayOpportunity(True, "named_array_plus_polarity")
    return ArrayOpportunity(False, "no_named_directional_array")


def derive_month4(raw: dict) -> Month4State:
    base = derive_month4_catalog(raw)
    return replace(base, array_opportunity=classify_opportunity(base))
