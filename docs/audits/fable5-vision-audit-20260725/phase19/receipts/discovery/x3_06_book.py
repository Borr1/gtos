#!/usr/bin/env python3
"""x3_06_book — the early-entry book at BROKER-TRUE cost, both trigger polarities.

x3_05 charged the pool's frozen cost model (mean 0.663 R/trade), which L10X measured at
3.503x the broker-true bill (0.189 R).  At that toll no round-trip strategy of any kind can
exist, so it tests nothing.  This re-runs at the broker-true per-symbol cost
(L10X_POOL_RECOST_V1.json -> per_symbol.real_tot_med, R denominated on the row's risk
distance; the phantom book's risk unit IS that symbol's median candidate risk distance, so
the two are unit-matched).

Arms
  CONT      trigger direction = sign(running displacement)   (continuation)
  FADE      trigger direction = -sign(running displacement)  (mean reversion)
each in
  UNCOND    take the trade, run the full contract
  CONFIRM   flatten at the M15 close unless the generator emits a same-side candidate
and the baseline
  M15CLOSE  the real at-market candidates entered at the close, same risk unit, same toll.
"""
from __future__ import annotations
import csv, json, os, sys, collections
from datetime import datetime, timezone
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import x3_lib as X

M1_ROOT = ("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
           "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars")
DIRS = ["bridge_ftmo_m1_202512", "bridge_ftmo_m1_202601"]
JAN_LO = datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp() // 60
JAN_HI = datetime(2026, 2, 1, tzinfo=timezone.utc).timestamp() // 60
THETAS = [0.25, 0.5, 0.75, 1.0, 1.5]
MINUTES = [3, 5, 7, 9, 11, 13]
HORIZON = 120
RECOST = os.path.join(HERE, "L10X_POOL_RECOST_V1.json")


def load_m1(symbol):
    o = {}
    for d in DIRS:
        p = os.path.join(M1_ROOT, d, f"{symbol}_M1.csv")
        if not os.path.isfile(p):
            continue
        with open(p, newline="") as fh:
            rd = csv.reader(fh); next(rd)
            for row in rd:
                o[int(datetime.fromisoformat(row[0]).timestamp()) // 60] = (
                    float(row[1]), float(row[2]), float(row[3]), float(row[4]))
    return o


def walk(tape, t0, t_end, E, d, sgn, target=2.0, stop=-1.0, flatten_at=None):
    st = stop; lastc = 0.0
    for tt in range(t0, t_end):
        b = tape.get(tt)
        if b is None:
            continue
        if sgn > 0:
            fav = (b[1] - E) / d; adv = (b[2] - E) / d
        else:
            fav = (E - b[2]) / d; adv = (E - b[1]) / d
        cls = (b[3] - E) * sgn / d
        if adv <= st + 1e-12:
            return st, "stop"
        if target is not None and fav >= target - 1e-12:
            return target, "target"
        lastc = cls
        if flatten_at is not None and tt >= flatten_at:
            return cls, "flatten"
    return lastc, "mtm"


def stats(r, cost, day, bpsw, label):
    r = np.asarray(r); cost = np.asarray(cost)
    if r.size == 0:
        return {"label": label, "n": 0}
    net = r - cost
    sd = net.std(ddof=1) if r.size > 1 else float("nan")
    return {"label": label, "n": int(r.size), "gross_R": float(r.mean()),
            "cost_R": float(cost.mean()), "net_R": float(net.mean()),
            "t_net": float(net.mean() / (sd / np.sqrt(r.size))) if sd > 0 else None,
            "total_net_R": float(net.sum()), "total_gross_R": float(r.sum()),
            "win": float((r > 0).mean()),
            "gross_bps": float((r * bpsw).mean()), "cost_bps": float((cost * bpsw).mean()),
            "net_bps": float(((r - cost) * bpsw).mean())}


def main():
    t = X.Tape()
    atm = t.born == "born_at_limit"
    rc = json.load(open(RECOST))["per_symbol"]
    real = {}
    for i in range(t.n):
        if not atm[i]:
            continue
        T = int(datetime.fromisoformat(str(t.dtu[i])).timestamp()) // 60
        real.setdefault((str(t.sym[i]), T), set()).add(1 if t.is_long[i] else -1)
    rd_med, toll, bpsw = {}, {}, {}
    for s in sorted(set(t.sym)):
        m = (t.sym == s) & atm
        rd_med[s] = float(np.median(t.rdist[m]))
        toll[s] = float(rc[s]["real_tot_med"])
        bpsw[s] = float(np.median(t.bps_per_R[m]))
    print("broker-true toll (R at that symbol's median risk distance) and bps/R:")
    for s in sorted(rd_med):
        print(f"  {s:12s} rd={rd_med[s]:12.5f} toll_R={toll[s]:.5f} "
              f"bps_per_R={bpsw[s]:8.3f} toll_bps={toll[s]*bpsw[s]:7.3f}")

    arms = ("CONT", "FADE")
    modes = ("UNCOND", "CONFIRM")
    cells = {(a, mo, th, mj): collections.defaultdict(list)
             for a in arms for mo in modes for th in THETAS for mj in MINUTES}
    base = collections.defaultdict(list)
    scanned = 0
    for s in sorted(set(t.sym)):
        tape = load_m1(s)
        d = rd_med[s]; cst = toll[s]; bw = bpsw[s]
        grid = [m for m in sorted(tape) if m % 15 == 0 and JAN_LO <= m < JAN_HI]
        for t_open in grid:
            T = t_open + 15
            b0 = tape.get(t_open)
            if b0 is None or sum(1 for q in range(t_open, T) if q in tape) < 10:
                continue
            scanned += 1
            day = datetime.fromtimestamp(T * 60, timezone.utc).strftime("%Y-%m-%d")
            op = b0[0]
            cands = real.get((s, T), set())
            bcl = tape.get(T - 1)
            if bcl is not None:
                for sgn in cands:
                    r, why = walk(tape, T, T + HORIZON, bcl[3], d, sgn)
                    base["r"].append(r); base["cost"].append(cst)
                    base["day"].append(day); base["bw"].append(bw)
            for mj in MINUTES:
                lab = t_open + mj - 1
                b = tape.get(lab)
                if b is None:
                    continue
                D = b[3] - op
                if D == 0:
                    continue
                base_sgn = 1 if D > 0 else -1
                for th in THETAS:
                    if abs(D) < th * d:
                        continue
                    E = b[3]
                    for a in arms:
                        sgn = base_sgn if a == "CONT" else -base_sgn
                        conf = sgn in cands
                        ru, _ = walk(tape, lab + 1, T + HORIZON, E, d, sgn)
                        if conf:
                            rc_, wc = ru, "kept"
                        else:
                            rc_, wc = walk(tape, lab + 1, T, E, d, sgn, flatten_at=T - 1)
                        for mo, rr, cc in (("UNCOND", ru, cst),
                                           ("CONFIRM", rc_, cst if conf else 2 * cst)):
                            c = cells[(a, mo, th, mj)]
                            c["r"].append(rr); c["cost"].append(cc)
                            c["conf"].append(conf); c["day"].append(day); c["bw"].append(bw)
        print("scanned", s, len(grid), flush=True)

    out = {"m15_bars_scanned": scanned, "rd_median_by_symbol": rd_med,
           "toll_R_by_symbol": toll, "bps_per_R_by_symbol": bpsw, "cells": {}}
    bw = np.array(base["bw"])
    bstat = stats(base["r"], base["cost"], base["day"], bw, "M15CLOSE_baseline")
    bstat["dayboot_net"] = X.dayboot(np.array(base["day"]),
                                     np.array(base["r"]) - np.array(base["cost"]), reps=2000)
    out["baseline_m15_close"] = bstat
    print("\nBASELINE  n=%d gross=%+.5f R (%+.4f bps) toll=%.5f R (%.4f bps) net=%+.5f R "
          "(%+.4f bps) totalnet=%+.1f R" % (bstat["n"], bstat["gross_R"], bstat["gross_bps"],
                                            bstat["cost_R"], bstat["cost_bps"],
                                            bstat["net_R"], bstat["net_bps"],
                                            bstat["total_net_R"]))

    print("\n=== EARLY BOOKS at broker-true cost ===")
    print(f"{'arm':>5s} {'mode':>8s} {'th':>5s} {'min':>4s} {'n':>6s} {'prec':>6s} "
          f"{'grossR':>9s} {'netR':>9s} {'grossbps':>9s} {'netbps':>8s} {'totnet':>9s} "
          f"{'netR_conf':>10s} {'netR_phan':>10s}")
    for a in arms:
        for mo in modes:
            for th in THETAS:
                for mj in MINUTES:
                    c = cells[(a, mo, th, mj)]
                    if not c["r"]:
                        continue
                    w = np.array(c["bw"])
                    st = stats(c["r"], c["cost"], c["day"], w, f"{a}|{mo}|{th}|{mj}")
                    cf = np.array(c["conf"], bool)
                    r = np.array(c["r"]); co = np.array(c["cost"])
                    st.update({"arm": a, "mode": mo, "theta": th, "minute": mj,
                               "k": -15 + mj, "precision": float(cf.mean()),
                               "net_R_confirmed": float((r - co)[cf].mean()) if cf.sum() else None,
                               "net_R_phantom": float((r - co)[~cf].mean()) if (~cf).sum() else None,
                               "gross_R_confirmed": float(r[cf].mean()) if cf.sum() else None,
                               "gross_R_phantom": float(r[~cf].mean()) if (~cf).sum() else None})
                    out["cells"][st["label"]] = st
                    print(f"{a:>5s} {mo:>8s} {th:5.2f} {mj:4d} {st['n']:6d} "
                          f"{st['precision']:6.4f} {st['gross_R']:+9.5f} {st['net_R']:+9.5f} "
                          f"{st['gross_bps']:+9.4f} {st['net_bps']:+8.4f} "
                          f"{st['total_net_R']:+9.1f} {(st['net_R_confirmed'] or 0):+10.5f} "
                          f"{(st['net_R_phantom'] or 0):+10.5f}")

    best = max(out["cells"], key=lambda k: out["cells"][k]["total_net_R"])
    a, mo, th, mj = best.split("|")
    c = cells[(a, mo, float(th), int(mj))]
    net = np.array(c["r"]) - np.array(c["cost"])
    out["best_cell"] = {"cell": best, **out["cells"][best],
                        "dayboot_net": X.dayboot(np.array(c["day"]), net, reps=2000)}
    b = out["best_cell"]["dayboot_net"]
    print(f"\nBEST by total net R: {best}  net={b['mean']:+.5f} "
          f"CI95[{b['lo95']:+.5f},{b['hi95']:+.5f}] P(<=0)={b['p_le_0']:.3f}")
    bb = bstat["dayboot_net"]
    print(f"baseline               net={bb['mean']:+.5f} "
          f"CI95[{bb['lo95']:+.5f},{bb['hi95']:+.5f}] P(<=0)={bb['p_le_0']:.3f}")
    json.dump(out, open(os.path.join(HERE, "X3_BOOK_V1.json"), "w"), indent=1)
    print("\nwrote X3_BOOK_V1.json")


if __name__ == "__main__":
    main()
