# Parallel Goal Merge Playbook

Date: 2026-05-15
Status: active process control
Scope: parallel `/goal` worktrees, branch merge/review, and route sequencing

## Purpose

This playbook prevents parallel goal sessions from losing small details, overwriting each other, or turning closeout prose into accepted research state.

## Before Launch

For every parallel route, the orchestrator must confirm:

- unique worktree path;
- unique branch name;
- unique route directory;
- unique controlling prompt;
- unique output manifest;
- unique verifier/test ownership;
- no parent route running in parallel with children it may rewrite;
- no shared write targets except read-only context references.

For production-code integration, merge-conflict repair, VPS/local branch reconciliation, or any route that edits overlapping runtime files, use one owner integration session. Subagents may audit bounded shards, but they must not independently write the same runtime/config/profile/test files. Parallel goal sessions are for disjoint write surfaces; they are not a way to accelerate one contested merge.

Run prompt hardening checks before launch:

```powershell
python scripts/validate_goal_prompt_hardening.py research/science_program_2026_05/04_goal_prompts/<PROMPT>.md
```

If this Windows host cannot start `python` before script execution, use the equivalent `py -3` command and record the fallback rather than skipping the check.

If the script fails, fix the prompt or document exactly why the missing category is not applicable before giving the starter message.

The prompt must explicitly forbid arbitrary top-N/3/5/10 cutoffs for questions, ambiguities, possibilities, open doors, opportunities, blockers, source roots, branches, routes, and failure families. Ranked summaries are fine only when full ledgers preserve all material rows.

## While Running

The orchestrator should maintain a simple table:

- route id;
- worktree path;
- branch;
- prompt path;
- active evidence class;
- latest status;
- known blockers;
- expected terminal artifacts;
- whether output has been inspected from disk.

If a session reports a blocker, do not accept the word "blocked" until the same-evidence-class pursuit rule has been checked.

## On Completion

For each finished route:

1. Read the closeout only as a claim.
2. Run:

```powershell
python scripts/audit_goal_route_artifacts.py <ROUTE_DIR> --full-jsonl
```

Use `--profile launch-pack` for launch-pack directories and the default `standard` profile for completed route directories.

3. Inspect the route files directly:
   - completion audit;
   - decision ledger;
   - verification result;
   - output manifest;
   - blocker/repair/fail-closed/source-inventory/saturation ledgers;
   - large JSONL distributions and status counts;
   - next prompt or prompt pack.
4. Compare artifact facts against the closeout.
5. Re-run route verifier and focused tests when practical.
6. Check staged paths before commit or merge:

```powershell
git diff --cached --name-only
git status --short
```

7. For research merges, merge only scoped route/context files. Do not stage broad live/runtime/shadow dirt.
8. For production-code integration merges, stage only the deployable code/config/profile/verifier/launcher/test/context files explicitly owned by the integration route. Exclude raw research LFS ledgers unless the route proves they are required for runtime, production verifier execution, or deployment reproducibility.
9. Record runtime disposition for default-off, staged, production-active, and research-only components before committing.

## After Merge

After merging any branch:

- rerun the route verifier on main when possible;
- rerun focused tests for the merged route;
- regenerate `.context/LIVE_STATE.md`;
- update `.context/00_core/research_current_state.md` if the research map changed;
- update the route-status registry and question/ambiguity ledger;
- commit context refresh separately if needed.
- for production branches, run an LFS/scope review before push or handoff, and record exact VPS-side verification/deployment commands separately from local code integration.

## Gated Routes

For R7-style gated routes, the orchestrator must prove from disk that every prerequisite is:

- completed and accepted;
- completed and exactly bounded with proof; or
- explicitly not required by the gated route with a written reason.

If any prerequisite has only a pasted closeout and no disk review, do not launch the gated route.
