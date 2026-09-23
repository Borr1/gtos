"""B6 step 10 — the PAIRED protocol, specified and powered. Everything is held fixed except the
one treatment bit; the contrast is taken within the same day on the same universe."""
import numpy as np, pandas as pd, json, math, warnings
warnings.filterwarnings('ignore')
from scipy import stats
import b6_core as C
df=C.build_master(); P=df[df.elig&df.filled].copy().sort_values('date')
m=pd.read_csv('daily_direction_index.csv',parse_dates=['date']).set_index('date')['dir_idx']
days=sorted(P.date.unique())
Z=2.487   # 80% power, alpha=0.05 one-sided
Z10=2.123 # 80% power, alpha=0.10 one-sided
def days_needed(mu,sd,z=Z10): return (z*sd/mu)**2 if mu>0 else float('inf')
def paired(treat_mask, ctrl_mask, label, universe=None):
    U=P if universe is None else universe
    T=U[treat_mask(U)]; Cc=U[ctrl_mask(U)]
    dt=T.groupby('date',observed=True).net_r.mean(); dc=Cc.groupby('date',observed=True).net_r.mean()
    d=(dt-dc).dropna()
    if len(d)<10: return None
    rng=np.random.default_rng(5)
    b=np.array([d.iloc[rng.integers(0,len(d),len(d))].mean() for _ in range(4000)])
    r=dict(label=label,days=int(len(d)),mean=round(float(d.mean()),5),sd=round(float(d.std()),5),
           t=round(float(d.mean()/(d.std()/math.sqrt(len(d)))),3),share_pos=round(float((d>0).mean()),3),
           p_le0=round(float((b<=0).mean()),4),
           days_for_80pc_a10=round(days_needed(d.mean(),d.std()),1),
           days_for_80pc_a05=round(days_needed(d.mean(),d.std(),Z),1),
           n_treat=int(len(T)),n_ctrl=int(len(Cc)),
           abs_treat=round(float(T.net_r.mean()),5),abs_ctrl=round(float(Cc.net_r.mean()),5))
    print('  %-46s days=%3d  paired %+0.5f sd %.4f t %+0.2f  P(<=0) %.4f  pos %.2f | days@80%%,a=.10 %6.0f  (abs %+0.5f vs %+0.5f)'%(
      label,r['days'],r['mean'],r['sd'],r['t'],r['p_le0'],r['share_pos'],r['days_for_80pc_a10'],r['abs_treat'],r['abs_ctrl']))
    return r
out=[]
thr={dt:(P[P.date<dt].cost_r.quantile(0.25) if (P.date<dt).sum()>500 else np.nan) for dt in days}
P['thr25']=P.date.map(thr)
thr3={dt:(P[P.date<dt].cost_r.quantile(1/3.) if (P.date<dt).sum()>500 else np.nan) for dt in days}
P['thr33']=P.date.map(thr3)
U=P[P.thr25.notna()].copy()
tr2=m.shift(1).rolling(2,min_periods=1).mean(); U['sig']=U.date.map(tr2)
U['contr']=((U.side=='SHORT')&(U.sig>0))|((U.side=='LONG')&(U.sig<0))
U['costg']=U.cost_r<=U.thr25
print('=== PAIRED CONTRASTS (treatment vs control, same day, same universe) ===')
out.append(paired(lambda x:x.contr&x.costg, lambda x:x.costg, 'B6-P1  contrarian-side | cost-gated universe',U))
out.append(paired(lambda x:x.contr, lambda x:pd.Series(True,index=x.index), 'B6-P2  contrarian-side | full universe',U))
out.append(paired(lambda x:x.costg, lambda x:pd.Series(True,index=x.index), 'B6-P3  cost gate | full universe',U))
out.append(paired(lambda x:(~x.contr)&x.costg, lambda x:x.costg,           'B6-P0  momentum-side (wrong sign) control',U))
# the dead overlay, for comparison
from panel import make_panel
fd,B=make_panel(df,regime_lag=0)
X=fd[B['REG']+B['INT']].fillna(0.).to_numpy(float); mu=X.mean(0); sd=X.std(0); sd[sd<1e-12]=1.; X=(X-mu)/sd
p=C.wf_ridge(X,fd.y.to_numpy(float),fd.n.to_numpy(float),fd.date.to_numpy(),
             np.array(sorted(set(fd.date.to_numpy()))),alpha=10.,causal_scaler=False)
g=fd[['origin_family','date']].copy(); g['pr']=p; g=g.dropna()
V=U.merge(g,on=['origin_family','date'],how='left'); V=V[V.pr.notna()]
out.append(paired(lambda x:(x.pr>0)&x.costg, lambda x:x.costg, 'L6-A+B  NON-CAUSAL overlay (the artifact)',V))
fdc,Bc=make_panel(df,regime_lag=1)
pc=C.wf_ridge(fdc[Bc['REG']+Bc['INT']].fillna(0.).to_numpy(float),fdc.y.to_numpy(float),fdc.n.to_numpy(float),
   fdc.date.to_numpy(),np.array(sorted(set(fdc.date.to_numpy()))),alpha=10.,causal_scaler=True)
gc=fdc[['origin_family','date']].copy(); gc['prc']=pc; gc=gc.dropna()
W=U.merge(gc,on=['origin_family','date'],how='left'); W=W[W.prc.notna()]
out.append(paired(lambda x:(x.prc>0)&x.costg, lambda x:x.costg, 'B6-P4  CAUSAL regime overlay (lag-1)',W))
# SHORT-leg secondary
print('\n=== SHORT-LEG SECONDARY (the mandated one) ===')
out.append(paired(lambda x:x.contr&x.costg&(x.side=='SHORT'), lambda x:x.costg&(x.side=='SHORT'),
                  'B6-S1  contrarian SHORT leg vs cost-gated SHORT',U))
out.append(paired(lambda x:x.contr&x.costg&(x.side=='LONG'), lambda x:x.costg&(x.side=='LONG'),
                  'B6-S2  contrarian LONG leg vs cost-gated LONG',U))
json.dump([o for o in out if o],open('paired.json','w'),indent=1)
