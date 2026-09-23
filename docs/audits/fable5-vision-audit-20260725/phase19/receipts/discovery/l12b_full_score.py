#!/usr/bin/env python3
"""l12b: the production score reconstructed with the TWO penalties the earlier ablation
omitted — execution_fill_shortfall_rank_penalty (scheduler:21936-21943, weight 1.50 against
a 0.80 floor) and selector_reduce_risk_new_entry_penalty (:19504, base 0.20) — then
per-term deletion, fill-share of dispersion, and the paired value of stripping the whole
fill layer."""
import gzip, json, math, os, random, sys
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
    act = str(r.get("effective_selector_action") or "").lower()
    return {
        "ev_component": 0.55*ev,
        "probability_component": 1.20*(p-0.50),
        "confidence_component": 0.20*cf,
        "source_completeness_component": 0.15*k,
        "fill_probability_component": 0.10*f,
        "executable_transfer_component": 6.00*max(0., ev-c)*pm*fm*k,
        "uncertainty_penalty": -0.20*0.35,
        "cost_penalty": -0.80*c,
        "execution_fill_shortfall_rank_penalty": -1.50*max(0.0, 0.80-f),
        "selector_reduce_risk_new_entry_penalty": (-0.20 if "reduced-risk" in act else 0.0),
    }


FILL_TERMS = ("fill_probability_component", "execution_fill_shortfall_rank_penalty")


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
    rng = random.Random(31337)
    for pop in ("ALL", "CLEAN"):
        use = []
        for r in rows:
            if pop == "CLEAN" and not (r.get("_mkt") is not None and r["_mkt"] > -1.0):
                continue
            t = terms(r)
            if t is None:
                continue
            r["_t"] = t; r["_full"] = sum(t.values())
            use.append(r)
        keys = list(use[0]["_t"].keys())
        wins = defaultdict(list)
        for r in use:
            wins[r["decision_time_utc"]].append(r)
        wl = [c for c in wins.values() if len(c) > 1]
        res = {"n_candidates": len(use), "n_multi_windows": len(wl), "terms": {}}
        for k in keys:
            n, m, sd = st([r["_t"][k] for r in use])
            wsd = [st([r["_t"][k] for r in c])[2] for c in wl]
            changed = 0; dg = []; dh = []
            for c in wl:
                p1 = max(c, key=lambda r: r["_full"])
                p2 = max(c, key=lambda r: r["_full"] - r["_t"][k])
                if p2 is not p1:
                    changed += 1
                if p1.get("gross_r") is not None and p2.get("gross_r") is not None:
                    dg.append(p2["gross_r"]-p1["gross_r"])
                if p1.get("fill_honest_walk_r") is not None and p2.get("fill_honest_walk_r") is not None:
                    dh.append(p2["fill_honest_walk_r"]-p1["fill_honest_walk_r"])
            ng, mg, sg = st(dg); nh, mh, sh = st(dh)
            res["terms"][k] = {
                "pool_mean": round(m, 5), "pool_sd": round(sd, 5),
                "mean_within_window_sd": round(sum(wsd)/len(wsd), 5),
                "n_distinct": len({round(r["_t"][k], 9) for r in use}),
                "pick_changed_share": round(changed/len(wl), 5),
                "delete_delta_gross": round(mg, 6),
                "delete_delta_gross_t": round(mg/(sg/math.sqrt(ng)), 3) if sg else None,
                "delete_delta_honest": round(mh, 6),
                "delete_delta_honest_t": round(mh/(sh/math.sqrt(nh)), 3) if sh else None}
        # whole-fill-layer strip: delete both additive fill terms AND the fill multiplier
        arms = {}
        for name, fn in (
            ("PROD_full", lambda r: r["_full"]),
            ("STRIP_fill_additive", lambda r: r["_full"] - sum(r["_t"][k] for k in FILL_TERMS)),
            ("STRIP_fill_everywhere", lambda r: (r["_full"] - sum(r["_t"][k] for k in FILL_TERMS)
                                                 - r["_t"]["executable_transfer_component"]
                                                 + (r["_t"]["executable_transfer_component"]
                                                    / max(1e-9, min(1., max(0., r.get("execution_fill_probability") or 0.))))
                                                 if (r.get("execution_fill_probability") or 0) > 0
                                                 else r["_full"] - sum(r["_t"][k] for k in FILL_TERMS))),
            ("STRIP_fill_and_xfer", lambda r: (r["_full"] - sum(r["_t"][k] for k in FILL_TERMS)
                                               - r["_t"]["executable_transfer_component"])),
            ("PLAIN_ev_minus_cost", lambda r: (r.get("candidate_ev_r") or 0) - (r.get("cost_r") or 0)),
            ("INVERT_fillprob", lambda r: -(r.get("execution_fill_probability") or 0)),
        ):
            picks = [max(c, key=fn) for c in wl]
            a = {}
            for y in ("gross_r", "fill_honest_walk_r"):
                v = [p[y] for p in picks if p.get(y) is not None]
                n, m, sd = st(v)
                a[y] = {"n": n, "mean": round(m, 6), "t": round(m/(sd/math.sqrt(n)), 3)}
            arms[name] = a
        # paired deltas vs PROD
        prod = [max(c, key=lambda r: r["_full"]) for c in wl]
        for name, fn in (("STRIP_fill_additive", lambda r: r["_full"] - sum(r["_t"][k] for k in FILL_TERMS)),
                         ("STRIP_fill_and_xfer", lambda r: (r["_full"] - sum(r["_t"][k] for k in FILL_TERMS)
                                                            - r["_t"]["executable_transfer_component"])),
                         ("INVERT_fillprob", lambda r: -(r.get("execution_fill_probability") or 0))):
            alt = [max(c, key=fn) for c in wl]
            for y in ("gross_r", "fill_honest_walk_r"):
                d = [b[y]-a[y] for a, b in zip(prod, alt) if a.get(y) is not None and b.get(y) is not None]
                n, m, sd = st(d)
                perm = sum(1 for _ in range(3000)
                           if abs(sum(x if rng.random() < .5 else -x for x in d)/n) >= abs(m))
                arms[name].setdefault("paired_vs_PROD", {})[y] = {
                    "n": n, "delta": round(m, 6), "t": round(m/(sd/math.sqrt(n)), 3),
                    "sign_flip_p": round((perm+1)/3001, 5)}
        res["arms"] = arms
        # fill share of within-window dispersion
        tot = sum(res["terms"][k]["mean_within_window_sd"] for k in keys)
        res["fill_share_of_within_window_dispersion_additive_only"] = round(
            sum(res["terms"][k]["mean_within_window_sd"] for k in FILL_TERMS)/tot, 5)
        out[pop] = res
    dest = os.path.join(HERE, "L12B_FULL_SCORE_V1.json")
    json.dump(out, open(dest, "w"), indent=1)
    for pop in out:
        r = out[pop]
        print("==", pop, "cands", r["n_candidates"], "windows", r["n_multi_windows"])
        print("   %-42s %8s %8s %6s %7s %8s %8s" % ("term", "poolSD", "winSD", "dist", "chg%", "dGross", "dHonest"))
        for k, v in sorted(r["terms"].items(), key=lambda kv: -kv[1]["mean_within_window_sd"]):
            print("   %-42s %8.4f %8.4f %6d %7.4f %8.4f %8.4f" % (
                k, v["pool_sd"], v["mean_within_window_sd"], v["n_distinct"],
                v["pick_changed_share"], v["delete_delta_gross"], v["delete_delta_honest"]))
        print("   ARMS:")
        for k, v in r["arms"].items():
            pv = v.get("paired_vs_PROD", {}).get("fill_honest_walk_r")
            print("     %-24s gross %8.4f  honest %8.4f %s" % (
                k, v["gross_r"]["mean"], v["fill_honest_walk_r"]["mean"],
                ("| d %+.4f t %s p %s" % (pv["delta"], pv["t"], pv["sign_flip_p"])) if pv else ""))
    print("WROTE", dest)


if __name__ == "__main__":
    main()
