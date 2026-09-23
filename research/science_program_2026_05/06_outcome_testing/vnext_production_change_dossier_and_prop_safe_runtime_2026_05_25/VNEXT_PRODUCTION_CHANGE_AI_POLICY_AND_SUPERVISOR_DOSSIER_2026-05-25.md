# vNext Production Change Stage07 AI Policy And Supervisor Dossier

Created: 2026-05-25T09:15:33.221339Z

## Stage07 Runtime Change

- Added a mechanical-first vNext AI policy decision surface.
- Mechanical AVOID produces `SKIP_AI_MECHANICAL_AVOID`; current config keeps it shadowed by `ai_policy_apply_to_ai_call=false`.
- FOLLOW routes use a constrained validator by default; optional no-AI follow remains gated by config and risk tier.
- NARROW routes call AI only inside the selected side/framework/route-family scope.
- MIXED routes call AI only when source-bound prompt fields are present.
- LEGACY broad fallback is blocked when active unless an explicit replayed scope is present.
- Prompt packets carry deterministic SHA-256 hashes and a schema/cache contract; no paid API call is made by this harness.

## Evidence Consumed

- Stage07 decision-surface groups: 127.
- Stage07 decision-map rows: 627.
- Runtime surfaces: {"legacy_no_match_non_override_guard": 3, "pending_policy_nofill_limit_market_selector": 12, "pre_ai_route_selector_and_ai_narrowing": 88, "risk_adjustment_and_prop_safe_selector": 12, "route_decision_scorer_filter_router": 12}.
- Source components: {"l2_sl_beyond_ob_rejection_value": 2, "rejected_candidate_blocked_limit_value": 16, "rejected_candidate_c1_failed_value": 51, "rejected_candidate_c3_direction_mismatch_value": 6, "rejected_candidate_ob_proximity_value": 14, "rejected_candidate_other_unknown_value": 6, "rejected_candidate_prescreen_no_direction_value": 18, "unknown_component": 14}.
- Implementation decisions: {"KEEP_SHADOW": 42, "KEEP_SHADOW_OR_GUARD_ONLY": 25, "KILL_OR_REDESIGN_BEFORE_USE": 22, "PROMOTE_TO_PRODUCTION_CHANGE_DOSSIER": 38}.

## No-Paid-Call Harness

- Runtime scenario rows: 8.
- Action counts: {"BLOCK_LEGACY_BROAD_FALLBACK": 1, "CALL_AI_CONSTRAINED_VALIDATOR": 1, "CALL_AI_CURRENT_PATH": 2, "CALL_AI_LEGACY_REPLAYED": 1, "CALL_AI_MIXED_RESOLUTION": 1, "CALL_AI_NARROWED_ROUTE": 1, "SKIP_AI_MECHANICAL_AVOID": 1}.
- Would-action counts: {"BLOCK_LEGACY_BROAD_FALLBACK": 1, "CALL_AI_CONSTRAINED_VALIDATOR": 1, "CALL_AI_LEGACY_REPLAYED": 1, "CALL_AI_MIXED_RESOLUTION": 1, "CALL_AI_NARROWED_ROUTE": 1, "MECHANICAL_FOLLOW_NO_AI": 1, "SKIP_AI_MECHANICAL_AVOID": 2}.
- Prompt packet hashes: 8 unique for 8 packets.
- Schema/parser fixtures: 4 with parsed counts {"False": 2, "True": 2}.

## Supervisor Boundary

- Stage08 still owns the always-on AI supervisor implementation.
- Stage07 only creates the explicit policy contract, prompt-packet/hash harness, and parser fixtures consumed by that supervisor.
- No live trading, broker mutation, paid API/vendor call, source deletion, remote push, or activation flip is performed.
