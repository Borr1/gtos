"""Tests for pool_type normalization in _normalize_pa_fields().

Covers the fix for 289 parse failures caused by AI returning uppercase
("PDH") or compound ("session_high / equal_highs") pool_type values
that don't match the Pydantic Literal constraint.
"""

import json
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.components.primary_analyzer import _normalize_pa_fields
from src.models.analysis_models import PrimaryAnalysisOutput


def _make_pa_data(pool_type: str = "none", decision: str = "CANDIDATE") -> dict:
    """Build a minimal PA dict with the given pool_type."""
    data = {
        "timestamp_utc": "2026-01-15T13:15:00Z",
        "model_used": "claude-sonnet-4-6",
        "decision": decision,
        "confidence_score": 78,
        "confidence_computation": "C1=PASS C2=PASS C3=PASS",
        "framework": "ob_retest",
        "kill_zone": "london",
        "frameworks_evaluated": {
            "ob_retest": {"qualified": True, "reason": "test"}
        },
        "reasoning": {
            "daily_bias": {
                "direction": "bullish",
                "confidence": "high",
            },
            "h4_alignment": {
                "aligned": True,
                "explanation": "H4 data not provided",
            },
            "h1_setup": {
                "poi_identified": True,
                "poi_type": "OB",
                "poi_price_level": 4600.0,
                "zone": "discount",
                "causing_event_type": "BOS",
            },
            "liquidity_sweep": {
                "detected": True,
                "pool_type": pool_type,
                "sweep_quality": "clean",
                "sweep_price": 4580.0,
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
            "entry_price": 4618.93,
            "stop_loss": 4597.79,
            "take_profit_1": 4650.62,
            "risk_reward_ratio": 1.5,
            "position_size_lots": 0.01,
        },
        "no_trade_reason": None,
    }
    return data


class TestPoolTypeNormalization:
    """Tests for pool_type normalization in _normalize_pa_fields()."""

    # ── Already-valid values should pass through unchanged ──

    @pytest.mark.parametrize("pool_type", [
        "asian_high", "asian_low", "pdh", "pdl",
        "equal_highs", "equal_lows",
        "session_high", "session_low",
        "london_high", "london_low",
        "none",
    ])
    def test_valid_pool_types_unchanged(self, pool_type):
        data = _make_pa_data(pool_type=pool_type)
        _normalize_pa_fields(data)
        assert data["reasoning"]["liquidity_sweep"]["pool_type"] == pool_type
        PrimaryAnalysisOutput.model_validate(data)

    # ── Uppercase variants (the #1 cause: 142/289 failures) ──

    def test_pdh_uppercase(self):
        data = _make_pa_data(pool_type="PDH")
        _normalize_pa_fields(data)
        assert data["reasoning"]["liquidity_sweep"]["pool_type"] == "pdh"
        PrimaryAnalysisOutput.model_validate(data)

    def test_pdl_uppercase(self):
        data = _make_pa_data(pool_type="PDL")
        _normalize_pa_fields(data)
        assert data["reasoning"]["liquidity_sweep"]["pool_type"] == "pdl"
        PrimaryAnalysisOutput.model_validate(data)

    # ── Compound values with "/" separator ──

    def test_compound_slash(self):
        data = _make_pa_data(pool_type="session_low / london_low")
        _normalize_pa_fields(data)
        assert data["reasoning"]["liquidity_sweep"]["pool_type"] == "session_low"
        PrimaryAnalysisOutput.model_validate(data)

    def test_compound_slash_uppercase(self):
        data = _make_pa_data(pool_type="asian_high / PDH")
        _normalize_pa_fields(data)
        assert data["reasoning"]["liquidity_sweep"]["pool_type"] == "asian_high"
        PrimaryAnalysisOutput.model_validate(data)

    def test_compound_three_values(self):
        data = _make_pa_data(pool_type="session_high / london_high / equal_highs")
        _normalize_pa_fields(data)
        assert data["reasoning"]["liquidity_sweep"]["pool_type"] == "session_high"
        PrimaryAnalysisOutput.model_validate(data)

    # ── Compound values with "and" separator ──

    def test_compound_and(self):
        data = _make_pa_data(pool_type="PDL and session_high")
        _normalize_pa_fields(data)
        assert data["reasoning"]["liquidity_sweep"]["pool_type"] == "pdl"
        PrimaryAnalysisOutput.model_validate(data)

    # ── Compound values with "+" separator ──

    def test_compound_plus(self):
        data = _make_pa_data(pool_type="PDL sweep + equal highs run")
        _normalize_pa_fields(data)
        assert data["reasoning"]["liquidity_sweep"]["pool_type"] == "pdl"
        PrimaryAnalysisOutput.model_validate(data)

    # ── Trailing noise words ──

    def test_trailing_noise_sweep(self):
        data = _make_pa_data(pool_type="PDH sweep")
        _normalize_pa_fields(data)
        assert data["reasoning"]["liquidity_sweep"]["pool_type"] == "pdh"
        PrimaryAnalysisOutput.model_validate(data)

    # ── Legacy map: equal_high → equal_highs ──

    def test_equal_high_singular(self):
        data = _make_pa_data(pool_type="equal_high")
        _normalize_pa_fields(data)
        assert data["reasoning"]["liquidity_sweep"]["pool_type"] == "equal_highs"
        PrimaryAnalysisOutput.model_validate(data)

    def test_equal_low_singular(self):
        data = _make_pa_data(pool_type="equal_low")
        _normalize_pa_fields(data)
        assert data["reasoning"]["liquidity_sweep"]["pool_type"] == "equal_lows"
        PrimaryAnalysisOutput.model_validate(data)

    # ── Unrecognizable values fall back to "none" ──

    def test_unrecognizable_falls_to_none(self):
        data = _make_pa_data(pool_type="some_random_nonsense")
        _normalize_pa_fields(data)
        assert data["reasoning"]["liquidity_sweep"]["pool_type"] == "none"
        PrimaryAnalysisOutput.model_validate(data)

    def test_empty_string_falls_to_none(self):
        data = _make_pa_data(pool_type="")
        _normalize_pa_fields(data)
        assert data["reasoning"]["liquidity_sweep"]["pool_type"] == "none"
        PrimaryAnalysisOutput.model_validate(data)


class TestPoolTypeRealFailures:
    """Test against actual pool_type values from the 289 simulation failures."""

    REAL_VALUES = [
        ("PDH", "pdh"),
        ("PDL", "pdl"),
        ("session_low / london_low", "session_low"),
        ("asian_high / PDH", "asian_high"),
        ("asian_high / pdh", "asian_high"),
        ("equal_highs / session_high", "equal_highs"),
        ("session_high / equal_highs", "session_high"),
        ("session_high / london_high", "session_high"),
        ("asian_high / equal_highs", "asian_high"),
        ("asian_low / session_low / london_low", "asian_low"),
        ("PDL sweep + equal highs run", "pdl"),
        ("PDH sweep", "pdh"),
        ("asian_low / session_low", "asian_low"),
        ("session_high / london_high / equal_highs", "session_high"),
        ("PDL and session_high", "pdl"),
        ("PDL / session_high", "pdl"),
        ("session_low / equal_highs", "session_low"),
        ("equal_highs / session_high / london_high", "equal_highs"),
        ("PDH equal highs", "pdh"),
        ("asian_high / session_high / london_high", "asian_high"),
    ]

    @pytest.mark.parametrize("raw_value,expected", REAL_VALUES)
    def test_real_failure_normalizes(self, raw_value, expected):
        data = _make_pa_data(pool_type=raw_value)
        _normalize_pa_fields(data)
        assert data["reasoning"]["liquidity_sweep"]["pool_type"] == expected
        # Must pass full Pydantic validation
        PrimaryAnalysisOutput.model_validate(data)
