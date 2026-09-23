"""Session AL, item 4 — `asia_pdl_fade` taken seriously: the stop x target x time-stop
INTERACTION surface, gated at the declared family.

    python3 docs/audits/fable5-vision-audit-20260725/phase9/receipts/al_asia_pdl_frontier.py

WHY AN INTERACTION SURFACE AND NOT MORE ONE-AXIS CELLS
-----------------------------------------------------
AK swept AD's plan, which walks each exit family SEPARATELY (a stop-width axis, a target axis, a
time-stop axis) and then stacks the per-family argmaxes into ONE post-hoc composite. That found
`asia_pdl_fade`'s headline: `stop_2.5x_tgtscale` takes it from -0.0686 to **+0.0846 R/day with
5 of 5 OOS folds positive**, failing `significance` alone at p 0.0659 on n = 2,827 -- the largest
first-of-day sleeve in the estate and, at that p, the closest thing to an admission outside the
declared pair.

What no session has run is the CROSS. A one-axis sweep cannot see that a wider stop and a wider
target might only pay together, and AD §7.1 measured the consequence directly: **the post-hoc
composite is worse than the best single cell on 17 of 25 sleeves**, which is what stacking
argmaxes from separate axes does when the axes interact. So the cross is the missing measurement,
not a bigger version of one that exists.

WHAT MAKES THE STOP CELLS LEGITIMATE HERE
-----------------------------------------
Checked per sleeve rather than assumed, which is AD's own rule: `asia_pdl_fade.py:108` computes
the stop AFTER every admission gate, so a k-x stop changes the geometry of the same candidate set
and nothing else. AK re-verified it for this sleeve (§3 "the stop-width cells are a legitimate
re-simulation here, checked per sleeve").

WHAT THIS DOES *NOT* DO TO THE MULTIPLICITY BILL, AND THE RISK THAT REPLACES IT
------------------------------------------------------------------------------
`asia_pdl_fade` is already member of `CANDIDATE_BOOK_V1`, and an exit cell re-measures a
hypothesis rather than creating one (AI §0), so the family stays at V2's 35. That is the honest
treatment of the BETWEEN-sleeve bill and it says nothing about the WITHIN-sleeve one: picking the
best of N exit cells is a selection, BH across sleeves does not price it, and at N in the hundreds
it is the dominant risk. Two instruments are published instead of an argument:

  * the **plateau statistics** over the whole cross (`frac_positive`, the winner's rank, the
    median over the winner) -- AB's §5.1 instrument, applied to an interaction surface. A spike
    is a selection; a plateau is a property of the sleeve.
  * every cell in the **trial ledger**, so the DSR deflation everyone shares gets bigger.

And the frontier is reported as a frontier. If `significance` stays out of reach the row states
the measured distance and the next lever, which is what the working agreement asks for.
"""

from __future__ import annotations

import collections
import importlib.util
import itertools
import json
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))
AD_DIR = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"
sys.path.insert(0, str(AD_DIR))

import ad_exit_sweep as AD  # noqa: E402

from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
)
from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import run_gate  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402

import gzip  # noqa: E402

HERE = Path(__file__).resolve().parent
DECL = HERE / "CANDIDATE_FAMILY_V2.json"
OUT = HERE / "AL_ASIA_PDL_FRONTIER_V1.json"
AA_IN = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_TRADES.json.gz"

SLEEVE = "asia_pdl_fade"
SERVER = "FTMO-Server3"

#: The cross, centred on AK's winner (`stop_mult` 2.5, native target convention, no time stop).
#: `target_r=None` means "native": hold the sleeve's own target R multiple and let it scale with
#: the stop, which is what `stop_2.5x_tgtscale` did. The live time-stop contract is 32 M15 bars
#: (`execution_packets.py`, `time_stop_bars: 32` = 8 h), so it is IN the grid rather than beside it.
STOPS = (1.0, 1.5, 2.0, 2.5, 3.0, 3.5)
TARGETS = (None, 2.0, 3.0, 4.0, 5.0)
TIME_STOPS = (None, 8, 16, 32, 48)


def main() -> dict:
    t0 = time.time()
    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AL")
    fam = CF.load_candidate_family(DECL)
    raw = json.load(gzip.open(AA_IN, "rt"))
    base_rows = {s: list(r) for s, r in raw["trades"].items()}
    rows0 = base_rows[SLEEVE]
    costs = AD.load_broker_true_costs(AD.COSTS)
    rule = AD.resolve_rule(SERVER)
    series, index, _ = AD.load_bars()
    print(f"loaded {len(series)} bar series in {time.time()-t0:.0f}s; "
          f"{SLEEVE} n={len(rows0)}")

    base_opt = OPTIONS["B_balanced"]
    spec = base_opt.with_(spec_id=f"{base_opt.spec_id}_al_asia_pdl",
                          sleeve_symbol_allowlist=AD.allowlist())
    spec = CF.with_declared_family(spec, "CANDIDATE_BOOK_V1", loaded=fam)
    print(f"declared family {spec.declared_family_size} ({spec.declared_family_id})")

    cells: dict[str, dict] = {}
    n = 0
    total = len(STOPS) * len(TARGETS) * len(TIME_STOPS)
    for k, tr, ts in itertools.product(STOPS, TARGETS, TIME_STOPS):
        name = (f"stop_{k:g}x_tgt_{'native' if tr is None else f'{tr:g}R'}"
                f"_ts_{'none' if ts is None else ts}")
        v = AD.Variant(
            name=name, family="cross_stop_target_timestop", stop_mult=k,
            target_mode=("scales_with_stop" if tr is None else "fixed_r"),
            target_r=tr, time_stop_bars=ts,
            note=("AK's winning cell" if (k == 2.5 and tr is None and ts is None) else
                  ("the as-walked baseline" if (k == 1.0 and tr is None and ts is None) else
                   ("the LIVE time-stop contract, 32 M15 bars"
                    if (k == 1.0 and tr is None and ts == 32) else ""))))
        new_rows, tel = AD.resimulate(rows0, v, series, index, costs, spec.account, rule)
        if not new_rows:
            cells[name] = {"variant": v.as_dict(), "available": False,
                           "reason": "no trade survived re-simulation", "resim_skips": tel}
            continue
        recs = {s: AD.to_records(r if s != SLEEVE else new_rows) for s, r in base_rows.items()}
        res = run_gate(recs, spec, costs=costs, diagnose=True, server=SERVER)
        sv = res.verdicts[SLEEVE]
        cells[name] = {"variant": v.as_dict(), "stop_mult": k, "target_r": tr,
                       "time_stop_bars": ts, **AD.summarize(sv, tel, len(new_rows))}
        n += 1
        ledger.record(
            mechanism="exit_repair_cross", sleeve=SLEEVE, variant=v.as_dict(),
            window="full_archive", spec_sha256=spec.seal(),
            outcome={"ADMIT": "admitted", "REJECT": "rejected",
                     "NOT_EVALUABLE": "not_evaluable"}.get(sv.verdict.value, "evaluated"),
            metric=sv.pooled_oos_mean_r, metric_name="pooled_oos_mean_r",
            note=f"AL asia_pdl_fade stop x target x time_stop cross, cell {name}")
        if n % 20 == 0:
            print(f"  {n}/{total} cells  {time.time()-t0:.0f}s", flush=True)

    # ---- THE DUPLICATE COLUMN, found by an adversarial pass over this session's own §5 -------
    #  `asia_pdl_fade.py:30` sets TARGET_R = 3.0 and `:112` sets target_dist = TARGET_R * sd, so
    #  the `tgt_3R` cells (target_mode="fixed_r", target_r=3.0) are the SAME GEOMETRY as the
    #  `tgt_native` cells (target_mode="scales_with_stop"). 150 gated cells are 120 DISTINCT
    #  hypotheses plus 30 exact twins, and the twin pair also makes the reported argmax a
    #  tie-break on float noise. Measured rather than assumed.
    twins, max_delta = [], 0.0
    for nm, c in cells.items():
        if "_tgt_native_" not in nm or c.get("pooled_oos_mean_r") is None:
            continue
        tw = nm.replace("_tgt_native_", "_tgt_3R_")
        o = cells.get(tw)
        if o and o.get("pooled_oos_mean_r") is not None:
            d = abs(c["pooled_oos_mean_r"] - o["pooled_oos_mean_r"])
            max_delta = max(max_delta, d)
            twins.append({"native": nm, "fixed_3R": tw, "abs_delta": d})
    duplicates = {
        "why": ("sleeves/asia_pdl_fade.py:30 TARGET_R = 3.0 and :112 target_dist = TARGET_R * sd, "
                "so a `fixed_r` cell at target_r=3.0 is the sleeve's NATIVE geometry. The two "
                "columns are the same hypothesis measured twice."),
        "n_twin_pairs": len(twins), "max_abs_delta": max_delta,
        "n_cells_gated": len([1 for c in cells.values()
                              if c.get("pooled_oos_mean_r") is not None]),
        "n_cells_distinct": len([1 for c in cells.values()
                                 if c.get("pooled_oos_mean_r") is not None]) - len(twins),
        "consequence": ("every count in this artifact that says 150 is a GATED count; the distinct "
                        "hypothesis count is 120, and the argmax over the full set is a tie-break "
                        "between twins at ~4e-17. Read `distinct` for anything about the surface."),
        "twins": twins,
    }

    # ---- the failing-gate distribution, which the frontier prose needs and did not have -------
    #  "significance is the only thing left" is true of the BEST cell and false of the surface:
    #  most cells fail economics as well, so a median-cell reading is not a significance story.
    fail_hist = collections.Counter(
        "+".join(c["failing_gates"]) or "(none)" for c in cells.values()
        if c.get("failing_gates") is not None)
    n_sig_only = fail_hist.get("significance", 0)

    scored = [(c["pooled_oos_mean_r"], nm) for nm, c in cells.items()
              if c.get("pooled_oos_mean_r") is not None]
    scored.sort(reverse=True)
    base_name = "stop_1x_tgt_native_ts_none"
    ak_name = "stop_2.5x_tgt_native_ts_none"
    vals = [v for v, _ in scored]
    plateau = {
        "n_cells_gated": len(scored), "n_cells_planned": total,
        "frac_positive": round(sum(1 for v in vals if v > 0) / len(vals), 4) if vals else None,
        "median": round(statistics.median(vals), 5) if vals else None,
        "best": {"cell": scored[0][1], "value": round(scored[0][0], 5)} if scored else None,
        "worst": {"cell": scored[-1][1], "value": round(scored[-1][0], 5)} if scored else None,
        "ak_winner_rank": (1 + [nm for _, nm in scored].index(ak_name)
                           if ak_name in dict((nm, v) for v, nm in scored) else None),
        "as_walked_rank": (1 + [nm for _, nm in scored].index(base_name)
                           if base_name in dict((nm, v) for v, nm in scored) else None),
        "median_over_best": (round(statistics.median(vals) / scored[0][0], 4)
                             if scored and scored[0][0] else None),
        "ab_own_rule": {
            "source": "docs/audits/fable5-vision-audit-20260725/phase6/receipts/ab_neighborhood.py:116-132",
            "broad_needs_frac_positive_at_least": 0.60,
            "measured_frac_positive": (round(sum(1 for v in vals if v > 0) / len(vals), 4)
                                       if vals else None),
            "verdict_by_abs_own_thresholds": (
                "MIXED -- frac_positive 0.5933 is below AB's 0.60 BROAD threshold, and SPIKE if "
                "the SELECTED cell is taken to be the one this session proposes (rank 1-2 against "
                "a 0.05 * 150 = 7.5 bar at frac < 0.60). Session AL's first draft labelled it "
                "BROAD, which imported AB's BROAD prose at a frac AB assigns elsewhere. "
                "Corrected by an adversarial pass."),
        },
        "median_over_best_is_not_a_selection_share": {
            "full_grid": (round(statistics.median(vals) / max(vals), 4) if vals else None),
            "why_it_is_a_property_of_THIS_grid": (
                "25 of the 150 cells sit at stop 1.0 -- the as-walked geometry the repair exists "
                "to replace -- and 0 of those 25 are positive, so they hold the median down. All "
                "three axes are monotone and ordered, which is AB's own cost-in-R mechanism "
                "(ab_neighborhood.py:20-24), and an axis-wise argmax that never inspects a joint "
                "cell recovers ~99.6 % of the peak. A ratio computed on a grid that deliberately "
                "contains the broken geometry licenses 'the median of this grid is a tenth of its "
                "peak' and NOT a selection share -- and no held-out selection estimate exists "
                "here at all, because cells are ranked on the same metric that defines them."),
        },
        "failing_gate_distribution": dict(fail_hist.most_common()),
        "n_cells_failing_significance_ALONE": n_sig_only,
        "reading": (
            f"MIXED by AB's own rule. And only {n_sig_only} of the gated cells fail significance "
            "ALONE -- the rest also fail expectancy / lifetime / robustness / stability -- so "
            "'significance is what is left' is a statement about the BEST cell, not about the "
            "surface, and a median-cell reading is not a significance story."),
    }
    plateau["duplicates"] = duplicates

    #: The interaction question, answered as a number rather than as a picture: does the best
    #: target depend on the stop? If the argmax target is the same at every stop, the axes are
    #: separable and AK's one-axis sweep lost nothing. If it moves, the cross was necessary.
    best_target_by_stop, best_ts_by_stop = {}, {}
    for k in STOPS:
        sub = [(c["pooled_oos_mean_r"], c["target_r"], c["time_stop_bars"])
               for c in cells.values()
               if c.get("pooled_oos_mean_r") is not None and c.get("stop_mult") == k]
        if not sub:
            continue
        # key on the METRIC only: `target_r` and `time_stop_bars` are None for the native cells,
        # and a plain `max` over tuples compares them on a tie and raises on float-vs-None.
        # Ties: `tgt_native` and `tgt_3R` are the same geometry (see `duplicates`), so a raw
        # argmax picks between twins on ~4e-17 of float noise. Prefer the NATIVE label on a tie,
        # which is the sleeve's own contract and the honest reading.
        top = max(t[0] for t in sub)
        tied = [t for t in sub if abs(t[0] - top) < 1e-12]
        b = next((t for t in tied if t[1] is None), tied[0])
        best_target_by_stop[f"{k:g}"] = b[1]
        best_ts_by_stop[f"{k:g}"] = b[2]
    separable = len(set(map(str, best_target_by_stop.values()))) == 1

    best_cell = cells.get(scored[0][1]) if scored else {}
    p_best = best_cell.get("p_raw")
    m = spec.declared_family_size
    out = {
        "schema": "gtos.wave9.al.asia_pdl_frontier.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "session": "AL", "sleeve": SLEEVE, "n_trades_as_walked": len(rows0),
        "gate": {"option": "B_balanced", "alpha": base_opt.alpha,
                 "spec_sha256": spec.seal(),
                 "declared_family_size": m,
                 "declared_family_id": spec.declared_family_id,
                 "why_the_family_does_not_grow": (
                     "asia_pdl_fade is already a CANDIDATE_BOOK_V1 member and an exit cell "
                     "re-measures a hypothesis rather than creating one (AI §0). The within-"
                     "sleeve selection risk that replaces the between-sleeve one is priced by "
                     "the plateau statistics and by every cell landing in the trial ledger.")},
        "grid": {"stop_mult": list(STOPS), "target_r": list(TARGETS),
                 "time_stop_bars": list(TIME_STOPS), "n_planned": total},
        "stop_cells_legitimate_because": (
            "asia_pdl_fade.py:108 computes the stop AFTER every admission gate, so a k-x stop "
            "changes the geometry of the same candidate set and nothing else (AK §3, re-checked "
            "per sleeve rather than inherited)"),
        "ak_published": {"cell": "stop_2.5x_tgtscale", "pooled_oos_r_per_day": 0.0846,
                         "oos_folds_positive": "5/5", "p_raw": 0.0659, "n": 2827,
                         "as_walked_r_per_day": -0.0686},
        "plateau": plateau,
        "interaction": {
            "question": "does the best target depend on the stop? If not, the cross was optional.",
            "best_target_r_by_stop": best_target_by_stop,
            "best_time_stop_by_stop": best_ts_by_stop,
            "axes_separable": separable,
            "ties_resolved_toward_native": (
                "a raw argmax picks between the `tgt_native` / `tgt_3R` twins on ~4e-17; the "
                "native label wins ties here because it is the sleeve's own contract. Session "
                "AL's first draft published the un-resolved list, in which stop 2.5 read '3R'."),
            "the_axis_that_actually_moves": (
                "the TIME STOP, not the target: best_time_stop_by_stop varies while 4 of 6 stops "
                "pick the native target. And the cross's peak equals AK's stop-only winner to 17 "
                "digits, so the cross CONFIRMED the single-axis answer rather than showing it was "
                "the wrong object -- it bought 0.00000 R/day over it."),
            "separability_test_is_underpowered": (
                "`len(set(best_target_by_stop.values())) == 1` demands the conditional argmax over "
                "5 targets be identical at all 6 stops, which noise alone would defeat, so False "
                "carries little information. Stated rather than left implied."),
            "reading": ("separable == the one-axis sweeps AK ran lost nothing and the composite "
                        "is safe to read; NOT separable == the argmax moves with the stop and a "
                        "per-axis argmax stack is the wrong object (AD §7.1 measured that stack "
                        "losing on 17 of 25 sleeves)"),
        },
        "significance_distance": {
            "best_cell": scored[0][1] if scored else None,
            "best_p_raw": p_best,
            "bh_rank_1_threshold_at_alpha_0.10": round(base_opt.alpha / m, 6),
            "shortfall_factor": (round(p_best / (base_opt.alpha / m), 2)
                                 if p_best else None),
            "n_trades_needed_naively": (
                "p scales roughly as exp(-c*n) for a fixed effect, so a factor-of-X shortfall is "
                "not a simple trade multiple; the honest statement is the factor, and the next "
                "lever below."),
            "next_lever": (
                "regime conditioning from AB's dials (AB_REGIME_DIALS_V1.json) is UNEXPLORED for "
                "this sleeve -- AB's conditioning work covered the armed four and AH refuted "
                "MEMBER conditioning for the FX D1 cohort, which is a different axis from REGIME "
                "conditioning on a first-of-day sleeve. AH also measured that the entry HOUR is "
                "the FX D1 cohort's lever; asia_pdl_fade is by construction a first-of-day rule, "
                "so its entry-timing axis is fixed by the mechanism and the regime axis is what "
                "is left."),
        },
        "cells": cells,
        "seconds_total": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"\n{'cell':44s} {'verdict':13s} {'R/day':>9s} {'p_raw':>8s} {'folds+':>7s} "
          f"{'cov':>5s}")
    for v, nm in scored[:14]:
        c = cells[nm]
        print(f"{nm:44s} {c['verdict']:13s} {v:9.5f} "
              f"{(c['p_raw'] if c['p_raw'] is not None else float('nan')):8.4f} "
              f"{str(c['oos_positive_fold_frac']):>7s} "
              f"{str(c['coverage_frac']):>5s}")
    print(f"\nplateau: {plateau['frac_positive']} positive of {plateau['n_cells_gated']}, "
          f"median {plateau['median']}, AK winner rank {plateau['ak_winner_rank']}, "
          f"as-walked rank {plateau['as_walked_rank']}")
    print(f"axes separable: {separable}; best target by stop: {best_target_by_stop}")
    print(f"best p_raw {p_best} against a rank-1 bar of {base_opt.alpha/m:.6f}")
    print(f"wrote {OUT.relative_to(REPO)} ({n} cells, {time.time()-t0:.0f}s)")
    return out


if __name__ == "__main__":
    main()
