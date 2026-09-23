# NOFILL Forward Source Capture Contract 2026-05-09

Route: `NOFILL_FORWARD_SOURCE_CAPTURE_CONTRACT_HARDENING_OFFLINE_PROJECTION_PROTOTYPE`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Contract Boundary

This contract is frozen for source/control review only. It defines what a future owner-approved live logger lane would need to capture, but it does not implement that wiring.

## Field Families

| Family | Field Count |
|---|---:|
| `capture_latency_clock` | 8 |
| `duplicate_denominator` | 5 |
| `entry_touch_observability` | 2 |
| `event_order_resolution` | 2 |
| `no_leak_control` | 1 |
| `pending_lifecycle` | 5 |
| `pending_order_observability` | 7 |
| `regime_session_review_control` | 5 |
| `source_coverage` | 3 |
| `source_provenance` | 2 |
| `spread_slippage_execution_quality_status` | 11 |
| `terminal_area_observability` | 4 |

## Required Gate

Future live logger wiring is still gated behind independent G12 acceptance of this contract/prototype and separate owner approval.

## Forbidden Raw Values

Raw broker/account/order/deal/position/result/cost/performance values may not be emitted or hashed. The JSON contract carries the exact forbidden field-name taxonomy as source-control metadata only.
