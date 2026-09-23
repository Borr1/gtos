# Phase 3 Research Claim Verification Ledger

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Synthesis

All current Phase 3/orderflow claims in this ledger are tied to JSON artifacts. The ledger verifies structural path-scaling signal, V2b prospective blockage, expanded orderflow data coverage, and remaining label/proxy constraints.

## Claims

| Claim | Status | Statement | Key evidence |
|---|---|---|---|
| path_v2_full_corpus_scope | VERIFIED | V2 structural replay used the full available raw-OHLC corpus and kept NO_PROMOTION_VERDICT. | source_scope=FULL_AVAILABLE_CORPUS; rows_replayed=205197; take_rows_seen=23483; setup_ok_rows=12831; first_take_clock=2022-02-07T13:30:00+00:00; last_take_clock=2026-04-30T17:00:00+00:00; promotion_verdict=NO_PROMOTION_VERDICT |
| path_v2_headline_structural_signal | VERIFIED_CONCENTRATION_BLOCKED | The V2 headline structural variant beats J46 on same-dataset net mean R, but is not promotable. | best_structural_variant=STRUCT_SWING_PROTECTED_V2; best_structural_net_mean_r_cost_0.05=0.188405; j46_net_mean_r_cost_0.05=0.163894; delta=0.024511; best_structural_net_sum_r_cost_0.05=853.474166; j46_net_sum_r_cost_0.05=733.751655 |
| path_v2_ob_boundary_next_candidate | VERIFIED_DISCOVERY_ONLY | OB-boundary is the cleanest next structural hypothesis because it is positive versus J46 with lower truncation than swing/FVG. | ob_net_mean_r_cost_0.05=0.177765; ob_net_sum_r_cost_0.05=805.277617 |
| path_v2_composite_rejected | VERIFIED | The composite structural selector underperformed J46 and is rejected as over-locking. | composite_net_mean_r_cost_0.05=0.121828; composite_net_sum_r_cost_0.05=551.883086; j46_net_mean_r_cost_0.05=0.163894; composite_minus_j46=-0.042066; composite_lock_then_stop_rate=0.630583 |
| path_v2b_prospective_blocked | VERIFIED_BLOCKED | V2b has no post-cutoff prospective rows and cannot validate or promote. | validation_status=BLOCKED_NO_PROSPECTIVE_ROWS; rows_after_cutoff=0; wanted_resolved_rows_after_cutoff=0; promotion_verdict=NO_PROMOTION_VERDICT |
| usdjpy_6j_followup | VERIFIED_REVIEW_OPEN | 6J/USDJPY inverse-return mapping is broadly supportive but remains outside the proxy map due one weak strict-correlation window. | all_best_lag_zero=True; corr_pass_count=8; corr_pass_rate=0.888889; median_zero_lag_corr=0.904779; min_directional_agreement=0.928977; min_zero_lag_corr=0.825301; status=REVIEW_REMAINS_OPEN_SINGLE_WEAK_WINDOW; strict_transfer_pass=False |
| orderflow_proxy_expanded_manifest | VERIFIED | The expanded orderflow manifest covers five supported symbols and 241 events. | event_count=241; fetch_group_count=25 |
| orderflow_proxy_expanded_fetch | VERIFIED | The expanded trades-only Databento event-window plan executed under caps. | executed=True; blocked=False; total_estimated_cost_usd=2.909855; max_group_cost_usd=0.750000; max_total_cost_usd=4.000000 |
| orderflow_proxy_expanded_features | VERIFIED_DIAGNOSTIC_ONLY | Trades-level features were extracted for expanded windows, but remain diagnostic only. | feature_rows=324; primary_ok_rows=237; promotion_verdict=NO_PROMOTION_VERDICT |
| orderflow_proxy_expanded_outcomes | VERIFIED_LABEL_CONSTRAINED | Expanded proxy coverage improves synthetic target coverage but still lacks broker actual-R coverage. | candidate_feature_rows=54; join_matched=35; target_available=22; winner_count=12; loser_count=10; actual_realized_r_available=1; actual_feature_candidate_rows=54 |
| orderflow_asof_symbol_contrast | VERIFIED_NO_RULE | As-of orderflow diagnostics are symbol-specific and do not justify a broad rule. | promotion_verdict=NO_PROMOTION_VERDICT |

## Artifacts

| Artifact | Exists | SHA256 | Path |
|---|---:|---|---|
| v2_summary | True | d9cd082c25747c1841a15d9fd2231712c69321f75c67b5f2699f7b84e20b59b7 | `data\external\validation\calendar_macro_bundle_v1\historical_opportunities\raw_ohlc_prequential_replay\path_scaling_v2_structural_levels\raw_ohlc_path_scaling_v2_structural_levels_20260501T223136Z.json` |
| v2_concentration | True | 64b41352f68a2df7118aca9ca3c7f8866d44133ce29b560a23a201dc07c36606 | `research\phase_3_external_feed_validation\RAW_OHLC_PATH_SCALING_V2_CONCENTRATION_VERIFICATION_2026-05-02.json` |
| v2b_prospective | True | fefee6463a3d3677a35cb5690defe077ddf120d598ee291f694f6777c6eb8f20 | `research\phase_3_external_feed_validation\RAW_OHLC_PATH_SCALING_V2B_PROSPECTIVE_VALIDATION_2026-05-02.json` |
| usdjpy_followup_audit | True | 310e1a347c66933b488280660c7ff3f6ad9a804e70d6ffba6273d2f3984aaf51 | `research\databento_orderflow_capture_2026-05-02\USDJPY_6J_INVERSE_RETURN_FOLLOWUP_AUDIT_2026-05-02.json` |
| expanded_manifest | True | 1ef48b9f61fe9080b5c475bd6f5ba59ceafb620485b518a20f8f2e9066983d83 | `research\databento_orderflow_capture_2026-05-02\ORDERFLOW_EVENT_WINDOW_MANIFEST_PROXY_EXPANDED_2026-05-02.json` |
| expanded_fetch_plan | True | 31bb9449bbd49c737091193fe5a56998bfcea07d19d70921205557b82954ceac | `research\databento_orderflow_capture_2026-05-02\ORDERFLOW_EVENT_WINDOW_FETCH_PLAN_PROXY_EXPANDED_2026-05-02.json` |
| expanded_features | True | d233963f449844a9744216d4899a3679938a74e6ccefd92467b4866ccb121879 | `research\databento_orderflow_capture_2026-05-02\ORDERFLOW_EVENT_FEATURE_DIAGNOSTIC_PROXY_EXPANDED_2026-05-02.json` |
| expanded_outcome_join | True | a2346231069494407636c421a26edaba822e281f0d842ed0c924852a41078106 | `research\databento_orderflow_capture_2026-05-02\ORDERFLOW_CANDIDATE_OUTCOME_JOIN_PROXY_EXPANDED_2026-05-02.json` |
| expanded_asof | True | 028b96485c98b6b687cf3b3aa4b5a30a33ee0084d0f1027a746163cf0a28cbc0 | `research\databento_orderflow_capture_2026-05-02\ORDERFLOW_ASOF_SYMBOL_DIAGNOSTIC_PROXY_EXPANDED_2026-05-02.json` |
| expanded_actual_outcome | True | 37555604f4d957adb76312b8802dcb875aa3773f25b10bbc3c869f639bc4e88c | `research\databento_orderflow_capture_2026-05-02\ORDERFLOW_ACTUAL_OUTCOME_COVERAGE_AUDIT_PROXY_EXPANDED_2026-05-02.json` |

## Ambiguity Ledger

- This ledger verifies artifact consistency; it does not create new out-of-sample evidence.
- Path-scaling expectancy remains historical/research-only until prospective rows exist.
- Orderflow expectancy remains unavailable because current labels are sparse and mostly synthetic.
- Databento raw files are intentionally not committed; estimates and metadata are recorded in sidecars/reports.

## Opened Questions

1. Will V2b OB-boundary remain positive on post-cutoff rows?
2. Will USDJPY receive a strict transfer pass or a separately registered robust gate?
3. Can expanded orderflow coverage produce symbol-level winner/loser contrast with actual broker R?
4. Which orderflow feature family deserves pre-registration after enough labels accrue?

## Next Steps

1. Do not promote V2b or orderflow from these claims.
2. Use this ledger as the baseline before any new V2b/orderflow hypothesis registration.
3. Continue forward collection for labels and post-cutoff path-scaling rows.
