# HAZ-005 Transition Clock Split And Source Repair

Date: 2026-05-15

Evidence class: `READY8_HAZ005_TRANSITION_CLOCK_SPLIT_AND_SOURCE_REPAIR_ONLY`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## What Was Built

- Descriptor-state split rows: `8576`
- Pass/control recomputation rows: `896`
- Descriptor one-vs-rest rows: `1664`
- Horizon reversal rows: `200`
- Fail-closed prior-16 repair rows: `790`
- Repaired descriptor packet rows: `5`
- Concentration/deconcentration rows: `6784`
- READY8 interaction rows: `400`
- Future source-capture rows: `7`

## Prior-16 Repair Status

- `NOT_REPAIRABLE_FROM_SEARCHED_SAME_EVIDENCE_CLASS_SOURCES`: `785`
- `REPAIRED_FROM_LOCAL_SIERRA_CANDIDATE_REQUIRES_G12`: `5`

Local Sierra repairs are candidate source-control rows, not admitted validation rows. They require the next G12 audit before any denominator admission.

## Headline Sensitivity

- `SEALED_VALIDATION_CANDIDATE_DESIGN` `neutral_close_to_close_return_m15_horizons_v1` h1: 6.7453932e-05 -> 6.7453932e-05 (shift 0.0)
- `SEALED_VALIDATION_CANDIDATE_DESIGN` `neutral_close_to_close_return_m15_horizons_v1` h4: 8.4483928e-05 -> 8.4483928e-05 (shift 0.0)
- `SEALED_VALIDATION_CANDIDATE_DESIGN` `neutral_close_to_close_return_m15_horizons_v1` h16: -0.000410694858 -> -0.000410694858 (shift 0.0)
- `SEALED_VALIDATION_CANDIDATE_DESIGN` `neutral_close_to_close_return_m15_horizons_v1` h32: -3.6079381e-05 -> -3.6079381e-05 (shift 0.0)
- `STRESS_ROBUSTNESS_CANDIDATE_DESIGN` `neutral_close_to_close_return_m15_horizons_v1` h1: 0.000205035504 -> 0.000205035504 (shift 0.0)
- `STRESS_ROBUSTNESS_CANDIDATE_DESIGN` `neutral_close_to_close_return_m15_horizons_v1` h4: 0.000572163503 -> 0.000572163503 (shift 0.0)
- `STRESS_ROBUSTNESS_CANDIDATE_DESIGN` `neutral_close_to_close_return_m15_horizons_v1` h16: -0.001134829206 -> -0.001134829206 (shift 0.0)
- `STRESS_ROBUSTNESS_CANDIDATE_DESIGN` `neutral_close_to_close_return_m15_horizons_v1` h32: -0.000755603016 -> -0.000755603016 (shift 0.0)
- `SEALED_VALIDATION_CANDIDATE_DESIGN` `neutral_high_low_excursion_m15_horizons_v1` h1: 4.9912642e-05 -> 4.9912642e-05 (shift 0.0)
- `SEALED_VALIDATION_CANDIDATE_DESIGN` `neutral_high_low_excursion_m15_horizons_v1` h4: 7.9743878e-05 -> 7.9743878e-05 (shift 0.0)
- `SEALED_VALIDATION_CANDIDATE_DESIGN` `neutral_high_low_excursion_m15_horizons_v1` h16: -0.000359685132 -> -0.000359685132 (shift 0.0)
- `SEALED_VALIDATION_CANDIDATE_DESIGN` `neutral_high_low_excursion_m15_horizons_v1` h32: 0.000743962622 -> 0.000743962622 (shift 0.0)
- `STRESS_ROBUSTNESS_CANDIDATE_DESIGN` `neutral_high_low_excursion_m15_horizons_v1` h1: 0.000161649583 -> 0.000161649583 (shift 0.0)
- `STRESS_ROBUSTNESS_CANDIDATE_DESIGN` `neutral_high_low_excursion_m15_horizons_v1` h4: 0.000827522132 -> 0.000827522132 (shift 0.0)
- `STRESS_ROBUSTNESS_CANDIDATE_DESIGN` `neutral_high_low_excursion_m15_horizons_v1` h16: -0.000875958385 -> -0.000875958385 (shift 0.0)
- `STRESS_ROBUSTNESS_CANDIDATE_DESIGN` `neutral_high_low_excursion_m15_horizons_v1` h32: -0.000879720927 -> -0.000879720927 (shift 0.0)

Materiality observed: `True`.

## Interpretation

HAZ-005 was not closed as merely mixed. The route splits drift-bucket, range-bucket, session-open, combined transition states, h4-to-h16 reversal anatomy, source/economic/session concentration, fail-closed prior-16 repairs, and interactions with HAZ-001, UNC-004, BEH-001, MAC-001, and MAC-004.

Remaining work crosses an evidence-class gate: audit the repaired packet and source-search ledgers with G12 using `research/science_program_2026_05/06_outcome_testing/haz005_transition_clock_split_and_source_repair/G12_HAZ005_TRANSITION_CLOCK_REPAIR_AUDIT_PROMPT_2026-05-15.md`. This route makes no promotion, live-readiness, R/PnL, win-rate, expectancy, AI/API, paid, broker, raw-blob, prompt, config, risk, safety, or execution claim.
