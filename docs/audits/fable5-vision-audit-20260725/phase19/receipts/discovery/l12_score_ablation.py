#!/usr/bin/env python3
"""l12 step 4: ablate the scheduler quality score term by term.

The scheduler ranks with 15 additive components (scheduler:15781-15797, assembled
:21990-22092).  Reconstructed dominant form:

  score = 0.55*ev + 1.20*(p-0.50) + 0.20*conf + 0.15*completeness
        + 0.10*fill + 6.00*max(0, ev-cost)*p*fill*completeness - 0.80*cost

Two of those terms are exact constants on 100% of the pool (conf=0.55, completeness=1.0).
Cost is subtracted TWICE (inside the weight-6.0 executable-transfer term and again as
cost_penalty).  Probability is applied TWICE (inside ev via the debate engine, and again
as the executable-value multiplier).

This measures, for each ablation, the mean gross R of the top-K ranked candidates.
"""
import gzip
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w0_ws  # noqa: E402

ANCHOR = os.path.join(HERE, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz")
KS = [21, 50, 100, 250, 500, 1000, 2000, 4095, 7210]

W_EV = 0.55
W_P = 1.20
W_CONF = 0.20
W_COMP = 0.15
W_FILL = 0.10
W_XFER = 6.00
W_COST = 0.80


def scores(r):
    ev = r.get("candidate_ev_r")
    p = r.get("candidate_probability")
    c = r.get("cost_r")
    f = r.get("execution_fill_probability")
    k = r.get("source_completeness")
    conf = r.get("candidate_confidence")
    if None in (ev, p, c, k, conf):
        return None
    if f is None:
        f = 0.0
    k = max(0.0, min(1.0, float(k)))
    pm = max(0.0, min(1.0, float(p)))
    fm = max(0.0, min(1.0, float(f)))
    net = ev - c
    base = (W_EV * ev + W_P * (p - 0.50) + W_CONF * conf + W_COMP * k + W_FILL * f)
    xfer_full = W_XFER * max(0.0, net) * pm * fm * k
    out = {}
    out["A_as_is"] = base + xfer_full - W_COST * c
    out["B_single_charge_cost"] = base + xfer_full                       # drop cost_penalty
    out["C_no_double_probability"] = (base + W_XFER * max(0.0, net) * fm * k
                                      - W_COST * c)
    out["D_no_fill_multiplier"] = (base + W_XFER * max(0.0, net) * pm * k
                                   - W_COST * c)
    out["E_no_double_p_no_fill"] = base + W_XFER * max(0.0, net) * k - W_COST * c
    out["F_plain_expected_net"] = net
    out["G_plain_ev"] = ev
    out["H_plain_probability"] = p
    out["I_neg_cost"] = -c
    out["J_neg_fill_prob"] = -f
    out["K_unfloored_xfer"] = base + W_XFER * net * pm * fm * k - W_COST * c
    return out


def topk_stat(rows, key, k):
    ranked = sorted(rows, key=lambda r: -r["_s"][key])[:k]
    g = [r["gross_r"] for r in ranked if r.get("gross_r") is not None]
    if not g:
        return None
    return {"n": len(g), "gross": round(sum(g) / len(g), 6),
            "win": round(sum(1 for x in g if x > 0) / len(g), 5),
            "sum": round(sum(g), 2)}


def main():
    rows = w0_ws.load()
    by = {}
    for r in rows:
        by[(r.get("candidate_id"), r.get("decision_time_utc"))] = r
    with gzip.open(ANCHOR, "rt") as fh:
        for line in fh:
            if not line.strip():
                continue
            a = json.loads(line)
            t = by.get((a.get("candidate_id"), a.get("decision_time_utc")))
            if t is not None:
                t["_mkt_r"] = a.get("mkt_r_prev_close")

    usable = []
    for r in rows:
        s = scores(r)
        if s is None or r.get("gross_r") is None:
            continue
        r["_s"] = s
        usable.append(r)
    clean = [r for r in usable
             if r.get("_mkt_r") is not None and r["_mkt_r"] > -1.0]

    def cost_pass(r):
        sr, tr = r.get("spread_r"), r.get("cost_r")
        return sr is not None and tr is not None and sr <= 0.10 and tr <= 0.15
    clean_pass = [r for r in clean if cost_pass(r)]

    pops = {"ALL": usable, "CLEAN": clean, "CLEAN_COSTPASS": clean_pass}
    keys = list(usable[0]["_s"].keys())
    out = {"pop_sizes": {k: len(v) for k, v in pops.items()}, "ks": KS, "table": {}}
    rng = random.Random(20260804)
    for pname, pop in pops.items():
        base_mean = round(sum(r["gross_r"] for r in pop) / len(pop), 6)
        out["table"][pname] = {"population_mean_gross": base_mean, "scores": {}}
        for key in keys:
            out["table"][pname]["scores"][key] = {
                str(k): topk_stat(pop, key, k) for k in KS if k <= len(pop)}
        # random baseline, 200 draws
        rnd = {}
        for k in KS:
            if k > len(pop):
                continue
            acc = []
            for _ in range(200):
                acc.append(sum(x["gross_r"] for x in rng.sample(pop, k)) / k)
            rnd[str(k)] = {"n": k, "gross": round(sum(acc) / len(acc), 6),
                           "p05": round(sorted(acc)[10], 6),
                           "p95": round(sorted(acc)[189], 6)}
        out["table"][pname]["scores"]["Z_random"] = rnd

    dest = os.path.join(HERE, "L12_SCORE_ABLATION_V1.json")
    with open(dest, "w") as fh:
        json.dump(out, fh, indent=1)

    for pname in pops:
        print("== %s  n=%d  pop_mean_gross=%.5f" % (
            pname, len(pops[pname]), out["table"][pname]["population_mean_gross"]))
        hdr = "%-26s" % "score"
        for k in [21, 100, 500, 2000]:
            hdr += "%12s" % ("top%d" % k)
        print(hdr)
        for key in keys + ["Z_random"]:
            line = "%-26s" % key
            for k in [21, 100, 500, 2000]:
                v = out["table"][pname]["scores"][key].get(str(k))
                line += "%12s" % ("%.4f" % v["gross"] if v else "-")
            print(line)
    print("WROTE", dest)


if __name__ == "__main__":
    main()
