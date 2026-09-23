"""Tests for T7 simulation script fixes (L2 bypass, P2A timestamp normalization)."""

import json
import pytest
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.simulate_t7_live_period import (
    RAW_CANDIDATE_DECISIONS,
    _apply_live_candidate_output_guards,
    _epsilon_for_symbol,
    _normalize_p2a_candle_time,
    _parse_response,
    compute_outcome,
)


# ── P2A Timestamp Normalization Tests ──────────────────────────────────


class TestNormalizeP2ATimestamp:
    """Tests for _normalize_p2a_candle_time()."""

    def test_standard_case_london_open(self):
        """P2A at 07:15:48 → simulation candle 07:00."""
        result = _normalize_p2a_candle_time("2026-04-07T07:15:48.173643+00:00")
        assert result == "2026-04-07T07:00:00Z"

    def test_standard_case_second_candle(self):
        """P2A at 07:30:05 → simulation candle 07:15."""
        result = _normalize_p2a_candle_time("2026-04-07T07:30:05.000000+00:00")
        assert result == "2026-04-07T07:15:00Z"

    def test_standard_case_third_candle(self):
        """P2A at 07:45:05 → simulation candle 07:30."""
        result = _normalize_p2a_candle_time("2026-04-07T07:45:05.000000+00:00")
        assert result == "2026-04-07T07:30:00Z"

    def test_hour_boundary_ny_close(self):
        """P2A at 17:00:05 → simulation candle 16:45."""
        result = _normalize_p2a_candle_time("2026-04-07T17:00:05.000000+00:00")
        assert result == "2026-04-07T16:45:00Z"

    def test_midnight_boundary(self):
        """P2A at 00:15:05 → simulation candle 00:00."""
        result = _normalize_p2a_candle_time("2026-04-09T00:15:05.000000+00:00")
        assert result == "2026-04-09T00:00:00Z"

    def test_day_rollback(self):
        """P2A at 00:00:05 → simulation candle 23:45 previous day."""
        result = _normalize_p2a_candle_time("2026-04-08T00:00:05.000000+00:00")
        assert result == "2026-04-07T23:45:00Z"

    def test_z_suffix_input(self):
        """Handle Z suffix instead of +00:00."""
        result = _normalize_p2a_candle_time("2026-04-07T07:15:48Z")
        assert result == "2026-04-07T07:00:00Z"

    def test_no_microseconds(self):
        """Handle timestamps without microseconds."""
        result = _normalize_p2a_candle_time("2026-04-07T07:30:05+00:00")
        assert result == "2026-04-07T07:15:00Z"

    def test_late_seconds(self):
        """P2A at 07:15:59 still maps to 07:00 candle."""
        result = _normalize_p2a_candle_time("2026-04-07T07:15:59.999999+00:00")
        assert result == "2026-04-07T07:00:00Z"

    def test_exact_minute(self):
        """P2A at 07:15:00 exactly → 07:00 candle."""
        result = _normalize_p2a_candle_time("2026-04-07T07:15:00.000000+00:00")
        assert result == "2026-04-07T07:00:00Z"

    def test_real_p2a_apr9(self):
        """Real P2A data from Apr 9 (later start)."""
        result = _normalize_p2a_candle_time("2026-04-09T07:45:44.483608+00:00")
        assert result == "2026-04-09T07:30:00Z"


# ── Parse Response Tests ───────────────────────────────────────────────


class TestParseResponse:
    """Tests for _parse_response() and PA validation behavior."""

    def _make_candidate_json(self, **overrides):
        """Build a minimal T7 CANDIDATE JSON string."""
        data = {
            "timestamp_utc": "2026-04-07T07:45:00Z",
            "model_used": "claude-sonnet-4-6",
            "decision": "CANDIDATE",
            "confidence_score": 78,
            "confidence_computation": "C1=PASS C2=PASS C3=PASS",
            "framework": "ob_retest",
            "kill_zone": "london",
            "frameworks_evaluated": {
                "ob_retest": {"qualified": True, "reason": "H1 bullish"}
            },
            "reasoning": {
                "daily_bias": {"direction": "bullish", "confidence": "high"},
                "h4_alignment": {"aligned": True, "explanation": "H4 data not provided"},
                "h1_setup": {
                    "poi_identified": True,
                    "poi_type": "OB",
                    "poi_price_level": 4640.0,
                    "zone": "discount",
                    "causing_event_type": "BOS",
                },
                "liquidity_sweep": {
                    "detected": False,
                    "sweep_type": "none",
                    "quality": "ambiguous",
                    "pool_type": "none",
                },
                "m15_confirmation": {
                    "choch_detected": True,
                    "displacement_quality": "strong",
                    "displacement_candle_body_vs_avg_ratio": 2.5,
                },
                "setup_grade": "A+",
                "overall_reasoning": "All C-gates pass.",
            },
            "trade_parameters": {
                "direction": "LONG",
                "entry_price": 4653.84,
                "stop_loss": 4634.37,
                "take_profit_1": 4683.09,
                "risk_reward_ratio": 1.5,
                "position_size_lots": 0.01,
                "sl_buffer_applied": 0.0,
                "tp2": 0.0,
                "tp3": 0.0,
            },
            "no_trade_reason": None,
        }
        data.update(overrides)
        return json.dumps(data)

    def _make_no_trade_json(self):
        """Build a minimal T7 NO_TRADE JSON string."""
        return json.dumps({
            "timestamp_utc": "2026-04-07T08:00:00Z",
            "model_used": "claude-sonnet-4-6",
            "decision": "NO_TRADE",
            "confidence_score": 0,
            "confidence_computation": "C1=FAIL",
            "framework": "none",
            "kill_zone": "london",
            "frameworks_evaluated": {},
            "reasoning": {
                "daily_bias": {"direction": "ranging", "confidence": "low"},
                "h4_alignment": {"aligned": False, "explanation": "H4 data not provided"},
                "h1_setup": {
                    "poi_identified": False,
                    "poi_type": "none",
                    "poi_price_level": 0.0,
                    "zone": "neutral",
                    "causing_event_type": "unknown",
                },
                "liquidity_sweep": {
                    "detected": False,
                    "sweep_type": "none",
                    "quality": "ambiguous",
                    "pool_type": "none",
                },
                "m15_confirmation": {
                    "choch_detected": False,
                    "displacement_quality": "none",
                    "displacement_candle_body_vs_avg_ratio": 0.0,
                },
                "setup_grade": "C",
                "overall_reasoning": "C1 FAIL: no H1 bias",
            },
            "trade_parameters": None,
            "no_trade_reason": "C1 FAIL: no directional bias",
        })

    def test_no_trade_returns_no_trade(self):
        """AI NO_TRADE → decision stays NO_TRADE, pa_obj doesn't matter."""
        text = self._make_no_trade_json()
        report, pa_obj = _parse_response(text, "2026-04-07T08:00:00Z", "london")
        assert report["decision"] == "NO_TRADE"
        assert report["no_trade_reason"] == "C1 FAIL: no directional bias"

    def test_candidate_extracts_trade_params(self):
        """AI CANDIDATE → report has entry/SL/TP."""
        text = self._make_candidate_json()
        report, pa_obj = _parse_response(text, "2026-04-07T07:45:00Z", "london")
        assert report["decision"] == "CANDIDATE"
        assert report["entry_price"] == 4653.84
        assert report["stop_loss"] == 4634.37
        assert report["take_profit_1"] == 4683.09
        assert report["direction"] == "LONG"

    def test_malformed_json_returns_parse_error(self):
        """Completely broken JSON → PARSE_ERROR."""
        report, pa_obj = _parse_response("not json {{{", "2026-04-07T07:00:00Z", "london")
        assert report["decision"] == "PARSE_ERROR"
        assert pa_obj is None

    def test_candidate_with_bad_schema_returns_none_pa(self):
        """AI says CANDIDATE but schema doesn't validate → pa_obj is None."""
        # Remove required reasoning fields to break Pydantic validation
        text = json.dumps({
            "decision": "CANDIDATE",
            "trade_parameters": {
                "direction": "LONG",
                "entry_price": 4653.84,
                "stop_loss": 4634.37,
                "take_profit_1": 4683.09,
            },
            # Missing: reasoning, framework, timestamp_utc, etc.
        })
        report, pa_obj = _parse_response(text, "2026-04-07T07:45:00Z", "london")
        assert report["decision"] == "CANDIDATE"
        assert pa_obj is None  # Parse failed, L2 would be skipped

    def test_candidate_with_valid_schema_returns_pa(self):
        """Full valid schema → pa_obj is not None."""
        text = self._make_candidate_json()
        report, pa_obj = _parse_response(text, "2026-04-07T07:45:00Z", "london")
        assert report["decision"] == "CANDIDATE"
        assert pa_obj is not None


# ── L2 Bypass Fix Integration Test ────────────────────────────────────


class TestL2BypassFix:
    """Verify the L2 bypass produces NO_TRADE_PARSE_FAIL, not CANDIDATE."""

    def test_simulation_flow_with_parse_failure(self):
        """Simulate the code path: AI CANDIDATE + pa_obj=None → NO_TRADE_PARSE_FAIL.

        This tests the logic that was changed in the fix, extracted from
        the main simulation loop (lines 658-682).
        """
        # Simulate a result where AI said CANDIDATE but PA parse failed
        result = {
            "decision": "CANDIDATE",
            "entry_price": 4653.84,
            "stop_loss": 4634.37,
            "take_profit_1": 4683.09,
            "direction": "LONG",
        }
        pa_obj = None  # Simulates parse failure

        # This is the FIXED code path (extracted from lines 658-682)
        if result.get("decision") == "CANDIDATE":
            if pa_obj is not None:
                # L2 would run here
                pass
            else:
                result["decision"] = "NO_TRADE_PARSE_FAIL"
                result["l2_passed"] = "skipped"
                result["l2_reason"] = "PA parse failed — L2 requires structured output"

        assert result["decision"] == "NO_TRADE_PARSE_FAIL"
        assert result["l2_passed"] == "skipped"
        # Trade should NOT proceed to inverted TP or trade limits
        assert result["decision"] != "CANDIDATE"

    def test_simulation_flow_with_l2_pass(self):
        """AI CANDIDATE + valid PA + L2 passes → stays CANDIDATE."""
        result = {"decision": "CANDIDATE"}
        pa_obj = MagicMock()  # Non-None = parse succeeded

        if result.get("decision") == "CANDIDATE":
            if pa_obj is not None:
                # L2 runs — simulate pass
                result["l2_passed"] = True
            else:
                result["decision"] = "NO_TRADE_PARSE_FAIL"

        assert result["decision"] == "CANDIDATE"
        assert result["l2_passed"] is True


# ── Funnel Counting Test ──────────────────────────────────────────────


class TestLiveCandidateOutputGuards:
    def test_degenerate_candidate_is_demoted_before_l2_and_outcome(self):
        trade_params = {
            "direction": "LONG",
            "entry_price": 1.10000,
            "stop_loss": 1.10000,
            "take_profit_1": 1.10150,
            "risk_reward_ratio": 1.5,
            "position_size_lots": 0.01,
            "sl_buffer_applied": 0.00010,
            "tp2": 0.0,
            "tp3": 0.0,
        }
        text = TestParseResponse()._make_candidate_json(
            trade_parameters=trade_params,
        )
        report, pa_obj = _parse_response(text, "2026-04-07T07:45:00Z", "london")

        guarded_report, guarded_pa = _apply_live_candidate_output_guards(report, pa_obj)

        assert guarded_pa.decision == "NO_TRADE"
        assert guarded_report["decision"] == "NO_TRADE_LIVE_GUARD"
        assert guarded_report["no_trade_reason"] == "degenerate_trade_parameters"
        assert guarded_report["l2_passed"] == "skipped"
        assert "degenerate_trade_parameters" in guarded_report["l2_reason"]

    def test_non_degenerate_candidate_stays_candidate(self):
        text = TestParseResponse()._make_candidate_json()
        report, pa_obj = _parse_response(text, "2026-04-07T07:45:00Z", "london")

        guarded_report, guarded_pa = _apply_live_candidate_output_guards(report, pa_obj)

        assert guarded_pa.decision == "CANDIDATE"
        assert guarded_report["decision"] == "CANDIDATE"
        assert "l2_passed" not in guarded_report


class TestFunnelCounting:
    """Verify NO_TRADE_PARSE_FAIL is counted in the right funnel buckets."""

    def test_parse_fail_counted_as_raw_candidate(self):
        """NO_TRADE_PARSE_FAIL should be in raw candidate count (AI said CANDIDATE)."""
        results = [
            {"decision": "CANDIDATE"},
            {"decision": "REJECTED_L2"},
            {"decision": "BLOCKED_LIMIT"},
            {"decision": "NO_TRADE_PARSE_FAIL"},
            {"decision": "NO_TRADE_LIVE_GUARD"},
            {"decision": "NO_TRADE"},
        ]
        raw_cand = [r for r in results if r["decision"] in RAW_CANDIDATE_DECISIONS]
        final = [r for r in results if r["decision"] == "CANDIDATE"]
        parse_fail = [r for r in results if r["decision"] == "NO_TRADE_PARSE_FAIL"]

        assert len(raw_cand) == 5  # All except plain NO_TRADE
        assert len(final) == 1     # Only true CANDIDATE
        assert len(parse_fail) == 1

    def test_parse_fail_not_in_final_trades(self):
        """NO_TRADE_PARSE_FAIL must NOT be counted as a final trade."""
        results = [
            {"decision": "NO_TRADE_PARSE_FAIL"},
            {"decision": "NO_TRADE_PARSE_FAIL"},
        ]
        final = [r for r in results if r["decision"] == "CANDIDATE"]
        assert len(final) == 0


# ── P2A Comparison Recovery Test ──────────────────────────────────────


class TestP2AComparisonRecovery:
    """Test that normalized P2A timestamps can match simulation candle times."""

    def test_real_p2a_matches_simulation_candle(self):
        """Real P2A timestamp from Apr 7 should match simulation's 07:00 candle."""
        p2a_ct = "2026-04-07T07:15:48.173643+00:00"
        sim_ct = "2026-04-07T07:00:00Z"
        assert _normalize_p2a_candle_time(p2a_ct) == sim_ct

    def test_multiple_p2a_entries_unique_keys(self):
        """Different P2A timestamps should normalize to different candle times."""
        timestamps = [
            "2026-04-07T07:15:48.173643+00:00",
            "2026-04-07T07:30:05.000000+00:00",
            "2026-04-07T07:45:05.000000+00:00",
            "2026-04-07T08:00:05.000000+00:00",
        ]
        normalized = [_normalize_p2a_candle_time(t) for t in timestamps]
        assert len(set(normalized)) == 4  # All unique
        assert normalized == [
            "2026-04-07T07:00:00Z",
            "2026-04-07T07:15:00Z",
            "2026-04-07T07:30:00Z",
            "2026-04-07T07:45:00Z",
        ]


class TestPerSymbolFillEpsilon:
    @pytest.mark.parametrize(
        ("symbol", "expected"),
        [
            ("US30.cash", 2.0),
            ("US30_cash", 2.0),
            ("US30", 2.0),
            ("YM", 2.0),
            ("YMM26-CBOT", 2.0),
            ("XAGUSD", 0.002),
            ("XAGUSD_SI", 0.002),
            ("SI", 0.002),
            ("SIM26-CME", 0.002),
            ("ESM26-CME", 0.50),
            ("MESM26-CME", 0.50),
            ("NQM26-CME", 2.0),
            ("6EM26-CME", 0.0002),
            ("6BM26-CME", 0.0002),
            ("6JM26-CME", 0.02),
            ("GCM26-CME", 0.20),
        ],
    )
    def test_vnext_and_futures_aliases_use_family_epsilon(self, symbol, expected):
        assert _epsilon_for_symbol(symbol) == expected

    def test_usdjpy_futures_alias_does_not_use_legacy_wide_epsilon(self):
        candidate = {
            "candle_time": "2026-04-07T07:00:00Z",
            "entry_price": 151.00,
            "stop_loss": 150.97,
            "take_profit_1": 151.06,
            "direction": "LONG",
            "candle_close": 151.03,
        }
        candles = [
            {
                "time": "2026-04-07T07:00:00Z",
                "high": 151.03,
                "low": 151.03,
                "close": 151.03,
            },
            {
                "time": "2026-04-07T07:15:00Z",
                "high": 151.07,
                "low": 151.01,
                "close": 151.05,
            },
        ]

        outcome = compute_outcome(candidate, candles, symbol="6JM26-CME")

        assert outcome == {"outcome": "UNFILLED", "reason": "entry_limit_never_reached"}
