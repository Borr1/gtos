# Raw OHLC Pre-Fill Delivery Path Coverage

Date: 2026-05-03
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`
Discovery label: `COVERAGE_ONLY_NOT_STRATEGY_SCORE`

## Registered Question Before Outputs

Can existing local OHLC rows reconstruct setup-close-to-fill/expiry pre-fill paths and expose as-of delivery proxies without using post-fill outcome information?

## Bottom Line

Existing local OHLC rows can reconstruct a pre-fill path coverage ledger for setup-ok V2/J46 rows, but the result is coverage/tooling only. It still lacks original POI bounds, true broker pending-limit lifecycle state, and intrabar ordering inside the fill row.

## Coverage

| metric | value |
| --- | --- |
| setup rows seen | 12831 |
| captured setup rows | 12831 |
| lower-TF available rows | 5512 |
| lower-TF available rate | 0.429585 |
| selected timeframes | {'M15': 7319, 'M5': 4738, 'M1': 774} |
| fill/expiry states | {'FILLED_RECONSTRUCTED_PATH_TOUCH': 5088, 'NOT_FILLED_BEFORE_EXPIRY_ON_SELECTED_PATH': 6063, 'UNRESOLVED_PATH_ENDS_BEFORE_EXPIRY': 1679, 'NO_PATH_ROWS': 1} |
| rows with original POI bounds | 0 |
| rows with broker lifecycle state | 0 |
| rows with structure proxy | 12626 |

## By Symbol

| symbol | n | lower-TF rate | selected timeframes | fill/expiry states |
| --- | --- | --- | --- | --- |
| GBPJPY | 1211 | 0.453344 | {'M15': 662, 'M5': 471, 'M1': 78} | {'FILLED_RECONSTRUCTED_PATH_TOUCH': 481, 'NOT_FILLED_BEFORE_EXPIRY_ON_SELECTED_PATH': 560, 'UNRESOLVED_PATH_ENDS_BEFORE_EXPIRY': 170} |
| GBPUSD | 1633 | 0.390692 | {'M15': 995, 'M5': 456, 'M1': 182} | {'FILLED_RECONSTRUCTED_PATH_TOUCH': 740, 'NOT_FILLED_BEFORE_EXPIRY_ON_SELECTED_PATH': 686, 'UNRESOLVED_PATH_ENDS_BEFORE_EXPIRY': 207} |
| NAS100 | 2017 | 0.603371 | {'M15': 800, 'M5': 1195, 'M1': 22} | {'FILLED_RECONSTRUCTED_PATH_TOUCH': 902, 'UNRESOLVED_PATH_ENDS_BEFORE_EXPIRY': 238, 'NOT_FILLED_BEFORE_EXPIRY_ON_SELECTED_PATH': 877} |
| US30_cash | 1205 | 0.351037 | {'M15': 782, 'M5': 361, 'M1': 62} | {'NOT_FILLED_BEFORE_EXPIRY_ON_SELECTED_PATH': 672, 'FILLED_RECONSTRUCTED_PATH_TOUCH': 396, 'UNRESOLVED_PATH_ENDS_BEFORE_EXPIRY': 136, 'NO_PATH_ROWS': 1} |
| USDJPY | 3849 | 0.261886 | {'M15': 2841, 'M5': 841, 'M1': 167} | {'FILLED_RECONSTRUCTED_PATH_TOUCH': 1690, 'UNRESOLVED_PATH_ENDS_BEFORE_EXPIRY': 467, 'NOT_FILLED_BEFORE_EXPIRY_ON_SELECTED_PATH': 1692} |
| XAGUSD | 1217 | 0.552177 | {'M15': 545, 'M5': 616, 'M1': 56} | {'NOT_FILLED_BEFORE_EXPIRY_ON_SELECTED_PATH': 678, 'FILLED_RECONSTRUCTED_PATH_TOUCH': 344, 'UNRESOLVED_PATH_ENDS_BEFORE_EXPIRY': 195} |
| XAUUSD | 1699 | 0.591524 | {'M15': 694, 'M5': 798, 'M1': 207} | {'FILLED_RECONSTRUCTED_PATH_TOUCH': 535, 'NOT_FILLED_BEFORE_EXPIRY_ON_SELECTED_PATH': 898, 'UNRESOLVED_PATH_ENDS_BEFORE_EXPIRY': 266} |

## Source Inventory

| symbol | tf | rows | first close | last close | source |
| --- | --- | --- | --- | --- | --- |
| GBPJPY | M1 | 99711 | 2026-01-23T08:55:00+00:00 | 2026-05-01T00:00:00+00:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\GBPJPY_M1.csv |
| GBPJPY | M15 | 100012 | 2022-04-14T11:30:00+00:00 | 2026-05-01T00:00:00+00:00 | data\mt5_research_exports\phase3_m15_2022_2026_fn_chunked_v1\GBPJPY_M15.csv |
| GBPJPY | M5 | 99941 | 2024-12-26T11:30:00+00:00 | 2026-05-01T00:00:00+00:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\GBPJPY_M5.csv |
| GBPUSD | M1 | 99722 | 2026-01-23T09:16:00+00:00 | 2026-05-01T00:00:00+00:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\GBPUSD_M1.csv |
| GBPUSD | M15 | 100012 | 2022-04-14T19:15:00+00:00 | 2026-05-01T00:00:00+00:00 | data\mt5_research_exports\phase3_m15_2022_2026_fn_chunked_v1\GBPUSD_M15.csv |
| GBPUSD | M5 | 99941 | 2024-12-26T16:55:00+00:00 | 2026-05-01T00:00:00+00:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\GBPUSD_M5.csv |
| NAS100 | M1 | 99768 | 2026-01-20T05:28:00+00:00 | 2026-05-01T00:00:00+00:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\NAS100_M1.csv |
| NAS100 | M15 | 72862 | 2022-10-20T11:15:00+00:00 | 2026-05-01T00:00:00+00:00 | data\mt5_research_exports\phase3_m15_2022_2026_fn_chunked_v1\NAS100_M15.csv |
| NAS100 | M5 | 99953 | 2024-11-28T06:35:00+00:00 | 2026-05-01T00:00:00+00:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\NAS100_M5.csv |
| US30_cash | M1 | 99769 | 2026-01-20T02:02:00+00:00 | 2026-04-30T23:59:00+00:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\US30_cash_M1.csv |
| US30_cash | M15 | 72847 | 2022-10-20T11:15:00+00:00 | 2026-05-01T00:00:00+00:00 | data\mt5_research_exports\phase3_m15_2022_2026_fn_chunked_v1\US30_cash_M15.csv |
| US30_cash | M5 | 99953 | 2024-11-28T06:15:00+00:00 | 2026-05-01T00:00:00+00:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\US30_cash_M5.csv |
| USDJPY | M1 | 99718 | 2026-01-23T08:59:00+00:00 | 2026-05-01T00:00:00+00:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\USDJPY_M1.csv |
| USDJPY | M15 | 100012 | 2022-04-14T19:15:00+00:00 | 2026-05-01T00:00:00+00:00 | data\mt5_research_exports\phase3_m15_2022_2026_fn_chunked_v1\USDJPY_M15.csv |
| USDJPY | M5 | 99941 | 2024-12-26T17:35:00+00:00 | 2026-05-01T00:00:00+00:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\USDJPY_M5.csv |
| XAGUSD | M1 | 99768 | 2026-01-19T11:40:00+00:00 | 2026-05-01T00:00:00+00:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\XAGUSD_M1.csv |
| XAGUSD | M15 | 99195 | 2022-01-03T01:15:00+00:00 | 2026-05-01T00:00:00+00:00 | data\mt5_research_exports\phase3_m15_2022_2026_fn_chunked_v1\XAGUSD_M15.csv |
| XAGUSD | M5 | 99953 | 2024-11-29T03:25:00+00:00 | 2026-05-01T00:00:00+00:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\XAGUSD_M5.csv |
| XAUUSD | M1 | 99768 | 2026-01-19T12:00:00+00:00 | 2026-05-01T00:00:00+00:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\XAUUSD_M1.csv |
| XAUUSD | M15 | 100012 | 2022-02-01T21:45:00+00:00 | 2026-05-01T00:00:00+00:00 | data\mt5_research_exports\phase3_m15_2022_2026_fn_chunked_v1\XAUUSD_M15.csv |
| XAUUSD | M5 | 99953 | 2024-11-29T06:45:00+00:00 | 2026-05-01T00:00:00+00:00 | data\mt5_research_exports\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\XAUUSD_M5.csv |

## Outputs

| artifact | value |
| --- | --- |
| summary json | research/phase_3_external_feed_validation/RAW_OHLC_PREFILL_DELIVERY_PATH_COVERAGE_2026-05-03.json |
| sample jsonl | research/phase_3_external_feed_validation/RAW_OHLC_PREFILL_DELIVERY_PATH_SAMPLE_2026-05-03.jsonl |
| markdown | research/phase_3_external_feed_validation/RAW_OHLC_PREFILL_DELIVERY_PATH_COVERAGE_2026-05-03.md |
| jsonl sample rows | 200 |
| full captured records counted | 12831 |

## Captured Row Schema

Each JSONL row includes:

- `setup_id`
- `symbol`
- `side`
- `setup_decision_close_utc`
- `pending_limit_created_utc`
- `entry_price`
- `original_poi_type_and_bounds`
- `pre_fill_path_timeframe`
- `pre_fill_path_rows`
- `fill_or_expiry_state`
- `lower_tf_available`
- `as_of_delivery_structure_flags`
- `ambiguity_flags`

## Ambiguity Flag Counts

| flag | count |
| --- | --- |
| BROKER_PENDING_LIFECYCLE_STATE_MISSING | 12831 |
| LOWER_TF_UNAVAILABLE_SELECTED_M15 | 7319 |
| M15_FILL_ROW_INTRABAR_ORDER_AMBIGUOUS | 2941 |
| M1_FILL_ROW_INTRABAR_ORDER_AMBIGUOUS | 417 |
| M1_M5_UNAVAILABLE_IN_POST_DECISION_WINDOW | 7319 |
| M1_UNAVAILABLE_IN_POST_DECISION_WINDOW | 4738 |
| M5_FILL_ROW_INTRABAR_ORDER_AMBIGUOUS | 1730 |
| NO_POST_DECISION_PATH_ROWS | 1 |
| ORIGINAL_POI_TYPE_AND_BOUNDS_MISSING_IN_V2_EVENT_LOG | 12831 |
| PATH_SOURCE_ENDS_BEFORE_PENDING_EXPIRY | 1679 |
| PENDING_LIMIT_CREATED_UTC_ASSUMED_EQUAL_SETUP_DECISION_CLOSE | 12831 |

## Missing Fields

- `original_poi_type_and_bounds`
- `broker_pending_lifecycle_state`
- `true_pending_limit_created_utc`
- `intrabar_order_inside_fill_row`

## Explicit Non-Claims

- No delivery-leg strategy is scored.
- Reconstructed fill touch is an OHLC path touch, not a broker-confirmed fill.
- As-of delivery structure flags are primitive OHLC proxies, not validated market-structure labels.
- Post-fill rows are not used to define pre-fill structure flags.

## Next Steps

1. Add true pending-limit lifecycle telemetry before treating reconstructed touches as broker fills.
2. Add original POI type/bounds to future path-scaling event logs.
3. Use this coverage ledger as an input to V3/design forensics only after risk-bank tests exist.
4. Keep any delivery-leg plus reversal-leg scoring in a separate pre-registered discovery task.
