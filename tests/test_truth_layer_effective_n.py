import json
import shutil
import uuid
from pathlib import Path

import numpy as np
import pytest

from scripts.analyze_truth_layer_effective_n import (
    analyze_effective_n,
    effective_n_participation_ratio,
    render_report,
)


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"truth_layer_effective_n_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_participation_ratio_effective_n_bounds():
    independent = np.eye(3)
    identical = np.ones((3, 3))

    independent_n, _ = effective_n_participation_ratio(independent)
    identical_n, _ = effective_n_participation_ratio(identical)

    assert independent_n == pytest.approx(3.0)
    assert identical_n == pytest.approx(1.0)


def test_effective_n_diagnostic_uses_registered_matrix_and_blocks_promotion(tmp_path):
    truth_path = tmp_path / "truth.jsonl"
    matrix_path = tmp_path / "matrix.json"
    _write_matrix(matrix_path)
    rows = []
    for month in range(1, 5):
        rows.append(_row("USDJPY", "tokyo", "bearish|D1", "2026", month, "TP", 1.0))
        rows.append(_row("GBPJPY", "tokyo", "bullish|D1", "2026", month, "SL", -1.0))
        rows.append(_row("XAUUSD", "ny", "bullish|D1", "2026", month, "TP", 1.0 if month % 2 else -1.0))
    _write_jsonl(truth_path, rows)

    summary = analyze_effective_n(input_path=truth_path, matrix_path=matrix_path)
    report = render_report(summary)

    assert summary["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert summary["matrix_effective_n"]["status"] == "COMPUTED_DIAGNOSTIC_ONLY"
    assert summary["matrix_effective_n"]["candidate_count"] == 3
    assert summary["primary_children_effective_n"]["candidate_count"] == 2
    assert summary["promotion_usable"] is False
    assert "Historical effective_N is diagnostic-only" in report


def _write_matrix(path):
    payload = {
        "schema_version": "truth_layer_prospective_candidate_matrix_v1",
        "promotion_verdict_allowed": False,
        "population": {
            "scope_name": "RESOLUTION_SAFE_HIGH",
            "setup_only": True,
            "truth_confidences": ["HIGH"],
            "exclude_truth_outcomes": ["SAME_BAR", "LOWER_TF_GAPPY"],
            "require_resolution_safe": True,
            "primary_resolved_outcomes": ["TP", "SL", "TIMEOUT"],
        },
        "candidates": [
            {"cohort_key": "USDJPY|tokyo|bearish|D1", "role": "primary_controlled_child"},
            {"cohort_key": "GBPJPY|tokyo|bullish|D1", "role": "primary_controlled_child"},
            {"cohort_key": "XAUUSD|ny|bullish|D1", "role": "registered_matrix_candidate"},
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
