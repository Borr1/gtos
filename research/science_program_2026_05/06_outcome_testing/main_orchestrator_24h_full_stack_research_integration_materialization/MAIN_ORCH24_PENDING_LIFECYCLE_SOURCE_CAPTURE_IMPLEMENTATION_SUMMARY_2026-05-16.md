# Pending Lifecycle Source Capture Integration

Generated: `2026-05-16T14:40:58+00:00`
Implementation commit: `f54a0e0989a6b983a485cde660ad0a1f133985c9 research: enrich pending lifecycle source capture`

This plate converts the live/shadow legacy decision `UPGRADE_CAPTURE_CONTRACT_NOT_SCORE_ROWS` into an additive pending-limit lifecycle source-capture improvement.

It adds forward source-safe fields for pending horizon, cancel/expiry reason status, decision and entry-touch spread, terminal/protective area touch status, event-order resolution method, and same-tick/same-bar ambiguity status.

No trade placement, AI prompt, risk, selector, safety gate, broker operation, promotion, validation-safe claim, or live-effect change is opened.

Verification recorded: `ast_parse_ok`; focused pytest with repo-local temp and cache disabled: `31 passed in 5.07s`.
