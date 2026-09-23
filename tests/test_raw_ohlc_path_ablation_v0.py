from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil
import uuid

import pytest

from scripts.run_raw_ohlc_path_ablation_v0 import (
    PathOutcome,
    VariantStats,
    first_row_after,
    registered_policies,
    render_report,
    resolve_policy_outcome,
)
from src.research_infra.dumb_baseline import MechanicalSetup


@pytest.fixture
def tmp_path():
    """Local tmp_path replacement for this Windows sandbox.

    Pytest's built-in tmp_path uses restrictive directory permissions that are
    not readable in the current Codex sandbox. Several Phase 3 research tests
    use this local-fixture pattern; it still gives conftest autouse fixtures a
    per-test scratch path without touching production runtime directories.
    """
    path = Path(".test_tmp") / f"path_ablation_v0_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_j46_j49_hits_six_r_after_three_r_lock():
    policy = _policy("J46_J49_ONLY")
    setup = _setup()
    rows = [
        _bar(15, high=101, low=99, close=100.5),
        _bar(30, high=135, low=110, close=130),
        _bar(45, high=161, low=130, close=160),
    ]

    outcome = resolve_policy_outcome(setup, rows, policy=policy)

    assert outcome.outcome == "TP"
    assert outcome.gross_r == 6.0
    assert outcome.locks_triggered == [{"trigger_r": 3.0, "floor_r": 0.0}]


def test_j46_j49_can_lock_then_stop_at_be():
    policy = _policy("J46_J49_ONLY")
    setup = _setup()
    rows = [
        _bar(15, high=101, low=99, close=100.5),
        _bar(30, high=135, low=95, close=130),
        _bar(45, high=120, low=100, close=105),
    ]

    outcome = resolve_policy_outcome(setup, rows, policy=policy)

    assert outcome.outcome == "BE_STOP"
    assert outcome.gross_r == 0.0
    assert outcome.max_locked_floor_r == 0.0


def test_path_lock_half_gain_locks_profit_without_reentry():
    policy = _policy("PATH_LOCK_HALF_GAIN_V0")
    setup = _setup()
    rows = [
        _bar(15, high=101, low=99, close=100.5),
        _bar(30, high=121, low=101, close=120),
        _bar(45, high=115, low=110, close=111),
    ]

    outcome = resolve_policy_outcome(setup, rows, policy=policy)

    assert outcome.outcome == "LOCK_STOP"
    assert outcome.gross_r == 1.0
    assert outcome.max_locked_floor_r == 1.0


def test_same_bar_fill_and_path_event_is_unresolved():
    policy = _policy("PATH_LOCK_EARLY_BE_V0")
    setup = _setup()
    rows = [_bar(15, high=112, low=99, close=110)]

    outcome = resolve_policy_outcome(setup, rows, policy=policy)

    assert outcome.outcome == "SAME_BAR"
    assert outcome.gross_r is None
    assert outcome.skip_reason == "FILL_AND_PATH_EVENT_SAME_BAR"


def test_path_replay_starts_after_setup_candle_close():
    policy = _policy("BASE_RAW_FIXED_TP")
    setup = _setup()
    rows = [
        _bar(0, high=200, low=50, close=150),
        _bar(15, high=101, low=99, close=100.5),
        _bar(30, high=116, low=100, close=115),
    ]

    assert first_row_after(rows, setup.candle_close_time) == 1

    outcome = resolve_policy_outcome(setup, rows, policy=policy)

    assert outcome.outcome == "TP"
    assert outcome.bars_to_fill == 1


def test_policy_losses_are_capped_at_initial_one_r():
    rows = [
        _bar(15, high=101, low=99, close=100.5),
        _bar(30, high=101, low=89, close=90),
    ]

    for policy in registered_policies():
        outcome = resolve_policy_outcome(_setup(), rows, policy=policy)
        assert outcome.outcome == "SL"
        assert outcome.gross_r == -1.0


def test_variant_stats_apply_round_turn_cost_sensitivity():
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

    assert stats.resolved_n == 1
    assert stats.net_returns_by_cost[0.0] == [1.5]
    assert stats.net_returns_by_cost[0.05] == [1.45]


def test_report_keeps_no_promotion_and_synthesis_sections():
    report = render_report(
        {
            "created_at_utc": "2026-05-01T00:00:00+00:00",
            "spec_path": "spec.json",
            "promotion_verdict": "NO_PROMOTION_VERDICT",
            "source_scope": "FULL_AVAILABLE_CORPUS",
            "rows_replayed": 1,
            "take_rows_seen": 1,
            "setup_ok_rows": 1,
            "path_timeframe": "M15",
            "include_blocked_controls": True,
            "first_take_clock": "2026-01-01T00:15:00+00:00",
            "last_take_clock": "2026-01-01T00:15:00+00:00",
            "cost_model": {"unit": "R per completed round turn"},
            "policies": [],
            "synthesis": [{"question": "Does this promote?", "answer": "No."}],
            "variant_summary": [],
            "group_summary": [],
            "cohort_summary": [],
            "pbo_diagnostic": {"pbo": None, "status": "insufficient", "promotion_usable": False},
            "effective_n_diagnostic": {"promotion_usable": False, "exit_policy_effective_n": {}},
            "ambiguity_ledger": [{"item": "Cost model", "status": "SENSITIVITY", "detail": "not measured"}],
            "next_steps": [{"rank": "1", "next_step": "Refine", "reason": "diagnostic"}],
        }
    )

    assert "NO_PROMOTION_VERDICT" in report
    assert "## Direct Answers" in report
    assert "## Ambiguity Ledger" in report
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
