#!/usr/bin/env python3
"""Phase 0 T1 — the inverted-entry cost, measured, with an uncertainty band.

Four terms, each stated as MEASURED or MODELLED and each in units of the INVERTED
risk distance (which is 2.0x the original stop distance, so a fixed price cost is
worth half as many inverted R as original R).

  1. spread            already inside the walk (the labeler transforms the tape onto
                       the executable side). Reported as charged, bracketed by the
                       spread model's own low/high band, and validated at the exact
                       trigger instants against the broker tick archive where it
                       covers the window.
  2. entry timing      the labeler fills a MARKET order at the OPEN of the first
                       complete successor M1 bar, i.e. 60 s after the decision. A live
                       book fills within ~1 s. The tape drift over that minute is a
                       windfall or a penalty depending on sign, and it is the
                       momentum-entry term the plan asked for.
  3. execution slip    the residual sub-minute cost of a real market order, from the
                       broker-reconciled fill capture and from tick latency drift.
  4. commission/swap   carried unchanged from the sealed rows, rescaled to inverted R.
"""
from __future__ import annotations

import gzip
import json
import pickle
import subprocess
from collections import defaultdict
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
SLIPPAGE_ARTIFACT = (
    "docs/audits/fable5-vision-audit-20260725/phase21/cost/SLIPPAGE_PRICE_V1.json"
)
REPO = "/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725"


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


def stats(values):
    values = [v for v in values if v is not None]
    if not values:
        return {"n": 0}
    arr = np.asarray(values, dtype=float)
    return {
        "n": int(arr.size),
        "mean": float(arr.mean()),
        "median": float(np.median(arr)),
        "p10": float(np.percentile(arr, 10)),
        "p90": float(np.percentile(arr, 90)),
        "se": float(arr.std(ddof=1) / np.sqrt(arr.size)) if arr.size > 1 else None,
    }


def main():
    records = [row for row in load() if row["family"] in MARKET]
    elig = [
        row
        for row in records
        if row["cost_r"] <= 0.20 and row["inv"]["status"] in FILLED
    ]
    report = {
        "scope": {
            "records": len(records),
            "eligible_inverted_filled": len(elig),
            "eligibility": "cost_r <= 0.20, the funnel's own gate (candidate_funnel_analysis.py:52)",
        }
    }

    # ---- term 1: spread, as charged, and the model's own band ------------
    spread = {}
    for family in MARKET:
        rows = [row for row in elig if row["family"] == family]
        allrows = [row for row in records if row["family"] == family]
        spread[family] = {
            "eligible_spread_r_orig_units": stats([row["spread_r"] for row in rows]),
            "eligible_spread_r_inverted_units": stats(
                [row["spread_r"] * row["risk_price"] / row["risk_price_inv"] for row in rows]
            ),
            "all_population_spread_r_orig_units": stats(
                [row["spread_r"] for row in allrows]
            ),
        }
    report["term1_spread"] = {
        "charged_where": (
            "mechanically, inside terminal_gross_r: the entry transacts on the "
            "executable entry side and stop/target are compared against the executable "
            "exit side (quote_side.py:385-413, :1218-1247). One round trip = one spread."
        ),
        "source": "spread_model_v1, hour-aware, account FTMO, band mid",
        "per_family": spread,
    }

    # ---- term 2: entry timing (the 60 s-late modelled fill) --------------
    timing = {}
    for family in MARKET:
        rows = [
            row
            for row in elig
            if row["family"] == family and row["entry_drift_r_orig_dir"] is not None
        ]
        # positive D = tape moved in the ORIGINAL direction over the minute, so the
        # inverted contract sells higher / buys lower than a decision-instant fill:
        # a windfall of D/ratio inverted R that a live book would not receive.
        windfall = [
            row["entry_drift_r_orig_dir"] * row["risk_price"] / row["risk_price_inv"]
            for row in rows
        ]
        timing[family] = {
            "orig_dir_tape_drift_r_orig_units": stats(
                [row["entry_drift_r_orig_dir"] for row in rows]
            ),
            "inverted_windfall_r_inverted_units": stats(windfall),
            "per_month_windfall_mean": {
                month: stats(
                    [
                        row["entry_drift_r_orig_dir"] * row["risk_price"] / row["risk_price_inv"]
                        for row in rows
                        if row["month"] == month
                    ]
                ).get("mean")
                for month in MONTHS
            },
        }
    report["term2_entry_timing"] = {
        "what": (
            "resolve_post_submission_m1_lifecycle refuses the submission bar as causal "
            "and fills MARKET at the OPEN of the first complete successor M1 bar "
            "(quote_side.py:1278-1290), i.e. 60 s after the decision instant. A live "
            "book places at the decision instant. The tape drift over that minute is "
            "measured here from the same M1 source the walk used."
        ),
        "sign_convention": (
            "positive = the walk gives the INVERTED contract a better entry price than "
            "a decision-instant fill would, i.e. the walk is generous to the inversion "
            "by this much and a live result would be worse by it"
        ),
        "per_family": timing,
    }

    # ---- term 3: execution slippage --------------------------------------
    artifact = json.loads(
        subprocess.run(
            ["git", "show", f"origin/main:{SLIPPAGE_ARTIFACT}"],
            cwd=REPO, capture_output=True, text=True, check=True,
        ).stdout
    )
    ftmo = artifact["records"]["FTMO"]
    risk_by_symbol = defaultdict(list)
    for row in elig:
        risk_by_symbol[row["symbol"]].append(row["risk_price"])
    inv_risk_by_symbol = defaultdict(list)
    for row in elig:
        inv_risk_by_symbol[row["symbol"]].append(row["risk_price_inv"])
    measured = {}
    for symbol, record in sorted(ftmo.items()):
        if symbol not in inv_risk_by_symbol:
            continue
        median_inv_risk = float(np.median(inv_risk_by_symbol[symbol]))
        measured[symbol] = {
            "expected_adverse_price": record["expected_adverse_price"],
            "signed_mean_price": record["signed_mean_price"],
            "n_reconciled_fills": record["n"],
            "median_inverted_risk_price": median_inv_risk,
            "adverse_r_inverted_units": record["expected_adverse_price"] / median_inv_risk
            if median_inv_risk > 0
            else None,
            "candidates": len(inv_risk_by_symbol[symbol]),
        }
    weights = {s: v["candidates"] for s, v in measured.items()}
    total = sum(weights.values())
    pooled = (
        sum(measured[s]["adverse_r_inverted_units"] * weights[s] for s in measured) / total
        if total
        else None
    )
    report["term3_execution_slippage"] = {
        "artifact": SLIPPAGE_ARTIFACT,
        "artifact_accepted_rows": artifact["accepted_rows"],
        "estimator": artifact["records"]["FTMO"][next(iter(ftmo))]["estimator"],
        "caveat": (
            "these are the ARMED ESTATE's own reconciled entry fills (n=138 total, "
            "2026-06..07), not funnel entries; they carry no momentum conditioning and "
            "cover 8 of the 24 surface symbols. Transferred, not measured, for the funnel."
        ),
        "sealed_replay_charge_r_orig_units": 0.02,
        "sealed_replay_charge_source": (
            "config.selected_cell_default_expected_slippage_r, a flat constant "
            "(broker_net_cost_engine.py:718-728) -- 0.02 R on every row of every symbol"
        ),
        "per_symbol": measured,
        "candidate_weighted_adverse_r_inverted_units": pooled,
    }

    # ---- term 4: commission + swap ---------------------------------------
    report["term4_commission_swap"] = {
        "per_family": {
            family: {
                "commission_r_orig_units": stats(
                    [row["commission_r"] for row in elig if row["family"] == family]
                ),
                "swap_r_orig_units": stats(
                    [row["swap_r"] for row in elig if row["family"] == family]
                ),
                "deductible_r_inverted_units": stats(
                    [
                        row["inv"]["deductible"]
                        for row in elig
                        if row["family"] == family and row["inv"]["deductible"] is not None
                    ]
                ),
            }
            for family in MARKET
        }
    }

    # ---- the assembled inverted-entry cost and the live-realistic result --
    assembled = {}
    for family in MARKET:
        rows = [row for row in elig if row["family"] == family]
        walk = float(np.mean([row["inv"]["net"] for row in rows]))
        windfall = float(
            np.mean(
                [
                    row["entry_drift_r_orig_dir"] * row["risk_price"] / row["risk_price_inv"]
                    for row in rows
                    if row["entry_drift_r_orig_dir"] is not None
                ]
            )
        )
        assembled[family] = {
            "n": len(rows),
            "walk_net_r": walk,
            "entry_timing_windfall_r": windfall,
            "live_realistic_net_r": walk - windfall,
            "note": "live_realistic removes the 60 s free look the walk hands the inversion",
        }
    report["assembled"] = assembled

    path = OUT / "receipts/P0_T1_COST.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(report, indent=1, sort_keys=True, allow_nan=False) + "\n")
    print("WROTE", path)
    print(f"{'family':34s} {'walk net':>9s} {'timing':>9s} {'live-real':>10s} {'spread(inv)':>12s}")
    for family in MARKET:
        a = assembled[family]
        s = spread[family]["eligible_spread_r_inverted_units"]["median"]
        print(
            f"{family:34s} {a['walk_net_r']:+9.4f} {a['entry_timing_windfall_r']:+9.4f} "
            f"{a['live_realistic_net_r']:+10.4f} {s:12.4f}"
        )
    print("candidate-weighted broker-reconciled adverse slippage, inverted R:", pooled)


if __name__ == "__main__":
    main()
