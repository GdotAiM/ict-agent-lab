import json

import pytest
from pydantic import ValidationError

from ict_lab.loyalty import compute_loyalty_discount
from ict_lab.models import (
    LoyaltyDiscountResult, MeasurementWindow, OrderStatus, RefundRequest, RefundResult,
    ResearchHypothesis, RiskReward, validate_to_json,
)

ORDER = {
    "order_id": "ORD-002", "customer_id": "CUST-123", "status": "delivered",
    "items": [{"name": "Kindle Paperwhite", "qty": 1, "price": 139.99}],
    "total": 139.99, "tracking_number": "TRK123456789", "carrier": "USPS",
    "delivered_date": "2026-09-23",
}


# -- OrderStatus ---------------------------------------------------------------
def test_order_status_valid_and_extra_keys_kept():
    o = OrderStatus.model_validate({**ORDER, "gift_wrap": True})
    assert o.status == "DELIVERED" and o.total == 139.99
    assert o.model_dump()["gift_wrap"] is True


@pytest.mark.parametrize("patch", [
    {"order_id": "XYZ-1"}, {"total": 0}, {"total": -5},
    {"items": [{"name": "x", "qty": 0, "price": 1}]},
])
def test_order_status_invalid(patch):
    with pytest.raises(ValidationError):
        OrderStatus.model_validate({**ORDER, **patch})


def test_order_status_missing_total():
    data = dict(ORDER); data.pop("total")
    with pytest.raises(ValidationError):
        OrderStatus.model_validate(data)


# -- Refunds -------------------------------------------------------------------
def test_refund_request_requires_positive_amount():
    assert RefundRequest(order_id="ORD-002", reason="return", amount=139.99).amount == 139.99
    for bad in (0, -1):
        with pytest.raises(ValidationError):
            RefundRequest(order_id="ORD-002", reason="return", amount=bad)
    with pytest.raises(ValidationError):
        RefundRequest(order_id="ORD-002", reason="return")


def test_refund_result_zero_amount_rejected():
    ok = {"refund_id": "REF-42R2DRAX", "order_id": "ORD-002", "status": "APPROVED", "amount": 139.99}
    assert RefundResult.model_validate(ok).amount == 139.99
    out = json.loads(validate_to_json(RefundResult, {**ok, "amount": 0}))
    assert "error" in out and out["details"][0]["field"] == "amount"


# -- Loyalty -------------------------------------------------------------------
def test_loyalty_gold_4250_points_150():
    r = compute_loyalty_discount(4250, "Gold", 150.0, "standard")
    m = LoyaltyDiscountResult.model_validate(r)
    assert (m.points_redeemed, m.tier_discount_pct, m.final_total, m.remaining_points) == (4000, 10.0, 99.0, 400)
    assert m.points_value == 40.0 and m.tier_discount == 11.0 and m.total_savings == 51.0


def test_loyalty_points_capped_at_half_order():
    r = compute_loyalty_discount(100_000, "Platinum", 30.0, "device")
    assert r["points_redeemed"] == 1500  # $15 = 50% of $30
    LoyaltyDiscountResult.model_validate(r)


def test_loyalty_below_block_redeems_nothing():
    r = compute_loyalty_discount(499, "Silver", 20.0)
    assert r["points_redeemed"] == 0 and r["final_total"] == 20.0


@pytest.mark.parametrize("patch", [
    {"final_total": 95.0},              # inconsistent with savings (the old wrong answer)
    {"points_redeemed": 4100},          # not a 500 block
    {"points_value": 50.0},             # != points/100
    {"tier": "Diamond"},
    {"tier_discount": 15.0},            # 10% of pre-points total instead of post-points
    {"remaining_points": -1},
])
def test_loyalty_inconsistent_outputs_rejected(patch):
    good = compute_loyalty_discount(4250, "Gold", 150.0)
    out = json.loads(validate_to_json(LoyaltyDiscountResult, {**good, **patch}))
    assert out["error"].startswith("LoyaltyDiscountResult validation failed")


def test_validate_to_json_non_json():
    out = json.loads(validate_to_json(LoyaltyDiscountResult, "not json"))
    assert "not valid JSON" in out["error"]


@pytest.mark.parametrize("bad", [("Bronze", 10.0, "standard"), ("Gold", 0, "standard"), ("Gold", 10.0, "toys")])
def test_loyalty_bad_inputs(bad):
    tier, total, cat = bad
    with pytest.raises(ValueError):
        compute_loyalty_discount(1000, tier, total, cat)


# -- RiskReward / ResearchHypothesis models --------------------------------------
def test_risk_reward_model_side_checks():
    RiskReward(direction="long", entry=100, stop_loss=90, target=130, risk=10, reward=30, r_multiple=3)
    with pytest.raises(ValidationError):
        RiskReward(direction="long", entry=100, stop_loss=110, target=130, risk=10, reward=30, r_multiple=3)
    with pytest.raises(ValidationError):
        RiskReward(direction="short", entry=100, stop_loss=90, target=80, risk=10, reward=20, r_multiple=2)


@pytest.mark.parametrize("kw", [
    {"start": "10:00", "end": "09:00", "timezone": "America/New_York"},
    {"start": "10am", "end": "11:00", "timezone": "America/New_York"},
    {"start": "10:00", "end": "11:00", "timezone": "Mars/Olympus"},
])
def test_measurement_window_invalid(kw):
    with pytest.raises(ValidationError):
        MeasurementWindow(**kw)


def test_research_hypothesis_requires_evidence():
    base = dict(
        question="Does X happen?", hypothesis="X happens more often than baseline.",
        instrument="NQ", observable_condition="price touches level",
        invalidation_condition="touch rate not above baseline",
        measurement_window={"start": "10:00", "end": "11:00", "timezone": "America/New_York"},
    )
    assert ResearchHypothesis(**base, required_evidence=["1m data"]).status == "draft"
    for ev in ([], ["  "]):
        with pytest.raises(ValidationError):
            ResearchHypothesis(**base, required_evidence=ev)
