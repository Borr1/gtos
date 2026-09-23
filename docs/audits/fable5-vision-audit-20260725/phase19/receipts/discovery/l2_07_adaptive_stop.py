"""l2 step 7 — THE RULE.  A per-row stop floor, priced.

Three rules, each a per-row multiple k_i of the structural risk distance, applied in PRICE and
converted to R exactly once (R_new = R_old / k_i, cost_new = (spread_r+comm+swap)/k_i + slip):

  RULE S(c)   spread floor : k_i = max(1, c * spread_r)          "never risk less than c spreads"
  RULE A(c)   ATR floor    : k_i = max(1, c * ATR60/risk_dist)   "never risk less than c ATR60"
  RULE G      the incumbent: refuse if spread_r>0.10 or total_cost_r>0.15, stop untouched

Because spread_r is the FROZEN spread and it is measured 7.3-8.5x over-charged, every rule is
priced at three cost regimes.  The floor itself is also computed on the CORRECTED spread
(rule S73) so the repair is not driven by the known error.
Writes L2_ADAPTIVE_STOP_V1.json
"""
import sys, os, json, gzip, bisect
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import w0_ws

OUT = os.path.join(D, "L2_ADAPTIVE_STOP_V1.json")


def mean(v):
    v = [x for x in v if x is not None]
    return round(sum(v) / len(v), 6) if v else None


rows = w0_ws.load(); byk = {w0_ws.key(r): r for r in rows}
anch = {}
with gzip.open(os.path.join(D, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz"), "rt") as f:
    for ln in f:
        a = json.loads(ln); anch[(a["candidate_id"], a["decision_time_utc"])] = a
atr = {}
with gzip.open(os.path.join(D, "l2_ATR_V1.jsonl.gz"), "rt") as f:
    for ln in f:
        a = json.loads(ln); atr[(a["cid"], a["dt"])] = a

# ---- ladders, so any k can be evaluated in O(log n) ----
P = []
for rp in w0_ws.iter_rpaths():
    k = (rp["candidate_id"], rp["decision_time_utc"])
    r = byk.get(k)
    if r is None:
        continue
    a = anch.get(k); av = atr.get(k, {})
    fav, adv, cls = rp["fav"], rp["adv"], rp["cls"]
    n = len(fav)
    tgt = rp.get("policy_target_r") or 2.0
    fb = next((i for i in range(n) if adv[i] <= 0.0), None)
    e = {"fam": r.get("origin_family"), "sym": r["symbol"], "sess": r.get("session_bucket"),
         "m": (a["mkt_r_prev_close"] if a else None), "tgt": tgt,
         "sp": r.get("spread_r") or 0.0, "cm": r.get("commission_r") or 0.0,
         "sww": r.get("swap_cost_r") or 0.0, "sl": r.get("expected_slippage_r") or 0.0,
         "atrr": ((av["atr60"] / r["risk_distance"]) if av.get("atr60") else None),
         "fb": fb, "cid": rp["candidate_id"], "dt": rp["decision_time_utc"]}
    if fb is None:
        e["lad"] = None; P.append(e); continue
    minv = []; mini = []; cur = 1e18
    maxv = []; maxi = []; curx = -1e18
    for i in range(fb, n):
        if adv[i] < cur:
            cur = adv[i]; minv.append(-cur); mini.append(i)
        if fav[i] > curx:
            curx = fav[i]; maxv.append(curx); maxi.append(i)
    e["lad"] = (minv, mini, maxv, maxi, cls[n - 1])
    P.append(e)


def walk_k(e, kk):
    """R in the ORIGINAL unit at stop multiple kk (fixed structural price target)."""
    minv, mini, maxv, maxi, endc = e["lad"]
    j = bisect.bisect_left(minv, kk - 1e-12)
    bs = mini[j] if j < len(mini) else None
    j2 = bisect.bisect_left(maxv, e["tgt"] - 1e-12)
    bt = maxi[j2] if j2 < len(maxi) else None
    if bs is not None and (bt is None or bs <= bt):
        return -kk, "stop"
    if bt is not None:
        return e["tgt"], "target"
    return endc, "mark"


def evaluate(kf, label, pop, spread_div=1.0, res_extra=None):
    """kf(e)->k_i ; returns the priced block."""
    out = {"rule": label, "n": len(pop)}
    ks = []; gr = []; net_f = []; net_73 = []; net_85 = []; ex = []
    for e in pop:
        kk = kf(e)
        if kk is None or kk < 1e-9:
            continue
        ro, x = walk_k(e, kk)
        ks.append(kk); gr.append(ro / kk); ex.append(x)
        cp = e["sp"] + e["cm"] + e["sww"]
        cp73 = e["sp"] / 7.3 + e["cm"] + e["sww"]
        cp85 = e["sp"] / 8.5 + e["cm"] + e["sww"]
        net_f.append(ro / kk - (cp / kk + e["sl"]))
        net_73.append(ro / kk - (cp73 / kk + e["sl"]))
        net_85.append(ro / kk - (cp85 / kk + e["sl"]))
    if not ks:
        out["n_eval"] = 0
        return out
    out.update({"n_eval": len(ks), "k_mean": mean(ks), "k_median": round(sorted(ks)[len(ks) // 2], 4),
                "k_p90": round(sorted(ks)[int(0.9 * (len(ks) - 1))], 4),
                "k_max": round(max(ks), 3),
                "share_k_gt_1_pct": round(100 * sum(1 for x in ks if x > 1.000001) / len(ks), 3),
                "gross_newunit": mean(gr), "gross_oldunit_equiv": round((mean(gr) or 0) * (sum(ks) / len(ks)), 6),
                "win_pct": round(100 * sum(1 for x in gr if x > 0) / len(gr), 3),
                "stop_pct": round(100 * ex.count("stop") / len(ex), 3),
                "target_pct": round(100 * ex.count("target") / len(ex), 3),
                "mark_pct": round(100 * ex.count("mark") / len(ex), 3),
                "net_frozen": mean(net_f), "net_sp73": mean(net_73), "net_sp85": mean(net_85),
                "total_net_frozen_R": round(sum(net_f), 1), "total_net_sp73_R": round(sum(net_73), 1)})
    if res_extra:
        out.update(res_extra)
    return out


POP = [e for e in P if e["lad"] is not None and not (e["m"] is not None and e["m"] <= -1.0)]
res = {"n_honest_population": len(POP),
       "population": "filled AND ex-born_past_stop (stop already breached at the decision instant)",
       "convention": "structural price target held fixed; stop moved in price; R converted once"}

res["baseline_k1"] = evaluate(lambda e: 1.0, "BASELINE k=1 (as shipped)", POP)
for c in (1, 2, 3, 5, 8, 10, 15, 20):
    res["S_frozen_c%d" % c] = evaluate(lambda e, c=c: max(1.0, c * e["sp"]), "S(%d) spread floor, FROZEN spread" % c, POP)
for c in (1, 2, 3, 5, 8, 10, 15, 20):
    res["S_true73_c%d" % c] = evaluate(lambda e, c=c: max(1.0, c * e["sp"] / 7.3),
                                       "S(%d) spread floor on the CORRECTED spread (/7.3)" % c, POP)
for c in (0.5, 1, 2, 3, 5):
    res["A_atr_c%s" % c] = evaluate(lambda e, c=c: (max(1.0, c / e["atrr"]) if e["atrr"] else None),
                                    "A(%s) ATR60 floor" % c, POP)

# ---- the incumbent gate, stop untouched ----
for lab, dv in (("frozen", 1.0), ("sp73", 7.3)):
    keep = [e for e in POP if (e["sp"] / dv) <= 0.10 and (e["sp"] / dv + e["cm"] + e["sww"] + e["sl"]) <= 0.15]
    res["G_incumbent_gate_" + lab] = evaluate(lambda e: 1.0, "G incumbent cost gate (%s), stop untouched" % lab, keep,
                                              res_extra={"pass_pct_of_pop": round(100 * len(keep) / len(POP), 3)})

# ---- combination: spread floor THEN gate ----
for c in (5, 10):
    for lab, dv in (("frozen", 1.0), ("sp73", 7.3)):
        keep = []
        for e in POP:
            kk = max(1.0, c * (e["sp"] / dv))
            if (e["sp"] / dv) / kk <= 0.10 and ((e["sp"] / dv + e["cm"] + e["sww"]) / kk + e["sl"]) <= 0.15:
                keep.append(e)
        res["SG_c%d_%s" % (c, lab)] = evaluate(lambda e, c=c, dv=dv: max(1.0, c * (e["sp"] / dv)),
                                               "S(%d)/%s then incumbent gate" % (c, lab), keep,
                                               res_extra={"pass_pct_of_pop": round(100 * len(keep) / len(POP), 3)})

# ---- per family, best rule S(10) vs baseline ----
fam = {}
for f in sorted({e["fam"] for e in POP if e["fam"]}):
    sub = [e for e in POP if e["fam"] == f]
    b = evaluate(lambda e: 1.0, "base", sub)
    s = evaluate(lambda e: max(1.0, 10 * e["sp"]), "S10", sub)
    fam[f] = {"n": len(sub), "base_net_frozen": b["net_frozen"], "S10_net_frozen": s["net_frozen"],
              "delta_net_frozen": round((s["net_frozen"] or 0) - (b["net_frozen"] or 0), 6),
              "base_net_sp73": b["net_sp73"], "S10_net_sp73": s["net_sp73"],
              "delta_net_sp73": round((s["net_sp73"] or 0) - (b["net_sp73"] or 0), 6),
              "base_gross_new": b["gross_newunit"], "S10_gross_new": s["gross_newunit"],
              "k_median": s["k_median"], "share_k_gt_1_pct": s["share_k_gt_1_pct"]}
res["per_family_S10_vs_base"] = fam

with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1)
print("wrote", OUT, "n", len(POP))
hdr = "%-42s %6s %7s %7s %8s %9s %9s %9s"
print(hdr % ("rule", "n", "kmed", "k>1%", "gross", "netFROZEN", "net/7.3", "net/8.5"))
for k in ("baseline_k1", "S_frozen_c1", "S_frozen_c2", "S_frozen_c3", "S_frozen_c5", "S_frozen_c8",
          "S_frozen_c10", "S_frozen_c15", "S_frozen_c20", "S_true73_c1", "S_true73_c2", "S_true73_c3",
          "S_true73_c5", "S_true73_c10", "A_atr_c0.5", "A_atr_c1", "A_atr_c2", "A_atr_c3", "A_atr_c5",
          "G_incumbent_gate_frozen", "G_incumbent_gate_sp73", "SG_c5_frozen", "SG_c10_frozen",
          "SG_c5_sp73", "SG_c10_sp73"):
    b = res.get(k)
    if not b or not b.get("n_eval"):
        continue
    print(hdr % (b["rule"][:42], b["n_eval"], "%.3f" % b["k_median"], "%.1f" % b["share_k_gt_1_pct"],
                 "%+.5f" % b["gross_newunit"], "%+.5f" % b["net_frozen"], "%+.5f" % b["net_sp73"],
                 "%+.5f" % b["net_sp85"]))
