"""Treatment arms: one dimension varied, everything else held.

AN ARM IS A CONTRACT, NOT A BACKTEST
-------------------------------------
Every arm receives the same :class:`~substrate.Intent` and returns an
:class:`Outcome`.  It may change the exit contract, the charged cost, the entry instant, or
whether the decision is admitted at all.  It may **not** change the signal, the direction,
the stop distance, or the bar archive -- those are the held tuple, and the harness asserts
it (:func:`Arm.holds`).

THE FILL AUTHORITY IS THE ESTATE'S, NOT THIS PACKAGE'S
-------------------------------------------------------
Every outcome comes from `walkforward.exits.replay`, the sanctioned labeller whose
`simulate_detail` parity is fuzzed at 4,000 random series
(`tests/research_infra/test_wf_exits_parity.py`).  This module writes no fill logic of its
own, which is why a control that reproduces the estate's published `r_gross` is meaningful
rather than circular.

COST
----
`cost_band=None` reproduces the estate's gross labelling byte-for-byte (the control's
requirement).  A band applies the wave-20 r1 quote-side correction --
``entry_price = bars[i].c + direction * spread`` at AG's era/hour-aware model -- which is
the estate's own economic convention (`r_new_mid`) and charges SPREAD ONLY.  Lane 4 §1's
caveat carries: commission and swap are not in it, and a flat residual haircut is wrong for
a multi-night sleeve.  The harness therefore reports treatment DIFFERENCES, where a common
residual cost cancels exactly, and refuses to publish an arm LEVEL as an economic claim.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from src.components.ultimate_book.admission import winsorize_R
from src.components.ultimate_book.execution_packets import (
    DEFAULT_EXIT_PROFILE,
    SLEEVE_EXIT_PROFILES,
)
from src.research_infra.walkforward.exits import ExitPolicy, replay
from src.research_infra.walkforward.quote_side import (
    BarQuote,
    SpreadUnavailable,
    replay_anchor,
    spread_for,
)

from .causality import CONTRACT_ONLY, AsOf, InfoInput, InformationSet
from .substrate import MAXBARS, TF_MINUTES, TF_NAME, Intent, Substrate

#: The declaration shared by every arm that charges a cost band.  AG's spread model is
#: evaluated at the decision's own instant (causal) but was FITTED over the whole archive,
#: so a 2019 decision is priced by a model that saw 2026.  That is model-in-sample leakage,
#: not feature leakage: it cannot manufacture a per-decision signal, and it is flagged on
#: every arm that carries it rather than mentioned once in a footnote.
COST_BAND_INFO = InformationSet(
    inputs=(
        InfoInput("exit_contract_parameters", AsOf.CONSTANT),
        InfoInput("intent.stop_dist", AsOf.DECISION_INSTANT),
        InfoInput("spread_model(symbol, entry_instant, band)", AsOf.FITTED_ON_FULL_HISTORY,
                  note="src.costs.spread_model (Session AG): tick anchor x bar-measured era "
                       "ratio x intraweek multiplier. Evaluated AT the decision instant; "
                       "fitted over 2000-2026."),
    ),
    rationale="cost is charged through the entry anchor; the value is knowable at the "
              "decision, the MODEL that produces it is not out-of-sample for early years.")


class PairingClass(str, Enum):
    """How two arms of a question are paired, and therefore what n means."""

    TRADE_PAIRED = "trade_paired"
    ENTRY_PAIRED = "entry_paired"
    SELECTION_PAIRED = "selection_paired"
    BOOK_PAIRED = "book_paired"


@dataclass(frozen=True)
class Outcome:
    """What one arm did with one decision."""

    admitted: bool
    #: R contributed to the book.  Exactly 0.0 when the arm refuses the decision -- that is
    #: the book difference a selection treatment makes, not a missing value.
    r: float
    exit_reason: str | None
    grid: str
    entry_utc: str
    refusal: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)


class ArmUnavailable(RuntimeError):
    """This arm cannot be evaluated on this decision (missing bars, missing spread).

    Raised rather than returned so the evaluator's complete-case rule cannot be bypassed:
    an intent unavailable to ANY arm of a question is dropped from ALL of them.
    """


# ---------------------------------------------------------------- the held tuple ----------
HELD_FIELDS = ("sleeve", "symbol", "timeframe", "decision_bar_iso", "direction", "stop_dist")


@dataclass(frozen=True)
class Arm:
    """One treatment arm.

    `declared_at` and `rationale` are not decoration: the multiplicity ledger counts every
    arm ever registered, and an arm with no declaration cannot be counted honestly.

    `information_set` is REQUIRED and is validated at construction.  An arm that cannot say
    what its treatment reads does not exist -- see :mod:`causality` for why that is enforced
    here rather than left to a reviewer.
    """

    name: str
    dimension: str
    rationale: str
    declared_at: str
    #: (intent, substrate) -> Outcome.  Raise ArmUnavailable when the decision cannot be
    #: evaluated under this arm.
    fn: Callable[[Intent, Substrate], Outcome]
    information_set: InformationSet = CONTRACT_ONLY
    is_control: bool = False

    def __post_init__(self) -> None:
        # Refuses at construction, not at reporting time: an arm that reads the future must
        # never reach a population, because by then its numbers exist and will be quoted.
        self.information_set.validate(self.name)

    def evaluate(self, it: Intent, sub: Substrate) -> Outcome:
        return self.fn(it, sub)

    @staticmethod
    def holds(a: Intent, b: Intent) -> bool:
        """Two arms are paired only if they were handed the identical held tuple."""
        return all(getattr(a, f) == getattr(b, f) for f in HELD_FIELDS)


# ---------------------------------------------------------------- contracts ----------------
def published_policy(it: Intent, *, maxbars: int = MAXBARS) -> ExitPolicy:
    """The contract the estate's own labels were produced under.

    Copied from `aa_estate_generate.py:260-274` via `r1_estate_rewalk.py`: plain
    stop+target+maxbars, plus the trail for the two `trailing_runner` sleeves.  The
    per-sleeve `time_stop_bars` is deliberately NOT applied -- `AQ_ESTATE_TRADES_V2`'s own
    `exit_contracts[*].time_stop_bars_applied` is `false` on every sleeve, and an arm that
    quietly added it would be comparing against a contract the estate never published.
    """
    prof = SLEEVE_EXIT_PROFILES.get(it.sleeve, DEFAULT_EXIT_PROFILE)
    if prof.get("policy") == "trailing_runner":
        trig, gap = prof.get("trigger_r"), prof.get("trail_gap_r")
        if trig is not None and gap is not None:
            return ExitPolicy(
                target_dist=it.target_dist,
                trail_arm=float(trig) * it.stop_dist,
                trail_gap=float(gap) * it.stop_dist,
                maxbars=maxbars,
                label="published_trailing_runner",
            )
    return ExitPolicy(target_dist=it.target_dist, maxbars=maxbars, label="published_plain")


def target_r_policy(it: Intent, k: float, *, maxbars: int = MAXBARS) -> ExitPolicy:
    """A fixed k-R target, which is exactly AD's `target_mode="fixed_r"` frontier cell."""
    return ExitPolicy(target_dist=k * it.stop_dist, maxbars=maxbars, label=f"target_{k:g}R")


def partial_be_policy(it: Intent, trigger_r: float, *, frac: float = 0.5,
                      be: bool = True, maxbars: int = MAXBARS) -> ExitPolicy:
    """The live `partial_be_runner` contract: scale `frac` off at `trigger_r`, stop to BE."""
    return ExitPolicy(
        target_dist=it.target_dist,
        partial_at_r=trigger_r,
        partial_frac=frac,
        be_stop_after_partial=be,
        maxbars=maxbars,
        label=f"partial_{trigger_r:g}R_{'be' if be else 'nobe'}",
    )


# ---------------------------------------------------------------- evaluation ---------------
def _anchor(it: Intent, close: float, band: str | None, at: dt.datetime) -> tuple[float | None, float | None]:
    """(entry_price, spread) under a cost band, or (None, None) for the gross convention."""
    if band is None:
        return None, None
    try:
        s = spread_for(it.symbol, at, account="FTMO", band=band)
    except SpreadUnavailable as exc:
        raise ArmUnavailable(f"no spread[{band}] for {it.symbol} @ {at.isoformat()}: {exc}") from None
    return replay_anchor(close, it.direction, s, BarQuote.BID), s


def run_on_own_grid(it: Intent, sub: Substrate, policy: ExitPolicy, band: str | None) -> Outcome:
    """Replay one decision on its own grid under `policy`, charged at `band`."""
    got = sub.resolve(it)
    if got is None:
        raise ArmUnavailable(f"no bars for {it.symbol}/{TF_NAME[it.timeframe]} @ {it.decision_bar_iso}")
    s, i = got
    at = sub.entry_instant(it)
    entry_price, spread = _anchor(it, s.bars[i].c, band, at)
    res = replay(s.bars, i, it.direction, stop_dist=it.stop_dist, policy=policy,
                 entry_price=entry_price)
    return Outcome(
        admitted=True,
        r=winsorize_R(res.r_gross),
        exit_reason=res.exit_reason,
        grid=it.tf_name,
        entry_utc=at.isoformat(),
        detail={"spread": spread, "bars_held": res.bars_held, "mfe_r": res.mfe_r,
                "mae_r": res.mae_r, "policy": policy.label},
    )


def run_on_grid(it: Intent, sub: Substrate, timeframe: int, policy_fn: Callable[[Intent, int], ExitPolicy],
                band: str | None, *, defer_to_broker_hour: int | None = None,
                server: str = "FTMO-Server3") -> Outcome:
    """Replay the same decision on ANOTHER grid, optionally deferring the entry.

    `defer_to_broker_hour` reproduces `run_book.py --entry-hour`: the intent is held and
    re-proposed until the broker clock reaches the target hour, so the fill lands at the
    first bar of `timeframe` that CLOSES at or after that instant.  Deferral is bounded by
    the sleeve's own entry-lateness window (2 h on H4, 12 h on D1) exactly as the flag is;
    a decision that cannot be filled inside it is unavailable rather than silently late.
    """
    # `resolve_rule` fails closed on an unregistered server -- never hardcode +3 (CLAUDE.md §4).
    from src.utils.broker_clock import resolve_rule, utc_to_broker_naive

    try:
        rule = resolve_rule(server)
    except Exception as exc:
        raise ArmUnavailable(f"broker clock unresolvable for {server}: {exc}") from None

    got = sub.resolve_on(it, timeframe)
    if got is None:
        raise ArmUnavailable(f"no {TF_NAME[timeframe]} bars covering {it.symbol} @ {it.entry_utc}")
    s, j = got
    step = dt.timedelta(minutes=TF_MINUTES[timeframe])

    if defer_to_broker_hour is not None:
        limit = dt.timedelta(hours=12 if it.timeframe == 1440 else 2)
        deadline = sub.entry_instant(it) + limit
        k = j
        while k < len(s.times) - 2:
            close_at = s.times[k] + step
            if close_at > deadline:
                raise ArmUnavailable("deferral would exceed the sleeve's entry-lateness window")
            if utc_to_broker_naive(close_at, rule).hour == defer_to_broker_hour:
                j = k
                break
            k += 1
        else:
            raise ArmUnavailable("no bar closes at the target broker hour inside the window")

    at = s.times[j] + step
    policy = policy_fn(it, timeframe)
    entry_price, spread = _anchor(it, s.bars[j].c, band, at)
    res = replay(s.bars, j, it.direction, stop_dist=it.stop_dist, policy=policy,
                 entry_price=entry_price)
    return Outcome(
        admitted=True,
        r=winsorize_R(res.r_gross),
        exit_reason=res.exit_reason,
        grid=TF_NAME[timeframe],
        entry_utc=at.isoformat(),
        detail={"spread": spread, "bars_held": res.bars_held, "policy": policy.label,
                "deferred_to_hour": defer_to_broker_hour},
    )


# ---------------------------------------------------------------- arm builders --------------
def exit_arm(name: str, policy_fn: Callable[[Intent], ExitPolicy], *, band: str | None,
             dimension: str, rationale: str, declared_at: str, is_control: bool = False,
             information_set: InformationSet | None = None) -> Arm:
    def _fn(it: Intent, sub: Substrate) -> Outcome:
        return run_on_own_grid(it, sub, policy_fn(it), band)

    info = information_set or (COST_BAND_INFO if band else CONTRACT_ONLY)
    return Arm(name=name, dimension=dimension, rationale=rationale, declared_at=declared_at,
               fn=_fn, information_set=info, is_control=is_control)


def selection_arm(base: Arm, name: str, predicate: Callable[[Intent, Substrate], tuple[bool, str]],
                  *, dimension: str, rationale: str, declared_at: str,
                  information_set: InformationSet | None = None) -> Arm:
    """`base` with a generation-side admission gate in front of it.

    A refused decision returns `r = 0.0` and `admitted = False`.  That is the true book
    difference and it is also the trap: the zeros carry no information and must never be
    counted as sample size (:mod:`paired_stats` enforces it for SELECTION_PAIRED).
    """

    def _fn(it: Intent, sub: Substrate) -> Outcome:
        ok, why = predicate(it, sub)
        if not ok:
            # Still evaluate the base arm so the harness can report what was forgone; the
            # contributed R is 0.0 either way.
            base_out = base.evaluate(it, sub)
            return Outcome(admitted=False, r=0.0, exit_reason=None, grid=base_out.grid,
                           entry_utc=base_out.entry_utc, refusal=why,
                           detail={"forgone_r": base_out.r})
        return base.evaluate(it, sub)

    return Arm(name=name, dimension=dimension, rationale=rationale, declared_at=declared_at,
               fn=_fn, information_set=information_set or COST_BAND_INFO)


#: The RECON-adjudicated slippage constant.  `RECON_SLIPPAGE_ADJUDICATION_V1` measured
#: `expected_slippage_r = 0.02` correct within 4 % (+0.0208 on 18,978 tick-matched rows) and
#: overturned both competing estimates. A declared constant, hence causally free.
EXPECTED_SLIPPAGE_R = 0.02


def spread_geometry_predicate(limit: float, band: str = "mid", *,
                              lag_days: int = 0) -> Callable[[Intent, Substrate], tuple[bool, str]]:
    """`spread_r = spread_price / stop_dist <= limit`, the wave-13 generation-side floor.

    Same quantity `spread_geometry.py` computes and the same default limit
    (`SPREAD_GEOMETRY_FLOOR_DEFAULT_LIMIT = 0.10`, `broker_net_cost_engine`'s literal).

    `lag_days` is the TEMPORAL COMPANION hook: the gate decides today's admission on the
    spread it would have seen `lag_days` earlier.  A gate whose measured value evaporates
    under a one-day lag is reading contemporaneous state; that may still be legitimate live,
    but it is a different claim and the harness makes it visible instead of assuming it.
    """

    def _pred(it: Intent, sub: Substrate) -> tuple[bool, str]:
        at = sub.entry_instant(it) - dt.timedelta(days=lag_days)
        try:
            s = spread_for(it.symbol, at, account="FTMO", band=band)
        except SpreadUnavailable as exc:
            raise ArmUnavailable(f"no spread for the floor test: {exc}") from None
        spread_r = s / it.stop_dist if it.stop_dist > 0 else float("inf")
        if spread_r > limit:
            return False, f"spread_geometry_floor spread_r={spread_r:.4f}>{limit}"
        return True, ""

    return _pred


def ex_ante_cost_predicate(limit: float = 0.20, band: str = "mid", *,
                           lag_days: int = 0) -> Callable[[Intent, Substrate], tuple[bool, str]]:
    """The EX-ANTE COST GATE, ported from the funnel to the sleeve surface.

    `candidate_funnel_analysis.py:52` gates the funnel at `cost_r <= 0.20` and Lane 4 §2.2
    measured it removing 245,134 rows whose kept-vs-removed expectancy gap is -0.4224 against
    -0.0928 R/fill.  Nothing had ever asked the same question of the SLEEVE surface, where
    the trades are real and the cost is the estate's measured one.

    `cost_r = spread_price/stop_dist + EXPECTED_SLIPPAGE_R`.  Commission and swap are NOT in
    it: the estate's median commission and swap are both 0.0 for an intraday trade
    (`G_PAIRED_AND_COSTLINE_V1.json`) and a flat swap term would be wrong per sleeve by up to
    0.37 R/night.  The gate is therefore a LOWER bound on modelled cost, which makes it a
    conservative gate: every decision it refuses would be refused by a fuller cost model too.
    """

    def _pred(it: Intent, sub: Substrate) -> tuple[bool, str]:
        at = sub.entry_instant(it) - dt.timedelta(days=lag_days)
        try:
            s = spread_for(it.symbol, at, account="FTMO", band=band)
        except SpreadUnavailable as exc:
            raise ArmUnavailable(f"no spread for the cost gate: {exc}") from None
        cost_r = (s / it.stop_dist if it.stop_dist > 0 else float("inf")) + EXPECTED_SLIPPAGE_R
        if cost_r > limit:
            return False, f"ex_ante_cost_gate cost_r={cost_r:.4f}>{limit}"
        return True, ""

    return _pred
