# OTX G6 Internal Packet Audit

- Generated at UTC: `2026-05-07T07:50:26Z`
- Promotion verdict: `NO_PROMOTION_VERDICT`
- Validation safe: `false`
- Outcome review opened: `false`

```json
{
  "artifact_family": "OTX_G6_INTERNAL_PACKET_AUDIT",
  "generated_at_utc": "2026-05-07T07:50:26Z",
  "note": "Forbidden packet-key scan is enforced on rebuilt input proposals. Result rows are quarantined and may carry synthetic_r only in the OTI4b result ledger.",
  "outcome_review_opened": false,
  "packet_audit_rows": [
    {
      "changepoint_ready_rows": 0,
      "decision_reason": "Matched comparator remains proved, but external ticks cannot prove selected H1 OB source row, OB id, creation event, or touch sequence.",
      "experiment_id": "G6-EXP-001-OB-VS-GENERIC-RETRACE",
      "feature_asof_failure_count": 0,
      "feature_asof_failures": [],
      "forbidden_packet_field_hits": [],
      "internal_decision": "BLOCKED_WITH_EXACT_IMPOSSIBILITY_FROM_APPROVED_LOCAL_TICKS",
      "opening_drive_ready_rows": 0,
      "ordered_tick_path_ready_rows": 79,
      "packet_id": "OTG0-PKT-060",
      "quote_ready_rows": 76,
      "record_count": 80,
      "source_hash_missing_count": 0,
      "sweep_ready_rows": 0,
      "unique_duplicate_group_count": 20
    },
    {
      "changepoint_ready_rows": 0,
      "decision_reason": "Tick data clears most CNR rows, but at least one row lacks exact decision quote/path coverage; no result lane was opened.",
      "experiment_id": "G6-EXP-002-CONTINUATION-NO-RETRACE",
      "feature_asof_failure_count": 0,
      "feature_asof_failures": [],
      "forbidden_packet_field_hits": [],
      "internal_decision": "BLOCKED_WITH_EXACT_PARTIAL_TICK_COVERAGE_EVIDENCE",
      "opening_drive_ready_rows": 0,
      "ordered_tick_path_ready_rows": 50,
      "packet_id": "OTG0-PKT-061",
      "quote_ready_rows": 50,
      "record_count": 51,
      "source_hash_missing_count": 0,
      "sweep_ready_rows": 0,
      "unique_duplicate_group_count": 8
    },
    {
      "changepoint_ready_rows": 0,
      "decision_reason": "Opening-drive range/breakout fields were rebuilt from ticks where as-of complete; quarantined OTI4b ledger was computed from tick path only with noncountable row exclusions.",
      "experiment_id": "G6-EXP-003-OPENING-DRIVE-CONTINUATION",
      "feature_asof_failure_count": 9,
      "feature_asof_failures": [
        "OTG0-PKT-062|NAS100_2026-05-04T07:15:00+00:00",
        "OTG0-PKT-062|XAGUSD_2026-05-04T07:15:00+00:00",
        "OTG0-PKT-062|XAUUSD_2026-05-04T07:15:00+00:00",
        "OTG0-PKT-062|NAS100_2026-05-04T13:15:00+00:00",
        "OTG0-PKT-062|XAGUSD_2026-05-04T13:15:00+00:00",
        "OTG0-PKT-062|NAS100_2026-05-05T07:15:00+00:00",
        "OTG0-PKT-062|NAS100_2026-05-06T07:15:00+00:00",
        "OTG0-PKT-062|XAGUSD_2026-05-06T07:15:00+00:00",
        "OTG0-PKT-062|XAUUSD_2026-05-06T07:15:00+00:00"
      ],
      "forbidden_packet_field_hits": [],
      "internal_decision": "CLEARED_AND_QUARANTINED_TESTED_DISCOVERY_ONLY_WITH_ROW_EXCLUSIONS",
      "opening_drive_ready_rows": 73,
      "ordered_tick_path_ready_rows": 84,
      "packet_id": "OTG0-PKT-062",
      "quote_ready_rows": 81,
      "record_count": 86,
      "source_hash_missing_count": 0,
      "sweep_ready_rows": 0,
      "unique_duplicate_group_count": 19
    },
    {
      "changepoint_ready_rows": 81,
      "decision_reason": "Preregistered tick-derived CUSUM changepoint outputs exist for the covered subset; rows without sufficient predecision M1 bars are exact blockers.",
      "experiment_id": "G6-EXP-004-EXHAUSTION-CHANGEPOINT",
      "feature_asof_failure_count": 0,
      "feature_asof_failures": [],
      "forbidden_packet_field_hits": [],
      "internal_decision": "CLEARED_FOR_EXTERNAL_G12_REAUDIT_WITH_EXACT_ROW_BLOCKERS",
      "opening_drive_ready_rows": 0,
      "ordered_tick_path_ready_rows": 84,
      "packet_id": "OTG0-PKT-063",
      "quote_ready_rows": 81,
      "record_count": 86,
      "source_hash_missing_count": 0,
      "sweep_ready_rows": 0,
      "unique_duplicate_group_count": 21
    },
    {
      "changepoint_ready_rows": 0,
      "decision_reason": "Structured sweep fields are emitted, but rows lacking predecision tick coverage remain exact row blockers before any outcome opening.",
      "experiment_id": "G6-EXP-007-GOLD-ROUND-OB-CONFLUENCE",
      "feature_asof_failure_count": 4,
      "feature_asof_failures": [
        "OTG0-PKT-066|XAUUSD_2026-05-03T16:15:00+00:00",
        "OTG0-PKT-066|XAUUSD_2026-05-03T16:30:00+00:00",
        "OTG0-PKT-066|XAUUSD_2026-05-06T07:15:00+00:00",
        "OTG0-PKT-066|XAUUSD_2026-05-06T08:00:00+00:00"
      ],
      "forbidden_packet_field_hits": [],
      "internal_decision": "CLEARED_FOR_EXTERNAL_G12_REAUDIT_WITH_EXACT_ROW_BLOCKERS",
      "opening_drive_ready_rows": 0,
      "ordered_tick_path_ready_rows": 5,
      "packet_id": "OTG0-PKT-066",
      "quote_ready_rows": 3,
      "record_count": 7,
      "source_hash_missing_count": 0,
      "sweep_ready_rows": 7,
      "unique_duplicate_group_count": 6
    }
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "result_rows_forbidden_field_hits_packet_scope": [],
  "validation_safe": false
}
```
