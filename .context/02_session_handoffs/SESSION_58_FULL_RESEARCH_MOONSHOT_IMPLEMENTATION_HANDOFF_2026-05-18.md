# SESSION 58 HANDOFF - FULL RESEARCH AND MOONSHOT UNIVERSE TO MAIN SYSTEM IMPLEMENTATION

Date: 2026-05-18
Author: Codex GPT-5
Status: terminal checkpoint for current long goal session
Next objective: `FULL_RESEARCH_AND_MOONSHOT_UNIVERSE_TO_MAIN_SYSTEM_IMPLEMENTATION`

## Owner Override

The owner explicitly stopped the current long session from opening more plates. Finish only work already mid-edit, mid-test, or mid-commit; commit scoped finished work; refresh `research_current_state` and `LIVE_STATE`; write this handoff; then stop.

This instruction supersedes the older 48h prompt language that said not to finish early. Do not continue the old `MAIN_ORCHESTRATOR_48H_RESEARCH_TO_SYSTEM_COMPILER_AND_AI_DECISION_ARCHITECTURE` session after this handoff.

## Current Main State

Main repo: `C:\Users\MSI\Documents\ai-trading-agent`

Pre-handoff code checkpoint HEAD:

```text
3b372bda8 research: backfill ai trace trade records
```

After this handoff/docs commit, regenerate and trust `.context/LIVE_STATE.md` for the exact current HEAD. At handoff-writing time, `scripts/generate_live_state.py` reported:

- Generated: `2026-05-18 07:26:54 UTC`
- HEAD: `3b372bda8 research: backfill ai trace trade records`
- Research context freshness: `FRESH`
- Latest research-relevant commit: `3b372bda8 research: backfill ai trace trade records`
- Current-state captured commit: `3b372bda8 research: backfill ai trace trade records`

Runtime posture remains under `pipeline_state/RESEARCH_RUNTIME_HALT.flag`. Do not restart runtime/watchdog/observer/scheduler, do not place/modify/close broker orders, do not use paid vendor/API calls, and do not push remote without an explicit owner command.

## Dirty Files And Ownership

Scoped owned changes before the final docs commit:

- `.context/00_core/research_current_state.md` updated to capture `3b372bda8`.
- This handoff file.
- `.context/LIVE_STATE.md` regenerated for status visibility; do not stage it unless the owner explicitly asks.

Known unrelated dirty/untracked state remains extensive and pre-existing: runtime/shadow logs, generated research control files, local temp pytest directories, archived shadow divergence files, pipeline state, and live monitoring state. Treat those as user/runtime/generated state. Do not revert, delete, or stage them unless a future task explicitly owns them.

Use exact-path `git add` for checkpoint commits. In this environment, `git add`/`git commit` may require escalation because index writes run outside the sandbox user.

## Work Completed Immediately Before Stop

The only mid-edit plate finished after the owner correction was the AI trace trade-record backfill.

Commit:

```text
3b372bda8 research: backfill ai trace trade records
```

Files added:

- `src/research_infra/ai_decision_trace_backfill.py`
- `tests/research_infra/test_ai_decision_trace_backfill.py`
- `research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/build_main_orch48_ai_trace_trade_record_backfill_2026_05_18.py`
- `research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/verify_main_orch48_ai_trace_trade_record_backfill_2026_05_18.py`
- `research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/MAIN_ORCH48_AI_TRACE_TRADE_RECORD_BACKFILL_LEDGER_2026-05-18.jsonl`
- `research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/MAIN_ORCH48_AI_TRACE_TRADE_RECORD_BACKFILL_SUMMARY_2026-05-18.json`
- `research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/MAIN_ORCH48_AI_TRACE_TRADE_RECORD_BACKFILL_MANIFEST_2026-05-18.json`
- `research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/MAIN_ORCH48_AI_TRACE_TRADE_RECORD_BACKFILL_VERIFY_RESULT_2026-05-18.json`

Backfill facts:

- `540` JSON files discovered under `knowledge_base/trade_records`.
- `5` `_pending_records_index.json` files excluded as non-trade-record index files.
- `535` eligible trade records backfilled.
- `535` complete hash-only rows, `0` incomplete rows.
- `535` unique prompt-bundle hashes and `535` unique AI-response hashes.
- `0` rows store full prompt or response text.
- `0` runtime trace-stream writes, `0` broker operations, `0` paid API/vendor calls, `0` runtime-candidate-use rows.
- Symbol counts: XAUUSD `33`, US30_cash `54`, USDJPY `77`, GBPJPY `82`, GBPUSD `102`, XAGUSD `101`, NAS100 `86`.
- Final outcome counts: LIMIT_PLACED `76`, REJECTED_GATE1_SAFETY `102`, REJECTED_L2 `323`, REJECTED_L2_POST_M5 `3`, REJECTED_GATE0_5_TRADING_ENABLED `21`, REJECTED_GATE3_CIRCUIT_BREAKER `4`, EXECUTION_FAILED `6`.

Verification run:

- Builder: ok, `rows=535`, `complete_rows=535`, `stores_full_prompt_or_response_text_rows=0`.
- Verifier: ok, `issues=[]`, `rows=535`, `manifest_output_count=2`.
- Focused tests: `py -3 -m pytest tests/research_infra/test_ai_decision_trace_backfill.py -q --basetemp=.pytest_tmp_ai_trace_backfill` -> `3 passed`, pytest cache warning only.
- AST parse: `ast_ok 4`.
- Scoped `git diff --check`: passed.

## Earlier Current-Session Commits To Preserve

The current session already committed these relevant main-side system/compiler surfaces before this handoff:

- `db4b9f077 research: guard confidence active mode`
- `67d62df1b research: add ai decision trace provenance`
- `9db63bc94 research: register ai trace integrity guard`
- `35fc692d1 research: capture ai malformed attribution`
- `e1ccd9ff0 research: document cross correlation no-event status`
- `be232c615 research: enrich pre-ai h1 poi source capture`
- `778fe9fb1 research: join pre-ai h1 poi gate outcomes`
- `183764d6f research: join sl beyond ob outcomes`
- `1527d0293 research: join touch count gate outcomes`
- `ce0e08d7d research: materialize ai narrowing capacity blocklist`
- `d4897b695 research: guard ai narrowing runtime config`
- `1ecc16b86 research: guard ai narrowing shadow integrity`
- `9a5fa9ec8 research: add ai narrowing shadow evaluations`
- `b44514e60 research: capture ai narrowing event scope`
- `6f826f5f2 research: ingest cross correlation diagnostics`
- `474d014eb config: enable cross instrument correlation shadow decisions`
- `10db096e8 research: inventory gate evidence surfaces`
- `ae1900236 research: quarantine confidence filter promotion`
- `ddf62f8c0 config: enable sl beyond ob shadow decisions`
- `9fe1089ae research: specify ai narrowing event adapter`
- `764b13c7d research: audit ai narrowing event fields`
- `316cd0797 research: add ai narrowing policy registry`

Read `.context/00_core/research_current_state.md` for the full curated map. Do not infer completion from this abbreviated list.

## Moonshot Snapshot To Consume Next

Moonshot worktree:

```text

branch: research/weekend-moonshot-2026-05-15
HEAD: bbcf2bdfbe88ddd62bd84f6f50de617a9e06dc68
status: clean when queried with `git -c safe.directory=C:/tmp/ -C  status --short`
```

Git metadata needs per-command safe-directory because the worktree has different owner metadata:

```powershell
git -c safe.directory=C:/tmp/ -C  rev-parse HEAD
```

Canonical moonshot route directory:

```text
research\science_program_2026_05\06_outcome_testing\weekend_mechanical_edge_factory_moonshot_2026_05_15
```

CP280 is the full frozen moonshot universe and closure set. CP281 is the executable ready slice extracted from CP280. CP282 is the terminal handoff/index/consumption order. The next session must consume all three together.

### CP280 Full Frozen Universe And Closure

Result file:

```text
HISTORICAL_OHLC_GTOS_REPLAY_FROZEN_UNIVERSE_IMPLEMENTATION_CLOSURE_RESULT_2026-05-17.json
sha256: ba5702373b2a7980b29607625a86d0b78459ffdd62fcf91ff0ff2ac0d5dd2b80
ok: true
```

Counts:

- Input artifacts consumed: `3485`
- Input bytes hashed: `13220990164`
- JSONL rows scanned: `6442524`
- Action closure rows: `297622`
- Action closure source rows: `4490013`
- Market/timeframe/source coverage rows: `28474`
- Implementation-ready rows: `461`
- Implementation-ready source rows: `6428`
- Repair-needed rows: `243649`
- Repair-needed source rows: `2552078`
- Kill/preserve rows: `25811`
- Kill/preserve source rows: `303704`
- Main handoff rows: `5`
- Issue rows: `0`

Classification counts:

- implementation_ready `6428`
- default_off_candidate `222659`
- repair_required_for_implementation `762030`
- source_repair_required `83341`
- replay_repair_required `37402`
- redesign_required `1287905`
- redesign_mixed `14940`
- redesign_underpowered `143801`
- kill `136003`
- preserve_intelligence `167701`
- market_source_context `605540`
- classified_action_context `1627803`
- classified_context `1346971`

CP280 key artifact roles, row counts, and hashes are recorded in `HISTORICAL_OHLC_GTOS_REPLAY_FROZEN_UNIVERSE_MAIN_HANDOFF_ARTIFACT_LEDGER_2026-05-17.jsonl`:

- frozen_universe_manifest: `3485` rows, sha256 `2425104b8c06f4cac208b9d5dc256234fe214e26c55a64b5b178f2ee18f659c3`
- frozen_market_timeframe_source_coverage: `28474` rows, sha256 `f94b13d06ea0f65d8c388048d7db59665159c4b06c9b28ba155193ab5983cb26`
- frozen_action_closure: `297622` rows, sha256 `237fe7942248eb51ee1d587703bcffeaf00183386aa8397d93c41c66f863f0dd`
- implementation_ready_bundle: `461` rows, sha256 `34c868237fc551335a0caea5c8e7ad09b35dbdbdf3f258e0f054295879b2b50a`
- repair_needed_bundle: `243649` rows, sha256 `2b913a58d31c334bd94cad0b114308d42529b9d385ce1d0a9662de4c19861793`
- kill_preserve_ledger: `25811` rows, sha256 `aedfc1ddb58480330c2b709fe8bce3c1b282e91abbd444898912d0b8e2e4eabe`
- main_handoff_bundle: `5` rows, sha256 `823a20d6a7f7ffbdc2f448ee864f44997a67cc1f29ebb0807d16175ee2359255`
- completion_audit: `1` row, sha256 `6d5a4cf11ba8064327e45b7bfd8cba679d11ef0daf84fb68a8e95fef9dbd2ffb`

### CP281 Executable Ready Slice

Result file:

```text
HISTORICAL_OHLC_GTOS_REPLAY_FROZEN_UNIVERSE_READY_ACTION_RUNTIME_RESULT_2026-05-17.json
sha256: e87b728d1d823b591a08f8a798365eca42b9270afb780265c674e86710363e5f
ok: true
```

Counts:

- Input ready rows: `461`
- Runtime rule rows: `461`
- Self-test rows: `461`
- Self-test pass rows: `461`
- Aggregate scope rows: `107`
- Source rows represented: `6428`
- Action classes: follow_rule `173`, avoid_filter `288`
- Issue rows: `0`

CP281 key artifact roles:

- ready runtime rules: `461` rows, sha256 `09ba535d736acb0270ea1227f755ef02f4660d63dcdb7e392b824153380083ca`
- ready runtime self-tests: `461` rows, sha256 `5d0cac441a6d0d6d35962c88e8c8445d33b9e6a5ef7362395feb366135db822f`
- ready runtime aggregates: `107` rows, sha256 `4b16cf16b8b241853747af3401642657a831182563e86a1b80ba061c3946343e`
- ready runtime issues: `0` rows, sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- helper: `src/research_infra/moonshot_frozen_universe_ready_action_runtime.py`, sha256 `850366c38adc306babb5859092689d2228fc125d18df5401fe2ccb7741d34a37`

These `461` rows are the highest-priority executable moonshot ready slice. Do not reduce them to a top-N sample.

### CP282 Main Handoff And Consumption Order

Result file:

```text
HISTORICAL_OHLC_GTOS_REPLAY_FROZEN_UNIVERSE_MAIN_HANDOFF_RESULT_2026-05-17.json
sha256: 05b5862ed6428e30504988a07a61eb788afefcca783a49bec9e3e6db3700ee3c
ok: true
```

Verifier:

```text
HISTORICAL_OHLC_GTOS_REPLAY_FROZEN_UNIVERSE_MAIN_HANDOFF_VERIFIER_RESULT_2026-05-17.json
sha256: a0a84d6237318f21e47fee801a9903f466a5d414f94d4856ecc907816fc3b5ba
ok: true
issues: []
```

CP282 counts:

- Artifact rows: `27`
- CP280 artifact rows: `16`
- CP281 artifact rows: `11`
- Consumption-order rows: `5`
- Count-check rows: `12`
- Implementation-ready rows consumed: `461`
- Follow-rule inputs: `173`
- Avoid-filter inputs: `288`
- Aggregate scopes: `107`
- Represented source rows: `6428`
- Repair-needed rows preserved: `243649`
- Kill/preserve rows preserved: `25811`
- Coverage rows preserved: `28474`
- Main handoff rows: `5`
- Issue rows: `0`

CP282 ledgers:

- `HISTORICAL_OHLC_GTOS_REPLAY_FROZEN_UNIVERSE_MAIN_HANDOFF_ARTIFACT_LEDGER_2026-05-17.jsonl`, sha256 `202afed12f4ed64d136218b3a101286b67f00b2abf127b66d3e9ef381da8df42`, `27` lines.
- `HISTORICAL_OHLC_GTOS_REPLAY_FROZEN_UNIVERSE_MAIN_HANDOFF_CONSUMPTION_ORDER_LEDGER_2026-05-17.jsonl`, sha256 `ca600e0709a60ccccdd155ed4c138c278aced06a43f987b04efcdd0bb9e17d8d`, `5` lines.

Consumption order from CP282:

1. CP281 executable ready-slice runtime rules: `11` artifacts, artifact-paths sha256 `a6c52e3a4400f61a1c918c9ad408563ecbb9966859af267fe9fdd0495c8d4982`.
2. CP280 rule-performance evidence: `8` artifacts, artifact-paths sha256 `3a55f9cfcfb6da800d583a419f32b9daa41c72f32e7988ad39f20fba537864e7`.
3. CP280 action/application/execution proof: `19` artifacts, artifact-paths sha256 `f481d306b6249486ac3b300e66b4621bbf889688a96a29c98b15233f2708569d`.
4. CP280 preserved repair-needed bundle and repair task source artifacts: `9` artifacts, artifact-paths sha256 `990154b1ba2afbe21abc8c8069683bde86359e8a8eb73342938e3ddc73b40023`.
5. CP280 full frozen closure packet: `12` artifacts, artifact-paths sha256 `fa6a4f858c6902233530ccf1f0ad168a1e595cabb12ef79e789d9a968b27ef62`.

## Main Research Artifacts To Consume

The next session must consume the complete research body, not only CP282. Required starting points:

- `.context/LIVE_STATE.md`
- `.context/00_core/research_current_state.md`
- `.context/00_core/research_operating_doctrine.md`
- `.context/00_core/goal_session_research_discipline.md`
- `.context/00_core/orchestrator_successor_operating_brief.md`
- `.context/00_core/orchestrator_methodology_hardening_controls.md`
- `.context/00_core/parallel_goal_merge_playbook.md`
- `.context/00_core/ai_in_loop_cost_control_research_plan.md`
- `.context/00_core/local_heavy_data_inventory.md`
- `research/science_program_2026_05/04_goal_prompts/MAIN_ORCHESTRATOR_48H_RESEARCH_TO_SYSTEM_COMPILER_AND_AI_DECISION_ARCHITECTURE_GOAL_PROMPT_2026-05-18.md`
- `research/science_program_2026_05/04_goal_prompts/MAIN_ORCHESTRATOR_48H_RESEARCH_TO_SYSTEM_COMPILER_AND_AI_DECISION_ARCHITECTURE_STARTER_2026-05-18.txt`
- `research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/`
- `research/science_program_2026_05/06_outcome_testing/ready8_expanded_validation_scoring_result_materialization/`
- `research/science_program_2026_05/06_outcome_testing/ready8_expanded_sealed_validation_packet_after_repairs/`
- `research/science_program_2026_05/06_outcome_testing/g0_scid_ready8_numerical_screen_learning_synthesis_after_g12_audit/`
- `research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_numerical_screen_audit/`
- `research/program_control/`
- `shadow_logs/`
- `knowledge_base/trade_records/`
- `src/`, `config/`, `prompts/`, `scripts/`, and `tests/`

Material main-side artifact families already present in the route directory include:

- `MAIN_ORCH24_ACTION_AFTER_*`: current action denominator, exact/proxy-R repairs, kill-scope repairs, pending lifecycle repairs, FVG/OB repairs, source/cost repairs, duplicate merges, adverse-avoid materialization, and implementation-action revisions.
- `MAIN_ORCH48_MOONSHOT_*`: moonshot intake, reduced-surface candidates, registry/self-check, source capture contracts, replay validators, field availability, event adapters, scorer rollups, source-capture priorities, final-review adjusted registries/selectors, and production-dossier drafts.
- `MAIN_ORCH48_NUMERIC_ROUTER_*`: system recommendations, split-output preservation, source inventory, catalog/event/family specs, source-repair queue/proof, slippage join/identity/selection bridge, source-packet trace, selector surface/router, execution identity capture contract, future slippage lifecycle emitter, component bridge, and local-field/source-capture patches.
- `MAIN_ORCH48_AI_*`: AI decision architecture audit, parser hardening, malformed attribution, AI narrowing policy/registry/event scope/shadow evaluation/integrity/config guard/capacity blocklist, AI decision trace provenance/integrity, and trade-record backfill.
- `MAIN_ORCH48_CONFIDENCE_*`: confidence quarantine and active-mode guard.
- `MAIN_ORCH48_CROSS_*`: cross-instrument correlation logger/diagnostics/no-event status.
- `MAIN_ORCH48_SL_*`, `MAIN_ORCH48_TOUCH_*`, `MAIN_ORCH48_PRE_AI_*`: gate evidence joins and capture enrichments.

## Implementation-Ready Surfaces

The next session's primary job is conversion into main-repo behavior. These are not prompt packets:

- CP281 ready action runtime: `461` executable branch-local rule rows, split follow_rule `173` and avoid_filter `288`, with `461/461` self-tests passing and `107` aggregate scopes.
- CP280 implementation-ready bundle: `461` rows representing `6428` source rows.
- Main reduced-surface registry/evaluator surfaces in `src/research_infra/moonshot_expanded_market_reduced_surface_execution.py`; current logs lack full event contract fields, so event production/adapters need implementation rather than passive waiting.
- Numeric-router helper surfaces in `src/research_infra/moonshot_numeric_router_system_recommendations.py`; source-repair selector/router and identity payloads are default-off and ready for concrete event/scorer/router integration.
- AI narrowing policy registry/event scope/shadow evaluation/config guard/integrity guard exist; next step is to use them to actually narrow/remove/harden AI where replay/log/test evidence supports it.
- Confidence active mode is guarded: `active` is blocked unless future `confidence_filter_active_promotion.validated=true`; current effective behavior remains `shadow`.
- AI decision trace runtime logger is enabled in config for future PrimaryAnalyzer calls, integrity-registered, and historical trade records have hash-only prompt/response backfill rows.
- Gate evidence joins exist for touch count, SL beyond OB, pre-AI H1 POI, cross-correlation, confidence, malformed AI responses. Consume them into gate/filter/selector code decisions rather than more inventory.

## Repair-Needed Surfaces

Do not collapse these into vague blocker buckets. Each material row needs source/path/row ownership, code action, replay action, or exact parked reason.

- CP280 repair-needed bundle: `243649` rows and `2552078` source rows. Use CP282 order after CP281 ready rows.
- CP280 kill/preserve bundle: `25811` rows and `303704` source rows. Kill only unsupported current claims; preserve useful mechanism intelligence for redesign, inverse/avoid filters, context features, source repair, or specialization.
- CP280 market/timeframe/source coverage: `28474` rows. Use this for market/timeframe expansion, not just as documentation.
- Numeric-router source-packet context rows still need prospective execution identity capture for the packet-only selector paths; the source-packet trace established packet presence, not exact execution identity or exact R.
- Current main route ledgers still show many exact-R surfaces at `0` and proxy/source-repair denominators. The correct response is replay/source-bound proxy/exact replay repair, not owner-R or broker-R chasing.
- The reduced-surface field-availability audit found current logs do not yet expose the full base/reduced-surface contract fields; build event adapters or replay/shadow emitters.
- Live integrity verifier currently has unrelated pre-existing `ACTION_REQUIRED` issues outside the AI trace waiting lane. Do not confuse those with the new trace surface.
- Pending lifecycle had one recorded source requirement in earlier main action ledgers: `NAS100_2026-05-03T16:15:00+00:00` had no prior source-safe decision tick and the next local tick was at market reopen. Treat that as exact source ownership, not a reason to stop other pending lifecycle work.

## Killed, Shelved, And Preserved Logic

These decisions must not be reopened from stale context:

- READY8 standalone ladder is closed. Use READY8 only as tags, priors, controls, failure intelligence, and guardrails inside a broader system. Do not continue READY8 as standalone.
- V4 and LIRA remain shelved; V3 was empirically stronger in the prior prompt-cascade research. Any use must merge evidence into current architecture, not restart old ladders.
- Confidence scorer has `0` predictive strata in the current evidence and remains shadow/quarantined unless separately validated.
- Cross-correlation had no event rows for the status audit; no live correlation behavior change is justified from that no-event status alone.
- Kill labels must be scope-safe. A `KILL` row kills only an unsupported current claim; the mechanism/failure intelligence must be preserved where it can become redesign, avoid/inverse, context feature, source repair, specialization, or merged-system use.
- Stale CP215-CP223 snapshots are superseded by CP280/CP281/CP282 for moonshot terminal consumption. They can be read only as ancestry/source evidence, not as the controlling terminal map.

## Market And Timeframe Expansion State

The next session is not bounded by the live seven-symbol list. Consume the moonshot expansion universe and the main route artifacts together:

- CP280 coverage rows: `28474`.
- Moonshot prior expansion seeds in the controlling prompt include the 301-row/44-symbol market-expansion population and the 1,145-row/47-symbol-label expansion matrices. Locate and bind their exact artifacts from the moonshot worktree before making expansion claims.
- Current main route already contains expanded-market, reduced-surface, numeric-router, market/source coverage, and default-off scorer/router surfaces.
- Expansion output must become replay/backtest/simulation rows, source-bound proxy-R/expectancy tables, market/timeframe selectors, code/config entries, source-capture tasks, or exact parked states. Do not end at "needs market expansion."

## AI/API Implications

No new paid AI/API calls were made in this session. Future work should remain no-API unless explicitly testing incremental AI value with budget/caching.

Current AI evidence:

- AI malformed attribution: `39` malformed response rows inherited by the AI decision audit surfaces (`36` flat-refusal/short non-JSON, `2` JSON-fence/trailing-text parse failures, `1` other).
- Manual canary fixture inventory in the AI architecture audit: `83` fixtures.
- AI decision trace provenance is now hash-only and config-enabled for future PrimaryAnalyzer calls.
- AI trace integrity guard documents the trace waiting lane while runtime halt prevents new rows.
- AI trace trade-record backfill adds `535` historical hash-only prompt/response rows from saved trade records.
- Confidence active-mode guard prevents accidental activation of an unvalidated low-confidence skip filter.
- AI narrowing surfaces exist but remain default-off/guarded.

Next session must decide and implement where AI is removed, narrowed, explanation-only, schema-hardened, parser-hardened, or retained. Do not preserve AI/API as sacred. Do not leave AI architecture as prose when code/config/tests can encode the decision.

## Live And Shadow Implications

Live/shadow logs are evidence for production friction, path behavior, malformed AI outputs, gate decisions, source gaps, and execution/source-capture needs. They are not a reason to wait for more live data when historical replay/source-bound proxy work can proceed.

Use:

- `shadow_logs/malformed_responses.jsonl`
- `shadow_logs/candidate_features_log.jsonl`
- `shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl`
- `shadow_logs/strategy_follow_candidates.jsonl`
- `shadow_logs/strategy_follow_evaluations.jsonl`
- `shadow_logs/touch_count_gate_decisions.jsonl`
- `shadow_logs/sl_beyond_ob_decisions.jsonl`
- `shadow_logs/cross_instrument_correlation_decisions` if present through current route artifacts
- pending/no-fill/source repair logs including `pending_limit_lifecycle`, `nofill_forward_source_capture`, `candidate_path_follow`, `candidate_ltf_path_order`, `fvg_ob_confluence`, and related audit logs

Do not restart runtime during the halt. Do not place, close, or modify broker orders.

## Required Next Session Behavior

Start a fresh main goal session with exact objective:

```text
FULL_RESEARCH_AND_MOONSHOT_UNIVERSE_TO_MAIN_SYSTEM_IMPLEMENTATION
```

It must consume:

1. CP280 as full frozen moonshot universe and closure set.
2. CP281 as executable ready slice.
3. CP282 as main handoff/index/consumption order.
4. Prior main research, READY8 final intelligence, v2/v3/v4/cascade research, live/shadow findings, blocker/unblocker work, AI/API findings, gate findings, market/timeframe expansion findings, primitive-science hypotheses, failed branches, winning branches, killed branches, repair-needed rows, implementation-ready rows, replay/backtest/simulation outputs, and every implementation-ready research surface already in the repo.

It must not be steered by:

- stale CP215-CP223 moonshot snapshots,
- old READY8 ladders,
- old owner-R/broker-R framing,
- stale handoffs,
- defensive wrapper labels,
- old audit/checkpoint habits,
- arbitrary top-N/top 3/top 5/top 10 cuts,
- representative-only review,
- waiting for live data.

Forbidden terminal products:

- wrappers,
- audits,
- prompt routes,
- blocker packets,
- source-capture-only packets,
- summary-only artifacts,
- owner-R/broker-R chasing,
- stale-context continuation.

The core target is:

- simulated/replay/backtest R,
- source-bound proxy R,
- expectancy,
- market/timeframe expansion,
- strategy behavior,
- execution logic,
- filters/selectors/routers,
- AI/API role reduction or hardening,
- production architecture improvement.

Every research claim must be consumed into one of:

- code,
- config,
- tests,
- result tables,
- implementation decision,
- kill decision with preserved intelligence,
- repair task with exact source/path/row ownership,
- explicit parked state with exact reason.

No broad blocker buckets and no vague future work.

## First Concrete Next Actions

1. Regenerate and read `.context/LIVE_STATE.md`.
2. Read this handoff, `.context/00_core/research_current_state.md`, the moonshot CP282 summary, CP282 consumption-order ledger, CP280 result, CP281 result, and CP282 verifier.
3. Snapshot moonshot HEAD/status again with per-command safe-directory.
4. Build a main-side consumption ledger for CP280/CP281/CP282 if one does not already exist on main, preserving artifact paths, hashes, counts, and row ownership.
5. Start with CP281 `461` ready runtime rule rows: map every follow_rule/avoid_filter row to a main code/config/test surface or exact parked reason. Do not sample.
6. Then consume CP280 performance/action/execution proof and repair-needed bundles in CP282 order.
7. Cross-join the CP rows with the current main route surfaces (`MAIN_ORCH24_ACTION_AFTER_*`, `MAIN_ORCH48_MOONSHOT_*`, `MAIN_ORCH48_NUMERIC_ROUTER_*`, `MAIN_ORCH48_AI_*`, gate/selector joins) so the next work is implementation, replay, backtest, simulation, or exact source repair, not another inventory pass.
