"""Focused tests for the SCID forward-capture offline schema package."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
BUILDER_PATH = HERE / "build_scid_forward_capture_offline_schema_implementation_package_2026_05_12.py"
VERIFY_PATH = HERE / "verify_scid_forward_capture_offline_schema_implementation_package_2026_05_12.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load_module("scid_forward_capture_builder_for_tests", BUILDER_PATH)
verifier = load_module("scid_forward_capture_verifier_for_tests", VERIFY_PATH)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_all_ten_capture_groups_have_schema_and_common_required_fields():
    ledger = load_json(builder.output_path("FIELD_GROUP_SCHEMA_LEDGER", "json"))
    assert ledger["group_schema_count"] == 10
    assert ledger["total_schema_file_count"] == 11
    assert sorted(row["field_group"] for row in ledger["field_groups"]) == sorted(builder.FIELD_GROUPS)
    assert ledger["candidate_rows_coverage_expectation"] == 3014
    assert ledger["duplicate_proxy_denominator_key_coverage_expectation"] == 3014

    for group in builder.FIELD_GROUPS:
        schema_path = builder.SCHEMA_DIR / f"{builder.SCHEMA_VERSION}_{group}.schema.json"
        schema = load_json(schema_path)
        assert schema["additionalProperties"] is False
        assert set(builder.COMMON_FIELD_NAMES).issubset(set(schema["required"]))
        assert schema["x_scid_contract"]["field_group"] == group
        assert "no_leak_rule" in schema["x_scid_contract"]


def test_fixture_manifest_covers_required_pass_and_fail_closed_cases():
    manifest = load_json(builder.output_path("FIXTURE_MANIFEST", "json"))
    categories = {row["category"] for row in manifest["fixtures"]}
    assert {
        "valid_pass",
        "missing_field_fail_closed",
        "ltf_unavailable",
        "orderflow_proxy_unavailable",
        "forbidden_broker_identifier",
        "stale_asof_violation",
        "duplicate_denominator_consistency",
        "manifest_binding_repair_continuity",
    }.issubset(categories)
    assert set(manifest["field_groups_with_missing_fixture"]) == set(builder.FIELD_GROUPS)


def test_fixture_validator_observes_expected_pass_fail_behavior():
    manifest = load_json(builder.output_path("FIXTURE_MANIFEST", "json"))
    result = builder.validate_fixtures(manifest)
    assert result["all_expected_behavior_observed"] is True
    assert result["failure_count"] == 0

    by_id = {row["fixture_id"]: row for row in result["fixture_results"]}
    assert by_id["fully_populated_synthetic_source_safe_rowset"]["observed_valid"] is True
    assert by_id["ltf_unavailable_fail_closed_valid"]["observed_valid"] is True
    assert by_id["orderflow_proxy_unavailable_fail_closed_valid"]["observed_valid"] is True
    assert by_id["forbidden_broker_identifier_fail_closed"]["observed_valid"] is False
    assert by_id["stale_asof_violation_fail_closed"]["observed_valid"] is False
    assert by_id["duplicate_denominator_consistency_valid"]["observed_valid"] is True
    assert by_id["duplicate_denominator_mismatch_fail_closed"]["observed_valid"] is False
    assert by_id["manifest_binding_repair_continuity"]["observed_valid"] is True


def test_validator_rejects_missing_required_for_each_capture_group():
    manifest = load_json(builder.output_path("FIXTURE_MANIFEST", "json"))
    result = builder.validate_fixtures(manifest)
    missing_rows = [row for row in result["fixture_results"] if row["category"] == "missing_field_fail_closed"]
    assert len(missing_rows) == len(builder.FIELD_GROUPS)
    for row in missing_rows:
        assert row["observed_valid"] is False
        assert any(error.startswith("missing_required:") for error in row["errors"])


def test_unavailable_market_context_rows_are_valid_only_as_fail_closed():
    ltf_row = load_json(builder.FIXTURE_DIR / "ltf_unavailable_fail_closed_valid.json")
    orderflow_row = load_json(builder.FIXTURE_DIR / "orderflow_proxy_unavailable_fail_closed_valid.json")
    assert builder.validate_dataset([ltf_row]) == []
    assert builder.validate_dataset([orderflow_row]) == []
    assert ltf_row["field_status"] == "SOURCE_UNAVAILABLE_FAIL_CLOSED"
    assert ltf_row["source_hash_policy"] == "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED"
    assert orderflow_row["field_status"] == "SOURCE_UNAVAILABLE_FAIL_CLOSED"
    assert orderflow_row["source_hash_policy"] == "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED"


def test_forbidden_stale_and_duplicate_mismatch_rows_fail_closed():
    forbidden = load_json(builder.FIXTURE_DIR / "forbidden_broker_identifier_fail_closed.json")
    stale = load_json(builder.FIXTURE_DIR / "stale_asof_violation_fail_closed.json")
    duplicate_mismatch = builder.load_fixture_rows(builder.FIXTURE_DIR / "duplicate_denominator_mismatch_fail_closed.jsonl")

    assert any(error.startswith("unexpected_keys:") or error.startswith("forbidden_key:") for error in builder.validate_dataset([forbidden]))
    assert "asof_violation:source_observed_after_decision" in builder.validate_dataset([stale])
    assert any(error.startswith("duplicate_key_mismatch:") for error in builder.validate_dataset(duplicate_mismatch))


def test_manifest_repair_policy_is_strict_except_documented_repairs():
    fixture = load_json(builder.FIXTURE_DIR / "manifest_binding_repair_continuity.json")
    assert builder.manifest_repair_fixture_valid(fixture) == []

    policy = load_json(builder.output_path("MANIFEST_HASH_POLICY_LEDGER", "json"))
    assert policy["repair_policy"]["current_g12_prompt_hash_supersedes_stale_pre_hardening_hash"] is True
    assert policy["repair_policy"]["builder_output_manifest_self_hash_is_non_blocking"] is True
    assert policy["repair_policy"]["all_other_source_input_hash_mismatches_are_strict_blockers"] is True
    assert policy["blocking_unrepaired_hash_mismatches"] == []


def test_read_only_monitoring_alignment_covers_all_groups_without_wiring():
    alignment = load_json(builder.output_path("READ_ONLY_MONITORING_ALIGNMENT_LEDGER", "json"))
    assert alignment["read_only_alignment_only"] is True
    assert alignment["live_wiring_added"] is False
    assert alignment["producer_files_modified"] == []
    assert alignment["missing_alignment_groups"] == []
    assert alignment["alignment_target_count"] >= 10
    assert all(row["producer_modified"] is False for row in alignment["alignment_targets"])
    assert all(row["running_process_altered"] is False for row in alignment["alignment_targets"])
    assert all(row["raw_values_copied"] is False for row in alignment["alignment_targets"])


def test_verifier_passes_package_checks():
    result = verifier.verify()
    assert result["ok"] is True
    assert result["failed_check_count"] == 0
    assert result["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert result["validation_safe"] is False
    assert result["outcome_review_opened"] is False
    assert result["live_effect"] is False
