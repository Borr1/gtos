import json,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import e2_recost as E
W='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725'
F='/Users/borr/GTOSActive/worktrees/fa2-integration-20260803/docs/audits/fable5-vision-audit-20260725'
D=E.D
JOBS=[('JAN',f'{W}/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz',f'{D}/e2_ANCHOR_JAN.jsonl.gz'),
      ('FEB',f'{W}/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz',f'{D}/e2_ANCHOR_FEB.jsonl.gz'),
      ('APR',f'{F}/phase19/receipts/pools/CS_APRIL_S0R0_POOL_V1.jsonl.gz',f'{D}/e2_ANCHOR_APR.jsonl.gz'),
      ('MAY',f'{F}/phase19/receipts/pools/CS_MAY_S0R0_POOL_V1.jsonl.gz',f'{D}/e2_ANCHOR_MAY.jsonl.gz')]
out={}
for lbl,p,ap in JOBS:
    a=E.load_anchor(ap)
    rows,miss,un=E.build_rows(p,a,precomputed=False)
    r=E.full_report(rows,lbl); r['pool_path']=p; r['anchor_path']=ap; r['missing_symbols']=miss
    out[lbl]=r
json.dump(out,open(f'{D}/E2_MONTHS_ANCHORED_V1.json','w'),indent=1)
hdr=f"{'mo':<5}{'book':<34}{'n':>7}{'gross':>10}{'frozen':>9}{'real':>9}{'netFroz':>10}{'netReal':>10}"
print(hdr)
for lbl in out:
    for bk in ['A_all_rows','B_takeable_only','C_takeable_at_frozen_gate','D_takeable_at_real_gate','E_takeable_real_gate_cheapest_half']:
        b=out[lbl][bk]
        print(f"{lbl:<5}{bk:<34}{b['n']:>7}{b['gross']:>10.4f}{b['frozen_cost']:>9.4f}{b['real_cost']:>9.4f}{b['net_frozen']:>10.4f}{b['net_real']:>10.4f}")
print()
print(f"{'mo':<5}{'OVERCHG':>9}{'ratio':>7}{'takeable':>9}{'pastStop':>9}{'psShare':>9}")
for lbl in out:
    o=out[lbl]; ps=o['BORN_CENSUS'].get('born_past_stop',{'n':0,'share':0})
    print(f"{lbl:<5}{o['OVERCHARGE_R_PER_TRADE']:>9.4f}{o['OVERCHARGE_RATIO']:>7.2f}{o['n_takeable_ex_past_stop']:>9}{ps['n']:>9}{ps['share']:>9.4f}")
