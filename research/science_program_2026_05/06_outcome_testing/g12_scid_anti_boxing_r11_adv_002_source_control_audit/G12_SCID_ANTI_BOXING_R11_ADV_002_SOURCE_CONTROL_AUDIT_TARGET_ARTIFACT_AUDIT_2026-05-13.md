# Target Artifact Audit

```json
{
  "allowlist_required_fields_present": [
    "candidate_input_row_id",
    "canonical_counting_row_id",
    "collision_policy",
    "decision_asof_utc",
    "duplicate_proxy_denominator_key",
    "group_membership_manifest_sha256",
    "group_membership_version",
    "row_hash",
    "source_hash",
    "source_observed_asof_utc"
  ],
  "artifact_family": "target_artifact_audit",
  "audit_current_head": "fce52bec docs: refresh state after g12 prompt hardening",
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "controlling_prompt": "research/science_program_2026_05/04_goal_prompts/G12_SCID_ANTI_BOXING_R11_ADV_002_SOURCE_CONTROL_AUDIT_GOAL_PROMPT_2026-05-13.md",
  "credentials_touched": false,
  "denylist_required_fields_present": [
    "broker_account_history",
    "expectancy",
    "future_source_context",
    "order_deal_position_id",
    "performance",
    "pnl",
    "post_fill_path_label",
    "promotion",
    "r_multiple",
    "stop_hit",
    "target_hit",
    "trade_result",
    "win_loss"
  ],
  "evidence_class": "G12_ADV002_SOURCE_CONTROL_AUDIT_OR_SYNTHESIS_ONLY",
  "fail_closed_statuses_present": [
    "CANONICAL_ROW_AMBIGUOUS",
    "FORBIDDEN_FIELD_PRESENT",
    "MISSING_CANDIDATE_ID",
    "MISSING_COLLISION_POLICY",
    "MISSING_DUPLICATE_KEY",
    "MISSING_GROUP_MEMBERSHIP_VERSION",
    "MISSING_SOURCE_HASH",
    "ROW_HASH_EOL_FRICTION_UNRESOLVED",
    "SESSION_SYMBOL_TIMEFRAME_COLLISION_UNRESOLVED"
  ],
  "generated_at_utc": "2026-05-13T04:47:27Z",
  "live_effect": false,
  "manifest_hash_audit": {
    "mismatch_count": 0,
    "mismatches": [],
    "rows": [
      {
        "actual_sha256": "858d2b5752553c013f932e10652de536fb1e23615be3b737725c448d5cf56ca0",
        "exists": true,
        "is_manifest_self_row": false,
        "manifest_sha256": "858d2b5752553c013f932e10652de536fb1e23615be3b737725c448d5cf56ca0",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_CONTEXT_ANCHOR_2026-05-13.json"
      },
      {
        "actual_sha256": "43af43f10f934c4fc81b7d79e96b82dd272cdcf42a268072500723989a0069ab",
        "exists": true,
        "is_manifest_self_row": false,
        "manifest_sha256": "43af43f10f934c4fc81b7d79e96b82dd272cdcf42a268072500723989a0069ab",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_SOURCE_CONTRACT_LEDGER_2026-05-13.json"
      },
      {
        "actual_sha256": "8a74949701cda74e7daae54b0a837a70da505d64939a976505cad995fcbd1b17",
        "exists": true,
        "is_manifest_self_row": false,
        "manifest_sha256": "8a74949701cda74e7daae54b0a837a70da505d64939a976505cad995fcbd1b17",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_ROUTE_DECISION_LEDGER_2026-05-13.json"
      },
      {
        "actual_sha256": "5dde7d6c543fb2f2ba38d27ad1788afa5dad4debf9a1a494373f5b96a14a1850",
        "exists": true,
        "is_manifest_self_row": false,
        "manifest_sha256": "5dde7d6c543fb2f2ba38d27ad1788afa5dad4debf9a1a494373f5b96a14a1850",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_DUPLICATE_DENOMINATOR_POLICY_2026-05-13.json"
      },
      {
        "actual_sha256": "da1966a220007f32aae6108fd55ca48a855750833a6b4626db6aec653bc6b057",
        "exists": true,
        "is_manifest_self_row": false,
        "manifest_sha256": "da1966a220007f32aae6108fd55ca48a855750833a6b4626db6aec653bc6b057",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_ASOF_NOLEAK_DUPLICATE_POLICY_2026-05-13.json"
      },
      {
        "actual_sha256": "49cbf5f535f9100b74869be9e04dd72ed4361c472ded35a38c238dad0a52c351",
        "exists": true,
        "is_manifest_self_row": false,
        "manifest_sha256": "49cbf5f535f9100b74869be9e04dd72ed4361c472ded35a38c238dad0a52c351",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_SEARCHED_ROOT_LEDGER_2026-05-13.json"
      },
      {
        "actual_sha256": "9827edc7e8c407fe591149cee81af3b2443d7216b0878d2f668762f04c37aa8a",
        "exists": true,
        "is_manifest_self_row": false,
        "manifest_sha256": "9827edc7e8c407fe591149cee81af3b2443d7216b0878d2f668762f04c37aa8a",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_NEGATIVE_EVIDENCE_BLOCKER_LEDGER_2026-05-13.json"
      },
      {
        "actual_sha256": "4edf07122cb4a4c12fef150f6cdaedfacbd9ce1651246652c8363dcb989b2dd7",
        "exists": true,
        "is_manifest_self_row": false,
        "manifest_sha256": "4edf07122cb4a4c12fef150f6cdaedfacbd9ce1651246652c8363dcb989b2dd7",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_SATURATION_SELF_RED_TEAM_2026-05-13.json"
      },
      {
        "actual_sha256": "c1eaa08fa5f64299434101e310e2410c2942e7ca2ee5d0cf2a08c796734898f2",
        "exists": true,
        "is_manifest_self_row": false,
        "manifest_sha256": "c1eaa08fa5f64299434101e310e2410c2942e7ca2ee5d0cf2a08c796734898f2",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_SATURATION_SELF_RED_TEAM_2026-05-13.md"
      },
      {
        "actual_sha256": "ee19a94063ebf69fea546f9408f31feaeea7777003a5bc6672d4c742c263cf71",
        "exists": true,
        "is_manifest_self_row": false,
        "manifest_sha256": "ee19a94063ebf69fea546f9408f31feaeea7777003a5bc6672d4c742c263cf71",
        "ok": true,
        "path": "research/science_program_2026_05/04_goal_prompts/G12_SCID_ANTI_BOXING_R11_ADV_002_SOURCE_CONTROL_AUDIT_GOAL_PROMPT_2026-05-13.md"
      },
      {
        "actual_sha256": "997b3bfa097e4a557e6f76bb2ef244d6e9f2657b2335318e41e7ce85650105dd",
        "exists": true,
        "is_manifest_self_row": false,
        "manifest_sha256": "997b3bfa097e4a557e6f76bb2ef244d6e9f2657b2335318e41e7ce85650105dd",
        "ok": true,
        "path": "research/science_program_2026_05/04_goal_prompts/G0_SCID_ANTI_BOXING_R11_ADV_002_DENOMINATOR_CONTROL_SYNTHESIS_GOAL_PROMPT_2026-05-13.md"
      },
      {
        "actual_sha256": "1b65fc31cf8da324952233f0bd92c5f7656ddb5e3669284f534b0d6efcec0616",
        "exists": true,
        "is_manifest_self_row": false,
        "manifest_sha256": "1b65fc31cf8da324952233f0bd92c5f7656ddb5e3669284f534b0d6efcec0616",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/G12_SCID_ANTI_BOXING_R11_ADV_002_SOURCE_CONTROL_AUDIT_STARTER_2026-05-13.txt"
      },
      {
        "actual_sha256": "7fc85de6b8a1dd30b711f214b7f1dc50072aa1b5287f2311d82f1d519af8da3c",
        "exists": true,
        "is_manifest_self_row": false,
        "manifest_sha256": "7fc85de6b8a1dd30b711f214b7f1dc50072aa1b5287f2311d82f1d519af8da3c",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/G0_SCID_ANTI_BOXING_R11_ADV_002_DENOMINATOR_CONTROL_SYNTHESIS_STARTER_2026-05-13.txt"
      },
      {
        "actual_sha256": "20ef1379578a78cf3ba95b3f713e8a09dd8c22f8ed4c7e558594c0fc38dd6964",
        "exists": true,
        "is_manifest_self_row": false,
        "manifest_sha256": "20ef1379578a78cf3ba95b3f713e8a09dd8c22f8ed4c7e558594c0fc38dd6964",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/build_scid_anti_boxing_r11_adv_002_2026_05_13.py"
      },
      {
        "actual_sha256": "fc4056f30f517f75f8658865f3ce5b6ce50212c133d6273665d56f718c5378e4",
        "exists": true,
        "is_manifest_self_row": false,
        "manifest_sha256": "fc4056f30f517f75f8658865f3ce5b6ce50212c133d6273665d56f718c5378e4",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/verify_scid_anti_boxing_r11_adv_002_2026_05_13.py"
      },
      {
        "actual_sha256": "4b27ecbafe5fb04e6e3c0fbf922f0d517e57d575cd15d8b561fba88b952a4fcb",
        "exists": true,
        "is_manifest_self_row": false,
        "manifest_sha256": "4b27ecbafe5fb04e6e3c0fbf922f0d517e57d575cd15d8b561fba88b952a4fcb",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/test_scid_anti_boxing_r11_adv_002_2026_05_13.py"
      },
      {
        "actual_sha256": "568a370fdb6a143067a2626c3e68dc6cf847e124cf0cd297264527601eb22645",
        "exists": true,
        "is_manifest_self_row": false,
        "manifest_sha256": "568a370fdb6a143067a2626c3e68dc6cf847e124cf0cd297264527601eb22645",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_COMPLETION_AUDIT_2026-05-13.json"
      },
      {
        "actual_sha256": "4d06810d425bf802efa4b2a8e203a2933707587a4388753ddbad3f30785cd9af",
        "exists": true,
        "is_manifest_self_row": false,
        "manifest_sha256": "4d06810d425bf802efa4b2a8e203a2933707587a4388753ddbad3f30785cd9af",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_VERIFICATION_RESULT_2026-05-13.json"
      },
      {
        "actual_sha256": "db13536718cae3f75b843f5dce79d7d026e782503b4a75443beef1882571f490",
        "exists": true,
        "is_manifest_self_row": true,
        "manifest_sha256": null,
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_OUTPUT_MANIFEST_2026-05-13.json",
        "self_hash_policy": "self-referential manifest hash omitted; use external git/blob hash for the manifest itself"
      }
    ],
    "self_hash_rows": [
      {
        "actual_sha256": "db13536718cae3f75b843f5dce79d7d026e782503b4a75443beef1882571f490",
        "exists": true,
        "is_manifest_self_row": true,
        "manifest_sha256": null,
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_OUTPUT_MANIFEST_2026-05-13.json",
        "self_hash_policy": "self-referential manifest hash omitted; use external git/blob hash for the manifest itself"
      }
    ]
  },
  "may_open_outcomes_or_results_in_this_route": false,
  "mechanisms_present": [
    "canonical_row_ambiguity",
    "cross_card_duplication",
    "denominator_drift",
    "group_membership_instability",
    "row_hash_eol_friction",
    "session_symbol_timeframe_collision"
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
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G12_SCID_ANTI_BOXING_R11_ADV_002_SOURCE_CONTROL_AUDIT",
  "safe_flag_failures": [],
  "source_requirement_statuses": {
    "candidate id": "DESIGN_READY_G12_MUST_VERIFY",
    "collision policy": "DESIGN_READY_G12_MUST_VERIFY",
    "duplicate key": "DESIGN_READY_G12_MUST_VERIFY",
    "group membership version": "PARTIAL_LOCAL_EVIDENCE_EXACT_FIELD_BLOCKER",
    "source hash": "DESIGN_READY_G12_MUST_VERIFY_WITH_EOL_POLICY"
  },
  "source_requirements_present": [
    "candidate id",
    "collision policy",
    "duplicate key",
    "group membership version",
    "source hash"
  ],
  "target_completion_focused_tests_ok": true,
  "target_context_anchor_head": "3ab07d46 docs: refresh state after scid next wave prompt hardening",
  "target_context_anchor_head_note": "builder-generation head is retained as historical metadata; current G12 audit rehashed the target manifest under audit_current_head",
  "target_required_inputs_read": [
    "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_CONTEXT_ANCHOR_2026-05-13.json",
    "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_SOURCE_CONTRACT_LEDGER_2026-05-13.json",
    "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_ROUTE_DECISION_LEDGER_2026-05-13.json",
    "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_DUPLICATE_DENOMINATOR_POLICY_2026-05-13.json",
    "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_ASOF_NOLEAK_DUPLICATE_POLICY_2026-05-13.json",
    "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_SEARCHED_ROOT_LEDGER_2026-05-13.json",
    "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_NEGATIVE_EVIDENCE_BLOCKER_LEDGER_2026-05-13.json",
    "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_SATURATION_SELF_RED_TEAM_2026-05-13.json",
    "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_COMPLETION_AUDIT_2026-05-13.json",
    "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_VERIFICATION_RESULT_2026-05-13.json",
    "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_OUTPUT_MANIFEST_2026-05-13.json"
  ],
  "target_verifier_can_mark_goal_complete": true,
  "target_verifier_ok": true,
  "validation_safe": false
}
```
