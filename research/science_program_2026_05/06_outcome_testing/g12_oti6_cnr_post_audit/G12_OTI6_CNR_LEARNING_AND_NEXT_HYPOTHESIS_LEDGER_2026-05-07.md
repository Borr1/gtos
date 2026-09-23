# G12 OTI6 CNR Learning And Next Hypothesis Ledger - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

- The mechanism is not killed; the preregistered decision-close timing model was too late for this row.
- Next lane is preregistration/control only and does not open scoring.

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "G12_OTI6_CNR_LEARNING_AND_NEXT_HYPOTHESIS_LEDGER",
  "audit_verdict": "PASS_LEARNING_ACCEPTED_NEXT_LANE_IS_CONTROL_ONLY",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "databento_calls": 0,
  "date_stamp": "2026-05-07",
  "evidence_supporting_learning": {
    "cnr_e0_executable_entry": 4648.29,
    "distance_entry_to_tp1_r": 4.62385321,
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
    "original_take_profit_1": 4582.77,
    "oti6_row_teaches": [
      "The original GTOS structural idea had already delivered through TP1 before the CNR_E0 market-entry quote was available.",
      "A no-retrace continuation did occur in lifecycle context, but not in a way that the preregistered decision-close market-entry model can score.",
      "Using CNR_E0 at 4648.29 against original TP1 4582.77 would be an impossible long target geometry, not a profitable R result."
    ]
  },
  "generated_at_utc": "2026-05-07T10:47:40Z",
  "git_head_at_build": "16713c77 docs: refresh research state for g12 oti6 prompt",
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mechanism_interpretation": "CNR_MECHANISM_NOT_DEAD_CNR_E0_DECISION_CLOSE_MARKET_MODEL_TOO_LATE_FOR_THIS_ROW",
  "mt5_order_calls": 0,
  "next_hypothesis_to_register": {
    "lane_id": "CNR_TIMING_MODEL_PREREGISTRATION",
    "one_line_goal_prompt": "/goal Run CNR_TIMING_MODEL_PREREGISTRATION as a preregistration/control lane only from C:\\tmp\\gtos_otb\\G12OTI6 using research\\science_program_2026_05\\06_outcome_testing\\g12_oti6_cnr_post_audit\\G12_OTI6_CNR_DECISION_LEDGER_2026-05-07.json and G12_OTI6_CNR_LEARNING_AND_NEXT_HYPOTHESIS_LEDGER_2026-05-07.json as controlling inputs; complete mandatory GTOS preflight, verify OTI6 target-already-passed learning from files, define earlier-entry/timing candidates, target models, decision-latency/quote-side captures, duplicate policy, no-leak source fields, sample floors, and blocker conditions before any outcome opening, write only preregistration/control artifacts, do not score R or open alternate-target/earlier-entry outcomes, do not use broker actual-R/account-history/live trade results/live order state/paid/API/Databento/MT5 order calls, do not touch live prompts/risk/execution/permissions/safety gates/selectors/canaries/credentials/remotes/order behavior, preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false, and stop with an exact missing source/field/schema/timestamp/access/prereg blocker if the timing model cannot be frozen.",
    "question": "Which earlier-entry/timing model can be frozen before outcomes so target-already-passed states are handled prospectively?",
    "required_controls_before_outcome_opening": [
      "exact executable quote source and quote-side rule for each candidate timing model",
      "predefined target models, including whether original TP1 remains valid or a distinct continuation target is separately registered",
      "decision latency capture and as-of timestamp conventions",
      "duplicate-aware opportunity denominator",
      "sample floor before any result summary",
      "source hashes, no-leak field whitelist, and label-family separation",
      "explicit target-already-passed, no-fill, same-bar, and missing-source terminal states"
    ],
    "scope": "preregistration/control only; no scoring opened"
  },
  "order_calls": 0,
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-061",
  "paid_data_calls": 0,
  "post_hoc_routes_rejected": [
    "Score the post-decision upward path as a CNR_E0 win.",
    "Move the target beyond original TP1 after seeing the path.",
    "Invent an earlier entry after observing that decision-close entry is too late.",
    "Treat synthetic_path_r=null as an OTI6 implementation failure."
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "target_record_id": "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00",
  "terminal_g12_decision": "ACCEPT_AS_QUARANTINED_TARGET_ALREADY_PASSED_DISCOVERY_EVIDENCE",
  "validation_safe": false,
  "what_it_does_not_mean": [
    "It does not prove continuation/no-retrace is dead.",
    "It does not validate an earlier-entry model.",
    "It does not authorize an alternate target beyond original TP1.",
    "It does not permit broker actual-R, live order state, or live trade result inference."
  ],
  "what_the_row_teaches": [
    "The original GTOS LONG idea had already moved beyond original TP1 before a CNR_E0 decision-close market entry could be placed.",
    "The no-retrace continuation context is real-looking for this row, but the preregistered CNR_E0 entry and original TP1 target cannot produce valid R.",
    "The correct learning is timing/model eligibility, not a win/loss result and not a promotion claim."
  ]
}
```
