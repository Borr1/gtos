# FPB Sealed Source Pool Immutable SCID Hash Freeze Repair Goal Prompt

Date: 2026-05-11
Owner lane: source-control repair after G12 sealed source-pool audit
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Build `FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR`.

Repair the append-mutable native Sierra SCID source-hash drift found by `G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT`. The repair must freeze immutable source evidence for all 9 current native SCID sealed-pool candidates before any SCID-to-asof-bar derivation, candidate-generation, validation execution, or performance route can exist.

The prior source-expansion packet used full native SCID files as source evidence. G12 found those files are append-mutable: SHA256, file size, record count, and coverage end changed after materialization. This repair must replace mutable full-file evidence with either immutable snapshot evidence or bounded eligible-segment evidence, with exact hashes, coverage metadata, parser/as-of/no-leak status, duplicate decisions, partition assignments, and rerunnable verification.

This route is source-control repair only. It must not execute validation, generate replay/path labels, score results, promote a family, alter live behavior, call AI/API, use paid/vendor access, read broker account/order/history/deal/position evidence, or change prompts/config/risk/safety/execution/canary/selector behavior.

## Mandatory Preflight And Context

1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read the latest numbered `.context\02_session_handoffs\*`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\00_core\research_operating_doctrine.md`.
6. Read `.context\00_core\research_current_state.md`.
7. Read `.context\00_core\goal_session_research_discipline.md`.
8. Read `.context\00_core\local_heavy_data_inventory.md`.
9. Read `.context\00_core\ai_in_loop_cost_control_research_plan.md`.
10. Read `research\science_program_2026_05\05_synthesis\HISTORICAL_SEALED_VALIDATION_PROTOCOL_PLAN_2026-05-09.md`.
11. Read the failed G12 audit route:
    `research\science_program_2026_05\06_outcome_testing\g12_fpb_sealed_source_pool_materialization_audit\`.
12. Read the target source-expansion packet:
    `research\science_program_2026_05\06_outcome_testing\fpb_source_expansion_and_sealed_pool_materialization\`.
13. Read the sealed partition packet:
    `research\science_program_2026_05\06_outcome_testing\g0_fpb_sealed_partition_and_adversarial_baseline_packet\`.

Do not rely on chat memory. If there is compaction, restart, interruption, or uncertainty, regenerate live state and reread this controlling prompt, the failed G12 repair-blocker ledger, the source-expansion packet, and core context docs from disk before continuing.

Runtime and speed are not quality constraints. Do not stop after naming append mutability; repair it. If immutable full-file copies are feasible inside approved local source-control boundaries, create and hash them. If bounded eligible-segment hashes are the stronger source-control design, implement them with exact parser rules and coverage metadata. If a file is locked, inaccessible, too large, or changing during copy, pursue a safe retry, copy strategy, read-only snapshot method, or exact access/blocker proof before stopping.

## Evidence Class

`FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_ONLY`.

Allowed:

- read-only access to local Sierra SCID files needed for the 9 candidate sources,
- immutable snapshot copy under a research-controlled artifacts directory if source-safe and storage-safe,
- bounded eligible-segment extraction/hash if preferable to full mutable file snapshots,
- source hash, file size, record count, coverage start/end, eligible-segment start/end, parser/as-of/no-leak, duplicate-source, and partition metadata repair,
- repair packet builder, verifier, focused tests, and G12 rerun prompt,
- no-leak/dirty-state/scoped-diff audit,
- hardening, saturation, and failure-anatomy artifacts.

Forbidden:

- validation execution,
- replay/path-label/result scoring,
- R, PnL, win-rate, expectancy, performance, cost, slippage, or promotion claims,
- live behavior, live restart, prompt/config/risk/safety/execution/selector/canary changes,
- AI/API calls,
- paid/API/Databento routes,
- credentials,
- remote push,
- broker account/order/history/deal/position/ticket/live trade result reads.

## Required Repair Inputs

Use the G12 repair blocker ledger:

`research/science_program_2026_05/06_outcome_testing/g12_fpb_sealed_source_pool_materialization_audit/G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT_REPAIR_BLOCKER_LEDGER_2026-05-11.json`

It reports 9 repair blockers for append-mutable native SCID files:

- `6BM26-CME.scid` / `GBPUSD_6B`
- `6EM26-CME.scid` / `EURUSD`
- `6JM26-CME.scid` / `USDJPY_6J`
- `GCM26-COMEX.scid` / `XAUUSD_GC`
- `MGCM26-COMEX.scid` / `XAUUSD_MGC`
- `MYMM26-CBOT.scid` / `US30_MYM`
- `NQM26-CME.scid` / `NAS100_NQ`
- `SIM26-COMEX.scid` / `XAGUSD_SI`
- `YMM26-CBOT.scid` / `US30_YM`

For each source, reconcile stale packet hash/size/coverage/record-count metadata versus current recomputed metadata, and replace mutable evidence with immutable repaired evidence.

## Repair Design Requirements

The route must choose and justify one or both of these source-evidence policies:

1. Immutable snapshot policy:
   - copy the SCID file bytes to a research-controlled immutable snapshot path,
   - record source path, snapshot path, copy timestamp, source size, snapshot size, source hash at copy time, snapshot hash, record count, coverage start/end, and parser metadata,
   - prove snapshot bytes are stable across immediate rehash,
   - do not commit raw large SCID snapshots unless they are Git LFS pointers and policy permits it; prefer storing ignored/local snapshot files with committed hash manifests if raw size is unsuitable for Git.

2. Bounded eligible-segment policy:
   - parse only the accepted eligible segment needed for future sealed pool use,
   - freeze segment start/end UTC, byte/record boundaries if feasible, record count, segment hash, parser version/hash, and as-of/no-leak rules,
   - prove the segment excludes discovery-exposed and pre-eligible rows,
   - prove later append activity cannot change the segment hash.

If both are feasible, prefer the policy that is strongest for future G12 audit and sealed validation readiness without committing giant raw market-data blobs. If the chosen policy requires local ignored snapshot files, commit the manifest and verifier, not the raw data, unless explicit LFS/raw-data policy is satisfied.

## Required Work

1. Build a repair route under:
   `research\science_program_2026_05\06_outcome_testing\fpb_sealed_source_pool_immutable_scid_hash_freeze_repair\`.
2. Reconcile all 9 repair blockers from the G12 ledger.
3. Freeze immutable source evidence for all 9 or write exact per-source blocker proof.
4. Preserve all `365` selected FPB discovery source exclusions.
5. Preserve the four adversarial baselines:
   - `baseline_random_session_control`
   - `baseline_shifted_entry_control`
   - `baseline_momentum_continuation`
   - `baseline_mean_reversion`
6. Preserve `eligible_segment_start_utc` as a hard floor for every candidate.
7. Preserve the future gates:
   - `SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT`
   - separate validation-execution prompt after source-control contract acceptance.
8. Produce source freeze ledger with current mutable metadata, repaired immutable metadata, hashes, coverage, record counts, and chosen policy.
9. Produce snapshot/segment manifest and source-hash manifest.
10. Produce duplicate-source and discovery-source exclusion audit.
11. Produce parser/as-of/no-leak audit.
12. Produce no-leak/dirty-state/scoped-diff audit separating live/runtime dirt from repair scope.
13. Produce hardening-coverage, searched-root/source-saturation, no-lazy-blocker, hostile-source-review, negative/failure-anatomy, process-limitation countermeasure, and saturation/self-red-team ledgers.
14. Emit the next G12 repair reaudit prompt:
    `research\science_program_2026_05\04_goal_prompts\G12_FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_REAUDIT_GOAL_PROMPT_2026-05-11.md`.
15. Produce builder, verifier, focused tests, output manifest, completion audit, and research-state refresh if materially changed.

## Required Saturation And Self-Red-Team Questions

Before completion, answer and pursue any same-evidence-class gaps:

1. What exact mistake would let an append-mutable full file be treated as immutable source evidence again?
2. What exact mistake would let future appended records change the accepted sealed segment hash?
3. What exact mistake would let pre-eligible or discovery-exposed records enter a sealed segment?
4. Are raw snapshot files being committed accidentally, or are they safely ignored/LFS-managed with committed manifests?
5. Can every repaired source be rehashed immediately and reproduce the manifest?
6. Is the parser/as-of rule stable enough for a future SCID-to-asof-bar derivation contract?
7. Does any repair choice weaken the four adversarial baseline preservation?
8. Does any source remain inaccessible, locked, too large, or changing in a way that requires an exact owner/access/source action?
9. What would the next G12 audit reject, and what artifact preempts it?
10. What remains blocked before validation execution even after this repair?

If any answer exposes an allowed same-evidence-class gap, pursue it before closeout. "Outside scope" is valid only when the next step crosses into validation, scoring, G12 acceptance, registry edit, live behavior, paid spend, credentials/remotes, or forbidden broker/account/order evidence.

## Completion Standard

You may mark complete only if:

- every required repair artifact exists,
- all 9 SCID sources are repaired or have exact source/access blocker proof,
- repaired immutable source evidence rehashes deterministically,
- all 365 discovery source exclusions remain preserved,
- four adversarial baselines remain preserved,
- `eligible_segment_start_utc` hard floors remain preserved,
- SCID-to-asof-bar and candidate-generator gates remain explicit,
- no validation, scoring, promotion, AI/API, broker, paid/vendor, remote, credential, prompt/config/risk/safety/execution/canary/selector, or live behavior surface is opened,
- safe flags remain `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`,
- next G12 repair reaudit prompt exists and is runnable,
- verifier and focused tests pass,
- commits are scoped,
- remaining blockers are exact, actionable, and not lazy.

## One-Line Starter

`/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_GOAL_PROMPT_2026-05-11.md as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory or compaction memory; stay FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_ONLY with no validation execution, replay/path-label/result scoring, R/PnL/win-rate/expectancy/performance, promotion, live behavior, AI/API, paid/vendor access, credentials, remotes, broker account/order/history/deal/position data, or prompt/config/risk/safety changes; repair the 9 append-mutable Sierra SCID sealed-pool candidates from the G12 repair-blocker ledger by producing immutable snapshot hashes or bounded eligible-segment hashes, refreshed coverage windows, record counts, parser/as-of/no-leak metadata, duplicate decisions, partition assignments, discovery-source exclusions, four adversarial baseline preservation, eligible_segment_start_utc hard floors, no-leak/dirty-state scope, hardening coverage, and saturation/self-red-team; do not stop at naming append mutability; pursue every same-evidence-class repair until all 9 sources are repaired, exactly source/access-blocked, or proven impossible from approved routes; emit JSON+MD repair packet, source/snapshot/segment manifests, runnable G12 repair reaudit prompt, builder/verifier/focused tests, scoped commits, closeout verification, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; mark complete only when the prompt file's completion standard is fully satisfied.`
