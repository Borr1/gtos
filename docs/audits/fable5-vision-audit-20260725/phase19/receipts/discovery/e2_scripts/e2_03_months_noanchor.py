import json,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import e2_recost as E
W='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725'
F='/Users/borr/GTOSActive/worktrees/fa2-integration-20260803/docs/audits/fable5-vision-audit-20260725'
POOLS=[('JAN',f'{W}/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz'),
       ('FEB',f'{W}/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz'),
       ('APR',f'{F}/phase19/receipts/pools/CS_APRIL_S0R0_POOL_V1.jsonl.gz'),
       ('MAY',f'{F}/phase19/receipts/pools/CS_MAY_S0R0_POOL_V1.jsonl.gz')]
out={}
for lbl,p in POOLS:
    rows,miss,un=E.build_rows(p,None,precomputed=False)
    r=E.full_report(rows,lbl); r['missing_symbols']=miss; r['unusable']=un; r['pool_path']=p
    out[lbl]=r
json.dump(out,open(f'{E.D}/E2_MONTHS_NOANCHOR_V1.json','w'),indent=1)
print(f"{'mo':<5}{'n':>7}{'gross':>10}{'frozen':>9}{'real':>9}{'netFroz':>10}{'netReal':>10}{'OVERCHG':>10}{'ratio':>8}{'passF':>7}{'passR':>7}")
for lbl in out:
    a=out[lbl]['A_all_rows']
    print(f"{lbl:<5}{a['n']:>7}{a['gross']:>10.4f}{a['frozen_cost']:>9.4f}{a['real_cost']:>9.4f}{a['net_frozen']:>10.4f}{a['net_real']:>10.4f}{out[lbl]['OVERCHARGE_R_PER_TRADE']:>10.4f}{out[lbl]['OVERCHARGE_RATIO']:>8.2f}{out[lbl]['GATE_PASS_FROZEN_ALLROWS']:>7}{out[lbl]['GATE_PASS_REAL_ALLROWS']:>7}")
print()
print('FAMILY REAL COST DISPERSION (all rows, no anchor)')
for lbl in out:
    fd=out[lbl].get('FAMILY_REAL_COST_DISPERSION')
    print(' ',lbl,json.dumps(fd))
print('missing symbols:', {k:out[k]['missing_symbols'] for k in out}, 'unusable:', {k:out[k]['unusable'] for k in out})
