"""PAM1 evidence / context contract.

Parse and normalize labeled PAM1 model-instance evidence.
Does not derive Charter recognition.
Does not create tickets or mutate Core.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Pres = Literal["present", "none"]
Dir = Literal["bullish", "bearish", "none"]
PD = Literal["premium", "discount", "equilibrium", "none"]
ObjType = Literal["previous_daily_high", "previous_daily_low", "none"]
Fib = Literal["62_percent", "none"]

PRES = set(Pres.__args__)
DIRS = set(Dir.__args__)
PDS = set(PD.__args__)
OBJS = set(ObjType.__args__)
FIBS = set(Fib.__args__)


def _one(v, allowed):
    return v if v in allowed else "none"


@dataclass(frozen=True)
class IpdaContext:
    present: Pres = "none"
    lookback_trading_days: object = "none"  # 20 | 40 | "none"


@dataclass(frozen=True)
class LiquidityObjective:
    present: Pres = "none"
    type: ObjType = "none"


@dataclass(frozen=True)
class OteContext:
    present: Pres = "none"
    fib_level: Fib = "none"


@dataclass(frozen=True)
class PriceStructureConfirming:
    liquidity_raid: Pres = "none"
    displacement: Pres = "none"
    market_structure_shift: Pres = "none"
    institutional_reference: Pres = "none"


@dataclass(frozen=True)
class Pam1Evidence:
    """Labeled PAM1 model-instance context (not a detector result)."""

    direction: Dir = "none"
    ipda: IpdaContext = field(default_factory=IpdaContext)
    institutional_sponsorship: Pres = "none"
    premium_discount_context: PD = "none"
    liquidity_objective: LiquidityObjective = field(default_factory=LiquidityObjective)
    ny_execution_window: Pres = "none"
    ote: OteContext = field(default_factory=OteContext)
    directional_link: Pres = "none"  # entry → objective relationship labeled present
    confirming: PriceStructureConfirming = field(default_factory=PriceStructureConfirming)


def _ipda(raw: dict) -> IpdaContext:
    days = raw.get("lookback_trading_days")
    if days not in (20, 40, "20", "40"):
        days = "none"
    elif isinstance(days, str) and days.isdigit():
        days = int(days)
    return IpdaContext(
        present=_one(raw.get("present"), PRES),
        lookback_trading_days=days,
    )


def _obj(raw: dict) -> LiquidityObjective:
    return LiquidityObjective(
        present=_one(raw.get("present"), PRES),
        type=_one(raw.get("type"), OBJS),  # type: ignore[arg-type]
    )


def _ote(raw: dict) -> OteContext:
    return OteContext(
        present=_one(raw.get("present"), PRES),
        fib_level=_one(raw.get("fib_level"), FIBS),  # type: ignore[arg-type]
    )


def _conf(raw: dict) -> PriceStructureConfirming:
    return PriceStructureConfirming(
        liquidity_raid=_one(raw.get("liquidity_raid"), PRES),
        displacement=_one(raw.get("displacement"), PRES),
        market_structure_shift=_one(raw.get("market_structure_shift"), PRES),
        institutional_reference=_one(raw.get("institutional_reference"), PRES),
    )


def parse_pam1_evidence(raw: dict) -> Pam1Evidence | None:
    """Read labeled pam1_model_context from evidence or charter block."""
    ev = raw.get("evidence") or {}
    ch = raw.get("charter") or raw.get("ict_charter") or {}
    block = (
        ev.get("pam1_model_context")
        or ch.get("pam1_model_context")
        or raw.get("pam1_model_context")
    )
    if not block or not isinstance(block, dict):
        return None
    ip = block.get("ipda_data_range") or block.get("ipda") or {}
    lo = block.get("liquidity_objective") or {}
    ote = block.get("ote") or {}
    ps = block.get("price_structure") or block.get("confirming") or {}
    return Pam1Evidence(
        direction=_one(block.get("direction"), DIRS),  # type: ignore[arg-type]
        ipda=_ipda(ip if isinstance(ip, dict) else {}),
        institutional_sponsorship=_one(block.get("institutional_sponsorship"), PRES),
        premium_discount_context=_one(block.get("premium_discount_context"), PDS),  # type: ignore[arg-type]
        liquidity_objective=_obj(lo if isinstance(lo, dict) else {}),
        ny_execution_window=_one(block.get("ny_execution_window"), PRES),
        ote=_ote(ote if isinstance(ote, dict) else {}),
        directional_link=_one(block.get("directional_link"), PRES),
        confirming=_conf(ps if isinstance(ps, dict) else {}),
    )
