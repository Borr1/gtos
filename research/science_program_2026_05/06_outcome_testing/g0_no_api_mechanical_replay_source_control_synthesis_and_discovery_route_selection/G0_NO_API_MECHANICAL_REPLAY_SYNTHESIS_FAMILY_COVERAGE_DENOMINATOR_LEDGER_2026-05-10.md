# Family Coverage And Denominator Ledger

- **opened_family_count:** `11`
- **raw_candidate_attempts:** `13540033`
- **duplicate_candidate_keys:** `687275`

```json
{
  "artifact_family": "family_coverage_and_denominator_ledger",
  "compact_candidate_rows_suppressed": 12732758,
  "compact_candidate_rows_written": 120000,
  "compact_cap_policy": "Full-stream aggregate counts drive denominator reasoning; compact rows are for schema, examples, and bounded source-safe cross-tabs only.",
  "compact_sample_cross_tabs": {
    "by_family_regime_phase": {
      "adjacent_range_compression_breakout": {
        "bearish_context": 2223,
        "bullish_context": 2339,
        "range_or_mixed": 422
      },
      "baseline_mean_reversion": {
        "bearish_context": 4226,
        "bullish_context": 4462,
        "insufficient_history": 6,
        "range_or_mixed": 1165
      },
      "baseline_momentum_continuation": {
        "bearish_context": 7686,
        "bullish_context": 7861,
        "insufficient_history": 11,
        "range_or_mixed": 1775
      },
      "baseline_random_session_control": {
        "bearish_context": 1514,
        "bullish_context": 1509,
        "insufficient_history": 11,
        "range_or_mixed": 325
      },
      "baseline_shifted_entry_control": {
        "bearish_context": 10398,
        "bullish_context": 10574,
        "insufficient_history": 14,
        "range_or_mixed": 2679
      },
      "breaker_re_entry": {
        "bearish_context": 74,
        "bullish_context": 71,
        "insufficient_history": 1,
        "range_or_mixed": 25
      },
      "fvg_fill": {
        "bearish_context": 5443,
        "bullish_context": 5484,
        "insufficient_history": 8,
        "range_or_mixed": 1296
      },
      "liquidity_stop_run_context": {
        "bearish_context": 12700,
        "bullish_context": 12869,
        "insufficient_history": 7,
        "range_or_mixed": 3300
      },
      "ob_retest": {
        "bearish_context": 6173,
        "bullish_context": 6315,
        "insufficient_history": 11,
        "range_or_mixed": 1597
      },
      "opening_drive_no_fill_lifecycle": {
        "bearish_context": 1406,
        "bullish_context": 1397,
        "insufficient_history": 9,
        "range_or_mixed": 310
      },
      "session_kz_sweep": {
        "bearish_context": 1123,
        "bullish_context": 920,
        "insufficient_history": 4,
        "range_or_mixed": 257
      }
    },
    "by_family_session_or_kill_zone": {
      "adjacent_range_compression_breakout": {
        "London": 1147,
        "NY": 480,
        "outside_configured_kill_zone": 3357
      },
      "baseline_mean_reversion": {
        "London": 2600,
        "NY": 1190,
        "outside_configured_kill_zone": 6069
      },
      "baseline_momentum_continuation": {
        "London": 3751,
        "NY": 1828,
        "outside_configured_kill_zone": 11754
      },
      "baseline_random_session_control": {
        "London": 1677,
        "NY": 1682
      },
      "baseline_shifted_entry_control": {
        "London": 5888,
        "NY": 2845,
        "outside_configured_kill_zone": 14932
      },
      "breaker_re_entry": {
        "London": 35,
        "NY": 22,
        "outside_configured_kill_zone": 114
      },
      "fvg_fill": {
        "London": 2967,
        "NY": 1436,
        "outside_configured_kill_zone": 7828
      },
      "liquidity_stop_run_context": {
        "London": 7131,
        "NY": 3341,
        "outside_configured_kill_zone": 18404
      },
      "ob_retest": {
        "London": 3563,
        "NY": 1698,
        "outside_configured_kill_zone": 8835
      },
      "opening_drive_no_fill_lifecycle": {
        "London": 1641,
        "NY": 1481
      },
      "session_kz_sweep": {
        "London": 1546,
        "NY": 758
      }
    },
    "by_family_source_family": {
      "adjacent_range_compression_breakout": {
        "LOCAL_OHLCV_CSV": 4984
      },
      "baseline_mean_reversion": {
        "LOCAL_OHLCV_CSV": 9859
      },
      "baseline_momentum_continuation": {
        "LOCAL_OHLCV_CSV": 17333
      },
      "baseline_random_session_control": {
        "LOCAL_OHLCV_CSV": 3359
      },
      "baseline_shifted_entry_control": {
        "LOCAL_OHLCV_CSV": 23665
      },
      "breaker_re_entry": {
        "LOCAL_OHLCV_CSV": 171
      },
      "fvg_fill": {
        "LOCAL_OHLCV_CSV": 12231
      },
      "liquidity_stop_run_context": {
        "LOCAL_OHLCV_CSV": 28876
      },
      "ob_retest": {
        "LOCAL_OHLCV_CSV": 14096
      },
      "opening_drive_no_fill_lifecycle": {
        "LOCAL_OHLCV_CSV": 3122
      },
      "session_kz_sweep": {
        "LOCAL_OHLCV_CSV": 2304
      }
    },
    "by_family_symbol": {
      "adjacent_range_compression_breakout": {
        "EURUSD": 4784,
        "GBPUSD": 200
      },
      "baseline_mean_reversion": {
        "EURUSD": 9577,
        "GBPUSD": 282
      },
      "baseline_momentum_continuation": {
        "EURUSD": 16817,
        "GBPUSD": 516
      },
      "baseline_random_session_control": {
        "EURUSD": 2956,
        "GBPUSD": 403
      },
      "baseline_shifted_entry_control": {
        "EURUSD": 22916,
        "GBPUSD": 749
      },
      "breaker_re_entry": {
        "EURUSD": 162,
        "GBPUSD": 9
      },
      "fvg_fill": {
        "EURUSD": 11924,
        "GBPUSD": 307
      },
      "liquidity_stop_run_context": {
        "EURUSD": 28220,
        "GBPUSD": 656
      },
      "ob_retest": {
        "EURUSD": 13683,
        "GBPUSD": 413
      },
      "opening_drive_no_fill_lifecycle": {
        "EURUSD": 2802,
        "GBPUSD": 320
      },
      "session_kz_sweep": {
        "EURUSD": 2014,
        "GBPUSD": 290
      }
    },
    "by_family_timeframe": {
      "adjacent_range_compression_breakout": {
        "H1": 691,
        "H4": 86,
        "M15": 1719,
        "M5": 2488
      },
      "baseline_mean_reversion": {
        "H1": 1105,
        "H4": 204,
        "M15": 3274,
        "M5": 5276
      },
      "baseline_momentum_continuation": {
        "H1": 1972,
        "H4": 347,
        "M15": 5750,
        "M5": 9264
      },
      "baseline_random_session_control": {
        "H1": 1569,
        "M15": 1164,
        "M5": 626
      },
      "baseline_shifted_entry_control": {
        "H1": 2929,
        "H4": 453,
        "M15": 7970,
        "M5": 12313
      },
      "breaker_re_entry": {
        "H1": 32,
        "H4": 4,
        "M15": 48,
        "M5": 87
      },
      "fvg_fill": {
        "H1": 1196,
        "H4": 243,
        "M15": 3848,
        "M5": 6944
      },
      "liquidity_stop_run_context": {
        "H1": 2861,
        "H4": 399,
        "M15": 9733,
        "M5": 15883
      },
      "ob_retest": {
        "H1": 1631,
        "H4": 309,
        "M15": 4700,
        "M5": 7456
      },
      "opening_drive_no_fill_lifecycle": {
        "H1": 1360,
        "M15": 1142,
        "M5": 620
      },
      "session_kz_sweep": {
        "H1": 737,
        "H4": 124,
        "M15": 768,
        "M5": 675
      }
    }
  },
  "duplicate_candidate_keys": 687275,
  "family_rows": [
    {
      "compact_candidate_sample_count": 14096,
      "compact_sample_duplicate_summary": {
        "compact_sample_duplicate_keys": 0,
        "compact_sample_duplicate_rows": 0
      },
      "duplicate_denominator_scope": "global_duplicate_count_only_plus_compact_sample_duplicate_summary",
      "family_group": "core_model_a",
      "family_id": "ob_retest",
      "full_candidate_count": 1553202,
      "suppressed_by_compact_cap": 1539106,
      "terminal_status": "REPLAY_INVENTORY_BUILT",
      "unique_nonduplicate_denominator_scope": "accepted global unique denominator 12852758; per-family unique full denominator requires downstream source-safe aggregation"
    },
    {
      "compact_candidate_sample_count": 12231,
      "compact_sample_duplicate_summary": {
        "compact_sample_duplicate_keys": 0,
        "compact_sample_duplicate_rows": 0
      },
      "duplicate_denominator_scope": "global_duplicate_count_only_plus_compact_sample_duplicate_summary",
      "family_group": "core_model_a",
      "family_id": "fvg_fill",
      "full_candidate_count": 1532652,
      "suppressed_by_compact_cap": 1520421,
      "terminal_status": "REPLAY_INVENTORY_BUILT",
      "unique_nonduplicate_denominator_scope": "accepted global unique denominator 12852758; per-family unique full denominator requires downstream source-safe aggregation"
    },
    {
      "compact_candidate_sample_count": 171,
      "compact_sample_duplicate_summary": {
        "compact_sample_duplicate_keys": 0,
        "compact_sample_duplicate_rows": 0
      },
      "duplicate_denominator_scope": "global_duplicate_count_only_plus_compact_sample_duplicate_summary",
      "family_group": "core_model_a",
      "family_id": "breaker_re_entry",
      "full_candidate_count": 20269,
      "suppressed_by_compact_cap": 20098,
      "terminal_status": "REPLAY_INVENTORY_BUILT",
      "unique_nonduplicate_denominator_scope": "accepted global unique denominator 12852758; per-family unique full denominator requires downstream source-safe aggregation"
    },
    {
      "compact_candidate_sample_count": 3122,
      "compact_sample_duplicate_summary": {
        "compact_sample_duplicate_keys": 0,
        "compact_sample_duplicate_rows": 0
      },
      "duplicate_denominator_scope": "global_duplicate_count_only_plus_compact_sample_duplicate_summary",
      "family_group": "lifecycle_projection",
      "family_id": "opening_drive_no_fill_lifecycle",
      "full_candidate_count": 147780,
      "suppressed_by_compact_cap": 144658,
      "terminal_status": "REPLAY_INVENTORY_BUILT",
      "unique_nonduplicate_denominator_scope": "accepted global unique denominator 12852758; per-family unique full denominator requires downstream source-safe aggregation"
    },
    {
      "compact_candidate_sample_count": 2304,
      "compact_sample_duplicate_summary": {
        "compact_sample_duplicate_keys": 0,
        "compact_sample_duplicate_rows": 0
      },
      "duplicate_denominator_scope": "global_duplicate_count_only_plus_compact_sample_duplicate_summary",
      "family_group": "liquidity_context",
      "family_id": "session_kz_sweep",
      "full_candidate_count": 141507,
      "suppressed_by_compact_cap": 139203,
      "terminal_status": "REPLAY_INVENTORY_BUILT",
      "unique_nonduplicate_denominator_scope": "accepted global unique denominator 12852758; per-family unique full denominator requires downstream source-safe aggregation"
    },
    {
      "compact_candidate_sample_count": 28876,
      "compact_sample_duplicate_summary": {
        "compact_sample_duplicate_keys": 0,
        "compact_sample_duplicate_rows": 0
      },
      "duplicate_denominator_scope": "global_duplicate_count_only_plus_compact_sample_duplicate_summary",
      "family_group": "liquidity_context",
      "family_id": "liquidity_stop_run_context",
      "full_candidate_count": 3165357,
      "suppressed_by_compact_cap": 3136481,
      "terminal_status": "REPLAY_INVENTORY_BUILT",
      "unique_nonduplicate_denominator_scope": "accepted global unique denominator 12852758; per-family unique full denominator requires downstream source-safe aggregation"
    },
    {
      "compact_candidate_sample_count": 3359,
      "compact_sample_duplicate_summary": {
        "compact_sample_duplicate_keys": 0,
        "compact_sample_duplicate_rows": 0
      },
      "duplicate_denominator_scope": "global_duplicate_count_only_plus_compact_sample_duplicate_summary",
      "family_group": "adversarial_baseline",
      "family_id": "baseline_random_session_control",
      "full_candidate_count": 159883,
      "suppressed_by_compact_cap": 156524,
      "terminal_status": "REPLAY_INVENTORY_BUILT",
      "unique_nonduplicate_denominator_scope": "accepted global unique denominator 12852758; per-family unique full denominator requires downstream source-safe aggregation"
    },
    {
      "compact_candidate_sample_count": 23665,
      "compact_sample_duplicate_summary": {
        "compact_sample_duplicate_keys": 0,
        "compact_sample_duplicate_rows": 0
      },
      "duplicate_denominator_scope": "global_duplicate_count_only_plus_compact_sample_duplicate_summary",
      "family_group": "adversarial_baseline",
      "family_id": "baseline_shifted_entry_control",
      "full_candidate_count": 2543496,
      "suppressed_by_compact_cap": 2519831,
      "terminal_status": "REPLAY_INVENTORY_BUILT",
      "unique_nonduplicate_denominator_scope": "accepted global unique denominator 12852758; per-family unique full denominator requires downstream source-safe aggregation"
    },
    {
      "compact_candidate_sample_count": 17333,
      "compact_sample_duplicate_summary": {
        "compact_sample_duplicate_keys": 0,
        "compact_sample_duplicate_rows": 0
      },
      "duplicate_denominator_scope": "global_duplicate_count_only_plus_compact_sample_duplicate_summary",
      "family_group": "simple_baseline",
      "family_id": "baseline_momentum_continuation",
      "full_candidate_count": 1965307,
      "suppressed_by_compact_cap": 1947974,
      "terminal_status": "REPLAY_INVENTORY_BUILT",
      "unique_nonduplicate_denominator_scope": "accepted global unique denominator 12852758; per-family unique full denominator requires downstream source-safe aggregation"
    },
    {
      "compact_candidate_sample_count": 9859,
      "compact_sample_duplicate_summary": {
        "compact_sample_duplicate_keys": 0,
        "compact_sample_duplicate_rows": 0
      },
      "duplicate_denominator_scope": "global_duplicate_count_only_plus_compact_sample_duplicate_summary",
      "family_group": "simple_baseline",
      "family_id": "baseline_mean_reversion",
      "full_candidate_count": 1081043,
      "suppressed_by_compact_cap": 1071184,
      "terminal_status": "REPLAY_INVENTORY_BUILT",
      "unique_nonduplicate_denominator_scope": "accepted global unique denominator 12852758; per-family unique full denominator requires downstream source-safe aggregation"
    },
    {
      "compact_candidate_sample_count": 4984,
      "compact_sample_duplicate_summary": {
        "compact_sample_duplicate_keys": 0,
        "compact_sample_duplicate_rows": 0
      },
      "duplicate_denominator_scope": "global_duplicate_count_only_plus_compact_sample_duplicate_summary",
      "family_group": "source_safe_adjacent",
      "family_id": "adjacent_range_compression_breakout",
      "full_candidate_count": 542262,
      "suppressed_by_compact_cap": 537278,
      "terminal_status": "REPLAY_INVENTORY_BUILT",
      "unique_nonduplicate_denominator_scope": "accepted global unique denominator 12852758; per-family unique full denominator requires downstream source-safe aggregation"
    }
  ],
  "full_candidate_count_by_regime_phase": {
    "bearish_context": 5497199,
    "bullish_context": 5963680,
    "insufficient_history": 5852,
    "range_or_mixed": 1386027
  },
  "full_candidate_count_by_session_or_kill_zone": {
    "London": 1873860,
    "NY": 2091261,
    "Tokyo": 596526,
    "outside_configured_kill_zone": 8291111
  },
  "full_candidate_count_by_source_family": {
    "LOCAL_OHLCV_CSV": 12424441,
    "SIERRA_DERIVED_OHLCV_EXPORT": 428317
  },
  "full_candidate_count_by_symbol": {
    "AUDJPY": 7433,
    "AUDUSD": 7659,
    "BTCUSD": 9788,
    "CHFJPY": 7794,
    "ETHUSD": 9726,
    "EURGBP": 7655,
    "EURJPY": 7528,
    "EURUSD": 131765,
    "GBPJPY": 1855027,
    "GBPUSD": 1898588,
    "GBPUSD_6B": 2080,
    "GER40": 13021,
    "JP225": 7183,
    "NAS100": 1378625,
    "NAS100_MNQ": 3055,
    "NAS100_NQ": 3094,
    "NZDUSD": 112623,
    "SI": 3720,
    "SPX500": 5850,
    "SPX_ES": 2474,
    "SPX_MES": 2536,
    "UK100": 12743,
    "UKOIL_cash": 5887,
    "US30_MYM": 2846,
    "US30_YM": 3173,
    "US30_cash": 1405794,
    "USDCAD": 6476,
    "USDCHF": 7804,
    "USDJPY": 1952256,
    "USDJPY_6J": 1844,
    "USOIL_cash": 5252,
    "VIX": 698,
    "XAGUSD": 1728350,
    "XAGUSD_SI": 1116,
    "XAUUSD": 2075012,
    "XAUUSD_GC": 3098,
    "XAUUSD_MGC": 3098,
    "XAUUSD_SCID": 160087
  },
  "full_candidate_count_by_timeframe": {
    "H1": 524753,
    "H4": 76627,
    "M1": 8319229,
    "M15": 1662686,
    "M5": 2269463
  },
  "opened_family_count": 11,
  "raw_candidate_attempts": 13540033,
  "unique_nonduplicate_candidate_path_label_denominator": 12852758
}
```
