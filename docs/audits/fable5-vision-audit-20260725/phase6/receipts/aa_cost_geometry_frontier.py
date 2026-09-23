"""Turn every COST_GEOMETRY prescription into a number the repair has to beat.

    python3 docs/audits/fable5-vision-audit-20260725/phase6/receipts/aa_cost_geometry_frontier.py

WHAT THIS IS FOR
----------------
The diagnostic head says, for a sleeve whose gross is positive and whose net is not:
*"commission scales as 1/stop, so sweep stop width 1.0 -> 2.0x ATR."* That is a direction,
not a target, and a direction is what a repair session has to guess at.

The cost half of that sweep is **exactly computable without regenerating anything**, because
`cost_r` is an explicit function of the stop distance:

    commission_R = commission_ccy_per_lot / (sl * usd_per_price_unit_per_lot)   ~ 1/sl
    spread_R     = spread_price / sl                                           ~ 1/sl
    swap_R       = drag_per_night * nights / sl                                ~ 1/sl
    slippage_R   = measured R at the live geometry                             FIXED in R

So widening the stop by k divides the first three by k and leaves the fourth alone. What it
does NOT do is tell you what happens to gross R — a wider stop is a different trade, with a
different exit path, and only regeneration answers that (Session AD's parameter sweep, §5.1).

The useful thing that falls out is a **budget**: at stop multiple k the sleeve saves
`cost(1) - cost(k)` in R per trade, so the repair pays if and only if regeneration shows
gross falling by LESS than that. This file publishes that budget per sleeve per k, which
converts "sweep the stop" into "the sweep must keep gross within X of its current value" —
a falsifiable target instead of a hopeful direction.

TWO HONEST LIMITS, STATED SO NOBODY READS MORE INTO IT
------------------------------------------------------
1. **The R unit moves with the stop.** At k=2 the same price move is half the R, so a
   sleeve whose gross survives in *price* terms still halves in R terms. The naive
   expectation is therefore `gross(k) ~ gross(1)/k`, and the budget below is the amount of
   degradation BEYOND nothing — i.e. it answers "does cost fall faster than gross", which
   is the only question that matters and the one the 1/k scaling of BOTH sides makes
   non-obvious. Both scalings are published so the reader can do the comparison either way.
2. **Only the FIRST-ORDER cost effect is here.** A wider stop is hit less often, which
   changes the hold, which changes the swap nights. That second-order effect needs the
   regeneration too and is not modelled; it moves the budget in the sleeve's favour (fewer
   stop-outs, longer holds, more swap) or against it, and the sign is not knowable here.

Every cell is logged to the trial-budget ledger.
"""

from __future__ import annotations

import collections
import datetime as dt
import gzip
import json
import math
import os
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.costs import CostTruthError, cost_r, load_broker_true_costs  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
)

HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts"
IN = Path(os.environ.get("AA_TRADES_IN") or (HERE / "AA_ESTATE_TRADES.json.gz")).resolve()
OUT = HERE / f"AA_COST_GEOMETRY_FRONTIER_V1{os.environ.get('AA_OUT_SUFFIX', '')}.json"
COSTS = (REPO
         / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json")

#: Stop-width multiples. 1.0 is the sleeve as authored; 2.0 is the top of the range
#: `FOURTH_REVIEW.md` §3.2 names for `fx_jpy` ("1.0 -> 1.5-2.0x ATR").
MULTIPLES = (1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0)


def main() -> dict:
    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AA")
    truth = load_broker_true_costs(COSTS)
    with gzip.open(IN, "rt") as fh:
        raw = json.load(fh)

    out: dict = {
        "schema": "gtos.walkforward.cost_geometry_frontier.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "source": str(IN),
        "cost_artifact": str(COSTS.relative_to(REPO)),
        "multiples": list(MULTIPLES),
        "method": (
            "cost_r re-evaluated at sl' = k * sl for every trade, holding everything else "
            "fixed. Exact for the cost side (three of four terms are 1/sl, slippage is "
            "fixed in R); says NOTHING about gross, which needs regeneration."
        ),
        "limits": [
            "the R unit moves with the stop, so gross ~ gross/k is the naive expectation "
            "and the budget below is degradation BEYOND that; both scalings are published",
            "second-order effects (a wider stop is hit less often -> longer holds -> more "
            "swap nights) need the regeneration and are not modelled",
        ],
        "sleeves": {},
    }

    for sleeve, rows in sorted(raw["trades"].items()):
        if not rows:
            continue
        base_gross = statistics.fmean(float(r["r_gross"]) for r in rows)
        per_k: dict[str, dict] = {}
        n_unpriced = collections.Counter()
        for k in MULTIPLES:
            costs_r: list[float] = []
            terms = {"commission_r": 0.0, "swap_r": 0.0, "spread_r": 0.0, "slippage_r": 0.0}
            for r in rows:
                sl = float(r["sl_distance_price"]) * k
                try:
                    b = cost_r(
                        r["symbol"], "FTMO",
                        float(r["hold_hours"]),
                        sl_distance_price=sl,
                        entry_price=float(r["entry_price"]),
                        side=("LONG" if int(r["direction"]) > 0 else "SHORT"),
                        entry_utc=dt.datetime.fromisoformat(r["entry_utc"]),
                        costs=truth,
                    )
                except (CostTruthError, TypeError, ValueError, KeyError):
                    n_unpriced[k] += 1
                    continue
                costs_r.append(float(b.total_r.value))
                terms["commission_r"] += float(b.commission_r.value)
                terms["swap_r"] += float(b.swap_r.value)
                terms["spread_r"] += float(b.spread_r.value)
                terms["slippage_r"] += float(b.slippage_r.value)
            if not costs_r:
                continue
            n = len(costs_r)
            per_k[f"{k:g}"] = {
                "n_priced": n,
                "mean_cost_r": round(math.fsum(costs_r) / n, 6),
                "terms_mean_r": {t: round(v / n, 6) for t, v in terms.items()},
            }
        if "1" not in per_k:
            continue
        c1 = per_k["1"]["mean_cost_r"]
        for kk, v in per_k.items():
            saved = c1 - v["mean_cost_r"]
            k = float(kk)
            v["cost_saved_vs_1x_r"] = round(saved, 6)
            v["naive_gross_at_k_r"] = round(base_gross / k, 6)
            v["net_at_naive_gross_r"] = round(base_gross / k - v["mean_cost_r"], 6)
            # The budget: how much gross may fall (in R, from its 1x value) before the
            # widened stop stops paying. Positive means there is room.
            v["gross_degradation_budget_r"] = round(saved, 6)
            v["breakeven_gross_at_k_r"] = round(v["mean_cost_r"], 6)
            ledger.record(
                mechanism="stop_width_frontier", sleeve=sleeve,
                variant={"stop_multiple": k, "cost_artifact": "v1_1"},
                window="full_archive", outcome="evaluated",
                metric=v["mean_cost_r"], metric_name="mean_cost_r",
                note="cost-side only; gross needs regeneration (Session AD)",
            )
        for kk, v in per_k.items():
            # THE NUMBER SESSION AD ACTUALLY NEEDS: how much bigger must gross-in-R be at
            # this stop width for the sleeve to break even? Anything below 1.0 means the
            # sleeve is already net-positive there.
            v["required_gross_multiple_vs_1x"] = (
                round(v["mean_cost_r"] / base_gross, 4) if base_gross > 1e-9 else None
            )
        best = max(per_k.items(), key=lambda kv: kv[1]["net_at_naive_gross_r"])
        slip = per_k["1"]["terms_mean_r"]["slippage_r"]
        helps = bool(best[1]["net_at_naive_gross_r"] > per_k["1"]["net_at_naive_gross_r"] + 1e-9)
        out["sleeves"][sleeve] = {
            "n_trades": len(rows),
            "mean_gross_r_at_1x": round(base_gross, 6),
            "mean_net_r_at_1x": round(base_gross - c1, 6),
            "by_multiple": per_k,
            "best_multiple_under_naive_scaling": best[0],
            "net_at_best_under_naive_scaling": best[1]["net_at_naive_gross_r"],
            "naive_scaling_helps": helps,
            # THE ALGEBRA, STATED, BECAUSE "helps: YES" IS THE MOST MISREADABLE FIELD HERE.
            # net(k) = gross/k - c_var/k - c_fixed = (gross - c_var)/k - c_fixed, where
            # c_fixed is slippage (measured in R at the live geometry, so it does not
            # rescale). So `helps` is true exactly when gross < c_var, and in that case
            # net(k) rises with k toward the ASYMPTOTE -c_fixed and can never exceed it.
            "naive_asymptote_net_r": round(-slip, 6),
            "reading": (
                (f"'helps' is TRUE only because variable cost ({c1 - slip:.5f} R) exceeds "
                 f"gross ({base_gross:.5f} R): under naive 1/k rescaling net rises with k "
                 f"toward {-slip:+.5f} R and CANNOT become positive. Widening the stop "
                 f"rescues this sleeve only if the wider stop makes gross-in-R rise rather "
                 f"than fall — i.e. if it converts stop-outs into runners. That is the "
                 f"regeneration question, and the target is "
                 f"{per_k.get('2', {}).get('required_gross_multiple_vs_1x')}x current "
                 f"gross-in-R at k=2.")
                if helps else
                (f"variable cost ({c1 - slip:.5f} R) is below gross ({base_gross:.5f} R), "
                 f"so under naive rescaling net FALLS with k and the authored stop is "
                 f"already the best of this family. A stop sweep is not this sleeve's "
                 f"repair; read its prescription for what is.")
            ),
            "unpriced_by_multiple": {f"{k:g}": n_unpriced[k] for k in MULTIPLES if n_unpriced[k]},
        }

    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"wrote {OUT.relative_to(REPO)}")
    print(f"{'sleeve':42s} {'gross1x':>9s} {'net1x':>9s} {'cost1x':>8s} {'cost2x':>8s} "
          f"{'save@2x':>8s} {'needx@2x':>9s} {'asympt':>8s}")
    for s, v in sorted(out["sleeves"].items(),
                       key=lambda kv: -(kv[1]["net_at_best_under_naive_scaling"] or 0)):
        b = v["by_multiple"]
        c2 = b.get("2", {})
        need = c2.get("required_gross_multiple_vs_1x")
        print(f"{s:42s} {v['mean_gross_r_at_1x']:+9.5f} {v['mean_net_r_at_1x']:+9.5f} "
              f"{b['1']['mean_cost_r']:8.5f} {c2.get('mean_cost_r', float('nan')):8.5f} "
              f"{c2.get('cost_saved_vs_1x_r', float('nan')):8.5f} "
              f"{(f'{need:.2f}x' if need is not None else '    -'):>9s} "
              f"{v['naive_asymptote_net_r']:+8.5f}")
    print(f"ledger now {ledger.summary()['n_trials']} rows")
    return out


if __name__ == "__main__":
    main()
