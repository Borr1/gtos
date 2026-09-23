"""DP4 V3 control — thin wrapper around the production V3 prompt.

This is the BASELINE for the DP4 A/B test. It delegates all prompt assembly
to the production `src.prompts.primary_analyzer_prompt` module so the
V3-control variant is bit-identical to what lives on main today.

The sibling modules `prompt_lira.py` and `prompt_nocot.py` are the
counter-factuals that keep the SAME system-prompt core (gate criteria,
allow-list, H1 POI rules) but swap the OUTPUT STRUCTURE. That is the
apples-to-apples axis the DP4 experiment isolates.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.prompts.primary_analyzer_prompt import (
    build_static_context,
    build_system_prompt as _build_production_system_prompt,
    build_user_message as _build_production_user_message,
)

if TYPE_CHECKING:
    from src.models.market_state_models import MarketStateObject


VARIANT_NAME = "v3_control"


def build_system_prompt(config: dict | None = None) -> str:
    """Return the production V3 system prompt verbatim."""
    return _build_production_system_prompt(config)


def build_user_message(
    market_state: "MarketStateObject",
    kb_context: dict,
    current_time: str,
    kill_zone: str = "london",
    **kwargs,
) -> str:
    """Return the production V3 user message verbatim."""
    return _build_production_user_message(
        market_state,
        kb_context,
        current_time,
        kill_zone=kill_zone,
        **kwargs,
    )
