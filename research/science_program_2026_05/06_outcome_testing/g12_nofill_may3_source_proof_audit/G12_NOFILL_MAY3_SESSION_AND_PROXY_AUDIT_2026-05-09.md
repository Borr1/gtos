# G12 NOFILL May 3 Session And Proxy Audit - 2026-05-09

Generated: `2026-05-09T03:38:51Z`

Decision: `ACCEPT_AS_SOURCE_CONTROL_MARKET_SESSION_EMPTY_EVIDENCE_ONLY`

## Timezone Recompute

```json
{
  "date": "2026-05-03",
  "frozen_window_chicago_ct": {
    "end": "2026-05-03T08:30:00-05:00",
    "start": "2026-05-03T08:00:00-05:00",
    "timezone": "America/Chicago",
    "utc_offset": "-0500"
  },
  "frozen_window_new_york_et": {
    "end": "2026-05-03T09:30:00-04:00",
    "start": "2026-05-03T09:00:00-04:00",
    "timezone": "America/New_York",
    "utc_offset": "-0400"
  },
  "frozen_window_utc": {
    "end": "2026-05-03T13:30:00Z",
    "start": "2026-05-03T13:00:00Z"
  },
  "minutes_from_window_end_to_globex_open": 510,
  "official_globex_sunday_open_chicago_ct": "2026-05-03T17:00:00-05:00",
  "official_globex_sunday_open_new_york_et": "2026-05-03T18:00:00-04:00",
  "official_globex_sunday_open_utc": "2026-05-03T22:00:00Z",
  "weekday": "Sunday",
  "window_is_before_official_sunday_open": true
}
```

The frozen window was Sunday `08:00-08:30` America/Chicago and `09:00-09:30` America/New_York. CME Sunday evening open for the official proxy markets converts to `2026-05-03T22:00:00Z`, so the frozen range ended `510` minutes before open.

## Official Source Recheck

- NQ official source: CME E-mini Nasdaq-100 page, `turn5view1 lines 302-312`, short captured trading-hours phrase under 25 words.
- GC official source: CME Gold contract specs page, `turn5view3 lines 254-262`, short captured trading-hours phrase under 25 words.
- Upstream direct curl attempts remain honest negative evidence: failed attempts are recorded with `used_for_factual_claims=false`.

## Proxy Review

NAS100-to-NQ and XAUUSD-to-GC are accepted only for market-session source-control evidence. They do not prove broker-native CFD schedule, fill state, price path, result outcome, or validation. Same-symbol broker tick files are the broker-side quote evidence and the official CME markets are the session-open proxy evidence.

This is not a result label.

## Searched Routes

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
