# Recomputation Ledger

```json
{
  "adv_card_id_counts": {
    "ADV-001": {
      "ADV-001": 4288
    },
    "ADV-003": {
      "ADV-003": 12611
    }
  },
  "adv_control_roles": {
    "ADV-001": {
      "session_time_symbol_placebo": 4288
    },
    "ADV-003": {
      "duplicate_hash_bucket_placebo": 12611
    }
  },
  "artifact_family": "recomputation_ledger",
  "audit_current_head": "868f0dcc",
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "concentration_adjusted_interpretation_counts": {
    "CONCENTRATION_ADJUSTMENT_REQUIRED_BEFORE_INTERPRETATION": 19981,
    "UNCONCENTRATED_NEGATIVE_NEUTRAL_MOVEMENT": 163,
    "UNCONCENTRATED_POSITIVE_NEUTRAL_MOVEMENT": 245,
    "UNDERPOWERED_RETAINED_NOT_KILL_OR_PROMOTE": 59357
  },
  "concentration_card_counts": {
    "ADV-001": 4288,
    "ADV-003": 12611,
    "BEH-001": 8432,
    "HAZ-001": 16231,
    "HAZ-005": 23187,
    "MAC-001": 6376,
    "MAC-004": 5533,
    "UNC-004": 3088
  },
  "control_cards_are_not_edge_cards": true,
  "control_envelope_classification_counts": {
    "FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT": 2608,
    "MATERIALLY_WEAKENED_BY_ADV_CONTROL_DRIFT": 14,
    "NOT_NUMERIC_NOT_ADJUSTABLE": 3622,
    "RESIDUAL_PRESERVED_AFTER_ADV_CONTROL_ENVELOPE": 1,
    "UNDERPOWERED_PRESERVED_NOT_DECISION": 4318
  },
  "control_envelope_classification_counts_by_card": {
    "BEH-001": {
      "FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT": 239,
      "MATERIALLY_WEAKENED_BY_ADV_CONTROL_DRIFT": 14,
      "NOT_NUMERIC_NOT_ADJUSTABLE": 476,
      "RESIDUAL_PRESERVED_AFTER_ADV_CONTROL_ENVELOPE": 1,
      "UNDERPOWERED_PRESERVED_NOT_DECISION": 540
    },
    "HAZ-001": {
      "FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT": 219,
      "NOT_NUMERIC_NOT_ADJUSTABLE": 1380,
      "UNDERPOWERED_PRESERVED_NOT_DECISION": 1807
    },
    "HAZ-005": {
      "FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT": 966,
      "NOT_NUMERIC_NOT_ADJUSTABLE": 300,
      "UNDERPOWERED_PRESERVED_NOT_DECISION": 887
    },
    "MAC-001": {
      "FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT": 659,
      "NOT_NUMERIC_NOT_ADJUSTABLE": 438,
      "UNDERPOWERED_PRESERVED_NOT_DECISION": 303
    },
    "MAC-004": {
      "FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT": 131,
      "NOT_NUMERIC_NOT_ADJUSTABLE": 799,
      "UNDERPOWERED_PRESERVED_NOT_DECISION": 700
    },
    "UNC-004": {
      "FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT": 394,
      "NOT_NUMERIC_NOT_ADJUSTABLE": 229,
      "UNDERPOWERED_PRESERVED_NOT_DECISION": 81
    }
  },
  "control_envelope_math_mismatch_count": 0,
  "control_envelope_math_mismatches": [],
  "control_match_missing_rows": 0,
  "downstream_comparison_summary_counts": {
    "FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT": 2608,
    "MATERIALLY_WEAKENED_BY_ADV_CONTROL_DRIFT": 14,
    "NOT_NUMERIC_NOT_ADJUSTABLE": 3622,
    "RESIDUAL_PRESERVED_AFTER_ADV_CONTROL_ENVELOPE": 1,
    "UNDERPOWERED_PRESERVED_NOT_DECISION": 4318,
    "card:BEH-001:FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT": 239,
    "card:BEH-001:MATERIALLY_WEAKENED_BY_ADV_CONTROL_DRIFT": 14,
    "card:BEH-001:NOT_NUMERIC_NOT_ADJUSTABLE": 476,
    "card:BEH-001:RESIDUAL_PRESERVED_AFTER_ADV_CONTROL_ENVELOPE": 1,
    "card:BEH-001:UNDERPOWERED_PRESERVED_NOT_DECISION": 540,
    "card:HAZ-001:FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT": 219,
    "card:HAZ-001:NOT_NUMERIC_NOT_ADJUSTABLE": 1380,
    "card:HAZ-001:UNDERPOWERED_PRESERVED_NOT_DECISION": 1807,
    "card:HAZ-005:FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT": 966,
    "card:HAZ-005:NOT_NUMERIC_NOT_ADJUSTABLE": 300,
    "card:HAZ-005:UNDERPOWERED_PRESERVED_NOT_DECISION": 887,
    "card:MAC-001:FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT": 659,
    "card:MAC-001:NOT_NUMERIC_NOT_ADJUSTABLE": 438,
    "card:MAC-001:UNDERPOWERED_PRESERVED_NOT_DECISION": 303,
    "card:MAC-004:FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT": 131,
    "card:MAC-004:NOT_NUMERIC_NOT_ADJUSTABLE": 799,
    "card:MAC-004:UNDERPOWERED_PRESERVED_NOT_DECISION": 700,
    "card:UNC-004:FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT": 394,
    "card:UNC-004:NOT_NUMERIC_NOT_ADJUSTABLE": 229,
    "card:UNC-004:UNDERPOWERED_PRESERVED_NOT_DECISION": 81
  },
  "downstream_formula": {
    "control_envelope": "max(abs(matched ADV-001 deltas), abs(matched ADV-003 deltas)) at comparison-family/partition/horizon/target scope, falling back only to partition/horizon/target when exact family controls are absent",
    "full_explanation": "abs(raw_delta) <= control_envelope",
    "material_weakening": "control_envelope < abs(raw_delta) <= 2 * control_envelope",
    "raw_delta": "non-ADV target-movement delta from accepted sealed ledger",
    "residual_abs": "max(0, abs(raw_delta) - control_envelope)",
    "residual_preserved": "abs(raw_delta) > 2 * control_envelope and not underpowered"
  },
  "downstream_per_card_summary_counts": {
    "BEH-001": {
      "FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT": 239,
      "MATERIALLY_WEAKENED_BY_ADV_CONTROL_DRIFT": 14,
      "NOT_NUMERIC_NOT_ADJUSTABLE": 476,
      "RESIDUAL_PRESERVED_AFTER_ADV_CONTROL_ENVELOPE": 1,
      "UNDERPOWERED_PRESERVED_NOT_DECISION": 540
    },
    "HAZ-001": {
      "FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT": 219,
      "NOT_NUMERIC_NOT_ADJUSTABLE": 1380,
      "UNDERPOWERED_PRESERVED_NOT_DECISION": 1807
    },
    "HAZ-005": {
      "FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT": 966,
      "NOT_NUMERIC_NOT_ADJUSTABLE": 300,
      "UNDERPOWERED_PRESERVED_NOT_DECISION": 887
    },
    "MAC-001": {
      "FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT": 659,
      "NOT_NUMERIC_NOT_ADJUSTABLE": 438,
      "UNDERPOWERED_PRESERVED_NOT_DECISION": 303
    },
    "MAC-004": {
      "FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT": 131,
      "NOT_NUMERIC_NOT_ADJUSTABLE": 799,
      "UNDERPOWERED_PRESERVED_NOT_DECISION": 700
    },
    "UNC-004": {
      "FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT": 394,
      "NOT_NUMERIC_NOT_ADJUSTABLE": 229,
      "UNDERPOWERED_PRESERVED_NOT_DECISION": 81
    }
  },
  "duplicate_interpretation_counts": {
    "duplicate-hash placebo drift; no mechanism or edge-card claim": 256,
    "effective-N denominator record; row multiplicity is not independent evidence": 3014
  },
  "duplicate_record_type_counts": {
    "adv003_hash_bucket_branch": 256,
    "duplicate_effective_n_group": 3014
  },
  "evidence_class": "G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT_REVIEW_ONLY",
  "explained_weakened_extra_keys": [],
  "explained_weakened_key_set_matches_mapping": true,
  "explained_weakened_missing_keys": [],
  "generated_at_utc": "2026-05-15T11:29:32Z",
  "live_effect": false,
  "no_arbitrary_top_n_proof": {
    "adv001_rows_preserved": 4288,
    "adv003_rows_preserved": 12611,
    "baseline_drift_rows_preserved": 3546,
    "comparison_mapping_rows_preserved": 10563,
    "concentration_rows_preserved": 79746,
    "duplicate_artifact_rows_preserved": 3270,
    "stress_vs_sealed_rows_preserved": 45913,
    "underpower_rows_preserved": 79746
  },
  "nonadv_cards_observed": [
    "BEH-001",
    "HAZ-001",
    "HAZ-005",
    "MAC-001",
    "MAC-004",
    "UNC-004"
  ],
  "nonadv_comparison_rows_preserved": 10563,
  "nonadv_expected_cards": [
    "BEH-001",
    "HAZ-001",
    "HAZ-005",
    "MAC-001",
    "MAC-004",
    "UNC-004"
  ],
  "opens_ai_api": false,
  "opens_broker_account_order_history_deal_position_evidence": false,
  "opens_live_trading_behavior": false,
  "opens_paid_or_vendor_access": false,
  "opens_prompt_config_risk_safety_execution_canary_selector_edit": false,
  "opens_raw_market_data_blob_commit": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "residual_extra_keys": [],
  "residual_key_set_matches_mapping": true,
  "residual_missing_keys": [],
  "route_id": "G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT",
  "row_count_recomputation": {
    "adv001_placebo": 4288,
    "adv003_placebo": 12611,
    "baseline_drift": 3546,
    "comparison_mapping": 10563,
    "concentration": 79746,
    "control_design": 1,
    "downstream_rules": 1,
    "duplicate_artifact": 3270,
    "explained_weakened": 2622,
    "residual": 1,
    "stress_vs_sealed": 45913,
    "target_completion": 1,
    "target_focused_test": 1,
    "target_manifest": 1,
    "target_repair": 1,
    "target_saturation": 1,
    "target_verification": 1,
    "underpower": 79746
  },
  "stress_vs_sealed_classification_counts": {
    "PARTITION_PAIR_MISSING": 12080,
    "STRESS_REPLICATES_SEALED_DIRECTION": 4692,
    "STRESS_SEALED_DIRECTION_DIVERGENCE": 1568,
    "UNDERPOWERED_PARTITION_PAIR_RETAINED": 27573
  },
  "target_completion_can_mark_goal_complete": true,
  "target_file_scan_summary": {
    "adv001_placebo": {
      "parse_errors": [],
      "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_ADV001_PLACEBO_DRIFT_LEDGER_2026-05-15.jsonl",
      "rows": 4288,
      "safe_flag_failures": 0,
      "target_evidence_class_mismatches": 0,
      "target_route_id_mismatches": 0
    },
    "adv003_placebo": {
      "parse_errors": [],
      "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_ADV003_DUPLICATE_PLACEBO_DRIFT_LEDGER_2026-05-15.jsonl",
      "rows": 12611,
      "safe_flag_failures": 0,
      "target_evidence_class_mismatches": 0,
      "target_route_id_mismatches": 0
    },
    "baseline_drift": {
      "parse_errors": [],
      "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_BASELINE_DRIFT_BY_AXIS_LEDGER_2026-05-15.jsonl",
      "rows": 3546,
      "safe_flag_failures": 0,
      "target_evidence_class_mismatches": 0,
      "target_route_id_mismatches": 0
    },
    "comparison_mapping": {
      "parse_errors": [],
      "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_NONADV_COMPARISON_CONTROL_DRIFT_MAPPING_LEDGER_2026-05-15.jsonl",
      "rows": 10563,
      "safe_flag_failures": 0,
      "target_evidence_class_mismatches": 0,
      "target_route_id_mismatches": 0
    },
    "concentration": {
      "parse_errors": [],
      "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_CONCENTRATION_ADJUSTED_INTERPRETATION_LEDGER_2026-05-15.jsonl",
      "rows": 79746,
      "safe_flag_failures": 0,
      "target_evidence_class_mismatches": 0,
      "target_route_id_mismatches": 0
    },
    "control_design": {
      "parse_errors": [],
      "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_ADV001_ADV003_CONTROL_DESIGN_AUDIT_LEDGER_2026-05-15.json",
      "rows": 1,
      "safe_flag_failures": 0,
      "target_evidence_class_mismatches": 0,
      "target_route_id_mismatches": 0
    },
    "downstream_rules": {
      "parse_errors": [],
      "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_DOWNSTREAM_ADJUSTMENT_RULES_2026-05-15.json",
      "rows": 1,
      "safe_flag_failures": 0,
      "target_evidence_class_mismatches": 0,
      "target_route_id_mismatches": 0
    },
    "duplicate_artifact": {
      "parse_errors": [],
      "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_DUPLICATE_BUCKET_ARTIFACT_LEDGER_2026-05-15.jsonl",
      "rows": 3270,
      "safe_flag_failures": 0,
      "target_evidence_class_mismatches": 0,
      "target_route_id_mismatches": 0
    },
    "explained_weakened": {
      "parse_errors": [],
      "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_CONTROLS_FULLY_EXPLAIN_OR_WEAKEN_FINDINGS_LEDGER_2026-05-15.jsonl",
      "rows": 2622,
      "safe_flag_failures": 0,
      "target_evidence_class_mismatches": 0,
      "target_route_id_mismatches": 0
    },
    "prompt": {
      "parse_errors": [],
      "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT_PROMPT_2026-05-15.md",
      "rows": null
    },
    "residual": {
      "parse_errors": [],
      "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_NEGATIVE_CONTROLS_FAIL_TO_EXPLAIN_RESIDUAL_LEDGER_2026-05-15.jsonl",
      "rows": 1,
      "safe_flag_failures": 0,
      "target_evidence_class_mismatches": 0,
      "target_route_id_mismatches": 0
    },
    "starter": {
      "parse_errors": [],
      "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT_STARTER_2026-05-15.txt",
      "rows": null
    },
    "stress_vs_sealed": {
      "parse_errors": [],
      "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_STRESS_VS_SEALED_CONTROL_DRIFT_LEDGER_2026-05-15.jsonl",
      "rows": 45913,
      "safe_flag_failures": 0,
      "target_evidence_class_mismatches": 0,
      "target_route_id_mismatches": 0
    },
    "target_completion": {
      "parse_errors": [],
      "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_ADV_CONTROL_COMPLETION_AUDIT_2026-05-15.json",
      "rows": 1,
      "safe_flag_failures": 0,
      "target_evidence_class_mismatches": 0,
      "target_route_id_mismatches": 0
    },
    "target_focused_test": {
      "parse_errors": [],
      "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_ADV_CONTROL_FOCUSED_TEST_RESULT_2026-05-15.json",
      "rows": 1,
      "safe_flag_failures": 0,
      "target_evidence_class_mismatches": 0,
      "target_route_id_mismatches": 0
    },
    "target_manifest": {
      "parse_errors": [],
      "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_ADV_CONTROL_OUTPUT_MANIFEST_2026-05-15.json",
      "rows": 1,
      "safe_flag_failures": 0,
      "target_evidence_class_mismatches": 0,
      "target_route_id_mismatches": 0
    },
    "target_repair": {
      "parse_errors": [],
      "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_ADV_CONTROL_BLOCKER_REPAIR_LEDGER_2026-05-15.json",
      "rows": 1,
      "safe_flag_failures": 0,
      "target_evidence_class_mismatches": 0,
      "target_route_id_mismatches": 0
    },
    "target_saturation": {
      "parse_errors": [],
      "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_ADV_CONTROL_SATURATION_SELF_RED_TEAM_LEDGER_2026-05-15.json",
      "rows": 1,
      "safe_flag_failures": 0,
      "target_evidence_class_mismatches": 0,
      "target_route_id_mismatches": 0
    },
    "target_synthesis": {
      "parse_errors": [],
      "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_ADV_CONTROL_SYNTHESIS_2026-05-15.md",
      "rows": null
    },
    "target_verification": {
      "parse_errors": [],
      "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_ADV_CONTROL_VERIFICATION_RESULT_2026-05-15.json",
      "rows": 1,
      "safe_flag_failures": 0,
      "target_evidence_class_mismatches": 0,
      "target_route_id_mismatches": 0
    },
    "underpower": {
      "parse_errors": [],
      "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_BRANCH_UNDERPOWER_EFFECTIVE_N_LEDGER_2026-05-15.jsonl",
      "rows": 79746,
      "safe_flag_failures": 0,
      "target_evidence_class_mismatches": 0,
      "target_route_id_mismatches": 0
    }
  },
  "target_manifest_hash_audit": {
    "mismatch_count": 0,
    "mismatches": [],
    "rows": [
      {
        "actual_sha256": "f00970ccd21555f21c8a279804d456b3ffca2cdced086fff3fdfc7807b1eba08",
        "artifact_key": "adjustment_rules",
        "exists": true,
        "expected_sha256": "f00970ccd21555f21c8a279804d456b3ffca2cdced086fff3fdfc7807b1eba08",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_DOWNSTREAM_ADJUSTMENT_RULES_2026-05-15.json"
      },
      {
        "actual_sha256": "ec0db7b3b48dc7d2a877d6001b1b627b6d735cf41e86bf29f850b68c4b5ad8b2",
        "artifact_key": "adv001_placebo",
        "exists": true,
        "expected_sha256": "ec0db7b3b48dc7d2a877d6001b1b627b6d735cf41e86bf29f850b68c4b5ad8b2",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_ADV001_PLACEBO_DRIFT_LEDGER_2026-05-15.jsonl"
      },
      {
        "actual_sha256": "a9f23ef9c4aedca378ad95931cf48464284e05634c8f605b8e81e849263216a4",
        "artifact_key": "adv003_placebo",
        "exists": true,
        "expected_sha256": "a9f23ef9c4aedca378ad95931cf48464284e05634c8f605b8e81e849263216a4",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_ADV003_DUPLICATE_PLACEBO_DRIFT_LEDGER_2026-05-15.jsonl"
      },
      {
        "actual_sha256": "17e109f59bb02d75ce502d47a6edd26f923fdc0939700b7aa0bc2929587930b4",
        "artifact_key": "baseline_drift",
        "exists": true,
        "expected_sha256": "17e109f59bb02d75ce502d47a6edd26f923fdc0939700b7aa0bc2929587930b4",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_BASELINE_DRIFT_BY_AXIS_LEDGER_2026-05-15.jsonl"
      },
      {
        "actual_sha256": "edd6de06f21f6e45c30f2e44ac6b370809bfdcc6b941421d2004bd51e3c32461",
        "artifact_key": "blocker_repair",
        "exists": true,
        "expected_sha256": "edd6de06f21f6e45c30f2e44ac6b370809bfdcc6b941421d2004bd51e3c32461",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_ADV_CONTROL_BLOCKER_REPAIR_LEDGER_2026-05-15.json"
      },
      {
        "actual_sha256": "7cd1959d8faa5db62140aaa59a3a564134771f7262aaa4765190639b98640a9c",
        "artifact_key": "comparison_mapping",
        "exists": true,
        "expected_sha256": "7cd1959d8faa5db62140aaa59a3a564134771f7262aaa4765190639b98640a9c",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_NONADV_COMPARISON_CONTROL_DRIFT_MAPPING_LEDGER_2026-05-15.jsonl"
      },
      {
        "actual_sha256": "9c5b2fe7f220016237895055b3606616cfbf8053572ce5b67aeb49d8e864dcb4",
        "artifact_key": "completion_audit",
        "exists": true,
        "expected_sha256": "9c5b2fe7f220016237895055b3606616cfbf8053572ce5b67aeb49d8e864dcb4",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_ADV_CONTROL_COMPLETION_AUDIT_2026-05-15.json"
      },
      {
        "actual_sha256": "7d057fa72b923e79b17d6f458e016ab836dd85cdc7c65325d4d4eeddce862c6d",
        "artifact_key": "concentration_adjusted",
        "exists": true,
        "expected_sha256": "7d057fa72b923e79b17d6f458e016ab836dd85cdc7c65325d4d4eeddce862c6d",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_CONCENTRATION_ADJUSTED_INTERPRETATION_LEDGER_2026-05-15.jsonl"
      },
      {
        "actual_sha256": "fbb810d95e39fdfc3eab5313540e0b97567ca848254ce262a6dd3771eb75370c",
        "artifact_key": "context_anchor",
        "exists": true,
        "expected_sha256": "fbb810d95e39fdfc3eab5313540e0b97567ca848254ce262a6dd3771eb75370c",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_ADV_CONTROL_CONTEXT_ANCHOR_INPUT_BINDING_2026-05-15.json"
      },
      {
        "actual_sha256": "9894943572cc9818aa4358710f72857b318aff2745653e248feeb3d1c682a936",
        "artifact_key": "control_design",
        "exists": true,
        "expected_sha256": "9894943572cc9818aa4358710f72857b318aff2745653e248feeb3d1c682a936",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_ADV001_ADV003_CONTROL_DESIGN_AUDIT_LEDGER_2026-05-15.json"
      },
      {
        "actual_sha256": "64618483777c5267b4fe09c1b8d58511ab637ddc0fe8b12e0fcb2348abd11256",
        "artifact_key": "duplicate_artifact",
        "exists": true,
        "expected_sha256": "64618483777c5267b4fe09c1b8d58511ab637ddc0fe8b12e0fcb2348abd11256",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_DUPLICATE_BUCKET_ARTIFACT_LEDGER_2026-05-15.jsonl"
      },
      {
        "actual_sha256": "d256bc9986473ca9f361c9de50ef2c443dc7e685f763b8944183d8f592810e56",
        "artifact_key": "explained_weakened",
        "exists": true,
        "expected_sha256": "d256bc9986473ca9f361c9de50ef2c443dc7e685f763b8944183d8f592810e56",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_CONTROLS_FULLY_EXPLAIN_OR_WEAKEN_FINDINGS_LEDGER_2026-05-15.jsonl"
      },
      {
        "actual_sha256": "6fcc1a66e630173aef0502b58b6e90ab0191705f9fc2a5445f17b8d6ba0c284d",
        "artifact_key": "focused_test",
        "exists": true,
        "expected_sha256": "6fcc1a66e630173aef0502b58b6e90ab0191705f9fc2a5445f17b8d6ba0c284d",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_ADV_CONTROL_FOCUSED_TEST_RESULT_2026-05-15.json"
      },
      {
        "actual_sha256": "0f66ed30a7d59876e0b093d37fbda8a57e91064ee2296d51b078e3f8113b770a",
        "artifact_key": "g12_prompt",
        "exists": true,
        "expected_sha256": "0f66ed30a7d59876e0b093d37fbda8a57e91064ee2296d51b078e3f8113b770a",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT_PROMPT_2026-05-15.md"
      },
      {
        "actual_sha256": "65c58c9f078ee633e495f08d42c756ffb404e21848275d3507a5d88c3ba6edc8",
        "artifact_key": "g12_starter",
        "exists": true,
        "expected_sha256": "65c58c9f078ee633e495f08d42c756ffb404e21848275d3507a5d88c3ba6edc8",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT_STARTER_2026-05-15.txt"
      },
      {
        "actual_sha256": "7c82871faee18a4a8731fff97f91b4ce4e6b3cda1a1451ebb36b363e7fb91ffa",
        "artifact_key": "negative_controls",
        "exists": true,
        "expected_sha256": "7c82871faee18a4a8731fff97f91b4ce4e6b3cda1a1451ebb36b363e7fb91ffa",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_NEGATIVE_CONTROLS_FAIL_TO_EXPLAIN_RESIDUAL_LEDGER_2026-05-15.jsonl"
      },
      {
        "actual_sha256": "6f1a786bad7c7507c642ffb913dd49bd0d71f418ba3276532a9bde50436a87d9",
        "artifact_key": "saturation",
        "exists": true,
        "expected_sha256": "6f1a786bad7c7507c642ffb913dd49bd0d71f418ba3276532a9bde50436a87d9",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_ADV_CONTROL_SATURATION_SELF_RED_TEAM_LEDGER_2026-05-15.json"
      },
      {
        "actual_sha256": "8206ad0a3c1cfb861e67cc349819ece032488d14579e0d891b31f1da3b6c2602",
        "artifact_key": "stress_vs_sealed",
        "exists": true,
        "expected_sha256": "8206ad0a3c1cfb861e67cc349819ece032488d14579e0d891b31f1da3b6c2602",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_STRESS_VS_SEALED_CONTROL_DRIFT_LEDGER_2026-05-15.jsonl"
      },
      {
        "actual_sha256": "d65b5d5973fba487c184621693b79e0fc8cd00f66a2ce5c46cd263c7a76fcae9",
        "artifact_key": "synthesis",
        "exists": true,
        "expected_sha256": "d65b5d5973fba487c184621693b79e0fc8cd00f66a2ce5c46cd263c7a76fcae9",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_ADV_CONTROL_SYNTHESIS_2026-05-15.md"
      },
      {
        "actual_sha256": "27b375c364bd476b617eec719d4d115e28fac6e90371c8f060a96ed9f3264619",
        "artifact_key": "underpower",
        "exists": true,
        "expected_sha256": "27b375c364bd476b617eec719d4d115e28fac6e90371c8f060a96ed9f3264619",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_BRANCH_UNDERPOWER_EFFECTIVE_N_LEDGER_2026-05-15.jsonl"
      },
      {
        "actual_sha256": "a6e1ae560e225d6f0bd03ec1f1da24cd5bc4d5063fb1cb3341538bd40385ef8e",
        "artifact_key": "verification",
        "exists": true,
        "expected_sha256": "a6e1ae560e225d6f0bd03ec1f1da24cd5bc4d5063fb1cb3341538bd40385ef8e",
        "ok": true,
        "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/READY8_ADV_CONTROL_VERIFICATION_RESULT_2026-05-15.json"
      }
    ]
  },
  "target_repair_same_class_blockers_remaining": 0,
  "target_route_dir": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit",
  "target_same_evidence_class_blockers_remaining": 0,
  "target_verifier_can_mark_goal_complete": true,
  "target_verifier_issues": [],
  "target_verifier_ok": true,
  "underpower_card_counts": {
    "ADV-001": 4288,
    "ADV-003": 12611,
    "BEH-001": 8432,
    "HAZ-001": 16231,
    "HAZ-005": 23187,
    "MAC-001": 6376,
    "MAC-004": 5533,
    "UNC-004": 3088
  },
  "underpower_flag_counts": {
    "False": 20389,
    "True": 59357
  },
  "validation_safe": false
}
```
