# OTB2R G6 G12 Audit Handoff - 2026-05-07

Promotion posture: `NO_PROMOTION_VERDICT`

```json

{
  "artifact_family": "OTB2R_G6_G12_AUDIT_HANDOFF",
  "audit_status": {
    "duplicate_policy_present": true,
    "exact_blocker_count": 4,
    "forbidden_record_key_hits": 0,
    "label_family_pooling_allowed": false,
    "source_hash_failure_count": 0
  },
  "next_g12_questions": [
    "Does G12 accept paired generic comparator fields in OTG0-PKT-060 as packet inputs while keeping generic rows non-independent?",
    "Does G12 accept fixed OHLC proxy exhaustion fields as a packet scaffold, or require a separate true changepoint source before readiness?",
    "Should OTG0-PKT-061 stay forward-shadow partial until exact executable decision price and ordered path are captured?",
    "Are parsed verifier-text OB bounds sufficient for a packet audit, or must every OB bound come from structured market-state source rows?"
  ],
  "outcome_review_opened": false,
  "packet_summary": [
    {
      "decision": "INPUT_PACKET_BUILT_WITH_EXACT_LIMITATION_LEDGER",
      "experiment_id": "G6-EXP-001-OB-VS-GENERIC-RETRACE",
      "packet_hash": "0c3b2c3ca9ce635a2d335694e20d5d2ab4f6030801a66141614d8e8f4d06ed2d",
      "packet_id": "OTG0-PKT-060",
      "records": 80,
      "unique_duplicate_groups": 20
    },
    {
      "decision": "INPUT_PACKET_BUILT_PARTIAL_FORWARD_SOURCE_BLOCKED",
      "experiment_id": "G6-EXP-002-CONTINUATION-NO-RETRACE",
      "packet_hash": "7475a0da06e6730bf433b7e9abacf8edb59c249c2caf133a44ef808f33412873",
      "packet_id": "OTG0-PKT-061",
      "records": 51,
      "unique_duplicate_groups": 8
    },
    {
      "decision": "INPUT_PACKET_BUILT_SOURCE_HASHED_NO_OUTCOMES",
      "experiment_id": "G6-EXP-003-OPENING-DRIVE-CONTINUATION",
      "packet_hash": "a2ebcedd1bb2ba8fc45903c5b5a0e7b90315e2d5a35d10c33a12090c37e143ba",
      "packet_id": "OTG0-PKT-062",
      "records": 86,
      "unique_duplicate_groups": 19
    },
    {
      "decision": "INPUT_PACKET_BUILT_SOURCE_HASHED_NO_OUTCOMES",
      "experiment_id": "G6-EXP-004-EXHAUSTION-CHANGEPOINT",
      "packet_hash": "c23160ab3c161ca60ed12a964d690b31c54ff6648b1646ebb1bfea1f43a2a010",
      "packet_id": "OTG0-PKT-063",
      "records": 86,
      "unique_duplicate_groups": 21
    },
    {
      "decision": "INPUT_PACKET_BUILT_WITH_EXACT_LIMITATION_LEDGER",
      "experiment_id": "G6-EXP-007-GOLD-ROUND-OB-CONFLUENCE",
      "packet_hash": "78a399d502257e9f26a07bb294a37ada2777beb676e92fb5ed029b93fbd914cf",
      "packet_id": "OTG0-PKT-066",
      "records": 7,
      "unique_duplicate_groups": 6
    }
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "scope_limit": "Future G12 packet audit only; no outcome/result lane is opened.",
  "validation_safe": false
}

```
