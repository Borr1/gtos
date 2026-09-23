#!/usr/bin/env python3
"""x3_07_prize — what earliness is WORTH, per family, at broker-true cost, with CIs.

Per-row broker-true toll, rd-aware:
    toll_bps(row) = tick-archive median spread bps (L10X_TICK_SPREAD_V1, FTMO, full
                    population per symbol)
                  + (real_tot_med - real_spr_med)(sym) expressed in bps at that symbol's
                    median bps-per-R (L10X_POOL_RECOST_V1: commission + slippage)
    toll_R(row)   = toll_bps / bps_per_R(row)
Swap is 0 at a 2-hour horizon, as L10X charged it.
"""
from __future__ import annotations
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import x3_lib as X

KS = [-15, -13, -11, -10, -9, -8, -7, -6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 5, 8, 10, 15, 30]


def build_toll(t):
    ts = json.load(open(os.path.join(HERE, "L10X_TICK_SPREAD_V1.json")))
    rc = json.load(open(os.path.join(HERE, "L10X_POOL_RECOST_V1.json")))["per_symbol"]
    atm = t.born == "born_at_limit"
    toll_bps = {}
    for s in sorted(set(t.sym)):
        m = t.sym == s
        bpr = float(np.median(t.bps_per_R[m & atm])) if (m & atm).sum() else float(
            np.median(t.bps_per_R[m]))
        spr = ts.get(f"ftmo:{s}", {}).get("spread_bps_median")
        if spr is None:
            spr = rc[s]["real_spr_med"] * bpr
        cs = (rc[s]["real_tot_med"] - rc[s]["real_spr_med"]) * bpr
        toll_bps[s] = float(spr + cs)
    tb = np.array([toll_bps[s] for s in t.sym])
    toll_R = tb / t.bps_per_R
    return toll_R, tb, toll_bps


def main():
    t = X.Tape()
    z = np.load(os.path.join(HERE, "x3_SWEEP_RAW.npz"), allow_pickle=False)
    sup = z["support"]; atm = z["atm"]
    base = atm & sup
    toll_R, toll_bps, tbl = build_toll(t)
    out = {"toll_bps_by_symbol": tbl,
           "toll_R_mean_all_rows": float(toll_R.mean()),
           "toll_R_mean_at_market": float(toll_R[atm].mean()),
           "toll_bps_mean_at_market": float(toll_bps[atm].mean()),
           "L10X_reference_toll_R_all_rows": 0.189297,
           "frozen_cost_R_mean_at_market": float(t.cost_r[atm].mean())}
    print("broker-true toll: %.5f R all rows (L10X reference 0.189297), %.5f R at-market, "
          "%.4f bps at-market; frozen model charges %.5f R"
          % (out["toll_R_mean_all_rows"], out["toll_R_mean_at_market"],
             out["toll_bps_mean_at_market"], out["frozen_cost_R_mean_at_market"]))

    fams = sorted(set(t.fam[base]))
    res = {}
    print("\n=== per-family offset curve, POOL contract, NET of broker-true toll (R/trade) ===")
    hdr = "".join(f"{k:+9d}" for k in [-15, -10, -5, -2, 0, 2, 5, 10])
    print(f"{'family':34s}{'n':>6s}" + hdr + "   k*  lift_vs_k0   CI95        P(<=0)")
    for f in list(fams) + ["ALL_AT_MARKET"]:
        m = base if f == "ALL_AT_MARKET" else (base & (t.fam == f))
        if m.sum() < 50:
            continue
        cur = {}
        for k in KS:
            r = z[f"pool_{k}"]
            mm = m & ~np.isnan(r)
            cur[k] = {"n": int(mm.sum()), "gross_R": float(r[mm].mean()),
                      "net_R": float((r[mm] - toll_R[mm]).mean()),
                      "gross_bps": float((r[mm] * t.bps_per_R[mm]).mean()),
                      "net_bps": float(((r[mm] - toll_R[mm]) * t.bps_per_R[mm]).mean()),
                      "win": float((r[mm] > 0).mean()),
                      "target_rate": float((z[f"reason_pool_{k}"][mm] == 1).mean()),
                      "stop_rate": float((z[f"reason_pool_{k}"][mm] == 2).mean())}
        bk = max(KS, key=lambda k: cur[k]["net_R"])
        r0 = z["pool_0"]; rb = z[f"pool_{bk}"]
        mm = m & ~np.isnan(r0) & ~np.isnan(rb)
        d = rb[mm] - r0[mm]
        bt = X.dayboot(t.day[mm], d, reps=2000)
        res[f] = {"curve": cur, "best_k": bk, "lift_R": float(d.mean()),
                  "lift_bps": float((d * t.bps_per_R[mm]).mean()), "dayboot_lift": bt,
                  "n": int(m.sum())}
        row = "".join(f"{cur[k]['net_R']:+9.4f}" for k in [-15, -10, -5, -2, 0, 2, 5, 10])
        print(f"{f:34s}{int(m.sum()):6d}" + row +
              f" {bk:+4d} {d.mean():+9.4f} [{bt['lo95']:+.4f},{bt['hi95']:+.4f}] {bt['p_le_0']:.3f}")
    out["by_family"] = res

    # ---- the prize: the earliness-positive families, entered at k*, as a book
    gain = [f for f in fams if res.get(f) and res[f]["best_k"] < 0]
    lose = [f for f in fams if res.get(f) and res[f]["best_k"] >= 0]
    out["families_helped_by_earliness"] = gain
    out["families_not_helped"] = lose
    for tag, fl in (("EARLY_FAMILIES", gain), ("LATE_FAMILIES", lose)):
        m = base & np.isin(t.fam, fl)
        if m.sum() < 50:
            continue
        blk = {}
        for k in KS:
            r = z[f"pool_{k}"]; mm = m & ~np.isnan(r)
            blk[k] = {"n": int(mm.sum()), "gross_R": float(r[mm].mean()),
                      "net_R": float((r[mm] - toll_R[mm]).mean()),
                      "total_net_R": float((r[mm] - toll_R[mm]).sum()),
                      "net_bps": float(((r[mm] - toll_R[mm]) * t.bps_per_R[mm]).mean())}
        out[tag] = {"families": fl, "n": int(m.sum()), "curve": blk}
        print(f"\n=== {tag} ({len(fl)} families, n={m.sum()}) ===")
        print("  k    netR      total_net_R   net_bps")
        for k in KS:
            print(f" {k:+4d} {blk[k]['net_R']:+9.4f} {blk[k]['total_net_R']:+12.1f} "
                  f"{blk[k]['net_bps']:+9.4f}")
        # per-k day bootstrap of the level
        r = z[f"pool_{max(KS, key=lambda k: blk[k]['net_R'])}"]
        mm = m & ~np.isnan(r)
        out[tag]["best_k"] = int(max(KS, key=lambda k: blk[k]["net_R"]))
        out[tag]["dayboot_best_level"] = X.dayboot(t.day[mm], r[mm] - toll_R[mm], reps=2000)
        b = out[tag]["dayboot_best_level"]
        print(f"  best k={out[tag]['best_k']:+d} net {b['mean']:+.5f} "
              f"CI95[{b['lo95']:+.5f},{b['hi95']:+.5f}] P(<=0)={b['p_le_0']:.3f}")

    # ---- true-first-minute adverse selection (the estate's 55.65% refreshed)
    j1 = t.j(0)                                  # the minute [T, T+1) the sidecar never sees
    adv1 = t.advE[:, j1]
    m = sup & ~np.isnan(adv1)
    touched = m & (adv1 <= 0)
    r0 = z["pool_0"]
    out["true_first_minute"] = {
        "n": int(m.sum()),
        "share_entry_touched_in_true_first_60s": float(touched[m].sum() / m.sum()),
        "gross_R_touched": float(np.nanmean(r0[touched])),
        "gross_R_not_touched": float(np.nanmean(r0[m & ~touched])),
        "at_market_share_touched": float(touched[m & atm].sum() / (m & atm).sum()),
        "sidecar_bar1_share_touched": float(
            (t.advE[:, t.j(1)][m] <= 0).sum() / m.sum()),
    }
    print("\n=== the TRUE first 60 seconds (the minute the sealed sidecar skips) ===")
    for k, v in out["true_first_minute"].items():
        print(f"  {k:48s} {v}")

    json.dump(out, open(os.path.join(HERE, "X3_PRIZE_V1.json"), "w"), indent=1)
    print("\nwrote X3_PRIZE_V1.json")


if __name__ == "__main__":
    main()
