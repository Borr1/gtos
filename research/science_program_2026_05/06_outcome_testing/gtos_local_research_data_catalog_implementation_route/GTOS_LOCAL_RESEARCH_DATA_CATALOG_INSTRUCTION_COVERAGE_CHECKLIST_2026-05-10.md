# Instruction Coverage Checklist

Route: `GTOS_LOCAL_RESEARCH_DATA_CATALOG_IMPLEMENTATION_ROUTE`
Terminal decision: `ACCEPT_AS_LOCAL_RESEARCH_DATA_CATALOG_TOOLING`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "artifact_family": "instruction_coverage_checklist",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T09:31:31Z",
  "live_effect": false,
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
  "requirement_count": 12,
  "requirements": [
    {
      "evidence": "Context anchor records prompt path, HEAD, preflight docs, and boundaries.",
      "requirement_id": "preflight_context_anchor",
      "status": "satisfied"
    },
    {
      "evidence": "Machine-readable root config and schema emitted.",
      "requirement_id": "root_resolver_config_schema",
      "status": "satisfied"
    },
    {
      "evidence": "Catalog JSONL emitted from bounded read-only scan.",
      "requirement_id": "catalog_jsonl",
      "status": "satisfied"
    },
    {
      "evidence": "Configured query search-result ledger emitted with positive and negative evidence.",
      "requirement_id": "search_result_ledger",
      "status": "satisfied"
    },
    {
      "evidence": "Requested windows routed with exact next actions.",
      "requirement_id": "missing_window_ledger",
      "status": "satisfied"
    },
    {
      "evidence": "Acquisition manifest schema and example emitted.",
      "requirement_id": "acquisition_manifest",
      "status": "satisfied"
    },
    {
      "evidence": "Recoverable market data separated from non-generatable source-state truth.",
      "requirement_id": "recoverable_non_generatable",
      "status": "satisfied"
    },
    {
      "evidence": "Small-file SHA256 hashes and large-file deferrals emitted.",
      "requirement_id": "hash_deferral_manifest",
      "status": "satisfied"
    },
    {
      "evidence": "No-leak and forbidden live-surface audit emitted.",
      "requirement_id": "noleak_audit",
      "status": "satisfied"
    },
    {
      "evidence": "Future goal prompt guide emitted.",
      "requirement_id": "integration_guide",
      "status": "satisfied"
    },
    {
      "evidence": "Verifier and focused tests present.",
      "requirement_id": "verifier_tests",
      "status": "satisfied"
    },
    {
      "evidence": "NO_PROMOTION_VERDICT and closed flags preserved.",
      "requirement_id": "safe_flags",
      "status": "satisfied"
    }
  ],
  "route_id": "GTOS_LOCAL_RESEARCH_DATA_CATALOG_IMPLEMENTATION_ROUTE",
  "schema_version": "gtos_local_research_data_catalog_implementation_route_v1",
  "terminal_decision": "ACCEPT_AS_LOCAL_RESEARCH_DATA_CATALOG_TOOLING",
  "validation_safe": false
}
```
