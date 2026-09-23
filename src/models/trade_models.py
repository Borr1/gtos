"""Pydantic models for trade records, execution parameters, session state,
and the trade lifecycle state machine.

Trade Record:   knowledge_base/trades/tr_YYYY-MM-DD_NNN.yaml
Session:        knowledge_base/sessions/YYYY-MM-DD_session.json
No-Trade:       knowledge_base/no_trades/nt_YYYY-MM-DD_HHMM.yaml
Postmortem:     knowledge_base/postmortems/pm_tr_YYYY-MM-DD_NNN.yaml
Insights:       knowledge_base/insights/current_insights.yaml
"""

from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Lifecycle State Machine
# ---------------------------------------------------------------------------

VALID_TRANSITIONS: dict[str, set[str]] = {
    "EVALUATING": {"NO_TRADE", "CANDIDATE"},
    "CANDIDATE": {"DEBATED"},
    "DEBATED": {"REJECTED", "APPROVED"},
    "APPROVED": {"EXECUTING"},
    "EXECUTING": {"ACTIVE", "FAILED_EXECUTION"},
    "ACTIVE": {"CLOSED"},
}

TERMINAL_STATES: set[str] = {"NO_TRADE", "REJECTED", "FAILED_EXECUTION", "CLOSED"}


class InvalidTransitionError(Exception):
    pass


def transition(record: dict, from_state: str, to_state: str, event: str) -> None:
    """Enforce forward-only lifecycle transitions.

    Mutates *record* in place: updates ``lifecycle_state`` and appends to
    ``state_transitions``.

    Raises:
        InvalidTransitionError: if the record is not in *from_state*, or
            if *to_state* is not a valid successor of *from_state*, or
            if the record is already in a terminal state.
    """
    current = record["lifecycle_state"]

    if current in TERMINAL_STATES:
        raise InvalidTransitionError(
            f"Record is in terminal state {current}"
        )

    if current != from_state:
        raise InvalidTransitionError(
            f"Record is in {current}, not {from_state}"
        )

    if to_state not in VALID_TRANSITIONS.get(from_state, set()):
        raise InvalidTransitionError(
            f"Cannot transition from {from_state} to {to_state}"
        )

    record["lifecycle_state"] = to_state
    record["state_transitions"].append({
        "from": from_state,
        "to": to_state,
        "time": datetime.now(timezone.utc).isoformat(),
        "event": event,
    })


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class StateTransition(BaseModel):
    from_state: str = Field(alias="from")
    to_state: str = Field(alias="to")
    time: str
    event: str

    model_config = {"populate_by_name": True}


class TradeEvent(BaseModel):
    type: Literal[
        "PARTIAL_TP1", "PARTIAL_TP2", "RUNNER_TP3",
        "SL_HIT", "BE_HIT", "TRAIL_HIT",
        "SESSION_TIMEOUT", "MANUAL_CLOSE", "SYSTEM_ERROR",
    ]
    time: str
    price: float
    remaining_pct: float = Field(ge=0.0, le=1.0)


class DeterministicChecks(BaseModel):
    risk_exactly_1pct: bool = False
    within_session_window: bool = False
    sl_correct: bool = False
    position_size_correct: bool = False
    one_trade_limit: bool = False
    partials_correct: bool = False


class QualityScores(BaseModel):
    deterministic_score: float = 0.0
    deterministic_checks: Optional[DeterministicChecks] = None
    llm_score: float = 0.0
    combined_score: float = 0.0


class DebateFiles(BaseModel):
    round1: str = ""
    round2: str = ""
    verdict: str = ""


# ---------------------------------------------------------------------------
# Trade Record (Section 3.4)
# ---------------------------------------------------------------------------

class TradeRecord(BaseModel):
    trade_id: str
    date: str
    day_of_week: str

    # Lifecycle
    lifecycle_state: str = "EVALUATING"
    exit_substate: Optional[Literal[
        "CLOSED_SL", "CLOSED_BE", "CLOSED_TP2",
        "CLOSED_TP3_RUNNER", "CLOSED_TRAIL",
        "CLOSED_SESSION_TIMEOUT", "CLOSED_MANUAL",
        "CLOSED_SYSTEM_ERROR",
    ]] = None
    state_transitions: list[StateTransition] = Field(default_factory=list)

    # Trade parameters
    direction: Literal["LONG", "SHORT"]
    entry_price: float
    stop_loss: float
    sl_buffer_applied: float = 0.0
    take_profit_1: float
    take_profit_2: float = 0.0
    take_profit_3: float = 0.0
    risk_reward_ratio: float = 0.0
    position_size_lots: float = 0.0

    # Execution
    fill_price: Optional[float] = None
    slippage_cents: Optional[float] = None
    spread_at_entry: Optional[float] = None

    # Analysis context
    setup_grade: Literal["A+", "A", "B+", "B", "C"] = "C"
    daily_bias: Optional[str] = None
    h4_aligned: Optional[bool] = None
    liquidity_swept: Optional[str] = None
    displacement_quality: Optional[str] = None
    displacement_ratio: Optional[float] = None
    regime: Optional[str] = None

    # Debate
    debate_verdict: Optional[str] = None
    debate_confidence: Optional[int] = None
    bull_strength: Optional[int] = None
    bear_strength: Optional[int] = None
    debate_key_factor: Optional[str] = None
    debate_round2_enabled: bool = False

    # Outcome
    outcome: Optional[Literal["WIN", "LOSS", "BREAKEVEN"]] = None
    r_multiple: Optional[float] = None
    actual_risk_pct: Optional[float] = None
    pnl_dollars: Optional[float] = None
    hold_time_minutes: Optional[int] = None

    # Partial close events
    events: list[TradeEvent] = Field(default_factory=list)

    # Quality scores
    quality_scores: Optional[QualityScores] = None

    # Reasoning snapshot
    primary_analysis_file: Optional[str] = None
    debate_files: Optional[DebateFiles] = None


# ---------------------------------------------------------------------------
# Session Manifest (Section 3.5)
# ---------------------------------------------------------------------------

class PreSession(BaseModel):
    daily_bias: Optional[str] = None
    h4_alignment: Optional[str] = None
    key_levels_marked: list[str] = Field(default_factory=list)
    regime: Optional[str] = None
    high_impact_events: list[str] = Field(default_factory=list)


class CandleEvaluation(BaseModel):
    candle_time: str
    decision: str
    reason: Optional[str] = None
    confidence: Optional[int] = None
    setup_grade: Optional[str] = None
    debate_triggered: Optional[bool] = None
    debate_verdict: Optional[str] = None
    trade_executed: Optional[bool] = None
    trade_id: Optional[str] = None


class TradeSummary(BaseModel):
    trade_taken: bool = False
    trade_id: Optional[str] = None
    outcome: Optional[str] = None
    r_multiple: Optional[float] = None


class SessionManifest(BaseModel):
    date: str
    day_of_week: str
    session_start_utc: str
    session_end_utc: str
    pre_session: PreSession = Field(default_factory=PreSession)
    candle_evaluations: list[CandleEvaluation] = Field(default_factory=list)
    trade_summary: TradeSummary = Field(default_factory=TradeSummary)
    errors: list[str] = Field(default_factory=list)
    api_calls_count: int = 0
    api_cost_estimate_usd: float = 0.0


# ---------------------------------------------------------------------------
# No-Trade Record (Section 3.6)
# ---------------------------------------------------------------------------

class NoTradeReasoning(BaseModel):
    daily_bias: Optional[str] = None
    h4_alignment: Optional[str] = None
    stopped_at_step: Optional[int] = None
    full_explanation: str = ""


class NoTradeRecord(BaseModel):
    record_id: str
    date: str
    candle_time: str
    decision: Literal["NO_TRADE"] = "NO_TRADE"
    reason: str = ""
    reasoning: NoTradeReasoning = Field(default_factory=NoTradeReasoning)
    data_quality_ok: bool = True


# ---------------------------------------------------------------------------
# Postmortem Record (Section 3.7)
# ---------------------------------------------------------------------------

class LlmScoreBreakdown(BaseModel):
    bias_read: float = 0.0
    sweep_classification: float = 0.0
    displacement_assessment: float = 0.0
    grade_accuracy: float = 0.0
    missed_signals_penalty: float = 0.0


class PostmortemRecord(BaseModel):
    trade_id: str
    generated_at: str
    model_used: str

    # Hindsight analysis
    daily_bias_accuracy: str = ""
    h4_alignment_accuracy: str = ""
    sweep_classification_accuracy: str = ""
    displacement_assessment_accuracy: str = ""
    setup_grade_appropriate: bool = False
    missed_signals: list[str] = Field(default_factory=list)
    alternative_readings_in_hindsight: str = ""

    # LLM quality score
    llm_score: float = 0.0
    llm_score_breakdown: LlmScoreBreakdown = Field(default_factory=LlmScoreBreakdown)

    # Lessons
    lessons_learned: list[str] = Field(default_factory=list)
    key_pattern: str = ""

    # Summary
    summary: str = ""

    # Debate evaluation
    debate_verdict_correct: Optional[bool] = None
    debate_notes: str = ""


# ---------------------------------------------------------------------------
# Compressed Insights (Section 3.9)
# ---------------------------------------------------------------------------

class ConditionInsight(BaseModel):
    condition: str
    sample_size: int
    win_rate: float
    expectancy: float
    avg_r_winner: float = 0.0
    avg_r_loser: float = 0.0
    flag: Literal[
        "STRONG_EDGE", "UNDERPERFORMING",
        "SIGNIFICANTLY_UNDERPERFORMING", "NEUTRAL",
    ] = "NEUTRAL"
    note: str = ""


class DebateCalibration(BaseModel):
    total_debates: int = 0
    bull_wins: int = 0
    bear_wins: int = 0
    bull_win_rate: float = 0.0
    bear_win_rate: float = 0.0
    false_approvals_pct: float = 0.0
    false_rejections_pct: float = 0.0
    calibration_note: str = ""


class RegimeInsight(BaseModel):
    current_regime: str = ""
    regime_started: str = ""
    model_performance_in_regime: str = ""


class FailurePattern(BaseModel):
    pattern: str
    affected_trades: int
    all_losses: bool = False
    recommendation: str = ""


class RuleModification(BaseModel):
    modification: str
    date: str
    impact: str = ""
    status: Literal["permanent", "trial", "reverted"] = "trial"


class CompressedInsights(BaseModel):
    generated_at: str
    total_trades_analyzed: int = 0
    overall_win_rate: float = 0.0
    overall_expectancy: float = 0.0
    overall_profit_factor: float = 0.0
    max_consecutive_losses: int = 0

    condition_insights: list[ConditionInsight] = Field(default_factory=list)
    debate_calibration: DebateCalibration = Field(default_factory=DebateCalibration)
    regime_insight: RegimeInsight = Field(default_factory=RegimeInsight)
    active_failure_patterns: list[FailurePattern] = Field(default_factory=list)
    rule_modification_history: list[RuleModification] = Field(default_factory=list)
