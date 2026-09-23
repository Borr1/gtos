# Orderflow Event Window Fetch Plan

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Synthesis

This plan estimates or fetches mbp-10-schema Databento windows from the GTOS orderflow event manifest. It is data acquisition plumbing, not an alpha or promotion claim.

## Cost

- Executed: False
- Blocked: False
- Total estimated cost USD: $2.903098
- Status counts: {'planned': 14}

## Groups

| Group | Status | Cost USD | Records | Output exists |
|---|---|---:|---:|---:|
| ofwin_0001 | planned | 0.008977 | 52384 | False |
| ofwin_0002 | planned | 0.064019 | 373589 | False |
| ofwin_0003 | planned | 0.009290 | 54213 | False |
| ofwin_0004 | planned | 0.071574 | 417676 | False |
| ofwin_0005 | planned | 0.153442 | 895417 | False |
| ofwin_0006 | planned | 0.020658 | 120548 | False |
| ofwin_0007 | planned | 0.115051 | 671386 | False |
| ofwin_0008 | planned | 0.226985 | 1324585 | False |
| ofwin_0009 | planned | 0.912456 | 5324685 | False |
| ofwin_0010 | planned | 0.696604 | 4065068 | False |
| ofwin_0011 | planned | 0.042322 | 246970 | False |
| ofwin_0012 | planned | 0.014943 | 87200 | False |
| ofwin_0013 | planned | 0.121247 | 707542 | False |
| ofwin_0014 | planned | 0.445531 | 2599918 | False |

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
