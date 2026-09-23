"""p3-2 — THE STOP-FLOOR SWEEP. `max(wick + 0.10*ATR, k*ATR)`, k swept, on stored intents.

    python3 .../p3/p3_sweep.py --stage substrate   # build the re-labelled rows, all k
    python3 .../p3/p3_sweep.py --stage gate        # gate them at the ratified rule
    python3 .../p3/p3_sweep.py                     # both

THE GRID IS DECLARED HERE, BEFORE ANY RESULT WAS READ
------------------------------------------------------
    K_GRID = (0.00, 0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 2.00)

Eight cells. `k = 0.00` is the shipped generator exactly (the floor can never bind, because
`wick + 0.10*a > 0` always), and it is the A/B base. `k = 0.25` is not a free parameter: it
is the constant three other generators in this repository already use for the same idiom
(`metals.py:34`, `metals_ob_micro.py:46`, `structural_retest.py:28`), so it is the one cell
that was chosen by another session for another sleeve and therefore cannot be in-sample
here. The top of the grid, 2.00, is a bit over twice the sleeve's median stop of 0.906 ATR,
which is where a "floor" has stopped being a floor and has become a plain ATR stop — the
sweep is deliberately run out to that point so the reader can see the whole curve rather
than the part that flatters it.

WHY THIS IS A RE-LABEL AND NOT A RE-RUN, PROVED RATHER THAN ASSERTED
----------------------------------------------------------------------
`asia_pdl_fade.generate` computes `sd` at `:108`, AFTER every entry gate. The only way `sd`
can change what fires is `if sd <= 0: return None` at `:109-110`, and a floor can only make
`sd` larger. So the trade SET is invariant under k, and CONTROL C2 asserts exactly that:
identical (symbol, decision_bar) sets at every k. What changes is the R unit and, because
the contract is `target_dist = 3.0 * sd`, the target with it.

The ATR needed to build the floor is recomputed from the archive at the decision bar.
`atr14` reads only `bars[i-14 .. i]` (`primitives.py:23-30`), so this is bit-identical to
what the generator saw from its own 220-bar window — and lane p3's census proved it on
these very rows, inverting the shipped stop expression to a max relative error of 3.69e-15
over all 2,827 (`P3_STOP_COUPLING_V1.json -> controls`). CONTROL C1 re-asserts it here.

FOUR ARMS, COPIED FROM LANE m3 AND FOR ITS REASONS
---------------------------------------------------
    walk=old   spread=charged   the published convention. The A/B base.
    walk=qs_*  spread=charged   corrected walk, spread still charged. DOUBLE COUNTS.
                                Published as the strictly conservative bound.
    walk=qs_*  spread=removed   the arm that is arithmetically right: under fill anchoring
                                the R unit already contains the round-trip spread.
    walk=old   spread=removed   isolates the cost change from the walk change.

This matters more here than anywhere else in the estate, because the whole claim under test
is about the ratio of a PRICE-unit cost to a PRICE-unit stop. Getting the spread charged
twice would manufacture exactly the effect the sweep is looking for.

WHAT THE MULTIPLICITY BILL IS, AND THE PRECEDENT FOR IT
--------------------------------------------------------
`asia_pdl_fade` is ALREADY a declared member of `CANDIDATE_BOOK_V1` (V27, `look_taken=true`).
A stop floor changes no trade's existence, so under the estate's own recorded rule it adds
NO member: `CANDIDATE_FAMILY_V2.json -> families.CANDIDATE_BOOK_V1.history[0]
.what_it_does_NOT_add` names *"`asia_pdl_fade`'s stop x target x time-stop grid"* as an
exit-cell grid that adds no member, for exactly this reason (AI section 0: BH corrects for
distinct hypotheses, not for the number of times each is measured).

The sweep is therefore billed the way AO billed its enumerated dial cells
(`REGIME_CONDITIONING_V1.json -> enumeration_bills`): a **within-enumeration Bonferroni**,
`p_bonf = best_p_raw * n_cells`, reported with the largest declared family that would still
admit at alpha 0.10. Both n = 8 (every cell, conservative) and n = 7 (the alternatives to
the shipped contract) are printed, because the choice between them is a judgement and the
reader should not have to take mine.

**And the cumulative honesty, which no artifact in this estate has yet stated in one place:**
`asia_pdl_fade`'s stop axis has been enumerated before. `AK_EXIT_FRONTIER_V2.json` carries
58 exit cells for it, and AO enumerated 13 dial cells. Those looks were taken; they do not
un-take. The cumulative enumeration count is printed in the receipt.

Offline and pure. Reads gzipped JSON and gzipped CSV bars, writes two JSONs.
"""

from __future__ import annotations

import argparse
import collections
import contextlib
import dataclasses
import datetime as dt
import gzip
import json
import math
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(REPO))
AD_DIR = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"
sys.path.insert(0, str(AD_DIR))

import ad_exit_sweep as AD  # noqa: E402

from src.components.ultimate_book.admission import winsorize_R  # noqa: E402
from src.components.ultimate_book.primitives import atr14  # noqa: E402
from src.components.ultimate_book.sleeves import asia_pdl_fade as APF  # noqa: E402
from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import era_population as EP  # noqa: E402
from src.research_infra.walkforward import run_gate  # noqa: E402
from src.research_infra.walkforward.exits import ExitPolicy, replay  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402
from src.research_infra.walkforward.quote_side import (  # noqa: E402
    BarQuote,
    SpreadUnavailable,
    replay_anchor,
    spread_for,
)

HERE = Path(__file__).resolve().parent
P6 = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts"
P18 = REPO / "docs/audits/fable5-vision-audit-20260725/phase18/receipts"
AA_IN = P6 / "AA_ESTATE_TRADES.json.gz"
DECL_V27 = P18 / "CANDIDATE_FAMILY_V27.json"
SUB_OUT = HERE / "P3_SWEEP_SUBSTRATE_V1.json.gz"
GATE_OUT = HERE / "P3_SWEEP_GATE_V1.json"
CTL_OUT = HERE / "P3_SWEEP_CONTROLS_V1.json"

SLEEVE = "asia_pdl_fade"
ACCOUNT, SERVER = "FTMO", "FTMO-Server3"
MAXBARS = 80
TF_MINUTES = {15: 15, 16385: 15, 16388: 240, 16408: 1440}

#: DECLARED BEFORE ANY RESULT WAS READ. See the module docstring.
K_GRID = (0.00, 0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 2.00)

BANDS = ("low", "mid", "high")
ARMS = ("old",) + tuple(f"qs_{b}" for b in BANDS)
BAND_OF_ARM = {"old": None, "qs_low": "low", "qs_mid": "mid", "qs_high": "high"}


# =====================================================================================
# the one patched object — copied from m3_regate.spread_term_removed
# =====================================================================================

@contextlib.contextmanager
def spread_term_removed():
    """Zero `cost_r`'s spread term in-process, keeping every other term and its coverage."""
    from src.costs.model import Measure
    from src.research_infra.walkforward import panel as P

    original = P.cost_r

    def patched(symbol, account, *a, **kw):
        b = original(symbol, account, *a, **kw)
        zero = dataclasses.replace(
            b.spread_r, value=0.0,
            provenance=(b.spread_r.provenance +
                        " | ZEROED by p3: under FILL anchoring the corrected walk already "
                        "charges the round-trip spread as geometry"))
        total = dataclasses.replace(
            b.total_r, value=(b.commission_r.value + b.swap_r.value + b.slippage_r.value),
            provenance="sum of commission + swap + slippage (spread zeroed by p3)")
        assert isinstance(zero, Measure)
        return dataclasses.replace(b, spread_r=zero, total_r=total)

    P.cost_r = patched
    try:
        yield
    finally:
        P.cost_r = original
        assert P.cost_r is original


# =====================================================================================
# substrate
# =====================================================================================

def stop_at_k(bars, i, k: float) -> tuple[float, float, bool]:
    """`(sd, atr, floor_bound)` under `max(wick + STOP_BUF*a, k*a)`.

    The shipped expression is `asia_pdl_fade.py:108`; `APF.STOP_BUF` is imported rather
    than copied so a constant change in the generator cannot silently desynchronise the
    sweep from the thing it is sweeping.
    """
    a = atr14(bars, i)
    wick = bars[i].c - bars[i].l
    base = wick + APF.STOP_BUF * a
    floor = k * a
    return (max(base, floor), a, floor > base)


def build_substrate() -> dict:
    t0 = time.time()
    print("loading bars ...", flush=True)
    series, index, _res = AD.load_bars()
    print(f"  {len(series)} series in {time.time()-t0:.1f}s", flush=True)

    aa = json.load(gzip.open(AA_IN, "rt"))
    rows0 = aa["trades"][SLEEVE]
    print(f"{SLEEVE}: {len(rows0)} stored intents", flush=True)

    ctl: dict = {"C1_atr_inversion": {}, "C2_trade_set_invariance": {},
                 "C3_k0_reproduces_published": {}, "C4_floor_binding_fraction": {},
                 "C5_spread_refusals": {}}

    # ---- CONTROL C1: the shipped stop expression must invert exactly ------------------
    inv = []
    for r in rows0:
        key = (r["symbol"], int(r["timeframe"]))
        if key not in index:
            continue
        i = index[key].get(dt.datetime.fromisoformat(r["decision_bar_iso"]))
        if i is None:
            continue
        bars, _ = series[key]
        sd, a, _ = stop_at_k(bars, i, 0.0)
        inv.append(abs(sd - float(r["sl_distance_price"])) / max(abs(sd), 1e-12))
    ctl["C1_atr_inversion"] = {
        "n": len(inv), "max_rel_err": max(inv) if inv else None,
        "median_rel_err": statistics.median(inv) if inv else None,
        "claim": "max(wick + 0.10*atr14(bars,i), 0) recomputed from the archive reproduces "
                 "the stored sl_distance_price, so the ATR this sweep floors against IS the "
                 "ATR the generator used",
        "pass": bool(inv) and max(inv) < 1e-9,
    }
    print(f"C1 atr inversion: n={len(inv)} max_rel_err={max(inv):.3e}", flush=True)
    if not ctl["C1_atr_inversion"]["pass"]:
        raise SystemExit("C1 FAILED — the sweep would be about a different program")

    data: dict[str, dict[str, list[dict]]] = {a: {} for a in ARMS}
    keysets: dict[str, set] = {}
    binding: dict[str, dict] = {}
    refusals: collections.Counter = collections.Counter()

    for arm in ARMS:
        band = BAND_OF_ARM[arm]
        for k in K_GRID:
            out: list[dict] = []
            skips = collections.Counter()
            n_bound, stops_atr = 0, []
            for r in rows0:
                tf = int(r["timeframe"])
                key = (r["symbol"], tf)
                if key not in index:
                    skips["no_series"] += 1
                    continue
                i = index[key].get(dt.datetime.fromisoformat(r["decision_bar_iso"]))
                if i is None:
                    skips["bar_not_found"] += 1
                    continue
                bars, times = series[key]
                if i + 2 >= len(bars):
                    skips["no_room"] += 1
                    continue
                sd, a, bound = stop_at_k(bars, i, k)
                if sd <= 0:
                    skips["nonpositive_stop"] += 1
                    continue
                n_bound += int(bound)
                stops_atr.append(sd / a)
                td = APF.TARGET_R * sd          # the sleeve's own contract, :112
                ivl = dt.timedelta(minutes=TF_MINUTES[tf])
                entry_utc = times[i] + ivl
                anchor = None
                if band is not None:
                    try:
                        sp = spread_for(r["symbol"], entry_utc, account=ACCOUNT, band=band)
                        anchor = replay_anchor(bars[i].c, int(r["direction"]), sp,
                                               BarQuote.BID)
                    except SpreadUnavailable as e:
                        refusals[f"{arm}|{str(e)[:60]}"] += 1
                        skips["spread_unavailable"] += 1
                        continue
                pol = ExitPolicy(target_dist=td, maxbars=MAXBARS,
                                 label=f"stopfloor_{k:.2f}")
                pr = replay(bars, i, int(r["direction"]), stop_dist=sd, policy=pol,
                            times=times, server=SERVER, bar_minutes=TF_MINUTES[tf],
                            entry_price=anchor)
                xi = pr.exit_index
                out.append({
                    **r,
                    "entry_utc": entry_utc.isoformat(),
                    "exit_utc": (times[xi] + ivl).isoformat(),
                    "entry_price": (bars[i].c if anchor is None else anchor),
                    "sl_distance_price": sd,
                    "target_dist": td,
                    "r_gross": float(winsorize_R(pr.r_gross)),
                    "exit_policy": f"stopfloor_{k:.2f}",
                    "exit_reason": pr.exit_reason,
                    "mfe_r": round(pr.mfe_r, 6), "mae_r": round(pr.mae_r, 6),
                    "bars_to_mfe": int(pr.bars_to_mfe),
                    "exit_bar_offset": int(xi - i),
                    "hold_hours": round((xi - i) * TF_MINUTES[tf] / 60.0, 4),
                    "stop_atr": sd / a, "floor_bound": bound,
                })
            cell = f"{arm}|k={k:.2f}"
            data[arm][f"k={k:.2f}"] = out
            keysets[cell] = {(x["symbol"], x["decision_bar_iso"]) for x in out}
            binding[cell] = {
                "n": len(out), "n_floor_bound": n_bound,
                "frac_floor_bound": round(n_bound / len(out), 5) if out else None,
                "median_stop_atr": round(statistics.median(stops_atr), 5) if stops_atr else None,
                "mean_r_gross": round(statistics.fmean(x["r_gross"] for x in out), 6) if out else None,
                "skips": dict(skips),
            }
            print(f"  {cell:22s} n={len(out):5d} bound={n_bound:5d} "
                  f"medStopATR={binding[cell]['median_stop_atr']} "
                  f"meanRg={binding[cell]['mean_r_gross']}", flush=True)

    # ---- CONTROL C2: the trade SET is invariant in k, within an arm --------------------
    c2 = {}
    for arm in ARMS:
        base = keysets[f"{arm}|k=0.00"]
        same = all(keysets[f"{arm}|k={k:.2f}"] == base for k in K_GRID)
        c2[arm] = {"n_keys": len(base), "identical_at_every_k": same}
    ctl["C2_trade_set_invariance"] = {
        "arms": c2, "pass": all(v["identical_at_every_k"] for v in c2.values()),
        "claim": "a stop floor cannot add or remove a trade — the generator computes sd "
                 "after every entry gate (asia_pdl_fade.py:108) and its only sd-dependent "
                 "refusal is sd <= 0, which a floor can only move away from",
    }

    # ---- CONTROL C3: k=0 on the old walk must reproduce AA's published labelling -------
    pub = {(r["symbol"], r["decision_bar_iso"]): r for r in rows0}
    diffs, worst = 0, 0.0
    for x in data["old"]["k=0.00"]:
        p = pub.get((x["symbol"], x["decision_bar_iso"]))
        if p is None:
            continue
        d = abs(float(p["r_gross"]) - x["r_gross"])
        worst = max(worst, d)
        diffs += int(d > 1e-9)
    ctl["C3_k0_reproduces_published"] = {
        "n_compared": len(data["old"]["k=0.00"]), "n_differing": diffs,
        "max_abs_r_diff": worst, "pass": diffs == 0,
        "claim": "at k=0 on the uncorrected walk this file reproduces AA_ESTATE_TRADES "
                 "r_gross exactly, so every delta below is the floor and nothing else",
    }
    ctl["C4_floor_binding_fraction"] = binding
    ctl["C5_spread_refusals"] = dict(refusals)

    print(f"\nC2 trade-set invariance: {ctl['C2_trade_set_invariance']['pass']}")
    print(f"C3 k=0 reproduces AA: {ctl['C3_k0_reproduces_published']['pass']} "
          f"(n_diff={diffs}, max={worst:.3e})")

    doc = {
        "schema": "gtos.wave20.p3.sweep_substrate.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "generated_utc": dt.datetime.now(dt.UTC).isoformat(),
        "sleeve": SLEEVE, "k_grid": list(K_GRID), "arms": list(ARMS),
        "source_rows": str(AA_IN.relative_to(REPO)), "n_source_rows": len(rows0),
        "bars": AD.BARS, "maxbars": MAXBARS,
        "shipped_expression": "asia_pdl_fade.py:108  sd = (bars[i].c - bars[i].l) + 0.10*a",
        "swept_expression": "sd_k = max((c - l) + 0.10*a, k*a);  target = 3.0*sd_k",
        "controls": ctl, "data": data,
        "seconds": round(time.time() - t0, 1),
    }
    with gzip.open(SUB_OUT, "wt") as fh:
        json.dump(doc, fh)
    CTL_OUT.write_text(json.dumps({k: v for k, v in doc.items() if k != "data"}, indent=1))
    print(f"wrote {SUB_OUT}  ({time.time()-t0:.1f}s)")
    return doc


# =====================================================================================
# the gate
# =====================================================================================

def _row(sv, res, spec, **stamp) -> dict:
    st = sv.gates.get("stability", {}) if sv is not None else {}
    fam = res.family["multiplicity"]
    base = {**stamp, "alpha": spec.alpha, "multiplicity": spec.multiplicity,
            "declared_family_size": spec.declared_family_size,
            "declared_family_id": spec.declared_family_id,
            "effective_family_size": fam["effective_family_size"],
            "spec_sha256": spec.seal(), "spec_id": spec.spec_id}
    if sv is None:
        return {**base, "verdict": "ABSENT"}
    cov = sv.coverage or {}
    diag = sv.diagnostics or {}
    cd = diag.get("cost_decomposition") or {}
    hold = diag.get("holding") or {}
    exc = diag.get("excursion") or {}
    return {**base,
            "verdict": sv.verdict.value, "n_trades": sv.n_trades,
            "pooled_oos_mean_r": sv.pooled_oos_mean_r,
            "p_raw": sv.p_raw, "q_value": sv.q_value,
            "failing_core_gates": [g for g in ("expectancy", "lifetime", "stability",
                                               "robustness", "significance")
                                   if not sv.gates.get(g, {}).get("pass")],
            "fold_means": st.get("fold_means"),
            "oos_positive_fold_frac": st.get("oos_positive_fold_frac"),
            "n_folds_evaluable": sv.gates.get("sample", {}).get("n_folds_evaluable"),
            "drop_best_retention": sv.gates.get("robustness", {}).get("retention"),
            "oos_mean_r_per_trade": sv.gates.get("expectancy", {}).get("oos_mean_r_per_trade"),
            "lifetime_mean_r_per_trade": sv.gates.get("lifetime", {}).get(
                "mean_r_net_per_trade_all_folds"),
            "coverage_frac": cov.get("coverage_frac"),
            "mean_gross_r": cd.get("mean_gross_r"), "mean_cost_r": cd.get("mean_cost_r"),
            "cost_pct_of_abs_gross": cd.get("cost_pct_of_abs_gross"),
            "cost_terms_mean_r": {k: (v or {}).get("mean_r")
                                  for k, v in sorted((cd.get("terms") or {}).items())},
            "median_hold_hours": hold.get("median_hours"),
            "mean_mfe_r": exc.get("mean_mfe_r"), "mean_mae_r": exc.get("mean_mae_r"),
            "capture_ratio_pooled": exc.get("capture_ratio_pooled"),
            "exit_reasons": exc.get("exit_reasons"),
            "reasons": list(sv.reasons)}


def run_arm(rows, costs, allow, fam, *, pop, band, option, spread_charged, **stamp) -> dict:
    t0 = time.time()
    o = OPTIONS[option]
    spec = o.with_(spec_id=f"{o.spec_id}_p3_{stamp['arm']}_{stamp['cell']}"
                          f"{'' if spread_charged else '_nospread'}",
                   sleeve_symbol_allowlist=allow, spread_band=band)
    spec = CF.with_declared_family(spec, "CANDIDATE_BOOK_V1", loaded=fam)
    recs0 = {SLEEVE: AD.to_records(rows)}
    recs, spec, mix = EP.apply(pop, recs0, spec, account=ACCOUNT)
    ctx = contextlib.nullcontext() if spread_charged else spread_term_removed()
    with ctx:
        res = run_gate(recs, spec, costs=costs, server=SERVER)
    return _row(res.verdicts.get(SLEEVE), res, spec, population=pop,
                band=(band if band is not None else "flat_37_day_snapshot"),
                band_is_control=(band is None), option=option,
                spread_charged=spread_charged, population_mix=mix,
                seconds=round(time.time() - t0, 2), **stamp)


def run_gate_stage(sub: dict) -> dict:
    t0 = time.time()
    costs = AD.load_broker_true_costs(AD.COSTS)
    allow = AD.allowlist()
    fam = CF.load_candidate_family(DECL_V27)
    print(f"family V27 CANDIDATE_BOOK_V1 all_declared="
          f"{fam.effective_size('CANDIDATE_BOOK_V1', 'all_declared')}", flush=True)

    arms_out: list[dict] = []
    #: the ratified rule: RECORDED, B_balanced alpha=0.10, the three era bands.
    #: `old|charged` is the published convention and is carried as the A/B base.
    plan = [("old", None, True), ("old", None, False)]
    for b in BANDS:
        plan.append((f"qs_{b}", b, True))
        plan.append((f"qs_{b}", b, False))
    for arm, band, charged in plan:
        for k in K_GRID:
            cell = f"k={k:.2f}"
            rows = sub["data"][arm][cell]
            r = run_arm(rows, costs, allow, fam, pop="RECORDED", band=band,
                        option="B_balanced", spread_charged=charged,
                        arm=arm, cell=cell, k=k)
            arms_out.append(r)
            print(f"  {arm:8s} {cell:9s} spread={'chg' if charged else 'off':3s} "
                  f"-> {r['verdict']:14s} n={r.get('n_trades')} "
                  f"p={r.get('p_raw')} pooled={r.get('pooled_oos_mean_r')}", flush=True)
    return {"arms": arms_out, "seconds": round(time.time() - t0, 1)}


# =====================================================================================

def enumeration_bill(arms: list[dict], *, arm: str, spread_charged: bool) -> dict:
    """AO's convention (`REGIME_CONDITIONING_V1.json -> enumeration_bills`), applied to k."""
    sel = [a for a in arms if a["arm"] == arm and a["spread_charged"] == spread_charged
           and a.get("p_raw") is not None]
    if not sel:
        return {"available": False}
    best = min(sel, key=lambda a: a["p_raw"])
    out = {"n_cells_enumerated": len(sel), "best_cell": best["cell"],
           "best_k": best["k"], "best_p_raw": best["p_raw"],
           "best_verdict": best["verdict"],
           "best_pooled_oos_mean_r": best["pooled_oos_mean_r"]}
    for n, label in ((len(sel), "all_cells"), (len(sel) - 1, "alternatives_only")):
        p = best["p_raw"] * n
        out[f"bonferroni_within_enumeration_{label}"] = p
        out[f"max_declared_family_that_admits_at_alpha_0.10_{label}"] = (
            int(math.floor(0.10 / p)) if p > 0 else None)
    out["declared_family_here"] = best["declared_family_size"]
    out["why"] = ("an enumerated cell is a SEARCH over the pre-declared hypothesis's own "
                  "parameter space, so its own p carries the enumeration as a within-family "
                  "bill. AO's rule, applied verbatim to the k axis.")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="both",
                    choices=("substrate", "gate", "both"))
    args = ap.parse_args()

    sub = None
    if args.stage in ("substrate", "both"):
        sub = build_substrate()
    if args.stage in ("gate", "both"):
        if sub is None:
            sub = json.load(gzip.open(SUB_OUT, "rt"))
        g = run_gate_stage(sub)
        bills = {}
        for arm in ARMS:
            for charged in (True, False):
                bills[f"{arm}|spread={'charged' if charged else 'removed'}"] = \
                    enumeration_bill(g["arms"], arm=arm, spread_charged=charged)
        doc = {
            "schema": "gtos.wave20.p3.sweep_gate.v1",
            "generated_by": str(Path(__file__).relative_to(REPO)),
            "generated_utc": dt.datetime.now(dt.UTC).isoformat(),
            "sleeve": SLEEVE,
            "ratified_rule": {"population": "RECORDED", "option": "B_balanced",
                              "alpha": 0.10, "family": "CANDIDATE_BOOK_V1",
                              "basis": "all_declared",
                              "family_artifact": str(DECL_V27.relative_to(REPO))},
            "k_grid": list(K_GRID),
            "multiplicity": {
                "adds_no_member": True,
                "precedent": ("CANDIDATE_FAMILY_V2.json -> families.CANDIDATE_BOOK_V1"
                              ".history[0].what_it_does_NOT_add names asia_pdl_fade's "
                              "stop x target x time-stop grid as adding no member"),
                "why": ("a stop floor changes no trade's existence — CONTROL C2 measures "
                        "the trade set identical at every k — so it re-measures one "
                        "declared hypothesis rather than testing a new one"),
                "enumeration_bills": bills,
                "prior_enumeration_on_this_sleeve": {
                    "AK_EXIT_FRONTIER_V2_cells": 58,
                    "AO_dial_cells": 13,
                    "note": ("those looks were taken and do not un-take. This sweep's 8 "
                             "cells are additional to them, and the honest cumulative "
                             "enumeration on asia_pdl_fade's contract is 79."),
                },
            },
            "arms": g["arms"],
            "seconds": g["seconds"],
        }
        GATE_OUT.write_text(json.dumps(doc, indent=1))
        print(f"\nwrote {GATE_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
