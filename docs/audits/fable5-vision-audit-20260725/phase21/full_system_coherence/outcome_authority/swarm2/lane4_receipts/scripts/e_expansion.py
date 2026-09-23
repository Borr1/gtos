"""LANE 4 (D/E/F): symbol-expansion pricing, ATR-repeg sizing test, live sizing variance."""
import gzip, json, numpy as np, pandas as pd, sys
from pathlib import Path
REPO = Path("/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725")
OUT = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/lane4"); sys.path.insert(0,str(REPO))
rng = np.random.default_rng(20260812)
res = {}

# ---------- 1. armed-sleeve per-symbol economics on the archive ----------
rows = json.load(gzip.open(REPO/"docs/audits/fable5-vision-audit-20260725/phase20/forward/receipts/R1_ESTATE_ROWS_V2.json.gz","rt"))
df = pd.DataFrame(rows); df['entry']=pd.to_datetime(df.entry_utc,utc=True,format='mixed')
df['day']=df.entry.dt.strftime('%Y-%m-%d'); df['r']=pd.to_numeric(df.r_new_mid,errors='coerce')
df=df[df.r.notna()]
fwd = df[df.entry>='2025-01-01']; fwd_m=(fwd.entry.max()-fwd.entry.min()).days/30.4369
ARMED=['crypto','energy_agri','sub_xvol_pullback']
from src.components.ultimate_book.sleeves.registry import BUILT, CANDIDATE_BUILT, MARKET_EXPANSION_BUILT, active_specs
SPECS = {s.tag:s for s in active_specs(None, include_candidate_book=True, include_market_expansion_book=True,
          market_expansion_sleeves=list(MARKET_EXPANSION_BUILT))}
res['registry'] = {'specs':len(SPECS),'slots_spec_x_symbol':int(sum(len(s.on_surface) for s in SPECS.values())),
  'union_symbols':len({y for s in SPECS.values() for y in s.on_surface}),
  'timeframes':{str(k):int(v) for k,v in pd.Series([s.timeframe for s in SPECS.values()]).value_counts().items()},
  'armed_slots':int(sum(len(SPECS[t].on_surface) for t in ARMED if t in SPECS))}
per_sym={}
for t in ARMED:
    d = df[df.sleeve==t]; f = fwd[fwd.sleeve==t]
    spec = SPECS.get(t)
    g = d.groupby('symbol')['r'].agg(['size','mean','sum'])
    per_sym[t] = {'declared_on_surface': list(spec.on_surface) if spec else None,
      'declared_n': len(spec.on_surface) if spec else None,
      'archive_symbols_traded': sorted(d.symbol.unique().tolist()),
      'archive_n_symbols': int(d.symbol.nunique()),
      'per_symbol_all_years': json.loads(g.round(4).to_json(orient='index')),
      'forward_trades': int(len(f)), 'forward_symbols': sorted(f.symbol.unique().tolist()),
      'forward_mean_r': round(float(f.r.mean()),5) if len(f) else None,
      'forward_trades_per_month': round(len(f)/fwd_m,3)}
res['armed_sleeve_symbol_surface'] = per_sym

# ---------- 2. unarmed sleeves ranked, with t and multiplicity context ----------
g = fwd.groupby('sleeve')['r'].agg(n='size', mean='mean', sd='std', total='sum')
g['t']=g['mean']/(g['sd']/np.sqrt(g['n'])); g['r_per_month']=g['total']/fwd_m
g['trades_per_month']=g['n']/fwd_m; g['armed']=g.index.isin(ARMED)
g['spec_tf']=[SPECS[s].timeframe if s in SPECS else None for s in g.index]
g['in_registry']=[s in SPECS for s in g.index]
res['sleeves_forward_ranked'] = json.loads(g.sort_values('r_per_month',ascending=False).round(5).to_json(orient='index'))

# ---------- 3. (E) sizing: does re-pegging the stop from ATR14 to ATR50 add breadth? ----------
pop = pd.read_parquet("/tmp/lane_i/pop.parquet")
for c in ('month','symbol','lifecycle_label_status','trading_day'): pop[c]=pop[c].astype(str)
pop['net']=pd.to_numeric(pop.terminal_net_r,errors='coerce').fillna(0.0)
fil = pop[pop.eligible & pop.lifecycle_label_status.str.startswith('RESOLVED_FILLED_')].copy()
ops = fil.sort_values('label_span_start_utc').groupby(['trading_day','symbol'],observed=True,as_index=False).first()
ops['ratio']=ops.atr14_over_atr50.clip(0.3,3.0)
# A stop pegged to ATR50 instead of ATR14 rescales the R-unit by (ATR14/ATR50).
ops['r_atr50'] = ops.net*ops.ratio
def dayport(col, w=None):
    d = ops.copy()
    d['w'] = 1.0 if w is None else d[w]
    out=[]
    for day,dd in d.groupby('trading_day',observed=True):
        ww=dd.w.to_numpy(dtype=float)
        if ww.sum()<=0: continue
        out.append(float(np.sum(ww/ww.sum()*dd[col].to_numpy())))
    a=np.asarray(out)
    return {'days':int(len(a)),'mean':round(float(a.mean()),5),'sd':round(float(a.std(ddof=1)),5),
            't':round(float(a.mean()/(a.std(ddof=1)/np.sqrt(len(a)))),4)}
res['sizing_repeg'] = {
  'per_bet_sd_R_atr14_stop': round(float(ops.net.std(ddof=1)),5),
  'per_bet_sd_R_atr50_stop': round(float(ops.r_atr50.std(ddof=1)),5),
  'per_bet_mean_atr14': round(float(ops.net.mean()),5),
  'per_bet_mean_atr50': round(float(ops.r_atr50.mean()),5),
  'day_portfolio_atr14': dayport('net'),
  'day_portfolio_atr50': dayport('r_atr50'),
  'sd_ratio_atr50_over_atr14': round(float(ops.r_atr50.std(ddof=1)/ops.net.std(ddof=1)),4),
}
t14=res['sizing_repeg']['day_portfolio_atr14']['t']; t50=res['sizing_repeg']['day_portfolio_atr50']['t']
res['sizing_repeg']['breadth_equivalent_multiple'] = round((t50/t14)**2,4)
# dispersion predictability check: R^2 of |net R| on the pre-decision features that Lane I named
from numpy.linalg import lstsq
X = np.column_stack([np.ones(len(ops)), ops.atr14_over_atr50.fillna(1.0), ops.trigger_bar_range_atr.fillna(0),
                     ops.compression_ratio_prior_bar.fillna(1.0), ops.risk_over_atr.fillna(1.0)])
y = ops.net.abs().to_numpy()
b,_,_,_ = lstsq(X,y,rcond=None); yh=X@b
res['sizing_repeg']['R2_predicting_absR_from_4_predecision_features'] = round(float(1-((y-yh)**2).sum()/((y-y.mean())**2).sum()),5)

# ---------- 4. live sizing variance (Kelly-lite bins + cluster split) ----------
from src.components.ultimate_book.admission import GovernorLimits, DEFAULT_LIMITS
res['live_sizing'] = {
  'kelly_lite_bins_source':'admission.py — half-Kelly conviction bins ((1,1,0.748),(2,3,0.991),(4,99,1.241))',
  'multiplier_values':[0.748,0.991,1.241],
  'gross_open_risk_cap_pct': DEFAULT_LIMITS.gross_open_risk_cap_pct,
  'soft_daily_stop_pct': DEFAULT_LIMITS.soft_daily_stop_pct,
  'hard_daily_limit_pct': DEFAULT_LIMITS.hard_daily_limit_pct,
  'max_dd_limit_pct': DEFAULT_LIMITS.max_dd_limit_pct,
  'derisk_start_dd_pct': DEFAULT_LIMITS.derisk_start_dd_pct,
  'derisk_mode_default': DEFAULT_LIMITS.derisk_mode}
mults=np.array([0.748,0.991,1.241])
for lab, w in (('uniform_over_3_bins', np.array([1/3,1/3,1/3])),
               ('vps_observed_6to7_firing', np.array([0.1,0.2,0.7]))):
    m=float((mults*w).sum()); v=float((mults**2*w).sum()-m**2); cv=np.sqrt(v)/m
    res['live_sizing'][f'CV_size_{lab}']=round(float(cv),5)
    res['live_sizing'][f'variance_inflation_{lab}']=round(float(1+cv**2),5)
    res['live_sizing'][f'time_to_answer_penalty_{lab}']=round(float(1+cv**2),5)
# gross risk cap: how many concurrent 2.0% units fit
for dial in (0.75,1.1968,2.0):
    res['live_sizing'][f'max_concurrent_units_at_dial_{dial}pct'] = round(0.04/(dial/100.0),2)
(OUT/"E_EXPANSION_AND_SIZING_V1.json").write_text(json.dumps(res,indent=1,default=str))
print(json.dumps(res['registry'],indent=1))
print(json.dumps(res['armed_sleeve_symbol_surface'],indent=1)[:3000])
print("=== SIZING REPEG ==="); print(json.dumps(res['sizing_repeg'],indent=1))
print("=== LIVE SIZING ==="); print(json.dumps(res['live_sizing'],indent=1))
