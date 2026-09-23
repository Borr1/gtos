"""e3 -- run the L9-F2 passivity instrument over ANY month's diagnostic pool.

usage: python3 e3_month.py <tag> <pool_path> <yyyymm> [fp_field|NONE]

Emits  E3_MONTH_<tag>_V1.json      every table
       e3_slim_<tag>.jsonl.gz      the enriched rows (slim) for later reuse
"""
import collections, gzip, json, os, random, sys
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import e3_lib as E

TAG, POOL, YM = sys.argv[1], sys.argv[2], sys.argv[3]
FPF = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] != "NONE" else None

SLIM = ["candidate_id", "decision_time_utc", "symbol", "side", "origin_family", "session_bucket",
        "route_session", "kill_zone", "risk_finalizer_rank", "entry_price", "stop_loss",
        "policy_target_r", "cost_r", "spread_r", "commission_r", "swap_cost_r",
        "opportunity_net_proxy_r", "final_blocker_class", "scheduler_materialization_status",
        "risk_per_trade_pct", "decision_timeframe", "utc_hour_bucket"]
DERIVED = ["risk_distance", "mkt_r_prev_close", "born_state", "takeable", "dist_r", "atr14_m1",
           "fp_hat_m1atr", "path_bars", "bars_to_entry_touch", "which_came_first",
           "fill_honest_which_came_first", "fill_honest_walk_r", "mfe_r", "mae_r", "gross_r",
           "policy_target_r_used", "entry_traded_prior_24h", "bars_since_entry_last_traded",
           "execution_fill_probability"]


def scoreable(r):
    return str(r.get("missed_opportunity_r_scoreability_status") or "") == "diagnostic_opportunity_r_scoreable"


rows = []
n_raw = n_score = n_bad = 0
for r in E.read_jsonl(POOL):
    n_raw += 1
    if not scoreable(r):
        continue
    n_score += 1
    # February's pool carries the KEY `side` with a NULL value and puts the direction in
    # `direction`; a `"side" not in r` test silently leaves it None. enrich() falls back
    # correctly, but the emitted slim column did not -- fixed here.
    r["side"] = r.get("side") or r.get("direction")
    if not E.enrich(r, YM):
        n_bad += 1
        continue
    if FPF:
        r["fp"] = r.get(FPF)
    else:
        r["fp"] = r.get("fp_hat_m1atr")
    rows.append({k: r.get(k) for k in SLIM + DERIVED + ["fp"]})
E.drop_cache()

# W0-F1 pseudo-replication: rank each candidate_id's emissions by decision time.
_by = collections.defaultdict(list)
for r in rows:
    _by[r["candidate_id"]].append(r)
for cid, v in _by.items():
    v.sort(key=lambda r: r["decision_time_utc"])
    for i, r in enumerate(v):
        r["setup_dup_rank"] = i + 1
        r["setup_dup_count"] = len(v)
        r["is_first_emission"] = (i == 0)

OUT = {"tag": TAG, "pool": POOL, "yyyymm": YM, "fp_field": FPF or "fp_hat_m1atr",
       "n_raw_ledger": n_raw, "n_diagnostic_scoreable": n_score, "n_unenrichable": n_bad,
       "n_rows": len(rows)}

# ------------------------------------------------------------- born census
bc = collections.defaultdict(list)
for r in rows:
    bc[r["born_state"]].append(r)
OUT["born_census"] = {k: {"n": len(v), "share": len(v) / len(rows),
                          "honest": E.mean([x["fill_honest_walk_r"] for x in v]),
                          "gross": E.mean([x["gross_r"] for x in v]),
                          "mean_fp": E.mean([x["fp"] for x in v])} for k, v in sorted(bc.items())}

res = [r for r in rows if r["born_state"] == "resting"]
tk = [r for r in rows if r["takeable"]]
OUT["n_resting"] = len(res)
OUT["n_takeable"] = len(tk)

# ------------------------------------------------------------- the gradient
OUT["fp_bands_resting"] = E.band_table(res, lambda r: E.fb(r.get("fp")))
OUT["fp_bands_takeable"] = E.band_table(tk, lambda r: E.fb(r.get("fp")))
OUT["dist_bands_resting"] = E.band_table(res, lambda r: E.db(r.get("dist_r")))
OUT["dist_bands_takeable"] = E.band_table(tk, lambda r: E.db(r.get("dist_r")))

# cliff test: fp < 0.60 vs >= 0.60 over resting
for lab, sub in (("resting", res), ("takeable", tk)):
    lo = [r for r in sub if (r.get("fp") or 9) < 0.60]
    hi = [r for r in sub if (r.get("fp") or 9) >= 0.60]
    a = E.stats([r["fill_honest_walk_r"] for r in lo]); b = E.stats([r["fill_honest_walk_r"] for r in hi])
    rl = [r for r in lo if r["fill_honest_which_came_first"] in ("stop", "target")]
    rh = [r for r in hi if r["fill_honest_which_came_first"] in ("stop", "target")]
    OUT.setdefault("cliff_060", {})[lab] = {
        "n_below": a["n"], "below": a["mean"], "n_above": b["n"], "above": b["mean"],
        "delta": (a["mean"] - b["mean"]) if a["n"] and b["n"] else None,
        "below_zn": E.mean([E.hz(r) for r in lo]), "above_zn": E.mean([E.hz(r) for r in hi]),
        "resolved_below": E.mean([r["fill_honest_walk_r"] for r in rl]),
        "resolved_above": E.mean([r["fill_honest_walk_r"] for r in rh]),
        "resolved_win_below": (sum(1 for r in rl if r["fill_honest_which_came_first"] == "target") / len(rl)) if rl else None,
        "resolved_win_above": (sum(1 for r in rh if r["fill_honest_which_came_first"] == "target") / len(rh)) if rh else None,
    }

# ------------------------------------------------------------- configured floors
for f in (0.25, 0.35, 0.45, 0.60, 0.80):
    lo = [r for r in tk if (r.get("fp") or 9) < f]
    hi = [r for r in tk if (r.get("fp") or 9) >= f]
    a = E.stats([r["fill_honest_walk_r"] for r in lo]); b = E.stats([r["fill_honest_walk_r"] for r in hi])
    if not a["n"] or not b["n"]:
        continue
    sd = ((a["se"] or 0) ** 2 + (b["se"] or 0) ** 2) ** 0.5
    OUT.setdefault("floor_deltas_takeable", {})[str(f)] = {
        "n_excluded": a["n"], "excluded_R": a["mean"], "n_kept": b["n"], "kept_R": b["mean"],
        "delta": a["mean"] - b["mean"], "t": (a["mean"] - b["mean"]) / sd if sd else None,
        "zn_delta": E.mean([E.hz(r) for r in lo]) - E.mean([E.hz(r) for r in hi]),
        "excluded_share": a["n"] / len(tk)}

# ------------------------------------------------------------- per-cycle rule
fp = lambda r: (r.get("fp") if r.get("fp") is not None else 9.0)
for ms in (2, 3, 5, 8, 12):
    g = {t: v for t, v in E.groups(tk).items() if len(v) >= ms}
    if not g:
        continue
    p1 = [sorted(v, key=fp)[0] for v in g.values()]
    a1 = [sorted(v, key=lambda r: (r["risk_finalizer_rank"] if r["risk_finalizer_rank"] is not None else 1e9))[0]
          for v in g.values()]
    gm = [E.mean([r["fill_honest_walk_r"] for r in v]) for v in g.values()]
    sp = E.stats([r["fill_honest_walk_r"] for r in p1]); sa = E.stats([r["fill_honest_walk_r"] for r in a1])
    OUT.setdefault("percycle", {})[f"minsize{ms}"] = {
        "n_cycles": len(g), "pos1": sp["mean"], "pos1_se": sp["se"], "pos1_t": sp["t"],
        "pos1_zn": E.mean([E.hz(r) for r in p1]), "alloc1": sa["mean"],
        "alloc1_zn": E.mean([E.hz(r) for r in a1]), "random": E.stats(gm)["mean"],
        "delta_pos1_minus_alloc1": sp["mean"] - sa["mean"],
        "delta_zn": E.mean([E.hz(r) for r in p1]) - E.mean([E.hz(r) for r in a1])}

# permutation, minsize 5
g = {t: v for t, v in E.groups(tk).items() if len(v) >= 5}
if g:
    obs = E.mean([sorted(v, key=fp)[0]["fill_honest_walk_r"] for v in g.values()])
    rnd = random.Random(99)
    null = [E.mean([rnd.choice(v)["fill_honest_walk_r"] or 0.0 for v in g.values()]) for _ in range(2000)]
    ge = sum(1 for x in null if x >= obs)
    OUT["permutation"] = {"n_cycles": len(g), "observed_pos1": obs, "iters": 2000,
                          "n_null_ge_obs": ge, "p_one_sided": (ge + 1) / 2001.0,
                          "null_mean": sum(null) / len(null), "null_max": max(null)}
    # by day
    byday = collections.defaultdict(list)
    for v in g.values():
        r = sorted(v, key=fp)[0]
        byday[r["decision_time_utc"][:10]].append(r)
    dd = {k: E.mean([r["fill_honest_walk_r"] for r in v]) for k, v in sorted(byday.items())}
    vals = sorted(dd.values())
    OUT["pos1_by_day"] = {k: {"n": len(byday[k]), "honest": v} for k, v in dd.items()}
    OUT["pos1_day_positivity"] = {"days": len(vals), "positive": sum(1 for x in vals if x > 0),
                                  "median": vals[len(vals) // 2] if vals else None}

# ------------------------------------------------------------- L9's own next test:
# separate a FAR limit (market never got there) from a STALE limit (market was there and left)
def floor_delta(sub, floor=0.45):
    lo = [r for r in sub if (r.get("fp") or 9) < floor]
    hi = [r for r in sub if (r.get("fp") or 9) >= floor]
    a = E.stats([r["fill_honest_walk_r"] for r in lo]); b = E.stats([r["fill_honest_walk_r"] for r in hi])
    if not a["n"] or not b["n"]:
        return {"n_below": a["n"], "n_above": b["n"], "delta": None}
    sd = ((a["se"] or 0) ** 2 + (b["se"] or 0) ** 2) ** 0.5
    return {"n": len(sub), "n_below": a["n"], "below": a["mean"], "n_above": b["n"], "above": b["mean"],
            "delta": a["mean"] - b["mean"], "t": (a["mean"] - b["mean"]) / sd if sd else None,
            "zn_delta": E.mean([E.hz(r) for r in lo]) - E.mean([E.hz(r) for r in hi])}


FRESH = lambda r: bool(r.get("entry_traded_prior_24h"))
splits = {
    "ALL_takeable": tk,
    "FRESH_entry_traded_24h": [r for r in tk if FRESH(r)],
    "STALE_entry_untraded_24h": [r for r in tk if not FRESH(r)],
    "FIRST_EMISSION": [r for r in tk if r.get("is_first_emission")],
    "REEMISSION": [r for r in tk if not r.get("is_first_emission")],
    "FRESH_AND_FIRST": [r for r in tk if FRESH(r) and r.get("is_first_emission")],
    "RESTING_only": res,
    "RESTING_FRESH": [r for r in res if FRESH(r)],
    "RESTING_STALE": [r for r in res if not FRESH(r)],
    "RESTING_FRESH_FIRST": [r for r in res if FRESH(r) and r.get("is_first_emission")],
}
OUT["staleness_splits_floor045"] = {k: floor_delta(v) for k, v in splits.items() if v}
OUT["staleness_census"] = {
    "takeable_n": len(tk),
    "fresh_n": sum(1 for r in tk if FRESH(r)),
    "stale_n": sum(1 for r in tk if not FRESH(r)),
    "stale_share": sum(1 for r in tk if not FRESH(r)) / len(tk) if tk else None,
    "fresh_honest": E.mean([r["fill_honest_walk_r"] for r in tk if FRESH(r)]),
    "stale_honest": E.mean([r["fill_honest_walk_r"] for r in tk if not FRESH(r)]),
    "reemission_share": sum(1 for r in tk if not r.get("is_first_emission")) / len(tk) if tk else None,
}
# gradient inside the FRESH resting book only -- the decisive table for L9's next test
OUT["fp_bands_resting_FRESH"] = E.band_table([r for r in res if FRESH(r)], lambda r: E.fb(r.get("fp")))
OUT["fp_bands_resting_STALE"] = E.band_table([r for r in res if not FRESH(r)], lambda r: E.fb(r.get("fp")))
OUT["fp_bands_resting_FRESH_FIRST"] = E.band_table(
    [r for r in res if FRESH(r) and r.get("is_first_emission")], lambda r: E.fb(r.get("fp")))

# per-cycle rule on the fresh+first population
for lab, sub in (("FRESH", [r for r in tk if FRESH(r)]),
                 ("FRESH_AND_FIRST", [r for r in tk if FRESH(r) and r.get("is_first_emission")]),
                 ("FIRST_EMISSION", [r for r in tk if r.get("is_first_emission")])):
    g2 = {t: v for t, v in E.groups(sub).items() if len(v) >= 5}
    if not g2:
        continue
    p1 = [sorted(v, key=fp)[0] for v in g2.values()]
    a1 = [sorted(v, key=lambda r: (r["risk_finalizer_rank"] if r["risk_finalizer_rank"] is not None else 1e9))[0]
          for v in g2.values()]
    sp = E.stats([r["fill_honest_walk_r"] for r in p1]); sa = E.stats([r["fill_honest_walk_r"] for r in a1])
    OUT.setdefault("percycle_splits", {})[lab] = {
        "n_cycles": len(g2), "pos1": sp["mean"], "pos1_t": sp["t"], "alloc1": sa["mean"],
        "delta": sp["mean"] - sa["mean"], "pos1_zn": E.mean([E.hz(r) for r in p1]),
        "delta_zn": E.mean([E.hz(r) for r in p1]) - E.mean([E.hz(r) for r in a1])}

# how well does the portable axis stand in for the real field?
have = [r for r in rows if r.get("execution_fill_probability") is not None]
if have:
    import math as _m
    def _rho(pairs):
        pairs = [(a, b) for a, b in pairs if a is not None and b is not None]
        n = len(pairs)
        if n < 3:
            return None
        def rk(v):
            o = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0] * len(v); i = 0
            while i < len(o):
                j = i
                while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                    j += 1
                a = (i + j) / 2.0 + 1.0
                for k in range(i, j + 1):
                    r[o[k]] = a
                i = j + 1
            return r
        x = rk([p[0] for p in pairs]); y = rk([p[1] for p in pairs])
        mx = sum(x) / n; my = sum(y) / n
        num = sum((a - mx) * (b - my) for a, b in zip(x, y))
        dx = _m.sqrt(sum((a - mx) ** 2 for a in x)); dy = _m.sqrt(sum((b - my) ** 2 for b in y))
        return num / (dx * dy) if dx and dy else None
    hres = [r for r in have if r["born_state"] == "resting"]
    OUT["axis_calibration"] = {
        "n": len(have), "n_resting": len(hres),
        "rho_fp_vs_dist_r_all": _rho([(r["execution_fill_probability"], r["dist_r"]) for r in have]),
        "rho_fp_vs_dist_r_resting": _rho([(r["execution_fill_probability"], r["dist_r"]) for r in hres]),
        "rho_fp_vs_fphat_all": _rho([(r["execution_fill_probability"], r["fp_hat_m1atr"]) for r in have]),
        "rho_fp_vs_fphat_resting": _rho([(r["execution_fill_probability"], r["fp_hat_m1atr"]) for r in hres]),
        "mean_fp": E.mean([r["execution_fill_probability"] for r in have]),
        "mean_fphat": E.mean([r["fp_hat_m1atr"] for r in have]),
        "mean_abs_err": E.mean([abs(r["execution_fill_probability"] - r["fp_hat_m1atr"]) for r in have]),
    }
    # the same gradient measured on fp_hat, so the March numbers are comparable
    OUT["fphat_bands_resting"] = E.band_table(hres, lambda r: E.fb(r.get("fp_hat_m1atr")))

# ------------------------------------------------------------- boundary cuts
def cut(keyf, label, floor=0.45):
    d = collections.defaultdict(list)
    for r in tk:
        d[str(keyf(r))].append(r)
    t = {}
    for k, v in sorted(d.items()):
        lo = [r for r in v if (r.get("fp") or 9) < floor]
        hi = [r for r in v if (r.get("fp") or 9) >= floor]
        a = E.stats([r["fill_honest_walk_r"] for r in lo]); b = E.stats([r["fill_honest_walk_r"] for r in hi])
        if not a["n"] or not b["n"]:
            t[k] = {"n": len(v), "n_below": a["n"], "n_above": b["n"], "delta": None}
            continue
        sd = ((a["se"] or 0) ** 2 + (b["se"] or 0) ** 2) ** 0.5
        t[k] = {"n": len(v), "n_below": a["n"], "below": a["mean"], "n_above": b["n"], "above": b["mean"],
                "delta": a["mean"] - b["mean"], "t": (a["mean"] - b["mean"]) / sd if sd else None,
                "zn_delta": E.mean([E.hz(r) for r in lo]) - E.mean([E.hz(r) for r in hi])}
    OUT.setdefault("boundary_floor045", {})[label] = t


cut(lambda r: r.get("origin_family"), "family")
cut(lambda r: r.get("symbol"), "symbol")
cut(lambda r: r.get("session_bucket"), "session")
cut(lambda r: r.get("decision_time_utc")[11:13], "utc_hour")
cut(lambda r: r.get("decision_time_utc")[:10], "day")

json.dump(OUT, open(os.path.join(D, f"E3_MONTH_{TAG}_V1.json"), "w"), indent=1, default=str)
with gzip.open(os.path.join(D, f"e3_slim_{TAG}.jsonl.gz"), "wt") as fh:
    for r in rows:
        fh.write(json.dumps(r, default=str) + "\n")

print(f"[{TAG}] raw {n_raw} scoreable {n_score} enriched {len(rows)} bad {n_bad} "
      f"resting {len(res)} takeable {len(tk)}")
print(" born:", {k: (v["n"], round(v["honest"], 4)) for k, v in OUT["born_census"].items()})
print(" cliff resting:", {k: (round(v, 4) if isinstance(v, float) else v)
                          for k, v in OUT["cliff_060"]["resting"].items()})
print(" floors:", {k: (v["n_excluded"], round(v["delta"], 4), round(v["t"] or 0, 2))
                   for k, v in OUT.get("floor_deltas_takeable", {}).items()})
print(" percycle:", {k: (v["n_cycles"], round(v["pos1"], 4), round(v["delta_pos1_minus_alloc1"], 4))
                     for k, v in OUT.get("percycle", {}).items()})
print(" perm:", {k: (round(v, 5) if isinstance(v, float) else v) for k, v in OUT.get("permutation", {}).items()})
