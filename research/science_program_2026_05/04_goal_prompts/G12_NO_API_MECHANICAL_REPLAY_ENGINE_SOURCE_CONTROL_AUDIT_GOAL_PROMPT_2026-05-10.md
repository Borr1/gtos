# G12 NO-API Mechanical Replay Engine Source-Control Audit Goal Prompt

Date: 2026-05-10
Owner lane: independent G12 source-control audit
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Independently audit `NO_API_MECHANICAL_REPLAY_ENGINE_FROM_SOURCE_UNIVERSE` as source-control and discovery-inventory evidence only.

The target route is:

`research/science_program_2026_05/06_outcome_testing/no_api_mechanical_replay_engine_from_source_universe/`

The audit must decide whether the route is acceptable as a no-API mechanical pre-AI replay substrate before any downstream discovery-result, validation, AI-delta, or promotion lane can consume it. Do not rubber-stamp the route because its own verifier passed. Recompute, inspect, and adversarially test the source boundaries, frozen schema policy, family registry, source selection, hash handling, candidate/path-label inventories, no-leak guarantees, and saturation claims.

Terminal decision options:

- `ACCEPT_AS_NO_API_MECHANICAL_REPLAY_SOURCE_CONTROL_SUBSTRATE`
- `ACCEPT_WITH_EXACT_REPAIR_BLOCKERS`
- `REJECT_FOR_EVIDENCE_CLASS_OR_COUNT_DEFECT`

Acceptance does not make any candidate family validation-safe and does not open result scoring, live trading changes, registry edits, prompt/config/risk/safety changes, paid/API calls, broker actual-R reads, or promotion.

## Mandatory Preflight And Context

1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read the latest numbered `.context\02_session_handoffs\*`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\00_core\research_operating_doctrine.md`.
6. Read `.context\00_core\research_current_state.md`.
7. Read `.context\00_core\goal_session_research_discipline.md`.
8. Read `.context\00_core\local_heavy_data_inventory.md`.
9. Read `research\science_program_2026_05\04_goal_prompts\NO_API_MECHANICAL_REPLAY_ENGINE_FROM_SOURCE_UNIVERSE_GOAL_PROMPT_2026-05-10.md`.
10. Read this prompt and record exact HEAD, target route path, and this prompt path in the audit context anchor.

Do not rely on chat memory. If context compaction, restart, or uncertainty occurs, regenerate live state, re-read this prompt and the core context docs, re-read the target artifacts, and continue from disk.

If `git status` shows pre-existing runtime, shadow-log, generated live-state, or program-control dirt, snapshot it at preflight and treat it as environment/runtime state unless it overlaps the G12 audit write scope. Do not stage, revert, or fail the audit because of unrelated pre-existing dirt. Scope safety must be judged from the G12 committed/staged diff plus explicit preflight/closeout dirty-state ledgers, not from a blind requirement that the whole working tree be clean.

## Target Artifacts

Required target artifacts include:

- `NO_API_MECHANICAL_REPLAY_CONTEXT_ANCHOR_2026-05-10.json`
- `NO_API_MECHANICAL_REPLAY_FROZEN_REPLAY_SCHEMA_AND_POLICY_2026-05-10.json`
- `NO_API_MECHANICAL_REPLAY_MECHANICAL_FAMILY_REGISTRY_2026-05-10.json`
- `NO_API_MECHANICAL_REPLAY_SOURCE_SELECTION_AND_HASH_LEDGER_2026-05-10.json`
- `NO_API_MECHANICAL_REPLAY_CANDIDATE_INVENTORY_2026-05-10.json`
- `NO_API_MECHANICAL_REPLAY_CANDIDATE_INVENTORY_ROWS_2026-05-10.jsonl`
- `NO_API_MECHANICAL_REPLAY_DISCOVERY_PATH_LABEL_INVENTORY_2026-05-10.json`
- `NO_API_MECHANICAL_REPLAY_DISCOVERY_PATH_LABEL_ROWS_2026-05-10.jsonl`
- `NO_API_MECHANICAL_REPLAY_FAMILY_TERMINAL_STATUS_LEDGER_2026-05-10.json`
- `NO_API_MECHANICAL_REPLAY_SEARCHED_ROOT_LEDGER_2026-05-10.json`
- `NO_API_MECHANICAL_REPLAY_SAME_EVIDENCE_CLASS_CONTINUATION_LEDGER_2026-05-10.json`
- `NO_API_MECHANICAL_REPLAY_EXCLUDED_SLICE_LEDGER_2026-05-10.json`
- `NO_API_MECHANICAL_REPLAY_NOLEAK_AUDIT_2026-05-10.json`
- `NO_API_MECHANICAL_REPLAY_SATURATION_SELF_REDTEAM_PASS_2026-05-10.json`
- `NO_API_MECHANICAL_REPLAY_NEXT_PROMPT_PACK_2026-05-10.json`
- `NO_API_MECHANICAL_REPLAY_COMPLETION_AUDIT_2026-05-10.json`
- `NO_API_MECHANICAL_REPLAY_OUTPUT_MANIFEST_2026-05-10.json`
- `NO_API_MECHANICAL_REPLAY_SOURCE_PROGRESS_2026-05-10.jsonl`
- `NO_API_MECHANICAL_REPLAY_VERIFICATION_RESULT_2026-05-10.json`
- target builder, verifier, and focused tests.

Expected target summary from the completed route:

- source universe rows consumed: `3500`
- selected source rows: `365`
- excluded source slices: `3135`
- selected large OHLC hash resolutions: `18`
- opened mechanical families: `11`
- candidate inventory rows: `13540033`
- candidate rows written to compact artifact: `120000`
- discovery path-label rows: `12852758`
- path-label rows written to compact artifact: `120000`
- promotion verdict: `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

## Required Audit Work

Create a new independent G12 route under:

`research/science_program_2026_05/06_outcome_testing/g12_no_api_mechanical_replay_engine_source_control_audit/`

Required outputs:

1. Context anchor with HEAD, prompt path, target route path, target artifact list, and target code/artifact hashes.
2. Decision ledger with terminal decision and exact acceptance or rejection reasons.
3. Target artifact inventory and parse audit for all required JSON/JSONL artifacts.
4. Source-selection and hash audit, including every selected large-file hash resolution.
5. Frozen schema, duplicate-key, as-of/no-lookahead, and projection-boundary audit.
6. Mechanical family registry audit covering all opened families and high-value excluded families.
7. Candidate inventory count, row-schema, duplicate-key, cap-policy, source-progress, and concentration audit.
8. Discovery path-label count, row-schema, label-vocabulary, cap-policy, and no-result-language audit.
9. Git/LFS artifact-storage audit proving the two large compact-row JSONL artifacts are push-safe, locally materialized for parsing, and not committed as raw >100MB Git blobs.
10. Excluded-slice, searched-root, and same-evidence-class continuation audit.
11. No-leak and forbidden-surface audit.
12. Builder/verifier/test source audit.
13. Target verifier and focused-test rerun report.
14. Saturation/self-red-team ledger with explicit attempts to break target assumptions.
15. Exact repair/followup/source-request ledger, even if empty.
16. Dirty-state and committed-diff scope audit separating pre-existing runtime/generated dirt from G12-created artifacts.
17. Completion audit with `can_mark_goal_complete`.
18. Independent verifier and focused tests for the G12 audit route.

Minimum checks:

- Parse every target JSON/JSONL artifact.
- Recompute written candidate-row and path-label-row counts from the compact JSONL artifacts.
- Reconcile full-stream counts from target summaries, source progress, and builder aggregate logic.
- Verify artifact caps do not truncate aggregate counts, family terminal counts, path-label counts, or source-progress evidence.
- Verify the two compact-row JSONL artifacts are Git LFS tracked in the committed tree: `git show HEAD:<path>` must be a Git LFS pointer, `git cat-file -s HEAD:<path>` must be small pointer-sized content, the pointer OIDs/sizes must match local LFS objects, and `git lfs fsck` or an exact equivalent must pass.
- Materialize the two LFS JSONL artifacts locally before JSONL parsing if the working tree contains pointer text. Pointer text in the working tree is a storage/materialization issue to repair inside the audit, not a route parse failure by itself.
- Verify no non-LFS raw blob above GitHub's 100MB limit is introduced by the replay route or G12 audit route. If any such blob exists, repair by LFS/chunking/manifest policy before acceptance, without losing the source data.
- Verify the candidate duplicate key uses only source-safe fields and that duplicate counts are reported rather than hidden.
- Verify path-label rows have `label_family=DISCOVERY_PATH_LABEL_ONLY` and contain no result/cost/R/win-rate/expectancy fields.
- Verify all opened families reached terminal candidate/path-label inventory status and none remain prototype-only.
- Verify excluded native depth, tick, and GTOS source-state families have exact evidence-class or parser blockers and next executable routes.
- Verify the target builder does not import or call Anthropic/OpenAI, requests/http clients, Databento, MT5 order/account/history/deal/position paths, live restart code, remotes, credentials, prompts, config, risk, permissions, selectors, canaries, or production trading logic.
- Verify target code does not change source files outside the scoped route and the full next prompt file.
- Verify no broker actual-R, account IDs, raw ticket/order/deal/position fields, result/cost/R/win-rate/expectancy scoring, validation-safe flips, promotion flags, registry edits, remote pushes, live restarts, prompt/config/risk/safety changes, or live trading behavior changes.
- Verify all newly staged/committed files are limited to the G12 audit route, permitted same-evidence-class target repair, and required context refresh. Pre-existing runtime/shadow/generated dirt may remain unstaged, but it must be listed in the audit and shown not to overlap the audit's evidence or write scope.
- Run target syntax check, target focused tests, and target verifier.
- Run G12 syntax check, G12 focused tests, and G12 verifier.
- Regenerate `.context\LIVE_STATE.md` at closeout and verify research freshness.

## Hardening Standard

Operate adversarially and actively. If the target route can be accepted only after a same-evidence-class repair, make the repair inside the G12 route or reduce it to an exact repair blocker. Do not stop at a broad label such as data missing, sample too small, row count too large, not in git, or out of scope when the issue can be checked from source-safe local files, route artifacts, code inspection, parser repair, hash recomputation, or a bounded rerun.

If a full target rerun is feasible within local space and time, rerun it or perform a deliberately bounded rerun that proves the key invariants. If a full rerun is not necessary for acceptance, explain why the source-progress ledger, compact row artifacts, code audit, and verifier evidence are sufficient for source-control acceptance.

Preserve scope exactly:

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

Forbidden in this route:

- validation execution
- result/cost/R/win-rate/expectancy scoring
- promotion
- registry edits
- paid/API/Databento routes
- remote push
- live restart
- live trading prompts
- production trading logic changes
- config/risk/permissions/safety/selectors/canaries
- MT5 order/account/history/deal/position behavior
- broker actual-R
- credentials
- live trading behavior changes

## Completion Standard

You may mark the goal complete only if:

- every required G12 artifact exists,
- every target artifact is parsed or any parse failure becomes an exact repair blocker,
- expected target counts are independently reconciled or exact deviations are explained,
- target verifier and focused tests pass or exact environment-only friction is recorded with an accepted fallback,
- G12 verifier and focused tests pass,
- forbidden-surface scans pass,
- Git/LFS push-safety and local materialization checks pass for the compact JSONL artifacts,
- pre-existing dirty runtime/generated files are recorded, left unstaged, and shown not to affect the G12 audit evidence,
- completion audit says `can_mark_goal_complete=true`,
- research context is refreshed,
- commits are scoped to this G12 audit route, any permitted target source-control repair, and required context refresh,
- no unsafe flags are opened,
- and any remaining issue is exact, actionable, and not a lazy blocker.

One-line starter:

`/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/G12_NO_API_MECHANICAL_REPLAY_ENGINE_SOURCE_CONTROL_AUDIT_GOAL_PROMPT_2026-05-10.md as the complete objective; do mandatory preflight and context refresh first; stay G12_SOURCE_CONTROL_AUDIT_ONLY with no AI/API, validation, result scoring, promotion, live behavior, paid/vendor access, credentials, remotes, broker account/order/history/deal/position use, or prompt/config/risk/safety changes; independently audit the no-api mechanical replay candidate and discovery path-label inventories, source hashes, family terminal statuses, no-leak boundaries, duplicate/as-of policy, excluded-slice ledger, saturation pass, Git/LFS push-safe storage/materialization of large JSONL artifacts, and pre-existing dirty runtime/generated state separation; complete only with scoped audit artifacts, verifier/focused tests, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false.`
