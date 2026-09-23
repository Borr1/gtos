"""Statistics on the one cell with positive mean net@real across five months.
Bootstrap CI + a permutation test against same-session same-month peers."""
import json,sys,os,random,statistics as st
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
FAM2={'regime_transition_break','volatility_compression_expansion'}
cell=[]; ny=[]
for m in MO:
    for x in T[m]:
        if x['sess']!='ny': continue
        ny.append((m,x))
        if x['fam'] in FAM2: cell.append((m,x))
gv=[x['gross'] for _,x in cell]; nv=[x['gross']-x['rtot'] for _,x in cell]
random.seed(20260806)
def boot(v,B=20000):
    n=len(v); ms=[]
    for _ in range(B):
        ms.append(sum(v[random.randrange(n)] for _ in range(n))/n)
    ms.sort(); return round(ms[int(0.05*B)],6),round(ms[int(0.95*B)],6),round(ms[int(0.025*B)],6),round(ms[int(0.975*B)],6)
g5,g95,g025,g975=boot(gv); n5,n95,n025,n975=boot(nv)
# permutation: within each month, draw the same number of NY rows at random
bym=defaultdict(list)
for m,x in ny: bym[m].append(x)
cnt={m:sum(1 for mm,_ in cell if mm==m) for m in MO}
B=20000; hits=0; nulls=[]
obs=st.mean(gv)
for _ in range(B):
    tot=[];
    for m in MO:
        pool=bym[m]; k=cnt[m]
        tot.extend(pool[random.randrange(len(pool))]['gross'] for _ in range(k))
    mm=sum(tot)/len(tot); nulls.append(mm)
    if mm>=obs: hits+=1
p=(hits+1)/(B+1)
syms=defaultdict(int); fams=defaultdict(int); days=set()
for m,x in cell: syms[x['sym']]+=1; fams[x['fam']]+=1; days.add((m,x['day']))
res={'cell':'K2|ny = {regime_transition_break, volatility_compression_expansion} x session_bucket==ny, takeable',
 'n':len(gv),'n_by_month':cnt,'n_ny_universe':len(ny),
 'gross_mean':round(st.mean(gv),6),'gross_bootstrap_90CI':[g5,g95],'gross_bootstrap_95CI':[g025,g975],
 'net_real_mean':round(st.mean(nv),6),'net_real_bootstrap_90CI':[n5,n95],'net_real_bootstrap_95CI':[n025,n975],
 'real_cost_mean':round(st.mean([x['rtot'] for _,x in cell]),6),
 'permutation_p_vs_same_month_ny_peers':round(p,6),'permutation_B':B,
 'permutation_null_mean':round(st.mean(nulls),6),
 'ny_universe_gross_mean':round(st.mean([x['gross'] for _,x in ny]),6),
 'symbols':dict(sorted(syms.items(),key=lambda kv:-kv[1])),'families':dict(fams),
 'distinct_decision_days':len(days),
 'declared_looks_this_lane':100,
 'caveat':'DISCOVERY ONLY. n=390 over five months (78/month), 100 declared cells in this sweep, and the cell was picked BY its five-month mean. Not an admission claim.'}
json.dump(res,open(f'{D}/E2_CELLSTAT_V1.json','w'),indent=1)
print(json.dumps({k:v for k,v in res.items() if k not in ('symbols','caveat')},indent=1))
print('symbols:',json.dumps(res['symbols']))
