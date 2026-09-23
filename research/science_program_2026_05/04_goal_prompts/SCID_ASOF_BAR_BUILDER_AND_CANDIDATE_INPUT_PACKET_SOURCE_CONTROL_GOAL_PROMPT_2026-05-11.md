# SCID As-Of Bar Builder And Candidate Input Packet Source-Control Goal Prompt

Date: 2026-05-11
Owner lane: source-control bar-builder and candidate input-packet materialization only
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Build `SCID_ASOF_BAR_BUILDER_AND_CANDIDATE_INPUT_PACKET_SOURCE_CONTROL`.

Materialize source-control bars and candidate-generator input packets from the 9 G12-accepted bounded Sierra SCID segment references after rechecking segment hashes, parser layout, timestamp/as-of rules, duplicate/proxy policy, forbidden-field scanner semantics, fixture coverage, no-leak gates, discovery-source exclusions, adversarial baselines, and raw-data handling.

This route may build deterministic source-control bar artifacts and input-only candidate packet artifacts. It must not execute sealed validation, score candidates, derive path-label/result outcomes, calculate R/PnL/win-rate/expectancy/performance/cost/slippage, promote anything, call AI/API, use paid/vendor/credential/remote routes, inspect broker account/order/history/deal/position evidence, commit raw `.scid`, `.parquet`, `.csv`, `.dly`, `.bin`, or segment blob market-data files, or touch live behavior/prompt/config/risk/safety/execution/canary/selector surfaces.

This is the first lane after the SCID-to-asof source-control contract. Treat it as high risk for accidental validation leakage. Candidate rows must remain input-only and source-control only.

## Mandatory Preflight And Context

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read the latest numbered `.context/02_session_handoffs/*`.
4. Read `.context/00_core/quick_reference_card.md`.
5. Read `.context/00_core/research_operating_doctrine.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read `.context/00_core/goal_session_research_discipline.md`.
8. Read `.context/00_core/local_heavy_data_inventory.md`.
9. Read `.context/00_core/ai_in_loop_cost_control_research_plan.md`.
10. Read `research/science_program_2026_05/05_synthesis/HISTORICAL_SEALED_VALIDATION_PROTOCOL_PLAN_2026-05-09.md`.
11. Read the G12 SCID-to-asof contract audit route:
    `research/science_program_2026_05/06_outcome_testing/g12_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_audit/`.
12. Read the SCID-to-asof contract route:
    `research/science_program_2026_05/06_outcome_testing/scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint/`.
13. Read the accepted G12 SCID segment repair route:
    `research/science_program_2026_05/06_outcome_testing/g12_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_reaudit/`.
14. Read the bounded segment repair route:
    `research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/`.
15. Read the G0 sealed partition route:
    `research/science_program_2026_05/06_outcome_testing/g0_fpb_sealed_partition_and_adversarial_baseline_packet/`.

Do not rely on chat memory, thread summaries, or compaction memory. If interrupted, resumed, or uncertain, regenerate `LIVE_STATE`, reread this controlling prompt and latest route artifacts from disk, and continue from committed state.

Runtime and speed are not quality constraints. Do not shrink the packet because parsing is slow or fixtures are inconvenient. Use chunking, checkpoints, fixture subsets, byte-range reads, explicit cfile py_compile, no-cache pytest, and resumable builders where needed.

## Evidence Class

`SCID_ASOF_BAR_BUILDER_AND_CANDIDATE_INPUT_PACKET_SOURCE_CONTROL_ONLY`

Allowed:

- read-only byte-range parsing of the 9 accepted bounded Sierra SCID segments;
- deterministic as-of bar construction under the accepted contract;
- candidate-generator input packet construction with input-only fields;
- source hash, bar hash, packet hash, duplicate key, partition, no-leak, and fixture ledgers;
- repair of the two exact G12 contract warnings inside this same source-control lane;
- builder, verifier, focused tests, completion audit, and next G12/G0 source-control audit prompt;
- scoped commits for this source-control route and research-state refresh.

Forbidden:

- validation execution;
- sealed-validation row/result generation;
- scored candidate generation;
- replay/path-label/result outcomes;
- R, PnL, win-rate, expectancy, performance, cost, slippage, or promotion claims;
- AI/API calls, paid/vendor access, credentials, remotes, broker account/order/history/deal/position evidence, or live trade result reads;
- live behavior, live restart, prompt/config/risk/safety/execution/canary/selector changes;
- raw `.scid`, `.parquet`, `.csv`, `.dly`, `.bin`, segment blob, or other raw market-data blob commits.

## Mandatory Carry-Forward Repairs Before Packet Acceptance

The G12 contract audit accepted the prior contract with zero terminal blockers but exactly two warnings. This lane must close both before any packet acceptance:

1. `FORBIDDEN_SCAN_OVERMATCH_WIN_WINDOW`
   - Problem: required candidate fields `bar_window_start_utc` and `bar_window_end_utc` contain substring `win`; the prior forbidden ledger used substring matching and includes `win`.
   - Required repair: implement snake_case token matching for short forbidden words or explicitly whitelist `bar_window_*` before packet materialization.
   - Required tests: prove `bar_window_start_utc` and `bar_window_end_utc` pass, while genuine forbidden result/performance terms such as `win_rate`, `winning_trade`, `loss`, `pnl`, `expectancy`, `slippage`, `broker_order`, `deal`, `position`, `path_label`, and `result` fail.

2. `TARGET_TESTS_DO_NOT_EXECUTE_HARD_FLOOR_CASE`
   - Problem: source ledgers carry `eligible_segment_start_utc_hard_floor` and upstream G12 proves segment first records are at/after the floor, but target tests lacked dedicated executable hard-floor fixture assertions.
   - Required repair: add tests that reject records before `eligible_segment_start_utc_hard_floor`, records outside `segment_byte_start..segment_byte_end_exclusive`, partial bars after `decision_asof_utc`, and records exactly at decision as-of for the prior closed bar.
   - Required tests: fixture rows must cover before-hard-floor, exactly-at-hard-floor, before-segment, after-segment, exactly-at-decision-asof, same-millisecond records, duplicate timestamps, and non-monotonic source ordering.

Do not mark the route complete if either warning is only re-described. It must be repaired with executable tests and verifier checks.

## Required Materialization Rules

1. Rehash every accepted segment before consuming it.
2. Build bars only from raw bytes inside `segment_byte_start..segment_byte_end_exclusive`.
3. Preserve the accepted parser contract: 56-byte header, 40-byte records, Sierra epoch `1899-12-30T00:00:00Z`, source timestamp precision, and tie handling by `(source_timestamp_us, source_record_index)`.
4. Apply left-closed/right-open intervals: `bar_start_utc <= source_record_utc < bar_end_exclusive_utc`.
5. Include only closed bars where `bar_end_exclusive_utc <= decision_asof_utc`.
6. Exclude records exactly at decision as-of from the prior closed bar when the interval policy requires exclusion.
7. Represent empty/gap/session-closed bars fail-closed with null OHLC, zero volume, and `candidate_eligible=false`.
8. Never forward-fill, backward-fill, infer, or synthesize OHLC from neighboring bars.
9. Preserve the 365 discovery-source exclusions and keep them disjoint from sealed source inputs.
10. Preserve the four adversarial baselines exactly:
    - `baseline_random_session_control`
    - `baseline_shifted_entry_control`
    - `baseline_momentum_continuation`
    - `baseline_mean_reversion`
11. Apply duplicate/proxy policy across full/mini/micro/proxy contracts before any candidate denominator is emitted.
12. Mark every candidate input row as `CANDIDATE_GENERATOR_INPUT_ONLY_NOT_VALIDATION`.
13. Candidate input rows must contain no path labels, results, broker/account/order/history/deal/position fields, cost/slippage fields, AI/API fields, live-effect fields, or performance fields.

## Required Outputs

Create a route under:

`research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/`

Required artifacts:

- `SCID_ASOF_BAR_BUILDER_CONTRACT_INPUTS_2026-05-11.json`
- `SCID_ASOF_BAR_SOURCE_REHASH_LEDGER_2026-05-11.json`
- `SCID_ASOF_BAR_ROWS_2026-05-11.jsonl`
- `SCID_ASOF_BAR_MANIFEST_2026-05-11.json`
- `SCID_ASOF_CANDIDATE_INPUT_ROWS_2026-05-11.jsonl`
- `SCID_ASOF_CANDIDATE_INPUT_PACKET_MANIFEST_2026-05-11.json`
- `SCID_ASOF_FORBIDDEN_SCAN_REPAIR_LEDGER_2026-05-11.json`
- `SCID_ASOF_HARD_FLOOR_FIXTURE_LEDGER_2026-05-11.json`
- `SCID_ASOF_DUPLICATE_PROXY_DENOMINATOR_LEDGER_2026-05-11.json`
- `SCID_ASOF_DISCOVERY_EXCLUSION_BASELINE_AUDIT_2026-05-11.json`
- `SCID_ASOF_NOLEAK_PARTITION_AUDIT_2026-05-11.json`
- `SCID_ASOF_SATURATION_REDTEAM_LEDGER_2026-05-11.json`
- `SCID_ASOF_OUTPUT_MANIFEST_2026-05-11.json`
- `SCID_ASOF_COMPLETION_AUDIT_2026-05-11.json`
- `SCID_ASOF_COMPLETION_AUDIT_2026-05-11.md`
- `SCID_ASOF_VERIFICATION_RESULT_2026-05-11.json`
- builder script, verifier script, and focused pytest file.

Emit the next independent audit prompt:

`research/science_program_2026_05/04_goal_prompts/G12_SCID_ASOF_BAR_BUILDER_AND_CANDIDATE_INPUT_PACKET_SOURCE_CONTROL_AUDIT_GOAL_PROMPT_2026-05-11.md`

That next audit prompt must remain source-control packet audit only. It must not run validation, score candidates, derive path-label/result outcomes, or promote anything.

## Required Checks

1. Verify target contract G12 decision is `ACCEPT_WITH_EXACT_CONTRACT_WARNINGS` and terminal blocker count is zero.
2. Verify both exact warnings are repaired with code and tests before packet acceptance.
3. Verify all 9 accepted SCID segment hashes reproduce from current local files.
4. Verify no bar uses bytes outside its accepted segment.
5. Verify no bar uses a record after its decision as-of.
6. Verify no candidate row contains forbidden fields or forbidden values.
7. Verify candidate row count and bar row count are explicit, stable, and duplicate-policy controlled.
8. Verify candidate rows are input-only and cannot be interpreted as wins/losses/path labels/results.
9. Verify 365 discovery-source exclusions and four adversarial baselines remain preserved.
10. Verify raw market-data blobs are not staged or committed.
11. Run JSON/JSONL parse, verifier, focused tests, and syntax/compile checks.
12. Check committed-diff scope for forbidden live-surface changes; record unrelated runtime/shadow dirt separately.

## Required Saturation And Self-Red-Team

Before completion, answer and pursue same-evidence-class gaps:

1. What exact bug would let records outside the bounded segment into a bar?
2. What exact bug would let records at/after decision as-of enter a candidate input?
3. What exact bug would let `bar_window_*` be rejected by overbroad forbidden scanning?
4. What exact bug would let true performance/result words pass the repaired scanner?
5. What exact bug would make empty/gap/session-closed bars appear tradeable?
6. What exact duplicate/proxy mistake would inflate candidate denominator?
7. What exact field or value could make an input-only row look like validation/result evidence?
8. What exact row would a skeptical G12 reject, and does the verifier catch it?
9. Does the packet box research into current FPB families, or does it preserve future source-safe science expansion?
10. What exact next gate owns independent packet audit, G0 synthesis if needed, sealed validation execution, robustness/stress, and promotion?

If any answer exposes an allowed same-evidence-class gap, pursue it before closeout. "Outside scope" is valid only when the next step crosses into validation, scoring, G12/G0 acceptance, registry edit, live behavior, paid spend, credentials/remotes, or forbidden broker/account/order evidence.

## Completion Standard

Mark complete only if:

- every required artifact exists;
- both G12 warnings are repaired with executable tests and verifier checks;
- all 9 source segments rehash before consumption;
- bars and candidate input packets are deterministic, no-leak, source-bounded, as-of safe, duplicate-controlled, and input-only;
- no result/path-label/performance/cost/slippage/broker/AI/live fields exist in candidate rows;
- 365 discovery-source exclusions and four adversarial baselines are preserved;
- next G12 packet-audit prompt exists and is runnable;
- verifier and focused tests pass or environment friction is precisely separated from code failure;
- scoped commits are made;
- safe flags remain `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`;
- closeout `LIVE_STATE` is regenerated;
- remaining blockers are exact, actionable, and not lazy.

## One-Line Starter

`/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/SCID_ASOF_BAR_BUILDER_AND_CANDIDATE_INPUT_PACKET_SOURCE_CONTROL_GOAL_PROMPT_2026-05-11.md as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory or compaction memory; stay SCID_ASOF_BAR_BUILDER_AND_CANDIDATE_INPUT_PACKET_SOURCE_CONTROL_ONLY with no validation execution, sealed-validation row/result generation, scored candidate generation, replay/path-label/result outcomes, R/PnL/win-rate/expectancy/performance/cost/slippage scoring, promotion, live behavior, AI/API, paid/vendor access, credentials, remotes, broker account/order/history/deal/position evidence, raw market-data blob commits, or prompt/config/risk/safety/execution/canary/selector changes; repair the two exact G12 warnings with executable tests before packet acceptance, rehash all 9 accepted SCID segments, build deterministic source-control bars and input-only candidate packets under the accepted parser/as-of/interval/no-leak/duplicate/proxy contract, preserve 365 discovery exclusions and four adversarial baselines, and keep every candidate row CANDIDATE_GENERATOR_INPUT_ONLY_NOT_VALIDATION; do not stop at packet shape; pursue every same-evidence-class ambiguity until accepted, exactly blocked, rejected, or proven impossible from approved routes; emit JSON/JSONL+MD bars, packet manifests, repair ledgers, audits, builder/verifier/focused tests, next G12 packet-audit prompt, scoped commits, closeout verification, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; mark complete only when this prompt file's completion standard is fully satisfied.`
