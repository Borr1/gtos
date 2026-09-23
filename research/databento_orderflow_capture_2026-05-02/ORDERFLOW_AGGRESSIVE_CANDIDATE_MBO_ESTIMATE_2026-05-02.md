# Orderflow Event Window Fetch Plan

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Synthesis

This plan estimates or fetches mbo-schema Databento windows from the GTOS orderflow event manifest. It is data acquisition plumbing, not an alpha or promotion claim.

## Cost

- Executed: False
- Blocked: False
- Total estimated cost USD: $2.580502
- Status counts: {'planned': 13}

## Groups

| Group | Status | Cost USD | Records | Output exists |
|---|---|---:|---:|---:|
| ofwin_0001 | planned | 0.006990 | 74464 | False |
| ofwin_0002 | planned | 0.048930 | 521216 | False |
| ofwin_0003 | planned | 0.056471 | 601542 | False |
| ofwin_0004 | planned | 0.131990 | 1405988 | False |
| ofwin_0005 | planned | 0.019847 | 211411 | False |
| ofwin_0006 | planned | 0.094609 | 1007795 | False |
| ofwin_0007 | planned | 0.175644 | 1870990 | False |
| ofwin_0008 | planned | 0.878463 | 9357564 | False |
| ofwin_0009 | planned | 0.626640 | 6675100 | False |
| ofwin_0010 | planned | 0.039772 | 423664 | False |
| ofwin_0011 | planned | 0.011693 | 124553 | False |
| ofwin_0012 | planned | 0.081023 | 863073 | False |
| ofwin_0013 | planned | 0.408429 | 4350664 | False |

## Blockers

- None

## Ambiguity Ledger

- Cost estimates are vendor metadata values and may differ from final billing.
- mbo schema limitations must be documented before using it for inference.
- Cached files are treated as available raw inputs but are not revalidated unless force is used.

## Open Questions

1. After trades windows are fetched, which features survive candidate-versus-context diagnostics?
2. Are any event groups too sparse or truncated to use for orderflow inference?
3. Which subset, if any, justifies a depth-schema spend?

## Next Steps

1. Extract trades-level orderflow features for fetched windows.
2. Join features to GTOS event rows and synthetic/actual outcomes.
3. Register any structural hypothesis before testing a decision rule.
