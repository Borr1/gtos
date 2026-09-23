#!/usr/bin/env python3
"""l12 step 4b: the same ablation on the FILL-HONEST outcome, with bootstrap CIs.

w0 established gross_r is fill-blind and manufactures +0.2776 R/trade of value no limit
order could capture. Re-run the score ablation on fill_honest_walk_r so the ranking
verdict cannot be an artifact of the scoring convention.
"""
import gzip
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w0_ws  # noqa: E402
from l12_score_ablation import scores  # noqa: E402

ANCHOR = os.path.join(HERE, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz")
KS = [50, 100, 250, 500, 1000, 2000, 4000]
YCOLS = ["gross_r", "fill_honest_walk_r", "plain_walk_r"]


def topk(rows, key, k, y):
    ranked = sorted(rows, key=lambda r: -r["_s"][key])[:k]
    g = [r[y] for r in ranked if r.get(y) is not None]
    if not g:
        return None
    return {"n": len(g), "mean": round(sum(g) / len(g), 6),
            "win": round(sum(1 for x in g if x > 0) / len(g), 5)}


def main():
    rows = w0_ws.load()
    by = {}
    for r in rows:
        by[(r.get("candidate_id"), r.get("decision_time_utc"))] = r
    with gzip.open(ANCHOR, "rt") as fh:
        for line in fh:
            if line.strip():
                a = json.loads(line)
                t = by.get((a.get("candidate_id"), a.get("decision_time_utc")))
                if t is not None:
                    t["_mkt_r"] = a.get("mkt_r_prev_close")

    usable = []
    for r in rows:
        s = scores(r)
        if s is None:
            continue
        r["_s"] = s
        usable.append(r)
    clean = [r for r in usable if r.get("_mkt_r") is not None and r["_mkt_r"] > -1.0]

    keys = list(usable[0]["_s"].keys())
    out = {"n_all": len(usable), "n_clean": len(clean), "ks": KS, "res": {}}
    for pname, pop in (("ALL", usable), ("CLEAN", clean)):
        out["res"][pname] = {"pop_means": {}}
        for y in YCOLS:
            v = [r[y] for r in pop if r.get(y) is not None]
            out["res"][pname]["pop_means"][y] = {
                "n": len(v), "mean": round(sum(v) / len(v), 6) if v else None}
        for y in YCOLS:
            out["res"][pname][y] = {
                key: {str(k): topk(pop, key, k, y) for k in KS if k <= len(pop)}
                for key in keys}

    # bootstrap: A_as_is vs F_plain_expected_net at K=250 on CLEAN, fill-honest
    rng = random.Random(7)
    diffs = {}
    for y in YCOLS:
        for k in (100, 250, 500):
            d = []
            for _ in range(400):
                samp = [clean[rng.randrange(len(clean))] for _ in range(len(clean))]
                a = topk(samp, "A_as_is", k, y)
                f = topk(samp, "F_plain_expected_net", k, y)
                if a and f:
                    d.append(f["mean"] - a["mean"])
            d.sort()
            diffs["%s_K%d" % (y, k)] = {
                "median_F_minus_A": round(d[len(d) // 2], 6),
                "p05": round(d[int(.05 * len(d))], 6),
                "p95": round(d[int(.95 * len(d))], 6),
                "frac_F_better": round(sum(1 for x in d if x > 0) / len(d), 4)}
    out["bootstrap_F_minus_A"] = diffs

    dest = os.path.join(HERE, "L12_SCORE_ABLATION2_V1.json")
    with open(dest, "w") as fh:
        json.dump(out, fh, indent=1)

    for pname in ("ALL", "CLEAN"):
        print("== %s pop means:" % pname,
              {y: out["res"][pname]["pop_means"][y]["mean"] for y in YCOLS})
        for y in ("fill_honest_walk_r",):
            print("  y=%s" % y)
            hdr = "  %-26s" % "score"
            for k in (100, 250, 500, 1000, 2000):
                hdr += "%11s" % ("top%d" % k)
            print(hdr)
            for key in keys:
                line = "  %-26s" % key
                for k in (100, 250, 500, 1000, 2000):
                    v = out["res"][pname][y][key].get(str(k))
                    line += "%11s" % ("%.4f" % v["mean"] if v else "-")
                print(line)
    print("BOOTSTRAP F-A:", json.dumps(out["bootstrap_F_minus_A"], indent=0)[:900])
    print("WROTE", dest)


if __name__ == "__main__":
    main()
