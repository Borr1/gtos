"""LIVE_EXPECTATIONS_compute.py — build the owner-facing live-expectations dossier for the
clean_3 deploy book. Net of realistic fills (KB3 per-sleeve erosion). Reuses the LOCKED W2 MC
engine for challenge economics; recomputes returns/dollars/frequency/duration directly from the
per-day R streams + trade ledgers.

Deploy book = clean_3 = W3 8-sleeve book + sub_xvol_pullback(0.45) + vp_euidx_pocgrav(0.30)
+ sub_mid_dn_revert(0.20). Confidence applied at the per-day-mean stage (matching the deploy
engine). Per-sleeve R erosion from EXEC_REALISM_COMBINED_RESULT.json applied to every trade.
"""
import sys, json, math, statistics, collections, pickle, datetime
from pathlib import Path
HERE = Path('/Users/borr/Documents/gtos/repo/ai-trading-agent/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10')
sys.path.insert(0, str(HERE)); sys.path.insert(0, '/Users/borr/Documents/gtos/repo/ai-trading-agent')
import INTEG_portfolio_build as I
import INTEG_portfolio_build_w2 as W2
import INTEG_portfolio_build_w3 as W3

TARGET=I.TARGET; MAXDD=I.MAXDD; DAILY=I.DAILY; BLOCK=I.BLOCK; N=I.N
mc_series = W2.mc_series

# ---------------------------------------------------------------- exec erosion (per-trade R) --
ER = json.load(open(HERE/'EXEC_REALISM_COMBINED_RESULT.json'))
EROSION = {}                      # per-sleeve per-trade R erosion (negative = worse)
for s in ER['per_sleeve']:
    EROSION[s['sleeve']] = s['erosion']
EROSION['fx_jpy'] = EROSION.get('fx_jpy_london', -0.048)   # ledger sleeve name
# new W5 sleeves: no direct M1 measure. Apply class proxies (conservative, honest):
#   sub_xvol_pullback / vp_euidx_pocgrav: H4 index/metals/energy geometry (wide stop) -> metals-class -0.010
#   sub_mid_dn_revert: substrate all-class incl crypto, mid-vol -> use crypto-ish -0.030 (conservative)
EROSION.setdefault('sub_xvol_pullback', -0.010)
EROSION.setdefault('vp_euidx_pocgrav',  -0.013)   # idx, like idxrev wide-stop class
EROSION.setdefault('sub_mid_dn_revert', -0.030)   # conservative substrate proxy
NEW_PROXY = {'sub_xvol_pullback','vp_euidx_pocgrav','sub_mid_dn_revert'}

# ---------------------------------------------------------------- load streams ----------------
w3 = pickle.load(open(HERE/'INTEG_W3_streams_cache.pkl','rb'))
new = pickle.load(open(HERE/'INTEG_W5_new_streams_cache.pkl','rb'))
CLEAN3_NEW = {'sub_xvol_pullback':0.45, 'vp_euidx_pocgrav':0.30, 'sub_mid_dn_revert':0.20}
BOOK_CONF = dict(W3.SLEEVE_CONF)
CONF = dict(BOOK_CONF); CONF.update(CLEAN3_NEW)
SLEEVES = list(w3.keys()) + list(CLEAN3_NEW.keys())

# per-sleeve net rows: apply intra_size (R_sized for W3) then per-trade R erosion.
def net_rows(name):
    if name in w3:
        rows = w3[name]
        out=[]
        for r in rows:
            isz = r.get('intra_size',1.0)
            base = r['R'] * isz                       # R_sized
            er = EROSION.get(name,0.0) * isz          # erosion scales with size too
            out.append(dict(date=r['date'], year=r['year'], sym=r['sym'], Rnet=base+er, Rraw=base))
        return out
    else:
        rows = new[name]
        er = EROSION.get(name,0.0)
        return [dict(date=r['date'], year=r['year'], sym=r['sym'], Rnet=r['R']+er, Rraw=r['R']) for r in rows]

NET = {s: net_rows(s) for s in SLEEVES}

# ---------------------------------------------------------------- daily matrix (conf-wtd) -----
# Per deploy engine: per-day sleeve value = mean(R over trades that day) * conf.
def sleeve_daily(name, use_net=True):
    by=collections.defaultdict(list)
    for r in NET[name]:
        by[r['date']].append(r['Rnet'] if use_net else r['Rraw'])
    return {d: (sum(v)/len(v))*CONF[name] for d,v in by.items()}

DSL = {s: sleeve_daily(s, True) for s in SLEEVES}
DSL_raw = {s: sleeve_daily(s, False) for s in SLEEVES}
all_days = sorted(set().union(*[set(DSL[s]) for s in SLEEVES]))
comb_net = [sum(DSL[s].get(d,0.0) for s in SLEEVES) for d in all_days]
comb_raw = [sum(DSL_raw[s].get(d,0.0) for s in SLEEVES) for d in all_days]

# ---------------------------------------------------------------- chronological equity sim -----
def equity_path(days, vals, risk):
    """Compounded daily equity over the ACTUAL chronological day sequence. Returns
    equity list, daily-return list, maxDD."""
    eq=1.0; peak=1.0; mdd=0.0; eqs=[]; rets=[]
    for v in vals:
        dp = v*risk
        eq*=(1+dp); rets.append(dp)
        peak=max(peak,eq); mdd=max(mdd,(peak-eq)/peak)
        eqs.append(eq)
    return eqs, rets, mdd

def year_of(d): return d.year

def per_year_returns(days, vals, risk):
    """Compounded account return WITHIN each calendar year (equity resets to 1.0 each Jan)."""
    by=collections.defaultdict(list)
    for d,v in zip(days,vals): by[d.year].append(v)
    out={}
    for y in sorted(by):
        eq=1.0
        for v in by[y]: eq*=(1+v*risk)
        out[y]=eq-1.0
    return out

def monthly_returns(days, vals, risk):
    by=collections.defaultdict(list)
    for d,v in zip(days,vals): by[(d.year,d.month)].append(v)
    out={}
    for k in sorted(by):
        eq=1.0
        for v in by[k]: eq*=(1+v*risk)
        out[k]=eq-1.0
    return out

RES={}
RES['book'] = 'clean_3'
RES['n_days_all']=len(all_days);
fwd_days=[d for d in all_days if d.year>=2025]
RES['n_days_fwd']=len(fwd_days)
RES['date_range_all']=[str(all_days[0]), str(all_days[-1])]
RES['date_range_fwd']=[str(fwd_days[0]), str(fwd_days[-1])]
RES['combined_daily_mean_unitR_net']=round(statistics.fmean(comb_net),5)
RES['combined_daily_std_unitR_net']=round(statistics.pstdev(comb_net),5)
fwd_vals=[v for d,v in zip(all_days,comb_net) if d.year>=2025]
RES['combined_daily_mean_unitR_fwd_net']=round(statistics.fmean(fwd_vals),5)
RES['win_days_pct']=round(100*sum(1 for v in comb_net if v>0)/len(comb_net),1)
RES['erosion_applied']=EROSION

# trading-days-per-year (for annualization sanity) — count distinct active book-days/yr
days_by_year=collections.Counter(d.year for d in all_days)
RES['active_book_days_per_year']=dict(days_by_year)

# ---- RETURNS at 0.5% and 0.75% ----
RES['returns']={}
for risk in (0.005,0.0075):
    key=f"{risk*100:.2f}%"
    eqs,rets,mdd = equity_path(all_days, comb_net, risk)
    # full-history compounded total (across the whole timeline, equity NOT reset)
    total_compound = eqs[-1]-1.0
    # CAGR over the span
    span_days=(all_days[-1]-all_days[0]).days
    years=span_days/365.25
    cagr=(eqs[-1])**(1/years)-1 if years>0 else 0.0
    py = per_year_returns(all_days, comb_net, risk)
    mo = monthly_returns(all_days, comb_net, risk)
    mo_vals=list(mo.values())
    # forward window compounded (continuous, equity not reset across 2025->2026)
    eqs_f,rets_f,mdd_f = equity_path(fwd_days, fwd_vals, risk)
    fwd_total=eqs_f[-1]-1.0
    py_fwd={y:py[y] for y in py if y>=2025}
    # daily distribution
    pos=sum(1 for r in rets if r>0);
    RES['returns'][key]=dict(
        per_year_pct={str(y):round(100*v,2) for y,v in py.items()},
        full_history_total_compound_pct=round(100*total_compound,1),
        full_history_cagr_pct=round(100*cagr,2),
        forward_2025_pct=round(100*py.get(2025,0.0),2),
        forward_2026_pct=round(100*py.get(2026,0.0),2),
        forward_window_total_compound_pct=round(100*fwd_total,2),
        mean_monthly_pct=round(100*statistics.fmean(mo_vals),3),
        median_monthly_pct=round(100*statistics.median(mo_vals),3),
        n_months=len(mo_vals),
        daily_mean_pct=round(100*statistics.fmean(rets),4),
        daily_std_pct=round(100*statistics.pstdev(rets),4),
        pct_positive_days=round(100*pos/len(rets),1),
        best_day_pct=round(100*max(rets),3),
        worst_day_pct=round(100*min(rets),3),
        maxDD_pct=round(100*mdd,2),
        maxDD_fwd_pct=round(100*mdd_f,2),
    )
    # forward-only daily dist
    posf=sum(1 for r in rets_f if r>0)
    RES['returns'][key]['fwd_daily_mean_pct']=round(100*statistics.fmean(rets_f),4)
    RES['returns'][key]['fwd_daily_std_pct']=round(100*statistics.pstdev(rets_f),4)
    RES['returns'][key]['fwd_pct_positive_days']=round(100*posf/len(rets_f),1)
    RES['returns'][key]['fwd_best_day_pct']=round(100*max(rets_f),3)
    RES['returns'][key]['fwd_worst_day_pct']=round(100*min(rets_f),3)

# ---- DOLLARS per $100k ----
ACC=100000.0
RES['dollars_per_100k']={}
for risk in (0.005,0.0075):
    key=f"{risk*100:.2f}%"
    r=RES['returns'][key]
    # forward monthly $ (mean monthly % applied to fresh 100k each month, simple expectation)
    exp_month_pct = r['mean_monthly_pct']/100.0
    fwd_total_pct = r['forward_window_total_compound_pct']/100.0
    fwd_span_days=(fwd_days[-1]-fwd_days[0]).days
    fwd_years=fwd_span_days/365.25
    # forward annualized
    fwd_ann = (1+fwd_total_pct)**(1/fwd_years)-1 if fwd_years>0 else 0.0
    # days to +8% target (median from MC fwd) handled separately; here expected path
    RES['dollars_per_100k'][key]=dict(
        expected_dollar_per_month_fwd=round(ACC*exp_month_pct,0),
        fwd_window_total_dollar=round(ACC*fwd_total_pct,0),
        fwd_annualized_pct=round(100*fwd_ann,2),
        fwd_annualized_dollar=round(ACC*fwd_ann,0),
        dollar_to_pass_8pct=round(ACC*0.08,0),
        funded_dollar_per_month_after_pass_80split=round(ACC*exp_month_pct*0.80,0),
    )

# ---- FREQUENCY per sleeve and book ----
def sleeve_freq(name):
    rows=NET[name]
    n_all=len(rows); n_fwd=sum(1 for r in rows if r['year']>=2025)
    yrs=sorted(set(r['year'] for r in rows))
    # forward span in years for /yr (2025-06-ish to 2026-06): use distinct fwd dates span
    fwd_dates=sorted(set(r['date'] for r in rows if r['year']>=2025))
    all_dates=sorted(set(r['date'] for r in rows))
    fwd_span = ((fwd_dates[-1]-fwd_dates[0]).days/365.25) if len(fwd_dates)>1 else (1.0 if n_fwd else 0)
    all_span = ((all_dates[-1]-all_dates[0]).days/365.25) if len(all_dates)>1 else 1.0
    per_yr_fwd = n_fwd/fwd_span if fwd_span>0 else 0
    per_yr_all = n_all/all_span if all_span>0 else 0
    return dict(n_all=n_all, n_fwd=n_fwd, trades_per_year_fwd=round(per_yr_fwd,1),
                trades_per_year_all=round(per_yr_all,1), years_present=[min(yrs),max(yrs)])

RES['frequency']={'per_sleeve':{}}
tot_fwd=0.0; tot_all=0.0
for s in SLEEVES:
    f=sleeve_freq(s); RES['frequency']['per_sleeve'][s]=f
    tot_fwd+=f['trades_per_year_fwd']; tot_all+=f['trades_per_year_all']
RES['frequency']['book_trades_per_year_fwd']=round(tot_fwd,1)
RES['frequency']['book_trades_per_year_all']=round(tot_all,1)
RES['frequency']['book_trades_per_week_fwd']=round(tot_fwd/52.0,1)
RES['frequency']['book_trades_per_day_fwd']=round(tot_fwd/252.0,2)
for s in SLEEVES:
    RES['frequency']['per_sleeve'][s]['trades_per_week_fwd']=round(RES['frequency']['per_sleeve'][s]['trades_per_year_fwd']/52.0,2)
    RES['frequency']['per_sleeve'][s]['trades_per_day_fwd']=round(RES['frequency']['per_sleeve'][s]['trades_per_year_fwd']/252.0,3)

# ---- BREAKDOWN: per-sleeve contribution to return + frequency; per-asset-class ----
# contribution = sum over all days of conf-wtd net daily value (net erosion)
contrib={s:sum(DSL[s].values()) for s in SLEEVES}
contrib_fwd={s:sum(v for d,v in DSL[s].items() if d.year>=2025) for s in SLEEVES}
tot_c=sum(contrib.values()); tot_cf=sum(contrib_fwd.values())
RES['breakdown']={'per_sleeve':{}}
for s in sorted(SLEEVES,key=lambda x:-contrib[x]):
    RES['breakdown']['per_sleeve'][s]=dict(
        contrib_sum_net=round(contrib[s],3),
        contrib_share_pct=round(100*contrib[s]/tot_c,1) if tot_c else 0,
        contrib_fwd_sum_net=round(contrib_fwd[s],3),
        contrib_fwd_share_pct=round(100*contrib_fwd[s]/tot_cf,1) if tot_cf else 0,
        conf=CONF[s],
        trades_per_year_fwd=RES['frequency']['per_sleeve'][s]['trades_per_year_fwd'],
        freq_share_pct=round(100*RES['frequency']['per_sleeve'][s]['trades_per_year_fwd']/tot_fwd,1),
    )

# asset-class mapping
CLASS={
    'metals_core':'metals','metals_softband':'metals','metals_ob_micro':'metals',
    'crypto':'crypto','energy_agri':'energy_agri','idxrev':'index','fx_jpy':'fx',
    'fx_jpy_ny':'fx','sub_xvol_pullback':'multi(metals/energy/index/fx)',
    'vp_euidx_pocgrav':'index','sub_mid_dn_revert':'multi(all-class)',
}
cls_c=collections.defaultdict(float); cls_cf=collections.defaultdict(float); cls_f=collections.defaultdict(float)
for s in SLEEVES:
    cls_c[CLASS[s]]+=contrib[s]; cls_cf[CLASS[s]]+=contrib_fwd[s]
    cls_f[CLASS[s]]+=RES['frequency']['per_sleeve'][s]['trades_per_year_fwd']
RES['breakdown']['per_asset_class']={}
for c in sorted(cls_c, key=lambda x:-cls_c[x]):
    RES['breakdown']['per_asset_class'][c]=dict(
        contrib_share_pct=round(100*cls_c[c]/tot_c,1) if tot_c else 0,
        contrib_fwd_share_pct=round(100*cls_cf[c]/tot_cf,1) if tot_cf else 0,
        trades_per_year_fwd=round(cls_f[c],1),
        freq_share_pct=round(100*cls_f[c]/tot_fwd,1),
    )

# ---- HOLD-TIME / DURATION per sleeve ----
# Each sleeve's timeframe + outcome geometry caps. We derive hold-time from the per-trade
# outcome where the ledgers carry it (bars1R as a hold proxy when no exit_index), else use
# the geometry: timeframe bar-hours x typical-bars-to-exit. We compute a defensible median/
# p25/p75 in HOURS using sleeve TF + a bars-held estimate.
TF_HOURS={'metals_core':4,'metals_softband':4,'metals_ob_micro':4,'crypto':4,'energy_agri':4,
          'idxrev':4,'fx_jpy':0.25,'fx_jpy_ny':0.25,'sub_xvol_pullback':4,
          'vp_euidx_pocgrav':4,'sub_mid_dn_revert':4}
# cascade sleeves fill/exit on LTF; their realized hold is in LTF bars. We use the modeled
# H4 outcome horizon for the H4-native sleeves and report the cascade caveat.
MAXBARS={'metals_core':80,'metals_softband':80,'metals_ob_micro':80,'crypto':80,'energy_agri':80,
         'idxrev':60,'fx_jpy':48,'fx_jpy_ny':48,'sub_xvol_pullback':80,
         'vp_euidx_pocgrav':60,'sub_mid_dn_revert':80}

# Recompute exit_index distribution for the substrate/vp sleeves + idxrev via simulate_detail
# (they are cheap fixed-geometry single-stream sims). For cascade/EXEC_COMBO sleeves we read
# bars1R-class proxies from the D4 ledger + apply the geometry caps.
from geometry_lib import simulate_detail, atr14
import wave1_structure_setups_ict as w1
import compounding_sleeve as cs
import substrate as sub
import SUBSTRATE_corrcheck as SC

def pctiles(xs):
    xs=sorted(xs); n=len(xs)
    if n==0: return (None,None,None)
    def q(p):
        k=p*(n-1); lo=int(math.floor(k)); hi=int(math.ceil(k))
        if lo==hi: return xs[lo]
        return xs[lo]+(xs[hi]-xs[lo])*(k-lo)
    return (q(0.25), q(0.5), q(0.75))

HOLD={}

# idxrev: H4, recompute exit_index distribution directly (fixed geometry).
def idxrev_holds():
    LB=16;STOP_ATR=1.5;TGT_R=0.75;MAXB=60; bars=[]
    for sym in I.IDX_POCKET:
        try: T,B=w1.load(sym)
        except Exception: continue
        if len(B)<150: continue
        atrs=[atr14(B,k) for k in range(len(B))]; cost=w1.cost_for(sym)
        for i in range(120,len(B)):
            a=atrs[i]
            if a<=0: continue
            rhi=max(B[k].h for k in range(i-LB,i)); rlo=min(B[k].l for k in range(i-LB,i))
            b=B[i]; d=0
            if b.h>rhi and b.c<rhi: d=-1
            elif b.l<rlo and b.c>rlo: d=1
            if d==0: continue
            sd=STOP_ATR*a; rcost=cost/STOP_ATR
            _,ej=simulate_detail(B,i,d,stop_dist=sd,target_dist=TGT_R*sd,maxbars=MAXB,cost=rcost)
            bars.append(ej-i)
    return bars

# substrate cells: recompute exit_index via sub.outcome path (simulate_detail inside). We
# re-walk with SC.materialize_cell-equivalent but capture exit bars. Cheap enough for the 3 cells.
def substrate_holds(cell, symbols=None):
    # mimic SC.materialize_cell but capture (R, exit_idx-entry_idx)
    import KB5_fold_new_sleeves as FOLD
    parts=cell.split('|'); geomtok=parts[0]  # g1.0_3.0
    g=geomtok[1:].split('_'); stop_atr=float(g[0]); target_R=float(g[1])
    conds={}
    direction=None; depth=None
    for p in parts[1:]:
        if p.startswith('dir='): direction=int(p.split('=')[1])
        elif p.startswith('depth'): depth=int(p[5:])
        elif '=' in p:
            k,v=p.split('='); conds[k]=v
    syms=symbols if symbols is not None else [s for s in w1.SYMBOLS]
    bars=[]
    for s in syms:
        built=sub.build_states(s)
        if built is None: continue
        T,B,A,states=built; cost=w1.cost_for(s); n=len(B)
        for i in range(sub.WARMUP, n - sub.MAXBARS - 1):
            st=states[i]
            if st is None: continue
            co=sub.cell_coords(st)
            if not all(co.get(k)==v for k,v in conds.items()): continue
            a=A[i]
            if a<=0: continue
            d=direction; sd=stop_atr*a; td=target_R*sd; sc=cost/stop_atr
            _,ej=simulate_detail(B,i,d,stop_dist=sd,target_dist=td,maxbars=sub.MAXBARS,cost=sc)
            bars.append(ej-i)
    return bars

# vp_euidx: H4, recompute exit bars
def vp_holds():
    import VP_lib as vp_mod  # may not exist; fallback to KB5 internal
    bars=[]
    return bars

print("computing idxrev holds...", flush=True)
idx_b=idxrev_holds()
HOLD['idxrev']=dict(tf_hours=4, n=len(idx_b), bars_p25_p50_p75=pctiles(idx_b))

print("computing substrate holds (xvol)...", flush=True)
xvol_syms=[s for s in w1.SYMBOLS if s not in __import__('KB5_fold_new_sleeves').DROP_XVOL]
xb=substrate_holds("g1.0_3.0|dir=1|depth4|vol=xhi|persist=rand|trend=up|mtf=conflict", symbols=xvol_syms)
HOLD['sub_xvol_pullback']=dict(tf_hours=4, n=len(xb), bars_p25_p50_p75=pctiles(xb))

print("computing substrate holds (mid_dn)...", flush=True)
mb=substrate_holds("g1.0_3.0|dir=1|depth7|vol=mid|trend=dn|mtf=neutral|rngpos=mid|comp=norm|persist=revert|session=ny")
HOLD['sub_mid_dn_revert']=dict(tf_hours=4, n=len(mb), bars_p25_p50_p75=pctiles(mb))

# vp_euidx: recompute via KB5 _vp_pocgrav with exit capture
print("computing vp holds...", flush=True)
def vp_pocgrav_holds():
    import KB5_fold_new_sleeves as FOLD
    from geometry_lib import simulate_detail
    import VP_confluence as vc, volume_profile as vp
    bars=[]
    for sym in ["GER40","UK100"]:
        T,B=w1.load(sym)
        if len(B)<200: continue
        cost=w1.cost_for(sym); n=len(B); atrs=[atr14(B,i) for i in range(n)]
        profs,days=vp.daily_profiles(sym, bin_atr_frac=vc.BIN_FRAC)
        if not days: continue
        fday=days[0]
        for i in range(101,n-1):
            a=atrs[i]
            if a<=0: continue
            t=T[i]
            if t.date()<=fday: continue
            dp=vp.prior_profile_at(profs,days,t)
            if dp is None: continue
            price=B[i].c; stt=vp.nearest_node_state(dp,price,a)
            if stt is None: continue
            vr=cs.vol_ratio(atrs,i); dpoc=stt["d_poc_atr"]
            if abs(dpoc)<2.0 or stt["in_va"]: continue
            if vr<1.2: continue
            d=-1 if dpoc>0 else 1; stop_dist=1.0*a; target_dist=abs(price-dp.poc)
            if target_dist<0.8*stop_dist: continue
            _,ej=simulate_detail(B,i,d,stop_dist=stop_dist,target_dist=target_dist,maxbars=60,cost=cost)
            bars.append(ej-i)
    return bars
try:
    vb=vp_pocgrav_holds()
    HOLD['vp_euidx_pocgrav']=dict(tf_hours=4, n=len(vb), bars_p25_p50_p75=pctiles(vb))
except Exception as e:
    HOLD['vp_euidx_pocgrav']=dict(tf_hours=4, n=0, bars_p25_p50_p75=(None,None,None), err=str(e))

# H4 EV-carrier sleeves (metals_core, crypto, energy_agri, softband, ob_micro): these use
# cascade/EXEC_COMBO exits on LTF. The realized hold in wall-clock is bounded by the H4 horizon
# (80 H4 bars = 320h) but typically exits far earlier via scale/target. We use the D4 ledger's
# bars1R (bars to first 1R) as a LOWER-bound hold proxy and the maxbars cap as upper bound,
# plus the metals win-runner reason distribution. Report as H4-bar-based estimate with caveat.
import json as _j
d4_bars=collections.defaultdict(list)
for line in open(HERE/'D4_COMBINED_TRADE_LEDGER.jsonl'):
    line=line.strip()
    if not line: continue
    r=_j.loads(line)
    if r.get('bars1R') is not None and r.get('sleeve') in ('metals_core','metals_softband','metals_ob_micro','energy_agri'):
        d4_bars[r['sleeve']].append(r['bars1R'])
for s in ('metals_core','metals_softband','metals_ob_micro','energy_agri'):
    if d4_bars[s]:
        HOLD[s]=dict(tf_hours=4, n=len(d4_bars[s]), bars1R_p25_p50_p75=pctiles(d4_bars[s]),
                     note='bars1R = H4 bars to first 1R (hold lower-bound; runner/cascade exit later up to 80 H4 bars)')

# crypto: use TW cascade — base is H4 80-bar; estimate from base R sims is heavy. Use H4 caps.
HOLD['crypto']=dict(tf_hours=4, n=104, note='H4 entry, H1->M15 cascade fill + target4/runner exit; modeled horizon <=80 H4 bars (320h); typical scale/target exit earlier')

# fx_jpy / fx_jpy_ny: M15, recompute exit bars directly (cheap)
print("computing fx holds...", flush=True)
def fxlon_holds():
    import collections as _c
    bars=[]
    for sym in ('GBPJPY','USDJPY'):
        T,B,A=I._load_fx_m15(sym);
        if len(B)<100: continue
        cost=w1.cost_for(sym); byday=_c.defaultdict(list)
        for i,t in enumerate(T): byday[t.date()].append(i)
        for day,idxs in sorted(byday.items()):
            lon=[i for i in idxs if T[i].hour>=8]
            if len(lon)<6: continue
            i0=lon[0]
            if i0<20: continue
            iw=lon[3]; a=A[iw]
            if a<=0: continue
            d=1 if B[iw].c>B[i0].o else -1
            _,ej=simulate_detail(B,iw,d,stop_dist=1.0*a,target_dist=2.5*a,maxbars=48,cost=cost)
            bars.append(ej-iw)
    return bars
try:
    fb=fxlon_holds()
    HOLD['fx_jpy']=dict(tf_hours=0.25, n=len(fb), bars_p25_p50_p75=pctiles(fb))
except Exception as e:
    HOLD['fx_jpy']=dict(tf_hours=0.25, n=0, err=str(e))
# fx_jpy_ny shares M15 + same target/stop geometry -> use london dist as proxy
HOLD['fx_jpy_ny']=dict(tf_hours=0.25, note='M15, 1ATR stop / 2.5ATR target / maxbars48 — same geometry as fx_jpy (London); hold distribution ~ fx_jpy')

# convert bar-based holds to hours/days summary
def to_hours(rec, sleeve):
    tfh=rec.get('tf_hours',4)
    key = 'bars_p25_p50_p75' if 'bars_p25_p50_p75' in rec else ('bars1R_p25_p50_p75' if 'bars1R_p25_p50_p75' in rec else None)
    if key and rec[key][0] is not None:
        p25,p50,p75=rec[key]
        rec['hold_hours_p25_p50_p75']=[round(p25*tfh,2),round(p50*tfh,2),round(p75*tfh,2)]
        rec['hold_days_p25_p50_p75']=[round(p25*tfh/24.0,3),round(p50*tfh/24.0,3),round(p75*tfh/24.0,3)]
    return rec
for s in HOLD: to_hours(HOLD[s], s)
RES['hold_time']=HOLD

# ---- CHALLENGE ECONOMICS: reuse the locked deploy JSON + recompute on net streams ----
DEP=json.load(open(HERE/'INTEG_W5_CLEAN3_DEPLOY.json'))
RES['challenge_locked_volmatched_all']=DEP['mc_volmatched_all']
RES['challenge_locked_volmatched_stress']=DEP['mc_volmatched_stress']
RES['challenge_locked_fwd']=DEP['mc_fwd']
RES['challenge_locked_raw_all']=DEP['mc_raw_all']
RES['vol_scale']=DEP['vol_scale']
RES['daily_breach_locked']=DEP['daily_breach']
RES['two_account_locked']=DEP['two_account']

# Recompute net-of-erosion MC on OUR net combined series (cross-check vs locked raw-EV engine)
print("recomputing net MC (this takes a moment)...", flush=True)
sd_net=statistics.pstdev(comb_net)
# vol_scale to book std: use locked book std basis. We just report net-stream MC at nominal risk.
def grid_net(series, stress=False, scale=1.0):
    s=[(v*1.5 if v<0 else v) for v in series] if stress else series
    return {f"{r*100:.2f}%": mc_series(s, r*scale, seed_base=(999 if stress else 1)) for r in (0.005,0.0075,0.01)}
RES['challenge_net_all']=grid_net(comb_net)
RES['challenge_net_stress']=grid_net(comb_net, stress=True)
RES['challenge_net_fwd']={f"{r*100:.2f}%": mc_series(fwd_vals, r, seed_base=777) for r in (0.005,0.0075,0.01)}
# daily breach on net series
RES['daily_breach_net']={}
for r in (0.005,0.0075,0.01):
    RES['daily_breach_net'][f"{r*100:.2f}%"]=dict(
        worst_day_pct=round(min(comb_net)*r*100,3),
        breach_pct=round(100*sum(1 for v in comb_net if v*r<=-DAILY)/len(comb_net),3))

(HERE/'LIVE_EXPECTATIONS_RESULT.json').write_text(json.dumps(RES, indent=1, default=str))
print("\n=== DONE -> LIVE_EXPECTATIONS_RESULT.json ===")
print(f"days all={RES['n_days_all']} fwd={RES['n_days_fwd']} | daily mean net={RES['combined_daily_mean_unitR_net']} std={RES['combined_daily_std_unitR_net']} winday%={RES['win_days_pct']}")
for k in ('0.50%','0.75%'):
    r=RES['returns'][k]
    print(f"[{k}] fwd2025={r['forward_2025_pct']}% fwd2026={r['forward_2026_pct']}% fwd_total={r['forward_window_total_compound_pct']}% mean_mo={r['mean_monthly_pct']}% maxDD={r['maxDD_pct']}%")
    print(f"      per-year: {r['per_year_pct']}")
print(f"book tr/yr fwd={RES['frequency']['book_trades_per_year_fwd']} /wk={RES['frequency']['book_trades_per_week_fwd']} /day={RES['frequency']['book_trades_per_day_fwd']}")
print(f"net MC all 1%={RES['challenge_net_all']['1.00%']['p_pass']:.4f} | locked vm 1%={DEP['mc_volmatched_all']['1.00%']['p_pass']}")
