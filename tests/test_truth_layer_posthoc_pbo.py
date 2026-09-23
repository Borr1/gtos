import json
import shutil
import uuid
from pathlib import Path

import pytest

from scripts.analyze_truth_layer_posthoc_pbo import (
    analyze_posthoc_pbo,
    cscv_pbo,
    render_report,
)


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"truth_layer_posthoc_pbo_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_cscv_pbo_blocks_when_matrix_is_too_small():
    pbo, diagnostic = cscv_pbo([[1.0], [2.0]])

    assert pbo is None
    assert diagnostic["status"] == "BLOCKED_INSUFFICIENT_PERIODS_OR_STRATEGIES"


def test_cscv_pbo_uses_all_periods_when_period_count_is_not_divisible():
    matrix = [[float(row), float(20 - row)] for row in range(10)]

    pbo, diagnostic = cscv_pbo(matrix)

    assert pbo is not None
    assert diagnostic["periods_used"] == 10
    assert diagnostic["subperiod_policy"] == "balanced_contiguous_all_periods"
    assert sum(diagnostic["subperiod_sizes"]) == 10


def test_cscv_pbo_is_zero_when_is_winner_is_always_oos_winner():
    matrix = [[1.0, 0.0, -1.0] for _ in range(12)]

    pbo, diagnostic = cscv_pbo(matrix)

    assert pbo == 0.0
    assert diagnostic["status"] == "COMPUTED_POSTHOC_DIAGNOSTIC_ONLY"
    assert all(not record["below_median"] for record in diagnostic["sample_records"])


def test_cscv_pbo_is_one_when_is_winner_is_always_oos_loser():
    matrix = []
    for idx in range(12):
        if idx < 6:
            matrix.append([1.0, 0.0])
        else:
            matrix.append([0.0, 1.0])

    pbo, diagnostic = cscv_pbo(matrix)

    assert pbo == 1.0
    assert diagnostic["status"] == "COMPUTED_POSTHOC_DIAGNOSTIC_ONLY"


def test_posthoc_pbo_report_is_not_promotion_grade(tmp_path):
    truth_path = tmp_path / "truth.jsonl"
    spec_path = tmp_path / "spec.json"
    _write_spec(spec_path)
    rows = []
    for month in range(1, 9):
        year = "2022" if month <= 4 else "2023"
        rows.append(_row("USDJPY", "tokyo", "bearish|D1", year, month, "TP", 1.5))
        rows.append(_row("GBPJPY", "tokyo", "bullish|D1", year, month, "SL", -1.0))
    _write_jsonl(truth_path, rows)

    summary = analyze_posthoc_pbo(
        input_path=truth_path,
        spec_path=spec_path,
        min_total_resolved_n=1,
        min_valid_year_folds=1,
        min_year_resolved_n=1,
    )
    report = render_report(summary)

    assert summary["promotion_verdict_allowed"] is False
    assert summary["promotion_verdict"] == "NOT_ALLOWED_POSTHOC_DIAGNOSTIC_ONLY"
    assert summary["eligible_universe_n"] == 2
    assert "post-hoc selection-risk diagnostic" in report
    assert "not promotion-grade PBO" in report


def _write_spec(path):
    payload = {
        "schema_version": "truth_layer_controlled_hypotheses_v1",
        "promotion_verdict_allowed": False,
        "registry_markdown": "test.md",
        "selection_status": "post_diagnostic_same_dataset_followup",
        "default_population": {
            "scope_name": "RESOLUTION_SAFE_HIGH",
            "setup_only": True,
            "truth_confidences": ["HIGH"],
            "exclude_truth_outcomes": ["SAME_BAR", "LOWER_TF_GAPPY"],
            "require_resolution_safe": True,
            "primary_resolved_outcomes": ["TP", "SL", "TIMEOUT"],
        },
        "hypotheses": [
            {
                "hypothesis_id": "H-1",
                "cohort_key": "USDJPY|tokyo|bearish|D1",
                "role": "primary",
            },
            {
                "hypothesis_id": "H-2",
                "cohort_key": "GBPJPY|tokyo|bullish|D1",
                "role": "primary",
            },
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _row(symbol, session, regime, year, month, outcome, realized):
    return {
        "opportunity_key": f"{symbol}|{year}|{month}|{outcome}",
        "symbol": symbol,
        "session": session,
        "year": year,
        "candle_close_utc": f"{year}-{month:02d}-03T00:00:00+00:00",
        "truth_regime": regime,
        "truth_outcome": outcome,
        "truth_realized_r": realized,
        "truth_failure_bucket": "SUCCESS_TP_FIRST" if outcome == "TP" else "FAIL_STOP_FIRST",
        "truth_confidence": "HIGH",
        "truth_source_timeframe": "M1",
        "lower_tf_gap_count_in_horizon": 0,
        "lower_tf_first_gap_utc": None,
        "would_send_ai": True,
        "mechanical_setup_status": "OK",
        "mechanical_side": "SHORT",
        "ai_call_attempted": False,
        "ai_call_count": 0,
        "m1_gap_count_in_horizon": 0,
        "m1_first_gap_utc": None,
        "m1_refined_exit_time": f"{year}-{month:02d}-03T00:30:00+00:00",
        "m5_gap_count_in_horizon": 0,
    }


def _write_jsonl(path, rows):
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
