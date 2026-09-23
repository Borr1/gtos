from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from src.components.orchestrator import SessionOrchestrator
from src.components.trailing_stop_shadow_logger import (
    TrailingStopShadowTracker,
    write_trailing_stop_shadow_log,
)


def test_trailing_stop_v1_activates_and_locks_break_even_on_reversal():
    tracker = TrailingStopShadowTracker(
        trade_id="t1",
        entry_price=100.0,
        stop_loss=90.0,
        take_profit=130.0,
        direction="LONG",
        sl_distance=10.0,
        activation_r=0.5,
        trail_distance_r=0.5,
        source_evidence={"source_path": "unit-test"},
    )

    assert tracker.update(104.0) is False
    assert tracker.update(105.0) is True
    tracker.update(100.0)
    result = tracker.compute_hypothetical(
        actual_exit_price=90.0,
        actual_r_multiple=-1.0,
    )

    assert result is not None
    assert result["trailing_exit_triggered"] is True
    assert result["hypothetical_trailing_r"] == pytest.approx(0.0)
    assert result["delta_r"] == pytest.approx(1.0)
    assert result["trailing_stop_better"] is True
    assert result["source_evidence"]["source_path"] == "unit-test"


def test_trailing_stop_v1_ratchets_for_long_and_never_widens():
    tracker = TrailingStopShadowTracker(
        trade_id="t2",
        entry_price=100.0,
        stop_loss=90.0,
        take_profit=140.0,
        direction="LONG",
        sl_distance=10.0,
    )

    tracker.update(105.0)
    assert tracker.trailing_stop_r == pytest.approx(0.0)
    tracker.update(120.0)
    assert tracker.trailing_stop_r == pytest.approx(1.5)
    tracker.update(116.0)
    assert tracker.trailing_stop_r == pytest.approx(1.5)
    tracker.update(114.0)

    result = tracker.compute_hypothetical(
        actual_exit_price=114.0,
        actual_r_multiple=1.4,
    )

    assert result is not None
    assert result["hypothetical_trailing_r"] == pytest.approx(1.5)
    assert result["delta_r"] == pytest.approx(0.1)


def test_trailing_stop_v1_short_direction():
    tracker = TrailingStopShadowTracker(
        trade_id="t3",
        entry_price=100.0,
        stop_loss=110.0,
        take_profit=70.0,
        direction="SHORT",
        sl_distance=10.0,
    )

    assert tracker.update(95.0) is True
    tracker.update(80.0)
    assert tracker.trailing_stop_price == pytest.approx(85.0)
    tracker.update(86.0)
    result = tracker.compute_hypothetical(
        actual_exit_price=86.0,
        actual_r_multiple=1.4,
    )

    assert result is not None
    assert result["hypothetical_trailing_r"] == pytest.approx(1.5)
    assert result["trailing_exit_triggered"] is True


def test_trailing_stop_shadow_log_writer(tmp_path):
    path = tmp_path / "trailing.jsonl"
    entry = {
        "trade_id": "t4",
        "actual_r_multiple": -1.0,
        "hypothetical_trailing_r": 0.0,
        "delta_r": 1.0,
    }

    write_trailing_stop_shadow_log(entry, log_path=str(path))

    assert json.loads(path.read_text(encoding="utf-8")) == entry


def test_orchestrator_initializes_trailing_stop_shadow_from_config():
    orch = SessionOrchestrator.__new__(SessionOrchestrator)
    orch.config = {
        "shadow_loggers": {
            "partial_close_shadow_logger": {"enabled": False},
            "trailing_stop_v1_shadow_logger": {
                "enabled": True,
                "activation_r": 0.75,
                "trail_distance_r": 0.25,
                "source_path": "unit-source",
                "source_rows_represented": 2428,
            },
        }
    }
    trade_state = SimpleNamespace(
        trade_id="t5",
        entry_price=100.0,
        stop_loss=90.0,
        take_profit=130.0,
        direction="LONG",
        sl_distance=10.0,
        entry_time="2026-05-19T00:00:00+00:00",
    )

    orch._init_trade_tracking(trade_state)

    tracker = orch._trailing_stop_shadow_tracker
    assert tracker is not None
    assert tracker.activation_r == pytest.approx(0.75)
    assert tracker.trail_distance_r == pytest.approx(0.25)
    assert tracker.source_evidence["source_path"] == "unit-source"
    assert tracker.source_evidence["source_rows_represented"] == 2428


def test_orchestrator_can_disable_trailing_stop_shadow_tracker():
    orch = SessionOrchestrator.__new__(SessionOrchestrator)
    orch.config = {
        "shadow_loggers": {
            "partial_close_shadow_logger": {"enabled": False},
            "trailing_stop_v1_shadow_logger": {"enabled": False},
        }
    }
    trade_state = SimpleNamespace(
        trade_id="t6",
        entry_price=100.0,
        stop_loss=90.0,
        take_profit=130.0,
        direction="LONG",
        sl_distance=10.0,
        entry_time="2026-05-19T00:00:00+00:00",
    )

    orch._init_trade_tracking(trade_state)

    assert orch._trailing_stop_shadow_tracker is None
