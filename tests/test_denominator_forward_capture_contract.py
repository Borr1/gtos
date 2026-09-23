from __future__ import annotations

import json

from src.components.denominator_forward_capture_contract import (
    DEFAULT_LOG_PATH,
    ENABLED_CONFIG_KEY,
    LOG_ENABLED_CONFIG_KEY,
    LOG_PATH_CONFIG_KEY,
    M15_GRID_ORDER_LIFECYCLE_FAMILY,
    M15_GRID_ORDER_LIFECYCLE_REQUIRED_FIELDS,
    PENDING_CREATED_DECISION_TIME_FAMILY,
    PENDING_CREATED_DECISION_TIME_REQUIRED_FIELDS,
    build_denominator_forward_capture_downstream_join_review,
    build_denominator_forward_capture_expansion_review,
    build_denominator_forward_capture_row_review,
    build_denominator_forward_capture_code_contract,
    record_denominator_forward_capture_event,
    summarize_denominator_forward_capture_log,
    summarize_denominator_forward_capture_rows,
    validate_denominator_forward_capture_event,
)


def test_code_contract_counts_current_denominator_capture_blockers() -> None:
    contract = build_denominator_forward_capture_code_contract(
        pending_created_capture_required_rows=449,
        m15_grid_capture_required_rows=250,
        generated_utc="2026-06-20T08:00:00Z",
    )

    assert contract["status"] == "default_off_capture_writer_ready_for_runtime_wiring"
    assert contract["total_capture_required_units"] == 699
    assert contract["total_required_capture_field_rows"] == (
        449 * len(PENDING_CREATED_DECISION_TIME_REQUIRED_FIELDS)
        + 250 * len(M15_GRID_ORDER_LIFECYCLE_REQUIRED_FIELDS)
    )
    assert contract["runtime_effect_now"] is False
    assert contract["historical_reconstruction_allowed"] is False
    assert contract["selected_package_denominator_use_allowed"] is False
    assert contract["final_package_selection_allowed"] is False
    assert contract["contract_hash_sha256"]


def test_m15_grid_event_validation_accepts_runtime_aliases() -> None:
    validation = validate_denominator_forward_capture_event(
        {
            "decision_time_utc": "2026-05-05T07:15:00Z",
            "candidate_id": "candidate-original",
            "decision_window_id": "GBPJPY:LONG:2026-05-05T07:15:00Z",
            "selected_candidate_id": "candidate-selected",
            "order_intent": "place_pending_limit",
            "order_type": "limit",
            "pending_ticket": "123456",
            "pending_lifecycle_v4_state": "order_send_success_filled",
            "fill_no_fill_label": "internal_filled_broker_ticket_known",
            "time_in_force": "GTC",
            "broker_account_namespace": "FTMO_DEMO",
            "source_event_hash_sha256": "a" * 64,
        },
        requirement_family=M15_GRID_ORDER_LIFECYCLE_FAMILY,
        generated_utc="2026-06-20T08:00:00Z",
    )

    assert validation["status"] == "capture_event_complete"
    assert validation["missing_capture_fields"] == []
    assert validation["candidate_id"] == "candidate-selected"
    assert validation["source_event_hash"] == "a" * 64
    assert validation["selected_package_denominator_use_allowed"] is False
    assert validation["packet_hash_sha256"]


def test_pending_created_validation_keeps_missing_decision_time_blocking() -> None:
    validation = validate_denominator_forward_capture_event(
        {
            "row_bound_candidate_id": "candidate-selected",
            "pending_created_time_utc": "2026-06-01T03:15:00Z",
            "order_intent": "place_pending_limit",
            "cancel_replace_or_time_in_force": "expiry_48h",
            "source_event_hash": "b" * 64,
        },
        requirement_family=PENDING_CREATED_DECISION_TIME_FAMILY,
        generated_utc="2026-06-20T08:00:00Z",
    )

    assert validation["status"] == "capture_event_missing_required_fields"
    assert validation["missing_capture_fields"] == ["decision_time_utc"]
    assert validation["required_capture_fields"] == list(PENDING_CREATED_DECISION_TIME_REQUIRED_FIELDS)
    assert validation["historical_reconstruction_allowed"] is False
    assert validation["final_package_selection_allowed"] is False


def test_code_contract_exposes_default_off_writer_metadata() -> None:
    contract = build_denominator_forward_capture_code_contract(
        pending_created_capture_required_rows=449,
        m15_grid_capture_required_rows=250,
        generated_utc="2026-06-20T08:00:00Z",
    )

    assert contract["status"] == "default_off_capture_writer_ready_for_runtime_wiring"
    assert contract["default_log_path"] == DEFAULT_LOG_PATH
    assert contract["runtime_config_keys"] == {
        "enabled": ENABLED_CONFIG_KEY,
        "log_enabled": LOG_ENABLED_CONFIG_KEY,
        "log_path": LOG_PATH_CONFIG_KEY,
    }
    assert contract["runtime_effect_now"] is False
    assert contract["live_execution_activation_allowed"] is False


def test_record_denominator_forward_capture_event_is_disabled_by_default(tmp_path) -> None:
    log_path = tmp_path / "denominator_forward_capture.jsonl"

    validation = record_denominator_forward_capture_event(
        {
            "decision_time_utc": "2026-06-01T03:15:00Z",
            "row_bound_candidate_id": "candidate-selected",
            "pending_created_time_utc": "2026-06-01T03:16:00Z",
            "order_intent": "place_pending_limit",
            "cancel_replace_or_time_in_force": "expiry_48h",
            "source_event_hash": "c" * 64,
        },
        requirement_family=PENDING_CREATED_DECISION_TIME_FAMILY,
        log_path=log_path,
        generated_utc="2026-06-20T08:00:00Z",
    )

    assert validation["status"] == "capture_event_complete"
    assert validation["append_status"] == "disabled_by_runtime_config"
    assert validation["capture_writer"]["default_log_path"] == DEFAULT_LOG_PATH
    assert not log_path.exists()


def test_record_denominator_forward_capture_event_appends_when_explicitly_enabled(tmp_path) -> None:
    log_path = tmp_path / "capture" / "denominator_forward_capture.jsonl"

    validation = record_denominator_forward_capture_event(
        {
            "decision_time_utc": "2026-05-05T07:15:00Z",
            "original_candidate_id": "candidate-original",
            "stable_decision_window_id": "GBPJPY:LONG:2026-05-05T07:15:00Z",
            "selected_candidate_id": "candidate-selected",
            "order_intent": "place_pending_limit",
            "order_type": "limit",
            "pending_ticket_or_order_ticket": "123456",
            "lifecycle_state": "order_send_success_filled",
            "fill_or_no_fill": "internal_filled_broker_ticket_known",
            "cancel_replace_or_time_in_force": "GTC",
            "broker_profile_namespace": "FTMO_DEMO",
            "source_event_hash": "d" * 64,
        },
        requirement_family=M15_GRID_ORDER_LIFECYCLE_FAMILY,
        runtime_config={
            ENABLED_CONFIG_KEY: True,
            LOG_ENABLED_CONFIG_KEY: True,
            LOG_PATH_CONFIG_KEY: str(log_path),
        },
        generated_utc="2026-06-20T08:00:00Z",
    )

    rows = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert validation["append_status"] == "appended"
    assert validation["capture_log_path"] == str(log_path)
    assert len(rows) == 1
    assert rows[0]["status"] == "capture_event_complete"
    assert rows[0]["append_status"] == "appended"
    assert rows[0]["candidate_id"] == "candidate-selected"
    assert rows[0]["selected_package_denominator_use_allowed"] is False


def test_record_denominator_forward_capture_event_logs_missing_required_fields(tmp_path) -> None:
    log_path = tmp_path / "denominator_forward_capture.jsonl"

    validation = record_denominator_forward_capture_event(
        {"row_bound_candidate_id": "candidate-selected"},
        requirement_family=PENDING_CREATED_DECISION_TIME_FAMILY,
        runtime_config={
            ENABLED_CONFIG_KEY: True,
            LOG_ENABLED_CONFIG_KEY: True,
        },
        log_path=log_path,
        generated_utc="2026-06-20T08:00:00Z",
    )

    row = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert validation["append_status"] == "appended"
    assert row["status"] == "capture_event_missing_required_fields"
    assert row["missing_capture_fields"] == [
        "decision_time_utc",
        "pending_created_time_utc",
        "order_intent",
        "cancel_replace_or_time_in_force",
        "source_event_hash",
    ]
    assert row["final_package_selection_allowed"] is False


def test_summarize_denominator_forward_capture_log_handles_missing_log(tmp_path) -> None:
    log_path = tmp_path / "missing" / "denominator_forward_capture.jsonl"

    summary = summarize_denominator_forward_capture_log(
        log_path,
        generated_utc="2026-06-20T08:00:00Z",
    )

    assert summary["status"] == "capture_log_missing_no_rows_currently_observed"
    assert summary["log_exists"] is False
    assert summary["total_rows"] == 0
    assert summary["complete_event_rows"] == 0
    assert summary["denominator_expansion_allowed"] is False
    assert summary["final_package_selection_allowed"] is False


def test_expansion_review_keeps_missing_capture_log_non_countable(tmp_path) -> None:
    log_path = tmp_path / "missing" / "denominator_forward_capture.jsonl"
    summary = summarize_denominator_forward_capture_log(
        log_path,
        generated_utc="2026-06-20T08:00:00Z",
    )

    review = build_denominator_forward_capture_expansion_review(
        summary,
        required_capture_units=699,
        required_capture_field_rows=5694,
        generated_utc="2026-06-20T08:00:00Z",
        ingestion_summary_path="DENOMINATOR_FORWARD_CAPTURE_LOG_INGESTION_SUMMARY.json",
    )

    assert review["status"] == "no_captured_rows_no_denominator_expansion"
    assert review["capture_log_total_rows"] == 0
    assert review["expansion_review_candidate_rows"] == 0
    assert review["remaining_required_capture_units_after_observed_complete_rows"] == 699
    assert review["review_blockers"] == ["capture_log_missing_no_rows", "no_complete_capture_rows"]
    assert review["denominator_expansion_allowed"] is False
    assert review["training_use_allowed"] is False
    assert review["final_package_selection_allowed"] is False


def test_summarize_denominator_forward_capture_log_counts_complete_missing_and_parse_rows(tmp_path) -> None:
    log_path = tmp_path / "capture" / "denominator_forward_capture.jsonl"
    config = {
        ENABLED_CONFIG_KEY: True,
        LOG_ENABLED_CONFIG_KEY: True,
        LOG_PATH_CONFIG_KEY: str(log_path),
    }

    record_denominator_forward_capture_event(
        {
            "decision_time_utc": "2026-05-05T07:15:00Z",
            "original_candidate_id": "candidate-original",
            "stable_decision_window_id": "GBPJPY:LONG:2026-05-05T07:15:00Z",
            "selected_candidate_id": "candidate-selected",
            "order_intent": "place_pending_limit",
            "order_type": "limit",
            "pending_ticket_or_order_ticket": "123456",
            "lifecycle_state": "order_send_success_filled",
            "fill_or_no_fill": "internal_filled_broker_ticket_known",
            "cancel_replace_or_time_in_force": "GTC",
            "broker_profile_namespace": "FTMO_DEMO",
            "source_event_hash": "e" * 64,
        },
        requirement_family=M15_GRID_ORDER_LIFECYCLE_FAMILY,
        runtime_config=config,
        generated_utc="2026-06-20T08:00:00Z",
    )
    record_denominator_forward_capture_event(
        {
            "row_bound_candidate_id": "candidate-pending",
            "pending_created_time_utc": "2026-06-01T03:16:00Z",
            "order_intent": "place_pending_limit",
            "cancel_replace_or_time_in_force": "expiry_48h",
            "source_event_hash": "f" * 64,
        },
        requirement_family=PENDING_CREATED_DECISION_TIME_FAMILY,
        runtime_config=config,
        generated_utc="2026-06-20T08:00:00Z",
    )
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write("{bad-json}\n")

    summary = summarize_denominator_forward_capture_log(
        log_path,
        generated_utc="2026-06-20T08:00:00Z",
    )

    assert summary["status"] == "capture_log_parse_errors_review_required"
    assert summary["log_exists"] is True
    assert summary["line_count"] == 3
    assert summary["total_rows"] == 2
    assert summary["jsonl_parse_error_count"] == 1
    assert summary["complete_event_rows"] == 1
    assert summary["missing_required_field_event_rows"] == 1
    assert summary["family_counts"] == {
        M15_GRID_ORDER_LIFECYCLE_FAMILY: 1,
        PENDING_CREATED_DECISION_TIME_FAMILY: 1,
    }
    assert summary["append_status_counts"] == {"appended": 2}
    assert summary["missing_capture_field_counts"] == {"decision_time_utc": 1}
    assert summary["capture_log_has_complete_rows"] is True
    assert summary["complete_rows_ready_for_denominator_expansion_review"] is True
    assert summary["denominator_expansion_allowed"] is False
    assert summary["training_use_allowed"] is False


def test_expansion_review_requires_rerun_for_complete_rows_without_opening_gates(tmp_path) -> None:
    log_path = tmp_path / "capture" / "denominator_forward_capture.jsonl"
    config = {
        ENABLED_CONFIG_KEY: True,
        LOG_ENABLED_CONFIG_KEY: True,
        LOG_PATH_CONFIG_KEY: str(log_path),
    }
    record_denominator_forward_capture_event(
        {
            "decision_time_utc": "2026-05-05T07:15:00Z",
            "original_candidate_id": "candidate-original",
            "stable_decision_window_id": "GBPJPY:LONG:2026-05-05T07:15:00Z",
            "selected_candidate_id": "candidate-selected",
            "order_intent": "place_pending_limit",
            "order_type": "limit",
            "pending_ticket_or_order_ticket": "123456",
            "lifecycle_state": "order_send_success_filled",
            "fill_or_no_fill": "internal_filled_broker_ticket_known",
            "cancel_replace_or_time_in_force": "GTC",
            "broker_profile_namespace": "FTMO_DEMO",
            "source_event_hash": "1" * 64,
        },
        requirement_family=M15_GRID_ORDER_LIFECYCLE_FAMILY,
        runtime_config=config,
        generated_utc="2026-06-20T08:00:00Z",
    )
    summary = summarize_denominator_forward_capture_log(
        log_path,
        generated_utc="2026-06-20T08:00:00Z",
    )

    review = build_denominator_forward_capture_expansion_review(
        summary,
        required_capture_units=699,
        required_capture_field_rows=5694,
        generated_utc="2026-06-20T08:00:00Z",
    )

    assert review["status"] == "complete_capture_rows_observed_denominator_expansion_rerun_required"
    assert review["expansion_review_candidate_rows"] == 1
    assert review["complete_rows_require_route_denominator_expansion_rerun"] is True
    assert review["review_blockers"] == []
    assert review["remaining_required_capture_units_after_observed_complete_rows"] == 698
    assert review["required_next_artifacts"] == [
        "row_level_capture_log_review_ledger",
        "source_event_hash_dedup_ledger",
        "captured_row_to_selected_package_candidate_join_ledger",
        "captured_row_to_lifecycle_label_join_ledger",
        "denominator_expansion_replay_or_verifier_result",
        "split_floor_recalculation_after_verified_expansion",
    ]
    assert review["denominator_expansion_allowed"] is False
    assert review["model_training_allowed"] is False
    assert review["deployment_dossier_allowed"] is False


def test_row_review_keeps_empty_capture_log_fail_closed(tmp_path) -> None:
    log_path = tmp_path / "missing" / "denominator_forward_capture.jsonl"
    ingestion = summarize_denominator_forward_capture_log(
        log_path,
        generated_utc="2026-06-20T08:00:00Z",
    )

    review = build_denominator_forward_capture_row_review(
        [],
        ingestion_summary=ingestion,
        required_capture_units=699,
        generated_utc="2026-06-20T08:00:00Z",
        log_path=log_path,
    )

    assert review["summary"]["status"] == "no_capture_rows_no_row_review_candidates"
    assert review["summary"]["row_review_ledger_rows"] == 0
    assert review["summary"]["row_review_candidate_rows"] == 0
    assert review["summary"]["source_event_hash_dedup_pass_rows"] == 0
    assert review["summary"]["captured_row_to_selected_package_candidate_join_ready_rows"] == 0
    assert review["summary"]["remaining_required_capture_units_after_row_review_passed"] == 699
    assert review["summary"]["review_blockers"] == ["no_capture_rows"]
    assert review["summary"]["denominator_expansion_allowed"] is False
    assert review["summary"]["final_package_selection_allowed"] is False
    assert review["ledger_rows"] == []


def test_row_review_blocks_duplicate_source_event_hashes() -> None:
    rows = [
        validate_denominator_forward_capture_event(
            {
                "decision_time_utc": "2026-05-05T07:15:00Z",
                "original_candidate_id": "candidate-original-a",
                "stable_decision_window_id": "GBPJPY:LONG:2026-05-05T07:15:00Z",
                "selected_candidate_id": "candidate-selected-a",
                "order_intent": "place_pending_limit",
                "order_type": "limit",
                "pending_ticket_or_order_ticket": "123456",
                "lifecycle_state": "order_send_success_filled",
                "fill_or_no_fill": "internal_filled_broker_ticket_known",
                "cancel_replace_or_time_in_force": "GTC",
                "broker_profile_namespace": "FTMO_DEMO",
                "source_event_hash": "2" * 64,
            },
            requirement_family=M15_GRID_ORDER_LIFECYCLE_FAMILY,
            generated_utc="2026-06-20T08:00:00Z",
        ),
        validate_denominator_forward_capture_event(
            {
                "decision_time_utc": "2026-05-05T07:16:00Z",
                "original_candidate_id": "candidate-original-b",
                "stable_decision_window_id": "GBPJPY:LONG:2026-05-05T07:16:00Z",
                "selected_candidate_id": "candidate-selected-b",
                "order_intent": "place_pending_limit",
                "order_type": "limit",
                "pending_ticket_or_order_ticket": "123457",
                "lifecycle_state": "order_send_success_filled",
                "fill_or_no_fill": "internal_filled_broker_ticket_known",
                "cancel_replace_or_time_in_force": "GTC",
                "broker_profile_namespace": "FTMO_DEMO",
                "source_event_hash": "2" * 64,
            },
            requirement_family=M15_GRID_ORDER_LIFECYCLE_FAMILY,
            generated_utc="2026-06-20T08:00:00Z",
        ),
    ]
    ingestion = summarize_denominator_forward_capture_rows(
        rows,
        generated_utc="2026-06-20T08:00:00Z",
    )

    review = build_denominator_forward_capture_row_review(
        rows,
        ingestion_summary=ingestion,
        required_capture_units=699,
        generated_utc="2026-06-20T08:00:00Z",
    )

    assert review["summary"]["status"] == "capture_rows_blocked_by_source_event_hash_duplicates"
    assert review["summary"]["source_event_hash_duplicate_key_count"] == 1
    assert review["summary"]["source_event_hash_duplicate_row_count"] == 2
    assert review["summary"]["source_event_hash_dedup_pass_rows"] == 0
    assert review["summary"]["row_review_candidate_rows"] == 0
    assert review["summary"]["denominator_expansion_allowed"] is False
    assert [row["review_status"] for row in review["ledger_rows"]] == [
        "duplicate_source_event_hash_blocked",
        "duplicate_source_event_hash_blocked",
    ]
    assert all(row["source_event_hash_dedup_passed"] is False for row in review["ledger_rows"])


def test_row_review_unique_complete_rows_still_require_downstream_joins() -> None:
    row = validate_denominator_forward_capture_event(
        {
            "decision_time_utc": "2026-05-05T07:15:00Z",
            "original_candidate_id": "candidate-original",
            "stable_decision_window_id": "GBPJPY:LONG:2026-05-05T07:15:00Z",
            "selected_candidate_id": "candidate-selected",
            "order_intent": "place_pending_limit",
            "order_type": "limit",
            "pending_ticket_or_order_ticket": "123456",
            "lifecycle_state": "order_send_success_filled",
            "fill_or_no_fill": "internal_filled_broker_ticket_known",
            "cancel_replace_or_time_in_force": "GTC",
            "broker_profile_namespace": "FTMO_DEMO",
            "source_event_hash": "3" * 64,
        },
        requirement_family=M15_GRID_ORDER_LIFECYCLE_FAMILY,
        generated_utc="2026-06-20T08:00:00Z",
    )
    ingestion = summarize_denominator_forward_capture_rows(
        [row],
        generated_utc="2026-06-20T08:00:00Z",
    )

    review = build_denominator_forward_capture_row_review(
        [row],
        ingestion_summary=ingestion,
        required_capture_units=699,
        generated_utc="2026-06-20T08:00:00Z",
    )

    assert review["summary"]["status"] == "captured_rows_require_downstream_join_review"
    assert review["summary"]["row_review_candidate_rows"] == 1
    assert review["summary"]["source_event_hash_dedup_pass_rows"] == 1
    assert review["summary"]["captured_row_to_selected_package_candidate_join_ready_rows"] == 1
    assert review["summary"]["captured_row_to_selected_package_candidate_join_rows"] == 0
    assert review["summary"]["captured_row_to_lifecycle_label_join_rows"] == 0
    assert review["summary"]["denominator_expansion_candidate_rows"] == 0
    assert review["summary"]["denominator_expansion_allowed"] is False
    assert review["summary"]["training_use_allowed"] is False
    assert review["ledger_rows"][0]["review_status"] == (
        "captured_row_requires_selected_package_and_lifecycle_joins"
    )
    assert review["ledger_rows"][0]["source_event_hash_dedup_passed"] is True
    assert review["ledger_rows"][0]["selected_package_denominator_use_allowed"] is False


def test_downstream_join_review_keeps_empty_row_review_fail_closed() -> None:
    review = build_denominator_forward_capture_downstream_join_review(
        [],
        selected_package_candidate_ids={"candidate-selected"},
        lifecycle_label_candidate_ids={"candidate-selected"},
        generated_utc="2026-06-20T08:00:00Z",
    )

    assert review["summary"]["status"] == "no_row_review_rows_no_downstream_join_candidates"
    assert review["summary"]["row_review_ledger_rows"] == 0
    assert review["summary"]["captured_row_to_selected_package_candidate_join_rows"] == 0
    assert review["summary"]["captured_row_to_lifecycle_label_join_rows"] == 0
    assert review["summary"]["denominator_expansion_candidate_rows"] == 0
    assert review["summary"]["review_blockers"] == [
        "no_row_review_rows",
        "no_row_review_candidates",
        "no_source_event_hash_dedup_pass_rows",
    ]
    assert review["summary"]["denominator_expansion_allowed"] is False
    assert review["selected_package_join_rows"] == []
    assert review["lifecycle_label_join_rows"] == []


def test_downstream_join_review_blocks_missing_selected_and_lifecycle_matches() -> None:
    row = validate_denominator_forward_capture_event(
        {
            "decision_time_utc": "2026-05-05T07:15:00Z",
            "original_candidate_id": "candidate-original",
            "stable_decision_window_id": "GBPJPY:LONG:2026-05-05T07:15:00Z",
            "selected_candidate_id": "candidate-selected",
            "order_intent": "place_pending_limit",
            "order_type": "limit",
            "pending_ticket_or_order_ticket": "123456",
            "lifecycle_state": "order_send_success_filled",
            "fill_or_no_fill": "internal_filled_broker_ticket_known",
            "cancel_replace_or_time_in_force": "GTC",
            "broker_profile_namespace": "FTMO_DEMO",
            "source_event_hash": "4" * 64,
        },
        requirement_family=M15_GRID_ORDER_LIFECYCLE_FAMILY,
        generated_utc="2026-06-20T08:00:00Z",
    )
    row_review = build_denominator_forward_capture_row_review(
        [row],
        ingestion_summary=summarize_denominator_forward_capture_rows(
            [row],
            generated_utc="2026-06-20T08:00:00Z",
        ),
        generated_utc="2026-06-20T08:00:00Z",
    )

    review = build_denominator_forward_capture_downstream_join_review(
        row_review["ledger_rows"],
        selected_package_candidate_ids={"different-candidate"},
        lifecycle_label_decision_window_ids={"different-window"},
        generated_utc="2026-06-20T08:00:00Z",
    )

    assert review["summary"]["status"] == "captured_rows_missing_downstream_joins"
    assert review["summary"]["row_review_candidate_rows"] == 1
    assert review["summary"]["source_event_hash_dedup_pass_rows"] == 1
    assert review["summary"]["captured_row_to_selected_package_candidate_join_rows"] == 0
    assert review["summary"]["captured_row_to_lifecycle_label_join_rows"] == 0
    assert review["summary"]["denominator_expansion_candidate_rows"] == 0
    assert review["selected_package_join_rows"][0]["join_status"] == (
        "selected_package_candidate_join_missing"
    )
    assert review["lifecycle_label_join_rows"][0]["join_status"] == "lifecycle_label_join_missing"
    assert review["summary"]["final_package_selection_allowed"] is False


def test_downstream_join_review_matching_rows_require_rerun_before_use() -> None:
    row = validate_denominator_forward_capture_event(
        {
            "decision_time_utc": "2026-05-05T07:15:00Z",
            "original_candidate_id": "candidate-original",
            "stable_decision_window_id": "GBPJPY:LONG:2026-05-05T07:15:00Z",
            "selected_candidate_id": "candidate-selected",
            "order_intent": "place_pending_limit",
            "order_type": "limit",
            "pending_ticket_or_order_ticket": "123456",
            "lifecycle_state": "order_send_success_filled",
            "fill_or_no_fill": "internal_filled_broker_ticket_known",
            "cancel_replace_or_time_in_force": "GTC",
            "broker_profile_namespace": "FTMO_DEMO",
            "source_event_hash": "5" * 64,
        },
        requirement_family=M15_GRID_ORDER_LIFECYCLE_FAMILY,
        generated_utc="2026-06-20T08:00:00Z",
    )
    row_review = build_denominator_forward_capture_row_review(
        [row],
        ingestion_summary=summarize_denominator_forward_capture_rows(
            [row],
            generated_utc="2026-06-20T08:00:00Z",
        ),
        generated_utc="2026-06-20T08:00:00Z",
    )

    review = build_denominator_forward_capture_downstream_join_review(
        row_review["ledger_rows"],
        selected_package_candidate_ids={"candidate-selected"},
        lifecycle_label_decision_window_ids={"GBPJPY:LONG:2026-05-05T07:15:00Z"},
        generated_utc="2026-06-20T08:00:00Z",
    )

    assert review["summary"]["status"] == "captured_rows_joined_denominator_expansion_rerun_required"
    assert review["summary"]["captured_row_to_selected_package_candidate_join_rows"] == 1
    assert review["summary"]["captured_row_to_lifecycle_label_join_rows"] == 1
    assert review["summary"]["denominator_expansion_candidate_rows"] == 1
    assert review["summary"]["review_blockers"] == [
        "denominator_expansion_rerun_not_built",
        "split_floor_recalculation_not_built",
    ]
    assert review["selected_package_join_rows"][0]["selected_package_candidate_joined"] is True
    assert review["lifecycle_label_join_rows"][0]["lifecycle_label_joined"] is True
    assert review["selected_package_join_rows"][0]["denominator_expansion_allowed"] is False
    assert review["lifecycle_label_join_rows"][0]["final_package_selection_allowed"] is False


def test_summarize_denominator_forward_capture_rows_rejects_unknown_family() -> None:
    summary = summarize_denominator_forward_capture_rows(
        [
            {
                "schema": "gtos.final_moonshot.denominator_forward_capture.event_validation.v1",
                "requirement_family": "unknown_family",
                "status": "capture_event_complete",
                "missing_capture_fields": [],
            }
        ],
        generated_utc="2026-06-20T08:00:00Z",
    )

    assert summary["total_rows"] == 1
    assert summary["valid_event_rows"] == 0
    assert summary["invalid_row_reason_counts"] == {"unknown_requirement_family": 1}
    assert summary["denominator_expansion_allowed"] is False
