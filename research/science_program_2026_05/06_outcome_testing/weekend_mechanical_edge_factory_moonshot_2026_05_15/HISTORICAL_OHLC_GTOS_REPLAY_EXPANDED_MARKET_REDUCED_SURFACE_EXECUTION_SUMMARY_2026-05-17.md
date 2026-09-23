# Expanded-Market Reduced Surface Execution

This checkpoint materializes reduced leakage predicates as executable branch-local surfaces and executes them against held selection rows.

## Counts

- Input leakage-reduction rows: `1748`
- Input leakage-reduction match rows: `9266`
- Input implementation-selection rows: `22610`
- Reduced surface rows: `1748`
- Self-test rows: `1748`
- Execution rows: `1748`
- Execution match rows: `9266`
- Aggregate rows: `231`
- Execution pass rows: `1748`
- Execution repair rows: `0`

## Decisions

`{"IMPLEMENT_EXPANDED_MARKET_REDUCED_SURFACE_EXECUTION": 1748}`

## Continuation

Collapse passing reduced executions into row-level branch-local implementation candidates with replay geometry preserved.
