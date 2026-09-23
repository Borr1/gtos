"""LANE 4 (B): raw and effective breadth on the candidate funnel surface.
Effective breadth via the day-portfolio variance ratio:
  Var(sum of K same-day bets) / (K * sigma^2) = 1 + (K-1)*rhobar  -> solve rhobar
Read-only on /tmp/lane_i/pop.parquet. Writes only to lane4 scratch.
"""
import json, numpy as np, pandas as pd
from pathlib import Path
OUT = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/lane4"); OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(20260812)

df = pd.read_parquet("/tmp/lane_i/pop.parquet")
df['month'] = df['month'].astype(str)
df['trading_day'] = df['trading_day'].astype(str)
df['symbol'] = df['symbol'].astype(str)
df['lifecycle_label_status'] = df['lifecycle_label_status'].astype(str)
df['origin_family'] = df['origin_family'].astype(str)
df['proposed_order_type'] = df['proposed_order_type'].astype(str)
df['utc_session'] = df['utc_session'].astype(str)

res = {}
res['population'] = {
  'rows': int(len(df)),
  'eligible': int(df.eligible.sum()),
  'resolved_eligible': int((df.eligible & df.resolved).sum()),
  'months': sorted(df.month.unique().tolist()),
  'trading_days': int(df.trading_day.nunique()),
  'decision_windows': int(df.decision_window_id.nunique()),
  'symbols': int(df.symbol.nunique()),
  'families': int(df.origin_family.nunique()),
}
# eligible + FILLED rows (an actual outcome you could have taken)
el = df[df.eligible].copy()
el['filled'] = el.lifecycle_label_status.str.startswith('RESOLVED_FILLED_')
el['no_fill'] = el.lifecycle_label_status.eq('RESOLVED_NO_FILL')
el['censored'] = el.lifecycle_label_status.str.startswith('CENSORED_')
res['eligible_mix'] = {
  'filled': int(el.filled.sum()), 'resolved_no_fill': int(el.no_fill.sum()),
  'censored': int(el.censored.sum()),
  'windows_eligible': int(el.decision_window_id.nunique()),
  'days_eligible': int(el.trading_day.nunique()),
}
# per-month raw breadth counts at several unit definitions
def per_month(g):
    e = g[g.eligible]
    f = e[e.lifecycle_label_status.str.startswith('RESOLVED_FILLED_')]
    return pd.Series({
      'eligible_rows': len(e),
      'filled_rows': len(f),
      'windows': e.decision_window_id.nunique(),
      'days': e.trading_day.nunique(),
      'sym_days': e.groupby(['trading_day','symbol'], observed=True).ngroups,
      'sym_day_filled': f.groupby(['trading_day','symbol'], observed=True).ngroups,
      'sym_fam_days': e.groupby(['trading_day','symbol','origin_family'], observed=True).ngroups,
      'sym_windows': e.groupby(['decision_window_id','symbol'], observed=True).ngroups,
    })
res['raw_breadth_per_month'] = df.groupby('month').apply(per_month, include_groups=False).to_dict('index')

# ---- effective breadth: day-portfolio variance ratio on FILLED eligible rows
fil = el[el.filled].copy()
fil['net'] = pd.to_numeric(fil.terminal_net_r, errors='coerce').fillna(0.0)
sig2 = float(fil.net.var(ddof=1)); mu = float(fil.net.mean())
res['per_bet'] = {'n': int(len(fil)), 'mean_net_r': mu, 'sd_net_r': float(np.sqrt(sig2))}

def var_ratio(grpcols, label, sub=None):
    d = fil if sub is None else sub
    g = d.groupby(grpcols, observed=True)['net'].agg(['sum','count'])
    g = g[g['count'] >= 1]
    K = g['count'].to_numpy().astype(float); S = g['sum'].to_numpy()
    # demean per-bet contribution: var of (S - K*mu)
    resid = S - K*mu
    varS = float(np.sum(resid**2)/ (len(resid)-1))
    Kbar = float(K.mean()); Kmean2 = float((K**2).mean())
    # E[Var(S)] under indep = E[K]*sig2 ; under equicorr = sig2*(E[K] + (E[K^2]-E[K])*rho)
    denom_ind = Kbar*sig2
    rho = (varS/sig2 - Kbar) / max(Kmean2 - Kbar, 1e-12)
    neff = Kbar/(1.0 + (Kbar-1.0)*max(rho, 0.0)) if Kbar > 1 else Kbar
    # bootstrap CI on rho over groups
    idx = np.arange(len(K)); boots=[]
    for _ in range(400):
        b = rng.choice(idx, size=len(idx), replace=True)
        v = float(np.sum(resid[b]**2)/(len(b)-1)); kb = float(K[b].mean()); k2 = float((K[b]**2).mean())
        boots.append((v/sig2 - kb)/max(k2-kb,1e-12))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {'label': label, 'groups': int(len(K)), 'K_mean': Kbar, 'K_median': float(np.median(K)),
            'var_sum_observed': varS, 'var_sum_if_independent': denom_ind,
            'variance_inflation': varS/denom_ind if denom_ind else None,
            'rho_bar': float(rho), 'rho_ci95': [float(lo), float(hi)],
            'N_eff_per_group': float(neff), 'N_raw_per_group': Kbar}

res['effective_breadth'] = {
  'all_same_day': var_ratio(['trading_day'], 'all filled eligible in one trading day'),
  'same_window': var_ratio(['decision_window_id'], 'all filled eligible in one decision window'),
  'same_day_symbol': var_ratio(['trading_day','symbol'], 'same day + same symbol'),
  'same_day_family': var_ratio(['trading_day','origin_family'], 'same day + same family'),
  'same_day_one_per_symbol': None,
}
# one-per-symbol-per-day: pick first occurrence per (day,symbol), then day portfolio
ops = fil.sort_values('label_span_start_utc').groupby(['trading_day','symbol'], observed=True, as_index=False).first()
ops['net'] = pd.to_numeric(ops.terminal_net_r, errors='coerce').fillna(0.0)
g = ops.groupby('trading_day')['net'].agg(['sum','count'])
K = g['count'].to_numpy().astype(float); S=g['sum'].to_numpy()
mu2 = float(ops.net.mean()); s2 = float(ops.net.var(ddof=1))
resid = S - K*mu2; varS = float(np.sum(resid**2)/(len(resid)-1))
Kbar=float(K.mean()); Kmean2=float((K**2).mean())
rho = (varS/s2 - Kbar)/max(Kmean2-Kbar,1e-12)
res['effective_breadth']['same_day_one_per_symbol'] = {
  'label':'one candidate per symbol per day, day portfolio','groups':int(len(K)),
  'K_mean':Kbar,'K_median':float(np.median(K)),'var_sum_observed':varS,
  'var_sum_if_independent':Kbar*s2,'variance_inflation':varS/(Kbar*s2),
  'rho_bar':float(rho),'N_eff_per_group':float(Kbar/(1+(Kbar-1)*max(rho,0.0))),'N_raw_per_group':Kbar,
  'per_bet_sd': float(np.sqrt(s2)), 'per_bet_mean': mu2}

# pairwise correlation by symbol pair, on day-level symbol mean net R
sd = fil.groupby(['trading_day','symbol'], observed=True)['net'].mean().unstack()
sd = sd.loc[:, sd.notna().sum() >= 40]
C = sd.corr(min_periods=30)
vals = C.to_numpy()[np.triu_indices(len(C), k=1)]
vals = vals[np.isfinite(vals)]
res['symbol_pair_correlation'] = {
  'symbols': int(len(C)), 'pairs': int(len(vals)),
  'mean': float(np.mean(vals)), 'median': float(np.median(vals)),
  'p05': float(np.percentile(vals,5)), 'p95': float(np.percentile(vals,95)),
  'frac_above_0p2': float(np.mean(vals>0.2)),
  'top10': sorted(
     [(C.index[i], C.columns[j], float(C.iat[i,j]))
      for i in range(len(C)) for j in range(i+1,len(C)) if np.isfinite(C.iat[i,j])],
     key=lambda t:-t[2])[:10]}
# family pair correlation
fd = fil.groupby(['trading_day','origin_family'], observed=True)['net'].mean().unstack()
Cf = fd.corr(min_periods=30)
fv = Cf.to_numpy()[np.triu_indices(len(Cf),k=1)]; fv=fv[np.isfinite(fv)]
res['family_pair_correlation'] = {'families': int(len(Cf)), 'mean': float(np.mean(fv)),
  'median': float(np.median(fv)), 'p05': float(np.percentile(fv,5)), 'p95': float(np.percentile(fv,95))}

(OUT/"B_BREADTH_CEILING_V1.json").write_text(json.dumps(res, indent=1, default=str))
print(json.dumps({k:v for k,v in res.items() if k in ('population','eligible_mix','per_bet')}, indent=1))
print(json.dumps(res['effective_breadth'], indent=1, default=str))
print(json.dumps(res['symbol_pair_correlation'], indent=1, default=str))
