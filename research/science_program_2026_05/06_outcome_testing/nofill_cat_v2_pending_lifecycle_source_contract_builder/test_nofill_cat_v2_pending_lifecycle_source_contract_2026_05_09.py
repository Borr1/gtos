from __future__ import annotations

import json

from build_nofill_cat_v2_pending_lifecycle_source_contract_2026_05_09 import (
    DUPLICATE_CONTROL_REQUIRED_FIELDS,
    EXPECTED_ACCEPTED_SPLIT,
    EXPECTED_DUPLICATE_POSTURE,
    EXPECTED_LABEL_COUNTS,
    EXPECTED_PARTITION,
    FORBIDDEN_DECISION_TIME_FIELD_NAMES,
    PROMOTION_VERDICT,
    REQUIRED_FIELD_FAMILIES,
    ROUTE_DIR,
    ROW_LEDGER,
    contract_fields,
    read_jsonl,
    recompute_counts,
    required_output_files,
    validate_duplicate_denominator_record,
)


def test_recompute_counts_preserves_frozen_partition_and_labels() -> None:
    counts = recompute_counts(read_jsonl(ROW_LEDGER))

    assert counts["partition"] == EXPECTED_PARTITION
    assert counts["accepted_split"] == EXPECTED_ACCEPTED_SPLIT
    assert counts["accepted_label_counts"] == dict(sorted(EXPECTED_LABEL_COUNTS.items()))
    assert counts["duplicate_posture"]["accepted_row_level_source_inputs"] == 225
    assert counts["duplicate_posture"]["accepted_unique_nofill_duplicate_keys"] == 182
    assert counts["duplicate_posture"]["oti5_noncanonical_duplicate_projections_rejected"] == 39


def test_blockers_and_rejects_remain_outside_labels_and_denominators() -> None:
    counts = recompute_counts(read_jsonl(ROW_LEDGER))

    assert len(counts["blocked_rows"]) == 8
    assert len(counts["rejected_rows"]) == 65
    for row in counts["blocked_rows"] + counts["rejected_rows"]:
        assert row["categorical_input_label"] is None
        assert row["categorical_lifecycle_label"] is None
        assert row["in_accepted_packet_denominator"] is False
        assert row["validation_safe"] is False
        assert row["outcome_review_opened"] is False
        assert row["live_effect"] is False


def test_contract_fields_cover_required_families_and_metadata() -> None:
    fields = contract_fields()
    families = {field["field_family"] for field in fields}
    required_metadata = {
        "field_name",
        "field_family",
        "source_timing",
        "as_of_rule",
        "allowed_source_types",
        "required_or_optional",
        "no_leak_role",
        "forbidden_substitute_fields",
        "hash_requirements",
        "duplicate_denominator_role",
        "capture_availability",
    }

    assert set(REQUIRED_FIELD_FAMILIES).issubset(families)
    for field in fields:
        assert required_metadata.issubset(field)
    assert not ({field["field_name"] for field in fields} & FORBIDDEN_DECISION_TIME_FIELD_NAMES)


def test_duplicate_denominator_validator_rejects_missing_and_generated_controls() -> None:
    valid = {
        "row_level_denominator_scope": "accepted_input_only_rows_225",
        "unique_key_denominator_scope": "accepted_unique_nofill_duplicate_keys_182",
        "nofill_duplicate_key": "OTI5_G6_CUSUM|OTG0-PKT-063|XAGUSD|2026-05-04|london|SHORT|LONG",
        "duplicate_group_id": "G6_EXHAUSTION|XAGUSD|2026-05-04|london|SHORT|LONG",
        "canonical_counting_row_id": "NOFILL-CAT-ROW-0001",
        "is_canonical_counting_row": True,
        "noncanonical_projection_exclusion_policy": "REJECT_NONCANONICAL_PROJECTIONS_BEFORE_LABEL_OR_DENOMINATOR",
    }

    assert validate_duplicate_denominator_record(valid) == []
    for field in DUPLICATE_CONTROL_REQUIRED_FIELDS:
        invalid = dict(valid)
        invalid.pop(field)
        assert validate_duplicate_denominator_record(invalid)
    generated = dict(valid)
    generated["nofill_duplicate_key"] = "GENERATED_FALLBACK|UNKNOWN"
    assert "generated_or_fallback_nofill_duplicate_key" in validate_duplicate_denominator_record(generated)


def test_generated_json_artifacts_parse_and_preserve_safety_flags() -> None:
    json_names = [name for name in required_output_files() if name.endswith(".json")]

    assert json_names
    for name in json_names:
        data = json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))
        assert data["promotion_verdict"] == PROMOTION_VERDICT
        assert data["validation_safe"] is False
        assert data["outcome_review_opened"] is False
        assert data["live_effect"] is False


def test_required_markdown_artifacts_preserve_no_promotion_verdict() -> None:
    markdown_names = [name for name in required_output_files() if name.endswith(".md")]

    assert markdown_names
    for name in markdown_names:
        assert PROMOTION_VERDICT in (ROUTE_DIR / name).read_text(encoding="utf-8")


def test_duplicate_control_artifact_matches_expected_posture() -> None:
    path = ROUTE_DIR / "NOFILL_CAT_V2_DUPLICATE_DENOMINATOR_VERIFIER_CONTROL_2026-05-09.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["duplicate_posture"] == EXPECTED_DUPLICATE_POSTURE
    assert set(DUPLICATE_CONTROL_REQUIRED_FIELDS).issubset(set(data["required_fields"]))
    assert data["valid_example_errors"] == []
    for item in data["invalid_examples"]:
        assert item["expected_errors"], item["case_id"]
