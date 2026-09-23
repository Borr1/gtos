# Wave3 Lane 09: Market Whiteboard V2

You are the Wave3 `market_whiteboard_v2` goal session for GTOS final moonshot after the broker-real hard halt.

This is a production-code integration and source-repair lane. It is not a chat summary, not a conservative audit, not Wave2 completion acceptance, and not a live deployment lane. Operate at maximum practical reasoning depth. Use as much local computation, code/config/test editing, artifact production, verification, and scoped committing as needed inside the hard boundaries. The boundaries are rails, not brakes: never use them to avoid source-safe local implementation, replay, diagnostics, geometry binding, source repair, or artifact production that this lane can lawfully complete.

The target is the ultimate final GTOS system, not a cautious patch around the old failure. Push this lane as far as its evidence class allows across trade quality, win rate, broker-net expectancy, entry precision, path behavior, exits, allocator competition, same-symbol lifecycle, probability/debate, confluence, replay, and feature/label capture. Quality does not mean passivity: zero-trade is correct only when no candidate deserves risk, while valid scale, reduce, close, reverse, wait, and best-trade allocation opportunities must be made explicit and testable.

Use only context that changes the lane's decisions, implementation, verification, or evidence boundaries. Remove context-pollution from route artifacts and closeouts: stale hashes, old launch status, obsolete blockers, historical paths, storage-constraint psychology, generic warnings, and copied background prose do not belong unless they are explicitly labeled historical and materially affect the lane. Examples are starting points, not limits.

## Mandatory Preflight

Before making any claim or edit:

1. Run `python3 scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`, `.context/00_core/current_vnext_system_map.md`, `.context/00_core/current_repo_reading_order.md`, `.context/00_core/quick_reference_card.md`, `.context/00_core/final_moonshot_post_hard_halt_research_plan.md`, `.context/00_core/final_moonshot_goal_session_execution_architecture.md`, `.context/00_core/final_moonshot_central_orchestrator_successor_brief.md`, `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/orchestrator_successor_operating_brief.md`, `.context/00_core/orchestrator_methodology_hardening_controls.md`, and `.context/00_core/parallel_goal_merge_playbook.md`.
3. Verify and record `git branch --show-current`, `git rev-parse HEAD`, `git rev-parse main`, `git rev-parse origin/main`, `git worktree list`, and `git status --short`.
4. Read this prompt, the one-line starter, and the latest route artifacts again after any compaction, resume, interruption, uncertainty, tool crash, or surprising disk state. Do not rely on chat memory.

Treat `goal_session_research_discipline.md` and `research_operating_doctrine.md` as active instructions, not background. Operationalize curiosity, truthfulness, active creativity, result materialization, full same-evidence-class pursuit, and no conservative brake in the route ledger, searched-root ledger, verifier, and completion audit.

After reading required context, extract the lane-relevant operating rules into the route context anchor and stop carrying irrelevant background forward. The completion audit must show how the context changed the work, not merely list files read.

## Branch And Route Contract

- Lane: `market_whiteboard_v2`
- Launch order: `9`
- Branch: `wave3-market-whiteboard-v2-2026-06-04`
- Worktree: `/Users/borr/Documents/gtos/worktrees/wave3-market-whiteboard-v2-2026-06-04`
- Route directory: `research/operations/wave3_market_whiteboard_v2_2026_06_04`
- Evidence class: production-code integration plus source-bound repair and replay/design fixtures.
- RESULT_MATERIALIZATION_REQUIRED
- validation_result_status=false until this lane explicitly builds a sealed validation artifact.
- outcome_result_rows_status=false unless this lane is the validation/replay lane and freezes partitions first.
- broker_runtime_change_status=false.

These boundary fields prevent evidence-class inflation; they do not cap local research depth, implementation ambition, replay construction, source extraction, feature/label capture design, or V4 code/config/test materialization inside the authorized surfaces.

Authorized local repo surfaces:

- production code
- runtime code
- config
- prompts
- risk and safety gates
- canary and watchdog code
- selector/scheduler/execution logic
- profiles and launchers
- tests, verifiers, manifests, and route artifacts

Forbidden without separate owner approval:

- live trading deployment
- broker operation
- broker account/order/history/deal/position mutation
- credential mutation or disclosure
- paid API/vendor calls
- active VPS process changes
- remote push

Actively pursue relevant read-only local data extraction, including local MT5/cache/source inspection, when it can strengthen this lane; label exact versus proxy source status. Do not treat absent worktree data as a final blocker before checking approved local roots and route artifacts. Do not mutate broker/account/order/history/deal/position state. Do not copy redacted_account lots, fill prices, cash PnL, commission, swap, specs, sessions, lifecycle truth, or broker-local facts into FTMO truth. FTMO must remain target-broker-local truth.

## Wave2 Provenance

This lane is derived from repaired Wave2 evidence, not from stale chat steering and not from the rejected old prompt pack. The provenance below is mandatory and must survive into the route manifest, completion audit, and verifier:

```json
{
  "derived_from_broker_rows": [
    "WAVE2_EVERY_TRADE_CAUSAL_MICROSCOPE.jsonl:77_rows"
  ],
  "derived_from_candidate_rows": [
    "WAVE2_EVERY_CANDIDATE_CAUSAL_MICROSCOPE.jsonl:471_wave1a_candidate_rows_plus_12775_live_authority_rows"
  ],
  "derived_from_code_config_paths": [
    "config/agent_config.yaml",
    "src/components/orchestrator.py",
    "src/components/execution.py",
    "src/components/permissions.py"
  ],
  "derived_from_interaction_ids": [
    "W2INT-006"
  ],
  "derived_from_question_ids": [
    "W2Q_BAD_MARKET_VS_SYSTEM",
    "W2Q_DOMINANT_DAMAGE_SYMBOL_QUARANTINE"
  ],
  "derived_from_source_gaps": [
    "WAVE2_BLOCKER_AND_REPAIR_LEDGER.jsonl",
    "WAVE2_ALLOCATOR_WINDOW_SOURCE_COVERAGE_AUDIT.jsonl",
    "WAVE2_SLTP_MODIFY_LIFECYCLE_SOURCE_COVERAGE_LEDGER.jsonl",
    "WAVE2_PATH_REPAIR_SOURCE_COVERAGE_AUDIT.jsonl"
  ]
}
```

Common Wave2 inputs to read from disk:

- `research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_FINAL_MASTER_STATE_TABLE.json`
- `research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_FULL_SYSTEM_CAUSAL_MODEL.json`
- `research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_CONTRADICTION_REPAIR_LEDGER.jsonl`
- `research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_ACTIVE_CAUSAL_QUESTION_STACK.jsonl`
- `research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_QUESTION_COVERAGE_SATURATION_LEDGER.jsonl`
- `research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_EVERY_TRADE_CAUSAL_MICROSCOPE.jsonl`
- `research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_EVERY_CANDIDATE_CAUSAL_MICROSCOPE.jsonl`
- `research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_SAME_SYMBOL_LIFECYCLE_OWNERSHIP_CONTRACT.json`
- `research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_PROBABILITY_DEBATE_ENGINE_CONTRACT.json`
- `research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_FOLLOW_AVOID_MIXED_NUMERIC_CONFLUENCE_CONTRACT.json`
- `research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_WAVE4_WAVE5_ML_OWNERSHIP_CONTRACT.json`
- `research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_FEATURE_LABEL_STORE_CONTRACT.json`
- `research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_MODEL_REGISTRY_AND_CHALLENGER_CONTRACT.json`
- `research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_LONG_RUNNING_LOCAL_TRAINING_CONTRACT.json`
- `research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_DOWNSTREAM_OWNERSHIP_MAP.json`
- `research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_FULL_LEDGER_COVERAGE_AUDIT.json`
- `research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_MARKET_DATA_GAP_PROXY_REPAIR_SUMMARY.json`
- `research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_COST_SOURCE_COVERAGE_AUDIT.jsonl`
- `research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_PENDING_NOFILL_SOURCE_COVERAGE_SUMMARY.json`
- `research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_V3_VALIDATION_AI_DUAL_BROKER_DISPOSITION_SUMMARY.json`

Required lane inputs from the contract:

- `WAVE2_DOWNSTREAM_OWNERSHIP_MAP.json`
- `WAVE2_FULL_SYSTEM_CAUSAL_MODEL.json`

## Mandatory Semantic Ownership Map

The central orchestrator rejected the earlier Wave2 prompt pack as mechanically verified but semantically incomplete. This repaired prompt is generated from the Wave2 continuation repair and must not treat the old 16-lane pack as accepted.

Every Wave3 lane must preserve these ownership contracts, even when the lane is not the first-class implementer:

1. Same-symbol and same-instrument lifecycle is first-class. The lane `same_symbol_same_instrument_lifecycle_v4` owns same-direction scale-in, opposite-direction close/reverse, long/short conflict, open trade versus new candidate competition, ticket-bound lifecycle state, pending/partial/BE/trailing/stale-thesis state, broker-local risk, and no ambiguous hedge or duplicate exposure.
2. Probability and debate-team engine is first-class. The lane `probability_debate_team_engine_v4` owns calibrated probability and numeric competing theses for long, short, no-trade, wait, scale, reduce, close, and reverse. It must define EV, uncertainty, veto logic, missing-source penalties, confidence calibration, disagreement handling, and final action selection against alternatives.
3. FOLLOW/AVOID/MIXED confluence is numeric, not categorical permission. The lane `follow_avoid_mixed_numeric_confluence_v4` owns direction, strength, confidence, reliability history, evidence class, freshness, cost sensitivity, conflict reason, and source completeness for every confluence source. FOLLOW is not automatic trade permission. AVOID invalidation type must be explicit. MIXED structured disagreement must replace vague middle-state wording.
4. ML ownership is separate from AI reliability. Wave4/Wave5 own Feature Store, Label Store, Digital Twin, ML baselines, model registry, challenger models, training workers, walk-forward validation, leakage guards, calibration metrics, Brier, ECE, reliability bins, logloss, promotion/demotion gates, and long-running local training. The AI reliability lane may own LLM schema/budget/fallback behavior, but it must not bury ML under AI reliability.

Downstream label obligations include broker-real PnL/cash, exact-R, proxy-R, MFE, MAE, time-to-profit, time-to-destination, giveback, stale thesis, stop/target efficiency, harvest failure, and opportunity cost. If a lane touches decisions that can later become ML labels, it must emit source/as-of safe feature and label capture requirements instead of post-hoc labels.


## Objective

build all-symbol market-state memory that separates bad market, bad system, and market-system mismatch using source-bound M1/tick/spread/session/volatility/correlation inputs.

The Wave2 source-class repair evidence proves: 77 recent broker-real redacted_account GTOS trades netted `-859.69`, broker deal/order costs are joined for all 77 positions, shadow slippage prices are available for 70 positions and source-gapped for 7, pending/no-fill lifecycle has 877 reconciled rows with non-generatable historical truth separated, V3 full live authority is rejected, useful V3 components are active/staged/research-only/rejected by label, AI is a measured subsystem rather than a brute-force historical backtest actor, and dual-broker no-copy rules are mandatory.

Do not redo Wave1 or Wave2 for ceremony. If a concrete upstream source defect, stale contradiction, missing row, or unresolved source requirement affects this lane, repair it or bound it with exact proof, then continue building. Build the strongest V4 implementation or source-repair package this lane owns. Same-evidence-class blockers must be pursued until repaired, proven impossible from approved local/source-bound inputs, or reduced to exact owner/access/source/capture requirements. A blocker ledger, next prompt, or clean fail-closed label is not completion when repair is possible.

## Required Work

- Read current code before claiming current behavior.
- Preserve all material rows; no arbitrary top-N, small-number cap, representative-only truncation, or summary-only closure.
- Treat this lane's named outputs as an output floor, not a ceiling. Add every lane-owned artifact, fixture, source contract, test, verifier, code/config surface, and decision ledger discovered by saturation.
- Pursue every lane-owned question raised by the hard-halt evidence and this lane's sources, including trade quality, win-rate/expectancy/frequency tradeoff, entry timing, MFE/MAE, time-to-profit, time-to-destination, giveback, stale thesis, stop/target efficiency, static-R/target-distance/stop-width geometry, same-symbol lifecycle, probability/debate, numeric confluence, cost/swap/slippage, broker constraints, replay, and ML feature/label capture where relevant to the lane.
- Actively ask what the current system misses because it is too loose, too static, too late, too slow, too clustered, too cost-blind, too dependent on 2R-style destination assumptions, poor at harvesting partial directional movement, or too boxed by existing GTOS edge families.
- Do not convert the owner's trade-quality concern into a system that refuses to trade. Convert it into calibrated probability, stricter admission, better entries, better exits, best-trade allocation, ticket-bound lifecycle actions, and explicit no-trade only when the evidence says risk is not deserved.
- Do not optimize for speed, compactness, or a clean-looking closeout. Use chunking, checkpointing, local scripts, repeated passes, and route-local context anchors before accepting shallow substitutes.
- Search local route artifacts, `src`, `config`, `tests`, `scripts`, `shadow_logs`, `pipeline_state`, broker truth routes, accepted Wave1 routes, Wave2 ledgers, local heavy-data roots, and read-only MT5/source caches when relevant before accepting a missing-data blocker.
- Separate broker-real cash/PnL, exact-R, proxy-R, replay, simulation, shadow, live authority, default-off research, production code, source gap, and prospective capture requirement.
- Define source completeness, no-leak/as-of rules, duplicate policy, partition/holdout requirements, cost/slippage stress, rollback path, runtime evidence contract, and semantic ownership handoff.
- Materialize code/config/tests/verifiers where this lane owns production-code integration. Default-off is allowed only with config authority, promotion test, and exact remaining requirement.
- Record production code disposition for every touched component: `active`, `staged_default_off`, `research_only`, or `rejected`.
- Produce a scoped commit when the route is complete, with `Co-Authored-By: Codex GPT-5 <redacted@example.com>`. Do not push.

Required output floor, not a ceiling:

- Market Whiteboard V2 state contract
- symbol/session damage and quarantine rules
- zero-trade quality fixtures
- focused market-state tests and verifier

## Verification

Verification floor, not a ceiling:

- `python3 -m py_compile` for new or changed Python files.
- Focused pytest or focused script verifiers for touched code paths.
- A route verifier that parses every JSON/JSONL artifact and checks row counts, statuses, source-boundary labels, forbidden-surface absence, prompt/instruction coverage, and semantic ownership coverage.
- `python3 scripts/audit_goal_route_artifacts.py research/operations/wave3_market_whiteboard_v2_2026_06_04 --full-jsonl` after creating the route directory.
- `git status --short` and `git diff --cached --name-only` before committing.

Add every other focused test, replay check, source scan, static scan, and verifier this lane's code/config/artifacts make relevant. If an environment issue prevents a command, record the exact command, error, why it is environment friction rather than a code failure, and the strongest fallback verification actually run.

## Completion Standard

Complete means saturation, not "enough". Mark this lane complete only when all owned artifacts, code/config/test/verifier changes, manifest, saturation self-red-team, instruction coverage, production-disposition rows, source-gap rows, semantic ownership rows, focused tests, and newly discovered lane-owned implementation paths are complete, repaired, or exactly bounded. The completion audit must state:

- `goal_session_research_discipline.md` and `research_operating_doctrine.md` were read after preflight.
- This lane's builder/integration posture and anti-boxing questions actually pursued.
- The exact proof-or-impossibility stop condition used.
- Every same-evidence-class blocker repaired or exactly bounded.
- Every semantic ownership dependency either implemented or handed to its first-class owner with exact contract evidence.
- Every forbidden surface remained untouched.
- V4 implementation/deployment boundary status remains broker_runtime_change_status=false unless the owner separately approved live deployment.
- Every newly discovered lane-owned question was pursued, not parked as vague future work.
- Irrelevant context was removed or quarantined as historical/context-only instead of copied into active launch or completion artifacts.
