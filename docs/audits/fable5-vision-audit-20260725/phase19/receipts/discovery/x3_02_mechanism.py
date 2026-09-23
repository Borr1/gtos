#!/usr/bin/env python3
"""x3_02_mechanism — decompose the offset curve.

1. the average market path through the forming M15 bar, in the trade's own R units
2. the raw price head-start (-m) vs the R actually captured -> capture efficiency
3. how many early entries are already dead (stopped) before the signal exists
4. the 60-second blind spot the sealed sidecar bakes in
"""
from __future__ import annotations
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import x3_lib as X

OFFSETS = list(range(-15, 31))


def main():
    t = X.Tape()
    z = np.load(os.path.join(HERE, "x3_SWEEP_RAW.npz"), allow_pickle=False)
    sup = z["support"]; atm = z["atm"]
    m = atm & sup
    out = {"n": int(m.sum())}

    # ---- 1. mean market offset m(k): R the market sits at, relative to the shipped entry
    rows = []
    for k in OFFSETS:
        je = t.j(k) - 1
        mm = t.mR[m, je]
        v = ~np.isnan(mm)
        rows.append({"k": k, "n": int(v.sum()), "mean_mR": float(mm[v].mean()),
                     "median_mR": float(np.median(mm[v])),
                     "share_market_better_than_shipped": float((mm[v] < 0).mean())})
    out["market_path_R"] = rows
    print("=== market position at instant T+k, in the trade's own R (0 = shipped entry) ===")
    print(" k   mean_mR  median  share m<0 (better entry)   head_start(-mean_mR)")
    for r in rows:
        print(f"{r['k']:+4d} {r['mean_mR']:+8.4f} {r['median_mR']:+8.4f} "
              f"{r['share_market_better_than_shipped']:8.4f}      {-r['mean_mR']:+8.4f}")

    # ---- 2. capture efficiency: delta gross R vs the raw price head start
    cap = []
    for contract in ("pool", "trail"):
        r0 = z[f"{contract}_0"]
        for k in OFFSETS:
            rk = z[f"{contract}_{k}"]
            mm = m & ~np.isnan(rk) & ~np.isnan(r0)
            head = -t.mR[mm, t.j(k) - 1].mean()
            d = (rk[mm] - r0[mm]).mean()
            cap.append({"contract": contract, "k": k, "n": int(mm.sum()),
                        "head_start_R": float(head), "delta_R": float(d),
                        "capture_eff": float(d / head) if abs(head) > 1e-9 else None})
    out["capture"] = cap
    print("\n=== capture efficiency (delta gross R per R of price head start) ===")
    print(" k   head_start   pool_delta  eff   trail_delta  eff")
    for k in OFFSETS:
        p = next(c for c in cap if c["contract"] == "pool" and c["k"] == k)
        q = next(c for c in cap if c["contract"] == "trail" and c["k"] == k)
        print(f"{k:+4d} {p['head_start_R']:+10.5f} {p['delta_R']:+11.5f} "
              f"{(p['capture_eff'] or 0):5.2f} {q['delta_R']:+12.5f} {(q['capture_eff'] or 0):5.2f}")

    # ---- 3. early entries already dead before the signal exists
    dead = []
    for k in OFFSETS:
        if k >= 0:
            continue
        res = X.walk(t, k, contract="pool", sub=m)
        s = res["sel"]
        eb = res["exit_bar"]
        # bars walked before the decision instant = -k  (labels T+k .. T-1)
        pre = (eb <= -k) & (res["reason"] == 2) & s
        pre_t = (eb <= -k) & (res["reason"] == 1) & s
        dead.append({"k": k, "n": int(s.sum()),
                     "stopped_before_decision": float(pre.sum() / s.sum()),
                     "targeted_before_decision": float(pre_t.sum() / s.sum()),
                     "resolved_before_decision": float((pre.sum() + pre_t.sum()) / s.sum())})
    out["pre_decision_resolution"] = dead
    print("\n=== share of an early-entered trade already RESOLVED before the signal exists ===")
    print(" k    stopped   targeted   resolved")
    for d in dead:
        print(f"{d['k']:+4d} {d['stopped_before_decision']:9.4f} "
              f"{d['targeted_before_decision']:9.4f} {d['resolved_before_decision']:9.4f}")

    # ---- 4. the 60-second blind spot the sidecar bakes in
    r_true = X.walk(t, 0, contract="pool", sub=m)          # walks from label T+0
    # sidecar convention: walk from label T+1
    r_sc = X.walk(t, 1, contract="pool", sub=m)            # NOT the same: entry moves too
    # exact sidecar arm: entry at T (k=0 price) but first walk bar T+1
    tt = t
    save = tt.valid[:, tt.j(0)].copy()
    tt.valid[:, tt.j(0)] = False
    r_skip = X.walk(tt, 0, contract="pool", sub=m)
    tt.valid[:, tt.j(0)] = save
    s = r_true["sel"] & r_skip["sel"]
    plain = t.plain[s]
    out["blind_minute"] = {
        "n": int(s.sum()),
        "pool_walk_incl_first_minute": float(r_true["r"][s].mean()),
        "pool_walk_skipping_first_minute_sidecar_convention": float(r_skip["r"][s].mean()),
        "delta_R_of_the_first_60s": float((r_true["r"][s] - r_skip["r"][s]).mean()),
        "rows_whose_verdict_changes": int((np.abs(r_true["r"][s] - r_skip["r"][s]) > 1e-9).sum()),
        "shipped_plain_walk_r_mean_same_rows": float(plain.mean()),
        "recon_vs_shipped_plain_max_abs": float(np.abs(r_skip["r"][s] - plain).max()),
        "recon_vs_shipped_plain_mean_abs": float(np.abs(r_skip["r"][s] - plain).mean()),
    }
    print("\n=== the 60-second blind spot ===")
    for k2, v in out["blind_minute"].items():
        print(f"  {k2:52s} {v}")

    # ---- 5. per-direction split of the market path (is this just the bar's own move?)
    lg = m & t.is_long
    sh = m & ~t.is_long
    dirn = []
    for k in OFFSETS:
        je = t.j(k) - 1
        a = t.px[lg, je, 3] - t.entry[lg]
        b = t.px[sh, je, 3] - t.entry[sh]
        dirn.append({"k": k,
                     "long_mean_price_minus_entry_in_R": float(np.nanmean(a / t.rdist[lg])),
                     "short_mean_price_minus_entry_in_R": float(np.nanmean(b / t.rdist[sh]))})
    out["direction_split"] = dirn

    json.dump(out, open(os.path.join(HERE, "X3_MECHANISM_V1.json"), "w"), indent=1)
    print("\nwrote X3_MECHANISM_V1.json")


if __name__ == "__main__":
    main()
