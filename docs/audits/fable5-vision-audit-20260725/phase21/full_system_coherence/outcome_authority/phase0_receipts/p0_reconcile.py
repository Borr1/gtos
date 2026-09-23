#!/usr/bin/env python3
"""Phase 0 T2 reconciliation — the plan's arithmetic table vs the real walk.

Three estimators on exactly the same candidates:

  A   the plan's method as published: from the ORIGINAL walk outcome, map
      TARGET -> -1 R_new, STOP -> +1/1.5 R_new, TIME_STOP -> -gross/1.5.
      The plan's claimed geometry is 1.5R.
  A2  the same method at the geometry the sealed rows actually carry (RR 2.0):
      TARGET -> -1, STOP -> +1/2.0, TIME_STOP -> -gross/2.0.
  B   the real inverted walk through the committed labeler.

The A -> A2 step prices the plan's RR assumption; A2 -> B prices everything the
real walk adds (own-side spread at the inverted barriers, changed censoring,
exact time-stop payouts, changed fill price).
"""
from __future__ import annotations

import gzip
import json
import pickle
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

OUT = Path("/private/tmp/phase0-inversion")
MONTHS = ("feb", "apr", "may", "jun", "jul")
MARKET = (
    "structural_distance_extreme",
    "liquidity_sweep_reclaim",
    "cross_asset_lead_lag",
    "displacement_continuation",
    "session_open_range_break",
    "regime_transition_break",
    "volatility_compression_expansion",
)
FILLED = ("RESOLVED_FILLED_TARGET", "RESOLVED_FILLED_STOP", "RESOLVED_FILLED_TIME_STOP")


def load():
    records = []
    for month in MONTHS:
        path = OUT / f"walk_{month}.pkl.gz"
        if not path.is_file():
            continue
        rows = pickle.load(gzip.open(path, "rb"))
        for row in rows:
            row["month"] = month
        records.extend(rows)
    return records


def arithmetic(row, rr, *, cost_r=0.0):
    """The plan's inversion arithmetic on the ORIGINAL outcome, at assumed `rr`."""
    state = row["orig"]["state"]
    if state == "TARGET":
        value = -1.0
    elif state == "STOP":
        value = 1.0 / rr
    elif state == "TIME_STOP":
        value = -row["orig"]["gross"] / rr
    else:
        return None
    return value - cost_r


def mean(values):
    values = [v for v in values if v is not None]
    return float(np.mean(values)) if values else None


def main():
    records = [row for row in load() if row["family"] in MARKET]
    report = {"months_loaded": sorted({row["month"] for row in records})}
    table = {}
    for family in MARKET:
        rows = [row for row in records if row["family"] == family]
        orig_filled = [row for row in rows if row["orig"]["status"] in FILLED]
        inv_filled = [row for row in rows if row["inv"]["status"] in FILLED]
        both = [
            row
            for row in rows
            if row["orig"]["status"] in FILLED and row["inv"]["status"] in FILLED
        ]
        entry = {
            "n_orig_filled": len(orig_filled),
            "n_inv_filled": len(inv_filled),
            "n_both_filled": len(both),
            "A_plan_rr1p5_gross": mean([arithmetic(row, 1.5) for row in orig_filled]),
            "A_plan_rr1p5_less_0p05": mean(
                [arithmetic(row, 1.5, cost_r=0.05) for row in orig_filled]
            ),
            "A2_true_rr2p0_gross": mean([arithmetic(row, 2.0) for row in orig_filled]),
            "A2_true_rr2p0_less_deductible": mean(
                [
                    arithmetic(row, 2.0, cost_r=row["inv"]["deductible"] or 0.0)
                    for row in orig_filled
                    if row["inv"]["deductible"] is not None
                ]
            ),
            "B_real_walk_gross": mean([row["inv"]["gross"] for row in inv_filled]),
            "B_real_walk_net": mean([row["inv"]["net"] for row in inv_filled]),
            # like-for-like: the same candidates under both estimators
            "matched_A2": mean([arithmetic(row, 2.0) for row in both]),
            "matched_B_gross": mean([row["inv"]["gross"] for row in both]),
            "orig_net": mean([row["orig"]["net"] for row in orig_filled]),
        }
        # eligible (the cost gate the funnel actually applies)
        elig = [row for row in inv_filled if row["cost_r"] <= 0.20]
        entry["eligible"] = {
            "n": len(elig),
            "share_of_filled": len(elig) / len(inv_filled) if inv_filled else None,
            "B_real_walk_net": mean([row["inv"]["net"] for row in elig]),
            "per_month": {
                month: {
                    "n": sum(1 for row in elig if row["month"] == month),
                    "mean": mean(
                        [row["inv"]["net"] for row in elig if row["month"] == month]
                    ),
                }
                for month in MONTHS
            },
        }
        entry["cross_tab_state"] = {
            f"{row_state}->{inv_state}": count
            for (row_state, inv_state), count in sorted(
                Counter(
                    (
                        row["orig"]["state"] or row["orig"]["status"],
                        row["inv"]["state"] or row["inv"]["status"],
                    )
                    for row in rows
                ).items(),
                key=lambda item: -item[1],
            )[:10]
        }
        entry["spread_r"] = {
            "median": float(np.median([row["spread_r"] for row in rows])),
            "p90": float(np.percentile([row["spread_r"] for row in rows], 90)),
        }
        entry["cost_r_median"] = float(np.median([row["cost_r"] for row in rows]))
        table[family] = entry
    report["families"] = table
    path = OUT / "receipts/P0_RECONCILIATION.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(report, indent=1, sort_keys=True, allow_nan=False) + "\n")
    print("WROTE", path)
    header = (
        f"{'family':34s} {'A(1.5)':>8s} {'A2(2.0)':>8s} {'B gross':>8s} {'B net':>8s} "
        f"{'B net elig':>10s} {'spr med':>8s}"
    )
    print(header)
    for family in MARKET:
        e = table[family]
        print(
            f"{family:34s} {e['A_plan_rr1p5_gross']:+8.4f} {e['A2_true_rr2p0_gross']:+8.4f} "
            f"{e['B_real_walk_gross']:+8.4f} {e['B_real_walk_net']:+8.4f} "
            f"{e['eligible']['B_real_walk_net']:+10.4f} {e['spread_r']['median']:8.4f}"
        )


if __name__ == "__main__":
    main()
