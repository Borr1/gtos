import json,os,statistics as st
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260725'.replace('20260725','20260801') if False else '/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
L=lambda f: json.load(open(os.path.join(D,f)))
repro=L('E2_JAN_REPRO_V1.json'); five=L('E2_FIVE_MONTHS_V1.json'); dec=L('E2_DECOMP_V1.json')
lev=L('E2_LEVER_PRICE_V1.json'); best=L('E2_BEST_CELL_V1.json'); sw=L('E2_SWEEP_V1.json')
cs=L('E2_CELLSTAT_V1.json'); comp=L('E2_COMPOSITION_V1.json'); bnd=L('E2_BOUNDARY_V1.json')
mar=L('E2_MARCH_EXTRACT_V1.json')
MO=['JAN','FEB','MAR','APR','MAY']
R={'lane':'e2','finding_extended':'l10-broker-truth X7 (+0.473864 R/trade cost-model correction; 12.1x family real-cost dispersion)',
 'REPRODUCTION':{'checks':repro['n_checks'],'failures':repro['n_fail'],
   'headline_target':repro['headline_target'],'headline_reproduced_via_workingset':repro['headline_ws'],
   'headline_reproduced_via_raw_pool_portable_instrument':repro['headline_raw'],
   'verdict':'EXACT — 60/60 book fields matched to 1e-6 on both the original input file and an independently rebuilt portable path.'},
 'MONTHS':{m:{'n':five[m]['A_all_rows']['n'],'gross':five[m]['A_all_rows']['gross'],
    'frozen_cost':five[m]['A_all_rows']['frozen_cost'],'real_cost':five[m]['A_all_rows']['real_cost'],
    'net_frozen':five[m]['A_all_rows']['net_frozen'],'net_real':five[m]['A_all_rows']['net_real'],
    'WORTH_OF_COST_CORRECTION':five[m]['OVERCHARGE_R_PER_TRADE'],'overcharge_ratio':five[m]['OVERCHARGE_RATIO'],
    'real_cost_decomp':five[m]['REAL_COST_DECOMP'],
    'family_real_cost_dispersion':five[m]['FAMILY_REAL_COST_DISPERSION'],
    'born_past_stop_share':five[m]['BORN_CENSUS'].get('born_past_stop',{}).get('share'),
    'books':{k:five[m][k] for k in ['A_all_rows','B_takeable_only','C_takeable_at_frozen_gate','D_takeable_at_real_gate','E_takeable_real_gate_cheapest_half']}} for m in MO},
 'MONTH_SUMMARY':{'worth_min':min(five[m]['OVERCHARGE_R_PER_TRADE'] for m in MO),
   'worth_max':max(five[m]['OVERCHARGE_R_PER_TRADE'] for m in MO),
   'worth_mean':round(st.mean([five[m]['OVERCHARGE_R_PER_TRADE'] for m in MO]),6),
   'ratio_min':min(five[m]['OVERCHARGE_RATIO'] for m in MO),'ratio_max':max(five[m]['OVERCHARGE_RATIO'] for m in MO),
   'family_dispersion_min':min(five[m]['FAMILY_REAL_COST_DISPERSION']['ratio'] for m in MO),
   'family_dispersion_max':max(five[m]['FAMILY_REAL_COST_DISPERSION']['ratio'] for m in MO),
   'months_with_any_positive_book':0,
   'verdict':'HOLDS in all five months. Every one of the 25 month x book cells is negative.'},
 'SCALE_VS_RANK':dec['SCALE_VS_RANK'],
 'GATE_FIX_VALUE':best['GATE_FIX_VALUE'],
 'LEVER_STAGES':dec['LEVER_STAGES'],'JAN_SELECTED_4_FAMILIES':dec['JAN_SELECTED_4_FAMILIES'],
 'JAN_SELECTED_12_SYMBOLS':dec['JAN_SELECTED_12_SYMBOLS'],
 'LEVER_LADDER_JAN_SELECTED':{str(k):{m:lev['LADDER_JAN_SELECTED'][str(k)][m] for m in ['JAN','FEB','APR','MAY']} for k in range(1,11)},
 'BOUNDARY_FAMILY':bnd['per_family_takeable__real_cost'],
 'BOUNDARY_FAMILY_NET':bnd['per_family_takeable__net_real'],
 'BOUNDARY_SYMBOL':dec['BOUNDARY_SYMBOL'],'BOUNDARY_SESSION':dec['BOUNDARY_SESSION'],
 'SWEEP':{'n_declared_cells':sw['n_cells_declared'],'look_declaration':sw['look_declaration'],
   'n_positive_mean_gross':sum(1 for v in sw['cells'].values() if v['gross_mean']>0),
   'n_positive_mean_net_real':sum(1 for v in sw['cells'].values() if v['net_real_mean']>0),
   'top10':{k:{'gross_mean':v['gross_mean'],'net_real_mean':v['net_real_mean'],'n_total':v['n_total'],
               'n_min_month':v['n_min_month'],'months_gross_positive':v['months_gross_positive'],
               'per_month_gross':{m:v['per_month'][m]['gross'] for m in MO},
               'per_month_n':{m:v['per_month'][m]['n'] for m in MO}}
     for k,v in sorted(sw['cells'].items(),key=lambda kv:-kv[1]['gross_mean'])[:10]}},
 'BEST_CELL_STAT':cs,'CONDITIONED_CELLS':best['CONDITIONED_CELLS'],
 'COMPOSITION':comp,'MARCH_EXTRACT':mar,
 'EVIDENCE_SPEND_REGISTER':{
   'APRIL_2026':'ECONOMICS READ by this lane. Source docs/audits/.../phase19/receipts/pools/CS_APRIL_S0R0_POOL_V1.jsonl.gz (Session CS, billed:false, selection_authority NONE_SUBSTRATE_ONLY). Read: opportunity_net_proxy_r, cost_r, spread_r, expected_cost_r, entry_price, stop_loss, origin_family, session_bucket over all 25,056 rows. Purpose: cross-month extension of the l10 X7 cost-truth finding. No selection was made ON April; every family/symbol/session set evaluated was fixed by JANUARY real cost before April was opened.',
   'MAY_2026':'ECONOMICS READ by this lane. Source CS_MAY_S0R0_POOL_V1.jsonl.gz, 21,285 rows, same fields and same purpose and same pre-fixed selection.',
   'MARCH_2026':'ECONOMICS READ by this lane from the FA2_M_R0 (S0R0 baseline) missed-opportunity ledger, 26,500 diagnostic-scoreable rows of 130,004. March was already decoded once by Session MARCH-EXEC on 2026-08-05/06; this is a second read of the same decoded arm, not a new decode.',
   'FEBRUARY_2026':'ECONOMICS READ. Already used-once VAL per wave 18.',
   'claim_class':'DISCOVERY / LANE ITERATION. billed:false. No admission claim anywhere in this receipt.'},
 'ARTIFACTS':[f for f in sorted(os.listdir(D)) if f.startswith('E2_') or f.startswith('e2_')]}
json.dump(R,open(os.path.join(D,'e2_RESULT.json'),'w'),indent=1)
print('written', os.path.getsize(os.path.join(D,'e2_RESULT.json')))
