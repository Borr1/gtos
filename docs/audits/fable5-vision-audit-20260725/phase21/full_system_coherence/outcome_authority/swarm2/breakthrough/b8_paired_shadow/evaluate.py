"""The paired evaluator: complete-case pairing, and the proof that the arms are paired.

THE COMPLETE-CASE RULE
----------------------
An intent that any arm cannot evaluate is dropped from EVERY arm of that question.  Without
this the arms silently run on different populations and the "difference" mixes a treatment
effect with a composition effect -- the exact failure the brief names.  Drops are counted
per arm and per reason and land in the receipt, because a question whose control arm is
complete and whose treatment arm drops 30 % of the population is not a paired question and
the receipt should say so out loud.

THE PAIRING PROOF
-----------------
:func:`pairing_proof` is run on every question and its output is part of the receipt.  It
answers four things an adversary would ask:

* **Are the arms actually different?**  discordance -- the share of decisions where the two
  arms disagree.  0.0 means the arm pair is inert and the harness says so instead of
  producing a p-value.
* **Is the variance reduction earned or assumed?**  the measured correlation between the two
  arms' per-decision outcomes, and the identity ``Var(D) = Var(A) + Var(B) - 2 Cov(A,B)``
  checked numerically.  A claimed 4.25x noise cut that does not fall out of the measured
  covariance is arithmetic, not evidence.
* **Did the pairing survive the population?**  the held tuple is re-checked per decision.
* **Is the result a population effect or a handful of rows?**  top-1 % share and Kish n_eff,
  from :mod:`paired_stats`.
"""

from __future__ import annotations

import collections
import math
import statistics
from dataclasses import dataclass, field
from typing import Any, Sequence

from .arms import Arm, ArmUnavailable, Outcome, PairingClass
from .paired_stats import (
    PairedSummary,
    day_block_bootstrap,
    paired_summary,
    rate_per_month,
    span_months,
    time_to_answer,
)
from .substrate import Intent, Substrate


@dataclass
class ArmResult:
    arm: str
    outcomes: dict[tuple, Outcome] = field(default_factory=dict)
    drops: collections.Counter = field(default_factory=collections.Counter)

    @property
    def n(self) -> int:
        return len(self.outcomes)


@dataclass
class QuestionResult:
    question_id: str
    pairing_class: PairingClass
    control: str
    treatment: str
    n_paired: int
    summary: PairedSummary
    pairing_proof: dict[str, Any]
    arm_levels: dict[str, dict[str, Any]]
    drops: dict[str, dict[str, int]]
    rate: dict[str, Any]
    days_to_answer: dict[str, Any]
    extra: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "question_id": self.question_id,
            "pairing_class": self.pairing_class.value,
            "control_arm": self.control,
            "treatment_arm": self.treatment,
            "n_paired": self.n_paired,
            "paired_summary": self.summary.as_dict(),
            "pairing_proof": self.pairing_proof,
            "arm_levels": self.arm_levels,
            "drops": self.drops,
            "arrival_rate": self.rate,
            "days_to_answer": self.days_to_answer,
            **({"extra": self.extra} if self.extra else {}),
        }


def evaluate_arms(intents: Sequence[Intent], arms: Sequence[Arm], sub: Substrate,
                  *, progress: bool = False) -> tuple[dict[str, ArmResult], list[Intent]]:
    """Evaluate every arm on every intent, then intersect to the complete cases."""
    results = {a.name: ArmResult(arm=a.name) for a in arms}
    for n, it in enumerate(intents):
        for a in arms:
            try:
                results[a.name].outcomes[it.key] = a.evaluate(it, sub)
            except ArmUnavailable as exc:
                results[a.name].drops[str(exc).split(":")[0][:80]] += 1
            except Exception as exc:  # a broken arm must not masquerade as a null result
                results[a.name].drops[f"ERROR {type(exc).__name__}: {exc}"[:120]] += 1
        if progress and n and n % 5000 == 0:
            print(f"    .. {n}/{len(intents)}", flush=True)

    common = set.intersection(*[set(r.outcomes) for r in results.values()]) if results else set()
    kept = [it for it in intents if it.key in common]
    for r in results.values():
        r.outcomes = {k: v for k, v in r.outcomes.items() if k in common}
    return results, kept


def pairing_proof(a_vals: Sequence[float], b_vals: Sequence[float],
                  deltas: Sequence[float]) -> dict[str, Any]:
    """Prove the arms are genuinely paired rather than silently identical or independent."""
    n = len(deltas)
    if n < 2:
        return {"n": n, "verdict": "TOO_FEW"}
    # Sample (n-1) convention throughout, matching the estate's published SDs. The identity
    # Var(D) = Va + Vb - 2 Cov holds exactly under it as long as Cov uses the same divisor.
    va = statistics.variance(a_vals)
    vb = statistics.variance(b_vals)
    vd = statistics.variance(deltas)
    ma, mb = statistics.fmean(a_vals), statistics.fmean(b_vals)
    cov = math.fsum((x - ma) * (y - mb) for x, y in zip(a_vals, b_vals)) / (n - 1)
    rho = cov / math.sqrt(va * vb) if va > 0 and vb > 0 else None
    identity = va + vb - 2.0 * cov
    disc = sum(1 for d in deltas if abs(d) > 1e-12) / n
    sd_unpaired = math.sqrt((va + vb) / 2.0)
    sd_paired = math.sqrt(vd)
    return {
        "n": n,
        "discordance": round(disc, 6),
        "sd_arm_control": round(math.sqrt(va), 6),
        "sd_arm_treatment": round(math.sqrt(vb), 6),
        "sd_paired_difference": round(sd_paired, 6),
        "sd_unpaired_reference": round(sd_unpaired, 6),
        "noise_reduction_x": (round(sd_unpaired / sd_paired, 4) if sd_paired > 0 else None),
        "corr_between_arms": (round(rho, 6) if rho is not None else None),
        "variance_identity_var_d_minus_(va+vb-2cov)": round(vd - identity, 12),
        "variance_identity_holds": abs(vd - identity) < 1e-9 * max(1.0, vd),
        "verdict": (
            "INERT_ARMS" if disc == 0.0 else
            "SUSPECT_INDEPENDENT" if (rho is not None and rho < 0.2) else
            "PAIRED"
        ),
        "reading": (
            "sd_paired_difference is the SD the power calculation uses. "
            "noise_reduction_x is what the pairing bought, measured, not assumed; it falls "
            "out of corr_between_arms by Var(D) = Va + Vb - 2 Cov, checked above."
        ),
    }


def run_question(question_id: str, control: Arm, treatment: Arm, intents: Sequence[Intent],
                 sub: Substrate, *, pairing_class: PairingClass,
                 effects: Sequence[float] = (0.10, 0.05, 0.02, 0.01),
                 alpha: float = 0.05, seed: int = 20260812,
                 shadow_rate_per_month: float | None = None,
                 progress: bool = False) -> QuestionResult:
    """One control/treatment contrast, end to end."""
    arms = [control, treatment]
    results, kept = evaluate_arms(intents, arms, sub, progress=progress)
    if not kept:
        raise RuntimeError(f"{question_id}: no complete cases")

    a = [results[control.name].outcomes[i.key] for i in kept]
    b = [results[treatment.name].outcomes[i.key] for i in kept]
    a_r = [o.r for o in a]
    b_r = [o.r for o in b]
    deltas = [y - x for x, y in zip(a_r, b_r)]
    blocks = [i.decision_day for i in kept]

    informative_only = pairing_class is PairingClass.SELECTION_PAIRED
    summ = paired_summary(deltas, blocks, informative_only=informative_only, seed=seed)
    proof = pairing_proof(a_r, b_r, deltas)

    # THE RATE THAT MATTERS IS THE FORWARD ONE.  A question's calendar cost is set by how
    # fast a DEPLOYED shadow accumulates its decisions, not by the sleeve's whole-history
    # average -- symbol surfaces, archives and the estate itself have all changed.  Both are
    # reported; days-to-answer uses forward.
    all_months = span_months([i.entry_utc for i in kept])
    fwd = [i for i in kept if i.entry_utc[:4] >= "2025"]
    fwd_months = span_months([i.entry_utc for i in fwd]) if len(fwd) > 1 else 0.0
    obs_rate = rate_per_month(len(kept), all_months)
    fwd_rate = rate_per_month(len(fwd), fwd_months) if fwd_months > 0 else 0.0
    use_rate = shadow_rate_per_month or (fwd_rate if fwd_rate > 0 else obs_rate)
    rate = {"n": len(kept), "n_days": len(set(blocks)),
            "span_months_all": round(all_months, 3),
            "decisions_per_month_all_history": round(obs_rate, 3),
            "n_forward_2025plus": len(fwd), "span_months_forward": round(fwd_months, 3),
            "decisions_per_month_forward": round(fwd_rate, 3),
            "rate_used_for_days_to_answer": round(use_rate, 3),
            "rate_basis": ("caller-supplied shadow rate" if shadow_rate_per_month
                           else ("forward 2025+" if fwd_rate > 0 else "all history"))}
    dta = {f"{e:g}R": time_to_answer(summ.sd, e, use_rate, alpha=alpha) for e in effects}

    # THE SPEED-UP, MEASURED RATHER THAN PROJECTED.  The counterfactual is the SAME question
    # asked without pairing -- two independent samples of the same size -- which needs
    # 2 * sd_unpaired^2 in place of sd_paired^2 for the difference of two means.
    sd_unp = proof.get("sd_unpaired_reference")
    dta_unpaired: dict[str, Any] = {}
    if sd_unp:
        for e in effects:
            t_unp = time_to_answer(sd_unp * math.sqrt(2.0), e, use_rate, alpha=alpha)
            t_p = dta[f"{e:g}R"]
            dta_unpaired[f"{e:g}R"] = {
                **t_unp,
                "speedup_x_vs_paired": (round(t_unp["weeks"] / t_p["weeks"], 2)
                                        if t_p["weeks"] > 0 else None)}

    levels = {}
    for nm, vals, outs in ((control.name, a_r, a), (treatment.name, b_r, b)):
        reasons = collections.Counter(o.exit_reason for o in outs if o.exit_reason)
        levels[nm] = {
            "n": len(vals),
            "mean_r": round(statistics.fmean(vals), 6),
            "sd_r": round(statistics.pstdev(vals), 6),
            "sum_r": round(math.fsum(vals), 4),
            "admitted": sum(1 for o in outs if o.admitted),
            "exit_reasons": dict(sorted(reasons.items())),
        }

    return QuestionResult(
        question_id=question_id, pairing_class=pairing_class, control=control.name,
        treatment=treatment.name, n_paired=len(kept), summary=summ, pairing_proof=proof,
        arm_levels=levels,
        drops={nm: dict(r.drops) for nm, r in results.items()},
        rate=rate, days_to_answer=dta,
        extra={"days_to_answer_if_unpaired": dta_unpaired} if dta_unpaired else {})


# ------------------------------------------------------------------ book pairing ------------
def book_daily_difference(intents: Sequence[Intent], control: Arm, treatment: Arm,
                          sub: Substrate, *, cap_control, cap_treatment,
                          seed: int = 20260812) -> dict[str, Any]:
    """A BOOK_PAIRED contrast: two throttle regimes over the same arriving decision stream.

    `cap_*` are callables ``(intents_sorted) -> set of accepted intent keys``.  The daily
    difference is ``sum(R | treatment book) - sum(R | control book)`` on the same day, so
    every decision both books take cancels exactly and the day's difference is entirely the
    throttle's doing.  The resampling unit is the DAY, which is also the unit of the
    throttle -- a per-trade bootstrap here would be wrong twice over.
    """
    results, kept = evaluate_arms(intents, [control, treatment], sub)
    order = sorted(kept, key=lambda i: (i.entry_utc, i.sleeve, i.symbol))
    acc_c = cap_control(order)
    acc_t = cap_treatment(order)

    by_day_c: dict[str, float] = collections.defaultdict(float)
    by_day_t: dict[str, float] = collections.defaultdict(float)
    for it in order:
        if it.key in acc_c:
            by_day_c[it.decision_day] += results[control.name].outcomes[it.key].r
        if it.key in acc_t:
            by_day_t[it.decision_day] += results[treatment.name].outcomes[it.key].r

    days = sorted(set(by_day_c) | set(by_day_t))
    diffs = [by_day_t.get(d, 0.0) - by_day_c.get(d, 0.0) for d in days]
    summ = paired_summary(diffs, days, seed=seed)
    return {
        "n_days": len(days),
        "n_decisions": len(order),
        "accepted_control": len(acc_c),
        "accepted_treatment": len(acc_t),
        "control_total_R": round(math.fsum(by_day_c.values()), 4),
        "treatment_total_R": round(math.fsum(by_day_t.values()), 4),
        "daily_difference": summ.as_dict(),
        "pairing_proof": pairing_proof(
            [by_day_c.get(d, 0.0) for d in days],
            [by_day_t.get(d, 0.0) for d in days], diffs),
    }
