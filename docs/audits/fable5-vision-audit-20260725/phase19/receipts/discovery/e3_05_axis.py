"""e3 step 5 -- kill the reconstruction-error objection.

`fp_hat` is a reconstruction (Spearman 0.94 vs the real field). `dist_r` is EXACT: it is
|entry - market| / |entry - stop| measured off the same M1 bars, and it is the input to the
fill-probability formula's own risk_component. If the gradient is real it must show on the
exact axis too. This calibrates a dist_r threshold against the shipped 0.45 fp floor on
January, then applies that ONE threshold to all three months unchanged.
"""
import collections, gzip, json, os, sys
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import e3_lib as E

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY"]
rows = {m: [json.loads(l) for l in gzip.open(os.path.join(D, f"e3_slim_{m}.jsonl.gz"), "rt")] for m in MONTHS}
OUT = {}


def split_stats(lo, hi):
    a = E.stats([r["fill_honest_walk_r"] for r in lo]); b = E.stats([r["fill_honest_walk_r"] for r in hi])
    if not a["n"] or not b["n"]:
        return {"n_below": a["n"], "n_above": b["n"], "delta": None, "t": None}
    sd = ((a["se"] or 0) ** 2 + (b["se"] or 0) ** 2) ** 0.5
    return {"n_below": a["n"], "below": a["mean"], "n_above": b["n"], "above": b["mean"],
            "delta": a["mean"] - b["mean"], "t": (a["mean"] - b["mean"]) / sd if sd else None,
            "zn_below": E.mean([E.hz(r) for r in lo]), "zn_above": E.mean([E.hz(r) for r in hi]),
            "zn_delta": E.mean([E.hz(r) for r in lo]) - E.mean([E.hz(r) for r in hi]),
            "below_share": a["n"] / (a["n"] + b["n"])}


def by_dist(sub, thr):
    return ([r for r in sub if (r.get("dist_r") or -9) >= thr],
            [r for r in sub if (r.get("dist_r") or -9) < thr])


# --------------------------------------------------------- 1. calibrate on January
jan_tk = [r for r in rows["JAN"] if r["takeable"]]
real_excl = {(r["candidate_id"], r["decision_time_utc"]) for r in jan_tk
             if (r.get("execution_fill_probability") if r.get("execution_fill_probability") is not None else 9) < 0.45}
target_n = len(real_excl)
cand = sorted((r.get("dist_r") or -9) for r in jan_tk)
# dist_r threshold that excludes the same COUNT (the floor deletes the far tail)
thr = cand[len(cand) - target_n]
dist_excl = {(r["candidate_id"], r["decision_time_utc"]) for r in jan_tk if (r.get("dist_r") or -9) >= thr}
inter = len(real_excl & dist_excl)
OUT["calibration_january"] = {
    "n_takeable": len(jan_tk), "n_excluded_by_real_fp_0p45": target_n,
    "matched_dist_r_threshold": thr, "n_excluded_by_dist_r": len(dist_excl),
    "intersection": inter, "jaccard": inter / len(real_excl | dist_excl),
    "agreement_pct": 100.0 * inter / target_n}
THR = round(thr, 4)
OUT["dist_r_threshold_used"] = THR

# --------------------------------------------------------- 2. apply unchanged to all months
for m in MONTHS:
    tk = [r for r in rows[m] if r["takeable"]]
    lo, hi = by_dist(tk, THR)
    ff = [r for r in tk if r.get("entry_traded_prior_24h") and r.get("is_first_emission")]
    lo2, hi2 = by_dist(ff, THR)
    OUT.setdefault("month_dist_axis", {})[m] = {"takeable": split_stats(lo, hi),
                                                "fresh_first": split_stats(lo2, hi2)}
allt = [r for m in MONTHS for r in rows[m] if r["takeable"]]
lo, hi = by_dist(allt, THR)
OUT["pooled_dist_axis"] = split_stats(lo, hi)

# --------------------------------------------------------- 3. dist_r ladder, pooled
OUT["pooled_dist_bands"] = E.band_table(allt, lambda r: E.db(r.get("dist_r")))
for m in MONTHS:
    OUT.setdefault("month_dist_bands", {})[m] = E.band_table(
        [r for r in rows[m] if r["takeable"]], lambda r: E.db(r.get("dist_r")))

# --------------------------------------------------------- 4. boundary on the exact axis
def cut(keyf, label, minn=150):
    tab = {}
    pooled = collections.defaultdict(list)
    for m in MONTHS:
        d = collections.defaultdict(list)
        for r in rows[m]:
            if not r["takeable"]:
                continue
            d[str(keyf(r))].append(r)
            pooled[str(keyf(r))].append(r)
        for k, v in d.items():
            if len(v) < minn:
                continue
            lo, hi = by_dist(v, THR)
            tab.setdefault(k, {})[m] = split_stats(lo, hi)
    for k, v in pooled.items():
        if len(v) < minn:
            continue
        lo, hi = by_dist(v, THR)
        tab.setdefault(k, {})["POOLED"] = split_stats(lo, hi)
    OUT.setdefault("boundary_dist", {})[label] = tab


cut(lambda r: r.get("origin_family"), "family")
cut(lambda r: r.get("symbol"), "symbol")
cut(lambda r: r.get("session_bucket"), "session")

# --------------------------------------------------------- 5. the money question
def money(sub, label):
    n = len(sub)
    if not n:
        return
    hon = E.mean([r["fill_honest_walk_r"] for r in sub])
    zn = E.mean([E.hz(r) for r in sub])
    cost = E.mean([r.get("cost_r") or 0 for r in sub])
    spr = E.mean([r.get("spread_r") or 0 for r in sub])
    OUT.setdefault("money", {})[label] = {
        "n": n, "honest": hon, "zn": zn, "gross_pool": E.mean([r.get("gross_r") for r in sub]),
        "mean_cost_r_frozen": cost, "mean_spread_r": spr,
        "net_at_frozen": hon - cost,
        "net_at_spread_div_7p3": hon - (cost - spr * (1 - 1 / 7.3)),
        "net_at_spread_div_8p5": hon - (cost - spr * (1 - 1 / 8.5)),
        "zn_net_at_spread_div_7p3": zn - (cost - spr * (1 - 1 / 7.3)),
    }


money(allt, "ALL_takeable_3mo")
money(lo, "BELOW_floor_dist_axis")
money(hi, "ABOVE_floor_dist_axis")
for lab, f in (("dist>=1.0", 1.0), ("dist>=0.6", 0.6), ("dist>=0.35", 0.35), ("dist>=0.2", 0.2)):
    money([r for r in allt if (r.get("dist_r") or -9) >= f], lab)
# the strongest conditioned cell: the three limit families, below floor, fresh+first
fam3 = {"current_fvg_fill", "current_ob_retest", "current_breaker_re_entry"}
money([r for r in lo if r.get("origin_family") in fam3], "BELOW_floor_3limit_families")
money([r for r in lo if r.get("origin_family") in fam3 and r.get("entry_traded_prior_24h")
       and r.get("is_first_emission")], "BELOW_floor_3fam_FRESH_FIRST")
money([r for r in lo if r.get("session_bucket") in ("ny", "london")], "BELOW_floor_ny_london")

json.dump(OUT, open(os.path.join(D, "E3_AXIS_V1.json"), "w"), indent=1, default=str)

print("calibration:", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in OUT["calibration_january"].items()})
print(f"{'month':>6} {'nBelow':>7} {'below':>8} {'above':>8} {'delta':>8} {'t':>6} {'zn_d':>8} | fresh+first {'delta':>8} {'t':>6}")
for m in MONTHS:
    a = OUT["month_dist_axis"][m]["takeable"]; b = OUT["month_dist_axis"][m]["fresh_first"]
    print(f"{m:>6} {a['n_below']:>7} {a['below']:>+8.4f} {a['above']:>+8.4f} {a['delta']:>+8.4f} {a['t']:>+6.2f} {a['zn_delta']:>+8.4f} | "
          f"{(b['delta'] or 0):>+20.4f} {(b['t'] or 0):>+6.2f}")
p = OUT["pooled_dist_axis"]
print("POOLED:", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in p.items()})
print("dist bands pooled:")
t = OUT["pooled_dist_bands"]
print(f"{'band':>14} {'n':>6} {'honest':>8} {'t':>6} {'zn':>8} {'nof%':>5} {'resN':>6} {'resMean':>8} {'resWin%':>7} {'bEnt':>6}")
for k in sorted(t):
    v = t[k]
    print(f"{k:>14} {v['n']:>6} {v['honest']:>+8.4f} {(v['t'] or 0):>+6.2f} {v['zn']:>+8.4f} {v['pct_nofill']:>5.2f} "
          f"{v['resolved_n']:>6} {(v['resolved_mean'] or 0):>+8.4f} {100*(v['resolved_win'] or 0):>7.1f} {(v['bars_to_entry'] or 0):>6.1f}")
print("money:")
for k, v in OUT["money"].items():
    print(f"   {k:>32} n {v['n']:>6} hon {v['honest']:+.4f} zn {v['zn']:+.4f} cost {v['mean_cost_r_frozen']:.4f} "
          f"net@frozen {v['net_at_frozen']:+.4f} net@/7.3 {v['net_at_spread_div_7p3']:+.4f}")
