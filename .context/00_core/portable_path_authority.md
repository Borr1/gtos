# Portable Path Authority

Generated: 2026-06-04
Status: active final-moonshot path model

## Rule

GTOS final moonshot work is portable across the Mac research/orchestration workspace and the VPS production/runtime surface.

Use repo-relative paths for repo artifacts. Use workspace variables for local evidence/package roots. Preserve true VPS production/runtime paths only when they are explicitly labeled as VPS runtime paths. Historical Windows research-laptop paths are historical evidence only and must not appear as active launch instructions.

## Path Roles

| Role | Meaning | Current value or example |
|---|---|---|
| `repo_relative` | File inside the Git repo. Preferred for prompts, route artifacts, code, tests, configs, and context files. | `research/operations/final_moonshot_goal_session_execution_architecture_2026_06_04/GOAL_SESSION_LAUNCH_ORDER_2026-06-04.md` |
| `mac_research_workspace` | Durable Mac orchestration workspace root. Use only for Mac setup, package evidence, worktrees, and local verification. | `/Users/borr/Documents/gtos` |
| `mac_integration_repo` | Active Mac integration checkout. | `/Users/borr/Documents/gtos/repo/ai-trading-agent` |
| `mac_wave_worktree_root` | Parent for prepared Wave 1 Mac sparse worktrees. | `/Users/borr/Documents/gtos/worktrees` |
| `workspace_variable` | Portable symbolic variable for non-repo local roots. | `GTOS_WORKSPACE_ROOT=/Users/borr/Documents/gtos` |
| `package_import_path` | Local extracted migration or LFS package root. Never generic runtime truth. | `$GTOS_WORKSPACE_ROOT/packages/GTOS_MAC_RESEARCH_MIGRATION_2026_06_04` |
| `vps_runtime_path` | True Windows/VPS runtime or runtime-evidence path. Preserve with this label. | `C:\\Users\\MSI\\Documents\\gtos_vps_shadow_runtime_evidence_2026_06_04` |
| `historical_windows_research_path` | Old Windows research-laptop checkout/cache path. Historical/audit evidence only. | `C:\\Users\\MSI\\Documents\\ai-trading-agent-final-moonshot` |
| `hardcoded_bug` | Unlabeled machine-specific path inside active launch/code/config that would break another role. | must be repaired before launch |

## Active Mac Paths

- `GTOS_WORKSPACE_ROOT=/Users/borr/Documents/gtos`
- `GTOS_REPO_ROOT=/Users/borr/Documents/gtos/repo/ai-trading-agent`
- `GTOS_PACKAGE_ROOT=/Users/borr/Documents/gtos/packages`
- `GTOS_WORKTREE_ROOT=/Users/borr/Documents/gtos/worktrees`

Prepared Wave 1 worktrees:

- `/Users/borr/Documents/gtos/worktrees/final-moonshot-wave1a-2026-06-04`
- `/Users/borr/Documents/gtos/worktrees/final-moonshot-wave1b-2026-06-04`
- `/Users/borr/Documents/gtos/worktrees/final-moonshot-wave1c-2026-06-04`

## Active VPS Runtime Path

The VPS runtime/evidence cache path remains valid only when role-labeled:

`vps_runtime_path:C:\\Users\\MSI\\Documents\\gtos_vps_shadow_runtime_evidence_2026_06_04`

Do not convert true VPS runtime paths to Mac paths. Use Mac paths for research orchestration and package evidence. Use `vps_runtime_path` for VPS runtime/evidence transfer, production/runtime verification, and source-machine payload provenance.

## Launch Constraint

Storage availability is not a launch constraint or prompt psychology. Goal sessions use the prepared worktrees and materialize evidence by route need and evidence class, not by fear of workspace size.
