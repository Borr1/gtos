"""Path replay: MFE/MAE, trail exits, time stops, and the pre-rollover flat.

WHY THIS EXISTS
---------------
`FOURTH_REVIEW.md` §2.2 says an expectancy failure with gross > 0 is a *cost-geometry*
prescription and a per-trade failure is an *exit* prescription — but neither can be
written down without knowing what the trade's path did. `primitives.simulate_detail`
returns `(R, exit_index)` and throws the path away, so the estate's records carry an
outcome and no excursion. Two sleeves in §3.4 (`asian_fade`, `metal_session_reversion`)
cannot be walked at all, because their exit contract is a TRAIL and the generation driver
never passed `trail_arm`/`trail_gap` to the simulator that has supported them all along
(`primitives.py:35`).

This module replays the same path and returns what the diagnosis needs:

    r_gross      identical to `simulate_detail`'s R under the same policy
    exit_index   identical
    exit_reason  which of {stop, target, trail, time_stop, rollover_flat, maxbars}
    mfe_r        maximum favourable excursion, in R, over the held bars
    mae_r        maximum adverse excursion, in R
    bars_to_mfe  when the best price happened — an exit-timing repair reads this

`partial_at_r` adds the fourth production policy, `partial_be_runner` — scale out half at
a trigger R and move the stop to breakeven. It is the LIVE contract of `metals_core`,
`metals_softband`, `metals_ob_micro` and `energy_agri` (`execution_packets.py:44-51`), two
of which are armed, and no walk in this programme had ever simulated it (B752). It changes
`r_gross` and never `exit_reason`: the banked half is added to the remainder's R.

THE IDENTITY CLAIM, AND HOW IT IS HELD
---------------------------------------
`replay(...)` under `ExitPolicy(target_dist=t, maxbars=m)` must return exactly what
`simulate_detail(..., target_dist=t, maxbars=m)` returns — same R to the last bit, same
exit index — for every input, or every number this module produces is about a different
program than the one that labelled the estate. That is not asserted, it is fuzzed:
`tests/research_infra/test_wf_exits_parity.py` runs 4,000 random bar series through both
and compares with `==`, including the trail arms and the pessimistic same-bar tie rule
(stop wins). The ordering of the checks inside the loop is therefore load-bearing and is
copied from `primitives.py:75-101` rather than rewritten.

MFE/MAE ARE BAR-EXTREME BOUNDS, NOT FILLS
------------------------------------------
`mfe_r` is the best CLOSED-BAR EXTREME reached before the exit bar, divided by the stop
distance. It is an upper bound on what any exit rule inside this bar grid could have
captured — intrabar sequence is unknown, so a trade whose bar touched both +2R and -0.9R
has both numbers and neither says which came first. Every consumer must read it as
"this much excursion existed", never as "this much was capturable". The exit bar itself
is INCLUDED in the excursion scan, because the excursion that triggers a trail happens on
the bar that ends the trade.

THE TRAIL'S INTRABAR ASSUMPTION, AND WHY IT IS A SWITCH RATHER THAN A FIX
--------------------------------------------------------------------------
MEASURED 2026-07-29 (B613), and it is the single most important caveat in this module.
`primitives.simulate` updates the running extreme from bar *j*'s own high and then, on the
SAME bar *j*, checks whether the low has retraced `trail_gap` from it — so a trail can arm
and fill inside one bar, at `high - gap`. That is an assumption about intrabar sequencing
(the high came first) which no bar archive can support, and it is not a small effect:
labelling `asian_fade` under its production trail contract, **95.8 % of trail exits land on
the first bar after entry**, and they carry the whole of a +0.759 R/trade apparent
improvement.

The fix is not to "correct" the labeller — `simulate` is the sanctioned fill authority and
the parity claim above is what makes every number here about the estate rather than about a
private reimplementation. So it is a **switch**, defaulting to the production behaviour:

    trail_lag_extremes=False   reproduce `primitives.simulate` exactly (the default)
    trail_lag_extremes=True    the running extreme comes only from STRICTLY EARLIER bars,
                               so a trail can never fill on the bar that set its own high

The honest reading of any trail result is the pair. If a trail's benefit survives
`trail_lag_extremes=True` it is a real exit repair; if it evaporates, the benefit was
intrabar sequencing and the repair needs tick data, not a bar backtest.

THE PRE-ROLLOVER FLAT (`fx_jpy_ny`'s repair, §3.2)
---------------------------------------------------
`flat_before_rollover_local_hour` closes the trade at the last bar that is fully complete
before the cutoff, if the trade is still open then. It takes the bar's CLOSE, which is the
honest price for a scheduled time exit. Broker wall clock comes from
`utils/broker_clock.py`, which fails closed on an unregistered server — so a caller who
does not name a server gets no rollover rule rather than a +3 h guess.

**CORRECTED 2026-07-30 (B751), and the correction is the whole point of the rule.** As
first written the cutoff was compared against each bar's OPEN, so on an M15 grid with
`hour=0` it selected the bar opening 23:45 — whose CLOSE is exactly the broker midnight.
`costs.model.rollover_nights` counts a night at every broker midnight `day <= end`, so an
exit landing exactly ON the rollover instant is charged a night: measured, entry 16:00 and
exit 00:00 gives `nights=1.0`, while exit 23:45 gives `0.0`. The rule whose stated purpose
is *"caps swap at structurally zero"* therefore capped it at one, off by a single bar.

The comparison is now against each bar's **close**, which requires the bar interval, so
`bar_minutes` is a new argument and the rule **fails closed without it** — the same
doctrine as the server: a caller who does not name the grid gets no rollover rule rather
than an off-by-one-bar one.

`flat_before_utc` is the general form of the same primitive: be flat before a UTC instant
the CALLER computed. It exists because the §5.3 swap-aware exit ("close before rollover
when expected remaining edge < swap/night") and the pre-weekend flat both need *some*
rollovers avoided and not others — the triple-swap weekday is worth three nights and a
Tuesday is worth one — and that decision needs the cost model, which this module must not
import if `simulate` parity is to mean anything. So the caller prices the rollovers and
passes the instant; this module only knows how to be flat before one.
"""

from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass, field
from typing import Any, Sequence

__all__ = ["ExitPolicy", "PathResult", "replay", "PLAIN"]


@dataclass(frozen=True)
class ExitPolicy:
    """One exit contract. The default is the plain stop/target/maxbars the estate ran on."""

    #: Price distance to the take-profit. None = no target.
    target_dist: float | None = None
    #: Price distance in favour at which the trail arms. None = no trail.
    trail_arm: float | None = None
    #: Price distance the trail gives back from the running extreme. Required with an arm.
    trail_gap: float | None = None
    #: Hard bar ceiling, as `simulate_detail` means it.
    maxbars: int = 80
    #: Close at the open of bar `entry + time_stop_bars` if still held. None = off.
    #: Distinct from `maxbars`: a time stop is a POLICY the sleeve owns, `maxbars` is the
    #: harness's ceiling, and a repair that tightens one must not silently move the other.
    time_stop_bars: int | None = None
    #: Broker wall-clock hour before which the position must be flat, on the entry day.
    #: None = off. Requires `server` on the replay call.
    flat_before_rollover_local_hour: int | None = None
    #: Take `partial_frac` of the position off at this R and (by default) move the stop to
    #: breakeven for the remainder. None = off.
    #:
    #: **This is the LIVE contract of four W7 sleeves and no walk had ever simulated it**
    #: (B752). `execution_packets.py:44-51` gives `metals_core`, `metals_softband`,
    #: `metals_ob_micro` and `energy_agri` `policy="partial_be_runner"` with
    #: `trigger_r` 1.5-2.0 and `partial_close_ratio=0.5`; two of the four are armed and
    #: trading real money. AA labelled all four under plain stop/target/maxbars, so
    #: `metals_core`'s measured capture ratio of 0.114 is a number about a contract the live
    #: book does not run. The fill is at the trigger level exactly, which is the same
    #: intrabar convention `simulate` already uses for a target (`primitives.py:75-101`), so
    #: this adds no fiction the sanctioned labeller does not already contain.
    partial_at_r: float | None = None
    #: Fraction closed at `partial_at_r`. The remainder carries (1 - this) of the R.
    partial_frac: float = 0.5
    #: Move the stop to breakeven once the partial is taken — the `_be_` in the policy name.
    be_stop_after_partial: bool = True
    #: **The intrabar honesty switch.** See THE TRAIL'S INTRABAR ASSUMPTION below.
    #: False reproduces `primitives.simulate` exactly, including its same-bar
    #: arm-and-fill. True forbids the trail from filling on a bar before the running
    #: extreme has been set by a STRICTLY EARLIER bar — which removes the assumption
    #: that within one bar the high came before the low.
    trail_lag_extremes: bool = False
    #: Label carried into the record so a swept variant is identifiable in the ledger.
    label: str = "plain"

    def __post_init__(self) -> None:
        if (self.trail_arm is None) != (self.trail_gap is None):
            raise ValueError(
                "trail_arm and trail_gap must be given together; a trail with no gap has "
                "no exit and a gap with no arm never arms."
            )
        if self.trail_gap is not None and not (self.trail_gap > 0):
            raise ValueError(f"trail_gap must be > 0, got {self.trail_gap!r}")
        if self.time_stop_bars is not None and self.time_stop_bars < 1:
            raise ValueError(f"time_stop_bars must be >= 1, got {self.time_stop_bars!r}")
        if self.maxbars < 1:
            raise ValueError(f"maxbars must be >= 1, got {self.maxbars!r}")
        if self.partial_at_r is not None and not (self.partial_at_r > 0):
            raise ValueError(f"partial_at_r must be > 0, got {self.partial_at_r!r}")
        if not (0.0 < self.partial_frac < 1.0):
            raise ValueError(
                f"partial_frac must be strictly between 0 and 1 (0 is no partial and 1 is a "
                f"target, both of which are already expressible), got {self.partial_frac!r}"
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "target_dist": self.target_dist,
            "trail_arm": self.trail_arm,
            "trail_gap": self.trail_gap,
            "maxbars": self.maxbars,
            "time_stop_bars": self.time_stop_bars,
            "flat_before_rollover_local_hour": self.flat_before_rollover_local_hour,
            "partial_at_r": self.partial_at_r,
            "partial_frac": self.partial_frac,
            "be_stop_after_partial": self.be_stop_after_partial,
        }


PLAIN = ExitPolicy()


@dataclass(frozen=True)
class PathResult:
    #: Realised R, gross of cost. Identical to `simulate_detail`'s first return under a
    #: policy that carries only {target_dist, trail_arm, trail_gap, maxbars}.
    r_gross: float
    #: Bar index of the exit. Identical to `simulate_detail`'s second return, same caveat.
    exit_index: int
    exit_reason: str
    #: Maximum favourable / adverse excursion in R over [entry+1, exit], bar extremes.
    mfe_r: float
    mae_r: float
    #: Bars from entry to the bar that set the MFE. 0 means the excursion never went
    #: positive; that is a real answer and it is what an entry-timing repair reads.
    bars_to_mfe: int
    bars_held: int
    #: Diagnostics the caller may want but must not confuse with a fill.
    detail: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "r_gross": self.r_gross,
            "exit_index": self.exit_index,
            "exit_reason": self.exit_reason,
            "mfe_r": round(self.mfe_r, 6),
            "mae_r": round(self.mae_r, 6),
            "bars_to_mfe": self.bars_to_mfe,
            "bars_held": self.bars_held,
            **({"detail": self.detail} if self.detail else {}),
        }


def _last_bar_closing_before(
    times: Sequence[dt.datetime],
    i: int,
    end: int,
    cutoff_utc: dt.datetime,
    bar_minutes: int,
) -> int | None:
    """Last index in (i, end] whose bar CLOSE is strictly before `cutoff_utc`.

    The close is `times[j] + bar_minutes`, because `times` are bar OPENS. Strictly before,
    not at: a position closed exactly ON a broker midnight is charged that night
    (`costs.model.rollover_nights`, `day <= end`), so "flat before the rollover" has to
    mean the bar that finished before it.

    Scans forward and stops at the first bar that closes at or after the cutoff, so a
    weekend gap in the grid cannot make a later bar qualify.
    """
    width = dt.timedelta(minutes=bar_minutes)
    last = None
    for j in range(i + 1, min(end, len(times) - 1) + 1):
        if times[j] + width < cutoff_utc:
            last = j
        else:
            break
    return last


def _rollover_cutoff_index(
    times: Sequence[dt.datetime] | None,
    i: int,
    end: int,
    hour: int,
    server: str | None,
    bar_minutes: int | None,
) -> int | None:
    """Last bar index at or before `end` that CLOSES before the next `hour` cutoff.

    Returns None when the rule cannot be applied — no times, no server, an unregistered
    server, or no `bar_minutes`. Failing closed here is deliberate on all four counts: a
    rollover rule applied on a guessed clock would move exits by three hours and look like
    a repair (`CLAUDE.md` §4, the EET/US-DST correction), and one applied on a guessed bar
    width is off by a bar in the one direction that matters (B751 — it lands the exit
    exactly on the rollover instant, which is charged).
    """
    if times is None or server is None or hour is None or bar_minutes is None:
        return None
    try:
        from src.utils.broker_clock import broker_naive_to_utc, resolve_rule, utc_to_broker_naive
    except ImportError:  # pragma: no cover - defensive
        return None
    try:
        rule = resolve_rule(server)
    except Exception:
        return None
    entry_local = utc_to_broker_naive(times[i], rule)
    cutoff_local = entry_local.replace(hour=hour, minute=0, second=0, microsecond=0)
    if entry_local >= cutoff_local:
        # Entered after the cutoff: the flat rule applies to the NEXT day's cutoff, which
        # is exactly what a 16:00-entry / 23:45-flat contract means.
        cutoff_local = cutoff_local + dt.timedelta(days=1)
    return _last_bar_closing_before(
        times, i, end, broker_naive_to_utc(cutoff_local, rule), int(bar_minutes)
    )


def replay(
    bars: Sequence[Any],
    i: int,
    direction: int,
    *,
    stop_dist: float,
    policy: ExitPolicy = PLAIN,
    times: Sequence[dt.datetime] | None = None,
    server: str | None = None,
    bar_minutes: int | None = None,
    flat_before_utc: dt.datetime | None = None,
    entry_price: float | None = None,
    exit_bars: Sequence[Any] | None = None,
    first_tradable_fills: bool = False,
) -> PathResult:
    """Replay one trade's path under `policy`, and report what the path did.

    `bars[k]` needs `.o/.h/.l/.c` (`primitives.Bar`, or anything shaped like it). Entry is
    `bars[i].c`, matching the only sanctioned labeller.

    `flat_before_utc` closes at the last bar completing strictly before that instant — the
    general form of the pre-rollover flat, for the rules whose cutoff only the caller can
    price (§5.3's swap-aware exit, the pre-weekend flat). Needs `times` and `bar_minutes`
    and is ignored without them, same fail-closed doctrine as the hour rule.

    `entry_price` overrides the anchor every level and every realised R is measured from.
    **It is the one hook the quote-side correction needs, and it is deliberately the ONLY
    one** (`walkforward.quote_side`, wave 20 lane r1). The bar archives are BID on
    open/high/low/close — settled on 87,060 M15 bars over 33 symbols and 820,452 M1 bars —
    while a round trip transacts on both sides of the book. For a fill-anchored trade
    (the live W7 contract: `ultimate_book/order_router.py:66-73` crosses the spread and
    then hangs SL and TP off the CROSSED price) the whole correction is
    ``entry_price = bars[i].c + direction * spread``: it moves the stop one spread nearer
    and the target one spread further in tape space, and it charges every close-based exit
    exactly one spread. Nothing else in this function changes, which is what keeps the
    `simulate_detail` parity claim — and every number this module has ever produced —
    intact. ``None`` reproduces `bars[i].c` byte-for-byte.

    `exit_bars` is the executable quote path for the closing side: BID bars for a long,
    ASK bars for a short. It is deliberately opt-in. When absent, every read still comes
    from `bars`, preserving the sanctioned one-sided labeller byte-for-byte; when present,
    its length must match `bars` and stops, targets, trails, excursions and clock exits all
    resolve on that observed side. This is the hook that removes the scalar-entry-spread
    approximation from short exits when an ASK series exists.

    `first_tradable_fills` is also opt-in. On an opening quote already through a standing
    stop, target, trail, or partial scale-out, the transaction uses that opening quote
    rather than a level the market did not trade. Production's final target is broker-
    resting while the partial is client-triggered: a quote through both therefore resolves
    target-first absent deal evidence. A partial is modelled only when TP was not crossed,
    and then updates the breakeven stop for the remainder. A trail is eligible only if its
    level existed before the bar opened: the opening quote is never applied to a trail
    formed from that same bar's extreme. With the flag false, historical convention is
    unchanged.
    """
    if not (stop_dist > 0):
        raise ValueError(f"stop_dist must be > 0 (it is the R unit), got {stop_dist!r}")
    if direction not in (1, -1):
        raise ValueError(f"direction must be +1 or -1, got {direction!r}")

    quote_bars = bars if exit_bars is None else exit_bars
    if len(quote_bars) != len(bars):
        raise ValueError(
            "exit_bars must be index-aligned with bars: "
            f"got {len(quote_bars)} quote bars for {len(bars)} source bars"
        )

    entry = bars[i].c if entry_price is None else float(entry_price)
    end = min(i + policy.maxbars, len(bars) - 1)
    t_stop = (i + policy.time_stop_bars) if policy.time_stop_bars is not None else None
    roll = _rollover_cutoff_index(
        times, i, end, policy.flat_before_rollover_local_hour, server, bar_minutes
    )
    if flat_before_utc is not None and times is not None and bar_minutes is not None:
        cut = _last_bar_closing_before(times, i, end, flat_before_utc, int(bar_minutes))
        # Whichever scheduled flat comes first binds. Both mean "be flat by then", so the
        # earlier cutoff is the operative one; None means that rule did not apply.
        roll = cut if roll is None else (cut if cut is not None and cut < roll else roll)

    mfe = 0.0
    mae = 0.0
    at_mfe = i
    #: Banked R from a partial close, and the fraction it consumed. Both stay 0 on every
    #: path that does not use `partial_at_r`, which is what keeps the `simulate_detail`
    #: parity claim intact.
    banked_r = 0.0
    taken_frac = 0.0
    partial_fill_price: float | None = None
    partial_fill_convention: str | None = None
    part = policy.partial_at_r

    def _fin(j: int, price: float, reason: str) -> PathResult:
        raw = ((price - entry) if direction > 0 else (entry - price)) / stop_dist
        r = banked_r + (1.0 - taken_frac) * raw
        detail = {"policy": policy.label, "entry_price": entry}
        if exit_bars is not None:
            detail["exit_quote_path"] = "supplied"
        if first_tradable_fills:
            detail["fill_convention"] = "first_tradable_on_open_gap"
        if part is not None:
            detail["partial_order_event_authority"] = (
                "NOT_AVAILABLE_MODELLED_CLIENT_ACTION"
            )
        if part is not None and tgt is not None:
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
            if first_tradable_fills:
                detail.update({
                    "partial_fill_price": partial_fill_price,
                    "partial_fill_convention": partial_fill_convention,
                })
        return PathResult(
            r_gross=r, exit_index=j, exit_reason=reason,
            mfe_r=mfe, mae_r=mae, bars_to_mfe=at_mfe - i, bars_held=j - i,
            detail=detail,
        )

    if direction > 0:
        stop = entry - stop_dist
        tgt = entry + policy.target_dist if policy.target_dist else None
        arm = entry + policy.trail_arm if policy.trail_arm else None
        plvl = entry + part * stop_dist if part else None
        mx = entry
        armed = False
        standing_trail: float | None = None
        for j in range(i + 1, end + 1):
            b = quote_bars[j]
            # An opening quote through a level is ordered evidence: the position is gone
            # before this bar can make any later high or low. Check it before excursion so
            # post-exit extremes do not leak into MFE/MAE. A standing trail is checked
            # first because it is the operative tightened stop, not a second order behind
            # the original stop.
            if first_tradable_fills:
                opening_reason = None
                if standing_trail is not None and b.o <= standing_trail:
                    opening_reason = "trail"
                elif b.o <= stop:
                    opening_reason = "stop"
                elif tgt is not None and b.o >= tgt:
                    opening_reason = "target"
                else:
                    if plvl is not None and b.o >= plvl:
                        partial_raw = (b.o - entry) / stop_dist
                        banked_r += policy.partial_frac * partial_raw
                        taken_frac = policy.partial_frac
                        partial_fill_price = float(b.o)
                        partial_fill_convention = (
                            "modelled_client_partial_first_quote_no_order_event"
                        )
                        plvl = None
                        if policy.be_stop_after_partial:
                            stop = entry
                if opening_reason is not None:
                    fav = (b.o - entry) / stop_dist
                    adv = fav
                    if fav > mfe:
                        mfe, at_mfe = fav, j
                    if adv < mae:
                        mae = adv
                    return _fin(j, b.o, opening_reason)
            # Excursion first: the bar that ends the trade also carries excursion, and a
            # trail repair is precisely a claim about that bar.
            fav = (b.h - entry) / stop_dist
            adv = (b.l - entry) / stop_dist
            if fav > mfe:
                mfe, at_mfe = fav, j
            if adv < mae:
                mae = adv
            # Order copied from primitives.simulate_detail: stop, target, trail. The
            # pessimistic same-bar tie (stop wins) is the whole reason it is copied. The
            # partial sits AFTER the stop and target for the same reason: a bar that took
            # the stop out took it out before the scale-out level was reached.
            if b.l <= stop:
                return _fin(j, stop, "stop")
            if tgt is not None and b.h >= tgt:
                return _fin(j, tgt, "target")
            if plvl is not None and b.h >= plvl:
                banked_r += policy.partial_frac * part
                taken_frac = policy.partial_frac
                partial_fill_price = float(plvl)
                partial_fill_convention = "level_on_ohlc_trigger"
                plvl = None
                if policy.be_stop_after_partial:
                    stop = entry
            if arm is not None:
                # `prev_mx` is the extreme as of the END of the previous bar. Under
                # `trail_lag_extremes` the fill check uses THAT, so a bar cannot both set
                # the high and be filled against it. `mx` still advances, so the trail
                # tracks correctly from the next bar on.
                prev_mx = mx
                if b.h > mx:
                    mx = b.h
                if not armed and b.h >= arm:
                    armed = True
                ref = prev_mx if policy.trail_lag_extremes else mx
                if armed and ref > entry and b.l <= ref - policy.trail_gap:
                    lvl = ref - policy.trail_gap
                    # GAP-AWARE FILL, in the lagged variant only. A stop-sell resting at
                    # `lvl` cannot fill above the bar's OPEN when the market opened below
                    # it. Without this the lagged variant fills at a price the bar never
                    # traded — which is the same intrabar fiction it exists to remove,
                    # moved one bar to the right. The default path keeps `simulate`'s
                    # semantics exactly, because parity with the sanctioned labeller is
                    # what makes every other number here about the estate.
                    if policy.trail_lag_extremes and not first_tradable_fills:
                        lvl = min(lvl, b.o)
                    return _fin(j, lvl, "trail")
                if armed and mx > entry:
                    # This level exists at the NEXT bar's open. Keeping it separate from
                    # `ref` is what prevents a same-bar extreme from being mislabelled as
                    # an opening gap.
                    standing_trail = mx - policy.trail_gap
            # Scheduled exits are checked AFTER the price-triggered ones, because a stop
            # that hit on this bar hit before the clock ran out on it.
            if roll is not None and j >= roll:
                return _fin(j, b.c, "rollover_flat")
            if t_stop is not None and j >= t_stop:
                return _fin(j, b.c, "time_stop")
        return _fin(end, quote_bars[end].c, "maxbars")

    stop = entry + stop_dist
    tgt = entry - policy.target_dist if policy.target_dist else None
    arm = entry - policy.trail_arm if policy.trail_arm else None
    plvl = entry - part * stop_dist if part else None
    mn = entry
    armed = False
    standing_trail = None
    for j in range(i + 1, end + 1):
        b = quote_bars[j]
        if first_tradable_fills:
            opening_reason = None
            if standing_trail is not None and b.o >= standing_trail:
                opening_reason = "trail"
            elif b.o >= stop:
                opening_reason = "stop"
            elif tgt is not None and b.o <= tgt:
                opening_reason = "target"
            else:
                if plvl is not None and b.o <= plvl:
                    partial_raw = (entry - b.o) / stop_dist
                    banked_r += policy.partial_frac * partial_raw
                    taken_frac = policy.partial_frac
                    partial_fill_price = float(b.o)
                    partial_fill_convention = (
                        "modelled_client_partial_first_quote_no_order_event"
                    )
                    plvl = None
                    if policy.be_stop_after_partial:
                        stop = entry
            if opening_reason is not None:
                fav = (entry - b.o) / stop_dist
                adv = fav
                if fav > mfe:
                    mfe, at_mfe = fav, j
                if adv < mae:
                    mae = adv
                return _fin(j, b.o, opening_reason)
        fav = (entry - b.l) / stop_dist
        adv = (entry - b.h) / stop_dist
        if fav > mfe:
            mfe, at_mfe = fav, j
        if adv < mae:
            mae = adv
        if b.h >= stop:
            return _fin(j, stop, "stop")
        if tgt is not None and b.l <= tgt:
            return _fin(j, tgt, "target")
        if plvl is not None and b.l <= plvl:
            banked_r += policy.partial_frac * part
            taken_frac = policy.partial_frac
            partial_fill_price = float(plvl)
            partial_fill_convention = "level_on_ohlc_trigger"
            plvl = None
            if policy.be_stop_after_partial:
                stop = entry
        if arm is not None:
            prev_mn = mn
            if b.l < mn:
                mn = b.l
            if not armed and b.l <= arm:
                armed = True
            ref = prev_mn if policy.trail_lag_extremes else mn
            if armed and ref < entry and b.h >= ref + policy.trail_gap:
                lvl = ref + policy.trail_gap
                if policy.trail_lag_extremes and not first_tradable_fills:
                    lvl = max(lvl, b.o)
                return _fin(j, lvl, "trail")
            if armed and mn < entry:
                standing_trail = mn + policy.trail_gap
        if roll is not None and j >= roll:
            return _fin(j, b.c, "rollover_flat")
        if t_stop is not None and j >= t_stop:
            return _fin(j, b.c, "time_stop")
    return _fin(end, quote_bars[end].c, "maxbars")


def excursion_summary(results: Sequence[PathResult]) -> dict[str, Any]:
    """Sleeve-level MFE/MAE aggregates — the block §4.1 asks `diagnose()` to carry.

    `capture_ratio_pooled` is sum(realised R) / sum(MFE) over trades whose MFE was
    positive — a RATIO OF MEANS, because the mean of per-trade ratios is unbounded below
    and dominated by near-zero denominators (B615). It is the
    number that separates an EXIT repair from an ENTRY repair: a sleeve with big
    excursions and a low capture ratio is losing money it reached, which an exit change
    can recover; one with no excursion at all has an entry problem and no exit change
    will help it. Reported with its own n, because trades with MFE <= 0 are excluded from
    the denominator by construction and that exclusion is outcome-correlated.
    """
    if not results:
        return {"available": False, "reason": "no path results"}
    mfes = [r.mfe_r for r in results]
    maes = [r.mae_r for r in results]
    pairs = [(r.r_gross, r.mfe_r) for r in results if r.mfe_r > 1e-9]
    reasons: dict[str, int] = {}
    for r in results:
        reasons[r.exit_reason] = reasons.get(r.exit_reason, 0) + 1
    n = len(results)
    return {
        "available": True,
        "n": n,
        "mean_mfe_r": round(math.fsum(mfes) / n, 5),
        "mean_mae_r": round(math.fsum(maes) / n, 5),
        "median_mfe_r": round(sorted(mfes)[n // 2], 5),
        "median_mae_r": round(sorted(maes)[n // 2], 5),
        "frac_mfe_over_1r": round(sum(1 for x in mfes if x >= 1.0) / n, 5),
        "frac_mfe_over_2r": round(sum(1 for x in mfes if x >= 2.0) / n, 5),
        "mean_bars_to_mfe": round(math.fsum(r.bars_to_mfe for r in results) / n, 3),
        "mean_bars_held": round(math.fsum(r.bars_held for r in results) / n, 3),
        "capture_ratio_pooled": (
            round(math.fsum(r for r, _ in pairs) / math.fsum(m for _, m in pairs), 5)
            if pairs else None),
        "capture_ratio_n": len(pairs),
        "exit_reasons": dict(sorted(reasons.items())),
        "note": (
            "MFE/MAE are bar-extreme BOUNDS over [entry+1, exit], not fills; intrabar "
            "sequence is unknown. capture_ratio_pooled is sum(R)/sum(MFE) over trades "
            "with MFE > 0 only — a ratio of means, never a mean of ratios."
        ),
    }
