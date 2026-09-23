"""Tool ABC and shared schema utilities for AI tool-use grounding.

DESIGN.md §3.1 — each Tool must declare:
- ``name`` (matches Anthropic API ``tools[].name``)
- ``description`` (system-prompt-style guidance for when to call)
- ``input_schema`` (JSONSchema dict — Anthropic API ``tools[].input_schema``)
- ``execute(**kwargs) -> dict`` (returns a JSON-serializable result)

This is a SCAFFOLD only. No subclass yet wires into ``PrimaryAnalyzer``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping


class Tool(ABC):
    """Abstract base for all AI-callable tools.

    Subclasses MUST set ``name``, ``description``, ``input_schema`` as
    class-level attributes and implement ``execute``. Output of
    ``execute`` MUST be JSON-serializable (dict / list / scalar).
    """

    # Set by subclasses
    name: str = ""
    description: str = ""
    input_schema: Mapping[str, Any] = {}

    @abstractmethod
    def execute(self, **kwargs: Any) -> dict:
        """Execute the tool with the given keyword arguments.

        Errors MUST be returned as a dict with an ``"error"`` key, never
        raised — Anthropic tool_result blocks expect a string payload,
        and the multi-turn loop assumes errors are surfaced through that
        channel rather than propagating to the caller.
        """
        raise NotImplementedError

    def to_anthropic_tool_def(self) -> dict:
        """Render the tool definition in Anthropic API format.

        Used to populate the ``tools=[...]`` parameter on
        ``client.messages.create``. The shape is::

            {"name": str, "description": str, "input_schema": dict}
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": dict(self.input_schema),
        }


# ── Shared schema fragments (DRY) ────────────────────────────────────

LIVE_SYMBOLS = [
    "AUDJPY",
    "AUDUSD",
    "BTCUSD",
    "CHFJPY",
    "ETHUSD",
    "EURGBP",
    "EURJPY",
    "EURUSD",
    "GBPJPY",
    "GBPUSD",
    "GER40",
    "JP225",
    "NAS100",
    "NZDUSD",
    "SPX500",
    "UK100",
    "UKOIL_cash",
    "US30_cash",
    "USDCAD",
    "USDCHF",
    "USDJPY",
    "USOIL_cash",
    "XAGUSD",
    "XAUUSD",
]
"""Stage03 broker-native vNext production symbol surface."""

DAYS_BACK_PROPERTY = {
    "type": "integer",
    "minimum": 7,
    "maximum": 90,
    "description": "Lookback window in days (7-90).",
}

SYMBOL_PROPERTY = {
    "type": "string",
    "enum": LIVE_SYMBOLS,
    "description": "Instrument symbol; must be one of the Stage08 broker-native vNext symbols.",
}

DIRECTION_PROPERTY = {
    "type": "string",
    "enum": ["LONG", "SHORT"],
    "description": "Trade direction.",
}


__all__ = [
    "Tool",
    "LIVE_SYMBOLS",
    "DAYS_BACK_PROPERTY",
    "SYMBOL_PROPERTY",
    "DIRECTION_PROPERTY",
]
