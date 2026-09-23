# Session LH — archive hold manifest

Hold: **`/Users/borr/gtos-vps-archive-20260803/`** on the research laptop. Everything below was pulled
from the live VPS over SMB before the corresponding host deletion (ledger batches 7–10). Hashes are
sha256; "host" hashes were computed on the VPS before transfer, "mac" after landing.

| item | hold path | contents | verification |
|---|---|---|---|
| shadow_logs full copy | `shadow_logs/` | complete `ai-trading-agent\shadow_logs\` at pull time (3.6 GB — the W7 live-ledger copy-off priority from 2026-07-25) | rsync size/mtime; NOT deleted from host (live surface) — this is a safety copy, not a move |
| LFS archive | `lfs_archive_20260803.tar.gz` | 3,018 LFS objects (52.87 GB raw) absent from every other store: May science-program evidence, June lane routes, 53 no-ref orphans; OID→size list `lfs_archive_first2.txt` (committed beside this file) | host sha256 == mac sha256 (recorded below at pull) |
| packet repo | `packet_repo_20260803.bundle` + `packet-repo-dirty/` | `git bundle --all` of `ai-trading-agent-runtime-learning-packet` (HEAD `fc61a09fa`) + the 2 working-tree-modified files (`.context/LIVE_STATE.md`, `…wave_e…/VERIFICATION_RESULT.json`) | bundle verifies with `git bundle verify`; repo NOT deleted from host (live pipeline target) |
| codex sessions | `codex-sessions/` | `host-local\.codex\sessions` (403 MB) before deletion | size match |
| Hermes backups | `hermes-backups/` | `hermes-backup-20260704T100111Z.zip`, `hermes-backup-20260704T100714Z.zip` — Hermes's only non-empty restore points (its 2026-07-30 backup is 0 bytes) | host sha256 `3a67a7182520f050…` / `c255d9662163c01d…` == mac |
| Hermes migration-out | `hermes-migration-out/` | the 2026-07-09 migration tarballs + their own `sha256-manifest-20260709T045226Z.txt` (note: the manifest names a `user-jarvis-…` tarball that does not exist in the dir — pre-existing gap, archived as-found) | per the embedded manifest for the 045226Z generation |
| Downloads misc | `downloads-misc/` | `data-8827346f-…-batch-0000.zip` (24 MB, unknown provenance, 2026-07-04) | host sha256 `ee643cf2c6213189…` == mac |
| staging dirs | `staging/` | `GTOS_EXPORT_BARS_20260727` (64 MB), `gtos_exports` (47 MB), `GTOS_CARRY_20260729` (1 MB) | pulled whole before deletion |

Also committed beside this file: `lfs_store_list.txt` (full pre-deletion store inventory, 4,006 OIDs),
`lfs_delete_safe.txt` (244 Mac-covered OIDs deleted without archive), `lfs_archive_first2.txt`
(3,018 archived-then-deleted OIDs with sizes), `sparse_patterns.txt` (the 43-pattern sparse rule now
active on the host tree).

## Final hash record

*(filled at pull-verification time)*
