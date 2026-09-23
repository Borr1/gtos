#!/usr/bin/env python3
"""LANE 3 step 3: the gate-by-gate attrition ledger, labelled by realized outcome.

(A) per gate x month: n killed / n passed, mean+median terminal_net_r of each,
    difference with a day-clustered bootstrap CI, and the ranking metric
    (E[killed] - E[passed]) * n_killed.
(B) winner/loser autopsy: death-gate histograms for the top and bottom realized
    decile.
(C) MARKET-top-abstain: realized outcome of every abstained LIMIT top.
(D) reverse decomposition of the taken book.

Usage: step3_attrition.py [pred_key]   (default pred_month_boundary)
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
OUT.mkdir(exist_ok=True)
PRED_KEY = sys.argv[1] if len(sys.argv) > 1 else "pred_month_boundary"
TAG = "daily" if PRED_KEY == "pred_daily" else "monthfit"
RNG = np.random.default_rng(20260812)
NBOOT = 2000


def daily_preds():
    with gzip.open(OUT / "preds_daily.pkl.gz", "rb") as fh:
        return pickle.load(fh)


def stats(rows, key):
    """key: 'actual' (resolved only) or 'wc' (worst-case convention)."""
    if key == "actual":
        vals = [F.net_actual(r) for r in rows if r["resolved"]]
        days = [r["trading_day"] for r in rows if r["resolved"]]
    else:
        vals = [F.net_wc(r) for r in rows]
        days = [r["trading_day"] for r in rows]
    if not vals:
        return {"n": 0, "mean": None, "median": None, "sum": 0.0}
    a = np.asarray(vals, dtype=float)
    return {
        "n": int(a.size),
        "mean": float(a.mean()),
        "median": float(np.median(a)),
        "sum": float(a.sum()),
        "sd": float(a.std(ddof=1)) if a.size > 1 else None,
        "positive_rate": float((a > 0).mean()),
        "_vals": a,
        "_days": days,
    }


def day_cluster_boot_diff(a_vals, a_days, b_vals, b_days, nboot=NBOOT):
    """CI95 on mean(a)-mean(b), resampling trading days with replacement.
    Days are the cluster unit; both arms are resampled on the same day draw so
    the comparison stays paired within day."""
    if not len(a_vals) or not len(b_vals):
        return None
    days = sorted(set(a_days) | set(b_days))
    idx = {d: i for i, d in enumerate(days)}
    A = defaultdict(list)
    B = defaultdict(list)
    for v, d in zip(a_vals, a_days):
        A[idx[d]].append(v)
    for v, d in zip(b_vals, b_days):
        B[idx[d]].append(v)
    Aa = [np.asarray(A.get(i, []), dtype=float) for i in range(len(days))]
    Bb = [np.asarray(B.get(i, []), dtype=float) for i in range(len(days))]
    out = []
    n = len(days)
    for _ in range(nboot):
        pick = RNG.integers(0, n, n)
        av = np.concatenate([Aa[i] for i in pick]) if n else np.asarray([])
        bv = np.concatenate([Bb[i] for i in pick]) if n else np.asarray([])
        if av.size == 0 or bv.size == 0:
            continue
        out.append(av.mean() - bv.mean())
    if not out:
        return None
    o = np.asarray(out)
    return {
        "diff_point": float(np.mean(a_vals) - np.mean(b_vals)),
        "ci95_lo": float(np.percentile(o, 2.5)),
        "ci95_hi": float(np.percentile(o, 97.5)),
        "p_two_sided_sign": float(2 * min((o <= 0).mean(), (o >= 0).mean())),
        "nboot": len(o),
    }


def clean(d):
    return {k: v for k, v in d.items() if not k.startswith("_")}


def main():
    preds = daily_preds() if PRED_KEY == "pred_daily" else None
    report = {"pred_key": PRED_KEY, "months": {}}
    pooled_rows = []
    pooled_death = {}
    for month in F.MONTHS:
        rows = F.load_month(month)
        if preds is not None:
            for r_ in rows:
                p = preds.get(r_["candidate_occurrence_key"])
                r_["pred_daily"] = p
        sel, disp, death = F.run_funnel(rows, pred_key=PRED_KEY)
        for r_ in rows:
            r_["death_gate"] = death.get(r_["candidate_occurrence_key"], "UNSEEN")
        pooled_rows.extend(rows)
        pooled_death.update(death)
        report["months"][month] = month_report(rows, sel, disp)
        print(json.dumps({"month": month, "trades": len(sel),
                          "disp": disp}, sort_keys=True), flush=True)
    report["pooled"] = month_report(
        pooled_rows,
        [r_ for r_ in pooled_rows if r_["death_gate"] == F.TERMINAL],
        None,
        pooled=True,
    )
    (OUT / f"attrition_{TAG}.json").write_text(json.dumps(report, indent=1, sort_keys=True,
                                                          default=float))
    print("WROTE", OUT / f"attrition_{TAG}.json")


def month_report(rows, sel, disp, pooled=False):
    order = list(F.GATES) + [F.TERMINAL]
    rank = {g: i for i, g in enumerate(order)}
    out = {"dispositions": disp, "n_occurrences": len(rows)}

    # ---------- (A) gate ledger ----------
    ledger = {}
    for i, gate in enumerate(F.GATES):
        reached = [r_ for r_ in rows if rank.get(r_["death_gate"], 99) >= i]
        killed = [r_ for r_ in rows if r_["death_gate"] == gate]
        passed = [r_ for r_ in rows if rank.get(r_["death_gate"], 99) > i]
        if not killed:
            continue
        row = {"n_reached": len(reached), "n_killed": len(killed), "n_passed": len(passed),
               "kill_rate": len(killed) / len(reached) if reached else None}
        for basis in ("actual", "wc"):
            sk = stats(killed, basis)
            sp = stats(passed, basis)
            boot = day_cluster_boot_diff(sk.get("_vals", []), sk.get("_days", []),
                                         sp.get("_vals", []), sp.get("_days", [])) \
                if sk["n"] and sp["n"] else None
            row[basis] = {
                "killed": clean(sk), "passed": clean(sp),
                "diff_killed_minus_passed": boot,
                "rank_metric_total_r_thrown_away": (
                    (sk["mean"] - sp["mean"]) * len(killed)
                    if sk["mean"] is not None and sp["mean"] is not None else None),
                "absolute_r_in_killed_population": sk["sum"],
                "anti_selective": (sk["mean"] is not None and sp["mean"] is not None
                                   and sk["mean"] > sp["mean"]),
            }
        # feasible one-per-window recovery: only gates that kill a top-of-window
        # candidate can be reversed one-for-one.
        if gate in ("G4_top_below_min_pred", "G5_market_top_abstain"):
            row["feasible_recovery"] = {
                "n_windows": len(killed),
                "actual_sum_r": stats(killed, "actual")["sum"],
                "wc_sum_r": stats(killed, "wc")["sum"],
                "outcomes": dict(sorted(Counter(r_["state"] or "CENSORED" for r_ in killed).items())),
                "families": dict(sorted(Counter(r_["origin_family"] for r_ in killed).items())),
            }
        ledger[gate] = row
    out["gate_ledger"] = ledger

    # ---------- (B) winner / loser autopsy ----------
    resolved = [r_ for r_ in rows if r_["resolved"]]
    vals = np.asarray([F.net_actual(r_) for r_ in resolved], dtype=float)
    if vals.size:
        hi = float(np.percentile(vals, 90))
        lo = float(np.percentile(vals, 10))
        winners = [r_ for r_, v in zip(resolved, vals) if v > hi]
        losers = [r_ for r_, v in zip(resolved, vals) if v < lo]
        allres = resolved
        def hist(pop):
            c = Counter(r_["death_gate"] for r_ in pop)
            n = sum(c.values())
            return {"n": n, "counts": dict(sorted(c.items())),
                    "share": {k: v / n for k, v in sorted(c.items())} if n else {}}
        out["winner_autopsy"] = {
            "decile_threshold_hi": hi, "decile_threshold_lo": lo,
            "winners": hist(winners), "losers": hist(losers), "all_resolved": hist(allres),
            "winner_mean_r": float(np.mean([F.net_actual(r_) for r_ in winners])) if winners else None,
            "loser_mean_r": float(np.mean([F.net_actual(r_) for r_ in losers])) if losers else None,
            "lift_ratio": {},
        }
        w, l = out["winner_autopsy"]["winners"], out["winner_autopsy"]["losers"]
        a = out["winner_autopsy"]["all_resolved"]
        for g in set(w["share"]) | set(l["share"]):
            base = a["share"].get(g)
            out["winner_autopsy"]["lift_ratio"][g] = {
                "winner_share": w["share"].get(g, 0.0),
                "loser_share": l["share"].get(g, 0.0),
                "all_share": base,
                "winner_over_all": (w["share"].get(g, 0.0) / base) if base else None,
                "loser_over_all": (l["share"].get(g, 0.0) / base) if base else None,
            }

    # ---------- (C) MARKET-top-abstain ----------
    abst = [r_ for r_ in rows if r_["death_gate"] == "G5_market_top_abstain"]
    taken = [r_ for r_ in rows if r_["death_gate"] == F.TERMINAL]
    out["abstain"] = {
        "n_abstained_windows": len(abst),
        "n_taken": len(taken),
        "abstained_outcomes": dict(sorted(Counter(r_["state"] or "CENSORED" for r_ in abst).items())),
        "abstained_actual": clean(stats(abst, "actual")),
        "abstained_wc": clean(stats(abst, "wc")),
        "taken_actual": clean(stats(taken, "actual")),
        "taken_wc": clean(stats(taken, "wc")),
        "abstained_by_family": {
            fam: {
                "n": len(g),
                "actual_sum": clean(stats(g, "actual"))["sum"],
                "actual_mean": clean(stats(g, "actual"))["mean"],
                "no_fill": sum(1 for x in g if x["state"] == "NO_FILL"),
                "censored": sum(1 for x in g if not x["resolved"]),
            }
            for fam, g in sorted(
                ((f, [x for x in abst if x["origin_family"] == f])
                 for f in {x["origin_family"] for x in abst}))
        },
    }
    sk, sp = stats(abst, "actual"), stats(taken, "actual")
    out["abstain"]["diff_abstained_minus_taken_actual"] = day_cluster_boot_diff(
        sk.get("_vals", []), sk.get("_days", []), sp.get("_vals", []), sp.get("_days", []))

    # ---------- (D) reverse decomposition of the taken book ----------
    out["taken_decomposition"] = {
        "by_state": {
            st: {"n": len(g),
                 "sum_actual": float(sum(F.net_actual(x) or 0.0 for x in g if x["resolved"])),
                 "sum_wc": float(sum(F.net_wc(x) for x in g))}
            for st, g in sorted(((s, [x for x in taken if (x["state"] or "CENSORED") == s])
                                 for s in {(x["state"] or "CENSORED") for x in taken}))
        },
        "by_family": {
            fam: {"n": len(g),
                  "sum_actual": float(sum(F.net_actual(x) or 0.0 for x in g if x["resolved"])),
                  "sum_wc": float(sum(F.net_wc(x) for x in g))}
            for fam, g in sorted(((f, [x for x in taken if x["origin_family"] == f])
                                  for f in {x["origin_family"] for x in taken}))
        },
        "by_symbol_top": dict(sorted(
            ((s, round(float(sum(F.net_actual(x) or 0.0 for x in taken
                                 if x["symbol"] == s and x["resolved"])), 4))
             for s in {x["symbol"] for x in taken}), key=lambda kv: kv[1])[:12]),
    }
    return out


if __name__ == "__main__":
    main()
