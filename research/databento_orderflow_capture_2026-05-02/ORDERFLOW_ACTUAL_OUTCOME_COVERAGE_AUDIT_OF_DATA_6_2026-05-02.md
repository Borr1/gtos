# Orderflow Actual Outcome Coverage Audit

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Summary

This audit separates actual realized-R availability from synthetic/path outcome availability for the current orderflow candidate diagnostic sample.

## Coverage

- Candidate join rows loaded: 76
- Candidate join actual-R available total: 2
- Orderflow feature candidate rows: 23
- Orderflow synthetic target available: 13
- Orderflow actual realized-R available: 1
- Coverage class counts: {'actual_realized_r_available': 1, 'candidate_join_missing': 9, 'limit_placed_no_broker_close_in_join': 1, 'no_actual_by_design_pre_execution_reject': 12}
- Final outcome counts: {'LIMIT_PLACED': 2, 'REJECTED_GATE1_SAFETY': 1, 'REJECTED_L2': 11, 'none': 9}
- Record path status counts: {'exists': 14, 'no_path': 9}

## Readout

- Orderflow feature candidate rows have actual realized-R coverage 1/23; synthetic target coverage is 13/23.
- The actual-R blocker is mostly structural, not a parser miss: rejected candidates do not create broker exits.
- 1 orderflow rows were LIMIT_PLACED without actual R in the join; those are the only near-term broker-history enrichment targets.
- 12 orderflow rows were rejected before execution, so they can only be evaluated with synthetic/path labels.
- Depth/orderflow hypotheses should not be scored on actual realized R until forward collection or broker-history reconciliation expands coverage.

## By Symbol

| Symbol | n | synthetic target | actual R | coverage classes | final outcomes |
|---|---:|---:|---:|---|---|
| NAS100 | 12 | 11 | 1 | {'actual_realized_r_available': 1, 'candidate_join_missing': 1, 'no_actual_by_design_pre_execution_reject': 10} | {'LIMIT_PLACED': 1, 'REJECTED_L2': 10, 'none': 1} |
| US30 | 1 | 0 | 0 | {'no_actual_by_design_pre_execution_reject': 1} | {'REJECTED_L2': 1} |
| XAUUSD | 10 | 2 | 0 | {'candidate_join_missing': 8, 'limit_placed_no_broker_close_in_join': 1, 'no_actual_by_design_pre_execution_reject': 1} | {'LIMIT_PLACED': 1, 'REJECTED_GATE1_SAFETY': 1, 'none': 8} |

## Actual vs Synthetic Rows

| Symbol | Candle close UTC | synthetic R | actual R | actual - synthetic |
|---|---|---:|---:|---:|
| NAS100 | 2026-04-29T15:00:00+00:00 | -1.0000 | -1.0167 | -0.0167 |

## Ambiguity Ledger

- Synthetic/path R remains the only label for pre-execution rejects; this is not equivalent to broker realized R.
- Existing trade records prove actual-R extraction works when broker exits are reconciled, but coverage is sparse.
- LIMIT_PLACED rows without actual R may represent unfilled limits, still-open/missing close records, or absent broker-history backfill.
- Rejected CANDIDATE rows can still be useful for market-state diagnostics but cannot answer execution-quality questions.

## Open Questions

1. Can broker-history reconciliation recover additional LIMIT_PLACED rows in this orderflow subset?
2. How often do synthetic labels disagree with actual broker R once more actual rows are available?
3. Should forward orderflow research separate pre-execution filter diagnostics from executed-trade diagnostics?
4. Which depth/orderflow features explain rejected loser-like synthetic paths without overfitting to post-event data?

## Next Steps

1. Backfill broker-history actual R only for LIMIT_PLACED rows that lack actual R.
2. Keep rejected rows in a separate synthetic/path-outcome diagnostic bucket.
3. Do not promote any orderflow filter until actual-R coverage or pre-registered synthetic-label methodology is sufficient.
4. Use this audit to scope the first depth pilot to rows where outcome interpretation is least ambiguous.
