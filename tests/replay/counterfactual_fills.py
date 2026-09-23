"""Counterfactual fills harness.

For each historical fill (trade_record with execution metadata + recorded
outcome), replay the proposed pipeline change and assert the simulated
outcome matches the actual one.

"Fill" here strictly means an executed broker fill — not a pending limit
order that expired. In April 2026 the live fleet produced a small number
of real fills; the harness exposes them through ``load_historical_fills()``
so counterfactual tests can iterate.

Scope
-----
Use this for PRs that modify any code path between CAND production and
fill:
  - Post-AI guards (``primary_analyzer.guard_candidate_*``)
  - Permissions / verification
  - M5 refinement
  - Execution parameter transforms (e.g. SL buffer scaling)

Non-scope: changes that only affect post-fill management (partial close,
trailing stop) — the harness currently replays CAND→fill, not fill→exit.

How to use
----------
.. code-block:: python

    from tests.replay.counterfactual_fills import (
        CounterfactualFill, run_counterfactual,
    )

    def my_pipeline(pa, mso, config):
        pa = my_new_guard(pa)
        return pa  # or return None to signal "guard would have blocked"

    for fill in load_historical_fills():
        result = run_counterfactual(fill, pipeline_fn=my_pipeline, config=cfg)
        assert result.outcome_changed is False

Design note: the harness stops short of simulating price paths post-entry
because we don't have tick data. It only answers "would this CAND still
have reached the fill-able CANDIDATE state after the pipeline change?" —
that is the high-signal question for pre-fill PRs.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Literal, Optional

import pytest

from src.components.permissions import check_permissions
from src.components.verification import verify_candidate
from src.models.analysis_models import PrimaryAnalysisOutput
from tests.replay import helpers


pytestmark = pytest.mark.replay


OutcomeType = Literal["tp_hit", "sl_hit", "be_hit", "force_close", "broker_close", "unknown"]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class CounterfactualFill:
    """A single historical fill with reconstruction data."""
    trade_id: str
    symbol: str
    kill_zone: str
    candle_time: str
    entry: float
    sl: float
    tp1: float
    direction: Literal["LONG", "SHORT"]
    actual_outcome: OutcomeType
    actual_r: float
    pa: Optional[PrimaryAnalysisOutput]
    mso: Optional[object]  # MarketStateObject; typed loosely for test helpers
    record: dict = field(repr=False)

    @classmethod
    def from_record(cls, rec: dict) -> Optional["CounterfactualFill"]:
        pa = helpers.reconstruct_pa(rec)
        mso = helpers.reconstruct_mso(rec)
        if pa is None or pa.trade_parameters is None:
            return None
        tp = pa.trade_parameters
        outcome = helpers.outcome_of(rec) or "unknown"
        return cls(
            trade_id=(rec.get("metadata") or {}).get("trade_id", "?"),
            symbol=(rec.get("metadata") or {}).get("symbol", "?"),
            kill_zone=(rec.get("metadata") or {}).get("kill_zone", "?"),
            candle_time=(rec.get("metadata") or {}).get("candle_time", ""),
            entry=tp.entry_price,
            sl=tp.stop_loss,
            tp1=tp.take_profit_1,
            direction=tp.direction,
            actual_outcome=outcome,  # type: ignore[arg-type]
            actual_r=helpers.r_multiple_of(rec) or 0.0,
            pa=pa,
            mso=mso,
            record=rec,
        )


@dataclass
class CounterfactualResult:
    """Outcome of replaying one fill through a modified pipeline."""
    fill: CounterfactualFill
    would_reach_fill: bool
    blocked_by: Optional[str] = None
    blocked_detail: Optional[str] = None

    @property
    def outcome_changed(self) -> bool:
        """True if the pipeline would have prevented the fill from happening."""
        return not self.would_reach_fill


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def load_historical_fills(window_days: int = 30) -> list[CounterfactualFill]:
    """Return all reconstructible CounterfactualFill objects within ``window_days``.

    A record qualifies as a fill when ``helpers.is_historical_fill`` returns
    True. Records that fail Pydantic reconstruction are dropped with a stderr
    warning summary.
    """
    fills: list[CounterfactualFill] = []
    dropped = 0
    for rec in helpers.iter_trade_records(window_days=window_days, require_mso=True):
        if not helpers.is_historical_fill(rec):
            continue
        cf = CounterfactualFill.from_record(rec)
        if cf is None:
            dropped += 1
            continue
        fills.append(cf)
    if dropped:
        print(f"[counterfactual_fills] dropped {dropped} fills — reconstruction failed")
    return fills


# ---------------------------------------------------------------------------
# Replay pipeline primitives
# ---------------------------------------------------------------------------


def current_pipeline(pa: PrimaryAnalysisOutput, mso, config: dict) -> Optional[PrimaryAnalysisOutput]:
    """Identity pipeline: run the unmodified current code path end-to-end.

    Applies verify_candidate → check_permissions. Returns the PA unchanged on
    success; returns None if the pipeline would have blocked the fill.

    Matches the live order in orchestrator._handle_primary_analysis:
      1. L2 verification (verify_candidate)
      2. Gate 0/1/3 permissions (check_permissions)
    """
    # L2 verification
    v_result = verify_candidate(pa, mso, config)
    if not v_result.passed:
        return None

    # Gate 0/1/3 permissions
    session_state = {
        "daily_pnl_pct": 0.0,
        "deterministic_bias": pa.reasoning.daily_bias.direction if pa.reasoning else "",
    }
    mt5 = helpers.MockMT5()
    denial = check_permissions(pa, mso, session_state, mt5,
                               config=config, symbol="XAUUSD")
    if denial is not None:
        return None

    return pa


def run_counterfactual(
    fill: CounterfactualFill,
    pipeline_fn: Callable[[PrimaryAnalysisOutput, object, dict], Optional[PrimaryAnalysisOutput]] = None,
    config: Optional[dict] = None,
) -> CounterfactualResult:
    """Replay one fill through ``pipeline_fn`` and report whether the fill
    would still have been reachable.

    ``pipeline_fn`` receives ``(pa, mso, config)`` and must return either
    the PA (possibly modified) if the fill would still happen, or None if
    the pipeline would have blocked the trade. Default: ``current_pipeline``.
    """
    pipeline_fn = pipeline_fn or current_pipeline
    config = config or helpers.make_config()
    if fill.pa is None or fill.mso is None:
        return CounterfactualResult(
            fill=fill, would_reach_fill=False,
            blocked_by="reconstruction_failed",
        )
    try:
        result = pipeline_fn(fill.pa, fill.mso, config)
    except Exception as e:  # noqa: BLE001
        return CounterfactualResult(
            fill=fill, would_reach_fill=False,
            blocked_by="pipeline_crashed",
            blocked_detail=f"{e!r}",
        )
    if result is None:
        return CounterfactualResult(
            fill=fill, would_reach_fill=False,
            blocked_by="pipeline_rejected",
        )
    if result.decision != "CANDIDATE":
        return CounterfactualResult(
            fill=fill, would_reach_fill=False,
            blocked_by="decision_demoted",
            blocked_detail=result.decision,
        )
    return CounterfactualResult(fill=fill, would_reach_fill=True)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCounterfactualFills:
    """Smoke test: current pipeline should replay every fill as-is.

    If this fails, the replay harness itself is broken — every fill that
    reached production must still survive the unchanged current pipeline.
    """

    def test_current_pipeline_preserves_all_fills(self):
        fills = load_historical_fills(window_days=30)
        if not fills:
            pytest.skip(
                "No historical fills in the 30-day window. April 2026 LIVE "
                "activity produced LIMIT_PLACED orders that didn't fill — "
                "widen the window or wait for fills to accrue."
            )
        config = helpers.make_config()
        changed: list[CounterfactualResult] = []
        for fill in fills:
            result = run_counterfactual(fill, pipeline_fn=current_pipeline,
                                        config=config)
            if result.outcome_changed:
                changed.append(result)

        print(
            f"\n[counterfactual/current_pipeline] fills={len(fills)} "
            f"preserved={len(fills) - len(changed)} changed={len(changed)}"
        )
        for r in changed[:5]:
            print(f"  - {r.fill.trade_id}: {r.blocked_by} ({r.blocked_detail})")
        assert not changed, (
            "Replay harness broken: current pipeline rejects fills that "
            "reached production. Review verify_candidate / check_permissions "
            "against the recorded pipeline — a config mismatch is most likely."
        )

    def test_all_historical_fills_have_reconstructible_data(self):
        """Sanity check: each fill's PA + MSO reconstructs from JSON."""
        fills = load_historical_fills(window_days=30)
        if not fills:
            pytest.skip("No fills in window")
        bad = [f for f in fills if f.pa is None or f.mso is None]
        assert not bad, (
            f"{len(bad)} fills have missing/malformed PA or MSO. "
            "The schema may have drifted — inspect "
            "``tests/replay/helpers.py::reconstruct_pa/reconstruct_mso``."
        )
