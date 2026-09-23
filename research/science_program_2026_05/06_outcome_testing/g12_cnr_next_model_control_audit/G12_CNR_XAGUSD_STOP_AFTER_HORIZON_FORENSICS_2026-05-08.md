# G12 CNR XAGUSD Stop After Horizon Forensics - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "G12_CNR_XAGUSD_STOP_AFTER_HORIZON_FORENSICS",
  "bin_source": "non-optimized bins from CNR_RESIDUAL_R_FIELD_AND_BIN_SPEC; no new thresholds selected from outcomes",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "databento_calls": 0,
  "date_stamp": "2026-05-08",
  "decision": "ACCEPT_DISCOVERY_FORENSICS_ONLY",
  "forensics_status": "DISCOVERY_ONLY_MECHANISM_FORENSICS_NO_RESCUE_NO_GATE",
  "generated_at_utc": "2026-05-08T06:23:47Z",
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mechanism_learning": [
    "The May 4 OTI8 target-before-stop rows are described by the upstream artifacts as tiny original-TP1 residual-target cases; G12 treats that as learning evidence only.",
    "The May 5 NY XAGUSD six-row cluster had deeper original-TP1 residual geometry and did not reach a terminal event inside the original horizon.",
    "The source-hashed extension shows all six later hit the original stop after the horizon, so CNR_T3 lifecycle capture is useful for separating unresolved horizon labels from late failures.",
    "The evidence points to a narrow E0/E1 plus original-TP1 timing/target geometry failure mode, not to a validated CNR edge or anti-edge."
  ],
  "mt5_account_calls": 0,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "oti7_context_without_r_scoring": {
    "residual_bin_by_status": {
      "GT_0_TO_0_25_TINY_RESIDUAL": {
        "SCORED_TARGET_FIRST": 6
      },
      "GT_1_0_TO_LT_1_5_BELOW_GTOS_MIN_RR": {
        "SCORED_STOP_FIRST": 18
      },
      "MISSING_OR_STOP_INVALID": {
        "UNSCOREABLE_MISSING_SOURCE_GEOMETRY": 8,
        "UNSCOREABLE_STOP_INVALID_AT_EXECUTABLE_ENTRY": 18
      }
    },
    "row_count": 50,
    "session_counts": {
      "london": 26,
      "ny": 24
    }
  },
  "oti8_xagusd_summary_without_r_scoring": {
    "residual_bin_by_status": {
      "GT_0_TO_0_25_TINY_RESIDUAL": {
        "TARGET_REACHED_BEFORE_STOP": 2
      },
      "GT_1_0_TO_LT_1_5_BELOW_GTOS_MIN_RR": {
        "NO_TERMINAL_WITHIN_ORDERED_HORIZON": 6
      }
    },
    "row_count": 8,
    "session_counts": {
      "london": 2,
      "ny": 6
    },
    "timing_family_counts": {
      "CNR_E0_DECISION_CLOSE_MARKET": 4,
      "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE": 4
    },
    "unique_duplicate_groups": 2
  },
  "outcome_review_opened": false,
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "schema_version": "g12_cnr_next_model_control_audit_v1",
  "source_artifacts": {
    "control_forensics": "research/science_program_2026_05/06_outcome_testing/cnr_next_model_control_pack/CNR_XAGUSD_RESIDUAL_TARGET_FORENSICS_2026-05-08.json",
    "g12_oti8_integrity": "research/science_program_2026_05/06_outcome_testing/g12_oti8_cnr061_post_result_audit/G12_OTI8_CNR061_RESULT_INTEGRITY_AUDIT_2026-05-08.json",
    "oti8_result_ledger": "research/science_program_2026_05/06_outcome_testing/oti8_cnr061_quarantined_results/OTI8_CNR061_RESULT_LEDGER_2026-05-08.json",
    "residual_spec": "research/science_program_2026_05/06_outcome_testing/cnr_geometry_decay_residual_control/CNR_RESIDUAL_R_FIELD_AND_BIN_SPEC_2026-05-08.json"
  },
  "still_not_allowed": [
    "No residual rescue threshold is accepted.",
    "No live invalidity gate is accepted.",
    "No R/performance computation is made for the six lifecycle rows.",
    "No blocked-row scoring or hidden-path label use is allowed."
  ],
  "stop_after_original_horizon_finding": {
    "candidate_closes_utc": [
      "2026-05-05T16:30:00+00:00",
      "2026-05-05T16:45:00+00:00",
      "2026-05-05T17:00:00+00:00"
    ],
    "duplicate_groups": {
      "G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222": 6
    },
    "lifecycle_label_counts": {
      "stop_after_original_horizon": 6
    }
  },
  "validation_safe": false
}
```
