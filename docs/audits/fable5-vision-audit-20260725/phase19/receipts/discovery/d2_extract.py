"""d2_extract — pull the REAL downstream decision record for every roster candidate.

For each of the eight open sealed S0R0 arms, stream the MISSED_OPPORTUNITY ledger (the
declined set = roster minus selected) and the TRADE ledger (the taken set), and write a
slim per-candidate record keyed on (candidate_id, decision_time_utc) — the key Session PB
proved joins the reproduced roster to the sealed arm at 153,211/153,486 = 99.82 %.

Nothing is sampled: every row of every ledger is read.
"""
from __future__ import annotations

import gzip
import io
import json
import os
import subprocess
import sys
from pathlib import Path

ARM = {
    "2025-10": ("/Users/borr/GTOSActive/worktrees/fa2-integration-20260803/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse/LP_OCT_2025_S0R0", "LP_OCT_2025_S0R0"),
    "2025-11": ("/Users/borr/GTOSActive/worktrees/fa2-integration-20260803/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse/LP_NOV_2025_S0R0", "LP_NOV_2025_S0R0"),
    "2025-12": ("/Users/borr/GTOSActive/worktrees/fa2-integration-20260803/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse/LP_DEC_2025_S0R0", "LP_DEC_2025_S0R0"),
    "2026-01": ("/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse/CJ_RECLOCKED_S0R0_V7", "CJ_RECLOCKED_S0R0_V7"),
    "2026-02": ("/Users/borr/GTOSActive/worktrees/wave18-true-utc-factory-20260801/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse/CP_FEBRUARY_TRUE_UTC_S0R0_V1", "CP_FEBRUARY_TRUE_UTC_S0R0_V1"),
    "2026-03": ("/Users/borr/GTOSActive/worktrees/fa2-integration-20260803/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse/FA2_M_R0", "FA2_M_R0"),
    "2026-04": ("/Users/borr/GTOSActive/worktrees/wave19-breaker-folds-20260801/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse/CS_APRIL_S0R0_V2", "CS_APRIL_S0R0_V2"),
    "2026-05": ("/Users/borr/GTOSActive/worktrees/wave19-breaker-folds-20260801/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse/CS_MAY_S0R0_V1", "CS_MAY_S0R0_V1"),
}

MISS_FIELDS = [
    "candidate_id", "decision_time_utc", "symbol", "origin_family", "side", "direction",
    "entry_price", "stop_loss", "take_profit_1", "decision_timeframe",
    "miss_reason", "selector_action", "selector_reason",
    "effective_selector_action", "effective_selector_reason",
    "risk_finalizer_reason", "risk_finalizer_rank",
    "scheduler_materialization_status", "scheduler_selection_disposition",
    "admission_risk_class", "missed_package_replay_order_executable_final_blocker_class",
    "candidate_confidence", "candidate_probability", "candidate_ev_r", "expectancy_r",
    "expected_net_r", "expected_cost_r", "expected_slippage_r", "fill_probability",
    "cost_r", "spread_r", "commission_r", "swap_cost_r", "risk_per_trade_pct",
    "broker_pretrade_cost_executable", "entry_fill_executable", "fill_realism_class",
    "limit_marketable_at_decision", "effective_order_type", "dynamic_geometry_policy",
    "policy_target_r", "raw_target_r", "opportunity_net_proxy_r",
    "missed_opportunity_r_scoreability_status", "session_bucket", "utc_hour_bucket",
    "confidence_missing_degraded_default_applied", "source_completeness",
    "same_symbol_lifecycle_action", "opposite_pending_risk_pct", "same_side_pending_risk_pct",
]


def open_ledger(base: Path, stem: str, kind: str):
    for ext, mode in ((".jsonl.zst", "zst"), (".jsonl.gz", "gz"), (".jsonl", "raw")):
        p = base / f"{stem}_{kind}_LEDGER{ext}"
        if p.is_file():
            if mode == "zst":
                pr = subprocess.Popen(["zstdcat", str(p)], stdout=subprocess.PIPE)
                return io.TextIOWrapper(pr.stdout, encoding="utf-8"), pr
            if mode == "gz":
                return gzip.open(p, "rt"), None
            return open(p, "rt"), None
    raise FileNotFoundError(f"{base}/{stem}_{kind}_LEDGER")


def run_month(month: str, outdir: Path):
    base, stem = ARM[month]
    base = Path(base)
    outdir.mkdir(parents=True, exist_ok=True)

    n = 0
    with gzip.open(outdir / f"D2_MISS_{month}.jsonl.gz", "wt") as out:
        fh, pr = open_ledger(base, stem, "MISSED_OPPORTUNITY")
        for line in fh:
            r = json.loads(line)
            out.write(json.dumps({k: r.get(k) for k in MISS_FIELDS}) + "\n")
            n += 1
        fh.close()
        if pr:
            pr.wait()

    # taken trades — keep every field, there are only ~500 of them per estate
    m = 0
    with gzip.open(outdir / f"D2_TRADE_{month}.jsonl.gz", "wt") as out:
        fh, pr = open_ledger(base, stem, "TRADE")
        for line in fh:
            out.write(line if line.endswith("\n") else line + "\n")
            m += 1
        fh.close()
        if pr:
            pr.wait()

    # arm identity — selection/sizing factor, from the first decision row
    fh, pr = open_ledger(base, stem, "DECISION")
    first = json.loads(fh.readline())
    fh.close()
    if pr:
        pr.kill()
    ident = {k: v for k, v in first.items() if k.startswith("b7_5_selection_sizing_factorial_")}
    (outdir / f"D2_IDENT_{month}.json").write_text(json.dumps(ident, indent=1))
    print(f"{month}: missed={n} trades={m} S={ident.get('b7_5_selection_sizing_factorial_selection_factor')}"
          f" mode={ident.get('b7_5_selection_sizing_factorial_selection_mode')}"
          f" R={ident.get('b7_5_selection_sizing_factorial_sizing_factor')}"
          f" smode={ident.get('b7_5_selection_sizing_factorial_sizing_mode')}", flush=True)


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/d2")
    months = sys.argv[2].split(",") if len(sys.argv) > 2 else list(ARM)
    for mo in months:
        run_month(mo, out)
    print("ALLDONE", flush=True)
