"""h6 step 15 — the placebo panel. THE control this whole lane turns on.

The swarm's headline is +0.038342 R/trade gross at t +12.35 under (delay 5 min,
TRAIL025). Step 14 found that the SAME contract on a decision instant shifted +60 min
books +0.038659 at t +12.64 on the same rows. If that holds across shifts and delays,
the headline measures the CONTRACT, not the signal.

Panel: shift in {-120,-90,-60,+60,+90,+120,+180} x k in {0,1,2,3,5,8,15,30} x two
contracts (the swarm's TRAIL025 and this lane's joint optimum), all on the identical
rows, all with the identical cost.

The discriminating prediction, if the delay lever is a real repair of the generator's
own trigger-bar concession (l7-F5, entry = bar.close of the trigger bar):
    REAL cohort   : k=0 much worse than k>=1   (the concession exists)
    PLACEBO cohort: k=0 same as k>=1           (no trigger bar, no concession)
"""
import gzip, json, os, sys, time

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h6_lib as H  # noqa: E402
import h6_14_controls as C  # noqa: E402
import h6_02_build_cache as B  # noqa: E402

KS = [0, 1, 2, 3, 5, 8, 15, 30]
SHIFTS = [-120, -90, -60, 60, 90, 120, 180]
CONTRACTS = {"SWARM_TRAIL025": dict(target=None, stop=-1.0, trail=0.25, maxbars=None),
             "H6_OPTIMUM": dict(target=None, stop=-2.0, trail=0.10, maxbars=60),
             "SHIPPED_INC_2R": dict(target=2.0, stop=-1.0, trail=None, maxbars=None),
             "NO_TRAIL_STOPONLY": dict(target=None, stop=-1.0, trail=None, maxbars=None)}


def stats(v):
    n = len(v)
    m = float(v.mean()); s = float(v.std(ddof=1) / np.sqrt(n))
    return {"n": n, "mean": round(m, 6), "t": round(m / s, 3)}


def main():
    t0 = time.time()
    P, M = H.load()
    cost_hour = np.load(f"{D}/h6_cost_hour.npy")
    hour_bps = cost_hour * M["bpsfac"]
    rows = []
    for mk, ml, path in B.FILES:
        for x in gzip.open(path, "rt"):
            if x.strip():
                q = json.loads(x); q["_mk"] = mk; rows.append(q)
    out = {"note": "gross R/trade; identical rows, identical contract, identical cost. "
                   "PLACEBO = the same instrument/side/risk-unit entered at a bar close "
                   "SHIFT minutes away from the decision instant."}

    caches = {"REAL": P}
    for sh in SHIFTS:
        caches[str(sh)] = C.build_shifted(rows, sh)
        print("built", sh, round(time.time() - t0, 1), flush=True)

    CELL = None
    res = {}
    for cname, cw in CONTRACTS.items():
        res[cname] = {}
        for lab, PP in caches.items():
            row = {}
            for k in KS:
                r, reason, _e, trd, c0 = H.walk_all(PP, k=k, **cw)
                rr, _rs, _e2, td2, _c2 = H.walk_all(P, k=k, **cw)
                both = trd & td2 & np.isfinite(cost_hour)
                row[str(k)] = stats(r[both])
            res[cname][lab] = row
        print(cname, "REAL k5", res[cname]["REAL"]["5"], "PLACEBO+60 k5",
              res[cname]["60"]["5"], flush=True)
    out["panel_full_cohort"] = res

    # the same panel restricted to the paying cell (hour-true cost <= 0.60 bps)
    cellres = {}
    for cname, cw in CONTRACTS.items():
        cellres[cname] = {}
        for lab, PP in caches.items():
            row = {}
            for k in (5, 30):
                r, reason, _e, trd, c0 = H.walk_all(PP, k=k, **cw)
                rr, _rs, _e2, td2, _c2 = H.walk_all(P, k=k, **cw)
                both = (trd & td2 & np.isfinite(cost_hour)
                        & (hour_bps <= 0.60 + 1e-12))
                g = r[both]; c = cost_hour[both]
                nt = g - c
                row[str(k)] = {"n": int(both.sum()), "gross": round(float(g.mean()), 6),
                               "net": round(float(nt.mean()), 6),
                               "t_net": round(float(nt.mean() / (nt.std(ddof=1)
                                                                 / np.sqrt(int(both.sum())))), 3),
                               "ratio_r": round(float(g.mean() / c.mean()), 4)}
            cellres[cname][lab] = row
    out["panel_paying_cell_hourbps_le_060"] = cellres

    # summary: signal contribution = REAL - mean(PLACEBO)
    summ = {}
    for cname in CONTRACTS:
        for k in KS:
            real = res[cname]["REAL"][str(k)]["mean"]
            pls = [res[cname][str(s)][str(k)]["mean"] for s in SHIFTS]
            summ[f"{cname}|k={k}"] = {
                "real_gross": real, "placebo_mean": round(float(np.mean(pls)), 6),
                "placebo_min": round(float(np.min(pls)), 6),
                "placebo_max": round(float(np.max(pls)), 6),
                "signal_contribution": round(real - float(np.mean(pls)), 6),
                "real_beats_all_placebos": bool(real > max(pls))}
    out["signal_contribution"] = summ

    print("\n=== gross R/trade: REAL vs placebo mean (7 shifts) ===")
    print(f"{'contract':<20}{'k':>4}{'REAL':>11}{'PLACEBO_mean':>14}{'min':>10}{'max':>10}{'SIGNAL':>10}")
    for cname in CONTRACTS:
        for k in KS:
            v = summ[f"{cname}|k={k}"]
            print(f"{cname:<20}{k:>4}{v['real_gross']:>11.6f}{v['placebo_mean']:>14.6f}"
                  f"{v['placebo_min']:>10.6f}{v['placebo_max']:>10.6f}{v['signal_contribution']:>+10.6f}")

    json.dump(out, open(f"{D}/H6_PLACEBO_PANEL_V1.json", "w"), indent=1)
    print("\nwrote H6_PLACEBO_PANEL_V1.json", round(time.time() - t0, 1), flush=True)


if __name__ == "__main__":
    main()
