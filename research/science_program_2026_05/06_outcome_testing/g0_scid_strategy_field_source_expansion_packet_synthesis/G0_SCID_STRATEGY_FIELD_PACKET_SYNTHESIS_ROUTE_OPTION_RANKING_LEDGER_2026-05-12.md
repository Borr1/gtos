# Route Option Ranking Ledger

- **route_id:** `G0_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_SYNTHESIS`
- **evidence_class:** `G0_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_SYNTHESIS_CONTROL_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "artifact_family": "route_option_ranking_ledger",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G0_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_SYNTHESIS_CONTROL_ONLY",
  "generated_at_utc": "2026-05-12T00:19:24Z",
  "live_effect": false,
  "newly_discovered_route_options_scored": [
    "SCID_ADVERSARIAL_BASELINE_AND_DENOMINATOR_CONTROL_ROUTE",
    "SCID_INPUT_ONLY_MARKET_STATE_DESCRIPTOR_ATLAS_ROUTE",
    "SCID_PROXY_MAP_AND_SOURCE_PARITY_ROUTE",
    "SCID_SOURCE_SAFE_MSO_SNAPSHOT_RECONSTRUCTION_ROUTE",
    "SCID_COHORT_EXPANSION_SOURCE_CONTRACT_ROUTE",
    "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_ROUTE"
  ],
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
  "parallel_bundle_rationale": "Rank 1 closes source-state and future capture; rank 2 expands path/orderflow/proxy explanatory fields; rank 3 freezes result-design prerequisites after source acceptance. They are complementary but ordered to prevent result/control confusion.",
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "rank_1_route": "SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE",
  "ranking_method": "Weighted score prioritizes speed to edge testing and expected information gain while retaining source recoverability, G12 auditability, future validation readiness, implementation burden, and anti-boxing breadth.",
  "required_route_options_scored": [
    "SCID_STRATEGY_SOURCE_FIELD_FORWARD_CAPTURE_IMPLEMENTATION_CONTRACT",
    "SCID_STRATEGY_FIELD_BROADER_HISTORICAL_SOURCE_SEARCH",
    "SCID_DIRECTION_AWARE_RESULT_DESIGN",
    "SCID_LTF_AND_ORDERFLOW_PROXY_SOURCE_EXPANSION",
    "SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE"
  ],
  "route_id": "G0_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_SYNTHESIS",
  "routes": [
    {
      "anti_boxing_breadth_score_1_10": 9,
      "decision": "SELECT_AS_RANK_1_BUNDLE_LEAD",
      "expected_information_gain_score_1_10": 9,
      "future_validation_readiness_score_1_10": 7,
      "g12_auditability_score_1_10": 9,
      "implementation_burden_inverse_score_1_10": 7,
      "rank": 1,
      "rationale": "Fastest constructive route because it first exhausts recoverable source-state search, then freezes capture for true historical gaps without waiting passively.",
      "route_id": "SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE",
      "source_recoverability_score_1_10": 8,
      "speed_to_edge_testing_score_1_10": 9,
      "weighted_total_score": 8.5
    },
    {
      "anti_boxing_breadth_score_1_10": 8,
      "decision": "INCLUDE_IN_RANK_1_COMBINED_ROUTE",
      "expected_information_gain_score_1_10": 9,
      "future_validation_readiness_score_1_10": 8,
      "g12_auditability_score_1_10": 9,
      "implementation_burden_inverse_score_1_10": 7,
      "rank": 2,
      "rationale": "Directly closes future side/entry/stop/target/POI/framework/lifecycle capture requirements for direction-aware testing.",
      "route_id": "SCID_STRATEGY_SOURCE_FIELD_FORWARD_CAPTURE_IMPLEMENTATION_CONTRACT",
      "source_recoverability_score_1_10": 6,
      "speed_to_edge_testing_score_1_10": 8,
      "weighted_total_score": 8.0
    },
    {
      "anti_boxing_breadth_score_1_10": 9,
      "decision": "EMIT_PARALLEL_RANK_2_PROMPT",
      "expected_information_gain_score_1_10": 8,
      "future_validation_readiness_score_1_10": 6,
      "g12_auditability_score_1_10": 8,
      "implementation_burden_inverse_score_1_10": 6,
      "rank": 3,
      "rationale": "Adds path-shape and market-context explanatory fields that can expose mechanisms beyond current GTOS frameworks without inventing strategy intent.",
      "route_id": "SCID_LTF_AND_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "source_recoverability_score_1_10": 7,
      "speed_to_edge_testing_score_1_10": 7,
      "weighted_total_score": 7.33
    },
    {
      "anti_boxing_breadth_score_1_10": 8,
      "decision": "MERGE_REQUIREMENTS_INTO_RESULT_DESIGN_PREREG",
      "expected_information_gain_score_1_10": 7,
      "future_validation_readiness_score_1_10": 7,
      "g12_auditability_score_1_10": 9,
      "implementation_burden_inverse_score_1_10": 7,
      "rank": 4,
      "rationale": "Prevents market-state-only/session-only behavior from being mistaken for a strategy effect in later testing.",
      "route_id": "SCID_ADVERSARIAL_BASELINE_AND_DENOMINATOR_CONTROL_ROUTE",
      "source_recoverability_score_1_10": 8,
      "speed_to_edge_testing_score_1_10": 6,
      "weighted_total_score": 7.21
    },
    {
      "anti_boxing_breadth_score_1_10": 9,
      "decision": "KEEP_AS_FOLLOW_ON_SOURCE_DESCRIPTOR_ROUTE",
      "expected_information_gain_score_1_10": 7,
      "future_validation_readiness_score_1_10": 5,
      "g12_auditability_score_1_10": 8,
      "implementation_burden_inverse_score_1_10": 6,
      "rank": 5,
      "rationale": "Broadens geometry, topology, session, volatility, and proxy descriptors beyond current frameworks while staying source-only.",
      "route_id": "SCID_INPUT_ONLY_MARKET_STATE_DESCRIPTOR_ATLAS_ROUTE",
      "source_recoverability_score_1_10": 8,
      "speed_to_edge_testing_score_1_10": 7,
      "weighted_total_score": 7.13
    },
    {
      "anti_boxing_breadth_score_1_10": 7,
      "decision": "INCLUDE_IN_RANK_1_COMBINED_ROUTE",
      "expected_information_gain_score_1_10": 6,
      "future_validation_readiness_score_1_10": 5,
      "g12_auditability_score_1_10": 8,
      "implementation_burden_inverse_score_1_10": 8,
      "rank": 6,
      "rationale": "Worth a finite search because explicit source-state may exist in adjacent artifacts, but G12 already accepted current fail-closed absence so this should not block capture design.",
      "route_id": "SCID_STRATEGY_FIELD_BROADER_HISTORICAL_SOURCE_SEARCH",
      "source_recoverability_score_1_10": 5,
      "speed_to_edge_testing_score_1_10": 8,
      "weighted_total_score": 6.77
    },
    {
      "anti_boxing_breadth_score_1_10": 8,
      "decision": "KEEP_AS_ORDERFLOW_PROXY_SUBROUTE",
      "expected_information_gain_score_1_10": 7,
      "future_validation_readiness_score_1_10": 5,
      "g12_auditability_score_1_10": 8,
      "implementation_burden_inverse_score_1_10": 5,
      "rank": 7,
      "rationale": "Useful for futures/CFD transfer and instrument-specific context, especially for non-XAU instruments.",
      "route_id": "SCID_PROXY_MAP_AND_SOURCE_PARITY_ROUTE",
      "source_recoverability_score_1_10": 7,
      "speed_to_edge_testing_score_1_10": 6,
      "weighted_total_score": 6.59
    },
    {
      "anti_boxing_breadth_score_1_10": 8,
      "decision": "REGISTER_AS_HISTORICAL_RECOVERY_EXPERIMENT",
      "expected_information_gain_score_1_10": 8,
      "future_validation_readiness_score_1_10": 6,
      "g12_auditability_score_1_10": 7,
      "implementation_burden_inverse_score_1_10": 4,
      "rank": 8,
      "rationale": "Could recover as-of structure fields if source-safe MSO snapshots exist, but it must fail closed if it would reconstruct intent from price.",
      "route_id": "SCID_SOURCE_SAFE_MSO_SNAPSHOT_RECONSTRUCTION_ROUTE",
      "source_recoverability_score_1_10": 4,
      "speed_to_edge_testing_score_1_10": 5,
      "weighted_total_score": 6.05
    },
    {
      "anti_boxing_breadth_score_1_10": 7,
      "decision": "DEFER_UNTIL_FIELD_CONTRACT_EXISTS",
      "expected_information_gain_score_1_10": 6,
      "future_validation_readiness_score_1_10": 4,
      "g12_auditability_score_1_10": 8,
      "implementation_burden_inverse_score_1_10": 5,
      "rank": 9,
      "rationale": "More rows are useful only after source-field joins and duplicate policy are frozen.",
      "route_id": "SCID_COHORT_EXPANSION_SOURCE_CONTRACT_ROUTE",
      "source_recoverability_score_1_10": 7,
      "speed_to_edge_testing_score_1_10": 5,
      "weighted_total_score": 5.96
    },
    {
      "anti_boxing_breadth_score_1_10": 8,
      "decision": "EMIT_GATED_RANK_3_PROMPT_AFTER_SOURCE_ACCEPTANCE",
      "expected_information_gain_score_1_10": 8,
      "future_validation_readiness_score_1_10": 5,
      "g12_auditability_score_1_10": 7,
      "implementation_burden_inverse_score_1_10": 6,
      "rank": 10,
      "rationale": "High future value, but not ready until fail-closed strategy-intent/source-state families are closed or prospectively captured and accepted by G12.",
      "route_id": "SCID_DIRECTION_AWARE_RESULT_DESIGN",
      "source_recoverability_score_1_10": 3,
      "speed_to_edge_testing_score_1_10": 4,
      "weighted_total_score": 5.83
    },
    {
      "anti_boxing_breadth_score_1_10": 9,
      "decision": "DEFER_UNTIL_SOURCE_FIELDS_AND_PREREG",
      "expected_information_gain_score_1_10": 8,
      "future_validation_readiness_score_1_10": 5,
      "g12_auditability_score_1_10": 7,
      "implementation_burden_inverse_score_1_10": 5,
      "rank": 11,
      "rationale": "Can later turn source fields into candidate hypotheses without AI/API, but would be premature before source acceptance.",
      "route_id": "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_ROUTE",
      "source_recoverability_score_1_10": 4,
      "speed_to_edge_testing_score_1_10": 3,
      "weighted_total_score": 5.69
    }
  ],
  "schema_version": "g0_scid_strategy_field_packet_synthesis_v1",
  "selected_route_bundle": [
    {
      "prompt_path": "research/science_program_2026_05/04_goal_prompts/SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_GOAL_PROMPT_2026-05-12.md",
      "rank": 1,
      "route_id": "SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE"
    },
    {
      "prompt_path": "research/science_program_2026_05/04_goal_prompts/SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_ROUTE_GOAL_PROMPT_2026-05-12.md",
      "rank": 2,
      "route_id": "SCID_LTF_AND_ORDERFLOW_PROXY_SOURCE_EXPANSION"
    },
    {
      "gate": "Run only after rank-1 source fields and any rank-2 explanatory fields are G12-accepted.",
      "prompt_path": "research/science_program_2026_05/04_goal_prompts/SCID_DIRECTION_AWARE_RESULT_DESIGN_PREREGISTRATION_ROUTE_GOAL_PROMPT_2026-05-12.md",
      "rank": 3,
      "route_id": "SCID_DIRECTION_AWARE_RESULT_DESIGN"
    }
  ],
  "validation_safe": false
}
```
