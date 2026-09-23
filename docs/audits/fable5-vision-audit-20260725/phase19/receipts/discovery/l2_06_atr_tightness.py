"""l2 step 6 — is the stop too tight, and too tight RELATIVE TO WHAT?

Three structural yardsticks, all knowable at the decision instant:
  (1) the SPREAD          spread_r = spread_price / risk_distance.  spread_r >= 1 means the stop
                          is closer than the spread: the trade is dead on arrival.
  (2) pre-decision ATR60  stop_in_atr60 = risk_distance / ATR60 (no look-ahead, l2_04_atr.py)
  (3) risk distance as %  of price
For each bucket: n, gross price-space expectancy at k=1, the k-curve, net at frozen and /7.3.
Writes L2_TIGHTNESS_V1.json
"""
import sys, os, json, gzip
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import w0_ws

KS = [0.25, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.9, 1.0, 1.1, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]
I1 = KS.index(1.0)
OUT = os.path.join(D, "L2_TIGHTNESS_V1.json")


def mean(v):
    v = [x for x in v if x is not None]
    return round(sum(v) / len(v), 6) if v else None


def med(v):
    v = sorted(x for x in v if x is not None)
    return round(v[len(v) // 2], 6) if v else None


rows = w0_ws.load(); byk = {w0_ws.key(r): r for r in rows}
atr = {}
with gzip.open(os.path.join(D, "l2_ATR_V1.jsonl.gz"), "rt") as f:
    for ln in f:
        a = json.loads(ln); atr[(a["cid"], a["dt"])] = a
recs = {}
with gzip.open(os.path.join(D, "l2_RECS_V1.jsonl.gz"), "rt") as f:
    for ln in f:
        e = json.loads(ln); recs[(e["cid"], e["dt"])] = e

pop = []
allrows = []
with gzip.open(os.path.join(D, "l2_SWEEP_ROWS_V1.jsonl.gz"), "rt") as f:
    for ln in f:
        e = json.loads(ln)
        k = (e["cid"], e["dt"]); r = byk[k]; a = atr.get(k, {}); c = recs.get(k, {})
        d = {"A": e["A"], "fam": e["fam"], "sym": e["sym"], "m": e["m"], "rdpct": e["rdpct"],
             "sp": r.get("spread_r") or 0.0, "cm": r.get("commission_r") or 0.0,
             "sww": r.get("swap_cost_r") or 0.0, "sl": r.get("expected_slippage_r") or 0.0,
             "sia60": a.get("stop_in_atr60"), "sia240": a.get("stop_in_atr240"),
             "spatr": a.get("spread_in_atr60"), "atr60": a.get("atr60"),
             "exit": c.get("exit"), "born": ("past_stop" if (e["m"] is not None and e["m"] <= -1.0) else "ok"),
             "eng": r.get("gross_r"), "cost": r.get("expected_cost_r") or 0.0}
        allrows.append(d)
        if e["A"] is not None and d["born"] == "ok":
            pop.append(d)

res = {"n_pop": len(pop), "n_all": len(allrows)}


def block(v):
    if not v:
        return None
    g1 = [x["A"][I1][0] for x in v]
    c1 = [x["sp"] + x["cm"] + x["sww"] + x["sl"] for x in v]
    c1c = [x["sp"] / 7.3 + x["cm"] + x["sww"] + x["sl"] for x in v]
    kc = {}
    for ix, kk in enumerate(KS):
        if kk in (0.5, 0.75, 1.0, 1.5, 2.0, 3.0):
            kc["k%.2f" % kk] = round((mean([x["A"][ix][0] for x in v]) or 0) * kk, 6)
    return {"n": len(v), "gross_old_k1": mean(g1),
            "kcurve_gross_old": kc,
            "net_frozen_k1": round((mean(g1) or 0) - (mean(c1) or 0), 6),
            "net_sp73_k1": round((mean(g1) or 0) - (mean(c1c) or 0), 6),
            "spread_r_mean": mean([x["sp"] for x in v]), "spread_r_med": med([x["sp"] for x in v]),
            "stop_in_atr60_med": med([x["sia60"] for x in v]),
            "rdpct_med": med([x["rdpct"] for x in v]),
            "stop_pct": round(100 * sum(1 for x in v if x["exit"] == "stop") / len(v), 3),
            "target_pct": round(100 * sum(1 for x in v if x["exit"] == "target") / len(v), 3)}


# ---- (1) the stop inside the spread ----
bands = [(0, 0.05), (0.05, 0.10), (0.10, 0.25), (0.25, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, 5.0), (5.0, 1e9)]
res["spread_r_bands"] = [dict(band="[%s,%s)" % (a, b), **(block([x for x in pop if a <= x["sp"] < b]) or {}))
                         for a, b in bands]
n_dead = sum(1 for x in pop if x["sp"] >= 1.0)
res["stop_inside_the_spread"] = {
    "definition": "spread_r >= 1.0  <=>  quoted spread >= the entire risk distance",
    "n": n_dead, "share_of_honest_pop_pct": round(100 * n_dead / len(pop), 3),
    "gross_old_k1": mean([x["A"][I1][0] for x in pop if x["sp"] >= 1.0]),
    "net_frozen_k1": mean([x["A"][I1][0] - (x["sp"] + x["cm"] + x["sww"] + x["sl"]) for x in pop if x["sp"] >= 1.0]),
    "net_sp73_k1": mean([x["A"][I1][0] - (x["sp"] / 7.3 + x["cm"] + x["sww"] + x["sl"]) for x in pop if x["sp"] >= 1.0]),
    "contribution_to_pool_gross_r": round(sum(x["A"][I1][0] for x in pop if x["sp"] >= 1.0) / len(pop), 6),
    "contribution_to_pool_net_frozen_r": round(sum(x["A"][I1][0] - (x["sp"] + x["cm"] + x["sww"] + x["sl"])
                                                   for x in pop if x["sp"] >= 1.0) / len(pop), 6),
    "pool_gross_excluding_them": mean([x["A"][I1][0] for x in pop if x["sp"] < 1.0]),
    "pool_net_frozen_excluding_them": mean([x["A"][I1][0] - (x["sp"] + x["cm"] + x["sww"] + x["sl"])
                                            for x in pop if x["sp"] < 1.0]),
    "pool_net_sp73_excluding_them": mean([x["A"][I1][0] - (x["sp"] / 7.3 + x["cm"] + x["sww"] + x["sl"])
                                          for x in pop if x["sp"] < 1.0]),
    "by_family": {f: {"n": sum(1 for x in pop if x["fam"] == f and x["sp"] >= 1.0),
                      "pct": round(100 * sum(1 for x in pop if x["fam"] == f and x["sp"] >= 1.0)
                                   / max(1, sum(1 for x in pop if x["fam"] == f)), 2)}
                  for f in sorted({x["fam"] for x in pop if x["fam"]})},
    "by_symbol_top": sorted(({"sym": s,
                              "n": sum(1 for x in pop if x["sym"] == s and x["sp"] >= 1.0),
                              "pct": round(100 * sum(1 for x in pop if x["sym"] == s and x["sp"] >= 1.0)
                                           / max(1, sum(1 for x in pop if x["sym"] == s)), 2)}
                             for s in sorted({x["sym"] for x in pop})), key=lambda d: -d["n"])[:12]}

# ---- (2) stop measured in pre-decision ATR60 ----
ab = [(0, 0.25), (0.25, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, 4.0), (4.0, 8.0), (8.0, 1e9)]
res["stop_in_atr60_bands"] = [dict(band="[%s,%s)" % (a, b),
                                   **(block([x for x in pop if x["sia60"] is not None and a <= x["sia60"] < b]) or {}))
                              for a, b in ab]
sv = sorted([x for x in pop if x["sia60"] is not None], key=lambda x: x["sia60"])
res["stop_in_atr60_decile"] = []
for i in range(10):
    a = i * len(sv) // 10; b = (i + 1) * len(sv) // 10
    sl = sv[a:b]
    d = block(sl); d["decile"] = i + 1
    d["lo"] = round(sl[0]["sia60"], 5); d["hi"] = round(sl[-1]["sia60"], 5)
    res["stop_in_atr60_decile"].append(d)

res["atr_summary"] = {"stop_in_atr60": {"median": med([x["sia60"] for x in pop]),
                                        "p10": sorted(x["sia60"] for x in pop if x["sia60"] is not None)[len(sv) // 10],
                                        "p90": sorted(x["sia60"] for x in pop if x["sia60"] is not None)[9 * len(sv) // 10]},
                      "spread_in_atr60_median": med([x["spatr"] for x in pop]),
                      "share_stop_below_1_ATR60_pct": round(100 * sum(1 for x in pop if x["sia60"] is not None and x["sia60"] < 1.0) / len(sv), 3),
                      "share_stop_below_0p5_ATR60_pct": round(100 * sum(1 for x in pop if x["sia60"] is not None and x["sia60"] < 0.5) / len(sv), 3)}

# ---- born_past_stop vs tightness: was the untakeable cohort simply too tight? ----
ps = [x for x in allrows if x["born"] == "past_stop"]
res["born_past_stop_tightness"] = {"n": len(ps),
                                   "spread_r_med": med([x["sp"] for x in ps]),
                                   "stop_in_atr60_med": med([x["sia60"] for x in ps]),
                                   "rdpct_med": med([x["rdpct"] for x in ps]),
                                   "vs_takeable_stop_in_atr60_med": med([x["sia60"] for x in pop]),
                                   "vs_takeable_rdpct_med": med([x["rdpct"] for x in pop])}

with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1)
print("wrote", OUT)
print("DEAD-ON-ARRIVAL (spread_r>=1):", {k: v for k, v in res["stop_inside_the_spread"].items()
                                         if k in ("n", "share_of_honest_pop_pct", "gross_old_k1", "net_frozen_k1",
                                                  "net_sp73_k1", "contribution_to_pool_net_frozen_r",
                                                  "pool_gross_excluding_them", "pool_net_frozen_excluding_them",
                                                  "pool_net_sp73_excluding_them")})
print("--- spread_r bands ---")
for b in res["spread_r_bands"]:
    if b.get("n"):
        print("%-12s n=%5d gross_k1=%+8.5f net73=%+8.5f stop%%=%5.1f tgt%%=%5.1f rd%%=%.4f atr=%s"
              % (b["band"], b["n"], b["gross_old_k1"], b["net_sp73_k1"], b["stop_pct"], b["target_pct"],
                 b["rdpct_med"] or 0, b["stop_in_atr60_med"]))
print("--- stop_in_atr60 bands ---")
for b in res["stop_in_atr60_bands"]:
    if b.get("n"):
        print("%-12s n=%5d gross_k1=%+8.5f net73=%+8.5f stop%%=%5.1f tgt%%=%5.1f sprd_r=%.3f kcurve=%s"
              % (b["band"], b["n"], b["gross_old_k1"], b["net_sp73_k1"], b["stop_pct"], b["target_pct"],
                 b["spread_r_mean"], b["kcurve_gross_old"]))
print("atr_summary", res["atr_summary"])
