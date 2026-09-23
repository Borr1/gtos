# G0 NOFILL Forward Projection Evidence Chain Reconciliation

Route: `G0_NOFILL_FORWARD_PROJECTION_SYNTHESIS_CONTROL_ROUTE`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

| Chain Link | Status | Evidence | Boundary |
|---|---|---|---|
| CAT V3 source-control rebuild | accepted upstream | Accepted/source-control/source-impossible/reject families were frozen before projection. | Source/control only. |
| CAT V3 result contract/count packet | quarantined control evidence | Count denominators are row-level 225, primary 182, secondary 139. | Not validation or promotion. |
| Forward lifecycle capture contract audit | accepted with exact blockers | G12 accepted schema intent but required latency, pending-order, and spread/slippage addendum fields. | No raw logs consumed directly. |
| Forward contract addendum/projection builder | repaired and audited | Addendum added 26 fields; projection emitted 298 rows. | Source/control projection only. |
| G12 projection repair reaudit | accepted | Terminal decision `ACCEPT_AS_SOURCE_CONTROL_PROJECTION_EVIDENCE_ONLY`. | No result/cost/live use. |
| This G0 route | design synthesis | Ranks next route and freezes field/schema controls. | No implementation wiring. |

## Reconciled Counts

- Projection rows: `298`.
- Family counts: `{'accepted': 225, 'reject': 65, 'source_control': 4, 'source_impossible': 4}`.
- Required source-control rows remain `NOFILL-CAT-ROW-0049, NOFILL-CAT-ROW-0050, NOFILL-CAT-ROW-0051, NOFILL-CAT-ROW-0241`.
- Required source-impossible rows remain `NOFILL-CAT-ROW-0130, NOFILL-CAT-ROW-0143, NOFILL-CAT-ROW-0165, NOFILL-CAT-ROW-0178`.

## No-Leak And Hash Evidence

- Forbidden projection key hits: `0`.
- Forbidden projection value-token hits: `0`.
- Spread source hash non-null rows: `175`.
- Source hash records: `56`; parser hash records: `3`.

## Contract Blockers Translated Into Design

- `G12-FWD-BLOCKER-001`: Capture-latency observability is only partial. The contract has source manifest and source coverage timestamps, but no explicit row capture/write latency fields. Fix required: Add capture_observed_at_utc or equivalent.; Add capture_write_completed_utc or equivalent.; Add capture_latency_ms or explicit null/impossible reason.; Add capture_clock_source_and_skew_policy or equivalent..
- `G12-FWD-BLOCKER-002`: Source-safe pending-order observability is not explicit enough to consume current lifecycle logs without accidental order/account leakage. Fix required: Add pending_order_mode_source_safe or map pending_order_mode with an allowlist.; Add broker_pending_order_created_status as a categorical observability field, not a broker outcome label.; Add native_pending_order_type_status with MT5 ticket redaction proof.; Add mt5_order_ticket_redaction_status and fail closed when a ticket value would enter the contract row..
- `G12-FWD-BLOCKER-003`: Cost/spread coverage is present only as spread_state and quote_side. Slippage and execution-quality observability need closed source-safe status fields before any later cost or survival test. Fix required: Add decision_spread_source_safe and entry_touch_spread_source_safe or explicit unavailable statuses.; Add slippage_label_status fixed to NOT_OPENED_FOR_SOURCE_CONTROL unless a later result lane is explicitly opened.; Add execution_quality_label_status fixed to NOT_OPENED_FOR_SOURCE_CONTROL.; Preserve source hashes for any spread/quote measurement..
