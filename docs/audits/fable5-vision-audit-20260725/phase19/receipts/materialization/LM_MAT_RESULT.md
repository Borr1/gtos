# LM_MAT_RESULT — materializing the unbuilt 2025 lane calendar

Session **LM-MAT**, 2026-08-05/06, under **OD-BROAD-FORENSIC-2**. Branch
`phase19/march-confirm` in `worktrees/fa2-integration-20260803`. `main` untouched;
nothing merged.

**Evidence class.** `LANE_ITERATION_EVIDENCE — unbilled exploration, never
admission-grade`. Everything here is an **input**. Bars and ticks with one
timestamp column rewritten through `broker_epoch_to_utc`, their manifests, their
canonical source-plan digests, and their prepared day packs.

**No economic outcome of any newly materialized window was computed, printed,
logged or written.** Not an R, not a win rate, not a trade count, not a P&L, not
a candidate, not an order, not a ledger row, not a "sanity check on returns".
The windows below are outcome-unread and remain usable as first-read evidence.
Section 6 states how that claim is checkable rather than merely asserted.

---

## 0. TL;DR

**Six new lane windows exist where there were none, and the estate's testable
calendar goes from 5 windows to 11.** All six are registered, plan-bound and
pack-complete; §8 carries the exact `--window` / `--lane-source-plan-digest`
pair for each.

**A seventh, `july_2025`, is NOT_EVALUABLE and was deleted rather than
registered** — a measured gap in the upstream FTMO M1 export (§2b).

**Two corrections the next wave must carry.** These months are **not
outcome-virgin** — the estate's own ratified surface map names this exact range
as the selection surface that picked the armed sleeves (§2). And three of the
six are not whole calendar months, each for a measured boundary reason (§2b).

**The five pre-existing windows never moved**, verified after every mutating
step (§4).

---

## 1. What now exists

| window | span | days | ticks | packs | source-plan digest |
|---|---|---:|---|---:|---|
| `june_2025` | 2025-06-03 → 06-30 | 28 | — | 28 | `b2de9cb0…da66ab2e` |
| `july_2025` | — | — | — | — | **NOT_EVALUABLE, not registered** |
| `august_2025` | 2025-08-01 → 08-30 | 30 | — | 30 | `e604c43a…b65aebe3f` |
| `september_2025` | 2025-09-01 → 09-30 | 30 | — | 30 | `3df3c931…cd875ab03` |
| `october_2025` | 2025-10-01 → 10-31 | 31 | 4 sym | 31 | `b36eb41c…3ec32178` |
| `november_2025` | 2025-11-01 → 11-29 | 29 | 4 sym | 29 | `b51195fe…f874bc62` |
| `december_2025` | 2025-12-01 → 12-31 | 31 | 4 sym | 31 | `b63e8d91…20d9696b1` |

Full digests in §8 and in `LM_MAT_RESULT.json`. Sources added: 24 M1 files per
window (~745 k rows each) plus, for the three tick-bearing windows, the four
ordered-tick symbols. The 72 static D1/H4/M15 rows are reused **by reference**
from CJ's catalog in every window — re-transforming them would rewrite bytes
five other windows' manifest digests depend on.

The catalog itself is **unchanged** (`catalog_root_sha256` is bound by the
registry, so it must be). New M1 families live only in their own window's
manifest — exactly the shape the March extension established.

---

## 2. The correction that matters most: these months are NOT "virgin"

The brief that commissioned this work described the unbuilt 2025 calendar as
"outcome-virgin". **Half of that is true and half of it is false, and the false
half is load-bearing for whatever the next wave does with these windows.**

True: **never materialized.** Before this session there was no lane pack, no
source manifest, no source-plan digest and no true-UTC source for any 2025 month.
Verified by direct read of the hold before touching it — `manifests/` held
exactly five files, `packs/` exactly the five windows' roots (plus three
successor roots), and `sources/bars/` held M1 families for `202601`, `202602`,
`202603`, `202604`, `202605` only.

False: **outcome-virgin.** The estate's own ratified surface map
(`trainer_partitions.DEFAULT_SURFACE_MAP`, `val_selection_surface_2025_2026H1`,
ratified 2026-07-31) says of exactly this range, in its `prior_consumption`
field:

> SELECTION SURFACE. The W7 survivor book and the growth-Kelly sizing dial were
> both chosen on days >= 2025-01-01, so this range is the window that PICKED the
> armed sleeves. Also fitted day-by-day by the June v4 mechanical-edge route
> (`ULTIMATE_EDGE_TRAIN_DAY_PROGRESS_LEDGER.jsonl`, 234 rows
> 2025-07-01..2026-05-29, partition_role TRAIN and status completed on every
> row) …

So every window built here sits inside the `d.year >= 2025` predicate that
selected the armed sleeves (`build_survivor_book.py:74`,
`KB7_growth_kelly_sizing.py:130`), and **six of the seven** (July–December 2025)
also sit inside the June v4 route's day-by-day fitting range. **June 2025 is the
only one of the seven outside that day-by-day range**, and it is still inside the
selection predicate.

What is genuinely unread: no sealed B7.5 replay arm and no lane decode event has
ever read a 2025 day. The band's own list of sealed reads is 2026-only
(2026-01-01..01-31, 2026-04-01..04-15, 2026-05-13..05-17).

**The honest description of what this session produced is therefore: six
never-materialized, never-replayed windows on a surface that already selected
the armed book.** They are a large and real expansion of testable calendar. They
are not clean out-of-sample in the sense a naive reader of "virgin" would assume,
and any q-value or admission computed on them must carry the selection-surface
disclosure the surface map already attaches to them. The lane guard attaches it
automatically — every day here returns `surface=VAL` with
`used_once_disclosure` set — so the disclosure travels with the receipts whether
or not a reader remembers it.

---

## 2b. Four window-boundary defects, each measured

Four of the seven windows failed on the first attempt, and it is worth being
precise that they failed for **four different reasons**. None was a bug in the
extension; all four are properties of the source estate that only a real build
surfaces. Each was located from the tool's own refusal, not from a guess.

| defect | windows | how it announced itself | disposition |
|---|---|---|---|
| month-final Sunday | `august_2025`, `november_2025` | `canonical_source_plan_invalid`; 21 unresolved symbol-days, **all** `2025-11-30`, all `selected_day_source_below_session_scaled_floor` | **fixed** — window ends on the preceding Saturday |
| no M15 lead-in | `june_2025` | `prepared_timestamp_invalid:$.symbols[UKOIL_cash].asof_row.decision_max_source_time_utc_by_timeframe.H1` | **fixed** — start moved to 2025-06-03 |
| upstream export gap | `july_2025` | `canonical_source_plan_invalid`; 2 unresolved symbol-days, `2025-07-26`, BTCUSD + ETHUSD only | **NOT_EVALUABLE** — deleted, not registered |
| supervisor mis-ordering | (mine) | no failure; caught by inspection | **fixed** — see §7 item 7 |

**Month-final Sunday.** A UTC Sunday holds only the 21:00–24:00 week-open
sliver. The engine folds such a fragment into its *enclosing* broker day via
`lane_authority_rebind`, which works for every mid-month Sunday — January bound
with three of them — because the enclosing Monday sits inside the window's own
M1 family. For a month-**final** Sunday the enclosing Monday is in the next
month, whose M1 family the manifest does not bind. The day cannot rebind, falls
below the session-scaled floor, and the plan returns `valid: False`.

> **This explains a pre-existing anomaly nobody had a reason to look at.**
> `may_2026` is the **one** CJ window with no bound canonical source-plan
> digest, and `2026-05-31` is the **one** CJ window-end that falls on a Sunday.
> Same defect, latent since CJ. Untouched here — it is not this session's to
> repair, and it is now written down.

**No M15 lead-in.** `UKOIL_cash` has the latest M15 start in the entire archive
(`2025-06-02T00:00:00Z`). H1 is derived from M15 on this path
(`use_native_h1=False`), so a symbol with no M15 history before the window's
first decision has no H1 as-of stamp to write. One day of lead-in is the
cheapest fix that gives every symbol a complete prior H1.

**The upstream export gap is real and is not repaired.** BTCUSD and ETHUSD carry
**2** M1 rows on 2025-07-26 and **175** on 07-27, against **1,070–1,430** on
every other July weekend — measured on all four July weekends, so this is one
degraded broker weekend in the FTMO export, not systemic weekend sparsity. Only
the two weekend-trading symbols see it, which is why the other 22 pass. It
cannot be repaired from available inputs. Per the standing rule, a window with
partial coverage is NOT_EVALUABLE and is **deleted rather than registered** —
`july_2025` therefore does not exist in the registry.

A 25-day `2025-07-01..2025-07-25` July is available and was deliberately **not**
built. Trimming one unusable day off a boundary (August, November, June) keeps a
window recognisably a month; silently trimming six days out of the middle of the
calendar produces a window that would be compared against 30-day months without
anyone noticing the difference. That is an owner's call, not a builder's.

---

## 3. Method

Three steps per window, strictly serial, rule-2 fenced after every one of them
(`build_window.sh`):

1. `materialize-window` — 24 M1 bar files converted through
   `broker_epoch_to_utc`; the 72 static D1/H4/M15 rows reused **by reference**
   from CJ's catalog (re-transforming them would rewrite bytes five other
   windows' manifest digests depend on); ticks sliced from the captured corpus
   where the corpus covers the window; one manifest; one registry entry.
2. `bind-source-plan` — the engine recomputes the canonical plan over the
   window's own days and the digest is persisted in the registry.
3. `build-packs` — per-day immutable prepared packs, `--encoding-workers 2`.

Steps 2 and 3 open the registry through `LaneInputRegistry`, which refuses any
registry carrying `march_window_registered: true` unless the process holds the
March one-shot (`lane_rematerialization.py:2251-2257`). That fuse now covers the
whole registry, so those two steps run with
`GTOS_MARCH_ONE_SHOT_PREREG_SHA256` set. **This reads no March day.** Every
window requested is 2025 calendar, so `authorize_window`'s blackout branch never
fires and no registry or surface-map swap occurs — which is checkable rather than
promised: a swapped map renames itself with a `+march_one_shot:` suffix, and no
receipt written by this session carries one.

---

## 4. Rule-2 fence — the five pre-existing windows

`verify_pre_existing.py` compares each pre-existing window's **whole registry
entry** plus its manifest's root digest and its manifest file's byte hash against
a baseline frozen before the first mutation, and separately checks the two
digests the brief pinned by value. It ran before the first step and after every
mutating step of every window.

It passed **every** time it was run — before the first mutation, after each of
the three steps of each window, after each `unregister-window`, and at the end.
No pre-existing window entry, manifest root digest or manifest file hash moved
at any point. The fence is `verify_pre_existing.py`; the frozen baseline is
`PRE_EXISTING_WINDOW_BASELINE.json`; each pass is stamped in `build_log.txt`
with the window and step that had just run.

The two pinned digests, unchanged throughout:

| window | canonical source-plan digest |
|---|---|
| `january_2026` | `b44b433039bf7f5372fc067f62477cdb5c8b0d2caf4202755a922a7c198be954` |
| `march_2026` | `8163172cbae28ae943ae940f3293bb2272671114e9e9bc0de3a7e04f79ffdf8e` |

Two registry-level fields **do** move, necessarily and by the same mechanism the
March extension used: `registry_root_sha256` (it is a hash over the window set,
so adding a window must change it) and `status` (`…_COMPLETE` →
`…_SOURCE_READY` while any window is `NOT_BUILT`). Neither is a per-window
quantity and neither was in scope of the fence; both are recorded here so a later
reader does not mistake them for drift.

---

## 5. Disk, and the estimate that was wrong

Machine-readable trajectory: `DISK_TRAJECTORY.json`, built from the build log's
own `free=` stamps.

| moment | free |
|---|---:|
| session start, before any recovery | **19.0 GB** |
| after gzipping 149 FA2 route ledgers (5.35 GB → 0.50 GB) | **24.0 GB** |
| during `december_2025` (a concurrent estate reclaim landed — **not this session**) | **~51 GB** |
| steady state through the seven-window run | **43–46 GB** |

**The 20 GB step from 24 to ~44 was not mine** and is recorded that way in the
JSON so this session's actual contribution — **+4.85 GB** — is not
over-credited. The disk floor never came close to binding: peak consumption was
~8 GB of packs and ~7 GB of tick sources against 43 GB of headroom.

Recovery performed first, as instructed, and confined to what the brief
sanctioned: **149 uncompressed `*.jsonl` ledgers under this worktree's completed
FA2 March/January route outputs, gzipped in place — 5.35 GB → 0.50 GB, +4.85 GB
recovered.** None had been written to in the preceding three hours. Nothing was
deleted, nothing on the exception list was touched, no `git clean` or
`git checkout` was run anywhere, and `/Users/borr/GTOSActive/repo`'s dirty
sleeve-registry file (H1) was never approached.

---

## 6. Outcome-blindness, as a checkable property

* The only tool invoked is `lane_rematerialization`'s `materialize-window`,
  `bind-source-plan` and `build-packs`. None of the three constructs a
  candidate, walks a trade or computes an economic field; `build_packs` encodes
  bars into per-day shards and `bind-source-plan` hashes a source plan.
* No `train_engine.runner` arm was launched for any 2025 window. The runner is
  the thing that decodes economics, and it was not run.
* Every receipt this session wrote carries `economic_outcomes_read: false` and
  `march_outcomes_read: false`, and the registry's own `march_outcomes_read`
  stays `false`.
* `summarize_windows.py` builds the machine receipt from registry, manifest and
  catalog **metadata only** — per-symbol coverage is the declared
  `first_utc` / `last_utc` / `row_count`, never a decoded row.
* **One qualification, stated precisely rather than glossed.** `smoke-pack` was
  run on `december_2025` as an integrity proof, and it *does* open pack shards:
  it loads the first decision window of each day and checks the pack-root hash
  and runtime compatibility. What it loads are the market **inputs** this
  session just wrote — bars, for a decision window — and its own receipt records
  `economics_run: false`. Reading back a bar you wrote is not reading an
  outcome. Nothing else in this session opened a pack shard, and no other window
  was smoke-tested.

---

## 7. What I got wrong

**1. I accepted "outcome-virgin" and it is false.** Section 2. The estate's own
ratified surface map says this exact range is the selection surface that picked
the armed sleeves, and names a route that fitted 2025-07-01 onward day-by-day. I
did not check that before starting; I checked it while waiting on a tick pass,
and it is the single most important qualification on everything built here. Had
I not checked, the next wave would have computed q-values against a "clean
out-of-sample" that is nothing of the kind.

**2. I planned the whole run around a pack-size figure that was 4× too high.**
The commission said packs run ~4–5 GB each and I built the disk plan on it —
budgeting ~16 GB, projecting a stop after three to six windows, and preparing to
drop tick materialization from the older months to fit. Measured, the nine
existing pack roots are **1.0–1.3 GB each**. The 4–5 GB figure is real but it
describes something else: `run_march_decode_event.sh`'s own comment says *"the
evidence accumulation is 4-5 GB/arm"* — that is a replay **arm**, the thing this
session deliberately never ran. I carried a number across a category boundary
without checking what it measured, which is the same error class as reading a
level as a delta. **The correct total for all seven windows is ~9 GB of packs.**

**3. My invariance assertion was written for a serial world and would have
failed under the parallelism.** It compared the post-write registry against a
snapshot taken before an hour of bar conversion, so any sibling touching the
registry in between would make the call raise *after* writing its own entry —
producing exactly the half-built window the brief says to never register. Fixed
in `93e9906b5` by taking the snapshot inside the write lock. Worth naming
because the fence *looked* strong: it asserted the right property against the
wrong baseline, and a serial run would never have shown it.

**4. I framed the tick decision as mine to make on disk budget; it was not.**
I planned to include ticks for the three most recent months and drop them if
space got tight. The exporter's own manifest says the captured archive runs
**2025-10-01T00:05:03Z → 2026-04-29T23:54:59Z**, so June–September 2025 have no
captured ticks at any budget. The real decision was to read that metadata before
spending 11.6 GB of corpus reads per window discovering it — which is what the
`_tick_capture_span` skip does, and what CJ's own `may_2026` exclusion had
already established as the pattern.

**5. A fuse-design consequence I should report rather than fix.** Once March was
registered, `LaneInputRegistry` refuses to open the registry **at all** without
`GTOS_MARCH_ONE_SHOT_PREREG_SHA256` — for every window, not just March. Verified
both ways: unarmed raises
`lane_input_registry_march_registered_without_authorization`; armed opens
normally. So every future lane session must carry the March key regardless of
what it wants, which normalises possession of the key and erodes the fuse it was
built to be. The narrower fuse that protects March just as well is to refuse
*resolving `march_2026`* without authorization rather than refusing to open the
registry. I have not changed it — a safety fuse is not mine to loosen, and the
one-line description of the alternative is more useful to the owner than a
unilateral edit.

---

## 8. Arguments the next wave uses

This is the deliverable. Every window below is registered, plan-bound and
pack-complete; the digest is its `canonical_source_plan_digest_sha256` as stored
in `LANE_INPUT_REGISTRY.json`.

**Every command needs the March key**, whatever window it asks for — see §7
item 5. Without it the registry will not open at all.

```sh
export GTOS_MARCH_ONE_SHOT_PREREG_SHA256=\
da6c72627f35179f5f43cf9c3eec20b402ba12ad60af9487ae161f76c2a13a50

REG=/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/\
phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/LANE_INPUT_REGISTRY.json

python3 -m src.research_infra.train_engine.runner \
  --arm S0R0 --purpose LANE_ITERATION \
  --lane-input-registry "$REG" \
  --window <WINDOW> \
  --lane-source-plan-digest <DIGEST>
```

| `--window` | span | days | `--lane-source-plan-digest` |
|---|---|---:|---|
| `june_2025` | 2025-06-03 → 2025-06-30 | 28 | `b2de9cb0e396beffc06bdb18e50d3b168f9848d1f48996d0eab84891da66ab2e` |
| `august_2025` | 2025-08-01 → 2025-08-30 | 30 | `e604c43af82ed4625d56d0c45e618d69ed6db46d0fb1a855930bc57b65aebe3f` |
| `september_2025` | 2025-09-01 → 2025-09-30 | 30 | `3df3c931dcdec9d29589cc079ac89db433965c7141f245cd6148669cd875ab03` |
| `october_2025` | 2025-10-01 → 2025-10-31 | 31 | `b36eb41c0d382ad9e9df5d51502d45a569b719fac591737a5a6f73a23ec32178` |
| `november_2025` | 2025-11-01 → 2025-11-29 | 29 | `b51195fed36a96ef28d5ace9da8dcc14d4be646dc01344febbe12f10f874bc62` |
| `december_2025` | 2025-12-01 → 2025-12-31 | 31 | `b63e8d9115ff8c01288ed46bdd4bd3693ad1c31b8aff4e8eea2e9d620d9696b1` |

**`july_2025` is deliberately absent.** It is NOT_EVALUABLE on a measured
upstream export gap (§2b) and is not in the registry. Asking for it will fail
with `lane_window_not_registered`, which is the correct answer.

**Three things to carry with any result computed on these windows.**

1. **They are not clean out-of-sample** (§2). All six sit inside the
   `d.year >= 2025` predicate that selected the armed sleeves; five of the six
   (July–December) also sit inside the June v4 route's day-by-day fitting range.
   June 2025 is the only one outside that second range. The guard attaches the
   VAL `used_once_disclosure` automatically, so it will be on the receipts —
   read it.
2. **Three windows are not whole calendar months.** June starts on the 3rd,
   August ends on the 30th, November ends on the 29th, each for a measured
   reason in §2b. Any per-month aggregate must divide by the day counts above,
   not by 30/31.
3. **Tick coverage is split and it is not a defect.** October, November and
   December carry the same four ordered-tick symbols as January–April
   (`tick_gap_count` 20). June, August and September carry none, because the
   captured archive begins 2025-10-01 — recorded as
   `captured_tick_archive_begins_after_window`, not as missing symbols. This is
   the same shape `may_2026` has carried since CJ.

**6. I asserted a Sunday explanation before I had checked every window against
it, and July immediately falsified it.** After November and August failed I had
the month-final-Sunday mechanism measured and correct — and July then failed
too, on a **Thursday** month-end. The Sunday story was right about the windows
it described and simply did not cover July, whose defect is an unrelated
upstream export gap. The cost was small because I measured July rather than
assuming it was more of the same, but the order was wrong: I generalised from
two cases and got a third that did not fit, one failure later. Four windows
failed and they failed for four different reasons; that is the fact to carry,
not any single tidy mechanism.

**7. My own concurrency supervisor had an inverted sort, and the assumption
behind it was the interesting part.** To cap concurrent pack builds I ordered
processes "oldest first" by PID ascending. macOS PIDs wrap at ~99,999 and had
wrapped mid-run: `september` (pid 89956) started 23 minutes **before** `october`
(pid 19397). So the cap parked the most-advanced build — precisely the one most
likely to be holding the registry flock at `_register_pack_roots`, i.e. exactly
the deadlock the oldest-first rule existed to prevent. No deadlock occurred (I
checked both survivors were still advancing before changing anything), but the
guard was inverted for about eight minutes. Fixed by ordering on `ps -o etime`.
"PID order is start order" is true almost always, which is what makes it worth
writing down.

**8. I lost a completed pack build to my own process management.** `october`'s
build-packs was killed mid-run when the harness stopped the background task that
owned its process group — 29 minutes of work, and it left `october` registered
with 0 pack roots and 1.1 GB of partial packs, the exact partial-window state
the rules forbid. Recovered by deleting the partial packs and re-running step 3
only (its sources and plan digest were intact and did not need rebuilding). The
lesson is mechanical: work that must outlive a tool call has to be detached from
a **foreground** call, not wrapped in a tracked background task. The drivers
launched that way survived the same event untouched.
