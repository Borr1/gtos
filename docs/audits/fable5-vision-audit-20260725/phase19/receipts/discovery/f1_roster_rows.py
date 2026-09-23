import sys, os, json, gzip, glob
import numpy as np
REPO="/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
PBG=REPO+"/docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg"
sys.path.insert(0,PBG); sys.path.insert(0,REPO); os.chdir(REPO)
import pbg_lib as L, pbg_econ as E
sys.path.insert(0,'/tmp/f1')
from f1_walk import walk_limit2, NEXT, HOR
W=sys.argv[1]; SRC=sys.argv[2]
mons=[W.replace('-','')]+([NEXT[W]] if NEXT.get(W) else [])
tape=E.Tape(list(L.SYMBOLS),mons); cm=E.CostModel()
res=[]
for f in sorted(glob.glob(SRC+'/*.jsonl.gz')):
    with gzip.open(f,'rt') as fh:
        for line in fh:
            r=json.loads(line)
            if r['k']!=15: continue
            sym=r['s']
            if sym not in tape.c: continue
            i=tape.idx(r['t'])
            if not (0<i<tape.n): continue
            d=abs(r['e']-r['sl'])
            if not d>0: continue
            lng=r['d']=='L'
            o=walk_limit2(tape,sym,i,entry=r['e'],stop=r['sl'],long=lng,target_r=2.0,horizon=HOR)
            if o is None: continue
            px,_=cm.cost_px(sym,r['t'],r['e'],lng,hold_min=HOR)
            filled=o[1]!='no_fill'
            mkt=tape.last_close_before(sym,i)
            past=(mkt<=r['sl']) if lng else (mkt>=r['sl'])
            res.append(dict(sym=sym,day=r['t'][:10],fam=r['f'],d_bps=d/r['e']*1e4,
                g=o[0],c=(px/d) if filled else 0.0,filled=bool(filled),
                past=bool(past) if mkt==mkt else False, reason=o[1], touch=o[4]))
with gzip.open(f'/tmp/f1/out/RR_{W}.json.gz','wt') as fh: json.dump(res,fh)
print('roster rows',W,len(res))
