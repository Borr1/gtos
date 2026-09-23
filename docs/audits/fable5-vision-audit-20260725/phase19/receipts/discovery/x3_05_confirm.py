#!/usr/bin/env python3
"""x3_05_confirm — the IMPLEMENTABLE early-entry contract, fully charged.

The book already re-evaluates at every M15 close.  So an early entry does not have to be
an unconditional trade:

    minute j of the forming bar : partial-bar displacement trigger fires -> enter at market
    the M15 close               : the generator runs.  If it emits a candidate on the same
                                  symbol and the same side -> KEEP the position and run the
                                  normal contract.  If it does not -> FLATTEN at the close.

Phantoms are therefore charged their realised excursion over the j..15-minute window plus a
second round of cost, not a full trade.  Everything is priced in one risk unit per symbol
(the median risk distance of that symbol's at-market candidates) so the book is a real book.

Baseline arm: the same real candidates entered at the M15 close, same risk unit, same cost.
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
THETAS = [0.25, 0.4, 0.5, 0.75, 1.0]
MINUTES = [3, 5, 7, 9, 11, 13]
HORIZON = 120


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


def walk(tape, t0, t_end, E, d, sgn, target=2.0, stop=-1.0, contract="pool", trail=0.25,
         flatten_at=None):
    """Walk labels t0 .. t_end-1.  If flatten_at is not None and no barrier fired before
    that label, exit at that bar's close (mark to market)."""
    st = stop; peak = -1e18; lastc = 0.0
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
            return st, "stop", tt
        if contract == "pool" and target is not None and fav >= target - 1e-12:
            return target, "target", tt
        if fav > peak:
            peak = fav
        if contract == "trail" and peak >= trail:
            st = max(st, peak - trail)
        lastc = cls
        if flatten_at is not None and tt >= flatten_at:
            return cls, "flatten", tt
    return lastc, "mtm", t_end


def main():
    t = X.Tape()
    atm = t.born == "born_at_limit"
    real = {}
    for i in range(t.n):
        if not atm[i]:
            continue
        T = int(datetime.fromisoformat(str(t.dtu[i])).timestamp()) // 60
        real.setdefault((str(t.sym[i]), T), []).append(
            (1 if t.is_long[i] else -1, float(t.tgt[i])))
    rd_med, cost_med = {}, {}
    for s in sorted(set(t.sym)):
        m = (t.sym == s) & atm
        rd_med[s] = float(np.median(t.rdist[m]))
        cost_med[s] = float(np.median(t.cost_r[m]))

    symbols = sorted(set(t.sym))
    cells = {(th, mj): collections.defaultdict(list) for th in THETAS for mj in MINUTES}
    base = collections.defaultdict(list)
    scanned = 0
    for s in symbols:
        tape = load_m1(s)
        d = rd_med[s]; cst = cost_med[s]
        grid = [m for m in sorted(tape) if m % 15 == 0 and JAN_LO <= m < JAN_HI]
        for t_open in grid:
            T = t_open + 15
            b0 = tape.get(t_open)
            if b0 is None or sum(1 for q in range(t_open, T) if q in tape) < 10:
                continue
            scanned += 1
            day = datetime.fromtimestamp(T * 60, timezone.utc).strftime("%Y-%m-%d")
            op = b0[0]
            cands = real.get((s, T), [])
            # ---- baseline arm: every real at-market candidate entered at the M15 close
            bcl = tape.get(T - 1)
            if bcl is not None:
                for sgn, tgt in cands:
                    r, why, _ = walk(tape, T, T + HORIZON, bcl[3], d, sgn, target=2.0)
                    base["r"].append(r); base["day"].append(day)
                    base["cost"].append(cst); base["sym"].append(s)
            # ---- early arms
            for mj in MINUTES:
                lab = t_open + mj - 1
                b = tape.get(lab)
                if b is None:
                    continue
                D = b[3] - op
                sgn = 1 if D > 0 else -1
                confirmed = any(sd == sgn for sd, _ in cands)
                for th in THETAS:
                    if abs(D) < th * d:
                        continue
                    E = b[3]
                    if confirmed:
                        r, why, _ = walk(tape, lab + 1, T + HORIZON, E, d, sgn, target=2.0)
                        cost = cst
                    else:
                        r, why, _ = walk(tape, lab + 1, T, E, d, sgn, target=2.0,
                                         flatten_at=T - 1)
                        cost = 2.0 * cst
                    c = cells[(th, mj)]
                    c["r"].append(r); c["cost"].append(cost); c["conf"].append(confirmed)
                    c["day"].append(day); c["sym"].append(s); c["why"].append(why)
        print("scanned", s, len(grid), flush=True)

    out = {"m15_bars_scanned": scanned, "rd_median_by_symbol": rd_med,
           "cost_median_by_symbol": cost_med, "cells": {}}
    br = np.array(base["r"]); bc = np.array(base["cost"])
    out["baseline_m15_close"] = {
        "n": int(br.size), "gross_R": float(br.mean()), "cost_R": float(bc.mean()),
        "net_R": float((br - bc).mean()), "total_gross_R": float(br.sum()),
        "total_net_R": float((br - bc).sum()),
        "win": float((br > 0).mean()),
    }
    print("\nBASELINE (real at-market candidates, entered at the M15 close, one risk unit/symbol)")
    print("  n=%d gross=%+.5f cost=%.5f net=%+.5f totalnet=%+.1f R"
          % (br.size, br.mean(), bc.mean(), (br - bc).mean(), (br - bc).sum()))

    print("\n=== CONFIRM-OR-FLATTEN EARLY BOOK ===")
    print(f"{'th':>5s} {'min':>4s} {'trades':>7s} {'conf':>6s} {'prec':>6s} {'grossR':>9s} "
          f"{'costR':>7s} {'netR':>9s} {'net_conf':>9s} {'net_phan':>9s} {'totnet':>9s} "
          f"{'vs_base':>9s}")
    for th in THETAS:
        for mj in MINUTES:
            c = cells[(th, mj)]
            r = np.array(c["r"]); co = np.array(c["cost"]); cf = np.array(c["conf"], bool)
            if r.size == 0:
                continue
            net = r - co
            cell = {"theta": th, "minute": mj, "k": -15 + mj, "trades": int(r.size),
                    "confirmed": int(cf.sum()), "precision": float(cf.mean()),
                    "gross_R": float(r.mean()), "cost_R": float(co.mean()),
                    "net_R": float(net.mean()),
                    "net_R_confirmed": float(net[cf].mean()) if cf.sum() else None,
                    "net_R_phantom": float(net[~cf].mean()) if (~cf).sum() else None,
                    "gross_R_confirmed": float(r[cf].mean()) if cf.sum() else None,
                    "gross_R_phantom": float(r[~cf].mean()) if (~cf).sum() else None,
                    "total_net_R": float(net.sum()),
                    "total_net_R_vs_baseline": float(net.sum() - (br - bc).sum()),
                    "win": float((r > 0).mean()),
                    "phantom_flatten_share": float(np.mean(np.array(c["why"])[~cf] == "flatten"))
                    if (~cf).sum() else None}
            out["cells"][f"{th}|{mj}"] = cell
            print(f"{th:5.2f} {mj:4d} {cell['trades']:7d} {cell['confirmed']:6d} "
                  f"{cell['precision']:6.4f} {cell['gross_R']:+9.5f} {cell['cost_R']:7.5f} "
                  f"{cell['net_R']:+9.5f} {(cell['net_R_confirmed'] or 0):+9.5f} "
                  f"{(cell['net_R_phantom'] or 0):+9.5f} {cell['total_net_R']:+9.1f} "
                  f"{cell['total_net_R_vs_baseline']:+9.1f}")

    # day-block bootstrap on the best cell by total net R
    bestk = max(out["cells"], key=lambda k: out["cells"][k]["total_net_R"])
    th, mj = bestk.split("|"); th = float(th); mj = int(mj)
    c = cells[(th, mj)]
    net = np.array(c["r"]) - np.array(c["cost"])
    b = X.dayboot(np.array(c["day"]), net, reps=2000)
    out["best_cell"] = {"cell": bestk, **out["cells"][bestk], "dayboot_net_R": b}
    bb = X.dayboot(np.array(base["day"]), br - bc, reps=2000)
    out["baseline_m15_close"]["dayboot_net_R"] = bb
    print(f"\nbest cell {bestk}: net {b['mean']:+.5f} CI95[{b['lo95']:+.5f},{b['hi95']:+.5f}] "
          f"P(<=0)={b['p_le_0']:.3f} over {b['n_days']} days")
    print(f"baseline    : net {bb['mean']:+.5f} CI95[{bb['lo95']:+.5f},{bb['hi95']:+.5f}] "
          f"P(<=0)={bb['p_le_0']:.3f}")
    json.dump(out, open(os.path.join(HERE, "X3_CONFIRM_V1.json"), "w"), indent=1)
    print("\nwrote X3_CONFIRM_V1.json")


if __name__ == "__main__":
    main()
