# Final Moonshot VPS Shadow Runtime Evidence Transfer Goal Prompt - 2026-06-04

## Objective

Transfer the VPS shadow/runtime evidence payloads from the VPS source checkout or VPS local artifact store to the role-labeled runtime evidence cache for Wave 1 hard-halt forensics.

This is an evidence-transfer route. It is not a broker action, not a live trading operation, not a credential change, not a paid/vendor call, and not a remote push. Do not use GitHub LFS as the source-machine proof channel for this task; this route proves VPS/runtime source provenance with direct payload files, hashes, and manifests.

## Mandatory Context

Read from disk before acting:

- `AGENTS.md`
- `.context/LIVE_STATE.md`
- `.context/00_core/research_current_state.md`
- `.context/00_core/current_vnext_system_map.md`
- `.context/00_core/current_repo_reading_order.md`
- `.context/00_core/quick_reference_card.md`
- `.context/00_core/research_operating_doctrine.md`
- `.context/00_core/goal_session_research_discipline.md`
- `research/operations/final_moonshot_goal_session_execution_architecture_2026_06_04/FINAL_MOONSHOT_WAVE1_VPS_SHADOW_RUNTIME_EVIDENCE_CACHE_REQUIREMENTS_2026-06-04.md`
- `research/operations/final_moonshot_goal_session_execution_architecture_2026_06_04/FINAL_MOONSHOT_WAVE1_PROMPT_PACK_MANIFEST.json`

Do not rely on chat memory. Treat `goal_session_research_discipline.md` and `research_operating_doctrine.md` as active instructions, not background. Operationalize instruction-coverage into the transfer manifest, source-completeness ledger, verifier result, saturation/self-red-team note, and completion audit.

## Build And Boundary Posture

No conservative brake. Use constructive active creativity to get the required payloads moved and verified through the strongest available local transfer path.

This route owns evidence transfer, source completeness, manifest quality, payload verification, and exact blocker/source/capture requirements. It may write route artifacts, manifests, verifiers, helper scripts, and local transfer/staging outputs needed to complete the evidence transfer.

This route does not mutate broker account/order/history/deal/position state, perform a live trading broker operation, spend paid API/vendor budget, change credentials, remote publish, or change prompt/config/risk/execution/safety/canary/selector production behavior. If any of those surfaces become relevant, record the exact owner-action requirement and continue all non-dependent transfer work.

Result materialization standard: this route does not own exact-R, proxy-R, expectancy, or broker-real PnL claims. It must preserve result-use status, source-capture status, source completeness, branch decision, implementation decision, payload hash/size, and whether each downstream row-level claim is enabled by hydrated payload, local cache payload, pointer-only source, or exact source gap.

No arbitrary top-N, top 3/5/10, or number-limited cutoff. Preserve all material rows and every required payload path.

Full same-evidence-class pursuit is required. Literal impossibility means exactly every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action available on the VPS/source machine has been attempted or proven inapplicable before a payload is declared unavailable.

## Destination

Target cache root:

`vps_runtime_path:C:\Users\MSI\Documents\gtos_vps_shadow_runtime_evidence_2026_06_04`

Mirror repo-relative paths under that root.

Required destination manifest:

`vps_runtime_path:C:\Users\MSI\Documents\gtos_vps_shadow_runtime_evidence_2026_06_04\VPS_SHADOW_RUNTIME_EVIDENCE_MANIFEST_2026-06-04.json`

If direct write to the role-labeled cache path is unavailable, stage the payloads and manifest in a single clearly named transfer directory or archive on the VPS and report its exact path, size, hash manifest, and the exact owner action needed to move it to the target cache.

## Required Payloads

Copy these exact repo-relative paths when they exist as real payloads, not Git LFS pointer text:

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

Also include any tiny hard-halt emergency close audit files under:

`shadow_logs/redacted_account_live_bee34003/`

## Source Discovery

Start from disk. Do not rely on chat memory.

1. Run `git rev-parse --show-toplevel`, `git branch --show-current`, `git log -5 --oneline --decorate`, `git status --short`, and `git lfs status` in the VPS repo or temporary clean checkout that produced `d02a4c531 research: package shadow runtime evidence`.
2. Confirm whether `d02a4c531` is present locally. If not, discover the source checkout or artifact directory that still contains the pushed payloads.
3. For each required payload path, verify whether the file exists, its byte size, first line, and whether it is a Git LFS pointer. A pointer file starts with `version https://git-lfs.github.com/spec/v1`; pointer files are not payload access.
4. If a required payload is pointer-only on the VPS checkout, inspect the VPS local Git LFS object cache and any clean temporary worktree used for the successful push before declaring it unavailable.
5. Do not delete, rewrite, truncate, recompress in place, or move the only source payload.

## Manifest Contract

Create a JSON manifest with:

- `generated_at_utc`
- `source_machine`
- `source_repo_root`
- `source_branch`
- `source_head`
- `source_commit_expected`: `d02a4c531`
- `transfer_destination`
- `transfer_method`
- `payloads`
- `missing_or_pointer_only`
- `verification_commands`

Each `payloads` row must include:

- `relative_path`
- `source_path`
- `destination_path` or `staged_transfer_path`
- `size_bytes`
- `sha256`
- `first_line_class`: `payload` or `git_lfs_pointer`
- `source_commit`: `d02a4c531`
- `copied`: `true` or `false`

Each missing or pointer-only row must include:

- `relative_path`
- `searched_paths`
- `status`
- `exact_next_source_requirement`

Create a route-local transfer ledger under the source repo or staging directory:

`VPS_SHADOW_RUNTIME_EVIDENCE_TRANSFER_LEDGER_2026-06-04.jsonl`

Every required payload path gets at least one row with:

- `relative_path`
- `evidence_class`
- `source_status`
- `payload_status`
- `copy_status`
- `source_capture_status`
- `source_completeness_status`
- `branch_decision`
- `implementation_decision`
- `blocker_or_transfer_result`

## Transfer Rules

- Prefer direct file transfer to the laptop cache root when the VPS can write there.
- If direct transfer is unavailable, stage a transfer directory on the VPS that mirrors repo-relative paths and includes the manifest.
- If an archive is required, use a method that supports files larger than 2 GB and record the archive path, size, sha256, and extraction root. Do not use a tool that silently truncates large files.
- Preserve original filenames and repo-relative directory structure.
- Do not use `git add`, `git commit`, `git push`, or GitHub LFS for this transfer route.
- Do not hydrate broad unrelated LFS payloads unless a required payload cannot be found anywhere else and selective hydration is the only remaining route.

## Verification Before Handoff

Run or equivalent-check:

```powershell
Get-ChildItem <TRANSFER_ROOT> -Recurse -File | Select-Object FullName,Length
Get-FileHash <EACH_PAYLOAD> -Algorithm SHA256
Get-Content <EACH_PAYLOAD> -TotalCount 1
```

For JSON/JSONL payloads, sample parse a bounded set without loading the full file into memory.

Create a verifier result:

`VPS_SHADOW_RUNTIME_EVIDENCE_TRANSFER_VERIFICATION_RESULT_2026-06-04.json`

The verifier must check required path coverage, pointer detection, SHA256 presence, byte-size presence, copied/staged path existence, manifest parse, ledger parse, and missing/pointer-only rows with exact source requirements.

Create a saturation/self-red-team note:

`VPS_SHADOW_RUNTIME_EVIDENCE_TRANSFER_SATURATION_SELF_RED_TEAM_2026-06-04.md`

It must explicitly test for pointer-only false completion, partial top-N payload transfer, stale source checkout, accidental GitHub LFS dependency, archive truncation, missing manifest hashes, and missing owner-action clarity.

Create a completion audit:

`VPS_SHADOW_RUNTIME_EVIDENCE_TRANSFER_COMPLETION_AUDIT_2026-06-04.json`

It must state whether completion is `complete_payloads_landed`, `complete_staged_transfer_ready`, or `blocked_exact_source_requirement`.

Report:

- route/source directory;
- source branch and commit;
- copied payload count;
- missing/pointer-only payload count;
- total copied bytes;
- manifest path;
- transfer destination or staging artifact path;
- exact files not transferred and why;
- exact owner action if manual copy is still required.

Completion requires either the payloads and manifest landed in the research laptop cache root or a staged transfer artifact exists with manifest, hashes, and exact owner action to move it.
