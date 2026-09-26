"""Integration tests: lab bridge <-> vendored FTN package (PAPER only, offline)."""
import copy
import json
import sys

import pytest
from pydantic import ValidationError

from ict_lab import ftn_bridge
from ict_lab.ftn_bridge import (
    FTN_ROOT, FtnRefused, ftn_briefing, ftn_briefing_json, ftn_workflow_json,
    resolve_fixture, run_ftn_workflow,
)
from ict_lab.ftn_models import FtnTicket, FtnWorkflowResult

SAMPLE = json.loads((FTN_ROOT / "fixtures" / "sample_eurusd.json").read_text())


@pytest.fixture(autouse=True)
def _workdir(tmp_path, monkeypatch):
    monkeypatch.setenv("FTN_LAB_WORKDIR", str(tmp_path / "ftn_work"))
    monkeypatch.delenv("FTN_LIVE", raising=False)
    yield tmp_path / "ftn_work"


def _snapshot_vendor():
    return sorted(str(p.relative_to(FTN_ROOT)) for p in FTN_ROOT.rglob("*")
                  if "__pycache__" not in p.parts and ".pytest_cache" not in p.parts)


def test_sample_fixture_full_workflow(_workdir):
    before = _snapshot_vendor()
    r = run_ftn_workflow("sample_eurusd")
    t = r.ticket
    assert r.stages == ["PREP", "FILTER", "WATCH", "GATE", "MANAGE", "JOURNAL"]
    assert t.mode == "paper" and t.live_enabled is False and r.orders_placed == 0
    assert t.kind == "entry_candidate" and t.actionable_for_mint and not r.no_trade
    assert t.bias == "bearish" and len(t.four_levels) == 4
    prices = [lv.price for lv in t.four_levels]
    assert prices == sorted(prices, reverse=True) and all(p < t.price for p in prices)
    assert set(r.measurements) == {"pivots", "cbdr", "asian", "flout"}
    pd = SAMPLE["previous_day"]
    assert r.measurements["pivots"]["PP"] == pytest.approx((pd["high"] + pd["low"] + pd["close"]) / 3)
    assert t.pd_confluence and r.journal_markdown and "EURUSD" in r.journal_markdown
    # artefacts go to the work dir, never into the vendored FTN tree
    assert (_workdir / "dispatch" / "out" / "latest.json").is_file()
    assert _snapshot_vendor() == before


def test_compressed_session_is_no_trade():
    pack = copy.deepcopy(SAMPLE); pack["atr"] = 0.0010  # 10 pips < 20
    r = run_ftn_workflow(pack=pack)
    assert r.no_trade and r.ticket.kind == "no_trade" and "compressed_atr" in r.ticket.no_trade_reasons


def test_no_pd_overlap_is_no_trade():
    pack = copy.deepcopy(SAMPLE); pack["pd_arrays"] = []
    r = run_ftn_workflow(pack=pack)
    assert r.no_trade and "no_pd_array_overlap" in r.ticket.no_trade_reasons


def test_incomplete_gate_is_no_trade():
    pack = copy.deepcopy(SAMPLE); pack["setup"]["mss"] = False
    r = run_ftn_workflow(pack=pack)
    assert not r.ticket.gate_ok and "setup_gate_incomplete" in r.ticket.no_trade_reasons


def test_bias_override_and_price():
    r = run_ftn_workflow("sample_eurusd", bias="bullish", price=1.0870)
    assert r.ticket.bias == "bullish" and all(lv.price > 1.0870 for lv in r.ticket.four_levels)


def test_json_wrapper_and_prep_stage():
    out = json.loads(ftn_workflow_json("sample_eurusd"))
    assert out["ticket"]["mode"] == "paper"
    r = run_ftn_workflow("sample_eurusd", stage="prep")
    assert r.stages == ["PREP"] and r.journal_markdown is None


@pytest.mark.parametrize("bad", ["../../config", "/etc/passwd", "nope", "a b"])
def test_fixture_names_are_confined(bad):
    with pytest.raises(ValueError):
        resolve_fixture(bad)
    assert "error" in json.loads(ftn_workflow_json(bad))


def test_evidence_fixture_rejected_by_workflow():
    out = json.loads(ftn_workflow_json("integration_m1_m9_eurusd"))
    assert out["error"].startswith("FtnInputPack validation failed")


def test_invalid_inline_pack():
    pack = copy.deepcopy(SAMPLE); pack["cbdr"] = {"high": 1.0, "low": 1.1}
    out = json.loads(ftn_workflow_json(pack_json=json.dumps(pack)))
    assert "validation failed" in out["error"]
    assert "error" in json.loads(ftn_workflow_json(pack_json="{not json"))


def test_live_unlock_env_refused(monkeypatch):
    monkeypatch.setenv("FTN_LIVE", "1")
    with pytest.raises(FtnRefused):
        run_ftn_workflow("sample_eurusd")
    assert "charter" in json.loads(ftn_workflow_json())["error"]


@pytest.mark.parametrize("cfg", [
    {"mode": "live", "live_enabled": False},
    {"mode": "paper", "live_enabled": True},
])
def test_non_paper_config_refused(monkeypatch, cfg):
    ftn_bridge._ensure_path()
    import ftn.config_load
    monkeypatch.setattr(ftn.config_load, "load_config", lambda: dict(cfg))
    with pytest.raises(FtnRefused):
        ftn_bridge.check_charter()


def test_vendored_config_is_paper_and_caps_unchanged():
    text = (FTN_ROOT / "config.yaml").read_text()
    assert "mode: paper" in text and "live_enabled: false" in text
    for line in ("max_trade_risk_pct: 0.5", "max_daily_loss_pct: 2.0",
                 "max_portfolio_dd_pct: 5.0", "raise_requires: human"):
        assert line in text


def test_ticket_model_enforces_charter():
    good = run_ftn_workflow("sample_eurusd").ticket.model_dump()
    for patch in ({"mode": "live"}, {"live_enabled": True},
                  {"actionable_for_mint": False},          # inconsistent with no reasons
                  {"compressed": True},                     # compressed but not filtered
                  {"no_trade_reasons": ["because"]}):
        with pytest.raises(ValidationError):
            FtnTicket.model_validate({**good, **patch})


def test_bridge_never_loads_broker_adapters():
    run_ftn_workflow("sample_eurusd"); ftn_briefing()
    assert "ftn.adapters.live" not in sys.modules


def test_briefing_integration_fixture():
    b = ftn_briefing("integration_m1_m9_eurusd")
    assert (b.symbol, b.date, b.mode) == ("EURUSD", "2017-01-18", "paper")
    assert len(b.candidates) == 5 and {c.module for c in b.candidates} >= {"REV", "CONSO"}
    assert b.briefing_markdown.startswith("# Month-9 DTR briefing")
    assert json.loads(ftn_briefing_json("m9_reconstruction_eurusd"))["mode"] == "paper"
