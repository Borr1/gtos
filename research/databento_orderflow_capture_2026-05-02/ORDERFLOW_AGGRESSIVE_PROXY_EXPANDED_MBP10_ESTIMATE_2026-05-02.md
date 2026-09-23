# Orderflow Event Window Fetch Plan

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Synthesis

This plan estimates or fetches mbp-10-schema Databento windows from the GTOS orderflow event manifest. It is data acquisition plumbing, not an alpha or promotion claim.

## Cost

- Executed: False
- Blocked: False
- Total estimated cost USD: $14.357662
- Status counts: {'planned': 25}

## Groups

| Group | Status | Cost USD | Records | Output exists |
|---|---|---:|---:|---:|
| ofwin_0001 | planned | 0.016503 | 96307 | False |
| ofwin_0002 | planned | 0.098794 | 576515 | False |
| ofwin_0003 | planned | 0.099533 | 580831 | False |
| ofwin_0004 | planned | 0.059417 | 346731 | False |
| ofwin_0005 | planned | 0.194788 | 1136697 | True |
| ofwin_0006 | planned | 0.000000 | 0 | False |
| ofwin_0007 | planned | 0.033405 | 194937 | False |
| ofwin_0008 | planned | 0.115051 | 671386 | True |
| ofwin_0009 | planned | 0.366172 | 2136814 | True |
| ofwin_0010 | planned | 2.388071 | 13935718 | True |
| ofwin_0011 | planned | 0.299401 | 1747168 | False |
| ofwin_0012 | planned | 1.723868 | 10059722 | True |
| ofwin_0013 | planned | 2.458803 | 14348477 | False |
| ofwin_0014 | planned | 0.070375 | 410678 | False |
| ofwin_0015 | planned | 0.021289 | 124233 | False |
| ofwin_0016 | planned | 0.112237 | 654964 | False |
| ofwin_0017 | planned | 0.079827 | 465836 | False |
| ofwin_0018 | planned | 1.420021 | 8286608 | False |
| ofwin_0019 | planned | 0.152290 | 888694 | False |
| ofwin_0020 | planned | 1.278409 | 7460226 | False |
| ofwin_0021 | planned | 0.167361 | 976646 | False |
| ofwin_0022 | planned | 1.006802 | 5875245 | False |
| ofwin_0023 | planned | 1.298328 | 7576463 | False |
| ofwin_0024 | planned | 0.072373 | 422335 | False |
| ofwin_0025 | planned | 0.824544 | 4811673 | False |

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
