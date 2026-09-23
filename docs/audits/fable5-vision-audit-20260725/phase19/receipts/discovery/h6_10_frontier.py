"""h6 step 10 — the AFFORDABILITY FRONTIER under hour-true cost, and everything the
estate requires published about the cell that clears it.

  1. composition of the paying cell (instrument x broker hour) and its cost census
  2. contract sensitivity INSIDE the paying cell (k x trail x target x maxbars) --
     the joint optimum is re-chosen on the cohort that can pay, not on the pool
  3. horizon sensitivity: the 2-hour wall, truncation share, and what happens to the
     result when the contract is forced to close before it
  4. TRAIN/TEST across months, and a leave-one-month-out read
  5. equity path, day-level positivity, bootstrap
"""
import gzip, json, os, sys, time

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h6_lib as H  # noqa: E402

MONTHS = ("2026-01", "2026-02", "2026-03")
KS = [0, 1, 2, 3, 5, 8, 10, 15, 20, 30, 45]
TRAILS = [None, 0.10, 0.15, 0.25, 0.40, 0.75, 1.00]
TARGETS = [None, 1.0, 2.0, 3.0]
MAXBARS = [None, 15, 30, 45, 60, 90, 120]


def slim(s):
    return {k: (round(v, 6) if isinstance(v, float) else v) for k, v in s.items()}


def main():
    t0 = time.time()
    P, M = H.load()
    cost_hour = np.load(f"{D}/h6_cost_hour.npy")
    bh = np.load(f"{D}/h6_broker_hour.npy")
    Mh = dict(M)
    Mh["cost_true"] = cost_hour
    hour_bps = cost_hour * M["bpsfac"]
    out = {"cost_basis": "HOUR-TRUE broker spread (spread_bps_median_by_broker_hour) "
                         "+ commission + slippage; broker clock = America/New_York + 7h"}

    # -------- 1. the frontier: sweep the hour-true bps cap on a fixed reference contract
    ref = dict(k=3, target=None, stop=-1.0, trail=None, maxbars=None)
    r, reason, _e, trd, c0 = H.walk_all(P, **ref)
    fr = []
    for cap in [None, 2.5, 2.0, 1.5, 1.2, 1.0, 0.9, 0.85, 0.8, 0.75, 0.7, 0.68, 0.66,
                0.64, 0.62, 0.60, 0.58, 0.55, 0.50, 0.45, 0.40]:
        sel = trd & np.isfinite(cost_hour)
        if cap is not None:
            sel = sel & (hour_bps <= cap + 1e-12)
        if sel.sum() < 100:
            continue
        s = slim(H.score(r, Mh, sel, reason))
        s["cap_bps"] = cap
        for m in MONTHS:
            s2 = sel & (M["month"] == m)
            s["n_" + m[-2:]] = int(s2.sum())
            if s2.sum():
                s["net_" + m[-2:]] = round(float((r[s2] - cost_hour[s2]).mean()), 6)
        s["months_pos"] = sum(1 for m in MONTHS if s.get("net_" + m[-2:], -1) > 0)
        fr.append(s)
    out["frontier_k3_STOPONLY"] = fr
    print("frontier done", round(time.time() - t0, 1), flush=True)

    # pick the widest cap that is net-positive in all three months
    payers = [s for s in fr if s["months_pos"] == 3 and s["net"] > 0 and s["n"] >= 500]
    CAP = max(payers, key=lambda s: s["cap_bps"] or 0)["cap_bps"] if payers else 0.6
    out["chosen_cap_bps"] = CAP
    POP = trd & np.isfinite(cost_hour) & (hour_bps <= CAP + 1e-12)
    out["cap_population_n"] = int(POP.sum())
    print("CAP", CAP, "n", int(POP.sum()), flush=True)

    # -------- 2. composition
    comp = {}
    for lab, arr in (("symbol", M["symbol"]), ("broker_hour", bh.astype(str)),
                     ("family", M["family"]), ("session", M["session"]),
                     ("month", M["month"])):
        d = {}
        for v in np.unique(arr[POP]):
            m = POP & (arr == v)
            d[str(v)] = {"n": int(m.sum()),
                         "cost_hour_bps": round(float(hour_bps[m].mean()), 4),
                         "cost_flat_bps": round(float((M["cost_true"][m] * M["bpsfac"][m]).mean()), 4),
                         "cost_hour_R": round(float(cost_hour[m].mean()), 5)}
        comp[lab] = d
    out["composition"] = comp
    print("symbols in cap cell:", sorted(comp["symbol"]), flush=True)

    # -------- 3. contract sweep INSIDE the paying cohort
    grid = []
    for k in KS:
        for tg in TARGETS:
            for tr in TRAILS:
                for mb in MAXBARS:
                    rr, rs, _e2, td, cc = H.walk_all(P, k=k, target=tg, stop=-1.0,
                                                     trail=tr, maxbars=mb)
                    sel = td & POP
                    nn = int(sel.sum())
                    if nn < 300:
                        continue
                    s = slim(H.score(rr, Mh, sel, rs))
                    s.update({"k": k, "target": tg, "trail": tr, "maxbars": mb})
                    mp = 0
                    for m in MONTHS:
                        s2 = sel & (M["month"] == m)
                        if s2.sum():
                            v = float((rr[s2] - cost_hour[s2]).mean())
                            s["net_" + m[-2:]] = round(v, 6)
                            s["n_" + m[-2:]] = int(s2.sum())
                            mp += (v > 0)
                    s["months_pos"] = mp
                    # train Jan+Feb -> test Mar
                    trm = sel & np.isin(M["month"], MONTHS[:2])
                    tem = sel & (M["month"] == MONTHS[2])
                    s["train_net"] = round(float((rr[trm] - cost_hour[trm]).mean()), 6)
                    s["test_net"] = round(float((rr[tem] - cost_hour[tem]).mean()), 6)
                    grid.append(s)
    out["contract_grid_inside_cap"] = grid
    out["contract_cells_searched"] = len(grid)
    print("contract grid", len(grid), round(time.time() - t0, 1), flush=True)

    best = max(grid, key=lambda s: s["net"])
    best_robust = max([s for s in grid if s["months_pos"] == 3 and s["n"] >= 1000],
                      key=lambda s: s["net"], default=best)
    best_train = max(grid, key=lambda s: s["train_net"])
    out["best_net_in_cap"] = best
    out["best_robust_in_cap"] = best_robust
    out["best_on_train_read_on_test"] = best_train
    for lab, b in (("best_net", best), ("best_robust", best_robust),
                   ("best_on_train", best_train)):
        print(f" {lab}: k={b['k']} tgt={b['target']} trail={b['trail']} mb={b['maxbars']}"
              f" n={b['n']} net={b['net']:+.5f} rr={b['ratio_r']:.2f} trunc={b['share_maxbars_truncated']:.3f}"
              f" mo+={b['months_pos']} train={b['train_net']:+.5f} test={b['test_net']:+.5f}", flush=True)

    # -------- 4. horizon sensitivity of the chosen contract family
    hz = []
    for mb in [15, 30, 45, 60, 75, 90, 105, 120, None]:
        rr, rs, _e2, td, cc = H.walk_all(P, k=best_robust["k"], target=best_robust["target"],
                                         stop=-1.0, trail=best_robust["trail"], maxbars=mb)
        sel = td & POP
        s = slim(H.score(rr, Mh, sel, rs))
        s["maxbars"] = mb
        for m in MONTHS:
            s2 = sel & (M["month"] == m)
            if s2.sum():
                s["net_" + m[-2:]] = round(float((rr[s2] - cost_hour[s2]).mean()), 6)
        hz.append(s)
    out["horizon_sensitivity"] = hz
    print("\n horizon sensitivity (k=%s trail=%s target=%s):" %
          (best_robust["k"], best_robust["trail"], best_robust["target"]), flush=True)
    for s in hz:
        print(f"   maxbars {str(s['maxbars']):>5}  n {s['n']:>5}  net {s['net']:+.5f}"
              f"  rr {(s['ratio_r'] or 0):.2f}  trunc {s['share_maxbars_truncated']:.3f}"
              f"  {s.get('net_01',0):+.4f}/{s.get('net_02',0):+.4f}/{s.get('net_03',0):+.4f}", flush=True)

    # -------- 5. full economics of the headline cell
    for lab, b in (("HEADLINE", best_robust), ("BEST_TRAIN_PICK", best_train)):
        rr, rs, _e2, td, cc = H.walk_all(P, k=b["k"], target=b["target"], stop=-1.0,
                                         trail=b["trail"], maxbars=b["maxbars"])
        sel = td & POP
        bd = H.by_day(rr, Mh, sel)
        days = sorted(bd)
        cum, eq = 0.0, []
        for d in days:
            cum += bd[d]["sum_net"]; eq.append(round(cum, 3))
        peak, dd = -1e18, 0.0
        for e in eq:
            peak = max(peak, e); dd = min(dd, e - peak)
        rec = {"contract": {kk: b[kk] for kk in ("k", "target", "trail", "maxbars")},
               "score": slim(H.score(rr, Mh, sel, rs)),
               "score_flat_cost": slim(H.score(rr, M, sel, rs)),
               "per_symbol": {s: slim(v) for s, v in H.by_group(rr, Mh, sel, "symbol").items()},
               "per_month": {s: slim(v) for s, v in H.by_group(rr, Mh, sel, "month").items()},
               "per_hour": {s: slim(v) for s, v in H.by_group(rr, Mh, sel, "hour").items()},
               "per_family": {s: slim(v) for s, v in H.by_group(rr, Mh, sel, "family").items()},
               "n_days": len(days),
               "n_days_net_pos": sum(1 for d in days if bd[d]["net"] > 0),
               "n_days_gross_pos": sum(1 for d in days if bd[d]["gross"] > 0),
               "equity_net_R": eq, "max_dd_R": round(dd, 3),
               "final_net_R": eq[-1] if eq else 0.0,
               "boot_net": H.bootstrap_days(rr, Mh, sel, field="net"),
               "per_day": bd}
        rec["n_symbols_net_pos"] = sum(1 for v in rec["per_symbol"].values() if v["net"] > 0)
        # leave-one-month-out
        loo = {}
        for held in MONTHS:
            te = sel & (M["month"] == held)
            loo[held] = {"n": int(te.sum()),
                         "net": round(float((rr[te] - cost_hour[te]).mean()), 6),
                         "total_R": round(float((rr[te] - cost_hour[te]).sum()), 3)}
        rec["per_month_readout"] = loo
        out[lab] = rec
        print(f"\n {lab}: n {rec['score']['n']} net {rec['score']['net']:+.5f}"
              f" rr {rec['score']['ratio_r']:.2f} days+ {rec['n_days_net_pos']}/{rec['n_days']}"
              f" finalR {rec['final_net_R']} maxDD {rec['max_dd_R']}"
              f" boot p<=0 {rec['boot_net']['p_le_0']}", flush=True)

    json.dump(out, open(f"{D}/H6_FRONTIER_V1.json", "w"), indent=1)
    print("wrote H6_FRONTIER_V1.json", round(time.time() - t0, 1), flush=True)


if __name__ == "__main__":
    main()
