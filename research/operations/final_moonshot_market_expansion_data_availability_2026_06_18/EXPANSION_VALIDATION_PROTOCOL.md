# Market Expansion Validation Protocol

Status: availability and preregistration protocol, not live expansion authority.

## Boundary

- Allowed data: localhost Docker MT5 bridge read-only symbol info, OHLCV, and tick-volume columns; existing local exports.
- Forbidden data: orderflow/depth, broker order/deal/position/account mutation, credentials, remotes, VPS process mutation, paid APIs.
- Runtime effect: none. The full candidate book remains armed by commit `709aabfc8`; this route does not change config.

## Current Inventory

- Bridge-native symbols: `167`.
- Families discovered: `12`.
- Validation-ready symbols: `164`.
- Research-only or export-needed symbols: `3`.
- Coverage gap rows: `0`.

## Protocol

Data availability is only the first gate.

1. Keep every market family in the priority ledger; do not cap to a top-N summary.
2. Use symbol-info/spec/spread plus D1/H4/H1/M15/M1 OHLCV/tick-volume only.
3. Treat data availability as input readiness, not performance proof.
4. For any candidate family, freeze source window and aliases before scoring.
5. Run no-leak/as-of replay, cost stress, spread sensitivity, null/placebo, per-year/per-symbol splits, concentration checks, and full-book MC before any live expansion claim.
6. Keep NATGAS and HEATOIL hard-dropped unless a separate cost/limit-entry repair route revives them.

## Safe Export Commands

These are exact examples from the coverage-gap ledger; run more rows from `COVERAGE_GAP_LEDGER.jsonl` as needed.

- No current gaps found for bridge-native symbols in the scanned local export corpus.
