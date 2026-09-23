# SHADOW merge live — 2026-09-20

Owner NAME: Merge SHADOW + `GTOS_JEV_FLUID_GATES_SHADOW=1` only (no APPLY).

## Landed
- Overlay tip S16 stack into `judgment\warroom_shadow\` (sidecar; live `src\judgment` untouched)
- Backup: `host-local\redacted_host\repo\judgment\warroom_shadow_bak_20260920_035326`

## Flags
- `GTOS_JEV_FLUID_GATES_SHADOW=1` — ON for fluid sidecar runner
- `GTOS_JEV_FLUID_GATES_APPLY` — unset / never set this land
- `GTOS_DIG_MULTI_STAGE_GUARD_APPLY` — unset

## Runner
Scheduled task `GTOS_JEV_FLUID_SHADOW` → `judgment\warroom_shadow\scripts\run_fluid_shadow_loop.ps1`
