import json,gzip,glob,os
import numpy as np
AD=json.load(open('/tmp/f1/arm_days.json'))
R={};T={}
for f in sorted(glob.glob('/tmp/f1/out/RR_*.json.gz')):
    w=os.path.basename(f)[3:-8]
    with gzip.open(f,'rt') as fh: rows=json.load(fh)
    ok=set(AD[w]); R[w]=[r for r in rows if r['day'] in ok]
P={}
for f in sorted(glob.glob('/tmp/f1/out/M_*.json')):
    w=os.path.basename(f)[2:-5]; d=json.load(open(f))
    P[w]=d.get('pool',[]); T[w]=d.get('taken',[])
# march taken (no M_ file)
import sys
def add_march():
    try:
        d=json.load(open('/tmp/f1/out/W_2026-03.json'))
    except Exception: return
add_march()
def matched(controls_by_w, label, require_filled=True, tol=0.25, kmin=5):
    dl=[];tg=[];cg=[];n=0
    for w,tt in T.items():
        C=controls_by_w.get(w)
        if not C: continue
        idx={}
        for r in C:
            if require_filled and not r.get('filled',True): continue
            idx.setdefault(r['sym'],[]).append(r)
        for t in tt:
            cand=idx.get(t['sym'],[])
            lo,hi=t['d_bps']*(1-tol),t['d_bps']*(1+tol)
            mm=[x for x in cand if lo<=x['d_bps']<=hi]
            if len(mm)<kmin: continue
            n+=1; tg.append(t['g']); m=float(np.mean([x['g'] for x in mm])); cg.append(m); dl.append(t['g']-m)
    d=np.array(dl)
    if d.size<5: print(label,'insufficient'); return None
    rs=np.random.default_rng(23); b=d[rs.integers(0,d.size,(8000,d.size))].mean(axis=1)
    out=dict(label=label,n=int(n),taken_gross=float(np.mean(tg)),control_gross=float(np.mean(cg)),
             delta=float(d.mean()),ci95=[float(np.percentile(b,2.5)),float(np.percentile(b,97.5))],
             p_le0=float((b<=0).mean()))
    print('%-46s n=%4d taken=%+.5f ctrl=%+.5f DELTA=%+.5f CI95=[%+.5f,%+.5f] p(<=0)=%.4f'%(
        label,n,out['taken_gross'],out['control_gross'],out['delta'],out['ci95'][0],out['ci95'][1],out['p_le0']))
    return out
res={}
res['vs_pool']=matched(P,'TAKEN vs POOL (declined set), matched d+-25%',require_filled=True)
res['vs_roster']=matched(R,'TAKEN vs ROSTER (all emissions), matched d+-25%',require_filled=True)
# roster clean controls
Rc={w:[r for r in v if r['filled'] and not r['past'] and r['fam']!='current_breaker_re_entry'] for w,v in R.items()}
res['vs_roster_clean']=matched(Rc,'TAKEN vs ROSTER-CLEAN, matched d+-25%',require_filled=False)
# also same-family matched
def matched_fam(controls_by_w,label):
    dl=[];tg=[];cg=[];n=0
    for w,tt in T.items():
        C=controls_by_w.get(w)
        if not C: continue
        idx={}
        for r in C: idx.setdefault((r['sym'],r['fam']),[]).append(r)
        for t in tt:
            cand=idx.get((t['sym'],t['fam']),[])
            lo,hi=t['d_bps']*0.75,t['d_bps']*1.25
            mm=[x for x in cand if lo<=x['d_bps']<=hi]
            if len(mm)<5: continue
            n+=1; tg.append(t['g']); m=float(np.mean([x['g'] for x in mm])); cg.append(m); dl.append(t['g']-m)
    d=np.array(dl)
    if d.size<5: print(label,'insufficient'); return None
    rs=np.random.default_rng(31); b=d[rs.integers(0,d.size,(8000,d.size))].mean(axis=1)
    print('%-46s n=%4d taken=%+.5f ctrl=%+.5f DELTA=%+.5f CI95=[%+.5f,%+.5f] p(<=0)=%.4f'%(
        label,n,np.mean(tg),np.mean(cg),d.mean(),np.percentile(b,2.5),np.percentile(b,97.5),float((b<=0).mean())))
    return dict(label=label,n=int(n),taken_gross=float(np.mean(tg)),control_gross=float(np.mean(cg)),
                delta=float(d.mean()),ci95=[float(np.percentile(b,2.5)),float(np.percentile(b,97.5))],p_le0=float((b<=0).mean()))
res['vs_pool_samefam']=matched_fam(P,'TAKEN vs POOL, matched d +- family + symbol')
res['vs_roster_samefam']=matched_fam(R,'TAKEN vs ROSTER, matched d + family + symbol')
json.dump(res,open('/tmp/f1/matched_full.json','w'),indent=1)
