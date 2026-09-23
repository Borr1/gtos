"""h6 step 6 — the deep joint pricing of ONE contract.

  A. fill-floor inertness, measured per month with the NaN convention made explicit
  B. gate sweep in BOTH denominations, fine: cost_true (R) and cost_bps (price space)
  C. gate x cancel-band joint surface, with month splits
  D. the CORRECTED ablation: the cancel band is nested inside the delay (it does not
     exist without one), so removing the delay removes the band
  E. per-symbol edge:cost ratio table under the joint optimum and under each gate
  F. TRAIN/TEST: choose on two months, read on the third, all three ways
  G. equity path, day positivity, truncation share

usage: python3 h6_06_deep.py <tag> <k> <target|None> <stop> <trail|None> <maxbars|None>
"""
import json, os, sys, time

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h6_lib as H  # noqa: E402

MONTHS = ("2026-01", "2026-02", "2026-03")
BANDS = [("none", None, None),
         ("c0<=+0.10", None, 0.10), ("c0<=+0.05", None, 0.05), ("c0<=0", None, 0.0),
         ("c0<=-0.05", None, -0.05),
         ("c0>=0", 0.0, None), ("c0>=-0.05", -0.05, None), ("c0>=-0.10", -0.10, None),
         ("|c0|<=0.05", -0.05, 0.05), ("|c0|<=0.10", -0.10, 0.10),
         ("|c0|<=0.20", -0.20, 0.20)]
RGATES = [None, 0.40, 0.30, 0.25, 0.20, 0.15, 0.125, 0.10, 0.09, 0.08, 0.07, 0.06,
          0.05, 0.045, 0.04, 0.035, 0.03, 0.025, 0.02, 0.0175, 0.015, 0.0125, 0.01,
          0.0075, 0.005]
BGATES = [None, 6.0, 5.0, 4.0, 3.0, 2.5, 2.457, 2.0, 1.75, 1.5, 1.25, 1.0, 0.9, 0.8,
          0.7, 0.6, 0.5, 0.45, 0.4]
FLOORS = [None, 0.45, 0.70, 0.80, 0.90, 0.93]


def parse(x):
    return None if x in ("None", "none", "-") else float(x)


def slim(s):
    return {k: (round(v, 6) if isinstance(v, float) else v) for k, v in s.items()}


def main(tag, k, target, stop, trail, maxbars):
    t0 = time.time()
    P, M = H.load()
    r, reason, ebar, trd, c0 = H.walk_all(P, k=k, target=target, stop=stop,
                                          trail=trail, maxbars=maxbars)
    out = {"tag": tag, "contract": {"k": k, "target": target, "stop": stop,
                                    "trail": trail, "maxbars": maxbars}}
    base = H.population(M, trd, c0)
    out["ungated"] = slim(H.score(r, M, base, reason))

    # ---- A. fill floor
    efp = M["efp"]
    A = {"n_rows": int(len(efp)), "n_efp_present": int(np.isfinite(efp).sum()),
         "distinct_values": sorted(set(float(x) for x in efp[np.isfinite(efp)])),
         "per_month_present": {m: int(np.isfinite(efp[M["month"] == m]).sum())
                               for m in MONTHS},
         "per_month_n": {m: int((M["month"] == m).sum()) for m in MONTHS}}
    A["refusals_among_present"] = {str(f): int((efp[np.isfinite(efp)] < f).sum())
                                   for f in (0.45, 0.70, 0.80, 0.90, 0.93, 0.95)}
    A["refusals_nan_refused"] = {str(f): int(((~(efp >= f))).sum())
                                 for f in (0.45, 0.70, 0.80, 0.90, 0.93, 0.95)}
    for f in (0.45, 0.80, 0.90):
        s1 = H.population(M, trd, c0, fill_floor=f, floor_nan_passes=True)
        s2 = H.population(M, trd, c0, fill_floor=f, floor_nan_passes=False)
        A.setdefault("scored", {})[str(f)] = {
            "nan_passes": slim(H.score(r, M, s1, reason)),
            "nan_refused": slim(H.score(r, M, s2, reason))}
    out["A_fill_floor"] = A

    # ---- B. gate sweeps, both denominations
    B = {"cost_true_R": [], "cost_bps": []}
    for g in RGATES:
        sel = H.population(M, trd, c0, gate_total=g)
        if sel.sum() < 30:
            continue
        s = slim(H.score(r, M, sel, reason)); s["gate_R"] = g
        for m in MONTHS:
            s2 = sel & (M["month"] == m)
            s["n_" + m[-2:]] = int(s2.sum())
            if s2.sum():
                s["net_" + m[-2:]] = round(float((r[s2] - M["cost_true"][s2]).mean()), 6)
        B["cost_true_R"].append(s)
    for g in BGATES:
        sel = H.population(M, trd, c0, gate_bps=g)
        if sel.sum() < 30:
            continue
        s = slim(H.score(r, M, sel, reason)); s["gate_bps"] = g
        s["symbols"] = sorted(set(M["symbol"][sel].tolist()))
        for m in MONTHS:
            s2 = sel & (M["month"] == m)
            s["n_" + m[-2:]] = int(s2.sum())
            if s2.sum():
                s["net_" + m[-2:]] = round(float((r[s2] - M["cost_true"][s2]).mean()), 6)
        B["cost_bps"].append(s)
    out["B_gate_sweeps"] = B
    print("B done", round(time.time() - t0, 1), flush=True)

    # ---- C. gate x band surface (both denominations)
    C = []
    for bn, lo, hi in BANDS:
        for gk, glist in (("R", RGATES), ("bps", BGATES)):
            for g in glist:
                kw = {"gate_total": g} if gk == "R" else {"gate_bps": g}
                sel = H.population(M, trd, c0, entry_lo=lo, entry_hi=hi, **kw)
                nn = int(sel.sum())
                if nn < 100:
                    continue
                s = slim(H.score(r, M, sel, reason))
                s.update({"band": bn, "gate_kind": gk, "gate": g})
                for m in MONTHS:
                    s2 = sel & (M["month"] == m)
                    s["n_" + m[-2:]] = int(s2.sum())
                    if s2.sum():
                        s["net_" + m[-2:]] = round(float((r[s2] - M["cost_true"][s2]).mean()), 6)
                C.append(s)
    out["C_surface"] = C
    out["C_cells_searched"] = len(C)
    print("C done", len(C), round(time.time() - t0, 1), flush=True)

    # ---- D. corrected ablation (band nested in delay)
    def arm(delay_on, exit_on, band, gate, floor):
        kk = k if delay_on else 0
        if exit_on:
            rr = H.walk_all(P, k=kk, target=target, stop=stop, trail=trail, maxbars=maxbars)
        else:
            rr = H.walk_all(P, k=kk, target=2.0, stop=-1.0, trail=None, maxbars=None)
        rv, rs, _e, td, cc = rr
        lo, hi = (band if (band and delay_on) else (None, None))
        sel = H.population(M, td, cc, entry_lo=lo, entry_hi=hi, gate_total=gate,
                           fill_floor=floor, floor_nan_passes=True)
        return rv, rs, sel

    # choose the band and gate that the C surface says are best on the FULL sample,
    # then ablate at that point.  (train/test in F.)
    cand = [s for s in C if s["n"] >= 300 and s["gate_kind"] == "R"]
    bestc = max(cand, key=lambda s: s["net"])
    bb = next((lo, hi) for bn, lo, hi in BANDS if bn == bestc["band"])
    bg = bestc["gate"]
    out["D_ablation_point"] = {"band": bestc["band"], "gate_R": bg, "n": bestc["n"]}
    fac = {}
    for dd in (0, 1):
        for ee in (0, 1):
            for gg in (0, 1):
                for ff in (0, 1):
                    for bnd in ((0, 1) if dd else (0,)):
                        rv, rs, sel = arm(dd, ee, bb if bnd else None,
                                          bg if gg else None, 0.45 if ff else None)
                        key = f"D{dd}B{bnd}E{ee}G{gg}F{ff}"
                        fac[key] = slim(H.score(rv, M, sel, rs))
    out["D_factorial"] = fac
    b0 = fac["D0B0E0G0F0"]["net"]
    full = fac["D1B1E1G1F1"]["net"]
    stand = {"delay": fac["D1B0E0G0F0"]["net"] - b0,
             "band_given_delay": fac["D1B1E0G0F0"]["net"] - fac["D1B0E0G0F0"]["net"],
             "exit": fac["D0B0E1G0F0"]["net"] - b0,
             "gate": fac["D0B0E0G1F0"]["net"] - b0,
             "floor": fac["D0B0E0G0F1"]["net"] - b0}
    marg = {"delay+band": full - fac["D0B0E1G1F1"]["net"],
            "band_only": full - fac["D1B0E1G1F1"]["net"],
            "exit": full - fac["D1B1E0G1F1"]["net"],
            "gate": full - fac["D1B1E1G0F1"]["net"],
            "floor": full - fac["D1B1E1G1F0"]["net"]}
    out["D_summary"] = {"baseline_shipped_net": b0, "joint_net": full,
                        "joint_gain": full - b0, "standalone": stand, "marginal": marg,
                        "sum_standalone": sum(stand.values()),
                        "sum_marginal": sum(marg.values())}
    print("D done", json.dumps({k2: round(v, 5) for k2, v in out["D_summary"]["marginal"].items()}),
          flush=True)

    # ---- E. per-symbol ratio at a few gates
    E = {}
    for lab, kw in (("ungated", {}), ("gate_R<=0.05", {"gate_total": 0.05}),
                    ("gate_R<=0.02", {"gate_total": 0.02}),
                    ("gate_bps<=1.0", {"gate_bps": 1.0}),
                    ("best_cell", {"gate_total": bg, "entry_lo": bb[0], "entry_hi": bb[1]})):
        sel = H.population(M, trd, c0, **kw)
        g = H.by_group(r, M, sel, "symbol")
        E[lab] = {"n": int(sel.sum()), "per_symbol": {s: slim(v) for s, v in g.items()},
                  "n_ratio_gt_1": sum(1 for v in g.values() if (v["ratio_bps"] or 0) > 1),
                  "n_net_pos": sum(1 for v in g.values() if v["net"] > 0),
                  "n_net_pos_n_ge_100": sum(1 for v in g.values()
                                            if v["net"] > 0 and v["n"] >= 100)}
    out["E_per_symbol"] = E

    # ---- F. TRAIN / TEST over the C surface
    F = {}
    for held in MONTHS:
        tr_m = [m for m in MONTHS if m != held]
        best = None
        for bn, lo, hi in BANDS:
            for g in RGATES:
                sel = H.population(M, trd, c0, entry_lo=lo, entry_hi=hi, gate_total=g)
                str_ = sel & np.isin(M["month"], tr_m)
                if str_.sum() < 200:
                    continue
                nt = (r[str_] - M["cost_true"][str_]).mean()
                if best is None or nt > best[0]:
                    best = (float(nt), bn, g, lo, hi, int(str_.sum()))
        _, bn, g, lo, hi, ntr = best
        sel = H.population(M, trd, c0, entry_lo=lo, entry_hi=hi, gate_total=g)
        ste = sel & (M["month"] == held)
        F[held] = {"train_months": tr_m, "chosen_band": bn, "chosen_gate_R": g,
                   "train_n": ntr, "train_net": round(best[0], 6),
                   "test": slim(H.score(r, M, ste, reason))}
        print("F", held, bn, g, "train_net", round(best[0], 5),
              "TEST n", F[held]["test"]["n"], "net", F[held]["test"].get("net"), flush=True)
    out["F_train_test"] = F

    # ---- G. equity / days / truncation, at ungated and at the best cell
    G = {}
    for lab, kw in (("ungated", {}),
                    ("best_cell", {"gate_total": bg, "entry_lo": bb[0], "entry_hi": bb[1]}),
                    ("gate_R<=0.02", {"gate_total": 0.02}),
                    ("gate_bps<=1.0", {"gate_bps": 1.0})):
        sel = H.population(M, trd, c0, **kw)
        bd = H.by_day(r, M, sel)
        days = sorted(bd)
        cum, eq = 0.0, []
        for d in days:
            cum += bd[d]["sum_net"]; eq.append(round(cum, 3))
        peak, dd = -1e18, 0.0
        for e in eq:
            peak = max(peak, e); dd = min(dd, e - peak)
        G[lab] = {"score": slim(H.score(r, M, sel, reason)),
                  "n_days": len(days),
                  "n_days_net_pos": sum(1 for d in days if bd[d]["net"] > 0),
                  "n_days_gross_pos": sum(1 for d in days if bd[d]["gross"] > 0),
                  "equity_net_R": eq, "max_dd_R": round(dd, 3),
                  "final_net_R": eq[-1] if eq else 0.0,
                  "boot_net": H.bootstrap_days(r, M, sel, field="net"),
                  "boot_gross": H.bootstrap_days(r, M, sel, field="gross"),
                  "per_day": bd}
    out["G_paths"] = G
    json.dump(out, open(f"{D}/H6_DEEP_{tag}_V1.json", "w"), indent=1)
    print("wrote", f"H6_DEEP_{tag}_V1.json", round(time.time() - t0, 1), flush=True)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), parse(sys.argv[3]), parse(sys.argv[4]),
         parse(sys.argv[5]), None if sys.argv[6] in ("None", "none", "-") else int(sys.argv[6]))
