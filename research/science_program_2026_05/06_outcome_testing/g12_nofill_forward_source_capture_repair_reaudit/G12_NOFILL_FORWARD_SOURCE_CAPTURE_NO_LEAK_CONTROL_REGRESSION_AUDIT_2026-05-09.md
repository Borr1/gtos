# G12 NOFILL Forward Source Capture No-Leak Control Regression Audit 2026-05-09

Route: `G12_NOFILL_FORWARD_SOURCE_CAPTURE_REPAIR_REAUDIT`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`


| Item | Value |
|---|---|
| Status | `PASS` |
| Prototype rows | `298` |
| Family counts | `{"accepted": 225, "reject": 65, "source_control": 4, "source_impossible": 4}` |
| Accepted denominators | `[225, 182, 139]` |
| Forbidden key hits | `0` |
| Open flag hits | `0` |
| Same-tick ambiguity fixture present | `True` |
| Package no-leak status | `PASS` |
| Package denominator status | `PASS` |

The hash-policy repair did not alter prototype rows, family counts, accepted denominators, fixtures, no-leak controls, or source/cost/execution separation. The remaining weakness is isolated to non-text LF-fallback acceptance in the verifier policy.
