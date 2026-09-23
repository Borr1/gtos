# Future No-API Replay Route Bundle

- **route_id:** `SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS`
- **evidence_class:** `SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "artifact_family": "future_no_api_replay_route_bundle",
  "bundle_boundary": "recommendations only; no replay execution, scoring, validation, or promotion",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY",
  "generated_at_utc": "2026-05-12T05:31:11Z",
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
  "route_count": 5,
  "route_id": "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS",
  "routes": [
    {
      "card_ids": [
        "HAZ-001",
        "HAZ-005",
        "BEH-001",
        "MAC-001",
        "MAC-004",
        "UNC-004",
        "ADV-001",
        "ADV-003"
      ],
      "no_api": true,
      "purpose": "Freeze accepted-descriptor-only questions now without opening results.",
      "rank": 1,
      "required_inputs": [
        "candidate_input_row_id",
        "duplicate_proxy_denominator_key",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons",
        "baseline_control_fields.partition_assignment",
        "baseline_control_fields.symbol",
        "baseline_control_fields.session_bucket",
        "baseline_control_fields.time_of_day_bucket",
        "baseline_control_fields.baseline_family_session_only_volatility_only_random_proxy_matched",
        "baseline_control_fields.baseline_assignment_seed",
        "baseline_control_fields.baseline_duplicate_policy_id"
      ],
      "result_opening_allowed": false,
      "route_id": "SCID_DESCRIPTOR_ONLY_PREREGISTRATION_CONTROL_ROUTE"
    },
    {
      "card_ids": [
        "GEO-001",
        "GEO-005",
        "HAZ-002",
        "BEH-002",
        "BEH-003",
        "BEH-004",
        "BEH-005",
        "MAC-002",
        "MAC-005",
        "EXE-002",
        "EXE-004",
        "UNC-002",
        "UNC-003",
        "ADV-004",
        "ADV-005"
      ],
      "no_api": true,
      "purpose": "Materialize future side/entry/stop/target/POI/framework/lifecycle fields for no-API replay.",
      "rank": 2,
      "required_inputs": [
        "intended_side_direction",
        "intended_entry_reference",
        "intended_stop_reference",
        "intended_target_reference",
        "poi_type_bounds_source",
        "framework_setup_family",
        "lifecycle_fill_cancel_expiry_source_status"
      ],
      "result_opening_allowed": false,
      "route_id": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE"
    },
    {
      "card_ids": [
        "GEO-002",
        "GEO-003",
        "GEO-004",
        "HAZ-003",
        "HAZ-004",
        "MIC-001",
        "MIC-002",
        "MIC-003",
        "MIC-004",
        "MIC-005",
        "MAC-003",
        "EXE-001",
        "EXE-003",
        "EXE-005",
        "UNC-001",
        "UNC-005",
        "ADV-002"
      ],
      "no_api": true,
      "purpose": "Attach LTF, SCID/depth/proxy context under source-hash and as-of controls.",
      "rank": 3,
      "required_inputs": [
        "lower_timeframe_asof_path_availability",
        "future_orderflow_depth_proxy_requirements"
      ],
      "result_opening_allowed": false,
      "route_id": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION"
    },
    {
      "card_ids": [
        "ADV-001",
        "ADV-002",
        "ADV-003",
        "ADV-004",
        "ADV-005"
      ],
      "no_api": true,
      "purpose": "Freeze session-only, volatility-only, random proxy, side-flip, and translated-POI baselines.",
      "rank": 4,
      "required_inputs": [
        "baseline_control_fields",
        "future captured fields for gated placebos"
      ],
      "result_opening_allowed": false,
      "route_id": "SCID_BASELINE_CONTROL_ASSIGNMENT_MANIFEST_ROUTE"
    },
    {
      "card_ids": [
        "GEO-001",
        "GEO-002",
        "GEO-003",
        "GEO-004",
        "GEO-005",
        "HAZ-001",
        "HAZ-002",
        "HAZ-003",
        "HAZ-004",
        "HAZ-005",
        "MIC-001",
        "MIC-002",
        "MIC-003",
        "MIC-004",
        "MIC-005",
        "BEH-001",
        "BEH-002",
        "BEH-003",
        "BEH-004",
        "BEH-005",
        "MAC-001",
        "MAC-002",
        "MAC-003",
        "MAC-004",
        "MAC-005",
        "EXE-001",
        "EXE-002",
        "EXE-003",
        "EXE-004",
        "EXE-005",
        "UNC-001",
        "UNC-002",
        "UNC-003",
        "UNC-004",
        "UNC-005",
        "ADV-001",
        "ADV-002",
        "ADV-003",
        "ADV-004",
        "ADV-005"
      ],
      "no_api": true,
      "purpose": "Only after G12 source acceptance, freeze direction-aware result design before any outcome opening.",
      "rank": 5,
      "required_inputs": [
        "G12-accepted source fields",
        "frozen partitions",
        "duplicate policy",
        "baseline controls"
      ],
      "result_opening_allowed": false,
      "route_id": "SCID_RESULT_DESIGN_GATE_CONTROL_ROUTE"
    }
  ],
  "schema_version": "scid_no_api_mechanical_hypothesis_factory_offline_schema_v1",
  "validation_safe": false
}
```
