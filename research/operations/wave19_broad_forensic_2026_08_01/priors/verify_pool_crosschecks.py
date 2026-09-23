#!/usr/bin/env python3
"""PRIORS-DIGEST cross-check: stream the January and February compact scoreable pools
line-by-line and re-derive the aggregates the committed receipts publish.

Writes POOL_CROSSCHECK_V1.json beside itself. Never loads a whole ledger into memory.

Session FA wave-19 broad forensic, 2026-08-01. Read-only over committed receipts;
no March data, no live-forward data, no VPS, no replay.
"""
import gzip
import json
import os
from collections import Counter, defaultdict

WT = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
R16 = f"{WT}/docs/audits/fable5-vision-audit-20260725/phase16/receipts"
R18 = f"{WT}/docs/audits/fable5-vision-audit-20260725/phase18/receipts"
OUT = os.path.dirname(os.path.abspath(__file__))

JAN_POOL = f"{R16}/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"
FEB_POOL = f"{R18}/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz"
JAN_RECEIPT = f"{R16}/CJ_RECLOCKED_POOL_S0R0_V1.json"
FEB_RECEIPT = f"{R18}/CP_FEBRUARY_POOL_S0R0_V1.json"
JAN_LANE = f"{R16}/CJ_RECLOCKED_S0R0_V7_LANE/LANE_TRADE_TABLE.jsonl"
FEB_LANE = f"{R18}/CP_FEBRUARY_TRUE_UTC_S0R0_V1_LANE/LANE_TRADE_TABLE.jsonl"
SIDECAR = f"{R18}/pools/CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz"


def stream_pool(path):
    """One pass; returns aggregate dict. Uses the scoreable-net proxy column
    `opportunity_net_proxy_r` and cost columns as recorded in the pool rows."""
    n = 0
    net_sum = 0.0
    gross_sum = 0.0
    cost_sum = 0.0
    spread_sum = 0.0
    comm_sum = 0.0
    slip_sum = 0.0
    swap_sum = 0.0
    pos = 0
    day_net = defaultdict(float)
    exec_flag = Counter()
    n_target = 0
    n_stop = 0
    keys0 = None
    key_drift = set()
    for line in gzip.open(path, "rt"):
        r = json.loads(line)
        if keys0 is None:
            keys0 = sorted(r.keys())
        elif sorted(r.keys()) != keys0:
            key_drift.add(tuple(sorted(r.keys())))
        n += 1
        net = float(r["opportunity_net_proxy_r"])
        cost = float(r["cost_r"])
        net_sum += net
        cost_sum += cost
        gross_sum += net + cost
        spread_sum += float(r.get("spread_r") or 0.0)
        comm_sum += float(r.get("commission_r") or 0.0)
        slip_sum += float(r.get("expected_slippage_r") or 0.0)
        swap_sum += float(r.get("swap_cost_r") or 0.0)
        if net > 0:
            pos += 1
        d = str(r.get("decision_time_utc", ""))[:10]
        day_net[d] += net
        exec_flag[bool(r.get("broker_pretrade_cost_executable"))] += 1
        sbs = r.get("source_bound_signal_r")
        if sbs is not None:
            v = float(sbs)
            tgt = r.get("raw_target_r")
            if tgt is not None and abs(v - float(tgt)) < 1e-9:
                n_target += 1
            elif abs(v + 1.0) < 1e-9:
                n_stop += 1
    days_with_rows = {d: v for d, v in day_net.items() if d}
    neg_days = sum(1 for v in days_with_rows.values() if v < 0)
    return {
        "rows": n,
        "net_sum": net_sum,
        "net_mean": net_sum / n if n else None,
        "gross_mean": gross_sum / n if n else None,
        "cost_mean": cost_sum / n if n else None,
        "spread_mean": spread_sum / n if n else None,
        "commission_mean": comm_sum / n if n else None,
        "slippage_mean": slip_sum / n if n else None,
        "swap_mean": swap_sum / n if n else None,
        "positive_rows": pos,
        "positive_share": pos / n if n else None,
        "scoreable_days": len(days_with_rows),
        "negative_days": neg_days,
        "broker_pretrade_cost_executable": {str(k): v for k, v in exec_flag.items()},
        "binary_endpoint_counts_target_stop_heuristic": [n_target, n_stop],
        "row_key_count": len(keys0 or []),
        "row_key_drift_variants": len(key_drift),
    }


def lane_trades(path):
    """Line 1 = meta, then trades."""
    n = 0
    net = 0.0
    meta = None
    with open(path) as f:
        for i, line in enumerate(f):
            r = json.loads(line)
            if i == 0:
                meta = {k: r.get(k) for k in list(r)[:12]}
                if "schema" in r or "trade" not in json.dumps(r)[:200].lower():
                    continue
            n += 1
            for k in ("realized_net_r", "net_r", "realized_r", "physical_net_r"):
                if k in r and r[k] is not None:
                    net += float(r[k])
                    break
    return {"rows_after_meta": n, "summed_net_r_best_effort": net, "meta_head_keys": list(meta or {})}


def sidecar_scan(path):
    n = 0
    obs = 0
    join_keys = 0
    keys0 = None
    for line in gzip.open(path, "rt"):
        r = json.loads(line)
        if keys0 is None:
            keys0 = sorted(r.keys())
        n += 1
        o = r.get("observations")
        if isinstance(o, list):
            obs += len(o)
        elif isinstance(r.get("n_observations"), int):
            obs += r["n_observations"]
        if r.get("candidate_id") or r.get("join_key"):
            join_keys += 1
    return {"rows": n, "total_observations": obs, "rows_with_join_key": join_keys, "row_keys": keys0}


def main():
    out = {"schema": "gtos.session_fa.priors_pool_crosscheck.v1"}
    out["january"] = stream_pool(JAN_POOL)
    out["february"] = stream_pool(FEB_POOL)
    out["january_receipt"] = json.load(open(JAN_RECEIPT))
    out["february_receipt"] = json.load(open(FEB_RECEIPT))
    out["january_lane"] = lane_trades(JAN_LANE)
    out["february_lane"] = lane_trades(FEB_LANE)
    out["cq_sidecar"] = sidecar_scan(SIDECAR)
    with open(os.path.join(OUT, "POOL_CROSSCHECK_V1.json"), "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    for w in ("january", "february"):
        a = out[w]
        print(w, {k: a[k] for k in ("rows", "net_sum", "net_mean", "gross_mean", "cost_mean",
                                    "positive_rows", "scoreable_days", "negative_days")})
    print("jan exec flag:", out["january"]["broker_pretrade_cost_executable"])
    print("jan endpoints:", out["january"]["binary_endpoint_counts_target_stop_heuristic"])
    print("lane jan:", out["january_lane"])
    print("lane feb:", out["february_lane"])
    print("sidecar:", {k: out["cq_sidecar"][k] for k in ("rows", "total_observations")})


if __name__ == "__main__":
    main()
