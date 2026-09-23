"""Ghost 10011 close storm: backoff, max retries, dead-ticket cache.

10011 is order_send None (mt5_real wrapper), not a fill and not a disk closed
stamp. Sit door is positions_get absence. Do not flatten to "fix" this.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.components.ultimate_book.minimal_size import (
    F5_CLOSE_SEND_NONE_BACKOFF_S,
    F5_CLOSE_SEND_NONE_MAX_RETRIES,
    F5_CLOSE_SEND_NONE_RETCODE,
    f5_close_send_none_allow_order_send,
    f5_close_send_none_clear,
    f5_close_send_none_is_dead,
    f5_close_send_none_mark_absent,
    f5_close_send_none_note_none,
    f5_close_send_none_note_present,
    f5_close_send_none_reset,
    f5_close_send_none_seen,
    f5_close_send_none_should_defer_disk_closed,
)
from src.mt5.mt5_interface import ORDER_SEND_NONE_RETCODE, is_order_send_none, OrderResult

from tests.ultimate_book.test_f5_manage_consume import (
    _ManageEE,
    _consume,
    _events,
    _owner,
    _row,
    _write_manage,
)


T0 = datetime(2026, 8, 28, 8, 0, 0, tzinfo=timezone.utc)


def setup_function(_fn):
    f5_close_send_none_reset()


def teardown_function(_fn):
    f5_close_send_none_reset()


def test_constants_match_wrapper_retcode():
    assert F5_CLOSE_SEND_NONE_RETCODE == 10011
    assert ORDER_SEND_NONE_RETCODE == 10011
    assert F5_CLOSE_SEND_NONE_MAX_RETRIES == 5
    assert F5_CLOSE_SEND_NONE_BACKOFF_S[0] == 180
    assert F5_CLOSE_SEND_NONE_BACKOFF_S[0] > 60


def test_is_order_send_none_detects_wrapper_and_raw_none():
    assert is_order_send_none(None)
    assert is_order_send_none(OrderResult(
        retcode=10011, order=0, volume=0, price=0, comment="MT5 returned None",
    ))
    assert is_order_send_none(OrderResult(
        retcode=10011, order=0, volume=0, price=0, comment="fail",
    ))
    assert not is_order_send_none(OrderResult(
        retcode=10009, order=1, volume=0.1, price=1.0, comment="ok",
    ))


def test_first_close_is_allowed_then_backoff_blocks_60s_hammer():
    ticket = 178464792
    assert f5_close_send_none_allow_order_send(ticket, now=T0) is True
    state = f5_close_send_none_note_none(ticket, now=T0)
    assert state["attempts"] == 1
    assert state["dead"] is False
    assert f5_close_send_none_seen(ticket)
    assert f5_close_send_none_should_defer_disk_closed(ticket)
    # 60s poll would hammer; first backoff is 180s.
    assert f5_close_send_none_allow_order_send(
        ticket, now=T0 + timedelta(seconds=60),
    ) is False
    assert f5_close_send_none_allow_order_send(
        ticket, now=T0 + timedelta(seconds=179),
    ) is False
    assert f5_close_send_none_allow_order_send(
        ticket, now=T0 + timedelta(seconds=180),
    ) is True


def test_max_retries_marks_dead_and_never_sends():
    ticket = 179718360
    now = T0
    for _ in range(F5_CLOSE_SEND_NONE_MAX_RETRIES):
        state = f5_close_send_none_note_none(ticket, now=now)
        now = now + timedelta(seconds=3600)
    assert state["attempts"] == F5_CLOSE_SEND_NONE_MAX_RETRIES
    assert state["dead"] is True
    assert f5_close_send_none_is_dead(ticket)
    assert f5_close_send_none_allow_order_send(ticket, now=now) is False


def test_absent_sit_dead_cache_does_not_stamp_or_allow_send():
    ticket = 178947844
    f5_close_send_none_note_none(ticket, now=T0)
    f5_close_send_none_mark_absent(ticket, now=T0 + timedelta(seconds=1))
    assert f5_close_send_none_is_dead(ticket)
    assert f5_close_send_none_allow_order_send(
        ticket, now=T0 + timedelta(hours=24),
    ) is False
    assert f5_close_send_none_should_defer_disk_closed(ticket)


def test_present_sit_un_deads_but_keeps_backoff():
    ticket = 179079162
    f5_close_send_none_note_none(ticket, now=T0)
    f5_close_send_none_mark_absent(ticket, now=T0)
    f5_close_send_none_note_present(ticket, now=T0 + timedelta(seconds=10))
    assert f5_close_send_none_is_dead(ticket) is False
    assert f5_close_send_none_allow_order_send(
        ticket, now=T0 + timedelta(seconds=10),
    ) is False
    assert f5_close_send_none_allow_order_send(
        ticket, now=T0 + timedelta(seconds=180),
    ) is True


def test_clear_drops_cache_after_sit_door():
    ticket = 179145308
    f5_close_send_none_note_none(ticket, now=T0)
    f5_close_send_none_clear(ticket)
    assert not f5_close_send_none_seen(ticket)
    assert f5_close_send_none_allow_order_send(ticket, now=T0) is True


def test_manage_consume_skips_close_while_dead_and_does_not_flatten(tmp_path):
    owner = _owner(tmp_path)
    ee = _ManageEE(ticket=42)
    _write_manage(tmp_path, [_row(ticket=42, action="close")])
    f5_close_send_none_note_none(42, now=T0)
    for _ in range(F5_CLOSE_SEND_NONE_MAX_RETRIES - 1):
        f5_close_send_none_note_none(42, now=T0)
    assert f5_close_send_none_is_dead(42)
    summary = _consume(owner, ee, tmp_path)
    assert ee.closes == []
    assert ee.active_trade is not None
    rejected = _events(tmp_path, "f5_manage_rejected")
    assert rejected[0]["reason"] == "close_broker_unknown_dead_ticket"
    assert rejected[0]["broker_mutation"] is False
    assert summary["f5_manage"]["applied"] == 0


def test_manage_consume_skips_close_during_backoff(tmp_path):
    owner = _owner(tmp_path)
    ee = _ManageEE(ticket=42)
    _write_manage(tmp_path, [_row(ticket=42, action="close")])
    f5_close_send_none_note_none(42, now=datetime.now(timezone.utc))
    _consume(owner, ee, tmp_path)
    assert ee.closes == []
    assert ee.active_trade is not None
    assert _events(tmp_path, "f5_manage_rejected")[0]["reason"] == "close_broker_unknown_backoff"
