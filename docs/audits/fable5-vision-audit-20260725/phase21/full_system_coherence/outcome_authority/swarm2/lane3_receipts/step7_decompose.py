#!/usr/bin/env python3
"""LANE 3 step 7: the reverse decomposition (D) and the MARKET-conditional
winner/loser control for (B).

(D) For every window the funnel traded, the realized R decomposes exactly:
      pick  =  mean_of_available   +   (pick - mean_of_available)
    the first term is what a uniform random draw from the same window would
    have earned (the POOL component), the second is what the ranker's choice
    added or subtracted (the SELECTION component). They sum to the book.

(B) The population is 86 % LIMIT and 70 % of LIMIT never fills at exactly
    0.0 R, so any winner/loser rate computed over the whole population is a
    fill-rate statistic in disguise. Repeated inside the MARKET population,
    where every candidate fills, as the control.
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


def boot(vals, days, nboot=2000):
    if not len(vals):
        return None
    by = defaultdict(list)
    for v, d in zip(vals, days):
        by[d].append(v)
    arrs = [np.asarray(by[k], dtype=float) for k in sorted(by)]
    n = len(arrs)
    o = np.asarray([np.concatenate([arrs[i] for i in RNG.integers(0, n, n)]).mean()
                    for _ in range(nboot)])
    return {"point": float(np.mean(vals)), "n": int(len(vals)),
            "ci95_lo": float(np.percentile(o, 2.5)),
            "ci95_hi": float(np.percentile(o, 97.5)),
            "p_two_sided_sign": float(2 * min((o <= 0).mean(), (o >= 0).mean()))}


def main():
    preds = None
    if PRED_KEY == "pred_daily":
        with gzip.open(OUT / "preds_daily.pkl.gz", "rb") as fh:
            preds = pickle.load(fh)
    rep = {"pred_key": PRED_KEY, "months": {}}
    pooled_win = []
    pooled_market = []
    order = list(F.GATES) + [F.TERMINAL]
    rank = {g: i for i, g in enumerate(order)}

    for month in F.MONTHS:
        rows = F.load_month(month)
        if preds is not None:
            for r_ in rows:
                r_["pred_daily"] = preds.get(r_["candidate_occurrence_key"])
        sel, disp, death, windows = F.run_funnel(rows, pred_key=PRED_KEY, diagnose=True)
        pooled_win.extend(windows)

        # ---- (D) pool vs selection on the traded windows ------------------
        traded = [w for w in windows if w["outcome_gate"] == "TRADED"
                  and w["pick_actual"] is not None and w["mean_actual"] is not None]
        pick = [w["pick_actual"] for w in traded]
        pool = [w["mean_actual"] for w in traded]
        selc = [a - b for a, b in zip(pick, pool)]
        days = [w["trading_day"] for w in traded]
        # exit decomposition of the book actually taken
        tk = [r_ for r_ in rows if death.get(r_["candidate_occurrence_key"]) == F.TERMINAL]
        byst = defaultdict(lambda: [0, 0.0])
        for r_ in tk:
            st = r_["state"] or "CENSORED"
            byst[st][0] += 1
            byst[st][1] += (F.net_actual(r_) if r_["resolved"] else F.net_wc(r_))
        tgt = [F.net_actual(r_) for r_ in tk if r_["state"] == "TARGET"]
        stp = [F.net_actual(r_) for r_ in tk if r_["state"] == "STOP"]
        payoff = (float(np.mean(tgt)) if tgt else None)
        risk = (abs(float(np.mean(stp))) if stp else None)
        nres = sum(1 for r_ in tk if r_["resolved"])
        m = {
            "n_traded_windows": len(traded),
            "book_actual_r": round(float(np.sum(pick)), 4),
            "pool_component_r": round(float(np.sum(pool)), 4),
            "selection_component_r": round(float(np.sum(selc)), 4),
            "pool_share_of_loss": (float(np.sum(pool)) / float(np.sum(pick))
                                   if np.sum(pick) else None),
            "selection_mean_per_window": boot(selc, days, 2000),
            "exit_decomposition": {k: {"n": v[0], "r": round(v[1], 4)} for k, v in sorted(byst.items())},
            "mean_target_payoff_r": payoff,
            "mean_stop_loss_r": risk,
            "achieved_target_rate": (len(tgt) / nres) if nres else None,
            "breakeven_target_rate_ignoring_time_stops": (
                risk / (payoff + risk) if payoff and risk else None),
        }
        rep["months"][month] = m

        # ---- (B) MARKET-conditional control -------------------------------
        mk = [r_ for r_ in rows if r_["proposed_order_type"] == "MARKET" and r_["resolved"]]
        for r_ in mk:
            r_["_g"] = death.get(r_["candidate_occurrence_key"], "UNSEEN")
        pooled_market.extend(mk)
        print(json.dumps({"month": month, "traded": len(traded),
                          "book": m["book_actual_r"], "pool": m["pool_component_r"],
                          "sel": m["selection_component_r"]}, sort_keys=True), flush=True)

    # pooled (D)
    traded = [w for w in pooled_win if w["outcome_gate"] == "TRADED"
              and w["pick_actual"] is not None and w["mean_actual"] is not None]
    pick = [w["pick_actual"] for w in traded]
    pool = [w["mean_actual"] for w in traded]
    selc = [a - b for a, b in zip(pick, pool)]
    rep["pooled_decomposition"] = {
        "n_traded_windows": len(traded),
        "book_actual_r": round(float(np.sum(pick)), 4),
        "pool_component_r": round(float(np.sum(pool)), 4),
        "selection_component_r": round(float(np.sum(selc)), 4),
        "selection_mean_per_window": boot(selc, [w["trading_day"] for w in traded], 4000),
    }

    # pooled (B) MARKET-conditional
    nets = np.asarray([F.net_actual(r_) for r_ in pooled_market], dtype=float)
    hi, lo = float(np.percentile(nets, 90)), float(np.percentile(nets, 10))
    cls = ["winner" if v > hi else ("loser" if v < lo else "middle") for v in nets]
    cond = {}
    for i, gate in enumerate(F.GATES):
        entry = {}
        for c in ("winner", "loser", "middle"):
            popn = [r_ for r_, k in zip(pooled_market, cls)
                    if k == c and rank.get(r_["_g"], 99) >= i]
            surv = [r_ for r_ in popn if rank.get(r_["_g"], 99) > i]
            entry[c] = {"reached": len(popn), "survived": len(surv),
                        "survival_rate": len(surv) / len(popn) if popn else None}
        w, l = entry["winner"], entry["loser"]
        entry["selectivity_ratio"] = (w["survival_rate"] / l["survival_rate"]
                                      if w["survival_rate"] and l["survival_rate"] else None)
        cond[gate] = entry
    hist = lambda pop: dict(sorted(Counter(r_["_g"] for r_ in pop).items()))
    rep["market_only_autopsy"] = {
        "n_market_resolved": len(pooled_market), "decile_hi": hi, "decile_lo": lo,
        "winner_death_gates": hist([r_ for r_, k in zip(pooled_market, cls) if k == "winner"]),
        "loser_death_gates": hist([r_ for r_, k in zip(pooled_market, cls) if k == "loser"]),
        "all_death_gates": hist(pooled_market),
        "conditional_survival": cond,
    }
    (OUT / f"decompose_{TAG}.json").write_text(json.dumps(rep, indent=1, sort_keys=True, default=float))
    print("WROTE", OUT / f"decompose_{TAG}.json")


if __name__ == "__main__":
    main()
