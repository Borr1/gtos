# Orderflow Event Window Fetch Plan

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Synthesis

This plan estimates or fetches trades-schema Databento windows from the GTOS orderflow event manifest. It is data acquisition plumbing, not an alpha or promotion claim.

## Cost

- Executed: False
- Blocked: False
- Total estimated cost USD: $0.474594
- Status counts: {'planned': 14}

## Groups

| Group | Status | Cost USD | Records | Output exists |
|---|---|---:|---:|---:|
| ofwin_0001 | planned | 0.001008 | 805 | False |
| ofwin_0002 | planned | 0.008254 | 6594 | False |
| ofwin_0003 | planned | 0.000956 | 764 | False |
| ofwin_0004 | planned | 0.008005 | 6395 | False |
| ofwin_0005 | planned | 0.034740 | 27754 | False |
| ofwin_0006 | planned | 0.005271 | 4211 | False |
| ofwin_0007 | planned | 0.027476 | 21951 | True |
| ofwin_0008 | planned | 0.028341 | 22642 | False |
| ofwin_0009 | planned | 0.123514 | 98677 | False |
| ofwin_0010 | planned | 0.090594 | 72377 | False |
| ofwin_0011 | planned | 0.005455 | 4358 | False |
| ofwin_0012 | planned | 0.000920 | 735 | False |
| ofwin_0013 | planned | 0.016605 | 13266 | False |
| ofwin_0014 | planned | 0.123456 | 98631 | False |

## Blockers

- None

## Ambiguity Ledger

- Cost estimates are vendor metadata values and may differ from final billing.
- Trades schema cannot reproduce full heatmap/depth visuals; depth pulls need a later gate.
- Cached files are treated as available raw inputs but are not revalidated unless force is used.

## Open Questions

1. After trades windows are fetched, which features survive candidate-versus-context diagnostics?
2. Are any event groups too sparse or truncated to use for orderflow inference?
3. Which subset, if any, justifies a depth-schema spend?

## Next Steps

1. Extract trades-level orderflow features for fetched windows.
2. Join features to GTOS event rows and synthetic/actual outcomes.
3. Register any structural hypothesis before testing a decision rule.
