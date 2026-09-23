#!/usr/bin/env python3
"""e6 step 1 — INDEPENDENT reproduction of L8-F1 on January.

Re-implements the instrument from first principles off w0_R_PATHS + the decision anchor:
  fill_bar   = first 1-based bar index whose ADVERSE excursion touches 0 (entry level traded)
  honest_r   = first touch of +2R vs -1R AT OR AFTER fill_bar, conservative same-bar tie -> stop,
               unresolved marked at the 2h wall close, never-filled = 0.0 R
  born       = from w0cap2 anchor mkt_r_prev_close (clean pool drops born_past_stop)
Nothing here imports l8_*.
"""
import gzip, json, os, sys, collections
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import w0_ws

ANCH = os.path.join(D, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz")
OUT = os.path.join(D, "E6_JAN_REPRO_V1.json")


def born_state(m):
    if m is None: return "unknown"
    if m <= -1.0: return "born_past_stop"
    if m < -1e-9: return "born_marketable"
    if m <= 1e-9: return "born_at_limit"
    return "born_resting"


def resolve(fav, adv, cls, tgt=2.0, stp=-1.0):
    """(honest_r, outcome, fill_bar). fill_bar 1-based; -1 = never filled."""
    nb = len(fav)
    start = None
    for i in range(nb):
        if adv[i] <= 1e-12:
            start = i; break
    if start is None:
        return 0.0, "no_fill", -1
    bt = bs = -1
    for i in range(start, nb):
        if bt < 0 and fav[i] >= tgt - 1e-12: bt = i + 1
        if bs < 0 and adv[i] <= stp + 1e-12: bs = i + 1
        if bt > 0 and bs > 0: break
    fb = start + 1
    if bs > 0 and (bt <= 0 or bs <= bt):
        return stp, "stop", fb
    if bt > 0:
        return tgt, "target", fb
    return cls[nb - 1], "mark", fb


def main():
    anchor = {}
    with gzip.open(ANCH, "rt") as fh:
        for line in fh:
            r = json.loads(line)
            anchor[(r["candidate_id"], r["decision_time_utc"])] = r.get("mkt_r_prev_close")

    ws = {}
    for r in w0_ws.iter_rows():
        ws[w0_ws.key(r)] = r

    recs = []
    for rp in w0_ws.iter_rpaths():
        k = (rp["candidate_id"], rp["decision_time_utc"])
        w = ws[k]
        hr, oc, fb = resolve(rp["fav"], rp["adv"], rp["cls"])
        m = anchor.get(k)
        recs.append({"k": k, "fb": fb, "hr": hr, "oc": oc,
                     "born": born_state(m), "mkt_r": m,
                     "gross_r": w.get("gross_r"), "family": w.get("origin_family"),
                     "symbol": w.get("symbol")})
    clean = [r for r in recs if r["born"] != "born_past_stop"]

    def cohort(rows, lo, hi):
        return [r for r in rows if lo <= r["fb"] <= hi]

    def blk(rows):
        n = len(rows)
        if n == 0: return None
        hm = sum(r["hr"] for r in rows) / n
        gv = [r["gross_r"] for r in rows if r["gross_r"] is not None]
        gm = sum(gv) / len(gv) if gv else None
        c = collections.Counter(r["oc"] for r in rows)
        res = c["target"] + c["stop"]
        return {"n": n, "honest_mean": round(hm, 5),
                "gross_mean": round(gm, 5) if gm is not None else None,
                "res_win": round(c["target"] / res, 4) if res else None,
                "target_rate": round(c["target"] / n, 4), "stop_rate": round(c["stop"] / n, 4),
                "mark_rate": round(c["mark"] / n, 4)}

    out = {"n_paths": len(recs), "n_clean": len(clean), "cohorts": {}, "delay_sweep": [],
           "delay_sweep_raw": []}
    for lab, lo, hi in [("bar1", 1, 1), ("bar2_5", 2, 5), ("bar6_15", 6, 15),
                        ("bar16_60", 16, 60), ("bar61_120", 61, 120), ("never", -1, -1)]:
        out["cohorts"][lab] = blk(cohort(clean, lo, hi))
        if out["cohorts"][lab]:
            out["cohorts"][lab]["share"] = round(out["cohorts"][lab]["n"] / len(clean), 4)

    def sweep(rows, k):
        n = len(rows); vs = []
        c = collections.Counter()
        for r in rows:
            if r["fb"] < 0:
                vs.append(0.0); c["no_fill"] += 1
            elif r["fb"] <= k:
                vs.append(0.0); c["refused"] += 1
            else:
                vs.append(r["hr"]); c[r["oc"]] += 1
        traded = c["target"] + c["stop"] + c["mark"]
        res = c["target"] + c["stop"]
        m = sum(vs) / n
        sd = (sum((v - m) ** 2 for v in vs) / (n - 1)) ** 0.5 if n > 1 else 0.0
        ts = sum(v for v in vs if v != 0.0)
        return {"k": k, "n_opp": n, "n_traded": traded, "traded_share": round(traded / n, 4),
                "R_per_opportunity": round(m, 5),
                "R_per_trade": round(ts / traded, 5) if traded else None,
                "t": round(m / (sd / n ** 0.5), 3) if sd else 0.0,
                "res_win": round(c["target"] / res, 4) if res else None}

    for k in [0, 1, 2, 3, 5, 10, 20, 60]:
        out["delay_sweep"].append(sweep(clean, k))
    for k in [0, 1, 5, 15]:
        out["delay_sweep_raw"].append(sweep(recs, k))

    json.dump(out, open(OUT, "w"), indent=1)
    print("n_paths=%d n_clean=%d" % (len(recs), len(clean)))
    print("%-10s %7s %7s %10s %10s %8s" % ("cohort", "n", "share", "honest", "gross", "resWin"))
    for lab in ["bar1", "bar2_5", "bar6_15", "bar16_60", "bar61_120", "never"]:
        b = out["cohorts"][lab]
        if not b: print(lab, "n=0"); continue
        print("%-10s %7d %7.4f %+10.5f %+10s %8s" % (lab, b["n"], b["share"], b["honest_mean"],
              ("%+.5f" % b["gross_mean"]) if b["gross_mean"] is not None else "-", b["res_win"]))
    print("\nCLEAN delay sweep:  k  traded  R/opp      R/trade   resWin")
    for s in out["delay_sweep"]:
        print("  %3d %7d %+10.5f %+10s %8s" % (s["k"], s["n_traded"], s["R_per_opportunity"],
              ("%+.5f" % s["R_per_trade"]) if s["R_per_trade"] is not None else "-", s["res_win"]))
    print("RAW pool:", [(s["k"], s["R_per_opportunity"]) for s in out["delay_sweep_raw"]])
    print("->", OUT)


if __name__ == "__main__":
    main()
