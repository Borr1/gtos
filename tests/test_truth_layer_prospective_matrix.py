import json
import shutil
import uuid
from pathlib import Path

import pytest

from scripts.evaluate_truth_layer_prospective_matrix import (
    evaluate_prospective_matrix,
    render_report,
)


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"truth_layer_prospective_matrix_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_prospective_matrix_rejects_historical_rows(tmp_path):
    truth_path = tmp_path / "truth.jsonl"
    spec_path = tmp_path / "spec.json"
    matrix_path = tmp_path / "matrix.json"
    _write_spec(spec_path)
    _write_matrix(matrix_path)
    _write_jsonl(
        truth_path,
        [_row("USDJPY", "tokyo", "bearish|D1", "2026-04-30T17:00:00+00:00", "TP", 1.0)],
    )

    with pytest.raises(ValueError, match="prospective input is invalid"):
        evaluate_prospective_matrix(input_path=truth_path, spec_path=spec_path, matrix_path=matrix_path)


def test_prospective_matrix_reports_matrix_pbo_and_effective_n_without_promotion(tmp_path):
    truth_path = tmp_path / "truth.jsonl"
    spec_path = tmp_path / "spec.json"
    matrix_path = tmp_path / "matrix.json"
    _write_spec(spec_path)
    _write_matrix(matrix_path)
    rows = []
    for month in range(5, 13):
        timestamp = f"2026-{month:02d}-03T00:00:00+00:00"
        rows.append(_row("USDJPY", "tokyo", "bearish|D1", timestamp, "TP", 1.0))
        rows.append(_row("GBPJPY", "tokyo", "bullish|D1", timestamp, "TP", 1.0 if month % 2 else -1.0))
        rows.append(_row("XAUUSD", "ny", "bullish|D1", timestamp, "SL", -1.0 if month % 2 else 1.0))
    _write_jsonl(truth_path, rows)

    summary = evaluate_prospective_matrix(input_path=truth_path, spec_path=spec_path, matrix_path=matrix_path)
    report = render_report(summary)

    assert summary["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert summary["methodology_gates"]["prospective_input"] == "PASS"
    assert summary["methodology_gates"]["dsr_corrected_p"] == "NOT_COMPUTED"
    assert summary["matrix_pbo"]["status"] == "COMPUTED_PROSPECTIVE_MATRIX_DIAGNOSTIC_ONLY"
    assert summary["matrix_pbo"]["candidate_count"] == 3
    assert summary["effective_n"]["matrix_effective_n"]["status"] == "COMPUTED_DIAGNOSTIC_ONLY"
    assert summary["effective_n"]["matrix_effective_n"]["candidate_count"] == 3
    assert "full frozen candidate matrix" in report
    assert "alpha promotion remains blocked" in report


def _write_spec(path):
    payload = {
        "schema_version": "truth_layer_controlled_hypotheses_v1",
        "promotion_verdict_allowed": False,
        "selection_status": "post_diagnostic_same_dataset_followup",
        "registry_markdown": "test.md",
        "trial_budget_policy": {
            "registered_family": "truth_layer_jpy_tokyo_d1_v1"
        },
        "default_population": {
            "scope_name": "RESOLUTION_SAFE_HIGH",
            "setup_only": True,
            "truth_confidences": ["HIGH"],
            "exclude_truth_outcomes": ["SAME_BAR", "LOWER_TF_GAPPY"],
            "require_resolution_safe": True,
            "primary_resolved_outcomes": ["TP", "SL", "TIMEOUT"],
        },
        "split_plan": {
            "primary_valid_fold_min_resolved_n": 1
        },
        "hypotheses": [
            {
                "hypothesis_id": "H-1",
                "cohort_key": "USDJPY|tokyo|bearish|D1",
                "role": "primary",
                "population": {"inherit_default_population": True},
                "necessary_not_sufficient_research_preconditions": {
                    "min_total_resolved_n": 1,
                    "min_valid_year_folds": 1,
                    "require_all_valid_years_positive": True,
                    "max_single_year_resolved_share": 1.0,
                },
            },
            {
                "hypothesis_id": "H-2",
                "cohort_key": "GBPJPY|tokyo|bullish|D1",
                "role": "primary",
                "population": {"inherit_default_population": True},
                "necessary_not_sufficient_research_preconditions": {
                    "min_total_resolved_n": 1,
                    "min_valid_year_folds": 1,
                    "require_all_valid_years_positive": True,
                    "max_single_year_resolved_share": 1.0,
                },
            },
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


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


def _row(symbol, session, regime, timestamp, outcome, realized):
    return {
        "opportunity_key": f"{symbol}|{timestamp}|{outcome}",
        "symbol": symbol,
        "session": session,
        "year": timestamp[:4],
        "candle_close_utc": timestamp,
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
        "m1_refined_exit_time": timestamp,
        "m5_gap_count_in_horizon": 0,
    }


def _write_jsonl(path, rows):
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
