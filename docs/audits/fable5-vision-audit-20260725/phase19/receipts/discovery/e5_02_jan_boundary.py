"""e5 step 2 — where the ceiling is NOT zero, and whether it is edge or beta.

Three PRE-SPECIFIED geometries (no max-over-ladder selection):
  R1  as shipped        stop -1d, target +2d          (convention A, k=1)
  R2  unstopped mark    no stop, no target, 2h mark    (= convention B, k=inf)
  R3  proportional 3:1  stop -3d, target +6d           (convention B, k=3)
Each is compared to the k-invariant price-space cost C at three spread regimes.

The beta control: the same G split LONG vs SHORT inside each cohort. A directional edge
must show on BOTH sides; a January drift in the instrument shows on one.
Bootstrap: 400 resamples, seed 20260806, on the cohort mean.
Writes E5_JAN_BOUNDARY_V1.json
"""
import sys, os, json, gzip, random
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import w0_ws, e5_lib

OUT = os.path.join(D, "E5_JAN_BOUNDARY_V1.json")
SEED = 20260806
RULES = [("R1_as_shipped", 1.0, "A"), ("R2_unstopped_mark", e5_lib.INF_K, "B"),
         ("R3_prop_3x", 3.0, "B")]


def boot(vals, n=400, seed=SEED):
    if len(vals) < 20:
        return None
    rnd = random.Random(seed)
    m = []
    L = len(vals)
    for _ in range(n):
        s = sum(vals[rnd.randrange(L)] for _ in range(L))
        m.append(s / L)
    m.sort()
    return [round(m[int(0.025 * n)], 5), round(m[int(0.975 * n) - 1], 5)]


def load_jan():
    rows = w0_ws.load()
    byk = {w0_ws.key(r): r for r in rows}
    anch = {}
    with gzip.open(os.path.join(D, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz"), "rt") as f:
        for ln in f:
            a = json.loads(ln)
            anch[(a["candidate_id"], a["decision_time_utc"])] = a
    return e5_lib.build_entries(byk, w0_ws.iter_rpaths(), anch)


def cohort_table(ents, keyfn, label, min_n=150):
    groups = {}
    for e in ents:
        g = keyfn(e)
        if g is not None:
            groups.setdefault(str(g), []).append(e)
    out = {}
    for g, sub in sorted(groups.items()):
        if len(sub) < min_n:
            continue
        c_fr = sum(e["sp"] + e["cm"] + e["sww"] + e["sl"] for e in sub) / len(sub)
        c_73 = sum(e["sp"] / 7.3 + e["cm"] + e["sww"] + e["sl"] for e in sub) / len(sub)
        c_85 = sum(e["sp"] / 8.5 + e["cm"] + e["sww"] + e["sl"] for e in sub) / len(sub)
        rec = {"n": len(sub), "C_frozen": round(c_fr, 6), "C_sp73": round(c_73, 6),
               "C_sp85": round(c_85, 6)}
        for rname, kk, mode in RULES:
            v = [e5_lib.walk_k(e, kk, mode)[0] for e in sub]
            G = sum(v) / len(v)
            longs = [e5_lib.walk_k(e, kk, mode)[0] for e in sub if (e["side"] or "").upper().startswith("L")]
            shorts = [e5_lib.walk_k(e, kk, mode)[0] for e in sub if (e["side"] or "").upper().startswith("S")]
            rec[rname] = {
                "G": round(G, 6), "ci95": boot(v),
                "gap_frozen": round(G - c_fr, 6), "gap_sp73": round(G - c_73, 6),
                "gap_sp85": round(G - c_85, 6),
                "n_long": len(longs), "G_long": (round(sum(longs) / len(longs), 6) if longs else None),
                "n_short": len(shorts), "G_short": (round(sum(shorts) / len(shorts), 6) if shorts else None),
                "both_sides_positive": bool(longs and shorts and sum(longs) > 0 and sum(shorts) > 0),
            }
        out[g] = rec
    return {label: out}


if __name__ == "__main__":
    ents, st = load_jan()
    res = {"month": "january_2026", "n": len(ents), "build": st, "seed": SEED,
           "rules": [{"name": r[0], "k": (None if r[1] >= e5_lib.INF_K else r[1]), "mode": r[2]} for r in RULES]}
    res.update(cohort_table(ents, lambda e: "ALL", "overall", min_n=1))
    res.update(cohort_table(ents, lambda e: e["sym"], "by_symbol"))
    res.update(cohort_table(ents, lambda e: e["fam"], "by_family"))
    res.update(cohort_table(ents, lambda e: e["sess"], "by_session"))
    with open(OUT, "w") as fh:
        json.dump(res, fh, indent=1)

    hdr = "%-26s %6s %8s %8s %9s %9s %9s %7s"
    for grp in ("overall", "by_symbol", "by_family"):
        print("===", grp)
        print(hdr % ("cohort", "n", "C/7.3", "G_R2", "gapR2/7.3", "G_long", "G_short", "both+"))
        rank = sorted(res[grp].items(), key=lambda kv: -kv[1]["R2_unstopped_mark"]["gap_sp73"])
        for g, v in rank:
            r2 = v["R2_unstopped_mark"]
            print(hdr % (g[:26], v["n"], "%.4f" % v["C_sp73"], "%+.4f" % r2["G"],
                         "%+.4f" % r2["gap_sp73"],
                         ("%+.4f" % r2["G_long"]) if r2["G_long"] is not None else "-",
                         ("%+.4f" % r2["G_short"]) if r2["G_short"] is not None else "-",
                         "YES" if r2["both_sides_positive"] else ""))
    print("wrote", OUT)
