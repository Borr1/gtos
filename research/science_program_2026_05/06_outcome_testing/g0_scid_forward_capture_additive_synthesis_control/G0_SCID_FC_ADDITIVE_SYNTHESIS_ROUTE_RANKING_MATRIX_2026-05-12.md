# Route Ranking Matrix

- **route_id:** `G0_SCID_FORWARD_CAPTURE_ADDITIVE_SYNTHESIS_CONTROL`
- **evidence_class:** `G0_SCID_FORWARD_CAPTURE_ADDITIVE_SYNTHESIS_CONTROL_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "activation_route_is_nonblocking_followup_not_repair": true,
  "artifact_family": "route_ranking_matrix",
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G0_SCID_FORWARD_CAPTURE_ADDITIVE_SYNTHESIS_CONTROL_ONLY",
  "generated_at_utc": "2026-05-12T11:43:44Z",
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
  "rank_1_reason": "The no-API 40-card/8-domain preregistration and replay-input design has the highest evidence gain with no dependency on live row landing or owner-approved restart timing.",
  "rank_1_route": "SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN",
  "required_route_families_present": true,
  "route_id": "G0_SCID_FORWARD_CAPTURE_ADDITIVE_SYNTHESIS_CONTROL",
  "routes": [
    {
      "dependency_state": "not blocked by no-restart/no-live-row landing",
      "objective": "Map the accepted 40 hypothesis cards across 8 science domains to additive SCID capture groups, freeze source fields, eligibility, denominator keys, duplicate policy, as-of rules, input-packet requirements, and no-API replay-input design without opening results.",
      "parallel_ready": true,
      "prompt_path": "research/science_program_2026_05/04_goal_prompts/SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN_FROM_ADDITIVE_G0_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
      "rank": 1,
      "route_id": "SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN",
      "run_state": "RUN_NOW_NO_API_NO_OUTCOME_SCORING",
      "scores_0_to_5": {
        "activation_dependency": 0,
        "dependency_readiness": 5,
        "edge_discovery_unlock": 5,
        "evidence_gain": 5,
        "nonblocking_parallelism": 5,
        "source_noleak_cleanliness": 5
      },
      "starter_path": "research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_additive_synthesis_control/SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN_FROM_ADDITIVE_G0_SYNTHESIS_STARTER_2026-05-12.txt",
      "total_score": 25,
      "why_not_boxed": [
        "not selected because it is easy to explain",
        "route advances evidence gain inside its own evidence class",
        "does not assume OB/current GTOS field completeness"
      ]
    },
    {
      "dependency_state": "can run against existing local/source-status artifacts before live rows land",
      "objective": "Expand LTF/orderflow/proxy source-status validity around the accepted fail-closed SCID fields: search local-heavy roots and accepted source contracts, classify recoverable versus non-generatable fields, define as-of/hash/parser requirements, and identify proxy validity checks without paid pulls.",
      "parallel_ready": true,
      "prompt_path": "research/science_program_2026_05/04_goal_prompts/SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_VALIDITY_EXPANSION_FROM_ADDITIVE_G0_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
      "rank": 2,
      "route_id": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_VALIDITY_EXPANSION",
      "run_state": "RUN_NOW_SOURCE_STATUS_AND_VALIDITY_ONLY",
      "scores_0_to_5": {
        "activation_dependency": 0,
        "dependency_readiness": 4,
        "edge_discovery_unlock": 5,
        "evidence_gain": 5,
        "nonblocking_parallelism": 5,
        "source_noleak_cleanliness": 4
      },
      "starter_path": "research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_additive_synthesis_control/SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_VALIDITY_EXPANSION_FROM_ADDITIVE_G0_SYNTHESIS_STARTER_2026-05-12.txt",
      "total_score": 23,
      "why_not_boxed": [
        "not selected because it is easy to explain",
        "route advances evidence gain inside its own evidence class",
        "does not assume OB/current GTOS field completeness"
      ]
    },
    {
      "dependency_state": "can build health checks now; strict non-empty live verification waits for expected rows",
      "objective": "Build or specify a forward source-capture health guard for SCID rows: append-only schema checks, safe-flag checks, row freshness, missing-group status, fail-closed source-status summaries, and honest empty-path behavior without scoring any outcome.",
      "parallel_ready": true,
      "prompt_path": "research/science_program_2026_05/04_goal_prompts/SCID_FORWARD_CAPTURE_MONITORING_HEALTH_GUARD_FROM_ADDITIVE_G0_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
      "rank": 3,
      "route_id": "SCID_FORWARD_CAPTURE_MONITORING_HEALTH_GUARD",
      "run_state": "RUN_NOW_SOURCE_CONTROL_HEALTH_GUARD_ONLY",
      "scores_0_to_5": {
        "activation_dependency": 1,
        "dependency_readiness": 5,
        "edge_discovery_unlock": 3,
        "evidence_gain": 4,
        "nonblocking_parallelism": 4,
        "source_noleak_cleanliness": 5
      },
      "starter_path": "research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_additive_synthesis_control/SCID_FORWARD_CAPTURE_MONITORING_HEALTH_GUARD_FROM_ADDITIVE_G0_SYNTHESIS_STARTER_2026-05-12.txt",
      "total_score": 22,
      "why_not_boxed": [
        "not selected because it is easy to explain",
        "route advances evidence gain inside its own evidence class",
        "does not assume OB/current GTOS field completeness"
      ]
    },
    {
      "dependency_state": "requires normal orchestrator reload or owner-approved controlled reload plus expected eligible row",
      "objective": "Verify additive SCID activation honesty after normal or owner-approved orchestrator reload: row landing, group counts, safe flags, append-only behavior, and default verifier without --allow-empty only when live candidate/lifecycle rows are expected.",
      "parallel_ready": false,
      "prompt_path": "research/science_program_2026_05/04_goal_prompts/SCID_FORWARD_CAPTURE_ACTIVATION_READINESS_VERIFICATION_FROM_ADDITIVE_G0_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
      "rank": 4,
      "route_id": "SCID_FORWARD_CAPTURE_ACTIVATION_READINESS_VERIFICATION",
      "run_state": "OPERATIONAL_TIMING_REQUIRED_NOT_A_REPAIR_BLOCKER",
      "scores_0_to_5": {
        "activation_dependency": 4,
        "dependency_readiness": 2,
        "edge_discovery_unlock": 3,
        "evidence_gain": 4,
        "nonblocking_parallelism": 2,
        "source_noleak_cleanliness": 5
      },
      "starter_path": "research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_additive_synthesis_control/SCID_FORWARD_CAPTURE_ACTIVATION_READINESS_VERIFICATION_FROM_ADDITIVE_G0_SYNTHESIS_STARTER_2026-05-12.txt",
      "total_score": 20,
      "why_not_boxed": [
        "not selected because it is easy to explain",
        "route advances evidence gain inside its own evidence class",
        "does not assume OB/current GTOS field completeness"
      ]
    },
    {
      "dependency_state": "blocked until source/input activation evidence, preregistered hypothesis/input packet, duplicate policy, as-of proof, and G12/G0 gate approval exist",
      "objective": "Prepare the later gate definition for a sealed result packet only after source/input prerequisites are valid. This prompt is dormant until dependencies prove the packet can be opened without leakage.",
      "parallel_ready": false,
      "prompt_path": "research/science_program_2026_05/04_goal_prompts/SCID_SEALED_RESULT_PACKET_GATE_AFTER_SOURCE_ACTIVATION_FROM_ADDITIVE_G0_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
      "rank": 5,
      "route_id": "SCID_SEALED_RESULT_PACKET_GATE_AFTER_SOURCE_ACTIVATION",
      "run_state": "DO_NOT_RUN_UNTIL_DEPENDENCY_VALID",
      "scores_0_to_5": {
        "activation_dependency": 5,
        "dependency_readiness": 1,
        "edge_discovery_unlock": 5,
        "evidence_gain": 5,
        "nonblocking_parallelism": 1,
        "source_noleak_cleanliness": 5
      },
      "starter_path": "research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_additive_synthesis_control/SCID_SEALED_RESULT_PACKET_GATE_AFTER_SOURCE_ACTIVATION_FROM_ADDITIVE_G0_SYNTHESIS_STARTER_2026-05-12.txt",
      "total_score": 22,
      "why_not_boxed": [
        "not selected because it is easy to explain",
        "route advances evidence gain inside its own evidence class",
        "does not assume OB/current GTOS field completeness"
      ]
    }
  ],
  "schema_version": "g0_scid_forward_capture_additive_synthesis_v1",
  "sealed_result_packet_route_dependency_blocked": true,
  "validation_safe": false
}
```
