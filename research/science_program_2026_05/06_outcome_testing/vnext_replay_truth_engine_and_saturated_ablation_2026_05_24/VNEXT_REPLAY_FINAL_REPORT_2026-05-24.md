# VNEXT Replay Final Truth Freeze - 2026-05-24

## Verdict

The replay truth package is complete for the approved offline evidence class. No production/live trading change is promoted from this session.

Hypothetical vNext activation is a protective, default-off candidate: replay proxy total R improved from -59.0R to +1.5R and max drawdown improved from -63.5R to 0.0R, but entry-touched trades collapsed from 100 to 1. That is not a production-ready profit engine.

## Core Counts

| Metric | Value |
| --- | --- |
| event groups | 1635 |
| source event rows | 23042 |
| saturated replay rows | 3270 |
| runtime artifact paths loaded | 153 |
| runtime artifact rows loaded | 661344 |
| ablation rows | 2094510 |
| MIXED resolution rows | 1534 |
| robustness rows | 4796 |
| Stage08 repair rows | 50 |

## Outcomes

| Mode | Total R | Entry-Touched | Terminal Trades | Terminal WR | Max DD R | Daily DD R | Max Loss Streak |
| --- | --- | --- | --- | --- | --- | --- | --- |
| current_config_shadow | -59.0 | 100 | 69 | 0.057971014493 | -63.5 | -28.0 | 10 |
| hypothetical_activated_vnext | 1.5 | 1 | 1 | 1.0 | 0.0 | 0.0 | 0 |

Activation delta: {"effective_r_total_delta_hypothetical_minus_current": 60.5, "max_drawdown_r_delta_hypothetical_minus_current": 63.5, "trade_count_delta_hypothetical_minus_current": -99}

## System Behavior

The replay called the current vNext runtime surfaces through the Stage03 harness and preserved current shadow/default-off behavior separately from hypothetical activation. Decision distributions from Stage05:

| Metric | Distribution |
| --- | --- |
| route decisions | {"current_config_shadow":{"AVOID":296,"FOLLOW":114,"LEGACY":2,"MIXED":121,"None":1102},"hypothetical_activated_vnext":{"AVOID":296,"FOLLOW":114,"LEGACY":2,"MIXED":121,"None":1102}} |
| pre-AI actions | {"current_config_shadow":{"ALLOW_AI":1635},"hypothetical_activated_vnext":{"NARROW_AI_EXCLUDE_FRAMEWORKS":1457,"SKIP_AI_AVOID_ONLY":178}} |
| risk multipliers | {"current_config_shadow":{"0.0":531,"1.0":2,"None":1102},"hypothetical_activated_vnext":{"0.0":531,"1.0":2,"None":1102}} |

Rows without enough post-L2 fields remain explicit source-repair limitations, not hidden performance rows: {"PRE_AI_ONLY_INSUFFICIENT_POST_L2_FIELDS":1102,"RUNTIME_EVALUATED_WITH_PATH_SUMMARY":529,"RUNTIME_REFERENCE_ONLY_NOT_PERFORMANCE_DENOMINATOR":4}

## M15 And Path Blindness

Path reconstruction wrote 56226 rows. M15 bar-close had lower-timeframe/tick/OHLC comparisons in 578 groups; 162 groups disagreed with lower-path labels, a rate of 0.280276816609.

Path mode counts: {"bar_close_m15":6974,"current_config_shadow":4,"hypothetical_activated_vnext":4,"m1_path_aware":14154,"m5_path_aware":368,"missing_source":27573,"ohlc_only_proxy":368,"tick_or_sierra_path_aware":6781}

## Coverage

Stage05 preserved coverage by symbol/session/side/framework without collapsing unknown/null classes:

- Symbols: {"GBPJPY":428,"GBPUSD":239,"NAS100":145,"NDX100":45,"US30":16,"US30_cash":182,"USDJPY":276,"XAGUSD":196,"XAUUSD":108}
- Sessions: {"london":722,"ny":628,"off_core_session":1,"tokyo":284}
- Sides: {"LONG":500,"None":846,"SHORT":289}
- Frameworks: {"None":436,"breaker_re_entry":71,"fvg_fill":2,"none":633,"ob_retest":493}

## Execution, Fill, And Broker Truth

The replay measured entry touch/no-touch, pending/no-fill, stop-first/target-first, timeout, and path-aware proxy R. It did not fabricate broker-realized tickets, executed prices, commission, swap, slippage, partial exits, or account R. Required forward/demo capture fields are listed in the Stage08 execution dossier.

## MIXED Resolution

MIXED classification counts: {"ambiguous but replay-resolvable":927,"broad/unanchored/noisy":2,"neutral/no-effect context":291,"replay attribution only":90,"resolvable into AVOID":2,"source-required and not safely resolvable":172,"useful context":50}

Replay-resolvable MIXED rows: 929; source-required MIXED rows: 172.

## Prop-Firm Scenarios

| Scenario | Risk %/R | Current pass P | Current daily breach | Current max-loss breach | Activated pass P | Activated daily breach | Activated max-loss breach |
| --- | --- | --- | --- | --- | --- | --- | --- |
| challenge_8_5_current_config_2_0pct_per_r | 2.0 | 0.0002 | 0.1594 | 0.8404 | 0.0 | 0.0 | 0.0 |
| challenge_8_5_risk_0_5pct_per_r | 0.5 | 0.0 | 0.0002 | 0.9998 | 0.0 | 0.0 | 0.0 |
| challenge_8_5_risk_1_0pct_per_r | 1.0 | 0.0 | 0.031 | 0.969 | 0.0 | 0.0 | 0.0 |

## Final Decision Map

| Decision category | Rows |
| --- | --- |
| promote later | 0 |
| keep shadow/default-off | 6 |
| kill/remove candidate | 0 |
| source-repair required | 42 |
| replay-inconclusive | 1 |
| data-required | 1 |
| runtime bug found | 0 |
| methodology limitation | 0 |
| broker/demo-live observation required | 2 |
| AI minimal-budget evaluation required | 2 |

Headline actions:

- `no_production_promotion_from_replay_package`: Do not promote any vNext execution-effect flag from this session. Evidence: {"activated_entry_touched_trades": 1, "activated_total_r": 1.5, "activation_delta_r": 60.5, "current_entry_touched_trades": 100, "current_total_r": -59.0}
- `risk_blocks_remain_default_off_research_candidate`: Keep vNext risk/pending/pre-AI execution effects shadow/default-off pending demo observation. Evidence: {"active_blocked_rows": 677, "zero_risk_blocks": {"current_config_shadow": 531, "hypothetical_activated_vnext": 531}}
- `forward_capture_required_for_execution_truth`: Use demo/forward capture to collect broker execution geometry before exact R claims. Evidence: {"activated_order_attempt_count": 2, "activated_trade_count_entry_touched": 1, "broker_execution_fields_required": ["order_ticket", "deal_ticket", "broker_fill_time_utc", "executed_entry_price", "executed_exit_price", "executed_stop_price", "executed_target_price", "executed_lot_size", "commission", "swap", "slippage_price", "partial_exit_lifecycle"], "current_no_fill_rows": 423, "current_order_attempt_count": 523, "current_timeout_or_unresolved_rows": 31, "current_trade_count_entry_touched": 100, "pending_lifecycle_path_rows": 428}
- `minimal_budget_ai_evaluation_required_only_if_ai_claim_is_needed`: Do not run paid AI replay here; design a separate stratified/cache-backed AI reliability sample if needed. Evidence: {"activated_pre_ai_action_distribution": {"NARROW_AI_EXCLUDE_FRAMEWORKS": 1457, "SKIP_AI_AVOID_ONLY": 178}, "ai_calls_allowed_skipped_narrowed": {"current_config_shadow": {"NARROW_AI_EXCLUDE_FRAMEWORKS": 1457, "SKIP_AI_AVOID_ONLY": 178}, "hypothetical_activated_vnext": {"NARROW_AI_EXCLUDE_FRAMEWORKS": 1457, "SKIP_AI_AVOID_ONLY": 178}}, "current_pre_ai_action_distribution": {"ALLOW_AI": 1635}, "paid_api_or_vendor_call": false, "pre_ai_action_changed": 1635}

## Completion Audit

Completion audit status: `complete_with_source_bound_limitations`.

| Requirement | Status | Evidence |
| --- | --- | --- |
| preflight_context_reread | complete | LIVE_STATE and mandatory context were reread before Stage08/Stage09 continuation; hashes are recorded in the session spine and preregistration. |
| preregistration_manifest | complete | research/science_program_2026_05/06_outcome_testing/vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/VNEXT_REPLAY_PREREGISTRATION_MANIFEST_2026-05-24.json |
| data_inventory | complete | research/science_program_2026_05/06_outcome_testing/vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/VNEXT_REPLAY_DATA_COVERAGE_SUMMARY_2026-05-24.json |
| runtime_truth_harness | complete | research/science_program_2026_05/06_outcome_testing/vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/VNEXT_REPLAY_RUNTIME_HARNESS_VERIFY_2026-05-24.json |
| event_and_path_reconstruction | complete | research/science_program_2026_05/06_outcome_testing/vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/VNEXT_REPLAY_EVENT_PATH_RECONSTRUCTION_SUMMARY_2026-05-24.json |
| saturated_replay | complete | research/science_program_2026_05/06_outcome_testing/vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/VNEXT_REPLAY_SATURATED_REPLAY_SUMMARY_2026-05-24.json |
| ablation_and_mixed_resolution | complete | research/science_program_2026_05/06_outcome_testing/vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/VNEXT_REPLAY_ABLATION_MIXED_SUMMARY_2026-05-24.json |
| prop_firm_and_robustness_metrics | complete | research/science_program_2026_05/06_outcome_testing/vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/VNEXT_REPLAY_PROP_FIRM_METRICS_2026-05-24.json; research/science_program_2026_05/06_outcome_testing/vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/VNEXT_REPLAY_PROP_FIRM_ROBUSTNESS_SUMMARY_2026-05-24.json |
| failure_repair_dossiers | complete | research/science_program_2026_05/06_outcome_testing/vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/VNEXT_REPLAY_FAILURE_REPAIR_SUMMARY_2026-05-24.json |
| final_decision_map | complete | research/science_program_2026_05/06_outcome_testing/vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/VNEXT_REPLAY_PROMOTION_KILL_REPAIR_MAP_2026-05-24.json |
| final_report | complete | research/science_program_2026_05/06_outcome_testing/vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/VNEXT_REPLAY_FINAL_REPORT_2026-05-24.md |
| source_gap_evidence | complete | 43 source-gap repair rows preserved in Stage08. |
| m15_path_modes_separated | complete | M15 and lower-timeframe/tick/OHLC modes remain separate. |
| large_outputs_manifest_recorded | complete | research/science_program_2026_05/06_outcome_testing/vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/VNEXT_REPLAY_OUTPUT_MANIFEST_2026-05-24.json |

Remaining limitations are exact source/capture/approval requirements: {"ai_minimal_budget_required_rows": 2, "broker_demo_live_required_rows": 2, "data_required_rows": 1, "source_repair_required_rows": 42, "why_no_same_evidence_class_step_remains": "Remaining items require non-generatable historical GTOS state, future/demo broker execution capture, source-safe regime/news enrichment, read-only export not already present, or explicit paid-AI approval. All available repo/local replay, path, ablation, MIXED, prop, robustness, and repair-dossier steps are materialized."}

## Forbidden Surfaces

{
  "no_live_trading_or_broker_mutation": true,
  "paid_api_or_vendor_call": false,
  "production_config_mutated": false,
  "remote_push": false
}

## Artifacts

- Decision map: `research/science_program_2026_05/06_outcome_testing/vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/VNEXT_REPLAY_PROMOTION_KILL_REPAIR_MAP_2026-05-24.json`
- Completion audit: `research/science_program_2026_05/06_outcome_testing/vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/VNEXT_REPLAY_COMPLETION_AUDIT_2026-05-24.json`
- Output manifest: `research/science_program_2026_05/06_outcome_testing/vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/VNEXT_REPLAY_OUTPUT_MANIFEST_2026-05-24.json`
- Session spine: `research/science_program_2026_05/06_outcome_testing/gtos_vnext_replay_truth_engine/VNEXT_REPLAY_TRUTH_ENGINE_SESSION_STATE_2026-05-24.json`

## Artifact Packaging Addendum

This completed package is a logged-event replay truth package, not the full historical all-market candidate-generation replay.

The next phase is full historical vNext candidate generation over all available OHLC/M1/M5/tick/Sierra data, with source repair/acquisition as needed and simulated R/path-ordering as the primary historical performance truth. Broker-realized execution fields are later live/demo calibration, not a blocker for historical simulated replay.

Chunk manifest: `research/science_program_2026_05/06_outcome_testing/vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/VNEXT_REPLAY_LFS_CHUNK_MANIFEST_2026-05-24.json`

| Ledger | Original rows | Original bytes | Original sha256 | Chunk count | Max chunk bytes |
|---|---:|---:|---|---:|---:|
| saturated_replay | 3270 | 5501336398 | `f158e798f720e926909a215c41d75ab2770f04ef97b10ed0c38983b847507698` | 4 | 232072320 |
| ablation | 2094510 | 4790894180 | `764289c963373ad0b7a1acd3637f456d85f142a70af5fa794ba8c95818414c6a` | 3 | 43366397 |

The monolithic ledger paths are replaced for pushed history by the chunk files listed in the chunk manifest. Reconstruction order is the `reconstruction_order` array for each ledger.
