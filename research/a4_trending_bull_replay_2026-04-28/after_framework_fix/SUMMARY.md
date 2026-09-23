# A4 Replay — Summary

## Cohort
- records: 11, successes: 11, errors: 0

## Decision-flip distribution
- CAND_to_CAND: 11

## Filtered subset (current emits CANDIDATE)
- n: 11
- LONG: 11, SHORT: 0
- by kill zone: {'ny': 9, 'london': 2}

## Token + cost
- input tokens: 25,397
- output tokens: 11,913
- cache_read tokens: 0
- cache_creation tokens: 142,854
- cumulative cost (Sonnet 4.6 pricing): $1.1120
- median elapsed: 20437 ms

## Verdict bands — REQUIRES OUT-OF-BAND REALIZED-R JOIN
Realized R for these candidates is NOT in the trade record
(`exit: null` per memory `project_trade_records_enrichment_gap`).
Use `_trade_index.json` + `trades_unified.csv` + filtered-subset
mapping post-hoc; this script alone yields decision-flip distribution
only. GREEN/YELLOW/RED bands cannot be evaluated until that join.

## Ten interesting flips (CANDIDATEs the current AI now demotes)
