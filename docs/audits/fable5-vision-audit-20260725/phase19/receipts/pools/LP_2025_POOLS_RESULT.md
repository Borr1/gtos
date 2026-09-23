# LP_2025_POOLS_RESULT — diagnostic pools for all six 2025 lane windows

Session **LP**, 2026-08-06, under OD-BROAD-FORENSIC-2. Branch `phase19/march-confirm`
in `worktrees/fa2-integration-20260803`. `main` untouched; nothing merged.

**Evidence class.** `LANE_ITERATION_EVIDENCE — unbilled exploration, never
admission-grade`. Every artifact here is an **input**. `billed: false` and
`selection_authority: NONE_SUBSTRATE_ONLY` are stamped in all six receipts.

**LP took no look.** No economic quantity from any of these six windows is read,
interpreted, ranked or compared anywhere in this document. The pool receipts
carry the canonical reader's summary because every prior pool receipt does and
the next wave's tooling reads it; producing it is a mechanical byproduct of the
same single pass that writes the pool. LP did not read it.

---

## 0. TL;DR

**Six diagnostic pools exist where there were none.** 179 window-days replayed,
141,410 pool rows, six arms, zero failures. Every window in LM-MAT's registry
now has a pool.

**Three of the six are stamped READ-RESTRICTED** — `june_2025`, `august_2025`,
`september_2025`. They are built and join-ready and **may not be read** until a
pre-declared test names them. Building a pool is not reading it; §3.

**The machine's replay capacity was mispriced by ~3x, in the direction of
"we can do much more".** Six month-windows that cost **15.77 h of arm time** were
delivered in **5.78 h of wall clock**, and the per-window-day rate under five-way
concurrency (250–366 s/day) **straddles the solo baseline** (314.6 s/day). Running
five arms at once cost individual arms roughly nothing. §4 is the measured table,
and it is the most reusable thing in this document.

**The estate's testable calendar is now eleven windows with pools**: Jan/Feb/Apr/May
2026 here, March 2026 in the `wave19-broad-forensic-20260801` worktree, and these
six 2025 months. §5 states exactly where each lives, because they are not all in
one place and a reader who assumes they are will fail an `ls`.

---

## 1. What was run

One **r0 baseline arm** per window — the same shape that produced the January and
March pools, copied verbatim from `run_march_decode_event.sh`'s `FA2_M_R0` row so
the pools are comparable without any argument reconciliation:

```
--arm S0R0 --purpose LANE_ITERATION --keep-outputs
--patches authority_hash_content_memo,abc_concrete_types,gc_during_chunk,
          skip_post_hoc_ledger_recertification,ledger_scalar_projection,
          missed_pool_projection
--repairs commission_broker_true_gated,swap_horizon_true
```

Registry (read-only, external hold):
`/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/LANE_INPUT_REGISTRY.json`

Every invocation carried `GTOS_MARCH_ONE_SHOT_PREREG_SHA256=da6c7262…` — the
registry's fuse is broader than it needs to be and refuses to open without it,
whatever window is asked for (LM-MAT §7 item 5).

Runner: `lp_run_arm.sh` (this directory). Pools: `lp_pool.py`. The build was
driven by `lp_supervise.sh`, which projects each pool the moment its arm's
receipt appears — the arms finish at unpredictable times hours apart, and an
operator polling for them is both the slowest link and the one most likely to
drop one.

### The smoke, and what it taught

The commission asked for a 2-day smoke before committing hours to a window. The
first attempt **failed correctly**, and the failure is worth recording because
the next session will hit it:

```
ValueError: broad_replay_source_plan_digest_mismatch:
  expected=b36eb41c…(31-day registry digest):
  actual=['119a888b…']
```

`--lane-source-plan-digest` binds the canonical source plan over **the days
actually in the run**: `replay_acceleration_attempt5_typed_sparse_runner.py:16476`
builds `canonical_source_plan_digests` from the plans it just constructed and
`:16480` compares the expected digest against them. A `--days 2` prefix has its own
digest and can never match the whole-window one. **A bounded smoke of a lane
window must be given the prefix's own plan digest, not the registry's.** Re-run
that way it passed cleanly (972 s, 3.265 GB, 2 packs, 15,774 missed rows) and
proved registry, fuse key, pack resolution, engine and output writing before
anything long started.

---

## 2. The pools

| window | pool | rows | join keys | trading days | sha256 | read |
|---|---|---:|---:|---:|---|---|
| `june_2025` | `LP_june_2025_S0R0_POOL_V1.jsonl.gz` | 15,578 | 15,578 | 16 | `a6585218d0f2552e…` | **RESTRICTED** |
| `august_2025` | `LP_august_2025_S0R0_POOL_V1.jsonl.gz` | 22,242 | 22,242 | 20 | `1199ca0a4679c787…` | **RESTRICTED** |
| `september_2025` | `LP_september_2025_S0R0_POOL_V1.jsonl.gz` | 25,051 | 25,051 | 22 | `9c830abe961e1690…` | **RESTRICTED** |
| `october_2025` | `LP_october_2025_S0R0_POOL_V1.jsonl.gz` | 29,192 | 29,192 | 23 | `3a8e5a79777f16fc…` | open |
| `november_2025` | `LP_november_2025_S0R0_POOL_V1.jsonl.gz` | 26,374 | 26,374 | 20 | `e066aa6bf43f6b61…` | open |
| `december_2025` | `LP_december_2025_S0R0_POOL_V1.jsonl.gz` | 22,973 | 22,973 | 19 | `f9cab81ee969b05c…` | open |

All six live in
`docs/audits/fable5-vision-audit-20260725/phase19/receipts/pools/`, beside
`CS_APRIL_S0R0_POOL_V1.jsonl.gz` and `CS_MAY_S0R0_POOL_V1.jsonl.gz`. **52 MB for
all six.**

Each has a receipt `<window>_S0R0_POOL_V1.json` in the same directory, schema
`gtos-session-lp-compact-s0r0-pool-v1`, `compatible_with`
`gtos-session-cs-compact-s0r0-pool-v1`:

- `june_2025` `cc2806194a673915becd18ef4d1b7b5de61c469ba7f036b93765a44da79704d0`
- `august_2025` `7a0f3801839cb0ac6857fd0577482d6dc1baf8eb46f6fb21164485e1cc5652c1`
- `september_2025` `0074bfcdc15e0e5acd1c7103fdfb498abf1bf8532207ad346afab6e25007ae3c`
- `october_2025` `89671c5290f5c1d7fcd1caca6b111752f062be8d2fff7237f63f89b8c610ada4`
- `november_2025` `6bb9f42616b9a29646a264c443782485452a0cdc63974abf905eb47aab08dcce`
- `december_2025` `c30bc8a91c26d10088c85282972f3570be7d2f7c44dad749b53f6d34691c40ab`

**Rows equal unique join keys in all six.** The `(S0R0, candidate_id,
decision_time_utc)` key is unique with no duplicates anywhere, every row carries
the full identity + geometry set CS requires, every `decision_time_utc` falls
inside the registry's declared capture window, and every geometry is finite with
`entry_price != stop_loss`. Those are not assertions made afterwards — `lp_pool.py`
refuses to write a receipt if any of them fails, so the receipt's existence is
the check.

`trading days` is the count of distinct UTC decision dates present, which is
lower than the window's calendar length because weekends carry no candidates.

### Provenance binding

Each pool receipt binds, and `lp_pool.py` refuses on any mismatch: the arm's
`S0R0` id and `LANE_ITERATION` purpose; the registry's `window_id`; the
registry's `[start, end]`; the **canonical source-plan digest**;
`campaign_sealed: false`; and `clock_rule: new_york_plus_7`. It also records the
raw ledger's sha256 and byte count, and the arm receipt's sha256.

`train_dates` / `oos_dates` are **deliberately absent** and the receipt says so
(`fold_split_declared: false`). CS derives those from its window's declared local
split. These windows have no fold plan, and inventing one here would be a fold
decision made by the wrong session.

---

## 3. READ-RESTRICTED — june, august, september

These three carry a marker file beside the pool:

```
LP_june_2025_S0R0_POOL_V1.jsonl.gz.READ_RESTRICTED
LP_august_2025_S0R0_POOL_V1.jsonl.gz.READ_RESTRICTED
LP_september_2025_S0R0_POOL_V1.jsonl.gz.READ_RESTRICTED
```

and `read_restricted: true` with `status: BUILT_UNSPENT_HELD_OUT` in their
receipts.

**The rule: no analysis may read these three pools' economics until a
pre-declared test names the window.**

This is a test-set decision, not caution. Two candidate results died out of
sample this week, and an untouched window is the only instrument that catches
that early. The original instruction was to leave these three *unbuilt*; the
instruction changed to *build but do not read*, which is strictly better —
**building a pool is not reading it.** The replay is deterministic given the
registry inputs; nothing about the artifact's existence tells anyone what is in
it, and no economic quantity from these three was printed, logged or looked at
by this session. What changes is that when a declared test finally wants them
they are already on disk rather than three hours away.

`october_2025`, `november_2025` and `december_2025` are open — the working set.

---

## 4. Resource truth, measured

This section exists because the published estimate was wrong in both directions
at once, and both corrections matter for planning.

### Per arm

| window | days | wall | s / window-day | peak RSS |
|---|---:|---:|---:|---:|
| `june_2025` | 28 | 1h56m | 249.7 | 3.13 GB |
| `august_2025` | 30 | 2h45m | 330.1 | 4.23 GB |
| `september_2025` | 30 | 2h33m | 307.6 | 4.38 GB |
| `october_2025` | 31 | 3h08m | 365.7 | 3.71 GB |
| `november_2025` | 29 | 2h41m | 335.0 | 3.57 GB |
| `december_2025` | 31 | 2h39m | 309.6 | 4.03 GB |
| **solo baseline** `FA2_M_R0` (March, run alone) | 31 | 2h42m | **314.6** | 4.21 GB |

Ledger volumes are in `lp_result_table.py`'s output and in each arm receipt
(`receipt_counts`): 102,881–174,382 missed-opportunity rows per window.

### The two RSS numbers are both true and they are not the same measurement

- **Peak RSS per arm: 3.13–4.38 GB.** This is `maxrss` from the arm's own
  `rusage`, and it is what the commission's 4.2–4.8 GB figure was describing. It
  is correct.
- **Instantaneous RSS per arm under five-way concurrency: 0.35–1.5 GB** through
  most of a run. This is what a `ps` sample sees, and it is what the ~1.4 GB/arm
  correction was describing. It is also correct.

  One caveat that matters if you sample a *single* arm and generalise: RSS here
  is **elastic under pressure**. September, running alone at the end of the
  event with the machine quiet, sat at **3.7–4.0 GB sustained** — the same
  process that would have shown ~1 GB with four siblings competing. The low
  figure is partly the OS reclaiming, not purely the arm's demand. Sample under
  the concurrency you intend to run.

They differ ~3x because of H3's mechanism: the traced heap grows monotonically
through each replay day and collapses at day end, and RSS spikes to its peak at
the instant of that collapse, when day-end serialisation forces the accumulation
resident. **An arm is at its peak for seconds per day and near its floor the rest
of the time.**

The operational consequence is the useful part: **peaks across concurrent arms do
not coincide**, because the arms are not synchronised to each other's day
boundaries. Five arms whose individual peaks sum to ~19 GB were measured at a
**combined peak of 7.29 GB**. Planning against the sum of the peaks over-reserves
by roughly 2.5x.

Combined resident, sampled every 30 s across the whole event
(`LP_CONCURRENCY_SAMPLES.log`, 392 samples):

| arms in flight | max combined RSS observed |
|---:|---:|
| 2 | 5.64 GB |
| 3 | 3.93 GB |
| 4 | 7.05 GB |
| 5 | **7.29 GB** |
| 6 | 4.08 GB (only ~4 min at six — the sample never caught a peak) |

### Concurrency was close to free — and the binding constraint is cores, not RAM

**15.77 h of arm time delivered in 5.78 h of wall clock, 2.73x.** The 2.73 is a
floor, not a ceiling: the event ramped 2 → 5 arms and tailed to one, so mean
occupancy was well under five. Had all six started together it would have been
~3 h.

The reason concurrency is nearly free is that **each arm is single-threaded and
pins exactly one core at 98–100 %** (verified by `ps` on every arm, repeatedly).
This machine is an **Apple M4, `hw.ncpu` 10 — 4 Performance + 6 Efficiency**
(`hw.perflevel0.name = Performance, logicalcpu 4`; `hw.perflevel1.name =
Efficiency, logicalcpu 6`). So the throughput ceiling is *cores*, and the RAM
ceiling everyone has been planning against was never the binding one. Note the
P-core count is **four**: the fifth and sixth concurrent arms are already
landing on efficiency cores, which is part of why five is the practical number
and six buys little even before the swap problem. The per-window-day rates
above are the proof: under
five-way concurrency they run 249.7–365.7 s/day and **straddle the 314.6 s/day
solo baseline**. Four of six beat it or matched it.

### Where the ceiling actually is: five

Measured directly, and it is sharp.

- At **six** arms: swapouts ran **11–14 MB/s sustained**, the swap file grew
  5,120 → 8,192 MB, and free swap fell to **545 MB**. Arms' own resident total was
  only 3.9 GB — the pressure was macOS evicting everything else on the box to
  make room.
- Dropping to **five** took the swapout rate to **0 MB/100 s** within one sample
  interval, and swap used fell back.

So September was stopped after four minutes (0 days completed, nothing lost),
requeued, and started automatically when the first arm retired. **Five concurrent
lane arms is this machine's ceiling with an analysis swarm sharing it.** Later
in the event, with the swarm quieter, five arms ran at a 0 MB/s swapout rate for
long stretches — so five is the safe standing number and six is the number that
tips it.

Disk: **544–617 MB per route after compression, 3.4 GB for all six**;
`lp_run_arm.sh` gzips a route's `*.jsonl` only **after** its receipt exists, so a
crash during compression can never be mistaken for a completed arm. Free space
went 39 GB → 33 GB across the whole event, and that 6 GB includes the
uncompressed peak of whichever routes were mid-flight.

### What this re-prices

Six month-windows in under six hours on one laptop, at five at a time, with the
per-arm rate unharmed. A twelve-window year is a ~12 h overnight run, not a
multi-day campaign. **The published ~3 GB/arm-and-never-run-two folklore should
be replaced with: budget ~1.5 GB steady and ~4.4 GB peak per arm, run five, and
expect ~315 s per window-day regardless of how many are in flight.**

---

## 5. The eleven windows, and where they are

The estate now has a diagnostic pool for eleven windows. They are **not all in
one worktree**, and this is the list a reader should follow rather than guessing:

| window | pool | location |
|---|---|---|
| January 2026 | `CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz` | `phase16/receipts/pools/` (here) |
| February 2026 | `CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz` | `phase18/receipts/pools/` (here) |
| March 2026 | `e_MARCH_POOL_V1.jsonl.gz`, `e2_MARCH_R0_POOL_V1.jsonl.gz` | `phase19/receipts/discovery/` in **`worktrees/wave19-broad-forensic-20260801`** |
| April 2026 | `CS_APRIL_S0R0_POOL_V1.jsonl.gz` | `phase19/receipts/pools/` (here) |
| May 2026 | `CS_MAY_S0R0_POOL_V1.jsonl.gz` | `phase19/receipts/pools/` (here) |
| June 2025 | `LP_june_2025_S0R0_POOL_V1.jsonl.gz` | `phase19/receipts/pools/` — **RESTRICTED** |
| August 2025 | `LP_august_2025_S0R0_POOL_V1.jsonl.gz` | `phase19/receipts/pools/` — **RESTRICTED** |
| September 2025 | `LP_september_2025_S0R0_POOL_V1.jsonl.gz` | `phase19/receipts/pools/` — **RESTRICTED** |
| October 2025 | `LP_october_2025_S0R0_POOL_V1.jsonl.gz` | `phase19/receipts/pools/` |
| November 2025 | `LP_november_2025_S0R0_POOL_V1.jsonl.gz` | `phase19/receipts/pools/` |
| December 2025 | `LP_december_2025_S0R0_POOL_V1.jsonl.gz` | `phase19/receipts/pools/` |

**`july_2025` is absent and that is correct** — NOT_EVALUABLE on a measured gap
in the upstream FTMO M1 export, never registered (LM-MAT §2b). Asking for it
fails with `lane_window_not_registered`.

---

## 6. Two things the next wave must carry

**These months are not clean out-of-sample, restricted or not.** LM-MAT §2 is
explicit: the estate's own ratified surface map names this 2025 range as the
selection surface that picked the armed sleeves. The READ-RESTRICTED stamp buys
an *untouched-by-this-programme* test set, which is worth having and is not the
same thing as a virgin window. February 2026 was the last true first read and it
has been spent.

**Three of the six are not whole calendar months** — `june_2025` starts 06-03,
`august_2025` ends 08-30, `november_2025` ends 11-29 — each for a measured
boundary reason in LM-MAT §2b. Any per-month normalisation must use the pool's
own `dates` list, which the receipts carry, not a 30/31-day assumption.

---

## 7. Files

Produced by this session, all in
`docs/audits/fable5-vision-audit-20260725/phase19/receipts/pools/`:

- `LP_{june,august,september,october,november,december}_2025_S0R0_POOL_V1.jsonl.gz` — the pools
- `{june,august,september,october,november,december}_2025_S0R0_POOL_V1.json` — their receipts
- `LP_{june,august,september}_2025_S0R0_POOL_V1.jsonl.gz.READ_RESTRICTED` — the markers
- `arm_receipts/LP_{JUN,AUG,SEP,OCT,NOV,DEC}_2025_S0R0_RECEIPT.json` + `.log` — the arms
- `lp_run_arm.sh`, `lp_pool.py`, `lp_supervise.sh`, `lp_result_table.py` — the tooling
- `LP_CONCURRENCY_SAMPLES.log` — 392 30-second samples of arm count, combined RSS, swap and free memory; the evidence behind §4

Arm routes are untracked under
`research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse/LP_*_2025_S0R0/`,
gzipped, 3.4 GB for all six. They can be deleted; the pools are the mineable
artifact and every receipt records the raw ledger's sha256 and byte count so a
later session can tell whether the route it finds is the one the pool came from.

### One deliberate departure from the March precedent

The arms also emit `*_RECEIPT_ECONOMICS.json` — the per-trade, per-order and
per-scorecard tables. **These are NOT committed, and that is a choice against
precedent, so it is recorded rather than left for someone to notice.**

March committed its equivalent: `FA2_M_R0_RECEIPT_ECONOMICS.json` is a
**208.51 MB raw inline blob in HEAD**, `filter: unspecified` — not LFS. Six of
mine would have added **1.04 GB** of the same. `CLAUDE.md` §8 measures this exact
pathology (4.8 GB of the tracked tree already sits in 280 inline non-LFS blobs
over 5 MB) and admits generated evidence only when it is active reproducibility
evidence or unique intelligence behind a cold-evidence pointer. This content is
neither: it is fully regenerable from the retained routes and its mineable
projection is the pool.

They are therefore **gzipped and left untracked** beside the arm receipts —
113 MB total, in
`docs/audits/fable5-vision-audit-20260725/phase19/receipts/pools/arm_receipts/`:

- `LP_AUG_2025_S0R0_RECEIPT_ECONOMICS.json.gz` `264b20fd1d37acffb38aec49c44388e4d37f3fac77fe47d630693213c8ed0e57`
- `LP_DEC_2025_S0R0_RECEIPT_ECONOMICS.json.gz` `71d99e77caa4129cfdcba26a60fa3b2e652f23b52a788464d80c1cdf2a3b409e`
- `LP_JUN_2025_S0R0_RECEIPT_ECONOMICS.json.gz` `651f3c157c81cebb57b3159be87469d8fe0de080bec9d09cc0ea91ae970a89e1`
- `LP_NOV_2025_S0R0_RECEIPT_ECONOMICS.json.gz` `b1be4ccefef42509367c80e5ef70969b5ddf7e1c98cb9970cdd651d1aa7bda84`
- `LP_OCT_2025_S0R0_RECEIPT_ECONOMICS.json.gz` `f9e2e7ef9db3cc8d3474e6a11aa415d0880a2ea7761af5199022017b051f289d`
- `LP_SEP_2025_S0R0_RECEIPT_ECONOMICS.json.gz` `9240affd799e6d117e84333d6fea18316316921413f59b9bf8034cc82b121788`

If a later session decides they belong in HEAD, `git add` them as `.gz` — 113 MB
rather than 1.04 GB — and strike this note. **Machine-local until then: a fresh
clone will not have them.** The three from `june`/`august`/`september` are
covered by the read restriction (§3, `READ_RESTRICTED_INDEX.md`).
