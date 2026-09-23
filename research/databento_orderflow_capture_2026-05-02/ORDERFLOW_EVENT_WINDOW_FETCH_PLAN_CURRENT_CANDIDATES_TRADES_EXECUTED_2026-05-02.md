# Orderflow Event Window Fetch Plan

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Synthesis

This plan estimates or fetches trades-schema Databento windows from the GTOS orderflow event manifest. It is data acquisition plumbing, not an alpha or promotion claim.

## Cost

- Executed: True
- Blocked: False
- Total estimated cost USD: $0.635717
- Status counts: {'fetched': 12, 'cached': 1}

## Groups

| Group | Status | Cost USD | Records | Output exists |
|---|---|---:|---:|---:|
| ofwin_0001 | fetched | 0.001417 | 1132 | True |
| ofwin_0002 | fetched | 0.010806 | 8633 | True |
| ofwin_0003 | fetched | 0.010256 | 8194 | True |
| ofwin_0004 | cached | 0.044190 | 35304 | True |
| ofwin_0005 | fetched | 0.007556 | 6037 | True |
| ofwin_0006 | fetched | 0.031018 | 24781 | True |
| ofwin_0007 | fetched | 0.036432 | 29106 | True |
| ofwin_0008 | fetched | 0.173582 | 138677 | True |
| ofwin_0009 | fetched | 0.124306 | 99310 | True |
| ofwin_0010 | fetched | 0.008408 | 6717 | True |
| ofwin_0011 | fetched | 0.001185 | 947 | True |
| ofwin_0012 | fetched | 0.017808 | 14227 | True |
| ofwin_0013 | fetched | 0.168753 | 134819 | True |

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
