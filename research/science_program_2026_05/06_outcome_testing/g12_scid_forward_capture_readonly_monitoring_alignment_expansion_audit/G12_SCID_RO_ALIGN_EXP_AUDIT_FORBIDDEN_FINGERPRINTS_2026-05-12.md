# Forbidden Key And Shape Fingerprint Audit

- route_id: `G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT`
- evidence_class: `G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT_ONLY`
- terminal_decision: `n/a`
- status: `PASS`

```json
{
  "artifact_family": "forbidden_key_and_shape_fingerprint_audit",
  "blocking_content_hash_mismatch_count": 0,
  "blocking_content_hash_mismatch_sample": [],
  "content_hash_missing_path_count": 0,
  "content_hash_missing_paths_sample": [],
  "content_hashes_recomputed_from_disk": 2434,
  "content_hashes_recorded_count_reported": 2434,
  "evidence_class": "G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT_ONLY",
  "external_hash_drift_policy": "Absolute prior-worktree hash drift is recorded as nonblocking scoped evidence because it does not alter the target route, accepted offline-schema package, forbidden surfaces, or current G12 audit artifacts. Any current-worktree/input-route/upstream hash mismatch remains blocking.",
  "failures": [],
  "forbidden_examples_bad_disposition_count": 0,
  "forbidden_file_exclusion_count": 11,
  "forbidden_key_category_counts": {
    "broker_account_order_deal_position": 5032,
    "credential_or_api": 1916,
    "post_outcome_or_validation": 11697,
    "result_performance_outcome": 8772
  },
  "generated_at_utc": "2026-05-12T07:34:32Z",
  "live_effect": false,
  "matched_group_artifact_counts": {
    "baseline_control_fields": 1399,
    "framework_setup_family": 351,
    "future_orderflow_depth_proxy_requirements": 1867,
    "intended_entry_reference": 612,
    "intended_side_direction": 685,
    "intended_stop_reference": 458,
    "intended_target_reference": 709,
    "lifecycle_fill_cancel_expiry_source_status": 513,
    "lower_timeframe_asof_path_availability": 489,
    "poi_type_bounds_source": 1824
  },
  "nonblocking_external_content_hash_mismatch_count": 17,
  "nonblocking_external_content_hash_mismatch_sample": [
    {
      "expected": "66965e44af6d6d0c338b10ef1ca26d25d4e3186534f8fe42ac12b0a9c45b7233",
      "observed": "079feec64499888b81adff42f01fda6fecd8b7e573af0f69c76779e7d3e5a441",
      "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_ACCEPTED_AUDIT_RECONCILIATION_2026-05-12.json"
    },
    {
      "expected": "c45c499057c0dbeab7e43b2d86458f6cb21cd5ab6a533054cd2a53c02c20ad8e",
      "observed": "d71e2e050e27519fc6ad962b9f34421547354b8126cf65c0c77006f471f526d5",
      "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_ADVERSARIAL_BASELINE_PLACEBO_MATRIX_2026-05-12.json"
    },
    {
      "expected": "62250facf4f3f576791fd98dc973a82f0e58e10f1470293b7021811194a995a4",
      "observed": "a1f6d893194330fa8c37c123b2675a1618a80e5b9844fb83911e6ec2db1e00d7",
      "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_CLOSEOUT_VERIFICATION_2026-05-12.json"
    },
    {
      "expected": "96129d69b27ac309968a044c337bb4818f628e4f719673206891d4c3b5596214",
      "observed": "21fa1f64d132e06fbe95d03fa5346061211bbcaf4e72398f2f2cc646f62a54cd",
      "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_COMPLETION_AUDIT_2026-05-12.json"
    },
    {
      "expected": "47451538946338cd2c5225f10ea537103e120ce905b9f9e54b55cdccc5cce5dc",
      "observed": "75b9f9913895f35aa999d523224c5f586406431305c87577eb0ecf9679366f94",
      "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_CONTEXT_ANCHOR_2026-05-12.json"
    },
    {
      "expected": "8535a46e59ee79ddb6dfb6a038c3450c4f8f581aee9d0ce6681dbc2ef14b6593",
      "observed": "277b8b1f9451e28f9ba4b605d4688f267d3cc25fdabbcea570966610f3c8ae12",
      "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_DECISION_LEDGER_2026-05-12.json"
    },
    {
      "expected": "8216d5d329ea9236fc360b075948c8581cf770442aa4d9c027951ab58c0b4e82",
      "observed": "c5b06332aaf0a30d816a9a5193371367c3ca3dd8cf1b09ed23cb79b36d54a07a",
      "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_FUTURE_NO_API_REPLAY_ROUTE_BUNDLE_2026-05-12.json"
    },
    {
      "expected": "18f061fb73eeb29fd6f6f30b1d1301a2a610ccc7f1bc801eedff7fe46090796b",
      "observed": "5c831c0c1c7c74091e3f43b2e488fc7db2d5eafb7d6913e56a261aa8820364fd",
      "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_G12_G0_AUDIT_PROMPT_PACK_2026-05-12.json"
    },
    {
      "expected": "7d16e744ed72bd9a2990b282c9cf528690223e1ab879bf639e09f803d4188cea",
      "observed": "5b1ff0aab8f212abf0bed612afd304cb3aa6f24e72f95b65d659f0fb60cc2f05",
      "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_GENERIC_IDEA_LIST_SATURATION_PROOF_2026-05-12.json"
    },
    {
      "expected": "160d8fb21a496fc19cedc55774c8bc65f346d440e79f26e6cc264822474e80ca",
      "observed": "558e13eeade80be33febf10d78c69fa80dde12bf02c78a1bf5cb156b183d5046",
      "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_HYPOTHESIS_CARD_LEDGER_SUMMARY_2026-05-12.json"
    },
    {
      "expected": "73b1931f2ea87d5c5a2e0054cc34d419b175d67dccf476bd67bc9cd20946fc67",
      "observed": "569704c1e42baf9bbc8a6316c7172d752410917416c3720818f6df1277799b79",
      "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_MECHANISM_FAMILY_HYPOTHESIS_CATALOG_2026-05-12.json"
    },
    {
      "expected": "3ce17268d44ebd1d3c6153dd1f30a0e02f899c2499f3310f0be00167b4abf2aa",
      "observed": "0dae7f8c1e822c8421874ee6648b251d1f4d85c09579cba5792accfa6b08a2f0",
      "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_OUTPUT_MANIFEST_2026-05-12.json"
    },
    {
      "expected": "3ba7c6fd42e5683abe0ad48428aab363225885674977d4461b2e98b9a0abe5ee",
      "observed": "f202f290ade38eb6169908cb169db85fa8c763ab45e5bd93a707df4aeba26a8d",
      "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_PREREGISTRATION_READINESS_MATRIX_2026-05-12.json"
    },
    {
      "expected": "6eb9c6e0c753c221bff26c5387faeeb6609afab4747a48c4572dd1c4ed698159",
      "observed": "71e70ef20b1f2f46b27b21db59d5a939babb8150ee4a58ded12282ec88a01281",
      "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_SCIENCE_DOMAIN_COVERAGE_MATRIX_2026-05-12.json"
    },
    {
      "expected": "48a7243857b3e29328989809cb0974874cda8e0daf2be2a7ea7c635bef8f1163",
      "observed": "47bcd2dedaa03ce83691cc289d5751a3e9398b7e1431748a1b0a1e4b0a2b35f6",
      "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_SOURCE_FIELD_CHECKLIST_2026-05-12.json"
    },
    {
      "expected": "1c99a219778c82bf0a307e5c1efad3ccc2478c8d5d5ab783787c7853ce9622c3",
      "observed": "ddea945e5e4d7b90c2b1c5f8213cb41482e98446fbdd3654151935f3496c3f24",
      "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_VERIFICATION_RESULT_2026-05-12.json"
    },
    {
      "expected": "eb04e5a668a94e1d3359b51b9317cd45d2995f1ba4a46751f505ed6861239d45",
      "observed": "96ffdf17a798564b4cd18a21898375b631494b77724ad3c33d4a45912a3acdd5",
      "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/verify_scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis_2026_05_12.py"
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
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "raw_blob_rows": [],
  "raw_values_copied": false,
  "route_id": "G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT",
  "shape_fingerprint_count": 2551,
  "shape_inventory_artifact_count": 2551,
  "shape_only_policy": "Forbidden key shapes were recorded only as key names/categories and excluded from source/control coverage; no raw values were copied.",
  "status": "PASS",
  "validation_safe": false
}
```
