"""Month-11 Slice 3: mega_trade derivation.

identified_mega_trade == present → flag true.
Family / quarterly / seasonal / SMT notes do not mint the flag.
"""

from __future__ import annotations

from dataclasses import replace

from ftn.os.m11_context import derive_month11_context
from ftn.os.m11_contracts import MegaTrade, Month11State


def classify_mega_trade(st: Month11State) -> MegaTrade:
    if st.identified_mega_trade == "present":
        return MegaTrade(True, "identified_mega_trade")
    return MegaTrade(False, "no_identified_mega_trade")


def derive_month11(raw: dict) -> Month11State:
    base = derive_month11_context(raw)
    return replace(base, mega_trade=classify_mega_trade(base))
