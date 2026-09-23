import json
import shutil
import uuid
from pathlib import Path

import pytest

from scripts.run_truth_layer_prequential_replay import (
    decide,
    load_lab_spec,
    project_observation,
    render_report,
    run_prequential_replay,
    validate_strategy_references,
)


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"truth_layer_prequential_replay_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_observation_projection_hides_scorer_only_fields(tmp_path):
    lab_spec_path = tmp_path / "lab.json"
    _write_lab_spec(lab_spec_path)
    lab_spec = load_lab_spec(lab_spec_path)
    row = _row(
        "USDJPY",
        "tokyo",
        "bearish|D1",
        "2024-01-03T00:00:00+00:00",
        "TP",
        1.5,
    )

    observation = project_observation(row, lab_spec)

    assert observation["cohort_key"] == "USDJPY|tokyo|bearish|D1"
    assert observation["regime_key"] == "bearish|D1"
    assert observation["mechanical_setup_status"] == "OK"
    assert "truth_realized_r" not in observation
    assert "truth_outcome" not in observation
    assert "truth_regime" not in observation
    assert "m1_refined_exit_time" not in observation
    assert all(not key.startswith("truth_") for key in observation)


def test_strategy_references_must_be_observation_fields(tmp_path):
    lab_spec_path = tmp_path / "lab.json"
    _write_lab_spec(lab_spec_path)
    lab_spec = load_lab_spec(lab_spec_path)
    strategy = {
        "schema_version": "truth_layer_prequential_strategy_v1",
        "promotion_verdict_allowed": False,
        "strategy_type": "field_rules_v1",
        "rules": [{"field": "truth_realized_r", "op": "gt", "value": 0}],
    }

    with pytest.raises(ValueError, match="unavailable observation field"):
        validate_strategy_references(strategy, set(lab_spec["observation_projection"]["allowed_direct_fields"]))


def test_field_rule_strategy_uses_visible_fields_only():
    strategy = {
        "schema_version": "truth_layer_prequential_strategy_v1",
        "promotion_verdict_allowed": False,
        "strategy_type": "field_rules_v1",
        "decision_policy": {"match_action": "TAKE", "non_match_action": "SKIP"},
        "rules": [
            {"field": "symbol", "op": "eq", "value": "USDJPY"},
            {"field": "mechanical_setup_status", "op": "eq", "value": "OK"},
        ],
    }
    observation = {"symbol": "USDJPY", "mechanical_setup_status": "OK"}

    assert decide(strategy, observation)["action"] == "TAKE"


def test_prequential_replay_scores_after_decision_without_promotion(tmp_path):
    truth_path = tmp_path / "truth.jsonl"
    lab_spec_path = tmp_path / "lab.json"
    strategy_path = tmp_path / "strategy.json"
    _write_lab_spec(lab_spec_path)
    _write_strategy(strategy_path)
    rows = [
        _row("XAUUSD", "ny", "bullish|D1", "2024-01-03T13:15:00+00:00", "TP", 1.5),
        _row("USDJPY", "tokyo", "bearish|D1", "2024-01-03T00:00:00+00:00", "TP", 1.5),
        _row("USDJPY", "tokyo", "bearish|D1", "2024-01-04T00:00:00+00:00", "SL", -1.0),
        _row("GBPJPY", "tokyo", "bullish|D1", "2024-01-05T00:00:00+00:00", "NO_ENTRY", None),
        _row("GBPJPY", "tokyo", "bullish|D1", "2024-01-06T00:00:00+00:00", "SAME_BAR", None),
    ]
    _write_jsonl(truth_path, rows)

    summary = run_prequential_replay(
        input_path=truth_path,
        lab_spec_path=lab_spec_path,
        strategy_spec_path=strategy_path,
    )
    report = render_report(summary)

    assert summary["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert summary["integrity"]["status"] == "PASS"
    assert summary["input_order_diagnostics"]["input_order_clock_regressions"] == 1
    assert summary["decision_counts"] == {"SKIP": 1, "TAKE": 4}
    assert summary["score"]["actions_taken"] == 4
    assert summary["score"]["scoring_population_actions"] == 3
    assert summary["score"]["resolved_r_n"] == 2
    assert summary["score"]["mean_r"] == pytest.approx(0.25)
    assert summary["score"]["action_outcomes"]["NO_ENTRY"] == 1
    assert summary["score"]["scoring_exclusions"]["truth_outcome_excluded"] == 1
    assert "prequential" in report
    assert "NO_PROMOTION_VERDICT" in report


def _write_lab_spec(path):
    payload = {
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
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_strategy(path):
    payload = {
        "schema_version": "truth_layer_prequential_strategy_v1",
        "promotion_verdict_allowed": False,
        "strategy_id": "TEST",
        "strategy_type": "cohort_filter_v1",
        "run_mode": "LOCKED_HISTORICAL_REPLAY",
        "evidence_class": "test",
        "cohort_keys": [
            "USDJPY|tokyo|bearish|D1",
            "GBPJPY|tokyo|bullish|D1",
        ],
        "decision_policy": {
            "match_action": "TAKE",
            "non_match_action": "SKIP",
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _row(symbol, session, regime, timestamp, outcome, realized, **overrides):
    row = {
        "opportunity_key": f"{symbol}|{timestamp}|{outcome}",
        "symbol": symbol,
        "session": session,
        "year": timestamp[:4],
        "month": timestamp[:7],
        "candle_close_utc": timestamp,
        "truth_regime": regime,
        "truth_bias_stack": f"test={regime}",
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
    row.update(overrides)
    return row


def _write_jsonl(path, rows):
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

