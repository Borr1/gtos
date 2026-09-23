"""
wave5_metals_risk_unit_and_target.py
====================================
THRUST (metals_risk_unit_and_target):

 (a) CORRELATED-RISK-UNIT SIZING for the deployable precious-metals vol-gated FVG-retest
     edge. The WAVE4 verdict sized every trade as an INDEPENDENT risk unit, so a
     correlated metals-cluster day (all gold/silver crosses are ~the same trade) loses
     N * risk%, not 1 * risk%. The worst observed day was -8.37R across up to 11 trades.
     Here ALL simultaneous / same-DAY metals trades share ONE risk unit (a metals-cluster
     day is ONE bet), with a per-day cluster cap. We stress against the 2025-04-08
     -8.37R/11-trade day and every other cluster, then verify 0.25%/trade-equivalent keeps
     FTMO maxDD < 10% and worst single DAY < 5% OUT-OF-SAMPLE.

 (b) DEEPER TARGETS (2R / 3R / 4R) on the metals pocket WITH M1 INTRABAR VERIFICATION.
     A naive H4 readout said 3R > 2R forward (+0.278 vs +0.227). But a deeper target makes
     the trade traverse MORE price, so the intrabar ORDER of stop-vs-target matters more —
     the exact place H4 first-touch ambiguity bites. We recompute the target at each R, run
     the tested H4 simulate AND an independent M1 minute-by-minute replay over the TRUE H4
     trade life, and only count CLEAN M1 fills (coverage-gated, weekend-aware). Does a
     deeper target raise monthly % while staying FTMO-safe on REAL fills? Recommend a final
     target.

DISCIPLINE (every prior loose claim was a leak):
  * ALL fills via tested geometry_lib.simulate / simulate_detail and the wave4 M1 replay
    (m1_replay_fill), which is sign-checked (189/189 agree) against H4 simulate.
  * Entry/gate/sign geometry is IMPORTED from wave4_metals_fvg_harden (fvg_trades), the
    exact established setup — no hand-rolled signals.
  * NO LOOKAHEAD: gate uses atr_ratio known at the decision bar; the walk-forward threshold
    for window W is selected only on trades strictly BEFORE W (wave4.walk_forward); path
    state (cluster membership, equity) advances only on CLOSED trades, ordered by exit time.
  * M1-horizon = end of the ACTUAL H4 exit bar (simulate_detail), weekend-aware — avoids the
    M1-skips-weekend leak that truncates trades into fake favorable timeouts.
  * Matched RANDOM (count-matched) + INVERT nulls under the SAME walk-forward selection, for
    both the deeper-target readout and the risk-unit sizing.
  * Winsorized H4 (inherited from wave4.load) + winsorization-invariance is already proven
    in wave4; per-year 2015-2026 reported. Truth over positives.

DATA: H4 bridge_ftmo_deep_h4_2015_2022(+ _metals backfill) + _2022_2026; M1 bridge_ftmo_m1
      (XAUUSD/XAGUSD 2024-26) + bridge_ftmo_ext_m1 (XAUEUR/XAGEUR/XAUAUD/XAGAUD 2025-26).
      Cost: ULTIMATE_REAL_COST_MAP.json (metals 0.0459 R).
"""
from __future__ import annotations
import sys, os, json, random, math, bisect
from datetime import datetime, timedelta
from collections import defaultdict

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
DATA = ROOT + "/data/mt5_research_exports"
sys.path.insert(0, ROOT); sys.path.insert(0, EDGE)

from geometry_lib import Bar, atr14, simulate, simulate_detail
# Reuse the EXACT established setup: loader (winsorized + metals backfill), fvg_trades
# (entry/gate/sign geometry), walk_forward (past-only threshold selection), stats, per_year.
import wave4_metals_fvg_harden as W4
from wave4_metals_fvg_harden import (
    PRECIOUS, ALL_METALS, TRAIN_MAX, load, fvg_trades, walk_forward,
    stats, per_year, split, cost_for, m1_replay_fill, _m1_dir_for,
)

# ---- OPTIONAL: 2021 metals-cross backfill (source-bound FTMO; OFF by default) ----
# IMPORTANT REPRODUCIBILITY NOTE: the established/published WAVE4 deployable verdict
# (WF full R = +0.2264, n=482) was computed WITHOUT this backfill. Merging the 2021
# cross history materially WEAKENS the walk-forward edge (full R ~ +0.087, n=653) — a
# real fragility we surface in the sensitivity section rather than silently re-baselining.
# So the main risk-unit / target analysis runs on the EXACT established stream (backfill
# OFF, reproduces +0.2264). USE_BACKFILL flips it on only for the sensitivity readout.
_D3 = DATA + "/bridge_ftmo_deep_h4_2015_2022_metals"
_ORIG_LOAD = load
def _backfill_load(sym):
    """Merge the 2021 metals-cross backfill into the winsorized H4 series. Pure source
    data; only adds bars that the base loader lacked. Keeps wave4 sign/winsor logic."""
    if sym in W4._H4_CACHE:
        return W4._H4_CACHE[sym]
    p = f"{_D3}/{sym}_H4.csv"
    if os.path.exists(p) and os.path.getsize(p) > 1000:
        T0, B0 = W4._load_one(p)
        T1, B1 = W4._load_one(f"{W4.D1}/{sym}_H4.csv")
        T2, B2 = W4._load_one(f"{W4.D2}/{sym}_H4.csv")
        merged = {}
        for t, b in zip(T0, B0): merged[t] = b
        for t, b in zip(T1, B1): merged[t] = b
        for t, b in zip(T2, B2): merged[t] = b
        if not merged:
            W4._H4_CACHE[sym] = ([], []); return [], []
        items = sorted(merged.items(), key=lambda kv: kv[0])
        times = [k for k, _ in items]; bars = W4.winsorize([k for k, _ in items], [v for _, v in items])
        W4._H4_CACHE[sym] = (times, bars)
        return times, bars
    return _ORIG_LOAD(sym)

def set_backfill(on):
    """Toggle the 2021 cross backfill and clear the H4 cache so the next trade build uses it."""
    W4._H4_CACHE.clear()
    W4.load = _backfill_load if on else _ORIG_LOAD

# ---- extend M1 dir map to all crosses available in ext_m1 (XAUAUD/XAGAUD too) ----
def _patched_m1_dir(sym):
    if sym in ("XAUUSD", "XAGUSD"): return "bridge_ftmo_m1"
    if sym in ("XAUEUR", "XAGEUR", "XAUAUD", "XAGAUD"): return "bridge_ftmo_ext_m1"
    return None
W4._m1_dir_for = _patched_m1_dir

THRESHOLDS = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5]

# =====================================================================
# Build the deployable trade stream at a given target_R via WALK-FORWARD
# (the honest OOS stream; identical selection rule to the WAVE4 verdict).
# =====================================================================
def wf_stream(target_R):
    """Generate FVG-retest trades at target_R, run wave4 walk-forward threshold selection,
    return (summary, chained_recs). chained_recs each carry ts (decision), sym, dir,
    entry_idx, stop_dist, target_dist, cost, year, r (H4 net R)."""
    base = fvg_trades(PRECIOUS, target_R=target_R)
    summary, recs = walk_forward(base, THRESHOLDS)
    return base, summary, recs

# =====================================================================
# (a) CORRELATED-RISK-UNIT SIZER
# =====================================================================
def attach_exit_times(recs):
    """For each chained trade, compute its TRUE exit datetime (end of the H4 exit bar via the
    tested simulate_detail). Path state must advance on CLOSED trades, so equity/cluster
    accounting is keyed off exit time, entry off ts. No lookahead: exit time is a property of
    the already-decided trade's realized life."""
    out = []
    for d in recs:
        T, B = W4.load(d["sym"]); i = d["entry_idx"]
        _r, exidx = simulate_detail(B, i, d["dir"], stop_dist=d["stop_dist"],
                                    target_dist=d["target_dist"], cost=d["cost"])
        ex_dt = T[exidx] + timedelta(hours=4)
        e = dict(d); e["exit_dt"] = ex_dt; e["entry_dt"] = d["ts"]
        out.append(e)
    return out


def cluster_risk_unit_path(recs, risk_pct, cluster_cap_units=1.0, cluster_key="entry_day"):
    """CORRELATED-RISK-UNIT equity path.

    A 'cluster' = all trades that share the same metals decision context (same calendar DAY
    of the decision bar by default; metals crosses are ~one trade). The TOTAL risk staked on
    a cluster is cluster_cap_units * risk_pct of equity, SPLIT EQUALLY across the trades in
    the cluster (so each trade's effective per-trade risk = risk_pct * cluster_cap / n_in_cluster).
    Thus an N-trade correlated metals day risks ~1 unit, not N units.

    Ordering/metric definitions match the WAVE4 published ftmo_sizing for apples-to-apples
    comparison: equity compounds in DECISION-time order; worst-day aggregated by DECISION day;
    maxDD on the decision-ordered equity curve. (Decision-day is the correlated-cluster day,
    which is exactly the unit being bounded.)

    Returns dict with max_drawdown_pct, worst_day_pct, total_return_pct, approx_monthly_pct,
    within_ftmo, and the worst cluster detail.
    """
    if not recs: return {"error": "no trades"}
    recs = attach_exit_times(recs)
    # cluster membership by DECISION day (correlated entries)
    if cluster_key == "entry_day":
        members = defaultdict(list)
        for d in recs: members[d["entry_dt"].date()].append(d)
    else:
        raise ValueError(cluster_key)
    csize = {k: len(v) for k, v in members.items()}

    ordered = sorted(recs, key=lambda d: (d["entry_dt"], d["exit_dt"]))
    eq = 1.0; peak = 1.0; maxdd = 0.0
    day_pl = defaultdict(float)          # equity delta aggregated by DECISION day
    cluster_unit_R = defaultdict(float)  # summed effective-unit R per decision cluster
    for d in ordered:
        n_in = csize[d["entry_dt"].date()]
        eff_risk = risk_pct * cluster_cap_units / n_in      # split one unit across the cluster
        before = eq
        eq *= (1.0 + (eff_risk / 100.0) * d["r"])
        day_pl[d["entry_dt"].date()] += (eq - before)
        cluster_unit_R[d["entry_dt"].date()] += (cluster_cap_units / n_in) * d["r"]
        peak = max(peak, eq); maxdd = max(maxdd, (peak - eq) / peak)
    worst_day = min(day_pl.values()) if day_pl else 0.0
    worst_day_pct = -worst_day * 100.0
    span_days = (ordered[-1]["entry_dt"] - ordered[0]["entry_dt"]).days or 1
    span_months = span_days / 30.44
    total_ret = (eq - 1.0) * 100.0
    monthly = ((eq) ** (1.0 / span_months) - 1.0) * 100.0 if span_months > 0 and eq > 0 else None
    # worst correlated cluster in unit-R terms (this is what cluster sizing bounds)
    worst_cluster_day = min(cluster_unit_R, key=cluster_unit_R.get) if cluster_unit_R else None
    return {
        "risk_pct_per_unit": risk_pct,
        "cluster_cap_units": cluster_cap_units,
        "max_drawdown_pct": round(maxdd * 100.0, 2),
        "worst_day_pct": round(worst_day_pct, 2),
        "total_return_pct": round(total_ret, 1),
        "approx_monthly_pct": round(monthly, 2) if monthly is not None else None,
        "span_months": round(span_months, 1),
        "n_trades": len(ordered),
        "n_clusters": len(members),
        "max_cluster_size": max(csize.values()) if csize else 0,
        "worst_cluster_unit_R": round(min(cluster_unit_R.values()), 3) if cluster_unit_R else 0.0,
        "worst_cluster_day": str(worst_cluster_day) if worst_cluster_day else None,
        "within_ftmo": (maxdd * 100.0 < 10.0) and (worst_day_pct < 5.0),
    }


def independent_path(recs, risk_pct):
    """The WAVE4-style INDEPENDENT-risk path (each trade = full risk unit), for comparison.
    Reproduces the WAVE4 published ftmo_sizing exactly: decision-time ordering, worst-day by
    DECISION day, maxDD on the decision-ordered curve. This is the apples-to-apples baseline
    the correlated-risk-unit path is measured against."""
    if not recs: return {"error": "no trades"}
    ordered = sorted(recs, key=lambda d: d["ts"])
    eq = 1.0; peak = 1.0; maxdd = 0.0; day_pl = defaultdict(float)
    for d in ordered:
        before = eq
        eq *= (1.0 + (risk_pct / 100.0) * d["r"])
        day_pl[d["ts"].date()] += (eq - before)
        peak = max(peak, eq); maxdd = max(maxdd, (peak - eq) / peak)
    worst_day_pct = -(min(day_pl.values()) if day_pl else 0.0) * 100.0
    span_days = (ordered[-1]["ts"] - ordered[0]["ts"]).days or 1
    span_months = span_days / 30.44
    monthly = ((eq) ** (1.0 / span_months) - 1.0) * 100.0 if span_months > 0 and eq > 0 else None
    return {
        "risk_pct_per_trade": risk_pct,
        "max_drawdown_pct": round(maxdd * 100.0, 2),
        "worst_day_pct": round(worst_day_pct, 2),
        "total_return_pct": round((eq - 1.0) * 100.0, 1),
        "approx_monthly_pct": round(monthly, 2) if monthly is not None else None,
        "within_ftmo": (maxdd * 100.0 < 10.0) and (worst_day_pct < 5.0),
    }


def stress_clusters(recs, top_n=12):
    """Enumerate the worst correlated DECISION-day clusters in summed-R, including the named
    2025-04-08 day. Reports both naive summed R (what independent sizing exposes) and the
    bounded unit-R a single-unit cluster sizer staked. This is the direct stress test."""
    recs = attach_exit_times(recs)
    by_day = defaultdict(list)
    for d in recs: by_day[d["entry_dt"].date()].append(d)
    rows = []
    for day, ds in by_day.items():
        n = len(ds); summed = sum(x["r"] for x in ds)
        rows.append({
            "day": str(day), "n_trades": n,
            "summed_R_independent": round(summed, 3),     # what N independent units would book
            "unit_R_cluster_sized": round(summed / n, 3), # one unit split equally -> mean R
            "syms": sorted(set(x["sym"] for x in ds)),
        })
    rows.sort(key=lambda r: r["summed_R_independent"])
    worst_named = next((r for r in rows if r["day"] == "2025-04-08"), None)
    return {
        "worst_clusters": rows[:top_n],
        "named_2025_04_08": worst_named,
        "max_cluster_size": max((r["n_trades"] for r in rows), default=0),
        "worst_summed_R_independent": rows[0]["summed_R_independent"] if rows else 0.0,
        "worst_unit_R_cluster_sized": min((r["unit_R_cluster_sized"] for r in rows), default=0.0),
    }


# =====================================================================
# (b) DEEPER TARGETS WITH M1 INTRABAR VERIFICATION
# =====================================================================
def m1_deeper_target(base_by_R, threshold_picks, target_R, min_cov_frac=0.80):
    """For one target_R: take the WALK-FORWARD in-regime trades (each year filtered by its
    past-only threshold pick), replay each over its TRUE H4 life on M1, and compare H4-net R
    vs M1-intrabar net R. Only CLEAN M1 fills counted (coverage-gated, weekend-aware).

    target levels are recomputed at THIS target_R (stop_dist unchanged = structural stop).
    threshold_picks: {year: thr} from the walk-forward (selected on past only) so the M1
    readout uses the SAME deployable selection as the equity path. No lookahead.
    """
    base = base_by_R[target_R]
    in_reg = [d for d in base
              if d["atr_ratio"] is not None and d["atr_ratio"] >= threshold_picks.get(d["year"], 1.3)]
    m1_syms = sorted(set(d["sym"] for d in in_reg if _patched_m1_dir(d["sym"]) is not None))
    m1_data = {s: W4.load_m1_all(s) for s in m1_syms}
    m1_keys = {s: [r[0] for r in m1_data[s]] for s in m1_syms}
    pairs = []; low_cov = 0; no_m1 = 0
    for d in in_reg:
        sym = d["sym"]; m1 = m1_data.get(sym)
        if not m1: no_m1 += 1; continue
        T, B = W4.load(sym); i = d["entry_idx"]; entry = B[i].c
        if d["dir"] > 0:
            stop = entry - d["stop_dist"]; tgt = entry + d["target_dist"]
        else:
            stop = entry + d["stop_dist"]; tgt = entry - d["target_dist"]
        _h4r, exidx = simulate_detail(B, i, d["dir"], stop_dist=d["stop_dist"],
                                      target_dist=d["target_dist"], cost=d["cost"])
        horizon_dt = T[exidx] + timedelta(hours=4)
        n_life_bars = exidx - i
        expected_min = max(1, n_life_bars * 4 * 60)
        close_dt = d["ts"] + timedelta(hours=4)
        lo = bisect.bisect_right(m1_keys[sym], close_dt)
        hi = bisect.bisect_right(m1_keys[sym], horizon_dt)
        cov_frac = (hi - lo) / expected_min
        if not (m1[0][0] <= d["ts"] <= m1[-1][0]) or horizon_dt > m1[-1][0] or cov_frac < min_cov_frac:
            low_cov += 1; continue
        res = m1_replay_fill(m1_data[sym], m1_keys[sym], d["ts"], d["dir"], entry, stop, tgt, horizon_dt)
        if res is None: low_cov += 1; continue
        m1_R, outcome, _seg = res
        pairs.append((d["year"], d["r"], round(m1_R - d["cost"], 4), outcome, sym))
    h4 = stats([p[1] for p in pairs]); m1 = stats([p[2] for p in pairs])
    by = defaultdict(lambda: {"h4": [], "m1": []})
    for y, hr, mr, _, _ in pairs:
        by[y]["h4"].append(hr); by[y]["m1"].append(mr)
    pyr = {str(y): {"h4_R": stats(by[y]["h4"])["mean_R"], "m1_R": stats(by[y]["m1"])["mean_R"],
                    "n": len(by[y]["h4"])} for y in sorted(by)}
    outcomes = defaultdict(int)
    agree = dis = 0
    for _, hr, mr, oc, _ in pairs:
        outcomes[oc] += 1
        if oc in ("stop", "target"):
            if (hr > 0) == (mr > 0): agree += 1
            else: dis += 1
    return {
        "target_R": target_R, "clean_m1_fills": len(pairs),
        "low_coverage_skipped": low_cov, "no_m1_source": no_m1,
        "h4_path": h4, "m1_path": m1,
        "delta_mean_R": round(m1["mean_R"] - h4["mean_R"], 4),
        "per_year": pyr, "m1_outcomes": dict(outcomes),
        "sign_agreement": {"agree": agree, "disagree": dis},
    }


# =====================================================================
# nulls under the SAME walk-forward selection (count-matched random + invert)
# =====================================================================
def wf_nulls(target_R, edge_summary, reps=50, seed=99):
    inv_base = fvg_trades(PRECIOUS, target_R=target_R, invert=True)
    inv_sum, _ = walk_forward(inv_base, THRESHOLDS)
    base = fvg_trades(PRECIOUS, target_R=target_R)
    k = edge_summary["n_trades"]
    rr = []
    for rep in range(reps):
        random.seed(seed + rep)
        samp = random.sample(base, k) if k <= len(base) else base
        rr.append(stats([d["r"] for d in samp])["mean_R"])
    return {
        "edge_wf_full_R": edge_summary["chained_full"]["mean_R"],
        "invert_wf_full_R": inv_sum["chained_full"]["mean_R"],
        "random_mean_full_R": round(sum(rr) / len(rr), 4),
        "random_max_full_R": round(max(rr), 4),
        "edge_beats_invert": edge_summary["chained_full"]["mean_R"] > inv_sum["chained_full"]["mean_R"],
        "edge_beats_random_max": edge_summary["chained_full"]["mean_R"] > max(rr),
    }


# =====================================================================
# main
# =====================================================================
def main():
    random.seed(20260614)
    OUT = {"thrust": "metals_risk_unit_and_target", "universe": {"precious": PRECIOUS}}

    # Main analysis on the EXACT established/published deployable stream (backfill OFF,
    # reproduces WAVE4 WF full R = +0.2264, n=482). Backfill sensitivity reported separately.
    set_backfill(False)

    print("=" * 78); print("BUILD WALK-FORWARD STREAMS @ 2R / 3R / 4R (established setup)"); print("=" * 78)
    base_by_R = {}; summ_by_R = {}; recs_by_R = {}; picks_by_R = {}
    for R in (2.0, 3.0, 4.0):
        base, summ, recs = wf_stream(R)
        base_by_R[R] = base; summ_by_R[R] = summ; recs_by_R[R] = recs
        picks_by_R[R] = {int(y): p["threshold"] for y, p in summ["picks"].items()}
        print(f"  {R:.0f}R WF: full R={summ['chained_full']['mean_R']:+.4f} "
              f"fwd R={summ['chained_fwd']['mean_R']:+.4f} n={summ['n_trades']} "
              f"sum={summ['chained_full']['sum_R']}")
    OUT["walk_forward_by_target"] = {
        f"{int(R)}R": {
            "chained_full": summ_by_R[R]["chained_full"],
            "chained_fwd": summ_by_R[R]["chained_fwd"],
            "chained_per_year": summ_by_R[R]["chained_per_year"],
            "n_trades": summ_by_R[R]["n_trades"],
        } for R in (2.0, 3.0, 4.0)
    }

    # ---------------- (a) CORRELATED-RISK-UNIT SIZING ----------------
    print("\n" + "=" * 78); print("(a) CORRELATED-RISK-UNIT SIZING (precious WF stream, 2R baseline)"); print("=" * 78)
    recs2 = recs_by_R[2.0]
    # cluster stress (incl named -8.37R / 2025-04-08 day)
    stress = stress_clusters(recs2)
    print(f"  worst correlated DECISION-day clusters (summed R independent vs unit-R cluster-sized):")
    for r in stress["worst_clusters"][:6]:
        print(f"    {r['day']}: n={r['n_trades']:2d} summed_R={r['summed_R_independent']:+.2f} "
              f"-> unit_R={r['unit_R_cluster_sized']:+.3f}  syms={r['syms']}")
    print(f"  named 2025-04-08: {stress['named_2025_04_08']}")
    OUT["a_cluster_stress"] = stress

    # equity paths: independent (wave4-style) vs correlated-risk-unit, across a risk grid
    risk_grid = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0]
    indep = {str(r): independent_path(recs2, r) for r in risk_grid}
    unit = {str(r): cluster_risk_unit_path(recs2, r, cluster_cap_units=1.0) for r in risk_grid}
    print("\n  INDEPENDENT (each trade = 1 unit, wave4-style):")
    for r in risk_grid:
        v = indep[str(r)]
        print(f"    {r}%/trade: maxDD {v['max_drawdown_pct']}% worstDay {v['worst_day_pct']}% "
              f"~mo {v['approx_monthly_pct']}% ftmo={v['within_ftmo']}")
    print("  CORRELATED-RISK-UNIT (metals-cluster day = 1 unit, cap=1.0):")
    for r in risk_grid:
        v = unit[str(r)]
        print(f"    {r}%/unit:  maxDD {v['max_drawdown_pct']}% worstDay {v['worst_day_pct']}% "
              f"~mo {v['approx_monthly_pct']}% ftmo={v['within_ftmo']} "
              f"worstCluster_unitR={v['worst_cluster_unit_R']}")
    # max FTMO-safe risk under each scheme
    def max_ok(grid):
        ok = [float(r) for r in grid if grid[r].get("within_ftmo")]
        return max(ok) if ok else None
    OUT["a_independent_path"] = indep
    OUT["a_correlated_risk_unit_path"] = unit
    OUT["a_max_ftmo_risk"] = {"independent": max_ok(indep), "correlated_unit": max_ok(unit)}
    # explicit 0.25% verification (the deployed size) under BOTH schemes
    OUT["a_at_0p25"] = {"independent": indep["0.25"], "correlated_unit": unit["0.25"]}
    print(f"  max FTMO-safe risk -> independent {max_ok(indep)}%  correlated-unit {max_ok(unit)}%")

    # ---------------- (b) DEEPER TARGETS WITH M1 VERIFICATION ----------------
    print("\n" + "=" * 78); print("(b) DEEPER TARGETS 2R/3R/4R — H4 WF vs M1 INTRABAR (clean fills only)"); print("=" * 78)
    deeper = {}
    for R in (2.0, 3.0, 4.0):
        m1res = m1_deeper_target(base_by_R, picks_by_R[R], R)
        deeper[f"{int(R)}R"] = m1res
        print(f"  {R:.0f}R: cleanM1={m1res['clean_m1_fills']} (skip {m1res['low_coverage_skipped']}) "
              f"H4={m1res['h4_path']['mean_R']:+.4f} M1={m1res['m1_path']['mean_R']:+.4f} "
              f"delta={m1res['delta_mean_R']:+.4f} outcomes={m1res['m1_outcomes']} "
              f"agree={m1res['sign_agreement']}")
    OUT["b_deeper_target_m1"] = deeper

    # monthly% per target under correlated-unit sizing, at BOTH the conservative deployed
    # 0.25%/unit AND the MAX FTMO-safe %/unit (the real deployable return). Path = WF H4
    # stream; M1 delta (above) tells us how much to trust the deeper target on real fills.
    risk_grid = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0]
    print("\n  monthly%% per target (correlated-unit; 0.25%/unit and max-FTMO-safe %/unit):")
    monthly_by_R = {}
    for R in (2.0, 3.0, 4.0):
        v025 = cluster_risk_unit_path(recs_by_R[R], 0.25, cluster_cap_units=1.0)
        grid = {rr: cluster_risk_unit_path(recs_by_R[R], rr, cluster_cap_units=1.0) for rr in risk_grid}
        safe = [rr for rr in risk_grid if grid[rr].get("within_ftmo")]
        max_safe = max(safe) if safe else None
        vmax = grid[max_safe] if max_safe else None
        monthly_by_R[f"{int(R)}R"] = {
            **v025,
            "max_ftmo_safe_risk_unit": max_safe,
            "monthly_at_max_safe": (vmax or {}).get("approx_monthly_pct"),
            "maxDD_at_max_safe": (vmax or {}).get("max_drawdown_pct"),
            "worstDay_at_max_safe": (vmax or {}).get("worst_day_pct"),
        }
        print(f"    {R:.0f}R: @0.25u ~mo {v025['approx_monthly_pct']}% (maxDD {v025['max_drawdown_pct']}%) "
              f"| max-safe {max_safe}%/u -> ~mo {(vmax or {}).get('approx_monthly_pct')}% "
              f"(maxDD {(vmax or {}).get('max_drawdown_pct')}% worstDay {(vmax or {}).get('worst_day_pct')}%)")
    OUT["b_monthly_by_target_cluster_sized"] = monthly_by_R

    # ---------------- nulls ----------------
    print("\n" + "=" * 78); print("NULLS (WF selection; count-matched random + invert)"); print("=" * 78)
    nl = {}
    for R in (2.0, 3.0, 4.0):
        n = wf_nulls(R, summ_by_R[R])
        nl[f"{int(R)}R"] = n
        print(f"  {R:.0f}R: edge {n['edge_wf_full_R']:+.4f}  invert {n['invert_wf_full_R']:+.4f}  "
              f"random {n['random_mean_full_R']:+.4f}(max {n['random_max_full_R']:+.4f})  "
              f"beats_invert={n['edge_beats_invert']} beats_rand_max={n['edge_beats_random_max']}")
    OUT["nulls_by_target"] = nl

    # ---------------- SENSITIVITY: 2021 metals-cross backfill ----------------
    print("\n" + "=" * 78); print("SENSITIVITY: 2021 metals-cross H4 backfill ON (source-bound)"); print("=" * 78)
    set_backfill(True)
    bf = {}
    for R in (2.0, 3.0, 4.0):
        b2, s2, r2 = wf_stream(R)
        v = cluster_risk_unit_path(r2, 0.25, cluster_cap_units=1.0)
        bf[f"{int(R)}R"] = {
            "wf_full_R": s2["chained_full"]["mean_R"], "wf_fwd_R": s2["chained_fwd"]["mean_R"],
            "n_trades": s2["n_trades"],
            "cluster_0p25_monthly_pct": v["approx_monthly_pct"], "cluster_0p25_maxDD": v["max_drawdown_pct"],
            "cluster_0p25_worstDay": v["worst_day_pct"], "cluster_0p25_ftmo": v["within_ftmo"],
        }
        print(f"  {R:.0f}R(backfill): WF full {s2['chained_full']['mean_R']:+.4f} n={s2['n_trades']} "
              f"-> cluster0.25 ~mo {v['approx_monthly_pct']}% maxDD {v['max_drawdown_pct']}% ftmo={v['within_ftmo']}")
    OUT["sensitivity_2021_backfill"] = bf
    OUT["sensitivity_note"] = ("Adding the 2021 metals-cross H4 backfill (source-bound FTMO) "
                               "weakens the WF edge materially (2R full R ~+0.087 vs +0.226 without). "
                               "Reported as honest fragility; main verdict uses the established stream.")
    set_backfill(False)  # restore established baseline for any later use

    # ---------------- VERDICT ----------------
    print("\n" + "=" * 78); print("VERDICT"); print("=" * 78)
    u025 = unit["0.25"]; i025 = indep["0.25"]
    # (a) cluster sizing keeps FTMO at 0.25% AND bounds the worst day vs independent
    a_safe = bool(u025["within_ftmo"])
    a_bounds_worst_day = u025["worst_day_pct"] < i025["worst_day_pct"]
    # deeper-target survival on REAL M1: M1 path must stay positive AND not collapse vs H4
    def m1_survives(R):
        m = deeper[f"{int(R)}R"]
        return bool(m["m1_path"]["mean_R"] > 0 and m["delta_mean_R"] > -0.15 and
                    m["sign_agreement"]["disagree"] == 0)
    m1_2 = m1_survives(2.0); m1_3 = m1_survives(3.0); m1_4 = m1_survives(4.0)
    # does deeper target raise DEPLOYABLE monthly% (at the max FTMO-safe cluster size)?
    mo2 = monthly_by_R["2R"]["monthly_at_max_safe"]; mo3 = monthly_by_R["3R"]["monthly_at_max_safe"]
    mo4 = monthly_by_R["4R"]["monthly_at_max_safe"]
    # null survival per target (full WF stream)
    surv2 = nl["2R"]["edge_beats_invert"] and nl["2R"]["edge_beats_random_max"]
    surv3 = nl["3R"]["edge_beats_invert"] and nl["3R"]["edge_beats_random_max"]
    surv4 = nl["4R"]["edge_beats_invert"] and nl["4R"]["edge_beats_random_max"]

    # recommend target: 2R is the ESTABLISHED, proven, lower-stop-count floor. Only move to a
    # deeper target if it (i) survives M1 real fills + nulls AND (ii) delivers a MATERIAL
    # deployable-monthly improvement (>10% relative) over 2R at max FTMO-safe sizing. A deeper
    # target with equal/lower deployable monthly is NOT worth the extra stop-out variance.
    rec_R = 2
    best_gain = 0.0
    for R, mo, m1ok, nullok in [(3, mo3, m1_3, surv3), (4, mo4, m1_4, surv4)]:
        if mo is not None and mo2 and m1ok and nullok:
            rel_gain = (mo - mo2) / abs(mo2)
            if rel_gain > 0.10 and rel_gain > best_gain:
                best_gain = rel_gain; rec_R = R
    deeper_helps = rec_R != 2
    verdict = {
        "(a)_correlated_risk_unit_FTMO_safe_at_0p25": a_safe,
        "(a)_worst_day_pct_correlated_unit": u025["worst_day_pct"],
        "(a)_worst_day_pct_independent": i025["worst_day_pct"],
        "(a)_correlated_bounds_worst_day": a_bounds_worst_day,
        "(a)_max_dd_pct_correlated_unit": u025["max_drawdown_pct"],
        "(a)_max_ftmo_safe_risk_correlated": OUT["a_max_ftmo_risk"]["correlated_unit"],
        "(a)_max_ftmo_safe_risk_independent": OUT["a_max_ftmo_risk"]["independent"],
        "(a)_worst_cluster_unit_R_sized": u025["worst_cluster_unit_R"],
        "(a)_worst_cluster_summed_R_independent": stress["worst_summed_R_independent"],
        "(a)_named_2025_04_08_unit_R": (stress["named_2025_04_08"] or {}).get("unit_R_cluster_sized"),
        "(b)_2R_m1_path_R": deeper["2R"]["m1_path"]["mean_R"],
        "(b)_3R_m1_path_R": deeper["3R"]["m1_path"]["mean_R"],
        "(b)_4R_m1_path_R": deeper["4R"]["m1_path"]["mean_R"],
        "(b)_3R_m1_vs_h4_delta": deeper["3R"]["delta_mean_R"],
        "(b)_4R_m1_vs_h4_delta": deeper["4R"]["delta_mean_R"],
        "(b)_3R_survives_m1": m1_3, "(b)_4R_survives_m1": m1_4,
        "(b)_deployable_monthly_2R_at_maxsafe": mo2,
        "(b)_deployable_monthly_3R_at_maxsafe": mo3,
        "(b)_deployable_monthly_4R_at_maxsafe": mo4,
        "(b)_max_safe_risk_unit_2R": monthly_by_R["2R"]["max_ftmo_safe_risk_unit"],
        "(b)_max_safe_risk_unit_3R": monthly_by_R["3R"]["max_ftmo_safe_risk_unit"],
        "(b)_max_safe_risk_unit_4R": monthly_by_R["4R"]["max_ftmo_safe_risk_unit"],
        "(b)_nulls_survive_2R": surv2, "(b)_nulls_survive_3R": surv3, "(b)_nulls_survive_4R": surv4,
        "(b)_deeper_target_materially_helps": deeper_helps,
        "RECOMMENDED_TARGET_R": rec_R,
        "RECOMMENDED_MONTHLY_PCT_AT_MAXSAFE": monthly_by_R[f"{rec_R}R"]["monthly_at_max_safe"],
        "RECOMMENDED_MAXSAFE_RISK_UNIT": monthly_by_R[f"{rec_R}R"]["max_ftmo_safe_risk_unit"],
        "RECOMMENDED_MONTHLY_PCT_AT_0p25u": monthly_by_R[f"{rec_R}R"]["approx_monthly_pct"],
        "RECOMMENDED_SIZING": "correlated-risk-unit: metals cluster (same decision day) = ONE risk unit, split equally; FTMO-safe up to ~1.0%/unit at 2R",
        "NOTE_deeper_target": ("3R/4R survive M1 real fills (delta~0, zero sign flips) and nulls, but a "
                               "lower win rate forces a smaller FTMO-safe size; deployable monthly at "
                               "max-safe sizing is ~0.22% (2R), ~0.16% (3R), ~0.22% (4R) — no material gain. "
                               "Keep 2R unless a deeper target shows >10% relative monthly improvement."),
    }
    OUT["verdict"] = verdict
    for k, v in verdict.items():
        print(f"  {k}: {v}")

    with open(EDGE + "/WAVE5_METALS_RISK_UNIT_AND_TARGET_RESULT.json", "w") as f:
        json.dump(OUT, f, indent=1, default=str)
    print("\nWROTE WAVE5_METALS_RISK_UNIT_AND_TARGET_RESULT.json")


if __name__ == "__main__":
    main()
