# G12 OTI5 OTR061 Decision Ledger - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

- OTI5 terminal decision: `ACCEPT_AS_QUARANTINED_DISCOVERY_EVIDENCE`.
- OTR061 terminal decision: `ACCEPT_PACKET_FOR_FUTURE_QUARANTINED_RESULT_AUDIT`.
- Both decisions preserve research-only quarantine boundaries.

```json
{
  "artifact_family": "G12_OTI5_OTR061_DECISION_LEDGER",
  "audit_verdict": "PASS_BOTH_TARGETS_TERMINALLY_DECIDED",
  "decisions": [
    {
      "acceptance_scope": "Quarantined discovery evidence only; not validation, not promotion, not live logic.",
      "key_evidence": {
        "duplicate_primary_groups": 17,
        "excluded_rows": 5,
        "mean_resolved_synthetic_r": -0.72222222,
        "resolved_synthetic_rows": 9,
        "source_ready_rows": 81,
        "terminal_status_counts": {
          "ENTRY_TOUCHED_THEN_SL": 8,
          "ENTRY_TOUCHED_THEN_TP1": 1,
          "NO_ENTRY_TOUCH_NO_R_SCORED": 8
        }
      },
      "packet_id": "OTG0-PKT-063",
      "rationale": "The frozen 81-row subset, five exclusions, duplicate denominator, source/no-leak controls, label-family separation, and non-computable methodology status are file-supported. The negative result is valid discovery evidence rather than a control failure.",
      "target": "OTI5_G6_CUSUM_CHANGEPOINT_QUARANTINED_RESULTS",
      "terminal_g12_decision": "ACCEPT_AS_QUARANTINED_DISCOVERY_EVIDENCE"
    },
    {
      "acceptance_scope": "Input-only recovered packet for a future quarantined result lane; no result scoring opened here.",
      "key_evidence": {
        "decision_quote": {
          "ask": 4648.29,
          "bid": 4647.65,
          "decision_rows_lte_071500": 875,
          "executable_decision_price_long_ask": 4648.29,
          "quote_timestamp_utc": "2026-05-06T07:14:59.889000Z"
        },
        "ordered_path": {
          "first_timestamp_utc": "2026-05-06T07:15:00.634000Z",
          "last_timestamp_utc": "2026-05-06T11:14:59.900000Z",
          "post_horizon_first_timestamp_utc": "2026-05-06T11:15:00.335000Z",
          "row_count": 88060
        },
        "parquet_rows": 89391,
        "parquet_sha256": "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff"
      },
      "packet_id": "OTG0-PKT-061",
      "rationale": "The recovered XAUUSD MT5 read-only parquet exists in the current worktree, matches the claimed SHA256, contains 89391 rows over the required window, and reconstructs the decision quote and ordered tick path without broker actual-R, account history, paid data, or live order state.",
      "target": "OTR061_XAU_TICK_RECOVERY",
      "terminal_g12_decision": "ACCEPT_PACKET_FOR_FUTURE_QUARANTINED_RESULT_AUDIT"
    }
  ],
  "generated_at_utc": "2026-05-07T09:59:44Z",
  "git_head_at_build": "9e3c7f4e docs: record oti5 failure forensics prompt discipline",
  "global_boundaries": {
    "live_effect": false,
    "no_live_surface_edits": true,
    "no_paid_api_databento": true,
    "no_validation_or_promotion_meaning": true,
    "outcome_review_opened": false,
    "validation_safe": false
  },
  "lane_scope": "G12 combined post-test / packet-recovery audit",
  "live_effect": false,
  "next_lane_prompt_artifact": "G12_OTI5_OTR061_NEXT_LANE_PROMPT_PACK_2026-05-07.md",
  "next_lane_prompt_required": true,
  "objective_restated": "Run a combined G12 post-audit over OTI5 OTG0-PKT-063 CUSUM/changepoint quarantined results and OTR061 OTG0-PKT-061 XAU tick recovery, with file-grounded terminal decisions and no promotion or live-surface effect.",
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "terminal_decisions": {
    "OTI5": "ACCEPT_AS_QUARANTINED_DISCOVERY_EVIDENCE",
    "OTR061": "ACCEPT_PACKET_FOR_FUTURE_QUARANTINED_RESULT_AUDIT"
  },
  "validation_safe": false
}
```
