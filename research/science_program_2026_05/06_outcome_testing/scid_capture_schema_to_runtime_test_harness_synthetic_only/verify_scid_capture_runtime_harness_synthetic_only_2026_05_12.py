"""Standalone verifier for the route-local synthetic-only SCID harness."""

from __future__ import annotations

import json
import ast
from pathlib import Path
from typing import Any

import runtime_harness_synthetic_only_2026_05_12 as harness


DATE_TAG = "2026-05-12"
PREFIX = harness.ARTIFACT_PREFIX


def rel(path: Path) -> str:
    return path.resolve().relative_to(harness.REPO_ROOT).as_posix()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def fail(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def imports_production_src(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "src" or alias.name.startswith("src."):
                    return True
        if isinstance(node, ast.ImportFrom):
            if node.module == "src" or (node.module and node.module.startswith("src.")):
                return True
    return False


def verify() -> dict[str, Any]:
    failures: list[str] = []
    schemas = harness.load_accepted_schemas()
    fail(failures, "__master__" in schemas, "missing_master_schema")
    group_schemas = [group for group in schemas if group != "__master__"]
    fail(failures, sorted(group_schemas) == sorted(harness.CAPTURE_GROUPS), "capture_group_schema_set_mismatch")
    fail(failures, len(group_schemas) == 10, "schema_group_count_not_10")

    cases = harness.build_fixture_cases()
    outcomes = harness.validate_fixture_cases(cases)
    fail(failures, len(cases) >= 90, "fixture_case_count_below_saturation_floor")
    fail(failures, all(outcome.pass_status for outcome in outcomes), "fixture_outcome_expected_validity_mismatch")

    matrix = harness.category_matrix(cases)
    required_categories = {
        "positive_base",
        "positive_variant",
        "missing_required",
        "stale_asof",
        "forbidden_identifier",
        "duplicate_key_drift",
        "unavailable_source",
        "unsafe_flag",
        "manifest_repair_valid",
        "manifest_repair_invalid",
        "schema_version_mismatch",
        "unexpected_field",
    }
    missing_categories = sorted(required_categories - set(matrix))
    fail(failures, not missing_categories, f"missing_required_categories:{missing_categories}")

    for group in harness.CAPTURE_GROUPS:
        group_cases = [case for case in cases if case.field_group == group]
        fail(failures, any(case.category.startswith("positive") and case.expected_valid for case in group_cases), f"missing_positive_case:{group}")
        fail(failures, any(case.category == "missing_required" and not case.expected_valid for case in group_cases), f"missing_missing_required_negative:{group}")
        fail(failures, any(case.category == "stale_asof" and not case.expected_valid for case in group_cases), f"missing_stale_negative:{group}")
        fail(failures, any(case.category == "forbidden_identifier" and not case.expected_valid for case in group_cases), f"missing_forbidden_negative:{group}")
        fail(failures, any(case.category == "duplicate_key_drift" and not case.expected_valid for case in group_cases), f"missing_duplicate_negative:{group}")
        fail(failures, any(case.category == "unsafe_flag" and not case.expected_valid for case in group_cases), f"missing_unsafe_negative:{group}")
        fail(failures, any(case.category == "schema_version_mismatch" and not case.expected_valid for case in group_cases), f"missing_schema_version_negative:{group}")
        fail(failures, any(case.category == "unexpected_field" and not case.expected_valid for case in group_cases), f"missing_unexpected_field_negative:{group}")
        unavailable_cases = [case for case in group_cases if case.category == "unavailable_source"]
        fail(failures, bool(unavailable_cases), f"missing_unavailable_route:{group}")
        if group in harness.MARKET_CONTEXT_UNAVAILABLE_GROUPS:
            fail(failures, unavailable_cases[0].expected_valid and unavailable_cases[0].fail_closed_semantics, f"market_group_unavailable_not_valid_fail_closed:{group}")
        else:
            fail(failures, not unavailable_cases[0].expected_valid and bool(unavailable_cases[0].inapplicable_reason), f"non_market_unavailable_missing_inapplicable_proof:{group}")

    leak = harness.leak_redaction_audit(cases)
    fail(failures, leak["accepted_rows_clean"], "accepted_rows_have_forbidden_hits")
    fail(failures, leak["deliberate_negative_hit_count"] == 10, "deliberate_forbidden_negative_count_not_10")

    fixture_manifest_path = harness.ROUTE_DIR / f"{PREFIX}_FIXTURE_MANIFEST_{DATE_TAG}.json"
    fixture_validation_path = harness.ROUTE_DIR / f"{PREFIX}_FIXTURE_VALIDATION_RESULT_{DATE_TAG}.json"
    leak_path = harness.ROUTE_DIR / f"{PREFIX}_LEAK_REDACTION_AUDIT_{DATE_TAG}.json"
    matrix_path = harness.ROUTE_DIR / f"{PREFIX}_NEGATIVE_FIXTURE_MATRIX_{DATE_TAG}.json"
    required_artifacts = [
        fixture_manifest_path,
        fixture_validation_path,
        leak_path,
        matrix_path,
        harness.ROUTE_DIR / f"{PREFIX}_RUNTIME_PARSER_HARNESS_CONTRACT_{DATE_TAG}.md",
        harness.ROUTE_DIR / f"{PREFIX}_FUTURE_ADAPTER_CONTRACT_{DATE_TAG}.md",
        harness.ROUTE_DIR / f"{PREFIX}_SATURATION_SELF_REDTEAM_LEDGER_{DATE_TAG}.json",
    ]
    for path in required_artifacts:
        fail(failures, path.exists(), f"missing_artifact:{rel(path)}")

    if fixture_manifest_path.exists():
        manifest = read_json(fixture_manifest_path)
        fail(failures, manifest.get("synthetic_only") is True, "fixture_manifest_not_synthetic_only")
        fail(failures, manifest.get("candidate_row_boundary_preserved") == 3014, "candidate_boundary_not_3014")
        fail(failures, manifest.get("capture_group_count") == 10, "fixture_manifest_group_count_not_10")
        fail(failures, manifest.get("fixture_case_count") == len(cases), "fixture_manifest_case_count_mismatch")
        for row in manifest.get("fixture_rows", []):
            fail(failures, (harness.REPO_ROOT / row["fixture_path"]).exists(), f"missing_fixture_file:{row['fixture_path']}")

    if fixture_validation_path.exists():
        validation = read_json(fixture_validation_path)
        fail(failures, validation.get("all_expected_validity_matched") is True, "fixture_validation_result_not_all_matched")
        fail(failures, validation.get("fixture_case_count") == len(cases), "fixture_validation_case_count_mismatch")

    for code_path in [
        harness.ROUTE_DIR / "runtime_harness_synthetic_only_2026_05_12.py",
        harness.ROUTE_DIR / "build_scid_capture_runtime_harness_synthetic_only_2026_05_12.py",
        harness.ROUTE_DIR / "verify_scid_capture_runtime_harness_synthetic_only_2026_05_12.py",
        harness.ROUTE_DIR / "test_scid_capture_runtime_harness_synthetic_only_2026_05_12.py",
    ]:
        fail(failures, not imports_production_src(code_path), f"production_src_import_detected:{rel(code_path)}")

    result = {
        "route_id": harness.ROUTE_ID,
        "ok": not failures,
        "failures": failures,
        "synthetic_only": True,
        "schema_group_count_verified": len(group_schemas),
        "candidate_row_boundary_verified": 3014,
        "fixture_case_count_verified": len(cases),
        "fixture_outcomes_verified": len(outcomes),
        "safe_flags_preserved_false": True,
        "forbidden_surfaces_opened": [],
    }
    out_path = harness.ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json"
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    verification = verify()
    print(json.dumps(verification, indent=2, sort_keys=True))
    raise SystemExit(0 if verification["ok"] else 1)
