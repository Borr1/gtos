# OTB2R G6 Completion Audit - 2026-05-07

Promotion posture: `NO_PROMOTION_VERDICT`

```json

{
  "artifact_family": "OTB2R_G6_COMPLETION_AUDIT",
  "objective_restatement": "Build source-hashed, duplicate-grouped, decision_asof_utc, label-separated, input-only G6 packets from local OHLC/path/candidate evidence for OB-vs-generic retrace, no-retrace, opening-drive, exhaustion/changepoint, and gold round-number/OB confluence; do not open or inspect outcomes.",
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "prompt_to_artifact_checklist": [
    {
      "evidence": "LIVE_STATE was regenerated before builder implementation and is hashed in the manifest.",
      "requirement": "Complete mandatory GTOS preflight first",
      "status": "PASS"
    },
    {
      "evidence": "control_input_count=26; all_exist=True.",
      "requirement": "Use controlling G6/G0/G12/OTB2/OTB2R/OTG0/registry/current-state inputs",
      "status": "PASS"
    },
    {
      "evidence": "packet_ids=['OTG0-PKT-060', 'OTG0-PKT-061', 'OTG0-PKT-062', 'OTG0-PKT-063', 'OTG0-PKT-066']; record_count=310.",
      "requirement": "Build input-only packets for OB-vs-generic, no-retrace, opening-drive, exhaustion/changepoint, and gold round-number/OB confluence",
      "status": "PASS"
    },
    {
      "evidence": "source_hash_failure_count=0 over 310 records.",
      "requirement": "Source hashes recompute for every record",
      "status": "PASS"
    },
    {
      "evidence": "forbidden_record_key_hits=0; skipped_result_sources=4.",
      "requirement": "No packet record contains outcome/result/R label columns, broker actual-R, blocked-packet outcomes, or post-decision result features",
      "status": "PASS"
    },
    {
      "evidence": "duplicate_audit_packets=5; matched_policy_independent_generic_control_rows_allowed=False.",
      "requirement": "Duplicate denominators are explicit and matched controls do not double-count OB rows",
      "status": "PASS"
    },
    {
      "evidence": "label_audit_packets=5; validation_safe=False; outcome_review_opened=False.",
      "requirement": "Label families are separated and validation_safe remains false",
      "status": "PASS"
    },
    {
      "evidence": "terminal_order_claim_allowed=False; policy_counts={'LOCAL_OHLC_BOUNDED_PATH_TERMINAL_ORDER_NOT_CLAIMED': 233, 'M1_PATH_ORDER_LOG_METADATA_AVAILABLE_TERMINAL_EVENTS_EXCLUDED': 26, 'not_applicable_forward_packet': 51}.",
      "requirement": "Same-bar/timing policy does not guess terminal order",
      "status": "PASS"
    },
    {
      "evidence": "blocker_count=4; saturation=Local candidate, projection, OHLC, prereg, G12, OTB2/OTB2R, and continuation candidate artifacts were sufficient to build input packets, but exact structured OB.",
      "requirement": "Negative evidence and exact blocker ledgers name missing source/field/action",
      "status": "PASS"
    },
    {
      "evidence": "generated_artifact_classes=['builder script', 'packet JSONs', 'manifest', 'source-hash audit', 'no-leak audit', 'duplicate/denominator audit', 'label-family audit', 'matched-control policy', 'same-bar/timing policy', 'negative-evidence saturation ledger', 'G12 audit handoff', 'exact blocker ledger']; handoff_packets=5.",
      "requirement": "Produce all requested scoped artifacts",
      "status": "PASS"
    },
    {
      "evidence": "Manifest safety flags all false/zero; forbidden result/account-history/resolution sources are named as skipped policy paths without content hash/stat reads; builder writes only target artifacts.",
      "requirement": "No outcome scoring, broker actual-R, blocked-packet outcomes, paid/API/Databento, live trading, registry edit, or remote push",
      "status": "PASS"
    }
  ],
  "summary": {
    "can_mark_goal_complete": true,
    "external_or_paid_calls": 0,
    "forbidden_record_key_hits": 0,
    "packet_count": 5,
    "record_count": 310,
    "result_or_quarantine_outputs_created": false,
    "source_hash_failure_count": 0
  },
  "validation_safe": false
}

```
