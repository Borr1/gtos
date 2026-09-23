"""Causality: the layer that would have caught the lookahead a permutation null could not.

WHY THIS IS A HARNESS FEATURE AND NOT A RESEARCHER'S CHECKLIST
---------------------------------------------------------------
A sibling lane's only OOS-predictive finding was killed as a **lookahead artifact**.  Its
regime features aggregated over every candidate on the trading day -- including candidates
generated *after* the trade being scored.  It survived walk-forward, strictly-prior
training, daily prequential refit, and **four separate permutation nulls**.

It survived them because **a permutation null permutes labels.**  A leak that is present in
every permutation is invisible to it: the null and the alternative are contaminated
identically, so the contrast between them is clean while both are wrong.  Two things killed
it, and neither is a null:

* **lag the feature one day** -- rho +0.1539 -> -0.0432, p 0.25;
* **split the day at a cutoff and fit PAST-only against FUTURE-only on identical subsets** --
  PAST +0.0051 (p 0.90), FUTURE +0.1822 (p 1e-05).

**THE STANDARD, RECORDED HERE SO IT IS NOT RE-LEARNED: a permutation null is NECESSARY AND
NOT SUFFICIENT.**  Any arm whose treatment reads a same-day aggregate must additionally pass
a temporal test, and this module runs that test automatically rather than trusting a
researcher to remember it.

This matters more for a forward-shadow instrument than for a backtest.  In real time the
data genuinely arrives -- it just does not arrive in the order a backtest assumed -- so a
same-day aggregate feels available when it is not, and nothing in the log looks wrong.

WHAT IS ENFORCED, AND WHAT IS ONLY FLAGGED
-------------------------------------------
Enforced at registration (an arm that fails does not register):

* no declared input may be `POST_DECISION`;
* an input marked `same_day_aggregate` must name its cutoff discipline.

Flagged, loudly, but not fatal, because the estate's own instruments carry it:

* `FITTED_ON_FULL_HISTORY` -- a model input (AG's spread model, a ridge, an era table) fitted
  over a span that includes the future of the decision it is evaluated at.  This is
  in-sample MODEL leakage rather than in-sample FEATURE leakage: it cannot manufacture a
  per-decision signal the way a same-day aggregate can, but it is not nothing, and an arm
  that carries it is stamped so no downstream reader has to guess.
"""

from __future__ import annotations

import datetime as dt
import statistics
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Sequence


class AsOf(str, Enum):
    """When an input is knowable, relative to the decision instant it is used at."""

    PRE_DECISION = "pre_decision"          # strictly earlier bars/ticks
    DECISION_INSTANT = "decision_instant"  # the quote/clock at the decision itself
    CONSTANT = "constant"                  # a declared constant or a clock rule
    FITTED_ON_FULL_HISTORY = "fitted_on_full_history"   # flagged, see module docstring
    POST_DECISION = "post_decision"        # refused


@dataclass(frozen=True)
class InfoInput:
    name: str
    as_of: AsOf
    #: True when the value is an aggregate over the decision's own day.  This is the exact
    #: shape that killed the sibling lane's finding, so it forces a cutoff declaration.
    same_day_aggregate: bool = False
    #: Required when `same_day_aggregate` is True: how the day is cut so nothing later than
    #: the decision enters.  "none" is a legal answer only for a strictly causal aggregate
    #: (e.g. an arrival-ordered ledger), and it must be spelled out.
    cutoff_discipline: str = ""
    note: str = ""


class CausalityRefused(RuntimeError):
    """An arm whose declared information set cannot be honoured."""


@dataclass(frozen=True)
class InformationSet:
    """What an arm's TREATMENT reads.  Not what its outcome is measured from.

    The distinction is the whole point and is easy to get backwards: every arm's *label*
    comes from bars after the decision -- that is the outcome, and it is meant to.  What may
    never come from after the decision is the *treatment rule*: which contract is applied,
    whether the decision is admitted, when the entry is taken.
    """

    inputs: tuple[InfoInput, ...]
    rationale: str = ""

    def validate(self, arm_name: str) -> dict[str, Any]:
        bad = [i for i in self.inputs if i.as_of is AsOf.POST_DECISION]
        if bad:
            raise CausalityRefused(
                f"{arm_name}: treatment reads post-decision input(s) "
                f"{[i.name for i in bad]}. An arm that cannot be computed at the decision "
                f"instant is not a treatment, it is an outcome.")
        undeclared = [i for i in self.inputs if i.same_day_aggregate and not i.cutoff_discipline]
        if undeclared:
            raise CausalityRefused(
                f"{arm_name}: same-day aggregate input(s) {[i.name for i in undeclared]} "
                f"with no cutoff_discipline. This is the exact shape of the lookahead that "
                f"survived four permutation nulls; declare the cutoff or drop the input.")
        flags = [i.name for i in self.inputs if i.as_of is AsOf.FITTED_ON_FULL_HISTORY]
        aggs = [i.name for i in self.inputs if i.same_day_aggregate]
        return {
            "arm": arm_name,
            "inputs": [{"name": i.name, "as_of": i.as_of.value,
                        "same_day_aggregate": i.same_day_aggregate,
                        "cutoff_discipline": i.cutoff_discipline, "note": i.note}
                       for i in self.inputs],
            "verdict": ("CAUSAL_WITH_MODEL_IN_SAMPLE_FLAG" if flags else "CAUSAL"),
            "fitted_on_full_history_inputs": flags,
            "same_day_aggregate_inputs": aggs,
            "temporal_companion_required": bool(aggs) or bool(flags),
            "rationale": self.rationale,
        }


#: The declaration for a pure exit-contract treatment: a contract chosen in advance, applied
#: to a decision, reading nothing but the decision's own geometry.
CONTRACT_ONLY = InformationSet(
    inputs=(
        InfoInput("exit_contract_parameters", AsOf.CONSTANT,
                  note="a target multiple / scale-out trigger declared before the look"),
        InfoInput("intent.stop_dist", AsOf.DECISION_INSTANT,
                  note="the decision's own risk distance, fixed when it was generated"),
    ),
    rationale="the treatment is a contract, not a prediction; it reads no market state "
              "beyond what the decision already carried.")


# ------------------------------------------------------------------ temporal screens --------
def within_day_split(deltas: Sequence[float], instants: Sequence[str],
                     days: Sequence[str]) -> dict[str, Any]:
    """The PAST-only / FUTURE-only screen, generalised to a paired contrast.

    Each decision is placed in the earlier or later half of its OWN trading day (cut at that
    day's median decision instant), and the paired effect is measured on each half
    separately.  A treatment whose effect lives almost entirely in the later half is the
    signature of a same-day aggregate: late decisions are the ones a day-level aggregate can
    "see", because by then most of the day has happened.

    THIS IS A SCREEN AND NOT A PROOF, and the harness says so wherever it prints it.  A real
    intraday effect (a session, a rollover, a liquidity profile) produces the same asymmetry
    honestly.  What the screen buys is that the asymmetry is always ON THE PAGE, so nobody
    has to remember to look for it.
    """
    by_day: dict[str, list[int]] = {}
    for k, d in enumerate(days):
        by_day.setdefault(d, []).append(k)
    early: list[float] = []
    late: list[float] = []
    for d, idxs in by_day.items():
        if len(idxs) == 1:
            early.append(deltas[idxs[0]])
            continue
        ts = sorted(idxs, key=lambda k: instants[k])
        cut = len(ts) // 2
        early.extend(deltas[k] for k in ts[:cut])
        late.extend(deltas[k] for k in ts[cut:])

    def _s(v: list[float]) -> dict[str, Any]:
        if len(v) < 2:
            return {"n": len(v), "mean": (v[0] if v else None), "t": None}
        m = statistics.fmean(v)
        se = statistics.stdev(v) / (len(v) ** 0.5)
        return {"n": len(v), "mean": round(m, 6), "se": round(se, 6),
                "t": (round(m / se, 3) if se > 0 else None)}

    e, l = _s(early), _s(late)
    gap = None
    if e.get("mean") is not None and l.get("mean") is not None:
        gap = round(float(l["mean"]) - float(e["mean"]), 6)
    return {
        "screen": "within_day_past_vs_future",
        "early_half": e, "late_half": l, "late_minus_early": gap,
        "reading": ("A treatment effect concentrated in the LATE half is the signature of a "
                    "same-day aggregate leaking into the treatment rule. It is a screen, "
                    "not a verdict: a genuine intraday effect looks identical. Investigate "
                    "when the halves disagree in SIGN or by more than the pooled effect."),
        "flag": ("SIGN_DISAGREEMENT" if (e.get("mean") is not None and l.get("mean") is not None
                                         and float(e["mean"]) * float(l["mean"]) < 0)
                 else "OK"),
    }


def lag_companion_available(info: InformationSet) -> bool:
    """A lag test is only meaningful for a treatment that reads time-indexed market state.

    A pure exit contract has nothing to lag: lagging "use a 4R target" by a day is still
    "use a 4R target".  The harness reports NOT_APPLICABLE rather than fabricating a test,
    because a fabricated companion that always passes is worse than no companion.
    """
    return any(i.as_of in (AsOf.DECISION_INSTANT, AsOf.FITTED_ON_FULL_HISTORY)
               and i.name != "intent.stop_dist" for i in info.inputs)


@dataclass
class CausalityLedger:
    """Every arm's declaration and verdict, alongside the multiplicity ledger."""

    rows: dict[str, dict[str, Any]] = field(default_factory=dict)

    def register(self, arm_name: str, info: InformationSet) -> dict[str, Any]:
        rec = info.validate(arm_name)
        rec["lag_companion_applicable"] = lag_companion_available(info)
        self.rows[arm_name] = rec
        return rec

    def as_dict(self) -> dict[str, Any]:
        flagged = [a for a, r in self.rows.items() if r["fitted_on_full_history_inputs"]]
        aggs = [a for a, r in self.rows.items() if r["same_day_aggregate_inputs"]]
        return {
            "standard": (
                "A permutation null is NECESSARY AND NOT SUFFICIENT. A leak present in every "
                "permutation is invisible to it. Every arm declares its information set; any "
                "arm reading a same-day aggregate or a full-history-fitted model additionally "
                "carries the temporal companions."),
            "n_arms_declared": len(self.rows),
            "arms_with_full_history_fitted_inputs": flagged,
            "arms_with_same_day_aggregates": aggs,
            "declarations": self.rows,
        }
