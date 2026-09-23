#!/usr/bin/env python3
"""l12b: decompose the scheduler score into its terms and measure, per term,
(a) its dispersion pool-wide, (b) its dispersion WITHIN a decision window (the only
dispersion that can change a pick), (c) how often the pick changes if the term is deleted,
(d) the realised-R cost of deleting it (paired, per window)."""
import gzip, json, math, os, sys
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import w0_ws  # noqa
ANCHOR = os.path.join(HERE, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz")


def terms(r):
    ev, p, c = r.get("candidate_ev_r"), r.get("candidate_probability"), r.get("cost_r")
    f, k, cf = r.get("execution_fill_probability"), r.get("source_completeness"), r.get("candidate_confidence")
    if None in (ev, p, c, k, cf):
        return None
    f = 0.0 if f is None else f
    k = max(0., min(1., float(k))); pm = max(0., min(1., p)); fm = max(0., min(1., f))
    return {"ev_component": 0.55*ev,
            "probability_component": 1.20*(p-0.50),
            "confidence_component": 0.20*cf,
            "source_completeness_component": 0.15*k,
            "fill_probability_component": 0.10*f,
            "executable_transfer_component": 6.00*max(0., ev-c)*pm*fm*k,
            "cost_penalty": -0.80*c}


def st(v):
    n = len(v); m = sum(v)/n
    sd = (sum((x-m)**2 for x in v)/max(1, n-1))**.5
    return n, m, sd


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
    out = {}
    for pop in ("ALL", "CLEAN"):
        use = []
        for r in rows:
            if pop == "CLEAN" and not (r.get("_mkt") is not None and r["_mkt"] > -1.0):
                continue
            t = terms(r)
            if t is None:
                continue
            r["_t"] = t
            use.append(r)
        keys = list(use[0]["_t"].keys())
        wins = defaultdict(list)
        for r in use:
            wins[r["decision_time_utc"]].append(r)
        wl = [c for c in wins.values() if len(c) > 1]
        res = {"n_candidates": len(use), "n_multi_windows": len(wl), "terms": {}}
        # pool dispersion + mean within-window dispersion
        for k in keys:
            n, m, sd = st([r["_t"][k] for r in use])
            wsd = []
            for c in wl:
                _, _, s = st([r["_t"][k] for r in c])
                wsd.append(s)
            res["terms"][k] = {"pool_mean": round(m, 5), "pool_sd": round(sd, 5),
                               "mean_within_window_sd": round(sum(wsd)/len(wsd), 5),
                               "n_distinct_pool": len({round(r["_t"][k], 9) for r in use})}
        # deletion test
        for r in use:
            r["_full"] = sum(r["_t"].values())
        base_pick = {}
        for c in wl:
            base_pick[id(c)] = max(c, key=lambda r: r["_full"])
        for k in keys:
            changed = 0
            dg, dh = [], []
            for c in wl:
                p2 = max(c, key=lambda r: r["_full"] - r["_t"][k])
                p1 = base_pick[id(c)]
                if p2 is not p1:
                    changed += 1
                for y, acc in (("gross_r", dg), ("fill_honest_walk_r", dh)):
                    if p1.get(y) is not None and p2.get(y) is not None:
                        acc.append(p2[y]-p1[y])
            ng, mg, sg = st(dg); nh, mh, sh = st(dh)
            res["terms"][k].update({
                "pick_changed_windows": changed,
                "pick_changed_share": round(changed/len(wl), 5),
                "delete_delta_gross": round(mg, 6),
                "delete_delta_gross_t": round(mg/(sg/math.sqrt(ng)), 3) if sg else None,
                "delete_delta_honest": round(mh, 6),
                "delete_delta_honest_t": round(mh/(sh/math.sqrt(nh)), 3) if sh else None})
        out[pop] = res
    dest = os.path.join(HERE, "L12B_COMPONENT_POWER_V1.json")
    json.dump(out, open(dest, "w"), indent=1)
    for pop in out:
        r = out[pop]
        print("==", pop, "cands", r["n_candidates"], "multi-windows", r["n_multi_windows"])
        print("   %-32s %9s %9s %7s %9s %8s %9s %8s" % (
            "term", "pool_sd", "winSD", "distinct", "chg%", "dGross", "dHonest", "tHon"))
        for k, v in sorted(r["terms"].items(), key=lambda kv: -kv[1]["mean_within_window_sd"]):
            print("   %-32s %9.4f %9.4f %7d %9.4f %8.4f %9.4f %8s" % (
                k, v["pool_sd"], v["mean_within_window_sd"], v["n_distinct_pool"],
                v["pick_changed_share"], v["delete_delta_gross"], v["delete_delta_honest"],
                v["delete_delta_honest_t"]))
    print("WROTE", dest)


if __name__ == "__main__":
    main()
