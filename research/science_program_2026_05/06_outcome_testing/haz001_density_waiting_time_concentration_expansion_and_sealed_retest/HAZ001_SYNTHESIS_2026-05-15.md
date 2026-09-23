# HAZ-001 Density / Waiting-Time Expansion And Sealed Retest

Generated: 2026-05-15T10:12:56Z
Evidence class: `READY8_HAZ001_MECHANISM_EXPANSION_AND_QUARANTINED_RETEST_ONLY`
Promotion posture: `NO_PROMOTION_VERDICT`; `validation_safe=false`; `outcome_review_opened=false`; `live_effect=false`.

## Scope

This route recomputes HAZ-001 no-API neutral target-movement mechanism evidence from accepted frozen READY8 ledgers only. It is not R, PnL, win-rate, expectancy, live-readiness, or promotion evidence.

## Population

- HAZ-001 target rows scanned: 24112.
- HAZ-001 source rowset rows scanned: 3014.
- Unique duplicate denominator keys: 3014.
- Output ledger counts: {"deconcentration_rows": 38970, "fail_closed_rows": 394, "failure_rows": 3470, "horizon_target_rows": 80, "interaction_rows": 3877, "pass_control_rows": 3740, "question_rows": 46575, "retest_packet_rows": 3014, "source_inventory_rows": 22}.

## Mechanism Answer

HAZ-001 is capturing a candidate-arrival hazard state: either a long reset gap after prior candidates or a dense prior-24h burst relative to normal spacing controls. The source-bound signal is strongest when that state is evaluated at longer neutral horizons, especially h16/h32, and it is more visible in high-low excursion anatomy than in one-bar close-to-close noise.

The strongest card-level branch in this route is:

- `{'card_id': 'HAZ-001', 'horizon_m15_bars': '32', 'partition_assignment': 'SEALED_VALIDATION_CANDIDATE_DESIGN', 'target_family_id': 'neutral_high_low_excursion_m15_horizons_v1'}` delta=0.0073649237556876225 pass_n=987 control_n=312 classification=POSITIVE_PASS_GT_CONTROL.

## Concentration And Failure

- Leave-one deconcentration records emitted: 38970.
- Leave-one killed/reversed records: 91.
- Failure/inverse/null records preserved: 3470.
- Fail-closed sensitivity records preserved: 394.

Concentration remains material. Branches that survive current leave-one tests are retest candidates, not promotion candidates. Branches killed by a symbol/economic/session/source/date/window removal are explicitly retained as concentration-sensitive or failure anatomy.

## Retest Design

- Source-control retest packet rows emitted: 3014.
- Deconcentrated branch designs emitted: 143.

The next exact gate is G12 audit of this route. A broader deconcentrated historical retest requires a future source-control/result-packet route that freezes as-of source fields, duplicate policy, fail-closed policy, and target opening before admitting any new result rows.
