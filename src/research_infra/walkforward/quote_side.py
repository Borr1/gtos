"""The side of the book — the one correction every walker in this estate was missing.

WHY THIS EXISTS
---------------
Every bar archive on this machine is **BID** on open, high, low and close. Not inferred:

* `vps-bars-20260727` M15 — **87,060 bars, 33 symbols**, `close == last tick bid` at
  1.00000 on every symbol, `(close - mid)/spread = -0.500000` with a cross-symbol range of
  exactly [-0.5, -0.5], `high == max(bid)` and `low == min(bid)` at zero spreads of error.
* the true-UTC M1 packs (`bridge_ftmo_m1_*`) — **820,452 bars, 4 symbols x 7 months**,
  the same three identities at 1.000000, measured against a different tick hold on a
  different clock.

  (Receipts: `phase20/receipts/r1/R1_QUOTESIDE_M15_V1.json`,
  `R1_QUOTESIDE_M1_V1.json`. Corroborates d8x §2 and p3 §4.1 with independent code.)

A round trip transacts on **both** sides. Every walker in this estate resolved entries,
stops and targets against that one-sided tape with unshifted levels — the outcome of a
trader quoted the bid on both legs, who does not exist. Sized over the live sleeve estate
in `phase20/receipts/r1/R1_ESTATE_DELTA_V1.json` — see `SESSION_R1_QUOTE_SIDE_WALKER.md`
for the per-sleeve table and the verdict consequences.

**And the popular framing of the defect is wrong.** It is *not* "the tape is bid where it
should be mid". A MID tape is optimistic by exactly the same amount: what is missing is
that the round trip crosses the spread at all, and the crossing costs one full spread from
whichever side the tape is quoted on. `test_anchor_is_bar_quote_invariant` pins that.

THE CONVENTION, DERIVED — and where the live book proves each row
-----------------------------------------------------------------
Every row below is what the LIVE engine does, cited, not what a textbook says.

| leg                                   | you    | quote side | live proof                        |
|---------------------------------------|--------|------------|-----------------------------------|
| LONG entry, at market                 | buy    | **ASK**    | `execution.py:3247`               |
| SHORT entry, at market                | sell   | **BID**    | `execution.py:3247`               |
| LONG entry, pending at a level        | buy    | **ASK**    | `execution.py:6197`               |
| SHORT entry, pending at a level       | sell   | **BID**    | `execution.py:6197`               |
| LONG stop-loss / take-profit          | sell   | **BID**    | `execution.py:6953`, `:9213`      |
| SHORT stop-loss / take-profit         | buy    | **ASK**    | `execution.py:6953`, `:9213`      |
| LONG trail / scale-out / time stop    | sell   | **BID**    | `execution.py:6953` (the price     |
| SHORT trail / scale-out / time stop   | buy    | **ASK**    |  every management overlay reads)   |

    execution.py:3247   entry_price  = tick.ask if direction == "LONG" else tick.bid
    execution.py:6197   current_price= tick.ask if intent.direction == "LONG" else tick.bid
    execution.py:6953   current_price= tick.bid if trade.direction == "LONG" else tick.ask
    execution.py:9213   current      = tick.bid if ...direction == "LONG" else tick.ask

WHERE THE LEVELS HANG — the question that decides the whole correction
-----------------------------------------------------------------------
Two anchorings are possible and they give different answers, so it is measured rather
than assumed. The live W7 book is **fill-anchored**:

    order_router.py:66   entry = float(ask if d > 0 else bid)   # cross the spread on entry
    order_router.py:73   "stop_loss": entry - sign * rd,
                         "take_profit_1": entry + sign * target_dist
    execution_packets.py:566-569   stop_loss      = entry_price - sign * risk_distance
                                   take_profit_1  = entry_price + sign * final_target_r * risk_distance
    execution.py:3260              sl_distance    = abs(entry_price - sl)   # the R unit

So the book crosses the spread and then hangs BOTH exit legs off the crossed price, and
sizes on the crossed distance. Consequences, all exact:

* R at the stop is **-1** and at the target **+T**. The R *levels* do not move.
* What moves is the tape distance to them: **the stop is one spread NEARER and the target
  one spread FURTHER**, on both sides of the market. It is a *resolution* error, and no
  cost term applied afterwards can undo it — a trade booked as reaching target may in
  truth have stopped first.
* Every close-based exit (time stop, maxbars, rollover flat) is charged exactly one
  spread, because it transacts at the tape close on the wrong side.

`LevelAnchor.LEVEL` is the other case — a generator that emits absolute structural levels
and rests a pending order at one (the broad V4 family). There the R levels *do* shift and
the entry trigger displaces instead. Both are implemented; the default is FILL, because
that is what the armed book runs.

THE ENTIRE CORRECTION IS ONE NUMBER
------------------------------------
For a fill-anchored at-market trade on any tape:

    replay_anchor = bar_close + direction * spread

That single substitution into `exits.replay(..., entry_price=...)` is provably the whole
of it — stop, target, trail arm, trail fill, scale-out, time stop, maxbars, MFE and MAE
all follow correctly, because every one of them is measured from the anchor and every
fill lands on the trade's own exit-quote side. The derivation is in
`docs/audits/fable5-vision-audit-20260725/phase20/SESSION_R1_QUOTE_SIDE_WALKER.md` §2 and
each limb of it is pinned by a hand-computed test in
`tests/research_infra/test_quote_side.py`.

FAIL CLOSED
-----------
`spread_for` raises `SpreadUnavailable` rather than returning zero. A silent zero is the
defect this module exists to remove; re-introducing it as a fallback would make the repair
invisible exactly where the data is worst. Callers that want the old behaviour must pass
`spread=0.0` themselves, in the open.
"""

from __future__ import annotations

import datetime as dt
import math
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Sequence

from .exits import PLAIN, ExitPolicy, PathResult, replay

__all__ = [
    "BarQuote",
    "LevelAnchor",
    "M1ModelledLifecycleResult",
    "ObservedBookBars",
    "OrderedQuoteLifecycleResult",
    "ObservedQuoteSideTrade",
    "OrderedQuoteTicks",
    "QuoteTouch",
    "SpreadUnavailable",
    "TickPathResult",
    "QuoteSideTrade",
    "replay_anchor",
    "transacted_entry_price",
    "exit_quote_offset",
    "entry_trigger_level_on_tape",
    "first_resting_limit_touch",
    "resolve_post_submission_quote_lifecycle",
    "resolve_post_submission_m1_lifecycle",
    "replay_ticks",
    "spread_for",
    "walk",
    "walk_observed_book",
]


class BarQuote(Enum):
    """Which side of the book an OHLC archive is quoted on.

    Both archives on this machine are BID, measured. `MID` and `ASK` exist so a caller
    cannot express "I do not know" as BID by accident — there is no UNKNOWN member and
    the argument has no default at the module boundary.
    """

    BID = "bid"
    MID = "mid"
    ASK = "ask"


class LevelAnchor(Enum):
    """Where the stop and the target hang.

    FILL  — off the transacted entry price. The live W7 book (`order_router.py:66-73`).
    LEVEL — at absolute prices the generator emitted, independent of the fill.
    """

    FILL = "fill"
    LEVEL = "level"


class SpreadUnavailable(RuntimeError):
    """No defensible spread for this (symbol, account, instant). Never substitute zero."""


@dataclass(frozen=True)
class OrderedQuoteTicks:
    """One non-decreasing, uncrossed BID/ASK stream.

    Equal timestamps are allowed because MT5 can emit several stably ordered quotes in
    one millisecond. The sequence order remains authoritative; sorting inside an execution
    primitive would silently rewrite which quote touched first.
    """

    times: Sequence[Any]
    bids: Sequence[float]
    asks: Sequence[float]

    def __post_init__(self) -> None:
        n = len(self.times)
        if not (n == len(self.bids) == len(self.asks)):
            raise ValueError(
                "times, bids and asks must have equal lengths: "
                f"got {n}, {len(self.bids)}, {len(self.asks)}"
            )
        if n == 0:
            raise ValueError("an ordered quote stream cannot be empty")
        previous: Any = None
        for k in range(n):
            at = self.times[k]
            if isinstance(at, dt.datetime):
                if at.tzinfo is None or at.utcoffset() is None:
                    raise ValueError(f"tick {k} has a naive datetime: {at!r}")
            else:
                if isinstance(at, (str, bytes, bytearray)):
                    raise ValueError(
                        f"tick {k} timestamp strings are forbidden; decode to a numeric "
                        f"instant or timezone-aware datetime before ordering: {at!r}"
                    )
                try:
                    if not math.isfinite(float(at)):
                        raise ValueError(f"tick {k} has a non-finite timestamp: {at!r}")
                except (TypeError, ValueError) as exc:
                    if isinstance(exc, ValueError) and "non-finite" in str(exc):
                        raise
                    raise ValueError(
                        f"tick {k} timestamp must be numeric or timezone-aware datetime, got {at!r}"
                    ) from exc
            if k:
                try:
                    backwards = at < previous
                except TypeError as exc:
                    raise ValueError(
                        f"tick timestamps are not mutually comparable at {k - 1}/{k}: "
                        f"{previous!r}, {at!r}"
                    ) from exc
                if backwards:
                    raise ValueError(
                        f"ticks are not ordered at {k - 1}/{k}: {previous!r} > {at!r}"
                    )
            bid = float(self.bids[k])
            ask = float(self.asks[k])
            if not (math.isfinite(bid) and math.isfinite(ask) and bid > 0 and ask > 0):
                raise ValueError(f"tick {k} has invalid bid/ask: {bid!r}/{ask!r}")
            if ask < bid:
                raise ValueError(f"tick {k} is crossed: bid={bid!r} ask={ask!r}")
            previous = at


@dataclass(frozen=True)
class QuoteTouch:
    """The first correct-side quote that makes a resting order touch-eligible.

    This is not a broker fill claim. BID/ASK ticks contain no queue position, available
    depth, order acknowledgement, or execution event.
    """

    index: int
    at: Any
    bid: float
    ask: float
    price: float

    def as_dict(self) -> dict[str, Any]:
        at = self.at.isoformat() if isinstance(self.at, dt.datetime) else self.at
        return {
            "index": self.index,
            "at": at,
            "bid": self.bid,
            "ask": self.ask,
            "price": self.price,
        }


@dataclass(frozen=True)
class TickPathResult:
    """An exit resolved from ordered executable quotes, with no intrabar inference."""

    r_gross: float
    exit_index: int
    exit_at: Any
    exit_price: float
    exit_reason: str
    mfe_r: float
    mae_r: float
    ticks_held: int
    detail: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        at = self.exit_at.isoformat() if isinstance(self.exit_at, dt.datetime) else self.exit_at
        return {
            "r_gross": self.r_gross,
            "exit_index": self.exit_index,
            "exit_at": at,
            "exit_price": self.exit_price,
            "exit_reason": self.exit_reason,
            "mfe_r": self.mfe_r,
            "mae_r": self.mae_r,
            "ticks_held": self.ticks_held,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class OrderedQuoteLifecycleResult:
    """Quote-only order lifecycle with broker execution deliberately unresolved."""

    measurement_status: str
    modelled_lifecycle_status: str
    post_scheduler_order_type: str
    direction: int
    submission_or_ack_time_utc: str
    required_horizon_utc: str
    coverage_status: str
    activation_class: str | None
    first_causal_quote_index: int | None
    first_causal_quote_at: str | None
    first_causal_quote_side: str
    first_causal_quote_price: float | None
    correct_side_touch_eligible: bool | None
    correct_side_touch_index: int | None
    correct_side_touch_at: str | None
    modelled_entry_index: int | None
    modelled_entry_at: str | None
    modelled_entry_price: float | None
    approved_risk_distance: float
    stop_r: float | None
    target_r: float | None
    terminal_outcome: str | None
    terminal_at: str | None
    terminal_price: float | None
    terminal_r: float | None
    source_gaps: tuple[str, ...]
    detail: dict[str, Any]
    broker_fill_status: str = "NOT_EVALUABLE"
    broker_fill_claimed: bool = False
    claim_class: str = (
        "ORDERED_QUOTE_MODEL_NOT_BROKER_ORDER_QUEUE_DEAL_OR_POSITION_TRUTH"
    )

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class M1ModelledLifecycleResult:
    """One M1-modelled lifecycle label, never a broker fill claim.

    Times attached to intrabar events are conservative interval-close upper bounds;
    exact within-bar ordering is deliberately not invented.  The immutable proposed
    order geometry is echoed so a downstream label row can prove which denominator and
    boundaries were used.
    """

    lifecycle_label_status: str
    proposed_order_type: str
    modelled_fill_bar_index: int | None
    modelled_fill_time_utc: str | None
    modelled_fill_price: float | None
    terminal_state: str | None
    terminal_bar_index: int | None
    terminal_time_utc: str | None
    terminal_price: float | None
    terminal_gross_r: float | None
    censor_reason: str | None
    detail: dict[str, Any]
    evidence_class: str = "ALL24_M1_MODELLED_LIFECYCLE_NOT_BROKER_FILL"
    broker_fill_status: str = "NOT_EVALUABLE"
    broker_fill_claimed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ObservedBookBars:
    """Index-aligned BID and ASK OHLC built from the same ordered quote intervals."""

    bid: Sequence[Any]
    ask: Sequence[Any]

    def __post_init__(self) -> None:
        if len(self.bid) != len(self.ask):
            raise ValueError(
                f"bid/ask bar counts differ: {len(self.bid)} != {len(self.ask)}"
            )
        if len(self.bid) == 0:
            raise ValueError("an observed BID/ASK bar path cannot be empty")
        for k, (bb, ab) in enumerate(zip(self.bid, self.ask)):
            bv = tuple(float(getattr(bb, x)) for x in ("o", "h", "l", "c"))
            av = tuple(float(getattr(ab, x)) for x in ("o", "h", "l", "c"))
            if not all(math.isfinite(x) and x > 0 for x in bv + av):
                raise ValueError(f"bar {k} has non-finite/non-positive BID or ASK OHLC")
            for side, (o, h, l, c) in (("bid", bv), ("ask", av)):
                if h < max(o, c) or l > min(o, c) or h < l:
                    raise ValueError(
                        f"bar {k} has invalid {side} OHLC: o={o} h={h} l={l} c={c}"
                    )
            for field, bpx, apx in zip(("open", "high", "low", "close"), bv, av):
                if apx < bpx:
                    raise ValueError(
                        f"bar {k} has crossed {field}: bid={bpx!r} ask={apx!r}"
                    )


# --------------------------------------------------------------- quote geometry


def _side_offset(bar_quote: BarQuote, side: str, spread: float) -> float:
    """`side` price minus the tape, for one bar quote. `side` in {"bid","ask"}."""
    if spread < 0:
        raise ValueError(f"spread must be >= 0, got {spread!r}")
    if side not in ("bid", "ask"):
        raise ValueError(f"side must be 'bid' or 'ask', got {side!r}")
    if bar_quote is BarQuote.BID:
        return 0.0 if side == "bid" else spread
    if bar_quote is BarQuote.ASK:
        return -spread if side == "bid" else 0.0
    return -spread / 2.0 if side == "bid" else spread / 2.0


def exit_quote_offset(direction: int, bar_quote: BarQuote, spread: float) -> float:
    """Exit-trigger price minus the tape, for this direction.

    A LONG's stop and target are compared against the BID, a SHORT's against the ASK
    (`execution.py:6953`). This is the number that says how far a tape reading is from
    the price the broker is actually watching.
    """
    _check_direction(direction)
    return _side_offset(bar_quote, "bid" if direction > 0 else "ask", spread)


def entry_quote_offset(direction: int, bar_quote: BarQuote, spread: float) -> float:
    """Entry-transaction price minus the tape (`execution.py:3247`, `:6197`)."""
    _check_direction(direction)
    return _side_offset(bar_quote, "ask" if direction > 0 else "bid", spread)


def _check_direction(direction: int) -> None:
    if direction not in (1, -1):
        raise ValueError(f"direction must be +1 or -1, got {direction!r}")


def transacted_entry_price(
    bar_close: float, direction: int, spread: float, bar_quote: BarQuote
) -> float:
    """What an at-market order sent at this bar's close actually pays or receives.

    LONG pays the ask, SHORT receives the bid — `execution.py:3247`.
    """
    return float(bar_close) + entry_quote_offset(direction, bar_quote, spread)


def replay_anchor(
    bar_close: float, direction: int, spread: float, bar_quote: BarQuote
) -> float:
    """The `entry_price` to hand `exits.replay` for a fill-anchored at-market trade.

    ``anchor = transacted_entry - exit_quote_offset``, which collapses to

        anchor = bar_close + direction * spread

    on ANY bar quote — the crossing costs one full spread wherever the tape sits, so a
    mid archive is exactly as optimistic as a bid one. Pinned by
    `test_anchor_is_bar_quote_invariant`.
    """
    return (
        transacted_entry_price(bar_close, direction, spread, bar_quote)
        - exit_quote_offset(direction, bar_quote, spread)
    )


def entry_trigger_level_on_tape(
    level: float, direction: int, spread: float, bar_quote: BarQuote
) -> float:
    """Where a pending entry at `level` fires, expressed in tape units.

    A BUY LIMIT / BUY STOP triggers on the ASK and a SELL on the BID (`execution.py:6197`),
    so on a BID tape a long's trigger sits one spread BELOW the level and a short's exactly
    on it. This is the level-anchored entry displacement.

    **Whether that means "touches more often" depends on which way the market approaches, and
    the estate's dominant case is the opposite of the intuitive one** — corrected by the v1
    verification lane, wave 20, which found this docstring generalising in the flattering
    direction (`phase20/SESSION_V1_VERIFICATION.md` §4.4,
    `phase20/receipts/v1/v1_limit_fill.py`):

    | order (BID tape)            | tape trigger | approached      | vs an unshifted walk |
    |-----------------------------|-------------:|-----------------|----------------------|
    | BUY LIMIT (POI demand zone) |    level - s | falling into it | **LATER, touches LESS often** |
    | BUY STOP (breakout)         |    level - s | rising into it  | earlier, touches more often   |
    | SELL LIMIT / SELL STOP      |    level     | either          | unchanged                   |

    The broad V4 POI families (`current_fvg_fill`, `current_ob_retest`,
    `current_breaker_re_entry`) rest LIMITS, so for them a corrected walk makes a long
    touch-eligible strictly less often — by a median 0.081 R of extra penetration
    (`R1_BROAD_DELTA_V1.json → spread_over_risk_median`). No published number depends on
    this: `r1_broad_rewalk.py:184-190` walks its roster from the level unconditionally and
    says so.
    """
    return float(level) - entry_quote_offset(direction, bar_quote, spread)


def level_anchor_for_replay(
    level: float, direction: int, spread: float, bar_quote: BarQuote
) -> float:
    """`entry_price` for a LEVEL-anchored trade whose pending entry filled at `level`.

    The transacted price IS the level (you get filled at your own price); only the exit
    legs need translating into tape units, so the anchor is `level - exit_quote_offset`.
    """
    return float(level) - exit_quote_offset(direction, bar_quote, spread)


# ----------------------------------------------------------- ordered quote truth


def _tick_bounds(ticks: OrderedQuoteTicks, start: int, end: int | None) -> tuple[int, int]:
    n = len(ticks.times)
    stop = n if end is None else int(end)
    if not (0 <= start < stop <= n):
        raise ValueError(
            f"tick window must satisfy 0 <= start < end <= {n}, got {start}/{stop}"
        )
    return int(start), stop


def first_resting_limit_touch(
    ticks: OrderedQuoteTicks,
    direction: int,
    limit_price: float,
    *,
    start: int = 0,
    end: int | None = None,
) -> QuoteTouch | None:
    """Return the first ordered correct-side touch for a resting LIMIT, or ``None``.

    A BUY LIMIT is touch-eligible only when ASK is at or below its level; a SELL LIMIT
    only when BID is at or above it. The returned quote is the first observed eligibility
    event, not an execution: no queue/depth/order-event evidence is present. `start` is
    the first quote after activation; callers must not include pre-order ticks and this
    function never sorts their sequence.
    """
    _check_direction(direction)
    level = float(limit_price)
    if not (math.isfinite(level) and level > 0):
        raise ValueError(f"limit_price must be finite and > 0, got {limit_price!r}")
    lo, hi = _tick_bounds(ticks, start, end)
    for k in range(lo, hi):
        bid = float(ticks.bids[k])
        ask = float(ticks.asks[k])
        px = ask if direction > 0 else bid
        if (direction > 0 and px <= level) or (direction < 0 and px >= level):
            return QuoteTouch(k, ticks.times[k], bid, ask, px)
    return None


def replay_ticks(
    ticks: OrderedQuoteTicks,
    start: int,
    direction: int,
    *,
    entry_price: float,
    stop_dist: float,
    policy: ExitPolicy = PLAIN,
    end: int | None = None,
    horizon_reason: str = "maxbars",
    stop_price: float | None = None,
    target_price: float | None = None,
) -> TickPathResult:
    """Replay an entered trade on ordered BID/ASK quotes.

    `start` is the first quote after entry and `end` is exclusive. The caller owns the
    time-to-index conversion because only it knows whether the horizon is 80 M15 bars,
    a pending-order expiry, or an explicit clock deadline. LONG exits read BID; SHORT
    exits read ASK. Every triggered leg fills at the quote that first crossed it, so
    time-varying spread and gap-through are observed rather than modelled.

    Tick order removes the OHLC trail ambiguity: a quote may set a new extreme or retrace
    from an earlier one, but cannot do both at once. `trail_lag_extremes` is therefore not
    applied; it is a bar-only uncertainty switch. Rollover/time-stop policies must be
    converted into `end` by the caller and named with `horizon_reason`.
    """
    _check_direction(direction)
    if not (math.isfinite(float(entry_price)) and float(entry_price) > 0):
        raise ValueError(f"entry_price must be finite and > 0, got {entry_price!r}")
    if not (math.isfinite(float(stop_dist)) and float(stop_dist) > 0):
        raise ValueError(f"stop_dist must be finite and > 0, got {stop_dist!r}")
    if policy.flat_before_rollover_local_hour is not None or policy.time_stop_bars is not None:
        raise ValueError(
            "tick replay needs an explicit end index for clock exits; convert the deadline "
            "to end and pass its meaning as horizon_reason"
        )
    lo, hi = _tick_bounds(ticks, start, end)
    entry = float(entry_price)
    risk = float(stop_dist)
    stop = (
        entry - direction * risk
        if stop_price is None
        else float(stop_price)
    )
    target = (
        entry + direction * policy.target_dist
        if target_price is None and policy.target_dist
        else float(target_price)
        if target_price is not None
        else None
    )
    if not (math.isfinite(stop) and stop > 0):
        raise ValueError(f"stop_price must be finite and > 0, got {stop!r}")
    if target is not None and not (math.isfinite(target) and target > 0):
        raise ValueError(f"target_price must be finite and > 0, got {target!r}")
    partial = policy.partial_at_r
    partial_level = entry + direction * partial * risk if partial else None
    trail_arm = entry + direction * policy.trail_arm if policy.trail_arm else None
    extreme = entry
    armed = False
    banked_r = 0.0
    taken_frac = 0.0
    mfe = 0.0
    mae = 0.0

    def finish(k: int, px: float, reason: str) -> TickPathResult:
        raw = direction * (px - entry) / risk
        total = banked_r + (1.0 - taken_frac) * raw
        detail: dict[str, Any] = {
            "policy": policy.label,
            "entry_price": entry,
            "exit_quote_side": "bid" if direction > 0 else "ask",
            "fill_convention": "first_ordered_executable_quote",
        }
        if stop_price is not None or target_price is not None:
            detail["level_geometry"] = "explicit_absolute_stop_target"
        if partial is not None:
            detail["partial_order_event_authority"] = (
                "NOT_AVAILABLE_MODELLED_CLIENT_ACTION"
            )
        if partial is not None and target is not None:
            detail.update({
                "partial_vs_target_priority": (
                    "broker_resting_final_target_first_on_same_quote"
                ),
            })
        if taken_frac:
            detail.update({
                "partial_banked_r": round(banked_r, 6),
                "partial_frac_taken": taken_frac,
                "raw_remainder_r": round(raw, 6),
            })
        return TickPathResult(
            r_gross=total,
            exit_index=k,
            exit_at=ticks.times[k],
            exit_price=px,
            exit_reason=reason,
            mfe_r=mfe,
            mae_r=mae,
            ticks_held=k - lo + 1,
            detail=detail,
        )

    for k in range(lo, hi):
        px = float(ticks.bids[k] if direction > 0 else ticks.asks[k])
        r_here = direction * (px - entry) / risk
        if r_here > mfe:
            mfe = r_here
        if r_here < mae:
            mae = r_here

        # A protective stop wins first. The final target is broker-resting in production,
        # while the partial is a client-side detection followed by another order request.
        # Therefore one quote through both resolves target-first unless deal/order evidence
        # proves otherwise. A partial is modelled only when that quote has not reached TP.
        if (direction > 0 and px <= stop) or (direction < 0 and px >= stop):
            return finish(k, px, "stop")
        if target is not None and (
            (direction > 0 and px >= target) or (direction < 0 and px <= target)
        ):
            return finish(k, px, "target")
        if partial_level is not None and (
            (direction > 0 and px >= partial_level)
            or (direction < 0 and px <= partial_level)
        ):
            banked_r += policy.partial_frac * r_here
            taken_frac = policy.partial_frac
            partial_level = None
            if policy.be_stop_after_partial:
                stop = entry

        if trail_arm is not None:
            if direction > 0:
                if px > extreme:
                    extreme = px
                if not armed and px >= trail_arm:
                    armed = True
                level = extreme - policy.trail_gap
                if armed and extreme > entry and px <= level:
                    return finish(k, px, "trail")
            else:
                if px < extreme:
                    extreme = px
                if not armed and px <= trail_arm:
                    armed = True
                level = extreme + policy.trail_gap
                if armed and extreme < entry and px >= level:
                    return finish(k, px, "trail")

    last = hi - 1
    px = float(ticks.bids[last] if direction > 0 else ticks.asks[last])
    return finish(last, px, horizon_reason)


def _lifecycle_utc(value: Any, field: str) -> dt.datetime:
    if not isinstance(value, dt.datetime):
        raise ValueError(f"{field} must be a timezone-aware datetime, got {value!r}")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware, got {value!r}")
    return value.astimezone(dt.timezone.utc)


def resolve_post_submission_quote_lifecycle(
    ticks: OrderedQuoteTicks,
    *,
    direction: int,
    post_scheduler_order_type: str,
    submission_or_ack_time_utc: dt.datetime,
    required_horizon_utc: dt.datetime,
    source_start_utc: dt.datetime,
    source_end_utc: dt.datetime,
    source_coverage_verified: bool,
    approved_entry_price: float,
    approved_stop_price: float,
    approved_target_price: float,
    approved_risk_distance: float,
    policy: ExitPolicy = PLAIN,
) -> OrderedQuoteLifecycleResult:
    """Model one post-Scheduler order on a caller-verified ordered quote packet.

    MARKET activates at the first strictly post-submission far-side quote. LIMIT keeps
    its price bound: an immediately marketable limit activates at that first quote, while
    a resting limit is only *touch eligible* when ASK (buy) or BID (sell) reaches it.
    Resting touch is an optimistic model input, never queue or broker-fill evidence.

    The approved entry/stop distance remains the R denominator after price improvement.
    A no-touch or horizon close is measurable only when the declared source covers the
    whole required horizon and has an explicit executable quote strictly before it. A
    stop, target, or trail observed earlier may resolve on a shorter capture whose
    verified prefix begins no later than submission. Quotes at or after the horizon never
    trigger lifecycle predicates. Broker fill remains NOT_EVALUABLE throughout.
    """

    _check_direction(direction)
    order_type = str(post_scheduler_order_type).strip().upper()
    if order_type not in {"MARKET", "LIMIT"}:
        raise ValueError(
            "post_scheduler_order_type must be explicitly MARKET or LIMIT, got "
            f"{post_scheduler_order_type!r}"
        )
    submission = _lifecycle_utc(
        submission_or_ack_time_utc, "submission_or_ack_time_utc"
    )
    horizon = _lifecycle_utc(required_horizon_utc, "required_horizon_utc")
    source_start = _lifecycle_utc(source_start_utc, "source_start_utc")
    source_end = _lifecycle_utc(source_end_utc, "source_end_utc")
    if horizon <= submission:
        raise ValueError("required_horizon_utc must be after submission_or_ack_time_utc")
    if source_end < source_start:
        raise ValueError("source_end_utc precedes source_start_utc")

    approved_entry = float(approved_entry_price)
    approved_stop = float(approved_stop_price)
    approved_target = float(approved_target_price)
    approved_risk = float(approved_risk_distance)
    if not all(
        math.isfinite(value) and value > 0
        for value in (approved_entry, approved_stop, approved_target, approved_risk)
    ):
        raise ValueError("approved entry/stop/target/risk must all be finite and > 0")
    tolerance = max(1e-12, 1e-9 * max(abs(approved_entry), abs(approved_stop)))
    if abs(abs(approved_entry - approved_stop) - approved_risk) > tolerance:
        raise ValueError(
            "approved_risk_distance conflicts with approved entry/stop geometry"
        )
    if direction > 0 and not (approved_stop < approved_entry < approved_target):
        raise ValueError("LONG approved geometry must satisfy stop < entry < target")
    if direction < 0 and not (approved_target < approved_entry < approved_stop):
        raise ValueError("SHORT approved geometry must satisfy target < entry < stop")

    times = tuple(
        _lifecycle_utc(value, f"ticks.times[{index}]")
        for index, value in enumerate(ticks.times)
    )
    if times[0] < source_start or times[-1] > source_end:
        raise ValueError("ordered tick rows fall outside declared source interval")
    first_side = "ask" if direction > 0 else "bid"

    first_index = next(
        (index for index, at in enumerate(times) if at > submission),
        None,
    )
    horizon_cutoff = next(
        (index for index, at in enumerate(times) if at >= horizon),
        len(times),
    )
    horizon_close_index = horizon_cutoff - 1 if horizon_cutoff else None
    prefix_covered = bool(source_coverage_verified and source_start <= submission)
    horizon_covered = bool(
        prefix_covered
        and source_end >= horizon
        and horizon_close_index is not None
        and times[horizon_close_index] < horizon
    )
    first_price = (
        float(ticks.asks[first_index] if direction > 0 else ticks.bids[first_index])
        if first_index is not None
        else None
    )

    def result(
        *,
        measurement_status: str,
        lifecycle_status: str,
        coverage_status: str,
        activation_class: str | None = None,
        touch: QuoteTouch | None = None,
        touch_eligible: bool | None = None,
        entry_index: int | None = None,
        entry_price: float | None = None,
        stop_r: float | None = None,
        target_r: float | None = None,
        path: TickPathResult | None = None,
        source_gaps: tuple[str, ...] = (),
        detail: dict[str, Any] | None = None,
    ) -> OrderedQuoteLifecycleResult:
        payload = {
            "approved_entry_price": approved_entry,
            "approved_stop_price": approved_stop,
            "approved_target_price": approved_target,
            "source_start_utc": source_start.isoformat(),
            "source_end_utc": source_end.isoformat(),
            "source_coverage_verified": bool(source_coverage_verified),
            "horizon_close_quote_index": horizon_close_index,
            "horizon_boundary_convention": (
                "LAST_CAPTURED_EXECUTABLE_QUOTE_STRICTLY_BEFORE_HORIZON_"
                "UNDER_VERIFIED_COVERAGE"
            ),
            "entry_model_authority": (
                "FIRST_STRICTLY_CAUSAL_FAR_SIDE_QUOTE_MODEL"
                if order_type == "MARKET"
                else "OPTIMISTIC_CORRECT_SIDE_TOUCH_NOT_QUEUE_OR_FILL_TRUTH"
            ),
            **(detail or {}),
        }
        if path is not None:
            payload["ordered_exit_path"] = path.as_dict()
        return OrderedQuoteLifecycleResult(
            measurement_status=measurement_status,
            modelled_lifecycle_status=lifecycle_status,
            post_scheduler_order_type=order_type,
            direction=direction,
            submission_or_ack_time_utc=submission.isoformat(),
            required_horizon_utc=horizon.isoformat(),
            coverage_status=coverage_status,
            activation_class=activation_class,
            first_causal_quote_index=first_index,
            first_causal_quote_at=(
                times[first_index].isoformat() if first_index is not None else None
            ),
            first_causal_quote_side=first_side,
            first_causal_quote_price=first_price,
            correct_side_touch_eligible=touch_eligible,
            correct_side_touch_index=touch.index if touch is not None else None,
            correct_side_touch_at=(
                times[touch.index].isoformat() if touch is not None else None
            ),
            modelled_entry_index=entry_index,
            modelled_entry_at=(
                times[entry_index].isoformat() if entry_index is not None else None
            ),
            modelled_entry_price=entry_price,
            approved_risk_distance=approved_risk,
            stop_r=stop_r,
            target_r=target_r,
            terminal_outcome=path.exit_reason if path is not None else None,
            terminal_at=(
                times[path.exit_index].isoformat() if path is not None else None
            ),
            terminal_price=path.exit_price if path is not None else None,
            terminal_r=path.r_gross if path is not None else None,
            source_gaps=source_gaps,
            detail=payload,
        )

    if not prefix_covered:
        return result(
            measurement_status="NOT_EVALUABLE",
            lifecycle_status="SOURCE_PREFIX_NOT_VERIFIED_FROM_SUBMISSION",
            coverage_status="SOURCE_PREFIX_NOT_VERIFIED",
            source_gaps=("verified_ordered_quote_prefix_from_submission_missing",),
        )
    if first_index is None or times[first_index] >= horizon:
        return result(
            measurement_status="NOT_EVALUABLE",
            lifecycle_status="NO_CAUSAL_QUOTE_DURING_REQUIRED_WINDOW",
            coverage_status=(
                "FULL_HORIZON_WITHOUT_IN_WINDOW_QUOTE"
                if horizon_covered
                else "PARTIAL_HORIZON_CAPTURE"
            ),
            source_gaps=("first_strictly_post_submission_quote_missing_before_horizon",),
        )

    activation_end = horizon_cutoff
    path_end = horizon_cutoff
    if order_type == "MARKET":
        activation = "MARKET_FIRST_STRICTLY_CAUSAL_FAR_SIDE_QUOTE"
        touch = None
        touch_eligible = None
        entry_index = first_index
    else:
        marketable = (
            first_price <= approved_entry
            if direction > 0
            else first_price >= approved_entry
        )
        activation = (
            "MARKETABLE_LIMIT_AT_FIRST_STRICTLY_CAUSAL_QUOTE"
            if marketable
            else "RESTING_LIMIT_AFTER_FIRST_STRICTLY_CAUSAL_QUOTE"
        )
        touch = first_resting_limit_touch(
            ticks,
            direction,
            approved_entry,
            start=first_index,
            end=activation_end,
        )
        if touch is None:
            if horizon_covered:
                return result(
                    measurement_status="EVALUATED",
                    lifecycle_status="NO_CORRECT_SIDE_LIMIT_TOUCH_BEFORE_HORIZON",
                    coverage_status="FULL_REQUIRED_HORIZON_COVERED",
                    activation_class=activation,
                    touch_eligible=False,
                )
            return result(
                measurement_status="NOT_EVALUABLE",
                lifecycle_status="LIMIT_TOUCH_ABSENCE_NOT_EVALUABLE_PARTIAL_CAPTURE",
                coverage_status="PARTIAL_HORIZON_CAPTURE",
                activation_class=activation,
                source_gaps=("required_horizon_not_covered_for_limit_no_touch",),
            )
        touch_eligible = True
        entry_index = touch.index

    entry_price = float(
        ticks.asks[entry_index] if direction > 0 else ticks.bids[entry_index]
    )
    entry_exit_side = float(
        ticks.bids[entry_index] if direction > 0 else ticks.asks[entry_index]
    )
    stop_r = direction * (approved_stop - entry_price) / approved_risk
    target_r = direction * (approved_target - entry_price) / approved_risk
    entry_quote_through_stop = (
        entry_exit_side <= approved_stop
        if direction > 0
        else entry_exit_side >= approved_stop
    )
    if stop_r >= 0 or target_r <= 0 or entry_quote_through_stop:
        return result(
            measurement_status="NOT_EVALUABLE",
            lifecycle_status="FIRST_TRADABLE_ENTRY_QUOTE_PAST_PROTECTION_GEOMETRY",
            coverage_status=(
                "FULL_REQUIRED_HORIZON_COVERED"
                if horizon_covered
                else "PARTIAL_HORIZON_CAPTURE"
            ),
            activation_class=activation,
            touch=touch,
            touch_eligible=touch_eligible,
            entry_index=entry_index,
            entry_price=entry_price,
            stop_r=stop_r,
            target_r=target_r,
            source_gaps=(
                "entry_and_protective_order_sequence_requires_order_or_deal_evidence",
            ),
            detail={"modelled_entry_exit_side_price": entry_exit_side},
        )
    if entry_index + 1 >= path_end:
        return result(
            measurement_status="NOT_EVALUABLE",
            lifecycle_status="MODELLED_ENTRY_WITHOUT_POST_ENTRY_QUOTE",
            coverage_status="PARTIAL_HORIZON_CAPTURE",
            activation_class=activation,
            touch=touch,
            touch_eligible=touch_eligible,
            entry_index=entry_index,
            entry_price=entry_price,
            stop_r=stop_r,
            target_r=target_r,
            source_gaps=("post_entry_ordered_quote_missing",),
        )

    path = replay_ticks(
        ticks,
        entry_index + 1,
        direction,
        entry_price=entry_price,
        stop_dist=approved_risk,
        policy=policy,
        end=path_end,
        horizon_reason=("required_horizon" if horizon_covered else "capture_end"),
        stop_price=approved_stop,
        target_price=approved_target,
    )
    if path.exit_reason == "capture_end":
        return result(
            measurement_status="NOT_EVALUABLE",
            lifecycle_status="MODELLED_ENTRY_NO_TERMINAL_PARTIAL_CAPTURE",
            coverage_status="PARTIAL_HORIZON_CAPTURE",
            activation_class=activation,
            touch=touch,
            touch_eligible=touch_eligible,
            entry_index=entry_index,
            entry_price=entry_price,
            stop_r=stop_r,
            target_r=target_r,
            source_gaps=("required_horizon_not_covered_after_modelled_entry",),
            detail={"partial_capture_path_diagnostic": path.as_dict()},
        )
    return result(
        measurement_status="EVALUATED",
        lifecycle_status=(
            "MODELLED_MARKET_LIFECYCLE_NOT_BROKER_FILL"
            if order_type == "MARKET"
            else "MODELLED_FROM_OPTIMISTIC_LIMIT_TOUCH_NOT_QUEUE_OR_BROKER_FILL"
        ),
        coverage_status=(
            "FULL_REQUIRED_HORIZON_COVERED"
            if horizon_covered
            else "VERIFIED_PREFIX_THROUGH_OBSERVED_TERMINAL"
        ),
        activation_class=activation,
        touch=touch,
        touch_eligible=touch_eligible,
        entry_index=entry_index,
        entry_price=entry_price,
        stop_r=stop_r,
        target_r=target_r,
        path=path,
    )


def resolve_post_submission_m1_lifecycle(
    m1_bars: Sequence[Any],
    *,
    m1_open_times_utc: Sequence[dt.datetime],
    direction: int,
    proposed_order_type: str,
    submission_or_ack_time_utc: dt.datetime,
    expiry_utc: dt.datetime,
    required_horizon_utc: dt.datetime,
    approved_entry_price: float,
    approved_stop_price: float,
    approved_target_price: float,
    approved_risk_distance: float,
    m1_price_basis: BarQuote | None,
    spread_by_bar: Sequence[float | None] | None,
    source_interval_verified: bool,
    symbol_spec_hash_sha256: str | None,
    spread_source_hash_sha256: str | None,
) -> M1ModelledLifecycleResult:
    """Resolve a native MARKET/LIMIT lifecycle from caller-authorized M1 bars.

    The submission interval is never causal. Spread transforms the declared tape into
    executable entry/exit sides. Ambiguous OHLC ordering is censored, never guessed.
    """

    _check_direction(direction)
    order_type = str(proposed_order_type).strip().upper()
    if order_type not in {"MARKET", "LIMIT"}:
        raise ValueError(
            "proposed_order_type must be the occurrence's native MARKET or LIMIT, got "
            f"{proposed_order_type!r}"
        )
    submission = _lifecycle_utc(
        submission_or_ack_time_utc, "submission_or_ack_time_utc"
    )
    expiry = _lifecycle_utc(expiry_utc, "expiry_utc")
    horizon = _lifecycle_utc(required_horizon_utc, "required_horizon_utc")
    minute = dt.timedelta(minutes=1)

    def number_or_nan(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return math.nan

    entry, stop, target, risk = (
        number_or_nan(value)
        for value in (
            approved_entry_price,
            approved_stop_price,
            approved_target_price,
            approved_risk_distance,
        )
    )

    base_detail = {
        "order_contract": {
            "direction": direction,
            "submission_or_ack_time_utc": submission.isoformat(),
            "expiry_utc": expiry.isoformat(),
            "required_horizon_utc": horizon.isoformat(),
            "approved_entry_price": entry if math.isfinite(entry) else None,
            "approved_stop_price": stop if math.isfinite(stop) else None,
            "approved_target_price": target if math.isfinite(target) else None,
            "approved_risk_distance": risk if math.isfinite(risk) else None,
        },
        "m1_interval_seconds": 60,
        "m1_price_basis": (
            m1_price_basis.value if isinstance(m1_price_basis, BarQuote) else None
        ),
        "entry_quote_side": "ask" if direction > 0 else "bid",
        "exit_quote_side": "bid" if direction > 0 else "ask",
        "spread_geometry": "SOURCE_BOUND_CONSTANT_SPREAD_WITHIN_EACH_M1_INTERVAL",
        "symbol_spec_hash_sha256": symbol_spec_hash_sha256,
        "spread_source_hash_sha256": spread_source_hash_sha256,
        "time_stop_rule": "LAST_COMPLETE_PRE_HORIZON_EXECUTABLE_EXIT_SIDE_CLOSE",
    }

    def result(
        status: str,
        *,
        fill: tuple[int, dt.datetime, float] | None = None,
        terminal: tuple[str, int | None, dt.datetime, float | None, float | None]
        | None = None,
        reason: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> M1ModelledLifecycleResult:
        state, terminal_index, terminal_time, terminal_price, terminal_r = (
            terminal if terminal is not None else (None, None, None, None, None)
        )
        return M1ModelledLifecycleResult(
            lifecycle_label_status=status,
            proposed_order_type=order_type,
            modelled_fill_bar_index=fill[0] if fill else None,
            modelled_fill_time_utc=fill[1].isoformat() if fill else None,
            modelled_fill_price=fill[2] if fill else None,
            terminal_state=state,
            terminal_bar_index=terminal_index,
            terminal_time_utc=terminal_time.isoformat() if terminal_time else None,
            terminal_price=terminal_price,
            terminal_gross_r=terminal_r,
            censor_reason=reason,
            detail={**base_detail, **(detail or {})},
        )

    class _Censor(Exception):
        def __init__(self, status: str, reason: str):
            self.status, self.reason = status, reason

    def fail(status: str, reason: str) -> None:
        raise _Censor(status, reason)

    fill: tuple[int, dt.datetime, float, bool, str] | None = None
    try:
        if not all(math.isfinite(value) and value > 0 for value in (entry, stop, target, risk)):
            fail("CENSORED_GEOMETRY", "approved_order_geometry_non_finite_or_non_positive")
        if not submission < expiry <= horizon:
            fail("CENSORED_GEOMETRY", "invalid_submission_expiry_horizon_order")
        derived_risk = abs(entry - stop)
        tolerance = max(
            1e-12,
            8.0 * math.ulp(max(abs(entry), abs(stop))),
            1e-9 * max(derived_risk, risk),
        )
        if abs(derived_risk - risk) > tolerance:
            fail("CENSORED_GEOMETRY", "approved_risk_distance_conflicts_with_geometry")
        valid_geometry = (
            stop < entry < target if direction > 0 else target < entry < stop
        )
        if not valid_geometry:
            fail("CENSORED_GEOMETRY", "entry_stop_target_order_invalid")
        if source_interval_verified is not True:
            fail("CENSORED_SOURCE_INTERVAL_GAP", "m1_source_interval_not_verified")

        def valid_hash(value: Any) -> bool:
            return bool(
                isinstance(value, str)
                and len(value) == 64
                and all(char in "009abcdefABCDEF" for char in value)
            )

        if (
            not isinstance(m1_price_basis, BarQuote)
            or not valid_hash(symbol_spec_hash_sha256)
            or not valid_hash(spread_source_hash_sha256)
            or spread_by_bar is None
            or len(spread_by_bar) != len(m1_bars)
        ):
            fail(
                "CENSORED_SPREAD_OR_SPEC_AUTHORITY",
                "m1_price_basis_spread_or_symbol_spec_authority_missing",
            )
        if not m1_bars or len(m1_open_times_utc) != len(m1_bars):
            fail("CENSORED_SOURCE_INTERVAL_GAP", "m1_bar_time_rows_missing_or_misaligned")
        try:
            times = tuple(
                _lifecycle_utc(value, f"m1_open_times_utc[{index}]")
                for index, value in enumerate(m1_open_times_utc)
            )
        except ValueError:
            fail("CENSORED_SOURCE_INTERVAL_GAP", "m1_open_time_missing_or_naive")
        if any(now <= before for before, now in zip(times, times[1:])):
            fail("CENSORED_SOURCE_INTERVAL_GAP", "m1_open_times_not_strictly_increasing")

        submission_index = next(
            (
                index
                for index, opened in enumerate(times)
                if opened <= submission < opened + minute
            ),
            None,
        )
        if submission_index is None:
            fail("CENSORED_SOURCE_INTERVAL_GAP", "submission_m1_interval_missing")

        def contiguous(previous: int, current: int, boundary: str) -> None:
            if current >= len(times):
                fail("CENSORED_SOURCE_INTERVAL_GAP", f"m1_coverage_ends_before_{boundary}")
            if times[current] != times[previous] + minute:
                fail("CENSORED_SOURCE_INTERVAL_GAP", f"m1_interval_gap_before_{boundary}")

        successor = submission_index + 1
        contiguous(submission_index, successor, "first_complete_successor")
        if times[successor] <= submission:
            fail("CENSORED_SOURCE_INTERVAL_GAP", "first_complete_successor_not_causal")

        def side_bar(index: int, *, is_entry: bool) -> tuple[float, float, float, float]:
            try:
                spread = float(spread_by_bar[index])
            except (TypeError, ValueError, IndexError):
                fail("CENSORED_SPREAD_OR_SPEC_AUTHORITY", "m1_spread_missing")
            if not math.isfinite(spread) or spread < 0:
                fail("CENSORED_SPREAD_OR_SPEC_AUTHORITY", "m1_spread_invalid")
            try:
                values = tuple(
                    float(getattr(m1_bars[index], name)) for name in ("o", "h", "l", "c")
                )
            except (AttributeError, TypeError, ValueError, IndexError):
                fail("CENSORED_SOURCE_INTERVAL_GAP", "m1_ohlc_missing_or_invalid")
            o, high, low, close = values
            if (
                not all(math.isfinite(value) and value > 0 for value in values)
                or high < max(o, close)
                or low > min(o, close)
                or high < low
            ):
                fail("CENSORED_SOURCE_INTERVAL_GAP", "m1_ohlc_missing_or_invalid")
            offset = (
                entry_quote_offset(direction, m1_price_basis, spread)
                if is_entry
                else exit_quote_offset(direction, m1_price_basis, spread)
            )
            shifted = tuple(value + offset for value in values)
            if not all(math.isfinite(value) and value > 0 for value in shifted):
                fail("CENSORED_SPREAD_OR_SPEC_AUTHORITY", "m1_quote_transform_invalid")
            return shifted

        def limit_touched(values: tuple[float, float, float, float]) -> bool:
            return values[2] <= entry if direction > 0 else values[1] >= entry

        def terminal_touches(
            values: tuple[float, float, float, float]
        ) -> tuple[bool, bool]:
            hit_stop = values[2] <= stop if direction > 0 else values[1] >= stop
            hit_target = values[1] >= target if direction > 0 else values[2] <= target
            return hit_stop, hit_target

        def no_fill() -> M1ModelledLifecycleResult:
            return result(
                "RESOLVED_NO_FILL",
                terminal=("NO_FILL", None, expiry, None, None),
                detail={
                    "no_fill_rule": (
                        "FULL_VERIFIED_M1_PATH_WITHOUT_CORRECT_SIDE_LIMIT_TOUCH"
                    )
                },
            )

        if order_type == "LIMIT" and limit_touched(
            side_bar(submission_index, is_entry=True)
        ):
            fail(
                "CENSORED_SUBMISSION_BAR_LIMIT_TOUCH_ORDERING",
                "submission_bar_limit_touch_order_unresolved",
            )

        if order_type == "MARKET":
            if times[successor] >= expiry:
                fail(
                    "CENSORED_GEOMETRY",
                    "market_expires_before_first_complete_successor_open",
                )
            fill = (
                successor,
                times[successor],
                side_bar(successor, is_entry=True)[0],
                True,
                "FIRST_COMPLETE_SUCCESSOR_M1_OPEN",
            )
        else:
            previous, current = submission_index, successor
            while True:
                contiguous(previous, current, "limit_expiry")
                opened = times[current]
                if opened >= expiry:
                    return no_fill()
                values = side_bar(current, is_entry=True)
                favorable_open = (
                    values[0] <= entry if direction > 0 else values[0] >= entry
                )
                touched = limit_touched(values)
                if favorable_open:
                    fill = (
                        current,
                        opened,
                        values[0],
                        True,
                        "FAVORABLE_EXECUTABLE_SIDE_M1_OPEN_THROUGH_LIMIT",
                    )
                    break
                if opened + minute > expiry:
                    if touched:
                        fail(
                            "CENSORED_ORDERING_AMBIGUITY",
                            "limit_touch_order_relative_to_intrabar_expiry_unresolved",
                        )
                    return no_fill()
                if touched:
                    fill = (
                        current,
                        opened + minute,
                        entry,
                        False,
                        "INTRABAR_TOUCH_M1_CLOSE_UPPER_BOUND",
                    )
                    break
                if opened + minute == expiry:
                    return no_fill()
                previous, current = current, current + 1

        assert fill is not None
        fill_index, fill_time, fill_price, fill_at_open, fill_semantics = fill
        public_fill = (fill_index, fill_time, fill_price)
        fill_detail = {
            "fill_time_semantics": fill_semantics,
            "fill_price_convention": (
                "EXECUTABLE_ENTRY_SIDE_OPEN"
                if fill_at_open
                else "APPROVED_LIMIT_PRICE_ON_INTRABAR_CORRECT_SIDE_TOUCH"
            ),
        }
        fill_exit = side_bar(fill_index, is_entry=False)
        exit_open = fill_exit[0]
        invalid_gap = fill_at_open and (
            direction * (stop - fill_price) / risk >= 0
            or direction * (target - fill_price) / risk <= 0
            or (exit_open <= stop if direction > 0 else exit_open >= stop)
            or (exit_open >= target if direction > 0 else exit_open <= target)
        )
        if invalid_gap:
            fail(
                "CENSORED_INVALID_GAP_THROUGH_SL_OR_TP",
                "first_modelled_executable_entry_quote_through_stop_or_target",
            )
        fill_end = times[fill_index] + minute
        if fill_end > horizon:
            fail(
                "CENSORED_SOURCE_INTERVAL_GAP",
                "no_complete_post_fill_m1_interval_before_horizon",
            )

        def terminal(
            state: str,
            index: int,
            at: dt.datetime,
            price: float,
            semantics: str,
        ) -> M1ModelledLifecycleResult:
            return result(
                {
                    "TARGET": "RESOLVED_FILLED_TARGET",
                    "STOP": "RESOLVED_FILLED_STOP",
                    "TIME_STOP": "RESOLVED_FILLED_TIME_STOP",
                }[state],
                fill=public_fill,
                terminal=(
                    state,
                    index,
                    at,
                    price,
                    direction * (price - fill_price) / risk,
                ),
                detail={**fill_detail, "terminal_time_semantics": semantics},
            )

        def inspect_bar(
            index: int,
            values: tuple[float, float, float, float],
            *,
            fill_bar: bool = False,
            complete_before_horizon: bool = True,
        ) -> M1ModelledLifecycleResult | None:
            opened, bar_end = times[index], times[index] + minute
            if not fill_bar:
                if values[0] <= stop if direction > 0 else values[0] >= stop:
                    return terminal("STOP", index, opened, values[0], "SUCCESSOR_M1_OPEN_GAP")
                if values[0] >= target if direction > 0 else values[0] <= target:
                    return terminal(
                        "TARGET", index, opened, values[0], "SUCCESSOR_M1_OPEN_GAP"
                    )
            hit_stop, hit_target = terminal_touches(values)
            if fill_bar and not fill_at_open and (hit_stop or hit_target):
                fail(
                    "CENSORED_ORDERING_AMBIGUITY",
                    "intrabar_limit_fill_and_terminal_touch_same_m1_bar",
                )
            if not complete_before_horizon:
                if hit_stop or hit_target:
                    fail(
                        "CENSORED_ORDERING_AMBIGUITY",
                        "terminal_touch_order_relative_to_intrabar_horizon_unresolved",
                    )
                return None
            if hit_stop and hit_target:
                fail(
                    "CENSORED_ORDERING_AMBIGUITY",
                    "stop_and_target_touch_same_m1_bar",
                )
            if hit_stop:
                return terminal(
                    "STOP", index, bar_end, stop, "INTRABAR_TOUCH_M1_CLOSE_UPPER_BOUND"
                )
            if hit_target:
                return terminal(
                    "TARGET",
                    index,
                    bar_end,
                    target,
                    "INTRABAR_TOUCH_M1_CLOSE_UPPER_BOUND",
                )
            return None

        resolved = inspect_bar(fill_index, fill_exit, fill_bar=True)
        if resolved is not None:
            return resolved
        last_index, last_end, last_close = fill_index, fill_end, fill_exit[3]
        previous, current = fill_index, fill_index + 1
        while last_end < horizon:
            contiguous(previous, current, "required_horizon")
            opened = times[current]
            if opened >= horizon:
                break
            values = side_bar(current, is_entry=False)
            complete = opened + minute <= horizon
            resolved = inspect_bar(
                current, values, complete_before_horizon=complete
            )
            if resolved is not None:
                return resolved
            if not complete:
                break
            last_index, last_end, last_close = current, opened + minute, values[3]
            previous, current = current, current + 1

        return terminal(
            "TIME_STOP",
            last_index,
            last_end,
            last_close,
            "LAST_COMPLETE_PRE_HORIZON_EXECUTABLE_EXIT_SIDE_CLOSE",
        )
    except _Censor as exc:
        public_fill = (fill[0], fill[1], fill[2]) if fill else None
        detail = (
            {
                "fill_time_semantics": fill[4],
                "fill_price_convention": (
                    "EXECUTABLE_ENTRY_SIDE_OPEN"
                    if fill[3]
                    else "APPROVED_LIMIT_PRICE_ON_INTRABAR_CORRECT_SIDE_TOUCH"
                ),
            }
            if fill
            else None
        )
        return result(
            exc.status,
            fill=public_fill,
            reason=exc.reason,
            detail=detail,
        )

# ------------------------------------------------------------------- the spread


def spread_for(
    symbol: str,
    at_utc: dt.datetime,
    *,
    account: str = "FTMO",
    band: str = "mid",
    require_decidable: bool = False,
) -> float:
    """Broker-true quoted spread in PRICE units, from the measured spread model.

    Delegates to `src.costs.spread_model` (Session AG) — a tick-measured anchor times a
    bar-measured era ratio times an intraweek multiplier, published as a band. That model
    is the estate's only spread source that is era-aware, and era-awareness is not a
    detail here: FX spreads in 2000-2003 were 20-50x today's while metals today are the
    most expensive point in the archive, so a flat 2026 snapshot mis-signs the correction
    on deep history.

    **Fails closed.** Anything the model cannot defend raises `SpreadUnavailable`.
    """
    try:
        from src.costs.spread_model import spread_price
    except Exception as exc:  # pragma: no cover - import environment
        raise SpreadUnavailable(f"spread model unimportable: {exc!r}") from exc
    try:
        est = spread_price(
            symbol, account, at_utc, band=band, require_decidable=require_decidable
        )
    except Exception as exc:
        raise SpreadUnavailable(
            f"no spread for {symbol!r} on {account!r} at {at_utc!r}: {exc!r}"
        ) from exc
    s = float(est.spread_price)
    if not (s > 0):
        raise SpreadUnavailable(
            f"spread model returned {s!r} for {symbol!r} at {at_utc!r}; a zero spread is "
            f"the defect this module exists to remove and is never substituted silently"
        )
    return s


# --------------------------------------------------------------------- the walk


@dataclass(frozen=True)
class QuoteSideTrade:
    """One walked trade, both conventions, with the delta made explicit."""

    corrected: PathResult
    uncorrected: PathResult
    spread: float
    anchor: float
    #: corrected.r_gross - uncorrected.r_gross. Negative is the walker's own optimism.
    delta_r: float
    exit_reason_changed: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "spread": self.spread,
            "anchor": self.anchor,
            "delta_r": self.delta_r,
            "exit_reason_changed": self.exit_reason_changed,
            "corrected": self.corrected.as_dict(),
            "uncorrected": self.uncorrected.as_dict(),
        }


@dataclass(frozen=True)
class ObservedQuoteSideTrade:
    """Same BID bars under legacy, scalar-spread, and observed BID/ASK execution."""

    observed: PathResult
    scalar: PathResult
    uncorrected: PathResult
    entry_price: float
    entry_spread: float
    delta_observed_vs_scalar: float
    delta_observed_vs_uncorrected: float
    observed_vs_scalar_reason_changed: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_price": self.entry_price,
            "entry_spread": self.entry_spread,
            "delta_observed_vs_scalar": self.delta_observed_vs_scalar,
            "delta_observed_vs_uncorrected": self.delta_observed_vs_uncorrected,
            "observed_vs_scalar_reason_changed": self.observed_vs_scalar_reason_changed,
            "observed": self.observed.as_dict(),
            "scalar": self.scalar.as_dict(),
            "uncorrected": self.uncorrected.as_dict(),
        }


def walk(
    bars: Sequence[Any],
    i: int,
    direction: int,
    *,
    stop_dist: float,
    spread: float,
    bar_quote: BarQuote,
    policy: ExitPolicy = PLAIN,
    anchor: LevelAnchor = LevelAnchor.FILL,
    entry_level: float | None = None,
    times: Sequence[dt.datetime] | None = None,
    server: str | None = None,
    bar_minutes: int | None = None,
    flat_before_utc: dt.datetime | None = None,
) -> QuoteSideTrade:
    """Walk one trade on both conventions and return both plus the delta.

    The uncorrected arm is `replay(...)` with no anchor override — byte-identical to what
    the estate published — so the A/B is exact by construction and cannot drift.

    `anchor=LevelAnchor.LEVEL` needs `entry_level`: the price the pending order rested at
    and therefore transacted at. The caller owns the entry-trigger displacement in that
    mode (`entry_trigger_level_on_tape`), because only the caller knows which bar the
    order filled on.
    """
    if anchor is LevelAnchor.FILL:
        if entry_level is not None:
            raise ValueError("entry_level is meaningless under LevelAnchor.FILL")
        px = replay_anchor(bars[i].c, direction, spread, bar_quote)
    else:
        if entry_level is None:
            raise ValueError("LevelAnchor.LEVEL requires entry_level")
        px = level_anchor_for_replay(entry_level, direction, spread, bar_quote)

    kw = dict(
        stop_dist=stop_dist, policy=policy, times=times, server=server,
        bar_minutes=bar_minutes, flat_before_utc=flat_before_utc,
    )
    corrected = replay(bars, i, direction, entry_price=px, **kw)
    uncorrected = replay(bars, i, direction, **kw)
    return QuoteSideTrade(
        corrected=corrected,
        uncorrected=uncorrected,
        spread=float(spread),
        anchor=float(px),
        delta_r=corrected.r_gross - uncorrected.r_gross,
        exit_reason_changed=corrected.exit_reason != uncorrected.exit_reason,
    )


def walk_observed_book(
    book: ObservedBookBars,
    i: int,
    direction: int,
    *,
    stop_dist: float,
    policy: ExitPolicy = PLAIN,
    times: Sequence[dt.datetime] | None = None,
    server: str | None = None,
    bar_minutes: int | None = None,
    flat_before_utc: dt.datetime | None = None,
    first_tradable_fills: bool = True,
) -> ObservedQuoteSideTrade:
    """Compare the old BID walk, the scalar repair, and an observed BID/ASK path.

    The book is explicitly BID/ASK because all measured GTOS archives are BID. Entry is
    the actual decision-bar close quote (ASK for a long, BID for a short); every exit read
    is BID for a long and ASK for a short. The scalar arm is the exact Wave-20 R1 repair
    using the entry spread as a constant, and the uncorrected arm is R1's byte-identical
    historical call. This makes the short-side residual a direct same-bytes A/B rather
    than a separately implemented comparator.
    """
    _check_direction(direction)
    if not (0 <= i < len(book.bid)):
        raise ValueError(f"entry bar index {i} is outside 0..{len(book.bid) - 1}")
    bid_close = float(book.bid[i].c)
    ask_close = float(book.ask[i].c)
    spread = ask_close - bid_close
    if spread < 0:
        raise ValueError(
            f"entry bar is crossed at {i}: bid close {bid_close!r} > ask close {ask_close!r}"
        )
    entry = ask_close if direction > 0 else bid_close
    kw = dict(
        stop_dist=stop_dist,
        policy=policy,
        times=times,
        server=server,
        bar_minutes=bar_minutes,
        flat_before_utc=flat_before_utc,
    )
    scalar_pair = walk(
        book.bid,
        i,
        direction,
        spread=spread,
        bar_quote=BarQuote.BID,
        **kw,
    )
    observed = replay(
        book.bid,
        i,
        direction,
        entry_price=entry,
        exit_bars=book.bid if direction > 0 else book.ask,
        first_tradable_fills=first_tradable_fills,
        **kw,
    )
    return ObservedQuoteSideTrade(
        observed=observed,
        scalar=scalar_pair.corrected,
        uncorrected=scalar_pair.uncorrected,
        entry_price=entry,
        entry_spread=spread,
        delta_observed_vs_scalar=observed.r_gross - scalar_pair.corrected.r_gross,
        delta_observed_vs_uncorrected=observed.r_gross - scalar_pair.uncorrected.r_gross,
        observed_vs_scalar_reason_changed=(
            observed.exit_reason != scalar_pair.corrected.exit_reason
        ),
    )
