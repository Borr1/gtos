# G0EXP R1 Parser Version Shape Fingerprint Matrix

- **route_id:** `G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL`
- **evidence_class:** `G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

- Parser/control files fingerprinted: `120`.
- Schema/control shapes fingerprinted: `120`.

```json
{
  "artifact_family": "parser_version_shape_fingerprint_matrix",
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_ONLY",
  "generated_at_utc": "2026-05-13T02:51:58Z",
  "head_at_build": "3ab07d464082",
  "live_effect": false,
  "matrix_status": "CLOSED_PARSER_AND_SCHEMA_FINGERPRINTS_EMITTED",
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
  "parser_drift_policy": "Any future denominator-entry packet must bind parser_code_hash, shape_fingerprint, schema key-set fingerprint, producer file path, and lineage commit before outcome/result opening.",
  "parser_file_count": 120,
  "parser_rows": [
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\build_lto031_lto032_sierra_scid_footprint_profile_plan.py",
      "ast_status": "PARSED",
      "parser_code_hash": "b89875a08c3936334c4ae95d829a6d887be321327db30e00785188c885839852",
      "path": "scripts/build_lto031_lto032_sierra_scid_footprint_profile_plan.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/build_lto031_lto032_sierra_scid_footprint_profile_plan.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "build_parser",
          "main"
        ],
        "imports": [
          "__future__",
          "argparse",
          "json",
          "pathlib",
          "src",
          "sys"
        ],
        "markers": {
          "scid": true
        }
      },
      "shape_fingerprint": "f0f6f3c64051581a8e6ccb2357fe906cbc0e892b2d43e36a18efa1e2d672a04e",
      "size_bytes": 2919,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_d11_2022_2023_backfill_bias.py",
      "ast_status": "PARSED",
      "parser_code_hash": "7f08986c7a70a29cdcfea9a30c2191d0ae3d0994b3616836bfd03f3bbf803517",
      "path": "scripts/analyze_d11_2022_2023_backfill_bias.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_d11_2022_2023_backfill_bias.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "best_ohlc_source",
          "build_ohlc_audit",
          "build_payload",
          "candidate_ohlc_paths",
          "fmt",
          "generic_kill_zone",
          "label_coverage_flags",
          "load_csv_trade_rows",
          "load_mechanical_jsonl_events",
          "load_trade_index",
          "main",
          "make_bias_readout",
          "markdown_table",
          "mean",
          "median",
          "normalize_symbol",
          "parse_dt",
          "pct",
          "period_label",
          "quantile",
          "read_ohlc_rows",
          "render_markdown",
          "safe_float",
          "summarize_event_population",
          "summarize_ohlc_rows",
          "summarize_regime_jsonl",
          "summarize_trades",
          "write_outputs"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "csv",
          "datetime",
          "json",
          "math",
          "pathlib",
          "statistics",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "0eee74007337d563f04aeb5bba3922c186450c5d1a7a4a296cbd0acd46503eea",
      "size_bytes": 35178,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_external_feed_candidate_diagnostics.py",
      "ast_status": "PARSED",
      "parser_code_hash": "2e241f96d5ea277e9a13a9987b435022c868ad8a469cccbdcf34f5d3f847b89c",
      "path": "scripts/analyze_external_feed_candidate_diagnostics.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_external_feed_candidate_diagnostics.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_as_float",
          "_finite_number",
          "_fmt",
          "_label",
          "_mean_diff",
          "_pct",
          "_pearson",
          "_rank",
          "_sorted_groups",
          "_spearman",
          "build_candidate_diagnostics",
          "build_coverage",
          "build_fold_counts",
          "build_methodology_gate",
          "build_parser",
          "find_latest_candidate_join",
          "load_jsonl",
          "main",
          "render_markdown",
          "summarize_by_field",
          "summarize_numeric_field",
          "summarize_rows",
          "summarize_values",
          "write_diagnostic_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "json",
          "math",
          "pathlib",
          "src",
          "statistics",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "b51c2b4a3202f3b6489a93e0d043315837840fb8c1387eaf531a1d504deb0b94",
      "size_bytes": 22770,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_historical_opportunity_dataset.py",
      "ast_status": "PARSED",
      "parser_code_hash": "e3c2733c537afb71f725cc314102bb69934630b6d1ded9f397d78b783664361e",
      "path": "scripts/analyze_historical_opportunity_dataset.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_historical_opportunity_dataset.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [
          "DatasetAccumulator",
          "GroupStats",
          "RefinementAccumulator"
        ],
        "functions": [
          "_compare_builder_summaries",
          "_counter_pair_rows",
          "_feature_quintiles",
          "_feature_rows",
          "_first_after",
          "_float_or_none",
          "_iter_numeric_external_features",
          "_load_lower_timeframe_rows",
          "_markdown_cell",
          "_markdown_refinements",
          "_markdown_table",
          "_mean",
          "_rate",
          "_read_json",
          "_row_qualifies_for_refinement",
          "_scaled_hold_bars",
          "_setup_from_row",
          "_stats_rows",
          "_synthesis_bullets",
          "add",
          "add",
          "add",
          "analyze_dataset",
          "as_row",
          "build_parser",
          "find_latest_input",
          "infer_summary_path",
          "iter_jsonl",
          "main",
          "refine_mechanical_outcome",
          "render_report",
          "to_summary",
          "to_summary",
          "write_report"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "dataclasses",
          "datetime",
          "json",
          "math",
          "pathlib",
          "scripts",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "as_of": true,
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "7bb24a9b3181108851ccbf0257f656c0d34bfb0f2f97c3252d517e12dbd55d7c",
      "size_bytes": 41247,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_historical_opportunity_truth_layer.py",
      "ast_status": "PARSED",
      "parser_code_hash": "fa29d66b0aed171adbf166913d5c26a0535c631e48168e7689b840843a213212",
      "path": "scripts/analyze_historical_opportunity_truth_layer.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_historical_opportunity_truth_layer.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [
          "CohortStats",
          "M1M5DisagreementStats",
          "OhlcvCache",
          "PathAnatomyStats"
        ],
        "functions": [
          "__init__",
          "_add_path_metrics",
          "_analysis_timeframe",
          "_anatomy_rows",
          "_as_float",
          "_as_int",
          "_bucket_belongs_to_setup_population",
          "_candidate_rows",
          "_counter_rows",
          "_describe_values",
          "_failure_rank_rows",
          "_future_rows",
          "_group_keys",
          "_horizon_bars",
          "_is_setup_row",
          "_markdown_cell",
          "_markdown_table",
          "_mean",
          "_mean_list",
          "_quantile",
          "_rate",
          "_setup_values",
          "_short_artifact_slug",
          "_stats_rows",
          "_synthesis_bullets",
          "add",
          "add",
          "add_no_entry_metric",
          "add_row",
          "add_sl_metric",
          "analyze_truth_layer",
          "as_row",
          "build_parser",
          "compute_no_entry_path_metric",
          "compute_sl_path_metric",
          "find_latest_input",
          "future_slice",
          "iter_jsonl",
          "main",
          "no_entry_row",
          "render_report",
          "rows",
          "sl_row",
          "to_summary",
          "write_report",
          "write_summary"
        ],
        "imports": [
          "__future__",
          "argparse",
          "bisect",
          "collections",
          "dataclasses",
          "hashlib",
          "json",
          "math",
          "pathlib",
          "scripts",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "47e5a7de552461639eb3c8959bfaa980e01f087bd108ae793527eb4783453f87",
      "size_bytes": 51762,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_lane1_remaining_methodology_triage.py",
      "ast_status": "PARSED",
      "parser_code_hash": "8a6010bef9a037a8c34a45eafea0bc59f94c3404fbb1c684eb421dd7a13d0946",
      "path": "scripts/analyze_lane1_remaining_methodology_triage.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_lane1_remaining_methodology_triage.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "aggregate_fold_auc_diffs",
          "build_parser",
          "build_payload",
          "extract_path_diffs",
          "extract_v4_architecture_diffs",
          "finite",
          "fmt_float",
          "fold_ranges",
          "load_json",
          "locate_47_cell_panel_candidates",
          "main",
          "summarize_lift_series",
          "table",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "json",
          "math",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "schema_version": true
        }
      },
      "shape_fingerprint": "babdef66b2f63f1a6e955d676d79205d58d5477f2738e2951e0ef5345e0e0c22",
      "size_bytes": 21354,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_lane2_c7_c9_path_scaling_triage.py",
      "ast_status": "PARSED",
      "parser_code_hash": "87483a25d7008038fa0f5ee95f0dcdb44c366b9b9d3bbe3970a4cb42b46f0fd3",
      "path": "scripts/analyze_lane2_c7_c9_path_scaling_triage.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_lane2_c7_c9_path_scaling_triage.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "aggregate_fold_auc_diffs",
          "build_parser",
          "build_payload",
          "finite",
          "fmt_float",
          "fold_ranges",
          "load_json",
          "main",
          "path_diff_summary",
          "rel",
          "summarize_c9",
          "summarize_path9",
          "table",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "json",
          "math",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "schema_version": true
        }
      },
      "shape_fingerprint": "4db5f3ba3e16790baa31c2c99a36fa150b9d552f4c66b9976dc27542137cde1b",
      "size_bytes": 21396,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_lane3_execution_telemetry_verifiers.py",
      "ast_status": "PARSED",
      "parser_code_hash": "bc16605c5207cb0e369da81f2d6936a0a5c9cef765960e25e762e6a16841d5a7",
      "path": "scripts/analyze_lane3_execution_telemetry_verifiers.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_lane3_execution_telemetry_verifiers.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "build_parser",
          "build_payload",
          "fmt",
          "main",
          "rel",
          "table",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "schema_version": true
        }
      },
      "shape_fingerprint": "5326a67917e0dab25d954d13b66ad4818db136707e209a18b65e2da29ee314d9",
      "size_bytes": 8884,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_lane4_options_proxy_triage.py",
      "ast_status": "PARSED",
      "parser_code_hash": "eb3ce0eb2e4cbaa24050af92fde3c0da33c238ccfa305a540304ba2d2772b173",
      "path": "scripts/analyze_lane4_options_proxy_triage.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_lane4_options_proxy_triage.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_fmt",
          "_iter_jsonl",
          "_read_json",
          "_safe_rel",
          "_series_tokens_from_status",
          "build_parser",
          "build_payload",
          "classify_tasks",
          "detect_external_data_terms",
          "load_flashalpha_inventory",
          "load_fred_inventory",
          "main",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "typing"
        ],
        "markers": {
          "as_of": true,
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "85aab81141b2fd0a5ab26e4ce05912e79da271da0e5cba9aa3a3856717771bf5",
      "size_bytes": 16334,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_lane5_architecture_system_flow_triage.py",
      "ast_status": "PARSED",
      "parser_code_hash": "3292fa3a72c2e756a1c806aa83ea83e1512cd2680b5ce0898877b50dc3a454fb",
      "path": "scripts/analyze_lane5_architecture_system_flow_triage.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_lane5_architecture_system_flow_triage.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_read_json",
          "_safe_rel",
          "build_parser",
          "build_payload",
          "classify_tasks",
          "load_evidence",
          "main",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "typing"
        ],
        "markers": {
          "schema_version": true
        }
      },
      "shape_fingerprint": "8852e6836295b45244cc2662fcbae3a22a8b4932b68a7b03080258c248e8f446",
      "size_bytes": 14130,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_lane5_data_source_triage.py",
      "ast_status": "PARSED",
      "parser_code_hash": "4cbfc3702ec582fd6f056f826768cc9bc2044127b2694bc3f8cb2d7d352084cc",
      "path": "scripts/analyze_lane5_data_source_triage.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_lane5_data_source_triage.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_iter_jsonl",
          "_read_json",
          "_safe_rel",
          "build_parser",
          "build_payload",
          "cftc_inventory",
          "classify_tasks",
          "history_availability_inventory",
          "lbma_inventory",
          "main",
          "source_text_contains",
          "tick_inventory",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "parquet": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "548525315f4083bfc96f305ed84a64f38b97c0ea39875825a8e8bf713652e63f",
      "size_bytes": 18288,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_lane5_k54_architecture_triage.py",
      "ast_status": "PARSED",
      "parser_code_hash": "adae998f3f4fd8b4310ba8599f6199f61a83a174c95674b3c702c8c87778c379",
      "path": "scripts/analyze_lane5_k54_architecture_triage.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_lane5_k54_architecture_triage.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_gate_summary",
          "_read_json",
          "_safe_rel",
          "_variant_auc",
          "build_parser",
          "build_payload",
          "classify_tasks",
          "load_evidence",
          "main",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "typing"
        ],
        "markers": {
          "schema_version": true
        }
      },
      "shape_fingerprint": "32159ff2331115cc8580983dbe14228e4046fa352470649c13b5f7f505364871",
      "size_bytes": 21953,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_lane5_remaining_arch_ml_quality_triage.py",
      "ast_status": "PARSED",
      "parser_code_hash": "eb5210a5c911be74e9b3dc825f51ba562ce0d273da8e4357b0f0d9a4f8926498",
      "path": "scripts/analyze_lane5_remaining_arch_ml_quality_triage.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_lane5_remaining_arch_ml_quality_triage.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_read_json",
          "_read_text",
          "build_evidence",
          "build_parser",
          "build_payload",
          "classify_tasks",
          "data_source_evidence",
          "k54_evidence",
          "k55_ticket_evidence",
          "literature_evidence",
          "main",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "typing"
        ],
        "markers": {
          "schema_version": true
        }
      },
      "shape_fingerprint": "a60c85e557f338b3d74d684609a8c32749533cd1186010d18a57ac8879ec3869",
      "size_bytes": 20595,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_lane5_remaining_data_feed_triage.py",
      "ast_status": "PARSED",
      "parser_code_hash": "fff38ffe76097b5e13153a782a151e192d59ecd04461a5b0d3f5b42bb95cf6a5",
      "path": "scripts/analyze_lane5_remaining_data_feed_triage.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_lane5_remaining_data_feed_triage.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_iter_jsonl",
          "_read_json",
          "_safe_rel",
          "build_parser",
          "build_payload",
          "classify_tasks",
          "external_source_presence",
          "fred_inventory",
          "main",
          "normalized_inventory",
          "status_inventory",
          "tick_probe_inventory",
          "wgc_inventory",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "61dfd60a382581a385411bbdd06ffb8904502afc53ea4b60546a0d6bcb41766b",
      "size_bytes": 15930,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_lane6_asset_risk_edge_triage.py",
      "ast_status": "PARSED",
      "parser_code_hash": "07a458d32f8a7dac0b63627b7d77c0a0a3ed2c95df4bb5cdf82f816e8fc4dbda",
      "path": "scripts/analyze_lane6_asset_risk_edge_triage.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_lane6_asset_risk_edge_triage.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_float_or_none",
          "_latest_jsonl_for_series",
          "_line_count",
          "_near_round",
          "_read_json",
          "_read_text",
          "_round_unit",
          "build_evidence",
          "build_parser",
          "build_payload",
          "classify_tasks",
          "data_source_evidence",
          "external_feed_evidence",
          "k54_osler_evidence",
          "main",
          "production_trade_level_evidence",
          "regime_feature_evidence",
          "retail_flow_evidence",
          "vol_feature_evidence",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "csv",
          "datetime",
          "json",
          "math",
          "pathlib",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "cc3eb1611b0fcb940327a299dd78b64aef70a7234af7d48501af9304eacd9064",
      "size_bytes": 25211,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_lane6_priority620_triage.py",
      "ast_status": "PARSED",
      "parser_code_hash": "11c2bf2d90d72e2d193edf15c5a0d1d30b78bc5c40bd0d261a257d131bae027d",
      "path": "scripts/analyze_lane6_priority620_triage.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_lane6_priority620_triage.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "build_evidence",
          "build_payload",
          "cftc_inventory",
          "classifications",
          "count_jsonl_dir",
          "feature_stability_inventory",
          "flashalpha_inventory",
          "fred_series",
          "hpm_inventory",
          "inverted_tp_inventory",
          "latest_file",
          "lbma_inventory",
          "load_json",
          "main",
          "markdown_table",
          "read_jsonl",
          "render_markdown",
          "write_outputs"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "78400cbb2efaaa82d4cdab444648c83101d7091549a9874d6eb26b91b1659a41",
      "size_bytes": 25114,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_lane6_tail_triage.py",
      "ast_status": "PARSED",
      "parser_code_hash": "519b7f2fc1a80c2b01790e549ed967ea1576983f6bce4cd2a2d72d4ec6ad27d9",
      "path": "scripts/analyze_lane6_tail_triage.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_lane6_tail_triage.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "ai_tooling_inventory",
          "build_payload",
          "classifications",
          "count_latest_jsonl",
          "estimate_rough_vol_hurst",
          "evidence_inventory",
          "hpm_inventory",
          "latest_file",
          "load_close_frame",
          "load_json",
          "main",
          "markdown_table",
          "read_jsonl",
          "render_markdown",
          "rough_hurst_inventory",
          "source_inventory",
          "tail_correlation_inventory",
          "tick_inventory",
          "wgc_inventory",
          "write_outputs"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "csv",
          "datetime",
          "json",
          "math",
          "numpy",
          "pandas",
          "pathlib",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "parquet": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "f450a91d58e25ce91d3371563803903b9226d641ab6ef1851ebb918f3eb0a7c7",
      "size_bytes": 29672,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_lane7_open_questions_triage.py",
      "ast_status": "PARSED",
      "parser_code_hash": "a1b06a400bc03d8af84cf08dc91af5da2dae065985e6c6b0a77db9f7ab3d5a71",
      "path": "scripts/analyze_lane7_open_questions_triage.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_lane7_open_questions_triage.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "ai_scaffold_inventory",
          "build_payload",
          "decay_inventory",
          "dsr_inventory",
          "fred_month_summary",
          "k54_inventory",
          "lambda_scan",
          "latest_file",
          "load_json",
          "main",
          "path9_inventory",
          "quantum_inventory",
          "read_csv",
          "read_jsonl",
          "source_inventory",
          "task_classifications",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "csv",
          "datetime",
          "json",
          "pathlib",
          "re",
          "statistics",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "0c7a01e1753af862e3a5af8ee522a09e1aa0089bedeb845b165dde8cb26e28e0",
      "size_bytes": 23467,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_methodology_infrastructure_gate.py",
      "ast_status": "PARSED",
      "parser_code_hash": "68686424d6581a8cc59509ba70558a87ff46cb786100da8cdce8438d31c97d6e",
      "path": "scripts/analyze_methodology_infrastructure_gate.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_methodology_infrastructure_gate.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "audit_k54_v2",
          "audit_k54_v3",
          "audit_k54_v4",
          "audit_phase3_diagnostics",
          "audit_q1_dlinear",
          "build_parser",
          "build_payload",
          "dsr_row",
          "fmt",
          "hardening_gate",
          "load_json",
          "main",
          "summarize_weighted_se_from_paths",
          "table",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "schema_version": true
        }
      },
      "shape_fingerprint": "9a3b7b3ce69ff52b86abe0e1065340eb71996ce30bd9d319a596a43036ee7009",
      "size_bytes": 16546,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_orderflow_asof_symbol_diagnostics.py",
      "ast_status": "PARSED",
      "parser_code_hash": "46d9a98b7eb50e8c6b1e807c55b2a0dcef5e35d80c42217c83ac16ae2a36b2b4",
      "path": "scripts/analyze_orderflow_asof_symbol_diagnostics.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_orderflow_asof_symbol_diagnostics.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_bool_rate",
          "_fmt",
          "_numeric_median",
          "build_parser",
          "build_payload",
          "build_readout",
          "candidate_context_by_symbol",
          "load_json",
          "main",
          "outcome_by_symbol",
          "summarize_bucket",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "schema_version": true
        }
      },
      "shape_fingerprint": "6b471fe29bfdf7025adc5d41e4e329adbefe99e1cdf318d163e9e70375f7e164",
      "size_bytes": 14010,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_orderflow_depth_mbp10_features.py",
      "ast_status": "PARSED",
      "parser_code_hash": "713814b1827a22a01294f69b2a7c1680fae83c67273df8689e9d0d227619d55c",
      "path": "scripts/analyze_orderflow_depth_mbp10_features.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_orderflow_depth_mbp10_features.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_fmt",
          "_safe_float",
          "_sign_change_rate",
          "add_ladder_columns",
          "build_feature_rows",
          "build_parser",
          "build_payload",
          "build_readout",
          "candidate_context_by_symbol",
          "compute_event_ladder_features",
          "is_primary_proxy",
          "ladder_stats",
          "load_databento_mbp10_sampled",
          "main",
          "outcome_by_symbol",
          "summarize_bucket",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "databento",
          "json",
          "numpy",
          "pandas",
          "pathlib",
          "scripts",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "schema_version": true
        }
      },
      "shape_fingerprint": "7cc5c93d82adf5707ff43328c6b9c3fe9755143fa349c12bfbf7a85ab670508f",
      "size_bytes": 24382,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_orderflow_depth_mbp1_features.py",
      "ast_status": "PARSED",
      "parser_code_hash": "641d805ed84e1e25f7219bfb830598948da2e65d60ff759cb7ad256422e3d629",
      "path": "scripts/analyze_orderflow_depth_mbp1_features.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_orderflow_depth_mbp1_features.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_fmt",
          "_group_fetch_paths",
          "_safe_float",
          "_sign_change_rate",
          "attach_outcomes",
          "build_feature_rows",
          "build_parser",
          "build_payload",
          "build_readout",
          "candidate_context_by_symbol",
          "candidate_key",
          "compute_event_depth_features",
          "depth_stats",
          "index_outcome_rows",
          "is_primary_proxy",
          "load_databento_mbp1",
          "load_json",
          "main",
          "normalize_symbol",
          "outcome_by_symbol",
          "slice_window",
          "summarize_bucket",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "databento",
          "json",
          "math",
          "numpy",
          "pandas",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "schema_version": true
        }
      },
      "shape_fingerprint": "77a6f36f5fb15152e2bf4c6837f8a61267020b0650635f2d9c26ea8f25eebe3b",
      "size_bytes": 23248,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_orderflow_event_features.py",
      "ast_status": "PARSED",
      "parser_code_hash": "827f6d4d27d2f5485fa67fb5695c0f1f292a1368245c8e0481b70cb6a9cf8138",
      "path": "scripts/analyze_orderflow_event_features.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_orderflow_event_features.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_fmt",
          "_summary",
          "build_parser",
          "build_payload",
          "load_json",
          "main",
          "summarize_rows",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "schema_version": true
        }
      },
      "shape_fingerprint": "4a76d1fce1bfdd52475db951b78fa986090008fd72f080f387e69d976c23949e",
      "size_bytes": 11949,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_orderflow_mbo_nas100_features.py",
      "ast_status": "PARSED",
      "parser_code_hash": "09b38cdef35e45366bbd546d3a49affda9262ddb865a74041c211174bed25edf",
      "path": "scripts/analyze_orderflow_mbo_nas100_features.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_orderflow_mbo_nas100_features.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [
          "OrderBook",
          "WindowAccumulator",
          "WindowTracker"
        ],
        "functions": [
          "__init__",
          "__init__",
          "__init__",
          "_action",
          "_add_book",
          "_fmt",
          "_median",
          "_near10",
          "_recompute_best",
          "_remove_book",
          "_safe_float",
          "_side",
          "add_action",
          "add_sample",
          "advance",
          "append_effects",
          "append_snapshot",
          "apply_row",
          "best_ask",
          "best_bid",
          "build_feature_rows",
          "build_parser",
          "build_payload",
          "build_readout",
          "build_windows",
          "candidate_context",
          "clear",
          "finalize_window",
          "load_json",
          "load_mbo_features_for_group",
          "main",
          "outcome",
          "side_stats",
          "snapshot",
          "summarize_bucket",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "databento",
          "json",
          "math",
          "numpy",
          "pandas",
          "pathlib",
          "scripts",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "schema_version": true
        }
      },
      "shape_fingerprint": "6d9b598220c3e901e34f76ef14992f63c5bc3163e1eab41777e1f81800af503b",
      "size_bytes": 36964,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_orderflow_nas100_cached_feature_forensics.py",
      "ast_status": "PARSED",
      "parser_code_hash": "354d3d88c8900f5d8c7242945125b3f03d7306ad46499602e7f1a5a9122c8eef",
      "path": "scripts/analyze_orderflow_nas100_cached_feature_forensics.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_orderflow_nas100_cached_feature_forensics.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "build_parser",
          "build_payload",
          "candidate_rows",
          "concentration",
          "context_rows",
          "count_share",
          "event_date",
          "event_hour",
          "feature_forensics",
          "fmt",
          "forward_feature_families",
          "label_coverage",
          "leave_one_candidate_event",
          "leave_one_date",
          "load_json",
          "main",
          "median",
          "median_delta",
          "ok_nas100_rows",
          "outcome_delta",
          "runtime_diagnostics",
          "safe_float",
          "sign",
          "table",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "math",
          "pathlib",
          "statistics",
          "typing"
        ],
        "markers": {
          "schema_version": true
        }
      },
      "shape_fingerprint": "a30c883d82ba3466a39282b13e930aee083d821360bd98be18f1d285f1fa13d4",
      "size_bytes": 23252,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_orderflow_proxy_mapping_weekend_forensics.py",
      "ast_status": "PARSED",
      "parser_code_hash": "c0941587cf638e7ee5f044c4d23e1fa158271a487bc4a0026b1018ecdb8eda08",
      "path": "scripts/analyze_orderflow_proxy_mapping_weekend_forensics.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_orderflow_proxy_mapping_weekend_forensics.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "all_window_metrics",
          "build_parser",
          "build_payload",
          "fmt",
          "gbpjpy_feasibility",
          "load_json",
          "main",
          "median",
          "next_unresolved_symbol",
          "pair_status",
          "priority_status",
          "safe_float",
          "selected_diag",
          "table",
          "validation_window_lookup",
          "weak_window_forensics",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "json",
          "math",
          "pathlib",
          "statistics",
          "typing"
        ],
        "markers": {
          "schema_version": true
        }
      },
      "shape_fingerprint": "fc3c119ffcf2a58a8eae426e4317481761498bf50039a0638a6a9dc853ff43e7",
      "size_bytes": 17382,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_phase3_methodology_diagnostics.py",
      "ast_status": "PARSED",
      "parser_code_hash": "4bee0a891a363ea5b99a40bdd25981a2336d4e67008a01cd6a39824af827b430",
      "path": "scripts/analyze_phase3_methodology_diagnostics.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_phase3_methodology_diagnostics.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "analyze_claim",
          "build_parser",
          "build_payload",
          "diagnostic_policy",
          "dsr_reference_summary",
          "fmt",
          "load_json_if_exists",
          "main",
          "promotion_verdict_from_artifact",
          "stale_ledger_diagnostics",
          "table",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "json",
          "pathlib",
          "re",
          "typing"
        ],
        "markers": {
          "schema_version": true
        }
      },
      "shape_fingerprint": "2ef4afc1c38d61caa1a4e19a2fec4b0ce178b9f0e101c589e4fdc5a561b35671",
      "size_bytes": 14741,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_q13_cpcv_bias_variance.py",
      "ast_status": "PARSED",
      "parser_code_hash": "2f075d6e896eb4cdf5615b106fcecbc52738db97a29473eb3f4a27741b9a2e12",
      "path": "scripts/analyze_q13_cpcv_bias_variance.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_q13_cpcv_bias_variance.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "build_parser",
          "build_payload",
          "decompose_path_variance",
          "fixed_hp_path_diffs",
          "fmt",
          "load_json",
          "loo_influence",
          "main",
          "table",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "json",
          "math",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "schema_version": true
        }
      },
      "shape_fingerprint": "851cfdd5e2c9e62db46314eb442c10a35e102634434dbde9ebbc2cd39b715399",
      "size_bytes": 13057,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_raw_ohlc_path_ablation_v1_disposition.py",
      "ast_status": "PARSED",
      "parser_code_hash": "15d877d554a49b0b55e2a973d33cf5a38e5d1b815b5bb189a32711f522567f9d",
      "path": "scripts/analyze_raw_ohlc_path_ablation_v1_disposition.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_raw_ohlc_path_ablation_v1_disposition.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "add",
          "ambiguity_ledger",
          "best_lock_delta",
          "best_variant",
          "build_parser",
          "closed_questions",
          "cohort_best_rows",
          "coverage_subset_group_delta_rows",
          "coverage_subset_variant_rows",
          "direct_answers",
          "find_group_delta",
          "flatten_samebar_rows",
          "load_events",
          "main",
          "net_mean",
          "net_sum",
          "new_state",
          "next_steps",
          "render_report",
          "run_disposition_analysis",
          "samebar_breakdown",
          "summarize",
          "synthesis",
          "treated_value",
          "treatment_group_delta_rows",
          "treatment_variant_rows",
          "write_outputs"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "scripts",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "5f504cf8b515bb33e088626785254c9c92574d8c870a5ca6cf632fb75ef83c52",
      "size_bytes": 29302,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_raw_ohlc_path_ablation_v1_failure_forensics.py",
      "ast_status": "PARSED",
      "parser_code_hash": "4ce2bccef17c36e3d09a2de5b58929c70af47fe56a56b03844817e9eeea7a3d6",
      "path": "scripts/analyze_raw_ohlc_path_ablation_v1_failure_forensics.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_raw_ohlc_path_ablation_v1_failure_forensics.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [
          "MfeStats",
          "PairStats"
        ],
        "functions": [
          "__post_init__",
          "add",
          "add_j46",
          "ambiguity_ledger",
          "as_float",
          "bucket_value",
          "build_parser",
          "casebook_pair_row",
          "casebook_rows",
          "classify_mechanism",
          "cohort_pair_rows",
          "deeper_dive_candidates",
          "direct_answers",
          "find_mfe_row",
          "find_pair_row",
          "find_stress_row",
          "find_variant_row",
          "groups_for_row",
          "limitations",
          "load_events",
          "lock_steps_summary",
          "main",
          "mechanism_summary_rows",
          "mfe_opportunity_stats",
          "mfe_rows",
          "mtf_resolution_rows",
          "next_steps",
          "opened_questions",
          "outcome_transition_counts",
          "pairwise_failure_stats",
          "pairwise_group_rows",
          "pairwise_timeframe_rows",
          "pairwise_variant_rows",
          "pivot_events",
          "quantile",
          "render_casebook",
          "render_report",
          "resolved_value",
          "root_cause_summary",
          "round_optional",
          "row",
          "row",
          "run_failure_forensics",
          "samebar_stress_delta_rows",
          "synthesis",
          "top_cohort_rows",
          "transition_rows",
          "unanswered_questions_status",
          "unresolved_pair_rows",
          "value_for_treatment",
          "variant_outcome_rows",
          "what_failed",
          "what_worked",
          "write_outputs"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "dataclasses",
          "datetime",
          "json",
          "math",
          "pathlib",
          "scripts",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "6c076515d90989b80689034f931aeb8d8c8a365afb5faf9991815ea905c3946e",
      "size_bytes": 67735,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_raw_ohlc_path_scaling_v2_confluence.py",
      "ast_status": "PARSED",
      "parser_code_hash": "c63da2cc65a17badf8cbd9b54f72b82353f2f837a652a2375627a85ffbe9110b",
      "path": "scripts/analyze_raw_ohlc_path_scaling_v2_confluence.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_raw_ohlc_path_scaling_v2_confluence.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_absolute_bucket",
          "_bucket_table",
          "_composite_bucket",
          "_entry_tuple",
          "_fire_bucket",
          "_improvement_bucket",
          "_sequence_bucket",
          "_variant_stats",
          "bucket_summary",
          "build_event_profiles",
          "build_parser",
          "build_payload",
          "event_profile",
          "first_lock",
          "fmt",
          "load_event_rows",
          "lock_summary",
          "main",
          "mean",
          "net_r",
          "parse_utc",
          "sequence_summary",
          "slice_summary",
          "table",
          "top_examples",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "sys",
          "typing"
        ],
        "markers": {
          "as_of": true,
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "ed806d751a784028533cd3dd9b78f1dec0af2026bd3658f9b9b5ee3fed4b4801",
      "size_bytes": 32708,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_raw_ohlc_path_scaling_v2_confluence_deepdive.py",
      "ast_status": "PARSED",
      "parser_code_hash": "35d317a540eaeeed2f315776d2a2492e4306b2cbb5c13681588fd9352d4c8c46",
      "path": "scripts/analyze_raw_ohlc_path_scaling_v2_confluence_deepdive.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_raw_ohlc_path_scaling_v2_confluence_deepdive.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "as_float",
          "bucket_deep_dive",
          "build_casebooks",
          "build_parser",
          "build_payload",
          "case_row",
          "case_rows",
          "composite_arbitration",
          "concentration",
          "concentration_panel",
          "concentration_rows",
          "delta",
          "enrich_event",
          "fire_bucket",
          "first_lock_delta",
          "fmt",
          "group_by",
          "group_rows",
          "improvement_bucket",
          "leave_one_rows",
          "leave_one_stress",
          "load_events",
          "main",
          "mean",
          "parse_cohort",
          "sequence_bucket",
          "sequence_stats",
          "sign_flip",
          "slice_metrics",
          "sum_round",
          "synthesize",
          "table",
          "top_cases",
          "value",
          "variant_stats",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "scripts",
          "sys",
          "typing"
        ],
        "markers": {
          "schema_version": true
        }
      },
      "shape_fingerprint": "df60358e9ad641cad082553ef6701d5fe874d1131847a1acdf15dab8c464117f",
      "size_bytes": 43349,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_raw_ohlc_path_scaling_v2_selector_forensics.py",
      "ast_status": "PARSED",
      "parser_code_hash": "93f0849543f98a38d297a7ff2099f309be4f43cb0582290bd3bd104effa9ae01",
      "path": "scripts/analyze_raw_ohlc_path_scaling_v2_selector_forensics.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_raw_ohlc_path_scaling_v2_selector_forensics.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_fmt",
          "_group_lookup",
          "_sum_positive_group_delta",
          "_table",
          "build_parser",
          "build_payload",
          "cleanliness",
          "decision_readout",
          "load_event_rows",
          "main",
          "pair_rows_for_variant",
          "parse_utc",
          "stats_by_year",
          "stats_from_rows",
          "variant_profile",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "scripts",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "2d8b18f74cba5cef4488842479d96a8577a75a318a389af24165b27c07d67eae",
      "size_bytes": 15511,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_raw_ohlc_path_scaling_v3_exploratory.py",
      "ast_status": "PARSED",
      "parser_code_hash": "678befc480eceba4b7c68cfda77a6fa7cc20d990e4b1449969a57611a9781f46",
      "path": "scripts/analyze_raw_ohlc_path_scaling_v3_exploratory.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_raw_ohlc_path_scaling_v3_exploratory.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [
          "RiskBankPlan"
        ],
        "functions": [
          "aggregate_worst_case_r",
          "build_parser",
          "build_payload",
          "build_records",
          "casebook",
          "classify_same_row_fill_exit",
          "completed_leg_cost",
          "contribution_concentration",
          "dimension_summary",
          "event_quarter",
          "event_year",
          "finalized_unfilled_pending",
          "first_lock",
          "fmt",
          "group_by",
          "hit_reentry",
          "hit_stop",
          "hit_target",
          "load_events",
          "load_variant_spec",
          "main",
          "max_new_leg_size",
          "mean",
          "median",
          "methodology_diagnostics",
          "net_r",
          "normal_approx_p_value",
          "percentile",
          "plan_new_leg",
          "price_from_r",
          "r_distance",
          "r_from_price",
          "replay_variant_event",
          "selected_rows_after_lock",
          "sequence_bucket",
          "side_sign",
          "simulate_reentry_leg",
          "table",
          "taxonomy",
          "taxonomy_summary",
          "variant_lock_for_event",
          "variant_summary",
          "write_casebook",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "dataclasses",
          "datetime",
          "json",
          "math",
          "pathlib",
          "scripts",
          "statistics",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "5abb5e7f311c51119c07733e2f1681287c96b1dedfac78973c5a25ecdab82376",
      "size_bytes": 42583,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_raw_ohlc_replay_followups.py",
      "ast_status": "PARSED",
      "parser_code_hash": "8e6ab7266205b45efd40e2f36e9d5d8f76e677527556c8bae3f153afd1a34f7e",
      "path": "scripts/analyze_raw_ohlc_replay_followups.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_raw_ohlc_replay_followups.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [
          "ReturnStats"
        ],
        "functions": [
          "add_event",
          "ambiguity_ledger",
          "analyze_raw_ohlc_replay_followups",
          "as_float",
          "build_cohort_recency_rows",
          "build_cohort_rows",
          "build_group_rows",
          "build_parser",
          "build_window_rows",
          "cohort_status_read",
          "combine_periods",
          "dominant_outcome",
          "dsr_fields",
          "effective_n_diagnostic",
          "family_matrix",
          "groups_for_key",
          "is_scoring_population",
          "iter_jsonl",
          "latest_file",
          "main",
          "matrix_for_keys",
          "mean_or_none",
          "next_steps",
          "parse_event_time",
          "pbo_diagnostic",
          "pbo_variant",
          "pbo_variant_report_rows",
          "period_row",
          "rate_or_none",
          "recency_interpretation",
          "recency_windows",
          "render_report",
          "resolved_return",
          "row",
          "share_or_none",
          "source_scope",
          "synthesis_answers",
          "target_control_separation",
          "write_outputs"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "dataclasses",
          "datetime",
          "json",
          "math",
          "numpy",
          "pathlib",
          "scripts",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "a78953818db6f62d85a92b8124a2013ee6c8f319fa11b122f46342314d74b536",
      "size_bytes": 43555,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_truth_layer_cohort_stability.py",
      "ast_status": "PARSED",
      "parser_code_hash": "425bd38e59db1d4ffbb177ee98e1ace39538bbcecf71983eec2887a37e3c2065",
      "path": "scripts/analyze_truth_layer_cohort_stability.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_truth_layer_cohort_stability.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [
          "CohortSpec",
          "RunningStats"
        ],
        "functions": [
          "_add_row_to_state",
          "_ambiguity_rows",
          "_as_float",
          "_as_int",
          "_classify_treatment",
          "_format_signed",
          "_has_lower_tf_gap",
          "_is_ambiguous_outcome",
          "_is_resolution_safe",
          "_is_setup_row",
          "_markdown_cell",
          "_markdown_table",
          "_mean",
          "_new_cohort_state",
          "_parse_datetime",
          "_period_for_year",
          "_period_rows",
          "_priority_rows",
          "_rate",
          "_render_cohort_detail",
          "_round",
          "_row_cohort_key",
          "_row_year",
          "_scope_summary_rows",
          "_selected_exit_time",
          "_selected_first_gap_time",
          "_selected_gap_count",
          "_selected_gap_timing",
          "_short_slug",
          "_stability_summary",
          "_summarize_state",
          "_synthesis_bullets",
          "_utc_now",
          "_year_stability_rows",
          "add",
          "analyze_cohort_stability",
          "build_parser",
          "find_latest_input",
          "from_mapping",
          "iter_jsonl",
          "load_cohort_specs",
          "main",
          "parse_cohort_key",
          "render_report",
          "to_row",
          "write_report",
          "write_summary"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "dataclasses",
          "datetime",
          "hashlib",
          "json",
          "math",
          "pathlib",
          "re",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "38d29d03a3b1a4743b2b61593175d4d47ce9a8d7b621994b83b8e837c315f949",
      "size_bytes": 41079,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_truth_layer_effective_n.py",
      "ast_status": "PARSED",
      "parser_code_hash": "4ad87b9d25f5cfde7e2c518477d6d8eb5817246ea89ad06b6100f3e624757efd",
      "path": "scripts/analyze_truth_layer_effective_n.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_truth_layer_effective_n.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_effective_n_row",
          "_markdown_cell",
          "_markdown_table",
          "_promotion_usable_reason",
          "analyze_effective_n",
          "average_pairwise_correlations",
          "build_parser",
          "build_return_matrix",
          "candidate_activity_rows",
          "effective_n_diagnostics",
          "effective_n_participation_ratio",
          "load_matrix_registry",
          "main",
          "render_report",
          "select_columns",
          "write_outputs"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "math",
          "numpy",
          "pathlib",
          "scripts",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "b961e76d68a27ffef88f4ff71d545aeb17daad32187bdb7b7c9a017a33eaf12c",
      "size_bytes": 18565,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_truth_layer_matrix_followup_dominance.py",
      "ast_status": "PARSED",
      "parser_code_hash": "c715662def3a92aec331b2a0b904428f52a744a75a783a2d50cda0f5a128f5c9",
      "path": "scripts/analyze_truth_layer_matrix_followup_dominance.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_truth_layer_matrix_followup_dominance.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [
          "Stats"
        ],
        "functions": [
          "_mean",
          "_rate",
          "_round",
          "add",
          "add_cohort_key",
          "add_row",
          "analyze_matrix_followup_dominance",
          "audit_blockers",
          "audit_status",
          "build_parser",
          "compact_cohort_rows",
          "exclude_period",
          "load_followup_spec",
          "main",
          "markdown_table",
          "new_state",
          "next_action",
          "next_session_recommendation",
          "render_report",
          "row",
          "summarize_cohort",
          "summarize_families",
          "top_n_months",
          "write_outputs"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "dataclasses",
          "datetime",
          "json",
          "pathlib",
          "scripts",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "f9360e7483604c199aff6779966ff8194c2eda5b7cd751b88ea64f9f7b9ce161",
      "size_bytes": 21334,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\analyze_truth_layer_posthoc_pbo.py",
      "ast_status": "PARSED",
      "parser_code_hash": "ac52c193ca920c61f2d9b731a817175edb245cdfdcfef7ac28f686daaf629d54",
      "path": "scripts/analyze_truth_layer_posthoc_pbo.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/analyze_truth_layer_posthoc_pbo.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_add_resolved",
          "_balanced_subperiods",
          "_build_period_matrix",
          "_choose_subperiod_count",
          "_cohort_summary",
          "_markdown_cell",
          "_markdown_table",
          "_mean",
          "_new_period",
          "_new_state",
          "_new_year",
          "_primary_rows",
          "_row_month",
          "_utc_now",
          "analyze_posthoc_pbo",
          "build_parser",
          "cscv_pbo",
          "main",
          "render_report",
          "write_outputs"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "itertools",
          "json",
          "math",
          "pathlib",
          "scripts",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "eae01e3577839da9d67e16c2781a0d5ea589e4f4334be867506924823fd44b75",
      "size_bytes": 22004,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\audit_canary_restart_governance.py",
      "ast_status": "PARSED",
      "parser_code_hash": "3c1e446a888dbea62c272df809266d1c91a45ba70cbdb556b15d453503027c6d",
      "path": "scripts/audit_canary_restart_governance.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/audit_canary_restart_governance.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "append_jsonl_once",
          "build_report",
          "main",
          "read_jsonl",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "af6f06a9f19f0fd59530e2cc1636bcbc012132b120f1ee423748497ca84bdecc",
      "size_bytes": 7771,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\audit_databento_live_trigger_policy.py",
      "ast_status": "PARSED",
      "parser_code_hash": "07f3dbd5a6ab2805f2fbfd9cad89c76d590cd37ee728beb503e04a107053fc41",
      "path": "scripts/audit_databento_live_trigger_policy.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/audit_databento_live_trigger_policy.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "build_parser",
          "build_report",
          "counter",
          "main",
          "read_jsonl",
          "write_outputs"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "os",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "f5e708afa5fcd7da3a562585ef23b89f120c8f0e99259517f757b0a0fb824cfc",
      "size_bytes": 6820,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\audit_es_mes_preregistration.py",
      "ast_status": "PARSED",
      "parser_code_hash": "9f71667447f00dac6ee5557f990bbad4b01dc9226aae94b516c147104902f3d5",
      "path": "scripts/audit_es_mes_preregistration.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/audit_es_mes_preregistration.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "append_status_row_if_missing",
          "main",
          "read_json",
          "read_jsonl_with_lines",
          "write_json"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "0d9a55e8c84257b1445569c626112d15badc8acfd6c368f0117198a2f4dea063",
      "size_bytes": 5569,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\audit_expanded_oos_replay_portability.py",
      "ast_status": "PARSED",
      "parser_code_hash": "77540c2d3da0c2a9b91a100b75651f9cb98d1a6139396cc44e4d1abf0a6ea0f0",
      "path": "scripts/audit_expanded_oos_replay_portability.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/audit_expanded_oos_replay_portability.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [
          "ToolSpec"
        ],
        "functions": [
          "audit_tool",
          "build_parser",
          "build_payload",
          "extract_cli_args",
          "fmt",
          "main",
          "rel",
          "table",
          "utc_now",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "dataclasses",
          "datetime",
          "json",
          "pathlib",
          "re",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true,
          "scid": true
        }
      },
      "shape_fingerprint": "1dff90c31852517500bc2f089688e7032eb43b8a7941704937a07db468418e2b",
      "size_bytes": 16644,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\audit_futures_proxy_expansion_validation.py",
      "ast_status": "PARSED",
      "parser_code_hash": "d87723aceed6c1e4f16a9a442d51a6c14ca465b509154900afefa18e05f48618",
      "path": "scripts/audit_futures_proxy_expansion_validation.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/audit_futures_proxy_expansion_validation.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_fmt",
          "_table",
          "blocking_reasons",
          "build_parser",
          "build_payload",
          "estimate_cost",
          "load_json",
          "main",
          "pair_key",
          "status_for",
          "summarize_pairs",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "json",
          "pathlib",
          "statistics",
          "typing"
        ],
        "markers": {
          "schema_version": true
        }
      },
      "shape_fingerprint": "5b589f65ae396df0c190e165e8c642007e5426302203d37a6a2056fac39bbb71",
      "size_bytes": 14844,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\audit_gbpjpy_orderflow_proxy_gap.py",
      "ast_status": "PARSED",
      "parser_code_hash": "57353db196e88db114a479c0306d8c3faba4aa9f2439c1b31f5a143345d6690f",
      "path": "scripts/audit_gbpjpy_orderflow_proxy_gap.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/audit_gbpjpy_orderflow_proxy_gap.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_file_hash",
          "_safe_float",
          "append_status_rows_if_missing",
          "build_parser",
          "build_price_transfer_diagnostic",
          "build_report",
          "build_status_row",
          "fmt",
          "latest_by_candidate",
          "load_ohlcv_series",
          "main",
          "parse_dt",
          "pearson",
          "pre_registered_tests",
          "proxy_designs",
          "read_jsonl",
          "session_bucket",
          "source_signature",
          "table",
          "utc_now_iso",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "csv",
          "datetime",
          "hashlib",
          "json",
          "math",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "no_leak": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "107828a8d2747b497f33695d6a0ce5e2c43deba7ccdf69204d819027239cedee",
      "size_bytes": 32261,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\audit_limitations_to_opportunities_completion.py",
      "ast_status": "PARSED",
      "parser_code_hash": "571575b43183b4a9885ff37d11976039cdcb531d590b8ef31c2878f616693484",
      "path": "scripts/audit_limitations_to_opportunities_completion.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/audit_limitations_to_opportunities_completion.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_check",
          "_no_issues",
          "artifact_status",
          "build_payload",
          "main",
          "read_json",
          "read_text",
          "render_markdown",
          "utc_now_iso",
          "write_outputs"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "json",
          "pathlib",
          "scripts",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "eae371799c624ded697cce131e67c64e1084081f4f4319d1d9f89b870392acea",
      "size_bytes": 20364,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\audit_live_shadow_data_health.py",
      "ast_status": "PARSED",
      "parser_code_hash": "ed027ff57bce7e8d9954f05c7057301b75254dcdc1c4b144ae5815108df18b3e",
      "path": "scripts/audit_live_shadow_data_health.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/audit_live_shadow_data_health.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_bool_value",
          "_is_conditionally_allowed_null",
          "_is_null_like",
          "_m5_refinement_overrides",
          "add_mismatch",
          "audit_all_row_candidate_identity",
          "audit_candidate_coverage",
          "audit_external_confluence",
          "audit_lane_expectations",
          "audit_mechanical_rows",
          "audit_null_fields",
          "audit_opportunity_counts",
          "audit_path_label_geometry",
          "audit_pending_lifecycle_consistency",
          "audit_source_limitations",
          "audit_source_status_feature_interpretation",
          "audit_trade_record_candidate_coverage",
          "build_report",
          "compare_identity",
          "compare_trade_geometry",
          "effective_trade_record_params",
          "issue",
          "latest_by_candidate",
          "latest_by_candidate_asof",
          "latest_mechanical_by_key",
          "main",
          "normalize_source_path",
          "parse_utc",
          "read_jsonl",
          "status_from_issues",
          "strategy_ids",
          "trade_params",
          "values_match",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "no_leak": true,
          "schema_version": true,
          "source_hash": true
        }
      },
      "shape_fingerprint": "ed7555be70f64330d1a941de4667c057ee28840c959b59e2eb85694b8faab185",
      "size_bytes": 71316,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\audit_live_shadow_followup_coverage.py",
      "ast_status": "PARSED",
      "parser_code_hash": "bc2e9dc71bb0e5edc77bdd4563098b513ff132c9f4f7910d79876ffa097ef1dc",
      "path": "scripts/audit_live_shadow_followup_coverage.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/audit_live_shadow_followup_coverage.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_coverage_status",
          "_file_info",
          "_latest_jsonl",
          "build_report",
          "main",
          "render_md",
          "utc_now_iso"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "json",
          "pathlib",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "cfdff031301b24a0e2ac7cf1fe1efc370119b981dfb9b6f0130b750956650fb4",
      "size_bytes": 34723,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\audit_lto_blocked_lane_readiness.py",
      "ast_status": "PARSED",
      "parser_code_hash": "e89b257da9c5ea1115165a2a94389e83ed1cef7466b27dc8ca4576ed2cff9904",
      "path": "scripts/audit_lto_blocked_lane_readiness.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/audit_lto_blocked_lane_readiness.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "append_missing_rows",
          "main",
          "read_jsonl",
          "write_json",
          "write_text"
        ],
        "imports": [
          "__future__",
          "argparse",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "1cfdeef3517449d10bf98e0561e0f43e3ff14b5d2df66b1ead73d9428d3e9235",
      "size_bytes": 5045,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\audit_nas100_orderflow_adverse_selection.py",
      "ast_status": "PARSED",
      "parser_code_hash": "9dbe3fb82c6aee5c7f120b4071a5aabb7910d52945bada1d282e8ec527ca42de",
      "path": "scripts/audit_nas100_orderflow_adverse_selection.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/audit_nas100_orderflow_adverse_selection.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_fmt",
          "_table",
          "build_parser",
          "main",
          "write_outputs"
        ],
        "imports": [
          "__future__",
          "argparse",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {}
      },
      "shape_fingerprint": "13cc6223c9e2a7a3d3735ae8235ad4eeb29a9ef5177e528adb77b35117cd6ecd",
      "size_bytes": 7411,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\audit_notification_queue_dead_zone.py",
      "ast_status": "PARSED",
      "parser_code_hash": "a959c6d711a998acecbfc310373ec6f6c38515d53800fb9575eb7d64c27dd076",
      "path": "scripts/audit_notification_queue_dead_zone.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/audit_notification_queue_dead_zone.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "append_jsonl_once",
          "build_report",
          "main",
          "read_jsonl",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "af6f06a9f19f0fd59530e2cc1636bcbc012132b120f1ee423748497ca84bdecc",
      "size_bytes": 8332,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\audit_orderflow_actual_outcome_coverage.py",
      "ast_status": "PARSED",
      "parser_code_hash": "2d0a624eda91b844f200ecef66c478d5fb52ff5a0280cb43298c6216b0faef83",
      "path": "scripts/audit_orderflow_actual_outcome_coverage.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/audit_orderflow_actual_outcome_coverage.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_find_first_numeric_by_key",
          "_fmt",
          "build_audit_rows",
          "build_parser",
          "build_payload",
          "build_readout",
          "candidate_key",
          "classify_coverage",
          "index_candidate_rows",
          "inspect_trade_record",
          "load_json",
          "main",
          "normalize_symbol",
          "read_jsonl",
          "resolve_repo_path",
          "summarize_audit",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "73dc18f0d3b0cc2a47240f7d4786218b859b151bf2e4548cb2d6f5dfe22b52b0",
      "size_bytes": 19610,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\audit_orderflow_limit_intent_reconciliation.py",
      "ast_status": "PARSED",
      "parser_code_hash": "13613b05331316dd9cdf3fff588a5f8c06fc810feeaf6e20c51fe71c5cbfd1fe",
      "path": "scripts/audit_orderflow_limit_intent_reconciliation.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/audit_orderflow_limit_intent_reconciliation.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_csv_time",
          "_float_or_none",
          "_fmt",
          "_line_no",
          "_trade_id_variants",
          "build_parser",
          "build_payload",
          "build_readout",
          "build_reconciliation_rows",
          "candidate_key",
          "classify_reconciliation",
          "find_m1_csv",
          "find_numeric_key",
          "index_candidate_rows",
          "inspect_log_evidence",
          "inspect_trade_record",
          "iso_utc",
          "load_json",
          "log_file_for_symbol",
          "main",
          "parse_utc",
          "read_jsonl",
          "resolve_repo_path",
          "simulate_limit_path_from_m1",
          "summarize",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "csv",
          "datetime",
          "json",
          "math",
          "pathlib",
          "re",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "71f0db12d66e37965563420fdf5ff46b4754b944fdf6ab40f551e372a2ccebc2",
      "size_bytes": 27727,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\audit_orderflow_nas100_hypothesis_readiness.py",
      "ast_status": "PARSED",
      "parser_code_hash": "7c287ffb4be432a29cb904d2fc528cefd47902b31dcad5716568e3c1cf51fff2",
      "path": "scripts/audit_orderflow_nas100_hypothesis_readiness.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/audit_orderflow_nas100_hypothesis_readiness.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_fmt",
          "_get_nested",
          "_safe_float",
          "build_parser",
          "build_payload",
          "build_readout",
          "extract_diagnostic_summary",
          "extract_key_deltas",
          "load_json",
          "main",
          "proposed_unregistered_hypothesis",
          "readiness_gates",
          "summarize_feature_rows",
          "summarize_symbol_coverage",
          "summarize_synthetic_label_counts",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "as_of": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "07982b0dc5a42b1f0b5a11780f1c8286a59116e62e252d77792cca728c445d9e",
      "size_bytes": 20187,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\audit_orderflow_primitives.py",
      "ast_status": "PARSED",
      "parser_code_hash": "fa25af406bf3c41f5551ba8eb511287b7f4190328fbe0499fc2089115c82bb10",
      "path": "scripts/audit_orderflow_primitives.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/audit_orderflow_primitives.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_fmt",
          "_table",
          "append_status_row_if_missing",
          "build_parser",
          "main",
          "read_jsonl",
          "render_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true
        }
      },
      "shape_fingerprint": "3987904a5463778eee54b709de7ba3c70a05c21d9aa692d741ea9e057c6e51b8",
      "size_bytes": 9584,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\audit_orderflow_proxy_mapping_priorities.py",
      "ast_status": "PARSED",
      "parser_code_hash": "8688a556284fea653c19eb07a843aff3b766ec2421c6defa765b3cbf30eb1038",
      "path": "scripts/audit_orderflow_proxy_mapping_priorities.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/audit_orderflow_proxy_mapping_priorities.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "build_parser",
          "build_payload",
          "build_priority_queue",
          "build_synthesis",
          "candidate_direction",
          "generated_at_utc",
          "is_orderflow_relevant",
          "main",
          "sha256_file",
          "summarize_symbol_rows",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "hashlib",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "a327233d112746270ffc6c2e7a2ba55cbfbbc5005f0fb905a1aeddceebf82522",
      "size_bytes": 21913,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\audit_phase3_research_claim_ledger.py",
      "ast_status": "PARSED",
      "parser_code_hash": "e5d02762cb3f23c3303fa5b8bbe47cc07b2708755dcdda6563d43637b9da5c94",
      "path": "scripts/audit_phase3_research_claim_ledger.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/audit_phase3_research_claim_ledger.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_fmt",
          "artifact",
          "best_structural",
          "build_parser",
          "build_payload",
          "claim",
          "load_json",
          "main",
          "sha256",
          "variant",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "hashlib",
          "json",
          "pathlib",
          "typing"
        ],
        "markers": {
          "schema_version": true
        }
      },
      "shape_fingerprint": "6932c38217ba4569b2ad6e47e379c34bc720f5154e700d591afba90e7262547f",
      "size_bytes": 18193,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\audit_raw_ohlc_path_scaling_v2_concentration.py",
      "ast_status": "PARSED",
      "parser_code_hash": "c9b5ff468ff243f2530cb19beabcf2a44f9e0cd6b71d23c4d315ae88ec741882",
      "path": "scripts/audit_raw_ohlc_path_scaling_v2_concentration.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/audit_raw_ohlc_path_scaling_v2_concentration.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [
          "PairStats"
        ],
        "functions": [
          "_dimension_key",
          "_fmt",
          "_net_r",
          "_table",
          "add",
          "build_concentration_payload",
          "build_decision_readout",
          "build_pairwise_stats",
          "build_parser",
          "build_payload",
          "compare_to_summary",
          "concentration_broadness",
          "concentration_by_dimension",
          "group_deltas",
          "iter_pairs",
          "load_json",
          "load_relevant_event_rows",
          "main",
          "sha256_file",
          "summary_pairwise_lookup",
          "to_summary",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "dataclasses",
          "datetime",
          "hashlib",
          "json",
          "pathlib",
          "scripts",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "f537c660fd7697ff552c1c01b9834008ce07aecf019617e30df398bf3231b468",
      "size_bytes": 22316,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\audit_session_volatility_sweep_status.py",
      "ast_status": "PARSED",
      "parser_code_hash": "b870f61eecf7c44d245d0160bdba0aadf868906c0d7b3e16872ca6b4e580f471",
      "path": "scripts/audit_session_volatility_sweep_status.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/audit_session_volatility_sweep_status.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "append_jsonl",
          "build_report",
          "existing_row_keys",
          "main",
          "read_jsonl",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "8adc11b8ce5be44af42dfdc1b58b67731fe08469429c706fe8c0496852d16f84",
      "size_bytes": 8822,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\audit_shadow_observer_hardening.py",
      "ast_status": "PARSED",
      "parser_code_hash": "6919cb562805aaf1e86cee8c8c2d2f1ca467c2b794a7456d4444287f0838e3db",
      "path": "scripts/audit_shadow_observer_hardening.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/audit_shadow_observer_hardening.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "append_status_row_if_missing",
          "main",
          "read_jsonl_with_lines",
          "write_json"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "05816ab20e4df9776f86a5715843ca6932d9f6d46c2b3a2f1eb8b50edca073f5",
      "size_bytes": 5928,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\audit_sierra_6b_si_depth_policy.py",
      "ast_status": "PARSED",
      "parser_code_hash": "50d507c5dd116b04ec34405cdb6d210ccd472d23b4444147b4f3c7d380a55643",
      "path": "scripts/audit_sierra_6b_si_depth_policy.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/audit_sierra_6b_si_depth_policy.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_fmt",
          "append_status_rows_if_missing",
          "build_parser",
          "main",
          "read_jsonl",
          "render_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true
        }
      },
      "shape_fingerprint": "3111fbb1867623dce25788f7f788414277e9b24de77e65fb4386e32a31f73b72",
      "size_bytes": 7078,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\audit_sierra_depth_sampling_parity.py",
      "ast_status": "PARSED",
      "parser_code_hash": "4587ef97eebf84b19d1ff3a6f95a11f1442d7dd36c1e2c11134bd91311c319cd",
      "path": "scripts/audit_sierra_depth_sampling_parity.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/audit_sierra_depth_sampling_parity.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_fmt",
          "_ordered",
          "_safe_float",
          "_samples_from_df",
          "_second_key_from_ts",
          "build_event_audit",
          "build_window_audit",
          "classify_window",
          "delta_summary",
          "extract_databento_sample_maps",
          "extract_sierra_sample_maps",
          "feature_deltas",
          "find_databento_output_path",
          "load_event",
          "load_json",
          "main",
          "parse_args",
          "render_md",
          "sample_coverage",
          "second_iso",
          "summarize_databento_samples"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "math",
          "pandas",
          "pathlib",
          "scripts",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "schema_version": true
        }
      },
      "shape_fingerprint": "4c432dd77995b8e35ef0d02c6f7fbe4ec381f9272cb59455f4c5eec426082356",
      "size_bytes": 20010,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\audit_sierra_live_depth_confluence.py",
      "ast_status": "PARSED",
      "parser_code_hash": "101f45e3160b2ca8bf62f809394f71d610a820f3187f561757735ce4de94969f",
      "path": "scripts/audit_sierra_live_depth_confluence.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/audit_sierra_live_depth_confluence.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_counter",
          "_file_hash",
          "_fmt",
          "_symbol_status_counts",
          "_table",
          "append_status_row_if_missing",
          "build_parser",
          "build_report",
          "build_status_row",
          "latest_by_candidate",
          "main",
          "read_json",
          "read_jsonl",
          "source_signature",
          "utc_now_iso",
          "write_outputs"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "hashlib",
          "json",
          "pathlib",
          "scripts",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "no_leak": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "d64b3d795e831dc7c2e0a6f91779ec768b062d2a39673c13447edda0eaa4a3b2",
      "size_bytes": 16917,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\audit_sierra_proxy_registry.py",
      "ast_status": "PARSED",
      "parser_code_hash": "5b7bf72890118d53b544883b68e8c5a63ff2876d248f6f2a6e06d6547e5186dc",
      "path": "scripts/audit_sierra_proxy_registry.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/audit_sierra_proxy_registry.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_counts",
          "_file_hash",
          "_fmt",
          "_missing_required_proxy_classes",
          "_table",
          "append_status_rows_if_missing",
          "build_parser",
          "build_report",
          "build_status_row",
          "latest_by_candidate",
          "main",
          "read_jsonl",
          "source_signature",
          "utc_now_iso",
          "write_outputs"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "hashlib",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "2477971c0731e259a6d38daa735ab72cba9e70f9d39c7ff30dcb71579b47ad03",
      "size_bytes": 14051,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\audit_storage_retention.py",
      "ast_status": "PARSED",
      "parser_code_hash": "d732840979900bf1908183fcc1e7ceb05635e0b9fe41d96daecdccae3237385d",
      "path": "scripts/audit_storage_retention.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/audit_storage_retention.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_table",
          "append_jsonl_once",
          "build_report",
          "main",
          "read_jsonl",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "ddb3dcd39fc081aff689ee4a9fbf9290d62ca3bdbf78784994eaa03fe39f5bca",
      "size_bytes": 9441,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\audit_usdjpy_6j_followup_validation.py",
      "ast_status": "PARSED",
      "parser_code_hash": "8fc4cef37c30cdb68da3959ff09bf0219a11954405b96e40612f2c6455374fb1",
      "path": "scripts/audit_usdjpy_6j_followup_validation.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/audit_usdjpy_6j_followup_validation.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_estimate_cost",
          "_fmt",
          "_window_date",
          "build_parser",
          "build_payload",
          "expected_shift_for_date",
          "extract_rows",
          "load_json",
          "main",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "json",
          "pathlib",
          "statistics",
          "typing"
        ],
        "markers": {
          "schema_version": true
        }
      },
      "shape_fingerprint": "2ffefd93b4bba6759a52939130250bc8725f3fcda7a2c2c3b9e986de7ca8d864",
      "size_bytes": 13878,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\audit_v2_structural_selector_readiness.py",
      "ast_status": "PARSED",
      "parser_code_hash": "7ee64fae74f1ebaf947e15f109326a8c64e14c858ef7b64d3c7af111ddc62c69",
      "path": "scripts/audit_v2_structural_selector_readiness.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/audit_v2_structural_selector_readiness.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "append_status_row_if_missing",
          "main",
          "read_jsonl_with_lines",
          "write_json"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "05816ab20e4df9776f86a5715843ca6932d9f6d46c2b3a2f1eb8b50edca073f5",
      "size_bytes": 4779,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\audit_xauusd_same_market_extension.py",
      "ast_status": "PARSED",
      "parser_code_hash": "6539d2f6d836aa77b73b05c571271b1db4b365d2836220185b84cdb21409f221",
      "path": "scripts/audit_xauusd_same_market_extension.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/audit_xauusd_same_market_extension.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "append_status_row_if_missing",
          "main",
          "read_json",
          "read_jsonl_with_lines",
          "write_json"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "0d9a55e8c84257b1445569c626112d15badc8acfd6c368f0117198a2f4dea063",
      "size_bytes": 4997,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\backfill_2026_04_28_gbpjpy_close.py",
      "ast_status": "PARSED",
      "parser_code_hash": "8477c2ea63f689fa257845632e928d972df8d5ba4090f608db515ef41b1a0229",
      "path": "scripts/backfill_2026_04_28_gbpjpy_close.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/backfill_2026_04_28_gbpjpy_close.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "already_applied",
          "backup",
          "fix_daily_pnl",
          "fix_j46_j49_shadow",
          "fix_trade_record",
          "main"
        ],
        "imports": [
          "__future__",
          "json",
          "pathlib",
          "shutil"
        ],
        "markers": {
          "jsonl": true
        }
      },
      "shape_fingerprint": "c098fcd26a52733126563212abfb54e60d649491ab47febf3765b1584c1b59bf",
      "size_bytes": 7844,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\backfill_2026_04_29_nas100_sl.py",
      "ast_status": "PARSED",
      "parser_code_hash": "4147a41103659820237c8082906c034ae330f5e23417722d6a35c83d8cf471ec",
      "path": "scripts/backfill_2026_04_29_nas100_sl.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/backfill_2026_04_29_nas100_sl.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "already_applied",
          "backup",
          "fix_daily_pnl",
          "fix_j46_j49_shadow",
          "fix_trade_record",
          "main"
        ],
        "imports": [
          "__future__",
          "json",
          "pathlib",
          "shutil"
        ],
        "markers": {
          "jsonl": true
        }
      },
      "shape_fingerprint": "c098fcd26a52733126563212abfb54e60d649491ab47febf3765b1584c1b59bf",
      "size_bytes": 10290,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\backfill_account_pnl_truth_reconciliation.py",
      "ast_status": "PARSED",
      "parser_code_hash": "1a39ac26d833e5757a4ffc4b67aa2b1d767a156ec0fc998f64fe1519188f5dc9",
      "path": "scripts/backfill_account_pnl_truth_reconciliation.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/backfill_account_pnl_truth_reconciliation.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_jsonl_sources",
          "append_jsonl",
          "build_report",
          "existing_row_keys",
          "main",
          "read_json",
          "read_jsonl_with_lines",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "bc9519839310e4bac4d8778f73c60f929d078e179b36f4f7cf68a173c4c44752",
      "size_bytes": 8953,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\backfill_broker_actual_r_audit.py",
      "ast_status": "PARSED",
      "parser_code_hash": "6e62bc95be4bf53387513dfea585a0da4979e8be5bc92ed63d7a9862cca0eb65",
      "path": "scripts/backfill_broker_actual_r_audit.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/backfill_broker_actual_r_audit.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_jsonl_sources",
          "append_jsonl",
          "build_report",
          "existing_row_keys",
          "main",
          "read_jsonl_with_lines",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "1761cdecf5dc96ca096c75bef6923099fc9c02d9cbe4ba78e0a28fd9224e51fa",
      "size_bytes": 9453,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\backfill_candidate_mso_snapshot_joins.py",
      "ast_status": "PARSED",
      "parser_code_hash": "2f4d11877cd3663ce7eeba449db6fedd3621659441dc741bfb3487b79d012544",
      "path": "scripts/backfill_candidate_mso_snapshot_joins.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/backfill_candidate_mso_snapshot_joins.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "append_jsonl",
          "build_report",
          "existing_row_keys",
          "main",
          "read_jsonl_with_lines",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "f39f094da1bb7d646c0eea85e07f88161263445e1a8de55520cf7424247c1863",
      "size_bytes": 8411,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\backfill_candidate_path_contract_audit.py",
      "ast_status": "PARSED",
      "parser_code_hash": "da61f263a1e86135931183408dc7dc0c5cec8614f9cdbd0c72eddc7ae2598618",
      "path": "scripts/backfill_candidate_path_contract_audit.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/backfill_candidate_path_contract_audit.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "append_jsonl",
          "build_report",
          "existing_row_keys",
          "latest_ltf_by_candidate",
          "main",
          "read_jsonl_with_lines",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "2fe2a00e541d3f29e7e92384d0871a6e8f198847f88fa1a91ac9a913a9c37ce5",
      "size_bytes": 7503,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\backfill_candidate_registry_audit.py",
      "ast_status": "PARSED",
      "parser_code_hash": "f4a604f75ff8b4d4527b4cf5d0595d39ad3883a6d849eb31256708f9a4d9c09d",
      "path": "scripts/backfill_candidate_registry_audit.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/backfill_candidate_registry_audit.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "append_jsonl",
          "build_report",
          "existing_row_keys",
          "main",
          "read_jsonl_with_lines",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "f39f094da1bb7d646c0eea85e07f88161263445e1a8de55520cf7424247c1863",
      "size_bytes": 7192,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\backfill_context_control_audit.py",
      "ast_status": "PARSED",
      "parser_code_hash": "a56aa706c89292ac1abbb45a2b270e0d4d7c79bcce4a2931339ec22e84db8295",
      "path": "scripts/backfill_context_control_audit.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/backfill_context_control_audit.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "append_jsonl",
          "build_report",
          "existing_row_keys",
          "main",
          "read_jsonl_with_lines",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "f39f094da1bb7d646c0eea85e07f88161263445e1a8de55520cf7424247c1863",
      "size_bytes": 8909,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\backfill_continuation_no_retrace_shadow.py",
      "ast_status": "PARSED",
      "parser_code_hash": "270888359cb826a7ef7f398cc09ba5c8eeb7af217f19a474dee5e63425826261",
      "path": "scripts/backfill_continuation_no_retrace_shadow.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/backfill_continuation_no_retrace_shadow.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "append_jsonl",
          "existing_row_keys",
          "main",
          "read_jsonl_with_lines",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "49545de24775350dbf1aeaec0830a060d66100642b3fd510ca8a5f933e8c78a2",
      "size_bytes": 7888,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\backfill_decision_layer_diagnostics_join.py",
      "ast_status": "PARSED",
      "parser_code_hash": "f838ca8c7435f383d7af745fb6870f3578f8c22ac60a36a7236c72ed13d54966",
      "path": "scripts/backfill_decision_layer_diagnostics_join.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/backfill_decision_layer_diagnostics_join.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "append_jsonl",
          "build_report",
          "existing_row_keys",
          "main",
          "read_jsonl_with_lines",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "f39f094da1bb7d646c0eea85e07f88161263445e1a8de55520cf7424247c1863",
      "size_bytes": 11967,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\backfill_exit_management_no_event_status.py",
      "ast_status": "PARSED",
      "parser_code_hash": "4d43e1c0fbcf193fc3172972d4eeab5448a31265bca0dc466a28b79f1918f62a",
      "path": "scripts/backfill_exit_management_no_event_status.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/backfill_exit_management_no_event_status.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "append_jsonl",
          "build_report",
          "event_file_status",
          "existing_row_keys",
          "main",
          "read_jsonl_with_lines",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "0ee11bd578d843e1a1d7dbf18996159c432525d5cd9d6fa81f0e79588d856393",
      "size_bytes": 10107,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\backfill_fvg_ob_confluence_audit.py",
      "ast_status": "PARSED",
      "parser_code_hash": "7d67c58adaa9054953b0d04e1f90074875ef61a5750176cfba23141285c52ac2",
      "path": "scripts/backfill_fvg_ob_confluence_audit.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/backfill_fvg_ob_confluence_audit.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "append_jsonl",
          "build_report",
          "existing_row_keys",
          "main",
          "read_jsonl_with_lines",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "no_leak": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "6101ff676bcd173714291578697bcf117b151f776f7f2844194fcfd90be96e52",
      "size_bytes": 10963,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\backfill_fvg_ob_confluence_source_geometry.py",
      "ast_status": "PARSED",
      "parser_code_hash": "38eb7d2bd30d44ac99e3d4424c388b55db18fca0b4d2919dc0bf5305824ce584",
      "path": "scripts/backfill_fvg_ob_confluence_source_geometry.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/backfill_fvg_ob_confluence_source_geometry.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_has_exact_geometry",
          "append_jsonl",
          "build_enriched_confluence_rows",
          "main",
          "read_jsonl",
          "summarize_existing_recovered_geometry",
          "write_report"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "no_leak": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "cd16d4ad0e2c63228e7aff43b987c492d0c6e955be899328b1f905661e7eb546",
      "size_bytes": 10509,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\backfill_j46_j49_exit_comparator_audit.py",
      "ast_status": "PARSED",
      "parser_code_hash": "12bacbcaba307034295844e60360ae6f201006c28d874747ca081385d975e001",
      "path": "scripts/backfill_j46_j49_exit_comparator_audit.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/backfill_j46_j49_exit_comparator_audit.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "append_jsonl",
          "build_report",
          "existing_row_keys",
          "main",
          "read_jsonl_with_lines",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "f39f094da1bb7d646c0eea85e07f88161263445e1a8de55520cf7424247c1863",
      "size_bytes": 10075,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\backfill_k55_ml_shadow_predictions.py",
      "ast_status": "PARSED",
      "parser_code_hash": "9dced1f5835f76d638cba27d24c6396865157a4434c3134c6824d1938667ccff",
      "path": "scripts/backfill_k55_ml_shadow_predictions.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/backfill_k55_ml_shadow_predictions.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "append_jsonl",
          "existing_row_keys",
          "main",
          "read_jsonl_with_lines",
          "write_json"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "c7e89f8e981316a170fda3202acb3375226ba2f176fd34b1f26a4ee0acfc0acd",
      "size_bytes": 8694,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\backfill_m15_choch_diagnostics.py",
      "ast_status": "PARSED",
      "parser_code_hash": "e243f2d1121201cfa7a47e7d5539db59e1ba4448c9dcb565fcc1ee167fead782",
      "path": "scripts/backfill_m15_choch_diagnostics.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/backfill_m15_choch_diagnostics.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "append_jsonl",
          "existing_row_keys",
          "main",
          "read_jsonl_with_lines",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "49545de24775350dbf1aeaec0830a060d66100642b3fd510ca8a5f933e8c78a2",
      "size_bytes": 6495,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\backfill_mechanical_context_diagnostics_join.py",
      "ast_status": "PARSED",
      "parser_code_hash": "5db861cf8eb3f2d34fd678640a66dd378b2b3d207a0f78cda7280854e5c37c46",
      "path": "scripts/backfill_mechanical_context_diagnostics_join.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/backfill_mechanical_context_diagnostics_join.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "append_jsonl",
          "build_report",
          "existing_row_keys",
          "main",
          "read_jsonl_with_lines",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "f39f094da1bb7d646c0eea85e07f88161263445e1a8de55520cf7424247c1863",
      "size_bytes": 12553,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\backfill_opportunity_lifecycle_audit.py",
      "ast_status": "PARSED",
      "parser_code_hash": "890500fb4efd21540bfb5b0f2ee0fde9cbdf51b993013f9456bd207978f24963",
      "path": "scripts/backfill_opportunity_lifecycle_audit.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/backfill_opportunity_lifecycle_audit.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "append_jsonl",
          "build_report",
          "existing_row_keys",
          "main",
          "read_jsonl_with_lines",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "f39f094da1bb7d646c0eea85e07f88161263445e1a8de55520cf7424247c1863",
      "size_bytes": 9579,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\backfill_pending_limit_lifecycle_audit.py",
      "ast_status": "PARSED",
      "parser_code_hash": "2cb6b245456ff10e82cd6700bba158dc3958e0230c14e493ea3c42fc687e929c",
      "path": "scripts/backfill_pending_limit_lifecycle_audit.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/backfill_pending_limit_lifecycle_audit.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "append_jsonl",
          "build_report",
          "dedupe_jsonl_issues",
          "existing_rows_by_key",
          "latest_decision_date_prefix",
          "main",
          "read_jsonl_with_lines",
          "row_changed",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "d430f6da4e94e399c351b14a70cb25ed05b73f4f5ab7c5e0f6b000314feb72fd",
      "size_bytes": 15304,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\backfill_prefill_delivery_path_audit.py",
      "ast_status": "PARSED",
      "parser_code_hash": "f59a63abe21e5016cd06ea4375159d94c7f2954be325f14a727003daafe6a57a",
      "path": "scripts/backfill_prefill_delivery_path_audit.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/backfill_prefill_delivery_path_audit.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "append_jsonl",
          "build_report",
          "existing_row_keys",
          "main",
          "read_jsonl_with_lines",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "no_leak": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "6101ff676bcd173714291578697bcf117b151f776f7f2844194fcfd90be96e52",
      "size_bytes": 11957,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\backfill_regime_decay_outcome_join.py",
      "ast_status": "PARSED",
      "parser_code_hash": "02c23e571f8d349b555a7ff81095e30527f6a5367276fb8242cf95f4f7c637f3",
      "path": "scripts/backfill_regime_decay_outcome_join.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/backfill_regime_decay_outcome_join.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "append_jsonl",
          "build_report",
          "existing_row_keys",
          "latest_monthly_decay_report",
          "latest_ob_continuation_by_scope",
          "main",
          "read_csv_rows",
          "read_jsonl_with_lines",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "csv",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "6b568c2d2bc341ce86b7805eb00d3c17ef72981b64be5f28f45cdb940b9adbe7",
      "size_bytes": 13996,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\backfill_s79_side_aware_risk_context.py",
      "ast_status": "PARSED",
      "parser_code_hash": "b4d76fb18fd190f7e1c912b5410ccfae41b544ecd458150dfab8755c8e2bdae7",
      "path": "scripts/backfill_s79_side_aware_risk_context.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/backfill_s79_side_aware_risk_context.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "append_jsonl",
          "build_report",
          "existing_row_keys",
          "main",
          "read_json_object",
          "read_jsonl_with_lines",
          "read_yaml",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing",
          "yaml"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "fe7d45ee779325e1e0e17e5dc9d12d0c78e66c42912ebc3b89b1ec1ed1a0933c",
      "size_bytes": 10290,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\backfill_shadow_observer_tick_enrichment.py",
      "ast_status": "PARSED",
      "parser_code_hash": "dbc7840c58a7837fbe82c37c0b8162effb2ef3031d66842f1b4bc5034e8473cc",
      "path": "scripts/backfill_shadow_observer_tick_enrichment.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/backfill_shadow_observer_tick_enrichment.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "build_parser",
          "main"
        ],
        "imports": [
          "__future__",
          "argparse",
          "json",
          "pathlib",
          "src",
          "sys"
        ],
        "markers": {}
      },
      "shape_fingerprint": "683c3665c065de9332fe5e234af9d7a4557930b8c37b6b1c6f5687358a1ed298",
      "size_bytes": 1185,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\backfill_trade_index_lifecycle_audit.py",
      "ast_status": "PARSED",
      "parser_code_hash": "b7dac2a5032a6ce0125a8b7f3e568c015cbc6f800b12cd9ac91885fbb19992a2",
      "path": "scripts/backfill_trade_index_lifecycle_audit.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/backfill_trade_index_lifecycle_audit.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "append_jsonl",
          "build_report",
          "existing_rows_by_key",
          "main",
          "row_changed",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "02378f121a066c47e3c09f463265866cbcf342ada13ec8d06f881f8e056c3e23",
      "size_bytes": 11202,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\backfill_v2b_forward_pair_resolution_audit.py",
      "ast_status": "PARSED",
      "parser_code_hash": "905538e8a6e80a0f39aab0e20b7ea0ad854fd9e4a042809800d78af754f919b6",
      "path": "scripts/backfill_v2b_forward_pair_resolution_audit.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/backfill_v2b_forward_pair_resolution_audit.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "append_jsonl",
          "build_report",
          "existing_row_keys",
          "main",
          "read_jsonl_with_lines",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "no_leak": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "6101ff676bcd173714291578697bcf117b151f776f7f2844194fcfd90be96e52",
      "size_bytes": 12053,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\backfill_xagusd_fresh_ob_late_ny.py",
      "ast_status": "PARSED",
      "parser_code_hash": "cbc30fe8e419a21c019f983e75f4c155b8329ec28f2e2c092f2ec67f50421f9a",
      "path": "scripts/backfill_xagusd_fresh_ob_late_ny.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/backfill_xagusd_fresh_ob_late_ny.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "append_jsonl",
          "existing_row_keys",
          "main",
          "read_jsonl_with_lines",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "49545de24775350dbf1aeaec0830a060d66100642b3fd510ca8a5f933e8c78a2",
      "size_bytes": 6168,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\batch_backtest.py",
      "ast_status": "PARSED",
      "parser_code_hash": "847295cea89f9f8df8e93224f47e57175421ccf2987a1f911fdf7ac8be302d1b",
      "path": "scripts/batch_backtest.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/batch_backtest.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_build_request",
          "_safety_check",
          "build_batch_requests",
          "collect_prompts",
          "download_results",
          "estimate_cost",
          "generate_report",
          "main",
          "prescreen_date",
          "process_results",
          "submit_batch",
          "wait_for_batch"
        ],
        "imports": [
          "__future__",
          "anthropic",
          "argparse",
          "datetime",
          "dotenv",
          "json",
          "logging",
          "pathlib",
          "scripts",
          "src",
          "sys",
          "time",
          "typing",
          "yaml"
        ],
        "markers": {}
      },
      "shape_fingerprint": "da82ed23af1894f61f90a917ca27f9ee9483617f19915949530f747ad82d2dc2",
      "size_bytes": 55504,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\build_broker_r_reconciliation_coverage.py",
      "ast_status": "PARSED",
      "parser_code_hash": "8133568543d5da2e05ef1bfb378d8ba6db750d85eec7707ef096345712b748fd",
      "path": "scripts/build_broker_r_reconciliation_coverage.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/build_broker_r_reconciliation_coverage.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_has_broker_actual_r",
          "_has_execution",
          "_has_synthetic_path",
          "build_parser",
          "build_payload",
          "main",
          "read_jsonl",
          "read_trade_records",
          "render_md",
          "summarize",
          "utc_now_iso"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "json",
          "pathlib",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "b9e787e7bc9cd3ea61232c003ecc1d65cd341888c41eaf37744a3e756d94f546",
      "size_bytes": 7878,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\build_cost_slippage_exit_coverage.py",
      "ast_status": "PARSED",
      "parser_code_hash": "51e78f2f6ca2921a68c716cbabb5e4e9d54a10171ede97a92050e00076b83404",
      "path": "scripts/build_cost_slippage_exit_coverage.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/build_cost_slippage_exit_coverage.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "build_parser",
          "build_payload",
          "main",
          "read_jsonl",
          "render_md",
          "utc_now_iso"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "json",
          "pathlib",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "30931acbd9d745d10d9537ea681c9d53c53d727136ada49168c9bf7a3a258ba0",
      "size_bytes": 5723,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\build_daily_monitoring_checklist.py",
      "ast_status": "PARSED",
      "parser_code_hash": "7773561ff787a2213d411ccacaa3efd1a851b4ed130918c0c88e5c44ee3de41f",
      "path": "scripts/build_daily_monitoring_checklist.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/build_daily_monitoring_checklist.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "build_payload",
          "extract_python_commands",
          "lane_rows_from_queue",
          "load_lto_queue",
          "main",
          "read_text",
          "render_markdown",
          "write_outputs"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "json",
          "pathlib",
          "re",
          "scripts",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true,
          "scid": true
        }
      },
      "shape_fingerprint": "001abdf4d322ca1be6f87a272703c7a7c2bc3d93ea07470c90201f604f8a8b91",
      "size_bytes": 20523,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\build_expanded_oos_control_artifacts.py",
      "ast_status": "PARSED",
      "parser_code_hash": "da9e145fed76cf9a460c7837bef61223ac04b9f021f8337401e63884bce71821",
      "path": "scripts/build_expanded_oos_control_artifacts.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/build_expanded_oos_control_artifacts.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "build_parser",
          "build_source_map",
          "candidate_registry",
          "first_wave_depth_rows",
          "first_wave_scid_rows",
          "fmt",
          "gb",
          "iso_from_timestamp",
          "line_count",
          "load_json",
          "main",
          "mb",
          "rel",
          "summarize_databento_cache",
          "summarize_external_validation",
          "summarize_live_mt5_symbol_specs",
          "summarize_local_historical",
          "summarize_mt5_manifests",
          "summarize_mt5_tick_availability",
          "summarize_sierra_depth",
          "summarize_sierra_scid",
          "table",
          "top_mt5_rows",
          "utc_now",
          "write_json",
          "write_registry_markdown",
          "write_source_markdown"
        ],
        "imports": [
          "MetaTrader5",
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "re",
          "scripts",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true,
          "scid": true
        }
      },
      "shape_fingerprint": "62e02a18d64c866aa8057007d3b50a819403b1e3520d2a18f1b65064feb4945f",
      "size_bytes": 42797,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\build_expanded_oos_family_label_status.py",
      "ast_status": "PARSED",
      "parser_code_hash": "18b15edacc1aa2e62df8dda9c4cfcf2413096dedeba71ac5a427190116caad4e",
      "path": "scripts/build_expanded_oos_family_label_status.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/build_expanded_oos_family_label_status.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "build_family_status_rows",
          "build_parser",
          "build_payload",
          "classify_family_status",
          "compact_source_summary",
          "conversion_rows_by_source",
          "fmt",
          "load_json",
          "main",
          "reason_for_status",
          "rel",
          "replay_spec_cohorts",
          "rows_for_family",
          "source_row_status",
          "split_cohort_symbol",
          "table",
          "target_families",
          "utc_now",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "json",
          "pathlib",
          "sys",
          "typing"
        ],
        "markers": {
          "schema_version": true
        }
      },
      "shape_fingerprint": "e2b993c29c432a0adfa4941d683dce96b1df3fb6782852b68f3b817cc12fc6c2",
      "size_bytes": 16263,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\build_external_feed_candidate_dataset.py",
      "ast_status": "PARSED",
      "parser_code_hash": "98c78487132d4ff11f347e44cdb0a17d36e8415dfad1e9b2ef8bc1cf17f7cce1",
      "path": "scripts/build_external_feed_candidate_dataset.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/build_external_feed_candidate_dataset.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [
          "TradeRecordOutcome"
        ],
        "functions": [
          "_candidate_needed_keys",
          "_candidate_projection",
          "_extract_realized_r",
          "_has_near_future_bar",
          "_load_ohlcv_rows",
          "_ohlcv_stems",
          "_peek_validation_symbol",
          "_realized_r_missing_reason",
          "_resolve_ohlcv_path",
          "_simulate_candidate_opportunity",
          "_status_or_raw",
          "_synthetic_missing",
          "_trade_record_outcome",
          "_validation_symbol_aliases",
          "build_candidate_validation_rows",
          "build_parser",
          "find_latest_validation_paths",
          "load_candidate_rows",
          "load_trade_record_index",
          "load_validation_index",
          "main",
          "normalize_candidate_candle_close",
          "write_candidate_join_artifacts"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "csv",
          "dataclasses",
          "datetime",
          "json",
          "pathlib",
          "scripts",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "8371f441212bdbb09dd5b17c6d29a55dfada254fdc30cc58dd3d165639dfdadb",
      "size_bytes": 38280,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\build_external_feed_snapshots_historical.py",
      "ast_status": "PARSED",
      "parser_code_hash": "68c0d55bdb31258d0afa705caace22c0dae59dd960fba8a300633a7b8fe0085f",
      "path": "scripts/build_external_feed_snapshots_historical.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/build_external_feed_snapshots_historical.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [
          "PreparedGroup"
        ],
        "functions": [
          "_append_lbma_schedule_fields",
          "_append_snapshot_fields",
          "_parse_mt5_time",
          "_prepare_rows_by_symbol",
          "_row_observation_time",
          "_select_adjacent_prepared_rows",
          "_select_prepared_row",
          "build_historical_snapshots",
          "build_parser",
          "build_snapshot_from_index",
          "load_candle_closes",
          "main",
          "parse_group_filters",
          "parse_symbol_aliases",
          "prepare_snapshot_index",
          "write_historical_snapshots"
        ],
        "imports": [
          "__future__",
          "argparse",
          "bisect",
          "csv",
          "dataclasses",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "as_of": true,
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "6cf2e62a5d987ad51700a643623807cd2529c7bf3becdf0b562a809f305899fb",
      "size_bytes": 22186,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\build_external_feed_validation_dataset.py",
      "ast_status": "PARSED",
      "parser_code_hash": "707edb35644f31d174b79e501381347ff9539cccd17ef9478bdcb20305fa79e9",
      "path": "scripts/build_external_feed_validation_dataset.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/build_external_feed_validation_dataset.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [
          "Candle"
        ],
        "functions": [
          "_float_or_none",
          "_future_labels",
          "_infer_file_symbol",
          "_mean_forward_returns",
          "_parse_mt5_time",
          "_source_availability",
          "build_parser",
          "build_validation_rows",
          "find_latest_snapshot_paths",
          "load_jsonl",
          "load_mt5_candles",
          "main",
          "summarize_validation_rows",
          "validate_snapshot_no_lookahead",
          "write_validation_artifacts"
        ],
        "imports": [
          "__future__",
          "argparse",
          "csv",
          "dataclasses",
          "datetime",
          "json",
          "pathlib",
          "src",
          "statistics",
          "sys",
          "typing"
        ],
        "markers": {
          "as_of": true,
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "911eab52599f491323bacc06eff072e3f9915548114eba76c0a6dc1669730090",
      "size_bytes": 17542,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\build_forward_capture_artifacts.py",
      "ast_status": "PARSED",
      "parser_code_hash": "4a72df87c45dd0e67979208d03d64d16699dcdf02f390fde7a143804e046043f",
      "path": "scripts/build_forward_capture_artifacts.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/build_forward_capture_artifacts.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "base_payload",
          "build_claim_ledger_artifacts",
          "build_context_ai_source_reports",
          "build_databento_artifacts",
          "build_final_synthesis",
          "build_forward_collector_statuses",
          "build_ltf_status",
          "build_monitoring_runbook",
          "build_nas100_readiness",
          "build_pending_limit_status",
          "build_registration_reports",
          "build_sampling_and_source_reports",
          "count_jsonl",
          "main",
          "read_json",
          "status_md",
          "table",
          "utc_now_iso",
          "write_json",
          "write_text"
        ],
        "imports": [
          "__future__",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "a8487c215c6769a7eb34c0e4835a0577d63d9d5593df482b8cb80ebd97806e71",
      "size_bytes": 49152,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\build_historical_opportunity_dataset.py",
      "ast_status": "PARSED",
      "parser_code_hash": "f373780f8eea5a14e2d38e12337d8abdc49079f7f598a21cd11348214362b5a9",
      "path": "scripts/build_historical_opportunity_dataset.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/build_historical_opportunity_dataset.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [
          "AuditAccumulator",
          "CandleSeries",
          "OpportunityCandle"
        ],
        "functions": [
          "__init__",
          "_base_row",
          "_baseline_config_from_config",
          "_bias_projection",
          "_compute_deterministic_bias",
          "_counter_table",
          "_empty_mechanical_projection",
          "_empty_session_levels",
          "_ensure_source_availability_fields",
          "_error_gate_projection",
          "_evaluate_pre_ai",
          "_feature_availability",
          "_find_ohlcv_path",
          "_float_or_zero",
          "_is_first_ny_bar_to_skip",
          "_iso_z",
          "_json_default",
          "_kill_zone_windows",
          "_latest_source_timestamp",
          "_load_outcome_rows",
          "_markdown_source_availability",
          "_markdown_table",
          "_markdown_table_from_mapping",
          "_mechanical_projection",
          "_mso_feature_counts",
          "_ohlcv_source_flags",
          "_parse_hhmm",
          "_prescreen_mso",
          "_previous_weekday",
          "_sanitize_known_calendar_snapshot",
          "_session_for_bar_open",
          "_update_session_levels_from_slice",
          "add",
          "build_external_snapshot_projection",
          "build_parser",
          "build_raw_data_fast",
          "compute_session_levels_fast",
          "derive_h4_series_from_h1",
          "derived",
          "direction",
          "disable_component_side_effects",
          "enumerate_opportunity_candles",
          "from_csv",
          "iter_historical_opportunities",
          "load_base_config",
          "load_broker_symbol_map",
          "load_symbol_candle_series",
          "main",
          "render_audit_markdown",
          "slice_for_mso",
          "to_summary",
          "write_opportunity_artifacts",
          "write_report"
        ],
        "imports": [
          "__future__",
          "argparse",
          "bisect",
          "collections",
          "copy",
          "csv",
          "dataclasses",
          "datetime",
          "json",
          "logging",
          "pathlib",
          "scripts",
          "src",
          "sys",
          "typing",
          "yaml"
        ],
        "markers": {
          "as_of": true,
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "a284d37352d47b7c48b19d4fb1b61795cd184cb4f7560b435460560b4a2b188d",
      "size_bytes": 60694,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\build_historical_opportunity_truth_layer.py",
      "ast_status": "PARSED",
      "parser_code_hash": "fd48c7b4d680121d82a1c101d11e18cf0941c4a8362cda2a3e7682c79472c0bb",
      "path": "scripts/build_historical_opportunity_truth_layer.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/build_historical_opportunity_truth_layer.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [
          "LowerTimeframeDiagnostics",
          "TruthAccumulator",
          "TruthGroupStats"
        ],
        "functions": [
          "_add_empty_lower_fields",
          "_add_lower_fields",
          "_ambiguity_bucket",
          "_base_truth_row",
          "_bias_stack",
          "_classify_gate_reject",
          "_classify_setup_skip",
          "_confidence",
          "_counter_pair_rows",
          "_counter_rows",
          "_exit_before_first_gap",
          "_exit_status",
          "_fill_status",
          "_float_or_none",
          "_gate_failure_bucket",
          "_int_or_none",
          "_lower_refined_base",
          "_lower_refined_unavailable",
          "_lower_selection_reason",
          "_lower_truth_outcome",
          "_lower_truth_score",
          "_markdown_cell",
          "_markdown_lower_timeframes",
          "_markdown_table",
          "_mean",
          "_normalize_lower_timeframes",
          "_outcome_bucket",
          "_pair_key",
          "_rate",
          "_regime_label",
          "_row_matches_filter",
          "_select_truth_source",
          "_setup_failure_bucket",
          "_stats_rows",
          "_synthesis_bullets",
          "_timeframe_bonus",
          "_top_rows",
          "_truth_projection",
          "add",
          "add",
          "as_row",
          "build_parser",
          "build_truth_layer",
          "classify_truth_row",
          "inspect_lower_timeframe",
          "main",
          "refine_and_inspect_lower_timeframe",
          "render_report",
          "to_summary",
          "write_report"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "dataclasses",
          "datetime",
          "json",
          "pathlib",
          "scripts",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "as_of": true,
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "5a62c0b3a04438c070032e2ab3551a5c469dee86060508a3cfce0400d56e0f32",
      "size_bytes": 59329,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\build_k55_source_bundle_integration_plan.py",
      "ast_status": "PARSED",
      "parser_code_hash": "cf4705746901ae07fc50e31c37bec4ce448605558419e9d7e120d831ba3e227e",
      "path": "scripts/build_k55_source_bundle_integration_plan.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/build_k55_source_bundle_integration_plan.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "build_parser",
          "main"
        ],
        "imports": [
          "__future__",
          "argparse",
          "json",
          "pathlib",
          "src",
          "sys"
        ],
        "markers": {}
      },
      "shape_fingerprint": "683c3665c065de9332fe5e234af9d7a4557930b8c37b6b1c6f5687358a1ed298",
      "size_bytes": 2506,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\build_limitations_to_opportunities_queue_state.py",
      "ast_status": "PARSED",
      "parser_code_hash": "c36cf48114d0c06be2fec68ae0102aab42200309caa1be9fe38b6c5100b0b21f",
      "path": "scripts/build_limitations_to_opportunities_queue_state.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/build_limitations_to_opportunities_queue_state.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "build_payload",
          "clean_cell",
          "dynamic_status",
          "extract_block",
          "extract_prior_gap_ids",
          "load_coverage",
          "main",
          "parse_followup_mapping",
          "parse_lto_sections",
          "render_markdown",
          "split_markdown_row",
          "write_outputs"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "re",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "226dd21476bc59a84dea0a01d6c82323a5623d7a8004157f579f6bf7e2c3727b",
      "size_bytes": 43106,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\build_lto031_lto032_databento_credit_replay_manifests.py",
      "ast_status": "PARSED",
      "parser_code_hash": "707af9f06d4346c4577d7b10d7a2facad48fda46a32ff2bad05ddb22a862f81a",
      "path": "scripts/build_lto031_lto032_databento_credit_replay_manifests.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/build_lto031_lto032_databento_credit_replay_manifests.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "build_parser",
          "main"
        ],
        "imports": [
          "__future__",
          "argparse",
          "json",
          "pathlib",
          "src",
          "sys"
        ],
        "markers": {}
      },
      "shape_fingerprint": "683c3665c065de9332fe5e234af9d7a4557930b8c37b6b1c6f5687358a1ed298",
      "size_bytes": 2873,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\build_lto031_lto032_free_public_source_manifests.py",
      "ast_status": "PARSED",
      "parser_code_hash": "415d35704399b919b2d68b7932858a67242b50c771f167fcabaa17eaafa76f99",
      "path": "scripts/build_lto031_lto032_free_public_source_manifests.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/build_lto031_lto032_free_public_source_manifests.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "build_parser",
          "load_or_build_registry",
          "main",
          "read_json"
        ],
        "imports": [
          "__future__",
          "argparse",
          "json",
          "pathlib",
          "scripts",
          "src",
          "sys"
        ],
        "markers": {}
      },
      "shape_fingerprint": "51753d115110a5883651f0c7afce85f5868b9384dbd5579fc317c29aed239e07",
      "size_bytes": 3731,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\build_lto031_lto032_source_contract_registry.py",
      "ast_status": "PARSED",
      "parser_code_hash": "df05e01e4b9b57302883b96edee5e8a6ddac15421f1514a0ab843c6f3d0e83c5",
      "path": "scripts/build_lto031_lto032_source_contract_registry.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/build_lto031_lto032_source_contract_registry.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "build_parser",
          "main",
          "render_operations_summary",
          "utc_now_iso"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "json",
          "pathlib",
          "scripts",
          "src",
          "sys"
        ],
        "markers": {
          "schema_version": true
        }
      },
      "shape_fingerprint": "06b4718fa8741fa45a9a1e44e53bdf5e5e9736c943b42b6d09ec3dbdd79fa0ac",
      "size_bytes": 5878,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\build_lto031_lto032_source_unblocking_plan.py",
      "ast_status": "PARSED",
      "parser_code_hash": "b0d1ba528b368a1afbf76dd7df7d07955d5d0dc52bba5128bc05961da99b366d",
      "path": "scripts/build_lto031_lto032_source_unblocking_plan.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/build_lto031_lto032_source_unblocking_plan.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_fmt",
          "_source_keys",
          "_status_counts",
          "_table",
          "build_budget_policy",
          "build_parser",
          "build_payload",
          "build_phases",
          "build_source_contracts",
          "build_validation_gates",
          "file_hash",
          "main",
          "read_json",
          "render_goal_extension",
          "render_markdown",
          "source_signature",
          "utc_now_iso",
          "write_outputs"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "hashlib",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "schema_version": true,
          "scid": true
        }
      },
      "shape_fingerprint": "396cd142f764ca7f9bf5721be6c400ce6a908caefb4083946549293b787ae437",
      "size_bytes": 45572,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\build_lto032_options_gamma_vrp_source_manifests.py",
      "ast_status": "PARSED",
      "parser_code_hash": "a68dff4625c3e621315db9c1ee98cf771c54fc36baa2761d1db6b5a13ea7a3fe",
      "path": "scripts/build_lto032_options_gamma_vrp_source_manifests.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/build_lto032_options_gamma_vrp_source_manifests.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "build_parser",
          "main"
        ],
        "imports": [
          "__future__",
          "argparse",
          "json",
          "pathlib",
          "scripts",
          "src",
          "sys"
        ],
        "markers": {}
      },
      "shape_fingerprint": "954d45b4991cdeba5a866226c1d49e01c37619b19d99b103015f72351ed97e61",
      "size_bytes": 3152,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\build_master_research_queue_state.py",
      "ast_status": "PARSED",
      "parser_code_hash": "aab894dffb378343de93af662973db7fe0bdf80bac8d5c59b3db029d1e9abfa6",
      "path": "scripts/build_master_research_queue_state.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/build_master_research_queue_state.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "apply_overlay",
          "backlog_delta",
          "base_priority",
          "build_parser",
          "build_payload",
          "build_queue",
          "default_item",
          "fmt",
          "lane6_priority620_overlay",
          "lane6_tail_overlay",
          "lane7_overlay",
          "lane_for_item",
          "main",
          "normalize_status",
          "parse_backlog",
          "split_markdown_row",
          "summarize",
          "table",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "re",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "parquet": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "cae5b45affb9c46c90ffea7163f9fa0f9480011433fe141abca13933bfbaa4ba",
      "size_bytes": 117523,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\build_orderflow_event_manifest.py",
      "ast_status": "PARSED",
      "parser_code_hash": "22489c71be9d183e4043eeedd9cdcb8d1cf33b736de4a6e5053b01e4c04f3945",
      "path": "scripts/build_orderflow_event_manifest.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/build_orderflow_event_manifest.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "build_parser",
          "main",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true
        }
      },
      "shape_fingerprint": "da3db2076fd1ee4b391c11cb1de6350640e27362714f32699d357433d4dab237",
      "size_bytes": 5006,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\build_orderflow_forward_collection_plan.py",
      "ast_status": "PARSED",
      "parser_code_hash": "d1136d5e8c5f14f4b93422349cd64e03d058cd9ade804d56ff5b88c66eb07a68",
      "path": "scripts/build_orderflow_forward_collection_plan.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/build_orderflow_forward_collection_plan.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_event_class_count",
          "_fmt_cost",
          "_is_after_cap",
          "_sorted_counter",
          "build_collection_actions",
          "build_parser",
          "build_payload",
          "coverage_by_symbol",
          "load_json",
          "load_optional_json",
          "main",
          "read_jsonl",
          "summarize_feature_diag",
          "summarize_fetch_plan",
          "summarize_manifest",
          "summarize_source_log",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "e7f8440607dd41d2d28ea6efb9dba48416c087717b461bd370b8fadb7b612830",
      "size_bytes": 26453,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\build_orderflow_mbo_full_day_manifest.py",
      "ast_status": "PARSED",
      "parser_code_hash": "b9fd37c6dc798d728598b6d007e8e4d2e846b60f200daf4f6c1fcabf5c92c655",
      "path": "scripts/build_orderflow_mbo_full_day_manifest.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/build_orderflow_mbo_full_day_manifest.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "build_parser",
          "build_payload",
          "load_json",
          "main",
          "write_json",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "collections",
          "datetime",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "schema_version": true
        }
      },
      "shape_fingerprint": "576b6e2bd69f07880def0fd0ec7336a43c8ccacf6d495cf3b499f6479b95abdf",
      "size_bytes": 8861,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\build_orderflow_shadow_data_acceleration_plan.py",
      "ast_status": "PARSED",
      "parser_code_hash": "aea1d409c543b769a2eb42df852cd3d35546945c06bf23c7835ed6aecca14ca8",
      "path": "scripts/build_orderflow_shadow_data_acceleration_plan.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/build_orderflow_shadow_data_acceleration_plan.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "_file_hash",
          "_fmt",
          "_get",
          "_table",
          "build_parser",
          "build_payload",
          "main",
          "read_json",
          "render_markdown",
          "source_signature",
          "utc_now_iso",
          "write_outputs"
        ],
        "imports": [
          "__future__",
          "argparse",
          "datetime",
          "hashlib",
          "json",
          "pathlib",
          "src",
          "sys",
          "typing"
        ],
        "markers": {
          "schema_version": true
        }
      },
      "shape_fingerprint": "d42ea663f93fe295fd07b5fa86ae5d6653c43c220f9154ba84d1f132578d57bf",
      "size_bytes": 18279,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\build_raw_ohlc_prefill_delivery_path.py",
      "ast_status": "PARSED",
      "parser_code_hash": "027974a69a579dfeadd4aba4db03149aa6ba599abaef7d48dff0aeb06257186a",
      "path": "scripts/build_raw_ohlc_prefill_delivery_path.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/build_raw_ohlc_prefill_delivery_path.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [
          "PathIndex"
        ],
        "functions": [
          "__post_init__",
          "ambiguity_flags",
          "between",
          "build_parser",
          "build_payload",
          "capture_setup",
          "delivery_structure_flags",
          "detect_fill_state",
          "fill_hit",
          "fmt",
          "high_low_close",
          "iso",
          "load_path_indexes",
          "load_setup_rows",
          "m15_bars_between",
          "main",
          "max_run",
          "parse_cohort",
          "parse_utc",
          "pct",
          "row_snapshot",
          "select_prefill_window",
          "source_inventory",
          "summarize",
          "table",
          "write_json",
          "write_jsonl",
          "write_markdown"
        ],
        "imports": [
          "__future__",
          "argparse",
          "bisect",
          "collections",
          "dataclasses",
          "datetime",
          "json",
          "pathlib",
          "scripts",
          "sys",
          "typing"
        ],
        "markers": {
          "as_of": true,
          "jsonl": true,
          "schema_version": true
        }
      },
      "shape_fingerprint": "7d90e2f7555f5daafc002ec36d33679a81bfdaede1ea4a3b204906058a771272",
      "size_bytes": 29096,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    },
    {
      "absolute_path": "C:\\tmp\\gtos_nextwave\\EXP_R1_LINEAGE\\scripts\\build_science_goal_program.py",
      "ast_status": "PARSED",
      "parser_code_hash": "2ea6b5b541bba3c4330d9bcaab08f44d85d942903dc9470352159bcf7f1ebab5",
      "path": "scripts/build_science_goal_program.py",
      "producer_file_provenance": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        "path": "scripts/build_science_goal_program.py",
        "source_checkout": "current_git_worktree"
      },
      "shape": {
        "classes": [],
        "functions": [
          "build_parser",
          "main"
        ],
        "imports": [
          "__future__",
          "argparse",
          "json",
          "pathlib",
          "src",
          "sys"
        ],
        "markers": {
          "schema_version": true
        }
      },
      "shape_fingerprint": "191cbbe4d8429dd9ace693486fc9beb0b67546822904a99c8e6a3779aaa92f1f",
      "size_bytes": 1993,
      "source_status": "HASHED_PARSER_CONTROL_FILE"
    }
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL",
  "schema_shape_file_count": 120,
  "schema_shape_rows": [
    {
      "key_shape_fingerprint": "cf293eb155084e7144cafae343181d07dcda4cafff5944f1432afd0d1debeb66",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/00_control/G10_GOAL_STATUS_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/00_control/G10_GOAL_STATUS_2026-05-06.json",
      "shape": {
        "blockers": [
          "str"
        ],
        "commit_sha": "NoneType",
        "files_written": [
          "str"
        ],
        "lane_id": "str",
        "lane_status": "str",
        "next_questions": [
          "str"
        ],
        "promotion_verdict": "str",
        "tests_run": [
          "str"
        ]
      },
      "size_bytes": 3635,
      "source_hash": "9c837195ae33df8afca6bb7859c65ecaadbb85183da0be734162caebed195f56",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "blockers",
        "commit_sha",
        "files_written",
        "lane_id",
        "lane_status",
        "next_questions",
        "promotion_verdict",
        "tests_run"
      ]
    },
    {
      "key_shape_fingerprint": "71b2bdd898d593cda1647c0e909abb18dd18967971d9aa46d0a1becba26fc171",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/00_control/G11_DATA_SOURCES_EXPANSION_GOAL_STATUS_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/00_control/G11_DATA_SOURCES_EXPANSION_GOAL_STATUS_2026-05-06.json",
      "shape": {
        "blockers": [
          "str"
        ],
        "commit_sha": "NoneType",
        "commit_sha_note": "str",
        "files_written": [
          "str"
        ],
        "lane_id": "str",
        "lane_status": "str",
        "next_questions": [
          "str"
        ],
        "promotion_verdict": "str",
        "tests_run": [
          "str"
        ]
      },
      "size_bytes": 2927,
      "source_hash": "34bccc81b31f41a46ce1a5f784595fda633ad846b35221933f907e54018b3953",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "blockers",
        "commit_sha",
        "commit_sha_note",
        "files_written",
        "lane_id",
        "lane_status",
        "next_questions",
        "promotion_verdict",
        "tests_run"
      ]
    },
    {
      "key_shape_fingerprint": "bb662d3a43557103b8c8e0bf5003c3c7fda9feb495458ec425bf73e1ca978279",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/00_control/G11_DATA_SOURCES_EXPANSION_SOURCE_CONTRACTS_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/00_control/G11_DATA_SOURCES_EXPANSION_SOURCE_CONTRACTS_2026-05-06.json",
      "shape": [
        {
          "access_legal_state": "str",
          "allowed_feature_role": "str",
          "cache_path": "str",
          "cost_rule": "str",
          "promotion_verdict": "str",
          "publication_asof_timestamp_rule": "str",
          "source_id": "str",
          "url_or_vendor": "str",
          "validation_safe": "bool",
          "validation_safe_blockers": [
            "str"
          ]
        }
      ],
      "size_bytes": 7634,
      "source_hash": "778ad27d73da700b8191569bc64c682c7667ab6408d026576b105546676c29eb",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": []
    },
    {
      "key_shape_fingerprint": "dbb966cbae0cf4b0799a3275925003fb7adfd60356ae54adf99ff46f82d7070e",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/00_control/G1_VALIDATION_STATISTICS_GOAL_STATUS_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/00_control/G1_VALIDATION_STATISTICS_GOAL_STATUS_2026-05-06.json",
      "shape": {
        "blockers": [
          "str"
        ],
        "commit_sha": "str",
        "files_written": [
          "str"
        ],
        "lane_id": "str",
        "lane_status": "str",
        "next_questions": [
          "str"
        ],
        "promotion_verdict": "str",
        "tests_run": [
          "str"
        ]
      },
      "size_bytes": 4893,
      "source_hash": "1675a279f73d27639e28ac4fa18397a8faab31492c1256d0332cbd05dd30ae21",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "blockers",
        "commit_sha",
        "files_written",
        "lane_id",
        "lane_status",
        "next_questions",
        "promotion_verdict",
        "tests_run"
      ]
    },
    {
      "key_shape_fingerprint": "89b49b14f8404c00c07218a8715a5e4aab216af5ac8af64fc4277192dd9bcda5",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/00_control/G1_VALIDATION_STATISTICS_SOURCE_CONTRACTS_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/00_control/G1_VALIDATION_STATISTICS_SOURCE_CONTRACTS_2026-05-06.json",
      "shape": {
        "created_at_utc": "str",
        "lane_id": "str",
        "promotion_verdict": "str",
        "rows": [
          {
            "access_legal_state": "str",
            "allowed_feature_role": "str",
            "cache_path": "str",
            "cost_rule": "str",
            "promotion_verdict": "str",
            "publication_asof_timestamp_rule": "str",
            "source_id": "str",
            "url_or_vendor": "str",
            "validation_safe": "bool",
            "validation_safe_blockers": [
              "str"
            ]
          }
        ],
        "schema": "str",
        "source_index": "str"
      },
      "size_bytes": 9440,
      "source_hash": "c00b240ca57b67cdf0a59135e0f131e1c496426ce1752a128162612bce33a0e9",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "created_at_utc",
        "lane_id",
        "promotion_verdict",
        "rows",
        "schema",
        "source_index"
      ]
    },
    {
      "key_shape_fingerprint": "080620768eddd9e4e646fd18c7fcb51c35f16ad19d5db83b9f955c8a39813b01",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/00_control/G3_GEOMETRY_SIGNAL_GOAL_STATUS_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/00_control/G3_GEOMETRY_SIGNAL_GOAL_STATUS_2026-05-06.json",
      "shape": {
        "blockers": [
          "str"
        ],
        "commit_sha": "str",
        "files_written": [
          "str"
        ],
        "forbidden_surface_check": {
          "canary_changed": "bool",
          "execution_changed": "bool",
          "live_trading_prompt_changed": "bool",
          "mt5_changed": "bool",
          "order_behavior_changed": "bool",
          "paid_data_changed": "bool",
          "permissions_changed": "bool",
          "risk_changed": "bool",
          "safety_gate_changed": "bool",
          "selector_changed": "bool"
        },
        "generated_at_utc": "str",
        "lane_id": "str",
        "lane_status": "str",
        "next_questions": [
          "str"
        ],
        "promotion_verdict": "str",
        "tests_run": [
          {
            "command": "str",
            "result": "str"
          }
        ]
      },
      "size_bytes": 3741,
      "source_hash": "73a00ac95f55606ea83526f8b29ac9e3563816fcd5ea26813fcc1c63766d5e35",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "blockers",
        "commit_sha",
        "files_written",
        "forbidden_surface_check",
        "generated_at_utc",
        "lane_id",
        "lane_status",
        "next_questions",
        "promotion_verdict",
        "tests_run"
      ]
    },
    {
      "key_shape_fingerprint": "dbb966cbae0cf4b0799a3275925003fb7adfd60356ae54adf99ff46f82d7070e",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/00_control/G4_MICROSTRUCTURE_AUCTION_GOAL_STATUS_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/00_control/G4_MICROSTRUCTURE_AUCTION_GOAL_STATUS_2026-05-06.json",
      "shape": {
        "blockers": [
          "str"
        ],
        "commit_sha": "str",
        "files_written": [
          "str"
        ],
        "lane_id": "str",
        "lane_status": "str",
        "next_questions": [
          "str"
        ],
        "promotion_verdict": "str",
        "tests_run": [
          "str"
        ]
      },
      "size_bytes": 3384,
      "source_hash": "f0ef6707638fcf16fc94e224404cbffac8f0da6f62681295d2f8dafc0b513eb1",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "blockers",
        "commit_sha",
        "files_written",
        "lane_id",
        "lane_status",
        "next_questions",
        "promotion_verdict",
        "tests_run"
      ]
    },
    {
      "key_shape_fingerprint": "bb662d3a43557103b8c8e0bf5003c3c7fda9feb495458ec425bf73e1ca978279",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/00_control/G4_MICROSTRUCTURE_AUCTION_SOURCE_CONTRACTS_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/00_control/G4_MICROSTRUCTURE_AUCTION_SOURCE_CONTRACTS_2026-05-06.json",
      "shape": [
        {
          "access_legal_state": "str",
          "allowed_feature_role": "str",
          "cache_path": "str",
          "cost_rule": "str",
          "promotion_verdict": "str",
          "publication_asof_timestamp_rule": "str",
          "source_id": "str",
          "url_or_vendor": "str",
          "validation_safe": "bool",
          "validation_safe_blockers": [
            "str"
          ]
        }
      ],
      "size_bytes": 6145,
      "source_hash": "1a5d9d79b7e3dbffca62eb415157da8b7e224fdc8b157d7109bab231f685432c",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": []
    },
    {
      "key_shape_fingerprint": "cf293eb155084e7144cafae343181d07dcda4cafff5944f1432afd0d1debeb66",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/00_control/G5_GOAL_STATUS_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/00_control/G5_GOAL_STATUS_2026-05-06.json",
      "shape": {
        "blockers": [
          "str"
        ],
        "commit_sha": "NoneType",
        "files_written": [
          "str"
        ],
        "lane_id": "str",
        "lane_status": "str",
        "next_questions": [
          "str"
        ],
        "promotion_verdict": "str",
        "tests_run": [
          "str"
        ]
      },
      "size_bytes": 3334,
      "source_hash": "6dff1704765d27d299ec4f1e42c0430f5a30e7efb4c6fd45341a706a1d72cf29",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "blockers",
        "commit_sha",
        "files_written",
        "lane_id",
        "lane_status",
        "next_questions",
        "promotion_verdict",
        "tests_run"
      ]
    },
    {
      "key_shape_fingerprint": "cf293eb155084e7144cafae343181d07dcda4cafff5944f1432afd0d1debeb66",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/00_control/G7_MACRO_CROSS_ASSET_GOAL_STATUS_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/00_control/G7_MACRO_CROSS_ASSET_GOAL_STATUS_2026-05-06.json",
      "shape": {
        "blockers": [
          "str"
        ],
        "commit_sha": "NoneType",
        "files_written": [
          "str"
        ],
        "lane_id": "str",
        "lane_status": "str",
        "next_questions": [
          "str"
        ],
        "promotion_verdict": "str",
        "tests_run": [
          "str"
        ]
      },
      "size_bytes": 4915,
      "source_hash": "1d5d61d41b22b0a1799a16fcb31995e30022b1260a569fcb830e04ed6d4d9830",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "blockers",
        "commit_sha",
        "files_written",
        "lane_id",
        "lane_status",
        "next_questions",
        "promotion_verdict",
        "tests_run"
      ]
    },
    {
      "key_shape_fingerprint": "947cf6a235cbe4b74fe1ebb87d2e7a9d38c6791c56e19c0912d575e130294cfd",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/00_control/G8_OPTIONS_VOL_GOAL_STATUS_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/00_control/G8_OPTIONS_VOL_GOAL_STATUS_2026-05-06.json",
      "shape": {
        "blockers": [
          "str"
        ],
        "commit_sha": "NoneType",
        "files_written": [
          "str"
        ],
        "generated_at_utc": "str",
        "lane_id": "str",
        "lane_status": "str",
        "next_questions": [
          "str"
        ],
        "promotion_verdict": "str",
        "schema": "str",
        "tests_run": [
          "str"
        ]
      },
      "size_bytes": 3182,
      "source_hash": "cabfdec97604c9aecd974b2d5d7a9e3924a219d5e1bdd28a74bd15e238350a22",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "blockers",
        "commit_sha",
        "files_written",
        "generated_at_utc",
        "lane_id",
        "lane_status",
        "next_questions",
        "promotion_verdict",
        "schema",
        "tests_run"
      ]
    },
    {
      "key_shape_fingerprint": "f219e4dd6fef41d7db1991d57311f51736e105c935c0264fce14acb8741a8ee8",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/00_control/G8_OPTIONS_VOL_SOURCE_INDEX_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/00_control/G8_OPTIONS_VOL_SOURCE_INDEX_2026-05-06.json",
      "shape": {
        "fetch_notes": [
          "str"
        ],
        "generated_at_utc": "str",
        "lane_id": "str",
        "promotion_verdict": "str",
        "raw_cache_dir": "str",
        "schema": "str",
        "sources": [
          {
            "cache_path": "str",
            "first_date": "str",
            "http_status": "int",
            "last_date": "str",
            "promotion_verdict": "str",
            "rows": "int",
            "source_id": "str",
            "url": "str",
            "use": "str",
            "validation_safe": "bool",
            "validation_safe_blockers": [
              "str"
            ]
          }
        ]
      },
      "size_bytes": 6525,
      "source_hash": "ddf3b7305a046d31d69c8e7e0c2dbee3a6e19b0a356cccfc4ffc4c56cd612284",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "fetch_notes",
        "generated_at_utc",
        "lane_id",
        "promotion_verdict",
        "raw_cache_dir",
        "schema",
        "sources"
      ]
    },
    {
      "key_shape_fingerprint": "cf293eb155084e7144cafae343181d07dcda4cafff5944f1432afd0d1debeb66",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/00_control/G9_AI_ML_SYSTEMS_GOAL_STATUS_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/00_control/G9_AI_ML_SYSTEMS_GOAL_STATUS_2026-05-06.json",
      "shape": {
        "blockers": [
          "str"
        ],
        "commit_sha": "NoneType",
        "files_written": [
          "str"
        ],
        "lane_id": "str",
        "lane_status": "str",
        "next_questions": [
          "str"
        ],
        "promotion_verdict": "str",
        "tests_run": [
          "str"
        ]
      },
      "size_bytes": 3435,
      "source_hash": "4979b681c2b55afdd16cf9bf2f36b2382acc12533b18756deb017b2556ca5c4d",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "blockers",
        "commit_sha",
        "files_written",
        "lane_id",
        "lane_status",
        "next_questions",
        "promotion_verdict",
        "tests_run"
      ]
    },
    {
      "key_shape_fingerprint": "69ad03448b1d919252c7b288b0d12fac8d3ee10a8a3a003c78d97eb5bf064e31",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/00_control/G9_AI_ML_SYSTEMS_SOURCE_CONTRACTS_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/00_control/G9_AI_ML_SYSTEMS_SOURCE_CONTRACTS_2026-05-06.json",
      "shape": {
        "created_at_utc": "str",
        "lane_id": "str",
        "promotion_verdict": "str",
        "rows": [
          {
            "access_legal_state": "str",
            "allowed_feature_role": "str",
            "cache_path": "str",
            "cost_rule": "str",
            "promotion_verdict": "str",
            "publication_asof_timestamp_rule": "str",
            "source_id": "str",
            "url_or_vendor": "str",
            "validation_safe": "bool",
            "validation_safe_blockers": [
              "str"
            ]
          }
        ],
        "schema": "str"
      },
      "size_bytes": 7149,
      "source_hash": "fcc1ba5216589b63050be4a3cafa82211ee7409b7af1ebcc71b2938aaa01c437",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "created_at_utc",
        "lane_id",
        "promotion_verdict",
        "rows",
        "schema"
      ]
    },
    {
      "key_shape_fingerprint": "c56df4fc444e3a81520f998af60546b128309fbe01c223ee32fe56ff11287405",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/00_control/GOAL_STATUS_REGISTRY_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/00_control/GOAL_STATUS_REGISTRY_2026-05-06.json",
      "shape": [
        {
          "blockers": [
            "str"
          ],
          "cd2_reconciliation": {
            "accepted_master_prereg_rows": [
              "dict"
            ],
            "ai_calls": "int",
            "blocked_cd2_master_actions": [
              "dict"
            ],
            "canary_calls": "int",
            "cd2_artifacts": [
              "dict"
            ],
            "cd2_merge_commit": "str",
            "checked_at_utc": "str",
            "external_cash_spend_usd": "float",
            "g12_launch_status": "str",
            "head_reconciled": "str",
            "lane_id": "str",
            "live_behavior_changed": "bool",
            "master_row_delta": {
              "experiment_prereg_rows_added": "int",
              "hypothesis_rows_added": "int",
              "mechanism_rows_added": "int",
              "source_contract_rows_added": "int",
              "survivor_backlog_rows_added": "int"
            },
            "mt5_calls": "int",
            "order_calls": "int",
            "paid_data_calls": "int",
            "promotion_verdict": "str",
            "public_web_fetches_by_g0": "int",
            "source_policy": {
              "source_contract_rows_added": "int",
              "source_registry_action": "str",
              "validation_safe_true_allowed": "bool",
              "validation_safe_true_rows_after_reconciliation": "int"
            },
            "status": "str",
            "wave2_primary_reconciliation_commit": "str",
            "wave2_status_commit": "str"
          },
          "checked_at_utc": "str",
          "commit_sha": "str",
          "files_written": [
            "str"
          ],
          "lane_id": "str",
          "lane_status": "str",
          "next_questions": [
            "str"
          ],
          "promotion_verdict": "str",
          "tests_run": [
            "str"
          ]
        }
      ],
      "size_bytes": 67509,
      "source_hash": "ca0a6e8876dbe43d7d91f4ee4e4dce6d512b034cf98178a6b4fb7a8737ca7f38",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": []
    },
    {
      "key_shape_fingerprint": "d4b040bd55de72f59586bb416039e0bdadcc60c02428e968e09e9ab7f7090bb9",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/00_control/SCHEMA_CONTRACTS_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/00_control/SCHEMA_CONTRACTS_2026-05-06.json",
      "shape": {
        "experiment_prereg_v1": {
          "field_notes": {
            "dsr_pbo_effective_n_policy": "str",
            "duplicate_policy": "str",
            "frozen_at_utc": "str",
            "label_separation_policy": "str",
            "outcome_review_opened": "str"
          },
          "promotion_boundary": "str",
          "required_fields": [
            "str"
          ],
          "schema_name": "str"
        },
        "goal_status_v1": {
          "field_notes": {
            "commit_sha": "str",
            "promotion_verdict": "str"
          },
          "promotion_boundary": "str",
          "required_fields": [
            "str"
          ],
          "schema_name": "str"
        },
        "science_hypothesis_v1": {
          "field_notes": {
            "alternative": "str",
            "label_class": "str",
            "no_leak_fields": "str",
            "null": "str",
            "promotion_blockers": "str",
            "sample_floor": "str"
          },
          "promotion_boundary": "str",
          "required_fields": [
            "str"
          ],
          "schema_name": "str"
        },
        "science_mechanism_v1": {
          "field_notes": {
            "existing_gtos_overlap": "str",
            "expected_signature": "str",
            "killed_route_check": "str",
            "known_decay_mode": "str",
            "market_behavior": "str",
            "mechanism_id": "str",
            "required_data": "str",
            "science_domain": "str"
          },
          "promotion_boundary": "str",
          "required_fields": [
            "str"
          ],
          "schema_name": "str"
        },
        "source_contract_v2": {
          "field_notes": {
            "allowed_feature_role": "str",
            "publication_asof_timestamp_rule": "str",
            "validation_safe": "str"
          },
          "promotion_boundary": "str",
          "required_fields": [
            "str"
          ],
          "schema_name": "str"
        }
      },
      "size_bytes": 4534,
      "source_hash": "646a291896ebced23bcb7e2a68f41b73d7f157303c9856f54d29c358c06c247b",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "experiment_prereg_v1",
        "goal_status_v1",
        "science_hypothesis_v1",
        "science_mechanism_v1",
        "source_contract_v2"
      ]
    },
    {
      "key_shape_fingerprint": "26e8b3e1249d5811b8cb61d58905bfe5ad04d52f8a547f13f924e1610a4dd17b",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/00_control/SOURCE_BUDGET_LEDGER_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/00_control/SOURCE_BUDGET_LEDGER_2026-05-06.json",
      "shape": {
        "allowed_now": [
          "str"
        ],
        "budget_posture": "str",
        "cd2_reconciliation": {
          "cd2_merge_commit": "str",
          "checked_at_utc": "str",
          "head_reconciled": "str",
          "new_external_cash_spend_usd": "float",
          "new_public_fetches_by_g0": "int",
          "paid_data_calls_by_g0": "int",
          "promotion_verdict": "str",
          "source_contract_rows_added": "int",
          "source_contract_rows_total": "int",
          "validation_safe_true": "int"
        },
        "current_external_cash_spend_cap_usd": "float",
        "disallowed_until_owner_approval": [
          "str"
        ],
        "ledger_rows": [],
        "per_source_limit_usd": "NoneType",
        "post_g12_closeout": {
          "checked_at_utc": "str",
          "head_read": "str",
          "new_external_cash_spend_usd": "float",
          "new_public_fetches_by_g0": "int",
          "outcome_reviews_opened": "int",
          "paid_data_calls_by_g0": "int",
          "promotion_verdict": "str",
          "source_validation_decision": "str",
          "survivor_backlog_rows_added": "int",
          "validation_safe_true": "int"
        },
        "promotion_verdict": "str",
        "schema": "str",
        "spend_allowed": "bool",
        "wave1_reconciliation": {
          "checked_at_utc": "str",
          "main_head_reconciled": "str",
          "new_external_cash_spend_usd": "float",
          "paid_data_calls": "int",
          "promotion_verdict": "str",
          "source_contract_registry": "str",
          "source_contract_rows": "int",
          "validation_safe_false": "int",
          "validation_safe_true": "int"
        },
        "wave2_reconciliation": {
          "checked_at_utc": "str",
          "head_reconciled": "str",
          "new_external_cash_spend_usd": "float",
          "new_public_fetches_by_g0": "int",
          "paid_data_calls_by_g0": "int",
          "promotion_verdict": "str",
          "source_contract_registry": "str",
          "source_contract_rows": "int",
          "validation_safe_false": "int",
          "validation_safe_true": "int",
          "wave2_merge_commit": "str"
        }
      },
      "size_bytes": 2740,
      "source_hash": "fefe5ea3d4981bf916c7f2bd3474ab97a19fdb607510e37a7809a8dccd084b2a",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "allowed_now",
        "budget_posture",
        "cd2_reconciliation",
        "current_external_cash_spend_cap_usd",
        "disallowed_until_owner_approval",
        "ledger_rows",
        "per_source_limit_usd",
        "post_g12_closeout",
        "promotion_verdict",
        "schema",
        "spend_allowed",
        "wave1_reconciliation",
        "wave2_reconciliation"
      ]
    },
    {
      "key_shape_fingerprint": "3c501f537a7e8dce6b7bb93bd1220165c0a52fbb5ea0b60201e7dbf45fbbfd32",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/00_control/SOURCE_CONTRACT_REGISTRY_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/00_control/SOURCE_CONTRACT_REGISTRY_2026-05-06.json",
      "shape": {
        "cd2_reconciliation": {
          "accepted_master_prereg_rows": [
            {
              "assignment_id": "str",
              "experiment_id": "str",
              "hypothesis_id": "str",
              "lane_id": "str",
              "promotion_verdict": "str",
              "source_file": "str"
            }
          ],
          "ai_calls": "int",
          "blocked_cd2_master_actions": [
            {
              "artifacts": "list",
              "assignment_id": "str",
              "lane": "str",
              "master_action": "str",
              "promotion_verdict": "str",
              "reason": "str"
            }
          ],
          "canary_calls": "int",
          "cd2_artifacts": [
            {
              "artifacts": "list",
              "assignment_id": "str",
              "commit": "str",
              "g12_focus": "str",
              "lane": "str",
              "master_action": "str",
              "reason": "str",
              "title": "str"
            }
          ],
          "cd2_merge_commit": "str",
          "checked_at_utc": "str",
          "external_cash_spend_usd": "float",
          "g12_launch_status": "str",
          "head_reconciled": "str",
          "lane_id": "str",
          "live_behavior_changed": "bool",
          "master_row_delta": {
            "experiment_prereg_rows_added": "int",
            "hypothesis_rows_added": "int",
            "mechanism_rows_added": "int",
            "source_contract_rows_added": "int",
            "survivor_backlog_rows_added": "int"
          },
          "mt5_calls": "int",
          "order_calls": "int",
          "paid_data_calls": "int",
          "promotion_verdict": "str",
          "public_web_fetches_by_g0": "int",
          "source_policy": {
            "source_contract_rows_added": "int",
            "source_registry_action": "str",
            "validation_safe_true_allowed": "bool",
            "validation_safe_true_rows_after_reconciliation": "int"
          },
          "status": "str",
          "wave2_primary_reconciliation_commit": "str",
          "wave2_status_commit": "str"
        },
        "governor_reconciliation": {
          "checked_at_utc": "str",
          "governor_lane": "str",
          "head_reconciled": "str",
          "lane_blockers": {
            "G1": [
              "str"
            ],
            "G10": [
              "str"
            ],
            "G11": [
              "str"
            ],
            "G2": [
              "str"
            ],
            "G3": [
              "str"
            ],
            "G4": [
              "str"
            ],
            "G5": [
              "str"
            ],
            "G6": [
              "str"
            ],
            "G7": [
              "str"
            ],
            "G8": [
              "str"
            ],
            "G9": [
              "str"
            ]
          },
          "lane_counts": {
            "G1": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G10": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G11": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G2": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G3": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G4": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G5": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G6": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G7": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G8": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G9": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            }
          },
          "missing_lane_artifacts": [
            {
              "artifact_gap": "str",
              "blocking_master_merge": "bool",
              "lane_id": "str"
            }
          ],
          "primary_reconciliation_commit_sha": "str",
          "promotion_verdict": "str",
          "row_counts": {
            "experiment_prereg_rows_merged": "int",
            "goal_status_rows_total": "int",
            "hypothesis_rows_merged": "int",
            "mechanism_rows_merged": "int",
            "source_contract_rows_reconciled": "int"
          },
          "schema_check": {
            "duplicate_report": {
              "experiment_id_duplicates": "list",
              "hypothesis_id_duplicates": "list",
              "mechanism_id_duplicates": "list",
              "source_id_duplicates": "list"
            },
            "experiment_prereg_summary": {
              "experiment_prereg_rows": "int",
              "outcome_review_opened_false": "int",
              "outcome_review_opened_true": "int"
            },
            "hard_blocker_issue_count": "int",
            "label_class_counts_after_g0_normalization": {
              "broker_actual_r": "int",
              "context_only": "int",
              "lifecycle_no_fill": "int",
              "observation_only": "int",
              "synthetic_path_r": "int"
            },
            "no_leak_semantic_blockers": [
              "dict"
            ],
            "normalizations": [
              "dict"
            ],
            "relationship_issues": [],
            "required_field_issues": [],
            "source_contract_summary": {
              "blocked_source_rows": "list",
              "source_contract_rows": "int",
              "validation_safe_false": "int",
              "validation_safe_true": "int"
            },
            "source_reference_issues": [
              "dict"
            ]
          },
          "scope": "str",
          "wave2_merge_commit": "str"
        },
        "post_g12_closeout": {
          "checked_at_utc": "str",
          "future_clearance_required": "str",
          "g12_source_validation_decision": "str",
          "head_read": "str",
          "promotion_verdict": "str",
          "source_contract_rows": "int",
          "validation_safe_true": "int"
        },
        "promotion_verdict": "str",
        "row_sources": {
          "G1-SRC-LOCAL-GTOS-METHODOLOGY-GATE": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G1-SRC-LOCAL-GTOS-SCIENCE-SCHEMAS": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G1-SRC-PUBLIC-NATURE-LI-JI-EFFECTIVE-TESTS": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G1-SRC-PUBLIC-PMC-TARGET-TRIAL-CAUSAL": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G1-SRC-PUBLIC-SKLEARN-TIMESERIES-GAP": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G1-SRC-PUBLIC-SSRN-DSR-BLOCKED": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G1-SRC-PUBLIC-SSRN-PBO-BLOCKED": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G1-SRC-PUBLIC-STATSMODELS-POWER-PROPORTIONS": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G1-SRC-PUBLIC-WHITE-REALITY-CHECK": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G1-SRC-PUBLIC-WMICH-PSEUDO-MATH-BACKTEST-OVERFITTING": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G10-SRC-LOCAL-EXECUTION-CODE": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G10-SRC-MT5-ACCOUNT-HISTORY-READONLY": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G10-SRC-NEIGHBOR-G1-G6-G9": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G10-SRC-PHASE3-PATH-REPLAY": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G10-SRC-PROP-FTMO-OFFICIAL": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G10-SRC-PROP-redacted_account-OFFICIAL": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G10-SRC-SHADOW-LIFECYCLE-SLIPPAGE": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G6-SRC-CNR-SHADOW": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G6-SRC-FUTURE-EXTERNAL": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G6-SRC-LIT-D10-GOLD": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G6-SRC-LIT-D14-MOMENTUM": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G6-SRC-LIT-D15-MEAN-REVERSION": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G6-SRC-LOCAL-GTOS-SHADOW-OHLC": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G6-SRC-OBMON": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G11-AUCTION-NASDAQ-LBMA": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G11-CBOE-OPTIONS-VOL": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G11-DATABENTO-GLBX-MDP3": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G11-LOCAL-G0-REGISTRIES": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G11-LOCAL-INSTRUMENT-EXPANSION": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G11-LOCAL-LTO031032-SOURCE-UNBLOCKING": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G11-OBSERVER-SOURCE-REGISTRY": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G11-PUBLIC-CFTC-FRED-BIS": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G11-SIERRA-SCID-DEPTH": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G2-FORWARD-SHADOW-LIFECYCLE": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G2-LOCAL-OHLC-RETURNS": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G2-OPTIONS-GAMMA-VRP": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G2-REGIME-DECAY-JOIN": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G2-SIERRA-DATABENTO-DEPTH": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G2-TICK-DEPTH-HAWKES": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G3-LOCAL-CONTEXT-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G3-LOCAL-FEATURE-CATALOGS-003": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G3-LOCAL-OHLCV-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G3-TICK-SIERRA-DATABENTO-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G3-WEB-DC-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G3-WEB-TDA-007": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G3-WEB-WAVELET-HAR-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G3-WEB-WAVELET-JUMPS-008": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G4-DATABENTO-GLBX-MDP3": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G4-LBMA-ICE-AUCTION": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G4-LOCAL-GTOS-ORDERFLOW-ARTIFACTS": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G4-MT5-TICKS-ACCOUNT-HISTORY": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G4-NASDAQ-NOII-CROSSES": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G4-PAPERS-MICROSTRUCTURE": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G4-SIERRA-DEPTH-SCID": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G5-ACADEMIC-LIT-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G5-AI-SHADOW-LOCAL-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G5-CFTC-COT-GOLD-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G5-GTRENDS-SMC-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G5-NEWS-CALENDAR-LOCAL-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G5-OANDA-ORDERBOOK-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G5-PROMPT-NEUTRAL-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G7-BIS-STATS-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G7-CFTC-COT-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G7-FED-ECONRES-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G7-FED-FOMC-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G7-FRED-RATES-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G7-ICE-DXY-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G7-LBMA-FIX-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G7-LOCAL-GTOS-MACRO-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G7-WGC-GOLDHUB-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G8-CBOE-DELAYED-CHAIN-BLOCKED-008": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G8-CBOE-METHODOLOGY-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G8-CBOE-VOL-CSV-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G8-FLASHALPHA-GEX-PROXY-003": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G8-GAMMA-VRP-LITERATURE-007": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G8-OFFICIAL-HISTORICAL-GEX-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G8-OPEX-CALENDAR-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G8-VRP-FORMULA-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G9-AITOOLS-CODE-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SRC-G9-COMPONENT3B-DOSSIER-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          }
        },
        "rows": [
          {
            "access_legal_state": "str",
            "allowed_feature_role": "str",
            "cache_path": "str",
            "cost_rule": "str",
            "promotion_verdict": "str",
            "publication_asof_timestamp_rule": "str",
            "source_id": "str",
            "url_or_vendor": "str",
            "validation_safe": "bool",
            "validation_safe_blockers": [
              "str"
            ]
          }
        ],
        "schema": "str",
        "status": "str"
      },
      "size_bytes": 146421,
      "source_hash": "0450a95b3bb5b9f3a7cdbf305d2e7d94a1a72bdd0cea973874058a15133a1847",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "cd2_reconciliation",
        "governor_reconciliation",
        "post_g12_closeout",
        "promotion_verdict",
        "row_sources",
        "rows",
        "schema",
        "status"
      ]
    },
    {
      "key_shape_fingerprint": "eb19dabab2279001c11bd275d0ca225f86490665ed19f4ec17cbcd4dc42721d3",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/01_domain_syntheses/G10_CD2_06_PREFILL_PATH_MISSING_FIELD_AUDIT_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/01_domain_syntheses/G10_CD2_06_PREFILL_PATH_MISSING_FIELD_AUDIT_2026-05-06.json",
      "shape": {
        "artifact": "str",
        "assignment_id": "str",
        "continuation_no_retrace_coverage": {
          "aggregate_counting_status_counts": {
            "COUNTABLE_PRIMARY_ONLY": "int",
            "EXCLUDED_BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP": "int",
            "EXCLUDED_DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE": "int"
          },
          "candidate_entry_model_captured": "int",
          "candidate_rows": "int",
          "exact_decision_entry_price_captured": "int",
          "later_path_outcome_status_counts": {
            "ENTRY_TOUCHED_UNRESOLVED": "int",
            "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH": "int"
          },
          "resolution_rows": "int",
          "source_blocker_counts": {
            "EXACT_DECISION_ENTRY_PRICE_NOT_CAPTURED": "int",
            "ORDERED_POST_ENTRY_M1_OR_TICK_PATH_NOT_CAPTURED": "int"
          },
          "stop_loss_captured": "int",
          "synthetic_r_status_counts": {
            "NOT_COMPUTED_SOURCE_BLOCKED": "int"
          },
          "take_profit_1_captured": "int",
          "target_area_model_captured": "int",
          "tick_order_claim_status_counts": {
            "NO_TICK_ORDER_CLAIM_M15_OHLC_ONLY": "int"
          }
        },
        "current_evidence_counts": {
          "candidate_ltf_path_order_rows": "int",
          "close_side_slippage_rows": "int",
          "continuation_no_retrace_candidate_rows": "int",
          "continuation_no_retrace_resolution_rows": "int",
          "pending_limit_lifecycle_audit_rows": "int",
          "pending_limit_lifecycle_rows": "int",
          "prefill_delivery_path_audit_rows": "int",
          "prefill_delivery_path_resolution_rows": "int",
          "prefill_delivery_path_rows": "int",
          "slippage_rows": "int"
        },
        "generated_at_utc": "str",
        "hypothesis_blockers": {
          "G10-HYP-PREFILL-003": [
            "str"
          ],
          "G10-HYP-XDOMAIN-008": [
            "str"
          ],
          "G6-HYP-002": [
            "str"
          ],
          "HYP-G4-FILL-QUALITY-009": [
            "str"
          ]
        },
        "lane_id": "str",
        "latest_prefill_audit_state": {
          "decision_prefill_no_leak_status_counts": {
            "NO_POST_OUTCOME_STATE_IN_PREFILL_DECISION_ROW": "int"
          },
          "derived_prefill_path_status_counts": {
            "DERIVED_FROM_CANDIDATE_PATH_ASOF": "int",
            "DERIVED_FROM_LTF_PATH_ORDER_ASOF": "int"
          },
          "documented_limitation_counts": {
            "COST_AWARE_MIN_R_SOURCE_NOT_CAPTURED": "int",
            "EXACT_PREFILL_CANDLE_SEQUENCE_SOURCE_NOT_CAPTURED": "int",
            "EXACT_PREFILL_TICK_SUMMARY_SOURCE_NOT_CAPTURED": "int",
            "POST_LOCK_REENTRY_ELIGIBILITY_SOURCE_NOT_CAPTURED": "int",
            "PREFILL_DELIVERY_REVERSAL_SCORER_NOT_IMPLEMENTED": "int",
            "PREFILL_SOURCE_HASH_NOT_CAPTURED": "int",
            "PREFILL_SOURCE_SYMBOL_NOT_CAPTURED": "int",
            "PREFILL_TRADE_ID_NOT_CAPTURED": "int"
          },
          "duplicate_aware_counting_status_counts": {
            "BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP": "int",
            "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY": "int",
            "DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE": "int"
          },
          "latest_by_candidate_rows": "int",
          "path_outcome_status_counts": {
            "ENTRY_TOUCHED_THEN_SL": "int",
            "ENTRY_TOUCHED_THEN_TP1": "int",
            "ENTRY_TOUCHED_UNRESOLVED": "int",
            "M15_PATH_AMBIGUOUS_TP1_AND_SL": "int",
            "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH": "int"
          },
          "prefill_source_capture_status_counts": {
            "PREFILL_DECISION_CORE_SOURCE_CAPTURED": "int"
          }
        },
        "ltf_ambiguity_coverage": {
          "ltf_status_counts": {
            "M1_PATH_RECOVERED": "int",
            "SOURCE_BLOCKED": "int"
          },
          "rows": "int",
          "same_m1_ambiguity_counts": {
            "False": "int",
            "True": "int"
          },
          "terminal_order_ambiguity_counts": {
            "False": "int",
            "True": "int",
            "blank_or_missing": "int"
          }
        },
        "next_capture_priorities": [
          "str"
        ],
        "non_claims": [
          "str"
        ],
        "pending_limit_lifecycle_coverage": {
          "captured": {
            "candidate_id": "int",
            "checked_candle_time_utc": "int",
            "decision_time_utc": "int",
            "entry_price": "int",
            "fill_no_fill_label": "int",
            "pending_created_time_utc": "int",
            "spread": "int",
            "stop_loss": "int",
            "take_profit_1": "int",
            "tick_ask": "int",
            "tick_bid": "int",
            "trade_id": "int"
          },
          "label_boundary": {
            "actual_r_captured": "int",
            "actual_r_missing_is_required_label_separation": "bool",
            "synthetic_path_r_captured": "int"
          },
          "missing_or_not_captured": {
            "broker_pending_order_created": "int",
            "fill_time_utc": "int",
            "mt5_order_ticket": "int",
            "native_pending_order_type": "int",
            "order_send_attempted": "int",
            "order_send_success": "int",
            "pending_order_mode": "int",
            "slippage_price": "int"
          },
          "rows": "int"
        },
        "prefill_decision_packet_coverage": {
          "captured": {
            "asof_cutoff_utc": "int",
            "cancel_expiry_abort_reason": "int",
            "candidate_id": "int",
            "decision_time_utc": "int",
            "entry_arming_time_utc": "int",
            "fvg_ob_swing_state_at_arm": "int",
            "original_poi_bounds": "int",
            "original_poi_bounds_poi_price_level": "int",
            "structural_setup_id": "int",
            "symbol": "int"
          },
          "decision_label_boundary": {
            "fill_delay_seconds_missing_is_correct_for_decision_packet": "bool",
            "fill_happened_missing_is_correct_for_decision_packet": "bool",
            "reversal_leg_timing_missing_is_correct_for_decision_packet": "bool"
          },
          "missing_or_not_captured": {
            "fill_delay_seconds": "int",
            "fill_happened": "int",
            "pre_fill_candles": "int",
            "pre_fill_ticks_summary": "int",
            "reversal_leg_timing": "int",
            "source_hash": "int",
            "source_symbol": "int",
            "trade_id": "int"
          },
          "rows": "int"
        },
        "promotion_verdict": "str",
        "scope_boundary": {
          "forbidden_surface_edits": "bool",
          "live_strategy_scoring": "bool",
          "master_registry_edits": "bool",
          "research_only": "bool"
        },
        "seed_rows": [
          "str"
        ],
        "strategy_follow_join_coverage": {
          "entry_price_available": "int",
          "pending_mode_fields_available": "int",
          "prefill_rows_joined_by_candidate_id": "int",
          "stop_loss_available": "int",
          "take_profit_1_available": "int"
        }
      },
      "size_bytes": 7631,
      "source_hash": "14c948727cc4aa2dbac62ae9864c9203f0fa5d60c982d57ddf39d26c1b61b753",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "artifact",
        "assignment_id",
        "continuation_no_retrace_coverage",
        "current_evidence_counts",
        "generated_at_utc",
        "hypothesis_blockers",
        "lane_id",
        "latest_prefill_audit_state",
        "ltf_ambiguity_coverage",
        "next_capture_priorities",
        "non_claims",
        "pending_limit_lifecycle_coverage",
        "prefill_decision_packet_coverage",
        "promotion_verdict",
        "scope_boundary",
        "seed_rows",
        "strategy_follow_join_coverage"
      ]
    },
    {
      "key_shape_fingerprint": "75dec38c52f826e32633c61ae01838223dc305dec90a0eccd946a9b9a3309cfe",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/02_hypothesis_registry/G10_SOURCE_CONTRACT_ROWS_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/02_hypothesis_registry/G10_SOURCE_CONTRACT_ROWS_2026-05-06.json",
      "shape": {
        "generated_at_utc": "str",
        "lane_id": "str",
        "promotion_verdict": "str",
        "rows": [
          {
            "access_legal_state": "str",
            "allowed_feature_role": "str",
            "cache_path": "str",
            "cost_rule": "str",
            "promotion_verdict": "str",
            "publication_asof_timestamp_rule": "str",
            "source_id": "str",
            "url_or_vendor": "str",
            "validation_safe": "bool",
            "validation_safe_blockers": [
              "str"
            ]
          }
        ],
        "schema": "str"
      },
      "size_bytes": 7509,
      "source_hash": "2c1723a05170ef96b88be077f8a24be070d71b59e0010e2530c25e642ffed4c7",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "generated_at_utc",
        "lane_id",
        "promotion_verdict",
        "rows",
        "schema"
      ]
    },
    {
      "key_shape_fingerprint": "995297871c24e61cfab4f207d19c5171ef068082feaffc18a4230fe0c1dcff0a",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/02_hypothesis_registry/G11_DATA_SOURCES_EXPANSION_HYPOTHESES_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/02_hypothesis_registry/G11_DATA_SOURCES_EXPANSION_HYPOTHESES_2026-05-06.json",
      "shape": [
        {
          "alternative": "str",
          "entry_or_filter_or_exit_role": "str",
          "hypothesis_id": "str",
          "label_class": "str",
          "mechanism_id": "str",
          "no_leak_fields": [
            "str"
          ],
          "null": "str",
          "promotion_blockers": [
            "str"
          ],
          "promotion_verdict": "str",
          "sample_floor": "str",
          "symbols": [
            "str"
          ],
          "test_method": "str",
          "timeframes": [
            "str"
          ]
        }
      ],
      "size_bytes": 9897,
      "source_hash": "b7a53d59976fc65eb41eb30bc24509db12d41f5a90e9be5bcfa4704ea2335177",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": []
    },
    {
      "key_shape_fingerprint": "87505ca404e6b80e6a652aa6c9f4b83a5a4366524fa509973f4af36853d0c020",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/02_hypothesis_registry/G11_DATA_SOURCES_EXPANSION_MECHANISMS_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/02_hypothesis_registry/G11_DATA_SOURCES_EXPANSION_MECHANISMS_2026-05-06.json",
      "shape": [
        {
          "existing_gtos_overlap": "str",
          "expected_signature": "str",
          "killed_route_check": "str",
          "known_decay_mode": "str",
          "market_behavior": "str",
          "mechanism_id": "str",
          "promotion_verdict": "str",
          "required_data": [
            "str"
          ],
          "science_domain": "str"
        }
      ],
      "size_bytes": 8213,
      "source_hash": "7faf806104bd517d565e64f536347888e19b05f8d8ce175f4172362e6f1bdb69",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": []
    },
    {
      "key_shape_fingerprint": "75dec38c52f826e32633c61ae01838223dc305dec90a0eccd946a9b9a3309cfe",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/02_hypothesis_registry/G3_GEOMETRY_SIGNAL_SOURCE_CONTRACT_ROWS_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/02_hypothesis_registry/G3_GEOMETRY_SIGNAL_SOURCE_CONTRACT_ROWS_2026-05-06.json",
      "shape": {
        "generated_at_utc": "str",
        "lane_id": "str",
        "promotion_verdict": "str",
        "rows": [
          {
            "access_legal_state": "str",
            "allowed_feature_role": "str",
            "cache_path": "str",
            "cost_rule": "str",
            "promotion_verdict": "str",
            "publication_asof_timestamp_rule": "str",
            "source_id": "str",
            "url_or_vendor": "str",
            "validation_safe": "bool",
            "validation_safe_blockers": [
              "str"
            ]
          }
        ],
        "schema": "str"
      },
      "size_bytes": 8129,
      "source_hash": "893666b4eb4f7be2b01a77887574c9ba003f32237dd0786d553b60ea00fe2a42",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "generated_at_utc",
        "lane_id",
        "promotion_verdict",
        "rows",
        "schema"
      ]
    },
    {
      "key_shape_fingerprint": "75dec38c52f826e32633c61ae01838223dc305dec90a0eccd946a9b9a3309cfe",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/02_hypothesis_registry/G5_SOURCE_CONTRACT_ROWS_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/02_hypothesis_registry/G5_SOURCE_CONTRACT_ROWS_2026-05-06.json",
      "shape": {
        "generated_at_utc": "str",
        "lane_id": "str",
        "promotion_verdict": "str",
        "rows": [
          {
            "access_legal_state": "str",
            "allowed_feature_role": "str",
            "cache_path": "str",
            "cost_rule": "str",
            "promotion_verdict": "str",
            "publication_asof_timestamp_rule": "str",
            "source_id": "str",
            "url_or_vendor": "str",
            "validation_safe": "bool",
            "validation_safe_blockers": [
              "str"
            ]
          }
        ],
        "schema": "str"
      },
      "size_bytes": 7571,
      "source_hash": "ac98388ea01f1488ebb49c869c42b8a6f5677884822b15a5184eca3475f7522a",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "generated_at_utc",
        "lane_id",
        "promotion_verdict",
        "rows",
        "schema"
      ]
    },
    {
      "key_shape_fingerprint": "75dec38c52f826e32633c61ae01838223dc305dec90a0eccd946a9b9a3309cfe",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/02_hypothesis_registry/G7_MACRO_CROSS_ASSET_SOURCE_CONTRACT_ROWS_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/02_hypothesis_registry/G7_MACRO_CROSS_ASSET_SOURCE_CONTRACT_ROWS_2026-05-06.json",
      "shape": {
        "generated_at_utc": "str",
        "lane_id": "str",
        "promotion_verdict": "str",
        "rows": [
          {
            "access_legal_state": "str",
            "allowed_feature_role": "str",
            "cache_path": "str",
            "cost_rule": "str",
            "promotion_verdict": "str",
            "publication_asof_timestamp_rule": "str",
            "source_id": "str",
            "url_or_vendor": "str",
            "validation_safe": "bool",
            "validation_safe_blockers": [
              "str"
            ]
          }
        ],
        "schema": "str"
      },
      "size_bytes": 10282,
      "source_hash": "f72623e72faf1278c2be96225f252570081143c83f7c5a42c869204aeb942933",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "generated_at_utc",
        "lane_id",
        "promotion_verdict",
        "rows",
        "schema"
      ]
    },
    {
      "key_shape_fingerprint": "75dec38c52f826e32633c61ae01838223dc305dec90a0eccd946a9b9a3309cfe",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/02_hypothesis_registry/G8_OPTIONS_VOL_SOURCE_CONTRACT_ROWS_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/02_hypothesis_registry/G8_OPTIONS_VOL_SOURCE_CONTRACT_ROWS_2026-05-06.json",
      "shape": {
        "generated_at_utc": "str",
        "lane_id": "str",
        "promotion_verdict": "str",
        "rows": [
          {
            "access_legal_state": "str",
            "allowed_feature_role": "str",
            "cache_path": "str",
            "cost_rule": "str",
            "promotion_verdict": "str",
            "publication_asof_timestamp_rule": "str",
            "source_id": "str",
            "url_or_vendor": "str",
            "validation_safe": "bool",
            "validation_safe_blockers": [
              "str"
            ]
          }
        ],
        "schema": "str"
      },
      "size_bytes": 7809,
      "source_hash": "a49ddfd34f85e49fee974a4af8b30e9b033a480fdcdb9918d146c04078ff3146",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "generated_at_utc",
        "lane_id",
        "promotion_verdict",
        "rows",
        "schema"
      ]
    },
    {
      "key_shape_fingerprint": "bd79917bc6e2ad5a90eac9e69dd26dc58fef548ec6537e7ea43287bb5d8fde65",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/02_hypothesis_registry/HYPOTHESIS_REGISTRY_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/02_hypothesis_registry/HYPOTHESIS_REGISTRY_2026-05-06.json",
      "shape": {
        "governor_reconciliation": {
          "checked_at_utc": "str",
          "governor_lane": "str",
          "head_reconciled": "str",
          "lane_blockers": {
            "G1": [
              "str"
            ],
            "G10": [
              "str"
            ],
            "G11": [
              "str"
            ],
            "G2": [
              "str"
            ],
            "G3": [
              "str"
            ],
            "G4": [
              "str"
            ],
            "G5": [
              "str"
            ],
            "G6": [
              "str"
            ],
            "G7": [
              "str"
            ],
            "G8": [
              "str"
            ],
            "G9": [
              "str"
            ]
          },
          "lane_counts": {
            "G1": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G10": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G11": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G2": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G3": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G4": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G5": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G6": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G7": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G8": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G9": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            }
          },
          "missing_lane_artifacts": [
            {
              "artifact_gap": "str",
              "blocking_master_merge": "bool",
              "lane_id": "str"
            }
          ],
          "primary_reconciliation_commit_sha": "str",
          "promotion_verdict": "str",
          "row_counts": {
            "experiment_prereg_rows_merged": "int",
            "goal_status_rows_total": "int",
            "hypothesis_rows_merged": "int",
            "mechanism_rows_merged": "int",
            "source_contract_rows_reconciled": "int"
          },
          "schema_check": {
            "duplicate_report": {
              "experiment_id_duplicates": "list",
              "hypothesis_id_duplicates": "list",
              "mechanism_id_duplicates": "list",
              "source_id_duplicates": "list"
            },
            "experiment_prereg_summary": {
              "experiment_prereg_rows": "int",
              "outcome_review_opened_false": "int",
              "outcome_review_opened_true": "int"
            },
            "hard_blocker_issue_count": "int",
            "label_class_counts_after_g0_normalization": {
              "broker_actual_r": "int",
              "context_only": "int",
              "lifecycle_no_fill": "int",
              "observation_only": "int",
              "synthetic_path_r": "int"
            },
            "no_leak_semantic_blockers": [
              "dict"
            ],
            "normalizations": [
              "dict"
            ],
            "relationship_issues": [],
            "required_field_issues": [],
            "source_contract_summary": {
              "blocked_source_rows": "list",
              "source_contract_rows": "int",
              "validation_safe_false": "int",
              "validation_safe_true": "int"
            },
            "source_reference_issues": [
              "dict"
            ]
          },
          "scope": "str",
          "wave2_merge_commit": "str"
        },
        "promotion_verdict": "str",
        "row_sources": {
          "G10-HYP-COST-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G10-HYP-J46J49-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G10-HYP-PENDING-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G10-HYP-PORTFOLIO-007": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G10-HYP-PREFILL-003": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G10-HYP-PROP-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G10-HYP-RISKBANK-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G10-HYP-XDOMAIN-008": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G6-HYP-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G6-HYP-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G6-HYP-003": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G6-HYP-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G6-HYP-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G6-HYP-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G6-HYP-007": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "H-G2-AR-DECAY-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "H-G2-EVT-TAILDEP-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "H-G2-GARCH-LIFECYCLE-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "H-G2-HMM-DWELL-003": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "H-G2-JUMP-HAWKES-007": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "H-G2-ROUGH-PATH-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "H-G2-SURVIVAL-PATH-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G11-COVERAGE-GATE-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G11-FRICTION-GATE-007": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G11-OBSERVER-EXPANSION-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G11-OPTIONS-VOL-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G11-PROVENANCE-GATE-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G11-PUBLIC-LAG-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G11-SOURCE-TRANSFER-003": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G11G4-SOURCE-GATED-ORDERFLOW-008": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G3-COH-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G3-DC-OVERSHOOT-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G3-DC-SWING-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G3-HURST-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G3-MFD-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G3-SIG-008": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G3-TDA-007": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G3-WAV-HAR-003": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G4-FILL-QUALITY-009": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G4-FUTURES-PROXY-LEADLAG-008": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G4-LBMA-AUCTION-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G4-NAS100-DEPTH-ADVERSE-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G4-NASDAQ-CROSS-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G4-OFI-DEPTH-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G4-PROFILE-VWAP-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G4-STOP-CASCADE-MOMENTUM-007": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G4-XAUUSD-FOOTPRINT-ABSORB-003": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G4G3-AUCTION-PATH-014": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G4G3-DC-DEPTH-013": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G4G6-AUCTION-EXHAUSTION-012": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G4G6-CASCADE-GENERIC-011": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G4G6-DEPTH-CONTINUATION-010": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G5-AINARR-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G5-AMH-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G5-CROWD-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G5-HERD-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G5-NEWS-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G5-PRED-003": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G5-XG4-PRED-007": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G5-XG6-CROWD-DECAY-008": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G5-XG7-MACRO-ATTN-009": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G7-BIS-CARRY-STRESS-007": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G7-COT-GOLD-KILLED-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G7-CROSSASSET-STRESS-008": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G7-DXY-SOFT-CONTEXT-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G7-FOMC-ATTN-003": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G7-FX-COT-MAPPING-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G7-GOLD-FLOW-009": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G7-LBMA-FIX-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G7-USD-REALRATE-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G7-XG11-SOURCE-FRESH-012": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G7-XG5-MACRO-ATTN-010": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G7-XG8-VOL-MACRO-011": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G8-GEX-FEEDBACK-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G8-GVZ-METALS-003": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G8-OPEX-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G8-PROXYMAP-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G8-VIX1D9D-STRESS-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G8-VRP-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "HYP-G8-VVIX-TAIL-007": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          }
        },
        "rows": [
          {
            "alternative": "str",
            "entry_or_filter_or_exit_role": "str",
            "hypothesis_id": "str",
            "label_class": "str",
            "mechanism_id": "str",
            "no_leak_fields": [
              "str"
            ],
            "null": "str",
            "promotion_blockers": [
              "str"
            ],
            "promotion_verdict": "str",
            "sample_floor": "str",
            "source_ids": [
              "str"
            ],
            "symbols": [
              "str"
            ],
            "test_method": "str",
            "timeframes": [
              "str"
            ]
          }
        ],
        "schema": "str",
        "status": "str"
      },
      "size_bytes": 207814,
      "source_hash": "a266c3b3302c24c55ab1567823d436bc14d28fbd68fc7195cea854f0ae333f42",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "governor_reconciliation",
        "promotion_verdict",
        "row_sources",
        "rows",
        "schema",
        "status"
      ]
    },
    {
      "key_shape_fingerprint": "899181f2965afda216f2dca72679f373f2898efd87e310b4ec185cb05275ebbf",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/02_hypothesis_registry/MECHANISM_REGISTRY_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/02_hypothesis_registry/MECHANISM_REGISTRY_2026-05-06.json",
      "shape": {
        "governor_reconciliation": {
          "checked_at_utc": "str",
          "governor_lane": "str",
          "head_reconciled": "str",
          "lane_blockers": {
            "G1": [
              "str"
            ],
            "G10": [
              "str"
            ],
            "G11": [
              "str"
            ],
            "G2": [
              "str"
            ],
            "G3": [
              "str"
            ],
            "G4": [
              "str"
            ],
            "G5": [
              "str"
            ],
            "G6": [
              "str"
            ],
            "G7": [
              "str"
            ],
            "G8": [
              "str"
            ],
            "G9": [
              "str"
            ]
          },
          "lane_counts": {
            "G1": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G10": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G11": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G2": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G3": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G4": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G5": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G6": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G7": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G8": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G9": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            }
          },
          "missing_lane_artifacts": [
            {
              "artifact_gap": "str",
              "blocking_master_merge": "bool",
              "lane_id": "str"
            }
          ],
          "primary_reconciliation_commit_sha": "str",
          "promotion_verdict": "str",
          "row_counts": {
            "experiment_prereg_rows_merged": "int",
            "goal_status_rows_total": "int",
            "hypothesis_rows_merged": "int",
            "mechanism_rows_merged": "int",
            "source_contract_rows_reconciled": "int"
          },
          "schema_check": {
            "duplicate_report": {
              "experiment_id_duplicates": "list",
              "hypothesis_id_duplicates": "list",
              "mechanism_id_duplicates": "list",
              "source_id_duplicates": "list"
            },
            "experiment_prereg_summary": {
              "experiment_prereg_rows": "int",
              "outcome_review_opened_false": "int",
              "outcome_review_opened_true": "int"
            },
            "hard_blocker_issue_count": "int",
            "label_class_counts_after_g0_normalization": {
              "broker_actual_r": "int",
              "context_only": "int",
              "lifecycle_no_fill": "int",
              "observation_only": "int",
              "synthetic_path_r": "int"
            },
            "no_leak_semantic_blockers": [
              "dict"
            ],
            "normalizations": [
              "dict"
            ],
            "relationship_issues": [],
            "required_field_issues": [],
            "source_contract_summary": {
              "blocked_source_rows": "list",
              "source_contract_rows": "int",
              "validation_safe_false": "int",
              "validation_safe_true": "int"
            },
            "source_reference_issues": [
              "dict"
            ]
          },
          "scope": "str",
          "wave2_merge_commit": "str"
        },
        "promotion_verdict": "str",
        "row_sources": {
          "G10-MECH-COST-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G10-MECH-J46J49-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G10-MECH-PENDING-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G10-MECH-PORTFOLIO-007": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G10-MECH-PREFILL-003": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G10-MECH-PROP-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G10-MECH-RISKBANK-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G5-MECH-AINARR-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G5-MECH-AMH-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G5-MECH-CROWD-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G5-MECH-HERD-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G5-MECH-NEWSATTN-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G5-MECH-PRED-003": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G7-MECH-BIS-FX-CARRY-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G7-MECH-COT-POSITION-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G7-MECH-CROSSASSET-STRESS-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G7-MECH-FOMC-ATTENTION-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G7-MECH-GOLD-FLOW-007": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G7-MECH-LBMA-FIX-003": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G7-MECH-USD-REALRATE-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G1-VAL-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G1-VAL-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G1-VAL-003": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G1-VAL-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G1-VAL-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G1-VAL-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G11-COVERAGE-BIAS-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G11-FRICTION-007": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G11-OBSERVER-EXPANSION-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G11-OPTIONS-VOL-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G11-PROVENANCE-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G11-PUBLIC-LAG-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G11-SOURCE-TRANSFER-003": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G2-AR-DECAY-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G2-EVT-TAILDEP-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G2-GARCH-LIFECYCLE-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G2-HMM-DWELL-003": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G2-JUMP-HAWKES-007": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G2-ROUGH-PATH-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G2-SURVIVAL-PATH-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G3-COH-003": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G3-DC-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G3-HUR-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G3-MFD-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G3-SIG-007": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G3-TDA-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G3-WAV-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G4-AUCTION-IMBALANCE-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G4-FILL-QUALITY-008": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G4-FOOTPRINT-ABSORB-003": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G4-FUTURES-PROXY-007": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G4-OFI-DEPTH-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G4-PROFILE-VWAP-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G4-QUEUE-ADVERSE-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G4-STOP-CASCADE-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G6-GOLD-007": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G6-MOM-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G6-MOM-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G6-MOM-003": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G6-MR-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G6-MR-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G6-STATARB-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G8-GEX-FEEDBACK-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G8-METALS-IV-003": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G8-OPEX-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G8-PROXYMAP-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G8-SHORTVOL-STRESS-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G8-VOL-OF-VOL-007": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G8-VRP-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G9-AIML-COMPLEMENT-003": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G9-DEBATE-DISAGREE-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G9-K55-TARGET-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G9-LLM-SELFAUDIT-008": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G9-NOLEAK-FEATURE-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G9-OFFLINE-RL-007": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G9-REFLEXION-LABEL-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "SCI-G9-TOOL-GROUND-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          }
        },
        "rows": [
          {
            "existing_gtos_overlap": "str",
            "expected_signature": "str",
            "killed_route_check": "str",
            "known_decay_mode": "str",
            "market_behavior": "str",
            "mechanism_id": "str",
            "promotion_verdict": "str",
            "required_data": [
              "str"
            ],
            "science_domain": "str",
            "source_ids": [
              "str"
            ]
          }
        ],
        "schema": "str",
        "status": "str"
      },
      "size_bytes": 146416,
      "source_hash": "4b9571e1086e316f09d9ce59167baf51f977f1878ce17165485961e3ef0705b0",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "governor_reconciliation",
        "promotion_verdict",
        "row_sources",
        "rows",
        "schema",
        "status"
      ]
    },
    {
      "key_shape_fingerprint": "b50e763b1ed6320c9267b95dad668e31ab8e7657667f53f72ad3d88de7ca4102",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/03_experiment_specs/EXPERIMENT_PREREGISTRY_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/03_experiment_specs/EXPERIMENT_PREREGISTRY_2026-05-06.json",
      "shape": {
        "cd2_reconciliation": {
          "accepted_master_prereg_rows": [
            {
              "assignment_id": "str",
              "experiment_id": "str",
              "hypothesis_id": "str",
              "lane_id": "str",
              "promotion_verdict": "str",
              "source_file": "str"
            }
          ],
          "ai_calls": "int",
          "blocked_cd2_master_actions": [
            {
              "artifacts": "list",
              "assignment_id": "str",
              "lane": "str",
              "master_action": "str",
              "promotion_verdict": "str",
              "reason": "str"
            }
          ],
          "canary_calls": "int",
          "cd2_artifacts": [
            {
              "artifacts": "list",
              "assignment_id": "str",
              "commit": "str",
              "g12_focus": "str",
              "lane": "str",
              "master_action": "str",
              "reason": "str",
              "title": "str"
            }
          ],
          "cd2_merge_commit": "str",
          "checked_at_utc": "str",
          "external_cash_spend_usd": "float",
          "g12_launch_status": "str",
          "head_reconciled": "str",
          "lane_id": "str",
          "live_behavior_changed": "bool",
          "master_row_delta": {
            "experiment_prereg_rows_added": "int",
            "hypothesis_rows_added": "int",
            "mechanism_rows_added": "int",
            "source_contract_rows_added": "int",
            "survivor_backlog_rows_added": "int"
          },
          "mt5_calls": "int",
          "order_calls": "int",
          "paid_data_calls": "int",
          "promotion_verdict": "str",
          "public_web_fetches_by_g0": "int",
          "source_policy": {
            "source_contract_rows_added": "int",
            "source_registry_action": "str",
            "validation_safe_true_allowed": "bool",
            "validation_safe_true_rows_after_reconciliation": "int"
          },
          "status": "str",
          "wave2_primary_reconciliation_commit": "str",
          "wave2_status_commit": "str"
        },
        "governor_reconciliation": {
          "checked_at_utc": "str",
          "governor_lane": "str",
          "head_reconciled": "str",
          "lane_blockers": {
            "G1": [
              "str"
            ],
            "G10": [
              "str"
            ],
            "G11": [
              "str"
            ],
            "G2": [
              "str"
            ],
            "G3": [
              "str"
            ],
            "G4": [
              "str"
            ],
            "G5": [
              "str"
            ],
            "G6": [
              "str"
            ],
            "G7": [
              "str"
            ],
            "G8": [
              "str"
            ],
            "G9": [
              "str"
            ]
          },
          "lane_counts": {
            "G1": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G10": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G11": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G2": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G3": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G4": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G5": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G6": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G7": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G8": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G9": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            }
          },
          "missing_lane_artifacts": [
            {
              "artifact_gap": "str",
              "blocking_master_merge": "bool",
              "lane_id": "str"
            }
          ],
          "primary_reconciliation_commit_sha": "str",
          "promotion_verdict": "str",
          "row_counts": {
            "experiment_prereg_rows_merged": "int",
            "goal_status_rows_total": "int",
            "hypothesis_rows_merged": "int",
            "mechanism_rows_merged": "int",
            "source_contract_rows_reconciled": "int"
          },
          "schema_check": {
            "duplicate_report": {
              "experiment_id_duplicates": "list",
              "hypothesis_id_duplicates": "list",
              "mechanism_id_duplicates": "list",
              "source_id_duplicates": "list"
            },
            "experiment_prereg_summary": {
              "experiment_prereg_rows": "int",
              "outcome_review_opened_false": "int",
              "outcome_review_opened_true": "int"
            },
            "hard_blocker_issue_count": "int",
            "label_class_counts_after_g0_normalization": {
              "broker_actual_r": "int",
              "context_only": "int",
              "lifecycle_no_fill": "int",
              "observation_only": "int",
              "synthetic_path_r": "int"
            },
            "no_leak_semantic_blockers": [
              "dict"
            ],
            "normalizations": [
              "dict"
            ],
            "relationship_issues": [],
            "required_field_issues": [],
            "source_contract_summary": {
              "blocked_source_rows": "list",
              "source_contract_rows": "int",
              "validation_safe_false": "int",
              "validation_safe_true": "int"
            },
            "source_reference_issues": [
              "dict"
            ]
          },
          "scope": "str",
          "wave2_merge_commit": "str"
        },
        "post_g12_closeout": {
          "accepted_cd2_preregs_outcome_closed": [
            "str"
          ],
          "checked_at_utc": "str",
          "head_read": "str",
          "outcome_review_opened_true": "int",
          "promotion_verdict": "str",
          "survivor_backlog_rows_added": "int"
        },
        "promotion_verdict": "str",
        "row_sources": {
          "EXP-G11-COVERAGE-GATE-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G11-FRICTION-GATE-007": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G11-OBSERVER-EXPANSION-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G11-OPTIONS-VOL-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G11-PROVENANCE-GATE-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G11-PUBLIC-LAG-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G11-SOURCE-TRANSFER-003": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G11G4-SOURCE-GATED-ORDERFLOW-008": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G2-AR-DECAY-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G2-EVT-TAILDEP-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G2-GARCH-LIFECYCLE-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G2-HMM-DWELL-003": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G2-JUMP-HAWKES-007": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G2-ROUGH-PATH-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G2-SURVIVAL-PATH-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G3-COH-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G3-DC-OVERSHOOT-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G3-DC-SWING-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G3-HURST-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G3-MFD-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G3-SIG-008": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G3-TDA-007": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G3-WAV-HAR-003": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G4-AUCTION-CONTEXT-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G4-FILL-QUALITY-008": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G4-NAS100-DEPTH-ADVERSE-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G4-OFI-DEPTH-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G4-PROFILE-VWAP-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G4-PROXY-LEADLAG-007": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G4-STOP-CASCADE-MOMENTUM-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G4-XAUUSD-FOOTPRINT-ABSORB-003": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G4G3-AUCTION-PATH-013": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G4G3-DC-DEPTH-012": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G4G6-AUCTION-EXHAUSTION-011": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G4G6-CASCADE-GENERIC-010": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G4G6-DEPTH-CONTINUATION-009": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G5-AINARR-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G5-AMH-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G5-CROWD-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G5-HERD-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G5-NEWS-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G5-PRED-003": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G5-XG4-PRED-007": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G5-XG6-CROWD-DECAY-008": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G5-XG7-MACRO-ATTN-009": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G7-BIS-CARRY-007": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G7-COT-GOLD-KILLED-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G7-CROSSASSET-STRESS-008": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G7-DXY-SOFT-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G7-FOMC-ATTN-003": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G7-FX-COT-MAPPING-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G7-GOLD-FLOW-009": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G7-LBMA-FIX-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G7-USD-REALRATE-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G7-XG11-SOURCE-FRESH-012": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G7-XG5-MACRO-ATTN-010": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G7-XG8-VOL-MACRO-011": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G8-CD2-02-SHORTVOL-LIFECYCLE-001": {
            "lane_id": "str",
            "promotion_verdict": "str",
            "reconciled_by": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G8-GEX-FEEDBACK-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G8-GVZ-METALS-003": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G8-OPEX-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G8-PROXYMAP-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G8-VIX1D9D-STRESS-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G8-VRP-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G8-VVIX-TAIL-007": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G9-AIML-COMPARATOR-003": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G9-CD2-03-OFFLINE-RL-RISKBANK-001": {
            "lane_id": "str",
            "promotion_verdict": "str",
            "reconciled_by": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G9-DEBATE-007": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G9-K55-ARTIFACT-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G9-K55-NOLEAK-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G9-K55-SOURCE-006": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G9-LLM-SELFAUDIT-010": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G9-OFFLINE-RL-009": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G9-REFLEXION-008": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G9-TOOL-NUMERIC-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "EXP-G9-TOOL-ORDERFLOW-005": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G10-EXP-COST-002": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G10-EXP-J46J49-004": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G10-EXP-PENDING-001": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          },
          "G10-EXP-PORTFOLIO-007": {
            "lane_id": "str",
            "source_files": [
              "str"
            ]
          }
        },
        "rows": [
          {
            "cohort": "str",
            "cost_slippage_assumptions": "str",
            "dsr_pbo_effective_n_policy": "str",
            "duplicate_policy": "str",
            "exclusions": [
              "str"
            ],
            "experiment_id": "str",
            "frozen_at_utc": "str",
            "hypothesis_id": "str",
            "label_separation_policy": "str",
            "metric": "str",
            "outcome_review_opened": "bool",
            "promotion_verdict": "str",
            "reproducibility_key": "str"
          }
        ],
        "schema": "str",
        "status": "str"
      },
      "size_bytes": 209164,
      "source_hash": "487852fadfb9622dc60df032471078649e5864b59a69a048b056089fd8a2acd6",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "cd2_reconciliation",
        "governor_reconciliation",
        "post_g12_closeout",
        "promotion_verdict",
        "row_sources",
        "rows",
        "schema",
        "status"
      ]
    },
    {
      "key_shape_fingerprint": "fc50716ac003d002fd1a19b5de2633f46c35aa0efeb144e91b831b5cb028a0db",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/03_experiment_specs/G11_DATA_SOURCES_EXPANSION_EXPERIMENT_PREREGS_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/03_experiment_specs/G11_DATA_SOURCES_EXPANSION_EXPERIMENT_PREREGS_2026-05-06.json",
      "shape": [
        {
          "cohort": "str",
          "cost_slippage_assumptions": "str",
          "dsr_pbo_effective_n_policy": "str",
          "duplicate_policy": "str",
          "exclusions": [
            "str"
          ],
          "experiment_id": "str",
          "frozen_at_utc": "str",
          "hypothesis_id": "str",
          "label_separation_policy": "str",
          "metric": "str",
          "outcome_review_opened": "bool",
          "promotion_verdict": "str",
          "reproducibility_key": "str"
        }
      ],
      "size_bytes": 8944,
      "source_hash": "752cdc5a25581fe3e3ea7ed7e0bad68ba7ee747be3e52e0e555200c6d34c5b22",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": []
    },
    {
      "key_shape_fingerprint": "28197bad3b298301c4a73f2b3fb4231c8d808b4036a732a732a2fd254cd123e3",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/05_synthesis/G0_COMPLETION_AUDIT_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/05_synthesis/G0_COMPLETION_AUDIT_2026-05-06.json",
      "shape": {
        "audit_timestamp_utc": "str",
        "blockers": [
          "str"
        ],
        "can_mark_g0_cd2_complete": "bool",
        "cd2_merge_commit": "str",
        "head_reconciled": "str",
        "lane_id": "str",
        "objective_restatement": "str",
        "promotion_verdict": "str",
        "prompt_to_artifact_checklist": [
          {
            "evidence": "str",
            "requirement": "str",
            "status": "str"
          }
        ],
        "status": "str",
        "verification_results": [
          "str"
        ]
      },
      "size_bytes": 4583,
      "source_hash": "a5facef6dfd3f9dbfc6a892a7be33d16141f9fcbb8934ebc68a5ca0df92d7ef8",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "audit_timestamp_utc",
        "blockers",
        "can_mark_g0_cd2_complete",
        "cd2_merge_commit",
        "head_reconciled",
        "lane_id",
        "objective_restatement",
        "promotion_verdict",
        "prompt_to_artifact_checklist",
        "status",
        "verification_results"
      ]
    },
    {
      "key_shape_fingerprint": "13d13411458af2783cee0b15f8013dcaa7bd94394fdab4d49dd2fe247ffb64b7",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/05_synthesis/G0_POST_G12_COMPLETION_AUDIT_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/05_synthesis/G0_POST_G12_COMPLETION_AUDIT_2026-05-06.json",
      "shape": {
        "ai_calls": "int",
        "audit_timestamp_utc": "str",
        "can_mark_g0_post_g12_closeout_complete": "bool",
        "canary_calls": "int",
        "forbidden_surface_changes_made": "bool",
        "head_read": "str",
        "lane_id": "str",
        "live_behavior_changed": "bool",
        "mt5_calls": "int",
        "objective_restatement": "str",
        "order_calls": "int",
        "paid_data_calls": "int",
        "promotion_verdict": "str",
        "prompt_to_artifact_checklist": [
          {
            "evidence": "str",
            "requirement": "str",
            "status": "str"
          }
        ],
        "public_web_fetches": "int",
        "registry_invariants": {
          "accepted_cd2_preregs": "int",
          "experiment_prereg_rows": "int",
          "hypothesis_rows": "int",
          "mechanism_rows": "int",
          "no_leak_semantic_blockers": "int",
          "outcome_review_opened_true_preregs": "int",
          "source_contract_rows": "int",
          "source_reference_issues": "int",
          "survivor_backlog_rows": "int",
          "validation_safe_true_sources": "int"
        },
        "remote_pushes": "int",
        "schema": "str",
        "status": "str",
        "verification_results": [
          "str"
        ]
      },
      "size_bytes": 5060,
      "source_hash": "5815daa627fc791c7d7e064f5bb0a8f2c3cf1b6805a44a255032965015dad405",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "ai_calls",
        "audit_timestamp_utc",
        "can_mark_g0_post_g12_closeout_complete",
        "canary_calls",
        "forbidden_surface_changes_made",
        "head_read",
        "lane_id",
        "live_behavior_changed",
        "mt5_calls",
        "objective_restatement",
        "order_calls",
        "paid_data_calls",
        "promotion_verdict",
        "prompt_to_artifact_checklist",
        "public_web_fetches",
        "registry_invariants",
        "remote_pushes",
        "schema",
        "status",
        "verification_results"
      ]
    },
    {
      "key_shape_fingerprint": "5a00c94d19eae539d77aefcb235afbedee9a856c0aeea6ee1521c8d5f30e9b5d",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/05_synthesis/G0_POST_G12_EXPERIMENT_BACKLOG_READINESS_LEDGER_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/05_synthesis/G0_POST_G12_EXPERIMENT_BACKLOG_READINESS_LEDGER_2026-05-06.json",
      "shape": {
        "backlog_readiness": {
          "cleanup_control_backlog_rows": "int",
          "outcome_opening_backlog_rows": "int",
          "source_validation_backlog_rows": "int",
          "survivor_backlog_rows": "int"
        },
        "experiment_readiness": [
          {
            "assignment_id": "str",
            "current_status": "str",
            "next_action": "str",
            "outcome_review_opened": "bool",
            "readiness_class": "str",
            "row_or_artifact": "str",
            "survivor_backlog_candidate": "bool"
          }
        ],
        "lane_id": "str",
        "promotion_verdict": "str",
        "registry_readiness_summary": {
          "accepted_cd2_preregs": "int",
          "blocked_or_status_only_cd2_assignments": "int",
          "master_experiment_preregs": "int",
          "outcome_review_opened_true": "int",
          "survivor_backlog_rows": "int",
          "validation_safe_true_sources": "int"
        },
        "schema": "str",
        "status": "str"
      },
      "size_bytes": 4675,
      "source_hash": "712bb276ea42287874cac22768282a8459c752926304920123145f079266509f",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "backlog_readiness",
        "experiment_readiness",
        "lane_id",
        "promotion_verdict",
        "registry_readiness_summary",
        "schema",
        "status"
      ]
    },
    {
      "key_shape_fingerprint": "ad074f959aca63cec414fe1bdcfc5dea3444148dc4854fa0cd4ea24e5e821b41",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/05_synthesis/G0_POST_G12_SOURCE_NO_LEAK_CLEANUP_ASSIGNMENTS_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/05_synthesis/G0_POST_G12_SOURCE_NO_LEAK_CLEANUP_ASSIGNMENTS_2026-05-06.json",
      "shape": {
        "cleanup_mode": "str",
        "guardrails": {
          "live_behavior_change_allowed": "bool",
          "outcome_review_opening_allowed": "bool",
          "raw_orderflow_predictive_feature_add_allowed": "bool",
          "source_validation_flip_allowed": "bool",
          "survivor_backlog_add_allowed": "bool"
        },
        "lane_id": "str",
        "no_leak_cleanup_rows": [
          {
            "current_issue": "str",
            "future_assignment": "str",
            "row_id": "str"
          }
        ],
        "promotion_verdict": "str",
        "schema": "str",
        "source_reference_cleanup_rows": [
          {
            "current_issue": "str",
            "future_assignment": "str",
            "row_id": "str"
          }
        ],
        "status": "str"
      },
      "size_bytes": 4290,
      "source_hash": "e52dfefe88bc03c3068b66a9f05093e24d189ae341efdc4135822fa77dece3c7",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "cleanup_mode",
        "guardrails",
        "lane_id",
        "no_leak_cleanup_rows",
        "promotion_verdict",
        "schema",
        "source_reference_cleanup_rows",
        "status"
      ]
    },
    {
      "key_shape_fingerprint": "395f0273ec7c799b62ca9ab603ff3578756998433cf7c5207e2ef6b30009243b",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/05_synthesis/G4_CD2_04_K55_FEATURE_PROVENANCE_CONTRACT_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/05_synthesis/G4_CD2_04_K55_FEATURE_PROVENANCE_CONTRACT_2026-05-06.json",
      "shape": {
        "allowed_feature_prefixes": [
          "str"
        ],
        "allowed_feature_roles": [
          "str"
        ],
        "assignment_id": "str",
        "controlling_inputs": [
          "str"
        ],
        "forbidden_feature_fields_or_prefixes": [
          "str"
        ],
        "generated_at_utc": "str",
        "head_read": "str",
        "k55_version_gate": {
          "feature_bundle_version": "str",
          "inference_version": "str",
          "numeric_ready_source_bundles": "int",
          "stale_k54_reuse_allowed": "bool",
          "target_version": "str"
        },
        "lane_owner": "str",
        "metadata_only_fields": [
          "str"
        ],
        "non_claims": [
          "str"
        ],
        "promotion_verdict": "str",
        "safety_counters": {
          "ai_calls": "int",
          "canary_calls": "int",
          "mt5_calls": "int",
          "order_calls": "int",
          "paid_data_calls": "int",
          "remote_pushes": "int"
        },
        "schema_version": "str",
        "scope": "str",
        "seed_hypotheses": [
          {
            "cd2_04_role": "str",
            "hypothesis_id": "str"
          }
        ],
        "source_contract_state": {
          "all_sources_remain_validation_safe_false": "bool",
          "source_contract_rows_read": "int",
          "validation_safe_true_rows": "int"
        },
        "status": "str",
        "tool_grounding_boundary": {
          "allowed_tool_output_role": "str",
          "budget_or_approval_blocked": "bool",
          "decision_influence_allowed": "bool",
          "tool_grounding_activation_authorized": "bool"
        }
      },
      "size_bytes": 4541,
      "source_hash": "c00f2fec21f809cb7eaeb3f1ee96f531d37a7506043fd4c21b55fa9a6a1d3f0b",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "allowed_feature_prefixes",
        "allowed_feature_roles",
        "assignment_id",
        "controlling_inputs",
        "forbidden_feature_fields_or_prefixes",
        "generated_at_utc",
        "head_read",
        "k55_version_gate",
        "lane_owner",
        "metadata_only_fields",
        "non_claims",
        "promotion_verdict",
        "safety_counters",
        "schema_version",
        "scope",
        "seed_hypotheses",
        "source_contract_state",
        "status",
        "tool_grounding_boundary"
      ]
    },
    {
      "key_shape_fingerprint": "6481817b27d4162a3730996b57465fd394e66261adb3e859f2d03a167abdba45",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/05_synthesis/G4_CD2_04_SOURCE_STATUS_JOIN_MAP_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/05_synthesis/G4_CD2_04_SOURCE_STATUS_JOIN_MAP_2026-05-06.json",
      "shape": {
        "assignment_id": "str",
        "generated_at_utc": "str",
        "head_read": "str",
        "join_boundary": {
          "asof_rule": "str",
          "feature_output_boundary": "str",
          "metadata_goes_to_source_refs": [
            "str"
          ],
          "primary_join_keys": [
            "str"
          ]
        },
        "lane_owner": "str",
        "non_claims": [
          "str"
        ],
        "promotion_verdict": "str",
        "required_blocker_checks": {
          "databento_sierra_legality_and_timestamp_provenance": "str",
          "feature_bundle_target_version_match": "str",
          "no_source_marked_validation_safe_true": "str",
          "tool_grounding_approval_budget_blocked": "str"
        },
        "safety_counters": {
          "ai_calls": "int",
          "canary_calls": "int",
          "mt5_calls": "int",
          "order_calls": "int",
          "paid_data_calls": "int",
          "remote_pushes": "int"
        },
        "schema_version": "str",
        "scope": "str",
        "seed_hypothesis_coverage": {
          "HYP-G11G4-SOURCE-GATED-ORDERFLOW-008": "str",
          "HYP-G4-OFI-DEPTH-001": "str",
          "HYP-G9G4-K55-SOURCE-006": "str",
          "HYP-G9G4-TOOL-ORDERFLOW-005": "str"
        },
        "source_status_inputs": [
          {
            "allowed_k55_flags": [
              "str"
            ],
            "input_path": "str",
            "quarantined_fields": [
              "str"
            ],
            "source_role": "str"
          }
        ],
        "status": "str",
        "status_encoding_examples": [
          {
            "flag": "str",
            "source_status": "str",
            "value": "int"
          }
        ]
      },
      "size_bytes": 9658,
      "source_hash": "203d131896c9d7495bcd88f36df6f04e5cf27b2090d6eaa4ffb0ac9565afabe3",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "assignment_id",
        "generated_at_utc",
        "head_read",
        "join_boundary",
        "lane_owner",
        "non_claims",
        "promotion_verdict",
        "required_blocker_checks",
        "safety_counters",
        "schema_version",
        "scope",
        "seed_hypothesis_coverage",
        "source_status_inputs",
        "status",
        "status_encoding_examples"
      ]
    },
    {
      "key_shape_fingerprint": "6e3f157851fc25e613b51f5aa9cc0c858b87148a5abe6de59ff491f527f7be56",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/05_synthesis/G4_MICROSTRUCTURE_AUCTION_COMPLETION_AUDIT_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/05_synthesis/G4_MICROSTRUCTURE_AUCTION_COMPLETION_AUDIT_2026-05-06.json",
      "shape": {
        "artifact_counts": {
          "experiment_prereg_rows": "int",
          "goal_status_rows": "int",
          "hypothesis_rows": "int",
          "mechanism_rows": "int",
          "source_contract_rows": "int"
        },
        "blockers": [
          "str"
        ],
        "checks": [
          "str"
        ],
        "domain": "str",
        "forbidden_surfaces_touched": "bool",
        "lane_id": "str",
        "neighbor_pass": {
          "g11_outputs_read": "bool",
          "g11_state": "str",
          "g3_outputs_read": "bool",
          "g4g3_cross_domain_hypotheses_added": "int",
          "g4g6_cross_domain_hypotheses_added": "int",
          "g6_outputs_read": "bool"
        },
        "new_cash_spend_usd": "int",
        "objective": "str",
        "outcome_review_opened": "bool",
        "primary_commit": "str",
        "promotion_verdict": "str",
        "status": "str",
        "validation_safe_sources": "int"
      },
      "size_bytes": 1643,
      "source_hash": "1b0815a7b990fb4e4c015142ddf9203115747627b16c0867021935683137959f",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "artifact_counts",
        "blockers",
        "checks",
        "domain",
        "forbidden_surfaces_touched",
        "lane_id",
        "neighbor_pass",
        "new_cash_spend_usd",
        "objective",
        "outcome_review_opened",
        "primary_commit",
        "promotion_verdict",
        "status",
        "validation_safe_sources"
      ]
    },
    {
      "key_shape_fingerprint": "31c21e5582418d14b0307d38f3aa5cbd83fd89abb3b994c4c3ddcca0d357163f",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/05_synthesis/G5_CD2_05_ATTENTION_BLOCKER_LEDGER_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/05_synthesis/G5_CD2_05_ATTENTION_BLOCKER_LEDGER_2026-05-06.json",
      "shape": {
        "artifact_id": "str",
        "assignment_id": "str",
        "blockers": [
          {
            "applies_to_rows": [
              "str"
            ],
            "blocker_id": "str",
            "evidence": "str",
            "gate": "str",
            "promotion_verdict": "str",
            "required_resolution": "str",
            "status": "str",
            "title": "str"
          }
        ],
        "controlling_inputs": [
          "str"
        ],
        "current_local_evidence": {
          "fed_fomc_cache": {
            "path": "str",
            "present": "bool",
            "sha256": "str"
          },
          "head_read": "str",
          "local_news_calendar": {
            "configured_path": "str",
            "configured_path_present": "bool",
            "event_count": "int",
            "sha256": "str",
            "source_contract_path_present": "bool",
            "source_contract_path_seen": "str",
            "updated_at": "str",
            "week_of": "str"
          },
          "source_contract_state": {
            "SRC-G5-NEWS-CALENDAR-LOCAL-001": {
              "blocker_summary": "str",
              "validation_safe": "bool"
            },
            "SRC-G7-FED-FOMC-001": {
              "blocker_summary": "str",
              "validation_safe": "bool"
            },
            "SRC-G7-LOCAL-GTOS-MACRO-001": {
              "blocker_summary": "str",
              "validation_safe": "bool"
            }
          }
        },
        "dedupe_resolution": {
          "canonical_future_hypothesis_proposal": "str",
          "canonical_future_prereg_proposal": "str",
          "duplicate_interaction_rows_to_consolidate_later": [
            "str"
          ],
          "label_class": "str",
          "live_news_filter_changes_made": "bool",
          "master_registry_edits_made": "bool",
          "outcome_review_opened": "bool",
          "parent_source_or_cohort_rows_to_keep": [
            "str"
          ],
          "registry_edits_made": "bool"
        },
        "forbidden_changes_confirmed_by_scope": [
          "str"
        ],
        "generated_at_utc": "str",
        "owner_lane": "str",
        "promotion_verdict": "str",
        "required_next_artifacts_before_outcome_review": [
          "str"
        ],
        "seed_rows": [
          "str"
        ],
        "status": "str"
      },
      "size_bytes": 11147,
      "source_hash": "b81d8f21207f35138f5f789397806b45b9090306621221c9a89bc096ab555f70",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "artifact_id",
        "assignment_id",
        "blockers",
        "controlling_inputs",
        "current_local_evidence",
        "dedupe_resolution",
        "forbidden_changes_confirmed_by_scope",
        "generated_at_utc",
        "owner_lane",
        "promotion_verdict",
        "required_next_artifacts_before_outcome_review",
        "seed_rows",
        "status"
      ]
    },
    {
      "key_shape_fingerprint": "0de494947a0437a5ee1f9c22afc328d216f27d02c1948b262c39c3b9c89b5416",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/05_synthesis/G9_AI_ML_SYSTEMS_COMPLETION_AUDIT_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/05_synthesis/G9_AI_ML_SYSTEMS_COMPLETION_AUDIT_2026-05-06.json",
      "shape": {
        "artifact_counts": {
          "experiment_preregs": "int",
          "hypotheses": "int",
          "mechanisms": "int",
          "source_contracts": "int"
        },
        "checks": [
          "str"
        ],
        "created_at_utc": "str",
        "lane_id": "str",
        "objective_restated": "str",
        "promotion_verdict": "str",
        "schema": "str",
        "status": "str"
      },
      "size_bytes": 944,
      "source_hash": "7eee07e7df30d5f0cc655eb7b654984e7c78cfdf1c39d45ae5b9556ce9db5f2c",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "artifact_counts",
        "checks",
        "created_at_utc",
        "lane_id",
        "objective_restated",
        "promotion_verdict",
        "schema",
        "status"
      ]
    },
    {
      "key_shape_fingerprint": "d1f4c4e094a39a3b89c8b376232e065e38b02ac0e896bf9b3ede141fcd12d171",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/05_synthesis/G9_CD2_03_OFFLINE_RL_REWARD_CONTRACT_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/05_synthesis/G9_CD2_03_OFFLINE_RL_REWARD_CONTRACT_2026-05-06.json",
      "shape": {
        "action_space": [
          {
            "action_id": "str",
            "description": "str",
            "live_effect": "bool"
          }
        ],
        "allowed_state_fields": [
          "str"
        ],
        "artifact_id": "str",
        "assignment_id": "str",
        "cd2_03_blocker_checks": {
          "broker_actual_r_vs_synthetic_path_r_separation": "str",
          "dsr_pbo_effective_n_policy": "str",
          "duplicate_lifecycle_controls": "str",
          "no_live_sizing_or_execution_change": "str",
          "risk_bank_invariant": "str"
        },
        "comparison_baselines": [
          "str"
        ],
        "controlling_inputs": [
          "str"
        ],
        "episode_unit": {
          "child_rows_not_independent": [
            "str"
          ],
          "episode_id_components": [
            "str"
          ],
          "independent_unit": "str"
        },
        "forbidden_state_fields": [
          "str"
        ],
        "generated_at_utc": "str",
        "lane_id": "str",
        "non_authorized_surfaces": [
          "str"
        ],
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "reward_function": {
          "broker_actual_r_policy": "str",
          "cost_policy": "str",
          "formula": "str",
          "lifecycle_no_fill_policy": "str",
          "primary_label_class": "str",
          "same_bar_policy": "str",
          "unfilled_reentry_policy": "str"
        },
        "risk_bank_invariant": {
          "admissibility_rule": "str",
          "contract_failure_policy": "str",
          "formula": "str",
          "missing_ledger_policy": "str"
        },
        "seed_rows": [
          "str"
        ],
        "status": "str"
      },
      "size_bytes": 5855,
      "source_hash": "f91d5b9e1b070e4ba74634380292cce8039cda5f5fdeea5b56fc279214fcfb25",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "action_space",
        "allowed_state_fields",
        "artifact_id",
        "assignment_id",
        "cd2_03_blocker_checks",
        "comparison_baselines",
        "controlling_inputs",
        "episode_unit",
        "forbidden_state_fields",
        "generated_at_utc",
        "lane_id",
        "non_authorized_surfaces",
        "outcome_review_opened",
        "promotion_verdict",
        "reward_function",
        "risk_bank_invariant",
        "seed_rows",
        "status"
      ]
    },
    {
      "key_shape_fingerprint": "f8f5511bca6a29aa4cd9fadb4ac543f18e6424f973c0ccea724b4ff6d131b55b",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/05_synthesis/SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/05_synthesis/SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.json",
      "shape": {
        "blocker_summary": {
          "cd2_reconciliation_blockers": [
            {
              "artifacts": "list",
              "assignment_id": "str",
              "lane": "str",
              "master_action": "str",
              "promotion_verdict": "str",
              "reason": "str"
            }
          ],
          "cd2_registered_preregs": [
            {
              "assignment_id": "str",
              "experiment_id": "str",
              "hypothesis_id": "str",
              "lane_id": "str",
              "promotion_verdict": "str",
              "source_file": "str"
            }
          ],
          "duplicate_id_blockers": {
            "experiment_id_duplicates": [],
            "hypothesis_id_duplicates": [],
            "mechanism_id_duplicates": [],
            "source_id_duplicates": []
          },
          "missing_lane_artifacts": [
            {
              "artifact_gap": "str",
              "blocking_master_merge": "bool",
              "lane_id": "str"
            }
          ],
          "no_leak_semantic_blockers": [
            {
              "fields": "list",
              "hypothesis_id": "str",
              "issue": "str",
              "reason": "str"
            }
          ],
          "prereg_blockers": {
            "experiment_prereg_rows": "int",
            "outcome_review_opened_false": "int",
            "outcome_review_opened_true": "int"
          },
          "promotion_blocker": "str",
          "schema_normalization_blockers": [
            {
              "field": "str",
              "hypothesis_id": "str",
              "lane_id": "str",
              "normalized": "str",
              "original": "str",
              "reason": "str"
            }
          ],
          "source_blockers": {
            "blocked_source_rows": [
              "str"
            ],
            "source_contract_rows": "int",
            "validation_safe_false": "int",
            "validation_safe_true": "int"
          },
          "source_reference_issues": [
            {
              "blocking_validation_safe": "bool",
              "issue": "str",
              "row_id": "str",
              "row_type": "str",
              "source_id": "str"
            }
          ]
        },
        "cd2_reconciliation": {
          "accepted_master_prereg_rows": [
            {
              "assignment_id": "str",
              "experiment_id": "str",
              "hypothesis_id": "str",
              "lane_id": "str",
              "promotion_verdict": "str",
              "source_file": "str"
            }
          ],
          "ai_calls": "int",
          "blocked_cd2_master_actions": [
            {
              "artifacts": "list",
              "assignment_id": "str",
              "lane": "str",
              "master_action": "str",
              "promotion_verdict": "str",
              "reason": "str"
            }
          ],
          "canary_calls": "int",
          "cd2_artifacts": [
            {
              "artifacts": "list",
              "assignment_id": "str",
              "commit": "str",
              "g12_focus": "str",
              "lane": "str",
              "master_action": "str",
              "reason": "str",
              "title": "str"
            }
          ],
          "cd2_merge_commit": "str",
          "checked_at_utc": "str",
          "external_cash_spend_usd": "float",
          "g12_launch_status": "str",
          "head_reconciled": "str",
          "lane_id": "str",
          "live_behavior_changed": "bool",
          "master_row_delta": {
            "experiment_prereg_rows_added": "int",
            "hypothesis_rows_added": "int",
            "mechanism_rows_added": "int",
            "source_contract_rows_added": "int",
            "survivor_backlog_rows_added": "int"
          },
          "mt5_calls": "int",
          "order_calls": "int",
          "paid_data_calls": "int",
          "promotion_verdict": "str",
          "public_web_fetches_by_g0": "int",
          "source_policy": {
            "source_contract_rows_added": "int",
            "source_registry_action": "str",
            "validation_safe_true_allowed": "bool",
            "validation_safe_true_rows_after_reconciliation": "int"
          },
          "status": "str",
          "wave2_primary_reconciliation_commit": "str",
          "wave2_status_commit": "str"
        },
        "cross_domain_second_pass_assignments": "str",
        "g0_governor_reconciliation": {
          "checked_at_utc": "str",
          "governor_lane": "str",
          "head_reconciled": "str",
          "lane_blockers": {
            "G1": [
              "str"
            ],
            "G10": [
              "str"
            ],
            "G11": [
              "str"
            ],
            "G2": [
              "str"
            ],
            "G3": [
              "str"
            ],
            "G4": [
              "str"
            ],
            "G5": [
              "str"
            ],
            "G6": [
              "str"
            ],
            "G7": [
              "str"
            ],
            "G8": [
              "str"
            ],
            "G9": [
              "str"
            ]
          },
          "lane_counts": {
            "G1": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G10": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G11": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G2": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G3": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G4": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G5": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G6": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G7": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G8": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            },
            "G9": {
              "effective_commit_sha": "str",
              "experiment_preregs": "int",
              "hypotheses": "int",
              "mechanisms": "int",
              "source_contracts": "int",
              "status_source": "list"
            }
          },
          "missing_lane_artifacts": [
            {
              "artifact_gap": "str",
              "blocking_master_merge": "bool",
              "lane_id": "str"
            }
          ],
          "primary_reconciliation_commit_sha": "str",
          "promotion_verdict": "str",
          "row_counts": {
            "experiment_prereg_rows_merged": "int",
            "goal_status_rows_total": "int",
            "hypothesis_rows_merged": "int",
            "mechanism_rows_merged": "int",
            "source_contract_rows_reconciled": "int"
          },
          "schema_check": {
            "duplicate_report": {
              "experiment_id_duplicates": "list",
              "hypothesis_id_duplicates": "list",
              "mechanism_id_duplicates": "list",
              "source_id_duplicates": "list"
            },
            "experiment_prereg_summary": {
              "experiment_prereg_rows": "int",
              "outcome_review_opened_false": "int",
              "outcome_review_opened_true": "int"
            },
            "hard_blocker_issue_count": "int",
            "label_class_counts_after_g0_normalization": {
              "broker_actual_r": "int",
              "context_only": "int",
              "lifecycle_no_fill": "int",
              "observation_only": "int",
              "synthetic_path_r": "int"
            },
            "no_leak_semantic_blockers": [
              "dict"
            ],
            "normalizations": [
              "dict"
            ],
            "relationship_issues": [],
            "required_field_issues": [],
            "source_contract_summary": {
              "blocked_source_rows": "list",
              "source_contract_rows": "int",
              "validation_safe_false": "int",
              "validation_safe_true": "int"
            },
            "source_reference_issues": [
              "dict"
            ]
          },
          "scope": "str",
          "wave2_merge_commit": "str"
        },
        "g12_red_team_shortlist": "str",
        "goal_status_rows": [
          {
            "blockers": [
              "str"
            ],
            "cd2_reconciliation": {
              "accepted_master_prereg_rows": "list",
              "ai_calls": "int",
              "blocked_cd2_master_actions": "list",
              "canary_calls": "int",
              "cd2_artifacts": "list",
              "cd2_merge_commit": "str",
              "checked_at_utc": "str",
              "external_cash_spend_usd": "float",
              "g12_launch_status": "str",
              "head_reconciled": "str",
              "lane_id": "str",
              "live_behavior_changed": "bool",
              "master_row_delta": "dict",
              "mt5_calls": "int",
              "order_calls": "int",
              "paid_data_calls": "int",
              "promotion_verdict": "str",
              "public_web_fetches_by_g0": "int",
              "source_policy": "dict",
              "status": "str",
              "wave2_primary_reconciliation_commit": "str",
              "wave2_status_commit": "str"
            },
            "checked_at_utc": "str",
            "commit_sha": "NoneType",
            "files_written": [
              "str"
            ],
            "lane_id": "str",
            "lane_status": "str",
            "next_questions": [
              "str"
            ],
            "promotion_verdict": "str",
            "tests_run": [
              "str"
            ]
          }
        ],
        "post_g12_closeout": {
          "accepted_cd2_preregs_outcome_closed": [
            "str"
          ],
          "checked_at_utc": "str",
          "closeout_artifact": "str",
          "head_read": "str",
          "outcome_review_opened_true": "int",
          "promotion_verdict": "str",
          "standing_blockers_enforced": [
            "str"
          ],
          "survivor_backlog_rows": "int",
          "validation_safe_true_sources": "int"
        },
        "promotion_verdict": "str",
        "registries": {
          "experiment_preregistry": {
            "cd2_rows_registered": "int",
            "outcome_review_opened_true": "int",
            "path": "str",
            "promotion_verdict": "str",
            "rows": "int",
            "schema": "str",
            "status": "str"
          },
          "hypothesis_registry": {
            "g0_label_class_normalizations": "int",
            "no_leak_semantic_blockers": "int",
            "path": "str",
            "promotion_verdict": "str",
            "rows": "int",
            "schema": "str",
            "status": "str"
          },
          "mechanism_registry": {
            "path": "str",
            "promotion_verdict": "str",
            "rows": "int",
            "schema": "str",
            "status": "str"
          },
          "source_contract_registry": {
            "path": "str",
            "promotion_verdict": "str",
            "rows": "int",
            "schema": "str",
            "status": "str",
            "validation_safe_true": "int"
          }
        },
        "schema_version": "str",
        "survivor_backlog": []
      },
      "size_bytes": 135001,
      "source_hash": "9bf69dcb61adadb59becd96a3ec881d5dd38f95c93a11d80f95532433639b8c4",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "blocker_summary",
        "cd2_reconciliation",
        "cross_domain_second_pass_assignments",
        "g0_governor_reconciliation",
        "g12_red_team_shortlist",
        "goal_status_rows",
        "post_g12_closeout",
        "promotion_verdict",
        "registries",
        "schema_version",
        "survivor_backlog"
      ]
    },
    {
      "key_shape_fingerprint": "9b039794bbeb35ca4fcf75d01e2b2a6374769f1128c30627ff2ffac1fd15768c",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/OTG0_COMPLETION_AUDIT_2026-05-07.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/OTG0_COMPLETION_AUDIT_2026-05-07.json",
      "shape": {
        "access_scope": "str",
        "artifact_family": "str",
        "can_mark_otg0_control_artifacts_complete": "bool",
        "controlling_inputs": [
          {
            "path": "str",
            "sha256": "str",
            "size_bytes": "int"
          }
        ],
        "duplicate_hypothesis_families": {
          "HYP-G8-VIX1D9D-STRESS-002": [
            "str"
          ],
          "HYP-G9-OFFLINE-RL-POLICY-009": [
            "str"
          ]
        },
        "generated_at_utc": "str",
        "git_head_at_generation": "str",
        "objective_restatement": [
          "str"
        ],
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "prompt_to_artifact_checklist": [
          {
            "evidence": [
              "str"
            ],
            "requirement": "str",
            "status": "str"
          }
        ],
        "standing_blockers": [
          {
            "blocker_id": "str",
            "evidence": "str",
            "name": "str",
            "next_exact_question": "str"
          }
        ],
        "validation_safe": "bool",
        "version_date": "str"
      },
      "size_bytes": 12766,
      "source_hash": "3baecb56c4de5049576554150f2c0ffda0c7e15dd7127a46632c8e625f6fcabc",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "access_scope",
        "artifact_family",
        "can_mark_otg0_control_artifacts_complete",
        "controlling_inputs",
        "duplicate_hypothesis_families",
        "generated_at_utc",
        "git_head_at_generation",
        "objective_restatement",
        "outcome_review_opened",
        "promotion_verdict",
        "prompt_to_artifact_checklist",
        "standing_blockers",
        "validation_safe",
        "version_date"
      ]
    },
    {
      "key_shape_fingerprint": "72177954b9ff635ba0dc5cd4406eb9ceea177b32020161e041f354b6cdb79e51",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/OTG0_FROZEN_COHORT_PACKET_MANIFEST_2026-05-07.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/OTG0_FROZEN_COHORT_PACKET_MANIFEST_2026-05-07.json",
      "shape": {
        "access_scope": "str",
        "artifact_family": "str",
        "class_required_fields": {
          "broker_actual_r_blocked": [
            "str"
          ],
          "control_only": [
            "str"
          ],
          "forward_shadow_prospective": [
            "str"
          ],
          "lifecycle_no_fill_existing_data_audit": [
            "str"
          ],
          "source_asof_cleanup_first": [
            "str"
          ],
          "synthetic_replay_existing_data_audit": [
            "str"
          ]
        },
        "controlling_inputs": [
          {
            "path": "str",
            "sha256": "str",
            "size_bytes": "int"
          }
        ],
        "generated_at_utc": "str",
        "git_head_at_generation": "str",
        "label_family_rules": {
          "broker_actual_r": "str",
          "context_only": "str",
          "fill_no_fill": "str",
          "lifecycle_no_fill": "str",
          "observation_only": "str",
          "synthetic_path_r": "str"
        },
        "outcome_review_opened": "bool",
        "packet_manifest_status": "str",
        "packets": [
          {
            "alternative_definition": "str",
            "blockers": [
              "dict"
            ],
            "cohort_preregistered": "str",
            "cost_slippage_assumptions": "str",
            "descriptive_source_requirements_from_mechanism": [
              "str"
            ],
            "duplicate_policy": "str",
            "experiment_id": "str",
            "hypothesis_id": "str",
            "label_family_from_hypothesis": "str",
            "label_separation_policy": "str",
            "lane": "str",
            "metric_preregistered": "str",
            "next_lane": "str",
            "no_leak_fields_from_hypothesis": [
              "str"
            ],
            "null_definition": "str",
            "otg0_testing_lane": "str",
            "outcome_review_opened_owner_review": "bool",
            "outcome_review_opened_preregistry": "bool",
            "owner_testing_class": "str",
            "packet_id": "str",
            "packet_status": "str",
            "promotion_blockers_from_hypothesis": [
              "str"
            ],
            "promotion_verdict": "str",
            "registered_source_contracts": [],
            "required_packet_fields": [
              "str"
            ],
            "result_quarantine_path": "str",
            "sample_floor": "str",
            "source_gate_status": "str",
            "source_path_policy": "str",
            "test_method": "str",
            "unresolved_source_refs": []
          }
        ],
        "promotion_verdict": "str",
        "universal_packet_fields": [
          "str"
        ],
        "validation_safe": "bool",
        "version_date": "str"
      },
      "size_bytes": 545223,
      "source_hash": "d66c8aab004283afe4291dd5f9194797d689466301f67708ecd30ed7d2283fa7",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "access_scope",
        "artifact_family",
        "class_required_fields",
        "controlling_inputs",
        "generated_at_utc",
        "git_head_at_generation",
        "label_family_rules",
        "outcome_review_opened",
        "packet_manifest_status",
        "packets",
        "promotion_verdict",
        "universal_packet_fields",
        "validation_safe",
        "version_date"
      ]
    },
    {
      "key_shape_fingerprint": "94aac0ecc410ea81b78cbcffcbb3ac99da286ac13e6ea3c992d69accf3badf98",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/OTG0_PREREG_CLASSIFICATION_LEDGER_2026-05-07.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/OTG0_PREREG_CLASSIFICATION_LEDGER_2026-05-07.json",
      "shape": {
        "access_scope": "str",
        "artifact_family": "str",
        "class_mapping": {
          "BROKER_ACTUAL_R_SEPARATE_OR_BLOCKED": {
            "next_lane": "str",
            "otg0_class": "str",
            "packet_status": "str"
          },
          "CONTROL_OR_OBSERVATION_ONLY": {
            "next_lane": "str",
            "otg0_class": "str",
            "packet_status": "str"
          },
          "EXISTING_DATA_LIFECYCLE_OR_NO_FILL_CANDIDATE": {
            "next_lane": "str",
            "otg0_class": "str",
            "packet_status": "str"
          },
          "EXISTING_DATA_SYNTHETIC_REPLAY_CANDIDATE": {
            "next_lane": "str",
            "otg0_class": "str",
            "packet_status": "str"
          },
          "FORWARD_SHADOW_OR_PROSPECTIVE": {
            "next_lane": "str",
            "otg0_class": "str",
            "packet_status": "str"
          },
          "SOURCE_ASOF_CLEANUP_BEFORE_OUTCOME_TEST": {
            "next_lane": "str",
            "otg0_class": "str",
            "packet_status": "str"
          }
        },
        "controlling_inputs": [
          {
            "path": "str",
            "sha256": "str",
            "size_bytes": "int"
          }
        ],
        "duplicate_hypothesis_families": {
          "HYP-G8-VIX1D9D-STRESS-002": [
            "str"
          ],
          "HYP-G9-OFFLINE-RL-POLICY-009": [
            "str"
          ]
        },
        "generated_at_utc": "str",
        "git_head_at_generation": "str",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "rows": [
          {
            "experiment_id": "str",
            "hypothesis_id": "str",
            "lane": "str",
            "metric": "str",
            "next_lane": "str",
            "otg0_testing_lane": "str",
            "outcome_review_opened": "bool",
            "owner_testing_class": "str",
            "packet_id": "str",
            "packet_status": "str",
            "promotion_verdict": "str"
          }
        ],
        "summary": {
          "master_prereg_rows": "int",
          "otg0_class_counts": {
            "broker_actual_r_blocked": "int",
            "control_only": "int",
            "forward_shadow_prospective": "int",
            "lifecycle_no_fill_existing_data_audit": "int",
            "source_asof_cleanup_first": "int",
            "synthetic_replay_existing_data_audit": "int"
          },
          "owner_class_counts": {
            "BROKER_ACTUAL_R_SEPARATE_OR_BLOCKED": "int",
            "CONTROL_OR_OBSERVATION_ONLY": "int",
            "EXISTING_DATA_LIFECYCLE_OR_NO_FILL_CANDIDATE": "int",
            "EXISTING_DATA_SYNTHETIC_REPLAY_CANDIDATE": "int",
            "FORWARD_SHADOW_OR_PROSPECTIVE": "int",
            "SOURCE_ASOF_CLEANUP_BEFORE_OUTCOME_TEST": "int"
          },
          "owner_expected_count_mismatch": {},
          "owner_rows_parsed": "int"
        },
        "validation_safe": "bool",
        "version_date": "str"
      },
      "size_bytes": 67209,
      "source_hash": "20b1702ebe354e40450ec4a0b86c49a84dd7d2777d638281f6d1d6cb09cffe85",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "access_scope",
        "artifact_family",
        "class_mapping",
        "controlling_inputs",
        "duplicate_hypothesis_families",
        "generated_at_utc",
        "git_head_at_generation",
        "outcome_review_opened",
        "promotion_verdict",
        "rows",
        "summary",
        "validation_safe",
        "version_date"
      ]
    },
    {
      "key_shape_fingerprint": "a8c5143f7406aef96a902fc34015da9d269268d1021363b7886c06c49488af6d",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/OTL1_LIFECYCLE_NO_FILL_PACKET_AUDIT_2026-05-07.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/OTL1_LIFECYCLE_NO_FILL_PACKET_AUDIT_2026-05-07.json",
      "shape": {
        "artifact_family": "str",
        "audit_status": "str",
        "completion_checklist": {
          "all_10_packets_audited": "bool",
          "cancel_expiry_wrong_side_checked": "bool",
          "decision_asof_source_capture_checked": "bool",
          "duplicate_group_id_checked": "bool",
          "label_family_separation_checked": "bool",
          "lifecycle_state_and_denominator_checked": "bool",
          "mandatory_preflight_complete": "bool",
          "no_leak_fields_checked": "bool",
          "no_outcome_tests_run": "bool",
          "no_r_result_values_read": "bool",
          "packet_file_existence_checked": "bool",
          "source_contracts_checked": "bool",
          "stale_context_and_hidden_assumptions_checked": "bool"
        },
        "controlling_inputs": [
          "str"
        ],
        "global_blockers": [
          {
            "blocker_id": "str",
            "evidence": "str",
            "required_resolution": "str"
          }
        ],
        "outcome_tests_run": "bool",
        "packet_verdict_counts": {
          "BLOCKED_WITH_EXACT_FIELDS": "int",
          "PASS_PACKET_READY_FOR_TEST_IMPLEMENTATION": "int"
        },
        "packets": [
          {
            "blockers": [
              "str"
            ],
            "experiment_id": "str",
            "lane": "str",
            "packet_id": "str",
            "verdict": "str"
          }
        ],
        "preflight": {
          "branch_verified": "str",
          "generate_live_state_ran": "bool",
          "mandatory_context_read": [
            "str"
          ],
          "stale_context_handling": "str",
          "worktree": "str"
        },
        "promotion_verdict": "str",
        "r_result_values_read": "bool",
        "source_schema_evidence": {
          "g7_fomc_cache": {
            "fed_fomc_calendars_html_exists": "bool",
            "remaining_blockers": [
              "str"
            ]
          },
          "g8_cboe_cache": {
            "remaining_blockers": [
              "str"
            ],
            "vol_csv_files_exist": "bool"
          },
          "news_calendar": {
            "configured_event_count": "int",
            "configured_path": "str",
            "configured_path_exists": "bool",
            "configured_updated_at": "str",
            "contract_path": "str",
            "contract_path_exists": "bool"
          },
          "pending_limit_lifecycle_audit_jsonl": {
            "final_state_counts": {
              "NO_FILL_CANCELLED_SYSTEM_OR_MANUAL": "int",
              "NO_FILL_CANCELLED_WRONG_SIDE": "int",
              "NO_FILL_STILL_PENDING": "int",
              "PENDING_LIFECYCLE_GROUP_MISSING": "int"
            },
            "rows": "int"
          },
          "pending_limit_lifecycle_jsonl": {
            "exact_required_fields_present": [
              "str"
            ],
            "forbidden_primary_field_names_present": [
              "str"
            ],
            "rows": "int",
            "state_counts": {
              "no_fill_cancelled": "int",
              "no_fill_cancelled_wrong_side": "int",
              "no_fill_still_pending": "int"
            }
          },
          "prefill_delivery_path_audit_jsonl": {
            "duplicate_aware_counting_counts": {
              "BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP": "int",
              "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY": "int",
              "DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE": "int",
              "NO_OPPORTUNITY_CLUSTER_ROW": "int"
            },
            "rows": "int"
          },
          "prefill_delivery_path_jsonl": {
            "rows": "int",
            "source_hash_present_rows": "int",
            "source_symbol_present_rows": "int",
            "trade_id_present_rows": "int"
          },
          "raw_ohlc_prefill_delivery_path_coverage_json": {
            "captured_setup_rows": "int",
            "missing_fields": [
              "str"
            ],
            "rows_with_broker_lifecycle_state": "int",
            "rows_with_original_poi_bounds": "int"
          },
          "result_quarantine_paths": {
            "checked": "int",
            "existing": "int"
          }
        },
        "validation_safe": "bool",
        "version_date": "str"
      },
      "size_bytes": 13331,
      "source_hash": "c99574f6a231955b6ad707168b8bfa5ee813af0738ab2841ba867ffe5b96351a",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "artifact_family",
        "audit_status",
        "completion_checklist",
        "controlling_inputs",
        "global_blockers",
        "outcome_tests_run",
        "packet_verdict_counts",
        "packets",
        "preflight",
        "promotion_verdict",
        "r_result_values_read",
        "source_schema_evidence",
        "validation_safe",
        "version_date"
      ]
    },
    {
      "key_shape_fingerprint": "8e0032e0caaf746c0aeca4ed312318b6910da52f9fae852163640a73b31a4b30",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr061_geometry_horizon_sidecar/CNR061_EXACT_BLOCKER_OR_IMPOSSIBILITY_LEDGER_2026-05-08.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr061_geometry_horizon_sidecar/CNR061_EXACT_BLOCKER_OR_IMPOSSIBILITY_LEDGER_2026-05-08.json",
      "shape": {
        "artifact_family": "str",
        "blocker_rows": [
          {
            "blocker_state": "str",
            "blockers": [
              "str"
            ],
            "decision_asof_utc": "str",
            "entry_sl_tp_or_level_packet_available_from_source_field": "bool",
            "g12_reaudit_ready_status": "str",
            "live_effect": "bool",
            "minimum_unblocker": "str",
            "otr061_recovery_join_status": "str",
            "otx_path_status": "str",
            "otx_quote_path_join_status": "str",
            "otx_quote_status": "str",
            "packet_id": "str",
            "pre_entry_target_already_passed_check": "str",
            "promotion_verdict": "str",
            "quote_source_status": "str",
            "record_id": "str",
            "session": "str",
            "side": "str",
            "source_candidate_id": "str",
            "source_record_id": "str",
            "source_row_sha256": "str",
            "symbol": "str",
            "target_binding_status": "str",
            "target_model_family": "str",
            "timing_model_family": "str",
            "validation_safe": "bool"
          }
        ],
        "blocker_summary": {
          "blocked_e0e1_t0_rows": "int",
          "by_pre_entry_target_already_passed_check": {
            "NOT_COMPUTED_QUOTE_BLOCKED": "int",
            "TRUE_SOURCE_GEOMETRY_GATE_NO_R_SCORING": "int"
          },
          "by_quote_source_status": {
            "BLOCKED_NO_SOURCE_HASHED_EXECUTABLE_QUOTE": "int",
            "QUOTE_EXTRACTED_SOURCE_HASHED": "int"
          },
          "by_symbol": {
            "US30_cash": "int",
            "USDJPY": "int",
            "XAGUSD": "int",
            "XAUUSD": "int"
          },
          "otr061_recovered_rows_not_ready": "int"
        },
        "generated_at_utc": "str",
        "impossibility_status": "str",
        "live_effect": "bool",
        "minimum_logger_or_parser_requirements": [
          "str"
        ],
        "no_post_hoc_rescue_performed": "bool",
        "outcome_review_opened": "bool",
        "packet_id": "str",
        "promotion_verdict": "str",
        "ready_packet_status": "str",
        "schema_version": "str",
        "validation_safe": "bool"
      },
      "size_bytes": 161191,
      "source_hash": "e5c4e4985f4f26786a477cc95e607d082f037c743fda866d8337ca8a53ed3ce2",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "artifact_family",
        "blocker_rows",
        "blocker_summary",
        "generated_at_utc",
        "impossibility_status",
        "live_effect",
        "minimum_logger_or_parser_requirements",
        "no_post_hoc_rescue_performed",
        "outcome_review_opened",
        "packet_id",
        "promotion_verdict",
        "ready_packet_status",
        "schema_version",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "9ad3aad7084e67586266cc1e9df13a2c067a767205ffca63724f32c592b65c83",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr061_geometry_horizon_sidecar/CNR061_G12_REAUDIT_READY_PROPOSAL_2026-05-08.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr061_geometry_horizon_sidecar/CNR061_G12_REAUDIT_READY_PROPOSAL_2026-05-08.json",
      "shape": {
        "artifact_family": "str",
        "blocked_e0e1_t0_rows_not_in_packet": "int",
        "g12_oti7_blocker_context_used": [
          {
            "hypothesis": "str",
            "required_unblocker": "str",
            "status": "str"
          }
        ],
        "generated_at_utc": "str",
        "live_effect": "bool",
        "no_promotion_claim": "bool",
        "not_a_result_lane": "bool",
        "outcome_review_opened": "bool",
        "packet_id": "str",
        "promotion_verdict": "str",
        "proposal_status": "str",
        "ready_sidecar_row_count": "int",
        "ready_unique_record_ids": [
          "str"
        ],
        "required_g12_checks": [
          "str"
        ],
        "schema_version": "str",
        "validation_safe": "bool"
      },
      "size_bytes": 1868,
      "source_hash": "31e3a3e008d17a52d2b1545c50f0c8739dab0b1701af90eb3e2ee2fc94223a1a",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "artifact_family",
        "blocked_e0e1_t0_rows_not_in_packet",
        "g12_oti7_blocker_context_used",
        "generated_at_utc",
        "live_effect",
        "no_promotion_claim",
        "not_a_result_lane",
        "outcome_review_opened",
        "packet_id",
        "promotion_verdict",
        "proposal_status",
        "ready_sidecar_row_count",
        "ready_unique_record_ids",
        "required_g12_checks",
        "schema_version",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "263103b3b8881b503c097c4743a995b4f4c967d546e506d5758df49dc179fc9c",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr061_geometry_horizon_sidecar/CNR061_GEOMETRY_HORIZON_SIDECAR_COMPLETION_AUDIT_2026-05-08.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr061_geometry_horizon_sidecar/CNR061_GEOMETRY_HORIZON_SIDECAR_COMPLETION_AUDIT_2026-05-08.json",
      "shape": {
        "account_history_accessed": "bool",
        "api_calls": "int",
        "artifact_family": "str",
        "blocked_packet_outcome_source_read": "bool",
        "blocked_rows_not_in_packet": "int",
        "broker_actual_r_accessed": "bool",
        "can_mark_goal_complete_after_verifier_tests_and_commit": "bool",
        "databento_calls": "int",
        "deliverable_status": "str",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "live_trade_results_accessed": "bool",
        "mt5_order_calls": "int",
        "no_outcome_scoring_or_post_hoc_rescue_performed": "bool",
        "objective_restatement": "str",
        "order_calls": "int",
        "outcome_review_opened": "bool",
        "paid_data_calls": "int",
        "promotion_verdict": "str",
        "prompt_to_artifact_checklist": [
          {
            "evidence": "str",
            "requirement": "str",
            "status": "str"
          }
        ],
        "schema_version": "str",
        "sidecar_packet_rows": "int",
        "validation_safe": "bool",
        "verification_command_results": [
          {
            "command": "str",
            "evidence": "str",
            "status": "str"
          }
        ],
        "verification_requirements": [
          {
            "evidence": "str",
            "requirement": "str",
            "status": "str"
          }
        ]
      },
      "size_bytes": 5977,
      "source_hash": "36c171012876fd3e708c8791f0092787a4f15c5c43f43bfd7a92b8c4868882b9",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "account_history_accessed",
        "api_calls",
        "artifact_family",
        "blocked_packet_outcome_source_read",
        "blocked_rows_not_in_packet",
        "broker_actual_r_accessed",
        "can_mark_goal_complete_after_verifier_tests_and_commit",
        "databento_calls",
        "deliverable_status",
        "generated_at_utc",
        "live_effect",
        "live_trade_results_accessed",
        "mt5_order_calls",
        "no_outcome_scoring_or_post_hoc_rescue_performed",
        "objective_restatement",
        "order_calls",
        "outcome_review_opened",
        "paid_data_calls",
        "promotion_verdict",
        "prompt_to_artifact_checklist",
        "schema_version",
        "sidecar_packet_rows",
        "validation_safe",
        "verification_command_results",
        "verification_requirements"
      ]
    },
    {
      "key_shape_fingerprint": "fbeb1025480d62c1681eeae490494abcbe34262633850870485e3c59e231b952",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr061_geometry_horizon_sidecar/CNR061_NOLEAK_DUPLICATE_AUDIT_2026-05-08.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr061_geometry_horizon_sidecar/CNR061_NOLEAK_DUPLICATE_AUDIT_2026-05-08.json",
      "shape": {
        "account_history_accessed": "bool",
        "api_calls": "int",
        "artifact_family": "str",
        "blocked_packet_outcome_source_read": "bool",
        "broker_actual_r_accessed": "bool",
        "databento_calls": "int",
        "duplicate_denominator_key_counts": {
          "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-04|london|SHORT|75.471|CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1": "int",
          "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-04|london|SHORT|75.471|CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1": "int",
          "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222|CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1": "int",
          "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222|CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1": "int"
        },
        "duplicate_group_counts": {
          "G6_CNR|XAGUSD|2026-05-04|london|SHORT|75.471": "int",
          "G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222": "int"
        },
        "duplicate_policy": "str",
        "forbidden_sidecar_key_hits": [],
        "forbidden_sidecar_key_status": "str",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "live_trade_results_accessed": "bool",
        "metadata_flag_status": {
          "live_effect": "bool",
          "outcome_review_opened": "bool",
          "promotion_verdict": "str",
          "validation_safe": "bool"
        },
        "mt5_order_calls": "int",
        "order_calls": "int",
        "outcome_review_opened": "bool",
        "paid_data_calls": "int",
        "promotion_verdict": "str",
        "schema_version": "str",
        "sidecar_row_count": "int",
        "unique_duplicate_group_count": "int",
        "unique_sidecar_row_hashes": "int",
        "validation_safe": "bool"
      },
      "size_bytes": 1808,
      "source_hash": "8f9d84082004c6ce2d41463f1c2afd71e5179a26e9f59fda2a3359521d6ac109",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "account_history_accessed",
        "api_calls",
        "artifact_family",
        "blocked_packet_outcome_source_read",
        "broker_actual_r_accessed",
        "databento_calls",
        "duplicate_denominator_key_counts",
        "duplicate_group_counts",
        "duplicate_policy",
        "forbidden_sidecar_key_hits",
        "forbidden_sidecar_key_status",
        "generated_at_utc",
        "live_effect",
        "live_trade_results_accessed",
        "metadata_flag_status",
        "mt5_order_calls",
        "order_calls",
        "outcome_review_opened",
        "paid_data_calls",
        "promotion_verdict",
        "schema_version",
        "sidecar_row_count",
        "unique_duplicate_group_count",
        "unique_sidecar_row_hashes",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "bc6c33c8f05a70d064695517d1b3d4805e138f54f2ad3e575101565b9bdf00f2",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr061_geometry_horizon_sidecar/CNR061_SOURCE_JOIN_MAP_2026-05-08.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr061_geometry_horizon_sidecar/CNR061_SOURCE_JOIN_MAP_2026-05-08.json",
      "shape": {
        "artifact_family": "str",
        "conclusion": "str",
        "duplicate_group_join_ambiguity": [
          {
            "duplicate_group_id": "str",
            "join_status": "str",
            "otx_records_in_group": "int",
            "sidecar_rows": "int"
          }
        ],
        "generated_at_utc": "str",
        "join_attempts": [
          {
            "ambiguous_rows": "int",
            "match_widths": {
              "1": "int"
            },
            "matched_rows": "int",
            "missing_rows": "int",
            "name": "str",
            "source_rows": "int"
          }
        ],
        "join_failures": [],
        "live_effect": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "schema_version": "str",
        "source_counts": {
          "cnr_geometry_matrix_pkt061_rows": "int",
          "cnr_source_field_pkt061_e0e1_t0_rows": "int",
          "cnr_source_field_pkt061_e0e1_t0_unique_record_ids": "int",
          "cnr_source_field_pkt061_rows_all_timing_targets": "int",
          "g12_ready_pkt061_rows": "int",
          "g12_ready_pkt061_unique_record_ids": "int",
          "otr061_recovered_rows": "int",
          "otx_pkt061_proposal_rows": "int",
          "otx_pkt061_rows_with_decision_quote": "int",
          "otx_pkt061_rows_with_entry_sl_tp_or_level_packet": "int",
          "otx_pkt061_rows_with_ordered_path": "int",
          "sidecar_ready_rows": "int",
          "sidecar_unique_record_ids": "int"
        },
        "validation_safe": "bool"
      },
      "size_bytes": 3078,
      "source_hash": "60ebcd0c75adc9836f79aaeb9ff53c93cd45e8947823cafc426ff6bab5aece4b",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "artifact_family",
        "conclusion",
        "duplicate_group_join_ambiguity",
        "generated_at_utc",
        "join_attempts",
        "join_failures",
        "live_effect",
        "outcome_review_opened",
        "promotion_verdict",
        "schema_version",
        "source_counts",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "7f8dceceb0d256564d5802bac25f32d8e59e6ec50cfef842441002580e58af6e",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr061_geometry_horizon_sidecar/CNR061_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr061_geometry_horizon_sidecar/CNR061_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.json",
      "shape": {
        "absolute_local_root_searches": [
          {
            "denied_or_walk_errors": [],
            "exists": "bool",
            "matched_path_count_returned": "int",
            "matched_paths": [
              "str"
            ],
            "patterns": [
              "str"
            ],
            "root": "str",
            "search_limit_note": "str",
            "visited_files_until_limit": "int"
          }
        ],
        "access_request_status": "str",
        "access_requests": [],
        "account_history_accessed": "bool",
        "api_calls": "int",
        "artifact_family": "str",
        "blocked_packet_outcome_source_read": "bool",
        "broker_actual_r_accessed": "bool",
        "databento_calls": "int",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "live_trade_results_accessed": "bool",
        "mt5_order_calls": "int",
        "order_calls": "int",
        "outcome_review_opened": "bool",
        "paid_data_calls": "int",
        "promotion_verdict": "str",
        "schema_version": "str",
        "shadow_log_content_policy": "str",
        "source_files": [
          {
            "absolute_path": "str",
            "exists": "bool",
            "path": "str",
            "role": "str",
            "sha256": "str"
          }
        ],
        "source_hash_failures": [],
        "source_safe_token_scan": {
          "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\cnr061_geometry_horizon_sidecar": {
            "exists": "bool",
            "files_scanned": "int",
            "scope": "str",
            "token_counts": {
              "OTG0-PKT-061": "int",
              "decision_quote_packet": "int",
              "entry_sl_tp_or_level_packet": "int",
              "path_end_utc": "int",
              "path_start_utc": "int",
              "record_id": "int",
              "source_record_id": "int"
            }
          },
          "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\cnr_geometry_decay_residual_control": {
            "exists": "bool",
            "files_scanned": "int",
            "scope": "str",
            "token_counts": {
              "OTG0-PKT-061": "int",
              "decision_quote_packet": "int",
              "entry_sl_tp_or_level_packet": "int",
              "path_end_utc": "int",
              "path_start_utc": "int",
              "record_id": "int",
              "source_record_id": "int"
            }
          },
          "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder": {
            "exists": "bool",
            "files_scanned": "int",
            "scope": "str",
            "token_counts": {
              "OTG0-PKT-061": "int",
              "decision_quote_packet": "int",
              "entry_sl_tp_or_level_packet": "int",
              "path_end_utc": "int",
              "path_start_utc": "int",
              "record_id": "int",
              "source_record_id": "int"
            }
          },
          "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\g12_cnr_source_field_packet_audit": {
            "exists": "bool",
            "files_scanned": "int",
            "scope": "str",
            "token_counts": {
              "OTG0-PKT-061": "int",
              "decision_quote_packet": "int",
              "entry_sl_tp_or_level_packet": "int",
              "path_end_utc": "int",
              "path_start_utc": "int",
              "record_id": "int",
              "source_record_id": "int"
            }
          },
          "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\g12_oti7_cnr_post_result_audit": {
            "exists": "bool",
            "files_scanned": "int",
            "scope": "str",
            "token_counts": {
              "OTG0-PKT-061": "int",
              "decision_quote_packet": "int",
              "entry_sl_tp_or_level_packet": "int",
              "path_end_utc": "int",
              "path_start_utc": "int",
              "record_id": "int",
              "source_record_id": "int"
            }
          },
          "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\g12_otx_g6_post_audit": {
            "exists": "bool",
            "files_scanned": "int",
            "scope": "str",
            "token_counts": {
              "OTG0-PKT-061": "int",
              "decision_quote_packet": "int",
              "entry_sl_tp_or_level_packet": "int",
              "path_end_utc": "int",
              "path_start_utc": "int",
              "record_id": "int",
              "source_record_id": "int"
            }
          },
          "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery": {
            "exists": "bool",
            "files_scanned": "int",
            "scope": "str",
            "token_counts": {
              "OTG0-PKT-061": "int",
              "decision_quote_packet": "int",
              "entry_sl_tp_or_level_packet": "int",
              "path_end_utc": "int",
              "path_start_utc": "int",
              "record_id": "int",
              "source_record_id": "int"
            }
          },
          "C:\\tmp\\gtos_otb\\CNR061GEOM\\research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution": {
            "exists": "bool",
            "files_scanned": "int",
            "scope": "str",
            "token_counts": {
              "OTG0-PKT-061": "int",
              "decision_quote_packet": "int",
              "entry_sl_tp_or_level_packet": "int",
              "path_end_utc": "int",
              "path_start_utc": "int",
              "record_id": "int",
              "source_record_id": "int"
            }
          }
        },
        "validation_safe": "bool"
      },
      "size_bytes": 44260,
      "source_hash": "9b6739b76c3c7c61434da15c502b2d0f6cfa23d1b1a8d76baecb596010e4c744",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "absolute_local_root_searches",
        "access_request_status",
        "access_requests",
        "account_history_accessed",
        "api_calls",
        "artifact_family",
        "blocked_packet_outcome_source_read",
        "broker_actual_r_accessed",
        "databento_calls",
        "generated_at_utc",
        "live_effect",
        "live_trade_results_accessed",
        "mt5_order_calls",
        "order_calls",
        "outcome_review_opened",
        "paid_data_calls",
        "promotion_verdict",
        "schema_version",
        "shadow_log_content_policy",
        "source_files",
        "source_hash_failures",
        "source_safe_token_scan",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "c12e864300530dc7ea8611de0861cb35b8ee8f1a6311144619c89184424cec59",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_geometry_decay_residual_control/CNR_GEOMETRY_DECAY_INPUT_ROW_MATRIX_2026-05-08.jsonl",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_geometry_decay_residual_control/CNR_GEOMETRY_DECAY_INPUT_ROW_MATRIX_2026-05-08.jsonl",
      "shape": {
        "account_history_accessed": "bool",
        "api_calls": "int",
        "artifact_family": "str",
        "ask": "float",
        "bid": "float",
        "blocked_packet_outcome_source_read": "bool",
        "broker_actual_r_accessed": "bool",
        "broker_symbol": "str",
        "candidate_close_utc": "str",
        "countable_denominator_row": "bool",
        "databento_calls": "int",
        "decision_asof_utc": "str",
        "duplicate_denominator_key": "str",
        "duplicate_group_id": "str",
        "duplicate_policy": "str",
        "entry_eligible_utc": "str",
        "executable_quote_price": "float",
        "executable_quote_side": "str",
        "executable_stop_distance_price": "float",
        "experiment_id": "str",
        "geometry_source": "str",
        "hypothesis_id": "str",
        "input_row_hash": "str",
        "live_effect": "bool",
        "live_trade_results_accessed": "bool",
        "market_entry_geometry_gate_state": "str",
        "market_entry_geometry_valid_for_original_tp1": "bool",
        "mt5_order_calls": "int",
        "order_calls": "int",
        "original_base_r_price": "float",
        "original_entry_price": "float",
        "original_stop_loss": "float",
        "original_take_profit_1": "float",
        "outcome_review_opened": "bool",
        "packet_id": "str",
        "paid_data_calls": "int",
        "promotion_verdict": "str",
        "quote_age_ms": "int",
        "quote_displacement_from_original_entry_r": "float",
        "quote_displacement_from_original_entry_r_bin": "str",
        "quote_displacement_from_original_stop_r": "float",
        "quote_displacement_from_original_tp1_r": "float",
        "quote_displacement_from_original_tp1_r_bin": "str",
        "quote_side_rule": "str",
        "quote_source_path": "str",
        "quote_source_sha256": "str",
        "quote_source_status": "str",
        "quote_timestamp_utc": "str",
        "record_id": "str",
        "record_source_hash": "str",
        "residual_target_original_r_from_executable_quote": "float",
        "residual_target_price_from_executable_quote": "float",
        "residual_target_r_bin": "str",
        "residual_target_r_from_executable_quote": "float",
        "risk_reward_ratio_from_source": "float",
        "row_number": "int",
        "schema_version": "str",
        "session": "str",
        "side": "str",
        "signal_emitted_utc": "NoneType",
        "source_candidate_id": "str",
        "source_file_paths": [
          "str"
        ],
        "source_priority": "str",
        "source_record_id": "str",
        "source_row_sha256": "str",
        "source_sha256_hashes": [
          "str"
        ],
        "spread": "float",
        "stop_invalid_at_executable_quote": "bool",
        "stop_model_id": "str",
        "stop_r_bin": "str",
        "stop_r_from_executable_quote": "float",
        "symbol": "str",
        "target_already_passed_at_executable_quote": "bool",
        "target_binding_status": "str",
        "target_model_family": "str",
        "target_model_id": "str",
        "timing_model_family": "str",
        "upstream_forbidden_field_scan_result": "str",
        "upstream_pre_entry_target_already_passed_check": "str",
        "validation_safe": "bool"
      },
      "size_bytes": 439654,
      "source_hash": "8294e74c306abfb7cb1f9546710ff71214804815a339997c987ff53a72a3ade5",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "account_history_accessed",
        "api_calls",
        "artifact_family",
        "ask",
        "bid",
        "blocked_packet_outcome_source_read",
        "broker_actual_r_accessed",
        "broker_symbol",
        "candidate_close_utc",
        "countable_denominator_row",
        "databento_calls",
        "decision_asof_utc",
        "duplicate_denominator_key",
        "duplicate_group_id",
        "duplicate_policy",
        "entry_eligible_utc",
        "executable_quote_price",
        "executable_quote_side",
        "executable_stop_distance_price",
        "experiment_id",
        "geometry_source",
        "hypothesis_id",
        "input_row_hash",
        "live_effect",
        "live_trade_results_accessed",
        "market_entry_geometry_gate_state",
        "market_entry_geometry_valid_for_original_tp1",
        "mt5_order_calls",
        "order_calls",
        "original_base_r_price",
        "original_entry_price",
        "original_stop_loss",
        "original_take_profit_1",
        "outcome_review_opened",
        "packet_id",
        "paid_data_calls",
        "promotion_verdict",
        "quote_age_ms",
        "quote_displacement_from_original_entry_r",
        "quote_displacement_from_original_entry_r_bin",
        "quote_displacement_from_original_stop_r",
        "quote_displacement_from_original_tp1_r",
        "quote_displacement_from_original_tp1_r_bin",
        "quote_side_rule",
        "quote_source_path",
        "quote_source_sha256",
        "quote_source_status",
        "quote_timestamp_utc",
        "record_id",
        "record_source_hash",
        "residual_target_original_r_from_executable_quote",
        "residual_target_price_from_executable_quote",
        "residual_target_r_bin",
        "residual_target_r_from_executable_quote",
        "risk_reward_ratio_from_source",
        "row_number",
        "schema_version",
        "session",
        "side",
        "signal_emitted_utc",
        "source_candidate_id",
        "source_file_paths",
        "source_priority",
        "source_record_id",
        "source_row_sha256",
        "source_sha256_hashes",
        "spread",
        "stop_invalid_at_executable_quote",
        "stop_model_id",
        "stop_r_bin",
        "stop_r_from_executable_quote",
        "symbol",
        "target_already_passed_at_executable_quote",
        "target_binding_status",
        "target_model_family",
        "target_model_id",
        "timing_model_family",
        "upstream_forbidden_field_scan_result",
        "upstream_pre_entry_target_already_passed_check",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "dd2f35a4e2fea20eca0208265cf93cdbb52cc63b2268b29d157ee1b208a2f3d3",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_geometry_decay_residual_control/CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_COMPLETION_AUDIT_2026-05-08.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_geometry_decay_residual_control/CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_COMPLETION_AUDIT_2026-05-08.json",
      "shape": {
        "account_history_accessed": "bool",
        "api_calls": "int",
        "artifact_family": "str",
        "blocked_packet_outcome_source_read": "bool",
        "broker_actual_r_accessed": "bool",
        "can_mark_goal_complete_after_verifier_and_scoped_commit": "bool",
        "databento_calls": "int",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "live_trade_results_accessed": "bool",
        "matrix_summary": {
          "aggregate_sample_floor_status": "str",
          "aggregate_sample_floor_unique_groups": "int",
          "by_market_entry_geometry_gate_state": {
            "STOP_INVALID_AT_EXECUTABLE_QUOTE": "int",
            "VALID_FOR_FUTURE_RESULT_LANE_AFTER_SAMPLE_AND_DUPLICATE_AUDIT": "int"
          },
          "by_packet": {
            "OTG0-PKT-060": "int",
            "OTG0-PKT-061": "int",
            "OTG0-PKT-062": "int",
            "OTG0-PKT-063": "int",
            "OTG0-PKT-066": "int"
          },
          "by_residual_target_r_bin": {
            "GT_0_25_TO_0_5_SMALL_RESIDUAL": "int",
            "GT_0_5_TO_1_0_SUB_ONE_R": "int",
            "GT_0_TO_0_25_TINY_RESIDUAL": "int",
            "GT_1_0_TO_LT_1_5_BELOW_GTOS_MIN_RR": "int",
            "MISSING_OR_STOP_INVALID": "int"
          },
          "by_stop_r_bin": {
            "GT_1_0_TO_1_5_EXPANDED_STOP_DISTANCE": "int",
            "GT_1_5_LARGE_STOP_DISTANCE_DECAY": "int",
            "LTE_0_INVALID_STOP_GEOMETRY": "int"
          },
          "by_symbol": {
            "GBPJPY": "int",
            "NAS100": "int",
            "XAGUSD": "int",
            "XAUUSD": "int"
          },
          "by_timing_target": {
            "CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1": "int",
            "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1": "int"
          },
          "countable_rows": "int",
          "duplicate_context_rows": "int",
          "per_family_countable_unique_duplicate_groups": {
            "CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1": "int",
            "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1": "int"
          },
          "quote_age_ms_range": {
            "max": "int",
            "min": "int"
          },
          "residual_target_r_from_executable_quote_range": {
            "max": "float",
            "min": "float"
          },
          "row_count": "int",
          "stop_r_from_executable_quote_range": {
            "max": "float",
            "min": "float"
          },
          "unique_countable_duplicate_groups": "int",
          "unique_duplicate_groups": "int"
        },
        "mt5_order_calls": "int",
        "no_outcome_scoring_or_threshold_rescue_performed": "bool",
        "objective_restatement": "str",
        "order_calls": "int",
        "outcome_review_opened": "bool",
        "paid_data_calls": "int",
        "promotion_verdict": "str",
        "prompt_to_artifact_checklist": [
          {
            "evidence": "str",
            "requirement": "str",
            "status": "str"
          }
        ],
        "required_output_files": [
          "str"
        ],
        "validation_safe": "bool"
      },
      "size_bytes": 6192,
      "source_hash": "7c71263bc2b590ba6f7de6156e9795c1c300ee34edb8c98964c39939ee224774",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "account_history_accessed",
        "api_calls",
        "artifact_family",
        "blocked_packet_outcome_source_read",
        "broker_actual_r_accessed",
        "can_mark_goal_complete_after_verifier_and_scoped_commit",
        "databento_calls",
        "generated_at_utc",
        "live_effect",
        "live_trade_results_accessed",
        "matrix_summary",
        "mt5_order_calls",
        "no_outcome_scoring_or_threshold_rescue_performed",
        "objective_restatement",
        "order_calls",
        "outcome_review_opened",
        "paid_data_calls",
        "promotion_verdict",
        "prompt_to_artifact_checklist",
        "required_output_files",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "40a255a4e7920bc798d426bb1fc57f41d54ef8ce2f962089520fdfec9228b04e",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_geometry_decay_residual_control/CNR_NEXT_ROUTE_BLOCKER_DECISION_LEDGER_2026-05-08.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_geometry_decay_residual_control/CNR_NEXT_ROUTE_BLOCKER_DECISION_LEDGER_2026-05-08.json",
      "shape": {
        "account_history_accessed": "bool",
        "api_calls": "int",
        "artifact_family": "str",
        "blocked_outcome_families_remain_closed": [
          "str"
        ],
        "blocked_packet_outcome_source_read": "bool",
        "broker_actual_r_accessed": "bool",
        "databento_calls": "int",
        "g12_upstream_exact_requirement_counts": {
          "CNR_T1 target contract with frozen fixed-R multiple, stop model, executable entry quote, and source hash before outcome opening": "int",
          "CNR_T2 structural target contract with as-of level id, level timestamp, parser version, selection rule, and source hash": "int",
          "CNR_T3 terminal target contract with frozen horizon, terminal pricing source, same-bar/tick ordering policy, and source hash": "int",
          "decision_request_sent_utc, decision_response_received_utc, latency_ms, and frozen latency policy": "int",
          "earlier same-day tick/quote coverage for the trigger window; existing local parquet starts after the trigger or has no eligible quote at or before asof_cutoff_utc": "int",
          "input-only invalid-clearing policy for market-entry rows where the source-hashed executable quote is already past the original TP1 before any result audit": "int",
          "local read-only tick parquet or approved source-hashed quote cache for the exact broker symbol/date under approved roots": "int",
          "pre-outcome logger/parser field signal_emitted_utc joined to source_record_id": "int",
          "pretouch_trigger_id and pretouch_trigger_utc captured as-of before any result path is opened": "int",
          "source-bound fixed-R target model definition before outcomes": "int",
          "source-bound structural target level selected as-of before outcomes": "int",
          "source-bound terminal timebox policy before outcomes": "int",
          "source-hashed decision request/response timestamps and frozen latency policy for this source_record_id": "int",
          "source-hashed executable bid/ask/spread quote at or before the timing trigger for the packet symbol/date, with quote_timestamp_utc and source_sha256": "int",
          "source-hashed pretouch trigger id/utc captured before any outcome path review": "int",
          "source-hashed signal_emitted_utc materialized for this source_record_id": "int",
          "source-hashed timing trigger field materialized before outcome opening; CNR_E2 needs signal_emitted_utc, CNR_E3 needs request/response latency clock fields, and CNR_E4 needs pretouch_trigger_id/pretouch_trigger_utc": "int"
        },
        "generated_at_utc": "str",
        "live_effect": "bool",
        "live_trade_results_accessed": "bool",
        "mt5_order_calls": "int",
        "next_route_decisions": [
          {
            "decision": "str",
            "next_unblocker": "str",
            "route": "str"
          }
        ],
        "order_calls": "int",
        "otg0_pkt061_geometry_horizon_sidecar_findings": {
          "exact_next_blocker": "str",
          "otr061_single_xau_recovery_record_count": "int",
          "otr061_single_xau_terminal_state": "str",
          "otx_pkt061_proposal_rows": "int",
          "otx_pkt061_rows_with_decision_quote": "int",
          "otx_pkt061_rows_with_entry_sl_tp_or_level_packet": "int",
          "otx_pkt061_rows_with_ordered_path": "int",
          "source_field_pkt061_ready_rows": "int",
          "source_field_pkt061_rows_with_original_geometry": "int",
          "source_field_pkt061_status": "str",
          "source_field_pkt061_unique_duplicate_groups": "int"
        },
        "outcome_review_opened": "bool",
        "paid_data_calls": "int",
        "promotion_verdict": "str",
        "route_blocker_summary_from_source_rows": {
          "target_family_blockers": {
            "CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY": {
              "ready_rows": "int",
              "row_count": "int",
              "target_binding_status_counts": "dict",
              "target_blocker_counts": "dict"
            },
            "CNR_T2_ASOF_STRUCTURAL_LEVEL": {
              "ready_rows": "int",
              "row_count": "int",
              "target_binding_status_counts": "dict",
              "target_blocker_counts": "dict"
            },
            "CNR_T3_TIMEBOX_TERMINAL": {
              "ready_rows": "int",
              "row_count": "int",
              "target_binding_status_counts": "dict",
              "target_blocker_counts": "dict"
            }
          },
          "timing_family_blockers": {
            "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK": {
              "non_null_signal_emitted_utc_rows": "int",
              "ready_rows": "int",
              "row_count": "int",
              "timing_blocker_counts": "dict",
              "timing_source_status_counts": "dict"
            },
            "CNR_E3_LATENCY_BOUNDED_DECISION_WINDOW": {
              "non_null_signal_emitted_utc_rows": "int",
              "ready_rows": "int",
              "row_count": "int",
              "timing_blocker_counts": "dict",
              "timing_source_status_counts": "dict"
            },
            "CNR_E4_PRETOUCH_CONTINUATION_TRIGGER": {
              "non_null_signal_emitted_utc_rows": "int",
              "ready_rows": "int",
              "row_count": "int",
              "timing_blocker_counts": "dict",
              "timing_source_status_counts": "dict"
            }
          }
        },
        "validation_safe": "bool"
      },
      "size_bytes": 8388,
      "source_hash": "cc819f69aea3321a6fd26ec05dba6683c2d06454ea1dce7131812de2cc3516e1",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "account_history_accessed",
        "api_calls",
        "artifact_family",
        "blocked_outcome_families_remain_closed",
        "blocked_packet_outcome_source_read",
        "broker_actual_r_accessed",
        "databento_calls",
        "g12_upstream_exact_requirement_counts",
        "generated_at_utc",
        "live_effect",
        "live_trade_results_accessed",
        "mt5_order_calls",
        "next_route_decisions",
        "order_calls",
        "otg0_pkt061_geometry_horizon_sidecar_findings",
        "outcome_review_opened",
        "paid_data_calls",
        "promotion_verdict",
        "route_blocker_summary_from_source_rows",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "7aa4fc0eae5a5242ed4817680c8c411dcaa20a2c84d0789501a23c6b173df63a",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_geometry_decay_residual_control/CNR_NOLEAK_DUPLICATE_SAMPLE_AUDIT_2026-05-08.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_geometry_decay_residual_control/CNR_NOLEAK_DUPLICATE_SAMPLE_AUDIT_2026-05-08.json",
      "shape": {
        "account_history_accessed": "bool",
        "api_calls": "int",
        "artifact_family": "str",
        "blocked_packet_outcome_source_read": "bool",
        "broker_actual_r_accessed": "bool",
        "countable_rows": "int",
        "databento_calls": "int",
        "duplicate_context_rows": "int",
        "duplicate_denominator_key_collision_count": "int",
        "duplicate_denominator_key_collision_examples": {
          "OTG0-PKT-060|G6_OB_GENERIC|GBPJPY|2026-05-04|tokyo|LONG|213.257|CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1": "int",
          "OTG0-PKT-060|G6_OB_GENERIC|GBPJPY|2026-05-04|tokyo|LONG|213.257|CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1": "int",
          "OTG0-PKT-060|G6_OB_GENERIC|XAGUSD|2026-05-05|ny|SHORT|73.597|CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1": "int",
          "OTG0-PKT-060|G6_OB_GENERIC|XAGUSD|2026-05-05|ny|SHORT|73.597|CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1": "int",
          "OTG0-PKT-060|G6_OB_GENERIC|XAGUSD|2026-05-06|london|SHORT|73.597|CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1": "int",
          "OTG0-PKT-060|G6_OB_GENERIC|XAGUSD|2026-05-06|london|SHORT|73.597|CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1": "int",
          "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222|CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1": "int",
          "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222|CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1": "int",
          "OTG0-PKT-062|G6_OPENING_DRIVE|GBPJPY|2026-05-04|tokyo|NO_BREAKOUT_ASOF|CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1": "int",
          "OTG0-PKT-062|G6_OPENING_DRIVE|GBPJPY|2026-05-04|tokyo|NO_BREAKOUT_ASOF|CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1": "int"
        },
        "duplicate_policy": "str",
        "forbidden_input_row_key_hits": [],
        "forbidden_input_row_keys": [
          "str"
        ],
        "forbidden_input_row_scan_status": "str",
        "generated_at_utc": "str",
        "input_row_count": "int",
        "label_family_policy": "str",
        "live_effect": "bool",
        "live_trade_results_accessed": "bool",
        "mt5_order_calls": "int",
        "order_calls": "int",
        "outcome_review_opened": "bool",
        "paid_data_calls": "int",
        "promotion_verdict": "str",
        "sample_floor_status": "str",
        "sample_floor_unique_groups_per_family": "int",
        "timing_target_countable_rows": {
          "CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1": "int",
          "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1": "int"
        },
        "timing_target_unique_duplicate_groups": {
          "CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1": "int",
          "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1": "int"
        },
        "unique_countable_duplicate_groups": "int",
        "unique_duplicate_groups": "int",
        "validation_safe": "bool"
      },
      "size_bytes": 3532,
      "source_hash": "798e5af02c55ddd85b8d67aeca7ecd7861657bdacb43708b532ceb238c596d55",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "account_history_accessed",
        "api_calls",
        "artifact_family",
        "blocked_packet_outcome_source_read",
        "broker_actual_r_accessed",
        "countable_rows",
        "databento_calls",
        "duplicate_context_rows",
        "duplicate_denominator_key_collision_count",
        "duplicate_denominator_key_collision_examples",
        "duplicate_policy",
        "forbidden_input_row_key_hits",
        "forbidden_input_row_keys",
        "forbidden_input_row_scan_status",
        "generated_at_utc",
        "input_row_count",
        "label_family_policy",
        "live_effect",
        "live_trade_results_accessed",
        "mt5_order_calls",
        "order_calls",
        "outcome_review_opened",
        "paid_data_calls",
        "promotion_verdict",
        "sample_floor_status",
        "sample_floor_unique_groups_per_family",
        "timing_target_countable_rows",
        "timing_target_unique_duplicate_groups",
        "unique_countable_duplicate_groups",
        "unique_duplicate_groups",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "24fc1c2d2ac6b3f137975f4d31d0750bc73c72b7fbf05c81b21b0088fb231fac",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_geometry_decay_residual_control/CNR_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_geometry_decay_residual_control/CNR_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.json",
      "shape": {
        "absolute_local_root_searches": [
          {
            "denied_or_walk_errors": [],
            "exists": "bool",
            "matched_path_count_returned": "int",
            "matched_paths": [],
            "patterns": [
              "str"
            ],
            "root": "str",
            "search_limit_note": "str",
            "visited_files_until_limit": "int"
          }
        ],
        "access_request_status": "str",
        "access_requests": [],
        "account_history_accessed": "bool",
        "api_calls": "int",
        "artifact_family": "str",
        "blocked_packet_outcome_source_read": "bool",
        "broker_actual_r_accessed": "bool",
        "databento_calls": "int",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "live_trade_results_accessed": "bool",
        "matrix_source_hash_failures": [],
        "matrix_source_hash_status": "str",
        "mt5_order_calls": "int",
        "order_calls": "int",
        "outcome_review_opened": "bool",
        "paid_data_calls": "int",
        "promotion_verdict": "str",
        "source_files": [
          {
            "absolute_path": "str",
            "exists": "bool",
            "expected_sha256": "NoneType",
            "hash_status": "str",
            "path": "str",
            "role": "str",
            "sha256": "str"
          }
        ],
        "targeted_field_token_scan": {
          "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs": {
            "exists": "bool",
            "files_scanned": "int",
            "root": "str",
            "token_counts": {
              "decision_request_sent_utc": "int",
              "decision_response_received_utc": "int",
              "entry_sl_tp_or_level_packet": "int",
              "latency_ms": "int",
              "latency_policy_id": "int",
              "pretouch_trigger_id": "int",
              "pretouch_trigger_utc": "int",
              "signal_emitted_utc": "int"
            }
          },
          "C:\\tmp\\gtos_otb\\CNRGEOMCTRL\\research\\science_program_2026_05\\06_outcome_testing\\cnr_source_field_packet_builder": {
            "exists": "bool",
            "files_scanned": "int",
            "root": "str",
            "token_counts": {
              "decision_request_sent_utc": "int",
              "decision_response_received_utc": "int",
              "entry_sl_tp_or_level_packet": "int",
              "latency_ms": "int",
              "latency_policy_id": "int",
              "pretouch_trigger_id": "int",
              "pretouch_trigger_utc": "int",
              "signal_emitted_utc": "int"
            }
          },
          "C:\\tmp\\gtos_otb\\CNRGEOMCTRL\\research\\science_program_2026_05\\06_outcome_testing\\g12_cnr_source_field_packet_audit": {
            "exists": "bool",
            "files_scanned": "int",
            "root": "str",
            "token_counts": {
              "decision_request_sent_utc": "int",
              "decision_response_received_utc": "int",
              "entry_sl_tp_or_level_packet": "int",
              "latency_ms": "int",
              "latency_policy_id": "int",
              "pretouch_trigger_id": "int",
              "pretouch_trigger_utc": "int",
              "signal_emitted_utc": "int"
            }
          },
          "C:\\tmp\\gtos_otb\\CNRGEOMCTRL\\research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution": {
            "exists": "bool",
            "files_scanned": "int",
            "root": "str",
            "token_counts": {
              "decision_request_sent_utc": "int",
              "decision_response_received_utc": "int",
              "entry_sl_tp_or_level_packet": "int",
              "latency_ms": "int",
              "latency_policy_id": "int",
              "pretouch_trigger_id": "int",
              "pretouch_trigger_utc": "int",
              "signal_emitted_utc": "int"
            }
          },
          "C:\\tmp\\gtos_otb\\CNRGEOMCTRL\\shadow_logs": {
            "exists": "bool",
            "files_scanned": "int",
            "root": "str",
            "token_counts": {
              "decision_request_sent_utc": "int",
              "decision_response_received_utc": "int",
              "entry_sl_tp_or_level_packet": "int",
              "latency_ms": "int",
              "latency_policy_id": "int",
              "pretouch_trigger_id": "int",
              "pretouch_trigger_utc": "int",
              "signal_emitted_utc": "int"
            }
          }
        },
        "validation_safe": "bool"
      },
      "size_bytes": 33542,
      "source_hash": "78759e1606d00fca76a173259c6ce838847c91dae77443d4dd3dc62a2f6a9e5d",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "absolute_local_root_searches",
        "access_request_status",
        "access_requests",
        "account_history_accessed",
        "api_calls",
        "artifact_family",
        "blocked_packet_outcome_source_read",
        "broker_actual_r_accessed",
        "databento_calls",
        "generated_at_utc",
        "live_effect",
        "live_trade_results_accessed",
        "matrix_source_hash_failures",
        "matrix_source_hash_status",
        "mt5_order_calls",
        "order_calls",
        "outcome_review_opened",
        "paid_data_calls",
        "promotion_verdict",
        "source_files",
        "targeted_field_token_scan",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "fe04f85733d11ca6cb296e8f976fe29bd640d53b684a3346a0c2b6367f84a5df",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_next_model_control_pack/CNR_NEXT_MODEL_BLOCKER_AND_ROUTE_LEDGER_2026-05-08.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_next_model_control_pack/CNR_NEXT_MODEL_BLOCKER_AND_ROUTE_LEDGER_2026-05-08.json",
      "shape": {
        "account_history_accessed": "bool",
        "active_question_stack": [
          "str"
        ],
        "api_calls": "int",
        "artifact_family": "str",
        "blocked_packet_outcome_source_read": "bool",
        "broker_actual_r_accessed": "bool",
        "canary_calls": "int",
        "databento_calls": "int",
        "date_stamp": "str",
        "exact_blockers": [
          {
            "blocker": "str",
            "family": "str"
          }
        ],
        "generated_at_utc": "str",
        "live_effect": "bool",
        "live_order_state_accessed": "bool",
        "live_trade_results_accessed": "bool",
        "mt5_account_calls": "int",
        "mt5_order_calls": "int",
        "no_access_request_needed": "bool",
        "order_calls": "int",
        "outcome_review_opened": "bool",
        "paid_data_calls": "int",
        "promotion_verdict": "str",
        "route_decisions": [
          {
            "decision": "str",
            "reason": "str",
            "route": "str"
          }
        ],
        "schema_version": "str",
        "searched_root_ledger": {
          "forbidden_sources_seen_but_not_consumed": [
            "str"
          ],
          "searched_roots": [
            {
              "exists": "bool",
              "root": "str",
              "search_policy": "str"
            }
          ],
          "worktree_absence_is_not_data_absence_acknowledged": "bool",
          "xagusd_tick_file_count": "int"
        },
        "validation_safe": "bool"
      },
      "size_bytes": 7102,
      "source_hash": "e1ced510ae46f3b9d74d343cfe4fa4ab31c80bc0f5368a32a18fe937ae9af517",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "account_history_accessed",
        "active_question_stack",
        "api_calls",
        "artifact_family",
        "blocked_packet_outcome_source_read",
        "broker_actual_r_accessed",
        "canary_calls",
        "databento_calls",
        "date_stamp",
        "exact_blockers",
        "generated_at_utc",
        "live_effect",
        "live_order_state_accessed",
        "live_trade_results_accessed",
        "mt5_account_calls",
        "mt5_order_calls",
        "no_access_request_needed",
        "order_calls",
        "outcome_review_opened",
        "paid_data_calls",
        "promotion_verdict",
        "route_decisions",
        "schema_version",
        "searched_root_ledger",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "e87854266acd1fed2bc9c96c28dc055f8d663087dc36d2d9eac69ec1247667f1",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_next_model_control_pack/CNR_NEXT_MODEL_COMPLETION_AUDIT_2026-05-08.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_next_model_control_pack/CNR_NEXT_MODEL_COMPLETION_AUDIT_2026-05-08.json",
      "shape": {
        "account_history_accessed": "bool",
        "api_calls": "int",
        "artifact_family": "str",
        "blocked_packet_outcome_source_read": "bool",
        "broker_actual_r_accessed": "bool",
        "can_mark_goal_complete": "bool",
        "canary_calls": "int",
        "databento_calls": "int",
        "date_stamp": "str",
        "generated_artifacts": [
          "str"
        ],
        "generated_at_utc": "str",
        "live_effect": "bool",
        "live_order_state_accessed": "bool",
        "live_trade_results_accessed": "bool",
        "mt5_account_calls": "int",
        "mt5_order_calls": "int",
        "objective_restatement": [
          "str"
        ],
        "order_calls": "int",
        "outcome_review_opened": "bool",
        "paid_data_calls": "int",
        "promotion_verdict": "str",
        "prompt_to_artifact_checklist": [
          {
            "evidence": "str",
            "requirement": "str",
            "status": "str"
          }
        ],
        "schema_version": "str",
        "validation_safe": "bool",
        "verification_observed_at_utc": "str",
        "verification_results_observed": {
          "boundary_flag_scan": {
            "failures": [],
            "status": "str"
          },
          "builder_invariant_recompute": {
            "labels": [
              "str"
            ],
            "labels_allowed": "bool",
            "oti8_no_terminal_hashes": [
              "str"
            ],
            "packet_sidecar_hashes": [
              "str"
            ],
            "packet_status": "str",
            "r_key_hits": [],
            "rows": "int",
            "status": "str"
          },
          "focused_pytest": {
            "command": "str",
            "returncode": "int",
            "status": "str",
            "stderr_tail": "str",
            "stdout_tail": "str"
          },
          "forbidden_live_surface_diff_scan": {
            "changed_live_surface_files": [],
            "command": "str",
            "returncode": "int",
            "status": "str",
            "stderr_tail": "str",
            "stdout_tail": "str"
          },
          "generated_json_jsonl_parse": {
            "failures": [],
            "parsed_json_count": "int",
            "parsed_json_files": [
              "str"
            ],
            "parsed_jsonl": [
              "dict"
            ],
            "status": "str"
          },
          "no_leak_duplicate_samplefloor": {
            "checks": {
              "blocked_94": "bool",
              "no_leak": "bool",
              "sample_floor_false": "bool",
              "six_row_scope": "bool"
            },
            "status": "str"
          },
          "py_compile": {
            "command": "str",
            "returncode": "int",
            "status": "str",
            "stderr_tail": "str",
            "stdout_tail": "str"
          },
          "source_path_hash_recompute": {
            "source_hash_failures": [],
            "status": "str"
          }
        },
        "verification_status": "str"
      },
      "size_bytes": 10106,
      "source_hash": "e0a7ff2fe9162bbf06df5cc7d4125e11315d68009d80f1197677afda7634c1dd",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "account_history_accessed",
        "api_calls",
        "artifact_family",
        "blocked_packet_outcome_source_read",
        "broker_actual_r_accessed",
        "can_mark_goal_complete",
        "canary_calls",
        "databento_calls",
        "date_stamp",
        "generated_artifacts",
        "generated_at_utc",
        "live_effect",
        "live_order_state_accessed",
        "live_trade_results_accessed",
        "mt5_account_calls",
        "mt5_order_calls",
        "objective_restatement",
        "order_calls",
        "outcome_review_opened",
        "paid_data_calls",
        "promotion_verdict",
        "prompt_to_artifact_checklist",
        "schema_version",
        "validation_safe",
        "verification_observed_at_utc",
        "verification_results_observed",
        "verification_status"
      ]
    },
    {
      "key_shape_fingerprint": "0b811a8c916e7f92f5c96456766f84645e1c865972057225c68198efd17913e4",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_next_model_control_pack/CNR_TIMING_TARGET_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_next_model_control_pack/CNR_TIMING_TARGET_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json",
      "shape": {
        "account_history_accessed": "bool",
        "api_calls": "int",
        "artifact_family": "str",
        "blocked_94_not_scored_proof": {
          "blocked_rows": "int",
          "g12_blocked_audit_source": "str",
          "packet_rows_from_blocked_set": [],
          "status": "str"
        },
        "blocked_packet_outcome_source_read": "bool",
        "broker_actual_r_accessed": "bool",
        "canary_calls": "int",
        "databento_calls": "int",
        "date_stamp": "str",
        "duplicate_policy": {
          "do_not_join_on_duplicate_group_alone": "bool",
          "duplicate_denominator_key_counts": {
            "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222|CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1": "int",
            "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222|CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1": "int"
          },
          "duplicate_group_counts": {
            "G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222": "int"
          }
        },
        "exact_six_row_scope_check": {
          "oti8_no_terminal_sidecar_hashes": [
            "str"
          ],
          "packet_sidecar_hashes": [
            "str"
          ],
          "status": "str"
        },
        "generated_at_utc": "str",
        "live_effect": "bool",
        "live_order_state_accessed": "bool",
        "live_trade_results_accessed": "bool",
        "mt5_account_calls": "int",
        "mt5_order_calls": "int",
        "no_leak_scan": {
          "forbidden_packet_row_hits": [],
          "status": "str"
        },
        "order_calls": "int",
        "outcome_review_opened": "bool",
        "paid_data_calls": "int",
        "promotion_verdict": "str",
        "sample_floor": {
          "countable_rows": "int",
          "packet_row_count": "int",
          "reason": "str",
          "sample_floor_for_validation_met": "bool",
          "unique_duplicate_groups": "int"
        },
        "schema_version": "str",
        "source_contract_inventory_files": "int",
        "status": "str",
        "validation_safe": "bool"
      },
      "size_bytes": 3060,
      "source_hash": "ed387eeaab2aabbf740e8fa3edf6a9a18e5b6c687c28ca9aba8196f822f33d92",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "account_history_accessed",
        "api_calls",
        "artifact_family",
        "blocked_94_not_scored_proof",
        "blocked_packet_outcome_source_read",
        "broker_actual_r_accessed",
        "canary_calls",
        "databento_calls",
        "date_stamp",
        "duplicate_policy",
        "exact_six_row_scope_check",
        "generated_at_utc",
        "live_effect",
        "live_order_state_accessed",
        "live_trade_results_accessed",
        "mt5_account_calls",
        "mt5_order_calls",
        "no_leak_scan",
        "order_calls",
        "outcome_review_opened",
        "paid_data_calls",
        "promotion_verdict",
        "sample_floor",
        "schema_version",
        "source_contract_inventory_files",
        "status",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "c4daa7a51625218cd33e14a91f0117a1e4e04c5015f2f874ffd5b99cebcc77c9",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_next_model_control_pack/CNR_TIMING_TARGET_SOURCE_CONTRACTS_2026-05-08.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_next_model_control_pack/CNR_TIMING_TARGET_SOURCE_CONTRACTS_2026-05-08.json",
      "shape": {
        "account_history_accessed": "bool",
        "allowed_parsers": [
          "str"
        ],
        "allowed_source_roots": [
          "str"
        ],
        "api_calls": "int",
        "artifact_family": "str",
        "blocked_packet_outcome_source_read": "bool",
        "broker_actual_r_accessed": "bool",
        "canary_calls": "int",
        "databento_calls": "int",
        "date_stamp": "str",
        "forbidden_sources": [
          "str"
        ],
        "generated_at_utc": "str",
        "legal_source_state": {
          "E2_E3_E4": "str",
          "T1_T2_T3": "str"
        },
        "lifecycle_packet_status": "str",
        "live_effect": "bool",
        "live_order_state_accessed": "bool",
        "live_trade_results_accessed": "bool",
        "mt5_account_calls": "int",
        "mt5_order_calls": "int",
        "order_calls": "int",
        "outcome_review_opened": "bool",
        "paid_data_calls": "int",
        "promotion_verdict": "str",
        "schema_version": "str",
        "source_artifact_inventory": [
          {
            "directory_role": "str",
            "exists": "bool",
            "parse_status": "str",
            "path": "str",
            "required_directory": "str",
            "sha256": "str",
            "size_bytes": "int"
          }
        ],
        "status": "str",
        "target_family_ids": [
          "str"
        ],
        "timing_family_ids": [
          "str"
        ],
        "validation_safe": "bool"
      },
      "size_bytes": 229593,
      "source_hash": "ff94c2c86c3c76302bf7f4dc15175d8a7832d578a666f9c85c1dbfb144da9c7f",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "account_history_accessed",
        "allowed_parsers",
        "allowed_source_roots",
        "api_calls",
        "artifact_family",
        "blocked_packet_outcome_source_read",
        "broker_actual_r_accessed",
        "canary_calls",
        "databento_calls",
        "date_stamp",
        "forbidden_sources",
        "generated_at_utc",
        "legal_source_state",
        "lifecycle_packet_status",
        "live_effect",
        "live_order_state_accessed",
        "live_trade_results_accessed",
        "mt5_account_calls",
        "mt5_order_calls",
        "order_calls",
        "outcome_review_opened",
        "paid_data_calls",
        "promotion_verdict",
        "schema_version",
        "source_artifact_inventory",
        "status",
        "target_family_ids",
        "timing_family_ids",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "cf6c96542a642243a8cbb401ae33d3123975971d1477f81ca7c5a86958bd75ac",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_ANTI_BOXING_REVIEW_2026-05-07.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_ANTI_BOXING_REVIEW_2026-05-07.json",
      "shape": {
        "account_history_accessed": "bool",
        "anti_boxing_status": "str",
        "api_calls": "int",
        "artifact_family": "str",
        "blocked_packet_outcome_source_read": "bool",
        "broker_actual_r_accessed": "bool",
        "canary_calls": "int",
        "databento_calls": "int",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "live_order_state_accessed": "bool",
        "live_trade_results_accessed": "bool",
        "manual_search_caution": {
          "note": "str",
          "status": "str"
        },
        "mt5_order_calls": "int",
        "order_calls": "int",
        "outcome_review_opened": "bool",
        "paid_data_calls": "int",
        "promotion_verdict": "str",
        "scope_checked": {
          "modalities": [
            "str"
          ],
          "packet_ids": [
            "str"
          ],
          "symbols": [
            "str"
          ],
          "target_families": [
            "str"
          ],
          "timeframes": [
            "str"
          ],
          "timing_families": [
            "str"
          ]
        },
        "searched_roots": [
          {
            "denied_or_walk_errors": [],
            "exists": "bool",
            "max_results": "int",
            "patterns": [
              "str"
            ],
            "result_count_returned": "int",
            "results": [
              "str"
            ],
            "root": "str",
            "search_status": "str",
            "truncated": "bool"
          }
        ],
        "validation_safe": "bool"
      },
      "size_bytes": 105339,
      "source_hash": "08740ba95afca3a6c6c23839ac3a5098d2301f89e320d9282585bf5a30943153",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "account_history_accessed",
        "anti_boxing_status",
        "api_calls",
        "artifact_family",
        "blocked_packet_outcome_source_read",
        "broker_actual_r_accessed",
        "canary_calls",
        "databento_calls",
        "generated_at_utc",
        "live_effect",
        "live_order_state_accessed",
        "live_trade_results_accessed",
        "manual_search_caution",
        "mt5_order_calls",
        "order_calls",
        "outcome_review_opened",
        "paid_data_calls",
        "promotion_verdict",
        "scope_checked",
        "searched_roots",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "cf2513eaa3d404bed273168fe975c8e9449ecad51f9bcd769b222da1231f1ab4",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_CAPTURE_LEDGER_2026-05-07.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_CAPTURE_LEDGER_2026-05-07.json",
      "shape": {
        "account_history_accessed": "bool",
        "api_calls": "int",
        "artifact_family": "str",
        "blocked_packet_outcome_source_read": "bool",
        "broker_actual_r_accessed": "bool",
        "canary_calls": "int",
        "capture_summary": {
          "blocked_rows": "int",
          "packet_blocker_counts": {
            "OTG0-PKT-060": {
              "BLOCKED_WITH_EXACT_SOURCE_FIELD_REQUIREMENTS": "int",
              "READY_INPUT_ONLY_FOR_G12_G0_AUDIT": "int"
            },
            "OTG0-PKT-061": {
              "BLOCKED_WITH_EXACT_SOURCE_FIELD_REQUIREMENTS": "int",
              "READY_INPUT_ONLY_FOR_G12_G0_AUDIT": "int"
            },
            "OTG0-PKT-062": {
              "BLOCKED_WITH_EXACT_SOURCE_FIELD_REQUIREMENTS": "int",
              "READY_INPUT_ONLY_FOR_G12_G0_AUDIT": "int"
            },
            "OTG0-PKT-063": {
              "BLOCKED_WITH_EXACT_SOURCE_FIELD_REQUIREMENTS": "int",
              "READY_INPUT_ONLY_FOR_G12_G0_AUDIT": "int"
            },
            "OTG0-PKT-066": {
              "BLOCKED_WITH_EXACT_SOURCE_FIELD_REQUIREMENTS": "int",
              "READY_INPUT_ONLY_FOR_G12_G0_AUDIT": "int"
            }
          },
          "quote_extracted_rows": "int",
          "ready_input_only_rows": "int",
          "ready_scope_note": "str",
          "row_count": "int",
          "target_status_counts": {
            "CNR_T0_ORIGINAL_TP1": {
              "BOUND_INPUT_ONLY_ORIGINAL_TP1": "int"
            },
            "CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY": {
              "BLOCKED_TARGET_MODEL_NOT_PREBOUND_FOR_THIS_PACKET": "int"
            },
            "CNR_T2_ASOF_STRUCTURAL_LEVEL": {
              "BLOCKED_STRUCTURED_ASOF_LEVEL_SOURCE_NOT_BOUND": "int"
            },
            "CNR_T3_TIMEBOX_TERMINAL": {
              "BLOCKED_TERMINAL_TIMEBOX_POLICY_NOT_BOUND": "int"
            }
          },
          "timing_status_counts": {
            "CNR_E0_DECISION_CLOSE_MARKET": {
              "BLOCKED_NO_SOURCE_HASHED_EXECUTABLE_QUOTE": "int",
              "QUOTE_EXTRACTED_SOURCE_HASHED": "int"
            },
            "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE": {
              "BLOCKED_NO_SOURCE_HASHED_EXECUTABLE_QUOTE": "int",
              "QUOTE_EXTRACTED_SOURCE_HASHED": "int"
            },
            "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK": {
              "BLOCKED_TIMING_TRIGGER_NOT_MATERIALIZED": "int"
            },
            "CNR_E3_LATENCY_BOUNDED_DECISION_WINDOW": {
              "BLOCKED_TIMING_TRIGGER_NOT_MATERIALIZED": "int"
            },
            "CNR_E4_PRETOUCH_CONTINUATION_TRIGGER": {
              "BLOCKED_TIMING_TRIGGER_NOT_MATERIALIZED": "int"
            }
          }
        },
        "databento_calls": "int",
        "exact_remaining_blockers": {
          "latency_clock_chain": "str",
          "pretouch_trigger": "str",
          "quote_gaps": "str",
          "signal_emitted_utc": "str",
          "target_T1_T2_T3_bindings": "str"
        },
        "generated_at_utc": "str",
        "live_effect": "bool",
        "live_order_state_accessed": "bool",
        "live_trade_results_accessed": "bool",
        "mt5_order_calls": "int",
        "order_calls": "int",
        "outcome_review_opened": "bool",
        "paid_data_calls": "int",
        "parser_version": "str",
        "promotion_verdict": "str",
        "source_packet_count": "int",
        "source_record_count": "int",
        "target_families": [
          "str"
        ],
        "timing_families": [
          "str"
        ],
        "validation_safe": "bool"
      },
      "size_bytes": 3959,
      "source_hash": "7801d46b0fe5ac54102e7902d49861c48e1bafe42d0baf450fb07e4c063cd1b8",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "account_history_accessed",
        "api_calls",
        "artifact_family",
        "blocked_packet_outcome_source_read",
        "broker_actual_r_accessed",
        "canary_calls",
        "capture_summary",
        "databento_calls",
        "exact_remaining_blockers",
        "generated_at_utc",
        "live_effect",
        "live_order_state_accessed",
        "live_trade_results_accessed",
        "mt5_order_calls",
        "order_calls",
        "outcome_review_opened",
        "paid_data_calls",
        "parser_version",
        "promotion_verdict",
        "source_packet_count",
        "source_record_count",
        "target_families",
        "timing_families",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "bae2f9f9de5a7ea0fc3625edde16ef1c482b402badd2f4c008401195fe68ad5f",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_COMPLETION_AUDIT_2026-05-07.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_COMPLETION_AUDIT_2026-05-07.json",
      "shape": {
        "account_history_accessed": "bool",
        "api_calls": "int",
        "artifact_family": "str",
        "blocked_packet_outcome_source_read": "bool",
        "broker_actual_r_accessed": "bool",
        "canary_calls": "int",
        "databento_calls": "int",
        "duplicate_summary": {
          "by_packet": {
            "OTG0-PKT-060": {
              "countable_rows": "int",
              "rows": "int",
              "unique_denominator_keys": "int",
              "unique_primary_duplicate_groups": "int"
            },
            "OTG0-PKT-061": {
              "countable_rows": "int",
              "rows": "int",
              "unique_denominator_keys": "int",
              "unique_primary_duplicate_groups": "int"
            },
            "OTG0-PKT-062": {
              "countable_rows": "int",
              "rows": "int",
              "unique_denominator_keys": "int",
              "unique_primary_duplicate_groups": "int"
            },
            "OTG0-PKT-063": {
              "countable_rows": "int",
              "rows": "int",
              "unique_denominator_keys": "int",
              "unique_primary_duplicate_groups": "int"
            },
            "OTG0-PKT-066": {
              "countable_rows": "int",
              "rows": "int",
              "unique_denominator_keys": "int",
              "unique_primary_duplicate_groups": "int"
            }
          },
          "duplicate_context_rows": "int",
          "duplicate_policy": "str",
          "stability_status": "str",
          "total_rows": "int",
          "unique_denominator_keys": "int"
        },
        "forbidden_scan_summary": {
          "forbidden_tokens": [
            "str"
          ],
          "hit_count": "int",
          "hits": [],
          "scan_status": "str",
          "truncated": "bool"
        },
        "generated_at_utc": "str",
        "live_effect": "bool",
        "live_order_state_accessed": "bool",
        "live_trade_results_accessed": "bool",
        "mt5_order_calls": "int",
        "objective_restated": "str",
        "order_calls": "int",
        "outcome_review_opened": "bool",
        "packet_summary": {
          "blocked_rows": "int",
          "packet_blocker_counts": {
            "OTG0-PKT-060": {
              "BLOCKED_WITH_EXACT_SOURCE_FIELD_REQUIREMENTS": "int",
              "READY_INPUT_ONLY_FOR_G12_G0_AUDIT": "int"
            },
            "OTG0-PKT-061": {
              "BLOCKED_WITH_EXACT_SOURCE_FIELD_REQUIREMENTS": "int",
              "READY_INPUT_ONLY_FOR_G12_G0_AUDIT": "int"
            },
            "OTG0-PKT-062": {
              "BLOCKED_WITH_EXACT_SOURCE_FIELD_REQUIREMENTS": "int",
              "READY_INPUT_ONLY_FOR_G12_G0_AUDIT": "int"
            },
            "OTG0-PKT-063": {
              "BLOCKED_WITH_EXACT_SOURCE_FIELD_REQUIREMENTS": "int",
              "READY_INPUT_ONLY_FOR_G12_G0_AUDIT": "int"
            },
            "OTG0-PKT-066": {
              "BLOCKED_WITH_EXACT_SOURCE_FIELD_REQUIREMENTS": "int",
              "READY_INPUT_ONLY_FOR_G12_G0_AUDIT": "int"
            }
          },
          "quote_extracted_rows": "int",
          "ready_input_only_rows": "int",
          "ready_scope_note": "str",
          "row_count": "int",
          "target_status_counts": {
            "CNR_T0_ORIGINAL_TP1": {
              "BOUND_INPUT_ONLY_ORIGINAL_TP1": "int"
            },
            "CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY": {
              "BLOCKED_TARGET_MODEL_NOT_PREBOUND_FOR_THIS_PACKET": "int"
            },
            "CNR_T2_ASOF_STRUCTURAL_LEVEL": {
              "BLOCKED_STRUCTURED_ASOF_LEVEL_SOURCE_NOT_BOUND": "int"
            },
            "CNR_T3_TIMEBOX_TERMINAL": {
              "BLOCKED_TERMINAL_TIMEBOX_POLICY_NOT_BOUND": "int"
            }
          },
          "timing_status_counts": {
            "CNR_E0_DECISION_CLOSE_MARKET": {
              "BLOCKED_NO_SOURCE_HASHED_EXECUTABLE_QUOTE": "int",
              "QUOTE_EXTRACTED_SOURCE_HASHED": "int"
            },
            "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE": {
              "BLOCKED_NO_SOURCE_HASHED_EXECUTABLE_QUOTE": "int",
              "QUOTE_EXTRACTED_SOURCE_HASHED": "int"
            },
            "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK": {
              "BLOCKED_TIMING_TRIGGER_NOT_MATERIALIZED": "int"
            },
            "CNR_E3_LATENCY_BOUNDED_DECISION_WINDOW": {
              "BLOCKED_TIMING_TRIGGER_NOT_MATERIALIZED": "int"
            },
            "CNR_E4_PRETOUCH_CONTINUATION_TRIGGER": {
              "BLOCKED_TIMING_TRIGGER_NOT_MATERIALIZED": "int"
            }
          }
        },
        "paid_data_calls": "int",
        "promotion_verdict": "str",
        "prompt_to_artifact_checklist": [
          {
            "evidence": {
              "branch": "str",
              "git_status_short": "str",
              "head": "str",
              "latest_handoff_read": "str",
              "live_state_regenerated": "bool",
              "research_current_state_fresh_in_live_state": "bool"
            },
            "requirement": "str",
            "status": "str"
          }
        ],
        "sample_floor_summary": {
          "current_unique_primary_duplicate_groups": "int",
          "duplicate_report_ref": "str",
          "expansion_status": "str",
          "ready_unique_primary_duplicate_groups": "int",
          "sample_floor_policy": {
            "aggregate_descriptive": "str",
            "single_packet": "str",
            "validation_dossier": "str"
          },
          "searched_root_count": "int",
          "searched_roots": [
            {
              "denied_or_walk_errors": "list",
              "exists": "bool",
              "result_count_returned": "int",
              "root": "str",
              "search_status": "str",
              "truncated": "bool"
            }
          ],
          "small_n_handling": "str"
        },
        "stop_condition_status": "str",
        "validation_safe": "bool"
      },
      "size_bytes": 13046,
      "source_hash": "a59a47f3ecb50fca426dbb8a828ae76108c0e4f300814f2d4706aa2d9c2e1409",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "account_history_accessed",
        "api_calls",
        "artifact_family",
        "blocked_packet_outcome_source_read",
        "broker_actual_r_accessed",
        "canary_calls",
        "databento_calls",
        "duplicate_summary",
        "forbidden_scan_summary",
        "generated_at_utc",
        "live_effect",
        "live_order_state_accessed",
        "live_trade_results_accessed",
        "mt5_order_calls",
        "objective_restated",
        "order_calls",
        "outcome_review_opened",
        "packet_summary",
        "paid_data_calls",
        "promotion_verdict",
        "prompt_to_artifact_checklist",
        "sample_floor_summary",
        "stop_condition_status",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "62971ee52b93158395210d851d0a2f3815ae740fbdc5b9f0aac097299c464403",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_DATA_EXTRACTION_LEDGER_2026-05-07.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_DATA_EXTRACTION_LEDGER_2026-05-07.json",
      "shape": {
        "account_history_accessed": "bool",
        "api_calls": "int",
        "artifact_family": "str",
        "attempt_count": "int",
        "blocked_packet_outcome_source_read": "bool",
        "broker_actual_r_accessed": "bool",
        "canary_calls": "int",
        "databento_calls": "int",
        "extraction_policy": "str",
        "generated_at_utc": "str",
        "ledger": [
          {
            "date": "str",
            "first_timestamp_utc": "str",
            "last_timestamp_utc": "str",
            "rows": "int",
            "source_path": "str",
            "source_sha256": "str",
            "status": "str",
            "symbol": "str",
            "trigger_utc": "str"
          }
        ],
        "live_effect": "bool",
        "live_order_state_accessed": "bool",
        "live_trade_results_accessed": "bool",
        "local_parquet_sources_read": [
          "str"
        ],
        "mt5_order_calls": "int",
        "new_mt5_copy_ticks_range_calls": "int",
        "order_calls": "int",
        "outcome_review_opened": "bool",
        "paid_data_calls": "int",
        "promotion_verdict": "str",
        "status_counts": {
          "BLOCKED_NO_LOCAL_TICK_PARQUET": "int",
          "NO_QUOTE_AT_OR_BEFORE_TRIGGER_IN_SOURCE": "int",
          "QUOTE_EXTRACTED_SOURCE_HASHED": "int"
        },
        "validation_safe": "bool"
      },
      "size_bytes": 216358,
      "source_hash": "dcf7d34017633ea3a41b18bbabce6ca904b84a07196e5da9be467c5e12388020",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "account_history_accessed",
        "api_calls",
        "artifact_family",
        "attempt_count",
        "blocked_packet_outcome_source_read",
        "broker_actual_r_accessed",
        "canary_calls",
        "databento_calls",
        "extraction_policy",
        "generated_at_utc",
        "ledger",
        "live_effect",
        "live_order_state_accessed",
        "live_trade_results_accessed",
        "local_parquet_sources_read",
        "mt5_order_calls",
        "new_mt5_copy_ticks_range_calls",
        "order_calls",
        "outcome_review_opened",
        "paid_data_calls",
        "promotion_verdict",
        "status_counts",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "9e0ec534277396c922d8d324f63e1d264103333efeae20de04529c1d020e7d18",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_DUPLICATE_DENOMINATOR_REPORT_2026-05-07.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_DUPLICATE_DENOMINATOR_REPORT_2026-05-07.json",
      "shape": {
        "account_history_accessed": "bool",
        "api_calls": "int",
        "artifact_family": "str",
        "blocked_packet_outcome_source_read": "bool",
        "broker_actual_r_accessed": "bool",
        "by_packet": {
          "OTG0-PKT-060": {
            "countable_rows": "int",
            "rows": "int",
            "unique_denominator_keys": "int",
            "unique_primary_duplicate_groups": "int"
          },
          "OTG0-PKT-061": {
            "countable_rows": "int",
            "rows": "int",
            "unique_denominator_keys": "int",
            "unique_primary_duplicate_groups": "int"
          },
          "OTG0-PKT-062": {
            "countable_rows": "int",
            "rows": "int",
            "unique_denominator_keys": "int",
            "unique_primary_duplicate_groups": "int"
          },
          "OTG0-PKT-063": {
            "countable_rows": "int",
            "rows": "int",
            "unique_denominator_keys": "int",
            "unique_primary_duplicate_groups": "int"
          },
          "OTG0-PKT-066": {
            "countable_rows": "int",
            "rows": "int",
            "unique_denominator_keys": "int",
            "unique_primary_duplicate_groups": "int"
          }
        },
        "canary_calls": "int",
        "databento_calls": "int",
        "duplicate_context_rows": "int",
        "duplicate_policy": "str",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "live_order_state_accessed": "bool",
        "live_trade_results_accessed": "bool",
        "mt5_order_calls": "int",
        "order_calls": "int",
        "outcome_review_opened": "bool",
        "paid_data_calls": "int",
        "promotion_verdict": "str",
        "stability_status": "str",
        "total_rows": "int",
        "unique_denominator_keys": "int",
        "validation_safe": "bool"
      },
      "size_bytes": 1723,
      "source_hash": "bcdc81bd3fe9c8f6a85459cc95ed60b31bdf58e256dee780a14480bec17f7975",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "account_history_accessed",
        "api_calls",
        "artifact_family",
        "blocked_packet_outcome_source_read",
        "broker_actual_r_accessed",
        "by_packet",
        "canary_calls",
        "databento_calls",
        "duplicate_context_rows",
        "duplicate_policy",
        "generated_at_utc",
        "live_effect",
        "live_order_state_accessed",
        "live_trade_results_accessed",
        "mt5_order_calls",
        "order_calls",
        "outcome_review_opened",
        "paid_data_calls",
        "promotion_verdict",
        "stability_status",
        "total_rows",
        "unique_denominator_keys",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "00c1806990597650b8190cda6752de2ce73458de4734cffdeaf1a9ba1aff6388",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_MULTITIMEFRAME_EVIDENCE_MAP_2026-05-07.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_MULTITIMEFRAME_EVIDENCE_MAP_2026-05-07.json",
      "shape": {
        "account_history_accessed": "bool",
        "api_calls": "int",
        "artifact_family": "str",
        "blocked_packet_outcome_source_read": "bool",
        "broker_actual_r_accessed": "bool",
        "canary_calls": "int",
        "databento_calls": "int",
        "evidence_status_by_timeframe": {
          "H1": "str",
          "M15": "str",
          "M1_M5_H4_D1": "str",
          "tick_or_quote": {
            "BLOCKED_NO_SOURCE_HASHED_EXECUTABLE_QUOTE": "int",
            "BLOCKED_TIMING_TRIGGER_NOT_MATERIALIZED": "int",
            "QUOTE_EXTRACTED_SOURCE_HASHED": "int"
          }
        },
        "generated_at_utc": "str",
        "live_effect": "bool",
        "live_order_state_accessed": "bool",
        "live_trade_results_accessed": "bool",
        "mt5_order_calls": "int",
        "order_calls": "int",
        "outcome_review_opened": "bool",
        "paid_data_calls": "int",
        "promotion_verdict": "str",
        "timeframe_roles": {
          "D1": "str",
          "H1": "str",
          "H4": "str",
          "M1": "str",
          "M15": "str",
          "M5": "str",
          "session": "str",
          "tick_or_quote": "str"
        },
        "validation_safe": "bool"
      },
      "size_bytes": 1867,
      "source_hash": "bfc78a1adbb0be03db22fd1cf4dbaa8c7b66698aeb15b7083d372d1b60b2737d",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "account_history_accessed",
        "api_calls",
        "artifact_family",
        "blocked_packet_outcome_source_read",
        "broker_actual_r_accessed",
        "canary_calls",
        "databento_calls",
        "evidence_status_by_timeframe",
        "generated_at_utc",
        "live_effect",
        "live_order_state_accessed",
        "live_trade_results_accessed",
        "mt5_order_calls",
        "order_calls",
        "outcome_review_opened",
        "paid_data_calls",
        "promotion_verdict",
        "timeframe_roles",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "22006a2352e1b2ab026d42d06fa8c85f2d568c5efaa1b42bd016bd860da66347",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_NOLEAK_FORBIDDEN_FIELD_SCAN_2026-05-07.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_NOLEAK_FORBIDDEN_FIELD_SCAN_2026-05-07.json",
      "shape": {
        "account_history_accessed": "bool",
        "api_calls": "int",
        "artifact_family": "str",
        "blocked_packet_outcome_source_read": "bool",
        "broker_actual_r_accessed": "bool",
        "canary_calls": "int",
        "databento_calls": "int",
        "forbidden_tokens": [
          "str"
        ],
        "generated_at_utc": "str",
        "hit_count": "int",
        "hits": [],
        "live_effect": "bool",
        "live_order_state_accessed": "bool",
        "live_trade_results_accessed": "bool",
        "mt5_order_calls": "int",
        "order_calls": "int",
        "outcome_review_opened": "bool",
        "paid_data_calls": "int",
        "promotion_verdict": "str",
        "scan_status": "str",
        "truncated": "bool",
        "validation_safe": "bool"
      },
      "size_bytes": 1215,
      "source_hash": "cf166d7abda15cd32686771e395348927cdbbd92ea8fd5b61d4e29a96f65eb6d",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "account_history_accessed",
        "api_calls",
        "artifact_family",
        "blocked_packet_outcome_source_read",
        "broker_actual_r_accessed",
        "canary_calls",
        "databento_calls",
        "forbidden_tokens",
        "generated_at_utc",
        "hit_count",
        "hits",
        "live_effect",
        "live_order_state_accessed",
        "live_trade_results_accessed",
        "mt5_order_calls",
        "order_calls",
        "outcome_review_opened",
        "paid_data_calls",
        "promotion_verdict",
        "scan_status",
        "truncated",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "62b83b5b45f07f6b2ab14fc0e63a036b5525136fdacf2670c4389a1255c52b61",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_PACKET_BUILDER_CONTEXT_ANCHOR_2026-05-07.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_PACKET_BUILDER_CONTEXT_ANCHOR_2026-05-07.json",
      "shape": {
        "account_history_accessed": "bool",
        "active_question_stack": [
          "str"
        ],
        "api_calls": "int",
        "artifact_family": "str",
        "artifact_manifest_ref": "str",
        "blocked_packet_outcome_source_read": "bool",
        "boundaries": {
          "live_trading_surface_touched": "bool",
          "paid_or_api_calls": "bool",
          "result_quarantine_directories_opened_by_builder": "bool",
          "write_scope": "str"
        },
        "broker_actual_r_accessed": "bool",
        "canary_calls": "int",
        "controlling_prompt": "str",
        "databento_calls": "int",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "live_order_state_accessed": "bool",
        "live_trade_results_accessed": "bool",
        "mt5_order_calls": "int",
        "next_resume_step": "str",
        "order_calls": "int",
        "outcome_review_opened": "bool",
        "paid_data_calls": "int",
        "preflight": {
          "branch": "str",
          "git_status_short": "str",
          "head": "str",
          "latest_handoff_read": "str",
          "live_state_regenerated": "bool",
          "research_current_state_fresh_in_live_state": "bool"
        },
        "promotion_verdict": "str",
        "route_decisions": [
          "str"
        ],
        "validation_safe": "bool"
      },
      "size_bytes": 4563,
      "source_hash": "eb8933423147161d226fa4305674e7513fa6f79d46d8761598c7d9117cc4538e",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "account_history_accessed",
        "active_question_stack",
        "api_calls",
        "artifact_family",
        "artifact_manifest_ref",
        "blocked_packet_outcome_source_read",
        "boundaries",
        "broker_actual_r_accessed",
        "canary_calls",
        "controlling_prompt",
        "databento_calls",
        "generated_at_utc",
        "live_effect",
        "live_order_state_accessed",
        "live_trade_results_accessed",
        "mt5_order_calls",
        "next_resume_step",
        "order_calls",
        "outcome_review_opened",
        "paid_data_calls",
        "preflight",
        "promotion_verdict",
        "route_decisions",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "b4e82ca1c8510ccd9bdec37db97cba1a95fbe8485df5e0345382515ff4a88e4c",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_PACKET_MANIFEST_2026-05-07.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_PACKET_MANIFEST_2026-05-07.json",
      "shape": {
        "account_history_accessed": "bool",
        "api_calls": "int",
        "artifact_family": "str",
        "blocked_packet_outcome_source_read": "bool",
        "blocked_rows": "int",
        "broker_actual_r_accessed": "bool",
        "canary_calls": "int",
        "databento_calls": "int",
        "g12_g0_readiness": "str",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "live_order_state_accessed": "bool",
        "live_trade_results_accessed": "bool",
        "mt5_order_calls": "int",
        "order_calls": "int",
        "outcome_review_opened": "bool",
        "packet_row_file": "str",
        "packet_status": "str",
        "paid_data_calls": "int",
        "promotion_verdict": "str",
        "ready_input_only_rows": "int",
        "row_count": "int",
        "schema_version": "str",
        "source_packets": [
          {
            "decision": "str",
            "experiment_id": "str",
            "hypothesis_id": "str",
            "outcome_review_opened": "bool",
            "packet_id": "str",
            "packet_path": "str",
            "packet_sha256": "str",
            "promotion_verdict": "str",
            "record_count": "int",
            "unique_duplicate_group_count": "int",
            "validation_safe": "bool"
          }
        ],
        "validation_safe": "bool"
      },
      "size_bytes": 4717,
      "source_hash": "bfe31c2fb87a19b0139431e0eed5cb1926afffe6986ab395f56cf6e3d2c3b6e3",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "account_history_accessed",
        "api_calls",
        "artifact_family",
        "blocked_packet_outcome_source_read",
        "blocked_rows",
        "broker_actual_r_accessed",
        "canary_calls",
        "databento_calls",
        "g12_g0_readiness",
        "generated_at_utc",
        "live_effect",
        "live_order_state_accessed",
        "live_trade_results_accessed",
        "mt5_order_calls",
        "order_calls",
        "outcome_review_opened",
        "packet_row_file",
        "packet_status",
        "paid_data_calls",
        "promotion_verdict",
        "ready_input_only_rows",
        "row_count",
        "schema_version",
        "source_packets",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "af0ebe0258a55be116ad78ba97954e6e7beda8820c9e87af1099c05aa54c1085",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_SAMPLE_FLOOR_AND_EXPANSION_REPORT_2026-05-07.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_SAMPLE_FLOOR_AND_EXPANSION_REPORT_2026-05-07.json",
      "shape": {
        "account_history_accessed": "bool",
        "api_calls": "int",
        "artifact_family": "str",
        "blocked_packet_outcome_source_read": "bool",
        "broker_actual_r_accessed": "bool",
        "canary_calls": "int",
        "current_unique_primary_duplicate_groups": "int",
        "databento_calls": "int",
        "duplicate_report_ref": "str",
        "expansion_status": "str",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "live_order_state_accessed": "bool",
        "live_trade_results_accessed": "bool",
        "mt5_order_calls": "int",
        "order_calls": "int",
        "outcome_review_opened": "bool",
        "paid_data_calls": "int",
        "promotion_verdict": "str",
        "ready_unique_primary_duplicate_groups": "int",
        "sample_floor_policy": {
          "aggregate_descriptive": "str",
          "single_packet": "str",
          "validation_dossier": "str"
        },
        "searched_root_count": "int",
        "searched_roots": [
          {
            "denied_or_walk_errors": [],
            "exists": "bool",
            "result_count_returned": "int",
            "root": "str",
            "search_status": "str",
            "truncated": "bool"
          }
        ],
        "small_n_handling": "str",
        "validation_safe": "bool"
      },
      "size_bytes": 3693,
      "source_hash": "70608a18c3f0837f070787e792cd1b71042c1618b8327eecf738f56c2384094c",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "account_history_accessed",
        "api_calls",
        "artifact_family",
        "blocked_packet_outcome_source_read",
        "broker_actual_r_accessed",
        "canary_calls",
        "current_unique_primary_duplicate_groups",
        "databento_calls",
        "duplicate_report_ref",
        "expansion_status",
        "generated_at_utc",
        "live_effect",
        "live_order_state_accessed",
        "live_trade_results_accessed",
        "mt5_order_calls",
        "order_calls",
        "outcome_review_opened",
        "paid_data_calls",
        "promotion_verdict",
        "ready_unique_primary_duplicate_groups",
        "sample_floor_policy",
        "searched_root_count",
        "searched_roots",
        "small_n_handling",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "9383e02c75fca2cc2dde3ecce20c01016b6f847c7bda3cbcefa58f8ff9509917",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_SOURCE_HASH_MANIFEST_2026-05-07.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_SOURCE_HASH_MANIFEST_2026-05-07.json",
      "shape": {
        "account_history_accessed": "bool",
        "all_consumed_files_hashed": "bool",
        "all_required_control_inputs_exist": "bool",
        "api_calls": "int",
        "artifact_family": "str",
        "blocked_packet_outcome_source_read": "bool",
        "broker_actual_r_accessed": "bool",
        "canary_calls": "int",
        "databento_calls": "int",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "live_order_state_accessed": "bool",
        "live_trade_results_accessed": "bool",
        "mt5_order_calls": "int",
        "order_calls": "int",
        "outcome_review_opened": "bool",
        "paid_data_calls": "int",
        "parser_version": "str",
        "promotion_verdict": "str",
        "source_files": [
          {
            "absolute_path": "str",
            "exists": "bool",
            "path": "str",
            "required": "bool",
            "role": "str",
            "sha256": "str",
            "sha256_status": "str",
            "size_bytes": "int",
            "strict_hash_reverification": "bool"
          }
        ],
        "validation_safe": "bool"
      },
      "size_bytes": 32284,
      "source_hash": "2e4b7219a8cb0a6636421e284bb397d02fcc7fff380f8fabae58c9aed8f1bf8c",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "account_history_accessed",
        "all_consumed_files_hashed",
        "all_required_control_inputs_exist",
        "api_calls",
        "artifact_family",
        "blocked_packet_outcome_source_read",
        "broker_actual_r_accessed",
        "canary_calls",
        "databento_calls",
        "generated_at_utc",
        "live_effect",
        "live_order_state_accessed",
        "live_trade_results_accessed",
        "mt5_order_calls",
        "order_calls",
        "outcome_review_opened",
        "paid_data_calls",
        "parser_version",
        "promotion_verdict",
        "source_files",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "21ea386b82e721134dda35f000ed0bc0afbb511cd5d2d0ad9e6d82f8d06302dd",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_VERIFICATION_RESULTS_2026-05-07.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_VERIFICATION_RESULTS_2026-05-07.json",
      "shape": {
        "account_history_accessed": "bool",
        "api_calls": "int",
        "artifact_family": "str",
        "blocked_packet_outcome_source_read": "bool",
        "broker_actual_r_accessed": "bool",
        "commands": [
          {
            "command": "str",
            "status": "str"
          }
        ],
        "databento_calls": "int",
        "environment_warnings": [
          {
            "impact": "str",
            "path": "str",
            "status": "str"
          }
        ],
        "generated_at_utc": "str",
        "live_effect": "bool",
        "live_order_state_accessed": "bool",
        "live_trade_results_accessed": "bool",
        "mt5_order_calls": "int",
        "order_calls": "int",
        "outcome_review_opened": "bool",
        "paid_data_calls": "int",
        "promotion_verdict": "str",
        "validation_safe": "bool",
        "verification_status": "str"
      },
      "size_bytes": 2339,
      "source_hash": "1269472592e759502e2641b946778383a7d2bd3239ff4daf16d6ae24f8985ae6",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "account_history_accessed",
        "api_calls",
        "artifact_family",
        "blocked_packet_outcome_source_read",
        "broker_actual_r_accessed",
        "commands",
        "databento_calls",
        "environment_warnings",
        "generated_at_utc",
        "live_effect",
        "live_order_state_accessed",
        "live_trade_results_accessed",
        "mt5_order_calls",
        "order_calls",
        "outcome_review_opened",
        "paid_data_calls",
        "promotion_verdict",
        "validation_safe",
        "verification_status"
      ]
    },
    {
      "key_shape_fingerprint": "9b349fc732f0b576eec4984392f9d4fde7c4f6e294b69ae04223315746afa3b4",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_t3_lifecycle_expansion_source_packet/CNR_T3_BLOCKER_AND_IMPOSSIBILITY_LEDGER_2026-05-08.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_t3_lifecycle_expansion_source_packet/CNR_T3_BLOCKER_AND_IMPOSSIBILITY_LEDGER_2026-05-08.json",
      "shape": {
        "all_candidates_packetized_or_blocked": "bool",
        "artifact_family": "str",
        "blocker_count": "int",
        "blocker_label_counts": {
          "not_packet_eligible": "int"
        },
        "candidate_count": "int",
        "exact_blockers": [
          {
            "exact_blocker": "str",
            "inventory_id": "str",
            "lifecycle_label": "str",
            "packet_id": "str",
            "reasoning": "str",
            "row_id": "str",
            "searched_extended_tick_path": "bool",
            "source_lane": "str"
          }
        ],
        "generated_at_utc": "str",
        "global_blockers_for_future_routes": [
          {
            "exact_blocker": "str",
            "route": "str",
            "status": "str"
          }
        ],
        "live_effect": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "schema_version": "str",
        "validation_safe": "bool"
      },
      "size_bytes": 170165,
      "source_hash": "1f6e7ead32dba5fe5a40bcceffe8c733316e8b0b9ea3ef23f045eeb42e92c25e",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "all_candidates_packetized_or_blocked",
        "artifact_family",
        "blocker_count",
        "blocker_label_counts",
        "candidate_count",
        "exact_blockers",
        "generated_at_utc",
        "global_blockers_for_future_routes",
        "live_effect",
        "outcome_review_opened",
        "promotion_verdict",
        "schema_version",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "6bdbed84563f1345d336e13f443e1ee972f9dc14674cb99c874e046b3478776b",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_t3_lifecycle_expansion_source_packet/CNR_T3_COMPLETION_AUDIT_2026-05-08.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_t3_lifecycle_expansion_source_packet/CNR_T3_COMPLETION_AUDIT_2026-05-08.json",
      "shape": {
        "artifact_family": "str",
        "external_command_results": [
          {
            "command": "str",
            "note": "str",
            "result": "str"
          }
        ],
        "external_commands_to_run_after_build": [
          "str"
        ],
        "final_live_state_sha256": "str",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "objective_restatement": "str",
        "outcome_review_opened": "bool",
        "output_files_expected": [
          "str"
        ],
        "packet_summary": {
          "blocker_count": "int",
          "candidate_count": "int",
          "label_counts": {
            "stop_after_original_horizon": "int"
          },
          "learning_summary": {
            "ambiguous_target_stop_after_original_horizon": "int",
            "not_packet_eligible": "int",
            "source_horizon_insufficient": "int",
            "still_no_terminal_after_extended_horizon": "int",
            "stop_after_original_horizon": "int",
            "target_after_original_horizon": "int"
          },
          "packet_rows": "int"
        },
        "promotion_verdict": "str",
        "prompt_to_artifact_checklist": [
          {
            "evidence": "str",
            "requirement": "str",
            "status": "str"
          }
        ],
        "schema_version": "str",
        "static_completion_status": "str",
        "validation_safe": "bool"
      },
      "size_bytes": 7947,
      "source_hash": "de1ee0c89999e5daefc166fe0140be495f013c8ed42da8239b605dbd33a6ca16",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "artifact_family",
        "external_command_results",
        "external_commands_to_run_after_build",
        "final_live_state_sha256",
        "generated_at_utc",
        "live_effect",
        "objective_restatement",
        "outcome_review_opened",
        "output_files_expected",
        "packet_summary",
        "promotion_verdict",
        "prompt_to_artifact_checklist",
        "schema_version",
        "static_completion_status",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "0fd0046f58a8628c36b7d96575e0072750cc55546665a1a2e38ff3ef8c56a284",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_t3_lifecycle_expansion_source_packet/CNR_T3_FROZEN_LIFECYCLE_CONTRACT_2026-05-08.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_t3_lifecycle_expansion_source_packet/CNR_T3_FROZEN_LIFECYCLE_CONTRACT_2026-05-08.json",
      "shape": {
        "allowed_labels": [
          "str"
        ],
        "artifact_family": "str",
        "blocked_row_exclusion_rule": "str",
        "contract_id": "str",
        "contract_sha256": "str",
        "date_stamp": "str",
        "duplicate_denominator_policy": "str",
        "extended_horizon_cap_rule": "str",
        "extension_interval_rule": "str",
        "forbidden_fields": [
          "str"
        ],
        "freeze_order": "str",
        "live_effect": "bool",
        "no_leak_field_allowlist": [
          "str"
        ],
        "no_r_performance_rule": "str",
        "original_horizon_source_rule": "str",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "quote_side_terminal_rule_by_side": {
          "LONG": "str",
          "SHORT": "str"
        },
        "row_eligibility_rules": [
          "str"
        ],
        "schema_version": "str",
        "source_hash_requirements": [
          "str"
        ],
        "validation_safe": "bool"
      },
      "size_bytes": 3894,
      "source_hash": "41802e5ac8eca2ea83e8f67576400f79d9ec5fbecd345df2d302dbd5d4d76beb",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "allowed_labels",
        "artifact_family",
        "blocked_row_exclusion_rule",
        "contract_id",
        "contract_sha256",
        "date_stamp",
        "duplicate_denominator_policy",
        "extended_horizon_cap_rule",
        "extension_interval_rule",
        "forbidden_fields",
        "freeze_order",
        "live_effect",
        "no_leak_field_allowlist",
        "no_r_performance_rule",
        "original_horizon_source_rule",
        "outcome_review_opened",
        "promotion_verdict",
        "quote_side_terminal_rule_by_side",
        "row_eligibility_rules",
        "schema_version",
        "source_hash_requirements",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "9693d91acdf5f340f246658caa572296dddd0dea55096dd1188c956a5e980b2d",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_t3_lifecycle_expansion_source_packet/CNR_T3_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_t3_lifecycle_expansion_source_packet/CNR_T3_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json",
      "shape": {
        "allowed_label_status": "str",
        "artifact_family": "str",
        "blocked_94_exclusion": {
          "blocked_audit_status": "str",
          "blocked_overlap_with_accepted": [],
          "blocked_rows": "int",
          "note": "str",
          "packet_hashes_from_accepted_manifest": [
            "str"
          ],
          "packet_rows_from_blocked_set": [],
          "status": "str"
        },
        "blocked_94_status": "str",
        "candidate_count": "int",
        "countable_denominator_rows": "int",
        "duplicate_denominator_key_counts": {
          "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222|CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1": "int",
          "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222|CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1": "int"
        },
        "duplicate_group_counts": {
          "G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222": "int"
        },
        "forbidden_packet_row_key_hits": {},
        "forbidden_packet_row_key_status": "str",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "no_r_performance_computed": "bool",
        "outcome_review_opened": "bool",
        "packet_row_count": "int",
        "packetized_or_blocked_count": "int",
        "promotion_verdict": "str",
        "sample_floor_for_validation_met": "bool",
        "sample_floor_reason": "str",
        "schema_version": "str",
        "unique_duplicate_groups": "int",
        "validation_safe": "bool"
      },
      "size_bytes": 2140,
      "source_hash": "4d48113920e83d93a4a536f2ddf985ad098c0d67a3b15eb4f14d5086d5c5eb15",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "allowed_label_status",
        "artifact_family",
        "blocked_94_exclusion",
        "blocked_94_status",
        "candidate_count",
        "countable_denominator_rows",
        "duplicate_denominator_key_counts",
        "duplicate_group_counts",
        "forbidden_packet_row_key_hits",
        "forbidden_packet_row_key_status",
        "generated_at_utc",
        "live_effect",
        "no_r_performance_computed",
        "outcome_review_opened",
        "packet_row_count",
        "packetized_or_blocked_count",
        "promotion_verdict",
        "sample_floor_for_validation_met",
        "sample_floor_reason",
        "schema_version",
        "unique_duplicate_groups",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "6efa2429e8240392a35b7e88b11d5592d00bd8407aef2c6fccc3fa5de74b6c03",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_t3_lifecycle_expansion_source_packet/CNR_T3_SEARCHED_ROOT_AND_SOURCE_HASH_LEDGER_2026-05-08.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_t3_lifecycle_expansion_source_packet/CNR_T3_SEARCHED_ROOT_AND_SOURCE_HASH_LEDGER_2026-05-08.json",
      "shape": {
        "artifact_family": "str",
        "consumed_tick_file_hashes": [
          {
            "date": "str",
            "path": "str",
            "sha256": "str",
            "size_bytes": "int",
            "symbol": "str"
          }
        ],
        "date_stamp": "str",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "outcome_review_opened": "bool",
        "per_candidate_tick_search_entries": [
          {
            "date": "str",
            "exists": "bool",
            "path": "str",
            "root": "str",
            "symbol": "str"
          }
        ],
        "promotion_verdict": "str",
        "schema_version": "str",
        "searched_roots": [
          {
            "exists": "bool",
            "role": "str",
            "root": "str"
          }
        ],
        "upstream_artifact_hashes": [
          {
            "exists": "bool",
            "path": "str",
            "role": "str",
            "sha256": "str",
            "size_bytes": "int"
          }
        ],
        "validation_safe": "bool"
      },
      "size_bytes": 18634,
      "source_hash": "b5a9df7abbce14159ee2fc896cae1a923b06493d9d54e7600b788bff88e84377",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "artifact_family",
        "consumed_tick_file_hashes",
        "date_stamp",
        "generated_at_utc",
        "live_effect",
        "outcome_review_opened",
        "per_candidate_tick_search_entries",
        "promotion_verdict",
        "schema_version",
        "searched_roots",
        "upstream_artifact_hashes",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "1d498d134fcc80b70696efc24efb5b70d7131ccd12ce1bf1a19a94513186b360",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_timing_model_preregistration/CNR_TIMING_MODEL_BLOCKER_AND_SAMPLE_FLOOR_LEDGER_2026-05-07.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_timing_model_preregistration/CNR_TIMING_MODEL_BLOCKER_AND_SAMPLE_FLOOR_LEDGER_2026-05-07.json",
      "shape": {
        "account_history_accessed": "bool",
        "api_calls": "int",
        "artifact_family": "str",
        "blocked_packet_outcome_source_read": "bool",
        "blockers": [
          {
            "blocker_id": "str",
            "exact_requirement": "str",
            "status": "str"
          }
        ],
        "broker_actual_r_accessed": "bool",
        "canary_calls": "int",
        "databento_calls": "int",
        "date_stamp": "str",
        "generated_at_utc": "str",
        "git_branch_at_build": "str",
        "git_head_at_build": "str",
        "lane_id": "str",
        "ledger_verdict": "str",
        "live_effect": "bool",
        "live_order_state_accessed": "bool",
        "live_trade_results_accessed": "bool",
        "mt5_order_calls": "int",
        "order_calls": "int",
        "outcome_review_opened": "bool",
        "packet_id": "str",
        "paid_data_calls": "int",
        "promotion_verdict": "str",
        "statistical_handling": {
          "dsr_pbo_effective_n": "str",
          "n_20_to_29": "str",
          "n_at_least_30": "str",
          "n_less_than_20": "str",
          "validation_floor": "str"
        },
        "target_record_id": "str",
        "validation_safe": "bool"
      },
      "size_bytes": 3112,
      "source_hash": "9e115801a49ae5aa4dcb843f968c77dad32e3e8a0605f854a77bf86c66779fb3",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "account_history_accessed",
        "api_calls",
        "artifact_family",
        "blocked_packet_outcome_source_read",
        "blockers",
        "broker_actual_r_accessed",
        "canary_calls",
        "databento_calls",
        "date_stamp",
        "generated_at_utc",
        "git_branch_at_build",
        "git_head_at_build",
        "lane_id",
        "ledger_verdict",
        "live_effect",
        "live_order_state_accessed",
        "live_trade_results_accessed",
        "mt5_order_calls",
        "order_calls",
        "outcome_review_opened",
        "packet_id",
        "paid_data_calls",
        "promotion_verdict",
        "statistical_handling",
        "target_record_id",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "6189f2fd9e30fc184427433bb0bb19b07db9c6536c3594e051c593ed57129da2",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_timing_model_preregistration/CNR_TIMING_MODEL_COMPLETION_AUDIT_2026-05-07.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_timing_model_preregistration/CNR_TIMING_MODEL_COMPLETION_AUDIT_2026-05-07.json",
      "shape": {
        "account_history_accessed": "bool",
        "api_calls": "int",
        "artifact_family": "str",
        "blocked_packet_outcome_source_read": "bool",
        "broker_actual_r_accessed": "bool",
        "canary_calls": "int",
        "completion_verdict": "str",
        "databento_calls": "int",
        "date_stamp": "str",
        "generated_at_utc": "str",
        "git_branch_at_build": "str",
        "git_head_at_build": "str",
        "lane_id": "str",
        "live_effect": "bool",
        "live_order_state_accessed": "bool",
        "live_trade_results_accessed": "bool",
        "mt5_order_calls": "int",
        "objective_restatement": "str",
        "order_calls": "int",
        "outcome_review_opened": "bool",
        "packet_id": "str",
        "paid_data_calls": "int",
        "preflight_evidence": {
          "branch": "str",
          "dirty_files_at_builder_run": "str",
          "head": "str",
          "live_state_freshness": {
            "current_state_captured_commit": "str",
            "exists": "bool",
            "latest_research_relevant_commit": "str",
            "path": "str",
            "research_context_status": "str"
          }
        },
        "promotion_verdict": "str",
        "prompt_to_artifact_checklist": [
          {
            "evidence": "str",
            "requirement": "str",
            "status": "str"
          }
        ],
        "required_artifacts": [
          {
            "json": "str",
            "md": "str"
          }
        ],
        "success_criteria": [
          "str"
        ],
        "target_record_id": "str",
        "validation_safe": "bool",
        "verification_evidence": {
          "focused_pytest": {
            "args": [
              "str"
            ],
            "returncode": "int",
            "status": "str",
            "stderr_tail": "str",
            "stdout_tail": "str"
          },
          "forbidden_true_scan": "str",
          "json_parse_count": "int",
          "missing_files": [],
          "no_forbidden_live_surface_diff": "bool",
          "no_result_or_quarantine_output_dir": "bool",
          "py_compile": {
            "args": [
              "str"
            ],
            "returncode": "int",
            "status": "str",
            "stderr_tail": "str",
            "stdout_tail": "str"
          },
          "status": "str",
          "verification_results_artifact": "str"
        }
      },
      "size_bytes": 16828,
      "source_hash": "482940194047219f586cf518b5cccd6817c79a75f53386c886651b77fa946c57",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "account_history_accessed",
        "api_calls",
        "artifact_family",
        "blocked_packet_outcome_source_read",
        "broker_actual_r_accessed",
        "canary_calls",
        "completion_verdict",
        "databento_calls",
        "date_stamp",
        "generated_at_utc",
        "git_branch_at_build",
        "git_head_at_build",
        "lane_id",
        "live_effect",
        "live_order_state_accessed",
        "live_trade_results_accessed",
        "mt5_order_calls",
        "objective_restatement",
        "order_calls",
        "outcome_review_opened",
        "packet_id",
        "paid_data_calls",
        "preflight_evidence",
        "promotion_verdict",
        "prompt_to_artifact_checklist",
        "required_artifacts",
        "success_criteria",
        "target_record_id",
        "validation_safe",
        "verification_evidence"
      ]
    },
    {
      "key_shape_fingerprint": "8ed0fbd774ba568e718cce13ffd31dc4a932665b95e23b9e8b1da4595aa20674",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_timing_model_preregistration/CNR_TIMING_MODEL_RECURSIVE_AMBIGUITY_LEDGER_2026-05-07.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_timing_model_preregistration/CNR_TIMING_MODEL_RECURSIVE_AMBIGUITY_LEDGER_2026-05-07.json",
      "shape": {
        "account_history_accessed": "bool",
        "api_calls": "int",
        "artifact_family": "str",
        "blocked_packet_outcome_source_read": "bool",
        "broker_actual_r_accessed": "bool",
        "canary_calls": "int",
        "databento_calls": "int",
        "date_stamp": "str",
        "generated_at_utc": "str",
        "git_branch_at_build": "str",
        "git_head_at_build": "str",
        "lane_id": "str",
        "ledger_verdict": "str",
        "live_effect": "bool",
        "live_order_state_accessed": "bool",
        "live_trade_results_accessed": "bool",
        "mt5_order_calls": "int",
        "order_calls": "int",
        "outcome_review_opened": "bool",
        "packet_id": "str",
        "paid_data_calls": "int",
        "promotion_verdict": "str",
        "question_stack": [
          {
            "answer": "str",
            "question": "str",
            "status": "str"
          }
        ],
        "target_record_id": "str",
        "validation_safe": "bool"
      },
      "size_bytes": 3035,
      "source_hash": "23a2ddc94cb0f6290f5c0104d1384385151a445978a083a1f470ea9462eaa558",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "account_history_accessed",
        "api_calls",
        "artifact_family",
        "blocked_packet_outcome_source_read",
        "broker_actual_r_accessed",
        "canary_calls",
        "databento_calls",
        "date_stamp",
        "generated_at_utc",
        "git_branch_at_build",
        "git_head_at_build",
        "lane_id",
        "ledger_verdict",
        "live_effect",
        "live_order_state_accessed",
        "live_trade_results_accessed",
        "mt5_order_calls",
        "order_calls",
        "outcome_review_opened",
        "packet_id",
        "paid_data_calls",
        "promotion_verdict",
        "question_stack",
        "target_record_id",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "c06fca7f82594f3b4c634dce74cfc8337ef6971858fa6ab5e06429257ae946ec",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_timing_model_preregistration/CNR_TIMING_MODEL_SOURCE_FIELD_CONTRACT_2026-05-07.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_timing_model_preregistration/CNR_TIMING_MODEL_SOURCE_FIELD_CONTRACT_2026-05-07.json",
      "shape": {
        "account_history_accessed": "bool",
        "api_calls": "int",
        "artifact_family": "str",
        "blocked_packet_outcome_source_read": "bool",
        "broker_actual_r_accessed": "bool",
        "canary_calls": "int",
        "databento_calls": "int",
        "date_stamp": "str",
        "field_contract_verdict": "str",
        "forbidden_fields": [
          "str"
        ],
        "generated_at_utc": "str",
        "git_branch_at_build": "str",
        "git_head_at_build": "str",
        "lane_id": "str",
        "live_effect": "bool",
        "live_order_state_accessed": "bool",
        "live_trade_results_accessed": "bool",
        "mt5_order_calls": "int",
        "order_calls": "int",
        "outcome_review_opened": "bool",
        "packet_id": "str",
        "paid_data_calls": "int",
        "promotion_verdict": "str",
        "quote_side_rule": {
          "LONG": "str",
          "SHORT": "str"
        },
        "required_fields_by_layer": {
          "audit": [
            "str"
          ],
          "context": [
            "str"
          ],
          "executable_quote": [
            "str"
          ],
          "geometry": [
            "str"
          ],
          "identity": [
            "str"
          ],
          "timing": [
            "str"
          ]
        },
        "source_inventory": {
          "account_history_accessed": "bool",
          "all_required_control_inputs_exist": "bool",
          "all_required_control_inputs_hashed": "bool",
          "api_calls": "int",
          "artifact_family": "str",
          "blocked_packet_outcome_source_read": "bool",
          "broker_actual_r_accessed": "bool",
          "canary_calls": "int",
          "control_input_rows": [
            {
              "absolute_path": "str",
              "exists": "bool",
              "last_write_time_utc": "str",
              "path": "str",
              "required": "bool",
              "role": "str",
              "sha256": "str",
              "sha256_status": "str",
              "size_bytes": "int"
            }
          ],
          "databento_calls": "int",
          "date_stamp": "str",
          "generated_at_utc": "str",
          "git_branch_at_build": "str",
          "git_head_at_build": "str",
          "lane_id": "str",
          "live_effect": "bool",
          "live_order_state_accessed": "bool",
          "live_trade_results_accessed": "bool",
          "local_heavy_data_searches": [
            {
              "denied_or_walk_errors": "list",
              "exists": "bool",
              "max_results": "int",
              "patterns": "list",
              "result_count_returned": "int",
              "results": "list",
              "root": "str",
              "search_status": "str",
              "truncated": "bool"
            }
          ],
          "mt5_order_calls": "int",
          "order_calls": "int",
          "outcome_review_opened": "bool",
          "packet_id": "str",
          "paid_data_calls": "int",
          "promotion_verdict": "str",
          "source_inventory_verdict": "str",
          "target_record_id": "str",
          "validation_safe": "bool"
        },
        "target_record_id": "str",
        "validation_safe": "bool"
      },
      "size_bytes": 95063,
      "source_hash": "50a83c4a3bf9a921205faf6717d706fc3cb1bf9145d088b82a6997109b0db83a",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "account_history_accessed",
        "api_calls",
        "artifact_family",
        "blocked_packet_outcome_source_read",
        "broker_actual_r_accessed",
        "canary_calls",
        "databento_calls",
        "date_stamp",
        "field_contract_verdict",
        "forbidden_fields",
        "generated_at_utc",
        "git_branch_at_build",
        "git_head_at_build",
        "lane_id",
        "live_effect",
        "live_order_state_accessed",
        "live_trade_results_accessed",
        "mt5_order_calls",
        "order_calls",
        "outcome_review_opened",
        "packet_id",
        "paid_data_calls",
        "promotion_verdict",
        "quote_side_rule",
        "required_fields_by_layer",
        "source_inventory",
        "target_record_id",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "8ac8d2532528b5b150ae9dc90e6fdd1bb078fb3cf86af0f06edd3b9b82380e79",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/cnr_timing_model_preregistration/CNR_TIMING_MODEL_VERIFICATION_RESULTS_2026-05-07.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/cnr_timing_model_preregistration/CNR_TIMING_MODEL_VERIFICATION_RESULTS_2026-05-07.json",
      "shape": {
        "artifact_family": "str",
        "date_stamp": "str",
        "forbidden_diff_files": [],
        "forbidden_output_dirs": [],
        "forbidden_true_hits": [],
        "generated_at_utc": "str",
        "git_branch_at_verify": "str",
        "git_head_at_verify": "str",
        "issues": [],
        "live_effect": "bool",
        "missing_files": [],
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "py_compile": {
          "args": [
            "str"
          ],
          "returncode": "int",
          "status": "str",
          "stderr_tail": "str",
          "stdout_tail": "str"
        },
        "pytest": {
          "args": [
            "str"
          ],
          "returncode": "int",
          "status": "str",
          "stderr_tail": "str",
          "stdout_tail": "str"
        },
        "required_json_count": "int",
        "status": "str",
        "validation_safe": "bool"
      },
      "size_bytes": 1896,
      "source_hash": "2b91d08aa5e832fdd17b258a9d387bbd85f0bd95b7ddc2328be2983c49349ad4",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "artifact_family",
        "date_stamp",
        "forbidden_diff_files",
        "forbidden_output_dirs",
        "forbidden_true_hits",
        "generated_at_utc",
        "git_branch_at_verify",
        "git_head_at_verify",
        "issues",
        "live_effect",
        "missing_files",
        "outcome_review_opened",
        "promotion_verdict",
        "py_compile",
        "pytest",
        "required_json_count",
        "status",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "f821eafc2f262ede279bce82ff052d82a94f4156e78ab91a827d5dc407b34d20",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SCID_FREEZE_REPAIR_COMPLETION_AUDIT_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SCID_FREEZE_REPAIR_COMPLETION_AUDIT_2026-05-11.json",
      "shape": {
        "artifact_family": "str",
        "can_mark_goal_complete_after_verifier_tests_commit_and_context_refresh": "bool",
        "changes_live_trading_behavior": "bool",
        "completion_standard_satisfied": "bool",
        "credentials_touched": "bool",
        "evidence_class": "str",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "objective_restatement": "str",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "prompt_to_artifact_checklist": [
          {
            "artifact": "str",
            "requirement": "str",
            "status": "str"
          }
        ],
        "remaining_blockers": [],
        "route_id": "str",
        "schema_version": "str",
        "summary": {
          "completion_standard_satisfied": "bool",
          "remaining_blocker_count": "int",
          "repaired_source_count": "int"
        },
        "validation_safe": "bool"
      },
      "size_bytes": 5215,
      "source_hash": "b498ffc53d2994cde41b9ae0aefd2c5913640040a56ff97cf07c6cf6be6bc36e",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "artifact_family",
        "can_mark_goal_complete_after_verifier_tests_commit_and_context_refresh",
        "changes_live_trading_behavior",
        "completion_standard_satisfied",
        "credentials_touched",
        "evidence_class",
        "generated_at_utc",
        "live_effect",
        "objective_restatement",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "prompt_to_artifact_checklist",
        "remaining_blockers",
        "route_id",
        "schema_version",
        "summary",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "de59770744ae1cc474994c1c47bf9d413ce03b32d3562833d6d5c39203a02840",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SCID_FREEZE_REPAIR_DUPLICATE_EXCLUSION_AUDIT_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SCID_FREEZE_REPAIR_DUPLICATE_EXCLUSION_AUDIT_2026-05-11.json",
      "shape": {
        "accepted_fpb_path_label_rows_remain_excluded": "int",
        "all_four_baselines_preserved": "bool",
        "artifact_family": "str",
        "baseline_controls_present": [
          "str"
        ],
        "changes_live_trading_behavior": "bool",
        "checks": {
          "all_four_baselines_preserved": "bool",
          "g0_selected_source_count_is_365": "bool",
          "no_duplicate_segment_hashes": "bool",
          "no_selected_segment_hash_overlap": "bool",
          "partition_assignment_preserved": "bool",
          "selected_source_count_is_365": "bool"
        },
        "credentials_touched": "bool",
        "duplicate_decision": "str",
        "duplicate_segment_hashes": [],
        "evidence_class": "str",
        "expected_baselines": [
          "str"
        ],
        "g0_selected_source_count": "int",
        "g0_selected_source_hash_count": "int",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "partition_assignment_preserved": "bool",
        "promotion_verdict": "str",
        "repair_partition_assignment": "str",
        "route_id": "str",
        "schema_version": "str",
        "selected_segment_hash_overlap": [],
        "selected_source_coverage_row_count": "int",
        "selected_source_hash_count": "int",
        "selected_source_rows_preserved": "int",
        "summary": {
          "all_four_baselines_preserved": "bool",
          "duplicate_decision": "str",
          "selected_source_rows_preserved": "int"
        },
        "validation_safe": "bool"
      },
      "size_bytes": 2408,
      "source_hash": "0cd87678bf8dfa080bbb6e3415695997a3940a5082c993644ab9fb3a06ea43a6",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "accepted_fpb_path_label_rows_remain_excluded",
        "all_four_baselines_preserved",
        "artifact_family",
        "baseline_controls_present",
        "changes_live_trading_behavior",
        "checks",
        "credentials_touched",
        "duplicate_decision",
        "duplicate_segment_hashes",
        "evidence_class",
        "expected_baselines",
        "g0_selected_source_count",
        "g0_selected_source_hash_count",
        "generated_at_utc",
        "live_effect",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "partition_assignment_preserved",
        "promotion_verdict",
        "repair_partition_assignment",
        "route_id",
        "schema_version",
        "selected_segment_hash_overlap",
        "selected_source_coverage_row_count",
        "selected_source_hash_count",
        "selected_source_rows_preserved",
        "summary",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "a947553298d19608874842f1775e80080556d318087355cf2028d22c7a9715e1",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SCID_FREEZE_REPAIR_HARDENING_LEDGER_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SCID_FREEZE_REPAIR_HARDENING_LEDGER_2026-05-11.json",
      "shape": {
        "all_hardening_controls_covered": "bool",
        "artifact_family": "str",
        "changes_live_trading_behavior": "bool",
        "controls": [
          {
            "control": "str",
            "coverage": "str",
            "status": "str"
          }
        ],
        "credentials_touched": "bool",
        "evidence_class": "str",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "route_id": "str",
        "schema_version": "str",
        "summary": {
          "all_hardening_controls_covered": "bool",
          "control_count": "int"
        },
        "validation_safe": "bool"
      },
      "size_bytes": 2471,
      "source_hash": "05ea3d021fd1ac2202c2f3ceb4e880d61c13eed12d89b5193a1193b39248a4ee",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "all_hardening_controls_covered",
        "artifact_family",
        "changes_live_trading_behavior",
        "controls",
        "credentials_touched",
        "evidence_class",
        "generated_at_utc",
        "live_effect",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "route_id",
        "schema_version",
        "summary",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "bb92d67a0eba2dc255f2b6efa3a12451a748c205c715c56c054538a38cfcf4d8",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SCID_FREEZE_REPAIR_HOSTILE_REVIEW_LEDGER_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SCID_FREEZE_REPAIR_HOSTILE_REVIEW_LEDGER_2026-05-11.json",
      "shape": {
        "all_attacks_preempted_or_blocked": "bool",
        "artifact_family": "str",
        "changes_live_trading_behavior": "bool",
        "credentials_touched": "bool",
        "evidence_class": "str",
        "generated_at_utc": "str",
        "hostile_reviews": [
          {
            "attack": "str",
            "preemption": "str",
            "status": "str"
          }
        ],
        "live_effect": "bool",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "route_id": "str",
        "schema_version": "str",
        "segment_rows_reviewed": "int",
        "summary": {
          "all_attacks_preempted_or_blocked": "bool",
          "attack_count": "int"
        },
        "validation_safe": "bool"
      },
      "size_bytes": 2311,
      "source_hash": "015000dd4365ff2560fa80eb8fc12c50c0be3bf81a84e1f47b776ecb74b7680a",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "all_attacks_preempted_or_blocked",
        "artifact_family",
        "changes_live_trading_behavior",
        "credentials_touched",
        "evidence_class",
        "generated_at_utc",
        "hostile_reviews",
        "live_effect",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "route_id",
        "schema_version",
        "segment_rows_reviewed",
        "summary",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "d275bd7f86d1f9081687b6ec61be37afa33b9ccbf358fcde4499bd40d742113e",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SCID_FREEZE_REPAIR_NEGATIVE_ANATOMY_LEDGER_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SCID_FREEZE_REPAIR_NEGATIVE_ANATOMY_LEDGER_2026-05-11.json",
      "shape": {
        "artifact_family": "str",
        "changes_live_trading_behavior": "bool",
        "credentials_touched": "bool",
        "evidence_class": "str",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "prior_failure": {
          "failed_fields": [
            "str"
          ],
          "failure": "str",
          "root_cause": "str"
        },
        "promotion_verdict": "str",
        "repair": {
          "method": "str",
          "what_it_does_not_repair": [
            "str"
          ],
          "why_it_repairs": "str"
        },
        "route_id": "str",
        "schema_version": "str",
        "summary": {
          "root_cause": "str"
        },
        "validation_safe": "bool"
      },
      "size_bytes": 1709,
      "source_hash": "e639f206dc0f583c7a167f31f78005d2bfb4c990a8181710fc8c6c313ba46b7c",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "artifact_family",
        "changes_live_trading_behavior",
        "credentials_touched",
        "evidence_class",
        "generated_at_utc",
        "live_effect",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "prior_failure",
        "promotion_verdict",
        "repair",
        "route_id",
        "schema_version",
        "summary",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "905de4d4131e17d3db4fa9b81cd33a411aebac858b24d5ad895fa03a8c51799f",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SCID_FREEZE_REPAIR_NOLEAK_DIRTY_AUDIT_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SCID_FREEZE_REPAIR_NOLEAK_DIRTY_AUDIT_2026-05-11.json",
      "shape": {
        "artifact_family": "str",
        "changes_live_trading_behavior": "bool",
        "checks": {
          "no_live_prompt_config_risk_safety_execution_selector_canary_paths_in_scope": "bool",
          "scoped_paths_are_repair_or_reaudit_prompt_only": "bool"
        },
        "credentials_touched": "bool",
        "evidence_class": "str",
        "forbidden_surface_changes_detected": [],
        "generated_at_utc": "str",
        "live_effect": "bool",
        "live_state_refresh_path": [
          "str"
        ],
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "raw_market_data_commit_scan_rule": "str",
        "route_id": "str",
        "schema_version": "str",
        "scoped_diff_policy": "str",
        "scoped_repair_paths": [
          "str"
        ],
        "summary": {
          "forbidden_surface_changes_detected": "int",
          "scoped_path_count": "int",
          "unrelated_workspace_dirt_count": "int"
        },
        "unrelated_workspace_dirt_observed_not_part_of_repair_commit": [
          "str"
        ],
        "validation_safe": "bool"
      },
      "size_bytes": 13335,
      "source_hash": "a5d8342b897ce7f418dda3f92a496cb5c0364be15b109634dada8a42815d6c5b",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "artifact_family",
        "changes_live_trading_behavior",
        "checks",
        "credentials_touched",
        "evidence_class",
        "forbidden_surface_changes_detected",
        "generated_at_utc",
        "live_effect",
        "live_state_refresh_path",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "raw_market_data_commit_scan_rule",
        "route_id",
        "schema_version",
        "scoped_diff_policy",
        "scoped_repair_paths",
        "summary",
        "unrelated_workspace_dirt_observed_not_part_of_repair_commit",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "61148f9188022d79f2b249d860433edfd98874c5d27d2119b3f062bdca8cab7c",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SCID_FREEZE_REPAIR_NO_LAZY_BLOCKER_LEDGER_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SCID_FREEZE_REPAIR_NO_LAZY_BLOCKER_LEDGER_2026-05-11.json",
      "shape": {
        "artifact_family": "str",
        "changes_live_trading_behavior": "bool",
        "credentials_touched": "bool",
        "evidence_class": "str",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "remaining_blocker_count": "int",
        "remaining_blockers": [],
        "route_id": "str",
        "same_evidence_class_pursuit": [
          "str"
        ],
        "schema_version": "str",
        "summary": {
          "remaining_blocker_count": "int"
        },
        "terminal_blocker_status": "str",
        "validation_safe": "bool"
      },
      "size_bytes": 1430,
      "source_hash": "e1acb4ae385dd4e2163b205ba1253dc269b66fd264873641008de76aa844dadf",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "artifact_family",
        "changes_live_trading_behavior",
        "credentials_touched",
        "evidence_class",
        "generated_at_utc",
        "live_effect",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "remaining_blocker_count",
        "remaining_blockers",
        "route_id",
        "same_evidence_class_pursuit",
        "schema_version",
        "summary",
        "terminal_blocker_status",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "f033690eafc6af0aed51755986c334789793b98d06ddfddaab81545f602b6f43",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SCID_FREEZE_REPAIR_OUTPUT_MANIFEST_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SCID_FREEZE_REPAIR_OUTPUT_MANIFEST_2026-05-11.json",
      "shape": {
        "artifact_family": "str",
        "artifacts": {
          "completion_audit": {
            "json": "str",
            "md": "str"
          },
          "context_anchor": {
            "json": "str",
            "md": "str"
          },
          "duplicate_discovery_exclusion_audit": {
            "json": "str",
            "md": "str"
          },
          "hardening_coverage": {
            "json": "str",
            "md": "str"
          },
          "hostile_source_review": {
            "json": "str",
            "md": "str"
          },
          "negative_failure_anatomy": {
            "json": "str",
            "md": "str"
          },
          "next_g12_reaudit_prompt_pack": {
            "json": "str",
            "md": "str"
          },
          "no_lazy_blocker": {
            "json": "str",
            "md": "str"
          },
          "noleak_dirty_state_audit": {
            "json": "str",
            "md": "str"
          },
          "parser_asof_no_leak_audit": {
            "json": "str",
            "md": "str"
          },
          "process_limitation_countermeasures": {
            "json": "str",
            "md": "str"
          },
          "repair_packet": {
            "json": "str",
            "md": "str"
          },
          "saturation_self_redteam": {
            "json": "str",
            "md": "str"
          },
          "snapshot_segment_manifest": {
            "json": "str",
            "md": "str"
          },
          "source_freeze_ledger": {
            "json": "str",
            "md": "str"
          },
          "source_hash_manifest": {
            "json": "str",
            "md": "str"
          },
          "source_saturation": {
            "json": "str",
            "md": "str"
          }
        },
        "builder": "str",
        "changes_live_trading_behavior": "bool",
        "credentials_touched": "bool",
        "evidence_class": "str",
        "focused_tests": "str",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "next_g12_reaudit_prompt": "str",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "route_id": "str",
        "schema_version": "str",
        "summary": {
          "artifact_count": "int",
          "terminal_decision": "str"
        },
        "terminal_decision": "str",
        "validation_safe": "bool",
        "verifier": "str"
      },
      "size_bytes": 8858,
      "source_hash": "86dd799df41def28fbb478c71150370305ce811850e9135a05b61bc4204bf4dc",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "artifact_family",
        "artifacts",
        "builder",
        "changes_live_trading_behavior",
        "credentials_touched",
        "evidence_class",
        "focused_tests",
        "generated_at_utc",
        "live_effect",
        "next_g12_reaudit_prompt",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "route_id",
        "schema_version",
        "summary",
        "terminal_decision",
        "validation_safe",
        "verifier"
      ]
    },
    {
      "key_shape_fingerprint": "f30a06b0c54de2735cb69100b5bcd22ba91c2bf5618cf29fbb5336f7fcf150e1",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SCID_FREEZE_REPAIR_PARSER_ASOF_NOLEAK_AUDIT_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SCID_FREEZE_REPAIR_PARSER_ASOF_NOLEAK_AUDIT_2026-05-11.json",
      "shape": {
        "artifact_family": "str",
        "changes_live_trading_behavior": "bool",
        "checks": {
          "all_hard_floors_preserved": "bool",
          "all_parser_status_ok": "bool",
          "all_record_sizes_are_40": "bool",
          "no_broker_account_order_history_position_fields_read": "bool",
          "scid_to_asof_gate_explicit": "bool"
        },
        "credentials_touched": "bool",
        "evidence_class": "str",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "parser_rows": [
          {
            "as_of_rule": "str",
            "broker_account_order_history_position_fields_read": "bool",
            "eligible_hard_floor_preserved": "bool",
            "forbidden_fields_read": [],
            "header_size": "int",
            "no_leak_rule": "str",
            "parser_implementation": "str",
            "parser_implementation_sha256": "str",
            "parser_status": "str",
            "record_size": "int",
            "remaining_gate": "str",
            "segment_first_record_utc": "str",
            "segment_last_record_utc": "str",
            "source": "str",
            "symbol": "str",
            "version": "int"
          }
        ],
        "promotion_verdict": "str",
        "route_id": "str",
        "schema_version": "str",
        "summary": {
          "all_hard_floors_preserved": "bool",
          "parser_row_count": "int"
        },
        "validation_safe": "bool"
      },
      "size_bytes": 12160,
      "source_hash": "ccf9330f87d218fe82eb4e0adb63cbdbe2a5cad09e21d9dc1b1d0bdd76fb5984",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "artifact_family",
        "changes_live_trading_behavior",
        "checks",
        "credentials_touched",
        "evidence_class",
        "generated_at_utc",
        "live_effect",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "parser_rows",
        "promotion_verdict",
        "route_id",
        "schema_version",
        "summary",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "0e5a26a440b31f8ec4ef4a84caa71ee1a526120336508360025d7e5b6eef47f4",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SCID_FREEZE_REPAIR_SATURATION_REDTEAM_LEDGER_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SCID_FREEZE_REPAIR_SATURATION_REDTEAM_LEDGER_2026-05-11.json",
      "shape": {
        "artifact_family": "str",
        "changes_live_trading_behavior": "bool",
        "credentials_touched": "bool",
        "evidence_class": "str",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "required_questions": [
          {
            "answer": "str",
            "question": "str",
            "same_evidence_gap": "str"
          }
        ],
        "route_id": "str",
        "same_evidence_class_gaps_closed": "bool",
        "schema_version": "str",
        "summary": {
          "question_count": "int",
          "same_evidence_class_gaps_closed": "bool"
        },
        "validation_safe": "bool"
      },
      "size_bytes": 4428,
      "source_hash": "c9d32cc9060fc11b39982a8fa1c86f2e1bcf5edfc00831980279f3834713f6a7",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "artifact_family",
        "changes_live_trading_behavior",
        "credentials_touched",
        "evidence_class",
        "generated_at_utc",
        "live_effect",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "required_questions",
        "route_id",
        "same_evidence_class_gaps_closed",
        "schema_version",
        "summary",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "8a0960c22526e06c923ee6fba91c1634e63e49c9782f647ce06f20e3266dd28e",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SCID_FREEZE_REPAIR_SNAPSHOT_SEGMENT_MANIFEST_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SCID_FREEZE_REPAIR_SNAPSHOT_SEGMENT_MANIFEST_2026-05-11.json",
      "shape": {
        "artifact_family": "str",
        "changes_live_trading_behavior": "bool",
        "chosen_policy": "str",
        "credentials_touched": "bool",
        "evidence_class": "str",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "raw_snapshot_commit_policy": "str",
        "raw_snapshot_files_committed": "int",
        "raw_snapshot_files_written": "int",
        "route_id": "str",
        "schema_version": "str",
        "segment_count": "int",
        "segments": [
          {
            "append_safety_rule": "str",
            "eligible_segment_start_utc_hard_floor": "str",
            "immediate_rehash_matches": "bool",
            "segment_byte_end_exclusive": "int",
            "segment_byte_length": "int",
            "segment_byte_start": "int",
            "segment_descriptor_sha256": "str",
            "segment_first_record_utc": "str",
            "segment_last_record_utc": "str",
            "segment_record_count": "int",
            "segment_record_end_index_inclusive": "int",
            "segment_record_start_index": "int",
            "segment_records_sha256": "str",
            "snapshot_file_written": "bool",
            "snapshot_policy": "str",
            "source": "str",
            "source_path": "str",
            "symbol": "str"
          }
        ],
        "summary": {
          "policy": "str",
          "raw_snapshot_files_written": "int",
          "segment_count": "int"
        },
        "validation_safe": "bool"
      },
      "size_bytes": 10998,
      "source_hash": "7f7aeec4f6eff64cc402ce20b757a53c5049b5e6197df3bea718749a1937b7d2",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "artifact_family",
        "changes_live_trading_behavior",
        "chosen_policy",
        "credentials_touched",
        "evidence_class",
        "generated_at_utc",
        "live_effect",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "raw_snapshot_commit_policy",
        "raw_snapshot_files_committed",
        "raw_snapshot_files_written",
        "route_id",
        "schema_version",
        "segment_count",
        "segments",
        "summary",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "2474871dc7fcabda2e8fc2c15c0ac66fe772fa32581e936a263e5cca8e80cbdc",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SCID_FREEZE_REPAIR_SOURCE_FREEZE_LEDGER_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SCID_FREEZE_REPAIR_SOURCE_FREEZE_LEDGER_2026-05-11.json",
      "shape": {
        "all_9_sources_repaired": "bool",
        "all_9_sources_repaired_or_exact_blocked": "bool",
        "artifact_family": "str",
        "candidate_count": "int",
        "changes_live_trading_behavior": "bool",
        "credentials_touched": "bool",
        "evidence_class": "str",
        "freeze_rows": [
          {
            "chosen_repair_policy": "str",
            "coverage_end_drift_vs_source_packet": "bool",
            "current_mutable_metadata": {
              "absolute_path": "str",
              "coverage_end_utc": "str",
              "coverage_start_utc": "str",
              "current_full_file_hash_status": "str",
              "current_full_file_sha256_reference_only": "str",
              "exists": "bool",
              "file_name": "str",
              "first_record_timestamp_us": "int",
              "header_sha256": "str",
              "header_size": "int",
              "last_record_timestamp_us": "int",
              "magic": "str",
              "parser_status": "str",
              "record_count": "int",
              "record_size": "int",
              "remainder_bytes": "int",
              "size_bytes": "int",
              "utc_start_index": "int",
              "version": "int"
            },
            "duplicate_source_decision_prior": "str",
            "duplicate_source_decision_repaired": "str",
            "eligible_hard_floor_preserved": "bool",
            "eligible_segment_start_utc_hard_floor": "str",
            "g12_failure_anatomy": "str",
            "g12_recomputed_coverage_end_utc": "str",
            "g12_recomputed_full_file_sha256": "str",
            "g12_recomputed_size_bytes": "int",
            "no_leak_status": "str",
            "parser_asof_status": "str",
            "proxy_note": "str",
            "raw_snapshot_policy": "str",
            "record_count_drift_vs_source_packet": "int",
            "refreshed_coverage_end_utc": "str",
            "refreshed_coverage_start_utc": "str",
            "refreshed_record_count": "int",
            "refreshed_size_bytes": "int",
            "remaining_gates_before_validation": [
              "str"
            ],
            "repair_partition_assignment": "str",
            "repair_status": "str",
            "repaired_immutable_metadata": {
              "append_mutability_repaired_by": "str",
              "eligible_segment_start_utc_hard_floor": "str",
              "immediate_rehash_matches": "bool",
              "immediate_rehash_sha256": "str",
              "policy": "str",
              "pre_eligible_records_excluded": "int",
              "records_after_segment_may_append_without_hash_effect": "bool",
              "segment_byte_end_exclusive": "int",
              "segment_byte_length": "int",
              "segment_byte_start": "int",
              "segment_descriptor_sha256": "str",
              "segment_first_record_utc": "str",
              "segment_last_record_utc": "str",
              "segment_record_count": "int",
              "segment_record_end_index_inclusive": "int",
              "segment_record_start_index": "int",
              "segment_records_sha256": "str",
              "segment_status": "str",
              "source_file_name": "str",
              "source_path": "str"
            },
            "segment_hash_is_discovery_selected_source_hash": "bool",
            "source": "str",
            "source_family": "str",
            "source_full_file_hash_reference_only_not_accepted": "bool",
            "source_instrument": "str",
            "source_packet_coverage_end_utc": "str",
            "source_packet_coverage_start_utc": "str",
            "source_packet_eligible_segment_end_utc": "str",
            "source_packet_full_file_sha256": "str",
            "source_packet_partition_assignment": "str",
            "source_packet_record_count": "int",
            "source_packet_size_bytes": "int",
            "source_path": "str",
            "symbol": "str"
          }
        ],
        "generated_at_utc": "str",
        "live_effect": "bool",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "repair_blockers": [],
        "repair_policy": "str",
        "repair_policy_justification": "str",
        "repaired_source_count": "int",
        "route_id": "str",
        "schema_version": "str",
        "source_access_blocker_count": "int",
        "summary": {
          "candidate_count": "int",
          "repaired_source_count": "int",
          "source_access_blocker_count": "int",
          "terminal_repair_status": "str"
        },
        "validation_safe": "bool"
      },
      "size_bytes": 47370,
      "source_hash": "5f87cef4e19170c9b743d39c1f4c9d5a7d87157318b10c428e60a889f9c31758",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "all_9_sources_repaired",
        "all_9_sources_repaired_or_exact_blocked",
        "artifact_family",
        "candidate_count",
        "changes_live_trading_behavior",
        "credentials_touched",
        "evidence_class",
        "freeze_rows",
        "generated_at_utc",
        "live_effect",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "repair_blockers",
        "repair_policy",
        "repair_policy_justification",
        "repaired_source_count",
        "route_id",
        "schema_version",
        "source_access_blocker_count",
        "summary",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "5cff759cf7c975da6881f3907c6c71dbb35aaa9f9e4e8d071f6419888f9ffcd3",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SCID_FREEZE_REPAIR_SOURCE_HASH_MANIFEST_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SCID_FREEZE_REPAIR_SOURCE_HASH_MANIFEST_2026-05-11.json",
      "shape": {
        "accepted_hash_policy": "str",
        "all_accepted_hashes_present": "bool",
        "artifact_family": "str",
        "changes_live_trading_behavior": "bool",
        "credentials_touched": "bool",
        "evidence_class": "str",
        "full_file_hash_policy": "str",
        "generated_at_utc": "str",
        "hash_rows": [
          {
            "accepted_source_evidence_hash_type": "str",
            "accepted_source_evidence_sha256": "str",
            "full_file_reference_is_not_validation_evidence": "bool",
            "g12_recomputed_full_file_sha256_stale_reference": "str",
            "header_sha256": "str",
            "mutable_full_file_hash_reference_only": "str",
            "mutable_full_file_hash_status": "str",
            "parser_implementation": "str",
            "parser_implementation_sha256": "str",
            "segment_descriptor_sha256": "str",
            "source": "str",
            "source_packet_full_file_sha256_stale_reference": "str",
            "source_path": "str",
            "symbol": "str"
          }
        ],
        "live_effect": "bool",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "route_id": "str",
        "schema_version": "str",
        "summary": {
          "accepted_hashes_present": "bool",
          "hash_row_count": "int"
        },
        "validation_safe": "bool"
      },
      "size_bytes": 13627,
      "source_hash": "fcb4327bc3ce50293730278ffd973096d26b6e79a9350e22ab43b62f8903bdc0",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "accepted_hash_policy",
        "all_accepted_hashes_present",
        "artifact_family",
        "changes_live_trading_behavior",
        "credentials_touched",
        "evidence_class",
        "full_file_hash_policy",
        "generated_at_utc",
        "hash_rows",
        "live_effect",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "route_id",
        "schema_version",
        "summary",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "c25d435269d11f9315168bf40a6ac1d42dfa9474e6a2109501c554b7382ef7b3",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SCID_FREEZE_REPAIR_SOURCE_SATURATION_LEDGER_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SCID_FREEZE_REPAIR_SOURCE_SATURATION_LEDGER_2026-05-11.json",
      "shape": {
        "all_required_sources_seen": "bool",
        "artifact_family": "str",
        "changes_live_trading_behavior": "bool",
        "credentials_touched": "bool",
        "evidence_class": "str",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "required_source_names": [
          "str"
        ],
        "resolved_source_names": [
          "str"
        ],
        "route_id": "str",
        "schema_version": "str",
        "searched_roots": [
          {
            "finding": "str",
            "path": "str",
            "root_id": "str"
          }
        ],
        "source_saturation_decision": "str",
        "summary": {
          "all_required_sources_seen": "bool",
          "searched_root_count": "int"
        },
        "validation_safe": "bool"
      },
      "size_bytes": 2774,
      "source_hash": "53381df497b8f184458617d68ab5a084f32d2c76f9aad552d6170329c8f1af42",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "all_required_sources_seen",
        "artifact_family",
        "changes_live_trading_behavior",
        "credentials_touched",
        "evidence_class",
        "generated_at_utc",
        "live_effect",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "required_source_names",
        "resolved_source_names",
        "route_id",
        "schema_version",
        "searched_roots",
        "source_saturation_decision",
        "summary",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "c349d7b48e8f7d93b33dd4a7f8be370cff37cdd0b7338e53f7f31d475b7445a4",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_VERIFICATION_RESULT_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_VERIFICATION_RESULT_2026-05-11.json",
      "shape": {
        "baseline_controls_present": [
          "str"
        ],
        "can_mark_goal_complete_after_commit_and_context_refresh": "bool",
        "completion_standard_satisfied": "bool",
        "failures": [],
        "focused_tests": {
          "args": [
            "str"
          ],
          "ok": "bool",
          "returncode": "int",
          "stderr": "str",
          "stdout": "str"
        },
        "live_effect": "bool",
        "ok": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "py_compile": {
          "args": [
            "str"
          ],
          "ok": "bool",
          "returncode": "int",
          "stderr": "str",
          "stdout": "str"
        },
        "repaired_source_count": "int",
        "segment_rehash": {
          "failures": [],
          "ok": "bool",
          "verified_rows": [
            {
              "rehash_matches": "bool",
              "rehash_sha256": "str",
              "segment_byte_end_exclusive": "int",
              "segment_byte_start": "int",
              "segment_records_sha256": "str",
              "source": "str",
              "symbol": "str"
            }
          ],
          "verified_segment_count": "int"
        },
        "selected_source_rows_preserved": "int",
        "terminal_decision": "str",
        "validation_safe": "bool"
      },
      "size_bytes": 5993,
      "source_hash": "05558d50e485f9fbc0a131fc1abfac1a1df4bca0382bfb4b7793007d7ddacae8",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "baseline_controls_present",
        "can_mark_goal_complete_after_commit_and_context_refresh",
        "completion_standard_satisfied",
        "failures",
        "focused_tests",
        "live_effect",
        "ok",
        "outcome_review_opened",
        "promotion_verdict",
        "py_compile",
        "repaired_source_count",
        "segment_rehash",
        "selected_source_rows_preserved",
        "terminal_decision",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "33f4075a4fdd580d5b5bb1717679f70cdfef56add56185624c3c4fa5d972b7bd",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_ACQUISITION_LADDER_LEDGER_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_ACQUISITION_LADDER_LEDGER_2026-05-11.json",
      "shape": {
        "artifact_family": "str",
        "best_current_route": "str",
        "blocker_rows": [
          {
            "blocker": "str",
            "exact_unblocker": "str",
            "owner_action_required": "bool",
            "priority": "int"
          }
        ],
        "changes_live_trading_behavior": "bool",
        "credentials_touched": "bool",
        "evidence_class": "str",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "materialized_native_candidate_count": "int",
        "no_lazy_blocker_status": "str",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "rejected_or_unhashed_native_file_count": "int",
        "route_id": "str",
        "schema_version": "str",
        "validation_safe": "bool"
      },
      "size_bytes": 2116,
      "source_hash": "5408eeac920d3db944de91d0a90d2f70ffa1dd5ff68073e202c20e141ee88c3d",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "artifact_family",
        "best_current_route",
        "blocker_rows",
        "changes_live_trading_behavior",
        "credentials_touched",
        "evidence_class",
        "generated_at_utc",
        "live_effect",
        "materialized_native_candidate_count",
        "no_lazy_blocker_status",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "rejected_or_unhashed_native_file_count",
        "route_id",
        "schema_version",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "9ee8243a78364b6be8d0fe71ef2a20011fb8b9314f2d98f78093c091b1e63f13",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_ADVERSARIAL_BASELINE_PRESERVATION_LEDGER_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_ADVERSARIAL_BASELINE_PRESERVATION_LEDGER_2026-05-11.json",
      "shape": {
        "artifact_family": "str",
        "baseline_control_count": "int",
        "baseline_controls": [
          "str"
        ],
        "changes_live_trading_behavior": "bool",
        "credentials_touched": "bool",
        "evidence_class": "str",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "preservation_policy": "str",
        "promotion_verdict": "str",
        "route_id": "str",
        "schema_version": "str",
        "selected_fpb_families": [
          "str"
        ],
        "validation_execution_prompt_emitted": "bool",
        "validation_safe": "bool"
      },
      "size_bytes": 1390,
      "source_hash": "c9fa43c6410333eeb2de55a5b66ee365ee825d3e56b7e309219146380256a7f5",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "artifact_family",
        "baseline_control_count",
        "baseline_controls",
        "changes_live_trading_behavior",
        "credentials_touched",
        "evidence_class",
        "generated_at_utc",
        "live_effect",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "preservation_policy",
        "promotion_verdict",
        "route_id",
        "schema_version",
        "selected_fpb_families",
        "validation_execution_prompt_emitted",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "ec3276eadcab894aeccd43cd18b22ef8fa81d1628d801f57f8ddda2614eabeb0",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_COMPLETION_AUDIT_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_COMPLETION_AUDIT_2026-05-11.json",
      "shape": {
        "accepted_csv_candidate_count": "int",
        "accepted_native_scid_candidate_count": "int",
        "artifact_family": "str",
        "can_mark_goal_complete_after_verifier_tests_commit_and_context_refresh": "bool",
        "changes_live_trading_behavior": "bool",
        "completion_standard_satisfied": "bool",
        "credentials_touched": "bool",
        "current_discovery_exposed_source_rows_excluded": "int",
        "evidence_class": "str",
        "g12_source_pool_audit_prompt_emitted": "bool",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "missing_incomplete_or_weak_requirements": [],
        "objective_restatement": "str",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "prompt_to_artifact_checklist": [
          {
            "evidence": "str",
            "requirement": "str",
            "status": "str"
          }
        ],
        "route_id": "str",
        "schema_version": "str",
        "terminal_decision": "str",
        "validation_execution_prompt_emitted": "bool",
        "validation_safe": "bool"
      },
      "size_bytes": 7207,
      "source_hash": "5fe484b1195f85384caee378ced5f1d37a91504f4b4475d15f16b34474a45ecb",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "accepted_csv_candidate_count",
        "accepted_native_scid_candidate_count",
        "artifact_family",
        "can_mark_goal_complete_after_verifier_tests_commit_and_context_refresh",
        "changes_live_trading_behavior",
        "completion_standard_satisfied",
        "credentials_touched",
        "current_discovery_exposed_source_rows_excluded",
        "evidence_class",
        "g12_source_pool_audit_prompt_emitted",
        "generated_at_utc",
        "live_effect",
        "missing_incomplete_or_weak_requirements",
        "objective_restatement",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "prompt_to_artifact_checklist",
        "route_id",
        "schema_version",
        "terminal_decision",
        "validation_execution_prompt_emitted",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "5df87b9f45d2ec0973c29f35d6dd9bbcf87e613bfeeed55dab685327bcfc428d",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_CONTEXT_ANCHOR_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_CONTEXT_ANCHOR_2026-05-11.json",
      "shape": {
        "accepted_input_artifacts": {
          "controlling_prompt": "str",
          "fpb_aggregate_matrix": "str",
          "fpb_denominator_duplicate_policy": "str",
          "g0_baseline_packet": "str",
          "g0_completion": "str",
          "g0_partition_packet": "str",
          "g0_purge_policy": "str",
          "g0_source_contract": "str",
          "g0_synthesis_route_ranking": "str",
          "source_selection": "str",
          "source_universe": "str",
          "source_universe_rows": "str"
        },
        "adversarial_baselines": [
          "str"
        ],
        "artifact_family": "str",
        "changes_live_trading_behavior": "bool",
        "controlling_prompt": "str",
        "credentials_touched": "bool",
        "current_discovery_exposed_source_rows_excluded": "int",
        "evidence_class": "str",
        "generated_at_utc": "str",
        "git_head_at_build_start": "str",
        "live_effect": "bool",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "route_id": "str",
        "schema_version": "str",
        "scope_boundary": "str",
        "selected_families": [
          "str"
        ],
        "terminal_decision": "str",
        "validation_safe": "bool"
      },
      "size_bytes": 4096,
      "source_hash": "4cbe39169edc85d08d7ef6822c477da78dcf9bfc3a8e04f021b5717746743713",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "accepted_input_artifacts",
        "adversarial_baselines",
        "artifact_family",
        "changes_live_trading_behavior",
        "controlling_prompt",
        "credentials_touched",
        "current_discovery_exposed_source_rows_excluded",
        "evidence_class",
        "generated_at_utc",
        "git_head_at_build_start",
        "live_effect",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "route_id",
        "schema_version",
        "scope_boundary",
        "selected_families",
        "terminal_decision",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "f94e4dd1913f93ddfe78e6ce82d144d6b11fda57cfc05f22e27d61d9d2d60506",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_DUPLICATE_SOURCE_DECISION_LEDGER_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_DUPLICATE_SOURCE_DECISION_LEDGER_2026-05-11.json",
      "shape": {
        "artifact_family": "str",
        "changes_live_trading_behavior": "bool",
        "credentials_touched": "bool",
        "duplicate_key_policy": "str",
        "duplicate_source_count": "int",
        "duplicate_source_rows": [
          {
            "absolute_path": "str",
            "coverage_end_utc": "str",
            "coverage_start_utc": "str",
            "coverage_status": "str",
            "duplicate_of": "str",
            "file_name": "str",
            "has_ohlc": "bool",
            "hash_status": "str",
            "header": [
              "str"
            ],
            "partition_assignment": "str",
            "repo_relative_path": "str",
            "row_count": "int",
            "size_bytes": "int",
            "source_family": "str",
            "source_sha256": "str",
            "symbol": "str",
            "timeframe": "str",
            "triage_decision": "str"
          }
        ],
        "evidence_class": "str",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "route_id": "str",
        "schema_version": "str",
        "validation_safe": "bool"
      },
      "size_bytes": 343236,
      "source_hash": "555d4b386c1b96a3de72798c55f756a924a39b314d01d681e7e18f3a290f0e2f",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "artifact_family",
        "changes_live_trading_behavior",
        "credentials_touched",
        "duplicate_key_policy",
        "duplicate_source_count",
        "duplicate_source_rows",
        "evidence_class",
        "generated_at_utc",
        "live_effect",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "route_id",
        "schema_version",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "9c4077d66caa1d9bc8487c5252422a808d064f84ff91c12f715c8a3726bbcf2d",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_GIT_HISTORY_SOURCE_SEARCH_LEDGER_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_GIT_HISTORY_SOURCE_SEARCH_LEDGER_2026-05-11.json",
      "shape": {
        "artifact_family": "str",
        "changes_live_trading_behavior": "bool",
        "credentials_touched": "bool",
        "evidence_class": "str",
        "generated_at_utc": "str",
        "git_log_command": "str",
        "git_log_returncode": "int",
        "history_search_status": "str",
        "live_effect": "bool",
        "matched_source_or_artifact_path_count": "int",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "route_id": "str",
        "sample_matches": [
          "str"
        ],
        "schema_version": "str",
        "stderr": [],
        "validation_safe": "bool"
      },
      "size_bytes": 15706,
      "source_hash": "7522826a67aa5c5c6fefaa8fce4263ce263521e7b3601a5d111d703249d9699e",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "artifact_family",
        "changes_live_trading_behavior",
        "credentials_touched",
        "evidence_class",
        "generated_at_utc",
        "git_log_command",
        "git_log_returncode",
        "history_search_status",
        "live_effect",
        "matched_source_or_artifact_path_count",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "route_id",
        "sample_matches",
        "schema_version",
        "stderr",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "82d7bc9cb4ece590f073b4eb6fa80bdbcfa2739add127a83d0e9d335263bb10f",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_HARDENING_COVERAGE_LEDGER_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_HARDENING_COVERAGE_LEDGER_2026-05-11.json",
      "shape": {
        "all_required_hardening_controls_present": "bool",
        "artifact_family": "str",
        "changes_live_trading_behavior": "bool",
        "coverage_rows": [
          {
            "evidence": "str",
            "requirement": "str",
            "status": "str"
          }
        ],
        "credentials_touched": "bool",
        "evidence_class": "str",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "route_id": "str",
        "schema_version": "str",
        "validation_safe": "bool"
      },
      "size_bytes": 2238,
      "source_hash": "6d7e4532d471c0ec84f84303763555c4ffe34b8c454b26ba0e95b25b59b2fc9d",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "all_required_hardening_controls_present",
        "artifact_family",
        "changes_live_trading_behavior",
        "coverage_rows",
        "credentials_touched",
        "evidence_class",
        "generated_at_utc",
        "live_effect",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "route_id",
        "schema_version",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "5470921a0531ac3ccfc017929f9cf2b0a3a7aeb24cdd3992600cd67eef51ddba",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_HOSTILE_SOURCE_EDGE_REVIEW_LEDGER_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_HOSTILE_SOURCE_EDGE_REVIEW_LEDGER_2026-05-11.json",
      "shape": {
        "accepted_csv_candidate_count": "int",
        "accepted_native_candidate_count": "int",
        "artifact_family": "str",
        "changes_live_trading_behavior": "bool",
        "credentials_touched": "bool",
        "edge_review_boundary": "str",
        "evidence_class": "str",
        "generated_at_utc": "str",
        "hostile_review_rows": [
          {
            "mitigation": "str",
            "risk": "str"
          }
        ],
        "live_effect": "bool",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "route_id": "str",
        "schema_version": "str",
        "validation_safe": "bool"
      },
      "size_bytes": 1790,
      "source_hash": "64a45c0023bea05e75e0357e34fded8cb22e8e9733302d6f257441abc2e53634",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "accepted_csv_candidate_count",
        "accepted_native_candidate_count",
        "artifact_family",
        "changes_live_trading_behavior",
        "credentials_touched",
        "edge_review_boundary",
        "evidence_class",
        "generated_at_utc",
        "hostile_review_rows",
        "live_effect",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "route_id",
        "schema_version",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "a83598b999a1bddd1c5e92dd7f12f2113e596460faf71de34bd8dc68711c51f4",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_LFS_AND_MATERIALIZATION_AUDIT_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_LFS_AND_MATERIALIZATION_AUDIT_2026-05-11.json",
      "shape": {
        "artifact_family": "str",
        "changes_live_trading_behavior": "bool",
        "credentials_touched": "bool",
        "deferred_large_native_file_count": "int",
        "deferred_large_native_files": [
          {
            "file_name": "str",
            "size_bytes": "int",
            "unblocker": "str"
          }
        ],
        "evidence_class": "str",
        "generated_at_utc": "str",
        "hashed_native_scid_candidate_count": "int",
        "live_effect": "bool",
        "materialization_policy": "str",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "raw_source_files_committed_by_this_route": [],
        "route_id": "str",
        "schema_version": "str",
        "validation_safe": "bool"
      },
      "size_bytes": 2203,
      "source_hash": "efb6760114970de3de7bbd29e1c215d682902d837530fe58b23e6087ad8e7c51",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "artifact_family",
        "changes_live_trading_behavior",
        "credentials_touched",
        "deferred_large_native_file_count",
        "deferred_large_native_files",
        "evidence_class",
        "generated_at_utc",
        "hashed_native_scid_candidate_count",
        "live_effect",
        "materialization_policy",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "raw_source_files_committed_by_this_route",
        "route_id",
        "schema_version",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "3f821c2a5513eb4cd8efc7d2ec90d065590d23504c8b7b799ec7b2fb4646af72",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_LOCAL_CSV_TRIAGE_LEDGER_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_LOCAL_CSV_TRIAGE_LEDGER_2026-05-11.json",
      "shape": {
        "accepted_csv_candidate_count": "int",
        "accepted_csv_candidates": [],
        "artifact_family": "str",
        "changes_live_trading_behavior": "bool",
        "credentials_touched": "bool",
        "duplicate_csv_count": "int",
        "evidence_class": "str",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "rejected_csv_count": "int",
        "rejected_csv_rows": [
          {
            "absolute_path": "str",
            "coverage_end_utc": "str",
            "coverage_start_utc": "str",
            "coverage_status": "str",
            "file_name": "str",
            "has_ohlc": "bool",
            "hash_status": "str",
            "header": [
              "str"
            ],
            "partition_assignment": "str",
            "repo_relative_path": "str",
            "row_count": "int",
            "size_bytes": "int",
            "source_family": "str",
            "source_sha256": "str",
            "symbol": "str",
            "timeframe": "str",
            "triage_decision": "str"
          }
        ],
        "route_id": "str",
        "schema_version": "str",
        "validation_safe": "bool"
      },
      "size_bytes": 510541,
      "source_hash": "ae6a3bcb152d5d4f5b672a9b0d020b5048337e6cb2023cb345652bb786942cd1",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "accepted_csv_candidate_count",
        "accepted_csv_candidates",
        "artifact_family",
        "changes_live_trading_behavior",
        "credentials_touched",
        "duplicate_csv_count",
        "evidence_class",
        "generated_at_utc",
        "live_effect",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "rejected_csv_count",
        "rejected_csv_rows",
        "route_id",
        "schema_version",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "00b2df4a5f99858ef611f5306fa75d26e47dcb7aa7ac08bea243ce2ab3fc17ba",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_NATIVE_SCID_SEALED_POOL_CANDIDATE_LEDGER_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_NATIVE_SCID_SEALED_POOL_CANDIDATE_LEDGER_2026-05-11.json",
      "shape": {
        "accepted_native_scid_candidate_count": "int",
        "accepted_native_scid_candidates": [
          {
            "absolute_path": "str",
            "coverage_end_utc": "str",
            "coverage_start_utc": "str",
            "duplicate_source_decision": "str",
            "eligible_segment_end_utc": "str",
            "eligible_segment_start_utc": "str",
            "eligible_segment_status": "str",
            "file_name": "str",
            "hash_status": "str",
            "header_size": "int",
            "magic": "str",
            "no_leak_status": "str",
            "parser_asof_status": "str",
            "parser_status": "str",
            "partition_assignment": "str",
            "proxy_note": "str",
            "record_count": "int",
            "record_size": "int",
            "required_before_validation": [
              "str"
            ],
            "size_bytes": "int",
            "source_family": "str",
            "source_instrument": "str",
            "source_sha256": "str",
            "symbol": "str",
            "timeframe": "str",
            "triage_decision": "str",
            "utc_start_index": "int",
            "version": "int"
          }
        ],
        "artifact_family": "str",
        "candidate_pool_status": "str",
        "changes_live_trading_behavior": "bool",
        "credentials_touched": "bool",
        "duplicate_native_scid_count": "int",
        "evidence_class": "str",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "rejected_native_scid_count": "int",
        "rejected_native_scid_rows": [
          {
            "absolute_path": "str",
            "coverage_end_utc": "str",
            "coverage_start_utc": "str",
            "eligible_segment_end_utc": "str",
            "eligible_segment_start_utc": "NoneType",
            "eligible_segment_status": "str",
            "file_name": "str",
            "hash_status": "str",
            "header_size": "int",
            "magic": "str",
            "no_leak_status": "str",
            "parser_asof_status": "str",
            "parser_status": "str",
            "partition_assignment": "str",
            "proxy_note": "str",
            "record_count": "int",
            "record_size": "int",
            "size_bytes": "int",
            "source_family": "str",
            "source_instrument": "str",
            "source_sha256": "str",
            "symbol": "str",
            "timeframe": "str",
            "triage_decision": "str",
            "utc_start_index": "int",
            "version": "int"
          }
        ],
        "route_id": "str",
        "schema_version": "str",
        "terminal_decision": "str",
        "validation_safe": "bool"
      },
      "size_bytes": 46999,
      "source_hash": "5e9049c332d90fcebc6595739f42225bbe12d6282e21c6e847e210edcbd288e6",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "accepted_native_scid_candidate_count",
        "accepted_native_scid_candidates",
        "artifact_family",
        "candidate_pool_status",
        "changes_live_trading_behavior",
        "credentials_touched",
        "duplicate_native_scid_count",
        "evidence_class",
        "generated_at_utc",
        "live_effect",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "rejected_native_scid_count",
        "rejected_native_scid_rows",
        "route_id",
        "schema_version",
        "terminal_decision",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "9a760850ac2335f48019e39a4444b7a7dcf6532812f3a268df33ea6e1da54f97",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_NEGATIVE_FAILURE_ANATOMY_LEDGER_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_NEGATIVE_FAILURE_ANATOMY_LEDGER_2026-05-11.json",
      "shape": {
        "accepted_csv_candidate_count": "int",
        "accepted_native_scid_candidate_count": "int",
        "artifact_family": "str",
        "changes_live_trading_behavior": "bool",
        "credentials_touched": "bool",
        "evidence_class": "str",
        "generated_at_utc": "str",
        "key_findings": [
          "str"
        ],
        "live_effect": "bool",
        "materialized_clean_source_pool_exists": "bool",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "rejection_counts": {
          "NOT_MATERIALIZED_HASH_REQUIRED_BEFORE_SOURCE_POOL": "int",
          "REJECT_NATIVE_SCID_NO_POST_EMBARGO_SEGMENT_YET_OR_MISSING_COMPARABLE_SOURCE": "int",
          "REJECT_PURGE_EMBARGO_OR_MISSING_COVERAGE_FAIL_CLOSED": "int",
          "REJECT_SELECTED_SOURCE_HASH_DISCOVERY_EXPOSED": "int",
          "REJECT_UNSUPPORTED_SCHEMA_OR_TIMEFRAME_FOR_FPB_ENGINE": "int"
        },
        "route_id": "str",
        "schema_version": "str",
        "terminal_decision": "str",
        "validation_safe": "bool"
      },
      "size_bytes": 1853,
      "source_hash": "ab397c07483b6050a8a1e71e6d2cfb91d0f31642a94fac76a46dc23e8fec3040",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "accepted_csv_candidate_count",
        "accepted_native_scid_candidate_count",
        "artifact_family",
        "changes_live_trading_behavior",
        "credentials_touched",
        "evidence_class",
        "generated_at_utc",
        "key_findings",
        "live_effect",
        "materialized_clean_source_pool_exists",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "rejection_counts",
        "route_id",
        "schema_version",
        "terminal_decision",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "0f02ab10455154ce890d2ed2d95a49165d17c8f90d4c50f583d3cd31f727d060",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_NEXT_G12_PROMPT_PACK_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_NEXT_G12_PROMPT_PACK_2026-05-11.json",
      "shape": {
        "artifact_family": "str",
        "audit_boundary": "str",
        "changes_live_trading_behavior": "bool",
        "credentials_touched": "bool",
        "evidence_class": "str",
        "g12_source_pool_audit_prompt_emitted": "bool",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "native_scid_candidate_count_for_audit": "int",
        "next_g12_prompt_path": "str",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "route_id": "str",
        "schema_version": "str",
        "source_pool_ledger": "str",
        "validation_safe": "bool"
      },
      "size_bytes": 1397,
      "source_hash": "ce56918936af849731464c3be66e59c2888eadd705e453d3fa131ec78275af25",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "artifact_family",
        "audit_boundary",
        "changes_live_trading_behavior",
        "credentials_touched",
        "evidence_class",
        "g12_source_pool_audit_prompt_emitted",
        "generated_at_utc",
        "live_effect",
        "native_scid_candidate_count_for_audit",
        "next_g12_prompt_path",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "route_id",
        "schema_version",
        "source_pool_ledger",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "2abee93998169e3111fd86dc0a78f2ef187a363cb63a4bfe4474d8a2c31ca159",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_NOLEAK_DIRTY_STATE_AUDIT_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_NOLEAK_DIRTY_STATE_AUDIT_2026-05-11.json",
      "shape": {
        "artifact_family": "str",
        "changes_live_trading_behavior": "bool",
        "credentials_touched": "bool",
        "dirty_state_policy": "str",
        "evidence_class": "str",
        "generated_at_utc": "str",
        "git_status_returncode": "int",
        "live_effect": "bool",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "route_id": "str",
        "route_scope_dirty_entries": [
          "str"
        ],
        "schema_version": "str",
        "unrelated_dirty_entry_count": "int",
        "validation_safe": "bool"
      },
      "size_bytes": 1311,
      "source_hash": "96cf07203f4c98f1f386548ee3e75d311da389a48eb47b0b1060bf8ae92671a6",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "artifact_family",
        "changes_live_trading_behavior",
        "credentials_touched",
        "dirty_state_policy",
        "evidence_class",
        "generated_at_utc",
        "git_status_returncode",
        "live_effect",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "route_id",
        "route_scope_dirty_entries",
        "schema_version",
        "unrelated_dirty_entry_count",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "29591be31ca612d60a533493f0b23054f0eec8bb388f24b7ae8e4967db2473c2",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_OUTPUT_MANIFEST_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_OUTPUT_MANIFEST_2026-05-11.json",
      "shape": {
        "accepted_candidate_count": "int",
        "accepted_csv_candidate_count": "int",
        "accepted_native_scid_candidate_count": "int",
        "artifact_family": "str",
        "changes_live_trading_behavior": "bool",
        "credentials_touched": "bool",
        "evidence_class": "str",
        "g12_source_pool_audit_prompt_emitted": "bool",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "next_g12_prompt": "str",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "outputs": {
          "acquisition_ladder": {
            "json": "str",
            "md": "str"
          },
          "baseline_preservation": {
            "json": "str",
            "md": "str"
          },
          "context_anchor": {
            "json": "str",
            "md": "str"
          },
          "dirty_state": {
            "json": "str",
            "md": "str"
          },
          "duplicate_source": {
            "json": "str",
            "md": "str"
          },
          "git_history": {
            "json": "str",
            "md": "str"
          },
          "hardening": {
            "json": "str",
            "md": "str"
          },
          "hostile_review": {
            "json": "str",
            "md": "str"
          },
          "lfs_materialization": {
            "json": "str",
            "md": "str"
          },
          "local_csv_triage": {
            "json": "str",
            "md": "str"
          },
          "native_scid_pool": {
            "json": "str",
            "md": "str"
          },
          "negative_anatomy": {
            "json": "str",
            "md": "str"
          },
          "next_prompt_pack": {
            "json": "str",
            "md": "str"
          },
          "process_limitations": {
            "json": "str",
            "md": "str"
          },
          "selected_source_coverage": {
            "json": "str",
            "md": "str"
          },
          "self_redteam": {
            "json": "str",
            "md": "str"
          },
          "source_contract": {
            "json": "str",
            "md": "str"
          },
          "source_saturation": {
            "json": "str",
            "md": "str"
          },
          "tick_parquet_triage": {
            "json": "str",
            "md": "str"
          }
        },
        "promotion_verdict": "str",
        "route_id": "str",
        "schema_version": "str",
        "terminal_decision": "str",
        "validation_execution_prompt_emitted": "bool",
        "validation_safe": "bool"
      },
      "size_bytes": 9126,
      "source_hash": "0d177d4ded657183104fbd3f06c3f9b4881bb662bc06dff8d60bfc7d4548d072",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "accepted_candidate_count",
        "accepted_csv_candidate_count",
        "accepted_native_scid_candidate_count",
        "artifact_family",
        "changes_live_trading_behavior",
        "credentials_touched",
        "evidence_class",
        "g12_source_pool_audit_prompt_emitted",
        "generated_at_utc",
        "live_effect",
        "next_g12_prompt",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "outputs",
        "promotion_verdict",
        "route_id",
        "schema_version",
        "terminal_decision",
        "validation_execution_prompt_emitted",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "4a9cd8494b052178d05121ceba5d9d5d7f7271ca67e8e815709c27aadd9ae473",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_PROCESS_LIMITATION_COUNTERMEASURES_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_PROCESS_LIMITATION_COUNTERMEASURES_2026-05-11.json",
      "shape": {
        "anti_boxing_status": "str",
        "artifact_family": "str",
        "changes_live_trading_behavior": "bool",
        "credentials_touched": "bool",
        "evidence_class": "str",
        "generated_at_utc": "str",
        "limitations": [
          {
            "countermeasure": "str",
            "limitation": "str"
          }
        ],
        "live_effect": "bool",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "route_id": "str",
        "schema_version": "str",
        "validation_safe": "bool"
      },
      "size_bytes": 1640,
      "source_hash": "3c01fbff27725d0dfad480465e76d49930de080d25202e1e1933714f5e196189",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "anti_boxing_status",
        "artifact_family",
        "changes_live_trading_behavior",
        "credentials_touched",
        "evidence_class",
        "generated_at_utc",
        "limitations",
        "live_effect",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "route_id",
        "schema_version",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "6446544c157bc61a0e8e1aa2caeab1aa2559d331d43f662c425476de4817b82e",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_SATURATION_SELF_REDTEAM_LEDGER_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_SATURATION_SELF_REDTEAM_LEDGER_2026-05-11.json",
      "shape": {
        "accepted_candidate_count": "int",
        "artifact_family": "str",
        "changes_live_trading_behavior": "bool",
        "credentials_touched": "bool",
        "evidence_class": "str",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "route_id": "str",
        "saturation_verdict": "str",
        "schema_version": "str",
        "self_redteam_checks": [
          {
            "answer": "str",
            "question": "str"
          }
        ],
        "validation_safe": "bool"
      },
      "size_bytes": 1740,
      "source_hash": "e7ebfd6dd854c00de1578f624a1f6cfd0c9fd73ce7df4ce278665eceda78b4c3",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "accepted_candidate_count",
        "artifact_family",
        "changes_live_trading_behavior",
        "credentials_touched",
        "evidence_class",
        "generated_at_utc",
        "live_effect",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "route_id",
        "saturation_verdict",
        "schema_version",
        "self_redteam_checks",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "efd2a31780330a4482a907478c891a01f4a947ffc2d21a9f0778dd497f761944",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_SEARCHED_ROOT_SOURCE_SATURATION_LEDGER_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_SEARCHED_ROOT_SOURCE_SATURATION_LEDGER_2026-05-11.json",
      "shape": {
        "artifact_family": "str",
        "changes_live_trading_behavior": "bool",
        "credentials_touched": "bool",
        "evidence_class": "str",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "roots": [
          {
            "exists": "bool",
            "extension_counts": {
              ".csv": "int",
              ".parquet": "int"
            },
            "file_count": "int",
            "role": "str",
            "root_id": "str",
            "root_path": "str",
            "search_limit_hit": "bool",
            "sensitive_paths_excluded": "bool"
          }
        ],
        "route_id": "str",
        "schema_version": "str",
        "search_policy": "str",
        "source_saturation_status": "str",
        "validation_safe": "bool"
      },
      "size_bytes": 2579,
      "source_hash": "5350af8b872ce9f6871f1bc462237fc2399456b50367abf4309d9b792413e530",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "artifact_family",
        "changes_live_trading_behavior",
        "credentials_touched",
        "evidence_class",
        "generated_at_utc",
        "live_effect",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "roots",
        "route_id",
        "schema_version",
        "search_policy",
        "source_saturation_status",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "6b438403b58321f81fc431f2cfce2f3d46829967fd206b92f0ab953d4c1a634d",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_SELECTED_SOURCE_COVERAGE_LEDGER_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_SELECTED_SOURCE_COVERAGE_LEDGER_2026-05-11.json",
      "shape": {
        "artifact_family": "str",
        "changes_live_trading_behavior": "bool",
        "credentials_touched": "bool",
        "evidence_class": "str",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "partition_assignment": "str",
        "promotion_verdict": "str",
        "route_id": "str",
        "schema_version": "str",
        "selected_max_coverage_end_by_symbol": {
          "AUDJPY": "str",
          "AUDUSD": "str",
          "BTCUSD": "str",
          "CHFJPY": "str",
          "ETHUSD": "str",
          "EURGBP": "str",
          "EURJPY": "str",
          "EURUSD": "str",
          "GBPJPY": "str",
          "GBPUSD": "str",
          "GBPUSD_6B": "str",
          "GER40": "str",
          "JP225": "str",
          "NAS100": "str",
          "NAS100_MNQ": "str",
          "NAS100_NQ": "str",
          "NZDUSD": "str",
          "SI": "str",
          "SPX500": "str",
          "SPX_ES": "str",
          "SPX_MES": "str",
          "UK100": "str",
          "UKOIL_cash": "str",
          "US30_MYM": "str",
          "US30_YM": "str",
          "US30_cash": "str",
          "USDCAD": "str",
          "USDCHF": "str",
          "USDJPY": "str",
          "USDJPY_6J": "str",
          "USOIL_cash": "str",
          "VIX": "str",
          "XAGUSD": "str",
          "XAGUSD_SI": "str",
          "XAUUSD": "str",
          "XAUUSD_GC": "str",
          "XAUUSD_MGC": "str",
          "XAUUSD_SCID": "str"
        },
        "selected_source_count": "int",
        "selected_source_coverage_rows": [
          {
            "absolute_path": "str",
            "coverage_end_utc": "NoneType",
            "coverage_start_utc": "NoneType",
            "coverage_status": "str",
            "partition_assignment": "str",
            "repo_relative_path": "str",
            "row_count": "NoneType",
            "source_family": "str",
            "source_row_id": "str",
            "source_selected_in_fpb_discovery": "bool",
            "source_sha256": "str",
            "symbol": "str",
            "timeframe": "str"
          }
        ],
        "validation_safe": "bool"
      },
      "size_bytes": 443822,
      "source_hash": "47da2e95a649e2452090cfe4a689245110fc4155a5c64a4693e210231dbccbfb",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "artifact_family",
        "changes_live_trading_behavior",
        "credentials_touched",
        "evidence_class",
        "generated_at_utc",
        "live_effect",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "partition_assignment",
        "promotion_verdict",
        "route_id",
        "schema_version",
        "selected_max_coverage_end_by_symbol",
        "selected_source_count",
        "selected_source_coverage_rows",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "af03fe054912541d8e67b9a46a6d64db9e27c7a984722be00ef303ad72a7a012",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_SOURCE_ASOF_NOLEAK_LEDGER_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_SOURCE_ASOF_NOLEAK_LEDGER_2026-05-11.json",
      "shape": {
        "artifact_family": "str",
        "candidate_count": "int",
        "candidate_field_audit": [
          {
            "missing_fields": [],
            "source": "str",
            "status": "str",
            "symbol": "str"
          }
        ],
        "changes_live_trading_behavior": "bool",
        "credentials_touched": "bool",
        "evidence_class": "str",
        "forbidden_fields_policy": [
          "str"
        ],
        "generated_at_utc": "str",
        "live_effect": "bool",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "required_candidate_fields": [
          "str"
        ],
        "route_id": "str",
        "schema_version": "str",
        "validation_safe": "bool"
      },
      "size_bytes": 2612,
      "source_hash": "f2c00e667371181e304b0ca24bdc5e458881b19a7242f493ac4940949b47e29f",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "artifact_family",
        "candidate_count",
        "candidate_field_audit",
        "changes_live_trading_behavior",
        "credentials_touched",
        "evidence_class",
        "forbidden_fields_policy",
        "generated_at_utc",
        "live_effect",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "required_candidate_fields",
        "route_id",
        "schema_version",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "cf763c76a435490d9f170324e003c946351432ac85f4cd17e05f8997b0524045",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_TICK_PARQUET_TRIAGE_LEDGER_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_TICK_PARQUET_TRIAGE_LEDGER_2026-05-11.json",
      "shape": {
        "artifact_family": "str",
        "changes_live_trading_behavior": "bool",
        "credentials_touched": "bool",
        "evidence_class": "str",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "route_id": "str",
        "schema_version": "str",
        "tick_parquet_count": "int",
        "tick_parquet_rows": [
          {
            "absolute_path": "str",
            "coverage_end_utc": "str",
            "coverage_start_utc": "str",
            "file_name": "str",
            "no_leak_status": "str",
            "parser_asof_status": "str",
            "partition_assignment": "str",
            "path_depth": "int",
            "rejection_reason": "str",
            "repo_relative_path": "str",
            "size_bytes": "int",
            "source_family": "str",
            "source_sha256": "str",
            "symbol": "str",
            "timeframe": "str",
            "triage_decision": "str"
          }
        ],
        "triage_summary": {
          "FUTURE_SOURCE_POOL_CANDIDATE_REQUIRES_G12_AND_TICK_TO_BAR_CONTRACT": "int",
          "REJECT_CURRENTLY_INSIDE_SELECTED_SOURCE_EMBARGO_OR_FORWARD_CAPTURE_ONLY": "int"
        },
        "validation_safe": "bool"
      },
      "size_bytes": 91377,
      "source_hash": "ac786f86fb3a0f82528235bb3d86d6bd08400989a7d0c5e8ea21b8851e834f09",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "artifact_family",
        "changes_live_trading_behavior",
        "credentials_touched",
        "evidence_class",
        "generated_at_utc",
        "live_effect",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "route_id",
        "schema_version",
        "tick_parquet_count",
        "tick_parquet_rows",
        "triage_summary",
        "validation_safe"
      ]
    },
    {
      "key_shape_fingerprint": "2586a30b319b511fddef08806fb71e7d5ceb3cea1307a6e37b2286ceabaf873a",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_VERIFICATION_RESULT_2026-05-11.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_VERIFICATION_RESULT_2026-05-11.json",
      "shape": {
        "accepted_csv_candidate_count": "int",
        "accepted_native_scid_candidate_count": "int",
        "artifact_family": "str",
        "changes_live_trading_behavior": "bool",
        "check_count": "int",
        "checks": [
          {
            "check": "str",
            "evidence": "str",
            "status": "str"
          }
        ],
        "credentials_touched": "bool",
        "g12_source_pool_audit_prompt": "str",
        "generated_at_utc": "str",
        "live_effect": "bool",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_mt5_order_account_history_behavior": "bool",
        "opens_paid_api_or_databento_route": "bool",
        "opens_promotion": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "route_id": "str",
        "schema_version": "str",
        "terminal_decision": "str",
        "validation_safe": "bool",
        "verification_passed": "bool"
      },
      "size_bytes": 9191,
      "source_hash": "f229d962bb5ece7129f1c6d915c8f1bf9a984d615acac1ec8bf8428c07ba646f",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "accepted_csv_candidate_count",
        "accepted_native_scid_candidate_count",
        "artifact_family",
        "changes_live_trading_behavior",
        "check_count",
        "checks",
        "credentials_touched",
        "g12_source_pool_audit_prompt",
        "generated_at_utc",
        "live_effect",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_mt5_order_account_history_behavior",
        "opens_paid_api_or_databento_route",
        "opens_promotion",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "route_id",
        "schema_version",
        "terminal_decision",
        "validation_safe",
        "verification_passed"
      ]
    },
    {
      "key_shape_fingerprint": "ed399c4f998c6fd977c88362a68723e035c2700251143f6845f0956c71ef55be",
      "lineage": {
        "head_at_build": "3ab07d464082",
        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
        "path": "research/science_program_2026_05/06_outcome_testing/g0exp_r1_local_heavy_root_parser_hash_lineage_source_control/G0EXP_R1_ACTIVE_QUESTION_STACK_ROUTE_DECISION_LEDGER_2026-05-13.json",
        "source_checkout": "current_git_worktree"
      },
      "path": "research/science_program_2026_05/06_outcome_testing/g0exp_r1_local_heavy_root_parser_hash_lineage_source_control/G0EXP_R1_ACTIVE_QUESTION_STACK_ROUTE_DECISION_LEDGER_2026-05-13.json",
      "shape": {
        "active_question_stack": [
          {
            "answer_status": "str",
            "evidence": "str",
            "question": "str",
            "question_id": "str"
          }
        ],
        "adjacent_overflow_decisions": [
          {
            "accepted_40_card_denominator_inclusion": "bool",
            "candidate_family": "str",
            "candidate_id": "str",
            "decision": "str",
            "next_owner": "str",
            "why": "str"
          }
        ],
        "artifact_family": "str",
        "assigned_family_decisions": [
          {
            "accepted_40_card_denominator_inclusion": "bool",
            "candidate_family": "str",
            "candidate_id": "str",
            "decision": "str",
            "may_open_results_now": "bool"
          }
        ],
        "changes_trading_risk_safety_prompt_decision_behavior": "bool",
        "credentials_touched": "bool",
        "evidence_class": "str",
        "generated_at_utc": "str",
        "head_at_build": "str",
        "live_effect": "bool",
        "opens_ai_api": "bool",
        "opens_broker_account_order_history_deal_position_evidence": "bool",
        "opens_live_restart": "bool",
        "opens_live_trading_behavior": "bool",
        "opens_paid_or_vendor_access": "bool",
        "opens_prompt_config_risk_safety_execution_canary_selector_edit": "bool",
        "opens_raw_market_data_blob_commit": "bool",
        "opens_registry_edit": "bool",
        "opens_remote_push": "bool",
        "opens_result_scoring": "bool",
        "opens_strategy_edge_claims": "bool",
        "opens_validation": "bool",
        "outcome_review_opened": "bool",
        "promotion_verdict": "str",
        "route_id": "str",
        "route_posture": "str",
        "schema_version": "str",
        "terminal_decision": "str",
        "validation_safe": "bool"
      },
      "size_bytes": 7075,
      "source_hash": "d214171a1621ad76ce943dac01c5240de05e0df748712f6076a7ab4cf1620e19",
      "source_status": "HASHED_SCHEMA_CONTROL_FILE",
      "top_level_keys": [
        "active_question_stack",
        "adjacent_overflow_decisions",
        "artifact_family",
        "assigned_family_decisions",
        "changes_trading_risk_safety_prompt_decision_behavior",
        "credentials_touched",
        "evidence_class",
        "generated_at_utc",
        "head_at_build",
        "live_effect",
        "opens_ai_api",
        "opens_broker_account_order_history_deal_position_evidence",
        "opens_live_restart",
        "opens_live_trading_behavior",
        "opens_paid_or_vendor_access",
        "opens_prompt_config_risk_safety_execution_canary_selector_edit",
        "opens_raw_market_data_blob_commit",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_strategy_edge_claims",
        "opens_validation",
        "outcome_review_opened",
        "promotion_verdict",
        "route_id",
        "route_posture",
        "schema_version",
        "terminal_decision",
        "validation_safe"
      ]
    }
  ],
  "schema_version": "g0exp_r1_local_heavy_root_parser_hash_lineage_source_control_v1",
  "validation_safe": false
}
```
