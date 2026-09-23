# Integration Context Anchor

Generated: `2026-06-01T22:43:52.304207+00:00`

Controlling prompt: `research/science_program_2026_05/04_goal_prompts/VNEXT_VPS_LOCAL_V3_FTMO_PRODUCTION_INTEGRATION_GOAL_PROMPT_2026-06-02.md`
Current branch: `vnext-prod-integration-vps-v3-ftmo-2026-06-02`
Local HEAD: `b6a91c9a13be764eedc00332b8a33b8c677d7de5`
VPS branch: `origin/vps-prod-live-sync-2026-06-02`
VPS HEAD: `6726b0804582eaddacb9629eb82e5e9b90b8157e`
Merge base: `6726b0804582eaddacb9629eb82e5e9b90b8157e`

## Evidence Class

Production-code integration. Local code/config/profile/verifier/launcher/watchdog/test/handoff edits are authorized by the prompt. Broker/account/order/deal/position mutation, credentials, paid calls, remote push, and VPS live restart/reload are not authorized here.

## Required Context Read

The session regenerated `.context/LIVE_STATE.md` and reread AGENTS, current vNext map, reading order, quick reference, research/current doctrine, orchestration controls, moonshot vision, cleanup/scope policy, latest handoff, the controlling prompt, local HEAD, and `origin/vps-prod-live-sync-2026-06-02` from disk.

## Isolated Review Passes

- VPS production auditor: `VPS_PRODUCTION_CHANGE_INVENTORY.jsonl`.
- Local V3/FTMO auditor: `LOCAL_V3_FTMO_PRODUCTION_CHANGE_INVENTORY.jsonl`.
- Conflict integrator: `CONFLICT_RESOLUTION_LEDGER.jsonl`.
- Verifier architect: `VERIFICATION_MATRIX.json` and route verifier.
- LFS/scope auditor: `LFS_AND_PRODUCTION_SCOPE_LEDGER.jsonl`.

## Current Stop Condition

The route is complete only after conflicts are resolved, semantic overlaps reviewed, verification commands recorded, scope checks pass, output manifest and completion audit are final, and a scoped merge commit is created on `vnext-prod-integration-vps-v3-ftmo-2026-06-02`.
