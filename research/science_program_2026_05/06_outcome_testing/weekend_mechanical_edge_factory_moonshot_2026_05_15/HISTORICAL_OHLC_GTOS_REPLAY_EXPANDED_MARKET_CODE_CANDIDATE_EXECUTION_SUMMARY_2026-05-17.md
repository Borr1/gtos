# Expanded-Market Code Candidate Execution

This checkpoint executes branch-local code candidates against held implementation-selection rows and preserves match evidence.

## Counts

- Input code-candidate rows: `1748`
- Input selection rows: `22610`
- Execution rows: `1748`
- Match rows: `46002`
- Aggregate rows: `231`
- Execution pass rows: `24`
- Execution repair rows: `1724`

## Decisions

`{"IMPLEMENT_EXPANDED_MARKET_CODE_CANDIDATE_EXECUTION": 24, "REDESIGN_EXPANDED_MARKET_CODE_CANDIDATE_SCOPE_LEAKAGE": 1724}`

## Continuation

Reduce leakage rows into narrower branch-local code candidates or preserve them as redesign evidence.
