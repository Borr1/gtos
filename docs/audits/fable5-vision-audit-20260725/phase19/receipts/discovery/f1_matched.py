"""Matched control: is the TAKEN advantage a better SETUP, or just cheaper geometry?"""
import sys, os, json, gzip, argparse
import numpy as np
REPO="/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
PBG=REPO+"/docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg"
sys.path.insert(0,PBG); sys.path.insert(0,REPO); os.chdir(REPO)
import pbg_lib as L, pbg_econ as E
from collections import defaultdict
sys.path.insert(0,'/tmp/f1')
from f1_walk import walk_limit2, POOL, NEXT, HOR

def rows_for(w):
    out={'pool':[], 'taken':[]}
    tk=json.load(open('/tmp/f1/taken_slim.json'))[w]
    for r in tk:
        if r.get('stop_loss') is None: continue
        out['taken'].append(dict(sym=r['symbol'],t=r['decision_time_utc'],long=r['direction']=='LONG',
                                 entry=r['entry_price'],stop=r['stop_loss'],fam=r.get('origin_family')))
    if w in POOL and os.path.isfile(POOL[w]):
        with gzip.open(POOL[w],'rt') as fh:
            for line in fh:
                r=json.loads(line)
                if r.get('stop_loss') is None: continue
                out['pool'].append(dict(sym=r['symbol'],t=r['decision_time_utc'],
                    long=(r.get('direction') or r.get('side'))=='LONG',
                    entry=r['entry_price'],stop=r['stop_loss'],fam=r.get('origin_family')))
    return out

def walk_all(tape,cm,rows,target_r=2.0):
    res=[]
    for r in rows:
        if r['sym'] not in tape.c: continue
        i=tape.idx(r['t'])
        if not (0<i<tape.n): continue
        d=abs(r['entry']-r['stop'])
        if not d>0: continue
        o=walk_limit2(tape,r['sym'],i,entry=r['entry'],stop=r['stop'],long=r['long'],target_r=target_r,horizon=HOR)
        if o is None: continue
        px,_=cm.cost_px(r['sym'],r['t'],r['entry'],r['long'],hold_min=HOR)
        filled=o[1]!='no_fill'
        res.append(dict(sym=r['sym'],day=r['t'][:10],fam=r['fam'],d_bps=d/r['entry']*1e4,
                        g=o[0],c=(px/d) if filled else 0.0,filled=filled))
    return res

W=sys.argv[1]
mons=[W.replace('-','')]+([NEXT[W]] if NEXT.get(W) else [])
tape=E.Tape(list(L.SYMBOLS),mons); cm=E.CostModel()
R=rows_for(W)
out={}
for k in ('pool','taken'):
    if R[k]: out[k]=walk_all(tape,cm,R[k])
json.dump(out,open(f'/tmp/f1/out/M_{W}.json','w'))
print('rows',W,{k:len(v) for k,v in out.items()})
