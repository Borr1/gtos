"""Session CD -- CD-3's deliverable: the per-arm, per-repair delta table.

Reads the pool summaries `cd_pool.py` wrote for each arm plus each run's own
report, and assembles:

* the arm-level economics (trades, orders, cost decomposition, R/day);
* the frozen-vs-repaired delta per arm;
* the **bridge to the seal** -- the frozen arm's pool aggregate against the
  numbers AW's reader recomputed from the sealed arms of record, which is what
  licenses using the sealed arms as the frozen comparand for the other three;
* the loss-concentration shape at three cost bands, with the counterfactual
  "pool without the cost tail" that CD-3 asks about.

R/day is reported on TRADING days -- days on which the arm produced at least one
scoreable pool row -- not on calendar days, because January's 31 calendar days
include ten on which the engine does nothing and dividing by them would flatter
every number by a third.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[5]

#: What AW's reader recomputed from the SEALED arms of record, and matched to
#: 8 decimal places (`SESSION_AW_SEPARABILITY_MINE_RESULT.md` section 1).
#: This is the comparand for the bridge.
SEALED_ARM_POOLS: dict[str, dict[str, Any]] = {
    "S0R0": {"ledger_rows": 154299, "diagnostic_scoreable": 28519,
             "positive_rows": 8006, "negative_rows": 20513,
             "positive_net_r": 6916.94750286, "negative_net_r": -31400.82177687},
    "S1R0": {"ledger_rows": 154312, "diagnostic_scoreable": 28530,
             "positive_rows": 8012, "negative_rows": 20518,
             "positive_net_r": 6922.59393961, "negative_net_r": -31405.38242771},
    "S0R1": {"ledger_rows": 154302, "diagnostic_scoreable": 28523,
             "positive_rows": 8009, "negative_rows": 20514,
             "positive_net_r": 6919.49514546, "negative_net_r": -31401.06791085},
    "S1R1": {"ledger_rows": 154316, "diagnostic_scoreable": 28535,
             "positive_rows": 8016, "negative_rows": 20519,
             "positive_net_r": 6926.18946999, "negative_net_r": -31405.59305302},
}


def load(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def arm_row(pool: dict[str, Any], report: dict[str, Any] | None) -> dict[str, Any]:
    days = {d: v for d, v in (pool.get("by_day") or {}).items() if v.get("n")}
    trading_days = len(days)
    counts = (report or {}).get("economics_counts") or {}
    comp = pool["cost"]["components_mean_r"]
    band = pool["loss_concentration"]["bands"]["1.0"]
    return {
        "trades": counts.get("trade"),
        "orders": counts.get("order"),
        "missed_ledger_rows": pool["rows"],
        "diagnostic_scoreable_rows": pool["diagnostic_scoreable_rows"],
        "pool_net_r": pool["net_r"],
        "pool_mean_r_per_row": pool["mean_r_per_row"],
        "pool_trading_days": trading_days,
        "pool_r_per_trading_day": (
            round(pool["net_r"] / trading_days, 6) if trading_days else None
        ),
        "days_negative": pool["n_days_negative"],
        "base_rate_positive": pool["base_rate_positive"],
        "breakeven_precision": pool["breakeven_precision"],
        "gross_mean_r": pool["gross"]["mean_gross_r"],
        "binary_hit_rate": pool["gross"]["binary_population"]["hit_rate"],
        "mean_cost_r": pool["cost"]["mean_cost_r"],
        "component_commission_r": comp.get("commission_r"),
        "component_spread_r": comp.get("spread_r"),
        "component_swap_cost_r": comp.get("swap_cost_r"),
        "component_slippage_r": comp.get("expected_slippage_r"),
        "max_cost_r": pool["cost"]["max_cost_r"],
        "cost_tail_1r_rows": band["rows"],
        "cost_tail_1r_row_share": band["row_share"],
        "cost_tail_1r_share_of_pool_net_r": band["share_of_pool_net_r"],
        "pool_mean_r_without_cost_tail": band["mean_r_without_band"],
        "wall_seconds": (report or {}).get("wall_seconds"),
        "maxrss_bytes": ((report or {}).get("rusage") or {}).get("maxrss_bytes"),
    }


def delta(base: dict[str, Any], cand: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in sorted(set(base) | set(cand)):
        b, c = base.get(key), cand.get(key)
        if isinstance(b, (int, float)) and isinstance(c, (int, float)):
            out[key] = round(c - b, 8)
    return out


def bridge(arm: str, frozen: dict[str, Any]) -> dict[str, Any]:
    """Does the train lane reproduce the sealed arm of record?

    A month-scale identity check against the SEAL rather than against a fresh
    frozen run, which is stronger than what CB's H-CB-5 proposed: the sealed arm
    is the artifact of record the estate's negative verdict rests on.

    It is not expected to be exact, and the reason is stated rather than hoped
    away: the sealed arms ran under R1 while this lane binds R2, and the runs
    carry a different output namespace. So the comparison is reported field by
    field with the relative gap, and a reader can see how close is close.
    """

    sealed = SEALED_ARM_POOLS.get(arm)
    if sealed is None:
        return {"available": False}
    got_net = frozen["pool_net_r"]
    want_net = sealed["positive_net_r"] + sealed["negative_net_r"]
    return {
        "available": True,
        "sealed_arm_of_record": sealed,
        "regenerated_frozen": {
            "diagnostic_scoreable": frozen["diagnostic_scoreable_rows"],
            "ledger_rows": frozen["missed_ledger_rows"],
            "net_r": got_net,
        },
        "scoreable_row_delta": frozen["diagnostic_scoreable_rows"]
        - sealed["diagnostic_scoreable"],
        "scoreable_row_relative_gap": round(
            abs(frozen["diagnostic_scoreable_rows"] - sealed["diagnostic_scoreable"])
            / sealed["diagnostic_scoreable"],
            8,
        ),
        "net_r_delta": round(got_net - want_net, 6),
        "net_r_relative_gap": round(abs(got_net - want_net) / abs(want_net), 8),
        "caveat": (
            "The sealed arms ran under decision contract R1; this lane binds R2 "
            "(which moved two never-executing verifiers into verification_tooling). "
            "The output namespace differs too. So an exact match is not the "
            "expectation -- the question is whether the economics move, and by "
            "how much."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pool-dir", default="/tmp/cdbench")
    ap.add_argument("--out", required=True)
    ns = ap.parse_args()

    root = Path(ns.pool_dir)
    arms = ("S0R0", "S1R0", "S0R1", "S1R1")
    table: dict[str, Any] = {}
    for arm in arms:
        repaired_pool = load(root / f"CD_M2_REPAIRED_B7_5_{arm}_POOL.json")
        # The frozen side is the SEALED ARM OF RECORD, read in place through AW's
        # cold resolver -- not a re-run of it. That is the stronger comparand and
        # it is the one CD-3 actually asks for ("frozen January vs repaired
        # January"): the sealed arms ARE frozen January, and they are the
        # artifacts the estate's negative verdict rests on. A regenerated frozen
        # arm is accepted as a fallback if one exists.
        frozen_pool = load(root / f"CD_SEALED_{arm}_POOL.json") or load(
            root / f"CD_M3_FROZEN_B7_5_{arm}_POOL.json"
        )
        repaired_report = load(root / f"CD_M2_{arm}.json")
        frozen_report = load(root / f"CD_M3_{arm}.json")
        entry: dict[str, Any] = {}
        if frozen_pool:
            entry["frozen_source"] = frozen_pool.get("source", "regenerated_ledger")
            entry["frozen"] = arm_row(frozen_pool, frozen_report)
            entry["seal_bridge"] = bridge(arm, entry["frozen"])
        if repaired_pool:
            entry["repaired"] = arm_row(repaired_pool, repaired_report)
        if "frozen" in entry and "repaired" in entry:
            entry["delta_repaired_minus_frozen"] = delta(
                entry["frozen"], entry["repaired"]
            )
        if entry:
            table[arm] = entry

    payload = {
        "schema": "gtos.session_cd.delta_table.v1",
        "window": "2026-01-01..2026-01-31",
        "surface": "VAL",
        "disclosure": (
            "VAL is the survivor book's own selection surface "
            "(d.year >= 2025, build_survivor_book.py:74 / "
            "KB7_growth_kelly_sizing.py:130). Ranking and gradient checks only; "
            "no headline expectancy is quoted from VAL alone."
        ),
        "repairs_applied_to_the_repaired_arms": [
            "commission_broker_true_gated",
            "swap_horizon_true",
        ],
        "speed_cuts": [
            "authority_hash_content_memo",
            "abc_concrete_types",
            "gc_during_chunk",
            "skip_post_hoc_ledger_recertification",
            "ledger_scalar_projection",
            "missed_pool_projection",
        ],
        "note_on_r_per_day": (
            "R per TRADING day (a day with at least one scoreable pool row), not "
            "per calendar day. January's 31 calendar days include ten the engine "
            "does nothing on."
        ),
        "arms": table,
    }
    Path(ns.out).write_text(json.dumps(payload, indent=1, default=str))

    print(f"{'arm':6s} {'frozen R/row':>13s} {'repaired':>12s} {'delta':>10s} "
          f"{'gross froz':>11s} {'gross rep':>10s} {'trades f/r':>12s}")
    for arm, entry in table.items():
        f, r = entry.get("frozen"), entry.get("repaired")
        if not (f and r):
            continue
        print(
            f"{arm:6s} {f['pool_mean_r_per_row']:+13.6f} "
            f"{r['pool_mean_r_per_row']:+12.6f} "
            f"{r['pool_mean_r_per_row'] - f['pool_mean_r_per_row']:+10.6f} "
            f"{f['gross_mean_r']:+11.6f} {r['gross_mean_r']:+10.6f} "
            f"{str(f['trades']) + '/' + str(r['trades']):>12s}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
