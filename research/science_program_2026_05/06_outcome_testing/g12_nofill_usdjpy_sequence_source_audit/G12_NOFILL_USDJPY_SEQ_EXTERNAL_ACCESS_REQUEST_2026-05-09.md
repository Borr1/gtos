# G12 NOFILL USDJPY Sequence External Access Request - 2026-05-09

Promotion verdict: `NO_PROMOTION_VERDICT`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Exact Request

Provide a broker-native USDJPY quote-event stream or server-side quote log for these exact timestamps:

- `2026-04-20T00:15:04.153Z`
- `2026-05-01T00:30:00.083Z`

Required fields:

- broker-native bid and ask per quote event;
- sub-millisecond timestamp or monotonic quote-event sequence/event ID;
- source provenance and SHA256/hashable raw export;
- enough surrounding rows to verify ordering before/after the decisive update;
- no account, order, history, deal, position, PnL, actual-R, fill, or live-trade result labels.

## Why It Is Needed

Broker-native USDJPY quote-event stream or server-side quote log for 2026-04-20T00:15:04.153Z and 2026-05-01T00:30:00.083Z, carrying bid/ask plus sub-millisecond timestamp or monotonic quote-event sequence/event ID, with source hash/provenance and no account/order/history/deal/position labels.

Prospective source-only logging can prevent future blockers, but it cannot retro-clear these four historical rows unless the broker/native server log covers the exact timestamps above.
