from __future__ import annotations

from datetime import timedelta

import build_scid_asof_bar_builder_and_candidate_input_packet_source_control_2026_05_11 as builder


def test_forbidden_scanner_repairs_bar_window_overmatch() -> None:
    patterns = builder.forbidden_patterns()

    assert builder.forbidden_matches_for_name("bar_window_start_utc", patterns) == []
    assert builder.forbidden_matches_for_name("bar_window_end_utc", patterns) == []

    forbidden_terms = [
        "win_rate",
        "winning_trade",
        "loss",
        "pnl",
        "expectancy",
        "slippage",
        "broker_order",
        "deal",
        "position",
        "path_label",
        "result",
    ]
    for term in forbidden_terms:
        assert builder.forbidden_matches_for_name(term, patterns), term


def test_hard_floor_segment_bounds_and_decision_asof_fixture() -> None:
    records, segment, decision = builder.synthetic_fixture_records()
    bars, stats = builder.aggregate_records_to_dense_bars(records, segment, "FIXTURE_GROUP", decision)

    assert stats["rejected_before_hard_floor_count"] == 1
    assert stats["rejected_before_segment_count"] == 1
    assert stats["rejected_after_segment_count"] == 1
    assert stats["excluded_exactly_at_decision_asof_count"] == 1
    assert stats["excluded_at_or_after_decision_asof_count"] == 2
    assert all(row["bar_end_exclusive_utc"] <= builder.iso_ms(decision) for row in bars)

    first_present = next(row for row in bars if row["bar_status"] == "CLOSED_SOURCE_RECORDS_PRESENT")
    hard_floor_us = builder.datetime_to_sierra_us(
        builder.parse_time(segment["eligible_segment_start_utc_hard_floor"])
    )
    assert first_present["source_timestamp_min_us"] == hard_floor_us


def test_duplicate_same_ms_and_non_monotonic_source_order_are_handled() -> None:
    records, segment, decision = builder.synthetic_fixture_records()
    bars, stats = builder.aggregate_records_to_dense_bars(records, segment, "FIXTURE_GROUP", decision)

    assert stats["same_millisecond_record_count"] >= 1
    assert stats["same_timestamp_duplicate_record_count"] >= 1
    assert stats["source_order_violation_count"] >= 1

    first_present = next(row for row in bars if row["bar_status"] == "CLOSED_SOURCE_RECORDS_PRESENT")
    assert first_present["open"] == 100.0
    assert first_present["close"] == 101.1
    assert first_present["high"] == 102.2
    assert first_present["source_record_count"] == 3


def test_empty_gap_bars_fail_closed_without_synthetic_ohlc() -> None:
    records, segment, decision = builder.synthetic_fixture_records()
    bars, _stats = builder.aggregate_records_to_dense_bars(records, segment, "FIXTURE_GROUP", decision)
    empty_rows = [row for row in bars if row["bar_status"] != "CLOSED_SOURCE_RECORDS_PRESENT"]

    assert empty_rows
    assert all(row["candidate_eligible"] is False for row in empty_rows)
    assert all(row["open"] is None and row["high"] is None and row["low"] is None for row in empty_rows)
    assert all(row["total_volume"] == 0 and row["source_record_count"] == 0 for row in empty_rows)


def test_candidate_input_row_is_input_only_and_forbidden_scan_clean() -> None:
    records, segment, decision = builder.synthetic_fixture_records()
    bars, _stats = builder.aggregate_records_to_dense_bars(records, segment, "FIXTURE_GROUP", decision)
    primary = {"FIXTURE_GROUP": "FIXTURE"}
    rows, summary = builder.build_candidate_rows(bars, primary)

    assert rows
    assert summary["all_rows_input_only"] is True
    assert summary["all_forbidden_scans_pass"] is True
    assert rows[0]["candidate_input_only_status"] == "CANDIDATE_GENERATOR_INPUT_ONLY_NOT_VALIDATION"
    assert rows[0]["bar_window_start_utc"]
    assert rows[0]["bar_window_end_utc"]
    assert "row_hash" in rows[0]


def test_partial_after_decision_is_not_materialized_as_candidate_input() -> None:
    records, segment, decision = builder.synthetic_fixture_records()
    partial_time = decision + timedelta(minutes=1)
    partial_us = builder.datetime_to_sierra_us(partial_time)
    bars, _stats = builder.aggregate_records_to_dense_bars(records, segment, "FIXTURE_GROUP", decision)

    assert all(row["source_timestamp_max_us"] != partial_us for row in bars)
