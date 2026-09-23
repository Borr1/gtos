#!/usr/bin/env python3
"""Verify Wave C close-side broker-cost capture repair artifacts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROUTE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
PARENT_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_full_plan_goal_session_2026_06_19"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stable_verified_utc(result: dict[str, Any]) -> str:
    existing_path = ROUTE / "VERIFICATION_RESULT.json"
    if not existing_path.exists():
        return utc_now()
    try:
        existing = read_json(existing_path)
    except json.JSONDecodeError:
        return utc_now()
    comparable_existing = {key: value for key, value in existing.items() if key != "verified_utc"}
    comparable_result = {key: value for key, value in result.items() if key != "verified_utc"}
    if comparable_existing == comparable_result:
        return existing.get("verified_utc") or utc_now()
    return utc_now()


def main() -> int:
    issues: list[str] = []
    summary = read_json(ROUTE / "WAVE_C_CLOSE_SIDE_BROKER_COST_CAPTURE_SUMMARY.json")
    probes = read_jsonl(ROUTE / "WAVE_C_CLOSE_SIDE_SOURCE_PROBE_LEDGER.jsonl")
    current_rows = read_jsonl(ROUTE / "WAVE_C_CURRENT_TRADE_CLOSE_JOIN_LEDGER.jsonl")
    contract = read_json(ROUTE / "WAVE_C_CLOSE_SIDE_BROKER_COST_CAPTURE_CONTRACT.json")
    blockers = {row["blocker_id"]: row for row in read_jsonl(ROUTE / "WAVE_C_CLOSE_SIDE_RESIDUAL_BLOCKER_LEDGER.jsonl")}
    manifest = read_json(ROUTE / "OUTPUT_MANIFEST.json")
    completion = read_json(ROUTE / "COMPLETION_AUDIT.json")
    parent_questions = {row["question_id"]: row for row in read_jsonl(PARENT_ROUTE / "PARENT_ACTIVE_QUESTION_STACK.jsonl")}
    parent_sources = {row["request_id"]: row for row in read_jsonl(PARENT_ROUTE / "PARENT_SOURCE_REQUEST_LEDGER.jsonl")}
    parent_merges = {row["decision_id"]: row for row in read_jsonl(PARENT_ROUTE / "PARENT_MERGE_DECISION_LEDGER.jsonl")}
    source_text = (ROOT / "src/components/execution.py").read_text(encoding="utf-8")

    if summary.get("status") != "close_side_broker_cost_capture_checkpoint_not_final_selection":
        issues.append("summary_status_mismatch")
    if summary.get("local_ultimate_trade_records") != 9 or len(current_rows) != 9:
        issues.append("current_trade_row_count_mismatch")
    if summary.get("entry_account_history_reconciled_rows") != 9:
        issues.append("entry_reconciled_count_mismatch")
    if summary.get("current_trade_records_with_broker_actual_r") != 0:
        issues.append("broker_actual_r_unexpectedly_present")
    if summary.get("current_trade_records_with_close_block") != 0:
        issues.append("close_block_unexpectedly_present")
    if summary.get("local_account_history_deal_rows") != 46:
        issues.append("account_history_deal_row_count_mismatch")
    if summary.get("local_account_history_current_ticket_matches") != 0:
        issues.append("account_history_current_ticket_match_unexpected")
    if summary.get("local_close_slippage_rows") != 87:
        issues.append("close_slippage_row_count_mismatch")
    if summary.get("local_close_slippage_rows_with_commission") != 62:
        issues.append("close_slippage_commission_count_mismatch")
    if summary.get("local_close_slippage_rows_with_swap") != 62:
        issues.append("close_slippage_swap_count_mismatch")
    if summary.get("current_close_slippage_ticket_matches") != 0:
        issues.append("current_close_slippage_ticket_match_unexpected")
    if summary.get("code_repair_close_deal_lookup_present") is not True:
        issues.append("code_repair_not_detected")
    if "def _lookup_close_deal_accounting" not in source_text:
        issues.append("execution_close_lookup_missing")
    if 'broker_profit=metadata.get("broker_profit")' not in source_text:
        issues.append("execution_broker_profit_not_forwarded")
    if summary.get("terminal_decision", {}).get("final_package_selected") is not False:
        issues.append("final_package_selected")
    if any(value is not False for value in summary.get("forbidden_surface_status", {}).values()):
        issues.append("forbidden_surface_status_not_false")
    if len(probes) != 4:
        issues.append("source_probe_row_count_mismatch")
    if contract.get("status") != "prospective_close_side_read_only_account_history_capture_wired":
        issues.append("contract_status_mismatch")
    if blockers.get("WFB002", {}).get("status") != "partially_repaired_prospective_close_side_account_history_capture_wired_current_rows_still_unjoined":
        issues.append("wfb002_status_mismatch")
    if completion.get("goal_completion_claim") is not False:
        issues.append("completion_claim_not_false")
    for required in [
        "WAVE_C_CLOSE_SIDE_BROKER_COST_CAPTURE_SUMMARY.json",
        "WAVE_C_CLOSE_SIDE_SOURCE_PROBE_LEDGER.jsonl",
        "WAVE_C_CURRENT_TRADE_CLOSE_JOIN_LEDGER.jsonl",
        "WAVE_C_CLOSE_SIDE_BROKER_COST_CAPTURE_CONTRACT.json",
        "WAVE_C_CLOSE_SIDE_RESIDUAL_BLOCKER_LEDGER.jsonl",
        "VERIFICATION_RESULT.json",
    ]:
        if required not in set(manifest.get("files") or []):
            issues.append(f"manifest_missing:{required}")
    if parent_questions.get("PQ016", {}).get("status") != "answered_close_side_capture_checkpoint":
        issues.append("parent_pq016_missing")
    if parent_sources.get("PSR017", {}).get("status") != "prospective_close_capture_wired_current_close_rows_unjoined":
        issues.append("parent_psr017_missing")
    if parent_merges.get("PMD015", {}).get("status") != "selected":
        issues.append("parent_pmd015_missing")

    result = {
        "schema": "gtos.final_moonshot.wave_c.close_side_broker_cost_capture.verification_result.v1",
        "verified_utc": utc_now(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "local_ultimate_trade_records": summary.get("local_ultimate_trade_records"),
        "entry_account_history_reconciled_rows": summary.get("entry_account_history_reconciled_rows"),
        "current_trade_records_with_broker_actual_r": summary.get("current_trade_records_with_broker_actual_r"),
        "local_close_slippage_rows": summary.get("local_close_slippage_rows"),
        "current_close_slippage_ticket_matches": summary.get("current_close_slippage_ticket_matches"),
        "wfb002_status": summary.get("wfb002_status"),
        "final_package_selected": summary.get("terminal_decision", {}).get("final_package_selected"),
        "forbidden_surface_status": summary.get("forbidden_surface_status", {}),
    }
    result["verified_utc"] = stable_verified_utc(result)
    write_json(ROUTE / "VERIFICATION_RESULT.json", result)
    focused = read_json(ROUTE / "FOCUSED_TEST_RESULT.json")
    focused["status"] = "passed" if not issues else "failed"
    focused["verification_result"] = {"ok": result["ok"], "issue_count": result["issue_count"], "verified_utc": result["verified_utc"]}
    write_json(ROUTE / "FOCUSED_TEST_RESULT.json", focused)
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
