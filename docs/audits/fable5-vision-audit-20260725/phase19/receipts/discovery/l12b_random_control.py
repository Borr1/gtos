#!/usr/bin/env python3
"""l12b: the control the ablation never ran — is the 15-component scheduler score
better than a RANDOM pick from the same window, and how does it rank against every
single-field ranker and the oracle?

Per decision window: pick 1 candidate under each rule; report mean realised R.
"""
import gzip, json, math, os, random, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w0_ws  # noqa

ANCHOR = os.path.join(HERE, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz")
W_EV, W_P, W_CONF, W_COMP, W_FILL, W_XFER, W_COST = 0.55, 1.20, 0.20, 0.15, 0.10, 6.00, 0.80


def score_A(r):
    ev, p, c = r.get("candidate_ev_r"), r.get("candidate_probability"), r.get("cost_r")
    f, k, conf = r.get("execution_fill_probability"), r.get("source_completeness"), r.get("candidate_confidence")
    if None in (ev, p, c, k, conf):
        return None
    f = 0.0 if f is None else f
    k = max(0.0, min(1.0, float(k))); pm = max(0.0, min(1.0, p)); fm = max(0.0, min(1.0, f))
    return (W_EV*ev + W_P*(p-.5) + W_CONF*conf + W_COMP*k + W_FILL*f
            + W_XFER*max(0., ev-c)*pm*fm*k - W_COST*c)


def summ(v):
    n = len(v); m = sum(v)/n
    sd = (sum((x-m)**2 for x in v)/max(1, n-1))**.5
    return {"n": n, "mean": round(m, 6), "t": round(m/(sd/math.sqrt(n)), 3) if sd else None}


def main():
    rows = w0_ws.load()
    by = {(r["candidate_id"], r["decision_time_utc"]): r for r in rows}
    with gzip.open(ANCHOR, "rt") as fh:
        for line in fh:
            if line.strip():
                a = json.loads(line)
                t = by.get((a.get("candidate_id"), a.get("decision_time_utc")))
                if t is not None:
                    t["_mkt_r"] = a.get("mkt_r_prev_close")
    out = {}
    for pop in ("ALL", "CLEAN"):
        use = []
        for r in rows:
            if pop == "CLEAN" and not (r.get("_mkt_r") is not None and r["_mkt_r"] > -1.0):
                continue
            s = score_A(r)
            if s is None:
                continue
            r["_A"] = s
            use.append(r)
        wins = defaultdict(list)
        for r in use:
            wins[r["decision_time_utc"]].append(r)
        wl = list(wins.values())
        res = {"n_windows": len(wl), "n_candidates": len(use),
               "mean_window_size": round(len(use)/len(wl), 3), "rules": {}}
        for y in ("gross_r", "fill_honest_walk_r"):
            res["rules"][y] = {}
            # score A
            res["rules"][y]["SCORE_A_as_is"] = summ(
                [max(c, key=lambda r: r["_A"]).get(y) for c in wl
                 if max(c, key=lambda r: r["_A"]).get(y) is not None])
            # random control: 200 seeds
            means = []
            for seed in range(200):
                rng = random.Random(1000+seed)
                v = [rng.choice(c).get(y) for c in wl]
                v = [x for x in v if x is not None]
                means.append(sum(v)/len(v))
            mm = sum(means)/len(means)
            sd = (sum((x-mm)**2 for x in means)/(len(means)-1))**.5
            res["rules"][y]["RANDOM_200seeds"] = {
                "n": len(wl), "mean": round(mm, 6), "sd_across_seeds": round(sd, 6),
                "p05": round(sorted(means)[9], 6), "p95": round(sorted(means)[189], 6)}
            # every-candidate mean (no selection at all)
            allv = [r.get(y) for r in use if r.get(y) is not None]
            res["rules"][y]["NO_SELECTION_all_candidates"] = summ(allv)
            # single-field rankers, both directions
            for fld in ("candidate_ev_r", "candidate_probability", "execution_fill_probability",
                        "entry_quality_fill_probability", "cost_r", "spread_r", "risk_distance",
                        "matched_sleeve_count", "mfe_r_by_bar_5"):
                for sgn, tag in ((1, "HIGH"), (-1, "LOW")):
                    v = []
                    for c in wl:
                        cc = [r for r in c if r.get(fld) is not None]
                        if not cc:
                            continue
                        p = max(cc, key=lambda r: sgn*r[fld])
                        if p.get(y) is not None:
                            v.append(p[y])
                    if v:
                        res["rules"][y]["FIELD_%s_%s" % (fld, tag)] = summ(v)
            # oracle ceiling
            v = [max(c, key=lambda r: (r.get(y) if r.get(y) is not None else -9e9)).get(y) for c in wl]
            res["rules"][y]["ORACLE_best_in_window"] = summ([x for x in v if x is not None])
            v = [min(c, key=lambda r: (r.get(y) if r.get(y) is not None else 9e9)).get(y) for c in wl]
            res["rules"][y]["ANTIORACLE_worst_in_window"] = summ([x for x in v if x is not None])
        out[pop] = res
    dest = os.path.join(HERE, "L12B_RANDOM_CONTROL_V1.json")
    json.dump(out, open(dest, "w"), indent=1)
    for pop in out:
        print("==", pop, "windows", out[pop]["n_windows"], "meanwin", out[pop]["mean_window_size"])
        for y in out[pop]["rules"]:
            print("  --", y)
            for k, v in sorted(out[pop]["rules"][y].items(), key=lambda kv: -(kv[1]["mean"])):
                print("     %-42s %9.4f  n=%d" % (k, v["mean"], v["n"]))
    print("WROTE", dest)


if __name__ == "__main__":
    main()
