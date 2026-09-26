"""Month-10 Slice 1 contracts. Parse only. No detectors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Pres = Literal["present", "none"]
Dir = Literal["bullish", "bearish", "unclear", "none"]
Rs = Literal["accumulation", "distribution", "unclear", "none"]
Oi = Literal["rising", "falling", "unclear", "none"]
Carry = Literal["premium", "carrying_charge", "none"]
Asset = Literal["bond", "index", "stock", "commodity", "none"]
Watch = Literal["buy", "sell", "none"]

PRES = set(Pres.__args__)
DIRS = set(Dir.__args__)
RSS = set(Rs.__args__)
OIS = set(Oi.__args__)
CARRIES = set(Carry.__args__)
ASSETS = set(Asset.__args__)
WATCHES = set(Watch.__args__)


@dataclass(frozen=True)
class MultiAssetContext:
    flag: bool = False
    reason: str = "unevaluated"


@dataclass(frozen=True)
class Month10State:
    identified_multi_asset: Pres = "none"
    cot_reading: Dir = "none"
    relative_strength: Rs = "none"
    open_interest: Oi = "none"
    commodity_seasonal_note: Pres = "none"
    carrying_charge_note: Carry = "none"
    asset_class: Asset = "none"
    asset_session_note: Pres = "none"
    multi_asset_confluence_note: Pres = "none"
    options_note: Pres = "none"
    watchlist_note: Watch = "none"
    multi_asset_context: MultiAssetContext = field(default_factory=MultiAssetContext)


def _one(v, allowed, default="none"):
    return v if v in allowed else default


def parse_month10(raw: dict) -> Month10State | None:
    block = raw.get("month10") or raw.get("ict_multi_asset")
    if not block:
        return None
    mac = block.get("multi_asset_context") or {}
    if isinstance(mac, bool):
        mac = {"flag": mac}
    return Month10State(
        identified_multi_asset=_one(block.get("identified_multi_asset"), PRES),
        cot_reading=_one(block.get("cot_reading"), DIRS),
        relative_strength=_one(block.get("relative_strength"), RSS),
        open_interest=_one(block.get("open_interest"), OIS),
        commodity_seasonal_note=_one(block.get("commodity_seasonal_note"), PRES),
        carrying_charge_note=_one(block.get("carrying_charge_note"), CARRIES),
        asset_class=_one(block.get("asset_class"), ASSETS),
        asset_session_note=_one(block.get("asset_session_note"), PRES),
        multi_asset_confluence_note=_one(block.get("multi_asset_confluence_note"), PRES),
        options_note=_one(block.get("options_note"), PRES),
        watchlist_note=_one(block.get("watchlist_note"), WATCHES),
        multi_asset_context=MultiAssetContext(
            flag=bool(mac.get("flag", False)),
            reason=mac.get("reason") or "provided_state",
        ),
    )
