"""Tool registry — central catalog of AI-callable tools.

DESIGN.md §6.1 Phase-1 step 5: when wiring goes live, ``PrimaryAnalyzer``
will iterate ``TOOL_REGISTRY.values()`` to populate Anthropic's
``tools=[...]`` parameter and dispatch tool_use blocks back to the
correct ``Tool.execute`` instance.

This is a SCAFFOLD. Phase-1 build wires the registry into
``primary_analyzer.py`` behind a ``config.ai.tool_use_enabled`` feature
flag (default false).
"""

from __future__ import annotations

from src.components.ai_tools.base import Tool
from src.components.ai_tools.lookup_session_vol import LookupSessionVolatilityTool
from src.components.ai_tools.query_recent_outcomes import (
    QueryRecentTradeOutcomesTool,
)

# Order is intentional — first to register is first in Anthropic's tools=
# array. Models tend to favor earlier tools slightly. RANK #1 first.
_TIER1_TOOLS: list[Tool] = [
    QueryRecentTradeOutcomesTool(),
    LookupSessionVolatilityTool(),
    # check_correlation_exposure -- Phase 1 build (DESIGN.md §2.1 Tool C)
]

# Tier-2 tools (DESIGN.md §2.2) deliberately not included until Phase 4
# data-density gate is met.
_TIER2_TOOLS: list[Tool] = [
    # query_historical_WR        -- DESIGN.md §2.2 Tool D
    # find_similar_setups        -- DESIGN.md §2.2 Tool E
]

TOOL_REGISTRY: dict[str, Tool] = {
    tool.name: tool for tool in (_TIER1_TOOLS + _TIER2_TOOLS)
}


def get_anthropic_tool_defs() -> list[dict]:
    """Return the list of tool definitions in Anthropic API shape.

    Pass into ``client.messages.create(tools=...)``::

        response = client.messages.create(
            model="claude-sonnet-4-6",
            tools=get_anthropic_tool_defs(),
            ...
        )
    """
    return [tool.to_anthropic_tool_def() for tool in TOOL_REGISTRY.values()]


def execute_tool_call(name: str, tool_input: dict) -> dict:
    """Dispatch a tool_use block to the correct Tool.execute.

    Returns a dict suitable for stringifying into a tool_result block.
    Errors are SURFACED THROUGH THE RETURN DICT, never raised — see
    ``Tool.execute`` contract in ``base.py``.
    """
    tool = TOOL_REGISTRY.get(name)
    if tool is None:
        return {"error": "unknown_tool", "name": name,
                "available_tools": list(TOOL_REGISTRY.keys())}
    try:
        return tool.execute(**tool_input)
    except Exception as exc:  # pragma: no cover (defensive)
        return {"error": "tool_execution_failed", "name": name,
                "exception": str(exc)}


__all__ = [
    "TOOL_REGISTRY",
    "execute_tool_call",
    "get_anthropic_tool_defs",
]
