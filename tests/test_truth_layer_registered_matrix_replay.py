import json
import shutil
import uuid
from pathlib import Path

import pytest

from scripts.run_truth_layer_registered_matrix_replay import (
    build_registered_matrix_strategy_spec,
    render_report,
    run_registered_matrix_replay,
)


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"truth_layer_registered_matrix_replay_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_build_registered_matrix_strategy_spec_freezes_all_candidates(tmp_path):
    matrix_path = tmp_path / "matrix.json"
    registry = _matrix_registry()
    matrix_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")

    strategy = build_registered_matrix_strategy_spec(registry, matrix_path=matrix_path)

    assert strategy["strategy_type"] == "cohort_filter_v1"
    assert strategy["run_mode"] == "REGISTERED_MATRIX_REPLAY"
    assert strategy["promotion_verdict_allowed"] is False
    assert strategy["source_matrix"]["candidate_count"] == 3
    assert strategy["cohort_keys"] == [
        "USDJPY|tokyo|bearish|D1",
        "XAUUSD|ny|bullish|D1",
        "GBPUSD|london|bearish|D1",
    ]


def test_registered_matrix_replay_reports_groups_and_buckets(tmp_path):
    truth_path = tmp_path / "truth.jsonl"
    matrix_path = tmp_path / "matrix.json"
    lab_spec_path = tmp_path / "lab.json"
    strategy_path = tmp_path / "strategy.json"
    _write_json(matrix_path, _matrix_registry())
    _write_json(lab_spec_path, _lab_spec())
    _write_jsonl(
        truth_path,
        [
            _row("USDJPY", "tokyo", "bearish|D1", "2024-01-03T00:00:00+00:00", "TP", 1.5),
            _row("USDJPY", "tokyo", "bearish|D1", "2024-01-04T00:00:00+00:00", "TP", 1.5),
            _row("XAUUSD", "ny", "bullish|D1", "2024-01-04T13:15:00+00:00", "SL", -1.0),
            _row("GBPUSD", "london", "bearish|D1", "2024-01-05T07:15:00+00:00", "TP", 1.5),
            _row("GBPJPY", "tokyo", "bullish|D1", "2024-01-05T00:00:00+00:00", "TP", 1.5),
        ],
    )

    summary = run_registered_matrix_replay(
        input_path=truth_path,
        matrix_path=matrix_path,
        lab_spec_path=lab_spec_path,
        strategy_spec_path=strategy_path,
    )
    report = render_report(summary)

    assert summary["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert summary["candidate_count"] == 3
    assert summary["matrix_replay"]["decision_counts"] == {"SKIP": 1, "TAKE": 4}
    assert summary["matrix_replay"]["score"]["resolved_r_n"] == 4
    assert strategy_path.exists()
    assert "Instrument Summary" in report
    assert "Full Candidate Matrix" in report
    assert {row["symbol"] for row in summary["instrument_summary"]} == {"GBPUSD", "USDJPY", "XAUUSD"}


def test_registered_matrix_rejects_duplicate_candidate_keys(tmp_path):
    matrix_path = tmp_path / "matrix.json"
    registry = _matrix_registry()
    registry["candidates"].append(dict(registry["candidates"][0]))
    matrix_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate cohort keys"):
        build_registered_matrix_strategy_spec(registry, matrix_path=matrix_path)


def _matrix_registry():
    return {
        "schema_version": "truth_layer_prospective_candidate_matrix_v1",
        "promotion_verdict_allowed": False,
        "historical_pbo_reference": {
            "status": "POSTHOC_DIAGNOSTIC_ONLY",
            "pbo": 0.5,
        },
        "population": {
            "scope_name": "RESOLUTION_SAFE_HIGH",
            "setup_only": True,
            "truth_confidences": ["HIGH"],
            "exclude_truth_outcomes": ["SAME_BAR", "LOWER_TF_GAPPY"],
            "require_resolution_safe": True,
            "primary_resolved_outcomes": ["TP", "SL", "TIMEOUT"],
        },
        "candidates": [
            _candidate("P3-TL-MATRIX-001", "USDJPY|tokyo|bearish|D1", "primary_controlled_child", 2, 2, 0.3),
            _candidate("P3-TL-MATRIX-002", "XAUUSD|ny|bullish|D1", "registered_matrix_candidate", 1, 1, 0.3),
            _candidate("P3-TL-MATRIX-003", "GBPUSD|london|bearish|D1", "registered_matrix_candidate", 1, 1, 0.3),
        ],
    }


def _candidate(candidate_id, cohort_key, role, valid_years, positive_years, max_share):
    return {
        "candidate_id": candidate_id,
        "cohort_key": cohort_key,
        "role": role,
        "historical_valid_year_folds": valid_years,
        "historical_positive_valid_year_folds": positive_years,
        "historical_max_year_resolved_share": max_share,
        "historical_active_periods": 1,
    }


def _lab_spec():
    return {
        "schema_version": "truth_layer_historical_replay_lab_spec_v1",
        "promotion_verdict_allowed": False,
        "replay_clock": {
            "field": "candle_close_utc",
            "sort_before_replay": True,
        },
        "observation_projection": {
            "allowed_direct_fields": [
                "candle_close_utc",
                "symbol",
                "session",
                "mechanical_setup_status",
                "would_send_ai",
            ],
            "safe_aliases": {
                "cohort_key": "symbol|session|truth_regime",
                "regime_key": "truth_regime",
            },
            "forbidden_strategy_prefixes": ["truth_", "m1_", "m5_", "m15_", "lower_tf_"],
            "forbidden_strategy_fields": ["truth_realized_r", "truth_outcome", "truth_regime"],
        },
        "scoring": {
            "setup_only": True,
            "truth_confidences": ["HIGH"],
            "exclude_truth_outcomes": ["SAME_BAR", "LOWER_TF_GAPPY"],
            "require_resolution_safe": True,
            "resolved_outcomes": ["TP", "SL", "TIMEOUT"],
        },
    }


def _row(symbol, session, regime, timestamp, outcome, realized):
    return {
        "opportunity_key": f"{symbol}|{timestamp}|{outcome}",
        "symbol": symbol,
        "session": session,
        "year": timestamp[:4],
        "month": timestamp[:7],
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
        "ai_call_attempted": False,
        "ai_call_count": 0,
        "m1_gap_count_in_horizon": 0,
        "m1_first_gap_utc": None,
        "m1_refined_exit_time": timestamp,
        "m5_gap_count_in_horizon": 0,
    }


def _write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_jsonl(path, rows):
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

