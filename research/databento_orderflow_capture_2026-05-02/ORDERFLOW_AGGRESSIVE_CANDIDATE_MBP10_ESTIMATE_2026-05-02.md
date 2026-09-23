# Orderflow Event Window Fetch Plan

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Synthesis

This plan estimates or fetches mbp-10-schema Databento windows from the GTOS orderflow event manifest. It is data acquisition plumbing, not an alpha or promotion claim.

## Cost

- Executed: False
- Blocked: False
- Total estimated cost USD: $3.957062
- Status counts: {'planned': 13}

## Groups

| Group | Status | Cost USD | Records | Output exists |
|---|---|---:|---:|---:|
| ofwin_0001 | planned | 0.011943 | 69695 | False |
| ofwin_0002 | planned | 0.083219 | 485630 | False |
| ofwin_0003 | planned | 0.095698 | 558453 | False |
| ofwin_0004 | planned | 0.194788 | 1136697 | True |
| ofwin_0005 | planned | 0.029858 | 174237 | False |
| ofwin_0006 | planned | 0.136517 | 796655 | False |
| ofwin_0007 | planned | 0.281287 | 1641467 | False |
| ofwin_0008 | planned | 1.370484 | 7997534 | False |
| ofwin_0009 | planned | 0.958908 | 5595761 | False |
| ofwin_0010 | planned | 0.063368 | 369788 | False |
| ofwin_0011 | planned | 0.018835 | 109911 | False |
| ofwin_0012 | planned | 0.128242 | 748363 | False |
| ofwin_0013 | planned | 0.583913 | 3407453 | False |

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
