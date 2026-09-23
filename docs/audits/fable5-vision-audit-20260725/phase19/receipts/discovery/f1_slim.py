import pickle,json
d=pickle.load(open('/tmp/f1/trade_ledgers.pkl','rb'))
F=['candidate_id','decision_time_utc','symbol','direction','side','entry_price','stop_loss',
   'take_profit_1','origin_family','candidate_origin_family','setup_family','effective_order_type',
   'effective_order_type_reason','dynamic_geometry_policy','raw_target_r','policy_target_r',
   'final_r','cost_r','net_r','close_reason','raw_close_reason','policy_close_reason',
   'entry_time_utc','exit_time_utc','approved_risk_pct','risk_cash','risk_per_trade_pct',
   'candidate_confidence','candidate_probability','candidate_ev_r','expectancy_r',
   'spread_r','commission_r','swap_cost_r','expected_cost_r','decision_timeframe',
   'session_bucket','utc_hour_bucket','kill_zone','headline_result_exclusion_reason',
   'selector_action','selector_reason','fill_probability','execution_fill_probability',
   'limit_requested_entry_price','limit_requested_stop_loss','mfe_r','mae_r']
out={}
for w,rows in d.items():
    out[w]=[{k:r.get(k) for k in F} for r in rows]
json.dump(out,open('/tmp/f1/taken_slim.json','w'),indent=0)
r=out['2026-01'][0]
print(json.dumps(r,indent=1))
