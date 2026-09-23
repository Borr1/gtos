import json
import shutil
import uuid
from pathlib import Path

import pytest

from scripts.evaluate_truth_layer_controlled_hypotheses import (
    evaluate_controlled_hypotheses,
    load_hypothesis_spec,
    render_report,
)


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"truth_layer_controlled_hypotheses_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_population_filter_keeps_no_entry_and_excludes_unsafe_rows(tmp_path):
    truth_path = tmp_path / "truth.jsonl"
    spec_path = tmp_path / "spec.json"
    _write_spec(spec_path)
    rows = [
        _row("2022", "TP", 1.5, opportunity_key="tp"),
        _row("2022", "SL", -1.0, opportunity_key="sl"),
        _row("2022", "NO_ENTRY", None, opportunity_key="no-entry"),
        _row("2022", "SAME_BAR", None, opportunity_key="same-bar"),
        _row("2022", "TP", 1.5, truth_confidence="MEDIUM", opportunity_key="medium"),
        _row(
            "2022",
            "TP",
            1.5,
            opportunity_key="gap-before",
            lower_tf_gap_count_in_horizon=1,
            lower_tf_first_gap_utc="2022-01-03T00:01:00+00:00",
            m1_gap_count_in_horizon=1,
            m1_first_gap_utc="2022-01-03T00:01:00+00:00",
            m1_refined_exit_time="2022-01-03T00:30:00+00:00",
        ),
        _row(
            "2022",
            "TP",
            1.5,
            opportunity_key="gap-after",
            lower_tf_gap_count_in_horizon=1,
            lower_tf_first_gap_utc="2022-01-03T01:00:00+00:00",
            m1_gap_count_in_horizon=1,
            m1_first_gap_utc="2022-01-03T01:00:00+00:00",
            m1_refined_exit_time="2022-01-03T00:30:00+00:00",
        ),
    ]
    _write_jsonl(truth_path, rows)

    summary = evaluate_controlled_hypotheses(input_path=truth_path, spec_path=spec_path)

    hypothesis = summary["hypotheses"][0]
    included = hypothesis["included"]
    assert summary["verdict"] == "NO_PROMOTION_VERDICT"
    assert included["population_rows"] == 4
    assert included["resolved_r_n"] == 3
    assert included["mean_r"] == pytest.approx(0.666667)
    assert included["no_entry"] == 1
    assert included["no_entry_rate_population"] == pytest.approx(0.25)
    assert included["gap_after_resolution"] == 1
    assert hypothesis["excluded_counts"]["truth_outcome_excluded"] == 1
    assert hypothesis["excluded_counts"]["truth_confidence_not_allowed"] == 1
    assert hypothesis["excluded_counts"]["not_resolution_safe"] == 2


def test_report_declares_same_dataset_and_methodology_block(tmp_path):
    truth_path = tmp_path / "truth.jsonl"
    spec_path = tmp_path / "spec.json"
    _write_spec(spec_path)
    _write_jsonl(
        truth_path,
        [
            _row("2022", "TP", 1.5, opportunity_key="2022-tp"),
            _row("2023", "TP", 1.5, opportunity_key="2023-tp"),
            _row("2024", "TP", 1.5, opportunity_key="2024-tp"),
        ],
    )

    summary = evaluate_controlled_hypotheses(input_path=truth_path, spec_path=spec_path)
    report = render_report(summary)

    assert "NO_PROMOTION_VERDICT" in report
    assert "selected after same-dataset diagnostics" in report
    assert "DSR-corrected p, PBO, and true effective_N are not computed here" in report
    assert "must not be used as alpha promotion proof" in report


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
