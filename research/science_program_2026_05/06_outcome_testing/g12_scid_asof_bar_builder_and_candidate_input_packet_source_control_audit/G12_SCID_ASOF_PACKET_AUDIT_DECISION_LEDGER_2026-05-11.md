# G12 SCID As-Of Packet Audit Decision Ledger

- Terminal decision: `ACCEPT_AS_SOURCE_CONTROL_SCID_ASOF_CANDIDATE_INPUT_PACKET_ONLY`
- Promotion verdict: `NO_PROMOTION_VERDICT`
- validation_safe: `False`
- outcome_review_opened: `False`
- live_effect: `False`

## Summary

```json
{
  "summary": {
    "live_effect": false,
    "outcome_review_opened": false,
    "terminal_blocker_count": 0,
    "terminal_decision": "ACCEPT_AS_SOURCE_CONTROL_SCID_ASOF_CANDIDATE_INPUT_PACKET_ONLY",
    "validation_safe": false
  }
}
```

## Full Payload

```json
{
  "accepted_performance_scoring": false,
  "accepted_promotion": false,
  "accepted_replay_path_label_result_outcomes": false,
  "accepted_scored_candidate_generation": false,
  "accepted_source_control_packet_only": true,
  "accepted_validation_execution": false,
  "artifact_family": "decision_ledger",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G12_SCID_ASOF_BAR_BUILDER_AND_CANDIDATE_INPUT_PACKET_SOURCE_CONTROL_AUDIT_ONLY",
  "generated_at_utc": "2026-05-11T13:52:36Z",
  "live_effect": false,
  "next_allowed_lane_if_accepted": "research/science_program_2026_05/04_goal_prompts/G0_SCID_ASOF_PACKET_SOURCE_CONTROL_SYNTHESIS_AND_VALIDATION_DESIGN_GOAL_PROMPT_2026-05-11.md",
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
  "packet_warnings": [
    {
      "meaning": "Acceptance is source-control/input-packet only; validation/scoring remains forbidden.",
      "severity": "INFO_FAIL_CLOSED",
      "warning_id": "NEXT_GATE_REQUIRED_BEFORE_VALIDATION_OR_SCORING"
    }
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "review_summaries": {
    "bar_boundary": {
      "bar_row_count": 7567,
      "checks_pass": true,
      "empty_or_gap_bar_count": 3535,
      "record_present_bar_count": 4032
    },
    "candidate_input": {
      "candidate_input_row_count": 3014,
      "checks_pass": true,
      "unique_duplicate_key_count": 3014
    },
    "decision_source": {
      "checks_pass": true,
      "terminal_blocker_count": 0,
      "terminal_decision": "ACCEPT_WITH_EXACT_CONTRACT_WARNINGS",
      "warning_count": 2
    },
    "discovery_baseline": {
      "baseline_count": 4,
      "checks_pass": true
    },
    "duplicate_proxy": {
      "candidate_counting_source_count": 7,
      "checks_pass": true
    },
    "forbidden_field": {
      "bar_rows_scanned": 7567,
      "candidate_rows_scanned": 3014,
      "checks_pass": true
    },
    "source_rehash": {
      "checks_pass": true,
      "segment_count": 9
    },
    "warning_repair": {
      "checks_pass": true,
      "repaired_warning_count": 6
    }
  },
  "route_id": "G12_SCID_ASOF_BAR_BUILDER_AND_CANDIDATE_INPUT_PACKET_SOURCE_CONTROL_AUDIT",
  "schema_version": "g12_scid_asof_packet_audit_v1",
  "summary": {
    "live_effect": false,
    "outcome_review_opened": false,
    "terminal_blocker_count": 0,
    "terminal_decision": "ACCEPT_AS_SOURCE_CONTROL_SCID_ASOF_CANDIDATE_INPUT_PACKET_ONLY",
    "validation_safe": false
  },
  "terminal_blockers": [],
  "terminal_decision": "ACCEPT_AS_SOURCE_CONTROL_SCID_ASOF_CANDIDATE_INPUT_PACKET_ONLY",
  "validation_safe": false
}
```
