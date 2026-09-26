
"""DTR briefing markdown. Market State + candidates. Never reads gold files."""

from __future__ import annotations

from pathlib import Path

from ftn.models.ftn import annotate_ftn
from ftn.os.candidates import evaluate_candidates
from ftn.os.contracts import DayContext, MarketState, freeze_market_state, load_day_context
from ftn.os.dtr import build_context
from ftn.os.handoff import write_handoff, build_handoff
from ftn.os.mint_draft import write_draft
from ftn.os.session_ticket import attach_ticket, persist_ticket


def _chip(v) -> str:
    return str(v).replace("_", " ")














def _charter_lines(c: DayContext) -> list:
    ch = getattr(c, "charter", None)
    lines = ["## Charter (ICT PAM)", ""]
    if not ch:
        lines += ["- not attached", ""]
        return lines
    cr = ch.charter_recognition
    pams = [e.pam_id for e in (ch.recognized_pams or ()) if e.pam_id != "none"] or ["none"]
    lines += [
        f"- **Identified PAM:** {ch.identified_pam}",
        f"- **Recognized:** {', '.join(pams)}",
        f"- **Model 13 bridge:** {ch.model13_bridge}",
        f"- **Charter recognition:** {cr.flag} ({cr.reason}) — not a session ticket",
        "",
        "Charter describes named model recognition. It does not select an M9 candidate or create a paper ticket.",
        "",
    ]
    for e in ch.recognized_pams or ():
        if e.pam_id == "none":
            continue
        lines += [
            f"- **{e.pam_id}** ({e.horizon}): primary={e.primary_lecture_note}, "
            f"amplified={e.amplified_note}, trade_plan={e.trade_plan_note}, "
            f"algo={e.algorithmic_theory_note}",
        ]
    if ch.recognized_pams:
        lines.append("")
    return lines


def _month12_lines(c: DayContext) -> list:
    m12 = getattr(c, "month12", None)
    lines = ["## Month 12 (ICT top-down)", ""]
    if not m12:
        lines += ["- not attached", ""]
        return lines
    td = m12.top_down
    lines += [
        f"- **Long-term:** {m12.long_term_note}",
        f"- **Intermediate-term:** {m12.intermediate_term_note}",
        f"- **Short-term:** {m12.short_term_note}",
        f"- **Intraday:** {m12.intraday_note}",
        f"- **Identified top-down:** {m12.identified_top_down}",
        f"- **Top-down:** {td.flag} ({td.reason}) — not a session ticket",
        "",
        "Month 12 describes a top-down reading. It does not select an M9 candidate or write M5–M11 fields.",
        "",
    ]
    return lines


def _month11_lines(c: DayContext) -> list:
    m11 = getattr(c, "month11", None)
    lines = ["## Month 11 (ICT mega-trade)", ""]
    if not m11:
        lines += ["- not attached", ""]
        return lines
    mt = m11.mega_trade
    lines += [
        f"- **Family:** {m11.mega_trade_family}",
        f"- **Identified mega-trade:** {m11.identified_mega_trade}",
        f"- **Quarterly overlap:** {m11.quarterly_shift_overlap}",
        f"- **Seasonal overlap:** {m11.seasonal_overlap}",
        f"- **Relative strength:** {m11.relative_strength_note}",
        f"- **Mega-trade:** {mt.flag} ({mt.reason}) — not a session ticket",
        "",
        "Month 11 describes a mega-trade horizon. It does not select an M9 candidate or write M5 quarterly_shift.",
        "",
    ]
    return lines


def _month10_lines(c: DayContext) -> list:
    m10 = getattr(c, "month10", None)
    lines = ["## Month 10 (ICT multi-asset)", ""]
    if not m10:
        lines += ["- not attached", ""]
        return lines
    mac = m10.multi_asset_context
    lines += [
        f"- **Identified multi-asset:** {m10.identified_multi_asset}",
        f"- **COT:** {m10.cot_reading}",
        f"- **Relative strength:** {m10.relative_strength}",
        f"- **Open interest:** {m10.open_interest}",
        f"- **Commodity seasonal:** {m10.commodity_seasonal_note}",
        f"- **Carrying charge:** {m10.carrying_charge_note}",
        f"- **Asset class:** {m10.asset_class}",
        f"- **Asset session:** {m10.asset_session_note}",
        f"- **Confluence:** {m10.multi_asset_confluence_note}",
        f"- **Options:** {m10.options_note}",
        f"- **Watchlist:** {m10.watchlist_note}",
        f"- **Multi-asset context:** {mac.flag} ({mac.reason}) — not a session ticket",
        "",
        "Month 10 describes multi-asset context. It does not select an M9 candidate or write M5/M6 fields.",
        "",
    ]
    return lines


def _month1_lines(c: DayContext) -> list:
    m1 = getattr(c, "month1", None)
    lines = ["## Month 1 (ICT foundation)", ""]
    if not m1:
        lines += ["- not attached", ""]
        return lines
    se = m1.setup_elements
    lines += [
        f"- **Identified setup elements:** {m1.identified_setup_elements}",
        f"- **Dealing-range side:** {m1.dealing_range_side}",
        f"- **Conditioning:** {m1.conditioning_note}",
        f"- **Focus:** {m1.focus_note}",
        f"- **Fair valuation:** {m1.fair_valuation_note}",
        f"- **Liquidity run:** {m1.liquidity_run_note}",
        f"- **Impulse:** {m1.impulse_note}",
        f"- **Protraction:** {m1.protraction_note}",
        f"- **Setup elements:** {se.flag} ({se.reason}) — not a session ticket",
        "",
        "Month 1 describes foundation context. It does not select an M9 candidate or overwrite Hermes profile.",
        "",
    ]
    return lines


def _month2_lines(c: DayContext) -> list:
    m2 = getattr(c, "month2", None)
    lines = ["## Month 2 (ICT risk frame)", ""]
    if not m2:
        lines += ["- not attached", ""]
        return lines
    fr = m2.low_risk_frame
    lines += [
        f"- **Small-account posture:** {m2.small_account_posture}",
        f"- **Identified low-risk:** {m2.identified_low_risk_frame}",
        f"- **Identified high-reward:** {m2.identified_high_reward_context}",
        f"- **Guidance:** {m2.monthly_return_guidance}",
        f"- **Psychology:** {m2.psychology_note}",
        f"- **Loss mitigation:** {m2.loss_mitigation_note}",
        f"- **Trap note:** {m2.trap_pattern}",
        f"- **Low-risk frame:** {fr.flag} ({fr.reason}) — not a session ticket",
        "",
        "Month 2 describes risk framing. It does not select an M9 candidate or size a position.",
        "",
    ]
    return lines


def _month3_lines(c: DayContext) -> list:
    m3 = getattr(c, "month3", None)
    lines = ["## Month 3 (ICT next setup)", ""]
    if not m3:
        lines += ["- not attached", ""]
        return lines
    ns = m3.next_setup
    lines += [
        f"- **Timeframe:** {m3.selected_timeframe}",
        f"- **IOF:** {m3.institutional_order_flow}",
        f"- **Sponsorship:** {m3.institutional_sponsorship}",
        f"- **Structure:** {m3.institutional_structure}",
        f"- **Macro→micro:** {m3.macro_to_micro}",
        f"- **Trap note:** {m3.trap_pattern}",
        f"- **Anticipated setup:** {m3.anticipated_setup}",
        f"- **Next setup:** {ns.flag} ({ns.reason}) — not a session ticket",
        "",
        "Month 3 describes institutional context and anticipation. It does not select an M9 candidate.",
        "",
    ]
    return lines


def _month4_lines(c: DayContext) -> list:
    m4 = getattr(c, "month4", None)
    lines = ["## Month 4 (ICT arrays)", ""]
    if not m4:
        lines += ["- not attached", ""]
        return lines
    kinds = [a.kind for a in (m4.arrays or ()) if a.kind != "none"] or ["none"]
    so = m4.array_opportunity
    lines += [
        f"- **Catalog:** {', '.join(kinds)}",
        f"- **Pattern note:** {m4.pattern_note}",
        f"- **Rates:** {m4.interest_rate_effects}",
        f"- **Array opportunity:** {so.flag} ({so.reason}) — not a session ticket",
        "",
        "Month 4 describes the PD-array catalog. It does not select an M9 candidate.",
        "",
    ]
    return lines


def _month5_lines(c: DayContext) -> list:
    m5 = getattr(c, "month5", None)
    lines = ["## Month 5 (ICT position)", ""]
    if not m5:
        lines += ["- not attached", ""]
        return lines
    qs = m5.quarterly_shift
    ip = m5.ipda_window
    of_ = m5.open_float
    sw = m5.institutional_swing
    so = m5.position_opportunity
    lines += [
        f"- **Quarterly shift:** {qs.state} lookback={qs.lookback_months} {qs.direction}",
        f"- **IPDA:** {ip.days}",
        f"- **Open float:** buy={of_.buy_side} sell={of_.sell_side}",
        f"- **OF pools:** {list(m5.open_float_pools.pool_ids) or 'none'}",
        f"- **Institutional swing:** `{sw.kind}` entry={sw.entry_annotation}",
        f"- **Seasonal:** {m5.confirming.seasonal_tendency}",
        f"- **HTF PD:** {m5.htf_pd.dealing_range_tf} disc={m5.htf_pd.nearest_discount_id} prem={m5.htf_pd.nearest_premium_id}",
        f"- **Setup / entry:** {m5.setup_progression} / {m5.entry_technique}",
        f"- **Position opportunity:** {so.flag} ({so.reason}) — not a session ticket",
        "",
        "Month 5 describes the position. It does not select an M9 candidate.",
        "",
    ]
    return lines


def _month6_lines(c: DayContext) -> list:
    m6 = getattr(c, "month6", None)
    lines = ["## Month 6 (ICT swing)", ""]
    if not m6:
        lines += ["- not attached", ""]
        return lines
    rf = m6.risk_frame
    md = m6.million_dollar_swing
    so = m6.swing_opportunity
    lines += [
        f"- **Market selection:** {m6.market_selection.state}",
        f"- **HTF draw:** {m6.htf_draw}",
        f"- **Swing family:** `{m6.swing_family}`",
        f"- **Sequential pattern:** `{m6.sequential_pattern.name}` ({m6.sequential_pattern.state})",
        f"- **Risk:** stop={rf.stop_reference} target={rf.target_reference} frame={rf.reward_frame}",
        f"- **Million-Dollar:** {md.state} missing={list(md.missing)}",
        f"- **Swing opportunity:** {so.flag} ({so.reason}) — not a session ticket",
        "",
        "Month 6 describes the swing. It does not select an M9 candidate.",
        "",
    ]
    return lines


def _month7_lines(c: DayContext) -> list:
    m7 = getattr(c, "month7", None)
    lines = ["## Month 7 (ICT week)", ""]
    if not m7:
        lines += ["- not attached", ""]
        return lines
    dr = m7.dealing_range
    wp = m7.ict_weekly_profile
    tm = m7.manipulation_template
    sw = m7.swing_ticket
    lines += [
        f"- **Dealing range:** {dr.from_array_id} ({dr.from_tf}) → {dr.to_array_id} ({dr.to_tf}) {dr.direction}",
        f"- **IPDA:** {m7.ipda_window.days}",
        f"- **ICT weekly profile:** `{wp.name}` ({wp.state})",
        f"- **Manipulation template:** `{tm.name}`",
        f"- **LRLR:** {m7.lrlr.state}",
        f"- **Intraweek contrary:** {m7.intraweek_contrary.state}",
        f"- **OSOK opportunity:** {m7.osok_opportunity.flag} ({m7.osok_opportunity.reason}) — not a session ticket",
        f"- **Swing ticket:** {sw.id if sw else 'none'}",
        "",
        "Month 7 describes the week. It does not select an M9 candidate.",
        "",
    ]
    return lines


def _month8_lines(c: DayContext) -> list:
    m8 = getattr(c, "month8", None)
    lines = ["## Month 8 (ICT day)", ""]
    if not m8:
        lines += ["- not attached", ""]
        return lines
    td = m8.ict_true_day
    cb = m8.cbdr
    g = m8.london_session_gate
    pr = m8.daily_extreme_projection
    ov = m8.htf_entry_overlap
    lines += [
        f"- **True day:** clock `{td.clock}` anchor `{td.day_anchor}`",
        f"- **Windows:** Asian {td.asian} · London KZ {td.london_kz} · NY AM {td.ny_am} · London Close {td.london_close} · CBDR {td.cbdr_window}",
        f"- **CBDR:** {cb.height_pips} pips · {cb.classification} · classic={cb.daytrade_classic} (`{cb.origin}`)",
        f"- **Asian height:** {m8.asian_height_pips} pips",
        f"- **London gate:** allowed={g.allowed} reason={g.reason} (`{g.origin}`)",
        f"- **ICT London profile:** `{m8.ict_london_profile}`",
        f"- **Projection:** draw={pr.draw} selected={pr.selected_level} source={pr.source_range} (`{pr.origin}`)",
        f"- **SD levels:** {list(pr.sd_levels)}",
        f"- **Day-trade opportunity flag:** {m8.daytrade_opportunity} (not a session ticket)",
        f"- **HTF overlap:** present={ov.present} {ov.array_id} {ov.timeframe} {ov.relationship}",
        "",
        "Month 8 describes the day. It does not select an M9 candidate.",
        "",
    ]
    return lines


def render_briefing(state: MarketState, candidates, ftn=None) -> str:
    c = state.context
    s = c.sentiment
    ic = c.pair_institutional
    dxy = c.dxy or {}
    wr = s.indicator
    lines = [
        f"# Month-9 DTR briefing — {c.symbol} {c.date}",
        "",
        f"**Mode:** paper  ",
        f"**Focus pair:** {c.focus_pair}  ",
        f"**Last:** {c.last}  ",
        f"**Snapshot:** `{state.fingerprint}`",
        "",
        "This briefing is reconstructed from Market State evidence.",
        "It does not read an expected-winner file.",
        "",
        "## Market State",
        "",
        f"- **Sentiment:** {s.direction} / expected delivery {_chip(s.expected_delivery)}",
        f"- **Williams %R(10) 15m:** {wr.value} ({wr.state})",
        f"- **Reference open:** {s.reference_open} = {(c.opens or {}).get(s.reference_open, 'n/a')}",
        f"- **Asian range:** {s.asian_range}",
        f"- **Liquidity probe preferred:** {s.liquidity_probe.preferred_side}",
        f"- **Liquidity probe observed:** {s.liquidity_probe.observed_side}",
        f"- **Judas side:** {s.judas_side}",
        f"- **PD-array reaction:** {(s.reaction or {}).get('pd_array_reaction')}",
        f"- **HTF sponsorship:** daily={ic.sponsorship.daily} 4H={ic.sponsorship.h4} weekly={ic.sponsorship.weekly}",
        f"- **Daytrade IOF:** daily={ic.daytrade_iof.daily} 4H={ic.daytrade_iof.h4} 60m={ic.daytrade_iof.m60}",
        f"- **Daytrade state:** {ic.state} / {ic.confidence} {list(ic.notes)}",
        f"- **DXY relationship:** {dxy.get('relationship')} from {dxy.get('from')}",
        f"- **Profile:** {c.profile} (`hermes_interpretation`)",
        f"- **Origin PD:** {c.origin_pd_array}",
        f"- **Target arrays:** {', '.join(c.opposing_target_arrays) or '—'}",
        "",
    ]
    lines += _month1_lines(c)
    lines += _month2_lines(c)
    lines += _month3_lines(c)
    lines += _month4_lines(c)
    lines += _month5_lines(c)
    lines += _month6_lines(c)
    lines += _month7_lines(c)
    lines += _month8_lines(c)
    lines += _month10_lines(c)
    lines += _month11_lines(c)
    lines += _month12_lines(c)
    lines += _charter_lines(c)
    lines += [
        "## Scenarios",
        "",
        f"- **Primary:** {(c.scenarios or {}).get('primary', '—')}",
        f"- **Contrary:** {(c.scenarios or {}).get('contrary', '—')}",
        "",
        "## FTN objectives (annotation only)",
        "",
    ]
    ftn = ftn or {}
    four = ftn.get("four") or []
    if four:
        lines.append(f"- Family used: `{ftn.get('family')}`  bias={ftn.get('bias')}")
        for lv in four:
            lines.append(f"- L{lv['index']} {lv['name']} `{lv['price']:.5f}`")
        lines.append("")
        lines.append("These are projections/targets. They do not create an entry ticket.")
    else:
        lines.append("- No four-count (missing previous_day or last).")
    lines += [
        "",
        "## Calendar / opens",
        "",
    ]
    if c.calendar:
        for ev in c.calendar:
            lines.append(f"- {ev.get('when')} {ev.get('pair')} {ev.get('impact')} ({ev.get('killzone')})")
    else:
        lines.append("- none / watchlist path")
    lines += [
        "",
        f"- 0 GMT: {(c.opens or {}).get('gmt0')}",
        f"- NY midnight: {(c.opens or {}).get('ny_midnight')}",
        "",
        "## Candidate set",
        "",
        "| Module | State | Eligible | Reason | Origin |",
        "|--------|-------|----------|--------|--------|",
    ]
    selected = None
    for cand in candidates:
        lines.append(
            f"| {cand.module} | `{cand.state}` | {cand.eligible} | {cand.reason} | `{cand.origin}` |"
        )
        if cand.state == "selected":
            selected = cand
    lines += [
        "",
        "## Arbitration",
        "",
        "- Policy: `REV_preempts_CONSO_when_HTF_turn_confirmed` (`hermes_governance`)",
        "- This is conflict resolution, not a claim that REV is a better strategy.",
        "",
    ]
    if selected:
        lines.append(f"**Selected for paper ticket path:** `{selected.module}` — {selected.reason}")
        lines.append("")
        if c.session_ticket:
            lines.append("")
            lines.append(
                f"**session_ticket already set:** `{c.session_ticket.id}` "
                f"({c.session_ticket.module}). No second entry this session. (`hermes_governance`)"
            )
        else:
            lines.append("")
            lines.append("MINT handoff remains paper-only. Tickets ≠ orders.")
    else:
        lines.append("**No entry ticket.** Research log only.")
    lines += [
        "",
        "## Evidence used (raw)",
        "",
        f"```json\n{__import__('json').dumps(c.evidence, indent=2)}\n```",
        "",
        "---",
        "",
        "*Generated by ftn brief. Gold/expected files are not inputs.*",
        "",
    ]
    return "\n".join(lines)


def brief_from_fixture(path: str | Path) -> tuple[MarketState, tuple, str]:
    ctx = attach_ticket(build_context(path))
    prior = ctx.session_ticket
    state = freeze_market_state(ctx)
    cands = evaluate_candidates(state)
    ftn = annotate_ftn(state)
    selected = next((c for c in cands if c.state == "selected"), None)
    if selected and prior is None:
        persist_ticket(ctx, selected.module)
        ctx = attach_ticket(ctx)
        state = freeze_market_state(ctx)
    md = render_briefing(state, cands, ftn)
    write_handoff(state, cands, ftn)
    write_draft(build_handoff(state, cands, ftn))
    return state, cands, md, ftn
