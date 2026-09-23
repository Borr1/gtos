# G12 CNR Exact Blocker Ledger - 2026-05-08

Promotion verdict: `NO_PROMOTION_VERDICT`  
Validation safe: `false`  
Outcome review opened: `false`  
Live effect: `false`

## Blocked Row Count

```json
6098
```

## All Blocked Rows Have Exact Requirements

```json
true
```

## Exact Requirement Counts

```json
{
  "CNR_T1 target contract with frozen fixed-R multiple, stop model, executable entry quote, and source hash before outcome opening": 1550,
  "CNR_T2 structural target contract with as-of level id, level timestamp, parser version, selection rule, and source hash": 1550,
  "CNR_T3 terminal target contract with frozen horizon, terminal pricing source, same-bar/tick ordering policy, and source hash": 1550,
  "decision_request_sent_utc, decision_response_received_utc, latency_ms, and frozen latency policy": 1240,
  "earlier same-day tick/quote coverage for the trigger window; existing local parquet starts after the trigger or has no eligible quote at or before asof_cutoff_utc": 88,
  "input-only invalid-clearing policy for market-entry rows where the source-hashed executable quote is already past the original TP1 before any result audit": 490,
  "local read-only tick parquet or approved source-hashed quote cache for the exact broker symbol/date under approved roots": 24,
  "pre-outcome logger/parser field signal_emitted_utc joined to source_record_id": 1240,
  "pretouch_trigger_id and pretouch_trigger_utc captured as-of before any result path is opened": 1240,
  "source-bound fixed-R target model definition before outcomes": 1550,
  "source-bound structural target level selected as-of before outcomes": 1550,
  "source-bound terminal timebox policy before outcomes": 1550,
  "source-hashed decision request/response timestamps and frozen latency policy for this source_record_id": 1240,
  "source-hashed executable bid/ask/spread quote at or before the timing trigger for the packet symbol/date, with quote_timestamp_utc and source_sha256": 112,
  "source-hashed pretouch trigger id/utc captured before any outcome path review": 1240,
  "source-hashed signal_emitted_utc materialized for this source_record_id": 1240,
  "source-hashed timing trigger field materialized before outcome opening; CNR_E2 needs signal_emitted_utc, CNR_E3 needs request/response latency clock fields, and CNR_E4 needs pretouch_trigger_id/pretouch_trigger_utc": 3720
}
```

## Top Blocker Groups

```json
[
  {
    "exact_blockers": [
      "requires frozen R multiple, stop model, and executable quote binding before outcome opening"
    ],
    "row_count": 592
  },
  {
    "exact_blockers": [
      "requires structured level id/timestamp/parser/source hash selected before outcomes"
    ],
    "row_count": 592
  },
  {
    "exact_blockers": [
      "requires terminal pricing, timebox horizon, and same-bar/tick ordering policy before outcomes"
    ],
    "row_count": 592
  },
  {
    "exact_blockers": [
      "pre-entry executable quote is already beyond original TP1 in favorable direction"
    ],
    "row_count": 490
  },
  {
    "exact_blockers": [
      "BLOCKED_TIMING_TRIGGER_NOT_MATERIALIZED",
      "source-hashed signal_emitted_utc logger field is absent from current approved packet sources"
    ],
    "row_count": 310
  },
  {
    "exact_blockers": [
      "BLOCKED_TIMING_TRIGGER_NOT_MATERIALIZED",
      "requires frozen R multiple, stop model, and executable quote binding before outcome opening",
      "source-hashed signal_emitted_utc logger field is absent from current approved packet sources"
    ],
    "row_count": 310
  },
  {
    "exact_blockers": [
      "BLOCKED_TIMING_TRIGGER_NOT_MATERIALIZED",
      "requires structured level id/timestamp/parser/source hash selected before outcomes",
      "source-hashed signal_emitted_utc logger field is absent from current approved packet sources"
    ],
    "row_count": 310
  },
  {
    "exact_blockers": [
      "BLOCKED_TIMING_TRIGGER_NOT_MATERIALIZED",
      "requires terminal pricing, timebox horizon, and same-bar/tick ordering policy before outcomes",
      "source-hashed signal_emitted_utc logger field is absent from current approved packet sources"
    ],
    "row_count": 310
  },
  {
    "exact_blockers": [
      "BLOCKED_TIMING_TRIGGER_NOT_MATERIALIZED",
      "decision_request_sent_utc/response_received_utc and latency policy are not bound in source packet"
    ],
    "row_count": 310
  },
  {
    "exact_blockers": [
      "BLOCKED_TIMING_TRIGGER_NOT_MATERIALIZED",
      "decision_request_sent_utc/response_received_utc and latency policy are not bound in source packet",
      "requires frozen R multiple, stop model, and executable quote binding before outcome opening"
    ],
    "row_count": 310
  },
  {
    "exact_blockers": [
      "BLOCKED_TIMING_TRIGGER_NOT_MATERIALIZED",
      "decision_request_sent_utc/response_received_utc and latency policy are not bound in source packet",
      "requires structured level id/timestamp/parser/source hash selected before outcomes"
    ],
    "row_count": 310
  },
  {
    "exact_blockers": [
      "BLOCKED_TIMING_TRIGGER_NOT_MATERIALIZED",
      "decision_request_sent_utc/response_received_utc and latency policy are not bound in source packet",
      "requires terminal pricing, timebox horizon, and same-bar/tick ordering policy before outcomes"
    ],
    "row_count": 310
  },
  {
    "exact_blockers": [
      "BLOCKED_TIMING_TRIGGER_NOT_MATERIALIZED",
      "pretouch_trigger_id/pretouch_trigger_utc source-safe logger is absent; cannot infer from later path"
    ],
    "row_count": 310
  },
  {
    "exact_blockers": [
      "BLOCKED_TIMING_TRIGGER_NOT_MATERIALIZED",
      "pretouch_trigger_id/pretouch_trigger_utc source-safe logger is absent; cannot infer from later path",
      "requires frozen R multiple, stop model, and executable quote binding before outcome opening"
    ],
    "row_count": 310
  },
  {
    "exact_blockers": [
      "BLOCKED_TIMING_TRIGGER_NOT_MATERIALIZED",
      "pretouch_trigger_id/pretouch_trigger_utc source-safe logger is absent; cannot infer from later path",
      "requires structured level id/timestamp/parser/source hash selected before outcomes"
    ],
    "row_count": 310
  },
  {
    "exact_blockers": [
      "BLOCKED_TIMING_TRIGGER_NOT_MATERIALIZED",
      "pretouch_trigger_id/pretouch_trigger_utc source-safe logger is absent; cannot infer from later path",
      "requires terminal pricing, timebox horizon, and same-bar/tick ordering policy before outcomes"
    ],
    "row_count": 310
  },
  {
    "exact_blockers": [
      "BLOCKED_NO_SOURCE_HASHED_EXECUTABLE_QUOTE",
      "NO_ELIGIBLE_EXECUTABLE_QUOTE_AS_OF"
    ],
    "row_count": 22
  },
  {
    "exact_blockers": [
      "BLOCKED_NO_SOURCE_HASHED_EXECUTABLE_QUOTE",
      "NO_ELIGIBLE_EXECUTABLE_QUOTE_AS_OF",
      "requires frozen R multiple, stop model, and executable quote binding before outcome opening"
    ],
    "row_count": 22
  },
  {
    "exact_blockers": [
      "BLOCKED_NO_SOURCE_HASHED_EXECUTABLE_QUOTE",
      "NO_ELIGIBLE_EXECUTABLE_QUOTE_AS_OF",
      "requires structured level id/timestamp/parser/source hash selected before outcomes"
    ],
    "row_count": 22
  },
  {
    "exact_blockers": [
      "BLOCKED_NO_SOURCE_HASHED_EXECUTABLE_QUOTE",
      "NO_ELIGIBLE_EXECUTABLE_QUOTE_AS_OF",
      "requires terminal pricing, timebox horizon, and same-bar/tick ordering policy before outcomes"
    ],
    "row_count": 22
  },
  {
    "exact_blockers": [
      "BLOCKED_NO_SOURCE_HASHED_EXECUTABLE_QUOTE",
      "NO_LOCAL_TICK_PARQUET_FOR_SYMBOL_DATE"
    ],
    "row_count": 6
  },
  {
    "exact_blockers": [
      "BLOCKED_NO_SOURCE_HASHED_EXECUTABLE_QUOTE",
      "NO_LOCAL_TICK_PARQUET_FOR_SYMBOL_DATE",
      "requires frozen R multiple, stop model, and executable quote binding before outcome opening"
    ],
    "row_count": 6
  },
  {
    "exact_blockers": [
      "BLOCKED_NO_SOURCE_HASHED_EXECUTABLE_QUOTE",
      "NO_LOCAL_TICK_PARQUET_FOR_SYMBOL_DATE",
      "requires structured level id/timestamp/parser/source hash selected before outcomes"
    ],
    "row_count": 6
  },
  {
    "exact_blockers": [
      "BLOCKED_NO_SOURCE_HASHED_EXECUTABLE_QUOTE",
      "NO_LOCAL_TICK_PARQUET_FOR_SYMBOL_DATE",
      "requires terminal pricing, timebox horizon, and same-bar/tick ordering policy before outcomes"
    ],
    "row_count": 6
  }
]
```

