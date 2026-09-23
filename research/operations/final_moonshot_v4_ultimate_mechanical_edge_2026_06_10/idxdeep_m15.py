"""idxdeep M15 reclaim-timing test (track key: idxdeep).

For each H4 failed-breakout fade that passes the cross-sectional 'against-basket' gate, instead of
entering at the H4 close, wait inside the NEXT H4 window for an M15 RECLAIM-CONFIRM and enter there.

Reclaim-confirm (leak-free, all on CLOSED M15 bars after the H4 signal bar closes):
  SHORT fade (level=rhi): take first M15 bar that closes back BELOW rhi after a wick above it
                          OR (simpler) first M15 close below rhi - 0.0 within the window.
  LONG  fade (level=rlo): first M15 close back ABOVE rlo.
We require the reclaim to happen within the next H4 window (16 M15 bars). Entry = that M15 close.
Stop/target in the SAME R units as H4 (stop_atr * H4_ATR), scored on the M15 stream via simulate
(maxbars scaled: H4 maxbars 60 -> M15 60*16=960). This tests whether intrabar timing of the reclaim
lifts win-rate / lets the 0.75R target hit before the mean-revert fades.

NO LOOKAHEAD: H4 signal bar i must close (actionable from T_h4[i]+4h). M15 confirm uses only M15 bars
with open-time >= that instant and < next H4 close. Cost = w1.cost_for(sym)/stop_atr (same as H4).
Forward-only (M15 starts 2025-06) -> reported as TIMING evidence, not a holdout.
"""
import sys, os, csv, bisect
from datetime import datetime, timedelta
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from geometry_lib import simulate, atr14, Bar
import wave1_structure_setups_ict as w1
import idxrev_sleeve as ir
import idxdeep_xsec as X

DATA = str(HERE.parents[2]) + "/data/mt5_research_exports"
M15MAP = {
 'SPX500':      DATA+'/bridge_ftmo_m15_20250601_20260610/SPX500_M15.csv',
 'GER40':       DATA+'/bridge_ftmo_m15_20250601_20260610/GER40_M15.csv',
 'JP225':       DATA+'/bridge_ftmo_m15_20250601_20260610/JP225_M15.csv',
 'UK100':       DATA+'/bridge_ftmo_m15_20250601_20260610/UK100_M15.csv',
 'US30_cash':   DATA+'/bridge_ftmo_m15_20250601_20260610/US30_cash_M15.csv',
 'EU50_cash':   DATA+'/bridge_ftmo_ext_m15_20250601_20260611/EU50_cash_M15.csv',
 'FRA40_cash':  DATA+'/bridge_ftmo_ext_m15_20250601_20260611/FRA40_cash_M15.csv',
 'US2000_cash': DATA+'/bridge_ftmo_ext_m15_20250601_20260611/US2000_cash_M15.csv',
}
_M15 = {}
def load_m15(sym):
    if sym in _M15: return _M15[sym]
    p = M15MAP.get(sym); T=[]; B=[]
    if p and os.path.exists(p):
        with open(p) as f:
            for row in csv.DictReader(f):
                try:
                    t=datetime.strptime(row['time'],'%Y-%m-%d %H:%M:%S')
                    B.append(Bar(float(row['open']),float(row['high']),float(row['low']),
                                 float(row['close']),float(row.get('volume',0) or 0)))
                    T.append(t)
                except Exception: continue
    _M15[sym]=(T,B); return _M15[sym]

def wins(r): return max(-1.3, min(5.0, r))

def first_idx_ge(T, ts):
    lo=bisect.bisect_left(T, ts)
    return lo if lo < len(T) else None

def run(symbols, lb_range=16, stop_atr=1.5, tgt_R=0.75, maxbars_h4=60,
        against_gate=True, sign_flip_mabs=0.4, confirm_window_m15=16):
    """H4 signal -> M15 reclaim entry. Returns rows with R scored on M15 stream.
    Also returns the H4-baseline R for the SAME signals for a matched comparison."""
    rows=[]
    for s in symbols:
        Tm, Bm = load_m15(s)
        if len(Bm) < 50: continue
        cost = w1.cost_for(s); rcost = cost/stop_atr
        m15_per_h4 = 16
        mb_m15 = maxbars_h4 * m15_per_h4
        for (t, d, i, B, ac, vr, a, dist_opp, c, rhi, rlo, pdh, pdl) in ir.signals(s, lb_range):
            if t.year < 2025: continue  # M15 forward-only
            # cross-sectional gate (leak-free, from xsec module)
            if against_gate:
                _, mabs, _, signed = X.basket_state(t, 10)
                if d*signed >= 0: continue
                if s in X.SIGN_FLIP and mabs < sign_flip_mabs: continue
            # actionable instant: H4 signal bar closes at t + 4h
            t_close = t + timedelta(hours=4)
            j0 = first_idx_ge(Tm, t_close)
            if j0 is None: continue
            level = rhi if d < 0 else rlo
            sd = stop_atr * a
            # H4-baseline (matched): enter at H4 close c, scored on M15 from j0
            jbase = first_idx_ge(Tm, t)
            entered=False
            for k in range(j0, min(j0+confirm_window_m15, len(Bm))):
                bm = Bm[k]
                # reclaim confirm on CLOSED m15 bar
                if d < 0 and bm.c < level:   # short: m15 closes back below swept high
                    eidx=k; entered=True; break
                if d > 0 and bm.c > level:   # long: m15 closes back above swept low
                    eidx=k; entered=True; break
            if not entered: continue
            R = simulate(Bm, eidx, d, stop_dist=sd, target_dist=tgt_R*sd, maxbars=mb_m15, cost=rcost)
            rows.append(dict(sym=s, year=t.year, date=str(t)[:10], dir=d, R=wins(R), mode='m15'))
    return rows

def stat(rows):
    if not rows: return (0,0.0,0.0)
    n=len(rows); m=sum(r['R'] for r in rows)/n; w=sum(1 for r in rows if r['R']>0)/n*100
    return n,m,w
