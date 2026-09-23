"""Session BD — the `partial_be_runner` scale-out, gated at the ratified rule.

    python3 docs/audits/fable5-vision-audit-20260725/phase13/receipts/bd_partial_exit.py
    ... --no-ledger

WHY THIS RUNS AT ALL

`energy_agri` is ARMED on both funded accounts and its live exit is a `partial_be_runner`: half the
position off at +2R, stop to breakeven, the rest runs to 4R or the 1,280-bar horizon. Two sessions
have now measured that scale-out against a plain exit and both say it COSTS money:

    AD §6.2   -0.308 R/day   n=67    "a question, not a recommendation"  (thin, one instrument)
    AU §2     +0.2302 R/day  restamp error at EVERY band, on armed money

Neither was gated. AD's is a raw delta at n=67; AU's is restamp arithmetic establishing that the
published economics describe a contract the book does not run. So the estate has a twice-measured
number on armed money that has never been put through the admission machinery, which is exactly the
shape of claim the ratified rule exists for.

AND THE REASON IT IS NOT A GENERAL PRESCRIPTION. AU also measured that across the four
`partial_be_runner` sleeves **the sign runs both ways** -- `metals_core`'s scale-out HELPS by
0.0777 R/day. So "remove the scale-out" cannot be a policy; it is a per-sleeve question, and the
other three sleeves ride this grid as the control that says so. If the plain arm won everywhere, the
harness would be measuring the harness.

THE CUT RULE, DECLARED BEFORE ANY GATE RAN (agreement §1: declare the cut rule, not just the axis)

TWO ARMS PER SLEEVE. Not a grid, not a search, nothing fitted:

    LIVE   `resolve_exit_profile(sleeve)` verbatim -- the committed contract the book runs today.
    PLAIN  the same target and the same horizon with the scale-out and the BE move REMOVED
           (`policy="time_stop"`, `partial_close_ratio=None`, `trigger_r=final_target_r`).

`trigger_r` is set to `final_target_r` rather than to None deliberately: `build_book_trade_params`
reads `float(prof.get("trigger_r", final_target_r))`, so a literal None is a live `TypeError`, while
`final_target_r` is precisely the value every `time_stop` sleeve resolves to implicitly. The PLAIN
arm is therefore the contract `crypto` and `sub_xvol_pullback` already run, not a new one.

k=2 is still a search over two cells, so `p_min_over_grid` is reported against
`expected_min_p_under_global_null = 1-(1-p)^2` -- AR's standard, applied prospectively.

MULTIPLICITY. No new looks (AI §0): both arms are exit-cell re-measurements of sleeves already
declared in `CANDIDATE_BOOK_V1`. Family V5 (the tighter bar). Every arm ledgered including
NOT_EVALUABLE (B1267).

POPULATION. `RECORDED` with AN's conditions, the RATIFIED rule, band column alongside a flat control.
BOUNDARY. Offline and pure. No broker module, no order, no VPS, no config byte.
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase13/receipts"
AU = REPO / "docs/audits/fable5-vision-audit-20260725/phase12/receipts"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(AU))

import au_live_contract as LC  # noqa: E402

AD = LC.AD

from src.components.ultimate_book.execution_packets import (  # noqa: E402
    SLEEVE_EXIT_PROFILES,
    resolve_exit_profile,
)
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
)
from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import era_population as POP  # noqa: E402
from src.research_infra.walkforward import run_gate  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402

AA_IN = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_TRADES.json.gz"
FAMILY_V5 = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts/CANDIDATE_FAMILY_V5.json"
UNITS = LC.UNITS
OUT = HERE / "BD_PARTIAL_EXIT_V1.json"

ACCOUNT, SERVER = "FTMO", "FTMO-Server3"
BANDS = (None, "low", "mid", "high")
POPULATION = "RECORDED"
OPTION = "B_balanced"

#: The subject. ARMED on both accounts; the only sleeve here with money on the answer.
SUBJECT = "energy_agri"
#: The control. Every other sleeve whose live policy is `partial_be_runner`. AU measured the sign
#: runs both ways across them, so if PLAIN wins on all four this grid is measuring the harness.
CONTROLS = tuple(
    s for s, p in SLEEVE_EXIT_PROFILES.items()
    if str(p.get("policy")) == "partial_be_runner" and s != SUBJECT
)
ARMS = ("LIVE", "PLAIN")


def scale_out_profile(sleeve: str) -> dict:
    """The sleeve's `partial_be_runner` contract, whichever side of the default it now lives on.

    Added 2026-08-11. This receipt compares a scale-out arm against a plain arm, and it used to
    assume the scale-out was the COMMITTED contract. For `energy_agri` that inverted on 2026-08-11
    (owner-authorized, lane B7): plain became the default and the scale-out moved to the frontier
    override `partial_be_runner_restore`. A dated receipt must keep measuring the same two arms, so
    it asks for the scale-out by POLICY rather than by position.
    """
    prof = dict(resolve_exit_profile(sleeve))
    if str(prof.get("policy")) != "partial_be_runner":
        prof = dict(resolve_exit_profile(sleeve, frontier_exits=(sleeve,)))
    return prof


def plain_profile(sleeve: str) -> dict:
    """The scale-out profile with the scale-out and the BE move removed, nothing else moved."""
    prof = scale_out_profile(sleeve)
    if str(prof.get("policy")) != "partial_be_runner":
        raise ValueError(f"{sleeve} is not a partial_be_runner; refusing to build a PLAIN arm")
    ftr = prof.get("final_target_r")
    return {
        **prof,
        "policy": "time_stop",
        "partial_close_ratio": None,
        # NOT None: `build_book_trade_params` does `float(prof.get("trigger_r", final_target_r))`,
        # so a literal None is a live TypeError. `final_target_r` is what every `time_stop` sleeve
        # resolves to implicitly, which makes PLAIN an existing contract rather than a new one.
        "trigger_r": ftr if ftr is not None else prof.get("trigger_r"),
    }


def build_substrate() -> dict:
    t0 = time.time()
    raw = json.load(gzip.open(AA_IN, "rt"))
    base = {s: list(r) for s, r in raw["trades"].items() if r}
    series, index, _ = AD.load_bars()
    units = json.load(open(UNITS)) if UNITS.exists() else {}
    cohort = (SUBJECT,) + CONTROLS
    missing = [s for s in cohort if s not in base]
    print(f"substrate in {time.time() - t0:.0f}s: {len(base)} sleeves, cohort {len(cohort)}"
          + (f", ABSENT from AA: {missing}" if missing else ""), flush=True)
    return {"base": base, "costs": AD.load_broker_true_costs(AD.COSTS),
            "rule": AD.resolve_rule(SERVER), "series": series, "index": index,
            "allowlist": AD.allowlist(), "family": CF.load_candidate_family(FAMILY_V5),
            "cohort": tuple(s for s in cohort if s in base), "units": units,
            "cohort_absent": missing}


def relabel(sub: dict, arm: str) -> tuple[dict, dict]:
    """Every cohort sleeve under `arm`; every other sleeve exactly as AA walked it."""
    out = {s: list(r) for s, r in sub["base"].items()}
    tel: dict[str, dict] = {}
    for s in sub["cohort"]:
        prof = resolve_exit_profile(s) if arm == "LIVE" else plain_profile(s)
        grid = LC.grid_of(sub["base"][s])
        v = LC.variant_for_profile(
            s, prof, grid=grid, name=f"{arm.lower()}_{s}",
            printed_ratio=LC.printed_ratio_of(s, sub["units"]),
        )
        rows, t = AD.resimulate(sub["base"][s], v, sub["series"], sub["index"], sub["costs"],
                                ACCOUNT, sub["rule"])
        out[s] = rows
        tel[s] = {"variant": v.as_dict(), "grid": grid, **LC.maxbars_share(t)}
    return out, tel


def row_of(sv, spec, *, band, arm, seconds, mix, tel) -> dict:
    base = {"arm": arm, "population": POPULATION,
            "band": band if band is not None else "flat_37_day_snapshot",
            "band_is_control": band is None,
            "declared_family_size": spec.declared_family_size,
            "spec_sha256": spec.seal(), "population_mix": mix, "seconds": round(seconds, 2),
            "grid": tel.get("grid"), "variant": tel.get("variant"),
            "maxbars_share": tel.get("maxbars_share"),
            "time_stop_share": tel.get("time_stop_share"),
            "exit_reasons": tel.get("exit_reasons")}
    if sv is None:
        return {**base, "verdict": "ABSENT"}
    st = sv.gates.get("stability", {})
    t = sv.telemetry or {}
    ri = t.get("regime_inflation") or {}
    ins = t.get("in_sample") or {}
    fl = t.get("p_floor") or {}
    hold = (sv.diagnostics or {}).get("holding") or {}
    return {**base,
            "verdict": sv.verdict.value, "n_trades": sv.n_trades,
            "pooled_oos_mean_r": sv.pooled_oos_mean_r,
            "p_raw": sv.p_raw, "q_value": sv.q_value,
            "failing_core_gates": [g for g in ("expectancy", "lifetime", "stability",
                                               "robustness", "significance")
                                   if not sv.gates.get(g, {}).get("pass")],
            # Mandatory on every admission-grade claim (agreement §1): the gate reads fold SIGNS
            # only, and AN measured a 7.6x chronological decay that every gate passes.
            "fold_means": st.get("fold_means"),
            "oos_positive_fold_frac": st.get("oos_positive_fold_frac"),
            "n_folds_evaluable": sv.gates.get("sample", {}).get("n_folds_evaluable"),
            "drop_best_retention": sv.gates.get("robustness", {}).get("retention"),
            "p_floor": fl.get("p_floor"), "n_blocks": fl.get("n_blocks"),
            "p_floor_headroom": ((sv.p_raw / fl["p_floor"])
                                 if (sv.p_raw is not None and fl.get("p_floor")) else None),
            "regime_inflation_contaminated": ri.get("contamination_flag"),
            "recommended_magnitude_haircut": ri.get("recommended_magnitude_haircut"),
            "haircut_at_floor": ri.get("haircut_at_floor"),
            "in_sample_mean_is_r": ins.get("mean_is_r"),
            "in_sample_mean_oos_r": ins.get("mean_oos_r"),
            "in_sample_sign_inversion": (
                None if (ins.get("mean_is_r") is None or ins.get("mean_oos_r") is None)
                else bool(float(ins["mean_is_r"]) < 0 <= float(ins["mean_oos_r"]))),
            "median_hold_hours": hold.get("median_hours"),
            "reasons": list(sv.reasons)}


def run_grid(sub: dict, ledger: TrialLedger | None) -> dict:
    arms: dict[str, dict] = {}
    for arm in ARMS:
        labelled, tel = relabel(sub, arm)
        for band in BANDS:
            t0 = time.time()
            o = OPTIONS[OPTION]
            spec = o.with_(spec_id=f"{o.spec_id}_bd_partial_{arm.lower()}",
                           sleeve_symbol_allowlist=sub["allowlist"], spread_band=band)
            spec = CF.with_declared_family(spec, "CANDIDATE_BOOK_V1", loaded=sub["family"])
            recs0 = {s: AD.to_records(r) for s, r in labelled.items()}
            recs, spec, mix = POP.apply(POPULATION, recs0, spec, account=ACCOUNT,
                                        band=(band or "mid"))
            res = run_gate(recs, spec, costs=sub["costs"], server=SERVER, diagnose=True)
            wo = (res.family or {}).get("wipeout") or {}
            if wo.get("wiped_out"):
                raise RuntimeError(f"gate wipeout at {arm}/{band}: {wo}. Refusing to publish.")
            el = time.time() - t0
            key = f"{arm}|{band or 'flat'}"
            arms[key] = {}
            for s in sub["cohort"]:
                sv = res.verdicts.get(s)
                arms[key][s] = row_of(sv, spec, band=band, arm=arm, seconds=el, mix=mix,
                                      tel=tel.get(s, {}))
                if ledger is not None and sv is not None:
                    ledger.record(
                        mechanism="partial_exit_arms", sleeve=s,
                        variant={"arm": arm, "population": POPULATION,
                                 "band": arms[key][s]["band"], "option": OPTION},
                        window="full_archive", spec_sha256=spec.seal(),
                        outcome={"ADMIT": "admitted", "REJECT": "rejected",
                                 "NOT_EVALUABLE": "not_evaluable"}.get(sv.verdict.value,
                                                                       "evaluated"),
                        metric=sv.pooled_oos_mean_r, metric_name="pooled_oos_mean_r",
                        note=f"{s} {arm} at {band or 'flat'} band, {POPULATION}",
                    )
            print(f"  {key}: " + ", ".join(
                f"{s}={arms[key][s].get('pooled_oos_mean_r')}" for s in sub["cohort"]), flush=True)
    return arms


def compare(arms: dict, cohort: tuple[str, ...]) -> dict:
    """PLAIN minus LIVE per sleeve per band, and the verdict on each side."""
    out: dict[str, dict] = {}
    for s in cohort:
        per_band = {}
        for band in BANDS:
            b = band or "flat"
            live = arms.get(f"LIVE|{b}", {}).get(s) or {}
            plain = arms.get(f"PLAIN|{b}", {}).get(s) or {}
            lm, pm = live.get("pooled_oos_mean_r"), plain.get("pooled_oos_mean_r")
            per_band[b] = {
                "live_mean_r_per_day": lm, "plain_mean_r_per_day": pm,
                "plain_minus_live_r_per_day": (None if (lm is None or pm is None) else round(pm - lm, 6)),
                "live_verdict": live.get("verdict"), "plain_verdict": plain.get("verdict"),
                "live_p_raw": live.get("p_raw"), "plain_p_raw": plain.get("p_raw"),
                "live_maxbars_share": live.get("maxbars_share"),
                "plain_maxbars_share": plain.get("maxbars_share"),
                "live_n": live.get("n_trades"), "plain_n": plain.get("n_trades"),
            }
        deltas = [v["plain_minus_live_r_per_day"] for v in per_band.values()
                  if v["plain_minus_live_r_per_day"] is not None]
        ps = [p for p in (arms.get(f"{a}|{b or 'flat'}", {}).get(s, {}).get("p_raw")
                          for a in ARMS for b in BANDS) if p is not None]
        p_min = min(ps) if ps else None
        out[s] = {
            "armed": s == SUBJECT,
            "by_band": per_band,
            "plain_better_at_all_bands": bool(deltas) and all(d > 0 for d in deltas),
            "live_better_at_all_bands": bool(deltas) and all(d < 0 for d in deltas),
            "sign_is_consistent": bool(deltas) and (all(d > 0 for d in deltas) or all(d < 0 for d in deltas)),
            "min_delta_r_per_day": min(deltas) if deltas else None,
            "max_delta_r_per_day": max(deltas) if deltas else None,
            # k=2 arms; the search is small but it is still a search.
            "p_min_over_arms": p_min,
            "expected_min_p_under_global_null": (
                None if p_min is None else round(1 - (1 - p_min) ** len(ARMS), 6)),
            "any_arm_admits": any(
                (arms.get(f"{a}|{b or 'flat'}", {}).get(s, {}).get("verdict") == "ADMIT")
                for a in ARMS for b in BANDS),
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-ledger", action="store_true")
    args = ap.parse_args()
    ledger = None if args.no_ledger else TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="BD")

    sub = build_substrate()
    arms = run_grid(sub, ledger)
    cmp = compare(arms, sub["cohort"])

    doc = {
        "session": "BD",
        "artifact": "BD_PARTIAL_EXIT_V1",
        "question": (
            "Does removing the partial_be_runner scale-out beat the committed contract at the "
            "RATIFIED rule -- on energy_agri, which is ARMED, with the other three "
            "partial_be_runner sleeves as the sign control?"
        ),
        "rule": {"population": POPULATION, "option": OPTION, "alpha": 0.10,
                 "family": "CANDIDATE_BOOK_V1 via CANDIDATE_FAMILY_V5", "bands": list(BANDS),
                 "account": ACCOUNT, "server": SERVER},
        "declared_before_gating": {
            "arms": list(ARMS),
            "cut_rule": ("two arms per sleeve: the committed profile verbatim, and the same target "
                         "and horizon with partial_close_ratio removed and trigger_r set to "
                         "final_target_r. No grid, no threshold, nothing fitted."),
            "subject": SUBJECT, "controls": list(CONTROLS),
            "control_logic": ("AU measured the scale-out's sign runs BOTH ways across these four "
                              "sleeves (metals_core's HELPS by 0.0777 R/day). If PLAIN wins on all "
                              "four this grid is measuring the harness, not the contract."),
        },
        "prior_measurements_being_gated": {
            "AD_6.2": {"delta_r_per_day": -0.308, "n": 67,
                       "note": "the scale-out's cost vs plain; AD called it a question, not a "
                               "recommendation"},
            "AU_2": {"restamp_error_r_per_day": 0.2302,
                     "note": "at every band, on armed money; corroborates AD's sign through a "
                             "second instrument"},
        },
        "cohort": list(sub["cohort"]),
        "cohort_absent_from_aa": sub["cohort_absent"],
        "arms": arms,
        "comparison": cmp,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2, default=str), encoding="utf-8")
    print(f"\nwrote {OUT}")
    for s, c in cmp.items():
        tag = " [ARMED]" if c["armed"] else ""
        print(f"  {s}{tag}: delta {c['min_delta_r_per_day']} .. {c['max_delta_r_per_day']} R/day, "
              f"consistent={c['sign_is_consistent']}, any_admit={c['any_arm_admits']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
