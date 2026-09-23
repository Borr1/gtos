# G12 NOFILL USDJPY Sequence Next Prompt Pack - 2026-05-09

Promotion verdict: `NO_PROMOTION_VERDICT`.

Next route status: `WAIT_FOR_EXACT_BROKER_NATIVE_QUOTE_EVENT_SOURCE`.

If the owner obtains the requested source, run a new source-access lane only. Inputs must be the broker-native USDJPY quote-event stream/server-side quote log with source hash/provenance for `2026-04-20T00:15:04.153Z` and `2026-05-01T00:30:00.083Z`.

Allowed next work:

- verify source hash and schema;
- map quote events to the four target rows;
- decide whether each row clears as input-only source evidence or remains impossible;
- preserve exclusions until a separate G12/G0 source-control path accepts any change.

Forbidden next work:

- result scoring, validation, promotion, registry edits, live trading behavior, prompts, `src` trading logic, config/risk/execution/permission/safety/canary changes, broker account/order/history/deal/position labels, paid/API/Databento calls, credentials, or remote pushes.
