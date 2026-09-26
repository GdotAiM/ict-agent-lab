"""Month-10 Slice 3: multi_asset_context derivation.

identified_multi_asset == present → flag true.
COT / RS / OI / seasonal / asset notes do not mint the flag.
"""

from __future__ import annotations

from dataclasses import replace

from ftn.os.m10_context import derive_month10_context
from ftn.os.m10_contracts import Month10State, MultiAssetContext


def classify_multi_asset(st: Month10State) -> MultiAssetContext:
    if st.identified_multi_asset == "present":
        return MultiAssetContext(True, "identified_multi_asset")
    return MultiAssetContext(False, "no_identified_multi_asset")


def derive_month10(raw: dict) -> Month10State:
    base = derive_month10_context(raw)
    return replace(base, multi_asset_context=classify_multi_asset(base))
