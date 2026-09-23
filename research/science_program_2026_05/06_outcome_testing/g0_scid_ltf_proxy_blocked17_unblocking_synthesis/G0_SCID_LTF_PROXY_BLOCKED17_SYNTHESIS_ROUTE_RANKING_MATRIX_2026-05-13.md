# Route Ranking Matrix

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

## Machine Payload

```json
{
  "anti_boxing_policy": "Current GTOS/OB behavior is not a ranking ceiling; proxy-context, LTF path, orderflow, execution, uncertainty, macro/session, and non-generatable source-state routes remain first-class source-control routes.",
  "artifact_family": "ROUTE_RANKING_MATRIX",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G0_SCID_LTF_PROXY_BLOCKED17_UNBLOCKING_SYNTHESIS_ONLY",
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
  "ranked_routes": [
    {
      "card_count_touched": 13,
      "card_ids_touched": [
        "ADV-002",
        "EXE-001",
        "EXE-003",
        "EXE-005",
        "GEO-002",
        "GEO-003",
        "GEO-004",
        "HAZ-003",
        "HAZ-004",
        "MIC-002",
        "MIC-005",
        "UNC-001",
        "UNC-005"
      ],
      "dependency_count": 13,
      "future_result_gate": "Closed until parser packet is G12-accepted and duplicate policy/baseline controls are frozen.",
      "live_effect": false,
      "may_open_results_now": false,
      "outcome_review_opened": false,
      "parallel_group": "A",
      "prompt_filename": "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE_GOAL_PROMPT_2026-05-13.md",
      "rank": 1,
      "route_family": "LTF parser/hash/as-of packet construction",
      "route_id": "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE",
      "same_class_pursuit_done_here": "Accepted rows, field statuses, source roots, and source inventory were inspected; materialization is reduced to exact parser prompt because implementation is the next source-control builder gate.",
      "starter_filename": "SCID_LTF_ASOF_PATH_PARSER_HASH_MATERIALIZATION_ROUTE_STARTER_2026-05-13.txt",
      "status_counts": {
        "SOURCE_EXISTS_NEEDS_PARSER": 91
      },
      "terminal_closure": "all SOURCE_EXISTS_NEEDS_PARSER lower-timeframe dependencies either materialized as source-control rows or reduced to exact parser/source/hash/as-of blockers",
      "validation_safe": false,
      "why_ranked": "Largest recoverable same-evidence-class unlock: source exists for LTF path fields, but parser/hash/as-of materialization is missing.",
      "write_scope": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_asof_path_parser_hash_materialization_route/"
      ]
    },
    {
      "card_count_touched": 8,
      "card_ids_touched": [
        "EXE-005",
        "MAC-003",
        "MIC-001",
        "MIC-002",
        "MIC-003",
        "MIC-004",
        "MIC-005",
        "UNC-001"
      ],
      "dependency_count": 8,
      "future_result_gate": "Closed until future G12 accepts contract/month/source-family/parser/hash/as-of and non-equivalence controls.",
      "live_effect": false,
      "may_open_results_now": false,
      "outcome_review_opened": false,
      "parallel_group": "B",
      "prompt_filename": "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE_GOAL_PROMPT_2026-05-13.md",
      "rank": 2,
      "route_family": "proxy-validity contract design and orderflow context packet",
      "route_id": "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE",
      "same_class_pursuit_done_here": "Sierra, Databento, and proxy-registry source families plus equivalence rows were inspected; remaining work is exact source-family/parser/non-equivalence contract building.",
      "starter_filename": "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE_STARTER_2026-05-13.txt",
      "status_counts": {
        "PROXY_VALIDITY_REQUIRES_CONTRACT": 72
      },
      "terminal_closure": "every PROXY_VALIDITY_REQUIRES_CONTRACT dependency has a G12-ready source-family/parser/hash/as-of/non-equivalence contract or an exact access requirement",
      "validation_safe": false,
      "why_ranked": "Highest non-OB/context route: orderflow/depth/proxy source inventory is broad, but every proxy row remains non-equivalent context/control until transfer and parser contracts are accepted.",
      "write_scope": [
        "research/science_program_2026_05/06_outcome_testing/scid_orderflow_proxy_validity_contract_and_context_packet_route/"
      ]
    },
    {
      "card_count_touched": 10,
      "card_ids_touched": [
        "EXE-003",
        "GEO-003",
        "GEO-004",
        "HAZ-003",
        "HAZ-004",
        "MAC-003",
        "MIC-003",
        "MIC-004",
        "UNC-001",
        "UNC-005"
      ],
      "dependency_count": 8,
      "future_result_gate": "Closed until explicit source-safe logs or prospective capture verifier fixtures are accepted.",
      "live_effect": false,
      "may_open_results_now": false,
      "outcome_review_opened": false,
      "parallel_group": "C",
      "prompt_filename": "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE_GOAL_PROMPT_2026-05-13.md",
      "rank": 3,
      "route_family": "prospective capture for non-generatable strategy/source-state fields",
      "route_id": "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE",
      "same_class_pursuit_done_here": "Existing accepted future-capture/source-state materialization lanes were treated as source-state/control examples, not result unblocks.",
      "starter_filename": "SCID_NON_GENERATABLE_SOURCE_STATE_PROSPECTIVE_CAPTURE_ROUTE_STARTER_2026-05-13.txt",
      "status_counts": {
        "NON_GENERATABLE_HISTORICAL_SOURCE_STATE": 43,
        "PROSPECTIVE_CAPTURE_REQUIRED": 25
      },
      "terminal_closure": "every NON_GENERATABLE_HISTORICAL_SOURCE_STATE dependency is either recovered from explicit source-safe logs or converted into exact prospective capture fields and verifier fixtures",
      "validation_safe": false,
      "why_ranked": "Non-generatable historical strategy/source-state fields cannot be honestly derived from market data, but can be closed prospectively through capture contracts and fixtures.",
      "write_scope": [
        "research/science_program_2026_05/06_outcome_testing/scid_non_generatable_source_state_prospective_capture_route/"
      ]
    },
    {
      "card_count_touched": 5,
      "card_ids_touched": [
        "HAZ-004",
        "MAC-003",
        "MIC-004",
        "UNC-001",
        "UNC-005"
      ],
      "dependency_count": 5,
      "future_result_gate": "Closed until baseline seed, denominator ownership, duplicate key, and no-outcome controls are frozen.",
      "live_effect": false,
      "may_open_results_now": false,
      "outcome_review_opened": false,
      "parallel_group": "D",
      "prompt_filename": "SCID_BASELINE_CONTROL_PACKET_REPAIR_AND_DUPLICATE_POLICY_ROUTE_GOAL_PROMPT_2026-05-13.md",
      "rank": 4,
      "route_family": "baseline/control packet repair",
      "route_id": "SCID_BASELINE_CONTROL_PACKET_REPAIR_AND_DUPLICATE_POLICY_ROUTE",
      "same_class_pursuit_done_here": "Baseline/control fields were separated from market data and routed to packet metadata controls, not parser work.",
      "starter_filename": "SCID_BASELINE_CONTROL_PACKET_REPAIR_AND_DUPLICATE_POLICY_ROUTE_STARTER_2026-05-13.txt",
      "status_counts": {
        "PROSPECTIVE_CAPTURE_REQUIRED": 5
      },
      "terminal_closure": "baseline seed, duplicate policy, denominator ownership, and no-outcome baseline controls are frozen for all 17 cards without touching ready-8 or expansion denominators",
      "validation_safe": false,
      "why_ranked": "Small but necessary denominator-control route for baseline seeds and duplicate policy before any result-opening gate.",
      "write_scope": [
        "research/science_program_2026_05/06_outcome_testing/scid_baseline_control_packet_repair_and_duplicate_policy_route/"
      ]
    },
    {
      "card_count_touched": 17,
      "card_ids_touched": [
        "ADV-002",
        "EXE-001",
        "EXE-003",
        "EXE-005",
        "GEO-002",
        "GEO-003",
        "GEO-004",
        "HAZ-003",
        "HAZ-004",
        "MAC-003",
        "MIC-001",
        "MIC-002",
        "MIC-003",
        "MIC-004",
        "MIC-005",
        "UNC-001",
        "UNC-005"
      ],
      "dependency_count": 0,
      "future_result_gate": "Closed until owner/access/export requirements are explicit and no raw market blob commits are verified.",
      "live_effect": false,
      "may_open_results_now": false,
      "outcome_review_opened": false,
      "parallel_group": "E",
      "prompt_filename": "SCID_OWNER_ACCESS_EXPORT_REQUIREMENT_AND_NO_COMMIT_HASH_ROUTE_GOAL_PROMPT_2026-05-13.md",
      "rank": 5,
      "route_family": "owner/access/export and no-commit hash requirements",
      "route_id": "SCID_OWNER_ACCESS_EXPORT_REQUIREMENT_AND_NO_COMMIT_HASH_ROUTE",
      "same_class_pursuit_done_here": "Local-heavy probes and source inventory hash-deferral classes were inspected; exact no-commit hash/export manifests are the correct next closure.",
      "starter_filename": "SCID_OWNER_ACCESS_EXPORT_REQUIREMENT_AND_NO_COMMIT_HASH_ROUTE_STARTER_2026-05-13.txt",
      "status_counts": {
        "HASHED_NOW": 11932,
        "HASHED_NOW_EXISTING_LOCAL_SMALL_RAW_SOURCE_NO_RAW_COMMIT_ADDED": 180,
        "HASH_DEFERRED_LARGE_SUPPORTING_FILE": 491,
        "HASH_DEFERRED_RAW_MARKET_BLOB_OR_LARGE_EXTERNAL_FILE": 421
      },
      "terminal_closure": "all access/export/raw-parse/hash-deferral blockers are reduced to exact commands/manifests with no raw blob commits and no paid/API/broker account/order evidence",
      "validation_safe": false,
      "why_ranked": "Access/hash route prevents raw-blob leakage and makes any Sierra/vendor/local-heavy extraction auditable without committing raw data.",
      "write_scope": [
        "research/science_program_2026_05/06_outcome_testing/scid_owner_access_export_requirement_and_no_commit_hash_route/"
      ]
    }
  ],
  "ranking_policy": "Rank by recoverability, card coverage, ability to clear source-control blockers without crossing into result scoring, and anti-boxing value across LTF/orderflow/proxy/non-OB/context routes.",
  "route_id": "G0_SCID_LTF_PROXY_BLOCKED17_UNBLOCKING_SYNTHESIS",
  "schema_version": "g0_scid_ltf_proxy_blocked17_unblocking_synthesis_v1",
  "validation_safe": false
}
```
