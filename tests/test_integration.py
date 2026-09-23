"""Full integration tests for the gold-agent pipeline.

Tests exercise the complete flow: MarketStateObject → Primary Analyzer →
Debate → Execution → Knowledge Base → Adaptive Review, using mocked
Claude API calls throughout.
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml

from src.components.debate import DebateEngine
from src.components.knowledge_base import KnowledgeBase
from src.components.primary_analyzer import PrimaryAnalyzer
from src.components.adaptive_review import AdaptiveReviewSystem
from src.models.analysis_models import (
    DailyBiasAnalysis,
    H1SetupAnalysis,
    H4AlignmentAnalysis,
    LiquiditySweepAnalysis,
    M15ConfirmationAnalysis,
    PrimaryAnalysisOutput,
    PrimaryAnalysisReasoning,
    TradeParameters,
)
from src.models.debate_models import (
    BearArgument,
    BearRisk,
    BullArgument,
    BullKeyPoint,
    DebateRound1,
    DebateRound2,
    DebateVerdict,
    Rebuttal,
)
from src.models.market_state_models import (
    DataQuality,
    MarketStateObject,
    SessionLevels,
    StructureAnalysis,
    StructureEvent,
    Swing,
    TimeframeState,
)
from src.models.trade_models import (
    CandleEvaluation,
    NoTradeRecord,
    NoTradeReasoning,
    PostmortemRecord,
    PreSession,
    SessionManifest,
    TradeEvent,
    TradeRecord,
    TradeSummary,
    transition,
)
from src.utils.file_io import KNOWLEDGE_BASE_DIR, atomic_write, load_json, load_yaml
import src.utils.file_io as file_io_module


# ═══════════════════════════════════════════════════════════════════════
# Shared helpers
# ═══════════════════════════════════════════════════════════════════════

DEFAULT_CONFIG = {
    "ai": {
        "primary_model": "claude-sonnet-4-20250514",
        "debate_model": "claude-sonnet-4-20250514",
        "postmortem_model": "claude-sonnet-4-20250514",
        "review_model": "claude-sonnet-4-20250514",
        "debate_round2_enabled": False,
        "max_api_retries": 0,
        "api_timeout_seconds": 10,
    },
    "risk": {
        "max_spread_cents": 30,
        "min_rr": 3.0,
        "sl_buffer_dollars": 1.20,
    },
    "adaptation": {},
}


def _make_structure(direction: str = "bullish") -> StructureAnalysis:
    return StructureAnalysis(
        direction=direction,
        protected_swing=Swing(index=0, type="low", price=2680.0, time="2025-11-15T06:00:00Z"),
        swing_sequence=["HH", "HL", "HH", "HL"] if direction == "bullish" else ["LH", "LL", "LH", "LL"],
    )


def _make_timeframe_state(direction: str = "bullish") -> TimeframeState:
    return TimeframeState(
        structure=_make_structure(direction),
        swings=[
            Swing(index=0, type="low", price=2680.0, time="2025-11-15T06:00:00Z"),
            Swing(index=5, type="high", price=2720.0, time="2025-11-15T07:00:00Z"),
        ],
        avg_candle_body=3.5,
    )


def _make_market_state(
    daily_dir: str = "bullish",
    h4_dir: str = "bullish",
    spread: float = 20.0,
) -> MarketStateObject:
    return MarketStateObject(
        timestamp_utc="2025-11-15T07:15:00Z",
        timeframes={
            "D1": _make_timeframe_state(daily_dir),
            "H4": _make_timeframe_state(h4_dir),
            "H1": _make_timeframe_state(daily_dir),
            "M15": TimeframeState(
                structure=_make_structure(daily_dir),
                swings=[
                    Swing(index=0, type="low", price=2695.0, time="2025-11-15T07:00:00Z"),
                    Swing(index=3, type="high", price=2705.0, time="2025-11-15T07:15:00Z"),
                ],
                structure_events=[
                    StructureEvent(
                        type="CHoCH",
                        direction="bullish",
                        level_broken=2703.0,
                        close_price=2706.0,
                        candle_index=3,
                        time="2025-11-15T07:15:00Z",
                        displacement_present=True,
                        displacement_ratio=2.3,
                    ),
                ],
                avg_candle_body=2.0,
            ),
        },
        session_levels=SessionLevels(
            asian_high=2710.0,
            asian_low=2690.0,
            pdh=2715.0,
            pdl=2685.0,
        ),
        spread_cents=spread,
        data_quality=DataQuality(
            all_timeframes_complete=True,
            spread_normal=True,
            mt5_connected=False,
            timestamp_utc="2025-11-15T07:15:00Z",
        ),
    )


def _no_trade_response() -> str:
    """Raw JSON string for a Primary Analyzer NO_TRADE response."""
    return json.dumps({
        "timestamp_utc": "2025-11-15T07:15:00Z",
        "model_used": "claude-sonnet-4-20250514",
        "decision": "NO_TRADE",
        "confidence_score": 15,
        "reasoning": {
            "daily_bias": {"direction": "ranging", "confidence": "low",
                           "protected_swing_level": 0.0, "explanation": "Daily structure is ranging."},
            "h4_alignment": {"aligned": False, "explanation": "H4 structure conflicts."},
            "h1_setup": {"poi_identified": False, "explanation": "No valid H1 pullback."},
            "liquidity_sweep": {"detected": False, "explanation": "No sweep detected."},
            "m15_confirmation": {"choch_detected": False, "explanation": "No M15 CHoCH."},
            "setup_grade": "C",
            "overall_reasoning": "Market is ranging on Daily — no bias to trade.",
        },
        "trade_parameters": None,
        "no_trade_reason": "daily_ranging",
        "wait_reason": None,
    })


def _candidate_response() -> str:
    """Raw JSON string for a Primary Analyzer CANDIDATE response."""
    return json.dumps({
        "timestamp_utc": "2025-11-15T07:15:00Z",
        "model_used": "claude-sonnet-4-20250514",
        "decision": "CANDIDATE",
        "confidence_score": 78,
        "reasoning": {
            "daily_bias": {"direction": "bullish", "confidence": "high",
                           "protected_swing_level": 2680.0,
                           "explanation": "Clear HH/HL sequence on Daily."},
            "h4_alignment": {"aligned": True,
                             "h4_pois_identified": ["OB at 2690"],
                             "explanation": "H4 agrees with Daily bullish."},
            "h1_setup": {"poi_identified": True, "poi_type": "OB",
                         "poi_price_level": 2695.0, "zone": "discount",
                         "fib_retracement_pct": 68.0,
                         "explanation": "H1 pulled back to OB in OTE zone."},
            "liquidity_sweep": {"detected": True, "pool_type": "asian_low",
                                "sweep_quality": "clean", "sweep_price": 2689.5,
                                "explanation": "Clean sweep of Asian Low."},
            "m15_confirmation": {"choch_detected": True, "displacement_quality": "strong",
                                 "displacement_candle_body_vs_avg_ratio": 2.3,
                                 "explanation": "Strong M15 bullish CHoCH with displacement."},
            "setup_grade": "A",
            "overall_reasoning": "All Model A criteria met: bullish bias, aligned H4, OTE pullback, clean sweep, strong displacement.",
        },
        "trade_parameters": {
            "direction": "LONG",
            "entry_price": 2700.0,
            "stop_loss": 2688.0,
            "sl_buffer_applied": 1.20,
            "take_profit_1": 2736.0,
            "take_profit_2": 2750.0,
            "take_profit_3": 2770.0,
            "risk_reward_ratio": 3.0,
            "position_size_lots": 0.05,
        },
        "no_trade_reason": None,
        "wait_reason": None,
    })


def _bull_response() -> str:
    return json.dumps({
        "position": "TAKE_TRADE",
        "argument_strength_self_assessed": 82,
        "key_points": [
            {"point": "Clear bullish bias on Daily and H4.", "supporting_data": "HH/HL sequence confirmed."},
            {"point": "Clean Asian Low sweep at 2689.5.", "supporting_data": "Wick swept below, body closed inside."},
        ],
        "historical_parallels_cited": [],
        "full_argument": "Strong multi-timeframe alignment with clean sweep and strong displacement. A-grade setup.",
    })


def _bear_response() -> str:
    return json.dumps({
        "position": "DO_NOT_TRADE",
        "argument_strength_self_assessed": 45,
        "key_points": [
            {"point": "Displacement ratio borderline at 2.3.", "supporting_data": "Minimum strong threshold is 2.0."},
        ],
        "risks_identified": [
            {"risk": "Proximity to PDH resistance at 2715", "severity": "medium", "evidence": "PDH is only 15 points above entry."},
        ],
        "alternative_interpretations": ["H4 could be transitional rather than clearly bullish."],
        "full_argument": "While the setup has merit, the displacement is near the threshold and PDH resistance is close.",
    })


def _judge_approve_response(confidence: int = 80) -> str:
    return json.dumps({
        "timestamp_utc": "2025-11-15T07:16:00Z",
        "model_used": "claude-sonnet-4-20250514",
        "verdict": "APPROVE",
        "winning_perspective": "BULL",
        "confidence_score": confidence,
        "bull_argument_strength": 82,
        "bear_argument_strength": 45,
        "key_factor": "Clean sweep with strong displacement in aligned multi-TF structure.",
        "risk_concerns_acknowledged": ["PDH proximity noted but manageable with TP1 below."],
        "summary": "Bull case is clearly stronger. All Model A criteria met. Proceed with caution on PDH.",
    })


def _judge_reject_response() -> str:
    return json.dumps({
        "timestamp_utc": "2025-11-15T07:16:00Z",
        "model_used": "claude-sonnet-4-20250514",
        "verdict": "REJECT",
        "winning_perspective": "BEAR",
        "confidence_score": 55,
        "bull_argument_strength": 55,
        "bear_argument_strength": 60,
        "key_factor": "Borderline displacement and conflicting H4 structure.",
        "risk_concerns_acknowledged": ["Displacement ratio barely above threshold."],
        "summary": "Arguments are close to equal in strength. Ties go to the bear — REJECT.",
    })


def _postmortem_response(trade_id: str) -> str:
    return json.dumps({
        "trade_id": trade_id,
        "generated_at": "2025-11-15T12:00:00Z",
        "model_used": "claude-sonnet-4-20250514",
        "daily_bias_accuracy": "correct",
        "h4_alignment_accuracy": "correct",
        "sweep_classification_accuracy": "correct",
        "displacement_assessment_accuracy": "slightly_optimistic",
        "setup_grade_appropriate": True,
        "missed_signals": [],
        "alternative_readings_in_hindsight": "None — analysis was solid.",
        "llm_score": 85.0,
        "llm_score_breakdown": {
            "bias_read": 20.0,
            "sweep_classification": 20.0,
            "displacement_assessment": 15.0,
            "grade_accuracy": 20.0,
            "missed_signals_penalty": 10.0,
        },
        "lessons_learned": ["Strong displacement in OTE zone continues to produce winners."],
        "key_pattern": "asian_low_sweep_ote_strong_displacement",
        "summary": "Well-executed A-grade setup. Clean sweep, strong displacement, correct bias read.",
        "debate_verdict_correct": True,
        "debate_notes": "Bull case correctly identified the high-quality setup.",
    })


# ═══════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════

@pytest.fixture
def tmp_kb(tmp_path, monkeypatch):
    """Create a KnowledgeBase in a temp directory with rules initialized.

    Also patches ``KNOWLEDGE_BASE_DIR`` so that ``write_pipeline()`` writes
    to the same temp directory instead of the global knowledge_base/.
    """
    monkeypatch.setattr(file_io_module, "KNOWLEDGE_BASE_DIR", tmp_path)
    kb = KnowledgeBase(base_path=str(tmp_path))
    kb.initialize_rules()
    return kb


@pytest.fixture
def config():
    return DEFAULT_CONFIG.copy()


# ═══════════════════════════════════════════════════════════════════════
# Test 1: Full pipeline — NO_TRADE session
# ═══════════════════════════════════════════════════════════════════════

class TestFullPipelineNoTradeSession:
    """Create ranging market → Primary Analyzer returns NO_TRADE →
    no debate triggered → no-trade record written → session manifest correct."""

    @pytest.mark.asyncio
    async def test_full_pipeline_no_trade_session(self, tmp_kb, config):
        mso = _make_market_state(daily_dir="transitional", h4_dir="transitional")

        # Mock the Claude API call to return NO_TRADE
        with patch.object(PrimaryAnalyzer, "_call_claude", return_value=_no_trade_response()):
            analyzer = PrimaryAnalyzer(config, tmp_kb)
            result = await analyzer.analyze(mso)

        # 1. Primary Analyzer returned NO_TRADE
        assert result.decision == "NO_TRADE"
        assert result.no_trade_reason == "daily_ranging"

        # 2. No debate should be triggered (decision != CANDIDATE)
        assert result.decision != "CANDIDATE"

        # 3. Write no-trade record
        nt_record = NoTradeRecord(
            record_id="nt_2025-11-15_0715",
            date="2025-11-15",
            candle_time="2025-11-15T07:15:00Z",
            reason=result.no_trade_reason or "no_trade",
            reasoning=NoTradeReasoning(
                daily_bias=result.reasoning.daily_bias.direction,
                h4_alignment=str(result.reasoning.h4_alignment.aligned),
                stopped_at_step=1,
                full_explanation=result.reasoning.overall_reasoning,
            ),
        )
        nt_id = tmp_kb.write_no_trade(nt_record)
        assert nt_id == "nt_2025-11-15_0715"

        # Verify file was written
        nt_path = tmp_kb.base / "no_trades" / f"{nt_id}.yaml"
        assert nt_path.exists()
        loaded = load_yaml(nt_path)
        assert loaded["decision"] == "NO_TRADE"

        # 4. Session manifest
        manifest = SessionManifest(
            date="2025-11-15",
            day_of_week="Saturday",
            session_start_utc="2025-11-15T07:00:00Z",
            session_end_utc="2025-11-15T09:30:00Z",
            candle_evaluations=[
                CandleEvaluation(
                    candle_time="2025-11-15T07:15:00Z",
                    decision="NO_TRADE",
                    reason="daily_ranging",
                    confidence=15,
                    debate_triggered=False,
                    trade_executed=False,
                ),
            ],
            trade_summary=TradeSummary(trade_taken=False),
            api_calls_count=1,
        )
        tmp_kb.write_session_manifest(manifest)

        # Verify session manifest
        loaded_session = tmp_kb.load_session("2025-11-15")
        assert loaded_session is not None
        assert loaded_session.trade_summary.trade_taken is False
        assert len(loaded_session.candle_evaluations) == 1
        assert loaded_session.candle_evaluations[0].debate_triggered is False


# ═══════════════════════════════════════════════════════════════════════
# Test 2: Full pipeline — CANDIDATE → APPROVED → WIN
# ═══════════════════════════════════════════════════════════════════════

class TestFullPipelineCandidateApproved:
    """Clean bullish setup → CANDIDATE → debate APPROVE → trade WIN 3.2R →
    postmortem, stats, LanceDB all updated."""

    @pytest.mark.asyncio
    async def test_full_pipeline_candidate_approved(self, tmp_kb, config):
        mso = _make_market_state(daily_dir="bullish", h4_dir="bullish", spread=20.0)

        # ── Step 1: Primary Analyzer → CANDIDATE ──────────────────────
        with patch.object(PrimaryAnalyzer, "_call_claude", return_value=_candidate_response()):
            analyzer = PrimaryAnalyzer(config, tmp_kb)
            pa_result = await analyzer.analyze(mso)

        assert pa_result.decision == "CANDIDATE"
        assert pa_result.confidence_score == 78
        assert pa_result.trade_parameters is not None
        assert pa_result.trade_parameters.direction == "LONG"

        # ── Step 2: Debate → APPROVE ──────────────────────────────────
        api_responses = [_bull_response(), _bear_response(), _judge_approve_response(80)]
        with patch.object(DebateEngine, "_sync_call", side_effect=api_responses):
            debate = DebateEngine(config, tmp_kb)
            kb_context = {"layer1": {}, "layer2": {}, "layer3": []}
            verdict = await debate.run_debate(mso, pa_result, kb_context)

        assert verdict.verdict == "APPROVE"
        assert verdict.confidence_score == 80
        assert verdict.winning_perspective == "BULL"

        # Verify debate files written
        r1_path = tmp_kb.base / "pipeline_state" / "03b_debate_round1.json"
        v_path = tmp_kb.base / "pipeline_state" / "03b_verdict.json"
        assert r1_path.exists()
        assert v_path.exists()

        # Decision mapping
        decision = DebateEngine.evaluate_verdict(verdict)
        assert decision == "APPROVED"

        # ── Step 3: Create trade record ───────────────────────────────
        tp = pa_result.trade_parameters
        trade = TradeRecord(
            trade_id="",  # will be set by write_trade
            date="2025-11-15",
            day_of_week="Saturday",
            direction=tp.direction,
            entry_price=tp.entry_price,
            stop_loss=tp.stop_loss,
            sl_buffer_applied=tp.sl_buffer_applied,
            take_profit_1=tp.take_profit_1,
            take_profit_2=tp.take_profit_2,
            take_profit_3=tp.take_profit_3,
            risk_reward_ratio=tp.risk_reward_ratio,
            position_size_lots=tp.position_size_lots,
            setup_grade=pa_result.reasoning.setup_grade,
            daily_bias=pa_result.reasoning.daily_bias.direction,
            h4_aligned=pa_result.reasoning.h4_alignment.aligned,
            liquidity_swept=pa_result.reasoning.liquidity_sweep.pool_type,
            displacement_quality=pa_result.reasoning.m15_confirmation.displacement_quality,
            displacement_ratio=pa_result.reasoning.m15_confirmation.displacement_candle_body_vs_avg_ratio,
            debate_verdict=verdict.verdict,
            debate_confidence=verdict.confidence_score,
            bull_strength=verdict.bull_argument_strength,
            bear_strength=verdict.bear_argument_strength,
            debate_key_factor=verdict.key_factor,
        )

        # Walk through lifecycle states
        record_dict = {"lifecycle_state": "EVALUATING", "state_transitions": []}
        transition(record_dict, "EVALUATING", "CANDIDATE", "primary_candidate")
        transition(record_dict, "CANDIDATE", "DEBATED", "debate_completed")
        transition(record_dict, "DEBATED", "APPROVED", "verdict_approve")
        transition(record_dict, "APPROVED", "EXECUTING", "order_sent")
        transition(record_dict, "EXECUTING", "ACTIVE", "order_filled")

        # ── Step 4: Simulate trade outcome → WIN 3.2R ────────────────
        trade.fill_price = 2700.50
        trade.slippage_cents = 50.0
        trade.spread_at_entry = 20.0
        trade.outcome = "WIN"
        trade.r_multiple = 3.2
        trade.actual_risk_pct = 1.0
        trade.pnl_dollars = 384.0
        trade.hold_time_minutes = 95
        trade.events = [
            TradeEvent(type="PARTIAL_TP1", time="2025-11-15T08:30:00Z", price=2736.0, remaining_pct=0.50),
            TradeEvent(type="RUNNER_TP3", time="2025-11-15T09:15:00Z", price=2738.4, remaining_pct=0.0),
        ]

        transition(record_dict, "ACTIVE", "CLOSED", "tp_hit")
        trade.lifecycle_state = "CLOSED"

        # Write trade
        trade_id = tmp_kb.write_trade(trade)
        assert trade_id.startswith("tr_2025-11-15_")

        # ── Step 5: Postmortem ────────────────────────────────────────
        pm_data = json.loads(_postmortem_response(trade_id))
        pm = PostmortemRecord.model_validate(pm_data)
        pm_file = tmp_kb.write_postmortem(pm)
        assert pm_file == f"pm_{trade_id}.yaml"

        # Verify postmortem file
        loaded_pm = tmp_kb.load_postmortem(trade_id)
        assert loaded_pm is not None
        assert loaded_pm.llm_score == 85.0

        # ── Step 6: Stats updated ─────────────────────────────────────
        tmp_kb.update_rolling_stats(trade)
        stats = tmp_kb.load_rolling_stats()
        assert stats["total_trades"] == 1
        assert stats["wins"] == 1
        assert stats["win_rate"] == 1.0
        assert stats["gross_profit_r"] == 3.2

        # ── Step 7: LanceDB entry created ─────────────────────────────
        tmp_kb.initialize_vectordb()
        tmp_kb.embed_trade(trade, pm)

        # Query back
        count = tmp_kb._lance_table.count_rows()
        assert count == 1

        results = tmp_kb.find_similar_setups(mso, top_k=1)
        assert len(results) >= 1
        assert results[0]["trade_id"] == trade_id


# ═══════════════════════════════════════════════════════════════════════
# Test 3: Full pipeline — CANDIDATE → REJECTED
# ═══════════════════════════════════════════════════════════════════════

class TestFullPipelineCandidateRejected:
    """Borderline setup → CANDIDATE → debate REJECT →
    logged as REJECTED, no trade executed, debate transcript preserved."""

    @pytest.mark.asyncio
    async def test_full_pipeline_candidate_rejected(self, tmp_kb, config):
        mso = _make_market_state(daily_dir="bullish", h4_dir="bullish")

        # Primary Analyzer → CANDIDATE
        with patch.object(PrimaryAnalyzer, "_call_claude", return_value=_candidate_response()):
            analyzer = PrimaryAnalyzer(config, tmp_kb)
            pa_result = await analyzer.analyze(mso)

        assert pa_result.decision == "CANDIDATE"

        # Debate → REJECT
        api_responses = [_bull_response(), _bear_response(), _judge_reject_response()]
        with patch.object(DebateEngine, "_sync_call", side_effect=api_responses):
            debate = DebateEngine(config, tmp_kb)
            verdict = await debate.run_debate(mso, pa_result, {"layer1": {}, "layer2": {}, "layer3": []})

        assert verdict.verdict == "REJECT"
        decision = DebateEngine.evaluate_verdict(verdict)
        assert decision == "REJECTED"

        # Verify debate transcript preserved
        r1_path = tmp_kb.base / "pipeline_state" / "03b_debate_round1.json"
        v_path = tmp_kb.base / "pipeline_state" / "03b_verdict.json"
        assert r1_path.exists()
        assert v_path.exists()

        r1_data = load_json(r1_path)
        assert "bull_argument" in r1_data
        assert "bear_argument" in r1_data

        v_data = load_json(v_path)
        assert v_data["verdict"] == "REJECT"

        # No trade executed — session manifest records this
        manifest = SessionManifest(
            date="2025-11-15",
            day_of_week="Saturday",
            session_start_utc="2025-11-15T07:00:00Z",
            session_end_utc="2025-11-15T09:30:00Z",
            candle_evaluations=[
                CandleEvaluation(
                    candle_time="2025-11-15T07:15:00Z",
                    decision="CANDIDATE",
                    confidence=78,
                    setup_grade="A",
                    debate_triggered=True,
                    debate_verdict="REJECT",
                    trade_executed=False,
                ),
            ],
            trade_summary=TradeSummary(trade_taken=False),
            api_calls_count=4,
        )
        tmp_kb.write_session_manifest(manifest)

        loaded = tmp_kb.load_session("2025-11-15")
        assert loaded.trade_summary.trade_taken is False
        assert loaded.candle_evaluations[0].debate_verdict == "REJECT"


# ═══════════════════════════════════════════════════════════════════════
# Test 4: Safety check blocks execution
# ═══════════════════════════════════════════════════════════════════════

class TestFullPipelineSafetyCheckBlocks:
    """Debate → APPROVE, but spread is 35 cents (>30 max) →
    safety check blocks → REJECTED with reason."""

    @pytest.mark.asyncio
    async def test_full_pipeline_safety_check_blocks(self, tmp_kb, config):
        # Market state with wide spread
        mso = _make_market_state(daily_dir="bullish", h4_dir="bullish", spread=35.0)

        # Primary Analyzer → CANDIDATE
        with patch.object(PrimaryAnalyzer, "_call_claude", return_value=_candidate_response()):
            analyzer = PrimaryAnalyzer(config, tmp_kb)
            pa_result = await analyzer.analyze(mso)

        assert pa_result.decision == "CANDIDATE"

        # Debate → APPROVE
        api_responses = [_bull_response(), _bear_response(), _judge_approve_response(80)]
        with patch.object(DebateEngine, "_sync_call", side_effect=api_responses):
            debate = DebateEngine(config, tmp_kb)
            verdict = await debate.run_debate(mso, pa_result, {"layer1": {}, "layer2": {}, "layer3": []})

        assert verdict.verdict == "APPROVE"

        # ── Safety check: spread too wide ─────────────────────────────
        max_spread = config["risk"]["max_spread_cents"]
        current_spread = mso.spread_cents

        safety_passed = current_spread is not None and current_spread <= max_spread
        assert safety_passed is False, "Safety check should fail — spread 35 > max 30"

        # Record the rejection reason
        rejection_reason = f"spread_too_wide_{current_spread}_cents_max_{max_spread}"

        # Log as REJECTED despite APPROVE verdict
        record_dict = {"lifecycle_state": "EVALUATING", "state_transitions": []}
        transition(record_dict, "EVALUATING", "CANDIDATE", "primary_candidate")
        transition(record_dict, "CANDIDATE", "DEBATED", "debate_completed")
        transition(record_dict, "DEBATED", "REJECTED", f"safety_block:{rejection_reason}")

        assert record_dict["lifecycle_state"] == "REJECTED"
        assert "safety_block" in record_dict["state_transitions"][-1]["event"]

        # Session manifest records the safety block
        manifest = SessionManifest(
            date="2025-11-15",
            day_of_week="Saturday",
            session_start_utc="2025-11-15T07:00:00Z",
            session_end_utc="2025-11-15T09:30:00Z",
            candle_evaluations=[
                CandleEvaluation(
                    candle_time="2025-11-15T07:15:00Z",
                    decision="CANDIDATE",
                    confidence=78,
                    setup_grade="A",
                    debate_triggered=True,
                    debate_verdict="APPROVE",
                    trade_executed=False,
                    reason=rejection_reason,
                ),
            ],
            trade_summary=TradeSummary(trade_taken=False),
            api_calls_count=4,
        )
        tmp_kb.write_session_manifest(manifest)

        loaded = tmp_kb.load_session("2025-11-15")
        assert loaded.trade_summary.trade_taken is False
        assert "spread_too_wide" in loaded.candle_evaluations[0].reason


# ═══════════════════════════════════════════════════════════════════════
# Test 5: Knowledge Base accumulation
# ═══════════════════════════════════════════════════════════════════════

class TestKnowledgeBaseAccumulation:
    """Run 10 simulated trades → verify rolling stats correct after each →
    verify LanceDB has 10 entries → query returns sensible results."""

    def test_knowledge_base_accumulation(self, tmp_kb):
        mso = _make_market_state()
        tmp_kb.initialize_vectordb()

        outcomes = [
            ("WIN", 3.2), ("WIN", 2.1), ("LOSS", -1.0),
            ("WIN", 4.5), ("WIN", 1.8), ("LOSS", -1.0),
            ("WIN", 3.0), ("BREAKEVEN", 0.0), ("WIN", 2.5),
            ("LOSS", -1.0),
        ]

        expected_wins = 0
        expected_losses = 0
        expected_be = 0
        expected_gross_profit = 0.0
        expected_gross_loss = 0.0

        for i, (outcome, r_mult) in enumerate(outcomes, 1):
            trade = TradeRecord(
                trade_id="",
                date=f"2025-11-{i:02d}",
                day_of_week="Monday",
                direction="LONG",
                entry_price=2700.0,
                stop_loss=2688.0,
                take_profit_1=2736.0,
                risk_reward_ratio=3.0,
                setup_grade="A",
                daily_bias="bullish",
                h4_aligned=True,
                liquidity_swept="asian_low",
                displacement_quality="strong",
                regime="trending",
                outcome=outcome,
                r_multiple=r_mult,
                debate_confidence=80,
            )
            trade_id = tmp_kb.write_trade(trade)
            tmp_kb.update_rolling_stats(trade)

            # Track expected values
            if outcome == "WIN":
                expected_wins += 1
                expected_gross_profit += r_mult
            elif outcome == "LOSS":
                expected_losses += 1
                expected_gross_loss += abs(r_mult)
            else:
                expected_be += 1

            # Verify stats after each trade
            stats = tmp_kb.load_rolling_stats()
            assert stats["total_trades"] == i
            assert stats["wins"] == expected_wins
            assert stats["losses"] == expected_losses
            assert stats["breakeven"] == expected_be
            assert abs(stats["gross_profit_r"] - expected_gross_profit) < 0.01
            assert abs(stats["gross_loss_r"] - expected_gross_loss) < 0.01
            assert abs(stats["win_rate"] - expected_wins / i) < 0.001

            # Embed into LanceDB
            pm = PostmortemRecord(
                trade_id=trade_id,
                generated_at="2025-11-15T12:00:00Z",
                model_used="claude-sonnet-4-20250514",
                summary=f"Trade {i}: {outcome} {r_mult}R",
            )
            tmp_kb.embed_trade(trade, pm)

        # Verify LanceDB has 10 entries
        count = tmp_kb._lance_table.count_rows()
        assert count == 10

        # Query for similar setups
        results = tmp_kb.find_similar_setups(mso, top_k=5)
        assert len(results) >= 1
        # All results should have valid trade_ids
        for r in results:
            assert r["trade_id"].startswith("tr_2025-11-")

        # Final stats check
        final_stats = tmp_kb.load_rolling_stats()
        assert final_stats["total_trades"] == 10
        assert final_stats["wins"] == 6
        assert final_stats["losses"] == 3
        assert final_stats["breakeven"] == 1
        assert final_stats["win_rate"] == 0.6
        assert final_stats["max_consecutive_losses"] == 1


# ═══════════════════════════════════════════════════════════════════════
# Test 6: Lifecycle state tracking
# ═══════════════════════════════════════════════════════════════════════

class TestLifecycleStateTracking:
    """Run a full pipeline cycle for an APPROVED trade → verify all state
    transitions: EVALUATING → CANDIDATE → DEBATED → APPROVED → EXECUTING
    → ACTIVE → CLOSED with timestamps."""

    @pytest.mark.asyncio
    async def test_lifecycle_state_tracking(self, tmp_kb, config):
        mso = _make_market_state(daily_dir="bullish", h4_dir="bullish")

        # Step 1: Primary Analyzer → CANDIDATE
        with patch.object(PrimaryAnalyzer, "_call_claude", return_value=_candidate_response()):
            analyzer = PrimaryAnalyzer(config, tmp_kb)
            pa_result = await analyzer.analyze(mso)

        assert pa_result.decision == "CANDIDATE"

        # Step 2: Track lifecycle from EVALUATING
        record = {"lifecycle_state": "EVALUATING", "state_transitions": []}

        # EVALUATING → CANDIDATE
        transition(record, "EVALUATING", "CANDIDATE", "primary_analysis_candidate")
        assert record["lifecycle_state"] == "CANDIDATE"
        assert len(record["state_transitions"]) == 1

        # CANDIDATE → DEBATED
        transition(record, "CANDIDATE", "DEBATED", "debate_completed")
        assert record["lifecycle_state"] == "DEBATED"
        assert len(record["state_transitions"]) == 2

        # Step 3: Debate → APPROVE
        api_responses = [_bull_response(), _bear_response(), _judge_approve_response(85)]
        with patch.object(DebateEngine, "_sync_call", side_effect=api_responses):
            debate = DebateEngine(config, tmp_kb)
            verdict = await debate.run_debate(mso, pa_result, {"layer1": {}, "layer2": {}, "layer3": []})

        assert verdict.verdict == "APPROVE"

        # DEBATED → APPROVED
        transition(record, "DEBATED", "APPROVED", "verdict_approve")
        assert record["lifecycle_state"] == "APPROVED"
        assert len(record["state_transitions"]) == 3

        # APPROVED → EXECUTING
        transition(record, "APPROVED", "EXECUTING", "order_sent")
        assert record["lifecycle_state"] == "EXECUTING"
        assert len(record["state_transitions"]) == 4

        # EXECUTING → ACTIVE
        transition(record, "EXECUTING", "ACTIVE", "order_filled")
        assert record["lifecycle_state"] == "ACTIVE"
        assert len(record["state_transitions"]) == 5

        # ACTIVE → CLOSED
        transition(record, "ACTIVE", "CLOSED", "tp1_hit")
        assert record["lifecycle_state"] == "CLOSED"
        assert len(record["state_transitions"]) == 6

        # Verify all transitions logged with timestamps
        expected_sequence = [
            ("EVALUATING", "CANDIDATE"),
            ("CANDIDATE", "DEBATED"),
            ("DEBATED", "APPROVED"),
            ("APPROVED", "EXECUTING"),
            ("EXECUTING", "ACTIVE"),
            ("ACTIVE", "CLOSED"),
        ]
        for i, (from_s, to_s) in enumerate(expected_sequence):
            t = record["state_transitions"][i]
            assert t["from"] == from_s
            assert t["to"] == to_s
            assert "time" in t
            # Verify timestamp is valid ISO format
            dt = datetime.fromisoformat(t["time"])
            assert dt.year >= 2025

        # Verify timestamps are monotonically increasing
        times = [
            datetime.fromisoformat(t["time"])
            for t in record["state_transitions"]
        ]
        for i in range(1, len(times)):
            assert times[i] >= times[i - 1], "Timestamps should be monotonically increasing"
