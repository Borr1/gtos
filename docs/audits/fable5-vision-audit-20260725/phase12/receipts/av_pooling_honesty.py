#!/usr/bin/env python3
"""Session AV — what pooling actually buys, per family (AV-4, B1647-B1649... B1660).

    python3 docs/audits/fable5-vision-audit-20260725/phase12/receipts/av_pooling_honesty.py
    ... --families fam_energy_fvg_retest_energy_h4 fam_volume_surge_reversal_index_d1
    ... --all-coherent      # AF's two two-clause-coherent families (default)
    ... --all               # every family AF swept, for the census

THE QUESTION, AND WHY IT ROUTES EVERY FUTURE DATA ASK
------------------------------------------------------
"The family needs more sample" is not one prescription, it is two, and they are bought with
different money:

* **calendar time** --- only more YEARS help. Buying it means a data fetch or waiting.
* **width** --- more MEMBERS help. Buying it means a generator run over symbols already held.

The estate has been treating them as interchangeable. They are not, and the reason is
mechanical: the gate's null is a **block sign-flip on the pooled DAILY series**
(AO §5.3 measured this directly --- nine BTC members pooled went from p 0.0011 solo to 0.0067,
6.1x the WRONG way). So the resolution currency is **blocks**, not trades. A member that
trades on days another member already covers adds a trade to an existing block and buys
**zero** resolution. A member that trades on days nobody covers adds a block and buys some.

So this file measures, per family:

1. **The p-floor and its headroom.** `1 / 2^n_blocks` is the smallest p a block sign-flip can
   attain. If the family's BH rank-1 bar sits at or below it, the test cannot admit there at
   any effect size and the honest report is `NOT_EVALUABLE_AT_RANK`, not a p (wave-11 §2).
2. **The marginal block yield of every member** --- how many decision-days does member *i*
   contribute that no other member of the family has. That number IS the width lever's size.
3. **Blocks per calendar year**, which is the calendar-time lever's size.
4. **The requirement, in both currencies.** From the observed effect and dispersion, the
   trades needed to reach the bar; then that requirement expressed as YEARS at the family's
   own trade rate and as MEMBERS at its own marginal-block yield.
5. **The verdict**: CALENDAR_TIME_ONLY / WIDTH_HELPS / BOTH / NEITHER_REACHES.

Every arm carries the chronological fold table and its `maxbars` share (wave-12 §4).
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import gzip
import json
import math
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.costs.model import load_broker_true_costs  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
)
from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import era_population as EP  # noqa: E402
from src.research_infra.walkforward import run_gate  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402
from src.research_infra.walkforward.panel import TradeRecord  # noqa: E402

AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
HERE = AUD / "phase12/receipts"
AF_TRADES = AUD / "phase7/receipts/AF_FAMILY_TRADES.json.gz"
AF_REPAIRS = AUD / "phase7/receipts/AF_REPAIRS_V1.json"
FAMILY_V6 = HERE / "CANDIDATE_FAMILY_V6.json"
OUT = HERE / "AV_POOLING_HONESTY_V1.json"
COSTS = REPO / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"

SERVER = "FTMO-Server3"
ACCOUNT = "FTMO"
BANDS = (None, "low", "mid", "high")

#: AF's two-clause coherence test picks these two of 30: dispersion ratio < 1 AND every member
#: positive. They are the families the estate actually pools for sample, so they are the
#: default scope; `--all` runs the census.
COHERENT = ("fam_energy_fvg_retest_energy_h4", "fam_volume_surge_reversal_index_d1")


def load_af():
    """AF's trades, its per-family dilution table, and the member -> family map.

    The map is **rebuilt from the production `family.FamilyMember`**, not parsed out of the
    member name: the family key is `fam_<mechanism>_<ASSET CLASS>_<tf>` and the asset class is
    not recoverable from `mxf_<mechanism>_<symbol>_<tf>` by string surgery. AR §5.7's finding
    is the argument --- two naming conventions for one object made a triple-count invisible to
    the eye and to the ratchet, and it was caught by identity rather than by name.
    """
    import yaml

    from src.components.ultimate_book.bar_provider import TF_D1, TF_H4
    from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver
    from src.research_infra.walkforward import family as fam

    doc = json.load(gzip.open(AF_TRADES, "rt"))
    rep = json.load(AF_REPAIRS.open())
    by_family = rep["R8_best_cell_and_dilution"]["dilution"]["by_family"]

    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res = build_broker_symbol_resolver(prof)
    supports = getattr(res, "supports", None)
    symbols = sorted({rows[0]["symbol_canonical"] for rows in doc["trades"].values() if rows})
    tf_of = {"D1": TF_D1, "H4": TF_H4}
    member_family: dict[str, str] = {}
    grid_members = []
    for mech, tfs in doc["sweep"].items():
        for tfs_name in tfs:
            g = fam.family_members([mech], (tf_of[tfs_name],), symbols=symbols,
                                   broker_symbol=res,
                                   profile_supports=(supports if callable(supports) else None))
            grid_members.extend(g.members)
            for m in g.members:
                member_family[m.member] = m.family

    members_of: dict[str, list[str]] = collections.defaultdict(list)
    unmapped = []
    for member in doc["trades"]:
        f = member_family.get(member)
        (members_of[f].append(member) if f else unmapped.append(member))
    if unmapped:
        # Loud, not silent: an unmapped member would quietly shrink a family and make pooling
        # look narrower than it is.
        print(f"WARNING: {len(unmapped)} AF members could not be mapped to a family "
              f"(first: {unmapped[:3]})", file=sys.stderr)
    return doc, by_family, {k: sorted(v) for k, v in members_of.items()}, unmapped, grid_members


def to_records(rows, sleeve):
    return {sleeve: [TradeRecord(
        sleeve=sleeve, symbol=r["symbol"],
        entry_utc=dt.datetime.fromisoformat(r["entry_utc"]),
        exit_utc=dt.datetime.fromisoformat(r["exit_utc"]),
        direction=int(r["direction"]),
        sl_distance_price=float(r["sl_distance_price"]),
        entry_price=float(r["entry_price"]), r_gross=float(r["r_gross"]),
        features={"decision_day": r["decision_day"], "hold_hours": r["hold_hours"],
                  "symbol_canonical": r["symbol_canonical"],
                  "decision_bar_iso": r["decision_bar_iso"],
                  "exit_reason": r["exit_reason"],
                  "mfe_r": r["mfe_r"], "mae_r": r["mae_r"]}) for r in rows]}


def block_economics(rows_by_member: dict[str, list[dict]]) -> dict:
    """The two currencies, measured. Blocks are DECISION DAYS --- the gate's own unit."""
    days_of = {m: {r["decision_day"] for r in rows} for m, rows in rows_by_member.items()}
    all_days: set[str] = set().union(*days_of.values()) if days_of else set()
    marginal = {}
    for m, days in days_of.items():
        others = set().union(*(d for k, d in days_of.items() if k != m)) if len(days_of) > 1 else set()
        marginal[m] = {
            "n_days": len(days),
            "n_days_unique_to_this_member": len(days - others),
            "share_unique": round(len(days - others) / max(1, len(days)), 4),
            "n_trades": len(rows_by_member[m]),
        }
    if all_days:
        ds = sorted(dt.date.fromisoformat(d) for d in all_days)
        span_years = max(1e-9, (ds[-1] - ds[0]).days / 365.25)
    else:
        span_years = 0.0
    n_trades = sum(len(v) for v in rows_by_member.values())
    return {
        "n_members": len(rows_by_member),
        "n_trades": n_trades,
        "n_blocks_decision_days": len(all_days),
        "span_years": round(span_years, 4),
        "blocks_per_year": round(len(all_days) / span_years, 3) if span_years else None,
        "trades_per_block": round(n_trades / max(1, len(all_days)), 4),
        "per_member": marginal,
        "mean_share_of_days_unique_to_a_member": round(
            statistics.fmean([v["share_unique"] for v in marginal.values()]), 4) if marginal else None,
        "p_floor_from_blocks": 2.0 ** (-len(all_days)) if len(all_days) < 200 else 0.0,
        "what_the_numbers_mean": (
            "blocks are decision days because the gate's null is a block sign-flip on the "
            "pooled daily series. `share_unique` near 1 means a member brings its own days and "
            "width buys resolution; near 0 means it lands on days the family already has and "
            "width buys only trades."),
    }


def requirement(p_raw, bar, n_trades, n_blocks) -> dict:
    """How much more of each currency the family needs, from its own numbers.

    The trade requirement uses the standard z-scaling of a mean test: to move a p-value from
    `p_raw` to `bar`, the effective sample scales as `(z_bar / z_now)^2`. It is an estimate,
    stated as one, and it is the same arithmetic AR §5.6 used to price its near-miss at
    "4.7x the data".
    """
    def z(p):
        # inverse normal survival, Acklam-free: bisect, which is exact enough at this scale
        lo, hi = 0.0, 12.0
        for _ in range(200):
            mid = (lo + hi) / 2
            s = 0.5 * math.erfc(mid / math.sqrt(2))
            if s > p:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    if p_raw is None or p_raw <= 0 or p_raw >= 1 or bar <= 0:
        return {"evaluable": False, "why": "p_raw or bar outside (0,1)"}
    z_now, z_bar = z(p_raw), z(bar)
    if z_now <= 0:
        return {"evaluable": False, "why": "observed effect has the wrong sign for the test"}
    factor = (z_bar / z_now) ** 2
    return {
        "evaluable": True,
        "p_raw": p_raw, "bh_rank1_bar": bar,
        "shortfall_x": round(p_raw / bar, 3),
        "data_multiple_needed": round(factor, 3),
        "trades_needed": int(math.ceil(n_trades * factor)),
        "extra_trades_needed": int(math.ceil(n_trades * (factor - 1))),
        "blocks_needed": int(math.ceil(n_blocks * factor)),
        "extra_blocks_needed": int(math.ceil(n_blocks * (factor - 1))),
        "caveat": ("z-scaling assumes the effect size holds as the sample grows, which is the "
                   "OPTIMISTIC case: AN measured a 7.6x chronological decay that every gate "
                   "passes, so a family whose recent folds are weaker needs more than this."),
    }


def gate_one(rows, sleeve, costs, band, loaded, ledger, label, grid_members) -> dict:
    o = OPTIONS["B_balanced"]
    spec = o.with_(spec_id=f"{o.spec_id}_av_pool_{label}",
                   sleeve_symbol_allowlist={sleeve: tuple(sorted({r["symbol"] for r in rows}))},
                   spread_band=band)
    spec = CF.with_declared_family(spec, "ESTATE_UNION_V1", loaded=loaded)
    recs, spec, mix = EP.apply("RECORDED", to_records(rows, sleeve), spec,
                               account=ACCOUNT, band=(band or "mid"))
    # Every cell in this cohort is a surface expansion that sits in no registry, so gate.py's
    # hard fidelity refusal returns NOT_EVALUABLE on `port_fidelity_unmeasured` for all of them
    # -- which is exactly what the first run of this file did, on every arm, and what AQ's
    # `wipeout` signal (B1435) exists to make loud instead of silent. `expanded_surface` is for
    # generating; `fidelity_scope` is for SCORING, and the records are removed again on exit.
    from src.research_infra.walkforward import family as _fam
    with _fam.fidelity_scope(grid_members):
        res = run_gate(recs, spec, costs=costs, server=SERVER, diagnose=True)
    wipe = res.family.get("wipeout") or {}
    out = {"spec_sha256": spec.seal(), "population_mix": mix,
           "declared_family_size": spec.declared_family_size,
           "bh_rank1_bar": round(spec.alpha / spec.declared_family_size, 10),
           "band": band or "flat_37_day_snapshot"}
    if wipe.get("wiped_out"):
        out.update({"verdict": "NOT_EVALUABLE", "wipeout": wipe,
                    "reasons": sorted({r for v in res.verdicts.values() for r in v.reasons})})
        return out
    for _, sv in res.verdicts.items():
        st = sv.gates.get("stability", {})
        fl = (sv.telemetry or {}).get("p_floor", {}) or {}
        diag = sv.telemetry or {}
        out.update({
            "verdict": sv.verdict.value, "n_trades": sv.n_trades,
            "pooled_oos_mean_r": sv.pooled_oos_mean_r,
            "oos_mean_r_per_trade": sv.gates.get("expectancy", {}).get("oos_mean_r_per_trade"),
            "p_raw": sv.p_raw, "q_value": sv.q_value,
            "failing_core_gates": [g for g in ("expectancy", "lifetime", "stability",
                                               "robustness", "significance")
                                   if not sv.gates.get(g, {}).get("pass")],
            "fold_means": st.get("fold_means"),
            "oos_positive_fold_frac": st.get("oos_positive_fold_frac"),
            "n_folds_evaluable": sv.gates.get("sample", {}).get("n_folds_evaluable"),
            "n_thin_folds": sv.gates.get("sample", {}).get("n_thin_folds"),
            "drop_best_retention": sv.gates.get("robustness", {}).get("retention"),
            "coverage_frac": (sv.coverage or {}).get("coverage_frac"),
            "p_floor": fl.get("p_floor"), "n_blocks": fl.get("n_blocks"),
            "p_floor_headroom": ((sv.p_raw / fl["p_floor"])
                                 if (sv.p_raw is not None and fl.get("p_floor")) else None),
            "regime_inflation_flag": (diag.get("regime_inflation") or {}).get("contamination_flag"),
            "in_sample_mean_r": (diag.get("in_sample") or {}).get("mean_is_r"),
            "maxbars_share": round(
                sum(1 for r in rows if r["exit_reason"] == "maxbars") / max(1, len(rows)), 6),
            "reasons": list(sv.reasons),
        })
        if ledger is not None:
            ledger.record(mechanism="pooling_honesty", sleeve=label,
                          variant={"band": band or "flat", "population": "RECORDED",
                                   "option": "B_balanced"},
                          window="af_family_sweep", spec_sha256=spec.seal(),
                          outcome={"ADMIT": "admitted", "REJECT": "rejected",
                                   "NOT_EVALUABLE": "not_evaluable"}.get(
                                       sv.verdict.value, "evaluated"),
                          metric=sv.pooled_oos_mean_r, metric_name="pooled_oos_mean_r",
                          note="AV-4 what pooling buys")
    return out


def verdict_for(econ, pooled, solo) -> dict:
    """CALENDAR_TIME_ONLY / WIDTH_HELPS / BOTH / NEITHER_REACHES, from the measured currencies."""
    bar = pooled.get("bh_rank1_bar")
    floor = pooled.get("p_floor")
    req = pooled.get("requirement") or {}
    unique = econ.get("mean_share_of_days_unique_to_a_member")
    notes = []

    if floor is not None and bar is not None and bar <= floor:
        return {"verdict": "NOT_EVALUABLE_AT_RANK",
                "why": (f"the BH rank-1 bar {bar:.3g} sits at or below the block sign-flip "
                        f"floor {floor:.3g} at {pooled.get('n_blocks')} blocks: no effect size "
                        "can admit here, so the constraint is RESOLUTION and only more BLOCKS "
                        "(i.e. more distinct decision days) can change it"),
                "lever": "blocks"}
    if not req.get("evaluable"):
        return {"verdict": "NEITHER_REACHES", "why": req.get("why", "requirement not evaluable"),
                "lever": None}

    extra_blocks = req["extra_blocks_needed"]
    bpy = econ.get("blocks_per_year") or 0.0
    years = (extra_blocks / bpy) if bpy else None
    # Width's ceiling: even if every remaining member of the class were added, each brings
    # `mean_share_of_days_unique_to_a_member` of its days as NEW blocks.
    width_yield = (unique or 0.0) * (econ["n_blocks_decision_days"] / max(1, econ["n_members"]))
    members_needed = (extra_blocks / width_yield) if width_yield > 0 else None

    if unique is not None and unique < 0.15:
        notes.append(f"members share {1-unique:.0%} of their decision days, so width buys "
                     "trades and almost no resolution --- AO's pooling result, reproduced here")
        lever, verdict = "calendar_time", "CALENDAR_TIME_ONLY"
    elif members_needed is not None and members_needed <= 3 * econ["n_members"]:
        lever, verdict = "both", "BOTH"
    else:
        lever, verdict = "calendar_time", "CALENDAR_TIME_ONLY"

    return {
        "verdict": verdict, "lever": lever,
        "extra_blocks_needed": extra_blocks,
        "years_of_calendar_time_at_this_rate": round(years, 2) if years else None,
        "members_needed_at_this_marginal_yield": (round(members_needed, 1)
                                                  if members_needed else None),
        "marginal_new_blocks_per_added_member": round(width_yield, 2),
        "why": "; ".join(notes) or (
            f"reaching the bar needs {extra_blocks} more decision-day blocks; at "
            f"{bpy} blocks/year that is {years:.1f} more years, and at "
            f"{width_yield:.1f} new blocks per added member it is "
            f"{members_needed:.1f} more members"),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--families", nargs="*", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--census", action="store_true",
                    help="pooled @ mid only, over every family -- the estate-wide "
                         "calendar-vs-width call, without 246 solo gates")
    ap.add_argument("--no-ledger", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    doc, by_family, fam_members, unmapped, grid_members = load_af()
    costs = load_broker_true_costs(COSTS)
    loaded = CF.load_candidate_family(FAMILY_V6)
    ledger = None if args.no_ledger else TrialLedger(DEFAULT_TRIAL_LEDGER, session="AV")

    if args.families:
        families = list(args.families)
    elif args.all:
        families = sorted(fam_members)
    else:
        families = list(COHERENT)

    t0 = time.time()
    out = {}
    for fam in families:
        members = fam_members.get(fam) or []
        if not members:
            out[fam] = {"error": "no members found in AF's artifact"}
            continue
        rows_by_member = {m: doc["trades"].get(m, []) for m in members}
        rows_by_member = {m: v for m, v in rows_by_member.items() if v}
        pooled_rows = [r for v in rows_by_member.values() for r in v]
        econ = block_economics(rows_by_member)

        pooled = {}
        for band in ((None,) if args.census else BANDS) if not args.census else ("mid",):
            g = gate_one(pooled_rows, fam, costs, band, loaded, ledger, f"{fam}|pooled", grid_members)
            if g.get("p_raw") is not None:
                g["requirement"] = requirement(g["p_raw"], g["bh_rank1_bar"],
                                               g.get("n_trades") or len(pooled_rows),
                                               g.get("n_blocks") or econ["n_blocks_decision_days"])
            pooled[band or "flat"] = g

        solo = {}
        for m, rows in ([] if args.census else sorted(rows_by_member.items())):
            g = gate_one(rows, m, costs, "mid", loaded, ledger, f"{fam}|{m}", grid_members)
            if g.get("p_raw") is not None:
                g["requirement"] = requirement(g["p_raw"], g["bh_rank1_bar"],
                                               g.get("n_trades") or len(rows),
                                               g.get("n_blocks") or 1)
            solo[m] = g

        best_solo = min((g for g in solo.values() if g.get("p_raw") is not None),
                        key=lambda g: g["p_raw"], default=None)
        mid = pooled.get("mid", {})
        out[fam] = {
            "af_dilution": by_family.get(fam),
            "block_economics": econ,
            "pooled_by_band": pooled,
            "solo_by_member": solo,
            "what_pooling_bought": {
                "pooled_p_mid": mid.get("p_raw"),
                "best_solo_p_mid": best_solo.get("p_raw") if best_solo else None,
                "pooling_p_ratio": (round(mid["p_raw"] / best_solo["p_raw"], 3)
                                    if (mid.get("p_raw") and best_solo
                                        and best_solo.get("p_raw")) else None),
                "reading": ("a ratio > 1 means pooling made the p WORSE than the best member "
                            "alone --- which is AO's measured result on a same-mechanism, "
                            "same-class pool and the reason the estate stopped assuming "
                            "pooling buys resolution"),
                "pooled_n": mid.get("n_trades"), "pooled_blocks": mid.get("n_blocks"),
                "best_solo_member": (best_solo.get("_member") if best_solo else None),
            },
            "sample_constraint": verdict_for(econ, mid, solo),
            "two_block_counts_and_why_they_differ": {
                "decision_days_in_the_raw_stream": econ["n_blocks_decision_days"],
                "blocks_the_gate_bootstrapped": mid.get("n_blocks"),
                "why": ("the gate bootstraps over the blocks inside its SCORED FOLDS, after the "
                        "population filter, the warmup fold and the thin-fold drop; the raw "
                        "count is every decision day the family ever printed. Both are real "
                        "and only the gate's sets the p-floor, so the resolution verdict is "
                        "taken on the gate's and the acquisition arithmetic on the raw rate."),
            },
        }
        print(f"  {fam}: pooled p {mid.get('p_raw')} "
              f"({mid.get('verdict')}), {econ['n_members']} members, "
              f"{econ['n_blocks_decision_days']} blocks -> "
              f"{out[fam]['sample_constraint']['verdict']}", flush=True)

    payload = {
        "schema": "gtos.wave12.av.pooling_honesty.v1",
        "session": "AV", "blocks": "B1647-B1660",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "source": str(AF_TRADES.relative_to(REPO)),
        "declared_family": str(FAMILY_V6.relative_to(REPO)),
        "rule": "RECORDED / B_balanced alpha 0.10 / ESTATE_UNION_V1, the ratified rule",
        "why_no_new_family_members": (
            "every arm here re-measures an ALREADY DECLARED member or a pool of them at the "
            "ratified rule. AR declared the 9 members of the two coherent families in "
            "CANDIDATE_FAMILY_V4; AF's 246 sit in ESTATE_UNION_V1. Re-gating a declared "
            "member proposes no hypothesis, and the pooled arm is the family's own definition "
            "rather than a new cut."),
        "unmapped_af_members": unmapped,
        "families": out,
        "mode": ("census: pooled @ mid only, every family" if args.census
                 else "full: pooled at 4 bands + every member solo @ mid"),
        "roll_up": collections.Counter(
            f["sample_constraint"]["verdict"] for f in out.values()
            if isinstance(f, dict) and "sample_constraint" in f),
        "seconds_total": round(time.time() - t0, 1),
    }
    (Path(args.out) if args.out else OUT).write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(f"\nwrote {Path(args.out).resolve() if args.out else OUT}")
    print(json.dumps(dict(payload["roll_up"]), indent=1))


if __name__ == "__main__":
    main()
