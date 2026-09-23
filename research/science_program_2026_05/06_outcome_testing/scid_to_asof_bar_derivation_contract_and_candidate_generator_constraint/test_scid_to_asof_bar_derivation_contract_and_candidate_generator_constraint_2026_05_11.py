from __future__ import annotations

import json
import sys
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROUTE_DIR))

import build_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_2026_05_11 as builder


def test_left_closed_right_open_excludes_record_at_decision_asof() -> None:
    base_us = builder.sierra_us_from_iso("2026-05-04T13:00:00.000Z")
    records = [
        {
            "source_record_index": 1,
            "source_timestamp_us": base_us,
            "open": 10,
            "high": 11,
            "low": 9,
            "close": 10.5,
            "num_trades": 1,
            "total_volume": 10,
            "bid_volume": 4,
            "ask_volume": 6,
        },
        {
            "source_record_index": 2,
            "source_timestamp_us": base_us + 60_000_000,
            "open": 99,
            "high": 100,
            "low": 98,
            "close": 99.5,
            "num_trades": 1,
            "total_volume": 99,
            "bid_volume": 40,
            "ask_volume": 59,
        },
    ]

    result = builder.derive_fixture_bars(records, interval_seconds=60, decision_asof_us=base_us + 60_000_000)

    assert len(result["bars"]) == 1
    assert result["bars"][0]["open"] == 10
    assert result["bars"][0]["close"] == 10.5
    assert result["diagnostics"]["records_before_decision_asof"] == 1


def test_empty_bars_are_fail_closed_without_fabricated_ohlc() -> None:
    base_us = builder.sierra_us_from_iso("2026-05-04T13:00:00.000Z")
    records = [
        {
            "source_record_index": 1,
            "source_timestamp_us": base_us,
            "open": 10,
            "high": 11,
            "low": 9,
            "close": 10.5,
            "num_trades": 1,
            "total_volume": 10,
            "bid_volume": 4,
            "ask_volume": 6,
        },
        {
            "source_record_index": 2,
            "source_timestamp_us": base_us + 120_000_000,
            "open": 12,
            "high": 13,
            "low": 11,
            "close": 12.5,
            "num_trades": 1,
            "total_volume": 20,
            "bid_volume": 8,
            "ask_volume": 12,
        },
    ]

    result = builder.derive_fixture_bars(
        records,
        interval_seconds=60,
        decision_asof_us=base_us + 180_000_000,
        include_empty=True,
    )

    empty = [bar for bar in result["bars"] if bar["bar_status"] == "EMPTY_NO_SOURCE_RECORDS"]
    assert len(empty) == 1
    assert empty[0]["open"] is None
    assert empty[0]["high"] is None
    assert empty[0]["total_volume"] == 0
    assert empty[0]["candidate_eligible"] is False


def test_duplicate_timestamp_and_same_millisecond_use_raw_us_and_record_index() -> None:
    base_us = builder.sierra_us_from_iso("2026-05-04T13:00:00.000Z")
    records = [
        {
            "source_record_index": 3,
            "source_timestamp_us": base_us + 500,
            "open": 12,
            "high": 12,
            "low": 12,
            "close": 12,
            "num_trades": 1,
            "total_volume": 30,
            "bid_volume": 10,
            "ask_volume": 20,
        },
        {
            "source_record_index": 2,
            "source_timestamp_us": base_us + 500,
            "open": 11,
            "high": 11,
            "low": 11,
            "close": 11,
            "num_trades": 1,
            "total_volume": 20,
            "bid_volume": 9,
            "ask_volume": 11,
        },
        {
            "source_record_index": 1,
            "source_timestamp_us": base_us,
            "open": 10,
            "high": 10,
            "low": 10,
            "close": 10,
            "num_trades": 1,
            "total_volume": 10,
            "bid_volume": 4,
            "ask_volume": 6,
        },
    ]

    result = builder.derive_fixture_bars(records, interval_seconds=60, decision_asof_us=base_us + 60_000_000)

    bar = result["bars"][0]
    assert bar["open"] == 10
    assert bar["close"] == 12
    assert bar["total_volume"] == 60
    assert result["diagnostics"]["same_timestamp_group_count"] == 1
    assert result["diagnostics"]["sorted_pair_order"] == [
        (base_us, 1),
        (base_us + 500, 2),
        (base_us + 500, 3),
    ]


def test_non_monotonic_source_order_is_flagged_but_sorted_for_contract_fixture() -> None:
    base_us = builder.sierra_us_from_iso("2026-05-04T13:00:00.000Z")
    records = [
        {
            "source_record_index": 2,
            "source_timestamp_us": base_us + 5_000_000,
            "open": 20,
            "high": 20,
            "low": 20,
            "close": 20,
            "num_trades": 1,
            "total_volume": 20,
            "bid_volume": 10,
            "ask_volume": 10,
        },
        {
            "source_record_index": 1,
            "source_timestamp_us": base_us,
            "open": 10,
            "high": 10,
            "low": 10,
            "close": 10,
            "num_trades": 1,
            "total_volume": 10,
            "bid_volume": 5,
            "ask_volume": 5,
        },
    ]

    result = builder.derive_fixture_bars(records, interval_seconds=60, decision_asof_us=base_us + 60_000_000)

    assert result["diagnostics"]["source_order_violation_count"] == 1
    assert result["bars"][0]["open"] == 10
    assert result["bars"][0]["close"] == 20


def test_artifact_contract_preserves_required_baselines_and_forbidden_fields_after_build() -> None:
    builder.build_all()
    baseline_path = ROUTE_DIR / f"SCID_ASOF_DISCOVERY_EXCLUSION_AND_BASELINE_PRESERVATION_AUDIT_{builder.DATE_TAG}.json"
    forbidden_path = ROUTE_DIR / f"SCID_ASOF_FORBIDDEN_FIELD_LEDGER_{builder.DATE_TAG}.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    forbidden = json.loads(forbidden_path.read_text(encoding="utf-8"))

    assert baseline["selected_discovery_source_count"] == 365
    assert baseline["baseline_ids"] == builder.EXPECTED_BASELINES
    assert baseline["summary"]["checks_pass"] is True
    patterns = {entry["pattern"] for entry in forbidden["entries"]}
    assert "broker_actual_r" in patterns
    assert "path_label" in patterns
    assert "future_" in patterns
