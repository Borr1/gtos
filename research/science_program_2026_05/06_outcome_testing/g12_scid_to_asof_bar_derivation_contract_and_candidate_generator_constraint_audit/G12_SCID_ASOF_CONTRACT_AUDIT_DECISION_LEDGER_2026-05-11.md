# G12 SCID As-Of Contract Audit Decision Ledger

- Route: `G12_SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_AUDIT`
- Evidence class: `G12_SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AUDIT_ONLY`
- Terminal decision: `ACCEPT_WITH_EXACT_CONTRACT_WARNINGS`
- Promotion verdict: `NO_PROMOTION_VERDICT`
- validation_safe: `False`
- outcome_review_opened: `False`
- live_effect: `False`

## Summary

```json
{
  "next_prompt": "research/science_program_2026_05/04_goal_prompts/SCID_ASOF_BAR_BUILDER_AND_CANDIDATE_INPUT_PACKET_SOURCE_CONTROL_GOAL_PROMPT_2026-05-11.md",
  "terminal_blocker_count": 0,
  "terminal_decision": "ACCEPT_WITH_EXACT_CONTRACT_WARNINGS",
  "warning_count": 2
}
```

## Payload

```json
{
  "acceptance_checks": {
    "asof_noleak_accepted": true,
    "duplicate_proxy_accepted": true,
    "fixture_accepted_with_warning": true,
    "forbidden_field_accepted_no_fail_open": true,
    "parser_timestamp_accepted": true,
    "terminal_blockers_zero": true
  },
  "accepted_promotion": false,
  "accepted_result_scoring": false,
  "accepted_scored_candidate_generation": false,
  "accepted_source_control_scid_asof_contract_only": true,
  "accepted_validation_execution": false,
  "artifact_family": "decision_ledger",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G12_SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AUDIT_ONLY",
  "exact_contract_warnings": [
    {
      "evidence": "Required candidate fields `bar_window_start_utc` and `bar_window_end_utc` contain substring `win`; the forbidden ledger says substring matching and includes pattern `win`.",
      "required_repair_in_next_source_control_lane": "Use snake_case token matching for short words such as `win` or explicitly whitelist `bar_window_*` before packet materialization; include focused tests.",
      "risk": "A literal substring scanner would reject required input-packet fields. This is fail-closed and does not open validation or leakage, but the next packet-builder lane must repair scanner semantics.",
      "severity": "EXACT_CONTRACT_WARNING_FAIL_CLOSED_NOT_LEAK",
      "warning_id": "FORBIDDEN_SCAN_OVERMATCH_WIN_WINDOW"
    },
    {
      "evidence": "Target artifacts carry `eligible_segment_start_utc_hard_floor` for all 9 source inputs and upstream repair/G12 rehash proves first records are at or after hard floor, but the target focused pytest file does not contain a dedicated hard-floor fixture assertion.",
      "required_repair_in_next_source_control_lane": "Add focused tests that reject records before eligible_segment_start_utc_hard_floor and records outside segment_byte_start..segment_byte_end_exclusive.",
      "risk": "The contract is source-control safe because upstream segment repair closes hard-floor source acceptance; future bar-builder code still needs an executable hard-floor boundary fixture before materializing packets.",
      "severity": "EXACT_CONTRACT_WARNING_TEST_COVERAGE",
      "warning_id": "TARGET_TESTS_DO_NOT_EXECUTE_HARD_FLOOR_CASE"
    }
  ],
  "generated_at_utc": "2026-05-11T12:25:51Z",
  "live_effect": false,
  "next_allowed_lane_boundary": "source-control bar-builder and candidate input-packet materialization only; no validation execution, result/path-label scoring, R/PnL/win-rate/expectancy/performance/cost/slippage, AI/API, broker account/order/history/deal/position evidence, promotion, live behavior, raw market-data blob commits, prompt/config/risk/safety/execution/canary/selector changes, credentials, remotes, or paid/vendor access",
  "next_allowed_lane_if_accepted": "research/science_program_2026_05/04_goal_prompts/SCID_ASOF_BAR_BUILDER_AND_CANDIDATE_INPUT_PACKET_SOURCE_CONTROL_GOAL_PROMPT_2026-05-11.md",
  "no_promotion_verdict": "NO_PROMOTION_VERDICT",
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
  "route_id": "G12_SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_AUDIT",
  "schema_version": "g12_scid_asof_contract_audit_v1",
  "summary": {
    "next_prompt": "research/science_program_2026_05/04_goal_prompts/SCID_ASOF_BAR_BUILDER_AND_CANDIDATE_INPUT_PACKET_SOURCE_CONTROL_GOAL_PROMPT_2026-05-11.md",
    "terminal_blocker_count": 0,
    "terminal_decision": "ACCEPT_WITH_EXACT_CONTRACT_WARNINGS",
    "warning_count": 2
  },
  "terminal_decision": "ACCEPT_WITH_EXACT_CONTRACT_WARNINGS",
  "validation_safe": false
}
```
