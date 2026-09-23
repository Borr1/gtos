#!/usr/bin/env python3
"""x2 step 7 - do any of the NEW intra-bar features separate continuation from reversion?

Benchmark to beat: the estate's max |Cohen's d| over all 28 existing pre-decision fields is
0.152 (wave-19 discovery, prior swarm).  Every field here is computed from the 15 M1 bars of
the DECISION bar and is therefore strictly pre-decision, but invisible to a system that only
ever reads the completed M15 bar.
"""
import sys, os, json, gzip, collections, math
D = os.path.dirname(os.path.abspath(__file__))
FEATS = ["ib_range_atr", "ib_body_atr", "ib_clv", "ib_signed_clv", "ib_efficiency", "ib_path_atr",
         "ib_dir_changes", "ib_minute_of_high", "ib_minute_of_low", "ib_extreme_late",
         "ib_signed_extreme_minute", "ib_signed_adverse_minute", "ib_second_half_drift_atr",
         "ib_late_range_share", "ib_close_vs_mean_atr", "ib_fav_excursion_r",
         "ib_adv_excursion_r", "ib_signed_bar_move_r"]


def cohend(a, b):
    if len(a) < 2 or len(b) < 2: return 0.0
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    va = sum((x - ma) ** 2 for x in a) / (len(a) - 1)
    vb = sum((x - mb) ** 2 for x in b) / (len(b) - 1)
    sp = math.sqrt(((len(a) - 1) * va + (len(b) - 1) * vb) / (len(a) + len(b) - 2))
    return (ma - mb) / sp if sp > 0 else 0.0


def deciles(rows, f, key="gross_r"):
    v = sorted(rows, key=lambda r: r[f])
    n = len(v); out = []
    for k in range(10):
        seg = v[k * n // 10:(k + 1) * n // 10]
        if not seg: continue
        y = [r[key] for r in seg]
        m = sum(y) / len(y)
        se = (sum((x - m) ** 2 for x in y) / max(1, len(y) - 1)) ** .5 / math.sqrt(len(y))
        out.append((len(seg), seg[0][f], seg[-1][f], m, se))
    return out


def main():
    rows = [json.loads(l) for l in gzip.open(os.path.join(D, "x2_INTRABAR_FEATURES_V1.jsonl.gz"), "rt")]
    print("rows", len(rows))
    res = {"n": len(rows), "features": {}, "per_family_best": {}, "deciles": {}}
    tgt = [r for r in rows if r["which_came_first"] == "target"]
    stp = [r for r in rows if r["which_came_first"] == "stop"]
    print("target-first %d  stop-first %d  neither %d" % (len(tgt), len(stp), len(rows) - len(tgt) - len(stp)))
    print("\n%-28s %8s %10s %10s %10s" % ("feature", "|d|", "mean_tgt", "mean_stop", "spearman_gross"))
    ranked = []
    for f in FEATS:
        a = [r[f] for r in tgt]; b = [r[f] for r in stp]
        d = cohend(a, b)
        # rank correlation with gross_r
        s = sorted(rows, key=lambda r: r[f]); rx = {id(r): i for i, r in enumerate(s)}
        s2 = sorted(rows, key=lambda r: r["gross_r"]); ry = {id(r): i for i, r in enumerate(s2)}
        n = len(rows)
        cov = sum((rx[id(r)] - (n - 1) / 2) * (ry[id(r)] - (n - 1) / 2) for r in rows)
        var = sum((i - (n - 1) / 2) ** 2 for i in range(n))
        rho = cov / var if var else 0.0
        ranked.append((abs(d), f, d, sum(a) / len(a), sum(b) / len(b), rho))
        res["features"][f] = {"cohen_d": round(d, 4), "mean_target_first": round(sum(a) / len(a), 4),
                              "mean_stop_first": round(sum(b) / len(b), 4), "spearman_gross_r": round(rho, 4)}
    ranked.sort(reverse=True)
    for ad, f, d, ma, mb, rho in ranked:
        print("%-28s %8.4f %10.4f %10.4f %10.4f" % (f, ad, ma, mb, rho))
    best = ranked[0]
    print("\nBEST |Cohen d| = %.4f on %s  (estate benchmark on the 28 completed-bar fields: 0.152)" % (best[0], best[1]))
    for f in [x[1] for x in ranked[:5]]:
        print("\n== gross_r by decile of %s ==" % f)
        for k, (n, lo, hi, m, se) in enumerate(deciles(rows, f)):
            print("  d%-2d n=%5d [%9.4f,%9.4f] gross=%8.4f se=%.4f" % (k + 1, n, lo, hi, m, se))
        res["deciles"][f] = [{"n": n, "lo": lo, "hi": hi, "gross_r": m, "se": se}
                             for n, lo, hi, m, se in deciles(rows, f)]
    print("\n== best feature per family (|Cohen d| target-first vs stop-first) ==")
    for fam in sorted(set(r["family"] for r in rows)):
        rs = [r for r in rows if r["family"] == fam]
        t = [r for r in rs if r["which_came_first"] == "target"]; s = [r for r in rs if r["which_came_first"] == "stop"]
        if len(t) < 30 or len(s) < 30:
            continue
        bb = max(((abs(cohend([r[f] for r in t], [r[f] for r in s])), f) for f in FEATS))
        print("  %-32s n=%5d (t=%4d s=%4d)  best |d|=%.4f on %s" % (fam, len(rs), len(t), len(s), bb[0], bb[1]))
        res["per_family_best"][fam] = {"n": len(rs), "target_first": len(t), "stop_first": len(s),
                                       "best_abs_cohen_d": round(bb[0], 4), "feature": bb[1]}
    with open(os.path.join(D, "x2_SEPARATOR_V1.json"), "w") as fh:
        json.dump(res, fh, indent=1)


if __name__ == "__main__":
    main()
