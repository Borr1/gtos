# SCID Forward Capture Additive Implementation Dirty-State Ledger - 2026-05-12

## Pre-Edit Git Status

Command run before source edits:

```powershell
git status --short
```

Result: the worktree was already heavily dirty before this route made source changes. The dirty set included regenerated `.context/LIVE_STATE.md`, live runtime state under `pipeline_state/`, monitoring/index artifacts under `knowledge_base/`, many pre-existing research program-control reports, many live `shadow_logs/` files, two deleted compressed divergence logs, and untracked account-history/live-intelligence/archive/repair artifacts.

The command also emitted:

```text
warning: unable to access 'C:\Users\MSI/.config/git/ignore': Permission denied
```

## Unrelated Dirty Categories To Preserve

- Live/runtime state: `pipeline_state/*`, `shadow_logs/*`, `knowledge_base/*`.
- Existing research/program-control updates dated before this route.
- Existing repair and dedup manifests under `research/program_control/`.
- Existing untracked `research/archive/`, `research/live_intelligence/`, and `data/account_history/` trees.
- Existing deleted compressed divergence logs under `shadow_logs/`.

## Scoped Files This Route May Stage

- `src/research_infra/forward_capture.py`
- `src/components/pending_limit_lifecycle_logger.py`
- `tests/test_scid_forward_capture_runtime_adapter.py`
- `tests/test_scid_forward_capture_lifecycle_redaction.py`
- `scripts/verify_scid_forward_capture_schema.py`
- `.context/LIVE_STATE.md` after final regeneration
- `.context/00_core/research_current_state.md` if state update is required
- `research/science_program_2026_05/04_goal_prompts/G12_SCID_FORWARD_CAPTURE_ADDITIVE_IMPLEMENTATION_AUDIT_GOAL_PROMPT_2026-05-12.md`
- `research/science_program_2026_05/06_outcome_testing/scid_forward_capture_additive_implementation_from_parallel_g12_wave/**`

## Staging Rule

Do not use broad staging. Use explicit `git add` paths for the scoped files above only. Unrelated dirty runtime/research artifacts remain untouched.

