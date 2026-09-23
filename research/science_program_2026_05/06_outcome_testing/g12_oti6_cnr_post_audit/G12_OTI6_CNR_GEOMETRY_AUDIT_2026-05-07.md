# G12 OTI6 CNR Geometry Audit - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

- Recomputes that the CNR_E0 LONG decision ask was already beyond original TP1.
- Confirms geometry was applied before R scoring and no synthetic R was forced.

```json
{
  "account_history_accessed": false,
  "answer": "YES_CNR_E0_GEOMETRY_WAS_APPLIED_BEFORE_R_SCORING",
  "api_calls": 0,
  "artifact_family": "G12_OTI6_CNR_GEOMETRY_AUDIT",
  "audit_question": "Did OTI6 correctly apply the preregistered CNR_E0 geometry before R scoring?",
  "audit_verdict": "PASS_TARGET_ALREADY_PASSED_IS_CORRECT_UNDER_CNR_E0",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "code_evidence": {
    "builder_path": "research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/build_oti6_otr061_cnr_quarantined_results_2026_05_07.py",
    "c_nr_geometry_function_line": 295,
    "geometry_call_line": 400,
    "geometry_call_precedes_result_ledger": true,
    "r_scoring_attempted_false_line": 503,
    "result_ledger_line": 478,
    "synthetic_path_r_none_line": 498,
    "target_already_passed_long_branch_line": 297
  },
  "databento_calls": 0,
  "date_stamp": "2026-05-07",
  "entry_model_rule_verified": {
    "entry_model_id": "CNR_E0_DECISION_CLOSE_MARKET",
    "executable_price_rule": "LONG uses ask at decision quote; SHORT uses bid at decision quote.",
    "quote_timestamp_rule": "last source-hashed tick at or before decision_asof_utc"
  },
  "generated_at_utc": "2026-05-07T10:47:40Z",
  "git_head_at_build": "16713c77 docs: refresh research state for g12 oti6 prompt",
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "ordered_path_context_not_scored": {
    "first_ask": 4648.31,
    "first_bid": 4647.67,
    "first_timestamp_utc": "2026-05-06T07:15:00.634000Z",
    "last_ask": 4680.18,
    "last_bid": 4679.63,
    "last_timestamp_utc": "2026-05-06T11:14:59.900000Z",
    "not_scored_reason": "Path direction after decision is context only because the original TP1 was already behind the CNR_E0 entry.",
    "path_trended_up_after_decision": true,
    "row_count": 88060
  },
  "oti6_result_controls": {
    "r_scoring_attempted": false,
    "r_scoring_blocked_before_path_scoring_reason": "LONG executable ask is above original TP1 before CNR_E0 can enter.",
    "synthetic_path_r": null,
    "synthetic_path_r_status": "NOT_COMPUTED_PREREGISTERED_GEOMETRY_NOT_ELIGIBLE"
  },
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-061",
  "paid_data_calls": 0,
  "preregistered_geometry_gate": {
    "long_valid_ordering": "stop_loss < executable_entry < original_take_profit_1",
    "short_valid_ordering": "original_take_profit_1 < executable_entry < stop_loss",
    "target_already_passed_policy": "If executable entry is already beyond original TP1, do not score as positive R."
  },
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "recomputed_geometry": {
    "base_r_price": 14.17,
    "cnr_e0_executable_entry": 4648.29,
    "cnr_e0_long_geometry_valid_for_original_target": false,
    "distance_entry_to_original_entry_price": 86.77,
    "distance_entry_to_original_entry_r": 6.12350035,
    "distance_entry_to_tp1_price": 65.52,
    "distance_entry_to_tp1_r": 4.62385321,
    "original_entry_price": 4561.52,
    "original_geometry_valid": true,
    "original_stop_loss": 4547.35,
    "original_take_profit_1": 4582.77,
    "side": "LONG",
    "target_already_passed_at_decision": true,
    "tp1_minus_original_entry_price": 21.25,
    "tp1_minus_original_entry_r": 1.49964714
  },
  "source_evidence": {
    "candidate_geometry_source": {
      "line_no": 50,
      "row_key": "97a72dd896b0b4fb88a0b9aadb9295e6",
      "source_file": "shadow_logs/continuation_no_retrace_candidates.jsonl",
      "source_file_sha256": "30ae312b24db1a0808928d5c025aa0cb4c6fb626a239657e179512c45b2cdd76",
      "source_line_sha256": "27d379d158972f568f3c854aeaabae6604183f0283d988d11889380c140b3691"
    },
    "forensics_evidence": {
      "cnr_e0_entry_ask": 4648.29,
      "decision_quote_timestamp_utc": "2026-05-06T07:14:59.889000Z",
      "first_ordered_path_bid": 4647.67,
      "first_ordered_path_timestamp_utc": "2026-05-06T07:15:00.634000Z",
      "original_tp1": 4582.77,
      "source_file_line": "shadow_logs/continuation_no_retrace_candidates.jsonl:50",
      "target_already_passed_by_price": 65.52,
      "target_already_passed_by_r": 4.62385321
    },
    "oti6_parquet_sha256_matches_expected": true
  },
  "target_record_id": "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00",
  "terminal_g12_decision": "ACCEPT_AS_QUARANTINED_TARGET_ALREADY_PASSED_DISCOVERY_EVIDENCE",
  "validation_safe": false
}
```
