"""The paired statistics layer: error bars that survive an adversary.

FOUR THINGS THIS MODULE REFUSES TO DO, EACH BECAUSE IT IS A KNOWN WAY TO MANUFACTURE AN
ANSWER FROM A PAIRED DESIGN
-----------------------------------------------------------------------------------------
1. **It refuses to treat a degenerate arm pair as a measurement.**  If two arms produce the
   same number on every decision, the difference SD is 0 and the naive t is undefined or
   infinite.  :func:`paired_summary` returns ``verdict = "INERT"`` and no p-value.  The
   discordance rate is reported on every question whether it is degenerate or not, because
   a *nearly* inert arm (say 3 % discordant) is the dangerous case: it produces a finite,
   tiny SD and a huge t off a handful of rows.

2. **It refuses to hide how thin a contrast is.**  A SELECTION treatment's delta is exactly
   0 on every decision both arms take, so a result can rest on a small discordant subset
   while `n` reads in the thousands.  ``discordance`` and ``n_informative`` are reported on
   every contrast, and a contrast below 5 % discordance is stamped ``NEAR_INERT`` however
   large its n.
   *The power basis is deliberately NOT the discordant subset.*  The estimand is the mean
   difference per ARRIVING decision -- that is the quantity with a calendar meaning -- so the
   SD is taken over all arrivals, zeros included, and the rate is the arrival rate.  An
   earlier draft powered selection contrasts off the discordant subset while dividing the
   arrival rate by the discordance, which is wrong by about 1/discordance^2 and would have
   overstated Q4/Q7's calendar cost roughly tenfold.

3. **It refuses to price an i.i.d. standard error as if the deltas were independent.**
   Sleeve deltas cluster inside a day (Lane 4 §3.2: the armed three are 0.646-correlated
   within a day).  The reported interval is a **day-block bootstrap** -- resample whole
   trading days with replacement -- and the i.i.d. SE is carried alongside purely so the
   ratio between them is visible.  When the block SE is materially larger, the i.i.d. one
   was a fiction.

4. **It refuses to let a question stop early without paying for it.**  Sequential looks at
   accumulating data inflate type-I error; :class:`SequentialMonitor` spends alpha on a
   Lan-DeMets O'Brien-Fleming schedule, so a question stopped at 40 % information has been
   tested at a materially stricter z than one that runs to its horizon.

THE MULTIPLICITY LEDGER COUNTS ARMS, NOT CONCLUSIONS
------------------------------------------------------
`phase8/receipts/CANDIDATE_FAMILY_V1.json`'s ratified rule is the all-declared basis at the
sealed alpha = 0.10.  :class:`MultiplicityLedger` enumerates every arm ever registered --
including the ones that were run and abandoned -- and applies Benjamini-Hochberg over that
family.  An arm registered and never reported still counts, which is the whole point.
"""

from __future__ import annotations

import json
import math
import random
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

#: Power design used everywhere: two-sided alpha = 0.05, power 80 %.
#: n = k (sigma/mu)^2 with k = (z_{0.975} + z_{0.80})^2.  Same constant Lane 4 §4 used, so
#: this harness's days-to-answer numbers are comparable with its projections.
POWER_K = 7.848932

_Z975 = 1.959963984540054
_Z80 = 0.8416212335729143


def _phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def two_sided_p(z: float) -> float:
    return 2.0 * (1.0 - _phi(abs(z)))


def z_for_two_sided_alpha(alpha: float) -> float:
    """Inverse normal at 1 - alpha/2, by bisection (no scipy dependency on the VPS)."""
    target = 1.0 - alpha / 2.0
    lo, hi = 0.0, 40.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if _phi(mid) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


# ------------------------------------------------------------------ paired summary --------
@dataclass
class PairedSummary:
    n: int
    n_informative: int
    discordance: float
    mean: float
    sd: float
    se_iid: float | None
    se_block: float | None
    ci95_block: tuple[float, float] | None
    t_iid: float | None
    t_block: float | None
    p_block: float | None
    n_blocks: int
    #: Share of |delta| carried by the largest 1 % of rows.  A paired result that is really
    #: five rows in a trench coat shows up here and nowhere else.
    top1pct_share: float | None
    #: Kish effective sample size on |delta|; equals n for a flat contribution profile.
    n_eff_kish: float | None
    verdict: str
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        d = dict(self.__dict__)
        d["ci95_block"] = list(self.ci95_block) if self.ci95_block else None
        return d


def day_block_bootstrap(values: Sequence[float], blocks: Sequence[Any], *,
                        resamples: int = 2000, seed: int = 20260812,
                        pad_to: int | None = None) -> tuple[float, tuple[float, float]]:
    """Bootstrap the mean by resampling whole blocks (days) with replacement.

    `pad_to` divides each resample's sum by a FIXED denominator instead of the resample's
    own count.  It is not used for the mean interval (where the ratio estimator is the right
    one) and exists for the book-level daily aggregation, where the denominator is the
    number of calendar days and must not move with the resample.
    """
    grouped: dict[Any, list[float]] = {}
    for v, b in zip(values, blocks):
        grouped.setdefault(b, []).append(v)
    keys = list(grouped)
    if len(keys) < 2:
        return float("nan"), (float("nan"), float("nan"))
    rng = random.Random(seed)
    means: list[float] = []
    for _ in range(resamples):
        tot, cnt = 0.0, 0
        for _ in range(len(keys)):
            vs = grouped[keys[rng.randrange(len(keys))]]
            tot += math.fsum(vs)
            cnt += len(vs)
        denom = pad_to if pad_to else cnt
        if denom:
            means.append(tot / denom)
    means.sort()
    lo = means[int(0.025 * (len(means) - 1))]
    hi = means[int(0.975 * (len(means) - 1))]
    se = statistics.pstdev(means) if len(means) > 1 else float("nan")
    return se, (lo, hi)


def paired_summary(deltas: Sequence[float], blocks: Sequence[Any], *,
                   informative_only: bool = False, resamples: int = 2000,
                   seed: int = 20260812, zero_tol: float = 1e-12) -> PairedSummary:
    """The honest summary of one paired contrast.

    `informative_only` marks a SELECTION_PAIRED contrast.  It changes what is REPORTED (the
    discordant count and the discordant SD are surfaced as a caveat) and deliberately does
    NOT change what is computed: the mean, the SD and the interval are all over the arriving
    stream, because that is the quantity a calendar answers.  See point 2 of the module
    docstring for the 1/discordance^2 error this replaced.
    """
    n = len(deltas)
    notes: list[str] = []
    if n == 0:
        return PairedSummary(0, 0, 0.0, float("nan"), float("nan"), None, None, None, None,
                             None, None, 0, None, None, "NO_DATA", ["empty contrast"])

    nz = [i for i, d in enumerate(deltas) if abs(d) > zero_tol]
    discordance = len(nz) / n
    mean_all = statistics.fmean(deltas)

    if not nz:
        return PairedSummary(
            n=n, n_informative=0, discordance=0.0, mean=0.0, sd=0.0, se_iid=None,
            se_block=None, ci95_block=None, t_iid=None, t_block=None, p_block=None,
            n_blocks=len(set(blocks)), top1pct_share=None, n_eff_kish=None, verdict="INERT",
            notes=["every delta is exactly 0: the two arms are the same contract under two "
                   "names. No p-value is defensible and none is reported."])

    # THE ESTIMAND IS UNIFORM ACROSS ALL FOUR PAIRING CLASSES: the mean difference per
    # ARRIVING decision.  The SD used for power is therefore always the SD over arriving
    # decisions -- including the exact zeros a selection treatment produces.
    #
    # An earlier draft of this module powered SELECTION contrasts off the discordant subset
    # and divided the arrival rate by the discordance.  That is wrong by a factor of about
    # 1/discordance^2: sd_all^2 ~ discordance * E[d^2 | discordant], so the two routes agree
    # only when the discordant mean is zero.  At Q4's measured 31 % discordance it would have
    # overstated the calendar cost ~10x.  The discordant SD is still reported, as a caveat
    # about what the contrast rests on -- never as the power basis.
    sd = statistics.stdev(deltas) if n > 1 else 0.0
    se_iid = (sd / math.sqrt(n)) if n > 1 else None
    se_block, ci = day_block_bootstrap(deltas, blocks, resamples=resamples, seed=seed)
    blks = list(blocks)
    n_eff_basis = len(nz) if informative_only else n
    if informative_only:
        inf_vals = [deltas[i] for i in nz]
        sd_inf = statistics.stdev(inf_vals) if len(inf_vals) > 1 else 0.0
        notes.append(
            f"SELECTION contrast: {len(nz)}/{n} rows discordant ({discordance:.2%}); "
            f"SD among discordant rows {sd_inf:.4f} against {sd:.4f} over all arrivals. "
            f"Power is computed on the ARRIVING stream, which is the calendar quantity.")

    absd = sorted((abs(d) for d in deltas), reverse=True)
    tot = math.fsum(absd)
    k1 = max(1, int(round(0.01 * n)))
    top1 = (math.fsum(absd[:k1]) / tot) if tot > 0 else None
    sq = math.fsum(x * x for x in absd)
    kish = ((tot * tot) / sq) if sq > 0 else None

    t_iid = (mean_all / se_iid) if se_iid else None
    t_block = (mean_all / se_block) if se_block and se_block == se_block and se_block > 0 else None
    p_block = two_sided_p(t_block) if t_block is not None else None

    verdict = "MEASURED"
    if discordance < 0.05:
        verdict = "NEAR_INERT"
        notes.append(
            f"only {discordance:.2%} of decisions are discordant -- the contrast rests on "
            f"{len(nz)} rows. Treat the interval as a small-sample interval regardless of n.")
    if top1 is not None and top1 > 0.5:
        notes.append(f"the top 1 % of rows carry {top1:.1%} of the total |delta|: "
                     f"concentration, not a population effect.")
    if se_iid and se_block and se_block == se_block and se_iid > 0:
        ratio = se_block / se_iid
        notes.append(f"block SE / iid SE = {ratio:.3f}"
                     + (" -- the iid interval was optimistic." if ratio > 1.15 else ""))

    return PairedSummary(
        n=n, n_informative=n_eff_basis, discordance=discordance, mean=mean_all, sd=sd,
        se_iid=se_iid, se_block=se_block, ci95_block=ci, t_iid=t_iid, t_block=t_block,
        p_block=p_block, n_blocks=len(set(blks)), top1pct_share=top1, n_eff_kish=kish,
        verdict=verdict, notes=notes)


def unpaired_reference(a: Sequence[float], b: Sequence[float]) -> dict[str, Any]:
    """What the same question would cost WITHOUT pairing -- the speed-up's denominator."""
    pooled = list(a) + list(b)
    sd = statistics.pstdev(pooled) if len(pooled) > 1 else float("nan")
    return {"n": len(pooled), "sd_unpaired": sd}


# ------------------------------------------------------------------ power ------------------
def n_to_detect(sd: float, effect: float, *, alpha: float = 0.05, power_k: float = POWER_K) -> float:
    """Paired-difference n for `effect` at two-sided `alpha`, 80 % power."""
    if effect <= 0 or not (sd == sd) or sd <= 0:
        return float("inf")
    k = power_k if abs(alpha - 0.05) < 1e-12 else (z_for_two_sided_alpha(alpha) + _Z80) ** 2
    return k * (sd / effect) ** 2


def time_to_answer(sd: float, effect: float, rate_per_month: float, *,
                   alpha: float = 0.05) -> dict[str, float]:
    """Weeks/months to a powered answer at a measured arrival rate.

    `sd` is always the SD of the paired difference over ARRIVING decisions and
    `rate_per_month` the rate those decisions arrive at, for every pairing class.  There is
    deliberately no discordance argument: see the note in :func:`paired_summary`.
    """
    n = n_to_detect(sd, effect, alpha=alpha)
    months = n / rate_per_month if rate_per_month > 0 else float("inf")
    return {"n_required": n, "months": months, "weeks": months * 4.348,
            "decisions_per_month": rate_per_month}


# ------------------------------------------------------------------ sequential -------------
def obf_boundary(info_fraction: float, alpha: float = 0.05) -> float:
    """Lan-DeMets O'Brien-Fleming z-boundary at information fraction t.

    Spending function alpha*(t) = 2 - 2 Phi(z_{alpha/2} / sqrt(t)); the boundary is the
    two-sided critical z that spends exactly that much cumulative alpha.  At t = 1 it
    returns z_{alpha/2}, so a question run to its full horizon is tested at its nominal
    level and an early look is not.
    """
    t = min(max(float(info_fraction), 1e-6), 1.0)
    z_alpha = z_for_two_sided_alpha(alpha)
    spent = 2.0 - 2.0 * _phi(z_alpha / math.sqrt(t))
    spent = min(max(spent, 1e-12), alpha)
    return z_for_two_sided_alpha(spent)


@dataclass
class SequentialMonitor:
    """One question under sequential monitoring.

    `planned_n` is the information horizon declared BEFORE the first look -- the whole
    alpha-spending argument is void if it moves afterwards, so :meth:`look` refuses an
    information fraction above 1.0 by clamping and records that it did.
    """

    question_id: str
    planned_n: int
    alpha: float = 0.05
    looks: list[dict[str, Any]] = field(default_factory=list)

    def look(self, summary: PairedSummary, *, label: str = "") -> dict[str, Any]:
        n_info = summary.n_informative or 0
        t = min(1.0, n_info / self.planned_n) if self.planned_n else 0.0
        z_bound = obf_boundary(t, self.alpha)
        z_obs = summary.t_block if summary.t_block is not None else float("nan")
        crossed = (z_obs == z_obs) and abs(z_obs) >= z_bound
        rec = {
            "look": len(self.looks) + 1,
            "label": label,
            "information_fraction": round(t, 5),
            "n_informative": n_info,
            "z_observed_block": None if z_obs != z_obs else round(z_obs, 4),
            "z_boundary_obf": round(z_bound, 4),
            "nominal_z_at_alpha": round(z_for_two_sided_alpha(self.alpha), 4),
            # NAMED AGAINST ZERO ON PURPOSE. The sequential monitor answers "is there an
            # effect at all"; the question's pass bar answers "is it big enough to act on".
            # A contrast can legitimately be STOP_EFFECT_VS_ZERO and UNRESOLVED against its
            # own bar, and conflating the two is how a statistically real, economically
            # irrelevant effect gets promoted.
            "decision": ("STOP_EFFECT_VS_ZERO" if crossed else
                         ("HORIZON_REACHED_NO_EFFECT_VS_ZERO" if t >= 1.0 else "CONTINUE")),
            "what_this_does_not_say": ("crossing the boundary does NOT mean the effect "
                                       "clears the question's pass bar; read "
                                       "verdict_against_own_bar for that"),
            "mean": None if summary.mean != summary.mean else round(summary.mean, 6),
            "ci95_block": list(summary.ci95_block) if summary.ci95_block else None,
        }
        self.looks.append(rec)
        return rec


# ------------------------------------------------------------------ multiplicity ------------
@dataclass
class MultiplicityLedger:
    """Every arm ever registered, and BH over that declared family.

    The ledger is APPEND-ONLY on disk.  A re-run that registers the same arm name updates
    its p-value and never removes a row, so the family cannot shrink by forgetting.
    """

    path: Path
    alpha: float = 0.10
    rows: dict[str, dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path, alpha: float = 0.10) -> "MultiplicityLedger":
        led = cls(path=Path(path), alpha=alpha)
        if led.path.is_file():
            for line in led.path.read_text().splitlines():
                if line.strip():
                    r = json.loads(line)
                    led.rows[r["arm"]] = r
        return led

    def register(self, arm: str, *, question: str, dimension: str, declared_at: str,
                 rationale: str, p_value: float | None = None, reported: bool = False) -> None:
        prev = self.rows.get(arm, {})
        self.rows[arm] = {
            "arm": arm, "question": question, "dimension": dimension,
            "declared_at": declared_at, "rationale": rationale,
            "first_seen": prev.get("first_seen", declared_at),
            "p_value": p_value if p_value is not None else prev.get("p_value"),
            "reported": bool(reported or prev.get("reported")),
        }

    def flush(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w") as fh:
            for _, r in sorted(self.rows.items()):
                fh.write(json.dumps(r, sort_keys=True) + "\n")

    def benjamini_hochberg(self) -> dict[str, Any]:
        """BH over the DECLARED family -- every registered arm, tested or not.

        Arms with no p-value still enter the denominator: an arm you registered and did not
        report is a look you took.  That is the estate's all-declared basis
        (`CANDIDATE_FAMILY_V1.json -> ratified_rule`), applied to treatments.
        """
        family = sorted(self.rows)
        m = len(family)
        tested = sorted(((r["p_value"], a) for a, r in self.rows.items()
                         if r.get("p_value") is not None))
        out: dict[str, Any] = {"declared_family_size": m,
                               "n_with_p_value": len(tested), "alpha": self.alpha,
                               "results": {}}
        crit_rank = 0
        for rank, (p, _a) in enumerate(tested, start=1):
            if p <= self.alpha * rank / m:
                crit_rank = rank
        for rank, (p, a) in enumerate(tested, start=1):
            q = min(1.0, p * m / rank)
            out["results"][a] = {"p": p, "rank": rank, "bh_threshold": self.alpha * rank / m,
                                 "q_approx": q, "admits": rank <= crit_rank}
        out["n_admitting"] = sum(1 for v in out["results"].values() if v["admits"])
        return out


# ------------------------------------------------------------------ helpers ---------------
def rate_per_month(n: int, span_months: float) -> float:
    return n / span_months if span_months > 0 else float("nan")


def span_months(iso_dates: Iterable[str]) -> float:
    ds = sorted(iso_dates)
    if len(ds) < 2:
        return 0.0
    import datetime as _dt

    a = _dt.date.fromisoformat(ds[0][:10])
    b = _dt.date.fromisoformat(ds[-1][:10])
    return max((b - a).days / 30.4375, 1e-9)
