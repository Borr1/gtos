"""Tests for T2.8 concurrent-cap architecture.

Covers ``src/components/concurrent_tracker.py`` (formula, cache, cross-symbol
counting, fail-open) and the Gate 3 integration path in ``permissions.py``
that consults ``resolve_max_concurrent`` + ``get_filled_position_count``.

Fixture pattern: cache is a module-level mutable — each test resets it via
the ``_reset_tracker_cache`` autouse fixture below. Cross-symbol counting is
exercised through ``MockMT5._positions`` (production path uses the raw
MetaTrader5 module via ``_resolve_mt5_module``; the mock path is
``_count_via_mock``).
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from src.components import concurrent_tracker as _ct
from src.components.permissions import check_permissions
from src.mt5.mt5_interface import MAGIC_NUMBER, PositionInfo
from src.mt5.mt5_mock import MockMT5


# --------------------------------------------------------------------------
# Autouse fixtures — cache isolation
# --------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_tracker_cache():
    """Clear the TTL cache before and after every test.

    Without this, order-dependent cache hits would mask regressions.
    """
    _ct.reset_cache()
    yield
    _ct.reset_cache()


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _make_position(*, ticket: int = 1, symbol: str = "XAUUSD",
                   magic: int = MAGIC_NUMBER) -> PositionInfo:
    """Minimal ``PositionInfo`` for tests. Only ticket/symbol/magic matter
    for concurrent-cap counting; other fields are placeholder."""
    return PositionInfo(
        ticket=ticket,
        symbol=symbol,
        type=0,
        volume=0.10,
        price_open=2650.0,
        sl=2640.0,
        tp=2670.0,
        profit=0.0,
        magic=magic,
        comment="test",
        time=datetime.now(timezone.utc),
    )


# --------------------------------------------------------------------------
# compute_max_concurrent — formula semantics
# --------------------------------------------------------------------------

class TestComputeMaxConcurrent:
    def test_ftmo_formula_yields_2(self):
        """FTMO: 4.0% daily cap / 2.0% risk = 2 concurrent."""
        assert _ct.compute_max_concurrent(2.0, 4.0) == 2

    def test_redacted_account_formula_yields_4(self):
        """redacted_account: 4.0% daily cap / 1.0% risk = 4 concurrent."""
        assert _ct.compute_max_concurrent(1.0, 4.0) == 4

    def test_floor_rounds_down(self):
        """3% / 0.8% = 3.75 → floor to 3."""
        assert _ct.compute_max_concurrent(0.8, 3.0) == 3

    def test_minimum_cap_is_one(self):
        """Formula must never return 0 — a misconfig could stall all trading."""
        # 1% risk, 0.5% cap → floor(0.5) = 0 → clamped to 1
        assert _ct.compute_max_concurrent(1.0, 0.5) == 1

    def test_zero_risk_returns_one(self):
        """Non-positive risk fails open to cap=1."""
        assert _ct.compute_max_concurrent(0.0, 4.0) == 1

    def test_negative_risk_returns_one(self):
        assert _ct.compute_max_concurrent(-1.0, 4.0) == 1

    def test_zero_daily_loss_returns_one(self):
        assert _ct.compute_max_concurrent(2.0, 0.0) == 1

    def test_nonsense_types_return_one(self):
        assert _ct.compute_max_concurrent("foo", 4.0) == 1  # type: ignore
        assert _ct.compute_max_concurrent(None, 4.0) == 1  # type: ignore


# --------------------------------------------------------------------------
# resolve_max_concurrent — config precedence
# --------------------------------------------------------------------------

class TestResolveMaxConcurrent:
    def test_pinned_value_wins_over_formula(self):
        """An explicit legacy cap pin wins over formula derivation."""
        config = {"risk": {
            "risk_per_trade_pct": 2.0,
            "max_daily_loss_pct": 4.0,
            "max_concurrent": 2,
        }}
        assert _ct.resolve_max_concurrent(config) == 2

    def test_derives_when_pinned_is_null(self):
        config = {"risk": {
            "risk_per_trade_pct": 1.0,
            "max_daily_loss_pct": 4.0,
            "max_concurrent": None,
        }}
        assert _ct.resolve_max_concurrent(config) == 4

    def test_derives_when_pinned_missing(self):
        config = {"risk": {
            "risk_per_trade_pct": 2.0,
            "max_daily_loss_pct": 4.0,
        }}
        assert _ct.resolve_max_concurrent(config) == 2

    def test_pinned_value_ignored_if_bool(self):
        """``isinstance(True, int)`` is True in Python — explicit guard."""
        config = {"risk": {
            "risk_per_trade_pct": 2.0,
            "max_daily_loss_pct": 4.0,
            "max_concurrent": True,
        }}
        # Falls back to derivation (2.0 and 4.0 => 2)
        assert _ct.resolve_max_concurrent(config) == 2

    def test_pinned_value_ignored_if_less_than_one(self):
        config = {"risk": {
            "risk_per_trade_pct": 2.0,
            "max_daily_loss_pct": 4.0,
            "max_concurrent": 0,
        }}
        assert _ct.resolve_max_concurrent(config) == 2  # derives

    def test_defaults_when_config_missing(self):
        """No config at all → use default 2.0/4.0 which yields 2."""
        assert _ct.resolve_max_concurrent(None) == 2
        assert _ct.resolve_max_concurrent({}) == 2


# --------------------------------------------------------------------------
# get_filled_position_count — cross-symbol counting via MockMT5
# --------------------------------------------------------------------------

class TestGetFilledPositionCount:
    def test_zero_on_no_positions(self):
        mt5 = MockMT5(); mt5.connect()
        assert _ct.get_filled_position_count(mt5) == 0

    def test_counts_across_symbols(self):
        """A position on XAUUSD and one on US30 should both count — the
        magic-number filter doesn't discriminate by symbol."""
        mt5 = MockMT5(); mt5.connect()
        mt5._positions.append(_make_position(ticket=1, symbol="XAUUSD"))
        mt5._positions.append(_make_position(ticket=2, symbol="US30"))
        assert _ct.get_filled_position_count(mt5, now=0.0) == 2

    def test_ignores_foreign_magic(self):
        """Positions from other EAs (different magic) must not count."""
        mt5 = MockMT5(); mt5.connect()
        mt5._positions.append(_make_position(ticket=1))
        mt5._positions.append(_make_position(ticket=2, magic=99999))
        assert _ct.get_filled_position_count(mt5, now=0.0) == 1

    def test_counts_multiple_same_symbol(self):
        """Locked decision #2 — same-instrument concurrency allowed."""
        mt5 = MockMT5(); mt5.connect()
        mt5._positions.append(_make_position(ticket=1, symbol="XAUUSD"))
        mt5._positions.append(_make_position(ticket=2, symbol="XAUUSD"))
        assert _ct.get_filled_position_count(mt5, now=0.0) == 2


# --------------------------------------------------------------------------
# TTL cache behavior
# --------------------------------------------------------------------------

class TestCacheTTL:
    def test_cache_hit_returns_stale_value(self):
        """Within TTL, a fresh position is NOT reflected (cache is sticky)."""
        mt5 = MockMT5(); mt5.connect()
        # Seed: 1 position
        mt5._positions.append(_make_position(ticket=1))
        assert _ct.get_filled_position_count(mt5, ttl_seconds=10.0, now=0.0) == 1

        # Add second position; within TTL cache should still report 1.
        mt5._positions.append(_make_position(ticket=2))
        assert _ct.get_filled_position_count(mt5, ttl_seconds=10.0, now=5.0) == 1

    def test_cache_expiry_refreshes(self):
        """Beyond TTL, a fresh fetch must see the new count."""
        mt5 = MockMT5(); mt5.connect()
        mt5._positions.append(_make_position(ticket=1))
        assert _ct.get_filled_position_count(mt5, ttl_seconds=10.0, now=0.0) == 1

        mt5._positions.append(_make_position(ticket=2))
        assert _ct.get_filled_position_count(mt5, ttl_seconds=10.0, now=15.0) == 2

    def test_reset_cache_forces_refresh(self):
        mt5 = MockMT5(); mt5.connect()
        mt5._positions.append(_make_position(ticket=1))
        _ct.get_filled_position_count(mt5, now=0.0)
        mt5._positions.append(_make_position(ticket=2))
        _ct.reset_cache()
        # Same "now" as before, but cache cleared → must re-count.
        assert _ct.get_filled_position_count(mt5, now=0.0) == 2


# --------------------------------------------------------------------------
# Fail-open behavior on MT5 errors
# --------------------------------------------------------------------------

class _BrokenMT5Module:
    """Stands in for a raw MT5 module that raises on positions_get()."""

    def positions_get(self):
        raise RuntimeError("simulated MT5 glitch")


class _BrokenWrapper:
    """Mimics a RealMT5 wrapper carrying a raw module that breaks."""

    _mt5 = _BrokenMT5Module()

    def is_connected(self) -> bool:  # for completeness
        return True


class TestFailOpen:
    def test_counts_zero_on_mt5_exception(self):
        """Fail-open: if positions_get raises, return 0 (trade is LET THROUGH
        by the permissions gate). Daily loss stop + correlation caps remain
        authoritative; this gate is additive protection."""
        wrapper = _BrokenWrapper()
        assert _ct.get_filled_position_count(wrapper) == 0

    def test_none_mt5_returns_zero(self):
        """Defensive — if a test passes mt5=None the counter should no-op."""
        assert _ct.get_filled_position_count(None) == 0


# --------------------------------------------------------------------------
# Gate 3 integration — permissions.py denies when cap reached
# --------------------------------------------------------------------------

def _mock_pa(grade: str = "A+", direction: str = "LONG", entry: float = 2650.0,
             sl: float = 2640.0, rr: float = 1.5, daily_bias: str = "bullish"):
    """Build a minimal PrimaryAnalysisOutput-like object.

    Mirrors the shape used by ``tests/test_permissions.py::_mock_pa``:
    Gate 1 reads ``reasoning.setup_grade`` (required ≥ "A") and
    ``trade_parameters`` fields. A plain dict won't satisfy this path.
    """
    tp = SimpleNamespace(
        direction=direction,
        entry_price=entry,
        stop_loss=sl,
        risk_reward_ratio=rr,
        take_profit_1=entry + (entry - sl) * rr,
    )
    reasoning = SimpleNamespace(
        setup_grade=grade,
        daily_bias=SimpleNamespace(direction=daily_bias),
    )
    return SimpleNamespace(reasoning=reasoning, trade_parameters=tp)


def _mock_vnext_pa(*, durable_capture: bool = True, **kwargs):
    """A governed vNext row, i.e. one the selected-cell risk budget owns.

    ``durable_capture=False`` reproduces the pre-2026-07-27 fixture, which is kept
    because it is now a test subject of its own rather than an accident.
    """
    pa = _mock_pa(**kwargs)
    tp = pa.trade_parameters
    tp.gtos_vnext_production_execution_path = True
    tp.gtos_vnext_dynamic_policy_applied = True
    tp.gtos_vnext_dynamic_policy_selected = "momentum_exhaustion"
    tp.gtos_vnext_execution_policy_id = "unit_momentum_policy"
    tp.gtos_vnext_selected_cell_risk_pct = 0.25
    if durable_capture:
        # ``same_symbol_lifecycle_v4.durable_lifecycle_capture_contract`` requires six
        # candidate fields. ``risk_pct`` resolves from the selected-cell risk above and
        # ``source_completeness_status`` defaults to "runtime_candidate_packet"; the four
        # below were absent, so EVERY governed row in this class failed closed at
        # ``same_symbol_lifecycle_v4_source_required_fail_closed`` before the count-cap
        # bypass, duplicate-rejection and alias-aware hedge branches were ever reached.
        # The tests then measured the capture gate instead of their own subject.
        # The gate itself is pinned by
        # ``test_vnext_candidate_without_durable_capture_fails_closed``.
        tp.gtos_vnext_candidate_id = "unit_candidate_1"
        tp.gtos_vnext_thesis_id = "unit_thesis_1"
        tp.gtos_vnext_candidate_probability = 0.55
        tp.gtos_vnext_candidate_ev_r = 0.42
    return pa


def _mock_mso(m15_atr: float = 3.0):
    """Minimal MSO with enough structure for permissions to run."""
    return SimpleNamespace(m15_atr=m15_atr)


class TestGate3Integration:
    def _base_state(self):
        return {
            "daily_pnl_pct": 0.0,
            "trades_today": 0,
            "current_kill_zone": "london",
            "trades_london": 0,
            "losses_today": 0,
        }

    def test_passes_when_below_cap(self):
        """Zero open positions + default cap=2 → gate passes on that axis."""
        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(2650.00, 2650.18)
        denial = check_permissions(_mock_pa(), _mock_mso(),
                                   self._base_state(), mt5)
        assert denial is None

    def test_rejects_when_cap_reached_ftmo(self):
        """FTMO profile cap=2. 2 filled positions → gate rejects next attempt."""
        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(2650.00, 2650.18)
        mt5._positions.append(_make_position(ticket=1, symbol="XAUUSD"))
        mt5._positions.append(_make_position(ticket=2, symbol="US30"))

        config = {"risk": {
            "risk_per_trade_pct": 2.0,
            "max_daily_loss_pct": 4.0,
            "max_concurrent": 2,
        }}
        denial = check_permissions(_mock_pa(), _mock_mso(),
                                   self._base_state(), mt5, config=config)
        assert denial is not None
        assert denial.gate == "gate3_circuit_breaker"
        assert denial.reason == "concurrent_cap_reached"
        assert denial.details["filled_positions"] == 2
        assert denial.details["max_concurrent"] == 2

    def test_rejects_when_cap_reached_redacted_account(self):
        """redacted_account profile cap=4. 4 filled positions → gate rejects."""
        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(2650.00, 2650.18)
        for i in range(4):
            mt5._positions.append(_make_position(ticket=100 + i,
                                                 symbol=f"SYM{i}"))

        config = {"risk": {
            "risk_per_trade_pct": 1.0,
            "max_daily_loss_pct": 4.0,
            "max_concurrent": 4,
        }}
        denial = check_permissions(_mock_pa(), _mock_mso(),
                                   self._base_state(), mt5, config=config)
        assert denial is not None
        assert denial.reason == "concurrent_cap_reached"
        assert denial.details["filled_positions"] == 4
        assert denial.details["max_concurrent"] == 4

    def test_vnext_selected_cell_risk_bypasses_old_count_cap(self):
        """vNext rows are governed by account-risk exposure, not old count caps.

        The legacy row on the identical fixture is the positive control: it proves the
        count cap really would have bitten here, so ``denial is None`` below means the
        bypass fired and not that the gate was never reached.
        """
        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(2650.00, 2650.18)
        for i in range(4):
            mt5._positions.append(_make_position(ticket=200 + i,
                                                 symbol=f"SYM{i}"))

        config = {"risk": {
            "risk_per_trade_pct": 1.0,
            "max_daily_loss_pct": 4.0,
            "max_concurrent": 2,
        }}
        legacy = check_permissions(_mock_pa(), _mock_mso(),
                                   self._base_state(), mt5, config=config)
        assert legacy is not None and legacy.reason == "concurrent_cap_reached"

        denial = check_permissions(_mock_vnext_pa(), _mock_mso(),
                                   self._base_state(), mt5, config=config)
        assert denial is None

    def test_vnext_rejects_same_symbol_duplicate_without_scale_action(self):
        """Same-symbol duplicate exposure is explicit, not accidental."""
        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(2650.00, 2650.18)
        mt5._positions.append(_make_position(ticket=300, symbol="XAUUSD"))
        config = {"risk": {
            "risk_per_trade_pct": 1.0,
            "max_daily_loss_pct": 4.0,
            "max_concurrent": 4,
        }}
        denial = check_permissions(_mock_vnext_pa(), _mock_mso(),
                                   self._base_state(), mt5, config=config)
        assert denial is not None
        assert denial.reason == "same_symbol_lifecycle_v4_duplicate_exposure_rejected"
        assert denial.details["selected_cell_risk_pct"] == 0.25
        assert denial.details["same_symbol_lifecycle_v4"]["action"] == (
            "no_trade_duplicate"
        )

    def test_vnext_same_symbol_conflict_is_broker_alias_aware(self):
        """Strategy and broker aliases must not bypass same-symbol lifecycle proof."""
        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(30349.12, 30350.88)
        mt5._positions.append(_make_position(ticket=301, symbol="NDX100"))
        config = {
            "market": {"symbol": "NAS100", "mt5_symbol": "NDX100"},
            "risk": {
                "risk_per_trade_pct": 0.25,
                "max_daily_loss_pct": 4.0,
                "max_concurrent": 4,
            },
        }

        denial = check_permissions(
            _mock_vnext_pa(entry=30393.76, sl=30478.57, direction="SHORT"),
            _mock_mso(m15_atr=70.0),
            self._base_state(),
            mt5,
            config=config,
            symbol="NAS100",
        )

        assert denial is not None
        assert denial.reason == "same_symbol_lifecycle_v4_hedge_conflict_rejected"
        assert "NDX100" in denial.details["symbol_aliases_checked"]
        assert denial.details["same_symbol_lifecycle_v4"][
            "open_position_snapshot"
        ][0]["symbol"] == "NDX100"

    def test_vnext_candidate_without_durable_capture_fails_closed(self):
        """Negative control for the three governed-row tests above.

        Every one of them used to short-circuit HERE — the fixture omitted four candidate
        fields, so the durable-lifecycle-capture contract failed closed and the count-cap
        bypass, duplicate-rejection and hedge-conflict branches were never reached. Pinning
        the gate explicitly means the only way to make those three green is to complete the
        capture; removing the guard now turns this test red instead of the file green.
        """
        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(2650.00, 2650.18)
        mt5._positions.append(_make_position(ticket=400, symbol="XAUUSD"))
        config = {"risk": {
            "risk_per_trade_pct": 1.0,
            "max_daily_loss_pct": 4.0,
            "max_concurrent": 4,
        }}

        denial = check_permissions(_mock_vnext_pa(durable_capture=False), _mock_mso(),
                                   self._base_state(), mt5, config=config)

        assert denial is not None
        assert denial.gate == "gate3_circuit_breaker"
        assert denial.reason == "same_symbol_lifecycle_v4_source_required_fail_closed"
        packet = denial.details["same_symbol_lifecycle_v4"]
        assert packet["action"] == "source_required_fail_closed"
        assert packet["permitted_order_intent"] is False
        assert packet["source_completeness"]["durable_capture_missing_fields"] == [
            "candidate.candidate_id",
            "candidate.ev_r",
            "candidate.probability",
            "candidate.thesis_id",
        ]

    def test_vnext_same_symbol_position_source_error_fails_closed(self):
        """Governed vNext rows must not pass when same-symbol state is unreadable."""

        class BrokenPositionsMT5(MockMT5):
            def get_positions(self, symbol="XAUUSD"):
                raise RuntimeError(f"positions unavailable for {symbol}")

        mt5 = BrokenPositionsMT5(); mt5.connect()
        mt5.set_tick(2650.00, 2650.18)
        config = {"risk": {
            "risk_per_trade_pct": 1.0,
            "max_daily_loss_pct": 4.0,
            "max_concurrent": 4,
        }}

        denial = check_permissions(
            _mock_vnext_pa(),
            _mock_mso(),
            self._base_state(),
            mt5,
            config=config,
        )

        assert denial is not None
        assert denial.reason == "same_symbol_position_source_unavailable_for_vnext_lifecycle_guard"
        assert "positions unavailable" in denial.details["source_error"]

    def test_passes_when_positions_are_foreign_magic(self):
        """Positions from other EAs must not count toward our cap."""
        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(2650.00, 2650.18)
        # 5 foreign positions, 0 of ours
        for i in range(5):
            mt5._positions.append(_make_position(ticket=900 + i, magic=77777))

        config = {"risk": {
            "risk_per_trade_pct": 2.0,
            "max_daily_loss_pct": 4.0,
            "max_concurrent": 2,
        }}
        denial = check_permissions(_mock_pa(), _mock_mso(),
                                   self._base_state(), mt5, config=config)
        # Concurrent cap shouldn't block. (Any other gate rejection is fine.)
        if denial is not None:
            assert denial.reason != "concurrent_cap_reached"
