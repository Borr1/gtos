"""The fixing machine's head: every gate failure becomes a prescription with evidence.

WHY THIS MODULE EXISTS
----------------------
`WAVE_6_WORKING_AGREEMENT.md` §0, quoting Borhen: *"the option of them not working is
simply not allowed from me."* The orchestrator conceded the point — this programme built a
killing machine and never built a fixing machine. Every instrument it produced (the
admission gate, the refuters, the multiplicity correction, the brake-only learning rule) is
a rejection instrument, and none of them ever answered *"what would make this work?"*

`FOURTH_REVIEW.md` §2.2 is the answer, and §4.1 says it is cheap: the gate already computes
every number involved and then **flattens them into verdict-reason strings**
(`gate.py:836-878`, `SleeveVerdict.reasons`). Diagnostic mode just stops flattening.

    coverage        -> DATA_PATH            never "unjudgeable"
    expectancy/day  -> COST_GEOMETRY        when gross > 0: the edge exists, cost eats it
                    -> EXIT_REPAIR          when gross <= 0 but the excursion is there
                    -> INVERSE_TEST         when there is no excursion either
    expectancy/trade-> PER_TRADE_QUALITY    day-mean fine, a few bad trades drag it
    lifetime        -> REGIME_GATE          the rule changed sign somewhere in history
    stability       -> FOLD_CONDITIONING    what distinguishes the positive folds
    robustness      -> REGIME_GATE_OR_PARK  one fold carries it; name the variable or park
    significance    -> BREADTH              pool the mechanism as a family, or diversifier
    sample          -> SAMPLE_EXTENSION     with WHAT DATA would make it evaluable
    fidelity        -> FIDELITY_RECONCILIATION  a stamp and a work item, never a refusal

NO GATE IS RELAXED HERE, AND THAT IS THE POINT
-----------------------------------------------
This module reads a `SleeveVerdict` and writes a diagnosis. It sets no threshold, moves no
verdict, and cannot make a REJECT into an ADMIT. The seven gates and their sealed
thresholds in `GateSpec` are untouched — which is what makes the prescription trustworthy:
it is the repair path for a sleeve that genuinely failed, not a softer standard.

THE THREE-WAY SPLIT ON A NEGATIVE EXPECTANCY IS THE PART WORTH READING
-----------------------------------------------------------------------
`FOURTH_REVIEW.md` §3.3 asks for exactly one query and never says who runs it:
*"MFE/MAE decomposition on the regenerated stream: if setups have excursion the exit
misses -> exit repair; if none -> test the inverse; else park with list."* That query is
here, automatic, on every sleeve — because a human running it per sleeve is how it does not
get run. It needs `mfe_r`/`mae_r` on the trade features, which
`walkforward.exits.replay` produces; without them the diagnosis says so and names the run
that would supply them, rather than guessing.

WHAT A MARGIN IS
----------------
`margin = observed - required`, in the gate's own units, signed so that negative is the
distance still to travel. Every gate also gets a `margin_frac` where a scale-free reading
exists. A margin is the difference between "this sleeve failed" and "this sleeve failed by
0.4% of one fold", and the second is a repair brief.
"""

from __future__ import annotations

import collections
import datetime as dt
import enum
import math
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

__all__ = [
    "Prescription",
    "GateDiagnosis",
    "SleeveDiagnosis",
    "diagnose_sleeve",
    "build_repair_queue",
]

SCHEMA = "gtos.walkforward.repair_queue.v1"


class Prescription(str, enum.Enum):
    """What to DO. One value per mechanistically distinct repair path."""

    NONE = "NONE"
    DATA_PATH = "DATA_PATH"
    COST_GEOMETRY = "COST_GEOMETRY"
    EXIT_REPAIR = "EXIT_REPAIR"
    INVERSE_TEST = "INVERSE_TEST"
    PER_TRADE_QUALITY = "PER_TRADE_QUALITY"
    REGIME_GATE = "REGIME_GATE"
    FOLD_CONDITIONING = "FOLD_CONDITIONING"
    REGIME_GATE_OR_PARK = "REGIME_GATE_OR_PARK"
    BREADTH = "BREADTH"
    SAMPLE_EXTENSION = "SAMPLE_EXTENSION"
    FIDELITY_RECONCILIATION = "FIDELITY_RECONCILIATION"
    SYMBOL_SURFACE = "SYMBOL_SURFACE"
    #: The generator emitted NOTHING. Distinct from coverage, and the distinction is the
    #: whole point: a coverage failure means broker truth cannot price trades that exist,
    #: this means there are no trades to price. Conflating them produced the sentence
    #: "capture ticks for []" on the first run of this module.
    GENERATION = "GENERATION"


#: The owning component, in the brief's own vocabulary
#: ({entry, exit, session, symbol surface, sizing, pairing, regime gate, cost geometry}).
COMPONENT: dict[Prescription, str] = {
    Prescription.NONE: "none",
    Prescription.DATA_PATH: "data",
    Prescription.COST_GEOMETRY: "cost geometry",
    Prescription.EXIT_REPAIR: "exit",
    Prescription.INVERSE_TEST: "entry",
    Prescription.PER_TRADE_QUALITY: "entry",
    Prescription.REGIME_GATE: "regime gate",
    Prescription.FOLD_CONDITIONING: "regime gate",
    Prescription.REGIME_GATE_OR_PARK: "regime gate",
    Prescription.BREADTH: "pairing",
    Prescription.SAMPLE_EXTENSION: "data",
    Prescription.FIDELITY_RECONCILIATION: "generation port",
    Prescription.SYMBOL_SURFACE: "symbol surface",
    Prescription.GENERATION: "generation port",
}

#: Sleeves whose generator is known to fail closed on an input the archive does not hold.
#: Keyed by sleeve, value is the exact missing input and the fetch that supplies it. This
#: is a REGISTER, not a guess: each entry was established by reading the generator's own
#: fail-closed guard. An unlisted zero-trade sleeve gets the generic prescription, which
#: says to go and read the guard.
GENERATION_BLOCKERS: dict[str, str] = {
    "vp_euidx_pocgrav": (
        "needs an M1 aux feed to build the prior-day volume profile and fails closed "
        "without one (`sleeves/vp_euidx.py:70` — `if not aux_bars or not aux_times: "
        "return None`). The bars archive holds D1/H4/M15 for 50 symbols and NO M1 at all "
        "(verified by listing `vps-bars-20260727/` 2026-07-29). UNBLOCKING DATA: an M1 "
        "export for GER40 and UK100 over the H4 span (2018-03-25 .. 2026-07-26) — two "
        "symbols, one owner-executed read-only fetch of the same shape as the "
        "2026-07-27 bars ceremony. This sleeve is redacted_account's measured fourth "
        "UNCONDITIONAL survivor, so it is the highest-value fetch in the estate."
    ),
}


@dataclass
class GateDiagnosis:
    gate: str
    passed: bool
    #: observed - required, in the gate's own units. None when the gate has no scalar.
    margin: float | None = None
    #: Scale-free version where one exists (e.g. retention ratio, coverage fraction).
    margin_frac: float | None = None
    observed: Any = None
    required: Any = None
    prescription: Prescription = Prescription.NONE
    #: One sentence, in the imperative, naming what to change.
    action: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "gate": self.gate,
            "pass": self.passed,
            "margin": (round(self.margin, 8) if isinstance(self.margin, float)
                       and math.isfinite(self.margin) else self.margin),
            "margin_frac": (round(self.margin_frac, 6) if isinstance(self.margin_frac, float)
                            and math.isfinite(self.margin_frac) else self.margin_frac),
            "observed": self.observed,
            "required": self.required,
            "prescription": self.prescription.value,
            "component": COMPONENT[self.prescription],
            "action": self.action,
            "evidence": self.evidence,
        }


@dataclass
class SleeveDiagnosis:
    sleeve: str
    verdict: str
    #: Every gate, passed or failed, with its margin.
    gates: list[GateDiagnosis] = field(default_factory=list)
    #: The failure to attack first: the earliest failing gate in mechanistic order.
    primary: Prescription = Prescription.NONE
    #: Ordered, deduplicated repair paths — the sleeve's own repair list.
    repair_paths: list[str] = field(default_factory=list)
    #: Cross-cutting evidence every prescription may read.
    cost_decomposition: dict[str, Any] = field(default_factory=dict)
    excursion: dict[str, Any] = field(default_factory=dict)
    by_symbol: list[dict[str, Any]] = field(default_factory=list)
    by_side: list[dict[str, Any]] = field(default_factory=list)
    by_session: list[dict[str, Any]] = field(default_factory=list)
    by_fold: list[dict[str, Any]] = field(default_factory=list)
    holding: dict[str, Any] = field(default_factory=dict)
    fidelity_stamp: dict[str, Any] = field(default_factory=dict)

    @property
    def failing(self) -> list[GateDiagnosis]:
        return [g for g in self.gates if not g.passed]

    def as_dict(self) -> dict[str, Any]:
        return {
            "sleeve": self.sleeve,
            "verdict": self.verdict,
            "primary_prescription": self.primary.value,
            "primary_component": COMPONENT[self.primary],
            "repair_paths": self.repair_paths,
            "gates": [g.as_dict() for g in self.gates],
            "cost_decomposition": self.cost_decomposition,
            "excursion": self.excursion,
            "holding": self.holding,
            "by_fold": self.by_fold,
            "by_symbol": self.by_symbol,
            "by_side": self.by_side,
            "by_session": self.by_session,
            "fidelity_stamp": self.fidelity_stamp,
        }


# ======================================================================================
# evidence builders — all read the priced trades the gate already produced


def _priced_for(priced: Iterable[Any], sleeve: str) -> list[Any]:
    return [p for p in priced
            if p.status == "priced" and p.trade.sleeve == sleeve and p.r_net is not None]


def cost_decomposition(rows: Sequence[Any]) -> dict[str, Any]:
    """Which cost term is eating the edge, and therefore which repair applies.

    The four terms have four different repairs and the total tells them apart from none
    of them:

        commission  scales as 1/stop  -> a stop-width sweep moves it
        swap        scales with nights -> the exit moves it
        spread      scales with 1/stop and with the session -> entry timing, session filter
        slippage    fixed in R at the live geometry -> nothing here moves it

    `pct_of_gross` uses the SUM OF ABSOLUTE gross R as the denominator, not the signed
    sum. A sleeve whose gross nets to near zero over thousands of trades — `idxrev` is
    +0.006 on n=6,473 — would otherwise divide by ~0 and report a cost share in the
    thousands of percent, which is an artifact of the denominator and not a finding.
    """
    if not rows:
        return {"available": False, "reason": "no priced trades"}
    terms = ("commission_r", "swap_r", "spread_r", "slippage_r")
    have = [p for p in rows if p.components]
    if not have:
        return {"available": False,
                "reason": "priced trades carry no component breakdown (pre-B601 records)"}
    n = len(have)
    sums = {t: math.fsum(float(p.components.get(t, 0.0)) for p in have) for t in terms}
    total = math.fsum(sums.values())
    gross_abs = math.fsum(abs(p.trade.r_gross) for p in have)
    gross_sum = math.fsum(p.trade.r_gross for p in have)
    nights = [p.swap_nights for p in have if p.swap_nights is not None]
    out: dict[str, Any] = {
        "available": True,
        "n_trades": n,
        "mean_total_cost_r": round(total / n, 6),
        "mean_gross_r": round(gross_sum / n, 6),
        "mean_net_r": round((gross_sum - total) / n, 6),
        "terms": {
            t: {
                "mean_r": round(sums[t] / n, 6),
                "share_of_cost": (round(sums[t] / total, 5) if total else None),
                "pct_of_abs_gross": (round(100.0 * sums[t] / gross_abs, 3)
                                     if gross_abs else None),
            }
            for t in terms
        },
        "cost_pct_of_abs_gross": (round(100.0 * total / gross_abs, 3) if gross_abs else None),
        "largest_term": max(terms, key=lambda t: sums[t]),
    }
    if nights:
        nights_sorted = sorted(nights)
        out["swap_nights"] = {
            "n": len(nights),
            "mean": round(math.fsum(nights) / len(nights), 4),
            "median": round(nights_sorted[len(nights_sorted) // 2], 4),
            "frac_zero": round(sum(1 for x in nights if x <= 0.0) / len(nights), 5),
            "max": round(max(nights), 4),
        }
    return out


def holding_summary(rows: Sequence[Any]) -> dict[str, Any]:
    """Realised holding time — the number OD-3 turns on, measured rather than assumed.

    `SESSION_N_W7_RECOST_RESULT.md` §8.1 left this as an upper bound for nine of eleven
    sleeves because no exit index survived in any cache. It survives here: the hold comes
    off the simulated path, so this is a measurement of the rule as written.
    """
    if not rows:
        return {"available": False, "reason": "no priced trades"}
    hh = sorted(p.trade.holding_hours for p in rows)
    n = len(hh)

    def q(f: float) -> float:
        return round(hh[min(n - 1, max(0, int(f * (n - 1))))], 4)

    return {
        "available": True,
        "n": n,
        "mean_hours": round(math.fsum(hh) / n, 4),
        "median_hours": q(0.5),
        "p10_hours": q(0.10),
        "p90_hours": q(0.90),
        "p99_hours": q(0.99),
        "max_hours": round(hh[-1], 4),
        "frac_over_24h": round(sum(1 for x in hh if x > 24.0) / n, 5),
    }


def by_symbol(rows: Sequence[Any]) -> list[dict[str, Any]]:
    """Per-symbol net expectancy, worst first. Names the symbols to drop or condition."""
    acc: dict[str, list[float]] = collections.defaultdict(list)
    gross: dict[str, list[float]] = collections.defaultdict(list)
    for p in rows:
        acc[p.trade.symbol].append(p.r_net)
        gross[p.trade.symbol].append(p.trade.r_gross)
    out = []
    for sym, v in acc.items():
        out.append({
            "symbol": sym,
            "n": len(v),
            "mean_net_r": round(math.fsum(v) / len(v), 6),
            "mean_gross_r": round(math.fsum(gross[sym]) / len(v), 6),
            "sum_net_r": round(math.fsum(v), 4),
        })
    return sorted(out, key=lambda d: d["mean_net_r"])


def by_side(rows: Sequence[Any]) -> list[dict[str, Any]]:
    """LONG vs SHORT, with the swap charge split out — because carry is side-asymmetric.

    `cost_r` books adverse swap only: *"Zero when the swap is favourable"*
    (`model.py:253`), a deliberate and conservative choice. So an instrument whose long
    swap is a credit and whose short swap is a charge — FTMO's oil is +4.06 / −27.50
    points a night on USOIL and +21.72 / −104.42 on UKOIL — puts its ENTIRE carry cost on
    one side of the book. A carry repair for such a sleeve is therefore side-conditional
    (shorten the hold on shorts, or flat the shorts before rollover) and a symmetric one
    would pay for a problem half the trades do not have.
    """
    acc: dict[str, dict[str, Any]] = {}
    for p in rows:
        k = p.trade.side
        d = acc.setdefault(k, {"side": k, "n": 0, "net": [], "gross": [], "swap": []})
        d["n"] += 1
        d["net"].append(p.r_net)
        d["gross"].append(p.trade.r_gross)
        d["swap"].append(float((p.components or {}).get("swap_r", 0.0)))
    out = []
    for k, d in acc.items():
        n = d["n"]
        out.append({
            "side": k, "n": n,
            "mean_net_r": round(math.fsum(d["net"]) / n, 6),
            "mean_gross_r": round(math.fsum(d["gross"]) / n, 6),
            "mean_swap_r": round(math.fsum(d["swap"]) / n, 6),
            "sum_net_r": round(math.fsum(d["net"]), 4),
        })
    return sorted(out, key=lambda x: x["side"])


def by_session(rows: Sequence[Any], *, server: str | None = None) -> list[dict[str, Any]]:
    """Per-session net expectancy on the BROKER's wall clock where one is resolvable.

    Session windows are the broker's, not UTC's, and the two differ by 7 h against New
    York with a US DST calendar (`CLAUDE.md` §4). Guessing +3 would put every boundary in
    the wrong session for ~4 weeks a year including inside the sealed March window, so
    when no server resolves this falls back to UTC and STAMPS that it did.
    """
    conv = None
    basis = "utc_hour"
    if server:
        try:
            from src.utils.broker_clock import resolve_rule, utc_to_broker_naive
            rule = resolve_rule(server)
            conv = lambda t: utc_to_broker_naive(t, rule)  # noqa: E731
            basis = f"broker_wall_hour[{server}]"
        except Exception:
            conv = None
    buckets: dict[str, list[float]] = collections.defaultdict(list)
    for p in rows:
        t = p.trade.entry_utc
        h = (conv(t).hour if conv else t.hour)
        if 0 <= h < 8:
            name = "asia"
        elif 8 <= h < 13:
            name = "london"
        elif 13 <= h < 18:
            name = "ny_overlap"
        else:
            name = "late_ny"
        buckets[f"{name}[{basis}]"].append(p.r_net)
    out = []
    for k, v in buckets.items():
        out.append({"session": k, "n": len(v),
                    "mean_net_r": round(math.fsum(v) / len(v), 6),
                    "sum_net_r": round(math.fsum(v), 4)})
    return sorted(out, key=lambda d: d["mean_net_r"])


def excursion_from_features(rows: Sequence[Any]) -> dict[str, Any]:
    """MFE/MAE aggregates off the trade features, when the generator recorded them.

    Returns `available: False` WITH the run that would supply them, rather than a guess —
    `NOT_EVALUABLE` in this package always carries what data would make it evaluable
    (§4.1).
    """
    have = [p for p in rows if isinstance(p.trade.features, dict)
            and p.trade.features.get("mfe_r") is not None]
    if not have:
        return {
            "available": False,
            "reason": "no mfe_r on the trade features",
            "what_would_supply_it": (
                "regenerate through walkforward.exits.replay, which returns "
                "(r_gross, exit_index, mfe_r, mae_r, bars_to_mfe, exit_reason) and is "
                "fuzz-verified identical to primitives.simulate_detail on r and exit index"
            ),
        }
    n = len(have)
    mfe = [float(p.trade.features["mfe_r"]) for p in have]
    mae = [float(p.trade.features.get("mae_r") or 0.0) for p in have]
    # RATIO OF MEANS, not mean of ratios. Measured 2026-07-29 (B615): the per-trade ratio
    # `r_gross / mfe_r` is unbounded below — a trade that stopped at -1 R after a 0.02 R
    # excursion contributes -50 — so its MEAN is dominated by the smallest denominators
    # and came back NEGATIVE for every sleeve in the estate, which is not a capture ratio,
    # it is an artefact of the estimator. The pooled form is bounded, is what "share of
    # the available excursion the exit kept" actually means, and is the one reported.
    pairs = [(p.trade.r_gross, m) for p, m in zip(have, mfe) if m > 1e-9]
    caps = [r / m for r, m in pairs]
    reasons: collections.Counter = collections.Counter(
        str(p.trade.features.get("exit_reason") or "unknown") for p in have
    )
    b2m = [float(p.trade.features.get("bars_to_mfe") or 0) for p in have]
    return {
        "available": True,
        "n": n,
        "coverage_frac": round(n / len(rows), 5) if rows else None,
        "mean_mfe_r": round(math.fsum(mfe) / n, 5),
        "mean_mae_r": round(math.fsum(mae) / n, 5),
        "median_mfe_r": round(sorted(mfe)[n // 2], 5),
        "frac_mfe_over_1r": round(sum(1 for x in mfe if x >= 1.0) / n, 5),
        "frac_mfe_over_2r": round(sum(1 for x in mfe if x >= 2.0) / n, 5),
        # The headline: sum(realised R) / sum(MFE) over trades that had an excursion.
        "capture_ratio_pooled": (
            round(math.fsum(r for r, _ in pairs) / math.fsum(m for _, m in pairs), 5)
            if pairs else None),
        "capture_ratio_median": (round(sorted(caps)[len(caps) // 2], 5) if caps else None),
        "capture_ratio_n": len(caps),
        "capture_ratio_note": (
            "POOLED = sum(realised R) / sum(MFE). The mean of per-trade ratios is NOT "
            "reported: it is unbounded below and dominated by trades with a near-zero "
            "excursion, and it read negative for every sleeve in this estate."),
        "mean_bars_to_mfe": round(math.fsum(b2m) / n, 3) if b2m else None,
        "exit_reasons": dict(sorted(reasons.items())),
        "note": ("MFE/MAE are bar-extreme bounds over the held window, not fills. A high "
                 "mean MFE with a low capture ratio is an EXIT problem; no MFE at all is "
                 "an ENTRY problem."),
    }


# ======================================================================================
# the three-way split on a negative expectancy


#: A sleeve whose average trade reaches this much favourable excursion has setups; what
#: it lacks is a way to keep them. Set at 1 R — one stop-width of run — because that is
#: the smallest excursion any exit contract in this estate could have monetised (every
#: sleeve's target is >= 1 R). Below it, the entry is not finding movement and no exit
#: change can invent it.
EXCURSION_ALIVE_R = 1.0


def _negative_expectancy_prescription(exc: dict[str, Any]) -> tuple[Prescription, str]:
    if not exc.get("available"):
        return (
            Prescription.EXIT_REPAIR,
            "Run the MFE/MAE decomposition first (regenerate through "
            "walkforward.exits.replay): with excursion present this is an EXIT repair, "
            "without it an INVERSE test. Defaulting to EXIT_REPAIR names the cheaper "
            "measurement, not a conclusion.",
        )
    mean_mfe = float(exc.get("mean_mfe_r") or 0.0)
    frac1 = float(exc.get("frac_mfe_over_1r") or 0.0)
    cap = exc.get("capture_ratio_pooled")
    if mean_mfe >= EXCURSION_ALIVE_R or frac1 >= 0.35:
        return (
            Prescription.EXIT_REPAIR,
            f"The setups move: mean MFE {mean_mfe:.2f} R, {frac1:.0%} of trades reach 1 R, "
            f"capture ratio {cap if cap is not None else 'n/a'}. The entry is finding "
            f"excursion the exit is not keeping — sweep trail_arm/trail_gap and the time "
            f"stop through walkforward.exits.replay before touching the entry.",
        )
    return (
        Prescription.INVERSE_TEST,
        f"No excursion to keep: mean MFE {mean_mfe:.2f} R and only {frac1:.0%} of trades "
        f"reach 1 R, so no exit change can recover this. Test the INVERSE of the trigger "
        f"on the same bars (the charter's own doctrine for a measured-negative mechanism) "
        f"before parking, and record both directions in the trial ledger.",
    )


def _breadth_multiple(p_raw: float | None, q: float | None, alpha: float) -> dict[str, Any]:
    """How much breadth a family pool would need for this p to clear.

    Fundamental law: IR ~ IC x sqrt(breadth), so pooling k independent members of one
    mechanism scales the t-statistic by sqrt(k). Inverting: to move an observed one-sided
    p to alpha needs k ~ (z_alpha / z_obs)^2.

    Stated as an ORDER OF MAGNITUDE, not a promise. It assumes the members are
    independent and carry the same IC, and real symbol families are neither — the number
    is a sizing hint for how many symbols the mechanism sweep (§3.3 / Session AF) needs to
    cover, not a significance calculation.
    """
    if p_raw is None or not math.isfinite(p_raw) or p_raw <= 0 or p_raw >= 1:
        return {"available": False, "reason": f"p_raw {p_raw!r} not usable"}

    def _z(p: float) -> float:
        """One-sided upper-tail quantile: z such that P(Z > z) = p."""
        if p <= 0 or p >= 1:
            return float("nan")
        return -math.sqrt(2.0) * _erfinv(2.0 * p - 1.0)

    z_obs = _z(p_raw)
    z_tgt = _z(alpha)
    if not (math.isfinite(z_obs) and math.isfinite(z_tgt)) or z_obs <= 0:
        return {"available": False, "reason": "observed evidence is not in the right tail"}
    k = (z_tgt / z_obs) ** 2 if z_obs > 0 else float("inf")
    return {
        "available": True,
        "p_raw": p_raw,
        "q_value": q,
        "alpha": alpha,
        "z_observed": round(z_obs, 4),
        "z_needed_at_alpha": round(z_tgt, 4),
        "breadth_multiple_needed": (round(k, 2) if math.isfinite(k) else None),
        "reading": (
            f"pooling ~{math.ceil(k):d} equally-informative members of this mechanism "
            f"would put the raw evidence at alpha={alpha}"
            if math.isfinite(k) and k >= 1 else
            "the raw evidence already clears alpha; the failure is the multiplicity bill, "
            "so the repair is the family pool or the diversifier door, not more data"
        ),
        "caveat": ("assumes independent members of equal IC; a symbol family is neither. "
                   "Order of magnitude for scoping the sweep, not a significance claim."),
    }


def _erfinv(y: float) -> float:
    """Inverse error function (Giles 2010 single-precision refinement, Newton-polished)."""
    if y <= -1.0:
        return -float("inf")
    if y >= 1.0:
        return float("inf")
    w = -math.log((1.0 - y) * (1.0 + y))
    if w < 5.0:
        w -= 2.5
        p = 2.81022636e-08
        for c in (3.43273939e-07, -3.5233877e-06, -4.39150654e-06, 0.00021858087,
                  -0.00125372503, -0.00417768164, 0.246640727, 1.50140941):
            p = p * w + c
    else:
        w = math.sqrt(w) - 3.0
        p = -0.000200214257
        for c in (0.000100950558, 0.00134934322, -0.00367342844, 0.00573950773,
                  -0.0076224613, 0.00943887047, 1.00167406, 2.83297682):
            p = p * w + c
    x = p * y
    # two Newton steps against erf, which the stdlib has exactly
    for _ in range(2):
        err = math.erf(x) - y
        x -= err / (2.0 / math.sqrt(math.pi) * math.exp(-x * x))
    return x


# ======================================================================================


def diagnose_sleeve(
    sv: Any,
    spec: Any,
    *,
    priced: Sequence[Any] = (),
    server: str | None = None,
) -> SleeveDiagnosis:
    """Turn one `SleeveVerdict` into a repair brief. Changes no verdict and no threshold."""
    d = SleeveDiagnosis(sleeve=sv.sleeve, verdict=sv.verdict.value
                        if hasattr(sv.verdict, "value") else str(sv.verdict))
    rows = _priced_for(priced, sv.sleeve)
    d.cost_decomposition = cost_decomposition(rows)
    d.excursion = excursion_from_features(rows)
    d.holding = holding_summary(rows)
    d.by_symbol = by_symbol(rows)
    d.by_side = by_side(rows)
    d.by_session = by_session(rows, server=server)
    d.by_fold = [
        {"fold_id": f.get("fold_id"), "status": f.get("status"),
         "oos_start": f.get("oos_start"), "oos_end": f.get("oos_end"),
         "n_test_trades": f.get("n_test_trades"), "test_mean_r": f.get("test_mean_r"),
         "train_mean_r": f.get("train_mean_r")}
        for f in (sv.folds or [])
    ]
    d.fidelity_stamp = dict(sv.fidelity or {})

    g = sv.gates or {}

    # ---- fidelity: a STAMP and a work item, never a refusal (§2.1) --------------------
    fid = g.get("fidelity", {})
    recall = fid.get("live_recall")
    fid_ok = bool(fid.get("pass"))
    d.gates.append(GateDiagnosis(
        gate="fidelity", passed=fid_ok,
        margin=(None if recall is None else recall - float(fid.get("floor", 0.0))),
        margin_frac=recall,
        observed=recall, required=fid.get("floor"),
        prescription=Prescription.NONE if fid_ok else Prescription.FIDELITY_RECONCILIATION,
        action=("" if fid_ok else
                "Measure the rule on the port's own semantics and stamp the transfer risk "
                "(fidelity_class), then open a reconciliation work item: a live engine that "
                "does not implement its own spec is a bug in the engine or the spec, and "
                "either way the fix is ours. Never a reason the economics are unknowable."),
        evidence={"class": fid.get("live_recall"), **{k: v for k, v in (sv.fidelity or {}).items()
                                                      if k in ("class", "basis", "basis_n",
                                                               "basis_note", "ceiling_stamp")}},
    ))

    # ---- symbol consistency ----------------------------------------------------------
    sc = g.get("symbol_consistency")
    if sc is not None and sc.get("checked") and not sc.get("pass"):
        d.gates.append(GateDiagnosis(
            gate="symbol_consistency", passed=False,
            observed=sc.get("observed_symbols"), required=sc.get("expected_symbols"),
            prescription=Prescription.SYMBOL_SURFACE,
            action=("Reconcile the registry against the generator's own surface. A sleeve "
                    "sized for symbols it can never fire on is a wiring defect with a "
                    "one-line fix, not a sleeve failure."),
            evidence={"unexpected_symbols": sc.get("unexpected_symbols")},
        ))

    # ---- generation: nothing to price at all ------------------------------------------
    # Checked BEFORE coverage, because a sleeve with no trades has coverage 0/0 and would
    # otherwise be handed a coverage prescription naming an empty symbol list. Measured on
    # the first run of this module, which emitted the sentence "capture ticks for []".
    if int(sv.n_trades or 0) == 0:
        blocker = GENERATION_BLOCKERS.get(sv.sleeve)
        d.gates.append(GateDiagnosis(
            gate="generation", passed=False, margin=0.0, observed=0, required=1,
            prescription=Prescription.GENERATION,
            action=(
                f"The generator emitted ZERO candidates over the whole archive — there is "
                f"nothing to price, so this is not a coverage question. "
                + (blocker if blocker else
                   "Read the generator's own fail-closed guards and name the input it is "
                   "missing; every sleeve in this estate fails closed on a stated "
                   "condition rather than silently. Then either supply that input or "
                   "record it as the unblocking data.")
            ),
            evidence={"n_trades": 0, "known_blocker": blocker,
                      "fidelity": sv.fidelity},
        ))
        d.primary = Prescription.GENERATION
        # The fidelity stamp still travels — a first-of-day sleeve that generated nothing
        # has two work items, not one.
        d.repair_paths = [f"[{f.prescription.value}] {f.action}".strip()
                          for f in d.failing if f.action]
        return d

    # ---- coverage --------------------------------------------------------------------
    cov = g.get("cost_coverage", {})
    if cov:
        cf = float(cov.get("coverage_frac") or 0.0)
        floor = float(cov.get("floor") or 0.0)
        ok = bool(cov.get("pass"))
        unpriceable = cov.get("unpriceable_symbols") or []
        d.gates.append(GateDiagnosis(
            gate="coverage", passed=ok, margin=cf - floor, margin_frac=cf,
            observed=cf, required=floor,
            prescription=Prescription.NONE if ok else Prescription.DATA_PATH,
            action=("" if ok else
                    f"Data path, not a verdict. Either capture ticks for {unpriceable} "
                    f"(the metals gap closed this way on 2026-07-29: 58.7% -> 100% in "
                    f"about an hour), or price them through the banded spread model "
                    f"(FOURTH_REVIEW §4.6, Session AG) and carry {{low, mid, high}} "
                    f"verdicts. NEVER 'unjudgeable'."),
            evidence={"unpriceable_symbols": unpriceable,
                      "priceable_symbols": cov.get("priceable_symbols"),
                      "unpriced_reasons": (sv.coverage or {}).get("unpriced_reasons"),
                      "restricted": cov.get("restricted", False)},
        ))

    # ---- sample ----------------------------------------------------------------------
    smp = g.get("sample")
    if smp is not None:
        ok = bool(smp.get("pass"))
        n = int(smp.get("n_trades_in_scored_folds") or 0)
        need = int(smp.get("min_trades_total") or 0)
        nf = int(smp.get("n_folds_evaluable") or 0)
        needf = int(smp.get("min_folds_evaluable") or 0)
        lacks = []
        if n < need:
            lacks.append(f"{need - n} more scored trades")
        if nf < needf:
            lacks.append(f"{needf - nf} more evaluable folds")
        if float(smp.get("thin_fold_frac") or 0) > float(smp.get("max_thin_fold_frac") or 1):
            lacks.append(f"{smp.get('n_thin_folds')} thin folds to thicken")
        d.gates.append(GateDiagnosis(
            gate="sample", passed=ok,
            margin=float(n - need), margin_frac=(n / need if need else None),
            observed={"n_scored_trades": n, "n_folds_evaluable": nf},
            required={"min_trades_total": need, "min_folds_evaluable": needf},
            prescription=Prescription.NONE if ok else Prescription.SAMPLE_EXTENSION,
            action=("" if ok else
                    f"Extend the stream, do not refuse the sleeve. Needs {', '.join(lacks)}. "
                    f"The archive reaches back further than this sleeve's generated span for "
                    f"every timeframe the bars cover; where it does not, name the fetch "
                    f"(§9 deep-history) as the unblocking data."),
            evidence={"fold_status": smp.get("fold_status"),
                      "n_priced_trades_all_folds": smp.get("n_priced_trades_all_folds"),
                      "what_would_make_it_evaluable": lacks},
        ))

    # ---- expectancy (per day and per trade) -------------------------------------------
    exp = g.get("expectancy")
    if exp is not None:
        day = exp.get("pooled_oos_mean_r")
        day_floor = float(exp.get("min_oos_mean_r") or 0.0)
        per_t = exp.get("oos_mean_r_per_trade")
        per_floor = exp.get("min_oos_mean_r_per_trade")
        day_ok = isinstance(day, float) and math.isfinite(day) and day > day_floor
        per_ok = bool(exp.get("per_trade_pass", True))
        gross_mean = d.cost_decomposition.get("mean_gross_r")
        if not day_ok:
            if isinstance(gross_mean, float) and gross_mean > 0:
                pres = Prescription.COST_GEOMETRY
                largest = d.cost_decomposition.get("largest_term", "?")
                cpct = d.cost_decomposition.get("cost_pct_of_abs_gross")
                act = (
                    f"The edge exists and cost eats it: gross {gross_mean:+.5f} R/trade, cost "
                    f"{cpct}% of |gross|, largest term {largest}. Attack THAT term — "
                    f"commission scales as 1/stop so sweep stop width 1.0->2.0x ATR; swap "
                    f"scales with nights so tighten the exit or add a pre-rollover flat; "
                    f"spread is entry timing and a session filter. Log every sweep cell to "
                    f"the trial ledger."
                )
            else:
                pres, act = _negative_expectancy_prescription(d.excursion)
        else:
            pres, act = Prescription.NONE, ""
        d.gates.append(GateDiagnosis(
            gate="expectancy_per_day", passed=day_ok,
            margin=(day - day_floor) if isinstance(day, float) and math.isfinite(day) else None,
            observed=day, required=day_floor, prescription=pres, action=act,
            evidence={"mean_gross_r_per_trade": gross_mean,
                      "cost_decomposition": d.cost_decomposition,
                      "excursion": d.excursion,
                      "by_side": d.by_side},
        ))
        if per_floor is not None:
            d.gates.append(GateDiagnosis(
                gate="expectancy_per_trade", passed=per_ok,
                margin=((per_t - float(per_floor))
                        if isinstance(per_t, float) and math.isfinite(per_t) else None),
                observed=per_t, required=per_floor,
                prescription=(Prescription.NONE if per_ok
                              else (Prescription.PER_TRADE_QUALITY if day_ok
                                    else Prescription.COST_GEOMETRY)),
                action=("" if per_ok else
                        ("The day-mean is fine and the per-trade mean is not, so a few bad "
                         "trades per day are dragging it: cap intraday count, or add a "
                         "per-trade quality filter (a meta-label overlay, §4.8, is built for "
                         "exactly this shape). Read by_symbol and by_session below — the "
                         "drag is usually concentrated."
                         if day_ok else
                         "Both means are negative; the per-trade repair is downstream of "
                         "the day-mean one above.")),
                evidence={"n_scored_oos_trades": exp.get("n_scored_oos_trades"),
                          "worst_symbols": d.by_symbol[:3],
                          "worst_sessions": d.by_session[:2]},
            ))

    # ---- lifetime ---------------------------------------------------------------------
    lt = g.get("lifetime")
    if lt is not None and lt.get("enabled"):
        ok = bool(lt.get("pass"))
        obs = lt.get("mean_r_net_per_trade_all_folds")
        req = float(lt.get("min_lifetime_mean_r") or 0.0)
        d.gates.append(GateDiagnosis(
            gate="lifetime", passed=ok,
            margin=(obs - req) if isinstance(obs, float) and math.isfinite(obs) else None,
            observed=obs, required=req,
            prescription=Prescription.NONE if ok else Prescription.REGIME_GATE,
            action=("" if ok else
                    "The scored window is positive and the sleeve's own history is not, so "
                    "the rule changed sign somewhere. Find the break date from the fold "
                    "series below, NAME the conditioning variable (vol state, carry regime, "
                    "trend state), and gate on it explicitly — then re-walk. A regime gate "
                    "that cannot be named is the one case that parks, and it parks WITH "
                    "this list."),
            evidence={"fold_series": d.by_fold,
                      "fold0_unscored": (sv.telemetry or {}).get("lifetime", {}).get(
                          "fold0_unscored"),
                      "regime_inflation": (sv.telemetry or {}).get("regime_inflation")},
        ))

    # ---- stability --------------------------------------------------------------------
    st = g.get("stability")
    if st is not None:
        ok = bool(st.get("pass"))
        obs = float(st.get("oos_positive_fold_frac") or 0.0)
        req = float(st.get("min_oos_positive_fold_frac") or 0.0)
        means = st.get("fold_means") or []
        denom = int(st.get("denominator") or len(means) or 1)
        need_more = max(0, math.ceil(req * denom) - sum(1 for m in means if m > 0))
        neg = [(i, round(m, 5)) for i, m in enumerate(means) if m <= 0]
        d.gates.append(GateDiagnosis(
            gate="stability", passed=ok, margin=obs - req, margin_frac=obs,
            observed=obs, required=req,
            prescription=Prescription.NONE if ok else Prescription.FOLD_CONDITIONING,
            action=("" if ok else
                    f"{need_more} more positive fold(s) would clear it. The edge is "
                    f"regime-dependent: ask what distinguishes the POSITIVE folds from "
                    f"{[i for i, _ in neg]} — the same conditioning path as lifetime, at "
                    f"fold level. Thin folds count as non-positive by construction, so "
                    f"check whether the failure is regime or coverage first."),
            evidence={"fold_means": [round(m, 6) for m in means],
                      "negative_folds": neg,
                      "n_thin_counted_non_positive": st.get(
                          "n_thin_folds_counted_as_non_positive"),
                      "folds_needed_to_flip": need_more},
        ))

    # ---- robustness -------------------------------------------------------------------
    rb = g.get("robustness")
    if rb is not None and rb.get("enabled"):
        ok = bool(rb.get("pass"))
        ret = rb.get("retention")
        retf = rb.get("retention_floor")
        d.gates.append(GateDiagnosis(
            gate="robustness", passed=ok,
            margin=((ret - float(retf)) if isinstance(ret, float) and math.isfinite(ret)
                    and retf is not None else None),
            margin_frac=(ret if isinstance(ret, float) and math.isfinite(ret) else None),
            observed=ret, required=retf,
            prescription=Prescription.NONE if ok else Prescription.REGIME_GATE_OR_PARK,
            action=("" if ok else
                    f"Fold {rb.get('dropped_fold_id')} carries the result. Two readings and "
                    f"they are distinguishable: regime-gate to whatever that fold's regime "
                    f"was and re-walk (if the variable can be named), or it is noise. If the "
                    f"variable CANNOT be named after the attempt, park WITH this list — "
                    f"never delete the sleeve."),
            evidence={"dropped_fold_id": rb.get("dropped_fold_id"),
                      "pooled_excl_best": rb.get("pooled_oos_mean_r_excl_best_fold"),
                      "fold_series": d.by_fold},
        ))

    # ---- significance -----------------------------------------------------------------
    sig = g.get("significance")
    if sig is not None:
        ok = bool(sig.get("pass"))
        q = sig.get("q_value")
        alpha = float(sig.get("alpha") or 0.05)
        breadth = _breadth_multiple(sig.get("p_raw"), q, alpha)
        d.gates.append(GateDiagnosis(
            gate="significance", passed=ok,
            margin=((alpha - q) if isinstance(q, float) and math.isfinite(q) else None),
            observed=q, required=alpha,
            prescription=Prescription.NONE if ok else Prescription.BREADTH,
            action=("" if ok else
                    f"Real-looking edge, family too big for one sleeve to carry alone "
                    f"(family {sig.get('family_size')}). {breadth.get('reading', '')} Two "
                    f"doors: pool the MECHANISM across symbols as a family (IR ~ IC x "
                    f"sqrt(breadth) — `portfolio_contribution.py` says this in as many "
                    f"words), or admit through the diversifier door (§4.4) where the "
                    f"question is the book's Sharpe, not the sleeve's t-statistic."),
            evidence={"p_raw": sig.get("p_raw"), "family_size": sig.get("family_size"),
                      "breadth": breadth,
                      "p_floor": (sv.telemetry or {}).get("p_floor")},
        ))

    # ---- primary + the sleeve's repair list --------------------------------------------
    order = ("fidelity", "symbol_consistency", "coverage", "sample", "expectancy_per_day",
             "expectancy_per_trade", "lifetime", "stability", "robustness", "significance")
    idx = {name: i for i, name in enumerate(order)}
    failing = sorted(d.failing, key=lambda x: idx.get(x.gate, 99))
    d.primary = failing[0].prescription if failing else Prescription.NONE
    seen: set[str] = set()
    for f in failing:
        line = f"[{f.prescription.value}] {f.action}".strip()
        if f.action and line not in seen:
            seen.add(line)
            d.repair_paths.append(line)
    return d


def build_repair_queue(
    result: Any,
    *,
    priced_by_sleeve: dict[str, Sequence[Any]] | None = None,
    server: str | None = None,
    run_label: str = "",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """`REPAIR_QUEUE_V1.json` — one row per (sleeve, prescription, evidence).

    Rows are emitted for ADMITted sleeves too, with `prescription: NONE`, because a repair
    queue that only lists failures cannot be diffed against the next walk to show what a
    repair moved.
    """
    priced_by_sleeve = priced_by_sleeve or {}
    rows: list[dict[str, Any]] = []
    diags: dict[str, dict[str, Any]] = {}
    for sleeve, sv in sorted(result.verdicts.items()):
        d = diagnose_sleeve(sv, result.spec, priced=priced_by_sleeve.get(sleeve, ()),
                            server=server)
        diags[sleeve] = d.as_dict()
        fails = d.failing
        if not fails:
            rows.append({
                "sleeve": sleeve, "verdict": d.verdict,
                "prescription": Prescription.NONE.value, "component": "none",
                "gate": None, "margin": None, "action": "",
                "evidence": {"pooled_oos_mean_r": sv.pooled_oos_mean_r,
                             "q_value": sv.q_value, "n_trades": sv.n_trades},
            })
            continue
        for f in fails:
            rows.append({
                "sleeve": sleeve, "verdict": d.verdict,
                "prescription": f.prescription.value,
                "component": COMPONENT[f.prescription],
                "gate": f.gate,
                "margin": (round(f.margin, 8) if isinstance(f.margin, float)
                           and math.isfinite(f.margin) else f.margin),
                "is_primary": f.prescription is d.primary and f is fails[0],
                "action": f.action,
                "evidence": f.evidence,
            })
    by_pres: dict[str, int] = collections.Counter(r["prescription"] for r in rows)
    return {
        "schema": SCHEMA,
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "run_label": run_label,
        "spec_sha256": result.spec.seal(),
        "spec_id": result.spec.spec_id,
        "no_gate_relaxed": (
            "The seven gates and their sealed thresholds are untouched by this module. It "
            "reads verdicts and writes repair paths; it cannot turn a REJECT into an ADMIT."
        ),
        "summary": {
            "n_sleeves": len(result.verdicts),
            "n_rows": len(rows),
            "by_prescription": dict(sorted(by_pres.items())),
            "n_with_no_prescription": by_pres.get(Prescription.NONE.value, 0),
        },
        "rows": rows,
        "diagnostics": diags,
        **(extra or {}),
    }
