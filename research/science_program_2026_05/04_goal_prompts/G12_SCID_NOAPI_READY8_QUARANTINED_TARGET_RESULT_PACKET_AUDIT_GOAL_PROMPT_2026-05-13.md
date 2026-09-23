# G12 SCID No-API READY8 Quarantined Target Result Packet Audit

Evidence class: `G12_SCID_NOAPI_READY8_QUARANTINED_TARGET_RESULT_PACKET_AUDIT_ONLY`

Objective: independently audit the quarantined READY8 no-API target-result packet built by `SCID_NOAPI_READY8_QUARANTINED_TARGET_RESULT_PACKET_AFTER_G0_GATE`. Accept or reject only source/result-packet integrity. Do not validate, promote, score strategy performance, inspect blocked-card results, use AI/API, use paid/vendor data, inspect broker account/order/history/deal/position evidence, edit registry/remotes, or touch live trading behavior.

Audit posture hardening:
- Be strict on evidence and independent recomputation, but do not perform conservative theater. Do not invent limitations, speculative blockers, or reject broad/new/non-OB-adjacent evidence because it is unfamiliar or not part of the old GTOS edge box.
- Treat the packet as a quarantined result-target integrity artifact, not as a performance claim. The absence of validation/performance authorization is not a defect by itself.
- Any failure or blocker must cite exact disk evidence: artifact path, row id, hash, schema field, as-of rule, no-leak rule, verifier/test failure, or manifest mismatch.
- If a mismatch is repairable inside this same G12 evidence class through deterministic parser/hash/EOL/manifest recomputation or scoped artifact repair, pursue and close that repair before issuing a terminal rejection. Do not stop at "blocked" while the repair is locally actionable.
- If something truly requires a later evidence class, emit the exact next prompt/starter and prove why it cannot be solved in this audit. Do not make up missing requirements to look adversarial.
- The completion audit must include a prompt-to-artifact checklist showing mandatory context read, artifacts inspected, recomputations performed, repairs attempted/closed or proven out of scope, and the exact terminal decision.

Mandatory preflight:
1. Run `python scripts/generate_live_state.py`, then read `.context/LIVE_STATE.md`.
2. Read `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/research_current_state.md`, `.context/00_core/local_heavy_data_inventory.md`, and `.context/00_core/ai_in_loop_cost_control_research_plan.md`.
3. Read the controlling builder prompt `research/science_program_2026_05/04_goal_prompts/SCID_NOAPI_READY8_QUARANTINED_RESULT_PACKET_AFTER_G0_GATE_GOAL_PROMPT_2026-05-13.md`.
4. Read the G0 gate, G12 source-control audit, READY8 materialization packet, and this result-packet route at `research/science_program_2026_05/06_outcome_testing/scid_noapi_ready8_quarantined_target_result_packet_after_g0_gate`.

Audit requirements:
- Verify exactly 8 ready cards, 3,014 source candidates, 24,112 READY8 rowset rows, horizons 1/4/16/32, 2 neutral target families, and 192,896 target terminal rows.
- Recompute row/file hashes, row IDs, duplicate counts, source/as-of joins, bar-horizon off-by-one rules, source segment hashes, fail-closed statuses, and forbidden-field scans.
- Confirm blocked dependencies, expansion candidates, broker/account/order/history/deal/position fields, validation, promotion, R/PnL/win-rate/expectancy/performance, AI/API, paid/vendor, raw market blob, registry, remote, and live/trading-risk/safety/prompt-decision changes stayed closed.
- Audit sidecar diagnostics for denominator leakage and movement-as-performance interpretation.
- Produce a decision ledger, verification result, saturation/self-red-team, completion audit, and the next G0 or repair prompt/starter.

Allowed terminal decisions:
- `ACCEPT_AS_G12_SCID_NOAPI_READY8_QUARANTINED_TARGET_RESULT_PACKET_CONTROL_EVIDENCE_ONLY`
- `REJECT_WITH_EXACT_READY8_TARGET_RESULT_PACKET_REPAIR_REQUIREMENTS`

Keep `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
