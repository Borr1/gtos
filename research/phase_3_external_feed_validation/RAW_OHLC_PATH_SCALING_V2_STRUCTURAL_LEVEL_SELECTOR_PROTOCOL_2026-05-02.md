# Phase 3 Path Scaling V2 Structural Level Selector Protocol

**Created:** 2026-05-02
**Status:** REGISTERED_BEFORE_V2_RESULT_RUN
**Promotion verdict allowed:** false
**Required verdict string:** `NO_PROMOTION_VERDICT`

## Boundary

- Research/tooling only.
- No live trading logic changes.
- No prompt edits.
- No parameter optimization.
- No paid AI/API calls.
- Full final verdict requires the full available corpus.
- V2 is lock-only. Reentry remains blocked until a later registered hypothesis.

## V1 Lessons Carried Forward

V1 showed that the MTF path resolver is useful measurement infrastructure and that fixed-R lock-only rules are too blunt. The path-scaling thesis is not rejected, but the fixed-R abstraction is rejected as a promotion candidate. V2 therefore tests whether lock floors chosen from structural events can rescue adverse outcomes without cutting the right tail as aggressively as fixed-R ladders.

## V2 Registered Hypothesis

If a post-entry favorable path creates a no-leak structural floor, then locking behind that floor should outperform fixed-R lock-only controls and remain competitive with J46-J49 under cost sensitivity and same-bar stress. The structural floor must be observable at the replay clock. It must be behind price, positive in R terms, and it must not use future swing confirmation, future FVG fill state, future session extremes, or any post-exit information.

## Structural Event Catalog

The catalog is intentionally broad. Events marked `implemented_selector` are tested as lock candidates in V2. Events marked `diagnostic_only` are counted or carried in the report where available but are not promotion candidates. Events marked `future_registration_required` are not eligible for V2 selection because they require extra data, a new parameter, or a separate structural hypothesis.

| family | event class | V2 status | no-leak/as-of rule |
| --- | --- | --- | --- |
| swing_structure | confirmed swing high/low | implemented_selector | Pivot is known only after two later selected-timeframe bars close. |
| swing_structure | protected pullback swing in trade direction | implemented_selector | Latest confirmed swing low above entry for LONG, or swing high below entry for SHORT. |
| swing_structure | BOS broken level in trade direction | implemented_selector | Current closed bar must close beyond a previously confirmed swing. |
| swing_structure | CHoCH against trade | diagnostic_only | Current closed bar must close beyond a previously confirmed opposite swing. |
| swing_structure | failed break / wick reclaim | diagnostic_only | Wick breach and close reclaim are judged only on the closed bar. |
| liquidity | selected-path high/low run | implemented_selector | Broken high/low must be from prior selected-timeframe rows only. |
| liquidity | equal high/low run | implemented_selector | Equal level must be formed by at least two prior selected-timeframe extremes before the break bar closes. |
| liquidity | Asian high/low | diagnostic_only | Requires session segmentation by symbol clock; used for counts, not as a V2 promotion selector. |
| liquidity | London high/low | diagnostic_only | Requires session segmentation by symbol clock; used for counts, not as a V2 promotion selector. |
| liquidity | prior day high/low | diagnostic_only | Requires complete prior-day coverage; used for counts, not as a V2 promotion selector. |
| liquidity | sweep and reclaim | diagnostic_only | Wick breach plus close reclaim on a closed bar. |
| poi_boundary | fresh order-block protective boundary | implemented_selector | OB is defined only after an in-trade-direction BOS close; last opposing candle before the BOS is searched in prior closed bars. |
| poi_boundary | breaker boundary | future_registration_required | Requires robust mitigation state reconstruction; defer to a dedicated registered run. |
| poi_boundary | FVG midpoint | implemented_selector | Three-bar imbalance is known only after the third bar closes. |
| poi_boundary | FVG protective edge | implemented_selector | Same as FVG midpoint. |
| poi_boundary | FVG full fill / partial fill | diagnostic_only | Fill state can be counted after formation but not used to fit lock levels in V2. |
| volatility_displacement | displacement halfback | implemented_selector | Closed candle body must exceed 1.5x the prior body average; halfback is the candle body midpoint. |
| volatility_displacement | ATR favorable extension | diagnostic_only | Counted from trailing true range, but not a selector to avoid adding a tunable multiplier. |
| volatility_displacement | range expansion close | diagnostic_only | Closed-bar range/body diagnostics only. |
| premium_discount | impulse equilibrium / OTE | diagnostic_only | Requires stable impulse-leg reconstruction; not a V2 lock selector. |
| round_number | symbol round number reclaim | future_registration_required | Requires pre-registered symbol increments and separate multiple-testing control. |
| time_session | session boundary or kill-zone segment | diagnostic_only | Context only; not a structural lock level. |
| failure_state | loss of protected swing | diagnostic_only | Used to explain failures, not to exit in V2. |

## Registered V2 Policies

All V2 structural policies inherit the J46-J49 final target and hold profile: 6R final target and 12 M15-bar time stop after fill. A structural stop improvement is pending until the next path row, matching V0/V1 lock activation discipline.

| variant_id | family | selector set |
| --- | --- | --- |
| `STRUCT_SWING_PROTECTED_V2` | swing_structure | protected confirmed pullback swing |
| `STRUCT_BOS_LEVEL_V2` | swing_structure | broken confirmed swing level after BOS close |
| `STRUCT_DISPLACEMENT_HALFBACK_V2` | volatility_displacement | displacement candle body halfback |
| `STRUCT_FVG_MID_EDGE_V2` | poi_boundary | FVG midpoint plus protective edge |
| `STRUCT_OB_BOUNDARY_V2` | poi_boundary | fresh OB protective boundary after BOS |
| `STRUCT_LIQUIDITY_RUN_V2` | liquidity | prior path high/low run plus equal high/low run |
| `STRUCT_COMPOSITE_ANY_V2` | composite | best valid floor from all implemented selectors |

## Selector Validity Rules

- A candidate floor must improve the current pending stop.
- A LONG floor must be between entry and current close, inclusive of entry and exclusive of a price above current close.
- A SHORT floor must be between current close and entry, inclusive of entry and exclusive of a price below current close.
- A candidate floor must be non-negative in R terms.
- If multiple candidates are valid on the same closed row, the highest floor R is selected.
- The selected floor becomes active on the next row, never inside the bar that created it.
- Same-bar fill and path events remain unresolved under the selected timeframe and are excluded or stressed in diagnostics.

## Required Diagnostics

- Full available corpus replay scope and input hashes.
- MTF coverage ledger inherited from V1.
- Variant, group, cohort, and family summaries.
- Cost sensitivity at all registered cost scenarios.
- Same-bar stress table: exclude unresolved, breakeven, and pessimistic.
- Selector firing summary by family, timeframe, side, symbol, session, and role.
- Pairwise structural-versus-J46 and structural-versus-fixed-R deltas.
- Forensics tables for rescued J46 nonpositive rows, J46-truncated winners, and selector-specific failures.
- Ambiguity ledger, opened questions, next steps, and final synthesis.

## Decision Rule

V2 cannot promote live logic from this same-dataset historical replay. A favorable result can only register a later validation hypothesis. V2 can be marked `RESEARCH_ACCEPTED_FOR_NEXT_STAGE` only if:

1. The structural selector beats J46-J49 globally after 0.05R cost sensitivity.
2. The same structural selector does not flip negative under pessimistic same-bar stress.
3. The improvement is not concentrated in a single symbol/session/cohort.
4. No no-leak or coverage ambiguity remains blocking.

Otherwise V2 is rejected or retained as diagnostic evidence only.

## Opened Questions Before Running

| question | planned answer path |
| --- | --- |
| Do structural floors reduce V1's winner truncation? | Pairwise J46 versus structural policy forensics. |
| Do structural floors rescue the same J46 nonpositive rows that fixed-R locks rescued? | Rescue overlap and unique-rescue tables. |
| Which structural family works, if any? | Family summaries and selector firing tables. |
| Are M1/M5 advantages real or coverage artifacts? | Timeframe-stratified deltas plus M15 fallback ledger. |
| Are results driven by one instrument/session? | Cohort and group concentration diagnostics. |
| Do structural events fire too early and recreate V1 same-bar ambiguity? | Same-bar stress and lock activation diagnostics. |

