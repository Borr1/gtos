"""
liquidity_map.py
================
LAYER: Liquidity map + engineered stop-hunt engine.

This is a REUSABLE engine (importable), not a single strategy. It models where
resting liquidity / stop clusters sit, then mines the forward odds of the
canonical stop-hunt mechanic: SWEEP + RECLAIM (price pierces a cluster intrabar,
then CLOSES back through it), conditioned on relative-volume / activity
confirmation and cluster TYPE, on H4 and M15.

DOCTRINE (hard rules, enforced in code):
  - NO LOOKAHEAD. Every cluster level and every feature at decision bar i is built
    ONLY from closed bars index<=i (clusters use index<i for swing pivots that need
    a right-shoulder; the sweep bar itself is index i and we ENTER at i+1 open).
  - Fills via tested geometry_lib.simulate ONLY (no hand-rolled stop/target/sign).
  - R-unit = structural stop distance (beyond the swept extreme).
  - Real per-asset cost via w1.cost_for(sym).
  - FORWARD HOLDOUT: TRAIN<=2024 vs FORWARD(2025-26), per-YEAR, per-INSTRUMENT,
    per-CLUSTER-TYPE. A cell is trusted only if it holds forward AND n>=MIN_TRUST_N.
  - NO AVERAGES AS VERDICTS. Map judges STATES (cells), not the system.
  - High odds must come from CONFLUENCE (cluster type + reclaim strength + activity
    + optionally HTF alignment); sample size always reported.

ENGINE SURFACE (import this):
  - LiquidityMap(times, bars).build()  -> per-bar arrays of cluster levels.
  - cluster_levels_at(i)               -> dict of {cluster_type: [levels]} usable at bar i.
  - sweep_signals(...)                 -> generator of leak-free sweep+reclaim signals.
  - run_cells(...)                     -> mine forward-validated cells across the universe.

CLUSTER TYPES modelled:
  pd   : prior-day high / low
  ps   : prior-session high / low (Asia 00-08, London 08-16, NY 16-24 UTC bar-open)
  asia : Asian-range edges (prior completed Asia session H/L) — a subset of ps but
         tracked separately because Asia-range sweeps are a distinct, well-known mechanic
  eq   : equal highs / lows (>=2 swing extremes within EQ_TOL*ATR of each other = a cluster)
  rn   : round numbers (psychological levels at instrument-appropriate increments)
  sw   : swing pivots (fractal high/low with k bars either side; a single resting level)
"""
from __future__ import annotations
import sys, os, json, math
from datetime import datetime
from collections import defaultdict

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
sys.path.insert(0, ROOT); sys.path.insert(0, EDGE)
from geometry_lib import Bar, atr14, simulate
import wave1_structure_setups_ict as w1
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL

# trust threshold for a forward cell (per task brief: n>=~40)
MIN_TRUST_N = 40

# ----------------------------------------------------------------------------
# M15 loader (union of deep backfill 2014-2025 + recent 2025-06..2026-06)
# H4 loader is w1.load (already a 2015-2022 + 2022-2026 union, deep-backfilled).
# ----------------------------------------------------------------------------
M15_BACKFILL = ROOT + "/data/mt5_research_exports/bridge_ftmo_fx_m15_backfill_2014_2025"
M15_RECENT   = ROOT + "/data/mt5_research_exports/bridge_ftmo_m15_20250601_20260610"

def _read_m15(path):
    import csv
    T, B = [], []
    if not os.path.exists(path): return T, B
    with open(path) as f:
        for row in csv.DictReader(f):
            try:
                t = datetime.strptime(row["time"], "%Y-%m-%d %H:%M:%S")
                b = Bar(float(row["open"]), float(row["high"]), float(row["low"]),
                        float(row["close"]), float(row.get("volume", 0) or 0))
                T.append(t); B.append(b)
            except Exception:
                continue
    return T, B

def load_m15(sym):
    """Union deep M15 backfill + recent M15 by timestamp (recent wins on overlap)."""
    T1, B1 = _read_m15(f"{M15_BACKFILL}/{sym}_M15.csv")
    T2, B2 = _read_m15(f"{M15_RECENT}/{sym}_M15.csv")
    merged = {}
    for t, b in zip(T1, B1): merged[t] = b
    for t, b in zip(T2, B2): merged[t] = b
    if not merged: return [], []
    items = sorted(merged.items(), key=lambda kv: kv[0])
    return [k for k, _ in items], [v for _, v in items]

M15_SYMBOLS = sorted(
    {fn[:-8] for fn in os.listdir(M15_BACKFILL) if fn.endswith("_M15.csv")} |
    {fn[:-8] for fn in os.listdir(M15_RECENT)   if fn.endswith("_M15.csv")}
) if (os.path.isdir(M15_BACKFILL) or os.path.isdir(M15_RECENT)) else []

def load(sym, tf="H4"):
    return load_m15(sym) if tf == "M15" else w1.load(sym)

def cost_for(sym):
    return w1.cost_for(sym)

# ----------------------------------------------------------------------------
# round-number increment per instrument (psychological levels).
# Chosen so a "round" level recurs roughly every ~0.5-3 ATR on H4 — i.e. a real
# magnet density, not too sparse / too dense. Derived from price magnitude + class.
# ----------------------------------------------------------------------------
def round_increment(sym, ref_price):
    cls = ASSET_CLASS_BY_SYMBOL.get(sym, "")
    p = abs(ref_price) if ref_price else 1.0
    if cls in ("fx", "jpy_fx"):
        # JPY pairs ~100+ -> 0.5; majors ~1.0-1.5 -> 0.0050 (50 pip); cross >2 -> 0.01
        if p > 50:   return 0.5
        if p > 3:    return 0.05
        return 0.0050
    if cls == "metals":
        if p > 1000: return 50.0     # XAUUSD
        if p > 100:  return 5.0      # XAUEUR/AUD-ish
        if p > 10:   return 1.0      # silver ~20-40
        return 0.5
    if cls == "crypto":
        if p > 10000: return 1000.0  # BTC
        if p > 1000:  return 100.0   # ETH
        if p > 100:   return 10.0
        if p > 10:    return 1.0
        return 0.1
    if cls == "energy":
        if p > 50:   return 5.0      # oil
        return 0.5
    if cls == "agri":
        if p > 100:  return 10.0
        return 1.0
    if cls == "index":
        if p > 10000: return 500.0   # NAS100
        if p > 3000:  return 100.0   # SPX500/GER40
        if p > 1000:  return 50.0
        return 10.0
    # generic fallback by magnitude
    mag = 10 ** math.floor(math.log10(p)) if p > 0 else 1.0
    return mag / 2.0

# ----------------------------------------------------------------------------
# The engine
# ----------------------------------------------------------------------------
class LiquidityMap:
    """Builds per-bar, leak-free cluster levels for one instrument's bar series.

    All level arrays are aligned to bar index i and contain ONLY information knowable
    at the CLOSE of bar i (or earlier). Usage at decision time should reference levels
    at i (the sweep bar) which are built from bars strictly before i for pd/ps/asia/eq/sw
    (prior completed blocks / pivots needing a right shoulder), and from i's own close
    only for the round-number reference price (price level identity, not future info).
    """
    def __init__(self, times, bars, sym, *,
                 swing_k=3, eq_tol=0.15, eq_lookback=120, eq_min_touch=2,
                 pivot_lookback=150, rn_window=3):
        self.T = times; self.B = bars; self.sym = sym
        self.n = len(bars)
        self.swing_k = swing_k
        self.eq_tol = eq_tol
        self.eq_lookback = eq_lookback
        self.eq_min_touch = eq_min_touch
        self.pivot_lookback = pivot_lookback
        self.rn_window = rn_window
        self.atrs = [atr14(bars, i) for i in range(self.n)]
        # filled by build()
        self.pdh = self.pdl = self.psh = self.psl = None
        self.asia_h = self.asia_l = None
        self.swing_hi = None   # list of (idx, price) confirmed swing highs, append-only
        self.swing_lo = None
        self._sw_hi_by_i = None  # per-bar: list of swing-high prices confirmed <= i
        self._sw_lo_by_i = None
        self._relvol = None; self._rangeact = None; self._has_vol = False
        self._sw_hi_conf = self._sw_hi_px = self._sw_lo_conf = self._sw_lo_px = None

    # ---- prior-day / prior-session (reuse w1.levels logic, robust) ----
    def _build_pd_ps(self):
        T, B, n = self.T, self.B, self.n
        pdh=[None]*n; pdl=[None]*n; psh=[None]*n; psl=[None]*n
        asia_h=[None]*n; asia_l=[None]*n
        cd=None; cdh=cdl=ldh=ldl=None
        csk=None; csh=csl=lsh=lsl=None
        # prior completed ASIA session specifically
        cur_asia_key=None; cur_asia_h=cur_asia_l=None; last_asia_h=last_asia_l=None
        for i in range(n):
            t=T[i]; b=B[i]; dk=t.date()
            if dk!=cd:
                if cd is not None: ldh,ldl=cdh,cdl
                cd=dk; cdh=b.h; cdl=b.l
            else:
                cdh=max(cdh,b.h); cdl=min(cdl,b.l)
            sid=w1.session_id(t); sk=(dk,sid)
            if sk!=csk:
                if csk is not None: lsh,lsl=csh,csl
                csk=sk; csh=b.h; csl=b.l
            else:
                csh=max(csh,b.h); csl=min(csl,b.l)
            # asia block (sid==0)
            if sid==0:
                ak=dk
                if ak!=cur_asia_key:
                    if cur_asia_key is not None: last_asia_h,last_asia_l=cur_asia_h,cur_asia_l
                    cur_asia_key=ak; cur_asia_h=b.h; cur_asia_l=b.l
                else:
                    cur_asia_h=max(cur_asia_h,b.h); cur_asia_l=min(cur_asia_l,b.l)
            else:
                # left the asia block; if we had one building, on next-asia-start it rolls.
                # We expose the last COMPLETED asia block. When in London/NY, the most recent
                # completed asia block is (cur_asia if it just ended) -> handle by: when sid!=0
                # and cur_asia_key is the same day, that day's asia is now complete.
                if cur_asia_key is not None and cur_asia_key==dk and last_asia_h is None:
                    # first completion of today's asia
                    pass
                if cur_asia_key is not None and (last_asia_h is None or cur_asia_key!=None):
                    # expose today's just-completed asia once we're past it
                    if cur_asia_key==dk:
                        last_asia_h,last_asia_l=cur_asia_h,cur_asia_l
            pdh[i]=ldh; pdl[i]=ldl; psh[i]=lsh; psl[i]=lsl
            asia_h[i]=last_asia_h; asia_l[i]=last_asia_l
        self.pdh,self.pdl,self.psh,self.psl=pdh,pdl,psh,psl
        self.asia_h,self.asia_l=asia_h,asia_l

    # ---- swing pivots (fractal, leak-free: confirmed only after k right bars) ----
    def _build_swings(self):
        B,n,k=self.B,self.n,self.swing_k
        sw_hi=[]; sw_lo=[]
        # a pivot at center c is confirmed at bar c+k (needs k right shoulders)
        for c in range(k, n-k):
            hh=B[c].h; ll=B[c].l
            is_hi=all(B[c].h>=B[c-j].h for j in range(1,k+1)) and all(B[c].h>=B[c+j].h for j in range(1,k+1))
            is_lo=all(B[c].l<=B[c-j].l for j in range(1,k+1)) and all(B[c].l<=B[c+j].l for j in range(1,k+1))
            conf=c+k  # index at which this pivot becomes knowable
            if is_hi: sw_hi.append((conf,hh))
            if is_lo: sw_lo.append((conf,ll))
        self.swing_hi=sw_hi; self.swing_lo=sw_lo

    def _swings_known_at(self, i):
        """Swing prices confirmed in (i-lookback, i], leak-free.
        Uses precomputed conf-index-sorted arrays + a cached window range to stay
        near-linear over a forward scan of i (the access pattern in sweep_signals)."""
        lb=self.pivot_lookback
        return (self._window(self._sw_hi_conf, self._sw_hi_px, i, lb),
                self._window(self._sw_lo_conf, self._sw_lo_px, i, lb))

    @staticmethod
    def _window(conf, px, i, lb):
        # conf is ascending; return px where (i-lb)<=conf<=i. Binary-search bounds.
        import bisect
        lo=bisect.bisect_left(conf, i-lb)
        hi=bisect.bisect_right(conf, i)
        return px[lo:hi]

    def build(self):
        self._build_pd_ps()
        self._build_swings()
        # sort pivots by confirmation index for fast windowed access
        self.swing_hi.sort(); self.swing_lo.sort()
        self._sw_hi_conf=[c for c,_ in self.swing_hi]; self._sw_hi_px=[p for _,p in self.swing_hi]
        self._sw_lo_conf=[c for c,_ in self.swing_lo]; self._sw_lo_px=[p for _,p in self.swing_lo]
        # precompute activity arrays (relvol if volume present, else range-activity)
        self._precompute_activity()
        return self

    def _precompute_activity(self, lb=20):
        n=self.n; B=self.B
        has_vol=any(B[k].v>0 for k in range(min(n,500)))
        self._relvol=[1.0]*n; self._rangeact=[1.0]*n
        # rolling sums
        vsum=0.0; rsum=0.0
        for i in range(n):
            if i>=lb:
                if has_vol:
                    vsum=sum(B[k].v for k in range(i-lb,i)) if i==lb else vsum-B[i-lb-1].v+B[i-1].v
                    self._relvol[i]=(B[i].v/(vsum/lb)) if vsum>0 else 1.0
                rsum=sum(B[k].h-B[k].l for k in range(i-lb,i)) if i==lb else rsum-(B[i-lb-1].h-B[i-lb-1].l)+(B[i-1].h-B[i-1].l)
                self._rangeact[i]=((B[i].h-B[i].l)/(rsum/lb)) if rsum>0 else 1.0
        self._has_vol=has_vol

    # ---- equal-highs / equal-lows clusters at bar i (from confirmed swings) ----
    def _equal_clusters(self, i):
        a=self.atrs[i]
        if a<=0: return [],[]
        hi,lo=self._swings_known_at(i)
        tol=self.eq_tol*a
        def cluster(levels):
            levels=sorted(levels)
            out=[]; used=[False]*len(levels)
            for j in range(len(levels)):
                if used[j]: continue
                grp=[levels[j]]; used[j]=True
                for kk in range(j+1,len(levels)):
                    if not used[kk] and abs(levels[kk]-levels[j])<=tol:
                        grp.append(levels[kk]); used[kk]=True
                if len(grp)>=self.eq_min_touch:
                    out.append(sum(grp)/len(grp))
            return out
        return cluster(hi),cluster(lo)

    # ---- round-number levels straddling current price ----
    def _round_levels(self, i):
        b=self.B[i]; inc=round_increment(self.sym, b.c)
        if inc<=0: return [],[]
        base=math.floor(b.c/inc)*inc
        levels=[base+inc*d for d in range(-self.rn_window, self.rn_window+1)]
        # round numbers above and below current close
        rn_hi=[x for x in levels if x>=b.c]
        rn_lo=[x for x in levels if x<b.c]
        return rn_hi,rn_lo

    def cluster_levels_at(self, i):
        """Return {ctype: {'hi':[...],'lo':[...]}} usable at bar i (leak-free)."""
        eq_hi,eq_lo=self._equal_clusters(i)
        rn_hi,rn_lo=self._round_levels(i)
        sw_hi,sw_lo=self._swings_known_at(i)
        out={
            'pd':   {'hi':[self.pdh[i]] if self.pdh[i] is not None else [], 'lo':[self.pdl[i]] if self.pdl[i] is not None else []},
            'ps':   {'hi':[self.psh[i]] if self.psh[i] is not None else [], 'lo':[self.psl[i]] if self.psl[i] is not None else []},
            'asia': {'hi':[self.asia_h[i]] if self.asia_h[i] is not None else [], 'lo':[self.asia_l[i]] if self.asia_l[i] is not None else []},
            'eq':   {'hi':eq_hi, 'lo':eq_lo},
            'rn':   {'hi':rn_hi, 'lo':rn_lo},
            'sw':   {'hi':sw_hi, 'lo':sw_lo},
        }
        return out

    # ---- relative-volume / activity at bar i (leak-free, precomputed) ----
    def relvol(self, i, lb=20):
        """Volume relative to trailing avg; falls back to range-activity if no volume."""
        if self._relvol is None: self._precompute_activity()
        return self._relvol[i] if self._has_vol else self._rangeact[i]

    def range_activity(self, i, lb=20):
        """Bar range / avg range over lookback — a volume-free 'activity' proxy."""
        if self._rangeact is None: self._precompute_activity()
        return self._rangeact[i]


# ----------------------------------------------------------------------------
# SWEEP + RECLAIM signal generator (the stop-hunt mechanic), leak-free.
# Mechanic: at bar i, price PIERCES a cluster level beyond it (takes liquidity),
# then CLOSES back through it (reclaim). ENTER at NEXT bar open (i+1) in the
# reclaim direction. Stop just beyond the swept wick extreme. Target opposing
# cluster or fixed R.
# ----------------------------------------------------------------------------
def sweep_signals(lm: LiquidityMap, *, ctypes=('pd','ps','asia','eq','rn','sw'),
                  sweep_min=0.05, reclaim_min=0.10, stop_buf=0.05, atr_stop_floor=0.20,
                  target_mode='fixedR', target_R=2.0, min_RR=1.0,
                  activity_min=0.0, use_relvol=True):
    """
    Yields dicts (one per detected sweep+reclaim entry) with full state for cell mining.
    sweep_min / reclaim_min in ATR units. activity_min: minimum relvol/activity to fire.
    A SINGLE bar can sweep multiple cluster types; we emit one signal per (ctype, side)
    that qualifies so per-cluster-type odds are clean.
    """
    B=lm.B; T=lm.T; n=lm.n; sym=lm.sym; cost=cost_for(sym)
    for i in range(60, n-2):
        a=lm.atrs[i]
        if a<=0: continue
        b=B[i]; nb=B[i+1]; entry=nb.o
        act=(lm.relvol(i) if use_relvol else lm.range_activity(i))
        if act<activity_min: continue
        cl=lm.cluster_levels_at(i)
        for ct in ctypes:
            # --- sweep a LOW cluster (price dips below, closes back above) -> long ---
            for lvl in cl[ct]['lo']:
                if lvl is None: continue
                if (lvl-b.l)>=sweep_min*a and b.c>lvl and (b.c-lvl)>=reclaim_min*a:
                    stop_dist=max((entry-b.l)+stop_buf*a, atr_stop_floor*a)
                    if target_mode=='opposing':
                        # nearest opposing-side cluster of SAME type above entry
                        ups=[x for x in cl[ct]['hi'] if x is not None and x>entry]
                        td=(min(ups)-entry) if ups else None
                        if td is None or td<min_RR*stop_dist: td=target_R*stop_dist
                    else:
                        td=target_R*stop_dist
                    if td>=min_RR*stop_dist:
                        r=simulate(B,i+1,+1,stop_dist=stop_dist,target_dist=td,cost=cost)
                        yield dict(sym=sym, year=T[i+1].year, cls=ASSET_CLASS_BY_SYMBOL.get(sym),
                                   ct=ct, side='long', i=i+1, R=r, act=round(act,3),
                                   reclaim=round((b.c-lvl)/a,3), sweep=round((lvl-b.l)/a,3),
                                   stop_dist=stop_dist)
            # --- sweep a HIGH cluster (price pops above, closes back below) -> short ---
            for lvl in cl[ct]['hi']:
                if lvl is None: continue
                if (b.h-lvl)>=sweep_min*a and b.c<lvl and (lvl-b.c)>=reclaim_min*a:
                    stop_dist=max((b.h-entry)+stop_buf*a, atr_stop_floor*a)
                    if target_mode=='opposing':
                        dns=[x for x in cl[ct]['lo'] if x is not None and x<entry]
                        td=(entry-max(dns)) if dns else None
                        if td is None or td<min_RR*stop_dist: td=target_R*stop_dist
                    else:
                        td=target_R*stop_dist
                    if td>=min_RR*stop_dist:
                        r=simulate(B,i+1,-1,stop_dist=stop_dist,target_dist=td,cost=cost)
                        yield dict(sym=sym, year=T[i+1].year, cls=ASSET_CLASS_BY_SYMBOL.get(sym),
                                   ct=ct, side='short', i=i+1, R=r, act=round(act,3),
                                   reclaim=round((lvl-b.c)/a,3), sweep=round((b.h-lvl)/a,3),
                                   stop_dist=stop_dist)


# ----------------------------------------------------------------------------
# cell mining / reporting helpers
# ----------------------------------------------------------------------------
def stats(rs):
    rs=list(rs)
    if not rs: return dict(n=0, mean_R=0.0, win=0.0, sum_R=0.0)
    n=len(rs); s=sum(rs); w=sum(1 for r in rs if r>0)
    return dict(n=n, mean_R=round(s/n,4), win=round(100*w/n,1), sum_R=round(s,1))

def split_tf(recs):
    """recs: list of dicts with 'year' and 'R'. -> (train_stats, fwd_stats)."""
    tr=[r['R'] for r in recs if r['year']<=2024]
    fw=[r['R'] for r in recs if r['year']>=2025]
    return stats(tr), stats(fw)

def per_year(recs):
    by=defaultdict(list)
    for r in recs: by[r['year']].append(r['R'])
    return {y:stats(by[y]) for y in sorted(by)}

def forward_validated(recs, min_n=MIN_TRUST_N, min_fwd_R=0.0):
    """A cell is forward-validated if FWD n>=min_n AND FWD mean_R>min_fwd_R AND
    majority of forward years positive."""
    tr,fw=split_tf(recs)
    if fw['n']<min_n: return False
    if fw['mean_R']<=min_fwd_R: return False
    py=per_year(recs); fy=[y for y in py if y>=2025]
    if not fy: return False
    pos=sum(1 for y in fy if py[y]['mean_R']>0)
    return pos>=math.ceil(len(fy)/2)


def load_for_tf(sym, tf):
    return load(sym, tf)


# module-level cache of built LiquidityMaps so multi-config sweeps reuse the heavy build
_LM_CACHE={}

def get_map(sym, tf, build_kwargs=None):
    key=(sym, tf, tuple(sorted((build_kwargs or {}).items())))
    if key not in _LM_CACHE:
        try:
            T,B=load_for_tf(sym, tf)
        except Exception:
            _LM_CACHE[key]=None; return None
        if len(B)<300:
            _LM_CACHE[key]=None; return None
        _LM_CACHE[key]=LiquidityMap(T,B,sym,**(build_kwargs or {})).build()
    return _LM_CACHE[key]


def run_cells(tf="H4", symbols=None, *, gen_kwargs=None, build_kwargs=None,
              ctypes=('pd','ps','asia','eq','rn','sw')):
    """Mine every signal across the universe on one timeframe; return the raw
    per-signal list. Reuses cached LiquidityMap builds across calls (configs)."""
    gen_kwargs=dict(gen_kwargs or {})
    gen_kwargs.setdefault('ctypes', ctypes)
    if symbols is None:
        symbols = M15_SYMBOLS if tf=="M15" else w1.SYMBOLS
    allrecs=[]
    for sym in symbols:
        lm=get_map(sym, tf, build_kwargs)
        if lm is None: continue
        for sig in sweep_signals(lm, **gen_kwargs):
            allrecs.append(sig)
    return allrecs
