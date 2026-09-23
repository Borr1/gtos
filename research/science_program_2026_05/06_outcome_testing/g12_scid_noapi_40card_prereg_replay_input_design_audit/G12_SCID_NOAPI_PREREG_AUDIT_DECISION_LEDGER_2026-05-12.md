# Decision Ledger

```json
{
  "accepted_g12_control_evidence_only": true,
  "accepted_promotion": false,
  "accepted_strategy_performance": false,
  "accepted_validation_execution": false,
  "artifact_family": "decision_ledger",
  "blocked_dependency_count_verified": 32,
  "card_count_verified": 40,
  "cards_per_domain_verified": {
    "adversarial_baselines_placebo_explanations": 5,
    "behavioral_game_theory_session_participant_constraints": 5,
    "execution_science_spread_slippage_fillability": 5,
    "geometry_topology_path_shape": 5,
    "macro_session_calendar_cross_asset_context": 5,
    "microstructure_orderflow_liquidity_trapped_flow": 5,
    "ml_meta_labeling_model_disagreement_uncertainty_controls": 5,
    "stochastic_tail_hazard_first_passage": 5
  },
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "check_map": {
    "blocked_dependencies_exact": true,
    "blocker_pursuit_exact": true,
    "card_domain_readiness_recomputed": true,
    "context_and_inputs_read": true,
    "expansion_quarantine_exact": true,
    "hash_manifest_parser_verifier_test_audit": true,
    "no_leak_forbidden_surface_safe_flags": true,
    "replay_packets_exact": true,
    "saturation_fairness": true
  },
  "credentials_touched": false,
  "decision_rationale": "The target route preserves the accepted 40-card denominator, exact 8-domain/5-card structure, 8/15/17 split, 8 packet designs, 32 blocked dependency rows, and 8 quarantined expansion candidates. The only issue is the target manifest's self-hash entry, documented as a nonblocking follow-up because all non-self target artifacts rehash cleanly and the G12 audit binds the current manifest hash independently.",
  "domain_count_verified": 8,
  "evidence_class": "G12_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_AUDIT_ONLY",
  "exact_nonblocking_followups": [
    {
      "evidence": [
        {
          "classification": "NONBLOCKING_SELF_REFERENTIAL_MANIFEST_HASH",
          "current_sha256": "8f43555a3dadf8a3a98c1e0ff34a390843cadb1d311d54d42ca8775dc4d8a0cd",
          "explanation": "The target manifest includes a hash of itself, which changes when the manifest is written. The G12 audit binds the current manifest hash independently instead of treating this self-entry as blocking.",
          "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_OUTPUT_MANIFEST_2026-05-12.json",
          "recorded_sha256": "e0ff93ddd6f7c06b435d669fe97a06d5881a699cfacdf7743a764c82d32988f4"
        }
      ],
      "followup_id": "NONBLOCKING_TARGET_MANIFEST_SELF_HASH_POLICY",
      "required_future_action": "In a future target-route maintenance pass, either exclude the target output manifest from its own artifact hash list or mark the self-entry as nonbinding. This is not a denominator, no-leak, packet, blocker, verifier, or result-surface failure."
    }
  ],
  "expansion_candidate_count_verified": 8,
  "generated_at_utc": "2026-05-12T13:39:30Z",
  "live_effect": false,
  "next_g0_prompt_needed": true,
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
  "outside_current_gtos_ob_framing_count_verified": 33,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "readiness_split_verified": {
    "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS": 15,
    "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": 17,
    "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY": 8
  },
  "repair_prompt_needed": false,
  "replay_packet_count_verified": 8,
  "route_id": "G12_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_AUDIT",
  "schema_version": "g12_scid_noapi_40card_prereg_replay_input_design_audit_v1",
  "target_evidence_class": "SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN_ONLY",
  "target_route_id": "SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN",
  "terminal_blockers": [],
  "terminal_decision": "ACCEPT_WITH_EXACT_NONBLOCKING_FOLLOWUPS",
  "validation_safe": false
}
```
