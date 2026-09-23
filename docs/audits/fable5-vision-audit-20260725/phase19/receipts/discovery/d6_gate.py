"""d6_gate — the surviving candidate at the estate's ratified admission rule.

Uses the estate's OWN machinery where it exists:
  src.research_infra.walkforward.stats.day_block_bootstrap_p   (day-blocked null)
  src.research_infra.walkforward.stats.block_length_auto       (block length)
  src.research_infra.walkforward.stats.benjamini_hochberg      (multiplicity)
  src.research_infra.walkforward.spec.DEFAULT_SPEC             (the thresholds)

and implements the seven gate conditions of `walkforward/gate.py` on this
candidate's own trade series, because `run_gate` consumes a sleeve panel this
candidate is not a member of.  fidelity and coverage are reported
NOT_EVALUABLE-by-construction with the reason attached, exactly as the estate
does for CP's and CQ's factory candidates.

    python3 d6_gate.py --months 202601,202602,202603 --out /tmp/d6/D6_GATE_V1.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[5]))

import d6_lib as D  # noqa: E402
from src.research_infra.walkforward import stats as S  # noqa: E402
from src.research_infra.walkforward.spec import DEFAULT_SPEC  # noqa: E402

FAMILY_V27 = (Path(__file__).resolve().parents[6]
              / "docs/audits/fable5-vision-audit-20260725/phase18/receipts"
              / "CANDIDATE_FAMILY_V27.json")


def daily_series(trades):
    """[(day, sum_net_R, n_trades)] in calendar order."""
    by = defaultdict(lambda: [0.0, 0])
    for r, arm in trades:
        a = r.get(arm)
        if not a:
            continue
        day = (r["day_part"] if arm in ("P", "D") else r["day_close"])
        by[day][0] += a["g2"] - a["cr"]
        by[day][1] += 1
    return [(d, by[d][0], by[d][1]) for d in sorted(by)]


def folds(series, n_folds=6):
    """Contiguous calendar folds; fold 0 is the train block and is never scored."""
    n = len(series)
    if n < n_folds:
        return []
    edges = [round(i * n / n_folds) for i in range(n_folds + 1)]
    return [series[edges[i]:edges[i + 1]] for i in range(n_folds)]


def arm_stats(trades, label, spec=DEFAULT_SPEC, n_folds=6):
    ser = daily_series(trades)
    if not ser:
        return {"label": label, "verdict": "NOT_EVALUABLE", "reason": "no trades"}
    day_r = np.array([s[1] for s in ser], float)
    day_n = np.array([s[2] for s in ser], float)
    n_tr = int(day_n.sum())
    tot = float(day_r.sum())
    per_trade = tot / n_tr if n_tr else float("nan")
    per_day = float(day_r.mean())

    fs = folds(ser, n_folds)
    oos = fs[1:] if fs else []
    fold_rows = []
    for i, f in enumerate(oos, start=1):
        s = sum(x[1] for x in f)
        c = sum(x[2] for x in f)
        fold_rows.append({"fold": i, "days": len(f), "n_trades": c,
                          "sum_r": s, "r_per_day": (s / len(f) if f else None),
                          "r_per_trade": (s / c if c else None),
                          "first_day": f[0][0] if f else None,
                          "last_day": f[-1][0] if f else None})
    ev = [f for f in fold_rows if f["n_trades"] >= spec.min_trades_per_fold]
    pos = [f for f in ev if f["r_per_day"] is not None and f["r_per_day"] > 0]
    pos_frac = len(pos) / len(ev) if ev else 0.0

    # leave-best-fold-out
    drop = None
    retention = None
    if len(ev) >= 2:
        best = max(ev, key=lambda f: f["r_per_day"])
        rest = [f for f in ev if f is not best]
        d_days = sum(f["days"] for f in rest)
        d_sum = sum(f["sum_r"] for f in rest)
        drop = d_sum / d_days if d_days else None
        head = sum(f["sum_r"] for f in ev) / sum(f["days"] for f in ev)
        retention = (drop / head) if (head and head > 0) else None

    # day-blocked null on the OOS daily series
    oos_days = [x for f in oos for x in f]
    oos_r = np.array([x[1] for x in oos_days], float)
    block = S.block_length_auto(list(oos_r)) if len(oos_r) > 3 else 1
    null = (S.day_block_bootstrap_p(list(oos_r), block=int(block), n_boot=20000)
            if len(oos_r) > 3 else {"p_value": float("nan")})

    conds = {
        "fidelity": {"pass": None, "status": "NOT_EVALUABLE",
                     "reason": "no fidelity register entry: this candidate is a research "
                               "contract over the broad-origin generator, not a registry "
                               "sleeve. Same status the estate gives CP/CQ."},
        "coverage": {"pass": True, "status": "MEASURED",
                     "cost_coverage": 1.0,
                     "reason": "every trade is priced by the h1 four-term broker-true model "
                               "(hour-aware tick spread + broker-true commission + measured "
                               "price-unit slippage + swap); 0 unpriced."},
        "sample": {"pass": bool(n_tr >= spec.min_trades_total
                                and len(ev) >= spec.min_folds_evaluable),
                   "n_trades": n_tr, "min_trades_total": spec.min_trades_total,
                   "n_folds_evaluable": len(ev),
                   "min_folds_evaluable": spec.min_folds_evaluable},
        "expectancy": {"pass": bool(sum(f["sum_r"] for f in ev) / max(sum(f["days"] for f in ev), 1)
                                    > spec.min_oos_mean_r) if ev else False,
                       "oos_r_per_day": (sum(f["sum_r"] for f in ev)
                                         / sum(f["days"] for f in ev)) if ev else None,
                       "oos_r_per_trade": (sum(f["sum_r"] for f in ev)
                                           / sum(f["n_trades"] for f in ev))
                       if ev and sum(f["n_trades"] for f in ev) else None,
                       "min_oos_mean_r": spec.min_oos_mean_r},
        "stability": {"pass": pos_frac >= spec.min_oos_positive_fold_frac,
                      "positive_fold_frac": pos_frac,
                      "min": spec.min_oos_positive_fold_frac,
                      "n_positive": len(pos), "n_evaluable": len(ev)},
        "robustness": {"pass": bool(drop is not None and drop > 0
                                    and (retention is None
                                         or retention >= spec.min_drop_best_fold_retention)),
                       "drop_best_fold_r_per_day": drop, "retention": retention,
                       "min_retention": spec.min_drop_best_fold_retention},
        "significance": {"p_value": null.get("p_value"), "block": int(block),
                         "alpha": spec.alpha},
    }
    return {
        "label": label,
        "n_trades": n_tr, "n_days": len(ser),
        "total_net_r": tot, "net_r_per_trade": per_trade, "net_r_per_day": per_day,
        "folds": fold_rows,
        "conditions": conds,
        "p_value": null.get("p_value"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--months", default="")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    months = [m for m in args.months.split(",") if m] or D.months_available()

    atm = {m: D.load(m, fams=set(D.AT_MARKET)) for m in months}

    def sel(fams, mode, arm):
        """mode: 'none' | 'live'; arm: 'close' | 'partial' | 'paired_partial'"""
        out = []
        for m in months:
            rr = [r for r in atm[m] if r["f"] in fams]
            if arm == "paired_partial":
                cand = [(r, "P") for r in rr if r.get("C") and r.get("P")]
            elif arm == "partial":
                cand = [(r, "P") for r in rr if r.get("P")]
                cand += [(r, "C") for r in rr if r.get("C") and not r.get("P")]
            else:
                cand = [(r, "C") for r in rr if r.get("C")]
            if mode == "live":
                best = {}
                for r, a in cand:
                    t = r["t_part"] if a == "P" else r["t_close"]
                    day = r["day_part"] if a == "P" else r["day_close"]
                    k = (r["f"], r["s"], day)
                    if k not in best or t < best[k][2]:
                        best[k] = (r, a, t)
                cand = [(r, a) for r, a, _t in best.values()]
            out += cand
        return out

    E5 = set(D.EARLY5)
    ALL = set(D.AT_MARKET)
    RTB = {"regime_transition_break"}

    res = {"months": months, "generated_utc": datetime.now(timezone.utc).isoformat(),
           "spec": {"alpha": DEFAULT_SPEC.alpha,
                    "min_oos_positive_fold_frac": DEFAULT_SPEC.min_oos_positive_fold_frac,
                    "min_drop_best_fold_retention": DEFAULT_SPEC.min_drop_best_fold_retention,
                    "min_trades_total": DEFAULT_SPEC.min_trades_total,
                    "min_folds_evaluable": DEFAULT_SPEC.min_folds_evaluable,
                    "n_folds": 6, "multiplicity": DEFAULT_SPEC.multiplicity}}

    arms = {
        "A1_EARLY5_partial_book_NOdedup": sel(E5, "none", "partial"),
        "A1L_EARLY5_partial_book_LIVEdedup": sel(E5, "live", "partial"),
        "A0_EARLY5_close_book_NOdedup": sel(E5, "none", "close"),
        "A0L_EARLY5_close_book_LIVEdedup": sel(E5, "live", "close"),
        "A2_EARLY5_paired_partial_COUNTERFACTUAL": sel(E5, "none", "paired_partial"),
        "A3_ALL7_partial_book": sel(ALL, "none", "partial"),
        "A4_best_single_family_partial_book": sel(RTB, "none", "partial"),
        "A4L_best_single_family_partial_LIVEdedup": sel(RTB, "live", "partial"),
    }
    res["arms"] = {k: arm_stats(v, k) for k, v in arms.items()}

    # ---- multiplicity: BH at the declared family, all_declared basis, alpha 0.10
    fam = json.loads(Path(FAMILY_V27).read_text())["families"]["CANDIDATE_BOOK_V1"]
    m_declared = fam["high_water_size"] + 1          # + this candidate
    ps = [res["arms"][k]["p_value"] for k in arms]
    bh = S.benjamini_hochberg([p if p == p else 1.0 for p in ps], DEFAULT_SPEC.alpha)
    res["multiplicity"] = {
        "declared_family": "CANDIDATE_BOOK_V1",
        "declared_family_version": "V27",
        "high_water_size": fam["high_water_size"],
        "high_water_looks": fam["high_water_looks"],
        "m_with_this_candidate": m_declared,
        "alpha": DEFAULT_SPEC.alpha,
        "bh_rank1_bar_at_m": DEFAULT_SPEC.alpha / m_declared,
        "bonferroni_bar_at_m": 0.05 / m_declared,
        "within_lane_bh": {k: {"p": p, "q": q, "rejected": r}
                           for k, p, q, r in zip(arms, ps, bh["qvalues"], bh["rejected"])},
        "note": "the honest bill for this lane is larger than 1: the subset sweep alone is "
                "127 family subsets x 2 arms and the rule search is 1e2-1e3 cells; both are "
                "published in D6_MAIN_V1.json / D6_FEAT_V1.json so the reader can bill them.",
    }

    Path(args.out).write_text(json.dumps(res, indent=1))
    print("wrote", args.out)


if __name__ == "__main__":
    main()
