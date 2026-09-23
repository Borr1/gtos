#!/usr/bin/env python3
"""l12 step 2: does any decision-layer score ORDER outcomes at all?

A gate destroys value when the population it refuses is better than the population it
passes. This measures, for every score the decision path actually thresholds on, the
gross R by decile of that score. Monotone-increasing => the gate is a real filter.
Flat or inverted => the layer is noise dressed as risk management.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w0_ws  # noqa: E402

SCORES = [
    "candidate_ev_r",            # thesis EV; selector thresholds 0.10 / 0.02 on ev-cost
    "candidate_probability",     # thesis p
    "entry_quality_fill_probability",
    "execution_fill_probability",
    "cost_r",
    "spread_r",
    "risk_distance",
    "candidate_confidence",
]


def deciles(rows, key, ycol="gross_r", nb=10):
    vals = [(r.get(key), r.get(ycol)) for r in rows
            if r.get(key) is not None and r.get(ycol) is not None]
    if len(vals) < nb * 10:
        return {"n": len(vals), "note": "too_few"}
    vals.sort(key=lambda t: t[0])
    n = len(vals)
    out = []
    for b in range(nb):
        lo = b * n // nb
        hi = (b + 1) * n // nb
        seg = vals[lo:hi]
        ys = [y for _, y in seg]
        out.append({
            "bucket": b,
            "n": len(seg),
            "score_lo": round(seg[0][0], 6),
            "score_hi": round(seg[-1][0], 6),
            "gross_mean": round(sum(ys) / len(ys), 6),
            "win": round(sum(1 for y in ys if y > 0) / len(ys), 5),
        })
    # spearman-ish: correlation of bucket index with gross_mean
    xs = list(range(nb))
    ms = [d["gross_mean"] for d in out]
    mx = sum(xs) / nb
    mm = sum(ms) / nb
    cov = sum((x - mx) * (m - mm) for x, m in zip(xs, ms))
    vx = sum((x - mx) ** 2 for x in xs) ** 0.5
    vm = sum((m - mm) ** 2 for m in ms) ** 0.5
    r = cov / (vx * vm) if vx and vm else 0.0
    return {"n": n, "buckets": out,
            "monotone_corr_bucket_vs_gross": round(r, 4),
            "top_minus_bottom": round(out[-1]["gross_mean"] - out[0]["gross_mean"], 6)}


def main():
    rows = w0_ws.load()

    def cost_pass(r):
        sr, tr = r.get("spread_r"), r.get("cost_r")
        return sr is not None and tr is not None and sr <= 0.10 and tr <= 0.15

    passed = [r for r in rows if cost_pass(r)]

    out = {"pool_n": len(rows), "cost_pass_n": len(passed), "scores": {}}
    for key in SCORES:
        out["scores"][key] = {
            "ALL_POOL": deciles(rows, key),
            "COST_PASS": deciles(passed, key),
        }

    # derived: expected_net_r == ev - cost, the quantity the selector ladder thresholds
    for r in rows:
        ev, c = r.get("candidate_ev_r"), r.get("cost_r")
        r["_exp_net"] = None if (ev is None or c is None) else ev - c
    out["scores"]["_exp_net_ev_minus_cost"] = {
        "ALL_POOL": deciles(rows, "_exp_net"),
        "COST_PASS": deciles(passed, "_exp_net"),
    }

    dest = os.path.join(HERE, "L12_GATE_ORDERING_V1.json")
    with open(dest, "w") as fh:
        json.dump(out, fh, indent=1)

    print("%-34s %-10s %8s %9s %9s" % ("score", "pop", "corr", "top-bot", "n"))
    for key, d in out["scores"].items():
        for pop in ("ALL_POOL", "COST_PASS"):
            v = d[pop]
            if "buckets" not in v:
                continue
            print("%-34s %-10s %8.4f %9.4f %9d" % (
                key, pop, v["monotone_corr_bucket_vs_gross"],
                v["top_minus_bottom"], v["n"]))
    print("WROTE", dest)


if __name__ == "__main__":
    main()
