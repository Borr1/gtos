"""Tape-true spread by BROKER hour and by broker 15-minute slot.

Why not reuse Lane 1's ``TICK_SPREADS_BY_SESSION_V1.csv``: it aggregates to four
UTC sessions, so the rollover minute -- the single artifact this lane has to rule
out -- is averaged into a seven-hour median and disappears.  Lane 7 found the
shipped hour-flat cost model 4.5-6.4x too cheap outside cash sessions; the fix is
a per-broker-slot table, which is what this builds.

Ticks are broker wall clock (every ``.timebase.json`` in the archive says so).
"""
from __future__ import annotations
import glob, json, os, sys
import numpy as np
import pandas as pd

OUT = "/Users/borr/.claude/jobs/adb9e69b/tmp/b4cache"
os.makedirs(OUT, exist_ok=True)
ROOT = "/Users/borr/GTOSActive/vps-ticks-20260726"


def run(book="ftmo"):
    rows_h, rows_s = [], []
    files = sorted(glob.glob(f"{ROOT}/{book}/*_ticks_*.csv.gz"))
    for f in files:
        base = os.path.basename(f)
        sym = base.split("_ticks_")[0]
        sym = sym.replace("FTMO_", "").replace("redacted_account_", "")
        try:
            d = pd.read_csv(f, compression="gzip", usecols=["time", "bid", "ask"])
        except Exception as e:
            print("SKIP", base, e, flush=True)
            continue
        bt = pd.to_datetime(d["time"].values, unit="s")
        bid = d["bid"].values.astype(float); ask = d["ask"].values.astype(float)
        mid = 0.5 * (bid + ask)
        ok = np.isfinite(mid) & (mid > 0) & np.isfinite(ask - bid) & (ask >= bid)
        sp = np.where(ok, (ask - bid) / np.where(mid > 0, mid, np.nan), np.nan)
        hh = bt.hour.values.astype(np.int16)
        slot = (bt.hour.values * 4 + bt.minute.values // 15).astype(np.int16)
        g = pd.DataFrame({"bh": hh, "slot": slot, "sp": sp}).dropna()
        for key, store in (("bh", rows_h), ("slot", rows_s)):
            a = g.groupby(key)["sp"].agg(
                n="size", med="median", mean="mean",
                p25=lambda x: x.quantile(.25), p75=lambda x: x.quantile(.75),
                p95=lambda x: x.quantile(.95)).reset_index()
            a["sym"] = sym; a["book"] = book
            store.append(a)
        print("done", sym, len(g), flush=True)
    pd.concat(rows_h, ignore_index=True).to_parquet(f"{OUT}/tick_sp_bh_{book}.parquet", index=False)
    pd.concat(rows_s, ignore_index=True).to_parquet(f"{OUT}/tick_sp_slot_{book}.parquet", index=False)


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "ftmo")
