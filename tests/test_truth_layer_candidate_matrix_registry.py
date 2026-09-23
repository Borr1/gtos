import json
import shutil
import uuid
from pathlib import Path

import pytest

from scripts.register_truth_layer_candidate_matrix import (
    build_candidate_matrix_registry,
    render_report,
)


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"truth_layer_candidate_matrix_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_candidate_matrix_registry_freezes_primary_and_comparator_candidates(tmp_path):
    truth_path = tmp_path / "truth.jsonl"
    spec_path = tmp_path / "spec.json"
    _write_spec(spec_path)
    rows = []
    for month in range(1, 7):
        year = "2025" if month <= 3 else "2026"
        rows.append(_row("USDJPY", "tokyo", "bearish|D1", year, month, "TP", 1.5))
        rows.append(_row("XAUUSD", "ny", "bullish|D1", year, month, "TP", 1.0))
    _write_jsonl(truth_path, rows)

    registry = build_candidate_matrix_registry(
        input_path=truth_path,
        spec_path=spec_path,
        min_total_resolved_n=1,
        min_valid_year_folds=1,
        min_year_resolved_n=1,
    )
    report = render_report(registry)

    assert registry["promotion_verdict_allowed"] is False
    assert registry["candidate_count"] == 2
    assert registry["primary_candidate_count"] == 1
    assert {row["role"] for row in registry["candidates"]} == {
        "primary_controlled_child",
        "watchlist_from_controlled_spec",
    }
    assert "Future PBO/effective_N work must keep every registered candidate" in report


def _write_spec(path):
    payload = {
        "schema_version": "truth_layer_controlled_hypotheses_v1",
        "promotion_verdict_allowed": False,
        "prospective_holdout_plan": "plan.md",
        "prospective_cutoff_utc": "2026-04-30T17:00:00+00:00",
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
            }
        ],
        "watchlist_cohorts": [
            {"cohort_key": "XAUUSD|ny|bullish|D1", "status": "watchlist"}
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
