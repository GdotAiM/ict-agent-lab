
"""DTR builder: fill derived Market State fields from raw evidence."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from ftn.os.contracts import load_day_context
from ftn.os.institutional import build_institutional
from ftn.os.mss import detect_mss
from ftn.os.profile import derive_profile
from ftn.os.raid import detect_raid
from ftn.os.box import detect_box
from ftn.os.pd_origin import select_origin_targets
from ftn.os.calendar import pick_focus
from ftn.os.dxy import dxy_relationship
from ftn.os.clocks import session_clocks
from ftn.os.sentiment import build_sentiment
from ftn.os.m8_profile import derive_month8_profile
from ftn.os.m7_swing import derive_month7_swing
from ftn.os.m6_opportunity import derive_month6
from ftn.os.m5_opportunity import derive_month5
from ftn.os.m4_opportunity import derive_month4
from ftn.os.m3_setup import derive_month3
from ftn.os.m2_frame import derive_month2
from ftn.os.m1_setup import derive_month1
from ftn.os.m10_confluence import derive_month10
from ftn.os.m11_mega import derive_month11
from ftn.os.m12_topdown import derive_month12
from ftn.os.pam_recognize import derive_charter
from ftn.os.pam1_evidence import parse_pam1_evidence
from ftn.os.pam1_complete import annotate_pam1_completeness


def build_context(path: str | Path):
    path = Path(path)
    raw = json.loads(path.read_text())
    ctx = load_day_context(path)
    inst = build_institutional(raw)
    ev = dict(raw.get("evidence") or {})
    bars = raw.get("bars_m15") or ev.get("bars_m15") or []
    named = ((raw.get("ranges") or {}).get("named_extremes") or {})
    raid_in = ev.get("raid") or {}
    if bars and named and not raid_in.get("taken"):
        ev["raid"] = detect_raid(bars, named)
        if ev["raid"].get("taken") and ev["raid"].get("level") in {"pdh", "pdl"}:
            ev.setdefault("htf_pd_at_raid", raw.get("origin_pd_array"))
    if bars and "box" not in ev:
        box_bars = bars
        ridx = None
        if ev.get("raid") and ev["raid"].get("taken"):
            meta = detect_mss(bars, ev["raid"])
            ridx = meta.get("raid_bar_index")
        if ridx is not None and ridx >= 8:
            box_bars = bars[: int(ridx)]
        ev["box"] = detect_box(box_bars, (raw.get("ranges") or {}).get("previous_day"))
    if bars and ev.get("raid") and "mss" not in ev:
        ms = detect_mss(bars, ev.get("raid") or {})
        ev["mss"] = bool(ms.get("mss") or ms.get("displacement"))
        ev["displacement"] = ms.get("displacement")
        ev["mss_meta"] = {k: ms[k] for k in ("source", "raid_bar_index", "swing") if k in ms}
    wr_raw = dict(raw)
    # sentiment WR uses tape into the raid, not the displacement after
    idx = (ev.get("mss_meta") or {}).get("raid_bar_index")
    if bars and idx is not None:
        wr_raw["bars_m15"] = bars[: int(idx) + 1]
    sent = build_sentiment(wr_raw, inst.state)
    profile_raw = dict(raw)
    profile_raw["evidence"] = ev
    profile = derive_profile(profile_raw)
    focus = pick_focus(list(ctx.calendar), list(ctx.watchlist), raw.get("symbol"))
    ev["focus_source"] = focus["source"]
    ev["idle"] = focus["idle"]
    clocks = session_clocks(ev.get("session") or raw.get("session"), raw.get("clock") or ev.get("clock"))
    ev.setdefault("protraction_stage", clocks["protraction_stage"])
    ev.setdefault("pip20_window", clocks["pip20_window"])
    dxy = dict(ctx.dxy or raw.get("dxy") or {})
    dxy["relationship"] = dxy_relationship(
        focus["focus_pair"] or raw.get("symbol") or "",
        inst.state,
        dxy.get("institutional"),
    )
    origin = ctx.origin_pd_array
    targets = list(ctx.opposing_target_arrays)
    if not origin:
        daily = ((raw.get("pd_matrix") or {}).get("htf") or {}).get("daily") or []
        picked = select_origin_targets(daily, raw.get("last"), inst.state)
        origin = picked.get("origin")
        targets = picked.get("targets") or targets
        if origin:
            ev.setdefault("htf_pd_at_raid", origin)
    charter = None
    ch_ev = bool(
        raw.get("charter")
        or raw.get("ict_charter")
        or (raw.get("evidence") or {}).get("identified_pam")
        or (raw.get("evidence") or {}).get("recognized_pams")
    )
    if ch_ev:
        raw_ch = dict(raw)
        raw_ch["evidence"] = ev
        charter = derive_charter(raw_ch)
    pam1_evidence = parse_pam1_evidence(raw)
    pam1_completeness = annotate_pam1_completeness(pam1_evidence)
    month12 = None
    td_ev = bool(
        raw.get("month12")
        or raw.get("ict_top_down")
        or (raw.get("evidence") or {}).get("identified_top_down")
        or (raw.get("evidence") or {}).get("long_term_note")
        or (raw.get("evidence") or {}).get("intraday_note")
    )
    if td_ev:
        raw_m12 = dict(raw)
        raw_m12["evidence"] = ev
        month12 = derive_month12(raw_m12)
    month11 = None
    mega_ev = bool(
        raw.get("month11")
        or raw.get("ict_mega")
        or (raw.get("evidence") or {}).get("identified_mega_trade")
        or (raw.get("evidence") or {}).get("mega_trade_family")
    )
    if mega_ev:
        raw_m11 = dict(raw)
        raw_m11["evidence"] = ev
        month11 = derive_month11(raw_m11)
    month10 = None
    ma_ev = bool(
        raw.get("month10")
        or raw.get("ict_multi_asset")
        or (raw.get("evidence") or {}).get("identified_multi_asset")
        or (raw.get("evidence") or {}).get("cot_reading")
        or (raw.get("evidence") or {}).get("asset_class")
    )
    if ma_ev:
        raw_m10 = dict(raw)
        raw_m10["evidence"] = ev
        month10 = derive_month10(raw_m10)
    month1 = None
    found_ev = bool(
        raw.get("month1")
        or raw.get("ict_foundation")
        or (raw.get("evidence") or {}).get("identified_setup_elements")
        or (raw.get("evidence") or {}).get("dealing_range_side")
    )
    if found_ev:
        raw_m1 = dict(raw)
        raw_m1["evidence"] = ev
        month1 = derive_month1(raw_m1)
    month2 = None
    risk_ev = bool(
        raw.get("month2")
        or raw.get("ict_risk")
        or (raw.get("evidence") or {}).get("identified_low_risk_frame")
        or (raw.get("evidence") or {}).get("identified_high_reward_context")
    )
    if risk_ev:
        raw_m2 = dict(raw)
        raw_m2["evidence"] = ev
        month2 = derive_month2(raw_m2)
    month3 = None
    nxt_ev = bool(
        raw.get("month3")
        or raw.get("ict_next")
        or (raw.get("evidence") or {}).get("selected_timeframe")
        or (raw.get("evidence") or {}).get("anticipated_setup")
    )
    if nxt_ev:
        raw_m3 = dict(raw)
        raw_m3["evidence"] = ev
        month3 = derive_month3(raw_m3)
    month4 = None
    arr_ev = bool(
        raw.get("month4")
        or raw.get("ict_arrays")
        or (raw.get("evidence") or {}).get("arrays")
        or raw.get("arrays")
    )
    if arr_ev:
        raw_m4 = dict(raw)
        raw_m4["evidence"] = ev
        if origin:
            raw_m4["origin_pd_array"] = origin
        month4 = derive_month4(raw_m4)
    month5 = None
    inst_sp = ((raw.get("pair_institutional") or {}).get("sponsorship") or {})
    pos_ev = bool(
        raw.get("month5")
        or raw.get("ict_position")
        or raw.get("quarterly_shift")
        or raw.get("ipda_days")
        or inst_sp.get("monthly")
        or str(origin or raw.get("origin_pd_array") or "").startswith("M_")
    )
    if pos_ev:
        raw_m5 = dict(raw)
        raw_m5["evidence"] = ev
        if origin:
            raw_m5["origin_pd_array"] = origin
        month5 = derive_month5(raw_m5)
    month6 = None
    inst_sp = ((raw.get("pair_institutional") or {}).get("sponsorship") or {})
    swing_ev = bool(
        raw.get("month6")
        or raw.get("ict_swing")
        or inst_sp.get("monthly")
        or str(origin or raw.get("origin_pd_array") or "").startswith("M_")
    )
    if swing_ev:
        raw_m6 = dict(raw)
        raw_m6["evidence"] = ev
        if origin:
            raw_m6["origin_pd_array"] = origin
        month6 = derive_month6(raw_m6)
    month7 = None
    ev_path = (ev.get("week_path") or raw.get("week_path"))
    origin_tf = str(origin or raw.get("origin_pd_array") or "")
    weekly_ev = bool(
        raw.get("month7")
        or raw.get("ict_week")
        or ev_path
        or raw.get("ipda_days")
        or origin_tf.startswith("W_")
        or origin_tf.startswith("M_")
    )
    if weekly_ev:
        raw_m7 = dict(raw)
        raw_m7["evidence"] = ev
        if origin:
            raw_m7["origin_pd_array"] = origin
        month7 = derive_month7_swing(raw_m7, persist=False)
    month8 = None
    if raw.get("month8") or raw.get("ict_day") or (raw.get("ranges") or {}).get("cbdr"):
        raw_m8 = dict(raw)
        raw_m8["evidence"] = ev
        if origin:
            raw_m8["origin_pd_array"] = origin
        month8 = derive_month8_profile(raw_m8)
    return replace(
        ctx,
        pair_institutional=inst,
        sentiment=sent,
        profile=profile,
        evidence=ev,
        origin_pd_array=origin,
        opposing_target_arrays=tuple(targets),
        focus_pair=focus["focus_pair"] or ctx.focus_pair or raw.get("symbol") or "",
        dxy=dxy,
        month8=month8,
        month7=month7,
        month6=month6,
        month5=month5,
        month4=month4,
        month3=month3,
        month2=month2,
        month1=month1,
        month10=month10,
        month11=month11,
        month12=month12,
        charter=charter,
        pam1_evidence=pam1_evidence,
        pam1_completeness=pam1_completeness,
    )
