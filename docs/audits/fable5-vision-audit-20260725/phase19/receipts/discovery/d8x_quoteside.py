"""d8x_quoteside — SETTLE THE QUOTE SIDE OF THE BAR ARCHIVE.

h3 names this as its #1 open question: "The quote side of the M1 archive. Settling bid vs
mid changes the passive-entry arithmetic by ..." and every path walk in this estate resolves
stops and targets on the archive's HIGH and LOW.  If the bars are BID, then for a SHORT the
stop is a BUY that executes at the ASK, and walking it on a bid high under-triggers the stop
by exactly one spread -- a directional defect in every walk this estate has ever run.

Nobody has measured it, because until now the two artifacts were never put side by side:
  * vps-bars-20260727  : M15 OHLC + the MT5 `spread` column, broker wall clock, to 2026-07-24
  * vps-ticks-20260726 : raw bid/ask ticks, same broker, same wall clock, 2026-06-18..07-26

They overlap by 37 days.  Both are in RAW broker stamps, so no clock conversion is needed
and no clock risk is taken.

For each M15 bar in the overlap this compares
  close  vs the last tick's bid / mid / ask before the bar's end
  high   vs the max tick bid and the max tick ask in the bar
  low    vs the min tick bid and the min tick ask in the bar
  the bar `spread` column vs the tick spread distribution inside that same bar
and reports which hypothesis the archive satisfies, per symbol, over every bar.
"""
from __future__ import annotations

import glob
import gzip
import json
import os

import numpy as np
import pandas as pd

BARS = "/Users/borr/GTOSActive/vps-bars-20260727"
TICKS = "/Users/borr/GTOSActive/vps-ticks-20260726/ftmo"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "D8X_QUOTESIDE_V1.json")
TF = 900


def do(sym):
    bp = os.path.join(BARS, "FTMO_%s_M15.csv.gz" % sym)
    tp = glob.glob(os.path.join(TICKS, "FTMO_%s_ticks_*.csv.gz" % sym))
    if not os.path.isfile(bp) or not tp:
        return None
    b = pd.read_csv(bp, compression="gzip")
    bt = b["time"].to_numpy(np.int64)
    lo_t, hi_t = None, None
    # tick range first
    with gzip.open(tp[0], "rt") as fh:
        fh.readline()
        first = fh.readline().split(",")
        lo_t = int(first[0])
    m = (bt >= lo_t)
    b = b[m]
    bt = bt[m]
    if bt.size == 0:
        return None
    base = int(bt.min() // TF)
    nb = int(bt.max() // TF) - base + 1
    last_t = np.full(nb, -1, np.int64)
    last_bid = np.full(nb, np.nan)
    last_ask = np.full(nb, np.nan)
    max_bid = np.full(nb, -np.inf)
    min_bid = np.full(nb, np.inf)
    max_ask = np.full(nb, -np.inf)
    min_ask = np.full(nb, np.inf)
    sp_min = np.full(nb, np.inf)
    sp_sum = np.zeros(nb)
    sp_n = np.zeros(nb, np.int64)
    for ch in pd.read_csv(tp[0], compression="gzip",
                          usecols=["time_msc", "bid", "ask"],
                          dtype={"time_msc": np.int64, "bid": np.float64,
                                 "ask": np.float64}, chunksize=4_000_000):
        tm = ch["time_msc"].to_numpy()
        bid = ch["bid"].to_numpy()
        ask = ch["ask"].to_numpy()
        ok = (bid > 0) & (ask >= bid)
        tm, bid, ask = tm[ok], bid[ok], ask[ok]
        k = (tm // (TF * 1000)).astype(np.int64) - base
        ok = (k >= 0) & (k < nb)
        tm, bid, ask, k = tm[ok], bid[ok], ask[ok], k[ok]
        if k.size == 0:
            continue
        np.maximum.at(max_bid, k, bid)
        np.minimum.at(min_bid, k, bid)
        np.maximum.at(max_ask, k, ask)
        np.minimum.at(min_ask, k, ask)
        sp = ask - bid
        np.minimum.at(sp_min, k, sp)
        np.add.at(sp_sum, k, sp)
        np.add.at(sp_n, k, 1)
        np.maximum.at(last_t, k, tm)
    # second pass: pick the bid/ask of the last tick in each bucket
    for ch in pd.read_csv(tp[0], compression="gzip",
                          usecols=["time_msc", "bid", "ask"],
                          dtype={"time_msc": np.int64, "bid": np.float64,
                                 "ask": np.float64}, chunksize=4_000_000):
        tm = ch["time_msc"].to_numpy()
        bid = ch["bid"].to_numpy()
        ask = ch["ask"].to_numpy()
        k = (tm // (TF * 1000)).astype(np.int64) - base
        ok = (k >= 0) & (k < nb)
        tm, bid, ask, k = tm[ok], bid[ok], ask[ok], k[ok]
        if k.size == 0:
            continue
        hit = tm == last_t[k]
        last_bid[k[hit]] = bid[hit]
        last_ask[k[hit]] = ask[hit]

    ki = (bt // TF).astype(np.int64) - base
    C = b["close"].to_numpy(float)
    H = b["high"].to_numpy(float)
    L = b["low"].to_numpy(float)
    SPCOL = b["spread"].to_numpy(float) if "spread" in b else np.full(C.size, np.nan)
    lb, la = last_bid[ki], last_ask[ki]
    good = np.isfinite(lb) & np.isfinite(la) & (la > lb)
    if good.sum() < 100:
        return dict(symbol=sym, n_bars=int(good.sum()), note="insufficient overlap")
    lb, la, C2 = lb[good], la[good], C[good]
    mid = 0.5 * (lb + la)
    sp = la - lb
    r_bid = (C2 - lb) / sp
    r_mid = (C2 - mid) / sp
    r_ask = (C2 - la) / sp
    who = np.argmin(np.abs(np.stack([r_bid, r_mid, r_ask])), axis=0)
    mb, mnb = max_bid[ki][good], min_bid[ki][good]
    ma, mna = max_ask[ki][good], min_ask[ki][good]
    H2, L2 = H[good], L[good]
    hb = (H2 - mb) / sp
    ha = (H2 - ma) / sp
    lbo = (L2 - mnb) / sp
    lao = (L2 - mna) / sp
    # bar spread column against tick spread inside the same bar
    point = None
    spc = SPCOL[good]
    tick_min = sp_min[ki][good]
    tick_mean = (sp_sum[ki] / np.maximum(sp_n[ki], 1))[good]
    ok2 = np.isfinite(spc) & (spc > 0) & np.isfinite(tick_min)
    if ok2.sum() > 50:
        point = float(np.median(tick_min[ok2] / spc[ok2]))
    return dict(
        symbol=sym, n_bars=int(good.sum()),
        close_vs={"bid_in_spreads": float(np.median(r_bid)),
                  "mid_in_spreads": float(np.median(r_mid)),
                  "ask_in_spreads": float(np.median(r_ask))},
        closest_share={"bid": float((who == 0).mean()), "mid": float((who == 1).mean()),
                       "ask": float((who == 2).mean())},
        exact_bid_share=float((np.abs(C2 - lb) < 1e-12).mean()),
        exact_ask_share=float((np.abs(C2 - la) < 1e-12).mean()),
        high_vs={"max_bid_in_spreads": float(np.median(hb)),
                 "max_ask_in_spreads": float(np.median(ha))},
        low_vs={"min_bid_in_spreads": float(np.median(lbo)),
                "min_ask_in_spreads": float(np.median(lao))},
        median_spread_price=float(np.median(sp)),
        median_mid=float(np.median(mid)),
        median_spread_bps=float(np.median(sp / mid) * 1e4),
        bar_spread_col_median=float(np.nanmedian(spc)),
        tick_min_over_barspread=point,
        tick_mean_spread_price=float(np.median(tick_mean[np.isfinite(tick_mean)])),
    )


def main():
    syms = sorted(os.path.basename(p).split("_ticks_")[0].split("_", 1)[1]
                  for p in glob.glob(os.path.join(TICKS, "*_ticks_*.csv.gz")))
    out = []
    for i, s in enumerate(syms):
        try:
            r = do(s)
        except Exception as e:                                  # noqa: BLE001
            r = dict(symbol=s, error=str(e)[:200])
        if r is None:
            continue
        out.append(r)
        print("[%d/%d] %-14s n=%-6s close-bid=%+.3f close-mid=%+.3f closest=%s" % (
            i + 1, len(syms), s, r.get("n_bars"),
            (r.get("close_vs") or {}).get("bid_in_spreads", float("nan")),
            (r.get("close_vs") or {}).get("mid_in_spreads", float("nan")),
            max((r.get("closest_share") or {"?": 0}).items(), key=lambda kv: kv[1])[0]),
            flush=True)
        json.dump(out, open(OUT, "w"), indent=1)
    print("DONE", len(out))


if __name__ == "__main__":
    main()
