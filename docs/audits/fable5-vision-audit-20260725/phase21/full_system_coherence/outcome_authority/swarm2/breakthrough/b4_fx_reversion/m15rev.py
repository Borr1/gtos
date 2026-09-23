"""S4 - the constructive variant of Lane 1's lead, on 12 years of bars.

S2b found that the amplitude-to-cost ratio of the 15-minute reversion is NOT
highest in Lane 1's late session (broker 00, ratio 0.075: 0.96 bp of amplitude
against a 14.97 bp round trip) but in the CASH session -- broker 15 (= UTC
12:00/13:00, the US data window) at ratio 2.22, broker 12 (London) at 1.08.
That is a different cell from the one Lane 1 named, in the opposite part of the
day, and it was measured on 38 days of ticks.  This file tests it on the
2014-2026 bar archive, where the sample is 300x longer.

Two statistics, both anchored so that the artifact cannot pass:
  * ac1 and the lag-1 reversion beta per broker hour, pairs formed strictly
    inside one broker day;
  * a DIRECT backtest -- fade the last M15 bar, hold one bar, pay the tape-true
    spread for that broker hour twice -- because a beta is not a P&L.
"""
from __future__ import annotations
import json, math, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from panel import m15_syms   # noqa: E402
from vr import CELL          # noqa: E402

OUT = os.path.join(HERE, "receipts")
CACHE = "/Users/borr/.claude/jobs/adb9e69b/tmp/b4cache"


def tick_spread_table():
    """median close-to-close spread by (symbol, broker hour), bp, from S2b."""
    p = f"{OUT}/S2b_HOURLY_BIDMID_ROLL.csv"
    d = pd.read_csv(p)
    return {(r.sym, int(r.bh)): float(r.sp_close_med_bp) for r in d.itertuples()}


def main():
    sp = tick_spread_table()
    d = m15_syms(CELL)
    rows, bt_rows = [], []
    for sym, g in d.groupby("sym", sort=True):
        g = g.sort_values("bt").reset_index(drop=True)
        lp = np.log(g["close"].values)
        r = np.diff(lp)
        bh = g["bh"].values[1:]
        day = g["bdate"].values
        same = day[1:] == day[:-1]
        okr = np.isfinite(r) & same
        x = r[:-1]; y = r[1:]; hx = bh[:-1]
        m0 = okr[:-1] & okr[1:]
        yr = pd.DatetimeIndex(g["bt"].values[1:-1]).year
        for h in range(24):
            m = m0 & (hx == h)
            if m.sum() < 500:
                continue
            xs, ys = x[m], y[m]
            ac1 = float(np.corrcoef(xs, ys)[0, 1])
            b = np.cov(xs, ys, ddof=1)[0, 1] / np.var(xs, ddof=1)
            res = ys - (ys.mean() - b * xs.mean() + b * xs)
            se = math.sqrt(np.sum(res ** 2) / (len(xs) - 2) / np.sum((xs - xs.mean()) ** 2))
            sd = float(xs.std(ddof=1) * 1e4)
            amp = abs(b) * sd if b < 0 else 0.0
            spr = sp.get((sym, h), np.nan)
            # ---- direct backtest: fade bar t by -sign(r_t), hold one bar
            pnl_bp = -np.sign(xs) * ys * 1e4
            gross = float(pnl_bp.mean())
            cost = 2.0 * spr if spr == spr else np.nan   # cross in and out
            rows.append(dict(sym=sym, bh=h, n=int(m.sum()), ac1=ac1, beta=float(b),
                             t=float(b / se), sd_bp=sd, amp_bp=float(amp),
                             spread_bp=spr, gross_bp=gross,
                             net_bp=gross - cost if cost == cost else np.nan,
                             ratio=float(amp / (2 * spr)) if spr == spr and spr > 0 else np.nan))
            # per-year for the top cells
            for Y in np.unique(yr[m]):
                mm = m.copy(); mm[m0] = mm[m0]  # noop, keep types
                sel = (hx == h) & m0 & (np.concatenate([yr, [yr[-1]]])[:len(hx)] == Y) \
                    if len(yr) < len(hx) else (hx == h) & m0 & (yr[:len(hx)] == Y)
                if sel.sum() < 100:
                    continue
                bt_rows.append(dict(sym=sym, bh=h, year=int(Y), n=int(sel.sum()),
                                    ac1=float(np.corrcoef(x[sel], y[sel])[0, 1]),
                                    gross_bp=float((-np.sign(x[sel]) * y[sel] * 1e4).mean())))
        print("done", sym, flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/S4_M15_HOURLY_REVERSION_12Y.csv", index=False)
    pd.DataFrame(bt_rows).to_csv(f"{OUT}/S4_M15_HOURLY_BY_YEAR.csv", index=False)

    pd.set_option("display.width", 220)
    agg = df.groupby("bh").agg(ac1=("ac1", "mean"), beta=("beta", "mean"),
                               t=("t", "mean"), sd_bp=("sd_bp", "mean"),
                               amp_bp=("amp_bp", "mean"), spread_bp=("spread_bp", "mean"),
                               gross_bp=("gross_bp", "mean"), net_bp=("net_bp", "mean"),
                               ratio=("ratio", "mean"), n=("n", "sum"))
    print("\n=== 12-YEAR ARCHIVE, 12 FX, by BROKER hour ===")
    print(agg.round(4).to_string())
    print("\n=== the three hours S2b's 38-day tick sample nominated ===")
    print(agg.loc[[12, 15, 17, 0]].round(4).to_string())


if __name__ == "__main__":
    main()
