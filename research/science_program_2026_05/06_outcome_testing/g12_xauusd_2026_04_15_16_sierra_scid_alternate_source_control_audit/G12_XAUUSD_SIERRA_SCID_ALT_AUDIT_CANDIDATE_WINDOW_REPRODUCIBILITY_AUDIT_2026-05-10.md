# Candidate Window Reproducibility Audit

```json
{
  "all_candidates_have_nearest_records": true,
  "all_candidates_have_plus_minus_60s_rows": true,
  "april16_candidate_rows_remain_contamination_embargo_excluded": true,
  "artifact_family": "candidate_window_reproducibility_audit",
  "candidate_comparison_summary": [
    {
      "candidate_id": "XAUUSD_2026-04-15T14:15:05.007998+00:00",
      "candidate_utc": "2026-04-15T14:15:05.007998Z",
      "comparison_status": "MATCH",
      "contamination_or_embargo_excluded": false,
      "mismatches": [],
      "nearest_abs_delta_ms": 1.9980000000000002,
      "owner_request_id": "OWNER-TICK-0020",
      "rows_m15_context": 890,
      "rows_plus_minus_5_seconds": 10,
      "rows_plus_minus_60_seconds": 120,
      "source_date": "2026-04-15"
    },
    {
      "candidate_id": "XAUUSD_2026-04-16T09:30:05.013547+00:00",
      "candidate_utc": "2026-04-16T09:30:05.013547Z",
      "comparison_status": "MATCH",
      "contamination_or_embargo_excluded": true,
      "mismatches": [],
      "nearest_abs_delta_ms": 16.453,
      "owner_request_id": "OWNER-TICK-0021",
      "rows_m15_context": 794,
      "rows_plus_minus_5_seconds": 10,
      "rows_plus_minus_60_seconds": 112,
      "source_date": "2026-04-16"
    },
    {
      "candidate_id": "XAUUSD_2026-04-16T13:16:01.126537+00:00",
      "candidate_utc": "2026-04-16T13:16:01.126537Z",
      "comparison_status": "MATCH",
      "contamination_or_embargo_excluded": true,
      "mismatches": [],
      "nearest_abs_delta_ms": 316.463,
      "owner_request_id": "OWNER-TICK-0021",
      "rows_m15_context": 849,
      "rows_plus_minus_5_seconds": 11,
      "rows_plus_minus_60_seconds": 110,
      "source_date": "2026-04-16"
    }
  ],
  "candidate_coverage": [
    {
      "candidate_coverage_status": "SCID_RECORDS_PRESENT_AROUND_CANDIDATE",
      "candidate_id": "XAUUSD_2026-04-15T14:15:05.007998+00:00",
      "candidate_utc": "2026-04-15T14:15:05.007998Z",
      "contamination_or_embargo_excluded": false,
      "inside_requested_utc_day": true,
      "m15_context_summary": {
        "end_utc": "2026-04-15T14:30:00Z",
        "first_close": 4828.8203125,
        "first_timestamp_utc": "2026-04-15T14:15:00.021000Z",
        "last_close": 4825.35986328125,
        "last_timestamp_utc": "2026-04-15T14:29:59.227000Z",
        "max_close": 4830.5302734375,
        "min_close": 4822.43994140625,
        "record_status_anomaly_counts": {},
        "rows": 890,
        "start_utc": "2026-04-15T14:15:00Z",
        "timestamp_resolution": {
          "duplicate_timestamp_count": 0,
          "max_gap_seconds": 3.875,
          "median_positive_delta_us": 1000000,
          "min_positive_delta_us": 42000,
          "non_monotonic_timestamp_count": 0
        },
        "volume_totals": {
          "ask_volume": 9216,
          "bid_volume": 8899,
          "num_trades": 18115,
          "total_volume": 18115
        }
      },
      "nearest_abs_delta_ms": 1.9980000000000002,
      "nearest_records": {
        "at_or_before_record": {
          "abs_delta_to_candidate_ms": 1.9980000000000002,
          "ask_volume": 13,
          "bid_volume": 14,
          "close": 4828.02001953125,
          "delta_to_candidate_seconds": -0.001998,
          "high": 4828.14990234375,
          "index": 8565190,
          "low": 4828.02001953125,
          "num_trades": 27,
          "open": 4828.080078125,
          "record_status_anomalies": [],
          "sierra_datetime_us": 3985424105006000,
          "timestamp_utc": "2026-04-15T14:15:05.006000Z",
          "total_volume": 27
        },
        "at_or_following_record": {
          "abs_delta_to_candidate_ms": 1420.002,
          "ask_volume": 8,
          "bid_volume": 9,
          "close": 4828.02001953125,
          "delta_to_candidate_seconds": 1.420002,
          "high": 4828.02001953125,
          "index": 8565191,
          "low": 4827.91015625,
          "num_trades": 17,
          "open": 4827.9599609375,
          "record_status_anomalies": [],
          "sierra_datetime_us": 3985424106428000,
          "timestamp_utc": "2026-04-15T14:15:06.428000Z",
          "total_volume": 17
        },
        "nearest_record": {
          "abs_delta_to_candidate_ms": 1.9980000000000002,
          "ask_volume": 13,
          "bid_volume": 14,
          "close": 4828.02001953125,
          "delta_to_candidate_seconds": -0.001998,
          "high": 4828.14990234375,
          "index": 8565190,
          "low": 4828.02001953125,
          "num_trades": 27,
          "open": 4828.080078125,
          "record_status_anomalies": [],
          "sierra_datetime_us": 3985424105006000,
          "timestamp_utc": "2026-04-15T14:15:05.006000Z",
          "total_volume": 27
        },
        "strict_preceding_record": {
          "abs_delta_to_candidate_ms": 1.9980000000000002,
          "ask_volume": 13,
          "bid_volume": 14,
          "close": 4828.02001953125,
          "delta_to_candidate_seconds": -0.001998,
          "high": 4828.14990234375,
          "index": 8565190,
          "low": 4828.02001953125,
          "num_trades": 27,
          "open": 4828.080078125,
          "record_status_anomalies": [],
          "sierra_datetime_us": 3985424105006000,
          "timestamp_utc": "2026-04-15T14:15:05.006000Z",
          "total_volume": 27
        }
      },
      "owner_request_id": "OWNER-TICK-0020",
      "plus_minus_5_seconds_summary": {
        "end_utc": "2026-04-15T14:15:10.007998Z",
        "first_close": 4828.8203125,
        "first_timestamp_utc": "2026-04-15T14:15:00.021000Z",
        "last_close": 4828.009765625,
        "last_timestamp_utc": "2026-04-15T14:15:09.043000Z",
        "record_status_anomaly_counts": {},
        "rows": 10,
        "start_utc": "2026-04-15T14:15:00.007998Z",
        "timestamp_resolution": {
          "duplicate_timestamp_count": 0,
          "max_gap_seconds": 1.422,
          "median_positive_delta_us": 985000,
          "min_positive_delta_us": 594000,
          "non_monotonic_timestamp_count": 0
        },
        "volume_totals": {
          "ask_volume": 110,
          "bid_volume": 127,
          "num_trades": 237,
          "total_volume": 237
        }
      },
      "plus_minus_60_seconds_summary": {
        "end_utc": "2026-04-15T14:16:05.007998Z",
        "first_close": 4826.2998046875,
        "first_timestamp_utc": "2026-04-15T14:14:05.238000Z",
        "last_close": 4825.72998046875,
        "last_timestamp_utc": "2026-04-15T14:16:04.419000Z",
        "max_close": 4829.080078125,
        "min_close": 4825.25,
        "record_status_anomaly_counts": {},
        "rows": 120,
        "start_utc": "2026-04-15T14:14:05.007998Z",
        "timestamp_resolution": {
          "duplicate_timestamp_count": 0,
          "max_gap_seconds": 1.911,
          "median_positive_delta_us": 1000000,
          "min_positive_delta_us": 107000,
          "non_monotonic_timestamp_count": 0
        },
        "volume_totals": {
          "ask_volume": 986,
          "bid_volume": 927,
          "num_trades": 1913,
          "total_volume": 1913
        }
      },
      "rows_m15_context": 890,
      "rows_plus_minus_5_seconds": 10,
      "rows_plus_minus_60_seconds": 120,
      "source_date": "2026-04-15",
      "target_mt5_tick_path": "data/ticks/XAUUSD/2026-04-15.parquet"
    },
    {
      "candidate_coverage_status": "SCID_RECORDS_PRESENT_AROUND_CANDIDATE",
      "candidate_id": "XAUUSD_2026-04-16T09:30:05.013547+00:00",
      "candidate_utc": "2026-04-16T09:30:05.013547Z",
      "contamination_or_embargo_excluded": true,
      "inside_requested_utc_day": true,
      "m15_context_summary": {
        "end_utc": "2026-04-16T09:45:00Z",
        "first_close": 4813.33984375,
        "first_timestamp_utc": "2026-04-16T09:30:00.027000Z",
        "last_close": 4814.85986328125,
        "last_timestamp_utc": "2026-04-16T09:44:59.338000Z",
        "max_close": 4814.89990234375,
        "min_close": 4807.0302734375,
        "record_status_anomaly_counts": {},
        "rows": 794,
        "start_utc": "2026-04-16T09:30:00Z",
        "timestamp_resolution": {
          "duplicate_timestamp_count": 0,
          "max_gap_seconds": 4.443,
          "median_positive_delta_us": 1019000,
          "min_positive_delta_us": 13000,
          "non_monotonic_timestamp_count": 0
        },
        "volume_totals": {
          "ask_volume": 4983,
          "bid_volume": 4622,
          "num_trades": 9605,
          "total_volume": 9605
        }
      },
      "nearest_abs_delta_ms": 16.453,
      "nearest_records": {
        "at_or_before_record": {
          "abs_delta_to_candidate_ms": 774.547,
          "ask_volume": 4,
          "bid_volume": 12,
          "close": 4812.6103515625,
          "delta_to_candidate_seconds": -0.774547,
          "high": 4812.85009765625,
          "index": 8620277,
          "low": 4812.6103515625,
          "num_trades": 16,
          "open": 4812.77001953125,
          "record_status_anomalies": [],
          "sierra_datetime_us": 3985493404239000,
          "timestamp_utc": "2026-04-16T09:30:04.239000Z",
          "total_volume": 16
        },
        "at_or_following_record": {
          "abs_delta_to_candidate_ms": 16.453,
          "ask_volume": 9,
          "bid_volume": 13,
          "close": 4812.5498046875,
          "delta_to_candidate_seconds": 0.016453,
          "high": 4812.89990234375,
          "index": 8620278,
          "low": 4812.5498046875,
          "num_trades": 22,
          "open": 4812.6298828125,
          "record_status_anomalies": [],
          "sierra_datetime_us": 3985493405030000,
          "timestamp_utc": "2026-04-16T09:30:05.030000Z",
          "total_volume": 22
        },
        "nearest_record": {
          "abs_delta_to_candidate_ms": 16.453,
          "ask_volume": 9,
          "bid_volume": 13,
          "close": 4812.5498046875,
          "delta_to_candidate_seconds": 0.016453,
          "high": 4812.89990234375,
          "index": 8620278,
          "low": 4812.5498046875,
          "num_trades": 22,
          "open": 4812.6298828125,
          "record_status_anomalies": [],
          "sierra_datetime_us": 3985493405030000,
          "timestamp_utc": "2026-04-16T09:30:05.030000Z",
          "total_volume": 22
        },
        "strict_preceding_record": {
          "abs_delta_to_candidate_ms": 774.547,
          "ask_volume": 4,
          "bid_volume": 12,
          "close": 4812.6103515625,
          "delta_to_candidate_seconds": -0.774547,
          "high": 4812.85009765625,
          "index": 8620277,
          "low": 4812.6103515625,
          "num_trades": 16,
          "open": 4812.77001953125,
          "record_status_anomalies": [],
          "sierra_datetime_us": 3985493404239000,
          "timestamp_utc": "2026-04-16T09:30:04.239000Z",
          "total_volume": 16
        }
      },
      "owner_request_id": "OWNER-TICK-0021",
      "plus_minus_5_seconds_summary": {
        "end_utc": "2026-04-16T09:30:10.013547Z",
        "first_close": 4813.33984375,
        "first_timestamp_utc": "2026-04-16T09:30:00.027000Z",
        "last_close": 4812.0703125,
        "last_timestamp_utc": "2026-04-16T09:30:09.018000Z",
        "record_status_anomaly_counts": {},
        "rows": 10,
        "start_utc": "2026-04-16T09:30:00.013547Z",
        "timestamp_resolution": {
          "duplicate_timestamp_count": 0,
          "max_gap_seconds": 1.22,
          "median_positive_delta_us": 998000,
          "min_positive_delta_us": 791000,
          "non_monotonic_timestamp_count": 0
        },
        "volume_totals": {
          "ask_volume": 80,
          "bid_volume": 120,
          "num_trades": 200,
          "total_volume": 200
        }
      },
      "plus_minus_60_seconds_summary": {
        "end_utc": "2026-04-16T09:31:05.013547Z",
        "first_close": 4814.08984375,
        "first_timestamp_utc": "2026-04-16T09:29:05.217000Z",
        "last_close": 4809.97998046875,
        "last_timestamp_utc": "2026-04-16T09:31:04.052000Z",
        "max_close": 4814.08984375,
        "min_close": 4809.68994140625,
        "record_status_anomaly_counts": {},
        "rows": 112,
        "start_utc": "2026-04-16T09:29:05.013547Z",
        "timestamp_resolution": {
          "duplicate_timestamp_count": 0,
          "max_gap_seconds": 2.562,
          "median_positive_delta_us": 1013000,
          "min_positive_delta_us": 55000,
          "non_monotonic_timestamp_count": 0
        },
        "volume_totals": {
          "ask_volume": 881,
          "bid_volume": 957,
          "num_trades": 1838,
          "total_volume": 1838
        }
      },
      "rows_m15_context": 794,
      "rows_plus_minus_5_seconds": 10,
      "rows_plus_minus_60_seconds": 112,
      "source_date": "2026-04-16",
      "target_mt5_tick_path": "data/ticks/XAUUSD/2026-04-16.parquet"
    },
    {
      "candidate_coverage_status": "SCID_RECORDS_PRESENT_AROUND_CANDIDATE",
      "candidate_id": "XAUUSD_2026-04-16T13:16:01.126537+00:00",
      "candidate_utc": "2026-04-16T13:16:01.126537Z",
      "contamination_or_embargo_excluded": true,
      "inside_requested_utc_day": true,
      "m15_context_summary": {
        "end_utc": "2026-04-16T13:30:00Z",
        "first_close": 4817.83984375,
        "first_timestamp_utc": "2026-04-16T13:15:00.098000Z",
        "last_close": 4815.740234375,
        "last_timestamp_utc": "2026-04-16T13:29:59.066000Z",
        "max_close": 4821.25,
        "min_close": 4815.14990234375,
        "record_status_anomaly_counts": {},
        "rows": 849,
        "start_utc": "2026-04-16T13:15:00Z",
        "timestamp_resolution": {
          "duplicate_timestamp_count": 0,
          "max_gap_seconds": 3.491,
          "median_positive_delta_us": 1011500,
          "min_positive_delta_us": 35000,
          "non_monotonic_timestamp_count": 0
        },
        "volume_totals": {
          "ask_volume": 4376,
          "bid_volume": 4492,
          "num_trades": 8868,
          "total_volume": 8868
        }
      },
      "nearest_abs_delta_ms": 316.463,
      "nearest_records": {
        "at_or_before_record": {
          "abs_delta_to_candidate_ms": 970.537,
          "ask_volume": 1,
          "bid_volume": 0,
          "close": 4818.169921875,
          "delta_to_candidate_seconds": -0.970537,
          "high": 4818.169921875,
          "index": 8631981,
          "low": 4818.169921875,
          "num_trades": 1,
          "open": 4818.169921875,
          "record_status_anomalies": [],
          "sierra_datetime_us": 3985506960156000,
          "timestamp_utc": "2026-04-16T13:16:00.156000Z",
          "total_volume": 1
        },
        "at_or_following_record": {
          "abs_delta_to_candidate_ms": 316.463,
          "ask_volume": 3,
          "bid_volume": 1,
          "close": 4818.2099609375,
          "delta_to_candidate_seconds": 0.316463,
          "high": 4818.2099609375,
          "index": 8631982,
          "low": 4818.16015625,
          "num_trades": 4,
          "open": 4818.16015625,
          "record_status_anomalies": [],
          "sierra_datetime_us": 3985506961443000,
          "timestamp_utc": "2026-04-16T13:16:01.443000Z",
          "total_volume": 4
        },
        "nearest_record": {
          "abs_delta_to_candidate_ms": 316.463,
          "ask_volume": 3,
          "bid_volume": 1,
          "close": 4818.2099609375,
          "delta_to_candidate_seconds": 0.316463,
          "high": 4818.2099609375,
          "index": 8631982,
          "low": 4818.16015625,
          "num_trades": 4,
          "open": 4818.16015625,
          "record_status_anomalies": [],
          "sierra_datetime_us": 3985506961443000,
          "timestamp_utc": "2026-04-16T13:16:01.443000Z",
          "total_volume": 4
        },
        "strict_preceding_record": {
          "abs_delta_to_candidate_ms": 970.537,
          "ask_volume": 1,
          "bid_volume": 0,
          "close": 4818.169921875,
          "delta_to_candidate_seconds": -0.970537,
          "high": 4818.169921875,
          "index": 8631981,
          "low": 4818.169921875,
          "num_trades": 1,
          "open": 4818.169921875,
          "record_status_anomalies": [],
          "sierra_datetime_us": 3985506960156000,
          "timestamp_utc": "2026-04-16T13:16:00.156000Z",
          "total_volume": 1
        }
      },
      "owner_request_id": "OWNER-TICK-0021",
      "plus_minus_5_seconds_summary": {
        "end_utc": "2026-04-16T13:16:06.126537Z",
        "first_close": 4818.27001953125,
        "first_timestamp_utc": "2026-04-16T13:15:56.601000Z",
        "last_close": 4818.4296875,
        "last_timestamp_utc": "2026-04-16T13:16:06.096000Z",
        "record_status_anomaly_counts": {},
        "rows": 11,
        "start_utc": "2026-04-16T13:15:56.126537Z",
        "timestamp_resolution": {
          "duplicate_timestamp_count": 0,
          "max_gap_seconds": 1.974,
          "median_positive_delta_us": 1033500,
          "min_positive_delta_us": 120000,
          "non_monotonic_timestamp_count": 0
        },
        "volume_totals": {
          "ask_volume": 25,
          "bid_volume": 28,
          "num_trades": 53,
          "total_volume": 53
        }
      },
      "plus_minus_60_seconds_summary": {
        "end_utc": "2026-04-16T13:17:01.126537Z",
        "first_close": 4817.8798828125,
        "first_timestamp_utc": "2026-04-16T13:15:01.259000Z",
        "last_close": 4819.759765625,
        "last_timestamp_utc": "2026-04-16T13:17:00.311000Z",
        "max_close": 4819.89990234375,
        "min_close": 4817.14013671875,
        "record_status_anomaly_counts": {},
        "rows": 110,
        "start_utc": "2026-04-16T13:15:01.126537Z",
        "timestamp_resolution": {
          "duplicate_timestamp_count": 0,
          "max_gap_seconds": 2.297,
          "median_positive_delta_us": 1043000,
          "min_positive_delta_us": 120000,
          "non_monotonic_timestamp_count": 0
        },
        "volume_totals": {
          "ask_volume": 471,
          "bid_volume": 446,
          "num_trades": 917,
          "total_volume": 917
        }
      },
      "rows_m15_context": 849,
      "rows_plus_minus_5_seconds": 11,
      "rows_plus_minus_60_seconds": 110,
      "source_date": "2026-04-16",
      "target_mt5_tick_path": "data/ticks/XAUUSD/2026-04-16.parquet"
    }
  ],
  "candidate_window_policy": {
    "diagnostic_near_window": "plus_minus_5_seconds",
    "m15_context_window": "UTC M15 bar containing candidate timestamp",
    "primary_candidate_window": "plus_minus_60_seconds"
  },
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T11:13:20Z",
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
  "route_id": "G12_XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_AUDIT",
  "schema_version": "g12_xauusd_2026_04_15_16_sierra_scid_alternate_source_control_audit_v1",
  "source_path": "C:\\SierraChart\\Data\\XAUUSD.scid",
  "target_route_comparison": {
    "comparison_status": "MATCH",
    "mismatches": []
  },
  "target_route_id": "XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE",
  "validation_safe": false
}
```
