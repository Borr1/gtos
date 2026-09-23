# Session LH — VPS deletion ledger, 2026-08-03

Owner authority: Borhen's standing approval (commission §1, verbatim: "it has my explicit approval to delete
the things not needed there or stale or too old to save disk space"). Rules applied: §5 of the commission —
pull-before-delete for anything not recoverable; tracked-and-unmodified git content recoverable from the
host's own `.git` (sparse-checkout removes worktree copies only, zero object loss); LFS objects follow the
§5.c archive rule. Free-space checkpoints are `Win32_LogicalDisk` reads.

**C: at session start: 1.42 GB free** (after the commissioning session's emergency lane: recycle bin, temp
>1 day, WU download cache, crash dumps, hibernation off — 0.84 → 1.42).

| # | batch | path(s) | size | category | free after |
|---|---|---|---|---|---|
| 1 | Working-tree sparse-checkout exclude (43 patterns): 17 `research/operations/vnext_*` June lane routes, `research/program_control/`, 24 unreferenced `research/science_program_2026_05/06_outcome_testing/*` dirs (incl. `weekend_mechanical_edge_factory_moonshot` 14.2 GB) | live tree `research/` | **36.6 GB** | `SAFE-DELETE` (worktree only; all tracked-and-unmodified, bytes remain in host `.git` — LFS-backed content additionally archived in batch 7 before store deletion; git-restorable via `git sparse-checkout disable`) | 1.42 → **37.99** |
| 2 | 244 LFS store objects present in Mac store `/Users/borr/GTOSActive/repo/.git/lfs` (OID list `lfs_delete_safe.txt`) | `.git/lfs/objects/…` | 0.72 GB | `SAFE-DELETE` (verified on Mac store by OID) | — |
| 3 | 16 orphaned pack `.idx` files (no corresponding `.pack`; `git count-objects` garbage) | `.git/objects/pack/` | ~0.4 MB | `SAFE-DELETE` | — |
| 4 | Package-manager caches: `.codex\packages` 2,619 MB, `.codex\.tmp` 78 MB, `npm-cache` 861 MB, `pip` 386 MB, `uv` (Local cache, not the Roaming runtime) 1,045 MB | `host-local\…` | 4.9 GB | `SAFE-DELETE` (re-downloadable caches; Roaming\uv python runtime untouched — openviking runs from it) | — |
| 5 | Superseded installers: Edge WebView2 193 MB, VSCode setup 169 MB, mt5setup 22 MB, 2× Store installer, Codex installer, host-mesh-setup | `…\Downloads` | 0.39 GB | `SAFE-DELETE` (re-downloadable) | — |
| 6 | 13 stale `tmp*.db`/`-journal` litter files (0-byte, >12 h old) | `C:\ProgramData\HermesAgent\backups` | ~0 | `SAFE-DELETE` | batches 2–6: 37.75 → **42.69** (tar concurrently consuming ~0.7 GB) |
| 7 | 3,018 LFS objects absent from every reachable store (May science-program evidence 24.7 GB, June lane routes ~8 GB, 53 no-ref orphans 18.8 GB, misc) | `.git/lfs/objects/…` | **52.87 GB** | `ARCHIVED-THEN-DELETED` — single `lfs_archive_20260803.tar.gz` built host-side (BelowNormal), pulled to `~/gtos-vps-archive-20260803/`, sha256-verified both sides before store deletion; OID list `lfs_archive_first2.txt`, sha256 in `ARCHIVE_HOLD_MANIFEST.md` | pending |
| 8 | `.codex\sessions` 403 MB | `host-local\.codex` | 0.40 GB | `ARCHIVED-THEN-DELETED` (pulled to archive hold first) | pending |
| 9 | Hermes July backups 2× 621 MB + `migration-out` 443 MB | `C:\ProgramData\HermesAgent` | 1.66 GB | `ARCHIVED-THEN-DELETED` (the 2026-07-30 Hermes backup is 0 bytes — these two are Hermes's only good restore points, hence archive-first; broken-backup note on the owner sheet) | pending |
| 10 | Staging: `GTOS_EXPORT_BARS_20260727` 64 MB, `gtos_exports` 47 MB, `GTOS_CARRY_20260729` 1 MB | `C:\` | 0.11 GB | `ARCHIVED-THEN-DELETED` (pulled whole to archive hold — cheaper than per-file provenance hunting) | pending |
| — | `pagefile.sys` 15.19 GB → propose fixed 6–8 GB | `C:\` | up to ~8 GB | `RECOMMENDED-ONLY` (needs reboot — owner's schedule) | — |

**Kept deliberately (not deletions, recorded so nobody re-litigates):** MT5 `Bases` 12.4 + 6.5 GB (price
history the books chart from; `logs`/`Tester` measured trivial — the §5.d expectation of log bloat was wrong);
`C:\GTOS` 656 MB (live aux tree); Ollama models (2×~1.5 GB, active Hermes LLM stack); `ms-playwright` 0.67 GB
(possible Hermes automation dependency); `AppData\Roaming\MetaQuotes` 2.96 GB (MT5 state); `Programs` 5.7 GB
(installed apps); the packet repo 6.2 GB (live pipeline target, archived not deleted); all `pipeline_state/`,
current shadow logs/packets, tokens, both repo trees' tracked content per the git rules.
