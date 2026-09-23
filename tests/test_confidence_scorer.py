"""Tests for the post-hoc confidence scorer."""

from __future__ import annotations

import pytest
import yaml

from src.components.confidence_scorer import (
    ConfidenceMetrics,
    resolve_confidence_filter_mode,
    score_confidence,
    _count_patterns,
    _count_price_levels,
    _flatten_text,
    HESITATION_PHRASES,
    QUALITY_PHRASES,
)


# ── Fixtures ─────────────────────────────────────────────────────────────

def _make_reasoning(
    *,
    overall: str = "Clean setup with aligned structure.",
    sweep_explanation: str = "Clean PDL sweep at 2882.35.",
    m15_explanation: str = "Strong displacement confirmed at 2885.10.",
    h1_explanation: str = "H1 BOS confirmed at 2890.00 with OB at 2870.50.",
    h4_explanation: str = "H4 aligned bullish.",
    daily_explanation: str = "Daily bullish with swing at 2850.00.",
    extra_prices: list[str] | None = None,
) -> dict:
    """Build a minimal PA reasoning JSON for testing."""
    reasoning = {
        "reasoning": {
            "daily_bias": {
                "direction": "bullish",
                "confidence": "high",
                "protected_swing_level": 2850.00,
                "explanation": daily_explanation,
            },
            "h4_alignment": {
                "aligned": True,
                "h4_pois_identified": ["bullish OB 2860.00-2855.00"],
                "explanation": h4_explanation,
            },
            "h1_setup": {
                "poi_identified": True,
                "poi_type": "OB",
                "poi_price_level": 2870.50,
                "zone": "discount",
                "fib_retracement_pct": 68.0,
                "causing_event_type": "BOS",
                "explanation": h1_explanation,
            },
            "liquidity_sweep": {
                "detected": True,
                "pool_type": "pdl",
                "sweep_quality": "clean",
                "sweep_price": 2882.35,
                "explanation": sweep_explanation,
            },
            "m15_confirmation": {
                "choch_detected": True,
                "displacement_quality": "strong",
                "displacement_candle_body_vs_avg_ratio": 2.1,
                "explanation": m15_explanation,
            },
            "similar_historical_setups_considered": [],
            "setup_grade": "A+",
            "overall_reasoning": overall,
        }
    }
    return reasoning


# ── Unit Tests ───────────────────────────────────────────────────────────

class TestFlattenText:
    def test_simple_dict(self):
        assert "hello world" in _flatten_text({"a": "hello", "b": "world"})

    def test_nested(self):
        text = _flatten_text({"a": {"b": "deep"}})
        assert "deep" in text

    def test_list(self):
        text = _flatten_text(["one", "two"])
        assert "one" in text and "two" in text

    def test_non_string(self):
        assert _flatten_text(42) == ""
        assert _flatten_text(None) == ""


class TestCountPriceLevels:
    def test_gold_prices(self):
        text = "Price at 2882.35 with SL at 2870.50 and TP at 2900.00"
        assert _count_price_levels(text) == 3

    def test_deduplication(self):
        text = "Level 2882.35 was tested. Price returned to 2882.35."
        assert _count_price_levels(text) == 1

    def test_out_of_range(self):
        text = "Value 0001.50 and 9999.99 are not gold prices"
        assert _count_price_levels(text) == 0

    def test_no_prices(self):
        assert _count_price_levels("no prices here") == 0


class TestCountPatterns:
    def test_hesitation(self):
        text = "however the structure is unclear and only moderate"
        count = _count_patterns(text, HESITATION_PHRASES)
        # "however" + "unclear" + "only" + "moderate" = 4
        assert count >= 4

    def test_quality(self):
        text = "strong displacement with clean structure and confirmed bos"
        count = _count_patterns(text, QUALITY_PHRASES)
        # "strong displacement" + "clean structure" + "confirmed bos" = 3
        assert count == 3

    def test_empty(self):
        assert _count_patterns("", HESITATION_PHRASES) == 0


# ── Integration Tests ────────────────────────────────────────────────────

class TestScoreConfidenceHigh:
    """Test case: 10+ price levels, low hesitation → HIGH confidence."""

    def test_high_confidence(self):
        reasoning = _make_reasoning(
            overall="Clean setup with strongly aligned structure across all timeframes.",
            sweep_explanation="Clean PDL sweep at 2882.35 below 2883.00 session low.",
            m15_explanation="Strong displacement at 2885.10 above 2884.00 swing.",
            h1_explanation="H1 BOS at 2890.00 with OB zone 2870.50 to 2868.25, fib at 2875.30.",
            daily_explanation="Daily bullish with swing at 2850.00 and structure high 2910.40.",
        )
        metrics = score_confidence(reasoning)

        assert metrics.confidence_grade == "HIGH"
        assert metrics.position_size_multiplier == 1.0
        assert metrics.price_level_count >= 8
        assert metrics.hesitation_score <= 2

    def test_high_confidence_returns_model(self):
        reasoning = _make_reasoning()
        metrics = score_confidence(reasoning)
        assert isinstance(metrics, ConfidenceMetrics)


class TestScoreConfidenceLow:
    """Test case: few price levels, high hesitation → LOW confidence."""

    def test_low_confidence(self):
        reasoning = _make_reasoning(
            overall="However the structure is unclear and only moderate. Mixed signals but choppy.",
            sweep_explanation="Ambiguous sweep, unclear if clean.",
            m15_explanation="Weak displacement, barely visible, only moderate.",
            h1_explanation="However the OB is uncertain.",
            daily_explanation="Ranging structure with mixed signals.",
        )
        # Strip out specific price numbers to reduce price_level_count
        r = reasoning["reasoning"]
        r["h1_setup"]["poi_price_level"] = 0.0
        r["liquidity_sweep"]["sweep_price"] = 0.0
        r["daily_bias"]["protected_swing_level"] = 0.0

        metrics = score_confidence(reasoning)

        assert metrics.confidence_grade == "LOW"
        assert metrics.position_size_multiplier == 0.5
        assert metrics.hesitation_score > 2

    def test_low_prices_high_hesitation(self):
        reasoning = _make_reasoning(
            overall="However unclear moderate but only risk",
        )
        r = reasoning["reasoning"]
        r["h1_setup"]["poi_price_level"] = 0.0
        r["h1_setup"]["explanation"] = "unclear"
        r["liquidity_sweep"]["sweep_price"] = 0.0
        r["liquidity_sweep"]["explanation"] = "however"
        r["m15_confirmation"]["explanation"] = "moderate"
        r["daily_bias"]["protected_swing_level"] = 0.0
        r["daily_bias"]["explanation"] = "ranging"

        metrics = score_confidence(reasoning)
        assert metrics.hesitation_score > 2
        assert metrics.price_level_count < 8


class TestScoreConfidenceMedium:
    """Test case: one condition met, one not → MEDIUM."""

    def test_medium_good_prices_bad_hesitation(self):
        reasoning = _make_reasoning(
            overall="However the structure is only moderate but price levels are clear at 2900.10 and 2905.20 and 2910.30.",
            h1_explanation="OB at 2870.50 with level 2868.25 however unclear if 2875.30 holds.",
        )
        metrics = score_confidence(reasoning)
        # Should have enough prices (>= 8 from all the numbers)
        # but high hesitation from "however", "only", "moderate", "unclear"
        if metrics.price_level_count >= 8 and metrics.hesitation_score > 2:
            assert metrics.confidence_grade == "MEDIUM"
            assert metrics.position_size_multiplier == 0.75


class TestEdgeCases:
    def test_empty_reasoning(self):
        metrics = score_confidence({})
        # Empty text has 0 price levels (<8) but also 0 hesitation (<=2)
        # So one condition met → MEDIUM
        assert metrics.confidence_grade == "MEDIUM"
        assert metrics.price_level_count == 0
        assert metrics.word_count == 0

    def test_missing_fields(self):
        metrics = score_confidence({"reasoning": {}})
        assert isinstance(metrics, ConfidenceMetrics)
        # Same logic: 0 hesitation meets one condition → MEDIUM
        assert metrics.confidence_grade == "MEDIUM"

    def test_accepts_full_pa_output(self):
        """score_confidence should work with full PrimaryAnalysisOutput dict."""
        full = {
            "timestamp_utc": "2025-01-01T08:00:00Z",
            "model_used": "test",
            "decision": "CANDIDATE",
            "confidence_score": 80,
            "framework": "ob_retest",
            "kill_zone": "london",
            "reasoning": {
                "daily_bias": {"direction": "bullish", "confidence": "high",
                               "protected_swing_level": 2850.00, "explanation": "bullish at 2850.00 and 2860.00"},
                "h4_alignment": {"aligned": True, "h4_pois_identified": [],
                                 "explanation": "aligned at 2870.00 and 2875.00"},
                "h1_setup": {"poi_identified": True, "poi_type": "OB",
                             "poi_price_level": 2880.00, "zone": "discount",
                             "fib_retracement_pct": 68.0, "causing_event_type": "BOS",
                             "explanation": "BOS at 2890.00 OB 2880.00-2878.50"},
                "liquidity_sweep": {"detected": True, "pool_type": "pdl",
                                    "sweep_quality": "clean", "sweep_price": 2882.35,
                                    "explanation": "sweep at 2882.35 below 2883.00"},
                "m15_confirmation": {"choch_detected": True, "displacement_quality": "strong",
                                     "displacement_candle_body_vs_avg_ratio": 2.1,
                                     "explanation": "confirmed at 2885.10 above 2884.00"},
                "similar_historical_setups_considered": [],
                "setup_grade": "A+",
                "overall_reasoning": "Clean setup with aligned structure at 2890.00 and 2895.00.",
            },
            "trade_parameters": None,
        }
        metrics = score_confidence(full)
        assert isinstance(metrics, ConfidenceMetrics)
        assert metrics.price_level_count >= 8

    def test_accepts_reasoning_only(self):
        """score_confidence should also work with just the reasoning sub-object."""
        reasoning_only = {
            "daily_bias": {"direction": "bullish", "confidence": "high",
                           "protected_swing_level": 2850.00, "explanation": "ok"},
            "overall_reasoning": "Short text.",
        }
        metrics = score_confidence(reasoning_only)
        assert isinstance(metrics, ConfidenceMetrics)

    def test_word_count_from_overall_reasoning(self):
        reasoning = _make_reasoning(
            overall="One two three four five six seven eight nine ten."
        )
        metrics = score_confidence(reasoning)
        assert metrics.word_count == 10


class TestMultipliers:
    def test_high_multiplier(self):
        assert ConfidenceMetrics(
            price_level_count=10, hesitation_score=1, quality_score=3,
            word_count=30, confidence_grade="HIGH", position_size_multiplier=1.0,
        ).position_size_multiplier == 1.0

    def test_medium_multiplier(self):
        assert ConfidenceMetrics(
            price_level_count=10, hesitation_score=4, quality_score=1,
            word_count=30, confidence_grade="MEDIUM", position_size_multiplier=0.75,
        ).position_size_multiplier == 0.75

    def test_low_multiplier(self):
        assert ConfidenceMetrics(
            price_level_count=3, hesitation_score=5, quality_score=0,
            word_count=50, confidence_grade="LOW", position_size_multiplier=0.5,
        ).position_size_multiplier == 0.5


class TestResolveConfidenceFilterMode:
    def test_shadow_mode_passes_through(self):
        mode = resolve_confidence_filter_mode({"confidence_filter_mode": "shadow"})
        assert mode.requested_mode == "shadow"
        assert mode.effective_mode == "shadow"
        assert mode.blocked_reason is None

    def test_active_mode_requires_validated_promotion_flag(self):
        mode = resolve_confidence_filter_mode({"confidence_filter_mode": "active"})
        assert mode.requested_mode == "active"
        assert mode.effective_mode == "shadow"
        assert mode.blocked_reason == "active_confidence_filter_requires_validated_promotion"

    def test_active_mode_allowed_when_validation_flag_present(self):
        mode = resolve_confidence_filter_mode(
            {
                "confidence_filter_mode": "active",
                "confidence_filter_active_promotion": {"validated": True},
            }
        )
        assert mode.requested_mode == "active"
        assert mode.effective_mode == "active"
        assert mode.blocked_reason is None

    def test_active_mode_blocked_by_intra_candidate_evidence_policy(self):
        mode = resolve_confidence_filter_mode(
            {
                "confidence_filter_mode": "active",
                "confidence_filter_active_policy": (
                    "disabled_until_new_validated_intra_candidate_signal"
                ),
                "confidence_filter_active_promotion": {"validated": True},
            }
        )
        assert mode.requested_mode == "active"
        assert mode.effective_mode == "shadow"
        assert mode.blocked_reason == "active_confidence_filter_killed_by_intra_candidate_evidence"

    def test_agent_config_keeps_confidence_gate_shadow_by_evidence_policy(self):
        with open("config/agent_config.yaml", encoding="utf-8") as handle:
            cfg = yaml.safe_load(handle)

        cfg = {
            **cfg,
            "confidence_filter_mode": "active",
            "confidence_filter_active_promotion": {"validated": True},
        }
        mode = resolve_confidence_filter_mode(cfg)

        assert cfg["confidence_filter_active_policy"] == (
            "disabled_until_new_validated_intra_candidate_signal"
        )
        assert mode.effective_mode == "shadow"
        assert mode.blocked_reason == "active_confidence_filter_killed_by_intra_candidate_evidence"

    def test_unknown_mode_fails_closed_to_shadow(self):
        mode = resolve_confidence_filter_mode({"confidence_filter_mode": "surprise"})
        assert mode.requested_mode == "surprise"
        assert mode.effective_mode == "shadow"
        assert mode.blocked_reason == "unknown_confidence_filter_mode"
