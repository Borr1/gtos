"""GOLD SLEEVE — canonical deployable reference implementation (the one audited edge).

Spec (converged over 8 research waves, see ULTIMATE_GO_LIVE_DOSSIER.md):
  ENTRY  : H4 FVG-retest continuation in HTF trend (identical to wave1 setup_ob_fvg_retest).
  GATE   : volatility-expansion — take only when ATR14 >= GATE_K * SMA100(ATR14) (GATE_K=1.2).
  STOP   : structural (just beyond the retest/gap extreme + 0.10*ATR, floor 0.25*ATR).
  TARGET : 2R.
  UNIVERSE: precious metals only (XAU/XAG in USD/EUR/AUD).
  SIZING : correlated-risk-unit — all same-decision-day metals trades share ONE risk unit.
All fills via the unit-tested geometry_lib. No lookahead (gate is a pure price function; sizing
groups by decision day). This is the reference for owner-approved live wiring; it changes nothing live.
"""
from __future__ import annotations
import sys, math, statistics, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from geometry_lib import atr14, simulate
import wave1_structure_setups_ict as w1   # reuse audited load()/htf_trend()/cost_for()

GATE_K = 1.2
TARGET_R = 2.0
STOP_BUF = 0.10
ATR_STOP_FLOOR = 0.25
METALS = ["XAUUSD", "XAGUSD", "XAUEUR", "XAGEUR", "XAUAUD", "XAGAUD"]

def _atr_series(B):
    return [atr14(B, i) for i in range(len(B))]

def fvg_signals(sym, gate_k=GATE_K):
    """Yield (time, direction, stop_dist, target_dist) for vol-gated FVG-retest entries."""
    T, B = w1.load(sym)
    if len(B) < 200: return []
    atrs = _atr_series(B); n = len(B); out = []
    for i in range(60, n - 1):
        a = atrs[i]
        if a <= 0: continue
        # VOL GATE (pure price-history function; no lookahead)
        if i >= 100:
            sma100 = sum(atrs[i-99:i+1]) / 100
            if sma100 <= 0 or a < gate_k * sma100: continue
        else:
            continue
        tr = w1.htf_trend(B, i, 30); b = B[i]
        if tr == 1:
            for k in range(i-2, max(i-9, 60), -1):
                gap_top = B[k].l; gap_bot = B[k-2].h
                if gap_top - gap_bot < 0.10*a: continue
                if b.l <= gap_top and b.c > gap_bot and b.c > b.o:
                    sd = max((b.c - min(b.l, gap_bot)) + STOP_BUF*a, ATR_STOP_FLOOR*a)
                    out.append((T[i], +1, sd, TARGET_R*sd, i)); break
        elif tr == -1:
            for k in range(i-2, max(i-9, 60), -1):
                gap_bot = B[k].h; gap_top = B[k-2].l
                if gap_top - gap_bot < 0.10*a: continue
                if b.h >= gap_bot and b.c < gap_top and b.c < b.o:
                    sd = max((max(b.h, gap_top) - b.c) + STOP_BUF*a, ATR_STOP_FLOOR*a)
                    out.append((T[i], -1, sd, TARGET_R*sd, i)); break
    return [(t, d, sd, td, i, B, w1.cost_for(sym)) for (t, d, sd, td, i) in out]

def backtest(risk_per_unit=0.01, gate_k=GATE_K):
    """Correlated-risk-unit equity sim. Returns per-year R, monthly%, maxDD, worst-day, ftmo_ok."""
    trades = []  # (date, R)
    for sym in METALS:
        for (t, d, sd, td, i, B, cost) in fvg_signals(sym, gate_k):
            r = simulate(B, i, d, stop_dist=sd, target_dist=td, cost=cost)
            trades.append((t, r))
    trades.sort(key=lambda x: x[0])
    # per-year R (unsized)
    yr = collections.defaultdict(lambda: [0, 0.0])
    for t, r in trades:
        yr[t.year][0] += 1; yr[t.year][1] += r
    per_year = {y: round(v[1]/v[0], 4) for y, v in sorted(yr.items()) if v[0]}
    # correlated-risk-unit: group by decision DAY, all metals that day = 1 unit split equally
    byday = collections.defaultdict(list)
    for t, r in trades: byday[t.date()].append(r)
    equity = 1.0; peak = 1.0; maxdd = 0.0; worst_day = 0.0; daily = []
    for day in sorted(byday):
        rs = byday[day]; unit_r = sum(rs)/len(rs)  # cluster = 1 unit, equal split
        day_pct = unit_r * risk_per_unit
        equity *= (1 + day_pct); peak = max(peak, equity)
        dd = (peak-equity)/peak; maxdd = max(maxdd, dd); worst_day = min(worst_day, day_pct)
        daily.append(day_pct)
    n_days = max(1, (max(byday)-min(byday)).days)
    monthly = (equity-1.0)/(n_days/30.4)
    full_R = sum(r for _, r in trades)/len(trades) if trades else 0.0
    return {"n_trades": len(trades), "full_per_trade_R": round(full_R, 4),
            "per_year_R": per_year, "pos_years": sum(1 for v in per_year.values() if v>0),
            "total_years": len(per_year),
            "risk_per_unit_pct": risk_per_unit*100, "monthly_pct": round(monthly*100, 4),
            "maxDD_pct": round(maxdd*100, 2), "worst_day_pct": round(worst_day*100, 2),
            "ftmo_ok": bool(maxdd < 0.10 and abs(worst_day) < 0.05)}

if __name__ == "__main__":
    import json
    for risk in (0.0025, 0.01):
        print(json.dumps(backtest(risk), sort_keys=True))
