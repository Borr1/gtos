"""Focused tests for SCID read-only monitoring alignment expansion."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
BUILDER_PATH = HERE / "build_scid_forward_capture_readonly_monitoring_alignment_expansion_2026_05_12.py"
SPEC = importlib.util.spec_from_file_location("scid_readonly_alignment_builder", BUILDER_PATH)
assert SPEC is not None and SPEC.loader is not None
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def load_json(stem: str) -> dict:
    return json.loads(builder.output_path(stem, "json").read_text(encoding="utf-8"))


def test_collect_key_paths_is_shape_only_and_does_not_copy_values() -> None:
    payload = {
        "candidate_input_row_id": "SECRET_VALUE_SHOULD_NOT_APPEAR_AS_KEY",
        "nested": {"entry_reference_price": 123.45, "broker_order_id": "ORDER-123"},
        "_status_throttle|2026-05-04T07:15:00+00:00|123456": {"side": "LONG"},
        "rows": [{"ltf_timeframes_available": ["M1", "M5"]}],
    }
    keys = builder.collect_key_paths(payload)
    assert "candidate_input_row_id" in keys
    assert "nested.entry_reference_price" in keys
    assert "nested.broker_order_id" in keys
    assert "SECRET_VALUE_SHOULD_NOT_APPEAR_AS_KEY" not in keys
    assert "ORDER-123" not in keys
    assert "_status_throttle|<timestamp>|<number>" in keys
    assert all("2026-05-04T07:15:00" not in key for key in keys)


def test_forbidden_key_detection_marks_broker_and_performance_shapes() -> None:
    assert "broker_account_order_deal_position" in builder.forbidden_categories_for_key("nested.broker_order_id")
    assert "broker_account_order_deal_position" in builder.forbidden_categories_for_key("account.balance")
    assert "result_performance_outcome" in builder.forbidden_categories_for_key("summary.realized_r")
    assert "result_performance_outcome" in builder.forbidden_categories_for_key("terminal_target_status")
    assert builder.forbidden_categories_for_key("source_hash") == []


def test_group_matching_covers_representative_safe_shapes() -> None:
    keys = {
        "strategy_side",
        "entry_reference_price",
        "stop_reference_price",
        "target_reference_price",
        "poi_lower_bound",
        "frameworks_evaluated",
        "pending_intent_id",
        "ltf_timeframes_available",
        "proxy_instrument",
        "baseline_assignment_seed",
        "broker_order_id",
    }
    matches = builder.match_groups(keys)
    assert sorted(matches) == sorted(builder.CAPTURE_GROUPS)
    assert all("broker_order_id" not in item for group in matches.values() for item in group["matched_key_examples"])


def test_excluded_file_policy_blocks_raw_and_result_validation_families() -> None:
    assert builder.excluded_file_reason(Path("data/ticks/XAUUSD/example.parquet"), "data") == "raw_market_blob_or_archive_suffix_excluded"
    assert (
        builder.excluded_file_reason(
            Path("research/science_program_2026_05/06_outcome_testing/scid_asof_sealed_validation_execution_packet/a.json"),
            "current_scid_source_control_route_artifacts",
        )
        == "validation_result_or_neutral_target_route_excluded"
    )
    assert (
        builder.excluded_file_reason(
            Path("shadow_logs/account_truth_reconciliation_status.jsonl"),
            "shadow_logs_shape_only_non_forbidden_families",
        )
        == "shadow_log_forbidden_broker_account_result_performance_family_excluded"
    )


def test_generated_artifacts_cover_prompt_completion_standard() -> None:
    coverage = load_json("FIELD_GROUP_COVERAGE_GAP_MATRIX")
    searched = load_json("SEARCHED_ROOT_LEDGER")
    forbidden = load_json("FORBIDDEN_FIELD_KEY_SHAPE_EXCLUSION_LEDGER")
    fingerprints = load_json("SHAPE_FINGERPRINT_HASH_MANIFEST")
    gates = load_json("SOURCE_CAPTURE_APPROVAL_GATE_LEDGER")

    assert coverage["capture_group_count"] == 10
    assert sorted(row["field_group"] for row in coverage["coverage_rows"]) == sorted(builder.CAPTURE_GROUPS)
    assert searched["parsed_shape_file_count"] > 12
    assert any(
        row["root_path"].startswith("C:/tmp/gtos_otb/") or row["root_path"].startswith("C:/Users/MSI/Documents/ai-trading-agent")
        for row in searched["searched_roots"]
        if row["files_parsed_for_shape"] > 0
    )
    assert forbidden["forbidden_file_exclusion_count"] > 0
    assert fingerprints["shape_fingerprint_count"] > 12
    assert len(gates["gate_rows"]) == 10
    assert all(not row["historical_truth_inference_allowed"] for row in gates["gate_rows"])
