import gzip, json, os, sys
BASE="/Users/borr/GTOSActive/worktrees/fa2-integration-20260803/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse"
ROUTES = {"MAR_R0":"FA2_M_R0"}
TOP=["candidate_id","decision_time_utc","symbol","origin_family","session_bucket","route_session",
 "direction","entry_price","stop_loss","take_profit_1","policy_target_r","raw_target_r",
 "cost_r","expected_cost_r","opportunity_net_proxy_r","opportunity_gross_r","candidate_ev_r",
 "candidate_probability","candidate_confidence","source_completeness","limit_marketable_at_decision",
 "counterfactual_order_fill_status","limit_first_fill_status","limit_first_terminal_outcome",
 "counterfactual_order_terminal_outcome","counterfactual_order_close_mark_r",
 "counterfactual_order_close_time_utc","missed_opportunity_headline_r_scoreable",
 "missed_opportunity_non_executable_diagnostic_scoreable","missed_opportunity_r_scoreability_status",
 "decision_window_id","stable_decision_window_id","trading_day","utc_hour_bucket","final_blocker_class",
 "broker_pretrade_cost_executable","spread_r","commission_r","swap_cost_r","expected_slippage_r",
 "fill_probability","effective_order_type","opportunity_close_reason","opportunity_path_scored",
 "terminal_outcome","scheduler_materialization_status","selector_action","risk_per_trade_pct",
 "decision_timeframe","market_timeframe","kill_zone","pretrade_cost_packet_status"]
CDQ=["execution_fill_probability","entry_quality_fill_probability",
     "predecision_limit_fillability_probability","limit_fillability_probability","candidate_fill_probability"]
for tag,route in ROUTES.items():
    src=os.path.join(BASE,route,route+"_MISSED_OPPORTUNITY_LEDGER.jsonl.gz")
    out="/tmp/e4/%s_slim.jsonl.gz"%tag
    n=0
    with gzip.open(src,"rt") as fh, gzip.open(out,"wt",compresslevel=4) as w:
        for line in fh:
            if not line.strip(): continue
            r=json.loads(line); n+=1
            d={k:r.get(k) for k in TOP}
            q=r.get("candidate_decision_quality") or {}
            if isinstance(q,dict):
                for k in CDQ: d["cdq_"+k]=q.get(k)
            w.write(json.dumps(d)+"\n")
    print(tag,"rows",n,"->",out, flush=True)
print("DONE")
