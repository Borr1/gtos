# Accepted Evidence Chain Reconciliation Ledger

- **count_reconciliation_status:** `PASS`

```json
{
  "accepted_counts": {
    "candidate_lfs_pointer_oid": "48442dd5db7aa00e6a48770548ded751227aeec3a22481f6a203d52c153a96b6",
    "candidate_lfs_pointer_size": 205437302,
    "compact_candidate_rows_written": 120000,
    "compact_path_label_rows_written": 120000,
    "duplicate_candidate_keys": 687275,
    "excluded_source_slices": 3135,
    "live_effect": false,
    "opened_mechanical_families": 11,
    "outcome_review_opened": false,
    "path_label_lfs_pointer_oid": "78bca50ebb33a0eb5845494e8e2bc4b12196d198d0027aedb9966c0b74673e7a",
    "path_label_lfs_pointer_size": 170589802,
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "raw_candidate_attempts": 13540033,
    "selected_large_ohlc_hash_resolutions": 18,
    "selected_source_rows": 365,
    "source_universe_rows_consumed": 3500,
    "unique_nonduplicate_candidate_path_label_denominator": 12852758,
    "validation_safe": false
  },
  "artifact_family": "accepted_evidence_chain_reconciliation_ledger",
  "count_reconciliation_status": "PASS",
  "evidence_chain": [
    {
      "decision": "NO_PROMOTION_VERDICT_MECHANICAL_REPLAY_DISCOVERY_INVENTORY_BUILT",
      "route": "NO_API_MECHANICAL_REPLAY_ENGINE_FROM_SOURCE_UNIVERSE",
      "status": "accepted_by_target_completion_audit",
      "step": "target_substrate"
    },
    {
      "decision": "ACCEPT_AS_NO_API_MECHANICAL_REPLAY_SOURCE_CONTROL_SUBSTRATE",
      "route": "G12_NO_API_MECHANICAL_REPLAY_ENGINE_SOURCE_CONTROL_AUDIT",
      "status": "accepted_as_source_control_substrate",
      "step": "g12_source_control_audit"
    },
    {
      "decision": "ACCEPT_AS_G0_REPLAY_SYNTHESIS_WITH_RANKED_DISCOVERY_ROUTES",
      "route": "G0_NO_API_MECHANICAL_REPLAY_SOURCE_CONTROL_SYNTHESIS_AND_DISCOVERY_ROUTE_SELECTION",
      "status": "synthesis_control_only",
      "step": "g0_synthesis"
    }
  ],
  "exact_deviations": [],
  "g12_acceptance_reasons": [
    "all required target JSON/JSONL artifacts parsed",
    "expected headline counts independently reconciled from summaries, compact JSONL files, and source-progress final counters",
    "large compact JSONL artifacts are LFS pointer blobs in HEAD and materialized locally",
    "candidate and path-label compact rows preserve projection-only/no-result/no-validation flags",
    "all opened families reached terminal non-prototype inventory status",
    "forbidden validation/result/live/API/broker/remote surfaces remain closed",
    "pre-existing runtime/generated dirty state is separated from G12 scope"
  ],
  "g12_terminal_decision": "ACCEPT_AS_NO_API_MECHANICAL_REPLAY_SOURCE_CONTROL_SUBSTRATE",
  "target_terminal_decision": "NO_PROMOTION_VERDICT_MECHANICAL_REPLAY_DISCOVERY_INVENTORY_BUILT"
}
```
