import csv
import json
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts.run_raw_ohlc_prequential_replay import (
    DEFAULT_SPEC_PATH,
    CandleSeries,
    active_cohort_specs,
    build_asof_slices,
    compute_session_levels_no_leak,
    decide_from_cohorts,
    input_order_diagnostics,
    load_replay_spec,
    project_observation,
    render_report,
)


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"raw_ohlc_prequential_replay_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_m15_asof_window_excludes_future_candles(tmp_path):
    m15_path = tmp_path / "TEST_M15.csv"
    _write_ohlcv(
        m15_path,
        start=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
        delta=timedelta(minutes=15),
        highs=[101.0, 102.0, 999.0],
    )
    series = CandleSeries.from_csv(m15_path, timeframe="M15")

    slices, alignment = build_asof_slices(
        series_by_tf={"M15": series},
        candle_close_utc=datetime(2026, 1, 1, 0, 30, tzinfo=timezone.utc),
        lookbacks={"M15": 10, "H1": 10, "H4": 10, "D1": 10},
    )

    assert [row["time"] for row in slices["M15"]] == [
        "2026-01-01T00:00:00Z",
        "2026-01-01T00:15:00Z",
    ]
    assert max(row["high"] for row in slices["M15"]) == 102.0
    assert alignment["future_candle_exposure_violations"] == 0


def test_partial_htf_alignment_uses_closed_m15_not_future_native_htf(tmp_path):
    m15_path = tmp_path / "TEST_M15.csv"
    h1_path = tmp_path / "TEST_H1.csv"
    h4_path = tmp_path / "TEST_H4.csv"
    d1_path = tmp_path / "TEST_D1.csv"
    _write_ohlcv(
        m15_path,
        start=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
        delta=timedelta(minutes=15),
        highs=[101.0, 102.0, 999.0, 1000.0],
    )
    _write_ohlcv(
        h1_path,
        start=datetime(2025, 12, 31, 23, 0, tzinfo=timezone.utc),
        delta=timedelta(hours=1),
        highs=[50.0, 999.0],
    )
    _write_ohlcv(
        h4_path,
        start=datetime(2025, 12, 31, 20, 0, tzinfo=timezone.utc),
        delta=timedelta(hours=4),
        highs=[40.0, 999.0],
    )
    _write_ohlcv(
        d1_path,
        start=datetime(2025, 12, 31, 0, 0, tzinfo=timezone.utc),
        delta=timedelta(days=1),
        highs=[30.0, 999.0],
    )

    slices, alignment = build_asof_slices(
        series_by_tf={
            "M15": CandleSeries.from_csv(m15_path, timeframe="M15"),
            "H1": CandleSeries.from_csv(h1_path, timeframe="H1"),
            "H4": CandleSeries.from_csv(h4_path, timeframe="H4"),
            "D1": CandleSeries.from_csv(d1_path, timeframe="D1"),
        },
        candle_close_utc=datetime(2026, 1, 1, 0, 30, tzinfo=timezone.utc),
        lookbacks={"M15": 10, "H1": 10, "H4": 10, "D1": 10},
        htf_policy="partial_from_m15_no_leak",
    )

    assert slices["H1"][-1]["time"] == "2026-01-01T00:00:00Z"
    assert slices["H1"][-1]["high"] == 102.0
    assert slices["H4"][-1]["high"] == 102.0
    assert slices["D1"][-1]["high"] == 102.0
    assert alignment["partial_bar_included__H1"] is True
    assert alignment["partial_bar_included__H4"] is True
    assert alignment["partial_bar_included__D1"] is True
    assert alignment["future_candle_exposure_violations"] == 0
    assert alignment["htf_asof_violations"] == 0


def test_session_levels_exclude_future_m15_bars(tmp_path):
    m15_path = tmp_path / "TEST_M15.csv"
    _write_ohlcv(
        m15_path,
        start=datetime(2026, 1, 2, 7, 0, tzinfo=timezone.utc),
        delta=timedelta(minutes=15),
        highs=[101.0, 102.0, 999.0],
    )

    levels = compute_session_levels_no_leak(
        m15=CandleSeries.from_csv(m15_path, timeframe="M15"),
        target_date=datetime(2026, 1, 2, tzinfo=timezone.utc).date(),
        candle_close_utc=datetime(2026, 1, 2, 7, 30, tzinfo=timezone.utc),
    )

    assert levels["session_high"] == 102.0
    assert levels["london_high"] == 102.0


def test_input_order_diagnostics_reports_clock_regressions():
    events = [
        _event("USDJPY", datetime(2026, 1, 1, 1, 0, tzinfo=timezone.utc)),
        _event("GBPJPY", datetime(2026, 1, 1, 0, 30, tzinfo=timezone.utc)),
    ]

    diagnostics = input_order_diagnostics(events)

    assert diagnostics["input_order_clock_regressions"] == 1
    assert diagnostics["sort_before_replay"] is True


def test_report_keeps_no_promotion_boundary():
    summary = {
        "created_at_utc": "2026-05-01T00:00:00+00:00",
        "spec_path": "spec.json",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "spec_sha256": "abc",
        "code_commit": "test",
        "run_mode": "LOCKED_HISTORICAL_RAW_OHLC_REPLAY",
        "evidence_class": "same_dataset_historical_raw_ohlc_diagnostic",
        "data_inventory": [],
        "active_cohorts": [],
        "rows_replayed": 0,
        "duplicate_event_keys": 0,
        "invalid_clock_rows": 0,
        "future_candle_exposure_violations": 0,
        "htf_asof_violations": 0,
        "forbidden_observation_violations": 0,
        "ai_attempted_rows": 0,
        "ai_call_count_sum": 0,
        "integrity": {"status": "PASS"},
        "decision_counts": {},
        "pre_ai_gate_counts": {},
        "score": {
            "actions_taken": 0,
            "scoring_population_actions": 0,
            "resolved_r_n": 0,
            "sum_r": 0.0,
            "mean_r": None,
            "win_rate": None,
            "action_outcomes": {},
            "scoring_exclusions": {},
            "cohort_scores": [],
            "period_scores": [],
        },
    }

    report = render_report(summary)

    assert "NO_PROMOTION_VERDICT" in report
    assert "DSR, PBO, effective_N" in report
    assert "not a promotion dossier" in report


def test_raw_replay_import_does_not_load_paid_ai_clients():
    code = (
        "import sys\n"
        "import scripts.run_raw_ohlc_prequential_replay\n"
        "print('anthropic' in sys.modules)\n"
        "print('openai' in sys.modules)\n"
    )

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=True,
    )

    assert result.stdout.strip().splitlines() == ["False", "False"]


def _write_ohlcv(path, *, start, delta, highs):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["time", "open", "high", "low", "close", "volume"],
        )
        writer.writeheader()
        for idx, high in enumerate(highs):
            opened_at = start + delta * idx
            open_price = float(high) - 1.0
            writer.writerow(
                {
                    "time": opened_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "open": f"{open_price:.5f}",
                    "high": f"{float(high):.5f}",
                    "low": f"{open_price - 1.0:.5f}",
                    "close": f"{open_price + 0.5:.5f}",
                    "volume": 100 + idx,
                }
            )


def _event(symbol, candle_close):
    candle = type(
        "Candle",
        (),
        {
            "candle_close_utc": candle_close,
            "session": "tokyo",
        },
    )()
    return type(
        "Event",
        (),
        {
            "symbol": symbol,
            "candle": candle,
        },
    )()
