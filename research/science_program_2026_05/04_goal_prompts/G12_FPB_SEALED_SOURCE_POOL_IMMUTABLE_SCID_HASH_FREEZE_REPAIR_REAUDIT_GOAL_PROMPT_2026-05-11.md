# G12 FPB Sealed Source Pool Immutable SCID Hash Freeze Repair Reaudit Goal Prompt

Date: 2026-05-11
Owner lane: independent G12 reaudit of immutable SCID source-control repair
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Independently audit `FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR` as source-control repair evidence only.

Target repair route:

`research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/`

This G12 audit exists because the prior sealed source-pool audit rejected all 9 native Sierra SCID candidates as append-mutable full-file evidence. The repair claims all 9 are now repaired with bounded eligible-segment hashes. This audit must independently verify that claim from source files and committed manifests, not by trusting the target completion audit.

Accepted G12 output may unlock only the next source-control lane:

`SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT`

It must not unlock validation execution, result scoring, promotion, live logic, AI/API routes, or broker/account/order evidence.

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
11. Read the previous failed G12 audit route:
    `research/science_program_2026_05/06_outcome_testing/g12_fpb_sealed_source_pool_materialization_audit/`.
12. Read the target repair route:
    `research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/`.
13. Read the prior source expansion route:
    `research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/`.
14. Read the G0 sealed partition route:
    `research/science_program_2026_05/06_outcome_testing/g0_fpb_sealed_partition_and_adversarial_baseline_packet/`.

Do not rely on chat memory, thread summaries, or compaction memory. If interrupted, resumed, or uncertain, regenerate `LIVE_STATE`, reread this controlling prompt and the target route artifacts from disk, then continue from committed state.

Speed is not a quality constraint. Do not accept a shallow audit because the source files are large, mutable, or inconvenient. Use chunked reads, byte-range rehashing, explicit cfile py_compile, no-cache pytest, and rerunnable verifiers as needed.

## Evidence Class

`G12_FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_REAUDIT_ONLY`

Allowed:

- read-only access to the 9 local Sierra SCID files referenced by the repair manifests;
- independent byte-range or record-range rehashing of bounded eligible segments;
- recomputation of segment hashes, byte/record boundaries, coverage windows, record counts, first/last timestamps, parser/as-of/no-leak metadata, duplicate decisions, discovery-source exclusions, and partition assignments;
- rerunning the target verifier and focused tests as supporting evidence;
- building new G12 audit artifacts, verifier, focused tests, decision ledger, blocker ledger, and completion audit;
- scoped commits for the G12 audit route and research-state refresh.

Forbidden:

- validation execution;
- SCID-to-asof-bar derivation beyond verifying source-control gates;
- candidate generation, replay/path-label rows, result scoring, R, PnL, win-rate, expectancy, performance, cost, slippage, or promotion claims;
- AI/API calls, paid/vendor access, credentials, remotes, broker account/order/history/deal/position evidence, or live trade result reads;
- live behavior, live restart, prompt/config/risk/safety/execution/canary/selector changes;
- committing raw `.scid`, `.parquet`, `.csv`, or other raw market data blobs unless an explicit Git LFS/raw-data policy is already satisfied and the prompt separately authorizes it. This audit should normally commit manifests and audit artifacts only.

## Exact Audit Targets

Audit exactly the 9 repaired sources from the repair manifest and previous blocker ledger:

- `6BM26-CME.scid` / `GBPUSD_6B`
- `6EM26-CME.scid` / `EURUSD`
- `6JM26-CME.scid` / `USDJPY_6J`
- `GCM26-COMEX.scid` / `XAUUSD_GC`
- `MGCM26-COMEX.scid` / `XAUUSD_MGC`
- `MYMM26-CBOT.scid` / `US30_MYM`
- `NQM26-CME.scid` / `NAS100_NQ`
- `SIM26-COMEX.scid` / `XAGUSD_SI`
- `YMM26-CBOT.scid` / `US30_YM`

For each source, independently verify the target route's bounded eligible-segment repair:

- source path and source identity;
- segment byte start and byte end exclusive;
- segment hash;
- segment record count;
- segment first and last timestamp;
- coverage start/end window;
- `eligible_segment_start_utc_hard_floor`;
- parser name/version/hash or parser-as-of identity;
- no-leak rule and partition assignment;
- source-access status;
- whether later source-file append activity can alter the accepted segment hash.

## Required Independent Checks

1. Rehash every manifest segment using `segment_byte_start` and `segment_byte_end_exclusive`.
2. Confirm every segment hash reproduces deterministically from the current local source file.
3. Confirm accepted segment bytes are invariant under append-only full-file growth. Full-file hash drift is allowed only if bounded segment hashes remain stable and the segment boundaries are before appended bytes.
4. Confirm every segment first record is at or after `eligible_segment_start_utc_hard_floor`.
5. Confirm no segment overlaps discovery-exposed rows, pre-eligible rows, or the 365 selected FPB discovery source hashes.
6. Confirm all 365 selected FPB discovery source exclusions remain preserved and disjoint from repaired segment hashes.
7. Confirm all four adversarial baselines remain exactly:
   - `baseline_random_session_control`
   - `baseline_shifted_entry_control`
   - `baseline_momentum_continuation`
   - `baseline_mean_reversion`
8. Confirm duplicate-source and denominator controls remain source-control only and do not count validation rows.
9. Confirm SCID-to-asof-bar derivation and separate validation-execution prompt gates remain explicit and unopened.
10. Confirm safe flags remain `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
11. Confirm no raw market-data blobs were newly staged or committed by the target repair route or this G12 route.
12. Confirm all target artifacts live under the canonical repo path and no duplicated-root or path-alias artifact path is being treated as evidence.
13. Run the target repair verifier and focused tests.
14. Build a new G12 verifier that independently checks the target route and emits a machine-readable verification result.
15. Run focused G12 tests.
16. Run syntax/compile checks. If Windows pycache friction appears, use explicit short cfile compile or AST parse fallback and record the distinction.
17. Check committed-diff scope for forbidden live-surface changes. Treat unrelated live/runtime dirt as informational only, with a dirty-state ledger.

Do not stop at "target verifier passed." G12 acceptance requires independent recomputation and a hostile review of the repair logic.

## Required Artifacts

Create a G12 audit route under:

`research/science_program_2026_05/06_outcome_testing/g12_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_reaudit/`

Required artifacts:

- `G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_DECISION_LEDGER_2026-05-11.json`
- `G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_DECISION_LEDGER_2026-05-11.md`
- `G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_SOURCE_REHASH_AUDIT_2026-05-11.json`
- `G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_SOURCE_REHASH_AUDIT_2026-05-11.md`
- `G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_NOLEAK_PARTITION_AUDIT_2026-05-11.json`
- `G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_BLOCKER_LEDGER_2026-05-11.json`
- `G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_COMPLETION_AUDIT_2026-05-11.json`
- `G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_COMPLETION_AUDIT_2026-05-11.md`
- `G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_VERIFICATION_RESULT_2026-05-11.json`
- `verify_g12_fpb_scid_freeze_repair_reaudit_2026_05_11.py`
- focused pytest file.

If accepted, emit the next controlling prompt for the source-control-only derivation contract:

`research/science_program_2026_05/04_goal_prompts/SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_GOAL_PROMPT_2026-05-11.md`

That next prompt must remain source-control/design only unless a later G12/G0 lane explicitly authorizes validation execution.

## Required Saturation And Self-Red-Team

Before completion, answer and pursue any same-evidence-class gaps:

1. Could the segment hash be accidentally computed over text, decoded records, or normalized bytes instead of raw source bytes?
2. Could a later append, Sierra rewrite, compaction, or file truncation make the manifest appear stable while the source truth changed?
3. Could byte boundaries split a record or include partial binary data that is not parser-stable?
4. Could timestamp interpretation, timezone, Sierra epoch handling, or record sorting allow future data into the segment?
5. Could pre-eligible or discovery-exposed rows leak into the segment through off-by-one boundary logic?
6. Could the four adversarial baselines be preserved in name only while their underlying source partitions drift?
7. Could duplicate-source policy double-count one economic source across multiple futures proxies or mini/micro contracts?
8. Could path aliases, doubled roots, case-insensitive Windows paths, or stale sibling-worktree paths cause false source proof?
9. Could live/runtime dirt or current Sierra append activity make the audit nondeterministic?
10. What would a skeptical G12 reject, and did this audit preempt it with machine-checkable evidence?
11. What remains genuinely blocked before validation execution even if this G12 accepts the repair?

If any answer exposes an allowed same-evidence-class gap, pursue it before closeout. "Outside scope" is valid only when the next step crosses into validation, scoring, G0 synthesis, registry edit, live behavior, paid spend, credentials/remotes, or forbidden broker/account/order evidence.

## Decision Rules

Use one terminal decision:

- `ACCEPT_AS_SOURCE_CONTROL_IMMUTABLE_SCID_SEGMENT_REPAIR_EVIDENCE_ONLY`
- `ACCEPT_WITH_EXACT_SOURCE_CONTROL_WARNINGS`
- `REPAIR_BLOCKED_SOURCE_POOL_PACKET`
- `REJECT_AS_SOURCE_CONTROL_REPAIR_EVIDENCE`

Acceptance requires:

- 9/9 target sources repaired or exact source/access blockers recorded;
- 9/9 segment raw-byte rehashes deterministic;
- byte boundaries and record counts parser-stable;
- every first record at or after the hard floor;
- all discovery exclusions preserved;
- all four adversarial baselines preserved;
- no validation/scoring/promotion/live/API/broker surface opened;
- target verifier/tests and G12 verifier/tests pass;
- no raw data accidentally committed;
- no lazy blocker or vague future-work wording.

If any source fails, do not accept the packet. Emit exact repair blockers naming source path, expected/current metadata, failed check, searched evidence, and the next permitted repair action.

## Completion Standard

Mark complete only when:

- all required G12 artifacts exist;
- independent rehash/recompute checks have run;
- source-control verdict is frozen;
- safe flags remain closed;
- next prompt exists if and only if acceptance allows a next source-control lane;
- verifier and focused tests pass or environment friction is precisely separated from code failure;
- scoped commits are made;
- closeout `LIVE_STATE` is regenerated;
- remaining worktree dirt is recorded as unrelated runtime/generated dirt, not hidden in the audit.

## One-Line Starter

`/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/G12_FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_REAUDIT_GOAL_PROMPT_2026-05-11.md as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory or compaction memory; stay G12_FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_REAUDIT_ONLY with no validation execution, SCID-to-asof-bar derivation beyond source-control checks, candidate generation, replay/path-label/result scoring, R/PnL/win-rate/expectancy/performance, promotion, live behavior, AI/API, paid/vendor access, credentials, remotes, broker account/order/history/deal/position evidence, or prompt/config/risk/safety/execution/canary/selector changes; independently audit the 9 repaired Sierra SCID bounded eligible segments by raw-byte rehashing segment_byte_start/segment_byte_end_exclusive, proving deterministic hashes under append-mutable source files, verifying byte/record boundaries, coverage windows, eligible_segment_start_utc hard floors, parser/as-of/no-leak metadata, duplicate decisions, 365 discovery-source exclusions, four adversarial baselines, no raw-data commits, path-canonicality, dirty-state scope, and future source-control gates; do not stop at target verifier pass; pursue every G12 source-control ambiguity until accepted, exactly repair-blocked, rejected, or proven impossible from approved routes; emit JSON+MD decision/rehash/no-leak/blocker/completion artifacts, G12 verifier/focused tests, next source-control prompt only if accepted, scoped commits, closeout verification, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; mark complete only when this prompt file's completion standard is fully satisfied.`
