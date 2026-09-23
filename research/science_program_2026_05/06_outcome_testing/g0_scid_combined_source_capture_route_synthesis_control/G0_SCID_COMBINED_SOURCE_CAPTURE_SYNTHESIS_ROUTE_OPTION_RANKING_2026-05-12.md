# Route Option Ranking

- **route_id:** `G0_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_SYNTHESIS_CONTROL`
- **evidence_class:** `G0_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_SYNTHESIS_CONTROL_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "artifact_family": "route_option_ranking",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G0_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_SYNTHESIS_CONTROL_ONLY",
  "generated_at_utc": "2026-05-12T02:35:23Z",
  "high_value_prompt_pack_paths": {
    "SCID_DIRECTION_AWARE_RESULT_DESIGN_PREREGISTRATION_FROM_CAPTURE_AUDIT_GOAL_PROMPT_2026-05-12.md": "research/science_program_2026_05/04_goal_prompts/SCID_DIRECTION_AWARE_RESULT_DESIGN_PREREGISTRATION_FROM_CAPTURE_AUDIT_GOAL_PROMPT_2026-05-12.md",
    "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_GOAL_PROMPT_2026-05-12.md": "research/science_program_2026_05/04_goal_prompts/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_GOAL_PROMPT_2026-05-12.md",
    "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_CAPTURE_AUDIT_GOAL_PROMPT_2026-05-12.md": "research/science_program_2026_05/04_goal_prompts/SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_CAPTURE_AUDIT_GOAL_PROMPT_2026-05-12.md",
    "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_ACCEPTED_DESCRIPTORS_GOAL_PROMPT_2026-05-12.md": "research/science_program_2026_05/04_goal_prompts/SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_ACCEPTED_DESCRIPTORS_GOAL_PROMPT_2026-05-12.md"
  },
  "live_effect": false,
  "not_selected_as_rank_1_reasons": {
    "SCID_BROADER_SOURCE_CONTROL_SEARCH_EXTENSION": "Accepted G12 saturation found no concrete gap; further search should be targeted, not a substitute for capture implementation.",
    "SCID_DIRECTION_AWARE_RESULT_DESIGN_PREREGISTRATION": "Blocked until side/entry/stop/target/POI/framework/lifecycle source fields are prospectively captured or explicitly recovered and G12-accepted.",
    "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": "High-value explanatory expansion, but rank 1 must first materialize the accepted core capture schema so expansion fields have stable parser/redaction/as-of contracts.",
    "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_ACCEPTED_DESCRIPTORS": "High-value follow-up after schemas/descriptors are concrete; not rank 1 because current accepted descriptors do not include strategy intent."
  },
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
  "rank_1_prompt_path": "research/science_program_2026_05/04_goal_prompts/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_GOAL_PROMPT_2026-05-12.md",
  "rank_1_route": "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE",
  "ranking_method": "Aggressive value-weighted ranking inside the same G0 source/control evidence class; safety is a boundary, not the sole objective.",
  "required_route_options_evaluated": [
    "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE",
    "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
    "SCID_BROADER_SOURCE_CONTROL_SEARCH_EXTENSION",
    "SCID_DIRECTION_AWARE_RESULT_DESIGN_PREREGISTRATION",
    "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_ACCEPTED_DESCRIPTORS",
    "SCID_FORWARD_SHADOW_CAPTURE_MONITORING_ALIGNMENT"
  ],
  "route_id": "G0_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_SYNTHESIS_CONTROL",
  "routes": [
    {
      "decision": "SELECT_RANK_1_STARTER",
      "evidence": "G12 accepted exact capture groups and the builder readiness status is OFFLINE_CAPTURE_SCHEMA_READY_G12_AUDIT_REQUIRED_NO_LIVE_WIRING.",
      "prompt_path": "research/science_program_2026_05/04_goal_prompts/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_GOAL_PROMPT_2026-05-12.md",
      "rank": 1,
      "route_id": "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE",
      "scores_1_10": {
        "anti_boxing_breadth": 8,
        "boundary_safety": 10,
        "g12_auditability": 10,
        "implementation_burden_inverse": 8,
        "information_gain": 9,
        "speed_to_edge_evidence": 10
      },
      "weighted_total_score": 9.25,
      "why_not_safest_default": "This is not a passive safe summary; it turns the accepted contract into executable offline schemas, validators, fixtures, and read-only alignment without crossing live wiring."
    },
    {
      "decision": "COMBINE_IN_RANK_1_AS_READ_ONLY_ALIGNMENT",
      "evidence": "The accepted contract names future loggers; current G0 can align schemas to existing shadow/live outputs read-only, but cannot wire new logger calls.",
      "prompt_path": "research/science_program_2026_05/04_goal_prompts/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_GOAL_PROMPT_2026-05-12.md",
      "rank": 2,
      "route_id": "SCID_FORWARD_SHADOW_CAPTURE_MONITORING_ALIGNMENT",
      "scores_1_10": {
        "anti_boxing_breadth": 8,
        "boundary_safety": 10,
        "g12_auditability": 9,
        "implementation_burden_inverse": 9,
        "information_gain": 8,
        "speed_to_edge_evidence": 9
      },
      "weighted_total_score": 8.9,
      "why_combined": "Splitting read-only alignment from offline schema would create avoidable serial work inside the same evidence class."
    },
    {
      "decision": "EMIT_HIGH_VALUE_PARALLEL_OR_FOLLOWUP_PROMPT",
      "evidence": "G12 accepted LTF and orderflow/proxy as recoverable/requestable market context with capture contracts, not strategy intent.",
      "prompt_path": "research/science_program_2026_05/04_goal_prompts/SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_CAPTURE_AUDIT_GOAL_PROMPT_2026-05-12.md",
      "rank": 3,
      "route_id": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "scores_1_10": {
        "anti_boxing_breadth": 10,
        "boundary_safety": 8,
        "g12_auditability": 8,
        "implementation_burden_inverse": 7,
        "information_gain": 9,
        "speed_to_edge_evidence": 8
      },
      "weighted_total_score": 8.35,
      "why_high_value": "This keeps the science horizon open across path geometry, orderflow, proxy, liquidity, volatility, and session descriptors."
    },
    {
      "decision": "EMIT_HIGH_VALUE_FOLLOWUP_PROMPT_AFTER_SCHEMA_AND_DESCRIPTOR_FIELDS",
      "evidence": "The accepted 3,014 substrate and future capture fields can seed broad no-API hypothesis families without opening outcomes.",
      "prompt_path": "research/science_program_2026_05/04_goal_prompts/SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_ACCEPTED_DESCRIPTORS_GOAL_PROMPT_2026-05-12.md",
      "rank": 4,
      "route_id": "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_ACCEPTED_DESCRIPTORS",
      "scores_1_10": {
        "anti_boxing_breadth": 10,
        "boundary_safety": 8,
        "g12_auditability": 8,
        "implementation_burden_inverse": 6,
        "information_gain": 8,
        "speed_to_edge_evidence": 7
      },
      "weighted_total_score": 7.72,
      "why_not_now_as_rank_1": "Factory output is weaker until offline schemas and descriptor availability are concrete enough to prevent vague hypotheses."
    },
    {
      "decision": "EMIT_GATED_FOLLOWUP_PROMPT_NOT_RANK_1",
      "evidence": "Result design remains blocked because all seven historical strategy-intent families are non-generatable for all 3,014 rows.",
      "prompt_path": "research/science_program_2026_05/04_goal_prompts/SCID_DIRECTION_AWARE_RESULT_DESIGN_PREREGISTRATION_FROM_CAPTURE_AUDIT_GOAL_PROMPT_2026-05-12.md",
      "rank": 5,
      "route_id": "SCID_DIRECTION_AWARE_RESULT_DESIGN_PREREGISTRATION",
      "scores_1_10": {
        "anti_boxing_breadth": 9,
        "boundary_safety": 7,
        "g12_auditability": 8,
        "implementation_burden_inverse": 5,
        "information_gain": 8,
        "speed_to_edge_evidence": 5
      },
      "weighted_total_score": 6.85,
      "why_gated": "Preregistration is valuable after G12-accepted source fields; doing it first risks designing around missing intent."
    },
    {
      "decision": "DEFER_UNLESS_NEW_CONCRETE_SOURCE_GAP_APPEARS",
      "evidence": "G12 accepted saturation across required roots with zero new explicit historical strategy-intent recoveries and weak symbol-time leads not accepted without SCID binding.",
      "prompt_path": null,
      "rank": 6,
      "route_id": "SCID_BROADER_SOURCE_CONTROL_SEARCH_EXTENSION",
      "scores_1_10": {
        "anti_boxing_breadth": 8,
        "boundary_safety": 8,
        "g12_auditability": 8,
        "implementation_burden_inverse": 6,
        "information_gain": 5,
        "speed_to_edge_evidence": 5
      },
      "weighted_total_score": 6.1,
      "why_not_rank_1": "More broad search is lower-value than implementing the accepted capture contract unless a concrete new source class is identified."
    }
  ],
  "same_class_routes_combined_now": [
    "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE",
    "SCID_FORWARD_SHADOW_CAPTURE_MONITORING_ALIGNMENT"
  ],
  "schema_version": "g0_scid_combined_source_capture_synthesis_v1",
  "validation_safe": false
}
```
