# V121AA Runtime Final-Risk Public Authority Pre-Replay Brief

Generated: `2026-07-05T16:55:00Z`

Broker/live/final remain closed. Local replay/package authority remains full 82-sleeve authority.

## Current Completed Replay

Latest completed replay is `BROAD_LIVE_AS_IF_REPLAY_V121Z_STOP_HAZARD_PRESSURE_REALLOCATION_QUALITY_REPAIR_20260514`, window `2026-05-14..2026-05-14`. This is a bounded one-day hostile proof slice, not full-reservoir transfer proof.

V121Z rows: candidate `7968`, scorecard `96`, order `45`, trade `19`, missed `7945`, bucket `434`, source universe `282`. Trade result: net `NoneR`, gross/final `NoneR`, cash PnL `None`, risk cash `None`, W/L/F `None/None/None`.

## New Root Mismatch

V121Z proved the stop-hazard pressure and reallocation-quality patch, but exposed a ledger authority bug: `40` order/trade rows have public `final_approved_risk_pct` that differs from nested runtime risk authority. Example shape: top-level `final_approved_risk_pct=2.0`, `risk_pct/runtime_final_risk_pct=0.625`, nested `risk_authority.runtime_final_risk_pct=0.625`.

This is a correctness/ledger-authority repair. Expected R/cash effect is zero if execution sizing already used runtime risk. Expected reporting effect is that public `final_approved_risk_pct` and `approved_risk_pct` match executable runtime risk, while `selected_cell_risk_pct`, `scheduler_approved_risk_pct`, `risk_reduction_basis_pct`, and `full_risk_counterfactual_risk_pct` preserve the full-risk basis separately.

## Baseline Comparison

| Run | Window | Trades | Net R | Gross/Final R | Cash PnL | W/L/F |
|---|---:|---:|---:|---:|---:|---:|
| V89D | 2026-05-13..17 | 56 | +34.84520454 | +39.93441037 | +8178.90660707 | 41/15/0 |
| V90 | 2026-05-13..17 | 51 | +28.84201157 | +33.36349114 | +6371.80465431 | 37/14/0 |
| V92 | 2026-05-13..17 | 51 | +29.35570236 | +33.93212860 | +6228.63096022 | 37/14/0 |
| V121X | 2026-05-14 | 25 | -0.78175217 | +1.11053495 | -83.41120760 | 9/16/0 |
| V121Z | 2026-05-14 | None | None | None | None | None/None/None |

Five-day comparators are not denominator-equivalent to this one-day proof slice.

## Patch Batch

Files/components:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: canonical `runtime_risk_public_authority_fields`; normalization applies runtime public risk before ladder/transfer computation; blocker/probe risk checks prefer `runtime_final_risk_pct` over stale `final_approved_risk_pct`.
- `tests/test_v4_timewarp_simulated_live_research_loop.py`: regression for V121Z shape where runtime risk is `0.625` and full-risk basis is `2.0`.

Classification:

- Correctness: public final/approved risk fields now bind to executable runtime risk.
- Performance: none expected directly.
- Diagnostic/ledger: repair provenance fields show when public final risk was corrected.

## Success Criteria

Helped: V121AA order/trade rows have zero public-final-risk mismatches, executed REFUSED/source-gap remains zero, and R/cash are unchanged or causally explained.

Failed: any filled/pending order or trade row still has public `final_approved_risk_pct` different from nested runtime risk authority.

Exposed next flaw: truth repair passes; next root remains performance behavior in stop-loss/exit/lifecycle/fillability, especially NY/XAGUSD/AUDUSD/GBPJPY losing buckets.
