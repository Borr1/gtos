# GTOS Parser And Hash Drift Control Policy

Route: `GTOS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE`
Terminal decision: `ACCEPT_AS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "artifact_family": "parser_hash_drift_control_policy",
  "binary_text_artifact_gate": [
    {
      "artifact_class": "parquet_scid_depth_binary",
      "hash_rule": "raw_sha256",
      "normalization": "not_applicable"
    },
    {
      "artifact_class": "json_jsonl_md_py_text",
      "hash_rule": "raw_sha256",
      "normalization": "lf_normalized_sha256_optional_for_drift_audit"
    }
  ],
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "generated_artifact_regeneration_policy": [
    "Generated artifacts may change only through the route builder.",
    "If generator code changes, rerun builder, verifier, and focused tests.",
    "If only generated timestamp or LIVE_STATE freshness changes, classify as context volatility unless row semantics or parser bindings changed."
  ],
  "generated_at_utc": "2026-05-10T06:33:15Z",
  "live_effect": false,
  "mutable_context_classification": [
    {
      "class": "STRICT_HASH_REQUIRED",
      "examples": [
        "builder",
        "parser",
        "verifier",
        "focused tests",
        "source packet"
      ],
      "verifier_action": "fail until manifest repaired"
    },
    {
      "class": "GENERATED_CONTEXT_VOLATILE",
      "examples": [
        ".context/LIVE_STATE.md"
      ],
      "verifier_action": "do not fail strict parser hash; record freshness separately"
    },
    {
      "class": "RUNTIME_STATUS_MUTABLE_EXCLUDED",
      "examples": [
        "shadow log freshness tables"
      ],
      "verifier_action": "exclude from strict source packet parser hash"
    },
    {
      "class": "RAW_SOURCE_IMMUTABLE_ONCE_CONSUMED",
      "examples": [
        "packet input source file"
      ],
      "verifier_action": "fail if raw SHA changes"
    }
  ],
  "next_repair_route_template": {
    "allowed_actions": [
      "refresh source-hash manifest",
      "refresh parser_code_hash fields",
      "prove semantic no-row-change",
      "rerun verifier/tests"
    ],
    "forbidden_actions": [
      "add rows",
      "score outcomes",
      "change live behavior",
      "touch broker account/order/history"
    ],
    "prompt_name": "GTOS_SOURCE_CONTROL_PARSER_HASH_REPAIR_REBUILD"
  },
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
  "raw_sha_versus_lf_normalized_text_sha_policy": {
    "binary_artifacts": "raw_sha256_required",
    "markdown_policy_docs": "raw_sha256 plus lf_normalized_text_sha256 for line-ending drift diagnosis",
    "parser_code": "raw_sha256_required_for_strict_execution_binding",
    "text_artifacts": "raw_sha256_required; lf_normalized_text_sha256_recorded_for cross-platform review"
  },
  "route_id": "GTOS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE",
  "schema_version": "gtos_research_capability_limitation_closure_control_route_v1",
  "strict_parser_test_verifier_hash_policy": [
    "Route source-hash manifest must bind builder, verifier, and focused test raw SHA.",
    "Packet row parser_code_hash must match the accepted builder hash or an explicitly recorded parser bundle hash.",
    "Verifier must recompute these hashes from disk before accepting route completion."
  ],
  "terminal_decision": "ACCEPT_AS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE",
  "validation_safe": false,
  "verifier_self_check_pattern": [
    "Parse all route artifacts.",
    "Recompute strict hashes for parser/test/verifier files.",
    "Ignore LIVE_STATE strict hash drift for parser closure while still requiring final freshness read.",
    "Scan committed or working diff for forbidden live-surface paths.",
    "Emit exact repair prompt when strict parser hashes drift."
  ]
}
```
