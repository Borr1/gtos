"""Pydantic models for Bull/Bear Debate and Judge verdict (Component 3B).

Round 1: pipeline_state/03b_debate_round1.json
Round 2: pipeline_state/03b_debate_round2.json
Verdict: pipeline_state/03b_verdict.json
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class BullKeyPoint(BaseModel):
    point: str
    supporting_data: str = ""


class BullArgument(BaseModel):
    position: Literal["TAKE_TRADE"] = "TAKE_TRADE"
    argument_strength_self_assessed: int = Field(ge=0, le=100)
    key_points: list[BullKeyPoint] = Field(default_factory=list)
    historical_parallels_cited: list[str] = Field(default_factory=list)
    full_argument: str = ""


class BearRisk(BaseModel):
    risk: str
    severity: Literal["high", "medium", "low"]
    evidence: str = ""


class BearArgument(BaseModel):
    position: Literal["DO_NOT_TRADE"] = "DO_NOT_TRADE"
    argument_strength_self_assessed: int = Field(ge=0, le=100)
    key_points: list[BullKeyPoint] = Field(default_factory=list)
    risks_identified: list[BearRisk] = Field(default_factory=list)
    alternative_interpretations: list[str] = Field(default_factory=list)
    full_argument: str = ""


class DebateRound1(BaseModel):
    timestamp_utc: str
    bull_argument: BullArgument
    bear_argument: BearArgument


class Rebuttal(BaseModel):
    points_addressed: list[str] = Field(default_factory=list)
    rebuttal: str = ""
    concessions: list[str] = Field(default_factory=list)


class DebateRound2(BaseModel):
    timestamp_utc: str
    bull_rebuttal: Rebuttal
    bear_rebuttal: Rebuttal


class DebateVerdict(BaseModel):
    timestamp_utc: str
    model_used: str
    verdict: Literal["APPROVE", "REJECT"]
    winning_perspective: Literal["BULL", "BEAR"]
    confidence_score: int = Field(ge=0, le=100)
    bull_argument_strength: int = Field(ge=0, le=100)
    bear_argument_strength: int = Field(ge=0, le=100)
    key_factor: str = ""
    risk_concerns_acknowledged: list[str] = Field(default_factory=list)
    summary: str = ""
