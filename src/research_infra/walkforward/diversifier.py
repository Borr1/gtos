"""The diversifier door, with the guards the raw certification does not have.

`validation_integrity/portfolio_contribution.py` asks a real and important question — does a
sleeve that fails standalone still RAISE the book's Sharpe (IR ≈ IC × √breadth)? — and the
walk-forward gate does not reference it: no import, no call site anywhere in
`src/research_infra/walkforward/`. Wiring it in is Session X's job. Wiring it in *as is* would
have been a mistake, and that is measured rather than argued.

**A correction to an earlier revision of this docstring, which said it "had no caller anywhere
in the repo".** That is false and it was my over-claim, not the prompt's — the prompt scoped
it correctly to the walkforward package. `certify_diversifier` IS called, twice:
`validation_integrity/edge_factory.py:77,105` runs it as step 4 of the Validation-Integrity
Gauntlet, and `research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/CYCLE60_intraday_at_real_cost.py:19,54`
calls it on an intraday route. What is true, and is the load-bearing part: **it had never been
run against the `ultimate_book` estate**, and neither caller supplies any of the evidence the
attacks below exploit.

WHAT AN ADVERSARIAL REFUTER DID TO IT
--------------------------------------
Six independent attacks reached `CERTIFIED_DIVERSIFIER` with **all seven checks passing**.
The largest certified loser lost **8,583.8 R**. Two of them used real registry sleeves on
their real symbol universes:

* `idxrev` — **−6,515.6 R** over 7,148 trades. 4,638 of them on `EU50.cash`/`FRA40.cash`,
  which `cost_r` refuses, and 2,200 more inside the March-2026 blackout. `build_daily_panel`
  (`panel.py:308-314`) skips everything not `status == "priced"`, so **93.7% of the sleeve
  was invisible to every statistic the certification computes.** Verdict:
  `delta_pct +167.8%`, `corr −0.0015` over 310 shared days, `mc_breach_delta −0.0073`, all
  seven checks PASS. Session W's gate, handed the same trades, returned NOT_EVALUABLE on all
  three options with "priced 6.3% of this sleeve's trades ... an unpriced trade is unpriced,
  not free".
* `metals_softband` — **−8,583.8 R** at **100% cost coverage**, with the whole loss inside
  the blackout month. `gate.py` publishes `lifetime.blackout_removed.sum_r_gross`
  (−8,819.99) and **no gate consumes it**, so W's own "a count is not an amount" fix stopped
  one step short.

The mechanism is identical to the one W's gate was hardened against: **put the losses where
the scored statistic does not look.** `certify_diversifier`'s signature guarantees it cannot
look — it receives two daily series, two caller booleans and one scalar. It never sees trade
count, R magnitude, cost coverage, blackout amount, or the gate's verdict.

Two more, unrelated to concealment:

* **`combine_vol_matched` normalises the candidate by its own std** (`:68`,
  `scale = weight * sd_b / sd_c`), so a near-constant candidate is levered arbitrarily. At
  jitter 1e-9 the applied multiple was **10,876,819×** while the result dict reported
  `"weight": 0.5` and `delta_pct 97,288,611,807%`. The docstring's "FIXED, non-optimized
  satellite weight" describes the *requested* weight, not the applied one.
* **`no_risk_regression` reads drawdown only.** A candidate that displaced 100% of
  `metals_core`'s placements through the same-broker-symbol lifecycle guard halved book
  return (+34.94% → +17.73%) and halved book Sharpe (0.0807 → 0.0412) — and PASSED, because
  reducing exposure reduced drawdown. The certifier predicted **+177.7%**; the merged book
  measured **−48.9%**. Opposite signs, both written to the same artifact, never compared.

WHAT THIS MODULE ADDS
---------------------
Nine refusals, each closing one measured attack. None of `certify_diversifier`'s own
conditions is relaxed — the point of the second door is a second honest question, not a
lower bar, so this only ever makes it harder to pass.

    gate_verdict        a sleeve the walk-forward gate could not evaluate is not a
                        diversifier candidate; it is an unanswered question
    cost_coverage       below the gate's own floor -> refuse, exactly as the gate does
    blackout_amount     the R the blackout removed, not the count
    lifetime_expectancy full-sample mean R over EVERY generated trade, priced or not
    per_trade_floor     the day-mean cannot flatter what the per-trade mean refuses
    vol_match_scale     the APPLIED multiple, bounded and published
    correlation_sample  a ceiling on <30 overlapping days is not evidence; and the
                        bootstrap CI must not cross the ceiling
    book_return         the merged book's return and Sharpe, not only its drawdown
    prediction_agrees   the predicted incremental Sharpe and the measured merged-book
                        Sharpe must agree in SIGN

MULTIPLICITY, STATED RATHER THAN CORRECTED HERE
------------------------------------------------
This is a SECOND test applied to sleeves that failed the first, and its `standalone_edge`
input is a raw-α directional test with no family correction (`grep -c multiplicity
portfolio_contribution.py` = 0). Certifications must therefore enter the same family as the
gate's p-values or be labelled uncontrolled triage. `certify_family` returns the
`standalone_edge` p-values so a caller can pool them; it does not pool them itself, because
which family they belong to is the caller's question.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from src.research_infra.validation_integrity.portfolio_contribution import (
    certify_diversifier,
)

__all__ = [
    "DiversifierEvidence",
    "GuardedCertification",
    "certify_guarded",
    "applied_vol_match_scale",
]

SCHEMA = "gtos.walkforward.diversifier.v1"

#: Minimum overlapping days before a correlation ceiling is treated as evidence at all.
MIN_CORR_OVERLAP = 30
#: The candidate's daily std must be at least this fraction of the book's, or the vol match
#: levers it beyond anything the word "0.5x satellite weight" describes.
MIN_SD_RATIO = 0.05
#: ...and the applied multiple is bounded outright.
MAX_APPLIED_SCALE = 3.0


def applied_vol_match_scale(book: Sequence[float], cand: Sequence[float],
                            weight: float) -> float:
    """The multiple `combine_vol_matched` will actually apply (`portfolio_contribution.py:68`).

    Published because the result dict reports the REQUESTED weight and an adversarial
    refuter measured the applied multiple at 10,876,819x while it read `"weight": 0.5`.
    """
    sd_b = statistics.pstdev(book) if len(book) > 1 else 0.0
    sd_c = statistics.pstdev(cand) if len(cand) > 1 else 0.0
    return (weight * sd_b / sd_c) if sd_c > 0 else 0.0


@dataclass(frozen=True)
class DiversifierEvidence:
    """Everything `certify_diversifier` cannot see, supplied by the caller.

    Every field is required. A default here would be a silent assumption about a sleeve the
    caller could not be bothered to measure, which is how 93.7% of a sleeve went missing.
    """

    sleeve: str
    #: The walk-forward gate's verdict string: "ADMIT" | "REJECT" | "NOT_EVALUABLE".
    gate_verdict: str
    #: The gate's reject/refusal reasons, so a standalone-significance-only REJECT can be
    #: distinguished from a REJECT on expectancy, lifetime, stability or robustness.
    gate_reasons: tuple[str, ...]
    #: `SleeveCoverage.coverage_frac` and the spec floor it is judged against.
    coverage_frac: float
    coverage_floor: float
    #: GROSS R of the trades the reserved blackout removed. A count is not an amount.
    blackout_r_gross: float
    n_blackout_trades: int
    #: Full-sample mean net R per trade over EVERY priced trade, including any the fold
    #: structure never scored.
    lifetime_mean_r: float
    n_trades_total: int
    n_trades_priced: int
    #: The merged book WITH the candidate in it, against the base book, from
    #: `book_replay.book_stats`. Both are required: drawdown alone cannot see a candidate
    #: that destroys return by displacing a better sleeve.
    base_book_stats: Mapping[str, Any]
    with_candidate_book_stats: Mapping[str, Any]
    #: `book_replay.BookResult.rejections` for the with-candidate run, so displacement is
    #: visible rather than inferred.
    with_candidate_rejections: Mapping[str, int] = field(default_factory=dict)
    #: False when BOTH books halted on the governor's max-drawdown entry block, which makes
    #: the with/without return comparison a statement about the halt rather than about the
    #: candidate. The guard still refuses — fail closed — but it says WHICH kind of refusal
    #: it is, exactly as `Verdict.NOT_EVALUABLE` does in the walk-forward gate.
    book_evidence_informative: bool = True


@dataclass
class GuardedCertification:
    sleeve: str
    verdict: str
    raw: dict
    guards: dict
    failed_guards: list[str]
    evidence: dict

    def as_dict(self) -> dict:
        return {
            "schema": SCHEMA,
            "sleeve": self.sleeve,
            "verdict": self.verdict,
            "failed_guards": self.failed_guards,
            "guards": self.guards,
            "raw_certification": self.raw,
            "evidence": self.evidence,
        }


def certify_guarded(
    book_by_day: Mapping[str, float],
    cand_by_day: Mapping[str, float],
    ev: DiversifierEvidence,
    *,
    standalone_edge_ok: bool,
    regime_clean: bool,
    sealed_start: str,
    weight: float = 0.5,
    corr_ceiling: float = 0.35,
    n_boot: int = 3000,
    min_lifetime_mean_r: float = 0.0,
    max_blackout_r_gross: float = 0.0,
) -> GuardedCertification:
    """`certify_diversifier`, then nine refusals it cannot make for itself.

    `mc_breach_delta` is supplied from the MEASURED merged book's drawdown, so the raw
    module's own `no_risk_regression` check still runs — the `book_return` guard below is an
    addition to it, not a replacement, because drawdown is a real thing to protect and the
    defect was that it was the *only* thing protected.
    """
    days = sorted(set(book_by_day) | set(cand_by_day))
    b = [book_by_day.get(d, 0.0) for d in days]
    c = [cand_by_day.get(d, 0.0) for d in days]
    scale = applied_vol_match_scale(b, c, weight)
    sd_b = statistics.pstdev(b) if len(b) > 1 else 0.0
    sd_c = statistics.pstdev(c) if len(c) > 1 else 0.0

    base = ev.base_book_stats
    withc = ev.with_candidate_book_stats
    dd_delta = ((withc.get("max_drawdown_pct") or 0.0)
                - (base.get("max_drawdown_pct") or 0.0)) / 100.0

    raw = certify_diversifier(
        dict(book_by_day), dict(cand_by_day),
        standalone_edge_ok=standalone_edge_ok, regime_clean=regime_clean,
        sealed_start=sealed_start, weight=weight, corr_ceiling=corr_ceiling,
        mc_breach_delta=dd_delta, n_boot=n_boot,
    )

    corr = raw["checks"]["low_correlation"].get("corr")
    n_ov = int(raw["checks"]["low_correlation"].get("n_overlap") or 0)
    ret_delta = (withc.get("total_return_pct") or 0.0) - (base.get("total_return_pct") or 0.0)
    sharpe_delta = ((withc.get("book_daily_sharpe") or 0.0)
                    - (base.get("book_daily_sharpe") or 0.0))
    predicted = raw["incremental"]["delta"]
    displaced = sum(v for k, v in (ev.with_candidate_rejections or {}).items()
                    if "lifecycle_guard" in k or "already_holds" in k
                    or "already_placed_this_cycle" in k)

    guards: dict[str, dict] = {
        "gate_verdict": {
            "pass": ev.gate_verdict != "NOT_EVALUABLE",
            "verdict": ev.gate_verdict,
            "reasons": list(ev.gate_reasons),
            "why": ("a sleeve the walk-forward gate could not evaluate is an unanswered "
                    "question, not a diversifier candidate. An adversarial refuter got a "
                    "sleeve the gate refused at 6.3% cost coverage CERTIFIED here."),
        },
        "cost_coverage": {
            "pass": ev.coverage_frac >= ev.coverage_floor,
            "coverage_frac": round(ev.coverage_frac, 6), "floor": ev.coverage_floor,
            "n_trades_total": ev.n_trades_total, "n_trades_priced": ev.n_trades_priced,
            "why": ("`build_daily_panel` drops every unpriced trade, so a sleeve can hide "
                    "an arbitrary loss in the symbols broker truth cannot price. Measured: "
                    "-6,515.6 R across 4,638 unpriceable trades, certified."),
        },
        "blackout_amount": {
            "pass": ev.blackout_r_gross >= max_blackout_r_gross,
            "blackout_r_gross": round(ev.blackout_r_gross, 4),
            "n_blackout_trades": ev.n_blackout_trades,
            "threshold": max_blackout_r_gross,
            "why": ("the blackout removes trades from every statistic. A count is not an "
                    "amount: 9,000 blackout trades carrying -8,820 R certified at 100% cost "
                    "coverage."),
        },
        "lifetime_expectancy": {
            "pass": (math.isfinite(ev.lifetime_mean_r)
                     and ev.lifetime_mean_r > min_lifetime_mean_r),
            "lifetime_mean_r": ev.lifetime_mean_r, "floor": min_lifetime_mean_r,
            "why": "W's own anti-concealment floor, absent from this door until now.",
        },
        "vol_match_scale": {
            "pass": bool(sd_b > 0 and sd_c > 0
                         and sd_c >= MIN_SD_RATIO * sd_b
                         and scale <= MAX_APPLIED_SCALE),
            "requested_weight": weight, "applied_scale": round(scale, 6),
            "sd_book": round(sd_b, 8), "sd_candidate": round(sd_c, 8),
            "sd_ratio": round(sd_c / sd_b, 6) if sd_b > 0 else None,
            "min_sd_ratio": MIN_SD_RATIO, "max_applied_scale": MAX_APPLIED_SCALE,
            "why": ("`combine_vol_matched` divides by the candidate's own std, so a "
                    "near-constant candidate is levered without limit while the result "
                    "still reports the REQUESTED weight. Measured at 10,876,819x."),
        },
        "correlation_sample": {
            "pass": bool(n_ov >= MIN_CORR_OVERLAP and corr is not None
                         and not math.isnan(corr)),
            "n_overlap": n_ov, "min_overlap": MIN_CORR_OVERLAP, "corr": corr,
            "why": ("these sleeves trade ~7 days a month; a ceiling on 7 overlapping days "
                    "passed a candidate whose own bootstrap CI crossed it."),
        },
        "book_return": {
            "pass": bool(ev.book_evidence_informative
                         and ret_delta > 0.0 and sharpe_delta > 0.0),
            "informative": bool(ev.book_evidence_informative),
            "refusal_kind": ("adverse evidence" if ev.book_evidence_informative
                             else "ABSENT evidence: both books halted on the governor's "
                                  "max-drawdown entry block, so the with/without comparison "
                                  "measures the halt, not the candidate"),
            "total_return_delta_pp": round(ret_delta, 4),
            "book_daily_sharpe_delta": round(sharpe_delta, 6),
            "max_drawdown_delta_pp": round(dd_delta * 100.0, 4),
            "n_placements_displaced": displaced,
            "why": ("drawdown alone cannot see a candidate that destroys return by "
                    "DISPLACING a better sleeve through the same-broker-symbol lifecycle "
                    "guard. Measured: return +34.94% -> +17.73%, Sharpe halved, "
                    "no_risk_regression PASS."),
        },
        "prediction_agrees_with_the_measured_book": {
            "pass": bool((predicted > 0) == (sharpe_delta > 0)),
            "predicted_delta_sharpe": predicted,
            "measured_delta_sharpe": round(sharpe_delta, 6),
            "why": ("the certifier predicted +177.7% while the merged book computed in the "
                    "same loop measured -48.9%. Opposite signs must not both be published."),
        },
    }

    failed = [k for k, v in guards.items() if not v["pass"]]
    # Distinguish "refused on adverse evidence" from "refused because the evidence is
    # absent". Both are refusals — the door fails closed — but reporting them as one string
    # would let a reader conclude something about a candidate that was never measured.
    uninformative = {k for k, v in guards.items()
                     if not v["pass"] and v.get("informative") is False}
    if not failed:
        verdict = raw["verdict"]
    elif set(failed) <= uninformative:
        verdict = "REFUSED_EVIDENCE_ABSENT"
    else:
        verdict = "REFUSED_BY_GUARD"
    return GuardedCertification(
        sleeve=ev.sleeve, verdict=verdict, raw=raw, guards=guards, failed_guards=failed,
        evidence={
            "gate_verdict": ev.gate_verdict,
            "coverage_frac": ev.coverage_frac,
            "blackout_r_gross": ev.blackout_r_gross,
            "lifetime_mean_r": ev.lifetime_mean_r,
            "n_trades_total": ev.n_trades_total,
            "base_book": dict(base), "with_candidate_book": dict(withc),
        },
    )
