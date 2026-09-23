# Goal Session Launch Order - 2026-06-04

## Launch Surface

Use this Mac integration owner:

`/Users/borr/Documents/gtos/repo/ai-trading-agent`

Branch:

`final-moonshot-context-repair-2026-06-04`

Path model:

- repo artifacts use repo-relative paths;
- Mac package/evidence roots use `/Users/borr/Documents/gtos`;
- VPS production/runtime or runtime-evidence paths use explicit `vps_runtime_path` labels;
- historical Windows research-laptop paths are historical/audit context only.

## Build Authority

Final moonshot goal sessions have full control over repo changes and ship implementation, not only ledgers. Change production code, config, prompts, selector/scheduler/execution logic, risk and safety gates, canary/runtime behavior, profiles, launchers, tests, verifiers, and integration artifacts.

Use direct build language: full control over repo changes; change production/live code.

## Parallel Worktree Launch Mode

Use one integration owner plus three linked Wave 1 worktrees.

Integration owner:

`/Users/borr/Documents/gtos/repo/ai-trading-agent`

Prepared Wave 1 worktrees:

- `/Users/borr/Documents/gtos/worktrees/final-moonshot-wave1a-2026-06-04`
- `/Users/borr/Documents/gtos/worktrees/final-moonshot-wave1b-2026-06-04`
- `/Users/borr/Documents/gtos/worktrees/final-moonshot-wave1c-2026-06-04`

The goal sessions have absolute local filesystem access from their worktree and may inspect any relevant role-labeled path on the machine, including the Mac integration worktree, Mac package/evidence roots, repo-relative route artifacts, current Git/LFS object store, and explicit VPS runtime paths.

Run Wave 1A, Wave 1B, and Wave 1C in parallel in separate worktrees. Every route keeps full repo-control, parallel code-changing execution, isolated branches, scoped commits, and shared access to the same source/data universe.

Already-prepared Mac setup:

```sh
cd /Users/borr/Documents/gtos/repo/ai-trading-agent
git worktree list
```

Expected worktrees:

- `final-moonshot-wave1a-2026-06-04`
- `final-moonshot-wave1b-2026-06-04`
- `final-moonshot-wave1c-2026-06-04`

Run this at the start of each Wave 1 session:

```sh
cd /Users/borr/Documents/gtos/worktrees/final-moonshot-wave1a-2026-06-04
python3 scripts/generate_live_state.py
```

Use the matching folder/branch for Wave 1B and Wave 1C. Keep the final-moonshot integration worktree as the owner that reviews and merges scoped commits.

VPS shadow/runtime payload cache:

`vps_runtime_path:C:\Users\MSI\Documents\gtos_vps_shadow_runtime_evidence_2026_06_04`

The Mac integration branch has zero missing current-branch LFS objects. A route that needs VPS source-machine runtime provenance must still use the labeled VPS runtime cache or a route-local evidence transfer manifest rather than treating a Mac path as VPS runtime truth.

## Pre-Launch Evidence Transfer

If the cache root is empty or missing required payloads, run the VPS evidence-transfer starter before Wave 1 sessions make row-level runtime-log claims:

`research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_VPS_SHADOW_RUNTIME_EVIDENCE_TRANSFER_STARTER_2026-06-04.txt`

Route-local copy:

`research/operations/final_moonshot_goal_session_execution_architecture_2026_06_04/FINAL_MOONSHOT_VPS_SHADOW_RUNTIME_EVIDENCE_TRANSFER_STARTER_2026-06-04.txt`

Controlling prompt:

`research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_VPS_SHADOW_RUNTIME_EVIDENCE_TRANSFER_GOAL_PROMPT_2026-06-04.md`

This transfer route discovers the VPS source payloads from disk, copies only the required payload set, computes SHA256/size, creates the cache manifest, and avoids GitHub LFS as the transfer channel.

## Canonical Wave 1 Prompt Pack

Prompt pack manifest:

`research/operations/final_moonshot_goal_session_execution_architecture_2026_06_04/FINAL_MOONSHOT_WAVE1_PROMPT_PACK_MANIFEST.json`

Canonical prompts:

- `research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_WAVE1A_HARD_HALT_FORENSIC_MATRIX_GOAL_PROMPT_2026-06-04.md`
- `research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_WAVE1B_V3_LIVE_AUTHORITY_GAP_GOAL_PROMPT_2026-06-04.md`
- `research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_WAVE1C_DUAL_BROKER_ARCHITECTURE_GOAL_PROMPT_2026-06-04.md`

Canonical starters:

- `research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_WAVE1A_HARD_HALT_FORENSIC_MATRIX_STARTER_2026-06-04.txt`
- `research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_WAVE1B_V3_LIVE_AUTHORITY_GAP_STARTER_2026-06-04.txt`
- `research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_WAVE1C_DUAL_BROKER_ARCHITECTURE_STARTER_2026-06-04.txt`

Route-local starter copies:

- `research/operations/final_moonshot_goal_session_execution_architecture_2026_06_04/FINAL_MOONSHOT_WAVE1A_STARTER_2026-06-04.txt`
- `research/operations/final_moonshot_goal_session_execution_architecture_2026_06_04/FINAL_MOONSHOT_WAVE1B_STARTER_2026-06-04.txt`
- `research/operations/final_moonshot_goal_session_execution_architecture_2026_06_04/FINAL_MOONSHOT_WAVE1C_STARTER_2026-06-04.txt`

## Wave 1 Parallel Routes

### Wave 1A - Hard-Halt Broker/Candidate Forensic Matrix

Objective: join all `77` recent redacted_account GTOS trades to broker groups, deals, orders, trade records, runtime decisions, selected-cell evidence, cost/swap/slippage, M1/tick path, exposure state, and failure tags.

Owned evidence class: broker-real redacted_account PnL/cash plus source-bound joins and exact missing-source proof.

Worktree:

`/Users/borr/Documents/gtos/worktrees/final-moonshot-wave1a-2026-06-04`

Primary route path:

`research/operations/final_moonshot_wave1a_hard_halt_forensic_matrix_2026_06_04/`

Prompt:

`research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_WAVE1A_HARD_HALT_FORENSIC_MATRIX_GOAL_PROMPT_2026-06-04.md`

Starter:

`research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_WAVE1A_HARD_HALT_FORENSIC_MATRIX_STARTER_2026-06-04.txt`

### Wave 1B - V3 Versus Live Authority Gap Audit

Objective: classify every material hard-halt live candidate/trade as Selector V3, Scheduler V3, Execution Policy V3 active, default-off, provenance-only, fallback, hybrid, missing, or divergent.

Owned evidence class: live authority versus default-off research/package/provenance boundary.

Worktree:

`/Users/borr/Documents/gtos/worktrees/final-moonshot-wave1b-2026-06-04`

Primary route path:

`research/operations/final_moonshot_wave1b_v3_live_authority_gap_2026_06_04/`

Prompt:

`research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_WAVE1B_V3_LIVE_AUTHORITY_GAP_GOAL_PROMPT_2026-06-04.md`

Starter:

`research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_WAVE1B_V3_LIVE_AUTHORITY_GAP_STARTER_2026-06-04.txt`

### Wave 1C - Dual-Broker Failure/Architecture Audit

Objective: separate redacted_account full runtime from FTMO follower/projector evidence; audit namespace, broker-local risk, lifecycle, target state, crash recovery, cost/spec/session, and whether FTMO should remain follower-only or gain broker-local lifecycle authority.

Owned evidence class: dual-broker runtime/supervisor/follower evidence, not redacted_account broker PnL unless joined explicitly.

Worktree:

`/Users/borr/Documents/gtos/worktrees/final-moonshot-wave1c-2026-06-04`

Primary route path:

`research/operations/final_moonshot_wave1c_dual_broker_architecture_2026_06_04/`

Prompt:

`research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_WAVE1C_DUAL_BROKER_ARCHITECTURE_GOAL_PROMPT_2026-06-04.md`

Starter:

`research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_WAVE1C_DUAL_BROKER_ARCHITECTURE_STARTER_2026-06-04.txt`

## Sequencing

Wave 1A, 1B, and 1C run in parallel worktrees as code-changing goal sessions. Each route gets full repo-control, full source/data access, subagent reviews, verifier/test execution, staged-path review, LFS/materialization review, completion audit, and a scoped commit.

The integration owner reviews the scoped route commits from disk, resolves contested production-code surfaces, and merges the branches before Final Master After Hard Halt.

Final Master After Hard Halt must wait for Wave 1 artifacts or exact blockers:

`research/operations/final_moonshot_master_after_hard_halt_2026_06_04/`

## Prompt Requirements

Each prompt must name:

- `.context/LIVE_STATE.md`
- `.context/00_core/current_vnext_system_map.md`
- `.context/00_core/current_repo_reading_order.md`
- `.context/00_core/quick_reference_card.md`
- `.context/00_core/final_moonshot_post_hard_halt_research_plan.md`
- `.context/00_core/final_moonshot_goal_session_execution_architecture.md`
- `.context/00_core/final_moonshot_central_orchestrator_successor_brief.md`
- `.context/00_core/research_operating_doctrine.md`
- `.context/00_core/goal_session_research_discipline.md`
- route-specific evidence paths.

Each prompt must declare that the session has full control over repo changes and changes production/live code to build the final system.

Each prompt must require:

- full ledgers, not top-N closure;
- implementation decisions and code/config changes;
- same-evidence-class blocker pursuit;
- LFS/data materialization ledger;
- verifier;
- manifest;
- saturation/self-red-team;
- completion audit.
