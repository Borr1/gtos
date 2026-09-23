# NOFILL CAT V3 Count Context Anchor

Promotion posture: `NO_PROMOTION_VERDICT`

Route: `NOFILL_CAT_V3_QUARANTINED_CATEGORICAL_COUNT_PACKET`
Contract: `NOFILL_CAT_V3_QUARANTINED_CATEGORICAL_RESULT_CONTRACT_V1`
Starting HEAD: `1aa209bd94fd5f138f998b3c3000d43f7ee79b95`

## Boundary

- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`
- Input/control counts only; no outcome, validation, promotion, or live behavior lane is opened.

## Active Questions

- Do the accepted-only rows reconcile to the exact 225/182/139 denominators?
- Do the four source-control, four source-impossible, and 65 reject rows stay outside every count?
- Does the 47-row reject overlap trap have zero denominator effect?
- Are there accepted duplicate-key label, geometry, ordering, source-hash, or denominator conflicts?
- Can categorical labels be interpreted only as input/control labels without outcome leakage?
