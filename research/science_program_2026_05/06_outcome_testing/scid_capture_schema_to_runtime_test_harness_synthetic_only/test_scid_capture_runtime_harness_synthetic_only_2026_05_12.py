import json
from pathlib import Path

import runtime_harness_synthetic_only_2026_05_12 as harness


def test_accepted_schema_bundle_has_ten_groups_and_master():
    schemas = harness.load_accepted_schemas()
    assert "__master__" in schemas
    assert sorted(group for group in schemas if group != "__master__") == sorted(harness.CAPTURE_GROUPS)
    assert len([group for group in schemas if group != "__master__"]) == 10


def test_positive_rows_validate_for_all_groups():
    schemas = harness.load_accepted_schemas()
    for group in harness.CAPTURE_GROUPS:
        assert harness.validate_row(harness.positive_row(group, "base"), schemas) == []
        assert harness.validate_row(harness.positive_row(group, "variant"), schemas) == []


def test_fixture_matrix_matches_expected_validity():
    cases = harness.build_fixture_cases()
    outcomes = harness.validate_fixture_cases(cases)
    assert len(cases) >= 90
    assert all(outcome.pass_status for outcome in outcomes), [
        outcome.to_dict() for outcome in outcomes if not outcome.pass_status
    ]


def test_unavailable_source_policy_is_market_context_only():
    cases = [case for case in harness.build_fixture_cases() if case.category == "unavailable_source"]
    assert len(cases) == 10
    for case in cases:
        outcome = harness.validate_fixture_case(case)
        assert outcome.pass_status, outcome.to_dict()
        if case.field_group in harness.MARKET_CONTEXT_UNAVAILABLE_GROUPS:
            assert case.expected_valid is True
            assert case.fail_closed_semantics is True
        else:
            assert case.expected_valid is False
            assert case.inapplicable_reason


def test_duplicate_key_drift_fails_dataset_validation():
    case = next(
        case
        for case in harness.build_fixture_cases()
        if case.category == "duplicate_key_drift" and case.field_group == "intended_side_direction"
    )
    outcome = harness.validate_fixture_case(case)
    assert outcome.expected_valid is False
    assert outcome.observed_valid is False
    assert any("duplicate_key_drift" in error for error in outcome.errors)


def test_recursive_forbidden_identifier_is_caught():
    row = harness.positive_row("intended_entry_reference", "forbidden_nested")
    row["safe_nested_payload"] = {"broker_order_id": "ORDER-SYNTHETIC-FORBIDDEN"}
    errors = harness.validate_dataset([row])
    assert any("unexpected_keys" in error for error in errors)
    assert any("forbidden_key" in error for error in errors)
    assert any("forbidden_value_marker" in error for error in errors)


def test_manifest_binding_repair_contract_valid_and_invalid_routes():
    valid_payload = harness.build_manifest_repair_payload(valid=True)
    invalid_payload = harness.build_manifest_repair_payload(valid=False)
    assert harness.manifest_repair_valid(valid_payload)[0] is True
    invalid_ok, invalid_errors = harness.manifest_repair_valid(invalid_payload)
    assert invalid_ok is False
    assert any("all_other_source_and_input_hash_mismatches_are_strict_blockers" in error for error in invalid_errors)


def test_leak_audit_keeps_expected_valid_rows_clean():
    audit = harness.leak_redaction_audit(harness.build_fixture_cases())
    assert audit["accepted_rows_clean"] is True
    assert audit["deliberate_negative_hit_count"] == 10


def test_generated_fixture_manifest_if_builder_has_run():
    manifest_path = harness.ROUTE_DIR / f"{harness.ARTIFACT_PREFIX}_FIXTURE_MANIFEST_2026-05-12.json"
    if not manifest_path.exists():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["synthetic_only"] is True
    assert manifest["candidate_row_boundary_preserved"] == 3014
    assert manifest["capture_group_count"] == 10
    for row in manifest["fixture_rows"]:
        assert (harness.REPO_ROOT / Path(row["fixture_path"])).exists()
