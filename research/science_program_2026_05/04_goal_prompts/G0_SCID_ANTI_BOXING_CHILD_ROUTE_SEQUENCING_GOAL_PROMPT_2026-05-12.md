# G0 SCID Anti-Boxing Child Route Sequencing

Evidence class: `G0_SCID_ANTI_BOXING_CHILD_ROUTE_SEQUENCING_ONLY`

Objective: rank and sequence the 12 accepted anti-boxing child route prompt packs after the G12 intake audit. Do not launch child routes inside this G0 sequencing lane.

Operating posture: sequence aggressively and intelligently. This is not a conservative queue-management exercise and not an OB-only fallback. The goal is to maximize research surface area while preserving dependency order and evidence boundaries. The 12 child routes are the accepted first wave, not the limit of future inquiry; if disk evidence exposes missing adjacent routes or a better parallelization strategy, emit them as exact quarantined follow-ups without launching them here.

Constructive framing rule: boundary language in this prompt exists only to keep sequencing and evidence classes clean. It must not make the session cautious, narrow, or reluctant to rank broad science routes. Interpret every safety boundary as a scoping rail around a full-strength sequencing search, not as a reason to find fewer child routes, prefer old GTOS/OB behavior, or suppress novel route families.

## Mandatory Preflight And Context

1. Run `python scripts/generate_live_state.py`, then read `.context/LIVE_STATE.md`.
2. Read `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/research_current_state.md`, `.context/00_core/local_heavy_data_inventory.md`, and `.context/00_core/ai_in_loop_cost_control_research_plan.md`.
3. Read this G12 audit route directory: `research/science_program_2026_05/06_outcome_testing/g12_scid_anti_boxing_route_intake_audit`.
4. Read the target anti-boxing intake directory: `research/science_program_2026_05/06_outcome_testing/scid_noapi_cross_domain_anti_boxing_route_intake`.

## Inputs To Sequence

1. `ADV-001` - `adversarial_baselines_placebos` - prompt `research/science_program_2026_05/04_goal_prompts/SCID_ANTI_BOXING_R01_ADV_001_GOAL_PROMPT_2026-05-12.md` - starter `research/science_program_2026_05/06_outcome_testing/scid_noapi_cross_domain_anti_boxing_route_intake/SCID_ANTI_BOXING_R01_ADV_001_STARTER_2026-05-12.txt`
2. `MISS-001` - `source_missingness_denominator_controls` - prompt `research/science_program_2026_05/04_goal_prompts/SCID_ANTI_BOXING_R02_MISS_001_GOAL_PROMPT_2026-05-12.md` - starter `research/science_program_2026_05/06_outcome_testing/scid_noapi_cross_domain_anti_boxing_route_intake/SCID_ANTI_BOXING_R02_MISS_001_STARTER_2026-05-12.txt`
3. `HAZ-001` - `stochastic_tail_hazard` - prompt `research/science_program_2026_05/04_goal_prompts/SCID_ANTI_BOXING_R03_HAZ_001_GOAL_PROMPT_2026-05-12.md` - starter `research/science_program_2026_05/06_outcome_testing/scid_noapi_cross_domain_anti_boxing_route_intake/SCID_ANTI_BOXING_R03_HAZ_001_STARTER_2026-05-12.txt`
4. `MICRO-001` - `auction_microstructure_orderflow_liquidity` - prompt `research/science_program_2026_05/04_goal_prompts/SCID_ANTI_BOXING_R04_MICRO_001_GOAL_PROMPT_2026-05-12.md` - starter `research/science_program_2026_05/06_outcome_testing/scid_noapi_cross_domain_anti_boxing_route_intake/SCID_ANTI_BOXING_R04_MICRO_001_STARTER_2026-05-12.txt`
5. `EXEC-002` - `execution_fillability_spread_slippage` - prompt `research/science_program_2026_05/04_goal_prompts/SCID_ANTI_BOXING_R05_EXEC_002_GOAL_PROMPT_2026-05-12.md` - starter `research/science_program_2026_05/06_outcome_testing/scid_noapi_cross_domain_anti_boxing_route_intake/SCID_ANTI_BOXING_R05_EXEC_002_STARTER_2026-05-12.txt`
6. `FAIL-001` - `failure_anatomy_derived_hypotheses` - prompt `research/science_program_2026_05/04_goal_prompts/SCID_ANTI_BOXING_R06_FAIL_001_GOAL_PROMPT_2026-05-12.md` - starter `research/science_program_2026_05/06_outcome_testing/scid_noapi_cross_domain_anti_boxing_route_intake/SCID_ANTI_BOXING_R06_FAIL_001_STARTER_2026-05-12.txt`
7. `GEOM-TOPO-001` - `geometry_topology_path_shape` - prompt `research/science_program_2026_05/04_goal_prompts/SCID_ANTI_BOXING_R07_GEOM_TOPO_001_GOAL_PROMPT_2026-05-12.md` - starter `research/science_program_2026_05/06_outcome_testing/scid_noapi_cross_domain_anti_boxing_route_intake/SCID_ANTI_BOXING_R07_GEOM_TOPO_001_STARTER_2026-05-12.txt`
8. `ML-001` - `ml_meta_labeling_uncertainty` - prompt `research/science_program_2026_05/04_goal_prompts/SCID_ANTI_BOXING_R08_ML_001_GOAL_PROMPT_2026-05-12.md` - starter `research/science_program_2026_05/06_outcome_testing/scid_noapi_cross_domain_anti_boxing_route_intake/SCID_ANTI_BOXING_R08_ML_001_STARTER_2026-05-12.txt`
9. `BEH-001` - `behavioral_game_theory_session_participants` - prompt `research/science_program_2026_05/04_goal_prompts/SCID_ANTI_BOXING_R09_BEH_001_GOAL_PROMPT_2026-05-12.md` - starter `research/science_program_2026_05/06_outcome_testing/scid_noapi_cross_domain_anti_boxing_route_intake/SCID_ANTI_BOXING_R09_BEH_001_STARTER_2026-05-12.txt`
10. `MACRO-004` - `macro_calendar_cross_asset` - prompt `research/science_program_2026_05/04_goal_prompts/SCID_ANTI_BOXING_R10_MACRO_004_GOAL_PROMPT_2026-05-12.md` - starter `research/science_program_2026_05/06_outcome_testing/scid_noapi_cross_domain_anti_boxing_route_intake/SCID_ANTI_BOXING_R10_MACRO_004_STARTER_2026-05-12.txt`
11. `ADV-002` - `adversarial_baselines_placebos` - prompt `research/science_program_2026_05/04_goal_prompts/SCID_ANTI_BOXING_R11_ADV_002_GOAL_PROMPT_2026-05-12.md` - starter `research/science_program_2026_05/06_outcome_testing/scid_noapi_cross_domain_anti_boxing_route_intake/SCID_ANTI_BOXING_R11_ADV_002_STARTER_2026-05-12.txt`
12. `ADV-004` - `adversarial_baselines_placebos` - prompt `research/science_program_2026_05/04_goal_prompts/SCID_ANTI_BOXING_R12_ADV_004_GOAL_PROMPT_2026-05-12.md` - starter `research/science_program_2026_05/06_outcome_testing/scid_noapi_cross_domain_anti_boxing_route_intake/SCID_ANTI_BOXING_R12_ADV_004_STARTER_2026-05-12.txt`

## Required Work

- Recompute from disk that G12 accepted the intake as control evidence only.
- Rank the 12 child routes for parallel or staged execution using source feasibility, cross-domain coverage, dependency leverage, verifier strength, and risk of accidental evidence-class crossing.
- Preserve the anti-boxing horizon: current GTOS OB/retest logic is not the full research horizon, and examples are not limits.
- Do not under-rank a route merely because it is novel, non-OB, cross-domain, proxy/context-heavy, failure-anatomy-derived, or outside current production behavior.
- Pursue same-evidence-class sequencing blockers inside this route; if a blocker cannot be closed, reduce it to an exact dependency/source/access/prompt requirement rather than a vague deferral.
- Preserve all hard boundaries. Do not open validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/live-restart/live-behavior/trading-risk-safety-prompt-decision changes.
- Do not launch any child route. Emit only a sequencing ledger and one-line starters for the chosen waves if needed.

## Required Outputs

Create a scoped G0 route under `research/science_program_2026_05/06_outcome_testing/g0_scid_anti_boxing_child_route_sequencing/` with route-ranking ledger, parallel/staged wave plan, dependency ledger, anti-boxing saturation ledger, adjacent-route follow-up ledger if discovered, no-leak/forbidden-surface audit, completion audit, verifier, and focused tests.

## Mandatory Instruction Coverage And Maximum-Horizon Pass

The completion audit must prove active use of the hardening context rather than chat memory. It must state:

- that live state was regenerated and `goal_session_research_discipline.md`, `research_operating_doctrine.md`, `research_current_state.md`, `local_heavy_data_inventory.md`, and `ai_in_loop_cost_control_research_plan.md` were read;
- that this lane is a G0 sequencing/control route, not a child-route execution, validation, scoring, or promotion route;
- which anti-boxing questions were applied across all 12 child routes and any adjacent routes found in the accepted intake artifacts;
- why the chosen sequencing maximizes breadth, creativity, source feasibility, parallel throughput, and evidence-class cleanliness instead of defaulting to current GTOS/OB/retest ideas;
- every same-evidence-class sequencing blocker pursued, and the exact dependency/source/access/prompt requirement for anything not cleared;
- the exact one-line starter messages and `codex --enable goals` commands for the recommended child-route wave(s).

The 12 accepted child routes are the first wave, not the horizon. If the artifacts expose additional lawful route families, preserve them in an adjacent-route follow-up ledger with denominator and evidence-class boundaries intact.

## Safe Flags

`NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Completion Standard

Complete only when all 12 child routes are ranked from disk evidence, the sequencing is broad rather than boxed, no child route is launched, same-evidence-class blockers are pursued, hard boundaries are closed, verifier/focused tests pass, and any remaining blocker is exact and actionable.
