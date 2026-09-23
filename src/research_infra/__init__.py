# GTOS research infrastructure (Phase 1)
"""Research infrastructure helpers for Phase 1 of the GTOS research program.

This package is **additive only** — production trading code (Component 3A,
Component 4, ``primary_analyzer.py``, ``permissions.py``, etc.) does **not**
import from ``src.research_infra``. Helpers under this package exist solely
for non-trading research workflows (decay analysis, regime classification
study, summary aggregation, batch jobs, fixture generation, etc.).

Hard rule preserved here: the trading-decision (MSO gate) call **must**
remain on Sonnet 4.6 effort=max as enforced by ``model_router.py``. Any
research helper that needs an LLM call should route through
``ModelRouter.route()`` so accidental drift to a different model in
ad-hoc analysis scripts is impossible.
"""
