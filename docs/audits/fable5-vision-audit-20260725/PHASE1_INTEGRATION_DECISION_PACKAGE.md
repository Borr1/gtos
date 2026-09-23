# Phase 1 Integration — Operator Decision Package

**Prepared** 2026-07-26 · **For** Borhen (owner executes all irreversible steps) · **Basis** three D1
contract-binding lenses, three adversarial refutations, the B29 sleeve patch plan and its adversarial
review, the tick-landing measurement — plus independent re-measurement performed while writing this
package. Every number below carries `[MEASURED]` or a `file:line`. Nothing is inherited on trust.

**Three things changed while writing this. Read them before anything else.**

1. **The D1 deletion is the wrong verb.** `[MEASURED]` **60.1 GiB of the 69.2 GiB target directory is
   not in git at all** (504 untracked + 10 ignored files). Deleting it is permanent destruction of
   one-of-a-kind evidence, not removal of a redundant copy. But the repo's own cold-demotion tool
   compresses this exact material at a **measured 35.6:1** across the 14 archives it already produced.
   **Cold-demote instead of delete and you reclaim 66.6 of 69.2 GiB — 96.2 % — with zero irreversible
   loss.** That is strictly better than the plan on the table and it is the same tool the task named.
2. **B29's "one clock" is two clocks, and the seam is inside the sealed March challenge.**
   `broker_clock.py:31` on `phase1/clock-truth` states the US/EU disagreement window is
   **2026-03-08..2026-03-28**, and says in terms that it "lies inside the sealed March challenge month."
   This is not a 28-day cosmetic gap; it is the month the campaign will be judged on.
3. **The disputed test baseline resolves in the plan's favour.** `[MEASURED]` at HEAD:
   `tests/ultimate_book` = **60 failed, 403 passed** (5.90 s). The adversarial review's D-16 challenged
   the "60 bad" figure, but it had only run `test_new_sleeves.py` (20/20 green — also confirmed). Both
   were right about different scopes. The unverified number is the **684** full-suite figure; do not
   quote it until someone runs the suite.

---

# A. D1 deletion decision

## A.0 The measurement that reframes the decision

Target: `/Users/borr/GTOSActive/repo/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/`

| quantity | `[MEASURED]` |
|---|---|
| directory total (`du -sk`) | **69.204 GiB** (74.3 GB) |
| top-level regular files | **883** files, 68.332 GiB |
| existing `*.jsonl.cold` archives | 14 dirs, 0.876 GiB |
| `__pycache__` + `research/` subdirs | 0.010 GiB |
| **not in git (untracked `??` + ignored)** | **514 files, 60.145 GiB** ← permanent loss if deleted |
| tracked (git/LFS-backed) | 369 files, 8.188 GiB ← restorable |
| cold-archive compression, 14 existing archives | 33,513,887,701 B → 941,430,259 B = **35.6 : 1** |
| free disk | 29 GiB of 460 GiB (94 % full) |

Two corrections to the framing the lenses inherited:

- **`git status` is not the deletion set.** 10 files (the January CAP_R2 golden group) are neither
  tracked nor reported by `git status -uall` — they are excluded at `.git/info/exclude:27`. A
  status-driven script would silently skip them, or a `git clean` would silently destroy them.
- **The cold tool refuses to re-archive.** `archive_b7_5_cold_evidence.py:979-981`
  (`raise DemotionRefusal(f"demotion_destination_exists:{candidate}")`) means the 7 CAP_R2 raw ledgers
  that already have `.cold` siblings **cannot** be cold-demoted. They must be plain-deleted — which is
  correct and safe, because the sibling archive already holds them byte-exactly (see A.4).

## A.1 FINAL HOLD list — 16 files, 154.1 MiB, never delete

Consolidated and de-duplicated from all three lenses plus both refuters. All 16 verified present
`[MEASURED]`. Total cost to keep: **0.22 % of the directory.**

| # | file (basename, in the target dir) | bytes | why it must survive |
|---|---|---|---|
| 1 | `BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_04_ENTRY_FILL_TERMINAL_LIFECYCLE_REPAIR_R5_RELATIONAL_COMPACT_FULLGRID_SOURCE_UNIVERSE_LEDGER.jsonl` | 1,417,943 | **Highest risk in the set.** Source-universe ledger of the *active, incomplete* April window. Bound by absolute path + `sha256 84d92d64…` in `…/.hermes/evidence/phase-d/april-post-acceleration-source-20260725T021800Z/CURRENT_SOURCE_SELECTION_RECEIPT.json` (`.source_ledger.path`, `.selection_command[6]`); reproduces `source_plan_digest 4987d98c…` that R2 seals as `window_source_plan_bindings[adverse_development_april]`. `b7_5_post_acceleration_runner.py:787-795` stats, size-checks and SHA-checks it as `sealed_tick_source_ledger` on **every arm launch**. Required arg at `replay_acceleration_slice.py:1881`. In **no commit, no LFS object, no `.cold` sibling** — irrecoverable. Loses April S1R1/S0R0/S1R0/S0R1. |
| 2 | `BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_01_SELECTION_SIZING_S0R0_SOURCE_REPAIRED_R3_CAP_R2_SOURCE_UNIVERSE_LEDGER.jsonl` | 3,079,300 | January source-universe ledger; `sha256 9bc4f3b1…` bound in four sealed source-selection receipts and as `role:"source"` in `PARTIAL_GOLDEN_MANIFEST.json`. Reproduces `85663876faba…`, hard-asserted at `replay_acceleration_attempt5_typed_sparse_runner.py:1020`. Ignored by git (`.git/info/exclude:27`). *Has* a `.cold` sibling, but must stay **raw** because the runner stats the raw path. |
| 3 | `RECONSTRUCTED_PROXY_PACKAGE_SELECTION_SUMMARY.json` | 5,662 | Fail-closed required runtime-evidence input: `attempt5:374-375`, `:385-393`, `:399-400` → `runtime_evidence_input_missing:reconstructed_selection`. Resolved only against the hardcoded `/Users/borr/GTOSActive/repo` (`attempt5:186`, `:361`; `b7_5_post_acceleration_runner.py:1021`). Working-tree bytes `b96907a2…` exist in **no commit** (HEAD holds `04a1d359…`), so `git checkout` restores a *different* payload. |
| 4 | `ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl` | 205,754 | `package_authority_input` of **both** R1 (`:641`) and R2 (`:652`), `sha256 19365f60…`, `source_root:"runtime_evidence"`; feeds all four arm fingerprints (`attempt5:1073-1078`). Also fail-closed `runtime_evidence_input_missing:sleeve_registry`. **The matching payload exists in exactly one place on this machine** — this file. Mainline worktree = `a5bcc0f8…`; engine worktree = 131-byte pointer. HEAD's LFS pointer names `a5bcc0f8`, so the `19365f60` object in `.git/lfs/objects` is **orphaned**: a `git lfs prune` erases the last backup. |
| 5 | `SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl` | 5,995,223 | Second `package_authority_input` in R1 (`:649`) / R2 (`:660`), `sha256 64fd1014…`, `source_root:"runtime_evidence"`; fail-closed `runtime_evidence_input_missing:member_axis` (`attempt5:371`). Recoverable (HEAD's LFS pointer names the matching oid, object present) **only while entry 11 survives**. |
| 6 | `run_broad_live_as_if_replay_harness.py` | 598,237 | Unique copy on this machine. `sha256 c8efd882…` bound in `B7_5_SELECTION_SIZING_DECISION_CONTRACT.json:304` (itself a bound `common_behavior_input` of R1/R2), as `resolver_file_sha256` in `AMENDMENT_R3.json:118-119`, and as `legacy_code_authority.code_files[0]`. Both other worktrees hold a 534-byte tombstone. **Without it the legacy broad ledgers can never be regenerated** — which is why the safe list below is a demotion, not a deletion. |
| 7 | `build_source_bound_execution_parity.py` | 418,819 | Bound `common_behavior_input` R1 `:584` / R2 `:587` (`34ff69ab…`) **and** `code_authority_paths` entry (`attempt5:1429`). The `/repo` copy carries the *legacy* payload `0691592f…` sealed into `PARTIAL_GOLDEN_MANIFEST.legacy_code_authority.code_files[10]` — a payload no other worktree holds `[MEASURED]`. |
| 8 | `run_selected_package_replay_bridge.py` | 468,438 | Bound `common_behavior_input` R1 `:408` / R2 `:555` (`2ed740e9…`); `code_authority_paths` (`attempt5:1409`); imported at import time via `sys.path` insertion (`attempt5:50-56`); its globals are what `configure_runtime_evidence_root` rebinds. |
| 9 | `verify_denominator_to_deployment_execution.py` | 1,734,190 | Bound `common_behavior_input` R1 `:592` / R2 `:363` (`4d933084…`) and `code_authority_paths` (`attempt5:1430`). Never executes; its **bytes** are hashed into every arm fingerprint. One of R2's seven `verification_tooling_deferred`. |
| 10 | `build_b7_5_extended_history_source_window_contract.py` | 31,764 | `source_plan_builder_file_sha256 b82c0f8c…` in `AMENDMENT_R3.json:122-123` and `B7_5_SELECTION_SIZING_DECISION_CONTRACT.json:658-659`. The replay-free reproduction path for the sealed January source plan the March challenge is compared against. |
| 11 | `.gitattributes` | 91 | **The sole reason `git checkout` restores payloads instead of pointer text.** Only rule on this machine making `*.jsonl` LFS-managed in this route (`*.jsonl filter=lfs diff=lfs merge=lfs -text`); root `.gitattributes` has no matching anchor; `.git/info/attributes` absent. Negative control executed by the refuter: without it `git check-attr -a` returns nothing; with it, `filter: lfs`. Delete it and entries 4/5 silently become 131/132-byte pointers on any restore → `selection_sizing_decision_contract_input_drift` with no clue as to cause. |
| 12 | `OUTPUT_MANIFEST.json` | 27,496 | The route's own pinning authority (231 pinned entries). `scripts/audit_goal_route_artifacts.py:202-205` fails **open** when it is absent, after which every survivor is classified "not pinned by OUTPUT_MANIFEST.json" (`:452`, `:511`). Deleting the index of what was authoritative, in the same operation that removes most of what it indexes, destroys the ability to state afterwards what the route's authoritative outputs were. |
| 13 | `BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_01_EXTENDED_HISTORY_REPAIRED_ONLY_RELATIONAL_COMPACT_FULLGRID_BUCKET_LEDGER.jsonl` | 17,863,464 | ↓ |
| 14 | `…_EXTENDED_HISTORY_REPAIRED_ONLY_RELATIONAL_COMPACT_FULLGRID_ORDER_LEDGER.jsonl` | 76,356,236 | ↓ |
| 15 | `…_EXTENDED_HISTORY_REPAIRED_ONLY_RELATIONAL_COMPACT_FULLGRID_ORDERED_PATH_ORACLE_LEDGER.jsonl` | 21,658,236 | ↓ |
| 16 | `…_EXTENDED_HISTORY_REPAIRED_ONLY_RELATIONAL_COMPACT_FULLGRID_TRADE_LEDGER.jsonl` | 31,691,600 | **13–16: the four raw survivors of the "RETAINED JANUARY" operation.** `B7_5_RETAINED_JANUARY_EXTENDED_HISTORY_APFS_COMPRESSION_MANIFEST.json` `[MEASURED]`: `allowed_root=/Users/borr/GTOSActive/repo`, `mutation_applied=true`, `status="FAILED_SAFE_COMPRESSION_INCOMPLETE"`, `totals.physical_bytes_post=null`, `physical_bytes_reclaimed=null`, 7 entries. The other 3 (DECISION/MISSED/SCORECARD) were cold-demoted; these 4 were not and have **no `.cold` sibling** `[MEASURED]`. Untracked, not ignored, no LFS object. Four of the manifest's seven `sha256` bindings can only ever be checked against these files: delete them and an incomplete mutating operation can never be completed, rolled back, or audited. Cost to keep: **147.6 MB.** |

**Total hold: 161,552,453 B = 154.1 MiB.**

## A.2 MUST-STAY-ABSENT — 2 paths (an inverted hold)

| path | state | why |
|---|---|---|
| `REPLAY_EXTENSION_OPTIMIZED_SOURCE_MATERIALIZER_LEDGER.jsonl` | `[MEASURED]` absent from disk; `git ls-files -v` → **`S`** (skip-worktree); present in HEAD | Optional runtime-evidence inputs (`attempt5:376-379`, absent from `required_inputs` `:385-393`). Their **absence** is baked into the `runtime_input_contract_root_sha256` of all four sealed January arms. Deleting them is a no-op. **Restoring them breaks the campaign**: any `git checkout -- <dir>`, `git restore`, `git clean` + checkout, `git lfs pull`, or clearing the skip-worktree bit materialises them, flips `present` to true, rebinds `selected_package_bridge.MATERIALIZER_LEDGER` / `PENDING_CREATED_SOURCE_COVERAGE_LEDGER` (`attempt5:432-436`) and changes the contract root hash against the sealed arms. |
| `REPLAY_EXTENSION_PENDING_CREATED_SOURCE_COVERAGE_LEDGER.jsonl` | same | same |

**Operational rule: never run a git working-tree-restoring command inside this directory.** The
deletion must be filesystem-level only.

Also hold, implicitly: the **14 existing `*.jsonl.cold` archives** (0.876 GiB). They *are* the backup
for six already-removed raw ledgers and for the seven CAP_R2 files step 2 deletes.

## A.3 FINAL SAFE list — by disposition, with measured reclaim

Rule: **everything in the directory that is not in A.1, A.2 or a `.cold` archive.** 867 files.

| # | disposition | selector | files | GiB | GB | reclaim | reversible? |
|---|---|---|---|---|---|---|---|
| S1 | **COLD-DEMOTE** | untracked, non-zero `*.jsonl`, no `.cold` sibling | **284** | **56.953** | 61.15 | **55.353 GiB** (→ ~1.600 GiB of zstd shards at the measured 35.6:1) | **YES — byte-exact, verified on write** |
| S2 | **PLAIN DELETE** | git/LFS-tracked files | **359** | **8.179** | 8.78 | 8.179 GiB | YES — `git checkout` (requires hold #11) |
| S3 | **PLAIN DELETE** | the 7 CAP_R2 raw ledgers that already have a verified `.cold` sibling | **7** | **3.010** | 3.23 | 3.010 GiB | YES — from the sibling `.cold` |
| S4 | **PLAIN DELETE** | untracked non-`.jsonl` (`.json` summaries, `.md` dossiers, `.py` scratch) | **173** | 0.040 | 0.04 | 0.040 GiB | NO — but 40 MB, all derived summaries |
| S5 | **PLAIN DELETE** | zero-byte `.jsonl` | **44** | 0.000 | 0.00 | 0 | n/a |
| S6 | **PLAIN DELETE** | `__pycache__/` | — | 0.010 | 0.01 | 0.010 GiB | regenerable |
| | **TOTAL** | | **867** | **68.182** | 73.21 | **≈ 66.58 GiB (96.2 % of 69.204)** | |

Residual on disk after the operation: **≈ 2.63 GiB** = 0.876 (existing cold) + ~1.600 (new shards) +
0.150 (hold list).

The bulk of S1, for orientation `[MEASURED]`, top prefixes:

| glob (all under the target dir) | files | GiB |
|---|---|---|
| `BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_04_ENTRY_FILL_TERMINAL_LIFECYCLE_REPAIR_R5_*` (minus hold #1) | 13 | 13.36 |
| `BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_04_TERMINAL_BLOCKER_STAGE_REPAIR_R4_*` | 14 | 13.31 |
| `SOURCE_BOUND_TO_EXECUTED_PARITY_*` (untracked subset) | 20 | 9.45 |
| `BROAD_LIVE_AS_IF_REPLAY_2026_01_{22_23,29_30}_*` (targeted 2-day probes) | 55 | 6.66 |
| `CANDIDATE_INSTANCE_PARITY_PROJECTION_*` (untracked subset) | 12 | 3.14 |
| `BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_01_TERMINAL_BLOCKER_STAGE_REPAIR_R4_*` (non-cold remainder) | 9 | 0.15 |
| remainder (369-file `BROAD_LIVE_AS_IF_REPLAY_*` long tail, untracked subset) | ~161 | ~10.9 |

S2's largest members are the June B7.3-era `BROAD_LIVE_AS_IF_REPLAY_V250_B7_3_NON_HOSTILE_5D_*` set
(4 files, 6.54 GiB) and `ULTIMATE_CANDIDATE_PACKAGE_REPLAY_AUTHORITY_CANDIDATE_LEDGER.jsonl` (0.675 GiB).

## A.4 Did a refuter find a counter-example? Yes — three, and all three change the plan

| finding | verdict | what it changes |
|---|---|---|
| **`.gitattributes` is not on any list, so the stated rule clears it** | **UPHELD** | Added as hold #11. It is the *only* thing making the "recoverable from git" story true for holds #4/#5 and for the whole 8.18 GiB S2 line. Deleting it converts every future `git checkout` in this route into a silent pointer-text write. This alone invalidates the original safe list. |
| **The two `REPLAY_EXTENSION_*` files are load-bearing by their absence** | **UPHELD** | Added as A.2. Cannot be destroyed by this deletion — but it forbids the entire class of git-based cleanup, which is exactly how a tired operator would tidy up afterwards. |
| **The four raw "RETAINED JANUARY" ledgers were the deleted half of one retention decision** | **UPHELD, and independently re-measured here** | Added as holds #13–16. The manifest is `status=FAILED_SAFE_COMPRESSION_INCOMPLETE`, `mutation_applied=true`, `physical_bytes_post=null` `[MEASURED]`. Protecting the three `.cold` halves while deleting these four is not defensible. 147.6 MB. |

Three further claims I checked and **do not** carry:

- *"Everything not on the hold list is safe"* — the framing, not a file. Replaced by A.3's disposition
  rule, which is exhaustive over all 883 files.
- *The CAP_R2 golden set must be held whole (47-entry prefix hold).* **Refuted by measurement.**
  All 8 `persisted_result_surfaces` of `PARTIAL_GOLDEN_MANIFEST.json` have byte-verified `.cold`
  archives. I hashed one directly: `…CAP_R2_MISSED_OPPORTUNITY_LEDGER.jsonl` on disk =
  `5012abd3f532d3bd6ca47de97f0da35a4e90743da2163a6a763747f7f4cbf679` `[MEASURED]`, identical to
  `manifest.json → logical_source.sha256`, `status=PASS_COLD_ARCHIVE_LOGICAL_BYTES_VERIFIED`. Seven
  are therefore free to plain-delete (S3); only the SOURCE_UNIVERSE ledger stays raw (hold #2),
  because the runner stats the raw path.
- *The output namespace / execution seals / prepared packs are at risk.* No. `ATTEMPT5_NAMESPACE_ROOT`
  resolves against the **executing** worktree (`attempt5:37`, `:185`); `attempt_5_typed_sparse` does
  not exist under `/repo` `[MEASURED]`, and every seal names the engine-worktree absolute path.

## A.5 Exact commands

**Preconditions** — run these first, in order:

```bash
# P1. Never do this inside the route: git checkout / git restore / git clean / git lfs pull / git lfs prune.
#     git lfs prune would erase the orphaned 19365f60 object that is hold #4's only backup.

# P2. Freeze the hold list to an out-of-tree, hash-verified copy BEFORE touching anything.
mkdir -p ~/gtos-d1-hold-20260726
cd /Users/borr/GTOSActive/repo/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20
cp -p .gitattributes OUTPUT_MANIFEST.json RECONSTRUCTED_PROXY_PACKAGE_SELECTION_SUMMARY.json \
      ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl \
      run_broad_live_as_if_replay_harness.py build_source_bound_execution_parity.py \
      run_selected_package_replay_bridge.py verify_denominator_to_deployment_execution.py \
      build_b7_5_extended_history_source_window_contract.py \
      BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_04_ENTRY_FILL_TERMINAL_LIFECYCLE_REPAIR_R5_RELATIONAL_COMPACT_FULLGRID_SOURCE_UNIVERSE_LEDGER.jsonl \
      BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_01_SELECTION_SIZING_S0R0_SOURCE_REPAIRED_R3_CAP_R2_SOURCE_UNIVERSE_LEDGER.jsonl \
      BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_01_EXTENDED_HISTORY_REPAIRED_ONLY_RELATIONAL_COMPACT_FULLGRID_BUCKET_LEDGER.jsonl \
      BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_01_EXTENDED_HISTORY_REPAIRED_ONLY_RELATIONAL_COMPACT_FULLGRID_ORDER_LEDGER.jsonl \
      BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_01_EXTENDED_HISTORY_REPAIRED_ONLY_RELATIONAL_COMPACT_FULLGRID_ORDERED_PATH_ORACLE_LEDGER.jsonl \
      BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_01_EXTENDED_HISTORY_REPAIRED_ONLY_RELATIONAL_COMPACT_FULLGRID_TRADE_LEDGER.jsonl \
      ~/gtos-d1-hold-20260726/
shasum -a 256 ~/gtos-d1-hold-20260726/* > ~/gtos-d1-hold-20260726/SHA256SUMS.txt   # 16 lines expected
```

**Step 0 — generate the disposition lists (deterministic, re-runnable, writes nothing into `/repo`):**

```bash
/opt/homebrew/bin/python3 - <<'EOF' > /tmp/d1_plan.json
import json, subprocess, pathlib
R="research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
root=pathlib.Path("/Users/borr/GTOSActive/repo"); D=root/R
HOLD={ "BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_04_ENTRY_FILL_TERMINAL_LIFECYCLE_REPAIR_R5_RELATIONAL_COMPACT_FULLGRID_SOURCE_UNIVERSE_LEDGER.jsonl",
 "BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_01_SELECTION_SIZING_S0R0_SOURCE_REPAIRED_R3_CAP_R2_SOURCE_UNIVERSE_LEDGER.jsonl",
 "RECONSTRUCTED_PROXY_PACKAGE_SELECTION_SUMMARY.json","ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl",
 "SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl","run_broad_live_as_if_replay_harness.py",
 "build_source_bound_execution_parity.py","run_selected_package_replay_bridge.py",
 "verify_denominator_to_deployment_execution.py","build_b7_5_extended_history_source_window_contract.py",
 ".gitattributes","OUTPUT_MANIFEST.json",
 "BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_01_EXTENDED_HISTORY_REPAIRED_ONLY_RELATIONAL_COMPACT_FULLGRID_BUCKET_LEDGER.jsonl",
 "BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_01_EXTENDED_HISTORY_REPAIRED_ONLY_RELATIONAL_COMPACT_FULLGRID_ORDER_LEDGER.jsonl",
 "BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_01_EXTENDED_HISTORY_REPAIRED_ONLY_RELATIONAL_COMPACT_FULLGRID_ORDERED_PATH_ORACLE_LEDGER.jsonl",
 "BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_01_EXTENDED_HISTORY_REPAIRED_ONLY_RELATIONAL_COMPACT_FULLGRID_TRADE_LEDGER.jsonl"}
tracked=set(subprocess.run(["git","--no-optional-locks","ls-files","--",R],cwd=root,
            capture_output=True,text=True).stdout.splitlines())
cold={p.name[:-5] for p in D.iterdir() if p.is_dir() and p.name.endswith(".jsonl.cold")}
plan={"demote":[],"delete":[],"hold":[]}
for p in sorted(D.iterdir()):
    if not p.is_file(): continue
    n,s=p.name,p.stat().st_size
    if n in HOLD: plan["hold"].append(str(p))
    elif n in cold or f"{R}/{n}" in tracked or s==0 or not n.endswith(".jsonl"):
        plan["delete"].append(str(p))
    else: plan["demote"].append(str(p))
assert len(plan["hold"])==16, len(plan["hold"])
json.dump(plan,__import__("sys").stdout,indent=1)
EOF
/opt/homebrew/bin/python3 -c "import json;p=json.load(open('/tmp/d1_plan.json'));print({k:len(v) for k,v in p.items()})"
# expected: {'demote': 284, 'delete': 583, 'hold': 16}
```

**Step 1 — COLD-DEMOTE dry run (default; no mutation).** Batch in tens; the tool is all-or-nothing per
invocation, so smaller batches give finer rollback granularity and visible progress.

```bash
cd /Users/borr/GTOSActive/repo/research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16

/opt/homebrew/bin/python3 - <<'EOF' > /tmp/d1_batches.sh
import json
paths=json.load(open('/tmp/d1_plan.json'))['demote']
for i in range(0,len(paths),10):
    args=" ".join(f'--path "{p}"' for p in paths[i:i+10])
    print(f'BATCH{i//10:03d}="{args}"')
EOF
source /tmp/d1_batches.sh

# DRY RUN — one batch. Repeat for every BATCHnnn before applying anything.
PYTHONPATH=. /opt/homebrew/bin/python3 archive_b7_5_cold_evidence.py \
  --repo-root  /Users/borr/GTOSActive/repo \
  --allowed-root /Users/borr/GTOSActive/repo/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20 \
  --zstd /opt/homebrew/Cellar/zstd/1.5.7_1/bin/zstd \
  --compression-level 6 \
  $(eval echo \$BATCH000)
```

Exit 0 with `status` PASS and `mutation_applied: false` = safe. Exit 2 prints `REFUSED: <reason>`;
`demotion_destination_exists` means the file already has a `.cold` sibling and belongs in step 2.

**Step 2 — plain deletes FIRST** (frees 11.2 GiB, giving the demotion headroom on a 94 %-full disk):

```bash
/opt/homebrew/bin/python3 -c "
import json;print('\n'.join(json.load(open('/tmp/d1_plan.json'))['delete']))" > /tmp/d1_delete.txt
wc -l /tmp/d1_delete.txt            # expect 583
# eyeball it, then:
xargs -d '\n' -a /tmp/d1_delete.txt rm -f
rm -rf /Users/borr/GTOSActive/repo/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/__pycache__
```

**Why plain deletion, not cold demotion, for these 583:** 359 are git/LFS-backed (the object store is
already the archive — demoting them would double-store); 7 already have a byte-verified `.cold` sibling
and the tool **refuses** them (`archive_b7_5_cold_evidence.py:979-981`); 44 are zero-byte; 173 are
`.json`/`.md`/`.py` derived summaries the JSONL tool cannot process at all (it requires full JSON-object
line validation). Do **not** follow the deletion with any git command — see A.2.

**Step 3 — COLD-DEMOTE apply.** `--apply` requires a **new, non-existent** `--operation-manifest`
(`archive_b7_5_cold_evidence.py:949-956`). Use one manifest per batch:

```bash
cd /Users/borr/GTOSActive/repo/research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
for n in $(seq -f "%03g" 0 28); do
  PYTHONPATH=. /opt/homebrew/bin/python3 archive_b7_5_cold_evidence.py \
    --repo-root  /Users/borr/GTOSActive/repo \
    --allowed-root /Users/borr/GTOSActive/repo/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20 \
    --zstd /opt/homebrew/Cellar/zstd/1.5.7_1/bin/zstd \
    --compression-level 6 \
    --operation-manifest /Users/borr/GTOSActive/repo/research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/D1_ROUTE_COLD_DEMOTION_${STAMP}_B${n}.json \
    $(eval echo \$BATCH${n}) --apply || { echo "STOPPED AT BATCH $n"; break; }
done
```

Expected per-batch: `status: PASS_COLD_DEMOTION_LOGICAL_BYTES_PRESERVED`, `failure: null`,
`retained_backups: []`. Precedent throughput `[MEASURED]` from
`.hermes/receipts/phase-d/JANUARY_S0R0_R2_COLD_DEMOTION.json`: 15.6 GB in 116 s
(`generated_at 10:30:14Z` → `completed_at 10:32:10Z`), so ~57 GiB ≈ **7–10 minutes** plus verification.

**Step 4 — verify:**

```bash
D=/Users/borr/GTOSActive/repo/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20
du -sh "$D"                                            # expect ~2.6 GiB
ls -1 "$D"/*.jsonl.cold | wc -l                        # expect 14 + 284 = 298
cd /Users/borr/GTOSActive/repo && shasum -a 256 -c ~/gtos-d1-hold-20260726/SHA256SUMS.txt 2>/dev/null | grep -c OK  # expect 16 after path fixup
# H1 contract re-check — must print nothing but the verification_tooling line:
/opt/homebrew/bin/python3 - <<'EOF'
import json,hashlib,pathlib
R2='/Users/borr/GTOSActive/repo/research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/B7_5_POST_ACCELERATION_DECISION_CONTRACT_R2_VERIFICATION_SPLIT.json'
d=json.load(open(R2))
for g in ('common_behavior_inputs','package_authority_inputs'):
    for r in d['input_bindings'][g]:
        p=pathlib.Path(r['path'])
        if not p.is_absolute(): p=pathlib.Path('/Users/borr/GTOSActive/repo')/p
        if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()!=r['sha256']: print('DRIFTED:',r['path'])
EOF
```

## A.6 Verdict — **GO WITH CARVE-OUTS**

Go, on these five conditions:

1. **Hold the 16 files in A.1** and freeze them out-of-tree first (P2). 154 MiB.
2. **Never restore the two A.2 paths.** No `git checkout` / `restore` / `clean` / `lfs pull` inside the
   route, ever. Filesystem deletion only.
3. **Never `git lfs prune`** while hold #4's `19365f60…` object is the only copy of a contract-bound
   payload. Fixing that orphan is separate work (see D-3).
4. **Cold-demote S1 rather than delete it.** 55.4 GiB reclaimed, zero loss. Deleting it instead
   destroys 57 GiB of one-of-a-kind evidence to save ~1.6 GiB more — a bad trade on any reading of
   the charter, and irreversible on a machine where regeneration costs 16.5 h per window (H5) and only
   works from this worktree (H4).
5. **Plain-delete S2–S6 before demoting**, for disk headroom.

I would not sign a plain `rm -rf` of the directory, and I would not sign the original safe list: it
clears `.gitattributes`, which silently breaks the recovery path it depends on. With the five
conditions, the operation is safe, 96.2 % effective, and fully reversible except for 40 MB of derived
summaries.

---

# B. B29 sleeve correction

## B.1 Final per-sleeve patch table

**Mechanism (one shared helper, not eight edits):** new file
`src/components/ultimate_book/sleeves/_session_clock.py` exposing `server_hour` / `server_hm` /
`server_day`, all routed through `broker_clock.utc_to_broker_naive(instant, NEW_YORK_PLUS_7)`
(`broker_clock.py:318`, rule at `:204`). Each sleeve's edit replaces the **body** of its own private
`_hour`/`_day`/`_hm`/`_daystr` — every constant and every call site stays byte-identical.

Corrections applied to the plan as written:
- **Import style:** use absolute `from src.utils.broker_clock import …`, the house convention in
  `src/components/` (`same_symbol_lifecycle_v4.py:20-21`, `broker_net_cost_engine.py:14`). The plan's
  `....` four-dot form is unprecedented in this tree and its cited precedent (`fx_jpy.py:77`) is
  `_STOP_M = 1.0`, not an import.
- **Fail closed on naive input.** `to_server_local` must **reject** a naive datetime, not
  `replace(tzinfo=utc)` it. `book_engine._resolve_repair_offset_seconds` (`:200-286`, docstring
  `:224-233`) documents a "leaked zero-offset state" in which stamps arrive broker-local mislabelled as
  UTC; silently assuming UTC there produces a double correction with no error.
- **Accept `datetime.date`.** `vss._daystr:71-77` branches on `hasattr(t,"year")`, which is true for
  `date`; an `isinstance(t, datetime)` branch narrows the contract silently.
- **Drop the `(_hour(...) or -1)` rewrite** at `metal_session_reversion.py:86`. Provably equivalent at
  `NY_LO=14`; bundling it destroys A/B attribution. Separate commit.
- **Branch prerequisite:** `src/utils/broker_clock.py` does not exist on `main` `[MEASURED]` — only on
  `phase1/clock-truth`. The patch must land there or after that merge.

Offsets, computed not asserted: **+3 h** while New York is on EDT (2026-03-08 → 2026-11-01), **+2 h**
otherwise. Server hour H fires at UTC H−3 / H−2. All line numbers below re-verified on `main`
`[MEASURED]`.

| # | file (`src/components/ultimate_book/sleeves/…`) | line | current | new | UTC fire window before → after (summer / winter) |
|---|---|---|---|---|---|
| 1 | `ny_crypto_momentum.py` | `:38` `DECISION_HOUR = 17`, `:39` `DECISION_MIN = 0` | `_hm` body `:48-55` reads `t.hour`/`s[11:13]` | `return server_hm(t)` | **17:00 exact → 14:00 / 15:00** |
| 2 | `kz_london_crypto_low.py` | `:29` `DECISION_HOUR = 12`, `:30` `DECISION_MIN = 0` | `_hm` body `:38-44` | `return server_hm(t)` | **12:00 exact → 09:00 / 10:00** |
| 3 | `asian_fade.py` | `:42` `ASIAN_END_HOUR = 7`, `:43` `ENTRY_LO_HOUR = 8`, `:44` `ENTRY_HI_HOUR = 21` | `_hour` `:49-56`, `_day` `:59-64` | `server_hour` / `server_day` | range **00-07 → 21:00(D-1)-04:59**; entry **08-21 → 05:00-18:59** / +1 h |
| 4 | `asia_pdl_fade.py` | `:31` `ASIA_HI = 6` | `_hour` `:44-50`, `_day` `:53-58` | same | **00-06 → 21:00(D-1)-03:59** / 22:00-04:59. **PDL re-based** — see B.3 Q3 |
| 5 | `orb_crypto_london.py` | `:26` `OR_HOUR = 7`, `:28` `BRK_LO, BRK_HI = 8, 11` | `_hour` `:39-45`, `_day` `:48-53` | same | OR **07:00-07:45 → 04:00-04:45**; break **08-11 → 05:00-08:59** / +1 h |
| 6 | `metal_session_reversion.py` | `:34` `NY_LO, NY_HI = 14, 21` | `_hour` `:39-45`, `_day` `:48-53` | same | **14-21 → 11:00-18:59** / 12:00-19:59; the session **anchor bar** moves with it |
| 7 | `liq_asia_up_low_metal.py` | `:34` `ASIA_HI = 6` | `_hour` `:47-53`, `_day` `:56-61` (`_is_asia` `:64-66` inherits) | same | **00-06 → 21:00(D-1)-03:59** / +1 h. **D1 resample + PDH/PDL re-cut** — see B.3 Q3 |
| 8 | `vss_fxcross_london_up_low.py` | `:33` `LONDON_LO = 7`, `:34` `LONDON_HI = 13` | `_hour` `:57-68`, `_daystr` `:71-77`, **plus call site `:131`** | `server_hour` / `server_day`; `:131` must pass `server_day(t)` instead of the engine's UTC `decision_day` (rename the `_d1_up_regime` param `:80` `decision_day` → `session_day`) | **07-12 → 04:00-09:59** / 05:00-10:59 |

**Why #8's third part is mandatory:** MT5 D1 bars are broker-day bars stamped 00:00 broker;
`mt5_real.py:210-218` subtracts the offset, so the D1 bar for broker day *X* carries UTC `(X-1) 21:00`
and `_daystr` reads it as *X-1*. The guard `day < decision_day` (`:86`) is therefore permanently inert
today. Swapping `_daystr` without `:131` makes it compare server dates against a UTC `decision_day` and
start dropping the newest D1 close.

**Test impact — the plan's §4 table is wrong in both directions.** The refuter simulated the patch by
monkeypatching the eight helpers: baseline `test_new_sleeves.py` 20 passed → patched **5 failed,
15 passed**. Corrections that must be carried into the patch:
- The `liq` failure is in `_liq_asia_up_low_metal_series` **`:288-314`** (`:293 start`, `:303 today`,
  the 24-bar loop `:304-311`), not `:320,321,362`. `:302`'s `pdh = max(… if t[:10]=="2026-06-16")` is a
  raw UTC-date slice inside the test that stops matching the sleeve's server-day grouping.
- `orb_crypto_london` has **no fire fixture** — `:394-403` is four negative asserts. "Rebuild its
  multi-day anchors" describes a fixture that does not exist.
- Several negative tests now pass **vacuously**:
  `test_liq_asia_up_low_metal_rejects_nonlow_vol_sweep` (`:342-344`) returns `None` via the *session*
  gate, not the vol gate it exists to test. `test_asian_fade_fires_on_rejected_break` (`:40-60`) stays
  green by luck (20 of 32 bars remain Asian; the 12 that move into the entry window sit inside the
  range). Fix the fixtures, don't just re-baseline.
- **Add** one winter-date case per sleeve (offset +2) and one DST-seam case at 2026-03-08 / 2026-11-01.
  That is the assertion the EU-calendar code would fail, and the reason this must not be a fixed-offset
  patch.
- **A/B baseline `[MEASURED]` at HEAD:** `tests/ultimate_book` = **60 failed, 403 passed**;
  `tests/ultimate_book/test_new_sleeves.py` = **20 passed, 0 failed**. The 60 are market-expansion /
  rolling-stress / wave-c *artifact* tests, unrelated to sleeve logic. The full-suite "684" figure is
  **unverified — do not quote it.**

## B.2 Day-key coverage — complete inside the sleeves, incomplete outside

**Inside: complete.** Every per-day grouping site routes through the module-private helper, so the body
swap covers all of them. Enumerated:

| sleeve | day sites | helper |
|---|---|---|
| `ny_crypto_momentum` | none (`decision_day` pass-through `:77`, `:114`) | — |
| `kz_london_crypto_low` | none (`:63`, `:102`) | — |
| `asian_fade` | `:82`, `:91`, `:104` | `_day:59-64` |
| `asia_pdl_fade` | `:78`, `:88`, `:104` | `_day:53-58` |
| `orb_crypto_london` | `:90`, `:97`, `:112` | `_day:48-53` |
| `metal_session_reversion` | `:85`, `:86` | `_day:48-53` |
| `liq_asia_up_low_metal` | `:75`, `:120`, `:146`, `:177` | `_day:56-61` |
| `vss_fxcross_london_up_low` | `:85-86`, `:131` | `_daystr:71-77` + call-site change |

**Outside: four consumers read the UTC `_dday`, and the plan re-keys one.**
`intent.decision_day` is set once per cycle at `book_engine.py:504` from `bar_provider.decision_day_of`
(`bar_provider.py:86-88`) — the **UTC** date. The two Asia sleeves then gate on server hours 0..6, which
in summer is 21:00(D-1)–03:59 UTC: one server day spanning two UTC dates.

| consumer | file:line | plan option (a) re-keys it? |
|---|---|---|
| one-trade-per-(sleeve,symbol,day) cap | `book_owner.py:1601-1602` | **yes** |
| one-unit-per-(cluster,day) cap | `book_owner.py:1611-1613` → `placement_ledger.py:173`; `_cluster_cap_on` default True `:169-174`, exempt set `{"jpy"}` `:175-176` — the two Asia sleeves are **not** exempt | **no** — it suppresses the identical trades option (a) was meant to unblock |
| Kelly-lite conviction count → **size multiplier** | `admission.py:1101-1106` → consumed `:1144-1150` | **no** |
| correlated-risk-unit bucket `(decision_day, cluster)` | `admission.py:1107-1113` | **no** |

So: **the in-sleeve half is complete; the cross-cutting half is 1-of-4 and must be stated as such.**
Do not change `bar_provider.decision_day_of` globally — it is shared by all 29 live sleeves, feeds the
ledger, `execution_packets.candidate_id` (`:220`), runtime learning packets and the convergence record,
and would re-key rows already on disk.

## B.3 Owner decisions — four crisp questions

> **Q1 — Do we run one broker clock or two?**
> The book currently has two. `fx_jpy._to_server_local` (`fx_jpy.py:110-119`) calls
> `_ftmo_server_offset_hours` (`:99-107`), an **EU** DST rule via `_last_sunday_0100_utc` (`:93-97`);
> `metals.py:157-158` imports the same function for its `session_hour` feature. `NEW_YORK_PLUS_7` is a
> **US** rule. They disagree by one hour on **2026-03-08..2026-03-28**, and `broker_clock.py:31` states
> that window **lies inside the sealed March challenge month**. Options: **(A)** move `fx_jpy` and
> `metals.py` onto `NEW_YORK_PLUS_7` in the same commit — three live sleeves change behaviour on those
> 28 days; **(B)** patch only the eight and accept two clocks; **(C)** hold everything until March is
> re-measured. *My recommendation: (A). The evidence at `broker_clock.py:209-218` says the measurement
> refutes the EU calendar; shipping a fix that leaves the refuted rule running on the exact days the
> March challenge covers is not defensible.*

> **Q2 — Which of the four `_dday` consumers get re-keyed: all, or none?**
> This is the question the plan mis-framed as an owner choice between (a)/(b)/(c). "Which one" has a
> correct answer — **all four consistently, or none** — and it is an engineering call. What genuinely
> needs your signature is the consequence: **under every option, including (a), realised position size
> on `asia_pdl_fade` and `liq_asia_up_low_metal` changes**, because `n_active_by_day` bucketing
> (`admission.py:1101-1106` → `:1144-1150`) is wrong for a server-day-straddling sleeve either way.
> "Leaves the Kelly-lite conviction count untouched" is true as code and false as behaviour.

> **Q3 — Do you accept a trade-population change on the two Asia sleeves, not just a timing change?**
> `[MEASURED]` by the refuter on `data/historical_2026/`: **(i) Monday PDL re-basing.** Broker week
> opens Sunday 17:00 NY = server Monday 00:00. Under UTC `_day`, Monday's prior day is an 8-bar Sunday
> sliver; under server `_day`, server-Sunday has no bars so the scan (`asia_pdl_fade.py:87-96`,
> `liq_asia_up_low_metal.py:115-130`) walks back to **Friday**. XAUUSD **29/29** server-Mondays change
> PDL (example −46.14: 3884.11 → 3837.97); EURUSD 29/29; BTCUSD 13/16 (delta to +1275.60).
> **(ii) Regime-gate flips.** `_build_d1` re-buckets M15→D1: XAUUSD 177 UTC-day bars → **145** server-day
> bars (−18 %); the mandatory `_regime_up` gate (`:102`) flips on **21/120 = 17.5 %** of shared days
> (XAUUSD) and **18/120 = 15.0 %** (XAGUSD). This is the broadest sleeve in the book (30 symbols).

> **Q4 — Restore the *fitted* hour, or the *economic* hour?**
> `ny_crypto_momentum.py:38` documents the constant as "server-local **EET**" — the clock
> `broker_clock.py:209-218` says the measurement refutes. The fitted NY window is described as
> 14:00→17:00 server = UTC 11:00-14:00 in summer, which is *before* the 13:30 UTC NYSE open. The miner
> that produced the constant is not vendored (confirmed: no `gen_cmap_*` or `verify_*_sleeve.py`
> anywhere in the tree), so "restore server 17:00" is faithful to the archive but the archive's own
> session labelling cannot be audited. Moving it to the economic NY open is a **strategy change**, not
> this patch.

Two things in the plan that are **not** owner calls and should be handled as engineering: whether
`(_hour(...) or -1)` gets rewritten (no — separate commit), and the ~15× slowdown in `_day`
(0.53 ms → 8.12 ms over 3200 M15 stamps; ~25 ms/cycle for 4 metals) — cache the conversion, don't
escalate it.

## B.4 Replay blast radius — **NO. Sealed-arm comparability is not at risk.**

Evidence, all three binding mechanisms checked independently and each probe positively controlled:

| mechanism | result |
|---|---|
| R2 enforced bindings | **43** paths (41 `common_behavior_inputs` + 2 `package_authority_inputs`; `attempt5:1078` iterates only those two groups). **Zero** contain `ultimate_book`. Probe validated: it returns `config/agent_config.yaml` from the same list, and returns the two `…_SLEEVE_…_LEDGER.jsonl` paths for a `sleeve` substring. |
| `code_authority_paths` | 21 paths at `replay_acceleration_attempt5_typed_sparse_runner.py:1405-1431`. No `ultimate_book` file. |
| `_SOURCE_CONSUMER_COMPONENTS` | AST-hashes exactly two files (`replay_acceleration_source_batch.py:249-265`): `v4_timewarp_simulated_live_research_loop.py`, `wave4r_replay_microstructure.py`. No sleeve. |
| import reachability | `rg` for all eight sleeve names across `src/research_infra/` and `src/research/` → **zero hits**. The only replay→`ultimate_book` edge is `v4_timewarp_simulated_live_research_loop.py:105-108`, importing two float constants (`TICK_SPREAD_FLOOR_R`, `TICK_SPREAD_FLOOR_UNTRADEABLE_R`) from `admission.py`. `admission.py` has **no module-level sleeve import** — all are function-body (`:496`, `:519`, `:525`, `:531`, `:569`, `:605`, `:1478`), so importing `admission` never imports a sleeve. |

**The caveat that belongs next to that "no".** With `ultimate_book_live_activation_allowed: false`
(`config/agent_config.yaml:1249`), the only consumer of these sleeves today is the **shadow / runtime-learning
record — the evidence the go-live decision will be made on**. "No replay impact" is not "no impact";
100 % of the cost lands on the record that decides activation. And per CLAUDE.md §4 as reconciled
2026-07-26, the brake is a single YAML boolean on a running, funded, connected host — so the option
(c) framing "the book holds no broker authority, the cost is only shadow evidence" is a valid decision
input but a stale risk statement.

---

# C. Tick landing

## C.1 Measured broker offset — **+3 h CONFIRMED for this window; the fixed constant is REFUTED**

Independently measured on 6 symbols across 7 world-calendar anchors, offset = stamped − true UTC:

| symbol | anchor (fixed in its own calendar) | true UTC | stamped bucket measured | offset |
|---|---|---|---|---|
| JP225.cash | Tokyo cash open 09:00 JST | 00:00 | 03:00 (peak 105,971; busiest minute of day) | **+3** |
| JP225.cash | Osaka futures open 08:45 JST | 23:45 | 02:45 (8.8k → 42.6k) | **+3** |
| JP225.cash | Tokyo lunch 11:30–12:30 JST | 02:30–03:30 | dip 05:30–06:15, resume 06:30 | **+3** |
| US30.cash | NYSE open 09:30 EDT | 13:30 | 16:30 (48k → 165k; busiest minute 12,295) | **+3** |
| US30.cash | NYSE close 16:00 EDT | 20:00 | 22:45 auction spike → 23:00 collapse | **+3** |
| GER40.cash | Xetra open 09:00 CEST | 07:00 | 10:00 (23k → 74.8k) | **+3** |
| UK100.cash | LSE open 08:00 BST | 07:00 | 10:00 (12.9k → 51.3k) | **+3** |
| GER40 / UK100 | closing auctions 17:30 CEST / 16:30 BST | 15:30 | 18:34 spike on both | **+3** |
| EURUSD | US macro release 08:30 ET | 12:30 | 15:30 step (+32 %) | **+3** |
| USDJPY | Tokyo TTM fix 09:55 JST | 00:55 | 03:54 = single busiest minute (4,312) | **+3** |
| EURUSD / USDJPY | FX week Fri 21:00Z → Sun 21:00Z | — | close Fri 23:54, reopen Mon 00:05 | **+3** |
| US indices | CME early close 13:00 ET (2026-06-19, 2026-07-03) | 17:00 | 19:59:37–19:59:45 | **+3** |

Non-broker cross-check: BTCUSD/ETHUSD/AVAUSD trade 24/7, so last tick ≈ export instant. Stamped
03:19:18 / 03:20:02 / 03:17:00; Mac file mtimes 08:19 / 08:20 / 08:17 local on a UTC+8 machine =
00:19 / 00:20 / 00:17 true UTC. **Independent +3.**

Uniformity across all 19 files: 16 non-crypto symbols each show exactly 5 weekend gaps at a consistent
stamped time-of-day per asset class (FX Fri 23:54 → Mon 00:05; EU indices Fri 22:49 → Mon 01:05:15;
US indices + XAU + JP225 Fri 23:49 → Mon 01:05:00). The 3 crypto files have no ≥20 h gap. **One clock,
19 files.**

**The verdict that matters: `+3` is confirmed but must not be declared as a constant.** The window
2026-06-18→07-26 sits inside *both* the US and EU DST seasons, so this measurement **cannot
discriminate** `NEW_YORK_PLUS_7` from EET/EEST. The rule is `NEW_YORK_PLUS_7` (`broker_clock.py:204`,
evidence `:209-218`): UTC+2 under EST, UTC+3 under EDT. **Declare the rule, not −10800.** A constant is
wrong the moment anything spans 2026-11-01 (US fall-back) or 2026-10-25 (EU).

**Second correction: the window is broker-dated.** Filenames and manifest say
`20260618_to_20260726`; in true UTC the coverage is `2026-06-17T21:05Z → 2026-07-24T20:54Z` (crypto to
`2026-07-26T00:20Z`). Nothing is missing — the FX/index market never reopened before the export ran.
**Do not name the landing directory with the broker-stamped dates**, or the defect is baked into the path.

## C.2 Landing location and the exact declaration steps

`[MEASURED]`: 19 files, **71,997,348 rows**, **568,656 KB = 555.3 MiB (582.3 MB)** gzipped, ~4.2 GB
uncompressed at 58.2 B/row. Disk: **29 GiB free / 94 % full**.

**Land at `/Users/borr/GTOSActive/vps-ticks-20260726-utc/`, gzipped, outside every git tree.**
Sibling to `/Users/borr/GTOSActive/vps-export-20260725/` — the established precedent for host-mesh
arrivals from this same VPS session. Outside any working tree, so it cannot be committed by accident,
is immune to `git clean -fdx`, and survives worktree churn. **Keep them gzipped** — every probe streamed
straight from `.csv.gz` at acceptable speed; materialising 4.2 GB would take 14 % of remaining free space
for no benefit. Cost: 2 % of free space. Doctrine basis: `docs/STORAGE_AND_REMOTES.md:34` — "Generated
evidence is not committed to git going forward."

Rejected, with reasons: `<worktree>/data/mt5_research_exports/` (gitignored `.gitignore:133` and the
script default, but inside the active worktree — exposed to `git clean -fdx`);
`~/Documents/gtos/repo/ai-trading-agent/data/mt5_research_exports/` (verified safe — H4's binding is to
one `manifest.json` whose SHA-256 still matches `2362858a3b03…` — but it puts 582 MB inside a second,
inactive checkout; keep as fallback only); iCloud (forbidden as a live/read path,
`STORAGE_AND_REMOTES.md:12`).

**Steps:**

```bash
mkdir -p /Users/borr/GTOSActive/vps-ticks-20260726-utc
mv ~/Downloads/FTMO_*_ticks_20260618_to_20260726.csv.gz ~/Downloads/TICKS_MANIFEST.jsonl \
   /Users/borr/GTOSActive/vps-ticks-20260726-utc/
cd /Users/borr/GTOSActive/vps-ticks-20260726-utc && shasum -a 256 *.csv.gz > SHA256SUMS.txt
# cross-check every line against TICKS_MANIFEST.jsonl .sha256_of_gz (2 of 19 already re-verified: AVAUSD, JP225.cash)
```

**Declaring the time base — the tooling does not handle these files; four items need work.**

| file | gap | fix |
|---|---|---|
| `src/utils/broker_clock.py` | **none.** `broker_epoch_to_utc(epoch, rule)` `:308-315` is already correct for both `time` (epoch s) and `time_msc` (epoch ms) | — |
| `src/utils/research_timebase.py` | `read_bars:212` `path.open(...)` — plain text, no gzip | `gzip.open` on `.gz` |
| | `read_bars:217-226` — `strptime` then `fromisoformat`. Tested on real values, Python 3.14.4: `'1781744700'` → `ValueError: Invalid isoformat string`; `'1781744700241'` → `ValueError: month must be in 1..12, not 74`. **Both raise, uncaught — `read_bars` cannot read these files at all.** (Good news: fails loudly; 10- and 13-digit epochs cannot be mistaken for `YYYYMMDD`.) | epoch branch dispatching to `broker_epoch_to_utc` |
| | `write_sidecar:243-248` hardcodes `"time_column": "time"`; schema `gtos_timebase_sidecar_v1` has **no field for the column's encoding** — it declares *what clock* but not *what representation* | add optional additive `time_column_encoding: "epoch_seconds"\|"epoch_millis"\|"datetime_string"`, defaulting to `datetime_string` so existing v1 sidecars keep validating (no schema bump). Declare `time_msc` explicitly as the **raw broker epoch**, kept as the dedup/reconciliation key while only derived UTC is corrected |
| `scripts/declare_research_timebase.py` | `:113` `data_dir.rglob("*.csv")` never matches `*.csv.gz` | one-line glob fix |
| `scripts/measure_broker_clock_offset.py` | the real work, ~80 lines. `_load_bars:97` plain `open()`; `_load_bars:115` strptime-only and on failure **silently `continue`s** → zero rows → `main()` returns 2 ("no anchor instruments found"); `:238` hardcodes `data_dir/f"{symbol}_M15.csv"`; `ANCHORS:72-79` use GTOS names (`JP225`, `GER40`, `UK100`, `SPX500`, `US30_cash`, `NAS100`) while the export uses broker-native (`JP225.cash`, …); and **the estimator itself is wrong for ticks** — `VOLUME_COLUMNS:92 = ("volume","tick_volume","real_volume")`, but `[MEASURED]` across EURUSD (2.54 M rows), XAUUSD (6.90 M), US30.cash (4.06 M): `volume != 0` in **0** rows, `volume_real != 0` in **0**, `last != 0` in **0**. A volume-step estimator would silently produce garbage — exactly the all-zero trap the tool's own comment `:88-92` warns about | gzip + epoch branch + `.csv.gz` glob + broker-native anchor names + **a tick-COUNT-per-bucket estimator** (which is what the probe above used, and why it worked) |

`sidecar_path()` already works on `.csv.gz` (verified → `FTMO_JP225_cash_ticks_….csv.gz.timebase.json`).
**Do not shortcut with `--skip-verification`** (`declare_research_timebase.py:73-78`) — it stamps the
sidecar "asserted, not measured" and throws away the 7-anchor measurement above.

**Interim, if you want the declaration today:** call `write_sidecar` directly for the 19 files with
`basis=BROKER_LOCAL`, `rule=NEW_YORK_PLUS_7`, `server="FTMO-Server3"`, evidence citing this session's
anchors (JP225 03:00 / 05:30-06:30, US30 16:30, GER40 10:00, UK100 10:00 / 18:34, USDJPY 03:54, plus the
UTC+8-Mac-mtime cross-check). Genuinely measured, just not yet re-runnable by the probe.

**Also write a corrected companion manifest.** `TICKS_MANIFEST.jsonl`'s field *names*
`first_tick_utc` / `last_tick_utc` are actively false (`[MEASURED]`: they carry broker-local stamps with
a `Z` suffix). Leave the original byte-identical — its hashes are the verification anchor — and emit
`TICKS_MANIFEST.utc_corrected.jsonl` beside it with `first_tick_broker_local` / `first_tick_true_utc`
pairs.

**Then archive, per doctrine:** one tar of the 19 `.gz` + both manifests + sidecars + `SHA256SUMS.txt`
→ `~/Library/Mobile Documents/com~apple~CloudDocs/GTOS Cold Archive/`. Already-compressed,
manifest-bound, one large file — satisfies all three F20 rules. **In the repo commit only a pointer**
(a few KB of JSON under `research/operations/`): the 19 SHA-256s, row counts, absolute landing path,
true-UTC window, and the timebase declaration. **Delete from `~/Downloads` after landing** — Downloads
is not a storage tier. **Secrets: clean** — the manifest carries no account, login, server or path; the
CSVs are `time,bid,ask,last,volume,time_msc,flags,volume_real` only.

## C.3 What is MISSING

**Symbols — 17 of the replay 24-surface arrived; 7 did not.**
Surface: `GTOS_24_SYMBOL_SURFACE`, `v4_timewarp_simulated_live_research_loop.py:251-278`; broker names
via `FTMO_SYMBOL_MAP:280-290`.

**Missing (7):** `CHFJPY`, `EURGBP`, `EURJPY`, `USDCHF`, `XAGUSD`, `USOIL_cash`, `UKOIL_cash`.
**Arrived but outside the surface (2):** `AVAUSD`, `NZDJPY`. 17 + 2 = 19. ✓

Per-sleeve tick coverage for the eight B29 sleeves (`ON_SURFACE` read from each module):

| sleeve | `ON_SURFACE` | covered | gap |
|---|---|---|---|
| `ny_crypto_momentum` `:45`, `kz_london_crypto_low` `:35`, `orb_crypto_london` `:36` | BTCUSD, ETHUSD | 2/2 | — |
| `asian_fade` `:46` | EURUSD, GBPUSD | 2/2 | — |
| `metal_session_reversion` `:36` | XAUUSD, XAGUSD | **1/2** | XAGUSD |
| `liq_asia_up_low_metal` `:28` | XAUUSD, XAGUSD, XPTUSD, XPDUSD | **1/4** | XAGUSD, XPTUSD, XPDUSD |
| `vss_fxcross_london_up_low` `:37` | EURJPY, GBPJPY, CHFJPY, AUDJPY, EURGBP | **2/5** | EURJPY, CHFJPY, EURGBP |
| `asia_pdl_fade` `:33-39` (30 symbols) | — | **17/30** | USDCHF, EURJPY, CHFJPY, EURGBP, XAGUSD, XPTUSD, XPDUSD, XRPUSD, XTZUSD, LTCUSD, DASHUSD, USOIL_cash, UKOIL_cash |

**This is directly load-bearing for B29.** The three worst-covered sleeves —
`metal_session_reversion`, `liq_asia_up_low_metal`, `vss_fxcross_london_up_low` — are exactly the ones
whose behaviour the clock fix changes most (Q3's 17.5 % / 15.0 % regime flips were measured on
XAUUSD/**XAGUSD**, and XAGUSD has no ticks). Tick-level validation of the fix is possible on XAUUSD and
the crypto/major-FX sleeves; it is **not** possible on the metals crosses or the fx-cross sleeve.

**Depth — nothing arrived. The probe returned zero, and the probe is validated.**
- The export is `COPY_TICKS_ALL` (manifest `note`): "time=epoch seconds, time_msc=epoch ms; gzip CSV",
  columns `time,bid,ask,last,volume,time_msc,flags,volume_real`. **Top-of-book quotes only.**
- `last`, `volume`, `volume_real` are **identically zero** across every symbol sampled `[MEASURED]`.
  No trade prints, no size, no depth.
- No `market_book` / DOM capture exists in the VPS export `[MEASURED]`: `rg` over
  `gtos_export_20260725T230714Z.FINAL.MANIFEST.jsonl` → 0 hits for `market_book`, `MarketBook`,
  `depth_capture`; the 3 `orderbook` and 1 `book_depth` hits are **literature files**
  (`research/ml_program/literature/06_market_microstructure_orderbook/papers.csv`,
  `primitive_orderflow_sources_2026-05-02/raw/cboe_equities_book_depth.html`). Probe positively
  controlled: the same `rg` returns 1 for `ftmo_history_deals_get`.
- `04_pipeline_state/sierra_depth_enrichment_checkpoint.json` `[MEASURED]`: every candidate has
  `depth_path: null`, `depth_file_size_bytes: null`, `features_present: false`,
  `last_feature_status: "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL"`. **The Sierra depth pipeline never
  produced a single depth file.**

## C.4 Do these ticks substitute for the dead execution ledgers? **No.**

**What they genuinely unblock** — this is real and it is large:
- Quality: `time_msc` sub-second ≠ 0 on **100.0 %** of rows (EURUSD 2,536,416/2,536,569; XAUUSD
  6,904,074/6,904,623; US30 4,055,114/4,055,135). Flags `1158`/`1154`/`1028` — BID and/or ASK bits on
  every row. **Genuine millisecond quote ticks, not bar-synthesised** (synthesis lands on round seconds
  and carries LAST/VOLUME flags).
- `09_mt5_api/ftmo_history_deals_get.jsonl` holds **269 FTMO deal rows with real fill prices**
  (`price`, `commission`, `swap`, `profit`, `entry`, `volume`). V2 said
  `broker_order_lifecycle_capture_v4` is request-side only — true, but the broker's own deal history is
  the **result** side, and it survived. Both `deal.time_msc` and `tick.time_msc` are the same broker
  millisecond epoch, so **the join needs no clock correction at all** (correction is only needed to
  *report* in true UTC).
- **173 of 268 traded deals fall inside the tick window; 100 % of those 173 are on covered symbols;
  all 173 carry a real fill price** (−777.97 total commission); ≈86 round trips across 17 symbols.
  Executed: joining USDJPY deals to 2,035,570 ticks reproduced a quote for **every** deal at a **median
  149 ms** quote age.

**The self-correction that must survive into the record.** A first pass reported a "deterministic
0.30 pip buy / 0.20 pip sell markup with zero variance" across 24 USDJPY deals. **That was an artifact
of a naive last-tick-at-or-before estimator and it is wrong.** Asking instead whether *any* tick within
±2 s reproduces the fill exactly overturned it:

| symbol | slip vs last-tick touch | best \|fill − touch\| within ±2 s |
|---|---|---|
| GER40.cash (6) | 0.000 on all 6 | 0.000 — exact |
| XAUUSD (18) | median 1.0 unit | **0.000 — exact** |
| EURUSD (13) | median +0.2 pip | median 1.0 tick |
| USDJPY (24) | median +0.25 pip | median 2.0 ticks; 3/24 exact |

Honest conclusion: **fills sit within 0–2 minimum ticks of the exported quote stream.** That validates
the join and supports a cost model. It is **not** a zero-residual reconciliation — the residual mixes
execution latency, the executing feed differing from Market Watch history, and at least one genuine
coverage hole (one EURUSD deal at broker stamp `Fri 2026-06-19 14:30:54` = `11:30:54Z` has **no tick
within ±2 s** — a Friday-midday gap, not a market closure). A Phase 6 build must model that, not assume
it away.

**Why they are not a substitute:**
- A tick says what the touch was at time T. It says nothing about queue position, market impact,
  partial-fill behaviour, requote / last-look, or why a pending order did not fill.
- No trade prints, no size, no depth (C.3).
- The 594 request-side rows in `broker_order_lifecycle_capture_v4` gain a **counterfactual reference
  price at request instant** — an upgrade from unusable to "cost bounded against quoted top-of-book" —
  but that is inference, not fill truth.
- **V2 remains a build item.** These ticks change its scope (a reference price now exists for the
  request side) but not its necessity.

---

# D. Residual risks — what I would not sign off on

**D-1. The orphaned LFS object is a single point of failure and nothing currently protects it.**
Hold #4's contract-matching payload `19365f60…` exists as one working-tree file plus one **unreferenced**
object in `/repo/.git/lfs/objects/19/36/`. HEAD's pointer names `a5bcc0f8…`. Any `git lfs prune`,
`git gc --aggressive` with LFS integration, or fresh clone loses it. **Closes when:** the operator either
commits the `19365f60` bytes so a pointer references them, or copies the file to the out-of-tree hold
directory (P2 does this) *and* records the hash in a committed pointer artifact. I would not consider the
D1 operation complete without P2 executed.

**D-2. The 40 MB of untracked `.json` / `.md` in S4 is genuinely unrecoverable and I did not read all
173 of them.** I classified them by extension and by absence from any contract binding, prefix sweep, or
`.hermes` reference. That is a negative result from a name-based probe, and the probe was positively
controlled — but a summary JSON containing a number nobody re-derives elsewhere would not show up in it.
**Closes when:** someone greps the 173 for numeric claims cited in the audits, or (cheaper) demotes them
alongside S1 instead of deleting. At 40 MB the cost of keeping is nil; **if you want zero residual risk,
move S4 into the hold and accept 40 MB.**

**D-3. I did not execute the per-day replay body.** H3/H5 forbid it here (8.61 GB maxrss, 16.5 h/arm,
no sub-window mode). The claim that a fresh or resumed April arm touches exactly six paths under the
target directory rests on the refuter's instrumented replication of `run_sealed_arm()`
(`b7_5_post_acceleration_runner.py:2210-2239`) reaching `shared digest match: True` — a launch the seal
would accept — stopped deliberately before `configure_output_namespace` and `run_replay_engine`, plus a
static bound on the eight globals `configure_runtime_evidence_root` rebinds. **If a route read exists
deeper in the day loop that is not reachable from those globals, that method would not have seen it.**
**Closes when:** the first post-deletion April arm launches and reaches day 1 without
`runtime_evidence_input_missing:*`. Do that on **one arm** before proceeding to the other three.

**D-4. The B29 patch is not ready to apply.** Q1 (one clock or two) must be answered first — it decides
whether `fx_jpy.py:99-119` and `metals.py:157-158` move in the same commit, and the disagreement window
is inside the sealed March challenge. Q2's four-consumer answer must be written down before code lands.
The fixtures at `test_new_sleeves.py:288-314` and `:302` must be rebuilt, not re-baselined. **I would not
sign the plan as written**; I would sign the patch table in B.1 once Q1 and Q2 are answered.

**D-5. The "684 failures at `acad79826`" figure is unverified.** I measured `tests/ultimate_book` (60
failed / 403 passed) and `test_new_sleeves.py` (20/20) but did not run the full suite. CLAUDE.md H2's
established figure is 10 failures in `tests/test_selector_v4.py`. **Closes when:** someone runs the suite
at `HEAD~` and at the change and diffs the failure sets, per CLAUDE.md §6.

**D-6. Tick-level validation of the B29 fix is impossible on three of the eight sleeves.** XAGUSD,
XPTUSD, XPDUSD, EURJPY, CHFJPY, EURGBP have no tick coverage (C.3). The Q3 measurements that justify the
owner decision were made on M15 bars from `data/historical_2026/`, not on these ticks. **Closes when:**
a second VPS export covers the 7 missing surface symbols — cheap, same script, ~1 hour.

**D-7. The tick timebase cannot yet be declared by the sanctioned tool.** Four files need work (C.2) and
`measure_broker_clock_offset.py` would silently return "no anchor instruments found" today. Declaring via
a direct `write_sidecar` call is defensible because the measurement is real, but it leaves the
declaration **not re-runnable**, which is exactly the property the tool exists to provide. **Closes
when:** the tick-count estimator lands and `declare_research_timebase.py` re-derives +3 from the files
themselves.

**D-8. Nothing in this package touches the actual brake.** Per CLAUDE.md §4 as reconciled 2026-07-26,
the only thing between a running, funded, connected VPS and live orders is
`ultimate_book_live_broker_authority: false` — no flag file exists anywhere in either tree. The
activation-token mechanism (`src/safety/activation_token.py`) is the thing that fails closed, and **it is
not on the VPS**. Everything in A, B and C is preparatory. **Closes when:** the token is ported to the
VPS. That is the highest-value item on this page and it is not in scope of any of the five inputs.
