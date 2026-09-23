"""PRICE THE LEVER. The l10 finding says family real-cost dispersion (12.1x) is 'a live lever
nobody has priced'.  Price it out-of-sample: rank families by real cost on JANUARY ONLY, then
evaluate the January-chosen K-cheapest set on FEB / MAR / APR / MAY."""
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
R={}
for lbl,p,ap in JOBS:
    a=E.load_anchor(ap); rows,_,_=E.build_rows(p,a,precomputed=False)
    R[lbl]=[x for x in rows if x['bs']!='born_past_stop']   # takeable
MO=list(R)
def bk(rr):
    if not rr: return {'n':0}
    return {'n':len(rr),'gross':E.m_([x['gross'] for x in rr]),'real_cost':E.m_([x['rtot'] for x in rr]),
            'net_real':E.m_([x['gross']-x['rtot'] for x in rr])}
# JANUARY-ONLY family ranking by real cost
jf=defaultdict(list)
for x in R['JAN']: jf[x['fam']].append(x)
jrank=sorted(jf,key=lambda k:st.mean([y['rtot'] for y in jf[k]]))
out={'january_family_rank_by_real_cost':jrank,
     'january_family_real_cost':{k:round(st.mean([y['rtot'] for y in jf[k]]),6) for k in jrank}}
lad={}
for K in range(1,len(jrank)+1):
    sel=set(jrank[:K]); row={'families':sorted(sel)}
    for mo in MO:
        row[mo]=bk([x for x in R[mo] if x['fam'] in sel])
        row[mo+'_realgate']=bk([x for x in R[mo] if x['fam'] in sel and E.gate(x['rspr'],x['rtot'])])
    lad[K]=row
out['LADDER_JAN_SELECTED']=lad
# same for symbols
js=defaultdict(list)
for x in R['JAN']: js[x['sym']].append(x)
srank=sorted(js,key=lambda k:st.mean([y['rtot'] for y in js[k]]))
out['january_symbol_rank_by_real_cost']=srank
slad={}
for K in [3,6,8,12,16,20,24]:
    sel=set(srank[:K]); row={'n_syms':K,'symbols':sorted(sel)}
    for mo in MO:
        row[mo]=bk([x for x in R[mo] if x['sym'] in sel])
        row[mo+'_realgate']=bk([x for x in R[mo] if x['sym'] in sel and E.gate(x['rspr'],x['rtot'])])
    slad[K]=row
out['LADDER_SYMBOL_JAN_SELECTED']=slad
# combined: Jan-cheapest 4 families AND Jan-cheapest 12 symbols AND real gate AND cheapest half
comb={}
fs=set(jrank[:4]); ss=set(srank[:12])
for mo in MO:
    c=[x for x in R[mo] if x['fam'] in fs and x['sym'] in ss and E.gate(x['rspr'],x['rtot'])]
    comb[mo]=bk(c)
out['COMBINED_JAN_SELECTED_4fam_12sym_realgate']={'families':sorted(fs),'symbols':sorted(ss),'by_month':comb}
json.dump(out,open(f'{D}/E2_LEVER_PRICE_V1.json','w'),indent=1)
print('JAN family rank (cheapest first):'); 
for i,k in enumerate(jrank): print(f'  {i+1:>2} {k:<34}{out["january_family_real_cost"][k]:.4f}')
print()
print('LADDER — cheapest-K families chosen on JANUARY, net@real by month (takeable, no gate)')
print(f"{'K':>2}"+''.join(f'{m:>11}' for m in MO)+f"{'nJAN':>8}{'nOOSmean':>10}")
for K in sorted(lad):
    r=lad[K]; oosn=st.mean([r[m]['n'] for m in MO if m!='JAN'])
    print(f"{K:>2}"+''.join(f"{r[m].get('net_real',0):>11.4f}" for m in MO)+f"{r['JAN']['n']:>8}{oosn:>10.0f}")
print()
print('SAME + REAL GATE')
print(f"{'K':>2}"+''.join(f'{m:>11}' for m in MO)+f"{'nJAN':>8}")
for K in sorted(lad):
    r=lad[K]
    print(f"{K:>2}"+''.join(f"{r[m+'_realgate'].get('net_real',0):>11.4f}" for m in MO)+f"{r['JAN_realgate']['n']:>8}")
print()
print('COMBINED 4fam x 12sym x realgate:', json.dumps(comb))
