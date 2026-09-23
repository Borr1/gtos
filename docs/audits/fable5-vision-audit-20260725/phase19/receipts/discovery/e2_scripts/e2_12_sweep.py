"""Systematic conditioned-cell sweep. Every cell is defined by JANUARY-ONLY structure
(families ranked by January real cost) crossed with a session set and gate choice; the
economics are then read on all five months. The full look count is declared."""
import json,sys,os,statistics as st,itertools
from collections import defaultdict
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import e2_recost as E
D=E.D
W='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725'
F='/Users/borr/GTOSActive/worktrees/fa2-integration-20260803/docs/audits/fable5-vision-audit-20260725'
JOBS=[('JAN',f'{W}/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz',f'{D}/e2_ANCHOR_JAN.jsonl.gz'),
      ('FEB',f'{W}/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz',f'{D}/e2_ANCHOR_FEB.jsonl.gz'),
      ('MAR',f'{D}/e2_MARCH_R0_POOL_V1.jsonl.gz',f'{D}/e2_ANCHOR_MAR.jsonl.gz'),
      ('APR',f'{F}/phase19/receipts/pools/CS_APRIL_S0R0_POOL_V1.jsonl.gz',f'{D}/e2_ANCHOR_APR.jsonl.gz'),
      ('MAY',f'{F}/phase19/receipts/pools/CS_MAY_S0R0_POOL_V1.jsonl.gz',f'{D}/e2_ANCHOR_MAY.jsonl.gz')]
T={}
for lbl,p,ap in JOBS:
    a=E.load_anchor(ap); rows,_,_=E.build_rows(p,a,precomputed=False)
    T[lbl]=[x for x in rows if x['bs']!='born_past_stop']
MO=list(T)
jf=defaultdict(list)
for x in T['JAN']: jf[x['fam']].append(x)
JRANK=sorted(jf,key=lambda k:st.mean([y['rtot'] for y in jf[k]]))
SESSSETS={'ALL':None,'london':{'london'},'ny':{'ny'},'london_ny':{'london','ny'},
          'london_ny_tokyo':{'london','ny','tokyo'}}
CELLS=[]
for K in range(1,11):
    fams=set(JRANK[:K])
    for sname,sset in SESSSETS.items():
        for gname,gon in [('nogate',False),('realgate',True)]:
            CELLS.append((f'K{K}|{sname}|{gname}',fams,sset,gon))
def sel(rows,fams,sset,gon):
    o=[]
    for x in rows:
        if x['fam'] not in fams: continue
        if sset is not None and x['sess'] not in sset: continue
        if gon and not E.gate(x['rspr'],x['rtot']): continue
        o.append(x)
    return o
res={}
for name,fams,sset,gon in CELLS:
    per={}
    for m in MO:
        s=sel(T[m],fams,sset,gon)
        per[m]={'n':len(s),'gross':E.m_([x['gross'] for x in s]),'real_cost':E.m_([x['rtot'] for x in s]),
                'net_real':E.m_([x['gross']-x['rtot'] for x in s])} if s else {'n':0,'gross':None,'real_cost':None,'net_real':None}
    gs=[per[m]['gross'] for m in MO if per[m]['n']>=30]
    ns=[per[m]['net_real'] for m in MO if per[m]['n']>=30]
    if not gs: continue
    res[name]={'per_month':per,'gross_mean':round(st.mean(gs),6),'net_real_mean':round(st.mean(ns),6),
        'months_gross_positive':sum(1 for g in gs if g>0),'months_net_positive':sum(1 for v in ns if v>0),
        'n_total':sum(per[m]['n'] for m in MO),'n_min_month':min(per[m]['n'] for m in MO),
        'worst_gross':round(min(gs),6),'families':sorted(fams),'sessions':(sorted(sset) if sset else 'ALL'),'gate':gon}
out={'n_cells_declared':len(CELLS),'n_cells_evaluated':len(res),
 'look_declaration':'10 family-depths x 5 session sets x 2 gate choices = 100 declared cells, evaluated on 5 months. Family ORDER is fixed by January real cost only (no outcome read). Sessions and gate are pre-enumerated, not searched. This is DISCOVERY evidence; no admission claim.',
 'january_family_rank':JRANK,'cells':res}
json.dump(out,open(f'{D}/E2_SWEEP_V1.json','w'),indent=1)
top=sorted(res.items(),key=lambda kv:-kv[1]['gross_mean'])[:14]
print(f'{len(CELLS)} declared cells, {len(res)} evaluable. TOP 14 by MEAN GROSS across five months:')
print(f"{'cell':<26}"+''.join(f'{m:>9}' for m in MO)+f"{'meanG':>9}{'meanNet':>9}{'g+':>3}{'nMin':>7}{'N':>7}")
for k,v in top:
    p=v['per_month']
    print(f"{k:<26}"+''.join(f"{p[m]['gross']:>9.4f}" if p[m]['n']>=30 else f"{'-':>9}" for m in MO)+f"{v['gross_mean']:>9.4f}{v['net_real_mean']:>9.4f}{v['months_gross_positive']:>3}{v['n_min_month']:>7}{v['n_total']:>7}")
print()
print('cells with POSITIVE mean gross:',sum(1 for v in res.values() if v['gross_mean']>0),'of',len(res))
print('cells with POSITIVE mean net@real:',sum(1 for v in res.values() if v['net_real_mean']>0),'of',len(res))
