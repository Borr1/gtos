# Provenance Allowlist

- **route_id:** `SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET`
- **evidence_class:** `SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "allowed_field_sources": {
    "candidate_identity": [
      "candidate_input_row_id",
      "duplicate_key",
      "duplicate_proxy_denominator_key"
    ],
    "neutral_side_marker_only": [
      "duplicate_key_fields.side=SIDE_NEUTRAL_SOURCE_CONTROL_INPUT"
    ],
    "source_coverage": [
      "source_coverage_quality_bucket",
      "prior_windows",
      "not-computable descriptor buckets"
    ],
    "source_descriptors": [
      "symbol",
      "source_file_name",
      "source_proxy_group",
      "session_bucket",
      "time_of_day_bucket",
      "partition_assignment"
    ]
  },
  "allowed_input_artifacts": [
    {
      "name": "controlling_prompt",
      "path": "research/science_program_2026_05/04_goal_prompts/SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_GOAL_PROMPT_2026-05-12.md",
      "sha256": "777c1a440e79a1871cb00a505a5c71cef4502047610acd991aeb2a06da1d0798"
    },
    {
      "name": "descriptor_freeze",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_asof_quarantined_neutral_target_execution_packet/SCID_ASOF_NEUTRAL_TARGET_DESCRIPTOR_FREEZE_LEDGER_2026-05-12.json",
      "sha256": "67209b0f64b8990417bb51d8d2b17937d5604ed15fa449d39fa106ad849f1911"
    },
    {
      "name": "candidate_rows",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/SCID_ASOF_CANDIDATE_INPUT_ROWS_2026-05-11.jsonl",
      "sha256": "a692db4032a945f588d2cb4232600262e4f7eaa2f39a0725f13f5a5e3cab5eb2"
    },
    {
      "name": "candidate_manifest",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/SCID_ASOF_CANDIDATE_INPUT_PACKET_MANIFEST_2026-05-11.json",
      "sha256": "35587e78cbddc922e87ef450bf5ceb91b86245805daf2be48ff62e0c98452222"
    },
    {
      "name": "source_field_inventory",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_asof_sealed_validation_target_horizon_repair/SCID_ASOF_TARGET_HORIZON_SOURCE_FIELD_INVENTORY_2026-05-11.json",
      "sha256": "51cc87822caab49da466bd4b89f2c35650b8d89e01cf9450f955f2a1f4beb6dd"
    },
    {
      "name": "source_field_derivation_contract",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_asof_sealed_validation_target_horizon_repair/SCID_ASOF_TARGET_HORIZON_SOURCE_FIELD_DERIVATION_CONTRACT_2026-05-11.json",
      "sha256": "beb8537af1f0d76d39a9fe3799931f75ce3ca8ccf52e4b9d530c522403fe9f0a"
    },
    {
      "name": "g0_completion_audit",
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_neutral_target_control_synthesis/G0_SCID_NEUTRAL_TARGET_SYNTHESIS_COMPLETION_AUDIT_2026-05-12.json",
      "sha256": "ec39fa0c96020a146d6634dccefca87de9d8629f745168184d7c36b893e9a800"
    },
    {
      "name": "g0_route_ranking",
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_neutral_target_control_synthesis/G0_SCID_NEUTRAL_TARGET_SYNTHESIS_ROUTE_RANKING_LEDGER_2026-05-12.json",
      "sha256": "6f36c9eccf80c90854e8a6eb0eabfbd7c8e265a9eae872cb201f67b3926af347"
    },
    {
      "name": "g0_future_source_fields",
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_neutral_target_control_synthesis/G0_SCID_NEUTRAL_TARGET_SYNTHESIS_FUTURE_SOURCE_FIELD_REQUIREMENT_LEDGER_2026-05-12.json",
      "sha256": "245a4a74d70ca8920cebf7fa2a3924c377d5e87f9acec8101bfd0e79d3b6e71c"
    },
    {
      "name": "g0_evidence_reconciliation",
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_neutral_target_control_synthesis/G0_SCID_NEUTRAL_TARGET_SYNTHESIS_ACCEPTED_EVIDENCE_RECONCILIATION_2026-05-12.json",
      "sha256": "8fe1a7260f551f5bcecafe5eabe83b38d7bc58ef449fd360ff58795befdee9ce"
    },
    {
      "name": "g0_anti_boxing",
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_neutral_target_control_synthesis/G0_SCID_NEUTRAL_TARGET_SYNTHESIS_ANTI_BOXING_MECHANISM_REVIEW_2026-05-12.json",
      "sha256": "f2fac27c4901ee533fb02e863f39d8f4fb7ee6fcf947d04e49ba1e641cf7da3d"
    },
    {
      "name": "g0_saturation",
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_neutral_target_control_synthesis/G0_SCID_NEUTRAL_TARGET_SYNTHESIS_SATURATION_SELF_REDTEAM_PASS_2026-05-12.json",
      "sha256": "759c908197ec50fea9590bf3ca996a078eba034b1294918a3a9f2d8d7ccb0c3c"
    },
    {
      "name": "g12_decision",
      "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_asof_quarantined_neutral_target_execution_packet_audit/G12_SCID_ASOF_NEUTRAL_TARGET_PACKET_AUDIT_DECISION_LEDGER_2026-05-12.json",
      "sha256": "51de883059cb9c1db7d90cb80c5203696387dd36acb361a874b789495b037bf0"
    },
    {
      "name": "g12_source_binding",
      "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_asof_quarantined_neutral_target_execution_packet_audit/G12_SCID_ASOF_NEUTRAL_TARGET_PACKET_AUDIT_SOURCE_HASH_INPUT_BINDING_AUDIT_2026-05-12.json",
      "sha256": "247413e456c03a069c4229d3513e7c240eb51e52474f4e7ef4083618b677b9a4"
    },
    {
      "name": "target_source_binding",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_asof_quarantined_neutral_target_execution_packet/SCID_ASOF_NEUTRAL_TARGET_SOURCE_HASH_BINDING_2026-05-12.json",
      "sha256": "291dc772f4baba27380a73b70ac7e1433fa6b4e408c1ee9614e2fd39faae1d78"
    },
    {
      "name": "target_pre_freeze",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_asof_quarantined_neutral_target_execution_packet/SCID_ASOF_NEUTRAL_TARGET_PRE_TARGET_FREEZE_PACKET_2026-05-12.json",
      "sha256": "3c95ef05fe42afb993d93930962cc566c9616df72882cb86912620dbac12b85a"
    }
  ],
  "artifact_family": "field_provenance_and_no_leak_allowlist",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_ONLY",
  "forbidden_input_families": [
    "broker account/order/history/deal/position evidence",
    "target/result/performance fields",
    "AI/API outputs",
    "paid/vendor calls",
    "raw market-data blob commits",
    "live trading prompt/config/risk/safety/execution/canary/selector changes"
  ],
  "forbidden_result_keys_checked_by_verifier": [
    "actual_r",
    "broker_actual_r",
    "close_to_close_absolute_delta",
    "close_to_close_percent_return",
    "downside_excursion_absolute",
    "downside_excursion_percent",
    "expectancy",
    "horizon_close",
    "max_high_over_horizon",
    "mean_r",
    "median_r",
    "min_low_over_horizon",
    "pnl",
    "profit_factor",
    "r_multiple",
    "slippage",
    "target_row_hash",
    "upside_excursion_absolute",
    "upside_excursion_percent",
    "win_rate"
  ],
  "generated_at_utc": "2026-05-11T23:23:39Z",
  "live_effect": false,
  "no_leak_rule": "Closure rows may record field availability and source requirements only; they must not contain target values, result labels, R/PnL, win-rate, expectancy, or performance fields.",
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
  "route_id": "SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET",
  "schema_version": "scid_strategy_field_source_expansion_packet_v1",
  "validation_safe": false
}
```
