"""Verifier for the NOFILL historical partition/source-binding route."""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Any

ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research_infra.forward_capture import NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS


PREFIX = "NOFILL_HISTORICAL_SEALED_VALIDATION"
SAFE_FLAG_KEYS = ("validation_safe", "outcome_review_opened", "live_effect")
FORBIDDEN_TRUE_KEYS = (
    "opens_result_scoring",
    "opens_validation",
    "opens_promotion",
    "opens_registry_edit",
    "opens_paid_api_or_databento_route",
    "opens_live_trading_behavior",
    "changes_live_trading_behavior",
)


def load_json(name: str) -> dict[str, Any]:
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


def load_jsonl(name: str) -> list[dict[str, Any]]:
    rows = []
    with (ROUTE_DIR / name).open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def scan_forbidden_true(obj: Any, path: str = "$") -> list[str]:
    issues: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            child = f"{path}.{key}"
            if key in SAFE_FLAG_KEYS and value is not False:
                issues.append(f"{child} must be false")
            if key in FORBIDDEN_TRUE_KEYS and value is True:
                issues.append(f"{child} opens forbidden route")
            if key == "promotion_verdict" and value != "NO_PROMOTION_VERDICT":
                issues.append(f"{child} must be NO_PROMOTION_VERDICT")
            issues.extend(scan_forbidden_true(value, child))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            issues.extend(scan_forbidden_true(value, f"{path}[{idx}]"))
    return issues


def parse_all_generated() -> list[str]:
    issues: list[str] = []
    for path in ROUTE_DIR.glob("*.json"):
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - verifier reports exact failure
            issues.append(f"{path.name} JSON parse failed: {exc}")
            continue
        issues.extend(scan_forbidden_true(obj, path.name))
    for path in ROUTE_DIR.glob("*.jsonl"):
        try:
            with path.open(encoding="utf-8") as f:
                for idx, line in enumerate(f, start=1):
                    if line.strip():
                        obj = json.loads(line)
                        issues.extend(scan_forbidden_true(obj, f"{path.name}:{idx}"))
        except Exception as exc:  # pragma: no cover
            issues.append(f"{path.name} JSONL parse failed: {exc}")
    for path in ROUTE_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        if "NO_PROMOTION_VERDICT" not in text and "Prompt Pack" not in path.name:
            issues.append(f"{path.name} missing NO_PROMOTION_VERDICT text")
    return issues


def verify() -> dict[str, Any]:
    issues: list[str] = []
    issues.extend(parse_all_generated())

    partition = load_json(f"{PREFIX}_PARTITION_LEDGER_2026-05-10.json")
    partition_rows = load_jsonl(f"{PREFIX}_PARTITION_ROW_LEDGER_2026-05-10.jsonl")
    contamination = load_json(f"{PREFIX}_CONTAMINATION_PROOF_LEDGER_2026-05-10.json")
    field_matrix = load_json(f"{PREFIX}_55_FIELD_SOURCE_BINDING_MATRIX_2026-05-10.json")
    blockers = load_json(f"{PREFIX}_FIELD_BLOCKERS_OWNER_REQUIREMENTS_LEDGER_2026-05-10.json")
    search = load_json(f"{PREFIX}_LOCAL_HEAVY_DATA_PRIOR_ARTIFACT_SEARCH_LEDGER_2026-05-10.json")
    forbidden = load_json(f"{PREFIX}_FORBIDDEN_ROUTE_LEDGER_2026-05-10.json")
    completion = load_json(f"{PREFIX}_COMPLETION_AUDIT_2026-05-10.json")

    if len(partition_rows) != 298:
        issues.append(f"partition row count must be 298, got {len(partition_rows)}")
    family_counts = {}
    for row in partition_rows:
        family_counts[row["v3_terminal_family"]] = family_counts.get(row["v3_terminal_family"], 0) + 1
        if row.get("sealed_validation_eligible") is not False:
            issues.append(f"{row.get('packet_row_id')} unexpectedly sealed-validation eligible")
    expected_family_counts = {"accepted": 225, "reject": 65, "source_control": 4, "source_impossible": 4}
    if family_counts != expected_family_counts:
        issues.append(f"terminal family counts mismatch: {family_counts}")
    if partition.get("sealed_validation_current_committed_nofill_rows") != 0:
        issues.append("sealed validation committed NOFILL rows must be 0")
    if contamination.get("all_cat_v3_rows_contaminated_for_future_validation") is not True:
        issues.append("contamination proof must mark CAT V3 rows contaminated")

    fields = field_matrix.get("fields", [])
    field_names = [row.get("field_name") for row in fields]
    if len(fields) != 55:
        issues.append(f"field matrix must have 55 rows, got {len(fields)}")
    if set(field_names) != set(NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS):
        issues.append("field matrix names do not match runtime NOFILL contract")
    allowed_binding_classes = {
        "SOURCE_BOUND_HISTORICAL_OR_FAIL_CLOSED",
        "FUTURE_LOGGER_BOUND_REQUIRED_FOR_FULL_COVERAGE",
        "SCHEMA_ONLY_CONTROL",
        "FORBIDDEN_REDACTED_STATUS_ONLY",
        "EXACT_BLOCKED_OWNER_SOURCE_CAPTURE_REQUIRED",
    }
    for row in fields:
        if row.get("binding_class") not in allowed_binding_classes:
            issues.append(f"{row.get('field_name')} has invalid binding class {row.get('binding_class')}")
        if not row.get("exact_requirement_before_validation"):
            issues.append(f"{row.get('field_name')} missing exact requirement")
    expected_design_counts = {
        "EXISTING_SOURCE_SAFE_CAPTURE_READY": 17,
        "FORBIDDEN_OR_REDACTED_SOURCE_ONLY": 7,
        "FUTURE_LOGGER_FIELD_REQUIRED": 20,
        "SCHEMA_ONLY_CONTROL_FIELD": 11,
    }
    if field_matrix.get("design_terminal_status_counts") != expected_design_counts:
        issues.append(f"design status counts mismatch: {field_matrix.get('design_terminal_status_counts')}")
    if blockers.get("field_blocker_count") != 20:
        issues.append(f"expected 20 future logger/source extraction requirements, got {blockers.get('field_blocker_count')}")
    if search.get("nofill_shadow_capture_logs", {}).get("status") not in {
        "NO_NOFILL_FORWARD_SOURCE_CAPTURE_LOG_FOUND",
        "NOFILL_FORWARD_SOURCE_CAPTURE_LOG_METADATA_PRESENT",
    }:
        issues.append("local search ledger nofill shadow status invalid")
    if any(item.get("opened") for item in forbidden.get("forbidden_surfaces", [])):
        issues.append("forbidden route ledger opened a forbidden surface")
    if completion.get("can_mark_goal_complete_after_commit_and_closeout_verification") is not True:
        issues.append("completion audit does not allow goal completion after commit/closeout")

    for path in ROUTE_DIR.glob("*.py"):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            issues.append(f"{path.name} syntax parse failed: {exc}")

    result = {
        "ok": not issues,
        "route_id": "NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_AND_SOURCE_BINDING",
        "schema_version": "nofill_historical_sealed_validation_partition_and_source_binding_verifier_v1",
        "issues": issues,
        "cat_v3_partition_rows": len(partition_rows),
        "field_count": len(fields),
        "field_blocker_count": blockers.get("field_blocker_count"),
        "sealed_validation_current_committed_nofill_rows": partition.get(
            "sealed_validation_current_committed_nofill_rows"
        ),
        "can_mark_goal_complete": not issues,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    (ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_2026-05-10.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
