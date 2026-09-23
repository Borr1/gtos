"""Read `EXIT_FRONTIER_V1.json` and answer the four questions the surfaces were swept for.

    python3 docs/audits/fable5-vision-audit-20260725/phase7/receipts/ad_frontier_analysis.py

1. THE TRAIL BOUNDS (item 7 / B613). The rule "run every trail against the intrabar-honest
   variant and report both bounds" is law in this lane and it stands. What does NOT stand is
   the reading attached to it — that the production bound is the OPTIMISTIC one. That was
   measured on `asian_fade`, and `asian_fade` is a FADE. `simulate`'s same-bar arm-and-fill
   makes the trail exit EARLIER at a price the bar may never have offered in that sequence;
   on a mean-reversion sleeve an early exit at a good price is an over-claim, and on a trend
   sleeve it is an under-claim, because it cuts the runner. So the sign of the bias is a
   property of the mechanism, not of the switch. Measured here over every trail cell in the
   sweep.

2. THE STOP-WIDTH FRONTIER TARGETS (item 3). `AA_COST_GEOMETRY_FRONTIER_V1.json` gives each
   COST_GEOMETRY sleeve the gross-in-R retention it needs at a 2x stop to break even —
   `metals_core` 0.59x, `fx_jpy` 1.89x. This measures the retention actually achieved, under
   both target conventions, and compares.

3. THE LIVE-CONTRACT DIVERGENCE. AA labelled the whole estate under plain stop/target/maxbars.
   Four sleeves' live contract is `partial_be_runner` and twelve more carry a time stop that
   B750 measured as binding. So for those sleeves AA's published economics are about a
   contract the live book does not run. This measures the gap.

4. THE WINNERS, against the two bounds that matter: the zero-carry CEILING (the most any
   carry repair could be worth) and the three spread bands (whether the cell wins only at the
   flat 37-day snapshot).
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"
IN = HERE / "EXIT_FRONTIER_V1.json"
AA_FRONTIER = (REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts"
               / "AA_COST_GEOMETRY_FRONTIER_V1.json")
OUT = HERE / "AD_FRONTIER_ANALYSIS_V1.json"

#: Mechanism class per sleeve, read from the generator's own name and docstring. Needed for
#: question 1: the intrabar bias' sign is a property of the mechanism.
MECHANISM = {
    "metals_core": "retest_continuation", "metals_softband": "retest_continuation",
    "metals_ob_micro": "retest_continuation", "crypto": "breakout_continuation",
    "energy_agri": "breakout_continuation", "idxrev": "reversion",
    "fx_jpy": "session_momentum", "fx_jpy_ny": "session_momentum",
    "sub_mid_dn_revert": "reversion", "sub_xvol_pullback": "pullback_continuation",
    "vol_compression": "breakout_continuation",
    "vss_fxcross_london_up_low": "session_momentum",
    "metal_session_reversion": "reversion", "kz_london_crypto_low": "reversion",
    "ny_crypto_momentum": "momentum_continuation",
    "asia_pdl_fade": "reversion", "asian_fade": "reversion",
    "orb_crypto_london": "breakout_continuation",
    "liq_asia_up_low_metal": "reversion",
}
#: The `mx_*` family is classified by the mechanism in its own tag rather than enumerated,
#: because the tag IS the mechanism (`market_expansion_d1.py:207-213` dispatches on exactly
#: these three strings).
_MX_MECHANISM = (("donchian", "breakout_continuation"),
                 ("volume_surge_reversal", "reversion"),
                 ("atr_mean_reversion", "reversion"))


def mech(sleeve: str) -> str:
    if sleeve in MECHANISM:
        return MECHANISM[sleeve]
    for token, m in _MX_MECHANISM:
        if token in sleeve:
            return m
    return "unknown"


def main() -> dict:
    # Merge the main sweep with any supplementary run, later files winning per sleeve. The
    # supplement exists because the two `trailing_runner` sleeves needed their own live
    # arm/gap in the grid and re-running 24 sleeves to add two cells would have been silly.
    parts = sorted(HERE.glob("EXIT_FRONTIER_V1*.json"))
    d = json.loads(IN.read_text())
    merged_from = [IN.name]
    for p in parts:
        if p == IN or p.name == OUT.name:
            continue
        extra = json.loads(p.read_text())
        for k, v in (extra.get("sleeves") or {}).items():
            if v.get("available"):
                d["sleeves"][k] = v
        d["n_cells_gated"] = d.get("n_cells_gated", 0) + extra.get("n_cells_gated", 0)
        merged_from.append(p.name)
    sl = {k: v for k, v in d["sleeves"].items() if v.get("available")}
    print(f"{len(sl)} sleeves, {d['n_cells_gated']} gated cells "
          f"(merged from {merged_from})\n")

    # =============================================================== 1. trail bounds
    trail_rows = []
    for s, v in sl.items():
        cells = v["cells"]
        for name, c in cells.items():
            if not name.startswith("trail_") or not name.endswith("_prod"):
                continue
            h = cells.get(name[:-5] + "_honest")
            if not h or c.get("pooled_oos_mean_r") is None \
                    or h.get("pooled_oos_mean_r") is None:
                continue
            arm = float(name.split("_a")[1].split("_g")[0])
            gap = float(name.split("_g")[1].split("_")[0])
            trail_rows.append({
                "sleeve": s, "mechanism": mech(s), "arm_r": arm, "gap_r": gap,
                "prod_pooled": c["pooled_oos_mean_r"],
                "honest_pooled": h["pooled_oos_mean_r"],
                "honest_minus_prod": round(h["pooled_oos_mean_r"] - c["pooled_oos_mean_r"], 6),
                "prod_gross_per_trade": c["mean_gross_r"],
                "honest_gross_per_trade": h["mean_gross_r"],
                "prod_median_hold_h": c["median_hold_hours"],
                "honest_median_hold_h": h["median_hold_hours"],
                "prod_trail_exit_frac": round(
                    (c["exit_reasons"].get("trail", 0) / max(1, c["n_resimulated"])), 4),
                "honest_trail_exit_frac": round(
                    (h["exit_reasons"].get("trail", 0) / max(1, h["n_resimulated"])), 4),
            })
    n = len(trail_rows)
    honest_worse = [r for r in trail_rows if r["honest_minus_prod"] < 0]
    honest_better = [r for r in trail_rows if r["honest_minus_prod"] > 0]
    by_mech: dict[str, list] = {}
    by_arm: dict[float, list] = {}
    for r in trail_rows:
        by_mech.setdefault(r["mechanism"], []).append(r["honest_minus_prod"])
        by_arm.setdefault(r["arm_r"], []).append(r["honest_minus_prod"])
    print("=== 1. the trail's intrabar bias: which direction, and does it have one? ===")
    print(f"{n} trail cells with both bounds. honest WORSE than production: "
          f"{len(honest_worse)} ({100*len(honest_worse)/max(1,n):.0f} %); "
          f"honest BETTER: {len(honest_better)} ({100*len(honest_better)/max(1,n):.0f} %)")
    print(f"\n{'by mechanism':28s} {'n':>4s} {'mean honest-prod':>18s} {'median':>10s} "
          f"{'frac honest better':>19s}")
    for m, vals in sorted(by_mech.items(), key=lambda kv: statistics.fmean(kv[1])):
        print(f"{m:28s} {len(vals):4d} {statistics.fmean(vals):18.5f} "
              f"{statistics.median(vals):10.5f} "
              f"{sum(1 for x in vals if x > 0)/len(vals):19.2f}")
    print(f"\n{'by trail arm (R)':28s} {'n':>4s} {'mean honest-prod':>18s} {'median':>10s} "
          f"{'frac honest better':>19s}")
    for a, vals in sorted(by_arm.items()):
        print(f"{'arm ' + str(a):28s} {len(vals):4d} {statistics.fmean(vals):18.5f} "
              f"{statistics.median(vals):10.5f} "
              f"{sum(1 for x in vals if x > 0)/len(vals):19.2f}")

    # =============================================================== 2. frontier targets
    print("\n=== 2. the stop-width frontier: measured gross retention vs AA's target ===")
    #: `required_gross_multiple_vs_1x` lives per (sleeve, multiple) in AA's frontier — the
    #: gross-in-R the sleeve must retain at that stop multiple to break even. The 2x cell is
    #: the one AA's table published and the prompt quotes.
    aa = json.loads(AA_FRONTIER.read_text()) if AA_FRONTIER.is_file() else {}
    aa_req: dict[str, float] = {}
    aa_gross_1x: dict[str, float] = {}
    for name, rec in (aa.get("sleeves") or {}).items():
        cell = ((rec.get("by_multiple") or {}).get("2") or {})
        v = cell.get("required_gross_multiple_vs_1x")
        if isinstance(v, (int, float)):
            aa_req[name] = float(v)
        if isinstance(rec.get("mean_gross_r_at_1x"), (int, float)):
            aa_gross_1x[name] = float(rec["mean_gross_r_at_1x"])
    fr_rows = []
    print(f"{'sleeve':42s} {'native':14s} {'req@2x':>7s} {'got@2x_nat':>11s} "
          f"{'got@2x_alt':>11s} {'clears?':>8s}")
    for s, v in sl.items():
        if not v.get("stop_width_swept"):
            continue
        base = v["cells"]["as_walked"]["mean_gross_r"]
        conv = v["native_target_convention"]["convention"]
        nat = "stop_2x_tgtscale" if conv == "scales_with_stop" else "stop_2x_tgtfix"
        alt = "stop_2x_tgtfix" if conv == "scales_with_stop" else "stop_2x_tgtscale"
        gn = (v["cells"].get(nat) or {}).get("mean_gross_r")
        ga = (v["cells"].get(alt) or {}).get("mean_gross_r")
        req = aa_req.get(s)
        mn = (gn / base) if (gn is not None and base not in (None, 0)) else None
        ma = (ga / base) if (ga is not None and base not in (None, 0)) else None
        clears = (None if (mn is None or req is None) else
                  ("yes" if mn >= req else "no"))
        fr_rows.append({"sleeve": s, "native_convention": conv,
                        "aa_required_gross_multiple_at_2x": req,
                        "gross_at_1x": base,
                        "gross_at_2x_native": gn, "gross_at_2x_alt": ga,
                        "measured_multiple_native": (round(mn, 4) if mn else None),
                        "measured_multiple_alt": (round(ma, 4) if ma else None),
                        "clears_target_native": clears,
                        "pooled_at_2x_native": (v["cells"].get(nat) or {}).get(
                            "pooled_oos_mean_r"),
                        "pooled_as_walked": v["cells"]["as_walked"]["pooled_oos_mean_r"],
                        "verdict_at_2x_native": (v["cells"].get(nat) or {}).get("verdict"),
                        "swap_nights_1x": v["cells"]["as_walked"]["swap_nights_mean"],
                        "swap_nights_2x_native": (v["cells"].get(nat) or {}).get(
                            "swap_nights_mean")})
        f = lambda x: ("          -" if x is None else f"{x:11.4f}")  # noqa: E731
        print(f"{s:42s} {conv:14s} {(f'{req:.2f}' if req else '-'):>7s} "
              f"{f(mn)} {f(ma)} {str(clears):>8s}")

    # =============================================================== 3. live divergence
    print("\n=== 3. the live exit contract vs the contract AA published economics for ===")
    print(f"{'sleeve':42s} {'live policy':20s} {'as_walked':>10s} {'live cell':>10s} "
          f"{'delta':>9s} {'capt aw':>8s} {'capt live':>9s}")
    div_rows = []
    for s, v in sl.items():
        prof = v["live_exit_contract"]
        pol = str(prof.get("policy"))
        cells = v["cells"]
        aw = cells["as_walked"]
        live_cell = None
        if pol == "partial_be_runner" and prof.get("trigger_r") is not None:
            live_cell = f"partial_{float(prof['trigger_r']):g}R_be"
        elif pol == "time_stop" and v.get("live_time_stop_in_own_bars"):
            t = max(1, int(round(v["live_time_stop_in_own_bars"])))
            live_cell = f"time_stop_{t}" if t < d["maxbars"] else "as_walked"
        c = cells.get(live_cell or "")
        if not c or c.get("pooled_oos_mean_r") is None:
            div_rows.append({"sleeve": s, "live_policy": pol, "live_cell": live_cell,
                             "measurable": False,
                             "reason": ("the live contract's cell is as_walked — its time "
                                        "stop equals or exceeds MAXBARS, so the walk already "
                                        "ran the live contract"
                                        if live_cell == "as_walked" else
                                        "no cell for the live contract in this sweep")})
            print(f"{s:42s} {pol:20s} {'(walk == live contract)' if live_cell == 'as_walked' else '(no cell)'}")
            continue
        delta = c["pooled_oos_mean_r"] - aw["pooled_oos_mean_r"]
        div_rows.append({
            "sleeve": s, "live_policy": pol, "live_cell": live_cell, "measurable": True,
            "aa_walked_pooled": aw["pooled_oos_mean_r"],
            "live_contract_pooled": c["pooled_oos_mean_r"],
            "delta_pooled": round(delta, 6),
            "aa_walked_capture": aw["capture_ratio_pooled"],
            "live_contract_capture": c["capture_ratio_pooled"],
            "aa_walked_gross": aw["mean_gross_r"],
            "live_contract_gross": c["mean_gross_r"],
            "aa_walked_median_hold_h": aw["median_hold_hours"],
            "live_contract_median_hold_h": c["median_hold_hours"],
            "aa_walked_verdict": aw["verdict"], "live_contract_verdict": c["verdict"],
        })
        print(f"{s:42s} {pol:20s} {aw['pooled_oos_mean_r']:10.5f} "
              f"{c['pooled_oos_mean_r']:10.5f} {delta:+9.5f} "
              f"{str(aw['capture_ratio_pooled']):>8s} {str(c['capture_ratio_pooled']):>9s}")

    # =============================================================== 4. winners
    print("\n=== 4. the winning cell per sleeve, against the ceiling and the bands ===")
    print(f"{'sleeve':42s} {'best cell':28s} {'R/day':>9s} {'dR/day':>9s} "
          f"{'ceil':>9s} {'beats?':>7s} {'band lo/mid/hi verdicts':>26s}")
    win_rows = []
    for s, v in sl.items():
        cells = v["cells"]
        aw = cells["as_walked"]
        scored = [(c["pooled_oos_mean_r"], nm) for nm, c in cells.items()
                  if c.get("pooled_oos_mean_r") is not None]
        if not scored:
            continue
        best_r, best = max(scored)
        c = cells[best]
        ceil = v["zero_carry_ceiling"]
        bands = (v.get("best_cell_at_spread_bands") or {}).get("bands") or {}
        beats = (ceil.get("pooled_oos_mean_r") is not None
                 and best_r > ceil["pooled_oos_mean_r"])
        bv = "/".join(bands.get(b, {}).get("verdict", "-")[:6] for b in ("low", "mid", "high"))
        win_rows.append({
            "sleeve": s, "best_cell": best, "best_family": (c.get("variant") or {}).get("family"),
            "best_pooled": best_r, "as_walked_pooled": aw["pooled_oos_mean_r"],
            "delta_pooled": round(best_r - aw["pooled_oos_mean_r"], 6),
            "best_verdict": c["verdict"], "best_failing_gates": c["failing_gates"],
            "best_q": c["q_value"], "best_p_raw": c["p_raw"],
            "best_capture": c["capture_ratio_pooled"],
            "best_gross": c["mean_gross_r"], "best_cost_pct": c["cost_pct_of_abs_gross"],
            "zero_carry_ceiling_pooled": ceil.get("pooled_oos_mean_r"),
            "zero_carry_ceiling_verdict": ceil.get("verdict"),
            "best_beats_zero_carry_ceiling": beats,
            "spread_band_cell": (v.get("best_cell_at_spread_bands") or {}).get("cell"),
            "spread_bands": {b: {"verdict": x.get("verdict"),
                                 "pooled": x.get("pooled_oos_mean_r"),
                                 "coverage_frac": x.get("coverage_frac")}
                             for b, x in bands.items()},
            "any_admit_anywhere": any(x["verdict"] == "ADMIT" for x in cells.values()
                                      if x.get("verdict")),
        })
        print(f"{s:42s} {best:28s} {best_r:9.5f} "
              f"{best_r - aw['pooled_oos_mean_r']:+9.5f} "
              f"{(ceil.get('pooled_oos_mean_r') or 0):9.5f} {str(beats):>7s} {bv:>26s}")

    admits = [r["sleeve"] for r in win_rows if r["any_admit_anywhere"]]
    print(f"\ncells reaching ADMIT anywhere in the sweep: "
          f"{admits if admits else 'NONE'}")
    fails = {}
    for r in win_rows:
        for g in r["best_failing_gates"]:
            fails[g] = fails.get(g, 0) + 1
    print(f"failing gate at each sleeve's BEST cell: {dict(sorted(fails.items(), key=lambda kv: -kv[1]))}")

    doc = {
        "schema": "gtos.walkforward.exit_frontier_analysis.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "session": "AD", "block": "B754",
        "source": str(IN.relative_to(REPO)),
        "merged_from": merged_from,
        "baseline_caveat_for_the_two_trailing_sleeves": (
            "`asian_fade` and `metal_session_reversion` carry policy=trailing_runner "
            "(execution_packets.py:57,61) and AA published their economics under the TRAIL. "
            "This sweep's `as_walked` cell is the PLAIN stop/target/maxbars labelling for "
            "every sleeve including those two, so for them `as_walked` is NOT AA's published "
            "row and the two must not be compared. Their production contract is the cell "
            "marked `the LIVE contract` in the trail family."),
        "trail_bounds": {
            "question": ("B613's RULE is 'report both bounds' and it stands. Its READING — "
                         "that the production bound is the optimistic one — was measured on "
                         "`asian_fade`, a FADE. `simulate`'s same-bar arm-and-fill makes the "
                         "trail exit EARLIER at a price the bar may never have offered in "
                         "that sequence; on a reversion sleeve an early exit at a good price "
                         "over-claims, and on a continuation sleeve it UNDER-claims because "
                         "it cuts the runner. Measured over every trail cell here."),
            "n_cells_with_both_bounds": n,
            "n_honest_worse_than_production": len(honest_worse),
            "n_honest_better_than_production": len(honest_better),
            "by_mechanism": {m: {"n": len(v2), "mean_honest_minus_prod": round(
                statistics.fmean(v2), 6), "median": round(statistics.median(v2), 6),
                "frac_honest_better": round(sum(1 for x in v2 if x > 0) / len(v2), 4)}
                for m, v2 in sorted(by_mech.items())},
            "by_trail_arm_r": {str(a): {"n": len(v2), "mean_honest_minus_prod": round(
                statistics.fmean(v2), 6), "median": round(statistics.median(v2), 6),
                "frac_honest_better": round(sum(1 for x in v2 if x > 0) / len(v2), 4)}
                for a, v2 in sorted(by_arm.items())},
            "cells": trail_rows,
        },
        "stop_width_frontier": {
            "question": ("AA_COST_GEOMETRY_FRONTIER_V1.json gives each COST_GEOMETRY sleeve "
                         "the gross-in-R retention it needs at a 2x stop to break even. This "
                         "is the retention actually achieved, under both target conventions."),
            "aa_required_multiples_at_2x": aa_req,
            "aa_mean_gross_r_at_1x": aa_gross_1x,
            "the_correction_this_measures": (
                "AA's algebra is net(k) = (gross - c_var)/k - c_fixed, which treats cost as "
                "one term that scales as 1/k and one that does not. SWAP IS NEITHER: it grows "
                "with the HOLD, and a wider stop lengthens the hold. Measured on the swap "
                "columns below — every sleeve pays MORE nights at 2x than at 1x. So the "
                "required-multiple targets are optimistic for any carry-bearing sleeve, and "
                "the gap widens with the sleeve's nights."),
            "rows": fr_rows,
        },
        "live_contract_divergence": {
            "question": ("AA labelled the whole estate under plain stop/target/maxbars. Four "
                         "sleeves' live contract is partial_be_runner (execution_packets.py:"
                         "44-51) and the mx_* family carries a time stop B750 measured as "
                         "binding on 72-90 % of trades. For those sleeves AA's published "
                         "economics describe a contract the live book does not run."),
            "rows": div_rows,
        },
        "winners": {
            "sleeves_reaching_admit_anywhere": admits,
            "failing_gate_at_each_sleeves_best_cell": fails,
            "rows": win_rows,
        },
    }
    OUT.write_text(json.dumps(doc, indent=1, default=str))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return doc


if __name__ == "__main__":
    main()
