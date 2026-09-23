# G12 SCID Blocked17 LTF Asof Path Attachment Repair Audit

Objective: Independently audit the source/control artifacts from `research/science_program_2026_05/06_outcome_testing/scid_blocked17_ltf_asof_path_parser_and_candidate_attachment` for the `SCID_BLOCKED17_LTF_ASOF_PATH_PARSER_AND_CANDIDATE_ATTACHMENT_ONLY` route. Accept or reject only the parser/source-hash/as-of attachment packet. Do not open validation, result scoring, R/PnL/win-rate/expectancy/performance, promotion, AI/API, paid vendor access, broker account/order/history/deal/position evidence, raw market blob commits, live restart/live behavior, or trading/risk/safety/prompt-decision changes.

Audit posture hardening:
- Be strict on parser/source-hash/as-of evidence, but do not perform conservative theater. Do not invent limitations, speculative blockers, or reject broad/new/non-OB-adjacent LTF path evidence because it is unfamiliar or not part of the old GTOS edge box.
- Any failure or blocker must cite exact disk evidence: artifact path, card id, field row, parser requirement, source hash, as-of rule, no-leak rule, verifier/test failure, or manifest mismatch.
- If a mismatch is repairable inside this same G12 evidence class through deterministic parser/hash/as-of/manifest recomputation or scoped artifact repair, pursue and close that repair before issuing a terminal rejection. Do not stop at "blocked" while the repair is locally actionable.
- If a source truly requires future capture or another evidence class, emit the exact next prompt/starter and prove why it cannot be solved in this audit.
- The completion audit must include a prompt-to-artifact checklist showing mandatory context read, artifacts inspected, recomputations performed, repairs attempted/closed or proven out of scope, and the exact terminal decision.

Mandatory preflight:
1. `python scripts/generate_live_state.py`
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/goal_session_research_discipline.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/research_current_state.md`.
6. Read `.context/00_core/local_heavy_data_inventory.md`.
7. Read `.context/00_core/ai_in_loop_cost_control_research_plan.md`.

Required audit inputs:
- `research/science_program_2026_05/06_outcome_testing/scid_blocked17_ltf_asof_path_parser_and_candidate_attachment/SCID_BLOCKED17_LTF_ASOF_PARSER_SOURCE_HASH_ATTACHMENT_MATRIX_2026-05-13.json`
- `research/science_program_2026_05/06_outcome_testing/scid_blocked17_ltf_asof_path_parser_and_candidate_attachment/SCID_BLOCKED17_LTF_ASOF_CANDIDATE_DECISION_WINDOW_ASOF_MANIFEST_2026-05-13.json`
- `research/science_program_2026_05/06_outcome_testing/scid_blocked17_ltf_asof_path_parser_and_candidate_attachment/SCID_BLOCKED17_LTF_ASOF_MISSING_PARSER_ACCESS_LEDGER_2026-05-13.json`
- `research/science_program_2026_05/06_outcome_testing/scid_blocked17_ltf_asof_path_parser_and_candidate_attachment/SCID_BLOCKED17_LTF_ASOF_DENOMINATOR_NOLEAK_AUDIT_2026-05-13.json`
- `research/science_program_2026_05/06_outcome_testing/scid_blocked17_ltf_asof_path_parser_and_candidate_attachment/SCID_BLOCKED17_LTF_ASOF_SATURATION_SELF_REDTEAM_LEDGER_2026-05-13.json`
- `research/science_program_2026_05/06_outcome_testing/scid_blocked17_ltf_asof_path_parser_and_candidate_attachment/SCID_BLOCKED17_LTF_ASOF_COMPLETION_AUDIT_2026-05-13.json`

Audit requirements:
- Verify the exact `17` Blocked17 denominator and the exact `13` LTF source-exists card subset.
- Verify all `78` `SOURCE_EXISTS_NEEDS_PARSER` field rows are either parser-bound with hash/as-of requirements attached or reduced to exact no-commit hash/source/access/capture requirements.
- Verify candidate decision-window as-of rules use `decision_asof_utc` as the hard upper bound and fail closed without `decision_minus_window_start_utc`.
- Verify no ready8, expansion, or other blocked-card rows entered this denominator.
- Verify every artifact preserves `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
- Verify no result, target-hit, stop-hit, R/PnL, win-rate, expectancy, broker account/order/history/deal/position, AI/API, paid vendor, raw blob commit, live, or trading-decision surface was opened.

Expected outputs:
- G12 decision ledger.
- Source-status recomputation audit.
- Parser/hash/as-of row audit.
- Missing exact-requirement audit.
- Denominator/no-leak audit.
- Saturation/self-red-team audit.
- Verification result and completion audit.

Completion standard: complete only if the packet can be accepted or rejected from disk evidence. If rejected, reduce every rejection to an exact parser/source/hash/as-of/access/capture repair requirement. Keep `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.
