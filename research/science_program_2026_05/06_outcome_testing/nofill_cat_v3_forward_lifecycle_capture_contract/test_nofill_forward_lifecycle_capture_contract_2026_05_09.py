from __future__ import annotations

import json

from build_nofill_forward_lifecycle_capture_contract_2026_05_09 import (
    FIELD_FAMILIES,
    FORBIDDEN_SOURCE_FIELD_NAMES,
    PROMOTION_VERDICT,
    REQUIRED_FIELD_NAMES,
    ROUTE_DIR,
    SOURCE_CONTROL_ROWS,
    SOURCE_IMPOSSIBLE_ROWS,
    contract_fields,
    contract_json,
    duplicate_policy_json,
    no_leak_policy_json,
    required_output_files,
    safety_flags,
    schema_json,
)


def test_contract_preserves_no_promotion_and_frozen_counts() -> None:
    contract = contract_json()

    assert contract["route_id"] == "NOFILL_CAT_V3_FORWARD_LIFECYCLE_CAPTURE_CONTRACT"
    assert contract["promotion_verdict"] == PROMOTION_VERDICT
    assert contract["validation_safe"] is False
    assert contract["outcome_review_opened"] is False
    assert contract["live_effect"] is False
    assert contract["opens_result_scoring"] is False
    assert contract["changes_live_trading_behavior"] is False
    assert contract["controlling_counts"]["universe_rows"] == 298
    assert contract["controlling_counts"]["accepted_row_level_inputs"] == 225
    assert contract["controlling_counts"]["accepted_unique_nofill_duplicate_keys"] == 182
    assert contract["controlling_counts"]["accepted_secondary_duplicate_group_ids"] == 139
    assert contract["controlling_counts"]["source_control_rows"] == SOURCE_CONTROL_ROWS
    assert contract["controlling_counts"]["source_impossible_rows"] == SOURCE_IMPOSSIBLE_ROWS


def test_schema_covers_required_fields_families_and_metadata() -> None:
    schema = schema_json()
    fields = schema["contract_fields"]
    field_names = {field["field_name"] for field in fields}
    families = {field["field_family"] for field in fields}
    required_metadata = {
        "field_name",
        "field_family",
        "required_or_optional",
        "allowed_source_types",
        "as_of_rule",
        "hash_requirement",
        "no_leak_role",
        "forbidden_substitute_fields",
        "capture_mode",
        "verification_rule",
    }

    assert set(REQUIRED_FIELD_NAMES).issubset(field_names)
    assert set(FIELD_FAMILIES).issubset(families)
    assert not (field_names & FORBIDDEN_SOURCE_FIELD_NAMES)
    for field in fields:
        assert required_metadata.issubset(field)
        assert field["capture_mode"] == "forward_source_capture_only"
        assert "account_history" in field["forbidden_substitute_fields"]


def test_no_leak_policy_closes_result_and_live_flags() -> None:
    policy = no_leak_policy_json()

    for flag, expected in safety_flags().items():
        assert policy[flag] == expected
    assert policy["closed_states"]["future_result_label_status"] == "NOT_OPENED"
    assert policy["closed_states"]["broker_actual_r_status"] == "FORBIDDEN"
    assert policy["closed_states"]["hidden_path_label_status"] == "FORBIDDEN"
    assert policy["closed_states"]["live_account_order_label_status"] == "FORBIDDEN"
    assert policy["closed_states"]["validation_safe"] is False
    assert policy["closed_states"]["outcome_review_opened"] is False
    assert policy["closed_states"]["live_effect"] is False


def test_duplicate_policy_enforces_accepted_first_and_exclusions() -> None:
    policy = duplicate_policy_json()
    rendered = json.dumps(policy, sort_keys=True)

    assert policy["denominators"]["row_level_accepted_inputs"] == 225
    assert policy["denominators"]["unique_nofill_duplicate_key"] == 182
    assert policy["denominators"]["secondary_duplicate_group_id"] == 139
    assert "accepted_input_only" in rendered
    assert "reject-overlap" in rendered
    assert "source-control" in rendered
    assert "source-impossible" in rendered
    assert "canonical_row_id" in policy["required_fields"]


def test_required_output_files_have_expected_names() -> None:
    names = required_output_files()

    assert "NOFILL_FORWARD_CAPTURE_CONTRACT_2026-05-09.json" in names
    assert "NOFILL_FORWARD_SOURCE_FIELD_SCHEMA_2026-05-09.json" in names
    assert "NOFILL_FORWARD_NEXT_PROMPT_PACK_2026-05-09.md" in names
    assert "NOFILL_FORWARD_COMPLETION_AUDIT_2026-05-09.json" in names


def test_generated_artifacts_parse_after_builder_has_run() -> None:
    json_names = [name for name in required_output_files() if name.endswith(".json")]
    existing = [name for name in json_names if (ROUTE_DIR / name).exists()]
    if not existing:
        return

    for name in existing:
        data = json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))
        assert data["promotion_verdict"] == PROMOTION_VERDICT
        assert data["validation_safe"] is False
        assert data["outcome_review_opened"] is False
        assert data["live_effect"] is False


def test_contract_fields_builder_matches_schema_length() -> None:
    assert len(contract_fields()) == len(REQUIRED_FIELD_NAMES)
