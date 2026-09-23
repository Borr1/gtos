# G12 ADV-002 Source-Control Audit

Evidence class: `G12_ADV002_SOURCE_CONTROL_AUDIT_OR_SYNTHESIS_ONLY`

Objective: audit the ADV-002 duplicate-key collision source-control design package and decide whether it is acceptable as source/control evidence only. Do mandatory preflight and context refresh first. Do not rely on chat memory or closeout claims; inspect the route artifacts on disk.

Mandatory preflight and context:
- Run `python scripts/generate_live_state.py`, then read `.context/LIVE_STATE.md`.
- Read `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/research_current_state.md`, and `.context/00_core/local_heavy_data_inventory.md`.
- Read the controlling builder prompt, route output manifest, completion audit, verifier, focused tests, and every required input below before deciding.

Audit posture hardening:
- Be strict on duplicate/collision source-control evidence, but do not perform conservative theater. Do not invent limitations, speculative blockers, or reject anti-boxing/non-OB/novel collision controls because they are unfamiliar or outside the old GTOS edge box.
- Any failure or blocker must cite exact disk evidence: artifact path, candidate id, duplicate key, row hash, group version, collision rule, as-of/no-leak rule, verifier/test failure, or manifest mismatch.
- If a mismatch is repairable inside this same G12 evidence class through deterministic hash/EOL/manifest/group-policy repair or scoped artifact repair, pursue and close that repair before issuing a terminal rejection. Do not stop at "blocked" while the repair is locally actionable.
- If a source truly requires later capture or another evidence class, emit the exact next prompt/starter and prove why it cannot be solved in this audit.
- The completion audit must include a prompt-to-artifact checklist showing mandatory context read, artifacts inspected, recomputations performed, repairs attempted/closed or proven out of scope, and the exact terminal decision.

Required inputs:
- `research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_CONTEXT_ANCHOR_2026-05-13.json`
- `research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_SOURCE_CONTRACT_LEDGER_2026-05-13.json`
- `research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_ROUTE_DECISION_LEDGER_2026-05-13.json`
- `research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_DUPLICATE_DENOMINATOR_POLICY_2026-05-13.json`
- `research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_ASOF_NOLEAK_DUPLICATE_POLICY_2026-05-13.json`
- `research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_SEARCHED_ROOT_LEDGER_2026-05-13.json`
- `research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_NEGATIVE_EVIDENCE_BLOCKER_LEDGER_2026-05-13.json`
- `research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_SATURATION_SELF_RED_TEAM_2026-05-13.md`
- `research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_COMPLETION_AUDIT_2026-05-13.json`
- `research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_VERIFICATION_RESULT_2026-05-13.json`

Audit focus:
- candidate id, duplicate key, source hash, group membership version, and collision policy coverage;
- denominator drift, group-membership instability, canonical-row ambiguity, cross-card duplication, session/symbol/timeframe collision, and row-hash/EOL friction;
- no-leak/as-of field allowlist and forbidden field denylist;
- fail-closed statuses for unresolved collisions;
- exact repair blockers where a source contract is missing.

Boundaries:
- may_open_outcomes_or_results_in_this_route=false
- Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
- No validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/live-restart/live-behavior/trading-risk-safety-prompt-decision changes.

Completion standard: emit `ACCEPT_AS_G12_ADV002_DUPLICATE_COLLISION_SOURCE_CONTROL_DESIGN_EVIDENCE_ONLY or exact repair blockers` with a prompt-to-artifact checklist, exact blockers or acceptance criteria, verifier output, focused tests where useful, and scoped commits. If any result or validation step appears necessary, stop and emit a separate future evidence-class prompt before scoring.
