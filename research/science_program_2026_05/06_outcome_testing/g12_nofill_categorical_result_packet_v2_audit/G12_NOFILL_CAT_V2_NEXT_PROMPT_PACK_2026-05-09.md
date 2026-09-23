# G12 NOFILL CAT V2 Next Prompt Pack

Promotion posture: `NO_PROMOTION_VERDICT`.

## Recommended Next Lane

`NOFILL_CAT_V2_QUARANTINED_CATEGORICAL_SYNTHESIS_FORENSICS`.

Objective: summarize and slice the 225 accepted V2 input-only categorical labels as source/control evidence, preserving blocked/rejected families, without converting any label into R, win rate, expectancy, broker actual-R, validation, promotion, live-gate evidence, or live behavior.

## Starting Facts To Preserve

- `298 = 225 accepted + 8 blocked + 65 rejected`.
- `225 = 52 prior accepted + 173 source-corrected accepted`.
- Accepted label counts: `nofill_terminal_before_entry=110`, `source_corrected_no_entry_through_pending_horizon=32`, `opening_drive_source_projection_ready_no_result_label=51`, `fill_path_entry_before_protective_level_no_terminal_observed=22`, `fill_path_entry_before_protective_level_before_terminal_area=4`, `fill_path_entry_before_terminal_area_before_protective_level=3`, `canonical_duplicate_geometry_source_ready_no_label_assigned=3`.
- Source-lane counts: prior G12 categorical packet audit 52, OTI1 32, OTI2 V2 29, OTI3 58, OTI4 51, OTI5 3.
- Residual blockers: 3 OTI4 May 3 source gaps, 4 OTI3 same-tick order ambiguities, 1 original OTI2 source gap.
- Rejects: 26 OTI4 contract-excluded rows and 39 OTI5 noncanonical duplicate projections.

## Required Boundaries

- Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
- Do not inspect broker/account/live/order/history labels, hidden labels, blocked-row outcomes, or performance values.
- Do not edit live trading prompts, risk, execution, permissions, safety gates, selectors, canaries, credentials, registries, remotes, paid/API/Databento paths, MT5 order/account/history code, or order behavior.

## Optional Separate Blocker-Clear Lane

If the owner wants to clear blockers instead, open a narrow source-access/capture lane for exactly the 8 blockers and request the named read-only source coverage. Do not score or promote anything in that lane.
