"""LANE I Part 2 — the conditioning-variable structure scan.

For every (conditioning variable x horizon x grid) cell:
  * quintile bins formed WITHIN SYMBOL (so cross-symbol scale never drives a bin)
  * effect = mean forward return (ATR units) in Q5 minus Q1, and the |fwd| version
  * monotonicity  = Spearman(bin index, bin mean) over the 5 bins
  * stability     = per-year effect, sign-agreement fraction, and a genuine
                    2014-2021 -> 2022-2026 holdout
  * null          = 200 circular shifts of the forward-return series within
                    symbol (destroys the conditional relation, preserves each
                    series' own autocorrelation and marginals).  Effects are
                    reported as z against that null SD -- NOT as p-values.

No trading rule is produced anywhere in this file.
"""
import json, sys, time
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import spearmanr

OUT = Path("/tmp/lane_i")
SEED = 20260811
NSHIFT = 200

VARS = ['vol_regime', 'vol_ratio_cc', 'trend_dev_atr', 'mom6_atr', 'mom24_atr',
        'range_pos20', 'dist_high20_atr', 'dist_low20_atr', 'bar_range_atr', 'compression',
        'usd_strength', 'risk_state', 'global_vol']
FACTORS = ['hour', 'weekday', 'dom_tertile']


def add_cross_asset(df):
    """Market-wide pre-decision state, joined on timestamp."""
    USD_UP = ['USDJPY', 'USDCHF', 'USDCAD']          # +USD
    USD_DN = ['EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD']  # -USD
    r = df.pivot_table(index='time', columns='symbol', values='mom6_atr', observed=True)
    have = [c for c in USD_UP if c in r] + [c for c in USD_DN if c in r]
    sgn = np.array([1.0] * len([c for c in USD_UP if c in r]) + [-1.0] * len([c for c in USD_DN if c in r]))
    usd = (r[have] * sgn).mean(axis=1)
    risk_syms = [c for c in ['US500_cash', 'SPX500', 'US100_cash', 'NAS100', 'GER40_cash', 'GER40'] if c in r]
    risk = r[risk_syms].mean(axis=1) if risk_syms else pd.Series(np.nan, index=r.index)
    gv = df.pivot_table(index='time', columns='symbol', values='bar_range_atr', observed=True).mean(axis=1)
    m = pd.DataFrame({'usd_strength': usd, 'risk_state': risk, 'global_vol': gv})
    return df.merge(m, left_on='time', right_index=True, how='left')


def qbin(s, k=5):
    """Quintile rank within the already-grouped series; NaN-safe."""
    try:
        return pd.qcut(s.rank(method='first'), k, labels=False, duplicates='drop')
    except Exception:
        return pd.Series(np.nan, index=s.index)


def scan_grid(grid, horizons, rng):
    df = pd.read_parquet(OUT / f"bars_{grid}.parquet")
    df = add_cross_asset(df)
    df['dom_tertile'] = pd.cut(df['dom'], [0, 10, 20, 32], labels=[0, 1, 2]).astype('float')
    for v in VARS:
        df[v + '__q'] = df.groupby('symbol', observed=True)[v].transform(qbin)
    rows = []
    sym_codes = df['symbol'].astype(str).to_numpy()
    order = np.lexsort((df['time'].to_numpy(), sym_codes))
    d = df.iloc[order].reset_index(drop=True)
    sym = d['symbol'].astype(str).to_numpy()
    bounds = np.r_[0, np.flatnonzero(sym[1:] != sym[:-1]) + 1, len(sym)]
    year = d['year'].to_numpy()

    for hz in horizons:
        f_signed = d[f'fwd{hz}_atr'].to_numpy(float)
        f_abs = np.abs(f_signed)
        sd = float(np.nanstd(f_signed))
        # pre-compute the circular-shift null population once per horizon
        shifted = []
        for _ in range(NSHIFT):
            z = np.empty_like(f_signed)
            for a, b in zip(bounds[:-1], bounds[1:]):
                k = rng.integers(200, max(201, b - a - 200))
                z[a:b] = np.roll(f_signed[a:b], k)
            shifted.append(z)
        shifted = np.asarray(shifted)

        for var, bincol, kind in ([(v, v + '__q', 'quintile') for v in VARS]
                                  + [(f, f, 'factor') for f in FACTORS]):
            b = d[bincol].to_numpy(float)
            ok = np.isfinite(b) & np.isfinite(f_signed)
            if ok.sum() < 5000:
                continue
            levels = np.unique(b[ok])
            if len(levels) < 2 or len(levels) > 30:
                continue
            gm = np.array([np.nanmean(f_signed[ok & (b == L)]) for L in levels])
            ga = np.array([np.nanmean(f_abs[ok & (b == L)]) for L in levels])
            gn = np.array([int((ok & (b == L)).sum()) for L in levels])
            lo, hi = int(np.argmin(gm)), int(np.argmax(gm))
            spread = float(gm[hi] - gm[lo])
            endpoint = float(gm[-1] - gm[0])            # ordered-endpoint effect
            mono = float(spearmanr(np.arange(len(levels)), gm).statistic) if len(levels) > 2 else np.nan
            abs_spread = float(ga.max() - ga.min())
            # null: max-minus-min of the same binning under circular shift
            null_sp = np.empty(NSHIFT)
            for i in range(NSHIFT):
                z = shifted[i]
                g = np.array([np.nanmean(z[ok & (b == L)]) for L in levels])
                null_sp[i] = g.max() - g.min()
            nz = float(np.std(null_sp)) or np.nan
            # stability: per-year endpoint effect, and the 2014-21 / 2022-26 holdout
            yrs, ysp = [], []
            for y in np.unique(year[ok]):
                sel = ok & (year == y)
                if sel.sum() < 800:
                    continue
                g = np.array([np.nanmean(f_signed[sel & (b == L)]) for L in levels])
                if np.isfinite(g).all():
                    yrs.append(int(y)); ysp.append(float(g[-1] - g[0]))
            ysp = np.asarray(ysp)
            sign_agree = float(np.mean(np.sign(ysp) == np.sign(endpoint))) if len(ysp) else np.nan
            def half(mask, series):
                g = np.array([np.nanmean(series[ok & mask & (b == L)]) for L in levels])
                return float(g[-1] - g[0]) if np.isfinite(g).all() else np.nan
            train_sp = half(year <= 2021, f_signed) if grid != 'M15' else np.nan
            test_sp = half(year >= 2022, f_signed) if grid != 'M15' else np.nan
            # --- the same treatment for the MAGNITUDE effect (|fwd|) ---------
            abs_endpoint = float(ga[-1] - ga[0])
            abs_train = half(year <= 2021, f_abs) if grid != 'M15' else np.nan
            abs_test = half(year >= 2022, f_abs) if grid != 'M15' else np.nan
            abs_mono = float(spearmanr(np.arange(len(levels)), ga).statistic) if len(levels) > 2 else np.nan
            ayr = []
            for y in np.unique(year[ok]):
                sel = ok & (year == y)
                if sel.sum() < 800:
                    continue
                g = np.array([np.nanmean(f_abs[sel & (b == L)]) for L in levels])
                if np.isfinite(g).all():
                    ayr.append(float(g[-1] - g[0]))
            ayr = np.asarray(ayr)
            abs_sign_agree = float(np.mean(np.sign(ayr) == np.sign(abs_endpoint))) if len(ayr) else np.nan
            # per-symbol stability of both effects
            def per_symbol(series, pooled):
                agree = []
                for sname in np.unique(sym):
                    sel = ok & (sym == sname)
                    if sel.sum() < 500:
                        continue
                    g = np.array([np.nanmean(series[sel & (b == L)]) for L in levels])
                    if np.isfinite(g).all():
                        agree.append(np.sign(g[-1] - g[0]) == np.sign(pooled))
                return (float(np.mean(agree)), len(agree)) if agree else (np.nan, 0)
            sym_sign, sym_n = per_symbol(f_signed, endpoint)
            asym_sign, _ = per_symbol(f_abs, abs_endpoint)
            rows.append({
                'grid': grid, 'horizon_bars': hz, 'variable': var, 'kind': kind,
                'levels': len(levels), 'n': int(ok.sum()),
                'fwd_sd_atr': round(sd, 5),
                'endpoint_effect_atr': round(endpoint, 5),
                'maxmin_spread_atr': round(spread, 5),
                'monotonicity_rho': None if not np.isfinite(mono) else round(mono, 4),
                'abs_return_spread_atr': round(abs_spread, 5),
                'endpoint_ir': round(endpoint / sd, 5) if sd else None,
                'null_shift_sd_atr': round(nz, 5) if np.isfinite(nz) else None,
                'z_vs_shift_null': round(spread / nz, 3) if np.isfinite(nz) and nz else None,
                'years_measured': len(ysp),
                'year_sign_agreement': None if not np.isfinite(sign_agree) else round(sign_agree, 3),
                'year_effect_median_atr': round(float(np.median(ysp)), 5) if len(ysp) else None,
                'holdout_train_2014_2021_atr': None if not np.isfinite(train_sp) else round(train_sp, 5),
                'holdout_test_2022_2026_atr': None if not np.isfinite(test_sp) else round(test_sp, 5),
                'symbols_measured': sym_n,
                'symbol_sign_agreement': None if not np.isfinite(sym_sign) else round(sym_sign, 3),
                'abs_endpoint_effect_atr': round(abs_endpoint, 5),
                'abs_endpoint_ir': round(abs_endpoint / sd, 5) if sd else None,
                'abs_monotonicity_rho': None if not np.isfinite(abs_mono) else round(abs_mono, 4),
                'abs_year_sign_agreement': None if not np.isfinite(abs_sign_agree) else round(abs_sign_agree, 3),
                'abs_symbol_sign_agreement': None if not np.isfinite(asym_sign) else round(asym_sign, 3),
                'abs_holdout_train_2014_2021_atr': None if not np.isfinite(abs_train) else round(abs_train, 5),
                'abs_holdout_test_2022_2026_atr': None if not np.isfinite(abs_test) else round(abs_test, 5),
                'level_means_atr': [round(float(x), 5) for x in gm],
                'level_n': gn.tolist(),
            })
        print(json.dumps({"grid": grid, "hz": hz, "cells": len(rows)}), flush=True)
    return rows


def main():
    rng = np.random.default_rng(SEED)
    t0 = time.time()
    allrows = []
    for grid, hz in [("H4", [1, 6, 18, 30]), ("D1", [1, 3, 5, 10]), ("M15", [4, 16, 96])]:
        allrows += scan_grid(grid, hz, rng)
        print(json.dumps({"grid_done": grid, "t": round(time.time() - t0, 1)}), flush=True)
    tab = pd.DataFrame(allrows)
    tab.to_parquet(OUT / "PART2_STRUCTURE_SCAN.parquet")
    tab.drop(columns=['level_means_atr', 'level_n']).to_csv(OUT / "PART2_STRUCTURE_SCAN.csv", index=False)
    (OUT / "PART2_STRUCTURE_SCAN.json").write_text(json.dumps(allrows, indent=1, sort_keys=True))
    print("DONE", len(allrows), round(time.time() - t0, 1))


main()
