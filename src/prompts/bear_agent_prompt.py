"""System and user prompts for the Bear agent in Component 3B debate."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.analysis_models import PrimaryAnalysisOutput
    from src.models.market_state_models import MarketStateObject

from src.prompts.primary_analyzer_prompt import (
    ANTI_HALLUCINATION,
    _format_layer3,
)

SYSTEM_PROMPT = """You are a senior risk manager whose primary job is to protect capital. The Primary Analyzer has identified a CANDIDATE trade. Your task is to present the STRONGEST POSSIBLE CASE for NOT taking this trade.

## Your Objective
Find every legitimate reason to reject this trade. You must:
1. Look for alternative structure readings that contradict the Primary Analyzer
2. Assess whether displacement is genuinely strong or borderline
3. Question the sweep classification — could it be a run, not a sweep?
4. Check for unfavorable patterns from the knowledge base (similar setups that failed)
5. Identify proximity to high-impact news events
6. Assess regime conditions — does the current regime favor this setup type?
7. Look for any signal the Primary Analyzer may have downplayed or missed

## Rules
- Be SPECIFIC. "This trade is risky" is worthless. Identify WHAT is risky and WHY with data.
- Vague pessimism is as useless as vague optimism.
- You may acknowledge genuine strengths but must explain why weaknesses outweigh them.
- Reference similar historical trades that FAILED if available.
- Your default recommendation is DO_NOT_TRADE. You only concede if you genuinely cannot find material weaknesses.
- Your full_argument MUST be under 200 words. Every word must add evidence, not filler.
- Keep key_points to 3-5 items, risks_identified to 2-3 items. Be surgical, not exhaustive.

## Output Format
Respond with ONLY valid JSON matching the Bear Argument schema. No preamble.

{
  "position": "DO_NOT_TRADE",
  "argument_strength_self_assessed": 0-100,
  "key_points": [{"point": "...", "supporting_data": "..."}],
  "risks_identified": [{"risk": "...", "severity": "high|medium|low", "evidence": "..."}],
  "alternative_interpretations": ["..."],
  "full_argument": "..."
}

""" + ANTI_HALLUCINATION


def build_system_prompt_for_instrument(config: dict | None = None) -> str:
    """Return SYSTEM_PROMPT with instrument-specific identity."""
    # Bear agent prompt doesn't mention "gold" in the identity line,
    # so no replacement needed. Kept for API consistency.
    return SYSTEM_PROMPT


def build_user_message(
    market_state: "MarketStateObject",
    primary_analysis: "PrimaryAnalysisOutput",
    kb_context: dict,
) -> str:
    """Build the user message for the Bear agent."""
    mso_json = json.dumps(
        market_state.model_dump(mode="json") if hasattr(market_state, "model_dump")
        else market_state,
        indent=2,
    )
    if len(mso_json) > 12_000:
        mso_json = mso_json[:12_000] + "\n... [truncated]"

    pa_json = json.dumps(
        primary_analysis.model_dump(mode="json") if hasattr(primary_analysis, "model_dump")
        else primary_analysis,
        indent=2,
    )

    layer3 = (kb_context or {}).get("layer3", [])

    return f"""## Market State Object
{mso_json}

## Primary Analysis (CANDIDATE)
{pa_json}

## Similar Historical Setups
{_format_layer3(layer3)}

Present the strongest possible case for NOT taking this trade. Output JSON only."""
