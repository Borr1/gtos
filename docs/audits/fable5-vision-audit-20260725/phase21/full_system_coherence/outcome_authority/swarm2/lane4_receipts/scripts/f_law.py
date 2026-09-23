"""LANE 4 (D/F): the breadth-vs-edge law, cost break-evens, concurrency and prop-rule checks."""
import gzip, json, numpy as np, pandas as pd, sys
from pathlib import Path
from scipy import stats
REPO = Path("/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725")
OUT = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/lane4"); sys.path.insert(0,str(REPO))
rng=np.random.default_rng(20260812); res={}

rows=json.load(gzip.open(REPO/"docs/audits/fable5-vision-audit-20260725/phase20/forward/receipts/R1_ESTATE_ROWS_V2.json.gz","rt"))
df=pd.DataFrame(rows); df['entry']=pd.to_datetime(df.entry_utc,utc=True,format='mixed')
df['day']=df.entry.dt.strftime('%Y-%m-%d'); df['r']=pd.to_numeric(df.r_new_mid,errors='coerce')
df=df[df.r.notna()]
fwd=df[df.entry>='2025-01-01']; fwd_m=(fwd.entry.max()-fwd.entry.min()).days/30.4369
ARMED=['crypto','energy_agri','sub_xvol_pullback']
res['note_on_instrument']=("r_new_mid is the r1 quote-side-corrected walker at the MID spread band. It charges "
 "SPREAD only. It does NOT charge commission or swap. Every per-trade figure below is therefore GROSS of "
 "commission+swap and must be haircut by the sleeve's own broker-true residual before any economic claim.")

# ---- 1. the breadth-vs-edge law across sleeves (forward window) ----
g=fwd.groupby('sleeve')['r'].agg(n='size',mean='mean',sd='std',total='sum')
g=g[g.n>=20].copy()
g['trades_per_month']=g.n/fwd_m; g['r_per_month']=g.total/fwd_m
g['t']=g['mean']/(g['sd']/np.sqrt(g.n))
x=np.log(g.trades_per_month.to_numpy()); y=np.log(np.abs(g['mean'].to_numpy())+1e-6)
sl,ic,rr,pv,se=stats.linregress(x,y)
res['breadth_edge_law']={'sleeves_n_ge_20':int(len(g)),
 'log_meanR_on_log_tradesPerMonth':{'slope':round(float(sl),4),'slope_se':round(float(se),4),
   'r':round(float(rr),4),'p':float(pv),'interpretation':
   'slope = -1 means edge-per-trade falls exactly as fast as trade count rises -> R/month is breadth-invariant'},
 }
x2=np.log(g.trades_per_month.to_numpy()); y2=g.r_per_month.to_numpy()
sl2,ic2,rr2,pv2,se2=stats.linregress(x2,y2)
res['breadth_edge_law']['RperMonth_on_log_tradesPerMonth']={'slope':round(float(sl2),4),'se':round(float(se2),4),
  'r':round(float(rr2),4),'p':float(pv2)}
res['breadth_edge_law']['spearman_tradesPerMonth_vs_RperMonth']=[round(float(v),4) for v in stats.spearmanr(g.trades_per_month,g.r_per_month)]
res['breadth_edge_law']['spearman_tradesPerMonth_vs_meanR']=[round(float(v),4) for v in stats.spearmanr(g.trades_per_month,g['mean'])]
res['breadth_edge_law']['table']=json.loads(g.sort_values('trades_per_month',ascending=False).round(5).to_json(orient='index'))

# ---- 2. break-even cost haircut per sleeve, and the broker-true residual from SURVIVOR_BOOK ----
sb=json.load(open(REPO/"research/operations/w7_recost_2026_07_27/SURVIVOR_BOOK_V1.json"))
ftmo=sb['accounts']['FTMO']['sleeves']
res['broker_true_cost_from_survivor_book']={k:{'n':v['n'],'gross_r':v['gross_r'],
  'true_cost_ex_swap_r':v['true_cost_ex_swap_r'],'swap_r_per_night':v['swap_r_per_night'],
  'net_n0':v['net_r']['n0'],'net_n_horizon_mean':v['net_r']['n_horizon_mean'],
  'horizon_mean_nights':v['horizon_mean_nights'],'survivor_tier':v.get('survivor_tier')} for k,v in ftmo.items()}
be={}
for s in g.index:
    m=float(g.loc[s,'mean']); sd=float(g.loc[s,'sd']); n=int(g.loc[s,'n'])
    be[s]={'mean_r_spread_only':round(m,5),'trades_per_month':round(float(g.loc[s,'trades_per_month']),3),
           'break_even_extra_cost_r':round(m,5),
           'break_even_extra_cost_lower_ci95':round(float(m-1.96*sd/np.sqrt(n)),5),
           'survives_a_0p02R_commission': bool(m>0.02),
           'survives_a_0p05R_commission': bool(m>0.05),
           'survives_estate_median_true_cost_0p1124R': bool(m>0.1124)}
res['break_even_cost_haircut']=be

# ---- 3. concurrency vs the 4% gross open-risk cap ----
from src.components.ultimate_book.admission import DEFAULT_LIMITS
def concurrency(d, sleeves):
    x=d[d.sleeve.isin(sleeves)]
    c=x.groupby('day').size()
    return {'days':int(len(c)),'mean_per_day':round(float(c.mean()),3),'p95_per_day':float(np.percentile(c,95)),
            'max_per_day':int(c.max()),'frac_days_ge_2':round(float((c>=2).mean()),4),
            'frac_days_ge_3':round(float((c>=3).mean()),4),'frac_days_ge_5':round(float((c>=5).mean()),4)}
ALL=sorted(df.sleeve.unique().tolist())
res['concurrency']={'armed3_forward':concurrency(fwd,ARMED),'all29_forward':concurrency(fwd,ALL),
  'gross_open_risk_cap_pct':DEFAULT_LIMITS.gross_open_risk_cap_pct,
  'max_concurrent_units_by_dial':{f'{d}%':round(0.04/(d/100),2) for d in (0.5,0.75,1.0,1.1968,1.5,2.0)},
  'note':'same-day count is an UPPER bound on concurrency: positions may close before the next fires'}

# ---- 4. prop-rule arithmetic for the ladder rungs ----
# worst single day exposure: N concurrent units each risking `dial`% -> worst-case daily loss = N*dial
FTMO_DAILY=0.05; FTMO_MAXDD_STATIC=0.10
rungs={}
for label,(bets_month, dial, conc) in {
  'R0_today_3_sleeves_2pct':(3.833,2.0,2),
  'R1_cluster_cap_off':(4.05,2.0,2),
  'R2_add_sub_mid_dn_revert_back':(5.83,2.0,2),
  'R3_incubation_6_extra_sleeves_at_0p25pct':(3.833+60.0,2.0,2),
  'R4_dial_1pct_double_concurrency':(7.67,1.0,4),
  'R5_dial_0p5pct_quadruple':(15.33,0.5,8),
}.items():
    worst_day=conc*dial/100.0
    rungs[label]={'bets_per_month':bets_month,'dial_pct':dial,'max_concurrent_units':conc,
      'worst_case_daily_loss_pct':round(worst_day*100,3),
      'breaches_5pct_daily': bool(worst_day>FTMO_DAILY),
      'headroom_vs_5pct_daily_x':round(FTMO_DAILY/worst_day,2),
      'gross_cap_satisfied': bool(conc*dial/100.0<=DEFAULT_LIMITS.gross_open_risk_cap_pct+1e-9)}
res['prop_rule_check']=rungs

# ---- 5. detectability at incubation size ----
Z=(stats.norm.ppf(0.975)+stats.norm.ppf(0.80))**2
def months(mu,sd,bpm): return Z*(sd/mu)**2/bpm
inc={}
for s in ['asian_fade','idxrev','fx_jpy_ny','vss_fxcross_london_up_low','vol_compression','sub_mid_dn_revert','metals_core']:
    if s not in g.index: continue
    mu=float(g.loc[s,'mean']); sd=float(g.loc[s,'sd']); bpm=float(g.loc[s,'trades_per_month'])
    inc[s]={'mean_r_spread_only':round(mu,5),'sd':round(sd,4),'trades_per_month':round(bpm,2),
            'months_to_own_answer_at_measured_edge':round(months(mu,sd,bpm),2) if mu!=0 else None,
            'months_to_detect_a_0p05R_edge':round(months(0.05,sd,bpm),2),
            'months_to_detect_a_0p10R_edge':round(months(0.10,sd,bpm),2)}
res['incubation_detectability']=inc
# the armed book, and the pooled incubation basket
pool=['asian_fade','idxrev','fx_jpy_ny','vss_fxcross_london_up_low']
sub=fwd[fwd.sleeve.isin(pool)]
res['incubation_basket']={'sleeves':pool,'trades':int(len(sub)),'trades_per_month':round(len(sub)/fwd_m,2),
  'mean_r_spread_only':round(float(sub.r.mean()),5),'sd':round(float(sub.r.std(ddof=1)),4),
  't':round(float(sub.r.mean()/(sub.r.std(ddof=1)/np.sqrt(len(sub)))),3),
  'months_to_own_answer':round(months(float(sub.r.mean()),float(sub.r.std(ddof=1)),len(sub)/fwd_m),3),
  'months_to_detect_0p05R':round(months(0.05,float(sub.r.std(ddof=1)),len(sub)/fwd_m),3),
  'months_to_detect_0p02R':round(months(0.02,float(sub.r.std(ddof=1)),len(sub)/fwd_m),3),
  'days_touched_per_month':round(sub.day.nunique()/fwd_m,2),
  'breadth_multiple_vs_armed_book':round((len(sub)/fwd_m)/3.833,1)}
(OUT/"F_LAW_AND_LADDER_V1.json").write_text(json.dumps(res,indent=1,default=str))
print(json.dumps({k:v for k,v in res['breadth_edge_law'].items() if k!='table'},indent=1))
print("=== BREAK-EVEN ==="); print(json.dumps(res['break_even_cost_haircut'],indent=1)[:2500])
print("=== CONCURRENCY ==="); print(json.dumps(res['concurrency'],indent=1))
print("=== PROP ==="); print(json.dumps(res['prop_rule_check'],indent=1))
print("=== INCUBATION ==="); print(json.dumps(res['incubation_detectability'],indent=1))
print(json.dumps(res['incubation_basket'],indent=1))
