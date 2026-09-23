"""h6 step 12 — a full dossier for every cell this lane wants to put on the record.

For each: economics under BOTH cost bases (flat median spread = the swarm's basis, and
hour-true broker spread), month split, per-symbol, equity path, day positivity,
day-block bootstrap, horizon sensitivity, truncation share, and a train/test read.
"""
import json, os, sys, time

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h6_lib as H  # noqa: E402

MONTHS = ("2026-01", "2026-02", "2026-03")


def slim(s):
    return {k: (round(v, 6) if isinstance(v, float) else v) for k, v in s.items()}


CELLS = [
    ("A_SWARM_REPAIRED", dict(k=5, target=None, stop=-1.0, trail=0.25, maxbars=None), {}),
    ("B_HOURCAP_060_k3", dict(k=3, target=None, stop=-1.0, trail=None, maxbars=120),
     {"hour_bps": 0.60}),
    ("C_HOURCAP_068_k3", dict(k=3, target=None, stop=-1.0, trail=None, maxbars=120),
     {"hour_bps": 0.68}),
    ("D_HOURCAP_060_k8_band", dict(k=8, target=None, stop=-1.0, trail=None, maxbars=120),
     {"hour_bps": 0.60, "entry_lo": -0.10, "entry_hi": 0.10}),
    ("E_XAUUSD_k30_tr010_mb60", dict(k=30, target=None, stop=-1.0, trail=0.10, maxbars=60),
     {"symbols": ["XAUUSD"]}),
    ("F_US30_k3_STOPONLY", dict(k=3, target=None, stop=-1.0, trail=None, maxbars=120),
     {"symbols": ["US30_cash"]}),
    ("G_GER40_k3_STOPONLY", dict(k=3, target=None, stop=-1.0, trail=None, maxbars=120),
     {"symbols": ["GER40"]}),
    ("H_NAS100_k20_tr010", dict(k=20, target=None, stop=-1.0, trail=0.10, maxbars=None),
     {"symbols": ["NAS100"]}),
    ("I_SWARM_CONTRACT_HOURCAP060", dict(k=5, target=None, stop=-1.0, trail=0.25,
                                         maxbars=None), {"hour_bps": 0.60}),
]


def main():
    t0 = time.time()
    P, M = H.load()
    cost_hour = np.load(f"{D}/h6_cost_hour.npy")
    bh = np.load(f"{D}/h6_broker_hour.npy")
    Mh = dict(M); Mh["cost_true"] = cost_hour
    hour_bps = cost_hour * M["bpsfac"]
    out = {}

    for lab, cw, pw in CELLS:
        pw = dict(pw)
        hcap = pw.pop("hour_bps", None)
        r, reason, _e, trd, c0 = H.walk_all(P, **cw)
        sel = H.population(M, trd, c0, **pw) & np.isfinite(cost_hour)
        if hcap is not None:
            sel &= hour_bps <= hcap + 1e-12
        rec = {"contract": cw, "population": dict(pw, hour_bps_cap=hcap),
               "n": int(sel.sum()),
               "flat_cost": slim(H.score(r, M, sel, reason)),
               "hour_true_cost": slim(H.score(r, Mh, sel, reason)),
               "per_symbol_hourcost": {s: slim(v) for s, v in
                                       H.by_group(r, Mh, sel, "symbol").items()},
               "per_month_hourcost": {s: slim(v) for s, v in
                                      H.by_group(r, Mh, sel, "month").items()},
               "boot_net_hourcost": H.bootstrap_days(r, Mh, sel, field="net"),
               "boot_gross": H.bootstrap_days(r, Mh, sel, field="gross")}
        bd = H.by_day(r, Mh, sel)
        days = sorted(bd)
        cum, eq = 0.0, []
        for d in days:
            cum += bd[d]["sum_net"]; eq.append(round(cum, 3))
        peak, dd = -1e18, 0.0
        for e in eq:
            peak = max(peak, e); dd = min(dd, e - peak)
        rec.update({"n_days": len(days),
                    "n_days_net_pos": sum(1 for d in days if bd[d]["net"] > 0),
                    "n_days_gross_pos": sum(1 for d in days if bd[d]["gross"] > 0),
                    "equity_net_R": eq, "max_dd_R": round(dd, 3),
                    "final_net_R": eq[-1] if eq else 0.0, "per_day": bd})
        # train Jan+Feb -> test Mar, and leave-one-out
        loo = {}
        for held in MONTHS:
            te = sel & (M["month"] == held)
            loo[held] = {"n": int(te.sum()),
                         "net_hour": round(float((r[te] - cost_hour[te]).mean()), 6)
                         if te.sum() else None,
                         "total_R_hour": round(float((r[te] - cost_hour[te]).sum()), 3)
                         if te.sum() else None}
        rec["per_month_readout"] = loo
        rec["months_net_pos"] = sum(1 for m in MONTHS
                                    if (loo[m]["net_hour"] or -1) > 0)
        # horizon sensitivity
        hz = []
        for mb in (15, 30, 45, 60, 90, 120, None):
            rr, rs, _e2, td, cc = H.walk_all(P, k=cw["k"], target=cw["target"],
                                             stop=cw["stop"], trail=cw["trail"], maxbars=mb)
            s2 = td & sel
            if s2.sum() < 50:
                continue
            s = slim(H.score(rr, Mh, s2, rs)); s["maxbars"] = mb
            hz.append(s)
        rec["horizon_sensitivity_hourcost"] = hz
        out[lab] = rec
        f, h = rec["flat_cost"], rec["hour_true_cost"]
        print(f"{lab:<26} n {rec['n']:>6}  netFLAT {f['net']:+.5f} rr {f['ratio_r']:.2f}"
              f" | netHOUR {h['net']:+.5f} rr {h['ratio_r']:.2f} t {h['t_net']:+.2f}"
              f" | mo+ {rec['months_net_pos']}/3 days+ {rec['n_days_net_pos']}/{rec['n_days']}"
              f" trunc {h['share_maxbars_truncated']:.3f} p<=0 {rec['boot_net_hourcost']['p_le_0']:.3f}"
              f" finalR {rec['final_net_R']:+.1f} DD {rec['max_dd_R']:.1f}", flush=True)

    json.dump(out, open(f"{D}/H6_DOSSIER_V1.json", "w"), indent=1)
    print("wrote H6_DOSSIER_V1.json", round(time.time() - t0, 1), flush=True)


if __name__ == "__main__":
    main()
