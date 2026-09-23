#!/usr/bin/env python3
"""Supplemental parent absorption verifier for lifecycle/fillability bridge route."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROUTE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
BRIDGE_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_final_package_lifecycle_fillability_bridge_2026_06_19"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def close_enough(actual: Any, expected: float, tolerance: float = 1e-6) -> bool:
    try:
        return abs(float(actual) - expected) <= tolerance
    except (TypeError, ValueError):
        return False


def main() -> int:
    issues: list[str] = []
    bridge_summary = read_json(BRIDGE_ROUTE / "FINAL_PACKAGE_LIFECYCLE_FILLABILITY_BRIDGE_SUMMARY.json")
    bridge_verification = read_json(BRIDGE_ROUTE / "VERIFICATION_RESULT.json")
    parent_audit = read_json(ROUTE / "PARENT_COMPLETION_AUDIT.json")
    parent_board = read_json(ROUTE / "PARENT_WAVE_STATUS_BOARD.json")

    wave_f = next((row for row in parent_board.get("waves", []) if row.get("wave") == "F"), {})
    if not bridge_verification.get("ok"):
        issues.append("bridge_route_verification_not_ok")
    if bridge_summary.get("status") != "final_package_lifecycle_fillability_bridge_checkpoint_exact_denominator_still_open":
        issues.append("bridge_summary_status_mismatch")
    expected_counts = {
        "input_package_sleeve_rows": 82,
        "input_sleeve_member_rows": 1101,
        "input_lifecycle_label_rows": 877,
        "context_bridge_rows": 19216,
        "context_bridged_sleeve_rows": 73,
        "context_bridged_member_rows": 730,
        "context_bridged_label_rows": 877,
        "exact_denominator_join_rows": 0,
    }
    for field, expected in expected_counts.items():
        if bridge_summary.get(field) != expected:
            issues.append(f"bridge_{field}_mismatch")
    if not close_enough(bridge_summary.get("preserved_combined_source_bound_signal_r"), 1249248.03066685):
        issues.append("bridge_preserved_signal_mismatch")
    terminal = bridge_summary.get("terminal_decision", {})
    if terminal.get("candidate_lifecycle_context_bridge_materialized") is not True:
        issues.append("bridge_context_not_materialized")
    if terminal.get("exact_lifecycle_denominator_bridge_closed") is not False:
        issues.append("bridge_exact_denominator_unexpectedly_closed")
    for field in [
        "broker_actual_r_claim_allowed",
        "broker_actual_r_is_edge_source",
        "deployment_dossier_allowed",
        "final_package_selected",
        "live_execution_activation_allowed",
        "model_training_allowed",
    ]:
        if terminal.get(field) is not False:
            issues.append(f"bridge_terminal_boundary_not_false:{field}")
    wave_f_evidence = set(wave_f.get("evidence") or [])
    required_evidence = {
        "research/operations/final_moonshot_ultimate_system_final_package_lifecycle_fillability_bridge_2026_06_19/FINAL_PACKAGE_LIFECYCLE_FILLABILITY_BRIDGE_SUMMARY.json",
        "research/operations/final_moonshot_ultimate_system_final_package_lifecycle_fillability_bridge_2026_06_19/FINAL_PACKAGE_LIFECYCLE_CONTEXT_JOIN_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_final_package_lifecycle_fillability_bridge_2026_06_19/FINAL_PACKAGE_LIFECYCLE_RESIDUAL_GATE_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_final_package_lifecycle_fillability_bridge_2026_06_19/VERIFICATION_RESULT.json",
    }
    missing_evidence = sorted(required_evidence - wave_f_evidence)
    if missing_evidence:
        issues.append(f"parent_wave_f_bridge_evidence_missing:{','.join(missing_evidence)}")
    verification = parent_audit.get("verification", {})
    if verification.get("final_package_lifecycle_fillability_bridge") != "passed":
        issues.append("parent_audit_bridge_verification_missing")
    if parent_audit.get("goal_completion_claim") is not False:
        issues.append("parent_goal_completion_claim_not_false")

    result = {
        "schema": "gtos.final_moonshot.ultimate_system_full_plan.parent_lifecycle_fillability_bridge_absorption.v1",
        "verified_utc": utc_now(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "context_bridge_rows": bridge_summary.get("context_bridge_rows"),
        "context_bridged_member_rows": bridge_summary.get("context_bridged_member_rows"),
        "context_bridged_label_rows": bridge_summary.get("context_bridged_label_rows"),
        "exact_denominator_join_rows": bridge_summary.get("exact_denominator_join_rows"),
        "final_package_selected": terminal.get("final_package_selected"),
    }
    write_json(ROUTE / "PARENT_LIFECYCLE_FILLABILITY_BRIDGE_VERIFICATION_RESULT.json", result)
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
