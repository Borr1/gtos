# Orderflow Event Window Fetch Plan

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Summary

This plan estimates or fetches mbp-1-schema Databento windows from the GTOS orderflow event manifest. It is data acquisition plumbing, not an alpha or promotion claim.

## Cost

- Executed: True
- Blocked: False
- Total estimated cost USD: $2.279908
- Status counts: {'fetched': 4}

## Groups

| Group | Status | Cost USD | Records | Output exists |
|---|---|---:|---:|---:|
| ofwin_0002 | fetched | 0.088294 | 658371 | True |
| ofwin_0006 | fetched | 0.162864 | 1214399 | True |
| ofwin_0007 | fetched | 1.185859 | 8842404 | True |
| ofwin_0009 | fetched | 0.842892 | 6285055 | True |

## Blockers

- None

## Ambiguity Ledger

- Cost estimates are vendor metadata values and may differ from final billing.
- MBP-1 schema exposes top-of-book updates only; full heatmap/depth ladder reconstruction would need deeper book or MBO pulls.
- Cached files are treated as available raw inputs but are not revalidated unless force is used.

## Open Questions

1. After MBP-1 windows are fetched, which top-of-book features survive candidate-versus-context diagnostics?
2. Are any event groups too sparse or truncated to use for orderflow inference?
3. Which subset, if any, justifies a depth-schema spend?

## Next Steps

1. Extract MBP-1 top-of-book depth features for fetched windows.
2. Join features to GTOS event rows and synthetic/actual outcomes.
3. Register any structural hypothesis before testing a decision rule.
