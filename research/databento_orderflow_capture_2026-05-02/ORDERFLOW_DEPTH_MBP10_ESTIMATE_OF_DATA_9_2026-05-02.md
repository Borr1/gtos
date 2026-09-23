# Orderflow Event Window Fetch Plan

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Summary

This plan estimates or fetches mbp-10-schema Databento windows from the GTOS orderflow event manifest. It is data acquisition plumbing, not an alpha or promotion claim.

## Cost

- Executed: True
- Blocked: False
- Total estimated cost USD: $4.672899
- Status counts: {'fetched': 4}

## Groups

| Group | Status | Cost USD | Records | Output exists |
|---|---|---:|---:|---:|
| ofwin_0002 | fetched | 0.194788 | 1136697 | True |
| ofwin_0006 | fetched | 0.366172 | 2136814 | True |
| ofwin_0007 | fetched | 2.388071 | 13935718 | True |
| ofwin_0009 | fetched | 1.723868 | 10059722 | True |

## Blockers

- None

## Ambiguity Ledger

- Cost estimates are vendor metadata values and may differ from final billing.
- MBP-10 schema exposes top ten book levels, but not full order identity, queue position, or complete MBO reconstruction.
- Cached files are treated as available raw inputs but are not revalidated unless force is used.

## Open Questions

1. After MBP-10 windows are fetched, which ladder features survive candidate-versus-context diagnostics?
2. Are any event groups too sparse or truncated to use for orderflow inference?
3. Which subset, if any, justifies a depth-schema spend?

## Next Steps

1. Extract sampled MBP-10 ladder-depth features for fetched windows.
2. Join features to GTOS event rows and synthetic/actual outcomes.
3. Register any structural hypothesis before testing a decision rule.
