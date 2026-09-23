#!/usr/bin/env python3
"""B1 — per-leg tick slippage, measured identically for the LIMIT and MARKET arms.

This is a port of `swarm2/recon_slippage_receipts/recon_slip.py` with the tick-walking logic
UNCHANGED, so the two arms are comparable by construction. Three things are parameterised:

  --src   which price-bearing export to read (the original MARKET lg_*, or B1's own exports)
  --tag   output name
  --months

Control B (`--src lg`) must reproduce the adjudication's MARKET numbers exactly:
  entry leg  +0.00663 on n = 18,978 ; stop leg +0.03932 on n = 9,543 ; target -0.03968 on n = 3,435.

Sign convention (identical to recon): +ve = the engine's booked price is BETTER than achievable
= engine optimism = a real cost.

Read-only. Writes only to the scratch dir and the receipts dir.
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import pickle

import numpy as np
import pandas as pd

TICK = "/Users/borr/GTOSActive/vps-ticks-20260726/ftmo"
MAP = {"NAS100": "US100_cash", "SPX500": "US500_cash", "GER40": "GER40_cash",
       "JP225": "JP225_cash", "UK100": "UK100_cash"}
OUT = "/Users/borr/.claude/jobs/adb9e69b/tmp/b1"
SRC = {
    "lg": "/private/tmp/laneG-walk/lg_{m}.pkl.gz",              # Lane G's original MARKET export
    "market": OUT + "/b1_market_{m}.pkl.gz",                     # B1's MARKET re-walk (control A)
    "limit": OUT + "/b1_limit_{m}.pkl.gz",                       # B1's LIMIT export (the new thing)
}
WIN0, WIN1 = pd.Timestamp("2026-06-18", tz="UTC"), pd.Timestamp("2026-07-24", tz="UTC")


def to_utc(sec):
    """Broker wall clock -> UTC via new_york_plus_7 (src/utils/broker_clock.py:273)."""
    bn = pd.to_datetime(sec, unit="s")
    return (bn - pd.Timedelta(hours=7)).dt.tz_localize(
        "America/New_York", ambiguous=False, nonexistent="shift_forward").dt.tz_convert("UTC")


def load_population(src: str, months: list[str]) -> pd.DataFrame:
    rows = []
    for mth in months:
        path = SRC[src].format(m=mth)
        if not os.path.exists(path):
            print(f"  MISSING {path}", flush=True)
            continue
        for r in pickle.load(gzip.open(path, "rb")):
            o = r.get("orig") or {}
            if not o.get("fill_time") or o.get("gross") is None:
                continue
            rows.append(dict(month=mth, symbol=r["symbol"], side=r["side"], family=r["family"],
                             day=r["day"], key=r["key"], order_type=r["order_type"],
                             entry=r["entry_price"], stop=r["stop_price"], target=r["target_price"],
                             risk=r["risk_price"], state=o.get("state"), status=o["status"],
                             gross=o["gross"], fill_price=o["fill_price"],
                             fill_time=o["fill_time"], term_time=o.get("terminal_time"),
                             spread_r_row=r.get("spread_r_row"),
                             model_spread=r.get("spread_at_fill_price")))
    c = pd.DataFrame(rows)
    print(f"resolved rows ({src}, {','.join(months)}):", len(c), flush=True)
    if len(c):
        print("  order_type:", c.order_type.value_counts().to_dict(), flush=True)
        print("  state     :", c.state.value_counts().to_dict(), flush=True)
    return c


def measure(c: pd.DataFrame, entry_offset_s: int = 0) -> pd.DataFrame:
    """entry_offset_s shifts the START of the exit scan. Default 0 = the adjudication's convention.

    Sensitivity use: the engine's LIMIT modelled_fill_time_utc is bar-shifted relative to the true
    intrabar touch (b1_feasibility_controls.py C1: feasibility 82.2 % on [0,120s) vs 97.3 % on
    [-60s,120s)), so the scan can start up to one M1 bar late on the LIMIT arm. Re-running with
    -60 tests whether that moves the stop-leg conditional the headline depends on.
    """
    c = c.copy()
    c["ft"] = pd.to_datetime(c.fill_time, utc=True)
    c["tt"] = pd.to_datetime(c.term_time, utc=True)
    c["d"] = np.where(c.side == "LONG", 1.0, -1.0)
    # engine's BOOKED exit price, recovered from the identity gross = d*(exit-fill)/risk
    c["booked_exit"] = c.fill_price + c.d * c.gross * c.risk

    cw = c[(c.ft >= WIN0) & (c.tt <= WIN1)].copy()
    print(f"in tick window {WIN0.date()}..{WIN1.date()}: {len(cw)} of {len(c)} "
          f"({100 * len(cw) / max(1, len(c)):.1f}%)", flush=True)
    print("  window state:", cw.state.value_counts().to_dict(), flush=True)

    res = []
    for sym, g in cw.groupby("symbol"):
        bs = MAP.get(sym, sym)
        f = f"{TICK}/FTMO_{bs}_ticks_20260618_to_20260726.csv.gz"
        if not os.path.exists(f):
            print("  SKIP (no tick file)", sym, len(g), flush=True)
            continue
        t = pd.read_csv(f, usecols=["time_msc", "bid", "ask"])
        t["tu"] = to_utc(t.time_msc / 1000.0)
        t = t.sort_values("tu")
        t = t[(t.ask >= t.bid) & (t.bid > 0)]
        tv = t.tu.values.astype("datetime64[ns]")
        bid = t.bid.values.astype("float64")
        ask = t.ask.values.astype("float64")
        n_t = len(tv)

        out = []
        for r in g.itertuples():
            ftn = np.datetime64(r.ft.tz_localize(None))
            ttn = np.datetime64(r.tt.tz_localize(None))
            a = int(np.searchsorted(tv, ftn + np.timedelta64(entry_offset_s, "s")))
            z = int(np.searchsorted(tv, ttn, side="right"))
            z = min(z + 2, n_t)                    # +2 ticks past terminal for the next-tick fill
            if a >= n_t:
                continue
            d = r.d
            rec = dict(key=r.key, month=r.month, symbol=sym, family=r.family, side=r.side,
                       order_type=r.order_type, state=r.state, day=r.day, risk=r.risk,
                       hour=int(r.ft.hour), n_ticks=int(max(0, z - a)), gross=r.gross)

            # --- ENTRY leg: true entry-side quote at the booked fill instant
            ei = min(a, n_t - 1)
            true_entry = ask[ei] if d > 0 else bid[ei]
            rec["entry_opt_r"] = float(d * (true_entry - r.fill_price) / r.risk)
            rec["true_spread_r"] = float((ask[ei] - bid[ei]) / r.risk)
            rec["model_spread_r"] = (float(r.model_spread / r.risk)
                                     if r.model_spread == r.model_spread and r.model_spread is not None
                                     else np.nan)
            rec["spread_r_row"] = float(r.spread_r_row) if r.spread_r_row == r.spread_r_row else np.nan

            # --- EXIT leg
            if z > a and r.state in ("STOP", "TARGET"):
                lvl = r.stop if r.state == "STOP" else r.target
                ex = bid[a:z] if d > 0 else ask[a:z]
                cross = (ex <= lvl) if ((d > 0) == (r.state == "STOP")) else (ex >= lvl)
                if cross.any():
                    j = int(np.argmax(cross))
                    rec["exit_opt_at_cross_r"] = float(d * (lvl - ex[j]) / r.risk)
                    jn = min(j + 1, len(ex) - 1)
                    rec["exit_opt_next_tick_r"] = float(d * (lvl - ex[jn]) / r.risk)
                    rec["found_cross"] = 1
                else:
                    rec["found_cross"] = 0
            elif z > a and r.state == "TIME_STOP":
                ti = min(int(np.searchsorted(tv, ttn)), n_t - 1)
                true_exit = bid[ti] if d > 0 else ask[ti]
                rec["exit_opt_at_cross_r"] = float(d * (r.booked_exit - true_exit) / r.risk)
                rec["exit_opt_next_tick_r"] = rec["exit_opt_at_cross_r"]
                rec["found_cross"] = 1
            out.append(rec)
        res.append(pd.DataFrame(out))
        print(f"  ok {sym:12s} n={len(out):6d}  ticks={n_t:>10,d}", flush=True)
    return pd.concat(res, ignore_index=True) if res else pd.DataFrame()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", choices=list(SRC), required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--months", default="feb,apr,may,jun,jul")
    ap.add_argument("--entry-offset-s", type=int, default=0)
    args = ap.parse_args()
    months = args.months.split(",")
    c = load_population(args.src, months)
    D = measure(c, entry_offset_s=args.entry_offset_s)
    path = f"{OUT}/legs_{args.tag}.pkl"
    D.to_pickle(path)
    print("\nMEASURED ROWS:", len(D), "->", path, flush=True)
    if len(D):
        print(D.state.value_counts().to_dict(), flush=True)
        # immediate headline so a dropped session still leaves the number on disk
        head = {}
        for st in ["STOP", "TARGET", "TIME_STOP"]:
            s = D[(D.state == st) & (D.get("found_cross") == 1)]
            head[st] = dict(n=int(len(s)),
                            mean=float(s.exit_opt_at_cross_r.mean()) if len(s) else None)
        head["ENTRY"] = dict(n=int(D.entry_opt_r.notna().sum()),
                             mean=float(D.entry_opt_r.mean()))
        head["n_rows"] = int(len(D))
        json.dump(head, open(f"{OUT}/head_{args.tag}.json", "w"), indent=1)
        print(json.dumps(head, indent=1), flush=True)


if __name__ == "__main__":
    main()
