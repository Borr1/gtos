#!/usr/bin/env python3
"""A2 RECONCILE lane — full Jan MISSED ledger streaming pass (153,425 rows, 1.34 GB).

Recomputes the PHYSICAL-side numbers of register rows D (7,575), I (3,536 and 3,281),
the funnel waterfall anchors (128,293 / 125,012 / 8,581 / 4,486 / 125,767), and the
key-count adjudication for row F ("80 fields"). Line-by-line; constant memory.
Writes MISSED_LEDGER_RESULT.json beside itself.
"""
import json, os, sys
from collections import Counter

OUT = os.path.dirname(os.path.abspath(__file__))
LEDGER = ("/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/research/operations/"
          "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/"
          "attempt_5_typed_sparse/CJ_RECLOCKED_S0R0_V7/CJ_RECLOCKED_S0R0_V7_MISSED_OPPORTUNITY_LEDGER.jsonl")
FBC = "missed_package_replay_order_executable_final_blocker_class"
SCS = "missed_opportunity_r_scoreability_status"
MAT = "scheduler_option_materialized"
RISK = {"trade", "open-reduced-risk", "reduce-risk"}
SCOREABLE = "missed_opportunity_diagnostic_scoreable"   # provisional; report actual values


def main():
    n = 0
    keycount = Counter()
    union_keys = set()
    scs_counter = Counter()
    sel_counter = Counter()
    packet_counter = Counter()
    blocker_counter = Counter()
    mat_counter = Counter()
    rej_mat = 0
    rej_mat_eff = Counter()
    rej_mat_reason = Counter()
    rej_mat_scs = Counter()
    effrisk_mat = 0
    effrisk_mat_scoreable = 0
    mat_total = 0
    mat_scs = Counter()
    refused_blocker_by_scoreable = {"scoreable": Counter(), "nonscoreable": Counter()}
    cost_failed_missreason = 0
    scoreable_blocker = Counter()
    scoreable_packet = Counter()

    with open(LEDGER) as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            n += 1
            keycount[len(r)] += 1
            if len(union_keys) < 200:
                union_keys.update(r.keys())
            scs = r.get(SCS)
            scs_counter[str(scs)] += 1
            scoreable = (r.get("opportunity_net_proxy_r") is not None)
            sa = r.get("selector_action")
            esa = r.get("effective_selector_action")
            mat = r.get("scheduler_materialization_status")
            packet = r.get("pretrade_cost_packet_status")
            blocker = r.get(FBC)
            sel_counter[str(sa)] += 1
            packet_counter[str(packet)] += 1
            blocker_counter[str(blocker)] += 1
            mat_counter[str(mat)] += 1
            inB = (mat == MAT)
            if inB:
                mat_total += 1
                mat_scs["scoreable" if scoreable else "nonscoreable"] += 1
            if sa == "reject" and inB:
                rej_mat += 1
                rej_mat_eff[str(esa)] += 1
                rej_mat_reason[str(r.get("selector_reason"))] += 1
                rej_mat_scs["scoreable" if scoreable else "nonscoreable"] += 1
            if esa in RISK and inB:
                effrisk_mat += 1
                if scoreable:
                    effrisk_mat_scoreable += 1
            if packet == "REFUSED":
                refused_blocker_by_scoreable["scoreable" if scoreable else "nonscoreable"][str(blocker)] += 1
            mr = str(r.get("miss_reason"))
            if "cost_failed" in mr:
                cost_failed_missreason += 1
            if scoreable:
                scoreable_blocker[str(blocker)] += 1
                scoreable_packet[str(packet)] += 1
            if n % 25000 == 0:
                print(f"...{n}", file=sys.stderr)

    refused_total = packet_counter.get("REFUSED", 0)
    cost_auth_total = blocker_counter.get("cost_authority", 0)
    out = {
        "schema": "gtos.a2_verify.reconcile.missed_ledger_pass.v1",
        "total_physical_rows": n,
        "F_row_key_count_distribution": dict(keycount),
        "F_union_key_count": len(union_keys),
        "scoreability_status_counts": dict(scs_counter.most_common()),
        "selector_action_counts": dict(sel_counter.most_common()),
        "packet_status_counts": dict(packet_counter.most_common()),
        "final_blocker_counts": dict(blocker_counter.most_common()),
        "materialization_status_counts": dict(mat_counter.most_common(8)),
        "I_reject_and_materialized_physical": rej_mat,
        "I_reject_mat_effective_action": dict(rej_mat_eff),
        "I_reject_mat_selector_reason": dict(rej_mat_reason),
        "I_reject_mat_scoreable_split": dict(rej_mat_scs),
        "I_refused_total": refused_total,
        "I_cost_authority_blocker_total": cost_auth_total,
        "I_refused_minus_cost_authority": refused_total - cost_auth_total,
        "I_refused_blocker_by_scoreable": {k: dict(v.most_common()) for k, v in refused_blocker_by_scoreable.items()},
        "I_scoreable_blocker_counts": dict(scoreable_blocker.most_common()),
        "I_scoreable_packet_counts": dict(scoreable_packet.most_common()),
        "D_effective_risk_and_materialized_physical": effrisk_mat,
        "D_effective_risk_and_materialized_scoreable": effrisk_mat_scoreable,
        "D_materialized_physical": mat_total,
        "D_materialized_scoreable_split": dict(mat_scs),
        "miss_reason_contains_cost_failed": cost_failed_missreason,
        "F_pool_vs_ledger_keys_note": "computed in md; union captured here",
        "F_ledger_union_keys": sorted(union_keys),
    }
    with open(os.path.join(OUT, "MISSED_LEDGER_RESULT.json"), "w") as f:
        json.dump(out, f, indent=1)
    for k in ("total_physical_rows", "I_reject_and_materialized_physical",
              "I_refused_total", "I_cost_authority_blocker_total",
              "I_refused_minus_cost_authority", "D_effective_risk_and_materialized_physical",
              "D_effective_risk_and_materialized_scoreable", "D_materialized_physical"):
        print(k, "=", out[k])
    print("reject_mat eff:", out["I_reject_mat_effective_action"])
    print("reject_mat reasons:", out["I_reject_mat_selector_reason"])
    print("reject_mat scoreable split:", out["I_reject_mat_scoreable_split"])
    print("materialized split:", out["D_materialized_scoreable_split"])
    print("refused blocker nonscoreable:", out["I_refused_blocker_by_scoreable"]["nonscoreable"])
    print("scoreability:", out["scoreability_status_counts"])
    print("key count dist:", out["F_row_key_count_distribution"])


if __name__ == "__main__":
    main()
