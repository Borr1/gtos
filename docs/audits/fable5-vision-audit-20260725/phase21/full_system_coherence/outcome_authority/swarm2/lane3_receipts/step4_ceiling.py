#!/usr/bin/env python3
"""LANE 3 step 4: the within-window ceiling, the ranker's decision-point skill,
conditional winner/loser survival, and the gate-loosening sweeps.

Answers, in order:
  * where COULD the R have come from (oracle ceiling per decision window)
  * does the ranker beat random at the one place it decides
  * do winners survive gates at a different rate than losers (conditional)
  * what a looser / tighter min-predicted and cost ceiling would have earned
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


def boot_day(vals, days, nboot=2000, fn=np.mean):
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
        v = np.concatenate([arrs[i] for i in pick])
        out.append(fn(v))
    o = np.asarray(out)
    return {"point": float(fn(np.asarray(vals, dtype=float))),
            "ci95_lo": float(np.percentile(o, 2.5)),
            "ci95_hi": float(np.percentile(o, 97.5)),
            "p_two_sided_sign": float(2 * min((o <= 0).mean(), (o >= 0).mean()))}


def main():
    preds = None
    if PRED_KEY == "pred_daily":
        with gzip.open(OUT / "preds_daily.pkl.gz", "rb") as fh:
            preds = pickle.load(fh)

    report = {"pred_key": PRED_KEY}
    all_windows = []
    all_rows_meta = []
    sweeps = defaultdict(lambda: defaultdict(float))
    sweep_n = defaultdict(lambda: defaultdict(int))

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
            all_rows_meta.append({
                "month": month, "day": r_["trading_day"],
                "gate": death.get(r_["candidate_occurrence_key"], "UNSEEN"),
                "resolved": r_["resolved"], "state": r_["state"],
                "net": F.net_actual(r_), "wc": F.net_wc(r_),
                "ot": r_["proposed_order_type"], "fam": r_["origin_family"],
                "cost": r_.get("cost_r"),
            })

        # ---- sweeps -------------------------------------------------------
        for mp in (-9.99, 0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50, 1.00):
            s, _d, _dd = F.run_funnel(rows, pred_key=PRED_KEY, min_pred=mp)
            p = F.portfolio(s)
            sweeps["min_pred"][mp] += p["actual_net_r"]
            sweeps["min_pred_wc"][mp] += p["worst_case_net_r"]
            sweep_n["min_pred"][mp] += p["selected"]
        for mc in (0.05, 0.10, 0.15, 0.20, 0.30, 0.50, 1.00, 99.0):
            s, _d, _dd = F.run_funnel(rows, pred_key=PRED_KEY, max_cost=mc)
            p = F.portfolio(s)
            sweeps["max_cost"][mc] += p["actual_net_r"]
            sweeps["max_cost_wc"][mc] += p["worst_case_net_r"]
            sweep_n["max_cost"][mc] += p["selected"]
        for pol in ("market_top_abstain", "mixed", "market_rerank"):
            s, _d, _dd = F.run_funnel(rows, pred_key=PRED_KEY, policy=pol)
            p = F.portfolio(s)
            sweeps["policy"][pol] += p["actual_net_r"]
            sweeps["policy_wc"][pol] += p["worst_case_net_r"]
            sweep_n["policy"][pol] += p["selected"]
        print(json.dumps({"month": month, "windows": len(windows), "trades": len(sel)}),
              flush=True)

    report["sweeps"] = {k: {str(kk): round(vv, 4) for kk, vv in sorted(v.items(), key=lambda x: str(x[0]))}
                        for k, v in sweeps.items()}
    report["sweep_trade_counts"] = {k: {str(kk): vv for kk, vv in sorted(v.items(), key=lambda x: str(x[0]))}
                                    for k, v in sweep_n.items()}

    # ---------------- (1) within-window ceiling --------------------------
    def ceiling(pop, label):
        if not pop:
            return None
        days = [w["trading_day"] for w in pop]
        res = {}
        for arm in ("pick_actual", "rank2_actual", "oracle_max_actual",
                    "oracle_min_actual", "mean_actual", "mincost_actual",
                    "market_argmax_actual"):
            vals = [w[arm] for w in pop if w[arm] is not None]
            dd = [w["trading_day"] for w in pop if w[arm] is not None]
            res[arm] = {"n": len(vals), "sum": round(float(np.sum(vals)), 4),
                        "mean": float(np.mean(vals)) if vals else None,
                        "boot": boot_day(vals, dd, 1000)}
        # ranker vs random, paired within window
        paired = [(w["pick_actual"], w["mean_actual"], w["trading_day"])
                  for w in pop if w["pick_actual"] is not None and w["mean_actual"] is not None]
        if paired:
            d = [a - b for a, b, _ in paired]
            res["pick_minus_random_paired"] = boot_day(d, [x[2] for x in paired], 2000)
            res["pick_minus_random_paired"]["n"] = len(d)
        hitrate = [1.0 if w["pick_is_window_best"] else 0.0 for w in pop if w["n_resolved"]]
        nav = [w["n_available"] for w in pop if w["n_resolved"]]
        res["pick_is_window_best_rate"] = float(np.mean(hitrate)) if hitrate else None
        res["random_would_be_best_rate"] = float(np.mean([1.0 / n for n in nav])) if nav else None
        res["mean_n_available"] = float(np.mean([w["n_available"] for w in pop]))
        res["windows"] = len(pop)
        res["windows_with_a_positive_available"] = sum(1 for w in pop if w["n_positive_available"])
        res["label"] = label
        return res

    report["ceiling_all_ranked_windows"] = ceiling(all_windows, "every window that reached the ranker")
    report["ceiling_decided_windows"] = ceiling(
        [w for w in all_windows if w["outcome_gate"] in ("TRADED", "G5_market_top_abstain")],
        "windows whose top cleared the 0.10 min-predicted bar")
    report["ceiling_traded_windows"] = ceiling(
        [w for w in all_windows if w["outcome_gate"] == "TRADED"], "windows actually traded")
    report["ceiling_abstained_windows"] = ceiling(
        [w for w in all_windows if w["outcome_gate"] == "G5_market_top_abstain"],
        "windows abstained because the top was LIMIT")
    report["ceiling_standdown_windows"] = ceiling(
        [w for w in all_windows if w["outcome_gate"] == "G4_top_below_min_pred"],
        "windows stood down because top pred < 0.10")

    # ---------------- (2) conditional winner/loser survival --------------
    resolved = [m for m in all_rows_meta if m["resolved"]]
    nets = np.asarray([m["net"] for m in resolved], dtype=float)
    hi, lo = float(np.percentile(nets, 90)), float(np.percentile(nets, 10))
    for m in resolved:
        m["cls"] = "winner" if m["net"] > hi else ("loser" if m["net"] < lo else "middle")
    order = list(F.GATES) + [F.TERMINAL]
    rank = {g: i for i, g in enumerate(order)}
    cond = {}
    for i, gate in enumerate(F.GATES):
        entry = {}
        for cls in ("winner", "loser", "middle"):
            pop = [m for m in resolved if m["cls"] == cls and rank.get(m["gate"], 99) >= i]
            surv = [m for m in pop if rank.get(m["gate"], 99) > i]
            entry[cls] = {"reached": len(pop), "survived": len(surv),
                          "survival_rate": len(surv) / len(pop) if pop else None}
        w, l = entry["winner"], entry["loser"]
        entry["winner_minus_loser_survival"] = (
            (w["survival_rate"] - l["survival_rate"])
            if w["survival_rate"] is not None and l["survival_rate"] is not None else None)
        entry["selectivity_ratio"] = (
            (w["survival_rate"] / l["survival_rate"])
            if w["survival_rate"] and l["survival_rate"] else None)
        cond[gate] = entry
    report["conditional_survival"] = {"decile_hi": hi, "decile_lo": lo, "gates": cond}

    # ---------------- (3) censoring asymmetry at the rank gate ------------
    reach3 = [m for m in all_rows_meta if rank.get(m["gate"], 99) >= rank["G3_lost_rank"]]
    top3 = [m for m in reach3 if m["gate"] != "G3_lost_rank"]
    lost3 = [m for m in reach3 if m["gate"] == "G3_lost_rank"]
    def cens(pop):
        return {"n": len(pop),
                "censored": sum(1 for m in pop if not m["resolved"]),
                "censor_rate": (sum(1 for m in pop if not m["resolved"]) / len(pop)) if pop else None,
                "limit_share": (sum(1 for m in pop if m["ot"] == "LIMIT") / len(pop)) if pop else None,
                "no_fill_share": (sum(1 for m in pop if m["state"] == "NO_FILL") / len(pop)) if pop else None,
                "mean_cost_r": float(np.mean([m["cost"] for m in pop if m["cost"] is not None])) if pop else None}
    report["rank_gate_censoring"] = {"ranked_top": cens(top3), "lost_rank": cens(lost3)}

    (OUT / f"ceiling_{TAG}.json").write_text(json.dumps(report, indent=1, sort_keys=True, default=float))
    with gzip.open(OUT / f"windows_{TAG}.pkl.gz", "wb") as fh:
        pickle.dump(all_windows, fh, protocol=5)
    print("WROTE", OUT / f"ceiling_{TAG}.json")


if __name__ == "__main__":
    main()
