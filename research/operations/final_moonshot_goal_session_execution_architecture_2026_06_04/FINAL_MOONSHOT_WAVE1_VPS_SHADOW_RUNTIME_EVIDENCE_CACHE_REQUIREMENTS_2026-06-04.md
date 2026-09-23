# Final Moonshot Wave 1 VPS Shadow Runtime Evidence Cache Requirements - 2026-06-04

## Purpose

The final-moonshot branch descends from `d02a4c531 research: package shadow runtime evidence`, and the Mac workspace has imported current-branch LFS payloads.

Pointer presence alone is not source-machine runtime provenance. Full Wave 1 runtime-log forensics may use Mac LFS/package evidence, but any claim that specifically depends on the VPS production/runtime source surface must use direct VPS transfer into the role-labeled cache below or a route-local manifest proving equivalent source provenance.

Operational transfer starter:

`research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_VPS_SHADOW_RUNTIME_EVIDENCE_TRANSFER_STARTER_2026-06-04.txt`

Controlling transfer prompt:

`research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_VPS_SHADOW_RUNTIME_EVIDENCE_TRANSFER_GOAL_PROMPT_2026-06-04.md`

## Target Cache Root

`vps_runtime_path:C:\Users\MSI\Documents\gtos_vps_shadow_runtime_evidence_2026_06_04`

Mirror repo-relative paths under this root.

Example:

`vps_runtime_path:C:\Users\MSI\Documents\gtos_vps_shadow_runtime_evidence_2026_06_04\shadow_logs\gtos_vnext_runtime_decisions.jsonl`

## Required Payloads

- `shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl`
- `shadow_logs/gtos_vnext_runtime_decisions.jsonl`
- `shadow_logs/strategy_follow_evaluations.jsonl`
- `shadow_logs/gtos_vnext_replacement_monitoring.jsonl`
- `shadow_logs/pending_limit_lifecycle.jsonl`
- `shadow_logs/ml_shadow_predictions.jsonl`
- `shadow_logs/v2b_forward_pair_resolution_audit.jsonl`
- `shadow_logs/live_candidate_strategy_rollups.jsonl`
- `shadow_logs/prefill_delivery_path_audit.jsonl`
- `research/program_control/SHADOW_LOG_INTEGRITY_VERIFICATION_2026-05-04.json`

## Required Cache Manifest

Create:

`vps_runtime_path:C:\Users\MSI\Documents\gtos_vps_shadow_runtime_evidence_2026_06_04\VPS_SHADOW_RUNTIME_EVIDENCE_MANIFEST_2026-06-04.json`

Each payload row must include:

- `relative_path`
- `source_vps_path`
- `size_bytes`
- `sha256`
- `source_commit`
- `captured_at_utc`
- `transfer_method`

Set `source_commit` to `d02a4c531` for payloads copied from the pushed VPS package.

## Verification Commands

From any Mac Wave 1 worktree:

```sh
python3 scripts/generate_live_state.py
git lfs ls-files --long
```

On the VPS/runtime surface, verify the role-labeled cache path with PowerShell:

```powershell
Get-ChildItem C:\Users\MSI\Documents\gtos_vps_shadow_runtime_evidence_2026_06_04 -Recurse | Select-Object FullName,Length
Get-Content C:\Users\MSI\Documents\gtos_vps_shadow_runtime_evidence_2026_06_04\VPS_SHADOW_RUNTIME_EVIDENCE_MANIFEST_2026-06-04.json -TotalCount 80
```

Wave 1 sessions must record whether a row-level claim came from:

- committed hydrated LFS payload;
- local VPS evidence cache payload;
- committed pointer only;
- smaller repo-local non-LFS artifact;
- source gap with exact transfer/hydration requirement.
