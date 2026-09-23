import json
import shutil
import uuid
from pathlib import Path

import pytest

from scripts.evaluate_truth_layer_methodology_readiness import (
    compute_dsr_diagnostic,
    evaluate_methodology_readiness,
    render_report,
)


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"truth_layer_methodology_readiness_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_same_dataset_dsr_is_computed_but_not_promotion_usable():
    diagnostic = compute_dsr_diagnostic([1.5, 1.5, 1.5, -1.0, 1.0], n_trials=200)

    assert diagnostic["status"] == "COMPUTED_SAME_DATASET_DIAGNOSTIC_ONLY"
    assert diagnostic["n"] == 5
    assert diagnostic["promotion_usable"] is False
    assert "same dataset" in diagnostic["promotion_usable_reason"]


def test_methodology_readiness_blocks_pbo_and_true_effective_n(tmp_path):
    truth_path = tmp_path / "truth.jsonl"
    spec_path = tmp_path / "spec.json"
    _write_spec(spec_path)
    _write_jsonl(
        truth_path,
        [
            _row("2022", "TP", 1.5, opportunity_key="2022-tp"),
            _row("2023", "TP", 1.5, opportunity_key="2023-tp"),
            _row("2024", "SL", -1.0, opportunity_key="2024-sl"),
            _row("2025", "TP", 1.5, opportunity_key="2025-tp"),
        ],
    )

    summary = evaluate_methodology_readiness(input_path=truth_path, spec_path=spec_path)

    assert summary["promotion_verdict"] == "BLOCKED"
    assert summary["methodology_gate_matrix"]["same_dataset_dsr_diagnostic"] == "COMPUTED_DIAGNOSTIC_ONLY"
    assert summary["methodology_gate_matrix"]["pbo"] == "BLOCKED_NOT_COMPUTABLE_FROM_PRIMARY_TWO_ONLY"
    assert summary["methodology_gate_matrix"]["true_effective_n"] == "BLOCKED_HISTORICAL_MATRIX_DIAGNOSTIC_ONLY"
    assert summary["pbo_blocker"]["status"] == "BLOCKED_NOT_COMPUTABLE_HONESTLY_FROM_CURRENT_PRIMARY_TWO_ONLY"
    assert summary["hypotheses"][0]["same_dataset_dsr"]["promotion_usable"] is False


def test_readiness_report_states_no_alpha_promotion(tmp_path):
    truth_path = tmp_path / "truth.jsonl"
    spec_path = tmp_path / "spec.json"
    _write_spec(spec_path)
    _write_jsonl(truth_path, [_row("2022", "TP", 1.5)])

    summary = evaluate_methodology_readiness(input_path=truth_path, spec_path=spec_path)
    report = render_report(summary)

    assert "PBO is not computable honestly from the two selected primary cohorts alone" in report
    assert "Historical matrix effective_N is available only as a separate diagnostic" in report
    assert "No alpha promotion or live improvement is authorized" in report


def _write_spec(path):
    payload = {
        "schema_version": "truth_layer_controlled_hypotheses_v1",
        "promotion_verdict_allowed": False,
        "registry_markdown": "test.md",
        "selection_status": "post_diagnostic_same_dataset_followup",
        "methodology_gates": {
            "required_for_any_promotion_claim": {
                "cumulative_program_trial_count_floor": 200
            }
        },
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


def _row(year, outcome, realized, **overrides):
    row = {
        "opportunity_key": f"USDJPY|tokyo|{year}|{outcome}",
        "symbol": "USDJPY",
        "session": "tokyo",
        "year": year,
        "candle_close_utc": f"{year}-01-03T00:00:00+00:00",
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
        "m1_refined_exit_time": f"{year}-01-03T00:30:00+00:00",
        "m5_gap_count_in_horizon": 0,
    }
    row.update(overrides)
    return row


def _write_jsonl(path, rows):
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
