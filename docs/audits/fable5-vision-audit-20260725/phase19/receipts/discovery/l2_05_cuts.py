"""l2 step 5 — per family / symbol / session / hour: where is the stop salvageable?

For each cut, on the honest population (filled, ex-born_past_stop):
  n, stop share, gross_oldunit at k=1 and k=2.5, the price-space delta (the ONLY part of a
  stop change that is not a denominator effect), net at k=1 and k=2.5 under frozen and /7.3
  spread, mean spread_r, median risk-distance %, and the salvage stats (share of stops that
  later reach target inside the 2h wall).
Writes L2_CUTS_V1.json
"""
import sys, os, json, gzip
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import w0_ws

KS = [0.25, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.9, 1.0, 1.1, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]
I1 = KS.index(1.0); I25 = KS.index(2.5); I15 = KS.index(1.5)
OUT = os.path.join(D, "L2_CUTS_V1.json")


def mean(v):
    v = [x for x in v if x is not None]
    return round(sum(v) / len(v), 6) if v else None


def med(v):
    v = sorted(x for x in v if x is not None)
    return round(v[len(v) // 2], 6) if v else None


rows = w0_ws.load(); byk = {w0_ws.key(r): r for r in rows}
recs = {}
with gzip.open(os.path.join(D, "l2_RECS_V1.jsonl.gz"), "rt") as f:
    for ln in f:
        e = json.loads(ln); recs[(e["cid"], e["dt"])] = e
pop = []
with gzip.open(os.path.join(D, "l2_SWEEP_ROWS_V1.jsonl.gz"), "rt") as f:
    for ln in f:
        e = json.loads(ln)
        if e["A"] is None or (e["m"] is not None and e["m"] <= -1.0):
            continue
        k = (e["cid"], e["dt"]); r = byk[k]; c = recs[k]
        pop.append({"A": e["A"], "fam": e["fam"], "sym": e["sym"], "sess": e["sess"],
                    "hr": r.get("utc_hour_bucket"), "tf": r.get("decision_timeframe"),
                    "side": r.get("side"),
                    "sp": r.get("spread_r") or 0.0, "cm": r.get("commission_r") or 0.0,
                    "sww": r.get("swap_cost_r") or 0.0, "sl": r.get("expected_slippage_r") or 0.0,
                    "rdpct": e["rdpct"], "exit": c.get("exit"),
                    "salv": c.get("bars_to_tgt_post") is not None if c.get("exit") == "stop" else None,
                    "mfe_post": c.get("mfe_post"), "mae_pre": c.get("mae_pre")})


def block(v):
    n = len(v)
    g1 = [x["A"][I1][0] for x in v]
    g25 = [x["A"][I25][0] for x in v]
    g15 = [x["A"][I15][0] for x in v]
    c1 = [x["sp"] + x["cm"] + x["sww"] + x["sl"] for x in v]
    c25 = [(x["sp"] + x["cm"] + x["sww"]) / 2.5 + x["sl"] for x in v]
    c1c = [x["sp"] / 7.3 + x["cm"] + x["sww"] + x["sl"] for x in v]
    c25c = [(x["sp"] / 7.3 + x["cm"] + x["sww"]) / 2.5 + x["sl"] for x in v]
    S = [x for x in v if x["exit"] == "stop"]
    sal = [x for x in S if x["salv"]]
    return {"n": n,
            "stop_pct_k1": round(100 * sum(1 for x in v if x["exit"] == "stop") / n, 3),
            "gross_old_k1": mean(g1),
            "gross_old_k1p5": round((mean(g15) or 0) * 1.5, 6),
            "gross_old_k2p5": round((mean(g25) or 0) * 2.5, 6),
            "price_space_delta_k1_to_2p5": round((mean(g25) or 0) * 2.5 - (mean(g1) or 0), 6),
            "gross_new_k1": mean(g1), "gross_new_k2p5": mean(g25),
            "net_frozen_k1": round((mean(g1) or 0) - (mean(c1) or 0), 6),
            "net_frozen_k2p5": round((mean(g25) or 0) - (mean(c25) or 0), 6),
            "net_sp73_k1": round((mean(g1) or 0) - (mean(c1c) or 0), 6),
            "net_sp73_k2p5": round((mean(g25) or 0) - (mean(c25c) or 0), 6),
            "spread_r_mean": mean([x["sp"] for x in v]),
            "spread_r_median": med([x["sp"] for x in v]),
            "risk_dist_pct_median": med([x["rdpct"] for x in v]),
            "n_stopped": len(S),
            "salvage_pct": round(100 * len(sal) / len(S), 3) if S else None,
            "mfe_after_stop_mean": mean([x["mfe_post"] for x in S])}


res = {"n": len(pop), "k_grid": KS,
       "note": "gross_old_* is PRICE-space expectancy (original R unit). Any change in it is a real "
               "stop effect; the new-unit improvement is the 1/k denominator and is reported separately."}
for cutname, keyf in (("family", lambda x: x["fam"]), ("symbol", lambda x: x["sym"]),
                      ("session", lambda x: x["sess"]), ("hour", lambda x: x["hr"]),
                      ("side", lambda x: x["side"]), ("timeframe", lambda x: x["tf"])):
    g = {}
    for x in pop:
        g.setdefault(keyf(x), []).append(x)
    res[cutname] = {str(k): block(v) for k, v in sorted(g.items(), key=lambda kv: -len(kv[1])) if len(v) >= 25}

# spread_r deciles -- 'how tight is the stop measured in spreads', known at decision
sv = sorted(pop, key=lambda x: x["sp"])
dec = []
for i in range(10):
    a = i * len(sv) // 10; b = (i + 1) * len(sv) // 10
    sl = sv[a:b]
    d = block(sl); d["decile"] = i + 1
    d["spread_r_lo"] = round(sl[0]["sp"], 5); d["spread_r_hi"] = round(sl[-1]["sp"], 5)
    dec.append(d)
res["spread_r_decile"] = dec

# risk-distance-%-of-price deciles
sv2 = sorted([x for x in pop if x["rdpct"] is not None], key=lambda x: x["rdpct"])
dec2 = []
for i in range(10):
    a = i * len(sv2) // 10; b = (i + 1) * len(sv2) // 10
    sl = sv2[a:b]
    d = block(sl); d["decile"] = i + 1
    d["rdpct_lo"] = round(sl[0]["rdpct"], 5); d["rdpct_hi"] = round(sl[-1]["rdpct"], 5)
    dec2.append(d)
res["risk_distance_pct_decile"] = dec2

with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1)
print("wrote", OUT, "n", len(pop))
print("%-32s %6s %8s %9s %9s %9s %8s %8s %7s" % ("family", "n", "stop%", "gross_k1", "gross_k2.5",
                                                 "delta_px", "sprd_r", "net73_k1", "salv%"))
for k, b in res["family"].items():
    print("%-32s %6d %8.2f %+9.5f %+10.5f %+9.5f %8.4f %+8.4f %7.1f"
          % (k[:32], b["n"], b["stop_pct_k1"], b["gross_old_k1"], b["gross_old_k2p5"],
             b["price_space_delta_k1_to_2p5"], b["spread_r_mean"], b["net_sp73_k1"], b["salvage_pct"] or 0))
print("--- spread_r decile ---")
for b in dec:
    print("d%-2d [%7.4f,%7.4f] n=%5d gross_k1=%+8.5f gross_k2.5=%+8.5f delta=%+8.5f net73_k1=%+8.5f rd%%=%.4f"
          % (b["decile"], b["spread_r_lo"], b["spread_r_hi"], b["n"], b["gross_old_k1"],
             b["gross_old_k2p5"], b["price_space_delta_k1_to_2p5"], b["net_sp73_k1"], b["risk_dist_pct_median"] or 0))
