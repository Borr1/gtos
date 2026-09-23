"""e3 step 1 -- (a) reproduce L9-F2 on January with L9's own instrument,
                (b) validate the portable raw-M1 engine against the January working set.

If (b) passes, the same engine can be pointed at February / March / any month.
"""
import json, os, sys, collections
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import l9_lib as L
import e3_lib as E

OUT = {}

# ---------------------------------------------------------------- (a) reproduce
rows = L.load()
res = [r for r in rows if r["born_state"] == "resting"]
tk = [r for r in rows if r["takeable"]]
OUT["jan_l9_instrument"] = {
    "n_rows": len(rows), "n_resting": len(res), "n_takeable": len(tk),
    "fp_bands_resting": E.band_table(res, lambda r: E.fb(r.get("execution_fill_probability"))),
}
fp = lambda r: (r.get("execution_fill_probability") if r.get("execution_fill_probability") is not None else 9.0)
g = {t: v for t, v in L.groups(tk).items() if len(v) >= 5}
p1 = [sorted(v, key=fp)[0] for v in g.values()]
a1 = [sorted(v, key=lambda r: r["risk_finalizer_rank"])[0] for v in g.values()]
s1 = L.stats([r.get("fill_honest_walk_r") for r in p1])
sa = L.stats([r.get("fill_honest_walk_r") for r in a1])
OUT["jan_percycle"] = {"n_cycles": len(g), "pos1": s1["mean"], "pos1_se": s1["se"], "pos1_t": s1["t"],
                       "alloc1": sa["mean"], "delta": s1["mean"] - sa["mean"],
                       "pos1_zn": E.mean([E.hz(r) for r in p1]),
                       "alloc1_zn": E.mean([E.hz(r) for r in a1])}
prior = json.load(open(os.path.join(D, "L9_FPDECOMP_V1.json")))["decomp"]["RESTING"]
diffs = {}
for k, v in OUT["jan_l9_instrument"]["fp_bands_resting"].items():
    if k in prior:
        diffs[k] = {"n_mine": v["n"], "n_prior": prior[k]["n"],
                    "honest_mine": round(v["honest"], 6), "honest_prior": round(prior[k]["honest"], 6),
                    "abs_diff": round(abs(v["honest"] - prior[k]["honest"]), 9)}
OUT["repro_vs_L9_FPDECOMP"] = diffs
OUT["repro_exact"] = all(d["n_mine"] == d["n_prior"] and d["abs_diff"] < 1e-9 for d in diffs.values())

# ---------------------------------------------------------------- (b) validate engine
by_key = {(r["candidate_id"], r["decision_time_utc"]): r for r in rows}
n_ok = n_try = 0
mism_born = mism_fh = mism_which = mism_entry = 0
d_mkt = []
cmp_rows = []
for r in rows:
    row = {"symbol": r["symbol"], "decision_time_utc": r["decision_time_utc"],
           "entry_price": r["entry_price"], "stop_loss": r["stop_loss"], "side": r["side"],
           "policy_target_r": r.get("policy_target_r"),
           "opportunity_net_proxy_r": r.get("opportunity_net_proxy_r"), "cost_r": r.get("cost_r")}
    n_try += 1
    if not E.enrich(row, "202601", want_atr=False):
        continue
    n_ok += 1
    if row["born_state"] != r["born_state"]:
        mism_born += 1
    if r.get("mkt_r_prev_close") is not None:
        d_mkt.append(abs(row["mkt_r_prev_close"] - r["mkt_r_prev_close"]))
    if row["fill_honest_which_came_first"] != r.get("fill_honest_which_came_first"):
        mism_which += 1
    if abs((row["fill_honest_walk_r"] or 0) - (r.get("fill_honest_walk_r") or 0)) > 1e-6:
        mism_fh += 1
    if (row["bars_to_entry_touch"] or -1) != (r.get("bars_to_entry_touch") or -1):
        mism_entry += 1
d_mkt.sort()
OUT["engine_validation_january"] = {
    "n_pool": n_try, "n_enriched": n_ok,
    "born_state_mismatch": mism_born, "born_state_match_pct": 100.0 * (n_ok - mism_born) / n_ok,
    "mkt_r_max_abs_diff": d_mkt[-1] if d_mkt else None,
    "mkt_r_p999_abs_diff": d_mkt[int(0.999 * len(d_mkt))] if d_mkt else None,
    "fill_honest_which_mismatch": mism_which,
    "fill_honest_which_match_pct": 100.0 * (n_ok - mism_which) / n_ok,
    "fill_honest_walk_r_mismatch": mism_fh,
    "fill_honest_walk_r_match_pct": 100.0 * (n_ok - mism_fh) / n_ok,
    "bars_to_entry_touch_mismatch": mism_entry,
}
# pool-level means, mine vs theirs
mine = [None] * 0
json.dump(OUT, open(os.path.join(D, "E3_REPRO_V1.json"), "w"), indent=1, default=str)
print("REPRO EXACT:", OUT["repro_exact"])
for k, d in sorted(OUT["repro_vs_L9_FPDECOMP"].items()):
    print(f"  {k:>12} n {d['n_mine']:>5}/{d['n_prior']:<5} honest {d['honest_mine']:+.4f}/{d['honest_prior']:+.4f} diff {d['abs_diff']:.2e}")
print("percycle:", {k: (round(v, 5) if isinstance(v, float) else v) for k, v in OUT["jan_percycle"].items()})
print("engine:", {k: (round(v, 6) if isinstance(v, float) else v) for k, v in OUT["engine_validation_january"].items()})
