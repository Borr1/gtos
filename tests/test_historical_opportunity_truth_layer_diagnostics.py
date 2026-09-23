import json
import shutil
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts.analyze_historical_opportunity_truth_layer import (
    analyze_truth_layer,
    compute_no_entry_path_metric,
    compute_sl_path_metric,
    render_report,
)


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"historical_opportunity_truth_layer_diagnostics_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_no_entry_metric_measures_nearest_approach_without_offset_sweep():
    row = _truth_row(
        truth_outcome="NO_ENTRY",
        mechanical_entry=100.0,
        mechanical_sl=99.0,
        mechanical_side="LONG",
        m1_horizon_bars=3,
    )
    rows = _future_rows(
        lows=[100.6, 100.2, 100.4],
        highs=[101.0, 100.9, 100.8],
    )

    metric = compute_no_entry_path_metric(row, rows=rows, timeframe="M1")

    assert metric["path_available"] is True
    assert metric["closest_distance_r"] == pytest.approx(0.2)
    assert metric["entry_proximity_of_sl_distance"] == pytest.approx(0.8)
    assert metric["bars_until_nearest"] == 2
    assert metric["fill_touched_in_path"] is False


def test_sl_metric_uses_pre_stop_mfe_and_counts_fill_to_stop_bars():
    row = _truth_row(
        truth_outcome="SL",
        truth_bars_in_trade=3,
        mechanical_entry=100.0,
        mechanical_sl=99.0,
        mechanical_side="LONG",
        m1_horizon_bars=4,
    )
    rows = _future_rows(
        lows=[100.2, 99.8, 98.9, 98.7],
        highs=[100.3, 100.6, 101.4, 101.5],
    )

    metric = compute_sl_path_metric(row, rows=rows, timeframe="M1")

    assert metric["path_available"] is True
    assert metric["fill_bar_index"] == 2
    assert metric["stop_bar_index"] == 3
    assert metric["bars_fill_to_stop"] == 2
    assert metric["mfe_before_stop_r"] == pytest.approx(0.6)


def test_analyze_truth_layer_ranks_positive_high_confidence_cohort_and_disagreements(tmp_path):
    path = tmp_path / "truth.jsonl"
    rows = [
        _truth_row(
            opportunity_key="XAUUSD|1",
            truth_outcome="TP",
            truth_realized_r=1.5,
            truth_failure_bucket="SUCCESS_TP_FIRST",
            m1_refined_outcome="TP",
            m5_refined_outcome="TP",
        ),
        _truth_row(
            opportunity_key="XAUUSD|2",
            truth_outcome="SL",
            truth_realized_r=-1.0,
            truth_failure_bucket="FAIL_STOP_FIRST",
            m1_refined_outcome="SL",
            m5_refined_outcome="TP",
        ),
        _truth_row(
            opportunity_key="XAUUSD|3",
            truth_outcome="NO_ENTRY",
            truth_realized_r=None,
            truth_failure_bucket="FAIL_NO_FILL",
            m1_refined_outcome="NO_ENTRY",
            m5_refined_outcome="NO_ENTRY",
        ),
        _truth_row(
            opportunity_key="XAUUSD|4",
            truth_outcome="PRE_SCREEN_REJECT",
            truth_realized_r=None,
            truth_failure_bucket="SETUP_MISSING_OR_LOW_QUALITY_POI",
            truth_confidence="NONE",
            truth_source_timeframe="NONE",
            would_send_ai=False,
            mechanical_setup_status="NOT_EVALUATED",
            m1_refinement_attempted=False,
            m1_local_coverage=False,
            m1_refined_outcome=None,
            m5_refinement_attempted=False,
            m5_local_coverage=False,
            m5_refined_outcome=None,
        ),
    ]
    _write_jsonl(path, rows)

    summary = analyze_truth_layer(
        input_path=path,
        data_dirs=[],
        compute_path_metrics=False,
        min_candidate_resolved_n=1,
        min_candidate_confidence_rows=1,
    )

    assert summary["rows"] == 4
    assert summary["ai_attempted_rows"] == 0
    assert summary["ai_call_count_sum"] == 0
    assert summary["m1_m5_disagreement"]["comparable_rows"] == 3
    assert summary["m1_m5_disagreement"]["disagreement_rows"] == 1
    assert summary["research_candidates_high_confidence"][0]["symbol_session_regime"] == (
        "XAUUSD|ny|bullish|H4+H1_consensus"
    )
    assert summary["research_candidates_high_confidence"][0]["mean_r"] == pytest.approx(0.25)
    failure_rows = summary["top_failure_buckets_by_symbol_session_regime"]
    no_fill = next(
        row
        for row in failure_rows
        if row["truth_failure_bucket"] == "FAIL_NO_FILL"
    )
    setup_reject = next(
        row
        for row in failure_rows
        if row["truth_failure_bucket"] == "SETUP_MISSING_OR_LOW_QUALITY_POI"
    )
    assert no_fill["bucket_share_of_setup"] == pytest.approx(1 / 3)
    assert setup_reject["bucket_share_of_setup"] is None


def test_report_states_research_boundary_not_optimization(tmp_path):
    path = tmp_path / "truth.jsonl"
    _write_jsonl(path, [_truth_row()])
    summary = analyze_truth_layer(
        input_path=path,
        data_dirs=[],
        compute_path_metrics=False,
        min_candidate_resolved_n=1,
        min_candidate_confidence_rows=1,
    )

    report = render_report(summary)

    assert "No AI/API calls are made" in report
    assert "No looser-entry or buffer simulation is included" in report
    assert "parameter optimization" in report


def _truth_row(**overrides):
    row = {
        "opportunity_key": "XAUUSD|2026-01-01T00:00:00+00:00",
        "symbol": "XAUUSD",
        "session": "ny",
        "year": "2026",
        "candle_close_utc": "2026-01-01T00:00:00+00:00",
        "truth_regime": "bullish|H4+H1_consensus",
        "truth_outcome": "TP",
        "truth_realized_r": 1.5,
        "truth_failure_bucket": "SUCCESS_TP_FIRST",
        "truth_confidence": "HIGH",
        "truth_source_timeframe": "M1",
        "truth_bars_in_trade": 2,
        "would_send_ai": True,
        "mechanical_setup_status": "OK",
        "mechanical_side": "LONG",
        "mechanical_entry": 100.0,
        "mechanical_sl": 99.0,
        "mechanical_tp": 101.5,
        "ai_call_attempted": False,
        "ai_call_count": 0,
        "m15_outcome": "TP",
        "m1_refinement_attempted": True,
        "m1_local_coverage": True,
        "m1_gap_count_in_horizon": 0,
        "m1_horizon_bars": 3,
        "m1_refined_outcome": "TP",
        "m5_refinement_attempted": True,
        "m5_local_coverage": True,
        "m5_gap_count_in_horizon": 0,
        "m5_horizon_bars": 1,
        "m5_refined_outcome": "TP",
    }
    row.update(overrides)
    return row


def _future_rows(*, lows, highs):
    start = datetime(2026, 1, 1, 0, 1, tzinfo=timezone.utc)
    rows = []
    for idx, (low, high) in enumerate(zip(lows, highs)):
        rows.append(
            {
                "time": start + timedelta(minutes=idx),
                "open": 100.5,
                "high": high,
                "low": low,
                "close": 100.3,
            }
        )
    return rows


def _write_jsonl(path, rows):
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
