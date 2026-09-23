# GTOS vNext Final Conversion Freeze Report

- Current checkpoint HEAD: `f3e0dc3a15bd523be6d0dc0c2fb7374d5eedf523`
- Master ledger: `research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/GTOS_VNEXT_MASTER_INTELLIGENCE_TO_RUNTIME_CONVERSION_LEDGER_2026-05-18.jsonl`
- Batch ledger: `research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/GTOS_VNEXT_BATCH_RUNTIME_CONVERSION_LEDGER_2026-05-18.jsonl`
- Freeze classification ledger: `research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/GTOS_VNEXT_FINAL_CONVERSION_FREEZE_CLASSIFICATION_LEDGER_2026-05-23.jsonl`

## Final Counts

- Total units: 13571
- Pre-freeze closed units: 11932
- Pre-freeze open NOT_STARTED units classified by freeze: 1639
- Freeze killed units: 1157
- Freeze parked units: 482
- Post-freeze candidate units requiring fresh admission: 0
- Final unclassified open units: 0
- Final classification coverage: 100.0%

## Freeze Class Counts

- LEGACY_OR_STALE_NON_OVERRIDE_PARK: 402
- NEEDS_USER_DECISION_BEFORE_RUNTIME: 7
- REPLAY_ATTRIBUTION_ONLY_PARK: 73
- WRAPPER_SUPPORT_CHILDREN_ALREADY_HANDLED_KILL: 1157

## Executed Waves

- WAVE_ACCEPTED_BUILDER_SOURCE_REPAIR_RUNTIME
- WAVE_ACCEPTED_CANDIDATE_M1_FILL_SOURCE_REPAIR_RUNTIME
- WAVE_ADVERSE_STOP_FIRST_EXECUTION_BEHAVIOR
- WAVE_AI_DECISION_TRACE_ROUTING_GUARD_RUNTIME
- WAVE_BRANCH_AMBIGUITY_COLLAPSE_RUNTIME
- WAVE_BRANCH_FOLLOWUP_COMPUTATION_RUNTIME
- WAVE_BRANCH_IMPLEMENTATION_REPLAY_RUNTIME
- WAVE_BRANCH_REPLAY_EXECUTION_REPAIR_RUNTIME
- WAVE_ENTRY_OFFSET_050R_CLUSTER_GUARD_RUNTIME
- WAVE_EXECUTION_ADJACENT_FRICTION_RESIDUE_RUNTIME
- WAVE_EXIT_MANAGEMENT_RESIDUE_RUNTIME
- WAVE_EXIT_MANAGEMENT_TRAILING_J46_RUNTIME
- WAVE_EXPANDED_MARKET_IMPLEMENTATION_SCORER_SURFACES
- WAVE_EXPANDED_MARKET_SOURCE_GEOMETRY_ROUTER
- WAVE_FVG_TRADE_RECORD_BOUNDS_EXECUTION_RUNTIME
- WAVE_GATE_SELECTOR_SESSION_TIMEFRAME_BEHAVIOR
- WAVE_GTOS_VNEXT_BRIDGE_RESIDUE_RUNTIME
- WAVE_INSTRUMENT_EXPANSION_MARKET_SESSION_RUNTIME
- WAVE_LEGACY_AI_CASCADE_MODEL_RUNTIME
- WAVE_LEGACY_LIVE_SHADOW_DECISION_RUNTIME
- WAVE_LEGACY_T7_PRODUCTION_SIMULATION_FRICTION_RUNTIME
- WAVE_LEGACY_V2_V3_PAPER_LIVE_FRICTION_RUNTIME_MERGE
- WAVE_LIFECYCLE_EXECUTION_SOURCE_GUARD_RUNTIME
- WAVE_LTF_PATH_GEOMETRY_SOURCE_RUNTIME
- WAVE_MAIN_ORCH24_ACTION_COMPLETENESS_RESIDUAL_R_RUNTIME
- WAVE_MAIN_ORCH24_IMPLEMENTATION_SELECTION_RUNTIME
- WAVE_MAIN_ORCH24_LIVE_MECHANICAL_GEOMETRY_OUTCOME_RUNTIME
- WAVE_MAIN_ORCH24_SNAPSHOT_DEPENDENCY_REPAIR_RUNTIME
- WAVE_MAIN_ORCH24_SOURCE_ACCEPTED_ACTION_REPAIR_RUNTIME
- WAVE_MAIN_ORCH24_SOURCE_M15_BRANCH_REPAIR_RUNTIME
- WAVE_MAIN_ORCH24_STRUCTURAL_REPAIR_ACTION_RUNTIME
- WAVE_MAIN_ORCH24_SURVIVOR_FAILURE_RUNTIME
- WAVE_MAIN_ORCH24_SWING_PROTECTED_SOURCE_REPAIR_RUNTIME
- WAVE_MAIN_ORCH24_TICK_STRUCTURAL_ENTRY_RUNTIME
- WAVE_MAIN_ORCH24_UNIFIED_CANDIDATE_PATH_PROXY_RUNTIME
- WAVE_MAIN_ORCH48_AI_NARROWING_DEFAULT_OFF_RUNTIME
- WAVE_MAIN_ORCH48_FINAL_REVIEW_SELECTOR_RUNTIME
- WAVE_MAIN_ORCH48_NR_SOURCE_REPAIR_EXECUTION_IDENTITY_RUNTIME
- WAVE_MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_RUNTIME
- WAVE_MARKET_GAP_PRIMITIVE_EXPANSION_ROUTER
- WAVE_NEARMISS_MARKET_ENTRY_JOIN_ROUTER
- WAVE_NOFILL_PENDING_LIFECYCLE_BEHAVIOR
- WAVE_OBSERVABLE_EXECUTION_SCORER_RUNTIME
- WAVE_OPENING_DRIVE_SOURCE_CONTRACT_RUNTIME
- WAVE_PRE_AI_H1_POI_SOURCE_GAP_RUNTIME
- WAVE_PRE_AI_POST_L2_ROUTING_BEHAVIOR
- WAVE_Q62_PARTIAL_CLOSE_EXIT_RUNTIME
- WAVE_READY8_CONTEXT_RISK_RULES
- WAVE_READY8_DISCRIMINATIVE_CONTEXT_RULES
- WAVE_READY8_FAILURE_CONTEXT_ADJUSTMENT_RULES
- WAVE_READY8_FAILURE_CONTROL_RESIDUE_RUNTIME
- WAVE_REJECTED_CANDIDATE_L2_VALUE_MINING_RUNTIME
- WAVE_REPAIRED_PROXY_SYMBOL_SURFACE
- WAVE_RISK_R_PROXY_STRESS_COST_BEHAVIOR
- WAVE_SCID_COMBINED_SOURCE_CAPTURE_POI_BOUNDS_RUNTIME
- WAVE_SCID_FORWARD_SOURCE_CAPTURE_RUNTIME
- WAVE_SCID_FUTURE_CAPTURE_SOURCE_STATE_RUNTIME
- WAVE_SCID_NOAPI_SOURCE_REPAIR_RUNTIME
- WAVE_SCID_TARGET_HORIZON_CONTROL_RUNTIME
- WAVE_SHADOW_SOURCE_LOG_MATERIALIZATION_RUNTIME
- WAVE_SIERRA_DEPTH_SOURCE_ACQUISITION_REPAIR
- WAVE_SL_BEYOND_OB_OUTCOME_JOIN_SOURCE_REPAIR_RUNTIME
- WAVE_SOURCE_REPAIR_MISSING_DENOMINATOR_BEHAVIOR
- WAVE_TARGET_STOP_ORDERING_EXECUTION_SCORING_RUNTIME
- WAVE_TICK_M15_EXECUTION_FRICTION_RUNTIME
- WAVE_TICK_M15_TARGET_CONTROL_RUNTIME
- WAVE_TICK_SOURCE_RECOVERY_QUOTE_CONTRACT_RUNTIME
- WAVE_TRADE_RECORD_EXECUTION_LIFECYCLE_RUNTIME
- WAVE_UNIFIED_CANDIDATE_ACTION_EXECUTION_RUNTIME
- WAVE_UNIFIED_CANDIDATE_MARKET_ROLLUP
- WAVE_UNIFIED_CANDIDATE_SCORING_EXECUTION_RUNTIME
- WAVE_UNIFIED_EXECUTION_ACTION_WORK_ORDER_RUNTIME
- WAVE_UNIFIED_EXECUTION_DECISION_RUNTIME
- WAVE_UNIFIED_SHADOW_SOURCE_MATERIALIZATION_RUNTIME
- WAVE_VNEXT_SCORER_FILTER_ROUTER_RUNTIME

## Runtime/System Behavior Actually Changed

- Converted runtime artifacts remain the only sources allowed to affect vNext route, risk, selector, gate, no-fill, entry, exit, AI-routing, and source-acquisition behavior.
- The final lifecycle checkpoint added source-acquisition guards for still-pending, wrong-side, trade-index action-required, and reset-policy lifecycle evidence without candidate-use, broker, paid API, or live-trading effect.
- Freeze rows add no FOLLOW, AVOID, MIXED, risk, selector, AI, entry, exit, no-fill, gate, broker, or source-component pressure.

## Code/Config/Tests Changed By Final Runtime Checkpoint

- `src/components/gtos_vnext_runtime.py`
- `config/agent_config.yaml`
- `scripts/build_gtos_vnext_master_conversion_ledger.py`
- `scripts/build_gtos_vnext_lifecycle_execution_source_guard_runtime_rows.py`
- `tests/test_gtos_vnext_runtime.py`
- `tests/test_gtos_vnext_master_conversion_ledger.py`
- Freeze checkpoint adds this report, classification ledger, summary, builder script, and freeze tests.

## Generated Runtime Artifacts

- Generated runtime artifact count loaded from config: 153
- Generated runtime row count loaded from config: 661344

## Markets/Symbols/Timeframes/Sessions/Sides

- symbols: {"6AM26-CME": 412, "6BM26-CME": 291, "6CM26-CME": 443, "6EM26-CME": 418, "6JM26-CME": 324, "6SM26-CME": 448, "AAPL": 442, "ALL_MARKETS": 4, "AMZN-NQTV": 440, "AUDJPY": 876, "AUDUSD": 835, "BTCUSD": 868, "BTCUSDT_PERP_BINANCE": 409, "CHFJPY": 917, "CL": 1, "CLM26-NYMEX": 429, "CL_PROXY": 444, "DXY": 282, "ESM26-CME": 535, "ETHUSD": 909, "EURGBP": 900, "EURJPY": 899, "EURUSD": 4160, "EURUSD_6E": 454, "EURUSD_SCID": 482, "GBPJPY": 212723, "GBPUSD": 40685, "GBPUSD_6B": 5096, "GCM26-COMEX": 315, "GER40": 1030, "JP225": 892, "M2KM26-CME": 444, "MCLM26-NYMEX": 427, "MESM26-CME": 534, "MESU25-CME": 2, "MGCM26-COMEX": 315, "MNQM26-CME": 323, "MYMM26-CBOT": 310, "NA": 3, "NAS100": 47344, "NAS100_MNQ": 454, "NAS100_NQ": 5052, "NDX100": 1189, "NQ": 2, "NQM26-CME": 329, "NZDUSD": 882, "None": 1, "RTYM26-CME": 447, "SILM26-COMEX": 305, "SIM26-COMEX": 301, "SPX500": 909, "SPX_ES": 415, "SPX_MES": 415, "SYNTH_USDJPY": 1, "SYSTEM_LEVEL": 8, "TICK-NYSE": 444, "UK100": 1024, "UKOIL_CASH": 160, "UKOIL_cash": 682, "UKOUSD": 7, "US30": 10020, "US30_CASH": 156, "US30_MYM": 584, "US30_YM": 5186, "US30_cash": 23102, "US500_cash": 1, "USDCAD": 954, "USDCHF": 914, "USDJPY": 37655, "USDJPY_6J": 5202, "USOIL_CASH": 133, "USOIL_cash": 794, "VIX_VXM": 406, "VIX_VXMM": 407, "VXM": 1, "VXM26-CFE": 425, "VXMM26-CFE": 426, "XAGUSD": 60693, "XAGUSD_SI": 4297, "XAGUSD_SIL": 488, "XAUUSD": 93867, "XAUUSD_GC": 4981, "XAUUSD_LIVE_BATCH": 1, "XAUUSD_MGC": 383, "XAUUSD_SCID": 382, "YMM26-CBOT": 317, "YMU25-CBOT": 2, "ZBM26-CBOT": 442, "ZN": 1, "ZNM26-CBOT": 452, "ZN_CONTROL": 481}
- source_symbols: {"6AM26-CME": 601, "6B.v.0": 1, "6BM26-CME": 510, "6CM26-CME": 602, "6E.v.0": 1, "6EM26-CME": 834, "6J.v.0": 1, "6JM26-CME": 628, "6SM26-CME": 666, "AAPL": 537, "ALL_MARKETS": 4, "AMZN-NQTV": 499, "AUDJPY": 747, "AUDUSD": 710, "BTCUSD": 729, "BTCUSDT_PERP_BINANCE": 480, "CHFJPY": 790, "CL.v.0": 1, "CLM26-NYMEX": 582, "CL_PROXY": 443, "DXY": 272, "ESM26-CME": 376, "ETHUSD": 766, "EURGBP": 757, "EURJPY": 762, "EURUSD": 4042, "EURUSD_6E": 483, "EURUSD_SCID": 481, "GBPJPY": 83696, "GBPUSD": 28420, "GBPUSD_6B": 14383, "GC.v.0": 1, "GCM26-COMEX": 387, "GER40": 865, "JP225": 753, "M2KM26-CME": 598, "MCLM26-NYMEX": 543, "MESM26-CME": 375, "MESU25-CME": 4, "MGCM26-COMEX": 384, "MNQM26-CME": 394, "MYMM26-CBOT": 381, "NA": 3, "NAS100": 34132, "NAS100_MNQ": 676, "NAS100_NQ": 14440, "NDX100": 1242, "NQ": 4, "NQ.v.0": 1, "NQM26-CME": 566, "NZDUSD": 737, "None": 1, "RTYM26-CME": 639, "SI.v.0": 1, "SILM26-COMEX": 373, "SIM26-COMEX": 372, "SPX500": 913, "SPX_ES": 576, "SPX_MES": 576, "SYNTH_USDJPY": 1, "SYSTEM_LEVEL": 6, "TICK-NYSE": 552, "UK100": 865, "UKOIL_CASH": 159, "UKOIL_cash": 563, "UKOUSD": 6, "US30": 644, "US30_CASH": 156, "US30_MYM": 1182, "US30_YM": 14963, "US30_cash": 19671, "US500_cash": 1, "USDCAD": 821, "USDCHF": 769, "USDJPY": 23912, "USDJPY_6J": 14755, "USOIL_CASH": 132, "USOIL_cash": 637, "VIX_VXM": 405, "VIX_VXMM": 406, "VX.v.0": 1, "VXM26-CFE": 499, "VXMM26-CFE": 488, "XAGUSD": 48663, "XAGUSD_SI": 12208, "XAGUSD_SIL": 791, "XAUUSD": 48978, "XAUUSD_GC": 14146, "XAUUSD_LIVE_BATCH": 1, "XAUUSD_MGC": 382, "XAUUSD_SCID": 381, "YM.v.0": 2, "YMM26-CBOT": 490, "YMU25-CBOT": 4, "ZBM26-CBOT": 641, "ZN.v.0": 1, "ZNM26-CBOT": 924, "ZN_CONTROL": 480}
- timeframes: {"D1": 19968, "H1": 14417, "H4": 12929, "M1": 12633, "M15": 233058, "M5": 8285}
- sessions: {"ALL_AVAILABLE_OR_UNMAPPED_SESSIONS": 93, "ALL_SESSIONS": 55264, "London": 28, "NA": 16, "NY": 31, "REGISTERED_OR_CONFIGURED_SESSIONS_NOT_YET_ROUTED": 6, "Tokyo": 29, "london": 229, "london_core": 73309, "ny": 161, "ny_core": 177572, "off_core_session": 87254, "off_kz": 876, "tokyo": 80, "tokyo_core_0000_0300": 856, "tokyo_kz": 156828, "unknown": 16}
- sides: {"ALL_SIDES": 9928, "LONG": 129319, "LONG_PROXY_FROM_SOURCE_CLOSE_SIGN": 1064, "SHORT": 63455, "SHORT_PROXY_FROM_SOURCE_CLOSE_SIGN": 33, "UNKNOWN": 921}
- frameworks: {"EXP-G3-DC-OVERSHOOT-002": 95, "EXP-G3-DC-SWING-001": 8, "EXP-G3-TDA-007": 96, "breaker_re_entry": 944, "breaker_retest": 1, "fvg_fill": 5435, "g3_geometry": 921, "none": 9, "ob_retest": 12905, "session_sweep": 7}

## Strategy Families, Entries, Exits, Filters, Gates, Risk, No-Fill, AI Paths

- Runtime evidence families: {"ai_decision_architecture": 462, "cp281_native_rule_replay": 1682, "cp281_ready_runtime_mapping": 214, "expanded_market_reduced_surface": 3496, "expanded_market_source_geometry": 57745, "gate_filter_selector_evidence": 6, "gtos_vnext_accepted_candidate_m1_fill_source_repair": 860, "gtos_vnext_adverse_stop_first_execution": 1049, "gtos_vnext_ai_decision_trace_routing_guard": 781, "gtos_vnext_ai_narrowing_default_off_runtime": 761, "gtos_vnext_branch_ambiguity_collapse": 2137, "gtos_vnext_branch_followup_computation": 315, "gtos_vnext_branch_implementation_replay": 4868, "gtos_vnext_branch_replay_execution_repair": 2829, "gtos_vnext_cp280_scorer_filter_router": 34718, "gtos_vnext_entry_offset_050r_cluster_guard": 35, "gtos_vnext_execution_adjacent_friction_residue": 50, "gtos_vnext_exit_management_residue": 12, "gtos_vnext_exit_management_trailing_j46": 12, "gtos_vnext_fvg_trade_record_bounds_execution_runtime": 3426, "gtos_vnext_gate_selector_session_timeframe": 8339, "gtos_vnext_instrument_expansion_market_session_runtime": 3714, "gtos_vnext_legacy_ai_cascade_model_runtime": 2033, "gtos_vnext_legacy_live_shadow_decision_runtime": 13, "gtos_vnext_legacy_t7_simulation_friction": 82, "gtos_vnext_legacy_v2_v3_paper_live_friction": 371, "gtos_vnext_lifecycle_execution_source_guard": 72, "gtos_vnext_ltf_path_geometry_source_runtime": 5017, "gtos_vnext_main_orch24_action_completeness_residual_r_runtime": 23368, "gtos_vnext_main_orch24_implementation_selection_runtime": 13018, "gtos_vnext_main_orch24_live_mechanical_geometry_outcome_runtime": 20445, "gtos_vnext_main_orch24_snapshot_dependency_repair_runtime": 11016, "gtos_vnext_main_orch24_source_accepted_action_repair_runtime": 86, "gtos_vnext_main_orch24_source_m15_branch_repair_runtime": 3976, "gtos_vnext_main_orch24_structural_repair_action_runtime": 13704, "gtos_vnext_main_orch24_swing_protected_source_repair_runtime": 274, "gtos_vnext_main_orch24_tick_structural_entry_runtime": 3526, "gtos_vnext_main_orch24_unified_candidate_path_proxy_runtime": 12081, "gtos_vnext_main_orch48_final_review_selector_runtime": 9728, "gtos_vnext_nofill_pending_lifecycle": 3658, "gtos_vnext_nr_source_repair_execution_identity": 12314, "gtos_vnext_numeric_router_catalog_runtime": 1362, "gtos_vnext_observable_execution": 2406, "gtos_vnext_opening_drive_source_contract": 20, "gtos_vnext_pre_ai_h1_poi_source_gap": 246, "gtos_vnext_pre_ai_post_l2_routing_policy": 874, "gtos_vnext_q62_partial_close_exit_runtime": 1013, "gtos_vnext_ready8_failure_control_residue": 8, "gtos_vnext_rejected_candidate_l2_value_mining": 266, "gtos_vnext_risk_proxy_stress_cost": 1944, "gtos_vnext_scid_combined_source_capture_poi_bounds": 27126, "gtos_vnext_scid_forward_source_capture": 3, "gtos_vnext_scid_future_capture_source_state": 1213, "gtos_vnext_scid_noapi_source_repair": 54227, "gtos_vnext_scid_target_horizon_control": 24988, "gtos_vnext_shadow_source_log_materialization": 182, "gtos_vnext_sierra_depth_source_acquisition": 4772, "gtos_vnext_sl_beyond_ob_outcome_join_source_repair": 332, "gtos_vnext_source_repair_missing_denominator": 5111, "gtos_vnext_survivor_failure_runtime": 946, "gtos_vnext_target_stop_ordering_execution_scoring": 1121, "gtos_vnext_tick_m15_execution_friction": 785, "gtos_vnext_tick_m15_target_control": 420, "gtos_vnext_tick_source_recovery_quote_contract_runtime": 961, "gtos_vnext_trade_record_execution_lifecycle": 535, "gtos_vnext_unified_candidate_action_execution": 992, "gtos_vnext_unified_candidate_scoring_execution": 91, "gtos_vnext_unified_execution_action_work_order": 17916, "gtos_vnext_unified_execution_decision": 1172, "gtos_vnext_unified_shadow_source_materialization": 2254, "numeric_router_source_repair": 21110, "numeric_router_system_recommendations": 26901}
- Runtime source components: {"a4_fill_simulation_result_pressure": 8, "accepted_candidate_classifier_validation_context": 2, "accepted_candidate_distribution_result_pressure": 14, "accepted_candidate_feature_ranking_pressure": 28, "accepted_candidate_feature_stratification_pressure": 84, "accepted_candidate_h1_h2_feature_stability_context": 5, "accepted_candidate_m1_fill_support_code_context": 10, "accepted_candidate_touch_bucket_result_pressure": 26, "accepted_filled_candidate_result_pressure": 25, "adv002_source_control_exact_requirement_guard": 7, "adverse_stop_first_execution": 141, "ai_architecture_audit": 4, "ai_hallucination_guard": 861, "ai_limit_order_prompt_context": 8, "ai_narrowing_policy_residue": 10, "ai_routing_architecture_context": 215, "ai_shadow_readiness": 1, "ai_source_lineage_materialization_guard": 265, "ai_trace_integrity_guard": 5, "ai_trace_provenance": 5, "ai_trace_trade_record_backfill": 535, "ai_v3_cascade_preferred": 113, "branch_replay_execution_blocker_repair_guard": 386, "branch_replay_execution_context_guard": 2, "branch_replay_execution_negative_or_redesign": 128, "branch_replay_execution_positive_challenger": 156, "branch_replay_execution_positive_proxy": 99, "branch_replay_execution_positive_repair_bounded_proxy": 209, "branch_replay_execution_positive_source_repair": 87, "branch_replay_execution_positive_work_unit": 51, "branch_replay_execution_source_ordering_guard": 334, "branch_replay_execution_work_unit_context": 1377, "broker_actual_r_slippage_source_repair": 11, "confidence_filter_quarantine": 505, "cp280_baseline_control": 95, "cp280_numeric_router_system_recommendations": 5, "cp280_numeric_shadow_scorer": 4, "cp280_observable_runtime_work": 4240, "cp280_scorer_filter_router": 19869, "cp280_unified_action_result": 5, "cp280_unified_candidate_scorer": 459, "data_inventory": 6973, "default_off_application": 13858, "default_off_scorer_application": 4236, "entry_adverse_execution": 276, "entry_geometry_fillability_tick_path_ordering": 264, "entry_geometry_fillability_tick_path_ordering_retest_control": 10, "exact_r_alias_search_context": 2, "exact_r_alias_search_source_repair": 7, "exact_r_bridge_kill_branch_avoid": 133, "exact_r_bridge_materialized_context": 210, "exact_r_bridge_missing_identifier_source_repair": 42, "exact_r_bridge_redesign_source_repair": 188, "exact_r_source_materialization_support_context": 4, "exact_r_verification_missing_identifier_source_repair": 2, "exact_r_verification_owner_reference_context": 2, "execution_replay_source_contract_context": 6, "execution_source_capture_contract_context": 14, "exit_no_event_status_observability": 7, "exit_optimization_context": 1, "exit_partial_split_policy_guard": 1, "exit_policy_h29_risk_context": 1, "exit_policy_legacy_batch_context": 1, "exit_session_timestamp_source_requirement": 2, "expanded_market_ohlc_source_reachable": 3308, "expanded_market_source_gap": 792, "expanded_market_source_geometry": 12412, "framework_gate_selector": 121, "fvg_entry_geometry_and_lock_metadata": 542, "fvg_ob_confluence_shared_path_scorer": 274, "fvg_ob_framework_repair": 1785, "g3_geometry_entry_missed_nofill": 81, "g3_geometry_same_m1_ambiguity_guard": 256, "g3_geometry_source_repair_guard": 76, "g3_geometry_stop_first_avoid": 2, "g3_geometry_target_first_follow": 16, "gate_confidence_filter": 1, "gate_cross_instrument_correlation": 19, "gate_cross_instrument_correlation_gate": 1, "gate_filter_selector_runtime_mapping": 1, "gate_pre_ai_h1_poi_availability": 1, "gate_pre_ai_poi_availability": 1, "gate_selector_session_timeframe_context": 338, "gate_session_57_runtime_halt_boundary": 1, "gate_sl_beyond_ob": 155, "gate_sl_beyond_ob_l2": 2, "gate_touch_count": 33, "gate_touch_count_gate": 2, "gbpjpy_long_adverse_avoid_reclass": 20, "gbpjpy_long_adverse_reclass_context": 599, "gtos_branch_ambiguity_branch": 332, "gtos_branch_ambiguity_bucket": 45, "gtos_branch_ambiguity_cause_matrix": 333, "gtos_branch_ambiguity_interval": 332, "gtos_branch_ambiguity_m15_same_bar": 332, "gtos_branch_ambiguity_ordering": 332, "gtos_branch_ambiguity_source_repair": 431, "gtos_branch_followup_binding": 2, "gtos_branch_followup_branch": 113, "gtos_branch_followup_bucket": 1, "gtos_branch_followup_family": 139, "gtos_branch_followup_m1": 12, "gtos_branch_followup_m15": 19, "gtos_branch_followup_positive": 12, "gtos_branch_followup_source": 17, "gtos_branch_impl_action": 490, "gtos_branch_impl_candidate": 269, "gtos_branch_impl_cause_matrix": 235, "gtos_branch_impl_code_replay": 85, "gtos_branch_impl_control_source_split": 172, "gtos_branch_impl_full_outcome": 234, "gtos_branch_impl_guarded_scope_scorer": 7, "gtos_branch_impl_m1_chronology": 14, "gtos_branch_impl_m1_interval": 54, "gtos_branch_impl_m1_support": 95, "gtos_branch_impl_next_compute": 323, "gtos_branch_impl_numeric_decision": 437, "gtos_branch_impl_numeric_router": 436, "gtos_branch_impl_ordering_collapse": 84, "gtos_branch_impl_positive_challenger": 477, "gtos_branch_impl_replay_builder": 317, "gtos_branch_impl_replay_matrix": 503, "gtos_branch_impl_router_scoring": 347, "gtos_branch_impl_score_export": 214, "gtos_branch_impl_source_spread_recompute": 75, "instrument_expansion_decay_cluster_context": 24, "instrument_expansion_decay_results_context": 24, "instrument_expansion_gbpusd_nofill_context": 22, "instrument_expansion_gbpusd_observer_avoid": 2, "instrument_expansion_gbpusd_observer_follow": 4, "instrument_expansion_h1_h2_decay_context": 375, "instrument_expansion_h1_h2_decay_guard": 9, "instrument_expansion_hourly_session_context": 576, "instrument_expansion_market_candidate_avoid": 18, "instrument_expansion_market_candidate_context": 36, "instrument_expansion_market_candidate_follow": 18, "instrument_expansion_microstructure_context": 15, "instrument_expansion_microstructure_cost_guard": 9, "instrument_expansion_monthly_context": 2375, "instrument_expansion_natural_kz_window": 41, "instrument_expansion_route_avoid": 58, "instrument_expansion_route_context": 15, "instrument_expansion_route_follow": 23, "instrument_expansion_tier2_job_context": 28, "instrument_expansion_tier2_slice_avoid": 6, "instrument_expansion_tier2_slice_context": 11, "instrument_expansion_tier2_slice_follow": 18, "instrument_expansion_tier2_source_repair_guard": 7, "j46_j49_active_exit_policy": 5, "j46_j49_actual_r_boundary": 1, "kill_scope_preservation": 8, "l2_entry_in_ob_rejection_value": 14, "l2_h1_poi_rejection_value": 30, "l2_m15_choch_rejection_value": 23, "l2_sl_beyond_ob_rejection_value": 23, "legacy_ai_cascade_context_guard": 74, "legacy_ai_model_context_guard": 117, "legacy_ai_schema_parser_guard": 391, "legacy_live_shadow_fvg_ob_source_acquisition": 1, "legacy_live_shadow_j46_j49_policy_follow": 1, "legacy_live_shadow_k54_k55_same_cohort_kill": 1, "legacy_live_shadow_nofill_capture_source_acquisition": 1, "legacy_live_shadow_partial_close_expansion_avoid": 1, "legacy_live_shadow_portfolio_vol_sizing_avoid": 1, "legacy_live_shadow_s79_side_aware_context": 1, "legacy_live_shadow_sierra_orderflow_diagnostic_context": 1, "legacy_live_shadow_strategy_replay_context": 1, "legacy_live_shadow_trailing_stop_shadow_context": 1, "legacy_live_shadow_v2_replay_context": 1, "legacy_live_shadow_v2b_forward_source_acquisition": 1, "legacy_live_shadow_xagusd_account_history_source_acquisition": 1, "legacy_t7_context_simulation": 35, "legacy_t7_negative_simulation": 15, "legacy_t7_positive_simulation": 32, "legacy_v2_v3_paper_live_context_guard": 104, "legacy_v2_v3_paper_live_follow_scorer": 60, "legacy_v2_v3_paper_live_friction_guard": 207, "legacy_v4_lira_guard": 470, "lifecycle_execution_replay_attribution_only": 4, "lifecycle_still_pending_no_fill_source_guard": 37, "lifecycle_wrong_side_no_fill_source_guard": 25, "ltf_path_contract_complete_context": 921, "ltf_path_source_blocked_guard": 163, "ltf_path_source_context": 1826, "ltf_path_source_recovered_context": 1590, "ltf_path_strategy_candidate_context": 86, "ltf_selector_repair": 371, "m1_backfill_source_coverage_guard": 8, "m1_fill_quality_result_pressure": 13, "m1_micro_feature_no_signal_context": 15, "main_orch24_action_completeness_context": 2496, "main_orch24_action_completeness_default_off_follow": 3301, "main_orch24_action_completeness_entry_offset_follow": 117, "main_orch24_action_completeness_entry_offset_redesign_guard": 69, "main_orch24_action_completeness_fvg_ob_kill_guard": 1323, "main_orch24_action_completeness_fvg_structural_follow": 317, "main_orch24_action_completeness_keep_context": 1596, "main_orch24_action_completeness_kill_guard": 3888, "main_orch24_action_completeness_nofill_far_miss_kill_guard": 1258, "main_orch24_action_completeness_pending_redesign_guard": 1734, "main_orch24_action_completeness_redesign_guard": 8764, "main_orch24_action_completeness_source_provenance_follow": 25, "main_orch24_action_completeness_source_provenance_redesign_guard": 11, "main_orch24_action_completeness_source_repair_requirement": 5137, "main_orch24_action_completeness_swing_unprotected_kill_guard": 112, "main_orch24_entry_offset_025r_kill_guard": 85, "main_orch24_entry_offset_050r_challenger": 10, "main_orch24_entry_offset_tick_source_acquisition": 2, "main_orch24_live_mechanical_ambiguous_path_guard": 67, "main_orch24_live_mechanical_context": 1432, "main_orch24_live_mechanical_forward_follow": 585, "main_orch24_live_mechanical_geometry_proxy_context": 12408, "main_orch24_live_mechanical_kill_guard": 144, "main_orch24_live_mechanical_pending_lifecycle_guard": 16, "main_orch24_live_mechanical_redesign_guard": 222, "main_orch24_live_mechanical_source_acquisition": 3738, "main_orch24_live_mechanical_stop_or_nofill_avoid": 1833, "main_orch24_nas100_tick_order_repair_follow": 1, "main_orch24_residual_numeric_r_adverse_avoid_guard": 9, "main_orch24_residual_numeric_r_context": 1022, "main_orch24_residual_numeric_r_distance_context": 557, "main_orch24_residual_numeric_r_materialized_context": 1256, "main_orch24_residual_numeric_r_redesign_guard": 3394, "main_orch24_snapshot_dependency_control_inventory": 8, "main_orch24_snapshot_dependency_failure_intelligence": 11004, "main_orch24_snapshot_dependency_replay_attribution": 2, "main_orch24_snapshot_dependency_source_repair_requirement": 2, "main_orch24_source_accepted_degraded_redesign_source_acquisition": 47, "main_orch24_source_accepted_m15_ordering_follow": 20, "main_orch24_source_accepted_source_cost_proxy_follow": 19, "main_orch24_source_m15_default_off_context": 330, "main_orch24_source_m15_kill_or_no_fill_guard": 344, "main_orch24_source_m15_neutral_context": 669, "main_orch24_source_m15_ordering_positive_follow": 343, "main_orch24_source_m15_redesign_guard": 628, "main_orch24_source_m15_source_acquisition": 1662, "main_orch24_standalone_fvg_negative_guard": 2, "main_orch24_structural_context": 117, "main_orch24_structural_duplicate_redesign_guard": 2232, "main_orch24_structural_fvg_ob_shared_path_context": 235, "main_orch24_structural_fvg_ob_single_family_kill_guard": 756, "main_orch24_structural_gbpjpy_long_adverse_redesign_guard": 23, "main_orch24_structural_ltf_adverse_redesign_guard": 55, "main_orch24_structural_metadata_default_off_follow": 2097, "main_orch24_structural_pending_lifecycle_context": 1278, "main_orch24_structural_prefill_redesign_guard": 805, "main_orch24_structural_repair_kill_guard": 647, "main_orch24_structural_repair_redesign_guard": 1109, "main_orch24_structural_source_repair_requirement": 2222, "main_orch24_structural_standalone_fvg_kill_guard": 2072, "main_orch24_structural_swing_unprotected_kill_guard": 56, "main_orch24_swing_protected_negative_proxy_guard": 51, "main_orch24_swing_protected_neutral_context": 69, "main_orch24_swing_protected_source_acquisition": 14, "main_orch24_swing_protected_tick_repair_follow": 52, "main_orch24_swing_protected_unprotected_stop_guard": 89, "main_orch24_tick_negative_proxy_guard": 69, "main_orch24_tick_positive_proxy_follow": 188, "main_orch24_tick_preserve_source_acquisition": 9, "main_orch24_tick_redesign_source_repair": 1570, "main_orch24_tick_structural_context": 622, "main_orch24_tick_structural_kill_guard": 967, "main_orch24_unified_branch_proxy_avoid": 227, "main_orch24_unified_branch_proxy_follow": 272, "main_orch24_unified_branch_proxy_source_repair": 273, "main_orch24_unified_m1_entry_materialized_context": 49, "main_orch24_unified_m1_fill_ordering_source_repair": 536, "main_orch24_unified_m1_spread_fill_target_follow": 1720, "main_orch24_unified_ready8_source_capture_repair_replay": 5502, "main_orch24_unified_split_summary_replay_attribution": 374, "main_orch24_unified_tick_m15_path_follow": 1564, "main_orch24_unified_tick_m15_path_inverse_avoid": 1564, "market_gap_code": 29106, "missed_fill_entry_geometry_source_requirement": 3, "missed_fill_to_tp_area_source_requirement": 7, "ml_shadow_selector": 13, "no_ai_shadow_observer": 61, "nofill_far_miss_avoid": 27508, "nofill_far_miss_family": 3724, "nofill_far_miss_retest": 82746, "nofill_far_miss_source_confidence": 74608, "nofill_near_miss_market_entry": 11759, "nofill_near_miss_offset": 3491, "nofill_near_miss_source_requirement": 6402, "non_xau_fillback_source_inventory_guard": 6, "observable_execution_avoid_filter": 26, "observable_execution_control_guard": 1286, "observable_execution_denominator_guard": 248, "observable_execution_follow_scorer": 558, "observable_execution_horizon_repair": 29, "observable_execution_source_policy_guard": 20, "observable_execution_source_repair": 239, "old_backfill_source_bias_guard": 7, "old_backfill_source_context": 2, "opening_drive_contract_exclusion": 12, "opening_drive_source_gap": 2, "opening_drive_source_projection": 6, "opportunity_lifecycle_reset_policy_source_guard": 3, "orderflow_pending_lifecycle_source_gap": 5, "pending_lifecycle_fill_cancel_expiry_source_capture": 548, "pipeline_state/RESEARCH_RUNTIME_HALT.flag": 1, "pre_ai_h1_poi_bearish_source_gap": 73, "pre_ai_h1_poi_bullish_source_gap": 173, "prefill_delivery_adverse_reversal_path": 264, "prefill_delivery_adverse_reversal_path_retest_control": 10, "q62_common_trigger_runner_giveup_guard": 4, "q62_partial_close_policy_guard": 1, "q62_partial_close_scheme_result": 1004, "q62_variant_c_shadow_context": 1, "q62_variant_d_shadow_queue_guard": 3, "ready8_card_rank_redundancy_kill": 1, "ready8_control_only_quarantine": 1, "ready8_denominator_overlap_requirement": 1, "ready8_exact_geometry_source_requirement": 1, "ready8_fail_closed_source_policy": 1, "ready8_promotion_validation_block": 1, "ready8_source_control_repair_requirement": 1, "ready8_weak_overlap_shadow_only": 1, "registry_scorer_module": 1869, "registry_scorer_module_system": 102, "rejected_candidate_blocked_limit_value": 38, "rejected_candidate_c1_failed_value": 27, "rejected_candidate_c2_m15_opposing_value": 17, "rejected_candidate_c3_direction_mismatch_value": 13, "rejected_candidate_no_qualifying_h1_poi_value": 17, "rejected_candidate_no_reason_logged_value": 10, "rejected_candidate_ob_proximity_value": 20, "rejected_candidate_other_unknown_value": 6, "rejected_candidate_parse_error_value": 8, "rejected_candidate_prescreen_no_direction_value": 20, "risk_ai_cost_control": 21, "risk_cost_fill_proxy": 477, "risk_proxy_gap_status": 9, "risk_proxy_stress_cost_context": 527, "risk_rstyle_proxy_outcome": 70, "risk_sizing_policy": 43, "risk_source_cost_cap": 108, "risk_source_stress_acquisition": 87, "risk_stress_robustness": 286, "scid_combined_entry_reference_source_gap": 3014, "scid_combined_framework_setup_source_gap": 3014, "scid_combined_lifecycle_source_gap": 3014, "scid_combined_ltf_path_source_gap": 3014, "scid_combined_orderflow_depth_source_gap": 3014, "scid_combined_poi_bounds_source_gap": 3014, "scid_combined_side_direction_source_gap": 3014, "scid_combined_stop_reference_source_gap": 3014, "scid_combined_target_reference_source_gap": 3014, "scid_forward_source_capture_lifecycle": 3, "scid_future_capture_baseline_control": 190, "scid_future_capture_entry_reference": 190, "scid_future_capture_framework_setup": 190, "scid_future_capture_lifecycle_status": 73, "scid_future_capture_side_direction": 190, "scid_future_capture_stop_reference": 190, "scid_future_capture_target_reference": 190, "scid_neutral_target_candidate_context": 13104, "scid_neutral_target_control_context": 9, "scid_noapi_descriptor_control_replay_attribution": 59, "scid_noapi_forbidden_surface_guard": 3014, "scid_noapi_future_capture_source_acquisition": 91, "scid_noapi_ltf_orderflow_source_acquisition": 65, "scid_noapi_missing_source_acquisition": 1014, "scid_noapi_replay_attribution_only": 22858, "scid_strategy_field_ltf_orderflow_source_acquisition": 6028, "scid_strategy_field_missing_source_acquisition": 21098, "scid_target_control_card_rank_non_discriminative": 678, "scid_target_horizon_fail_closed_source_repair": 11058, "scid_target_horizon_neutral_only": 11, "scid_target_horizon_source_field_requirement": 128, "selector_shadow_source_guard": 3078, "session_timeframe_selector": 379, "shadow_action_required_source_gap": 12, "shadow_candidate_poi_source_gap": 4, "shadow_external_source_blocker": 15, "shadow_generic_source_materialization_gap": 58, "shadow_join_status_source_gap": 48, "shadow_path_contract_source_gap": 45, "shadow_source_guard": 48205, "sierra_depth_in_window_clear_repair": 114, "sierra_depth_live_feature_status": 3315, "sierra_depth_source_acquisition": 36, "sierra_depth_source_gap": 1010, "sierra_depth_window_sample_block": 297, "sierra_scid_source_bound_m15_bar_replay": 5150, "sl_beyond_ob_legacy_zero_buffer_source_repair": 1, "sl_beyond_ob_logger_activation": 4, "sl_beyond_ob_outcome_capture_gap": 93, "sl_beyond_ob_pass_adverse_outcome_reference": 31, "sl_beyond_ob_pass_nofill_outcome_reference": 187, "sl_beyond_ob_pass_outcome_reference": 12, "sl_beyond_ob_rejected_l2_counterfactual": 4, "source_cost_spread_bar_proxy_implication": 138, "source_repair_proof": 12669, "src/components/cross_instrument_correlation_gate.py": 1, "src/components/orchestrator.py confidence_filter_mode": 1, "src/components/permissions.py::_reject_if_touch_count_too_high": 1, "src/components/pre_ai_gates.py + src/components/candidate_features_logger.py": 1, "src/components/verification.py::_check_sl_beyond_ob": 1, "static_limit_adaptive_entry_challenger": 1, "static_limit_adaptive_entry_source_requirement": 10, "structural_lock_reentry_cost_metadata": 1096, "structural_swing_protected_stop_geometry": 84, "survivor_failure_proxy": 946, "target_stop_ordering_context_guard": 79, "target_stop_ordering_m15_bounds_avoid": 48, "target_stop_ordering_m15_bounds_follow": 102, "target_stop_ordering_m1_support_follow": 110, "target_stop_ordering_nofill_avoid": 131, "target_stop_ordering_positive_replay_avoid": 97, "target_stop_ordering_positive_replay_follow": 146, "target_stop_ordering_source_repair": 138, "target_stop_ordering_stop_first_avoid": 212, "target_stop_ordering_target_first_follow": 58, "targetstop_na_binding_repair": 13, "tick_derived_structural_source_repair": 196, "tick_m15_execution_friction_movement_dominates": 344, "tick_m15_execution_friction_spread_competes": 50, "tick_m15_execution_friction_weak_denominator": 391, "tick_m15_target_control_flat_or_negative_abs": 24, "tick_m15_target_control_negative_alignment": 26, "tick_m15_target_control_placebo_ready_positive": 42, "tick_m15_target_control_small_n_context": 328, "tick_source_recovery_geometry_join_context": 8, "tick_source_recovery_no_entry_touch_source_acquisition": 52, "tick_source_recovery_no_terminal_pending_guard": 6, "tick_source_recovery_opening_drive_source_acquisition": 163, "tick_source_recovery_ordered_path_source_acquisition": 27, "tick_source_recovery_partial_coverage_source_acquisition": 1, "tick_source_recovery_path_ready_context": 593, "tick_source_recovery_quote_tick_nofill_avoid": 58, "tick_source_recovery_separate_fill_path_source_acquisition": 11, "tick_source_recovery_source_hash_context": 2, "tick_source_recovery_stop_first_avoid": 36, "tick_source_recovery_target_first_follow": 4, "trade_index_lifecycle_action_required_source_repair": 3, "trade_record_execution_source_repair": 33, "trade_record_pending_lifecycle_context": 47, "trade_record_realized_exit_context": 5, "trade_record_rejected_decision_context": 453, "trailing_stop_v1_shadow": 5, "unified_candidate_action_branch_avoid_filter": 133, "unified_candidate_action_concentration_restress": 124, "unified_candidate_action_fillability_redesign": 213, "unified_candidate_action_market_entry_comparator": 29, "unified_candidate_action_market_gap_avoid_inverse": 69, "unified_candidate_action_market_gap_entry_geometry": 68, "unified_candidate_action_provenance_guard": 11, "unified_candidate_action_scorer_spec": 8, "unified_candidate_action_source_expansion": 309, "unified_candidate_action_symbol_session": 28, "unified_candidate_scoring_avoid_inverse_execution": 23, "unified_candidate_scoring_entry_geometry_execution": 68, "unified_candidate_variant_avoid_inverse": 23, "unified_candidate_variant_entry_geometry": 68, "unified_candidate_variant_source_expansion": 309, "unified_execution_decision_avoid_redirect": 266, "unified_execution_decision_fillability_retest_redesign": 426, "unified_execution_decision_market_entry_challenger": 58, "unified_execution_decision_market_gap_avoid_inverse": 23, "unified_execution_decision_market_gap_entry_geometry": 68, "unified_execution_decision_provenance_guard": 22, "unified_execution_decision_source_expansion_guard": 309, "unified_shadow_scorer_avoid_filter": 15, "unified_shadow_scorer_branch_failure_avoid_filter": 219, "unified_shadow_scorer_branch_proxy_scorer": 13, "unified_shadow_scorer_context": 346, "unified_shadow_scorer_control": 91, "unified_shadow_scorer_control_scored_redesign": 231, "unified_shadow_scorer_entry_geometry": 126, "unified_shadow_scorer_market_entry_comparator": 14, "unified_shadow_scorer_market_gap_avoid_filter": 15, "unified_shadow_scorer_market_gap_entry_geometry": 42, "unified_shadow_scorer_source_materialization": 433, "unified_source_materialization_execution": 309}
- Entries/exits/no-fill/risk/gate/filter/AI paths are only those already represented in generated runtime artifacts and active config before this freeze report.

## FOLLOW/AVOID/MIXED Totals

- Runtime decision totals: {"AVOID": 57896, "FOLLOW": 34554, "MIXED": 278294}
- MIXED means scoped source-acquisition, replay attribution, context guard, or non-directional guard rows already admitted by converted runtime artifacts; freeze residue cannot add broad MIXED context.

## Remaining Direct Runtime Candidates

- DIRECT_RUNTIME_CONVERSION_REQUIRED count: 0
- TESTED_SOURCE_REPAIR_OR_GUARD_REQUIRED count: 0

## Parked/Killed Residue

- REPLAY_ATTRIBUTION_ONLY_PARK: 73
  - `knowledge_base/monitoring/edge_monitor_state.json`
  - `research/operations/SHADOW_LOG_INTEGRITY_VERIFICATION_2026-05-05.json`
  - `research/operations/SHADOW_LOG_INTEGRITY_VERIFICATION_LTO014_2026-05-05.json`
  - `research/operations/SHADOW_LOG_INTEGRITY_VERIFICATION_LTO014_FINAL2_2026-05-05.json`
  - `research/operations/SHADOW_LOG_INTEGRITY_VERIFICATION_LTO014_FINAL3_2026-05-05.json`
  - `research/operations/SHADOW_LOG_INTEGRITY_VERIFICATION_LTO014_FINAL_2026-05-05.json`
  - `research/operations/SHADOW_LOG_INTEGRITY_VERIFICATION_LTO014_RERUN_2026-05-05.json`
  - `research/operations/SHADOW_LOG_INTEGRITY_VERIFICATION_LTO016_2026-05-05.json`
  - `research/operations/SHADOW_LOG_INTEGRITY_VERIFICATION_LTO017_2026-05-05.json`
  - `research/operations/SHADOW_LOG_INTEGRITY_VERIFICATION_LTO018_2026-05-05.json`
  - `research/operations/SHADOW_LOG_INTEGRITY_VERIFICATION_LTO019_2026-05-05.json`
  - `research/operations/SHADOW_LOG_INTEGRITY_VERIFICATION_LTO020_2026-05-05.json`
- LEGACY_OR_STALE_NON_OVERRIDE_PARK: 402
  - `research/a1_adr005_backtest/analysis_output.json`
  - `research/a4_trending_bull_replay_2026-04-28/a4_cohort_full.csv`
  - `research/a4_trending_bull_replay_2026-04-28/a4_realized_r_join.csv`
  - `research/academic_pipeline/data/all_evaluations_features.csv`
  - `research/academic_pipeline/data/dfii10_real_yield.json`
  - `research/academic_pipeline/data/entry_engineering_dataset.csv`
  - `research/academic_pipeline/data/post_trade_individual_v1.json`
  - `research/academic_pipeline/data/q4_entry_engineering.json`
  - `research/academic_pipeline/data/real_rates_annotated_trades.json`
  - `research/academic_pipeline/data/T3_binary_no_cot_results.json`
  - `research/academic_pipeline/data/T3_fincot_blueprint_results.json`
  - `research/academic_pipeline/data/T3_no_role_results.json`
- NEEDS_USER_DECISION_BEFORE_RUNTIME: 7
  - `research/ml_program/forensics/2026-04-29/agent_k1_decision_matrix.csv`
  - `research/program_control/LTO019_DECISION_LAYER_DIAGNOSTICS_JOIN_2026-05-05.json`
  - `research/science_program_2026_05/05_synthesis/G12_SURVIVOR_BLOCKER_DECISIONS_2026-05-06.json`
  - `research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_DUPLICATE_SOURCE_DECISION_LEDGER_2026-05-11.json`
  - `research/science_program_2026_05/06_outcome_testing/gtos_local_research_data_catalog_implementation_route/GTOS_LOCAL_RESEARCH_DATA_CATALOG_CATALOG_IMPLEMENTATION_DECISION_LEDGER_2026-05-10.json`
  - `research/science_program_2026_05/06_outcome_testing/otb6_g6_blocker_clearing_proof_pack/OTB6_G6_BLOCKER_CLEARING_DECISION_LEDGER_2026-05-07.json`
  - `research/science_program_2026_05/06_outcome_testing/oti1_covariate_source_asof_proof_pack/OTI1_BLOCKER_OWNER_APPROVAL_LEDGER_2026-05-07.json`
- WRAPPER_SUPPORT_CHILDREN_ALREADY_HANDLED_KILL: 1157
  - `.context/03_analysis/RESEARCH_GOAL_FOLLOWUP_CONTEXT_2026-05-03.md`
  - `.context/03_analysis/test_a_implications_analysis.md`
  - `.context/03_analysis/test_a_rerun_real_bos_results.md`
  - `.context/04_agents/PHASE_3_EXTERNAL_FEED_VALIDATION_REVIEW.md`
  - `.context/05_operations/c3_sprt_class_halt_playbook.md`
  - `.context/05_operations/FORWARD_CAPTURE_MONITORING_RUNBOOK_2026-05-04.json`
  - `.context/05_operations/FORWARD_CAPTURE_MONITORING_RUNBOOK_2026-05-04.md`
  - `.context/05_operations/GTOS_ACTIVE_MONITORING_CHECKPOINT_2026-05-04_0930UTC.md`
  - `.context/05_operations/GTOS_ACTIVE_MONITORING_CHECKPOINT_2026-05-04_0945UTC.md`
  - `.context/05_operations/GTOS_ACTIVE_MONITORING_CHECKPOINT_2026-05-04_1000UTC.md`
  - `.context/05_operations/GTOS_ACTIVE_MONITORING_CHECKPOINT_2026-05-04_1009UTC.md`
  - `.context/05_operations/GTOS_ACTIVE_MONITORING_CHECKPOINT_2026-05-04_1015UTC.md`
- DUPLICATE_OR_SUPERSEDED_KILL: 0

## Evidence Not Allowed To Affect Runtime Decisions

- Every row in the freeze classification ledger has `runtime_pressure_allowed=false` and `legacy_support_override_allowed=false`.
- Parked legacy/general/support/source-capture residue cannot cast FOLLOW, AVOID, MIXED, risk, selector, AI, entry, exit, no-fill, source-component, or gate pressure.
- Legacy/v2/v3/v4/live-shadow/support residue cannot override CP280/CP281/CP282, Main Orch, READY8, expanded-market, source-bound, or newer moonshot evidence.

## Default-Off Activation / Replay / Shadow Path

- Keep actual broker operations separate.
- Use current vNext runtime/config on a demo/free live account first to observe live broker cadence, retcodes, no-fill/pending lifecycle, vNext decisions, risk multipliers, route narrowing, SL/TP geometry, and logs.
- Run offline replay/ablation from disk in a fresh session using active config, master/batch ledgers, runtime artifact summaries, and this freeze classification ledger.

## Replay/Ablation Measurement Plan

- Baseline: replay current HEAD with vNext artifacts loaded and freeze residue excluded from runtime pressure.
- Ablation: compare route/risk/gate/no-fill/AI decisions with vNext artifact families disabled by family buckets, not by old file order.
- Shadow: record matched artifact IDs, source components, decision class, risk multiplier, source-acquisition zero-risk blocks, no-fill lifecycle transitions, and SL/TP geometry deltas.
- Report: measure decision deltas, no-fill lifecycle deltas, stop-first/fill-quality changes, risk multiplier distribution, and any blank-anchor match attempts.

## Risks Before Replay

- Artifact matching must be monitored for blank-anchor rows and broad context rows.
- Demo/live observation must confirm broker retcodes, pending lifecycle, no-fill lifecycle, route narrowing, and logs before any funded-account consideration.
- Parked residue may still contain historical insight, but it is intentionally barred from runtime pressure until a fresh explicit admission review.

## Handoff Instruction

Start a fresh replay/ablation session from disk using this report, current HEAD, active config, current master and batch ledgers, generated runtime artifact summaries, and the freeze classification ledger. Do not continue conversion-wave selection from old context. Do not run replay in this freeze session.
