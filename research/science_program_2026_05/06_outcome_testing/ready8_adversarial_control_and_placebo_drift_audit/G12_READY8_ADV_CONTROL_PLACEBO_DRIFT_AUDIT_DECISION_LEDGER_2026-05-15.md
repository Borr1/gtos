# Decision Ledger

```json
{
  "accepted": true,
  "accepted_counts": {
    "adv001_rows": 4288,
    "adv003_rows": 12611,
    "baseline_drift_rows": 3546,
    "concentration_rows": 79746,
    "duplicate_artifact_rows": 3270,
    "explained_weakened_rows": 2622,
    "non_adv_comparison_rows": 10563,
    "residual_rows": 1,
    "stress_vs_sealed_rows": 45913,
    "underpower_rows": 79746
  },
  "artifact_family": "decision_ledger",
  "canonical_downstream_use": "R6 ADV-001/ADV-003 control-envelope adjustment is accepted as downstream control evidence for R1-R5/R7 interpretation only, with duplicate-effective-N, concentration, stress/sealed, and underpower constraints preserved.",
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "classification_counts": {
    "FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT": 2608,
    "MATERIALLY_WEAKENED_BY_ADV_CONTROL_DRIFT": 14,
    "NOT_NUMERIC_NOT_ADJUSTABLE": 3622,
    "RESIDUAL_PRESERVED_AFTER_ADV_CONTROL_ENVELOPE": 1,
    "UNDERPOWERED_PRESERVED_NOT_DECISION": 4318
  },
  "evidence_class": "G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT_REVIEW_ONLY",
  "generated_at_utc": "2026-05-15T11:29:33Z",
  "interpretation": "ADV controls explain or weaken a material subset of READY8 movement, but are not blanket erasers. Only residuals beyond the matched control envelope can remain research intelligence, and even those remain neutral target-movement evidence subject to duplicate-effective-N, concentration, stress/sealed, and G12/R7 gates.",
  "live_effect": false,
  "not_accepted_as": [
    "promotion",
    "validation_safe",
    "live_readiness",
    "R/PnL",
    "win_rate",
    "expectancy",
    "broker-realized performance",
    "AI/API evidence",
    "prompt/config/risk/safety/execution behavior change"
  ],
  "opens_ai_api": false,
  "opens_broker_account_order_history_deal_position_evidence": false,
  "opens_live_trading_behavior": false,
  "opens_paid_or_vendor_access": false,
  "opens_prompt_config_risk_safety_execution_canary_selector_edit": false,
  "opens_raw_market_data_blob_commit": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT",
  "terminal_blockers": [],
  "terminal_decision": "ACCEPT_AS_G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT_CANONICAL_DOWNSTREAM_CONTROL_EVIDENCE_NO_PROMOTION",
  "validation_safe": false
}
```
