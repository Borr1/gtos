#!/usr/bin/env python3
"""Verify candidate-level expert match materialization artifacts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROUTE = Path(__file__).resolve().parent


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(name: str) -> Any:
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def read_jsonl(name: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in (ROUTE / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(name: str, data: Any) -> None:
    (ROUTE / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    now = utc_now()
    issues: list[str] = []
    required = [
        "build_candidate_level_match_materialization.py",
        "verify_candidate_level_match_materialization.py",
        "CANDIDATE_LEVEL_MATCH_SUMMARY.json",
        "CANDIDATE_LEVEL_MATCH_LEDGER.jsonl",
        "CANDIDATE_LEVEL_MATCH_SOURCE_ATTEMPT_LEDGER.jsonl",
        "CANDIDATE_LEVEL_MATCH_AGGREGATE_LEDGER.jsonl",
        "CANDIDATE_LEVEL_MATCH_DECISION_LEDGER.jsonl",
        "CANDIDATE_LEVEL_MATCH_REPAIR_LEDGER.jsonl",
        "COMPLETION_AUDIT.json",
        "FOCUSED_TEST_RESULT.json",
        "SATURATION_SELF_RED_TEAM.md",
        "CANDIDATE_LEVEL_MATCH_NEXT_PROMPT.md",
        "OUTPUT_MANIFEST.json",
    ]
    for name in required:
        if not (ROUTE / name).exists():
            issues.append(f"missing_required:{name}")

    summary = read_json("CANDIDATE_LEVEL_MATCH_SUMMARY.json")
    rows = read_jsonl("CANDIDATE_LEVEL_MATCH_LEDGER.jsonl")
    source_attempts = read_jsonl("CANDIDATE_LEVEL_MATCH_SOURCE_ATTEMPT_LEDGER.jsonl")
    aggregates = read_jsonl("CANDIDATE_LEVEL_MATCH_AGGREGATE_LEDGER.jsonl")
    repairs = read_jsonl("CANDIDATE_LEVEL_MATCH_REPAIR_LEDGER.jsonl")
    completion = read_json("COMPLETION_AUDIT.json")
    manifest = read_json("OUTPUT_MANIFEST.json")

    source_counts: dict[str, int] = {}
    for row in rows:
        source_counts[row.get("source_kind", "")] = source_counts.get(row.get("source_kind", ""), 0) + 1
        if row.get("broker_runtime_change_status") is not False:
            issues.append(f"broker_runtime_change_status_not_false:{row.get('match_row_id')}")
        if row.get("direct_execution_authority") is not False:
            issues.append(f"direct_execution_authority_not_false:{row.get('match_row_id')}")
        if row.get("forbidden_surface_crossed") is not False:
            issues.append(f"forbidden_surface_crossed:{row.get('match_row_id')}")
        if row.get("candidate_use_allowed_now") is True:
            issues.append(f"candidate_use_allowed_now_true:{row.get('match_row_id')}")

    if summary.get("ledger_rows") != len(rows):
        issues.append("summary_ledger_row_count_mismatch")
    expected_counts = {
        "selector_v3_runtime_rule": summary.get("selector_v3_runtime_rule_rows"),
        "cp281_ready_runtime_mapping_rule": summary.get("cp281_ready_runtime_mapping_rows"),
        "vnext_build_matrix_material_row": summary.get("vnext_build_matrix_rows"),
    }
    for source_kind, expected in expected_counts.items():
        if source_counts.get(source_kind, 0) != expected:
            issues.append(f"source_count_mismatch:{source_kind}")
    if source_counts.get("selector_v3_runtime_rule") != 2027:
        issues.append("selector_v3_runtime_rule_count_not_full")
    if source_counts.get("cp281_ready_runtime_mapping_rule") != 461:
        issues.append("cp281_runtime_mapping_count_not_full")
    if source_counts.get("vnext_build_matrix_material_row", 0) <= 0:
        issues.append("vnext_build_matrix_rows_missing")
    if len(rows) != sum(source_counts.values()):
        issues.append("ledger_source_count_sum_mismatch")

    source_status = {row.get("source_key"): row.get("read_status") for row in source_attempts}
    for source_key in ["selector_v3_package", "cp281_rule_ledger", "vnext_build_matrix", "vps_source_of_truth_update", "prior_candidate_replay_summary"]:
        if source_status.get(source_key) != "readable":
            issues.append(f"required_source_not_readable:{source_key}:{source_status.get(source_key)}")
    if source_status.get("scheduler_v3_blocked_edge") != "read_error:EDEADLK":
        issues.append(f"scheduler_source_status_unexpected:{source_status.get('scheduler_v3_blocked_edge')}")
    if source_status.get("wave4r_microscope") not in {"readable", "read_error:EDEADLK"}:
        issues.append(f"wave4r_source_status_unexpected:{source_status.get('wave4r_microscope')}")

    if not any(row.get("aggregate") == "source_kind" for row in aggregates):
        issues.append("missing_source_kind_aggregates")
    if completion.get("goal_completion_claim") is not False:
        issues.append("completion_claim_not_false")
    if completion.get("instruction_coverage", {}).get("no_arbitrary_top_n") is not True:
        issues.append("instruction_no_top_n_not_covered")
    if summary.get("final_package_selected") is not False:
        issues.append("summary_final_package_selected")
    if summary.get("model_training_allowed") is not False:
        issues.append("summary_model_training_allowed")
    if any(value is not False for value in summary.get("forbidden_surface_status", {}).values()):
        issues.append("summary_forbidden_surface_true")
    if not repairs:
        issues.append("empty_repair_ledger")
    if not all(item.get("exists") is True for item in manifest.get("files", [])):
        issues.append("manifest_file_missing")

    result = {
        "schema": "gtos.final_moonshot.candidate_level_match_materialization.verification_result.v1",
        "verified_utc": now,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "ledger_rows": len(rows),
        "source_counts": source_counts,
        "read_blocker_count": summary.get("read_blocker_count"),
        "source_status": source_status,
        "final_package_selected": summary.get("final_package_selected"),
        "model_training_allowed": summary.get("model_training_allowed"),
    }
    write_json("VERIFICATION_RESULT.json", result)
    focused = read_json("FOCUSED_TEST_RESULT.json")
    focused["status"] = "passed" if not issues else "failed"
    focused["verification_result"] = {"ok": result["ok"], "issue_count": result["issue_count"], "verified_utc": now}
    write_json("FOCUSED_TEST_RESULT.json", focused)
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
