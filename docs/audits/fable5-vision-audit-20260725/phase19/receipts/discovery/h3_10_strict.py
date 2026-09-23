"""h3-10 -- the passive lever under BOTH quote conventions, and robustness on the top cells.

WHY THIS EXISTS. h3-04 modelled a resting limit as "fills when the path touches the decision
price, saves half the quoted spread". That is the MID convention. MT5 bar exports are BID
series, and under a bid series the arithmetic is different and it matters:

  MID  path is the mid. Market in = half spread, market out = half spread (total one
       spread). A limit at E fills when mid touches E and saves the entry half.
  BID  path is the bid. For a LONG you buy the ASK and sell the BID, so the whole spread is
       charged against a bid-measured path at entry and nothing at exit. A limit at E fills
       only when ASK <= E, i.e. when the bid has fallen a FULL spread below E -- and it then
       costs no spread at all.

Both agree exactly on the at-market round trip (one full spread). They disagree on the
passive arm in opposite directions: BID is stricter on the fill and more generous on the
saving. Measuring both brackets the truth, which is the honest thing to do when the quote
side of an archived bar series is not itself recorded.

Also here: the top cells re-scored under the hour-aware toll, a January-train / Feb+Mar-test
read, and a 2,000-resample day-block bootstrap on each.
"""
import bisect
import gzip
import json
import os
import random
import sys
import time
from datetime import datetime, timedelta

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import e_lib          # noqa: E402
import e_build_month as bm  # noqa: E402
import h3_lib as H    # noqa: E402

C = "TRAIL025"
MON = {"2026-01": "202601", "2026-02": "202602", "2026-03": "202603"}
OUTF = os.path.join(D, "H3_STRICT_ROWS_V1.jsonl.gz")


def build():
    t0 = time.time()
    out = gzip.open(OUTF, "wt")
    nw = 0
    for month in sorted(MON):
        rows = H.load_atmkt([month])
        cache = {}
        for s in sorted({r["symbol"] for r in rows}):
            b = bm.load_bars(MON[month], s)
            if b is not None:
                cache[s] = b
        for r in rows:
            b = cache.get(r["symbol"])
            if b is None:
                continue
            dt = r["dt"]
            i = bisect.bisect_right(b["t"], dt) - 1
            if i < 1:
                continue
            entry, d = r["entry_price"], r["risk_distance"]
            sgn = 1.0 if r["side"] == "LONG" else -1.0
            rr = lambda px: sgn * (px - entry) / d          # noqa: E731
            end = (datetime.fromisoformat(dt) + timedelta(minutes=120)).isoformat()
            fav, adv, cls = [], [], []
            for kx in range(i + 1, min(i + 126, len(b["t"]))):
                if b["t"][kx] <= dt:
                    continue
                if b["t"][kx] > end:
                    break
                hi, lo = rr(b["h"][kx]), rr(b["l"][kx])
                fav.append(max(hi, lo)); adv.append(min(hi, lo)); cls.append(rr(b["c"][kx]))
                if len(fav) >= 120:
                    break
            if len(fav) < 5:
                continue
            s_r = r["real_spread_r"]
            o = {k: r[k] for k in ("cid", "dt", "day", "month", "symbol", "side", "family",
                                   "ny_hour", "utc_hour", "rdp", "risk_distance",
                                   "entry_price", "real_spread_r", "real_comm_r",
                                   "real_slip_r", "cost_true")}
            tg, st, trl, mb, _ = e_lib.CONTRACTS[C]
            # BID convention: limit at E fills when the ASK reaches E <=> bid <= E - spread
            js = next((k for k in range(len(adv)) if adv[k] <= -s_r + 1e-12), None)
            o["j_strict"] = js
            if js is not None:
                rv, rn, eb = e_lib.walk(fav, adv, cls, js, tg, st, trl, mb)
                o["strict_r"] = round(rv, 8); o["strict_x"] = rn; o["strict_b"] = eb
            else:
                o["strict_r"] = None
            # MID convention already measured in h3-02; carried here for one-file scoring
            jm = next((k for k in range(len(adv)) if adv[k] <= 1e-12), None)
            o["j_mid"] = jm
            if jm is not None:
                rv, rn, eb = e_lib.walk(fav, adv, cls, jm, tg, st, trl, mb)
                o["mid_r"] = round(rv, 8)
            else:
                o["mid_r"] = None
            for k in (5, 20):
                o[f"K{k}_{C}"] = r.get(f"K{k}_{C}")
            out.write(json.dumps(o) + "\n"); nw += 1
    out.close()
    return {"written": nw, "seconds": round(time.time() - t0, 1)}


if not os.path.isfile(OUTF) or os.environ.get("H3_REBUILD"):
    print(json.dumps(build()), flush=True)

rows = [json.loads(x) for x in gzip.open(OUTF, "rt") if x.strip()]
H.add_hour_cost(rows)
N = len(rows)
out = {"lane": "h3", "step": "strict_and_robust", "n": N, "contract": C}

TOLL_MKT = lambda r: r["cost_true"]                                            # noqa: E731
TOLL_MKT_H = lambda r: r["cost_true_hour"]                                     # noqa: E731
TOLL_MID = lambda r: 0.5 * r["real_spread_r"] + r["real_comm_r"]               # noqa: E731
TOLL_BID = lambda r: r["real_comm_r"]                                          # noqa: E731

sy = {}
for r in rows:
    sy.setdefault(r["symbol"], []).append(r)
symcost = sorted(sy, key=lambda s: H.mean([x["cost_true"] * x["rdp"] * 1e4 for x in sy[s]]))
CH2, CH6, CH12 = set(symcost[:2]), set(symcost[:6]), set(symcost[:12])


def boot(days, vals_by_day, B=2000, seed=17):
    rnd = random.Random(seed)
    ks = list(days)
    ms = []
    for _ in range(B):
        s = [rnd.choice(ks) for _ in ks]
        tot, cnt = 0.0, 0
        for d in s:
            v = vals_by_day[d]
            tot += sum(v); cnt += len(v)
        if cnt:
            ms.append(tot / cnt)
    ms.sort()
    return {"lo95": ms[int(0.025 * len(ms))], "hi95": ms[int(0.975 * len(ms))],
            "p_le_0": sum(1 for x in ms if x <= 0) / len(ms)}


def arm(sel, valf, tollf, label, extra=None, do_boot=True):
    g, t, n, keep = [], [], [], []
    for r in rows:
        if not sel(r):
            continue
        v = valf(r)
        tv = tollf(r)
        if v is None or tv is None:
            continue
        gb = v * r["rdp"] * 1e4
        tb = tv * r["rdp"] * 1e4
        g.append(gb); t.append(tb); n.append(gb - tb); keep.append(r)
    if len(g) < 10:
        return None
    d = {"label": label, "n": len(g), "keep_rate": len(g) / N,
         "edge_bps": H.mean(g), "toll_bps": H.mean(t), "net_bps": H.mean(n),
         "edge_over_toll": H.mean(g) / H.mean(t) if H.mean(t) else None,
         "net_bps_per_opportunity": H.mean(n) * len(g) / N,
         "net_r": H.mean([valf(r) - tollf(r) for r in keep]),
         "t_net_trade": H.tstat(n), "t_gross_trade": H.tstat(g)}
    bd = {}
    for r, v in zip(keep, n):
        bd.setdefault(r["day"], []).append(v)
    d["days_traded"] = len(bd)
    dm = [sum(v) / len(v) for v in bd.values()]
    d["days_net_positive"] = sum(1 for x in dm if x > 0)
    d["t_net_daily"] = H.tstat(dm)
    if do_boot:
        d["bootstrap_net_bps"] = boot(list(bd), bd)
    bmn = {}
    for m in sorted(H.MONTHS):
        k2 = [r for r in keep if r["month"] == m]
        if len(k2) >= 20:
            gg = [valf(r) * r["rdp"] * 1e4 for r in k2]
            tt = [tollf(r) * r["rdp"] * 1e4 for r in k2]
            bmn[m] = {"n": len(k2), "edge_bps": H.mean(gg), "toll_bps": H.mean(tt),
                      "net_bps": H.mean(gg) - H.mean(tt),
                      "edge_over_toll": H.mean(gg) / H.mean(tt) if H.mean(tt) else None}
    d["by_month"] = bmn
    d["months_e_over_t_ge_1"] = sum(1 for v in bmn.values()
                                    if v["edge_over_toll"] and v["edge_over_toll"] >= 1)
    d["months_measured"] = len(bmn)
    if extra:
        d.update(extra)
    return d


# -------------------------------------------------- 1. the two passive conventions
conv = []
conv.append(arm(lambda r: True, lambda r: r["K5_" + C], TOLL_MKT, "at-market baseline"))
conv.append(arm(lambda r: r["mid_r"] is not None, lambda r: r["mid_r"], TOLL_MID,
                "MID convention: limit at E, fill on touch, saves half spread"))
conv.append(arm(lambda r: r["strict_r"] is not None, lambda r: r["strict_r"], TOLL_BID,
                "BID convention: limit at E, fill when ask<=E, saves the whole spread"))
for c in (5, 10, 15, 20):
    conv.append(arm(lambda r, c=c: r["j_mid"] is not None and r["j_mid"] >= c,
                    lambda r: r["mid_r"], TOLL_MID,
                    f"MID + no-retrace >= {c} min", extra={"cond_min": c}))
    conv.append(arm(lambda r, c=c: r["j_strict"] is not None and r["j_strict"] >= c,
                    lambda r: r["strict_r"], TOLL_BID,
                    f"BID + no-retrace >= {c} min", extra={"cond_min": c}))
out["passive_conventions"] = conv
out["fill_rates"] = {
    "mid_fill_rate": sum(1 for r in rows if r["j_mid"] is not None) / N,
    "bid_fill_rate": sum(1 for r in rows if r["j_strict"] is not None) / N,
    "mean_spread_r": H.mean([r["real_spread_r"] for r in rows]),
    "median_mid_fill_bar": H.q([r["j_mid"] for r in rows if r["j_mid"] is not None], 0.5),
    "median_bid_fill_bar": H.q([r["j_strict"] for r in rows if r["j_strict"] is not None], 0.5)}

# -------------------------------------------------- 2. top cells, both cost bases
cells = []
SPEC = [
    ("CHEAP2 at-market k5", lambda r: r["symbol"] in CH2, lambda r: r["K5_" + C]),
    ("CHEAP6 at-market k5", lambda r: r["symbol"] in CH6, lambda r: r["K5_" + C]),
    ("CHEAP12 at-market k5", lambda r: r["symbol"] in CH12, lambda r: r["K5_" + C]),
    ("ALL at-market k5 (baseline)", lambda r: True, lambda r: r["K5_" + C]),
    ("NO-RETRACE>=10 market-on-touch, ALL",
     lambda r: r["j_mid"] is not None and r["j_mid"] >= 10, lambda r: r["mid_r"]),
    ("NO-RETRACE>=10 market-on-touch, CHEAP6",
     lambda r: r["j_mid"] is not None and r["j_mid"] >= 10 and r["symbol"] in CH6,
     lambda r: r["mid_r"]),
    ("NY13 at-market k5", lambda r: r["ny_hour"] == 13, lambda r: r["K5_" + C]),
    ("regime_transition_break at-market k5",
     lambda r: r.get("family") == "regime_transition_break", lambda r: r["K5_" + C]),
    ("GER40 at-market k5", lambda r: r["symbol"] == "GER40", lambda r: r["K5_" + C]),
]
for lab, sel, vf in SPEC:
    for tk, tf in (("flat_cost", TOLL_MKT), ("hour_aware_cost", TOLL_MKT_H)):
        d = arm(sel, vf, tf, f"{lab} [{tk}]", extra={"cost_basis": tk, "cell": lab})
        if d:
            cells.append(d)
out["top_cells_both_cost_bases"] = cells

# -------------------------------------------------- 3. train Jan / test Feb+Mar
jan = [r for r in rows if r["month"] == "2026-01"]
sy_j = {}
for r in jan:
    sy_j.setdefault(r["symbol"], []).append(r)
order_j = sorted(sy_j, key=lambda s: H.mean([x["cost_true"] * x["rdp"] * 1e4 for x in sy_j[s]]))
tt = []
for k in (2, 3, 6, 12, 24):
    ks = set(order_j[:k])
    for lab, mm in (("TRAIN Jan", ["2026-01"]), ("TEST FebMar", ["2026-02", "2026-03"])):
        sub = [r for r in rows if r["month"] in mm and r["symbol"] in ks]
        g = [r["K5_" + C] * r["rdp"] * 1e4 for r in sub if r.get("K5_" + C) is not None]
        t = [r["cost_true"] * r["rdp"] * 1e4 for r in sub if r.get("K5_" + C) is not None]
        tt.append({"k": k, "split": lab, "kept": order_j[:k], "n": len(g),
                   "edge_bps": H.mean(g), "toll_bps": H.mean(t),
                   "net_bps": H.mean(g) - H.mean(t),
                   "edge_over_toll": H.mean(g) / H.mean(t)})
out["train_test_instrument_choice"] = tt
out["jan_cost_order"] = order_j
out["pooled_cost_order"] = symcost
out["cost_order_jan_vs_pooled_identical_top6"] = order_j[:6] == symcost[:6]

p = H.dump(out, "H3_STRICT_V1.json")
print("fill rates", json.dumps(out["fill_rates"], indent=1))
print("\n%-56s %6s %6s %8s %8s %8s %7s %5s %s" %
      ("arm", "n", "keep", "edge", "toll", "net", "e/t", "m>=1", "boot95"))
for d in conv:
    b = d.get("bootstrap_net_bps") or {}
    print("%-56s %6d %6.3f %8.4f %8.4f %8.4f %7.3f %2d/%d [%+.3f,%+.3f]" %
          (d["label"][:56], d["n"], d["keep_rate"], d["edge_bps"], d["toll_bps"],
           d["net_bps"], d["edge_over_toll"] or 0, d["months_e_over_t_ge_1"],
           d["months_measured"], b.get("lo95", 0), b.get("hi95", 0)))
print("\nTOP CELLS under both cost bases")
print("%-52s %6s %8s %8s %8s %7s %5s %s" % ("cell", "n", "edge", "toll", "net", "e/t", "m>=1", "boot95"))
for d in cells:
    b = d.get("bootstrap_net_bps") or {}
    print("%-52s %6d %8.4f %8.4f %8.4f %7.3f %2d/%d [%+.3f,%+.3f] p<=0 %.3f" %
          (d["label"][:52], d["n"], d["edge_bps"], d["toll_bps"], d["net_bps"],
           d["edge_over_toll"] or 0, d["months_e_over_t_ge_1"], d["months_measured"],
           b.get("lo95", 0), b.get("hi95", 0), b.get("p_le_0", 0)))
print("\nTRAIN/TEST instrument choice (ranked by January cost only)")
for x in tt:
    print("  k=%2d %-12s n=%6d edge=%8.4f toll=%8.4f net=%8.4f e/t=%6.3f" %
          (x["k"], x["split"], x["n"], x["edge_bps"], x["toll_bps"], x["net_bps"],
           x["edge_over_toll"]))
print("top6 identical jan vs pooled:", out["cost_order_jan_vs_pooled_identical_top6"])
print("->", p)
