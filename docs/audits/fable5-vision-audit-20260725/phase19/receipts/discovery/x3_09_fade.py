#!/usr/bin/env python3
"""x3_09_fade — stress the one early cell whose PHANTOM leg is profitable.

x3_08 found FADE / theta=1.5 / minute 3 has a negative break-even precision: fading a
>=1.5-risk-distance displacement that has completed within the first 3 minutes of an M15
bar pays whether or not the generator later emits a candidate.  n=388 out of a 60-cell
search, so this is stressed here: per-symbol, per-day, day-block bootstrap, a sign-flip
placebo, and a theta/minute neighbourhood so the reader can see whether it is a ridge or a
spike.
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
THETAS = [1.0, 1.25, 1.5, 1.75, 2.0]
MINUTES = [2, 3, 4, 5, 6]
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


def walk(tape, t0, t_end, E, d, sgn, target=2.0, stop=-1.0):
    for tt in range(t0, t_end):
        b = tape.get(tt)
        if b is None:
            continue
        if sgn > 0:
            fav = (b[1] - E) / d; adv = (b[2] - E) / d
        else:
            fav = (E - b[2]) / d; adv = (E - b[1]) / d
        if adv <= stop + 1e-12:
            return stop
        if fav >= target - 1e-12:
            return target
        last = (b[3] - E) * sgn / d
    return last


def main():
    t = X.Tape()
    atm = t.born == "born_at_limit"
    rc = json.load(open(os.path.join(HERE, "L10X_POOL_RECOST_V1.json")))["per_symbol"]
    real = {}
    for i in range(t.n):
        if not atm[i]:
            continue
        T = int(datetime.fromisoformat(str(t.dtu[i])).timestamp()) // 60
        real.setdefault((str(t.sym[i]), T), set()).add(1 if t.is_long[i] else -1)
    rd_med, toll = {}, {}
    for s in sorted(set(t.sym)):
        m = (t.sym == s) & atm
        rd_med[s] = float(np.median(t.rdist[m])); toll[s] = float(rc[s]["real_tot_med"])

    rows = []
    for s in sorted(set(t.sym)):
        tape = load_m1(s)
        d = rd_med[s]
        grid = [m for m in sorted(tape) if m % 15 == 0 and JAN_LO <= m < JAN_HI]
        for t_open in grid:
            T = t_open + 15
            b0 = tape.get(t_open)
            if b0 is None or sum(1 for q in range(t_open, T) if q in tape) < 10:
                continue
            op = b0[0]
            cands = real.get((s, T), set())
            for mj in MINUTES:
                lab = t_open + mj - 1
                b = tape.get(lab)
                if b is None:
                    continue
                D = b[3] - op
                if D == 0:
                    continue
                bs = 1 if D > 0 else -1
                for th in THETAS:
                    if abs(D) < th * d:
                        continue
                    for pol, sgn in (("CONT", bs), ("FADE", -bs)):
                        r = walk(tape, lab + 1, T + HORIZON, b[3], d, sgn)
                        rows.append({"sym": s, "day": datetime.fromtimestamp(
                            T * 60, timezone.utc).strftime("%Y-%m-%d"),
                            "hour": int(datetime.fromtimestamp(T * 60, timezone.utc).hour),
                            "theta": th, "minute": mj, "pol": pol, "r": r,
                            "cost": toll[s], "conf": sgn in cands,
                            "absD_over_rd": abs(D) / d})
        print("scan", s, flush=True)

    out = {"n_rows": len(rows), "grid_thetas": THETAS, "grid_minutes": MINUTES}
    print("\n=== neighbourhood: net R/trade at broker-true cost (FADE polarity) ===")
    print(f"{'theta':>6s}" + "".join(f"{'m'+str(m):>12s}" for m in MINUTES))
    grid = {}
    for pol in ("FADE", "CONT"):
        for th in THETAS:
            line = f"{th:6.2f}"
            for mj in MINUTES:
                sel = [x for x in rows if x["pol"] == pol and x["theta"] == th
                       and x["minute"] == mj]
                if not sel:
                    grid[f"{pol}|{th}|{mj}"] = None
                    line += f"{'-':>12s}"
                    continue
                r = np.array([x["r"] for x in sel]); c = np.array([x["cost"] for x in sel])
                cf = np.array([x["conf"] for x in sel])
                net = r - c
                g = {"n": len(sel), "net_R": float(net.mean()),
                     "gross_R": float(r.mean()), "precision": float(cf.mean()),
                     "net_R_conf": float(net[cf].mean()) if cf.sum() else None,
                     "net_R_phan": float(net[~cf].mean()) if (~cf).sum() else None,
                     "total_net_R": float(net.sum()),
                     "n_days": len(set(x["day"] for x in sel)),
                     "n_symbols": len(set(x["sym"] for x in sel))}
                grid[f"{pol}|{th}|{mj}"] = g
                line += f"{g['net_R']:+8.4f}({g['n']:4d})".rjust(12)
            if pol == "FADE":
                print(line)
    out["grid"] = grid
    print("\n=== same grid, CONT polarity ===")
    print(f"{'theta':>6s}" + "".join(f"{'m'+str(m):>12s}" for m in MINUTES))
    for th in THETAS:
        line = f"{th:6.2f}"
        for mj in MINUTES:
            g = grid[f"CONT|{th}|{mj}"]
            line += (f"{g['net_R']:+8.4f}({g['n']:4d})".rjust(12) if g else f"{'-':>12s}")
        print(line)

    # focus cell
    for pol, th, mj in (("FADE", 1.5, 3), ("FADE", 1.5, 4), ("FADE", 1.75, 3), ("FADE", 2.0, 3)):
        sel = [x for x in rows if x["pol"] == pol and x["theta"] == th and x["minute"] == mj]
        if not sel:
            continue
        r = np.array([x["r"] for x in sel]); c = np.array([x["cost"] for x in sel])
        day = np.array([x["day"] for x in sel]); sy = np.array([x["sym"] for x in sel])
        net = r - c
        bt = X.dayboot(day, net, reps=5000)
        bysym = collections.Counter(sy)
        top = bysym.most_common(6)
        cont = [x for x in rows if x["pol"] == "CONT" and x["theta"] == th and x["minute"] == mj]
        rc_ = np.array([x["r"] for x in cont]) - np.array([x["cost"] for x in cont])
        d = {"cell": f"{pol}|{th}|{mj}", "n": len(sel), "net_R": float(net.mean()),
             "dayboot": bt, "n_days": len(set(day)), "n_symbols": len(set(sy)),
             "top_symbols": top,
             "mirror_CONT_net_R": float(rc_.mean()),
             "share_of_total_net_from_top_symbol": float(
                 net[sy == top[0][0]].sum() / net.sum()) if net.sum() != 0 else None,
             "days_positive": int(sum(1 for dd in set(day) if net[day == dd].sum() > 0)),
             "win": float((r > 0).mean())}
        out[f"focus_{pol}_{th}_{mj}"] = d
        print(f"\n--- {pol} theta={th} minute={mj}: n={d['n']} net={d['net_R']:+.5f} "
              f"CI95[{bt['lo95']:+.5f},{bt['hi95']:+.5f}] P(<=0)={bt['p_le_0']:.3f} "
              f"days={d['n_days']} days+={d['days_positive']} symbols={d['n_symbols']}")
        print("    top symbols:", top)

    json.dump(out, open(os.path.join(HERE, "X3_FADE_V1.json"), "w"), indent=1)
    print("\nwrote X3_FADE_V1.json")


if __name__ == "__main__":
    main()
