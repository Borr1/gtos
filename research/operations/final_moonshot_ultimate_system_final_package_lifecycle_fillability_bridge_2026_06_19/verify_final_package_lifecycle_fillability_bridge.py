#!/usr/bin/env python3
"""Verify lifecycle/fillability/order-type bridge artifacts for compressed package sleeves."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROUTE = Path(__file__).resolve().parent


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def close_enough(actual: Any, expected: float, tolerance: float = 1e-6) -> bool:
    try:
        return abs(float(actual) - expected) <= tolerance
    except (TypeError, ValueError):
        return False


def stable_verified_utc(result: dict[str, Any]) -> str:
    path = ROUTE / "VERIFICATION_RESULT.json"
    if not path.exists():
        return utc_now()
    try:
        existing = read_json(path)
    except json.JSONDecodeError:
        return utc_now()
    old = {key: value for key, value in existing.items() if key != "verified_utc"}
    new = {key: value for key, value in result.items() if key != "verified_utc"}
    return existing.get("verified_utc") or utc_now() if old == new else utc_now()


def main() -> int:
    issues: list[str] = []
    summary = read_json(ROUTE / "FINAL_PACKAGE_LIFECYCLE_FILLABILITY_BRIDGE_SUMMARY.json")
    source_rows = read_jsonl(ROUTE / "FINAL_PACKAGE_LIFECYCLE_FILLABILITY_SOURCE_LEDGER.jsonl")
    sleeve_rows = read_jsonl(ROUTE / "FINAL_PACKAGE_LIFECYCLE_SLEEVE_BRIDGE_LEDGER.jsonl")
    member_rows = read_jsonl(ROUTE / "FINAL_PACKAGE_LIFECYCLE_MEMBER_BRIDGE_LEDGER.jsonl")
    label_rows = read_jsonl(ROUTE / "FINAL_PACKAGE_LIFECYCLE_LABEL_BRIDGE_LEDGER.jsonl")
    context_rows = read_jsonl(ROUTE / "FINAL_PACKAGE_LIFECYCLE_CONTEXT_JOIN_LEDGER.jsonl")
    gap_rows = read_jsonl(ROUTE / "FINAL_PACKAGE_LIFECYCLE_SOURCE_GAP_LEDGER.jsonl")
    residual_rows = read_jsonl(ROUTE / "FINAL_PACKAGE_LIFECYCLE_RESIDUAL_GATE_LEDGER.jsonl")
    decisions = read_jsonl(ROUTE / "DECISION_LEDGER.jsonl")
    completion = read_json(ROUTE / "COMPLETION_AUDIT.json")
    manifest = read_json(ROUTE / "OUTPUT_MANIFEST.json")

    if summary.get("status") != "final_package_lifecycle_fillability_bridge_checkpoint_exact_denominator_still_open":
        issues.append("summary_status_mismatch")
    expected_counts = {
        "input_package_sleeve_rows": 82,
        "input_sleeve_member_rows": 1101,
        "input_lifecycle_label_rows": 877,
        "input_order_type_capture_requirement_rows": 4,
        "context_bridge_rows": 19216,
        "sleeve_bridge_rows": 82,
        "member_bridge_rows": 1101,
        "label_bridge_rows": 877,
        "source_gap_rows": 4,
        "residual_gate_rows": 4,
        "context_bridged_sleeve_rows": 73,
        "context_bridged_member_rows": 730,
        "context_bridged_label_rows": 877,
        "exact_denominator_join_rows": 0,
    }
    for field, expected in expected_counts.items():
        if summary.get(field) != expected:
            issues.append(f"{field}_mismatch")
    if len(source_rows) != 4:
        issues.append("source_rows_mismatch")
    if len(sleeve_rows) != 82:
        issues.append("sleeve_rows_mismatch")
    if len(member_rows) != 1101:
        issues.append("member_rows_mismatch")
    if len(label_rows) != 877:
        issues.append("label_rows_mismatch")
    if len(context_rows) != 19216:
        issues.append("context_rows_mismatch")
    if len(gap_rows) != 4:
        issues.append("gap_rows_mismatch")
    if len(residual_rows) != 4:
        issues.append("residual_rows_mismatch")
    if len(decisions) < 3:
        issues.append("decision_rows_too_low")
    if not close_enough(summary.get("preserved_combined_source_bound_signal_r"), 1249248.03066685):
        issues.append("preserved_signal_mismatch")
    if summary.get("broker_actual_r_role") != "calibration_only_not_edge_source":
        issues.append("broker_actual_r_role_mismatch")
    if summary.get("member_bridge_status_counts") != {
        "context_bridge_available_exact_denominator_blocked": 730,
        "no_lifecycle_label_context_for_symbol_side": 371,
    }:
        issues.append("member_bridge_status_counts_mismatch")
    if summary.get("sleeve_bridge_status_counts") != {
        "context_bridge_available_exact_denominator_blocked": 73,
        "no_lifecycle_label_context_for_sleeve_symbols": 9,
    }:
        issues.append("sleeve_bridge_status_counts_mismatch")
    if summary.get("label_bridge_status_counts") != {
        "context_bridge_available_exact_denominator_blocked": 877,
    }:
        issues.append("label_bridge_status_counts_mismatch")
    if any(row.get("exact_denominator_join_allowed") is not False for row in sleeve_rows + member_rows + label_rows + context_rows):
        issues.append("exact_denominator_join_unexpectedly_allowed")
    if any(row.get("final_package_selection_allowed") is not False for row in gap_rows + residual_rows + context_rows):
        issues.append("final_selection_unexpectedly_allowed")
    if not any(row.get("gate_id") == "FPSG002" and row.get("status") == "context_bridge_materialized_exact_denominator_still_open" for row in residual_rows):
        issues.append("fpsg002_status_missing")
    if not any(row.get("gap_id") == "LFOG001" and row.get("status") == "open_exact_denominator_bridge_requirement" for row in gap_rows):
        issues.append("candidate_namespace_gap_missing")
    if not any(row.get("label_fill_no_fill") == "internal_filled_broker_ticket_known" for row in context_rows):
        issues.append("filled_lifecycle_context_missing")
    if not any(row.get("label_fill_no_fill") == "no_fill_still_pending" for row in context_rows):
        issues.append("nofill_lifecycle_context_missing")
    if any(value is not False for value in summary.get("forbidden_surface_status", {}).values()):
        issues.append("forbidden_surface_crossed")
    terminal = summary.get("terminal_decision", {})
    if terminal.get("candidate_lifecycle_context_bridge_materialized") is not True:
        issues.append("context_bridge_not_materialized")
    if terminal.get("exact_lifecycle_denominator_bridge_closed") is not False:
        issues.append("exact_bridge_unexpectedly_closed")
    for field in [
        "broker_actual_r_claim_allowed",
        "broker_actual_r_is_edge_source",
        "deployment_dossier_allowed",
        "final_package_selected",
        "live_execution_activation_allowed",
        "model_training_allowed",
    ]:
        if terminal.get(field) is not False:
            issues.append(f"terminal_boundary_not_false:{field}")
    manifest_files = set(manifest.get("files") or [])
    for required in [
        "FINAL_PACKAGE_LIFECYCLE_FILLABILITY_BRIDGE_SUMMARY.json",
        "FINAL_PACKAGE_LIFECYCLE_SLEEVE_BRIDGE_LEDGER.jsonl",
        "FINAL_PACKAGE_LIFECYCLE_MEMBER_BRIDGE_LEDGER.jsonl",
        "FINAL_PACKAGE_LIFECYCLE_LABEL_BRIDGE_LEDGER.jsonl",
        "FINAL_PACKAGE_LIFECYCLE_CONTEXT_JOIN_LEDGER.jsonl",
        "FINAL_PACKAGE_LIFECYCLE_SOURCE_GAP_LEDGER.jsonl",
        "FINAL_PACKAGE_LIFECYCLE_RESIDUAL_GATE_LEDGER.jsonl",
        "VERIFICATION_RESULT.json",
    ]:
        if required not in manifest_files:
            issues.append(f"manifest_missing:{required}")
    if completion.get("goal_completion_claim") is not False:
        issues.append("completion_claim_not_false")

    result = {
        "schema": "gtos.final_moonshot.final_package_lifecycle_fillability_bridge.verification_result.v1",
        "verified_utc": utc_now(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "context_bridge_rows": len(context_rows),
        "sleeve_bridge_rows": len(sleeve_rows),
        "member_bridge_rows": len(member_rows),
        "label_bridge_rows": len(label_rows),
        "context_bridged_sleeve_rows": len({row.get("sleeve_id") for row in context_rows}),
        "context_bridged_member_rows": len({row.get("source_axis_row_index") for row in context_rows}),
        "context_bridged_label_rows": len({row.get("label_id") for row in context_rows}),
        "exact_denominator_join_rows": summary.get("exact_denominator_join_rows"),
        "member_bridge_status_counts": dict(Counter(row.get("bridge_status") for row in member_rows)),
        "sleeve_bridge_status_counts": dict(Counter(row.get("bridge_status") for row in sleeve_rows)),
        "final_package_selected": terminal.get("final_package_selected"),
        "exact_lifecycle_denominator_bridge_closed": terminal.get("exact_lifecycle_denominator_bridge_closed"),
    }
    result["verified_utc"] = stable_verified_utc(result)
    write_json(ROUTE / "VERIFICATION_RESULT.json", result)
    completion["verification"]["final_package_lifecycle_fillability_bridge"] = "passed" if not issues else "failed"
    write_json(ROUTE / "COMPLETION_AUDIT.json", completion)
    focused = read_json(ROUTE / "FOCUSED_TEST_RESULT.json")
    focused["status"] = "passed" if not issues else "failed"
    focused["verification_result"] = {
        "ok": result["ok"],
        "issue_count": result["issue_count"],
        "verified_utc": result["verified_utc"],
    }
    write_json(ROUTE / "FOCUSED_TEST_RESULT.json", focused)
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
