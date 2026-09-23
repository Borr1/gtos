"""Frozen MARKET-top-abstain selection for the forward-shadow lane.

Mirrors the committed February r2 scorer's ``select(..., policy=
"market_top_abstain")`` exactly, applied causally to one live decision window:

  * rank scope: every geometry-valid candidate with finite complete pretrade
    cost <= 0.2R whose symbol is not occupied;
  * rank: predicted net R desc, cost R asc, candidate occurrence key desc;
  * minimum predicted net R 0.1 — below it, no trade for the window;
  * if the single top candidate is LIMIT, ABSTAIN — never substitute a
    lower-ranked MARKET candidate;
  * one trade per decision window; a selected candidate occupies its symbol
    until its causal terminal or expiry (tracked by the shadow's own lifecycle
    state, since the future is not readable here).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Sequence

from src.research_infra.wave21_forward_shadow.feature_contract import (
    MIN_EXPECTED_NET_R,
    at_utc,
)


def prune_occupancy(
    active: Mapping[str, datetime], decision_at: datetime
) -> dict[str, datetime]:
    """Research semantics: occupied while ``end > decision_at`` (strict)."""

    return {symbol: end for symbol, end in active.items() if end > decision_at}


def select_market_top_abstain(
    rows: Sequence[Mapping[str, Any]],
    predictions: Sequence[float],
    *,
    active: Mapping[str, datetime],
    decision_at: datetime,
) -> tuple[dict[str, Any] | None, dict[str, int], dict[str, datetime]]:
    """Apply the frozen rule to one window's eligible rows.

    Returns ``(chosen_row_or_None, dispositions, pruned_active)``.  The caller
    owns occupancy state; on a trade it must register the chosen symbol with
    its expiry upper bound and later tighten it to the causal terminal.
    Disposition keys are the r2 scorer's: ``no_available_candidate``,
    ``top_below_0p10``, ``top_limit_abstain``, ``trade``.
    """

    if len(rows) != len(predictions):
        raise ValueError("rows/predictions length mismatch")
    pruned = prune_occupancy(active, decision_at)
    dispositions: dict[str, int] = {}

    available = [
        (float(prediction), -float(row["cost_r"]), row["candidate_occurrence_key"], row)
        for prediction, row in zip(predictions, rows)
        if row["symbol"] not in pruned
    ]
    if not available:
        dispositions["no_available_candidate"] = 1
        return None, dispositions, pruned
    prediction, _neg_cost, _key, row = max(available, key=lambda item: item[:3])
    if prediction < MIN_EXPECTED_NET_R:
        dispositions["top_below_0p10"] = 1
        return None, dispositions, pruned
    if row["proposed_order_type"] != "MARKET":
        dispositions["top_limit_abstain"] = 1
        return None, dispositions, pruned
    dispositions["trade"] = 1
    chosen = dict(row, predicted_net_r=float(prediction))
    return chosen, dispositions, pruned


def occupancy_end_for_selection(row: Mapping[str, Any]) -> datetime:
    """Upper bound at selection time: the expiry (label span not resolved yet).

    Mirrors ``at(row["label_span_end_utc"] or row["expiry_utc"])`` with
    ``label_span_end_utc`` still None at decision time.  The lifecycle tracker
    tightens this to the causal terminal when the modelled order resolves.
    """

    return at_utc(row["expiry_utc"])
