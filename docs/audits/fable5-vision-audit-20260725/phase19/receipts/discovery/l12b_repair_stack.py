#!/usr/bin/env python3
"""l12b: stack the repairs and price them, cumulatively and one at a time, as the mean
realised R of the single candidate the scheduler would select per decision window."""
import gzip, json, math, os, random, sys
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import w0_ws  # noqa
ANCHOR = os.path.join(HERE, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz")


def st(v):
    n = len(v); m = sum(v)/n
    sd = (sum((x-m)**2 for x in v)/max(1, n-1))**.5
    return {"n": n, "mean": round(m, 6), "t": round(m/(sd/math.sqrt(n)), 3) if sd else None}


def build(r, opt):
    ev, c, p = r["candidate_ev_r"], r["cost_r"], r["candidate_probability"]
    f = r.get("execution_fill_probability")
    f = 0.0 if f is None else f
    k = max(0., min(1., r["source_completeness"]))
    cf = r["candidate_confidence"]
    pm = max(0., min(1., p))
    fm = 1.0 if opt["no_fill_mult"] else max(0., min(1., f))
    if opt["declared_2R"]:
        ev = 3.0*p - 1.0
    net = ev - c
    if not opt["unfloor"]:
        net = max(0.0, net)
    s = (0.55*ev + 1.20*(p-0.5) + 0.20*cf + 0.15*k
         + (0.0 if opt["no_fill_add"] else 0.10*f)
         + 6.00*net*pm*fm*k
         - 0.20*0.35)
    if not opt["single_cost"]:
        s += -0.80*c
    if not opt["no_fill_add"]:
        s += -1.50*max(0.0, 0.80-f)
    act = str(r.get("effective_selector_action") or "").lower()
    if "reduced-risk" in act:
        s += -0.20
    return s


BASE = {"no_fill_mult": False, "no_fill_add": False, "declared_2R": False,
        "unfloor": False, "single_cost": False}
STEPS = [("R1_stop_validity_prefilter", None),
         ("R2_drop_fill_additive_terms", "no_fill_add"),
         ("R3_drop_fill_multiplier", "no_fill_mult"),
         ("R4_single_cost_charge", "single_cost"),
         ("R5_declared_2R_ev", "declared_2R"),
         ("R6_unfloor_net_edge", "unfloor")]


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
    usable = [r for r in rows if None not in (r.get("candidate_ev_r"), r.get("candidate_probability"),
                                              r.get("cost_r"), r.get("source_completeness"),
                                              r.get("candidate_confidence"))]
    rng = random.Random(9001)
    out = {}
    for label, prefilter in (("NO_PREFILTER", False), ("STOP_VALIDITY_PREFILTER", True)):
        pool = [r for r in usable
                if (not prefilter) or (r.get("_mkt") is not None and r["_mkt"] > -1.0)]
        wins = defaultdict(list)
        for r in pool:
            wins[r["decision_time_utc"]].append(r)
        wl = list(wins.values())
        res = {"n_windows": len(wl), "n_candidates": len(pool), "cumulative": {}, "marginal": {}}
        opt = dict(BASE)
        prev_pick = None
        for name, key in STEPS:
            if key:
                opt[key] = True
            picks = [max(c, key=lambda r: build(r, opt)) for c in wl]
            row = {}
            for y in ("gross_r", "fill_honest_walk_r"):
                row[y] = st([p[y] for p in picks if p.get(y) is not None])
                if prev_pick is not None:
                    d = [b[y]-a[y] for a, b in zip(prev_pick, picks)
                         if a.get(y) is not None and b.get(y) is not None]
                    row.setdefault("delta_vs_prev_step", {})[y] = st(d)
            res["cumulative"][name] = row
            prev_pick = picks
        # each repair ALONE against production
        prod = [max(c, key=lambda r: build(r, BASE)) for c in wl]
        res["production_baseline"] = {y: st([p[y] for p in prod if p.get(y) is not None])
                                      for y in ("gross_r", "fill_honest_walk_r")}
        for name, key in STEPS:
            if not key:
                continue
            o = dict(BASE); o[key] = True
            alt = [max(c, key=lambda r: build(r, o)) for c in wl]
            row = {}
            for y in ("gross_r", "fill_honest_walk_r"):
                d = [b[y]-a[y] for a, b in zip(prod, alt) if a.get(y) is not None and b.get(y) is not None]
                s = st(d)
                perm = sum(1 for _ in range(2000)
                           if abs(sum(x if rng.random() < .5 else -x for x in d)/len(d)) >= abs(s["mean"]))
                s["sign_flip_p"] = round((perm+1)/2001, 5)
                s["level"] = st([p[y] for p in alt if p.get(y) is not None])["mean"]
                row[y] = s
            res["marginal"][name] = row
        # the best rule found anywhere in this lane
        inv = [min(c, key=lambda r: (r.get("execution_fill_probability")
                                     if r.get("execution_fill_probability") is not None else 9)) for c in wl]
        res["BEST_RULE_lowest_modelled_fill_probability"] = {
            y: st([p[y] for p in inv if p.get(y) is not None]) for y in ("gross_r", "fill_honest_walk_r")}
        out[label] = res
    dest = os.path.join(HERE, "L12B_REPAIR_STACK_V1.json")
    json.dump(out, open(dest, "w"), indent=1)
    for lab in out:
        r = out[lab]
        print("==", lab, "windows", r["n_windows"], "cands", r["n_candidates"])
        print("   PROD baseline: gross %.4f honest %.4f" % (
            r["production_baseline"]["gross_r"]["mean"], r["production_baseline"]["fill_honest_walk_r"]["mean"]))
        print("   -- MARGINAL (each repair alone vs production)")
        for k, v in r["marginal"].items():
            h = v["fill_honest_walk_r"]
            print("      %-32s honest level %8.4f  d %+8.4f t %7s p %s" % (
                k, h["level"], h["mean"], h["t"], h["sign_flip_p"]))
        print("   -- CUMULATIVE")
        for k, v in r["cumulative"].items():
            print("      %-32s gross %8.4f honest %8.4f" % (
                k, v["gross_r"]["mean"], v["fill_honest_walk_r"]["mean"]))
        b = r["BEST_RULE_lowest_modelled_fill_probability"]
        print("   BEST RULE lowest-modelled-fill: gross %.4f honest %.4f (n=%d)" % (
            b["gross_r"]["mean"], b["fill_honest_walk_r"]["mean"], b["gross_r"]["n"]))
    print("WROTE", dest)


if __name__ == "__main__":
    main()
