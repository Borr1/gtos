# G12 SCID Blocked17 Orderflow Proxy Contract Audit Goal Prompt

Evidence class: G12 source-control audit only.

Objective: audit the source-family, proxy-equivalence, as-of/hash/redaction, blocker, and context-packet contracts emitted by `research/science_program_2026_05/06_outcome_testing/scid_orderflow_proxy_validity_contract_and_context_packet_route`. Accept or reject only whether the packet is G12-ready as source/control evidence. Do not open validation, result scoring, R/PnL/win-rate/expectancy/performance, promotion, AI/API, paid-vendor access, broker account/order/history/deal/position evidence, raw market blob commits, live restart/live behavior, registry edits, or trading/risk/safety/prompt-decision changes.

Audit posture hardening:
- Be strict on source-family/proxy-equivalence evidence, but do not perform conservative theater. Do not invent limitations, speculative blockers, or reject proxy/context evidence because it is broad, cross-domain, non-OB, or unfamiliar.
- Proxy evidence being context-only is not a defect by itself. Reject only if the packet claims broker-native CFD truth without source proof, leaks forbidden fields, has broken as-of/hash/redaction controls, or fails its stated contract.
- Any failure or blocker must cite exact disk evidence: artifact path, card id, source family, equivalence field, hash, as-of rule, redaction/no-leak rule, verifier/test failure, or manifest mismatch.
- If a mismatch is repairable inside this same G12 evidence class through deterministic contract/hash/manifest/parser repair, pursue and close that repair before issuing a terminal rejection. Do not stop at "blocked" while the repair is locally actionable.
- If a source truly requires later capture, paid/vendor approval, or another evidence class, emit the exact next prompt/starter and prove why it cannot be solved in this audit.
- The completion audit must include a prompt-to-artifact checklist showing mandatory context read, artifacts inspected, recomputations performed, repairs attempted/closed or proven out of scope, and the exact terminal decision.

Mandatory preflight:
1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/goal_session_research_discipline.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/research_current_state.md`.
6. Read `.context/00_core/local_heavy_data_inventory.md`.
7. Read `research/science_program_2026_05/06_outcome_testing/scid_orderflow_proxy_validity_contract_and_context_packet_route/SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_COMPLETION_AUDIT_2026-05-13.json`.
8. Read `research/science_program_2026_05/06_outcome_testing/scid_orderflow_proxy_validity_contract_and_context_packet_route/SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_OUTPUT_MANIFEST_2026-05-13.json`.
9. Read `research/science_program_2026_05/06_outcome_testing/scid_orderflow_proxy_validity_contract_and_context_packet_route/SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_SOURCE_FAMILY_CONTRACT_2026-05-13.json`.
10. Read `research/science_program_2026_05/06_outcome_testing/scid_orderflow_proxy_validity_contract_and_context_packet_route/SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_EQUIVALENCE_AND_INVALID_CONTEXT_MATRIX_2026-05-13.json`.
11. Read `research/science_program_2026_05/06_outcome_testing/scid_orderflow_proxy_validity_contract_and_context_packet_route/SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_PAID_ACCESS_FREE_BLOCKER_LEDGER_2026-05-13.json`.

Acceptance standard:
- The exact blocked-17 denominator is preserved, the other 15 blocked cards stay excluded, and ready-8/expansion denominators are untouched.
- Proxy evidence remains context/control only and `broker_native_cfd_truth_claims=0`.
- Every `PROXY_VALIDITY_REQUIRES_CONTRACT` surface is either covered by a source-family/parser/hash/as-of/non-equivalence contract or reduced to an exact source/parser/access/capture requirement.
- Source-family contracts fail closed on missing source family, symbol mapping, roll/session/as-of, staleness, inverse policy, hash/deferral, or non-equivalence fields.
- No forbidden surface is opened.

Required outputs: G12 decision ledger, artifact/hash audit, source-family contract audit, equivalence/non-equivalence audit, blocker exactness audit, no-leak/safe-flag audit, verifier/focused tests, completion audit, and next G0/G12 starter if accepted. Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
