#!/usr/bin/env python3
"""Evidence pack 1.4b — the gross-cap shed A/B (defect D1).

The question
------------
`admission._enforce_gross_open_risk_cap` (`admission.py:1319-1339`) is a
**first-fit-descending greedy**: units are considered in descending conviction and each is
admitted iff it fits the *remaining* headroom.  Its docstring claims it "sheds the LOWEST-conviction
units first".  It does not — it sheds by *fit* (D1).  Nobody has measured whether that costs
anything against the alternatives.  This does.

Why it has to be partly synthetic, stated up front
--------------------------------------------------
The cap **never bound live**.  Across the 1,754 recorded governor states the maximum
`would_total_risk_pct / available_gross_risk_pct` reached was 0.4654 and **zero** recorded units
carry `gross_risk_cap_would_exceed`.  A pure replay of the recorded (headroom, unit-set) pairs is
therefore a measurement of *nothing happening*, and it is reported as arm ``recorded`` precisely so
that fact is on the record rather than assumed.  The differentiating measurement runs the same
algorithms over unit sets drawn from the live 13-cluster confidence map against the **recorded
headroom distribution**, which is the part of the live evidence that is actually load-bearing here.

Arms
----
The session brief names first-fit vs smallest-first, largest-first and worst-expectancy-first.
Session H's own scoping (`third_review_receipts/read_session-h.md:23`) instead names FFD vs
proportional-scaling vs optimal-subset — and proportional scaling is the only alternative D1 itself
recommends.  This runs the **union**, plus two references:

  first_fit_descending   INCUMBENT.  Considered in descending conviction; admit iff fits.
  proportional_scaling   D1's proposed fix.  If sum > available, scale every unit by
                         available/sum.  Nothing is dropped.
  smallest_first         First-fit, considered in ascending unit_risk_pct.
  largest_first          First-fit, considered in descending unit_risk_pct.
  worst_expectancy_drop  Drop-until-fits: repeatedly remove the lowest-conviction remaining unit
                         until the set fits.  (This is the brief's "worst-expectancy-first" read as
                         a *shed* order, which is a genuinely different algorithm from a first-fit
                         admission order — under an admission reading it degenerates to
                         ascending_conviction.)
  ascending_conviction   First-fit, weakest considered first.  D1 shows this is *worse*; kept as a
                         negative reference so the claim is reproduced rather than cited.
  optimal_deployed       Exact max Σ unit_risk_pct subset (upper bound on deployed risk).
  optimal_conviction     Exact max Σ conf·unit_risk_pct subset (upper bound on conviction-weighted
                         deployed risk — a different objective, and the one the book's risk model
                         actually cares about).
  random_first_fit       THE NULL CONTROL (working agreement §3.1): first-fit in uniformly random
                         order, ``--null-draws`` draws per case.  Any claim that an ordering rule
                         beats another has to beat this first.

Metrics, reported as distributions
----------------------------------
  deployed          Σ unit_risk_pct admitted            (how much risk got deployed)
  conviction        Σ confidence · unit_risk_pct        (how much *conviction-weighted* risk)
  n_admitted        count of units admitted
  top_admitted      was the highest-conviction unit admitted at full size?  (D1's surviving
                    docstring property #2 — the metals_core starvation guarantee)
  shortfall_*       optimum − arm, per objective

Run:  python3 scripts/evidence_pack_shed_ab.py
"""
from __future__ import annotations

import argparse
import gzip
import json
import random
import statistics
import sys
from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

DEFAULT_PACKETS = Path(
    "/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs/"
    "ultimate_book_runtime_learning_packets.jsonl.gz"
)
DEFAULT_OUT = REPO / "docs/audits/fable5-vision-audit-20260725/phase3/evidence_packs"

SCHEMA = "gtos.phase3.evidence_pack.shed_ab.v1"

#: The live candidate-book flags, from `config/agent_config.yaml:1272-1286`.
LIVE_CANDIDATE_SLEEVES = (
    "asia_pdl_fade", "asian_fade", "kz_london_crypto_low", "liq_asia_up_low_metal",
    "metal_session_reversion", "ny_crypto_momentum", "orb_crypto_london",
    "vol_compression", "vss_fxcross_london_up_low",
)
LIVE_EXPANSION_POLICY = "positive_weighted12_after_swap"

#: `admission.py:1333` — the incumbent's fit tolerance.  Reused verbatim by every arm so the
#: comparison is of *order*, not of tolerance.
EPS = 1e-9


# --------------------------------------------------------------------------------------------
# units
# --------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Unit:
    cluster: str
    confidence: float
    unit_risk_pct: float

    @property
    def conviction_value(self) -> float:
        return self.confidence * self.unit_risk_pct


def _keep_mask_to_result(units: list[Unit], kept: list[float], available: float) -> dict:
    """`kept[i]` is the admitted risk for unit i (0.0 == shed).

    Two separate top-unit metrics, because they answer different questions and D1's surviving
    docstring property is the second one:
      ``top_full``    the highest-conviction unit was admitted at its full sized risk
      ``top_starved`` the highest-conviction unit got **zero** — the "NEVER starve metals_core"
                      hazard.  Proportional scaling scores 0 here and ~0 on ``top_full``: it
                      shrinks the top unit rather than dropping it, which is the whole point of it.
    """
    deployed = sum(kept)
    conviction = sum(u.confidence * k for u, k in zip(units, kept))
    n_admitted = sum(1 for k in kept if k > EPS)
    top_i = max(range(len(units)), key=lambda i: units[i].confidence) if units else None
    top_full = bool(top_i is not None and kept[top_i] >= units[top_i].unit_risk_pct - EPS)
    top_starved = bool(top_i is not None and kept[top_i] <= EPS
                       and units[top_i].unit_risk_pct > EPS)
    return {
        "deployed": deployed,
        "conviction": conviction,
        "n_admitted": n_admitted,
        "top_full": top_full,
        "top_starved": top_starved,
        "headroom_used": deployed / available if available > EPS else 0.0,
        "kept": kept,
    }


# --------------------------------------------------------------------------------------------
# arms
# --------------------------------------------------------------------------------------------
def _first_fit(units: list[Unit], available: float, order: list[int]) -> list[float]:
    """The incumbent's inner loop, `admission.py:1328-1338`, parameterised by consideration order."""
    remaining = available
    kept = [0.0] * len(units)
    for i in order:
        u = units[i]
        if u.unit_risk_pct <= remaining + EPS:
            remaining -= u.unit_risk_pct
            kept[i] = u.unit_risk_pct
    return kept


def arm_first_fit_descending(units, available, rng=None):
    order = sorted(range(len(units)), key=lambda i: -(units[i].confidence or 0.0))
    return _first_fit(units, available, order)


def arm_ascending_conviction(units, available, rng=None):
    order = sorted(range(len(units)), key=lambda i: (units[i].confidence or 0.0))
    return _first_fit(units, available, order)


def arm_smallest_first(units, available, rng=None):
    order = sorted(range(len(units)), key=lambda i: units[i].unit_risk_pct)
    return _first_fit(units, available, order)


def arm_largest_first(units, available, rng=None):
    order = sorted(range(len(units)), key=lambda i: -units[i].unit_risk_pct)
    return _first_fit(units, available, order)


def arm_worst_expectancy_drop(units, available, rng=None):
    """Drop the lowest-conviction remaining unit until the whole remaining set fits."""
    alive = sorted(range(len(units)), key=lambda i: -(units[i].confidence or 0.0))
    while alive and sum(units[i].unit_risk_pct for i in alive) > available + EPS:
        alive.pop()                       # the tail is the lowest conviction
    kept = [0.0] * len(units)
    for i in alive:
        kept[i] = units[i].unit_risk_pct
    return kept


def arm_proportional_scaling(units, available, rng=None):
    """D1's recommended fix — never drop, scale the whole book down to fit."""
    total = sum(u.unit_risk_pct for u in units)
    if total <= available + EPS:
        return [u.unit_risk_pct for u in units]
    if total <= 0:
        return [0.0] * len(units)
    scale = available / total
    return [u.unit_risk_pct * scale for u in units]


def arm_random_first_fit(units, available, rng):
    order = list(range(len(units)))
    rng.shuffle(order)
    return _first_fit(units, available, order)


def _optimal(units, available, key):
    """Exact max-subset by enumeration.  Unit sets are tiny (live max 4; synthetic capped)."""
    n = len(units)
    best_val, best_set = 0.0, ()
    for r in range(n, 0, -1):
        for combo in combinations(range(n), r):
            if sum(units[i].unit_risk_pct for i in combo) <= available + EPS:
                val = sum(key(units[i]) for i in combo)
                if val > best_val + EPS:
                    best_val, best_set = val, combo
    kept = [0.0] * n
    for i in best_set:
        kept[i] = units[i].unit_risk_pct
    return kept


def arm_optimal_deployed(units, available, rng=None):
    return _optimal(units, available, lambda u: u.unit_risk_pct)


def arm_optimal_conviction(units, available, rng=None):
    return _optimal(units, available, lambda u: u.conviction_value)


ARMS = {
    "first_fit_descending": arm_first_fit_descending,
    "proportional_scaling": arm_proportional_scaling,
    "smallest_first": arm_smallest_first,
    "largest_first": arm_largest_first,
    "worst_expectancy_drop": arm_worst_expectancy_drop,
    "ascending_conviction": arm_ascending_conviction,
    "optimal_deployed": arm_optimal_deployed,
    "optimal_conviction": arm_optimal_conviction,
}
INCUMBENT = "first_fit_descending"
NULL_ARM = "random_first_fit"


# --------------------------------------------------------------------------------------------
# evidence
# --------------------------------------------------------------------------------------------
def load_recorded(packets: Path):
    """Recorded (headroom, would_units) pairs and the distinct governor-state census."""
    opener = gzip.open if packets.suffix == ".gz" else open
    with opener(packets, "rb") as fh:
        head = fh.read(40)
    if head.startswith(b"version https://git-lfs"):
        raise SystemExit(f"packet source is an unhydrated LFS pointer: {packets}")

    gov_states, cases, unit_reasons, observed_clusters = {}, [], {}, Counter()
    with (gzip.open if packets.suffix == ".gz" else open)(packets, "rt") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            pkt = json.loads(line)
            bridge = pkt.get("bridge") or {}
            gov = bridge.get("governor")
            if not isinstance(gov, dict):
                continue
            ns = pkt.get("namespace")
            key = (ns, gov.get("allow_new_entries"), gov.get("available_gross_risk_pct"),
                   gov.get("size_cap_multiplier"), gov.get("reason"))
            if key not in gov_states:
                gov_states[key] = pkt.get("created_at_utc")
            wu = bridge.get("would_units") or []
            for u in wu:
                unit_reasons[u.get("reason")] = unit_reasons.get(u.get("reason"), 0) + 1
                observed_clusters[str(u.get("cluster"))] += 1
            if not wu:
                continue
            units = [Unit(str(u.get("cluster")), float(u.get("confidence") or 0.0),
                          float(u.get("unit_risk_pct") or 0.0)) for u in wu]
            cases.append({
                "namespace": ns,
                "created_at_utc": pkt.get("created_at_utc"),
                "available": float(gov.get("available_gross_risk_pct") or 0.0),
                "units": units,
            })
    # distinct (headroom, unit-set) cases, so re-emitted identical cycles do not vote twice
    seen, distinct = set(), []
    for c in cases:
        sig = (c["namespace"], round(c["available"], 9),
               tuple(sorted((u.cluster, u.confidence, u.unit_risk_pct) for u in c["units"])))
        if sig in seen:
            continue
        seen.add(sig)
        distinct.append(c)
    return gov_states, cases, distinct, unit_reasons, observed_clusters


def live_cluster_map():
    from src.components.ultimate_book import admission as A
    sleeves, err = A.resolve_market_expansion_sleeves(policy=LIVE_EXPANSION_POLICY)
    if err:
        raise SystemExit(f"market expansion policy unresolved: {err}")
    reg = A.effective_registry(
        include_clean3=False, include_clean4=False,
        include_candidate_book=True, candidate_book_sleeves=list(LIVE_CANDIDATE_SLEEVES),
        include_market_expansion_book=True, market_expansion_sleeves=sleeves,
    )
    out: dict[str, float] = {}
    for spec in reg.values():
        out[spec.asset_class] = max(out.get(spec.asset_class, 0.0), float(spec.confidence))
    return out


# --------------------------------------------------------------------------------------------
# runner
# --------------------------------------------------------------------------------------------
def run_case(units, available, rng, null_draws):
    results = {}
    for name, fn in ARMS.items():
        results[name] = _keep_mask_to_result(units, fn(units, available), available)
    nulls = [_keep_mask_to_result(units, arm_random_first_fit(units, available, rng), available)
             for _ in range(null_draws)]
    # A SINGLE draw, kept separate. Comparing every deterministic arm against the MEAN of
    # `null_draws` random orders divides the null's per-case standard deviation by sqrt(n) and
    # inflates any paired significance by the same factor; an adversarial pass measured the
    # incumbent's edge at 0.99 sigma per case against a single draw and 7.96 sigma against the
    # mean of 64. The single-draw arm is the fair paired comparator and both are reported.
    results["random_first_fit_single_draw"] = nulls[0]
    # How often the top-conviction unit is UNSEATABLE: its own risk exceeds the whole headroom, so
    # no subset algorithm whatsoever could admit it. This is the floor of `top_starved`, and the
    # incumbent sits exactly on it by construction (it tests the top unit against full headroom
    # first). Reporting the floor stops 0.28 % reading as a discovered property.
    top_i = max(range(len(units)), key=lambda i: units[i].confidence) if units else None
    results["__top_infeasible"] = bool(
        top_i is not None and units[top_i].unit_risk_pct > available + EPS)
    results[NULL_ARM] = {
        "deployed": statistics.fmean(n["deployed"] for n in nulls),
        "conviction": statistics.fmean(n["conviction"] for n in nulls),
        "n_admitted": statistics.fmean(n["n_admitted"] for n in nulls),
        "top_full": statistics.fmean(1.0 if n["top_full"] else 0.0 for n in nulls),
        "top_starved": statistics.fmean(1.0 if n["top_starved"] else 0.0 for n in nulls),
        "headroom_used": statistics.fmean(n["headroom_used"] for n in nulls),
        "kept": None,
    }
    return results


def summarise(values: list[float]) -> dict:
    if not values:
        return {"n": 0}
    v = sorted(values)
    def q(p):
        return v[min(len(v) - 1, max(0, int(round(p * (len(v) - 1)))))]
    return {
        "n": len(v), "mean": statistics.fmean(v), "min": v[0], "p05": q(0.05), "p25": q(0.25),
        "median": statistics.median(v), "p75": q(0.75), "p95": q(0.95), "max": v[-1],
    }


def _sign_test(deltas: list[float]) -> dict:
    """Two-sided exact sign test on the paired deltas, ties dropped.

    Deliberately non-parametric: the delta distributions are spiky (an exact zero whenever the cap
    does not bind, and a handful of discrete jumps when it does), so a t-test would be reporting a
    normal approximation of something visibly not normal.
    """
    pos = sum(1 for d in deltas if d > EPS)
    neg = sum(1 for d in deltas if d < -EPS)
    n = pos + neg
    if n == 0:
        return {"n_nonzero": 0, "n_pos": 0, "n_neg": 0, "p_two_sided": 1.0, "log10_p": 0.0}
    # log space: n reaches thousands here, so 2**n overflows a float outright.
    from math import lgamma, log, log10, exp
    lognchoose = [lgamma(n + 1) - lgamma(i + 1) - lgamma(n - i + 1) for i in range(min(pos, neg) + 1)]
    m = max(lognchoose)
    log_tail = m + log(sum(exp(x - m) for x in lognchoose)) - n * log(2.0)
    log10_p = (log_tail + log(2.0)) / log(10.0)
    return {"n_nonzero": n, "n_pos": pos, "n_neg": neg,
            "p_two_sided": min(1.0, exp(log_tail + log(2.0))) if log_tail > -700 else 0.0,
            "log10_p": min(0.0, log10_p)}


def run_arena(cases, rng, null_draws, label):
    """`cases` is a list of (units, available).  Returns the per-arm distributions."""
    metrics = ("deployed", "conviction", "n_admitted", "top_full", "top_starved", "headroom_used")
    per_arm: dict[str, dict[str, list]] = {}
    binding_idx: list[int] = []
    shortfall_rows = []
    top_infeasible: list[bool] = []
    utilizations: list[float] = []
    for case_i, (units, available) in enumerate(cases):
        total = sum(u.unit_risk_pct for u in units)
        binds = total > available + EPS
        if binds:
            binding_idx.append(case_i)
        res = run_case(units, available, rng, null_draws)
        top_infeasible.append(res.pop("__top_infeasible"))
        utilizations.append(total / available if available > EPS else float("inf"))
        opt_dep = res["optimal_deployed"]["deployed"]
        opt_con = res["optimal_conviction"]["conviction"]
        for name, r in res.items():
            slot = per_arm.setdefault(name, {m: [] for m in metrics}
                                      | {"shortfall_deployed": [], "shortfall_conviction": []})
            for m in metrics:
                slot[m].append(float(r[m]))
            slot["shortfall_deployed"].append(opt_dep - r["deployed"])
            slot["shortfall_conviction"].append(opt_con - r["conviction"])
        if binds:
            inc = res[INCUMBENT]
            shortfall_rows.append({
                "available": available,
                "requested": total,
                "utilization": total / available if available > 0 else None,
                "units": [[u.cluster, u.confidence, u.unit_risk_pct] for u in units],
                "incumbent_deployed": inc["deployed"],
                "optimal_deployed": opt_dep,
                "shortfall": opt_dep - inc["deployed"],
                "shortfall_frac_of_optimal": (opt_dep - inc["deployed"]) / opt_dep if opt_dep > 0 else 0.0,
                "incumbent_top_full": inc["top_full"],
                "incumbent_top_starved": inc["top_starved"],
            })

    out = {"label": label, "n_cases": len(cases), "n_binding_cases": len(binding_idx), "arms": {},
           "top_unit_infeasible_rate_on_binding": (
               sum(1 for i in binding_idx if top_infeasible[i]) / len(binding_idx)
               if binding_idx else 0.0),
           "top_unit_infeasible_note": (
               "the top-conviction unit's own risk exceeds the whole headroom, so NO algorithm can "
               "seat it. This is the floor of top_starved; an arm at this rate has starvation "
               "forced on it, not chosen."),
           "utilization": summarise([u for u in utilizations if u != float("inf")])}
    for name, slots in per_arm.items():
        entry = {k: summarise(v) for k, v in slots.items() if v}
        # binding-only distributions: the non-binding cases are identical across every arm and
        # would otherwise dilute every statistic toward "no difference".
        entry["binding_only"] = {
            k: summarise([slots[k][i] for i in binding_idx])
            for k in slots if binding_idx
        }
        out["arms"][name] = entry

    # paired deltas vs the incumbent AND vs the null, on binding cases only
    inc = per_arm[INCUMBENT]
    null = per_arm["random_first_fit_single_draw"]     # the FAIR paired comparator
    paired = {}
    for name, slots in per_arm.items():
        row = {}
        for base_name, base in (("vs_incumbent", inc),
                                ("vs_null_single_draw", null),
                                ("vs_null_mean_of_draws", per_arm[NULL_ARM])):
            if name == ({"vs_incumbent": INCUMBENT,
                         "vs_null_single_draw": "random_first_fit_single_draw",
                         "vs_null_mean_of_draws": NULL_ARM}[base_name]):
                continue
            block = {}
            for m in ("deployed", "conviction"):
                d = [slots[m][i] - base[m][i] for i in binding_idx]
                block[m] = {"delta": summarise(d), "sign_test": _sign_test(d),
                            "win_rate": (sum(1 for x in d if x > EPS) / len(d)) if d else None,
                            "loss_rate": (sum(1 for x in d if x < -EPS) / len(d)) if d else None}
            row[base_name] = block
        paired[name] = row
    out["paired_on_binding_cases"] = paired

    shortfall_rows.sort(key=lambda r: -r["shortfall_frac_of_optimal"])
    out["worst_incumbent_shortfalls"] = shortfall_rows[:15]
    return out


def synth_cases(cluster_map, rng, n_cases, headrooms, max_clusters, base_risk, kelly_bins):
    """Unit sets drawn from the live 13-cluster confidence map at live-shaped unit risks.

    A unit's risk is `base_risk * conf * kelly * gov_mult`; `gov_mult` is folded into the recorded
    headroom's own regime, so it is drawn here from the recorded `size_cap_multiplier` support.
    """
    clusters = sorted(cluster_map)
    cases = []
    for _ in range(n_cases):
        k = rng.randint(2, max_clusters)
        chosen = rng.sample(clusters, min(k, len(clusters)))
        units = []
        for c in chosen:
            conf = cluster_map[c] * rng.choice(kelly_bins)
            units.append(Unit(c, cluster_map[c], base_risk * conf))
        cases.append((units, rng.choice(headrooms)))
    return cases


def reproduce_d1_published_cases(cluster_map) -> dict:
    """Independent check: reproduce D1's own published numbers before trusting this harness.

    `SLEEVE_BOOK_DEFECT_REGISTER.md:110-132` publishes two things — a four-cluster headroom table
    and a 28.6 % shortfall case.  Both are at base_risk 0.02 with a uniform Kelly ×1.241.  If this
    harness cannot reproduce them, its own numbers are not trustworthy either.
    """
    K = 1.241
    def unit(cluster):
        return Unit(cluster, cluster_map[cluster], 0.02 * cluster_map[cluster] * K)

    four = [unit("metals"), unit("crypto"), unit("energy"), unit("index")]
    table = []
    for headroom in (0.0400, 0.0250, 0.0200, 0.0150):
        kept = arm_first_fit_descending(four, headroom)
        opt = arm_optimal_deployed(four, headroom)
        table.append({
            "headroom": headroom,
            "admitted": [f"{u.cluster}({u.confidence})" for u, k in zip(four, kept) if k > EPS],
            "shed": [f"{u.cluster}({u.confidence})" for u, k in zip(four, kept) if k <= EPS],
            "deployed": round(sum(kept), 8),
            "max_deployable": round(sum(opt), 8),
            "ffd_is_optimal": abs(sum(kept) - sum(opt)) <= EPS,
        })

    shortfall_set = [unit("crypto"), unit("jpy_fx"), unit("energy"), unit("metal_reversion")]
    ffd = arm_first_fit_descending(shortfall_set, 0.031)
    opt = arm_optimal_deployed(shortfall_set, 0.031)
    shortfall = {
        "headroom": 0.031,
        "ffd_admits": [u.cluster for u, k in zip(shortfall_set, ffd) if k > EPS],
        "ffd_deployed": round(sum(ffd), 8),
        "optimal_admits": [u.cluster for u, k in zip(shortfall_set, opt) if k > EPS],
        "optimal_deployed": round(sum(opt), 8),
        "shortfall": round(sum(opt) - sum(ffd), 8),
        "shortfall_frac_of_optimal": round((sum(opt) - sum(ffd)) / sum(opt), 6),
        "register_published": {"ffd_deployed": 0.021718, "optimal_deployed": 0.030404,
                               "shortfall": 0.008687, "shortfall_pct": 28.6},
    }
    shortfall["reproduces_register"] = (
        abs(shortfall["ffd_deployed"] - 0.021718) < 5e-6
        and abs(shortfall["optimal_deployed"] - 0.030404) < 5e-6
    )
    return {"four_cluster_headroom_table": table, "twenty_eight_percent_shortfall": shortfall,
            "kelly_multiplier_used": K, "base_risk_per_unit": 0.02}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--packets", type=Path, default=DEFAULT_PACKETS)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--seed", type=int, default=20260727)
    ap.add_argument("--null-draws", type=int, default=64)
    ap.add_argument("--synth-cases", type=int, default=20000)
    ap.add_argument("--max-clusters", type=int, default=6)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    gov_states, all_cases, distinct_cases, unit_reasons, observed_clusters = load_recorded(args.packets)
    cluster_map = live_cluster_map()

    headrooms = sorted({round(k[2], 9) for k in gov_states if k[2] is not None})
    nonzero_headrooms = [h for h in headrooms if h > 0]

    report: dict = {
        "schema": SCHEMA,
        "packet_source": str(args.packets),
        "seed": args.seed,
        "incumbent_arm": INCUMBENT,
        "null_control_arm": NULL_ARM,
        "null_draws_per_case": args.null_draws,
        "shed_source": "src/components/ultimate_book/admission.py:1319-1339",
        "evidence_census": {
            "distinct_governor_states": len(gov_states),
            "distinct_headroom_values": len(headrooms),
            "headroom_min": min(headrooms), "headroom_max": max(headrooms),
            "headroom_min_nonzero": min(nonzero_headrooms),
            "packets_with_would_units": len(all_cases),
            "distinct_headroom_and_unitset_cases": len(distinct_cases),
            "recorded_unit_reason_counts": unit_reasons,
            "live_cluster_confidence_map": cluster_map,
            "clusters_observed_in_recorded_would_units": dict(observed_clusters.most_common()),
            "clusters_in_map_never_observed": sorted(set(cluster_map) - set(observed_clusters)),
            "recorded_units_per_case_histogram": dict(sorted(
                Counter(len(c["units"]) for c in distinct_cases).items())),
        },
    }

    report["d1_reproduction"] = reproduce_d1_published_cases(cluster_map)

    # ---- arena A: exactly what was recorded --------------------------------------------------
    recorded = [(c["units"], c["available"]) for c in distinct_cases]
    max_util = max((sum(u.unit_risk_pct for u in us) / av) for us, av in recorded if av > 0)
    report["arena_recorded"] = run_arena(recorded, rng, args.null_draws, "recorded")
    report["arena_recorded"]["max_utilization"] = max_util
    report["arena_recorded"]["note"] = (
        "The cap never binds on recorded evidence: max utilization "
        f"{max_util:.6f}, zero units carry gross_risk_cap_would_exceed. Every arm is identical here "
        "by construction; this arena exists to put that on the record, not to discriminate."
    )

    # ---- arena B: recorded unit sets, headroom swept down -------------------------------------
    stress = {}
    for squeeze in (1.0, 0.75, 0.5, 0.35, 0.25, 0.15, 0.10, 0.05):
        cases = [(us, av * squeeze) for us, av in recorded]
        stress[f"headroom_x{squeeze}"] = run_arena(cases, rng, args.null_draws,
                                                   f"recorded_units_headroom_x{squeeze}")
    report["arena_recorded_units_headroom_stress"] = stress

    # ---- arena C: synthetic sets from the live cluster map x recorded headrooms ----------------
    kelly_bins = [0.748, 0.991, 1.241]        # the half-Kelly bins observed in the packet tags
    synth = synth_cases(cluster_map, rng, args.synth_cases, nonzero_headrooms,
                        args.max_clusters, 0.02, kelly_bins)
    report["arena_synthetic"] = run_arena(synth, rng, args.null_draws, "synthetic")
    report["arena_synthetic"]["generator"] = {
        "n_cases": args.synth_cases,
        "clusters_per_case": f"uniform 2..{args.max_clusters}",
        "base_risk_per_unit": 0.02,
        "kelly_bins": kelly_bins,
        "headroom_draw": "uniform over the recorded distinct non-zero available_gross_risk_pct values",
        "note": "unit risk = base_risk * cluster_max_conf * kelly_bin, matching admission.py:1192",
    }

    # ---- arena D: the same measurement restricted to clusters that ACTUALLY fired -------------
    # An adversarial pass found three clusters in the map -- metals (1.00), energy (0.80) and
    # fxcross_vol_state_squeeze (0.12) -- occur ZERO times in the 6,355 recorded would_units while
    # supplying ~23 % of synthetic units and appearing in ~94 % of binding cases. They are exactly
    # the high-confidence clusters, so they manufacture the binding regime. This arena removes
    # them, and it is the conservative reading of the whole pack.
    observed_map = {c: v for c, v in cluster_map.items() if c in observed_clusters}
    synth_obs = synth_cases(observed_map, rng, args.synth_cases, nonzero_headrooms,
                            args.max_clusters, 0.02, kelly_bins)
    report["arena_synthetic_observed_clusters_only"] = run_arena(
        synth_obs, rng, args.null_draws, "synthetic_observed_clusters_only")
    report["arena_synthetic_observed_clusters_only"]["generator"] = {
        "clusters": sorted(observed_map),
        "excluded_never_observed": sorted(set(cluster_map) - set(observed_map)),
        "note": ("same generator as arena_synthetic, restricted to clusters that appear in the "
                 "recorded would_units at least once"),
    }

    args.out.mkdir(parents=True, exist_ok=True)
    dest = args.out / "SHED_AB.json"
    dest.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")
    print(f"wrote {dest}")

    # ---- console summary ----------------------------------------------------------------------
    print(f"\ndistinct governor states: {len(gov_states)}   distinct headrooms: {len(headrooms)}")
    print(f"recorded (headroom, unit-set) cases: {len(recorded)}   max utilization: {max_util:.6f}")
    print(f"recorded unit reasons: {unit_reasons}")
    for arena_key in ("arena_recorded", "arena_synthetic",
                      "arena_synthetic_observed_clusters_only"):
        a = report[arena_key]
        print(f"\n== {a['label']}: {a['n_cases']} cases, {a['n_binding_cases']} binding "
              f"({100.0 * a['n_binding_cases'] / max(1, a['n_cases']):.2f} %)"
              f"  | top-unit infeasible on {a['top_unit_infeasible_rate_on_binding']*100:.2f} % of them"
              f"  | utilization median {a['utilization'].get('median', float('nan')):.3f}")
        print("   [binding cases only]")
        print(f"{'arm':24s} {'deployed':>12s} {'conviction':>12s} {'hdrm used':>10s} "
              f"{'top_full':>9s} {'top_starv':>10s} {'Δdep vs null':>13s} {'p(sign)':>9s}")
        for name in list(ARMS) + [NULL_ARM, "random_first_fit_single_draw"]:
            s = a["arms"].get(name)
            if not s or not s.get("binding_only") or not s["binding_only"].get("deployed"):
                continue
            b = s["binding_only"]
            pv = a["paired_on_binding_cases"].get(name, {}).get("vs_null_single_draw", {})
            dd = pv.get("deployed", {}).get("delta", {}).get("mean")
            pp = pv.get("deployed", {}).get("sign_test", {}).get("p_two_sided")
            print(f"{name:24s} {b['deployed']['mean']:12.8f} {b['conviction']['mean']:12.8f} "
                  f"{b['headroom_used']['mean']:10.4f} {b['top_full']['mean']:9.4f} "
                  f"{b['top_starved']['mean']:10.4f} "
                  f"{'' if dd is None else format(dd, '13.8f')} {'' if pp is None else format(pp, '9.2e')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
