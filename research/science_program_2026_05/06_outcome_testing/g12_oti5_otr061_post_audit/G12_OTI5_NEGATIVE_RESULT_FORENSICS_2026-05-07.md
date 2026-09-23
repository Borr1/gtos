# G12 OTI5 Negative Result Forensics - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

- Uses existing OTI5 row/result ledgers only.
- Explains the SL/no-entry failure anatomy without inventing a rescue rule.

```json
{
  "artifact_family": "G12_OTI5_NEGATIVE_RESULT_FORENSICS",
  "audit_verdict": "NEGATIVE_RESULT_LEARNED_NOT_PROMOTABLE",
  "breakdowns": {
    "by_changepoint_count_positive": {
      "changepoint_count_eq_0": {
        "ENTRY_TOUCHED_THEN_SL": 2,
        "NO_ENTRY_TOUCH_NO_R_SCORED": 2
      },
      "changepoint_count_gt_0": {
        "ENTRY_TOUCHED_THEN_SL": 6,
        "ENTRY_TOUCHED_THEN_TP1": 1,
        "NO_ENTRY_TOUCH_NO_R_SCORED": 6
      }
    },
    "by_session": {
      "london": {
        "ENTRY_TOUCHED_THEN_SL": 5,
        "ENTRY_TOUCHED_THEN_TP1": 1,
        "NO_ENTRY_TOUCH_NO_R_SCORED": 5
      },
      "ny": {
        "ENTRY_TOUCHED_THEN_SL": 1,
        "NO_ENTRY_TOUCH_NO_R_SCORED": 2
      },
      "tokyo": {
        "ENTRY_TOUCHED_THEN_SL": 2,
        "NO_ENTRY_TOUCH_NO_R_SCORED": 1
      }
    },
    "by_side": {
      "LONG": {
        "ENTRY_TOUCHED_THEN_SL": 4,
        "NO_ENTRY_TOUCH_NO_R_SCORED": 4
      },
      "SHORT": {
        "ENTRY_TOUCHED_THEN_SL": 4,
        "ENTRY_TOUCHED_THEN_TP1": 1,
        "NO_ENTRY_TOUCH_NO_R_SCORED": 4
      }
    },
    "by_symbol": {
      "GBPJPY": {
        "ENTRY_TOUCHED_THEN_SL": 3
      },
      "NAS100": {
        "ENTRY_TOUCHED_THEN_SL": 1,
        "ENTRY_TOUCHED_THEN_TP1": 1,
        "NO_ENTRY_TOUCH_NO_R_SCORED": 3
      },
      "US30_cash": {
        "NO_ENTRY_TOUCH_NO_R_SCORED": 1
      },
      "USDJPY": {
        "NO_ENTRY_TOUCH_NO_R_SCORED": 1
      },
      "XAGUSD": {
        "ENTRY_TOUCHED_THEN_SL": 3,
        "NO_ENTRY_TOUCH_NO_R_SCORED": 2
      },
      "XAUUSD": {
        "ENTRY_TOUCHED_THEN_SL": 1,
        "NO_ENTRY_TOUCH_NO_R_SCORED": 1
      }
    }
  },
  "casebook_primary_rows": [
    {
      "changepoint_count": 3,
      "changepoint_score": 0.40622739,
      "decision_asof_utc": "2026-05-04T02:15:00+00:00",
      "decision_to_entry_minutes": 90.071267,
      "distance_from_last_changepoint_bars": 11,
      "entry_first_touch_utc": "2026-05-04T03:45:04.276000Z",
      "entry_to_terminal_minutes": 0.199933,
      "feature_asof_utc_lte_decision_asof_utc": true,
      "record_id": "OTG0-PKT-063|GBPJPY_2026-05-04T02:15:00+00:00",
      "result_status": "ENTRY_TOUCHED_THEN_SL",
      "session": "tokyo",
      "side": "LONG",
      "symbol": "GBPJPY",
      "synthetic_r": -1.0,
      "terminal_event_utc": "2026-05-04T03:45:16.272000Z"
    },
    {
      "changepoint_count": 3,
      "changepoint_score": 0.03907862,
      "decision_asof_utc": "2026-05-04T07:15:00+00:00",
      "decision_to_entry_minutes": 167.337917,
      "distance_from_last_changepoint_bars": 3,
      "entry_first_touch_utc": "2026-05-04T10:02:20.275000Z",
      "entry_to_terminal_minutes": 1.687167,
      "feature_asof_utc_lte_decision_asof_utc": true,
      "record_id": "OTG0-PKT-063|NAS100_2026-05-04T07:15:00+00:00",
      "result_status": "ENTRY_TOUCHED_THEN_SL",
      "session": "london",
      "side": "LONG",
      "symbol": "NAS100",
      "synthetic_r": -1.0,
      "terminal_event_utc": "2026-05-04T10:04:01.505000Z"
    },
    {
      "changepoint_count": 1,
      "changepoint_score": 0.38849345,
      "decision_asof_utc": "2026-05-04T07:15:00+00:00",
      "decision_to_entry_minutes": null,
      "distance_from_last_changepoint_bars": 69,
      "entry_first_touch_utc": null,
      "entry_to_terminal_minutes": null,
      "feature_asof_utc_lte_decision_asof_utc": true,
      "record_id": "OTG0-PKT-063|XAGUSD_2026-05-04T07:15:00+00:00",
      "result_status": "NO_ENTRY_TOUCH_NO_R_SCORED",
      "session": "london",
      "side": "SHORT",
      "symbol": "XAGUSD",
      "synthetic_r": null,
      "terminal_event_utc": null
    },
    {
      "changepoint_count": 1,
      "changepoint_score": 0.0928054,
      "decision_asof_utc": "2026-05-04T07:15:00+00:00",
      "decision_to_entry_minutes": null,
      "distance_from_last_changepoint_bars": 69,
      "entry_first_touch_utc": null,
      "entry_to_terminal_minutes": null,
      "feature_asof_utc_lte_decision_asof_utc": true,
      "record_id": "OTG0-PKT-063|XAUUSD_2026-05-04T07:15:00+00:00",
      "result_status": "NO_ENTRY_TOUCH_NO_R_SCORED",
      "session": "london",
      "side": "SHORT",
      "symbol": "XAUUSD",
      "synthetic_r": null,
      "terminal_event_utc": null
    },
    {
      "changepoint_count": 7,
      "changepoint_score": 0.41509383,
      "decision_asof_utc": "2026-05-04T10:30:00+00:00",
      "decision_to_entry_minutes": 92.378183,
      "distance_from_last_changepoint_bars": 4,
      "entry_first_touch_utc": "2026-05-04T12:02:22.691000Z",
      "entry_to_terminal_minutes": 58.39955,
      "feature_asof_utc_lte_decision_asof_utc": true,
      "record_id": "OTG0-PKT-063|NAS100_2026-05-04T10:30:00+00:00",
      "result_status": "ENTRY_TOUCHED_THEN_TP1",
      "session": "london",
      "side": "SHORT",
      "symbol": "NAS100",
      "synthetic_r": 1.5,
      "terminal_event_utc": "2026-05-04T13:00:46.664000Z"
    },
    {
      "changepoint_count": 0,
      "changepoint_score": 0.35139418,
      "decision_asof_utc": "2026-05-04T13:15:00+00:00",
      "decision_to_entry_minutes": null,
      "distance_from_last_changepoint_bars": null,
      "entry_first_touch_utc": null,
      "entry_to_terminal_minutes": null,
      "feature_asof_utc_lte_decision_asof_utc": true,
      "record_id": "OTG0-PKT-063|NAS100_2026-05-04T13:15:00+00:00",
      "result_status": "NO_ENTRY_TOUCH_NO_R_SCORED",
      "session": "ny",
      "side": "LONG",
      "symbol": "NAS100",
      "synthetic_r": null,
      "terminal_event_utc": null
    },
    {
      "changepoint_count": 2,
      "changepoint_score": 0.21956079,
      "decision_asof_utc": "2026-05-04T13:15:00+00:00",
      "decision_to_entry_minutes": null,
      "distance_from_last_changepoint_bars": 55,
      "entry_first_touch_utc": null,
      "entry_to_terminal_minutes": null,
      "feature_asof_utc_lte_decision_asof_utc": true,
      "record_id": "OTG0-PKT-063|XAGUSD_2026-05-04T13:15:00+00:00",
      "result_status": "NO_ENTRY_TOUCH_NO_R_SCORED",
      "session": "ny",
      "side": "SHORT",
      "symbol": "XAGUSD",
      "synthetic_r": null,
      "terminal_event_utc": null
    },
    {
      "changepoint_count": 0,
      "changepoint_score": 0.56609046,
      "decision_asof_utc": "2026-05-05T00:45:00+00:00",
      "decision_to_entry_minutes": null,
      "distance_from_last_changepoint_bars": null,
      "entry_first_touch_utc": null,
      "entry_to_terminal_minutes": null,
      "feature_asof_utc_lte_decision_asof_utc": true,
      "record_id": "OTG0-PKT-063|USDJPY_2026-05-05T00:45:00+00:00",
      "result_status": "NO_ENTRY_TOUCH_NO_R_SCORED",
      "session": "tokyo",
      "side": "SHORT",
      "symbol": "USDJPY",
      "synthetic_r": null,
      "terminal_event_utc": null
    },
    {
      "changepoint_count": 2,
      "changepoint_score": 0.09782466,
      "decision_asof_utc": "2026-05-05T07:15:00+00:00",
      "decision_to_entry_minutes": null,
      "distance_from_last_changepoint_bars": 21,
      "entry_first_touch_utc": null,
      "entry_to_terminal_minutes": null,
      "feature_asof_utc_lte_decision_asof_utc": true,
      "record_id": "OTG0-PKT-063|NAS100_2026-05-05T07:15:00+00:00",
      "result_status": "NO_ENTRY_TOUCH_NO_R_SCORED",
      "session": "london",
      "side": "LONG",
      "symbol": "NAS100",
      "synthetic_r": null,
      "terminal_event_utc": null
    },
    {
      "changepoint_count": 4,
      "changepoint_score": 0.43015992,
      "decision_asof_utc": "2026-05-05T07:30:00+00:00",
      "decision_to_entry_minutes": 1173.368767,
      "distance_from_last_changepoint_bars": 10,
      "entry_first_touch_utc": "2026-05-06T03:03:22.126000Z",
      "entry_to_terminal_minutes": 167.1661,
      "feature_asof_utc_lte_decision_asof_utc": true,
      "record_id": "OTG0-PKT-063|XAGUSD_2026-05-05T07:30:00+00:00",
      "result_status": "ENTRY_TOUCHED_THEN_SL",
      "session": "london",
      "side": "SHORT",
      "symbol": "XAGUSD",
      "synthetic_r": -1.0,
      "terminal_event_utc": "2026-05-06T05:50:32.092000Z"
    },
    {
      "changepoint_count": 3,
      "changepoint_score": 0.12756197,
      "decision_asof_utc": "2026-05-05T08:00:00+00:00",
      "decision_to_entry_minutes": 58.5849,
      "distance_from_last_changepoint_bars": 57,
      "entry_first_touch_utc": "2026-05-05T08:58:35.094000Z",
      "entry_to_terminal_minutes": 258.707267,
      "feature_asof_utc_lte_decision_asof_utc": true,
      "record_id": "OTG0-PKT-063|XAUUSD_2026-05-05T08:00:00+00:00",
      "result_status": "ENTRY_TOUCHED_THEN_SL",
      "session": "london",
      "side": "SHORT",
      "symbol": "XAUUSD",
      "synthetic_r": -1.0,
      "terminal_event_utc": "2026-05-05T13:17:17.530000Z"
    },
    {
      "changepoint_count": 0,
      "changepoint_score": 0.21132584,
      "decision_asof_utc": "2026-05-05T14:15:00+00:00",
      "decision_to_entry_minutes": 768.368767,
      "distance_from_last_changepoint_bars": null,
      "entry_first_touch_utc": "2026-05-06T03:03:22.126000Z",
      "entry_to_terminal_minutes": 167.1661,
      "feature_asof_utc_lte_decision_asof_utc": true,
      "record_id": "OTG0-PKT-063|XAGUSD_2026-05-05T14:15:00+00:00",
      "result_status": "ENTRY_TOUCHED_THEN_SL",
      "session": "ny",
      "side": "SHORT",
      "symbol": "XAGUSD",
      "synthetic_r": -1.0,
      "terminal_event_utc": "2026-05-06T05:50:32.092000Z"
    },
    {
      "changepoint_count": 1,
      "changepoint_score": 0.08431134,
      "decision_asof_utc": "2026-05-06T02:30:00+00:00",
      "decision_to_entry_minutes": 117.14595,
      "distance_from_last_changepoint_bars": 64,
      "entry_first_touch_utc": "2026-05-06T04:27:08.757000Z",
      "entry_to_terminal_minutes": 0.100333,
      "feature_asof_utc_lte_decision_asof_utc": true,
      "record_id": "OTG0-PKT-063|GBPJPY_2026-05-06T02:30:00+00:00",
      "result_status": "ENTRY_TOUCHED_THEN_SL",
      "session": "tokyo",
      "side": "LONG",
      "symbol": "GBPJPY",
      "synthetic_r": -1.0,
      "terminal_event_utc": "2026-05-06T04:27:14.777000Z"
    },
    {
      "changepoint_count": 2,
      "changepoint_score": 0.50647463,
      "decision_asof_utc": "2026-05-06T07:15:00+00:00",
      "decision_to_entry_minutes": null,
      "distance_from_last_changepoint_bars": 32,
      "entry_first_touch_utc": null,
      "entry_to_terminal_minutes": null,
      "feature_asof_utc_lte_decision_asof_utc": true,
      "record_id": "OTG0-PKT-063|NAS100_2026-05-06T07:15:00+00:00",
      "result_status": "NO_ENTRY_TOUCH_NO_R_SCORED",
      "session": "london",
      "side": "LONG",
      "symbol": "NAS100",
      "synthetic_r": null,
      "terminal_event_utc": null
    },
    {
      "changepoint_count": 1,
      "changepoint_score": 0.12225145,
      "decision_asof_utc": "2026-05-06T07:15:00+00:00",
      "decision_to_entry_minutes": 0.003533,
      "distance_from_last_changepoint_bars": 86,
      "entry_first_touch_utc": "2026-05-06T07:15:00.212000Z",
      "entry_to_terminal_minutes": 0.0,
      "feature_asof_utc_lte_decision_asof_utc": true,
      "record_id": "OTG0-PKT-063|XAGUSD_2026-05-06T07:15:00+00:00",
      "result_status": "ENTRY_TOUCHED_THEN_SL",
      "session": "london",
      "side": "SHORT",
      "symbol": "XAGUSD",
      "synthetic_r": -1.0,
      "terminal_event_utc": "2026-05-06T07:15:00.212000Z"
    },
    {
      "changepoint_count": 0,
      "changepoint_score": 0.41339756,
      "decision_asof_utc": "2026-05-06T07:30:00+00:00",
      "decision_to_entry_minutes": 23.550017,
      "distance_from_last_changepoint_bars": null,
      "entry_first_touch_utc": "2026-05-06T07:53:33.001000Z",
      "entry_to_terminal_minutes": 5.025167,
      "feature_asof_utc_lte_decision_asof_utc": true,
      "record_id": "OTG0-PKT-063|GBPJPY_2026-05-06T07:30:00+00:00",
      "result_status": "ENTRY_TOUCHED_THEN_SL",
      "session": "london",
      "side": "LONG",
      "symbol": "GBPJPY",
      "synthetic_r": -1.0,
      "terminal_event_utc": "2026-05-06T07:58:34.511000Z"
    },
    {
      "changepoint_count": 4,
      "changepoint_score": 0.27702299,
      "decision_asof_utc": "2026-05-06T09:15:00+00:00",
      "decision_to_entry_minutes": null,
      "distance_from_last_changepoint_bars": 11,
      "entry_first_touch_utc": null,
      "entry_to_terminal_minutes": null,
      "feature_asof_utc_lte_decision_asof_utc": true,
      "record_id": "OTG0-PKT-063|US30_cash_2026-05-06T09:15:00+00:00",
      "result_status": "NO_ENTRY_TOUCH_NO_R_SCORED",
      "session": "london",
      "side": "LONG",
      "symbol": "US30_cash",
      "synthetic_r": null,
      "terminal_event_utc": null
    }
  ],
  "failure_anatomy": {
    "adverse_continuation_review": "Supported descriptively by 4 SL rows that failed within five minutes of entry touch, including immediate/near-immediate failures; this is not validation evidence.",
    "headline": "The CUSUM/changepoint construction did not identify a useful continuation-quality state in this frozen discovery subset.",
    "late_or_stale_signal_review": "Partially supported for no-entry rows, where stale or absent last-changepoint distance appears repeatedly, but not sufficient as a full diagnosis because several SL rows also had recent or nonzero changepoint counts.",
    "loss_no_entry_mix": "Eight of 17 duplicate-primary rows never touched entry, and eight of the nine touched rows stopped before TP1; only one NAS100 London SHORT reached TP1.",
    "sample_power_review": "Underpowered by construction: 17 duplicate-primary groups and 9 resolved synthetic rows are enough for failure anatomy, not DSR/PBO/effective-N validation.",
    "wrong_market_condition_review": "Available packet fields cannot prove regime/volatility/liquidity condition mismatch; exact missing fields are predecision continuation-quality, delivery-path, liquidity-sweep, and path-state features."
  },
  "forensics_scope": "Existing OTI5 row/result ledgers only; no excluded-row rescoring, no broker actual-R, no live trade result, no threshold optimization.",
  "future_hypotheses_to_register": [
    "CUSUM/changepoint recency should be logged as context and tested prospectively against continuation quality, not promoted from this subset.",
    "Add predecision delivery-path and adverse-excursion flags so no-entry versus fast-SL failures can be separated before outcome scoring.",
    "Register a no-entry/stale-changepoint diagnostic that predicts failure-to-touch separately from resolved R.",
    "Require enough resolved duplicate groups before comparing changepoint_count partitions with DSR/PBO/effective-N diagnostics."
  ],
  "generated_at_utc": "2026-05-07T09:59:27Z",
  "live_effect": false,
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-063",
  "primary_countable_rows": 17,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "resolved_synthetic_rows": 9,
  "tempting_rescue_routes_rejected": [
    "Do not threshold-mine changepoint_score, count, or recency on these 17 groups.",
    "Do not pull the five excluded blocker rows into the denominator.",
    "Do not mix duplicate non-primary rows into sample floor or effective-N claims.",
    "Do not treat synthetic path-R as broker actual-R or validation evidence."
  ],
  "terminal_g12_decision": "ACCEPT_AS_QUARANTINED_DISCOVERY_EVIDENCE",
  "terminal_status_counts": {
    "ENTRY_TOUCHED_THEN_SL": 8,
    "ENTRY_TOUCHED_THEN_TP1": 1,
    "NO_ENTRY_TOUCH_NO_R_SCORED": 8
  },
  "unanswered_questions_and_exact_capture_requirements": [
    {
      "missing_field_or_capture": "As-of delivery-path/continuation-quality flags before entry touch, frozen before result scoring.",
      "question": "Did the signal fail because continuation quality was poor before entry?"
    },
    {
      "missing_field_or_capture": "As-of volatility/path-state/liquidity-sweep fields joined to each packet row before opening outcomes.",
      "question": "Was the failure driven by volatility/path state or liquidity sweeps?"
    },
    {
      "missing_field_or_capture": "Prospective packet fields separating failure-to-touch, immediate adverse excursion, and post-touch continuation state.",
      "question": "Are fast-SL cases structurally distinct from no-entry cases?"
    }
  ],
  "validation_safe": false,
  "what_losing_rows_had_in_common_before_outcome": [
    "They were selected by a CUSUM/changepoint feature that was as-of safe but not linked to an independent continuation-quality filter.",
    "SL rows were split across side/session/symbol, so the failure is not reducible to one obvious single-symbol denominator error.",
    "Many no-entry rows had stale or absent changepoint recency, suggesting the signal can describe exhaustion without producing an executable retest."
  ],
  "what_single_tp1_row_had_that_losers_lacked": [
    "The lone TP1 row was NAS100 London SHORT with changepoint_count=7 and distance_from_last_changepoint_bars=4.",
    "This is a single descriptive case; using count/recency as a rescue threshold would be post-hoc threshold mining unless preregistered and tested on unseen rows."
  ]
}
```
