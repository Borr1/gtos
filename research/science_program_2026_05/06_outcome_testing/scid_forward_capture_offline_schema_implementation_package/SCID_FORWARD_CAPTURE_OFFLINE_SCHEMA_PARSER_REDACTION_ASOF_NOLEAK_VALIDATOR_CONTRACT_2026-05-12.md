# Parser Redaction As-Of No-Leak Validator Contract

- **route_id:** `SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE`
- **evidence_class:** `SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "artifact_family": "parser_redaction_asof_noleak_validator_contract",
  "asof_contract": {
    "common_check": "source_observed_asof_utc must be <= decision_asof_utc for decision-source and market-context rows",
    "lifecycle_note": "lifecycle events are append-only source-state rows and remain forbidden from broker/account/order-history evidence in this route"
  },
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "downstream_g12_acceptance_rule": "G12 must rerun row coverage, schema, fixture, hash, as-of, forbidden-surface, read-only alignment, and manifest repair checks before accepting this package.",
  "evidence_class": "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_ONLY",
  "field_group_contracts": {
    "baseline_control_fields": {
      "as_of_rule": "baseline assignment may use only closed source-control descriptors and frozen deterministic seed before result opening",
      "fields": [
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "partition_assignment",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "symbol",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "session_bucket",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "time_of_day_bucket",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [
            "session_only",
            "volatility_only",
            "random_proxy_matched"
          ],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "baseline_family_session_only_volatility_only_random_proxy_matched",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "baseline_assignment_seed",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "baseline_duplicate_policy_id",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        }
      ],
      "future_source_or_logger": "offline_baseline_control_assignment_manifest",
      "historical_status": "CONTROL_CONTRACT_FROZEN_FROM_CLOSED_DESCRIPTOR_FIELDS",
      "no_leak_rule": "baseline fields cannot use target status, realized result, future path, or performance-selected thresholds"
    },
    "framework_setup_family": {
      "as_of_rule": "framework selection/evaluation must be logged before L2, fill, or path result fields are known",
      "fields": [
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "frameworks_evaluated",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "array_string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "framework_qualified_flags",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "object"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "selected_framework_or_none",
          "nullable": true,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "setup_family",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "framework_tiebreak_rule_id",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "framework_source_snapshot_hash",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        }
      ],
      "future_source_or_logger": "source_safe_strategy_decision_packet_logger",
      "historical_status": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
      "no_leak_rule": "framework cannot be assigned from later path shape or favorable outcome family"
    },
    "future_orderflow_depth_proxy_requirements": {
      "as_of_rule": "source capture and derived features must be timestamped no later than decision_asof_utc unless marked forensic-only",
      "fields": [
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "proxy_instrument",
          "nullable": true,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "proxy_contract_month",
          "nullable": true,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [
            "scid",
            "depth",
            "mbo",
            "mbp",
            "other",
            "unavailable"
          ],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "source_family_scid_depth_mbo_mbp_other",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "source_file_pointer_or_vendor_cache_id",
          "nullable": true,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "proxy_mapping_version",
          "nullable": true,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "publication_or_capture_asof_utc",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "timestamp"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "derived_feature_schema_version",
          "nullable": true,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [
            "AVAILABLE",
            "UNAVAILABLE_FAIL_CLOSED"
          ],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "orderflow_proxy_availability_status",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        }
      ],
      "future_source_or_logger": "orderflow_depth_proxy_context_capture",
      "historical_status": "RECOVERABLE_OR_REQUESTABLE_MARKET_CONTEXT_WITH_PROXY_CONTRACT_CAPTURE_REQUIRED",
      "no_leak_rule": "no post-event orderflow, future depth state, paid-call output, or raw blob commit in this route"
    },
    "intended_entry_reference": {
      "as_of_rule": "entry reference must be present before fill, cancel, expiry, or target horizon is known",
      "fields": [
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [
            "market",
            "limit",
            "zone_midpoint",
            "other"
          ],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "entry_reference_type_market_limit_zone_midpoint_other",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "entry_reference_price",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "number"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "entry_reference_time_utc",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "timestamp"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "entry_source_timeframe",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "entry_source_bar_hash_or_mso_snapshot_hash",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        }
      ],
      "future_source_or_logger": "source_safe_strategy_decision_packet_logger",
      "historical_status": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
      "no_leak_rule": "no fill-derived or hindsight-optimized entry references"
    },
    "intended_side_direction": {
      "as_of_rule": "side must be emitted at or before decision_asof_utc and before any target/path/result horizon is opened",
      "fields": [
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [
            "LONG",
            "SHORT",
            "NEUTRAL",
            "NO_STRATEGY"
          ],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "strategy_side_enum_LONG_SHORT_NEUTRAL_NO_STRATEGY",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "side_source_component",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "side_source_rule_or_model_hash",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "side_emission_reason_code",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        }
      ],
      "future_source_or_logger": "source_safe_strategy_decision_packet_logger",
      "historical_status": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
      "no_leak_rule": "do not derive side from post-decision price movement, terminal target status, broker result, or future path labels"
    },
    "intended_stop_reference": {
      "as_of_rule": "stop reference must be emitted with the source decision packet and frozen before path/result opening",
      "fields": [
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "stop_reference_price",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "number"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "stop_reference_type",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "stop_buffer_rule_id",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "stop_source_structure_id",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "stop_source_snapshot_hash",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        }
      ],
      "future_source_or_logger": "source_safe_strategy_decision_packet_logger",
      "historical_status": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
      "no_leak_rule": "stop cannot be fitted to later adverse excursion, target status, realized R, or broker close state"
    },
    "intended_target_reference": {
      "as_of_rule": "target reference must be frozen at decision time; neutral target horizons are not strategy targets",
      "fields": [
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "target_reference_price",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "number"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "target_reference_type",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "target_rule_id",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "risk_reward_reference",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "number"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "target_source_snapshot_hash",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        }
      ],
      "future_source_or_logger": "source_safe_strategy_decision_packet_logger",
      "historical_status": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
      "no_leak_rule": "do not create targets from terminal status, later high/low, realized R, or selected performance"
    },
    "lifecycle_fill_cancel_expiry_source_status": {
      "as_of_rule": "lifecycle events must be append-only and timestamped when GTOS observes or changes intent state",
      "fields": [
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "pending_intent_id",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [
            "created",
            "updated",
            "expired",
            "cancelled",
            "replaced",
            "no_order"
          ],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "source_event_type_created_updated_expired_cancelled_replaced_no_order",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "source_event_utc",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "timestamp"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "source_event_clock_basis",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "intent_state_before",
          "nullable": true,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "intent_state_after",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "redacted_order_bridge_hash_optional",
          "nullable": true,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        }
      ],
      "future_source_or_logger": "nonbroker_pending_intent_lifecycle_event_logger",
      "historical_status": "NON_GENERATABLE_HISTORICAL_LIFECYCLE_SOURCE_TRUTH_CAPTURE_REQUIRED",
      "no_leak_rule": "do not use broker account history, deal/position/order history, realized result, or later path labels"
    },
    "lower_timeframe_asof_path_availability": {
      "as_of_rule": "only bars/ticks with timestamps <= decision_asof_utc may be used for availability or descriptor fields",
      "fields": [
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "ltf_timeframes_available",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "array_string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "ltf_source_file_pointer_or_cache_id",
          "nullable": true,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "ltf_source_hash",
          "nullable": true,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "decision_minus_window_start_utc",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "timestamp"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "bars_present_by_timeframe",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "object"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "asof_path_descriptor_version",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [
            "AVAILABLE",
            "UNAVAILABLE_FAIL_CLOSED"
          ],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "ltf_availability_status",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        }
      ],
      "future_source_or_logger": "ltf_source_availability_and_path_descriptor_capture",
      "historical_status": "RECOVERABLE_MARKET_CONTEXT_BUT_NOT_ATTACHED_TO_ACCEPTED_CANDIDATES_CAPTURE_REQUIRED",
      "no_leak_rule": "availability/path descriptors cannot include post-decision target/stop/fill status"
    },
    "poi_type_bounds_source": {
      "as_of_rule": "POI bounds must come from the as-of market-state snapshot used by the decision packet",
      "fields": [
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [
            "ob",
            "fvg",
            "breaker",
            "swing",
            "other",
            "none"
          ],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "poi_type_enum_ob_fvg_breaker_swing_other_none",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "poi_lower_bound",
          "nullable": true,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "number"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "poi_upper_bound",
          "nullable": true,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "number"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "poi_source_timeframe",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "poi_source_bar_ids",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "array_string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "mso_snapshot_hash",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        },
        {
          "as_of_semantics": "source-safe field captured under group-specific as-of rule",
          "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
          "enum": [],
          "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
          "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
          "name": "poi_detection_rule_version",
          "nullable": false,
          "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
          "source_hash_or_deferral_policy_required": true,
          "source_identifier_required": true,
          "type": "string"
        }
      ],
      "future_source_or_logger": "source_safe_mso_snapshot_and_poi_logger",
      "historical_status": "NON_GENERATABLE_HISTORICAL_STRUCTURE_SOURCE_STATE_CAPTURE_REQUIRED",
      "no_leak_rule": "do not reconstruct POI from later price movement or result-selection logic"
    }
  },
  "generated_at_utc": "2026-05-12T03:20:54Z",
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
  "parser_contract": {
    "candidate_key_policy": "candidate_input_row_id and duplicate_proxy_denominator_key are required on every capture group row",
    "duplicate_policy": "all rows with the same candidate_input_row_id must carry the same duplicate_proxy_denominator_key",
    "fail_closed_policy": "missing required fields, stale as-of timestamps, forbidden identifiers, unsafe flags, bad enums, and duplicate-key drift fail closed",
    "input_format": "append-only JSONL rows or fixture JSON rows under scid_forward_source_capture_v1",
    "schema_version_check": "required exact match to scid_forward_source_capture_v1",
    "source_hash_policy": "STRICT_SHA256_REQUIRED unless the field is explicitly unavailable and fail-closed under HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED"
  },
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "redaction_contract": {
    "allowed_identifier_policy": "source-local event ids or redacted/salted hashes only; raw broker account/order/deal/position identifiers forbidden",
    "forbidden_values": [
      "account_history",
      "account_id",
      "account_pnl",
      "balance",
      "broker_actual_r",
      "broker_order_id",
      "deal",
      "deal_id",
      "expectancy",
      "mt5_deal_id",
      "mt5_order_ticket",
      "mt5_position_id",
      "order_id",
      "pnl",
      "position_id",
      "profit",
      "r_multiple",
      "realized_r",
      "terminal_target_status",
      "ticket",
      "win_rate"
    ],
    "policy_id": "SCID_FORWARD_CAPTURE_NO_BROKER_ACCOUNT_ORDER_DEAL_POSITION_IDS_V1"
  },
  "route_id": "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE",
  "schema_version": "scid_forward_capture_offline_schema_package_v1",
  "validation_safe": false
}
```
