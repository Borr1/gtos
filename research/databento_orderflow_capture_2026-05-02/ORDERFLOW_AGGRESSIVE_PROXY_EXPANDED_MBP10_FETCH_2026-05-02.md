# Orderflow Event Window Fetch Plan

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Synthesis

This plan estimates or fetches mbp-10-schema Databento windows from the GTOS orderflow event manifest. It is data acquisition plumbing, not an alpha or promotion claim.

## Cost

- Executed: True
- Blocked: False
- Total estimated cost USD: $14.357662
- Status counts: {'fetched': 20, 'cached': 5}

## Groups

| Group | Status | Cost USD | Records | Output exists |
|---|---|---:|---:|---:|
| ofwin_0001 | fetched | 0.016503 | 96307 | True |
| ofwin_0002 | fetched | 0.098794 | 576515 | True |
| ofwin_0003 | fetched | 0.099533 | 580831 | True |
| ofwin_0004 | fetched | 0.059417 | 346731 | True |
| ofwin_0005 | cached | 0.194788 | 1136697 | True |
| ofwin_0006 | fetched | 0.000000 | 0 | True |
| ofwin_0007 | fetched | 0.033405 | 194937 | True |
| ofwin_0008 | cached | 0.115051 | 671386 | True |
| ofwin_0009 | cached | 0.366172 | 2136814 | True |
| ofwin_0010 | cached | 2.388071 | 13935718 | True |
| ofwin_0011 | fetched | 0.299401 | 1747168 | True |
| ofwin_0012 | cached | 1.723868 | 10059722 | True |
| ofwin_0013 | fetched | 2.458803 | 14348477 | True |
| ofwin_0014 | fetched | 0.070375 | 410678 | True |
| ofwin_0015 | fetched | 0.021289 | 124233 | True |
| ofwin_0016 | fetched | 0.112237 | 654964 | True |
| ofwin_0017 | fetched | 0.079827 | 465836 | True |
| ofwin_0018 | fetched | 1.420021 | 8286608 | True |
| ofwin_0019 | fetched | 0.152290 | 888694 | True |
| ofwin_0020 | fetched | 1.278409 | 7460226 | True |
| ofwin_0021 | fetched | 0.167361 | 976646 | True |
| ofwin_0022 | fetched | 1.006802 | 5875245 | True |
| ofwin_0023 | fetched | 1.298328 | 7576463 | True |
| ofwin_0024 | fetched | 0.072373 | 422335 | True |
| ofwin_0025 | fetched | 0.824544 | 4811673 | True |

## Blockers

- None

## Ambiguity Ledger

- Cost estimates are vendor metadata values and may differ from final billing.
- MBP-10 schema exposes top ten book levels, but not full order identity, queue position, or complete MBO reconstruction.
- Cached files are treated as available raw inputs but are not revalidated unless force is used.

## Open Questions

1. After trades windows are fetched, which features survive candidate-versus-context diagnostics?
2. Are any event groups too sparse or truncated to use for orderflow inference?
3. Which subset, if any, justifies a depth-schema spend?

## Next Steps

1. Extract trades-level orderflow features for fetched windows.
2. Join features to GTOS event rows and synthetic/actual outcomes.
3. Register any structural hypothesis before testing a decision rule.
