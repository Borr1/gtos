# SCID READY8 Discriminative Sealed Validation Execution

Generated: 2026-05-13T17:56:35Z
Evidence class: `SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_EXECUTION_ONLY`
Promotion posture: `NO_PROMOTION_VERDICT`

## Scope

This route scored the frozen READY8 sealed and stress target-result packet only. Metrics are neutral target-movement, sign-rate, pass/control, descriptor-contrast, effective-N, concentration, and fail-closed anatomy diagnostics. They are not R, PnL, trade win rate, expectancy, live-readiness, strategy deployment, or promotion claims.

## Population

- Frozen READY8 cards: 8.
- Frozen duplicate denominator keys: 3014.
- Sealed branch records: 44434.
- Pass/control and descriptor contrast records: 18071.
- Fail-closed/source-repair ledger rows: 2161 aggregating 35811 excluded target rows or fail-closed role rows.

## Validation Shape

- Comparable pass-vs-control records above the duplicate floor: 1278.
- Positive pass-minus-control records: 724.
- Inverse pass-minus-control records: 554.
- Descriptor one-vs-rest records: 9570.
- Sealed branch records below duplicate floor: 30305.
- Sealed branch records with a concentration warning: 44103.

## Strongest Positive Pass/Control Summaries

Full ledgers are in `R8DISC_SEALED_PASS_CONTROL_2026-05-13.jsonl`; the rows below are readability summaries only.

- `pass_vs_control_economic_group_target_family_horizon` `HAZ-001` h=32 target=`neutral_high_low_excursion_m15_horizons_v1` delta=0.0160409268 pass_n=189 control_n=68
- `pass_vs_control_source_segment_target_family_horizon` `HAZ-001` h=32 target=`neutral_high_low_excursion_m15_horizons_v1` delta=0.0160409268 pass_n=189 control_n=68
- `pass_vs_control_symbol_target_family_horizon` `HAZ-001` h=32 target=`neutral_high_low_excursion_m15_horizons_v1` delta=0.0160409268 pass_n=189 control_n=68
- `pass_vs_control_economic_group_target_family_horizon` `HAZ-001` h=32 target=`neutral_close_to_close_return_m15_horizons_v1` delta=0.0125696989 pass_n=175 control_n=75
- `pass_vs_control_source_segment_target_family_horizon` `HAZ-001` h=32 target=`neutral_close_to_close_return_m15_horizons_v1` delta=0.0125696989 pass_n=175 control_n=75

## Strongest Inverse Pass/Control Summaries

Full ledgers are in `R8DISC_SEALED_PASS_CONTROL_2026-05-13.jsonl`; the rows below are readability summaries only.

- `pass_vs_control_economic_group_target_family_horizon` `MAC-001` h=32 target=`neutral_close_to_close_return_m15_horizons_v1` delta=-0.0149323711 pass_n=90 control_n=161
- `pass_vs_control_source_segment_target_family_horizon` `MAC-001` h=32 target=`neutral_close_to_close_return_m15_horizons_v1` delta=-0.0149323711 pass_n=90 control_n=161
- `pass_vs_control_symbol_target_family_horizon` `MAC-001` h=32 target=`neutral_close_to_close_return_m15_horizons_v1` delta=-0.0149323711 pass_n=90 control_n=161
- `pass_vs_control_economic_group_target_family_horizon` `MAC-001` h=32 target=`neutral_high_low_excursion_m15_horizons_v1` delta=-0.0118658828 pass_n=117 control_n=140
- `pass_vs_control_source_segment_target_family_horizon` `MAC-001` h=32 target=`neutral_high_low_excursion_m15_horizons_v1` delta=-0.0118658828 pass_n=117 control_n=140

## Why Slices Worked Or Failed

Working slices are those where frozen pass or descriptor branches had more positive neutral target movement than their control/rest comparator while clearing duplicate-key floor checks. Failing slices are inverse, neutral, underpowered, concentrated, or fail-closed in the ledgers. The explanation ledger preserves the source-bound reason for each: observed descriptor/horizon/target-family contrast, duplicate-key underpowering, source/economic/symbol/session concentration, stress sensitivity, or exact fail-closed source repair family.

## Next Gate

The next step is independent G12 audit of this result execution packet: `research/science_program_2026_05/04_goal_prompts/G12_R8DISC_SEALED_VALIDATION_AUDIT_GOAL_PROMPT_2026-05-13.md`. That audit must recompute counts and selected metrics from frozen files, attack leakage/duplicate/concentration/stress issues, and preserve `NO_PROMOTION_VERDICT`.
