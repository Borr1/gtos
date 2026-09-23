# G0 NOFILL Forward Duplicate And Denominator Control Review

Route: `G0_NOFILL_FORWARD_PROJECTION_SYNTHESIS_CONTROL_ROUTE`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Universe equation: `298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject`.

| Denominator | Value | Control |
|---|---:|---|
| Row-level accepted | 225 | Accepted rows only; source-control/source-impossible/reject excluded before count. |
| Primary duplicate-key | 182 | Raw duplicate text is never emitted; SHA256 only. |
| Secondary duplicate-group | 139 | Group collapse remains unchanged by projection fields. |
| Reject overlap rows | 47 | Zero denominator effect by accepted-first filtering. |

## Future Rule

Any future source-capture implementation must carry row-level, primary duplicate-key, and secondary duplicate-group membership fields plus accepted-first filtering status. A row cannot enter a result/cost lane unless a frozen source/control packet and G12 audit prove the denominator effect remains explicit.
