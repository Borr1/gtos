from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
ROUTE_DIR = Path(__file__).resolve().parent
LANE01_LEDGER = ROOT / "research" / "operations" / "vnext_lane01_fixed_friday_portfolio_replay_engine_2026_05_31" / "LANE01_RISK_EXPOSURE_DOLLAR_R_LEDGER.jsonl"
RESULT_PATH = ROUTE_DIR / "LANE05_VERIFICATION_RESULT.json"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            text = line.strip()
            if text:
                rows.append(json.loads(text))
    return rows


def main() -> int:
    issues = []
    required = [
        "LANE05_RUNTIME_SCHEDULER_CODE_PATH_LEDGER.jsonl",
        "LANE05_SCHEDULER_LEDGER.jsonl",
        "LANE05_BEFORE_AFTER_GATE_MATRIX.jsonl",
        "LANE05_IMPLEMENTATION_DECISION_LEDGER.jsonl",
        "LANE05_SOURCE_COMPLETENESS_LEDGER.jsonl",
        "LANE05_SHARED_CODE_OWNERSHIP_LEDGER.jsonl",
        "LANE05_FOCUSED_TEST_RESULT.json",
        "LANE05_OUTPUT_MANIFEST.json",
        "LANE05_COMPLETION_AUDIT.json",
    ]
    for name in required:
        if not (ROUTE_DIR / name).exists():
            issues.append(f"missing_required_output:{name}")

    scheduler_rows = read_jsonl(ROUTE_DIR / "LANE05_SCHEDULER_LEDGER.jsonl")
    source_rows = read_jsonl(LANE01_LEDGER)
    if len(scheduler_rows) != len(source_rows):
        issues.append(f"scheduler_row_count_mismatch:{len(scheduler_rows)}!={len(source_rows)}")

    authorities = {row.get("final_risk_authority") for row in scheduler_rows}
    for required_authority in {
        "account_exposure_budget_accept",
        "account_exposure_budget_reject",
        "same_symbol_lifecycle_guard_reject",
    }:
        if required_authority not in authorities:
            issues.append(f"missing_scheduler_authority:{required_authority}")

    matrix = read_jsonl(ROUTE_DIR / "LANE05_BEFORE_AFTER_GATE_MATRIX.jsonl")
    scenario_ids = {row.get("scenario_id") for row in matrix}
    for required_scenario in {
        "account_exposure_allow_full_risk",
        "account_exposure_reduce_to_overall_budget",
        "account_exposure_defer_until_daily_reset",
        "account_exposure_block_current_overall_breach",
        "pending_risk_reduces_budget",
        "simultaneous_candidates_reserve_budget",
        "non_vnext_legacy_concurrent_cap_blocks",
        "governed_vnext_bypasses_legacy_concurrent_cap",
        "same_symbol_vnext_conflict_blocks_until_multi_ticket_contract",
    }:
        if required_scenario not in scenario_ids:
            issues.append(f"missing_gate_matrix_scenario:{required_scenario}")

    code_rows = read_jsonl(ROUTE_DIR / "LANE05_RUNTIME_SCHEDULER_CODE_PATH_LEDGER.jsonl")
    missing_markers = [row.get("marker_id") for row in code_rows if row.get("status") != "present"]
    if missing_markers:
        issues.append(f"missing_code_markers:{missing_markers}")

    tests = read_json(ROUTE_DIR / "LANE05_FOCUSED_TEST_RESULT.json")
    if not tests.get("ok"):
        issues.append("focused_tests_not_ok")

    audit = read_json(ROUTE_DIR / "LANE05_COMPLETION_AUDIT.json")
    if audit.get("status") != "pass":
        issues.append(f"completion_audit_not_pass:{audit.get('status')}")

    result = {
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "route_id": "vnext_lane05_runtime_portfolio_scheduler_integration_2026_05_31",
        "schema_version": "lane05_verification_result_v1",
        "scheduler_rows": len(scheduler_rows),
        "gate_matrix_rows": len(matrix),
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
