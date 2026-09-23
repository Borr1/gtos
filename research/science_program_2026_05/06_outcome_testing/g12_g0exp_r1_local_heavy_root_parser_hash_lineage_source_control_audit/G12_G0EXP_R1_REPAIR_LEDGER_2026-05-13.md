# G12 G0EXP R1 Repair Ledger

- **route_id:** `G12_G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_AUDIT`
- **evidence_class:** `G12_G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_AUDIT_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

- Terminal repair status: `CLOSED`.
- Remaining source/access/export/capture requirements: `0`.

```json
{
  "artifact_family": "repair_ledger",
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "closed_repair_rows": [
    {
      "evidence_source": "e25a57e7:research/science_program_2026_05/06_outcome_testing/g0exp_r1_local_heavy_root_parser_hash_lineage_source_control/G0EXP_R1_OUTPUT_MANIFEST_2026-05-13.json",
      "lineage": [
        "75c5b249 research: harden scid next wave g12 prompts",
        "e25a57e7 research: integrate scid next wave route artifacts"
      ],
      "new_sha256": "6827ab5f40b7aef98cca1e91e334cac2c0122f8c0c6e5391846d5943ffe87d7c",
      "new_size_bytes": 4057,
      "old_sha256": "8360a3e7795f6cbbecf6573a020e47a5c857cd1d52808bb730c65747e12bbadb",
      "old_size_bytes": 2809,
      "path": "research/science_program_2026_05/04_goal_prompts/G12_G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_AUDIT_GOAL_PROMPT_2026-05-13.md",
      "reason": "Original R1 packet manifest predates later G12 prompt hardening; current manifest is repaired.",
      "repair_id": "R1_OUTPUT_MANIFEST_G12_PROMPT_HASH",
      "status": "CLOSED_BY_CURRENT_HASH_RECOMPUTATION"
    }
  ],
  "credentials_touched": false,
  "evidence_class": "G12_G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_AUDIT_ONLY",
  "generated_at_utc": "2026-05-13T04:47:59Z",
  "historical_original_packet_prompt_mismatch": {
    "actual_sha256": "6827ab5f40b7aef98cca1e91e334cac2c0122f8c0c6e5391846d5943ffe87d7c",
    "actual_size_bytes": 4057,
    "evidence_source": "e25a57e7:research/science_program_2026_05/06_outcome_testing/g0exp_r1_local_heavy_root_parser_hash_lineage_source_control/G0EXP_R1_OUTPUT_MANIFEST_2026-05-13.json",
    "expected_sha256": "8360a3e7795f6cbbecf6573a020e47a5c857cd1d52808bb730c65747e12bbadb",
    "expected_size_bytes": 2809,
    "mismatch_type": "historical_packet_hash_or_size_mismatch",
    "path": "research/science_program_2026_05/04_goal_prompts/G12_G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_AUDIT_GOAL_PROMPT_2026-05-13.md"
  },
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
  "post_lineage_policy_rows_not_terminal_blockers": [
    {
      "actual_sha256": "f6c7d86659e0b2c6086baee3d81887774c1b4e028ac691aa3ca318631a7fcc1b",
      "actual_size_bytes": 31048,
      "expected_sha256": "764355075de4bbdf6bebd7457543263a57485cd6d3d42d99cb008df548c7ee2f",
      "expected_size_bytes": 27420,
      "mismatch_type": "hash_or_size_mismatch",
      "path": "research/science_program_2026_05/06_outcome_testing/g0exp_r1_local_heavy_root_parser_hash_lineage_source_control/G0EXP_R1_ARTIFACT_LINEAGE_MANIFEST_BINDING_PROOF_2026-05-13.json",
      "policy_classification": "SELF_REFERENTIAL_LINEAGE_ROW"
    },
    {
      "actual_sha256": "a11faa5da7a75bd3f90fab2412c09bac0267ed8593452eb5b04d2ae3004ec977",
      "actual_size_bytes": 31436,
      "expected_sha256": "086dcdce2673e0ec8ae2bba328930caaccfb97b784b0c1209f6ed43597e66db4",
      "expected_size_bytes": 27873,
      "mismatch_type": "hash_or_size_mismatch",
      "path": "research/science_program_2026_05/06_outcome_testing/g0exp_r1_local_heavy_root_parser_hash_lineage_source_control/G0EXP_R1_ARTIFACT_LINEAGE_MANIFEST_BINDING_PROOF_2026-05-13.md",
      "policy_classification": "SELF_REFERENTIAL_LINEAGE_ROW"
    },
    {
      "actual_sha256": "7d9f6827926e8f6f8e57981686821bb5f0bca56cb1b932911c657e15e571b631",
      "actual_size_bytes": 8859,
      "expected_sha256": "eb11e181d9d15e567a3ffa01cd7aae37259d84ac06f36d8955192bfc31c912d1",
      "expected_size_bytes": 8571,
      "mismatch_type": "hash_or_size_mismatch",
      "path": "research/science_program_2026_05/06_outcome_testing/g0exp_r1_local_heavy_root_parser_hash_lineage_source_control/G0EXP_R1_COMPLETION_AUDIT_2026-05-13.json",
      "policy_classification": "POST_VERIFIER_MUTABLE_COMPLETION_ROW"
    },
    {
      "actual_sha256": "428a623c447046f51523522750c537749a35bf4c052f62deed7c0c97b06237b3",
      "actual_size_bytes": 9129,
      "expected_sha256": "befa1cb9fbf1d4ef8ea7489f732d888ebf9bb7bdc94d1f915dc6683051778287",
      "expected_size_bytes": 9032,
      "mismatch_type": "hash_or_size_mismatch",
      "path": "research/science_program_2026_05/06_outcome_testing/g0exp_r1_local_heavy_root_parser_hash_lineage_source_control/G0EXP_R1_COMPLETION_AUDIT_2026-05-13.md",
      "policy_classification": "POST_VERIFIER_MUTABLE_COMPLETION_ROW"
    },
    {
      "actual_sha256": "7ddbeaf6830b9018800cde2be4c38f7e0112526b0c76e90dc0dd62fa3e56a65a",
      "actual_size_bytes": 8427,
      "expected_sha256": "d63928270f77400e9b495c6d0a68c0e7d8678bd93fad3618abac23e128bbaa31",
      "expected_size_bytes": 8427,
      "mismatch_type": "hash_or_size_mismatch",
      "path": "research/science_program_2026_05/06_outcome_testing/g0exp_r1_local_heavy_root_parser_hash_lineage_source_control/G0EXP_R1_OUTPUT_MANIFEST_2026-05-13.json",
      "policy_classification": "OUTPUT_MANIFEST_SELF_HASH_POLICY_ROW"
    },
    {
      "actual_sha256": "4b10056fb1895feb72a6c449d24aaf8376fae99c390e3602d5fcf961a3e11b3e",
      "actual_size_bytes": 8715,
      "expected_sha256": "6ffaa7a4a5dba456d9cac5bce1347bb6e29c21ca430f025a93fa153ab08c5613",
      "expected_size_bytes": 8818,
      "mismatch_type": "hash_or_size_mismatch",
      "path": "research/science_program_2026_05/06_outcome_testing/g0exp_r1_local_heavy_root_parser_hash_lineage_source_control/G0EXP_R1_OUTPUT_MANIFEST_2026-05-13.md",
      "policy_classification": "OUTPUT_MANIFEST_SELF_HASH_POLICY_ROW"
    }
  ],
  "post_output_manifest_mismatches": [],
  "pre_lineage_mismatches": [
    {
      "actual_sha256": "f6c7d86659e0b2c6086baee3d81887774c1b4e028ac691aa3ca318631a7fcc1b",
      "actual_size_bytes": 31048,
      "expected_sha256": "764355075de4bbdf6bebd7457543263a57485cd6d3d42d99cb008df548c7ee2f",
      "expected_size_bytes": 27420,
      "mismatch_type": "hash_or_size_mismatch",
      "path": "research/science_program_2026_05/06_outcome_testing/g0exp_r1_local_heavy_root_parser_hash_lineage_source_control/G0EXP_R1_ARTIFACT_LINEAGE_MANIFEST_BINDING_PROOF_2026-05-13.json"
    },
    {
      "actual_sha256": "a11faa5da7a75bd3f90fab2412c09bac0267ed8593452eb5b04d2ae3004ec977",
      "actual_size_bytes": 31436,
      "expected_sha256": "086dcdce2673e0ec8ae2bba328930caaccfb97b784b0c1209f6ed43597e66db4",
      "expected_size_bytes": 27873,
      "mismatch_type": "hash_or_size_mismatch",
      "path": "research/science_program_2026_05/06_outcome_testing/g0exp_r1_local_heavy_root_parser_hash_lineage_source_control/G0EXP_R1_ARTIFACT_LINEAGE_MANIFEST_BINDING_PROOF_2026-05-13.md"
    },
    {
      "actual_sha256": "7d9f6827926e8f6f8e57981686821bb5f0bca56cb1b932911c657e15e571b631",
      "actual_size_bytes": 8859,
      "expected_sha256": "eb11e181d9d15e567a3ffa01cd7aae37259d84ac06f36d8955192bfc31c912d1",
      "expected_size_bytes": 8571,
      "mismatch_type": "hash_or_size_mismatch",
      "path": "research/science_program_2026_05/06_outcome_testing/g0exp_r1_local_heavy_root_parser_hash_lineage_source_control/G0EXP_R1_COMPLETION_AUDIT_2026-05-13.json"
    },
    {
      "actual_sha256": "428a623c447046f51523522750c537749a35bf4c052f62deed7c0c97b06237b3",
      "actual_size_bytes": 9129,
      "expected_sha256": "befa1cb9fbf1d4ef8ea7489f732d888ebf9bb7bdc94d1f915dc6683051778287",
      "expected_size_bytes": 9032,
      "mismatch_type": "hash_or_size_mismatch",
      "path": "research/science_program_2026_05/06_outcome_testing/g0exp_r1_local_heavy_root_parser_hash_lineage_source_control/G0EXP_R1_COMPLETION_AUDIT_2026-05-13.md"
    },
    {
      "actual_sha256": "7ddbeaf6830b9018800cde2be4c38f7e0112526b0c76e90dc0dd62fa3e56a65a",
      "actual_size_bytes": 8427,
      "expected_sha256": "d63928270f77400e9b495c6d0a68c0e7d8678bd93fad3618abac23e128bbaa31",
      "expected_size_bytes": 8427,
      "mismatch_type": "hash_or_size_mismatch",
      "path": "research/science_program_2026_05/06_outcome_testing/g0exp_r1_local_heavy_root_parser_hash_lineage_source_control/G0EXP_R1_OUTPUT_MANIFEST_2026-05-13.json"
    },
    {
      "actual_sha256": "4b10056fb1895feb72a6c449d24aaf8376fae99c390e3602d5fcf961a3e11b3e",
      "actual_size_bytes": 8715,
      "expected_sha256": "6ffaa7a4a5dba456d9cac5bce1347bb6e29c21ca430f025a93fa153ab08c5613",
      "expected_size_bytes": 8818,
      "mismatch_type": "hash_or_size_mismatch",
      "path": "research/science_program_2026_05/06_outcome_testing/g0exp_r1_local_heavy_root_parser_hash_lineage_source_control/G0EXP_R1_OUTPUT_MANIFEST_2026-05-13.md"
    }
  ],
  "pre_output_manifest_mismatches": [],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "remaining_exact_source_access_export_capture_requirements": [],
  "repair_summary": "The only actionable current-output mismatch was the G12 prompt hash drift introduced by later prompt hardening. The R1 output manifest and lineage prompt row were recomputed. Remaining lineage mismatches are self-hash or post-verifier mutable rows covered by the manifest self-hash policy.",
  "route_id": "G12_G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_AUDIT",
  "schema_version": "g12_g0exp_r1_local_heavy_root_parser_hash_lineage_source_control_audit_v1",
  "terminal_repair_status": "CLOSED",
  "validation_safe": false
}
```
