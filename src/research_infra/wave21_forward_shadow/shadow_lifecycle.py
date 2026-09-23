"""Causal would-be-order lifecycle tracking for the forward-shadow lane.

Outcomes are MODELLED, and labeled as such: the tracker runs the exact research
lifecycle resolver (`src.research_infra.walkforward.quote_side.
resolve_post_submission_m1_lifecycle`) — the same M1 logic class, quote-side
transform, spread model, and censoring rules the frozen funnel's labels were
built from (`candidate_funnel_analysis._lifecycle_row`) — over closed M1 bars
fetched forward.  No broker fill, no order, no position is involved anywhere.

Causality: at each cycle the tracker sees only bars closed so far.  A truncated
probe (horizon = last witnessed M1 open) may resolve early ONLY on bar-local
verdicts (target/stop hit, ordering ambiguity, geometry/authority censors) —
verdicts later bars cannot change.  Everything else stays PENDING until the M1
stream covers the order's full expiry horizon, at which point the resolver runs
exactly as the research labeler would and its verdict is FINAL.
"""

from __future__ import annotations

import bisect
import dataclasses
import hashlib
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.components.ultimate_book.primitives import Bar
from src.costs.spread_model import load_spread_model
from src.research_infra.walkforward.quote_side import (
    BarQuote,
    resolve_post_submission_m1_lifecycle,
    spread_for,
)

EVIDENCE_CLASS = "forward_shadow_modelled_m1_lifecycle_not_broker_realized"

# Statuses a truncated (pre-horizon) probe may finalize: bar-local or
# input-local verdicts that additional future bars cannot change.
_EARLY_FINAL_STATUSES = frozenset(
    {
        "RESOLVED_FILLED_TARGET",
        "RESOLVED_FILLED_STOP",
        "CENSORED_SUBMISSION_BAR_LIMIT_TOUCH_ORDERING",
        "CENSORED_ORDERING_AMBIGUITY",
        "CENSORED_GEOMETRY",
        "CENSORED_SPREAD_OR_SPEC_AUTHORITY",
        "CENSORED_INVALID_GAP_THROUGH_SL_OR_TP",
    }
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SPEC_PATH = _REPO_ROOT / "src/costs/SYMBOL_AUTHORITY_V1.json"

_spec_sha256: str | None = None
_spread_sha256: str | None = None


def _authority_hashes() -> tuple[str, str]:
    global _spec_sha256, _spread_sha256
    if _spec_sha256 is None:
        _spec_sha256 = hashlib.sha256(_SPEC_PATH.read_bytes()).hexdigest()
    if _spread_sha256 is None:
        _spread_sha256 = load_spread_model().artifact_sha256
    return _spec_sha256, _spread_sha256


@dataclasses.dataclass
class WouldBeOrder:
    """One selected would-be trade being tracked to its modelled terminal.

    ``lanes`` records which selection lane(s) chose it: ``general`` (the full
    rule) and/or ``scoped_lsr`` (the same rule restricted to the
    ``liquidity_sweep_reclaim`` family — the bar-3-ratified primary deployable
    object).  One shared modelled lifecycle serves both lanes; occupancy is
    tracked per lane by the runner.
    """

    candidate_occurrence_key: str
    decision_window_id: str
    trading_day: str
    symbol: str
    side: str
    proposed_order_type: str
    submission_utc: datetime
    expiry_utc: datetime
    entry_price: float
    stop_loss: float
    take_profit_1: float
    deductible_cost_r: float
    predicted_net_r: float
    cost_r: float
    origin_family: str = ""
    lanes: tuple[str, ...] = ("general",)

    @property
    def direction(self) -> int:
        return 1 if self.side.upper() == "LONG" else -1

    @property
    def risk(self) -> float:
        return abs(self.entry_price - self.stop_loss)

    def to_json(self) -> dict[str, Any]:
        payload = dataclasses.asdict(self)
        payload["submission_utc"] = self.submission_utc.isoformat()
        payload["expiry_utc"] = self.expiry_utc.isoformat()
        payload["lanes"] = list(self.lanes)
        return payload

    @classmethod
    def from_json(cls, payload: Mapping[str, Any]) -> "WouldBeOrder":
        data = dict(payload)
        for key in ("submission_utc", "expiry_utc"):
            value = datetime.fromisoformat(str(data[key]).replace("Z", "+00:00"))
            if value.tzinfo is None:
                raise ValueError(f"naive {key} in persisted would-be order")
            data[key] = value.astimezone(timezone.utc)
        if "lanes" in data:
            data["lanes"] = tuple(str(lane) for lane in data["lanes"])
        known = {field.name for field in dataclasses.fields(cls)}
        return cls(**{key: value for key, value in data.items() if key in known})


def spread_series(
    symbol: str,
    times: Sequence[datetime],
    *,
    cache: dict[tuple[str, datetime], float] | None = None,
) -> list[float]:
    """Hour-cached research spread model series, exactly as the labelers build it."""

    cache = cache if cache is not None else {}
    out: list[float] = []
    for instant in times:
        hour = instant.replace(minute=0, second=0, microsecond=0)
        key = (symbol, hour)
        if key not in cache:
            cache[key] = spread_for(symbol, hour, account="FTMO", band="mid")
        out.append(cache[key])
    return out


def resolve_would_be_order(
    order: WouldBeOrder,
    *,
    m1_times: Sequence[datetime],
    m1_bars: Sequence[Bar],
    spreads: Sequence[float],
    now_utc: datetime,
) -> dict[str, Any]:
    """Probe/finalize one order against the closed M1 bars seen so far.

    Returns a status dict; ``final`` False means keep tracking.  The window
    slice mirrors ``candidate_funnel_analysis._lifecycle_row``: start one bar
    before submission, end one bar past the boundary.
    """

    spec_sha, spread_sha = _authority_hashes()
    submission, expiry = order.submission_utc, order.expiry_utc
    if len(m1_times) != len(m1_bars) or len(spreads) != len(m1_bars):
        raise ValueError("m1 stream misaligned")

    full_coverage = bool(m1_times) and m1_times[-1] >= expiry
    boundary = expiry if full_coverage else (m1_times[-1] if m1_times else None)
    if boundary is None or boundary <= submission:
        return {
            "final": False,
            "phase": "pending_no_causal_m1_yet",
            "lifecycle_label_status": None,
        }

    start = max(0, bisect.bisect_right(m1_times, submission) - 1)
    end = min(len(m1_times), bisect.bisect_left(m1_times, boundary) + 1)
    lifecycle = resolve_post_submission_m1_lifecycle(
        m1_bars[start:end],
        m1_open_times_utc=m1_times[start:end],
        direction=order.direction,
        proposed_order_type=order.proposed_order_type,
        submission_or_ack_time_utc=submission,
        expiry_utc=boundary,
        required_horizon_utc=boundary,
        approved_entry_price=order.entry_price,
        approved_stop_price=order.stop_loss,
        approved_target_price=order.take_profit_1,
        approved_risk_distance=order.risk,
        m1_price_basis=BarQuote.BID,
        spread_by_bar=spreads[start:end],
        source_interval_verified=True,
        symbol_spec_hash_sha256=spec_sha,
        spread_source_hash_sha256=spread_sha,
    )
    status = lifecycle.lifecycle_label_status
    final = full_coverage or status in _EARLY_FINAL_STATUSES
    if not final:
        return {
            "final": False,
            "phase": "pending_truncated_probe",
            "lifecycle_label_status": status,
            "probe_boundary_utc": boundary.isoformat(),
        }

    # Final mapping — verbatim from candidate_funnel_analysis._lifecycle_row.
    if status == "RESOLVED_NO_FILL":
        cost_status, gross, net, label_end = ("NOT_APPLICABLE_NO_FILL", None, None, expiry)
    elif status.startswith("RESOLVED_FILLED_"):
        gross = float(lifecycle.terminal_gross_r)
        cost_status, net = "COMPLETE", gross - order.deductible_cost_r
        label_end = datetime.fromisoformat(str(lifecycle.terminal_time_utc))
    else:
        cost_status, gross, net, label_end = (
            "INCOMPLETE_OTHER_EXPLICIT_REASON",
            None,
            None,
            None,
        )
    occupancy_end = label_end if label_end is not None else expiry
    resolved_early = full_coverage is False
    result = {
        "final": True,
        "phase": "final_early_bar_local" if resolved_early else "final_full_horizon",
        "evidence_class": EVIDENCE_CLASS,
        "lifecycle_label_status": status,
        "cost_label_status": cost_status,
        "terminal_state": lifecycle.terminal_state,
        "terminal_time_utc": lifecycle.terminal_time_utc,
        "terminal_gross_r": gross,
        "terminal_net_r": net,
        "deductible_cost_r": order.deductible_cost_r,
        "censor_reason": lifecycle.censor_reason,
        "modelled_fill_time_utc": lifecycle.modelled_fill_time_utc,
        "modelled_fill_price": lifecycle.modelled_fill_price,
        "label_span_start_utc": submission.isoformat(),
        "label_span_end_utc": label_end.isoformat() if label_end else None,
        "occupancy_end_utc": occupancy_end.isoformat(),
        "resolved_at_utc": now_utc.isoformat(),
        "symbol_spec_hash_sha256": spec_sha,
        "spread_source_hash_sha256": spread_sha,
    }
    if not math.isfinite(order.risk) or order.risk <= 0:
        result["geometry_note"] = "non_positive_risk_at_tracking"
    return result
