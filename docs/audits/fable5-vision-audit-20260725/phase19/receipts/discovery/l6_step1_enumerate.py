#!/usr/bin/env python3
"""l6 STEP 1 — enumerate EVERY gate/refusal field and every distinct value, with the
outcome of what it refused. Writes L6_GATE_ENUM_V1.json."""
import json, os, sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
from l6_lib import load, stats  # noqa: E402

FIELDS = [
    "final_blocker_class", "miss_reason",
    "selector_action", "selector_reason",
    "effective_selector_action", "effective_selector_reason",
    "risk_finalizer_reason", "risk_finalizer_rank",
    "scheduler_selection_disposition", "scheduler_materialization_status",
    "candidate_lifecycle_action", "same_symbol_lifecycle_action",
    "pretrade_cost_packet_status", "broker_pretrade_cost_executable",
    "admission_risk_class", "fill_realism_class", "fill_realism_executable",
    "entry_fill_executable", "effective_order_type", "source_completeness",
    "limit_marketable_at_decision", "effective_admission_count", "matched_sleeve_count",
    "route_session", "session_bucket", "authority_session", "kill_zone",
    "dynamic_geometry_policy", "selected_policy_for_expected_net_r",
    "swap_horizon_repair_status", "commission_r_repair_status",
    "confidence_default_applied", "decision_timeframe", "born", "hreason",
]


def main():
    rows = load()
    res = {"n_pool": len(rows), "POOL": stats(rows, "ALL"), "fields": {}}
    for f in FIELDS:
        g = {}
        for r in rows:
            g.setdefault(str(r.get(f)), []).append(r)
        vals = []
        for v, rs in sorted(g.items(), key=lambda kv: -len(kv[1])):
            vals.append(stats(rs, v))
        res["fields"][f] = {
            "n_distinct": len(g),
            "values": vals,
        }
    out = os.path.join(D, "L6_GATE_ENUM_V1.json")
    with open(out, "w") as fh:
        json.dump(res, fh, indent=1)
    # compact console summary
    print("POOL", json.dumps({k: res["POOL"][k] for k in
          ("n", "eng_gross_mean", "takeable_n", "h_gross_mean", "h_win_pct",
           "h_net_corr73_mean")}))
    for f in FIELDS:
        d = res["fields"][f]
        print(f"{f:42s} {d['n_distinct']:3d} vals  top={d['values'][0]['value'][:34]:34s} n={d['values'][0]['n']}")


if __name__ == "__main__":
    main()
