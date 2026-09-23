"""Candidate-book dossiers for Session AI, at every look deflated.

    python3 docs/audits/fable5-vision-audit-20260725/phase8/receipts/ak_candidate_dossier.py

WHAT AI ASKED FOR, AND WHAT MAKES THIS CHEAPER THAN RE-DERIVING IT
------------------------------------------------------------------
Two members are candidate-book material blocked on sample and multiplicity rather than on
economics, and AI's composition question is cheaper the cleaner their dossier is:

  `mx_jp225_cash_d1_volume_surge_reversal`  AF's second-strongest single member: +0.2071 R/day at
                                           mid band, raw p 0.1126, 80 % of folds positive,
                                           band-stable (AF §5.2)
  `vol_compression`                        AD's `time_stop_20`: +0.445 R/day, from +0.269
                                           as-walked (AD §6.1)

Also carried, because this session produced them and they are the same shape:
`ny_index_momentum` and the one `session_leadlag_genuine` leg that fails significance alone.

THE DEFLATION IS THE POINT
--------------------------
Every one of these fails on `significance`, and `significance` is a function of
`declared_family_size`, which has no principled stopping rule. So a dossier that quotes one
q-value is quoting a choice. Each row therefore carries:

  * `q` at AA's 69, at AF's 276, at the trial ledger's MEASURED look count, and at the sleeve
    alone (family size 1) — the four readings between which the owner decision sits;
  * the BH threshold each family size implies, so a reader can see how far the raw p is from
    admission rather than only that it is;
  * the DSR sweep the gate already computes, at the ledger's measured `n_trials`;
  * the per-fold OOS series, which is what AI needs to know whether two candidates' good folds
    are the same folds.

Nothing here re-runs generation. Every number is a re-gate of stored intents at one named cell.
"""

from __future__ import annotations

import gzip
import json
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"))

import ad_exit_sweep as AD  # noqa: E402
from src.costs import load_broker_true_costs  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
    measured_n_trials,
)
from src.research_infra.walkforward import run_gate  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402
from src.research_infra.walkforward.stats import benjamini_hochberg, bonferroni  # noqa: E402

AA_IN = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_TRADES.json.gz"
AK_IN = HERE / "AK_SUPPLY_TRADES.json.gz"
CELLS_IN = HERE / "AK_SLEEVE_CELLS_V1.json"
OUT = HERE / "AK_CANDIDATE_DOSSIER_V1.json"
SERVER = AD.SERVER

#: (sleeve, cell, why this cell). Declared before the run.
DOSSIER = [
    ("mx_jp225_cash_d1_volume_surge_reversal", None,
     "AF §5.2's second-strongest single member. Cell taken as the argmax of AD's own frontier "
     "for this sleeve, so the dossier quotes the best measured configuration rather than "
     "as-walked."),
    ("vol_compression", "time_stop_20",
     "AD §6.1: +0.445 R/day against +0.269 as-walked. Named explicitly rather than argmaxed, "
     "because AI's prompt names it."),
    ("ny_index_momentum", None,
     "AK: REJECT on significance ALONE at +0.0758 R/day, the cleanest of the four sleeves no "
     "registry can reach. Cell taken as the argmax of this session's frontier."),
    ("fam_session_leadlag_us30_cash_usdjpy_t2.0", None,
     "AK: the one leg of session_leadlag_genuine that fails significance alone (+0.2774 R/day, "
     "p 0.113 on n=161). Its parent pools four legs and dilutes it."),
]

FAMILY_SIZES = {"sleeve_alone": 1, "AA_69": 69, "AF_276": 276}


#: The per-fold OOS mean, under whichever name the diagnostics head emits. Ordered by preference;
#: `test_mean_r` is what `diagnostics.py:592` writes today.
_FOLD_KEYS = ("test_mean_r", "oos_mean_r", "oos_mean", "mean_r")


def _fold_series_key(folds) -> str | None:
    for k in _FOLD_KEYS:
        if any(isinstance(f, dict) and f.get(k) is not None for f in (folds or ())):
            return k
    return None


def _fold_series(folds):
    k = _fold_series_key(folds)
    if k is None:
        return None
    return [f.get(k) for f in folds]


def frontier_cells(sleeve: str) -> dict:
    out: dict = {}
    for p in (REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts/EXIT_FRONTIER_V1.json",
              REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts/EXIT_FRONTIER_V1_TRAIL.json",
              HERE / "AK_EXIT_FRONTIER_V2.json"):
        if not p.is_file():
            continue
        d = json.loads(p.read_text())
        sl = (d.get("sleeves") or {}).get(sleeve)
        if isinstance(sl, dict) and sl.get("cells"):
            out.update(sl["cells"])
    if CELLS_IN.is_file():
        c = json.loads(CELLS_IN.read_text())
        ef = ((c.get("cells") or {}).get(sleeve) or {}).get("exit_frontier") or {}
        if ef.get("cells"):
            out.update(ef["cells"])
    return out


def deflation(p_raw: float | None, alpha: float, sizes: dict[str, int]) -> dict:
    """What each family size does to one raw p, both corrections, with the threshold shown."""
    if p_raw is None:
        return {"p_raw": None}
    out: dict = {"p_raw": p_raw, "alpha": alpha, "by_family_size": {}}
    for label, n in sizes.items():
        padded = [p_raw] + [1.0] * max(0, n - 1)
        bh = benjamini_hochberg(padded, alpha)
        bf = bonferroni(padded, alpha)
        # Rank-1 BH threshold for a single tested hypothesis against n: alpha * 1 / n.
        out["by_family_size"][label] = {
            "n": n,
            "bh_q": bh["qvalues"][0], "bh_admits": bool(bh["rejected"][0]),
            "bh_threshold_at_rank1": round(alpha / n, 8),
            "bonferroni_q": bf["qvalues"][0], "bonferroni_admits": bool(bf["rejected"][0]),
            "bonferroni_threshold": round(alpha / n, 8),
        }
    ok = [n for lbl, n in sorted(sizes.items(), key=lambda kv: kv[1])
          if out["by_family_size"][lbl]["bh_admits"]]
    out["largest_family_that_admits_under_bh"] = max(ok) if ok else None
    out["note"] = ("BH at rank 1 against a family of n admits iff p <= alpha/n, so the largest "
                   "admitting family is floor(alpha/p). Published because 'q = 1.0' hides how "
                   "far from admission a sleeve actually is.")
    if p_raw > 0:
        out["largest_family_that_would_admit"] = int(alpha / p_raw)
    return out


def main() -> dict:
    t_start = time.time()
    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AK")
    aa = json.load(gzip.open(AA_IN, "rt"))
    ak = json.load(gzip.open(AK_IN, "rt"))
    costs = load_broker_true_costs(AD.COSTS)
    units = json.loads(AD.UNITS.read_text())

    rows_all: dict[str, list[dict]] = {s: list(v) for s, v in aa["trades"].items()}
    for tag, v in ak["trades"].items():
        rows_all[tag] = list(v)
    if CELLS_IN.is_file():
        cdoc = json.loads(CELLS_IN.read_text())
        # The cells' fidelity records live in a process-local table that
        # `ak_supply_cells.py` clears on exit, so they have to be re-registered here or every
        # `fam_*` row returns NOT_EVALUABLE for a reason that has nothing to do with the sleeve.
        # Found by reading this script's own first output — the row came back `pooled=None`.
        from src.research_infra.walkforward.fidelity import (
            clear_surface_expansions,
            register_surface_expansion,
        )
        clear_surface_expansions()
        for name, c in (cdoc.get("cells") or {}).items():
            register_surface_expansion(
                name, parent=c["parent"],
                symbol=",".join(c.get("priceable_surface") or ()) or "(none priceable)",
                timeframe="M15",
                surface_note=("re-registered from AK_SLEEVE_CELLS_V1.json; the authoritative "
                              "stamp and its restriction are recorded there"))
        for name, c in (cdoc.get("cells") or {}).items():
            # the cell populations, rebuilt from the parent's rows on the cell's own surface
            surf = set(c.get("priceable_surface") or ())
            parent = c.get("parent")
            leg = (c.get("cell") or {})
            src = rows_all.get(parent) or []
            if c.get("kind") == "declared_leg":
                tag = f"{leg.get('leader')}->{leg.get('follower')}@{leg.get('geom')}"
                sel = [r for r in src if r.get("ll_impulse") == tag]
            else:
                sel = [r for r in src if r.get("symbol_canonical") in surf]
            rows_all[name] = [{**r, "sleeve": name} for r in sel
                              if r.get("symbol_canonical") in surf or not surf]

    tf_of = {s: {"M15": AD.TF_M15, "H4": AD.TF_H4, "D1": AD.TF_D1}[v]
             for s, v in aa["timeframe_by_sleeve"].items()}
    for tag, meta in ak["specs"].items():
        tf_of[tag] = {"M15": AD.TF_M15, "H4": AD.TF_H4, "D1": AD.TF_D1}[meta["timeframe"]]
    for name in list(rows_all):
        tf_of.setdefault(name, AD.TF_M15)

    n_meas = measured_n_trials(ledger_paths=[REPO / DEFAULT_TRIAL_LEDGER])
    sizes = {**FAMILY_SIZES, "trial_ledger_measured": int(n_meas["n_trials"])}
    print(f"family sizes: {sizes}  (ledger basis: {n_meas.get('basis')})")

    spec_base = OPTIONS["B_balanced"]
    series = index = rule = None
    out: dict = {
        "schema": "gtos.walkforward.candidate_dossier.v1",
        "generated_by": ("docs/audits/fable5-vision-audit-20260725/phase8/receipts/"
                         "ak_candidate_dossier.py"),
        "session": "AK", "blocks": "B950-B999",
        "for": "Session AI — candidate-book composition",
        "family_sizes": sizes,
        "trial_ledger": n_meas,
        "cost_artifact": str(AD.COSTS.relative_to(REPO)),
        "candidates": {},
    }

    for sleeve, want_cell, why in DOSSIER:
        src = rows_all.get(sleeve) or []
        if not src:
            out["candidates"][sleeve] = {"available": False, "reason": "no stored trades",
                                        "why_selected": why}
            print(f"{sleeve}: no trades, skipped")
            continue
        cells = frontier_cells(sleeve)
        ok = {k: c for k, c in cells.items()
              if isinstance(c, dict) and c.get("pooled_oos_mean_r") is not None}
        cell = want_cell or (max(ok, key=lambda k: ok[k]["pooled_oos_mean_r"]) if ok else
                             "as_walked")
        if want_cell and want_cell not in ok:
            print(f"  NOTE {sleeve}: named cell {want_cell!r} is not gated on any frontier; "
                  f"re-gating it here from the plan")
        if series is None:
            print("=== loading bars ===", flush=True)
            t0 = time.time()
            series, index, _r = AD.load_bars()
            rule = AD.resolve_rule(SERVER)
            print(f"  {len(series)} series in {time.time()-t0:.0f}s", flush=True)

        tf = tf_of[sleeve]
        plan = {v.name: v for v in AD.plan_for(sleeve if sleeve in tf_of else sleeve, tf, units)}
        if cell == "as_walked":
            v = AD.AS_WALKED
        elif cell in plan:
            v = plan[cell]
        else:
            d = dict((cells.get(cell) or {}).get("variant") or {})
            d.pop("name", None); d.pop("family", None)
            note = d.pop("note", "")
            v = AD.Variant(name=cell, family="rebuilt_from_artifact", note=note, **d)
        new_rows, tel = AD.resimulate(src, v, series, index, costs, spec_base.account, rule)

        rows_for_gate = {s: AD.to_records(r if s != sleeve else new_rows)
                         for s, r in rows_all.items()}
        spec = spec_base.with_(spec_id=f"B_balanced_ak_dossier_{sleeve[:24]}",
                               declared_family_size=AD.DECLARED_FAMILY)
        res = run_gate(rows_for_gate, spec, costs=costs, diagnose=True, server=SERVER)
        sv = res.verdicts[sleeve]
        d = sv.diagnostics or {}
        folds = d.get("by_fold") or []
        row = {
            "available": True, "why_selected": why,
            "cell": cell, "variant": v.as_dict(), "n_resimulated": len(new_rows),
            "verdict": sv.verdict.value,
            "pooled_oos_mean_r": sv.pooled_oos_mean_r,
            "p_raw": sv.p_raw,
            "q_at_declared_69": sv.q_value,
            "failing_gates": [g for g in ("expectancy", "lifetime", "stability", "robustness",
                                          "significance")
                              if not sv.gates.get(g, {}).get("pass")],
            "gates": {g: bool(x.get("pass")) for g, x in sorted(sv.gates.items())},
            "oos_positive_fold_frac": sv.gates.get("stability", {}).get(
                "oos_positive_fold_frac"),
            "drop_best_retention": sv.gates.get("robustness", {}).get("retention"),
            "coverage_frac": sv.gates.get("cost_coverage", {}).get("coverage_frac"),
            "n_folds_evaluable": sv.gates.get("sample", {}).get("n_folds_evaluable"),
            "by_fold": folds,
            # `diagnostics.py:592` emits `test_mean_r`; the first version of this line read
            # `oos_mean_r` and produced [None, None, ...] on every row, which then emptied the
            # pairwise agreement table below. The deliverable AI is told to read was blank.
            # Found by a completeness pass. `_fold_series` also falls back across the plausible
            # key names so a rename upstream degrades loudly rather than to nulls.
            "fold_oos_mean_r_series": _fold_series(folds),
            "fold_series_key_used": _fold_series_key(folds),
            "by_symbol": d.get("by_symbol"),
            "by_side": d.get("by_side"),
            "cost_decomposition": d.get("cost_decomposition"),
            "holds": d.get("holds"),
            "excursion": d.get("excursion"),
            "regime_inflation": (sv.telemetry or {}).get("regime_inflation"),
            "dsr": (sv.telemetry or {}).get("dsr"),
            "deflation": deflation(sv.p_raw, spec.alpha, sizes),
            "fidelity": sv.fidelity,
            "primary_prescription": d.get("primary_prescription"),
        }
        out["candidates"][sleeve] = row
        dfl = row["deflation"]
        print(f"{sleeve[:44]:44s} cell={cell:22s} pooled={row['pooled_oos_mean_r']} "
              f"p={row['p_raw']} folds+={row['oos_positive_fold_frac']} "
              f"admits_up_to_family={dfl.get('largest_family_that_would_admit')} "
              f"failing={row['failing_gates']}", flush=True)
        ledger.record(
            mechanism="candidate_dossier", sleeve=sleeve,
            variant={"cell": cell, "for": "AI candidate book"},
            window="full_archive", spec_sha256=spec.seal(),
            outcome={"ADMIT": "admitted", "REJECT": "rejected",
                     "NOT_EVALUABLE": "not_evaluable"}.get(sv.verdict.value, "evaluated"),
            metric=sv.pooled_oos_mean_r, metric_name="pooled_oos_mean_r",
            note=f"AK dossier for AI at cell {cell}")

    # Do the good folds coincide? That is the one thing AI cannot read off separate dossiers.
    fseries = {s: r["fold_oos_mean_r_series"] for s, r in out["candidates"].items()
               if r.get("fold_oos_mean_r_series")}
    pairs = {}
    names = sorted(fseries)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            xa, xb = fseries[a], fseries[b]
            n = min(len(xa), len(xb))
            va = [x for x in xa[:n] if x is not None]
            vb = [x for x in xb[:n] if x is not None]
            if len(va) != len(vb) or len(va) < 3:
                continue
            ma, mb = statistics.fmean(va), statistics.fmean(vb)
            sa = statistics.pstdev(va) or 1e-12
            sb = statistics.pstdev(vb) or 1e-12
            cov = statistics.fmean([(x - ma) * (y - mb) for x, y in zip(va, vb)])
            pairs[f"{a} | {b}"] = {
                "n_folds": len(va), "corr_of_fold_means": round(cov / (sa * sb), 4),
                "both_positive_in": sum(1 for x, y in zip(va, vb) if x > 0 and y > 0),
                "same_sign_in": sum(1 for x, y in zip(va, vb) if (x > 0) == (y > 0)),
            }
    out["fold_series_agreement"] = {
        "what": ("correlation of the per-fold OOS means between every pair of candidates. Two "
                 "candidates whose good folds are the SAME folds do not diversify each other, "
                 "however uncorrelated their daily series look."),
        "caveat": ("the fold calendars are per sleeve — GateSpec.fold_rule is "
                   "'equal_calendar_folds_over_sleeve_span', so fold k of one sleeve is not the "
                   "same dates as fold k of another. Read this as a shape hint, not a "
                   "correlation, and use the daily series for anything load-bearing."),
        "pairs": pairs,
    }
    out["seconds_total"] = round(time.time() - t_start, 1)
    OUT.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nwrote {OUT.relative_to(REPO)} in {time.time()-t_start:.0f}s")
    print(f"ledger: {ledger.n_written} rows written, {ledger.write_errors} errors")
    return out


if __name__ == "__main__":
    main()
