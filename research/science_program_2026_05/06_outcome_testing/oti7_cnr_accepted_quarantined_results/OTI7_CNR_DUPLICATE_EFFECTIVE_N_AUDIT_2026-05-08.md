# OTI7 CNR Duplicate Effective-N Audit - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `False`  
**Outcome review opened:** `False`  
**Live effect:** `False`

```json
{
  "accepted_blocker_row_number_overlap_count": 0,
  "accepted_blocker_row_sha_overlap_count": 0,
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "OTI7_CNR_ACCEPTED_QUARANTINED_RESULTS",
  "artifact_type": "duplicate_effective_n_audit",
  "blocked_packet_outcome_source_read": false,
  "blocked_rows_excluded": 6098,
  "broker_actual_r_accessed": false,
  "by_countable_policy": {
    "countable": {
      "countable_rows": 54,
      "r_summary": {
        "mean_r": -0.755473,
        "median_r": -1.0,
        "scored_rows": 44,
        "stop_first": 34,
        "target_first": 10,
        "total_r": -33.240792
      },
      "rows": 54,
      "status_counts": {
        "SCORED_STOP_FIRST": 34,
        "SCORED_TARGET_FIRST": 10,
        "UNSCOREABLE_MISSING_SOURCE_GEOMETRY": 4,
        "UNSCOREABLE_STOP_INVALID_AT_EXECUTABLE_ENTRY": 6
      },
      "unique_duplicate_groups": 27
    },
    "duplicate_context": {
      "countable_rows": 0,
      "r_summary": {
        "mean_r": -0.930745,
        "median_r": -1.0,
        "scored_rows": 32,
        "stop_first": 30,
        "target_first": 2,
        "total_r": -29.78383
      },
      "rows": 48,
      "status_counts": {
        "SCORED_STOP_FIRST": 30,
        "SCORED_TARGET_FIRST": 2,
        "UNSCOREABLE_MISSING_SOURCE_GEOMETRY": 4,
        "UNSCOREABLE_STOP_INVALID_AT_EXECUTABLE_ENTRY": 12
      },
      "unique_duplicate_groups": 13
    }
  },
  "databento_calls": 0,
  "duplicate_group_status_counts": {
    "G6_CNR|XAGUSD|2026-05-04|london|SHORT|75.471": {
      "UNSCOREABLE_MISSING_SOURCE_GEOMETRY": 2
    },
    "G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222": {
      "UNSCOREABLE_MISSING_SOURCE_GEOMETRY": 6
    },
    "G6_EXHAUSTION|GBPJPY|2026-05-04|tokyo|LONG|LONG": {
      "SCORED_STOP_FIRST": 6
    },
    "G6_EXHAUSTION|GBPJPY|2026-05-06|london|LONG|LONG": {
      "SCORED_STOP_FIRST": 4
    },
    "G6_EXHAUSTION|GBPJPY|2026-05-06|tokyo|LONG|LONG": {
      "SCORED_STOP_FIRST": 2
    },
    "G6_EXHAUSTION|NAS100|2026-05-04|london|LONG|LONG": {
      "SCORED_STOP_FIRST": 2
    },
    "G6_EXHAUSTION|XAGUSD|2026-05-04|london|SHORT|LONG": {
      "SCORED_TARGET_FIRST": 2
    },
    "G6_EXHAUSTION|XAGUSD|2026-05-05|ny|SHORT|LONG": {
      "SCORED_STOP_FIRST": 6
    },
    "G6_EXHAUSTION|XAGUSD|2026-05-06|london|SHORT|LONG": {
      "UNSCOREABLE_STOP_INVALID_AT_EXECUTABLE_ENTRY": 6
    },
    "G6_EXHAUSTION|XAUUSD|2026-05-05|london|SHORT|LONG": {
      "SCORED_STOP_FIRST": 2
    },
    "G6_EXHAUSTION|XAUUSD|2026-05-06|london|SHORT|LONG": {
      "SCORED_TARGET_FIRST": 2
    },
    "G6_OB_GENERIC|GBPJPY|2026-05-04|tokyo|LONG|213.257": {
      "SCORED_STOP_FIRST": 4
    },
    "G6_OB_GENERIC|GBPJPY|2026-05-06|london|LONG|212.397": {
      "SCORED_STOP_FIRST": 2
    },
    "G6_OB_GENERIC|GBPJPY|2026-05-06|tokyo|LONG|213.914": {
      "SCORED_STOP_FIRST": 2
    },
    "G6_OB_GENERIC|NAS100|2026-05-04|london|LONG|27714.5": {
      "SCORED_STOP_FIRST": 2
    },
    "G6_OB_GENERIC|XAGUSD|2026-05-04|london|SHORT|75.63": {
      "SCORED_TARGET_FIRST": 2
    },
    "G6_OB_GENERIC|XAGUSD|2026-05-05|ny|SHORT|73.597": {
      "SCORED_STOP_FIRST": 6
    },
    "G6_OB_GENERIC|XAGUSD|2026-05-06|london|SHORT|73.597": {
      "UNSCOREABLE_STOP_INVALID_AT_EXECUTABLE_ENTRY": 6
    },
    "G6_OB_GENERIC|XAUUSD|2026-05-05|london|SHORT|4569.31": {
      "SCORED_STOP_FIRST": 2
    },
    "G6_OPENING_DRIVE|GBPJPY|2026-05-04|tokyo|NO_BREAKOUT_ASOF": {
      "SCORED_STOP_FIRST": 6
    },
    "G6_OPENING_DRIVE|GBPJPY|2026-05-06|london|NO_BREAKOUT_ASOF": {
      "SCORED_STOP_FIRST": 4
    },
    "G6_OPENING_DRIVE|GBPJPY|2026-05-06|tokyo|NO_BREAKOUT_ASOF": {
      "SCORED_STOP_FIRST": 2
    },
    "G6_OPENING_DRIVE|NAS100|2026-05-04|london|NO_BREAKOUT_ASOF": {
      "SCORED_STOP_FIRST": 2
    },
    "G6_OPENING_DRIVE|XAGUSD|2026-05-04|london|NO_BREAKOUT_ASOF": {
      "SCORED_TARGET_FIRST": 2
    },
    "G6_OPENING_DRIVE|XAGUSD|2026-05-05|ny|NO_BREAKOUT_ASOF": {
      "SCORED_STOP_FIRST": 6
    },
    "G6_OPENING_DRIVE|XAGUSD|2026-05-06|london|NO_BREAKOUT_ASOF": {
      "UNSCOREABLE_STOP_INVALID_AT_EXECUTABLE_ENTRY": 6
    },
    "G6_OPENING_DRIVE|XAUUSD|2026-05-05|london|NO_BREAKOUT_ASOF": {
      "SCORED_STOP_FIRST": 2
    },
    "G6_OPENING_DRIVE|XAUUSD|2026-05-06|london|NO_BREAKOUT_ASOF": {
      "SCORED_TARGET_FIRST": 2
    },
    "G6_XAU_ROUND_OB|2026-05-05|SHORT|4569.3": {
      "SCORED_STOP_FIRST": 2
    },
    "G6_XAU_ROUND_OB|2026-05-06|SHORT|4672.1": {
      "SCORED_TARGET_FIRST": 2
    }
  },
  "g12_duplicate_policy": "one countable row per duplicate_group_id per packet/timing_model_family/target_model_family",
  "g12_ready_countable_rows": 54,
  "g12_ready_countable_unique_primary_duplicate_groups": 27,
  "g12_ready_noncountable_duplicate_context_rows": 48,
  "g12_ready_rows": 102,
  "g12_ready_unique_primary_duplicate_groups": 30,
  "generated_at_utc": "2026-05-08T01:56:25Z",
  "live_effect": false,
  "live_trade_results_accessed": false,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "outcome_review_opened": false,
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "result_countable_rows": 54,
  "result_duplicate_context_rows": 48,
  "result_rows": 102,
  "result_scored_countable_rows": 44,
  "result_scored_countable_unique_primary_duplicate_groups": 22,
  "result_scored_rows": 76,
  "result_status": "RESULT_QUARANTINED_DISCOVERY_ONLY",
  "validation_safe": false
}
```
