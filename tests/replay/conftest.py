"""Shared fixtures for replay tests.

The fixtures are generators/lazy iterables so we don't hold 1,000+ rows in
memory when a test only needs to sample. Callers that need deterministic
replay can materialize with ``list(...)``.

Design notes
------------
- ``live_eval_rows``: thin metadata from ``knowledge_base/live_evaluations/*.jsonl``.
  ~1,000 rows fleet-wide for last 30 days. One row per AI call. No MSO.
- ``trade_records``: full-fidelity from ``knowledge_base/trade_records/*.json``.
  Smaller n (~90 in April) but contains MSO + AI output + decision_pipeline
  + trade_parameters + shadow data. This is what you replay through changed
  code paths.
- ``historical_fills``: subset of trade_records where execution metadata
  indicates a real fill (not pending-only). This is the strictest comparator
  for guards that might demote a winner.
- ``baseline_cand_rate``: current CAND rate per instrument for sanity checks.

All fixtures accept optional ``request.param`` overrides via ``pytest.mark.parametrize``
but default to last-30-days window across all 5 symbols.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path
from typing import Callable, Iterator, Optional

import pytest

# Make sure tests/replay/helpers is importable and src/ is on sys.path.
_REPLAY_DIR = Path(__file__).resolve().parent
if str(_REPLAY_DIR) not in sys.path:
    sys.path.insert(0, str(_REPLAY_DIR))

from tests.replay import helpers  # noqa: E402


# ---------------------------------------------------------------------------
# Marker registration (ensures `pytest -m replay` works even without
# pyproject.toml/pytest.ini entry). Also register the xfail marker for the
# known structural-bias bug.
# ---------------------------------------------------------------------------


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "replay: replay-based regression tests against live/historical data "
        "(no API cost; seconds-to-minutes runtime).",
    )


# ---------------------------------------------------------------------------
# Core fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def live_eval_rows() -> Callable[..., Iterator[dict]]:
    """Return a *factory* that yields live_evaluation rows.

    Usage::

        def test_something(live_eval_rows):
            for row in live_eval_rows(window_days=30, symbols=("XAUUSD",)):
                ...

    Each row is the raw ``evaluation_logger`` dict plus ``_source_file`` and
    ``_source_line``. Malformed rows are silently skipped (a one-line stderr
    summary is printed at the end).
    """

    def _factory(
        window_days: int = 30,
        symbols: Optional[tuple] = None,
    ) -> Iterator[dict]:
        return helpers.iter_live_eval_rows(
            window_days=window_days,
            symbols=symbols,
        )

    return _factory


@pytest.fixture
def trade_records() -> Callable[..., Iterator[dict]]:
    """Return a factory yielding full trade_record dicts.

    Each record includes ``_source_file`` and ``_candle_time_dt``. Records
    that fail to parse or lack a timestamp are skipped.
    """

    def _factory(
        window_days: int = 30,
        symbols: Optional[tuple] = None,
        require_mso: bool = False,
    ) -> Iterator[dict]:
        return helpers.iter_trade_records(
            window_days=window_days,
            symbols=symbols,
            require_mso=require_mso,
        )

    return _factory


@pytest.fixture
def historical_fills(trade_records) -> list[dict]:
    """Materialized list of trade_records that represent actual fills.

    Small (typically <20 in April 2026), so materializing is fine.
    """
    return [r for r in trade_records(window_days=30) if helpers.is_historical_fill(r)]


@pytest.fixture
def baseline_cand_rate(live_eval_rows) -> dict[str, float]:
    """Current CAND rate per instrument, as a fraction (0.0 – 1.0).

    Uses the last 30 days of live_evaluations. Returned map is keyed by
    symbol. Used by demotion-rate tests as a comparator.
    """
    totals: Counter = Counter()
    cands: Counter = Counter()
    for row in live_eval_rows(window_days=30):
        sym = row.get("symbol") or ""
        if not sym:
            continue
        totals[sym] += 1
        if row.get("decision") == "CANDIDATE":
            cands[sym] += 1
    return {
        sym: (cands[sym] / totals[sym]) if totals[sym] else 0.0
        for sym in totals
    }


@pytest.fixture
def replay_config() -> dict:
    """Load live ``config/agent_config.yaml`` and overlay replay-safe defaults.

    Using the live config means Gate 1/3 replays run with the SAME thresholds
    as production, so ``test_decision_invariance`` catches real drift. We
    then overlay a few keys that only make sense in a synthetic run (force
    pre_ai_gates on, disable log writes, fix deployment.phase=3).

    Tests that need a specific override should call
    ``helpers.make_config({...})`` directly for clarity.
    """
    import yaml

    cfg_path = helpers.repo_root() / "config" / "agent_config.yaml"
    if cfg_path.exists():
        with cfg_path.open(encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    else:
        cfg = {}

    # Replay-safe overlays — these don't vary between live and test.
    overlays = {
        "deployment": {"phase": 3},
        "pre_ai_gates": {"h1_poi_availability_enabled": True},
        "verification": {"enabled": True, "log_warnings": False},
        "gate1": {"sl_liquidity_cluster_enabled": False},  # log-only in live
    }
    helpers._deep_merge(cfg, overlays)
    return cfg


@pytest.fixture
def mock_mt5():
    """A minimal mt5 stand-in that satisfies Gate 3 connectivity + spread."""
    return helpers.MockMT5()


@pytest.fixture(autouse=True)
def _silence_shadow_log_writes(monkeypatch):
    """Monkeypatch out the two permissions shadow-log writers.

    Tests that call ``check_permissions`` trigger the sl-liquidity-cluster
    shadow logger, which tries to append to ``shadow_logs/`` — blocked by
    the repo-wide conftest write-guard. The call is wrapped in try/except
    in production, so blocking produces a warning per call but doesn't fail.
    This replaces both writers with no-ops for the duration of each replay
    test to keep stderr clean.

    The production code path is exercised in ``tests/test_permissions.py``
    already; here we only care about gate DECISIONS, not the shadow-log
    side effect.
    """
    import src.components.permissions as perm

    def _noop(*args, **kwargs):  # noqa: ARG001
        return None

    monkeypatch.setattr(perm, "_log_liquidity_distance", _noop, raising=False)
    monkeypatch.setattr(perm, "_log_inverted_tp", _noop, raising=False)
    yield


# ---------------------------------------------------------------------------
# H1 rolling-window fixture (for structure-detector tests)
# ---------------------------------------------------------------------------


@pytest.fixture
def h1_windows():
    """Factory yielding 168-bar H1 windows from historical_2026 CSVs.

    Usage::

        def test_whatever(h1_windows):
            for window in h1_windows("XAUUSD", step=24):
                ...

    Defaults: window=168 bars (~1 week of H1), step=24 bars (~1 day).
    """

    def _factory(
        symbol: str = "XAUUSD",
        window: int = 168,
        step: int = 24,
    ):
        bars = helpers.load_ohlcv_csv(symbol, "H1")
        return helpers.rolling_windows(bars, window=window, step=step)

    return _factory
