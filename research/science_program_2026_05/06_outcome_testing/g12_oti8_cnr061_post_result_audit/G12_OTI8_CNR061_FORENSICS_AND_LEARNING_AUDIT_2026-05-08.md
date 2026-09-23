# G12 OTI8 CNR061 Forensics And Learning Audit - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

- `learning_verdict`: `ACCEPT_TINY_POSITIVE_AND_NO_TERMINAL_PATTERN_AS_QUARANTINED_LEARNING_ONLY`

```json
{
  "accepted_learning_not_promotion": true,
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "G12_OTI8_CNR061_FORENSICS_AND_LEARNING_AUDIT",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "databento_calls": 0,
  "date_stamp": "2026-05-08",
  "g12_oti7_context": {
    "decision": "ACCEPT_AS_QUARANTINED_NEGATIVE_DISCOVERY_EVIDENCE",
    "headline": "CNR E0/E1 market-entry with original TP1 is accepted as a clean quarantined negative discovery result, not rescued or promoted.",
    "oti7_all_rows_raw_summary": {
      "mean_r": -0.829271,
      "median_r": -1.0,
      "scored_rows": 76,
      "stop_first": 64,
      "target_first": 12,
      "total_r": -63.024622
    },
    "oti7_countable_raw_summary": {
      "mean_r": -0.755473,
      "median_r": -1.0,
      "scored_rows": 44,
      "stop_first": 34,
      "target_first": 10,
      "total_r": -33.240792
    }
  },
  "generated_at_utc": "2026-05-08T05:43:40Z",
  "learning_verdict": "ACCEPT_TINY_POSITIVE_AND_NO_TERMINAL_PATTERN_AS_QUARANTINED_LEARNING_ONLY",
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mt5_account_calls": 0,
  "mt5_order_calls": 0,
  "next_source_safe_routes": [
    {
      "exact_next_action": "Build an input-only packet that captures signal_emitted_utc, decision_request_sent_utc, decision_response_received_utc, latency_ms, and pretouch trigger ids before any terminal path is opened.",
      "route": "CNR_E2_E3_E4_TIMING_PACKET_PREREG",
      "status": "NEXT_LANE_SOURCE_SAFE_PREREG_REQUIRED"
    },
    {
      "exact_next_action": "Freeze fixed-R, structural-level, and terminal/timebox target contracts with stop model, quote side, source hashes, duplicate policy, and no-leak tests before scoring.",
      "route": "CNR_T1_T2_T3_TARGET_FAMILY_PREREG",
      "status": "NEXT_LANE_SOURCE_SAFE_PREREG_REQUIRED"
    },
    {
      "exact_next_action": "Create a source-hashed lifecycle/timebox packet for the six May 5 no-terminal rows that records what happens after the four-hour horizon without using broker/account/live labels.",
      "route": "CNR061_NO_TERMINAL_TIMEBOX_LIFECYCLE_LABELS",
      "status": "NEXT_LANE_ALLOWED_AS_INPUT_BUILDER_NOT_RESULT"
    },
    {
      "exact_next_action": "Analyze residual_target_r_from_executable_quote bins and no-terminal continuation behavior across accepted source-safe CNR rows; keep results as discovery until a separate preregistration exists.",
      "route": "XAGUSD_CNR_RESIDUAL_TARGET_FORENSICS",
      "status": "NEXT_LANE_DISCOVERY_FORENSICS_ONLY"
    },
    {
      "exact_next_action": "Draft a non-live gate spec for market entries where original TP1 is already tiny from executable quote; do not wire selector/risk/execution behavior.",
      "route": "CNR_MARKET_ENTRY_INVALIDITY_OR_TINY_RESIDUAL_GATE",
      "status": "SPEC_ONLY_UNTIL_VALIDATION_DOSSIER"
    }
  ],
  "order_calls": 0,
  "oti8_blocker_next_actions": [
    "Run a G12 post-result review over the OTI8 result package before any future synthesis cites it.",
    "Draft a CNR_T4/T5 target preregistration that separates tiny residual-target continuation from deep-target unresolved paths.",
    "Add prospective capture for CNR_E2/E3/E4 timing triggers instead of deriving them after the path is known."
  ],
  "oti8_forensics_input_status": "NEGATIVE_OR_TINY_N_LEARNING_RECORDED_NO_RESCUE",
  "oti8_learning": [
    {
      "evidence": "OTI7 reported OTG0-PKT-061 as unscoreable missing source geometry; CNR061 sidecar rebuilt geometry/quote/path packets for eight rows.",
      "finding": "OTI8 clears OTI7's missing-geometry blocker only for the exact eight G12 CNR061 accepted rows."
    },
    {
      "evidence": "Both E0/E1 rows resolve at +0.054478301R because the executable quote was already very near original TP1.",
      "finding": "The May 4 London XAGUSD target-first rows are tiny residual-target wins, not material edge evidence."
    },
    {
      "evidence": "Six rows retain synthetic_r=null; target and stop gaps remain positive at horizon end.",
      "finding": "The May 5 NY XAGUSD rows are neither wins nor losses under the frozen horizon."
    },
    {
      "evidence": "OTI7 countable scored rows were mean -0.755473R with 34 stop-first vs 10 target-first; OTI8 is n=8 row-level / two duplicate groups and synthetic path-R only.",
      "finding": "OTI8 does not overturn OTI7's broad negative CNR result."
    }
  ],
  "otx_g12_context": {
    "g12_otx_packet_062_acceptance": "ACCEPT_PACKET_062_AS_QUARANTINED_DISCOVERY_ONLY_NO_VALIDATION",
    "reason_for_context": "OTX/G12 OTX establishes the tick-recomputed quarantined evidence pattern and non-promotion boundary used here."
  },
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-061",
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "schema_version": "g12_oti8_cnr061_post_result_audit_v1",
  "still_forbidden_routes": [
    {
      "forbidden_until": "G12/G0/owner-approved source-safe packet rebuild and explicit result lane",
      "reason": "They were excluded by G12 CNR061 and cannot be opened by this audit.",
      "route": "SCORE_THE_94_BLOCKED_ROWS"
    },
    {
      "forbidden_until": "A separately approved broker-label lane with label-family separation",
      "reason": "OTI8 is synthetic ordered-tick path-R only.",
      "route": "USE_BROKER_ACTUAL_R_ACCOUNT_HISTORY_OR_LIVE_ORDER_STATE"
    },
    {
      "forbidden_until": "Separate promotion dossier with validation-safe evidence",
      "reason": "n=8 row-level / two duplicate groups and no DSR/PBO/effective-N support.",
      "route": "PROMOTE_CNR061_OR_CHANGE_LIVE_SELECTORS"
    },
    {
      "forbidden_until": "Target family is preregistered before outcomes",
      "reason": "OTI8 teaches target design questions but cannot rescue itself with invented thresholds.",
      "route": "POST_HOC_TARGET_RESCUE"
    }
  ],
  "validation_safe": false
}
```
