from __future__ import annotations

import sys
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROUTE_DIR))

import build_scid_noapi_ready8_quarantined_target_result_packet_after_g0_gate_2026_05_13 as builder


def _rowset_row() -> dict:
    return {
        "rowset_row_id": "rowset-1",
        "row_hash": "row-hash",
        "card_id": "ADV-001",
        "packet_id": "packet",
        "science_domain": "adversarial_baselines_placebo_explanations",
        "mechanism_family": "session_only_matched_placebo",
        "candidate_input_row_id": "candidate-1",
        "candidate_input_row_hash": "candidate-hash",
        "duplicate_proxy_denominator_key": "dup-1",
        "baseline_duplicate_policy_id": "policy",
        "baseline_assignment_family": "session_only_matched_placebo",
        "baseline_assignment_seed": "seed",
        "baseline_control_bucket": "CONTROL_BUCKET_00",
        "matched_control_group_key": "matched",
        "partition_assignment": "SEALED_VALIDATION_CANDIDATE_DESIGN",
        "candidate_input_partition_assignment": "SOURCE_CONTROL_INPUT_PACKET_ONLY_NOT_VALIDATION",
        "symbol": "EURUSD",
        "canonical_economic_group": "EURUSD_FUTURES_6E_PROXY",
        "source_proxy_group": "EURUSD_FUTURES_6E_PROXY::6EM26-CME.scid",
        "source_group": "baseline_control_fields",
        "source_hash": "candidate-hash",
        "source_identifier": "artifact://candidate",
        "source_hash_policy": "STRICT_SHA256_REQUIRED",
        "source_observed_asof_utc": "2026-05-10T22:15:00.000Z",
        "entry_reference_time_utc": "2026-05-10T22:15:00.000Z",
        "decision_asof_utc": "2026-05-10T22:15:00.000Z",
        "session_bucket": "GLOBAL_OFF_SESSION_OR_TRANSITION",
        "time_of_day_bucket": "UTC_18_23",
        "utc_hour": 22,
        "source_coverage_quality_bucket": "PRIOR_96_PARTIAL_RECORD_PRESENT",
        "denominator_group_concentration_bucket": "DENOMINATOR_GROUP_SMALL_LT100",
        "prior_context_descriptor_buckets": {},
        "source_artifact_pointers": [
            {
                "artifact_role": "source_segment",
                "segment_records_sha256": "segment-sha",
                "source_file_name": "6EM26-CME.scid",
            }
        ],
    }


def _bar(end: str, close: float, high: float, low: float, bar_hash: str, *, segment_sha: str = "segment-sha") -> dict:
    end_dt = builder.parse_ts(end)
    start = builder.format_ts(end_dt - builder.timedelta(minutes=15))
    return {
        "canonical_economic_group": "EURUSD_FUTURES_6E_PROXY",
        "bar_end_exclusive_utc": end,
        "bar_start_utc": start,
        "bar_status": "CLOSED_SOURCE_RECORDS_PRESENT",
        "symbol": "EURUSD",
        "canonical_economic_group": "EURUSD_FUTURES_6E_PROXY",
        "close": close,
        "high": high,
        "low": low,
        "bar_hash": bar_hash,
        "segment_records_sha256": segment_sha,
        "source_file_name": "6EM26-CME.scid",
    }


def _bars() -> dict:
    rows = [
        _bar("2026-05-10T22:15:00.000Z", 1.1000, 9.9000, 1.0900, "entry-hash"),
        _bar("2026-05-10T22:30:00.000Z", 1.1015, 1.1020, 1.0990, "h1-hash"),
        _bar("2026-05-10T22:45:00.000Z", 1.1025, 1.1030, 1.1000, "h2-hash"),
        _bar("2026-05-10T23:00:00.000Z", 1.1040, 1.1060, 1.1010, "h3-hash"),
        _bar("2026-05-10T23:15:00.000Z", 1.1050, 1.1070, 1.1020, "h4-hash"),
    ]
    return {(row["symbol"], row["bar_end_exclusive_utc"]): row for row in rows}


def test_close_to_close_uses_entry_bar_close_and_horizon_close() -> None:
    row = builder.compute_target_result(
        _rowset_row(),
        "neutral_close_to_close_return_m15_horizons_v1",
        4,
        _bars(),
    )

    assert row["terminal_status"] == "COMPUTABLE"
    assert row["entry_close"] == 1.1
    assert row["horizon_close"] == 1.105
    assert row["close_to_close_absolute_delta"] == 0.005
    assert row["required_bar_end_utc"] == ["2026-05-10T22:15:00.000Z", "2026-05-10T23:15:00.000Z"]


def test_excursion_excludes_entry_bar_and_uses_forward_path_only() -> None:
    row = builder.compute_target_result(
        _rowset_row(),
        "neutral_high_low_excursion_m15_horizons_v1",
        4,
        _bars(),
    )

    assert row["terminal_status"] == "COMPUTABLE"
    assert row["max_high_over_horizon"] == 1.107
    assert row["min_low_over_horizon"] == 1.099
    assert row["upside_excursion_absolute"] == 0.007
    assert row["downside_excursion_absolute"] == 0.001


def test_missing_horizon_bar_fails_closed_without_inference() -> None:
    bars = _bars()
    bars.pop(("EURUSD", "2026-05-10T23:15:00.000Z"))

    row = builder.compute_target_result(
        _rowset_row(),
        "neutral_close_to_close_return_m15_horizons_v1",
        4,
        bars,
    )

    assert row["terminal_status"] == "FAIL_CLOSED_NOT_COMPUTABLE"
    assert row["fail_closed_primary_reason"] == "FAIL_CLOSED_HORIZON_BAR_MISSING"
    assert row["close_to_close_absolute_delta"] is None


def test_source_segment_mismatch_fails_closed() -> None:
    bars = _bars()
    bars[("EURUSD", "2026-05-10T22:30:00.000Z")]["segment_records_sha256"] = "different"

    row = builder.compute_target_result(
        _rowset_row(),
        "neutral_high_low_excursion_m15_horizons_v1",
        1,
        bars,
    )

    assert row["terminal_status"] == "FAIL_CLOSED_NOT_COMPUTABLE"
    assert row["fail_closed_primary_reason"] == "FAIL_CLOSED_PATH_SOURCE_HASH_MISMATCH"


def test_computed_row_has_no_forbidden_exact_fields_and_safe_flags_closed() -> None:
    row = builder.compute_target_result(
        _rowset_row(),
        "neutral_close_to_close_return_m15_horizons_v1",
        1,
        _bars(),
    )

    assert not (set(row) & builder.FORBIDDEN_EXACT_FIELDS)
    assert row["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert row["validation_safe"] is False
    assert row["live_effect"] is False
    assert row["opens_ai_api"] is False
