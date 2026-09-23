from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil
import uuid

import pytest

from scripts.run_raw_ohlc_path_ablation_v0 import registered_policies, resolve_policy_outcome
from scripts.run_raw_ohlc_path_ablation_v1_mtf import PathWindow, resolve_policy_outcome_mtf
from scripts.run_raw_ohlc_path_scaling_v2_levels import (
    build_structural_path_features,
    candidate_from_price,
    confirmed_swings_as_of,
    registered_structural_policies,
    registered_v2_policies,
    render_report,
    resolve_structural_policy_outcome,
)
from src.research_infra.dumb_baseline import MechanicalSetup


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"path_scaling_v2_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_confirmed_swing_is_not_available_before_right_side_lag():
    setup = _setup_long()
    rows = [
        _bar(1, open=108, high=110, low=105, close=108),
        _bar(2, open=108, high=109, low=104, close=107),
        _bar(3, open=107, high=108, low=101, close=106),
        _bar(4, open=106, high=109, low=103, close=108),
        _bar(5, open=108, high=112, low=104, close=111),
    ]

    before_confirmation = confirmed_swings_as_of(rows, current_index=3)
    after_confirmation = confirmed_swings_as_of(rows, current_index=4)
    features = build_structural_path_features(setup, rows, selected_timeframe="M1")

    assert not [swing for swing in before_confirmation if swing.swing_type == "low" and swing.index == 2]
    assert [swing for swing in after_confirmation if swing.swing_type == "low" and swing.index == 2]
    assert not _selector_ids(features.candidates_by_index.get(3, []), "PROTECTED_CONFIRMED_SWING")
    assert _selector_ids(features.candidates_by_index.get(4, []), "PROTECTED_CONFIRMED_SWING")


def test_structural_lock_activates_on_next_row_not_signal_row():
    policy = _struct_policy("STRUCT_LIQUIDITY_RUN_V2")
    setup = _setup_long()
    rows = [
        _bar(1, open=105, high=105, low=99, close=101),
        _bar(2, open=101, high=125, low=101, close=122),
        _bar(3, open=122, high=124, low=105, close=106),
    ]

    outcome = resolve_structural_policy_outcome(setup, _window(rows), policy=policy)

    assert outcome.outcome == "LOCK_STOP"
    assert outcome.gross_r == 0.5
    assert outcome.locks_triggered[0]["selector_id"] == "PATH_HIGH_LOW_RUN"


def test_candidate_floor_rejects_nonpositive_or_not_behind_price():
    setup = _setup_long()

    below_entry = candidate_from_price(
        setup,
        selector_id="PATH_HIGH_LOW_RUN",
        event_type="test",
        price=95,
        current_close=110,
        source_index=1,
        source_time=None,
        confirmed_index=1,
        confirmed_time=None,
        selected_timeframe="M1",
    )
    above_close = candidate_from_price(
        setup,
        selector_id="PATH_HIGH_LOW_RUN",
        event_type="test",
        price=115,
        current_close=110,
        source_index=1,
        source_time=None,
        confirmed_index=1,
        confirmed_time=None,
        selected_timeframe="M1",
    )

    assert below_entry is None
    assert above_close is None


def test_short_structural_liquidity_lock_is_symmetric():
    policy = _struct_policy("STRUCT_LIQUIDITY_RUN_V2")
    setup = _setup_short()
    rows = [
        _bar(1, open=95, high=101, low=95, close=99),
        _bar(2, open=99, high=99, low=78, close=78),
        _bar(3, open=78, high=95, low=77, close=94),
    ]

    outcome = resolve_structural_policy_outcome(setup, _window(rows), policy=policy)

    assert outcome.outcome == "LOCK_STOP"
    assert outcome.gross_r == 0.5
    assert outcome.locks_triggered[0]["selector_id"] == "PATH_HIGH_LOW_RUN"


def test_v2_fixed_r_comparator_reproduces_v1_mtf_fallback():
    policy = _v2_policy("PATH_LOCK_HALF_GAIN_V0")
    setup = _setup_long()
    rows = [
        _bar(15, open=105, high=101, low=99, close=100.5),
        _bar(30, open=101, high=121, low=101, close=120),
        _bar(45, open=120, high=115, low=110, close=111),
    ]
    rows_by_tf = {"M1": [], "M5": [], "M15": rows}

    v0 = resolve_policy_outcome(setup, rows, policy=policy)
    v1 = resolve_policy_outcome_mtf(setup, rows_by_tf, policy=policy)

    assert v1.selected_timeframe == "M15"
    assert v1.outcome == v0.outcome == "LOCK_STOP"
    assert v1.gross_r == v0.gross_r == 1.0


def test_report_keeps_no_promotion_and_required_sections():
    report = render_report(
        {
            "created_at_utc": "2026-05-02T00:00:00+00:00",
            "replay_spec_path": "replay.json",
            "v2_spec_path": "v2.json",
            "v2_protocol_path": "protocol.md",
            "v1_failure_forensics_path": "v1.md",
            "promotion_verdict": "NO_PROMOTION_VERDICT",
            "source_scope": "FULL_AVAILABLE_CORPUS",
            "rows_replayed": 1,
            "take_rows_seen": 1,
            "setup_ok_rows": 1,
            "include_blocked_controls": True,
            "first_take_clock": "2026-01-01T00:15:00+00:00",
            "last_take_clock": "2026-01-01T00:15:00+00:00",
            "coverage_diagnostics": {"m1_available_windows": 1, "lower_tf_start_violations": 0},
            "structural_selector_policy": {"swing_confirmation_lag_bars": 2},
            "policies": [],
            "synthesis": [{"question": "Does this promote?", "answer": "No."}],
            "variant_summary": [],
            "samebar_stress_summary": [],
            "group_summary": [],
            "cohort_summary": [],
            "selector_fire_summary": [],
            "structural_event_census": [],
            "structural_diagnostic_census": [],
            "pairwise_vs_j46": [],
            "pairwise_vs_fixed_r": [],
            "pbo_diagnostic": {"pbo": None, "status": "insufficient", "promotion_usable": False},
            "effective_n_diagnostic": {"promotion_usable": False, "exit_policy_effective_n": {}},
            "ambiguity_ledger": [{"item": "Same-bar", "status": "QUANTIFIED", "detail": "none"}],
            "opened_questions": [{"question": "Any blockers?", "status": "ANSWERED", "detail": "none"}],
            "next_steps": [{"rank": "1", "next_step": "Review", "reason": "diagnostic"}],
        }
    )

    assert "NO_PROMOTION_VERDICT" in report
    assert "## Same-Bar Stress Summary" in report
    assert "## Selector Fire Summary" in report
    assert "## Ambiguity Ledger" in report
    assert "## Opened Questions" in report
    assert "## Next Steps" in report


def _struct_policy(variant_id):
    return next(policy for policy in registered_structural_policies() if policy.variant_id == variant_id)


def _v2_policy(variant_id):
    return next(policy for policy in registered_v2_policies() if policy.variant_id == variant_id)


def _setup_long():
    return MechanicalSetup(
        cand_id="test-long",
        symbol="XAUUSD",
        candle_close_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        side="LONG",
        framework="ob_retest",
        ob_high=100.0,
        ob_low=90.0,
        entry=100.0,
        sl=90.0,
        tp=160.0,
        rr=6.0,
    )


def _setup_short():
    return MechanicalSetup(
        cand_id="test-short",
        symbol="XAUUSD",
        candle_close_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        side="SHORT",
        framework="ob_retest",
        ob_high=110.0,
        ob_low=100.0,
        entry=100.0,
        sl=110.0,
        tp=40.0,
        rr=6.0,
    )


def _window(rows):
    return PathWindow(
        selected_timeframe="M1",
        selected_rows=rows,
        fallback_reason=None,
        row_counts={"M1": len(rows), "M5": 0, "M15": 0},
        first_close={"M1": rows[0]["time"].isoformat(), "M5": None, "M15": None},
        last_close={"M1": rows[-1]["time"].isoformat(), "M5": None, "M15": None},
    )


def _bar(minutes, *, open, high, low, close):
    return {
        "time": datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=minutes),
        "open": open,
        "high": high,
        "low": low,
        "close": close,
    }


def _selector_ids(candidates, selector_id):
    return [candidate for candidate in candidates if candidate.selector_id == selector_id]
