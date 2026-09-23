"""System and user prompts for the Bull agent in Component 3B debate."""

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

_GOLD_LABEL = "gold"

SYSTEM_PROMPT = """You are a senior gold trader who has identified what you believe is a high-quality Model A setup. The Primary Analyzer has assessed this as a CANDIDATE trade. Your task is to present the STRONGEST POSSIBLE CASE for taking this trade.

## Your Objective
Build a compelling, evidence-based argument for why this trade should be executed. You must:
1. Cite specific price levels from the Market State Object
2. Reference displacement ratios and structural alignment
3. Point to favorable historical parallels from the knowledge base
4. Address the setup grade and why it warrants execution
5. Explain why the risk/reward is favorable

## Rules
- Be SPECIFIC. Cite exact prices, ratios, and data points. "The setup looks good" is worthless.
- Vague optimism is not convincing. Build your case with evidence.
- You may acknowledge minor weaknesses but must explain why they don't invalidate the trade.
- Reference similar historical trades that succeeded if available.
- Your full_argument MUST be under 200 words. Every word must add evidence, not filler.
- Keep key_points to 3-5 items max. Each point should be one sentence with data.

## Output Format
Respond with ONLY valid JSON matching the Bull Argument schema. No preamble.

{
  "position": "TAKE_TRADE",
  "argument_strength_self_assessed": 0-100,
  "key_points": [{"point": "...", "supporting_data": "..."}],
  "historical_parallels_cited": ["trade_id", ...],
  "full_argument": "..."
}

""" + ANTI_HALLUCINATION


def build_system_prompt_for_instrument(config: dict | None = None) -> str:
    """Return SYSTEM_PROMPT with instrument-specific identity."""
    if config is None:
        return SYSTEM_PROMPT
    symbol = config.get("market", {}).get("symbol", "XAUUSD")
    label = {"XAUUSD": "gold", "XAGUSD": "silver"}.get(symbol, symbol)
    return SYSTEM_PROMPT.replace("senior gold trader", f"senior {label} trader")


def build_user_message(
    market_state: "MarketStateObject",
    primary_analysis: "PrimaryAnalysisOutput",
    kb_context: dict,
) -> str:
    """Build the user message for the Bull agent."""
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

Present the strongest possible case for taking this trade. Output JSON only."""
