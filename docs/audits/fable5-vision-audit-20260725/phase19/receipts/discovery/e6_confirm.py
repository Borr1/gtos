#!/usr/bin/env python3
"""e6_confirm — the four controls that decide whether the entry-delay find is bankable.

 C1  CANCEL vs DEFER, decomposed per month. The rule has two separable halves:
       (a) delay submission by 60 s and take the next touch of the same level  = DEFER
       (b) additionally ABANDON the candidate if the level printed in that minute = CANCEL
     Which half carries the value?
 C2  PSEUDO-REPLICATION control (W0-F1). candidate_id is not a primary key; a quarter of
     January is the same setup re-emitted every 15 min. Does the effect survive first-emission-only
     and one-vote-per-setup weighting?
 C3  PER-DAY SIGN TEST. ~105 trading days across five months: on how many is the delta positive?
 C4  COST-AWARE BOTTOM LINE. Gross-honest R is not money. Charge the frozen cost model and the
     spread-corrected variants (the 7.3x / 8.5x measured over-charge) on the trades each rule
     actually takes.
"""
import collections, gzip, json, os, sys

D = os.path.dirname(os.path.abspath(__file__))
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY"]
OUT = os.path.join(D, "E6_CONFIRM_V1.json")


def load(m):
    with gzip.open(os.path.join(D, "e6_MECH_%s.jsonl.gz" % m), "rt") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def stat(vs):
    n = len(vs)
    if n == 0: return None
    m = sum(vs) / n
    sd = (sum((v - m) ** 2 for v in vs) / (n - 1)) ** 0.5 if n > 1 else 0.0
    return {"n": n, "mean": round(m, 5), "t": round(m / (sd / n ** 0.5), 3) if sd else 0.0,
            "total_R": round(sum(vs), 1)}


def rule_vals(rows, mode, k=1):
    """R per candidate-opportunity under one rule."""
    out = []
    for r in rows:
        if mode == "shipped":
            out.append(r["hr"] if r["fb"] > 0 else 0.0)
        elif mode == "cancel":
            out.append(0.0 if (r["fb"] < 0 or r["fb"] <= k) else r["hr"])
        elif mode == "defer":
            out.append(r["dhr%d" % k])
    return out


def main():
    data = {m: load(m) for m in MONTHS}
    allrows = [r for m in MONTHS for r in data[m]]
    clean = [r for r in allrows if r["born"] != "born_past_stop"]
    res = {"n_all": len(allrows), "n_clean": len(clean)}

    # ---------------- C1 cancel vs defer ----------------
    c1 = {}
    for m in MONTHS + ["POOLED"]:
        rows = [r for r in clean if (m == "POOLED" or r["month"] == m)]
        s = stat(rule_vals(rows, "shipped"))
        d = stat(rule_vals(rows, "defer", 1))
        c = stat(rule_vals(rows, "cancel", 1))
        c1[m] = {"n": s["n"], "shipped": s["mean"], "defer_k1": d["mean"], "cancel_k1": c["mean"],
                 "value_of_delay_alone": round(d["mean"] - s["mean"], 5),
                 "value_of_cancel": round(c["mean"] - d["mean"], 5),
                 "value_total": round(c["mean"] - s["mean"], 5),
                 "t_shipped": s["t"], "t_cancel": c["t"], "t_defer": d["t"]}
    res["C1_cancel_vs_defer"] = c1

    # ---------------- C2 pseudo-replication ----------------
    # first emission = earliest decision_time for a candidate_id inside its month
    first = {}
    cnt = collections.Counter()
    for r in clean:
        k = (r["month"], r["cid"])
        cnt[k] += 1
        if k not in first or r["dt"] < first[k]:
            first[k] = r["dt"]
    fe = [r for r in clean if first[(r["month"], r["cid"])] == r["dt"]]
    dupcnt = collections.Counter(cnt.values())
    c2 = {"n_clean": len(clean), "n_distinct_setups": len(cnt),
          "n_first_emission": len(fe),
          "repeated_setup_rows": len(clean) - len(cnt),
          "dup_count_hist": {str(k): v for k, v in sorted(dupcnt.items())[:10]},
          "max_repeats": max(cnt.values())}
    for lab, rows in (("all_rows", clean), ("first_emission_only", fe)):
        s = stat(rule_vals(rows, "shipped")); c = stat(rule_vals(rows, "cancel", 1))
        c2[lab] = {"n": s["n"], "k0": s["mean"], "k1": c["mean"],
                   "delta": round(c["mean"] - s["mean"], 5), "t_k0": s["t"]}
    # setup-weighted: every distinct candidate_id gets one vote (mean of its rows)
    g0 = collections.defaultdict(list); g1 = collections.defaultdict(list)
    for r, v0, v1 in zip(clean, rule_vals(clean, "shipped"), rule_vals(clean, "cancel", 1)):
        g0[(r["month"], r["cid"])].append(v0); g1[(r["month"], r["cid"])].append(v1)
    sw0 = stat([sum(v) / len(v) for v in g0.values()])
    sw1 = stat([sum(v) / len(v) for v in g1.values()])
    c2["setup_weighted"] = {"n": sw0["n"], "k0": sw0["mean"], "k1": sw1["mean"],
                            "delta": round(sw1["mean"] - sw0["mean"], 5)}
    # bar-1 share inside repeated vs unique setups
    rep = [r for r in clean if cnt[(r["month"], r["cid"])] > 1]
    uni = [r for r in clean if cnt[(r["month"], r["cid"])] == 1]
    for lab, rows in (("repeated_setups", rep), ("unique_setups", uni)):
        if not rows: continue
        s = stat(rule_vals(rows, "shipped")); c = stat(rule_vals(rows, "cancel", 1))
        c2[lab] = {"n": len(rows), "k0": s["mean"], "k1": c["mean"],
                   "delta": round(c["mean"] - s["mean"], 5),
                   "bar1_share": round(sum(1 for r in rows if r["fb"] == 1) / len(rows), 4)}
    res["C2_pseudo_replication"] = c2

    # ---------------- C3 per-day sign test ----------------
    byday = collections.defaultdict(list)
    for r in clean:
        byday[(r["month"], r["dt"][:10])].append(r)
    days = []
    for k, rows in sorted(byday.items()):
        if len(rows) < 30: continue
        s = stat(rule_vals(rows, "shipped")); c = stat(rule_vals(rows, "cancel", 1))
        days.append({"day": k[1], "month": k[0], "n": len(rows), "k0": s["mean"],
                     "k1": c["mean"], "delta": round(c["mean"] - s["mean"], 5)})
    pos = sum(1 for d in days if d["delta"] > 0)
    res["C3_per_day"] = {"n_days": len(days), "positive_days": pos,
                         "share_positive": round(pos / len(days), 4) if days else None,
                         "worst_days": sorted(days, key=lambda d: d["delta"])[:6],
                         "best_days": sorted(days, key=lambda d: -d["delta"])[:4],
                         "by_month_positive": {m: "%d/%d" % (
                             sum(1 for d in days if d["month"] == m and d["delta"] > 0),
                             sum(1 for d in days if d["month"] == m)) for m in MONTHS},
                         "all_days": days}

    # ---------------- C4 cost-aware bottom line ----------------
    # cost is charged ONLY on candidates the rule actually trades.
    c4 = {}
    for div, lab in ((1.0, "frozen"), (7.3, "spread_over_7.3x"), (8.5, "spread_over_8.5x")):
        for mode, k in (("shipped", 0), ("cancel", 1), ("cancel", 5)):
            vals = []
            traded = 0
            for r in clean:
                if mode == "shipped":
                    take = r["fb"] > 0
                else:
                    take = r["fb"] > k
                if not take:
                    vals.append(0.0); continue
                traded += 1
                cost = r.get("cost_r")
                sp = r.get("spread_r")
                if cost is None:
                    vals.append(r["hr"]); continue
                if div > 1.0 and sp is not None:
                    cost = cost - sp + sp / div
                vals.append(r["hr"] - cost)
            s = stat(vals)
            c4["%s_%s_k%d" % (lab, mode, k)] = {
                "n_opp": s["n"], "n_traded": traded,
                "net_R_per_opportunity": s["mean"], "t": s["t"],
                "net_R_per_trade": round(s["total_R"] / traded, 5) if traded else None}
    res["C4_cost_aware"] = c4

    json.dump(res, open(OUT, "w"), indent=1)

    print("=== C1 CANCEL vs DEFER (clean, R per candidate-opportunity) ===")
    print("%-8s %7s %10s %10s %10s %12s %12s" % ("month", "n", "shipped", "defer_k1", "cancel_k1", "delay_alone", "cancel_half"))
    for m in MONTHS + ["POOLED"]:
        b = c1[m]
        print("%-8s %7d %+10.5f %+10.5f %+10.5f %+12.5f %+12.5f" % (
            m, b["n"], b["shipped"], b["defer_k1"], b["cancel_k1"],
            b["value_of_delay_alone"], b["value_of_cancel"]))
    print("\n=== C2 PSEUDO-REPLICATION ===")
    print("distinct setups %d of %d rows (max repeats %d)" % (
        c2["n_distinct_setups"], c2["n_clean"], c2["max_repeats"]))
    for lab in ["all_rows", "first_emission_only", "setup_weighted", "repeated_setups", "unique_setups"]:
        b = c2.get(lab)
        if b: print("%-22s n=%6d k0 %+0.5f -> k1 %+0.5f  delta %+0.5f" % (lab, b["n"], b["k0"], b["k1"], b["delta"]))
    print("\n=== C3 PER-DAY SIGN TEST ===")
    print("days %d | positive %d (%.4f) | by month %s" % (
        res["C3_per_day"]["n_days"], pos, res["C3_per_day"]["share_positive"],
        res["C3_per_day"]["by_month_positive"]))
    print("worst:", [(d["day"], d["delta"], d["n"]) for d in res["C3_per_day"]["worst_days"]])
    print("\n=== C4 COST-AWARE (net R per candidate-opportunity, and per trade) ===")
    print("%-32s %8s %12s %12s" % ("book", "traded", "net/opp", "net/trade"))
    for k2, v in c4.items():
        print("%-32s %8d %+12.5f %+12s" % (k2, v["n_traded"], v["net_R_per_opportunity"],
              ("%+.5f" % v["net_R_per_trade"]) if v["net_R_per_trade"] is not None else "-"))
    print("->", OUT)


if __name__ == "__main__":
    main()
