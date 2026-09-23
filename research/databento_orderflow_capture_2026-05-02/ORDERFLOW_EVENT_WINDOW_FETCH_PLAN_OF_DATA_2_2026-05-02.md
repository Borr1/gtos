# Orderflow Event Window Fetch Plan

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Summary

This plan estimates or fetches trades-schema Databento windows from the GTOS orderflow event manifest. It is data acquisition plumbing, not an alpha or promotion claim.

## Cost

- Executed: True
- Blocked: False
- Total estimated cost USD: $2.866733
- Status counts: {'cached': 20}

## Groups

| Group | Status | Cost USD | Records | Output exists |
|---|---|---:|---:|---:|
| ofwin_0001 | cached | 0.015897 | 12700 | True |
| ofwin_0002 | cached | 0.044190 | 35304 | True |
| ofwin_0003 | cached | 0.000000 | 0 | True |
| ofwin_0004 | cached | 0.008389 | 6702 | True |
| ofwin_0005 | cached | 0.027476 | 21951 | True |
| ofwin_0006 | cached | 0.048921 | 39084 | True |
| ofwin_0007 | cached | 0.318224 | 254234 | True |
| ofwin_0008 | cached | 0.033264 | 26575 | True |
| ofwin_0009 | cached | 0.225341 | 180028 | True |
| ofwin_0010 | cached | 0.312282 | 249487 | True |
| ofwin_0011 | cached | 0.009403 | 7512 | True |
| ofwin_0012 | cached | 0.025286 | 20201 | True |
| ofwin_0013 | cached | 0.439257 | 350929 | True |
| ofwin_0014 | cached | 0.039116 | 31250 | True |
| ofwin_0015 | cached | 0.352383 | 281524 | True |
| ofwin_0016 | cached | 0.035686 | 28510 | True |
| ofwin_0017 | cached | 0.279300 | 223137 | True |
| ofwin_0018 | cached | 0.360599 | 288088 | True |
| ofwin_0019 | cached | 0.019595 | 15655 | True |
| ofwin_0020 | cached | 0.272125 | 217405 | True |

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
