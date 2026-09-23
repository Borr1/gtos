#!/usr/bin/env python3
"""FG4 raw recompute: stream the Jan and Feb S0R0 pools line-by-line and
recompute the ghost-written result's headline aggregates.

February is read attribution-only under owner_mandate_20260801.
Never touches March or live-forward data. Peak memory: O(1) aggregates.
"""
import gzip, json

POOLS = {
    "january": "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz",
    "february": "/Users/borr/GTOSActive/worktrees/wave18-true-utc-factory-20260801/docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz",
}

out = {}
for label, path in POOLS.items():
    n = 0
    net_sum = 0.0
    net_nonnull = 0
    cost_sum = 0.0
    cost_nonnull = 0
    prob_sum = 0.0
    prob_nonnull = 0
    pos_rows = 0
    refused_n = 0
    refused_net_sum = 0.0
    refused_cost_sum = 0.0
    refused_pos = 0
    blocker_counts = {}
    with gzip.open(path, "rt") as f:
        for line in f:
            d = json.loads(line)
            n += 1
            netv = d.get("opportunity_net_proxy_r")
            costv = d.get("cost_r")
            probv = d.get("candidate_probability")
            if netv is not None:
                net_sum += netv
                net_nonnull += 1
                if netv > 0:
                    pos_rows += 1
            if costv is not None:
                cost_sum += costv
                cost_nonnull += 1
            if probv is not None:
                prob_sum += probv
                prob_nonnull += 1
            fbc = str(d.get("final_blocker_class"))
            blocker_counts[fbc] = blocker_counts.get(fbc, 0) + 1
            if fbc == "cost_authority":
                refused_n += 1
                if netv is not None:
                    refused_net_sum += netv
                    if netv > 0:
                        refused_pos += 1
                if costv is not None:
                    refused_cost_sum += costv
    out[label] = {
        "rows": n,
        "net_nonnull": net_nonnull,
        "net_sum_r": round(net_sum, 6),
        "net_mean_r": round(net_sum / max(net_nonnull, 1), 6),
        "cost_nonnull": cost_nonnull,
        "cost_sum_r": round(cost_sum, 6),
        "gross_sum_r_as_net_plus_cost": round(net_sum + cost_sum, 6),
        "candidate_probability_mean": round(prob_sum / max(prob_nonnull, 1), 6),
        "prob_nonnull": prob_nonnull,
        "net_positive_rows": pos_rows,
        "net_positive_rate": round(pos_rows / max(net_nonnull, 1), 6),
        "cost_authority_refused_n": refused_n,
        "cost_authority_refused_mean_net_r": round(refused_net_sum / max(refused_n, 1), 6),
        "cost_authority_refused_mean_cost_r": round(refused_cost_sum / max(refused_n, 1), 6),
        "cost_authority_refused_n_positive": refused_pos,
        "final_blocker_class_counts": blocker_counts,
    }

print(json.dumps(out, indent=1))
