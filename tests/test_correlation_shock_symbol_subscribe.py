"""Tests for the correlation-shock monitor's startup symbol_select wiring
(Issue #17, 2026-04-28).

Background
----------
Direct MT5 query returned EURJPY M15 bars only up to 00:30 UTC at 14:30
UTC live. EURJPY isn't directly traded but is in the JPY_CROSSES
correlation_shock monitor group. Without an explicit ``symbol_select(EURJPY,
True)`` call, MT5's ``copy_rates_from_pos`` returns short/empty series for
symbols absent from Market Watch.

Fix: ``correlation_shock_monitor.py`` now calls ``symbol_select(broker_symbol,
True)`` for every symbol in ``DEFAULT_CORRELATION_GROUPS`` ONCE on startup
(inside ``main()``, before the per-pair fetch loop). Failures are logged
+ skipped silently — out-of-our-control if the broker doesn't serve the
symbol at all.

Tests use ``tmp_path`` + module-ref monkeypatch (canon).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import correlation_shock_monitor as mod  # noqa: E402


# ---------------------------------------------------------------------------
# 1 — _all_group_symbols: deduplicates + sorts across all groups
# ---------------------------------------------------------------------------


class TestAllGroupSymbols:
    def test_returns_sorted_unique_list(self):
        symbols = mod._all_group_symbols()
        assert symbols == sorted(symbols), "must be sorted for determinism"
        assert len(symbols) == len(set(symbols)), "must be deduplicated"

    def test_contains_eurjpy(self):
        """The symbol that motivated Issue #17 must be present."""
        assert "EURJPY" in mod._all_group_symbols()

    def test_contains_xauusd_xagusd_us30(self):
        """Other group members must also appear (sanity)."""
        sym = mod._all_group_symbols()
        for expected in (
            "XAUUSD",
            "XAGUSD",
            "US30_cash",
            "NAS100",
            "USDJPY",
            "GBPJPY",
        ):
            assert expected in sym, f"{expected} missing from group symbols"


# ---------------------------------------------------------------------------
# 2 — ensure_symbols_subscribed: invokes mt5.symbol_select per symbol
# ---------------------------------------------------------------------------


class _FakeRawMT5:
    """Captures every symbol_select call with the broker symbol passed in."""

    def __init__(self, fail_for: set = None):
        self.calls = []
        self.fail_for = fail_for or set()

    def symbol_select(self, symbol: str, enable: bool) -> bool:
        self.calls.append((symbol, enable))
        if symbol in self.fail_for:
            return False
        return True


class _FakeFacade:
    """Mimics src.mt5.RealMT5 — exposes ._mt5 raw module attribute."""

    def __init__(self, raw):
        self._mt5 = raw


class TestEnsureSymbolsSubscribed:
    def test_calls_symbol_select_for_each_symbol(self):
        raw = _FakeRawMT5()
        facade = _FakeFacade(raw)
        result = mod.ensure_symbols_subscribed(facade, ["EURJPY", "USDJPY"])
        assert raw.calls == [("EURJPY", True), ("USDJPY", True)]
        assert result == {"EURJPY": True, "USDJPY": True}

    def test_uses_broker_symbol_alias(self):
        """US30_cash → US30.cash on FTMO-shape brokers (alias defined in
        BROKER_SYMBOL_ALIAS). The wired call must apply that translation."""
        raw = _FakeRawMT5()
        facade = _FakeFacade(raw)
        mod.ensure_symbols_subscribed(facade, ["US30_cash"])
        # The first arg must be the broker alias, not the canonical name
        broker_arg = raw.calls[0][0]
        assert broker_arg == mod.broker_symbol("US30_cash")

    def test_uses_nas100_broker_symbol_alias(self):
        """NAS100 is monitored through the redacted_account NDX100 broker symbol."""
        raw = _FakeRawMT5()
        facade = _FakeFacade(raw)
        mod.ensure_symbols_subscribed(facade, ["NAS100"])
        assert raw.calls == [("NDX100", True)]

    def test_individual_failures_recorded_not_raised(self):
        raw = _FakeRawMT5(fail_for={"EURJPY"})
        facade = _FakeFacade(raw)
        result = mod.ensure_symbols_subscribed(
            facade, ["EURJPY", "USDJPY", "GBPJPY"]
        )
        assert result == {"EURJPY": False, "USDJPY": True, "GBPJPY": True}

    def test_facade_without_raw_returns_no_op_success(self):
        """Test/mock facades without ``_mt5`` get a no-op success map so
        ``main()`` can run unmodified in test envs that don't stub the raw
        module."""
        result = mod.ensure_symbols_subscribed(object(), ["EURJPY"])
        assert result == {"EURJPY": True}

    def test_symbol_select_exception_does_not_crash(self):
        class _ExplodingRaw:
            def symbol_select(self, *args, **kwargs):
                raise RuntimeError("boom")

        result = mod.ensure_symbols_subscribed(
            _FakeFacade(_ExplodingRaw()), ["EURJPY"]
        )
        assert result == {"EURJPY": False}


# ---------------------------------------------------------------------------
# 3 — main() invokes _subscribe_all_group_symbols before fetching closes
# ---------------------------------------------------------------------------


class TestMainInvokesSubscribe:
    """The fix's load-bearing claim: subscribe MUST happen on startup before
    the per-pair fetch loop runs (which happens before any check_pair call)."""

    def test_main_calls_subscribe_before_fetch_closes(
        self, monkeypatch, tmp_path
    ):
        # Isolate state file
        monkeypatch.setattr(mod, "STATE_FILE", tmp_path / "state.json")

        call_order = []

        def fake_subscribe():
            call_order.append("subscribe")
            return {"EURJPY": True}

        def fake_fetch(sym, count=mod.M15_LOOKBACK_CANDLES):
            call_order.append(f"fetch:{sym}")
            return []  # empty -> no_data status -> no alarm

        monkeypatch.setattr(mod, "_subscribe_all_group_symbols", fake_subscribe)
        monkeypatch.setattr(mod, "fetch_closes", fake_fetch)

        rc = mod.main()
        assert rc == 0  # no alarms

        assert call_order, "main produced no actions"
        assert call_order[0] == "subscribe", (
            f"Expected first action to be subscribe; got {call_order[:3]}"
        )

    def test_subscribe_failure_does_not_block_fetch(
        self, monkeypatch, tmp_path
    ):
        """The subscribe step is best-effort — its failure must not abort
        the monitor (which would mask correlation shocks during a transient
        MT5 hiccup)."""
        monkeypatch.setattr(mod, "STATE_FILE", tmp_path / "state.json")

        fetch_called = {"count": 0}

        def boom():
            raise RuntimeError("simulated subscribe failure")

        def fake_fetch(sym, count=mod.M15_LOOKBACK_CANDLES):
            fetch_called["count"] += 1
            return []

        monkeypatch.setattr(mod, "_subscribe_all_group_symbols", boom)
        monkeypatch.setattr(mod, "fetch_closes", fake_fetch)

        rc = mod.main()
        assert rc == 0
        assert fetch_called["count"] > 0, (
            "fetch_closes was never invoked; subscribe failure aborted main"
        )
