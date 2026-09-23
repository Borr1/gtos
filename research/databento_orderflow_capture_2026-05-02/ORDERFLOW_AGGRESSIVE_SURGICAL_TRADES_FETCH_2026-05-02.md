# Orderflow Event Window Fetch Plan

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Synthesis

This plan estimates or fetches trades-schema Databento windows from the GTOS orderflow event manifest. It is data acquisition plumbing, not an alpha or promotion claim.

## Cost

- Executed: True
- Blocked: False
- Total estimated cost USD: $0.474594
- Status counts: {'fetched': 13, 'cached': 1}

## Groups

| Group | Status | Cost USD | Records | Output exists |
|---|---|---:|---:|---:|
| ofwin_0001 | fetched | 0.001008 | 805 | True |
| ofwin_0002 | fetched | 0.008254 | 6594 | True |
| ofwin_0003 | fetched | 0.000956 | 764 | True |
| ofwin_0004 | fetched | 0.008005 | 6395 | True |
| ofwin_0005 | fetched | 0.034740 | 27754 | True |
| ofwin_0006 | fetched | 0.005271 | 4211 | True |
| ofwin_0007 | cached | 0.027476 | 21951 | True |
| ofwin_0008 | fetched | 0.028341 | 22642 | True |
| ofwin_0009 | fetched | 0.123514 | 98677 | True |
| ofwin_0010 | fetched | 0.090594 | 72377 | True |
| ofwin_0011 | fetched | 0.005455 | 4358 | True |
| ofwin_0012 | fetched | 0.000920 | 735 | True |
| ofwin_0013 | fetched | 0.016605 | 13266 | True |
| ofwin_0014 | fetched | 0.123456 | 98631 | True |

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
