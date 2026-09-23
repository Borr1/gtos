import json,glob,os
import numpy as np
D={os.path.basename(f)[2:-5]:json.load(open(f)) for f in sorted(glob.glob('/tmp/f1/out/W_*.json'))}
def pool_e(key,sub=None):
    """weighted pooling of per-window econ dicts by n (means are per-trade)"""
    ns=[];gm=[];cm=[];nm=[]
    for w in sorted(D):
        e=D[w].get(key)
        if sub and e: e=e.get(sub)
        if not e: continue
        ns.append(e['n']); gm.append(e['gross_mean']); cm.append(e['cost_mean']); nm.append(e['net_mean'])
    if not ns: return None
    ns=np.array(ns,float)
    return dict(n=int(ns.sum()),windows=len(ns),
       gross=float((np.array(gm)*ns).sum()/ns.sum()),
       cost=float((np.array(cm)*ns).sum()/ns.sum()),
       net=float((np.array(nm)*ns).sum()/ns.sum()),
       per_window_net=[round(x,5) for x in nm],
       windows_net_positive=int(sum(1 for x in nm if x>0)))
KEYS=[('roster_honest_t2.0','ROSTER honest 2R (all emissions)'),
      ('roster_honest_t2.0|filled_only','ROSTER honest 2R FILLED only'),
      ('pool_honest_t2.0','POOL(missed,scoreable) honest 2R'),
      ('taken_honest_t2.0','TAKEN honest 2R (plain contract)'),
      ('taken_realised','TAKEN realised (arm policy+arm cost)'),
      ('roster_honest_t2.0|cohort_at_market','ROSTER at-market honest 2R'),
      ('pool_honest_t2.0|cohort_at_market','POOL at-market honest 2R'),
      ('taken_honest_t2.0|cohort_at_market','TAKEN at-market honest 2R'),
      ('roster_honest_t2.0|cohort_poi','ROSTER POI honest 2R'),
      ('pool_honest_t2.0|cohort_poi','POOL POI honest 2R'),
      ('taken_honest_t2.0|cohort_poi','TAKEN POI honest 2R'),
      ]
print(f"{'population':42s} {'n':>8s} {'win':>3s} {'gross':>9s} {'cost':>8s} {'net':>9s} {'w+':>4s}")
print('-'*95)
res={}
for k,lab in KEYS:
    if '|' in k: a,b=k.split('|')
    else: a,b=k,None
    p=pool_e(a,b)
    if not p: continue
    res[lab]=p
    print(f"{lab:42s} {p['n']:8d} {p['windows']:3d} {p['gross']:+9.5f} {p['cost']:8.5f} {p['net']:+9.5f} {p['windows_net_positive']:4d}")
json.dump(res,open('/tmp/f1/pooled.json','w'),indent=1)
