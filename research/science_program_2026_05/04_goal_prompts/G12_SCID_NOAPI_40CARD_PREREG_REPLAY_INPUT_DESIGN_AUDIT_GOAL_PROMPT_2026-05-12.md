# G12 SCID No-API 40-Card Preregistration Replay-Input Design Audit Goal Prompt

Evidence class: `G12_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_AUDIT_ONLY`

Target route:

`research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/`

Objective: independently audit the SCID no-API 40-card/8-domain preregistration replay-input design route. Accept it only if the accepted 40-card denominator, all 8 science domains, the 8/15/17 readiness split, the 8 preregisterable packet designs, the 32 blocked-card dependency rows, and the 8 quarantined expansion candidates are source/control-consistent, hash-bound, no-leak, denominator-safe, and strictly non-result-scoring.

This is a G12 audit, not a pessimistic theater prompt. Be adversarial about evidence, hashes, counts, leakage, denominator drift, and prompt compliance, but do not invent blockers and do not punish novelty. Expansion candidates beyond the accepted 40 are not a blocker if they remain quarantined outside the accepted denominator with clear future acceptance requirements.

Mandatory preflight:

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/goal_session_research_discipline.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/research_current_state.md`.
6. Read the target route completion audit, verification result, output manifest, source-field mapping matrix, per-card terminal status ledger, replay-input packet design ledger, blocked-card dependency ledger, blocker-pursuit ledger, partition/forward-capture dependency ledger, expansion-candidate ledger, negative-evidence/anti-boxing ledger, saturation/anti-ceiling ledger, builder, verifier, and focused tests.
7. Read the upstream accepted hypothesis-factory ledger and G12 audit:
   - `research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_HYPOTHESIS_CARD_LEDGER_2026-05-12.jsonl`
   - `research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_HYPOTHESIS_CARD_LEDGER_SUMMARY_2026-05-12.json`
   - `research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_SCIENCE_DOMAIN_COVERAGE_MATRIX_2026-05-12.json`
   - `research/science_program_2026_05/06_outcome_testing/g12_scid_no_api_mechanical_hypothesis_factory_audit/G12_SCID_NO_API_HYP_FACTORY_AUDIT_SCIENCE_DOMAIN_AND_OUTSIDE_CURRENT_EDGE_BREADTH_AUDIT_2026-05-12.json`
8. Read the accepted G0 additive synthesis ledgers and the rank-1 hardening addendum:
   - `research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_additive_synthesis_control/G0_SCID_FC_ADDITIVE_SYNTHESIS_ROUTE_RANKING_MATRIX_2026-05-12.json`
   - `research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_additive_synthesis_control/G0_SCID_FC_ADDITIVE_SYNTHESIS_RANK1_PROMPT_HARDENING_ADDENDUM_2026-05-12.json`

Audit posture:

- Recompute from disk. Do not rely on pasted closeouts.
- Do not accept route claims without checking the actual artifacts.
- Do not reject because the route is broad, creative, outside OB, or emits expansion candidates.
- Do reject or repair-block if the accepted 40-card denominator changes silently, if expansion candidates enter accepted denominators, if result/performance fields open, if blocked cards are dropped, if source/status requirements are vague, if hashes are stale, or if the verifier/test coverage does not actually check the claimed invariants.
- Treat `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false` as hard required posture.

Required independent recomputations:

1. Recompute accepted card count: exactly `40`.
2. Recompute domain count: exactly `8`.
3. Recompute cards per domain: exactly `5` each for:
   - `geometry_topology_path_shape`
   - `stochastic_tail_hazard_first_passage`
   - `microstructure_orderflow_liquidity_trapped_flow`
   - `behavioral_game_theory_session_participant_constraints`
   - `macro_session_calendar_cross_asset_context`
   - `execution_science_spread_slippage_fillability`
   - `ml_meta_labeling_model_disagreement_uncertainty_controls`
   - `adversarial_baselines_placebo_explanations`
4. Recompute readiness split: `8` preregisterable-now, `15` future-capture-field blocked, `17` LTF/orderflow/proxy blocked.
5. Recompute outside-current-GTOS/OB framing count: `33`.
6. Verify all 40 accepted cards appear exactly once in source-field mapping and terminal status ledgers.
7. Verify 8 replay-input packet rows exist only for preregisterable-now cards and carry eligibility, denominator, as-of, no-leak, forbidden-field, baseline/control, and future-result-gate fields.
8. Verify 32 blocked-card dependency rows exist only for blocked cards and include exact missing fields/statuses, required capture groups, source/capture/proxy requirements, exact next source-control route, future result gate, and parallelization/activation relation.
9. Verify 8 expansion-candidate rows are outside the accepted denominator with `accepted_40_card_denominator_inclusion=false`, future acceptance requirements, and no result-scoring/live/AI/API/paid/broker surfaces.
10. Verify same-evidence-class blocker pursuit is real: captured groups were resolved where allowed, remaining blockers are exact dependency blockers, and no blocker was left as a vague label.
11. Rehash target artifacts and parser/verifier/test files. Any hash mismatch must be explained and either repaired or recorded as a blocker.
12. Run the target verifier and focused tests. Prefer the route-local verifier/test commands; if Windows pycache friction occurs, use explicit cfile or AST fallback and record the reason.
13. Scan target artifacts for forbidden result/performance terms and unsafe flag openings. The scan must distinguish forbidden metric/result usage from harmless string references inside "forbidden" or "closed" statements.
14. Check git diff scope: no production prompt-decision, trading/risk/safety/execution/canary/selector/live behavior, AI/API, paid/vendor, broker/account/order/history/deal/position evidence, raw market blob, registry edit, credential, remote, or live restart changes were opened by this route.

Required G12 outputs:

- Decision ledger with terminal decision.
- Card/domain/readiness recomputation ledger.
- Replay-input packet audit ledger.
- Blocked-card dependency exactness audit.
- Expansion-candidate quarantine audit.
- Same-evidence-class blocker-pursuit audit.
- No-leak/forbidden-surface/safe-flag audit.
- Hash/manifest/parser/verifier/test audit.
- Saturation/fairness ledger proving the audit did not reject novelty, did not collapse to OB-only, and did not accept silent denominator expansion.
- Completion audit with `can_mark_goal_complete`.
- Standalone verifier and focused tests for the G12 audit route.
- If accepted, emit the next G0 synthesis prompt/starter. If repair-blocked, emit the exact repair prompt/starter. If rejected, emit exact rejection evidence.

Allowed terminal decisions:

- `ACCEPT_AS_G12_SCID_NOAPI_PREREG_REPLAY_INPUT_DESIGN_CONTROL_EVIDENCE_ONLY`
- `ACCEPT_WITH_EXACT_NONBLOCKING_FOLLOWUPS`
- `REPAIR_BLOCKED_SCID_NOAPI_PREREG_REPLAY_INPUT_DESIGN`
- `REJECT_INVALID_SCID_NOAPI_PREREG_REPLAY_INPUT_DESIGN`

Completion standard:

- All required recomputations are present.
- Target verifier/test results are rerun or exact environment-friction fallback is recorded.
- G12 verifier and focused tests pass.
- Accepted 40-card denominator and 8 expansion candidates are separated.
- No validation/result scoring, R/PnL/win-rate/expectancy/performance claim, promotion, AI/API, paid/vendor, broker account/order/history/deal/position evidence, raw market-data blob commit, live restart, registry edit, remote push, credential use, prompt/config/risk/safety/execution/canary/selector change, or live trading behavior is opened.
- `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false` are preserved.
- Scoped artifacts and context refresh are committed.

One-line starter:

`/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/G12_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_AUDIT_GOAL_PROMPT_2026-05-12.md as the complete objective; run mandatory preflight/context refresh; do not rely on chat memory; stay G12_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_AUDIT_ONLY with no validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/live-behavior/trading-risk-safety-prompt-decision changes; independently audit the SCID no-API prereg/replay-input route from disk; recompute 40 cards, 8 domains, 5 cards/domain, 8/15/17 readiness, 33 outside-GTOS/OB, 8 packet designs, 32 blocked dependencies, and 8 quarantined expansion candidates; verify hashes, no-leak, denominator separation, blocker pursuit, target verifier/tests, G12 verifier/tests, and fair audit posture; do not reject novelty or expansion candidates when quarantined, and do not accept silent denominator expansion; emit decision, audit ledgers, next G0 or repair prompt, scoped commits, NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false; mark complete only when this prompt's completion standard is fully satisfied.`
