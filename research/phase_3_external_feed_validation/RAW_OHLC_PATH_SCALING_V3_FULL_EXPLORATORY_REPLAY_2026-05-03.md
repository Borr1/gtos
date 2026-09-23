# Raw OHLC Path Scaling V3 Full Exploratory Replay

Date: 2026-05-03
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`
Discovery label: `DISCOVERY_ONLY_NOT_REGISTERED`

## Pre-Registration

Variant sidecar: `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_PRE_REGISTERED_VARIANTS_2026-05-03.json`

| variant | family | status | mechanism |
| --- | --- | --- | --- |
| V3_OB_LOCK_PULLBACK_RISK_BANK | risk_bank_sizing_only | PRE_REGISTERED_DISCOVERY_ONLY | Use OB boundary as tail-preserving floor, then test whether a pullback to that floor can recycle locked profit without increasing setup worst-case below -1R. |
| V3_FVG_THEN_OB_TAIL_RISK_BANK | fvg_ob_agreement_gate | PRE_REGISTERED_DISCOVERY_ONLY | Test the P1-A structural reading that FVG confirms delivery first and OB later preserves tail. |
| V3_FVG_ONLY_RESCUE_RISK_BANK | fvg_only_rescue_gate | PRE_REGISTERED_DISCOVERY_ONLY | Test whether the FVG-only rescue pocket can be converted into a bounded reentry hypothesis without relying on OB formation. |
| V3_OB_LOCK_COST_AWARE_MIN_R | cost_aware_min_incremental_r_gate | PRE_REGISTERED_DISCOVERY_ONLY | Reject low-incremental-upside reentries where costs can dominate the second leg. |

## Label Separation

- `actual_broker_r`: not available in V2 event log and never overwritten
- `path_synthetic_r`: V3 replay output only
- `fill_no_fill`: reported per reentry leg; unfilled pending contributes no reentry realized R

## Variant Summary

| variant | eligible | resolved | fill rate | ambiguity rate | mean R | median R | sum R | WR > 0 | p10 | mean delta vs J46 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V3_FVG_ONLY_RESCUE_RISK_BANK | 625 | 352 | 0.995200 | 0.436800 | 0.275834 | -0.100000 | 97.093652 | 0.329545 | -0.100000 | 0.270259 |
| V3_FVG_THEN_OB_TAIL_RISK_BANK | 689 | 642 | 0.606676 | 0.068215 | 0.549169 | 0.381356 | 352.566386 | 0.686916 | -0.100000 | -0.872794 |
| V3_OB_LOCK_COST_AWARE_MIN_R | 1286 | 1190 | 0.582426 | 0.074650 | 0.557772 | 0.326460 | 663.748912 | 0.672269 | -0.100000 | -0.910455 |
| V3_OB_LOCK_PULLBACK_RISK_BANK | 1286 | 1190 | 0.582426 | 0.074650 | 0.557772 | 0.326460 | 663.748912 | 0.672269 | -0.100000 | -0.910455 |

## Fill And Risk Status

| variant | fill status counts | risk-bank status counts |
| --- | --- | --- |
| V3_FVG_ONLY_RESCUE_RISK_BANK | {'FILLED_RESOLVED': 349, 'FILLED_AMBIGUOUS_SAME_ROW': 273, 'UNFILLED_REENTRY_PENDING': 3} | {'ACCEPTED_FULL_SIZE': 625} |
| V3_FVG_THEN_OB_TAIL_RISK_BANK | {'UNFILLED_REENTRY_PENDING': 271, 'FILLED_RESOLVED': 371, 'FILLED_AMBIGUOUS_SAME_ROW': 47} | {'ACCEPTED_FULL_SIZE': 689} |
| V3_OB_LOCK_COST_AWARE_MIN_R | {'UNFILLED_REENTRY_PENDING': 537, 'FILLED_RESOLVED': 653, 'FILLED_AMBIGUOUS_SAME_ROW': 96} | {'ACCEPTED_FULL_SIZE': 1286} |
| V3_OB_LOCK_PULLBACK_RISK_BANK | {'UNFILLED_REENTRY_PENDING': 537, 'FILLED_RESOLVED': 653, 'FILLED_AMBIGUOUS_SAME_ROW': 96} | {'ACCEPTED_FULL_SIZE': 1286} |

## Taxonomy

| variant | taxonomy counts |
| --- | --- |
| V3_FVG_ONLY_RESCUE_RISK_BANK | {'reentry_stop_gave_back_locked_profit': 236, 'reentry_timeout_path_dependent': 113, 'ambiguous_same_row_fill_exit': 273, 'unfilled_reentry_closed_too_early': 3} |
| V3_FVG_THEN_OB_TAIL_RISK_BANK | {'unfilled_reentry_closed_too_early': 271, 'reentry_timeout_path_dependent': 190, 'reentry_stop_gave_back_locked_profit': 181, 'ambiguous_same_row_fill_exit': 47} |
| V3_OB_LOCK_COST_AWARE_MIN_R | {'unfilled_reentry_closed_too_early': 536, 'reentry_timeout_path_dependent': 293, 'reentry_stop_gave_back_locked_profit': 359, 'reentry_target_after_pullback': 1, 'ambiguous_same_row_fill_exit': 96, 'unfilled_reentry_initial_lock_only_better': 1} |
| V3_OB_LOCK_PULLBACK_RISK_BANK | {'unfilled_reentry_closed_too_early': 536, 'reentry_timeout_path_dependent': 293, 'reentry_stop_gave_back_locked_profit': 359, 'reentry_target_after_pullback': 1, 'ambiguous_same_row_fill_exit': 96, 'unfilled_reentry_initial_lock_only_better': 1} |

## Concentration

| variant | top symbol/session/side share | top group | top year share | top year |
| --- | --- | --- | --- | --- |
| V3_FVG_ONLY_RESCUE_RISK_BANK | 0.268087 | {'symbol': 'GBPJPY', 'session': 'tokyo', 'side': 'LONG'} | 0.422457 | {'year': 2025} |
| V3_FVG_THEN_OB_TAIL_RISK_BANK | 0.270845 | {'symbol': 'NAS100', 'session': 'ny', 'side': 'LONG'} | 0.495376 | {'year': 2026} |
| V3_OB_LOCK_COST_AWARE_MIN_R | 0.213613 | {'symbol': 'NAS100', 'session': 'ny', 'side': 'LONG'} | 0.558352 | {'year': 2026} |
| V3_OB_LOCK_PULLBACK_RISK_BANK | 0.213613 | {'symbol': 'NAS100', 'session': 'ny', 'side': 'LONG'} | 0.558352 | {'year': 2026} |

## Methodology Diagnostics

- Variant count: `4`.
- DSR: `not_computable` because same_dataset_discovery_variants_not_frozen_unseen_validation; DSR would be promotion-style misuse.
- PBO: `not_computable` because no CSCV matrix of pre-registered folds for V3; current run is exploratory full-corpus replay.
- Effective-N proxy: `proxy_only_not_promotion_effective_n`.

## Interpretation

- What V3 appears to capture: A bounded way to recycle locked structural progress: close initial exposure at a confirmed FVG/OB floor, then test whether a pullback to that floor can be reentered without pushing aggregate setup worst-case below -1R.
- Likely structural signal: Rows with FVG-then-OB sequence and later successful pullback target are the most structurally interpretable. FVG-only rows are a separate rescue pocket but carry higher concentration risk from P1-A.

Likely artifacts:

- The replay uses selected OHLC rows, not broker lifecycle telemetry.
- The original POI bounds are missing, so reentry level quality is inferred from structural lock metadata.
- Same-row fill/exit ambiguity is bounded, not guessed.
- Same-dataset variant selection is not validation.

Next hypotheses:

1. Forward-log original POI bounds and pending lifecycle fields before any V3 promotion lane.
2. Test FVG-then-OB tail preservation on post-cutoff V2b rows first.
3. Add broker/tick costs and close-side slippage before reentry sizing research gets promoted beyond discovery.

## Casebook

Representative casebook rows are in `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_CASEBOOK_2026-05-03.jsonl`.
