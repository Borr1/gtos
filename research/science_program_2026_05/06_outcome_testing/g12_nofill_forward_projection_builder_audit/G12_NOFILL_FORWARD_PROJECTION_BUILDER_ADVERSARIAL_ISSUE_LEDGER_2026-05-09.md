# G12 NOFILL Forward Projection Builder Adversarial Issue Ledger 2026-05-09

Promotion posture: `NO_PROMOTION_VERDICT`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

- `G12-PROJ-BLOCKER-001` BLOCKING_VERIFICATION_FAILURE: The upstream projection verifier crashes on main after mandatory LIVE_STATE regeneration.
- `G12-PROJ-BLOCKER-002` BLOCKING_CONTRACT_GAP: The projection allowlist spec is not exhaustive: projection rows emit fields outside the declared allowed field sets.
- `G12-PROJ-WARN-001` NONBLOCKING_SEMANTIC_TIGHTENING: Entry-touch spread null semantics are disambiguated by entry_touch_spread_status but collapsed to SOURCE_FIELD_MISSING in missing_statuses for TOUCH_NOT_OBSERVED rows.
