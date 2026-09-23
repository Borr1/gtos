# NOFILL CAT V2 Learning Ledger

Promotion posture: `NO_PROMOTION_VERDICT`.

## What V2 Adds

- Carries forward 52 prior accepted `nofill_terminal_before_entry` rows.
- Consumes 173 G12-accepted source-corrected input rows without opening performance outcomes.
- Converts the prior 246 blocked-row mass into 173 accepted inputs, 8 exact blockers, and 65 noncountable rejects.

## Residual Blocker Learning

- OTI3 same-tick blockers need source-safe intra-tick ordering; the current source proves ambiguity, not a label.
- OTI4 May 3 source gaps need read-only tick or M1/lower OHLC coverage for the frozen opening range.
- The original OTI2 source gap remains blocked until side-aware tick confirmation and active-window coverage exist.

## Reject Learning

- The 26 OTI4 contract-excluded rows are not denominator evidence because the opening-drive contract excludes them.
- The 39 OTI5 repeated projections are noncanonical duplicates and would inflate the denominator if counted.
