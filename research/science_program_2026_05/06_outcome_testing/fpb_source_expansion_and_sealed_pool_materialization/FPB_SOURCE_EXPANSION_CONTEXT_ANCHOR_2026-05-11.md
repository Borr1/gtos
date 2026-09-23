# Context Anchor

- Route: `FPB_SOURCE_EXPANSION_AND_SEALED_POOL_MATERIALIZATION`
- Evidence class: `SOURCE_CONTROL_MATERIALIZATION_ONLY`
- Promotion posture: `NO_PROMOTION_VERDICT`
- validation_safe: `false`
- outcome_review_opened: `false`
- live_effect: `false`

## Summary

```json
{
  "artifact_family": "context_anchor",
  "current_discovery_exposed_source_rows_excluded": 365,
  "live_effect": false,
  "outcome_review_opened": false,
  "terminal_decision": "MATERIALIZED_NATIVE_SCID_SEALED_SOURCE_POOL_CANDIDATES_G12_AUDIT_REQUIRED",
  "validation_safe": false
}
```

## Notes

- The build is anchored to current disk artifacts and git HEAD, not compaction memory.
