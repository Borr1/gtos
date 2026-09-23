#!/usr/bin/env python3
"""Phase 0 — the exact decomposition from the plan's published number to the walk."""
from __future__ import annotations

import gzip
import json
import pickle
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
PLAN = json.loads((Path("/private/tmp/w21-puzzle-cache") / "INVERSION_ANSWERS.json").read_text())


def load(directory=OUT):
    records = []
    for month in MONTHS:
        path = directory / f"walk_{month}.pkl.gz"
        if not path.is_file():
            continue
        rows = pickle.load(gzip.open(path, "rb"))
        for row in rows:
            row["month"] = month
        records.extend(rows)
    return records


def arith(row, rr):
    state = row["orig"]["state"]
    if state is None:
        return None
    if state == "TARGET":
        return -1.0
    if state == "STOP":
        return 1.0 / rr
    return -row["orig"]["gross"] / rr


def main():
    records = load()
    live_by_key = {}
    for month in MONTHS:
        path = OUT / f"live_{month}.pkl.gz"
        if path.is_file():
            for row in pickle.load(gzip.open(path, "rb")):
                live_by_key[row["key"]] = row

    out = {"steps": {}, "note": (
        "each step changes exactly one thing; the candidate set is identical to the "
        "plan's (n matches per family and per month, see plan_n vs walk_n)"
    )}
    for family in MARKET:
        rows = [r for r in records if r["family"] == family]
        of = [r for r in rows if r["orig"]["status"] in FILLED]
        inf = [r for r in rows if r["inv"]["status"] in FILLED]
        elig = [r for r in inf if r["cost_r"] <= 0.20]
        s0 = PLAN.get(family, {}).get("inverted_mean_R")
        s1 = float(np.mean([arith(r, 1.5) for r in of]))
        s2 = float(np.mean([arith(r, 2.0) for r in of]))
        s3 = float(np.mean([r["inv"]["gross"] for r in inf]))
        s4 = float(np.mean([r["inv"]["net"] for r in inf]))
        s5 = float(np.mean([r["inv"]["net"] for r in elig]))
        live = [
            live_by_key[r["key"]]["inv_live"]["net"]
            for r in elig
            if r["key"] in live_by_key
            and live_by_key[r["key"]]["inv_live"]["status"] in FILLED
        ]
        # decision-instant-fill arm on its own eligible population
        keys_elig = {r["key"] for r in rows if r["cost_r"] <= 0.20}
        live_all = [
            v["inv_live"]["net"]
            for k, v in live_by_key.items()
            if k in keys_elig and v["inv_live"]["status"] in FILLED
        ]
        out["steps"][family] = {
            "plan_n": PLAN.get(family, {}).get("n_filled_5mo"),
            "walk_n_orig_filled": len(of),
            "walk_n_inv_filled": len(inf),
            "walk_n_inv_filled_eligible": len(elig),
            "s0_plan_published": s0,
            "s1_plan_method_zero_cost_rr1p5": s1,
            "s1_minus_s0_implied_flat_cost": None if s0 is None else s1 - s0,
            "s2_same_method_true_rr2p0": s2,
            "d_geometry_correction": s2 - s1,
            "s3_real_walk_gross": s3,
            "d_real_walk_vs_arithmetic": s3 - s2,
            "s4_real_walk_net": s4,
            "d_deductible": s4 - s3,
            "s5_real_walk_net_cost_eligible": s5,
            "d_eligibility_gate": s5 - s4,
            "s6_decision_instant_fill_eligible": float(np.mean(live_all)) if live_all else None,
            "d_live_fill_convention": (
                float(np.mean(live_all)) - s5 if live_all else None
            ),
        }
    path = OUT / "receipts/P0_DECOMPOSITION.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(out, indent=1, sort_keys=True, allow_nan=False) + "\n")
    print("WROTE", path)
    hdr = f"{'family':30s} {'plan':>7s} {'A1.5':>7s} {'A2.0':>7s} {'walk g':>7s} {'walk n':>7s} {'elig':>7s} {'live':>7s}"
    print(hdr)
    for family in MARKET:
        s = out["steps"][family]
        live = s["s6_decision_instant_fill_eligible"]
        print(
            f"{family:30s} {(s['s0_plan_published'] or 0):+7.4f} {s['s1_plan_method_zero_cost_rr1p5']:+7.4f} "
            f"{s['s2_same_method_true_rr2p0']:+7.4f} {s['s3_real_walk_gross']:+7.4f} "
            f"{s['s4_real_walk_net']:+7.4f} {s['s5_real_walk_net_cost_eligible']:+7.4f} "
            + (f"{live:+7.4f}" if live is not None else "    n/a")
        )


if __name__ == "__main__":
    main()
