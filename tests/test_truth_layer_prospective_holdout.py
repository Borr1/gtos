import json
import shutil
import uuid
from pathlib import Path

import pytest

from scripts.evaluate_truth_layer_prospective_holdout import (
    PROSPECTIVE_CUTOFF_UTC,
    evaluate_prospective_holdout,
    render_report,
    validate_prospective_input,
)


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"truth_layer_prospective_holdout_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_prospective_holdout_rejects_same_dataset_rows(tmp_path):
    truth_path = tmp_path / "truth.jsonl"
    spec_path = tmp_path / "spec.json"
    _write_spec(spec_path)
    _write_jsonl(
        truth_path,
        [
            _row(
                "2026-04-30T17:00:00+00:00",
                "TP",
                1.5,
                opportunity_key="same-dataset-cutoff-row",
            )
        ],
    )

    validation = validate_prospective_input(truth_path)

    assert validation["prospective_input_valid"] is False
    assert validation["stale_rows_at_or_before_cutoff"] == 1
    with pytest.raises(ValueError, match="prospective input is invalid"):
        evaluate_prospective_holdout(input_path=truth_path, spec_path=spec_path)


def test_prospective_holdout_valid_future_rows_still_cannot_promote(tmp_path):
    truth_path = tmp_path / "truth.jsonl"
    spec_path = tmp_path / "spec.json"
    _write_spec(spec_path)
    _write_jsonl(
        truth_path,
        [
            _row("2026-05-01T00:15:00+00:00", "TP", 1.5, opportunity_key="future-tp"),
            _row("2026-05-02T00:15:00+00:00", "SL", -1.0, opportunity_key="future-sl"),
        ],
    )

    summary = evaluate_prospective_holdout(input_path=truth_path, spec_path=spec_path)
    report = render_report(summary)

    assert PROSPECTIVE_CUTOFF_UTC.isoformat() == "2026-04-30T17:00:00+00:00"
    assert summary["input_validation"]["prospective_input_valid"] is True
    assert summary["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert summary["methodology_gates"]["dsr_corrected_p"] == "NOT_COMPUTED"
    assert summary["controlled_summary"]["hypotheses"][0]["included"]["resolved_r_n"] == 2
    assert "refuses same-dataset rows" in report
    assert "This report cannot promote alpha" in report


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
                "hypothesis_id": "H-TEST-1",
                "cohort_key": "USDJPY|tokyo|bearish|D1",
                "role": "primary",
                "selection_reason": "test",
                "population": {
                    "inherit_default_population": True
                },
                "necessary_not_sufficient_research_preconditions": {
                    "min_total_resolved_n": 1,
                    "min_valid_year_folds": 1,
                    "require_all_valid_years_positive": True,
                    "max_single_year_resolved_share": 1.0,
                },
            }
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _row(timestamp, outcome, realized, **overrides):
    row = {
        "opportunity_key": f"USDJPY|tokyo|{timestamp}|{outcome}",
        "symbol": "USDJPY",
        "session": "tokyo",
        "year": timestamp[:4],
        "candle_close_utc": timestamp,
        "truth_regime": "bearish|D1",
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
