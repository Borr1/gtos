# G0 ADV-002 Denominator-Control Synthesis

Evidence class: `G0_ADV002_SOURCE_CONTROL_AUDIT_OR_SYNTHESIS_ONLY`

Objective: synthesize the G12-audited ADV-002 duplicate-key collision controls into future denominator-entry gates without opening results. Do mandatory preflight and context refresh first. Do not rely on chat memory or closeout claims; inspect the route artifacts on disk.

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

Completion standard: emit `G0_SYNTHESIS_SOURCE_CONTROL_ONLY_NEXT_ROUTE_DECISION or exact G12/source-contract blocker list` with a prompt-to-artifact checklist, exact blockers or acceptance criteria, verifier output, focused tests where useful, and scoped commits. If any result or validation step appears necessary, stop and emit a separate future evidence-class prompt before scoring.
