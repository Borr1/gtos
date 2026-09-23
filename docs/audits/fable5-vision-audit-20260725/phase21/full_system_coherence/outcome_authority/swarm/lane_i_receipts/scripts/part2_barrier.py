"""LANE I Part 2 (Q5 + Q6) — horizon economics and payoff-shape asymmetry.

Q5 horizon:  how forward-return dispersion, conditional edge and the COST DRAG
             scale with holding horizon.  Cost is paid once; dispersion grows
             roughly with sqrt(t); so cost drag falls monotonically with horizon.
Q6 asymmetry: first-touch triple-barrier expectancy at fixed risk, computed on
             the bar path, conditional on pre-state.  A cell can pay at fixed
             risk with zero mean drift if the tail behaviour is asymmetric.

Tie rule: a bar that spans both barriers is scored STOP (conservative).  The
estate's own labeller CENSORS that case (CENSORED_SUBMISSION_BAR_LIMIT_TOUCH_
ORDERING / CENSORED_ORDERING_AMBIGUITY); scoring it as a loss is the strictly
pessimistic alternative and is stated as such.
"""
import json, time
from pathlib import Path
import numpy as np, pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

OUT = Path("/tmp/lane_i")
VARS = ['vol_regime', 'vol_ratio_cc', 'trend_dev_atr', 'mom6_atr', 'mom24_atr',
        'range_pos20', 'dist_high20_atr', 'dist_low20_atr', 'bar_range_atr', 'compression']


def first_touch(high, low, close, atr, stop_atr, tgt_atr, H, side):
    """Vectorised first-touch over the next H bars. Returns R outcome per bar."""
    n = len(close)
    pad = np.full(H, np.nan)
    hi = sliding_window_view(np.r_[high[1:], pad], H)[:n]
    lo = sliding_window_view(np.r_[low[1:], pad], H)[:n]
    cl = np.r_[close[H:], pad]
    if side == "LONG":
        stop, tgt = close - stop_atr * atr, close + tgt_atr * atr
        hit_s = lo <= stop[:, None]
        hit_t = hi >= tgt[:, None]
        drift = (cl - close) / (stop_atr * atr)
    else:
        stop, tgt = close + stop_atr * atr, close - tgt_atr * atr
        hit_s = hi >= stop[:, None]
        hit_t = lo <= tgt[:, None]
        drift = (close - cl) / (stop_atr * atr)
    BIG = H + 1
    i_s = np.where(hit_s.any(1), hit_s.argmax(1), BIG)
    i_t = np.where(hit_t.any(1), hit_t.argmax(1), BIG)
    out = np.where(i_s <= i_t, -1.0, np.where(i_t < i_s, tgt_atr / stop_atr, np.nan))
    none = (i_s == BIG) & (i_t == BIG)
    out = np.where(none, drift, out)
    bad = ~np.isfinite(atr) | (atr <= 0) | ~np.isfinite(cl)
    out[bad] = np.nan
    return out, np.where(none, 2, np.where(i_s <= i_t, 0, 1)).astype(float)


def main():
    t0 = time.time()
    report = {"schema": "gtos.lane_i.horizon_and_asymmetry.v1",
              "tie_rule": "bar spanning both barriers scored STOP (conservative)"}

    # ---- estate cost anchor, in ATR units, from the five-month population ----
    pop = pd.read_parquet(OUT / "pop.parquet")
    e = pop[pop.eligible]
    cost_atr = (e['cost_r'] * e['risk_over_atr']).dropna()
    report['estate_cost_anchor'] = {
        "median_cost_r": round(float(e['cost_r'].median()), 5),
        "median_risk_over_atr": round(float(e['risk_over_atr'].median()), 5),
        "median_cost_in_atr_units": round(float(cost_atr.median()), 5),
        "p90_cost_in_atr_units": round(float(cost_atr.quantile(0.90)), 5),
        "note": "cost_atr = cost_r * risk_over_atr; a barrier trade stopping at s ATR "
                "pays cost_atr/s in R",
    }
    C = float(cost_atr.median())

    # ---- Q5: horizon economics -------------------------------------------
    hz_tab = []
    for grid, hzs, hours in [("M15", [4, 16, 96], {4: 1, 16: 4, 96: 24}),
                             ("H4", [1, 6, 18, 30], {1: 4, 6: 24, 18: 72, 30: 120}),
                             ("D1", [1, 3, 5, 10], {1: 24, 3: 72, 5: 120, 10: 240})]:
        d = pd.read_parquet(OUT / f"bars_{grid}.parquet")
        for hz in hzs:
            f = d[f'fwd{hz}_atr'].to_numpy(float)
            f = f[np.isfinite(f)]
            sd = float(f.std())
            hz_tab.append({
                "grid": grid, "horizon_bars": hz, "horizon_hours": hours[hz], "n": int(len(f)),
                "fwd_sd_atr": round(sd, 5), "fwd_mean_abs_atr": round(float(np.abs(f).mean()), 5),
                "cost_drag_frac_of_1sd": round(C / sd, 5),
                "cost_drag_frac_of_mean_abs": round(C / float(np.abs(f).mean()), 5),
                "skew": round(float(pd.Series(f).skew()), 4),
                "kurtosis_excess": round(float(pd.Series(f).kurt()), 4),
                "tail_ratio_2sd": round(float((f > 2 * sd).mean() / max((f < -2 * sd).mean(), 1e-9)), 4),
            })
    report['horizon_economics'] = hz_tab
    print(json.dumps({"stage": "horizon", "t": round(time.time() - t0, 1)}), flush=True)

    # ---- Q6: barrier expectancy, unconditional and conditional -------------
    d = pd.read_parquet(OUT / "bars_H4.parquet")
    d = d.sort_values(['symbol', 'time']).reset_index(drop=True)
    for v in VARS:
        d[v + '__q'] = d.groupby('symbol', observed=True)[v].transform(
            lambda s: pd.qcut(s.rank(method='first'), 5, labels=False, duplicates='drop'))
    grids = [(1.0, k, H) for k in (1.0, 2.0, 3.0, 5.0) for H in (6, 18, 30)]
    res_cols = {}
    for stop_atr, tgt_atr, H in grids:
        for side in ("LONG", "SHORT"):
            out = np.full(len(d), np.nan); lab = np.full(len(d), np.nan)
            for _s, g in d.groupby('symbol', observed=True):
                i = g.index.to_numpy()
                o, l = first_touch(g['high'].to_numpy(float), g['low'].to_numpy(float),
                                   g['close'].to_numpy(float), g['atr14'].to_numpy(float),
                                   stop_atr, tgt_atr, H, side)
                out[i] = o; lab[i] = l
            res_cols[(stop_atr, tgt_atr, H, side)] = (out, lab)
        print(json.dumps({"stage": "barrier", "cell": f"{stop_atr}:{tgt_atr}:{H}",
                          "t": round(time.time() - t0, 1)}), flush=True)

    uncond, conds = [], []
    net_adj = C / 1.0   # stop = 1 ATR -> cost in R
    for (s, k, H, side), (out, lab) in res_cols.items():
        ok = np.isfinite(out)
        y = out[ok]
        row = {"stop_atr": s, "target_atr": k, "horizon_bars": H, "horizon_hours": H * 4,
               "side": side, "n": int(ok.sum()),
               "gross_expectancy_r": round(float(y.mean()), 5),
               "net_expectancy_r": round(float(y.mean()) - net_adj, 5),
               "win_rate": round(float((lab[ok] == 1).mean()), 5),
               "stop_rate": round(float((lab[ok] == 0).mean()), 5),
               "timeout_rate": round(float((lab[ok] == 2).mean()), 5),
               "breakeven_win_rate": round(1.0 / (1.0 + k / s), 5)}
        uncond.append(row)
        if H != 18 or k not in (2.0, 5.0):
            continue
        for v in VARS:
            b = d[v + '__q'].to_numpy(float)
            for L in range(5):
                sel = ok & (b == L)
                if sel.sum() < 2000:
                    continue
                yy = out[sel]
                fwd = d[f'fwd{H}_atr'].to_numpy(float)[sel]
                conds.append({
                    "variable": v, "quintile": L, "target_atr": k, "horizon_bars": H, "side": side,
                    "n": int(sel.sum()),
                    "gross_expectancy_r": round(float(yy.mean()), 5),
                    "net_expectancy_r": round(float(yy.mean()) - net_adj, 5),
                    "mean_fwd_atr": round(float(np.nanmean(fwd)), 5),
                    "win_rate": round(float((lab[sel] == 1).mean()), 5),
                    "skew_fwd": round(float(pd.Series(fwd).skew()), 4),
                    "tail_ratio_2sd": round(float(
                        (fwd > 2 * np.nanstd(fwd)).mean() / max((fwd < -2 * np.nanstd(fwd)).mean(), 1e-9)), 4),
                })
    report['barrier_unconditional'] = uncond
    report['barrier_conditional'] = conds
    (OUT / "PART2_HORIZON_ASYMMETRY.json").write_text(json.dumps(report, indent=1, sort_keys=True))
    pd.DataFrame(uncond).to_csv(OUT / "PART2_BARRIER_UNCONDITIONAL.csv", index=False)
    pd.DataFrame(conds).to_csv(OUT / "PART2_BARRIER_CONDITIONAL.csv", index=False)
    print("DONE", round(time.time() - t0, 1))


main()
