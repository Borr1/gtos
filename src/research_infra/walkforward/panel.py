"""Trade records in, cost-true daily panel out.

THE COST BINDING, AND THE ONE RULE THAT MATTERS
-----------------------------------------------
`src/costs/cost_r` is the only cost authority (Session J's broker-truth layer). When it
raises, the trade is recorded UNPRICED and the sleeve's coverage falls. It is never
back-filled with a plausible number. That is not fastidiousness — it is F38, the defect
this whole wave exists downstream of: `broker_net_cost_engine.py:577-583` sums
`spread_r + expected_slippage_r + swap_cost_r`, three terms, no commission, and the
resulting "validation" was positive over 1,679 days and worthless.

THE DECOMPOSITION, AND WHY IT NEEDS NO FIXED POINT
--------------------------------------------------
Cost depends on holding time; holding time comes from the exit simulation; so naively the
two are circular. They are not, because `primitives.simulate` subtracts cost as a scalar in
R **at the end of the trade** and never uses it to decide a fill (`primitives.py:33-73` —
every `return` is `(price_delta)/stop_dist - cost`). The path is cost-independent. So:

    R_gross = simulate(..., cost=0.0)        # path, exit bar, holding time
    cost_r  = cost_r(symbol, account, holding_hours=..., sl_distance_price=...)
    R_net   = R_gross - cost_r

is exact, not an approximation. This is the same arithmetic Session N used to recover
`R_gross = R_cached + charged_cost_r` from the caches (`scripts/recost_w7_validation.py`
module docstring), and it holds for the same reason.

WHAT `cost_r` CANNOT ANSWER, AND WHY THAT IS PUBLISHED
------------------------------------------------------
`BROKER_TRUE_COSTS_V1.json` carries 167 FTMO instruments but only 26 with a measured
spread; `model.py:349-352` hard-raises for the rest ("no measured spread ... Its spread is
unmeasured, not zero"). Measured 2026-07-29 against the live 12-sleeve market-expansion
allowlist: **9 are priceable on FTMO, 3 are not** — `mx_cadjpy_d1_volume_surge_reversal`,
`mx_eu50_cash_d1_volume_surge_reversal`, `mx_fra40_cash_d1_volume_surge_reversal`. Two of
those three (`EU50.cash`, `FRA40.cash`) are also absent from the bars archive entirely, so
they cannot even be generated. That is a coverage fact for the owner, not a gap to fill.

DAY AGGREGATION IS THE FIRST CLUSTERING CONTROL
-----------------------------------------------
Trades are not iid. `sub_xvol_pullback`'s 90 validated trades sit on 33 dates with up to 12
on one day and lag-1 rho 0.511; `crypto` 104 on 67 dates, rho 0.441 (B279). Collapsing to
one observation per day removes the within-day cluster before any statistic is computed.
The across-day dependence is handled downstream in `stats.py`.

(Correction recorded here because this module is where it would have bitten: the prompt for
this session attributes "up to 12 in one day, rho 0.511" to `metals_core`. Both primary
sources — `SESSION_R_LEARNING_LANE_RESULT.md:233-238` and `IMPLEMENTATION_STATE.md` B279 —
say `sub_xvol_pullback`. `metals_core` is a different sleeve with a different profile.)

ONE AXIS CHOICE, STATED BECAUSE IT IS EASY TO MISREAD AS A CONVENTION MISMATCH
-------------------------------------------------------------------------------
`scripts/recost_w7_validation.py:build_matrix_from` also aggregates by day-mean, but it
zero-fills a UNION calendar (`:903`, `daily[sl].get(day, 0.0)`) because it is assembling a
PORTFOLIO matrix, where a sleeve that did not trade contributes 0 R to the book that day.
This module omits non-trading days instead, because it measures a SINGLE sleeve's
expectancy per day it traded. The two answer different questions and the numbers differ:
zero-filling folds trade FREQUENCY into the mean, so a selective sleeve and a frequent one
with the same per-trade edge get different scores. For an admission decision about one
sleeve, frequency belongs in the sizing conversation, not in the expectancy estimate.

The consequence is worth naming: because rows here are trading days rather than calendar
days, a row-indexed fold cut is not an equal-calendar cut. See `folds.py`.
"""

from __future__ import annotations

import datetime as dt
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from src.costs import Coverage, CostTruthError, cost_r, load_broker_true_costs, weakest
from src.research_infra.walkforward.spec import GateSpec

__all__ = [
    "TradeRecord",
    "PricedTrade",
    "SleeveCoverage",
    "price_trades",
    "build_daily_panel",
]


@dataclass(frozen=True)
class TradeRecord:
    """One generated trade, before cost.

    Everything `cost_r` needs is required rather than defaulted, because every default here
    would be a silent assumption about someone's money.
    """

    sleeve: str
    #: BROKER symbol (e.g. "US500.cash"), not canonical. Cross the boundary with
    #: `symbol_map.build_broker_symbol_resolver(config)` — never by hand, and never by
    #: probing `mt5.symbol_info` on a canonical name (that mistake reported two sleeves of
    #: a funded book as untradeable when both are at full surface).
    symbol: str
    entry_utc: dt.datetime
    exit_utc: dt.datetime
    direction: int  # +1 long, -1 short
    #: Price distance to the stop. This is the R unit and the denominator of every cost.
    sl_distance_price: float
    entry_price: float
    #: Realised R BEFORE cost, from `primitives.simulate(..., cost=0.0)`.
    r_gross: float
    features: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.direction not in (1, -1):
            raise ValueError(f"direction must be +1 or -1, got {self.direction!r}")
        if not (self.sl_distance_price > 0):
            raise ValueError(
                f"sl_distance_price must be > 0 (it is the R unit and every cost's "
                f"denominator), got {self.sl_distance_price!r}"
            )
        if self.exit_utc < self.entry_utc:
            raise ValueError(f"exit_utc {self.exit_utc} precedes entry_utc {self.entry_utc}")

    @property
    def holding_hours(self) -> float:
        return (self.exit_utc - self.entry_utc).total_seconds() / 3600.0

    @property
    def side(self) -> str:
        return "LONG" if self.direction > 0 else "SHORT"

    def day(self, day_key: str = "entry") -> dt.date:
        return (self.entry_utc if day_key == "entry" else self.exit_utc).date()

    def spans(self) -> tuple[dt.date, dt.date]:
        """The trade's label span — what purging must not straddle."""
        return self.entry_utc.date(), self.exit_utc.date()


@dataclass(frozen=True)
class PricedTrade:
    trade: TradeRecord
    #: None when unpriced.
    cost_r: float | None
    coverage: Coverage | None
    status: str  # "priced" | "unpriced" | "blackout"
    reason: str | None = None
    #: The four cost terms in R — {commission_r, swap_r, spread_r, slippage_r} — kept
    #: rather than summed away. Added 2026-07-29 (B601) because the §2.2 cost-geometry
    #: prescription is not one repair but four different ones, and the total cannot tell
    #: them apart: commission scales as 1/stop so it is repaired by widening the stop;
    #: swap scales with nights held so it is repaired by the exit; spread is repaired by
    #: entry timing or by the session filter. Session N's whole correction — "the 31.6%
    #: was mostly swap, not commission" — was a statement nobody could have made from a
    #: total. None when unpriced.
    components: dict[str, float] | None = None
    #: Evidence class for each component.  A total class alone cannot distinguish a
    #: measured spread plus transferred commission from the inverse, and an unpriced
    #: trade is represented by ``status=unpriced`` / NOT_EVALUABLE rather than a zero.
    component_coverage: dict[str, Coverage] | None = None
    #: Swap-charged nights `cost_r` actually counted on the broker's wall clock. The
    #: carry question OD-3 turns on is this number, per trade, not a horizon assumption.
    swap_nights: float | None = None

    @property
    def r_net(self) -> float | None:
        if self.cost_r is None:
            return None
        return self.trade.r_gross - self.cost_r


@dataclass(frozen=True)
class SleeveCoverage:
    sleeve: str
    n_total: int
    n_priced: int
    n_unpriced: int
    n_blackout_dropped: int
    #: GROSS R of the blackout-dropped trades. Published because a count alone lets a
    #: material loss hide behind a neutral-looking number.
    blackout_r_gross: float
    coverage_frac: float
    weakest_coverage: Coverage | None
    measured_frac: float
    #: Counts over the evaluated population. NOT_EVALUABLE is a status, deliberately
    #: not a numeric Coverage member: no Measure exists for a refused row.
    coverage_class_counts: dict[str, int]
    unpriced_reasons: dict[str, int]

    def as_dict(self) -> dict[str, Any]:
        return {
            "sleeve": self.sleeve,
            "n_total": self.n_total,
            "n_priced": self.n_priced,
            "n_unpriced": self.n_unpriced,
            "n_blackout_dropped": self.n_blackout_dropped,
            "blackout_r_gross": round(self.blackout_r_gross, 5),
            "coverage_frac": round(self.coverage_frac, 6),
            "weakest_coverage": self.weakest_coverage.value if self.weakest_coverage else None,
            "measured_frac": round(self.measured_frac, 6),
            "coverage_class_counts": dict(sorted(self.coverage_class_counts.items())),
            "unpriced_reasons": dict(sorted(self.unpriced_reasons.items())),
        }


def _swap_nights(breakdown: Any) -> float | None:
    """Charged nights from `cost_r`'s own detail, or None if it did not record them.

    Read rather than recomputed: `model.rollover_nights` counts on the broker's wall
    clock with the triple-swap weekday, and a second implementation here would be a
    second chance to get the DST calendar wrong (`CLAUDE.md` §4).
    """
    try:
        n = (breakdown.detail.get("swap") or {}).get("nights_charged")
        return float(n) if n is not None else None
    except (AttributeError, TypeError, ValueError):  # pragma: no cover - defensive
        return None


def _blackout_drop(trade: TradeRecord, spec: GateSpec) -> bool:
    """Keyed on the ENTRY day only.

    Keying on the full [entry, exit] span made the drop depend on the SIMULATED exit date,
    so a trade entering 2026-02-25 was dropped if its path happened to run into March and
    kept if it stopped out quickly — a selection on the realised path, and duration
    correlates with outcome. Measured at 19 of 2,675 trades (0.71%). The entry day is
    outcome-independent, which is the property that matters; leakage into March is already
    prevented by the fold-boundary rule and by the purge.
    """
    lo, _hi = trade.spans()
    return bool(spec.blackout_hits(lo, lo))


def price_trades(
    trades: Iterable[TradeRecord],
    spec: GateSpec,
    *,
    costs: Any = None,
) -> tuple[list[PricedTrade], dict[str, SleeveCoverage]]:
    """Charge broker truth to every trade. Refuse, loudly and per-trade, where it cannot.

    Trades whose label span touches a `reserved_blackout` range are dropped before pricing
    and counted separately — they are not "unpriced", they are deliberately not looked at.
    """
    truth = costs if costs is not None else load_broker_true_costs()
    priced: list[PricedTrade] = []
    per: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"total": 0, "priced": 0, "unpriced": 0, "blackout": 0,
                 "blackout_r_gross": 0.0, "covs": [], "reasons": defaultdict(int)}
    )

    for t in trades:
        acc = per[t.sleeve]
        acc["total"] += 1
        if _blackout_drop(t, spec):
            acc["blackout"] += 1
            acc["blackout_r_gross"] += t.r_gross
            # Recorded, not vanished. An adversarial refuter moved 2,200 losing trades into
            # the blackout window and took a sleeve from +94.7 R to -2,105 R lifetime while
            # every scored number stayed frozen and the telemetry reported only a COUNT.
            # A count is not an amount.
            priced.append(PricedTrade(t, None, None, "blackout", "reserved_blackout"))
            continue
        # Cost in R is a price drag divided by the stop, so a larger declared stop is a
        # cheaper trade. Nothing downstream cross-checks the stop against the price.
        # Measured by an adversarial refuter: the same gold trades REJECT at a $5 stop and
        # ADMIT at $20, and `sl_distance_price=1e6` was accepted silently.
        lo, hi = spec.sl_over_price_band
        ratio = (t.sl_distance_price / t.entry_price) if t.entry_price else float("inf")
        if not (lo <= ratio <= hi):
            reason = (
                f"implausible_stop: sl/entry_price = {ratio:.3g}, outside the sealed band "
                f"[{lo:g}, {hi:g}]"
            )
            acc["unpriced"] += 1
            acc["reasons"][reason] += 1
            priced.append(PricedTrade(t, None, None, "unpriced", reason))
            continue
        try:
            if t.holding_hours is None:  # pragma: no cover - guarded by dataclass
                raise CostTruthError("holding_hours is None")
            b = cost_r(
                t.symbol,
                spec.account,
                t.holding_hours,
                sl_distance_price=t.sl_distance_price,
                entry_price=t.entry_price,
                side=t.side,
                entry_utc=t.entry_utc,
                # None keeps the flat 37-day snapshot and every refusal that goes with
                # it; a band charges the era measured for THIS trade's quarter instead.
                spread_band=getattr(spec, "spread_band", None),
                # None takes the measured composition (`v2_damped`). Both are carried so a
                # pre-2026-07-30 banded number can be reproduced byte-for-byte and so the
                # fitted exponent's envelope can be walked without editing source.
                spread_composition=getattr(spec, "spread_composition", None),
                spread_era_exponent=getattr(spec, "spread_era_exponent", None),
                # True makes an undecidable era a REFUSAL rather than a MODELLED stamp, so
                # the trade lands in `unpriced` and `coverage_policy` decides what that costs
                # the sleeve. This is how a population rule reaches the gate without any
                # driver reimplementing it -- see `era_population.py`.
                spread_require_decidable=bool(
                    getattr(spec, "spread_require_decidable", None) or False),
                costs=truth,
            )
        except CostTruthError as e:
            # The layer refused. Record why; never substitute a number.
            reason = str(e).split(".")[0][:120]
            acc["unpriced"] += 1
            acc["reasons"][reason] += 1
            priced.append(PricedTrade(t, None, None, "unpriced", reason))
            continue
        except (TypeError, ValueError, KeyError) as e:
            # `cost_r` does not guard everything: holding_hours=None escapes as TypeError
            # and `BrokerTrueCosts.symbols` raises a bare KeyError on an unknown account
            # (`model.py:129-130`). Treat any of these as a refusal, not a crash.
            reason = f"{type(e).__name__}: {str(e)[:100]}"
            acc["unpriced"] += 1
            acc["reasons"][reason] += 1
            priced.append(PricedTrade(t, None, None, "unpriced", reason))
            continue
        acc["priced"] += 1
        acc["covs"].append(b.total_r.coverage)
        priced.append(PricedTrade(
            t, float(b.total_r.value), b.total_r.coverage, "priced",
            components={
                "commission_r": float(b.commission_r.value),
                "swap_r": float(b.swap_r.value),
                "spread_r": float(b.spread_r.value),
                "slippage_r": float(b.slippage_r.value),
            },
            component_coverage={
                "commission_r": b.commission_r.coverage,
                "swap_r": b.swap_r.coverage,
                "spread_r": b.spread_r.coverage,
                "slippage_r": b.slippage_r.coverage,
            },
            swap_nights=_swap_nights(b),
        ))

    coverage: dict[str, SleeveCoverage] = {}
    for sleeve, a in per.items():
        looked_at = a["priced"] + a["unpriced"]
        covs = a["covs"]
        n_meas = sum(1 for c in covs if c is Coverage.MEASURED)
        class_counts = {c.value: sum(1 for got in covs if got is c) for c in Coverage}
        class_counts["NOT_EVALUABLE"] = a["unpriced"]
        coverage[sleeve] = SleeveCoverage(
            sleeve=sleeve,
            n_total=a["total"],
            n_priced=a["priced"],
            n_unpriced=a["unpriced"],
            n_blackout_dropped=a["blackout"],
            blackout_r_gross=a["blackout_r_gross"],
            coverage_frac=(a["priced"] / looked_at) if looked_at else 0.0,
            # Coverage does NOT propagate through arithmetic — `Measure` implements no
            # operators, so the caller must combine it. `src/costs/model.py:420-421` is the
            # only other place in the repo that does this; this is the second.
            weakest_coverage=weakest(*covs) if covs else None,
            measured_frac=(n_meas / len(covs)) if covs else 0.0,
            coverage_class_counts=class_counts,
            unpriced_reasons=dict(a["reasons"]),
        )
    return priced, coverage


def build_daily_panel(
    priced: Sequence[PricedTrade],
    spec: GateSpec,
) -> tuple[dict[str, dict[dt.date, float]], dict[str, dict[dt.date, int]]]:
    """Collapse priced trades to one observation per sleeve per day.

    Returns ``(daily, counts)`` where ``daily[sleeve][date]`` is the aggregated net R and
    ``counts[sleeve][date]`` is how many trades produced it. Unpriced trades are excluded
    from both: a day whose only trade could not be costed contributes no observation, and
    the coverage report is where that shows up.
    """
    buckets: dict[str, dict[dt.date, list[float]]] = defaultdict(lambda: defaultdict(list))
    for p in priced:
        if p.status != "priced":
            continue
        r = p.r_net
        if r is None:  # pragma: no cover - implied by status
            continue
        buckets[p.trade.sleeve][p.trade.day(spec.day_key)].append(r)

    agg = statistics.fmean if spec.day_aggregation == "mean" else sum
    daily: dict[str, dict[dt.date, float]] = {}
    counts: dict[str, dict[dt.date, int]] = {}
    for sleeve, days in buckets.items():
        daily[sleeve] = {d: float(agg(v)) for d, v in sorted(days.items())}
        counts[sleeve] = {d: len(v) for d, v in sorted(days.items())}
    return daily, counts
