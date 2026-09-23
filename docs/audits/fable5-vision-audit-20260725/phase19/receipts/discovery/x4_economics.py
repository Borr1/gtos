#!/usr/bin/env python3
"""x4 step 2 — is the intra-bar signal ECONOMIC, and does it survive symbol composition?

(1) Within-symbol standardisation: re-run the effect sizes on z-scores computed inside each
    symbol, so nothing can ride on which symbols happen to win.
(2) Decile tables in R/trade on the two populations that matter.
(3) Split-half by calendar (days 1-15 vs 16-31) and odd/even day, both directions.
(4) Per-symbol and per-family sign consistency of the leading features.
"""
import collections, json, math, os, statistics as st, sys
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import x4_lib as X

rows = X.load_joined()
XC = X.xcols(rows)
take = [r for r in rows if r["takeable"]]
bar1 = [r for r in take if r.get("bars_to_entry_touch") == 1]

OUTC = {
    "bar1": (bar1, "fill_honest_walk_r"),
    "takeable": (take, "gross_r"),
}


def zsym(pop, col):
    """within-symbol z-score of col; returns dict id(row)->z"""
    by = collections.defaultdict(list)
    for r in pop:
        if X._num(r.get(col)):
            by[r["symbol"]].append(r[col])
    stats = {}
    for s, v in by.items():
        if len(v) < 20:
            continue
        m = st.mean(v); sd = st.pstdev(v)
        stats[s] = (m, sd if sd > 0 else None)
    out = {}
    for r in pop:
        if not X._num(r.get(col)):
            continue
        s = stats.get(r["symbol"])
        if not s or s[1] is None:
            continue
        out[id(r)] = (r[col] - s[0]) / s[1]
    return out


res = {}

# ---------------- (1) within-symbol effect sizes -----------------------------
for pname, (pop, ycol) in OUTC.items():
    if pname == "bar1":
        pos = [r for r in pop if r.get("fill_honest_which_came_first") == "target"]
        neg = [r for r in pop if r.get("fill_honest_which_came_first") == "stop"]
    else:
        pos = [r for r in pop if r["outcome_band"] == "ge_target"]
        neg = [r for r in pop if r["outcome_band"] == "full_stop"]
    rank = []
    for c in XC:
        z = zsym(pop, c)
        a = [z[id(r)] for r in pos if id(r) in z]
        b = [z[id(r)] for r in neg if id(r) in z]
        d = X.cohend(a, b)
        if d is None:
            continue
        # continuous: spearman of the within-symbol z against realised R
        vv = [(z[id(r)], r[ycol]) for r in pop if id(r) in z and X._num(r.get(ycol))]
        sp = X.spearman([v[0] for v in vv], [v[1] for v in vv]) if len(vv) > 200 else None
        t = X.welch_t(a, b)
        rank.append({"feature": c, "d_within_symbol": round(d, 4),
                     "auc": round(X.auc(a, b), 4), "n_pos": len(a), "n_neg": len(b),
                     "spearman_z_vs_R": round(sp, 4) if sp else None,
                     "welch_t": round(t, 3) if t else None,
                     "p": X.two_sided_p_from_t(t),
                     "known_axis": c.replace("x4_", "") in X.KNOWN_AXIS})
    rank.sort(key=lambda r: -abs(r["d_within_symbol"]))
    res[f"within_symbol_{pname}"] = rank

# ---------------- (2) economic deciles ---------------------------------------
TOP = [r["feature"] for r in res["within_symbol_bar1"][:14]]
dec = {}
for pname, (pop, ycol) in OUTC.items():
    for c in TOP:
        z = zsym(pop, c)
        v = sorted(((z[id(r)], r) for r in pop if id(r) in z and X._num(r.get(ycol))),
                   key=lambda x: x[0])
        n = len(v)
        tab = []
        for i in range(10):
            a, b = n * i // 10, n * (i + 1) // 10
            ch = v[a:b]
            ys = [r[ycol] for _, r in ch]
            wr = sum(1 for _, r in ch if (r.get("fill_honest_which_came_first") == "target"
                                          if pname == "bar1" else r["outcome_band"] == "ge_target"))
            tab.append({"dec": i + 1, "n": len(ch), "z_lo": round(ch[0][0], 3),
                        "z_hi": round(ch[-1][0], 3), "meanR": round(X.mean(ys), 5),
                        "win%": round(100.0 * wr / len(ch), 2)})
        dec[f"{pname}::{c}"] = tab
res["deciles"] = dec

# ---------------- (3) split-half stability ------------------------------------
def half(r, mode):
    dd = int(r["day"][8:10])
    return (dd <= 15) if mode == "calendar" else (dd % 2 == 1)


sh = {}
for mode in ("calendar", "oddeven"):
    for pname, (pop, ycol) in OUTC.items():
        A = [r for r in pop if half(r, mode)]
        B = [r for r in pop if not half(r, mode)]
        rec = {}
        for c in TOP:
            row = {}
            for tag, sub in (("A", A), ("B", B)):
                z = zsym(sub, c)
                vv = [(z[id(r)], r[ycol]) for r in sub if id(r) in z and X._num(r.get(ycol))]
                if len(vv) < 200:
                    row[tag] = None; continue
                sp = X.spearman([v[0] for v in vv], [v[1] for v in vv])
                # top-vs-bottom tercile R gap
                vv.sort(key=lambda x: x[0]); m = len(vv)
                lo = X.mean([y for _, y in vv[:m // 3]])
                hi = X.mean([y for _, y in vv[-(m // 3):]])
                row[tag] = {"n": m, "spearman": round(sp, 4),
                            "R_bottom_tercile": round(lo, 5), "R_top_tercile": round(hi, 5),
                            "gap": round(hi - lo, 5)}
            if row.get("A") and row.get("B"):
                row["sign_agree_spearman"] = (row["A"]["spearman"] * row["B"]["spearman"]) > 0
                row["sign_agree_gap"] = (row["A"]["gap"] * row["B"]["gap"]) > 0
            rec[c] = row
        sh[f"{mode}::{pname}"] = rec
res["split_half"] = sh

# ---------------- (4) per-symbol / per-family sign consistency -----------------
cons = {}
for c in TOP:
    for pname, (pop, ycol) in (("bar1", (bar1, "fill_honest_walk_r")),):
        agree_s = tot_s = 0; detail = {}
        by = collections.defaultdict(list)
        for r in pop:
            by[r["symbol"]].append(r)
        # global direction from the whole population
        z = zsym(pop, c)
        vv = [(z[id(r)], r[ycol]) for r in pop if id(r) in z and X._num(r.get(ycol))]
        gs = X.spearman([v[0] for v in vv], [v[1] for v in vv])
        for s, sub in sorted(by.items()):
            if len(sub) < 120:
                continue
            v2 = sorted(((r[c], r[ycol]) for r in sub
                         if X._num(r.get(c)) and X._num(r.get(ycol))), key=lambda x: x[0])
            if len(v2) < 120:
                continue
            m = len(v2)
            lo = X.mean([y for _, y in v2[:m // 3]]); hi = X.mean([y for _, y in v2[-(m // 3):]])
            tot_s += 1
            ok = ((hi - lo) > 0) == (gs > 0)
            agree_s += 1 if ok else 0
            detail[s] = {"n": m, "gap": round(hi - lo, 4), "agrees": ok}
        cons[c] = {"global_spearman": round(gs, 4), "symbols_tested": tot_s,
                   "symbols_agreeing": agree_s, "per_symbol": detail}
res["per_symbol_consistency_bar1"] = cons

json.dump(res, open(os.path.join(D, "x4_ECONOMICS_V1.json"), "w"), indent=1)

print("=== within-symbol d, BAR-1 cohort (continues vs reverts) — top 16 ===")
for r in res["within_symbol_bar1"][:16]:
    print(f"  {r['feature']:34s} d={r['d_within_symbol']:+.4f} auc={r['auc']} "
          f"sp={r['spearman_z_vs_R']} p={r['p']:.2e} known={r['known_axis']}")
print("\n=== within-symbol d, TAKEABLE (ge_target vs full_stop) — top 12 ===")
for r in res["within_symbol_takeable"][:12]:
    print(f"  {r['feature']:34s} d={r['d_within_symbol']:+.4f} auc={r['auc']} "
          f"sp={r['spearman_z_vs_R']} p={r['p']:.2e} known={r['known_axis']}")
print("\nwrote x4_ECONOMICS_V1.json")
