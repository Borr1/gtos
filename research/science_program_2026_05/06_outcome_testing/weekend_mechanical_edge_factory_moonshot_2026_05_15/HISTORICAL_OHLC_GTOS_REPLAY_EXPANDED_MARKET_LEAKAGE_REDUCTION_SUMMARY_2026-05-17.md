# Expanded-Market Leakage Reduction

This checkpoint narrows code-candidate execution leakage with source path/hash and replay-performance thresholds.

## Counts

- Input code-candidate execution rows: `1748`
- Input code-candidate rows: `1748`
- Input implementation-selection rows: `22610`
- Leakage-reduction rows: `1748`
- Leakage-reduction match rows: `9266`
- Aggregate rows: `231`
- Preserved execution-pass rows: `24`
- Reduced execution-pass rows: `1724`
- Remaining repair rows: `0`

## Decisions

`{"IMPLEMENT_EXPANDED_MARKET_CODE_CANDIDATE_EXECUTION_PRESERVED": 24, "IMPLEMENT_EXPANDED_MARKET_LEAKAGE_REDUCED_CODE_CANDIDATE": 1724}`

## Continuation

Consume reduced and preserved rows into concrete branch-local execution surfaces or terminal redesign evidence.
