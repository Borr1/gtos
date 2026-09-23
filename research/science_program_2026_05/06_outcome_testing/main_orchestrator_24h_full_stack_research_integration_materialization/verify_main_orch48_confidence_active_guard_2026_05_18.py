from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_CONFIDENCE_ACTIVE_GUARD"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"{ROUTE_ID}_VERIFY_RESULT_{DATE}.json"

EXPECTED_ROWS = 4
EXPECTED_TEST_COVERAGE_ROWS = 4
EXPECTED_MANIFEST_OUTPUT_COUNT = 2


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def resolve_display_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return REPO / path


def verify() -> dict[str, Any]:
    issues: list[str] = []
    for path in (LEDGER, SUMMARY, MANIFEST):
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    rows = read_jsonl(LEDGER) if LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}

    if len(rows) != EXPECTED_ROWS:
        issues.append(f"row_count_unexpected:{len(rows)}")
    if summary.get("rows") != len(rows):
        issues.append(f"summary_rows_mismatch:{summary.get('rows')}:{len(rows)}")
    if summary.get("current_shadow_effective_rows") != 1:
        issues.append(f"current_shadow_effective_rows_unexpected:{summary.get('current_shadow_effective_rows')}")
    if summary.get("active_unvalidated_blocked_rows") != 1:
        issues.append(f"active_unvalidated_blocked_rows_unexpected:{summary.get('active_unvalidated_blocked_rows')}")
    if summary.get("active_validated_allowed_rows") != 1:
        issues.append(f"active_validated_allowed_rows_unexpected:{summary.get('active_validated_allowed_rows')}")
    if summary.get("unknown_mode_shadow_rows") != 1:
        issues.append(f"unknown_mode_shadow_rows_unexpected:{summary.get('unknown_mode_shadow_rows')}")
    if summary.get("resolver_helper_present_rows") != 1:
        issues.append(f"resolver_helper_present_rows_unexpected:{summary.get('resolver_helper_present_rows')}")
    if summary.get("orchestrator_uses_resolver_rows") != 1:
        issues.append(f"orchestrator_uses_resolver_rows_unexpected:{summary.get('orchestrator_uses_resolver_rows')}")
    if summary.get("repo_runtime_guard_code_changed_rows") != 1:
        issues.append(
            f"repo_runtime_guard_code_changed_rows_unexpected:{summary.get('repo_runtime_guard_code_changed_rows')}"
        )
    if summary.get("expected_test_names_covered_rows") != EXPECTED_TEST_COVERAGE_ROWS:
        issues.append(f"expected_test_names_covered_rows_unexpected:{summary.get('expected_test_names_covered_rows')}")
    if summary.get("inherited_b12_confidence_predictive_strata") != 0:
        issues.append(
            "inherited_b12_confidence_predictive_strata_unexpected:"
            f"{summary.get('inherited_b12_confidence_predictive_strata')}"
        )
    if summary.get("runtime_behavior_effect_if_unvalidated_active_requested_rows") != 2:
        issues.append(
            "runtime_behavior_effect_if_unvalidated_active_requested_rows_unexpected:"
            f"{summary.get('runtime_behavior_effect_if_unvalidated_active_requested_rows')}"
        )
    if summary.get("current_runtime_behavior_changed_rows") != 0:
        issues.append(
            f"current_runtime_behavior_changed_rows_unexpected:{summary.get('current_runtime_behavior_changed_rows')}"
        )

    expected_surfaces = {
        "confidence_filter_active_guard_test_coverage",
        "confidence_filter_mode_guard_behavior",
        "confidence_filter_quarantine_inheritance",
        "confidence_filter_runtime_guard_patch",
    }
    if set(summary.get("audit_surface_counts") or {}) != expected_surfaces:
        issues.append(f"audit_surface_counts_unexpected:{summary.get('audit_surface_counts')}")

    for key in ("paid_api_or_vendor_call_rows", "broker_operation_rows", "runtime_candidate_use_permitted_rows"):
        if summary.get(key) != 0:
            issues.append(f"{key}_nonzero:{summary.get(key)}")

    effect = summary.get("implementation_effect") or {}
    for key in ("confidence_filter_active_mode_guarded", "current_confidence_filter_mode_remains_shadow"):
        if effect.get(key) is not True:
            issues.append(f"effect_{key}_not_true:{effect.get(key)}")
    for key in (
        "current_runtime_behavior_changed",
        "paid_api_or_vendor_call",
        "broker_operation",
        "runtime_trading_or_live_broker_effect",
        "runtime_candidate_use_permitted",
    ):
        if effect.get(key) is not False:
            issues.append(f"effect_{key}_unexpected:{effect.get(key)}")

    guard_rows = [row for row in rows if row.get("audit_surface") == "confidence_filter_mode_guard_behavior"]
    if len(guard_rows) != 1:
        issues.append(f"guard_row_count_unexpected:{len(guard_rows)}")
    else:
        row = guard_rows[0]
        if row.get("current_requested_mode") != "shadow" or row.get("current_effective_mode") != "shadow":
            issues.append(
                "current_mode_unexpected:"
                f"{row.get('current_requested_mode')}:{row.get('current_effective_mode')}"
            )
        if row.get("active_unvalidated_effective_mode") != "shadow":
            issues.append(f"active_unvalidated_effective_mode_unexpected:{row.get('active_unvalidated_effective_mode')}")
        if row.get("active_unvalidated_blocked_reason") != "active_confidence_filter_requires_validated_promotion":
            issues.append(f"active_unvalidated_blocked_reason_unexpected:{row.get('active_unvalidated_blocked_reason')}")
        if row.get("active_validated_effective_mode") != "active":
            issues.append(f"active_validated_effective_mode_unexpected:{row.get('active_validated_effective_mode')}")

    runtime_rows = [row for row in rows if row.get("audit_surface") == "confidence_filter_runtime_guard_patch"]
    if len(runtime_rows) != 1:
        issues.append(f"runtime_patch_row_count_unexpected:{len(runtime_rows)}")
    else:
        row = runtime_rows[0]
        for key in (
            "resolver_helper_present",
            "active_validation_flag_checked",
            "orchestrator_uses_resolver",
            "unvalidated_active_warning_present",
            "repo_runtime_guard_code_changed",
        ):
            if row.get(key) is not True:
                issues.append(f"runtime_patch_{key}_not_true:{row.get(key)}")

    test_rows = [row for row in rows if row.get("audit_surface") == "confidence_filter_active_guard_test_coverage"]
    if len(test_rows) != 1:
        issues.append(f"test_row_count_unexpected:{len(test_rows)}")
    else:
        covered = test_rows[0].get("expected_test_name_coverage") or {}
        missing = [name for name, present in covered.items() if not present]
        if missing:
            issues.append(f"expected_tests_missing:{missing}")

    for row in rows:
        boundary = row.get("research_boundary") or {}
        row_id = row.get("confidence_active_guard_row_id")
        if boundary.get("current_runtime_behavior_changed"):
            issues.append(f"current_runtime_behavior_changed_claimed:{row_id}")
        for key in ("paid_api_or_vendor_call", "broker_operation", "runtime_trading_or_live_broker_effect", "runtime_candidate_use_permitted"):
            if boundary.get(key):
                issues.append(f"{key}_claimed:{row_id}")
                break

    output_by_name = {Path(item["path"]).name: item for item in manifest.get("outputs") or []}
    for path in (LEDGER, SUMMARY):
        item = output_by_name.get(path.name)
        if not item:
            issues.append(f"manifest_missing_output:{path.name}")
            continue
        if item.get("sha256") != sha256_path(path):
            issues.append(f"manifest_hash_mismatch:{path.name}")
            break
    if len(output_by_name) != EXPECTED_MANIFEST_OUTPUT_COUNT:
        issues.append(f"manifest_output_count_unexpected:{len(output_by_name)}")

    for surface in summary.get("code_surfaces") or []:
        path = resolve_display_path(surface.get("path", ""))
        if not path.exists():
            issues.append(f"code_surface_missing:{surface.get('path')}")
            continue
        if surface.get("sha256") != sha256_path(path):
            issues.append(f"code_surface_hash_mismatch:{surface.get('path')}")
            break

    result = {
        "route_id": ROUTE_ID,
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "rows": len(rows),
        "active_unvalidated_blocked_rows": summary.get("active_unvalidated_blocked_rows"),
        "active_validated_allowed_rows": summary.get("active_validated_allowed_rows"),
        "current_runtime_behavior_changed_rows": summary.get("current_runtime_behavior_changed_rows"),
        "paid_api_or_vendor_call_rows": summary.get("paid_api_or_vendor_call_rows"),
        "broker_operation_rows": summary.get("broker_operation_rows"),
        "runtime_candidate_use_permitted_rows": summary.get("runtime_candidate_use_permitted_rows"),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
