#!/usr/bin/env python3
"""l12b: (1) paired significance of ranking on INVERTED execution_fill_probability vs the
production score and vs random; (2) the mechanism — entry-limit distance from market
(mkt_r, measured no-look-ahead) vs realised R, independent of the model."""
import gzip, json, math, os, random, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w0_ws  # noqa
ANCHOR = os.path.join(HERE, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz")
W = (0.55, 1.20, 0.20, 0.15, 0.10, 6.00, 0.80)


def score_A(r):
    ev, p, c = r.get("candidate_ev_r"), r.get("candidate_probability"), r.get("cost_r")
    f, k, cf = r.get("execution_fill_probability"), r.get("source_completeness"), r.get("candidate_confidence")
    if None in (ev, p, c, k, cf):
        return None
    f = 0.0 if f is None else f
    k = max(0., min(1., float(k))); pm = max(0., min(1., p)); fm = max(0., min(1., f))
    return (W[0]*ev + W[1]*(p-.5) + W[2]*cf + W[3]*k + W[4]*f
            + W[5]*max(0., ev-c)*pm*fm*k - W[6]*c)


def st(v):
    n = len(v); m = sum(v)/n
    sd = (sum((x-m)**2 for x in v)/max(1, n-1))**.5
    return {"n": n, "mean": round(m, 6), "sd": round(sd, 4),
            "t": round(m/(sd/math.sqrt(n)), 3) if sd else None}


def main():
    rows = w0_ws.load()
    by = {(r["candidate_id"], r["decision_time_utc"]): r for r in rows}
    with gzip.open(ANCHOR, "rt") as fh:
        for line in fh:
            if line.strip():
                a = json.loads(line)
                t = by.get((a["candidate_id"], a["decision_time_utc"]))
                if t is not None:
                    t["_mkt"] = a.get("mkt_r_prev_close")
                    t["_anchor_exact"] = a.get("anchor_exact")
    out = {}
    rng = random.Random(77)
    for pop in ("ALL", "CLEAN"):
        use = []
        for r in rows:
            if pop == "CLEAN" and not (r.get("_mkt") is not None and r["_mkt"] > -1.0):
                continue
            s = score_A(r)
            if s is None or r.get("execution_fill_probability") is None:
                continue
            r["_A"] = s
            use.append(r)
        wins = defaultdict(list)
        for r in use:
            wins[r["decision_time_utc"]].append(r)
        wl = list(wins.values())
        res = {"n_windows": len(wl)}
        for y in ("gross_r", "fill_honest_walk_r"):
            d_vs_score, d_vs_rand, lv, av, rv = [], [], [], [], []
            for c in wl:
                a = max(c, key=lambda r: r["_A"])
                lo = min(c, key=lambda r: r["execution_fill_probability"])
                rd = rng.choice(c)
                if a.get(y) is None or lo.get(y) is None or rd.get(y) is None:
                    continue
                av.append(a[y]); lv.append(lo[y]); rv.append(rd[y])
                d_vs_score.append(lo[y]-a[y]); d_vs_rand.append(lo[y]-rd[y])
            perm = 0
            obs = sum(d_vs_score)/len(d_vs_score)
            for _ in range(4000):
                s = sum(x if rng.random() < .5 else -x for x in d_vs_score)/len(d_vs_score)
                if abs(s) >= abs(obs):
                    perm += 1
            res[y] = {
                "SCORE_A": st(av), "FILLPROB_LOWEST": st(lv), "RANDOM_1seed": st(rv),
                "paired_LOW_minus_SCORE": st(d_vs_score),
                "paired_LOW_minus_RANDOM": st(d_vs_rand),
                "sign_flip_p_LOW_vs_SCORE": round((perm+1)/4001, 5),
                "frac_windows_LOW_better": round(sum(1 for x in d_vs_score if x > 0)/len(d_vs_score), 4),
                "frac_windows_identical": round(sum(1 for x in d_vs_score if abs(x) < 1e-12)/len(d_vs_score), 4)}
        out[pop] = res

    # MECHANISM: distance buckets, no model involved
    buckets = [(-1e9, -1.0, "past_stop"), (-1.0, -1e-12, "marketable"), (-1e-12, 1e-12, "at_limit"),
               (1e-12, 0.25, "rest_0-0.25R"), (0.25, 0.5, "rest_0.25-0.5R"), (0.5, 1.0, "rest_0.5-1R"),
               (1.0, 2.0, "rest_1-2R"), (2.0, 5.0, "rest_2-5R"), (5.0, 1e9, "rest_>5R")]
    mech = {}
    for lo, hi, name in buckets:
        sel = [r for r in rows if r.get("_mkt") is not None and lo < r["_mkt"] <= hi]
        if not sel:
            continue
        g = [r["gross_r"] for r in sel if r.get("gross_r") is not None]
        h = [r["fill_honest_walk_r"] for r in sel if r.get("fill_honest_walk_r") is not None]
        fp = [r["execution_fill_probability"] for r in sel if r.get("execution_fill_probability") is not None]
        tt = [1 for r in sel if r.get("entry_touched")]
        mech[name] = {"n": len(sel),
                      "gross_mean": round(sum(g)/len(g), 5) if g else None,
                      "gross_win": round(sum(1 for x in g if x > 0)/len(g), 5) if g else None,
                      "honest_mean": round(sum(h)/len(h), 5) if h else None,
                      "mean_model_fillprob": round(sum(fp)/len(fp), 5) if fp else None,
                      "realised_entry_touch_rate": round(len(tt)/len(sel), 5),
                      "median_cost_r": round(sorted(r["cost_r"] for r in sel)[len(sel)//2], 5)}
    out["MECHANISM_distance_buckets"] = mech
    dest = os.path.join(HERE, "L12B_FILLPROB_MECHANISM_V1.json")
    json.dump(out, open(dest, "w"), indent=1)
    for pop in ("ALL", "CLEAN"):
        print("==", pop, "windows", out[pop]["n_windows"])
        for y in ("gross_r", "fill_honest_walk_r"):
            b = out[pop][y]
            print("  %-18s A %8.4f | LOWFILL %8.4f | RAND %8.4f | d %7.4f t %6s p %s better%% %s"
                  % (y, b["SCORE_A"]["mean"], b["FILLPROB_LOWEST"]["mean"], b["RANDOM_1seed"]["mean"],
                     b["paired_LOW_minus_SCORE"]["mean"], b["paired_LOW_minus_SCORE"]["t"],
                     b["sign_flip_p_LOW_vs_SCORE"], b["frac_windows_LOW_better"]))
    print("-- MECHANISM (no model): distance of entry limit from market at decision")
    print("   %-16s %6s %9s %8s %9s %9s %8s" % ("bucket", "n", "gross", "win", "honest", "modelP", "touch"))
    for k, v in mech.items():
        print("   %-16s %6d %9.4f %8.4f %9.4f %9.4f %8.4f"
              % (k, v["n"], v["gross_mean"], v["gross_win"], v["honest_mean"],
                 v["mean_model_fillprob"], v["realised_entry_touch_rate"]))
    print("WROTE", dest)


if __name__ == "__main__":
    main()
