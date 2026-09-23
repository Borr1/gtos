# Mac Migration Package Evidence Index

Generated: 2026-06-04T21:16:00+08:00

Purpose: make the Mac package and runtime evidence discoverable to agents that start inside the repo, without moving cold payloads, LFS cache, or raw runtime dumps into current Git history.

## Current Decision

Do not bulk-copy the full package tree into the repo.

Keep the repo as the active code, context, tests, manifests, and route surface. Keep the Mac migration package as external cold evidence under the GTOS workspace root, and materialize only specific files when a route manifest or verifier proves they are needed.

## Active Repo

- Repo: `/Users/borr/Documents/gtos/repo/ai-trading-agent`
- Branch: `final-moonshot-context-repair-2026-06-04`
- HEAD: see `.context/LIVE_STATE.md` and `git rev-parse HEAD`
- Current-branch missing LFS objects: `0`
- Historical all-ref missing LFS objects: `280`

## External Package Roots

- Workspace root: `/Users/borr/Documents/gtos`
- Mac migration package: `/Users/borr/Documents/gtos/packages/GTOS_MAC_RESEARCH_MIGRATION_2026_06_04`
- Windows local LFS supplement: `/Users/borr/Documents/gtos/packages/GTOS_WINDOWS_LOCAL_LFS_SUPPLEMENT_2026_06_04`
- Windows research supplement audit: `/Users/borr/Documents/gtos/packages/GTOS_WINDOWS_RESEARCH_SUPPLEMENT_AUDIT_2026_06_04`
- Windows all-local refs bundle: `/Users/borr/Documents/gtos/packages/GTOS_WINDOWS_ALL_LOCAL_REFS_2026_06_04.bundle`
- Workspace audit manifests: `/Users/borr/Documents/gtos/manifests`

## Mac Package Contents

- `manifests/`: package ledgers and completion audits.
- `working_tree_payloads/`: captured uncommitted or non-recoverable repo state from the source machine.
- `emergency_hard_halt_evidence/`: hard-halt runtime evidence, pipeline state, shadow logs, knowledge-base evidence, and data snapshots.
- `repo_bundle/`: source repo all-refs bundle from the migration package.
- `lfs_objects/`: local LFS object cache from the source machine.

Approximate package size split on 2026-06-04:

- `lfs_objects/`: about `50G`
- `repo_bundle/`: about `760M`
- `emergency_hard_halt_evidence/`: about `566M`
- `working_tree_payloads/`: about `333M`
- `manifests/`: about `5.8M`

## Package-Only Evidence

Most package ledger paths are already present in the active repo or imported into `.git/lfs/objects`. A small package-only set remains outside the repo working tree:

- total package-ledger paths absent from repo working tree: `54`
- classes: `51` hydrated payloads, `2` runtime logs, `1` git bundle
- top-level areas: `pipeline_state`, `knowledge_base`, `shadow_logs`, `repo_bundle`
- declared size of absent package-ledger paths: about `800.6M`, dominated by the repo bundle

Use the package manifests to locate exact files and hashes before consuming any package-only evidence.

## Why Not Put It All In Git

Bulk-copying these packages into the repo would:

- duplicate LFS objects that are already imported into `.git/lfs/objects`;
- make ordinary clones, status, checkout, LFS fsck, and agent startup slower;
- mix mutable runtime state and cold evidence with active source code;
- risk committing lock files, daemon heartbeat files, and broker/runtime logs as if they were current authority;
- increase GitHub LFS and repository payload pressure without improving agent understanding;
- blur evidence classes that the final moonshot program explicitly preserves.

The repo should contain the map, hashes, manifests, summaries, tests, builders, and active route artifacts. The package tree should remain addressable cold evidence.

## Agent Use Rule

When a route needs evidence that is not in the repo working tree:

1. Check this file, `.context/00_core/local_heavy_data_inventory.md`, and `.context/00_core/repo_cleanup_and_staleness_policy.md`.
2. Search the active repo first.
3. Search `/Users/borr/Documents/gtos/packages/GTOS_MAC_RESEARCH_MIGRATION_2026_06_04` with a targeted path or manifest key.
4. Record the absolute source path, hash, file class, evidence class, and reason for use in the route audit.
5. Copy or materialize only the exact required file into the route/output location if the route needs local materialization.
6. Do not promote package-only runtime evidence to current production truth without a route manifest, verifier, and evidence-class statement.

## Cleanup Boundary

It is safe for routine agent work to delete staging folders such as `/Users/borr/Documents/gtos/scratch`. It is not safe to delete the Mac migration package until its package-only runtime/pipeline evidence has either been archived elsewhere or intentionally declared unnecessary by a dedicated cleanup route.

The workspace-level cleanup plan is:

`/Users/borr/Documents/gtos/manifests/WORKSPACE_CLEANUP_PLAN.md`
