# B7.5 XAU Ordered-Tick Replacement-Value Proof

- Decision: `TERMINAL_TRUTH_GREEN_ESCALATE_FULL_PORTFOLIO`
- Causal disposition: `TERMINAL_TRUTH_GREEN_LIFECYCLE_NOT_EVALUATED_DUE_PRIOR_COST_BLOCK`
- Portfolio disposition: `ESCALATE_FULL_PORTFOLIO`
- Analysis valid: `true`
- Structural issues: `0`
- Evidence class: `bounded_xau_only_ordered_tick_local_replay`
- Full-portfolio economic claim authorized: `false`
- Policy change authorized: `false`
- Broker/live/final authority: `false / false / false`

## Exact candidate trace

| Surface | Time | Identity | Disposition | Scoreable | Net R | Cash |
|---|---|---|---|---:|---:|---:|
| baseline | 2026-06-04T07:30:00+00:00 | `broadorigin_27432b7392759e5a5dbe7658@@2026-06-04T07:30:00+00:00` | trade | False | None | None |
| baseline | 2026-06-04T07:45:00+00:00 | `broadorigin_730290b8b2d3fc07f83c9320@@2026-06-04T07:45:00+00:00` | missed | True | None | None |
| target | 2026-06-04T07:30:00+00:00 | `broadorigin_27432b7392759e5a5dbe7658@@2026-06-04T07:30:00+00:00` | trade | True | 1.0724184 | 670.2615 |
| target | 2026-06-04T07:45:00+00:00 | `broadorigin_730290b8b2d3fc07f83c9320@@2026-06-04T07:45:00+00:00` | missed | True | None | None |

## Ordered-tick terminal proof

- Contract valid: `true`
- Outcome: `target_reached_before_stop`
- Target 07:30 net R: `1.0724184`
- Target 07:30 cash PnL: `670.2615`
- Tick query rows: `16833`

## Chronology and same-symbol authority

- 07:30 decision -> fill -> 07:45 decision exact: `true`
- 07:30 trade open at 07:45: `true`
- Same-symbol authority status: `lifecycle_not_evaluated_due_prior_cost_block`
- Serialized context consistent with chronology: `true`
- Context required for terminal decision: `false`
- Valid prior cost-block precedence: `true`
- Provenance-label caveat: `serialized_source_observed_context_is_provenance_only_not_decision_authority_after_pre_lifecycle_cost_continue`
- Late effective selector action: `reject`
- Late terminal blocker: `broker_cost_authority_blocked_non_executable`

## Replacement-value boundary

- Executed early net R: `1.0724184`
- Late diagnostic opportunity R: `0.3762609`
- These values are not arithmetically netted. The late value is diagnostic and joint execution was not replayed.
- No scale-in, reserve, rejection, allocation, or other policy preference is inferred.

## Same-day simulated portfolio reconciliation

- Status: `not_computed_xau_only_target_scope`
- Authorized: `false`
- Broad/generalization, policy, broker, live, and final claims remain unauthorized.

## Evidence boundary

This is a one-day XAUUSD-only ordered-tick local replay discriminator anchored to a completed 24-symbol baseline. It requires a completed 24-symbol reconciliation before any same-day simulated portfolio delta.
