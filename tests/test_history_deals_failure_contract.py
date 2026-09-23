"""A failed broker history fetch must be distinguishable from "no deals today".

`RealMT5.get_history_deals` used to return `[]` for both. That collapses two very
different facts into one, and the orchestrator's consecutive-losses computation reads
the result directly: `for d in reversed(all_deals)` with a fetch failure yielding `[]`
sets `consecutive_losses = 0`, which silently RELEASES the consec_losses emergency
brake (`orchestrator.py:7004` is the reader) on a transient broker read error. A risk
brake that disengages when telemetry fails is a fail-open.

The VPS live-hardening branch fixed the root of it by returning `None` on failure, and
the ABC signature now says so (`mt5_interface.py`: "None means the broker fetch
failed"). These tests pin that contract, because it is only meaningful if every caller
honours it -- and two orchestrator sites did not, which is what made the change unsafe
to take on its own.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.mt5.mt5_real import RealMT5


class _BrokerStub:
    """Minimal stand-in for the MetaTrader5 module surface these paths touch."""

    def __init__(self, deals_result):
        self._deals_result = deals_result
        self.calls = 0

    def history_deals_get(self, *args, **kwargs):
        self.calls += 1
        return self._deals_result


def _real_mt5_with(broker) -> RealMT5:
    obj = RealMT5.__new__(RealMT5)          # bypass __init__: no terminal, no connect
    obj._mt5 = broker
    obj._broker_offset_detected = True      # skip the get_tick offset probe
    obj._broker_offset_seconds = 0
    return obj


def _window():
    now = datetime.now(timezone.utc)
    return now - timedelta(days=1), now


def test_failed_fetch_returns_none_not_empty_list():
    """The whole point: None (fetch failed) must not look like [] (no deals)."""
    broker = _BrokerStub(None)
    start, end = _window()

    result = _real_mt5_with(broker).get_history_deals(start, end, "XAUUSD")

    assert result is None, (
        "A failed history fetch returned a falsy list instead of None. Callers that "
        "compute risk state from this cannot tell failure from an empty day, and the "
        "consecutive-losses emergency brake resets to 0 on a broker hiccup."
    )
    assert broker.calls == 1


def test_genuinely_empty_history_returns_empty_list():
    """The other half of the contract: a real empty day is still []."""
    broker = _BrokerStub([])
    start, end = _window()

    result = _real_mt5_with(broker).get_history_deals(start, end, "XAUUSD")

    assert result == [], "An empty broker history must stay [], not become None."


def test_none_and_empty_are_not_interchangeable():
    """Guards the distinction itself, so a future refactor cannot quietly re-merge them."""
    start, end = _window()
    failed = _real_mt5_with(_BrokerStub(None)).get_history_deals(start, end, "XAUUSD")
    empty = _real_mt5_with(_BrokerStub([])).get_history_deals(start, end, "XAUUSD")

    assert failed is not empty
    assert (failed is None) and (empty == [])
    # Both are falsy -- which is exactly why `if not deals:` is the wrong test and
    # `if deals is None:` is the right one.
    assert not failed and not empty


def test_interface_declares_the_optional_contract():
    """The ABC must advertise it, or implementers will keep returning []."""
    import inspect

    from src.mt5.mt5_interface import MT5Interface

    sig = inspect.signature(MT5Interface.get_history_deals)
    assert "Optional" in str(sig.return_annotation) or "None" in str(sig.return_annotation), (
        f"MT5Interface.get_history_deals return annotation is {sig.return_annotation!r}; "
        "it must declare that None is possible."
    )
    assert "None" in (inspect.getdoc(MT5Interface.get_history_deals) or "")
