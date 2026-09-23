"""Pytest entry-point for the counterfactual_fills harness.

The harness itself lives in ``tests/replay/counterfactual_fills.py`` so
test authors can import ``load_historical_fills``, ``run_counterfactual``,
etc., from a single module. This file just re-exports the test class so
pytest's default collection (``test_*.py``) picks it up under
``pytest tests/replay/``.
"""
import pytest

from tests.replay.counterfactual_fills import TestCounterfactualFills  # noqa: F401


pytestmark = pytest.mark.replay
