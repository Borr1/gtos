import json,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import e2_recost as E
D=E.D
anch=E.load_anchor(f'{D}/w0cap2_DECISION_ANCHOR_V1.jsonl.gz')
# path 1: EXACT reproduction — same input file (working set, precomputed d & gross_r)
rows_ws,miss_ws,un_ws=E.build_rows(f'{D}/w0_WORKING_SET.jsonl.gz',anch,precomputed=True)
rep_ws=E.full_report(rows_ws,'JAN_via_workingset')
# path 2: PORTABLE path — raw pool, d and gross_r recomputed from first principles
rows_raw,miss_raw,un_raw=E.build_rows('/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz',anch,precomputed=False)
rep_raw=E.full_report(rows_raw,'JAN_via_rawpool_PORTABLE')
TARGET=json.load(open(f'{D}/L10X_BOTTOMLINE_V1.json'))
checks=[];
for bk in ['A_all_rows','B_takeable_only','C_takeable_at_frozen_gate','D_takeable_at_real_gate','E_takeable_real_gate_cheapest_half']:
    for f in ['n','gross','frozen_cost','real_cost','net_frozen','net_real']:
        t=TARGET[bk][f]
        for lbl,rep in [('ws',rep_ws),('raw',rep_raw)]:
            g=rep[bk][f]
            ok = (t==g) if f=='n' else (abs(t-g)<=1e-6)
            checks.append({'book':bk,'field':f,'variant':lbl,'target':t,'got':g,'match':ok})
res={'n_checks':len(checks),'n_fail':sum(1 for c in checks if not c['match']),
 'fails':[c for c in checks if not c['match']],
 'headline_target':round(TARGET['A_all_rows']['frozen_cost']-TARGET['A_all_rows']['real_cost'],6),
 'headline_ws':rep_ws['OVERCHARGE_R_PER_TRADE'],'headline_raw':rep_raw['OVERCHARGE_R_PER_TRADE'],
 'missing_symbols_ws':miss_ws,'missing_symbols_raw':miss_raw,'unusable_raw':un_raw,
 'JAN_ws':rep_ws,'JAN_raw':rep_raw}
json.dump(res,open(f'{D}/E2_JAN_REPRO_V1.json','w'),indent=1)
print('checks',res['n_checks'],'fails',res['n_fail'])
print('headline target',res['headline_target'],'ws',res['headline_ws'],'raw',res['headline_raw'])
for c in res['fails'][:12]: print('FAIL',c)
print('missing raw',miss_raw,'unusable raw',un_raw)
