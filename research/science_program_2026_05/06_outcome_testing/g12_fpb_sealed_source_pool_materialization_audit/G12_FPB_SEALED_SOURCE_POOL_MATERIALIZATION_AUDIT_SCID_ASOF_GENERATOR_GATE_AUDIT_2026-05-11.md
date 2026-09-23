# SCID As-Of Generator Gate Audit

- Route: `G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT`
- Artifact family: `scid_asof_and_candidate_generator_gate_audit`
- Evidence class: `G12_FPB_SEALED_SOURCE_POOL_SOURCE_CONTROL_AUDIT_ONLY`
- Promotion posture: `NO_PROMOTION_VERDICT`
- Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

```json
{
  "artifact_family": "scid_asof_and_candidate_generator_gate_audit",
  "candidate_count": 9,
  "changes_live_trading_behavior": false,
  "checks": {
    "all_candidates_have_eligible_segment_generator_gate": true,
    "all_candidates_have_scid_to_asof_gate": true,
    "all_parser_statuses_block_replay_until_contract": true
  },
  "credentials_touched": false,
  "evidence_class": "G12_FPB_SEALED_SOURCE_POOL_SOURCE_CONTROL_AUDIT_ONLY",
  "future_use_status": "VALIDATION_REMAINS_BLOCKED_UNTIL_NEXT_SOURCE_CONTROL_ROUTE_FREEZES_BAR_DERIVATION_AND_GENERATOR_CONSTRAINT",
  "generated_at_utc": "2026-05-11T09:43:01Z",
  "live_effect": false,
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
  "route_id": "G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT",
  "rows": [
    {
      "eligible_segment_generator_gate_explicit": true,
      "parser_asof_status": "SOURCE_LOCAL_FILE_ONLY_REQUIRES_BAR_DERIVATION_CONTRACT_BEFORE_REPLAY",
      "required_before_validation": [
        "G12 source-pool audit acceptance",
        "SCID-to-asof-bar derivation contract",
        "candidate generator must read only eligible_segment_start_utc onward",
        "same duplicate key and adversarial baseline packet preserved"
      ],
      "scid_to_asof_gate_explicit": true,
      "source": "6BM26-CME.scid",
      "symbol": "GBPUSD_6B"
    },
    {
      "eligible_segment_generator_gate_explicit": true,
      "parser_asof_status": "SOURCE_LOCAL_FILE_ONLY_REQUIRES_BAR_DERIVATION_CONTRACT_BEFORE_REPLAY",
      "required_before_validation": [
        "G12 source-pool audit acceptance",
        "SCID-to-asof-bar derivation contract",
        "candidate generator must read only eligible_segment_start_utc onward",
        "same duplicate key and adversarial baseline packet preserved"
      ],
      "scid_to_asof_gate_explicit": true,
      "source": "6EM26-CME.scid",
      "symbol": "EURUSD"
    },
    {
      "eligible_segment_generator_gate_explicit": true,
      "parser_asof_status": "SOURCE_LOCAL_FILE_ONLY_REQUIRES_BAR_DERIVATION_CONTRACT_BEFORE_REPLAY",
      "required_before_validation": [
        "G12 source-pool audit acceptance",
        "SCID-to-asof-bar derivation contract",
        "candidate generator must read only eligible_segment_start_utc onward",
        "same duplicate key and adversarial baseline packet preserved"
      ],
      "scid_to_asof_gate_explicit": true,
      "source": "6JM26-CME.scid",
      "symbol": "USDJPY_6J"
    },
    {
      "eligible_segment_generator_gate_explicit": true,
      "parser_asof_status": "SOURCE_LOCAL_FILE_ONLY_REQUIRES_BAR_DERIVATION_CONTRACT_BEFORE_REPLAY",
      "required_before_validation": [
        "G12 source-pool audit acceptance",
        "SCID-to-asof-bar derivation contract",
        "candidate generator must read only eligible_segment_start_utc onward",
        "same duplicate key and adversarial baseline packet preserved"
      ],
      "scid_to_asof_gate_explicit": true,
      "source": "GCM26-COMEX.scid",
      "symbol": "XAUUSD_GC"
    },
    {
      "eligible_segment_generator_gate_explicit": true,
      "parser_asof_status": "SOURCE_LOCAL_FILE_ONLY_REQUIRES_BAR_DERIVATION_CONTRACT_BEFORE_REPLAY",
      "required_before_validation": [
        "G12 source-pool audit acceptance",
        "SCID-to-asof-bar derivation contract",
        "candidate generator must read only eligible_segment_start_utc onward",
        "same duplicate key and adversarial baseline packet preserved"
      ],
      "scid_to_asof_gate_explicit": true,
      "source": "MGCM26-COMEX.scid",
      "symbol": "XAUUSD_MGC"
    },
    {
      "eligible_segment_generator_gate_explicit": true,
      "parser_asof_status": "SOURCE_LOCAL_FILE_ONLY_REQUIRES_BAR_DERIVATION_CONTRACT_BEFORE_REPLAY",
      "required_before_validation": [
        "G12 source-pool audit acceptance",
        "SCID-to-asof-bar derivation contract",
        "candidate generator must read only eligible_segment_start_utc onward",
        "same duplicate key and adversarial baseline packet preserved"
      ],
      "scid_to_asof_gate_explicit": true,
      "source": "MYMM26-CBOT.scid",
      "symbol": "US30_MYM"
    },
    {
      "eligible_segment_generator_gate_explicit": true,
      "parser_asof_status": "SOURCE_LOCAL_FILE_ONLY_REQUIRES_BAR_DERIVATION_CONTRACT_BEFORE_REPLAY",
      "required_before_validation": [
        "G12 source-pool audit acceptance",
        "SCID-to-asof-bar derivation contract",
        "candidate generator must read only eligible_segment_start_utc onward",
        "same duplicate key and adversarial baseline packet preserved"
      ],
      "scid_to_asof_gate_explicit": true,
      "source": "NQM26-CME.scid",
      "symbol": "NAS100_NQ"
    },
    {
      "eligible_segment_generator_gate_explicit": true,
      "parser_asof_status": "SOURCE_LOCAL_FILE_ONLY_REQUIRES_BAR_DERIVATION_CONTRACT_BEFORE_REPLAY",
      "required_before_validation": [
        "G12 source-pool audit acceptance",
        "SCID-to-asof-bar derivation contract",
        "candidate generator must read only eligible_segment_start_utc onward",
        "same duplicate key and adversarial baseline packet preserved"
      ],
      "scid_to_asof_gate_explicit": true,
      "source": "SIM26-COMEX.scid",
      "symbol": "XAGUSD_SI"
    },
    {
      "eligible_segment_generator_gate_explicit": true,
      "parser_asof_status": "SOURCE_LOCAL_FILE_ONLY_REQUIRES_BAR_DERIVATION_CONTRACT_BEFORE_REPLAY",
      "required_before_validation": [
        "G12 source-pool audit acceptance",
        "SCID-to-asof-bar derivation contract",
        "candidate generator must read only eligible_segment_start_utc onward",
        "same duplicate key and adversarial baseline packet preserved"
      ],
      "scid_to_asof_gate_explicit": true,
      "source": "YMM26-CBOT.scid",
      "symbol": "US30_YM"
    }
  ],
  "schema_version": "g12_fpb_sealed_source_pool_materialization_audit_v1",
  "validation_safe": false
}
```
