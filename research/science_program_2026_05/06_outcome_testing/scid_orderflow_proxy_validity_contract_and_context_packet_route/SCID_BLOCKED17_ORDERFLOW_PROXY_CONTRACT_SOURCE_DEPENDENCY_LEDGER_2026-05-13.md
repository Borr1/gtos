# Source Dependency Ledger

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

```json
{
  "artifact_family": "SOURCE_DEPENDENCY_LEDGER",
  "blocked17_card_count": 17,
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_AND_SOURCE_STATUS_ATTACH_ONLY",
  "generated_at_utc": "2026-05-13T02:48:20Z",
  "live_effect": false,
  "opens_ai_api": false,
  "opens_broker_account_order_history_deal_position_evidence": false,
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_paid_or_vendor_access": false,
  "opens_prompt_config_risk_safety_execution_canary_selector_edit": false,
  "opens_raw_market_data_blob_commit": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_strategy_edge_claims": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "proxy_card_count": 8,
  "proxy_card_level_requirement_count": 8,
  "proxy_cards": [
    {
      "card_id": "EXE-005",
      "card_level_dependency_group": "future_orderflow_depth_proxy_requirements",
      "denominator_inclusion": "blocked17_only",
      "dependency_surface_count": 9,
      "field_requirement_count": 8,
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "recommended_route_ids": [
        "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
        "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE"
      ],
      "required_capture_groups": [
        "lower_timeframe_asof_path_availability",
        "future_orderflow_depth_proxy_requirements"
      ],
      "science_domain": "execution_science_spread_slippage_fillability",
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED"
    },
    {
      "card_id": "MAC-003",
      "card_level_dependency_group": "future_orderflow_depth_proxy_requirements",
      "denominator_inclusion": "blocked17_only",
      "dependency_surface_count": 9,
      "field_requirement_count": 8,
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "recommended_route_ids": [
        "SCID_BASELINE_CONTROL_PACKET_REPAIR_AND_DUPLICATE_POLICY_ROUTE",
        "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE",
        "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE"
      ],
      "required_capture_groups": [
        "baseline_control_fields",
        "future_orderflow_depth_proxy_requirements"
      ],
      "science_domain": "macro_session_calendar_cross_asset_context",
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED"
    },
    {
      "card_id": "MIC-001",
      "card_level_dependency_group": "future_orderflow_depth_proxy_requirements",
      "denominator_inclusion": "blocked17_only",
      "dependency_surface_count": 9,
      "field_requirement_count": 8,
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "recommended_route_ids": [
        "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE"
      ],
      "required_capture_groups": [
        "future_orderflow_depth_proxy_requirements"
      ],
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED"
    },
    {
      "card_id": "MIC-002",
      "card_level_dependency_group": "future_orderflow_depth_proxy_requirements",
      "denominator_inclusion": "blocked17_only",
      "dependency_surface_count": 9,
      "field_requirement_count": 8,
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "recommended_route_ids": [
        "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
        "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE"
      ],
      "required_capture_groups": [
        "future_orderflow_depth_proxy_requirements",
        "lower_timeframe_asof_path_availability"
      ],
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED"
    },
    {
      "card_id": "MIC-003",
      "card_level_dependency_group": "future_orderflow_depth_proxy_requirements",
      "denominator_inclusion": "blocked17_only",
      "dependency_surface_count": 9,
      "field_requirement_count": 8,
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "recommended_route_ids": [
        "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE",
        "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE"
      ],
      "required_capture_groups": [
        "poi_type_bounds_source",
        "future_orderflow_depth_proxy_requirements"
      ],
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "terminal_source_status": "PARTIAL_SOURCE_STATUS_EXPANDED_WITH_NON_GENERATABLE_SOURCE_STATE_DEPENDENCY"
    },
    {
      "card_id": "MIC-004",
      "card_level_dependency_group": "future_orderflow_depth_proxy_requirements",
      "denominator_inclusion": "blocked17_only",
      "dependency_surface_count": 9,
      "field_requirement_count": 8,
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "recommended_route_ids": [
        "SCID_BASELINE_CONTROL_PACKET_REPAIR_AND_DUPLICATE_POLICY_ROUTE",
        "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE",
        "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE"
      ],
      "required_capture_groups": [
        "future_orderflow_depth_proxy_requirements",
        "baseline_control_fields"
      ],
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED"
    },
    {
      "card_id": "MIC-005",
      "card_level_dependency_group": "future_orderflow_depth_proxy_requirements",
      "denominator_inclusion": "blocked17_only",
      "dependency_surface_count": 9,
      "field_requirement_count": 8,
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "recommended_route_ids": [
        "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
        "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE"
      ],
      "required_capture_groups": [
        "future_orderflow_depth_proxy_requirements",
        "lower_timeframe_asof_path_availability"
      ],
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED"
    },
    {
      "card_id": "UNC-001",
      "card_level_dependency_group": "future_orderflow_depth_proxy_requirements",
      "denominator_inclusion": "blocked17_only",
      "dependency_surface_count": 9,
      "field_requirement_count": 8,
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "recommended_route_ids": [
        "SCID_BASELINE_CONTROL_PACKET_REPAIR_AND_DUPLICATE_POLICY_ROUTE",
        "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
        "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE",
        "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE"
      ],
      "required_capture_groups": [
        "lower_timeframe_asof_path_availability",
        "future_orderflow_depth_proxy_requirements",
        "baseline_control_fields"
      ],
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED"
    }
  ],
  "proxy_dependency_rows": [
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "EXE-005",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "derived_feature_schema_version",
      "may_score_results_now": false,
      "science_domain": "execution_science_spread_slippage_fillability",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "EXE-005",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "proxy_contract_month",
      "may_score_results_now": false,
      "science_domain": "execution_science_spread_slippage_fillability",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "EXE-005",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "proxy_instrument",
      "may_score_results_now": false,
      "science_domain": "execution_science_spread_slippage_fillability",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "EXE-005",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "proxy_mapping_version",
      "may_score_results_now": false,
      "science_domain": "execution_science_spread_slippage_fillability",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "EXE-005",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "publication_or_capture_asof_utc",
      "may_score_results_now": false,
      "science_domain": "execution_science_spread_slippage_fillability",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "EXE-005",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "source_family_scid_depth_mbo_mbp_other",
      "may_score_results_now": false,
      "science_domain": "execution_science_spread_slippage_fillability",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "EXE-005",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "source_file_pointer_or_vendor_cache_id",
      "may_score_results_now": false,
      "science_domain": "execution_science_spread_slippage_fillability",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "EXE-005",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "source_hash",
      "may_score_results_now": false,
      "science_domain": "execution_science_spread_slippage_fillability",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MAC-003",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "derived_feature_schema_version",
      "may_score_results_now": false,
      "science_domain": "macro_session_calendar_cross_asset_context",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MAC-003",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "proxy_contract_month",
      "may_score_results_now": false,
      "science_domain": "macro_session_calendar_cross_asset_context",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MAC-003",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "proxy_instrument",
      "may_score_results_now": false,
      "science_domain": "macro_session_calendar_cross_asset_context",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MAC-003",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "proxy_mapping_version",
      "may_score_results_now": false,
      "science_domain": "macro_session_calendar_cross_asset_context",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MAC-003",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "publication_or_capture_asof_utc",
      "may_score_results_now": false,
      "science_domain": "macro_session_calendar_cross_asset_context",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MAC-003",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "source_family_scid_depth_mbo_mbp_other",
      "may_score_results_now": false,
      "science_domain": "macro_session_calendar_cross_asset_context",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MAC-003",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "source_file_pointer_or_vendor_cache_id",
      "may_score_results_now": false,
      "science_domain": "macro_session_calendar_cross_asset_context",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MAC-003",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "source_hash",
      "may_score_results_now": false,
      "science_domain": "macro_session_calendar_cross_asset_context",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-001",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "derived_feature_schema_version",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-001",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "proxy_contract_month",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-001",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "proxy_instrument",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-001",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "proxy_mapping_version",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-001",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "publication_or_capture_asof_utc",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-001",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "source_family_scid_depth_mbo_mbp_other",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-001",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "source_file_pointer_or_vendor_cache_id",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-001",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "source_hash",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-002",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "derived_feature_schema_version",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-002",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "proxy_contract_month",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-002",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "proxy_instrument",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-002",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "proxy_mapping_version",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-002",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "publication_or_capture_asof_utc",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-002",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "source_family_scid_depth_mbo_mbp_other",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-002",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "source_file_pointer_or_vendor_cache_id",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-002",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "source_hash",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-003",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "derived_feature_schema_version",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-003",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "proxy_contract_month",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-003",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "proxy_instrument",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-003",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "proxy_mapping_version",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-003",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "publication_or_capture_asof_utc",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-003",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "source_family_scid_depth_mbo_mbp_other",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-003",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "source_file_pointer_or_vendor_cache_id",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-003",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "source_hash",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-004",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "derived_feature_schema_version",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-004",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "proxy_contract_month",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-004",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "proxy_instrument",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-004",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "proxy_mapping_version",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-004",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "publication_or_capture_asof_utc",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-004",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "source_family_scid_depth_mbo_mbp_other",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-004",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "source_file_pointer_or_vendor_cache_id",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-004",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "source_hash",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-005",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "derived_feature_schema_version",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-005",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "proxy_contract_month",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-005",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "proxy_instrument",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-005",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "proxy_mapping_version",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-005",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "publication_or_capture_asof_utc",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-005",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "source_family_scid_depth_mbo_mbp_other",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-005",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "source_file_pointer_or_vendor_cache_id",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "MIC-005",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "source_hash",
      "may_score_results_now": false,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "UNC-001",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "derived_feature_schema_version",
      "may_score_results_now": false,
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "UNC-001",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "proxy_contract_month",
      "may_score_results_now": false,
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "UNC-001",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "proxy_instrument",
      "may_score_results_now": false,
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "UNC-001",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "proxy_mapping_version",
      "may_score_results_now": false,
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "UNC-001",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "publication_or_capture_asof_utc",
      "may_score_results_now": false,
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "UNC-001",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "source_family_scid_depth_mbo_mbp_other",
      "may_score_results_now": false,
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "UNC-001",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "source_file_pointer_or_vendor_cache_id",
      "may_score_results_now": false,
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    },
    {
      "attached_contract_ids": [
        "SIERRA_DEPTH_MARKET_DEPTH_CONTRACT_V1",
        "SIERRA_SCID_FOOTPRINT_BID_ASK_VOLUME_CONTRACT_V1",
        "DATABENTO_CACHED_OR_DECLARED_ORDERFLOW_ARTIFACTS_CONTRACT_V1",
        "PROXY_MAPPING_REGISTRY_AND_BLOCKER_LOGS_CONTRACT_V1"
      ],
      "broker_native_cfd_truth_claim_allowed": false,
      "card_id": "UNC-001",
      "contract_attachment_status": "CONTRACT_OR_EXACT_ACCESS_REQUIREMENT_ATTACHED_CONTEXT_ONLY",
      "exact_next_requirement": "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
      "field": "source_hash",
      "may_score_results_now": false,
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
      "source_paths_or_roots_searched": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "C:/SierraChart/Data",
        "C:/Users/MSI/Documents/ai-trading-agent/data/external"
      ],
      "upstream_status": "PROXY_VALIDITY_REQUIRES_CONTRACT"
    }
  ],
  "proxy_field_requirement_count": 64,
  "proxy_requirement_surface_count": 72,
  "route_count_reconciliation": {
    "card_level_future_orderflow_depth_proxy_requirements": 8,
    "g0_ranked_route_status_count": 72,
    "g12_recomputed_field_status_count": 64,
    "interpretation": "G0 rank-level 72 equals 64 exact per-field proxy requirements plus 8 card-level orderflow/proxy dependency groups.",
    "reconciled_total_surfaces": 72
  },
  "route_id": "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE",
  "schema_version": "scid_blocked17_orderflow_proxy_contract_v1",
  "validation_safe": false
}
```
