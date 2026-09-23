"""Composition check: why is March's born_past_stop share 5.76% when the other four are 12.1-12.8%?
Also the per-month family mix, which governs comparability of every pooled number above."""
import json,sys,os,statistics as st
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
ALL={}
for lbl,p,ap in JOBS:
    a=E.load_anchor(ap); rows,_,_=E.build_rows(p,a,precomputed=False); ALL[lbl]=rows
MO=list(ALL)
out={'months':MO}
comp={}; ps={}
for m in MO:
    r=ALL[m]; n=len(r); g=defaultdict(list)
    for x in r: g[x['fam']].append(x)
    comp[m]={k:round(len(v)/n,5) for k,v in sorted(g.items(),key=lambda kv:-len(kv[1]))}
    ps[m]={k:round(sum(1 for y in v if y['bs']=='born_past_stop')/len(v),5) for k,v in g.items()}
    ps[m]['__POOL__']=round(sum(1 for x in r if x['bs']=='born_past_stop')/n,5)
out['family_share']=comp; out['past_stop_rate_by_family']=ps
# counterfactual: give March January's family weights, recompute past-stop share
fams=sorted(set.union(*[set(comp[m]) for m in MO]))
cf={}
for m in MO:
    s=sum(comp['JAN'].get(f,0) for f in fams if f in ps[m])
    cf[m]=round(sum(comp['JAN'].get(f,0)*ps[m].get(f,0) for f in fams if f in ps[m])/s,5) if s else None
out['past_stop_share_reweighted_to_JAN_family_mix']=cf
json.dump(out,open(f'{D}/E2_COMPOSITION_V1.json','w'),indent=1)
print('FAMILY SHARE of pool')
print(f"{'family':<34}"+''.join(f'{m:>9}' for m in MO))
for f in sorted(fams,key=lambda f:-comp['JAN'].get(f,0)):
    print(f"{f:<34}"+''.join(f"{comp[m].get(f,0):>9.4f}" for m in MO))
print()
print('BORN_PAST_STOP RATE within family')
print(f"{'family':<34}"+''.join(f'{m:>9}' for m in MO))
for f in sorted(fams,key=lambda f:-ps['JAN'].get(f,0)):
    print(f"{f:<34}"+''.join(f"{ps[m].get(f,0):>9.4f}" for m in MO))
print(f"{'__POOL__':<34}"+''.join(f"{ps[m]['__POOL__']:>9.4f}" for m in MO))
print(f"{'REWEIGHTED to JAN family mix':<34}"+''.join(f"{cf[m]:>9.4f}" for m in MO))
