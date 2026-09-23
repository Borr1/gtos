#!/usr/bin/env python3
"""e6_mech — WHY bar-1 fills are adverse, and the live-implementable form of the rule.

Two questions the l8 receipt did not answer:

 1. MECHANISM. Is the value in the CLOCK (60 s) or in the PRE-RUN (price first had to travel
    AWAY from the entry, in the trade's favour, before coming back to fill)? A bar-1 fill has a
    pre-run of exactly 0 by construction: the market never left. `prerun_r` = the largest
    favourable excursion, measured from the entry level, over the bars BEFORE the fill bar.

 2. IMPLEMENTABILITY. l8's rule CANCELS a candidate whose entry trades in the first k bars.
    A live book would more naturally DEFER: hold the order back until bar k+1 and take the fill
    if the level trades again. Deferring recovers candidates the cancel rule throws away, so it
    is the cheaper repair -- if it survives.

Emits e6_MECH_<MONTH>.jsonl.gz and E6_MECH_V1.json.
"""
import collections, gzip, json, os, sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import e6_build_month as B

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY"]
OUT = os.path.join(D, "E6_MECH_V1.json")
TOL = B.TOL


def first_fill_at_or_after(adv, lo):
    for i in range(lo, len(adv)):
        if adv[i] <= TOL:
            return i
    return None


def resolve_from(fav, adv, cls, start, tgt=2.0, stp=-1.0):
    bt = bs = -1
    for i in range(start, len(fav)):
        if bt < 0 and fav[i] >= tgt - TOL:
            bt = i + 1
        if bs < 0 and adv[i] <= stp + TOL:
            bs = i + 1
        if bt > 0 and bs > 0:
            break
    if bs > 0 and (bt <= 0 or bs <= bt):
        return stp, "stop"
    if bt > 0:
        return tgt, "target"
    return cls[-1], "mark"


def build(month):
    cfg = B.MONTHS[month]
    filt = cfg.get("filt")
    sidecar = {}
    if cfg["sidecar"]:
        with gzip.open(cfg["sidecar"], "rt") as fh:
            for line in fh:
                s = json.loads(line)
                sidecar[(s["candidate_id"], s["decision_time_utc"])] = s["ordered_path_observations"]
    rows = []
    with gzip.open(cfg["pool"], "rt") as fh:
        for line in fh:
            r = json.loads(line)
            if filt is not None and not filt(r):
                continue
            entry = r.get("entry_price"); stop = r.get("stop_loss")
            side = r.get("side") or r.get("direction")
            if entry is None or stop is None or side is None:
                continue
            rd = abs(entry - stop)
            if rd <= 0:
                continue
            b = B.load_bars(cfg["bars"], r["symbol"])
            obs = sidecar.get((r["candidate_id"], r["decision_time_utc"]))
            if obs is None:
                if b is None:
                    continue
                obs = B.bars_after(b, r["decision_time_utc"])
                if not obs:
                    continue
            fav, adv, cls = B.rpath(obs, entry, rd, side)
            start = first_fill_at_or_after(adv, 0)
            if start is None:
                rec = {"fb": -1, "hr": 0.0, "oc": "no_fill", "prerun": round(max(fav), 4),
                       "b1rng": round(fav[0] - adv[0], 4), "b1fav": fav[0], "b1adv": adv[0]}
            else:
                hr, oc = resolve_from(fav, adv, cls, start)
                prerun = round(max(fav[:start]), 4) if start > 0 else 0.0
                rec = {"fb": start + 1, "hr": round(hr, 6), "oc": oc, "prerun": prerun,
                       "b1rng": round(fav[0] - adv[0], 4), "b1fav": fav[0], "b1adv": adv[0]}
            # DEFER variant: hold the order back until bar k+1, take the next touch
            for k in (1, 2, 5):
                s2 = first_fill_at_or_after(adv, k)
                if s2 is None:
                    rec["dfb%d" % k] = -1; rec["dhr%d" % k] = 0.0; rec["doc%d" % k] = "no_fill"
                else:
                    h2, o2 = resolve_from(fav, adv, cls, s2)
                    rec["dfb%d" % k] = s2 + 1; rec["dhr%d" % k] = round(h2, 6); rec["doc%d" % k] = o2
            mkt = B.anchor_mkt_r(b, r["decision_time_utc"], entry, rd, side) if b is not None else None
            npr = r.get("opportunity_net_proxy_r"); cr = r.get("cost_r")
            rec.update({"cid": r["candidate_id"], "dt": r["decision_time_utc"], "month": month,
                        "sym": r.get("symbol"), "side": side, "fam": r.get("origin_family"),
                        "sess": r.get("session_bucket"), "born": B.born_state(mkt), "mkt_r": mkt,
                        "cost_r": cr, "spread_r": r.get("spread_r"),
                        "gross_r": round(npr + cr, 6) if (npr is not None and cr is not None) else None,
                        "nb": len(fav)})
            rows.append(rec)
    p = os.path.join(D, "e6_MECH_%s.jsonl.gz" % month)
    with gzip.open(p, "wt") as fh:
        for r in rows:
            fh.write(json.dumps(r, separators=(",", ":")) + "\n")
    print("MECH %s rows=%d -> %s" % (month, len(rows), p))
    return rows


def load(month):
    p = os.path.join(D, "e6_MECH_%s.jsonl.gz" % month)
    with gzip.open(p, "rt") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def mean(vs):
    return sum(vs) / len(vs) if vs else None


def opp(rows, field="hr", refuse=None):
    """R per candidate-opportunity; `refuse(r)` -> True books 0.0."""
    vs = []
    for r in rows:
        if r[field] == 0.0 and r.get("oc") == "no_fill":
            vs.append(0.0)
        elif refuse is not None and refuse(r):
            vs.append(0.0)
        else:
            vs.append(r[field])
    n = len(vs)
    m = sum(vs) / n
    sd = (sum((v - m) ** 2 for v in vs) / (n - 1)) ** 0.5 if n > 1 else 0.0
    return {"n": n, "mean": round(m, 5), "t": round(m / (sd / n ** 0.5), 3) if sd else 0.0}


PRERUN_EDGES = [0.0, 0.05, 0.10, 0.25, 0.50, 1.00]
PRERUN_LABS = ["0", "0-0.05", "0.05-0.10", "0.10-0.25", "0.25-0.50", "0.50-1.0", ">1.0"]


def prebucket(v):
    if v is None: return "null"
    if v <= 1e-9: return "0"
    for e, lab in zip(PRERUN_EDGES[1:], PRERUN_LABS[1:]):
        if v <= e: return lab
    return ">1.0"


FBLABS = [("1", 1, 1), ("2-5", 2, 5), ("6-15", 6, 15), ("16-60", 16, 60), ("61-120", 61, 120)]


def main():
    if "--build" in sys.argv:
        for m in MONTHS:
            build(m)
        return
    allrows = []
    for m in MONTHS:
        allrows.extend(load(m))
    clean = [r for r in allrows if r["born"] != "born_past_stop"]
    filled = [r for r in clean if r["fb"] > 0]
    res = {"n_all": len(allrows), "n_clean": len(clean), "n_filled": len(filled)}

    # ---- 1. prerun ladder on filled candidates
    tab = {}
    for lab in PRERUN_LABS:
        sub = [r for r in filled if prebucket(r["prerun"]) == lab]
        if not sub: continue
        c = collections.Counter(r["oc"] for r in sub)
        rz = c["target"] + c["stop"]
        tab[lab] = {"n": len(sub), "share": round(len(sub) / len(filled), 4),
                    "honest_mean": round(mean([r["hr"] for r in sub]), 5),
                    "res_win": round(c["target"] / rz, 4) if rz else None,
                    "median_fb": sorted(r["fb"] for r in sub)[len(sub) // 2]}
    res["prerun_ladder"] = tab

    # ---- 2. 2D prerun x fill-bar: does the CLOCK still matter inside a prerun bucket?
    grid = {}
    for lab in PRERUN_LABS:
        row = {}
        for flab, lo, hi in FBLABS:
            sub = [r for r in filled if prebucket(r["prerun"]) == lab and lo <= r["fb"] <= hi]
            if len(sub) < 50: continue
            row[flab] = {"n": len(sub), "mean": round(mean([r["hr"] for r in sub]), 5)}
        if row: grid[lab] = row
    res["prerun_x_fillbar"] = grid

    # ---- 3. a PURE prerun rule vs the pure clock rule, priced identically
    res["rule_compare"] = {}
    base = opp(clean, "hr")
    res["rule_compare"]["as_shipped_k0"] = base
    res["rule_compare"]["clock_k1"] = opp(clean, "hr", refuse=lambda r: 0 < r["fb"] <= 1)
    res["rule_compare"]["clock_k2"] = opp(clean, "hr", refuse=lambda r: 0 < r["fb"] <= 2)
    res["rule_compare"]["clock_k5"] = opp(clean, "hr", refuse=lambda r: 0 < r["fb"] <= 5)
    for x in [0.01, 0.05, 0.10, 0.25, 0.50, 1.0]:
        res["rule_compare"]["prerun_ge_%.2f" % x] = opp(
            clean, "hr", refuse=lambda r, x=x: r["fb"] > 0 and r["prerun"] < x)
    # combined
    res["rule_compare"]["clock_k1_AND_prerun_ge_0.10"] = opp(
        clean, "hr", refuse=lambda r: r["fb"] > 0 and (r["fb"] <= 1 or r["prerun"] < 0.10))

    # ---- 4. DEFER variant (live-implementable): hold the order until bar k+1
    res["defer"] = {}
    for k in (1, 2, 5):
        f = "dhr%d" % k
        vs = [r[f] for r in clean]
        n = len(vs); m = sum(vs) / n
        sd = (sum((v - m) ** 2 for v in vs) / (n - 1)) ** 0.5
        c = collections.Counter(r["doc%d" % k] for r in clean)
        traded = c["target"] + c["stop"] + c["mark"]
        rz = c["target"] + c["stop"]
        res["defer"]["k%d" % k] = {
            "n_opp": n, "R_per_opportunity": round(m, 5),
            "t": round(m / (sd / n ** 0.5), 3),
            "n_traded": traded, "traded_share": round(traded / n, 4),
            "R_per_trade": round(sum(v for v in vs if v != 0.0) / traded, 5) if traded else None,
            "res_win": round(c["target"] / rz, 4) if rz else None,
            "recovered_vs_cancel": traded - sum(1 for r in clean if r["fb"] > k)}
        # per month
        res["defer"]["k%d" % k]["by_month"] = {}
        for mm in MONTHS:
            sub = [r for r in clean if r["month"] == mm]
            v2 = [r[f] for r in sub]
            res["defer"]["k%d" % k]["by_month"][mm] = round(sum(v2) / len(v2), 5)

    # ---- 5. speed proxy: the first bar's own range in R
    def rb(v):
        for e, lab in zip([0.05, 0.1, 0.2, 0.4, 0.8], ["<=0.05", "0.05-0.1", "0.1-0.2", "0.2-0.4", "0.4-0.8"]):
            if v <= e: return lab
        return ">0.8"
    sp = {}
    for lab in ["<=0.05", "0.05-0.1", "0.1-0.2", "0.2-0.4", "0.4-0.8", ">0.8"]:
        sub = [r for r in clean if rb(r["b1rng"]) == lab]
        if len(sub) < 100: continue
        f1 = [r for r in sub if r["fb"] == 1]
        fl = [r for r in sub if r["fb"] > 1]
        sp[lab] = {"n": len(sub), "bar1_share": round(len(f1) / len(sub), 4),
                   "bar1_mean": round(mean([r["hr"] for r in f1]), 5) if f1 else None,
                   "later_mean": round(mean([r["hr"] for r in fl]), 5) if fl else None,
                   "k0": opp(sub, "hr")["mean"],
                   "k1": opp(sub, "hr", refuse=lambda r: 0 < r["fb"] <= 1)["mean"]}
    res["bar1_range_r"] = sp

    json.dump(res, open(OUT, "w"), indent=1)

    print("n_clean=%d n_filled=%d" % (len(clean), len(filled)))
    print("\n=== PRERUN LADDER (filled, clean, 5 months) ===")
    print("%-12s %8s %7s %10s %8s %8s" % ("prerun_r", "n", "share", "honest", "resWin", "medFB"))
    for lab in PRERUN_LABS:
        if lab not in tab: continue
        b = tab[lab]
        print("%-12s %8d %7.4f %+10.5f %8s %8d" % (lab, b["n"], b["share"], b["honest_mean"], b["res_win"], b["median_fb"]))
    print("\n=== PRERUN x FILL-BAR (mean honest R; n in parens) ===")
    hdr = [f[0] for f in FBLABS]
    print("%-12s" % "prerun" + "".join("%16s" % h for h in hdr))
    for lab in PRERUN_LABS:
        if lab not in grid: continue
        s = "%-12s" % lab
        for h in hdr:
            c = grid[lab].get(h)
            s += "%16s" % (("%+.4f/%d" % (c["mean"], c["n"])) if c else "-")
        print(s)
    print("\n=== RULE COMPARISON (R per candidate-opportunity, clean pool) ===")
    for k2, v in res["rule_compare"].items():
        print("%-34s n=%6d %+0.5f t=%+.2f" % (k2, v["n"], v["mean"], v["t"]))
    print("\n=== DEFER (hold order to bar k+1, take next touch) ===")
    for k in (1, 2, 5):
        d = res["defer"]["k%d" % k]
        print("k=%d R/opp %+0.5f t=%+.2f traded %d (%.4f) R/trade %s resWin %s | by month %s" % (
            k, d["R_per_opportunity"], d["t"], d["n_traded"], d["traded_share"],
            d["R_per_trade"], d["res_win"], d["by_month"]))
    print("\n=== BAR-1 RANGE (speed proxy) ===")
    print("%-10s %8s %8s %10s %10s %10s %10s" % ("b1rng_R", "n", "b1share", "bar1", "later", "k0", "k1"))
    for lab, b in sp.items():
        print("%-10s %8d %8.4f %+10s %+10s %+10.5f %+10.5f" % (
            lab, b["n"], b["bar1_share"],
            ("%+.5f" % b["bar1_mean"]) if b["bar1_mean"] is not None else "-",
            ("%+.5f" % b["later_mean"]) if b["later_mean"] is not None else "-", b["k0"], b["k1"]))
    print("->", OUT)


if __name__ == "__main__":
    main()
