from __future__ import annotations

import sys
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROUTE_DIR))

import build_g12_scid_ready8_disc_target_result_audit_2026_05_13 as audit


def _rowset_row() -> dict:
    return {
        "rowset_row_id": "rowset-1",
        "row_hash": "row-hash",
        "card_id": "ADV-001",
        "partition_assignment": "SEALED_VALIDATION_CANDIDATE_DESIGN",
        "symbol": "EURUSD",
        "source_observed_asof_utc": "2026-05-10T22:15:00.000Z",
        "decision_asof_utc": "2026-05-10T22:15:00.000Z",
        "entry_reference_time_utc": "2026-05-10T22:15:00.000Z",
        "source_artifact_pointers": [
            {
                "artifact_role": "source_segment",
                "segment_records_sha256": "segment-sha",
                "source_file_name": "6EM26-CME.scid",
            }
        ],
    }


def _bar(end: str, close: float, high: float, low: float, bar_hash: str) -> dict:
    return {
        "symbol": "EURUSD",
        "bar_end_exclusive_utc": end,
        "bar_status": "CLOSED_SOURCE_RECORDS_PRESENT",
        "close": close,
        "high": high,
        "low": low,
        "bar_hash": bar_hash,
        "segment_records_sha256": "segment-sha",
        "source_file_name": "6EM26-CME.scid",
    }


def _bars() -> dict:
    rows = [
        _bar("2026-05-10T22:15:00.000Z", 1.1000, 9.9000, 1.0900, "entry"),
        _bar("2026-05-10T22:30:00.000Z", 1.1015, 1.1020, 1.0990, "h1"),
        _bar("2026-05-10T22:45:00.000Z", 1.1025, 1.1030, 1.1000, "h2"),
        _bar("2026-05-10T23:00:00.000Z", 1.1040, 1.1060, 1.1010, "h3"),
        _bar("2026-05-10T23:15:00.000Z", 1.1050, 1.1070, 1.1020, "h4"),
    ]
    return {(row["symbol"], row["bar_end_exclusive_utc"]): row for row in rows}


def test_canonical_json_hash_is_stable() -> None:
    assert audit.sha256_json({"b": 1, "a": 2}) == audit.sha256_json({"a": 2, "b": 1})


def test_close_to_close_horizon_end_uses_exact_h_step() -> None:
    result = audit.expected_target_fields(
        _rowset_row(),
        "neutral_close_to_close_return_m15_horizons_v1",
        4,
        _bars(),
    )
    assert result["terminal_status"] == "COMPUTABLE"
    assert result["required_bar_end_utc"] == ["2026-05-10T22:15:00.000Z", "2026-05-10T23:15:00.000Z"]
    assert result["horizon_close"] == 1.105
    assert result["close_to_close_absolute_delta"] == 0.005


def test_high_low_uses_entry_for_close_but_excludes_entry_extreme() -> None:
    result = audit.expected_target_fields(
        _rowset_row(),
        "neutral_high_low_excursion_m15_horizons_v1",
        4,
        _bars(),
    )
    assert result["terminal_status"] == "COMPUTABLE"
    assert result["required_bar_end_utc"][0] == "2026-05-10T22:15:00.000Z"
    assert result["required_bar_end_utc"][-1] == "2026-05-10T23:15:00.000Z"
    assert result["max_high_over_horizon"] == 1.107
    assert result["min_low_over_horizon"] == 1.099


def test_missing_path_bar_fails_closed_without_inference() -> None:
    bars = _bars()
    bars.pop(("EURUSD", "2026-05-10T23:15:00.000Z"))
    result = audit.expected_target_fields(
        _rowset_row(),
        "neutral_high_low_excursion_m15_horizons_v1",
        4,
        bars,
    )
    assert result["terminal_status"] == "FAIL_CLOSED_NOT_COMPUTABLE"
    assert result["fail_closed_primary_reason"] == "FAIL_CLOSED_PATH_BAR_MISSING"


def test_forbidden_exact_scan_allows_safe_flags_but_blocks_performance_keys() -> None:
    assert "validation_safe" not in audit.FORBIDDEN_EXACT_FIELDS
    assert "outcome_review_opened" not in audit.FORBIDDEN_EXACT_FIELDS
    assert "win_rate" in audit.FORBIDDEN_EXACT_FIELDS
    assert "broker_actual_r" in audit.FORBIDDEN_EXACT_FIELDS

