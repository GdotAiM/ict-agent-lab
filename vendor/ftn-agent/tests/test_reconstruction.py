
"""Oracle test: engine never opens the gold file. Test harness does."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ftn.os.briefing import brief_from_fixture
from ftn.os.contracts import load_day_context
from ftn.models.rev import evaluate_rev


FIXTURE = ROOT / "fixtures/m9_reconstruction_eurusd.json"
GOLD = ROOT / "fixtures/m9_reconstruction_eurusd.expected.json"
CASES = [
    ("m9_reconstruction_eurusd.json", "m9_reconstruction_eurusd.expected.json"),
    ("m9_rev_no_raid.json", "m9_rev_no_raid.expected.json"),
    ("m9_rev_unnamed_no_htf.json", "m9_rev_unnamed_no_htf.expected.json"),
    ("m9_rev_eligible_no_mss.json", "m9_rev_eligible_no_mss.expected.json"),
    ("m9_rev_inside_box.json", "m9_rev_inside_box.expected.json"),
    ("m9_conso_fade_only.json", "m9_conso_fade_only.expected.json"),
    ("m9_bb_offset.json", "m9_bb_offset.expected.json"),
    ("m9_pip20_ny.json", "m9_pip20_ny.expected.json"),
    ("m9_raw_eurusd.json", "m9_raw_eurusd.expected.json"),
]

CASES_CHARTER = [
    ("charter_evidence_eurusd.json", "present", ("pam1",), True),
]


CASES_M12 = [
    ("m12_evidence_eurusd.json", "none", "present", True),
]


CASES_M11 = [
    ("m11_evidence_eurusd.json", "fx", "present", True),
]


CASES_M10 = [
    ("m10_evidence_eurusd.json", "present", "index", True),
]


CASES_M1 = [
    ("m1_evidence_eurusd.json", "present", "discount", True),
]


CASES_M2 = [
    ("m2_evidence_eurusd.json", "present", "present", True),
]


CASES_M3 = [
    ("m3_evidence_eurusd.json", "monthly", "present", True),
]


CASES_M4 = [
    ("m4_evidence_eurusd.json", ("fvg", "liquidity_void"), "double_bottom", True),
]


CASES_M5 = [
    ("m5_evidence_eurusd.json", "in_progress", 60, "breaker_swing_point", True),
]


CASES_M6 = [
    ("m6_evidence_xauusd.json", "bull", "mw_bullish_daily_correcting", True, "incomplete"),
]


CASES_M7 = [
    ("m7_path_eurusd.json", "classic_tuesday_low_of_week", True, "low"),
    ("m7_evidence_eurusd.json", "none", False, "unclear"),
]


CASES_M8 = [
    # fixture, expect_profile, expect_gate, notes
    ("m8_path_eurusd.json", "normal_protraction_sell", True),
    ("m8_s4_late_rally.json", "delayed_protraction_sell", True),
    ("m8_s4_late_rally_window_only.json", "delayed_protraction_sell", True),
    ("m8_s4_no_hh.json", "none", True),
    ("m8_s4_first_move_only.json", "none", True),
    ("m8_evidence_eurusd.json", "none", True),
]


def test_fixture_has_no_winner():
    raw = json.loads(FIXTURE.read_text())
    assert "expected_winner" not in raw and "pick" not in raw
    load_day_context(FIXTURE)


def test_loader_rejects_winner_key(tmp_path):
    bad = tmp_path / "bad.json"
    raw = json.loads(FIXTURE.read_text())
    raw["expected_winner"] = "REV"
    bad.write_text(json.dumps(raw))
    try:
        load_day_context(bad)
        raise AssertionError("should reject")
    except ValueError:
        pass


def test_reconstruct_matches_gold():
    gold = json.loads(GOLD.read_text())
    state, cands, *_ = brief_from_fixture(FIXTURE)
    ctx = state.context
    read = gold["expected_market_read"]
    assert ctx.sentiment.direction == read["sentiment"]
    assert ctx.sentiment.indicator.state == read["wr_state"]
    assert ctx.pair_institutional.sponsorship.daily == read["sponsorship"]
    assert ctx.pair_institutional.state == read["daytrade_iof"]
    assert ctx.pair_institutional.confidence == read["daytrade_confidence"]
    assert ctx.dxy.get("relationship") == read["dxy"]
    assert ctx.profile == read["profile"]
    assert ctx.origin_pd_array == read["origin"]
    got = {c.module: c.state for c in cands}
    assert got == gold["expected_candidate_states"]


def test_gold_edit_does_not_change_engine(tmp_path):
    """Changing the gold file must not change engine output."""
    state, cands, *_ = brief_from_fixture(FIXTURE)
    before = {c.module: c.state for c in cands}
    poisoned = tmp_path / "poisoned.expected.json"
    data = json.loads(GOLD.read_text())
    data["expected_candidate_states"]["REV"] = "ineligible"
    poisoned.write_text(json.dumps(data))
    # engine path does not accept/read this file
    state2, cands2, *_ = brief_from_fixture(FIXTURE)
    after = {c.module: c.state for c in cands2}
    assert before == after
    assert after["REV"] == "selected"
    assert json.loads(poisoned.read_text())["expected_candidate_states"]["REV"] == "ineligible"


def test_rev_reads_market_state_only():
    state, *_ = brief_from_fixture(FIXTURE)
    out = evaluate_rev(state)
    assert out["candidate"].module == "REV"
    assert out["eligibility"]["named_extreme_raid"] is True
    assert out["execution"]["confirmed"] is True
    assert out["evidence"]["fingerprint"] == state.fingerprint




def test_all_reconstruction_cases():
    for fx_name, gold_name in CASES:
        fx = ROOT / "fixtures" / fx_name
        gold = json.loads((ROOT / "fixtures" / gold_name).read_text())
        raw = json.loads(fx.read_text())
        assert "expected_winner" not in raw and "pick" not in raw
        state, cands, *_ = brief_from_fixture(fx)
        got = {c.module: c.state for c in cands}
        exp = gold["expected_candidate_states"]
        assert got == exp, f"{fx_name}: {got} != {exp}"




def test_conso_fade_play_and_preemption():
    from ftn.models.conso import evaluate_conso
    fade = brief_from_fixture(ROOT / "fixtures/m9_conso_fade_only.json")[0]
    pack = evaluate_conso(fade)
    assert pack["play"] == "fade_edge" and pack["target"] == "eq"
    assert pack["candidate"].state == "unevaluated"
    boxed = brief_from_fixture(ROOT / "fixtures/m9_rev_inside_box.json")
    states = {c.module: c.state for c in boxed[1]}
    assert states["REV"] == "selected" and states["CONSO"] == "suppressed"
    pack2 = evaluate_conso(boxed[0])
    assert pack2["play"] == "fade_edge"  # still eligible underneath preemption




def test_bb_engines():
    from ftn.models.bb import evaluate_bb
    off = brief_from_fixture(ROOT / "fixtures/m9_bb_offset.json")[0]
    pack = evaluate_bb(off)
    assert pack["engine"] == "offset" and pack["side"] == "buy"
    wait = brief_from_fixture(ROOT / "fixtures/m9_rev_no_raid.json")[0]
    w = evaluate_bb(wait)
    assert w["eligibility"]["waiting_judas"] is True
    assert w["engine"] is None
    inv = brief_from_fixture(ROOT / "fixtures/m9_reconstruction_eurusd.json")
    assert {c.module: c.state for c in inv[1]}["BB"] == "invalidated"




def test_pip20_window_and_bb_suppress():
    from ftn.models.pip20 import evaluate_pip20
    st, cands, *_ = brief_from_fixture(ROOT / "fixtures/m9_pip20_ny.json")
    pack = evaluate_pip20(st)
    assert pack["window"] == "ny_expansion" and pack["candidate"].eligible
    states = {c.module: c.state for c in cands}
    assert states["PIP20"] == "unevaluated" and states["BB"] == "suppressed"




def test_session_ticket_one_per_session(tmp_path=None):
    from ftn.os.session_ticket import path_for, load_ticket
    st0, cands0, *_ = brief_from_fixture(FIXTURE)
    # ensure a selected exists
    sel = next(c for c in cands0 if c.state == "selected")
    st1, cands1, md1, _ = brief_from_fixture(FIXTURE)
    ticket = st1.context.session_ticket
    assert ticket is not None
    assert ticket.module == sel.module
    states0 = {c.module: c.state for c in cands0}
    states1 = {c.module: c.state for c in cands1}
    assert states0 == states1
    st2, cands2, md2, _ = brief_from_fixture(FIXTURE)
    assert st2.context.session_ticket.id == ticket.id
    assert {c.module: c.state for c in cands2} == states1
    assert "No second entry" in md2




def test_dtr_derives_unlabeled_raw():
    import json
    raw = json.loads((ROOT / "fixtures/m9_raw_eurusd.json").read_text())
    assert "profile" not in raw
    assert "state" not in raw.get("pair_institutional", {})
    from ftn.os.dtr import build_context
    ctx = build_context(ROOT / "fixtures/m9_raw_eurusd.json")
    gold = json.loads((ROOT / "fixtures/m9_raw_eurusd.expected.json").read_text())["expected_market_read"]
    assert ctx.profile == gold["profile"]
    assert ctx.pair_institutional.state == gold["daytrade_iof"]
    assert ctx.pair_institutional.confidence == gold["daytrade_confidence"]
    assert ctx.sentiment.direction == gold["sentiment"]




def test_wr_from_bars():
    import json
    from ftn.os.dtr import build_context
    raw = json.loads((ROOT / "fixtures/m9_raw_eurusd.json").read_text())
    assert raw["sentiment"]["indicator"].get("value") is None
    ctx = build_context(ROOT / "fixtures/m9_raw_eurusd.json")
    assert ctx.sentiment.indicator.state == "bullish"
    assert ctx.sentiment.indicator.value <= -80




def test_raid_from_bars():
    import json
    raw = json.loads((ROOT / "fixtures/m9_raw_eurusd.json").read_text())
    assert not (raw.get("evidence") or {}).get("raid", {}).get("taken")
    from ftn.os.dtr import build_context
    ctx = build_context(ROOT / "fixtures/m9_raw_eurusd.json")
    raid = ctx.evidence["raid"]
    assert raid["taken"] and raid["level"] == "pdl" and raid["source"] == "detector"




def test_mss_from_bars():
    import json
    raw = json.loads((ROOT / "fixtures/m9_raw_eurusd.json").read_text())
    assert "mss" not in (raw.get("evidence") or {})
    from ftn.os.dtr import build_context
    ctx = build_context(ROOT / "fixtures/m9_raw_eurusd.json")
    assert ctx.evidence.get("mss") is True
    assert ctx.evidence.get("mss_meta", {}).get("source") == "detector"




def test_box_from_bars():
    import json
    from ftn.os.dtr import build_context
    raw = json.loads((ROOT / "fixtures/m9_raw_eurusd.json").read_text())
    assert "box" not in (raw.get("evidence") or {})
    ctx = build_context(ROOT / "fixtures/m9_raw_eurusd.json")
    assert not ctx.evidence.get("box")
    fade = json.loads((ROOT / "fixtures/m9_conso_fade_only.json").read_text())
    assert "box" not in (fade.get("evidence") or {})
    ctx2 = build_context(ROOT / "fixtures/m9_conso_fade_only.json")
    assert ctx2.evidence.get("box") and ctx2.evidence["box"].get("source") == "detector"
    assert ctx2.profile == "consolidation"




def test_origin_from_arrays():
    import json
    from ftn.os.dtr import build_context
    raw = json.loads((ROOT / "fixtures/m9_raw_eurusd.json").read_text())
    assert "origin_pd_array" not in raw
    ctx = build_context(ROOT / "fixtures/m9_raw_eurusd.json")
    assert ctx.origin_pd_array == "D_FVG_bull"
    assert "PDH_liq" in ctx.opposing_target_arrays




def test_calendar_focus():
    from ftn.os.dtr import build_context
    news = build_context(ROOT / "fixtures/m9_raw_eurusd.json")
    assert news.focus_pair == "EURUSD" and news.evidence.get("focus_source") == "calendar"
    wl = build_context(ROOT / "fixtures/m9_calendar_watchlist.json")
    assert wl.focus_pair == "GBPUSD" and wl.evidence.get("focus_source") == "watchlist"
    idle = build_context(ROOT / "fixtures/m9_calendar_idle.json")
    assert idle.evidence.get("idle") is True and idle.evidence.get("focus_source") == "idle"




def test_dxy_relationship():
    from ftn.os.dtr import build_context
    from ftn.os.dxy import dxy_relationship
    ctx = build_context(ROOT / "fixtures/m9_raw_eurusd.json")
    assert ctx.dxy.get("relationship") == "supportive"
    assert dxy_relationship("EURUSD", "bearish", {"state": "bearish"}) == "contradictory"
    assert dxy_relationship("USDJPY", "bearish", {"state": "bearish"}) == "supportive"
    assert dxy_relationship("EURUSD", "bullish", None) == "unavailable"




def test_session_clocks():
    from ftn.os.clocks import session_clocks
    from ftn.os.dtr import build_context
    assert session_clocks("ny_am", "08:20")["protraction_stage"] == "cme_0820"
    assert session_clocks("asia", "19:00")["pip20_window"] == "asia_ny_stops"
    ctx = build_context(ROOT / "fixtures/m9_raw_eurusd.json")
    assert ctx.evidence.get("protraction_stage") == "gmt_0000"




def test_x_ask_read_only():
    from ftn.os.briefing import brief_from_fixture
    from ftn.os.handoff import build_handoff
    from ftn.os.x_ask import why_selected
    st, cands, *_rest = brief_from_fixture(FIXTURE)
    ftn = _rest[-1] if _rest else {}
    ans = why_selected(build_handoff(st, cands, ftn if isinstance(ftn, dict) else {}))
    assert ans["selected"]["module"] == "REV"
    assert "must not edit" in ans["rule"]




def test_mint_draft_paper():
    from ftn.os.briefing import brief_from_fixture
    from ftn.os.handoff import build_handoff
    from ftn.os.mint_draft import draft_from_handoff
    st, cands, *rest = brief_from_fixture(FIXTURE)
    ftn = rest[-1] if rest else {}
    d = draft_from_handoff(build_handoff(st, cands, ftn if isinstance(ftn, dict) else {}))
    assert d["actionable_for_mint"] is False and d["mode"] == "paper"
    assert d["module"] == "REV" and d["side"] == "buy"




def test_live_data_off_by_default():
    import os
    os.environ.pop("FTN_LIVE_DATA", None)
    from ftn.adapters.live import fetch_quote, live_data_allowed, refuse_live_orders
    assert live_data_allowed({}) is False
    q = fetch_quote("EURUSD", {})
    assert q["ok"] is False and q["reason"] == "live_data_disabled"
    assert refuse_live_orders()["reason"] == "live_orders_refused"


def test_month8_contracts_and_fixture():
    import json
    from ftn.os.contracts import load_day_context
    from ftn.os.m8_contracts import classify_cbdr
    fx = ROOT / "fixtures/m8_reconstruction_eurusd.json"
    raw = json.loads(fx.read_text())
    assert "pick" not in raw and "expected_winner" not in raw
    ctx = load_day_context(fx)
    m8 = ctx.month8
    assert m8 is not None
    assert m8.cbdr.classification == "ideal"
    assert m8.cbdr.daytrade_classic is True
    assert m8.ict_london_profile == "normal_protraction_sell"
    assert m8.london_session_gate.allowed is True
    assert m8.daily_extreme_projection.draw == "high"
    assert m8.htf_entry_overlap.present is True
    assert ctx.profile != m8.ict_london_profile
    assert classify_cbdr(26) == "ideal"
    assert classify_cbdr(45) == "expanded"
    assert classify_cbdr(55) == "wide"



def test_month8_evidence_derives_gate():
    import json
    from ftn.os.m8_detect import derive_month8_measures
    raw = json.loads((ROOT / "fixtures/m8_evidence_eurusd.json").read_text())
    assert "ict_london_profile" not in raw.get("month8", {})
    assert "london_session_gate" not in raw.get("month8", {})
    st = derive_month8_measures(raw)
    assert st.cbdr.classification == "ideal"
    assert st.london_session_gate.allowed is True
    assert st.ict_london_profile == "none"
    assert st.daytrade_opportunity is False
    assert st.ict_true_day.day_anchor == "00:00"
    assert st.ict_true_day.clock == "America/New_York"



def test_month8_slice2_does_not_name_profile():
    import json
    from ftn.os.m8_detect import derive_month8_measures
    raw = json.loads((ROOT / "fixtures/m8_path_eurusd.json").read_text())
    st = derive_month8_measures(raw)
    assert st.ict_london_profile == "none"


def test_month8_profile_from_path():
    import json
    from ftn.os.m8_profile import derive_month8_profile
    raw = json.loads((ROOT / "fixtures/m8_path_eurusd.json").read_text())
    assert "ict_london_profile" not in (raw.get("month8") or {})
    st = derive_month8_profile(raw)
    assert st.cbdr.classification == "ideal"
    assert st.london_session_gate.allowed is True
    assert st.ict_london_profile == "normal_protraction_sell"
    assert st.daytrade_opportunity is True
    # IOF + ideal CBDR without path must not be enough
    raw2 = json.loads((ROOT / "fixtures/m8_evidence_eurusd.json").read_text())
    raw2["pair_institutional"]["state"] = "bearish"
    st2 = derive_month8_profile(raw2)
    assert st2.ict_london_profile == "none"


def test_month8_expanded_gate_is_hermes():
    from ftn.os.m8_contracts import CbdrState
    from ftn.os.m8_detect import london_gate_from_measures
    cb = CbdrState(height_pips=45, classification="expanded")
    g = london_gate_from_measures(cb, 20)
    assert g.allowed is False and g.reason == "expanded_cbdr"
    assert g.origin == "hermes_interpretation"
    wide = london_gate_from_measures(CbdrState(height_pips=55, classification="wide"), 20)
    assert wide.origin == "ict_source" and wide.reason == "wide_cbdr"



def test_month8_slice4_regression():
    import json
    from ftn.os.m8_profile import derive_month8_profile
    cases = [
        ("m8_path_eurusd.json", "normal_protraction_sell"),
        ("m8_s4_late_rally.json", "delayed_protraction_sell"),
        ("m8_s4_late_rally_window_only.json", "delayed_protraction_sell"),
        ("m8_s4_no_hh.json", "none"),
        ("m8_s4_first_move_only.json", "none"),
        ("m8_evidence_eurusd.json", "none"),
    ]
    for name, expect in cases:
        raw = json.loads((ROOT / "fixtures" / name).read_text())
        raw.setdefault("pair_institutional", {})["state"] = "bearish"
        st = derive_month8_profile(raw)
        assert st.ict_london_profile == expect, f"{name}: {st.ict_london_profile} != {expect}"



def test_month8_slice5_projection():
    import json
    from ftn.os.m8_profile import derive_month8_profile
    from ftn.os.m8_project import project_daily_extreme
    from ftn.os.m8_contracts import CbdrState
    raw = json.loads((ROOT / "fixtures/m8_path_eurusd.json").read_text())
    st = derive_month8_profile(raw)
    assert st.daily_extreme_projection.draw == "high"
    assert st.daily_extreme_projection.selected_level == 1.063
    assert st.daily_extreme_projection.origin == "ict_source"
    bull = project_daily_extreme(
        CbdrState(body_high=1.0606, body_low=1.0582, height_pips=24, classification="ideal"),
        "bullish",
    )
    assert bull.draw == "low" and bull.selected_level == 1.0558



def test_month8_slice6_htf():
    import json
    from ftn.os.m8_profile import derive_month8_profile
    from ftn.os.m8_htf import annotate_htf_overlap
    raw = json.loads((ROOT / "fixtures/m8_path_eurusd.json").read_text())
    st = derive_month8_profile(raw)
    assert st.htf_entry_overlap.present is True
    assert st.htf_entry_overlap.relationship == "seed_only"
    assert st.htf_entry_overlap.array_id == "D_FVG_bear"
    assert annotate_htf_overlap({}).present is False



def test_month8_slice7_dtr():
    from ftn.os.dtr import build_context
    ctx = build_context(ROOT / "fixtures/m8_path_eurusd.json")
    assert ctx.month8 is not None
    assert ctx.month8.ict_london_profile == "normal_protraction_sell"
    ctx9 = build_context(ROOT / "fixtures/m9_reconstruction_eurusd.json")
    # M9 tape may derive a month8 layer; candidates still reconstructed separately
    assert ctx9.profile in {"expansion", "consolidation", "reversal_watch", "continuation", "unclear"}



def test_month8_slice8_brief():
    from ftn.os.briefing import brief_from_fixture
    _, _, md, *_ = brief_from_fixture(ROOT / "fixtures/m8_path_eurusd.json")
    assert "## Month 8 (ICT day)" in md
    assert "normal_protraction_sell" in md
    assert "seed_only" in md
    assert "not a session ticket" in md



def test_month8_slice9_matrix():
    import json
    from ftn.os.m8_profile import derive_month8_profile
    from ftn.os.dtr import build_context
    for name, prof, gate in CASES_M8:
        raw = json.loads((ROOT / "fixtures" / name).read_text())
        raw.setdefault("pair_institutional", {})["state"] = raw.get("pair_institutional", {}).get("state") or "bearish"
        assert "pick" not in raw and "expected_winner" not in raw
        st = derive_month8_profile(raw)
        assert st.ict_london_profile == prof, name
        assert st.london_session_gate.allowed is gate
        ctx = build_context(ROOT / "fixtures" / name)
        assert ctx.month8 is not None
        assert ctx.month8.ict_london_profile == prof


def test_month8_engine_never_opens_gold():
    from pathlib import Path
    roots = [
        ROOT / "src/ftn/os/m8_contracts.py",
        ROOT / "src/ftn/os/m8_detect.py",
        ROOT / "src/ftn/os/m8_profile.py",
        ROOT / "src/ftn/os/m8_project.py",
        ROOT / "src/ftn/os/m8_htf.py",
        ROOT / "src/ftn/os/dtr.py",
        ROOT / "src/ftn/os/briefing.py",
    ]
    for path in roots:
        txt = path.read_text()
        assert ".expected.json" not in txt, path.name
        assert "m8_path_eurusd.expected" not in txt



def test_month7_slice1_schema():
    from ftn.os.contracts import load_day_context
    from ftn.os.m7_contracts import WEEKLY_PROFILES
    ctx = load_day_context(ROOT / "fixtures/m7_reconstruction_eurusd.json")
    assert ctx.month7 is not None
    assert ctx.month7.ict_weekly_profile.name == "classic_tuesday_low_of_week"
    assert ctx.month7.manipulation_template.name == "classic_tuesday_low_liquidity_pool"
    assert ctx.month7.osok_opportunity.flag is True
    assert ctx.month7.swing_ticket is None
    assert ctx.session_ticket is None
    ctx9 = load_day_context(ROOT / "fixtures/m9_reconstruction_eurusd.json")
    assert ctx9.month7 is None
    assert "classic_tuesday_low_of_week" in WEEKLY_PROFILES



def test_month7_slice2_range():
    import json
    from ftn.os.m7_range import derive_month7_range
    raw = json.loads((ROOT / "fixtures/m7_evidence_eurusd.json").read_text())
    st = derive_month7_range(raw)
    assert st.dealing_range.from_array_id == "M_DISCOUNT"
    assert st.dealing_range.to_array_id == "W_PREMIUM"
    assert st.dealing_range.direction == "bullish"
    assert st.ipda_window.days == 20
    assert st.ict_weekly_profile.name == "none"
    assert st.osok_opportunity.flag is False
    assert st.swing_ticket is None
    # known-state fixture still has a provided profile via parse, but slice 2 derive strips it
    raw2 = json.loads((ROOT / "fixtures/m7_reconstruction_eurusd.json").read_text())
    st2 = derive_month7_range(raw2)
    assert st2.ict_weekly_profile.name == "none"



def test_month7_slice3_profile():
    import json
    from ftn.os.m7_range import derive_month7_range
    from ftn.os.m7_profile import derive_month7_profile
    path = json.loads((ROOT / "fixtures/m7_path_eurusd.json").read_text())
    ev = json.loads((ROOT / "fixtures/m7_evidence_eurusd.json").read_text())
    assert derive_month7_range(path).ict_weekly_profile.name == "none"
    st = derive_month7_profile(path)
    assert st.ict_weekly_profile.name == "classic_tuesday_low_of_week"
    assert st.osok_opportunity.flag is False
    assert st.swing_ticket is None
    st2 = derive_month7_profile(ev)
    assert st2.ict_weekly_profile.name == "none"
    assert st2.dealing_range.from_array_id == "M_DISCOUNT"



def test_month7_slice4_template():
    import json
    from ftn.os.m7_profile import derive_month7_profile
    from ftn.os.m7_template import derive_month7_template
    path = json.loads((ROOT / "fixtures/m7_path_eurusd.json").read_text())
    st = derive_month7_template(path)
    assert st.ict_weekly_profile.name == "classic_tuesday_low_of_week"
    assert st.manipulation_template.name == "classic_tuesday_low_liquidity_pool"
    assert derive_month7_profile(path).manipulation_template.name == "none"
    ev = json.loads((ROOT / "fixtures/m7_evidence_eurusd.json").read_text())
    st2 = derive_month7_template(ev)
    assert st2.ict_weekly_profile.name == "none"
    assert st2.manipulation_template.name == "none"
    assert st.osok_opportunity.flag is False



def test_month7_slice5_lrlr():
    import json
    from ftn.os.m7_lrlr import derive_month7_lrlr
    path = json.loads((ROOT / "fixtures/m7_path_eurusd.json").read_text())
    st = derive_month7_lrlr(path)
    assert st.lrlr.state == "low"
    assert st.ict_weekly_profile.name == "classic_tuesday_low_of_week"
    assert st.osok_opportunity.flag is False
    high = json.loads(json.dumps(path))
    high["evidence"]["week_path"]["lrlr"] = "high"
    st_h = derive_month7_lrlr(high)
    assert st_h.lrlr.state == "high"
    assert st_h.osok_opportunity.flag is False
    ev = json.loads((ROOT / "fixtures/m7_evidence_eurusd.json").read_text())
    assert derive_month7_lrlr(ev).lrlr.state == "unclear"



def test_month7_slice6_osok():
    import json
    from ftn.os.m7_osok import derive_month7_osok
    path = json.loads((ROOT / "fixtures/m7_path_eurusd.json").read_text())
    st = derive_month7_osok(path)
    assert st.osok_opportunity.flag is True
    assert st.swing_ticket is None
    high = json.loads(json.dumps(path))
    high["evidence"]["week_path"]["lrlr"] = "high"
    assert derive_month7_osok(high).osok_opportunity.flag is False
    rev = json.loads(json.dumps(path))
    rev["evidence"]["week_path"]["contrary"] = "confirmed"
    assert derive_month7_osok(rev).osok_opportunity.flag is False
    ev = json.loads((ROOT / "fixtures/m7_evidence_eurusd.json").read_text())
    assert derive_month7_osok(ev).osok_opportunity.flag is False



def test_month7_slice7_swing():
    import json
    from ftn.os.m7_osok import derive_month7_osok
    from ftn.os.m7_swing import derive_month7_swing, path_for
    path = json.loads((ROOT / "fixtures/m7_path_eurusd.json").read_text())
    assert derive_month7_osok(path).swing_ticket is None
    dry = derive_month7_swing(path, persist=False)
    assert dry.osok_opportunity.flag is True
    assert dry.swing_ticket is None
    live = derive_month7_swing(path, persist=True)
    assert live.swing_ticket is not None
    assert live.swing_ticket.kind == "paper_swing"
    assert live.swing_ticket.module == "OSOK"
    assert live.swing_ticket.origin == "hermes_governance"
    again = derive_month7_swing(path, persist=True)
    assert again.swing_ticket.id == live.swing_ticket.id
    ev = json.loads((ROOT / "fixtures/m7_evidence_eurusd.json").read_text())
    st_ev = derive_month7_swing(ev, persist=True)
    assert st_ev.osok_opportunity.flag is False
    # evidence date differs so no collision required
    assert path_for("EURUSD", path["date"]).name.startswith("swing_")



def test_month7_slice8_dtr():
    from ftn.os.dtr import build_context
    ctx = build_context(ROOT / "fixtures/m7_path_eurusd.json")
    assert ctx.month7 is not None
    assert ctx.month7.ict_weekly_profile.name == "classic_tuesday_low_of_week"
    assert ctx.month7.osok_opportunity.flag is True
    assert ctx.session_ticket is None
    ctx9 = build_context(ROOT / "fixtures/m9_reconstruction_eurusd.json")
    assert ctx9.profile in {"expansion", "consolidation", "reversal_watch", "continuation", "unclear"}



def test_month7_slice9_brief():
    from ftn.os.briefing import brief_from_fixture
    _, _, md, *_ = brief_from_fixture(ROOT / "fixtures/m7_path_eurusd.json")
    assert "## Month 7 (ICT week)" in md
    assert "classic_tuesday_low_of_week" in md
    assert "not a session ticket" in md



def test_month7_slice10_matrix():
    import json
    from ftn.os.m7_osok import derive_month7_osok
    from ftn.os.dtr import build_context
    for name, prof, osok, lrlr in CASES_M7:
        raw = json.loads((ROOT / "fixtures" / name).read_text())
        assert "pick" not in raw and "expected_winner" not in raw
        st = derive_month7_osok(raw)
        assert st.ict_weekly_profile.name == prof, name
        assert st.osok_opportunity.flag is osok
        assert st.lrlr.state == lrlr
        ctx = build_context(ROOT / "fixtures" / name)
        assert ctx.month7 is not None
        assert ctx.month7.ict_weekly_profile.name == prof


def test_month7_engine_never_opens_gold():
    roots = [
        ROOT / "src/ftn/os/m7_contracts.py",
        ROOT / "src/ftn/os/m7_range.py",
        ROOT / "src/ftn/os/m7_profile.py",
        ROOT / "src/ftn/os/m7_template.py",
        ROOT / "src/ftn/os/m7_lrlr.py",
        ROOT / "src/ftn/os/m7_osok.py",
        ROOT / "src/ftn/os/m7_swing.py",
        ROOT / "src/ftn/os/dtr.py",
        ROOT / "src/ftn/os/briefing.py",
    ]
    for path in roots:
        txt = path.read_text()
        assert ".expected.json" not in txt, path.name



def test_month6_slice1_schema():
    from ftn.os.contracts import load_day_context
    from ftn.os.m6_contracts import MD_GATES, BULL_SEQUENCES
    ctx = load_day_context(ROOT / "fixtures/m6_reconstruction_xauusd.json")
    assert ctx.month6 is not None
    assert ctx.month6.swing_family == "bull"
    assert ctx.month6.sequential_pattern.name == "mw_bullish_daily_correcting"
    assert ctx.month6.million_dollar_swing.state == "incomplete"
    assert "management" in ctx.month6.million_dollar_swing.missing
    assert ctx.month6.swing_opportunity.flag is True
    assert ctx.session_ticket is None
    assert getattr(ctx, "month6")
    ctx9 = load_day_context(ROOT / "fixtures/m9_reconstruction_eurusd.json")
    assert ctx9.month6 is None
    assert len(MD_GATES) == 6
    assert "mwd_all_bullish" in BULL_SEQUENCES



def test_month6_slice2_env():
    import json
    from ftn.os.m6_env import derive_month6_env, htf_draw
    ev = json.loads((ROOT / "fixtures/m6_evidence_xauusd.json").read_text())
    st = derive_month6_env(ev)
    assert st.market_selection.state == "suitable"
    assert st.htf_draw == "bullish"
    assert htf_draw(ev) == "bullish"
    assert st.swing_family == "none"
    assert st.sequential_pattern.name == "none"
    assert st.swing_opportunity.flag is False
    raw = json.loads((ROOT / "fixtures/m6_reconstruction_xauusd.json").read_text())
    st2 = derive_month6_env(raw)
    assert st2.swing_family == "none"
    assert st2.sequential_pattern.name == "none"



def test_month6_slice3_evidence():
    import json
    from ftn.os.m6_evidence import derive_month6_evidence
    from ftn.os.m6_env import derive_month6_env
    ev = json.loads((ROOT / "fixtures/m6_evidence_xauusd.json").read_text())
    st = derive_month6_evidence(ev)
    assert st.supporting_evidence.htf_trend is True
    assert st.supporting_evidence.institutional_order_flow is True
    assert st.supporting_evidence.pd_arrays is True
    assert st.supporting_evidence.seasonal_tendency is True
    assert st.supporting_evidence.cot is False
    assert st.swing_family == "none"
    assert st.sequential_pattern.name == "none"
    assert st.million_dollar_swing.state == "none"
    assert st.swing_opportunity.flag is False
    assert derive_month6_env(ev).supporting_evidence.htf_trend is False



def test_month6_slice4_family():
    import json
    from ftn.os.m6_evidence import derive_month6_evidence
    from ftn.os.m6_family import derive_month6_family
    ev = json.loads((ROOT / "fixtures/m6_evidence_xauusd.json").read_text())
    assert derive_month6_evidence(ev).swing_family == "none"
    st = derive_month6_family(ev)
    assert st.swing_family == "bull"
    assert st.sequential_pattern.name == "mw_bullish_daily_correcting"
    assert st.million_dollar_swing.state == "none"
    assert st.swing_opportunity.flag is False
    bear = json.loads(json.dumps(ev))
    bear["pair_institutional"]["sponsorship"] = {
        "monthly": "bearish", "weekly": "bearish", "daily": "bullish"
    }
    st_b = derive_month6_family(bear)
    assert st_b.swing_family == "bear"
    assert st_b.sequential_pattern.name == "mw_bearish_daily_correcting"
    allb = json.loads(json.dumps(ev))
    allb["pair_institutional"]["sponsorship"]["daily"] = "bullish"
    assert derive_month6_family(allb).sequential_pattern.name == "mwd_all_bullish"
    unclear_d = json.loads(json.dumps(ev))
    unclear_d["pair_institutional"]["sponsorship"]["daily"] = "unclear"
    st_u = derive_month6_family(unclear_d)
    assert st_u.swing_family == "none"
    assert st_u.sequential_pattern.name == "none"
    unclear_w = json.loads(json.dumps(ev))
    unclear_w["pair_institutional"]["sponsorship"]["weekly"] = "unclear"
    st_w = derive_month6_family(unclear_w)
    assert st_w.swing_family == "none"
    assert st_w.sequential_pattern.name == "none"



def test_month6_slice5_risk():
    import json
    from ftn.os.m6_family import derive_month6_family
    from ftn.os.m6_risk import derive_month6_risk
    ev = json.loads((ROOT / "fixtures/m6_evidence_xauusd.json").read_text())
    st = derive_month6_risk(ev)
    assert st.risk_frame.stop_reference == "M_OB_bull"
    assert st.risk_frame.target_reference == "W_PREMIUM"
    assert st.risk_frame.reward_frame == "discount_to_premium"
    assert st.swing_opportunity.flag is False
    assert st.million_dollar_swing.state == "none"
    assert derive_month6_family(ev).risk_frame.stop_reference is None



def test_month6_slice6_md():
    import json
    from ftn.os.m6_risk import derive_month6_risk
    from ftn.os.m6_md import derive_month6_md
    ev = json.loads((ROOT / "fixtures/m6_evidence_xauusd.json").read_text())
    st = derive_month6_md(ev)
    assert st.swing_family == "bull"
    assert st.million_dollar_swing.state == "incomplete"
    assert "management" in st.million_dollar_swing.missing
    assert "major_market_analysis" in st.million_dollar_swing.missing
    assert st.swing_opportunity.flag is False
    assert derive_month6_risk(ev).million_dollar_swing.state == "none"
    full = json.loads(json.dumps(ev))
    full["ipda_days"] = 20
    full["evidence"]["million_dollar"] = {
        "major_market_analysis": True,
        "intermarket_analysis": True,
        "top_down_analysis": True,
        "management": True,
    }
    assembled = derive_month6_md(full)
    assert assembled.million_dollar_swing.state == "assembled"
    assert assembled.million_dollar_swing.missing == ()
    assert assembled.swing_opportunity.flag is False



def test_month6_slice7_opportunity():
    import json
    from ftn.os.m6_md import derive_month6_md
    from ftn.os.m6_opportunity import derive_month6
    ev = json.loads((ROOT / "fixtures/m6_evidence_xauusd.json").read_text())
    assert derive_month6_md(ev).swing_opportunity.flag is False
    st = derive_month6(ev)
    assert st.swing_opportunity.flag is True
    assert st.million_dollar_swing.state == "incomplete"
    assert "md_assembled" not in st.swing_opportunity.reason
    unsuit = json.loads(json.dumps(ev))
    unsuit["pair_institutional"]["sponsorship"] = {}
    unsuit["pair_institutional"]["state"] = "unclear"
    unsuit.pop("origin_pd_array", None)
    st_u = derive_month6(unsuit)
    assert st_u.swing_opportunity.flag is False



def test_month6_slice8_dtr():
    from ftn.os.dtr import build_context
    ctx = build_context(ROOT / "fixtures/m6_evidence_xauusd.json")
    assert ctx.month6 is not None
    assert ctx.month6.swing_family == "bull"
    assert ctx.month6.swing_opportunity.flag is True
    assert ctx.session_ticket is None
    ctx9 = build_context(ROOT / "fixtures/m9_reconstruction_eurusd.json")
    assert ctx9.profile in {"expansion", "consolidation", "reversal_watch", "continuation", "unclear"}



def test_month6_slice9_brief():
    from ftn.os.briefing import brief_from_fixture
    _, _, md, *_ = brief_from_fixture(ROOT / "fixtures/m6_evidence_xauusd.json")
    assert "## Month 6 (ICT swing)" in md
    assert "mw_bullish_daily_correcting" in md
    assert "not a session ticket" in md



def test_month6_slice10_matrix():
    import json
    from ftn.os.m6_opportunity import derive_month6
    from ftn.os.dtr import build_context
    for name, fam, seq, opp, md in CASES_M6:
        raw = json.loads((ROOT / "fixtures" / name).read_text())
        assert "pick" not in raw and "expected_winner" not in raw
        st = derive_month6(raw)
        assert st.swing_family == fam
        assert st.sequential_pattern.name == seq
        assert st.swing_opportunity.flag is opp
        assert st.million_dollar_swing.state == md
        ctx = build_context(ROOT / "fixtures" / name)
        assert ctx.month6 is not None
        assert ctx.month6.swing_family == fam
        assert ctx.month6.sequential_pattern.name == seq


def test_month6_engine_never_opens_gold():
    roots = [
        ROOT / "src/ftn/os/m6_contracts.py",
        ROOT / "src/ftn/os/m6_env.py",
        ROOT / "src/ftn/os/m6_evidence.py",
        ROOT / "src/ftn/os/m6_family.py",
        ROOT / "src/ftn/os/m6_risk.py",
        ROOT / "src/ftn/os/m6_md.py",
        ROOT / "src/ftn/os/m6_opportunity.py",
        ROOT / "src/ftn/os/dtr.py",
        ROOT / "src/ftn/os/briefing.py",
    ]
    for path in roots:
        txt = path.read_text()
        assert ".expected.json" not in txt, path.name



def test_month5_slice1_schema():
    from ftn.os.contracts import load_day_context
    ctx = load_day_context(ROOT / "fixtures/m5_reconstruction_eurusd.json")
    assert ctx.month5 is not None
    assert ctx.month5.quarterly_shift.state == "in_progress"
    assert ctx.month5.ipda_window.days == 60
    assert ctx.month5.institutional_swing.kind == "breaker_swing_point"
    assert ctx.month5.open_float.buy_side == "present"
    assert ctx.month5.position_opportunity.flag is True
    assert ctx.session_ticket is None
    ctx9 = load_day_context(ROOT / "fixtures/m9_reconstruction_eurusd.json")
    assert ctx9.month5 is None



def test_month5_slice2_env():
    import json
    from ftn.os.m5_env import derive_month5_env
    ev = json.loads((ROOT / "fixtures/m5_evidence_eurusd.json").read_text())
    st = derive_month5_env(ev)
    assert st.quarterly_shift.state == "in_progress"
    assert st.quarterly_shift.lookback_months == 3
    assert st.ipda_window.days == 60
    assert st.institutional_swing.kind == "none"
    assert st.position_opportunity.flag is False
    raw = json.loads((ROOT / "fixtures/m5_reconstruction_eurusd.json").read_text())
    st2 = derive_month5_env(raw)
    assert st2.position_opportunity.flag is False
    assert st2.institutional_swing.kind == "none"
    src = Path(ROOT / "src/ftn/os/m5_env.py").read_text()
    assert 'raw.get("month7")' not in src



def test_month5_slice3_float():
    import json
    from ftn.os.m5_env import derive_month5_env
    from ftn.os.m5_float import derive_month5_float
    ev = json.loads((ROOT / "fixtures/m5_evidence_eurusd.json").read_text())
    env = derive_month5_env(ev)
    assert env.open_float.buy_side == "unclear"
    assert env.open_float_pools.pool_ids == ()
    st = derive_month5_float(ev)
    assert st.open_float.buy_side == "present"
    assert st.open_float.sell_side == "absent"
    assert st.open_float_pools.pool_ids == ("IPDA60L",)
    assert st.institutional_swing.kind == "none"
    assert st.position_opportunity.flag is False



def test_month5_slice4_swing():
    import json
    from ftn.os.m5_float import derive_month5_float
    from ftn.os.m5_swing import derive_month5_swing
    ev = json.loads((ROOT / "fixtures/m5_evidence_eurusd.json").read_text())
    assert derive_month5_float(ev).institutional_swing.kind == "none"
    st = derive_month5_swing(ev)
    assert st.institutional_swing.kind == "breaker_swing_point"
    assert st.institutional_swing.entry_annotation == "turtle_soup"
    assert st.position_opportunity.flag is False
    fail = json.loads(json.dumps(ev))
    fail["evidence"]["institutional_swing"] = {"kind": "failure_swing"}
    assert derive_month5_swing(fail).institutional_swing.kind == "failure_swing"
    bad = json.loads(json.dumps(ev))
    bad["evidence"]["institutional_swing"] = {"kind": "choch"}
    assert derive_month5_swing(bad).institutional_swing.kind == "none"



def test_month5_slice5_confirm():
    import json
    from ftn.os.m5_swing import derive_month5_swing
    from ftn.os.m5_confirm import derive_month5_confirm
    ev = json.loads((ROOT / "fixtures/m5_evidence_eurusd.json").read_text())
    assert derive_month5_swing(ev).confirming.seasonal_tendency == "none"
    st = derive_month5_confirm(ev)
    assert st.confirming.seasonal_tendency == "bullish"
    assert st.confirming.intermarket is True
    assert st.confirming.ten_year_notes is False
    assert st.position_opportunity.flag is False



def test_month5_slice6_pd():
    import json
    from ftn.os.m5_confirm import derive_month5_confirm
    from ftn.os.m5_pd import derive_month5_pd
    ev = json.loads((ROOT / "fixtures/m5_evidence_eurusd.json").read_text())
    assert derive_month5_confirm(ev).htf_pd.dealing_range_tf == "none"
    st = derive_month5_pd(ev)
    assert st.htf_pd.dealing_range_tf == "monthly"
    assert st.htf_pd.nearest_discount_id == "M_OB_bull"
    assert st.htf_pd.nearest_premium_id == "M_OH"
    assert st.position_opportunity.flag is False
    src = (ROOT / "src/ftn/os/m5_pd.py").read_text()
    assert "mitigation" not in src.lower()



def test_month5_slice7_setup():
    import json
    from ftn.os.m5_pd import derive_month5_pd
    from ftn.os.m5_setup import derive_month5_setup
    ev = json.loads((ROOT / "fixtures/m5_evidence_eurusd.json").read_text())
    assert derive_month5_pd(ev).setup_progression == "none"
    st = derive_month5_setup(ev)
    assert st.setup_progression == "watching"
    assert st.entry_technique == "limit"
    assert st.position_management == "none"
    assert st.position_opportunity.flag is False



def test_month5_slice8_opportunity():
    import json
    from ftn.os.m5_setup import derive_month5_setup
    from ftn.os.m5_opportunity import derive_month5
    ev = json.loads((ROOT / "fixtures/m5_evidence_eurusd.json").read_text())
    assert derive_month5_setup(ev).position_opportunity.flag is False
    st = derive_month5(ev)
    assert st.position_opportunity.flag is True
    assert st.confirming.ten_year_notes is False
    missing = json.loads(json.dumps(ev))
    missing["evidence"].pop("htf_pd")
    missing.pop("origin_pd_array", None)
    assert derive_month5(missing).position_opportunity.flag is False



def test_month5_slice9_dtr_brief():
    from ftn.os.dtr import build_context
    from ftn.os.briefing import brief_from_fixture
    ctx = build_context(ROOT / "fixtures/m5_evidence_eurusd.json")
    assert ctx.month5 is not None
    assert ctx.month5.position_opportunity.flag is True
    assert ctx.session_ticket is None
    _, _, md, *_ = brief_from_fixture(ROOT / "fixtures/m5_evidence_eurusd.json")
    assert "## Month 5 (ICT position)" in md
    assert "not a session ticket" in md
    ctx9 = build_context(ROOT / "fixtures/m9_reconstruction_eurusd.json")
    assert ctx9.profile in {"expansion", "consolidation", "reversal_watch", "continuation", "unclear"}



def test_month5_slice10_matrix():
    import json
    from ftn.os.m5_opportunity import derive_month5
    from ftn.os.dtr import build_context
    for name, qs, days, swing, opp in CASES_M5:
        raw = json.loads((ROOT / "fixtures" / name).read_text())
        assert "pick" not in raw and "expected_winner" not in raw
        st = derive_month5(raw)
        assert st.quarterly_shift.state == qs
        assert st.ipda_window.days == days
        assert st.institutional_swing.kind == swing
        assert st.position_opportunity.flag is opp
        ctx = build_context(ROOT / "fixtures" / name)
        assert ctx.month5 is not None
        assert ctx.month5.quarterly_shift.state == qs
        assert ctx.month5.institutional_swing.kind == swing
        assert ctx.month5.position_opportunity.flag is opp
        assert ctx.session_ticket is None


def test_month5_engine_never_opens_gold():
    roots = [
        ROOT / "src/ftn/os/m5_contracts.py",
        ROOT / "src/ftn/os/m5_env.py",
        ROOT / "src/ftn/os/m5_float.py",
        ROOT / "src/ftn/os/m5_swing.py",
        ROOT / "src/ftn/os/m5_confirm.py",
        ROOT / "src/ftn/os/m5_pd.py",
        ROOT / "src/ftn/os/m5_setup.py",
        ROOT / "src/ftn/os/m5_opportunity.py",
        ROOT / "src/ftn/os/dtr.py",
        ROOT / "src/ftn/os/briefing.py",
    ]
    for path in roots:
        txt = path.read_text()
        assert ".expected.json" not in txt, path.name



def test_month4_slice1_schema():
    from ftn.os.contracts import load_day_context
    ctx = load_day_context(ROOT / "fixtures/m4_reconstruction_eurusd.json")
    assert ctx.month4 is not None
    assert len(ctx.month4.arrays) == 2
    assert ctx.month4.arrays[0].kind == "fvg"
    assert ctx.month4.arrays[1].kind == "liquidity_void"
    assert ctx.month4.pattern_note == "double_bottom"
    assert ctx.month4.array_opportunity.flag is True
    assert ctx.session_ticket is None
    ctx9 = load_day_context(ROOT / "fixtures/m9_reconstruction_eurusd.json")
    assert ctx9.month4 is None



def test_month4_slice2_catalog():
    import json
    from ftn.os.m4_catalog import derive_month4_catalog
    ev = json.loads((ROOT / "fixtures/m4_evidence_eurusd.json").read_text())
    st = derive_month4_catalog(ev)
    assert [a.kind for a in st.arrays] == ["fvg", "liquidity_void"]
    assert st.pattern_note == "double_bottom"
    assert st.interest_rate_effects is False
    assert st.array_opportunity.flag is False
    raw = json.loads((ROOT / "fixtures/m4_reconstruction_eurusd.json").read_text())
    st2 = derive_month4_catalog(raw)
    assert st2.array_opportunity.flag is False
    bad = json.loads(json.dumps(ev))
    bad["evidence"]["arrays"].append({"kind": "choch", "polarity": "bullish"})
    st3 = derive_month4_catalog(bad)
    assert st3.arrays[-1].kind == "none"
    src = (ROOT / "src/ftn/os/m4_catalog.py").read_text()
    assert 'raw.get("month5")' not in src
    assert 'raw.get("month7")' not in src



def test_month4_slice3_opportunity():
    import json
    from ftn.os.m4_catalog import derive_month4_catalog
    from ftn.os.m4_opportunity import derive_month4
    ev = json.loads((ROOT / "fixtures/m4_evidence_eurusd.json").read_text())
    assert derive_month4_catalog(ev).array_opportunity.flag is False
    st = derive_month4(ev)
    assert st.array_opportunity.flag is True
    assert st.interest_rate_effects is False
    nonep = json.loads(json.dumps(ev))
    for a in nonep["evidence"]["arrays"]:
        a["polarity"] = "none"
    assert derive_month4(nonep).array_opportunity.flag is False
    empty = json.loads(json.dumps(ev))
    empty["evidence"]["arrays"] = [{"kind": "choch", "polarity": "bullish"}]
    assert derive_month4(empty).array_opportunity.flag is False



def test_month4_slice4_dtr():
    from ftn.os.dtr import build_context
    ctx = build_context(ROOT / "fixtures/m4_evidence_eurusd.json")
    assert ctx.month4 is not None
    assert [a.kind for a in ctx.month4.arrays] == ["fvg", "liquidity_void"]
    assert ctx.month4.array_opportunity.flag is True
    assert ctx.session_ticket is None
    ctx9 = build_context(ROOT / "fixtures/m9_reconstruction_eurusd.json")
    assert ctx9.month4 is None or ctx9.month4.arrays == ()



def test_month4_slice5_brief():
    from ftn.os.briefing import brief_from_fixture
    _, _, md, *_ = brief_from_fixture(ROOT / "fixtures/m4_evidence_eurusd.json")
    assert "## Month 4 (ICT arrays)" in md
    assert "fvg" in md and "liquidity_void" in md
    assert "not a session ticket" in md
    assert "does not select an M9 candidate" in md



def test_month4_slice6_matrix():
    import json
    from ftn.os.m4_opportunity import derive_month4
    from ftn.os.dtr import build_context
    for name, kinds, note, opp in CASES_M4:
        raw = json.loads((ROOT / "fixtures" / name).read_text())
        assert "pick" not in raw and "expected_winner" not in raw
        st = derive_month4(raw)
        assert tuple(a.kind for a in st.arrays) == kinds
        assert st.pattern_note == note
        assert st.array_opportunity.flag is opp
        ctx = build_context(ROOT / "fixtures" / name)
        assert ctx.month4 is not None
        assert tuple(a.kind for a in ctx.month4.arrays) == kinds
        assert ctx.month4.array_opportunity.flag is opp
        assert ctx.session_ticket is None


def test_month4_engine_never_opens_gold():
    roots = [
        ROOT / "src/ftn/os/m4_contracts.py",
        ROOT / "src/ftn/os/m4_catalog.py",
        ROOT / "src/ftn/os/m4_opportunity.py",
        ROOT / "src/ftn/os/dtr.py",
        ROOT / "src/ftn/os/briefing.py",
    ]
    for path in roots:
        txt = path.read_text()
        assert ".expected.json" not in txt, path.name



def test_month3_slice1_schema():
    from ftn.os.contracts import load_day_context
    ctx = load_day_context(ROOT / "fixtures/m3_reconstruction_eurusd.json")
    assert ctx.month3 is not None
    assert ctx.month3.selected_timeframe == "monthly"
    assert ctx.month3.anticipated_setup == "present"
    assert ctx.month3.next_setup.flag is True
    assert ctx.session_ticket is None
    ctx9 = load_day_context(ROOT / "fixtures/m9_reconstruction_eurusd.json")
    assert ctx9.month3 is None



def test_month3_slice2_context():
    import json
    from ftn.os.m3_context import derive_month3_context
    ev = json.loads((ROOT / "fixtures/m3_evidence_eurusd.json").read_text())
    st = derive_month3_context(ev)
    assert st.selected_timeframe == "monthly"
    assert st.institutional_order_flow == "bullish"
    assert st.anticipated_setup == "present"
    assert st.next_setup.flag is False
    raw = json.loads((ROOT / "fixtures/m3_reconstruction_eurusd.json").read_text())
    assert derive_month3_context(raw).next_setup.flag is False
    noant = json.loads(json.dumps(ev))
    noant["evidence"]["anticipated_setup"] = "none"
    st2 = derive_month3_context(noant)
    assert st2.anticipated_setup == "none"
    assert st2.next_setup.flag is False
    src = (ROOT / "src/ftn/os/m3_context.py").read_text()
    assert "pair_institutional =" not in src and '.pair_institutional' not in src
    assert 'raw.get("month4")' not in src



def test_month3_slice3_setup():
    import json
    from ftn.os.m3_context import derive_month3_context
    from ftn.os.m3_setup import derive_month3
    ev = json.loads((ROOT / "fixtures/m3_evidence_eurusd.json").read_text())
    assert derive_month3_context(ev).next_setup.flag is False
    st = derive_month3(ev)
    assert st.next_setup.flag is True
    noant = json.loads(json.dumps(ev))
    noant["evidence"]["anticipated_setup"] = "none"
    st2 = derive_month3(noant)
    assert st2.institutional_order_flow == "bullish"
    assert st2.next_setup.flag is False
    notf = json.loads(json.dumps(ev))
    notf["evidence"]["selected_timeframe"] = "none"
    assert derive_month3(notf).next_setup.flag is False



def test_month3_slice4_dtr():
    from ftn.os.dtr import build_context
    ctx = build_context(ROOT / "fixtures/m3_evidence_eurusd.json")
    assert ctx.month3 is not None
    assert ctx.month3.next_setup.flag is True
    assert ctx.session_ticket is None
    ctx9 = build_context(ROOT / "fixtures/m9_reconstruction_eurusd.json")
    assert ctx9.month3 is None



def test_month3_slice5_brief():
    from ftn.os.briefing import brief_from_fixture
    _, _, md, *_ = brief_from_fixture(ROOT / "fixtures/m3_evidence_eurusd.json")
    assert "## Month 3 (ICT next setup)" in md
    assert "Anticipated setup" in md
    assert "not a session ticket" in md
    assert "does not select an M9 candidate" in md



def test_month3_slice6_matrix():
    import json
    from ftn.os.m3_setup import derive_month3
    from ftn.os.dtr import build_context
    for name, tf, ant, nxt in CASES_M3:
        raw = json.loads((ROOT / "fixtures" / name).read_text())
        assert "pick" not in raw and "expected_winner" not in raw
        st = derive_month3(raw)
        assert st.selected_timeframe == tf
        assert st.anticipated_setup == ant
        assert st.next_setup.flag is nxt
        ctx = build_context(ROOT / "fixtures" / name)
        assert ctx.month3 is not None
        assert ctx.month3.next_setup.flag is nxt
        assert ctx.session_ticket is None


def test_month3_engine_never_opens_gold():
    roots = [
        ROOT / "src/ftn/os/m3_contracts.py",
        ROOT / "src/ftn/os/m3_context.py",
        ROOT / "src/ftn/os/m3_setup.py",
        ROOT / "src/ftn/os/dtr.py",
        ROOT / "src/ftn/os/briefing.py",
    ]
    for path in roots:
        txt = path.read_text()
        assert ".expected.json" not in txt, path.name



def test_month2_slice1_schema():
    from ftn.os.contracts import load_day_context
    ctx = load_day_context(ROOT / "fixtures/m2_reconstruction_eurusd.json")
    assert ctx.month2 is not None
    assert ctx.month2.identified_low_risk_frame == "present"
    assert ctx.month2.low_risk_frame.flag is True
    assert ctx.session_ticket is None
    ctx9 = load_day_context(ROOT / "fixtures/m9_reconstruction_eurusd.json")
    assert ctx9.month2 is None



def test_month2_slice2_context():
    import json
    from ftn.os.m2_context import derive_month2_context
    ev = json.loads((ROOT / "fixtures/m2_evidence_eurusd.json").read_text())
    st = derive_month2_context(ev)
    assert st.identified_low_risk_frame == "present"
    assert st.identified_high_reward_context == "present"
    assert st.low_risk_frame.flag is False
    raw = json.loads((ROOT / "fixtures/m2_reconstruction_eurusd.json").read_text())
    assert derive_month2_context(raw).low_risk_frame.flag is False
    one = json.loads(json.dumps(ev))
    one["evidence"]["identified_high_reward_context"] = "none"
    st2 = derive_month2_context(one)
    assert st2.identified_high_reward_context == "none"
    assert st2.low_risk_frame.flag is False
    src = (ROOT / "src/ftn/os/m2_context.py").read_text()
    assert "from ftn.os.m6" not in src
    assert 'raw.get("month6")' not in src



def test_month2_slice3_frame():
    import json
    from ftn.os.m2_context import derive_month2_context
    from ftn.os.m2_frame import derive_month2
    ev = json.loads((ROOT / "fixtures/m2_evidence_eurusd.json").read_text())
    assert derive_month2_context(ev).low_risk_frame.flag is False
    st = derive_month2(ev)
    assert st.low_risk_frame.flag is True
    one = json.loads(json.dumps(ev))
    one["evidence"]["identified_high_reward_context"] = "none"
    assert derive_month2(one).low_risk_frame.flag is False
    assert derive_month2(one).small_account_posture == "present"



def test_month2_slice4_dtr():
    from ftn.os.dtr import build_context
    ctx = build_context(ROOT / "fixtures/m2_evidence_eurusd.json")
    assert ctx.month2 is not None
    assert ctx.month2.low_risk_frame.flag is True
    assert ctx.session_ticket is None
    ctx9 = build_context(ROOT / "fixtures/m9_reconstruction_eurusd.json")
    assert ctx9.month2 is None



def test_month2_slice5_brief():
    from ftn.os.briefing import brief_from_fixture
    _, _, md, *_ = brief_from_fixture(ROOT / "fixtures/m2_evidence_eurusd.json")
    assert "## Month 2 (ICT risk frame)" in md
    assert "not a session ticket" in md
    assert "does not select an M9 candidate" in md



def test_month2_slice6_matrix():
    import json
    from ftn.os.m2_frame import derive_month2
    from ftn.os.dtr import build_context
    for name, lo, hi, flag in CASES_M2:
        raw = json.loads((ROOT / "fixtures" / name).read_text())
        assert "pick" not in raw and "expected_winner" not in raw
        st = derive_month2(raw)
        assert st.identified_low_risk_frame == lo
        assert st.identified_high_reward_context == hi
        assert st.low_risk_frame.flag is flag
        ctx = build_context(ROOT / "fixtures" / name)
        assert ctx.month2 is not None
        assert ctx.month2.low_risk_frame.flag is flag
        assert ctx.session_ticket is None


def test_month2_engine_never_opens_gold():
    roots = [
        ROOT / "src/ftn/os/m2_contracts.py",
        ROOT / "src/ftn/os/m2_context.py",
        ROOT / "src/ftn/os/m2_frame.py",
        ROOT / "src/ftn/os/dtr.py",
        ROOT / "src/ftn/os/briefing.py",
    ]
    for path in roots:
        txt = path.read_text()
        assert ".expected.json" not in txt, path.name



def test_month1_slice1_schema():
    from ftn.os.contracts import load_day_context
    ctx = load_day_context(ROOT / "fixtures/m1_reconstruction_eurusd.json")
    assert ctx.month1 is not None
    assert ctx.month1.identified_setup_elements == "present"
    assert ctx.month1.dealing_range_side == "discount"
    assert ctx.month1.setup_elements.flag is True
    assert ctx.session_ticket is None
    ctx9 = load_day_context(ROOT / "fixtures/m9_reconstruction_eurusd.json")
    assert ctx9.month1 is None



def test_month1_slice2_context():
    import json
    from ftn.os.m1_context import derive_month1_context
    ev = json.loads((ROOT / "fixtures/m1_evidence_eurusd.json").read_text())
    st = derive_month1_context(ev)
    assert st.identified_setup_elements == "present"
    assert st.dealing_range_side == "discount"
    assert st.setup_elements.flag is False
    raw = json.loads((ROOT / "fixtures/m1_reconstruction_eurusd.json").read_text())
    assert derive_month1_context(raw).setup_elements.flag is False
    noneid = json.loads(json.dumps(ev))
    noneid["evidence"]["identified_setup_elements"] = "none"
    st2 = derive_month1_context(noneid)
    assert st2.identified_setup_elements == "none"
    assert st2.setup_elements.flag is False
    src = (ROOT / "src/ftn/os/m1_context.py").read_text()
    assert "liquidity_probe =" not in src and ".liquidity_probe" not in src
    assert 'raw.get("month4")' not in src
    assert 'raw.get("month5")' not in src



def test_month1_slice3_setup():
    import json
    from ftn.os.m1_context import derive_month1_context
    from ftn.os.m1_setup import derive_month1
    ev = json.loads((ROOT / "fixtures/m1_evidence_eurusd.json").read_text())
    assert derive_month1_context(ev).setup_elements.flag is False
    st = derive_month1(ev)
    assert st.setup_elements.flag is True
    noneid = json.loads(json.dumps(ev))
    noneid["evidence"]["identified_setup_elements"] = "none"
    st2 = derive_month1(noneid)
    assert st2.dealing_range_side == "discount"
    assert st2.liquidity_run_note == "present"
    assert st2.setup_elements.flag is False



def test_month1_slice4_dtr():
    from ftn.os.dtr import build_context
    ctx = build_context(ROOT / "fixtures/m1_evidence_eurusd.json")
    assert ctx.month1 is not None
    assert ctx.month1.setup_elements.flag is True
    assert ctx.session_ticket is None
    ctx9 = build_context(ROOT / "fixtures/m9_reconstruction_eurusd.json")
    assert ctx9.month1 is None



def test_month1_slice5_brief():
    from ftn.os.briefing import brief_from_fixture
    _, _, md, *_ = brief_from_fixture(ROOT / "fixtures/m1_evidence_eurusd.json")
    assert "## Month 1 (ICT foundation)" in md
    assert "not a session ticket" in md
    assert "does not select an M9 candidate" in md



def test_month1_slice6_matrix():
    import json
    from ftn.os.m1_setup import derive_month1
    from ftn.os.dtr import build_context
    for name, ident, side, flag in CASES_M1:
        raw = json.loads((ROOT / "fixtures" / name).read_text())
        assert "pick" not in raw and "expected_winner" not in raw
        st = derive_month1(raw)
        assert st.identified_setup_elements == ident
        assert st.dealing_range_side == side
        assert st.setup_elements.flag is flag
        ctx = build_context(ROOT / "fixtures" / name)
        assert ctx.month1 is not None
        assert ctx.month1.setup_elements.flag is flag
        assert ctx.session_ticket is None


def test_month1_engine_never_opens_gold():
    roots = [
        ROOT / "src/ftn/os/m1_contracts.py",
        ROOT / "src/ftn/os/m1_context.py",
        ROOT / "src/ftn/os/m1_setup.py",
        ROOT / "src/ftn/os/dtr.py",
        ROOT / "src/ftn/os/briefing.py",
    ]
    for path in roots:
        txt = path.read_text()
        assert ".expected.json" not in txt, path.name



def test_integration_i2_attach():
    from ftn.os.dtr import build_context
    ctx = build_context(ROOT / "fixtures/integration_m1_m9_eurusd.json")
    assert ctx.month1 is not None
    assert ctx.month2 is not None
    assert ctx.month3 is not None
    assert ctx.month4 is not None
    assert ctx.month5 is not None
    assert ctx.month6 is not None
    assert ctx.month7 is not None
    assert ctx.month8 is not None
    assert ctx.month1.setup_elements.flag is True
    assert ctx.month2.low_risk_frame.flag is True
    assert ctx.month3.next_setup.flag is True
    assert ctx.month4.array_opportunity.flag is True


def test_integration_i3_ticket_isolation():
    import json
    from ftn.os.dtr import build_context
    ctx = build_context(ROOT / "fixtures/integration_m1_m9_eurusd.json")
    assert ctx.session_ticket is None
    payload = json.loads((ROOT / "fixtures/integration_m1_m9_eurusd.json").read_text())
    assert "pick" not in payload and "expected_winner" not in payload


def test_integration_i4_brief():
    from ftn.os.briefing import brief_from_fixture
    _, _, md, *_ = brief_from_fixture(ROOT / "fixtures/integration_m1_m9_eurusd.json")
    for h in (
        "## Month 1 (ICT foundation)",
        "## Month 2 (ICT risk frame)",
        "## Month 3 (ICT next setup)",
        "## Month 4 (ICT arrays)",
        "## Month 5 (ICT position)",
        "## Month 6 (ICT swing)",
        "## Month 7 (ICT week)",
        "## Month 8 (ICT day)",
    ):
        assert h in md, h
    i1 = md.find("## Month 1")
    i9 = md.find("## Candidate")
    assert 0 <= i1 < i9


def test_integration_i5_golds():
    test_reconstruct_matches_gold()
    test_month1_slice6_matrix()
    test_month2_slice6_matrix()
    test_month3_slice6_matrix()
    test_month4_slice6_matrix()



def test_month10_slice1_schema():
    from ftn.os.contracts import load_day_context
    ctx = load_day_context(ROOT / "fixtures/m10_reconstruction_eurusd.json")
    assert ctx.month10 is not None
    assert ctx.month10.identified_multi_asset == "present"
    assert ctx.month10.asset_class == "index"
    assert ctx.month10.multi_asset_context.flag is True
    assert ctx.session_ticket is None
    ctx9 = load_day_context(ROOT / "fixtures/m9_reconstruction_eurusd.json")
    assert ctx9.month10 is None



def test_month10_slice2_context():
    import json
    from ftn.os.m10_context import derive_month10_context
    ev = json.loads((ROOT / "fixtures/m10_evidence_eurusd.json").read_text())
    st = derive_month10_context(ev)
    assert st.identified_multi_asset == "present"
    assert st.cot_reading == "bullish"
    assert st.asset_class == "index"
    assert st.multi_asset_context.flag is False
    raw = json.loads((ROOT / "fixtures/m10_reconstruction_eurusd.json").read_text())
    assert derive_month10_context(raw).multi_asset_context.flag is False
    noneid = json.loads(json.dumps(ev))
    noneid["evidence"]["identified_multi_asset"] = "none"
    st2 = derive_month10_context(noneid)
    assert st2.identified_multi_asset == "none"
    assert st2.multi_asset_context.flag is False
    src = (ROOT / "src/ftn/os/m10_context.py").read_text()
    assert 'raw.get("month5")' not in src
    assert 'raw.get("month6")' not in src



def test_month10_slice3_flag():
    import json
    from ftn.os.m10_context import derive_month10_context
    from ftn.os.m10_confluence import derive_month10
    ev = json.loads((ROOT / "fixtures/m10_evidence_eurusd.json").read_text())
    assert derive_month10_context(ev).multi_asset_context.flag is False
    st = derive_month10(ev)
    assert st.multi_asset_context.flag is True
    noneid = json.loads(json.dumps(ev))
    noneid["evidence"]["identified_multi_asset"] = "none"
    st2 = derive_month10(noneid)
    assert st2.cot_reading == "bullish"
    assert st2.asset_class == "index"
    assert st2.multi_asset_context.flag is False



def test_month10_slice4_dtr():
    from ftn.os.dtr import build_context
    ctx = build_context(ROOT / "fixtures/m10_evidence_eurusd.json")
    assert ctx.month10 is not None
    assert ctx.month10.multi_asset_context.flag is True
    assert ctx.session_ticket is None
    ctx9 = build_context(ROOT / "fixtures/m9_reconstruction_eurusd.json")
    assert ctx9.month10 is None



def test_month10_slice5_brief():
    from ftn.os.briefing import brief_from_fixture
    _, _, md, *_ = brief_from_fixture(ROOT / "fixtures/m10_evidence_eurusd.json")
    assert "## Month 10 (ICT multi-asset)" in md
    assert "not a session ticket" in md
    assert "does not select an M9 candidate" in md



def test_month10_slice6_matrix():
    import json
    from ftn.os.m10_confluence import derive_month10
    from ftn.os.dtr import build_context
    for name, ident, asset, flag in CASES_M10:
        raw = json.loads((ROOT / "fixtures" / name).read_text())
        assert "pick" not in raw and "expected_winner" not in raw
        st = derive_month10(raw)
        assert st.identified_multi_asset == ident
        assert st.asset_class == asset
        assert st.multi_asset_context.flag is flag
        ctx = build_context(ROOT / "fixtures" / name)
        assert ctx.month10 is not None
        assert ctx.month10.multi_asset_context.flag is flag
        assert ctx.session_ticket is None


def test_month10_engine_never_opens_gold():
    roots = [
        ROOT / "src/ftn/os/m10_contracts.py",
        ROOT / "src/ftn/os/m10_context.py",
        ROOT / "src/ftn/os/m10_confluence.py",
        ROOT / "src/ftn/os/dtr.py",
        ROOT / "src/ftn/os/briefing.py",
    ]
    for path in roots:
        txt = path.read_text()
        assert ".expected.json" not in txt, path.name



def test_month11_slice1_schema():
    from ftn.os.contracts import load_day_context
    ctx = load_day_context(ROOT / "fixtures/m11_reconstruction_eurusd.json")
    assert ctx.month11 is not None
    assert ctx.month11.mega_trade_family == "fx"
    assert ctx.month11.identified_mega_trade == "present"
    assert ctx.month11.mega_trade.flag is True
    assert ctx.session_ticket is None
    ctx9 = load_day_context(ROOT / "fixtures/m9_reconstruction_eurusd.json")
    assert ctx9.month11 is None



def test_month11_slice2_context():
    import json
    from ftn.os.m11_context import derive_month11_context
    ev = json.loads((ROOT / "fixtures/m11_evidence_eurusd.json").read_text())
    st = derive_month11_context(ev)
    assert st.mega_trade_family == "fx"
    assert st.identified_mega_trade == "present"
    assert st.mega_trade.flag is False
    raw = json.loads((ROOT / "fixtures/m11_reconstruction_eurusd.json").read_text())
    assert derive_month11_context(raw).mega_trade.flag is False
    noneid = json.loads(json.dumps(ev))
    noneid["evidence"]["identified_mega_trade"] = "none"
    st2 = derive_month11_context(noneid)
    assert st2.quarterly_shift_overlap == "present"
    assert st2.mega_trade.flag is False
    src = (ROOT / "src/ftn/os/m11_context.py").read_text()
    assert 'raw.get("month5")' not in src
    assert 'raw.get("month6")' not in src



def test_month11_slice3_flag():
    import json
    from ftn.os.m11_context import derive_month11_context
    from ftn.os.m11_mega import derive_month11
    ev = json.loads((ROOT / "fixtures/m11_evidence_eurusd.json").read_text())
    assert derive_month11_context(ev).mega_trade.flag is False
    st = derive_month11(ev)
    assert st.mega_trade.flag is True
    noneid = json.loads(json.dumps(ev))
    noneid["evidence"]["identified_mega_trade"] = "none"
    st2 = derive_month11(noneid)
    assert st2.mega_trade_family == "fx"
    assert st2.quarterly_shift_overlap == "present"
    assert st2.mega_trade.flag is False



def test_month11_slice4_dtr():
    from ftn.os.dtr import build_context
    ctx = build_context(ROOT / "fixtures/m11_evidence_eurusd.json")
    assert ctx.month11 is not None
    assert ctx.month11.mega_trade.flag is True
    assert ctx.session_ticket is None
    ctx9 = build_context(ROOT / "fixtures/m9_reconstruction_eurusd.json")
    assert ctx9.month11 is None



def test_month11_slice5_brief():
    from ftn.os.briefing import brief_from_fixture
    _, _, md, *_ = brief_from_fixture(ROOT / "fixtures/m11_evidence_eurusd.json")
    assert "## Month 11 (ICT mega-trade)" in md
    assert "not a session ticket" in md
    assert "does not select an M9 candidate" in md



def test_month11_slice6_matrix():
    import json
    from ftn.os.m11_mega import derive_month11
    from ftn.os.dtr import build_context
    for name, family, ident, flag in CASES_M11:
        raw = json.loads((ROOT / "fixtures" / name).read_text())
        assert "pick" not in raw and "expected_winner" not in raw
        st = derive_month11(raw)
        assert st.mega_trade_family == family
        assert st.identified_mega_trade == ident
        assert st.mega_trade.flag is flag
        ctx = build_context(ROOT / "fixtures" / name)
        assert ctx.month11 is not None
        assert ctx.month11.mega_trade.flag is flag
        assert ctx.session_ticket is None


def test_month11_engine_never_opens_gold():
    roots = [
        ROOT / "src/ftn/os/m11_contracts.py",
        ROOT / "src/ftn/os/m11_context.py",
        ROOT / "src/ftn/os/m11_mega.py",
        ROOT / "src/ftn/os/dtr.py",
        ROOT / "src/ftn/os/briefing.py",
    ]
    for path in roots:
        txt = path.read_text()
        assert ".expected.json" not in txt, path.name



def test_month12_slice1_schema():
    from ftn.os.contracts import load_day_context
    ctx = load_day_context(ROOT / "fixtures/m12_reconstruction_eurusd.json")
    assert ctx.month12 is not None
    assert ctx.month12.intermediate_term_note == "none"
    assert ctx.month12.identified_top_down == "present"
    assert ctx.month12.top_down.flag is True
    assert ctx.session_ticket is None
    ctx9 = load_day_context(ROOT / "fixtures/m9_reconstruction_eurusd.json")
    assert ctx9.month12 is None



def test_month12_slice2_context():
    import json
    from ftn.os.m12_context import derive_month12_context
    ev = json.loads((ROOT / "fixtures/m12_evidence_eurusd.json").read_text())
    st = derive_month12_context(ev)
    assert st.intermediate_term_note == "none"
    assert st.identified_top_down == "present"
    assert st.top_down.flag is False
    raw = json.loads((ROOT / "fixtures/m12_reconstruction_eurusd.json").read_text())
    assert derive_month12_context(raw).top_down.flag is False
    four = json.loads(json.dumps(ev))
    four["evidence"]["intermediate_term_note"] = "present"
    four["evidence"]["identified_top_down"] = "none"
    st2 = derive_month12_context(four)
    assert st2.long_term_note == "present"
    assert st2.identified_top_down == "none"
    assert st2.top_down.flag is False
    src = (ROOT / "src/ftn/os/m12_context.py").read_text()
    assert 'raw.get("month5")' not in src
    assert 'raw.get("month11")' not in src



def test_month12_slice3_flag():
    import json
    from ftn.os.m12_context import derive_month12_context
    from ftn.os.m12_topdown import derive_month12
    ev = json.loads((ROOT / "fixtures/m12_evidence_eurusd.json").read_text())
    assert derive_month12_context(ev).top_down.flag is False
    st = derive_month12(ev)
    assert st.intermediate_term_note == "none"
    assert st.identified_top_down == "present"
    assert st.top_down.flag is True
    noneid = json.loads(json.dumps(ev))
    noneid["evidence"]["identified_top_down"] = "none"
    noneid["evidence"]["intermediate_term_note"] = "present"
    st2 = derive_month12(noneid)
    assert st2.long_term_note == "present"
    assert st2.intermediate_term_note == "present"
    assert st2.short_term_note == "present"
    assert st2.intraday_note == "present"
    assert st2.top_down.flag is False



def test_month12_slice4_dtr():
    from ftn.os.dtr import build_context
    ctx = build_context(ROOT / "fixtures/m12_evidence_eurusd.json")
    assert ctx.month12 is not None
    assert ctx.month12.intermediate_term_note == "none"
    assert ctx.month12.top_down.flag is True
    assert ctx.session_ticket is None
    ctx9 = build_context(ROOT / "fixtures/m9_reconstruction_eurusd.json")
    assert ctx9.month12 is None



def test_month12_slice5_brief():
    from ftn.os.briefing import brief_from_fixture
    _, _, md, *_ = brief_from_fixture(ROOT / "fixtures/m12_evidence_eurusd.json")
    assert "## Month 12 (ICT top-down)" in md
    assert "not a session ticket" in md
    assert "does not select an M9 candidate" in md
    assert "Intermediate-term:** none" in md



def test_month12_slice6_matrix():
    import json
    from ftn.os.m12_topdown import derive_month12
    from ftn.os.dtr import build_context
    for name, inter, ident, flag in CASES_M12:
        raw = json.loads((ROOT / "fixtures" / name).read_text())
        assert "pick" not in raw and "expected_winner" not in raw
        st = derive_month12(raw)
        assert st.intermediate_term_note == inter
        assert st.identified_top_down == ident
        assert st.top_down.flag is flag
        ctx = build_context(ROOT / "fixtures" / name)
        assert ctx.month12 is not None
        assert ctx.month12.top_down.flag is flag
        assert ctx.session_ticket is None


def test_month12_engine_never_opens_gold():
    roots = [
        ROOT / "src/ftn/os/m12_contracts.py",
        ROOT / "src/ftn/os/m12_context.py",
        ROOT / "src/ftn/os/m12_topdown.py",
        ROOT / "src/ftn/os/dtr.py",
        ROOT / "src/ftn/os/briefing.py",
    ]
    for path in roots:
        txt = path.read_text()
        assert ".expected.json" not in txt, path.name



def test_charter_slice1_schema():
    from ftn.os.contracts import load_day_context
    ctx = load_day_context(ROOT / "fixtures/charter_reconstruction_eurusd.json")
    assert ctx.charter is not None
    assert ctx.charter.identified_pam == "present"
    assert len(ctx.charter.recognized_pams) == 1
    e = ctx.charter.recognized_pams[0]
    assert e.pam_id == "pam1"
    assert e.horizon == "intraday_scalp"
    assert e.primary_lecture_note == "present"
    assert ctx.charter.charter_recognition.flag is True
    assert ctx.charter.model13_bridge == "none"
    assert ctx.session_ticket is None
    ctx9 = load_day_context(ROOT / "fixtures/m9_reconstruction_eurusd.json")
    assert ctx9.charter is None



def test_charter_slice2_context():
    import json
    from ftn.os.pam_context import derive_charter_context
    ev = json.loads((ROOT / "fixtures/charter_evidence_eurusd.json").read_text())
    st = derive_charter_context(ev)
    assert st.identified_pam == "present"
    assert len(st.recognized_pams) == 1
    assert st.recognized_pams[0].pam_id == "pam1"
    assert st.charter_recognition.flag is False
    assert st.charter_recognition.reason == "slice2_context_only"
    raw = json.loads((ROOT / "fixtures/charter_reconstruction_eurusd.json").read_text())
    assert derive_charter_context(raw).charter_recognition.flag is False
    noneid = json.loads(json.dumps(ev))
    noneid["evidence"]["identified_pam"] = "none"
    st2 = derive_charter_context(noneid)
    assert st2.recognized_pams[0].pam_id == "pam1"
    assert st2.charter_recognition.flag is False
    src = (ROOT / "src/ftn/os/pam_context.py").read_text()
    assert 'raw.get("month5")' not in src
    assert 'raw.get("month7")' not in src
    assert 'raw.get("month9")' not in src



def test_charter_slice3_recognition():
    import json
    from ftn.os.pam_context import derive_charter_context
    from ftn.os.pam_recognize import derive_charter
    ev = json.loads((ROOT / "fixtures/charter_evidence_eurusd.json").read_text())
    assert derive_charter_context(ev).charter_recognition.flag is False
    st = derive_charter(ev)
    assert st.identified_pam == "present"
    assert st.recognized_pams[0].pam_id == "pam1"
    assert st.charter_recognition.flag is True
    noneid = json.loads(json.dumps(ev))
    noneid["evidence"]["identified_pam"] = "none"
    st2 = derive_charter(noneid)
    assert st2.recognized_pams[0].pam_id == "pam1"
    assert st2.charter_recognition.flag is False
    nopam = json.loads(json.dumps(ev))
    nopam["evidence"]["recognized_pams"] = []
    st3 = derive_charter(nopam)
    assert st3.identified_pam == "present"
    assert st3.charter_recognition.flag is False



def test_charter_slice4_dtr():
    from ftn.os.dtr import build_context
    ctx = build_context(ROOT / "fixtures/charter_evidence_eurusd.json")
    assert ctx.charter is not None
    assert ctx.charter.recognized_pams[0].pam_id == "pam1"
    assert ctx.charter.charter_recognition.flag is True
    assert ctx.session_ticket is None
    ctx9 = build_context(ROOT / "fixtures/m9_reconstruction_eurusd.json")
    assert ctx9.charter is None



def test_charter_slice5_brief():
    from ftn.os.briefing import brief_from_fixture
    _, _, md, *_ = brief_from_fixture(ROOT / "fixtures/charter_evidence_eurusd.json")
    assert "## Charter (ICT PAM)" in md
    assert "not a session ticket" in md
    assert "does not select an M9 candidate" in md
    assert "pam1" in md



def test_charter_slice6_matrix():
    import json
    from ftn.os.pam_recognize import derive_charter
    from ftn.os.dtr import build_context
    for name, ident, pams, flag in CASES_CHARTER:
        raw = json.loads((ROOT / "fixtures" / name).read_text())
        assert "pick" not in raw and "expected_winner" not in raw
        st = derive_charter(raw)
        assert st.identified_pam == ident
        assert tuple(e.pam_id for e in st.recognized_pams) == pams
        assert st.charter_recognition.flag is flag
        ctx = build_context(ROOT / "fixtures" / name)
        assert ctx.charter is not None
        assert ctx.charter.charter_recognition.flag is flag
        assert ctx.session_ticket is None


def test_charter_engine_never_opens_gold():
    roots = [
        ROOT / "src/ftn/os/pam_contracts.py",
        ROOT / "src/ftn/os/pam_context.py",
        ROOT / "src/ftn/os/pam_recognize.py",
        ROOT / "src/ftn/os/dtr.py",
        ROOT / "src/ftn/os/briefing.py",
    ]
    for path in roots:
        txt = path.read_text()
        assert ".expected.json" not in txt, path.name



def test_pam1_evidence_schema():
    import json
    from ftn.os.pam1_evidence import parse_pam1_evidence
    raw = json.loads((ROOT / "fixtures/pam1_evidence_eurusd.json").read_text())
    e = parse_pam1_evidence(raw)
    assert e is not None
    assert e.direction == "bullish"
    assert e.ipda.present == "present"
    assert e.ipda.lookback_trading_days == 20
    assert e.institutional_sponsorship == "present"
    assert e.premium_discount_context == "discount"
    assert e.liquidity_objective.type == "previous_daily_high"
    assert e.ny_execution_window == "present"
    assert e.ote.fib_level == "62_percent"
    assert e.directional_link == "present"
    assert e.confirming.liquidity_raid == "present"
    # still not a detector / ticket path
    from ftn.os.pam_recognize import derive_charter
    st = derive_charter(raw)
    assert st.charter_recognition.flag is True  # identified + pam1 listed
    from ftn.os.dtr import build_context
    ctx = build_context(ROOT / "fixtures/pam1_evidence_eurusd.json")
    assert ctx.session_ticket is None



def test_pam1_dtr_attach():
    from ftn.os.dtr import build_context
    ctx = build_context(ROOT / "fixtures/pam1_evidence_eurusd.json")
    assert ctx.pam1_evidence is not None
    assert ctx.pam1_evidence.direction == "bullish"
    assert ctx.pam1_evidence.ipda.lookback_trading_days == 20
    assert ctx.charter is not None
    assert ctx.charter.recognized_pams[0].pam_id == "pam1"
    assert ctx.session_ticket is None
    ctx9 = build_context(ROOT / "fixtures/m9_reconstruction_eurusd.json")
    assert ctx9.pam1_evidence is None
    assert ctx9.charter is None



def test_pam1_completeness():
    import json
    from ftn.os.pam1_complete import derive_pam1_completeness
    from ftn.os.dtr import build_context
    raw = json.loads((ROOT / "fixtures/pam1_evidence_eurusd.json").read_text())
    c = derive_pam1_completeness(raw)
    assert c is not None
    assert c.required_complete is True
    assert "direction" in c.required_present
    assert "ote" in c.required_present
    assert "liquidity_raid" in c.confirming_present
    incomplete = json.loads(json.dumps(raw))
    incomplete["evidence"]["pam1_model_context"]["ote"] = {"present": "none"}
    c2 = derive_pam1_completeness(incomplete)
    assert c2.required_complete is False
    assert "ote" in c2.required_missing
    ctx = build_context(ROOT / "fixtures/pam1_evidence_eurusd.json")
    assert ctx.pam1_completeness.required_complete is True
    assert ctx.session_ticket is None
    # completeness is not recognition
    assert ctx.charter.charter_recognition.flag is True  # still from identified_pam



def test_pam1_completeness_matrix():
    """Completeness is descriptive; never mints Charter recognition or ticket alone."""
    import json
    from ftn.os.pam1_complete import derive_pam1_completeness
    from ftn.os.pam_recognize import derive_charter
    from ftn.os.dtr import build_context

    base = json.loads((ROOT / "fixtures/pam1_evidence_eurusd.json").read_text())
    # complete required
    c = derive_pam1_completeness(base)
    assert c.required_complete is True
    assert not c.required_missing
    st = derive_charter(base)
    assert st.charter_recognition.flag is True  # from identified_pam + pam1, not completeness

    # missing ote → incomplete, recognition unchanged if identified still present
    miss = json.loads(json.dumps(base))
    miss["evidence"]["pam1_model_context"]["ote"] = {"present": "none", "fib_level": "none"}
    c2 = derive_pam1_completeness(miss)
    assert c2.required_complete is False
    assert "ote" in c2.required_missing
    st2 = derive_charter(miss)
    assert st2.charter_recognition.flag is True  # still identified

    # confirming all none → still complete if required ok
    noconf = json.loads(json.dumps(base))
    noconf["evidence"]["pam1_model_context"]["price_structure"] = {
        "liquidity_raid": "none",
        "displacement": "none",
        "market_structure_shift": "none",
        "institutional_reference": "none",
    }
    c3 = derive_pam1_completeness(noconf)
    assert c3.required_complete is True
    assert set(c3.confirming_missing) == {
        "liquidity_raid", "displacement", "market_structure_shift", "institutional_reference"
    }

    # no identified_pam → recognition false even if evidence complete
    noid = json.loads(json.dumps(base))
    noid["evidence"]["identified_pam"] = "none"
    st4 = derive_charter(noid)
    assert st4.charter_recognition.flag is False
    assert derive_pam1_completeness(noid).required_complete is True

    ctx = build_context(ROOT / "fixtures/pam1_evidence_eurusd.json")
    assert ctx.session_ticket is None
    assert ctx.pam1_completeness.required_complete is True



def test_handoff_v1_i1b():
    """I1b: day_context_handoff transport + PAM1 fields; no signal keys."""
    import json
    from ftn.os.briefing import brief_from_fixture
    from ftn.os.handoff import build_handoff, KIND_V1, SCHEMA_VERSION
    state, cands, md, ftn = brief_from_fixture(ROOT / "fixtures/pam1_evidence_eurusd.json")
    h = build_handoff(state, cands, ftn or {})
    assert h["schemaVersion"] == SCHEMA_VERSION
    assert h["kind"] == KIND_V1
    assert h["kind"] != "month9_handoff"
    ms = h["market_state"]
    assert ms.get("charter") is not None
    assert ms["charter"]["charter_recognition"]["flag"] is True
    assert ms.get("pam1_evidence") is not None
    assert ms["pam1_evidence"]["direction"] == "bullish"
    assert ms.get("pam1_completeness") is not None
    assert ms["pam1_completeness"]["required_complete"] is True
    assert h.get("session_ticket") is None
    # Signal-style keys must be absent at top level (not institutional confidence labels)
    for banned in ("BUY", "SELL", "best_pam", "pam_rank", "broker_instruction", "recommendation"):
        assert banned not in h
    assert "best_pam" not in json.dumps(h.get("candidates"))
    assert h.get("session_ticket") is None



if __name__ == "__main__":
    test_fixture_has_no_winner()
    test_reconstruct_matches_gold()
    test_gold_edit_does_not_change_engine(Path("/tmp"))
    test_rev_reads_market_state_only()
    test_all_reconstruction_cases()
    test_conso_fade_play_and_preemption()
    test_bb_engines()
    test_pip20_window_and_bb_suppress()
    test_session_ticket_one_per_session()
    test_dtr_derives_unlabeled_raw()
    test_wr_from_bars()
    test_raid_from_bars()
    test_mss_from_bars()
    test_box_from_bars()
    test_origin_from_arrays()
    test_calendar_focus()
    test_dxy_relationship()
    test_session_clocks()
    test_x_ask_read_only()
    test_mint_draft_paper()
    test_live_data_off_by_default()
    test_month8_contracts_and_fixture()
    test_month8_evidence_derives_gate()
    test_month8_slice2_does_not_name_profile()
    test_month8_profile_from_path()
    test_month8_expanded_gate_is_hermes()
    test_month8_slice4_regression()
    test_month8_slice5_projection()
    test_month8_slice6_htf()
    test_month8_slice7_dtr()
    test_month8_slice8_brief()
    test_month8_slice9_matrix()
    test_month8_engine_never_opens_gold()
    test_month7_slice1_schema()
    test_month7_slice2_range()
    test_month7_slice3_profile()
    test_month7_slice4_template()
    test_month7_slice5_lrlr()
    test_month7_slice6_osok()
    test_month7_slice7_swing()
    test_month7_slice8_dtr()
    test_month7_slice9_brief()
    test_month7_slice10_matrix()
    test_month7_engine_never_opens_gold()
    test_month6_slice1_schema()
    test_month5_slice1_schema()
    test_month4_slice1_schema()
    test_month3_slice1_schema()
    test_month2_slice1_schema()
    test_month1_slice1_schema()
    test_month10_slice1_schema()
    test_month11_slice1_schema()
    test_month12_slice1_schema()
    test_charter_slice1_schema()
    test_charter_slice2_context()
    test_charter_slice3_recognition()
    test_charter_slice4_dtr()
    test_charter_slice5_brief()
    test_charter_slice6_matrix()
    test_pam1_evidence_schema()
    test_pam1_dtr_attach()
    test_pam1_completeness()
    test_pam1_completeness_matrix()
    test_handoff_v1_i1b()
    test_charter_engine_never_opens_gold()
    test_month12_slice2_context()
    test_month12_slice3_flag()
    test_month12_slice4_dtr()
    test_month12_slice5_brief()
    test_month12_slice6_matrix()
    test_month12_engine_never_opens_gold()
    test_month11_slice2_context()
    test_month11_slice3_flag()
    test_month11_slice4_dtr()
    test_month11_slice5_brief()
    test_month11_slice6_matrix()
    test_month11_engine_never_opens_gold()
    test_month10_slice2_context()
    test_month10_slice3_flag()
    test_month10_slice4_dtr()
    test_month10_slice5_brief()
    test_month10_slice6_matrix()
    test_month10_engine_never_opens_gold()
    test_month1_slice2_context()
    test_month1_slice3_setup()
    test_month1_slice4_dtr()
    test_month1_slice5_brief()
    test_month1_slice6_matrix()
    test_month1_engine_never_opens_gold()
    test_integration_i2_attach()
    test_integration_i3_ticket_isolation()
    test_integration_i4_brief()
    test_integration_i5_golds()
    test_month2_slice2_context()
    test_month2_slice3_frame()
    test_month2_slice4_dtr()
    test_month2_slice5_brief()
    test_month2_slice6_matrix()
    test_month2_engine_never_opens_gold()
    test_month3_slice2_context()
    test_month3_slice3_setup()
    test_month3_slice4_dtr()
    test_month3_slice5_brief()
    test_month3_slice6_matrix()
    test_month3_engine_never_opens_gold()
    test_month4_slice2_catalog()
    test_month4_slice3_opportunity()
    test_month4_slice4_dtr()
    test_month4_slice5_brief()
    test_month4_slice6_matrix()
    test_month4_engine_never_opens_gold()
    test_month5_slice2_env()
    test_month5_slice3_float()
    test_month5_slice4_swing()
    test_month5_slice5_confirm()
    test_month5_slice6_pd()
    test_month5_slice7_setup()
    test_month5_slice8_opportunity()
    test_month5_slice9_dtr_brief()
    test_month5_slice10_matrix()
    test_month5_engine_never_opens_gold()
    test_month6_slice2_env()
    test_month6_slice3_evidence()
    test_month6_slice4_family()
    test_month6_slice5_risk()
    test_month6_slice6_md()
    test_month6_slice7_opportunity()
    test_month6_slice8_dtr()
    test_month6_slice9_brief()
    test_month6_slice10_matrix()
    test_month6_engine_never_opens_gold()
    print("all reconstruction tests ok")
