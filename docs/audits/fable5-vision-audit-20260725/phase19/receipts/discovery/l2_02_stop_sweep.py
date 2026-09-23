"""l2 step 2 — stop-distance sweep, done in PRICE, converted to R exactly once.

The stop is moved to `k * risk_distance` in PRICE.  Because every *_r column is normalised by
the ORIGINAL risk_distance d, the new stop is simply `adv <= -k` in the R path, and the trade's
realised R in the NEW risk unit is `R_old / k` (position size scales 1/k to hold cash risk
constant).  Both are reported:
    mean_r_newunit  = fixed CASH RISK per trade (the correct comparable)
    mean_r_oldunit  = fixed POSITION SIZE (what the raw path books)

Two target conventions:
    A  FIXED PRICE target      fav >= policy_target_r          (the structural target stays put)
    B  PROPORTIONAL target     fav >= 2*k                      (constant 2:1 in the new unit)

Population: FIXED at the k=1 honest set (filled, ex-born_past_stop) so the comparison is
'same trades, different stop'.  A k-native population (each k has its own takeable set, since a
wider stop makes some previously-untakeable orders placeable) is reported separately.
Writes L2_STOP_SWEEP_V1.json + l2_SWEEP_ROWS_V1.jsonl.gz
"""
import sys, os, json, gzip, bisect
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import w0_ws

KS = [0.25, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.9, 1.0, 1.1, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]
OUT = os.path.join(D, "L2_STOP_SWEEP_V1.json")
ROWS_OUT = os.path.join(D, "l2_SWEEP_ROWS_V1.jsonl.gz")


def mean(v):
    v = [x for x in v if x is not None]
    return round(sum(v) / len(v), 6) if v else None


rows = w0_ws.load()
byk = {w0_ws.key(r): r for r in rows}
anch = {}
with gzip.open(os.path.join(D, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz"), "rt") as f:
    for ln in f:
        a = json.loads(ln)
        anch[(a["candidate_id"], a["decision_time_utc"])] = a

out_rows = []
for rp in w0_ws.iter_rpaths():
    k = (rp["candidate_id"], rp["decision_time_utc"])
    r = byk.get(k); a = anch.get(k)
    if r is None:
        continue
    m = a["mkt_r_prev_close"] if a else None
    fav, adv, cls = rp["fav"], rp["adv"], rp["cls"]
    n = len(fav)
    tgt = rp.get("policy_target_r") or 2.0
    fb = next((i for i in range(n) if adv[i] <= 0.0), None)
    rec = {"cid": rp["candidate_id"], "dt": rp["decision_time_utc"], "sym": r["symbol"],
           "fam": r.get("origin_family"), "sess": r.get("session_bucket"), "m": m, "tgt": tgt,
           "fb": fb, "n": n, "cost": r.get("expected_cost_r") or 0.0,
           "rdpct": (r["risk_distance"] / r["entry_price"] * 100.0) if r.get("entry_price") else None}
    if fb is None:
        rec["A"] = None; rec["B"] = None
        out_rows.append(rec); continue
    # monotone breakpoint ladders from the fill bar
    minv = []; mini = []; cur = 1e18
    maxv = []; maxi = []; curx = -1e18
    for i in range(fb, n):
        if adv[i] < cur:
            cur = adv[i]; minv.append(cur); mini.append(i)
        if fav[i] > curx:
            curx = fav[i]; maxv.append(curx); maxi.append(i)
    negmin = [-v for v in minv]                     # increasing
    endc = cls[n - 1]

    def first_stop(kk):
        j = bisect.bisect_left(negmin, kk - 1e-12)
        return mini[j] if j < len(mini) else None

    def first_tgt(t):
        j = bisect.bisect_left(maxv, t - 1e-12)
        return maxi[j] if j < len(maxi) else None

    bt_fixed = first_tgt(tgt)
    A = []; B = []
    for kk in KS:
        bs = first_stop(kk)
        # ---- convention A : fixed price target
        if bs is not None and (bt_fixed is None or bs <= bt_fixed):
            ro, ex = -kk, "stop"
        elif bt_fixed is not None:
            ro, ex = tgt, "target"
        else:
            ro, ex = endc, "mark"
        A.append([round(ro / kk, 6), ex])
        # ---- convention B : proportional 2:1 target
        bt2 = first_tgt(2.0 * kk)
        if bs is not None and (bt2 is None or bs <= bt2):
            ro2, ex2 = -kk, "stop"
        elif bt2 is not None:
            ro2, ex2 = 2.0 * kk, "target"
        else:
            ro2, ex2 = endc, "mark"
        B.append([round(ro2 / kk, 6), ex2])
    rec["A"] = A; rec["B"] = B
    out_rows.append(rec)

with gzip.open(ROWS_OUT, "wt") as fh:
    for e in out_rows:
        fh.write(json.dumps(e, separators=(",", ":")) + "\n")

BASE_I = KS.index(1.0)
FIXED = [e for e in out_rows if e["A"] is not None and not (e["m"] is not None and e["m"] <= -1.0)]

res = {"ks": KS, "n_fixed_population": len(FIXED),
       "population_note": "filled AND ex-born_past_stop at k=1; identical rows at every k",
       "unit_note": "mean_r_newunit = R_old/k (constant cash risk); mean_r_oldunit = raw path R (constant position size)"}


def sweep(pop, conv):
    tab = []
    base = [e[conv][BASE_I][0] for e in pop]
    for ix, kk in enumerate(KS):
        rr = [e[conv][ix][0] for e in pop]
        ex = [e[conv][ix][1] for e in pop]
        nw = sum(1 for x in rr if x > 0)
        conv_lw = sum(1 for j in range(len(rr)) if base[j] <= 0 and rr[j] > 0)
        conv_wl = sum(1 for j in range(len(rr)) if base[j] > 0 and rr[j] <= 0)
        wins = [x for x in rr if x > 0]; loss = [x for x in rr if x <= 0]
        tab.append({"k": kk, "n": len(rr),
                    "mean_r_newunit": mean(rr),
                    "mean_r_oldunit": round(mean(rr) * kk, 6),
                    "win_pct": round(100 * nw / len(rr), 3),
                    "stop_pct": round(100 * ex.count("stop") / len(rr), 3),
                    "target_pct": round(100 * ex.count("target") / len(rr), 3),
                    "mark_pct": round(100 * ex.count("mark") / len(rr), 3),
                    "mean_winner": mean(wins), "mean_loser": mean(loss),
                    "payoff": round(abs(mean(wins) / mean(loss)), 4) if loss and mean(loss) else None,
                    "converted_loser_to_winner": conv_lw,
                    "converted_winner_to_loser": conv_wl,
                    "delta_vs_k1_newunit": round(mean(rr) - mean(base), 6)})
    return tab


res["A_fixed_price_target"] = sweep(FIXED, "A")
res["B_proportional_2to1_target"] = sweep(FIXED, "B")

# ---- k-native population: a wider stop makes some untakeable orders placeable ----
nat = []
for ix, kk in enumerate(KS):
    pop = [e for e in out_rows if e["A"] is not None and not (e["m"] is not None and e["m"] <= -kk)]
    rr = [e["A"][ix][0] for e in pop]
    nat.append({"k": kk, "n_takeable": len(pop),
                "n_extra_vs_k1": len(pop) - len(FIXED),
                "mean_r_newunit": mean(rr),
                "win_pct": round(100 * sum(1 for x in rr if x > 0) / len(rr), 3),
                "total_r_newunit": round(sum(rr), 2)})
res["A_k_native_population"] = nat

with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1)
print("wrote", OUT, "n_fixed", len(FIXED))
for t in res["A_fixed_price_target"]:
    print("A k=%.2f mean_new=%+.5f old=%+.5f win=%6.3f stop=%6.2f tgt=%6.2f mark=%6.2f L>W=%5d W>L=%5d"
          % (t["k"], t["mean_r_newunit"], t["mean_r_oldunit"], t["win_pct"], t["stop_pct"],
             t["target_pct"], t["mark_pct"], t["converted_loser_to_winner"], t["converted_winner_to_loser"]))
for t in res["B_proportional_2to1_target"]:
    print("B k=%.2f mean_new=%+.5f win=%6.3f stop=%6.2f tgt=%6.2f mark=%6.2f"
          % (t["k"], t["mean_r_newunit"], t["win_pct"], t["stop_pct"], t["target_pct"], t["mark_pct"]))
