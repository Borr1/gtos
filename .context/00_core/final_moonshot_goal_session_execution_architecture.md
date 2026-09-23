# Final Moonshot Goal Session Execution Architecture

Date: 2026-06-04
Status: active orchestration architecture

## Purpose

This file defines how to run final moonshot goal sessions after the hard halt. Goal sessions are force multipliers after Wave 0 source/context authority is coherent. They must not be launched from stale or dirty context, and they must not be weakened into theory-only research.

## Build-And-Ship Authority

Final moonshot goal sessions have full control over repo changes and ship implementation. Change production code, config, prompt surfaces, selector/scheduler/execution logic, risk and safety gates, canary/runtime behavior, profiles, launchers, tests, verifiers, default-on or default-off packages, and integration artifacts to build the strongest final system.

Prompt language states full control over repo changes. The Mac research workspace is the orchestration/build surface. The VPS remains the production/runtime surface.

## Current Integration Worktree

Primary historical Mac orchestration worktree:

`/Users/borr/Documents/gtos/repo/ai-trading-agent`

Branch:

`final-moonshot-context-repair-2026-06-04`

Current accepted local authority:

Read `.context/LIVE_STATE.md` for the current HEAD. Wave1 integration landed at `d8a95f722 merge: complete final moonshot wave1 integration review`; Wave2 launch hardening landed at `26d2c698e context: harden wave2 final master launch`.

Active Wave2 worktree:

`/Users/borr/Documents/gtos/worktrees/final-moonshot-wave2-master-2026-06-04`

Active Wave2 branch:

`final-moonshot-wave2-master-2026-06-04`

Remote state:

`origin/main` remains at `bc797b108 context: finalize portable moonshot launch authority` until the owner approves a push.

Base shadow/runtime evidence:

`origin/main` / `d02a4c531 research: package shadow runtime evidence`

Path model:

- repo artifacts: repo-relative paths;
- Mac workspace/evidence packages: `/Users/borr/Documents/gtos`;
- prepared Mac worktrees: `/Users/borr/Documents/gtos/worktrees`;
- VPS production/runtime or runtime-evidence paths: explicit `vps_runtime_path` labels;
- historical Windows research-laptop paths: historical/audit context only, never active launch paths.

## Launch Rule

Do not launch substantial goal sessions until:

1. `python scripts\generate_live_state.py` passes and `.context/LIVE_STATE.md` is read.
2. `git status --short` is inspected.
3. The route has a prompt path, route directory, manifest, verifier/test ownership, evidence class, scoped commit plan, and clean branch/worktree state.
4. The controlling prompt embeds `goal_session_research_discipline.md`, `research_operating_doctrine.md`, context-resume rules, no arbitrary top-N, same-evidence-class pursuit, and build-and-ship authority.
5. LFS/data/package/VPS evidence requirements are explicit, role-labeled, and materialized only when the route needs them.
6. Deep causal master routes embed living question-stack requirements, row-generated hypothesis lineage, accept/reject/manage/exit/halt/capture interaction analysis, dynamic lane derivation, and proof that newly discovered questions were pursued beyond static prompt examples.

## Sparse-Parallel Launch Mode

Wave1 sparse-parallel launch mode is complete and the Wave1 execution/review worktrees have been removed after merge. Active launch mode is now a single sparse Wave2 master worktree that must first perform the full post-hard-halt causal microscope, then generate the Wave3 V4 sparse-parallel prompt/worktree plan from the evidence it proves.

Integration owner:

`/Users/borr/Documents/gtos/repo/ai-trading-agent`

Removed completed Wave1 worktrees:

- `/Users/borr/Documents/gtos/worktrees/final-moonshot-wave1a-2026-06-04`
- `/Users/borr/Documents/gtos/worktrees/final-moonshot-wave1b-2026-06-04`
- `/Users/borr/Documents/gtos/worktrees/final-moonshot-wave1c-2026-06-04`
- `/Users/borr/Documents/gtos/worktrees/final-moonshot-wave1-integration-2026-06-04`

Future Wave3 sessions should run in their own branch and worktree, with full control over repo changes and absolute local filesystem access. Each session changes production code, live-behavior code, config, prompts, selector/scheduler/execution logic, risk/safety/canary/runtime code, profiles, launchers, tests, verifiers, replay/capture builders, manifests, and integration artifacts wherever the evidence says the final system needs it.

Wave2 is not complete merely because it emits Wave3 prompts. It must prove, source-gap, or implement the master answers for broker-real hard-halt trades, material candidates, rejects, skips, no-trade rows, pending/no-fill lifecycle, accept/reject authority, scheduler allocation, execution entry, path behavior, MFE/MAE, maximum favorable profitability, lost-trade profit harvest failure, overnight/next-day stale-thesis behavior, stop width, target distance, fixed/static R target geometry, exit management, cost/swap/slippage, market-versus-system disposition, runtime authority, data capture, validation, and production-code disposition.

The prompt examples are minimum seeds. Wave2 must maintain an active question stack and discovered-hypothesis ledger, expand them as rows and code/config are inspected, analyze the coupled accept/reject/manage/exit/halt/capture system, and preserve all material questions before ranking. Any newly discovered intelligence must become an answered finding, implementation decision, Wave3 lane requirement, or exact source/capture blocker.

Wave3 lane set and launch order must be derived from Wave2's row-generated question stack, discovered hypotheses, interaction graph, and source-gap consequences, not only from the named lane list. Every Wave3 lane contract must carry `derived_from_question_ids` and `derived_from_interaction_ids` when Wave2 creates those artifacts.

Wave2 owns the next worktree plan. Do not create Wave3 worktrees until Wave2 publishes branch names, route contracts, prompt packs, merge gates, and the causal microscope artifacts that justify those lanes.

Sparse checkout paths:

- `.context`
- `src`
- `scripts`
- `tests`
- `config`
- `research/operations`
- `research/science_program_2026_05/04_goal_prompts`
- `shadow_logs`
- `pipeline_state`
- `knowledge_base/redacted_account_live_bee34003/trade_records`

Sparse absence is not a source gap. Goal sessions may use repo-relative paths, the Mac integration worktree, Mac package/evidence roots, route artifacts, and explicitly labeled VPS runtime paths.

Active Wave2 LFS posture:

- `scripts/generate_live_state.py` separates sparse-excluded LFS rows from true missing pointer-only rows.
- In the sparse Wave2 worktree, sparse-excluded LFS rows are not evidence of current-branch LFS object loss.
- Known historical LFS clean-filter dirt under `research/science_program_2026_05/06_outcome_testing/` is locally marked `assume-unchanged` in the Wave2 worktree only after confirmation it was legacy noise, not owner/session changes.
- Expand sparse checkout or use a route-specific evidence cache before making row-level claims from sparse-excluded evidence.

VPS shadow/runtime payload cache:

`vps_runtime_path:C:\Users\MSI\Documents\gtos_vps_shadow_runtime_evidence_2026_06_04`

The current final branch has zero missing current-branch LFS objects on the Mac integration workspace. Full row-level VPS-runtime provenance can still require direct source-machine transfer into the labeled VPS cache when a route must prove the payload came from the VPS runtime surface rather than from Git/LFS/package evidence.

Accepted Wave1 terminal inputs:

- Wave 1A hard-halt broker/candidate forensic matrix.
- Wave 1B V3 versus live authority gap audit.
- Wave 1C dual-broker failure/architecture audit.

Wave1A, Wave1B, and Wave1C are merged into local `main` through `d8a95f722`; Wave2 launch hardening is accepted locally through `26d2c698e`. Wave2 must consume those terminal artifacts from disk and must not relaunch Wave1 unless a verifier records a concrete defect or source hashes change.

## Starter Standard

Each starter must be one physical line and start:

`/goal Follow the full controlling prompt in <PROMPT_PATH> as the complete objective; do mandatory preflight and context refresh first;`

It must include:

- no chat-memory reliance;
- reread prompt/starter/doctrine/latest route artifacts after compaction/resume/interruption/uncertainty;
- exact evidence class;
- explicit build-and-ship authority;
- proof-or-impossibility to the full end;
- no arbitrary top-N;
- same-evidence-class blocker pursuit;
- required verifier/tests/manifest/completion audit;
- scoped commits if the route owns commits.

## Review Standard

The orchestrator must inspect artifacts from disk before accepting any closeout:

- completion audit;
- verifier result;
- manifest;
- terminal decision/decision ledger;
- source/gap/blocker/repair/saturation ledgers;
- full ledger coverage audit, row-key uniqueness, question-key uniqueness, source-hash/source-path coverage, and status coverage before any representative-row sampling;
- representative rows and status distributions from large JSONL only after full ledger coverage is proven;
- git diff, staged paths, and LFS status;
- focused tests or recorded test result.

Closeout prose is a claim. Files, hashes, verifiers, tests, ledgers, manifests, and broker truth are evidence.

## Immediate Launch Order

1. Run Wave2 Final Master After Hard Halt from `/Users/borr/Documents/gtos/worktrees/final-moonshot-wave2-master-2026-06-04`.
2. Use controlling prompt `research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_WAVE2_FINAL_MASTER_AFTER_HARD_HALT_GOAL_PROMPT_2026-06-04.md`.
3. Use starter `research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_WAVE2_FINAL_MASTER_AFTER_HARD_HALT_STARTER_2026-06-04.txt`.
4. Wave2 consumes accepted Wave1 artifacts from disk, performs the full causal microscope and unbounded question-discovery pass, and only then generates the Wave3 V4 prompt/worktree plan.
5. Launch V4 rebuild lanes only after Wave2 publishes hardened prompts, one-line starters, route contracts, verifier/test expectations, merge gates, and causal artifacts proving why each lane exists.

## Implementation Posture

Goal sessions have full control over repo changes. Change live-code and live-behavior code to build the final system.

The Mac research workspace is the orchestration/build surface. The VPS remains the production/runtime surface.
