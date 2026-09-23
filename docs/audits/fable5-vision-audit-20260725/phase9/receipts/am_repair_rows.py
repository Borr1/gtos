"""Append Session AM's repair-queue rows, idempotently.

    python3 docs/audits/fable5-vision-audit-20260725/phase9/receipts/am_repair_rows.py

Idempotent by (session, sleeve, prescription, component): AK's B-block records that its own
repair-row script double-appended when re-run (§7.7), so this one reads the file first and refuses
to add a row whose key is already present, reporting what it skipped.

The queue is append-only and shared with every other session, so nothing here rewrites an existing
row — an AMENDS row is added instead, which is the convention AI used.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO))

QUEUE = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/REPAIR_QUEUE_APPEND.jsonl"
TS = "2026-07-30T12:00:00+00:00"

RECLOCK = HERE / "SUBMID_RECLOCK_V1.json"
ENTRY = HERE / "ENTRY_FRONTIER_H4_V1.json"
ERA = HERE / "ERA_ANCHOR_V2_VALIDATION.json"


def _load(p: Path) -> dict:
    return json.loads(p.read_text()) if p.is_file() else {}


def rows() -> list[dict]:
    rc, en, er = _load(RECLOCK), _load(ENTRY), _load(ERA)
    out: list[dict] = []

    # ---- item 1 -------------------------------------------------------------------------
    ab = rc.get("clock_ab") or {}
    rep = ab.get("server_repaired") or {}
    aut = ab.get("authored_utc") or {}
    sv = (((rc.get("runs") or {}).get("server_repaired") or {}).get("sleeve") or {})
    carry = {k: v for k, v in ((rc.get("carry") or {}).get("rows") or {}).items()
             if k.startswith("server_repaired")}
    out.append({
        "ts": TS, "session": "AM", "sleeve": "sub_mid_dn_revert",
        "component": "src/components/ultimate_book/sleeves/substrate.py",
        "gate": (sv.get("failing_gates") or ["n/a"])[0] if sv else "n/a",
        "prescription": "GENERATION",
        "prescription_in_diagnostics_enum": True,
        "action": (
            "REPAIRED (B1200). `_utc_hour` -> `_session_hour` via `_server_clock.server_hour`: the "
            "8/16 session boundaries were mined on the broker clock, so `session=ny` moved from "
            "server-hour {20, 00} to {16, 20}. This changes WHICH TRADES EXIST, so every published "
            "number for the sleeve was re-derived rather than rescaled — AA's population and "
            "verdict, and AD's B753 carry-tier restatement, were all measured on the wrong clock. "
            "The authored-UTC arm reproduces AA exactly, which is what makes the A/B a measurement "
            "of the clock and of nothing else."),
        "evidence": {
            "n_repaired": rep.get("n"), "n_authored": aut.get("n"),
            "n_shared": ab.get("n_shared"), "jaccard": ab.get("jaccard"),
            "mean_r_gross_repaired": rep.get("mean_r_gross"),
            "mean_r_gross_authored": aut.get("mean_r_gross"),
            "verdict_repaired": sv.get("verdict"),
            "pooled_oos_mean_r_repaired": sv.get("pooled_oos_mean_r"),
            "p_raw_repaired": sv.get("p_raw"),
            "failing_gates_repaired": sv.get("failing_gates"),
            "parity_vs_aa_on_the_authored_arm": (rc.get("parity_vs_aa_authored_arm") or {}).get(
                "trade_keys_identical"),
            "carry_tier_restated": {k: v.get("restated_tier") for k, v in carry.items()},
        },
    })

    out.append({
        "ts": TS, "session": "AM", "sleeve": "sub_mid_dn_revert",
        "component": "src/components/ultimate_book/admission.py:1143-1148,1186-1189,1199",
        "gate": "none",
        "prescription": "GENERATION",
        "prescription_in_diagnostics_enum": True,
        "action": (
            "THE COUPLING CHANNEL MY OWN REPAIR NOTE MISSED, found by an adversarial pass. I claimed "
            "the clock repair 'cannot move the ARMED book because sub_xvol_pullback is need_hour="
            "False'. The mechanism half is verified (48 vs 48 byte-identical xvol intents under both "
            "clocks; `_session_hour` has exactly one caller, `_bucket_session` exactly one). The "
            "CONCLUSION does not follow: `sub_mid_dn_revert`'s firing set DOES change, and it feeds "
            "`n_active_by_day` -> `na` -> `kelly_lite_conviction_multiplier`, applied as "
            "`su_combined = min(su * kelly_mult, OVERLAY_SIZEUP_MAX)` to EVERY unit that day, armed "
            "ones included. kelly_lite/kelly_conservative/kelly_running_count are all true live, so a "
            "bin-edge crossing is a 25-32 % size event on the armed sleeves — AK's B970 hazard, "
            "reached by a different door. Inert today only because of THREE conditions, not one: "
            "include_clean3 (mainline false, host UNVERIFIED), `--tags` can only subset, and this "
            "repair is not on the VPS. Remove any one and the coupling is live."),
        "evidence": {
            "channel": "n_active_by_day -> kelly_lite conviction multiplier -> every unit that day",
            "size_effect_at_a_bin_edge": "25-32 %",
            "xvol_intents_unchanged": "48 vs 48, byte-identical, real-archive A/B",
            "conditions_that_keep_it_inert": ["ultimate_book_include_clean3 false (host UNVERIFIED)",
                                              "run_book.py --tags can only subset",
                                              "B1200 is not carried to the VPS"],
            "prior_art": "AK B970; CLAUDE.md §4 records the same mechanism as a +25.2 % event",
        },
    })
    out.append({
        "ts": TS, "session": "AM", "sleeve": "__estate__",
        "component": "src/research_infra/replay_policy/generation_lineage.py",
        "gate": "none",
        "prescription": "FIDELITY_RECONCILIATION",
        "prescription_in_diagnostics_enum": True,
        "action": (
            "REPAIRED (B1201). `clock_dependent_sleeves()` detects clock OWNERS by scanning for the "
            "literal `_server_clock import`, so a module reaching the clock as "
            "`from . import _server_clock as _sc` is invisible to the live-lineage register — a "
            "`deployed_lineage()` replay would run the REPAIRED clock while claiming to reproduce the "
            "VPS. Import form changed and `substrate` registered with `pre_b1200_utc_hour`. STANDING "
            "HAZARD for the next clock repair: the detector is a source-string match, so it is only as "
            "good as the import style. A behavioural detector (does the module's hour function move "
            "when `_server_clock` is patched?) would not have this hole."),
        "evidence": {
            "detector": "_CLOCK_MARKERS source-string scan",
            "blind_to": "from . import _server_clock as _sc",
            "verified_behaviourally": "mainline server 17 -> ny; deployed UTC 14 -> london; restored",
            "residual": "clock_dependent_sleeves() - DEPLOYED_HELPERS == {session_leadlag, "
                        "structural_retest}, both pre-existing and both fixed on main by b48441e4c",
        },
    })

    # ---- item 2/3 -----------------------------------------------------------------------
    hc = en.get("hour_cost_frontier") or {}
    sub = ((en.get("h4_hour00_subset") or {}).get("subsets") or {})
    h00 = sub.get("hour00") or {}
    ctl = sub.get("control_other_hours") or {}
    out.append({
        "ts": TS, "session": "AM", "sleeve": "__fx_d1_cohort__",
        "component": "entry convention (run_book decision -> fill instant)",
        "gate": "cost_geometry",
        "prescription": "COST_GEOMETRY",
        "prescription_in_diagnostics_enum": True,
        "action": (
            "ONE HOUR, NOT FOUR. The fx hour term is a one-hour spike (16.67x at broker 00, 1.333x "
            "at 01, 1.0 from 02; jpy_fx 12.56x then 1.167x), so a ONE-HOUR delay captures the "
            "great majority of the rollover saving AH priced at four hours — measured exactly on "
            "AH's own 17,888-trade arm-B population, because cost_r is a function of the entry "
            "INSTANT and needs no bar. AH could not see this: the H4 grid has no point between 0 h "
            "and 4 h. The remaining three hours buy the last few percent and pay three more hours "
            "of signal decay, which is what hurt the reversion members. OWNER DECISION, same class "
            "as AH's: the entry convention is a contract."),
        "evidence": {
            "mean_cost_r_by_shift_hours": {k: v.get("mean_total_r")
                                           for k, v in (hc.get("per_shift") or {}).items()},
            "saving_vs_shift_0_r": hc.get("saving_vs_shift_0_r"),
            "fraction_of_the_best_achievable_saving": hc.get(
                "fraction_of_the_best_achievable_saving"),
            "best_shift_hours": hc.get("best_shift_hours"),
            "swap_is_unchanged_at_every_shift": True,
            "frontier_is_not_monotone": ("broker 03 and 08 carry their own session-open premium, so "
                                         "3 h and 8 h are worse than 2 h and 7 h"),
        },
    })
    out.append({
        "ts": TS, "session": "AM", "sleeve": "__h4_fx_cohort__",
        "component": "entry convention (H4 decision bars closing at broker 00)",
        "gate": "cost_geometry",
        "prescription": "COST_GEOMETRY",
        "prescription_in_diagnostics_enum": True,
        "action": (
            "The H4 FX hour-00 subset, with its own hour CONTROL — the same one-bar and two-bar "
            "shift applied to the members' non-hour-00 decision bars. It separates the two effects "
            "AH's D1 design superposed, and they turn out to be independent. COST: entering at "
            "broker 00 pays 0.482 R (48 % of the risk unit); one bar later pays 0.119 R, and an "
            "adversarial decomposition attributes 96.4 % of the control's mirror-image cost RISE to "
            "the hour (hold -0.0002 R, symbol mix nothing, era drift 0.16 % of rows). The control "
            "INVERTS rather than merely failing to move, because 11,789 of its 57,661 bars close at "
            "server 20 and one bar later lands them ON the rollover — the A@hour-20 and C@hour-0 key "
            "sets are set-equal, 11,789 = 11,789. GROSS: my first mechanism ('the rollover distorts "
            "the mid') is REFUTED by that same control — moving the entry ONTO the rollover gains "
            "MORE gross (+0.0495 R, day-clustered t +3.69) than the hour-00 cell (+0.0433, t +2.18). "
            "The gross gain tracks the DECISION bar's hour: sign(dGross) = -sign(pre-entry drift) on "
            "6 of 6 decision-hour cells, r = -0.915. One bar of delay pays where the intervening bar "
            "reverts against the signal, which is orthogonal to the rollover."),
        "evidence": {
            "n_hour00": h00.get("n"), "n_control": ctl.get("n"),
            "hour00_saving_model_convention_r": h00.get("saving_model_convention_r"),
            "control_saving_model_convention_r": ctl.get("saving_model_convention_r"),
            "hour00_net_delta_r": h00.get("net_delta_model_convention_r"),
            "control_net_delta_r": ctl.get("net_delta_model_convention_r"),
        },
    })

    # ---- item 4 -------------------------------------------------------------------------
    b = ((er.get("boundary_falsification_test") or {}).get("per_account") or {}).get("FTMO") or {}
    v = er.get("fx_verdicts_at_the_repaired_term") or {}
    out.append({
        "ts": TS, "session": "AM", "sleeve": "__estate__",
        "component": "src/costs/spread_model.py era term",
        "gate": "none",
        "prescription": "COST_GEOMETRY",
        "prescription_in_diagnostics_enum": True,
        "action": (
            "PARKED WITH A NUMBER, and the shape of the repair changed. AH §6's min-to-median era "
            "bias is NOT confirmed and NOT estimable from this archive: a difference-in-differences "
            "at SCHEDULE/RECORDED boundaries has forward and reverse boundaries disagreeing in SIGN "
            "once oriented (-0.642 vs +0.016 against a predicted -0.405), which is the refutation "
            "condition the driver's own docstring names; sign test p 1.0000 on n=8; 93 % CI "
            "[-0.817, +0.030] contains both 0 and the prediction. Decisively, and independently of "
            "that test, it moves 0 of 42 member verdicts and 0 of 3 family "
            "verdicts at FULL magnitude on all four of AH's entry arms. 12 of 43 FTMO H4 symbols "
            "are outside its scope by construction (their reference window is itself a nominal "
            "constant, so the factor cancels). The residual is unidentifiable — k_era needs tick "
            "data contemporaneous with a 2000-2010 era — so it belongs in the BAND, not the level: "
            "SPREAD_MODEL_V1_ERA_SCHEDULE_BAND_WIDENED.json widens 536 eras' half-width to cover "
            "the hypothesis and 0 become undecidable. Adopting it is a merge-train decision."),
        "evidence": {
            "did_per_class_ftmo_NOT_AN_ESTIMATE": {
                k: {"n": r.get("n_boundaries"), "n_fwd": r.get("n_forward"),
                    "n_rev": r.get("n_reverse"), "did": r.get("median_did_oriented"),
                    "predicted": r.get("predicted_log_k_ref")}
                for k, r in (b.get("per_class") or {}).items()},
            "why_not_an_estimate": ("forward and reverse boundaries disagree in sign once oriented, "
                                    "which do_boundary's own docstring names as the refutation "
                                    "condition; n=8, sign test p 1.0"),
            "n_verdicts_moved_at_full_magnitude": v.get("n_verdicts_moved"),
            "n_members_crossing_zero": len(v.get("members_crossing_zero") or {}),
            "symbols_out_of_scope_reference_is_nominal": len(
                (er.get("nominal_reference_symbols") or {}).get("FTMO") or []),
            "held_out_winner_by_account": {
                a: (r or {}).get("held_out_winner")
                for a, r in ((er.get("reconciliation") or {}).get("per_account") or {}).items()},
        },
    })
    return out


def main() -> int:
    existing = []
    if QUEUE.is_file():
        for line in QUEUE.read_text().splitlines():
            if line.strip():
                existing.append(json.loads(line))
    keys = {(r.get("session"), r.get("sleeve"), r.get("prescription"), r.get("component"))
            for r in existing}
    new, skipped = [], []
    for r in rows():
        k = (r["session"], r["sleeve"], r["prescription"], r["component"])
        (skipped if k in keys else new).append(r)
        keys.add(k)
    if new:
        with QUEUE.open("a") as fh:
            for r in new:
                fh.write(json.dumps(r, sort_keys=True) + "\n")
    print(f"{QUEUE.relative_to(REPO)}: {len(existing)} rows before, {len(new)} appended, "
          f"{len(skipped)} skipped as already present")
    for r in new:
        print(f"  + {r['sleeve']:24s} {r['prescription']:16s} {r['component'][:52]}")
    for r in skipped:
        print(f"  = {r['sleeve']:24s} {r['prescription']:16s} (already present)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
