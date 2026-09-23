# G12 NOFILL CAT V2 Forensics Audit Next Prompt Pack

Promotion posture: `NO_PROMOTION_VERDICT`.

## Primary Next Route

`NOFILL_CAT_V2_G0_SYNTHESIS_CONTROL_ROUTE`

Objective: use the accepted G12 forensics audit as source/control input only. Synthesize what the no-fill categorical evidence says about pending lifecycle hygiene, source contracts, duplicate controls, and future capture needs. Do not open result scoring.

Required starting facts:

- `298 = 225 accepted + 8 blocked + 65 rejected`.
- `225 = 52 prior accepted + 173 source-corrected accepted`.
- Accepted labels stay input-only categorical/source-control labels.
- The 8 blockers and 65 rejects remain outside labels, denominators, and outcome use.
- `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false` remain mandatory.

## Optional Narrow Blocker Route

`NOFILL_CAT_V2_RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_LANE` may target exactly the 8 residual blockers. It must request or use only read-only source/capture evidence named in the audit. It must not score accepted rows, rejected rows, or blocked rows.

## Optional Preregistration Design Route

`NOFILL_CAT_V2_FROZEN_PREREGISTRATION_DESIGN_LANE` may design a future result contract, but must not open outcomes. It must name denominator, source fields, sample floor, no-leak proof, duplicate policy, G12 gate, and owner approval.

Forbidden: no R/performance, win-rate, expectancy, DSR/PBO performance claims, validation-safe flip, outcome-review opening, promotion, registry edit, live trading prompt or `src/` trading-logic change, risk/execution/permissions/safety/selector/canary change, credentials, remote push, paid/API/Databento call, MT5 order/account/history call, or live order behavior.
