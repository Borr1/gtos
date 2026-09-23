"""Research-program scripts (Phase 1).

This package is a deliberately thin namespace for ad-hoc research tooling
that is NOT part of the live trading path. Files here are dispatched by
the CEO + research agents, not by the orchestrator.

Anything under this package MUST be additive — never import from here in
``src/`` or ``run_agent.py``.
"""
