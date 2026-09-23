"""Tests for the cross-instrument correlation-aware risk gate.

Covers ``src/components/cross_instrument_correlation_gate.py`` (logic +
config helpers) and the Gate 3.5 integration path in ``permissions.py``
that consults the gate for the REJECT action.

Fixture pattern: the gate's correlation table is module-level mutable so
tests pin a deterministic copy via ``set_correlation_table()``. The
production fallback is exercised by a single sanity test that walks the
hardcoded table through canonical lookups.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from src.components import cross_instrument_correlation_gate as gate
from src.components import cross_instrument_correlation_gate_logger as gate_logger
from src.components import concurrent_tracker as _ct
from src.components.cross_instrument_correlation_gate import (
    CrossInstrumentCorrelationResult,
    apply_risk_multiplier,
    check_cross_instrument_correlation,
    evaluate_for_candidate,
    get_correlation_table,
    is_enabled,
    lookup_correlation,
    resolve_pair_budget_groups,
    resolve_min_positions,
    resolve_threshold,
    set_correlation_table,
)
from src.components.permissions import check_permissions
from src.mt5.mt5_interface import MAGIC_NUMBER, PositionInfo
from src.mt5.mt5_mock import MockMT5


# ---------------------------------------------------------------------------
# Pinned correlation table — keeps tests independent of the JSON export file.
# ---------------------------------------------------------------------------

_PINNED_TABLE: dict[str, dict[str, float]] = {
    # Choices below align with the structural-screen finding cited in the
    # gate's module docstring: GBPUSD correlated 0.4+ with multiple
    # non-group instruments simultaneously.
    "GBPUSD": {
        "US30_cash": 0.45,
        "XAUUSD": 0.42,
        "GBPJPY": 0.50,
        "USDJPY": -0.42,   # negative — mirrors XAUUSD/USDJPY structural inverse
        "EURUSD": 0.65,
    },
    "XAUUSD": {
        "GBPUSD": 0.42,
        "US30_cash": 0.10,  # below threshold
        "USDJPY": -0.42,
        "GBPJPY": -0.10,    # below
    },
    "US30_cash": {
        "GBPUSD": 0.45,
        "XAUUSD": 0.10,
        "GBPJPY": 0.40,
        "EURUSD": 0.15,
    },
    "GBPJPY": {
        "GBPUSD": 0.50,
        "US30_cash": 0.40,
        "XAUUSD": -0.10,
        "USDJPY": 0.508,
    },
    "USDJPY": {
        "GBPUSD": -0.42,
        "XAUUSD": -0.42,
        "GBPJPY": 0.508,
    },
    "EURUSD": {
        "GBPUSD": 0.65,
        "US30_cash": 0.15,
    },
}


@pytest.fixture(autouse=True)
def _pin_table_and_reset_caches():
    """Inject a deterministic correlation table for every test."""
    original = get_correlation_table()
    set_correlation_table(_PINNED_TABLE)
    _ct.reset_cache()
    yield
    set_correlation_table(original)
    _ct.reset_cache()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_position_dict(symbol: str, direction: str) -> dict:
    """Build a plain-dict open-position record (matches ``open_positions``)."""
    return {"symbol": symbol, "direction": direction}


def _make_position_info(*, ticket: int = 1, symbol: str = "XAUUSD",
                        ptype: int = 0,
                        magic: int = MAGIC_NUMBER) -> PositionInfo:
    """Mock MT5 position. type=0 -> LONG/BUY, type=1 -> SHORT/SELL."""
    return PositionInfo(
        ticket=ticket,
        symbol=symbol,
        type=ptype,
        volume=0.10,
        price_open=1.0,
        sl=0.95,
        tp=1.10,
        profit=0.0,
        magic=magic,
        comment="test",
        time=datetime.now(timezone.utc),
    )


def _make_pa(direction: str = "LONG"):
    """Trade-params object shaped like ``PrimaryAnalysisOutput``.

    Geometry is intentionally COARSE — Gate 1 will reject on rr_too_low /
    tp1_too_close / direction_mismatch (depending on direction). We only
    care that Gate 3.5 (cross-instrument correlation) gets the right
    chance to either pass or reject before Gate 1 inspects geometry.
    """
    if direction == "LONG":
        tp = SimpleNamespace(
            direction="LONG",
            entry_price=1.2500,
            stop_loss=1.2450,
            take_profit_1=1.2575,
            take_profit_2=None,
            take_profit_3=None,
            risk_reward_ratio=1.5,
        )
        bias = "bullish"
    else:
        tp = SimpleNamespace(
            direction="SHORT",
            entry_price=1.2500,
            stop_loss=1.2550,
            take_profit_1=1.2425,
            take_profit_2=None,
            take_profit_3=None,
            risk_reward_ratio=1.5,
        )
        bias = "bearish"
    return SimpleNamespace(
        trade_parameters=tp,
        reasoning=SimpleNamespace(
            setup_grade="A",
            daily_bias=SimpleNamespace(direction=bias),
        ),
        framework="ob_retest",
    )


# ---------------------------------------------------------------------------
# 1. Single open position, no candidate match -> NONE
# ---------------------------------------------------------------------------

class TestNoActionPaths:
    def test_no_open_positions_returns_none(self):
        result = check_cross_instrument_correlation(
            "GBPUSD", "LONG", mt5=None,
            open_positions=[],
        )
        assert result.action == "NONE"
        assert result.risk_multiplier == 1.0
        assert result.reason == "no_open_positions"

    def test_one_correlated_position_below_min_returns_none(self):
        """1 correlated position is below the default min_positions=2 floor."""
        result = check_cross_instrument_correlation(
            "GBPUSD", "LONG", mt5=None,
            open_positions=[_make_position_dict("US30_cash", "LONG")],
        )
        assert result.action == "NONE"
        assert result.risk_multiplier == 1.0
        # The correlated_positions list still records the single match.
        assert len(result.correlated_positions) == 1
        assert result.correlated_positions[0]["symbol"] == "US30_cash"

    def test_uncorrelated_position_does_not_count(self):
        """XAUUSD <-> US30 below threshold (0.10) is filtered out."""
        result = check_cross_instrument_correlation(
            "XAUUSD", "LONG", mt5=None,
            open_positions=[_make_position_dict("US30_cash", "LONG")],
        )
        assert result.action == "NONE"
        assert result.correlated_positions == []

    def test_same_symbol_skipped(self):
        """Two positions on the candidate's own symbol must NOT count."""
        result = check_cross_instrument_correlation(
            "GBPUSD", "LONG", mt5=None,
            open_positions=[
                _make_position_dict("GBPUSD", "LONG"),
                _make_position_dict("GBPUSD", "LONG"),
            ],
        )
        assert result.action == "NONE"
        assert result.correlated_positions == []


# ---------------------------------------------------------------------------
# 2. Two correlated positions same direction -> HALVE
# ---------------------------------------------------------------------------

class TestHalvePath:
    def test_two_same_direction_correlated_halves(self):
        """USD-weakness day GBPUSD LONG with US30 LONG + XAU LONG already open
        -> cluster size 2 -> HALVE."""
        result = check_cross_instrument_correlation(
            "GBPUSD", "LONG", mt5=None,
            open_positions=[
                _make_position_dict("US30_cash", "LONG"),
                _make_position_dict("XAUUSD", "LONG"),
            ],
        )
        assert result.action == "RISK_REDUCE_HALF"
        assert result.risk_multiplier == 0.5
        assert len(result.correlated_positions) == 2
        # Reason mentions the cluster size.
        assert "2" in result.reason
        assert "halving" in result.reason

    def test_apply_multiplier_halves_risk_pct(self):
        """``apply_risk_multiplier`` returns base * 0.5 on HALVE result."""
        result = CrossInstrumentCorrelationResult(
            action="RISK_REDUCE_HALF",
            risk_multiplier=0.5,
        )
        assert apply_risk_multiplier(2.0, result) == 1.0
        assert apply_risk_multiplier(1.0, result) == 0.5
        assert apply_risk_multiplier(0.5, result) == 0.25  # FN XAUUSD overlay


# ---------------------------------------------------------------------------
# 2b. Exact shared pair budget -> HALVE with one correlated peer
# ---------------------------------------------------------------------------

class TestPairBudgetPath:
    def test_usdjpy_gbpjpy_pair_budget_halves_with_single_peer_position(self):
        result = check_cross_instrument_correlation(
            "USDJPY", "LONG", mt5=None,
            min_correlated_positions=2,
            open_positions=[
                _make_position_dict("GBPJPY", "LONG"),
            ],
            pair_budget_groups=[
                {
                    "name": "JPY_SHARED_BUDGET",
                    "instruments": ["USDJPY", "GBPJPY"],
                    "risk_multiplier": 0.5,
                }
            ],
        )

        assert result.action == "RISK_REDUCE_HALF"
        assert result.risk_multiplier == 0.5
        assert result.correlated_positions == [
            {"symbol": "GBPJPY", "direction": "LONG", "correlation": 0.508}
        ]
        assert "cross_instrument_pair_budget" in result.reason
        assert "JPY_SHARED_BUDGET" in result.reason

    def test_pair_budget_does_not_fire_for_hedging_direction(self):
        result = check_cross_instrument_correlation(
            "USDJPY", "LONG", mt5=None,
            min_correlated_positions=2,
            open_positions=[
                _make_position_dict("GBPJPY", "SHORT"),
            ],
            pair_budget_groups=[
                {
                    "name": "JPY_SHARED_BUDGET",
                    "instruments": ["USDJPY", "GBPJPY"],
                    "risk_multiplier": 0.5,
                }
            ],
        )

        assert result.action == "NONE"
        assert result.correlated_positions == []

    def test_evaluate_for_candidate_uses_configured_pair_budget(self):
        mt5 = MockMT5(); mt5.connect()
        mt5._positions.append(_make_position_info(ticket=1, symbol="GBPJPY", ptype=0))
        cfg = {
            "market": {"symbol": "USDJPY"},
            "risk": {
                "cross_instrument_correlation_enabled": True,
                "cross_instrument_pair_budget_enabled": True,
                "cross_instrument_pair_budget_groups": [
                    {
                        "name": "JPY_SHARED_BUDGET",
                        "instruments": ["USDJPY", "GBPJPY"],
                        "risk_multiplier": 0.5,
                    }
                ],
            },
        }

        result = evaluate_for_candidate("USDJPY", "LONG", mt5, cfg)

        assert result.action == "RISK_REDUCE_HALF"
        assert result.reason.startswith("cross_instrument_pair_budget")


# ---------------------------------------------------------------------------
# 3. Three correlated positions same direction -> REJECT
# ---------------------------------------------------------------------------

class TestRejectPath:
    def test_three_same_direction_correlated_rejects(self):
        result = check_cross_instrument_correlation(
            "GBPUSD", "LONG", mt5=None,
            open_positions=[
                _make_position_dict("US30_cash", "LONG"),
                _make_position_dict("XAUUSD", "LONG"),
                _make_position_dict("GBPJPY", "LONG"),
            ],
        )
        assert result.action == "REJECT"
        assert len(result.correlated_positions) == 3
        assert "cross_instrument_correlation_excess" in result.reason

    def test_four_correlated_still_rejects(self):
        """Cluster size beyond reject floor stays REJECT (monotonic)."""
        result = check_cross_instrument_correlation(
            "GBPUSD", "LONG", mt5=None,
            open_positions=[
                _make_position_dict("US30_cash", "LONG"),
                _make_position_dict("XAUUSD", "LONG"),
                _make_position_dict("GBPJPY", "LONG"),
                _make_position_dict("EURUSD", "LONG"),
            ],
        )
        assert result.action == "REJECT"
        assert len(result.correlated_positions) == 4


# ---------------------------------------------------------------------------
# 4. Two positions but different directions -> NONE (gate doesn't apply)
# ---------------------------------------------------------------------------

class TestDirectionFilter:
    def test_opposite_direction_with_positive_corr_does_not_count(self):
        """GBPUSD LONG candidate vs US30 SHORT (r = +0.45) is a hedge,
        not amplification."""
        result = check_cross_instrument_correlation(
            "GBPUSD", "LONG", mt5=None,
            open_positions=[
                _make_position_dict("US30_cash", "SHORT"),
                _make_position_dict("XAUUSD", "SHORT"),
            ],
        )
        assert result.action == "NONE"
        assert result.correlated_positions == []

    def test_one_same_direction_one_opposite(self):
        """Same-direction US30 LONG counts; opposite XAUUSD SHORT does not.
        Net cluster size = 1 < 2 -> NONE."""
        result = check_cross_instrument_correlation(
            "GBPUSD", "LONG", mt5=None,
            open_positions=[
                _make_position_dict("US30_cash", "LONG"),
                _make_position_dict("XAUUSD", "SHORT"),
            ],
        )
        assert result.action == "NONE"
        assert len(result.correlated_positions) == 1
        assert result.correlated_positions[0]["symbol"] == "US30_cash"


# ---------------------------------------------------------------------------
# 5. Negative correlation handling
# ---------------------------------------------------------------------------

class TestNegativeCorrelation:
    def test_negative_corr_same_direction_does_not_count(self):
        """XAUUSD LONG candidate, USDJPY LONG open, r=-0.42:
        same direction but inversely correlated -> hedge, not amplification."""
        result = check_cross_instrument_correlation(
            "XAUUSD", "LONG", mt5=None,
            open_positions=[
                _make_position_dict("USDJPY", "LONG"),
                _make_position_dict("USDJPY", "LONG"),
            ],
        )
        # Both positions hedge a LONG XAU candidate (negative correlation
        # -> they move opposite when XAU spikes), so cluster is empty.
        assert result.action == "NONE"
        assert result.correlated_positions == []

    def test_negative_corr_opposite_direction_amplifies(self):
        """XAUUSD LONG candidate, USDJPY SHORT (r=-0.42 between symbols):
        SHORT in USDJPY moves with LONG XAU -> amplifies. Two such positions
        clear the HALVE floor."""
        result = check_cross_instrument_correlation(
            "XAUUSD", "LONG", mt5=None,
            open_positions=[
                _make_position_dict("USDJPY", "SHORT"),
                _make_position_dict("GBPUSD", "LONG"),  # +0.42
            ],
        )
        assert result.action == "RISK_REDUCE_HALF"
        assert len(result.correlated_positions) == 2
        symbols = sorted(p["symbol"] for p in result.correlated_positions)
        assert symbols == ["GBPUSD", "USDJPY"]


# ---------------------------------------------------------------------------
# 6. Configurable threshold + min_positions
# ---------------------------------------------------------------------------

class TestConfigurable:
    def test_higher_threshold_excludes_borderline(self):
        """Threshold 0.5 excludes the 0.42-0.45 correlations -> NONE."""
        result = check_cross_instrument_correlation(
            "GBPUSD", "LONG", mt5=None,
            correlation_threshold=0.55,
            open_positions=[
                _make_position_dict("US30_cash", "LONG"),
                _make_position_dict("XAUUSD", "LONG"),
            ],
        )
        assert result.action == "NONE"

    def test_min_positions_three_does_not_halve_at_two(self):
        """min_positions=3 means HALVE only at >=3 cluster, REJECT at >=4."""
        result = check_cross_instrument_correlation(
            "GBPUSD", "LONG", mt5=None,
            min_correlated_positions=3,
            open_positions=[
                _make_position_dict("US30_cash", "LONG"),
                _make_position_dict("XAUUSD", "LONG"),
            ],
        )
        assert result.action == "NONE"

    def test_min_positions_three_halves_at_three(self):
        result = check_cross_instrument_correlation(
            "GBPUSD", "LONG", mt5=None,
            min_correlated_positions=3,
            open_positions=[
                _make_position_dict("US30_cash", "LONG"),
                _make_position_dict("XAUUSD", "LONG"),
                _make_position_dict("GBPJPY", "LONG"),
            ],
        )
        assert result.action == "RISK_REDUCE_HALF"

    def test_min_positions_three_rejects_at_four(self):
        result = check_cross_instrument_correlation(
            "GBPUSD", "LONG", mt5=None,
            min_correlated_positions=3,
            open_positions=[
                _make_position_dict("US30_cash", "LONG"),
                _make_position_dict("XAUUSD", "LONG"),
                _make_position_dict("GBPJPY", "LONG"),
                _make_position_dict("EURUSD", "LONG"),
            ],
        )
        assert result.action == "REJECT"


# ---------------------------------------------------------------------------
# 7. lookup_correlation + canonicalization
# ---------------------------------------------------------------------------

class TestLookupCorrelation:
    def test_symmetric_lookup(self):
        """lookup(A, B) == lookup(B, A) when both directions present."""
        a = lookup_correlation("GBPUSD", "US30_cash")
        b = lookup_correlation("US30_cash", "GBPUSD")
        assert a == 0.45
        assert b == 0.45

    def test_unknown_returns_none(self):
        assert lookup_correlation("FOO", "BAR") is None

    def test_same_symbol_returns_none(self):
        assert lookup_correlation("GBPUSD", "GBPUSD") is None
        # Aliased forms also collapse to None.
        assert lookup_correlation("US30", "US30_cash") is None
        assert lookup_correlation("US30_cash", "US30") is None

    def test_alias_resolution(self):
        """MT5 may return ``US30`` while screening uses ``US30_cash``."""
        canonical = lookup_correlation("GBPUSD", "US30_cash")
        aliased = lookup_correlation("GBPUSD", "US30")
        assert canonical == aliased == 0.45

    def test_vnext_futures_and_broker_alias_resolution(self):
        """Futures contracts and broker-dot symbols resolve to matrix families."""
        set_correlation_table({
            "GBPUSD": {"US30_cash": 0.45, "NAS100": 0.47},
            "SPX500": {"US30_cash": 0.90},
            "XAUUSD": {"XAGUSD": 0.79},
        })

        assert lookup_correlation("GBPUSD", "YM") == 0.45
        assert lookup_correlation("GBPUSD", "NQM26-CME") == 0.47
        assert lookup_correlation("ESM26-CME", "US30.cash") == 0.90
        assert lookup_correlation("GCM26-CME", "SIM26-CME") == 0.79
        assert lookup_correlation("SI", "XAGUSD") is None


# ---------------------------------------------------------------------------
# 8. Config helpers
# ---------------------------------------------------------------------------

class TestConfigHelpers:
    def test_is_enabled_default_true(self):
        assert is_enabled(None) is True
        assert is_enabled({}) is True
        assert is_enabled({"risk": {}}) is True

    def test_is_enabled_explicit_false(self):
        cfg = {"risk": {"cross_instrument_correlation_enabled": False}}
        assert is_enabled(cfg) is False

    def test_resolve_threshold_default(self):
        assert resolve_threshold(None) == 0.4

    def test_resolve_threshold_override(self):
        cfg = {"risk": {"cross_instrument_correlation_threshold": 0.55}}
        assert resolve_threshold(cfg) == 0.55

    def test_resolve_threshold_bad_value_falls_back(self):
        cfg = {"risk": {"cross_instrument_correlation_threshold": "bogus"}}
        assert resolve_threshold(cfg) == 0.4

    def test_resolve_min_positions_default(self):
        assert resolve_min_positions(None) == 2

    def test_resolve_min_positions_override(self):
        cfg = {"risk": {"cross_instrument_correlation_min_positions": 3}}
        assert resolve_min_positions(cfg) == 3

    def test_resolve_min_positions_floor(self):
        """Values < 1 clamp to 1 — never zero, never negative."""
        cfg = {"risk": {"cross_instrument_correlation_min_positions": 0}}
        assert resolve_min_positions(cfg) == 1

    def test_resolve_pair_budget_groups_from_config(self):
        cfg = {
            "risk": {
                "cross_instrument_pair_budget_enabled": True,
                "cross_instrument_pair_budget_groups": [
                    {
                        "name": "JPY_SHARED_BUDGET",
                        "instruments": ["USDJPY", "GBPJPY"],
                        "risk_multiplier": 0.5,
                        "source_line_no": 232,
                    }
                ],
            }
        }

        groups = resolve_pair_budget_groups(cfg)

        assert groups == [
            {
                "name": "JPY_SHARED_BUDGET",
                "instruments": ["GBPJPY", "USDJPY"],
                "risk_multiplier": 0.5,
                "source_path": None,
                "source_line_no": 232,
            }
        ]

    def test_agent_config_wires_jpy_pair_budget(self):
        with Path("config/agent_config.yaml").open("r", encoding="utf-8") as handle:
            cfg = yaml.safe_load(handle)

        groups = resolve_pair_budget_groups(cfg)

        assert groups == [
            {
                "name": "JPY_SHARED_BUDGET",
                "instruments": ["GBPJPY", "USDJPY"],
                "risk_multiplier": 0.5,
                "source_path": ".context/02_session_handoffs/04_apr6_expansion_sprint.md",
                "source_line_no": 232,
            }
        ]

    def test_evaluate_for_candidate_disabled_returns_none(self):
        """Disabled flag short-circuits to NONE without consulting MT5."""
        mt5 = MockMT5(); mt5.connect()
        mt5._positions.append(_make_position_info(symbol="US30_cash", ptype=0))
        mt5._positions.append(_make_position_info(symbol="XAUUSD", ptype=0))
        cfg = {
            "market": {"symbol": "GBPUSD"},
            "risk": {"cross_instrument_correlation_enabled": False},
        }
        result = evaluate_for_candidate("GBPUSD", "LONG", mt5, cfg)
        assert result.action == "NONE"
        assert result.reason == "gate_disabled"


# ---------------------------------------------------------------------------
# 8b. Observation-only decision logger
# ---------------------------------------------------------------------------

class TestDecisionLogger:
    def test_evaluate_logs_when_shadow_logger_enabled(self, monkeypatch, tmp_path):
        log_path = tmp_path / "cross_instrument_correlation_decisions.jsonl"
        monkeypatch.setattr(gate_logger, "SHADOW_LOG_PATH", str(log_path))
        cfg = {
            "risk": {
                "cross_instrument_correlation_enabled": True,
                "cross_instrument_correlation_threshold": 0.4,
                "cross_instrument_correlation_min_positions": 2,
            },
            "shadow_loggers": {
                "cross_instrument_correlation_decisions_logger": {"enabled": True},
            },
        }

        result = evaluate_for_candidate(
            "GBPUSD",
            "LONG",
            None,
            cfg,
            evaluation_context="unit_test",
        )

        assert result.action == "NONE"
        rows = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
        assert len(rows) == 1
        assert rows[0]["candidate_symbol"] == "GBPUSD"
        assert rows[0]["candidate_direction"] == "LONG"
        assert rows[0]["evaluation_context"] == "unit_test"
        assert rows[0]["gate_action"] == "NONE"
        assert rows[0]["reason"] == "no_open_positions"

    def test_evaluate_does_not_log_without_explicit_logger_enable(self, monkeypatch, tmp_path):
        log_path = tmp_path / "cross_instrument_correlation_decisions.jsonl"
        monkeypatch.setattr(gate_logger, "SHADOW_LOG_PATH", str(log_path))
        cfg = {
            "risk": {
                "cross_instrument_correlation_enabled": True,
            },
        }

        result = evaluate_for_candidate("GBPUSD", "LONG", None, cfg)

        assert result.action == "NONE"
        assert not log_path.exists()


# ---------------------------------------------------------------------------
# 9. MT5 wiring — positions resolved via MockMT5
# ---------------------------------------------------------------------------

class TestMT5Resolution:
    def test_evaluate_via_mock_mt5_three_long_rejects(self):
        mt5 = MockMT5(); mt5.connect()
        mt5._positions.append(_make_position_info(ticket=1, symbol="US30_cash", ptype=0))
        mt5._positions.append(_make_position_info(ticket=2, symbol="XAUUSD", ptype=0))
        mt5._positions.append(_make_position_info(ticket=3, symbol="GBPJPY", ptype=0))
        cfg = {"market": {"symbol": "GBPUSD"}, "risk": {}}
        result = evaluate_for_candidate("GBPUSD", "LONG", mt5, cfg)
        assert result.action == "REJECT"
        assert len(result.correlated_positions) == 3

    def test_evaluate_via_mock_mt5_skips_foreign_magic(self):
        """Foreign-magic positions must not enter the cluster."""
        mt5 = MockMT5(); mt5.connect()
        mt5._positions.append(_make_position_info(ticket=1, symbol="US30_cash", ptype=0))
        mt5._positions.append(_make_position_info(
            ticket=2, symbol="XAUUSD", ptype=0, magic=99999,
        ))
        mt5._positions.append(_make_position_info(ticket=3, symbol="GBPJPY", ptype=0))
        cfg = {"market": {"symbol": "GBPUSD"}, "risk": {}}
        result = evaluate_for_candidate("GBPUSD", "LONG", mt5, cfg)
        # 2 GTOS positions (US30, GBPJPY) -> cluster size 2 -> HALVE.
        assert result.action == "RISK_REDUCE_HALF"
        assert len(result.correlated_positions) == 2

    def test_evaluate_with_no_mt5_returns_none(self):
        cfg = {"market": {"symbol": "GBPUSD"}, "risk": {}}
        result = evaluate_for_candidate("GBPUSD", "LONG", None, cfg)
        assert result.action == "NONE"
        assert result.reason == "no_open_positions"


# ---------------------------------------------------------------------------
# 10. Permissions integration — Gate 3.5 REJECT path
# ---------------------------------------------------------------------------

class TestPermissionsIntegration:
    def _base_config(self) -> dict:
        return {
            "deployment": {"phase": 3},
            "trading_enabled": True,
            "market": {"symbol": "GBPUSD"},
            "risk": {
                "risk_per_trade_pct": 1.0,
                "max_daily_loss_pct": 4.0,
                "max_concurrent": 4,  # FN — don't trip concurrent cap.
                "cross_instrument_correlation_enabled": True,
                "cross_instrument_correlation_threshold": 0.4,
                "cross_instrument_correlation_min_positions": 2,
            },
        }

    def _session_state(self) -> dict:
        return {"daily_pnl_pct": 0.0, "deterministic_bias": "bullish"}

    def test_gate_rejects_when_three_correlated_long_open(self):
        mt5 = MockMT5(); mt5.connect()
        mt5._positions.append(_make_position_info(ticket=1, symbol="US30_cash", ptype=0))
        mt5._positions.append(_make_position_info(ticket=2, symbol="XAUUSD", ptype=0))
        mt5._positions.append(_make_position_info(ticket=3, symbol="GBPJPY", ptype=0))

        denial = check_permissions(
            trade_params=_make_pa("LONG"),
            mso=SimpleNamespace(timeframes={}),
            session_state=self._session_state(),
            mt5=mt5,
            config=self._base_config(),
            symbol="GBPUSD",
        )
        assert denial is not None
        assert denial.gate == "gate3_circuit_breaker"
        assert denial.reason == "cross_instrument_correlation_excess"
        assert denial.details["cluster_size"] == 3
        assert denial.details["candidate_symbol"] == "GBPUSD"
        assert denial.details["candidate_direction"] == "LONG"

    def test_gate_passes_when_two_correlated_open(self):
        """Cluster size 2 is HALVE territory — Gate 3.5 must NOT reject.
        The HALVE flow happens later in the orchestrator."""
        mt5 = MockMT5(); mt5.connect()
        mt5._positions.append(_make_position_info(ticket=1, symbol="US30_cash", ptype=0))
        mt5._positions.append(_make_position_info(ticket=2, symbol="XAUUSD", ptype=0))

        denial = check_permissions(
            trade_params=_make_pa("LONG"),
            mso=SimpleNamespace(timeframes={}),
            session_state=self._session_state(),
            mt5=mt5,
            config=self._base_config(),
            symbol="GBPUSD",
        )
        # Either passes through this gate (returns None) or gets blocked
        # later by gate1 (no trade_parameters geometry). The cross-corr
        # gate itself must NOT be the one that rejected.
        if denial is not None:
            assert denial.reason != "cross_instrument_correlation_excess"

    def test_gate_disabled_does_not_reject(self):
        """Even with 3 correlated open, ``enabled=False`` short-circuits to NONE."""
        cfg = self._base_config()
        cfg["risk"]["cross_instrument_correlation_enabled"] = False
        mt5 = MockMT5(); mt5.connect()
        mt5._positions.append(_make_position_info(ticket=1, symbol="US30_cash", ptype=0))
        mt5._positions.append(_make_position_info(ticket=2, symbol="XAUUSD", ptype=0))
        mt5._positions.append(_make_position_info(ticket=3, symbol="GBPJPY", ptype=0))

        denial = check_permissions(
            trade_params=_make_pa("LONG"),
            mso=SimpleNamespace(timeframes={}),
            session_state=self._session_state(),
            mt5=mt5,
            config=cfg,
            symbol="GBPUSD",
        )
        if denial is not None:
            assert denial.reason != "cross_instrument_correlation_excess"


# ---------------------------------------------------------------------------
# 11. Hardcoded-table sanity (production fallback)
# ---------------------------------------------------------------------------

class TestProductionFallback:
    def test_fallback_table_has_required_pairs(self):
        """The hardcoded fallback in the module covers GTOS production
        instruments. Reset to module fallback (autouse fixture pinned a
        narrower test table) and confirm the keys we rely on are present."""
        from src.components.cross_instrument_correlation_gate import (
            _FALLBACK_CORRELATION_TABLE,
        )
        required = {
            "XAUUSD", "GBPUSD", "GBPJPY", "USDJPY", "US30_cash",
        }
        assert required.issubset(_FALLBACK_CORRELATION_TABLE.keys())
        # GBPUSD <-> XAUUSD must exist in BOTH directions.
        assert "XAUUSD" in _FALLBACK_CORRELATION_TABLE["GBPUSD"]
        assert "GBPUSD" in _FALLBACK_CORRELATION_TABLE["XAUUSD"]
        # Sanity: GBPUSD-GBPJPY is 0.59 in the production matrix (>=0.4).
        # The brief's failure mode (GBPUSD+GBPJPY same-direction) must be
        # detectable in production, not just under the test pin.
        assert _FALLBACK_CORRELATION_TABLE["GBPUSD"]["GBPJPY"] >= 0.4
