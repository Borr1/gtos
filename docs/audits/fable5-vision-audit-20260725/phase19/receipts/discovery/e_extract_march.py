import gzip, json, collections, os
SRC='/Users/borr/GTOSActive/worktrees/fa2-integration-20260803/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse/FA2_M_R0/FA2_M_R0_MISSED_OPPORTUNITY_LEDGER.jsonl.gz'
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
OUT=os.path.join(D,'e_MARCH_POOL_V1.jsonl.gz')
KEEP=['candidate_id','decision_time_utc','symbol','direction','origin_family','entry_price','stop_loss',
 'take_profit_1','policy_target_r','raw_target_r','risk_distance','risk_per_trade_pct','cost_r','expected_cost_r',
 'spread_r','commission_r','swap_cost_r','expected_slippage_r','opportunity_net_proxy_r','expected_net_r',
 'candidate_probability','candidate_ev_r','expectancy_r','fill_probability','final_blocker_class','route_session',
 'authority_session','session_bucket','kill_zone','scheduler_materialization_status','effective_order_type',
 'effective_selector_action','decision_timeframe','limit_marketable_at_decision','fill_realism_class',
 'missed_opportunity_r_scoreability_status','missed_opportunity_non_executable_diagnostic_scoreable',
 'scheduler_selection_disposition','risk_finalizer_rank','matched_sleeve_count','candidate_confidence']
st=collections.Counter(); fam=collections.Counter(); n=0; kept=0
with gzip.open(OUT,'wt') as w:
    for line in gzip.open(SRC,'rt'):
        if not line.strip(): continue
        r=json.loads(line); n+=1
        st[r.get('missed_opportunity_r_scoreability_status')]+=1
        if r.get('opportunity_net_proxy_r') is None: continue
        if r.get('missed_opportunity_r_scoreability_status')!='diagnostic_opportunity_r_scoreable': continue
        o={k:r.get(k) for k in KEEP}
        o['side']=r.get('direction')
        o['gross_r']=float(r['opportunity_net_proxy_r'])+float(r['cost_r'])
        fam[r.get('origin_family')]+=1
        w.write(json.dumps(o)+'\n'); kept+=1
json.dump({'ledger_rows':n,'pool_rows':kept,'status_census':dict(st),'family_counts':dict(fam)},
          open(os.path.join(D,'e_MARCH_POOL_BUILD_V1.json'),'w'),indent=1)
print('DONE',n,kept)
