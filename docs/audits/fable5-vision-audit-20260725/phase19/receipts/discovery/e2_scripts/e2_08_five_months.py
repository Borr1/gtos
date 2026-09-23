import json,sys,os,statistics as st
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import e2_recost as E
W='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725'
F='/Users/borr/GTOSActive/worktrees/fa2-integration-20260803/docs/audits/fable5-vision-audit-20260725'
D=E.D
JOBS=[('JAN',f'{W}/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz',f'{D}/e2_ANCHOR_JAN.jsonl.gz'),
      ('FEB',f'{W}/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz',f'{D}/e2_ANCHOR_FEB.jsonl.gz'),
      ('MAR',f'{D}/e2_MARCH_R0_POOL_V1.jsonl.gz',f'{D}/e2_ANCHOR_MAR.jsonl.gz'),
      ('APR',f'{F}/phase19/receipts/pools/CS_APRIL_S0R0_POOL_V1.jsonl.gz',f'{D}/e2_ANCHOR_APR.jsonl.gz'),
      ('MAY',f'{F}/phase19/receipts/pools/CS_MAY_S0R0_POOL_V1.jsonl.gz',f'{D}/e2_ANCHOR_MAY.jsonl.gz')]
out={}
for lbl,p,ap in JOBS:
    a=E.load_anchor(ap); rows,miss,un=E.build_rows(p,a,precomputed=False)
    r=E.full_report(rows,lbl); r['pool_path']=p; r['anchor_path']=ap; r['missing_symbols']=miss; r['unusable']=un
    # cost-term decomposition on all rows
    r['REAL_COST_DECOMP']={'spread':E.m_([x['rspr'] for x in rows]),'commission':E.m_([x['rcm'] for x in rows]),
                          'slippage':E.m_([x['rsl'] for x in rows])}
    out[lbl]=r
json.dump(out,open(f'{D}/E2_FIVE_MONTHS_V1.json','w'),indent=1)
MO=list(out)
print('=== HEADLINE: what correcting the cost model is worth, per month (ALL rows) ===')
print(f"{'mo':<5}{'n':>7}{'gross':>10}{'frozen':>9}{'real':>9}{'netFroz':>10}{'netReal':>10}{'WORTH':>9}{'ratio':>7}")
for k in MO:
    a=out[k]['A_all_rows']
    print(f"{k:<5}{a['n']:>7}{a['gross']:>10.4f}{a['frozen_cost']:>9.4f}{a['real_cost']:>9.4f}{a['net_frozen']:>10.4f}{a['net_real']:>10.4f}{out[k]['OVERCHARGE_R_PER_TRADE']:>9.4f}{out[k]['OVERCHARGE_RATIO']:>7.2f}")
print()
print('=== LADDER (takeable) ===')
print(f"{'mo':<5}{'B_n':>7}{'B_net':>9}{'C_n':>7}{'C_net':>9}{'D_n':>7}{'D_net':>9}{'E_n':>7}{'E_net':>9}{'pastStop%':>10}")
for k in MO:
    o=out[k]; ps=o['BORN_CENSUS'].get('born_past_stop',{'share':0})
    print(f"{k:<5}{o['B_takeable_only']['n']:>7}{o['B_takeable_only']['net_real']:>9.4f}{o['C_takeable_at_frozen_gate']['n']:>7}{o['C_takeable_at_frozen_gate']['net_real']:>9.4f}{o['D_takeable_at_real_gate']['n']:>7}{o['D_takeable_at_real_gate']['net_real']:>9.4f}{o['E_takeable_real_gate_cheapest_half']['n']:>7}{o['E_takeable_real_gate_cheapest_half']['net_real']:>9.4f}{100*ps['share']:>10.2f}")
print()
print('=== REAL COST DECOMP (R/trade, all rows) + family dispersion ===')
print(f"{'mo':<5}{'spread':>9}{'comm':>9}{'slip':>9}{'famMin':>9}{'famMax':>9}{'famRatio':>9}")
for k in MO:
    d_=out[k]['REAL_COST_DECOMP']; f_=out[k]['FAMILY_REAL_COST_DISPERSION']
    print(f"{k:<5}{d_['spread']:>9.4f}{d_['commission']:>9.4f}{d_['slippage']:>9.4f}{f_['min']:>9.4f}{f_['max']:>9.4f}{f_['ratio']:>9.2f}")
