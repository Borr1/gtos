# G0 NOFILL Forward Capture Implementation Design Ranking

Route: `G0_NOFILL_FORWARD_PROJECTION_SYNTHESIS_CONTROL_ROUTE`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

| Rank | Route | Evidence Class | Allowed Now | Why |
|---:|---|---|---|---|
| 1 | `NOFILL_FORWARD_SOURCE_CAPTURE_CONTRACT_HARDENING_AND_OFFLINE_PROJECTION_PROTOTYPE` | `source_control_design_and_offline_projection` | `True` | It is the strongest next route because G12 accepted the repaired projection only as source/control evidence, while the remaining useful work is to freeze exact future capture fields, statuses, parser projections, fixtures, and verifiers before any live logger code is touched. |
| 2 | `G12_NOFILL_FORWARD_CAPTURE_CONTRACT_ACCEPTANCE_AUDIT` | `independent_source_control_audit` | `after_rank_1_artifacts_exist` | The contract/prototype must be independently accepted before becoming canonical input for any future implementation plan. |
| 3 | `OWNER_APPROVED_LIVE_LOGGER_WIRING_PLAN_PACKET` | `implementation_plan_requires_owner_approval` | `plan_only` | Useful as a plan only after source controls are accepted; actual code changes would touch live logger surfaces and need explicit owner approval. |
| 4 | `OFFLINE_RESULT_OR_COST_SCORING_PACKET` | `future_result_cost_lane` | `False` | It becomes relevant only after source-capture fields are frozen and source-safe input packets are accepted. It is forbidden in this G0 route. |
| 5 | `DIRECT_LIVE_LOGGER_WIRING_FROM_CURRENT_PROJECTION` | `forbidden_live_behavior_shortcut` | `False` | Current evidence is accepted only as source/control projection evidence and cannot justify direct live logger code changes. |

## Rank-1 Specification

The next route should build a source-capture contract hardening and offline projection prototype. It must produce fixtures, parser/projection rules, field allowlists, source-hash and parser-hash manifests, no-leak scans, duplicate/denominator proofs, and a G12-ready verifier. It must not touch live logger code.

Rank 3 is only a plan packet because live logger wiring requires explicit owner approval. Rank 4 and rank 5 are forbidden in this route.
