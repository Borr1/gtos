# SCID To As-Of Bar Derivation Contract And Candidate Generator Constraint Goal Prompt

Date: 2026-05-11
Owner lane: source-control/design contract after G12 SCID segment repair acceptance
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Build `SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT`.

Design the source-control contract that will let future lanes convert accepted Sierra SCID bounded segments into as-of bar inputs and constrained candidate-generator inputs without opening validation, result scoring, path-label outcomes, promotion, live behavior, AI/API calls, paid/vendor routes, or broker/account/order evidence.

This is a contract/design lane only. It may define parser rules, byte/record boundaries, bar-construction rules, timestamp inclusivity, no-leak constraints, candidate-generator input schemas, duplicate policy, source partitions, fixtures, validator expectations, and next-gate prompts. It must not run a validation set, generate accepted candidate rows for scoring, derive path-label/result outcomes, calculate R/PnL/win-rate/expectancy/performance, tune edge rules from outcomes, or promote anything.

The output should make the next builder lane stronger, not looser: future SCID-to-asof conversion must be deterministic, source-hashed, no-leak, duplicate-safe, partition-aware, and auditable before any candidate generation or sealed validation execution can happen.

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
11. Read the accepted G12 SCID repair reaudit route:
    `research/science_program_2026_05/06_outcome_testing/g12_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_reaudit/`.
12. Read the target SCID repair route:
    `research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/`.
13. Read the sealed source-pool route:
    `research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/`.
14. Read the G0 sealed partition packet:
    `research/science_program_2026_05/06_outcome_testing/g0_fpb_sealed_partition_and_adversarial_baseline_packet/`.
15. Read the accepted FPB discovery result and G12 audit routes:
    `research/science_program_2026_05/06_outcome_testing/no_api_mechanical_replay_family_path_behavior_discovery_result_screen/`
    and
    `research/science_program_2026_05/06_outcome_testing/g12_fpb_result_audit/`.

Do not rely on chat memory, thread summaries, or compaction memory. If interrupted, resumed, or uncertain, regenerate `LIVE_STATE`, reread this controlling prompt and the current lane artifacts from disk, and continue from the committed context anchor.

Runtime and speed are not quality constraints. Do not emit a thin schema memo if the same evidence class can freeze stronger parser, as-of, duplicate, fixture, and verification contracts. Use chunking, fixture subsets, exact manifests, explicit cfile py_compile, no-cache pytest, and scoped commits as needed.

## Evidence Class

`SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_ONLY`

Allowed:

- read-only inspection of accepted repair manifests, G12 audit artifacts, and source-control route artifacts;
- limited read-only parsing of accepted bounded SCID segments for schema/fixture/contract verification only;
- defining deterministic SCID parser contract, bar derivation contract, as-of boundaries, timestamp inclusivity, OHLCV/volume semantics, session/KZ handling, duplicate policy, and candidate-generator constraints;
- emitting small source-safe fixtures derived from bounded segments only if they are no-leak, non-result, non-path-label, and not raw market-data blobs;
- verifier, focused tests, no-leak scans, duplicate/partition audits, and next G12 prompt;
- scoped commits for this source-control/design route and research-state refresh.

Forbidden:

- validation execution;
- sealed-validation row generation;
- replay/path-label/result outcome generation;
- R, PnL, win-rate, expectancy, performance, cost, slippage, or promotion claims;
- tuning/selecting edge logic from any result/path-label outcomes;
- AI/API calls, paid/vendor access, credentials, remotes, broker account/order/history/deal/position evidence, or live trade result reads;
- live behavior, live restart, prompt/config/risk/safety/execution/canary/selector changes;
- committing raw `.scid`, `.parquet`, `.csv`, `.dly`, `.bin`, or other raw market-data blobs.

## Required Design Questions

The route must answer and freeze:

1. What exact SCID binary parser contract is accepted for future use?
2. What exact timestamp representation is used, including Sierra epoch, UTC conversion, millisecond precision, inclusivity, and tie handling?
3. What is the deterministic rule for deriving bars from tick/record streams?
4. Are bars anchored by source timestamp, close timestamp, interval start, interval end, or decision as-of timestamp?
5. Is the as-of rule left-closed/right-open, right-closed, or another explicit interval policy?
6. Which fields can be derived source-safely from SCID records, and which fields are forbidden because they are broker/order/result/path-label/cost/live evidence?
7. How are OHLC, volume, bid-volume, ask-volume, trade-count, and empty bars represented?
8. How are gaps, session closures, holidays, partial bars, duplicate timestamps, non-monotonic records, same-millisecond records, and out-of-order records handled?
9. How are mini/micro/proxy sources, symbol aliases, contract roll identity, and duplicate economic sources prevented from double-counting?
10. How are the 365 discovery-source exclusions and four adversarial baselines preserved in every future derived packet?
11. How does the future candidate generator consume derived bars without looking beyond the decision as-of?
12. What fields must a future candidate-generator packet include to support no-leak verification, duplicate controls, partition assignment, and eventual G12/G0 review?
13. What exact source-control gates remain before validation execution can exist?

## Required Outputs

Create a route under:

`research/science_program_2026_05/06_outcome_testing/scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint/`

Required artifacts:

- `SCID_ASOF_BAR_DERIVATION_CONTRACT_2026-05-11.json`
- `SCID_ASOF_BAR_DERIVATION_CONTRACT_2026-05-11.md`
- `SCID_ASOF_CANDIDATE_GENERATOR_CONSTRAINT_2026-05-11.json`
- `SCID_ASOF_CANDIDATE_GENERATOR_CONSTRAINT_2026-05-11.md`
- `SCID_ASOF_FIELD_SCHEMA_2026-05-11.json`
- `SCID_ASOF_FORBIDDEN_FIELD_LEDGER_2026-05-11.json`
- `SCID_ASOF_TIMESTAMP_AND_INTERVAL_POLICY_2026-05-11.json`
- `SCID_ASOF_DUPLICATE_AND_PROXY_POLICY_2026-05-11.json`
- `SCID_ASOF_DISCOVERY_EXCLUSION_AND_BASELINE_PRESERVATION_AUDIT_2026-05-11.json`
- `SCID_ASOF_NOLEAK_PARTITION_AUDIT_2026-05-11.json`
- `SCID_ASOF_FIXTURE_LEDGER_2026-05-11.json`
- `SCID_ASOF_SOURCE_CONTROL_GATE_LEDGER_2026-05-11.json`
- `SCID_ASOF_SATURATION_REDTEAM_LEDGER_2026-05-11.json`
- `SCID_ASOF_OUTPUT_MANIFEST_2026-05-11.json`
- `SCID_ASOF_COMPLETION_AUDIT_2026-05-11.json`
- `SCID_ASOF_COMPLETION_AUDIT_2026-05-11.md`
- `SCID_ASOF_VERIFICATION_RESULT_2026-05-11.json`
- builder script, verifier script, and focused pytest file.

Emit the next independent G12 prompt:

`research/science_program_2026_05/04_goal_prompts/G12_SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_AUDIT_GOAL_PROMPT_2026-05-11.md`

That next G12 prompt must audit the contract only. It must not run validation, generate scored candidates, derive path-label outcomes, promote anything, or touch live behavior.

## Required Checks

1. Reconcile the accepted G12 SCID repair audit decision and verify zero remaining SCID segment repair blockers.
2. Confirm all 9 accepted bounded segments are represented as source inputs by manifest reference, not raw blob copy.
3. Confirm 365 discovery-source exclusions remain excluded from any future sealed source use.
4. Confirm all four adversarial baselines remain exact and cannot be silently weakened by the derivation contract.
5. Confirm the contract forbids every post-decision, path-label, result, broker/account/order/history, cost/slippage, AI-response, and live-effect field.
6. Confirm interval/as-of logic cannot read records after the decision as-of.
7. Confirm empty/gap/session-closed handling fails closed rather than fabricating market data.
8. Confirm duplicate/proxy policy prevents double-counting the same economic source across full/mini/micro/proxy contracts.
9. Confirm the future candidate-generator packet cannot silently become validation execution.
10. Confirm raw data blobs are neither staged nor committed.
11. Run JSON parse, verifier, focused tests, and syntax/compile checks.
12. Check committed-diff scope for forbidden live-surface changes while treating unrelated runtime/shadow dirt as informational.

## Required Saturation And Self-Red-Team

Before completion, answer and pursue same-evidence-class gaps:

1. What exact bug would let bar derivation look one bar into the future?
2. What exact bug would turn a segment-source packet into a result/path-label packet?
3. What exact bug would let a raw SCID full-file hash drift invalidate future derived bars?
4. What exact timestamp/timezone/interval ambiguity would a skeptical G12 reject?
5. What exact duplicate/proxy ambiguity could inflate sample size?
6. What exact field would leak broker, order, result, cost, path-label, or live information if admitted?
7. What exact gap/session-closure behavior could fabricate nonexistent bars?
8. What exact fixture is needed to prove empty bars, duplicate timestamps, same-millisecond records, non-monotonic records, and segment boundaries are handled?
9. What exact future G12/G0 gates are required before any sealed validation or result lane?
10. Which broader science hypotheses could use this derivation contract later, and what must stay out of this contract so it does not box the research?

If any answer exposes an allowed same-evidence-class gap, pursue it before closeout. "Outside scope" is valid only when the next step crosses into validation, scoring, G12 acceptance, G0 synthesis, registry edit, live behavior, paid spend, credentials/remotes, or forbidden broker/account/order evidence.

## Completion Standard

Mark complete only if:

- every required artifact exists;
- the SCID parser/bar/as-of/candidate-generator contract is explicit and machine-checkable;
- all accepted SCID segments are referenced source-safely;
- 365 discovery-source exclusions and four adversarial baselines are preserved;
- forbidden fields and no-leak partition rules are frozen;
- duplicate/proxy policy is frozen;
- future validation and result gates remain closed;
- next G12 contract-audit prompt exists and is runnable;
- verifier and focused tests pass, or environment friction is precisely separated from code failure;
- scoped commits are made;
- `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false` remain closed;
- closeout `LIVE_STATE` is regenerated;
- remaining blockers are exact, actionable, and not lazy.

## One-Line Starter

`/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_GOAL_PROMPT_2026-05-11.md as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory or compaction memory; stay SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_ONLY with no validation execution, sealed-validation row generation, replay/path-label/result outcomes, R/PnL/win-rate/expectancy/performance/cost/slippage scoring, promotion, live behavior, AI/API, paid/vendor access, credentials, remotes, broker account/order/history/deal/position evidence, raw market-data blob commits, or prompt/config/risk/safety/execution/canary/selector changes; design the source-control contract for converting the 9 G12-accepted bounded Sierra SCID segments into deterministic as-of bar inputs and constrained future candidate-generator inputs, freezing parser/timestamp/interval/as-of/OHLCV/gap/session/duplicate/proxy/no-leak/forbidden-field/discovery-exclusion/adversarial-baseline policies; do not run validation or score candidates; pursue every same-evidence-class ambiguity until contract-closed, exactly blocked, rejected, or proven impossible from approved routes; emit JSON+MD contracts, schemas, audits, fixture ledger, gate ledger, builder/verifier/focused tests, next G12 contract-audit prompt, scoped commits, closeout verification, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; mark complete only when this prompt file's completion standard is fully satisfied.`
