# GTOS Storage and Remotes Doctrine

Settled 2026-07-25 with the owner, at the close of the second audit. This is the operating truth for
where bytes live and how pushes work. Sessions follow this instead of improvising.

## The four tiers

| Tier | Holds | Rules |
|---|---|---|
| **GitHub** (`Borr1/ai-trading-agent`) | code, docs, configs, tests, small receipts — the lean lineage | Push normally. **LFS objects are intentionally NOT uploaded to GitHub** (billing): `lfs.allowincompletepush=true` is set in repo config, so pushes proceed while large LFS content stays local. A GitHub clone therefore yields LFS *pointers*; hydration needs this machine (or the iCloud archive). |
| **This Mac (local disk)** | the hot working set: checkouts, the LFS object store (`/Users/borr/GTOSActive/repo/.git/lfs`, ~55 GB), sealed campaign evidence in the replay worktree, caches | The only tier live processes read from. Keep hot; nothing here may depend on iCloud availability. |
| **iCloud Drive** (~1.5 TB free) | **write-once cold archives**: compressed evidence bundles, data-export archives, backups of irreplaceable ledgers | Three hard rules learned from the measured eviction incident (audit F20 — macOS silently evicted 53/96 bundle-bound files to zero-byte placeholders): (1) archive **large compressed files with manifests + SHA-256**, never trees of small hot files; (2) verify hashes on retrieval; (3) **no live or replay code path ever reads an iCloud path** — copy to local disk first. Caution: a running VM disk (colima/Docker) on iCloud is corruption/eviction-prone; keep VM disks local and archive only their *exports*. |
| **Windows VPS** (running, paid) | live/shadow runtime state: `pipeline_state/`, `shadow_logs/`, runtime-learning packets, halt/kill flags, MT5 terminals | The live filesystem of record. The W7 live-window per-trade ledgers exist **only** here until the Phase-1 forensics copies them off — treat that copy-off as urgent. |

## Push conventions (as executed 2026-07-25)

- **GitHub `main` = the prior lineage + one reviewed foundation-snapshot commit (`95105914f`)**
  carrying the full audit-era state (both audits, plan, prompts, fixes, doctrine). The granular
  July commit history (5 Opus-audit + 9 Fable-audit commits) is **archived locally** on
  `audit/claude-opus5-architecture-20260725`: it cannot land on GitHub because its history
  references four >2 GiB LFS ledgers that exceed GitHub's per-file LFS hard limit, and GitHub's
  built-in GH008 missing-LFS-object pre-receive check (not configurable per repo) rejects any push
  whose history references objects LFS storage cannot hold. Those four generated ledgers are
  untracked from the snapshot onward (paths listed in `.gitignore`); their bytes remain in the local
  LFS store.
- One-time LFS upload performed: **13 objects, ~0.83 GB** (July campaign ledgers ≤2 GiB each) — needed
  so the snapshot's pointer set passes GH008; inside GitHub's free LFS quota, and frozen: with no new
  LFS files ever added, this number never grows.
- **Standard push:** `GIT_LFS_SKIP_PUSH=1 git push` (LFS's own supported skip switch — hooks still
  run; `--no-verify` is blocked by policy and unnecessary). New commits add no LFS objects, so
  pushes stay pointer-clean by construction.
- History on GitHub contains ~4.8 GB of inline (non-LFS) evidence blobs from the pre-June-5 era;
  inline storage is free and stays as-is. **Generated evidence is not committed to git going
  forward** — local cold store (+ iCloud archive) with manifests, per the audits' demotion policy.
- Small checkout-critical data files (e.g. the 200 KB sleeve registry) may be converted from LFS to
  plain git files so fresh clones never see unhydratable pointers.
- Shell note that has now bitten twice: in zsh, always brace refspecs — `"${C}:refs/heads/main"` —
  a bare `$C:refs/...` gets eaten by the `:r` modifier.

## Data acquisition on this Mac

MT5 pulls run through the containerized python bridge (`siliconmetatrader5`, localhost:8001) under
colima/Docker — see `scripts/export_mt5_research_ohlcv.py` / `export_mt5_research_ticks.py`. Any
re-export must include the Phase-1 clock fix (broker-epoch → true UTC) before the data is used.
