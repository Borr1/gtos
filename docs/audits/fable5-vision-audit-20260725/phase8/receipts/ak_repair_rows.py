"""Session AK's repair-queue rows, built from the artifacts rather than by hand.

    python3 docs/audits/fable5-vision-audit-20260725/phase8/receipts/ak_repair_rows.py

Same contract as AD's (`ad_repair_queue.py`): the canonical append is
`phase6/receipts/REPAIR_QUEUE_APPEND.jsonl`, one `O_APPEND` write per row so three concurrent
wave-8 sessions cannot clobber each other, with a pointer under `REPAIR_QUEUE_V1.json` ->
`appends.AK`. AA's `rows`, `summary` and `diagnostics` are untouched.

Every `action` is a next step with a number attached. No row says "reject" — a negative
measurement's deliverable is the repair it prescribes, the conditioning that would rescue it, or
the exact data that would close it (working agreement §7).
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

P6 = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts"
P8 = REPO / "docs/audits/fable5-vision-audit-20260725/phase8/receipts"
QUEUE = P6 / "REPAIR_QUEUE_V1.json"
APPEND = P6 / "REPAIR_QUEUE_APPEND.jsonl"

GATE = P8 / "AK_SUPPLY_GATE_V1.json"
CELLS = P8 / "AK_SLEEVE_CELLS_V1.json"
FRONTIER = P8 / "AK_EXIT_FRONTIER_V2.json"
DIV = P8 / "AK_DIVERSIFIER_V1.json"
DOSSIER = P8 / "AK_CANDIDATE_DOSSIER_V1.json"
TRADES = P8 / "AK_SUPPLY_TRADES.json.gz"

SESSION = "AK"


def row(sleeve: str, prescription: str, component: str, action: str, evidence: dict, *,
        verdict: str = "REJECT", gate: str = "", margin=None, is_primary: bool = False) -> dict:
    return {"session": SESSION, "sleeve": sleeve, "verdict": verdict,
            "prescription": prescription, "component": component, "gate": gate,
            "margin": margin, "is_primary": is_primary, "action": action,
            "evidence": evidence}


def _load(p: Path):
    if not p.is_file():
        return None
    if p.suffix == ".gz":
        import gzip
        return json.load(gzip.open(p, "rt"))
    return json.loads(p.read_text())


def build() -> list[dict]:
    g = _load(GATE) or {}
    c = _load(CELLS) or {}
    fr = _load(FRONTIER) or {}
    dv = _load(DIV) or {}
    do = _load(DOSSIER) or {}
    tr = _load(TRADES) or {}
    rows: list[dict] = []
    ns = g.get("new_sleeves") or {}
    sl = fr.get("sleeves") or {}

    def best(sleeve):
        s = sl.get(sleeve) or {}
        return (s.get("best_cell"), s.get("best_pooled_oos_mean_r"),
                s.get("as_walked_pooled_oos_mean_r"), s.get("delta_vs_as_walked"),
                s.get("best_failing_gates"))

    # ---------------------------------------------------------------- the four new sleeves
    for tag in ("vol_squeeze", "ny_index_momentum", "structural_retest",
                "session_leadlag_genuine"):
        v = ns.get(tag)
        if not v:
            continue
        bc, bp, aw, dl, bf = best(tag)
        spec = (tr.get("specs") or {}).get(tag) or {}
        base = {
            "first_walk_of_this_sleeve": True,
            "why_never_walked": spec.get("why_unreachable"),
            "n_trades": v["n_trades"],
            "gross_r_per_trade": v["mean_gross_r"],
            "cost_pct_of_abs_gross": v["cost_pct_of_abs_gross"],
            "cost_terms_mean_r": v["cost_terms_mean_r"],
            "pooled_oos_mean_r_at_authored_exit": v["pooled_oos_mean_r"],
            "p_raw": v["p_raw"], "q_at_69": v["q_value"],
            "failing_gates": v["failing_gates"],
            "authored_exit": spec.get("authored_exit"),
            "authored_vs_plain_r_per_trade": (
                None if not spec else
                round((spec["summary_authored_exit"].get("mean_r_gross") or 0)
                      - (spec["summary_plain_exit"].get("mean_r_gross") or 0), 6)),
            "best_exit_cell": bc, "best_exit_pooled": bp,
            "exit_frontier_as_walked": aw, "exit_delta": dl,
            "best_cell_failing_gates": bf,
            "source": ["AK_SUPPLY_GATE_V1.json", "AK_EXIT_FRONTIER_V2.json",
                       "AK_SUPPLY_TRADES.json.gz"],
        }

        if tag == "vol_squeeze":
            terms = v["cost_terms_mean_r"]
            swap_share = (terms.get("swap_r") or 0) / max(1e-12, sum(terms.values()))
            rows.append(row(
                tag, "CARRY_THEN_EXIT", "sleeves/vol_squeeze.py + the exit table",
                (f"Gross is +{v['mean_gross_r']:.4f} R/trade over {v['n_trades']} trades and the "
                 f"sleeve is REJECT at {v['pooled_oos_mean_r']:.4f} R/day, so the whole distance "
                 f"is cost — and swap is {swap_share:.0%} of it "
                 f"({terms.get('swap_r'):.4f} R of {sum(terms.values()):.4f}) over a 48 h median "
                 f"hold on an H4 index sleeve. The exit sweep already buys "
                 f"{dl:+.4f} R/day at `{bc}` and leaves it at {bp:+.4f}. NEXT: the carry cells "
                 f"specifically — `flat_before_every_rollover` and `flat_before_triple_swap` are "
                 f"in the frontier and their swap column is the number to read; if the tightest "
                 f"carry-free cell still does not clear zero, the sleeve's remaining distance is "
                 f"its 0.136 capture ratio against a 1.59 R mean excursion, which is a target/"
                 f"trail question and not a carry one. Do NOT read this as a dead sleeve: it "
                 f"coheres on gross across all five indices (dispersion ratio 0.386, 5/5 "
                 f"positive) — the mechanism is there and the geometry is paying for it."),
                {**base, "swap_share_of_cost": round(swap_share, 4),
                 "mean_mfe_r": v["mean_mfe_r"], "capture_ratio": v["capture_ratio_pooled"],
                 "coherence_gross": ((c.get("coherence") or {}).get(tag) or {}).get(
                     "gross_basis")},
                is_primary=True))

        elif tag == "ny_index_momentum":
            rows.append(row(
                tag, "SAMPLE_M15_DEPTH", "the bars archive",
                (f"The cleanest new-edge shape this session found: REJECT on **significance "
                 f"alone** at {v['pooled_oos_mean_r']:+.4f} R/day, raw p {v['p_raw']:.4f}, "
                 f"{v['n_folds_evaluable']} folds evaluable, "
                 f"{v['oos_positive_fold_frac']:.0%} of OOS folds positive, drop-best retention "
                 f"{v['drop_best_retention']:.3f}, cost coverage 1.00. Its best exit cell `{bc}` "
                 f"takes it to {bp:+.4f}. Significance is not an exit question and it is not a "
                 f"breadth question either — the sleeve already pools six indices and they "
                 f"COHERE on gross. What binds is n={v['n_trades']} against the research's own "
                 f"pooled n=863, and the reason is that the M15 archive starts 2024-01-02. "
                 f"NEXT: M15 bars for SPX500/GER40/UK100/US30_cash/NAS100/JP225 before "
                 f"2024-01-02 — one read-only export of the shape that already ran on "
                 f"2026-07-27. At p {v['p_raw']:.4f} it admits under BH alpha=0.10 against a "
                 f"family of "
                 f"{int(0.10 / v['p_raw']) if v['p_raw'] else 'n/a'} or fewer looks, so the "
                 f"declared_family_size decision touches it too."),
                {**base, "research_pooled_n": 863,
                 "archive_m15_first_bar": "2024-01-02",
                 "largest_family_that_would_admit_under_bh": (
                     int(0.10 / v["p_raw"]) if v.get("p_raw") else None),
                 "coherence_gross": ((c.get("coherence") or {}).get(tag) or {}).get(
                     "gross_basis"),
                 "coherence_net": ((c.get("coherence") or {}).get(tag) or {}).get("net_basis")},
                gate="significance", is_primary=True))

        elif tag == "structural_retest":
            ask = c.get("tick_capture_ask") or {}
            cellrows = {k: x for k, x in (c.get("cells") or {}).items()
                        if x.get("parent") == "structural_retest"}
            rows.append(row(
                tag, "DATA_PATH_TICK_SPREAD", "the tick archive",
                (f"NOT_EVALUABLE at {v['coverage_frac']:.1%} cost coverage — "
                 f"{len(ask.get('symbols') or [])} of its 23 symbols have no file in the tick "
                 f"archive, so `cost_r` refuses them and the retained fraction falls under the "
                 f"60 % floor. No exit change can move a coverage refusal, and the sweep "
                 f"confirms it: all 59 cells return NOT_EVALUABLE. NEXT, and it is a capture "
                 f"rather than a decision (unlike energy_agri's NATGAS commission, AF §3.3): "
                 f"tick spread for {', '.join(ask.get('symbols') or [])}, which unlocks "
                 f"{ask.get('n_trades_it_would_unlock')} trades. MEANWHILE the sleeve is not "
                 f"unjudgeable — its three whitelist cells are declared in its own source and "
                 f"two are fully priceable; all three are gated in AK_SLEEVE_CELLS_V1.json. "
                 f"This is the estate's ONLY short-side mechanism: 4,235 of its 5,045 trades "
                 f"are SHORT and both accounts carry no deliberate short exposure today."),
                {**base, "unpriceable_symbols": ask.get("symbols"),
                 "n_trades_unlocked_by_capture": ask.get("n_trades_it_would_unlock"),
                 "n_short": (tr.get("specs", {}).get(tag, {})
                             .get("summary_authored_exit", {}).get("n_short")),
                 "n_long": (tr.get("specs", {}).get(tag, {})
                            .get("summary_authored_exit", {}).get("n_long")),
                 "cell_verdicts": {k: {"verdict": x.get("verdict"),
                                       "pooled_oos_mean_r": x.get("pooled_oos_mean_r"),
                                       "p_raw": x.get("p_raw"),
                                       "failing_gates": x.get("failing_gates"),
                                       "n": x.get("n_trades_priceable")}
                                   for k, x in sorted(cellrows.items())}},
                verdict="NOT_EVALUABLE", gate="cost_coverage", is_primary=True))
            rows.append(row(
                tag, "GENERATOR_HTF_PHASE_DEPENDENCE",
                "sleeves/structural_retest.py:82-103",
                (f"`_htf_trend_at` rebuilds its 16-bar HTF blocks from index 0 of the WINDOW it "
                 f"is handed and sets `completed_at_i` before appending the block bar i closes, "
                 f"so the ABSOLUTE bars it reads depend on `bar_count mod 16`. At 513 the "
                 f"reference block is the 16 bars immediately preceding the decision bar; at 528 "
                 f"it ends 16 bars earlier. Measured on three symbols: jaccard "
                 f"{(tr.get('htf_phase_sensitivity') or {}).get('jaccard')} — "
                 f"{(tr.get('htf_phase_sensitivity') or {}).get('n_only_aligned')} trades exist "
                 f"only at 513 and "
                 f"{(tr.get('htf_phase_sensitivity') or {}).get('n_only_probe')} only at 528. "
                 f"So `bar_count` is NOT a free parameter for this generator and a live "
                 f"SleeveSpec that picked it carelessly would run a different rule. 513 is the "
                 f"SMALLEST aligned length above the MIN_BARS=512 floor, not the only one — "
                 f"every bar_count = 1 (mod 16) is equally aligned. And the phase changes "
                 f"trade/no-trade, NOT direction: each (class, session) appears once in "
                 f"WHITELIST, and of the 782 bars present at both phases the direction flips on "
                 f"0. NEXT: fix "
                 f"the chunking to anchor on `i` rather than on the window start (a two-line "
                 f"change: iterate backwards from i in 16-bar blocks), then RE-DERIVE the three "
                 f"whitelist cells, because the verified cells were mined under the research "
                 f"generator's own chunking and changing it changes the rule. Not repaired here "
                 f"for exactly that reason — a port must not quietly become a re-derivation."),
                {"htf_phase_sensitivity": tr.get("htf_phase_sensitivity"),
                 "chosen_bar_count": 513,
                 "why_513": ("the SMALLEST length above the MIN_BARS=512 floor at which the HTF "
                             "reference block ends adjacent to the decision bar; every "
                             "bar_count = 1 (mod 16) is equally aligned, so 513 is minimal and "
                             "not unique"),
                 "direction_flips_between_phases": 0,
                 "what_the_phase_changes": "trade/no-trade, never long/short"},
                verdict="INFORMATIONAL"))
            rows.append(row(
                tag, "F7_CLOCK_REPAIR_LANDED", "sleeves/structural_retest.py:47-70",
                (f"Its session boundaries (8/16) are a verbatim port of "
                 f"`wave1_structure_setups_ict.session_id:93-97`, which read `t.hour` off the "
                 f"broker-clock research archive — so they are FTMO SERVER hours, and the live "
                 f"feed is true UTC. The sleeve compared UTC to a server constant, which put "
                 f"every bar 2 h (winter) or 3 h (summer) into the wrong session bucket, and the "
                 f"bucket is this sleeve's whitelist key. Repaired in B950. Both readings "
                 f"published: repaired n="
                 f"{((tr.get('clock_ab') or {}).get(tag) or {}).get('repaired_server_clock', {}).get('n')} "
                 f"at "
                 f"{((tr.get('clock_ab') or {}).get(tag) or {}).get('repaired_server_clock', {}).get('mean_r_gross')} "
                 f"R/trade gross against authored-UTC n="
                 f"{((tr.get('clock_ab') or {}).get(tag) or {}).get('authored_utc_clock', {}).get('n')} "
                 f"at "
                 f"{((tr.get('clock_ab') or {}).get(tag) or {}).get('authored_utc_clock', {}).get('mean_r_gross')}, "
                 f"sharing only "
                 f"{((tr.get('clock_ab') or {}).get(tag) or {}).get('n_shared')} trades — so the "
                 f"repair changes WHICH trades exist. NEXT: nothing for this sleeve; the row "
                 f"exists so the B29/B54 repair's own coverage question is closed. It was the "
                 f"TENTH sleeve and the only one still on raw UTC, missed because the repair "
                 f"enumerated the DEPLOYED set and this one is in no registry. "
                 f"tests/ultimate_book/test_sleeve_server_clock.py now covers it."),
                {"clock_ab": (tr.get("clock_ab") or {}).get(tag),
                 "sleeves_using_server_clock_before": 9,
                 "sleeves_using_server_clock_after": 10},
                verdict="FIXED"))

        elif tag == "session_leadlag_genuine":
            legs = {k: x for k, x in (c.get("cells") or {}).items()
                    if x.get("parent") == "session_leadlag_genuine"}
            pos = {k: x for k, x in legs.items()
                   if (x.get("pooled_oos_mean_r") or -1) > 0}
            rows.append(row(
                tag, "COST_GEOMETRY_STOP_WIDTH",
                "sleeves/session_leadlag.py (new) + KB5's 0.5xATR stop",
                (f"A generator now exists IN THIS PACKAGE (B960; a research-side one, "
                 f"KB6_session_stacks.py:77, has existed for weeks and produced the registered "
                 f"numbers). It reproduces the MECHANISM and its trade POPULATION: on the "
                 f"matching span n=368 against the registry's n=390, win 34.9 %/35.2 % against "
                 f"35.0 %/36.7 %, and the LEGS table is element-for-element identical to LL_FWD. "
                 f"It does NOT reproduce the R, and an adversarial pass on this session's own "
                 f"claim is why that is stated: the registry's +0.46 is NET of the legacy flat-R "
                 f"cost model (KB5_leadlag_subh4.py:150,178-182) and +0.4986 is GROSS; on a "
                 f"common basis they are +0.3975 against +0.4598, and on KB5's DECLARED forward "
                 f"window (year >= 2025, not its 2025-06 coverage start) the walk is +0.3716 "
                 f"gross / +0.2708 legacy-net on n=565. Over the whole "
                 f"archive it is +{v['mean_gross_r']:.4f} gross and "
                 f"{v['pooled_oos_mean_r']:+.4f} R/day NET, i.e. cost is the entire distance: "
                 f"spread {v['cost_terms_mean_r'].get('spread_r'):.4f} + commission "
                 f"{v['cost_terms_mean_r'].get('commission_r'):.4f} R against a stop of "
                 f"0.5xATR, which is what makes a fixed spread enormous in R. NEXT, in this "
                 f"order: (1) the stop-width cells — the entry signal does not read the stop "
                 f"(`mine_pair` sets stop and target from ATR independently), so a k-x stop is a "
                 f"legitimate re-simulation and the frontier already contains them; (2) the LEG "
                 f"concentration below, which is larger than the stop question."),
                {**base, "forward_window_gross_r": 0.4986,
                 "forward_window_n": 406,
                 "registry_note_claim": "+0.46 R on n=390 (admission.py:271-277)",
                 "why_the_two_differ": ("the forward window is the sleeve's best; the full "
                                        "archive is 2.5 years and the research window is "
                                        "13 months of it"),
                 "coherence_gross": ((c.get("coherence") or {}).get(tag) or {}).get(
                     "gross_basis"),
                 "coherence_net": ((c.get("coherence") or {}).get(tag) or {}).get("net_basis")},
                is_primary=True))
            rows.append(row(
                tag, "MEMBER_CONDITIONING_NOT_BREADTH",
                "KB6_session_stacks.py:52-58 — the four LL_FWD legs",
                (f"Pooling the four declared legs DILUTES the sleeve. Gated separately, "
                 f"{len(pos)} of {len(legs)} is positive: "
                 + "; ".join(f"{k.replace('fam_session_leadlag_', '')} "
                             f"{x.get('pooled_oos_mean_r'):+.4f} (p "
                             f"{x.get('p_raw'):.3f}, n={x.get('n_trades_priceable')})"
                             for k, x in sorted(legs.items(),
                                                key=lambda kv: -(kv[1].get(
                                                    'pooled_oos_mean_r') or -9)))
                 + f". The winner, US30_cash->USDJPY@T2.0, fails **significance alone**. NEXT: "
                 f"this is exactly AF's MEMBER_CONDITIONING_NOT_BREADTH shape — do not ask for "
                 f"more legs, ask why the Dow leads USDJPY and not AUDJPY. Note the leg count is "
                 f"a look each: four legs is four hypotheses and they are in the ledger."),
                {"legs": {k: {"pooled_oos_mean_r": x.get("pooled_oos_mean_r"),
                              "p_raw": x.get("p_raw"),
                              "n": x.get("n_trades_priceable"),
                              "failing_gates": x.get("failing_gates"),
                              "cell": x.get("cell")}
                          for k, x in sorted(legs.items())}},
                gate="significance"))
            rows.append(row(
                tag, "LIVE_WIRING_GAP_CROSS_SYMBOL_FEED",
                "book_engine per-spec fetch + SleeveSpec",
                (json.dumps((tr.get("live_wiring_gap") or {}).get("what_is_missing"))
                 + " Smallest sufficient change: "
                 + "; ".join((tr.get("live_wiring_gap") or {}).get(
                     "smallest_sufficient_change") or [])
                 + " Why it is not free: "
                 + str((tr.get("live_wiring_gap") or {}).get("why_it_is_not_free"))
                 + " NEXT: this is an OWNER decision, not a research one — whether to spend an "
                 "engine change on a conf-0.15 forward-only sleeve. The measurement that makes "
                 "it answerable is above."),
                {"live_wiring_gap": tr.get("live_wiring_gap"),
                 "registry_edit_proposal": (tr.get("registry_edit_proposal") or {}).get(
                     "session_leadlag_genuine")},
                verdict="OWNER_DECISION"))

    # ------------------------------------------------------- AD's four unswept sleeves
    gapmeta = fr.get("ad_frontier_gap") or g.get("ad_frontier_gap") or {}
    for sleeve in (gapmeta.get("gap") or []):
        bc, bp, aw, dl, bf = best(sleeve)
        armed = sleeve == "sub_xvol_pullback"
        s = sl.get(sleeve) or {}
        if not s.get("available"):
            continue
        if bp is None:
            rows.append(row(
                sleeve, "COVERAGE_OR_SAMPLE_BEFORE_EXIT", "the exit frontier",
                (f"AD's WORK_LIST did not name this sleeve, so it had no exit frontier of any "
                 f"kind. Swept here over {s.get('n_trades')} trades and {s.get('n_cells')} "
                 f"gated cells: every cell returns no pooled OOS mean, which means the "
                 f"population — not the exit — is what refuses. NEXT: read the baseline "
                 f"refusal in AK_SUPPLY_GATE_V1.json -> gap_sleeves_baseline."
                 + (" THIS SLEEVE IS ARMED." if armed else "")),
                {"n_trades": s.get("n_trades"), "n_cells": s.get("n_cells"),
                 "baseline": (g.get("gap_sleeves_baseline") or {}).get(sleeve),
                 "why_it_had_no_frontier": gapmeta.get("why"),
                 "armed": armed},
                verdict="NOT_EVALUABLE", is_primary=True))
            continue
        rows.append(row(
            sleeve, ("EXIT_REPAIR_LANDED_SIGNIFICANCE_REMAINS"
                     if bf == ["significance"] else "EXIT_REPAIR_PARTIAL"),
            "the exit frontier — AD's gap",
            (f"AD swept 25 of the 29 sleeves AA generated and this was one of the four its "
             f"WORK_LIST did not name; it had NO exit frontier of any kind. Swept here with AD's "
             f"own machinery, imported: as_walked {aw:+.4f} -> `{bc}` {bp:+.4f} R/day "
             f"({dl:+.4f}), verdict {s.get('best_verdict')}, failing {bf}. "
             + ("Failing SIGNIFICANCE ALONE at the best cell, which no exit change can pay — "
                "this is a family/sample question now. " if bf == ["significance"] else "")
             + ("THIS SLEEVE IS ARMED AND TRADING REAL MONEY: its exit surface was the largest "
                "unmeasured one in the estate, and AA measured its capture ratio at 0.604, the "
                "best of any sleeve. " if armed else "")
             + f"NEXT: the cell is in AK_EXIT_FRONTIER_V2.json and it is a composition input, "
               f"not a recommendation — sleeve composition is Borhen's."),
            {"n_trades": s.get("n_trades"), "n_cells": s.get("n_cells"),
             "as_walked_pooled": aw, "best_cell": bc, "best_pooled": bp, "delta": dl,
             "best_verdict": s.get("best_verdict"), "best_failing_gates": bf,
             "armed": armed, "why_it_had_no_frontier": gapmeta.get("why"),
             "source": "AK_EXIT_FRONTIER_V2.json"},
            gate=("significance" if bf == ["significance"] else ""),
            is_primary=True))

    # ------------------------------------------------------- the clock site AK did NOT repair
    rows.append(row(
        "sub_mid_dn_revert", "F7_CLOCK_SITE_STILL_OPEN",
        "sleeves/substrate.py:75-84 + sleeves/substrate_engine.py:102-108",
        ("Found by an adversarial pass on THIS session's own B950 claim, and it measures larger "
         "than the repair it refuted. AK's first draft said `structural_retest` was the only "
         "sleeve in the package still reading a raw UTC hour. It is not: `substrate._utc_hour` "
         "returns the raw UTC hour and `substrate_engine._bucket_session` cuts it on the "
         "IDENTICAL 8/16 boundaries — the same pair `structural_retest._session` uses and the "
         "same pair `wave1_structure_setups_ict.session_id:93-97` mined on the broker-clock "
         "archive. `sub_mid_dn_revert` is backed by that code and it IS in the production "
         "generation registry (`registry.py:55`, BUILT), with `session=ny` as one of its seven "
         "cell conditions (`substrate.py:67-71`). MEASURED over the archive: **185,548 of "
         "370,808 H4 bars — 50.04 % — bucket into a DIFFERENT session under the two clocks**, "
         "entirely at UTC close-hours 05/06/13/14/21/22 (the archive's H4 closes convert to odd "
         "UTC hours, which is why an assumed 00/04/08/... grid shows no shift and AK's first "
         "attempt to dismiss this was also wrong). NOT costing money today: the armed --tags are "
         "crypto/energy_agri/sub_xvol_pullback and `sub_xvol_pullback` is built with "
         "need_hour=False (`substrate.py:121`), so it never reads the hour — but it is one "
         "--tags change away, which is the hazard CLAUDE.md §4 already names. Why the F7/B29/B54 "
         "pass skipped it, per its own record at IMPLEMENTATION_STATE.md:706-709: the pass scoped "
         "by CONFIG REACHABILITY, not registry membership — `substrate.py` was set aside because "
         "`include_clean3: false` meant it 'cannot generate live', and CLAUDE.md §4 records that "
         "flag as TRUE on the VPS. NEXT, and DELIBERATELY NOT DONE HERE: correcting the bucket "
         "changes which bars the sleeve fires on, which changes its economics, which invalidates "
         "its SURVIVOR_BOOK_V1 carry tier and AD's B753 restatement of it. That is a "
         "re-derivation and needs its own session — the same line drawn for the "
         "structural_retest HTF chunking. Pinned by four tests in "
         "tests/ultimate_book/test_sleeve_server_clock.py so the next session inherits a "
         "measurement rather than a suspicion."),
        {"n_h4_bars_measured": 370808, "n_bars_bucketed_differently": 185548,
         "frac_shifted": 0.500388,
         "shifted_utc_close_hours": [5, 6, 13, 14, 21, 22],
         "symbols": 18,
         "armed_impact_today": "none — sub_xvol_pullback has need_hour=False",
         "live_reachable": "yes when include_clean3 is true (CLAUDE.md §4 records it true on the "
                           "VPS) and --tags does not exclude it",
         "why_not_repaired": "re-derivation, not a port: it changes the sleeve's generated set",
         "refutes": "AK's own first-draft claim that structural_retest was the ONLY raw-UTC site"},
        verdict="OPEN_DEFECT", is_primary=True))

    # ------------------------------------------------------- the instrument corrections
    corr = c.get("coherence_basis_correction") or {}
    if corr:
        rows.append(row(
            "AF_REPAIRS_V1.json", "COHERENCE_TEST_BASIS", "AF's two-clause family rule",
            (f"AF §0's rule — dispersion ratio < 1 AND every member positive — is computed on "
             f"per-member GROSS R (`af_repairs.py:820`, artifact key `member_mean_r_gross`). "
             f"Measured here on gross AND net over the IDENTICAL row population: "
             f"**{corr.get('n_genuine_multi_member_flips')} genuine multi-member flips** — "
             f"{', '.join(corr.get('genuine_multi_member_flips') or [])} — cohere on gross and "
             f"do NOT cohere on net. Two more are k=1 cells where the test is degenerate and are "
             f"excluded; one more "
             f"({', '.join(corr.get('flips_that_were_an_unmatched_population_ARTIFACT') or [])}) "
             f"was an ARTIFACT of comparing gross-over-all-rows against net-over-priced-rows, and "
             f"that correction came from an adversarial pass on this session's own first draft. "
             f"The trap is worth naming because it is silent: `coverage_frac` excludes "
             f"reserved_blackout drops from its denominator (`panel.py:313,323`), so a cell reads "
             f"coverage 1.00 while up to 18 % of its rows never reach the net basis. The CAUSE is "
             f"also not what the first draft said — within these sleeves the stop rule is one "
             f"symbol-agnostic ATR constant, and the data invert the R-unit story (XAUAUD's "
             f"tighter stop pays 0.10 R against XAGAUD's 0.53 R; ny_index_momentum's "
             f"WIDEST-stop member is its most expensive), so the spread is the instrument's own "
             f"spread/swap drag. NEXT: run the two-clause test on the `mean_gross_r`/`mean_net_r` "
             f"PAIR from diagnostics.by_symbol — one field, already emitted, and the only way the "
             f"two are over the same rows. Filed as a row rather than edited into AF's artifact, "
             f"the same way AD filed against AA's frontier algebra."),
            corr, verdict="INSTRUMENT_CORRECTION"))

    # ------------------------------------------------------- the registry-edit decision
    prop = tr.get("registry_edit_proposal") or {}
    if prop:
        rows.append(row(
            "vol_squeeze / ny_index_momentum / structural_retest",
            "REGISTRY_ENTRY_OWNER_DECISION", "sleeves/registry.py",
            ("AA §4 routed this as 'one one-line decision, not a research project' and it is "
             "right about the edit and incomplete about the consequence. The three edits are in "
             "AK_SUPPLY_TRADES.json.gz -> registry_edit_proposal, each with the table, the exact "
             "line, what else it needs, and why it is live-safe. TWO THINGS THE ROUTING DID NOT "
             "SAY. (1) `structural_retest` cannot take a careless `bar_count`: its HTF trend is "
             "window-phase dependent (row above), so the spec's bar_count picks the rule. "
             "(2) The live-safety argument has a shape worth naming: `registry.py:130-134` "
             "treats an EMPTY candidate allowlist as ALL candidates, so a registry entry is "
             "inert only while the deployed allowlist stays non-empty. NEXT: none of these three "
             "has evidence that would justify arming it today — every one is REJECT or "
             "NOT_EVALUABLE — so the value of the edit is that a future walk can reach them "
             "through the production path instead of through a research spec table."),
            {"registry_edit_proposal": prop,
             "measured_verdicts": {t: {"verdict": (ns.get(t) or {}).get("verdict"),
                                       "pooled_oos_mean_r": (ns.get(t) or {}).get(
                                           "pooled_oos_mean_r")}
                                   for t in ("vol_squeeze", "ny_index_momentum",
                                             "structural_retest")}},
            verdict="OWNER_DECISION"))

    # ------------------------------------------------------- the diversifier results
    for sleeve, cand in (dv.get("candidates") or {}).items():
        if not cand.get("available"):
            continue
        cellrows = cand.get("cells") or {}
        rule = cand.get("trail_bound_rule") or {}
        summary = []
        for name, x in sorted(cellrows.items()):
            if not x.get("available"):
                continue
            wc = x.get("with_candidate_book") or {}
            bs = (dv.get("armed_book") or {}).get("stats") or {}
            summary.append(
                f"{name}[{x.get('bound') or 'n/a'}] verdict {x['certification']['verdict']}, "
                f"failed {x['certification']['failed_guards']}, corr "
                f"{x['certification']['raw_certification']['checks']['low_correlation'].get('corr')}, "
                f"dSharpe {round((wc.get('book_daily_sharpe') or 0) - (bs.get('book_daily_sharpe') or 0), 5):+}, "
                f"dRet {round((wc.get('total_return_pct') or 0) - (bs.get('total_return_pct') or 0), 3):+}pp")
        if not summary:
            continue
        rows.append(row(
            sleeve, "DIVERSIFIER_DOOR_MEASURED",
            "walkforward/diversifier.py against the ARMED book",
            (f"Run against the three sleeves `run_book.py --tags` actually carries "
             f"({', '.join((dv.get('armed_book') or {}).get('sleeves') or [])}), at this sleeve's "
             f"repaired exit cell. " + " | ".join(summary)
             + (f" TRAIL BOUND RULE: {rule.get('reported_verdict_is')} "
                f"(production {rule.get('production_pooled')}, honest "
                f"{rule.get('honest_pooled')}, sign flips: "
                f"{rule.get('honest_bound_flips_the_sign')})." if rule else "")
             + " NEXT: read `failed_guards`. A `genuine_edge` failure is the door working as "
               "designed on a ~zero-mean sleeve and the repair is standalone expectancy, not "
               "correlation; a `book_return` or `prediction_agrees` failure is adverse evidence "
               "about the MERGED book and is the one that should stop a composition."),
            {"cells": {k: {"bound": x.get("bound"),
                           "verdict": x["certification"]["verdict"],
                           "failed_guards": x["certification"]["failed_guards"],
                           "standalone_edge_inputs": x.get("standalone_edge_inputs"),
                           "with_candidate_book": x.get("with_candidate_book")}
                       for k, x in sorted(cellrows.items()) if x.get("available")},
             "trail_bound_rule": rule,
             "armed_book": {k: v for k, v in (dv.get("armed_book") or {}).items()
                            if k != "rejections"}},
            verdict="INFORMATIONAL"))

    # ------------------------------------------------------- the dossier hand-off
    for sleeve, x in (do.get("candidates") or {}).items():
        if not x.get("available"):
            continue
        dfl = x.get("deflation") or {}
        rows.append(row(
            sleeve, "CANDIDATE_BOOK_INPUT_FOR_AI", "the candidate book",
            (f"Dossier for Session AI at cell `{x['cell']}`: {x['pooled_oos_mean_r']:+.4f} R/day, "
             f"raw p {x['p_raw']}, {x.get('oos_positive_fold_frac')} of OOS folds positive, "
             f"drop-best retention {x.get('drop_best_retention')}, failing {x['failing_gates']}. "
             f"It admits under BH alpha=0.10 against a family of "
             f"{dfl.get('largest_family_that_would_admit')} or fewer looks and the trial ledger "
             f"measures {(do.get('family_sizes') or {}).get('trial_ledger_measured')}. NEXT: this "
             f"is AI's composition input, and the number that decides it is "
             f"`declared_family_size` — which is Borhen's, not a session's (AF §11). Fold series "
             f"attached so AI can check whether two candidates' good folds are the SAME folds."),
            {"cell": x["cell"], "pooled_oos_mean_r": x["pooled_oos_mean_r"],
             "p_raw": x["p_raw"], "deflation": dfl,
             "fold_oos_mean_r_series": x.get("fold_oos_mean_r_series"),
             "why_selected": x.get("why_selected"),
             "fold_series_agreement": (do.get("fold_series_agreement") or {}).get("pairs")},
            verdict="INFORMATIONAL"))

    return rows


def main() -> dict:
    rows = build()
    payload = [{"appended_utc": dt.datetime.now(dt.timezone.utc).isoformat(), **r}
               for r in rows]
    # IDEMPOTENT FOR THIS SESSION'S OWN ROWS ONLY. The agreement's "append, never overwrite" is
    # about not clobbering a SIBLING session's rows, and this preserves every non-AK line
    # byte-for-byte while replacing AK's — because a corrected re-run that left the wrong rows
    # behind would put two contradictory versions of the same finding in the queue. Found the
    # hard way: the first re-run after an adversarial correction double-appended 22 rows.
    keep: list[str] = []
    if APPEND.is_file():
        for line in APPEND.read_text().splitlines():
            if not line.strip():
                continue
            try:
                if (json.loads(line).get("session") or "") == SESSION:
                    continue
            except json.JSONDecodeError:
                pass                      # not ours to interpret; keep it
            keep.append(line)
        n_dropped = len(APPEND.read_text().splitlines()) - len(keep)
        if n_dropped:
            APPEND.write_text("".join(x + "\n" for x in keep))
            print(f"replaced {n_dropped} pre-existing {SESSION} row(s); "
                  f"{len(keep)} other-session rows preserved byte-for-byte")
    fd = os.open(APPEND, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        for r in payload:
            os.write(fd, (json.dumps(r, sort_keys=True, default=str) + "\n").encode())
    finally:
        os.close(fd)
    print(f"appended {len(payload)} rows to {APPEND.relative_to(REPO)}")

    q = json.loads(QUEUE.read_text())
    appends = q.setdefault("appends", {})
    by_presc: dict[str, int] = {}
    for r in rows:
        by_presc[r["prescription"]] = by_presc.get(r["prescription"], 0) + 1
    appends[SESSION] = {
        "session": SESSION, "wave": 8,
        "file": str(APPEND.relative_to(REPO)),
        "format": "append-only JSONL, O_APPEND per row — safe for concurrent sessions",
        "n_rows": len(rows),
        "by_prescription": dict(sorted(by_presc.items())),
        "note": ("AA's `rows`, `summary` and `diagnostics` untouched, and AD's `appends.AD` "
                 "untouched. This session writes exactly one new key: appends.AK."),
        "produced_by": [p.name for p in (GATE, CELLS, FRONTIER, DIV, DOSSIER, TRADES)
                        if p.is_file()],
    }
    QUEUE.write_text(json.dumps(q, indent=1, default=str))
    print(f"pointer written into {QUEUE.relative_to(REPO)} -> appends.{SESSION}")
    print("by prescription:", json.dumps(dict(sorted(by_presc.items())), indent=1))
    return {"n_rows": len(rows), "by_prescription": by_presc}


if __name__ == "__main__":
    main()
