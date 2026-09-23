# vNext Replacement Production Candidate Contract - 2026-05-26

Route: `vnext_moonshot_production_replacement_activation_2026_05_26`

## Contract Boundary

This contract freezes the Stage 03 replacement target. It does not apply the activation overlay. Stage 04 must implement the runtime behavior, Stage 05/06 must replay and delta-test it, and Stage 11/13 may apply the overlay only after semantic gates pass.

## Candidate Universe

- Denominator rows: `903163`
- Generated candidate rows: `253234`
- Moonshot replayable rows: `214536`
- Repaired executable stream rows: `79320`
- Full Stage04 path rows: `1978947`
- No FVG subset, top-N, or selected-only summary can satisfy activation proof.

Framework counts:
| Framework | Rows |
| --- | --- |
| breaker_re_entry | 69502 |
| fvg_fill | 106679 |
| ob_retest | 77053 |

## Candidate Origins

All registry rows are preserved in the JSON contract. Current GTOS frameworks remain baseline/comparator origins; new origin families require source availability, activation exclusion, or forward-capture rules before they can affect execution.
| Origin | Category | Source Status | Current GTOS Status | Next Replay Action |
| --- | --- | --- | --- | --- |
| ob_retest | current_gtos_framework | available | active_baseline | keep_as_baseline_comparator |
| fvg_fill | current_gtos_framework | available | active_baseline | keep_as_baseline_comparator |
| breaker_re_entry | current_gtos_framework | available | active_baseline | keep_as_baseline_comparator |
| liquidity_sweep_reclaim | liquidity_and_stop_cascade | available | shadow_or_partial_diagnostic | build_sweep_reclaim_candidate_generator |
| displacement_continuation | impulse_path_geometry | available | shadow_diagnostic | build_displacement_continuation_generator |
| continuation_no_retrace | impulse_path_geometry | available | shadow_diagnostic | convert_cnr_shadow_to_candidate_generator |
| nofill_reprice_reentry | pending_lifecycle | forward_capture_required_for_exact_historical_truth | repair_needed | build_forward_capture_then_replay_reprice_rules |
| volatility_compression_expansion | volatility_state | available | not_first_class_candidate_origin | build_volatility_state_origin_generator |
| session_open_range_break | session_clock | available | not_first_class_candidate_origin | build_session_open_range_generator |
| regime_transition_break | regime_state | available | shadow_context | build_regime_transition_origin_generator |
| orderflow_depth_imbalance_proxy | microstructure_orderflow | available_but_parser_or_quote_contract_required | source_limited_shadow | build_proxy_packet_then_candidate_generator |
| spread_liquidity_state_shift | execution_microstructure | available_but_parser_or_quote_contract_required | not_first_class_candidate_origin | build_spread_state_origin_or_filter_comparator |
| news_volatility_reprice | calendar_macro | available | filter_context | build_calendar_window_origin_generator |
| cross_asset_lead_lag | cross_market_context | available | risk_gate_context | build_lead_lag_origin_generator |
| path_hazard_early_failure | survival_hazard | available | not_first_class_entry_or_exit_origin | build_hazard_state_exit_and_entry_comparator |
| structural_distance_extreme | geometry_topology | available | passive_feature_or_prompt_context | build_structural_distance_origin_generator |

## Semantics

- `FOLLOW`: can proceed through mechanical route, AI-narrowed route, risk modification, LTF monitoring, or prop-governed allow, while hard safety remains mandatory.
- `AVOID`: can block, zero risk, skip AI, defer, or require repair only when source-bound evidence supports it.
- `MIXED`: must resolve, fall back, exclude, request source capture, or use a budgeted AI resolver. It cannot remain inert.
- `LEGACY`: comparator, rollback, or explicit row-level fallback only. It cannot dominate activated behavior without test proof.

## Dynamic Execution

Primary policy frozen for implementation: `be_after_trigger` because highest expectancy among activation-candidate dynamic policies in Stage04 dynamic replay.
| Policy | Runtime Role | Rows | Total R | Expectancy R |
| --- | --- | --- | --- | --- |
| live_current_j46_j49 | comparator_and_rollback_only | 214536 | 38663.2722865153 | 0.18021810925213155 |
| legacy_fixed_1.5r | fixed_r_comparator_only_not_activation_truth | 214536 | 80776.05194895089 | 0.3765151394122706 |
| ai_target | ai_calibrated_only_after_budgeted_validation | 214536 | 80776.05194895089 | 0.3765151394122706 |
| partial_be_runner | activation_candidate_dynamic_policy | 214536 | 67480.977363153 | 0.3145438404890228 |
| be_after_trigger | activation_candidate_dynamic_policy | 214536 | 83555.67921897746 | 0.3894716001928695 |
| trailing_runner | activation_candidate_dynamic_policy | 214536 | 59910.137747734196 | 0.2792544735975976 |
| time_stop_only | activation_candidate_dynamic_policy | 214536 | 35889.65814266152 | 0.16728967698969646 |
| early_cut_if_no_progress | activation_candidate_dynamic_policy | 214536 | 80771.71024283684 | 0.37649490175465583 |
| path_aware_runner | activation_candidate_dynamic_policy | 214536 | 38663.2722865153 | 0.18021810925213155 |

J46/J49 and fixed 1.5R are comparator/rollback surfaces, not final moonshot execution truth.

## Prop Governor

Primary prop policy: `ACCOUNT_ABANDON_OR_RESTART`.
Allowed actions are `ALLOW`, `REDUCE_RISK`, `MICRO_RISK`, `DEFER_UNTIL_RESET`, `ACCOUNT_ABANDON_OR_RESTART`, and row-level `BLOCK` only with negative-EV proof. Broad safe-but-dead blockers fail this contract.

## AI And ML

- Paid AI/vendor calls allowed now: `False`
- Route-state budget cap: `None`
- AI cannot be used as production selector until Stage09 writes the calibration package and budget cap.
- ML is monitoring/assistant only until sealed validation and no-leak tests approve live control.
| Role | Disposition | Runtime Interaction |
| --- | --- | --- |
| ML ranker for candidate quality | weak_ranker_monitor_only | ML may rank source-complete candidates before AI spend; activation requires separate validation. |
| ML risk reducer | weak_shadow_signal_monitor_only | ML may size down high stop-first probability classes in shadow only until validated. |
| ML no-fill/stop-first blocker | not_useful_as_standalone_challenger | ML may flag path/fill risk for LTF monitoring; no execution block without production-change dossier. |
| ML timeout/ambiguous monitor | shadow_candidate_promising_not_activation_approved | Drift monitor logs distribution shifts; no direct execution effect. |
| ML AI-call reducer | shadow_candidate_promising_not_activation_approved | ML may reduce paid AI calls only after actual AI labels confirm no false skip risk. |
| ML source-confidence scorer | shadow_candidate_promising_not_activation_approved | ML may prioritize source capture and repair; it cannot convert missing source into truth. |
| ML partition robustness scorer | shadow_candidate_promising_not_activation_approved | ML may score partition robustness from train-only labels; full-sample Stage05 classifications remain diagnostic only. |
| ML prop-pass probability scorer | weak_shadow_signal_monitor_only | ML may rank trades near prop constraints by opportunity-adjusted EV in shadow. |
| ML drift detector | shadow_drift_monitor_ready | Drift monitor logs distribution shifts; no direct execution effect. |

## Source Capture

Forward capture fields frozen by the contract:

- `broker_order_id`
- `broker_deal_id`
- `requested_entry_price`
- `executed_entry_price`
- `requested_exit_price`
- `executed_exit_price`
- `fill_time_utc`
- `close_time_utc`
- `bid_ask_ordered_path`
- `spread`
- `slippage`
- `commission`
- `swap`
- `partial_close_lifecycle`
- `breakeven_modify_lifecycle`
- `trailing_modify_lifecycle`
- `time_stop_lifecycle`
- `pending_order_lifecycle`
- `cancel_expire_lifecycle`
- `source_join_ids`
- `candidate_id`
- `policy_hash`
- `prompt_hash`
- `ai_response_id`
- `runtime_branch_label`
- `runtime_policy_label`
- `prop_governor_decision_fields`
- `source_completeness`
- `source_ambiguity`

Historical broker/order/intent lifecycle truth cannot be backfilled from price movement. Missing historical system-state truth is excluded or repaired only from existing source-safe logs.

## Activation Flags

Observed base flags remain apply-off. Stage11/13 can apply the activation overlay only after runtime tests, activated replay, semantic verification, rollback proof, monitoring checklist, and scoped commit checks pass.

## Failure Gates

- `old_gtos_still_primary_under_activation`
- `moonshot_router_not_runtime_wired`
- `j46_j49_or_fixed_1_5r_dominates_activated_exit`
- `fvg_subset_or_top_n_proof`
- `failed_10_trade_route_reproduced`
- `broad_prop_or_avoid_blocker_without_negative_ev_proof`
- `mixed_or_legacy_inert_terminal_labels`
- `no_paid_ai_diagnostic_treated_as_production_selector`
- `source_missing_rows_activated_without_capture_or_exclusion`
- `selected_coverage_silent_shrink`
- `config_gated_state_used_as_terminal_excuse`
- `artifact_existence_treated_as_completion`

## Next Invariant

`stage_04_runtime_implementation_pending`
