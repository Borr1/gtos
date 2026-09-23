# G12 NOFILL Remaining USDJPY Same-Tick Impossibility Audit - 2026-05-09

Decision: `ACCEPT_AS_SOURCE_IMPOSSIBILITY_EVIDENCE_ONLY`

## Row Audit

| packet_row_id | same_tick_impossibility_holds | exact_rows |
| --- | --- | --- |
| NOFILL-CAT-ROW-0130 | True | 1 |
| NOFILL-CAT-ROW-0143 | True | 1 |
| NOFILL-CAT-ROW-0165 | True | 1 |
| NOFILL-CAT-ROW-0178 | True | 1 |

## Official Source Contract

```json
{
  "copyticksrange_flags_describe_changed_fields": true,
  "copyticksrange_orders_rows_past_to_present": true,
  "mqltick_has_bid_ask": true,
  "mqltick_has_flags": true,
  "mqltick_has_time_msc": true,
  "python_returns_named_time_bid_ask_last_flags": true,
  "sub_row_sequence_field_found": false
}
```

## Independent Source Search

No searched local root or prior worktree exposed a source-safe USDJPY route with sequence ID, sub-millisecond timestamp, or sub-row quote-event ordering. All found USDJPY sources are quote-state rows, M1 context, or futures/proxy context. XAUUSD 0241 is resolved by read-only side-aware broker ticks.

Exact unblocker: A broker-native USDJPY quote-event source with a sequence ID, exchange/broker quote-event sequence number, or sub-millisecond/sub-row timestamp for each quote update, source-hashed and without account/order/history labels.

This is impossibility evidence only, not a result or validation label.
