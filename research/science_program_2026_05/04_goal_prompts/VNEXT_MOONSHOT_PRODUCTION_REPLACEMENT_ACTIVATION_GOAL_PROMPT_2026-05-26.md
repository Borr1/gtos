# vNext Moonshot Production Replacement Activation Goal Prompt

Route id: `vnext_moonshot_production_replacement_activation_2026_05_26`

This is the controlling prompt for the next long-running goal session. The objective is to replace current GTOS production decision behavior with evidence-backed vNext/moonshot behavior and end with the vNext production activation configuration applied when semantic gates pass. Old GTOS is the baseline comparator and rollback implementation. vNext/moonshot is the target implementation.

Required terminal deliverables: production runtime code, config, tests, replay verifiers, semantic verifiers, activation package, applied vNext production activation config overlay after gates pass, rollback proof, scoped commits, and route-local evidence artifacts. Standalone wrappers, anatomy reports, summaries, question packs, inert route states, and unresolved activation dossiers are intermediate artifacts and cannot satisfy the route by themselves.

## Instruction Authority

This prompt and its starter are the active execution contract. When prior prompts, handoffs, reports, closeout messages, route state files, completion audits, or chat summaries conflict with this prompt, use this prompt's route invariants and completion gates for this route. System/developer instructions and external-surface limits still apply.

Do not rely on chat memory. Disk evidence wins over chat memory. Closeout prose is a claim, not proof. Every claim must be verified from local files, code, config, replay shards, ledgers, summaries, tests, verifiers, git state, and route artifacts.

Examples in this prompt are starting points, not limits. Listed artifacts are mandatory starting points, not the entire search space. Listed stages are the mandatory floor, not the ceiling. Listed questions are a seed stack, not a cap. Current GTOS frameworks are baselines, not the horizon.

No arbitrary top-N. Do not cap questions, partitions, rows, failure families, source roots, candidate-origin families, exit policies, branches, blockers, opportunities, ML features, AI validation strata, or findings at 3, 5, 10, 15, 20, or any convenient number. Ranked summaries require complete machine-readable ledgers preserving all material rows and every material class.

Completion validity invariant: a route directory, verifier, completion audit, state refresh, wrapper ledger, prompt, or next-route file is insufficient when same-evidence-class repair remains possible. If code can be wired, a source can be searched, a parser can be fixed, a replay can be rerun, a policy can be simulated, a static assumption can be audited, a question can be answered, or a downstream metric can be recomputed inside this evidence class, execute that action and record the result.

Constructive production-change posture: route boundaries define execution surfaces; they do not reduce the required depth of repo-local implementation, replay, source repair, semantic verification, or activation-package work. Prop logic must optimize expected value and opportunity cost under challenge constraints. A prop rule can block, resize, defer, abandon, or restart when the branch-level and account-attempt evidence proves that action dominates the available alternatives.

Full same-evidence-class pursuit is mandatory. Literal impossibility means exactly this: every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action inside this evidence class has been executed, or the remaining action requires an external live/broker/paid/API/vendor/remote/history/credential surface or non-generatable historical system-state truth. Missing fields, source gaps, stale hashes, nulls, parser friction, timeout friction, storage friction, broad rows, incomplete verifiers, primitive labels, and disabled flags are work items to repair, replay, recompute, test, or exactly bind; they are not completion labels.

## Route Execution Surface

This route operates on repo-local code, config, tests, replay builders, verifiers, research artifacts, route-local artifacts, and scoped commits. The final vNext production activation config overlay is part of this route after semantic gates pass.

Allowed and required inside this route:

- read and scan local code, configs, JSON/JSONL/JSONL.gz, CSV, parquet, SCID-derived, Sierra-derived, tick, shadow-log, route-local, research, prompt, and test artifacts;
- use local source roots and local-heavy-data inventories;
- build runtime code, schemas, config flags, loggers, monitors, replay builders, verifiers, tests, route states, ledgers, reports, and activation packages;
- run local tests, focused replays, static checks, artifact audits, row-count/hash checks, no-top-N checks, and semantic verifiers;
- create scoped commits containing intended code/config/test/prompt/artifact changes;
- spawn, use, close, and replace subagents for disjoint runtime, replay, evidence, AI/ML, and review lanes;
- run long local builders/replays with checkpointing, heartbeats, sharding, process audits, and resume logic;
- write row-preserving route-local artifacts with manifests, hashes, and exact restore paths;
- apply the final vNext production activation config overlay after the semantic verifier, replay verifier, runtime tests, rollback proof, monitoring checklist, and scoped commit checks pass;
- build AI calibration manifests, prompt packs, cache keys, schema validators, and spend caps without making paid calls unless a route-state budget cap is present.

External surfaces outside this route execution surface:

- live trading;
- broker/account/order/deal/position/history mutation;
- account-connected runtime process startup;
- paid API/vendor/model calls without a route-state budget cap;
- credential changes;
- remote push;
- destructive source deletion;
- Git history rewrite or LFS migration that rewrites committed history.

External surfaces do not reduce repo-local deliverables. A live/broker/account surface does not change the requirement to produce the tested activation package and applied config overlay. A paid-AI surface does not change the requirement to build the AI calibration manifest, prompt pack, cache-key verifier, schema verifier, budget estimate, and activation-impact split. A source-capture surface does not change the requirement to wire forward capture now when the runtime can capture it prospectively.

## Mandatory Context Use

At start, after any resume, after context compaction, after interruption, after timeout, after command denial, after a long command, after any failed command, before selecting a new stage, before committing, and before marking complete:

1. Run `py -3 scripts/generate_live_state.py` or `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read this prompt.
4. Read the starter file:
   `research/science_program_2026_05/04_goal_prompts/VNEXT_MOONSHOT_PRODUCTION_REPLACEMENT_ACTIVATION_STARTER_2026-05-26.txt`
5. Read and operationalize:
   - `.context/00_core/goal_session_research_discipline.md`
   - `.context/00_core/research_operating_doctrine.md`
   - `.context/00_core/orchestrator_successor_operating_brief.md`
   - `.context/00_core/orchestrator_methodology_hardening_controls.md`
   - `.context/00_core/parallel_goal_merge_playbook.md`
   - `.context/00_core/quick_reference_card.md`
   - `.context/00_core/local_heavy_data_inventory.md`
   - `.context/00_core/ai_in_loop_cost_control_research_plan.md`
6. Read the latest handoff:
   - `.context/02_session_handoffs/SESSION_63_VNEXT_EXACT_R_SOURCE_REPAIR_GUARD_HANDOFF_2026-05-19.md`
7. Read active runtime/config/test surfaces before interpreting or changing behavior:
   - `config/agent_config.yaml`
   - `src/components/gtos_vnext_runtime.py`
   - `src/components/orchestrator.py`
   - `src/components/execution.py`
   - `src/components/j46_j49_policy.py`
   - `src/research/moonshot_default_off_policy_router.py`
   - `src/components/market_state.py`
   - `src/components/primary_analyzer.py`
   - `src/components/pre_ai_gates.py`
   - `src/components/permissions.py`
   - `src/components/ai_supervisor.py`
   - relevant shadow loggers and monitors for candidate features, path contracts, BE, partial close, trailing, J46/J49, time-in-trade, slippage, pending lifecycle, no-fill, orderflow, displacement, malformed responses, source capture, and live monitor.
8. Read the required vNext evidence artifacts listed below.
9. Inspect `git status --short`, unstaged/staged diffs, and large-file/storage state.
10. Identify the first incomplete invariant from the route state and continue there.

"Read" means apply the information to decisions. The final completion audit must include prompt hash, starter hash, current HEAD, exact artifacts read, exact row counts scanned, exact source roots searched, exact files changed, exact files deliberately left untouched, exact tests/verifiers run, exact budget-cap state, exact external-surface handoff state, and exact completion-gate result.

## Required Evidence Artifacts

Read these exact routes and then search neighboring artifacts when needed. Treat `.context/00_core/research_current_state.md` as stale where it disagrees with 2026-05-25 and 2026-05-26 artifacts.

Full historical replay:

- `research/science_program_2026_05/06_outcome_testing/vnext_full_historical_candidate_generation_replay_2026_05_24/VNEXT_FULL_REPLAY_FINAL_REPORT_2026-05-24.md`
- `research/science_program_2026_05/06_outcome_testing/vnext_full_historical_candidate_generation_replay_2026_05_24/VNEXT_FULL_REPLAY_CANDIDATE_GENERATION_SUMMARY_2026-05-24.json`
- `research/science_program_2026_05/06_outcome_testing/vnext_full_historical_candidate_generation_replay_2026_05_24/VNEXT_FULL_REPLAY_STAGE04_SOURCE_MODE_SUMMARY_2026-05-24.json`
- `research/science_program_2026_05/06_outcome_testing/vnext_full_historical_candidate_generation_replay_2026_05_24/VNEXT_FULL_REPLAY_STAGE06_FINAL_SUMMARY_2026-05-24.json`
- every Stage01-Stage06 builder, verifier, manifest, row shard, final report, and completion audit needed to trace candidate generation, source modes, M1/LTF path truth, runtime labels, dominance, MIXED, and terminal metrics.

Failed production-change route and forensic accountability:

- `research/science_program_2026_05/06_outcome_testing/vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25/VNEXT_PRODUCTION_CHANGE_FORENSIC_ACCOUNTABILITY_REPORT_DO_NOT_ACTIVATE_2026-05-25.md`
- Stage09/Stage10 builders, tests, verifiers, replay shards, metrics summary, completion audit, activation dossier, and any route-control/nudge ledger from that route.

Repaired production-candidate and EV prop governor route:

- `research/science_program_2026_05/06_outcome_testing/vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25/VNEXT_PRODUCTION_CANDIDATE_REPAIR_DECISION_DOSSIER_2026-05-25.md`
- `research/science_program_2026_05/06_outcome_testing/vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25/VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE02_ACCEPTANCE_GATE_REPAIR_SUMMARY_2026-05-25.json`
- `research/science_program_2026_05/06_outcome_testing/vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25/VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE03_EXECUTABLE_STREAM_SEMANTICS_SUMMARY_2026-05-25.json`
- `research/science_program_2026_05/06_outcome_testing/vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25/VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE05_AVOID_PRE_AI_REPAIR_SUMMARY_2026-05-25.json`
- `research/science_program_2026_05/06_outcome_testing/vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25/VNEXT_PRODUCTION_CANDIDATE_REPAIR_REPLAY_METRICS_SUMMARY_2026-05-25.json`
- Stage08 repaired decision ledger, prop attempt ledger, Stage10 addendum, AI sensitivity artifacts, accepted missing-source ledgers, and verifiers.

Activation edge anatomy, AI budget, and ML feasibility route:

- `research/science_program_2026_05/04_goal_prompts/VNEXT_ACTIVATION_EDGE_ANATOMY_AI_BUDGET_ML_FEASIBILITY_GOAL_PROMPT_2026-05-26.md`
- `research/science_program_2026_05/06_outcome_testing/vnext_activation_edge_anatomy_ai_budget_ml_feasibility_2026_05_26/VNEXT_ACTIVATION_FINAL_REPORT_2026-05-26.md`
- `research/science_program_2026_05/06_outcome_testing/vnext_activation_edge_anatomy_ai_budget_ml_feasibility_2026_05_26/VNEXT_ACTIVATION_COMPLETION_AUDIT_2026-05-26.json`
- `research/science_program_2026_05/06_outcome_testing/vnext_activation_edge_anatomy_ai_budget_ml_feasibility_2026_05_26/VNEXT_ACTIVATION_QUESTION_STACK_LEDGER_2026-05-26.jsonl`
- `research/science_program_2026_05/06_outcome_testing/vnext_activation_edge_anatomy_ai_budget_ml_feasibility_2026_05_26/VNEXT_ACTIVATION_SUBSET_CANDIDATE_SUMMARY_2026-05-26.json`
- `research/science_program_2026_05/06_outcome_testing/vnext_activation_edge_anatomy_ai_budget_ml_feasibility_2026_05_26/VNEXT_ACTIVATION_PROP_EV_ANATOMY_SUMMARY_2026-05-26.json`
- `research/science_program_2026_05/06_outcome_testing/vnext_activation_edge_anatomy_ai_budget_ml_feasibility_2026_05_26/VNEXT_ACTIVATION_ML_CHALLENGER_RESULTS_2026-05-26.json`
- every Stage00-Stage11 verifier result, report, manifest, builder, shard, partition ledger, block/miss ledger, AI budget manifest, ML role ledger, and final audit needed to answer the question stack without summary substitution.

Moonshot substrate and dynamic execution repair route:

- `research/science_program_2026_05/04_goal_prompts/VNEXT_MOONSHOT_SUBSTRATE_DYNAMIC_EXECUTION_REPAIR_GOAL_PROMPT_2026-05-26.md`
- `research/science_program_2026_05/06_outcome_testing/vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/VNEXT_MOONSHOT_FINAL_REPORT_2026-05-26.md`
- `research/science_program_2026_05/06_outcome_testing/vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/VNEXT_MOONSHOT_STAGE04_DYNAMIC_POLICY_REPLAY_SUMMARY_2026-05-26.json`
- `research/science_program_2026_05/06_outcome_testing/vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/VNEXT_MOONSHOT_CORRECTED_BRANCH_SUMMARY_2026-05-26.json`
- `research/science_program_2026_05/06_outcome_testing/vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/VNEXT_MOONSHOT_RUNTIME_INTEGRATION_MAP_2026-05-26.json`
- `research/science_program_2026_05/06_outcome_testing/vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/VNEXT_MOONSHOT_COMPLETION_AUDIT_2026-05-26.json`
- `research/science_program_2026_05/06_outcome_testing/vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/VNEXT_MOONSHOT_NEXT_PRODUCTION_CHANGE_OR_VALIDATION_PLAN_2026-05-26.md`
- `research/science_program_2026_05/06_outcome_testing/vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/VNEXT_MOONSHOT_UNIVERSAL_CANDIDATE_ORIGIN_REGISTRY_2026-05-26.jsonl`
- `research/science_program_2026_05/06_outcome_testing/vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/VNEXT_MOONSHOT_CANDIDATE_ORIGIN_BOXING_AUDIT_LEDGER_2026-05-26.jsonl`
- `research/science_program_2026_05/06_outcome_testing/vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/VNEXT_MOONSHOT_STAGE11_CONDITION_ROUTER_INTEGRATION_MAP_2026-05-26.json`
- `research/science_program_2026_05/06_outcome_testing/vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/VNEXT_MOONSHOT_FORWARD_CAPTURE_REQUIREMENTS_2026-05-26.jsonl`
- `research/science_program_2026_05/06_outcome_testing/vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/VNEXT_MOONSHOT_SOURCE_PATH_CAPABILITY_SUMMARY_2026-05-26.json`
- Stage04 dynamic policy shards, Stage10 router replay, Stage11 condition replay, refusal split, question stack, self-red-team, final semantic verifier, tests, and route control ledger.

Research-to-runtime conversion and weekend factory roots:

- `research/gtos_vnext_research_to_runtime_builder/GTOS_VNEXT_MASTER_INTELLIGENCE_TO_RUNTIME_CONVERSION_SUMMARY_2026-05-18.json`
- `research/gtos_vnext_research_to_runtime_builder/GTOS_VNEXT_FINAL_CONVERSION_FREEZE_REPORT_2026-05-23.md`
- `research/science_program_2026_05/04_goal_prompts/GTOS_VNEXT_72H_RESEARCH_TO_RUNTIME_BUILDER_TRANSLATOR_EXECUTIONER_GOAL_PROMPT_2026-05-18.md`
- row-bearing weekend artifacts under `research/weekend_mechanical_edge_factory_moonshot_2026_05_15/`, especially challenger frontier, control screen, unified numeric result ledgers, source geometry repair ledgers, recommendation merge bundles, expanded-market ledgers, runtime candidate bundles, and every artifact that maps conversion findings to runtime candidates.

The file list above does not limit the search. Use `rg`, route manifests, git history, builder imports, tests, and neighboring route outputs to find any vNext, CP280/CP281/CP282, READY8, SCID, J46/J49, dynamic-execution, source-capture, AI-budget, ML-feasibility, follow/avoid, MIXED, LEGACY, prop-governor, or candidate-origin artifact that matters.

## Starting Facts To Recompute From Disk

Recompute these before citing them in final artifacts. They are anchors, not unverified final numbers.

- Current HEAD after the last completed moonshot route: `00b14c6d3 research: complete moonshot final decision stage`.
- Current config has `gtos_vnext_runtime.enabled: true`, but `gtos_vnext_runtime.apply_to_execution: false`.
- Current config has moonshot router flags disabled/off for execution.
- Current config has pre-AI apply off, AI policy apply off, LTF execution apply off, prop selector apply off, and many vNext surfaces set to log/diagnostic rather than execution effect.
- Production orchestrator calls vNext pre-AI, post-L2, risk, pending policy, LTF path, prop selector, and logging, but execution effect is gated by config.
- `src/research/moonshot_default_off_policy_router.py` is not production-wired into `src/components/orchestrator.py` or `src/components/gtos_vnext_runtime.py`.
- Current runtime labels exist, but AVOID/MIXED/LEGACY affect production according to config; MIXED and LEGACY have been mostly inert.
- `src/components/execution.py` still routes target/BE behavior through J46/J49 policy surfaces; dynamic execution is not primary production behavior until wired.
- Active `risk.min_rr` has been `1.5`, and older replay/anatomy logic used fixed target/stop labels too often as if they were moonshot execution.

Universe and replay anchors:

- M15 denominator rows: `903,163`.
- Generated vNext candidate rows: `253,234`.
- Dynamic moonshot replayable rows: `214,536`.
- Framework candidate rows: `fvg_fill 106,679`, `ob_retest 77,053`, `breaker_re_entry 69,502`.
- Full replay symbols: `AUDJPY`, `AUDUSD`, `BTCUSD`, `CHFJPY`, `ETHUSD`, `EURGBP`, `EURJPY`, `EURUSD`, `GBPJPY`, `GBPUSD`, `GER40`, `JP225`, `NAS100`, `NZDUSD`, `SPX500`, `UK100`, `UKOIL_cash`, `US30_cash`, `USDCAD`, `USDCHF`, `USDJPY`, `USOIL_cash`, `XAGUSD`, `XAUUSD`.
- Source modes included `OHLC_M1_CSV`, `SIERRA_SCID_CONVERTED_M1_PROXY`, `MISSING_SOURCE`, `OHLC_M15_CSV`, `LOCAL_TICK_PARQUET`, and `OHLC_M5_CSV`.

Failed production-change route anchors:

- Failed route selected `10 / 253,234`.
- Failed route total R about `-4.999959`, expectancy about `-0.499996`, WR `20%`, PF about `0.375005`, missed winners `104,440`, blocked `216,161`.
- Baseline/current shadow selected `35,983`, total R about `+4008.331701`, expectancy about `+0.118432`, WR about `44.7658%`, PF about `1.214657`.
- Failed route blocked `15,150` baseline-selected winners and about `+4011.831701R`.
- This collapse was caused by bad acceptance gates, continuous-account prop replay modeling, route semantics bugs, and verifier/completion failure. It is a mandatory negative fixture.

Repaired production-candidate anchors:

- Repaired executable stream: `79,320` rows.
- Best repaired prop policy: `ACCOUNT_ABANDON_OR_RESTART`.
- Best repaired selected rows: `22,270`; performance rows `21,727`; total R about `2434.896089846658`; risk-adjusted R about `2429.284061660785`; expectancy about `0.11206775394`; WR about `0.445022322456`; PF about `1.202010371798`; pass rate about `0.497753818509`; account loss/abandon about `0.501347708895`; EV/attempt about `$3681.72327` at fee `599` and payout `8000`.
- High-quality branch: `15,067` rows, expectancy about `0.15711019407556978`, PF about `1.2926588415077604`, source-missing `0`.
- Aggressive branch: `30,476` rows, expectancy about `0.5077132399926312`, PF about `2.280095658733947`; treat as research-intelligence requiring exact no-leak and source validation before production.
- AI required after best prop accept: `22,270`; pre-prop rows `79,320`; prop block/defer saved `57,050`; paid calls made `0`.
- Accepted missing-source rows: `457` must be captured, repaired, or excluded before activation.

Moonshot execution anchors:

- Old `live_current_j46_j49` expectancy about `0.180218109252` over `214,536` replayable rows.
- Fixed `1.5R` / AI-target expectancy about `0.376515139412`.
- Global `be_after_trigger` expectancy about `0.389471600193`; selected vs old live delta about `+0.209253490941R`.
- `condition_asof_displacement_v1` expectancy about `0.416740877018`; about `+0.027269276825R` vs global BE and about `+0.067283575294R` on primary FVG scope, but local prop replay rejected it as primary prop default.
- Moonshot route candidate selected in latest moonshot route: `moonshot_fvg_be_after_trigger_prop_aware_router`, primary branch `origin_current_fvg_fill`, policy `be_after_trigger`, prop policy `ACCOUNT_ABANDON_OR_RESTART`, replacing `live_current_j46_j49`.
- Stage07 FVG/BE prop stream: `82,509` input rows; `49,002` allowed trades; total R about `28,610.598206027866`; risk-adjusted R about `28,383.3408697874`; expectancy about `0.583865928044`; PF about `3.322860439072`; pass probability proxy about `0.981666130589`; account loss rate about `0.01801222258`; EV terminal day about `$7842.539723`.
- Refused rows: `154,651`; local repairable-now rows `0`; ordered LTF/tick required `115,756`; source-window incomplete `84,187`; forward-capture requirement rows `23`.

Question and anatomy anchors:

- Activation question ledger: `24,327` rows.
- Moonshot final question stack: `24,337` rows.
- Missed winners: `13,073`.
- Avoided losers: `16,815`.
- Selected losers: `12,058`.
- No-fills: `1,817`.
- Timeouts: `5,424`.
- Source-missing rows: `11,631`.
- Partition edge actions include `182 promote`, `393 promote_with_reduced_risk`, `17 AI_validate`, `1,346 ML_rank`, and `5,958 source_repair`. Do not cherry-pick a small subset.

## Replacement Mission

Replace old GTOS with vNext/moonshot in production-ready code and activation packaging. This means:

- old GTOS candidate generation, routing, filtering, AI gate, risk, prop selector, pending/no-fill handling, and exit logic must be explicitly replaced, narrowed, or retained as comparator/rollback with row-level proof;
- vNext FOLLOW/AVOID/MIXED/LEGACY decisions must have production semantics that change runtime decisions under the activation overlay;
- moonshot dynamic execution must run on the runtime path, beyond research builders;
- candidate-origin expansion must leave the old three frameworks as baselines, not the ceiling;
- replay must be rerun under activated-config production semantics, not stale fixed 1.5R or artifact labels;
- prop safety must become prop EV governance with opportunity-cost accounting;
- AI must be calibrated with a small, decisive, budget-capped package rather than brute-forced across every trade;
- ML must become a validated assistant/monitoring module where useful, not an unvalidated controller;
- source gaps must become capture, exclusion, local repair, or exact non-generatable proof;
- final output must include exact config overlays, activation commands, rollback commands, monitoring commands, kill criteria, external-surface handoff fields, and tests/verifiers proving the replacement behavior.

## Runtime Surfaces That Must Be Converted Or Killed

### Current Baseline Frameworks

Retain as baseline comparators and fallback where explicitly justified:

- `ob_retest`
- `fvg_fill`
- `breaker_re_entry`

Do not let these three frameworks define the boundary of vNext. If old GTOS can still place trades under "vNext activated" without an explicit vNext route, fallback label, and measured reason, the replacement is incomplete.

### Candidate-Origin Families To Convert

Build runtime candidate generators, decision modules, source contracts, replay validators, or explicit kill/redesign rows for every viable family:

- `liquidity_sweep_reclaim`
- `displacement_continuation`
- `continuation_no_retrace`
- `nofill_reprice_reentry`
- `volatility_compression_expansion`
- `session_open_range_break`
- `regime_transition_break`
- `orderflow_depth_imbalance_proxy`
- `spread_liquidity_state_shift`
- `news_volatility_reprice`
- `cross_asset_lead_lag`
- `path_hazard_early_failure`
- `structural_distance_extreme`

The current universal origin registry remains an input artifact until runtime modules, schemas, config flags, logs, tests, and replay validators exist. Completion requires the conversion status of every family, with exact reason for implement-now, replay-required, source-capture-required, AI-budget-required, monitor, killed, or activation-config-applied.

### Clock And Source Expansion

Support non-M15 candidate clocks and source contracts for:

- M15 close;
- M5 and M1 event clocks;
- ordered tick/quote path;
- Sierra/SCID-derived context where source-transfer contracts permit it;
- session open/range clocks;
- calendar/news clocks;
- pending-lifecycle clocks;
- fill/modify/close lifecycle clocks for execution management.

Do not treat delayed Sierra data as live trigger truth without a real-time source contract. For live activation, classify each market as broker-native live feed, proxy-context, source-capture required, or excluded until source exists. The 24-market replay universe is the starting universe; the stale seven-market live list is not the replay boundary.

### Dynamic Execution

Replace J46/J49 as primary exit behavior with a vNext dynamic execution layer. Implement config-gated runtime policies and comparators for at least:

- `be_after_trigger` as the current prop-default replacement candidate;
- `condition_asof_displacement_v1` as a challenger with source/proper prop validation requirements;
- `legacy_fixed_1.5r` as a comparator;
- `live_current_j46_j49` as a comparator/rollback;
- `partial_be_runner`;
- `early_cut_if_no_progress`;
- `trailing_runner`;
- `time_stop`;
- `path_aware_exit`;
- `ai_target_validator` where budget-capped calibration supports it.

Dynamic policy state must persist through `PendingLimitIntent`, trade state, order send payloads where needed, trade records, pending lifecycle logs, slippage logs, close logs, restart recovery, monitoring, and replay. Do not allow `j46_j49_policy.is_enabled()` to override a vNext activated policy.

### FOLLOW / AVOID / MIXED / LEGACY Semantics

Define exact production semantics:

- `FOLLOW`: allowed to proceed, size, route, or execute under vNext policy and prop-EV governor.
- `AVOID`: blocks, zero-risks, or route-specific rejects when source-bound avoided-set evidence supports it; broad AVOID with positive avoided-set R fails semantic verification until repaired.
- `MIXED`: routes to constrained AI, defer, reduce risk, require source repair, or block by exact source/ambiguity class.
- `LEGACY`: must become rollback, bounded transition fallback, AI validation input, or explicit no-trade unless a measured vNext rule retains it.

If MIXED and LEGACY remain non-executing labels, the route is not complete.

### Prop EV Governor

Prop rules are constraints, not the objective. The governor must optimize expected value, opportunity cost, pass probability, loss/abandon/restart economics, daily reset, static max-loss floor, internal overlay, open/pending risk, simultaneous candidate reservation, and trade quality. It must not block nearly everything because the account is near a floor unless it proves that blocking has higher EV than reduced-risk, micro-risk, high-quality continuation, defer-until-reset, or abandon/restart.

The failed 10-trade route is the negative fixture. Any new prop governor that collapses trade count or blocks a strongly positive baseline without proof fails semantic verification.

### AI

AI is a constrained validator and resolver, not a reason to stall the mechanical system and not a brute-force tax on every candidate.

Build the AI calibration package before any paid calls:

- selected strata manifest;
- prompt/context packets;
- schema;
- cache key and prompt hash;
- malformed-response handling;
- cost estimate;
- hard spend cap;
- budget-cap execution decision field;
- result verifier;
- false accept/reject smoke metrics.

Default calibration target: a small decisive run, such as 32 calls with a hard `$5` cap. If the route-state budget cap is absent, do not make paid calls. Continue by separating mechanical activation surfaces from AI-dependent surfaces and by producing the exact budget request and activation impact.

### ML

ML is not the live controller unless sealed validation and no-leak tests prove it. Convert useful ML roles into monitored/config-gated assistant modules:

- AI-call reducer;
- source-confidence scorer;
- partition robustness scorer;
- timeout/ambiguous monitor;
- drift detector.

Underpowered candidate-quality, risk, or prop scorers remain monitoring modules until evidence improves. ML must feed decisions through a tested, source-bound, no-leak, config-gated path.

### Source Capture

Implement schemas/loggers/tests for all forward-capture fields required by the moonshot artifacts, including:

- broker order/deal IDs;
- requested and executed entry/exit prices;
- fill time and close time;
- bid/ask ordered path;
- spread;
- slippage;
- commission;
- swap;
- partial close lifecycle;
- BE modify lifecycle;
- trailing modify lifecycle;
- time-stop lifecycle;
- pending order lifecycle;
- cancel/expire lifecycle;
- source join IDs;
- candidate IDs;
- policy hashes;
- prompt hashes;
- AI response IDs where route-state budget-capped calls run;
- runtime branch/policy labels;
- prop governor decision fields;
- source completeness and ambiguity fields.

Never backfill historical broker lifecycle truth from price movement alone. Recover historical market data where possible; treat non-generatable historical system-state truth as prospective capture work, then wire the capture now.

## Stage Plan

Each stage must write or update the route state before and after execution. Each stage must identify its first incomplete invariant and exact next action. Stages can be subdivided; they cannot be skipped because they are required.

### Stage 00 - Preflight, Input Freeze, And State Spine

Create route directory:

`research/science_program_2026_05/06_outcome_testing/vnext_moonshot_production_replacement_activation_2026_05_26/`

Create and maintain:

- `VNEXT_REPLACEMENT_SESSION_STATE_2026-05-26.json`
- `VNEXT_REPLACEMENT_INPUT_FREEZE_MANIFEST_2026-05-26.json`
- `VNEXT_REPLACEMENT_OUTPUT_MANIFEST_2026-05-26.json`
- `VNEXT_REPLACEMENT_CONTROL_LEDGER_2026-05-26.jsonl`

The state must include route id, current stage, first incomplete invariant, exact next action, current HEAD, dirty path summary, prompt/starter hashes, required context hashes, input artifact hashes, row counts scanned, searched roots, output manifest, active question stack, blocker-pursuit status, tests/verifiers run, commits, activation-package status, and completion-gate status.

### Stage 01 - Evidence Reconciliation

Reconcile full historical replay, failed production-change route, repaired EV route, activation anatomy route, moonshot route, conversion freeze, weekend factory, runtime code, config, tests, and shadow logs.

Every upstream claim must be classified as:

- accepted for runtime;
- superseded;
- static/proxy comparator;
- dynamic-valid;
- source-capture required;
- AI-budget required;
- activation-config-applied;
- killed/redesigned with reason.

Output:

- `VNEXT_REPLACEMENT_UPSTREAM_EVIDENCE_RECONCILIATION_LEDGER_2026-05-26.jsonl`
- `VNEXT_REPLACEMENT_EVIDENCE_RECONCILIATION_REPORT_2026-05-26.md`

### Stage 02 - Old GTOS Replacement Map

Enumerate every old GTOS production surface to retire, override, narrow, or retain as rollback:

- candidate origin generation;
- old three-framework routing;
- D1/H4/H1 prescreen;
- static POI assumptions;
- AI gate;
- pre-AI avoid;
- L2 checks;
- J46/J49;
- fixed 1.5R;
- pending/no-fill handling;
- prop/risk/drawdown rules;
- permissions gates;
- monitoring and canary assumptions.

Output:

- `VNEXT_REPLACEMENT_OLD_GTOS_REPLACEMENT_MAP_2026-05-26.json`
- `VNEXT_REPLACEMENT_LEGACY_SURFACE_RETIREMENT_LEDGER_2026-05-26.jsonl`

Failure gate: old GTOS cannot still dominate when vNext activation flags are enabled unless a row-level rollback/fallback rule explicitly says so and a test proves the boundary.

### Stage 03 - Production Candidate Contract

Freeze the vNext production candidate contract:

- candidate origins and source contracts;
- market/session/timeframe/source applicability;
- FOLLOW/AVOID/MIXED/LEGACY semantics;
- dynamic execution policy routing;
- prop EV governor policy;
- AI role and budget gate;
- ML role;
- source-capture requirements;
- activation flags;
- fallback and rollback semantics.

Output:

- `VNEXT_REPLACEMENT_PRODUCTION_CANDIDATE_CONTRACT_2026-05-26.md`
- `VNEXT_REPLACEMENT_PRODUCTION_CANDIDATE_CONTRACT_2026-05-26.json`

### Stage 04 - Runtime Implementation

Implement the replacement in runtime code, beyond research scripts:

- wire moonshot dynamic execution router into `gtos_vnext_runtime.py` and orchestrator path;
- generalize routing beyond hard-coded FVG;
- add universal candidate event schema and origin registry surfaces;
- add config flags for origin families, clocks, dynamic execution, condition router, LTF path, prop governor, AI calibration, ML shadow modules, source capture, and activation overlay;
- implement FOLLOW/AVOID/MIXED/LEGACY production semantics;
- implement dynamic execution policy state and persistence;
- wire LTF path actions into execution under activation flags;
- wire prop governor as an execution modifier under activation flags;
- add monitoring/logging for every runtime effect;
- preserve broker/account/order state while repo activation flags are configured and verified.

Output:

- source/config/test diffs;
- `VNEXT_REPLACEMENT_RUNTIME_INTEGRATION_MAP_2026-05-26.json`
- `VNEXT_REPLACEMENT_RUNTIME_EFFECT_LEDGER_2026-05-26.jsonl`

Changed-behavior proof is mandatory. Tests and/or replay fixtures must prove that when the vNext activation overlay is enabled, production decisions actually change versus old GTOS where the evidence says they should change. If the activated overlay leaves old GTOS behavior dominant, the stage fails.

### Stage 05 - Full Activated Historical Replay

Run full activated-config replay across all available candidates and frameworks/route families. Use the full denominator and full candidate universe. No FVG subset. No top-N. No summary proof without row-preserving ledgers.

Replay must compare:

- old GTOS/current shadow;
- current vNext labels before activation;
- moonshot BE;
- condition router;
- dynamic execution policies;
- LTF path effects;
- prop governor effects;
- AI policy scenarios;
- ML shadow scenarios;
- source-complete and source-missing partitions;
- all markets, sessions, years, symbols, frameworks, candidate-origin families, source modes, and disposition classes.

Output:

- `VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_*`
- row-preserving shards;
- shard manifest;
- hash manifest;
- summary;
- verifier.

Failure gate: selected coverage cannot silently shrink. Source modes cannot collapse. Missing shards fail. Fixed 1.5R cannot be used as final truth unless explicitly labeled as a comparator.

### Stage 06 - Legacy-vs-vNext Delta

Produce candidate-level and branch-level deltas:

- selected count;
- performance count;
- total R;
- expectancy;
- WR;
- PF;
- pass probability proxy;
- drawdown;
- account loss/abandon/restart;
- missed winners;
- avoided losers;
- blocked winners;
- saved losers;
- frequency by symbol/session/day/week/month/year;
- hold time;
- timeout behavior;
- no-fill behavior;
- source completeness;
- old-live leakage.

Output:

- `VNEXT_REPLACEMENT_LEGACY_VS_VNEXT_DELTA_LEDGER_2026-05-26.jsonl`
- `VNEXT_REPLACEMENT_LEGACY_VS_VNEXT_DELTA_REPORT_2026-05-26.md`

### Stage 07 - Question Ledger Closure

Import activation question ledger rows, moonshot question rows, and every new question found in this route. Answer each row explicitly as one of:

- answered with disk evidence;
- superseded with exact artifact;
- implemented;
- killed/redesigned with reason;
- source-capture required;
- AI-budget required;
- activation-config-applied;
- non-generatable historical truth with prospective capture;
- external-surface package required.

No packed statuses. No "TBD". No deferred-action placeholder. No summary replacement for row-level answers.

Output:

- `VNEXT_REPLACEMENT_QUESTION_STACK_LEDGER_2026-05-26.jsonl`
- `VNEXT_REPLACEMENT_QUESTION_CLOSURE_SUMMARY_2026-05-26.json`

### Stage 08 - Source And Market Activation Map

Classify every market from the 24-market replay universe:

- broker-native live feed available now;
- source-complete historical and live;
- proxy-context;
- Sierra delayed context;
- forward-capture required;
- excluded until source exists.

Include the live deployment symbols, but do not limit the route to them. Produce Sierra/SCID/MT5/broker source handling rules for live and replay.

Output:

- `VNEXT_REPLACEMENT_MARKET_SOURCE_ACTIVATION_MAP_2026-05-26.json`
- `VNEXT_REPLACEMENT_SOURCE_CAPTURE_REQUIREMENTS_2026-05-26.jsonl`
- `VNEXT_REPLACEMENT_ACTIVATION_EXCLUSION_LEDGER_2026-05-26.jsonl`

### Stage 09 - AI Calibration Package And Budget-Capped Spend Plan

Build the minimum decisive AI API calibration package:

- prompt and context packets;
- selected strata manifest;
- cache key and prompt hash;
- schema validator;
- malformed-response repair/supervisor path;
- spend estimate;
- hard cap;
- route-state budget-cap field.

If the exact budget cap is present in route state, run the minimum calibration inside that cap and update the activation package. If the route-state budget cap is absent, do not spend and separate mechanical activation from AI-dependent activation.

Output:

- `VNEXT_REPLACEMENT_AI_CALIBRATION_MANIFEST_2026-05-26.json`
- `VNEXT_REPLACEMENT_AI_PROMPT_PACK_2026-05-26.jsonl`
- `VNEXT_REPLACEMENT_AI_SPEND_REQUEST_2026-05-26.md`
- `VNEXT_REPLACEMENT_AI_CALIBRATION_RESULTS_*` when budget-capped calls run.

### Stage 10 - ML And Monitoring Integration

Convert useful ML roles into monitored/config-gated modules:

- AI-call reducer;
- source-confidence scorer;
- partition robustness scorer;
- timeout/ambiguous monitor;
- drift detector.

Add runtime monitoring for:

- vNext apply status;
- router decisions;
- label effects;
- AVOID/MIXED/LEGACY distribution and execution effect;
- dynamic exit transitions;
- LTF pending monitor health;
- prop budget projection;
- source-capture completeness;
- old-live fallback leakage;
- malformed AI responses.

Output:

- `VNEXT_REPLACEMENT_ML_MONITORING_INTEGRATION_MAP_2026-05-26.json`
- monitoring tests and log schemas.

### Stage 11 - Activation Dossier And Config Overlay Application

Build the activation package and apply the vNext production activation config overlay after its gates pass:

- exact old behavior replaced or narrowed;
- exact vNext behavior replacing it;
- exact config overlay for shadow/demo;
- exact production activation config overlay to apply after semantic gates pass;
- exact commands for tests, replay verifier, demo activation, monitoring, and rollback;
- exact monitoring fields/logs;
- stop/rollback thresholds;
- exact external-surface handoff fields for paid spend, remote push, destructive deletion, history rewrite, or broker/account/order/deal/position/history action;
- exact list of markets and source classes enabled at each activation phase;
- exact surfaces still excluded and why.

Output:

- `VNEXT_REPLACEMENT_PRODUCTION_ACTIVATION_DOSSIER_2026-05-26.md`
- `VNEXT_REPLACEMENT_CONFIG_OVERLAY_DIFF_2026-05-26.yaml`
- `VNEXT_REPLACEMENT_ROLLBACK_RUNBOOK_2026-05-26.md`
- `VNEXT_REPLACEMENT_DEMO_SHADOW_ACTIVATION_RUNBOOK_2026-05-26.md`
- `VNEXT_REPLACEMENT_MONITORING_CHECKLIST_2026-05-26.md`

The output cannot stop at an unapplied overlay if the semantic gates pass. The route must apply the vNext production activation config overlay in the repo, commit it, and prove the rollback overlay restores old behavior.

### Stage 12 - Semantic Verification And Red Team

Run semantic verification, not artifact-existence verification. Attack these failure classes:

- primitive fixed-target labels treated as moonshot truth;
- old GTOS still primary;
- FVG subset narrowing;
- 10-trade collapse;
- broad prop blocker;
- broad AVOID blocker with positive avoided-set R;
- MIXED/LEGACY inert labels;
- no-paid-AI diagnostic treated as production selector;
- source-missing rows activated without capture/exclusion;
- selected coverage lies by reporting universe coverage;
- config-gated state used as terminal excuse;
- artifact existence treated as completion;
- shallow verifier accepting bad metrics;
- row loss from compression, histogramming, top-N, or Git convenience.
- activation overlay that passes tests while leaving old GTOS effectively in control.

Output:

- `VNEXT_REPLACEMENT_FINAL_SEMANTIC_VERIFICATION_RESULT_2026-05-26.json`
- `VNEXT_REPLACEMENT_SATURATION_SELF_RED_TEAM_2026-05-26.md`
- route verifier script;
- focused tests.

The semantic verifier must include an activation-overlay behavioral diff. It must fail if enabling the vNext replacement overlay does not alter routing, execution policy, label effects, prop governor behavior, monitoring output, and replay decisions in the exact places the replacement contract says it must.

### Stage 13 - Commit And Activation Config Application

Commit scoped code/config/test/prompt/report artifacts. Do not stage unrelated dirty files. Remote push, history rewrite, and LFS migration are outside this route surface.

If all activation gates pass, apply the vNext production activation config overlay, run preflight/smoke/verification, commit the change, and record the activation-config result. Paid API spend, remote push, destructive deletion, history rewrite, and broker/account/order/deal/position/history action remain external-surface handoff fields.

Output:

- scoped commit(s);
- `VNEXT_REPLACEMENT_COMPLETION_AUDIT_2026-05-26.json`;
- final status.

Allowed final statuses:

- `production_activation_config_overlay_applied_after_semantic_gates`
- `production_activation_config_overlay_applied_with_ai_budget_manifest`
- `production_activation_config_overlay_applied_with_named_source_capture_surface`
- `failed_do_not_activate_with_repair_steps_executed`

Disallowed terminal labels:

- `summary_complete`
- `anatomy_complete`
- `wrapper_complete`
- `default_off_complete`
- `shadow_log_complete`
- `external_waiting_not_live_ready`
- `needs_future_work`
- `activation_deferred_terminal_label`
- `old_gtos_remains_primary_without_evidence`

## Required Subagent Use Inside The Goal

Use subagents aggressively but with bounded responsibilities. Close completed agents and spawn fresh ones when a new evidence lane needs it. Do not let subagent count become an excuse to stop. Do not let subagents write to the same files concurrently.

Minimum lanes:

- Runtime lane: code/config/tests for vNext replacement flags, router wiring, dynamic execution, and state persistence.
- Replay lane: full activated replay, row-preserving shards, hash manifests, and delta ledgers.
- Evidence lane: question ledger closure, source gaps, market activation map, artifact reconciliation.
- AI/ML lane: AI calibration manifest, cache/schema validation, ML shadow role integration.
- Review lane: semantic verifier, activation dossier audit, anti-old-GTOS leakage review, instruction-invariant review.

The route controller keeps final judgment, state file, commits, and merge decisions. Subagents provide evidence and bounded patches; they do not replace the route controller's responsibility.

## Evidence Preservation Standard

Evidence has priority over Git convenience.

- Do not replace exact row-level evidence with histograms, summaries, samples, indexes, or top-N slices.
- Do not shrink, aggregate, compress, or delete material evidence to satisfy normal Git push.
- Chunking means row-preserving sharding with manifests, hashes, row counts, and resume markers.
- Summary reports are derived views, not evidence replacement.
- Storage runway is handled before route start by the orchestrator/user, not as a goal-stage distraction. If storage pressure appears during the run, checkpoint exact progress, preserve row-level evidence, report the exact free-space requirement, and continue after storage is restored. Do not silently reduce evidence.
- Git/LFS/packaging status is packaging metadata. It cannot decide what evidence exists or whether the route is complete.

## Completion Gate

Mark complete when every stage is complete from disk evidence and the final package answers:

- what replaces old GTOS;
- what remains rollback/comparator;
- what code/config/tests changed;
- what replay proves under activated-config production semantics;
- what dynamic execution policy is active in the package;
- what source classes and markets are activated, excluded, or forward-capture required;
- what AI/ML surfaces are mechanical, calibrated, monitored, or waiting on a route-state budget cap;
- what exact config flags change;
- what commands are available for execution;
- what monitoring proves success/failure;
- what rollback command restores old behavior;
- what activation config overlay was applied;
- what external-surface handoff fields remain for paid spend, remote push, rewrite history, destructive source deletion, or broker/account/order/deal/position/history state.

A route is not complete because artifacts exist, a verifier passes shallow checks, a state file says complete, config-gated flags remain unchanged, push is blocked, AI budget cap is absent, or broker/account action is external to the route. Those are constraints to package and act on, not terminal products.

Invalid completion gates:

- incomplete if old GTOS still controls activated execution without explicit rollback/fallback proof;
- incomplete if the moonshot router remains research artifact without runtime wiring;
- incomplete if J46/J49 or fixed 1.5R still dominates activated exit behavior;
- incomplete if FOLLOW/AVOID/MIXED/LEGACY remain non-executing labels;
- incomplete if the route writes dossiers, reports, wrappers, or state files without changed runtime/config/test behavior;
- incomplete if no full activated-config replay or exact resource-proof equivalent exists;
- incomplete if no test/replay proves changed production behavior under the vNext overlay;
- incomplete if the final package lacks exact applied activation overlay, rollback overlay, monitoring checklist, kill thresholds, and scoped commit evidence.

Before final response, run `scripts/validate_goal_prompt_hardening.py` on this prompt if editing it, run route artifact audits/verifiers, inspect the output artifacts from disk, inspect `git status --short`, and make sure the answer responds to the newest owner instruction rather than a stale context summary.
