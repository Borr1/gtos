"""Focused tests for the SCID strategy-field source expansion packet."""

from __future__ import annotations

import json

import build_scid_strategy_field_source_expansion_packet_2026_05_12 as builder
import verify_scid_strategy_field_source_expansion_packet_2026_05_12 as verifier


def _sample_descriptor(candidate_id: str = "candidate_input:TEST:2026-05-12T00:00:00.000Z") -> dict:
    return {
        "candidate_input_row_id": candidate_id,
        "canonical_economic_group": "TEST_GROUP",
        "denominator_group_concentration_bucket": "DENOMINATOR_GROUP_SMALL_LT100",
        "duplicate_proxy_denominator_key": "dup-key",
        "entry_reference_time_utc": "2026-05-12T00:00:00.000Z",
        "partition_assignment": "SEALED_VALIDATION_CANDIDATE_DESIGN",
        "prior_16_drift_bucket": "NOT_COMPUTABLE_DESCRIPTOR_BUCKET",
        "prior_16_range_bucket": "NOT_COMPUTABLE_DESCRIPTOR_BUCKET",
        "prior_32_range_bucket": "NOT_COMPUTABLE_DESCRIPTOR_BUCKET",
        "prior_windows": {"16": {"complete": False}, "32": {"complete": False}},
        "session_bucket": "GLOBAL_OFF_SESSION_OR_TRANSITION",
        "source_coverage_quality_bucket": "PRIOR_96_PARTIAL_RECORD_PRESENT",
        "source_file_name": "TEST.scid",
        "source_proxy_group": "TEST_GROUP::TEST.scid",
        "symbol": "TEST",
        "time_of_day_bucket": "UTC_00_05",
        "utc_hour": 0,
    }


def _sample_candidate(candidate_id: str = "candidate_input:TEST:2026-05-12T00:00:00.000Z") -> dict:
    return {
        "candidate_input_row_id": candidate_id,
        "candidate_family_id": "scid_asof_m15_source_control_input",
        "canonical_economic_group": "TEST_GROUP",
        "decision_asof_utc": "2026-05-12T00:00:00.000Z",
        "duplicate_key": "candidate-dup-key",
        "duplicate_key_fields": {
            "candidate_family_id": "scid_asof_m15_source_control_input",
            "canonical_economic_group": "TEST_GROUP",
            "decision_asof_utc": "2026-05-12T00:00:00.000Z",
            "entry_reference_time_utc": "2026-05-12T00:00:00.000Z",
            "side": "SIDE_NEUTRAL_SOURCE_CONTROL_INPUT",
            "source_partition_id": "SCID_ASOF_ACCEPTED_9_SEGMENT_SOURCE_CONTROL",
        },
        "interval": "M15",
        "source_file_name": "TEST.scid",
        "symbol": "TEST",
    }


def test_closure_row_uses_exact_status_enum_and_hashes() -> None:
    rows = builder.build_closure_rows([_sample_descriptor()], [_sample_candidate()])
    assert len(rows) == 1
    row = rows[0]
    assert set(row["field_statuses"]) == set(builder.FIELD_FAMILIES)
    assert {payload["status"] for payload in row["field_statuses"].values()} <= builder.FIELD_STATUS_ENUM
    rehashed = dict(row)
    rehashed.pop("field_closure_row_hash")
    assert row["field_closure_row_hash"] == builder.stable_hash(rehashed)
    assert row["field_statuses"]["intended_side_direction"]["status"] == "FAIL_CLOSED_MISSING_SOURCE_FIELD"
    assert row["field_statuses"]["lower_timeframe_asof_path_availability"]["status"] == "PROSPECTIVE_CAPTURE_REQUIRED"
    assert row["field_statuses"]["broker_account_order_history_deal_position_evidence"]["status"] == "FORBIDDEN_IN_THIS_EVIDENCE_CLASS"


def test_future_requirements_are_exact_enough_for_g12() -> None:
    required = {
        "future_source_or_logger",
        "required_fields",
        "parser_requirement",
        "schema_version_required",
        "redaction_rule",
        "as_of_rule",
        "g12_acceptance_requirement",
    }
    for family in [
        "intended_side_direction",
        "intended_entry_reference",
        "intended_stop_reference",
        "intended_target_reference",
        "poi_type_bounds_source",
        "framework_setup_family",
        "lifecycle_fill_cancel_expiry_source_status",
    ]:
        assert required <= set(builder.make_missing_requirement(family))
    for family in [
        "lower_timeframe_asof_path_availability",
        "future_orderflow_depth_proxy_requirements",
    ]:
        assert required <= set(builder.make_prospective_requirement(family))


def test_built_packet_verifies_after_builder_run() -> None:
    assert builder.OUTPUTS["closure_rows_jsonl"].exists(), "run builder before focused tests"
    result = verifier.verify()
    assert result["ok"], json.dumps(result["issues"], indent=2)
    assert result["candidate_rows_verified"] == 3014
    assert result["unique_candidate_ids_verified"] == 3014


def test_closure_rows_do_not_expose_forbidden_result_keys() -> None:
    rows = verifier.load_jsonl(builder.OUTPUTS["closure_rows_jsonl"])
    assert rows
    keys = verifier.walk_keys(rows)
    assert not (keys & builder.FORBIDDEN_RESULT_KEYS)
