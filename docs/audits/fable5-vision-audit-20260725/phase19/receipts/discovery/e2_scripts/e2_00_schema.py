import json,gzip,sys
FILES={
 'JAN':'/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz',
 'FEB':'/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz',
 'APR':'/Users/borr/GTOSActive/worktrees/fa2-integration-20260803/docs/audits/fable5-vision-audit-20260725/phase19/receipts/pools/CS_APRIL_S0R0_POOL_V1.jsonl.gz',
 'MAY':'/Users/borr/GTOSActive/worktrees/fa2-integration-20260803/docs/audits/fable5-vision-audit-20260725/phase19/receipts/pools/CS_MAY_S0R0_POOL_V1.jsonl.gz',
}
NEED=['symbol','entry_price','risk_distance','spread_r','expected_cost_r','cost_r','opportunity_net_proxy_r','origin_family','candidate_id','decision_time_utc','stop_loss','take_profit_1','commission_r','swap_cost_r','side','expected_slippage_r']
out={}
for k,p in FILES.items():
    n=0; keys=None; first=None
    for l in gzip.open(p,'rt'):
        r=json.loads(l); n+=1
        if keys is None: keys=set(r.keys()); first=r
        else: keys &= set(r.keys())
    out[k]={'n':n,'n_fields':len(first),'has':{f:(f in keys) for f in NEED}}
    out[k]['missing_from_NEED']=[f for f in NEED if f not in keys]
    out[k]['field_list_sorted']=sorted(first.keys())
json.dump(out,open('/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/E2_SCHEMA_V1.json','w'),indent=1)
for k in out: print(k,'n=',out[k]['n'],'fields=',out[k]['n_fields'],'MISSING:',out[k]['missing_from_NEED'])
