#!/usr/bin/env python3
"""x3_04_phantom — THE HONEST BILL FOR EARLINESS.

The offset curve's early half assumes the direction was known at the instant of entry.  It
was not: the generator only decides at the M15 close.  A real early entry needs a trigger
that fires INSIDE the forming bar, and such a trigger fires on bars that never become a
candidate at all.  Those are real trades with real losses.

This scans EVERY M15 bar of January on all 24 symbols, fires a partial-bar displacement
trigger at minute j, walks every firing on the same M1 tape under the same contract, and
splits the book into
   MATCHED   - a real candidate was emitted at that bar's close, same side  (recall)
   PHANTOM   - no such candidate: the setup never formed                    (the charge)

Nothing here looks at anything later than the entry instant except the walk itself.
"""
from __future__ import annotations
import csv, gzip, json, os, sys, collections
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
MINUTES = [3, 5, 7, 9, 11, 13]          # minute of the forming bar at which we may fire
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


def walk_px(tape, t0, E, d, sgn, target=2.0, stop=-1.0, contract="pool", trail=0.25):
    """Walk price bars labelled t0 .. t0+H-1 (skipping absent minutes)."""
    st = stop; peak = -1e18; lastc = None
    for tt in range(t0, t0 + HORIZON):
        b = tape.get(tt)
        if b is None:
            continue
        fav = (b[1] - E) * sgn / d if sgn > 0 else (E - b[2]) / d
        adv = (b[2] - E) * sgn / d if sgn > 0 else (E - b[1]) / d
        cls = (b[3] - E) * sgn / d
        if adv <= st + 1e-12:
            return st, "stop"
        if contract == "pool" and fav >= target - 1e-12:
            return target, "target"
        if fav > peak:
            peak = fav
        if contract == "trail" and peak >= trail:
            st = max(st, peak - trail)
        lastc = cls
    return (lastc if lastc is not None else 0.0), "mtm"


def main():
    t = X.Tape()
    atm = t.born == "born_at_limit"
    # real candidates, keyed (symbol, decision_minute) -> set of sides
    real = collections.defaultdict(set)
    real_any = collections.defaultdict(int)
    for i in range(t.n):
        T = int(datetime.fromisoformat(str(t.dtu[i])).timestamp()) // 60
        if atm[i]:
            real[(str(t.sym[i]), T)].add(1 if t.is_long[i] else -1)
        real_any[(str(t.sym[i]), T)] += 1
    rd_med = {}
    for s in sorted(set(t.sym)):
        m = (t.sym == s) & atm
        rd_med[s] = float(np.median(t.rdist[m])) if m.sum() else None
    print("per-symbol median risk distance (at-market candidates):",
          {k: round(v, 5) for k, v in list(rd_med.items())[:4]}, "...")

    symbols = sorted(set(t.sym))
    books = {(th, mj, c): collections.defaultdict(list)
             for th in THETAS for mj in MINUTES for c in ("pool", "trail")}
    scanned = 0
    for s in symbols:
        tape = load_m1(s)
        d = rd_med[s]
        mins = sorted(tape)
        grid = [m for m in mins if m % 15 == 0 and JAN_LO <= m < JAN_HI]
        for t_open in grid:
            T = t_open + 15                       # decision instant of this M15 bar
            b0 = tape.get(t_open)
            if b0 is None:
                continue
            present = sum(1 for q in range(t_open, T) if q in tape)
            if present < 10:
                continue
            scanned += 1
            op = b0[0]
            for mj in MINUTES:
                lab = t_open + mj - 1             # bar whose close is instant t_open+mj
                b = tape.get(lab)
                if b is None:
                    continue
                D = b[3] - op
                sgn = 1 if D > 0 else -1
                for th in THETAS:
                    if abs(D) < th * d:
                        continue
                    E = b[3]
                    for c in ("pool", "trail"):
                        r, why = walk_px(tape, lab + 1, E, d, sgn, contract=c)
                        matched = sgn in real[(s, T)]
                        anycand = real_any[(s, T)] > 0
                        books[(th, mj, c)]["r"].append(r)
                        books[(th, mj, c)]["matched"].append(matched)
                        books[(th, mj, c)]["anycand"].append(anycand)
                        books[(th, mj, c)]["sym"].append(s)
                        books[(th, mj, c)]["day"].append(
                            datetime.fromtimestamp(T * 60, timezone.utc).strftime("%Y-%m-%d"))
                        books[(th, mj, c)]["why"].append(why)
        print("scanned", s, len(grid))

    out = {"m15_bars_scanned": scanned, "thetas": THETAS, "minutes": MINUTES,
           "rd_median_by_symbol": rd_med, "cells": {}}
    print("\n=== EARLY-DETECTOR BOOK: every M15 bar in January, trigger at minute j ===")
    print(f"{'th':>5s} {'min':>4s} {'ctr':>5s} {'fired':>7s} {'matched':>8s} {'prec':>6s} "
          f"{'meanR_all':>10s} {'meanR_match':>12s} {'meanR_phantom':>14s} {'per_bar_R':>10s}")
    for th in THETAS:
        for mj in MINUTES:
            for c in ("pool", "trail"):
                b = books[(th, mj, c)]
                r = np.array(b["r"]); mt = np.array(b["matched"])
                if r.size == 0:
                    continue
                cell = {
                    "theta": th, "minute": mj, "contract": c, "k": -15 + mj,
                    "fired": int(r.size), "matched": int(mt.sum()),
                    "precision": float(mt.mean()),
                    "fire_rate_per_scanned_bar": float(r.size / scanned),
                    "meanR_all": float(r.mean()),
                    "meanR_matched": float(r[mt].mean()) if mt.sum() else None,
                    "meanR_phantom": float(r[~mt].mean()) if (~mt).sum() else None,
                    "totalR": float(r.sum()),
                    "R_per_scanned_bar": float(r.sum() / scanned),
                    "win_all": float((r > 0).mean()),
                }
                out["cells"][f"{th}|{mj}|{c}"] = cell
                if c == "pool":
                    print(f"{th:5.2f} {mj:4d} {c:>5s} {cell['fired']:7d} {cell['matched']:8d} "
                          f"{cell['precision']:6.4f} {cell['meanR_all']:+10.5f} "
                          f"{(cell['meanR_matched'] or 0):+12.5f} "
                          f"{(cell['meanR_phantom'] or 0):+14.5f} "
                          f"{cell['R_per_scanned_bar']:+10.5f}")

    # recall: what share of the real at-market candidates does the trigger catch?
    rec = {}
    for th in THETAS:
        for mj in MINUTES:
            b = books[(th, mj, "pool")]
            got = set()
            for s, m, day in zip(b["sym"], b["matched"], b["day"]):
                pass
            got_n = int(np.array(b["matched"]).sum())
            rec[f"{th}|{mj}"] = {"matched_firings": got_n,
                                 "real_at_market_candidates": int(atm.sum()),
                                 "recall_upper_bound": got_n / int(atm.sum())}
    out["recall"] = rec
    json.dump(out, open(os.path.join(HERE, "X3_PHANTOM_V1.json"), "w"), indent=1)
    print("\nwrote X3_PHANTOM_V1.json")


if __name__ == "__main__":
    main()
