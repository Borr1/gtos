# STORAGE RECLAMATION V1 — 2026-08-12

Owner-authorized disk reclamation on the GTOS research laptop, to make room for a large
continuous replay program. Owner word: *"make sure the disk is there and anything that we
dont need either gets deleted or archived in the icloud drive to save storage. Same with
lfs and everything."*

**Nothing live was touched.** No broker path, no config, no armed-set artifact, no VPS.
The R2 decision contract was measured before and after the one git-level operation and did
not move (§6).

---

## 1. Before / after

| | free on `/System/Volumes/Data` (460 GB volume) |
|---|---|
| session start | **27.00 GB** |
| session end | **86.64 GB** |
| **reclaimed this session** | **+59.64 GB** |

`GTOSActive` went **157.0 GB → 103.26 GB**. (Context: the volume was at 4.4 GB free before
the orchestrator removed 24 already-merged worktrees ahead of this session, so the full
recovery across both passes is 4.4 → 86.64 GB.)

**The 150 GB target was not reached, and it is not reachable inside GTOS.** §7 states the
exact boundary and prices the next 20 GB.

---

## 2. Archive of record

**Location:** `~/Library/Mobile Documents/com~apple~CloudDocs/GTOS-Cold-Archive/2026-08-12 Storage Reclamation/`
(4.25 GB, following the existing `GTOS-Cold-Archive/` dated-folder convention.)

| manifest | rows |
|---|---|
| `ARCHIVE_MANIFEST.jsonl` — sealed-arm intelligence | 6,311 |
| `WORKTREE_UNCOMMITTED_MANIFEST.jsonl` — uncommitted worktree content | 638 |
| **total files archived** | **6,949** |
| **verified by sha256 after write** | **6,949 (100 %)** |
| unverified | 0 |

Committed copies of both manifests sit beside this file as `.jsonl.gz`.
Each row carries `origin_worktree`, `path`, `size_bytes`, `sha256`,
`verified_in_archive`, `storage`, `archive`.

**Verification method.** Every source file was sha256'd, written into a `tar.zst`, and then
the *finished archive* was streamed back and every member re-hashed and compared. This is a
read-back proof, not a copy-and-trust. iCloud upload is asynchronous; the local copies exist
and hash correctly, which is what was required.

One subtlety worth recording: 22 members of the engine archive are stored by tar as
**hardlink entries** (the source tree had 560 `nlink>1` files). They were each resolved to
their link target and that target's content hash matched the expected sha256 — so they are
verified, and extraction reproduces them. They are stamped
`storage: "tar hardlink member -> verified identical-content member"`.

### Archives written

| archive | source files | source | compressed |
|---|---:|---:|---:|
| `fa2-integration-20260803-intelligence.tar.zst` | 484 | 1.38 GB | 0.99 GB |
| `replay-accel-engine-20260719-intelligence.tar.zst` | 3,277 | 3.42 GB | 2.00 GB |
| `replay-accel-attempt5-20260719-intelligence.tar.zst` | 2,550 | 0.75 GB | 0.28 GB |
| 16 × `<worktree>-uncommitted.tar.zst` | 638 | — | 0.97 GB |

**Keep rule applied.** For every sealed-arm directory: economics receipts, semantic
diagnostics, manifests, summary JSON and any ledger **≤ 50 MB** were archived. Dropped as
regenerable bulk: `compact-event-shards/` (8.49 GB in fa2 alone), `prepared-day-packs/`,
`attempt_5_tick_sparse_cache/` (content-addressed, 4.15 GB), `__pycache__`, `scratch/`, and
the > 50 MB raw exhaust ledgers (`*_MISSED_OPPORTUNITY_LEDGER`,
`*_SEMANTIC_ORDER_PREIMAGE_LEDGER`).

---

## 3. The three large worktrees

### `fa2-integration-20260803` — 20.41 GB

- Branch `phase19/march-confirm` @ `870d4cb53`. **Not** an ancestor of `origin/main`.
- **History preserved twice.** (a) `git worktree remove` does not delete a branch ref — the
  branch still resolves in `repo/.git` at `870d4cb53`. (b) An independent bundle exists at
  `hermes-evidence-hold-20260727/branch-bundles-20260810/phase19-march-confirm-with-spent-markers.bundle`
  (90.9 MB) whose `git bundle list-heads` reports exactly
  `870d4cb535ed225faa587b9823ca9c28320dcdd2 refs/heads/phase19/march-confirm` — a byte-level
  match to the removed worktree's HEAD.
- 0 tracked modifications; 2,240 untracked files (12.48 GB). The six March sealed-arm
  outputs (`FA2_M_ARM_I`..`V`, `FA2_M_R0`) and the six 2025 lane receipts
  (`LP_{JUN,AUG,SEP,OCT,NOV,DEC}_2025_S0R0_RECEIPT_ECONOMICS.json.gz`) are inside the
  archived 484-file intelligence set. ~99 machine-hours of arm *conclusions* are preserved;
  the regenerable per-day exhaust is gone.

### `replay-accel-engine-20260719` — 9.25 GB

- Branch `replay-accel-engine-20260719` @ `a3badc054`, ref intact in `repo/.git`.
- Contained 41 symlinks pointing at
  `iCloud/GTOS-Cold-Storage/replay-accel-engine-20260719/2026-07-23/superseded-replay-runs`
  (34 entries) — a **prior** July archival of this same tree. Verified: zero dangling
  symlinks, so that archive still resolves. Removing the worktree removed only the links.
- 3,277 intelligence files archived.

### `replay-accel-attempt5-20260719` — 5.26 GB

- Detached HEAD `cca259054`. **Pinned before removal** as tag
  `archived/replay-accel-attempt5-20260719` so the commit cannot become unreachable.
- 4.15 GB of it was `attempt_5_tick_sparse_cache/` — an 8-entry content-addressed cache,
  regenerable. 2,550 intelligence files archived.
- `replay-accel-attempt3-20260719` (0.03 GB, detached `0ca5882b1`) removed alongside,
  pinned as tag `archived/replay-accel-attempt3-20260719`.

Removal of the first two needed `chmod -R u+w` first: the `.hermes/evidence/phase-d/*`
trees are **sealed read-only** by design. Only paths under `GTOSActive/worktrees/` were
ever chmod'd; the evidence hold was never touched.

---

## 4. Worktrees removed (22, 17.66 GB)

Removing a worktree does not delete its branch, so committed work is never at risk. For each,
all uncommitted content (untracked + modified, ≤ 50 MB, non-bulk) was archived and verified
**before** removal.

| worktree | GB | vs `origin/main` | HEAD | uncommitted archived |
|---|---:|---|---|---:|
| `wave19-breaker-folds-20260801` | 1.75 | NOT merged | `7f9ab73c2` | 32 |
| `wave19-broad-forensic-20260801` | 1.58 | NOT merged | `ca7dec531` | 310 |
| `wave16-rematerialization-20260731` | 1.53 | merged | `31ece3744` | 25 |
| `wave18-true-utc-factory-20260801` | 1.12 | merged | `ac3c66d60` | 15 |
| `wave15-lane-footprint-20260731` | 0.99 | merged | `ccdd9c166` | 87 |
| `wave21-quote-cost-compatibility-20260809` | 0.98 | merged | `4a8174249` | 3 |
| `wave21-probability-truth-parent-ab-20260809` | 0.98 | merged | `e6192a226` | 0 |
| `codex-predicate-falsifier.VnpkSi` | 0.98 | merged | `5a1b66cb7` | 0 |
| `wave21-timewarp-flow-truth-20260808` | 0.98 | merged | `e8d9fcf29` | 9 |
| `wave20-p1-m1-verifier-repair-20260802` | 0.83 | NOT merged | `85533d2a1` | 0 |
| `wave21-w7-recost-current` | 0.70 | merged | `ba30c0d4b` | 9 |
| `_merge-main-tmp` | 0.65 | merged | `6f061af2d` | 2 |
| `wave21-quote-execution-truth` | 0.50 | merged | `439020364` | 116 |
| `wave19-sol-grid-20260801` | 0.49 | NOT merged | `6ef09b8f4` | 1 |
| `wave21-verification` | 0.47 | merged | `3ed0da7f7` | 6 |
| `wave21-selector-truth` | 0.46 | merged | `07f81cc1f` | 4 |
| `wave21-cost-truth` | 0.46 | merged | `38e65184d` | 5 |
| `wave21-scheduler-risk-truth` | 0.46 | merged | `c5857b0d3` | 6 |
| `wave21-candidate-semantics` | 0.46 | NOT merged | `8ecc79018` | 8 |
| `wave21-comparator-start-939` | 0.46 | merged | `9392e9bbd` | 0 |
| `wave21-comparator-foundation-5d3` | 0.45 | merged | `5d3fe32c7` | 0 |
| `wave21-comparator-forward-ca7` | 0.39 | NOT merged | `ca7dec531` | 0 |

Full machine-readable record: `WORKTREE_REMOVAL_LOG.json` in the archive folder.

### Worktrees deliberately kept

| worktree | GB | why |
|---|---:|---|
| `wave21-rule-v2-20260811` | 1.07 | Rule V2 is commissioned and active (owner "proceed", 2026-08-12) |
| `wave21-full-system-coherence-20260809` | 0.99 | the JunJul generation tree; carries the disclosed uncommitted `JUNJUL_MACHINERY_PATCH_V1..V1_3` state |
| `march-durable-preservation-20260808` | 1.07 | named durable preservation; not merged |
| `three-sleeve-restatement-20260811` | 0.35 | active swarm audit surface |
| `claude-opus5-architecture-audit-20260725` | 1.56 | this session's own working tree |

---

## 5. Scratch and caches

| item | reclaimed | note |
|---|---:|---|
| `/private/tmp` git worktrees (7) | ~4.0 GB | 5 merged+clean removed via `git worktree remove`; 2 pinned-by-ref removed with `--force` |
| `/private/tmp` scratch dirs (13) | ~3.4 GB | `p2-scoped`, `p2-ab-worktree` (already prunable), `lane_i`, `mag_program`, `ac_refute{,2,3,4}`, `wave21-minimal-repair-*`, `wave21-postinteg-*` |
| `__pycache__` / `.pytest_cache` under `GTOSActive` | 0.81 GB | 749 directories |
| `~/.cache/codex-runtimes` | 4.15 GB | re-downloadable runtimes |
| `~/.Trash` | 0.13 GB | emptied |
| `git worktree prune` | — | cleared 2 stale registrations |

`/private/tmp` went 10.24 GB → 3.29 GB. The Aug-11/12 caches
(`w21-rulev2-20260811`, `w21-postmortem-cache-20260811`, `w21-puzzle-cache`,
`junjul-lane-mat-20260810`, `native-hotfix-review.*`) were **left in place** — they are
recent and plausibly in use by the running full-puzzle analysis.

---

## 6. LFS — measured, and it is not the lever it looked like

`repo/.git/lfs` was **41.74 GB**, the single largest item on the machine after the working
trees. It is now 41.27 GB. Only **508 MB was prunable**, and that is the honest ceiling.

**`git lfs prune` was initially blocked**, and the reason matters for anyone who tries again:
the repo is a **partial clone** (`remote.origin.promisor=true`,
`partialclonefilter=blob:none`), so LFS's history scan hit `missing object: <oid>` and
aborted. Each invocation lazily fetched exactly one missing object and then died, which reads
like an infinite wall. It is not — `git rev-list --objects --all --missing=print` showed
only **12** missing objects. Touching each with `git cat-file -t` materialized all 12 in
under a minute and the scan then completed cleanly.

The prune was then run in **`--verify-remote`** mode, which deletes a local object only after
confirming the remote still has it. Result:

```
1246 local objects, 4206 retained, 78 verified with remote, done.
Deleting objects: 100% (93/93), done.     # 508 MB
```

**4,206 objects are retained because they are genuinely referenced.** The LFS store is not
stale; it is working set. There is no further LFS reclamation available without deleting
referenced evidence.

`--verify-remote` was not optional caution. The repo carries `lfs.allowincompletepush=true`,
so "it is on GitHub" could not be assumed — and the obvious local fallback does **not**
exist: `~/gtos-vps-archive-20260803/lfs-objects-zst` holds 2,965 objects but **only 1 of the
1,246 local objects overlaps it**. It is the VPS's object set, not a backup of this one.

**H1 regression check.** The R2 decision contract's input-binding drift was measured
immediately before and immediately after the prune, from this worktree:

| | drifted | unhydrated-LFS |
|---|---:|---:|
| before prune | 7 | 0 |
| after prune | 7 | 0 |

Unchanged, and critically **no bound path became an un-hydrated pointer**. (The 7 are
pre-existing and worktree-local — this tree is on `wave21/forward-shadow-live-commission`,
whose `src/` legitimately differs from the sealed contract. Per CLAUDE.md the count is a
property of a working tree's hydration state and is not portable.)

---

## 7. Not deleted, with reasons — and the price of the next 20 GB

### Inside GTOS — at its floor

| item | GB | why it stays |
|---|---:|---|
| `repo/` working tree | ~9 | **hard prohibition.** `ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl` exists only as an uncommitted working copy there and satisfies R2 by the runner's `binding_roots` fallback. Never cleaned, stashed, or checked out. |
| `repo/.git/lfs` | 41.27 | measured above: 4,206 objects referenced, nothing further prunable |
| `lane-inputs-true-utc-hold-20260805` | 33.96 | **investigated as instructed.** 16.7 GB `sources/` + 17.2 GB `packs/` across 15 monthly windows. Referenced by live code — `src/research_infra/lane_rematerialization.py`, `p1_upstream_reconstruction.py`, `wave21_full_flow_harness.py`, `session_fc_exit_overlay.py`, `p1_offline_complete_path_runner.py` — and its `LANE_INPUT_REGISTRY.json` hashes are the pins the JunJul prereg V1_3 re-pinned to. It also holds the four never-funnel-read 2025 windows the program calls its validation currency. **Load-bearing; do not touch.** |
| `hermes-evidence-hold-20260727` | 4.58 | protected by instruction; also holds the March branch bundles |
| `vps-export-20260725` | 4.61 | read-only VPS snapshot; the evidence behind the H6 `mt5_preflight` finding |
| `vps-ticks-20260726` | 2.18 | protected; 263.9 M sha-verified ticks, not reproducible without a VPS pull |

GTOS is now **103.26 GB** and roughly at its floor. Squeezing it further means deleting
referenced evidence.

### The next 20 GB — cheapest-first, all outside GTOS

The 150 GB target needs **+63.4 GB**, and every remaining candidate is another system's data.
I stopped here rather than guess. Ranked by what is actually lost:

**Tier 1 — zero irreversible loss, re-downloadable (~20.2 GB, the recommended next 20):**

| item | GB | cost of deleting |
|---|---:|---|
| `~/Library/Application Support/Claude/vm_bundles` | 11.73 | Claude Desktop re-downloads them |
| `~/.ollama/models` | 5.88 | `ollama pull` re-fetches |
| `~/.codex/packages` | 2.63 | re-downloadable |

**Tier 2 — stale backups of a *different* system (~34 GB, needs a yes):**

| item | GB | what it is |
|---|---:|---|
| `~/.hermes-action-node/backups/full-jarvis-predeploy-20260722-013336` | 20.63 | a 2026-07-22 pre-deploy snapshot of HermesActionNode |
| `~/.hermes-action-node/backups/pre-update-2026-07-{12,26,29}*.zip` | 13.34 | three pre-update archives, all ≥ 2 weeks old |

**Tier 3 — history you may want (~41 GB, I would ask first):**

| item | GB | what is lost |
|---|---:|---|
| `~/.codex/sessions` + `logs_2.sqlite` | 29.95 | Codex CLI transcript history for 2026 |
| `~/gtos-vps-archive-20260803` | 11.10 | GTOS VPS snapshot: 7.42 GB LFS objects (2,965, essentially disjoint from local), an 0.86 GB packet-repo bundle, shadow logs |

Tier 1 + Tier 2 reaches **~141 GB free**; adding Tier 3 clears 150 GB comfortably.
`~/Downloads` (9.17 GB) is personal (an Instagram export, installers) and was left alone.

---

## 8. What was committed

Only this report and the two gzipped manifests. No runtime dirt was staged.

- `STORAGE_RECLAMATION_V1.md` (this file)
- `STORAGE_RECLAMATION_ARCHIVE_MANIFEST.jsonl.gz` (6,311 rows)
- `STORAGE_RECLAMATION_WORKTREE_UNCOMMITTED_MANIFEST.jsonl.gz` (638 rows)
