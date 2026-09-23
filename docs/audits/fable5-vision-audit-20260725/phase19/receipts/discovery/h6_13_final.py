"""h6 step 13 — the final joint object.

  1. contract-axis ablation done properly: ADD-ONE (standalone) vs LEAVE-ONE-OUT
     (marginal), read off the 25,800-contract sweep, plus the additivity ratio.
  2. the sweep optimum re-priced at HOUR-TRUE cost, with the hour-true affordability
     cap applied on top -> the best joint form this lane can find.
  3. risk-normalised economics (a stop at -2R risks twice the declared unit).
  4. equity, day positivity, bootstrap, truncation for every headline cell.
"""
import gzip, json, os, sys, time

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h6_lib as H  # noqa: E402

MONTHS = ("2026-01", "2026-02", "2026-03")
DEFAULTS = {"k": 0, "trail": None, "target": 2.0, "stop": -1.0, "maxbars": None}
OPT = {"k": 30, "trail": 0.10, "target": None, "stop": -2.0, "maxbars": 60}


def slim(s):
    return {k: (round(v, 6) if isinstance(v, float) else v) for k, v in s.items()}


def main():
    t0 = time.time()
    out = {}

    # ---------- 1. contract-axis ablation from the sweep
    idx = {}
    for line in gzip.open(f"{D}/h6_SWEEP_V1.jsonl.gz", "rt"):
        r = json.loads(line)
        if r["gate"] != "ungated":
            continue
        idx[(r["k"], r["trail"], r["target"], r["stop"], r["maxbars"])] = r

    def key(d):
        return (d["k"], d["trail"], d["target"], d["stop"], d["maxbars"])

    base = idx[key(DEFAULTS)]
    opt = idx[key(OPT)]
    add1, loo = {}, {}
    for ax in DEFAULTS:
        d = dict(DEFAULTS); d[ax] = OPT[ax]
        a = idx.get(key(d))
        add1[ax] = {"net": a["net"], "gross": a["gross"], "delta_net": round(a["net"] - base["net"], 6),
                    "delta_gross": round(a["gross"] - base["gross"], 6)}
        d2 = dict(OPT); d2[ax] = DEFAULTS[ax]
        b = idx.get(key(d2))
        loo[ax] = {"net": b["net"], "gross": b["gross"],
                   "marginal_net": round(opt["net"] - b["net"], 6),
                   "marginal_gross": round(opt["gross"] - b["gross"], 6)}
    out["contract_ablation"] = {
        "baseline_shipped_k0_2R_1R": base, "joint_optimum": opt,
        "add_one_standalone": add1, "leave_one_out_marginal": loo,
        "joint_gain_net": round(opt["net"] - base["net"], 6),
        "joint_gain_gross": round(opt["gross"] - base["gross"], 6),
        "sum_standalone_net": round(sum(v["delta_net"] for v in add1.values()), 6),
        "sum_marginal_net": round(sum(v["marginal_net"] for v in loo.values()), 6)}
    ca = out["contract_ablation"]
    ca["standalone_overcount_x"] = round(ca["sum_standalone_net"] / ca["joint_gain_net"], 4)
    ca["marginal_overcount_x"] = round(ca["sum_marginal_net"] / ca["joint_gain_net"], 4)
    ca["double_counted_pct_standalone"] = round(
        100 * (1 - ca["joint_gain_net"] / ca["sum_standalone_net"]), 2)
    print("=== contract-axis ablation ===")
    print(f"baseline(shipped k0 2R/-1R) net {base['net']}  gross {base['gross']}")
    print(f"joint optimum {OPT} net {opt['net']} gross {opt['gross']} t {opt['tg']}")
    print(f"{'axis':<9}{'standalone dNet':>17}{'marginal dNet':>15}{'standalone dGross':>19}{'marginal dGross':>17}")
    for ax in DEFAULTS:
        print(f"{ax:<9}{add1[ax]['delta_net']:>17.6f}{loo[ax]['marginal_net']:>15.6f}"
              f"{add1[ax]['delta_gross']:>19.6f}{loo[ax]['marginal_gross']:>17.6f}")
    print(f"joint gain net {ca['joint_gain_net']}  sum standalone {ca['sum_standalone_net']}"
          f" ({ca['double_counted_pct_standalone']}% double-counted)  sum marginal {ca['sum_marginal_net']}")

    # ---------- 2/3/4 full economics of the headline forms
    P, M = H.load()
    cost_hour = np.load(f"{D}/h6_cost_hour.npy")
    Mh = dict(M); Mh["cost_true"] = cost_hour
    hour_bps = cost_hour * M["bpsfac"]

    FORMS = [
        ("R0_shipped_k0_2R", dict(DEFAULTS), None),
        ("R1_swarm_k5_TRAIL025", dict(k=5, trail=0.25, target=None, stop=-1.0, maxbars=None), None),
        ("R2_joint_optimum_ungated", dict(OPT), None),
        ("R3_joint_optimum_hourcap_1.0", dict(OPT), 1.0),
        ("R4_joint_optimum_hourcap_0.8", dict(OPT), 0.8),
        ("R5_joint_optimum_hourcap_0.68", dict(OPT), 0.68),
        ("R6_joint_optimum_hourcap_0.60", dict(OPT), 0.60),
        ("R7_joint_optimum_hourcap_0.50", dict(OPT), 0.50),
        ("R8_gate005_best_k5_tr010_s2_mb60",
         dict(k=5, trail=0.10, target=None, stop=-2.0, maxbars=60), None),
        ("R9_gate002_best_k30_tr075_s15_mb60",
         dict(k=30, trail=0.75, target=None, stop=-1.5, maxbars=60), None),
    ]
    res = {}
    for lab, cw, hcap in FORMS:
        r, reason, _e, trd, c0 = H.walk_all(P, **cw)
        sel = trd & np.isfinite(cost_hour)
        if hcap is not None:
            sel = sel & (hour_bps <= hcap + 1e-12)
        if lab.startswith("R8"):
            sel = sel & (M["cost_true"] <= 0.05 + 1e-12)
        if lab.startswith("R9"):
            sel = sel & (M["cost_true"] <= 0.02 + 1e-12)
        sf = H.score(r, M, sel, reason)
        sh = H.score(r, Mh, sel, reason)
        risk = abs(cw["stop"]) if cw["stop"] else 1.0
        bd = H.by_day(r, Mh, sel)
        days = sorted(bd)
        cum, eq = 0.0, []
        for d in days:
            cum += bd[d]["sum_net"]; eq.append(round(cum, 3))
        peak, dd = -1e18, 0.0
        for e in eq:
            peak = max(peak, e); dd = min(dd, e - peak)
        mo = {}
        for m in MONTHS:
            s2 = sel & (M["month"] == m)
            mo[m] = {"n": int(s2.sum()),
                     "net_hour": round(float((r[s2] - cost_hour[s2]).mean()), 6) if s2.sum() else None}
        rec = {"contract": cw, "hour_bps_cap": hcap, "n": int(sel.sum()),
               "flat_cost": slim(sf), "hour_true_cost": slim(sh),
               "risk_units_per_trade": risk,
               "net_per_unit_risk_hour": round(sh["net"] / risk, 6),
               "gross_per_unit_risk_hour": round(sh["gross"] / risk, 6),
               "cost_per_unit_risk_hour": round(sh["cost"] / risk, 6),
               "months": mo,
               "months_net_pos": sum(1 for m in MONTHS if (mo[m]["net_hour"] or -1) > 0),
               "n_days": len(days),
               "n_days_net_pos": sum(1 for d in days if bd[d]["net"] > 0),
               "n_days_gross_pos": sum(1 for d in days if bd[d]["gross"] > 0),
               "equity_net_R": eq, "max_dd_R": round(dd, 3),
               "final_net_R": eq[-1] if eq else 0.0,
               "boot_net_hour": H.bootstrap_days(r, Mh, sel, field="net"),
               "boot_gross": H.bootstrap_days(r, Mh, sel, field="gross"),
               "per_symbol_hour": {s: slim(v) for s, v in H.by_group(r, Mh, sel, "symbol").items()},
               "per_day": bd}
        rec["n_symbols_net_pos"] = sum(1 for v in rec["per_symbol_hour"].values() if v["net"] > 0)
        rec["n_symbols_gross_pos"] = sum(1 for v in rec["per_symbol_hour"].values() if v["gross"] > 0)
        rec["n_symbols"] = len(rec["per_symbol_hour"])
        res[lab] = rec
        print(f"{lab:<34} n {rec['n']:>6} grossH {sh['gross']:+.5f} costH {sh['cost']:.5f}"
              f" netH {sh['net']:+.5f} rr {sh['ratio_r']:.3f} rb {(sh['ratio_bps'] or 0):.3f}"
              f" t {sh['t_net']:+.2f} | mo+ {rec['months_net_pos']}/3 d+ {rec['n_days_net_pos']}/{rec['n_days']}"
              f" trunc {sh['share_maxbars_truncated']:.3f} p<=0 {rec['boot_net_hour']['p_le_0']:.3f}"
              f" R {rec['final_net_R']:+.1f} DD {rec['max_dd_R']:.1f} sym+ {rec['n_symbols_net_pos']}/{rec['n_symbols']}",
              flush=True)
    out["forms"] = res
    json.dump(out, open(f"{D}/H6_FINAL_V1.json", "w"), indent=1)
    print("wrote H6_FINAL_V1.json", round(time.time() - t0, 1), flush=True)


if __name__ == "__main__":
    main()
