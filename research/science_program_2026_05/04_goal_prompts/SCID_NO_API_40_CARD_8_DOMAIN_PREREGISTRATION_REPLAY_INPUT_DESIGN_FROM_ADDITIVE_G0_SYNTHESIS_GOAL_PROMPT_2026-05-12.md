# SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN Goal Prompt

Evidence class: `SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN_ONLY`
Input G0 synthesis: `research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_additive_synthesis_control/`

Objective: Map the accepted 40 hypothesis cards across 8 science domains to additive SCID capture groups, freeze source fields, eligibility, denominator keys, duplicate policy, as-of rules, input-packet requirements, and no-API replay-input design without opening results.

Mandatory preflight:
1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/goal_session_research_discipline.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/research_current_state.md`.
6. Read the additive G0 synthesis decision ledger, accepted G12 synthesis, route ranking matrix, follow-up/blocker ledger, sequencing ledger, saturation/self-red-team ledger, not-in-a-loop ledger, and prompt-pack ledger.
7. Read the accepted hypothesis-factory artifacts and G12 audit artifacts from disk, not from memory:
   - `research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_HYPOTHESIS_CARD_LEDGER_2026-05-12.jsonl`
   - `research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_HYPOTHESIS_CARD_LEDGER_SUMMARY_2026-05-12.json`
   - `research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_SCIENCE_DOMAIN_COVERAGE_MATRIX_2026-05-12.json`
   - `research/science_program_2026_05/06_outcome_testing/g12_scid_no_api_mechanical_hypothesis_factory_audit/G12_SCID_NO_API_HYP_FACTORY_AUDIT_SCIENCE_DOMAIN_AND_OUTSIDE_CURRENT_EDGE_BREADTH_AUDIT_2026-05-12.json`

Lane posture:
- Do not rely on chat memory or compacted summaries.
- Treat examples as starting points, not boundaries.
- Current GTOS OB/retest logic is not the research horizon.
- Current SCID fields are a substrate, not the outer boundary; define additional source-safe fields or exact blockers where useful.
- Be broad, curious, active, and non-lazy while preserving hard evidence-class boundaries.
- Source-safe means auditable, redacted, as-of-bound, duplicate-controlled, fail-closed where unavailable, and no-leak. It does not mean narrow or OB-only.
- This is a full-population design route over the accepted hypothesis-card ledger. Do not sample, summarize, or choose favorites. Every accepted card must receive terminal treatment: preregisterable-now input design, blocked-pending-future-capture design, blocked-pending-LTF/orderflow/proxy design, or exact impossible proof.
- Treat the accepted `40` cards as the mandatory floor, not the research ceiling. If disk inspection, source-field mapping, blocker analysis, or replay-input design exposes additional source-safe hypothesis families, derived descriptors, adversarial controls, denominator concepts, or field requirements, emit them in a separate expansion-candidate ledger. Do not mix expansion candidates into the accepted 40-card denominator unless a later G12/G0 route accepts them.
- Preserve all eight accepted domains exactly:
  - `geometry_topology_path_shape`
  - `stochastic_tail_hazard_first_passage`
  - `microstructure_orderflow_liquidity_trapped_flow`
  - `behavioral_game_theory_session_participant_constraints`
  - `macro_session_calendar_cross_asset_context`
  - `execution_science_spread_slippage_fillability`
  - `ml_meta_labeling_model_disagreement_uncertainty_controls`
  - `adversarial_baselines_placebo_explanations`
- Preserve accepted coverage facts unless disk recomputation proves otherwise: `40` total cards, `5` cards per domain, `33/40` outside current GTOS/OB framing, readiness split `8` preregisterable-now descriptor-control cards, `15` blocked pending future capture fields, and `17` blocked pending LTF/orderflow/proxy expansion.
- Treat the `8` preregisterable-now cards as the highest-priority concrete replay/input-design candidates, but do not drop the other `32`; emit exact source-field/capture/proxy requirements for them.
- Pursue blockers inside this evidence class instead of merely naming them. If a missing field, source descriptor, denominator key, proxy status, or capture requirement can be resolved from existing accepted artifacts, local source-control files, route ledgers, or read-only hash-bound local data without opening forbidden surfaces, resolve it and record the proof. Only leave a blocker when it is genuinely outside this evidence class, non-generatable historical GTOS source-state, requires live activation, requires paid/API/vendor/broker evidence, or requires a later validation/result gate.
- Be creative but controlled: propose new field families, transformations, controls, and no-API replay-input structures when they are source-safe and auditable. Keep them quarantined as expansion candidates until accepted; do not suppress them because they are outside existing GTOS/OB framing.

Forbidden surfaces:
- No validation/result scoring/strategy-edge/R/PnL/win-rate/expectancy/performance claim.
- No promotion dossier or live-trading recommendation.
- No AI/API calls, paid/vendor access, credential/remote action, broker account/order/history/deal/position evidence, or raw market-data blob commit.
- No trading, risk, safety, production prompt-decision, canary, selector, execution, order-behavior, or live-restart change.
- Do not convert the additive no-restart/no-live-row landing into a repair blocker.

Required outputs:
- 40-card/8-domain source-field mapping matrix with one row per card and domain totals that reconcile to `40 = 8 domains * 5 cards`.
- Per-card terminal status ledger: preregisterable-now input design, future-capture-field requirement, LTF/orderflow/proxy source requirement, or exact impossible proof. The ledger must reconcile to the accepted readiness split or explain any disk-proven delta.
- Replay/input packet design ledger for the preregisterable-now cards, including eligibility, as-of source fields, duplicate denominator key, source proxy group, no-leak fields, forbidden fields, null/fail-closed statuses, and adversarial baseline/control pairing.
- Dependency ledger for blocked cards that is active and specific: exact missing field, exact accepted/needed capture group, exact local/source search or forward-capture requirement, and whether it can run in parallel with activation/monitoring routes.
- Same-evidence-class blocker pursuit ledger proving which blockers were actively pursued, which were resolved inside this prompt, and which remain exact dependency blockers.
- Expansion-candidate ledger for any additional source-safe hypotheses, fields, controls, denominators, transformations, or replay-input structures discovered beyond the accepted 40 cards. This ledger must be clearly separated from the accepted 40-card denominator and must state the evidence needed for future acceptance.
- Sealed historical partition or forward-capture dependency ledger. Do not open outcome scoring, but specify what must be frozen before a later result-packet route can be valid.
- Negative-evidence and anti-boxing ledger covering non-OB/current-field alternatives, including at least the eight domains above and the `33/40` outside-current-GTOS/OB-framing fact.
- Saturation ledger proving every accepted card was read and assigned.
- Machine-checkable verifier or focused test that confirms card count, domain count, per-card uniqueness, terminal-status reconciliation, safe flags, and no result-scoring fields.
- Completion audit with `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`, and result scoring closed.

Completion Standard:
- Produce scoped artifacts and, where useful, a verifier/focused test or machine-checkable checklist.
- Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
- Distinguish true blockers from nonblocking activation/source follow-ups.
- Include a saturation/self-red-team pass showing whether the lane accidentally became activation-only, OB-only, current-field-only, or passive live-row waiting.
- Include an anti-ceiling pass answering whether the route treated the accepted 40 cards as a ceiling. If yes, repair before completion by adding an expansion-candidate ledger.
- Do not mark complete unless all 40 cards and all 8 domains are accounted for exactly once and the verifier/focused test passes.

One-line starter for this prompt:
`/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN_FROM_ADDITIVE_G0_SYNTHESIS_GOAL_PROMPT_2026-05-12.md as the complete objective; run mandatory preflight/context refresh; do not rely on chat memory; stay SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN_ONLY with no validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/live-behavior/trading-risk-safety-prompt-decision changes; read the accepted hypothesis-card ledger and G12 audit from disk; account for all 40 accepted cards across all 8 domains exactly once, preserving the accepted 8/15/17 readiness split or proving any disk-based delta; treat the 40 cards as mandatory floor not ceiling; actively pursue same-evidence-class blockers and resolve any source-safe fields/denominators/proxies found from accepted artifacts or local hash-bound sources; design preregistered no-API replay/input packets for preregisterable cards and exact source/capture/proxy requirements for blocked cards; emit a separate expansion-candidate ledger for any new source-safe hypotheses/fields/controls/denominators/replay-input structures discovered beyond the 40 without mixing them into the accepted denominator; pursue proof-or-impossibility broadly inside this evidence class, not OB-only/current-field-only/passive-waiting; preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false; emit scoped artifacts, verifier/focused test, saturation/self-red-team, anti-ceiling, blocker/follow-up, and completion-audit ledgers; mark complete only when every accepted card/domain is terminally treated and the prompt file's completion standard is fully satisfied.`
