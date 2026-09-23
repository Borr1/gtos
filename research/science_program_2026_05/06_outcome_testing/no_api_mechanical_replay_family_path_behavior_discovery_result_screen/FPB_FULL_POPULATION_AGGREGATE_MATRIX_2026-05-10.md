# Full Population Aggregate Matrix

- Route: `NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_SCREEN`
- Evidence class: `NO_API_DISCOVERY_RESULT_QUARANTINED_ONLY`
- Generated: `2026-05-11T04:20:56+00:00`
- Promotion posture: `NO_PROMOTION_VERDICT`
- Boundary: discovery path-behavior only; no validation, promotion, R, PnL, win-rate, expectancy, broker/account/order/history/deal/position evidence, AI/API, paid/vendor access, or live behavior.

```json
{
  "aggregation_mode": "full_stream_recomputed_from_accepted_source_rows_aggregate_only",
  "artifact_family": "full_population_aggregate_matrix",
  "baseline_control_combined_distribution": {
    "ambiguity_unresolved_count": 307319,
    "continuation_context_touch_count": 1969930,
    "counts": {
      "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0,
      "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1969930,
      "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0,
      "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 3472480,
      "SAME_BAR_CONTEXT_AMBIGUOUS": 248590,
      "UNRESOLVED_AT_SOURCE_END": 238,
      "UNRESOLVED_BY_WINDOW": 58491
    },
    "denominator": 5749729,
    "interpretation_boundary": "DISCOVERY_PATH_LABEL_ONLY_NOT_PERFORMANCE",
    "opening_drive_midpoint_or_extension_context_count": 0,
    "proportions": {
      "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0.0,
      "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 0.34261267,
      "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0.0,
      "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 0.60393803,
      "SAME_BAR_CONTEXT_AMBIGUOUS": 0.04323508,
      "UNRESOLVED_AT_SOURCE_END": 4.139e-05,
      "UNRESOLVED_BY_WINDOW": 0.01017283
    },
    "protective_boundary_context_touch_count": 3472480
  },
  "baseline_control_families": [
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion"
  ],
  "candidate_by_family_regime_phase": {
    "adjacent_range_compression_breakout": {
      "bearish_context": 221535,
      "bullish_context": 274455,
      "range_or_mixed": 46272
    },
    "baseline_mean_reversion": {
      "bearish_context": 451897,
      "bullish_context": 500421,
      "insufficient_history": 492,
      "range_or_mixed": 128233
    },
    "baseline_momentum_continuation": {
      "bearish_context": 846442,
      "bullish_context": 925110,
      "insufficient_history": 920,
      "range_or_mixed": 192835
    },
    "baseline_random_session_control": {
      "bearish_context": 66393,
      "bullish_context": 76193,
      "insufficient_history": 667,
      "range_or_mixed": 16630
    },
    "baseline_shifted_entry_control": {
      "bearish_context": 1089271,
      "bullish_context": 1171137,
      "insufficient_history": 904,
      "range_or_mixed": 282184
    },
    "breaker_re_entry": {
      "bearish_context": 8554,
      "bullish_context": 9140,
      "insufficient_history": 19,
      "range_or_mixed": 2556
    },
    "fvg_fill": {
      "bearish_context": 671469,
      "bullish_context": 703222,
      "insufficient_history": 803,
      "range_or_mixed": 157158
    },
    "liquidity_stop_run_context": {
      "bearish_context": 1360049,
      "bullish_context": 1449196,
      "insufficient_history": 370,
      "range_or_mixed": 355742
    },
    "ob_retest": {
      "bearish_context": 660100,
      "bullish_context": 719010,
      "insufficient_history": 776,
      "range_or_mixed": 173316
    },
    "opening_drive_no_fill_lifecycle": {
      "bearish_context": 61383,
      "bullish_context": 70196,
      "insufficient_history": 580,
      "range_or_mixed": 15621
    },
    "session_kz_sweep": {
      "bearish_context": 60106,
      "bullish_context": 65600,
      "insufficient_history": 321,
      "range_or_mixed": 15480
    }
  },
  "candidate_by_family_session_or_kill_zone": {
    "adjacent_range_compression_breakout": {
      "London": 66306,
      "NY": 65746,
      "Tokyo": 23195,
      "outside_configured_kill_zone": 387015
    },
    "baseline_mean_reversion": {
      "London": 151995,
      "NY": 168116,
      "Tokyo": 47244,
      "outside_configured_kill_zone": 713688
    },
    "baseline_momentum_continuation": {
      "London": 255352,
      "NY": 274435,
      "Tokyo": 81989,
      "outside_configured_kill_zone": 1353531
    },
    "baseline_random_session_control": {
      "London": 64572,
      "NY": 70993,
      "Tokyo": 24318
    },
    "baseline_shifted_entry_control": {
      "London": 356502,
      "NY": 398098,
      "Tokyo": 112439,
      "outside_configured_kill_zone": 1676457
    },
    "breaker_re_entry": {
      "London": 2419,
      "NY": 3355,
      "Tokyo": 1735,
      "outside_configured_kill_zone": 12760
    },
    "fvg_fill": {
      "London": 214724,
      "NY": 237600,
      "Tokyo": 66583,
      "outside_configured_kill_zone": 1013745
    },
    "liquidity_stop_run_context": {
      "London": 433020,
      "NY": 485345,
      "Tokyo": 135533,
      "outside_configured_kill_zone": 2111459
    },
    "ob_retest": {
      "London": 215535,
      "NY": 249949,
      "Tokyo": 65262,
      "outside_configured_kill_zone": 1022456
    },
    "opening_drive_no_fill_lifecycle": {
      "London": 60170,
      "NY": 66251,
      "Tokyo": 21359
    },
    "session_kz_sweep": {
      "London": 53265,
      "NY": 71373,
      "Tokyo": 16869
    }
  },
  "candidate_by_family_side": {
    "adjacent_range_compression_breakout": {
      "LONG": 277578,
      "SHORT": 264684
    },
    "baseline_mean_reversion": {
      "LONG": 534691,
      "SHORT": 546352
    },
    "baseline_momentum_continuation": {
      "LONG": 1014260,
      "SHORT": 951047
    },
    "baseline_random_session_control": {
      "LONG": 79835,
      "SHORT": 80048
    },
    "baseline_shifted_entry_control": {
      "LONG": 1271891,
      "SHORT": 1271605
    },
    "breaker_re_entry": {
      "LONG": 9512,
      "SHORT": 10757
    },
    "fvg_fill": {
      "LONG": 771438,
      "SHORT": 761214
    },
    "liquidity_stop_run_context": {
      "LONG": 1568105,
      "SHORT": 1597252
    },
    "ob_retest": {
      "LONG": 792890,
      "SHORT": 760312
    },
    "opening_drive_no_fill_lifecycle": {
      "LONG": 77638,
      "SHORT": 70142
    },
    "session_kz_sweep": {
      "LONG": 64137,
      "SHORT": 77370
    }
  },
  "candidate_by_family_source_family": {
    "adjacent_range_compression_breakout": {
      "LOCAL_OHLCV_CSV": 523645,
      "SIERRA_DERIVED_OHLCV_EXPORT": 18617
    },
    "baseline_mean_reversion": {
      "LOCAL_OHLCV_CSV": 1042339,
      "SIERRA_DERIVED_OHLCV_EXPORT": 38704
    },
    "baseline_momentum_continuation": {
      "LOCAL_OHLCV_CSV": 1896908,
      "SIERRA_DERIVED_OHLCV_EXPORT": 68399
    },
    "baseline_random_session_control": {
      "LOCAL_OHLCV_CSV": 155233,
      "SIERRA_DERIVED_OHLCV_EXPORT": 4650
    },
    "baseline_shifted_entry_control": {
      "LOCAL_OHLCV_CSV": 2459595,
      "SIERRA_DERIVED_OHLCV_EXPORT": 83901
    },
    "breaker_re_entry": {
      "LOCAL_OHLCV_CSV": 17217,
      "SIERRA_DERIVED_OHLCV_EXPORT": 3052
    },
    "fvg_fill": {
      "LOCAL_OHLCV_CSV": 1473076,
      "SIERRA_DERIVED_OHLCV_EXPORT": 59576
    },
    "liquidity_stop_run_context": {
      "LOCAL_OHLCV_CSV": 3071756,
      "SIERRA_DERIVED_OHLCV_EXPORT": 93601
    },
    "ob_retest": {
      "LOCAL_OHLCV_CSV": 1504756,
      "SIERRA_DERIVED_OHLCV_EXPORT": 48446
    },
    "opening_drive_no_fill_lifecycle": {
      "LOCAL_OHLCV_CSV": 143168,
      "SIERRA_DERIVED_OHLCV_EXPORT": 4612
    },
    "session_kz_sweep": {
      "LOCAL_OHLCV_CSV": 136748,
      "SIERRA_DERIVED_OHLCV_EXPORT": 4759
    }
  },
  "candidate_by_family_symbol": {
    "adjacent_range_compression_breakout": {
      "AUDJPY": 304,
      "AUDUSD": 293,
      "BTCUSD": 432,
      "CHFJPY": 295,
      "ETHUSD": 412,
      "EURGBP": 238,
      "EURJPY": 270,
      "EURUSD": 5447,
      "GBPJPY": 72981,
      "GBPUSD": 80088,
      "GBPUSD_6B": 68,
      "GER40": 545,
      "JP225": 339,
      "NAS100": 61525,
      "NAS100_MNQ": 117,
      "NAS100_NQ": 128,
      "NZDUSD": 4109,
      "SI": 159,
      "SPX500": 268,
      "SPX_ES": 103,
      "SPX_MES": 104,
      "UK100": 540,
      "UKOIL_cash": 283,
      "US30_MYM": 137,
      "US30_YM": 160,
      "US30_cash": 62690,
      "USDCAD": 241,
      "USDCHF": 314,
      "USDJPY": 83750,
      "USDJPY_6J": 70,
      "USOIL_cash": 231,
      "VIX": 19,
      "XAGUSD": 71251,
      "XAGUSD_SI": 59,
      "XAUUSD": 87592,
      "XAUUSD_GC": 108,
      "XAUUSD_MGC": 111,
      "XAUUSD_SCID": 6481
    },
    "baseline_mean_reversion": {
      "AUDJPY": 574,
      "AUDUSD": 592,
      "BTCUSD": 758,
      "CHFJPY": 594,
      "ETHUSD": 771,
      "EURGBP": 598,
      "EURJPY": 565,
      "EURUSD": 10953,
      "GBPJPY": 156128,
      "GBPUSD": 161612,
      "GBPUSD_6B": 266,
      "GER40": 967,
      "JP225": 522,
      "NAS100": 117519,
      "NAS100_MNQ": 303,
      "NAS100_NQ": 308,
      "NZDUSD": 8238,
      "SI": 577,
      "SPX500": 449,
      "SPX_ES": 297,
      "SPX_MES": 301,
      "UK100": 972,
      "UKOIL_cash": 499,
      "US30_MYM": 301,
      "US30_YM": 300,
      "US30_cash": 119555,
      "USDCAD": 495,
      "USDCHF": 584,
      "USDJPY": 160652,
      "USDJPY_6J": 289,
      "USOIL_cash": 449,
      "VIX": 177,
      "XAGUSD": 149330,
      "XAGUSD_SI": 89,
      "XAUUSD": 170742,
      "XAUUSD_GC": 283,
      "XAUUSD_MGC": 290,
      "XAUUSD_SCID": 13144
    },
    "baseline_momentum_continuation": {
      "AUDJPY": 1040,
      "AUDUSD": 1031,
      "BTCUSD": 1411,
      "CHFJPY": 1032,
      "ETHUSD": 1356,
      "EURGBP": 917,
      "EURJPY": 983,
      "EURUSD": 19192,
      "GBPJPY": 275953,
      "GBPUSD": 296331,
      "GBPUSD_6B": 409,
      "GER40": 1785,
      "JP225": 1073,
      "NAS100": 213734,
      "NAS100_MNQ": 506,
      "NAS100_NQ": 517,
      "NZDUSD": 14528,
      "SI": 734,
      "SPX500": 840,
      "SPX_ES": 472,
      "SPX_MES": 482,
      "UK100": 1810,
      "UKOIL_cash": 926,
      "US30_MYM": 518,
      "US30_YM": 559,
      "US30_cash": 218099,
      "USDCAD": 859,
      "USDCHF": 1088,
      "USDJPY": 299662,
      "USDJPY_6J": 404,
      "USOIL_cash": 818,
      "VIX": 143,
      "XAGUSD": 268562,
      "XAGUSD_SI": 194,
      "XAUUSD": 312714,
      "XAUUSD_GC": 491,
      "XAUUSD_MGC": 477,
      "XAUUSD_SCID": 23657
    },
    "baseline_random_session_control": {
      "AUDJPY": 486,
      "AUDUSD": 482,
      "BTCUSD": 649,
      "CHFJPY": 486,
      "ETHUSD": 655,
      "EURGBP": 486,
      "EURJPY": 482,
      "EURUSD": 3568,
      "GBPJPY": 27208,
      "GBPUSD": 20717,
      "GBPUSD_6B": 36,
      "GER40": 748,
      "JP225": 445,
      "NAS100": 7162,
      "NAS100_MNQ": 36,
      "NAS100_NQ": 36,
      "NZDUSD": 6110,
      "SI": 71,
      "SPX500": 355,
      "SPX_ES": 36,
      "SPX_MES": 36,
      "UK100": 758,
      "UKOIL_cash": 320,
      "US30_MYM": 36,
      "US30_YM": 36,
      "US30_cash": 15847,
      "USDCAD": 402,
      "USDCHF": 486,
      "USDJPY": 31198,
      "USDJPY_6J": 36,
      "USOIL_cash": 341,
      "VIX": 43,
      "XAGUSD": 18333,
      "XAGUSD_SI": 43,
      "XAUUSD": 20088,
      "XAUUSD_GC": 36,
      "XAUUSD_MGC": 36,
      "XAUUSD_SCID": 1554
    },
    "baseline_shifted_entry_control": {
      "AUDJPY": 1402,
      "AUDUSD": 1523,
      "BTCUSD": 1731,
      "CHFJPY": 1446,
      "ETHUSD": 1850,
      "EURGBP": 1468,
      "EURJPY": 1412,
      "EURUSD": 25941,
      "GBPJPY": 367777,
      "GBPUSD": 374317,
      "GBPUSD_6B": 396,
      "GER40": 2535,
      "JP225": 1331,
      "NAS100": 274115,
      "NAS100_MNQ": 593,
      "NAS100_NQ": 610,
      "NZDUSD": 21865,
      "SI": 670,
      "SPX500": 1074,
      "SPX_ES": 447,
      "SPX_MES": 483,
      "UK100": 2409,
      "UKOIL_cash": 1113,
      "US30_MYM": 509,
      "US30_YM": 576,
      "US30_cash": 277021,
      "USDCAD": 1287,
      "USDCHF": 1430,
      "USDJPY": 384786,
      "USDJPY_6J": 306,
      "USOIL_cash": 910,
      "VIX": 83,
      "XAGUSD": 342006,
      "XAGUSD_SI": 214,
      "XAUUSD": 414213,
      "XAUUSD_GC": 612,
      "XAUUSD_MGC": 606,
      "XAUUSD_SCID": 32429
    },
    "breaker_re_entry": {
      "AUDJPY": 18,
      "AUDUSD": 19,
      "BTCUSD": 19,
      "CHFJPY": 11,
      "ETHUSD": 19,
      "EURGBP": 7,
      "EURJPY": 4,
      "EURUSD": 188,
      "GBPJPY": 2559,
      "GBPUSD": 3018,
      "GBPUSD_6B": 2,
      "GER40": 19,
      "JP225": 25,
      "NAS100": 2521,
      "NAS100_MNQ": 3,
      "NAS100_NQ": 2,
      "NZDUSD": 148,
      "SI": 1,
      "SPX500": 6,
      "SPX_ES": 1,
      "SPX_MES": 1,
      "UK100": 15,
      "UKOIL_cash": 24,
      "US30_MYM": 5,
      "US30_YM": 10,
      "US30_cash": 2614,
      "USDCAD": 15,
      "USDCHF": 18,
      "USDJPY": 3051,
      "USOIL_cash": 5,
      "VIX": 3,
      "XAGUSD": 2865,
      "XAGUSD_SI": 47,
      "XAUUSD": 2794,
      "XAUUSD_GC": 5,
      "XAUUSD_MGC": 2,
      "XAUUSD_SCID": 205
    },
    "fvg_fill": {
      "AUDJPY": 702,
      "AUDUSD": 749,
      "BTCUSD": 938,
      "CHFJPY": 689,
      "ETHUSD": 911,
      "EURGBP": 544,
      "EURJPY": 630,
      "EURUSD": 13377,
      "GBPJPY": 201202,
      "GBPUSD": 230722,
      "GBPUSD_6B": 218,
      "GER40": 1301,
      "JP225": 769,
      "NAS100": 160140,
      "NAS100_MNQ": 282,
      "NAS100_NQ": 296,
      "NZDUSD": 10606,
      "SI": 391,
      "SPX500": 592,
      "SPX_ES": 190,
      "SPX_MES": 194,
      "UK100": 1333,
      "UKOIL_cash": 650,
      "US30_MYM": 301,
      "US30_YM": 484,
      "US30_cash": 160440,
      "USDCAD": 568,
      "USDCHF": 828,
      "USDJPY": 243035,
      "USDJPY_6J": 155,
      "USOIL_cash": 594,
      "VIX": 87,
      "XAGUSD": 226256,
      "XAGUSD_SI": 296,
      "XAUUSD": 253413,
      "XAUUSD_GC": 313,
      "XAUUSD_MGC": 292,
      "XAUUSD_SCID": 18164
    },
    "liquidity_stop_run_context": {
      "AUDJPY": 1344,
      "AUDUSD": 1427,
      "BTCUSD": 1798,
      "CHFJPY": 1616,
      "ETHUSD": 1758,
      "EURGBP": 1754,
      "EURJPY": 1643,
      "EURUSD": 31777,
      "GBPJPY": 480892,
      "GBPUSD": 465661,
      "GBPUSD_6B": 408,
      "GER40": 2503,
      "JP225": 1166,
      "NAS100": 349660,
      "NAS100_MNQ": 728,
      "NAS100_NQ": 717,
      "NZDUSD": 23955,
      "SI": 575,
      "SPX500": 1041,
      "SPX_ES": 537,
      "SPX_MES": 535,
      "UK100": 2273,
      "UKOIL_cash": 825,
      "US30_MYM": 652,
      "US30_YM": 634,
      "US30_cash": 350788,
      "USDCAD": 1248,
      "USDCHF": 1477,
      "USDJPY": 470114,
      "USDJPY_6J": 331,
      "USOIL_cash": 701,
      "VIX": 34,
      "XAGUSD": 405271,
      "XAGUSD_SI": 27,
      "XAUUSD": 517104,
      "XAUUSD_GC": 785,
      "XAUUSD_MGC": 795,
      "XAUUSD_SCID": 40803
    },
    "ob_retest": {
      "AUDJPY": 856,
      "AUDUSD": 851,
      "BTCUSD": 1212,
      "CHFJPY": 869,
      "ETHUSD": 1155,
      "EURGBP": 830,
      "EURJPY": 834,
      "EURUSD": 15521,
      "GBPJPY": 225972,
      "GBPUSD": 223713,
      "GBPUSD_6B": 200,
      "GER40": 1449,
      "JP225": 802,
      "NAS100": 174657,
      "NAS100_MNQ": 425,
      "NAS100_NQ": 417,
      "NZDUSD": 12132,
      "SI": 439,
      "SPX500": 702,
      "SPX_ES": 306,
      "SPX_MES": 312,
      "UK100": 1468,
      "UKOIL_cash": 733,
      "US30_MYM": 357,
      "US30_YM": 385,
      "US30_cash": 172181,
      "USDCAD": 701,
      "USDCHF": 871,
      "USDJPY": 227828,
      "USDJPY_6J": 191,
      "USOIL_cash": 673,
      "VIX": 60,
      "XAGUSD": 205290,
      "XAGUSD_SI": 91,
      "XAUUSD": 257833,
      "XAUUSD_GC": 395,
      "XAUUSD_MGC": 411,
      "XAUUSD_SCID": 20080
    },
    "opening_drive_no_fill_lifecycle": {
      "AUDJPY": 446,
      "AUDUSD": 437,
      "BTCUSD": 587,
      "CHFJPY": 428,
      "ETHUSD": 577,
      "EURGBP": 421,
      "EURJPY": 435,
      "EURUSD": 3376,
      "GBPJPY": 23994,
      "GBPUSD": 19335,
      "GBPUSD_6B": 36,
      "GER40": 733,
      "JP225": 443,
      "NAS100": 7258,
      "NAS100_MNQ": 32,
      "NAS100_NQ": 32,
      "NZDUSD": 5458,
      "SI": 66,
      "SPX500": 334,
      "SPX_ES": 32,
      "SPX_MES": 32,
      "UK100": 721,
      "UKOIL_cash": 301,
      "US30_MYM": 30,
      "US30_YM": 29,
      "US30_cash": 14113,
      "USDCAD": 385,
      "USDCHF": 437,
      "USDJPY": 27952,
      "USDJPY_6J": 34,
      "USOIL_cash": 322,
      "VIX": 32,
      "XAGUSD": 17820,
      "XAGUSD_SI": 47,
      "XAUUSD": 19538,
      "XAUUSD_GC": 31,
      "XAUUSD_MGC": 31,
      "XAUUSD_SCID": 1465
    },
    "session_kz_sweep": {
      "AUDJPY": 261,
      "AUDUSD": 255,
      "BTCUSD": 253,
      "CHFJPY": 328,
      "ETHUSD": 262,
      "EURGBP": 392,
      "EURJPY": 270,
      "EURUSD": 2425,
      "GBPJPY": 20361,
      "GBPUSD": 23074,
      "GBPUSD_6B": 41,
      "GER40": 436,
      "JP225": 268,
      "NAS100": 10334,
      "NAS100_MNQ": 30,
      "NAS100_NQ": 31,
      "NZDUSD": 5474,
      "SI": 37,
      "SPX500": 189,
      "SPX_ES": 53,
      "SPX_MES": 56,
      "UK100": 444,
      "UKOIL_cash": 213,
      "US30_cash": 12446,
      "USDCAD": 275,
      "USDCHF": 271,
      "USDJPY": 20228,
      "USDJPY_6J": 28,
      "USOIL_cash": 208,
      "VIX": 17,
      "XAGUSD": 21366,
      "XAGUSD_SI": 9,
      "XAUUSD": 18981,
      "XAUUSD_GC": 39,
      "XAUUSD_MGC": 47,
      "XAUUSD_SCID": 2105
    }
  },
  "candidate_by_family_timeframe": {
    "adjacent_range_compression_breakout": {
      "H1": 21271,
      "H4": 2984,
      "M1": 348144,
      "M15": 72263,
      "M5": 97600
    },
    "baseline_mean_reversion": {
      "H1": 35250,
      "H4": 6466,
      "M1": 712818,
      "M15": 133589,
      "M5": 192920
    },
    "baseline_momentum_continuation": {
      "H1": 64073,
      "H4": 11819,
      "M1": 1309715,
      "M15": 238194,
      "M5": 341506
    },
    "baseline_random_session_control": {
      "H1": 58274,
      "M1": 19406,
      "M15": 56586,
      "M5": 25617
    },
    "baseline_shifted_entry_control": {
      "H1": 93830,
      "H4": 15402,
      "M1": 1661528,
      "M15": 322243,
      "M5": 450493
    },
    "breaker_re_entry": {
      "H1": 853,
      "H4": 176,
      "M1": 12960,
      "M15": 2637,
      "M5": 3643
    },
    "fvg_fill": {
      "H1": 40697,
      "H4": 8563,
      "M1": 1073725,
      "M15": 161436,
      "M5": 248231
    },
    "liquidity_stop_run_context": {
      "H1": 85782,
      "H4": 12666,
      "M1": 2109963,
      "M15": 381701,
      "M5": 575245
    },
    "ob_retest": {
      "H1": 52886,
      "H4": 9880,
      "M1": 1010553,
      "M15": 197740,
      "M5": 282143
    },
    "opening_drive_no_fill_lifecycle": {
      "H1": 47775,
      "M1": 19350,
      "M15": 55261,
      "M5": 25394
    },
    "session_kz_sweep": {
      "H1": 24062,
      "H4": 8671,
      "M1": 41067,
      "M15": 41036,
      "M5": 26671
    }
  },
  "changes_live_trading_behavior": false,
  "compact_sample_used_for_decisive_ranking": false,
  "concentration_diagnostics": {
    "source_row_count_with_candidates": 365,
    "top_10_source_rows_candidate_count": 7436388,
    "top_10_source_rows_candidate_share": 0.57858306,
    "top_source_rows": [
      {
        "candidate_count": 1106517,
        "source_row_id": "SRC-02180"
      },
      {
        "candidate_count": 1095491,
        "source_row_id": "SRC-02171"
      },
      {
        "candidate_count": 1081816,
        "source_row_id": "SRC-02184"
      },
      {
        "candidate_count": 1077585,
        "source_row_id": "SRC-02173"
      },
      {
        "candidate_count": 979551,
        "source_row_id": "SRC-02182"
      },
      {
        "candidate_count": 718299,
        "source_row_id": "SRC-02176"
      },
      {
        "candidate_count": 703985,
        "source_row_id": "SRC-02178"
      },
      {
        "candidate_count": 225954,
        "source_row_id": "SRC-02181"
      },
      {
        "candidate_count": 223715,
        "source_row_id": "SRC-02174"
      },
      {
        "candidate_count": 223475,
        "source_row_id": "SRC-02172"
      },
      {
        "candidate_count": 211387,
        "source_row_id": "SRC-02185"
      },
      {
        "candidate_count": 196866,
        "source_row_id": "SRC-02183"
      },
      {
        "candidate_count": 146513,
        "source_row_id": "SRC-02179"
      },
      {
        "candidate_count": 144535,
        "source_row_id": "SRC-02177"
      },
      {
        "candidate_count": 124745,
        "source_row_id": "SRC-00324"
      },
      {
        "candidate_count": 77471,
        "source_row_id": "SRC-00055"
      },
      {
        "candidate_count": 75856,
        "source_row_id": "SRC-01958"
      },
      {
        "candidate_count": 75784,
        "source_row_id": "SRC-00051"
      },
      {
        "candidate_count": 74594,
        "source_row_id": "SRC-02139"
      },
      {
        "candidate_count": 73603,
        "source_row_id": "SRC-01966"
      },
      {
        "candidate_count": 73490,
        "source_row_id": "SRC-02134"
      },
      {
        "candidate_count": 73221,
        "source_row_id": "SRC-00059"
      },
      {
        "candidate_count": 72797,
        "source_row_id": "SRC-02135"
      },
      {
        "candidate_count": 71811,
        "source_row_id": "SRC-02097"
      },
      {
        "candidate_count": 71648,
        "source_row_id": "SRC-00067"
      }
    ]
  },
  "credentials_touched": false,
  "decisive_matrix_source": "full_population_aggregate",
  "duplicate_candidate_keys": 687275,
  "duplicate_path_keys": 0,
  "evidence_class": "NO_API_DISCOVERY_RESULT_QUARANTINED_ONLY",
  "excluded_source_slice_count": 3135,
  "family_rows": [
    {
      "ambiguity_unresolved_count": 45587,
      "candidate_denominator": 1553202,
      "continuation_context_touch_count": 811194,
      "counts": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0,
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 811194,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 696421,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 20665,
        "UNRESOLVED_AT_SOURCE_END": 82,
        "UNRESOLVED_BY_WINDOW": 24840
      },
      "denominator": 1553202,
      "family_id": "ob_retest",
      "interpretation_boundary": "DISCOVERY_PATH_LABEL_ONLY_NOT_PERFORMANCE",
      "opening_drive_midpoint_or_extension_context_count": 0,
      "proportions": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0.0,
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 0.52227205,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0.0,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 0.44837761,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 0.01330477,
        "UNRESOLVED_AT_SOURCE_END": 5.279e-05,
        "UNRESOLVED_BY_WINDOW": 0.01599277
      },
      "protective_boundary_context_touch_count": 696421
    },
    {
      "ambiguity_unresolved_count": 263279,
      "candidate_denominator": 1532652,
      "continuation_context_touch_count": 433391,
      "counts": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0,
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 433391,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 835982,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 252778,
        "UNRESOLVED_AT_SOURCE_END": 60,
        "UNRESOLVED_BY_WINDOW": 10441
      },
      "denominator": 1532652,
      "family_id": "fvg_fill",
      "interpretation_boundary": "DISCOVERY_PATH_LABEL_ONLY_NOT_PERFORMANCE",
      "opening_drive_midpoint_or_extension_context_count": 0,
      "proportions": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0.0,
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 0.28277195,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0.0,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 0.54544802,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 0.1649285,
        "UNRESOLVED_AT_SOURCE_END": 3.915e-05,
        "UNRESOLVED_BY_WINDOW": 0.00681237
      },
      "protective_boundary_context_touch_count": 835982
    },
    {
      "ambiguity_unresolved_count": 694,
      "candidate_denominator": 20269,
      "continuation_context_touch_count": 9485,
      "counts": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0,
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 9485,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 10090,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 437,
        "UNRESOLVED_AT_SOURCE_END": 5,
        "UNRESOLVED_BY_WINDOW": 252
      },
      "denominator": 20269,
      "family_id": "breaker_re_entry",
      "interpretation_boundary": "DISCOVERY_PATH_LABEL_ONLY_NOT_PERFORMANCE",
      "opening_drive_midpoint_or_extension_context_count": 0,
      "proportions": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0.0,
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 0.46795599,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0.0,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 0.49780453,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 0.02156002,
        "UNRESOLVED_AT_SOURCE_END": 0.00024668,
        "UNRESOLVED_BY_WINDOW": 0.01243278
      },
      "protective_boundary_context_touch_count": 10090
    },
    {
      "ambiguity_unresolved_count": 6846,
      "candidate_denominator": 147780,
      "continuation_context_touch_count": 0,
      "counts": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 61385,
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 0,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 79549,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 0,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3189,
        "UNRESOLVED_AT_SOURCE_END": 12,
        "UNRESOLVED_BY_WINDOW": 3645
      },
      "denominator": 147780,
      "family_id": "opening_drive_no_fill_lifecycle",
      "interpretation_boundary": "DISCOVERY_PATH_LABEL_ONLY_NOT_PERFORMANCE",
      "opening_drive_midpoint_or_extension_context_count": 140934,
      "proportions": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0.41538097,
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 0.0,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0.53829341,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 0.0,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 0.02157937,
        "UNRESOLVED_AT_SOURCE_END": 8.12e-05,
        "UNRESOLVED_BY_WINDOW": 0.02466504
      },
      "protective_boundary_context_touch_count": 0
    },
    {
      "ambiguity_unresolved_count": 4893,
      "candidate_denominator": 141507,
      "continuation_context_touch_count": 64258,
      "counts": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0,
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 64258,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 72356,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1715,
        "UNRESOLVED_AT_SOURCE_END": 10,
        "UNRESOLVED_BY_WINDOW": 3168
      },
      "denominator": 141507,
      "family_id": "session_kz_sweep",
      "interpretation_boundary": "DISCOVERY_PATH_LABEL_ONLY_NOT_PERFORMANCE",
      "opening_drive_midpoint_or_extension_context_count": 0,
      "proportions": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0.0,
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 0.45409768,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0.0,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 0.51132453,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 0.01211954,
        "UNRESOLVED_AT_SOURCE_END": 7.067e-05,
        "UNRESOLVED_BY_WINDOW": 0.02238759
      },
      "protective_boundary_context_touch_count": 72356
    },
    {
      "ambiguity_unresolved_count": 41104,
      "candidate_denominator": 3165357,
      "continuation_context_touch_count": 1403208,
      "counts": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0,
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1403208,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1721045,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 24811,
        "UNRESOLVED_AT_SOURCE_END": 122,
        "UNRESOLVED_BY_WINDOW": 16171
      },
      "denominator": 3165357,
      "family_id": "liquidity_stop_run_context",
      "interpretation_boundary": "DISCOVERY_PATH_LABEL_ONLY_NOT_PERFORMANCE",
      "opening_drive_midpoint_or_extension_context_count": 0,
      "proportions": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0.0,
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 0.44330166,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0.0,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 0.54371276,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 0.00783829,
        "UNRESOLVED_AT_SOURCE_END": 3.854e-05,
        "UNRESOLVED_BY_WINDOW": 0.00510874
      },
      "protective_boundary_context_touch_count": 1721045
    },
    {
      "ambiguity_unresolved_count": 4100,
      "candidate_denominator": 159883,
      "continuation_context_touch_count": 55491,
      "counts": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0,
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 55491,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 100292,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3822,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 276
      },
      "denominator": 159883,
      "family_id": "baseline_random_session_control",
      "interpretation_boundary": "DISCOVERY_PATH_LABEL_ONLY_NOT_PERFORMANCE",
      "opening_drive_midpoint_or_extension_context_count": 0,
      "proportions": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0.0,
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 0.34707255,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0.0,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 0.6272837,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 0.02390498,
        "UNRESOLVED_AT_SOURCE_END": 1.251e-05,
        "UNRESOLVED_BY_WINDOW": 0.00172626
      },
      "protective_boundary_context_touch_count": 100292
    },
    {
      "ambiguity_unresolved_count": 166991,
      "candidate_denominator": 2543496,
      "continuation_context_touch_count": 1095593,
      "counts": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0,
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1095593,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1280912,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 110965,
        "UNRESOLVED_AT_SOURCE_END": 140,
        "UNRESOLVED_BY_WINDOW": 55886
      },
      "denominator": 2543496,
      "family_id": "baseline_shifted_entry_control",
      "interpretation_boundary": "DISCOVERY_PATH_LABEL_ONLY_NOT_PERFORMANCE",
      "opening_drive_midpoint_or_extension_context_count": 0,
      "proportions": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0.0,
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 0.43074296,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0.0,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 0.50360292,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 0.04362696,
        "UNRESOLVED_AT_SOURCE_END": 5.504e-05,
        "UNRESOLVED_BY_WINDOW": 0.02197212
      },
      "protective_boundary_context_touch_count": 1280912
    },
    {
      "ambiguity_unresolved_count": 31979,
      "candidate_denominator": 1965307,
      "continuation_context_touch_count": 615758,
      "counts": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0,
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 615758,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1317570,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 29975,
        "UNRESOLVED_AT_SOURCE_END": 64,
        "UNRESOLVED_BY_WINDOW": 1940
      },
      "denominator": 1965307,
      "family_id": "baseline_momentum_continuation",
      "interpretation_boundary": "DISCOVERY_PATH_LABEL_ONLY_NOT_PERFORMANCE",
      "opening_drive_midpoint_or_extension_context_count": 0,
      "proportions": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0.0,
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 0.3133139,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0.0,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 0.67041434,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 0.01525207,
        "UNRESOLVED_AT_SOURCE_END": 3.256e-05,
        "UNRESOLVED_BY_WINDOW": 0.00098712
      },
      "protective_boundary_context_touch_count": 1317570
    },
    {
      "ambiguity_unresolved_count": 104249,
      "candidate_denominator": 1081043,
      "continuation_context_touch_count": 203088,
      "counts": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0,
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 203088,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 773706,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 103828,
        "UNRESOLVED_AT_SOURCE_END": 32,
        "UNRESOLVED_BY_WINDOW": 389
      },
      "denominator": 1081043,
      "family_id": "baseline_mean_reversion",
      "interpretation_boundary": "DISCOVERY_PATH_LABEL_ONLY_NOT_PERFORMANCE",
      "opening_drive_midpoint_or_extension_context_count": 0,
      "proportions": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0.0,
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 0.18786302,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0.0,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 0.71570326,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 0.09604428,
        "UNRESOLVED_AT_SOURCE_END": 2.96e-05,
        "UNRESOLVED_BY_WINDOW": 0.00035984
      },
      "protective_boundary_context_touch_count": 773706
    },
    {
      "ambiguity_unresolved_count": 33714,
      "candidate_denominator": 542262,
      "continuation_context_touch_count": 396812,
      "counts": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0,
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 396812,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 111736,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 510,
        "UNRESOLVED_AT_SOURCE_END": 71,
        "UNRESOLVED_BY_WINDOW": 33133
      },
      "denominator": 542262,
      "family_id": "adjacent_range_compression_breakout",
      "interpretation_boundary": "DISCOVERY_PATH_LABEL_ONLY_NOT_PERFORMANCE",
      "opening_drive_midpoint_or_extension_context_count": 0,
      "proportions": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0.0,
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 0.73177173,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0.0,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 0.20605538,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 0.0009405,
        "UNRESOLVED_AT_SOURCE_END": 0.00013093,
        "UNRESOLVED_BY_WINDOW": 0.06110146
      },
      "protective_boundary_context_touch_count": 111736
    }
  ],
  "full_candidate_count_by_family": {
    "adjacent_range_compression_breakout": 542262,
    "baseline_mean_reversion": 1081043,
    "baseline_momentum_continuation": 1965307,
    "baseline_random_session_control": 159883,
    "baseline_shifted_entry_control": 2543496,
    "breaker_re_entry": 20269,
    "fvg_fill": 1532652,
    "liquidity_stop_run_context": 3165357,
    "ob_retest": 1553202,
    "opening_drive_no_fill_lifecycle": 147780,
    "session_kz_sweep": 141507
  },
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
  "generated_at_utc": "2026-05-11T04:20:56+00:00",
  "global_label_distribution": {
    "ambiguity_unresolved_count": 703436,
    "continuation_context_touch_count": 5088278,
    "counts": {
      "MIDPOINT_RETRACE_BEFORE_EXTENSION": 61385,
      "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 5088278,
      "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 79549,
      "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 6920110,
      "SAME_BAR_CONTEXT_AMBIGUOUS": 552695,
      "UNRESOLVED_AT_SOURCE_END": 600,
      "UNRESOLVED_BY_WINDOW": 150141
    },
    "denominator": 12852758,
    "interpretation_boundary": "DISCOVERY_PATH_LABEL_ONLY_NOT_PERFORMANCE",
    "opening_drive_midpoint_or_extension_context_count": 140934,
    "proportions": {
      "MIDPOINT_RETRACE_BEFORE_EXTENSION": 0.00477602,
      "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 0.39588997,
      "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 0.00618926,
      "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 0.5384144,
      "SAME_BAR_CONTEXT_AMBIGUOUS": 0.04300205,
      "UNRESOLVED_AT_SOURCE_END": 4.668e-05,
      "UNRESOLVED_BY_WINDOW": 0.01168162
    },
    "protective_boundary_context_touch_count": 6920110
  },
  "interpretation_boundary": "All counts are discovery path-behavior ledgers only. They are not R, PnL, cost, slippage, win-rate, expectancy, validation, or promotion evidence.",
  "label_by_family_regime_phase_status": {
    "adjacent_range_compression_breakout": {
      "bearish_context": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 162275,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 45809,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 222,
        "UNRESOLVED_AT_SOURCE_END": 28,
        "UNRESOLVED_BY_WINDOW": 13201
      },
      "bullish_context": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 200516,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 56335,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 238,
        "UNRESOLVED_AT_SOURCE_END": 42,
        "UNRESOLVED_BY_WINDOW": 17324
      },
      "range_or_mixed": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 34021,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 9592,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 50,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 2608
      }
    },
    "baseline_mean_reversion": {
      "bearish_context": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 61866,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 336068,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 53838,
        "UNRESOLVED_AT_SOURCE_END": 13,
        "UNRESOLVED_BY_WINDOW": 112
      },
      "bullish_context": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 116800,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 345636,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 37737,
        "UNRESOLVED_AT_SOURCE_END": 13,
        "UNRESOLVED_BY_WINDOW": 235
      },
      "insufficient_history": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 99,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 348,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 43,
        "UNRESOLVED_BY_WINDOW": 2
      },
      "range_or_mixed": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 24323,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 91654,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 12210,
        "UNRESOLVED_AT_SOURCE_END": 6,
        "UNRESOLVED_BY_WINDOW": 40
      }
    },
    "baseline_momentum_continuation": {
      "bearish_context": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 264381,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 568774,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 12506,
        "UNRESOLVED_AT_SOURCE_END": 31,
        "UNRESOLVED_BY_WINDOW": 750
      },
      "bullish_context": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 290584,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 619355,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 14126,
        "UNRESOLVED_AT_SOURCE_END": 28,
        "UNRESOLVED_BY_WINDOW": 1017
      },
      "insufficient_history": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 279,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 615,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 19,
        "UNRESOLVED_BY_WINDOW": 7
      },
      "range_or_mixed": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 60514,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 128826,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3324,
        "UNRESOLVED_AT_SOURCE_END": 5,
        "UNRESOLVED_BY_WINDOW": 166
      }
    },
    "baseline_random_session_control": {
      "bearish_context": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 22930,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 41754,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1600,
        "UNRESOLVED_BY_WINDOW": 109
      },
      "bullish_context": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 26505,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 47722,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1835,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 129
      },
      "insufficient_history": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 242,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 401,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 21,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "range_or_mixed": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 5814,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 10415,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 366,
        "UNRESOLVED_BY_WINDOW": 35
      }
    },
    "baseline_shifted_entry_control": {
      "bearish_context": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 465832,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 551782,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 48138,
        "UNRESOLVED_AT_SOURCE_END": 63,
        "UNRESOLVED_BY_WINDOW": 23456
      },
      "bullish_context": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 507288,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 587738,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 50349,
        "UNRESOLVED_AT_SOURCE_END": 63,
        "UNRESOLVED_BY_WINDOW": 25699
      },
      "insufficient_history": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 361,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 404,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 47,
        "UNRESOLVED_BY_WINDOW": 92
      },
      "range_or_mixed": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 122112,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 140988,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 12431,
        "UNRESOLVED_AT_SOURCE_END": 14,
        "UNRESOLVED_BY_WINDOW": 6639
      }
    },
    "breaker_re_entry": {
      "bearish_context": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 4049,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 4227,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 174,
        "UNRESOLVED_AT_SOURCE_END": 4,
        "UNRESOLVED_BY_WINDOW": 100
      },
      "bullish_context": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 4235,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 4586,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 199,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 119
      },
      "insufficient_history": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 9,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 10
      },
      "range_or_mixed": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1192,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1267,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 64,
        "UNRESOLVED_BY_WINDOW": 33
      }
    },
    "fvg_fill": {
      "bearish_context": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 188577,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 369282,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 109272,
        "UNRESOLVED_AT_SOURCE_END": 23,
        "UNRESOLVED_BY_WINDOW": 4315
      },
      "bullish_context": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 201025,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 380472,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 116703,
        "UNRESOLVED_AT_SOURCE_END": 30,
        "UNRESOLVED_BY_WINDOW": 4992
      },
      "insufficient_history": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 219,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 419,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 119,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 44
      },
      "range_or_mixed": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 43570,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 85809,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 26684,
        "UNRESOLVED_AT_SOURCE_END": 5,
        "UNRESOLVED_BY_WINDOW": 1090
      }
    },
    "liquidity_stop_run_context": {
      "bearish_context": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 603405,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 739014,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 10485,
        "UNRESOLVED_AT_SOURCE_END": 53,
        "UNRESOLVED_BY_WINDOW": 7092
      },
      "bullish_context": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 640318,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 790352,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 11413,
        "UNRESOLVED_AT_SOURCE_END": 47,
        "UNRESOLVED_BY_WINDOW": 7066
      },
      "insufficient_history": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 165,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 194,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 4,
        "UNRESOLVED_BY_WINDOW": 7
      },
      "range_or_mixed": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 159320,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 191485,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 2909,
        "UNRESOLVED_AT_SOURCE_END": 22,
        "UNRESOLVED_BY_WINDOW": 2006
      }
    },
    "ob_retest": {
      "bearish_context": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 342501,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 299160,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 8241,
        "UNRESOLVED_AT_SOURCE_END": 34,
        "UNRESOLVED_BY_WINDOW": 10164
      },
      "bullish_context": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 378372,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 319355,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 9495,
        "UNRESOLVED_AT_SOURCE_END": 38,
        "UNRESOLVED_BY_WINDOW": 11750
      },
      "insufficient_history": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 407,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 288,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 7,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 73
      },
      "range_or_mixed": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 89914,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 77618,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 2922,
        "UNRESOLVED_AT_SOURCE_END": 9,
        "UNRESOLVED_BY_WINDOW": 2853
      }
    },
    "opening_drive_no_fill_lifecycle": {
      "bearish_context": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 25493,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 33064,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1305,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 1519
      },
      "bullish_context": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 29453,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 37405,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1607,
        "UNRESOLVED_AT_SOURCE_END": 9,
        "UNRESOLVED_BY_WINDOW": 1722
      },
      "insufficient_history": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 268,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 274,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 11,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 26
      },
      "range_or_mixed": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 6171,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 8806,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 266,
        "UNRESOLVED_BY_WINDOW": 378
      }
    },
    "session_kz_sweep": {
      "bearish_context": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 27308,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 30813,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 658,
        "UNRESOLVED_AT_SOURCE_END": 6,
        "UNRESOLVED_BY_WINDOW": 1321
      },
      "bullish_context": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 29724,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 33538,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 904,
        "UNRESOLVED_AT_SOURCE_END": 3,
        "UNRESOLVED_BY_WINDOW": 1431
      },
      "insufficient_history": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 128,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 150,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 4,
        "UNRESOLVED_BY_WINDOW": 39
      },
      "range_or_mixed": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 7098,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 7855,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 149,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 377
      }
    }
  },
  "label_by_family_session_or_kill_zone_status": {
    "adjacent_range_compression_breakout": {
      "London": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 49694,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 13735,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 37,
        "UNRESOLVED_BY_WINDOW": 2840
      },
      "NY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 49166,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 13934,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 131,
        "UNRESOLVED_AT_SOURCE_END": 10,
        "UNRESOLVED_BY_WINDOW": 2505
      },
      "Tokyo": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 17114,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 4685,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 63,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 1331
      },
      "outside_configured_kill_zone": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 280838,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 79382,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 279,
        "UNRESOLVED_AT_SOURCE_END": 59,
        "UNRESOLVED_BY_WINDOW": 26457
      }
    },
    "baseline_mean_reversion": {
      "London": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 28958,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 108180,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 14833,
        "UNRESOLVED_BY_WINDOW": 24
      },
      "NY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 32052,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 117635,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 18354,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 73
      },
      "Tokyo": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 9175,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 32591,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 5473,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "outside_configured_kill_zone": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 132903,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 515300,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 65168,
        "UNRESOLVED_AT_SOURCE_END": 28,
        "UNRESOLVED_BY_WINDOW": 289
      }
    },
    "baseline_momentum_continuation": {
      "London": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 84810,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 166275,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 4184,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 81
      },
      "NY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 91027,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 177782,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 5423,
        "UNRESOLVED_BY_WINDOW": 203
      },
      "Tokyo": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 25883,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 54236,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1833,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 35
      },
      "outside_configured_kill_zone": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 414038,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 919277,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 18535,
        "UNRESOLVED_AT_SOURCE_END": 60,
        "UNRESOLVED_BY_WINDOW": 1621
      }
    },
    "baseline_random_session_control": {
      "London": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 22460,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 40809,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1288,
        "UNRESOLVED_BY_WINDOW": 15
      },
      "NY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 25257,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 43400,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 2140,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 194
      },
      "Tokyo": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 7774,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 16083,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 394,
        "UNRESOLVED_BY_WINDOW": 67
      }
    },
    "baseline_shifted_entry_control": {
      "London": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 157186,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 177709,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 17121,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 4485
      },
      "NY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 173670,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 197681,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 20166,
        "UNRESOLVED_AT_SOURCE_END": 16,
        "UNRESOLVED_BY_WINDOW": 6565
      },
      "Tokyo": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 49361,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 54053,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 6086,
        "UNRESOLVED_AT_SOURCE_END": 3,
        "UNRESOLVED_BY_WINDOW": 2936
      },
      "outside_configured_kill_zone": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 715376,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 851469,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 67592,
        "UNRESOLVED_AT_SOURCE_END": 120,
        "UNRESOLVED_BY_WINDOW": 41900
      }
    },
    "breaker_re_entry": {
      "London": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1206,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1158,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 37,
        "UNRESOLVED_BY_WINDOW": 18
      },
      "NY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1522,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1697,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 108,
        "UNRESOLVED_BY_WINDOW": 28
      },
      "Tokyo": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 803,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 857,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 61,
        "UNRESOLVED_BY_WINDOW": 14
      },
      "outside_configured_kill_zone": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 5954,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 6378,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 231,
        "UNRESOLVED_AT_SOURCE_END": 5,
        "UNRESOLVED_BY_WINDOW": 192
      }
    },
    "fvg_fill": {
      "London": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 59252,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 117076,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 37749,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 646
      },
      "NY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 65498,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 128768,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 42080,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 1253
      },
      "Tokyo": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 18218,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 34603,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 13291,
        "UNRESOLVED_BY_WINDOW": 471
      },
      "outside_configured_kill_zone": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 290423,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 555535,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 159658,
        "UNRESOLVED_AT_SOURCE_END": 58,
        "UNRESOLVED_BY_WINDOW": 8071
      }
    },
    "liquidity_stop_run_context": {
      "London": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 197367,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 231315,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3432,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 905
      },
      "NY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 222774,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 254988,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 5242,
        "UNRESOLVED_AT_SOURCE_END": 6,
        "UNRESOLVED_BY_WINDOW": 2335
      },
      "Tokyo": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 62528,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 70621,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1673,
        "UNRESOLVED_AT_SOURCE_END": 5,
        "UNRESOLVED_BY_WINDOW": 706
      },
      "outside_configured_kill_zone": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 920539,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1164121,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 14464,
        "UNRESOLVED_AT_SOURCE_END": 110,
        "UNRESOLVED_BY_WINDOW": 12225
      }
    },
    "ob_retest": {
      "London": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 113469,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 97980,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 2498,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 1587
      },
      "NY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 129757,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 112216,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 5039,
        "UNRESOLVED_AT_SOURCE_END": 5,
        "UNRESOLVED_BY_WINDOW": 2932
      },
      "Tokyo": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 33955,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 28910,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1346,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 1050
      },
      "outside_configured_kill_zone": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 534013,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 457315,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 11782,
        "UNRESOLVED_AT_SOURCE_END": 75,
        "UNRESOLVED_BY_WINDOW": 19271
      }
    },
    "opening_drive_no_fill_lifecycle": {
      "London": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 25725,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 32868,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 900,
        "UNRESOLVED_BY_WINDOW": 677
      },
      "NY": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 26670,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 35438,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1976,
        "UNRESOLVED_AT_SOURCE_END": 11,
        "UNRESOLVED_BY_WINDOW": 2156
      },
      "Tokyo": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 8990,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 11243,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 313,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 812
      }
    },
    "session_kz_sweep": {
      "London": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 24442,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 27559,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 505,
        "UNRESOLVED_AT_SOURCE_END": 3,
        "UNRESOLVED_BY_WINDOW": 756
      },
      "NY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 32347,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 36020,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1069,
        "UNRESOLVED_AT_SOURCE_END": 6,
        "UNRESOLVED_BY_WINDOW": 1931
      },
      "Tokyo": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 7469,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 8777,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 141,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 481
      }
    }
  },
  "label_by_family_side_status": {
    "adjacent_range_compression_breakout": {
      "LONG": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 203624,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 55742,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 239,
        "UNRESOLVED_AT_SOURCE_END": 40,
        "UNRESOLVED_BY_WINDOW": 17933
      },
      "SHORT": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 193188,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 55994,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 271,
        "UNRESOLVED_AT_SOURCE_END": 31,
        "UNRESOLVED_BY_WINDOW": 15200
      }
    },
    "baseline_mean_reversion": {
      "LONG": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 9532,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 430119,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 95029,
        "UNRESOLVED_AT_SOURCE_END": 11
      },
      "SHORT": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 193556,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 343587,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 8799,
        "UNRESOLVED_AT_SOURCE_END": 21,
        "UNRESOLVED_BY_WINDOW": 389
      }
    },
    "baseline_momentum_continuation": {
      "LONG": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 318704,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 680021,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 14123,
        "UNRESOLVED_AT_SOURCE_END": 34,
        "UNRESOLVED_BY_WINDOW": 1378
      },
      "SHORT": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 297054,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 637549,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 15852,
        "UNRESOLVED_AT_SOURCE_END": 30,
        "UNRESOLVED_BY_WINDOW": 562
      }
    },
    "baseline_random_session_control": {
      "LONG": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 28323,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 49585,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1764,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 162
      },
      "SHORT": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 27168,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 50707,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 2058,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 114
      }
    },
    "baseline_shifted_entry_control": {
      "LONG": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 560077,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 624828,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 56795,
        "UNRESOLVED_AT_SOURCE_END": 67,
        "UNRESOLVED_BY_WINDOW": 30124
      },
      "SHORT": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 535516,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 656084,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 54170,
        "UNRESOLVED_AT_SOURCE_END": 73,
        "UNRESOLVED_BY_WINDOW": 25762
      }
    },
    "breaker_re_entry": {
      "LONG": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 4538,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 4671,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 192,
        "UNRESOLVED_BY_WINDOW": 111
      },
      "SHORT": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 4947,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 5419,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 245,
        "UNRESOLVED_AT_SOURCE_END": 5,
        "UNRESOLVED_BY_WINDOW": 141
      }
    },
    "fvg_fill": {
      "LONG": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 222911,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 413915,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 129133,
        "UNRESOLVED_AT_SOURCE_END": 39,
        "UNRESOLVED_BY_WINDOW": 5440
      },
      "SHORT": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 210480,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 422067,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 123645,
        "UNRESOLVED_AT_SOURCE_END": 21,
        "UNRESOLVED_BY_WINDOW": 5001
      }
    },
    "liquidity_stop_run_context": {
      "LONG": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 707815,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 838703,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 12610,
        "UNRESOLVED_AT_SOURCE_END": 52,
        "UNRESOLVED_BY_WINDOW": 8925
      },
      "SHORT": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 695393,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 882342,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 12201,
        "UNRESOLVED_AT_SOURCE_END": 70,
        "UNRESOLVED_BY_WINDOW": 7246
      }
    },
    "ob_retest": {
      "LONG": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 420516,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 347386,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 11682,
        "UNRESOLVED_AT_SOURCE_END": 45,
        "UNRESOLVED_BY_WINDOW": 13261
      },
      "SHORT": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 390678,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 349035,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 8983,
        "UNRESOLVED_AT_SOURCE_END": 37,
        "UNRESOLVED_BY_WINDOW": 11579
      }
    },
    "opening_drive_no_fill_lifecycle": {
      "LONG": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 31725,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 42181,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1652,
        "UNRESOLVED_AT_SOURCE_END": 8,
        "UNRESOLVED_BY_WINDOW": 2072
      },
      "SHORT": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 29660,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 37368,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1537,
        "UNRESOLVED_AT_SOURCE_END": 4,
        "UNRESOLVED_BY_WINDOW": 1573
      }
    },
    "session_kz_sweep": {
      "LONG": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 29452,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 32325,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 684,
        "UNRESOLVED_AT_SOURCE_END": 4,
        "UNRESOLVED_BY_WINDOW": 1672
      },
      "SHORT": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 34806,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 40031,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1031,
        "UNRESOLVED_AT_SOURCE_END": 6,
        "UNRESOLVED_BY_WINDOW": 1496
      }
    }
  },
  "label_by_family_source_family_status": {
    "adjacent_range_compression_breakout": {
      "LOCAL_OHLCV_CSV": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 383035,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 107712,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 499,
        "UNRESOLVED_AT_SOURCE_END": 55,
        "UNRESOLVED_BY_WINDOW": 32344
      },
      "SIERRA_DERIVED_OHLCV_EXPORT": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 13777,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 4024,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 11,
        "UNRESOLVED_AT_SOURCE_END": 16,
        "UNRESOLVED_BY_WINDOW": 789
      }
    },
    "baseline_mean_reversion": {
      "LOCAL_OHLCV_CSV": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 195666,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 746059,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 100203,
        "UNRESOLVED_AT_SOURCE_END": 26,
        "UNRESOLVED_BY_WINDOW": 385
      },
      "SIERRA_DERIVED_OHLCV_EXPORT": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 7422,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 27647,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3625,
        "UNRESOLVED_AT_SOURCE_END": 6,
        "UNRESOLVED_BY_WINDOW": 4
      }
    },
    "baseline_momentum_continuation": {
      "LOCAL_OHLCV_CSV": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 593554,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1272315,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 29075,
        "UNRESOLVED_AT_SOURCE_END": 44,
        "UNRESOLVED_BY_WINDOW": 1920
      },
      "SIERRA_DERIVED_OHLCV_EXPORT": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 22204,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 45255,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 900,
        "UNRESOLVED_AT_SOURCE_END": 20,
        "UNRESOLVED_BY_WINDOW": 20
      }
    },
    "baseline_random_session_control": {
      "LOCAL_OHLCV_CSV": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 53924,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 97287,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3756,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 264
      },
      "SIERRA_DERIVED_OHLCV_EXPORT": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1567,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 3005,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 66,
        "UNRESOLVED_BY_WINDOW": 12
      }
    },
    "baseline_shifted_entry_control": {
      "LOCAL_OHLCV_CSV": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1058823,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1238396,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 107581,
        "UNRESOLVED_AT_SOURCE_END": 111,
        "UNRESOLVED_BY_WINDOW": 54684
      },
      "SIERRA_DERIVED_OHLCV_EXPORT": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 36770,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 42516,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3384,
        "UNRESOLVED_AT_SOURCE_END": 29,
        "UNRESOLVED_BY_WINDOW": 1202
      }
    },
    "breaker_re_entry": {
      "LOCAL_OHLCV_CSV": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 8275,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 8320,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 375,
        "UNRESOLVED_AT_SOURCE_END": 5,
        "UNRESOLVED_BY_WINDOW": 242
      },
      "SIERRA_DERIVED_OHLCV_EXPORT": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1210,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1770,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 62,
        "UNRESOLVED_BY_WINDOW": 10
      }
    },
    "fvg_fill": {
      "LOCAL_OHLCV_CSV": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 412428,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 804432,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 245942,
        "UNRESOLVED_AT_SOURCE_END": 37,
        "UNRESOLVED_BY_WINDOW": 10237
      },
      "SIERRA_DERIVED_OHLCV_EXPORT": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 20963,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 31550,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 6836,
        "UNRESOLVED_AT_SOURCE_END": 23,
        "UNRESOLVED_BY_WINDOW": 204
      }
    },
    "liquidity_stop_run_context": {
      "LOCAL_OHLCV_CSV": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1362635,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1668895,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 24174,
        "UNRESOLVED_AT_SOURCE_END": 99,
        "UNRESOLVED_BY_WINDOW": 15953
      },
      "SIERRA_DERIVED_OHLCV_EXPORT": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 40573,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 52150,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 637,
        "UNRESOLVED_AT_SOURCE_END": 23,
        "UNRESOLVED_BY_WINDOW": 218
      }
    },
    "ob_retest": {
      "LOCAL_OHLCV_CSV": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 785539,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 674699,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 20016,
        "UNRESOLVED_AT_SOURCE_END": 64,
        "UNRESOLVED_BY_WINDOW": 24438
      },
      "SIERRA_DERIVED_OHLCV_EXPORT": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 25655,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 21722,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 649,
        "UNRESOLVED_AT_SOURCE_END": 18,
        "UNRESOLVED_BY_WINDOW": 402
      }
    },
    "opening_drive_no_fill_lifecycle": {
      "LOCAL_OHLCV_CSV": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 59641,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 76879,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3141,
        "UNRESOLVED_AT_SOURCE_END": 8,
        "UNRESOLVED_BY_WINDOW": 3499
      },
      "SIERRA_DERIVED_OHLCV_EXPORT": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 1744,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 2670,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 48,
        "UNRESOLVED_AT_SOURCE_END": 4,
        "UNRESOLVED_BY_WINDOW": 146
      }
    },
    "session_kz_sweep": {
      "LOCAL_OHLCV_CSV": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 62169,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 69769,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1680,
        "UNRESOLVED_AT_SOURCE_END": 10,
        "UNRESOLVED_BY_WINDOW": 3120
      },
      "SIERRA_DERIVED_OHLCV_EXPORT": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 2089,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 2587,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 35,
        "UNRESOLVED_BY_WINDOW": 48
      }
    }
  },
  "label_by_family_status": {
    "adjacent_range_compression_breakout": {
      "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 396812,
      "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 111736,
      "SAME_BAR_CONTEXT_AMBIGUOUS": 510,
      "UNRESOLVED_AT_SOURCE_END": 71,
      "UNRESOLVED_BY_WINDOW": 33133
    },
    "baseline_mean_reversion": {
      "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 203088,
      "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 773706,
      "SAME_BAR_CONTEXT_AMBIGUOUS": 103828,
      "UNRESOLVED_AT_SOURCE_END": 32,
      "UNRESOLVED_BY_WINDOW": 389
    },
    "baseline_momentum_continuation": {
      "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 615758,
      "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1317570,
      "SAME_BAR_CONTEXT_AMBIGUOUS": 29975,
      "UNRESOLVED_AT_SOURCE_END": 64,
      "UNRESOLVED_BY_WINDOW": 1940
    },
    "baseline_random_session_control": {
      "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 55491,
      "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 100292,
      "SAME_BAR_CONTEXT_AMBIGUOUS": 3822,
      "UNRESOLVED_AT_SOURCE_END": 2,
      "UNRESOLVED_BY_WINDOW": 276
    },
    "baseline_shifted_entry_control": {
      "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1095593,
      "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1280912,
      "SAME_BAR_CONTEXT_AMBIGUOUS": 110965,
      "UNRESOLVED_AT_SOURCE_END": 140,
      "UNRESOLVED_BY_WINDOW": 55886
    },
    "breaker_re_entry": {
      "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 9485,
      "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 10090,
      "SAME_BAR_CONTEXT_AMBIGUOUS": 437,
      "UNRESOLVED_AT_SOURCE_END": 5,
      "UNRESOLVED_BY_WINDOW": 252
    },
    "fvg_fill": {
      "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 433391,
      "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 835982,
      "SAME_BAR_CONTEXT_AMBIGUOUS": 252778,
      "UNRESOLVED_AT_SOURCE_END": 60,
      "UNRESOLVED_BY_WINDOW": 10441
    },
    "liquidity_stop_run_context": {
      "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1403208,
      "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1721045,
      "SAME_BAR_CONTEXT_AMBIGUOUS": 24811,
      "UNRESOLVED_AT_SOURCE_END": 122,
      "UNRESOLVED_BY_WINDOW": 16171
    },
    "ob_retest": {
      "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 811194,
      "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 696421,
      "SAME_BAR_CONTEXT_AMBIGUOUS": 20665,
      "UNRESOLVED_AT_SOURCE_END": 82,
      "UNRESOLVED_BY_WINDOW": 24840
    },
    "opening_drive_no_fill_lifecycle": {
      "MIDPOINT_RETRACE_BEFORE_EXTENSION": 61385,
      "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 79549,
      "SAME_BAR_CONTEXT_AMBIGUOUS": 3189,
      "UNRESOLVED_AT_SOURCE_END": 12,
      "UNRESOLVED_BY_WINDOW": 3645
    },
    "session_kz_sweep": {
      "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 64258,
      "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 72356,
      "SAME_BAR_CONTEXT_AMBIGUOUS": 1715,
      "UNRESOLVED_AT_SOURCE_END": 10,
      "UNRESOLVED_BY_WINDOW": 3168
    }
  },
  "label_by_family_symbol_status": {
    "adjacent_range_compression_breakout": {
      "AUDJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 196,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 43,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1,
        "UNRESOLVED_BY_WINDOW": 64
      },
      "AUDUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 198,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 38,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 55
      },
      "BTCUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 271,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 59,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 2,
        "UNRESOLVED_BY_WINDOW": 100
      },
      "CHFJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 194,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 35,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1,
        "UNRESOLVED_BY_WINDOW": 65
      },
      "ETHUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 257,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 48,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 2,
        "UNRESOLVED_BY_WINDOW": 105
      },
      "EURGBP": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 150,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 22,
        "UNRESOLVED_BY_WINDOW": 66
      },
      "EURJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 172,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 36,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1,
        "UNRESOLVED_BY_WINDOW": 61
      },
      "EURUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 3679,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 883,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 6,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 877
      },
      "GBPJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 53248,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 15553,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 92,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 4086
      },
      "GBPUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 58646,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 16763,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 79,
        "UNRESOLVED_AT_SOURCE_END": 4,
        "UNRESOLVED_BY_WINDOW": 4596
      },
      "GBPUSD_6B": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 51,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 14,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "GER40": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 345,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 73,
        "UNRESOLVED_BY_WINDOW": 127
      },
      "JP225": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 213,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 46,
        "UNRESOLVED_BY_WINDOW": 80
      },
      "NAS100": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 45456,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 12767,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 58,
        "UNRESOLVED_AT_SOURCE_END": 15,
        "UNRESOLVED_BY_WINDOW": 3229
      },
      "NAS100_MNQ": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 81,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 30,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 5
      },
      "NAS100_NQ": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 92,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 30,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 5
      },
      "NZDUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 2610,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 550,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 5,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 943
      },
      "SI": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 108,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 33,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 16
      },
      "SPX500": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 179,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 31,
        "UNRESOLVED_BY_WINDOW": 58
      },
      "SPX_ES": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 71,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 28,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 2
      },
      "SPX_MES": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 74,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 27,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "UK100": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 348,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 73,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 2,
        "UNRESOLVED_BY_WINDOW": 117
      },
      "UKOIL_cash": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 180,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 37,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 65
      },
      "US30_MYM": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 108,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 23,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 5
      },
      "US30_YM": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 126,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 29,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 4
      },
      "US30_cash": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 45883,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 12497,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 65,
        "UNRESOLVED_AT_SOURCE_END": 3,
        "UNRESOLVED_BY_WINDOW": 4242
      },
      "USDCAD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 163,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 34,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 43
      },
      "USDCHF": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 200,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 46,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 66
      },
      "USDJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 61863,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 17080,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 103,
        "UNRESOLVED_AT_SOURCE_END": 7,
        "UNRESOLVED_BY_WINDOW": 4697
      },
      "USDJPY_6J": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 53,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 13,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "USOIL_cash": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 134,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 32,
        "UNRESOLVED_BY_WINDOW": 65
      },
      "VIX": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 12,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 3,
        "UNRESOLVED_BY_WINDOW": 4
      },
      "XAGUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 51761,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 15024,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 48,
        "UNRESOLVED_AT_SOURCE_END": 7,
        "UNRESOLVED_BY_WINDOW": 4411
      },
      "XAGUSD_SI": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 46,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 11,
        "UNRESOLVED_BY_WINDOW": 2
      },
      "XAUUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 64641,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 18267,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 41,
        "UNRESOLVED_AT_SOURCE_END": 13,
        "UNRESOLVED_BY_WINDOW": 4630
      },
      "XAUUSD_GC": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 73,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 31,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "XAUUSD_MGC": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 72,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 35,
        "UNRESOLVED_BY_WINDOW": 4
      },
      "XAUUSD_SCID": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 4858,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1392,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 2,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 228
      }
    },
    "baseline_mean_reversion": {
      "AUDJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 98,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 409,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 64,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 2
      },
      "AUDUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 123,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 415,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 53,
        "UNRESOLVED_AT_SOURCE_END": 1
      },
      "BTCUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 148,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 531,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 79
      },
      "CHFJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 98,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 428,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 68
      },
      "ETHUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 166,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 526,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 76,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "EURGBP": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 115,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 398,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 81,
        "UNRESOLVED_BY_WINDOW": 4
      },
      "EURJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 106,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 397,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 59,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "EURUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 2132,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 7802,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1005,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 13
      },
      "GBPJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 29783,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 112122,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 14198,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 24
      },
      "GBPUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 31035,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 115110,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 15396,
        "UNRESOLVED_AT_SOURCE_END": 3,
        "UNRESOLVED_BY_WINDOW": 68
      },
      "GBPUSD_6B": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 44,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 202,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 20
      },
      "GER40": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 195,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 673,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 98,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "JP225": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 98,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 363,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 60,
        "UNRESOLVED_AT_SOURCE_END": 1
      },
      "NAS100": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 20646,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 85619,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 11189,
        "UNRESOLVED_AT_SOURCE_END": 6,
        "UNRESOLVED_BY_WINDOW": 59
      },
      "NAS100_MNQ": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 51,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 229,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 23
      },
      "NAS100_NQ": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 53,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 228,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 27
      },
      "NZDUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1543,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 5910,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 766,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 18
      },
      "SI": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 136,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 391,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 49,
        "UNRESOLVED_AT_SOURCE_END": 1
      },
      "SPX500": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 79,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 314,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 55,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "SPX_ES": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 55,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 223,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 19
      },
      "SPX_MES": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 54,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 221,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 26
      },
      "UK100": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 176,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 699,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 93,
        "UNRESOLVED_BY_WINDOW": 4
      },
      "UKOIL_cash": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 98,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 362,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 38,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "US30_MYM": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 64,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 200,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 37
      },
      "US30_YM": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 65,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 205,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 30
      },
      "US30_cash": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 22186,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 85671,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 11620,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 76
      },
      "USDCAD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 103,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 348,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 41,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "USDCHF": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 118,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 407,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 58,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "USDJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 30236,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 115191,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 15190,
        "UNRESOLVED_AT_SOURCE_END": 4,
        "UNRESOLVED_BY_WINDOW": 31
      },
      "USDJPY_6J": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 67,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 207,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 15
      },
      "USOIL_cash": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 94,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 316,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 37,
        "UNRESOLVED_BY_WINDOW": 2
      },
      "VIX": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 40,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 124,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 13
      },
      "XAGUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 29690,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 104575,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 15024,
        "UNRESOLVED_AT_SOURCE_END": 4,
        "UNRESOLVED_BY_WINDOW": 37
      },
      "XAGUSD_SI": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 14,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 71,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3,
        "UNRESOLVED_AT_SOURCE_END": 1
      },
      "XAUUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 31015,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 122841,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 16846,
        "UNRESOLVED_AT_SOURCE_END": 3,
        "UNRESOLVED_BY_WINDOW": 37
      },
      "XAUUSD_GC": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 49,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 204,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 29,
        "UNRESOLVED_AT_SOURCE_END": 1
      },
      "XAUUSD_MGC": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 50,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 209,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 30,
        "UNRESOLVED_AT_SOURCE_END": 1
      },
      "XAUUSD_SCID": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 2265,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 9565,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1313,
        "UNRESOLVED_BY_WINDOW": 1
      }
    },
    "baseline_momentum_continuation": {
      "AUDJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 327,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 693,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 16,
        "UNRESOLVED_BY_WINDOW": 4
      },
      "AUDUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 320,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 687,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 18,
        "UNRESOLVED_BY_WINDOW": 6
      },
      "BTCUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 387,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 986,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 34,
        "UNRESOLVED_BY_WINDOW": 4
      },
      "CHFJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 307,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 692,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 27,
        "UNRESOLVED_BY_WINDOW": 6
      },
      "ETHUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 381,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 945,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 25,
        "UNRESOLVED_BY_WINDOW": 5
      },
      "EURGBP": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 252,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 637,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 23,
        "UNRESOLVED_BY_WINDOW": 5
      },
      "EURJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 278,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 692,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 10,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "EURUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 5820,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 13026,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 288,
        "UNRESOLVED_AT_SOURCE_END": 3,
        "UNRESOLVED_BY_WINDOW": 55
      },
      "GBPJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 83722,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 188148,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3950,
        "UNRESOLVED_AT_SOURCE_END": 4,
        "UNRESOLVED_BY_WINDOW": 129
      },
      "GBPUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 94184,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 197619,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 4251,
        "UNRESOLVED_AT_SOURCE_END": 9,
        "UNRESOLVED_BY_WINDOW": 268
      },
      "GBPUSD_6B": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 157,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 248,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 4
      },
      "GER40": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 563,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1183,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 32,
        "UNRESOLVED_BY_WINDOW": 7
      },
      "JP225": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 344,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 708,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 20,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "NAS100": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 67147,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 142967,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3231,
        "UNRESOLVED_AT_SOURCE_END": 5,
        "UNRESOLVED_BY_WINDOW": 384
      },
      "NAS100_MNQ": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 167,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 328,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 10,
        "UNRESOLVED_AT_SOURCE_END": 1
      },
      "NAS100_NQ": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 165,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 343,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 8,
        "UNRESOLVED_AT_SOURCE_END": 1
      },
      "NZDUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 4307,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 9938,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 226,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 56
      },
      "SI": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 221,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 505,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 6,
        "UNRESOLVED_AT_SOURCE_END": 2
      },
      "SPX500": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 252,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 568,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 18,
        "UNRESOLVED_BY_WINDOW": 2
      },
      "SPX_ES": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 149,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 308,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 13,
        "UNRESOLVED_AT_SOURCE_END": 2
      },
      "SPX_MES": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 147,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 324,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 10,
        "UNRESOLVED_AT_SOURCE_END": 1
      },
      "UK100": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 553,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1218,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 27,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 11
      },
      "UKOIL_cash": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 301,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 598,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 21,
        "UNRESOLVED_BY_WINDOW": 6
      },
      "US30_MYM": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 174,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 330,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 14
      },
      "US30_YM": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 207,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 339,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 13
      },
      "US30_cash": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 69542,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 144753,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3371,
        "UNRESOLVED_AT_SOURCE_END": 5,
        "UNRESOLVED_BY_WINDOW": 428
      },
      "USDCAD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 236,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 610,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 12,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "USDCHF": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 312,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 756,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 19,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "USDJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 95390,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 199509,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 4523,
        "UNRESOLVED_AT_SOURCE_END": 10,
        "UNRESOLVED_BY_WINDOW": 230
      },
      "USDJPY_6J": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 157,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 241,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 4,
        "UNRESOLVED_AT_SOURCE_END": 2
      },
      "USOIL_cash": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 236,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 558,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 20,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "VIX": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 37,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 104,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1,
        "UNRESOLVED_AT_SOURCE_END": 1
      },
      "XAGUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 83410,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 180618,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 4357,
        "UNRESOLVED_AT_SOURCE_END": 5,
        "UNRESOLVED_BY_WINDOW": 172
      },
      "XAGUSD_SI": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 76,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 118
      },
      "XAUUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 98029,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 209558,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 4968,
        "UNRESOLVED_AT_SOURCE_END": 9,
        "UNRESOLVED_BY_WINDOW": 150
      },
      "XAUUSD_GC": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 137,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 341,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 13
      },
      "XAUUSD_MGC": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 145,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 317,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 15
      },
      "XAUUSD_SCID": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 7219,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 16057,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 377,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 3
      }
    },
    "baseline_random_session_control": {
      "AUDJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 150,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 326,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 10
      },
      "AUDUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 172,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 303,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 7
      },
      "BTCUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 181,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 450,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 15,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "CHFJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 152,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 324,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 10
      },
      "ETHUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 197,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 444,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 10,
        "UNRESOLVED_BY_WINDOW": 4
      },
      "EURGBP": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 146,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 316,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 19,
        "UNRESOLVED_BY_WINDOW": 5
      },
      "EURJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 164,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 308,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 7,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "EURUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1308,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 2144,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 114,
        "UNRESOLVED_BY_WINDOW": 2
      },
      "GBPJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 9041,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 17642,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 468,
        "UNRESOLVED_BY_WINDOW": 57
      },
      "GBPUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 7527,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 12664,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 498,
        "UNRESOLVED_BY_WINDOW": 28
      },
      "GBPUSD_6B": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 9,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 27
      },
      "GER40": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 283,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 451,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 14
      },
      "JP225": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 137,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 295,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 12,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "NAS100": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 2701,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 4046,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 402,
        "UNRESOLVED_BY_WINDOW": 13
      },
      "NAS100_MNQ": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 7,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 28,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1
      },
      "NAS100_NQ": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 11,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 25
      },
      "NZDUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1961,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 4049,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 84,
        "UNRESOLVED_BY_WINDOW": 16
      },
      "SI": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 22,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 47,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 2
      },
      "SPX500": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 111,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 232,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 8,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "SPX_ES": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 8,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 27,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1
      },
      "SPX_MES": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 14,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 21,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1
      },
      "UK100": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 266,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 463,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 23,
        "UNRESOLVED_BY_WINDOW": 6
      },
      "UKOIL_cash": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 116,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 202,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 2
      },
      "US30_MYM": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 15,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 18,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 2,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "US30_YM": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 13,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 22,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1
      },
      "US30_cash": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 5551,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 9786,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 509,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "USDCAD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 138,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 250,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 13,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "USDCHF": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 139,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 332,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 12,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "USDJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 10789,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 19697,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 616,
        "UNRESOLVED_BY_WINDOW": 96
      },
      "USDJPY_6J": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 17,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 19
      },
      "USOIL_cash": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 114,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 219,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 8
      },
      "VIX": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 12,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 29,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "XAGUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 6345,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 11552,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 418,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 17
      },
      "XAGUSD_SI": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 11,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 32
      },
      "XAUUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 7143,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 12419,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 519,
        "UNRESOLVED_BY_WINDOW": 7
      },
      "XAUUSD_GC": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 13,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 22,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "XAUUSD_MGC": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 14,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 22
      },
      "XAUUSD_SCID": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 493,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1039,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 15,
        "UNRESOLVED_BY_WINDOW": 7
      }
    },
    "baseline_shifted_entry_control": {
      "AUDJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 540,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 667,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 75,
        "UNRESOLVED_BY_WINDOW": 120
      },
      "AUDUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 634,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 690,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 69,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 129
      },
      "BTCUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 682,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 804,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 75,
        "UNRESOLVED_AT_SOURCE_END": 3,
        "UNRESOLVED_BY_WINDOW": 167
      },
      "CHFJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 557,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 694,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 60,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 134
      },
      "ETHUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 712,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 856,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 73,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 208
      },
      "EURGBP": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 596,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 625,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 73,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 172
      },
      "EURJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 552,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 681,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 52,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 126
      },
      "EURUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 10964,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 12315,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1175,
        "UNRESOLVED_AT_SOURCE_END": 4,
        "UNRESOLVED_BY_WINDOW": 1483
      },
      "GBPJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 159523,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 185838,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 14813,
        "UNRESOLVED_AT_SOURCE_END": 9,
        "UNRESOLVED_BY_WINDOW": 7594
      },
      "GBPUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 161346,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 187577,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 17201,
        "UNRESOLVED_AT_SOURCE_END": 15,
        "UNRESOLVED_BY_WINDOW": 8178
      },
      "GBPUSD_6B": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 189,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 183,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 14,
        "UNRESOLVED_AT_SOURCE_END": 3,
        "UNRESOLVED_BY_WINDOW": 7
      },
      "GER40": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1015,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1140,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 141,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 238
      },
      "JP225": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 550,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 598,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 62,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 119
      },
      "NAS100": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 118348,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 139927,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 11095,
        "UNRESOLVED_AT_SOURCE_END": 8,
        "UNRESOLVED_BY_WINDOW": 4737
      },
      "NAS100_MNQ": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 257,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 305,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 27,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "NAS100_NQ": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 272,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 300,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 25,
        "UNRESOLVED_BY_WINDOW": 13
      },
      "NZDUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 8635,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 10317,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 911,
        "UNRESOLVED_AT_SOURCE_END": 5,
        "UNRESOLVED_BY_WINDOW": 1997
      },
      "SI": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 290,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 335,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 23,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 20
      },
      "SPX500": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 436,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 471,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 60,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 106
      },
      "SPX_ES": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 198,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 211,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 26,
        "UNRESOLVED_AT_SOURCE_END": 6,
        "UNRESOLVED_BY_WINDOW": 6
      },
      "SPX_MES": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 220,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 246,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 13,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "UK100": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 947,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1087,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 158,
        "UNRESOLVED_AT_SOURCE_END": 3,
        "UNRESOLVED_BY_WINDOW": 214
      },
      "UKOIL_cash": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 488,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 460,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 53,
        "UNRESOLVED_AT_SOURCE_END": 3,
        "UNRESOLVED_BY_WINDOW": 109
      },
      "US30_MYM": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 206,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 271,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 18,
        "UNRESOLVED_AT_SOURCE_END": 5,
        "UNRESOLVED_BY_WINDOW": 9
      },
      "US30_YM": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 264,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 276,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 30,
        "UNRESOLVED_BY_WINDOW": 6
      },
      "US30_cash": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 119243,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 138859,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 11936,
        "UNRESOLVED_AT_SOURCE_END": 8,
        "UNRESOLVED_BY_WINDOW": 6975
      },
      "USDCAD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 525,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 598,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 48,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 114
      },
      "USDCHF": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 578,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 680,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 58,
        "UNRESOLVED_AT_SOURCE_END": 4,
        "UNRESOLVED_BY_WINDOW": 110
      },
      "USDJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 166069,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 192801,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 17680,
        "UNRESOLVED_AT_SOURCE_END": 9,
        "UNRESOLVED_BY_WINDOW": 8227
      },
      "USDJPY_6J": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 143,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 150,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 10,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "USOIL_cash": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 380,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 396,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 50,
        "UNRESOLVED_BY_WINDOW": 84
      },
      "VIX": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 38,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 30,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 7,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 6
      },
      "XAGUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 147042,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 172091,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 15979,
        "UNRESOLVED_AT_SOURCE_END": 18,
        "UNRESOLVED_BY_WINDOW": 6876
      },
      "XAGUSD_SI": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 103,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 103,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 7,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "XAUUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 178478,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 210886,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 17627,
        "UNRESOLVED_AT_SOURCE_END": 17,
        "UNRESOLVED_BY_WINDOW": 7205
      },
      "XAUUSD_GC": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 273,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 306,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 24,
        "UNRESOLVED_BY_WINDOW": 9
      },
      "XAUUSD_MGC": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 255,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 337,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 10,
        "UNRESOLVED_BY_WINDOW": 4
      },
      "XAUUSD_SCID": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 14045,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 16801,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1207,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 374
      }
    },
    "breaker_re_entry": {
      "AUDJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 6,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 11,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "AUDUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 8,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 11
      },
      "BTCUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 6,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 11,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "CHFJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 7,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 4
      },
      "ETHUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 8,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 9,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "EURGBP": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 3,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "EURJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 2,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 2
      },
      "EURUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 88,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 82,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 7,
        "UNRESOLVED_BY_WINDOW": 11
      },
      "GBPJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1200,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1258,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 66,
        "UNRESOLVED_BY_WINDOW": 35
      },
      "GBPUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1380,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1516,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 80,
        "UNRESOLVED_AT_SOURCE_END": 4,
        "UNRESOLVED_BY_WINDOW": 38
      },
      "GBPUSD_6B": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1
      },
      "GER40": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 8,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 8,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1,
        "UNRESOLVED_BY_WINDOW": 2
      },
      "JP225": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 10,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 12,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "NAS100": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1160,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1261,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 74,
        "UNRESOLVED_BY_WINDOW": 26
      },
      "NAS100_MNQ": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 2
      },
      "NAS100_NQ": {
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 2
      },
      "NZDUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 72,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 68,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3,
        "UNRESOLVED_BY_WINDOW": 5
      },
      "SI": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1
      },
      "SPX500": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 3,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 3
      },
      "SPX_ES": {
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1
      },
      "SPX_MES": {
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1
      },
      "UK100": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 4,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 8,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "UKOIL_cash": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 12,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 8,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "US30_MYM": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 3,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "US30_YM": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 3,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 5,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "US30_cash": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1211,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1297,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 62,
        "UNRESOLVED_BY_WINDOW": 44
      },
      "USDCAD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 7,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 6,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "USDCHF": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 8,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 7,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1,
        "UNRESOLVED_BY_WINDOW": 2
      },
      "USDJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1451,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1502,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 65,
        "UNRESOLVED_BY_WINDOW": 33
      },
      "USOIL_cash": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 3,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1
      },
      "VIX": {
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 3
      },
      "XAGUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1384,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1425,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 32,
        "UNRESOLVED_BY_WINDOW": 24
      },
      "XAGUSD_SI": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 22,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 25
      },
      "XAUUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1322,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1420,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 37,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 14
      },
      "XAUUSD_GC": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 3,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 2
      },
      "XAUUSD_MGC": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 2
      },
      "XAUUSD_SCID": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 88,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 114,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3
      }
    },
    "fvg_fill": {
      "AUDJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 168,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 381,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 122,
        "UNRESOLVED_BY_WINDOW": 31
      },
      "AUDUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 202,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 382,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 138,
        "UNRESOLVED_BY_WINDOW": 27
      },
      "BTCUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 287,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 485,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 120,
        "UNRESOLVED_BY_WINDOW": 46
      },
      "CHFJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 182,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 358,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 125,
        "UNRESOLVED_BY_WINDOW": 24
      },
      "ETHUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 250,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 497,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 116,
        "UNRESOLVED_BY_WINDOW": 48
      },
      "EURGBP": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 127,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 266,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 122,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 28
      },
      "EURJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 177,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 316,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 103,
        "UNRESOLVED_BY_WINDOW": 34
      },
      "EURUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 3657,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 7024,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 2403,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 291
      },
      "GBPJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 56083,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 110466,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 33466,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 1185
      },
      "GBPUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 64122,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 125582,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 39470,
        "UNRESOLVED_AT_SOURCE_END": 8,
        "UNRESOLVED_BY_WINDOW": 1540
      },
      "GBPUSD_6B": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 81,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 104,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 30,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "GER40": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 339,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 670,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 227,
        "UNRESOLVED_BY_WINDOW": 65
      },
      "JP225": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 195,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 404,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 145,
        "UNRESOLVED_BY_WINDOW": 25
      },
      "NAS100": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 46356,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 87507,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 25253,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 1022
      },
      "NAS100_MNQ": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 83,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 155,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 44
      },
      "NAS100_NQ": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 91,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 159,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 46
      },
      "NZDUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 2852,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 5532,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1819,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 402
      },
      "SI": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 120,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 211,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 58,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "SPX500": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 149,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 292,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 128,
        "UNRESOLVED_BY_WINDOW": 23
      },
      "SPX_ES": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 62,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 95,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 31,
        "UNRESOLVED_AT_SOURCE_END": 2
      },
      "SPX_MES": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 62,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 98,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 32,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "UK100": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 340,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 682,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 262,
        "UNRESOLVED_BY_WINDOW": 49
      },
      "UKOIL_cash": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 200,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 316,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 101,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 32
      },
      "US30_MYM": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 98,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 158,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 43,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "US30_YM": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 160,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 263,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 59,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "US30_cash": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 46322,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 86587,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 25929,
        "UNRESOLVED_AT_SOURCE_END": 3,
        "UNRESOLVED_BY_WINDOW": 1599
      },
      "USDCAD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 138,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 289,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 114,
        "UNRESOLVED_BY_WINDOW": 27
      },
      "USDCHF": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 222,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 425,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 144,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 35
      },
      "USDJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 69081,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 131721,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 40818,
        "UNRESOLVED_AT_SOURCE_END": 8,
        "UNRESOLVED_BY_WINDOW": 1407
      },
      "USDJPY_6J": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 50,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 85,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 19,
        "UNRESOLVED_AT_SOURCE_END": 1
      },
      "USOIL_cash": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 191,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 281,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 95,
        "UNRESOLVED_BY_WINDOW": 27
      },
      "VIX": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 30,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 44,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 5,
        "UNRESOLVED_AT_SOURCE_END": 5,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "XAGUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 64400,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 122833,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 37913,
        "UNRESOLVED_AT_SOURCE_END": 3,
        "UNRESOLVED_BY_WINDOW": 1107
      },
      "XAGUSD_SI": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 139,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 147,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 9,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "XAUUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 70967,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 140732,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 40397,
        "UNRESOLVED_AT_SOURCE_END": 9,
        "UNRESOLVED_BY_WINDOW": 1308
      },
      "XAUUSD_GC": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 99,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 167,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 44,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "XAUUSD_MGC": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 101,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 148,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 41,
        "UNRESOLVED_AT_SOURCE_END": 2
      },
      "XAUUSD_SCID": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 5208,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 10120,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 2787,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 47
      }
    },
    "liquidity_stop_run_context": {
      "AUDJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 560,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 733,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 11,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 38
      },
      "AUDUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 602,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 770,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 16,
        "UNRESOLVED_BY_WINDOW": 39
      },
      "BTCUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 782,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 950,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 10,
        "UNRESOLVED_BY_WINDOW": 56
      },
      "CHFJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 652,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 907,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 16,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 40
      },
      "ETHUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 749,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 933,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 13,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 61
      },
      "EURGBP": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 762,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 885,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 25,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 81
      },
      "EURJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 698,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 888,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 16,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 40
      },
      "EURUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 13996,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 16955,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 299,
        "UNRESOLVED_AT_SOURCE_END": 5,
        "UNRESOLVED_BY_WINDOW": 522
      },
      "GBPJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 212369,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 262884,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3663,
        "UNRESOLVED_AT_SOURCE_END": 11,
        "UNRESOLVED_BY_WINDOW": 1965
      },
      "GBPUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 207957,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 251210,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3760,
        "UNRESOLVED_AT_SOURCE_END": 23,
        "UNRESOLVED_BY_WINDOW": 2711
      },
      "GBPUSD_6B": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 175,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 229,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "GER40": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1081,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1331,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 24,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 65
      },
      "JP225": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 516,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 617,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 10,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 22
      },
      "NAS100": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 154089,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 191678,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 2563,
        "UNRESOLVED_AT_SOURCE_END": 6,
        "UNRESOLVED_BY_WINDOW": 1324
      },
      "NAS100_MNQ": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 301,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 425,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 2
      },
      "NAS100_NQ": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 287,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 425,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "NZDUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 10289,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 12794,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 223,
        "UNRESOLVED_AT_SOURCE_END": 3,
        "UNRESOLVED_BY_WINDOW": 646
      },
      "SI": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 230,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 342,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 2,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "SPX500": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 453,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 536,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 12,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 39
      },
      "SPX_ES": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 240,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 291,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 2,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 2
      },
      "SPX_MES": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 229,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 300,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "UK100": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1011,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1183,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 23,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 55
      },
      "UKOIL_cash": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 362,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 428,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 5,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 29
      },
      "US30_MYM": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 291,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 359,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1,
        "UNRESOLVED_AT_SOURCE_END": 1
      },
      "US30_YM": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 291,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 337,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 5,
        "UNRESOLVED_AT_SOURCE_END": 1
      },
      "US30_cash": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 155882,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 189665,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3105,
        "UNRESOLVED_AT_SOURCE_END": 5,
        "UNRESOLVED_BY_WINDOW": 2131
      },
      "USDCAD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 512,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 688,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 9,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 38
      },
      "USDCHF": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 634,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 788,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 16,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 37
      },
      "USDJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 210102,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 253744,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3834,
        "UNRESOLVED_AT_SOURCE_END": 19,
        "UNRESOLVED_BY_WINDOW": 2415
      },
      "USDJPY_6J": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 131,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 200
      },
      "USOIL_cash": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 321,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 357,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 6,
        "UNRESOLVED_BY_WINDOW": 17
      },
      "VIX": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 14,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 17,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "XAGUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 179141,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 221116,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3273,
        "UNRESOLVED_AT_SOURCE_END": 15,
        "UNRESOLVED_BY_WINDOW": 1726
      },
      "XAGUSD_SI": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 10,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 16,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "XAUUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 228837,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 282681,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3576,
        "UNRESOLVED_AT_SOURCE_END": 7,
        "UNRESOLVED_BY_WINDOW": 2003
      },
      "XAUUSD_GC": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 337,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 437,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 10,
        "UNRESOLVED_AT_SOURCE_END": 1
      },
      "XAUUSD_MGC": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 331,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 456,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 7,
        "UNRESOLVED_AT_SOURCE_END": 1
      },
      "XAUUSD_SCID": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 17984,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 22490,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 266,
        "UNRESOLVED_BY_WINDOW": 63
      }
    },
    "ob_retest": {
      "AUDJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 447,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 341,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 15,
        "UNRESOLVED_BY_WINDOW": 53
      },
      "AUDUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 401,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 366,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 10,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 73
      },
      "BTCUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 588,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 501,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 23,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 99
      },
      "CHFJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 434,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 351,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 17,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 65
      },
      "ETHUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 527,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 494,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 20,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 112
      },
      "EURGBP": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 417,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 310,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 9,
        "UNRESOLVED_BY_WINDOW": 94
      },
      "EURJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 399,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 348,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 9,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 76
      },
      "EURUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 8050,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 6572,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 228,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 669
      },
      "GBPJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 120506,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 99607,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 2691,
        "UNRESOLVED_AT_SOURCE_END": 13,
        "UNRESOLVED_BY_WINDOW": 3155
      },
      "GBPUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 116867,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 100375,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 2757,
        "UNRESOLVED_AT_SOURCE_END": 8,
        "UNRESOLVED_BY_WINDOW": 3706
      },
      "GBPUSD_6B": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 126,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 73,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "GER40": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 696,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 615,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 22,
        "UNRESOLVED_BY_WINDOW": 116
      },
      "JP225": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 386,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 345,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 20,
        "UNRESOLVED_BY_WINDOW": 51
      },
      "NAS100": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 89791,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 80166,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 2509,
        "UNRESOLVED_AT_SOURCE_END": 7,
        "UNRESOLVED_BY_WINDOW": 2184
      },
      "NAS100_MNQ": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 229,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 186,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 7,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 2
      },
      "NAS100_NQ": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 228,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 180,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 5,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "NZDUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 5948,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 5059,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 179,
        "UNRESOLVED_BY_WINDOW": 946
      },
      "SI": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 234,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 189,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 12
      },
      "SPX500": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 341,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 292,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 16,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 52
      },
      "SPX_ES": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 192,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 110,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 2,
        "UNRESOLVED_BY_WINDOW": 2
      },
      "SPX_MES": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 190,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 119,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 2,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "UK100": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 725,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 613,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 27,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 101
      },
      "UKOIL_cash": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 348,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 316,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 14,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 53
      },
      "US30_MYM": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 200,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 150,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 2,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "US30_YM": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 209,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 167,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 4,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "US30_cash": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 88831,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 77276,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 2854,
        "UNRESOLVED_AT_SOURCE_END": 7,
        "UNRESOLVED_BY_WINDOW": 3213
      },
      "USDCAD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 355,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 279,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 7,
        "UNRESOLVED_BY_WINDOW": 60
      },
      "USDCHF": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 424,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 373,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 19,
        "UNRESOLVED_BY_WINDOW": 55
      },
      "USDJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 119331,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 101749,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3302,
        "UNRESOLVED_AT_SOURCE_END": 8,
        "UNRESOLVED_BY_WINDOW": 3438
      },
      "USDJPY_6J": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 121,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 64,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1,
        "UNRESOLVED_BY_WINDOW": 5
      },
      "USOIL_cash": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 328,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 273,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 16,
        "UNRESOLVED_BY_WINDOW": 56
      },
      "VIX": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 38,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 15,
        "UNRESOLVED_AT_SOURCE_END": 3,
        "UNRESOLVED_BY_WINDOW": 4
      },
      "XAGUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 108418,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 91201,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 2542,
        "UNRESOLVED_AT_SOURCE_END": 8,
        "UNRESOLVED_BY_WINDOW": 3121
      },
      "XAGUSD_SI": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 36,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 55
      },
      "XAUUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 133726,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 117867,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3105,
        "UNRESOLVED_AT_SOURCE_END": 5,
        "UNRESOLVED_BY_WINDOW": 3130
      },
      "XAUUSD_GC": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 219,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 165,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 8,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "XAUUSD_MGC": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 221,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 181,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 6,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "XAUUSD_SCID": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 10667,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 9078,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 214,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 120
      }
    },
    "opening_drive_no_fill_lifecycle": {
      "AUDJPY": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 232,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 195,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 9,
        "UNRESOLVED_BY_WINDOW": 10
      },
      "AUDUSD": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 227,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 200,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 7,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "BTCUSD": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 282,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 269,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 18,
        "UNRESOLVED_BY_WINDOW": 18
      },
      "CHFJPY": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 210,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 188,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 13,
        "UNRESOLVED_BY_WINDOW": 17
      },
      "ETHUSD": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 283,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 259,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 15,
        "UNRESOLVED_BY_WINDOW": 20
      },
      "EURGBP": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 208,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 173,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 12,
        "UNRESOLVED_BY_WINDOW": 28
      },
      "EURJPY": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 219,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 196,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 10,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 9
      },
      "EURUSD": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 1601,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 1651,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 98,
        "UNRESOLVED_BY_WINDOW": 26
      },
      "GBPJPY": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 9766,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 13050,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 269,
        "UNRESOLVED_BY_WINDOW": 909
      },
      "GBPUSD": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 7857,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 10633,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 371,
        "UNRESOLVED_BY_WINDOW": 474
      },
      "GBPUSD_6B": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 13,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 20,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "GER40": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 374,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 327,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 20,
        "UNRESOLVED_BY_WINDOW": 12
      },
      "JP225": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 214,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 203,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 13,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 12
      },
      "NAS100": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 2694,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 4072,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 445,
        "UNRESOLVED_AT_SOURCE_END": 3,
        "UNRESOLVED_BY_WINDOW": 44
      },
      "NAS100_MNQ": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 12,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 18,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "NAS100_NQ": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 13,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 17,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "NZDUSD": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 2423,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 2693,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 79,
        "UNRESOLVED_BY_WINDOW": 263
      },
      "SI": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 24,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 38,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "SPX500": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 158,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 155,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 8,
        "UNRESOLVED_BY_WINDOW": 13
      },
      "SPX_ES": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 11,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 20,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1
      },
      "SPX_MES": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 13,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 18,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "UK100": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 401,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 291,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 21,
        "UNRESOLVED_BY_WINDOW": 8
      },
      "UKOIL_cash": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 144,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 144,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 8,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 4
      },
      "US30_MYM": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 11,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 17,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "US30_YM": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 10,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 18,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "US30_cash": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 5363,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 7999,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 458,
        "UNRESOLVED_BY_WINDOW": 293
      },
      "USDCAD": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 196,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 173,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 6,
        "UNRESOLVED_BY_WINDOW": 10
      },
      "USDCHF": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 213,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 183,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 12,
        "UNRESOLVED_BY_WINDOW": 29
      },
      "USDJPY": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 11142,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 15409,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 469,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 931
      },
      "USDJPY_6J": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 8,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 26
      },
      "USOIL_cash": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 170,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 145,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 4,
        "UNRESOLVED_BY_WINDOW": 3
      },
      "VIX": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 14,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 16,
        "UNRESOLVED_BY_WINDOW": 2
      },
      "XAGUSD": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 7846,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 9364,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 354,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 254
      },
      "XAGUSD_SI": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 16,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 30,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1
      },
      "XAUUSD": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 8444,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 10441,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 461,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 191
      },
      "XAUUSD_GC": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 17,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 12,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "XAUUSD_MGC": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 18,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 11,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "XAUUSD_SCID": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 538,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 875,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3,
        "UNRESOLVED_BY_WINDOW": 49
      }
    },
    "session_kz_sweep": {
      "AUDJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 107,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 143,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 2,
        "UNRESOLVED_BY_WINDOW": 9
      },
      "AUDUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 120,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 125,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 2,
        "UNRESOLVED_BY_WINDOW": 8
      },
      "BTCUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 117,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 117,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 8,
        "UNRESOLVED_BY_WINDOW": 11
      },
      "CHFJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 134,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 176,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 13
      },
      "ETHUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 95,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 155,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1,
        "UNRESOLVED_BY_WINDOW": 11
      },
      "EURGBP": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 193,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 154,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 6,
        "UNRESOLVED_BY_WINDOW": 39
      },
      "EURJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 131,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 123,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 4,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 11
      },
      "EURUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1189,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1178,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 24,
        "UNRESOLVED_BY_WINDOW": 34
      },
      "GBPJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 9179,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 10664,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 194,
        "UNRESOLVED_BY_WINDOW": 324
      },
      "GBPUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 10733,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 11569,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 247,
        "UNRESOLVED_BY_WINDOW": 525
      },
      "GBPUSD_6B": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 24,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 17
      },
      "GER40": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 162,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 243,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 10,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 20
      },
      "JP225": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 110,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 140,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 5,
        "UNRESOLVED_BY_WINDOW": 13
      },
      "NAS100": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 4990,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 4842,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 315,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 186
      },
      "NAS100_MNQ": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 9,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 21
      },
      "NAS100_NQ": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 11,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 20
      },
      "NZDUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 2357,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 2803,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 42,
        "UNRESOLVED_BY_WINDOW": 272
      },
      "SI": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 12,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 25
      },
      "SPX500": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 89,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 78,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 4,
        "UNRESOLVED_BY_WINDOW": 18
      },
      "SPX_ES": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 27,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 26
      },
      "SPX_MES": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 29,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 27
      },
      "UK100": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 199,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 214,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 8,
        "UNRESOLVED_BY_WINDOW": 23
      },
      "UKOIL_cash": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 98,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 99,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 4,
        "UNRESOLVED_BY_WINDOW": 12
      },
      "US30_cash": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 5886,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 6131,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 217,
        "UNRESOLVED_BY_WINDOW": 212
      },
      "USDCAD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 115,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 146,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 2,
        "UNRESOLVED_BY_WINDOW": 12
      },
      "USDCHF": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 98,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 155,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 2,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 14
      },
      "USDJPY": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 8933,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 10518,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 174,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 602
      },
      "USDJPY_6J": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 11,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 17
      },
      "USOIL_cash": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 84,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 111,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3,
        "UNRESOLVED_BY_WINDOW": 10
      },
      "VIX": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 7,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 10
      },
      "XAGUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 9587,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 11151,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 203,
        "UNRESOLVED_BY_WINDOW": 425
      },
      "XAGUSD_SI": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 4,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 5
      },
      "XAUUSD": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 8479,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 9947,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 220,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 333
      },
      "XAUUSD_GC": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 28,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 9,
        "UNRESOLVED_BY_WINDOW": 2
      },
      "XAUUSD_MGC": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 35,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 10,
        "UNRESOLVED_BY_WINDOW": 2
      },
      "XAUUSD_SCID": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 876,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1187,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 15,
        "UNRESOLVED_BY_WINDOW": 27
      }
    }
  },
  "label_by_family_timeframe_status": {
    "adjacent_range_compression_breakout": {
      "H1": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 14153,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 2517,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 70,
        "UNRESOLVED_AT_SOURCE_END": 12,
        "UNRESOLVED_BY_WINDOW": 4519
      },
      "H4": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1316,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 80,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3,
        "UNRESOLVED_AT_SOURCE_END": 5,
        "UNRESOLVED_BY_WINDOW": 1580
      },
      "M1": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 264366,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 80723,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 245,
        "UNRESOLVED_AT_SOURCE_END": 12,
        "UNRESOLVED_BY_WINDOW": 2798
      },
      "M15": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 47395,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 9953,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 92,
        "UNRESOLVED_AT_SOURCE_END": 30,
        "UNRESOLVED_BY_WINDOW": 14793
      },
      "M5": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 69582,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 18463,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 100,
        "UNRESOLVED_AT_SOURCE_END": 12,
        "UNRESOLVED_BY_WINDOW": 9443
      }
    },
    "baseline_mean_reversion": {
      "H1": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 6707,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 24063,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 4325,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 153
      },
      "H4": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 962,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 4812,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 546,
        "UNRESOLVED_AT_SOURCE_END": 7,
        "UNRESOLVED_BY_WINDOW": 139
      },
      "M1": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 135427,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 510447,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 66937,
        "UNRESOLVED_AT_SOURCE_END": 7
      },
      "M15": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 25171,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 94203,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 14129,
        "UNRESOLVED_AT_SOURCE_END": 6,
        "UNRESOLVED_BY_WINDOW": 80
      },
      "M5": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 34821,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 140181,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 17891,
        "UNRESOLVED_AT_SOURCE_END": 10,
        "UNRESOLVED_BY_WINDOW": 17
      }
    },
    "baseline_momentum_continuation": {
      "H1": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 18934,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 42870,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1545,
        "UNRESOLVED_AT_SOURCE_END": 26,
        "UNRESOLVED_BY_WINDOW": 698
      },
      "H4": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 3228,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 7920,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 250,
        "UNRESOLVED_AT_SOURCE_END": 8,
        "UNRESOLVED_BY_WINDOW": 413
      },
      "M1": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 416736,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 874232,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 18737,
        "UNRESOLVED_AT_SOURCE_END": 9,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "M15": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 71196,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 161825,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 4409,
        "UNRESOLVED_AT_SOURCE_END": 16,
        "UNRESOLVED_BY_WINDOW": 748
      },
      "M5": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 105664,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 230723,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 5034,
        "UNRESOLVED_AT_SOURCE_END": 5,
        "UNRESOLVED_BY_WINDOW": 80
      }
    },
    "baseline_random_session_control": {
      "H1": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 20909,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 35268,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1858,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 237
      },
      "M1": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 6456,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 12695,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 255
      },
      "M15": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 19564,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 35720,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1264,
        "UNRESOLVED_BY_WINDOW": 38
      },
      "M5": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 8562,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 16609,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 445,
        "UNRESOLVED_BY_WINDOW": 1
      }
    },
    "baseline_shifted_entry_control": {
      "H1": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 35849,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 38592,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 5401,
        "UNRESOLVED_AT_SOURCE_END": 45,
        "UNRESOLVED_BY_WINDOW": 13943
      },
      "H4": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 4757,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 6335,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 549,
        "UNRESOLVED_AT_SOURCE_END": 16,
        "UNRESOLVED_BY_WINDOW": 3745
      },
      "M1": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 725525,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 859436,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 72744,
        "UNRESOLVED_AT_SOURCE_END": 22,
        "UNRESOLVED_BY_WINDOW": 3801
      },
      "M15": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 132714,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 150237,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 14625,
        "UNRESOLVED_AT_SOURCE_END": 43,
        "UNRESOLVED_BY_WINDOW": 24624
      },
      "M5": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 196748,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 226312,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 17646,
        "UNRESOLVED_AT_SOURCE_END": 14,
        "UNRESOLVED_BY_WINDOW": 9773
      }
    },
    "breaker_re_entry": {
      "H1": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 369,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 359,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 28,
        "UNRESOLVED_BY_WINDOW": 97
      },
      "H4": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 50,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 87,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3,
        "UNRESOLVED_AT_SOURCE_END": 1,
        "UNRESOLVED_BY_WINDOW": 35
      },
      "M1": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 6123,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 6547,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 274,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 14
      },
      "M15": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1233,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1263,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 50,
        "UNRESOLVED_AT_SOURCE_END": 2,
        "UNRESOLVED_BY_WINDOW": 89
      },
      "M5": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1710,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1834,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 82,
        "UNRESOLVED_BY_WINDOW": 17
      }
    },
    "fvg_fill": {
      "H1": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 10283,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 19352,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 8212,
        "UNRESOLVED_AT_SOURCE_END": 19,
        "UNRESOLVED_BY_WINDOW": 2831
      },
      "H4": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 1654,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 3768,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1417,
        "UNRESOLVED_AT_SOURCE_END": 12,
        "UNRESOLVED_BY_WINDOW": 1712
      },
      "M1": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 305230,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 592508,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 175697,
        "UNRESOLVED_AT_SOURCE_END": 10,
        "UNRESOLVED_BY_WINDOW": 280
      },
      "M15": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 43976,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 84455,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 28353,
        "UNRESOLVED_AT_SOURCE_END": 12,
        "UNRESOLVED_BY_WINDOW": 4640
      },
      "M5": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 72248,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 135899,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 39099,
        "UNRESOLVED_AT_SOURCE_END": 7,
        "UNRESOLVED_BY_WINDOW": 978
      }
    },
    "liquidity_stop_run_context": {
      "H1": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 37030,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 42779,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1456,
        "UNRESOLVED_AT_SOURCE_END": 31,
        "UNRESOLVED_BY_WINDOW": 4486
      },
      "H4": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 4473,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 5842,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 111,
        "UNRESOLVED_AT_SOURCE_END": 13,
        "UNRESOLVED_BY_WINDOW": 2227
      },
      "M1": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 940828,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 1154130,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 14555,
        "UNRESOLVED_AT_SOURCE_END": 22,
        "UNRESOLVED_BY_WINDOW": 428
      },
      "M15": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 166880,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 202815,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 4254,
        "UNRESOLVED_AT_SOURCE_END": 33,
        "UNRESOLVED_BY_WINDOW": 7719
      },
      "M5": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 253997,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 315479,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 4435,
        "UNRESOLVED_AT_SOURCE_END": 23,
        "UNRESOLVED_BY_WINDOW": 1311
      }
    },
    "ob_retest": {
      "H1": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 25009,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 20261,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1289,
        "UNRESOLVED_AT_SOURCE_END": 16,
        "UNRESOLVED_BY_WINDOW": 6311
      },
      "H4": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 3509,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 3517,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 79,
        "UNRESOLVED_AT_SOURCE_END": 8,
        "UNRESOLVED_BY_WINDOW": 2767
      },
      "M1": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 534151,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 463425,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 12273,
        "UNRESOLVED_AT_SOURCE_END": 23,
        "UNRESOLVED_BY_WINDOW": 681
      },
      "M15": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 99699,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 82686,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3371,
        "UNRESOLVED_AT_SOURCE_END": 22,
        "UNRESOLVED_BY_WINDOW": 11962
      },
      "M5": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 148826,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 126532,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 3653,
        "UNRESOLVED_AT_SOURCE_END": 13,
        "UNRESOLVED_BY_WINDOW": 3119
      }
    },
    "opening_drive_no_fill_lifecycle": {
      "H1": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 22253,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 21282,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1952,
        "UNRESOLVED_AT_SOURCE_END": 12,
        "UNRESOLVED_BY_WINDOW": 2276
      },
      "M1": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 4746,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 14446,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 35,
        "UNRESOLVED_BY_WINDOW": 123
      },
      "M15": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 24720,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 28393,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 1028,
        "UNRESOLVED_BY_WINDOW": 1120
      },
      "M5": {
        "MIDPOINT_RETRACE_BEFORE_EXTENSION": 9666,
        "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE": 15428,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 174,
        "UNRESOLVED_BY_WINDOW": 126
      }
    },
    "session_kz_sweep": {
      "H1": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 11543,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 10999,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 569,
        "UNRESOLVED_BY_WINDOW": 951
      },
      "H4": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 2997,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 3869,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 83,
        "UNRESOLVED_AT_SOURCE_END": 10,
        "UNRESOLVED_BY_WINDOW": 1712
      },
      "M1": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 18186,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 22618,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 262,
        "UNRESOLVED_BY_WINDOW": 1
      },
      "M15": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 19300,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 20696,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 563,
        "UNRESOLVED_BY_WINDOW": 477
      },
      "M5": {
        "ONE_ATR_CONTINUATION_CONTEXT_TOUCH": 12232,
        "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH": 14174,
        "SAME_BAR_CONTEXT_AMBIGUOUS": 238,
        "UNRESOLVED_BY_WINDOW": 27
      }
    }
  },
  "label_vocabulary": [
    "ONE_ATR_CONTINUATION_CONTEXT_TOUCH",
    "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH",
    "MIDPOINT_RETRACE_BEFORE_EXTENSION",
    "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE",
    "SAME_BAR_CONTEXT_AMBIGUOUS",
    "UNRESOLVED_BY_WINDOW",
    "UNRESOLVED_AT_SOURCE_END"
  ],
  "large_file_hash_resolution_count": 18,
  "live_effect": false,
  "missing_candidate_context_for_path_label": 0,
  "opened_families": [
    "ob_retest",
    "fvg_fill",
    "breaker_re_entry",
    "opening_drive_no_fill_lifecycle",
    "session_kz_sweep",
    "liquidity_stop_run_context",
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion",
    "adjacent_range_compression_breakout"
  ],
  "opened_family_count": 11,
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
  "path_label_row_count": 12852758,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "raw_candidate_attempts": 13540033,
  "route_id": "NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_SCREEN",
  "route_priority_not_performance": [
    {
      "ambiguity_unresolved_rate": 0.0621729,
      "baseline_distribution_js_divergence": 0.15904391,
      "candidate_denominator": 542262,
      "family_id": "adjacent_range_compression_breakout",
      "inspection_priority_score_not_performance": 23.060193,
      "priority_policy": "Full-population path-behavior inspection priority only; not validation, edge, R, PnL, win-rate, expectancy, or promotion.",
      "rank": 1
    },
    {
      "ambiguity_unresolved_rate": 0.01298558,
      "baseline_distribution_js_divergence": 0.0161661,
      "candidate_denominator": 3165357,
      "family_id": "liquidity_stop_run_context",
      "inspection_priority_score_not_performance": 21.999089,
      "priority_policy": "Full-population path-behavior inspection priority only; not validation, edge, R, PnL, win-rate, expectancy, or promotion.",
      "rank": 2
    },
    {
      "ambiguity_unresolved_rate": 0.02935034,
      "baseline_distribution_js_divergence": 0.02837154,
      "candidate_denominator": 1553202,
      "family_id": "ob_retest",
      "inspection_priority_score_not_performance": 21.612181,
      "priority_policy": "Full-population path-behavior inspection priority only; not validation, edge, R, PnL, win-rate, expectancy, or promotion.",
      "rank": 3
    },
    {
      "ambiguity_unresolved_rate": 0.09643372,
      "baseline_distribution_js_divergence": 0.03148052,
      "candidate_denominator": 1081043,
      "family_id": "baseline_mean_reversion",
      "inspection_priority_score_not_performance": 21.530428,
      "priority_policy": "Full-population path-behavior inspection priority only; not validation, edge, R, PnL, win-rate, expectancy, or promotion.",
      "rank": 4
    },
    {
      "ambiguity_unresolved_rate": 0.04632562,
      "baseline_distribution_js_divergence": 0.9550197,
      "candidate_denominator": 147780,
      "family_id": "opening_drive_no_fill_lifecycle",
      "inspection_priority_score_not_performance": 21.458852,
      "priority_policy": "Full-population path-behavior inspection priority only; not validation, edge, R, PnL, win-rate, expectancy, or promotion.",
      "rank": 5
    },
    {
      "ambiguity_unresolved_rate": 0.17178003,
      "baseline_distribution_js_divergence": 0.03075115,
      "candidate_denominator": 1532652,
      "family_id": "fvg_fill",
      "inspection_priority_score_not_performance": 20.622446,
      "priority_policy": "Full-population path-behavior inspection priority only; not validation, edge, R, PnL, win-rate, expectancy, or promotion.",
      "rank": 6
    },
    {
      "ambiguity_unresolved_rate": 0.06565412,
      "baseline_distribution_js_divergence": 0.00851365,
      "candidate_denominator": 2543496,
      "family_id": "baseline_shifted_entry_control",
      "inspection_priority_score_not_performance": 20.02036,
      "priority_policy": "Full-population path-behavior inspection priority only; not validation, edge, R, PnL, win-rate, expectancy, or promotion.",
      "rank": 7
    },
    {
      "ambiguity_unresolved_rate": 0.01627176,
      "baseline_distribution_js_divergence": 0.00992963,
      "candidate_denominator": 1965307,
      "family_id": "baseline_momentum_continuation",
      "inspection_priority_score_not_performance": 19.832679,
      "priority_policy": "Full-population path-behavior inspection priority only; not validation, edge, R, PnL, win-rate, expectancy, or promotion.",
      "rank": 8
    },
    {
      "ambiguity_unresolved_rate": 0.03457779,
      "baseline_distribution_js_divergence": 0.01681024,
      "candidate_denominator": 141507,
      "family_id": "session_kz_sweep",
      "inspection_priority_score_not_performance": 14.897141,
      "priority_policy": "Full-population path-behavior inspection priority only; not validation, edge, R, PnL, win-rate, expectancy, or promotion.",
      "rank": 9
    },
    {
      "ambiguity_unresolved_rate": 0.02564375,
      "baseline_distribution_js_divergence": 0.00460732,
      "candidate_denominator": 159883,
      "family_id": "baseline_random_session_control",
      "inspection_priority_score_not_performance": 13.664295,
      "priority_policy": "Full-population path-behavior inspection priority only; not validation, edge, R, PnL, win-rate, expectancy, or promotion.",
      "rank": 10
    },
    {
      "ambiguity_unresolved_rate": 0.03423948,
      "baseline_distribution_js_divergence": 0.01351858,
      "candidate_denominator": 20269,
      "family_id": "breaker_re_entry",
      "inspection_priority_score_not_performance": 13.073167,
      "priority_policy": "Full-population path-behavior inspection priority only; not validation, edge, R, PnL, win-rate, expectancy, or promotion.",
      "rank": 11
    }
  ],
  "schema_version": "family_path_behavior_discovery_result_screen_v1",
  "selected_source_count": 365,
  "source_progress_path": "research/science_program_2026_05/06_outcome_testing/no_api_mechanical_replay_family_path_behavior_discovery_result_screen/FPB_SOURCE_PROGRESS_2026-05-10_20260511_0420560000.jsonl",
  "unique_nonduplicate_candidate_path_label_denominator": 12852758,
  "validation_safe": false
}
```
