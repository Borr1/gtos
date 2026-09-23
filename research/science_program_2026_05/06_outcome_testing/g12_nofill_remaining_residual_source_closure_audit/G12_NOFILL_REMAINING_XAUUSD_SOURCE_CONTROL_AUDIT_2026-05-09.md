# G12 NOFILL Remaining XAUUSD Source-Control Audit - 2026-05-09

Decision: `ACCEPT_AS_SOURCE_CONTROL_INPUT_ONLY_EVIDENCE`

## Direct Recheck

```json
{
  "may5_active_window": {
    "columns": [
      "ts_utc",
      "ts_msc",
      "bid",
      "ask",
      "last",
      "volume",
      "flags",
      "inferred_aggressor"
    ],
    "entry_price": 4668.45,
    "exists": true,
    "first_window_ts_utc": "2026-05-05T08:15:26.522000Z",
    "last_window_ts_utc": "2026-05-05T23:59:59.998000Z",
    "max_ask": 4596.34,
    "max_bid": 4595.69,
    "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-05.parquet",
    "rows_total": 460423,
    "sha256": "9a361078f8448d8d69aacbf3905d38d291282ce223d269fe033b0e6eb9814a0f",
    "short_entry_touch_bid_ge_entry": false,
    "window_rows": 325629
  },
  "recovered_may6_gap": {
    "columns": [
      "ts_utc",
      "ts_msc",
      "time",
      "bid",
      "ask",
      "last",
      "volume",
      "flags",
      "volume_real",
      "broker_offset_seconds_applied",
      "mt5_symbol"
    ],
    "entry_price": 4668.45,
    "exists": true,
    "first_window_ts_utc": "2026-05-06T00:00:00.025000Z",
    "last_window_ts_utc": "2026-05-06T00:00:36.853000Z",
    "max_ask": 4596.87,
    "max_bid": 4596.22,
    "path": "C:\\tmp\\gtos_otb\\G12NOFILLREMAINING\\research\\science_program_2026_05\\06_outcome_testing\\nofill_remaining_residual_source_closure\\raw\\NOFILL_REMAINING_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_000000_000037.parquet",
    "rows_total": 549,
    "sha256": "e58f36caad1108c641a08636f65dfa9b593a14c156b5166b48ac5236259add50",
    "short_entry_touch_bid_ge_entry": false,
    "window_rows": 549
  }
}
```

## Interpretation

Accept. The May 5 broker tick stream and recovered true-UTC May 6 gap stream are side-aware, hashed, and show bid below the short entry through the observed cancel. The capture recorded zero account, order, deal, position, history, order_send, paid API, or Databento calls.

It proves no side-aware short entry touch through cancel for source/control input use only. It does not prove a lifecycle label, result, R/performance, denominator admission, validation, promotion, or live behavior.
