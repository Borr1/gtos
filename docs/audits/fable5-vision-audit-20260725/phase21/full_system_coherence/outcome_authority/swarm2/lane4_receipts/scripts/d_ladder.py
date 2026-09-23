"""LANE 4 (C/E): detectability ladder + sizing-as-breadth-substitute."""
import gzip, json, numpy as np, pandas as pd
from pathlib import Path
from scipy import stats
REPO = Path("/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725")
OUT = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/lane4")
rng = np.random.default_rng(20260812)
Z = stats.norm.ppf(0.975) + stats.norm.ppf(0.80)   # 1.959964 + 0.841621
K = Z**2
res = {'design': {'alpha_two_sided':0.05,'power':0.80,'z_sum':float(Z),'k_z2':float(K),
                  'n_required_formula':'n = k * (sigma/mu)^2','note':'IID bets; correlated bets enter via effective breadth'}}

# ---- anchors (all measured elsewhere, cited in the report) ----
anchors = {
 'live_book_FTMO_three_sleeve_CURRENT_SURFACE': dict(mu=0.3298, sd=1.1785, bets_per_month=3.833,
    unit='R per book-day', src='THREE_SLEEVE_BOOK_RESTATEMENT_V1.md §3.2 (n=69 book-days, t=2.325)'),
 'live_book_FN_three_sleeve_FN_TRADEABLE': dict(mu=0.4026, sd=1.0071, bets_per_month=2.938,
    unit='R per book-day', src='THREE_SLEEVE_BOOK_RESTATEMENT_V1.md §3.2 (n=47 book-days, t=2.740)'),
 'archive_armed3_forward_capped': dict(mu=1.02672, sd=2.20513, bets_per_month=4.637,
    unit='R per trade', src='LANE 4 C_SLEEVE_SURFACE_V1.json forward_2025plus L0'),
 'funnel_frozen_rule_within_window_edge': dict(mu=0.00298, sd=1.1388, bets_per_month=1847.4,
    unit='R per trade (within-window lift)', src='LANE_I §3.1 + LANE 4 B (windows/month)'),
 'funnel_required_breakeven_edge': dict(mu=0.09, sd=1.1388, bets_per_month=1847.4,
    unit='R per trade', src='LANE_I §7.1 required edge; funnel breadth from LANE 4 B'),
 'funnel_negative_cost_heuristic': dict(mu=0.00650, sd=1.1388, bets_per_month=1847.4,
    unit='R per trade', src='LANE_I §3.1 F8'),
}
def months_to_answer(mu, sd, bpm):
    n = K*(sd/mu)**2
    return {'n_bets_required': n, 'months': n/bpm, 'years': n/bpm/12}
for name, a in anchors.items():
    r = months_to_answer(a['mu'], a['sd'], a['bets_per_month'])
    res.setdefault('anchors',{})[name] = {**a, **{k: (round(v,3) if v<1e6 else v) for k,v in r.items()}}

# ---- the ladder: months-to-answer as f(breadth multiple, edge dilution) ----
base = anchors['live_book_FTMO_three_sleeve_CURRENT_SURFACE']
lad = {}
for B in (1,2,3,5,10,17.4,25,50,100,1000):
    row = {}
    for k_dil in (1.0, 1.25, 1.5, 2.0, 3.0):
        mu = base['mu']/k_dil
        r = months_to_answer(mu, base['sd'], base['bets_per_month']*B)
        row[f'dilution_x{k_dil}'] = round(r['months'],3)
    lad[f'breadth_x{B}'] = {'bets_per_month': round(base['bets_per_month']*B,2), **row}
res['ladder_live_book'] = lad
# minimum detectable effect at 6 weeks / 3 months / 6 months as f(breadth)
mde = {}
for B in (1,2,3,5,10,17.4,25,50,100,1000):
    bpm = base['bets_per_month']*B
    row = {'bets_per_month': round(bpm,2)}
    for T,label in ((1.5,'6_weeks'),(3.0,'3_months'),(6.0,'6_months'),(12.0,'12_months')):
        row[f'mde_R_per_bet_{label}'] = round(base['sd']*np.sqrt(K/(bpm*T)),4)
        row[f'mde_as_frac_of_measured_edge_{label}'] = round(base['sd']*np.sqrt(K/(bpm*T))/base['mu'],3)
    mde[f'breadth_x{B}'] = row
res['minimum_detectable_effect_live_book'] = mde
# same for the funnel, at its own breadth
fb = anchors['funnel_frozen_rule_within_window_edge']['bets_per_month']
res['minimum_detectable_effect_funnel'] = {
  f'{lab}': {'bets': round(fb*T,1), 'mde_R_per_trade': round(1.1388*np.sqrt(K/(fb*T)),5)}
  for T,lab in ((0.25,'1_week'),(0.75,'3_weeks'),(1.5,'6_weeks'),(3.0,'3_months'),(6.0,'6_months'))}

# ---- (E) sizing as a breadth substitute, on the funnel population ----
df = pd.read_parquet("/tmp/lane_i/pop.parquet")
for c in ('month','symbol','lifecycle_label_status','trading_day','origin_family','proposed_order_type'):
    df[c]=df[c].astype(str)
df['net']=pd.to_numeric(df.terminal_net_r,errors='coerce').fillna(0.0)
fil = df[df.eligible & df.lifecycle_label_status.str.startswith('RESOLVED_FILLED_')].copy()
fil['absr']=fil.net.abs()
# predictor of DISPERSION available pre-decision (LANE I F2/F6/§8): atr14_over_atr50 quintile within symbol
fil['q'] = fil.groupby('symbol', observed=True)['atr14_over_atr50'].transform(
    lambda s: pd.qcut(s, 5, labels=False, duplicates='drop'))
disp = fil.groupby('q')['absr'].mean()
sd_by_q = fil.groupby('q')['net'].std()
res['sizing'] = {'dispersion_by_atr_quintile': {int(k): float(v) for k,v in disp.items()},
                 'sd_net_r_by_atr_quintile': {int(k): float(v) for k,v in sd_by_q.items()}}
# day portfolios under three weighting schemes, on the one-per-symbol-per-day book
ops = fil.sort_values('label_span_start_utc').groupby(['trading_day','symbol'], observed=True, as_index=False).first()
ops['q']=ops['q'].fillna(2)
# scheme weights, normalised so each DAY deploys the same total risk (1 unit)
def day_stats(w_col):
    g = ops.groupby('trading_day', observed=True)
    out=[]
    for day, d in g:
        w = d[w_col].to_numpy(dtype=float)
        if w.sum()<=0: continue
        w = w/w.sum()
        out.append(float(np.sum(w*d.net.to_numpy())))
    a=np.asarray(out)
    return {'days':int(len(a)),'mean':float(a.mean()),'sd':float(a.std(ddof=1)),
            't':float(a.mean()/(a.std(ddof=1)/np.sqrt(len(a)))),
            'sharpe_per_day':float(a.mean()/a.std(ddof=1))}
ops['w_equal']=1.0
sdq = ops.groupby('q')['net'].transform('std')
ops['w_invvol']=1.0/sdq.replace(0,np.nan).fillna(sdq.mean())
ops['w_invatr']=1.0/ops.atr14_over_atr50.clip(lower=0.2)
res['sizing']['day_portfolio'] = {
  'equal_weight': day_stats('w_equal'),
  'inverse_predicted_dispersion': day_stats('w_invvol'),
  'inverse_atr_ratio': day_stats('w_invatr')}
# concentration: how much of the SD comes from the top-decile-|R| bets
ops_sorted = ops.reindex(ops.net.abs().sort_values(ascending=False).index)
n=len(ops_sorted); top=int(n*0.1)
res['sizing']['concentration'] = {
  'n': n, 'var_share_top_decile_by_absR': float((ops_sorted.net.iloc[:top]**2).sum()/(ops_sorted.net**2).sum()),
  'mean_share_top_decile': float(ops_sorted.net.iloc[:top].sum()/ops_sorted.net.sum()) if ops_sorted.net.sum() else None}
# n-bets-equivalent gain from re-weighting: t^2 ratio
eq=res['sizing']['day_portfolio']['equal_weight']['t']
for k in ('inverse_predicted_dispersion','inverse_atr_ratio'):
    tt=res['sizing']['day_portfolio'][k]['t']
    res['sizing']['day_portfolio'][k]['breadth_equivalent_multiple_vs_equal'] = round((tt/eq)**2,4) if eq else None
(OUT/"D_LADDER_AND_SIZING_V1.json").write_text(json.dumps(res, indent=1, default=str))
print(json.dumps(res['anchors'], indent=1))
print("=== LADDER (months to a 2-sided 80%-power answer, live book) ===")
print(json.dumps(res['ladder_live_book'], indent=1))
print("=== MDE funnel ==="); print(json.dumps(res['minimum_detectable_effect_funnel'], indent=1))
print("=== SIZING ==="); print(json.dumps(res['sizing'], indent=1))
