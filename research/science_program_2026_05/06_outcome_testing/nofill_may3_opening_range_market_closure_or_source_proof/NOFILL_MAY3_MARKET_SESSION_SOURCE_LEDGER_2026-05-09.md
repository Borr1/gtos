# NOFILL May 3 Market Session Source Ledger

- Generated UTC: 2026-05-09T02:50:02Z
- Source/control status: `MARKET_SESSION_NONTRADING_EMPTY_PROVEN_SOURCE_CONTROL`
- Official Sunday open UTC used for source contract: `2026-05-03T22:00:00Z`
- Frozen window before open: `True`

## Source Records

| Symbol | Family | Role | Window rows | First UTC | Last UTC | Policy |
|---|---|---|---:|---|---|---|
| NAS100 | broker_tick_parquet | broker_tick_parquet | 0 | 2026-05-03T22:00:00.391000Z | 2026-05-03T23:59:59.872000Z | primary_same_symbol_broker_quote_file_zero_rows_in_window_and_first_tick_after_window |
| XAUUSD | broker_tick_parquet | broker_tick_parquet | 0 | 2026-05-03T22:00:00.780000Z | 2026-05-03T23:59:59.226000Z | primary_same_symbol_broker_quote_file_zero_rows_in_window_and_first_tick_after_window |
| NAS100 | local_m1_ohlc_csv | worktree_converted_sierra_nq_to_nas100_m1 | 0 | 2025-10-29T22:43:00Z | 2026-05-01T20:59:00Z | supporting_absence_only_file_ends_before_may3_window |
| XAUUSD | local_m1_ohlc_csv | worktree_converted_sierra_xauusd_m1 | 0 | 2025-10-28T14:19:00Z | 2026-05-01T20:44:00Z | supporting_absence_only_file_ends_before_may3_window |
| NAS100 | local_m1_ohlc_csv | absolute_converted_sierra_nq_to_nas100_m1 | 0 | 2025-10-29T22:43:00Z | 2026-05-01T20:59:00Z | supporting_absence_only_file_ends_before_may3_window |
| XAUUSD | local_m1_ohlc_csv | absolute_converted_sierra_xauusd_m1 | 0 | 2025-10-28T14:19:00Z | 2026-05-01T20:44:00Z | supporting_absence_only_file_ends_before_may3_window |
| NAS100 | local_m1_ohlc_csv | first_wave_nq_m1 | 0 | 2026-04-15T00:00:00Z | 2026-04-17T20:59:00Z | supporting_absence_only_file_ends_before_may3_window |
| NAS100 | local_m1_ohlc_csv | first_wave_mnq_m1 | 0 | 2026-04-15T00:00:00Z | 2026-04-17T20:59:00Z | supporting_absence_only_file_ends_before_may3_window |
| XAUUSD | local_m1_ohlc_csv | first_wave_xauusd_scid_m1 | 0 | 2026-04-15T00:00:00Z | 2026-04-17T20:45:00Z | supporting_absence_only_file_ends_before_may3_window |
| XAUUSD | local_m1_ohlc_csv | first_wave_gc_m1 | 0 | 2026-04-15T00:00:00Z | 2026-04-17T20:59:00Z | supporting_absence_only_file_ends_before_may3_window |
| XAUUSD | local_m1_ohlc_csv | first_wave_mgc_m1 | 0 | 2026-04-15T00:00:00Z | 2026-04-17T20:59:00Z | supporting_absence_only_file_ends_before_may3_window |
| NAS100 | raw_sierra_scid | raw_sierra_nq_futures_proxy_scid | 0 | 2025-10-29T22:43:23.898000+00:00 | 2026-05-08T20:59:59.002006+00:00 | supporting_zero_rows_in_frozen_window_proxy_not_broker_quote |
| NAS100 | raw_sierra_scid | raw_sierra_mnq_futures_proxy_scid | 0 | 2025-10-28T14:54:37.713000+00:00 | 2026-05-08T20:59:59.437000+00:00 | supporting_zero_rows_in_frozen_window_proxy_not_broker_quote |
| XAUUSD | raw_sierra_scid | raw_sierra_xauusd_same_market_scid | 0 | 2025-10-28T14:19:09.044000+00:00 | 2026-05-01T20:44:58.881000+00:00 | supporting_absence_only_file_ends_before_may3_window |
| XAUUSD | raw_sierra_scid | raw_sierra_gc_futures_proxy_scid | 0 | 2025-10-29T05:09:05.892000+00:00 | 2026-05-08T20:59:59.668000+00:00 | supporting_zero_rows_in_frozen_window_proxy_not_broker_quote |
| XAUUSD | raw_sierra_scid | raw_sierra_mgc_futures_proxy_scid | 0 | 2025-10-29T06:30:54.023000+00:00 | 2026-05-08T20:59:59.077001+00:00 | supporting_zero_rows_in_frozen_window_proxy_not_broker_quote |
| NAS100 | raw_sierra_depth_date_file | raw_sierra_nq_depth_date_file |  |  |  | supporting_presence_only_depth_not_accepted_ohlc_or_quote_stream |
| NAS100 | raw_sierra_depth_date_file | raw_sierra_mnq_depth_date_file |  |  |  | supporting_presence_only_depth_not_accepted_ohlc_or_quote_stream |
| XAUUSD | raw_sierra_depth_date_file | raw_sierra_gc_depth_date_file |  |  |  | supporting_presence_only_depth_not_accepted_ohlc_or_quote_stream |
| XAUUSD | raw_sierra_depth_date_file | raw_sierra_mgc_depth_date_file |  |  |  | supporting_presence_only_depth_not_accepted_ohlc_or_quote_stream |

## Search Routes

- `worktree_target_lane`: searched - controlling prompt, starter, raw source capture, generated lane outputs
- `worktree_data_sierra_ohlcv`: searched - converted M1 OHLC roots for NAS100 and XAUUSD
- `absolute_broker_tick_parquet`: searched - NAS100 and XAUUSD 2026-05-03 broker tick parquets
- `absolute_sierra_ohlcv`: searched - absolute converted M1 OHLC roots for NAS100 and XAUUSD
- `absolute_sierra_raw_scid`: searched - NQM26, MNQM26, XAUUSD, GCM26, MGCM26 raw SCID files
- `absolute_sierra_market_depth`: searched - NQ/MNQ/GC/MGC 2026-05-03 depth files; not accepted as OHLC/quote stream
- `broad_tmp_targeted_rg`: searched_with_access_denied_noise - found prior worktree artifacts and stale research reports; no additional approved broker tick/M1 source consumed
- `documents_targeted_rg`: searched - found main repo source docs/orderflow reports only; paid/cached Databento artifacts not consumed
- `mt5_read_only_route`: not_used_for_source_evidence - copy_ticks_range/copy_rates_range/symbol_info present; Python package exposed no session schedule function in this environment; no account/order/history routes called
- `official_cme_web_route`: web_tool_capture_used_curl_failed - official CME NQ and GC product-page trading-hours source contract
