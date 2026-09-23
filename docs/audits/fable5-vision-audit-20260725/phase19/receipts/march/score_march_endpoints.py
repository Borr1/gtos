"""Score MARCH_PREREG_V1's five P endpoints and two S bands. Thresholds are frozen.

Every threshold below is transcribed from the prereg's §4 table and is a literal
here on purpose: a scorer that recomputed a threshold from the data it is scoring
is not a test. Nothing in this file decides anything -- it applies rules that were
written before any March byte existed.

The one judgement call, made explicit: a P endpoint whose inputs are missing (an
arm that errored) is `NOT_EVALUABLE`, never `FAIL`. A failure means the January
mechanism did not reproduce out-of-window, which is a finding; a missing arm means
we did not measure, which is not.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

# -- frozen thresholds (MARCH_PREREG_V1 §4) --------------------------------------
P1_MULTIPLE = 1.5  # trades(I) >= 1.5 x trades(R0)
P2_MULTIPLE = 0.25  # trades(II) <= 0.25 x trades(R0)
P3_FLOOR = 3  # trades(III) <= max(3, 0.10 x trades(R0))
P3_MULTIPLE = 0.10
P4_PER_TRADE_TOL = 1e-9  # trade set (IV) == (R0), per-trade net_r within tol
P5_REFUSAL_RATE = 0.99  # breaker cost-refusal in (V) >= 99 %
S1_BAND = (4.0, 16.0)  # frozen/truthed spread ratio
S2_BAND = (2.0, 8.0)  # transformed/untransformed median breaker cost_r

JAN = {  # January values, for the "what changed vs January" column only
    "P1": 2.42,
    "P2": 0.105,
    "P3": 1,
    "P4": "exact",
    "P5": (0, 1.0),
    "S1": 8.48,
    "S2": 3.67,
}


def _verdict(passed: bool | None) -> str:
    if passed is None:
        return "NOT_EVALUABLE"
    return "PASS" if passed else "FAIL (January mechanism REFUTED out-of-window)"


def _count_power_note(r0: int | None, arm: int | None, *, direction: str) -> str:
    """Say when a frozen count threshold is arithmetically weak on THIS month.

    This changes no threshold and no verdict -- the prereg's rules are applied
    exactly as written. It only stops a degenerate pass from being read as a
    confirmation. If March's R0 book is much thinner than January's 57 trades,
    "trades(I) >= 1.5 x trades(R0)" can be satisfied by two or three trades, and
    a reader deserves to be told that before quoting it as a mechanism confirm.
    """

    if r0 is None or arm is None:
        return "inputs missing"
    if r0 == 0:
        return (
            "DEGENERATE: R0 admitted zero trades, so every count bar is 0 and the "
            "widening/stand-down endpoints carry no information this month"
        )
    if r0 < 10:
        return (
            f"WEAK: R0 admitted only {r0} trades (January had 57), so this bar is "
            f"crossed by a handful of admissions; the direction is readable, the "
            f"magnitude is not"
        )
    if direction == "up" and arm - r0 < 5:
        return "NARROW: the margin over the bar is under 5 trades"
    return "adequate: R0 book is thick enough for the count bar to discriminate"


def score(
    *, analyses: dict[str, dict[str, Any]], pool_census: dict[str, Any] | None
) -> dict[str, Any]:
    def trades(key: str) -> int | None:
        row = analyses.get(key)
        return None if row is None else int(row["book"]["arm_trades"])

    r0 = trades("R0")
    ti, tii, tiii = trades("I"), trades("II"), trades("III")

    # -- P1 -----------------------------------------------------------------
    p1_bar = None if r0 is None else P1_MULTIPLE * r0
    p1 = None if (ti is None or r0 is None) else bool(ti >= p1_bar)

    # -- P2 -----------------------------------------------------------------
    p2_bar = None if r0 is None else P2_MULTIPLE * r0
    p2 = None if (tii is None or r0 is None) else bool(tii <= p2_bar)

    # -- P3 -----------------------------------------------------------------
    p3_bar = None if r0 is None else max(P3_FLOOR, P3_MULTIPLE * r0)
    p3 = None if (tiii is None or r0 is None) else bool(tiii <= p3_bar)

    # -- P4: the identity endpoint ------------------------------------------
    iv = analyses.get("IV")
    if iv is None:
        p4 = None
        p4_detail: dict[str, Any] = {"reason": "arm_IV_missing"}
    else:
        same_set = (
            len(iv["admitted_set_diff"]["only_arm_keys"]) == 0
            and len(iv["admitted_set_diff"]["only_r0_keys"]) == 0
        )
        moved = int(iv["shared_trades"]["moved_economics"])
        book_delta = abs(float(iv["book"]["delta_total_net_r"]))
        p4 = bool(same_set and moved == 0 and book_delta <= P4_PER_TRADE_TOL)
        p4_detail = {
            "trade_sets_identical": same_set,
            "only_arm_n": len(iv["admitted_set_diff"]["only_arm_keys"]),
            "only_r0_n": len(iv["admitted_set_diff"]["only_r0_keys"]),
            "shared_trades_moved_economics": moved,
            "book_delta_abs": book_delta,
            "per_trade_tolerance": P4_PER_TRADE_TOL,
        }

    # -- P5: two clauses, both required -------------------------------------
    v = analyses.get("V")
    refusal = (
        None
        if pool_census is None
        else pool_census.get("P5_breaker_cost_refusal_rate_transformed")
    )
    transformed_n = None if v is None else int(v["transformed_trades"]["n"])
    if transformed_n is None or refusal is None:
        p5 = None
    else:
        p5 = bool(transformed_n == 0 and refusal >= P5_REFUSAL_RATE)
    p5_detail = {
        "transformed_admissions": transformed_n,
        "transformed_admissions_clause_pass": (
            None if transformed_n is None else bool(transformed_n == 0)
        ),
        "breaker_cost_refusal_rate": refusal,
        "refusal_clause_pass": (
            None if refusal is None else bool(refusal >= P5_REFUSAL_RATE)
        ),
        "tp_provenance_status": (
            None if v is None else v["transformed_trades"]["tp_provenance_status"]
        ),
        "tp_provenance": (None if v is None else v["transformed_trades"]["tp_provenance"]),
    }

    # -- S1: the spread census, from arm (i)'s own repair census -------------
    s1_ratio = None
    s1_detail: dict[str, Any] = {}
    arm_i = analyses.get("I") or {}
    census = ((arm_i.get("receipt") or {}).get("repair_report") or {}).get(
        "spread_input_truth"
    )
    if census:
        frozen = census.get("baseline_r_sum")
        truthed = census.get("charged_r_sum")
        if frozen and truthed:
            s1_ratio = round(float(frozen) / float(truthed), 4)
        s1_detail = {
            "frozen_spread_r_sum": frozen,
            "truthed_spread_r_sum": truthed,
            "packets_called": census.get("calls"),
            "packets_applied": census.get("applied"),
        }
    s1 = None if s1_ratio is None else bool(S1_BAND[0] <= s1_ratio <= S1_BAND[1])

    s2_ratio = (
        None
        if pool_census is None
        else pool_census.get("S2_transformed_over_untransformed_median_cost_r")
    )
    s2 = None if s2_ratio is None else bool(S2_BAND[0] <= s2_ratio <= S2_BAND[1])

    return {
        "schema": "gtos.march.endpoint_scores.v1",
        "protocol": "MARCH_PREREG_V1 §4 (thresholds frozen before any March byte)",
        "r0_trades_march": r0,
        "primary_endpoints": {
            "P1": {
                "claim": "cost truth widens the funnel",
                "rule": f"trades(I) >= {P1_MULTIPLE} x trades(R0)",
                "measured": {"trades_I": ti, "trades_R0": r0, "bar": p1_bar,
                             "ratio": (None if not r0 or ti is None else round(ti / r0, 4))},
                "january": JAN["P1"],
                "power_note": _count_power_note(r0, ti, direction="up"),
                "verdict": _verdict(p1),
            },
            "P2": {
                "claim": "belief honesty stands down",
                "rule": f"trades(II) <= {P2_MULTIPLE} x trades(R0)",
                "measured": {"trades_II": tii, "trades_R0": r0, "bar": p2_bar,
                             "ratio": (None if not r0 or tii is None else round(tii / r0, 4))},
                "january": JAN["P2"],
                "power_note": _count_power_note(r0, tii, direction="down"),
                "verdict": _verdict(p2),
            },
            "P3": {
                "claim": "ceiling composes to near-silence",
                "rule": f"trades(III) <= max({P3_FLOOR}, {P3_MULTIPLE} x trades(R0))",
                "measured": {"trades_III": tiii, "trades_R0": r0, "bar": p3_bar},
                "january": JAN["P3"],
                "power_note": _count_power_note(r0, tiii, direction="down"),
                "verdict": _verdict(p3),
            },
            "P4": {
                "claim": "machinery is inert",
                "rule": f"trade set (IV) == (R0) exactly, per-trade net_r <= {P4_PER_TRADE_TOL}",
                "measured": p4_detail,
                "january": JAN["P4"],
                "verdict": _verdict(p4),
            },
            "P5": {
                "claim": "the edge is inexpressible",
                "rule": (
                    f"transformed admissions in (V) == 0 AND breaker cost-refusal "
                    f">= {P5_REFUSAL_RATE:.0%}"
                ),
                "measured": p5_detail,
                "january": {"transformed_admissions": 0, "refusal_rate": 1.0},
                "verdict": _verdict(p5),
            },
        },
        "census_confirms": {
            "S1": {
                "claim": "frozen/truthed spread ratio",
                "band": list(S1_BAND),
                "measured_ratio": s1_ratio,
                "detail": s1_detail,
                "january": JAN["S1"],
                "verdict": _verdict(s1),
            },
            "S2": {
                "claim": "transformed/untransformed median breaker cost_r",
                "band": list(S2_BAND),
                "measured_ratio": s2_ratio,
                "january": JAN["S2"],
                "verdict": _verdict(s2),
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis-dir", type=Path, required=True)
    parser.add_argument("--pool-census", type=Path)
    parser.add_argument("--out", type=Path)
    ns = parser.parse_args()
    analyses = {}
    for key in ("R0", "I", "II", "III", "IV", "V"):
        path = ns.analysis_dir / f"MARCH_ARM_{key}_ANALYSIS.json"
        if path.is_file():
            analyses[key] = json.loads(path.read_text(encoding="utf-8"))
    pool = (
        json.loads(ns.pool_census.read_text(encoding="utf-8"))
        if ns.pool_census and ns.pool_census.is_file()
        else None
    )
    payload = score(analyses=analyses, pool_census=pool)
    payload["arms_present"] = sorted(analyses)
    payload["arms_missing"] = sorted(
        {"R0", "I", "II", "III", "IV", "V"} - set(analyses)
    )
    text = json.dumps(payload, indent=1, sort_keys=True, default=str) + "\n"
    if ns.out:
        ns.out.parent.mkdir(parents=True, exist_ok=True)
        ns.out.write_text(text, encoding="utf-8")
        print(f"written: {ns.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
