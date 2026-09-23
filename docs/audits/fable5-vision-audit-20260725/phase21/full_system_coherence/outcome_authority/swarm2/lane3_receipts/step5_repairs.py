#!/usr/bin/env python3
"""LANE 3 step 5: the constructive layer + the adversarial self-checks.

  * cost-gate reversal curve: E[realized net] by cost_r bin, so the 0.20
    ceiling can be moved on evidence rather than on the killed-mean alone
  * the corrected best-pick rate (windows with a STRICTLY positive best only)
  * censor rate of the ranked top, split by order type - the mechanism behind
    G3's worst-case anti-selectivity
  * the abstain counterfactual as a paired per-window quantity against 0
  * the tightened-cost sweep (downward is measurable; upward is not)
  * candidate repair arms, each scored on the same five months
"""
import gzip
import json
import pickle
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import funnel_lib as F

OUT = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/lane3/out")
PRED_KEY = sys.argv[1] if len(sys.argv) > 1 else "pred_month_boundary"
TAG = "daily" if PRED_KEY == "pred_daily" else "monthfit"
RNG = np.random.default_rng(20260812)


def boot_day(vals, days, nboot=2000):
    if not len(vals):
        return None
    by = defaultdict(list)
    for v, d in zip(vals, days):
        by[d].append(v)
    keys = sorted(by)
    arrs = [np.asarray(by[k], dtype=float) for k in keys]
    n = len(keys)
    out = []
    for _ in range(nboot):
        pick = RNG.integers(0, n, n)
        out.append(np.concatenate([arrs[i] for i in pick]).mean())
    o = np.asarray(out)
    return {"point": float(np.mean(vals)), "n": int(len(vals)),
            "ci95_lo": float(np.percentile(o, 2.5)),
            "ci95_hi": float(np.percentile(o, 97.5)),
            "p_two_sided_sign": float(2 * min((o <= 0).mean(), (o >= 0).mean()))}


def main():
    preds = None
    if PRED_KEY == "pred_daily":
        with gzip.open(OUT / "preds_daily.pkl.gz", "rb") as fh:
            preds = pickle.load(fh)

    rep = {"pred_key": PRED_KEY}
    cost_rows = []
    all_windows = []
    tops = []
    sweeps = defaultdict(lambda: defaultdict(float))
    sweep_n = defaultdict(lambda: defaultdict(int))
    arms = defaultdict(lambda: {"actual": 0.0, "wc": 0.0, "n": 0, "days": defaultdict(float)})

    for month in F.MONTHS:
        rows = F.load_month(month)
        if preds is not None:
            for r_ in rows:
                r_["pred_daily"] = preds.get(r_["candidate_occurrence_key"])
        sel, disp, death, windows = F.run_funnel(rows, pred_key=PRED_KEY, diagnose=True)
        for w in windows:
            w["month"] = month
        all_windows.extend(windows)
        for r_ in rows:
            g = death.get(r_["candidate_occurrence_key"], "UNSEEN")
            if r_["predecision_geometry_valid"]:
                try:
                    c = float(r_["cost_r"])
                except (TypeError, ValueError):
                    c = None
                if c is not None and np.isfinite(c) and r_["resolved"]:
                    cost_rows.append((c, F.net_actual(r_), r_["trading_day"],
                                      r_["proposed_order_type"]))
            if g not in ("G0_geometry_invalid", "G1_cost_gt_0p20",
                         "G2_symbol_occupied", "G3_lost_rank"):
                tops.append({"gate": g, "resolved": r_["resolved"], "state": r_["state"],
                             "ot": r_["proposed_order_type"], "fam": r_["origin_family"]})

        # tightened cost ceiling (downward only - see funnel_lib note)
        for mc in (0.05, 0.08, 0.10, 0.12, 0.15, 0.18, 0.20):
            s, _d, _dd = F.run_funnel(rows, pred_key=PRED_KEY, max_cost=mc)
            p = F.portfolio(s)
            sweeps["max_cost"][mc] += p["actual_net_r"]
            sweeps["max_cost_wc"][mc] += p["worst_case_net_r"]
            sweep_n["max_cost"][mc] += p["selected"]

        # ---- repair arms, all scored on the same windows ------------------
        def bank(name, value, day, wc=None):
            arms[name]["actual"] += value
            arms[name]["wc"] += (value if wc is None else wc)
            arms[name]["n"] += 1
            arms[name]["days"][day] += value

        for w in windows:
            day = w["trading_day"]
            traded = w["outcome_gate"] == "TRADED"
            abst = w["outcome_gate"] == "G5_market_top_abstain"
            if traded:
                bank("A0_shipped", w["pick_actual"] or 0.0, day, w["pick_wc"])
            if traded or abst:
                # R1: drop the abstain clause entirely (mixed at the top slot only,
                # occupancy held at the shipped path - an upper bound on its cost)
                bank("R1_no_abstain_top_slot", w["pick_actual"] or 0.0, day, w["pick_wc"])
                # R2: substitute the best MARKET candidate instead of abstaining
                v = w["market_argmax_actual"] if abst else w["pick_actual"]
                vw = w["market_argmax_wc"] if abst else w["pick_wc"]
                if v is not None:
                    bank("R2_market_substitute", v, day, vw)
                # R3: rank by cost ascending inside the decided windows
                if w["mincost_actual"] is not None:
                    bank("R3_cheapest_in_window", w["mincost_actual"], day, w["mincost_wc"])
                # R4: take rank 2 instead of rank 1
                if w["rank2_actual"] is not None:
                    bank("R4_rank2", w["rank2_actual"], day, w["rank2_wc"])
                # R5: oracle ceiling on the decided windows
                if w["oracle_max_actual"] is not None:
                    bank("R5_oracle_ceiling", w["oracle_max_actual"], day, w["oracle_max_wc"])
        print(json.dumps({"month": month, "windows": len(windows)}), flush=True)

    # ---------------- cost-gate reversal curve --------------------------
    cost_rows.sort(key=lambda t: t[0])
    cs = np.asarray([c for c, _n, _d, _o in cost_rows])
    ns = np.asarray([n for _c, n, _d, _o in cost_rows])
    ds = [d for _c, _n, d, _o in cost_rows]
    ots = [o for _c, _n, _d, o in cost_rows]
    bins = [0.0, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18, 0.20,
            0.25, 0.30, 0.40, 0.60, 1.00, 1e9]
    curve = []
    for lo, hi in zip(bins, bins[1:]):
        m = (cs >= lo) & (cs < hi)
        if not m.any():
            continue
        sub = ns[m]
        subd = [d for d, k in zip(ds, m) if k]
        row = {"cost_lo": lo, "cost_hi": hi, "n": int(m.sum()),
               "mean_net_r": float(sub.mean()), "sum_net_r": float(sub.sum()),
               "boot": boot_day(sub, subd, 600)}
        for ot in ("MARKET", "LIMIT"):
            mm = m & np.asarray([o == ot for o in ots])
            row[ot] = {"n": int(mm.sum()),
                       "mean_net_r": float(ns[mm].mean()) if mm.any() else None}
        curve.append(row)
    rep["cost_gate_reversal_curve"] = curve
    rep["cost_gate_note"] = (
        "Loosening above 0.20 cannot be scored from the cache: rows above the "
        "shipped ceiling were never in r.eligible and carry no prediction. The "
        "curve is the population-level reversal measurement - if E[net] is flat "
        "through and beyond 0.20 the ceiling is arbitrary; if it falls, it is not."
    )

    # ---------------- corrected best-pick rate ---------------------------
    strict = [w for w in all_windows if w["oracle_max_actual"] is not None
              and w["oracle_max_actual"] > 0]
    rep["best_pick_rate_strict"] = {
        "windows_with_strictly_positive_best": len(strict),
        "ranker_picks_the_best": float(np.mean([1.0 if w["pick_is_window_best"] else 0.0
                                                for w in strict])) if strict else None,
        "random_would": float(np.mean([1.0 / w["n_available"] for w in strict])) if strict else None,
        "note": ("the headline 0.1117 counts ties at 0.0 R (NO_FILL); this row "
                 "restricts to windows where the best available candidate is "
                 "strictly positive, so 'best' is unique-ish and unambiguous"),
    }
    n_pos = [w["n_positive_available"] for w in strict]
    rep["best_pick_rate_strict"]["mean_positive_candidates_per_window"] = (
        float(np.mean(n_pos)) if n_pos else None)
    rep["best_pick_rate_strict"]["expected_hit_if_uniform_over_positives"] = (
        float(np.mean([p / w["n_available"] for p, w in zip(n_pos, strict)])) if strict else None)

    # ---------------- censoring at the ranked top, by order type ----------
    byot = defaultdict(Counter)
    for t in tops:
        byot[t["ot"]]["n"] += 1
        byot[t["ot"]]["censored"] += 0 if t["resolved"] else 1
        byot[t["ot"]]["no_fill"] += 1 if t["state"] == "NO_FILL" else 0
    rep["ranked_top_censoring_by_order_type"] = {
        ot: {"n": c["n"], "censored": c["censored"],
             "censor_rate": c["censored"] / c["n"] if c["n"] else None,
             "no_fill_rate": c["no_fill"] / c["n"] if c["n"] else None}
        for ot, c in sorted(byot.items())
    }

    # ---------------- abstain counterfactual, paired against 0 -------------
    ab = [w for w in all_windows if w["outcome_gate"] == "G5_market_top_abstain"]
    vals = [w["pick_actual"] for w in ab if w["pick_actual"] is not None]
    days = [w["trading_day"] for w in ab if w["pick_actual"] is not None]
    rep["abstain_counterfactual"] = {
        "windows_abstained": len(ab),
        "limit_top_realized_actual": boot_day(vals, days, 4000),
        "limit_top_total_actual_r": float(np.sum(vals)),
        "limit_top_states": dict(sorted(Counter(w["top_family"] for w in ab).items())),
        "market_substitute_total_actual_r": float(
            np.sum([w["market_argmax_actual"] for w in ab if w["market_argmax_actual"] is not None])),
        "market_substitute_mean": boot_day(
            [w["market_argmax_actual"] for w in ab if w["market_argmax_actual"] is not None],
            [w["trading_day"] for w in ab if w["market_argmax_actual"] is not None], 2000),
        "note": ("abstaining books exactly 0 R per window, so the counterfactual "
                 "mean IS the value of the rule with the sign flipped"),
    }

    # ---------------- repair arms -----------------------------------------
    out_arms = {}
    for name, a in sorted(arms.items()):
        dv = list(a["days"].values())
        out_arms[name] = {
            "n_decisions": a["n"], "actual_net_r": round(a["actual"], 4),
            "worst_case_net_r": round(a["wc"], 4),
            "mean_per_decision": a["actual"] / a["n"] if a["n"] else None,
            "positive_days": sum(1 for v in dv if v > 0),
            "negative_days": sum(1 for v in dv if v < 0),
        }
    base = out_arms.get("A0_shipped", {}).get("actual_net_r", 0.0)
    for name, v in out_arms.items():
        v["delta_vs_shipped_actual_r"] = round(v["actual_net_r"] - base, 4)
    rep["repair_arms"] = out_arms
    rep["repair_arms_note"] = (
        "arms are scored on the DECIDED windows (traded + abstained) with the "
        "shipped occupancy path held fixed, so each is a same-window swap and "
        "not a full re-simulation; occupancy knock-on is not modelled"
    )

    rep["sweeps_cost_tightened"] = {
        str(k): {"actual": round(sweeps["max_cost"][k], 4),
                 "wc": round(sweeps["max_cost_wc"][k], 4),
                 "n": sweep_n["max_cost"][k]}
        for k in sorted(sweeps["max_cost"])
    }

    (OUT / f"repairs_{TAG}.json").write_text(json.dumps(rep, indent=1, sort_keys=True, default=float))
    print("WROTE", OUT / f"repairs_{TAG}.json")


if __name__ == "__main__":
    main()
