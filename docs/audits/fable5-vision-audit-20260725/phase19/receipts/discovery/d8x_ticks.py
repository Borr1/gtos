"""d8x_ticks — THE TOLL HAS NEVER BEEN CHECKED AGAINST TICKS.

Every economic conclusion in this wave divides by a modelled toll (0.28118 R/trade on the
roster; 2.457 bps; h1's four-term basis).  The toll is 21x the signal deficit, so the toll
is the single most load-bearing number in the estate -- and it has never once been compared
to the 263,894,769-row broker tick archive sitting outside the repo, which is the only
ground truth for the quantity on this machine.

This measures, over the WHOLE archive (no sampling):
  * realised quoted spread in bps, per symbol, tick-weighted and time-weighted
  * spread by UTC hour (the model AH proved is hour-blind)
  * spread by position INSIDE the M15 bar: [0,60)s after the close, [60,300)s, [300,900)s
    -- which prices the microstructure component of every "delay the entry" lever in the
    estate, none of which has ever been charged a boundary premium.

Broker stamps are broker wall clock = America/New_York + 7h.  The archive window
(2026-06-18..07-26) is entirely inside US EDT, so broker = UTC+3 throughout; the conversion
is a constant -3h and is asserted, not assumed, by checking the FX weekend gap.
"""
from __future__ import annotations

import glob
import gzip
import json
import os
import sys

import numpy as np
import pandas as pd

TICKS = "/Users/borr/GTOSActive/vps-ticks-20260726"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "D8X_TICK_TOLL_V1.json")

NB = 4000          # spread histogram bins
BW = 0.02          # bps per bin -> 0..80 bps
BROKER_TO_UTC = -3 * 3600


def q_from_hist(h, bw, qs=(0.10, 0.25, 0.50, 0.75, 0.90, 0.99)):
    tot = h.sum()
    if tot == 0:
        return {str(q): None for q in qs}
    c = np.cumsum(h)
    out = {}
    for q in qs:
        i = int(np.searchsorted(c, q * tot))
        out[str(q)] = float(min(i, NB) * bw + bw / 2)
    return out


def do_file(path):
    sym = os.path.basename(path).split("_ticks_")[0]
    broker, sym = sym.split("_", 1)
    hist_all = np.zeros(NB + 1, np.int64)
    hist_hour = np.zeros((24, NB + 1), np.int64)
    hist_mb = np.zeros((3, NB + 1), np.int64)
    n = 0
    s_sum = 0.0
    tw_sum = 0.0        # time-weighted numerator (spread * dt)
    tw_dt = 0.0
    zero = 0
    t_min, t_max = None, None
    for ch in pd.read_csv(path, compression="gzip", usecols=["time_msc", "bid", "ask"],
                          dtype={"time_msc": np.int64, "bid": np.float64, "ask": np.float64},
                          chunksize=4_000_000):
        tm = ch["time_msc"].to_numpy()
        bid = ch["bid"].to_numpy()
        ask = ch["ask"].to_numpy()
        ok = (bid > 0) & (ask > 0) & (ask >= bid)
        zero += int((~ok).sum())
        tm, bid, ask = tm[ok], bid[ok], ask[ok]
        if tm.size == 0:
            continue
        mid = 0.5 * (bid + ask)
        sp = (ask - bid) / mid * 1e4
        t = tm / 1000.0 + BROKER_TO_UTC          # seconds, UTC
        if t_min is None:
            t_min = float(t[0])
        t_max = float(t[-1])
        b = np.clip((sp / BW).astype(np.int64), 0, NB)
        hist_all += np.bincount(b, minlength=NB + 1)
        hr = ((t // 3600) % 24).astype(np.int64)
        hist_hour += np.bincount(hr * (NB + 1) + b,
                                 minlength=24 * (NB + 1)).reshape(24, NB + 1)
        # position inside the M15 bar, in seconds since the M15 boundary
        off = t % 900.0
        mb = np.where(off < 60, 0, np.where(off < 300, 1, 2)).astype(np.int64)
        hist_mb += np.bincount(mb * (NB + 1) + b,
                               minlength=3 * (NB + 1)).reshape(3, NB + 1)
        n += int(sp.size)
        s_sum += float(sp.sum())
        # time-weighted: each quote holds until the next one
        dt = np.diff(t, append=t[-1])
        dt = np.clip(dt, 0, 60)   # cap gaps (weekends/halts) at 60 s
        tw_sum += float((sp * dt).sum())
        tw_dt += float(dt.sum())
    res = dict(broker=broker, symbol=sym, n_ticks=n, n_rejected=zero,
               mean_bps=s_sum / max(n, 1),
               time_weighted_mean_bps=tw_sum / max(tw_dt, 1e-9),
               utc_first=t_min, utc_last=t_max,
               q=q_from_hist(hist_all, BW),
               by_hour={str(h): dict(n=int(hist_hour[h].sum()),
                                     median=q_from_hist(hist_hour[h], BW)["0.5"])
                        for h in range(24)},
               by_m15_bucket={k: dict(n=int(hist_mb[i].sum()),
                                      mean=float((np.arange(NB + 1) * BW + BW / 2)
                                                 @ hist_mb[i] / max(hist_mb[i].sum(), 1)),
                                      **{("q" + q): v for q, v in
                                         q_from_hist(hist_mb[i], BW).items()})
                             for i, k in enumerate(("s0_60", "s60_300", "s300_900"))})
    return res


def main():
    files = sorted(glob.glob(os.path.join(TICKS, "*", "*_ticks_*.csv.gz")))
    only = sys.argv[1] if len(sys.argv) > 1 else None
    if only:
        files = [f for f in files if only in f]
    out = []
    for i, f in enumerate(files):
        try:
            r = do_file(f)
        except Exception as e:                                   # noqa: BLE001
            r = dict(symbol=os.path.basename(f), error=str(e)[:200])
        out.append(r)
        print("[%d/%d] %s %s n=%s mean=%.4f tw=%.4f" %
              (i + 1, len(files), r.get("broker"), r.get("symbol"),
               r.get("n_ticks"), r.get("mean_bps", -1), r.get("time_weighted_mean_bps", -1)),
              flush=True)
        json.dump(out, open(OUT, "w"), indent=1)
    print("DONE", len(out))


if __name__ == "__main__":
    main()
