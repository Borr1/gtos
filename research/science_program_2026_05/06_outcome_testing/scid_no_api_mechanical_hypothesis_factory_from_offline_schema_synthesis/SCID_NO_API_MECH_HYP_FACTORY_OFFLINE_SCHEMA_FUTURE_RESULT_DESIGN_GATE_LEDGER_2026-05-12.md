# Future Result-Design Gate Ledger

- **route_id:** `SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS`
- **evidence_class:** `SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "artifact_family": "future_result_design_gate_ledger",
  "cards_blocked_until_gate_pass": [
    "GEO-001",
    "GEO-002",
    "GEO-003",
    "GEO-004",
    "GEO-005",
    "HAZ-001",
    "HAZ-002",
    "HAZ-003",
    "HAZ-004",
    "HAZ-005",
    "MIC-001",
    "MIC-002",
    "MIC-003",
    "MIC-004",
    "MIC-005",
    "BEH-001",
    "BEH-002",
    "BEH-003",
    "BEH-004",
    "BEH-005",
    "MAC-001",
    "MAC-002",
    "MAC-003",
    "MAC-004",
    "MAC-005",
    "EXE-001",
    "EXE-002",
    "EXE-003",
    "EXE-004",
    "EXE-005",
    "UNC-001",
    "UNC-002",
    "UNC-003",
    "UNC-004",
    "UNC-005",
    "ADV-001",
    "ADV-002",
    "ADV-003",
    "ADV-004",
    "ADV-005"
  ],
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY",
  "gate_count": 6,
  "gates": [
    {
      "gate_id": "GATE-01-SOURCE-FIELDS",
      "must_pass_before_result_design": "All required future source fields for selected cards captured or recovered and G12-accepted."
    },
    {
      "gate_id": "GATE-02-ASOF-NOLEAK",
      "must_pass_before_result_design": "Every consumed field has source_observed_asof_utc <= decision_asof_utc and no forbidden broker/result/future path field."
    },
    {
      "gate_id": "GATE-03-DUPLICATE-POLICY",
      "must_pass_before_result_design": "candidate_input_row_id and duplicate_proxy_denominator_key preserved; denominator choice frozen."
    },
    {
      "gate_id": "GATE-04-PARTITION-BASELINES",
      "must_pass_before_result_design": "partition_assignment and adversarial baseline/control assignment frozen before opening outcomes."
    },
    {
      "gate_id": "GATE-05-SEPARATE-RESULT-PROMPT",
      "must_pass_before_result_design": "A separate result-design preregistration prompt authorizes the evidence-class transition."
    },
    {
      "gate_id": "GATE-06-FORBIDDEN-SURFACE-SCAN",
      "must_pass_before_result_design": "No AI/API, paid/vendor, raw blob, broker account/order/deal/position, live behavior, prompt/config/risk/safety/execution/canary/selector change."
    }
  ],
  "generated_at_utc": "2026-05-12T05:31:11Z",
  "live_effect": false,
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
  "result_design_opened_now": false,
  "route_id": "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS",
  "schema_version": "scid_no_api_mechanical_hypothesis_factory_offline_schema_v1",
  "validation_safe": false
}
```
