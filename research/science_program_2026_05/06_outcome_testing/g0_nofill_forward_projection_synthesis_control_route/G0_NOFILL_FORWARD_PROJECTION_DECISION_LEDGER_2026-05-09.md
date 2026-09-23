# G0 NOFILL Forward Projection Decision Ledger

Route: `G0_NOFILL_FORWARD_PROJECTION_SYNTHESIS_CONTROL_ROUTE`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Terminal G0 design decision: `NOFILL_FORWARD_SOURCE_CAPTURE_CONTRACT_HARDENING_AND_OFFLINE_PROJECTION_PROTOTYPE`.

G12 actually accepted: `ACCEPT_AS_SOURCE_CONTROL_PROJECTION_EVIDENCE_ONLY`.

G12 did not accept result/cost scoring, validation, promotion, registry edits, live logger wiring, paid/API routes, broker/account/order-history labels, or live behavior.

## Evidence

- Projection partition: `298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject`.
- Accepted denominators: row-level `225`, primary duplicate-key `182`, secondary duplicate-group `139`.
- Reject-overlap rows: `47` with zero denominator effect.
- G12 repair blockers `G12-PROJ-BLOCKER-001`, `G12-PROJ-BLOCKER-002`, and `G12-PROJ-WARN-001` are closed in the accepted repair reaudit.

## Next Gate

Before any code changes to live logger wiring, the next evidence-class gate is: owner-approved implementation lane after a source-capture contract/offline projection prototype passes independent G12 acceptance. This G0 route only specifies the design.
