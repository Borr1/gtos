#!/usr/bin/env python3
"""Stream the Jan/Feb MISSED_OPPORTUNITY ledgers line-by-line and count the
funnel-stage populations FF's licensing narrative uses (FF-L1 context).
Nothing is accumulated beyond counters. February: attribution-only under
owner_mandate_20260801."""
import json
import sys
from collections import Counter

JAN_MISSED = "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse/CJ_RECLOCKED_S0R0_V7/CJ_RECLOCKED_S0R0_V7_MISSED_OPPORTUNITY_LEDGER.jsonl"
FEB_MISSED = "/Users/borr/GTOSActive/worktrees/wave18-true-utc-factory-20260801/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse/CP_FEBRUARY_TRUE_UTC_S0R0_V1/CP_FEBRUARY_TRUE_UTC_S0R0_V1_MISSED_OPPORTUNITY_LEDGER.jsonl"
OUT = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/forensic/a2_verify/ff_funnel_stream_result.json"


def scan(path):
    n = 0
    fvg = 0
    xau = 0
    fvg_cost_exec = 0
    cost_exec = 0
    sel_action = Counter()
    sched_status = Counter()
    sel_pass = 0
    fvg_sel_pass = 0
    sched_mat = 0
    fvg_sched_mat = 0
    xau_cost_exec = 0
    xau_sel_pass = 0
    xau_sched_mat = 0
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            n += 1
            fam = r.get("origin_family")
            is_fvg = fam == "current_fvg_fill"
            is_xau = r.get("symbol") == "XAUUSD"
            if is_fvg:
                fvg += 1
            if is_xau:
                xau += 1
            ce = r.get("broker_pretrade_cost_executable") is True
            if ce:
                cost_exec += 1
                if is_fvg:
                    fvg_cost_exec += 1
                if is_xau:
                    xau_cost_exec += 1
            act = r.get("effective_selector_action")
            sel_action[act] += 1
            sp = ce and act not in ("reject", None)
            if sp:
                sel_pass += 1
                if is_fvg:
                    fvg_sel_pass += 1
                if is_xau:
                    xau_sel_pass += 1
            ss = r.get("scheduler_materialization_status")
            sched_status[ss] += 1
            sm = ss not in (None, "not_scheduler_ranked")
            if sm:
                sched_mat += 1
                if is_fvg:
                    fvg_sched_mat += 1
                if is_xau:
                    xau_sched_mat += 1
    return {
        "rows": n,
        "fvg_rows": fvg,
        "xauusd_rows": xau,
        "cost_executable_true": cost_exec,
        "fvg_cost_executable_true": fvg_cost_exec,
        "xau_cost_executable_true": xau_cost_exec,
        "selector_action_counts": dict(sel_action.most_common(12)),
        "selector_pass_proxy_cost_exec_and_not_reject": sel_pass,
        "fvg_selector_pass_proxy": fvg_sel_pass,
        "xau_selector_pass_proxy": xau_sel_pass,
        "scheduler_status_counts": dict(sched_status.most_common(12)),
        "scheduler_materialized_proxy_not_none_not_skipped": sched_mat,
        "fvg_scheduler_materialized_proxy": fvg_sched_mat,
        "xau_scheduler_materialized_proxy": xau_sched_mat,
    }


def main():
    out = {
        "schema": "gtos.wave19.a2_verify.lane_ff.funnel_stream.v1",
        "note": "streamed line-by-line; counters only; February attribution-only under owner_mandate_20260801",
        "january_missed": scan(JAN_MISSED),
        "february_missed": scan(FEB_MISSED),
    }
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    sys.exit(main())
