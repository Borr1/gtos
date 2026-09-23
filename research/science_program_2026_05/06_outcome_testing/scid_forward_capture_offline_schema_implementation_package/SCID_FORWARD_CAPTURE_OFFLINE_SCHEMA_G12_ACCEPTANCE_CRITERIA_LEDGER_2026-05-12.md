# G12 Acceptance Criteria Ledger

- **route_id:** `SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE`
- **evidence_class:** `SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "acceptance_criteria": [
    "Recompute 3,014 candidate_input_row_id coverage expectation and 3,014 duplicate_proxy_denominator_key expectation from accepted G12/G0 inputs.",
    "Verify all 10 accepted capture groups have schema, parser, redaction, as-of, no-leak, fail-closed, fixture, and G12 acceptance treatment.",
    "Run the offline validator on valid, missing, unavailable, forbidden, stale, duplicate, and manifest-repair fixtures.",
    "Verify read-only monitoring alignment only inspects shape/key metadata and does not alter producers or running processes.",
    "Verify manifest-binding repair continuity: current G12 prompt hash rebound and self-referential builder manifest hash non-blocking only.",
    "Reject any validation/result scoring/strategy-edge/R/PnL/win-rate/expectancy/performance/promotion/live behavior/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/prompt-config-risk-safety-execution-canary-selector change."
  ],
  "artifact_family": "g12_acceptance_criteria_ledger",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_ONLY",
  "generated_at_utc": "2026-05-12T03:20:55Z",
  "live_effect": false,
  "next_g12_prompt_path": "research/science_program_2026_05/04_goal_prompts/G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_AUDIT_GOAL_PROMPT_2026-05-12.md",
  "opens_ai_api": false,
  "opens_broker_account_order_history_deal_position_evidence": false,
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_paid_or_vendor_access": false,
  "opens_prompt_config_risk_safety_execution_canary_selector_edit": false,
  "opens_raw_market_data_blob_commit": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_strategy_edge_claims": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE",
  "schema_version": "scid_forward_capture_offline_schema_package_v1",
  "terminal_accept_decision_if_passed": "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_CONTROL_EVIDENCE_ONLY",
  "terminal_reject_decision_if_failed": "REPAIR_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_BEFORE_USE",
  "validation_safe": false
}
```
