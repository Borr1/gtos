# Orderflow Event Window Fetch Plan

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Synthesis

This plan estimates or fetches mbo-schema Databento windows from the GTOS orderflow event manifest. It is data acquisition plumbing, not an alpha or promotion claim.

## Cost

- Executed: False
- Blocked: False
- Total estimated cost USD: $1.889027
- Status counts: {'planned': 14}

## Groups

| Group | Status | Cost USD | Records | Output exists |
|---|---|---:|---:|---:|
| ofwin_0001 | planned | 0.005248 | 55898 | False |
| ofwin_0002 | planned | 0.037631 | 400856 | False |
| ofwin_0003 | planned | 0.005454 | 58102 | False |
| ofwin_0004 | planned | 0.042396 | 451607 | False |
| ofwin_0005 | planned | 0.103814 | 1105847 | False |
| ofwin_0006 | planned | 0.013783 | 146818 | False |
| ofwin_0007 | planned | 0.078414 | 835278 | False |
| ofwin_0008 | planned | 0.141569 | 1508023 | False |
| ofwin_0009 | planned | 0.582337 | 6203169 | False |
| ofwin_0010 | planned | 0.456498 | 4862706 | False |
| ofwin_0011 | planned | 0.026644 | 283817 | False |
| ofwin_0012 | planned | 0.009263 | 98676 | False |
| ofwin_0013 | planned | 0.076648 | 816473 | False |
| ofwin_0014 | planned | 0.309328 | 3295021 | False |

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
