import json

import pytest
from pydantic import ValidationError

from ict_lab.ict_tools import (
    build_hypothesis, compute_risk_reward, detect_instrument, detect_timezone,
    hypothesis_json, parse_window, risk_reward_json,
)

SB_Q = "Does NQ retrace to the NY midnight open during the 10-11am NY Silver Bullet window?"


# -- Risk / reward -------------------------------------------------------------
def test_long_nq_3r():
    rr = compute_risk_reward(18000, 17980, 18060, "long")
    assert (rr.risk, rr.reward, rr.r_multiple) == (20, 60, 3.0)


def test_short_trade():
    rr = compute_risk_reward(18000, 18025, 17950, "short")
    assert (rr.direction, rr.risk, rr.reward, rr.r_multiple) == ("short", 25, 50, 2.0)


@pytest.mark.parametrize("stop,target,expected", [(17980, 18060, "long"), (18020, 17960, "short")])
def test_direction_inferred(stop, target, expected):
    assert compute_risk_reward(18000, stop, target).direction == expected


@pytest.mark.parametrize("direction", ["BUY", "Long", " long "])
def test_direction_aliases(direction):
    assert compute_risk_reward(100, 95, 110, direction).direction == "long"


def test_fractional_r_rounded():
    assert compute_risk_reward(1.1000, 1.0950, 1.1080, "long").r_multiple == 1.6


@pytest.mark.parametrize("args,msg", [
    ((18000, 18020, 18060, "long"), "stop_loss must be below entry"),
    ((18000, 17980, 17950, "short"), "stop_loss must be above entry"),
    ((18000, 17980, 17990, "long"), "target must be above entry"),
    ((18000, 18020, 18010, "short"), "target must be below entry"),
    ((18000, 18000, 18060, "long"), "cannot equal entry"),
    ((18000, 17980, 18060, "sideways"), "direction must be"),
    ((0, 17980, 18060, "long"), "entry must be a positive"),
    ((18000, -1, 18060, "long"), "stop_loss must be a positive"),
])
def test_risk_reward_invalid(args, msg):
    with pytest.raises(ValueError, match=msg):
        compute_risk_reward(*args)
    assert msg in json.loads(risk_reward_json(*args))["error"]


def test_target_equal_entry_rejected():
    with pytest.raises(ValueError):
        compute_risk_reward(100, 95, 100, "long")


# -- Hypothesis parsing ----------------------------------------------------------
@pytest.mark.parametrize("text,expected", [
    ("10-11am", ("10:00", "11:00")),
    ("9:30 to 10:00 am", ("09:30", "10:00")),
    ("2 - 3pm", ("14:00", "15:00")),
    ("between 12-1pm", ("12:00", "13:00")),
    ("no window here", None),
])
def test_parse_window(text, expected):
    assert parse_window(text) == expected


def test_detect_instrument_and_timezone():
    assert detect_instrument(SB_Q) == "NQ"
    assert detect_instrument("does the market go up") is None
    assert detect_timezone(SB_Q) == "America/New_York"
    assert detect_timezone("London open behaviour") == "Europe/London"


def test_build_hypothesis_silver_bullet():
    h = build_hypothesis(SB_Q)
    w = h.measurement_window
    assert (h.instrument, w.start, w.end, w.timezone) == ("NQ", "10:00", "11:00", "America/New_York")
    assert w.label == "Silver Bullet window"
    assert "midnight" in h.observable_condition.lower() or "00:00" in h.observable_condition
    assert len(h.required_evidence) >= 3 and h.status == "draft"


def test_build_hypothesis_overrides():
    h = build_hypothesis(SB_Q, hypothesis="NQ touches the midnight open in the window on most days.",
                         required_evidence=["tick data"], timezone="UTC")
    assert h.hypothesis.startswith("NQ touches") and h.required_evidence == ["tick data"]
    assert h.measurement_window.timezone == "UTC"


@pytest.mark.parametrize("question,err", [
    ("Does price go up at 10-11am?", "instrument"),
    ("Does NQ go up in the morning?", "time window"),
])
def test_build_hypothesis_missing_parts(question, err):
    with pytest.raises(ValueError, match=err):
        build_hypothesis(question)
    assert err in json.loads(hypothesis_json(question))["error"]


def test_build_hypothesis_bad_timezone_returns_error_json():
    out = json.loads(hypothesis_json(SB_Q, timezone="Nowhere/Land"))
    assert out["error"].startswith("ResearchHypothesis validation failed")
    with pytest.raises(ValidationError):
        build_hypothesis(SB_Q, timezone="Nowhere/Land")
