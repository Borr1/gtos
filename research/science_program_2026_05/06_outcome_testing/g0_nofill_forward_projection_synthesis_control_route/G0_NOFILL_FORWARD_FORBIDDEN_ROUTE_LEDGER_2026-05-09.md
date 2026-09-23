# G0 NOFILL Forward Forbidden Route Ledger

Route: `G0_NOFILL_FORWARD_PROJECTION_SYNTHESIS_CONTROL_ROUTE`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

| Forbidden Route Or Field Family | Status | Reason |
|---|---|---|
| Outcome scoring, R, WR, expectancy, DSR, PBO | `FORBIDDEN` | Current evidence is source/control only. |
| Setting validation, outcome-review, or live-effect flags to true | `FORBIDDEN` | Required flags stay false. |
| Registry edits | `FORBIDDEN` | No master registry change is authorized. |
| Live logger wiring or live trading surfaces | `FORBIDDEN` | Requires separate owner-approved implementation lane. |
| `src/`, prompts, config/risk/execution/permissions/safety/selectors/canaries/order behavior | `FORBIDDEN` | Live behavior surfaces are out of scope. |
| MT5 order/account/history/deal/position labels | `FORBIDDEN` | Would open broker result/order evidence. |
| Paid/API/Databento routes | `FORBIDDEN` | No spend or external call is authorized. |
| Raw tickets, pending tickets, deal IDs, position IDs | `FORBIDDEN` | Redaction statuses only. |

Any future lane that needs one of these routes must be explicitly opened by the owner and must state the evidence class it is crossing into.
