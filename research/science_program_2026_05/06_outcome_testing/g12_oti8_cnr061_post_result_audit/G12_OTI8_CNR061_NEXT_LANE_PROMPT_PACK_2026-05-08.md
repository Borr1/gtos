# G12 OTI8 CNR061 Next Lane Prompt Pack - 2026-05-08

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

## Decision Anchor

G12 accepts OTI8 only as quarantined discovery evidence. The accepted evidence is tiny and synthetic: exactly 8 row-level rows, 4 countable timing-family rows, 2 duplicate groups, 2 target-before-stop tiny residual wins, 6 no-terminal rows, and zero validation/promotion support.

## Prompt 1 - CNR Timing And Target Preregistration

`/goal Build CNR_E2_E3_E4_AND_CNR_T1_T2_T3_INPUT_ONLY_PREREG using OTI8/G12 OTI8 as learning context; freeze timing fields, target contracts, quote-side policy, duplicate denominator policy, source hashes, no-leak rules, and sample floors before any outcome opening; keep NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false; do not score blocked rows, broker actual-R, account history, live order state, or hidden labels; produce prereg, source contract, no-leak, duplicate, and completion artifacts plus verifier/tests.`

## Prompt 2 - CNR061 No-Terminal Lifecycle Timebox Packet

`/goal Build CNR061_NO_TERMINAL_TIMEBOX_LIFECYCLE_INPUT_PACKET for the six OTI8 no-terminal rows only; extend source-hashed ordered tick/lifecycle observation beyond the frozen four-hour horizon without using broker/account/live labels; define terminal/timebox labels before reading outcomes; preserve the exact OTI8 duplicate policy; output packet/source/no-leak/duplicate/blocker artifacts and stop before result scoring unless separately authorized.`

## Prompt 3 - XAGUSD Residual Target Mechanism Forensics

`/goal Run XAGUSD_CNR_RESIDUAL_TARGET_FORENSICS as discovery-only source-safe analysis; inspect residual_target_r_from_executable_quote bins, no-terminal behavior, session/timing-family differences, and original-TP1 tiny-target pathology using only accepted source-safe rows; do not invent rescue thresholds or live gates; produce mechanism report, exact blocker ledger, preregistered next hypotheses, and verifier/tests under NO_PROMOTION_VERDICT.`

## Forbidden Until Separate Approval

- Scoring any of the 94 G12-blocked CNR061 rows.
- Using broker actual-R, account history, live trade results, live order state, or hidden path labels.
- Promoting CNR061, changing selectors, prompts, risk, execution, permissions, safety gates, canaries, MT5 order behavior, credentials, or remotes.
- Treating OTI8's +0.054478301R target rows as material edge evidence.
