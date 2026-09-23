"""Session AH -- is the entry-hour saving an artifact of the era extrapolation?

    python3 .../ah_entry_era_robustness.py

The saving arm C books is a SPREAD saving, and the spread charge at broker hour 00 rests on
two things: the hour multiplier (measured on the 37-day tick window -- solid ground for
today) and the era ratio (measured from bar minima, extrapolated). If the whole saving lived
in eras where the era term is doing the work, it would be a modelling artifact.

So the same before/after is cut three ways, none of which looks at an outcome to decide the
cut: by era CLASS of the trade's own quarter (RECORDED vs the rest), by decade, and by
whether the trade sits inside the tick-measured reference era. If the saving survives on
RECORDED eras and post-2020 trades, it is a property of the broker's quoted spread and not of
the model's extrapolation.
"""

from __future__ import annotations

import collections
import datetime as dt
import gzip
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO))

from src.costs.model import cost_r, load_broker_true_costs  # noqa: E402
from src.costs.spread_model import load_spread_model  # noqa: E402

TRADES = HERE / "AH_ENTRY_SHIFT_TRADES.json.gz"
OUT = HERE / "AH_ENTRY_ERA_ROBUSTNESS.json"
COSTS = REPO / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"
SAMPLE = 3


def main() -> int:
    with gzip.open(TRADES, "rt") as fh:
        art = json.load(fh)
    costs = load_broker_true_costs(COSTS)
    sm = load_spread_model()

    by_key = collections.defaultdict(dict)
    for r in art["trades"]:
        by_key[(r["member"], r["decision_bar_iso"])][r["arm"]] = r
    pairs = [(v["B_d1close_h4exit"], v["C_h4next_h4exit"]) for v in by_key.values()
             if {"B_d1close_h4exit", "C_h4next_h4exit"} <= set(v)
             and not v["B_d1close_h4exit"].get("dropped")
             and not v["C_h4next_h4exit"].get("dropped")
             and v["A_d1close_d1exit"]["engine_reachable"]]
    print(f"{len(pairs)} B/C pairs on the reachable common population")

    cells = collections.defaultdict(lambda: collections.defaultdict(list))
    for i, (b, c) in enumerate(pairs):
        if i % SAMPLE:
            continue
        tb = dt.datetime.fromisoformat(b["entry_utc"])
        try:
            est = sm.estimate(b["symbol"], "FTMO", tb, band="mid")
            cb = cost_r(b["symbol"], "FTMO", b["hold_hours"],
                        sl_distance_price=b["sl_distance_price"],
                        entry_price=b["entry_price"], entry_utc=tb,
                        spread_band="mid", costs=costs)
            tc = dt.datetime.fromisoformat(c["entry_utc"])
            cc = cost_r(c["symbol"], "FTMO", c["hold_hours"],
                        sl_distance_price=c["sl_distance_price"],
                        entry_price=c["entry_price"], entry_utc=tc,
                        spread_band="mid", costs=costs)
        except Exception:                                        # noqa: BLE001, S112
            continue
        # THE CUT THAT ACTUALLY ANSWERS THE QUESTION, and it is not `era_class`.
        # An adversarial pass on this session's own claim caught the conflation: `RECORDED`
        # says the era's spread series is a dispersed per-bar measurement, NOT that its ratio
        # is near 1 -- the RECORDED cell's median era ratio is ~2.1, so the era term is still
        # doing work there. `era_ratio_band` is the era-NEUTRAL cut: rows whose own era ratio
        # sits inside [0.9, 1.1] pay essentially the tick-measured hour term and nothing
        # extrapolated.
        er = est.era_ratio
        band = ("neutral_0.9_1.1" if 0.9 <= er <= 1.1
                else "validated_0.78_1.30" if 0.78 <= er <= 1.30
                else "extrapolated_gt_1.30" if er > 1.30 else "extrapolated_lt_0.78")
        keys = [("all", "all"),
                ("era_class", est.era_class),
                ("decade", f"{tb.year // 10 * 10}s"),
                ("era_ratio_band", band),
                ("recorded_only", "RECORDED" if est.era_class == "RECORDED" else "other")]
        for dim, key in keys:
            acc = cells[dim][key]
            acc.append((cb.spread_r.value, cc.spread_r.value,
                        cb.total_r.value, cc.total_r.value,
                        b["r_gross"], c["r_gross"], er,
                        est.detail.get("hour_mult_reference"),
                        est.detail.get("hour_mult_effective")))

    out = {"schema": "gtos.ah.entry_era_robustness.v1",
           "generated_by": str(Path(__file__).relative_to(REPO)),
           "sample_every": SAMPLE, "n_pairs_total": len(pairs), "cells": {}}
    for dim, d in sorted(cells.items()):
        out["cells"][dim] = {}
        for key, acc in sorted(d.items()):
            n = len(acc)
            out["cells"][dim][key] = {
                "n": n,
                "spread_r_B": statistics.mean(a[0] for a in acc),
                "spread_r_C": statistics.mean(a[1] for a in acc),
                "spread_saving_r": statistics.mean(a[0] - a[1] for a in acc),
                "total_r_B": statistics.mean(a[2] for a in acc),
                "total_r_C": statistics.mean(a[3] for a in acc),
                "cost_saving_r": statistics.mean(a[2] - a[3] for a in acc),
                "gross_B": statistics.mean(a[4] for a in acc),
                "gross_C": statistics.mean(a[5] for a in acc),
                "gross_delta_r": statistics.mean(a[5] - a[4] for a in acc),
                "net_delta_r": statistics.mean((a[5] - a[3]) - (a[4] - a[2]) for a in acc),
                # How much of this cell's charge is the era term rather than the hour term?
                "era_ratio_median": statistics.median(a[6] for a in acc),
                "era_ratio_mean": statistics.mean(a[6] for a in acc),
                "frac_era_ratio_in_0.9_1.1": sum(
                    1 for a in acc if 0.9 <= a[6] <= 1.1) / n,
                "frac_era_ratio_in_validated_0.78_1.30": sum(
                    1 for a in acc if 0.78 <= a[6] <= 1.30) / n,
                "hour_mult_effective_over_reference_median": statistics.median(
                    [a[8] / a[7] for a in acc if a[7]]) if any(a[7] for a in acc) else None,
            }
    OUT.write_text(json.dumps(out, indent=1))
    for dim in out["cells"]:
        print(f"\n--- {dim}")
        print(f"{'cell':22s} {'n':>6s} {'save':>8s} {'dNet':>8s} {'eraR~':>7s} "
              f"{'in.9-1.1':>9s} {'eff/ref':>8s}")
        for k, v in out["cells"][dim].items():
            print(f"{k:22s} {v['n']:6d} {v['spread_saving_r']:8.4f} {v['net_delta_r']:8.4f} "
                  f"{v['era_ratio_median']:7.3f} {v['frac_era_ratio_in_0.9_1.1']:9.3f} "
                  f"{(v['hour_mult_effective_over_reference_median'] or 0):8.3f}")
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
