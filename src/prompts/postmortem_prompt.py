"""System and user prompts for postmortem analysis."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.market_state_models import MarketStateObject
    from src.models.trade_models import TradeRecord

from src.prompts.primary_analyzer_prompt import ANTI_HALLUCINATION

SYSTEM_PROMPT = """You are analyzing a completed trade. Evaluate the quality of the reasoning and decisions made. Be honest and specific — the purpose of this postmortem is to improve future performance, not to justify past actions.

## Your Tasks
1. Assess accuracy of each analysis step (daily bias, H4 alignment, sweep classification, displacement quality, setup grade)
2. Identify any signals that were missed or misread
3. Score the AI's reasoning quality (0-100) with breakdowns
4. Extract concrete, actionable lessons learned
5. Generate a compact summary suitable for embedding in the knowledge base

## Scoring Guidelines
- 90-100: Near-perfect analysis, all assessments correct, no missed signals
- 75-89: Good analysis with minor inaccuracies that didn't affect outcome
- 60-74: Adequate analysis but with notable misreads or missed factors
- Below 60: Material errors in reasoning that led to poor outcomes

## Output Format
Respond with ONLY valid JSON matching the PostmortemRecord schema. No preamble, no markdown fences, no explanation outside the JSON structure.

""" + ANTI_HALLUCINATION


def build_user_message(
    trade: "TradeRecord",
    market_state_at_entry: "MarketStateObject",
    actual_outcome: dict,
) -> str:
    """Build the user message for postmortem generation."""
    trade_json = json.dumps(
        trade.model_dump(mode="json") if hasattr(trade, "model_dump")
        else trade,
        indent=2,
    )

    mso_json = json.dumps(
        market_state_at_entry.model_dump(mode="json")
        if hasattr(market_state_at_entry, "model_dump")
        else market_state_at_entry,
        indent=2,
    )
    if len(mso_json) > 12_000:
        mso_json = mso_json[:12_000] + "\n... [truncated]"

    outcome_json = json.dumps(actual_outcome or {}, indent=2)

    return f"""## Completed Trade Record
{trade_json}

## Market State at Entry
{mso_json}

## Actual Outcome
{outcome_json}

Analyze this completed trade. Evaluate the quality of the reasoning and decisions. Output JSON only."""
