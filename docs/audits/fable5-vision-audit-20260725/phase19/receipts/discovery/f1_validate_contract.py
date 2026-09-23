import sys, os, json, gzip
import numpy as np
REPO="/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
PBG=REPO+"/docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg"
sys.path.insert(0,PBG); sys.path.insert(0,REPO); os.chdir(REPO)
import pbg_lib as L, pbg_econ as E
from collections import Counter
DISC=REPO+"/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery"
ws={}
with gzip.open(DISC+'/w0_WORKING_SET.jsonl.gz','rt') as fh:
    for l in fh:
        r=json.loads(l); ws[(r['candidate_id'],r['decision_time_utc'])]=r
tape=E.Tape(list(L.SYMBOLS),['202601','202602'])
mine_h={};mine_m={}
wcf=Counter()
for k,r in ws.items():
    sym=r['symbol']; i=tape.idx(r['decision_time_utc'])
    lng = (r.get('direction') or r.get('side'))=='LONG'
    o=E.walk_limit(tape,sym,i,entry=r['entry_price'],stop=r['stop_loss'],long=lng,target_r=2.0,horizon=120)
    m=E.walk(tape,sym,i,entry=r['entry_price'],stop=r['stop_loss'],long=lng,target_r=2.0,horizon=120)
    mine_h[k]=o[0] if o else None; mine_m[k]=m[0] if m else None
    wcf[o[1] if o else 'none']+=1
a=np.array([mine_h[k] for k in ws if mine_h[k] is not None])
b=np.array([ws[k]['fill_honest_walk_r'] for k in ws if mine_h[k] is not None])
c=np.array([mine_m[k] for k in ws if mine_m[k] is not None])
d=np.array([ws[k]['plain_walk_r'] for k in ws if mine_m[k] is not None])
print('HONEST  mine %.6f  ws %.6f  meanabsdiff %.6f  within0.01 %.4f  n=%d'%(a.mean(),b.mean(),np.abs(a-b).mean(),(np.abs(a-b)<0.01).mean(),a.size))
print('MARKET  mine %.6f  ws %.6f  meanabsdiff %.6f  within0.01 %.4f  n=%d'%(c.mean(),d.mean(),np.abs(c-d).mean(),(np.abs(c-d)<0.01).mean(),c.size))
print('my exit reasons',wcf.most_common())
print('ws fill_honest_which_came_first',Counter(r['fill_honest_which_came_first'] for r in ws.values()).most_common())
