# Next Prompt Pack - NOFILL Forward Source-Capture Implementation Lane

Use only after independent G12 acceptance of this design package and explicit owner approval for additive logger code wiring.

Objective: implement the source-safe NOFILL forward source-capture parser, fixtures, verifier, and additive shadow logger writer for the accepted 55-field contract.

Mandatory boundaries: preserve NO_PROMOTION_VERDICT; keep validation_safe=false, outcome_review_opened=false, live_effect=false; do not open scoring, validation, promotion, registry edit, paid/API route, remote push, or live decision behavior.

Required implementation order:

1. Re-run GTOS preflight and read this design package.
2. Implement offline parser and fixtures first.
3. Run verifier against fixture rows and existing source logs.
4. Only after owner approval, add fail-open additive writer calls with no return value consumed by trading decisions.
5. Run focused tests, no-leak scan, hash manifest rebuild, and independent G12 acceptance package.

Completion requires exact 55-field projection rows, source hashes, redaction proof, rollback proof, and no forbidden live-surface change.
