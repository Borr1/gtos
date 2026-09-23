import json
from pathlib import Path
import shutil
import uuid

import pytest

from scripts.analyze_raw_ohlc_path_ablation_v1_failure_forensics import (
    render_report,
    run_failure_forensics,
)


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"path_ablation_v1_failure_forensics_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_failure_forensics_classifies_truncation_rescue_and_missed_path(tmp_path):
    event_log = tmp_path / "events.jsonl"
    rows = [
        _event("e1", "J46_J49_ONLY", "TP", 6.0, mfe=6.2, mae=-0.4),
        _event(
            "e1",
            "PATH_LOCK_HALF_GAIN_V0",
            "LOCK_STOP",
            1.5,
            mfe=6.2,
            mae=-0.4,
            locks=[{"trigger_r": 3.0, "floor_r": 1.5}],
        ),
        _event("e2", "J46_J49_ONLY", "SL", -1.0, mfe=2.1, mae=-1.1),
        _event(
            "e2",
            "PATH_LOCK_HALF_GAIN_V0",
            "LOCK_STOP",
            0.5,
            mfe=2.1,
            mae=-1.1,
            locks=[{"trigger_r": 1.5, "floor_r": 0.5}],
        ),
        _event("e3", "J46_J49_ONLY", "TIMEOUT", -0.2, mfe=3.0, mae=-0.8),
        _event("e3", "PATH_LOCK_HALF_GAIN_V0", "SL", -1.0, mfe=3.0, mae=-1.0),
    ]
    event_log.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    summary = run_failure_forensics(event_log_path=event_log)

    half = _variant(summary["pairwise_variant_summary"], "PATH_LOCK_HALF_GAIN_V0")
    assert half["paired_resolved_n"] == 3
    assert half["j46_better_n"] == 2
    assert half["lock_better_n"] == 1
    assert half["truncation_n"] == 1
    assert half["truncation_lost_r"] == 4.5
    assert half["rescued_to_positive_n"] == 1

    mechanism = _mechanism(summary["mechanism_group_summary"], "PATH_LOCK_HALF_GAIN_V0", "all_enabled")
    assert mechanism["winner_truncated_but_positive_n"] == 1
    assert mechanism["lock_rescued_loss_to_positive_n"] == 1
    assert mechanism["lock_failed_to_improve_j46_nonpositive_n"] == 1

    mfe_all = _mfe(summary["mfe_opportunity_summary"], "group", "all_enabled")
    assert mfe_all["j46_nonpositive_n"] == 2
    assert mfe_all["nonpositive_mfe_ge_1.5_n"] == 2
    assert summary["casebook"]["largest_j46_better_examples"]
    assert summary["casebook"]["true_rescue_examples"]
    assert summary["casebook"]["missed_favorable_path_examples"]


def test_samebar_stress_and_mtf_resolution_are_reported(tmp_path):
    event_log = tmp_path / "events.jsonl"
    rows = [
        _event("e1", "J46_J49_ONLY", "SAME_BAR", None, timeframe="M1"),
        _event("e1", "PATH_LOCK_CONSERVATIVE_V0", "TP", 2.0, timeframe="M1"),
        _event("e2", "J46_J49_ONLY", "TP", 1.0, timeframe="M5"),
        _event("e2", "PATH_LOCK_CONSERVATIVE_V0", "SAME_BAR", None, timeframe="M5"),
    ]
    event_log.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    summary = run_failure_forensics(event_log_path=event_log)

    mtf = _variant(summary["mtf_resolution_summary"], "J46_J49_ONLY")
    assert mtf["v0_samebar_n"] == 2
    assert mtf["v1_samebar_n"] == 1
    assert mtf["v0_samebar_resolved_by_mtf_n"] == 1

    stress = [
        row
        for row in summary["samebar_stress_delta_summary"]
        if row["treatment"] == "samebar_pessimistic" and row["group"] == "target_cohorts"
    ][0]
    assert stress["j46_net_mean_r_cost_0.05"] == -0.05
    assert stress["best_lock_variant"] == "PATH_LOCK_CONSERVATIVE_V0"
    assert stress["best_lock_minus_j46"] == 0.5

    unresolved = _variant(summary["unresolved_pair_summary"], "PATH_LOCK_CONSERVATIVE_V0")
    assert unresolved["j46_resolved_lock_samebar"] == 1
    assert unresolved["lock_resolved_j46_samebar"] == 1


def test_failure_forensics_report_contains_closure_sections(tmp_path):
    event_log = tmp_path / "events.jsonl"
    rows = [
        _event("e1", "J46_J49_ONLY", "TP", 1.0),
        _event("e1", "PATH_LOCK_HALF_GAIN_V0", "LOCK_STOP", 0.5, locks=[{"trigger_r": 1.5, "floor_r": 0.5}]),
    ]
    event_log.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    report = render_report(run_failure_forensics(event_log_path=event_log))

    assert "NO_PROMOTION_VERDICT" in report
    assert "## Direct Answers" in report
    assert "## What Worked" in report
    assert "## What Failed" in report
    assert "## Root Cause Summary" in report
    assert "## Casebook" in report
    assert "## Unanswered Questions Status" in report
    assert "## Ambiguity Ledger" in report
    assert "## Opened Questions" in report
    assert "## Limitations" in report
    assert "## Synthesis" in report


def _event(
    event_key,
    variant,
    outcome,
    gross_r,
    *,
    timeframe="M15",
    cohort="USDJPY|tokyo|bearish|D1",
    role="primary_controlled_child",
    mfe=1.0,
    mae=-0.5,
    locks=None,
):
    return {
        "schema_version": "raw_ohlc_path_ablation_v1_mtf_event",
        "event_key": event_key,
        "variant_id": variant,
        "v0_outcome": "SAME_BAR",
        "v1_outcome": outcome,
        "v1_gross_r": gross_r,
        "v1_selected_timeframe": timeframe,
        "raw_cohort_key": cohort,
        "role": role,
        "mfe_r": mfe,
        "mae_r": mae,
        "locks_triggered": locks or [],
        "max_locked_floor_r": locks[-1]["floor_r"] if locks else None,
        "bars_in_trade": 4,
    }


def _variant(rows, variant):
    return next(row for row in rows if row["variant_id"] == variant)


def _mechanism(rows, variant, key):
    return next(row for row in rows if row["variant_id"] == variant and row["key"] == key)


def _mfe(rows, scope, key):
    return next(row for row in rows if row["scope"] == scope and row["key"] == key)
