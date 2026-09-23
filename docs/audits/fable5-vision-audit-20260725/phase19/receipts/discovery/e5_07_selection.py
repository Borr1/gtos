"""e5 step 7 — where L2-F6's zero ceiling STOPS applying.

Part A. The SHRINK term factorises again. With w_i = 1/k_i and x_i = (R_i(1) - c_i):
    mean(w x) - mean(x) = mean(x)*(mean(w)-1)  +  cov(w, x)
The first term is MECHANICAL (any uniform down-sizing of a negative book gives it).
The second is TARGETING -- it is only nonzero if cost-based sizing down-weights the rows
that were actually worse. Measured per month.

Part B. Exit levers all have a zero ceiling because they only change how much of a
negatively-drifting instrument you hold. ENTRY-side selection is a different operator:
it changes WHICH rows you own. Threshold chosen on JANUARY, tested unchanged on FEBRUARY
and MARCH. Reports the honest out-of-sample gap, not the in-sample maximum.
Writes E5_SELECTION_V1.json
"""
import sys, os, json, gzip
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import e5_lib

OUT = os.path.join(D, "E5_SELECTION_V1.json")
MONTHS = ["january", "february", "march"]
QS = [0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50, 0.60, 0.75, 0.90, 1.00]


def load(m):
    rows = []
    with gzip.open(os.path.join(D, "e5_%s_WS_V1.jsonl.gz" % m), "rt") as f:
        for ln in f:
            r = json.loads(ln)
            mk = r["mkt_r_prev_close"]
            if mk is not None and mk <= -1.0:
                continue
            adv = r["adv"]
            fb = next((i for i in range(len(adv)) if adv[i] <= 1e-12), None)
            if fb is None:
                continue
            sp = float(r.get("spread_r") or 0); cm = float(r.get("commission_r") or 0)
            sw = float(r.get("swap_cost_r") or 0); sl = float(r.get("expected_slippage_r") or 0)
            e = {"fav": r["fav"], "adv": adv, "cls": r["cls"], "fb": fb,
                 "tgt": (r.get("policy_target_r") or 2.0), "sym": r["symbol"],
                 "fam": r.get("origin_family"), "sess": r.get("session_bucket"),
                 "side": r.get("side"), "sp": sp, "cm": cm, "sww": sw, "sl": sl,
                 "c": sp + cm + sw + sl, "c73": sp / 7.3 + cm + sw + sl,
                 "tight_pct": (r["risk_distance"] / abs(float(r["entry_price"])) * 100.0
                               if r.get("entry_price") else None),
                 "ptgt": (r.get("policy_target_r") or 2.0)}
            rows.append(e)
    return rows


def walk(e, trail=None, stop_r=-1.0):
    fav, adv, cls, fb, tgt = e["fav"], e["adv"], e["cls"], e["fb"], e["tgt"]
    stop = stop_r; peak = -1e18
    for i in range(fb, len(fav)):
        f, a = fav[i], adv[i]
        if a <= stop + 1e-12:
            return stop
        if f >= tgt - 1e-12:
            return tgt
        if f > peak:
            peak = f
        if trail is not None and peak >= trail:
            stop = max(stop, peak - trail)
    return cls[-1]


def mean(v):
    return sum(v) / len(v) if v else None


res = {"schema": "gtos.e5.selection.v1"}
data = {}
for m in MONTHS:
    ents = load(m)
    for e in ents:
        e["R1"] = walk(e)
        e["Rt"] = walk(e, trail=0.25)
        e["Rt10"] = walk(e, trail=0.1)
    data[m] = ents

# ---------------- Part A: mechanical vs targeting ----------------
partA = {}
for m in MONTHS:
    ents = data[m]
    blk = {}
    for c in (2, 5, 10, 20):
        w = [1.0 / max(1.0, c * e["sp"]) for e in ents]
        for lab, cost in (("frozen", "c"), ("sp73", "c73")):
            x = [e["R1"] - e[cost] for e in ents]
            mw, mx = mean(w), mean(x)
            tot = mean([a * b for a, b in zip(w, x)]) - mx
            mech = mx * (mw - 1.0)
            cov = tot - mech
            blk["S%d_%s" % (c, lab)] = {
                "mean_w": round(mw, 6), "mean_x": round(mx, 6),
                "total_shrink": round(tot, 6), "mechanical": round(mech, 6),
                "targeting_cov": round(cov, 6),
                "targeting_share_pct": round(100 * cov / tot, 2) if abs(tot) > 1e-9 else None}
    partA[m] = blk
res["partA_shrink_factorisation"] = partA

# ---------------- Part B: entry-side selection ----------------
def sweep(ents, keyfn, ascending=True, exit_key="R1", cost_key="c73"):
    vals = [(keyfn(e), e) for e in ents if keyfn(e) is not None]
    vals.sort(key=lambda t: t[0], reverse=not ascending)
    out = {}
    for q in QS:
        k = max(30, int(q * len(vals)))
        sub = [e for _, e in vals[:k]]
        G = mean([e[exit_key] for e in sub])
        C = mean([e[cost_key] for e in sub])
        out[str(q)] = {"n": len(sub), "G": round(G, 6), "C": round(C, 6),
                       "gap": round(G - C, 6),
                       "cut": round(vals[k - 1][0], 8)}
    return out


SEL = {
    "cheap_spread_r": (lambda e: e["sp"], True),
    "cheap_total_cost": (lambda e: e["c"], True),
    "wide_stop_pct_of_price": (lambda e: e["tight_pct"], False),
    "tight_stop_pct_of_price": (lambda e: e["tight_pct"], True),
    "low_policy_target_r": (lambda e: e["ptgt"], True),
    "high_policy_target_r": (lambda e: e["ptgt"], False),
}
partB = {}
for exit_key in ("R1", "Rt", "Rt10"):
    for sname, (kf, asc) in SEL.items():
        blk = {m: sweep(data[m], kf, asc, exit_key) for m in MONTHS}
        # pick q on JANUARY, read it out of sample
        jq = max(QS, key=lambda q: blk["january"][str(q)]["gap"])
        blk["january_chosen_q"] = jq
        blk["oos"] = {m: blk[m][str(jq)]["gap"] for m in MONTHS}
        blk["oos_mean_feb_mar"] = round((blk["february"][str(jq)]["gap"] + blk["march"][str(jq)]["gap"]) / 2, 6)
        partB["%s|%s" % (exit_key, sname)] = blk
res["partB_entry_selection_sp73"] = partB

with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1)

print("=== PART A: is the SHRINK mechanical or targeted? (cost at /7.3) ===")
print("%-10s %-8s %9s %11s %11s %11s %8s" % ("month", "rule", "mean_w", "total", "mechanical", "targeting", "tgt%"))
for m in MONTHS:
    for c in (2, 5, 10, 20):
        v = partA[m]["S%d_sp73" % c]
        print("%-10s S(%-6d) %9.4f %+11.5f %+11.5f %+11.5f %8s"
              % (m, c, v["mean_w"], v["total_shrink"], v["mechanical"], v["targeting_cov"],
                 v["targeting_share_pct"]))
print()
print("=== PART B: entry selection, q chosen on JANUARY, gap at corrected spread ===")
print("%-34s %5s %10s %10s %10s %11s" % ("exit|selector", "q", "JAN gap", "FEB gap", "MAR gap", "meanFEB+MAR"))
for k, v in sorted(partB.items(), key=lambda kv: -kv[1]["oos_mean_feb_mar"]):
    print("%-34s %5.2f %+10.5f %+10.5f %+10.5f %+11.5f"
          % (k, v["january_chosen_q"], v["oos"]["january"], v["oos"]["february"],
             v["oos"]["march"], v["oos_mean_feb_mar"]))
print("wrote", OUT)
