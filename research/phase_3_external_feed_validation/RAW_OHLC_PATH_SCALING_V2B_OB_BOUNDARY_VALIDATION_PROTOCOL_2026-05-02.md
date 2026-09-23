# Phase 3 Path Scaling V2b OB-Boundary Validation Protocol

Date: 2026-05-02
Spec: `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2B_OB_BOUNDARY_VALIDATION_SPEC_V1.json`
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Purpose

V2 found a real structural path-management signal, but the headline winner `STRUCT_SWING_PROTECTED_V2` is concentration-blocked. Independent recomputation from the V2 event log confirmed that the top four positive swing-protected cohorts explain `0.962136` of positive cohort lift.

The cleanest next candidate is not the headline winner. It is `STRUCT_OB_BOUNDARY_V2`, because it is positive across all major group families and produces materially less winner truncation than the broader swing/FVG/composite policies. V2b exists to validate that OB-boundary finding without promoting it from the same data that discovered it.

## Registered Hypothesis

Post-entry OB protective-boundary floors can improve J46-J49 path management with less right-tail truncation than broader swing/FVG/composite structural floors, and the effect should remain positive across target, control, and blocked-control families rather than depending on a single dominance pocket.

## Primary Candidate

`STRUCT_OB_BOUNDARY_V2`

Rule:

- Detect an in-trade-direction BOS close.
- Search only prior closed selected-timeframe bars.
- Identify the protective boundary of the last opposing candle before that BOS close.
- Convert the protective boundary to base-R floor.
- Accept the floor only if it is non-negative R, behind current close, and improves the current stop.
- Activate the floor on the next selected path row only.

## Comparison Arms

| Arm | Role |
|---|---|
| `J46_J49_ONLY` | baseline |
| `STRUCT_SWING_PROTECTED_V2` | V2 headline winner / concentration-blocked comparator |
| `STRUCT_FVG_MID_EDGE_V2` | strongest pairwise structural comparator |
| `PATH_LOCK_HALF_GAIN_V0` | best fixed-R lock comparator |

Excluded from the primary decision:

- `STRUCT_COMPOSITE_ANY_V2`: rejected in V2 for over-locking.
- `STRUCT_DISPLACEMENT_HALFBACK_V2`: rejected in V2 as standalone floor.
- Reentry: V3-only and blocked until level quality is validated.

## Validation Lane

Preferred lane:

- Prospective rows with `candle_close_utc > 2026-04-30T17:00:00+00:00`.
- Final result must use the full available corpus after cutoff.

Same-event-log V2 data may only be used for verification and harness testing. It cannot validate V2b or promote live logic.

## Acceptance Gates

All gates are research-only. Passing them would justify continued validation work, not live deployment.

| Gate | Rule |
|---|---|
| global pairwise positive | OB-boundary pairwise mean delta vs J46 at `0.05R` cost must be `> 0`. |
| all major groups nonnegative | all-enabled, target, primary, cleared, negative-control, and blocked-control deltas must be `>= 0`. |
| target stronger than negative controls | target-cohorts mean delta must exceed negative-controls mean delta. |
| blocked controls not driver | blocked-control sum delta must be less than target-cohort sum delta. |
| cohort breadth | at least 5 raw cohorts positive; at least 3 positive cohorts must be non-blocked-control cohorts. |
| single-cohort cap | largest positive raw cohort contributes `<=45%` of total positive raw-cohort lift. |
| sample floor | interim: all-enabled paired n `>=150` and target paired n `>=75`; final: inherit prospective lane minimums. |
| no-leak | lower-TF starts after setup close; OB boundary uses only prior closed bars plus observed BOS close. |

## Known Discovery-Set Baseline

From `RAW_OHLC_PATH_SCALING_V2_CONCENTRATION_VERIFICATION_2026-05-02.md`:

| Metric | Discovery-set value |
|---|---:|
| OB-boundary pairwise mean delta vs J46 | `0.024061` |
| OB-boundary pairwise sum delta vs J46 | `105.724281` |
| target-cohorts mean delta | `0.041812` |
| negative-controls mean delta | `0.019349` |
| blocked-control sum delta | `17.857556` |
| target-cohort sum delta | `58.494471` |
| largest positive cohort share | `0.382696` |
| positive raw cohorts | `7` |

These numbers justify registration. They do not validate the hypothesis.

## Ambiguity Ledger

- The discovery-set OB-boundary result is still same-dataset evidence.
- Historical OHLC cost remains sensitivity-based, not true broker cost.
- OB-boundary is cleaner than swing/FVG by group behavior, but raw-cohort concentration still exists and must be gated.
- Prospective data may arrive slowly; interim readouts must be labeled interim.
- V3 reentry remains blocked because OB-boundary level quality has not been validated on unseen rows.

## Open Questions

1. Does OB-boundary remain positive on future rows after the 2026-04-30 cutoff?
2. Does OB-boundary keep lower truncation than swing/FVG when measured outside the discovery event log?
3. Does the result remain group-broad, or does it collapse into a single symbol/session pocket?
4. If OB-boundary fails broad validation but succeeds in a specific cohort, should the next hypothesis become cohort-specific instead of general?

## Next Steps

1. Build or adapt the V2 runner so it can run this V2b spec on future/prospective rows only.
2. Use same-event-log data only as a harness verification, not as validation.
3. Keep V3 reentry blocked until V2b either validates OB-boundary level quality or rejects it.
4. Preserve `NO_PROMOTION_VERDICT` in every V2b output unless a separate future promotion dossier is explicitly built.
