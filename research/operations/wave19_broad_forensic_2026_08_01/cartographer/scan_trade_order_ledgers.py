#!/usr/bin/env python3
"""Cartographer receipt tool: stream TRADE/ORDER ledgers of a lane arm and
collect close_reason / status / economics field distributions. Streams
line-by-line. Wave 19 forensic, Session FA."""
import json
import sys
from collections import Counter

TRADE_FIELDS = [
    "close_reason",
    "status",
    "order_type",
    "final_r",
    "gross_r",
    "net_r",
    "cost_r",
    "exact_r",
    "commission_r",
    "spread_r",
    "swap_cost_r",
    "expected_slippage_r",
    "risk_pct",
    "risk_cash",
    "policy_name",
    "selected_policy",
    "terminal_outcome",
    "close_mark_source",
    "dynamic_geometry_policy",
    "exit_reason",
    "policy_exit_reason",
    "selected_policy_exit_reason",
    "b7_5_selection_sizing_factorial_arm_id",
    "profit_harvest_applied",
]


def main(path: str, kind: str) -> None:
    counters = {f: Counter() for f in TRADE_FIELDS}
    keys_seen = Counter()
    n = 0
    close_reason_like = Counter()
    with open(path, "rt") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            n += 1
            for k in row:
                keys_seen[k] += 1
                if "close_reason" in k or "exit_reason" in k:
                    v = row.get(k)
                    if isinstance(v, (str, int, float, bool, type(None))):
                        close_reason_like[f"{k}={v}"] += 1
            for f in TRADE_FIELDS:
                v = row.get(f)
                if isinstance(v, float):
                    v = round(v, 4)
                if isinstance(v, (dict, list)):
                    v = f"<{type(v).__name__}>"
                counters[f][json.dumps(v)] += 1
    print(f"# {kind}: {n} rows, {len(keys_seen)} distinct keys")
    for f in TRADE_FIELDS:
        c = counters[f]
        if not c or (len(c) == 1 and "null" in c):
            continue
        print(f"== {f}: {dict(c.most_common(12))}")
    print("== close/exit-reason-like fields (top 40):")
    for k, v in close_reason_like.most_common(40):
        print(f"   {v:4d}  {k[:160]}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
