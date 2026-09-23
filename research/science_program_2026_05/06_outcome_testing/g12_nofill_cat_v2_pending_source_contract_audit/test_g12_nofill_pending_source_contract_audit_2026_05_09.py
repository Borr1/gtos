from __future__ import annotations

import json

from build_g12_nofill_pending_source_contract_audit_2026_05_09 import (
    DECISION,
    DUPLICATE_CONTROL,
    EXPECTED_ACCEPTED_SPLIT,
    EXPECTED_DUPLICATE_POSTURE,
    EXPECTED_LABEL_COUNTS,
    EXPECTED_PARTITION,
    PROMOTION_VERDICT,
    REQUIRED_FIELD_FAMILIES,
    ROUTE_DIR,
    ROW_LEDGER,
    SOURCE_SCHEMA_FIELDS,
    build_duplicate_review,
    build_schema_field_review,
    read_json,
    read_jsonl,
    recompute_counts,
    required_output_files,
    validate_duplicate_denominator_record,
)


def test_recomputes_frozen_partition_and_label_counts() -> None:
    counts = recompute_counts(read_jsonl(ROW_LEDGER))

    assert counts["partition"] == EXPECTED_PARTITION
    assert counts["accepted_split"] == EXPECTED_ACCEPTED_SPLIT
    assert counts["accepted_label_counts"] == EXPECTED_LABEL_COUNTS
    assert counts["duplicate_posture"] == EXPECTED_DUPLICATE_POSTURE


def test_blocked_and_rejected_rows_have_no_label_denominator_or_safe_flags() -> None:
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


def test_schema_review_covers_all_46_fields_and_families() -> None:
    counts = recompute_counts(read_jsonl(ROW_LEDGER))
    review = build_schema_field_review(read_json(SOURCE_SCHEMA_FIELDS), counts)

    assert review["status"] == "PASS"
    assert review["field_count"] == 46
    assert not review["missing_required_families"]
    assert set(REQUIRED_FIELD_FAMILIES).issubset(set(review["family_counts"]))
    assert not review["forbidden_schema_field_names"]
    assert len(review["field_reviews"]) == 46
    assert all(item["status"] == "PASS" for item in review["field_reviews"])


def test_duplicate_validator_rejects_missing_and_generated_identity() -> None:
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
    missing = dict(valid)
    missing.pop("duplicate_group_id")
    assert "missing_duplicate_group_id" in validate_duplicate_denominator_record(missing)
    generated = dict(valid)
    generated["nofill_duplicate_key"] = "GENERATED_FALLBACK|UNKNOWN"
    assert "generated_or_fallback_nofill_duplicate_key" in validate_duplicate_denominator_record(generated)


def test_duplicate_review_executes_control_invalid_examples() -> None:
    counts = recompute_counts(read_jsonl(ROW_LEDGER))
    review = build_duplicate_review(read_json(DUPLICATE_CONTROL), counts)

    assert review["status"] == "PASS"
    assert review["duplicate_posture"] == EXPECTED_DUPLICATE_POSTURE
    assert review["invalid_case_results"]
    assert all(item["status"] == "PASS" for item in review["invalid_case_results"])


def test_generated_artifacts_parse_and_preserve_false_safety_flags() -> None:
    json_names = [name for name in required_output_files() if name.endswith(".json")]

    assert json_names
    for name in json_names:
        data = json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))
        assert data["promotion_verdict"] == PROMOTION_VERDICT
        assert data["validation_safe"] is False
        assert data["outcome_review_opened"] is False
        assert data["live_effect"] is False


def test_decision_accepts_only_future_source_control_routing() -> None:
    decision = json.loads(
        (ROUTE_DIR / "G12_NOFILL_PENDING_SOURCE_CONTRACT_DECISION_LEDGER_2026-05-09.json").read_text(
            encoding="utf-8"
        )
    )

    assert decision["decision"] == DECISION
    assert decision["decision_scope"] == "future_source_control_routing_only"
    assert decision["opens_result_scoring"] is False
    assert decision["changes_live_trading_behavior"] is False
    closed = [
        item
        for item in decision["route_decisions"]
        if item["route"] == "NOFILL_CAT_V2_QUANTITATIVE_RESULT_LANE"
        and item["decision"] == "REJECT_FOR_THIS_LANE_AND_KEEP_CLOSED"
    ]
    assert closed


def test_markdown_artifacts_contain_no_promotion_verdict() -> None:
    markdown_names = [name for name in required_output_files() if name.endswith(".md")]

    assert markdown_names
    for name in markdown_names:
        assert PROMOTION_VERDICT in (ROUTE_DIR / name).read_text(encoding="utf-8")
