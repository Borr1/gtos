# G0 NOFILL Forward Source Cost Execution Separation Ledger

Route: `G0_NOFILL_FORWARD_PROJECTION_SYNTHESIS_CONTROL_ROUTE`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

| Family | Source-Safe Now | Future Use | Still Closed |
|---|---|---|---|
| Decision spread | `decision_spread_status`, `decision_spread_value_source_safe`, `decision_spread_unit`, `spread_source_hash` | Later cost context if a result/cost lane is opened. | Not slippage, not R, not execution quality. |
| Entry-touch spread | `entry_touch_spread_status`, `entry_touch_spread_value_source_safe`, `spread_source_hash` | Later spread-at-touch context if exact touch timestamp exists. | Not fill price, not order history. |
| Slippage | `slippage_label_status`, `slippage_value_redaction_status` only | Future result/cost lane can request explicit labels. | Slippage values remain redacted/closed now. |
| Execution quality | `execution_quality_label_status`, `execution_quality_value_redaction_status` only | Future lane can classify missed/partial/failed fill after source gate. | No order-send result labels now. |
| Outcome/cost testing | `cost_testing_gate_status` | Marks whether spread-only source control is ready. | R, WR, expectancy, DSR, PBO, validation remain closed. |

## Current Source Projection Counts

- Decision spread status counts: `{'CAPTURED_SOURCE_SAFE': 167, 'SOURCE_FIELD_MISSING': 131}`.
- Entry-touch spread status counts: `{'CAPTURED_SOURCE_SAFE': 59, 'SOURCE_FIELD_MISSING': 126, 'TOUCH_NOT_OBSERVED_SOURCE_SAFE': 113}`.
- These counts are source observability counts, not performance outcomes.
