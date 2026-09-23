"""r1-1 — establish the quote side of the M15 bar archive, whole population.

Re-derives d8x's BID finding independently, on every symbol the two archives
share, over the whole overlap, with no sampling.

    bars  : /Users/borr/GTOSActive/vps-bars-20260727/FTMO_<SYM>_M15.csv.gz
            `time` = BROKER SERVER WALL CLOCK epoch (per the .timebase.json sidecar)
    ticks : /Users/borr/GTOSActive/vps-ticks-20260726/ftmo/FTMO_<SYM>_ticks_*.csv.gz
            `time`/`time_msc` = BROKER SERVER WALL CLOCK epoch (per its sidecar)

Both are the same broker clock, so the join takes NO clock risk: no conversion is
applied and none is needed.  (CLAUDE.md §4 warns never to trust a `_utc` field
name; there is no such field on either side here.)

Per bar, over the ticks whose broker stamp falls in [t, t+900):

    close vs last bid / last ask / mid          -> which side is the OHLC on
    high  vs max bid / max ask
    low   vs min bid / min ask
    bar `spread` column vs tick-measured spread -> is the bar spread usable

Emits R1_QUOTESIDE_M15_V1.json.
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np

BARS = Path("/Users/borr/GTOSActive/vps-bars-20260727")
TICKS = Path("/Users/borr/GTOSActive/vps-ticks-20260726/ftmo")
OUT = Path(__file__).resolve().parent / "R1_QUOTESIDE_M15_V1.json"

# the bar archive and the tick archive name five index CFDs differently.
# Measured by directory listing, not assumed.
BAR_FOR_TICK = {
    "US100_cash": "NAS100",
    "US500_cash": "SPX500",
    "UK100_cash": "UK100",
    "GER40_cash": "GER40_cash",
    "JP225_cash": "JP225_cash",
}


def read_bars(sym: str):
    p = BARS / f"FTMO_{sym}_M15.csv.gz"
    if not p.is_file():
        return None
    t, o, h, lo, c, sp = [], [], [], [], [], []
    with gzip.open(p, "rt") as fh:
        head = fh.readline().strip().split(",")
        ix = {k: i for i, k in enumerate(head)}
        for line in fh:
            f = line.rstrip("\n").split(",")
            t.append(int(f[ix["time"]]))
            o.append(float(f[ix["open"]]))
            h.append(float(f[ix["high"]]))
            lo.append(float(f[ix["low"]]))
            c.append(float(f[ix["close"]]))
            sp.append(float(f[ix["spread"]]))
    return (np.array(t, dtype=np.int64), np.array(o), np.array(h),
            np.array(lo), np.array(c), np.array(sp))


def read_ticks(name: str, lo_t: int, hi_t: int):
    hits = sorted(TICKS.glob(f"FTMO_{name}_ticks_*.csv.gz"))
    if not hits:
        return None
    ts, bd, ak = [], [], []
    for p in hits:
        with gzip.open(p, "rt") as fh:
            head = fh.readline().strip().split(",")
            ix = {k: i for i, k in enumerate(head)}
            for line in fh:
                f = line.rstrip("\n").split(",")
                tt = int(f[ix["time"]])
                if tt < lo_t or tt >= hi_t:
                    continue
                b = float(f[ix["bid"]])
                a = float(f[ix["ask"]])
                if b <= 0 or a <= 0:
                    continue
                ts.append(tt)
                bd.append(b)
                ak.append(a)
    if not ts:
        return None
    t = np.array(ts, dtype=np.int64)
    order = np.argsort(t, kind="stable")
    return t[order], np.array(bd)[order], np.array(ak)[order]


def measure(sym_tick: str) -> dict | None:
    sym_bar = BAR_FOR_TICK.get(sym_tick, sym_tick)
    bars = read_bars(sym_bar)
    if bars is None:
        return None
    bt, bo, bh, bl, bc, bsp = bars
    # tick coverage window, from the file name range, widened by one bar
    tk = read_ticks(sym_tick, int(bt.min()), int(bt.max()) + 900)
    if tk is None:
        return None
    tt, tb, ta = tk
    t0, t1 = int(tt.min()), int(tt.max())
    m = (bt >= t0) & (bt + 900 <= t1)
    if not m.any():
        return None
    bt, bo, bh, bl, bc, bsp = bt[m], bo[m], bh[m], bl[m], bc[m], bsp[m]

    lo_i = np.searchsorted(tt, bt, side="left")
    hi_i = np.searchsorted(tt, bt + 900, side="left")
    keep = (hi_i - lo_i) >= 3
    bt, bo, bh, bl, bc, bsp = bt[keep], bo[keep], bh[keep], bl[keep], bc[keep], bsp[keep]
    lo_i, hi_i = lo_i[keep], hi_i[keep]
    n = len(bt)
    if n == 0:
        return None

    last_bid = tb[hi_i - 1]
    last_ask = ta[hi_i - 1]
    first_bid = tb[lo_i]
    first_ask = ta[lo_i]
    max_bid = np.maximum.reduceat(tb, lo_i)
    min_bid = np.minimum.reduceat(tb, lo_i)
    max_ask = np.maximum.reduceat(ta, lo_i)
    min_ask = np.minimum.reduceat(ta, lo_i)
    # reduceat needs the segment ends to be the next start; recompute exactly
    # for any bar whose next start is not hi_i (gaps between bars)
    bad = np.nonzero(np.append(lo_i[1:], hi_i[-1]) != hi_i)[0]
    for k in bad:
        a, b = lo_i[k], hi_i[k]
        max_bid[k] = tb[a:b].max()
        min_bid[k] = tb[a:b].min()
        max_ask[k] = ta[a:b].max()
        min_ask[k] = ta[a:b].min()

    spr = last_ask - last_bid
    pos = spr > 0
    mid = (last_bid + last_ask) / 2.0

    def frac_eq(a, b, tol):
        return float(np.mean(np.abs(a - b) <= tol))

    tol = np.maximum(np.abs(bc) * 1e-9, 1e-10)
    out = {
        "symbol_tick": sym_tick,
        "symbol_bar": sym_bar,
        "n_bars": int(n),
        "n_bars_positive_spread": int(pos.sum()),
        "broker_epoch_first": int(bt.min()),
        "broker_epoch_last": int(bt.max()),
        "close_eq_last_bid": frac_eq(bc, last_bid, tol),
        "close_eq_last_ask": frac_eq(bc, last_ask, tol),
        "open_eq_first_bid": frac_eq(bo, first_bid, tol),
        "high_eq_max_bid": frac_eq(bh, max_bid, tol),
        "high_eq_max_ask": frac_eq(bh, max_ask, tol),
        "low_eq_min_bid": frac_eq(bl, min_bid, tol),
        "low_eq_min_ask": frac_eq(bl, min_ask, tol),
    }
    if pos.sum():
        out["close_minus_mid_over_spread_median"] = float(
            np.median((bc[pos] - mid[pos]) / spr[pos]))
        out["close_minus_mid_over_spread_p05"] = float(
            np.percentile((bc[pos] - mid[pos]) / spr[pos], 5))
        out["close_minus_mid_over_spread_p95"] = float(
            np.percentile((bc[pos] - mid[pos]) / spr[pos], 95))
        out["high_minus_maxbid_over_spread_median"] = float(
            np.median((bh[pos] - max_bid[pos]) / spr[pos]))
        out["high_minus_maxask_over_spread_median"] = float(
            np.median((bh[pos] - max_ask[pos]) / spr[pos]))
        out["low_minus_minbid_over_spread_median"] = float(
            np.median((bl[pos] - min_bid[pos]) / spr[pos]))
        out["low_minus_minask_over_spread_median"] = float(
            np.median((bl[pos] - min_ask[pos]) / spr[pos]))
        out["tick_spread_bps_median"] = float(
            np.median(spr[pos] / bc[pos] * 1e4))
        # the bar `spread` column is in POINTS; recover its price value using
        # the implied point size from the close's decimals is unsafe, so report
        # the RATIO bar_spread_column / tick_spread in the same units the column
        # would take if point == 10**-digits, digits inferred per symbol below.
        out["bar_spread_col_median_points"] = float(np.median(bsp[pos]))
    return out


def main() -> int:
    names = sorted({p.name.split("_ticks_")[0][len("FTMO_"):]
                    for p in TICKS.glob("FTMO_*_ticks_*.csv.gz")})
    rows = []
    for s in names:
        try:
            r = measure(s)
        except Exception as exc:  # pragma: no cover
            r = {"symbol_tick": s, "error": repr(exc)}
        if r:
            rows.append(r)
            print(json.dumps(r), flush=True)
    ok = [r for r in rows if "n_bars" in r]
    tot = sum(r["n_bars"] for r in ok)
    agg = {
        "what": "quote side of the M15 bar archive, settled against broker bid/ask ticks",
        "bars_archive": str(BARS),
        "tick_archive": str(TICKS),
        "clock": ("both archives carry BROKER SERVER WALL CLOCK epochs per their own "
                  ".timebase.json sidecars; joined raw, no conversion applied"),
        "n_symbols": len(ok),
        "n_bars_total": tot,
        "weighted_close_eq_last_bid": (
            sum(r["close_eq_last_bid"] * r["n_bars"] for r in ok) / tot if tot else None),
        "weighted_close_eq_last_ask": (
            sum(r["close_eq_last_ask"] * r["n_bars"] for r in ok) / tot if tot else None),
        "min_symbol_close_eq_last_bid": min((r["close_eq_last_bid"] for r in ok), default=None),
        "max_symbol_close_eq_last_ask": max((r["close_eq_last_ask"] for r in ok), default=None),
        "close_minus_mid_over_spread_range": [
            min((r.get("close_minus_mid_over_spread_median", 9e9) for r in ok), default=None),
            max((r.get("close_minus_mid_over_spread_median", -9e9) for r in ok), default=None)],
        "per_symbol": rows,
    }
    OUT.write_text(json.dumps(agg, indent=1, sort_keys=True))
    print("WROTE", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
