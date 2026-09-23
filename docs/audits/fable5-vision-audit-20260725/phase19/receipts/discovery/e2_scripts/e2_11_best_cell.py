"""Final: the best CONDITIONED cell, chosen on JANUARY ONLY, measured on all five months.
Also the direct 'what does fixing the GATE change' number (frozen gate book vs real gate book)."""
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
T={}
for lbl,p,ap in JOBS:
    a=E.load_anchor(ap); rows,_,_=E.build_rows(p,a,precomputed=False)
    T[lbl]=[x for x in rows if x['bs']!='born_past_stop']
MO=list(T)
def bk(rr):
    if not rr: return {'n':0,'gross':None,'real_cost':None,'net_real':None}
    return {'n':len(rr),'gross':E.m_([x['gross'] for x in rr]),'real_cost':E.m_([x['rtot'] for x in rr]),
            'net_real':E.m_([x['gross']-x['rtot'] for x in rr]),
            'net_frozen':E.m_([x['gross']-x['froz_tot'] for x in rr])}
out={'months':MO}
# GATE FIX VALUE
gf={}
for m in MO:
    c=bk([x for x in T[m] if E.gate(x['froz_spr'],x['froz_tot'])])
    d=bk([x for x in T[m] if E.gate(x['rspr'],x['rtot'])])
    gf[m]={'frozen_gate_book':c,'real_gate_book':d,
           'delta_net_real':round(d['net_real']-c['net_real'],6),'n_ratio':round(d['n']/c['n'],4)}
out['GATE_FIX_VALUE']=gf
# CONDITIONED CELL LADDER, all chosen on JANUARY
JF4=['regime_transition_break','volatility_compression_expansion','session_open_range_break','displacement_continuation']
SESS=['london','ny']
cells={
 'cell1_london_ny':lambda x: x['sess'] in SESS,
 'cell2_4fam':lambda x: x['fam'] in JF4,
 'cell3_4fam_x_londonny':lambda x: x['fam'] in JF4 and x['sess'] in SESS,
 'cell4_4fam_x_londonny_x_realgate':lambda x: x['fam'] in JF4 and x['sess'] in SESS and E.gate(x['rspr'],x['rtot']),
 'cell5_2fam_x_londonny_x_realgate':lambda x: x['fam'] in JF4[:2] and x['sess'] in SESS and E.gate(x['rspr'],x['rtot']),
 'cell6_sorb_only':lambda x: x['fam']=='session_open_range_break',
 'cell7_sorb_londonny_realgate':lambda x: x['fam']=='session_open_range_break' and x['sess'] in SESS and E.gate(x['rspr'],x['rtot']),
 'cell8_rtb_only':lambda x: x['fam']=='regime_transition_break',
}
res={}
for nm,fn in cells.items():
    res[nm]={m:bk([x for x in T[m] if fn(x)]) for m in MO}
    gs=[res[nm][m]['gross'] for m in MO if res[nm][m]['n']]
    ns=[res[nm][m]['net_real'] for m in MO if res[nm][m]['n']]
    res[nm]['SUMMARY']={'gross_mean':round(st.mean(gs),6),'net_real_mean':round(st.mean(ns),6),
        'n_total':sum(res[nm][m]['n'] for m in MO),'months_net_positive':sum(1 for v in ns if v>0),
        'months_gross_positive':sum(1 for v in gs if v>0),'worst_month_net':round(min(ns),6),'best_month_net':round(max(ns),6)}
out['CONDITIONED_CELLS']=res
json.dump(out,open(f'{D}/E2_BEST_CELL_V1.json','w'),indent=1)
print('=== GATE FIX VALUE (takeable): frozen-gate book vs real-gate book, at real cost ===')
print(f"{'mo':<5}{'Cn':>7}{'Cnet':>9}{'Dn':>7}{'Dnet':>9}{'delta':>9}{'nRatio':>8}")
for m in MO:
    v=gf[m]; print(f"{m:<5}{v['frozen_gate_book']['n']:>7}{v['frozen_gate_book']['net_real']:>9.4f}{v['real_gate_book']['n']:>7}{v['real_gate_book']['net_real']:>9.4f}{v['delta_net_real']:>9.4f}{v['n_ratio']:>8.2f}")
print(f"{'MEAN':<5}{'':>7}{'':>9}{'':>7}{'':>9}{st.mean([gf[m]['delta_net_real'] for m in MO]):>9.4f}{st.mean([gf[m]['n_ratio'] for m in MO]):>8.2f}")
print()
print('=== CONDITIONED CELLS (all chosen on JANUARY), net@real by month ===')
print(f"{'cell':<36}"+''.join(f'{m:>10}' for m in MO)+f"{'meanNet':>9}{'meanGross':>10}{'N':>7}{'g+':>3}")
for nm in res:
    r=res[nm]; s=r['SUMMARY']
    print(f"{nm:<36}"+''.join(f"{r[m]['net_real']:>10.4f}" if r[m]['n'] else f"{'-':>10}" for m in MO)+f"{s['net_real_mean']:>9.4f}{s['gross_mean']:>10.4f}{s['n_total']:>7}{s['months_gross_positive']:>3}")
print()
print('n per month for the two best cells:')
for nm in ['cell4_4fam_x_londonny_x_realgate','cell7_sorb_londonny_realgate']:
    print(' ',nm,{m:res[nm][m]['n'] for m in MO},'gross',{m:res[nm][m]['gross'] for m in MO})
