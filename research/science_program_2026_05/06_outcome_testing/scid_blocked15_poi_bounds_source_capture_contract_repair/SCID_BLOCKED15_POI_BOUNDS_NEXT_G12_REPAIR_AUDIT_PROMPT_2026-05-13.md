# G12 SCID Blocked15 POI Bounds Source Capture Contract Repair Audit

Evidence class: `G12_SCID_BLOCKED15_POI_BOUNDS_SOURCE_CAPTURE_CONTRACT_REPAIR_AUDIT_ONLY`

Audit the repair package in `research/science_program_2026_05/06_outcome_testing/scid_blocked15_poi_bounds_source_capture_contract_repair`. Use mandatory preflight first, then independently verify:

Mandatory preflight and context:
- Run `python scripts/generate_live_state.py`, then read `.context/LIVE_STATE.md`.
- Read `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/research_current_state.md`, and `.context/00_core/local_heavy_data_inventory.md`.
- Read the controlling builder prompt, route output manifest, completion audit, verifier, focused tests, schema/fixture files, and every repair artifact in the package. Do not rely on chat memory or closeout claims.

Audit posture hardening:
- Be strict on source/control evidence, but do not perform conservative theater. Do not invent limitations, speculative blockers, or reject broad/new/non-OB mechanism support because it is unfamiliar or outside the old OB-only frame.
- Any failure or blocker must cite exact disk evidence: artifact path, card id, capture field, schema/fixture row, hash, as-of rule, redaction/no-leak rule, verifier/test failure, or manifest mismatch.
- If a mismatch is repairable inside this same G12 evidence class through deterministic schema/fixture/hash/manifest/parser repair, pursue and close that repair before issuing a terminal repair blocker. Do not stop at "blocked" while the repair is locally actionable.
- If something truly requires future forward capture or a later evidence class, emit the exact next prompt/starter and prove why it cannot be solved in this audit.
- The completion audit must include a prompt-to-artifact checklist showing mandatory context read, artifacts inspected, recomputations performed, repairs attempted/closed or proven out of scope, and the exact terminal decision.

1. The package stays source/control only with `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
2. No validation, result scoring, R/PnL/win-rate/expectancy/performance, promotion, AI/API, paid vendor, broker account/order/history/deal/position evidence, raw market blob, live restart, live behavior, or trading/risk/safety/prompt-decision surface is opened.
3. The target cards are exactly `ADV-005`, `BEH-002`, `BEH-003`, `BEH-005`, and `GEO-001`.
4. The `source_safe_mso_snapshot_and_poi_logger` contract has exact fields, parser requirements, as-of rules, hash recomputation, redaction rules, duplicate policy, fail-closed statuses, and G12 acceptance criteria.
5. The MSO snapshot/source-bar schema commits only hashes and source pointers, never raw market blobs, and supports non-OB mechanisms through `poi_mechanism_family`.
6. Synthetic fixtures cover valid OB/FVG/non-OB geometry and fail closed on missing bounds, stale as-of, late source bars, forbidden fields, hash mismatch, duplicate drift, and raw-blob attempts.
7. Each target card remains fail-closed until all dependency capture groups for that card are source-hashed, as-of-safe, redacted, candidate-attached by `candidate_input_row_id` and `duplicate_proxy_denominator_key`, and accepted by G12.

Terminal decisions allowed:

- `ACCEPT_AS_G12_SCID_BLOCKED15_POI_BOUNDS_SOURCE_CAPTURE_CONTRACT_REPAIR_CONTROL_EVIDENCE_ONLY`
- `REPAIR_REQUIRED_WITH_EXACT_FIELDS`

Do not open any result, validation, denominator movement, live behavior, API/spend, broker/account/order/history/deal/position, or promotion lane.
