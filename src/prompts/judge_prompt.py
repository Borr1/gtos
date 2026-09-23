"""System and user prompts for the Judge in Component 3B debate."""

from __future__ import annotations

import json
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.analysis_models import PrimaryAnalysisOutput
    from src.models.debate_models import BullArgument, BearArgument, DebateRound2

from src.prompts.primary_analyzer_prompt import ANTI_HALLUCINATION

# ── Section 5.5 — Judge System Prompt ─────────────────────────────────
SYSTEM_PROMPT = """You are the fund manager making the final allocation decision on a gold trade. You have heard both the bull case (for the trade) and the bear case (against the trade). Your job is to evaluate the QUALITY of each argument and deliver a final verdict.

## Your Decision Framework
1. Which argument is better supported by the ACTUAL price data in the Market State Object?
2. Did either agent fabricate confluence or ignore contradicting data?
3. Are the bear's risks genuine and material, or speculative and unlikely?
4. Are the bull's strengths specific and verifiable, or vague and hopeful?
5. Does the knowledge base context (historical parallels, insights) support or contradict the trade?

## Your Default Bias: CAPITAL PRESERVATION
- If the arguments are roughly equal in strength: REJECT. Ties go to the bear.
- Only APPROVE if the bull case is CLEARLY and SPECIFICALLY stronger than the bear case.
- A CANDIDATE with genuine weaknesses identified by the bear should be REJECTED even if the bull makes a decent case.

## Confidence Score Guidelines
- 85-100: Overwhelming bull case, bear found no material weaknesses
- 70-84: Strong bull case, bear's concerns are minor or manageable
- 50-69: Bull case is stronger but bear raised valid concerns. Trade proceeds but flagged as marginal.
- Below 50: Insufficient conviction → treated as REJECT regardless of verdict field

## Rules
- You do NOT produce new analysis. You evaluate the arguments presented.
- If either agent's argument contains claims not supported by the Market State Object data, call it out.
- Be explicit about which specific point tipped your decision.

## Output Format
Respond with ONLY valid JSON matching the Verdict schema. No preamble.

{
  "verdict": "APPROVE | REJECT",
  "winning_perspective": "BULL | BEAR",
  "confidence_score": 0-100,
  "bull_argument_strength": 0-100,
  "bear_argument_strength": 0-100,
  "key_factor": "...",
  "risk_concerns_acknowledged": ["..."],
  "summary": "..."
}

""" + ANTI_HALLUCINATION


def build_system_prompt_for_instrument(config: dict | None = None) -> str:
    """Return SYSTEM_PROMPT with instrument-specific identity."""
    if config is None:
        return SYSTEM_PROMPT
    symbol = config.get("market", {}).get("symbol", "XAUUSD")
    label = {"XAUUSD": "gold", "XAGUSD": "silver"}.get(symbol, symbol)
    return SYSTEM_PROMPT.replace("a gold trade", f"a {label} trade")


# ── Section 5.6 — Rebuttal System Prompts ─────────────────────────────

BULL_REBUTTAL_SYSTEM_PROMPT = """You are the Bull Agent. You have read the Bear's argument against this trade. Respond to their specific points. For each bear point: either rebut it with specific data, or concede it as valid. Be honest — conceding weak points strengthens your overall credibility.

""" + ANTI_HALLUCINATION

BEAR_REBUTTAL_SYSTEM_PROMPT = """You are the Bear Agent. You have read the Bull's argument for this trade. Respond to their specific points. For each bull point: either challenge it with specific counter-evidence, or concede it as valid. Your job is still to protect capital — but intellectual honesty strengthens your case.

""" + ANTI_HALLUCINATION


# ── Message builders ──────────────────────────────────────────────────

def build_user_message(
    primary_analysis: "PrimaryAnalysisOutput",
    bull_r1: "BullArgument",
    bear_r1: "BearArgument",
    round2: "Optional[DebateRound2]" = None,
) -> str:
    """Build the user message for the Judge."""
    pa_json = json.dumps(
        primary_analysis.model_dump(mode="json") if hasattr(primary_analysis, "model_dump")
        else primary_analysis,
        indent=2,
    )
    bull_json = json.dumps(
        bull_r1.model_dump(mode="json") if hasattr(bull_r1, "model_dump")
        else bull_r1,
        indent=2,
    )
    bear_json = json.dumps(
        bear_r1.model_dump(mode="json") if hasattr(bear_r1, "model_dump")
        else bear_r1,
        indent=2,
    )

    parts = [
        f"## Primary Analysis\n{pa_json}",
        f"## Bull Argument (Round 1)\n{bull_json}",
        f"## Bear Argument (Round 1)\n{bear_json}",
    ]

    if round2 is not None:
        r2_json = json.dumps(
            round2.model_dump(mode="json") if hasattr(round2, "model_dump")
            else round2,
            indent=2,
        )
        parts.append(f"## Round 2 Rebuttals\n{r2_json}")
    else:
        parts.append("## Round 2: Not conducted.")

    parts.append(
        "Evaluate both arguments and deliver your verdict. Output JSON only."
    )
    return "\n\n".join(parts)


def build_rebuttal_message(
    own_argument: dict,
    opposing_argument: dict,
    side: str,
) -> str:
    """Build the user message for a Round 2 rebuttal.

    *side* is ``"bull"`` or ``"bear"``.
    """
    own_json = json.dumps(
        own_argument.model_dump(mode="json") if hasattr(own_argument, "model_dump")
        else own_argument,
        indent=2,
    )
    opp_json = json.dumps(
        opposing_argument.model_dump(mode="json") if hasattr(opposing_argument, "model_dump")
        else opposing_argument,
        indent=2,
    )

    if side == "bull":
        label = "Bear's"
        role = "Bull"
    else:
        label = "Bull's"
        role = "Bear"

    return f"""{label} argument:
{opp_json}

Your Round 1 argument:
{own_json}

Respond to their specific points. Output JSON only:
{{"points_addressed": [...], "rebuttal": "...", "concessions": [...]}}"""
