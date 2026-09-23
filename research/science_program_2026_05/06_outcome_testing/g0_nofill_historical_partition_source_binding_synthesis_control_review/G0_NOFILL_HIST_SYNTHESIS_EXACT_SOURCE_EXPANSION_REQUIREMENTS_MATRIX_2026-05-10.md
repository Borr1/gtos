# Exact Source Expansion Requirements Matrix

Route: `G0_NOFILL_HISTORICAL_PARTITION_SOURCE_BINDING_SYNTHESIS_CONTROL_REVIEW`
Terminal decision: `ACCEPT_AS_G0_SOURCE_CONTROL_SYNTHESIS_FOR_NEXT_SEALED_SOURCE_EXPANSION`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "artifact_family": "exact_source_expansion_requirements_matrix",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T04:31:04Z",
  "live_effect": false,
  "matrix": [
    {
      "asof_policy": "all fields must be available at decision/capture as-of or carry fail-closed missing status",
      "duplicate_policy": "exclude contaminated packet/source IDs, nofill duplicate keys, duplicate groups, source dates, and one-day embargo overlaps",
      "field_count_target": 55,
      "field_requirement": "55/55 field checklist required per row; 17 source-bound fields preserved, 20 extracted or fail-closed, 11 schema-only, 7 redacted status-only.",
      "g12_acceptance_requirement": "mandatory before validation execution",
      "owner_access_requirement": [
        "source hash manifest for every consumed tick/shadow/source file",
        "frozen source-bound NOFILL candidate packet",
        "55-field binding checklist per row",
        "duplicate key and duplicate group ledgers",
        "forbidden field scan",
        "G12 audit prompt pack"
      ],
      "rank": 1,
      "result_or_cost_scoring_allowed": false,
      "route_class": "source_expansion_builder",
      "route_id": "NOFILL_HISTORICAL_SOURCE_EXPANSION_BUILDER_LOCAL_TICK_SHADOW_PACKET",
      "source_hash_policy": "SHA256 every consumed raw/source/log/parser artifact before row admission",
      "source_roots": [
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs",
        "current worktree committed source-control artifacts"
      ],
      "validation_execution_allowed": false
    },
    {
      "asof_policy": "all fields must be available at decision/capture as-of or carry fail-closed missing status",
      "duplicate_policy": "exclude contaminated packet/source IDs, nofill duplicate keys, duplicate groups, source dates, and one-day embargo overlaps",
      "field_count_target": null,
      "field_requirement": "context fields only until proxy transfer/as-of contract is G12 accepted",
      "g12_acceptance_requirement": "mandatory before joining to NOFILL packet",
      "owner_access_requirement": [
        "Sierra parser/source hash manifest",
        "proxy transfer contract by symbol",
        "as-of timestamp convention",
        "separation from GTOS broker NOFILL labels"
      ],
      "rank": 2,
      "result_or_cost_scoring_allowed": false,
      "route_class": "source_contract_and_context_packet",
      "route_id": "NOFILL_SIERRA_FUTURES_PROXY_CONTEXT_SOURCE_EXPANSION",
      "source_hash_policy": "SHA256 every consumed raw/source/log/parser artifact before row admission",
      "source_roots": [
        "C:\\SierraChart\\Data",
        "C:\\SierraChart\\Data\\MarketDepthData"
      ],
      "validation_execution_allowed": false
    },
    {
      "asof_policy": "all fields must be available at decision/capture as-of or carry fail-closed missing status",
      "duplicate_policy": "exclude contaminated packet/source IDs, nofill duplicate keys, duplicate groups, source dates, and one-day embargo overlaps",
      "field_count_target": null,
      "field_requirement": "control evidence only",
      "g12_acceptance_requirement": "mandatory before any broader use",
      "owner_access_requirement": [
        "owner/current-process state check",
        "first-row schema verification",
        "forward pool separation from historical sealed validation"
      ],
      "rank": 3,
      "result_or_cost_scoring_allowed": false,
      "route_class": "forward_shadow_source_capture",
      "route_id": "NOFILL_FORWARD_SOURCE_CAPTURE_NEXT_CANDIDATE_PACKET",
      "source_hash_policy": "SHA256 every consumed raw/source/log/parser artifact before row admission",
      "source_roots": [
        "shadow_logs\\nofill_forward_source_capture.jsonl"
      ],
      "validation_execution_allowed": false
    },
    {
      "asof_policy": "all fields must be available at decision/capture as-of or carry fail-closed missing status",
      "duplicate_policy": "exclude contaminated packet/source IDs, nofill duplicate keys, duplicate groups, source dates, and one-day embargo overlaps",
      "field_count_target": null,
      "field_requirement": "control evidence only",
      "g12_acceptance_requirement": "mandatory before any broader use",
      "owner_access_requirement": [
        "prior artifact hash ledger",
        "contradiction ledger",
        "proof that no row is admitted solely from stale worktree output"
      ],
      "rank": 4,
      "result_or_cost_scoring_allowed": false,
      "route_class": "source_control_reconciliation",
      "route_id": "NOFILL_PRIOR_WORKTREE_ARTIFACT_RECONCILIATION_CONTROL_ROUTE",
      "source_hash_policy": "SHA256 every consumed raw/source/log/parser artifact before row admission",
      "source_roots": [
        "C:\\tmp\\gtos_otb"
      ],
      "validation_execution_allowed": false
    },
    {
      "asof_policy": "all fields must be available at decision/capture as-of or carry fail-closed missing status",
      "duplicate_policy": "exclude contaminated packet/source IDs, nofill duplicate keys, duplicate groups, source dates, and one-day embargo overlaps",
      "field_count_target": null,
      "field_requirement": "control evidence only",
      "g12_acceptance_requirement": "mandatory before any broader use",
      "owner_access_requirement": [
        "separate owner-approved evidence-class prompt if ever needed"
      ],
      "rank": 5,
      "result_or_cost_scoring_allowed": false,
      "route_class": "forbidden_here",
      "route_id": "BROKER_ACCOUNT_HISTORY_OR_RESULT_LABEL_ROUTE",
      "source_hash_policy": "SHA256 every consumed raw/source/log/parser artifact before row admission",
      "source_roots": [],
      "validation_execution_allowed": false
    }
  ],
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
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G0_NOFILL_HISTORICAL_PARTITION_SOURCE_BINDING_SYNTHESIS_CONTROL_REVIEW",
  "schema_version": "g0_nofill_historical_partition_source_binding_synthesis_control_review_v1",
  "universal_admission_requirements": [
    "frozen controlling prompt before outcome opening",
    "source hash manifest",
    "parser code hash",
    "55-field binding per admitted row when route is NOFILL candidate packet",
    "duplicate/purge/embargo ledger",
    "forbidden field scan",
    "zero broker actual-R/account-history fields",
    "G12 source/control acceptance before any validation execution prompt"
  ],
  "validation_safe": false
}
```
