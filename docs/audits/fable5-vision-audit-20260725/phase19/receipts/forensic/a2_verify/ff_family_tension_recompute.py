#!/usr/bin/env python3
"""Recompute FAMILY_TENSION point estimates from raw pool + trade ledgers.

Pool comparator: scoreable non-selected rows of the family (the compact pools
contain only missed rows -- verified 100% carry miss_reason -- so the whole
family slice is the comparator), measured on opportunity_net_proxy_r.
Executed: TRADE_LEDGER net_r.
Paired: executed net_r minus mean(peer opportunity_net_proxy_r) over pool rows
of the same origin_family with identical decision_time_utc.
Wilson 95% intervals recomputed directly.
February attribution-only under owner_mandate_20260801. Streaming throughout.
"""
import gzip
import json
import math
import sys
from collections import defaultdict

JAN_POOL = "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"
FEB_POOL = "/Users/borr/GTOSActive/worktrees/wave18-true-utc-factory-20260801/docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz"
JAN_TL = "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse/CJ_RECLOCKED_S0R0_V7/CJ_RECLOCKED_S0R0_V7_TRADE_LEDGER.jsonl"
FEB_TL = "/Users/borr/GTOSActive/worktrees/wave18-true-utc-factory-20260801/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse/CP_FEBRUARY_TRUE_UTC_S0R0_V1/CP_FEBRUARY_TRUE_UTC_S0R0_V1_TRADE_LEDGER.jsonl"
OUT = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/forensic/a2_verify/ff_family_tension_recompute_result.json"

FAMS = ("current_breaker_re_entry", "structural_distance_extreme")


def wilson95(wins, n):
    if n == 0:
        return None
    z = 1.959963984540054
    p = wins / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return [center - half, center + half]


def scan_pool(path):
    """family -> {n, sum, wins}; and family -> decision_time -> [proxy_r,...]"""
    stats = {f: {"n": 0, "sum": 0.0, "wins": 0, "vals": []} for f in FAMS}
    by_window = {f: defaultdict(list) for f in FAMS}
    with gzip.open(path, "rt") as f:
        for line in f:
            r = json.loads(line)
            fam = r.get("origin_family")
            if fam not in stats:
                continue
            v = r.get("opportunity_net_proxy_r")
            if v is None:
                continue
            s = stats[fam]
            s["n"] += 1
            s["sum"] += v
            s["vals"].append(v)
            if v > 0:
                s["wins"] += 1
            by_window[fam][r["decision_time_utc"]].append(v)
    for f_ in FAMS:
        vals = sorted(stats[f_].pop("vals"))
        n = len(vals)
        med = None
        if n:
            med = vals[n // 2] if n % 2 else 0.5 * (vals[n // 2 - 1] + vals[n // 2])
        stats[f_]["median"] = med
        stats[f_]["mean"] = stats[f_]["sum"] / n if n else None
    return stats, by_window


def load_trades(path):
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            out.append({
                "fam": r.get("origin_family"),
                "decision_time_utc": r.get("decision_time_utc"),
                "net_r": r.get("net_r"),
            })
    return out


def main():
    result = {"schema": "gtos.wave19.a2_verify.lane_ff.family_tension.v1"}
    for win, pool, tl in (("january", JAN_POOL, JAN_TL), ("february", FEB_POOL, FEB_TL)):
        stats, by_window = scan_pool(pool)
        trades = load_trades(tl)
        block = {}
        for fam in FAMS:
            ex = [t for t in trades if t["fam"] == fam]
            ex_sc = [t["net_r"] for t in ex if t["net_r"] is not None]
            paired = []
            no_peer = 0
            for t in ex:
                if t["net_r"] is None:
                    continue
                peers = by_window[fam].get(t["decision_time_utc"], [])
                if peers:
                    paired.append(t["net_r"] - sum(peers) / len(peers))
                else:
                    no_peer += 1
            block[fam] = {
                "pool_nonselected": {
                    "rows": stats[fam]["n"],
                    "mean_r": stats[fam]["mean"],
                    "median_r": stats[fam]["median"],
                    "sum_r": stats[fam]["sum"],
                    "wins": stats[fam]["wins"],
                },
                "executed": {
                    "rows": len(ex),
                    "scoreable_n": len(ex_sc),
                    "mean_r": (sum(ex_sc) / len(ex_sc)) if ex_sc else None,
                    "sum_r": sum(ex_sc),
                    "wins": sum(1 for v in ex_sc if v > 0),
                    "win_share_wilson95": wilson95(sum(1 for v in ex_sc if v > 0), len(ex_sc)),
                },
                "paired_same_window": {
                    "n": len(paired),
                    "executed_minus_peer_mean": (sum(paired) / len(paired)) if paired else None,
                    "positive_pairs": sum(1 for v in paired if v > 0),
                    "executed_scoreable_without_peers": no_peer,
                },
            }
        result[win] = block
    with open(OUT, "w") as f:
        json.dump(result, f, indent=1, sort_keys=True)
    print(json.dumps(result, indent=1, sort_keys=True))


if __name__ == "__main__":
    sys.exit(main())
