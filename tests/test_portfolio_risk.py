"""Tests for correlation-aware position sizing (Task 2)."""

from src.components.portfolio_risk import check_correlation_risk, CorrelationAdjustment


class TestNoCorrelationConflict:
    def test_no_open_positions(self):
        """Full risk when no positions open."""
        adj = check_correlation_risk("GBPJPY", 1.0, [])
        assert not adj.adjusted
        assert adj.final_risk_pct == 1.0
        assert adj.reason == "no_open_positions"

    def test_uncorrelated_position_open(self):
        """XAUUSD and EURJPY are not in the same group — no reduction."""
        adj = check_correlation_risk(
            "XAUUSD", 1.0,
            [{"symbol": "EURJPY", "risk_pct": 1.0}],
        )
        assert not adj.adjusted
        assert adj.final_risk_pct == 1.0
        assert adj.reason == "no_correlation_conflict"

    def test_same_symbol_not_conflict(self):
        """An open position on the SAME symbol isn't a correlation conflict
        (that's handled by circuit breakers, not correlation logic)."""
        adj = check_correlation_risk(
            "GBPJPY", 1.0,
            [{"symbol": "GBPJPY", "risk_pct": 1.0}],
        )
        assert not adj.adjusted
        assert adj.final_risk_pct == 1.0


class TestOneSidedConflict:
    def test_gbpjpy_reduced_when_eurjpy_open(self):
        """EURJPY open at 1% → GBPJPY reduced to 0.5% (group max 1.5%)."""
        adj = check_correlation_risk(
            "GBPJPY", 1.0,
            [{"symbol": "EURJPY", "risk_pct": 1.0}],
        )
        assert adj.adjusted
        assert adj.final_risk_pct == 0.5
        assert adj.correlated_instrument == "EURJPY"
        assert adj.group_name == "JPY_CROSSES"

    def test_eurjpy_reduced_when_gbpjpy_open(self):
        """GBPJPY open at 1% → EURJPY reduced to 0.5% (bidirectional)."""
        adj = check_correlation_risk(
            "EURJPY", 1.0,
            [{"symbol": "GBPJPY", "risk_pct": 1.0}],
        )
        assert adj.adjusted
        assert adj.final_risk_pct == 0.5
        assert adj.correlated_instrument == "GBPJPY"

    def test_xagusd_reduced_when_xauusd_open(self):
        """XAUUSD open at 1% → XAGUSD reduced to 0.5%."""
        adj = check_correlation_risk(
            "XAGUSD", 1.0,
            [{"symbol": "XAUUSD", "risk_pct": 1.0}],
        )
        assert adj.adjusted
        assert adj.final_risk_pct == 0.5
        assert adj.group_name == "PRECIOUS_METALS"

    def test_index_futures_alias_reduced_against_us_index_group(self):
        """YM and ES contract aliases resolve into the configured index group."""
        adj = check_correlation_risk(
            "YM", 1.0,
            [{"symbol": "ESM26-CME", "risk_pct": 1.0}],
        )
        assert adj.adjusted
        assert adj.final_risk_pct == 0.5
        assert adj.group_name == "US_INDICES"
        assert adj.correlated_instrument == "ESM26-CME"

    def test_nas100_reduced_when_us30_open(self):
        """Unit62: live NAS100 participates in the US index risk group."""
        adj = check_correlation_risk(
            "NAS100", 1.0,
            [{"symbol": "US30.cash", "risk_pct": 1.0}],
        )
        assert adj.adjusted
        assert adj.final_risk_pct == 0.5
        assert adj.group_name == "US_INDICES"
        assert adj.correlated_instrument == "US30.cash"

    def test_nq_futures_alias_reduced_when_ym_futures_open(self):
        """Unit62: NQ/MNQ aliases inherit NAS100's US index correlation budget."""
        adj = check_correlation_risk(
            "NQM26-CME", 1.0,
            [{"symbol": "YMM26-CME", "risk_pct": 1.0}],
        )
        assert adj.adjusted
        assert adj.final_risk_pct == 0.5
        assert adj.group_name == "US_INDICES"
        assert adj.correlated_instrument == "YMM26-CME"

    def test_same_underlying_broker_and_futures_alias_not_group_conflict(self):
        """US30 broker/cash/futures aliases collapse before same-symbol comparison."""
        adj = check_correlation_risk(
            "YM",
            1.0,
            [{"symbol": "US30.cash", "risk_pct": 1.0}],
        )
        assert not adj.adjusted
        assert adj.final_risk_pct == 1.0
        assert adj.reason == "no_correlation_conflict"

    def test_silver_futures_alias_reduced_against_gold_futures_alias(self):
        """SI/SIM contracts resolve into the precious-metals group."""
        adj = check_correlation_risk(
            "SIM26-CME", 1.0,
            [{"symbol": "GCM26-CME", "risk_pct": 1.0}],
        )
        assert adj.adjusted
        assert adj.final_risk_pct == 0.5
        assert adj.group_name == "PRECIOUS_METALS"


class TestSkipWhenBudgetExhausted:
    def test_skip_when_correlated_at_max(self):
        """If correlated position already at 1.5%, new trade gets 0% → skip."""
        adj = check_correlation_risk(
            "GBPUSD", 1.0,
            [{"symbol": "EURUSD", "risk_pct": 1.5}],
        )
        assert adj.adjusted
        assert adj.final_risk_pct == 0.0
        assert "skip" in adj.reason


class TestConfigOverride:
    def test_custom_groups_from_config(self):
        """Config-provided groups override defaults."""
        config = {
            "correlation_groups": {
                "CUSTOM": {
                    "instruments": ["XAUUSD", "EURJPY"],
                    "max_combined_risk_pct": 1.0,
                }
            }
        }
        adj = check_correlation_risk(
            "EURJPY", 1.0,
            [{"symbol": "XAUUSD", "risk_pct": 0.8}],
            config=config,
        )
        assert adj.adjusted
        assert abs(adj.final_risk_pct - 0.2) < 0.01
        assert adj.group_name == "CUSTOM"

    def test_default_groups_when_no_config(self):
        """Falls back to defaults when config has no correlation_groups."""
        adj = check_correlation_risk(
            "GBPJPY", 1.0,
            [{"symbol": "EURJPY", "risk_pct": 1.0}],
            config={},
        )
        assert adj.adjusted
        assert adj.final_risk_pct == 0.5
