import json
from pathlib import Path
import shutil
import uuid

import pytest

from scripts.analyze_raw_ohlc_path_ablation_v1_disposition import (
    render_report,
    run_disposition_analysis,
)


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"path_ablation_v1_disposition_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_disposition_registers_pessimistic_samebar_treatment(tmp_path):
    event_log = tmp_path / "events.jsonl"
    rows = [
        _event("e1", "J46_J49_ONLY", "TP", 1.0, "M1", "USDJPY|tokyo|bearish|D1", "primary_controlled_child"),
        _event("e1", "PATH_LOCK_CONSERVATIVE_V0", "SAME_BAR", None, "M1", "USDJPY|tokyo|bearish|D1", "primary_controlled_child"),
        _event("e2", "J46_J49_ONLY", "SAME_BAR", None, "M15", "GBPUSD|london|bearish|H4+H1_consensus", "negative_control"),
        _event("e2", "PATH_LOCK_CONSERVATIVE_V0", "TP", 2.0, "M15", "GBPUSD|london|bearish|H4+H1_consensus", "negative_control"),
    ]
    event_log.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    summary = run_disposition_analysis(event_log_path=event_log)

    assert summary["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert summary["v1_final_verdict"] == "REJECTED_FOR_EXIT_POLICY_PROMOTION"
    samebar = summary["samebar_breakdown"]
    assert samebar["policy_event_rows_by_timeframe"] == {"M1": 1, "M15": 1}
    pessimistic = [
        row
        for row in summary["treatment_variant_summary"]
        if row["treatment"] == "samebar_pessimistic"
    ]
    by_variant = {row["variant_id"]: row for row in pessimistic}
    assert by_variant["J46_J49_ONLY"]["n"] == 2
    assert by_variant["J46_J49_ONLY"]["net_sum_r_cost_0.05"] == -0.1
    assert by_variant["PATH_LOCK_CONSERVATIVE_V0"]["n"] == 2
    assert by_variant["PATH_LOCK_CONSERVATIVE_V0"]["net_sum_r_cost_0.05"] == 0.9


def test_final_report_contains_closed_questions_and_synthesis(tmp_path):
    event_log = tmp_path / "events.jsonl"
    rows = [
        _event("e1", "J46_J49_ONLY", "TP", 1.0, "M1", "USDJPY|tokyo|bearish|D1", "primary_controlled_child"),
        _event("e1", "PATH_LOCK_HALF_GAIN_V0", "SAME_BAR", None, "M1", "USDJPY|tokyo|bearish|D1", "primary_controlled_child"),
    ]
    event_log.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    summary = run_disposition_analysis(event_log_path=event_log)

    report = render_report(summary)

    assert "NO_PROMOTION_VERDICT" in report
    assert "REJECTED_FOR_EXIT_POLICY_PROMOTION" in report
    assert "## Closed Questions" in report
    assert "## Ambiguity Ledger" in report
    assert "## Synthesis" in report


def _event(event_key, variant, outcome, gross_r, timeframe, cohort_key, role):
    return {
        "schema_version": "raw_ohlc_path_ablation_v1_mtf_event",
        "event_key": event_key,
        "variant_id": variant,
        "v0_outcome": "SAME_BAR" if outcome != "SAME_BAR" else "SAME_BAR",
        "v1_outcome": outcome,
        "v1_gross_r": gross_r,
        "v1_selected_timeframe": timeframe,
        "raw_cohort_key": cohort_key,
        "role": role,
    }
