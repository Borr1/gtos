#!/usr/bin/env python3
"""Phase 0 T4 — the LIMIT families under inversion.

Two questions, in order:

  1. Is an inverted LIMIT contract WELL-DEFINED? Answered structurally, from the
     estate's own execution semantics.
  2. If so, can it be MEASURED with the committed machinery? Answered by running the
     committed resolver on the inverted LIMIT contract and reporting what it does.

Plus a bounded arithmetic estimate from the sealed labels, using the A2 estimator
whose bias against a real walk this session has now MEASURED on seven MARKET
families.
"""
from __future__ import annotations

import gzip
import json
import pickle
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, "/private/tmp/phase0-inversion")

OUT = Path("/private/tmp/phase0-inversion")
CACHE = Path("/private/tmp/w21-puzzle-cache")
MONTHS = ("feb", "apr", "may", "jun", "jul")
LIMIT_FAMILIES = ("current_fvg_fill", "current_ob_retest", "current_breaker_re_entry")
STATE = {
    "RESOLVED_FILLED_TARGET": "TARGET",
    "RESOLVED_FILLED_STOP": "STOP",
    "RESOLVED_FILLED_TIME_STOP": "TIME_STOP",
}


def stats(values):
    values = [v for v in values if v is not None]
    if not values:
        return {"n": 0}
    arr = np.asarray(values, dtype=float)
    return {
        "n": int(arr.size),
        "mean": float(arr.mean()),
        "median": float(np.median(arr)),
        "se": float(arr.std(ddof=1) / np.sqrt(arr.size)) if arr.size > 1 else None,
    }


def a2(row, rr=2.0, *, charge):
    """Corrected inversion arithmetic on a sealed label (RR 2.0)."""
    state = STATE.get(row["lifecycle_label_status"])
    if state is None:
        return None
    gross = float(row["terminal_net_r"]) + float(row["deductible_cost_r"])
    if state == "TARGET":
        value = -1.0
    elif state == "STOP":
        value = 1.0 / rr
    else:
        value = -gross / rr
    return value - (float(row["deductible_cost_r"]) / rr if charge else 0.0)


def main():
    report = {
        "question_1_well_defined": {
            "verdict": "YES, but it is a different order type",
            "reasoning": [
                "The three LIMIT families rest a pending entry at a level AWAY from the "
                "market (limit_marketable_at_decision is False on 98.9 % of rows; median "
                "distance_to_limit_risk 4.45 risk units).",
                "A LONG resting below the market is a BUY LIMIT. Inverting the side while "
                "keeping the level makes it a SELL order below the market, which is a SELL "
                "STOP, not a SELL LIMIT.",
                "The trigger EVENT is nearly the same (price falling to the level) but the "
                "trigger QUOTE SIDE flips: a BUY LIMIT/BUY STOP triggers on the ASK and a "
                "SELL on the BID (quote_side.entry_trigger_level_on_tape, citing "
                "execution.py:6197), so the two trigger one spread apart.",
                "The FILL PRICE convention inverts, and this is the substantive change: a "
                "LIMIT fills at its level OR BETTER (a gap through the level is price "
                "improvement); a STOP fills at its level OR WORSE (a gap through the level "
                "is slippage). The plan's premise that 'fill dynamics change' is correct, "
                "and the direction is adverse to the inversion.",
            ],
        },
        "question_2_measurable_with_committed_machinery": {
            "verdict": "NO",
            "blocking_facts": [
                "resolve_post_submission_m1_lifecycle accepts only MARKET or LIMIT and "
                "raises on anything else (quote_side.py:1059-1063). There is no STOP-entry "
                "branch anywhere in the resolver.",
                "Its limit-touch predicate is hardwired to the direction: "
                "limit_touched = low <= entry for direction > 0 else high >= entry "
                "(quote_side.py:1249-1250). Flipping the side of a BUY LIMIT therefore "
                "asks 'did the HIGH reach a level BELOW the market', which is true at the "
                "submission bar, so the row is censored as "
                "CENSORED_SUBMISSION_BAR_LIMIT_TOUCH_ORDERING (:1270-1276) rather than "
                "resolved. The measured degeneracy is reported below.",
                "The favourable-open fill branch "
                "(FAVORABLE_EXECUTABLE_SIDE_M1_OPEN_THROUGH_LIMIT, :1300-1310) grants "
                "price improvement on a gap. For a stop entry that same bar must pay the "
                "gap. Reusing it would systematically flatter the inverted contract.",
                "The submission-bar guard would have to be replaced: a stop entry that is "
                "already through its level at submission is an immediate market order, not "
                "an ordering ambiguity.",
            ],
            "machinery_required": [
                "a STOP order type in resolve_post_submission_m1_lifecycle with (a) the "
                "direction-inverted touch predicate, (b) adverse gap fill at the "
                "executable-side open rather than at the level, (c) an "
                "already-through-at-submission disposition that fills at market rather "
                "than censoring, and (d) its own censoring rule for a stop trigger and a "
                "terminal touch inside one M1 bar;",
                "a matching generator hook so the inverted contract is emitted rather "
                "than reconstructed post hoc;",
                "tests pinning that a STOP fill is never better than its level, which is "
                "the one property the LIMIT branch deliberately violates.",
            ],
            "estimated_scope": "one focused session on quote_side.py plus its test module",
        },
    }

    # ---- the measured degeneracy -----------------------------------------
    demo_path = OUT / "walk_limit_demo.pkl.gz"
    if demo_path.is_file():
        rows = pickle.load(gzip.open(demo_path, "rb"))
        report["question_2_measurable_with_committed_machinery"]["measured_degeneracy"] = {
            "scope": f"{len(rows)} LIMIT-family candidates, one trading day, both arms walked",
            "orig_status": dict(Counter(row["orig"]["status"] for row in rows).most_common()),
            "inverted_status": dict(
                Counter(row["inv"]["status"] for row in rows).most_common()
            ),
            "orig_fill_convention": dict(
                Counter(
                    row["orig"]["fill_convention"]
                    for row in rows
                    if row["orig"]["fill_convention"]
                ).most_common()
            ),
        }

    # ---- bounded arithmetic estimate from the sealed labels ---------------
    per_family = {}
    for family in LIMIT_FAMILIES:
        per_month, pooled_rows = {}, []
        for month in MONTHS:
            rows = [
                row
                for row in pickle.load(gzip.open(CACHE / f"rows_{month}.pkl.gz", "rb"))
                if row["origin_family"] == family
                and row["lifecycle_label_status"] in STATE
            ]
            pooled_rows.extend(rows)
            per_month[month] = {
                "n": len(rows),
                "A2_charged": stats([a2(row, charge=True) for row in rows]).get("mean"),
            }
        elig = [row for row in pooled_rows if row["cost_r"] <= 0.20]
        states = Counter(STATE[row["lifecycle_label_status"]] for row in pooled_rows)
        barrier = states["TARGET"] + states["STOP"]
        per_family[family] = {
            "filled_n": len(pooled_rows),
            "eligible_n": len(elig),
            "orig_hit_rate": states["TARGET"] / barrier if barrier else None,
            "driftless_benchmark_at_rr2": 1 / 3,
            "time_stop_share": states["TIME_STOP"] / len(pooled_rows) if pooled_rows else None,
            "orig_mean_net_r": stats(
                [float(row["terminal_net_r"]) for row in pooled_rows]
            ).get("mean"),
            "spread_r_median": float(np.median([row["spread_r"] for row in pooled_rows])),
            "cost_r_median": float(np.median([row["cost_r"] for row in pooled_rows])),
            "A2_pooled_charged": stats([a2(row, charge=True) for row in pooled_rows]).get("mean"),
            "A2_pooled_charged_eligible": stats([a2(row, charge=True) for row in elig]).get("mean"),
            "A2_per_month": per_month,
        }
    report["bounded_arithmetic_estimate"] = {
        "estimator": (
            "A2: the plan's own inversion arithmetic corrected to the geometry the "
            "sealed rows carry (RR 2.0), charging the original deductible rescaled to "
            "inverted risk. Computed straight off the sealed labels, so it needs no walk."
        ),
        "known_bias": (
            "A2 is OPTIMISTIC. On the seven MARKET families this session walked both "
            "estimators over the same 81,968 candidates: A2 minus the real walk is "
            "+0.027 to +0.169 R/trade (see P0_RECONCILIATION.json, A2_true_rr2p0_gross "
            "vs B_real_walk_gross). The bias scales with spread_r, and the LIMIT "
            "families' spread_r sits inside the MARKET families' range."
        ),
        "per_family": per_family,
    }

    path = OUT / "receipts/P0_T4_LIMIT.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(report, indent=1, sort_keys=True, allow_nan=False) + "\n")
    print("WROTE", path)
    for family, value in per_family.items():
        print(
            f"{family:28s} n={value['filled_n']:7d} orig_hit={value['orig_hit_rate']:.4f} "
            f"(driftless 0.3333) A2={value['A2_pooled_charged']:+.4f} "
            f"A2elig={value['A2_pooled_charged_eligible']:+.4f} "
            f"spr_med={value['spread_r_median']:.4f}"
        )


if __name__ == "__main__":
    main()
