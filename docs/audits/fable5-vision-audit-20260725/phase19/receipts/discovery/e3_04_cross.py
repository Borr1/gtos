"""e3 step 4 -- cross-month comparison on ONE common axis, plus the boundary.

March carries no `execution_fill_probability` column, so every cross-month table here is
computed on `fp_hat_m1atr` -- the SAME quantity reconstructed from
poi_execution_lifecycle.py:161-193 with an M1 ATR14. Calibration against the real field
(January + February, n = 51,677): Spearman 0.939 / 0.930 overall, 0.944 / 0.948 inside the
resting book, mean |error| 0.069.
"""
import collections, gzip, json, os, random, sys
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import e3_lib as E

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY"]
AX = "fp_hat_m1atr"
FLOOR = 0.45
OUT = {"axis": AX, "floor": FLOOR, "note": "March has no execution_fill_probability column; "
       "fp_hat_m1atr is the source formula recomputed from M1 bars for all three months"}

rows = {}
for m in MONTHS:
    rows[m] = [json.loads(l) for l in gzip.open(os.path.join(D, f"e3_slim_{m}.jsonl.gz"), "rt")]


def fdelta(sub, ax=AX, floor=FLOOR):
    lo = [r for r in sub if (r.get(ax) if r.get(ax) is not None else 9) < floor]
    hi = [r for r in sub if (r.get(ax) if r.get(ax) is not None else 9) >= floor]
    a = E.stats([r["fill_honest_walk_r"] for r in lo]); b = E.stats([r["fill_honest_walk_r"] for r in hi])
    if not a["n"] or not b["n"]:
        return {"n": len(sub), "n_below": a["n"], "n_above": b["n"], "delta": None, "t": None}
    sd = ((a["se"] or 0) ** 2 + (b["se"] or 0) ** 2) ** 0.5
    return {"n": len(sub), "n_below": a["n"], "below": a["mean"], "n_above": b["n"], "above": b["mean"],
            "delta": a["mean"] - b["mean"], "t": (a["mean"] - b["mean"]) / sd if sd else None,
            "zn_delta": E.mean([E.hz(r) for r in lo]) - E.mean([E.hz(r) for r in hi]),
            "below_share": a["n"] / len(sub)}


# --------------------------------------------------------------- 1. common-axis month table
for m in MONTHS:
    tk = [r for r in rows[m] if r["takeable"]]
    res = [r for r in rows[m] if r["born_state"] == "resting"]
    fr = [r for r in tk if r.get("entry_traded_prior_24h")]
    ff = [r for r in fr if r.get("is_first_emission")]
    OUT.setdefault("month_common_axis", {})[m] = {
        "n_pool": len(rows[m]), "n_takeable": len(tk), "n_resting": len(res),
        "takeable": fdelta(tk), "resting": fdelta(res), "fresh": fdelta(fr), "fresh_first": fdelta(ff),
        "bands_resting": E.band_table(res, lambda r: E.fb(r.get(AX))),
        "bands_takeable": E.band_table(tk, lambda r: E.fb(r.get(AX))),
    }

# --------------------------------------------------------------- 2. day-bootstrap interval
def boot(sub, iters=2000, seed=7):
    byday = collections.defaultdict(list)
    for r in sub:
        byday[r["decision_time_utc"][:10]].append(r)
    days = list(byday)
    rnd = random.Random(seed)
    vals = []
    for _ in range(iters):
        pick = [byday[rnd.choice(days)] for _ in days]
        flat = [r for v in pick for r in v]
        d = fdelta(flat)
        if d["delta"] is not None:
            vals.append(d["delta"])
    vals.sort()
    if not vals:
        return None
    return {"n_days": len(days), "p05": vals[int(0.05 * len(vals))], "p50": vals[len(vals) // 2],
            "p95": vals[int(0.95 * len(vals))], "share_positive": sum(1 for v in vals if v > 0) / len(vals)}


for m in MONTHS:
    tk = [r for r in rows[m] if r["takeable"]]
    ff = [r for r in tk if r.get("entry_traded_prior_24h") and r.get("is_first_emission")]
    OUT.setdefault("day_bootstrap", {})[m] = {"takeable": boot(tk), "fresh_first": boot(ff)}

# --------------------------------------------------------------- 3. boundary cuts, per month + pooled
def cuts(keyf, label, minn=150):
    tab = {}
    pooled = collections.defaultdict(list)
    for m in MONTHS:
        tk = [r for r in rows[m] if r["takeable"]]
        d = collections.defaultdict(list)
        for r in tk:
            d[str(keyf(r))].append(r)
            pooled[str(keyf(r))].append(r)
        for k, v in d.items():
            if len(v) < minn:
                continue
            tab.setdefault(k, {})[m] = fdelta(v)
    for k, v in pooled.items():
        if len(v) < minn:
            continue
        tab.setdefault(k, {})["POOLED"] = fdelta(v)
    OUT.setdefault("boundary", {})[label] = tab


cuts(lambda r: r.get("origin_family"), "family")
cuts(lambda r: r.get("symbol"), "symbol")
cuts(lambda r: r.get("session_bucket"), "session")
cuts(lambda r: r.get("decision_time_utc")[11:13], "utc_hour")
cuts(lambda r: r.get("decision_timeframe"), "decision_timeframe")
cuts(lambda r: r.get("born_state"), "born_state")

# --------------------------------------------------------------- 4. pooled 3-month headline
allrows = [r for m in MONTHS for r in rows[m]]
tk_all = [r for r in allrows if r["takeable"]]
OUT["pooled_3month"] = {
    "n_pool": len(allrows), "n_takeable": len(tk_all),
    "takeable": fdelta(tk_all),
    "resting": fdelta([r for r in allrows if r["born_state"] == "resting"]),
    "fresh_first": fdelta([r for r in tk_all if r.get("entry_traded_prior_24h") and r.get("is_first_emission")]),
    "bands_takeable": E.band_table(tk_all, lambda r: E.fb(r.get(AX))),
    "bands_resting": E.band_table([r for r in allrows if r["born_state"] == "resting"], lambda r: E.fb(r.get(AX))),
}
# floor sweep, pooled
for f in (0.15, 0.25, 0.35, 0.45, 0.55, 0.60, 0.70, 0.80, 0.90):
    OUT.setdefault("pooled_floor_sweep", {})[str(f)] = fdelta(tk_all, floor=f)

json.dump(OUT, open(os.path.join(D, "E3_CROSS_V1.json"), "w"), indent=1, default=str)

print(f"{'month':>6} {'nTk':>7} {'takeable delta':>15} {'t':>6} | {'resting':>9} {'t':>6} | {'fresh+first':>12} {'t':>6}")
for m in MONTHS:
    b = OUT["month_common_axis"][m]
    print(f"{m:>6} {b['n_takeable']:>7} {b['takeable']['delta']:>+15.4f} {b['takeable']['t']:>+6.2f} | "
          f"{b['resting']['delta']:>+9.4f} {(b['resting']['t'] or 0):>+6.2f} | "
          f"{b['fresh_first']['delta']:>+12.4f} {(b['fresh_first']['t'] or 0):>+6.2f}")
print("POOLED takeable:", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in OUT["pooled_3month"]["takeable"].items()})
print("bootstrap:", {m: {k: (round(v["p05"], 4), round(v["p50"], 4), round(v["p95"], 4), round(v["share_positive"], 3))
                         for k, v in d.items() if v} for m, d in OUT["day_bootstrap"].items()})
print("family (delta per month | pooled):")
for k, v in sorted(OUT["boundary"]["family"].items(), key=lambda kv: -(kv[1].get("POOLED", {}).get("delta") or -9)):
    s = " ".join(f"{m}:{(v[m]['delta'] if v.get(m) and v[m]['delta'] is not None else float('nan')):+.3f}" for m in MONTHS if m in v)
    p = v.get("POOLED", {})
    print(f"   {k:>32} {s}  POOLED {(p.get('delta') or 0):+.4f} t {(p.get('t') or 0):+.2f} n {p.get('n', 0)}")
