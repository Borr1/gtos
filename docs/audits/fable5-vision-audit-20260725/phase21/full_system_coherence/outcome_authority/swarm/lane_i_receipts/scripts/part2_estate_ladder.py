"""LANE I Part 2 bridge — the estate's OWN contract, lengthened.

The five-month candidate population runs a 2-hour label span with median
stop 0.986 x M15-ATR14 and median target 1.479 x ATR14 (R:R 1.5).  This file
prices that exact geometry on the M15 bar archive, then walks the horizon and
the target out, so the cost of the short contract is a measured number rather
than an argument.  Every bar of every symbol is an entry -- there is no rule
here, only geometry.
"""
import json, time
from pathlib import Path
import numpy as np, pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

OUT = Path("/tmp/lane_i")
COST_ATR = 0.08972    # median cost_r * risk_over_atr over the eligible population


def touch(high, low, close, atr, s, k, H, side):
    n = len(close); pad = np.full(H, np.nan)
    hi = sliding_window_view(np.r_[high[1:], pad], H)[:n]
    lo = sliding_window_view(np.r_[low[1:], pad], H)[:n]
    cl = np.r_[close[H:], pad]
    if side == "LONG":
        hs = lo <= (close - s * atr)[:, None]; ht = hi >= (close + k * atr)[:, None]
        drift = (cl - close) / (s * atr)
    else:
        hs = hi >= (close + s * atr)[:, None]; ht = lo <= (close - k * atr)[:, None]
        drift = (close - cl) / (s * atr)
    BIG = H + 1
    i_s = np.where(hs.any(1), hs.argmax(1), BIG); i_t = np.where(ht.any(1), ht.argmax(1), BIG)
    none = (i_s == BIG) & (i_t == BIG)
    out = np.where(none, drift, np.where(i_s <= i_t, -1.0, k / s))
    out[~np.isfinite(atr) | (atr <= 0) | ~np.isfinite(cl)] = np.nan
    lab = np.where(none, 2, np.where(i_s <= i_t, 0, 1)).astype(float)
    return out, lab


def main():
    t0 = time.time()
    d = pd.read_parquet(OUT / "bars_M15.parquet").sort_values(['symbol', 'time']).reset_index(drop=True)
    d['vol_regime__q'] = d.groupby('symbol', observed=True)['vol_regime'].transform(
        lambda s: pd.qcut(s.rank(method='first'), 5, labels=False, duplicates='drop'))
    S = 1.0
    # 8 M15 bars = the estate's own 2-hour label span
    LADDER = [(1.5, 8), (1.5, 32), (1.5, 96), (1.5, 288),
              (2.0, 8), (2.0, 32), (2.0, 96), (2.0, 288),
              (3.0, 32), (3.0, 96), (3.0, 288),
              (5.0, 96), (5.0, 288), (5.0, 672)]
    rows, cond = [], []
    vq = d['vol_regime__q'].to_numpy(float)
    for k, H in LADDER:
        for side in ("LONG", "SHORT"):
            out = np.full(len(d), np.nan); lab = np.full(len(d), np.nan)
            for _s, g in d.groupby('symbol', observed=True):
                i = g.index.to_numpy()
                o, l = touch(g['high'].to_numpy(float), g['low'].to_numpy(float),
                             g['close'].to_numpy(float), g['atr14'].to_numpy(float), S, k, H, side)
                out[i] = o; lab[i] = l
            ok = np.isfinite(out); y = out[ok]
            rows.append({"grid": "M15", "stop_atr": S, "target_atr": k, "horizon_bars": H,
                         "horizon_hours": H * 0.25, "side": side, "n": int(ok.sum()),
                         "win_rate": round(float((lab[ok] == 1).mean()), 5),
                         "breakeven_win_rate": round(1.0 / (1.0 + k / S), 5),
                         "stop_rate": round(float((lab[ok] == 0).mean()), 5),
                         "timeout_rate": round(float((lab[ok] == 2).mean()), 5),
                         "gross_expectancy_r": round(float(y.mean()), 5),
                         "net_expectancy_r": round(float(y.mean()) - COST_ATR / S, 5),
                         "se_r": round(float(y.std(ddof=1) / np.sqrt(len(y))), 5)})
            for L in range(5):
                sel = ok & (vq == L)
                if sel.sum() < 5000:
                    continue
                yy = out[sel]
                cond.append({"stop_atr": S, "target_atr": k, "horizon_bars": H, "horizon_hours": H * 0.25,
                             "side": side, "vol_regime_quintile": L, "n": int(sel.sum()),
                             "gross_expectancy_r": round(float(yy.mean()), 5),
                             "net_expectancy_r": round(float(yy.mean()) - COST_ATR / S, 5),
                             "se_r": round(float(yy.std(ddof=1) / np.sqrt(len(yy))), 5),
                             "win_rate": round(float((lab[sel] == 1).mean()), 5)})
        print(json.dumps({"cell": f"{k}:{H}", "t": round(time.time() - t0, 1)}), flush=True)
    rep = {"schema": "gtos.lane_i.estate_contract_ladder.v1",
           "grid": "M15 (bridge_ftmo_m15_20250601_20260610, true UTC, 24 symbols, 612,190 bars, "
                   "2025-06-01..2026-06-09)",
           "estate_contract_reference": {
               "label_span_hours_median": 2.0, "stop_distance_atr_median": 0.9857,
               "target_distance_atr_median": 1.4786, "risk_over_atr_median": 0.9591,
               "implied_rr": 1.5, "cost_in_atr_units_median": COST_ATR},
           "ladder": rows, "by_vol_regime": cond}
    (OUT / "PART2_ESTATE_CONTRACT_LADDER.json").write_text(json.dumps(rep, indent=1, sort_keys=True))
    pd.DataFrame(rows).to_csv(OUT / "PART2_ESTATE_CONTRACT_LADDER.csv", index=False)
    print("DONE", round(time.time() - t0, 1))


main()
