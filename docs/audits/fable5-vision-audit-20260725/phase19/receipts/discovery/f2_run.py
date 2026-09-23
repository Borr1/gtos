"""f2_run — drive the oracle ladder for one month and write the receipt JSON.

    python3 f2_run.py --in /tmp/pbg_full_jan --month 202601 --out F2_LADDER_202601_V1.json

Everything is measured over the whole population.  Two tracks are produced:

  TRACK B (primary, full population, no capacity constraint)
      R1  no gate, shipped exit                     -> the raw signal, no downstream
      R3  + oracle exit (menu, and path ceiling)
      R4  + oracle entry instant
      R5  + oracle direction
  TRACK A (cumulative, capacity-matched to what the shipped gate actually admits)
      R0 -> R1 -> R2 -> R3 -> R4 -> R5

and both tracks are computed for REAL, PLACEBO-SIDE and PLACEBO-TIME arms.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import f2_ladder as F  # noqa: E402
import pbg_econ as E  # noqa: E402
import pbg_lib as L  # noqa: E402

SHIPPED_SPREAD_CAP_R = 0.10   # L8/L11: the shipped spread cap, in R
SHIPPED_COST_CAP_R = 0.15     # L8/L11: the shipped total-cost cap, in R


def month_symbols(rows):
    return sorted({r["s"] for r in rows})


def build_frame(rows, tape, cm, *, horizon, seed=20260806, placebo=None, rng=None):
    """Return a dict of aligned arrays for a population.

    placebo=None          -> the real rows
    placebo='side'        -> identical instants/risk, random side
    placebo='time'        -> same (symbol, day) and risk distance, random instant on the
                             system's own 96-window grid, random side
    """
    n = len(rows)
    long = np.array([r["d"] == "L" for r in rows])
    d = np.array([abs(r["e"] - r["sl"]) for r in rows])
    day = np.array([r["t"][:10] for r in rows])
    fam = np.array([r["f"] for r in rows])
    sym = np.array([r["s"] for r in rows])
    inst = [r["t"] for r in rows]

    if placebo == "side":
        long = rng.random(n) < 0.5
    elif placebo == "time":
        long = rng.random(n) < 0.5
        w = rng.integers(0, 96, size=n)
        inst = [
            (datetime.fromisoformat(day[a] + "T00:00:00+00:00")
             + timedelta(minutes=15 * int(w[a]))).isoformat()
            for a in range(n)
        ]

    prows = [
        {"s": sym[a], "t": inst[a], "f": fam[a], "d": "L" if long[a] else "S"}
        for a in range(n)
    ]
    idx, W_c, W_h, W_l = F.build_paths(tape, prows, extra=F.ENTRY_WINDOW + horizon + 4)
    if placebo == "time":
        # the real emitted entry belongs to a different instant; use the tape's own
        # last print before the drawn instant, which is what a market order would get
        entry = W_c[:, 0].copy()
    else:
        # the generator's OWN emitted entry price.  PB proved it equals the last M1
        # close strictly before the decision instant on 198,539/198,539 at-market
        # emissions at 0.0 relative error, so this is the same number wherever the
        # tape has a print — and it keeps rows the tape happens to be missing.
        entry = np.array([float(r["e"]) for r in rows])
    ok = np.isfinite(entry) & (d > 0)
    # column 0 IS the shipped fill, so make the j=0 entry-oracle candidate exactly the
    # shipped one (proven identical wherever the tape has the print; this only recovers
    # the handful of rows where the tape is missing that single minute)
    W_c[:, 0] = np.where(np.isfinite(entry), entry, W_c[:, 0])

    # broker-true toll, in R, at the shipped fill
    cost_r = np.full(n, np.nan)
    spread_r = np.full(n, np.nan)
    for a in range(n):
        if not ok[a]:
            continue
        tot, terms = cm.cost_px(sym[a], inst[a], float(entry[a]), bool(long[a]))
        cost_r[a] = tot / d[a]
        spread_r[a] = terms["spread"] / d[a]

    return {
        "n": n, "long": long, "d": d, "day": day, "fam": fam, "sym": sym,
        "inst": inst, "idx": idx, "W_c": W_c, "W_h": W_h, "W_l": W_l,
        "entry": entry, "ok": ok, "cost_r": cost_r, "spread_r": spread_r,
    }


def ladder(fr, *, horizon, target_r, capacity_by_day=None, want_entry_oracle=True):
    """Compute every rung on one frame.  Returns dict of arrays + summaries."""
    ok = fr["ok"]
    d = fr["d"]
    entry = fr["entry"]
    long = fr["long"]
    cost_r = fr["cost_r"]
    day = fr["day"]

    rc, rh, rl = F.r_frames(fr["W_c"], fr["W_h"], fr["W_l"], entry, d, long, 0, horizon)

    shipped, code = F.walk_fixed(rc, rh, rl, target_r)
    shipped = np.where(ok, shipped, np.nan)

    menu = F.exit_menu(rc, rh, rl)
    menu_best = np.nanmax(np.vstack([np.where(ok, v, -np.inf) for v in menu.values()]), axis=0)
    menu_best = np.where(ok, menu_best, np.nan)
    menu_which = np.array(list(menu.keys()))[
        np.argmax(np.vstack([np.where(ok, v, -np.inf) for v in menu.values()]), axis=0)
    ]
    path_or = np.where(ok, F.oracle_exit_close(rc), np.nan)
    intrabar_or = np.where(ok, F.oracle_exit_intrabar(rh), np.nan)

    res = {
        "shipped": shipped, "code": code, "menu": menu, "menu_best": menu_best,
        "menu_which": menu_which, "path_oracle": path_or, "intrabar_oracle": intrabar_or,
    }

    if want_entry_oracle:
        # best entry instant among the 15 M1 stamps covering the following M15 bar,
        # risk distance held at the generator's own d (so R units stay comparable)
        best_menu = np.full(fr["n"], -np.inf)
        best_path = np.full(fr["n"], -np.inf)
        best_j = np.zeros(fr["n"], dtype=int)
        best_flip = np.full(fr["n"], -np.inf)
        for j in range(F.ENTRY_WINDOW):
            ej = fr["W_c"][:, j]
            okj = np.isfinite(ej) & ok
            rcj, rhj, rlj = F.r_frames(fr["W_c"], fr["W_h"], fr["W_l"], ej, d, long, j, horizon)
            mj = F.exit_menu(rcj, rhj, rlj)
            mb = np.nanmax(np.vstack([np.where(okj, v, -np.inf) for v in mj.values()]), axis=0)
            pj = np.where(okj, F.oracle_exit_close(rcj), -np.inf)
            # opposite direction on the same entry -- the direction oracle
            rcf, rhf, rlf = F.r_frames(fr["W_c"], fr["W_h"], fr["W_l"], ej, d, ~long, j, horizon)
            pf = np.where(okj, F.oracle_exit_close(rcf), -np.inf)
            upd = mb > best_menu
            best_j = np.where(upd, j, best_j)
            best_menu = np.maximum(best_menu, mb)
            best_path = np.maximum(best_path, pj)
            best_flip = np.maximum(best_flip, np.maximum(pj, pf))
        res["entry_oracle_menu"] = np.where(ok, best_menu, np.nan)
        res["entry_oracle_path"] = np.where(ok, best_path, np.nan)
        res["entry_oracle_j"] = best_j
        res["dir_oracle"] = np.where(ok, best_flip, np.nan)
        # direction oracle at the SHIPPED entry, shipped exit -- the cheap version
        rcf0, rhf0, rlf0 = F.r_frames(fr["W_c"], fr["W_h"], fr["W_l"], entry, d, ~long, 0, horizon)
        flip0, _ = F.walk_fixed(rcf0, rhf0, rlf0, target_r)
        res["dir_oracle_shipped_exit"] = np.where(ok, np.maximum(shipped, flip0), np.nan)
    return res


def topn_by_day(vals, day, cap):
    """Boolean mask keeping the top cap[d] rows of each day by `vals`."""
    keep = np.zeros(len(vals), dtype=bool)
    by = defaultdict(list)
    for a, dd in enumerate(day):
        if np.isfinite(vals[a]):
            by[dd].append(a)
    for dd, aa in by.items():
        k = cap.get(dd, 0)
        if k <= 0:
            continue
        aa = np.asarray(aa)
        order = aa[np.argsort(-vals[aa])]
        keep[order[:k]] = True
    return keep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="indir", required=True)
    ap.add_argument("--month", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--horizon", type=int, default=F.HORIZON)
    ap.add_argument("--target-r", type=float, default=F.SHIPPED_TARGET_R)
    ap.add_argument("--cohort", default="AT_MARKET", choices=["AT_MARKET", "POI"])
    args = ap.parse_args()

    fams = set(F.AT_MARKET if args.cohort == "AT_MARKET" else F.POI)
    rows = F.load_close_rows(args.indir, fams)
    out = {
        "lane": "f2", "month": args.month, "cohort": args.cohort,
        "horizon_m1_bars": args.horizon, "shipped_target_r": args.target_r,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "population_source": args.indir,
        "n_setup_keys": len(rows),
    }
    print("rows", len(rows), flush=True)

    tape = E.Tape(L.SYMBOLS, [args.month])
    cm = E.CostModel()
    rng = np.random.default_rng(20260806)

    arms = {}
    for name, pl in (("REAL", None), ("PLACEBO_SIDE", "side"), ("PLACEBO_TIME", "time")):
        fr = build_frame(rows, tape, cm, horizon=args.horizon, placebo=pl, rng=rng)
        lad = ladder(fr, horizon=args.horizon, target_r=args.target_r)
        arms[name] = (fr, lad)
        print("built", name, "ok=", int(fr["ok"].sum()), flush=True)

    # ---------------------------------------------------------------- rungs
    def rungs(fr, lad):
        ok = fr["ok"]
        day, cost = fr["day"], fr["cost_r"]
        sh = lad["shipped"]
        gate = ok & (fr["spread_r"] <= SHIPPED_SPREAD_CAP_R) & (cost <= SHIPPED_COST_CAP_R)
        cap = defaultdict(int)
        for a in np.nonzero(gate & np.isfinite(sh))[0]:
            cap[day[a]] += 1

        def m(mask, vals, lbl, extra=None):
            v = np.where(mask, vals, np.nan)
            return F.agg(v, cost, day, label=lbl, extra=extra)

        R0 = m(gate, sh, "R0_as_the_system_runs_it")
        R1 = m(ok, sh, "R1_no_gate")
        k2 = topn_by_day(np.where(ok, sh - cost, -np.inf), day, cap)
        R2 = m(k2, sh, "R2_oracle_ordering_at_shipped_capacity")
        me = lad["menu_best"]
        k3 = topn_by_day(np.where(ok, me - cost, -np.inf), day, cap)
        R3 = m(k3, me, "R3_oracle_exit_menu_capacity_matched")
        eo = lad["entry_oracle_menu"]
        k4 = topn_by_day(np.where(ok, eo - cost, -np.inf), day, cap)
        R4 = m(k4, eo, "R4_oracle_entry_capacity_matched")
        do = lad["dir_oracle"]
        k5 = topn_by_day(np.where(ok, do - cost, -np.inf), day, cap)
        R5 = m(k5, do, "R5_oracle_direction_capacity_matched")

        # TRACK B: full population, no capacity
        B = {
            "R1_no_gate": F.agg(np.where(ok, sh, np.nan), cost, day, label="B_R1"),
            "R3_oracle_exit_menu": F.agg(np.where(ok, me, np.nan), cost, day, label="B_R3_menu"),
            "R3b_oracle_exit_path": F.agg(lad["path_oracle"], cost, day, label="B_R3_path"),
            "R3c_oracle_exit_intrabar_UNACHIEVABLE": F.agg(
                lad["intrabar_oracle"], cost, day, label="B_R3_intrabar"),
            "R4_oracle_entry_plus_menu_exit": F.agg(eo, cost, day, label="B_R4_menu"),
            "R4b_oracle_entry_plus_path_exit": F.agg(
                lad["entry_oracle_path"], cost, day, label="B_R4_path"),
            "R5_oracle_direction": F.agg(do, cost, day, label="B_R5"),
            "R5b_direction_only_shipped_exit": F.agg(
                lad["dir_oracle_shipped_exit"], cost, day, label="B_R5_shipped_exit"),
        }
        for k, v in B.items():
            src = {"R1_no_gate": sh, "R3_oracle_exit_menu": me,
                   "R3b_oracle_exit_path": lad["path_oracle"],
                   "R3c_oracle_exit_intrabar_UNACHIEVABLE": lad["intrabar_oracle"],
                   "R4_oracle_entry_plus_menu_exit": eo,
                   "R4b_oracle_entry_plus_path_exit": lad["entry_oracle_path"],
                   "R5_oracle_direction": do,
                   "R5b_direction_only_shipped_exit": lad["dir_oracle_shipped_exit"]}[k]
            v["boot_net"] = F.day_boot(np.where(ok, src, np.nan) - cost, day)

        # each single fixed exit contract, pooled (the realistic non-oracle counterpart)
        fixed = {
            name: F.agg(np.where(ok, v, np.nan), cost, day, label="fixed_" + name)
            for name, v in lad["menu"].items()
        }
        return {
            "TRACK_A_capacity_matched": {
                "R0": R0, "R1": R1, "R2": R2, "R3": R3, "R4": R4, "R5": R5,
                "shipped_gate_admit_share": float(gate.sum() / max(ok.sum(), 1)),
                "capacity_per_day_total": int(sum(cap.values())),
            },
            "TRACK_B_full_population": B,
            "fixed_exit_contracts_pooled": fixed,
            "menu_winner_mix": {
                k: int(v) for k, v in
                sorted(dict(zip(*np.unique(lad["menu_which"][ok], return_counts=True))).items(),
                       key=lambda kv: -kv[1])
            },
            "shipped_exit_mix": {
                str(k): int(v) for k, v in
                sorted(dict(zip(*np.unique(lad["code"][ok], return_counts=True))).items())
            },
            "toll": {
                "cost_r_per_trade": float(np.nanmean(fr["cost_r"][ok])),
                "spread_r_per_trade": float(np.nanmean(fr["spread_r"][ok])),
                "median_cost_r": float(np.nanmedian(fr["cost_r"][ok])),
            },
        }

    for name, (fr, lad) in arms.items():
        out[name] = rungs(fr, lad)

    # ---- COST-CAP SWEEP.  The shipped gate is a cost filter; push it to its limit
    # and ask whether ANY affordability threshold makes the shipped signal pay.  The
    # placebo column is what makes it readable: if the placebo passes the same cap
    # with the same net, the cap is selecting cheap instruments, not good trades.
    frR2, ladR2 = arms["REAL"]
    frP2, ladP2 = arms["PLACEBO_SIDE"]
    okc = frR2["ok"] & frP2["ok"]
    sweep = {}
    for cap in (1e9, 0.50, 0.30, 0.20, 0.15, 0.10, 0.07, 0.05, 0.03, 0.02, 0.01):
        m = okc & (frR2["cost_r"] <= cap)
        a = F.agg(np.where(m, ladR2["shipped"], np.nan), frR2["cost_r"], frR2["day"],
                  label="cap_%.2f" % cap)
        b = F.agg(np.where(m, ladP2["shipped"], np.nan), frP2["cost_r"], frP2["day"],
                  label="cap_%.2f_placebo" % cap)
        if not a.get("n"):
            continue
        a["boot_net"] = F.day_boot(
            np.where(m, ladR2["shipped"], np.nan) - frR2["cost_r"], frR2["day"])
        sweep["cap_%.2f" % cap] = {
            "n": a["n"], "share_of_population": a["n"] / max(int(okc.sum()), 1),
            "gross_r_per_trade": a["gross_r_per_trade"],
            "cost_r_per_trade": a["cost_r_per_trade"],
            "net_r_per_trade": a["net_r_per_trade"],
            "placebo_net_r_per_trade": b["net_r_per_trade"],
            "signal_net": a["net_r_per_trade"] - b["net_r_per_trade"],
            "days_net_positive": a["days_net_positive"], "n_days": a["n_days"],
            "boot_net": a["boot_net"],
        }
    out["COST_CAP_SWEEP"] = sweep

    # ------------------------------------------------- signal = real - placebo
    sig = {}
    for track in ("TRACK_A_capacity_matched", "TRACK_B_full_population"):
        sig[track] = {}
        for rung in out["REAL"][track]:
            r = out["REAL"][track][rung]
            if not isinstance(r, dict) or "net_r_per_trade" not in r:
                continue
            row = {"real_net": r["net_r_per_trade"], "real_gross": r["gross_r_per_trade"]}
            for p in ("PLACEBO_SIDE", "PLACEBO_TIME"):
                q = out[p][track].get(rung)
                if isinstance(q, dict) and "net_r_per_trade" in q:
                    row[p + "_net"] = q["net_r_per_trade"]
                    row[p + "_gross"] = q["gross_r_per_trade"]
                    row["signal_vs_" + p + "_net"] = r["net_r_per_trade"] - q["net_r_per_trade"]
                    row["signal_vs_" + p + "_gross"] = r["gross_r_per_trade"] - q["gross_r_per_trade"]
            sig[track][rung] = row
    out["SIGNAL_MINUS_PLACEBO"] = sig

    # ---- PAIRED signal test.  PLACEBO_SIDE shares every row, instant, risk distance
    # and toll with REAL, so the per-row difference is a paired quantity and a
    # day-block bootstrap of it is the honest significance statement for "does the
    # signal's DIRECTIONAL call carry anything at this rung".
    frR, ladR = arms["REAL"]
    frP, ladP = arms["PLACEBO_SIDE"]
    okp = frR["ok"] & frP["ok"]
    paired = {}
    for lbl, key in (
        ("R1_shipped_exit", "shipped"),
        ("R3_oracle_exit_menu", "menu_best"),
        ("R3b_oracle_exit_path", "path_oracle"),
        ("R4_oracle_entry_plus_menu_exit", "entry_oracle_menu"),
        ("R4b_oracle_entry_plus_path_exit", "entry_oracle_path"),
    ):
        a = np.where(okp, ladR[key], np.nan)
        b = np.where(okp, ladP[key], np.nan)
        diff = a - b            # the toll is identical on both sides, so it cancels
        paired[lbl] = F.day_boot(diff, frR["day"])
        paired[lbl]["n_paired"] = int(np.isfinite(diff).sum())
        paired[lbl]["share_real_beats_placebo"] = float(
            np.nanmean((diff > 0).astype(float)[np.isfinite(diff)]))
    out["PAIRED_SIGNAL_VS_RANDOM_SIDE"] = paired

    # ---- how much of the shipped book's loss is the toll vs the gross
    okR = frR["ok"]
    out["TOLL_DECOMPOSITION"] = {
        "gross_r_per_trade_R1": float(np.nanmean(np.where(okR, ladR["shipped"], np.nan))),
        "toll_r_per_trade": float(np.nanmean(frR["cost_r"][okR])),
        "toll_over_gross_abs": float(
            np.nanmean(frR["cost_r"][okR])
            / max(abs(np.nanmean(np.where(okR, ladR["shipped"], np.nan))), 1e-12)),
        "gross_needed_for_breakeven_R": float(np.nanmean(frR["cost_r"][okR])),
        "R4_path_gross": float(np.nanmean(ladR["entry_oracle_path"])),
        "R4_path_signal_over_placebo_gross": float(
            np.nanmean(np.where(okp, ladR["entry_oracle_path"], np.nan))
            - np.nanmean(np.where(okp, ladP["entry_oracle_path"], np.nan))),
    }
    # everything again in price-bps, so the toll can be read against the broker's
    # own fee schedule rather than against a risk distance that varies by setup
    rr = frR["d"][okR] / frR["entry"][okR] * 1e4      # one R, in bps of price
    def _bps(v):
        return float(np.nanmean(np.where(okR, v, np.nan)[okR] * rr))
    out["TOLL_DECOMPOSITION"].update({
        "one_R_in_price_bps_mean": float(np.nanmean(rr)),
        "toll_bps_mean": float(np.nanmean(frR["cost_r"][okR] * rr)),
        "R1_gross_bps": _bps(ladR["shipped"]),
        "R4_path_gross_bps": _bps(ladR["entry_oracle_path"]),
        "R4_path_signal_bps": float(
            np.nanmean((np.where(okp, ladR["entry_oracle_path"], np.nan)
                        - np.where(okp, ladP["entry_oracle_path"], np.nan))[okR] * rr)),
        "signal_R1_bps": float(
            np.nanmean((np.where(okp, ladR["shipped"], np.nan)
                        - np.where(okp, ladP["shipped"], np.nan))[okR] * rr)),
    })

    # ------------------------------------------------------- per family / symbol
    fr, lad = arms["REAL"]
    frp, ladp = arms["PLACEBO_SIDE"]
    ok = fr["ok"]
    cuts = {}
    for axis, keyarr in (("family", fr["fam"]), ("instrument", fr["sym"])):
        tab = {}
        for val in sorted(set(keyarr[ok])):
            m = ok & (keyarr == val)
            if m.sum() < 30:
                continue
            e = {}
            for lbl, v in (("R1", lad["shipped"]), ("R3_menu", lad["menu_best"]),
                           ("R3_path", lad["path_oracle"]),
                           ("R4_menu", lad["entry_oracle_menu"]),
                           ("R4_path", lad["entry_oracle_path"]),
                           ("R5", lad["dir_oracle"])):
                e[lbl] = F.agg(np.where(m, v, np.nan), fr["cost_r"], fr["day"], label=lbl)
            for lbl, v in (("R1", ladp["shipped"]), ("R3_path", ladp["path_oracle"]),
                           ("R4_path", ladp["entry_oracle_path"])):
                e["PLACEBO_SIDE_" + lbl] = F.agg(
                    np.where(m, v, np.nan), frp["cost_r"], frp["day"], label="pl_" + lbl)
            for lbl in ("R1", "R3_path", "R4_path"):
                if e[lbl].get("n") and e["PLACEBO_SIDE_" + lbl].get("n"):
                    e["signal_" + lbl] = (
                        e[lbl]["net_r_per_trade"] - e["PLACEBO_SIDE_" + lbl]["net_r_per_trade"])
            tab[str(val)] = e
        cuts[axis] = tab
    out["by_axis"] = cuts

    Path(args.out).write_text(json.dumps(out, indent=1, default=str))
    A = out["REAL"]["TRACK_A_capacity_matched"]
    B = out["REAL"]["TRACK_B_full_population"]
    print("\n== TRACK A (capacity-matched) ==")
    for k in ("R0", "R1", "R2", "R3", "R4", "R5"):
        r = A[k]
        print("%-4s n=%-7d gross %+.5f  cost %.5f  net %+.5f  winrate %.4f"
              % (k, r["n"], r["gross_r_per_trade"], r["cost_r_per_trade"],
                 r["net_r_per_trade"], r["win_rate_gross"]))
    print("\n== TRACK B (full population) ==")
    for k, r in B.items():
        print("%-42s n=%-7d gross %+.5f  net %+.5f" % (k, r["n"], r["gross_r_per_trade"],
                                                       r["net_r_per_trade"]))
    print("\n== SIGNAL - PLACEBO (track B, net R/trade) ==")
    for k, v in out["SIGNAL_MINUS_PLACEBO"]["TRACK_B_full_population"].items():
        print("%-42s real %+.5f  plSIDE %+.5f (sig %+.5f)  plTIME %+.5f (sig %+.5f)"
              % (k, v["real_net"], v.get("PLACEBO_SIDE_net", float("nan")),
                 v.get("signal_vs_PLACEBO_SIDE_net", float("nan")),
                 v.get("PLACEBO_TIME_net", float("nan")),
                 v.get("signal_vs_PLACEBO_TIME_net", float("nan"))))


if __name__ == "__main__":
    main()
