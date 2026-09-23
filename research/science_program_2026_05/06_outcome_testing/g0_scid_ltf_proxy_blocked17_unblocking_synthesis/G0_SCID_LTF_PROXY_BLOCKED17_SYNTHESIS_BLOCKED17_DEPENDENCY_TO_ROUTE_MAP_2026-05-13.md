# Blocked-17 Dependency To Route Map

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

## Machine Payload

```json
{
  "artifact_family": "BLOCKED17_DEPENDENCY_TO_ROUTE_MAP",
  "card_count": 17,
  "cards": [
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "ADV-002",
      "denominator_inclusion": "blocked17_only",
      "dependency_rows": [
        {
          "card_id": "ADV-002",
          "dependency_group": "lower_timeframe_asof_path_availability",
          "dependency_status": "SOURCE_EXISTS_NEEDS_PARSER",
          "future_g12_acceptance_criteria": [
            "source file or cache pointer exists",
            "hash or accepted hash deferral exists",
            "window start/end computed without target/result fields",
            "duplicate denominator key remains unchanged"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "Parser must select only bars/ticks with source time <= decision_asof_utc, bind timezone/session conventions, and emit missing-bar/gap flags.",
          "recommended_route_id": "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
          "recoverability_class": "RECOVERABLE_MARKET_DATA_SOURCE_EXISTS",
          "science_domain": "adversarial_baselines_placebo_explanations",
          "source_families": [
            "accepted_scid_m15_source_control_bars",
            "sierra_converted_m1_m5_m15_ohlcv_roots",
            "prior_production_mt5_tick_parquet_market_context"
          ],
          "source_pointer_policy": "Reference local files by path/size/mtime and small-file hash; do not commit raw parquet/SCID/large market blobs."
        }
      ],
      "field_status_counts": {
        "RECOVERED_SOURCE_BOUND": 2,
        "SOURCE_EXISTS_NEEDS_PARSER": 6
      },
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "recommended_route_ids": [
        "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE"
      ],
      "required_capture_groups": [
        "lower_timeframe_asof_path_availability"
      ],
      "science_domain": "adversarial_baselines_placebo_explanations",
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_LTF_PARSER_REQUIRED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "EXE-001",
      "denominator_inclusion": "blocked17_only",
      "dependency_rows": [
        {
          "card_id": "EXE-001",
          "dependency_group": "lower_timeframe_asof_path_availability",
          "dependency_status": "SOURCE_EXISTS_NEEDS_PARSER",
          "future_g12_acceptance_criteria": [
            "source file or cache pointer exists",
            "hash or accepted hash deferral exists",
            "window start/end computed without target/result fields",
            "duplicate denominator key remains unchanged"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "Parser must select only bars/ticks with source time <= decision_asof_utc, bind timezone/session conventions, and emit missing-bar/gap flags.",
          "recommended_route_id": "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
          "recoverability_class": "RECOVERABLE_MARKET_DATA_SOURCE_EXISTS",
          "science_domain": "execution_science_spread_slippage_fillability",
          "source_families": [
            "accepted_scid_m15_source_control_bars",
            "sierra_converted_m1_m5_m15_ohlcv_roots",
            "prior_production_mt5_tick_parquet_market_context"
          ],
          "source_pointer_policy": "Reference local files by path/size/mtime and small-file hash; do not commit raw parquet/SCID/large market blobs."
        }
      ],
      "field_status_counts": {
        "RECOVERED_SOURCE_BOUND": 2,
        "SOURCE_EXISTS_NEEDS_PARSER": 6
      },
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "recommended_route_ids": [
        "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE"
      ],
      "required_capture_groups": [
        "lower_timeframe_asof_path_availability"
      ],
      "science_domain": "execution_science_spread_slippage_fillability",
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_LTF_PARSER_REQUIRED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "EXE-003",
      "denominator_inclusion": "blocked17_only",
      "dependency_rows": [
        {
          "card_id": "EXE-003",
          "dependency_group": "intended_entry_reference",
          "dependency_status": "NON_GENERATABLE_HISTORICAL_SOURCE_STATE",
          "future_g12_acceptance_criteria": [
            "source-state proof exists or prospective capture contract accepted"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "Prospective capture must bind source component, rule/model hash, MSO snapshot hash, and decision clock.",
          "recommended_route_id": "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE",
          "recoverability_class": "NON_GENERATABLE_IF_NOT_ALREADY_LOGGED",
          "science_domain": "execution_science_spread_slippage_fillability",
          "source_families": [
            "strategy field source expansion packet",
            "forward capture implementation design"
          ],
          "source_pointer_policy": "Use source-safe GTOS logs only if explicit field exists; do not infer from price/proxy/path."
        },
        {
          "card_id": "EXE-003",
          "dependency_group": "lower_timeframe_asof_path_availability",
          "dependency_status": "SOURCE_EXISTS_NEEDS_PARSER",
          "future_g12_acceptance_criteria": [
            "source file or cache pointer exists",
            "hash or accepted hash deferral exists",
            "window start/end computed without target/result fields",
            "duplicate denominator key remains unchanged"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "Parser must select only bars/ticks with source time <= decision_asof_utc, bind timezone/session conventions, and emit missing-bar/gap flags.",
          "recommended_route_id": "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
          "recoverability_class": "RECOVERABLE_MARKET_DATA_SOURCE_EXISTS",
          "science_domain": "execution_science_spread_slippage_fillability",
          "source_families": [
            "accepted_scid_m15_source_control_bars",
            "sierra_converted_m1_m5_m15_ohlcv_roots",
            "prior_production_mt5_tick_parquet_market_context"
          ],
          "source_pointer_policy": "Reference local files by path/size/mtime and small-file hash; do not commit raw parquet/SCID/large market blobs."
        }
      ],
      "field_status_counts": {
        "NON_GENERATABLE_HISTORICAL_SOURCE_STATE": 5,
        "RECOVERED_SOURCE_BOUND": 2,
        "SOURCE_EXISTS_NEEDS_PARSER": 6
      },
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "recommended_route_ids": [
        "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
        "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE"
      ],
      "required_capture_groups": [
        "intended_entry_reference",
        "lower_timeframe_asof_path_availability"
      ],
      "science_domain": "execution_science_spread_slippage_fillability",
      "terminal_source_status": "PARTIAL_SOURCE_STATUS_EXPANDED_WITH_NON_GENERATABLE_SOURCE_STATE_DEPENDENCY"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "EXE-005",
      "denominator_inclusion": "blocked17_only",
      "dependency_rows": [
        {
          "card_id": "EXE-005",
          "dependency_group": "lower_timeframe_asof_path_availability",
          "dependency_status": "SOURCE_EXISTS_NEEDS_PARSER",
          "future_g12_acceptance_criteria": [
            "source file or cache pointer exists",
            "hash or accepted hash deferral exists",
            "window start/end computed without target/result fields",
            "duplicate denominator key remains unchanged"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "Parser must select only bars/ticks with source time <= decision_asof_utc, bind timezone/session conventions, and emit missing-bar/gap flags.",
          "recommended_route_id": "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
          "recoverability_class": "RECOVERABLE_MARKET_DATA_SOURCE_EXISTS",
          "science_domain": "execution_science_spread_slippage_fillability",
          "source_families": [
            "accepted_scid_m15_source_control_bars",
            "sierra_converted_m1_m5_m15_ohlcv_roots",
            "prior_production_mt5_tick_parquet_market_context"
          ],
          "source_pointer_policy": "Reference local files by path/size/mtime and small-file hash; do not commit raw parquet/SCID/large market blobs."
        },
        {
          "card_id": "EXE-005",
          "dependency_group": "future_orderflow_depth_proxy_requirements",
          "dependency_status": "PROXY_VALIDITY_REQUIRES_CONTRACT",
          "future_g12_acceptance_criteria": [
            "proxy mapping version exists",
            "contract/month/session calendar is frozen",
            "non-equivalence to broker CFD truth is explicit",
            "source family parser excludes account/order/deal/position evidence"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "Parser must bind source family, contract, capture/publication as-of, instrument mapping, and source hash before any join.",
          "recommended_route_id": "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE",
          "recoverability_class": "RECOVERABLE_OR_REQUESTABLE_MARKET_CONTEXT_WITH_PROXY_CAVEATS",
          "science_domain": "execution_science_spread_slippage_fillability",
          "source_families": [
            "sierra_depth_market_depth",
            "sierra_scid_footprint_bid_ask_volume",
            "databento_cached_or_declared_orderflow_artifacts",
            "sierra_proxy_registry_status"
          ],
          "source_pointer_policy": "Reference source-status/cache artifacts and local source paths. New paid/vendor/API pulls are forbidden in this route."
        }
      ],
      "field_status_counts": {
        "PROXY_VALIDITY_REQUIRES_CONTRACT": 8,
        "RECOVERED_SOURCE_BOUND": 2,
        "SOURCE_EXISTS_NEEDS_PARSER": 6
      },
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "recommended_route_ids": [
        "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
        "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE"
      ],
      "required_capture_groups": [
        "lower_timeframe_asof_path_availability",
        "future_orderflow_depth_proxy_requirements"
      ],
      "science_domain": "execution_science_spread_slippage_fillability",
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "GEO-002",
      "denominator_inclusion": "blocked17_only",
      "dependency_rows": [
        {
          "card_id": "GEO-002",
          "dependency_group": "lower_timeframe_asof_path_availability",
          "dependency_status": "SOURCE_EXISTS_NEEDS_PARSER",
          "future_g12_acceptance_criteria": [
            "source file or cache pointer exists",
            "hash or accepted hash deferral exists",
            "window start/end computed without target/result fields",
            "duplicate denominator key remains unchanged"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "Parser must select only bars/ticks with source time <= decision_asof_utc, bind timezone/session conventions, and emit missing-bar/gap flags.",
          "recommended_route_id": "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
          "recoverability_class": "RECOVERABLE_MARKET_DATA_SOURCE_EXISTS",
          "science_domain": "geometry_topology_path_shape",
          "source_families": [
            "accepted_scid_m15_source_control_bars",
            "sierra_converted_m1_m5_m15_ohlcv_roots",
            "prior_production_mt5_tick_parquet_market_context"
          ],
          "source_pointer_policy": "Reference local files by path/size/mtime and small-file hash; do not commit raw parquet/SCID/large market blobs."
        }
      ],
      "field_status_counts": {
        "RECOVERED_SOURCE_BOUND": 2,
        "SOURCE_EXISTS_NEEDS_PARSER": 6
      },
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "recommended_route_ids": [
        "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE"
      ],
      "required_capture_groups": [
        "lower_timeframe_asof_path_availability"
      ],
      "science_domain": "geometry_topology_path_shape",
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_LTF_PARSER_REQUIRED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "GEO-003",
      "denominator_inclusion": "blocked17_only",
      "dependency_rows": [
        {
          "card_id": "GEO-003",
          "dependency_group": "poi_type_bounds_source",
          "dependency_status": "NON_GENERATABLE_HISTORICAL_SOURCE_STATE",
          "future_g12_acceptance_criteria": [
            "source-state proof exists or prospective capture contract accepted"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "Prospective capture must bind source component, rule/model hash, MSO snapshot hash, and decision clock.",
          "recommended_route_id": "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE",
          "recoverability_class": "NON_GENERATABLE_IF_NOT_ALREADY_LOGGED",
          "science_domain": "geometry_topology_path_shape",
          "source_families": [
            "strategy field source expansion packet",
            "forward capture implementation design"
          ],
          "source_pointer_policy": "Use source-safe GTOS logs only if explicit field exists; do not infer from price/proxy/path."
        },
        {
          "card_id": "GEO-003",
          "dependency_group": "lower_timeframe_asof_path_availability",
          "dependency_status": "SOURCE_EXISTS_NEEDS_PARSER",
          "future_g12_acceptance_criteria": [
            "source file or cache pointer exists",
            "hash or accepted hash deferral exists",
            "window start/end computed without target/result fields",
            "duplicate denominator key remains unchanged"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "Parser must select only bars/ticks with source time <= decision_asof_utc, bind timezone/session conventions, and emit missing-bar/gap flags.",
          "recommended_route_id": "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
          "recoverability_class": "RECOVERABLE_MARKET_DATA_SOURCE_EXISTS",
          "science_domain": "geometry_topology_path_shape",
          "source_families": [
            "accepted_scid_m15_source_control_bars",
            "sierra_converted_m1_m5_m15_ohlcv_roots",
            "prior_production_mt5_tick_parquet_market_context"
          ],
          "source_pointer_policy": "Reference local files by path/size/mtime and small-file hash; do not commit raw parquet/SCID/large market blobs."
        }
      ],
      "field_status_counts": {
        "NON_GENERATABLE_HISTORICAL_SOURCE_STATE": 7,
        "RECOVERED_SOURCE_BOUND": 2,
        "SOURCE_EXISTS_NEEDS_PARSER": 6
      },
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "recommended_route_ids": [
        "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
        "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE"
      ],
      "required_capture_groups": [
        "poi_type_bounds_source",
        "lower_timeframe_asof_path_availability"
      ],
      "science_domain": "geometry_topology_path_shape",
      "terminal_source_status": "PARTIAL_SOURCE_STATUS_EXPANDED_WITH_NON_GENERATABLE_SOURCE_STATE_DEPENDENCY"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "GEO-004",
      "denominator_inclusion": "blocked17_only",
      "dependency_rows": [
        {
          "card_id": "GEO-004",
          "dependency_group": "intended_entry_reference",
          "dependency_status": "NON_GENERATABLE_HISTORICAL_SOURCE_STATE",
          "future_g12_acceptance_criteria": [
            "source-state proof exists or prospective capture contract accepted"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "Prospective capture must bind source component, rule/model hash, MSO snapshot hash, and decision clock.",
          "recommended_route_id": "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE",
          "recoverability_class": "NON_GENERATABLE_IF_NOT_ALREADY_LOGGED",
          "science_domain": "geometry_topology_path_shape",
          "source_families": [
            "strategy field source expansion packet",
            "forward capture implementation design"
          ],
          "source_pointer_policy": "Use source-safe GTOS logs only if explicit field exists; do not infer from price/proxy/path."
        },
        {
          "card_id": "GEO-004",
          "dependency_group": "lower_timeframe_asof_path_availability",
          "dependency_status": "SOURCE_EXISTS_NEEDS_PARSER",
          "future_g12_acceptance_criteria": [
            "source file or cache pointer exists",
            "hash or accepted hash deferral exists",
            "window start/end computed without target/result fields",
            "duplicate denominator key remains unchanged"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "Parser must select only bars/ticks with source time <= decision_asof_utc, bind timezone/session conventions, and emit missing-bar/gap flags.",
          "recommended_route_id": "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
          "recoverability_class": "RECOVERABLE_MARKET_DATA_SOURCE_EXISTS",
          "science_domain": "geometry_topology_path_shape",
          "source_families": [
            "accepted_scid_m15_source_control_bars",
            "sierra_converted_m1_m5_m15_ohlcv_roots",
            "prior_production_mt5_tick_parquet_market_context"
          ],
          "source_pointer_policy": "Reference local files by path/size/mtime and small-file hash; do not commit raw parquet/SCID/large market blobs."
        }
      ],
      "field_status_counts": {
        "NON_GENERATABLE_HISTORICAL_SOURCE_STATE": 5,
        "RECOVERED_SOURCE_BOUND": 2,
        "SOURCE_EXISTS_NEEDS_PARSER": 6
      },
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "recommended_route_ids": [
        "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
        "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE"
      ],
      "required_capture_groups": [
        "intended_entry_reference",
        "lower_timeframe_asof_path_availability"
      ],
      "science_domain": "geometry_topology_path_shape",
      "terminal_source_status": "PARTIAL_SOURCE_STATUS_EXPANDED_WITH_NON_GENERATABLE_SOURCE_STATE_DEPENDENCY"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "HAZ-003",
      "denominator_inclusion": "blocked17_only",
      "dependency_rows": [
        {
          "card_id": "HAZ-003",
          "dependency_group": "lower_timeframe_asof_path_availability",
          "dependency_status": "SOURCE_EXISTS_NEEDS_PARSER",
          "future_g12_acceptance_criteria": [
            "source file or cache pointer exists",
            "hash or accepted hash deferral exists",
            "window start/end computed without target/result fields",
            "duplicate denominator key remains unchanged"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "Parser must select only bars/ticks with source time <= decision_asof_utc, bind timezone/session conventions, and emit missing-bar/gap flags.",
          "recommended_route_id": "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
          "recoverability_class": "RECOVERABLE_MARKET_DATA_SOURCE_EXISTS",
          "science_domain": "stochastic_tail_hazard_first_passage",
          "source_families": [
            "accepted_scid_m15_source_control_bars",
            "sierra_converted_m1_m5_m15_ohlcv_roots",
            "prior_production_mt5_tick_parquet_market_context"
          ],
          "source_pointer_policy": "Reference local files by path/size/mtime and small-file hash; do not commit raw parquet/SCID/large market blobs."
        },
        {
          "card_id": "HAZ-003",
          "dependency_group": "intended_entry_reference",
          "dependency_status": "NON_GENERATABLE_HISTORICAL_SOURCE_STATE",
          "future_g12_acceptance_criteria": [
            "source-state proof exists or prospective capture contract accepted"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "Prospective capture must bind source component, rule/model hash, MSO snapshot hash, and decision clock.",
          "recommended_route_id": "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE",
          "recoverability_class": "NON_GENERATABLE_IF_NOT_ALREADY_LOGGED",
          "science_domain": "stochastic_tail_hazard_first_passage",
          "source_families": [
            "strategy field source expansion packet",
            "forward capture implementation design"
          ],
          "source_pointer_policy": "Use source-safe GTOS logs only if explicit field exists; do not infer from price/proxy/path."
        },
        {
          "card_id": "HAZ-003",
          "dependency_group": "intended_stop_reference",
          "dependency_status": "NON_GENERATABLE_HISTORICAL_SOURCE_STATE",
          "future_g12_acceptance_criteria": [
            "source-state proof exists or prospective capture contract accepted"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "Prospective capture must bind source component, rule/model hash, MSO snapshot hash, and decision clock.",
          "recommended_route_id": "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE",
          "recoverability_class": "NON_GENERATABLE_IF_NOT_ALREADY_LOGGED",
          "science_domain": "stochastic_tail_hazard_first_passage",
          "source_families": [
            "strategy field source expansion packet",
            "forward capture implementation design"
          ],
          "source_pointer_policy": "Use source-safe GTOS logs only if explicit field exists; do not infer from price/proxy/path."
        },
        {
          "card_id": "HAZ-003",
          "dependency_group": "intended_target_reference",
          "dependency_status": "NON_GENERATABLE_HISTORICAL_SOURCE_STATE",
          "future_g12_acceptance_criteria": [
            "source-state proof exists or prospective capture contract accepted"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "Prospective capture must bind source component, rule/model hash, MSO snapshot hash, and decision clock.",
          "recommended_route_id": "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE",
          "recoverability_class": "NON_GENERATABLE_IF_NOT_ALREADY_LOGGED",
          "science_domain": "stochastic_tail_hazard_first_passage",
          "source_families": [
            "strategy field source expansion packet",
            "forward capture implementation design"
          ],
          "source_pointer_policy": "Use source-safe GTOS logs only if explicit field exists; do not infer from price/proxy/path."
        }
      ],
      "field_status_counts": {
        "NON_GENERATABLE_HISTORICAL_SOURCE_STATE": 5,
        "PROSPECTIVE_CAPTURE_REQUIRED": 10,
        "RECOVERED_SOURCE_BOUND": 2,
        "SOURCE_EXISTS_NEEDS_PARSER": 6
      },
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "recommended_route_ids": [
        "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
        "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE"
      ],
      "required_capture_groups": [
        "lower_timeframe_asof_path_availability",
        "intended_entry_reference",
        "intended_stop_reference",
        "intended_target_reference"
      ],
      "science_domain": "stochastic_tail_hazard_first_passage",
      "terminal_source_status": "PARTIAL_SOURCE_STATUS_EXPANDED_WITH_NON_GENERATABLE_SOURCE_STATE_DEPENDENCY"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "HAZ-004",
      "denominator_inclusion": "blocked17_only",
      "dependency_rows": [
        {
          "card_id": "HAZ-004",
          "dependency_group": "lower_timeframe_asof_path_availability",
          "dependency_status": "SOURCE_EXISTS_NEEDS_PARSER",
          "future_g12_acceptance_criteria": [
            "source file or cache pointer exists",
            "hash or accepted hash deferral exists",
            "window start/end computed without target/result fields",
            "duplicate denominator key remains unchanged"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "Parser must select only bars/ticks with source time <= decision_asof_utc, bind timezone/session conventions, and emit missing-bar/gap flags.",
          "recommended_route_id": "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
          "recoverability_class": "RECOVERABLE_MARKET_DATA_SOURCE_EXISTS",
          "science_domain": "stochastic_tail_hazard_first_passage",
          "source_families": [
            "accepted_scid_m15_source_control_bars",
            "sierra_converted_m1_m5_m15_ohlcv_roots",
            "prior_production_mt5_tick_parquet_market_context"
          ],
          "source_pointer_policy": "Reference local files by path/size/mtime and small-file hash; do not commit raw parquet/SCID/large market blobs."
        },
        {
          "card_id": "HAZ-004",
          "dependency_group": "baseline_control_fields",
          "dependency_status": "PROSPECTIVE_CAPTURE_REQUIRED",
          "future_g12_acceptance_criteria": [
            "baseline seed frozen",
            "duplicate policy frozen",
            "no outcome fields opened"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "No parser until rowset/control packet route materializes denominator and seed assignment.",
          "recommended_route_id": "SCID_BASELINE_CONTROL_PACKET_REPAIR_AND_DUPLICATE_POLICY_ROUTE",
          "recoverability_class": "SOURCE_CONTROL_ASSIGNMENT_REQUIRED_BEFORE_RESULTS",
          "science_domain": "stochastic_tail_hazard_first_passage",
          "source_families": [
            "ready-rowset denominator/control packet"
          ],
          "source_pointer_policy": "Control fields are packet metadata, not market data. They must be frozen before scoring."
        }
      ],
      "field_status_counts": {
        "PROSPECTIVE_CAPTURE_REQUIRED": 3,
        "RECOVERED_SOURCE_BOUND": 7,
        "SOURCE_EXISTS_NEEDS_PARSER": 6
      },
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "recommended_route_ids": [
        "SCID_BASELINE_CONTROL_PACKET_REPAIR_AND_DUPLICATE_POLICY_ROUTE",
        "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
        "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE"
      ],
      "required_capture_groups": [
        "lower_timeframe_asof_path_availability",
        "baseline_control_fields"
      ],
      "science_domain": "stochastic_tail_hazard_first_passage",
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_LTF_PARSER_REQUIRED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "MAC-003",
      "denominator_inclusion": "blocked17_only",
      "dependency_rows": [
        {
          "card_id": "MAC-003",
          "dependency_group": "baseline_control_fields",
          "dependency_status": "PROSPECTIVE_CAPTURE_REQUIRED",
          "future_g12_acceptance_criteria": [
            "baseline seed frozen",
            "duplicate policy frozen",
            "no outcome fields opened"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "No parser until rowset/control packet route materializes denominator and seed assignment.",
          "recommended_route_id": "SCID_BASELINE_CONTROL_PACKET_REPAIR_AND_DUPLICATE_POLICY_ROUTE",
          "recoverability_class": "SOURCE_CONTROL_ASSIGNMENT_REQUIRED_BEFORE_RESULTS",
          "science_domain": "macro_session_calendar_cross_asset_context",
          "source_families": [
            "ready-rowset denominator/control packet"
          ],
          "source_pointer_policy": "Control fields are packet metadata, not market data. They must be frozen before scoring."
        },
        {
          "card_id": "MAC-003",
          "dependency_group": "future_orderflow_depth_proxy_requirements",
          "dependency_status": "PROXY_VALIDITY_REQUIRES_CONTRACT",
          "future_g12_acceptance_criteria": [
            "proxy mapping version exists",
            "contract/month/session calendar is frozen",
            "non-equivalence to broker CFD truth is explicit",
            "source family parser excludes account/order/deal/position evidence"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "Parser must bind source family, contract, capture/publication as-of, instrument mapping, and source hash before any join.",
          "recommended_route_id": "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE",
          "recoverability_class": "RECOVERABLE_OR_REQUESTABLE_MARKET_CONTEXT_WITH_PROXY_CAVEATS",
          "science_domain": "macro_session_calendar_cross_asset_context",
          "source_families": [
            "sierra_depth_market_depth",
            "sierra_scid_footprint_bid_ask_volume",
            "databento_cached_or_declared_orderflow_artifacts",
            "sierra_proxy_registry_status"
          ],
          "source_pointer_policy": "Reference source-status/cache artifacts and local source paths. New paid/vendor/API pulls are forbidden in this route."
        }
      ],
      "field_status_counts": {
        "PROSPECTIVE_CAPTURE_REQUIRED": 3,
        "PROXY_VALIDITY_REQUIRES_CONTRACT": 8,
        "RECOVERED_SOURCE_BOUND": 6
      },
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "recommended_route_ids": [
        "SCID_BASELINE_CONTROL_PACKET_REPAIR_AND_DUPLICATE_POLICY_ROUTE",
        "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE",
        "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE"
      ],
      "required_capture_groups": [
        "baseline_control_fields",
        "future_orderflow_depth_proxy_requirements"
      ],
      "science_domain": "macro_session_calendar_cross_asset_context",
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "MIC-001",
      "denominator_inclusion": "blocked17_only",
      "dependency_rows": [
        {
          "card_id": "MIC-001",
          "dependency_group": "future_orderflow_depth_proxy_requirements",
          "dependency_status": "PROXY_VALIDITY_REQUIRES_CONTRACT",
          "future_g12_acceptance_criteria": [
            "proxy mapping version exists",
            "contract/month/session calendar is frozen",
            "non-equivalence to broker CFD truth is explicit",
            "source family parser excludes account/order/deal/position evidence"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "Parser must bind source family, contract, capture/publication as-of, instrument mapping, and source hash before any join.",
          "recommended_route_id": "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE",
          "recoverability_class": "RECOVERABLE_OR_REQUESTABLE_MARKET_CONTEXT_WITH_PROXY_CAVEATS",
          "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
          "source_families": [
            "sierra_depth_market_depth",
            "sierra_scid_footprint_bid_ask_volume",
            "databento_cached_or_declared_orderflow_artifacts",
            "sierra_proxy_registry_status"
          ],
          "source_pointer_policy": "Reference source-status/cache artifacts and local source paths. New paid/vendor/API pulls are forbidden in this route."
        }
      ],
      "field_status_counts": {
        "PROXY_VALIDITY_REQUIRES_CONTRACT": 8,
        "RECOVERED_SOURCE_BOUND": 1
      },
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "recommended_route_ids": [
        "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE"
      ],
      "required_capture_groups": [
        "future_orderflow_depth_proxy_requirements"
      ],
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "MIC-002",
      "denominator_inclusion": "blocked17_only",
      "dependency_rows": [
        {
          "card_id": "MIC-002",
          "dependency_group": "future_orderflow_depth_proxy_requirements",
          "dependency_status": "PROXY_VALIDITY_REQUIRES_CONTRACT",
          "future_g12_acceptance_criteria": [
            "proxy mapping version exists",
            "contract/month/session calendar is frozen",
            "non-equivalence to broker CFD truth is explicit",
            "source family parser excludes account/order/deal/position evidence"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "Parser must bind source family, contract, capture/publication as-of, instrument mapping, and source hash before any join.",
          "recommended_route_id": "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE",
          "recoverability_class": "RECOVERABLE_OR_REQUESTABLE_MARKET_CONTEXT_WITH_PROXY_CAVEATS",
          "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
          "source_families": [
            "sierra_depth_market_depth",
            "sierra_scid_footprint_bid_ask_volume",
            "databento_cached_or_declared_orderflow_artifacts",
            "sierra_proxy_registry_status"
          ],
          "source_pointer_policy": "Reference source-status/cache artifacts and local source paths. New paid/vendor/API pulls are forbidden in this route."
        },
        {
          "card_id": "MIC-002",
          "dependency_group": "lower_timeframe_asof_path_availability",
          "dependency_status": "SOURCE_EXISTS_NEEDS_PARSER",
          "future_g12_acceptance_criteria": [
            "source file or cache pointer exists",
            "hash or accepted hash deferral exists",
            "window start/end computed without target/result fields",
            "duplicate denominator key remains unchanged"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "Parser must select only bars/ticks with source time <= decision_asof_utc, bind timezone/session conventions, and emit missing-bar/gap flags.",
          "recommended_route_id": "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
          "recoverability_class": "RECOVERABLE_MARKET_DATA_SOURCE_EXISTS",
          "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
          "source_families": [
            "accepted_scid_m15_source_control_bars",
            "sierra_converted_m1_m5_m15_ohlcv_roots",
            "prior_production_mt5_tick_parquet_market_context"
          ],
          "source_pointer_policy": "Reference local files by path/size/mtime and small-file hash; do not commit raw parquet/SCID/large market blobs."
        }
      ],
      "field_status_counts": {
        "PROXY_VALIDITY_REQUIRES_CONTRACT": 8,
        "RECOVERED_SOURCE_BOUND": 2,
        "SOURCE_EXISTS_NEEDS_PARSER": 6
      },
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "recommended_route_ids": [
        "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
        "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE"
      ],
      "required_capture_groups": [
        "future_orderflow_depth_proxy_requirements",
        "lower_timeframe_asof_path_availability"
      ],
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "MIC-003",
      "denominator_inclusion": "blocked17_only",
      "dependency_rows": [
        {
          "card_id": "MIC-003",
          "dependency_group": "poi_type_bounds_source",
          "dependency_status": "NON_GENERATABLE_HISTORICAL_SOURCE_STATE",
          "future_g12_acceptance_criteria": [
            "source-state proof exists or prospective capture contract accepted"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "Prospective capture must bind source component, rule/model hash, MSO snapshot hash, and decision clock.",
          "recommended_route_id": "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE",
          "recoverability_class": "NON_GENERATABLE_IF_NOT_ALREADY_LOGGED",
          "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
          "source_families": [
            "strategy field source expansion packet",
            "forward capture implementation design"
          ],
          "source_pointer_policy": "Use source-safe GTOS logs only if explicit field exists; do not infer from price/proxy/path."
        },
        {
          "card_id": "MIC-003",
          "dependency_group": "future_orderflow_depth_proxy_requirements",
          "dependency_status": "PROXY_VALIDITY_REQUIRES_CONTRACT",
          "future_g12_acceptance_criteria": [
            "proxy mapping version exists",
            "contract/month/session calendar is frozen",
            "non-equivalence to broker CFD truth is explicit",
            "source family parser excludes account/order/deal/position evidence"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "Parser must bind source family, contract, capture/publication as-of, instrument mapping, and source hash before any join.",
          "recommended_route_id": "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE",
          "recoverability_class": "RECOVERABLE_OR_REQUESTABLE_MARKET_CONTEXT_WITH_PROXY_CAVEATS",
          "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
          "source_families": [
            "sierra_depth_market_depth",
            "sierra_scid_footprint_bid_ask_volume",
            "databento_cached_or_declared_orderflow_artifacts",
            "sierra_proxy_registry_status"
          ],
          "source_pointer_policy": "Reference source-status/cache artifacts and local source paths. New paid/vendor/API pulls are forbidden in this route."
        }
      ],
      "field_status_counts": {
        "NON_GENERATABLE_HISTORICAL_SOURCE_STATE": 7,
        "PROXY_VALIDITY_REQUIRES_CONTRACT": 8,
        "RECOVERED_SOURCE_BOUND": 1
      },
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "recommended_route_ids": [
        "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE",
        "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE"
      ],
      "required_capture_groups": [
        "poi_type_bounds_source",
        "future_orderflow_depth_proxy_requirements"
      ],
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "terminal_source_status": "PARTIAL_SOURCE_STATUS_EXPANDED_WITH_NON_GENERATABLE_SOURCE_STATE_DEPENDENCY"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "MIC-004",
      "denominator_inclusion": "blocked17_only",
      "dependency_rows": [
        {
          "card_id": "MIC-004",
          "dependency_group": "future_orderflow_depth_proxy_requirements",
          "dependency_status": "PROXY_VALIDITY_REQUIRES_CONTRACT",
          "future_g12_acceptance_criteria": [
            "proxy mapping version exists",
            "contract/month/session calendar is frozen",
            "non-equivalence to broker CFD truth is explicit",
            "source family parser excludes account/order/deal/position evidence"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "Parser must bind source family, contract, capture/publication as-of, instrument mapping, and source hash before any join.",
          "recommended_route_id": "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE",
          "recoverability_class": "RECOVERABLE_OR_REQUESTABLE_MARKET_CONTEXT_WITH_PROXY_CAVEATS",
          "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
          "source_families": [
            "sierra_depth_market_depth",
            "sierra_scid_footprint_bid_ask_volume",
            "databento_cached_or_declared_orderflow_artifacts",
            "sierra_proxy_registry_status"
          ],
          "source_pointer_policy": "Reference source-status/cache artifacts and local source paths. New paid/vendor/API pulls are forbidden in this route."
        },
        {
          "card_id": "MIC-004",
          "dependency_group": "baseline_control_fields",
          "dependency_status": "PROSPECTIVE_CAPTURE_REQUIRED",
          "future_g12_acceptance_criteria": [
            "baseline seed frozen",
            "duplicate policy frozen",
            "no outcome fields opened"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "No parser until rowset/control packet route materializes denominator and seed assignment.",
          "recommended_route_id": "SCID_BASELINE_CONTROL_PACKET_REPAIR_AND_DUPLICATE_POLICY_ROUTE",
          "recoverability_class": "SOURCE_CONTROL_ASSIGNMENT_REQUIRED_BEFORE_RESULTS",
          "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
          "source_families": [
            "ready-rowset denominator/control packet"
          ],
          "source_pointer_policy": "Control fields are packet metadata, not market data. They must be frozen before scoring."
        }
      ],
      "field_status_counts": {
        "PROSPECTIVE_CAPTURE_REQUIRED": 3,
        "PROXY_VALIDITY_REQUIRES_CONTRACT": 8,
        "RECOVERED_SOURCE_BOUND": 6
      },
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "recommended_route_ids": [
        "SCID_BASELINE_CONTROL_PACKET_REPAIR_AND_DUPLICATE_POLICY_ROUTE",
        "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE",
        "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE"
      ],
      "required_capture_groups": [
        "future_orderflow_depth_proxy_requirements",
        "baseline_control_fields"
      ],
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "MIC-005",
      "denominator_inclusion": "blocked17_only",
      "dependency_rows": [
        {
          "card_id": "MIC-005",
          "dependency_group": "future_orderflow_depth_proxy_requirements",
          "dependency_status": "PROXY_VALIDITY_REQUIRES_CONTRACT",
          "future_g12_acceptance_criteria": [
            "proxy mapping version exists",
            "contract/month/session calendar is frozen",
            "non-equivalence to broker CFD truth is explicit",
            "source family parser excludes account/order/deal/position evidence"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "Parser must bind source family, contract, capture/publication as-of, instrument mapping, and source hash before any join.",
          "recommended_route_id": "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE",
          "recoverability_class": "RECOVERABLE_OR_REQUESTABLE_MARKET_CONTEXT_WITH_PROXY_CAVEATS",
          "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
          "source_families": [
            "sierra_depth_market_depth",
            "sierra_scid_footprint_bid_ask_volume",
            "databento_cached_or_declared_orderflow_artifacts",
            "sierra_proxy_registry_status"
          ],
          "source_pointer_policy": "Reference source-status/cache artifacts and local source paths. New paid/vendor/API pulls are forbidden in this route."
        },
        {
          "card_id": "MIC-005",
          "dependency_group": "lower_timeframe_asof_path_availability",
          "dependency_status": "SOURCE_EXISTS_NEEDS_PARSER",
          "future_g12_acceptance_criteria": [
            "source file or cache pointer exists",
            "hash or accepted hash deferral exists",
            "window start/end computed without target/result fields",
            "duplicate denominator key remains unchanged"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "Parser must select only bars/ticks with source time <= decision_asof_utc, bind timezone/session conventions, and emit missing-bar/gap flags.",
          "recommended_route_id": "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
          "recoverability_class": "RECOVERABLE_MARKET_DATA_SOURCE_EXISTS",
          "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
          "source_families": [
            "accepted_scid_m15_source_control_bars",
            "sierra_converted_m1_m5_m15_ohlcv_roots",
            "prior_production_mt5_tick_parquet_market_context"
          ],
          "source_pointer_policy": "Reference local files by path/size/mtime and small-file hash; do not commit raw parquet/SCID/large market blobs."
        }
      ],
      "field_status_counts": {
        "PROXY_VALIDITY_REQUIRES_CONTRACT": 8,
        "RECOVERED_SOURCE_BOUND": 2,
        "SOURCE_EXISTS_NEEDS_PARSER": 6
      },
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "recommended_route_ids": [
        "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
        "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE"
      ],
      "required_capture_groups": [
        "future_orderflow_depth_proxy_requirements",
        "lower_timeframe_asof_path_availability"
      ],
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow",
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "UNC-001",
      "denominator_inclusion": "blocked17_only",
      "dependency_rows": [
        {
          "card_id": "UNC-001",
          "dependency_group": "lower_timeframe_asof_path_availability",
          "dependency_status": "SOURCE_EXISTS_NEEDS_PARSER",
          "future_g12_acceptance_criteria": [
            "source file or cache pointer exists",
            "hash or accepted hash deferral exists",
            "window start/end computed without target/result fields",
            "duplicate denominator key remains unchanged"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "Parser must select only bars/ticks with source time <= decision_asof_utc, bind timezone/session conventions, and emit missing-bar/gap flags.",
          "recommended_route_id": "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
          "recoverability_class": "RECOVERABLE_MARKET_DATA_SOURCE_EXISTS",
          "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
          "source_families": [
            "accepted_scid_m15_source_control_bars",
            "sierra_converted_m1_m5_m15_ohlcv_roots",
            "prior_production_mt5_tick_parquet_market_context"
          ],
          "source_pointer_policy": "Reference local files by path/size/mtime and small-file hash; do not commit raw parquet/SCID/large market blobs."
        },
        {
          "card_id": "UNC-001",
          "dependency_group": "future_orderflow_depth_proxy_requirements",
          "dependency_status": "PROXY_VALIDITY_REQUIRES_CONTRACT",
          "future_g12_acceptance_criteria": [
            "proxy mapping version exists",
            "contract/month/session calendar is frozen",
            "non-equivalence to broker CFD truth is explicit",
            "source family parser excludes account/order/deal/position evidence"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "Parser must bind source family, contract, capture/publication as-of, instrument mapping, and source hash before any join.",
          "recommended_route_id": "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE",
          "recoverability_class": "RECOVERABLE_OR_REQUESTABLE_MARKET_CONTEXT_WITH_PROXY_CAVEATS",
          "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
          "source_families": [
            "sierra_depth_market_depth",
            "sierra_scid_footprint_bid_ask_volume",
            "databento_cached_or_declared_orderflow_artifacts",
            "sierra_proxy_registry_status"
          ],
          "source_pointer_policy": "Reference source-status/cache artifacts and local source paths. New paid/vendor/API pulls are forbidden in this route."
        },
        {
          "card_id": "UNC-001",
          "dependency_group": "baseline_control_fields",
          "dependency_status": "PROSPECTIVE_CAPTURE_REQUIRED",
          "future_g12_acceptance_criteria": [
            "baseline seed frozen",
            "duplicate policy frozen",
            "no outcome fields opened"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "No parser until rowset/control packet route materializes denominator and seed assignment.",
          "recommended_route_id": "SCID_BASELINE_CONTROL_PACKET_REPAIR_AND_DUPLICATE_POLICY_ROUTE",
          "recoverability_class": "SOURCE_CONTROL_ASSIGNMENT_REQUIRED_BEFORE_RESULTS",
          "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
          "source_families": [
            "ready-rowset denominator/control packet"
          ],
          "source_pointer_policy": "Control fields are packet metadata, not market data. They must be frozen before scoring."
        }
      ],
      "field_status_counts": {
        "PROSPECTIVE_CAPTURE_REQUIRED": 3,
        "PROXY_VALIDITY_REQUIRES_CONTRACT": 8,
        "RECOVERED_SOURCE_BOUND": 7,
        "SOURCE_EXISTS_NEEDS_PARSER": 6
      },
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "recommended_route_ids": [
        "SCID_BASELINE_CONTROL_PACKET_REPAIR_AND_DUPLICATE_POLICY_ROUTE",
        "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
        "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE",
        "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE"
      ],
      "required_capture_groups": [
        "lower_timeframe_asof_path_availability",
        "future_orderflow_depth_proxy_requirements",
        "baseline_control_fields"
      ],
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
      "terminal_source_status": "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED"
    },
    {
      "accepted_readiness": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
      "card_id": "UNC-005",
      "denominator_inclusion": "blocked17_only",
      "dependency_rows": [
        {
          "card_id": "UNC-005",
          "dependency_group": "baseline_control_fields",
          "dependency_status": "PROSPECTIVE_CAPTURE_REQUIRED",
          "future_g12_acceptance_criteria": [
            "baseline seed frozen",
            "duplicate policy frozen",
            "no outcome fields opened"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "No parser until rowset/control packet route materializes denominator and seed assignment.",
          "recommended_route_id": "SCID_BASELINE_CONTROL_PACKET_REPAIR_AND_DUPLICATE_POLICY_ROUTE",
          "recoverability_class": "SOURCE_CONTROL_ASSIGNMENT_REQUIRED_BEFORE_RESULTS",
          "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
          "source_families": [
            "ready-rowset denominator/control packet"
          ],
          "source_pointer_policy": "Control fields are packet metadata, not market data. They must be frozen before scoring."
        },
        {
          "card_id": "UNC-005",
          "dependency_group": "framework_setup_family",
          "dependency_status": "NON_GENERATABLE_HISTORICAL_SOURCE_STATE",
          "future_g12_acceptance_criteria": [
            "source-state proof exists or prospective capture contract accepted"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "Prospective capture must bind source component, rule/model hash, MSO snapshot hash, and decision clock.",
          "recommended_route_id": "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE",
          "recoverability_class": "NON_GENERATABLE_IF_NOT_ALREADY_LOGGED",
          "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
          "source_families": [
            "strategy field source expansion packet",
            "forward capture implementation design"
          ],
          "source_pointer_policy": "Use source-safe GTOS logs only if explicit field exists; do not infer from price/proxy/path."
        },
        {
          "card_id": "UNC-005",
          "dependency_group": "lower_timeframe_asof_path_availability",
          "dependency_status": "SOURCE_EXISTS_NEEDS_PARSER",
          "future_g12_acceptance_criteria": [
            "source file or cache pointer exists",
            "hash or accepted hash deferral exists",
            "window start/end computed without target/result fields",
            "duplicate denominator key remains unchanged"
          ],
          "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
          "may_score_results_now": false,
          "parser_asof_requirement": "Parser must select only bars/ticks with source time <= decision_asof_utc, bind timezone/session conventions, and emit missing-bar/gap flags.",
          "recommended_route_id": "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
          "recoverability_class": "RECOVERABLE_MARKET_DATA_SOURCE_EXISTS",
          "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
          "source_families": [
            "accepted_scid_m15_source_control_bars",
            "sierra_converted_m1_m5_m15_ohlcv_roots",
            "prior_production_mt5_tick_parquet_market_context"
          ],
          "source_pointer_policy": "Reference local files by path/size/mtime and small-file hash; do not commit raw parquet/SCID/large market blobs."
        }
      ],
      "field_status_counts": {
        "NON_GENERATABLE_HISTORICAL_SOURCE_STATE": 6,
        "PROSPECTIVE_CAPTURE_REQUIRED": 3,
        "RECOVERED_SOURCE_BOUND": 7,
        "SOURCE_EXISTS_NEEDS_PARSER": 6
      },
      "future_result_gate": "No result/design/scoring lane may consume this card until required fields are captured or recovered, G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design prompt authorizes outcome opening.",
      "may_score_results_now": false,
      "recommended_route_ids": [
        "SCID_BASELINE_CONTROL_PACKET_REPAIR_AND_DUPLICATE_POLICY_ROUTE",
        "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
        "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE"
      ],
      "required_capture_groups": [
        "baseline_control_fields",
        "framework_setup_family",
        "lower_timeframe_asof_path_availability"
      ],
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls",
      "terminal_source_status": "PARTIAL_SOURCE_STATUS_EXPANDED_WITH_NON_GENERATABLE_SOURCE_STATE_DEPENDENCY"
    }
  ],
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "dependency_group_counts": {
    "baseline_control_fields": 5,
    "framework_setup_family": 1,
    "future_orderflow_depth_proxy_requirements": 8,
    "intended_entry_reference": 3,
    "intended_stop_reference": 1,
    "intended_target_reference": 1,
    "lower_timeframe_asof_path_availability": 13,
    "poi_type_bounds_source": 2
  },
  "evidence_class": "G0_SCID_LTF_PROXY_BLOCKED17_UNBLOCKING_SYNTHESIS_ONLY",
  "field_status_counts": {
    "NON_GENERATABLE_HISTORICAL_SOURCE_STATE": 35,
    "PROSPECTIVE_CAPTURE_REQUIRED": 25,
    "PROXY_VALIDITY_REQUIRES_CONTRACT": 64,
    "RECOVERED_SOURCE_BOUND": 55,
    "SOURCE_EXISTS_NEEDS_PARSER": 78
  },
  "generated_at_utc": "2026-05-13T01:20:09Z",
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
  "route_counts": {
    "SCID_BASELINE_CONTROL_PACKET_REPAIR_AND_DUPLICATE_POLICY_ROUTE": 5,
    "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE": 13,
    "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE": 10,
    "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE": 8
  },
  "route_id": "G0_SCID_LTF_PROXY_BLOCKED17_UNBLOCKING_SYNTHESIS",
  "schema_version": "g0_scid_ltf_proxy_blocked17_unblocking_synthesis_v1",
  "validation_safe": false
}
```
