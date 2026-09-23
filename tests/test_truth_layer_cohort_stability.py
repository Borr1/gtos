import json
import shutil
import uuid
from pathlib import Path

import pytest

from scripts.analyze_truth_layer_cohort_stability import (
    analyze_cohort_stability,
    parse_cohort_key,
    render_report,
)


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"truth_layer_cohort_stability_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_parse_cohort_key_preserves_regime_delimiter():
    assert parse_cohort_key("XAUUSD|ny|bullish|D1") == (
        "XAUUSD",
        "ny",
        "bullish|D1",
    )


def test_clean_scope_excludes_ambiguous_outcomes_but_keeps_gap_diagnostics(tmp_path):
    truth_path = tmp_path / "truth.jsonl"
    cohort_path = tmp_path / "cohorts.json"
    _write_cohorts(cohort_path, ["XAUUSD|ny|bullish|D1"])
    rows = [
        _row("2022", "TP", 1.5, opportunity_key="a"),
        _row("2022", "SL", -1.0, opportunity_key="b"),
        _row("2022", "SAME_BAR", None, opportunity_key="c"),
        _row(
            "2022",
            "TP",
            1.5,
            opportunity_key="d",
            lower_tf_gap_count_in_horizon=1,
            lower_tf_first_gap_utc="2022-01-03T01:00:00+00:00",
            m1_gap_count_in_horizon=1,
            m1_first_gap_utc="2022-01-03T01:00:00+00:00",
            m1_refined_exit_time="2022-01-03T00:15:00+00:00",
        ),
        _row("2022", "NO_ENTRY", None, opportunity_key="e"),
    ]
    _write_jsonl(truth_path, rows)

    summary = analyze_cohort_stability(
        input_path=truth_path,
        cohort_path=cohort_path,
        min_year_resolved_n=1,
        min_total_resolved_n=1,
    )

    cohort = summary["cohorts"][0]
    assert cohort["scopes"]["HIGH_ONLY"]["resolved_r_n"] == 3
    assert cohort["scopes"]["HIGH_ONLY"]["same_bar"] == 1
    assert cohort["scopes"]["HIGH_ONLY"]["gap_rows"] == 1
    assert cohort["scopes"]["CLEAN_HIGH"]["resolved_r_n"] == 3
    assert cohort["scopes"]["CLEAN_HIGH"]["same_bar"] == 0
    assert cohort["scopes"]["CLEAN_HIGH"]["gap_rows"] == 1
    assert cohort["scopes"]["CLEAN_HIGH"]["no_entry"] == 1
    assert cohort["scopes"]["RESOLUTION_SAFE_HIGH"]["resolved_r_n"] == 3
    assert cohort["scopes"]["RESOLUTION_SAFE_HIGH"]["gap_after_resolution"] == 1
    assert cohort["scopes"]["ZERO_GAP_HIGH"]["resolved_r_n"] == 2
    assert cohort["scopes"]["ZERO_GAP_HIGH"]["gap_rows"] == 0


def test_stability_classifies_primary_only_when_clean_years_are_positive(tmp_path):
    truth_path = tmp_path / "truth.jsonl"
    cohort_path = tmp_path / "cohorts.json"
    _write_cohorts(cohort_path, ["XAUUSD|ny|bullish|D1"])
    rows = []
    for year in ("2022", "2023", "2024"):
        rows.extend(
            [
                _row(year, "TP", 1.5, opportunity_key=f"{year}-tp-1"),
                _row(year, "TP", 1.5, opportunity_key=f"{year}-tp-2"),
                _row(year, "SL", -1.0, opportunity_key=f"{year}-sl"),
            ]
        )
    _write_jsonl(truth_path, rows)

    summary = analyze_cohort_stability(
        input_path=truth_path,
        cohort_path=cohort_path,
        min_year_resolved_n=3,
        min_total_resolved_n=9,
    )

    treatment = summary["cohorts"][0]["treatment"]
    stability = summary["cohorts"][0]["stability"]["CLEAN_HIGH"]
    assert stability["valid_years"] == 3
    assert stability["positive_years"] == 3
    assert treatment["recommended_treatment"] == "PRIMARY_CONTROLLED_RESEARCH"


def test_report_declares_post_diagnostic_boundary_and_no_promotion(tmp_path):
    truth_path = tmp_path / "truth.jsonl"
    cohort_path = tmp_path / "cohorts.json"
    _write_cohorts(cohort_path, ["XAUUSD|ny|bullish|D1"])
    _write_jsonl(truth_path, [_row("2022", "TP", 1.5)])

    summary = analyze_cohort_stability(
        input_path=truth_path,
        cohort_path=cohort_path,
        min_year_resolved_n=1,
        min_total_resolved_n=1,
    )
    report = render_report(summary)

    assert "selected after seeing the diagnostic report" in report
    assert "DSR-corrected p, PBO, and true effective_N are not computed here" in report
    assert "Selected-source lower-timeframe gap counts remain visible as diagnostics" in report
    assert "`RESOLUTION_SAFE_*` scopes additionally exclude selected-source gaps" in report
    assert "`ZERO_GAP_*` scopes additionally require zero selected-source lower-timeframe gap counts" in report
    assert "No AI/API calls are made" in report


def _row(year, outcome, realized, **overrides):
    row = {
        "opportunity_key": f"XAUUSD|ny|{year}|{outcome}",
        "symbol": "XAUUSD",
        "session": "ny",
        "year": year,
        "candle_close_utc": f"{year}-01-03T00:00:00+00:00",
        "truth_regime": "bullish|D1",
        "truth_outcome": outcome,
        "truth_realized_r": realized,
        "truth_failure_bucket": "SUCCESS_TP_FIRST" if outcome == "TP" else "FAIL_STOP_FIRST",
        "truth_confidence": "HIGH",
        "truth_source_timeframe": "M1",
        "lower_tf_gap_count_in_horizon": 0,
        "lower_tf_first_gap_utc": None,
        "would_send_ai": True,
        "mechanical_setup_status": "OK",
        "mechanical_side": "LONG",
        "ai_call_attempted": False,
        "ai_call_count": 0,
        "m1_gap_count_in_horizon": 0,
        "m1_first_gap_utc": None,
        "m1_refined_exit_time": f"{year}-01-03T00:30:00+00:00",
        "m5_gap_count_in_horizon": 0,
    }
    row.update(overrides)
    return row


def _write_cohorts(path, keys):
    payload = {
        "schema_version": "test_cohorts_v1",
        "selection_status": "post_diagnostic_followup_v1",
        "interpretation_boundary": ["test"],
        "cohorts": [{"cohort_key": key, "role": "test"} for key in keys],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_jsonl(path, rows):
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
