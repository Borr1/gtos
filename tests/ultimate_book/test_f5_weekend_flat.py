"""F5 weekend-carry rule (namespace code-default, 2026-08-25).

Non-24/7 symbols with an open F5 position at/after Friday 20:30 UTC are closed unless the
stop already locks >= +0.5R. Crypto is exempt (its market does not close). Distinct from the
argv-armed Session-BA `--weekend-flat` policy; no launch-contract change.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.components.ultimate_book.book_owner import UltimateBookOwner
from src.components.ultimate_book.minimal_size import (
    F5_ALWAYS_OPEN_SYMBOLS,
    F5_WEEKEND_LOCKED_R_EXEMPT,
    MinimalSizeConfig,
)

F5_NS = "operator"

FRI_2045 = datetime(2026, 8, 28, 20, 45, tzinfo=timezone.utc)   # Friday, inside the window
FRI_1000 = datetime(2026, 8, 28, 10, 0, tzinfo=timezone.utc)    # Friday, before 20:30
FRI_2130 = datetime(2026, 8, 28, 21, 30, tzinfo=timezone.utc)   # Friday, after summer close
WED_2045 = datetime(2026, 8, 26, 20, 45, tzinfo=timezone.utc)   # Wednesday
SAT_0100 = datetime(2026, 8, 29, 1, 0, tzinfo=timezone.utc)     # Saturday


class _MT5:
    def __init__(self, server=None):
        self._server = server

    def get_tick(self, _symbol):
        return SimpleNamespace(bid=100.0, ask=100.02, time=datetime.now(timezone.utc))

    def get_account_balance(self):
        return 100_000.0

    def get_account_equity(self):
        return 100_000.0

    def get_account_server(self):
        return self._server


class _WeekendEE:
    def __init__(self, ticket=42, direction="LONG", entry=100.0, stop=99.0,
                 sl_distance=1.0, close_ok=True):
        self.active_trade = SimpleNamespace(
            ticket=ticket, direction=direction, entry_price=entry, stop_loss=stop,
            sl_distance=sl_distance, current_volume=1.0,
        )
        self.closes = []
        self._close_ok = close_ok

    def close_position(self, reason):
        self.closes.append(reason)
        if self._close_ok:
            self.active_trade = None
        return self._close_ok


def _config():
    return {
        "market": {"symbol": "XAUUSD", "mt5_symbol": "XAUUSD"},
        "gtos_vnext_runtime": {
            "ultimate_book_enabled": True,
            "ultimate_book_apply_to_execution": True,
            "ultimate_book_live_activation_allowed": True,
            "ultimate_book_live_broker_authority": True,
            "ultimate_book_disable_broad_selector": True,
            "ultimate_book_profile": "clean3_w7_measured_nom1p25",
            "ultimate_book_include_clean3": True,
            "ultimate_book_derisk_mode": "band",
            "ultimate_book_include_candidate_book": False,
            "ultimate_book_include_market_expansion_book": False,
            "ultimate_book_stress_derisk": False,
            "ultimate_book_kelly_lite": True,
            "ultimate_book_kelly_conservative": True,
            "ultimate_book_drop_w7_symbols": True,
            "selector_v4_enabled": True,
            "selector_v4_apply_to_execution": False,
        },
    }


def _owner(tmp_path, namespace=F5_NS, server=None):
    return UltimateBookOwner(
        _config(),
        _MT5(server=server),
        str(tmp_path),
        namespace=namespace,
        engine_factory=lambda _symbol: _WeekendEE(),
        minimal_size=MinimalSizeConfig(
            enabled=True, target_risk_usd=75.0, notional_initial_usd=100_000.0,
        ),
    )


def _events(tmp_path, namespace=F5_NS):
    p = Path(tmp_path) / "shadow_logs" / "f5_minimal" / namespace / "events.jsonl"
    if not p.is_file():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# the four commissioned cases
# ---------------------------------------------------------------------------
def test_friday_after_2030_closes_a_carrying_fx_position(tmp_path):
    owner = _owner(tmp_path)
    ee = _WeekendEE()
    action = owner._f5_weekend_flat_close(ee, "GBPJPY", "fx_jpy", now=FRI_2045)
    assert action == "f5_weekend_flat"
    assert ee.closes == ["f5_weekend_flat"]
    events = [e for e in _events(tmp_path) if e["event"] == "f5_weekend_flat"]
    assert len(events) == 1
    assert events[0]["status"] == "closed"
    assert events[0]["broker_mutation"] is True
    assert events[0]["ticket"] == 42


def test_wednesday_does_not_fire(tmp_path):
    owner = _owner(tmp_path)
    ee = _WeekendEE()
    assert owner._f5_weekend_flat_close(ee, "GBPJPY", "fx_jpy", now=WED_2045) is None
    assert ee.closes == []
    assert _events(tmp_path) == []


def test_crypto_is_exempt(tmp_path):
    owner = _owner(tmp_path)
    for sym in ("LTCUSD", "BTCUSD", "ETHUSD"):
        assert sym in F5_ALWAYS_OPEN_SYMBOLS
        ee = _WeekendEE()
        assert owner._f5_weekend_flat_close(ee, sym, "asia_pdl_fade", now=FRI_2045) is None
        assert ee.closes == []


def test_locked_profit_is_exempt(tmp_path):
    owner = _owner(tmp_path)
    # LONG from 100.0, initial stop distance 1.0, stop trailed to 100.6 -> locked +0.6R.
    ee = _WeekendEE(entry=100.0, stop=100.6, sl_distance=1.0)
    assert owner._f5_weekend_flat_close(ee, "GBPJPY", "fx_jpy", now=FRI_2045) is None
    assert ee.closes == []
    events = [e for e in _events(tmp_path) if e["event"] == "f5_weekend_flat"]
    assert len(events) == 1
    assert events[0]["status"] == "exempt_locked_profit"
    assert events[0]["locked_r"] == pytest.approx(0.6)
    assert events[0]["locked_r_exempt_threshold"] == F5_WEEKEND_LOCKED_R_EXEMPT


# ---------------------------------------------------------------------------
# window edges and reconstruction details
# ---------------------------------------------------------------------------
def test_friday_before_2030_does_not_fire(tmp_path):
    owner = _owner(tmp_path)
    ee = _WeekendEE()
    assert owner._f5_weekend_flat_close(ee, "GBPJPY", "fx_jpy", now=FRI_1000) is None
    assert ee.closes == []


def test_saturday_does_not_fire(tmp_path):
    owner = _owner(tmp_path)
    ee = _WeekendEE()
    assert owner._f5_weekend_flat_close(ee, "GBPJPY", "fx_jpy", now=SAT_0100) is None
    assert ee.closes == []


def test_registered_server_bounds_the_window_at_the_true_broker_close(tmp_path):
    # August: broker Sat 00:00 == 21:00 UTC Friday (NY+7, EDT). At 21:30 the market is
    # shut -- no doomed close attempts; at 20:45 the close still fires.
    owner = _owner(tmp_path, server="FTMO-Server3")
    ee = _WeekendEE()
    assert owner._f5_weekend_flat_close(ee, "GBPJPY", "fx_jpy", now=FRI_2130) is None
    assert ee.closes == []
    action = owner._f5_weekend_flat_close(ee, "GBPJPY", "fx_jpy", now=FRI_2045)
    assert action == "f5_weekend_flat"


def test_locked_below_threshold_still_closes(tmp_path):
    owner = _owner(tmp_path)
    ee = _WeekendEE(entry=100.0, stop=100.3, sl_distance=1.0)     # +0.3R < +0.5R
    action = owner._f5_weekend_flat_close(ee, "GBPJPY", "fx_jpy", now=FRI_2045)
    assert action == "f5_weekend_flat"
    events = [e for e in _events(tmp_path) if e["event"] == "f5_weekend_flat"]
    assert events[0]["locked_r"] == pytest.approx(0.3)
    assert events[0]["status"] == "closed"


def test_short_locked_profit_is_exempt(tmp_path):
    owner = _owner(tmp_path)
    ee = _WeekendEE(direction="SHORT", entry=100.0, stop=99.4, sl_distance=1.0)
    assert owner._f5_weekend_flat_close(ee, "GBPJPY", "fx_jpy", now=FRI_2045) is None
    events = [e for e in _events(tmp_path) if e["event"] == "f5_weekend_flat"]
    assert events[0]["status"] == "exempt_locked_profit"
    assert events[0]["locked_r"] == pytest.approx(0.6)


def test_denominator_reconstructs_from_the_trade_record(tmp_path):
    owner = _owner(tmp_path)
    # An adopted position: sl_distance on the trade is the ADOPTION-TIME distance (already
    # trailed), which would overstate the lock. The record's intended geometry wins.
    owner._write_trade_record(42, {
        "instrumentation": {"entry_price": 100.0, "stop_loss": 99.0},
    })
    ee = _WeekendEE(entry=100.0, stop=100.6, sl_distance=0.05)
    assert owner._f5_weekend_flat_close(ee, "GBPJPY", "fx_jpy", now=FRI_2045) is None
    events = [e for e in _events(tmp_path) if e["event"] == "f5_weekend_flat"]
    assert events[0]["status"] == "exempt_locked_profit"
    assert events[0]["locked_r"] == pytest.approx(0.6)            # NOT 12.0 from 0.05


def test_close_failure_is_loud_once_and_retries(tmp_path):
    owner = _owner(tmp_path)
    ee = _WeekendEE(close_ok=False)
    assert owner._f5_weekend_flat_close(ee, "GBPJPY", "fx_jpy", now=FRI_2045) is None
    assert owner._f5_weekend_flat_close(ee, "GBPJPY", "fx_jpy", now=FRI_2045) is None
    assert ee.closes == ["f5_weekend_flat", "f5_weekend_flat"]    # keeps trying
    events = [e for e in _events(tmp_path) if e["event"] == "f5_weekend_flat"]
    assert len(events) == 1                                       # but says so once
    assert events[0]["status"] == "close_failed_position_still_open"


def test_namespace_gated_off_for_production(tmp_path):
    owner = _owner(tmp_path, namespace="operator_profile")
    ee = _WeekendEE()
    assert owner._f5_weekend_flat_close(ee, "GBPJPY", "fx_jpy", now=FRI_2045) is None
    assert ee.closes == []


def test_no_position_is_a_no_op(tmp_path):
    owner = _owner(tmp_path)
    ee = _WeekendEE()
    ee.active_trade = None
    assert owner._f5_weekend_flat_close(ee, "GBPJPY", "fx_jpy", now=FRI_2045) is None


def test_manage_engine_wiring_records_the_weekend_close(tmp_path, monkeypatch):
    """End-to-end through _manage_engine: the close lands in summary['closed'] with its
    real reason, exactly like the BA policy's path."""
    import src.components.ultimate_book.book_owner as bo

    class _FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return FRI_2045 if tz else FRI_2045.replace(tzinfo=None)

    monkeypatch.setattr(bo, "datetime", _FrozenDatetime)
    owner = _owner(tmp_path)
    owner._send_card = lambda *_a, **_k: None
    owner._emit_management_runtime_learning = lambda *_a, **_k: None
    ee = _WeekendEE()
    summary = {"managed": [], "adopted": [], "closed": [], "errors": []}
    owner._manage_engine(ee, "GBPJPY", "fx_jpy", summary)
    assert ee.closes == ["f5_weekend_flat"]
    assert summary["closed"] and summary["closed"][0]["action"] == "f5_weekend_flat"
