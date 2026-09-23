# G12 NOFILL Forward Projection Builder Context Anchor 2026-05-09

Promotion posture: `NO_PROMOTION_VERDICT`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Scope

Independent G12 red-team acceptance audit of the merged NOFILL forward source-safe projection builder.
This audit is source/control only. It does not score outcomes, compute R/win-rate/expectancy/DSR/PBO, validate,
promote, wire live loggers, edit registries, call paid/API/Databento, or touch live trading behavior.

## Current Decision

Terminal verdict: `BLOCK_ACCEPTANCE_PENDING_EXACT_REPAIR`.

Accepted evidence after repair: universe/denominator recomputation `PASS`, source/hash/no-leak audit `PASS_WITH_CONTRACT_GAPS`, local-heavy audit `PASS`.

## Active Issues

- `G12-PROJ-BLOCKER-001` BLOCKING_VERIFICATION_FAILURE: The upstream projection verifier crashes on main after mandatory LIVE_STATE regeneration.
- `G12-PROJ-BLOCKER-002` BLOCKING_CONTRACT_GAP: The projection allowlist spec is not exhaustive: projection rows emit fields outside the declared allowed field sets.
- `G12-PROJ-WARN-001` NONBLOCKING_SEMANTIC_TIGHTENING: Entry-touch spread null semantics are disambiguated by entry_touch_spread_status but collapsed to SOURCE_FIELD_MISSING in missing_statuses for TOUCH_NOT_OBSERVED rows.
