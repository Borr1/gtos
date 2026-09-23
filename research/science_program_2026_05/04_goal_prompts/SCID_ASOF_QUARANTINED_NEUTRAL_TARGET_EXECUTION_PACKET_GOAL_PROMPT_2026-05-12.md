# SCID As-Of Quarantined Neutral Target Execution Packet Goal Prompt

Date: 2026-05-12
Owner lane: builder/discovery/execution packet, source-safe neutral target behavior only
Evidence class: `SCID_ASOF_QUARANTINED_NEUTRAL_TARGET_EXECUTION_PACKET_ONLY`
Terminal goal: build the full neutral-target behavior packet unlocked by the accepted G12 target/horizon rulebook

## Objective

Build `SCID_ASOF_QUARANTINED_NEUTRAL_TARGET_EXECUTION_PACKET`.

This route must consume the accepted SCID as-of candidate packet, G0 sealed/stress partition design, SCID target/horizon repair route, and G12 target/horizon repair audit. It must compute source-safe neutral bar-behavior targets for the full accepted candidate population under the frozen rulebook:

- candidate rows: `3,014`
- sealed-design rows: `2,432`
- stress-design rows: `582`
- discovery exclusions preserved: `365`
- denominator economic groups: `7`
- horizons: `1`, `4`, `16`, `32` M15 bars
- target families:
  - `neutral_close_to_close_return_m15_horizons_v1`
  - `neutral_high_low_excursion_m15_horizons_v1`

This is not a strategy PnL, R, win-rate, expectancy, promotion, live-readiness, AI-decision, broker-execution, or GTOS-entry-quality lane. It is a quarantined source-safe neutral target behavior execution packet. It may compute the neutral target values that G12 accepted as source-control inputs, but it must not interpret them as OB/FVG/breaker/no-fill/GTOS strategy performance.

## Mandatory Context Use

Before building anything:

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/goal_session_research_discipline.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read this prompt from disk.

The route must treat those files as active instructions, not background context. The completion audit must explicitly report:

- `goal_session_research_discipline_read_after_preflight=true`
- `research_operating_doctrine_read_after_preflight=true`
- lane posture: `BUILDER_DISCOVERY_EXECUTION_PACKET_AGGRESSIVE_SOURCE_SAFE`
- builder posture applied: broad, curious, outside-current-edge, non-conservative evidence construction
- G12/G0 posture not imported into builder: no defensive self-censoring and no stopping at "no edge found" without full permitted execution
- anti-boxing questions pursued
- outside-current-edge route families considered
- proof-or-impossibility stop condition used
- which doctrine requirements were deliberately not answered because they cross evidence-class or forbidden boundaries

## Builder Posture

This is a builder/discovery execution packet, not a G12 audit. Do not frame the work as trying to avoid findings. Do not be timid. Do not stop at availability counts, packet shape, or "not strategy performance" disclaimers if the neutral target values can be computed source-safely.

The correct posture is:

- compute the full permitted source-safe target behavior packet;
- use every accepted row, horizon, partition, and source-safe slice allowed by the accepted artifacts;
- derive and freeze any source-safe as-of diagnostic features before target computation when useful for later interpretation;
- search beyond the current OB edge and current production logic for neutral path-behavior structures visible in the accepted source-control data;
- label limitations precisely without turning them into premature stopping;
- leave independent rejection or acceptance to the next G12 audit.

Do not collapse the route into the default answer "no new edge, only OB retest." Current GTOS frameworks are baseline context, not the research boundary.

## Required Inputs

Read and bind these exact artifacts:

- `research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/SCID_ASOF_BAR_ROWS_2026-05-11.jsonl`
- `research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/SCID_ASOF_BAR_MANIFEST_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/SCID_ASOF_CANDIDATE_INPUT_ROWS_2026-05-11.jsonl`
- `research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/SCID_ASOF_CANDIDATE_INPUT_PACKET_MANIFEST_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/g12_scid_asof_bar_builder_and_candidate_input_packet_source_control_audit/G12_SCID_ASOF_PACKET_AUDIT_DECISION_LEDGER_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/G0_SCID_ASOF_ROW_PARTITION_LEDGER_2026-05-11.jsonl`
- `research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/G0_SCID_ASOF_VALIDATION_DESIGN_RULEBOOK_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/g12_scid_asof_sealed_validation_design_audit/G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_AUDIT_DECISION_LEDGER_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/scid_asof_sealed_validation_target_horizon_repair/SCID_ASOF_TARGET_HORIZON_RULEBOOK_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/scid_asof_sealed_validation_target_horizon_repair/SCID_ASOF_TARGET_HORIZON_NEUTRAL_TARGET_CONTRACT_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/g12_scid_asof_target_horizon_repair_audit/G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_DECISION_LEDGER_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/g12_scid_asof_target_horizon_repair_audit/G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_COMPLETION_AUDIT_2026-05-11.json`

Also search nearby route artifacts, verifiers, tests, manifests, and current research state with `rg` before accepting any ambiguity.

## Evidence Class And Boundaries

Allowed:

- compute neutral close-to-close target values from accepted source-control bars;
- compute neutral high/low excursion target values from accepted source-control bars;
- emit row-level target computability and not-computable reasons;
- emit aggregate distribution matrices for neutral target behavior;
- emit partition, symbol, economic-group, hour/session, horizon, source-file, coverage, concentration, and denominator diagnostics;
- derive source-safe pre-target as-of descriptors from bars ending at or before the candidate entry reference time, if frozen before target computation;
- emit failure anatomy for missing coverage and negative/null/ambiguous neutral behavior;
- emit the next independent G12 audit prompt.

Forbidden:

- R, PnL, win-rate, expectancy, profit factor, strategy edge lift, or promotion readiness;
- strategy-side interpretation;
- OB/FVG/breaker/no-fill/GTOS family performance claims;
- broker account/order/history/deal/position evidence;
- broker actual-R or hidden result labels;
- AI/API calls;
- paid/vendor access;
- raw `.scid`, `.parquet`, `.csv`, `.dly`, `.bin`, or segment blob commits;
- live behavior, live restart, prompt/config/risk/safety/execution/canary/selector changes;
- registry edits;
- remote push;
- credential access.

Safe flags must remain:

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

The packet may include `neutral_target_behavior_opened=true` only as a source-safe neutral target behavior flag. It must also include `strategy_result_scoring_opened=false`.

## Pre-Target Freeze Requirement

Before computing any target value, emit a pre-target freeze packet that records:

- current HEAD;
- controlling prompt path;
- accepted G12 packet audit decision;
- accepted G12 design audit decision;
- accepted G12 target/horizon audit decision;
- source artifact paths and SHA256 hashes;
- exact candidate row count;
- exact bar row count;
- partition counts;
- denominator group count;
- discovery exclusion count;
- target families;
- horizons;
- frozen target formula text;
- frozen fail-closed not-computable rules;
- frozen aggregate slices;
- frozen source-safe as-of descriptor definitions, if any;
- frozen forbidden metric list;
- frozen next G12 audit requirement.

If this packet cannot be emitted, stop before target computation and emit an exact repair prompt. Do not compute targets without it.

## Target Computation Rules

For every candidate row:

1. Use `duplicate_key_fields.entry_reference_time_utc` as the reference time.
2. Require it to equal `decision_asof_utc`; otherwise fail closed.
3. Use the source-control bar with `bar_end_exclusive_utc == entry_reference_time_utc` and matching `symbol`.
4. Require entry bar `bar_status == RECORD_PRESENT`.
5. Require entry bar `close` non-null.
6. For each horizon `H` in `[1,4,16,32]`:
   - close-to-close target requires horizon close bar at `entry_reference_time_utc + H * 15m`, `RECORD_PRESENT`, non-null close;
   - high/low excursion requires all bars with `bar_start_utc >= entry_reference_time_utc` and `bar_end_exclusive_utc <= entry_reference_time_utc + H * 15m`, all `RECORD_PRESENT`, non-null `high`, `low`, and `close`.
7. Do not shorten horizons.
8. Do not impute missing bars.
9. Do not reset at sessions.
10. Do not use future bars beyond accepted source-control segment coverage.
11. Emit exact `NOT_COMPUTABLE_*` reason per candidate/horizon/target family when any rule fails.

For computable rows, emit:

- candidate row id;
- duplicate denominator key;
- partition assignment;
- symbol;
- canonical economic group;
- source file;
- entry reference time;
- entry close;
- horizon;
- horizon close for return target;
- close-to-close absolute delta;
- close-to-close percent return;
- max high over horizon for excursion target;
- min low over horizon for excursion target;
- upside excursion absolute and percent;
- downside excursion absolute and percent;
- source bar hashes consumed;
- target row hash;
- evidence-class flags and safe flags.

## Source-Safe As-Of Diagnostic Descriptors

To avoid a shallow packet, build a source-safe descriptor ledger before target computation where possible. Use only bars ending at or before `entry_reference_time_utc`. Allowed examples:

- prior 4/16/32/96-bar realized range;
- prior 4/16/32/96-bar close-to-close drift;
- prior high-low compression percentile within the source segment;
- prior volatility/range bucket;
- time-of-day bucket;
- session bucket derived only from UTC time and symbol;
- source coverage quality bucket;
- denominator group;
- symbol/source proxy group.

These descriptors are for neutral behavior slicing only. They are not strategy features for live trading, and they must not be selected after seeing target values. If descriptor computation is impossible, emit exact reasons and still compute the base target packet.

## Required Outputs

Create a new route directory:

`research/science_program_2026_05/06_outcome_testing/scid_asof_quarantined_neutral_target_execution_packet/`

Required artifacts:

- `SCID_ASOF_NEUTRAL_TARGET_CONTEXT_ANCHOR_2026-05-12.json`
- `SCID_ASOF_NEUTRAL_TARGET_CONTEXT_ANCHOR_2026-05-12.md`
- `SCID_ASOF_NEUTRAL_TARGET_PREREQUISITE_ACCEPTANCE_LEDGER_2026-05-12.json`
- `SCID_ASOF_NEUTRAL_TARGET_PRE_TARGET_FREEZE_PACKET_2026-05-12.json`
- `SCID_ASOF_NEUTRAL_TARGET_SOURCE_HASH_BINDING_2026-05-12.json`
- `SCID_ASOF_NEUTRAL_TARGET_DESCRIPTOR_FREEZE_LEDGER_2026-05-12.json`
- `SCID_ASOF_NEUTRAL_TARGET_ROW_RESULTS_2026-05-12.jsonl`
- `SCID_ASOF_NEUTRAL_TARGET_NOT_COMPUTABLE_LEDGER_2026-05-12.jsonl`
- `SCID_ASOF_NEUTRAL_TARGET_AGGREGATE_DISTRIBUTION_MATRIX_2026-05-12.json`
- `SCID_ASOF_NEUTRAL_TARGET_PARTITION_SYMBOL_SESSION_MATRIX_2026-05-12.json`
- `SCID_ASOF_NEUTRAL_TARGET_CONCENTRATION_DENOMINATOR_AUDIT_2026-05-12.json`
- `SCID_ASOF_NEUTRAL_TARGET_BASELINE_CONTROL_READINESS_LEDGER_2026-05-12.json`
- `SCID_ASOF_NEUTRAL_TARGET_FAILURE_ANATOMY_LEDGER_2026-05-12.json`
- `SCID_ASOF_NEUTRAL_TARGET_INTERPRETATION_LIMITS_2026-05-12.md`
- `SCID_ASOF_NEUTRAL_TARGET_OUTPUT_MANIFEST_2026-05-12.json`
- `SCID_ASOF_NEUTRAL_TARGET_COMPLETION_AUDIT_2026-05-12.json`
- `SCID_ASOF_NEUTRAL_TARGET_COMPLETION_AUDIT_2026-05-12.md`
- `SCID_ASOF_NEUTRAL_TARGET_VERIFICATION_RESULT_2026-05-12.json`
- `build_scid_asof_neutral_target_execution_packet_2026_05_12.py`
- `verify_scid_asof_neutral_target_execution_packet_2026_05_12.py`
- `test_scid_asof_neutral_target_execution_packet_2026_05_12.py`

Emit the next independent G12 prompt:

`research/science_program_2026_05/04_goal_prompts/G12_SCID_ASOF_QUARANTINED_NEUTRAL_TARGET_EXECUTION_PACKET_AUDIT_GOAL_PROMPT_2026-05-12.md`

That audit prompt must remain neutral-target packet audit only. It must not promote, open live behavior, use broker evidence, call AI/API, or reinterpret neutral targets as strategy performance.

## Aggregate Matrices

Build aggregate matrices for all source-safe slices with sufficient rows. Include computable and not-computable counts. At minimum:

- overall by partition (`SEALED_VALIDATION_CANDIDATE_DESIGN`, `STRESS_ROBUSTNESS_CANDIDATE_DESIGN`);
- by horizon;
- by target family;
- by symbol;
- by canonical economic group;
- by source file;
- by UTC hour;
- by session bucket;
- by descriptor buckets frozen before target computation;
- by denominator group/concentration bucket.

Allowed neutral distribution summaries:

- count;
- missing/not-computable count;
- mean, median, standard deviation;
- min, max;
- p05, p25, p75, p95;
- sign distribution for neutral close-to-close returns, labeled as `positive_return_fraction_not_win_rate`;
- upside/downside excursion ratio summaries, labeled as neutral path-shape diagnostics, not trade outcomes.

Forbidden labels in matrices:

- `win_rate`
- `expectancy`
- `R`
- `PnL`
- `profit_factor`
- `edge`
- `alpha`
- `pass_rate`
- `promotion`

## Anti-Boxing And Creative Search Requirements

Do not restrict interpretation to OB retest or existing GTOS frameworks. This packet is neutral path behavior; use it to expose which source-safe path behaviors are worth later strategy-specific source-field expansion.

The route must explicitly answer:

1. Which neutral target horizons have the strongest source-safe availability?
2. Which horizons and descriptors show non-random-looking path behavior that merits a future preregistered strategy-specific test?
3. Which results are simply broad market drift, session behavior, or volatility state rather than a tradable edge?
4. Which slices are dominated by one symbol, one proxy group, one source file, one session, one hour, or one denominator group?
5. Which candidate families cannot be interpreted because the packet lacks side/entry/stop/POI/lifecycle fields?
6. What source-field expansion would be required to turn a neutral behavior finding into a strategy-specific test?
7. What future science routes does this unlock beyond OB retest, including path geometry, volatility/tail behavior, session microstructure, orderflow proxy context, execution timing, and regime/state descriptors?
8. What would be the strongest next route if neutral behavior looks promising?
9. What would be the strongest next route if neutral behavior is null or baseline-explained?

## Saturation And Self-Red-Team

Before completion, run a written saturation pass that answers:

- Did every accepted candidate row appear exactly once in either target results or not-computable ledgers?
- Did every candidate/horizon/target-family combination get a terminal status?
- Did any target value use a missing, gap, synthetic, future-context, or non-source-control bar?
- Did any matrix accidentally use discovery exclusions, forbidden secondary denominator sources, or duplicate rows?
- Did any matrix use labels that imply strategy performance?
- Did any target/horizon/descriptor get selected after target values were inspected?
- Did any blocked computation have a source-safe same-class repair path that was left undone?
- Did runtime/live dirt or unrelated files affect the committed lane?
- Did the builder posture remain aggressive and creative without crossing evidence-class boundaries?
- Did the route emit the strongest possible next G12 audit prompt?

If any answer exposes an allowed same-evidence-class gap, pursue it before closeout. Do not defer same-class work as vague future work.

## Verification Requirements

Required checks:

- JSON parse for all generated JSON files;
- JSONL parse and row-count checks for target and not-computable ledgers;
- exact input row counts: `3,014` candidates, `7,567` bar rows;
- exact partition counts: `2,432` sealed, `582` stress, `365` discovery exclusions preserved;
- exact horizon set: `[1,4,16,32]`;
- exact target family set;
- every candidate/horizon/target-family has exactly one terminal status;
- no forbidden metric names or strategy-performance labels;
- no raw market-data blob committed;
- no forbidden live/prompt/config/risk/safety/execution/canary/selector path changes;
- source hash bindings match consumed input artifacts;
- `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`;
- `python -m py_compile` or explicit short-cfile compile if Windows pycache friction appears;
- focused pytest;
- route verifier;
- post-commit no-write verifier against committed artifacts.

## Git And Dirty-State Rules

Commit only:

- the new neutral-target route directory;
- the emitted next G12 prompt;
- focused context refresh files if needed.

Do not stage unrelated runtime/shadow/live dirt. If unrelated dirt exists, record it in a dirty-state ledger as informational only. Before commit, inspect staged files.

## Completion Standard

The goal can be marked complete only when:

- mandatory context files were read and applied;
- accepted G12 target/horizon repair decision is proven from disk;
- pre-target freeze packet exists before target values;
- all `3,014` candidate rows are represented;
- all horizons and target families are executed or fail closed with exact reasons;
- aggregate matrices and failure anatomy exist;
- no forbidden strategy-performance labels or live/broker/API surfaces were opened;
- verifier and focused tests pass;
- next G12 audit prompt exists and is runnable;
- scoped commits exist;
- final closeout verification passes.

Allowed terminal decisions:

- `BUILT_QUARANTINED_NEUTRAL_TARGET_EXECUTION_PACKET_G12_AUDIT_REQUIRED`
- `EXECUTION_BLOCKED_SOURCE_COVERAGE_REPAIR_REQUIRED`
- `EXECUTION_REJECTED_NO_SOURCE_SAFE_NEUTRAL_TARGET_ROUTE`

Do not use a blocked terminal decision if the same-class source-safe computation can be completed by searching, repairing, deriving, or writing code inside this goal.

## One-Line Starter

```text
/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/SCID_ASOF_QUARANTINED_NEUTRAL_TARGET_EXECUTION_PACKET_GOAL_PROMPT_2026-05-12.md as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; read and operationalize .context/00_core/goal_session_research_discipline.md and .context/00_core/research_operating_doctrine.md as active instructions; stay SCID_ASOF_QUARANTINED_NEUTRAL_TARGET_EXECUTION_PACKET_ONLY with no R/PnL/win-rate/expectancy/profit-factor/strategy-edge/promotion/live behavior/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/prompt-config-risk-safety-execution-canary-selector changes; use aggressive builder posture, not conservative audit posture, and compute the full source-safe neutral target behavior packet for all 3,014 candidates, 2,432 sealed rows, 582 stress rows, 7 denominator groups, both target families, and horizons 1/4/16/32; emit pre-target freeze, row results, not-computable ledgers, source-safe descriptor slices, aggregate matrices, concentration/no-leak/failure-anatomy ledgers, verifier, focused tests, scoped commits, next G12 audit prompt, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; pursue every same-evidence-class blocker until cleared, proven impossible from approved routes, or reduced to exact owner/access/source/capture requirement, and mark complete only when the prompt file's completion standard is fully satisfied.
```
