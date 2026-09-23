"""e5 step 3 — L2-F6 across January, February and March on ONE validated instrument.

Per month:
  (a) the L2-F6 rule ladder, priced end to end  (does the RECOVERY reproduce?)
  (b) the price-space ceiling ladder G(k), conventions A and B, k=1..inf
      (does the k-INVARIANCE premise, and hence the zero ceiling, reproduce?)
  (c) the pre-specified boundary table with the LONG/SHORT beta control
Writes E5_THREE_MONTHS_V1.json
"""
import sys, os, json, gzip, random
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import e5_lib

OUT = os.path.join(D, "E5_THREE_MONTHS_V1.json")
MONTHS = ["january", "february", "march"]
KLADDER = [1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 15.0, 20.0, 30.0,
           50.0, 100.0, e5_lib.INF_K]
RULES = [("R1_as_shipped", 1.0, "A"), ("R2_unstopped_mark", e5_lib.INF_K, "B"),
         ("R3_prop_3x", 3.0, "B")]
SEED = 20260806


def boot(vals, n=400, seed=SEED):
    if len(vals) < 30:
        return None
    rnd = random.Random(seed)
    L = len(vals)
    m = sorted(sum(vals[rnd.randrange(L)] for _ in range(L)) / L for _ in range(n))
    return [round(m[int(0.025 * n)], 5), round(m[int(0.975 * n) - 1], 5)]


def load_month(m):
    rows = []
    with gzip.open(os.path.join(D, "e5_%s_WS_V1.jsonl.gz" % m), "rt") as f:
        for ln in f:
            rows.append(json.loads(ln))
    byk = {(r["candidate_id"], r["decision_time_utc"]): r for r in rows}
    anch = {k: {"mkt_r_prev_close": v["mkt_r_prev_close"]} for k, v in byk.items()}
    ents, st = e5_lib.build_entries(byk, iter(rows), anch)
    return rows, ents, st


def cohort(ents, keyfn, min_n=150):
    groups = {}
    for e in ents:
        g = keyfn(e)
        if g is not None:
            groups.setdefault(str(g), []).append(e)
    out = {}
    for g, sub in groups.items():
        if len(sub) < min_n:
            continue
        n = len(sub)
        c_fr = sum(e["sp"] + e["cm"] + e["sww"] + e["sl"] for e in sub) / n
        c_73 = sum(e["sp"] / 7.3 + e["cm"] + e["sww"] + e["sl"] for e in sub) / n
        c_85 = sum(e["sp"] / 8.5 + e["cm"] + e["sww"] + e["sl"] for e in sub) / n
        rec = {"n": n, "C_frozen": round(c_fr, 6), "C_sp73": round(c_73, 6), "C_sp85": round(c_85, 6)}
        for rname, kk, mode in RULES:
            v = [e5_lib.walk_k(e, kk, mode)[0] for e in sub]
            G = sum(v) / n
            lo = [e5_lib.walk_k(e, kk, mode)[0] for e in sub if (e["side"] or "").startswith("L")]
            sh = [e5_lib.walk_k(e, kk, mode)[0] for e in sub if (e["side"] or "").startswith("S")]
            rec[rname] = {"G": round(G, 6), "ci95": boot(v),
                          "gap_frozen": round(G - c_fr, 6), "gap_sp73": round(G - c_73, 6),
                          "gap_sp85": round(G - c_85, 6),
                          "n_long": len(lo), "n_short": len(sh),
                          "G_long": (round(sum(lo) / len(lo), 6) if lo else None),
                          "G_short": (round(sum(sh) / len(sh), 6) if sh else None),
                          "both_sides_positive": bool(lo and sh and sum(lo) > 0 and sum(sh) > 0)}
        out[g] = rec
    return out


res = {"schema": "gtos.e5.l2f6.three_months.v1", "seed": SEED,
       "instrument": "e5_lib + e5_build_month, validated bar-for-bar against CQ's January sidecar"}
for m in MONTHS:
    rows, ents, st = load_month(m)
    n = len(ents)
    mm = {"n_pool_rows": len(rows), "n_entries": n, "build": st}
    # (a) the L2 rule ladder
    mm["rules"] = {
        "baseline_k1": e5_lib.rule_eval(ents, lambda e: 1.0, "baseline k=1"),
        "S2": e5_lib.rule_eval(ents, lambda e: max(1.0, 2 * e["sp"]), "S(2)"),
        "S5": e5_lib.rule_eval(ents, lambda e: max(1.0, 5 * e["sp"]), "S(5)"),
        "S10": e5_lib.rule_eval(ents, lambda e: max(1.0, 10 * e["sp"]), "S(10)"),
        "S20": e5_lib.rule_eval(ents, lambda e: max(1.0, 20 * e["sp"]), "S(20)"),
        "k3": e5_lib.rule_eval(ents, lambda e: 3.0, "flat k=3"),
    }
    mm["recovery_frozen"] = round(mm["rules"]["S20"]["net_frozen"] - mm["rules"]["baseline_k1"]["net_frozen"], 6)
    mm["recovery_sp73"] = round(mm["rules"]["S20"]["net_sp73"] - mm["rules"]["baseline_k1"]["net_sp73"], 6)
    # (b) the ceiling
    for mode in ("A", "B"):
        mm["ladder_" + mode] = [e5_lib.price_space(ents, k, mode) for k in KLADDER]
    GA = [p["G_price"] for p in mm["ladder_A"]]
    GB = [p["G_price"] for p in mm["ladder_B"]]
    mm["k_invariance"] = {
        "A_range": round(max(GA) - min(GA), 6), "A_min": min(GA), "A_max": max(GA),
        "B_range": round(max(GB) - min(GB), 6), "B_min": min(GB), "B_max": max(GB),
        "C_frozen": mm["ladder_A"][0]["C_frozen"], "C_sp73": mm["ladder_A"][0]["C_sp73"],
        "ceiling_gap_frozen": round(max(max(GA), max(GB)) - mm["ladder_A"][0]["C_frozen"], 6),
        "ceiling_gap_sp73": round(max(max(GA), max(GB)) - mm["ladder_A"][0]["C_sp73"], 6),
    }
    # (c) boundary
    mm["overall"] = cohort(ents, lambda e: "ALL", min_n=1)
    mm["by_symbol"] = cohort(ents, lambda e: e["sym"])
    mm["by_family"] = cohort(ents, lambda e: e["fam"])
    mm["by_session"] = cohort(ents, lambda e: e["sess"])
    mm["by_hour"] = cohort(ents, lambda e: e["hour"])
    res[m] = mm
    print(m, "n", n, "recovery_frozen", mm["recovery_frozen"], "recovery/7.3", mm["recovery_sp73"],
          "| A_range", mm["k_invariance"]["A_range"], "B_range", mm["k_invariance"]["B_range"],
          "| ceiling_gap/7.3", mm["k_invariance"]["ceiling_gap_sp73"])

with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1)
print("wrote", OUT)
