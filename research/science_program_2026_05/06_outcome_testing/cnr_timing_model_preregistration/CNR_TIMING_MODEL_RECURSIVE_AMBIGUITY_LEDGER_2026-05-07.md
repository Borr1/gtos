# CNR Timing Model Recursive Ambiguity Ledger - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "CNR_TIMING_MODEL_RECURSIVE_AMBIGUITY_LEDGER",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "databento_calls": 0,
  "date_stamp": "2026-05-07",
  "generated_at_utc": "2026-05-07T11:29:43Z",
  "git_branch_at_build": "cnr-timing-model-preregistration",
  "git_head_at_build": "6aa3d07a docs: refresh research state after cnr small-n mandate",
  "lane_id": "CNR_TIMING_MODEL_PREREGISTRATION",
  "ledger_verdict": "SATURATED_FOR_PREREGISTRATION_SCOPE_OPEN_AMBIGUITIES_HAVE_EXACT_CAPTURE_REQUIREMENTS",
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-061",
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "question_stack": [
    {
      "answer": "CNR_E0 decision-close entry clock was too late for original TP1 geometry.",
      "question": "What exact failure did OTI6 expose?",
      "status": "ANSWERED"
    },
    {
      "answer": "Yes, CNR_E1/E2/E3/E4 are frozen with source/latency gates; current OTI6 cannot be rescored under them.",
      "question": "Can earlier-entry timing families be frozen without outcome leakage?",
      "status": "ANSWERED"
    },
    {
      "answer": "LONG uses ask, SHORT uses bid, source-hashed quote at/before trigger or inside predeclared latency window.",
      "question": "Which quote-side rules are executable as-of?",
      "status": "ANSWERED"
    },
    {
      "answer": "Original TP1, fixed-R, structural level, and timebox targets are legitimate only if bound before outcomes; alternate targets are rejected for OTI6 rescue.",
      "question": "Which target models are legitimate?",
      "status": "ANSWERED"
    },
    {
      "answer": "Only rows with source hashes, timing fields, quote side, duplicate denominator, target model, and no forbidden labels.",
      "question": "Which rows can join future packets?",
      "status": "ANSWERED"
    },
    {
      "answer": "Small n blocks validation/promotion, not preregistration; exact floors and expansion plan are frozen.",
      "question": "What sample floor blocks future claims?",
      "status": "ANSWERED"
    },
    {
      "answer": "Yes, local packet rows and heavy roots exist; future extraction must remain input-only and source-hashed.",
      "question": "Can local data expand the denominator?",
      "status": "ANSWERED"
    },
    {
      "answer": "No outcome-safe local step can recover signal_emitted_utc or score earlier entries without post-hoc rescue; those are future instrumentation/source-capture requirements.",
      "question": "Does any ambiguity remain locally resolvable now?",
      "status": "NO"
    }
  ],
  "target_record_id": "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00",
  "validation_safe": false
}
```
