#!/usr/bin/env python3
"""Session FA / wave-19 forensic — February refusal-funnel analyst.

Streams a full MISSED_OPPORTUNITY ledger (1.2-1.4 GB jsonl) line by line and
writes a compact pickle of the ~23 funnel-relevant fields per physical row.
Never holds the raw ledger in memory. February re-decode is owner-authorized
for defect attribution only; every derived number is attribution evidence,
never a selection surface.

Usage: python3 extract_funnel_fields.py <ledger.jsonl> <out.pkl.gz>
"""
import sys, json, gzip, pickle

FIELDS = [
    "selector_action", "selector_reason",
    "effective_selector_action", "effective_selector_reason",
    "scheduler_materialization_status", "scheduler_selection_disposition",
    "risk_finalizer_rank", "risk_finalizer_reason",
    "miss_reason", "candidate_lifecycle_action",
    "missed_opportunity_non_executable_diagnostic_scoreable",
    "missed_opportunity_r_scoreability_status",
    "opportunity_net_proxy_r", "cost_r", "opportunity_gross_r",
    "spread_r", "commission_r", "expected_slippage_r", "swap_cost_r",
    "framework", "origin_family", "route_family", "dynamic_geometry_policy",
    "direction", "session_bucket", "authority_session", "route_session",
    "symbol", "trading_day", "utc_hour_bucket", "effective_order_type",
    "admission_risk_class", "broker_pretrade_cost_executable",
    "entry_fill_executable", "fill_realism_executable", "fill_realism_class",
    "candidate_confidence", "candidate_ev_r", "expected_net_r",
]
# final blocker field name differs between compact pool and full ledger
BLOCKER_KEYS = ("missed_package_replay_order_executable_final_blocker_class",
                "final_blocker_class")

def main(src, dst):
    rows = []
    n = 0
    with open(src, "rb") as f:
        for line in f:
            if not line.strip():
                continue
            d = json.loads(line)
            n += 1
            rec = {k: d.get(k) for k in FIELDS}
            for bk in BLOCKER_KEYS:
                if bk in d:
                    rec["final_blocker_class"] = d[bk]
                    break
            else:
                rec["final_blocker_class"] = None
            rows.append(rec)
            if n % 20000 == 0:
                print(f"  {n} rows", file=sys.stderr, flush=True)
    with gzip.open(dst, "wb", compresslevel=4) as g:
        pickle.dump(rows, g, protocol=4)
    print(f"DONE {src}: {n} physical rows -> {dst}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
