"""AI tool-use grounding module — scaffolding (sprint-3 design phase).

This module hosts the tool-fetching helpers that will eventually be wired
into ``PrimaryAnalyzer._call_claude`` via Anthropic's tool-use API. As of
2026-04-25 the helpers are NOT yet wired into the live trading path —
only the data-fetching utility functions exist, callable independently
for testing and validation.

Design doc: ``research/tool_use_grounding/DESIGN.md``.

Module layout
-------------
- ``base.py``        — Tool ABC + shared schema definitions
- ``registry.py``    — TOOL_REGISTRY mapping tool name -> ToolDef
- ``query_recent_outcomes.py``  — Tool A (rank #1)
- ``lookup_session_vol.py``     — Tool B (rank #2; placeholder skeleton)

When wiring becomes live, add the import + registry call here:

    from src.components.ai_tools.registry import TOOL_REGISTRY  # noqa: F401

so callers can do ``from src.components.ai_tools import TOOL_REGISTRY``.
"""

from __future__ import annotations

# Intentionally empty for the design-phase scaffold — implementation agent
# wires up exports in Phase 1 step 5 of DESIGN.md §6.1.

__all__: list[str] = []
