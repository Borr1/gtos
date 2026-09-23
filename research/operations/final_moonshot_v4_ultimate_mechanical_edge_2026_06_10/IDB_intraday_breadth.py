"""IDB — INTRADAY BREADTH on the VALIDATED sleeves (track key: IDB).

GOAL (track: intraday frequency with QUALITY): add genuinely NEW intraday continuation
entries on the train-validated sleeves (crypto carriers, energy) by running the SAME proven
continuation rule (Donchian breakout + ac60 persistence gate + wide stop + deep target) on
the H1 / M15 streams instead of H4. These are NEW signals (a faster trigger fires more often),
not a re-timing of the H4 signal (that is the TW cascade, already done).

DOCTRINE held verbatim:
  - geometry_lib.simulate is the leak-free pessimistic labeler. Features from CLOSED bars index<=i.
  - ac60 = cs.autocorr on the SAME stream (closed bars only). vol_ratio = cs.vol_ratio.
  - Real cost w1.cost_for(sym) (crypto->global_median 0.0953; energy 0.0372), scaled by stop tightness.
  - Winsorize netR [-1.3,+5]. Size-by-confidence, nothing killed.
  - Frequency AND return both matter; report trades/year.

HOLDOUT (the honest one given LTF starts 2025-06):
  - LTF data is 2025-06..2026-06 only -> NO pre-2025 OOS exists for these symbols (same confound the
    TW cascade carries). So the time-split is the WITHIN-window holdout:
        TRAIN  = entries 2025-06 .. 2025-12  (pick the rule here)
        FWD    = entries 2026-01 .. 2026-06  (report the SAME rule forward)
  - PLUS per-symbol cross-validation: a rule that is positive across MULTIPLE independent carriers
    (7 crypto, 4 energy) is the cross-sectional substitute for a long time-split. Distrust any
    forward-only or single-symbol positive.
  - Mechanism credibility: the H4 version of THIS EXACT rule (Donchian+ac60+wide stop+4R) is the
    train-validated crypto/energy sleeve (KB_crypto/KB_energy_agri). Running it faster is a frequency
    extension of an already-causal edge, not a new hypothesis.
"""
from __future__ import annotations
import sys, os, csv, json, statistics
from datetime import datetime
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))
from geometry_lib import Bar, atr14, simulate
import wave1_structure_setups_ict as w1
import compounding_sleeve as cs

DATA = str(ROOT) + "/data/mt5_research_exports"
M15A = DATA + "/bridge_ftmo_m15_20250601_20260610"
M15B = DATA + "/bridge_ftmo_ext_m15_20250601_20260611"
H1A  = DATA + "/bridge_ftmo_htf_20250601_20260610"
H1B  = DATA + "/bridge_ftmo_ext_htf_20250601_20260611"

CRYPTO = ['BTCUSD','ETHUSD','DASHUSD','LTCUSD','DOTUSD','ADAUSD','XTZUSD']
ENERGY = ['USOIL_cash','UKOIL_cash','NATGAS_cash','HEATOIL_c']
METALS = ['XAUUSD','XAGUSD','XAUEUR','XAGEUR','XAUAUD','XAGAUD']

def wins(r): return max(-1.3, min(5.0, r))

def _path(grp, sym, tf):
    if tf == 'M15':
        pa, pb = f"{M15A}/{sym}_M15.csv", f"{M15B}/{sym}_M15.csv"
    else:
        pa, pb = f"{H1A}/{sym}_H1.csv", f"{H1B}/{sym}_H1.csv"
    return pa if os.path.exists(pa) else pb

_CACHE = {}
def load_ltf(grp, sym, tf):
    key = (sym, tf)
    if key in _CACHE: return _CACHE[key]
    p = _path(grp, sym, tf); T=[]; B=[]
    if os.path.exists(p):
        with open(p) as f:
            for row in csv.DictReader(f):
                try:
                    t = datetime.strptime(row['time'], "%Y-%m-%d %H:%M:%S")
                    B.append(Bar(float(row['open']),float(row['high']),float(row['low']),
                                 float(row['close']),float(row.get('volume',0) or 0)))
                    T.append(t)
                except Exception: continue
    _CACHE[key] = (T,B)
    return T,B

# ---- the proven continuation rule, run on an arbitrary stream ----
def breakout_signals(T, B, atrs, lb, ac_thr, sd_mult, tgt_R, cost, maxbars,
                     vr_min=None, vr_max=None):
    """Donchian-lb breakout (closed bars) + ac60>=ac_thr persistence + wide stop sd_mult*ATR
    + fixed tgt_R target. Optional vol-regime band [vr_min,vr_max). Yields trade dicts.
    Cost scaled by stop tightness: cost / sd_mult (a wider stop => smaller cost in R-units)."""
    out = []
    n = len(B)
    start = max(lb+1, 101)  # need lb window + 100-bar vr SMA + 60-bar ac
    for i in range(start, n-1):
        a = atrs[i]
        if a <= 0: continue
        hh = max(B[k].h for k in range(i-lb, i))
        ll = min(B[k].l for k in range(i-lb, i))
        c = B[i].c
        d = 0
        if c > hh: d = +1
        elif c < ll: d = -1
        if d == 0: continue
        ac = cs.autocorr(B, i, 60)
        if ac is None or ac < ac_thr: continue
        vr = cs.vol_ratio(atrs, i)
        if vr_min is not None and vr < vr_min: continue
        if vr_max is not None and vr >= vr_max: continue
        sd = sd_mult * a
        # cost in R: per-trade cost is fixed in price; in R-units it scales 1/stop.
        # KB convention: cost_for is already an R figure tuned at a reference stop; scale by tightness.
        r = wins(simulate(B, i, d, stop_dist=sd, target_dist=tgt_R*sd, cost=cost, maxbars=maxbars))
        out.append(dict(t=T[i], sym=None, dir=d, ac60=round(ac,4), vr=round(vr,3),
                        R=round(r,4), year=T[i].year, half=('H1' if T[i].year==2025 else 'H2')))
    return out

def half_key(t):
    # within-window holdout: TRAIN = 2025-06..2025-12 ; FWD = 2026-01..2026-06
    return 'TRAIN' if t.year == 2025 else 'FWD'

def stats(rows):
    if not rows: return (0, 0.0, 0.0)
    n=len(rows); m=sum(r['R'] for r in rows)/n; w=sum(1 for r in rows if r['R']>0)/n*100
    return n, round(m,4), round(w,1)

def build(grp, syms, tf, lb, ac_thr, sd_mult, tgt_R, maxbars, vr_min=None, vr_max=None):
    allrows=[]
    persym={}
    for s in syms:
        T,B = load_ltf(grp,s,tf)
        if len(B) < 300: continue
        atrs=[atr14(B,k) for k in range(len(B))]
        cost = w1.cost_for(s) / sd_mult     # scale cost by stop tightness
        rows = breakout_signals(T,B,atrs,lb,ac_thr,sd_mult,tgt_R,cost,maxbars,vr_min,vr_max)
        for r in rows: r['sym']=s
        allrows += rows
        persym[s]=rows
    return allrows, persym

def report_split(rows):
    tr=[r for r in rows if half_key(r['t'])=='TRAIN']
    fw=[r for r in rows if half_key(r['t'])=='FWD']
    return stats(tr), stats(fw)

# trades/yr: window is ~12.3 months (2025-06-01 .. 2026-06-10)
WINDOW_YEARS = (datetime(2026,6,10)-datetime(2025,6,1)).days/365.25
def per_yr(n): return round(n/WINDOW_YEARS,1)

# =====================================================================
# THE QUALITY INTRADAY ENTRY: vol-gated FVG-retest continuation (the
# train-validated metals/gold-sleeve entry) run on the H1 stream.
# This is NOT raw breakout (proven too noisy intraday, see KB3). It is the
# SAME entry+gate+geometry that is train-validated on 11yr H4 metals, just
# faster -> a frequency extension of an already-causal continuation edge.
# Leak-free: vol-gate + trend + FVG all use closed bars index<=i; ac60 on
# closed bars; geometry_lib.simulate labels forward only.
# =====================================================================
def fvg_retest_signals(T, B, atrs, cost, *, gate_k=1.2, trend_lb=30,
                       ac_thr=0.10, tgt_R=2.0, maxbars=320):
    n=len(B); out=[]
    for i in range(max(trend_lb+2,101), n-1):
        a=atrs[i]
        if a<=0: continue
        sma100=sum(atrs[i-99:i+1])/100
        if sma100<=0 or a < gate_k*sma100: continue       # vol-expansion gate
        diff=B[i].c-B[i-trend_lb].c
        tr = 1 if diff>1.0*a else (-1 if diff<-1.0*a else 0)
        if tr==0: continue
        ac=cs.autocorr(B,i,60)
        if ac_thr is not None and (ac is None or ac<ac_thr): continue
        b=B[i]; d=0; sd=None
        if tr==1:
            for k in range(i-2, max(i-9,60), -1):
                gap_top=B[k].l; gap_bot=B[k-2].h
                if gap_top-gap_bot < 0.10*a: continue
                if b.l<=gap_top and b.c>gap_bot and b.c>b.o:
                    sd=max((b.c-min(b.l,gap_bot))+0.10*a, 0.25*a); d=1; break
        else:
            for k in range(i-2, max(i-9,60), -1):
                gap_bot=B[k].h; gap_top=B[k-2].l
                if gap_top-gap_bot < 0.10*a: continue
                if b.h>=gap_bot and b.c<gap_top and b.c<b.o:
                    sd=max((max(b.h,gap_top)-b.c)+0.10*a, 0.25*a); d=-1; break
        if d==0 or sd is None: continue
        r=wins(simulate(B,i,d,stop_dist=sd,target_dist=tgt_R*sd,cost=cost,maxbars=maxbars))
        out.append(dict(t=T[i], sym=None, dir=d, ac60=round(ac,4) if ac is not None else None,
                        R=round(r,4), year=T[i].year))
    return out

def build_fvg(grp, syms, tf, *, gate_k=1.2, ac_thr=0.10, tgt_R=2.0, trend_lb=30):
    mb = 320 if tf=='H1' else 1280
    allrows=[]; persym={}
    for s in syms:
        T,B = load_ltf(grp,s,tf)
        if len(B) < 300: continue
        atrs=[atr14(B,k) for k in range(len(B))]
        cost = w1.cost_for(s)            # FVG stop is structural-tight; base cost (no widen)
        rows = fvg_retest_signals(T,B,atrs,cost, gate_k=gate_k, trend_lb=trend_lb,
                                  ac_thr=ac_thr, tgt_R=tgt_R, maxbars=mb)
        for r in rows: r['sym']=s
        allrows += rows; persym[s]=rows
    return allrows, persym
