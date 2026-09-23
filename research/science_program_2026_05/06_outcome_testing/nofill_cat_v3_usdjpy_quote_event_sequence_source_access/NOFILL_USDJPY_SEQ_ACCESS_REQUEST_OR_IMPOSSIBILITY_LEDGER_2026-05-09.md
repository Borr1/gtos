# NOFILL USDJPY Sequence Access Request Or Impossibility Ledger

Promotion verdict: `NO_PROMOTION_VERDICT`.

All four rows are `SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES` under approved current sources.

Exact owner/source request:

- Provide a broker-native USDJPY quote-event stream or server-side quote log for the two decisive UTC instants: `2026-04-20T00:15:04.153Z` and `2026-05-01T00:30:00.083Z`.
- Required fields: bid, ask, event timestamp with sub-millisecond precision or a monotonic quote-event sequence/event ID, and source provenance/hash.
- Forbidden fields: account/order/history/deal/position labels, broker actual-R, live trade result, hidden labels, paid/API/Databento pulls unless a separate owner-approved lane authorizes them.
- If historical broker-native sequence cannot be exported, a prospective source-only USDJPY quote logger with a monotonic event counter can prevent future same-tick blockers but cannot retroactively clear these four rows.
