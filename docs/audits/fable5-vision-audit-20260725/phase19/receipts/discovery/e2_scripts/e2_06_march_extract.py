"""Build a January-comparable March diagnostic pool by streaming the raw missed-opportunity ledger
and applying the SAME scoreability gate that built CJ_RECLOCKED (w0 dictionary D3)."""
import json,gzip,os
from collections import Counter
SRC='/Users/borr/GTOSActive/worktrees/fa2-integration-20260803/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse/FA2_M_R0/FA2_M_R0_MISSED_OPPORTUNITY_LEDGER.jsonl.gz'
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
KEEP=['candidate_id','decision_time_utc','symbol','direction','entry_price','stop_loss','take_profit_1',
 'spread_r','cost_r','expected_cost_r','opportunity_net_proxy_r','origin_family',
 'commission_r','swap_cost_r','expected_slippage_r','session_bucket','final_blocker_class',
 'missed_opportunity_r_scoreability_status','headline_r_scoreable','policy_target_r','raw_target_r',
 'missed_opportunity_non_executable_diagnostic_scoreable','missed_opportunity_cost_opportunity_scoreable']
stat=Counter(); nkept=0; ntot=0; seen=set(); nodata=Counter()
with gzip.open(f'{D}/e2_MARCH_R0_POOL_V1.jsonl.gz','wt') as f:
    for l in gzip.open(SRC,'rt'):
        r=json.loads(l); ntot+=1
        if not seen: seen=set(r.keys())
        s=r.get('missed_opportunity_r_scoreability_status'); stat[str(s)]+=1
        if s!='diagnostic_opportunity_r_scoreable': continue
        if r.get('opportunity_net_proxy_r') is None: nodata['no_proxy']+=1; continue
        ep,sl=r.get('entry_price'),r.get('stop_loss')
        if ep is None or sl is None or not abs(float(ep)-float(sl))>0: nodata['bad_geometry']+=1; continue
        o={k:r.get(k) for k in KEEP}; o['side']=o.get('direction')
        f.write(json.dumps(o)+'\n'); nkept+=1
res={'source':SRC,'ledger_rows':ntot,'kept':nkept,'scoreability_status_census':dict(stat),
 'dropped_after_status_gate':dict(nodata),'n_source_fields':len(seen),
 'KEEP_missing_from_source':[k for k in KEEP if k not in seen]}
json.dump(res,open(f'{D}/E2_MARCH_EXTRACT_V1.json','w'),indent=1)
print(json.dumps(res,indent=1)[:1200])
