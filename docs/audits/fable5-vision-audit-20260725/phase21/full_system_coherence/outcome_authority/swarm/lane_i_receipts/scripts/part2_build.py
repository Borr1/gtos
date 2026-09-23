"""LANE I Part 2 — build the conditioned forward-return panel from the bar archives.

Sources (SOURCE_CATALOG.json: time_column_basis "true_utc",
broker_clock_rule "new_york_plus_7", clock_conversion "broker_epoch_to_utc"):
  H4/D1  sources/bars/deep_universe_h4d1_2014_2026   24 symbols, 2014-01 -> 2026-06
  M15    sources/bars/bridge_ftmo_m15_20250601_20260610  24 symbols, 2025-06 -> 2026-06
"""
import json, sys, time
from pathlib import Path
import numpy as np, pandas as pd

HOLD = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
            "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars")
DEEP = HOLD / "deep_universe_h4d1_2014_2026"
M15D = HOLD / "bridge_ftmo_m15_20250601_20260610"
OUT = Path("/tmp/lane_i")


def atr(h, l, c, n):
    pc = np.r_[np.nan, c[:-1]]
    tr = np.nanmax(np.c_[h - l, np.abs(h - pc), np.abs(l - pc)], axis=1)
    return pd.Series(tr).rolling(n, min_periods=n).mean().to_numpy()


def roll(x, n, fn):
    return getattr(pd.Series(x).rolling(n, min_periods=n), fn)().to_numpy()


def build(path, symbol, grid, horizons):
    d = pd.read_csv(path)
    t = pd.to_datetime(d['time'], utc=True, format='ISO8601')
    o, h, l, c = (d[k].to_numpy(float) for k in ('open', 'high', 'low', 'close'))
    n = len(c)
    a14, a50 = atr(h, l, c, 14), atr(h, l, c, 50)
    ret1 = np.r_[np.nan, np.diff(c)]
    out = {
        'symbol': symbol, 'grid': grid, 'time': t.to_numpy(), 'close': c, 'high': h, 'low': l,
        'atr14': a14, 'atr50': a50,
        # --- pre-decision conditioning state, all computed from bars <= t ---------
        'vol_regime': a14 / a50,
        'vol_ratio_cc': roll(ret1 / a14, 8, 'std') / roll(ret1 / a14, 48, 'std'),
        'trend_dev_atr': (c - roll(c, 50, 'mean')) / a14,
        'mom6_atr': (c - np.r_[[np.nan] * 6, c[:-6]]) / a14,
        'mom24_atr': (c - np.r_[[np.nan] * 24, c[:-24]]) / a14,
        'range_pos20': (c - roll(l, 20, 'min')) / (roll(h, 20, 'max') - roll(l, 20, 'min')),
        'dist_high20_atr': (roll(h, 20, 'max') - c) / a14,
        'dist_low20_atr': (c - roll(l, 20, 'min')) / a14,
        'bar_range_atr': (h - l) / a14,
        'compression': (h - l) / roll(h - l, 20, 'mean'),
        'hour': t.dt.hour.to_numpy(), 'weekday': t.dt.weekday.to_numpy(),
        'dom': t.dt.day.to_numpy(), 'year': t.dt.year.to_numpy(),
    }
    for hz in horizons:
        fwd = np.r_[c[hz:], [np.nan] * hz] - c
        out[f'fwd{hz}_atr'] = fwd / a14
        # forward path extremes (for the barrier / asymmetry work)
        hi = pd.Series(h).rolling(hz, min_periods=hz).max().shift(-hz).to_numpy()
        lo = pd.Series(l).rolling(hz, min_periods=hz).min().shift(-hz).to_numpy()
        out[f'mfe{hz}_atr'] = (hi - c) / a14
        out[f'mae{hz}_atr'] = (c - lo) / a14
    return pd.DataFrame(out)


def main():
    t0 = time.time()
    specs = [
        ("H4", DEEP, "_H4.csv", [1, 3, 6, 18, 30]),      # 4h, 12h, 1d, 3d, 5d
        ("D1", DEEP, "_D1.csv", [1, 3, 5, 10]),           # 1d, 3d, 5d, 10d
        ("M15", M15D, "_M15.csv", [4, 8, 16, 32, 96]),    # 1h, 2h, 4h, 8h, 1d
    ]
    for grid, root, suffix, hz in specs:
        frames = []
        for p in sorted(root.glob("*" + suffix)):
            sym = p.name[:-len(suffix)]
            frames.append(build(p, sym, grid, hz))
        df = pd.concat(frames, ignore_index=True)
        df['symbol'] = df['symbol'].astype('category')
        df.to_parquet(OUT / f"bars_{grid}.parquet")
        print(json.dumps({"grid": grid, "symbols": int(df.symbol.nunique()), "rows": len(df),
                          "first": str(df.time.min()), "last": str(df.time.max()),
                          "t": round(time.time() - t0, 1)}), flush=True)


main()
