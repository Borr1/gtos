"""Tests for the AI-tool registry — DESIGN.md §6.1 Phase-1 step 5 wiring."""

from __future__ import annotations

import pytest

from src.components.ai_tools.registry import (
    TOOL_REGISTRY,
    execute_tool_call,
    get_anthropic_tool_defs,
)


def test_registry_has_tier1_tools():
    """Phase-1 minimum: query_recent_trade_outcomes + lookup_session_volatility."""
    assert "query_recent_trade_outcomes" in TOOL_REGISTRY
    assert "lookup_session_volatility" in TOOL_REGISTRY


def test_anthropic_tool_defs_well_formed():
    defs = get_anthropic_tool_defs()
    assert isinstance(defs, list)
    assert len(defs) >= 2
    for d in defs:
        # Each def must have these keys per Anthropic API contract.
        assert set(d.keys()) >= {"name", "description", "input_schema"}
        assert isinstance(d["name"], str) and d["name"]
        assert isinstance(d["description"], str) and d["description"]
        assert d["input_schema"]["type"] == "object"


def test_unknown_tool_returns_error():
    out = execute_tool_call("not_a_tool", {})
    assert out["error"] == "unknown_tool"
    assert "available_tools" in out


def test_execute_tool_call_dispatches(tmp_path, monkeypatch):
    """Dispatch should invoke the tool's execute, not raise on bad input."""
    # Empty args -> tool returns its error dict, never raises.
    out = execute_tool_call("query_recent_trade_outcomes", {"symbol": "BAD"})
    assert out["error"] == "unknown_symbol"


def test_lookup_session_volatility_unknown_session():
    out = execute_tool_call(
        "lookup_session_volatility",
        {"symbol": "XAUUSD", "session": "ZULU"},
    )
    assert out["error"] == "unknown_session"


def test_lookup_session_volatility_unknown_symbol():
    out = execute_tool_call(
        "lookup_session_volatility",
        {"symbol": "FAKE", "session": "ny"},
    )
    assert out["error"] == "unknown_symbol"


def test_no_tier2_tools_in_phase1():
    """DESIGN.md §6.4: tier-2 tools (D, E) must NOT be registered in Phase 1.

    Sparse-data risk (R7) means they would return n=0 ≥80% of the time
    at current scale. Defer until 50-instrument scale.
    """
    assert "query_historical_WR" not in TOOL_REGISTRY
    assert "find_similar_setups" not in TOOL_REGISTRY


def test_tool_descriptions_contain_use_guidance():
    """Anthropic docs: tool descriptions should tell the model WHEN to call.

    DESIGN.md §7 R1 (AI ignores tools) — guard against descriptions that
    are pure technical specs. Each must contain "use" or "when".
    """
    for name, tool in TOOL_REGISTRY.items():
        desc_lower = tool.description.lower()
        assert "use" in desc_lower or "when" in desc_lower, (
            f"Tool {name!r} description lacks call-time guidance: {tool.description}"
        )
