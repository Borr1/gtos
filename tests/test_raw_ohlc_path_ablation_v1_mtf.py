from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil
import uuid

import pytest

from scripts.run_raw_ohlc_path_ablation_v0 import (
    PathOutcome,
    VariantStats,
    registered_policies,
    resolve_policy_outcome,
)
from scripts.run_raw_ohlc_path_ablation_v1_mtf import (
    render_report,
    resolve_policy_outcome_mtf,
    rows_in_window,
    select_path_window,
)
from src.research_infra.dumb_baseline import MechanicalSetup


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"path_ablation_v1_mtf_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_lower_timeframe_rows_start_strictly_after_setup_close():
    setup = _setup()
    rows = [
        _bar(0, high=200, low=50, close=150),
        _bar(1, high=101, low=99, close=100.5),
        _bar(16, high=116, low=100, close=115),
    ]

    selected = rows_in_window(rows, start=setup.candle_close_time, end=setup.candle_close_time + timedelta(minutes=15))

    assert [row["time"] for row in selected] == [setup.candle_close_time + timedelta(minutes=1)]


def test_same_bar_m15_ambiguity_resolved_by_m1_order():
    policy = _policy("BASE_RAW_FIXED_TP")
    setup = _setup()
    rows_by_tf = {
        "M15": [_bar(15, high=116, low=99, close=115)],
        "M5": [],
        "M1": [
            _bar(1, high=101, low=99, close=100.5),
            _bar(2, high=116, low=100.5, close=115),
        ],
    }

    v0 = resolve_policy_outcome(setup, rows_by_tf["M15"], policy=policy)
    v1 = resolve_policy_outcome_mtf(setup, rows_by_tf, policy=policy)

    assert v0.outcome == "SAME_BAR"
    assert v1.selected_timeframe == "M1"
    assert v1.outcome == "TP"
    assert v1.gross_r == 1.5


def test_mtf_resolver_falls_back_to_m5_when_m1_unavailable():
    policy = _policy("BASE_RAW_FIXED_TP")
    setup = _setup()
    rows_by_tf = {
        "M15": [_bar(15, high=116, low=99, close=115)],
        "M5": [
            _bar(5, high=101, low=99, close=100.5),
            _bar(10, high=116, low=100.5, close=115),
        ],
        "M1": [],
    }

    outcome = resolve_policy_outcome_mtf(setup, rows_by_tf, policy=policy)

    assert outcome.selected_timeframe == "M5"
    assert outcome.fallback_reason == "M1_UNAVAILABLE_IN_POST_DECISION_WINDOW"
    assert outcome.outcome == "TP"


def test_future_lower_timeframe_rows_are_not_used_for_pending_fill():
    policy = _policy("BASE_RAW_FIXED_TP")
    setup = _setup()
    far_future = setup.candle_close_time + timedelta(minutes=(96 * 15) + 1)
    rows_by_tf = {
        "M15": [_bar(15, high=104, low=101, close=102)],
        "M5": [],
        "M1": [
            {"time": far_future, "open": 100, "high": 116, "low": 99, "close": 115},
        ],
    }

    outcome = resolve_policy_outcome_mtf(setup, rows_by_tf, policy=policy)

    assert outcome.selected_timeframe == "M15"
    assert outcome.outcome == "NO_ENTRY"


def test_mtf_resolver_falls_back_to_m15_when_lower_timeframes_unavailable():
    policy = _policy("BASE_RAW_FIXED_TP")
    setup = _setup()
    rows_by_tf = {
        "M15": [
            _bar(15, high=101, low=99, close=100.5),
            _bar(30, high=116, low=100, close=115),
        ],
        "M5": [],
        "M1": [],
    }

    v0 = resolve_policy_outcome(setup, rows_by_tf["M15"], policy=policy)
    v1 = resolve_policy_outcome_mtf(setup, rows_by_tf, policy=policy)

    assert v1.selected_timeframe == "M15"
    assert v1.outcome == v0.outcome == "TP"
    assert v1.gross_r == v0.gross_r


def test_j46_j49_unchanged_when_mtf_path_has_no_ambiguity():
    policy = _policy("J46_J49_ONLY")
    setup = _setup()
    rows_by_tf = {
        "M15": [
            _bar(15, high=101, low=99, close=100.5),
            _bar(30, high=135, low=110, close=130),
            _bar(45, high=161, low=130, close=160),
        ],
        "M5": [],
        "M1": [
            _bar(1, high=101, low=99, close=100.5),
            _bar(16, high=135, low=110, close=130),
            _bar(31, high=161, low=130, close=160),
        ],
    }

    v0 = resolve_policy_outcome(setup, rows_by_tf["M15"], policy=policy)
    v1 = resolve_policy_outcome_mtf(setup, rows_by_tf, policy=policy)

    assert v0.outcome == v1.outcome == "TP"
    assert v0.gross_r == v1.gross_r == 6.0
    assert v1.locks_triggered == [{"trigger_r": 3.0, "floor_r": 0.0}]


def test_cost_accounting_remains_round_turn_sensitivity():
    stats = VariantStats()
    stats.add(
        PathOutcome(
            variant_id="TEST",
            outcome="TP",
            gross_r=1.5,
            bars_to_fill=1,
            bars_in_trade=2,
            exit_time="2026-01-01T00:30:00+00:00",
        ),
        cost_scenarios=[0.0, 0.05],
    )

    assert stats.net_returns_by_cost[0.0] == [1.5]
    assert stats.net_returns_by_cost[0.05] == [1.45]


def test_report_keeps_no_promotion_verdict_and_required_sections():
    report = render_report(
        {
            "created_at_utc": "2026-05-02T00:00:00+00:00",
            "replay_spec_path": "replay.json",
            "v1_spec_path": "v1.json",
            "v1_protocol_path": "protocol.md",
            "v0_report_path": "v0.md",
            "promotion_verdict": "NO_PROMOTION_VERDICT",
            "source_scope": "FULL_AVAILABLE_CORPUS",
            "rows_replayed": 1,
            "take_rows_seen": 1,
            "setup_ok_rows": 1,
            "include_blocked_controls": True,
            "first_take_clock": "2026-01-01T00:15:00+00:00",
            "last_take_clock": "2026-01-01T00:15:00+00:00",
            "mtf_resolution_policy": {"path_timeframe_hierarchy": ["M1", "M5", "M15"]},
            "coverage_diagnostics": {"m1_available_windows": 1, "lower_tf_start_violations": 0},
            "cost_model": {"unit": "R per completed round turn"},
            "policies": [],
            "synthesis": [{"question": "Does this promote?", "answer": "No."}],
            "variant_summary": [],
            "v0_m15_variant_summary": [],
            "comparison_summary": [],
            "group_summary": [],
            "group_delta_summary": [],
            "cohort_summary": [],
            "cohort_delta_summary": [],
            "conclusion_changes": [],
            "pbo_diagnostic": {"pbo": None, "status": "insufficient", "promotion_usable": False},
            "effective_n_diagnostic": {"promotion_usable": False, "exit_policy_effective_n": {}},
            "ambiguity_ledger": [{"item": "Same-bar", "status": "CLEAR", "detail": "none"}],
            "opened_questions": [{"question": "Any blockers?", "status": "CLEARED", "detail": "none"}],
            "next_steps": [{"rank": "1", "next_step": "Review", "reason": "diagnostic"}],
        }
    )

    assert "NO_PROMOTION_VERDICT" in report
    assert "## Ambiguity Ledger" in report
    assert "## Opened Questions" in report
    assert "## Next Steps" in report


def _policy(variant_id):
    return next(policy for policy in registered_policies() if policy.variant_id == variant_id)


def _setup():
    return MechanicalSetup(
        cand_id="test",
        symbol="XAUUSD",
        candle_close_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        side="LONG",
        framework="ob_retest",
        ob_high=100.0,
        ob_low=90.0,
        entry=100.0,
        sl=90.0,
        tp=115.0,
        rr=1.5,
    )


def _bar(minutes, *, high, low, close):
    return {
        "time": datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=minutes),
        "open": 100.0,
        "high": high,
        "low": low,
        "close": close,
    }
