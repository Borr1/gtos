# Next G12 Acceptance Prompt Pack

Run an independent G12 acceptance audit of the additive NOFILL forward source-capture logger implementation package.

Required checks:

1. Recompute the 55-field contract from accepted design artifacts and runtime constants.
2. Confirm all 20 future logger fields are emitted or fail-closed with accepted vocabulary.
3. Confirm forbidden/redacted fields are status-only and no raw value or raw-value hash leaks.
4. Confirm writer is fail-open and no return value is consumed by trading decisions.
5. Confirm diff scope excludes prompts, config, risk, permissions, safety, selectors, canaries, MT5 order/account/history/deal/position behavior, registry, paid/API, remote, scoring, validation, and promotion.
6. Run the implementation verifier and focused tests.
7. Preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false.

Terminal verdict may only be ACCEPT_AS_SOURCE_CONTROL_IMPLEMENTATION_EVIDENCE_ONLY or an exact repair blocker list.
