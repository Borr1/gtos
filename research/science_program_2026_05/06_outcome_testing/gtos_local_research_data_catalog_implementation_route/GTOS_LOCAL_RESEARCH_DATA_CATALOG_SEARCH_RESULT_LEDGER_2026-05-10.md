# Search Result Ledger

Route: `GTOS_LOCAL_RESEARCH_DATA_CATALOG_IMPLEMENTATION_ROUTE`
Terminal decision: `ACCEPT_AS_LOCAL_RESEARCH_DATA_CATALOG_TOOLING`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "artifact_family": "search_result_ledger",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T09:31:31Z",
  "live_effect": false,
  "negative_query_count": 4,
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_mt5_order_account_history_behavior": false,
  "opens_paid_api_or_databento_route": false,
  "opens_promotion": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "positive_query_count": 2,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "query_count": 6,
  "route_id": "GTOS_LOCAL_RESEARCH_DATA_CATALOG_IMPLEMENTATION_ROUTE",
  "rows": [
    {
      "match_count": 1,
      "negative_evidence": [],
      "positive_evidence": [
        {
          "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-08.parquet",
          "catalog_row_id": "LCAT-000668",
          "hash_status": "deferred_large_file_requires_dedicated_hash_manifest",
          "root_id": "absolute_main_tick_root",
          "sha256": null
        }
      ],
      "purpose": "NOFILL source-expansion fixture tick file search",
      "query": {
        "extensions": [
          ".parquet"
        ],
        "purpose": "NOFILL source-expansion fixture tick file search",
        "query_id": "accepted_fixture_nas100_tick_2026_05_08",
        "source_date": "2026-05-08",
        "source_family_contains": "tick",
        "symbol": "NAS100"
      },
      "query_id": "accepted_fixture_nas100_tick_2026_05_08",
      "roots_searched": [
        "current_worktree_data_root",
        "current_worktree_tick_root",
        "current_worktree_shadow_logs",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "absolute_main_data_root",
        "absolute_main_tick_root",
        "absolute_main_shadow_logs",
        "absolute_main_exports",
        "absolute_main_external_data",
        "prior_worktree_root",
        "sierra_chart_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "owner_documents_candidate_root"
      ]
    },
    {
      "match_count": 1,
      "negative_evidence": [],
      "positive_evidence": [
        {
          "absolute_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\US30_cash\\2026-05-08.parquet",
          "catalog_row_id": "LCAT-000680",
          "hash_status": "sha256_complete",
          "root_id": "absolute_main_tick_root",
          "sha256": "bfed917d099ba990458319e4c607e405e3a53de458be13d9dc893be011fc4cd6"
        }
      ],
      "purpose": "NOFILL source-expansion fixture tick file search",
      "query": {
        "extensions": [
          ".parquet"
        ],
        "purpose": "NOFILL source-expansion fixture tick file search",
        "query_id": "accepted_fixture_us30_cash_tick_2026_05_08",
        "source_date": "2026-05-08",
        "source_family_contains": "tick",
        "symbol": "US30_cash"
      },
      "query_id": "accepted_fixture_us30_cash_tick_2026_05_08",
      "roots_searched": [
        "current_worktree_data_root",
        "current_worktree_tick_root",
        "current_worktree_shadow_logs",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "absolute_main_data_root",
        "absolute_main_tick_root",
        "absolute_main_shadow_logs",
        "absolute_main_exports",
        "absolute_main_external_data",
        "prior_worktree_root",
        "sierra_chart_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "owner_documents_candidate_root"
      ]
    },
    {
      "match_count": 0,
      "negative_evidence": [
        {
          "classification": "not_recovered_in_bounded_local_catalog_scan",
          "exact_next_action": "route_to_missing_window_or_acquisition_manifest_if required_by_lane",
          "searched_roots": [
            "current_worktree_data_root",
            "current_worktree_tick_root",
            "current_worktree_shadow_logs",
            "current_worktree_exports",
            "current_worktree_external_data",
            "current_worktree_science_routes",
            "absolute_main_data_root",
            "absolute_main_tick_root",
            "absolute_main_shadow_logs",
            "absolute_main_exports",
            "absolute_main_external_data",
            "prior_worktree_root",
            "sierra_chart_root",
            "sierra_chart_data_root",
            "sierra_chart_depth_root",
            "owner_documents_candidate_root"
          ]
        }
      ],
      "positive_evidence": [],
      "purpose": "recoverable market-data absence example",
      "query": {
        "extensions": [
          ".parquet"
        ],
        "purpose": "recoverable market-data absence example",
        "query_id": "upstream_missing_gbpjpy_tick_2026_04_14",
        "source_date": "2026-04-14",
        "source_family_contains": "tick",
        "symbol": "GBPJPY"
      },
      "query_id": "upstream_missing_gbpjpy_tick_2026_04_14",
      "roots_searched": [
        "current_worktree_data_root",
        "current_worktree_tick_root",
        "current_worktree_shadow_logs",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "absolute_main_data_root",
        "absolute_main_tick_root",
        "absolute_main_shadow_logs",
        "absolute_main_exports",
        "absolute_main_external_data",
        "prior_worktree_root",
        "sierra_chart_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "owner_documents_candidate_root"
      ]
    },
    {
      "match_count": 0,
      "negative_evidence": [
        {
          "classification": "not_recovered_in_bounded_local_catalog_scan",
          "exact_next_action": "route_to_missing_window_or_acquisition_manifest_if required_by_lane",
          "searched_roots": [
            "current_worktree_data_root",
            "current_worktree_tick_root",
            "current_worktree_shadow_logs",
            "current_worktree_exports",
            "current_worktree_external_data",
            "current_worktree_science_routes",
            "absolute_main_data_root",
            "absolute_main_tick_root",
            "absolute_main_shadow_logs",
            "absolute_main_exports",
            "absolute_main_external_data",
            "prior_worktree_root",
            "sierra_chart_root",
            "sierra_chart_data_root",
            "sierra_chart_depth_root",
            "owner_documents_candidate_root"
          ]
        }
      ],
      "positive_evidence": [],
      "purpose": "current acceptance-fixture G12 source-control route artifact search",
      "query": {
        "extensions": [
          ".json",
          ".md",
          ".py"
        ],
        "path_contains": "g12_nofill_historical_source_expansion_hash_repair_reaudit",
        "purpose": "current acceptance-fixture G12 source-control route artifact search",
        "query_id": "g12_hash_repair_reaudit_manifest"
      },
      "query_id": "g12_hash_repair_reaudit_manifest",
      "roots_searched": [
        "current_worktree_data_root",
        "current_worktree_tick_root",
        "current_worktree_shadow_logs",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "absolute_main_data_root",
        "absolute_main_tick_root",
        "absolute_main_shadow_logs",
        "absolute_main_exports",
        "absolute_main_external_data",
        "prior_worktree_root",
        "sierra_chart_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "owner_documents_candidate_root"
      ]
    },
    {
      "match_count": 0,
      "negative_evidence": [
        {
          "classification": "not_recovered_in_bounded_local_catalog_scan",
          "exact_next_action": "route_to_missing_window_or_acquisition_manifest_if required_by_lane",
          "searched_roots": [
            "current_worktree_data_root",
            "current_worktree_tick_root",
            "current_worktree_shadow_logs",
            "current_worktree_exports",
            "current_worktree_external_data",
            "current_worktree_science_routes",
            "absolute_main_data_root",
            "absolute_main_tick_root",
            "absolute_main_shadow_logs",
            "absolute_main_exports",
            "absolute_main_external_data",
            "prior_worktree_root",
            "sierra_chart_root",
            "sierra_chart_data_root",
            "sierra_chart_depth_root",
            "owner_documents_candidate_root"
          ]
        }
      ],
      "positive_evidence": [],
      "purpose": "upstream 198-row prototype catalog source search",
      "query": {
        "extensions": [
          ".jsonl"
        ],
        "path_contains": "GTOS_CAP_LIMIT_CLOSURE_LOCAL_RESEARCH_DATA_CATALOG_PROTOTYPE",
        "purpose": "upstream 198-row prototype catalog source search",
        "query_id": "cap_limit_catalog_prototype"
      },
      "query_id": "cap_limit_catalog_prototype",
      "roots_searched": [
        "current_worktree_data_root",
        "current_worktree_tick_root",
        "current_worktree_shadow_logs",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "absolute_main_data_root",
        "absolute_main_tick_root",
        "absolute_main_shadow_logs",
        "absolute_main_exports",
        "absolute_main_external_data",
        "prior_worktree_root",
        "sierra_chart_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "owner_documents_candidate_root"
      ]
    },
    {
      "match_count": 0,
      "negative_evidence": [
        {
          "classification": "not_recovered_in_bounded_local_catalog_scan",
          "exact_next_action": "route_to_missing_window_or_acquisition_manifest_if required_by_lane",
          "searched_roots": [
            "current_worktree_data_root",
            "current_worktree_tick_root",
            "current_worktree_shadow_logs",
            "current_worktree_exports",
            "current_worktree_external_data",
            "current_worktree_science_routes",
            "absolute_main_data_root",
            "absolute_main_tick_root",
            "absolute_main_shadow_logs",
            "absolute_main_exports",
            "absolute_main_external_data",
            "prior_worktree_root",
            "sierra_chart_root",
            "sierra_chart_data_root",
            "sierra_chart_depth_root",
            "owner_documents_candidate_root"
          ]
        }
      ],
      "positive_evidence": [],
      "purpose": "Sierra local cache source discovery",
      "query": {
        "extensions": [
          ".scid",
          ".depth"
        ],
        "purpose": "Sierra local cache source discovery",
        "query_id": "sierra_nq_or_nqm26_depth_or_scid",
        "symbol_any": [
          "NQ",
          "NQM26"
        ]
      },
      "query_id": "sierra_nq_or_nqm26_depth_or_scid",
      "roots_searched": [
        "current_worktree_data_root",
        "current_worktree_tick_root",
        "current_worktree_shadow_logs",
        "current_worktree_exports",
        "current_worktree_external_data",
        "current_worktree_science_routes",
        "absolute_main_data_root",
        "absolute_main_tick_root",
        "absolute_main_shadow_logs",
        "absolute_main_exports",
        "absolute_main_external_data",
        "prior_worktree_root",
        "sierra_chart_root",
        "sierra_chart_data_root",
        "sierra_chart_depth_root",
        "owner_documents_candidate_root"
      ]
    }
  ],
  "schema_version": "gtos_local_research_data_catalog_implementation_route_v1",
  "terminal_decision": "ACCEPT_AS_LOCAL_RESEARCH_DATA_CATALOG_TOOLING",
  "validation_safe": false
}
```
