"""HARD_OFF + occupancy-script: writer refuses asia_pdl even if inbox APPROVE."""
from __future__ import annotations

from datetime import datetime, timezone

from src.components.ultimate_book.minimal_size import (
    F5_HARD_OFF_SLEEVES,
    F5_NAMESPACE,
    f5_hard_off_sleeve_reason,
    f5_standing_hold_reason,
)


def test_asia_pdl_is_hard_off_even_when_vacant(monkeypatch):
    monkeypatch.setattr(
        "src.components.ultimate_book.minimal_size.fear_withholds",
        lambda *a, **k: a[0],
    )
    assert "asia_pdl_fade" in F5_HARD_OFF_SLEEVES
    cid = "W7_BOOK::liquidity_sweep::UK100::2026-08-27::LONG::asia_pdl_fade"
    assert f5_hard_off_sleeve_reason(cid) == "hard_off_sleeve"
    reason = f5_standing_hold_reason(
        F5_NAMESPACE, "UK100", occupied_symbols=(),
        direction="LONG", family=cid, now=datetime(2026, 8, 31, 4, 0, tzinfo=timezone.utc),
    )
    assert reason == "hard_off_sleeve"


def test_isolated_reentry_wanted_cannot_arm_asia_pdl(monkeypatch):
    monkeypatch.setattr(
        "src.components.ultimate_book.minimal_size.fear_withholds",
        lambda *a, **k: a[0],
    )
    reason = f5_standing_hold_reason(
        F5_NAMESPACE, "UK100", occupied_symbols=(),
        direction=1, family="asia_pdl_fade",
        sl=10800.0, tp=10900.0, entry=10850.0,
        now=datetime(2026, 8, 31, 4, 33, tzinfo=timezone.utc),
    )
    assert reason == "hard_off_sleeve"


def test_climax_flush_needle_is_hard_off():
    assert f5_hard_off_sleeve_reason("dsp_climax_flush_to_96low_then_snap") == "hard_off_sleeve"
    assert f5_hard_off_sleeve_reason("LAUNCHER::EURUSD::dsp_climax_flush_to_96low_then_snap::2026-08-28")


def test_paid_sleeves_are_not_hard_off():
    for name in (
        "dsp_expanding_up_staircase",
        "dsp_wide_down_then_micro_bounce_then_through",
        "dsp_bleed_accept_fresh_20low_second_push",
    ):
        assert f5_hard_off_sleeve_reason(name) is None
        reason = f5_standing_hold_reason(
            F5_NAMESPACE, "US30", occupied_symbols=(),
            direction="SHORT", family=name,
            now=datetime(2026, 8, 31, 13, 0, tzinfo=timezone.utc),
        )
        assert reason != "hard_off_sleeve"


def test_usdjpy_named_hold_still_binds(monkeypatch):

    monkeypatch.setattr(
        "src.components.ultimate_book.minimal_size.fear_withholds",
        lambda *a, **k: a[0],
    )
    reason = f5_standing_hold_reason(
        F5_NAMESPACE, "USDJPY", occupied_symbols=(),
        direction="SHORT", family="dsp_isolated_spike_high",
        now=datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc),
    )
    assert reason == "usdjpy_verification_hold_5pip_dsp_stop"


def test_occupancy_keep_one_stays_script(monkeypatch):
    monkeypatch.setattr(
        "src.components.ultimate_book.minimal_size.fear_withholds",
        lambda *a, **k: None,
    )
    reason = f5_standing_hold_reason(
        F5_NAMESPACE, "US30", occupied_symbols=("US30",),
        direction="SHORT", family="dsp_expanding_up_staircase",
        now=datetime(2026, 8, 31, 13, 0, tzinfo=timezone.utc),
    )
    assert reason == "same_symbol_stack_keep_working_ticket"
