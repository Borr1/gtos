# Field Group Coverage And Gap Matrix

- **route_id:** `SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION`
- **evidence_class:** `SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "all_ten_capture_groups_represented": true,
  "artifact_family": "field_group_coverage_gap_matrix",
  "capture_group_count": 10,
  "changes_live_trading_behavior": false,
  "coverage_rows": [
    {
      "as_of_rule": "side must be emitted at or before decision_asof_utc and before any target/path/result horizon is opened",
      "coverage_status": "SHAPE_COVERAGE_PRESENT_EXACT_CAPTURE_FIELDS_PRESENT_IN_INSPECTED_SHAPES",
      "exact_capture_requirement_to_close_gap": "Add/verify future additive capture rows for strategy_side_enum_LONG_SHORT_NEUTRAL_NO_STRATEGY, side_source_component, side_source_rule_or_model_hash, side_emission_reason_code via source_safe_strategy_decision_packet_logger; enforce source_id/source_hash/as_of/redaction/forbidden-key fail-closed checks before G12 acceptance.",
      "exact_schema_field_matches_found_by_name": [
        "side_emission_reason_code",
        "side_source_component",
        "side_source_rule_or_model_hash",
        "strategy_side_enum_LONG_SHORT_NEUTRAL_NO_STRATEGY"
      ],
      "existing_shape_artifact_count": 685,
      "field_group": "intended_side_direction",
      "future_source_or_logger": "source_safe_strategy_decision_packet_logger",
      "historical_status": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
      "label": "side",
      "missing_exact_schema_fields": [],
      "no_leak_rule": "do not derive side from post-decision price movement, terminal target status, broker result, or future path labels",
      "representative_shape_artifacts": [
        {
          "matched_key_count": 46,
          "matched_key_examples": [
            "_add_direction_mismatch",
            "_d1_bias_context",
            "_direction_context",
            "_normalize_direction",
            "ai_direction",
            "ai_direction_evaluated",
            "ai_direction_mismatch_side",
            "bearish",
            "bias",
            "bullish",
            "d1_bias",
            "d1_bias_lag"
          ],
          "path": "src/research_infra/decision_layer_diagnostics_join.py",
          "root_label": "research_infra_keyword_shapes",
          "safe_shape_fingerprint_sha256": "059c940a2ded1cb3ab2adec4bcd9129a2f3e846460f48e91034145f58290412c"
        },
        {
          "matched_key_count": 37,
          "matched_key_examples": [
            "ai_direction",
            "candidate_features_context.ai_direction_evaluated",
            "candidate_features_context.daily_bias_confidence",
            "candidate_features_context.daily_bias_direction",
            "candidate_features_context.mso.d1_structure_direction",
            "candidate_features_context.mso.h1_structure_direction",
            "candidate_features_context.mso.m15_structure_direction",
            "d1_bias_lag_context",
            "d1_bias_lag_context.d1_bias",
            "d1_bias_lag_context.h1_direction",
            "d1_bias_lag_context.h4_bias",
            "d1_bias_lag_context.h4_missing"
          ],
          "path": "shadow_logs/decision_layer_diagnostics_join.jsonl",
          "root_label": "shadow_logs_shape_only_non_forbidden_families",
          "safe_shape_fingerprint_sha256": "f837b1d374f915620580de2982b0b470503984edbc703170e294fd151070cef4"
        },
        {
          "matched_key_count": 26,
          "matched_key_examples": [
            "ai_direction",
            "ai_direction_evaluated",
            "bearish",
            "bullish",
            "c1_h1_bias_ranging",
            "daily_bias",
            "daily_bias_confidence",
            "daily_bias_direction",
            "direction",
            "h1_opp_ob_touch_long",
            "h1_opp_ob_touch_short",
            "long"
          ],
          "path": "tests/test_candidate_features_logger_adr005.py",
          "root_label": "focused_tests_keyword_shapes",
          "safe_shape_fingerprint_sha256": "c9c5965b456f4a1657e0903aad4cc8043087120682e9489a07cd358d71ccb161"
        },
        {
          "matched_key_count": 25,
          "matched_key_examples": [
            "_j46_side",
            "_side_multiplier",
            "build_s79_side_aware_context_rows",
            "direction",
            "effective_risk_pct_if_side_aware_applied",
            "long",
            "long_multiplier",
            "long_win_count",
            "s79_side_aware_context_action_required",
            "s79_side_aware_context_documented",
            "s79_side_aware_context_status",
            "s79_side_aware_risk_context"
          ],
          "path": "src/research_infra/s79_side_aware_risk_context.py",
          "root_label": "research_infra_keyword_shapes",
          "safe_shape_fingerprint_sha256": "9a3e3ef7a16a91b29e9c3ece4c93dd7290c9a73bea4bd0fbaeef4f1851c06fe4"
        },
        {
          "matched_key_count": 23,
          "matched_key_examples": [
            "bear",
            "bearish",
            "bull",
            "bullish",
            "direction",
            "directional",
            "inside",
            "key_side",
            "long",
            "long_n",
            "resolve_side",
            "short"
          ],
          "path": "src/research_infra/stratification.py",
          "root_label": "research_infra_keyword_shapes",
          "safe_shape_fingerprint_sha256": "d5220c4adb8e07bfa771c59be5bcd733681308161ab639ee30157cbff74eb1a7"
        },
        {
          "matched_key_count": 21,
          "matched_key_examples": [
            "_normalized_side",
            "bearish",
            "bias",
            "bullish",
            "c1_h1_bias_present",
            "c3_direction_matches",
            "decision_c1_h1_bias_present",
            "decision_c3_direction_matches",
            "direction",
            "long",
            "outside",
            "risk_side_aware_enabled"
          ],
          "path": "src/research_infra/k55_ml_shadow.py",
          "root_label": "research_infra_keyword_shapes",
          "safe_shape_fingerprint_sha256": "021fb61c07dcdd9986ff0e17785cedda667ea54682638549f8adf6e706427c74"
        },
        {
          "matched_key_count": 19,
          "matched_key_examples": [
            "field_group_contracts.intended_side_direction",
            "field_group_contracts.intended_side_direction.as_of_rule",
            "field_group_contracts.intended_side_direction.fields",
            "field_group_contracts.intended_side_direction.fields[]",
            "field_group_contracts.intended_side_direction.fields[].as_of_semantics",
            "field_group_contracts.intended_side_direction.fields[].downstream_g12_acceptance_rule",
            "field_group_contracts.intended_side_direction.fields[].enum",
            "field_group_contracts.intended_side_direction.fields[].enum[]",
            "field_group_contracts.intended_side_direction.fields[].fail_closed_missing_status",
            "field_group_contracts.intended_side_direction.fields[].forbidden_value_policy",
            "field_group_contracts.intended_side_direction.fields[].name",
            "field_group_contracts.intended_side_direction.fields[].nullable"
          ],
          "path": "C:/Users/MSI/Documents/ai-trading-agent/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT_2026-05-12.json",
          "root_label": "original_local_repo_scid_route_artifact_shapes::ai-trading-agent",
          "safe_shape_fingerprint_sha256": "82201d61e896d2af7552d2451ce0e7f557de9c3b24a6fb1b5a08c4109ca10cc5"
        },
        {
          "matched_key_count": 19,
          "matched_key_examples": [
            "field_group_contracts.intended_side_direction",
            "field_group_contracts.intended_side_direction.as_of_rule",
            "field_group_contracts.intended_side_direction.fields",
            "field_group_contracts.intended_side_direction.fields[]",
            "field_group_contracts.intended_side_direction.fields[].as_of_semantics",
            "field_group_contracts.intended_side_direction.fields[].downstream_g12_acceptance_rule",
            "field_group_contracts.intended_side_direction.fields[].enum",
            "field_group_contracts.intended_side_direction.fields[].enum[]",
            "field_group_contracts.intended_side_direction.fields[].fail_closed_missing_status",
            "field_group_contracts.intended_side_direction.fields[].forbidden_value_policy",
            "field_group_contracts.intended_side_direction.fields[].name",
            "field_group_contracts.intended_side_direction.fields[].nullable"
          ],
          "path": "C:/tmp/gtos_otb/SCID_IMPL_DESIGN/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT_2026-05-12.json",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_IMPL_DESIGN",
          "safe_shape_fingerprint_sha256": "82201d61e896d2af7552d2451ce0e7f557de9c3b24a6fb1b5a08c4109ca10cc5"
        },
        {
          "matched_key_count": 19,
          "matched_key_examples": [
            "field_group_contracts.intended_side_direction",
            "field_group_contracts.intended_side_direction.as_of_rule",
            "field_group_contracts.intended_side_direction.fields",
            "field_group_contracts.intended_side_direction.fields[]",
            "field_group_contracts.intended_side_direction.fields[].as_of_semantics",
            "field_group_contracts.intended_side_direction.fields[].downstream_g12_acceptance_rule",
            "field_group_contracts.intended_side_direction.fields[].enum",
            "field_group_contracts.intended_side_direction.fields[].enum[]",
            "field_group_contracts.intended_side_direction.fields[].fail_closed_missing_status",
            "field_group_contracts.intended_side_direction.fields[].forbidden_value_policy",
            "field_group_contracts.intended_side_direction.fields[].name",
            "field_group_contracts.intended_side_direction.fields[].nullable"
          ],
          "path": "C:/tmp/gtos_otb/SCID_LTF_OF_EXPANSION/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT_2026-05-12.json",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_LTF_OF_EXPANSION",
          "safe_shape_fingerprint_sha256": "82201d61e896d2af7552d2451ce0e7f557de9c3b24a6fb1b5a08c4109ca10cc5"
        },
        {
          "matched_key_count": 19,
          "matched_key_examples": [
            "field_group_contracts.intended_side_direction",
            "field_group_contracts.intended_side_direction.as_of_rule",
            "field_group_contracts.intended_side_direction.fields",
            "field_group_contracts.intended_side_direction.fields[]",
            "field_group_contracts.intended_side_direction.fields[].as_of_semantics",
            "field_group_contracts.intended_side_direction.fields[].downstream_g12_acceptance_rule",
            "field_group_contracts.intended_side_direction.fields[].enum",
            "field_group_contracts.intended_side_direction.fields[].enum[]",
            "field_group_contracts.intended_side_direction.fields[].fail_closed_missing_status",
            "field_group_contracts.intended_side_direction.fields[].forbidden_value_policy",
            "field_group_contracts.intended_side_direction.fields[].name",
            "field_group_contracts.intended_side_direction.fields[].nullable"
          ],
          "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT_2026-05-12.json",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_NOAPI_HYP_FACTORY",
          "safe_shape_fingerprint_sha256": "82201d61e896d2af7552d2451ce0e7f557de9c3b24a6fb1b5a08c4109ca10cc5"
        },
        {
          "matched_key_count": 19,
          "matched_key_examples": [
            "field_group_contracts.intended_side_direction",
            "field_group_contracts.intended_side_direction.as_of_rule",
            "field_group_contracts.intended_side_direction.fields",
            "field_group_contracts.intended_side_direction.fields[]",
            "field_group_contracts.intended_side_direction.fields[].as_of_semantics",
            "field_group_contracts.intended_side_direction.fields[].downstream_g12_acceptance_rule",
            "field_group_contracts.intended_side_direction.fields[].enum",
            "field_group_contracts.intended_side_direction.fields[].enum[]",
            "field_group_contracts.intended_side_direction.fields[].fail_closed_missing_status",
            "field_group_contracts.intended_side_direction.fields[].forbidden_value_policy",
            "field_group_contracts.intended_side_direction.fields[].name",
            "field_group_contracts.intended_side_direction.fields[].nullable"
          ],
          "path": "C:/tmp/gtos_otb/SCID_SYNTH_HARNESS/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT_2026-05-12.json",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_SYNTH_HARNESS",
          "safe_shape_fingerprint_sha256": "82201d61e896d2af7552d2451ce0e7f557de9c3b24a6fb1b5a08c4109ca10cc5"
        },
        {
          "matched_key_count": 19,
          "matched_key_examples": [
            "field_group_contracts.intended_side_direction",
            "field_group_contracts.intended_side_direction.as_of_rule",
            "field_group_contracts.intended_side_direction.fields",
            "field_group_contracts.intended_side_direction.fields[]",
            "field_group_contracts.intended_side_direction.fields[].as_of_semantics",
            "field_group_contracts.intended_side_direction.fields[].downstream_g12_acceptance_rule",
            "field_group_contracts.intended_side_direction.fields[].enum",
            "field_group_contracts.intended_side_direction.fields[].enum[]",
            "field_group_contracts.intended_side_direction.fields[].fail_closed_missing_status",
            "field_group_contracts.intended_side_direction.fields[].forbidden_value_policy",
            "field_group_contracts.intended_side_direction.fields[].name",
            "field_group_contracts.intended_side_direction.fields[].nullable"
          ],
          "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT_2026-05-12.json",
          "root_label": "current_scid_source_control_route_artifacts",
          "safe_shape_fingerprint_sha256": "82201d61e896d2af7552d2451ce0e7f557de9c3b24a6fb1b5a08c4109ca10cc5"
        }
      ]
    },
    {
      "as_of_rule": "entry reference must be present before fill, cancel, expiry, or target horizon is known",
      "coverage_status": "SHAPE_COVERAGE_PRESENT_EXACT_CAPTURE_FIELDS_PRESENT_IN_INSPECTED_SHAPES",
      "exact_capture_requirement_to_close_gap": "Add/verify future additive capture rows for entry_reference_type_market_limit_zone_midpoint_other, entry_reference_price, entry_reference_time_utc, entry_source_timeframe, entry_source_bar_hash_or_mso_snapshot_hash via source_safe_strategy_decision_packet_logger; enforce source_id/source_hash/as_of/redaction/forbidden-key fail-closed checks before G12 acceptance.",
      "exact_schema_field_matches_found_by_name": [
        "entry_reference_price",
        "entry_reference_time_utc",
        "entry_reference_type_market_limit_zone_midpoint_other",
        "entry_source_bar_hash_or_mso_snapshot_hash",
        "entry_source_timeframe"
      ],
      "existing_shape_artifact_count": 612,
      "field_group": "intended_entry_reference",
      "future_source_or_logger": "source_safe_strategy_decision_packet_logger",
      "historical_status": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
      "label": "entry",
      "missing_exact_schema_fields": [],
      "no_leak_rule": "no fill-derived or hindsight-optimized entry references",
      "representative_shape_artifacts": [
        {
          "matched_key_count": 42,
          "matched_key_examples": [
            "complete_with_limitations",
            "continued_without_entry_touch_to_tp_area",
            "derived_from_pending_limit_lifecycle_audit",
            "documented_limitation_codes",
            "documented_limitation_counts",
            "entry_",
            "entry_arming_time_utc",
            "entry_first_touch_utc",
            "entry_then_sl",
            "entry_then_tp1",
            "entry_touch_utc",
            "entry_touched_reversal_unresolved_by_asof"
          ],
          "path": "src/research_infra/prefill_delivery_path_audit.py",
          "root_label": "research_infra_keyword_shapes",
          "safe_shape_fingerprint_sha256": "b6cee28f87cb56f34b5c75a933a28211980442d9b611ddc8f3f0b5b822b51881"
        },
        {
          "matched_key_count": 40,
          "matched_key_examples": [
            "entry",
            "entry_first_touch_utc",
            "entry_price",
            "entry_reference_metrics",
            "entry_seen",
            "entry_sl_same_m1_ambiguous",
            "entry_then_sl",
            "entry_then_sl_before_tp1",
            "entry_then_sl_same_m1_ambiguous",
            "entry_then_tp1",
            "entry_then_tp1_before_sl",
            "entry_then_tp1_same_m1_ambiguous"
          ],
          "path": "src/research_infra/live_shadow_gap_closure.py",
          "root_label": "research_infra_keyword_shapes",
          "safe_shape_fingerprint_sha256": "deb04aaa1a9f3d274be10a8e172f9d33c9106420205c4763a48d1e385c52b2c4"
        },
        {
          "matched_key_count": 33,
          "matched_key_examples": [
            "_candidate_limit_geometry",
            "_pending_limit_strategy_status",
            "context_only_no_alternate_entry_model",
            "entry",
            "entry_price",
            "entry_reference_metrics",
            "entry_then_sl",
            "entry_then_sl_same_m1_ambiguous",
            "entry_then_tp1",
            "entry_then_tp1_same_m1_ambiguous",
            "entry_then_tp1_sl_same_m1_ambiguous",
            "entry_touched_then_sl"
          ],
          "path": "src/research_infra/live_mechanical_shadow.py",
          "root_label": "research_infra_keyword_shapes",
          "safe_shape_fingerprint_sha256": "0b2f11cbdcf30b23afb2b17009f4ed8261ce7b59fc06bf3f29538e02bc34d244"
        },
        {
          "matched_key_count": 29,
          "matched_key_examples": [
            "_pending_limit_intent_snapshot",
            "breaker_re_entry",
            "candidate_entry_price",
            "cost_aware_reentry_comparator",
            "entry",
            "entry_arming_time_utc",
            "entry_price",
            "entry_touch_condition_met_source_safe",
            "entry_touch_first",
            "entry_touch_first_utc",
            "entry_touch_not_observed_source_safe",
            "entry_touch_spread"
          ],
          "path": "src/research_infra/forward_capture.py",
          "root_label": "research_infra_keyword_shapes",
          "safe_shape_fingerprint_sha256": "bacdff315bfc5e9429481bd6cf9deac34958633004ed08cdb1e3e937d25a7516"
        },
        {
          "matched_key_count": 29,
          "matched_key_examples": [
            "_limit_candidates",
            "_limit_trade_records",
            "_trade_record_entry",
            "_trade_record_limit_intent",
            "build_pending_limit_lifecycle_audit_row",
            "build_pending_limit_lifecycle_audit_rows",
            "complete_with_limitations",
            "documented_limitation_codes",
            "entry",
            "entry_price",
            "entry_then",
            "limit"
          ],
          "path": "src/research_infra/pending_limit_lifecycle_audit.py",
          "root_label": "research_infra_keyword_shapes",
          "safe_shape_fingerprint_sha256": "dd320ce6150cddaca4018eb525d52aaf6ad15660a37fb70b3834df8dfcc3a273"
        },
        {
          "matched_key_count": 28,
          "matched_key_examples": [
            "_entry_dt",
            "current_entry",
            "entry",
            "entry_delta",
            "entry_dt",
            "entry_first_touch_utc",
            "entry_price",
            "entry_similar",
            "entry_then_sl",
            "entry_then_sl_before_tp1",
            "entry_then_sl_same_m1_ambiguous",
            "entry_then_tp1"
          ],
          "path": "src/research_infra/live_opportunity_dedupe.py",
          "root_label": "research_infra_keyword_shapes",
          "safe_shape_fingerprint_sha256": "9891ea144f0623ad8fb760db2e25ed80bc771b9224a2c5582acddb93ff4a127d"
        },
        {
          "matched_key_count": 21,
          "matched_key_examples": [
            "_distance_from_original_limit",
            "_entry_models",
            "distance_from_original_limit",
            "entry",
            "entry_first_touch_utc",
            "entry_model_id",
            "entry_models",
            "entry_price",
            "entry_source_status",
            "entry_touched_then_sl",
            "entry_touched_then_tp1",
            "entry_touched_unresolved"
          ],
          "path": "src/research_infra/continuation_no_retrace.py",
          "root_label": "research_infra_keyword_shapes",
          "safe_shape_fingerprint_sha256": "1a176ba9f30f6d19b76405d93e417e16de41c8b9a12abcab02db7b1dfe59f350"
        },
        {
          "matched_key_count": 19,
          "matched_key_examples": [
            "field_group_contracts.intended_entry_reference",
            "field_group_contracts.intended_entry_reference.as_of_rule",
            "field_group_contracts.intended_entry_reference.fields",
            "field_group_contracts.intended_entry_reference.fields[]",
            "field_group_contracts.intended_entry_reference.fields[].as_of_semantics",
            "field_group_contracts.intended_entry_reference.fields[].downstream_g12_acceptance_rule",
            "field_group_contracts.intended_entry_reference.fields[].enum",
            "field_group_contracts.intended_entry_reference.fields[].enum[]",
            "field_group_contracts.intended_entry_reference.fields[].fail_closed_missing_status",
            "field_group_contracts.intended_entry_reference.fields[].forbidden_value_policy",
            "field_group_contracts.intended_entry_reference.fields[].name",
            "field_group_contracts.intended_entry_reference.fields[].nullable"
          ],
          "path": "C:/Users/MSI/Documents/ai-trading-agent/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT_2026-05-12.json",
          "root_label": "original_local_repo_scid_route_artifact_shapes::ai-trading-agent",
          "safe_shape_fingerprint_sha256": "82201d61e896d2af7552d2451ce0e7f557de9c3b24a6fb1b5a08c4109ca10cc5"
        },
        {
          "matched_key_count": 19,
          "matched_key_examples": [
            "field_group_contracts.intended_entry_reference",
            "field_group_contracts.intended_entry_reference.as_of_rule",
            "field_group_contracts.intended_entry_reference.fields",
            "field_group_contracts.intended_entry_reference.fields[]",
            "field_group_contracts.intended_entry_reference.fields[].as_of_semantics",
            "field_group_contracts.intended_entry_reference.fields[].downstream_g12_acceptance_rule",
            "field_group_contracts.intended_entry_reference.fields[].enum",
            "field_group_contracts.intended_entry_reference.fields[].enum[]",
            "field_group_contracts.intended_entry_reference.fields[].fail_closed_missing_status",
            "field_group_contracts.intended_entry_reference.fields[].forbidden_value_policy",
            "field_group_contracts.intended_entry_reference.fields[].name",
            "field_group_contracts.intended_entry_reference.fields[].nullable"
          ],
          "path": "C:/tmp/gtos_otb/SCID_IMPL_DESIGN/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT_2026-05-12.json",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_IMPL_DESIGN",
          "safe_shape_fingerprint_sha256": "82201d61e896d2af7552d2451ce0e7f557de9c3b24a6fb1b5a08c4109ca10cc5"
        },
        {
          "matched_key_count": 19,
          "matched_key_examples": [
            "field_group_contracts.intended_entry_reference",
            "field_group_contracts.intended_entry_reference.as_of_rule",
            "field_group_contracts.intended_entry_reference.fields",
            "field_group_contracts.intended_entry_reference.fields[]",
            "field_group_contracts.intended_entry_reference.fields[].as_of_semantics",
            "field_group_contracts.intended_entry_reference.fields[].downstream_g12_acceptance_rule",
            "field_group_contracts.intended_entry_reference.fields[].enum",
            "field_group_contracts.intended_entry_reference.fields[].enum[]",
            "field_group_contracts.intended_entry_reference.fields[].fail_closed_missing_status",
            "field_group_contracts.intended_entry_reference.fields[].forbidden_value_policy",
            "field_group_contracts.intended_entry_reference.fields[].name",
            "field_group_contracts.intended_entry_reference.fields[].nullable"
          ],
          "path": "C:/tmp/gtos_otb/SCID_LTF_OF_EXPANSION/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT_2026-05-12.json",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_LTF_OF_EXPANSION",
          "safe_shape_fingerprint_sha256": "82201d61e896d2af7552d2451ce0e7f557de9c3b24a6fb1b5a08c4109ca10cc5"
        },
        {
          "matched_key_count": 19,
          "matched_key_examples": [
            "field_group_contracts.intended_entry_reference",
            "field_group_contracts.intended_entry_reference.as_of_rule",
            "field_group_contracts.intended_entry_reference.fields",
            "field_group_contracts.intended_entry_reference.fields[]",
            "field_group_contracts.intended_entry_reference.fields[].as_of_semantics",
            "field_group_contracts.intended_entry_reference.fields[].downstream_g12_acceptance_rule",
            "field_group_contracts.intended_entry_reference.fields[].enum",
            "field_group_contracts.intended_entry_reference.fields[].enum[]",
            "field_group_contracts.intended_entry_reference.fields[].fail_closed_missing_status",
            "field_group_contracts.intended_entry_reference.fields[].forbidden_value_policy",
            "field_group_contracts.intended_entry_reference.fields[].name",
            "field_group_contracts.intended_entry_reference.fields[].nullable"
          ],
          "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT_2026-05-12.json",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_NOAPI_HYP_FACTORY",
          "safe_shape_fingerprint_sha256": "82201d61e896d2af7552d2451ce0e7f557de9c3b24a6fb1b5a08c4109ca10cc5"
        },
        {
          "matched_key_count": 19,
          "matched_key_examples": [
            "field_group_contracts.intended_entry_reference",
            "field_group_contracts.intended_entry_reference.as_of_rule",
            "field_group_contracts.intended_entry_reference.fields",
            "field_group_contracts.intended_entry_reference.fields[]",
            "field_group_contracts.intended_entry_reference.fields[].as_of_semantics",
            "field_group_contracts.intended_entry_reference.fields[].downstream_g12_acceptance_rule",
            "field_group_contracts.intended_entry_reference.fields[].enum",
            "field_group_contracts.intended_entry_reference.fields[].enum[]",
            "field_group_contracts.intended_entry_reference.fields[].fail_closed_missing_status",
            "field_group_contracts.intended_entry_reference.fields[].forbidden_value_policy",
            "field_group_contracts.intended_entry_reference.fields[].name",
            "field_group_contracts.intended_entry_reference.fields[].nullable"
          ],
          "path": "C:/tmp/gtos_otb/SCID_SYNTH_HARNESS/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT_2026-05-12.json",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_SYNTH_HARNESS",
          "safe_shape_fingerprint_sha256": "82201d61e896d2af7552d2451ce0e7f557de9c3b24a6fb1b5a08c4109ca10cc5"
        }
      ]
    },
    {
      "as_of_rule": "stop reference must be emitted with the source decision packet and frozen before path/result opening",
      "coverage_status": "SHAPE_COVERAGE_PRESENT_EXACT_CAPTURE_FIELDS_PRESENT_IN_INSPECTED_SHAPES",
      "exact_capture_requirement_to_close_gap": "Add/verify future additive capture rows for stop_reference_price, stop_reference_type, stop_buffer_rule_id, stop_source_structure_id, stop_source_snapshot_hash via source_safe_strategy_decision_packet_logger; enforce source_id/source_hash/as_of/redaction/forbidden-key fail-closed checks before G12 acceptance.",
      "exact_schema_field_matches_found_by_name": [
        "stop_buffer_rule_id",
        "stop_reference_price",
        "stop_reference_type",
        "stop_source_snapshot_hash",
        "stop_source_structure_id"
      ],
      "existing_shape_artifact_count": 458,
      "field_group": "intended_stop_reference",
      "future_source_or_logger": "source_safe_strategy_decision_packet_logger",
      "historical_status": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
      "label": "stop",
      "missing_exact_schema_fields": [],
      "no_leak_rule": "stop cannot be fitted to later adverse excursion, target status, realized R, or broker close state",
      "representative_shape_artifacts": [
        {
          "matched_key_count": 20,
          "matched_key_examples": [
            "diagnostic_join_statuses.sl_beyond_ob",
            "sl_beyond_ob_context",
            "sl_beyond_ob_context.candle_time",
            "sl_beyond_ob_context.direction",
            "sl_beyond_ob_context.framework",
            "sl_beyond_ob_context.h1_atr",
            "sl_beyond_ob_context.join_status",
            "sl_beyond_ob_context.l2_decision",
            "sl_beyond_ob_context.l2_reason",
            "sl_beyond_ob_context.ob_high",
            "sl_beyond_ob_context.ob_low",
            "sl_beyond_ob_context.offset_seconds"
          ],
          "path": "shadow_logs/decision_layer_diagnostics_join.jsonl",
          "root_label": "shadow_logs_shape_only_non_forbidden_families",
          "safe_shape_fingerprint_sha256": "f837b1d374f915620580de2982b0b470503984edbc703170e294fd151070cef4"
        },
        {
          "matched_key_count": 19,
          "matched_key_examples": [
            "field_group_contracts.intended_stop_reference",
            "field_group_contracts.intended_stop_reference.as_of_rule",
            "field_group_contracts.intended_stop_reference.fields",
            "field_group_contracts.intended_stop_reference.fields[]",
            "field_group_contracts.intended_stop_reference.fields[].as_of_semantics",
            "field_group_contracts.intended_stop_reference.fields[].downstream_g12_acceptance_rule",
            "field_group_contracts.intended_stop_reference.fields[].enum",
            "field_group_contracts.intended_stop_reference.fields[].enum[]",
            "field_group_contracts.intended_stop_reference.fields[].fail_closed_missing_status",
            "field_group_contracts.intended_stop_reference.fields[].forbidden_value_policy",
            "field_group_contracts.intended_stop_reference.fields[].name",
            "field_group_contracts.intended_stop_reference.fields[].nullable"
          ],
          "path": "C:/Users/MSI/Documents/ai-trading-agent/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT_2026-05-12.json",
          "root_label": "original_local_repo_scid_route_artifact_shapes::ai-trading-agent",
          "safe_shape_fingerprint_sha256": "82201d61e896d2af7552d2451ce0e7f557de9c3b24a6fb1b5a08c4109ca10cc5"
        },
        {
          "matched_key_count": 19,
          "matched_key_examples": [
            "field_group_contracts.intended_stop_reference",
            "field_group_contracts.intended_stop_reference.as_of_rule",
            "field_group_contracts.intended_stop_reference.fields",
            "field_group_contracts.intended_stop_reference.fields[]",
            "field_group_contracts.intended_stop_reference.fields[].as_of_semantics",
            "field_group_contracts.intended_stop_reference.fields[].downstream_g12_acceptance_rule",
            "field_group_contracts.intended_stop_reference.fields[].enum",
            "field_group_contracts.intended_stop_reference.fields[].enum[]",
            "field_group_contracts.intended_stop_reference.fields[].fail_closed_missing_status",
            "field_group_contracts.intended_stop_reference.fields[].forbidden_value_policy",
            "field_group_contracts.intended_stop_reference.fields[].name",
            "field_group_contracts.intended_stop_reference.fields[].nullable"
          ],
          "path": "C:/tmp/gtos_otb/SCID_IMPL_DESIGN/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT_2026-05-12.json",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_IMPL_DESIGN",
          "safe_shape_fingerprint_sha256": "82201d61e896d2af7552d2451ce0e7f557de9c3b24a6fb1b5a08c4109ca10cc5"
        },
        {
          "matched_key_count": 19,
          "matched_key_examples": [
            "field_group_contracts.intended_stop_reference",
            "field_group_contracts.intended_stop_reference.as_of_rule",
            "field_group_contracts.intended_stop_reference.fields",
            "field_group_contracts.intended_stop_reference.fields[]",
            "field_group_contracts.intended_stop_reference.fields[].as_of_semantics",
            "field_group_contracts.intended_stop_reference.fields[].downstream_g12_acceptance_rule",
            "field_group_contracts.intended_stop_reference.fields[].enum",
            "field_group_contracts.intended_stop_reference.fields[].enum[]",
            "field_group_contracts.intended_stop_reference.fields[].fail_closed_missing_status",
            "field_group_contracts.intended_stop_reference.fields[].forbidden_value_policy",
            "field_group_contracts.intended_stop_reference.fields[].name",
            "field_group_contracts.intended_stop_reference.fields[].nullable"
          ],
          "path": "C:/tmp/gtos_otb/SCID_LTF_OF_EXPANSION/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT_2026-05-12.json",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_LTF_OF_EXPANSION",
          "safe_shape_fingerprint_sha256": "82201d61e896d2af7552d2451ce0e7f557de9c3b24a6fb1b5a08c4109ca10cc5"
        },
        {
          "matched_key_count": 19,
          "matched_key_examples": [
            "field_group_contracts.intended_stop_reference",
            "field_group_contracts.intended_stop_reference.as_of_rule",
            "field_group_contracts.intended_stop_reference.fields",
            "field_group_contracts.intended_stop_reference.fields[]",
            "field_group_contracts.intended_stop_reference.fields[].as_of_semantics",
            "field_group_contracts.intended_stop_reference.fields[].downstream_g12_acceptance_rule",
            "field_group_contracts.intended_stop_reference.fields[].enum",
            "field_group_contracts.intended_stop_reference.fields[].enum[]",
            "field_group_contracts.intended_stop_reference.fields[].fail_closed_missing_status",
            "field_group_contracts.intended_stop_reference.fields[].forbidden_value_policy",
            "field_group_contracts.intended_stop_reference.fields[].name",
            "field_group_contracts.intended_stop_reference.fields[].nullable"
          ],
          "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT_2026-05-12.json",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_NOAPI_HYP_FACTORY",
          "safe_shape_fingerprint_sha256": "82201d61e896d2af7552d2451ce0e7f557de9c3b24a6fb1b5a08c4109ca10cc5"
        },
        {
          "matched_key_count": 19,
          "matched_key_examples": [
            "field_group_contracts.intended_stop_reference",
            "field_group_contracts.intended_stop_reference.as_of_rule",
            "field_group_contracts.intended_stop_reference.fields",
            "field_group_contracts.intended_stop_reference.fields[]",
            "field_group_contracts.intended_stop_reference.fields[].as_of_semantics",
            "field_group_contracts.intended_stop_reference.fields[].downstream_g12_acceptance_rule",
            "field_group_contracts.intended_stop_reference.fields[].enum",
            "field_group_contracts.intended_stop_reference.fields[].enum[]",
            "field_group_contracts.intended_stop_reference.fields[].fail_closed_missing_status",
            "field_group_contracts.intended_stop_reference.fields[].forbidden_value_policy",
            "field_group_contracts.intended_stop_reference.fields[].name",
            "field_group_contracts.intended_stop_reference.fields[].nullable"
          ],
          "path": "C:/tmp/gtos_otb/SCID_SYNTH_HARNESS/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT_2026-05-12.json",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_SYNTH_HARNESS",
          "safe_shape_fingerprint_sha256": "82201d61e896d2af7552d2451ce0e7f557de9c3b24a6fb1b5a08c4109ca10cc5"
        },
        {
          "matched_key_count": 19,
          "matched_key_examples": [
            "field_group_contracts.intended_stop_reference",
            "field_group_contracts.intended_stop_reference.as_of_rule",
            "field_group_contracts.intended_stop_reference.fields",
            "field_group_contracts.intended_stop_reference.fields[]",
            "field_group_contracts.intended_stop_reference.fields[].as_of_semantics",
            "field_group_contracts.intended_stop_reference.fields[].downstream_g12_acceptance_rule",
            "field_group_contracts.intended_stop_reference.fields[].enum",
            "field_group_contracts.intended_stop_reference.fields[].enum[]",
            "field_group_contracts.intended_stop_reference.fields[].fail_closed_missing_status",
            "field_group_contracts.intended_stop_reference.fields[].forbidden_value_policy",
            "field_group_contracts.intended_stop_reference.fields[].name",
            "field_group_contracts.intended_stop_reference.fields[].nullable"
          ],
          "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT_2026-05-12.json",
          "root_label": "current_scid_source_control_route_artifacts",
          "safe_shape_fingerprint_sha256": "82201d61e896d2af7552d2451ce0e7f557de9c3b24a6fb1b5a08c4109ca10cc5"
        },
        {
          "matched_key_count": 15,
          "matched_key_examples": [
            "_jsonl_lock_sleep_seconds",
            "same_bar_tp_sl_ambiguity",
            "sl_before_tp",
            "sl_buffer_applied",
            "sl_hit",
            "sl_time_utc",
            "sleep",
            "slippage_label_closed_not_emitted",
            "slippage_label_status",
            "slippage_present",
            "slippage_price",
            "slippage_value_omitted_not_hashed"
          ],
          "path": "src/research_infra/forward_capture.py",
          "root_label": "research_infra_keyword_shapes",
          "safe_shape_fingerprint_sha256": "bacdff315bfc5e9429481bd6cf9deac34958633004ed08cdb1e3e937d25a7516"
        },
        {
          "matched_key_count": 14,
          "matched_key_examples": [
            "properties.stop_buffer_rule_id",
            "properties.stop_buffer_rule_id.minLength",
            "properties.stop_buffer_rule_id.type",
            "properties.stop_reference_price",
            "properties.stop_reference_price.type",
            "properties.stop_reference_type",
            "properties.stop_reference_type.minLength",
            "properties.stop_reference_type.type",
            "properties.stop_source_snapshot_hash",
            "properties.stop_source_snapshot_hash.minLength",
            "properties.stop_source_snapshot_hash.type",
            "properties.stop_source_structure_id"
          ],
          "path": "C:/Users/MSI/Documents/ai-trading-agent/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/schemas/scid_forward_source_capture_v1_intended_stop_reference.schema.json",
          "root_label": "original_local_repo_scid_route_artifact_shapes::ai-trading-agent",
          "safe_shape_fingerprint_sha256": "fd6a4a51ce68b9307a56ca74ab498783ab9348cb3ed9e5227c8ed6b390a25318"
        },
        {
          "matched_key_count": 14,
          "matched_key_examples": [
            "properties.stop_buffer_rule_id",
            "properties.stop_buffer_rule_id.minLength",
            "properties.stop_buffer_rule_id.type",
            "properties.stop_reference_price",
            "properties.stop_reference_price.type",
            "properties.stop_reference_type",
            "properties.stop_reference_type.minLength",
            "properties.stop_reference_type.type",
            "properties.stop_source_snapshot_hash",
            "properties.stop_source_snapshot_hash.minLength",
            "properties.stop_source_snapshot_hash.type",
            "properties.stop_source_structure_id"
          ],
          "path": "C:/tmp/gtos_otb/SCID_IMPL_DESIGN/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/schemas/scid_forward_source_capture_v1_intended_stop_reference.schema.json",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_IMPL_DESIGN",
          "safe_shape_fingerprint_sha256": "fd6a4a51ce68b9307a56ca74ab498783ab9348cb3ed9e5227c8ed6b390a25318"
        },
        {
          "matched_key_count": 14,
          "matched_key_examples": [
            "properties.stop_buffer_rule_id",
            "properties.stop_buffer_rule_id.minLength",
            "properties.stop_buffer_rule_id.type",
            "properties.stop_reference_price",
            "properties.stop_reference_price.type",
            "properties.stop_reference_type",
            "properties.stop_reference_type.minLength",
            "properties.stop_reference_type.type",
            "properties.stop_source_snapshot_hash",
            "properties.stop_source_snapshot_hash.minLength",
            "properties.stop_source_snapshot_hash.type",
            "properties.stop_source_structure_id"
          ],
          "path": "C:/tmp/gtos_otb/SCID_LTF_OF_EXPANSION/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/schemas/scid_forward_source_capture_v1_intended_stop_reference.schema.json",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_LTF_OF_EXPANSION",
          "safe_shape_fingerprint_sha256": "fd6a4a51ce68b9307a56ca74ab498783ab9348cb3ed9e5227c8ed6b390a25318"
        },
        {
          "matched_key_count": 14,
          "matched_key_examples": [
            "properties.stop_buffer_rule_id",
            "properties.stop_buffer_rule_id.minLength",
            "properties.stop_buffer_rule_id.type",
            "properties.stop_reference_price",
            "properties.stop_reference_price.type",
            "properties.stop_reference_type",
            "properties.stop_reference_type.minLength",
            "properties.stop_reference_type.type",
            "properties.stop_source_snapshot_hash",
            "properties.stop_source_snapshot_hash.minLength",
            "properties.stop_source_snapshot_hash.type",
            "properties.stop_source_structure_id"
          ],
          "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/schemas/scid_forward_source_capture_v1_intended_stop_reference.schema.json",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_NOAPI_HYP_FACTORY",
          "safe_shape_fingerprint_sha256": "fd6a4a51ce68b9307a56ca74ab498783ab9348cb3ed9e5227c8ed6b390a25318"
        }
      ]
    },
    {
      "as_of_rule": "target reference must be frozen at decision time; neutral target horizons are not strategy targets",
      "coverage_status": "SHAPE_COVERAGE_PRESENT_EXACT_CAPTURE_FIELDS_INCOMPLETE",
      "exact_capture_requirement_to_close_gap": "Add/verify future additive capture rows for risk_reward_reference via source_safe_strategy_decision_packet_logger; enforce source_id/source_hash/as_of/redaction/forbidden-key fail-closed checks before G12 acceptance.",
      "exact_schema_field_matches_found_by_name": [
        "target_reference_price",
        "target_reference_type",
        "target_rule_id",
        "target_source_snapshot_hash"
      ],
      "existing_shape_artifact_count": 709,
      "field_group": "intended_target_reference",
      "future_source_or_logger": "source_safe_strategy_decision_packet_logger",
      "historical_status": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
      "label": "target",
      "missing_exact_schema_fields": [
        "risk_reward_reference"
      ],
      "no_leak_rule": "do not create targets from terminal status, later high/low, realized R, or selected performance",
      "representative_shape_artifacts": [
        {
          "matched_key_count": 54,
          "matched_key_examples": [
            "accept_as_g12_source_safe_neutral_target_rulebook_control_evidence_only",
            "accepted_source_safe_neutral_target_rulebook_only",
            "all_target_defs_forbid_strategy_edge_interpretation",
            "all_target_defs_have_source_fields",
            "control_tied_to_neutral_targets",
            "controls_bound_to_neutral_targets",
            "g12_scid_asof_target_horizon_repair_audit",
            "g12_scid_asof_target_horizon_repair_audit_completion_audit_",
            "g12_scid_asof_target_horizon_repair_audit_context_anchor_",
            "g12_scid_asof_target_horizon_repair_audit_count_reconciliation_",
            "g12_scid_asof_target_horizon_repair_audit_decision_ledger_",
            "g12_scid_asof_target_horizon_repair_audit_family_matrix_review_"
          ],
          "path": "C:/Users/MSI/Documents/ai-trading-agent/research/science_program_2026_05/06_outcome_testing/g12_scid_asof_target_horizon_repair_audit/build_g12_scid_asof_target_horizon_repair_audit_2026_05_11.py",
          "root_label": "original_local_repo_scid_route_artifact_shapes::ai-trading-agent",
          "safe_shape_fingerprint_sha256": "f991e1dd6b2ba1c4ebb8e2722d6c8cf320a411b6918a21f4866590f88a76d130"
        },
        {
          "matched_key_count": 54,
          "matched_key_examples": [
            "accept_as_g12_source_safe_neutral_target_rulebook_control_evidence_only",
            "accepted_source_safe_neutral_target_rulebook_only",
            "all_target_defs_forbid_strategy_edge_interpretation",
            "all_target_defs_have_source_fields",
            "control_tied_to_neutral_targets",
            "controls_bound_to_neutral_targets",
            "g12_scid_asof_target_horizon_repair_audit",
            "g12_scid_asof_target_horizon_repair_audit_completion_audit_",
            "g12_scid_asof_target_horizon_repair_audit_context_anchor_",
            "g12_scid_asof_target_horizon_repair_audit_count_reconciliation_",
            "g12_scid_asof_target_horizon_repair_audit_decision_ledger_",
            "g12_scid_asof_target_horizon_repair_audit_family_matrix_review_"
          ],
          "path": "C:/tmp/gtos_otb/SCID_IMPL_DESIGN/research/science_program_2026_05/06_outcome_testing/g12_scid_asof_target_horizon_repair_audit/build_g12_scid_asof_target_horizon_repair_audit_2026_05_11.py",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_IMPL_DESIGN",
          "safe_shape_fingerprint_sha256": "f991e1dd6b2ba1c4ebb8e2722d6c8cf320a411b6918a21f4866590f88a76d130"
        },
        {
          "matched_key_count": 54,
          "matched_key_examples": [
            "accept_as_g12_source_safe_neutral_target_rulebook_control_evidence_only",
            "accepted_source_safe_neutral_target_rulebook_only",
            "all_target_defs_forbid_strategy_edge_interpretation",
            "all_target_defs_have_source_fields",
            "control_tied_to_neutral_targets",
            "controls_bound_to_neutral_targets",
            "g12_scid_asof_target_horizon_repair_audit",
            "g12_scid_asof_target_horizon_repair_audit_completion_audit_",
            "g12_scid_asof_target_horizon_repair_audit_context_anchor_",
            "g12_scid_asof_target_horizon_repair_audit_count_reconciliation_",
            "g12_scid_asof_target_horizon_repair_audit_decision_ledger_",
            "g12_scid_asof_target_horizon_repair_audit_family_matrix_review_"
          ],
          "path": "C:/tmp/gtos_otb/SCID_LTF_OF_EXPANSION/research/science_program_2026_05/06_outcome_testing/g12_scid_asof_target_horizon_repair_audit/build_g12_scid_asof_target_horizon_repair_audit_2026_05_11.py",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_LTF_OF_EXPANSION",
          "safe_shape_fingerprint_sha256": "f991e1dd6b2ba1c4ebb8e2722d6c8cf320a411b6918a21f4866590f88a76d130"
        },
        {
          "matched_key_count": 54,
          "matched_key_examples": [
            "accept_as_g12_source_safe_neutral_target_rulebook_control_evidence_only",
            "accepted_source_safe_neutral_target_rulebook_only",
            "all_target_defs_forbid_strategy_edge_interpretation",
            "all_target_defs_have_source_fields",
            "control_tied_to_neutral_targets",
            "controls_bound_to_neutral_targets",
            "g12_scid_asof_target_horizon_repair_audit",
            "g12_scid_asof_target_horizon_repair_audit_completion_audit_",
            "g12_scid_asof_target_horizon_repair_audit_context_anchor_",
            "g12_scid_asof_target_horizon_repair_audit_count_reconciliation_",
            "g12_scid_asof_target_horizon_repair_audit_decision_ledger_",
            "g12_scid_asof_target_horizon_repair_audit_family_matrix_review_"
          ],
          "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/g12_scid_asof_target_horizon_repair_audit/build_g12_scid_asof_target_horizon_repair_audit_2026_05_11.py",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_NOAPI_HYP_FACTORY",
          "safe_shape_fingerprint_sha256": "f991e1dd6b2ba1c4ebb8e2722d6c8cf320a411b6918a21f4866590f88a76d130"
        },
        {
          "matched_key_count": 54,
          "matched_key_examples": [
            "accept_as_g12_source_safe_neutral_target_rulebook_control_evidence_only",
            "accepted_source_safe_neutral_target_rulebook_only",
            "all_target_defs_forbid_strategy_edge_interpretation",
            "all_target_defs_have_source_fields",
            "control_tied_to_neutral_targets",
            "controls_bound_to_neutral_targets",
            "g12_scid_asof_target_horizon_repair_audit",
            "g12_scid_asof_target_horizon_repair_audit_completion_audit_",
            "g12_scid_asof_target_horizon_repair_audit_context_anchor_",
            "g12_scid_asof_target_horizon_repair_audit_count_reconciliation_",
            "g12_scid_asof_target_horizon_repair_audit_decision_ledger_",
            "g12_scid_asof_target_horizon_repair_audit_family_matrix_review_"
          ],
          "path": "C:/tmp/gtos_otb/SCID_SYNTH_HARNESS/research/science_program_2026_05/06_outcome_testing/g12_scid_asof_target_horizon_repair_audit/build_g12_scid_asof_target_horizon_repair_audit_2026_05_11.py",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_SYNTH_HARNESS",
          "safe_shape_fingerprint_sha256": "f991e1dd6b2ba1c4ebb8e2722d6c8cf320a411b6918a21f4866590f88a76d130"
        },
        {
          "matched_key_count": 54,
          "matched_key_examples": [
            "accept_as_g12_source_safe_neutral_target_rulebook_control_evidence_only",
            "accepted_source_safe_neutral_target_rulebook_only",
            "all_target_defs_forbid_strategy_edge_interpretation",
            "all_target_defs_have_source_fields",
            "control_tied_to_neutral_targets",
            "controls_bound_to_neutral_targets",
            "g12_scid_asof_target_horizon_repair_audit",
            "g12_scid_asof_target_horizon_repair_audit_completion_audit_",
            "g12_scid_asof_target_horizon_repair_audit_context_anchor_",
            "g12_scid_asof_target_horizon_repair_audit_count_reconciliation_",
            "g12_scid_asof_target_horizon_repair_audit_decision_ledger_",
            "g12_scid_asof_target_horizon_repair_audit_family_matrix_review_"
          ],
          "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_asof_target_horizon_repair_audit/build_g12_scid_asof_target_horizon_repair_audit_2026_05_11.py",
          "root_label": "current_scid_source_control_route_artifacts",
          "safe_shape_fingerprint_sha256": "f991e1dd6b2ba1c4ebb8e2722d6c8cf320a411b6918a21f4866590f88a76d130"
        },
        {
          "matched_key_count": 34,
          "matched_key_examples": [
            "accept_as_g0_neutral_target_synthesis_with_ranked_next_route",
            "g0_g12_target_evidence_chain_reconciled",
            "g0_scid_neutral_target_control_synthesis",
            "g0_scid_neutral_target_synthesis_accepted_evidence_reconciliation_2026",
            "g0_scid_neutral_target_synthesis_anti_boxing_mechanism_review_2026",
            "g0_scid_neutral_target_synthesis_completion_audit_2026",
            "g0_scid_neutral_target_synthesis_future_source_field_requirement_ledger_2026",
            "g0_scid_neutral_target_synthesis_route_ranking_ledger_2026",
            "g0_scid_neutral_target_synthesis_saturation_self_redteam_pass_2026",
            "g12_audit_and_target_packet_artifacts_read_from_disk",
            "g12_neutral_target_audit_route",
            "g12_scid_asof_neutral_target_packet_audit_decision_ledger_2026"
          ],
          "path": "C:/Users/MSI/Documents/ai-trading-agent/research/science_program_2026_05/06_outcome_testing/scid_strategy_field_source_expansion_packet/build_scid_strategy_field_source_expansion_packet_2026_05_12.py",
          "root_label": "original_local_repo_scid_route_artifact_shapes::ai-trading-agent",
          "safe_shape_fingerprint_sha256": "fb7268a083575a0ad929a6bc88ea733fa6a86491a202d694986f353f77231712"
        },
        {
          "matched_key_count": 34,
          "matched_key_examples": [
            "accept_as_g0_neutral_target_synthesis_with_ranked_next_route",
            "g0_g12_target_evidence_chain_reconciled",
            "g0_scid_neutral_target_control_synthesis",
            "g0_scid_neutral_target_synthesis_accepted_evidence_reconciliation_2026",
            "g0_scid_neutral_target_synthesis_anti_boxing_mechanism_review_2026",
            "g0_scid_neutral_target_synthesis_completion_audit_2026",
            "g0_scid_neutral_target_synthesis_future_source_field_requirement_ledger_2026",
            "g0_scid_neutral_target_synthesis_route_ranking_ledger_2026",
            "g0_scid_neutral_target_synthesis_saturation_self_redteam_pass_2026",
            "g12_audit_and_target_packet_artifacts_read_from_disk",
            "g12_neutral_target_audit_route",
            "g12_scid_asof_neutral_target_packet_audit_decision_ledger_2026"
          ],
          "path": "C:/tmp/gtos_otb/SCID_IMPL_DESIGN/research/science_program_2026_05/06_outcome_testing/scid_strategy_field_source_expansion_packet/build_scid_strategy_field_source_expansion_packet_2026_05_12.py",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_IMPL_DESIGN",
          "safe_shape_fingerprint_sha256": "fb7268a083575a0ad929a6bc88ea733fa6a86491a202d694986f353f77231712"
        },
        {
          "matched_key_count": 34,
          "matched_key_examples": [
            "accept_as_g0_neutral_target_synthesis_with_ranked_next_route",
            "g0_g12_target_evidence_chain_reconciled",
            "g0_scid_neutral_target_control_synthesis",
            "g0_scid_neutral_target_synthesis_accepted_evidence_reconciliation_2026",
            "g0_scid_neutral_target_synthesis_anti_boxing_mechanism_review_2026",
            "g0_scid_neutral_target_synthesis_completion_audit_2026",
            "g0_scid_neutral_target_synthesis_future_source_field_requirement_ledger_2026",
            "g0_scid_neutral_target_synthesis_route_ranking_ledger_2026",
            "g0_scid_neutral_target_synthesis_saturation_self_redteam_pass_2026",
            "g12_audit_and_target_packet_artifacts_read_from_disk",
            "g12_neutral_target_audit_route",
            "g12_scid_asof_neutral_target_packet_audit_decision_ledger_2026"
          ],
          "path": "C:/tmp/gtos_otb/SCID_LTF_OF_EXPANSION/research/science_program_2026_05/06_outcome_testing/scid_strategy_field_source_expansion_packet/build_scid_strategy_field_source_expansion_packet_2026_05_12.py",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_LTF_OF_EXPANSION",
          "safe_shape_fingerprint_sha256": "fb7268a083575a0ad929a6bc88ea733fa6a86491a202d694986f353f77231712"
        },
        {
          "matched_key_count": 34,
          "matched_key_examples": [
            "accept_as_g0_neutral_target_synthesis_with_ranked_next_route",
            "g0_g12_target_evidence_chain_reconciled",
            "g0_scid_neutral_target_control_synthesis",
            "g0_scid_neutral_target_synthesis_accepted_evidence_reconciliation_2026",
            "g0_scid_neutral_target_synthesis_anti_boxing_mechanism_review_2026",
            "g0_scid_neutral_target_synthesis_completion_audit_2026",
            "g0_scid_neutral_target_synthesis_future_source_field_requirement_ledger_2026",
            "g0_scid_neutral_target_synthesis_route_ranking_ledger_2026",
            "g0_scid_neutral_target_synthesis_saturation_self_redteam_pass_2026",
            "g12_audit_and_target_packet_artifacts_read_from_disk",
            "g12_neutral_target_audit_route",
            "g12_scid_asof_neutral_target_packet_audit_decision_ledger_2026"
          ],
          "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/scid_strategy_field_source_expansion_packet/build_scid_strategy_field_source_expansion_packet_2026_05_12.py",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_NOAPI_HYP_FACTORY",
          "safe_shape_fingerprint_sha256": "fb7268a083575a0ad929a6bc88ea733fa6a86491a202d694986f353f77231712"
        },
        {
          "matched_key_count": 34,
          "matched_key_examples": [
            "accept_as_g0_neutral_target_synthesis_with_ranked_next_route",
            "g0_g12_target_evidence_chain_reconciled",
            "g0_scid_neutral_target_control_synthesis",
            "g0_scid_neutral_target_synthesis_accepted_evidence_reconciliation_2026",
            "g0_scid_neutral_target_synthesis_anti_boxing_mechanism_review_2026",
            "g0_scid_neutral_target_synthesis_completion_audit_2026",
            "g0_scid_neutral_target_synthesis_future_source_field_requirement_ledger_2026",
            "g0_scid_neutral_target_synthesis_route_ranking_ledger_2026",
            "g0_scid_neutral_target_synthesis_saturation_self_redteam_pass_2026",
            "g12_audit_and_target_packet_artifacts_read_from_disk",
            "g12_neutral_target_audit_route",
            "g12_scid_asof_neutral_target_packet_audit_decision_ledger_2026"
          ],
          "path": "C:/tmp/gtos_otb/SCID_SYNTH_HARNESS/research/science_program_2026_05/06_outcome_testing/scid_strategy_field_source_expansion_packet/build_scid_strategy_field_source_expansion_packet_2026_05_12.py",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_SYNTH_HARNESS",
          "safe_shape_fingerprint_sha256": "fb7268a083575a0ad929a6bc88ea733fa6a86491a202d694986f353f77231712"
        },
        {
          "matched_key_count": 34,
          "matched_key_examples": [
            "accept_as_g0_neutral_target_synthesis_with_ranked_next_route",
            "g0_g12_target_evidence_chain_reconciled",
            "g0_scid_neutral_target_control_synthesis",
            "g0_scid_neutral_target_synthesis_accepted_evidence_reconciliation_2026",
            "g0_scid_neutral_target_synthesis_anti_boxing_mechanism_review_2026",
            "g0_scid_neutral_target_synthesis_completion_audit_2026",
            "g0_scid_neutral_target_synthesis_future_source_field_requirement_ledger_2026",
            "g0_scid_neutral_target_synthesis_route_ranking_ledger_2026",
            "g0_scid_neutral_target_synthesis_saturation_self_redteam_pass_2026",
            "g12_audit_and_target_packet_artifacts_read_from_disk",
            "g12_neutral_target_audit_route",
            "g12_scid_asof_neutral_target_packet_audit_decision_ledger_2026"
          ],
          "path": "research/science_program_2026_05/06_outcome_testing/scid_strategy_field_source_expansion_packet/build_scid_strategy_field_source_expansion_packet_2026_05_12.py",
          "root_label": "current_scid_source_control_route_artifacts",
          "safe_shape_fingerprint_sha256": "fb7268a083575a0ad929a6bc88ea733fa6a86491a202d694986f353f77231712"
        }
      ]
    },
    {
      "as_of_rule": "POI bounds must come from the as-of market-state snapshot used by the decision packet",
      "coverage_status": "SHAPE_COVERAGE_PRESENT_EXACT_CAPTURE_FIELDS_INCOMPLETE",
      "exact_capture_requirement_to_close_gap": "Add/verify future additive capture rows for mso_snapshot_hash via source_safe_mso_snapshot_and_poi_logger; enforce source_id/source_hash/as_of/redaction/forbidden-key fail-closed checks before G12 acceptance.",
      "exact_schema_field_matches_found_by_name": [
        "poi_detection_rule_version",
        "poi_lower_bound",
        "poi_source_bar_ids",
        "poi_source_timeframe",
        "poi_type_enum_ob_fvg_breaker_swing_other_none",
        "poi_upper_bound"
      ],
      "existing_shape_artifact_count": 1824,
      "field_group": "poi_type_bounds_source",
      "future_source_or_logger": "source_safe_mso_snapshot_and_poi_logger",
      "historical_status": "NON_GENERATABLE_HISTORICAL_STRUCTURE_SOURCE_STATE_CAPTURE_REQUIRED",
      "label": "POI",
      "missing_exact_schema_fields": [
        "mso_snapshot_hash"
      ],
      "no_leak_rule": "do not reconstruct POI from later price movement or result-selection logic",
      "representative_shape_artifacts": [
        {
          "matched_key_count": 117,
          "matched_key_examples": [
            "final_closeout_detection.confirmed_observer_ids",
            "final_closeout_detection.confirmed_observer_ids[]",
            "final_closeout_detection.rows[].kill_zone_window_state",
            "final_closeout_detection.rows[].observer_id",
            "lifecycle_summary.latest_status_by_observer",
            "lifecycle_summary.latest_status_by_observer.eurusd_6e_mso_shadow_v1",
            "lifecycle_summary.latest_status_by_observer.eurusd_6e_mso_shadow_v1._line_no",
            "lifecycle_summary.latest_status_by_observer.eurusd_6e_mso_shadow_v1.activation_state",
            "lifecycle_summary.latest_status_by_observer.eurusd_6e_mso_shadow_v1.ai_calls",
            "lifecycle_summary.latest_status_by_observer.eurusd_6e_mso_shadow_v1.config_symbol",
            "lifecycle_summary.latest_status_by_observer.eurusd_6e_mso_shadow_v1.created_at_utc",
            "lifecycle_summary.latest_status_by_observer.eurusd_6e_mso_shadow_v1.databento_calls"
          ],
          "path": "shadow_logs/shadow_observer_hardening_status.jsonl",
          "root_label": "shadow_logs_shape_only_non_forbidden_families",
          "safe_shape_fingerprint_sha256": "a2450d69b76e4f90be802810813d9ed0c974ab7b20b762401e283aceef49fb37"
        },
        {
          "matched_key_count": 71,
          "matched_key_examples": [
            "_bounds_overlap",
            "_is_bounds",
            "action_required_decision_fvg_ob_leak_status_present",
            "astimezone",
            "backfilled_from_fvg_ob_resolution_path_structural_and_opportunity_rows",
            "both_fvg_and_ob_fire",
            "bounds",
            "build_fvg_ob_confluence_audit_rows",
            "candidate_path_row_not_available_for_fvg_ob",
            "confluence_bucket_captured_overlap_exact_bounds_missing",
            "decision_fvg_ob_no_leak_status",
            "exact_bounds_captured_rows"
          ],
          "path": "src/research_infra/fvg_ob_confluence_audit.py",
          "root_label": "research_infra_keyword_shapes",
          "safe_shape_fingerprint_sha256": "dab59412ffb025b37922834ff936e43bcc07ce00bb1ce8d41f0da544cc39a141"
        },
        {
          "matched_key_count": 62,
          "matched_key_examples": [
            "astimezone",
            "both_fvg_and_ob_fire",
            "breaker_block",
            "breaker_block_count",
            "breaker_blocks",
            "breaker_re_entry",
            "breaker_retest",
            "build_fvg_ob_confluence_row",
            "candidate_h1_poi_price_level",
            "candidate_h1_poi_type",
            "capture_observed_at_utc",
            "entry_touch_not_observed_source_safe"
          ],
          "path": "src/research_infra/forward_capture.py",
          "root_label": "research_infra_keyword_shapes",
          "safe_shape_fingerprint_sha256": "bacdff315bfc5e9429481bd6cf9deac34958633004ed08cdb1e3e937d25a7516"
        },
        {
          "matched_key_count": 45,
          "matched_key_examples": [
            "_kill_zone_window_state",
            "_latest_by_observer",
            "_max_kill_zone_end_utc",
            "_strategy_observer_counts",
            "action_required_observer_ids",
            "active_observers",
            "astimezone",
            "confirmed_observer_ids",
            "default_observer_registry_path",
            "g3_stale_observer_detection",
            "kill_zone_window_state",
            "kill_zones"
          ],
          "path": "src/research_infra/shadow_observer_hardening.py",
          "root_label": "research_infra_keyword_shapes",
          "safe_shape_fingerprint_sha256": "38ee26ec89af0e3c77dfb709e92a48f42d3213b269fec87844d4906f2eb74aa1"
        },
        {
          "matched_key_count": 41,
          "matched_key_examples": [
            "all_expected_behavior_observed",
            "blob",
            "bounds",
            "breaker",
            "breaker_re_entry",
            "checkpoint_chunk_resume_status",
            "entry_reference_type_market_limit_zone_midpoint_other",
            "fvg",
            "fvg_fill",
            "ltf_source_file_pointer_or_cache_id",
            "ob_retest",
            "object"
          ],
          "path": "C:/Users/MSI/Documents/ai-trading-agent/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/build_scid_forward_capture_offline_schema_implementation_package_2026_05_12.py",
          "root_label": "original_local_repo_scid_route_artifact_shapes::ai-trading-agent",
          "safe_shape_fingerprint_sha256": "2c971e6356e9178e94dcdc43a6a49f0cd5fa8d69c6586f521f28b0c71c3dde3d"
        },
        {
          "matched_key_count": 41,
          "matched_key_examples": [
            "blob",
            "blobs",
            "bounds",
            "breaker",
            "build_insertion_point_ledger",
            "entry_reference_type_market_limit_zone_midpoint_other",
            "existing_observable_surfaces",
            "fvg",
            "insertion_point",
            "insertion_points",
            "ltf_source_file_pointer_or_cache_id",
            "no_scoped_raw_market_blob"
          ],
          "path": "C:/tmp/gtos_otb/SCID_IMPL_DESIGN/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_implementation_design_package/build_scid_forward_capture_implementation_design_package_2026_05_12.py",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_IMPL_DESIGN",
          "safe_shape_fingerprint_sha256": "27c33e98b36b9919588d91275cb084291d54033b445c4a20872a38fa082349a6"
        },
        {
          "matched_key_count": 41,
          "matched_key_examples": [
            "all_expected_behavior_observed",
            "blob",
            "bounds",
            "breaker",
            "breaker_re_entry",
            "checkpoint_chunk_resume_status",
            "entry_reference_type_market_limit_zone_midpoint_other",
            "fvg",
            "fvg_fill",
            "ltf_source_file_pointer_or_cache_id",
            "ob_retest",
            "object"
          ],
          "path": "C:/tmp/gtos_otb/SCID_IMPL_DESIGN/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/build_scid_forward_capture_offline_schema_implementation_package_2026_05_12.py",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_IMPL_DESIGN",
          "safe_shape_fingerprint_sha256": "2c971e6356e9178e94dcdc43a6a49f0cd5fa8d69c6586f521f28b0c71c3dde3d"
        },
        {
          "matched_key_count": 41,
          "matched_key_examples": [
            "all_expected_behavior_observed",
            "blob",
            "bounds",
            "breaker",
            "breaker_re_entry",
            "checkpoint_chunk_resume_status",
            "entry_reference_type_market_limit_zone_midpoint_other",
            "fvg",
            "fvg_fill",
            "ltf_source_file_pointer_or_cache_id",
            "ob_retest",
            "object"
          ],
          "path": "C:/tmp/gtos_otb/SCID_LTF_OF_EXPANSION/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/build_scid_forward_capture_offline_schema_implementation_package_2026_05_12.py",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_LTF_OF_EXPANSION",
          "safe_shape_fingerprint_sha256": "2c971e6356e9178e94dcdc43a6a49f0cd5fa8d69c6586f521f28b0c71c3dde3d"
        },
        {
          "matched_key_count": 41,
          "matched_key_examples": [
            "all_expected_behavior_observed",
            "blob",
            "bounds",
            "breaker",
            "breaker_re_entry",
            "checkpoint_chunk_resume_status",
            "entry_reference_type_market_limit_zone_midpoint_other",
            "fvg",
            "fvg_fill",
            "ltf_source_file_pointer_or_cache_id",
            "ob_retest",
            "object"
          ],
          "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/build_scid_forward_capture_offline_schema_implementation_package_2026_05_12.py",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_NOAPI_HYP_FACTORY",
          "safe_shape_fingerprint_sha256": "2c971e6356e9178e94dcdc43a6a49f0cd5fa8d69c6586f521f28b0c71c3dde3d"
        },
        {
          "matched_key_count": 41,
          "matched_key_examples": [
            "all_expected_behavior_observed",
            "blob",
            "bounds",
            "breaker",
            "breaker_re_entry",
            "checkpoint_chunk_resume_status",
            "entry_reference_type_market_limit_zone_midpoint_other",
            "fvg",
            "fvg_fill",
            "ltf_source_file_pointer_or_cache_id",
            "ob_retest",
            "object"
          ],
          "path": "C:/tmp/gtos_otb/SCID_SYNTH_HARNESS/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/build_scid_forward_capture_offline_schema_implementation_package_2026_05_12.py",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_SYNTH_HARNESS",
          "safe_shape_fingerprint_sha256": "2c971e6356e9178e94dcdc43a6a49f0cd5fa8d69c6586f521f28b0c71c3dde3d"
        },
        {
          "matched_key_count": 41,
          "matched_key_examples": [
            "all_expected_behavior_observed",
            "blob",
            "bounds",
            "breaker",
            "breaker_re_entry",
            "checkpoint_chunk_resume_status",
            "entry_reference_type_market_limit_zone_midpoint_other",
            "fvg",
            "fvg_fill",
            "ltf_source_file_pointer_or_cache_id",
            "ob_retest",
            "object"
          ],
          "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/build_scid_forward_capture_offline_schema_implementation_package_2026_05_12.py",
          "root_label": "current_scid_source_control_route_artifacts",
          "safe_shape_fingerprint_sha256": "2c971e6356e9178e94dcdc43a6a49f0cd5fa8d69c6586f521f28b0c71c3dde3d"
        },
        {
          "matched_key_count": 40,
          "matched_key_examples": [
            "_active_question_stack_and_checkpoint_ledger_",
            "active_question_stack_and_checkpoint_ledger",
            "active_question_stack_and_checkpoint_resume_ledger",
            "blob",
            "blobs",
            "bounds",
            "breaker",
            "capture_contract_frozen_with_raw_blob_and_proxy_boundaries",
            "checkpoint",
            "checkpoint_chunk_resume_status",
            "checkpoint_resume_ledger",
            "checkpoint_resume_policy"
          ],
          "path": "C:/Users/MSI/Documents/ai-trading-agent/research/science_program_2026_05/06_outcome_testing/scid_combined_source_search_and_forward_capture_route/build_scid_combined_source_search_and_forward_capture_route_2026_05_12.py",
          "root_label": "original_local_repo_scid_route_artifact_shapes::ai-trading-agent",
          "safe_shape_fingerprint_sha256": "051dbd6879e0a78a8270c1a839a7a76089982d7213ac9f950404402f13247da4"
        }
      ]
    },
    {
      "as_of_rule": "framework selection/evaluation must be logged before L2, fill, or path result fields are known",
      "coverage_status": "SHAPE_COVERAGE_PRESENT_EXACT_CAPTURE_FIELDS_PRESENT_IN_INSPECTED_SHAPES",
      "exact_capture_requirement_to_close_gap": "Add/verify future additive capture rows for frameworks_evaluated, framework_qualified_flags, selected_framework_or_none, setup_family, framework_tiebreak_rule_id, framework_source_snapshot_hash via source_safe_strategy_decision_packet_logger; enforce source_id/source_hash/as_of/redaction/forbidden-key fail-closed checks before G12 acceptance.",
      "exact_schema_field_matches_found_by_name": [
        "framework_qualified_flags",
        "framework_source_snapshot_hash",
        "framework_tiebreak_rule_id",
        "frameworks_evaluated",
        "selected_framework_or_none",
        "setup_family"
      ],
      "existing_shape_artifact_count": 351,
      "field_group": "framework_setup_family",
      "future_source_or_logger": "source_safe_strategy_decision_packet_logger",
      "historical_status": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
      "label": "framework",
      "missing_exact_schema_fields": [],
      "no_leak_rule": "framework cannot be assigned from later path shape or favorable outcome family",
      "representative_shape_artifacts": [
        {
          "matched_key_count": 19,
          "matched_key_examples": [
            "field_group_contracts.framework_setup_family",
            "field_group_contracts.framework_setup_family.as_of_rule",
            "field_group_contracts.framework_setup_family.fields",
            "field_group_contracts.framework_setup_family.fields[]",
            "field_group_contracts.framework_setup_family.fields[].as_of_semantics",
            "field_group_contracts.framework_setup_family.fields[].downstream_g12_acceptance_rule",
            "field_group_contracts.framework_setup_family.fields[].enum",
            "field_group_contracts.framework_setup_family.fields[].enum[]",
            "field_group_contracts.framework_setup_family.fields[].fail_closed_missing_status",
            "field_group_contracts.framework_setup_family.fields[].forbidden_value_policy",
            "field_group_contracts.framework_setup_family.fields[].name",
            "field_group_contracts.framework_setup_family.fields[].nullable"
          ],
          "path": "C:/Users/MSI/Documents/ai-trading-agent/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT_2026-05-12.json",
          "root_label": "original_local_repo_scid_route_artifact_shapes::ai-trading-agent",
          "safe_shape_fingerprint_sha256": "82201d61e896d2af7552d2451ce0e7f557de9c3b24a6fb1b5a08c4109ca10cc5"
        },
        {
          "matched_key_count": 19,
          "matched_key_examples": [
            "properties.framework_qualified_flags",
            "properties.framework_qualified_flags.type",
            "properties.framework_source_snapshot_hash",
            "properties.framework_source_snapshot_hash.minLength",
            "properties.framework_source_snapshot_hash.type",
            "properties.framework_tiebreak_rule_id",
            "properties.framework_tiebreak_rule_id.minLength",
            "properties.framework_tiebreak_rule_id.type",
            "properties.frameworks_evaluated",
            "properties.frameworks_evaluated.items",
            "properties.frameworks_evaluated.items.type",
            "properties.frameworks_evaluated.type"
          ],
          "path": "C:/Users/MSI/Documents/ai-trading-agent/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/schemas/scid_forward_source_capture_v1_framework_setup_family.schema.json",
          "root_label": "original_local_repo_scid_route_artifact_shapes::ai-trading-agent",
          "safe_shape_fingerprint_sha256": "3211c32ba5a8b8711ab9e5c23386555dababeead4bbe401b0ed09a662f46463b"
        },
        {
          "matched_key_count": 19,
          "matched_key_examples": [
            "field_group_contracts.framework_setup_family",
            "field_group_contracts.framework_setup_family.as_of_rule",
            "field_group_contracts.framework_setup_family.fields",
            "field_group_contracts.framework_setup_family.fields[]",
            "field_group_contracts.framework_setup_family.fields[].as_of_semantics",
            "field_group_contracts.framework_setup_family.fields[].downstream_g12_acceptance_rule",
            "field_group_contracts.framework_setup_family.fields[].enum",
            "field_group_contracts.framework_setup_family.fields[].enum[]",
            "field_group_contracts.framework_setup_family.fields[].fail_closed_missing_status",
            "field_group_contracts.framework_setup_family.fields[].forbidden_value_policy",
            "field_group_contracts.framework_setup_family.fields[].name",
            "field_group_contracts.framework_setup_family.fields[].nullable"
          ],
          "path": "C:/tmp/gtos_otb/SCID_IMPL_DESIGN/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT_2026-05-12.json",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_IMPL_DESIGN",
          "safe_shape_fingerprint_sha256": "82201d61e896d2af7552d2451ce0e7f557de9c3b24a6fb1b5a08c4109ca10cc5"
        },
        {
          "matched_key_count": 19,
          "matched_key_examples": [
            "properties.framework_qualified_flags",
            "properties.framework_qualified_flags.type",
            "properties.framework_source_snapshot_hash",
            "properties.framework_source_snapshot_hash.minLength",
            "properties.framework_source_snapshot_hash.type",
            "properties.framework_tiebreak_rule_id",
            "properties.framework_tiebreak_rule_id.minLength",
            "properties.framework_tiebreak_rule_id.type",
            "properties.frameworks_evaluated",
            "properties.frameworks_evaluated.items",
            "properties.frameworks_evaluated.items.type",
            "properties.frameworks_evaluated.type"
          ],
          "path": "C:/tmp/gtos_otb/SCID_IMPL_DESIGN/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/schemas/scid_forward_source_capture_v1_framework_setup_family.schema.json",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_IMPL_DESIGN",
          "safe_shape_fingerprint_sha256": "3211c32ba5a8b8711ab9e5c23386555dababeead4bbe401b0ed09a662f46463b"
        },
        {
          "matched_key_count": 19,
          "matched_key_examples": [
            "field_group_contracts.framework_setup_family",
            "field_group_contracts.framework_setup_family.as_of_rule",
            "field_group_contracts.framework_setup_family.fields",
            "field_group_contracts.framework_setup_family.fields[]",
            "field_group_contracts.framework_setup_family.fields[].as_of_semantics",
            "field_group_contracts.framework_setup_family.fields[].downstream_g12_acceptance_rule",
            "field_group_contracts.framework_setup_family.fields[].enum",
            "field_group_contracts.framework_setup_family.fields[].enum[]",
            "field_group_contracts.framework_setup_family.fields[].fail_closed_missing_status",
            "field_group_contracts.framework_setup_family.fields[].forbidden_value_policy",
            "field_group_contracts.framework_setup_family.fields[].name",
            "field_group_contracts.framework_setup_family.fields[].nullable"
          ],
          "path": "C:/tmp/gtos_otb/SCID_LTF_OF_EXPANSION/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT_2026-05-12.json",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_LTF_OF_EXPANSION",
          "safe_shape_fingerprint_sha256": "82201d61e896d2af7552d2451ce0e7f557de9c3b24a6fb1b5a08c4109ca10cc5"
        },
        {
          "matched_key_count": 19,
          "matched_key_examples": [
            "properties.framework_qualified_flags",
            "properties.framework_qualified_flags.type",
            "properties.framework_source_snapshot_hash",
            "properties.framework_source_snapshot_hash.minLength",
            "properties.framework_source_snapshot_hash.type",
            "properties.framework_tiebreak_rule_id",
            "properties.framework_tiebreak_rule_id.minLength",
            "properties.framework_tiebreak_rule_id.type",
            "properties.frameworks_evaluated",
            "properties.frameworks_evaluated.items",
            "properties.frameworks_evaluated.items.type",
            "properties.frameworks_evaluated.type"
          ],
          "path": "C:/tmp/gtos_otb/SCID_LTF_OF_EXPANSION/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/schemas/scid_forward_source_capture_v1_framework_setup_family.schema.json",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_LTF_OF_EXPANSION",
          "safe_shape_fingerprint_sha256": "3211c32ba5a8b8711ab9e5c23386555dababeead4bbe401b0ed09a662f46463b"
        },
        {
          "matched_key_count": 19,
          "matched_key_examples": [
            "field_group_contracts.framework_setup_family",
            "field_group_contracts.framework_setup_family.as_of_rule",
            "field_group_contracts.framework_setup_family.fields",
            "field_group_contracts.framework_setup_family.fields[]",
            "field_group_contracts.framework_setup_family.fields[].as_of_semantics",
            "field_group_contracts.framework_setup_family.fields[].downstream_g12_acceptance_rule",
            "field_group_contracts.framework_setup_family.fields[].enum",
            "field_group_contracts.framework_setup_family.fields[].enum[]",
            "field_group_contracts.framework_setup_family.fields[].fail_closed_missing_status",
            "field_group_contracts.framework_setup_family.fields[].forbidden_value_policy",
            "field_group_contracts.framework_setup_family.fields[].name",
            "field_group_contracts.framework_setup_family.fields[].nullable"
          ],
          "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT_2026-05-12.json",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_NOAPI_HYP_FACTORY",
          "safe_shape_fingerprint_sha256": "82201d61e896d2af7552d2451ce0e7f557de9c3b24a6fb1b5a08c4109ca10cc5"
        },
        {
          "matched_key_count": 19,
          "matched_key_examples": [
            "properties.framework_qualified_flags",
            "properties.framework_qualified_flags.type",
            "properties.framework_source_snapshot_hash",
            "properties.framework_source_snapshot_hash.minLength",
            "properties.framework_source_snapshot_hash.type",
            "properties.framework_tiebreak_rule_id",
            "properties.framework_tiebreak_rule_id.minLength",
            "properties.framework_tiebreak_rule_id.type",
            "properties.frameworks_evaluated",
            "properties.frameworks_evaluated.items",
            "properties.frameworks_evaluated.items.type",
            "properties.frameworks_evaluated.type"
          ],
          "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/schemas/scid_forward_source_capture_v1_framework_setup_family.schema.json",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_NOAPI_HYP_FACTORY",
          "safe_shape_fingerprint_sha256": "3211c32ba5a8b8711ab9e5c23386555dababeead4bbe401b0ed09a662f46463b"
        },
        {
          "matched_key_count": 19,
          "matched_key_examples": [
            "field_group_contracts.framework_setup_family",
            "field_group_contracts.framework_setup_family.as_of_rule",
            "field_group_contracts.framework_setup_family.fields",
            "field_group_contracts.framework_setup_family.fields[]",
            "field_group_contracts.framework_setup_family.fields[].as_of_semantics",
            "field_group_contracts.framework_setup_family.fields[].downstream_g12_acceptance_rule",
            "field_group_contracts.framework_setup_family.fields[].enum",
            "field_group_contracts.framework_setup_family.fields[].enum[]",
            "field_group_contracts.framework_setup_family.fields[].fail_closed_missing_status",
            "field_group_contracts.framework_setup_family.fields[].forbidden_value_policy",
            "field_group_contracts.framework_setup_family.fields[].name",
            "field_group_contracts.framework_setup_family.fields[].nullable"
          ],
          "path": "C:/tmp/gtos_otb/SCID_SYNTH_HARNESS/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT_2026-05-12.json",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_SYNTH_HARNESS",
          "safe_shape_fingerprint_sha256": "82201d61e896d2af7552d2451ce0e7f557de9c3b24a6fb1b5a08c4109ca10cc5"
        },
        {
          "matched_key_count": 19,
          "matched_key_examples": [
            "properties.framework_qualified_flags",
            "properties.framework_qualified_flags.type",
            "properties.framework_source_snapshot_hash",
            "properties.framework_source_snapshot_hash.minLength",
            "properties.framework_source_snapshot_hash.type",
            "properties.framework_tiebreak_rule_id",
            "properties.framework_tiebreak_rule_id.minLength",
            "properties.framework_tiebreak_rule_id.type",
            "properties.frameworks_evaluated",
            "properties.frameworks_evaluated.items",
            "properties.frameworks_evaluated.items.type",
            "properties.frameworks_evaluated.type"
          ],
          "path": "C:/tmp/gtos_otb/SCID_SYNTH_HARNESS/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/schemas/scid_forward_source_capture_v1_framework_setup_family.schema.json",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_SYNTH_HARNESS",
          "safe_shape_fingerprint_sha256": "3211c32ba5a8b8711ab9e5c23386555dababeead4bbe401b0ed09a662f46463b"
        },
        {
          "matched_key_count": 19,
          "matched_key_examples": [
            "field_group_contracts.framework_setup_family",
            "field_group_contracts.framework_setup_family.as_of_rule",
            "field_group_contracts.framework_setup_family.fields",
            "field_group_contracts.framework_setup_family.fields[]",
            "field_group_contracts.framework_setup_family.fields[].as_of_semantics",
            "field_group_contracts.framework_setup_family.fields[].downstream_g12_acceptance_rule",
            "field_group_contracts.framework_setup_family.fields[].enum",
            "field_group_contracts.framework_setup_family.fields[].enum[]",
            "field_group_contracts.framework_setup_family.fields[].fail_closed_missing_status",
            "field_group_contracts.framework_setup_family.fields[].forbidden_value_policy",
            "field_group_contracts.framework_setup_family.fields[].name",
            "field_group_contracts.framework_setup_family.fields[].nullable"
          ],
          "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT_2026-05-12.json",
          "root_label": "current_scid_source_control_route_artifacts",
          "safe_shape_fingerprint_sha256": "82201d61e896d2af7552d2451ce0e7f557de9c3b24a6fb1b5a08c4109ca10cc5"
        },
        {
          "matched_key_count": 19,
          "matched_key_examples": [
            "properties.framework_qualified_flags",
            "properties.framework_qualified_flags.type",
            "properties.framework_source_snapshot_hash",
            "properties.framework_source_snapshot_hash.minLength",
            "properties.framework_source_snapshot_hash.type",
            "properties.framework_tiebreak_rule_id",
            "properties.framework_tiebreak_rule_id.minLength",
            "properties.framework_tiebreak_rule_id.type",
            "properties.frameworks_evaluated",
            "properties.frameworks_evaluated.items",
            "properties.frameworks_evaluated.items.type",
            "properties.frameworks_evaluated.type"
          ],
          "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/schemas/scid_forward_source_capture_v1_framework_setup_family.schema.json",
          "root_label": "current_scid_source_control_route_artifacts",
          "safe_shape_fingerprint_sha256": "3211c32ba5a8b8711ab9e5c23386555dababeead4bbe401b0ed09a662f46463b"
        }
      ]
    },
    {
      "as_of_rule": "lifecycle events must be append-only and timestamped when GTOS observes or changes intent state",
      "coverage_status": "SHAPE_COVERAGE_PRESENT_EXACT_CAPTURE_FIELDS_INCOMPLETE",
      "exact_capture_requirement_to_close_gap": "Add/verify future additive capture rows for redacted_order_bridge_hash_optional, source_event_clock_basis, source_event_utc via nonbroker_pending_intent_lifecycle_event_logger; enforce source_id/source_hash/as_of/redaction/forbidden-key fail-closed checks before G12 acceptance.",
      "exact_schema_field_matches_found_by_name": [
        "intent_state_after",
        "intent_state_before",
        "pending_intent_id",
        "source_event_type_created_updated_expired_cancelled_replaced_no_order"
      ],
      "existing_shape_artifact_count": 513,
      "field_group": "lifecycle_fill_cancel_expiry_source_status",
      "future_source_or_logger": "nonbroker_pending_intent_lifecycle_event_logger",
      "historical_status": "NON_GENERATABLE_HISTORICAL_LIFECYCLE_SOURCE_TRUTH_CAPTURE_REQUIRED",
      "label": "lifecycle",
      "missing_exact_schema_fields": [
        "redacted_order_bridge_hash_optional",
        "source_event_clock_basis",
        "source_event_utc"
      ],
      "no_leak_rule": "do not use broker account history, deal/position/order history, realized result, or later path labels",
      "representative_shape_artifacts": [
        {
          "matched_key_count": 97,
          "matched_key_examples": [
            "created_at_utc",
            "final_closeout_detection.rows[].latest_lifecycle_status",
            "lifecycle_summary",
            "lifecycle_summary.latest_status_by_observer",
            "lifecycle_summary.latest_status_by_observer.eurusd_6e_mso_shadow_v1",
            "lifecycle_summary.latest_status_by_observer.eurusd_6e_mso_shadow_v1._line_no",
            "lifecycle_summary.latest_status_by_observer.eurusd_6e_mso_shadow_v1.activation_state",
            "lifecycle_summary.latest_status_by_observer.eurusd_6e_mso_shadow_v1.ai_calls",
            "lifecycle_summary.latest_status_by_observer.eurusd_6e_mso_shadow_v1.config_symbol",
            "lifecycle_summary.latest_status_by_observer.eurusd_6e_mso_shadow_v1.created_at_utc",
            "lifecycle_summary.latest_status_by_observer.eurusd_6e_mso_shadow_v1.databento_calls",
            "lifecycle_summary.latest_status_by_observer.eurusd_6e_mso_shadow_v1.decision_time_utc"
          ],
          "path": "shadow_logs/shadow_observer_hardening_status.jsonl",
          "root_label": "shadow_logs_shape_only_non_forbidden_families",
          "safe_shape_fingerprint_sha256": "a2450d69b76e4f90be802810813d9ed0c974ab7b20b762401e283aceef49fb37"
        },
        {
          "matched_key_count": 88,
          "matched_key_examples": [
            "_candidate_matches_lifecycle",
            "_pendingintentunpickler",
            "_persisted_intent_matches_lifecycle",
            "_plainpendingintent",
            "_trade_record_limit_intent",
            "_trade_record_matches_lifecycle",
            "action_required_active_pending_intent_not_persisted",
            "action_required_missing_cancel_reason",
            "action_required_missing_lifecycle_truth",
            "backfilled_from_lifecycle_candidate_trade_record_path_and_pending_intent_rows",
            "build_missing_lifecycle_audit_row",
            "build_pending_limit_lifecycle_audit_row"
          ],
          "path": "src/research_infra/pending_limit_lifecycle_audit.py",
          "root_label": "research_infra_keyword_shapes",
          "safe_shape_fingerprint_sha256": "dd320ce6150cddaca4018eb525d52aaf6ad15660a37fb70b3834df8dfcc3a273"
        },
        {
          "matched_key_count": 46,
          "matched_key_examples": [
            "_lifecycle_matches_candidate",
            "_pending_limit_strategy_status",
            "best_created",
            "cancelled_sl_too_close",
            "computed_from_pending_lifecycle",
            "correction_of_created_at_utc",
            "created",
            "created_at_utc",
            "default_pending_lifecycle",
            "expired_48h",
            "intent",
            "intent_after_check"
          ],
          "path": "src/research_infra/live_mechanical_shadow.py",
          "root_label": "research_infra_keyword_shapes",
          "safe_shape_fingerprint_sha256": "0b2f11cbdcf30b23afb2b17009f4ed8261ce7b59fc06bf3f29538e02bc34d244"
        },
        {
          "matched_key_count": 46,
          "matched_key_examples": [
            "_lifecycle_state",
            "_pending_audit_by_trade_record_path",
            "build_trade_index_lifecycle_rows",
            "by_lifecycle_completeness",
            "by_trade_index_lifecycle_status",
            "created_at_utc",
            "embedded_pending",
            "has_embedded_pending",
            "has_embedded_pending_lifecycle",
            "has_pending_audit",
            "has_pending_lifecycle_audit",
            "lifecycle"
          ],
          "path": "src/research_infra/trade_index_lifecycle_audit.py",
          "root_label": "research_infra_keyword_shapes",
          "safe_shape_fingerprint_sha256": "60f08a8ebae1edf7233e3bff02f773fb0ef4dd0f26a4d7f9eb146acde735957e"
        },
        {
          "matched_key_count": 39,
          "matched_key_examples": [
            "_pending_appends",
            "_pending_limit_intent_snapshot",
            "cancel_expiry_abort_reason",
            "cancel_expiry_reason_status",
            "cancel_expiry_utc",
            "cancel_or_expiry_reason_captured_source_safe",
            "cancel_reason",
            "cancel_time_utc",
            "created_at_utc",
            "decision_time_source_captured_path_derivation_pending",
            "execution_lifecycle",
            "expiry_time_utc"
          ],
          "path": "src/research_infra/forward_capture.py",
          "root_label": "research_infra_keyword_shapes",
          "safe_shape_fingerprint_sha256": "bacdff315bfc5e9429481bd6cf9deac34958633004ed08cdb1e3e937d25a7516"
        },
        {
          "matched_key_count": 32,
          "matched_key_examples": [
            "_lifecycle",
            "action_required_active_pending_intent_not_persisted",
            "build_pending_limit_lifecycle_audit_rows",
            "cancel_reason",
            "created_at_utc",
            "intent_after_check",
            "internal_candle_polled_intent",
            "legacy_lifecycle_row_candidate_id_not_captured_recovered_from_trade_record",
            "lifecycle",
            "limit_intent",
            "limit_placed_source_has_no_matching_pending_lifecycle_group",
            "matched_active_persisted_intent"
          ],
          "path": "tests/test_pending_limit_lifecycle_audit.py",
          "root_label": "focused_tests_keyword_shapes",
          "safe_shape_fingerprint_sha256": "ef53121dc302eb530868cbd1461946381d4a943c04d655ed933dc95b0a025203"
        },
        {
          "matched_key_count": 29,
          "matched_key_examples": [
            "_pending_audit",
            "action_required_missing_lifecycle_truth",
            "build_trade_index_lifecycle_rows",
            "has_pending_lifecycle_audit",
            "lifecycle_completeness",
            "limit_intent",
            "limit_placed_complete_with_pending_lifecycle_audit",
            "limit_placed_documented_legacy_lifecycle_gap",
            "matched_pending_lifecycle_audit_action_required",
            "no_fill_still_pending",
            "no_lifecycle_group",
            "pending1"
          ],
          "path": "tests/test_trade_index_lifecycle_audit.py",
          "root_label": "focused_tests_keyword_shapes",
          "safe_shape_fingerprint_sha256": "206ce477f4e87aba2f856f3fd1d8239206f21fe4ff0f203cb10ed59b54f5ab83"
        },
        {
          "matched_key_count": 25,
          "matched_key_examples": [
            "build_pending_limit_lifecycle_entry",
            "cancel",
            "cancel_limit_intent",
            "cancel_reason",
            "cancelled_sl_too_close",
            "expired_48h",
            "expiry",
            "intent_after_check",
            "internal_candle_polled_intent",
            "internal_limit_lifecycle",
            "lifecycle",
            "lifecycle_mod"
          ],
          "path": "tests/test_pending_limit_lifecycle_logger.py",
          "root_label": "focused_tests_keyword_shapes",
          "safe_shape_fingerprint_sha256": "b1426f32bea9cb697643496f6f89b132ea09d53273d445002e0c7111d955853e"
        },
        {
          "matched_key_count": 24,
          "matched_key_examples": [
            "created_at_utc",
            "feature_availability.source_refs.databento_trigger.created_at_utc",
            "feature_availability.source_refs.decision_diagnostics.created_at_utc",
            "feature_availability.source_refs.j46_j49.created_at_utc",
            "feature_availability.source_refs.mechanical_context.created_at_utc",
            "feature_availability.source_refs.mso.created_at_utc",
            "feature_availability.source_refs.orderflow_status.created_at_utc",
            "feature_availability.source_refs.regime_decay.created_at_utc",
            "feature_availability.source_refs.s79.created_at_utc",
            "feature_availability.source_refs.sierra_depth.created_at_utc",
            "feature_availability.source_refs.sierra_proxy.created_at_utc",
            "feature_availability.source_refs.sierra_status.created_at_utc"
          ],
          "path": "shadow_logs/ml_shadow_predictions.jsonl",
          "root_label": "shadow_logs_shape_only_non_forbidden_families",
          "safe_shape_fingerprint_sha256": "9bb0509929154d071d7b3150c50bd1a6612d18ba5c81688c62a5db1f6a2d0b61"
        },
        {
          "matched_key_count": 24,
          "matched_key_examples": [
            "build_opportunity_lifecycle_audit_row",
            "build_opportunity_lifecycle_audit_rows",
            "cancel",
            "candidate_lifecycle_signature",
            "created_at_utc",
            "current_created",
            "expiry",
            "formal_lifecycle_states",
            "legacy_cluster_row_lifecycle_signature_not_captured",
            "legacy_cluster_row_lifecycle_state_not_captured",
            "lifecycle",
            "lifecycle_state"
          ],
          "path": "src/research_infra/opportunity_lifecycle_audit.py",
          "root_label": "research_infra_keyword_shapes",
          "safe_shape_fingerprint_sha256": "c9ea81a100e2acee767a44d8380dc7ac5e09e9c90bbb3c647ab944dad000ce06"
        },
        {
          "matched_key_count": 22,
          "matched_key_examples": [
            "answered_fail_closed_for_historical_intent_fields",
            "cancel",
            "expiry",
            "explicit_new_strategy_intent_recoveries",
            "explicit_scid_key_hits_present_but_no_new_strategy_intent_field_beyond_accepted_packet",
            "focused_tests_pending",
            "forbidden_or_insufficient_for_strategy_intent",
            "historical_intent_fields",
            "intent",
            "intent_state_after",
            "intent_state_before",
            "lifecycle"
          ],
          "path": "C:/Users/MSI/Documents/ai-trading-agent/research/science_program_2026_05/06_outcome_testing/scid_combined_source_search_and_forward_capture_route/build_scid_combined_source_search_and_forward_capture_route_2026_05_12.py",
          "root_label": "original_local_repo_scid_route_artifact_shapes::ai-trading-agent",
          "safe_shape_fingerprint_sha256": "051dbd6879e0a78a8270c1a839a7a76089982d7213ac9f950404402f13247da4"
        },
        {
          "matched_key_count": 22,
          "matched_key_examples": [
            "answered_fail_closed_for_historical_intent_fields",
            "cancel",
            "expiry",
            "explicit_new_strategy_intent_recoveries",
            "explicit_scid_key_hits_present_but_no_new_strategy_intent_field_beyond_accepted_packet",
            "focused_tests_pending",
            "forbidden_or_insufficient_for_strategy_intent",
            "historical_intent_fields",
            "intent",
            "intent_state_after",
            "intent_state_before",
            "lifecycle"
          ],
          "path": "C:/tmp/gtos_otb/SCID_IMPL_DESIGN/research/science_program_2026_05/06_outcome_testing/scid_combined_source_search_and_forward_capture_route/build_scid_combined_source_search_and_forward_capture_route_2026_05_12.py",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_IMPL_DESIGN",
          "safe_shape_fingerprint_sha256": "051dbd6879e0a78a8270c1a839a7a76089982d7213ac9f950404402f13247da4"
        }
      ]
    },
    {
      "as_of_rule": "only bars/ticks with timestamps <= decision_asof_utc may be used for availability or descriptor fields",
      "coverage_status": "SHAPE_COVERAGE_PRESENT_EXACT_CAPTURE_FIELDS_INCOMPLETE",
      "exact_capture_requirement_to_close_gap": "Add/verify future additive capture rows for asof_path_descriptor_version, decision_minus_window_start_utc via ltf_source_availability_and_path_descriptor_capture; enforce source_id/source_hash/as_of/redaction/forbidden-key fail-closed checks before G12 acceptance.",
      "exact_schema_field_matches_found_by_name": [
        "bars_present_by_timeframe",
        "ltf_availability_status",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "ltf_timeframes_available"
      ],
      "existing_shape_artifact_count": 489,
      "field_group": "lower_timeframe_asof_path_availability",
      "future_source_or_logger": "ltf_source_availability_and_path_descriptor_capture",
      "historical_status": "RECOVERABLE_MARKET_CONTEXT_BUT_NOT_ATTACHED_TO_ACCEPTED_CANDIDATES_CAPTURE_REQUIRED",
      "label": "LTF",
      "missing_exact_schema_fields": [
        "asof_path_descriptor_version",
        "decision_minus_window_start_utc"
      ],
      "no_leak_rule": "availability/path descriptors cannot include post-decision target/stop/fill status",
      "representative_shape_artifacts": [
        {
          "matched_key_count": 52,
          "matched_key_examples": [
            "action_required_decision_prefill_leak_status_present",
            "ambiguous_ltf_order_requires_ticks",
            "ambiguous_path_order_requires_ticks",
            "backfilled_from_prefill_resolution_path_ltf_pending_structural_and_opportunity_rows",
            "build_prefill_delivery_path_audit_rows",
            "candidate_path_row_not_available_for_prefill",
            "decision_prefill_no_leak_status",
            "derived_from_ltf_path_order_asof",
            "derived_prefill_path_status",
            "derived_prefill_path_status_counts",
            "entry_touched_unresolved_by_ltf_asof",
            "exact_prefill_candle_sequence_source_not_captured"
          ],
          "path": "src/research_infra/prefill_delivery_path_audit.py",
          "root_label": "research_infra_keyword_shapes",
          "safe_shape_fingerprint_sha256": "b6cee28f87cb56f34b5c75a933a28211980442d9b611ddc8f3f0b5b822b51881"
        },
        {
          "matched_key_count": 47,
          "matched_key_examples": [
            "field_statuses.lower_timeframe_asof_path_availability",
            "field_statuses.lower_timeframe_asof_path_availability.reason",
            "field_statuses.lower_timeframe_asof_path_availability.requirement_id",
            "field_statuses.lower_timeframe_asof_path_availability.source_paths_searched",
            "field_statuses.lower_timeframe_asof_path_availability.source_paths_searched[]",
            "field_statuses.lower_timeframe_asof_path_availability.source_truth_class",
            "field_statuses.lower_timeframe_asof_path_availability.status",
            "field_statuses.lower_timeframe_asof_path_availability.value_summary",
            "field_statuses.lower_timeframe_asof_path_availability.value_summary.accepted_packet_interval",
            "field_statuses.lower_timeframe_asof_path_availability.value_summary.lower_timeframe_source_attached",
            "field_statuses.lower_timeframe_asof_path_availability.value_summary.prior_windows",
            "field_statuses.lower_timeframe_asof_path_availability.value_summary.prior_windows.16"
          ],
          "path": "C:/Users/MSI/Documents/ai-trading-agent/research/science_program_2026_05/06_outcome_testing/scid_strategy_field_source_expansion_packet/SCID_STRATEGY_FIELD_CANDIDATE_FIELD_CLOSURE_LEDGER_2026-05-12.jsonl",
          "root_label": "original_local_repo_scid_route_artifact_shapes::ai-trading-agent",
          "safe_shape_fingerprint_sha256": "32eee23c4e196aa14f888ebcb3a04243371aca06a73d6f22b1b50b8a1ea4f27c"
        },
        {
          "matched_key_count": 47,
          "matched_key_examples": [
            "field_statuses.lower_timeframe_asof_path_availability",
            "field_statuses.lower_timeframe_asof_path_availability.reason",
            "field_statuses.lower_timeframe_asof_path_availability.requirement_id",
            "field_statuses.lower_timeframe_asof_path_availability.source_paths_searched",
            "field_statuses.lower_timeframe_asof_path_availability.source_paths_searched[]",
            "field_statuses.lower_timeframe_asof_path_availability.source_truth_class",
            "field_statuses.lower_timeframe_asof_path_availability.status",
            "field_statuses.lower_timeframe_asof_path_availability.value_summary",
            "field_statuses.lower_timeframe_asof_path_availability.value_summary.accepted_packet_interval",
            "field_statuses.lower_timeframe_asof_path_availability.value_summary.lower_timeframe_source_attached",
            "field_statuses.lower_timeframe_asof_path_availability.value_summary.prior_windows",
            "field_statuses.lower_timeframe_asof_path_availability.value_summary.prior_windows.16"
          ],
          "path": "C:/tmp/gtos_otb/SCID_IMPL_DESIGN/research/science_program_2026_05/06_outcome_testing/scid_strategy_field_source_expansion_packet/SCID_STRATEGY_FIELD_CANDIDATE_FIELD_CLOSURE_LEDGER_2026-05-12.jsonl",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_IMPL_DESIGN",
          "safe_shape_fingerprint_sha256": "32eee23c4e196aa14f888ebcb3a04243371aca06a73d6f22b1b50b8a1ea4f27c"
        },
        {
          "matched_key_count": 47,
          "matched_key_examples": [
            "field_statuses.lower_timeframe_asof_path_availability",
            "field_statuses.lower_timeframe_asof_path_availability.reason",
            "field_statuses.lower_timeframe_asof_path_availability.requirement_id",
            "field_statuses.lower_timeframe_asof_path_availability.source_paths_searched",
            "field_statuses.lower_timeframe_asof_path_availability.source_paths_searched[]",
            "field_statuses.lower_timeframe_asof_path_availability.source_truth_class",
            "field_statuses.lower_timeframe_asof_path_availability.status",
            "field_statuses.lower_timeframe_asof_path_availability.value_summary",
            "field_statuses.lower_timeframe_asof_path_availability.value_summary.accepted_packet_interval",
            "field_statuses.lower_timeframe_asof_path_availability.value_summary.lower_timeframe_source_attached",
            "field_statuses.lower_timeframe_asof_path_availability.value_summary.prior_windows",
            "field_statuses.lower_timeframe_asof_path_availability.value_summary.prior_windows.16"
          ],
          "path": "C:/tmp/gtos_otb/SCID_LTF_OF_EXPANSION/research/science_program_2026_05/06_outcome_testing/scid_strategy_field_source_expansion_packet/SCID_STRATEGY_FIELD_CANDIDATE_FIELD_CLOSURE_LEDGER_2026-05-12.jsonl",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_LTF_OF_EXPANSION",
          "safe_shape_fingerprint_sha256": "32eee23c4e196aa14f888ebcb3a04243371aca06a73d6f22b1b50b8a1ea4f27c"
        },
        {
          "matched_key_count": 47,
          "matched_key_examples": [
            "field_statuses.lower_timeframe_asof_path_availability",
            "field_statuses.lower_timeframe_asof_path_availability.reason",
            "field_statuses.lower_timeframe_asof_path_availability.requirement_id",
            "field_statuses.lower_timeframe_asof_path_availability.source_paths_searched",
            "field_statuses.lower_timeframe_asof_path_availability.source_paths_searched[]",
            "field_statuses.lower_timeframe_asof_path_availability.source_truth_class",
            "field_statuses.lower_timeframe_asof_path_availability.status",
            "field_statuses.lower_timeframe_asof_path_availability.value_summary",
            "field_statuses.lower_timeframe_asof_path_availability.value_summary.accepted_packet_interval",
            "field_statuses.lower_timeframe_asof_path_availability.value_summary.lower_timeframe_source_attached",
            "field_statuses.lower_timeframe_asof_path_availability.value_summary.prior_windows",
            "field_statuses.lower_timeframe_asof_path_availability.value_summary.prior_windows.16"
          ],
          "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/scid_strategy_field_source_expansion_packet/SCID_STRATEGY_FIELD_CANDIDATE_FIELD_CLOSURE_LEDGER_2026-05-12.jsonl",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_NOAPI_HYP_FACTORY",
          "safe_shape_fingerprint_sha256": "32eee23c4e196aa14f888ebcb3a04243371aca06a73d6f22b1b50b8a1ea4f27c"
        },
        {
          "matched_key_count": 47,
          "matched_key_examples": [
            "field_statuses.lower_timeframe_asof_path_availability",
            "field_statuses.lower_timeframe_asof_path_availability.reason",
            "field_statuses.lower_timeframe_asof_path_availability.requirement_id",
            "field_statuses.lower_timeframe_asof_path_availability.source_paths_searched",
            "field_statuses.lower_timeframe_asof_path_availability.source_paths_searched[]",
            "field_statuses.lower_timeframe_asof_path_availability.source_truth_class",
            "field_statuses.lower_timeframe_asof_path_availability.status",
            "field_statuses.lower_timeframe_asof_path_availability.value_summary",
            "field_statuses.lower_timeframe_asof_path_availability.value_summary.accepted_packet_interval",
            "field_statuses.lower_timeframe_asof_path_availability.value_summary.lower_timeframe_source_attached",
            "field_statuses.lower_timeframe_asof_path_availability.value_summary.prior_windows",
            "field_statuses.lower_timeframe_asof_path_availability.value_summary.prior_windows.16"
          ],
          "path": "C:/tmp/gtos_otb/SCID_SYNTH_HARNESS/research/science_program_2026_05/06_outcome_testing/scid_strategy_field_source_expansion_packet/SCID_STRATEGY_FIELD_CANDIDATE_FIELD_CLOSURE_LEDGER_2026-05-12.jsonl",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_SYNTH_HARNESS",
          "safe_shape_fingerprint_sha256": "32eee23c4e196aa14f888ebcb3a04243371aca06a73d6f22b1b50b8a1ea4f27c"
        },
        {
          "matched_key_count": 47,
          "matched_key_examples": [
            "field_statuses.lower_timeframe_asof_path_availability",
            "field_statuses.lower_timeframe_asof_path_availability.reason",
            "field_statuses.lower_timeframe_asof_path_availability.requirement_id",
            "field_statuses.lower_timeframe_asof_path_availability.source_paths_searched",
            "field_statuses.lower_timeframe_asof_path_availability.source_paths_searched[]",
            "field_statuses.lower_timeframe_asof_path_availability.source_truth_class",
            "field_statuses.lower_timeframe_asof_path_availability.status",
            "field_statuses.lower_timeframe_asof_path_availability.value_summary",
            "field_statuses.lower_timeframe_asof_path_availability.value_summary.accepted_packet_interval",
            "field_statuses.lower_timeframe_asof_path_availability.value_summary.lower_timeframe_source_attached",
            "field_statuses.lower_timeframe_asof_path_availability.value_summary.prior_windows",
            "field_statuses.lower_timeframe_asof_path_availability.value_summary.prior_windows.16"
          ],
          "path": "research/science_program_2026_05/06_outcome_testing/scid_strategy_field_source_expansion_packet/SCID_STRATEGY_FIELD_CANDIDATE_FIELD_CLOSURE_LEDGER_2026-05-12.jsonl",
          "root_label": "current_scid_source_control_route_artifacts",
          "safe_shape_fingerprint_sha256": "32eee23c4e196aa14f888ebcb3a04243371aca06a73d6f22b1b50b8a1ea4f27c"
        },
        {
          "matched_key_count": 42,
          "matched_key_examples": [
            "build_ltf_row",
            "candidate_ltf_path_order",
            "candidate_ltf_path_order_refresh_summary_v1",
            "candidate_ltf_path_order_v1",
            "entry_sl_same_m1_ambiguous",
            "entry_then_sl_same_m1_ambiguous",
            "entry_then_tp1_same_m1_ambiguous",
            "entry_then_tp1_sl_same_m1_ambiguous",
            "entry_touched_unresolved_by_ltf_asof",
            "entry_tp1_same_m1_ambiguous",
            "entry_tp1_sl_same_m1_ambiguous",
            "latest_ltf"
          ],
          "path": "src/research_infra/live_shadow_gap_closure.py",
          "root_label": "research_infra_keyword_shapes",
          "safe_shape_fingerprint_sha256": "deb04aaa1a9f3d274be10a8e172f9d33c9106420205c4763a48d1e385c52b2c4"
        },
        {
          "matched_key_count": 31,
          "matched_key_examples": [
            "build_m15_choch_diagnostic_row",
            "build_m15_choch_diagnostic_rows",
            "entry_touched_tp1_sl_m15_ambiguous",
            "entry_touched_tp_and_sl_m15_ambiguous",
            "is_m15_choch_failure",
            "m15",
            "m15_choch_ai_value",
            "m15_choch_audit_status",
            "m15_choch_check_detail",
            "m15_choch_check_not_captured",
            "m15_choch_check_status",
            "m15_choch_decision_diagnostic"
          ],
          "path": "src/research_infra/m15_choch_diagnostics.py",
          "root_label": "research_infra_keyword_shapes",
          "safe_shape_fingerprint_sha256": "6920c582fffcc9551afd2f88dd51d98e688cc02944b33b4bf31f59a9877d06c2"
        },
        {
          "matched_key_count": 30,
          "matched_key_examples": [
            "m15_choch_diagnostic",
            "m15_choch_diagnostic.blocked_by",
            "m15_choch_diagnostic.decision_time_only",
            "m15_choch_diagnostic.diagnostic_status",
            "m15_choch_diagnostic.displacement_ratio_ai_value",
            "m15_choch_diagnostic.displacement_ratio_check_detail",
            "m15_choch_diagnostic.displacement_ratio_check_status",
            "m15_choch_diagnostic.displacement_ratio_mso_value",
            "m15_choch_diagnostic.m15_choch_ai_value",
            "m15_choch_diagnostic.m15_choch_check_detail",
            "m15_choch_diagnostic.m15_choch_check_status",
            "m15_choch_diagnostic.m15_choch_mso_value"
          ],
          "path": "shadow_logs/strategy_follow_candidates.jsonl",
          "root_label": "shadow_logs_shape_only_non_forbidden_families",
          "safe_shape_fingerprint_sha256": "91f92c420458f71d164b7d47f0a9fc2ccc2e0788e081ad3820b805a98dd6ddfd"
        },
        {
          "matched_key_count": 27,
          "matched_key_examples": [
            "build_prefill_delivery_path_row",
            "canonical_m15_close_utc",
            "classify_ltf_ambiguity",
            "lower_tf_available",
            "lower_tf_coverage_missing_fail_closed",
            "lower_tf_coverage_window_end_utc",
            "lower_tf_coverage_window_start_utc",
            "lower_timeframe_available",
            "lower_timeframe_path_ordering",
            "m15",
            "m15_choch_decision_diagnostic",
            "m15_choch_diagnostic"
          ],
          "path": "src/research_infra/forward_capture.py",
          "root_label": "research_infra_keyword_shapes",
          "safe_shape_fingerprint_sha256": "bacdff315bfc5e9429481bd6cf9deac34958633004ed08cdb1e3e937d25a7516"
        },
        {
          "matched_key_count": 26,
          "matched_key_examples": [
            "_ltf",
            "_prefill",
            "build_prefill_delivery_path_audit_rows",
            "candidate_ltf_path_order_v1",
            "derived_from_ltf_path_order_asof",
            "lower_timeframe_path_ordering",
            "ltf_",
            "ltf_rows",
            "ltf_status",
            "m15_displacement_quality",
            "m1_path_recovered",
            "path_order_label"
          ],
          "path": "tests/test_prefill_delivery_path_audit.py",
          "root_label": "focused_tests_keyword_shapes",
          "safe_shape_fingerprint_sha256": "42de930da71f7984f89a0bf16f7bcb2cc12939cd20fa48d97694895207805cbd"
        }
      ]
    },
    {
      "as_of_rule": "source capture and derived features must be timestamped no later than decision_asof_utc unless marked forensic-only",
      "coverage_status": "SHAPE_COVERAGE_PRESENT_EXACT_CAPTURE_FIELDS_INCOMPLETE",
      "exact_capture_requirement_to_close_gap": "Add/verify future additive capture rows for derived_feature_schema_version, publication_or_capture_asof_utc, source_file_pointer_or_vendor_cache_id via orderflow_depth_proxy_context_capture; enforce source_id/source_hash/as_of/redaction/forbidden-key fail-closed checks before G12 acceptance.",
      "exact_schema_field_matches_found_by_name": [
        "orderflow_proxy_availability_status",
        "proxy_contract_month",
        "proxy_instrument",
        "proxy_mapping_version",
        "source_family_scid_depth_mbo_mbp_other"
      ],
      "existing_shape_artifact_count": 1867,
      "field_group": "future_orderflow_depth_proxy_requirements",
      "future_source_or_logger": "orderflow_depth_proxy_context_capture",
      "historical_status": "RECOVERABLE_OR_REQUESTABLE_MARKET_CONTEXT_WITH_PROXY_CONTRACT_CAPTURE_REQUIRED",
      "label": "orderflow/proxy",
      "missing_exact_schema_fields": [
        "derived_feature_schema_version",
        "publication_or_capture_asof_utc",
        "source_file_pointer_or_vendor_cache_id"
      ],
      "no_leak_rule": "no post-event orderflow, future depth state, paid-call output, or raw blob commit in this route",
      "representative_shape_artifacts": [
        {
          "matched_key_count": 138,
          "matched_key_examples": [
            "feature_availability.source_refs.databento_trigger",
            "feature_availability.source_refs.databento_trigger.backfilled_at_utc",
            "feature_availability.source_refs.databento_trigger.created_at_utc",
            "feature_availability.source_refs.databento_trigger.joined",
            "feature_availability.source_refs.databento_trigger.row_key",
            "feature_availability.source_refs.databento_trigger.schema_version",
            "feature_availability.source_refs.databento_trigger.source_line",
            "feature_availability.source_refs.orderflow_status",
            "feature_availability.source_refs.orderflow_status.backfilled_at_utc",
            "feature_availability.source_refs.orderflow_status.created_at_utc",
            "feature_availability.source_refs.orderflow_status.joined",
            "feature_availability.source_refs.orderflow_status.row_key"
          ],
          "path": "shadow_logs/ml_shadow_predictions.jsonl",
          "root_label": "shadow_logs_shape_only_non_forbidden_families",
          "safe_shape_fingerprint_sha256": "9bb0509929154d071d7b3150c50bd1a6612d18ba5c81688c62a5db1f6a2d0b61"
        },
        {
          "matched_key_count": 98,
          "matched_key_examples": [
            "accept_as_source_control_scid_asof_contract_only",
            "accepted_9_scid_segments",
            "accepted_g12_scid_repair_reaudit_completion",
            "accepted_g12_scid_repair_reaudit_decision",
            "accepted_g12_scid_repair_reaudit_noleak",
            "accepted_g12_scid_repair_reaudit_source_rehash",
            "allowed_scid_record_fields",
            "as_of_bid_ask_volume_from_scid_record",
            "ask",
            "ask_volume",
            "bid",
            "bid_volume"
          ],
          "path": "C:/Users/MSI/Documents/ai-trading-agent/research/science_program_2026_05/06_outcome_testing/scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint/build_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_2026_05_11.py",
          "root_label": "original_local_repo_scid_route_artifact_shapes::ai-trading-agent",
          "safe_shape_fingerprint_sha256": "65bbabc92b12e40720d841a8216df87b9f6f21a2ae368b483e186a3f643fa909"
        },
        {
          "matched_key_count": 98,
          "matched_key_examples": [
            "accept_as_source_control_scid_asof_contract_only",
            "accepted_9_scid_segments",
            "accepted_g12_scid_repair_reaudit_completion",
            "accepted_g12_scid_repair_reaudit_decision",
            "accepted_g12_scid_repair_reaudit_noleak",
            "accepted_g12_scid_repair_reaudit_source_rehash",
            "allowed_scid_record_fields",
            "as_of_bid_ask_volume_from_scid_record",
            "ask",
            "ask_volume",
            "bid",
            "bid_volume"
          ],
          "path": "C:/tmp/gtos_otb/SCID_IMPL_DESIGN/research/science_program_2026_05/06_outcome_testing/scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint/build_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_2026_05_11.py",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_IMPL_DESIGN",
          "safe_shape_fingerprint_sha256": "65bbabc92b12e40720d841a8216df87b9f6f21a2ae368b483e186a3f643fa909"
        },
        {
          "matched_key_count": 98,
          "matched_key_examples": [
            "accept_as_source_control_scid_asof_contract_only",
            "accepted_9_scid_segments",
            "accepted_g12_scid_repair_reaudit_completion",
            "accepted_g12_scid_repair_reaudit_decision",
            "accepted_g12_scid_repair_reaudit_noleak",
            "accepted_g12_scid_repair_reaudit_source_rehash",
            "allowed_scid_record_fields",
            "as_of_bid_ask_volume_from_scid_record",
            "ask",
            "ask_volume",
            "bid",
            "bid_volume"
          ],
          "path": "C:/tmp/gtos_otb/SCID_LTF_OF_EXPANSION/research/science_program_2026_05/06_outcome_testing/scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint/build_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_2026_05_11.py",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_LTF_OF_EXPANSION",
          "safe_shape_fingerprint_sha256": "65bbabc92b12e40720d841a8216df87b9f6f21a2ae368b483e186a3f643fa909"
        },
        {
          "matched_key_count": 98,
          "matched_key_examples": [
            "accept_as_source_control_scid_asof_contract_only",
            "accepted_9_scid_segments",
            "accepted_g12_scid_repair_reaudit_completion",
            "accepted_g12_scid_repair_reaudit_decision",
            "accepted_g12_scid_repair_reaudit_noleak",
            "accepted_g12_scid_repair_reaudit_source_rehash",
            "allowed_scid_record_fields",
            "as_of_bid_ask_volume_from_scid_record",
            "ask",
            "ask_volume",
            "bid",
            "bid_volume"
          ],
          "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint/build_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_2026_05_11.py",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_NOAPI_HYP_FACTORY",
          "safe_shape_fingerprint_sha256": "65bbabc92b12e40720d841a8216df87b9f6f21a2ae368b483e186a3f643fa909"
        },
        {
          "matched_key_count": 98,
          "matched_key_examples": [
            "accept_as_source_control_scid_asof_contract_only",
            "accepted_9_scid_segments",
            "accepted_g12_scid_repair_reaudit_completion",
            "accepted_g12_scid_repair_reaudit_decision",
            "accepted_g12_scid_repair_reaudit_noleak",
            "accepted_g12_scid_repair_reaudit_source_rehash",
            "allowed_scid_record_fields",
            "as_of_bid_ask_volume_from_scid_record",
            "ask",
            "ask_volume",
            "bid",
            "bid_volume"
          ],
          "path": "C:/tmp/gtos_otb/SCID_SYNTH_HARNESS/research/science_program_2026_05/06_outcome_testing/scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint/build_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_2026_05_11.py",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_SYNTH_HARNESS",
          "safe_shape_fingerprint_sha256": "65bbabc92b12e40720d841a8216df87b9f6f21a2ae368b483e186a3f643fa909"
        },
        {
          "matched_key_count": 98,
          "matched_key_examples": [
            "accept_as_source_control_scid_asof_contract_only",
            "accepted_9_scid_segments",
            "accepted_g12_scid_repair_reaudit_completion",
            "accepted_g12_scid_repair_reaudit_decision",
            "accepted_g12_scid_repair_reaudit_noleak",
            "accepted_g12_scid_repair_reaudit_source_rehash",
            "allowed_scid_record_fields",
            "as_of_bid_ask_volume_from_scid_record",
            "ask",
            "ask_volume",
            "bid",
            "bid_volume"
          ],
          "path": "research/science_program_2026_05/06_outcome_testing/scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint/build_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_2026_05_11.py",
          "root_label": "current_scid_source_control_route_artifacts",
          "safe_shape_fingerprint_sha256": "65bbabc92b12e40720d841a8216df87b9f6f21a2ae368b483e186a3f643fa909"
        },
        {
          "matched_key_count": 94,
          "matched_key_examples": [
            "accept_as_g12_scid_forward_capture_offline_schema_implementation_package_control_evidence_only",
            "baseline_family_session_only_volatility_only_random_proxy_matched",
            "build_scid_forward_capture_offline_schema_implementation_package_2026_05_12",
            "builder_unique_duplicate_proxy_denominator_keys",
            "built_scid_forward_capture_offline_schema_package_g12_audit_required",
            "candidate_input_row_id_plus_duplicate_proxy_denominator_key_v1",
            "databento_live_trigger_decisions",
            "depth",
            "duplicate_proxy_denominator_key",
            "duplicate_proxy_denominator_key_coverage_expectation",
            "forbidden",
            "forbidden_fail_closed"
          ],
          "path": "C:/Users/MSI/Documents/ai-trading-agent/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/build_scid_forward_capture_offline_schema_implementation_package_2026_05_12.py",
          "root_label": "original_local_repo_scid_route_artifact_shapes::ai-trading-agent",
          "safe_shape_fingerprint_sha256": "2c971e6356e9178e94dcdc43a6a49f0cd5fa8d69c6586f521f28b0c71c3dde3d"
        },
        {
          "matched_key_count": 94,
          "matched_key_examples": [
            "accept_as_g12_scid_forward_capture_offline_schema_implementation_package_control_evidence_only",
            "baseline_family_session_only_volatility_only_random_proxy_matched",
            "build_scid_forward_capture_offline_schema_implementation_package_2026_05_12",
            "builder_unique_duplicate_proxy_denominator_keys",
            "built_scid_forward_capture_offline_schema_package_g12_audit_required",
            "candidate_input_row_id_plus_duplicate_proxy_denominator_key_v1",
            "databento_live_trigger_decisions",
            "depth",
            "duplicate_proxy_denominator_key",
            "duplicate_proxy_denominator_key_coverage_expectation",
            "forbidden",
            "forbidden_fail_closed"
          ],
          "path": "C:/tmp/gtos_otb/SCID_IMPL_DESIGN/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/build_scid_forward_capture_offline_schema_implementation_package_2026_05_12.py",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_IMPL_DESIGN",
          "safe_shape_fingerprint_sha256": "2c971e6356e9178e94dcdc43a6a49f0cd5fa8d69c6586f521f28b0c71c3dde3d"
        },
        {
          "matched_key_count": 94,
          "matched_key_examples": [
            "accept_as_g12_scid_forward_capture_offline_schema_implementation_package_control_evidence_only",
            "baseline_family_session_only_volatility_only_random_proxy_matched",
            "build_scid_forward_capture_offline_schema_implementation_package_2026_05_12",
            "builder_unique_duplicate_proxy_denominator_keys",
            "built_scid_forward_capture_offline_schema_package_g12_audit_required",
            "candidate_input_row_id_plus_duplicate_proxy_denominator_key_v1",
            "databento_live_trigger_decisions",
            "depth",
            "duplicate_proxy_denominator_key",
            "duplicate_proxy_denominator_key_coverage_expectation",
            "forbidden",
            "forbidden_fail_closed"
          ],
          "path": "C:/tmp/gtos_otb/SCID_LTF_OF_EXPANSION/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/build_scid_forward_capture_offline_schema_implementation_package_2026_05_12.py",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_LTF_OF_EXPANSION",
          "safe_shape_fingerprint_sha256": "2c971e6356e9178e94dcdc43a6a49f0cd5fa8d69c6586f521f28b0c71c3dde3d"
        },
        {
          "matched_key_count": 94,
          "matched_key_examples": [
            "accept_as_g12_scid_forward_capture_offline_schema_implementation_package_control_evidence_only",
            "baseline_family_session_only_volatility_only_random_proxy_matched",
            "build_scid_forward_capture_offline_schema_implementation_package_2026_05_12",
            "builder_unique_duplicate_proxy_denominator_keys",
            "built_scid_forward_capture_offline_schema_package_g12_audit_required",
            "candidate_input_row_id_plus_duplicate_proxy_denominator_key_v1",
            "databento_live_trigger_decisions",
            "depth",
            "duplicate_proxy_denominator_key",
            "duplicate_proxy_denominator_key_coverage_expectation",
            "forbidden",
            "forbidden_fail_closed"
          ],
          "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/build_scid_forward_capture_offline_schema_implementation_package_2026_05_12.py",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_NOAPI_HYP_FACTORY",
          "safe_shape_fingerprint_sha256": "2c971e6356e9178e94dcdc43a6a49f0cd5fa8d69c6586f521f28b0c71c3dde3d"
        },
        {
          "matched_key_count": 94,
          "matched_key_examples": [
            "accept_as_g12_scid_forward_capture_offline_schema_implementation_package_control_evidence_only",
            "baseline_family_session_only_volatility_only_random_proxy_matched",
            "build_scid_forward_capture_offline_schema_implementation_package_2026_05_12",
            "builder_unique_duplicate_proxy_denominator_keys",
            "built_scid_forward_capture_offline_schema_package_g12_audit_required",
            "candidate_input_row_id_plus_duplicate_proxy_denominator_key_v1",
            "databento_live_trigger_decisions",
            "depth",
            "duplicate_proxy_denominator_key",
            "duplicate_proxy_denominator_key_coverage_expectation",
            "forbidden",
            "forbidden_fail_closed"
          ],
          "path": "C:/tmp/gtos_otb/SCID_SYNTH_HARNESS/research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/build_scid_forward_capture_offline_schema_implementation_package_2026_05_12.py",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_SYNTH_HARNESS",
          "safe_shape_fingerprint_sha256": "2c971e6356e9178e94dcdc43a6a49f0cd5fa8d69c6586f521f28b0c71c3dde3d"
        }
      ]
    },
    {
      "as_of_rule": "baseline assignment may use only closed source-control descriptors and frozen deterministic seed before result opening",
      "coverage_status": "SHAPE_COVERAGE_PRESENT_EXACT_CAPTURE_FIELDS_PRESENT_IN_INSPECTED_SHAPES",
      "exact_capture_requirement_to_close_gap": "Add/verify future additive capture rows for partition_assignment, symbol, session_bucket, time_of_day_bucket, baseline_family_session_only_volatility_only_random_proxy_matched, baseline_assignment_seed, baseline_duplicate_policy_id via offline_baseline_control_assignment_manifest; enforce source_id/source_hash/as_of/redaction/forbidden-key fail-closed checks before G12 acceptance.",
      "exact_schema_field_matches_found_by_name": [
        "baseline_assignment_seed",
        "baseline_duplicate_policy_id",
        "baseline_family_session_only_volatility_only_random_proxy_matched",
        "partition_assignment",
        "session_bucket",
        "symbol",
        "time_of_day_bucket"
      ],
      "existing_shape_artifact_count": 1399,
      "field_group": "baseline_control_fields",
      "future_source_or_logger": "offline_baseline_control_assignment_manifest",
      "historical_status": "CONTROL_CONTRACT_FROZEN_FROM_CLOSED_DESCRIPTOR_FIELDS",
      "label": "baseline-control",
      "missing_exact_schema_fields": [],
      "no_leak_rule": "baseline fields cannot use target status, realized result, future path, or performance-selected thresholds",
      "representative_shape_artifacts": [
        {
          "matched_key_count": 105,
          "matched_key_examples": [
            "_adversarial_baseline_and_robustness_plan_",
            "_duplicate_proxy_denominator_rules_",
            "_row_partition_ledger_",
            "accept_as_source_control_scid_asof_candidate_input_packet_only",
            "accepted_source_control_packet_only",
            "adversarial_baseline_and_robustness_plan",
            "adversarial_baseline_and_robustness_planning",
            "adversarial_baseline_ids",
            "adversarial_baselines",
            "baseline",
            "baseline_count",
            "baseline_mean_reversion"
          ],
          "path": "C:/Users/MSI/Documents/ai-trading-agent/research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/build_g0_scid_asof_synthesis_validation_design_2026_05_11.py",
          "root_label": "original_local_repo_scid_route_artifact_shapes::ai-trading-agent",
          "safe_shape_fingerprint_sha256": "a685fb5caefd6a88624b52f6449e4265de8b35f5fe54e3013289b0826a4bdc2b"
        },
        {
          "matched_key_count": 105,
          "matched_key_examples": [
            "_adversarial_baseline_and_robustness_plan_",
            "_duplicate_proxy_denominator_rules_",
            "_row_partition_ledger_",
            "accept_as_source_control_scid_asof_candidate_input_packet_only",
            "accepted_source_control_packet_only",
            "adversarial_baseline_and_robustness_plan",
            "adversarial_baseline_and_robustness_planning",
            "adversarial_baseline_ids",
            "adversarial_baselines",
            "baseline",
            "baseline_count",
            "baseline_mean_reversion"
          ],
          "path": "C:/tmp/gtos_otb/SCID_IMPL_DESIGN/research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/build_g0_scid_asof_synthesis_validation_design_2026_05_11.py",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_IMPL_DESIGN",
          "safe_shape_fingerprint_sha256": "a685fb5caefd6a88624b52f6449e4265de8b35f5fe54e3013289b0826a4bdc2b"
        },
        {
          "matched_key_count": 105,
          "matched_key_examples": [
            "_adversarial_baseline_and_robustness_plan_",
            "_duplicate_proxy_denominator_rules_",
            "_row_partition_ledger_",
            "accept_as_source_control_scid_asof_candidate_input_packet_only",
            "accepted_source_control_packet_only",
            "adversarial_baseline_and_robustness_plan",
            "adversarial_baseline_and_robustness_planning",
            "adversarial_baseline_ids",
            "adversarial_baselines",
            "baseline",
            "baseline_count",
            "baseline_mean_reversion"
          ],
          "path": "C:/tmp/gtos_otb/SCID_LTF_OF_EXPANSION/research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/build_g0_scid_asof_synthesis_validation_design_2026_05_11.py",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_LTF_OF_EXPANSION",
          "safe_shape_fingerprint_sha256": "a685fb5caefd6a88624b52f6449e4265de8b35f5fe54e3013289b0826a4bdc2b"
        },
        {
          "matched_key_count": 105,
          "matched_key_examples": [
            "_adversarial_baseline_and_robustness_plan_",
            "_duplicate_proxy_denominator_rules_",
            "_row_partition_ledger_",
            "accept_as_source_control_scid_asof_candidate_input_packet_only",
            "accepted_source_control_packet_only",
            "adversarial_baseline_and_robustness_plan",
            "adversarial_baseline_and_robustness_planning",
            "adversarial_baseline_ids",
            "adversarial_baselines",
            "baseline",
            "baseline_count",
            "baseline_mean_reversion"
          ],
          "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/build_g0_scid_asof_synthesis_validation_design_2026_05_11.py",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_NOAPI_HYP_FACTORY",
          "safe_shape_fingerprint_sha256": "a685fb5caefd6a88624b52f6449e4265de8b35f5fe54e3013289b0826a4bdc2b"
        },
        {
          "matched_key_count": 105,
          "matched_key_examples": [
            "_adversarial_baseline_and_robustness_plan_",
            "_duplicate_proxy_denominator_rules_",
            "_row_partition_ledger_",
            "accept_as_source_control_scid_asof_candidate_input_packet_only",
            "accepted_source_control_packet_only",
            "adversarial_baseline_and_robustness_plan",
            "adversarial_baseline_and_robustness_planning",
            "adversarial_baseline_ids",
            "adversarial_baselines",
            "baseline",
            "baseline_count",
            "baseline_mean_reversion"
          ],
          "path": "C:/tmp/gtos_otb/SCID_SYNTH_HARNESS/research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/build_g0_scid_asof_synthesis_validation_design_2026_05_11.py",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_SYNTH_HARNESS",
          "safe_shape_fingerprint_sha256": "a685fb5caefd6a88624b52f6449e4265de8b35f5fe54e3013289b0826a4bdc2b"
        },
        {
          "matched_key_count": 105,
          "matched_key_examples": [
            "_adversarial_baseline_and_robustness_plan_",
            "_duplicate_proxy_denominator_rules_",
            "_row_partition_ledger_",
            "accept_as_source_control_scid_asof_candidate_input_packet_only",
            "accepted_source_control_packet_only",
            "adversarial_baseline_and_robustness_plan",
            "adversarial_baseline_and_robustness_planning",
            "adversarial_baseline_ids",
            "adversarial_baselines",
            "baseline",
            "baseline_count",
            "baseline_mean_reversion"
          ],
          "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/build_g0_scid_asof_synthesis_validation_design_2026_05_11.py",
          "root_label": "current_scid_source_control_route_artifacts",
          "safe_shape_fingerprint_sha256": "a685fb5caefd6a88624b52f6449e4265de8b35f5fe54e3013289b0826a4bdc2b"
        },
        {
          "matched_key_count": 74,
          "matched_key_examples": [
            "accept_as_source_control_scid_asof_contract_only",
            "adversarial_baseline_ids",
            "adversarial_baseline_source_ref",
            "all_four_baselines_exact",
            "all_four_baselines_frozen",
            "bar_duplicate_key",
            "baseline",
            "baseline_controls",
            "baseline_count",
            "baseline_ids",
            "baseline_mean_reversion",
            "baseline_momentum_continuation"
          ],
          "path": "C:/Users/MSI/Documents/ai-trading-agent/research/science_program_2026_05/06_outcome_testing/scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint/build_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_2026_05_11.py",
          "root_label": "original_local_repo_scid_route_artifact_shapes::ai-trading-agent",
          "safe_shape_fingerprint_sha256": "65bbabc92b12e40720d841a8216df87b9f6f21a2ae368b483e186a3f643fa909"
        },
        {
          "matched_key_count": 74,
          "matched_key_examples": [
            "accept_as_source_control_scid_asof_contract_only",
            "adversarial_baseline_ids",
            "adversarial_baseline_source_ref",
            "all_four_baselines_exact",
            "all_four_baselines_frozen",
            "bar_duplicate_key",
            "baseline",
            "baseline_controls",
            "baseline_count",
            "baseline_ids",
            "baseline_mean_reversion",
            "baseline_momentum_continuation"
          ],
          "path": "C:/tmp/gtos_otb/SCID_IMPL_DESIGN/research/science_program_2026_05/06_outcome_testing/scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint/build_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_2026_05_11.py",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_IMPL_DESIGN",
          "safe_shape_fingerprint_sha256": "65bbabc92b12e40720d841a8216df87b9f6f21a2ae368b483e186a3f643fa909"
        },
        {
          "matched_key_count": 74,
          "matched_key_examples": [
            "accept_as_source_control_scid_asof_contract_only",
            "adversarial_baseline_ids",
            "adversarial_baseline_source_ref",
            "all_four_baselines_exact",
            "all_four_baselines_frozen",
            "bar_duplicate_key",
            "baseline",
            "baseline_controls",
            "baseline_count",
            "baseline_ids",
            "baseline_mean_reversion",
            "baseline_momentum_continuation"
          ],
          "path": "C:/tmp/gtos_otb/SCID_LTF_OF_EXPANSION/research/science_program_2026_05/06_outcome_testing/scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint/build_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_2026_05_11.py",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_LTF_OF_EXPANSION",
          "safe_shape_fingerprint_sha256": "65bbabc92b12e40720d841a8216df87b9f6f21a2ae368b483e186a3f643fa909"
        },
        {
          "matched_key_count": 74,
          "matched_key_examples": [
            "accept_as_source_control_scid_asof_contract_only",
            "adversarial_baseline_ids",
            "adversarial_baseline_source_ref",
            "all_four_baselines_exact",
            "all_four_baselines_frozen",
            "bar_duplicate_key",
            "baseline",
            "baseline_controls",
            "baseline_count",
            "baseline_ids",
            "baseline_mean_reversion",
            "baseline_momentum_continuation"
          ],
          "path": "C:/tmp/gtos_otb/SCID_NOAPI_HYP_FACTORY/research/science_program_2026_05/06_outcome_testing/scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint/build_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_2026_05_11.py",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_NOAPI_HYP_FACTORY",
          "safe_shape_fingerprint_sha256": "65bbabc92b12e40720d841a8216df87b9f6f21a2ae368b483e186a3f643fa909"
        },
        {
          "matched_key_count": 74,
          "matched_key_examples": [
            "accept_as_source_control_scid_asof_contract_only",
            "adversarial_baseline_ids",
            "adversarial_baseline_source_ref",
            "all_four_baselines_exact",
            "all_four_baselines_frozen",
            "bar_duplicate_key",
            "baseline",
            "baseline_controls",
            "baseline_count",
            "baseline_ids",
            "baseline_mean_reversion",
            "baseline_momentum_continuation"
          ],
          "path": "C:/tmp/gtos_otb/SCID_SYNTH_HARNESS/research/science_program_2026_05/06_outcome_testing/scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint/build_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_2026_05_11.py",
          "root_label": "prior_worktree_scid_route_artifact_shapes::SCID_SYNTH_HARNESS",
          "safe_shape_fingerprint_sha256": "65bbabc92b12e40720d841a8216df87b9f6f21a2ae368b483e186a3f643fa909"
        },
        {
          "matched_key_count": 74,
          "matched_key_examples": [
            "accept_as_source_control_scid_asof_contract_only",
            "adversarial_baseline_ids",
            "adversarial_baseline_source_ref",
            "all_four_baselines_exact",
            "all_four_baselines_frozen",
            "bar_duplicate_key",
            "baseline",
            "baseline_controls",
            "baseline_count",
            "baseline_ids",
            "baseline_mean_reversion",
            "baseline_momentum_continuation"
          ],
          "path": "research/science_program_2026_05/06_outcome_testing/scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint/build_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_2026_05_11.py",
          "root_label": "current_scid_source_control_route_artifacts",
          "safe_shape_fingerprint_sha256": "65bbabc92b12e40720d841a8216df87b9f6f21a2ae368b483e186a3f643fa909"
        }
      ]
    }
  ],
  "credentials_touched": false,
  "evidence_class": "SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_ONLY",
  "generated_at_utc": "2026-05-12T05:26:39Z",
  "groups_requiring_exact_additive_capture_fields": [
    "intended_target_reference",
    "poi_type_bounds_source",
    "lifecycle_fill_cancel_expiry_source_status",
    "lower_timeframe_asof_path_availability",
    "future_orderflow_depth_proxy_requirements"
  ],
  "groups_with_no_shape_coverage": [],
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
  "route_id": "SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION",
  "schema_version": "scid_forward_capture_readonly_alignment_expansion_v1",
  "validation_safe": false
}
```
