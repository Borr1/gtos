#!/usr/bin/env python3
"""l12 step 1: what kills a candidate AFTER it has already passed the cost gate?

The pool's headline blocker census is 73.9% cost_authority. That answer is exhausted.
The unasked question: of the 7,210 candidates the cost gate PASSED, only 21 ever reach
selector 'trade'. Which layer eats the other 7,189, and what was each cohort worth?
"""
import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w0_ws  # noqa: E402


def stat(rows, key="gross_r"):
    v = [r.get(key) for r in rows if r.get(key) is not None]
    if not v:
        return {"n": 0}
    v_sorted = sorted(v)
    n = len(v)
    return {
        "n": n,
        "mean": round(sum(v) / n, 6),
        "median": round(v_sorted[n // 2], 6),
        "win_rate": round(sum(1 for x in v if x > 0) / n, 6),
        "sum": round(sum(v), 3),
    }


def main():
    rows = w0_ws.load()
    N = len(rows)

    # cost gate limbs, from broker_net_cost_engine.py:859-866 (spread) and :923-927 (total)
    def cost_pass(r):
        sr = r.get("spread_r")
        tr = r.get("cost_r")
        if sr is None or tr is None:
            return False
        return sr <= 0.10 and tr <= 0.15

    passed = [r for r in rows if cost_pass(r)]
    blocked = [r for r in rows if not cost_pass(r)]

    out = {
        "pool_n": N,
        "cost_gate_pass_n": len(passed),
        "cost_gate_block_n": len(blocked),
        "cost_pass_gross": stat(passed),
        "cost_block_gross": stat(blocked),
    }

    # --- Where do the cost-passing candidates die? ---
    fields = [
        "final_blocker_class",
        "selector_action",
        "scheduler_materialization_status",
        "scheduler_materialization_skip_reason",
        "same_symbol_lifecycle_action",
        "effective_order_type",
        "admission_action",
        "selector_primary_reason",
    ]
    for f in fields:
        c = Counter(str(r.get(f)) for r in passed)
        out["passed_by_" + f] = {k: v for k, v in c.most_common(25)}

    # gross by selector_action within the cost-passing cohort
    by_sel = defaultdict(list)
    for r in passed:
        by_sel[str(r.get("selector_action"))].append(r)
    out["passed_gross_by_selector_action"] = {
        k: stat(v) for k, v in sorted(by_sel.items(), key=lambda kv: -len(kv[1]))
    }

    by_blk = defaultdict(list)
    for r in passed:
        by_blk[str(r.get("final_blocker_class"))].append(r)
    out["passed_gross_by_blocker"] = {
        k: stat(v) for k, v in sorted(by_blk.items(), key=lambda kv: -len(kv[1]))
    }

    # primary reason with gross, restricted to cost-passing
    by_reason = defaultdict(list)
    for r in passed:
        by_reason[str(r.get("selector_primary_reason"))].append(r)
    out["passed_gross_by_selector_primary_reason"] = {
        k: stat(v) for k, v in
        sorted(by_reason.items(), key=lambda kv: -len(kv[1]))[:25]
    }

    # scheduler skip reason with gross
    by_skip = defaultdict(list)
    for r in passed:
        by_skip[str(r.get("scheduler_materialization_skip_reason"))].append(r)
    out["passed_gross_by_scheduler_skip_reason"] = {
        k: stat(v) for k, v in
        sorted(by_skip.items(), key=lambda kv: -len(kv[1]))[:25]
    }

    dest = os.path.join(HERE, "L12_POSTCOST_FUNNEL_V1.json")
    with open(dest, "w") as fh:
        json.dump(out, fh, indent=1)

    print("pool", N, "cost_pass", len(passed), "cost_block", len(blocked))
    print("cost_pass gross", out["cost_pass_gross"])
    print("cost_block gross", out["cost_block_gross"])
    print("--- passed by selector_action (n, mean gross, win) ---")
    for k, v in list(out["passed_gross_by_selector_action"].items())[:10]:
        print("  %-34s %6d %9.4f %7.4f" % (k, v["n"], v["mean"], v["win_rate"]))
    print("--- passed by final_blocker_class ---")
    for k, v in list(out["passed_gross_by_blocker"].items())[:12]:
        print("  %-34s %6d %9.4f %7.4f" % (k, v["n"], v["mean"], v["win_rate"]))
    print("WROTE", dest)


if __name__ == "__main__":
    main()
