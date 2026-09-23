import sys, os, json, gzip
import numpy as np
REPO="/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
PBG=REPO+"/docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg"
sys.path.insert(0,PBG); sys.path.insert(0,REPO); os.chdir(REPO)
import pbg_lib as L, pbg_econ as E
from collections import Counter
DISC=REPO+"/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery"

def walk_limit2(tape,sym,i,*,entry,stop,long,target_r=2.0,horizon=120):
    d=abs(entry-stop)
    if not (d>0): return None
    a=i; b=min(a+horizon,tape.n)
    if a>=b: return None
    hi=tape.h[sym][a:b]; lo=tape.l[sym][a:b]
    ok=~np.isnan(hi)
    if not ok.any(): return None
    idxs=np.nonzero(ok)[0]
    touched = (lo[idxs]<=entry) if long else (hi[idxs]>=entry)
    if not touched.any(): return (0.0,'no_fill',None,int(ok.sum()),None)
    j=int(idxs[int(np.argmax(touched))])
    res=E.walk(tape,sym,a+j,entry=entry,stop=stop,long=long,target_r=target_r,horizon=horizon-j-1)
    if res is None: return (0.0,'no_fill',None,0,None)
    return (res[0],res[1],res[2],res[3],j)

ws={}
with gzip.open(DISC+'/w0_WORKING_SET.jsonl.gz','rt') as fh:
    for l in fh:
        r=json.loads(l); ws[(r['candidate_id'],r['decision_time_utc'])]=r
tape=E.Tape(list(L.SYMBOLS),['202601','202602'])
A=[];B=[];R=Counter();J=[]
for k,r in ws.items():
    lng=(r.get('direction') or r.get('side'))=='LONG'
    i=tape.idx(r['decision_time_utc'])
    o=walk_limit2(tape,r['symbol'],i,entry=r['entry_price'],stop=r['stop_loss'],long=lng,target_r=2.0,horizon=120)
    if o is None: continue
    A.append(o[0]); B.append(r['fill_honest_walk_r']); R[o[1]]+=1
    if o[4] is not None: J.append((o[4], r.get('bars_to_entry_touch')))
A=np.array(A);B=np.array(B)
print('HONEST2 mine %.6f  ws %.6f  meanabs %.6f  within0.01 %.4f  n=%d'%(A.mean(),B.mean(),np.abs(A-B).mean(),(np.abs(A-B)<0.01).mean(),A.size))
print('reasons',R.most_common())
jj=[x for x in J if x[1] is not None]
print('touch-bar agreement: exact %.4f  n=%d'%(np.mean([1.0 if x[0]+1==x[1] or x[0]==x[1] else 0.0 for x in jj]),len(jj)))
