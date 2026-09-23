"""Tests for Component 6 — Adaptive Review System.

All tests mock the Anthropic API — no real API calls.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.components.adaptive_review import (
    PROTECTED_PARAMETERS,
    AdaptiveReviewSystem,
)
from src.components.knowledge_base import KnowledgeBase
from src.models.trade_models import TradeEvent, TradeRecord
from src.utils.file_io import atomic_write, load_json


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def config():
    return {
        "ai": {
            "review_model": "claude-sonnet-4-20250514",
            "api_timeout_seconds": 30,
            "max_api_retries": 1,
        },
        "adaptation": {
            "tier2_deviation_threshold": 0.15,
            "tier2_min_samples": 20,
            "tier3_min_samples": 50,
            "max_modifications_per_50_trades": 1,
        },
    }


@pytest.fixture
def kb(tmp_path, monkeypatch):
    """KnowledgeBase backed by tmp directory."""
    import src.utils.file_io as fio
    monkeypatch.setattr(fio, "KNOWLEDGE_BASE_DIR", tmp_path)
    (tmp_path / "pipeline_state").mkdir(parents=True, exist_ok=True)
    kb = KnowledgeBase(base_path=str(tmp_path))
    kb.initialize_rules()
    return kb


def _make_review(config, kb):
    """Build an AdaptiveReviewSystem with a mocked Anthropic client."""
    with patch("src.components.adaptive_review.Anthropic") as MockCls:
        mock_client = MagicMock()
        MockCls.return_value = mock_client
        review = AdaptiveReviewSystem(config, kb)
    return review


def _make_trade(
    trade_id: str = "tr_2026-01-15_001",
    date: str = "2026-01-15",
    day_of_week: str = "Wednesday",
    direction: str = "LONG",
    outcome: str = "WIN",
    r_multiple: float = 2.5,
    setup_grade: str = "A",
    liquidity_swept: str = "asian_low",
    displacement_quality: str = "strong",
    regime: str = "trending",
    entry_price: float = 3040.0,
    stop_loss: float = 3034.0,
    take_profit_1: float = 3052.0,
    **kwargs,
) -> TradeRecord:
    return TradeRecord(
        trade_id=trade_id,
        date=date,
        day_of_week=day_of_week,
        direction=direction,
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit_1=take_profit_1,
        risk_reward_ratio=3.0,
        lifecycle_state="CLOSED",
        outcome=outcome,
        r_multiple=r_multiple,
        setup_grade=setup_grade,
        daily_bias="bullish",
        h4_aligned=True,
        liquidity_swept=liquidity_swept,
        displacement_quality=displacement_quality,
        regime=regime,
        **kwargs,
    )


# ═══════════════════════════════════════════════════════════════════════
# test_post_trade_update_stats
# ═══════════════════════════════════════════════════════════════════════

class TestPostTradeUpdateStats:

    def test_stats_update_win(self, config, kb):
        review = _make_review(config, kb)
        trade = _make_trade(outcome="WIN", r_multiple=2.5)

        review.post_trade_update(trade)

        stats = kb.load_rolling_stats()
        assert stats["total_trades"] == 1
        assert stats["wins"] == 1
        assert stats["win_rate"] == 1.0

    def test_stats_update_loss(self, config, kb):
        review = _make_review(config, kb)
        trade = _make_trade(outcome="LOSS", r_multiple=-1.0)

        review.post_trade_update(trade)

        stats = kb.load_rolling_stats()
        assert stats["total_trades"] == 1
        assert stats["losses"] == 1
        assert stats["win_rate"] == 0.0

    def test_stats_update_multiple_trades(self, config, kb):
        review = _make_review(config, kb)

        for i in range(3):
            t = _make_trade(
                trade_id=f"tr_2026-01-{15+i}_001",
                date=f"2026-01-{15+i}",
                outcome="WIN", r_multiple=2.0,
            )
            review.post_trade_update(t)

        t_loss = _make_trade(
            trade_id="tr_2026-01-18_001",
            date="2026-01-18",
            outcome="LOSS", r_multiple=-1.0,
        )
        review.post_trade_update(t_loss)

        stats = kb.load_rolling_stats()
        assert stats["total_trades"] == 4
        assert stats["wins"] == 3
        assert stats["losses"] == 1
        assert abs(stats["win_rate"] - 0.75) < 0.01

    def test_trade_index_updated(self, config, kb):
        review = _make_review(config, kb)
        trade = _make_trade()

        review.post_trade_update(trade)

        trades = kb.get_last_n_trades(10)
        assert len(trades) == 1
        assert trades[0]["trade_id"] == trade.trade_id

    def test_quality_scores_written(self, config, kb):
        review = _make_review(config, kb)
        trade = _make_trade()

        review.post_trade_update(trade)

        scores_data = load_json(kb.base / "statistics" / "quality_scores.json")
        assert len(scores_data["scores"]) == 1
        assert scores_data["scores"][0]["trade_id"] == trade.trade_id
        assert scores_data["scores"][0]["deterministic_score"] > 0


# ═══════════════════════════════════════════════════════════════════════
# test_deterministic_scoring
# ═══════════════════════════════════════════════════════════════════════

class TestDeterministicScoring:

    def test_perfect_trade_scores_high(self, config, kb):
        trade = _make_trade(
            actual_risk_pct=1.0,
            position_size_lots=0.08,
            events=[
                TradeEvent(
                    type="PARTIAL_TP1", time="T1",
                    price=3052.0, remaining_pct=0.50,
                ),
            ],
        )
        result = AdaptiveReviewSystem.score_trade_deterministic(trade)

        assert result["deterministic_score"] == 100.0
        checks = result["deterministic_checks"]
        assert checks["risk_exactly_1pct"] is True
        assert checks["sl_correct"] is True
        assert checks["position_size_correct"] is True
        assert checks["partials_correct"] is True

    def test_wrong_risk_fails_check(self):
        trade = _make_trade(actual_risk_pct=2.5)
        result = AdaptiveReviewSystem.score_trade_deterministic(trade)
        assert result["deterministic_checks"]["risk_exactly_1pct"] is False

    def test_sl_wrong_direction_fails(self):
        # LONG with SL above entry
        trade = _make_trade(direction="LONG", entry_price=3040, stop_loss=3050)
        result = AdaptiveReviewSystem.score_trade_deterministic(trade)
        assert result["deterministic_checks"]["sl_correct"] is False

    def test_short_sl_correct(self):
        trade = _make_trade(
            direction="SHORT", entry_price=3060, stop_loss=3066,
        )
        result = AdaptiveReviewSystem.score_trade_deterministic(trade)
        assert result["deterministic_checks"]["sl_correct"] is True

    def test_short_sl_wrong(self):
        trade = _make_trade(
            direction="SHORT", entry_price=3060, stop_loss=3050,
        )
        result = AdaptiveReviewSystem.score_trade_deterministic(trade)
        assert result["deterministic_checks"]["sl_correct"] is False

    def test_no_position_size_fails(self):
        trade = _make_trade(position_size_lots=0.0)
        result = AdaptiveReviewSystem.score_trade_deterministic(trade)
        assert result["deterministic_checks"]["position_size_correct"] is False

    def test_partial_score_calculation(self):
        # Fail 2 out of 6 checks
        trade = _make_trade(
            actual_risk_pct=3.0,   # fails risk check
            position_size_lots=0,  # fails position size
        )
        result = AdaptiveReviewSystem.score_trade_deterministic(trade)
        # 4/6 pass = 66.7%
        assert 65 < result["deterministic_score"] < 68


# ═══════════════════════════════════════════════════════════════════════
# test_condition_tracking
# ═══════════════════════════════════════════════════════════════════════

class TestConditionTracking:

    def test_individual_dimensions_tracked(self, config, kb):
        review = _make_review(config, kb)
        trade = _make_trade(
            day_of_week="Tuesday",
            liquidity_swept="pdl",
            displacement_quality="strong",
            regime="trending",
        )
        review.post_trade_update(trade)

        perf = load_json(kb.base / "statistics" / "condition_performance.json")

        assert "day_of_week:Tuesday" in perf
        assert "liquidity_type:pdl" in perf
        assert "displacement_quality:strong" in perf
        assert "regime:trending" in perf

    def test_combined_dimensions_tracked(self, config, kb):
        review = _make_review(config, kb)
        trade = _make_trade(
            day_of_week="Tuesday",
            liquidity_swept="pdl",
            displacement_quality="strong",
            regime="trending",
        )
        review.post_trade_update(trade)

        perf = load_json(kb.base / "statistics" / "condition_performance.json")

        assert "day_of_week+liquidity_type:Tuesday_pdl" in perf
        assert "displacement_quality+regime:strong_trending" in perf

    def test_condition_stats_accumulate(self, config, kb):
        review = _make_review(config, kb)

        for i in range(5):
            t = _make_trade(
                trade_id=f"tr_2026-01-{15+i}_001",
                date=f"2026-01-{15+i}",
                day_of_week="Monday",
                outcome="WIN" if i < 3 else "LOSS",
                r_multiple=2.0 if i < 3 else -1.0,
            )
            review.post_trade_update(t)

        perf = load_json(kb.base / "statistics" / "condition_performance.json")
        monday = perf["day_of_week:Monday"]
        assert monday["total"] == 5
        assert monday["wins"] == 3
        assert monday["losses"] == 2
        assert abs(monday["win_rate"] - 0.6) < 0.01


# ═══════════════════════════════════════════════════════════════════════
# test_adaptation_flag_tier2
# ═══════════════════════════════════════════════════════════════════════

class TestAdaptationFlagTier2:

    def test_flag_raised_on_deviation(self, config, kb):
        """25 trades in a condition with 20% WR (vs ~50% overall) → flag."""
        review = _make_review(config, kb)

        # First, create 25 trades to establish an overall baseline ~ 50%
        for i in range(25):
            t = _make_trade(
                trade_id=f"tr_base_{i:03d}",
                date=f"2026-01-{(i % 28) + 1:02d}",
                day_of_week="Tuesday",
                liquidity_swept="pdh",
                displacement_quality="strong",
                outcome="WIN" if i % 2 == 0 else "LOSS",
                r_multiple=2.0 if i % 2 == 0 else -1.0,
            )
            review.post_trade_update(t)

        # Now add 25 trades in a specific condition with 20% WR
        for i in range(25):
            t = _make_trade(
                trade_id=f"tr_monday_{i:03d}",
                date=f"2026-02-{(i % 28) + 1:02d}",
                day_of_week="Monday",
                liquidity_swept="asian_low",
                displacement_quality="weak",
                outcome="WIN" if i < 5 else "LOSS",  # 5/25 = 20%
                r_multiple=2.0 if i < 5 else -1.0,
            )
            review.post_trade_update(t)

        result = review.check_adaptation_flags()

        # The "day_of_week:Monday" condition (or similar) should be flagged
        flagged_conditions = [f["condition"] for f in result["flags"]]
        # At least one flag should exist where Monday or weak or asian_low
        # has significant deviation from the ~50% overall
        assert len(result["flags"]) > 0, (
            f"Expected at least one flag, got: {result}"
        )

        # Verify at least one flag is tier 2
        tiers = [f["tier"] for f in result["flags"]]
        assert 2 in tiers

    def test_flag_written_to_pending_reviews(self, config, kb):
        review = _make_review(config, kb)

        # Create 25 winning trades with one set of conditions (baseline ~50%)
        for i in range(25):
            t = _make_trade(
                trade_id=f"tr_good_{i:03d}",
                date=f"2026-01-{(i % 28) + 1:02d}",
                day_of_week="Tuesday",
                liquidity_swept="pdh",
                displacement_quality="strong",
                outcome="WIN" if i % 2 == 0 else "LOSS",
                r_multiple=2.0 if i % 2 == 0 else -1.0,
            )
            review.post_trade_update(t)

        # Create 25 ALL-LOSS trades with a different condition
        for i in range(25):
            t = _make_trade(
                trade_id=f"tr_bad_{i:03d}",
                date=f"2026-02-{(i % 28) + 1:02d}",
                day_of_week="Friday",
                liquidity_swept="equal_lows",
                displacement_quality="weak",
                outcome="LOSS",
                r_multiple=-1.0,
            )
            review.post_trade_update(t)

        review.check_adaptation_flags()

        from src.utils.file_io import load_yaml
        pending = load_yaml(kb.base / "rules" / "pending_reviews.yaml")
        assert "items" in pending
        assert len(pending["items"]) > 0


# ═══════════════════════════════════════════════════════════════════════
# test_no_flag_small_sample
# ═══════════════════════════════════════════════════════════════════════

class TestNoFlagSmallSample:

    def test_no_flag_below_minimum_sample(self, config, kb):
        """10 trades with deviation should NOT trigger a flag (below min 20)."""
        review = _make_review(config, kb)

        # 10 overall trades at 50% WR
        for i in range(10):
            t = _make_trade(
                trade_id=f"tr_base_{i:03d}",
                date=f"2026-01-{(i % 28) + 1:02d}",
                day_of_week="Tuesday",
                outcome="WIN" if i % 2 == 0 else "LOSS",
                r_multiple=2.0 if i % 2 == 0 else -1.0,
            )
            review.post_trade_update(t)

        # 10 trades with 0% WR in a specific condition
        for i in range(10):
            t = _make_trade(
                trade_id=f"tr_bad_{i:03d}",
                date=f"2026-02-{(i % 28) + 1:02d}",
                day_of_week="Friday",
                liquidity_swept="equal_highs",
                displacement_quality="weak",
                outcome="LOSS",
                r_multiple=-1.0,
            )
            review.post_trade_update(t)

        result = review.check_adaptation_flags()

        # No condition should have 20+ samples in a single bucket,
        # so no flags expected for the "bad" condition specifically
        friday_flags = [
            f for f in result["flags"]
            if "Friday" in f["condition"] or "equal_highs" in f["condition"]
            or "weak" in f["condition"]
        ]
        # These specific conditions each have only 10 samples → no flag
        assert len(friday_flags) == 0, (
            f"Expected no flags for small sample, got: {friday_flags}"
        )


# ═══════════════════════════════════════════════════════════════════════
# test_hard_guardrails
# ═══════════════════════════════════════════════════════════════════════

class TestHardGuardrails:

    def test_protected_parameters_not_modifiable(self):
        for param in PROTECTED_PARAMETERS:
            assert AdaptiveReviewSystem.validate_rule_change(param, "any") is False

    def test_non_protected_parameters_modifiable(self):
        assert AdaptiveReviewSystem.validate_rule_change("min_rr", 4.0) is True
        assert AdaptiveReviewSystem.validate_rule_change("max_spread_cents", 25) is True
        assert AdaptiveReviewSystem.validate_rule_change("min_debate_confidence", 60) is True

    def test_protected_set_is_complete(self):
        """Verify all critical safety parameters are protected."""
        expected = {
            "max_risk_pct",
            "max_daily_losses",
            "max_daily_loss_pct",
            "max_weekly_loss_pct",
            "max_monthly_loss_pct",
            "session_start_utc",
            "session_end_utc",
            "debate_required",
        }
        assert PROTECTED_PARAMETERS == expected

    def test_base_rules_restorable(self, kb):
        """Verify base_rules.yaml exists and has expected structure."""
        from src.utils.file_io import load_yaml
        base_rules = load_yaml(kb.base / "rules" / "base_rules.yaml")
        assert "rules" in base_rules
        assert base_rules["rules"]["max_risk_pct"] == 2.0
        assert base_rules["rules"]["max_daily_losses"] == 2


# ═══════════════════════════════════════════════════════════════════════
# test_weekly_insights (async, mocked API)
# ═══════════════════════════════════════════════════════════════════════

class TestWeeklyInsights:

    def test_generate_weekly_insights(self, config, kb):
        review = _make_review(config, kb)

        insights_yaml = """
generated_at: "2026-03-28T10:00:00Z"
total_trades_analyzed: 50
overall_win_rate: 0.48
overall_expectancy: 0.72
overall_profit_factor: 1.85
max_consecutive_losses: 3
condition_insights:
  - condition: "Tuesday_asian_low_strong"
    sample_size: 22
    win_rate: 0.68
    expectancy: 1.45
    flag: STRONG_EDGE
    note: "Best performing condition"
debate_calibration:
  total_debates: 30
  bull_wins: 21
  bear_wins: 9
  bull_win_rate: 0.70
  bear_win_rate: 0.30
  false_approvals_pct: 0.18
  false_rejections_pct: 0.12
regime_insight:
  current_regime: trending
  regime_started: "2026-03-01"
  model_performance_in_regime: "Strong"
active_failure_patterns: []
rule_modification_history: []
"""
        # Mock the API response
        content_block = MagicMock()
        content_block.text = insights_yaml
        resp = MagicMock()
        resp.content = [content_block]
        review.client.messages.create.return_value = resp

        result = asyncio.get_event_loop().run_until_complete(
            review.generate_weekly_insights()
        )

        assert result is not None
        assert result.get("total_trades_analyzed") == 50
        assert result.get("overall_win_rate") == 0.48

        # Verify file was written
        from src.utils.file_io import load_yaml
        saved = load_yaml(kb.base / "insights" / "current_insights.yaml")
        assert saved.get("total_trades_analyzed") == 50
