# GTOS Contamination And Embargo Router

Route: `GTOS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE`
Terminal decision: `ACCEPT_AS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "artifact_family": "contamination_embargo_router",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "denominator_guard": {
    "blocked_rows_count_as": "source_control_blockers_only",
    "contaminated_rows_count_as": "forensics_or_fixture_only",
    "rejects_count_as": "source_control_rejects_only",
    "sealed_validation_denominator_requires": [
      "source_hash",
      "as_of_rule",
      "duplicate_policy",
      "purge_check",
      "embargo_check",
      "G12_source_control_acceptance",
      "separate_validation_prompt"
    ]
  },
  "generated_at_utc": "2026-05-10T06:33:15Z",
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
  "rejected_row_routes": [
    {
      "allowed_use": "mechanism forensics and prompt hardening",
      "denominator_status": "excluded_from_validation_and_promotion",
      "route": "discovery_only"
    },
    {
      "allowed_use": "source failure anatomy and capture requirement design",
      "denominator_status": "excluded_from_validation_and_promotion",
      "route": "forensics_only"
    },
    {
      "allowed_use": "parser, redaction, no-leak, and source-binding tests",
      "denominator_status": "excluded_from_validation_and_promotion",
      "route": "source_contract_fixture"
    },
    {
      "allowed_use": "robustness design after labels are separated",
      "denominator_status": "excluded_from_sealed_validation_denominator",
      "route": "stress_control"
    }
  ],
  "route_id": "GTOS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE",
  "schema_version": "gtos_research_capability_limitation_closure_control_route_v1",
  "sealed_partition_expansion_plan": [
    "Build untouched row/window/symbol/session inventory before outcome opening.",
    "Purge packet row id, source row id, duplicate key, duplicate group, source date, and one-day same-symbol source-lane overlap.",
    "Prefer new source-hashed windows over relabeling contaminated rows.",
    "Route dirty rows to fixture or forensics use rather than sealed denominator use."
  ],
  "state_machine": [
    {
      "allowed_next": [
        "SOURCE_HASHED",
        "REJECTED_SOURCE_INVALID"
      ],
      "state": "SOURCE_DISCOVERED"
    },
    {
      "allowed_next": [
        "PURGE_CHECKED",
        "SOURCE_CONTRACT_FIXTURE"
      ],
      "state": "SOURCE_HASHED"
    },
    {
      "allowed_next": [
        "EMBARGO_CHECKED",
        "CONTAMINATED_QUARANTINE"
      ],
      "state": "PURGE_CHECKED"
    },
    {
      "allowed_next": [
        "SEALED_CANDIDATE",
        "EMBARGO_EXCLUDED"
      ],
      "state": "EMBARGO_CHECKED"
    },
    {
      "allowed_next": [
        "G12_SOURCE_CONTROL_AUDIT"
      ],
      "state": "SEALED_CANDIDATE"
    },
    {
      "allowed_next": [
        "G0_SYNTHESIS_OR_NEXT_EVIDENCE_PROMPT"
      ],
      "state": "G12_SOURCE_CONTROL_AUDIT"
    }
  ],
  "terminal_decision": "ACCEPT_AS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE",
  "validation_safe": false
}
```
