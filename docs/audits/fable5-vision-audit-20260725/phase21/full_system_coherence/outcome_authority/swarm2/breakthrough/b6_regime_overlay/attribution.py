"""B6 step 8 — THE SHORT-LEG VERDICT. Attribute the published A+B's LONG-only edge.
Hypothesis: the artifact reads the day's realised trendiness, so it lands on days that trended;
the window's cumulative direction is UP, so the days it lands on are mostly up-days, so its LONG
leg wins and its SHORT leg does not. Test it directly."""
import numpy as np, pandas as pd, json, warnings
warnings.filterwarnings('ignore')
from scipy import stats
import b6_core as C
from panel import make_panel
df=C.build_master(); P0=df[df.elig&df.filled].copy()
mkt=pd.read_csv('daily_direction_index.csv',parse_dates=['date']).set_index('date')
m=mkt['dir_idx']
def gate(lag,cs):
    fd,B=make_panel(df,regime_lag=lag)
    cols=B['REG']+B['INT']
    X=fd[cols].fillna(0.).to_numpy(float)
    if not cs:
        mu=X.mean(0); sd=X.std(0); sd[sd<1e-12]=1.; X=(X-mu)/sd
    y=fd.y.to_numpy(float); w=fd.n.to_numpy(float); d=fd.date.to_numpy(); ud=np.array(sorted(set(d)))
    p=C.wf_ridge(X,y,w,d,ud,alpha=10.,causal_scaler=cs)
    g=fd[['origin_family','date']].copy(); g['pr']=p; return g.dropna()
g=gate(0,False)
P=P0.merge(g,on=['origin_family','date'],how='left'); P=P[P.pr.notna()].sort_values('date')
days=sorted(P.date.unique())
thr={dt:(P[P.date<dt].cost_r.quantile(1/3.) if (P.date<dt).sum()>500 else np.nan) for dt in days}
P['thr']=P.date.map(thr); P=P[P.thr.notna()]
S=P[(P.pr>0)&(P.cost_r<=P.thr)]
print('published A+B rebuilt (global scaler): n=%d  net %+0.5f  LONG %+0.5f (n=%d)  SHORT %+0.5f (n=%d)'%(
  len(S),S.net_r.mean(),S[S.side=='LONG'].net_r.mean(),(S.side=='LONG').sum(),
  S[S.side=='SHORT'].net_r.mean(),(S.side=='SHORT').sum()))
S=S.copy(); S['dir']=S.date.map(m); P=P.copy(); P['dir']=P.date.map(m)
print('\n1) DOES THE GATE LAND ON UP-DAYS?  mean direction index')
sw=S.groupby('date',observed=True).size()
print('   all OOS days            : %+0.4f  (n=%d days)'%(P.groupby('date').dir.first().mean(),P.date.nunique()))
print('   A+B trade-weighted      : %+0.4f'%S.dir.mean())
print('   A+B day-weighted        : %+0.4f  (n=%d days)'%(S.groupby('date').dir.first().mean(),S.date.nunique()))
r=stats.spearmanr(sw.reindex(P.date.unique()).fillna(0), m.reindex(P.date.unique()))
print('   corr(A+B trades that day, direction index) rho %+0.3f p %.4f'%(r.statistic,r.pvalue))
print('\n2) A+B LEGS BY DAY-DIRECTION TERCILE (of the OOS days)')
q=pd.qcut(m.reindex(P.date.unique()).dropna(),3,labels=[0,1,2])
S['q']=S.date.map(q); P['q']=P.date.map(q)
print('%-6s %6s %8s | %22s | %22s'%('tercile','days','dir','A+B  LONG / SHORT / all','CONTROL LONG / SHORT'))
rows=[]
for t in (0,1,2):
    s=S[S.q==t]; c=P[P.q==t]
    rows.append(dict(tercile=int(t),days=int(s.date.nunique()),dir=round(float(m[q[q==t].index].mean()),4),
       ab_long=round(float(s[s.side=='LONG'].net_r.mean()),5),ab_short=round(float(s[s.side=='SHORT'].net_r.mean()),5),
       ab_all=round(float(s.net_r.mean()),5),ab_n=int(len(s)),
       ctl_long=round(float(c[c.side=='LONG'].net_r.mean()),5),ctl_short=round(float(c[c.side=='SHORT'].net_r.mean()),5)))
    print('%-6d %6d %+8.4f | %+7.4f %+7.4f %+7.4f | %+7.4f %+7.4f'%(t,s.date.nunique(),m[q[q==t].index].mean(),
      s[s.side=='LONG'].net_r.mean(),s[s.side=='SHORT'].net_r.mean(),s.net_r.mean(),
      c[c.side=='LONG'].net_r.mean(),c[c.side=='SHORT'].net_r.mean()))
print('\n3) IS A+B ANYTHING BEYOND ITS DAY x SIDE COMPOSITION?')
key=pd.MultiIndex.from_arrays([P.date,P.side])
base=P.groupby(['date','side'],observed=True).net_r.mean()
S['base']=pd.MultiIndex.from_arrays([S.date,S.side]).map(base)
resid=S.net_r-S.base
b=C.day_boot_mean(resid,S.date,seed=31)
print('   E[net | A+B]                                = %+0.5f'%S.net_r.mean())
print('   E[same-day same-side control | A+B rows]    = %+0.5f   <-- pure day x side COMPOSITION'%S.base.mean())
print('   residual (within day, within side)          = %+0.5f  95%%CI [%+0.5f,%+0.5f]  P(<=0)=%.4f'%(
   resid.mean(),np.quantile(b,.025),np.quantile(b,.975),(b<=0).mean()))
print('   control overall                             = %+0.5f'%P.net_r.mean())
print('   => composition explains %.0f%% of the +%.5f gap'%(
   100*(S.base.mean()-P.net_r.mean())/(S.net_r.mean()-P.net_r.mean()), S.net_r.mean()-P.net_r.mean()))
for sd_ in ('LONG','SHORT'):
    x=S[S.side==sd_]; rr=x.net_r-x.base
    print('   %-5s leg: net %+0.5f = composition %+0.5f + residual %+0.5f'%(sd_,x.net_r.mean(),x.base.mean(),rr.mean()))
json.dump(dict(terciles=rows,resid=float(resid.mean()),resid_ci=[float(np.quantile(b,.025)),float(np.quantile(b,.975))],
   resid_p=float((b<=0).mean()),composition=float(S.base.mean()),ab=float(S.net_r.mean()),ctrl=float(P.net_r.mean()),
   dir_ab=float(S.dir.mean()),dir_all=float(P.groupby('date').dir.first().mean())),open('attribution.json','w'),indent=1)
