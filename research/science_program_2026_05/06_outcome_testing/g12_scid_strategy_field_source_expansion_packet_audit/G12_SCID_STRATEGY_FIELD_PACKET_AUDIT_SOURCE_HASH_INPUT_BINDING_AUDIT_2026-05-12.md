# Source Hash Input Binding Audit

```json
{
  "artifact_family": "source_hash_input_binding_audit",
  "blocking_manifest_artifact_hash_mismatch_count": 0,
  "blocking_manifest_artifact_hash_mismatch_examples": [],
  "builder_manifest_read_fully": true,
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G12_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_AUDIT_ONLY",
  "generated_at_utc": "2026-05-11T23:49:47Z",
  "hash_warning_boundary": "The builder manifest's next_g12_prompt hash may differ after later prompt-hardening commits. That is a warning, not a packet source-input mismatch, because the prompt is the current controlling audit file and not a closure-row source artifact.",
  "live_effect": false,
  "manifest_artifact_hash_comparisons_checked": 28,
  "manifest_artifact_hash_mismatch_count": 1,
  "manifest_artifact_hash_mismatch_examples": [
    {
      "actual_sha256": "6b0d491c74646e73a9896092367a6aa8a12ebf37b501e98530998506a90aeed3",
      "artifact_name": "next_g12_prompt",
      "expected_sha256_after_build": "1e049c78adbfc0b87bdf9762fa8c5342b8d2fc59861e9e69d1c7ada766654cfe",
      "matched": false,
      "path": "research/science_program_2026_05/04_goal_prompts/G12_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_AUDIT_GOAL_PROMPT_2026-05-12.md"
    }
  ],
  "opens_ai_api": false,
  "opens_broker_account_order_history_deal_position_evidence": false,
  "opens_live_trading_behavior": false,
  "opens_paid_or_vendor_access": false,
  "opens_prompt_config_risk_safety_execution_canary_selector_edit": false,
  "opens_raw_market_data_blob_commit": false,
  "opens_result_scoring": false,
  "opens_strategy_edge_claims": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "post_build_prompt_hardening_mismatch_count": 1,
  "post_build_prompt_hardening_mismatches": [
    {
      "actual_sha256": "6b0d491c74646e73a9896092367a6aa8a12ebf37b501e98530998506a90aeed3",
      "artifact_name": "next_g12_prompt",
      "expected_sha256_after_build": "1e049c78adbfc0b87bdf9762fa8c5342b8d2fc59861e9e69d1c7ada766654cfe",
      "matched": false,
      "path": "research/science_program_2026_05/04_goal_prompts/G12_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_AUDIT_GOAL_PROMPT_2026-05-12.md"
    }
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G12_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_AUDIT",
  "schema_version": "g12_scid_strategy_field_source_expansion_packet_audit_v1",
  "source_hash_binding_ok": true,
  "source_inventory_hash_mismatch_count": 0,
  "source_inventory_hash_mismatch_examples": [],
  "source_inventory_input_hash_comparisons": [
    {
      "actual_sha256": "777c1a440e79a1871cb00a505a5c71cef4502047610acd991aeb2a06da1d0798",
      "exists": true,
      "expected_sha256": "777c1a440e79a1871cb00a505a5c71cef4502047610acd991aeb2a06da1d0798",
      "input_name": "controlling_prompt",
      "matched": true,
      "path": "research/science_program_2026_05/04_goal_prompts/SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_GOAL_PROMPT_2026-05-12.md"
    },
    {
      "actual_sha256": "67209b0f64b8990417bb51d8d2b17937d5604ed15fa449d39fa106ad849f1911",
      "exists": true,
      "expected_sha256": "67209b0f64b8990417bb51d8d2b17937d5604ed15fa449d39fa106ad849f1911",
      "input_name": "descriptor_freeze",
      "matched": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_asof_quarantined_neutral_target_execution_packet/SCID_ASOF_NEUTRAL_TARGET_DESCRIPTOR_FREEZE_LEDGER_2026-05-12.json"
    },
    {
      "actual_sha256": "a692db4032a945f588d2cb4232600262e4f7eaa2f39a0725f13f5a5e3cab5eb2",
      "exists": true,
      "expected_sha256": "a692db4032a945f588d2cb4232600262e4f7eaa2f39a0725f13f5a5e3cab5eb2",
      "input_name": "candidate_rows",
      "matched": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/SCID_ASOF_CANDIDATE_INPUT_ROWS_2026-05-11.jsonl"
    },
    {
      "actual_sha256": "35587e78cbddc922e87ef450bf5ceb91b86245805daf2be48ff62e0c98452222",
      "exists": true,
      "expected_sha256": "35587e78cbddc922e87ef450bf5ceb91b86245805daf2be48ff62e0c98452222",
      "input_name": "candidate_manifest",
      "matched": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/SCID_ASOF_CANDIDATE_INPUT_PACKET_MANIFEST_2026-05-11.json"
    },
    {
      "actual_sha256": "51cc87822caab49da466bd4b89f2c35650b8d89e01cf9450f955f2a1f4beb6dd",
      "exists": true,
      "expected_sha256": "51cc87822caab49da466bd4b89f2c35650b8d89e01cf9450f955f2a1f4beb6dd",
      "input_name": "source_field_inventory",
      "matched": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_asof_sealed_validation_target_horizon_repair/SCID_ASOF_TARGET_HORIZON_SOURCE_FIELD_INVENTORY_2026-05-11.json"
    },
    {
      "actual_sha256": "beb8537af1f0d76d39a9fe3799931f75ce3ca8ccf52e4b9d530c522403fe9f0a",
      "exists": true,
      "expected_sha256": "beb8537af1f0d76d39a9fe3799931f75ce3ca8ccf52e4b9d530c522403fe9f0a",
      "input_name": "source_field_derivation_contract",
      "matched": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_asof_sealed_validation_target_horizon_repair/SCID_ASOF_TARGET_HORIZON_SOURCE_FIELD_DERIVATION_CONTRACT_2026-05-11.json"
    },
    {
      "actual_sha256": "ec39fa0c96020a146d6634dccefca87de9d8629f745168184d7c36b893e9a800",
      "exists": true,
      "expected_sha256": "ec39fa0c96020a146d6634dccefca87de9d8629f745168184d7c36b893e9a800",
      "input_name": "g0_completion_audit",
      "matched": true,
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_neutral_target_control_synthesis/G0_SCID_NEUTRAL_TARGET_SYNTHESIS_COMPLETION_AUDIT_2026-05-12.json"
    },
    {
      "actual_sha256": "6f36c9eccf80c90854e8a6eb0eabfbd7c8e265a9eae872cb201f67b3926af347",
      "exists": true,
      "expected_sha256": "6f36c9eccf80c90854e8a6eb0eabfbd7c8e265a9eae872cb201f67b3926af347",
      "input_name": "g0_route_ranking",
      "matched": true,
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_neutral_target_control_synthesis/G0_SCID_NEUTRAL_TARGET_SYNTHESIS_ROUTE_RANKING_LEDGER_2026-05-12.json"
    },
    {
      "actual_sha256": "245a4a74d70ca8920cebf7fa2a3924c377d5e87f9acec8101bfd0e79d3b6e71c",
      "exists": true,
      "expected_sha256": "245a4a74d70ca8920cebf7fa2a3924c377d5e87f9acec8101bfd0e79d3b6e71c",
      "input_name": "g0_future_source_fields",
      "matched": true,
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_neutral_target_control_synthesis/G0_SCID_NEUTRAL_TARGET_SYNTHESIS_FUTURE_SOURCE_FIELD_REQUIREMENT_LEDGER_2026-05-12.json"
    },
    {
      "actual_sha256": "8fe1a7260f551f5bcecafe5eabe83b38d7bc58ef449fd360ff58795befdee9ce",
      "exists": true,
      "expected_sha256": "8fe1a7260f551f5bcecafe5eabe83b38d7bc58ef449fd360ff58795befdee9ce",
      "input_name": "g0_evidence_reconciliation",
      "matched": true,
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_neutral_target_control_synthesis/G0_SCID_NEUTRAL_TARGET_SYNTHESIS_ACCEPTED_EVIDENCE_RECONCILIATION_2026-05-12.json"
    },
    {
      "actual_sha256": "f2fac27c4901ee533fb02e863f39d8f4fb7ee6fcf947d04e49ba1e641cf7da3d",
      "exists": true,
      "expected_sha256": "f2fac27c4901ee533fb02e863f39d8f4fb7ee6fcf947d04e49ba1e641cf7da3d",
      "input_name": "g0_anti_boxing",
      "matched": true,
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_neutral_target_control_synthesis/G0_SCID_NEUTRAL_TARGET_SYNTHESIS_ANTI_BOXING_MECHANISM_REVIEW_2026-05-12.json"
    },
    {
      "actual_sha256": "759c908197ec50fea9590bf3ca996a078eba034b1294918a3a9f2d8d7ccb0c3c",
      "exists": true,
      "expected_sha256": "759c908197ec50fea9590bf3ca996a078eba034b1294918a3a9f2d8d7ccb0c3c",
      "input_name": "g0_saturation",
      "matched": true,
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_neutral_target_control_synthesis/G0_SCID_NEUTRAL_TARGET_SYNTHESIS_SATURATION_SELF_REDTEAM_PASS_2026-05-12.json"
    },
    {
      "actual_sha256": "51de883059cb9c1db7d90cb80c5203696387dd36acb361a874b789495b037bf0",
      "exists": true,
      "expected_sha256": "51de883059cb9c1db7d90cb80c5203696387dd36acb361a874b789495b037bf0",
      "input_name": "g12_decision",
      "matched": true,
      "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_asof_quarantined_neutral_target_execution_packet_audit/G12_SCID_ASOF_NEUTRAL_TARGET_PACKET_AUDIT_DECISION_LEDGER_2026-05-12.json"
    },
    {
      "actual_sha256": "247413e456c03a069c4229d3513e7c240eb51e52474f4e7ef4083618b677b9a4",
      "exists": true,
      "expected_sha256": "247413e456c03a069c4229d3513e7c240eb51e52474f4e7ef4083618b677b9a4",
      "input_name": "g12_source_binding",
      "matched": true,
      "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_asof_quarantined_neutral_target_execution_packet_audit/G12_SCID_ASOF_NEUTRAL_TARGET_PACKET_AUDIT_SOURCE_HASH_INPUT_BINDING_AUDIT_2026-05-12.json"
    },
    {
      "actual_sha256": "291dc772f4baba27380a73b70ac7e1433fa6b4e408c1ee9614e2fd39faae1d78",
      "exists": true,
      "expected_sha256": "291dc772f4baba27380a73b70ac7e1433fa6b4e408c1ee9614e2fd39faae1d78",
      "input_name": "target_source_binding",
      "matched": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_asof_quarantined_neutral_target_execution_packet/SCID_ASOF_NEUTRAL_TARGET_SOURCE_HASH_BINDING_2026-05-12.json"
    },
    {
      "actual_sha256": "3c95ef05fe42afb993d93930962cc566c9616df72882cb86912620dbac12b85a",
      "exists": true,
      "expected_sha256": "3c95ef05fe42afb993d93930962cc566c9616df72882cb86912620dbac12b85a",
      "input_name": "target_pre_freeze",
      "matched": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_asof_quarantined_neutral_target_execution_packet/SCID_ASOF_NEUTRAL_TARGET_PRE_TARGET_FREEZE_PACKET_2026-05-12.json"
    },
    {
      "actual_sha256": "777c1a440e79a1871cb00a505a5c71cef4502047610acd991aeb2a06da1d0798",
      "exists": true,
      "expected_sha256": "777c1a440e79a1871cb00a505a5c71cef4502047610acd991aeb2a06da1d0798",
      "input_name": "controlling_prompt",
      "matched": true,
      "path": "research/science_program_2026_05/04_goal_prompts/SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_GOAL_PROMPT_2026-05-12.md"
    },
    {
      "actual_sha256": "67209b0f64b8990417bb51d8d2b17937d5604ed15fa449d39fa106ad849f1911",
      "exists": true,
      "expected_sha256": "67209b0f64b8990417bb51d8d2b17937d5604ed15fa449d39fa106ad849f1911",
      "input_name": "descriptor_freeze",
      "matched": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_asof_quarantined_neutral_target_execution_packet/SCID_ASOF_NEUTRAL_TARGET_DESCRIPTOR_FREEZE_LEDGER_2026-05-12.json"
    },
    {
      "actual_sha256": "a692db4032a945f588d2cb4232600262e4f7eaa2f39a0725f13f5a5e3cab5eb2",
      "exists": true,
      "expected_sha256": "a692db4032a945f588d2cb4232600262e4f7eaa2f39a0725f13f5a5e3cab5eb2",
      "input_name": "candidate_rows",
      "matched": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/SCID_ASOF_CANDIDATE_INPUT_ROWS_2026-05-11.jsonl"
    },
    {
      "actual_sha256": "35587e78cbddc922e87ef450bf5ceb91b86245805daf2be48ff62e0c98452222",
      "exists": true,
      "expected_sha256": "35587e78cbddc922e87ef450bf5ceb91b86245805daf2be48ff62e0c98452222",
      "input_name": "candidate_manifest",
      "matched": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/SCID_ASOF_CANDIDATE_INPUT_PACKET_MANIFEST_2026-05-11.json"
    },
    {
      "actual_sha256": "51cc87822caab49da466bd4b89f2c35650b8d89e01cf9450f955f2a1f4beb6dd",
      "exists": true,
      "expected_sha256": "51cc87822caab49da466bd4b89f2c35650b8d89e01cf9450f955f2a1f4beb6dd",
      "input_name": "source_field_inventory",
      "matched": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_asof_sealed_validation_target_horizon_repair/SCID_ASOF_TARGET_HORIZON_SOURCE_FIELD_INVENTORY_2026-05-11.json"
    },
    {
      "actual_sha256": "beb8537af1f0d76d39a9fe3799931f75ce3ca8ccf52e4b9d530c522403fe9f0a",
      "exists": true,
      "expected_sha256": "beb8537af1f0d76d39a9fe3799931f75ce3ca8ccf52e4b9d530c522403fe9f0a",
      "input_name": "source_field_derivation_contract",
      "matched": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_asof_sealed_validation_target_horizon_repair/SCID_ASOF_TARGET_HORIZON_SOURCE_FIELD_DERIVATION_CONTRACT_2026-05-11.json"
    },
    {
      "actual_sha256": "ec39fa0c96020a146d6634dccefca87de9d8629f745168184d7c36b893e9a800",
      "exists": true,
      "expected_sha256": "ec39fa0c96020a146d6634dccefca87de9d8629f745168184d7c36b893e9a800",
      "input_name": "g0_completion_audit",
      "matched": true,
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_neutral_target_control_synthesis/G0_SCID_NEUTRAL_TARGET_SYNTHESIS_COMPLETION_AUDIT_2026-05-12.json"
    },
    {
      "actual_sha256": "6f36c9eccf80c90854e8a6eb0eabfbd7c8e265a9eae872cb201f67b3926af347",
      "exists": true,
      "expected_sha256": "6f36c9eccf80c90854e8a6eb0eabfbd7c8e265a9eae872cb201f67b3926af347",
      "input_name": "g0_route_ranking",
      "matched": true,
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_neutral_target_control_synthesis/G0_SCID_NEUTRAL_TARGET_SYNTHESIS_ROUTE_RANKING_LEDGER_2026-05-12.json"
    },
    {
      "actual_sha256": "245a4a74d70ca8920cebf7fa2a3924c377d5e87f9acec8101bfd0e79d3b6e71c",
      "exists": true,
      "expected_sha256": "245a4a74d70ca8920cebf7fa2a3924c377d5e87f9acec8101bfd0e79d3b6e71c",
      "input_name": "g0_future_source_fields",
      "matched": true,
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_neutral_target_control_synthesis/G0_SCID_NEUTRAL_TARGET_SYNTHESIS_FUTURE_SOURCE_FIELD_REQUIREMENT_LEDGER_2026-05-12.json"
    },
    {
      "actual_sha256": "8fe1a7260f551f5bcecafe5eabe83b38d7bc58ef449fd360ff58795befdee9ce",
      "exists": true,
      "expected_sha256": "8fe1a7260f551f5bcecafe5eabe83b38d7bc58ef449fd360ff58795befdee9ce",
      "input_name": "g0_evidence_reconciliation",
      "matched": true,
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_neutral_target_control_synthesis/G0_SCID_NEUTRAL_TARGET_SYNTHESIS_ACCEPTED_EVIDENCE_RECONCILIATION_2026-05-12.json"
    },
    {
      "actual_sha256": "f2fac27c4901ee533fb02e863f39d8f4fb7ee6fcf947d04e49ba1e641cf7da3d",
      "exists": true,
      "expected_sha256": "f2fac27c4901ee533fb02e863f39d8f4fb7ee6fcf947d04e49ba1e641cf7da3d",
      "input_name": "g0_anti_boxing",
      "matched": true,
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_neutral_target_control_synthesis/G0_SCID_NEUTRAL_TARGET_SYNTHESIS_ANTI_BOXING_MECHANISM_REVIEW_2026-05-12.json"
    },
    {
      "actual_sha256": "759c908197ec50fea9590bf3ca996a078eba034b1294918a3a9f2d8d7ccb0c3c",
      "exists": true,
      "expected_sha256": "759c908197ec50fea9590bf3ca996a078eba034b1294918a3a9f2d8d7ccb0c3c",
      "input_name": "g0_saturation",
      "matched": true,
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_neutral_target_control_synthesis/G0_SCID_NEUTRAL_TARGET_SYNTHESIS_SATURATION_SELF_REDTEAM_PASS_2026-05-12.json"
    },
    {
      "actual_sha256": "51de883059cb9c1db7d90cb80c5203696387dd36acb361a874b789495b037bf0",
      "exists": true,
      "expected_sha256": "51de883059cb9c1db7d90cb80c5203696387dd36acb361a874b789495b037bf0",
      "input_name": "g12_decision",
      "matched": true,
      "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_asof_quarantined_neutral_target_execution_packet_audit/G12_SCID_ASOF_NEUTRAL_TARGET_PACKET_AUDIT_DECISION_LEDGER_2026-05-12.json"
    },
    {
      "actual_sha256": "247413e456c03a069c4229d3513e7c240eb51e52474f4e7ef4083618b677b9a4",
      "exists": true,
      "expected_sha256": "247413e456c03a069c4229d3513e7c240eb51e52474f4e7ef4083618b677b9a4",
      "input_name": "g12_source_binding",
      "matched": true,
      "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_asof_quarantined_neutral_target_execution_packet_audit/G12_SCID_ASOF_NEUTRAL_TARGET_PACKET_AUDIT_SOURCE_HASH_INPUT_BINDING_AUDIT_2026-05-12.json"
    },
    {
      "actual_sha256": "291dc772f4baba27380a73b70ac7e1433fa6b4e408c1ee9614e2fd39faae1d78",
      "exists": true,
      "expected_sha256": "291dc772f4baba27380a73b70ac7e1433fa6b4e408c1ee9614e2fd39faae1d78",
      "input_name": "target_source_binding",
      "matched": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_asof_quarantined_neutral_target_execution_packet/SCID_ASOF_NEUTRAL_TARGET_SOURCE_HASH_BINDING_2026-05-12.json"
    },
    {
      "actual_sha256": "3c95ef05fe42afb993d93930962cc566c9616df72882cb86912620dbac12b85a",
      "exists": true,
      "expected_sha256": "3c95ef05fe42afb993d93930962cc566c9616df72882cb86912620dbac12b85a",
      "input_name": "target_pre_freeze",
      "matched": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_asof_quarantined_neutral_target_execution_packet/SCID_ASOF_NEUTRAL_TARGET_PRE_TARGET_FREEZE_PACKET_2026-05-12.json"
    }
  ],
  "validation_safe": false
}
```
