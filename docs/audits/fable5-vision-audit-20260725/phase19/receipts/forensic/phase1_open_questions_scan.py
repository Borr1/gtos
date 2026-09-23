#!/usr/bin/env python3
"""B4 Phase-1 open questions: measured incidence on the FA2 2-day fence lane arm.

Reads the FA2_FENCE_S0R0_2D MISSED_OPPORTUNITY + TRADE ledgers (January 2-day
engineering_stop_after_day lane arm, sealed CJ-baseline-identical per the A0 fence)
and emits PHASE1_OPEN_QUESTIONS.json with the distributions the three questions need:

  Q1  candidate_probability distribution + clamp-bound mass + EV floor
  Q2  fill_probability distribution + the 0.92 marketable-limit template incidence
  Q3  close-reason vocabulary vs exact-endpoint (binary_population) membership

No March-2026 data, no live-forward data: the fence arm is January 2026 days 1-2.
"""
from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

BASE = Path(
    "/Users/borr/GTOSActive/worktrees/fa2-integration-20260803/research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/"
    "attempt_5_typed_sparse/FA2_FENCE_S0R0_2D"
)
OUT = Path(__file__).with_name("PHASE1_OPEN_QUESTIONS.json")

TOL = 1e-9


def _f(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def quantiles(values, points=(0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99)):
    if not values:
        return {}
    ordered = sorted(values)
    n = len(ordered)
    out = {}
    for p in points:
        idx = min(n - 1, max(0, int(round(p * (n - 1)))))
        out[f"q{p:g}"] = ordered[idx]
    return out


def dist(values):
    if not values:
        return {"n": 0}
    return {
        "n": len(values),
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / len(values),
        **quantiles(values),
    }


def near(value, anchor, tol=TOL):
    return value is not None and abs(value - anchor) <= tol


def main() -> None:
    missed_path = BASE / "FA2_FENCE_S0R0_2D_MISSED_OPPORTUNITY_LEDGER.jsonl"
    trade_path = BASE / "FA2_FENCE_S0R0_2D_TRADE_LEDGER.jsonl"

    # ---------------- MISSED ----------------
    n_rows = 0
    probs, fills, evs, nets, costs = [], [], [], [], []
    prob_counter: Counter[float] = Counter()
    fill_counter: Counter[float] = Counter()
    prob_null = fill_null = 0
    ev_dup_expectancy = 0
    net_identity_ok = 0
    net_identity_n = 0
    fill_key_presence: Counter[str] = Counter()
    limit_marketable: Counter[str] = Counter()
    exec_fill_counter: Counter[float] = Counter()
    exec_fill_n = 0
    terminal_counter: Counter[str] = Counter()
    close_reason_counter: Counter[str] = Counter()
    terminal_eq_close = 0
    # Q3 partitions on scoreable rows (opportunity_gross_r present)
    scoreable = 0
    by_reason: dict[str, Counter] = {}
    recon_stop = recon_target_fixed = recon_target_own = 0
    native_stop = native_target_fixed = native_target_own = 0
    recon_by_reason: dict[str, Counter] = {}
    ev_floor_breach = 0  # candidate_ev_r <= 0
    net_le_zero = 0
    prob_below_058 = prob_above_097 = 0

    with missed_path.open() as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            n_rows += 1

            p = _f(row.get("candidate_probability"))
            if p is None:
                prob_null += 1
            else:
                probs.append(p)
                prob_counter[round(p, 9)] += 1
                if p < 0.58 - TOL:
                    prob_below_058 += 1
                if p > 0.97 + TOL:
                    prob_above_097 += 1

            fp = _f(row.get("fill_probability"))
            if fp is None:
                fill_null += 1
            else:
                fills.append(fp)
                fill_counter[round(fp, 9)] += 1

            for key in row:
                if "fill_probability" in key:
                    fill_key_presence[key] += 1
            lm = row.get("limit_marketable_at_decision")
            limit_marketable[str(lm)] += 1
            for key in (
                "execution_fill_probability",
                "predecision_limit_fillability_probability",
                "limit_fillability_probability",
            ):
                v = _f(row.get(key))
                if v is not None:
                    exec_fill_n += 1
                    exec_fill_counter[round(v, 9)] += 1
                    break

            ev = _f(row.get("candidate_ev_r"))
            expectancy = _f(row.get("expectancy_r"))
            net = _f(row.get("expected_net_r"))
            cost = _f(row.get("cost_r"))
            if ev is not None:
                evs.append(ev)
                if ev <= 0:
                    ev_floor_breach += 1
            if ev is not None and expectancy is not None and ev == expectancy:
                ev_dup_expectancy += 1
            if net is not None:
                nets.append(net)
                if net <= 0:
                    net_le_zero += 1
            if cost is not None:
                costs.append(cost)
            if ev is not None and net is not None and cost is not None:
                net_identity_n += 1
                if near(net, ev - cost, 1e-6):
                    net_identity_ok += 1

            terminal = str(row.get("terminal_outcome"))
            close_reason = str(row.get("opportunity_close_reason"))
            terminal_counter[terminal] += 1
            close_reason_counter[close_reason] += 1
            if terminal == close_reason:
                terminal_eq_close += 1

            gross = _f(row.get("opportunity_gross_r"))
            net_proxy = _f(row.get("opportunity_net_proxy_r"))
            target = _f(row.get("policy_target_r"))
            if gross is not None:
                scoreable += 1
                bucket = by_reason.setdefault(close_reason, Counter())
                bucket["n"] += 1
                if near(gross, -1.0):
                    bucket["native_stop_endpoint"] += 1
                    native_stop += 1
                if near(gross, 2.0):
                    bucket["native_target_2p0_endpoint"] += 1
                    native_target_fixed += 1
                if target is not None and near(gross, target):
                    bucket["native_own_target_endpoint"] += 1
                    native_target_own += 1
            if net_proxy is not None and cost is not None:
                recon = net_proxy + cost
                rbucket = recon_by_reason.setdefault(close_reason, Counter())
                rbucket["n"] += 1
                if near(recon, -1.0):
                    rbucket["recon_stop_endpoint"] += 1
                    recon_stop += 1
                if near(recon, 2.0):
                    rbucket["recon_target_2p0_endpoint"] += 1
                    recon_target_fixed += 1
                if target is not None and near(recon, target):
                    rbucket["recon_own_target_endpoint"] += 1
                    recon_target_own += 1

    # ---------------- TRADE ----------------
    trades = []
    with trade_path.open() as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("ledger_meta") or row.get("meta"):  # 1 meta line + N trades
                if not row.get("candidate_id") and not row.get("symbol"):
                    trades.append({"meta_line": True, "keys": len(row)})
                    continue
            picked = {}
            for key in sorted(row):
                if (
                    "fill_probability" in key
                    or key
                    in {
                        "candidate_probability",
                        "probability",
                        "candidate_ev_r",
                        "expected_net_r",
                        "cost_r",
                        "terminal_outcome",
                        "opportunity_close_reason",
                        "close_reason",
                        "exit_reason",
                        "net_r",
                        "gross_r",
                        "symbol",
                        "side",
                        "limit_marketable_at_decision",
                    }
                ):
                    picked[key] = row.get(key)
            trades.append(picked)

    result = {
        "schema": "gtos.fa2.phase1_open_questions.v1",
        "substrate": {
            "arm": "FA2_FENCE_S0R0_2D (January 2026, engineering_stop_after_day=2, lane path)",
            "missed_rows": n_rows,
            "trade_ledger_lines": len(trades),
            "evidence_class": "DIAGNOSTIC (billed:false, 2-day fence arm, development window)",
        },
        "q1_candidate_probability": {
            "n": len(probs),
            "n_null": prob_null,
            "distribution": dist(probs),
            "mass_at_exact_values_top10": prob_counter.most_common(10),
            "count_exactly_0.55_fallback": prob_counter.get(0.55, 0),
            "count_below_0.58": prob_below_058,
            "count_above_0.97": prob_above_097,
            "count_at_observed_min": prob_counter.get(round(min(probs), 9), 0) if probs else 0,
            "count_at_observed_max": prob_counter.get(round(max(probs), 9), 0) if probs else 0,
            "candidate_ev_r": dist(evs),
            "count_ev_le_zero": ev_floor_breach,
            "count_expectancy_r_equals_candidate_ev_r": ev_dup_expectancy,
            "expected_net_r": dist(nets),
            "count_expected_net_r_le_zero": net_le_zero,
            "net_identity_expected_net_eq_ev_minus_cost": {
                "n_checked": net_identity_n,
                "n_match_1e-6": net_identity_ok,
            },
            "cost_r": dist(costs),
        },
        "q2_fill_probability": {
            "n": len(fills),
            "n_null": fill_null,
            "distribution": dist(fills),
            "mass_at_exact_values_top10": fill_counter.most_common(10),
            "count_exactly_0.92": fill_counter.get(0.92, 0),
            "count_exactly_0.95_ceiling": fill_counter.get(0.95, 0),
            "count_exactly_0.05_floor": fill_counter.get(0.05, 0),
            "fill_probability_key_presence": dict(fill_key_presence),
            "limit_marketable_at_decision_counts": dict(limit_marketable),
            "execution_or_limit_fillability": {
                "n_present": exec_fill_n,
                "mass_at_exact_values_top10": exec_fill_counter.most_common(10),
                "count_exactly_0.92": exec_fill_counter.get(0.92, 0),
            },
        },
        "q3_population_vs_close_reason": {
            "terminal_outcome_counts": dict(terminal_counter.most_common()),
            "opportunity_close_reason_counts": dict(close_reason_counter.most_common()),
            "terminal_outcome_equals_close_reason_rows": terminal_eq_close,
            "scoreable_rows_native_gross_present": scoreable,
            "native_endpoint_membership": {
                "stop_-1.0": native_stop,
                "target_+2.0_fixed": native_target_fixed,
                "target_own_policy_target_r": native_target_own,
            },
            "reconstructed_net_plus_cost_endpoint_membership": {
                "stop_-1.0": recon_stop,
                "target_+2.0_fixed": recon_target_fixed,
                "target_own_policy_target_r": recon_target_own,
            },
            "per_close_reason_native": {k: dict(v) for k, v in sorted(by_reason.items())},
            "per_close_reason_reconstructed": {
                k: dict(v) for k, v in sorted(recon_by_reason.items())
            },
        },
        "trade_rows": trades,
    }
    OUT.write_text(json.dumps(result, indent=2, default=str) + "\n")
    print(json.dumps(result["substrate"], indent=2))
    print("q1 dist:", json.dumps(result["q1_candidate_probability"]["distribution"]))
    print("q1 top10:", result["q1_candidate_probability"]["mass_at_exact_values_top10"])
    print("q2 dist:", json.dumps(result["q2_fill_probability"]["distribution"]))
    print("q2 top10:", result["q2_fill_probability"]["mass_at_exact_values_top10"])
    print("q2 0.92:", result["q2_fill_probability"]["count_exactly_0.92"])
    print("q3 close reasons:", json.dumps(result["q3_population_vs_close_reason"]["opportunity_close_reason_counts"]))


if __name__ == "__main__":
    main()
