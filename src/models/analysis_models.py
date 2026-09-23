"""Pydantic models for Primary Analyzer output (Component 3A).

Written to pipeline_state/03a_primary_analysis.json by Component 3A.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class DailyBiasAnalysis(BaseModel):
    direction: Literal["bullish", "bearish", "ranging"]
    confidence: Literal["high", "medium", "low"]
    protected_swing_level: float = 0.0
    explanation: str = ""


class H4AlignmentAnalysis(BaseModel):
    aligned: bool
    h4_pois_identified: list[str] = Field(default_factory=list)
    explanation: str = ""


class H1SetupAnalysis(BaseModel):
    poi_identified: bool
    poi_type: Literal["OB", "FVG", "breaker_block", "liquidity_zone", "none"] = "none"
    poi_price_level: float = 0.0
    zone: Literal["premium", "discount", "neutral"] = "neutral"
    fib_retracement_pct: float = 0.0
    causing_event_type: Literal["BOS", "CHoCH", "price_action", "unknown"] = "unknown"
    explanation: str = ""


class LiquiditySweepAnalysis(BaseModel):
    detected: bool
    pool_type: Literal[
        "asian_high", "asian_low", "pdh", "pdl",
        "equal_highs", "equal_lows",
        "session_high", "session_low",
        "london_high", "london_low",
        "none",
    ] = "none"
    sweep_quality: Literal["clean", "messy", "ambiguous"] = "ambiguous"
    sweep_price: float = 0.0
    explanation: str = ""


class M15ConfirmationAnalysis(BaseModel):
    choch_detected: bool
    displacement_quality: Literal["strong", "medium", "weak", "none"] = "none"
    displacement_candle_body_vs_avg_ratio: float = 0.0
    explanation: str = ""


class SimilarSetupReference(BaseModel):
    trade_id: str
    similarity_score: float
    outcome: Literal["WIN", "LOSS", "BREAKEVEN"]
    r_multiple: float
    key_difference: str = ""


class TradeParameters(BaseModel):
    direction: Literal["LONG", "SHORT"]
    entry_price: float
    stop_loss: float
    sl_buffer_applied: float = 0.0
    take_profit_1: float
    take_profit_2: float = 0.0
    take_profit_3: float = 0.0
    risk_reward_ratio: float
    position_size_lots: float = 0.0


class PrimaryAnalysisReasoning(BaseModel):
    daily_bias: DailyBiasAnalysis
    h4_alignment: H4AlignmentAnalysis
    h1_setup: H1SetupAnalysis
    liquidity_sweep: LiquiditySweepAnalysis
    m15_confirmation: M15ConfirmationAnalysis
    similar_historical_setups_considered: list[SimilarSetupReference] = Field(
        default_factory=list
    )
    setup_grade: Literal["A+", "A", "B+", "B", "C"] = "C"
    overall_reasoning: str = ""


class FrameworkEvaluation(BaseModel):
    qualified: bool = False
    reason: str = ""


class PrimaryAnalysisOutput(BaseModel):
    timestamp_utc: str
    model_used: str
    decision: Literal["NO_TRADE", "CANDIDATE", "WAIT"]
    confidence_score: int = 0
    confidence_computation: Optional[str] = None
    framework: Literal[
        "session_sweep",
        "ob_retest",
        "breaker_retest",
        # ``breaker_re_entry`` (2026-04-25): explicit additive framework activated
        # for FTMO challenge. Distinct from legacy ``breaker_retest`` only by
        # name — both anchor on the ``breaker_blocks`` MSO field, but
        # ``breaker_re_entry`` is the production-facing label gated by
        # ``model_a.enabled_frameworks`` and verified by L2's
        # ``entry_in_breaker`` check. Existing ``breaker_retest`` literal is
        # preserved for backwards compatibility with historical fixtures.
        "breaker_re_entry",
        "equal_sweep",
        "fvg_fill",
        "none",
    ] = "none"
    kill_zone: Literal["london", "ny", "tokyo"] = "london"
    frameworks_evaluated: Optional[dict[str, FrameworkEvaluation]] = None
    reasoning: PrimaryAnalysisReasoning
    trade_parameters: Optional[TradeParameters] = None
    no_trade_reason: Optional[str] = None
    wait_reason: Optional[str] = None
