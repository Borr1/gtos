import json, os
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260725/'.replace('20260725','20260801') if False else '/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
def L(n):
    p=os.path.join(D,n); return json.load(open(p)) if os.path.isfile(p) else None
out=L('L10_PART1.json')
cs=L('L10_COMM_SWAP_V1.json'); rc=L('L10_REAL_COST_V1.json')['summary']
sm=L('L10_SPREADMODEL_VS_REAL_V1.json')['summary']; sbs=L('L10_SPREADBAND_BY_SYMBOL_V1.json')
ss=L('L10_SPEC_SPREAD_V1.json')['summary']; con=L('L10_CONSTRAINTS_V1.json')
stc=L('L10_STOP_SLIP_CLEAN_V1.json'); stp=L('L10_STOP_SLIP_V1.json')['summary']; em=L('L10_EXIT_MECH_V1.json')
out['F5_commission_truth']=dict(
  claim='Broker commission is exactly $5.00/lot round-turn on every FX pair at BOTH firms, exactly ZERO on every index CFD, and notional-scaled on crypto. In R terms the frozen research model is nearly right on commission (1.08x) - commission is NOT where the cost error lives.',
  ftmo=dict(total_commission_usd=cs['ftmo']['total_commission'], entry_volume_lots=cs['ftmo']['total_entry_volume'],
            blended_per_lot_roundturn=cs['ftmo']['overall_comm_per_lot_roundturn'], fee_total=cs['ftmo']['total_fee']),
  redacted_account=dict(total_commission_usd=cs['redacted_account']['total_commission'], entry_volume_lots=cs['redacted_account']['total_entry_volume'],
            blended_per_lot_roundturn=cs['redacted_account']['overall_comm_per_lot_roundturn'], fee_total=cs['redacted_account']['total_fee']),
  per_symbol_usd_per_lot_roundturn=dict(ftmo={k:v['comm_per_lot_roundturn'] for k,v in cs['ftmo']['per_symbol'].items()},
                                        redacted_account={k:v['comm_per_lot_roundturn'] for k,v in cs['redacted_account']['per_symbol'].items()}),
  fx_rate_usd_per_lot_roundturn=5.0, index_rate_usd_per_lot_roundturn=0.0,
  crypto_rates=dict(ftmo_BTCUSD=-40.02559, ftmo_ETHUSD=-11.33708, redacted_account_BTCUSD=-26.45303, redacted_account_ETHUSD=-0.71599,
                    note='per-lot figures are not constants - crypto commission is a fraction of notional, so USD/lot moves with price and with contract size'),
  commission_r_measured=rc['commission_r'], commission_r_by_class={c:v['commission_r'] for c,v in rc['by_class'].items()})
out['F6_swap_truth']=dict(
  claim='Swap is charged on only 24.29% of live trades and 11-14% of deals, but when it fires it is large: max 0.715 R on a single position. The frozen model UNDER-charges swap by 1.51x.',
  ftmo=dict(total_swap_usd=cs['ftmo']['total_swap'], n_deals_with_swap=cs['ftmo']['n_deals_with_swap'], frac_deals=cs['ftmo']['swap_frac']),
  redacted_account=dict(total_swap_usd=cs['redacted_account']['total_swap'], n_deals_with_swap=cs['redacted_account']['n_deals_with_swap'], frac_deals=cs['redacted_account']['swap_frac']),
  swap_r_measured=rc['swap_r'], n_positions_with_swap=rc['n_swap_nonzero'], frac_positions_with_swap=rc['frac_swap_nonzero'],
  swap_r_by_class={c:v['swap_r'] for c,v in rc['by_class'].items()},
  swap_mode_census=con['swap_modes'], triple_swap_day_census=con['swap_rollover3days'],
  triple_swap_note='swap_rollover3days is 3 (Wednesday) on 23 traded symbols and 5 (Friday) on 19 - the two firms do not share a triple-swap day, so a single global carry rule is wrong for one of them')
out['F7_spread_truth']=dict(
  claim='The truthed spread model at band=mid is VALIDATED against 135 real broker quotes at real fill instants: ratio model/real mean 1.0020, median 1.0000. The high band is NOT a conservative bound - on 8 redacted_account instruments it is 35-43x the real quoted spread, by construction (band_halfwidth_log 3.64774 = e^3.64774 = 38.4x) because those symbols have no bar history.',
  n_real_quotes=135, real_spread_r_at_request=ss['real_spread_r_at_request'],
  live_pretrade_model_equals_captured_quote=dict(model_minus_real_mean=0.0, model_minus_real_max=0.0,
     note='the LIVE cost path uses the broker quote itself (tick_cost.source_status=captured on 140/140); it does not model spread at all'),
  band_ratio_vs_real=dict(low=sm['ratio_model_over_real_low'], mid=sm['ratio_model_over_real_mid'], high=sm['ratio_model_over_real_high']),
  band_ratio_by_symbol=sbs,
  mechanism='src spread model artifact research/operations/spread_model_2026_07_29/SPREAD_MODEL_V1.json: redacted_account index/metal symbols carry no_bar_history=true and era_fallback.band_halfwidth_log=3.64774, described as "p5/p95 of the observed log era ratio across the index class (252 RECORDED eras)" with decidable_at_reference_only=true. e^3.64774 = 38.39x, which is exactly the measured high-band ratio on those symbols (35.9-42.5x).',
  frozen_research_model_spread_r=0.564213, real_spread_r=0.056133, overcharge_ratio=10.051,
  established_claim_tested='7.3-8.5x spread overcharge (January+March). CONFIRMED and slightly larger against real broker quotes: 10.05x on the mean.')
out['F8_total_cost_truth']=dict(
  claim='All-in real broker cost on 140 real fills is 0.150328 R/trade mean, 0.098965 R median. The frozen research model charges 0.663161 R - a 4.411x overcharge whose entire excess is the spread term.',
  n=140, TOTAL_REAL_COST_R=rc['TOTAL_REAL_COST_R'],
  decomposition_real=dict(spread_r=0.056133, commission_r=0.060264, slippage_r=0.013232, swap_r=0.020699, total_r=0.150328),
  decomposition_frozen=dict(spread_r=0.564213, commission_r=0.065220, slippage_r=0.020000, swap_r=0.013720, total_r=0.663161),
  overcharge_ratio=dict(spread=10.051, commission=1.082, slippage=1.511, swap=0.663, total=4.411),
  frozen_source='swarm brief + w0_DATA_DICTIONARY D1/D8, CJ January pool n=27,658',
  caveat='different populations: 140 real FTMO/redacted_account fills 2026-06-18..07-02 across 4 asset classes at live stop geometry, vs 27,658 January diagnostic candidates across 10 families. This is the first real-fill anchor for the cost model, not a like-for-like replacement.',
  by_class={c:dict(n=v['n'],spread_r=v['spread_r']['mean'],commission_r=v['commission_r']['mean'],swap_r=v['swap_r']['mean'],
                   slippage_r=v['slippage_r']['mean'],total_r=v['total_r']['mean']) for c,v in rc['by_class'].items()},
  by_account={a:dict(n=v['n'],total_r=v['total_r']) for a,v in rc['by_account'].items()},
  live_gate=dict(max_spread_r_standard=0.10, max_total_cost_r_standard=0.15,
     per_sleeve_override=dict(max_spread_r=0.35, max_total_cost_r=0.45, sleeves=['fx_jpy','fx_jpy_ny'], n_fills=32),
     standard_gate_fills=117, fills_exceeding_own_limit=0, pretrade_status_PASSED=149,
     config_lines='config/agent_config.yaml:715 (max_spread_r 0.10), :716 (max_total_cost_r 0.15), :724 by_sleeve spread, :727 by_sleeve total, :740 slippage 0.02'),
  gate_pass_at_real_cost=dict(real_spread_r_over_0p10=dict(n=21,frac=0.15),
     real_all_in_over_0p15=dict(n=59,frac=0.4214),
     by_class_spread_over_0p10=dict(fx=0.389,crypto=0.0,index=0.0,metals=0.0),
     by_class_total_over_0p15=dict(fx=0.852,crypto=0.478,index=0.041,metals=0.0)))
out['F9_stop_slippage']=dict(
  claim='The research walk assumes a stop fills exactly at -1R. Real stops fill 0.0322 R WORSE than their own price on average (n=167), 83.8% adverse, p95 +0.10 R, worst +0.9355 R. Nothing in the cost model carries this.',
  n_clean=stc['clean_n'], clean_stats=stc['clean_stats'], by_class=stc['by_class'],
  frac_exact=0.1317, frac_adverse=0.8383,
  tail=dict(worse_than_0p02R=dict(n=58,frac=0.3473), worse_than_0p05R=dict(n=30,frac=0.1796),
            worse_than_0p10R=dict(n=8,frac=0.0479), worse_than_0p25R=dict(n=2,frac=0.012)),
  worst_events=stp['sl_worst'],
  method='SL in force at the exit reconstructed from the runtime sltp_modify_result timeline (271 rows, retcode 10009 only) applied over the entry order SL; 92 of 300 positions have a captured modify timeline. Clean population excludes 13 exits whose price beat their recorded stop by more than 0.02 R - those are stale-SL coverage artifacts (a stop cannot fill materially better than its own price), not price improvement.',
  target_slippage_r=stp['tp_slip_r'],
  pool_impact_estimate=dict(note='the January pool takes a full stop on 54.4% of candidates; at the measured 0.0322 R/stop that is 0.0175 R/trade of cost the research model does not charge',
                            value_r_per_trade=round(0.544*0.032236,6)))
out['F10_exit_mechanics']=dict(
  claim='79% of FTMO exits and 69% of redacted_account exits are executed by the BROKER (resting SL/TP), not by the book. Positions are managed by the server far more than by the engine.',
  ftmo=dict(exit_reason=em['ftmo']['exit_reason'], broker_sl=em['ftmo']['exit_share_broker_sl'], broker_tp=em['ftmo']['exit_share_broker_tp'],
            book_expert=em['ftmo']['exit_share_book_expert'], manual=em['ftmo']['exit_share_manual'],
            positions=em['ftmo']['n_positions'], multi_exit=em['ftmo']['n_positions_multi_exit_deal'], multi_exit_frac=em['ftmo']['frac_multi_exit']),
  redacted_account=dict(exit_reason=em['redacted_account']['exit_reason'], broker_sl=em['redacted_account']['exit_share_broker_sl'], broker_tp=em['redacted_account']['exit_share_broker_tp'],
            book_expert=em['redacted_account']['exit_share_book_expert'], manual=em['redacted_account']['exit_share_manual'],
            positions=em['redacted_account']['n_positions'], multi_exit=em['redacted_account']['n_positions_multi_exit_deal'], multi_exit_frac=em['redacted_account']['frac_multi_exit']),
  partial_fills=dict(n_orders_state_PARTIAL=0, n_filled_with_residual_volume=0, n_positions_partially_closed_and_left_open=0,
                     note='ZERO partial fills in 633 orders at either broker'))
out['F11_broker_behaviour']=dict(
  claim='Zero requotes, zero invalid-stops, zero price-changed, zero partial fills in the entire live history. But 24.65% of all order_sends are SL/TP modifies that change nothing, and 8 SL/TP modifies were refused MARKET_CLOSED on German index CFDs before the cash open - a silently failed protective move.',
  retcode_census=con['retcode_by_stage'], result_comments=con['result_comments'],
  never_seen=dict(REQUOTE_10004=0, INVALID_STOPS_10016=0, PRICE_CHANGED_10020=0, DONE_PARTIAL_10010=0, TIMEOUT_10012=0, NO_MONEY_10019=0, TOO_MANY_REQUESTS_10024=0),
  wasted_modifies=dict(n=106, of_total_order_sends=430, frac=0.2465),
  market_closed=dict(n=8, events=con['market_closed_events'],
     reading='all 8 are GER40.cash / GER30 SL-TP modifies at 07:52-07:59 UTC on 2026-06-27, before the German cash index opens. The book retried 1 s later and was refused again. A trail/BE/stop move attempted before the underlying opens silently does not happen.'),
  stop_level_constraints=dict(n_symbols=con['n_symbols'], n_with_nonzero_trade_stops_level=con['n_symbols_with_stops_level'],
     nonzero=con['nonzero_stops_level'], nonzero_freeze_level=con['nonzero_freeze_level'],
     reading='trade_stops_level is 0 on 40 of 42 traded symbols (1 point on redacted_account BTCUSD/ETHUSD) and trade_freeze_level is 0 everywhere. There is effectively NO broker minimum stop distance to model at either firm.'),
  order_result_price=dict(n=430, n_zero=430, frac_zero=1.0,
     reading='MT5 order_send returns price=0.0 on 430 of 430 results at BOTH brokers. Any code that reads result.price as the fill price gets zero, always. The fill price is recoverable only from account history - which is exactly what deal_cost_reconciliation does (RECONCILED_FROM_ACCOUNT_HISTORY on 140/149, UNRESOLVED on 9). src/components/execution.py:7007-7030 already carries a documented fallback for this.'))
out['F12_nofill_logger_is_empty']=dict(
  claim='The infrastructure built to answer "did the limit fill" has never captured a single usable observation. All 446 rows of nofill_forward_source_capture.jsonl are fail-closed placeholders.',
  n_rows=446, window=['2026-05-10T16:30:00+00:00','2026-06-02T07:00:00Z'],
  statuses=dict(native_pending_order_type_status='SOURCE_FIELD_MISSING_FAIL_CLOSED on 446/446',
    cancel_expiry_reason_status='LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED on 446/446',
    entry_touch_spread_status='QUOTE_SNAPSHOT_MISSING_FAIL_CLOSED on 446/446',
    side_aware_entry_touch_status='LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED on 446/446',
    protective_area_touch_status='LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED on 446/446',
    terminal_area_touch_status='LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED on 446/446',
    execution_quality_label_status='EXECUTION_QUALITY_LABEL_CLOSED_NOT_EMITTED on 446/446',
    slippage_label_status='SLIPPAGE_LABEL_CLOSED_NOT_EMITTED on 446/446',
    same_tick_same_bar_ambiguity_status='UNRESOLVED_REQUIRES_FORWARD_PATH_JOIN on 446/446',
    entry_touch_first_utc='the literal string LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED on 446/446',
    cancel_expiry_utc='same, 446/446'),
  the_32=dict(n=32, broker_pending_order_created_status='BROKER_PENDING_ORDER_CREATED_FALSE_STATUS_ONLY',
     pending_order_mode_source_safe='INTERNAL_CANDLE_POLLED_INTENT',
     reading='the only 32 rows that carry a pending-order mode say the pending order was an INTERNAL POLLED INTENT and that no broker pending order was created. This corroborates F1 independently.'),
  degraded_secondary_source=dict(file='slippage.jsonl', n_rows=192, n_with_both_prices=79,
     verdict='UNUSABLE for slippage: displacement in R has mean 1.07e12 and max 7.28e13, with a mass at exactly +-1.0 R - the entry_price and sl_distance fields are not on a common basis. It belongs to the pre-W7 agent (2026-05-11..2026-06-03). Reported as a data-quality fact, not used for any number here.'))
json.dump(out,open(D+'/l10_RESULT.json','w'),indent=1)
print('keys',list(out.keys())); print('written', D+'/l10_RESULT.json')
