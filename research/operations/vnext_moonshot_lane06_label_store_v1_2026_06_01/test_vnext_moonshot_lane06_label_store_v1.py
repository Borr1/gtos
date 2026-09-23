from __future__ import annotations

import gzip
import json
from pathlib import Path

from build_vnext_moonshot_lane06_label_store_v1 import (
    DEPENDENCY_STATE_LEDGER,
    DOWNSTREAM_CONTRACT,
    LANE05_DIR,
    LANE07_DIR,
    LABEL_FAMILY_COVERAGE_LEDGER,
    LABEL_SCHEMA,
    LABEL_VECTOR_LEDGER,
    MISSING_LABEL_GAP_LEDGER,
    NO_LEAK_LEDGER,
    RUNTIME_EFFECT_BOUNDARY,
    derive_timeline_label_vector,
    label_schema_payload,
)


def test_label_derivation_uses_event_order_for_sl_before_1r() -> None:
    row = {
        "row_id": "unit_trade",
        "candidate_id": "unit_candidate",
        "symbol": "XAUUSD",
        "framework": "ob_retest",
        "origin_family": "liquidity_sweep_reclaim",
        "side": "LONG",
        "source_time_utc": "2026-05-01T10:00:00+00:00",
        "entry_time_utc": "2026-05-01T10:00:10+00:00",
        "exit_time_utc": "2026-05-01T10:15:00+00:00",
        "final_r": -1.0,
        "mfe_r": 2.0,
        "mae_r": -1.2,
        "chosen_policy": "partial_be_runner",
        "fill_status": "entry_filled",
        "path_class": "loss_sl_before_partial_trigger",
        "ordered_path_status": "ordered_tick_bid_ask_path",
        "ordered_events": [
            {"event_type": "entry_touch", "time_utc": "2026-05-01T10:00:10+00:00"},
            {"event_type": "sl_touch", "time_utc": "2026-05-01T10:02:00+00:00"},
            {"event_type": "one_r_trigger", "time_utc": "2026-05-01T10:05:00+00:00"},
        ],
    }
    vector = derive_timeline_label_vector(row, {}, {}, Path("unit_source.jsonl"))
    assert vector["label_values"]["sl_before_1r"] is True
    assert vector["label_values"]["one_r_reached"] is False
    assert vector["label_values"]["partial_then_be"] is False
    assert vector["runtime_effect_boundary"] == RUNTIME_EFFECT_BOUNDARY


def test_label_derivation_keeps_broker_net_r_separate_from_proxy_r() -> None:
    row = {
        "row_id": "unit_trade",
        "candidate_id": "unit_candidate",
        "trade_id": "unit_trade",
        "symbol": "XAUUSD",
        "framework": "ob_retest",
        "origin_family": "liquidity_sweep_reclaim",
        "side": "LONG",
        "source_time_utc": "2026-05-01T10:00:00+00:00",
        "entry_time_utc": "2026-05-01T10:00:10+00:00",
        "exit_time_utc": "2026-05-01T10:15:00+00:00",
        "final_r": 1.25,
        "mfe_r": 1.5,
        "mae_r": -0.1,
        "chosen_policy": "momentum_exhaustion",
        "fill_status": "filled_in_replay",
        "ordered_events": [{"event_type": "one_r_trigger", "time_utc": "2026-05-01T10:06:00+00:00"}],
    }
    supplements = {
        ("candidate_id", "unit_candidate"): {
            "broker_real_net_r": 1.03,
            "broker_lifecycle_status": "FULLY_CLOSED_BROKER_HISTORY",
        }
    }
    vector = derive_timeline_label_vector(row, supplements, {}, Path("unit_source.jsonl"))
    assert vector["label_values"]["source_bound_proxy_r"] == 1.25
    assert vector["label_values"]["broker_real_net_r"] == 1.03
    assert "broker_real_truth" in vector["evidence_class"]


def test_schema_declares_required_downstream_label_families() -> None:
    schema = label_schema_payload("2026-06-01T00:00:00+00:00")
    families = set(schema["label_families"])
    assert {
        "sl_before_1r",
        "one_r_reached",
        "partial_then_be",
        "partial_then_final",
        "final_target_reached",
        "broker_real_net_r",
        "source_bound_proxy_r",
        "stale_blocker",
        "correct_rejection",
        "missed_opportunity",
    }.issubset(families)
    assert schema["label_authority_order"] == ["broker_real_truth", "strict_tick_projection", "m15_proxy_replay"]


def test_materialized_artifacts_have_core_rows_when_builder_has_run() -> None:
    assert LABEL_SCHEMA.exists()
    assert LABEL_VECTOR_LEDGER.exists()
    assert MISSING_LABEL_GAP_LEDGER.exists()
    assert LABEL_FAMILY_COVERAGE_LEDGER.exists()

    schema = json.loads(LABEL_SCHEMA.read_text(encoding="utf-8"))
    assert "broker_real_net_r" in schema["label_families"]

    with gzip.open(LABEL_VECTOR_LEDGER, "rt", encoding="utf-8") as handle:
        first = json.loads(next(line for line in handle if line.strip()))
    assert first["no_leak_status"] == "label_only_excluded_from_feature_rows"
    assert "sl_before_1r" in first["label_values"]
    assert "feature_value" not in first

    opener = gzip.open if MISSING_LABEL_GAP_LEDGER.suffix == ".gz" else open
    with opener(MISSING_LABEL_GAP_LEDGER, "rt", encoding="utf-8") as handle:
        first_gap = json.loads(next(line for line in handle if line.strip()))
    assert first_gap["canonical_candidate_id"]
    assert first_gap["repair_requirement_code"]

    coverage = [
        json.loads(line)
        for line in LABEL_FAMILY_COVERAGE_LEDGER.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    by_family = {row["label_family"]: row for row in coverage}
    assert by_family["sl_before_1r"]["available_rows"] > 0
    assert by_family["source_bound_proxy_r"]["available_rows"] > 0


def test_lane05_and_lane07_present_contracts_are_consumed_when_available() -> None:
    deps = [
        json.loads(line)
        for line in DEPENDENCY_STATE_LEDGER.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    by_name = {row["dependency_name"]: row for row in deps}
    if LANE05_DIR.exists():
        assert by_name["lane05_feature_store_contract"]["dependency_state"] == "present_consumed_for_label_join_no_leak_contract"
    if LANE07_DIR.exists():
        assert by_name["lane07_broker_truth_cost_calibration"]["dependency_state"] == "present_consumed_for_broker_truth_cost_labels_where_joinable"

    no_leak = [
        json.loads(line)
        for line in NO_LEAK_LEDGER.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    checks = {row["check_id"]: row for row in no_leak}
    assert checks["lane05_feature_store_present_or_absent_state_recorded"]["status"] == "pass"
    assert checks["lane05_feature_schema_has_no_label_family_columns"]["status"] == "pass"
    assert checks["lane05_label_join_after_split_contract_present"]["status"] == "pass"
    assert checks["lane07_broker_truth_contract_label_store_join_only"]["status"] == "pass"

    downstream = json.loads(DOWNSTREAM_CONTRACT.read_text(encoding="utf-8"))
    if LANE05_DIR.exists():
        assert downstream["feature_store"]["lane05_state"] == "present_consumed_for_label_join_no_leak_contract"
    if LANE07_DIR.exists():
        assert "broker_truth_cost_contract" in json.dumps(downstream)
