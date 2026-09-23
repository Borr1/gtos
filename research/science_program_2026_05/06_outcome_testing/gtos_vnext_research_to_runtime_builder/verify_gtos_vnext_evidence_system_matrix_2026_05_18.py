from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "GTOS_VNEXT_RESEARCH_TO_RUNTIME_BUILDER"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.gtos_vnext_evidence_system import (  # noqa: E402
    SCHEMA_VERSION,
    find_safety_issues,
    read_jsonl,
    sha256_path,
)


MATRIX = ROUTE_DIR / f"GTOS_VNEXT_EVIDENCE_TO_SYSTEM_BUILD_MATRIX_{DATE}.jsonl"
SOURCE_INVENTORY = ROUTE_DIR / f"GTOS_VNEXT_SOURCE_INVENTORY_{DATE}.jsonl"
RUNTIME_ARCHITECTURE = ROUTE_DIR / f"GTOS_VNEXT_RUNTIME_ARCHITECTURE_DECISION_LEDGER_{DATE}.jsonl"
SCORER_FILTER_ROUTER = ROUTE_DIR / f"GTOS_VNEXT_SCORER_FILTER_ROUTER_IMPLEMENTATION_LEDGER_{DATE}.jsonl"
AI_DECISION = ROUTE_DIR / f"GTOS_VNEXT_AI_DECISION_ARCHITECTURE_LEDGER_{DATE}.jsonl"
GATE_RISK_EXIT = ROUTE_DIR / f"GTOS_VNEXT_GATE_FILTER_SELECTOR_RISK_EXIT_LEDGER_{DATE}.jsonl"
MARKET_TIMEFRAME = ROUTE_DIR / f"GTOS_VNEXT_MARKET_TIMEFRAME_EXPANSION_LEDGER_{DATE}.jsonl"
LEGACY_MERGER = ROUTE_DIR / f"GTOS_VNEXT_LEGACY_RESEARCH_MERGER_LEDGER_{DATE}.jsonl"
EXACT_PROXY_SUMMARY = ROUTE_DIR / f"GTOS_VNEXT_EXACT_PROXY_R_EXPECTANCY_SUMMARY_{DATE}.json"
INSTRUCTION_COVERAGE = ROUTE_DIR / f"GTOS_VNEXT_INSTRUCTION_COVERAGE_LEDGER_{DATE}.jsonl"
COMPLETION_AUDIT = ROUTE_DIR / f"GTOS_VNEXT_CHECKPOINT_COMPLETION_AUDIT_{DATE}.json"
SUMMARY = ROUTE_DIR / f"GTOS_VNEXT_BUILD_MATRIX_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"GTOS_VNEXT_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"GTOS_VNEXT_BUILD_MATRIX_VERIFY_RESULT_{DATE}.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify() -> dict[str, Any]:
    issues: list[str] = []
    required = [
        MATRIX,
        SOURCE_INVENTORY,
        RUNTIME_ARCHITECTURE,
        SCORER_FILTER_ROUTER,
        AI_DECISION,
        GATE_RISK_EXIT,
        MARKET_TIMEFRAME,
        LEGACY_MERGER,
        EXACT_PROXY_SUMMARY,
        INSTRUCTION_COVERAGE,
        COMPLETION_AUDIT,
        SUMMARY,
        MANIFEST,
    ]
    for path in required:
        if not path.exists():
            issues.append(f"missing_output:{path.name}")
    if issues:
        result = {"ok": False, "route_id": ROUTE_ID, "schema_version": SCHEMA_VERSION, "issues": issues}
        write_json(VERIFY_RESULT, result)
        return result

    matrix_rows = read_jsonl(MATRIX)
    inventory_rows = read_jsonl(SOURCE_INVENTORY)
    runtime_rows = read_jsonl(RUNTIME_ARCHITECTURE)
    scorer_rows = read_jsonl(SCORER_FILTER_ROUTER)
    ai_rows = read_jsonl(AI_DECISION)
    gate_rows = read_jsonl(GATE_RISK_EXIT)
    market_rows = read_jsonl(MARKET_TIMEFRAME)
    legacy_rows = read_jsonl(LEGACY_MERGER)
    instruction_rows = read_jsonl(INSTRUCTION_COVERAGE)
    exact_summary = read_json(EXACT_PROXY_SUMMARY)
    completion = read_json(COMPLETION_AUDIT)
    summary = read_json(SUMMARY)
    manifest = read_json(MANIFEST)

    expected_rows = sum(row.get("source_rows", 0) for row in inventory_rows)
    if len(matrix_rows) != expected_rows:
        issues.append(f"matrix_source_row_count_mismatch:{len(matrix_rows)}:{expected_rows}")
    if summary.get("matrix_rows") != len(matrix_rows):
        issues.append(f"summary_matrix_rows_mismatch:{summary.get('matrix_rows')}:{len(matrix_rows)}")
    if summary.get("source_rows_expected") != expected_rows:
        issues.append(f"summary_source_rows_expected_mismatch:{summary.get('source_rows_expected')}:{expected_rows}")
    if summary.get("all_source_rows_preserved") is not True:
        issues.append("summary_all_source_rows_preserved_not_true")

    matrix_ids = [row.get("vnext_matrix_row_id") for row in matrix_rows]
    if len(matrix_ids) != len(set(matrix_ids)):
        issues.append("duplicate_matrix_row_ids")
    for row in matrix_rows[:10]:
        if not row.get("source_artifact_sha256") or not row.get("source_row_payload_sha256"):
            issues.append(f"matrix_row_missing_hash:{row.get('vnext_matrix_row_id')}")
            break
        if not row.get("source_line_no"):
            issues.append(f"matrix_row_missing_line:{row.get('vnext_matrix_row_id')}")
            break

    safety_issues = find_safety_issues(matrix_rows)
    if safety_issues:
        issues.extend(safety_issues[:25])

    expected_target_counts = summary.get("ledger_target_counts") or {}
    split_counts = {
        "scorer_filter_router": len(scorer_rows),
        "ai_decision_architecture": len(ai_rows),
        "gate_filter_selector_risk_exit": len(gate_rows),
        "market_timeframe_expansion": len(market_rows),
        "legacy_research_merger": len(legacy_rows),
    }
    for target, count in split_counts.items():
        if count != expected_target_counts.get(target):
            issues.append(f"target_split_count_mismatch:{target}:{count}:{expected_target_counts.get(target)}")

    if len(runtime_rows) != len(inventory_rows):
        issues.append(f"runtime_architecture_count_mismatch:{len(runtime_rows)}:{len(inventory_rows)}")
    if any(row.get("all_source_rows_preserved") is not True for row in runtime_rows):
        issues.append("runtime_architecture_source_preservation_failed")

    exact_expected_rows = expected_target_counts.get("exact_proxy_r")
    if exact_summary.get("overall", {}).get("source_rows") != exact_expected_rows:
        issues.append(
            "exact_proxy_source_rows_mismatch:"
            f"{exact_summary.get('overall', {}).get('source_rows')}:{exact_expected_rows}"
        )
    if completion.get("can_mark_goal_complete") is not False:
        issues.append("completion_audit_allows_goal_complete")
    if completion.get("checkpoint_status") != "CHECKPOINT_NOT_FINAL_72H_OBJECTIVE_REMAINS_ACTIVE":
        issues.append("completion_audit_not_checkpoint_status")
    if any(row.get("coverage_status") == "FAIL" for row in instruction_rows):
        issues.append("instruction_coverage_contains_fail")

    manifest_outputs = manifest.get("outputs") or []
    manifest_by_path = {row.get("path"): row for row in manifest_outputs}
    for path in required:
        if path == MANIFEST:
            continue
        key = str(path.resolve().relative_to(REPO.resolve())).replace("\\", "/")
        manifest_row = manifest_by_path.get(key)
        if not manifest_row:
            issues.append(f"manifest_missing_output:{path.name}")
            continue
        if manifest_row.get("sha256") != sha256_path(path):
            issues.append(f"manifest_sha_mismatch:{path.name}")

    result = {
        "ok": not issues,
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "issues": issues,
        "matrix_rows": len(matrix_rows),
        "source_rows_expected": expected_rows,
        "runtime_architecture_rows": len(runtime_rows),
        "split_counts": split_counts,
        "exact_proxy_rows": exact_summary.get("overall", {}).get("source_rows"),
        "instruction_coverage_rows": len(instruction_rows),
    }
    write_json(VERIFY_RESULT, result)
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, sort_keys=True))
