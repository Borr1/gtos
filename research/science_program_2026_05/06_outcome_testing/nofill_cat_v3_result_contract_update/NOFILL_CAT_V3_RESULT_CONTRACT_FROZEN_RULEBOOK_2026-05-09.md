# NOFILL CAT V3 Result Contract Frozen Rulebook - 2026-05-09

Promotion posture: `NO_PROMOTION_VERDICT`

Contract: `NOFILL_CAT_V3_QUARANTINED_CATEGORICAL_RESULT_CONTRACT_V1`

This contract freezes the future quarantined categorical scoring universe. It does not open the scoring lane.

## Frozen Universe

- Full V3 universe: `298` rows exactly once.
- Future scoring-eligible rows: `225` accepted input-only categorical rows.
- Excluded source-control rows: `NOFILL-CAT-ROW-0049`, `0050`, `0051`, `0241`.
- Excluded source-impossible rows: `NOFILL-CAT-ROW-0130`, `0143`, `0165`, `0178`.
- Excluded reject rows: `65`.

## Consumption Rule

A future scorer may consume only `NOFILL_CAT_V3_RESULT_CONTRACT_ELIGIBILITY_LEDGER_2026-05-09.jsonl`. It may read the exclusion ledger only to prove non-denominator rows stayed excluded.

## Methodology Boundary

Categorical counts are allowed only in a future lane after G12 acceptance. R, win rate, expectancy, DSR/PBO performance, broker actual-R, account history, live order/deal/position labels, validation, promotion, and live effect remain forbidden.
