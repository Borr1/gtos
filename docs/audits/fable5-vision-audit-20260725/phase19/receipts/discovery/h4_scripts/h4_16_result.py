import json
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/'
rr=json.load(open(D+'h4_PERSYMBOL_RERANK_V1.json'))
ct=json.load(open(D+'h4_CORRECTED_TOLL_V1.json'))
hb=json.load(open(D+'h4_HOURBAND_TOLL_V1.json'))
sp=json.load(open(D+'h4_SPREAD_MODEL_TEST_V1.json'))
sl=json.load(open(D+'h4_SLIPPAGE_TRUTH_V1.json'))
cm=json.load(open(D+'h4_COMMISSION_TRUTH_V1.json'))
fz=json.load(open(D+'h4_FROZEN_VS_LIVE_V1.json'))
out={
 "lane":"h4",
 "question":"what we ACTUALLY pay, from the live accounts",
 "scope_note":"execution mechanics and costs only; no P&L of any live-forward trade computed or reported",
 "headline":{
   "published_toll_bps":2.4571,"reproduced_toll_bps":rr['weighted_cost_pub'],
   "live_grounded_toll_bps":rr['weighted_cost_corrected'],
   "all_in_toll_bps":rr['weighted_cost_all_in'],
   "conservative_all_in_toll_bps":round(rr['weighted_cost_corrected']+ct['swap_uncharged_bps']+ct['exit_slip_uncharged_bps']*0.5731,4),
   "ratio_all_in_over_published":round(rr['weighted_cost_all_in']/2.4571,4),
   "weighted_edge_bps":rr['weighted_edge'],
   "edge_over_cost_published":round(rr['weighted_edge']/2.4571,4),
   "edge_over_cost_all_in":round(rr['weighted_edge']/rr['weighted_cost_all_in'],4)},
 "inventory":{
   "sources":12,"positions":cm['n_positions'],"strategy_deals":cm['n_deals'],
   "orders":633,"filled":628,"pending_canceled":2,"rejected":3,"partial_fills":0,
   "reconciled_fills_with_quote":149,"fills_with_req_and_fill_price":140,
   "coverage_utc":["2026-04-27","2026-07-03"],
   "armed_period_placements":0,
   "armed_period_note":"FTMO armed 2026-07-29 12:55Z, FN 2026-07-30 ~05:18Z; packet stream runs to 2026-08-03 and carries zero unit_placed after 2026-07-02",
   "archive_vs_export":"byte-identical (md5) for all four execution logs"},
 "commission":{
   "ftmo_charges_both_sides":True,"redacted_account_charges_entry_only":True,
   "ftmo_crypto_bps_per_side":{"BTCUSD":3.2494,"ETHUSD":3.2497,"n_entry_deals":[15,8]},
   "measured_round_turn_bps":{k:v['comm_rt_bps']['median'] for k,v in cm['per_symbol'].items()},
   "model_defects":{
     "BTCUSD":{"model":4.4332,"live":6.4957,"ratio":round(6.4957/4.4332,3),
       "mechanism":"39.2778 price units measured at BTC 62,502 divided by the POOL median price 88,599.74"},
     "ETHUSD":{"model":3.5803,"live":6.4674,"ratio":round(6.4674/3.5803,3),
       "mechanism":"1.09905 price units frozen at ETH 1,746, applied flat at pool ETH ~3,069"},
     "UKOIL_cash":{"model":0.0,"live":5.1738,"coverage":"TRANSFERRED from redacted_account; identical 100-bbl contract at FTMO"},
     "USOIL_cash":{"model":0.0,"live":5.3706,"coverage":"TRANSFERRED"},
     "XAGUSD":{"model":0.1110,"live":0.3222}}},
 "spread":{"validated_level":True,"model_test_at_149_real_fills":sp,
   "hour_aware_uplift_on_pool":1.1166,
   "worst_per_symbol_ratio":{"UK100":2.6144,"GBPUSD":2.2732,"CHFJPY":1.9641,"GER40":1.7269,"USDJPY":1.6500}},
 "slippage":{"realised_mean_r":sl['pooled_slip_r']['mean'],"realised_mean_bps":sl['pooled_slip_bps']['mean'],
   "realised_median_bps":sl['pooled_slip_bps']['median'],
   "modelled_flat_r":0.02,"modelled_flat_bps_at_live_stops":0.5795,"overcharge_ratio":4.97,
   "share_of_fills_below_model":sl['overcharged_share'],
   "by_session_bps_mean":{k:v['slip_bps']['mean'] for k,v in sl['by_session_trueUTC'].items()},
   "by_broker_bps_mean":{k:v['slip_bps']['mean'] for k,v in sl['by_broker'].items()}},
 "swap":{"pool_rows_crossing_rollover_2h":ct['n_cross'],"share":ct['cross_share'],
   "triple_swap_nights":ct['n_triple'],"uncharged_bps":ct['swap_uncharged_bps'],
   "worst_nightly_bps":{"UKOIL_cash_SHORT":16.199,"NAS100_LONG":2.431,"UK100_LONG":2.365,"SPX500_LONG":2.305}},
 "exit_slippage":{"uncharged_bps":ct['exit_slip_uncharged_bps'],"by_class_bps":ct['exit_slip_by_class_bps'],
   "source":"l10 167 clean stop exits, +0.032236 R, re-denominated at live stop widths"},
 "model_comparison":{"pool_weighted_frozen_bps":6.2599,"pool_weighted_broker_true_bps":2.1309,
   "pool_weighted_live_grounded_bps":2.8871,
   "spearman_frozen_vs_live":0.4261,"spearman_brokertrue_vs_live":0.8974,
   "worst_frozen":{"NAS100":28.032,"SPX500":16.380,"UKOIL_cash":0.199,"USOIL_cash":0.234}},
 "cells":{
   "n_symbols_ratio_gt1_published":1,"n_symbols_ratio_gt1_live_grounded":0,"n_symbols_ratio_gt1_all_in":0,
   "GER40_all_hours":{"edge_bps":0.9107,"toll_pub":0.5012,"ratio_pub":1.387,
     "toll_live":0.9820,"ratio_live":0.927,"toll_all_in":1.5750,"ratio_all_in":0.578},
   "GER40_broker_hours_14_18":{"toll_bps":hb['GER40']['cheapest_toll'],"edge_bps":0.9107,
     "ratio":hb['GER40']['ratio_cheapest_band'],"share_of_rows":hb['GER40']['cheapest_share'],
     "approx_n":round(1858*hb['GER40']['cheapest_share']),
     "caveat":"edge borrowed from the all-hours figure and assumed hour-invariant; not measured by this lane"},
   "intra_symbol_hour_dispersion":{k:hb[k]['dispersion'] for k in sorted(hb,key=lambda k:-hb[k]['dispersion'])[:6]}},
 "replacements":{
   "crypto_commission_ftmo_bps_per_side":3.2494,
   "crypto_commission_redacted_account_bps_entry_only":3.9994,
   "oil_commission_rt_bps":{"UKOIL_cash":5.1738,"USOIL_cash":5.3706},
   "spread_term":"spread_bps_median_by_broker_hour[broker_hour(row)] instead of the flat symbol median",
   "expected_slippage":"0.12 bps of price (not 0.02 R); in R = 0.0012/rd_bps -> 0.0114 R at the pool median",
   "swap_at_2h_bps":0.1402,"exit_slippage_bps":0.4719},
 "artifacts":[ "h4_RESULT.md","h4_LIVE_RECORD_CENSUS_V1.json","h4_packet_inventory.json",
   "h4_ORDER_CENSUS_V1.json","h4_FILL_MECHANICS_V1.json","h4_FILL_LEDGER_RAW.json",
   "h4_FILL_COST_BPS_V1.json","h4_COMMISSION_TRUTH_V1.json","h4_SLIPPAGE_TRUTH_V1.json",
   "h4_SWAP_AT_2H_V1.json","h4_SPREAD_HOURAWARE_V1.json","h4_SPREAD_MODEL_TEST_V1.json",
   "h4_TOLL_DECOMP_V1.json","h4_CORRECTED_TOLL_V1.json","h4_PERSYMBOL_RERANK_V1.json",
   "h4_HOURBAND_TOLL_V1.json","h4_FROZEN_VS_LIVE_V1.json","h4_scripts/"],
 "not_established":[
   "no armed-period (post 2026-07-29) cost evidence exists on this machine",
   "hour-conditional EDGE is unmeasured; the GER40 cell borrows an all-hours edge",
   "FTMO oil commission is TRANSFERRED from redacted_account (identical 100-bbl contract), not measured",
   "exit-slippage bps is re-denominated from l10's live stop widths (~3x the pool's)",
   "per-instrument n is 1-19 positions for most symbols"]}
json.dump(out, open(D+'h4_RESULT.json','w'), indent=1)
print(json.dumps(out['headline'],indent=1))
print('cells',json.dumps(out['cells']['GER40_broker_hours_14_18'],indent=1))
