"""B6 step 5 — the A+B book re-measured with a CAUSAL regime gate, plus the dial ablation that
identifies which part of the day-median carries the artifact."""
import numpy as np, pandas as pd, json, math, warnings
warnings.filterwarnings('ignore')
from scipy import stats
import b6_core as C
from panel import make_panel
rng=np.random.default_rng(20260811)
df=C.build_master()

def gate_pred(regime_lag, cols_mode='M6', alpha=10.0, causal_scaler=True):
    fd,B=make_panel(df,regime_lag=regime_lag)
    cols = B['REG']+B['INT'] if cols_mode=='M6' else B['FAM']+B['REG']+B['INT']
    X=fd[cols].fillna(0.).to_numpy(float); y=fd.y.to_numpy(float); w=fd.n.to_numpy(float)
    d=fd.date.to_numpy(); ud=np.array(sorted(set(d)))
    p=C.wf_ridge(X,y,w,d,ud,alpha=alpha,causal_scaler=causal_scaler)
    g=fd[['origin_family','date']].copy(); g['pred_regime']=p
    return g.dropna()

P0=df[df.elig&df.filled].copy()
def book(g, q=1/3.0, label=''):
    P=P0.merge(g,on=['origin_family','date'],how='left')
    P=P[P.pred_regime.notna()].sort_values('date').copy()
    days=sorted(P.date.unique())
    thr={dt:(P[P.date<dt].cost_r.quantile(q) if (P.date<dt).sum()>500 else np.nan) for dt in days}
    P['thr']=P.date.map(thr); P=P[P.thr.notna()]
    S=P[(P.pred_regime>0)&(P.cost_r<=P.thr)]
    Bc=P[P.cost_r<=P.thr]                      # cost gate alone, same universe
    A=P[P.pred_regime>0]
    res={}
    for nm,x in (('ALL control',P),('A regime only',A),('B cost only',Bc),('A+B',S)):
        if len(x)<50: continue
        b=C.day_boot_mean(x.net_r,x.date,seed=7)
        pm=x.groupby('month',observed=True).net_r.mean().reindex(['apr','may','jun','jul'])
        res[nm]=dict(n=int(len(x)),mean=round(float(x.net_r.mean()),5),
            se_day=round(float(C.day_cluster_se(x.net_r,x.date)),5),
            ci=[round(float(np.quantile(b,.025)),5),round(float(np.quantile(b,.975)),5)],
            p_le0=round(float((b<=0).mean()),4),total=round(float(x.net_r.sum()),2),
            months_pos=int((pm>0).sum()),
            per_month={k:(round(float(v),5) if pd.notna(v) else None) for k,v in pm.items()})
    return res,S,P

print('='*100); print('A+B WITH THE PUBLISHED (NON-CAUSAL) GATE  vs  A+B WITH A CAUSAL GATE'); print('='*100)
allres={}
for lab,lag,cs in (('published: same-day regime, global scaler',0,False),
                   ('causal: lag-1 regime, train-only scaler',1,True)):
    g=gate_pred(lag,'M6',causal_scaler=cs)
    r,S,P=book(g,label=lab); allres[lab]=r
    print('\n-- %s'%lab)
    print('%-16s %7s %10s %9s %20s %8s %s'%('rule','n','R/trade','se_day','95%CI day-boot','P(<=0)','per-month'))
    for k,v in r.items():
        print('%-16s %7d %+10.5f %9.5f [%+.5f,%+.5f] %8.4f %s  %d/4'%(k,v['n'],v['mean'],v['se_day'],
          v['ci'][0],v['ci'][1],v['p_le0'],' '.join('%+.4f'%x if x is not None else '  n/a' for x in v['per_month'].values()),v['months_pos']))
    if lab.startswith('causal'): CAUS=S
    else: PUB=S
json.dump(allres,open('book_causal.json','w'),indent=1)

# ---- dial ablation: which regime dial carries the artifact? (non-causal L0 arm) ----
print('\n'+'='*100); print('WHICH DIAL CARRIES THE ARTIFACT? (leave-one-out on the non-causal L0 M6 arm)'); print('='*100)
fd,B=make_panel(df,regime_lag=0)
def rho_of(cols):
    X=fd[cols].fillna(0.).to_numpy(float); y=fd.y.to_numpy(float); w=fd.n.to_numpy(float)
    d=fd.date.to_numpy(); ud=np.array(sorted(set(d)))
    p=C.wf_ridge(X,y,w,d,ud,alpha=10.,causal_scaler=False); ok=~np.isnan(p)
    return stats.spearmanr(p[ok],y[ok])
base=rho_of(B['REG']+B['INT']); print('full M6 rho %+.4f (p %.2g)'%(base.statistic,base.pvalue))
abl={}
for dial in ['vol','ccvol','comp','spread','cost','risk','trendshare','upshare','dow']:
    cols=[c for c in B['REG'] if c!=dial]+[c for c in B['INT'] if not c.endswith('_'+dial)]
    r=rho_of(cols); abl[dial]=round(float(r.statistic),5)
    print('  drop %-11s rho %+.4f (p %-9.2g) delta %+.4f'%(dial,r.statistic,r.pvalue,r.statistic-base.statistic))
# keep-one
print(' keep-one-dial-only (dial + its 10 family interactions):')
k1={}
for dial in ['vol','ccvol','comp','spread','cost','risk','trendshare','upshare']:
    cols=[dial]+[c for c in B['INT'] if c.endswith('_'+dial)]
    if len(cols)==1: cols=[dial]
    r=rho_of(cols); k1[dial]=round(float(r.statistic),5)
    print('  only %-11s rho %+.4f (p %.2g)'%(dial,r.statistic,r.pvalue))
json.dump(dict(base=round(float(base.statistic),5),leave_one_out=abl,keep_one=k1),open('dial_ablation.json','w'),indent=1)
