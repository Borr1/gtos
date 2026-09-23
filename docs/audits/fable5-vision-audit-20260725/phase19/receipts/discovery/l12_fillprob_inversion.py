#!/usr/bin/env python3
"""l12 step 3: execution_fill_probability orders gross R BACKWARDS (corr -0.878).

That quantity feeds the scheduler quality score and the risk-finalizer transfer rank.
Question: does the inversion survive after removing w0-capture's born_past_stop artifact
(3,516 rows whose stop was already breached at the decision instant)?
If yes, the ranking layer is actively anti-selecting.
"""
import gzip
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w0_ws  # noqa: E402

ANCHOR = os.path.join(HERE, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz")


def deciles(rows, key, ycol="gross_r", nb=10):
    vals = [(r.get(key), r.get(ycol)) for r in rows
            if r.get(key) is not None and r.get(ycol) is not None]
    if len(vals) < nb * 10:
        return {"n": len(vals), "note": "too_few"}
    vals.sort(key=lambda t: t[0])
    n = len(vals)
    out = []
    for b in range(nb):
        seg = vals[b * n // nb:(b + 1) * n // nb]
        ys = [y for _, y in seg]
        out.append({"b": b, "n": len(seg),
                    "lo": round(seg[0][0], 5), "hi": round(seg[-1][0], 5),
                    "gross": round(sum(ys) / len(ys), 6),
                    "win": round(sum(1 for y in ys if y > 0) / len(ys), 5)})
    xs = list(range(nb)); ms = [d["gross"] for d in out]
    mx = sum(xs) / nb; mm = sum(ms) / nb
    cov = sum((x - mx) * (m - mm) for x, m in zip(xs, ms))
    vx = sum((x - mx) ** 2 for x in xs) ** .5
    vm = sum((m - mm) ** 2 for m in ms) ** .5
    return {"n": n, "buckets": out,
            "corr": round(cov / (vx * vm) if vx and vm else 0.0, 4),
            "top_minus_bottom": round(ms[-1] - ms[0], 6)}


def main():
    rows = w0_ws.load()
    by_key = {}
    for r in rows:
        by_key[(r.get("candidate_id"), r.get("decision_time_utc"))] = r

    n_anchor = 0
    with gzip.open(ANCHOR, "rt") as fh:
        for line in fh:
            if not line.strip():
                continue
            a = json.loads(line)
            k = (a.get("candidate_id"), a.get("decision_time_utc"))
            r = by_key.get(k)
            if r is None:
                continue
            n_anchor += 1
            r["_mkt_r"] = a.get("mkt_r_prev_close")
            r["_bars_to_entry_touch"] = a.get("bars_to_entry_touch")

    def born(r):
        m = r.get("_mkt_r")
        if m is None:
            return "unanchored"
        if m <= -1.0:
            return "past_stop"
        if abs(m) < 1e-12:
            return "at_market"
        if m > 0:
            return "marketable"
        return "resting"

    for r in rows:
        r["_born"] = born(r)

    clean = [r for r in rows if r["_born"] not in ("past_stop", "unanchored")]
    resting = [r for r in rows if r["_born"] == "resting"]

    def cost_pass(r):
        sr, tr = r.get("spread_r"), r.get("cost_r")
        return sr is not None and tr is not None and sr <= 0.10 and tr <= 0.15

    clean_pass = [r for r in clean if cost_pass(r)]

    out = {
        "anchor_joined": n_anchor,
        "born_census": {},
        "execution_fill_probability": {
            "ALL_POOL": deciles(rows, "execution_fill_probability"),
            "CLEAN_no_past_stop": deciles(clean, "execution_fill_probability"),
            "CLEAN_and_COST_PASS": deciles(clean_pass, "execution_fill_probability"),
            "RESTING_ONLY": deciles(resting, "execution_fill_probability"),
        },
        "entry_quality_fill_probability": {
            "CLEAN_no_past_stop": deciles(clean, "entry_quality_fill_probability"),
        },
        "candidate_ev_r": {
            "CLEAN_no_past_stop": deciles(clean, "candidate_ev_r"),
        },
        "candidate_probability": {
            "CLEAN_no_past_stop": deciles(clean, "candidate_probability"),
        },
        "cost_r": {"CLEAN_no_past_stop": deciles(clean, "cost_r")},
        "spread_r": {"CLEAN_no_past_stop": deciles(clean, "spread_r")},
        "risk_distance": {"CLEAN_no_past_stop": deciles(clean, "risk_distance")},
    }
    for r in rows:
        b = r["_born"]
        d = out["born_census"].setdefault(b, {"n": 0, "sum_gross": 0.0})
        d["n"] += 1
        d["sum_gross"] += r.get("gross_r") or 0.0
    for b, d in out["born_census"].items():
        d["mean_gross"] = round(d["sum_gross"] / d["n"], 6)
        d["sum_gross"] = round(d["sum_gross"], 3)

    # the 0.92 flat block vs the decayed block
    flat = [r for r in clean if r.get("execution_fill_probability") == 0.92]
    dec = [r for r in clean if r.get("execution_fill_probability") is not None
           and r["execution_fill_probability"] != 0.92]

    def st(v):
        g = [x.get("gross_r") for x in v if x.get("gross_r") is not None]
        return {"n": len(g), "gross": round(sum(g) / len(g), 6) if g else None,
                "win": round(sum(1 for y in g if y > 0) / len(g), 5) if g else None}
    out["flat092_vs_decayed_CLEAN"] = {"flat_0.92": st(flat), "decayed": st(dec)}

    dest = os.path.join(HERE, "L12_FILLPROB_INVERSION_V1.json")
    with open(dest, "w") as fh:
        json.dump(out, fh, indent=1)

    print("born census:", {k: (v["n"], v["mean_gross"]) for k, v in out["born_census"].items()})
    for pop, v in out["execution_fill_probability"].items():
        if "buckets" in v:
            print("efp %-22s n=%6d corr=%7.4f top-bot=%8.4f" % (
                pop, v["n"], v["corr"], v["top_minus_bottom"]))
    print("flat0.92 vs decayed (clean):", out["flat092_vs_decayed_CLEAN"])
    for k in ("entry_quality_fill_probability", "candidate_ev_r", "candidate_probability",
              "cost_r", "spread_r", "risk_distance"):
        v = out[k]["CLEAN_no_past_stop"]
        if "buckets" in v:
            print("%-32s CLEAN n=%6d corr=%7.4f top-bot=%8.4f" % (
                k, v["n"], v["corr"], v["top_minus_bottom"]))
    print("WROTE", dest)


if __name__ == "__main__":
    main()
