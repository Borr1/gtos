# G12 NOFILL USDJPY Sequence Decision Ledger - 2026-05-09

Promotion verdict: `NO_PROMOTION_VERDICT`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

Terminal G12 verdict: `ACCEPT_AS_SOURCE_IMPOSSIBILITY_EVIDENCE_ONLY`.

| packet_row_id | symbol | side | decisive_timestamp_utc | rows_at_timestamp | sequence_like_fields | g12_verdict |
| --- | --- | --- | --- | --- | --- | --- |
| NOFILL-CAT-ROW-0130 | USDJPY | LONG | 2026-04-20T00:15:04.153000Z | 1 | none | ACCEPT_AS_SOURCE_IMPOSSIBILITY_EVIDENCE_ONLY |
| NOFILL-CAT-ROW-0143 | USDJPY | SHORT | 2026-05-01T00:30:00.083000Z | 1 | none | ACCEPT_AS_SOURCE_IMPOSSIBILITY_EVIDENCE_ONLY |
| NOFILL-CAT-ROW-0165 | USDJPY | LONG | 2026-04-20T00:15:04.153000Z | 1 | none | ACCEPT_AS_SOURCE_IMPOSSIBILITY_EVIDENCE_ONLY |
| NOFILL-CAT-ROW-0178 | USDJPY | SHORT | 2026-05-01T00:30:00.083000Z | 1 | none | ACCEPT_AS_SOURCE_IMPOSSIBILITY_EVIDENCE_ONLY |

## Decision

The source-access lane is accepted as source-impossibility evidence only. All four target rows are single broker quote-state snapshots where `entry_touch` and `protective_level` are simultaneously true, and no approved current/local route exposes a sub-millisecond timestamp, monotonic quote-event ID, event sequence, or other source-safe intra-row ordering field. Proxy routes remain context only and cannot clear broker-native USDJPY same-tick sequence.

Exact remaining unblocker: Broker-native USDJPY quote-event stream or server-side quote log for 2026-04-20T00:15:04.153Z and 2026-05-01T00:30:00.083Z, carrying bid/ask plus sub-millisecond timestamp or monotonic quote-event sequence/event ID, with source hash/provenance and no account/order/history/deal/position labels.
