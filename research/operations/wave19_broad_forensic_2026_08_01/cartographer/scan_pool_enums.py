#!/usr/bin/env python3
"""Cartographer receipt tool: stream a compact pool and count unique values of
the enum-like decision-cycle fields. Streams line-by-line (never loads whole
file). Wave 19 forensic, Session FA."""
import gzip
import json
import sys
from collections import Counter, defaultdict

ENUM_FIELDS = [
    "selector_action",
    "selector_reason",
    "effective_selector_action",
    "effective_selector_reason",
    "admission_risk_class",
    "scheduler_materialization_status",
    "scheduler_selection_disposition",
    "risk_finalizer_rank",
    "risk_finalizer_reason",
    "miss_reason",
    "candidate_lifecycle_action",
    "final_blocker_class",
    "missed_opportunity_r_scoreability_status",
    "missed_opportunity_non_executable_diagnostic_scoreable",
    "candidate_confidence",
    "confidence_default_applied",
    "broker_pretrade_cost_executable",
    "pretrade_cost_packet_status",
    "entry_fill_executable",
    "fill_realism_class",
    "fill_realism_executable",
    "effective_order_type",
    "dynamic_geometry_policy",
    "selected_policy_for_expected_net_r",
    "scheduler_materialization_status",
    "same_symbol_lifecycle_action",
    "origin_family",
    "framework",
    "route_family",
    "bucket_source_family",
    "setup_family",
    "authority_session",
    "swap_horizon_repair_status",
    "commission_r_repair_status",
    "limit_marketable_at_decision",
    "source_completeness",
    "risk_per_trade_pct",
    "policy_target_r",
    "raw_target_r",
    "candidate_probability",
    "candidate_ev_r",
    "expectancy_r",
    "fill_probability",
    "entry_quality_fill_probability",
    "execution_fill_probability",
    "limit_fillability_probability",
    "effective_admission_count",
    "matched_sleeve_count",
]


def main(path: str, out_path: str, max_uniques: int = 40) -> None:
    counters: dict[str, Counter] = defaultdict(Counter)
    n = 0
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            n += 1
            for f in ENUM_FIELDS:
                v = row.get(f)
                if isinstance(v, float):
                    v = round(v, 6)
                counters[f][json.dumps(v)] += 1
    out = {"rows": n, "fields": {}}
    for f, c in counters.items():
        top = c.most_common(max_uniques)
        out["fields"][f] = {
            "n_unique": len(c),
            "top": [{"value": v, "count": k} for v, k in top],
        }
    with open(out_path, "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    print(f"rows={n} fields={len(counters)} -> {out_path}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
