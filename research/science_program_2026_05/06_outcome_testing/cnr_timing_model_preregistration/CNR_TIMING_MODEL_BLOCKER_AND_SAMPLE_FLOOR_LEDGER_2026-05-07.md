# CNR Timing Model Blocker And Sample Floor Ledger - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "CNR_TIMING_MODEL_BLOCKER_AND_SAMPLE_FLOOR_LEDGER",
  "blocked_packet_outcome_source_read": false,
  "blockers": [
    {
      "blocker_id": "B1_SIGNAL_EMIT_TIMESTAMP",
      "exact_requirement": "source-hashed signal_emitted_utc or candidate_close_utc for each future row",
      "status": "BLOCKED_UNTIL_FIELD_CAPTURED"
    },
    {
      "blocker_id": "B2_EXECUTABLE_QUOTE_SIDE",
      "exact_requirement": "bid/ask quote stream and LONG/SHORT quote-side rule for every future row",
      "status": "PARTIALLY_SOLVED_BY_OTR061_FOR_ONE_XAU_ROW"
    },
    {
      "blocker_id": "B3_TARGET_MODEL",
      "exact_requirement": "CNR_T0/T1/T2/T3 selected before outcome opening",
      "status": "FROZEN_OPTIONS_BUT_FUTURE_PACKET_MUST_BIND_ONE"
    },
    {
      "blocker_id": "B4_SOURCE_HASH_AND_PARSER",
      "exact_requirement": "SHA256, parser version, timestamp convention, and as-of cutoff for every consumed source file",
      "status": "SOLVED_FOR_CONTROL_INPUTS_NOT_ALL_FUTURE_ROWS"
    },
    {
      "blocker_id": "B5_DUPLICATE_DENOMINATOR",
      "exact_requirement": "one countable row per denominator per timing-family/target-model pair",
      "status": "POLICY_FROZEN"
    },
    {
      "blocker_id": "B6_SAMPLE_SIZE",
      "exact_requirement": "single-packet result-or-impossibility allowed only after G12/G0 audit; aggregate descriptive summary requires >=30 unique duplicate groups; validation dossier requires >=50 unique duplicate groups, DSR/PBO/effective-N computable or explicitly not_computable",
      "status": "NOT_A_PREREGISTRATION_BLOCKER_VALIDATION_BLOCKER_ONLY"
    }
  ],
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "databento_calls": 0,
  "date_stamp": "2026-05-07",
  "generated_at_utc": "2026-05-07T11:29:43Z",
  "git_branch_at_build": "cnr-timing-model-preregistration",
  "git_head_at_build": "6aa3d07a docs: refresh research state after cnr small-n mandate",
  "lane_id": "CNR_TIMING_MODEL_PREREGISTRATION",
  "ledger_verdict": "NO_SMALL_N_STOPPAGE_PREREGISTRATION_FROZEN_WITH_EXACT_EXPANSION_REQUIREMENTS",
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-061",
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "statistical_handling": {
    "dsr_pbo_effective_n": "required when computable; otherwise report not_computable with exact reason",
    "n_20_to_29": "descriptive only; no aggregate lift claim",
    "n_at_least_30": "aggregate quarantined result summary can be reported with concentration and duplicate audit",
    "n_less_than_20": "no significance claim; failure anatomy only",
    "validation_floor": ">=50 unique duplicate groups plus DSR/PBO/effective-N diagnostics; promotion still requires separate dossier"
  },
  "target_record_id": "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00",
  "validation_safe": false
}
```
