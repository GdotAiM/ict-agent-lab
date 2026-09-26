"""Pydantic v2 models that validate tool outputs before they reach the agent."""
from __future__ import annotations

import json
import re
from typing import Any, Literal, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import (
    BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator,
)

_TOL = 0.011  # rounding tolerance for money comparisons (cents)


class _Base(BaseModel):
    # Keep any extra keys the tools return (e.g. carrier, eta) -- validate what we know.
    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)


# -- Customer-support models ----------------------------------------------------

class OrderItem(_Base):
    name: str = Field(min_length=1)
    qty: int = Field(ge=1)
    price: float = Field(ge=0)


class OrderStatus(_Base):
    order_id: str = Field(pattern=r"^ORD-\w+$")
    customer_id: Optional[str] = None
    status: str = Field(min_length=1)
    items: list[OrderItem] = Field(default_factory=list)
    total: float = Field(gt=0)
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    estimated_delivery: Optional[str] = None
    delivered_date: Optional[str] = None

    @field_validator("status")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.upper()


class RefundRequest(_Base):
    order_id: str = Field(pattern=r"^ORD-\w+$")
    reason: str = Field(min_length=1)
    amount: float = Field(gt=0, description="Refund amount in USD; required and > 0")


class RefundResult(_Base):
    refund_id: str = Field(pattern=r"^REF-[A-Z0-9]+$")
    order_id: str = Field(pattern=r"^ORD-\w+$")
    status: str = Field(min_length=1)
    amount: float = Field(gt=0)
    message: Optional[str] = None
    created_at: Optional[str] = None


class LoyaltyDiscountResult(_Base):
    points_redeemed: int = Field(ge=0)
    points_value: float = Field(ge=0)
    tier: Literal["Silver", "Gold", "Platinum"]
    tier_discount_pct: float = Field(ge=0, le=100)
    tier_discount: float = Field(ge=0)
    original_total: float = Field(gt=0)
    final_total: float = Field(ge=0)
    total_savings: float = Field(ge=0)
    points_earned: int = Field(ge=0)
    remaining_points: int = Field(ge=0)
    note: Optional[str] = None

    @model_validator(mode="after")
    def _consistent(self) -> "LoyaltyDiscountResult":
        if self.points_redeemed % 500:
            raise ValueError("points_redeemed must be a multiple of 500")
        if abs(self.points_value - self.points_redeemed / 100) > _TOL:
            raise ValueError("points_value must equal points_redeemed / 100")
        if self.points_value - self.original_total * 0.5 > _TOL:
            raise ValueError("points value cannot exceed 50% of the order total")
        if self.final_total - self.original_total > _TOL:
            raise ValueError("final_total cannot exceed original_total")
        if abs((self.original_total - self.total_savings) - self.final_total) > _TOL:
            raise ValueError("final_total must equal original_total - total_savings")
        expected_tier = (self.original_total - self.points_value) * self.tier_discount_pct / 100
        if abs(expected_tier - self.tier_discount) > _TOL:
            raise ValueError("tier_discount must be tier_discount_pct of the post-points subtotal")
        return self


# -- ICT research models ----------------------------------------------------------

class RiskReward(_Base):
    direction: Literal["long", "short"]
    entry: float = Field(gt=0)
    stop_loss: float = Field(gt=0)
    target: float = Field(gt=0)
    risk: float = Field(gt=0, description="Points risked per unit (|entry - stop|)")
    reward: float = Field(gt=0, description="Points to target per unit (|target - entry|)")
    r_multiple: float = Field(gt=0, description="reward / risk")

    @model_validator(mode="after")
    def _sides(self) -> "RiskReward":
        if self.direction == "long" and not (self.stop_loss < self.entry < self.target):
            raise ValueError("long trade requires stop_loss < entry < target")
        if self.direction == "short" and not (self.target < self.entry < self.stop_loss):
            raise ValueError("short trade requires target < entry < stop_loss")
        return self


_HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class MeasurementWindow(_Base):
    start: str = Field(description="HH:MM (24h) in `timezone`")
    end: str = Field(description="HH:MM (24h) in `timezone`")
    timezone: str = Field(description="IANA zone, e.g. America/New_York")
    label: Optional[str] = None

    @field_validator("start", "end")
    @classmethod
    def _hhmm(cls, v: str) -> str:
        if not _HHMM.match(v):
            raise ValueError("time must be HH:MM (24h)")
        return v

    @field_validator("timezone")
    @classmethod
    def _tz(cls, v: str) -> str:
        try:
            ZoneInfo(v)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError(f"unknown IANA timezone: {v}")
        return v

    @model_validator(mode="after")
    def _order(self) -> "MeasurementWindow":
        if self.start >= self.end:
            raise ValueError("window start must be before end (same day)")
        return self


class ResearchHypothesis(_Base):
    question: str = Field(min_length=5)
    hypothesis: str = Field(min_length=10)
    instrument: str = Field(min_length=1)
    observable_condition: str = Field(min_length=5)
    invalidation_condition: str = Field(min_length=5)
    measurement_window: MeasurementWindow
    required_evidence: list[str] = Field(min_length=1)
    status: Literal["draft", "testing", "supported", "rejected"] = "draft"

    @field_validator("required_evidence")
    @classmethod
    def _non_empty(cls, v: list[str]) -> list[str]:
        v = [e.strip() for e in v if e and e.strip()]
        if not v:
            raise ValueError("required_evidence needs at least one non-empty item")
        return v


# -- Helpers ------------------------------------------------------------------------

def validation_error_json(model: "type[BaseModel] | str", exc: ValidationError, raw: Any = None) -> str:
    """Clear, compact error payload for the agent when a tool output is invalid."""
    name = model if isinstance(model, str) else model.__name__
    errors = [
        {"field": ".".join(str(p) for p in e["loc"]) or "(model)", "problem": e["msg"]}
        for e in exc.errors()
    ]
    payload: dict[str, Any] = {
        "error": f"{name} validation failed; do not use these numbers.",
        "details": errors,
    }
    if raw is not None:
        payload["raw"] = raw
    return json.dumps(payload)


def validate_to_json(model: type[BaseModel], data: Any) -> str:
    """Validate ``data`` against ``model``; return model JSON or an error JSON."""
    try:
        if isinstance(data, str):
            data = json.loads(data)
        return model.model_validate(data).model_dump_json(exclude_none=True)
    except json.JSONDecodeError as exc:
        return json.dumps({"error": f"{model.__name__}: output was not valid JSON ({exc.msg})"})
    except ValidationError as exc:
        return validation_error_json(model, exc, raw=data)
