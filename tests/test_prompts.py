"""Tests for AI prompt construction (no API calls — just prompt building)."""

from __future__ import annotations

import pytest

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
    DebateRound2,
    Rebuttal,
)
from src.models.market_state_models import (
    DataQuality,
    LiquidityPool,
    LiquiditySweep,
    MarketStateObject,
    SessionLevels,
    StructureAnalysis,
    StructureEvent,
    TimeframeState,
)
from src.models.trade_models import TradeRecord

from src.prompts import (
    primary_analyzer_prompt,
    bull_agent_prompt,
    bear_agent_prompt,
    judge_prompt,
    postmortem_prompt,
)


# ── Shared fixtures ───────────────────────────────────────────────────

@pytest.fixture
def sample_mso():
    bullish = StructureAnalysis(direction="bullish", hh_count=3, hl_count=3)
    m15 = TimeframeState(
        structure=bullish,
        structure_events=[
            StructureEvent(
                type="BOS", direction="bullish",
                level_broken=3050.0, close_price=3055.0,
                candle_index=10, time="2026-03-28T07:30:00Z",
                displacement_present=True, displacement_ratio=2.4,
            ),
        ],
    )
    pool = LiquidityPool(type="asian_low", price=3038.50, side="low")
    return MarketStateObject(
        timestamp_utc="2026-03-28T07:30:00Z",
        timeframes={
            "D1": TimeframeState(structure=bullish),
            "H4": TimeframeState(structure=bullish),
            "H1": TimeframeState(structure=bullish),
            "M15": m15,
        },
        session_levels=SessionLevels(
            asian_high=3045.0, asian_low=3038.50, pdh=3052.0, pdl=3030.0,
        ),
        liquidity_pools=[pool],
        detected_sweeps=[
            LiquiditySweep(
                pool=pool, sweep_type="sweep",
                wick_extreme=3037.0, body_close=3039.0,
                candle_index=8, time="2026-03-28T07:15:00Z",
            ),
        ],
        data_quality=DataQuality(
            all_timeframes_complete=True, spread_normal=True,
            mt5_connected=True, timestamp_utc="2026-03-28T07:30:00Z",
        ),
    )


@pytest.fixture
def sample_primary_analysis():
    return PrimaryAnalysisOutput(
        timestamp_utc="2026-03-28T07:30:00Z",
        model_used="claude-sonnet-4-20250514",
        decision="CANDIDATE",
        confidence_score=78,
        reasoning=PrimaryAnalysisReasoning(
            daily_bias=DailyBiasAnalysis(
                direction="bullish", confidence="high",
                protected_swing_level=3030.0,
                explanation="Daily HH/HL intact.",
            ),
            h4_alignment=H4AlignmentAnalysis(
                aligned=True, h4_pois_identified=["OB at 3042"],
                explanation="H4 aligned with Daily.",
            ),
            h1_setup=H1SetupAnalysis(
                poi_identified=True, poi_type="OB",
                poi_price_level=3042.0, zone="discount",
                fib_retracement_pct=68.0,
                explanation="H1 pulled back to OB in OTE zone.",
            ),
            liquidity_sweep=LiquiditySweepAnalysis(
                detected=True, pool_type="asian_low",
                sweep_quality="clean", sweep_price=3037.0,
                explanation="Clean Asian low sweep.",
            ),
            m15_confirmation=M15ConfirmationAnalysis(
                choch_detected=True, displacement_quality="strong",
                displacement_candle_body_vs_avg_ratio=2.4,
                explanation="M15 CHoCH with 2.4x displacement.",
            ),
            setup_grade="A+",
            overall_reasoning="Full Model A alignment.",
        ),
        trade_parameters=TradeParameters(
            direction="LONG", entry_price=3039.85,
            stop_loss=3033.50, take_profit_1=3048.10,
            risk_reward_ratio=3.48,
        ),
    )


@pytest.fixture
def sample_bull():
    return BullArgument(
        argument_strength_self_assessed=82,
        key_points=[
            BullKeyPoint(point="Clean Asian low sweep", supporting_data="Wick to 3037.0"),
            BullKeyPoint(point="Strong displacement 2.4x", supporting_data="Avg body 2.3"),
        ],
        historical_parallels_cited=["tr_2026-02-10_001"],
        full_argument="Strong bullish setup with clean sweep and displacement.",
    )


@pytest.fixture
def sample_bear():
    return BearArgument(
        argument_strength_self_assessed=55,
        key_points=[
            BullKeyPoint(point="Friday afternoon risk", supporting_data="Liquidity thins after noon"),
        ],
        risks_identified=[
            BearRisk(risk="Friday low liquidity", severity="medium", evidence="Historical pattern"),
        ],
        alternative_interpretations=["Sweep could be a run if NY session pushes lower"],
        full_argument="Friday risk and potential run pattern make this marginal.",
    )


@pytest.fixture
def sample_kb_context():
    return {
        "layer1": {
            "last_10_trades": [
                {"trade_id": "tr_2026-03-27_001", "outcome": "WIN", "r_multiple": 3.2},
                {"trade_id": "tr_2026-03-26_001", "outcome": "LOSS", "r_multiple": -1.0},
            ],
            "rolling_stats": {"win_rate": 0.55, "expectancy": 0.9, "current_drawdown_pct": 0.5},
            "active_failure_patterns": [],
            "current_regime": "trending_bullish",
            "pending_reviews": [],
        },
        "layer2": {"overall_win_rate": 0.48, "overall_expectancy": 0.86},
        "layer3": [
            {
                "trade_id": "tr_2026-02-10_001",
                "similarity_score": 0.92,
                "outcome": "WIN",
                "r_multiple": 3.2,
                "setup_grade": "A+",
                "text_summary": "Bullish Daily aligned H4 | Asian low sweep clean",
                "postmortem_summary": "Clean setup.",
            }
        ],
    }


@pytest.fixture
def sample_trade():
    return TradeRecord(
        trade_id="tr_2026-03-28_001", date="2026-03-28",
        day_of_week="Friday", direction="LONG",
        entry_price=3039.85, stop_loss=3033.50, take_profit_1=3048.10,
        outcome="WIN", r_multiple=3.48,
    )


# ── Primary Analyzer ──────────────────────────────────────────────────

class TestPrimaryAnalyzerPrompt:

    def test_system_prompt_contains_key_phrases(self):
        sp = primary_analyzer_prompt.SYSTEM_PROMPT
        # T7 C-gate evaluation prompt
        assert "CANDIDATE" in sp
        assert "NO_TRADE" in sp
        # C-gate structural checks
        assert "C1" in sp
        assert "C2" in sp
        assert "C3" in sp
        assert "H1" in sp
        assert "M15" in sp
        assert "CHoCH" in sp
        assert "BOS" in sp
        # Schema fields present
        assert "ob_retest" in sp
        assert "kill_zone" in sp
        assert "setup_grade" in sp
        # Removed content from P2A v1
        assert "QUALIFYING CRITERIA" not in sp
        assert "DECISION THRESHOLDS" not in sp
        assert "CONFIDENCE SCORE" not in sp
        assert "Breaker Block" not in sp
        assert "FRAMEWORK 1" not in sp

    def test_build_user_message(self, sample_mso, sample_kb_context):
        msg = primary_analyzer_prompt.build_user_message(
            sample_mso, sample_kb_context, "2026-03-28T07:30:00Z",
        )
        assert isinstance(msg, str)
        assert len(msg) > 50
        assert "Dynamic Market Data" in msg
        assert "Candle" in msg
        assert "Evaluate this" in msg
        # Framework-neutral wording (HALLUC-1 fix 2026-04-28): the user
        # message must not name a specific framework as the default.
        assert "OB Retest setup" not in msg
        assert "Breaker Block" not in msg
        # The user message must reference PARALLEL EVALUATION so the AI
        # understands the multi-framework dispatch contract.
        assert "PARALLEL" in msg

        # Static context should have D1/H4 and session levels
        static = primary_analyzer_prompt.build_static_context(sample_mso)
        assert "Session Levels" in static
        assert "D1" in static

    def test_build_user_message_empty_context(self, sample_mso):
        msg = primary_analyzer_prompt.build_user_message(
            sample_mso, {}, "2026-03-28T07:30:00Z",
        )
        assert isinstance(msg, str)
        assert "Dynamic Market Data" in msg

    def test_build_user_message_none_context(self, sample_mso):
        msg = primary_analyzer_prompt.build_user_message(
            sample_mso, None, "2026-03-28T07:30:00Z",
        )
        assert isinstance(msg, str)
        assert len(msg) > 100


# ── Bull Agent ────────────────────────────────────────────────────────

class TestBullAgentPrompt:

    def test_system_prompt_contains_key_phrases(self):
        sp = bull_agent_prompt.SYSTEM_PROMPT
        assert "TAKE_TRADE" in sp
        assert "CANDIDATE" in sp
        assert "evidence" in sp.lower()
        assert "Data Grounding" in sp

    def test_build_user_message(self, sample_mso, sample_primary_analysis, sample_kb_context):
        msg = bull_agent_prompt.build_user_message(
            sample_mso, sample_primary_analysis, sample_kb_context,
        )
        assert isinstance(msg, str)
        assert "Market State Object" in msg
        assert "Primary Analysis" in msg
        assert "CANDIDATE" in msg
        assert "3038.5" in msg

    def test_build_user_message_empty_context(self, sample_mso, sample_primary_analysis):
        msg = bull_agent_prompt.build_user_message(
            sample_mso, sample_primary_analysis, {},
        )
        assert isinstance(msg, str)
        assert "No similar historical setups" in msg


# ── Bear Agent ────────────────────────────────────────────────────────

class TestBearAgentPrompt:

    def test_system_prompt_contains_key_phrases(self):
        sp = bear_agent_prompt.SYSTEM_PROMPT
        assert "DO_NOT_TRADE" in sp
        assert "risk" in sp.lower()
        assert "protect capital" in sp.lower()
        assert "Data Grounding" in sp

    def test_build_user_message(self, sample_mso, sample_primary_analysis, sample_kb_context):
        msg = bear_agent_prompt.build_user_message(
            sample_mso, sample_primary_analysis, sample_kb_context,
        )
        assert isinstance(msg, str)
        assert "Market State Object" in msg
        assert "NOT taking" in msg

    def test_build_user_message_none_context(self, sample_mso, sample_primary_analysis):
        msg = bear_agent_prompt.build_user_message(
            sample_mso, sample_primary_analysis, None,
        )
        assert isinstance(msg, str)


# ── Judge ─────────────────────────────────────────────────────────────

class TestJudgePrompt:

    def test_system_prompt_contains_key_phrases(self):
        sp = judge_prompt.SYSTEM_PROMPT
        assert "APPROVE" in sp
        assert "REJECT" in sp
        assert "CAPITAL PRESERVATION" in sp
        assert "Ties go to the bear" in sp
        assert "Data Grounding" in sp

    def test_build_user_message_without_round2(
        self, sample_primary_analysis, sample_bull, sample_bear,
    ):
        msg = judge_prompt.build_user_message(
            sample_primary_analysis, sample_bull, sample_bear, round2=None,
        )
        assert isinstance(msg, str)
        assert "Bull Argument" in msg
        assert "Bear Argument" in msg
        assert "Round 2: Not conducted" in msg

    def test_build_user_message_with_round2(
        self, sample_primary_analysis, sample_bull, sample_bear,
    ):
        r2 = DebateRound2(
            timestamp_utc="2026-03-28T07:17:00Z",
            bull_rebuttal=Rebuttal(
                points_addressed=["Friday risk"],
                rebuttal="TP1 closes 50% before noon.",
                concessions=["Liquidity does thin slightly."],
            ),
            bear_rebuttal=Rebuttal(
                points_addressed=["Clean sweep"],
                rebuttal="Sweep could still be a run.",
                concessions=["Displacement ratio is strong."],
            ),
        )
        msg = judge_prompt.build_user_message(
            sample_primary_analysis, sample_bull, sample_bear, round2=r2,
        )
        assert isinstance(msg, str)
        assert "Round 2 Rebuttals" in msg
        assert "TP1 closes" in msg

    def test_rebuttal_system_prompts_exist(self):
        assert "Bull Agent" in judge_prompt.BULL_REBUTTAL_SYSTEM_PROMPT
        assert "Bear Agent" in judge_prompt.BEAR_REBUTTAL_SYSTEM_PROMPT
        assert "Data Grounding" in judge_prompt.BULL_REBUTTAL_SYSTEM_PROMPT

    def test_build_rebuttal_message_bull(self, sample_bull, sample_bear):
        msg = judge_prompt.build_rebuttal_message(
            sample_bull, sample_bear, "bull",
        )
        assert isinstance(msg, str)
        assert "Bear's argument" in msg

    def test_build_rebuttal_message_bear(self, sample_bull, sample_bear):
        msg = judge_prompt.build_rebuttal_message(
            sample_bear, sample_bull, "bear",
        )
        assert isinstance(msg, str)
        assert "Bull's argument" in msg


# ── Postmortem ────────────────────────────────────────────────────────

class TestPostmortemPrompt:

    def test_system_prompt_contains_key_phrases(self):
        sp = postmortem_prompt.SYSTEM_PROMPT
        assert "postmortem" in sp.lower() or "completed" in sp.lower()
        assert "Data Grounding" in sp

    def test_build_user_message(self, sample_trade, sample_mso):
        outcome = {"outcome": "WIN", "r_multiple": 3.48, "pnl_dollars": 31.5}
        msg = postmortem_prompt.build_user_message(
            sample_trade, sample_mso, outcome,
        )
        assert isinstance(msg, str)
        assert "Completed Trade Record" in msg
        assert "Market State at Entry" in msg
        assert "Actual Outcome" in msg
        assert "3.48" in msg

    def test_build_user_message_empty_outcome(self, sample_trade, sample_mso):
        msg = postmortem_prompt.build_user_message(
            sample_trade, sample_mso, {},
        )
        assert isinstance(msg, str)
        assert len(msg) > 50

    def test_build_user_message_none_outcome(self, sample_trade, sample_mso):
        msg = postmortem_prompt.build_user_message(
            sample_trade, sample_mso, None,
        )
        assert isinstance(msg, str)


# ── Flow feature formatting in _format_tf (I1 feature engineering) ────

class TestFlowFeatureFormatting:

    def _format_tf(self, tf_data: dict) -> str:
        return primary_analyzer_prompt._format_tf("M15", tf_data)

    def test_clv_appears_in_output(self):
        tf_data = {
            "structure": {"direction": "bullish"},
            "clv_current": 0.73,
            "clv_avg_5": 0.31,
        }
        out = self._format_tf(tf_data)
        assert "CLV:" in out
        assert "+0.73" in out
        assert "+0.31" in out

    def test_clv_hidden_when_none(self):
        tf_data = {"structure": {"direction": "bullish"}}
        out = self._format_tf(tf_data)
        assert "CLV:" not in out

    def test_bvc_appears_in_output_buy(self):
        tf_data = {
            "structure": {"direction": "bullish"},
            "bvc_buy_fraction": 0.82,
            "net_flow_5": 4350,
        }
        out = self._format_tf(tf_data)
        assert "Flow:" in out
        assert "buy" in out
        assert "BVC=0.82" in out
        assert "+4350" in out

    def test_bvc_appears_in_output_sell(self):
        tf_data = {
            "structure": {"direction": "bearish"},
            "bvc_buy_fraction": 0.25,
            "net_flow_5": -2100,
        }
        out = self._format_tf(tf_data)
        assert "sell" in out
        assert "BVC=0.25" in out

    def test_bvc_neutral_label(self):
        tf_data = {
            "structure": {"direction": "bullish"},
            "bvc_buy_fraction": 0.50,
            "net_flow_5": 0,
        }
        out = self._format_tf(tf_data)
        assert "neutral" in out

    def test_bvc_hidden_when_none(self):
        tf_data = {"structure": {"direction": "bullish"}}
        out = self._format_tf(tf_data)
        assert "Flow:" not in out

    def test_session_atr_appears_with_ratio(self):
        tf_data = {
            "structure": {"direction": "bullish"},
            "atr_session": 8.52,
            "session_vol_ratio": 1.4,
        }
        out = self._format_tf(tf_data)
        assert "Session ATR:" in out
        assert "8.52" in out
        assert "HIGH" in out
        assert "1.4x avg" in out

    def test_session_atr_low_label(self):
        tf_data = {
            "structure": {"direction": "bullish"},
            "atr_session": 3.10,
            "session_vol_ratio": 0.6,
        }
        out = self._format_tf(tf_data)
        assert "low" in out

    def test_session_atr_hidden_when_none(self):
        tf_data = {"structure": {"direction": "bullish"}}
        out = self._format_tf(tf_data)
        assert "Session ATR:" not in out

    def test_all_features_absent_for_empty_tf(self):
        out = self._format_tf({})
        assert "CLV:" not in out
        assert "Flow:" not in out
        assert "Session ATR:" not in out
