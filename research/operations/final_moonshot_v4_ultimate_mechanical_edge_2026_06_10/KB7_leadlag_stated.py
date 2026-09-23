"""KB7 — re-label the highest-Sharpe leadlag legs with the REAL runtime exit (cs.exit_state_d)
and a WIDER stop, to test whether a better exit converts the 27%-win lottery geometry into a
higher-win, thinner-left-tail growth asset (the task: exits were tuned for core sleeves, not these).
Leak-free: entries unchanged (leader z-impulse at shared close), exit_state_d labels forward only.
"""
import sys; sys.path.insert(0,'.'); sys.path.insert(0,'../../..')
import pickle, statistics, collections, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
import leadlag as ll
import compounding_sleeve as cs
from geometry_lib import simulate
import KB5_fold_new_sleeves as F
def wins(r,hi=5.0): return max(-1.3,min(hi,r))

TOP4=[c for c in F.LEADLAG_CORE if (c[0],c[1]) in
      {('NAS100','SPX500'),('SPX500','NAS100'),('GER40','UK100'),('SPX500','GER40')}]
HISH2=[c for c in F.LEADLAG_CORE if (c[0],c[1]) in
       {('NAS100','SPX500'),('SPX500','NAS100'),('US30_cash','USDJPY')}]

def entries_for_cfg(cfg):
    leader,follower,relsign,look,z,thesis,gname,conf,csign,regime=cfg
    sig=ll.leader_signal(leader,look); pf=ll.panel(follower)
    fb=pf['bars']; ftmap=pf['tmap']; fatrs=pf['atrs']; cost=ll.cost_for(follower)
    T=pf['times']
    out=[]; last=-10**9
    for ts,zz in sig.items():
        if abs(zz)<z: continue
        i=ftmap.get(ts)
        if i is None or i<14 or i>=len(fb)-2: continue
        if i-last<2: continue
        a=fatrs[i]
        if a<=0: continue
        base=(1 if zz>0 else -1)*relsign
        d=base if thesis=='momentum' else -base
        if regime is not None:
            want='trend_up' if (d>0 and regime=='align') else 'trend_down' if (d<0 and regime=='align') else regime
            if not ll._laggard_regime_ok(fb,fatrs,i,want): continue
        out.append((follower,T[i],ts.year,d,i,fb,a,cost)); last=i
    return out

def relabel(cfgs, exit_mode, stop_mult):
    rows=[]
    for cfg in cfgs:
        for (sym,t,yr,d,i,fb,a,cost) in entries_for_cfg(cfg):
            sd=stop_mult*a
            if exit_mode=='state_d':
                vr=cs.vol_ratio([__import__('geometry_lib').atr14(fb,k) for k in range(max(0,i-1),i+1)],-1) if False else None
                # proper vr: cs.vol_ratio(atrs,i) needs full atrs; compute once per follower would be faster
                R=None
            rows.append((sym,t,yr,d,i,fb,a,cost,sd))
    return rows

# Build per-follower atrs once for vr; then relabel
from geometry_lib import atr14
def relabel_fast(cfgs, exit_mode, stop_mult):
    # cache atrs per follower
    panels={}; rows=[]
    for cfg in cfgs:
        ents=entries_for_cfg(cfg)
        for (sym,t,yr,d,i,fb,a,cost) in ents:
            if sym not in panels: panels[sym]=[atr14(fb,k) for k in range(len(fb))]
            atrs=panels[sym]; vr=cs.vol_ratio(atrs,i) or 1.0
            sd=stop_mult*a
            if exit_mode=='state_d':
                res=cs.exit_state_d(fb,i,d,sd,vr,cost,maxbars=80); R=res['R']
            elif exit_mode=='t2':
                R=wins(simulate(fb,i,d,stop_dist=sd,target_dist=2.0*sd,cost=cost,maxbars=80))
            else:
                R=wins(simulate(fb,i,d,stop_dist=sd,target_dist=2.0*sd,cost=cost,maxbars=80))
            rows.append(dict(sleeve='ll_stated',sym=sym,date=t.date(),year=yr,R=wins(R)))
    return rows

def stats(rows):
    R=[r['R'] for r in rows]; n=len(R)
    if not n: return {}
    m=sum(R)/n; sd=statistics.pstdev(R)
    tr=[r['R'] for r in rows if r['year']<=2024]; fw=[r['R'] for r in rows if r['year']>=2025]
    by=collections.defaultdict(list)
    for r in rows: by[r['year']].append(r['R'])
    posy=sum(1 for y,v in by.items() if sum(v)/len(v)>0)
    return dict(n=n,ev=round(m,3),sharpe=round(m/sd,3) if sd>0 else 0,win=round(100*sum(1 for x in R if x>0)/n,1),
                trN=len(tr),trEV=round(sum(tr)/len(tr),3) if tr else None,fwN=len(fw),fwEV=round(sum(fw)/len(fw),3) if fw else None,
                posyears=f'{posy}/{len(by)}', medR=round(sorted(R)[n//2],2))

OUT={}
print(f"{'config':<46}{'n':>5}{'EV':>7}{'Sh':>7}{'win':>6}{'medR':>6}{'TRAIN':>8}{'FWD':>8}{'posyr':>7}")
for name,cfgs in [('top4',TOP4),('hisharpe2',HISH2)]:
    for mode in ['t2_05stop(orig)','state_d_05stop','state_d_10stop','t2_10stop']:
        if mode=='t2_05stop(orig)': rows=relabel_fast(cfgs,'t2',0.5)
        elif mode=='state_d_05stop': rows=relabel_fast(cfgs,'state_d',0.5)
        elif mode=='state_d_10stop': rows=relabel_fast(cfgs,'state_d',1.0)
        else: rows=relabel_fast(cfgs,'t2',1.0)
        s=stats(rows); OUT[f'{name}__{mode}']=s
        if name=='top4' and mode=='state_d_10stop': pickle.dump(rows,open(HERE/'KB7_stream_ll_top4_stated10.pkl','wb'))
        print(f"{name+'__'+mode:<46}{s['n']:>5}{s['ev']:>+7.3f}{s['sharpe']:>+7.3f}{s['win']:>6}{s['medR']:>6}{str(s['trEV']):>8}{str(s['fwEV']):>8}{s['posyears']:>7}")
json.dump(OUT,open(HERE/'KB7_LEADLAG_STATED_RESULT.json','w'),indent=1,default=str)
print('\nwrote KB7_LEADLAG_STATED_RESULT.json')
