#!/usr/bin/env python3
"""B1 — aggregate the per-leg measurement and restate the arm split at MEASURED slippage.

Reads legs_*.pkl written by b1_slip.py, produces:
  * per-leg tables (n, mean, median, p95, p99, adverse fraction, cluster-bootstrap CI)
  * by symbol / by entry hour / by origin family
  * the like-for-like LIMIT vs MARKET comparison on shared (symbol, day) cells
  * the arm restatement: Lane 1's edge minus a deduction built from EACH ARM'S OWN measured legs
  * the adversarial checks (risk-distance composition, barrier-mix representativeness)

Cluster bootstrap on trading_day, seed 20260812 — identical to recon_agg.py.
"""
from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd

OUT = "/Users/borr/.claude/jobs/adb9e69b/tmp/b1"
SEED = 20260812

# ---- Lane 1's five-month arm ladder (LANE1_SUMMARY_V1.json /A_by_order_type) ----
LANE1 = {
    "LIMIT":  dict(n=72496, edge=0.05383, ci95=[0.0300, 0.0798]),
    "MARKET": dict(n=74249, edge=0.00844, ci95=[-0.0050, 0.0228]),
    "POOLED": dict(n=146745, edge=0.030867, ci95=[0.01813, 0.04389]),
}
# five-month barrier counts per arm (Lane 1 §1.1; MARKET independently reproduced by control B)
BARRIERS = {
    "LIMIT":  dict(TARGET=16136, STOP=40153, TIME_STOP=72496 - 16136 - 40153),
    "MARKET": dict(TARGET=14601, STOP=38054, TIME_STOP=74249 - 14601 - 38054),
}


def se_from_ci(ci):
    return (ci[1] - ci[0]) / (2 * 1.959964)


def boot_ci(v, days, B=4000, seed=SEED):
    rng = np.random.default_rng(seed)
    v = np.asarray(v, float)
    days = np.asarray(days)
    ok = ~np.isnan(v)
    v, days = v[ok], days[ok]
    if len(v) < 5:
        return [float("nan")] * 2, float("nan")
    ud = pd.unique(days)
    idx = {d: np.where(days == d)[0] for d in ud}
    means = np.empty(B)
    for b in range(B):
        pick = rng.choice(len(ud), len(ud), replace=True)
        sel = np.concatenate([idx[ud[p]] for p in pick])
        means[b] = v[sel].mean()
    return [float(np.quantile(means, .025)), float(np.quantile(means, .975))], float(means.std(ddof=1))


def desc(v, days=None, ci=False):
    v = np.asarray(v, float)
    v = v[~np.isnan(v)]
    if len(v) == 0:
        return None
    d = dict(n=int(len(v)), mean=float(v.mean()), median=float(np.median(v)),
             p95=float(np.quantile(v, .95)), p99=float(np.quantile(v, .99)),
             frac_adverse=float((v > 1e-9).mean()))
    if ci and days is not None:
        d["CI95"], d["boot_se"] = boot_ci(v, np.asarray(days)[:len(v)])
    return d


def legs_table(D, ci=True):
    """Per-leg summary for one arm's measured rows."""
    R = {}
    e = D.dropna(subset=["entry_opt_r"])
    R["entry"] = desc(e.entry_opt_r.values, e.day.values, ci=ci)
    for st in ["STOP", "TARGET", "TIME_STOP"]:
        s = D[(D.state == st) & (D.get("found_cross") == 1)]
        R[st] = dict(
            at_crossing_tick=desc(s.exit_opt_at_cross_r.values, s.day.values, ci=ci) if len(s) else None,
            at_next_tick=desc(s.exit_opt_next_tick_r.values, s.day.values, ci=ci) if len(s) else None,
            n_state_rows=int((D.state == st).sum()),
            n_resolved_from_ticks=int(len(s)),
            resolution_rate=float(len(s) / max(1, (D.state == st).sum())),
        )
    R["n_rows"] = int(len(D))
    R["window_state_shares"] = {st: float((D.state == st).mean())
                                for st in ["STOP", "TARGET", "TIME_STOP"]}
    return R


def deduction(arm, stop_cond, ts_cond, shares=None):
    """The adjudication's deduction: stop_cond*pS + ts_cond*pX; target leg is 0 by design."""
    b = BARRIERS[arm]
    n = sum(b.values())
    pS = shares["STOP"] if shares else b["STOP"] / n
    pX = shares["TIME_STOP"] if shares else b["TIME_STOP"] / n
    pT = shares["TARGET"] if shares else b["TARGET"] / n
    return dict(pS=pS, pT=pT, pX=pX,
                stop_term=stop_cond * pS, ts_term=ts_cond * pX, target_term=0.0,
                deduction=stop_cond * pS + ts_cond * pX)


def boot_deduction(D, arm, B=2000, seed=SEED):
    """Cluster-bootstrap the DEDUCTION itself (resample days, recompute both conditionals)."""
    rng = np.random.default_rng(seed + 1)
    b = BARRIERS[arm]
    n = sum(b.values())
    pS, pX = b["STOP"] / n, b["TIME_STOP"] / n
    st = D[(D.state == "STOP") & (D.found_cross == 1)]
    ts = D[(D.state == "TIME_STOP") & (D.found_cross == 1)]
    days = pd.unique(D.day.values)
    si = {d: st.exit_opt_at_cross_r.values[st.day.values == d] for d in days}
    ti = {d: ts.exit_opt_at_cross_r.values[ts.day.values == d] for d in days}
    out = np.empty(B)
    for k in range(B):
        pick = rng.choice(len(days), len(days), replace=True)
        sv = np.concatenate([si[days[p]] for p in pick]) if len(si) else np.array([0.0])
        tv = np.concatenate([ti[days[p]] for p in pick]) if len(ti) else np.array([0.0])
        sm = sv.mean() if len(sv) else 0.0
        tm = tv.mean() if len(tv) else 0.0
        out[k] = sm * pS + tm * pX
    return float(out.std(ddof=1))


def restate(arm, stop_cond, ts_cond, ded_se, label):
    L = LANE1[arm]
    d = deduction(arm, stop_cond, ts_cond)
    edge = L["edge"] - d["deduction"]
    se_edge = se_from_ci(L["ci95"])
    se_tot = float(np.hypot(se_edge, ded_se))
    return dict(arm=arm, basis=label, n=L["n"], edge_raw=L["edge"],
                stop_conditional=stop_cond, time_stop_conditional=ts_cond,
                **{k: d[k] for k in ("pS", "pT", "pX")},
                deduction=d["deduction"], edge_at_tick_truth=edge,
                se_edge_lane1=se_edge, se_deduction=ded_se, se_total=se_tot,
                t=edge / se_tot,
                ci95=[edge - 1.959964 * se_tot, edge + 1.959964 * se_tot],
                significant=bool(abs(edge / se_tot) > 1.959964))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit-tag", default="limit")
    ap.add_argument("--market-tag", default="ctrlB_lg_market")
    args = ap.parse_args()

    R = {"schema": "b1_limit_arm_measured_v1",
         "window": "2026-06-18..2026-07-24 (tick archive extent)",
         "sign_convention": "+ve = engine booked price BETTER than achievable = engine optimism = a cost",
         "seed": SEED}

    M = pd.read_pickle(f"{OUT}/legs_{args.market_tag}.pkl")
    R["MARKET_measured"] = legs_table(M)
    Lm = pd.read_pickle(f"{OUT}/legs_{args.limit_tag}.pkl")
    R["LIMIT_measured"] = legs_table(Lm)

    def cond(D, st):
        s = D[(D.state == st) & (D.found_cross == 1)]
        return float(s.exit_opt_at_cross_r.mean()) if len(s) else 0.0

    ms, mt = cond(M, "STOP"), cond(M, "TIME_STOP")
    ls, lt = cond(Lm, "STOP"), cond(Lm, "TIME_STOP")
    mse, lse = boot_deduction(M, "MARKET"), boot_deduction(Lm, "LIMIT")

    R["arm_restatement"] = {
        "MARKET_measured": restate("MARKET", ms, mt, mse, "measured on MARKET rows"),
        "LIMIT_transferred_recon": restate("LIMIT", ms, mt, mse,
                                           "TRANSFERRED from MARKET (the adjudication's basis)"),
        "LIMIT_measured": restate("LIMIT", ls, lt, lse, "MEASURED on LIMIT rows (this lane)"),
    }
    R["transfer_error"] = {
        "stop_conditional_MARKET": ms, "stop_conditional_LIMIT": ls,
        "ratio_LIMIT_over_MARKET": ls / ms if ms else None,
        "falsification_bar_stop_cond": 0.1150,
        "measured_vs_bar": ls / 0.1150,
    }

    # ---- like-for-like: shared (symbol, day) cells only ----
    ks = set(zip(M.symbol, M.day)) & set(zip(Lm.symbol, Lm.day))
    ms_ = M[[k in ks for k in zip(M.symbol, M.day)]]
    ls_ = Lm[[k in ks for k in zip(Lm.symbol, Lm.day)]]
    a = ms_[(ms_.state == "STOP") & (ms_.found_cross == 1)]
    b = ls_[(ls_.state == "STOP") & (ls_.found_cross == 1)]
    R["like_for_like_shared_symbol_day"] = {
        "n_cells": len(ks),
        "MARKET": desc(a.exit_opt_at_cross_r.values, a.day.values, ci=True),
        "LIMIT": desc(b.exit_opt_at_cross_r.values, b.day.values, ci=True),
    }

    # ---- adversarial: risk-distance composition (a tighter stop inflates R-slippage) ----
    R["risk_distance_composition"] = {}
    for nm, D in (("MARKET", M), ("LIMIT", Lm)):
        s = D[(D.state == "STOP") & (D.found_cross == 1)]
        R["risk_distance_composition"][nm] = dict(
            n=int(len(s)),
            risk_price_mean=float(s.risk.mean()), risk_price_median=float(s.risk.median()),
            slip_price_mean=float((s.exit_opt_at_cross_r * s.risk).mean()),
            slip_price_median=float((s.exit_opt_at_cross_r * s.risk).median()))
    # same quantity per symbol, so the composition question is answered within instrument
    rows = []
    for sym in sorted(set(M.symbol) & set(Lm.symbol)):
        a = M[(M.symbol == sym) & (M.state == "STOP") & (M.found_cross == 1)]
        b = Lm[(Lm.symbol == sym) & (Lm.state == "STOP") & (Lm.found_cross == 1)]
        if len(a) < 20 or len(b) < 20:
            continue
        rows.append(dict(symbol=sym, n_mkt=len(a), n_lim=len(b),
                         mkt_r=float(a.exit_opt_at_cross_r.mean()),
                         lim_r=float(b.exit_opt_at_cross_r.mean()),
                         mkt_price=float((a.exit_opt_at_cross_r * a.risk).mean()),
                         lim_price=float((b.exit_opt_at_cross_r * b.risk).mean()),
                         mkt_risk=float(a.risk.mean()), lim_risk=float(b.risk.mean())))
    R["stop_leg_by_symbol_both_arms"] = rows

    # ---- LIMIT stop leg by family / hour ----
    sl = Lm[(Lm.state == "STOP") & (Lm.found_cross == 1)]
    R["LIMIT_stop_by_family"] = {k: dict(n=int(len(g)), mean=float(g.exit_opt_at_cross_r.mean()),
                                         median=float(g.exit_opt_at_cross_r.median()),
                                         p95=float(g.exit_opt_at_cross_r.quantile(.95)),
                                         p99=float(g.exit_opt_at_cross_r.quantile(.99)))
                                 for k, g in sl.groupby("family")}
    R["LIMIT_stop_by_symbol"] = {k: dict(n=int(len(g)), mean=float(g.exit_opt_at_cross_r.mean()),
                                         median=float(g.exit_opt_at_cross_r.median()),
                                         p95=float(g.exit_opt_at_cross_r.quantile(.95)),
                                         p99=float(g.exit_opt_at_cross_r.quantile(.99)),
                                         frac_adverse=float((g.exit_opt_at_cross_r > 1e-9).mean()))
                                 for k, g in sl.groupby("symbol")}
    R["LIMIT_stop_by_hour"] = {int(k): dict(n=int(len(g)), mean=float(g.exit_opt_at_cross_r.mean()),
                                            p95=float(g.exit_opt_at_cross_r.quantile(.95)))
                               for k, g in sl.groupby("hour")}
    # month split (stability)
    R["LIMIT_stop_by_month"] = {k: dict(n=int(len(g)), mean=float(g.exit_opt_at_cross_r.mean()))
                                for k, g in sl.groupby("month")}

    # ---- gross-side control: LIMIT stops should book ~ -1.00100, 97.31% exactly -1 ----
    for nm, D in (("MARKET", M), ("LIMIT", Lm)):
        s = D[D.state == "STOP"]
        t = D[D.state == "TARGET"]
        R.setdefault("gross_booking_control", {})[nm] = dict(
            stop_mean_gross=float(s.gross.mean()), stop_frac_exact=float((s.gross.round(5) == -1.0).mean()),
            target_mean_gross=float(t.gross.mean()) if len(t) else None,
            target_frac_exact=float((t.gross.round(5) == 2.0).mean()) if len(t) else None)

    json.dump(R, open(f"{OUT}/B1_LIMIT_ARM_MEASURED_V1.json", "w"), indent=1)
    print(json.dumps({k: R[k] for k in ("arm_restatement", "transfer_error",
                                        "like_for_like_shared_symbol_day",
                                        "risk_distance_composition", "gross_booking_control")},
                     indent=1))


if __name__ == "__main__":
    main()
