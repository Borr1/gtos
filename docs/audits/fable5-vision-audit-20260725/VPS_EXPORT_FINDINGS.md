# VPS export — findings that change the plan

**2026-07-26.** A read-only export session on the Windows VPS (per `VPS_EXPORT_PROMPT.md`) transferred
4,640 MB / 29,818 files over host-mesh. **Manifest verification on this side: 29,784 of 29,784 rows,
0 mismatches, 0 missing** [MEASURED — `/Users/borr/GTOSActive/vps-export-20260725/verify_export.py`].

Landed at `/Users/borr/GTOSActive/vps-export-20260725/extracted/` (local disk, not iCloud, per
`docs/STORAGE_AND_REMOTES.md:11-12`). Credentials are segregated in the export's own
`SECRETS_DO_NOT_COMMIT` tree and must never enter this repo.

**Verification note for anyone re-running it.** My verifier reported false failures **twice** before it
was right: first by appending `.gz` to paths that already carried it, then by trusting the file suffix
instead of the manifest's `gzipped_in_export` flag — some sources were **already gzipped on the VPS**
(rotated logs), and for those the manifest hashes the compressed bytes as-found. 61 false mismatches.
The export was correct throughout. The lesson is the one this programme keeps relearning: the tool that
checks the evidence needs checking too.

---

## V1 — THE HALT DOES NOT EXIST [MEASURED]

**No `*.flag` file exists anywhere in either tree on the VPS.** Not
`pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag`, not `pipeline_state/RESEARCH_RUNTIME_HALT.flag`, not
`knowledge_base/meta/AUTOSTART_DISABLED.flag`, and **not either `ULTIMATE_BOOK_KILL_*.flag` path that
`run_book.py` is actively watching**. The only halt artifact on the machine is
`RESEARCH_RUNTIME_HALT.flag.archived_2026-05-28_vnext_activation` — renamed out of the way on
2026-05-18.

Meanwhile, at the moment of capture: the `GTOS_W7_BookSupervisor` task is **Running** (PID 3676, clean
5-minute single-instance cadence), both book workers healthy, both MT5 terminals connected, monitor /
companion / advisory daemons up, and **`trade_allowed: true` on both terminals**.

**Defect: the safety control has no redundancy.** Defence in depth was supposed to come from the flag
files *plus* the config gate. The flag layer is absent, so protection now rests on a single
configuration value with nothing behind it — a bad merge, a hand-edit or a stale overlay would remove it
with no second check. That is the finding: a reliability defect in a safety mechanism, on a system the
owner has deliberately kept out of the market.

**What this does to the record.** F2 concluded the flag mechanism could not protect a *fresh clone* and
that the halt "is real on the VPS filesystem, and that is unverifiable from here." Both halves are now
wrong: it is verifiable, and it is not real. Every statement in `CLAUDE.md`, in both audits, and in
`GATE_G0_RECEIPT.md` describing GTOS as "hard-halted as broker/VPS state" was describing files that do
not exist. `CLAUDE.md` and `AGENTS.md` §4 are corrected.

**What it does to the plan.** Phase 0's activation token was built for exactly this and is **on
mainline only**. Porting it to the VPS is now the highest-value deployment item in the programme —
ahead of Phase 7, where the plan currently places it. Note the token cannot be "installed" as a brake
the way a flag can: it is fail-closed by construction, so an un-tokened VPS simply stops being able to
open exposure, while risk-reducing requests keep working.

**The right repair is redundancy that cannot be removed by accident, not another flag.** The flag layer
is exactly what failed: it was renamed during an unrelated operation on 2026-05-18 and nobody noticed
for two months. The activation token is fail-closed by construction — its *absence* denies — so it
cannot be silently disabled the way a present-file check can.

---

## V2 — F21 refuted, and the truth is worse than "empty" [MEASURED]

`broker_order_lifecycle_capture_v4.jsonl` has **594 rows**, not zero. The second audit's F21 —
"has never captured a row anywhere" — is **REFUTED**.

But every row captures the **request side only**: `order_result` absent, deal-cost reconciliation
entirely null. It records intent and never a fill.

**Consequence:** it is unusable for execution-cost calibration in its present form. R28 named it as the
natural broker-truth source and Phase 6 leans on it. That is now a **build item, not a data pull** —
the channel must be repaired to capture the result side before it calibrates anything.

---

## V3 — Three execution ledgers died on 2026-07-02 and nobody noticed for 23 days [MEASURED]

The learning loop never stopped: **99,112 runtime-learning packets across 38 unbroken days**
(2026-06-18 → present, still writing). Live 2,100–9,570/day; shadow ~600–870/day.

But `execution_manager_v4_decisions`, `broker_order_lifecycle_capture_v4` and `slippage_runtime` have
written **nothing for 23 days**. The exporting session's phrasing is the right one: *"You are
accumulating volume, not execution evidence."*

**This breaks a stated premise of Phase 6.** `FULL_VISION_PLAN.md` says the VPS "has been in shadow
mode continuously since 2026-07-02… weeks of W7-side forward-shadow data already exist before this
phase formally begins," and Gate G6 says to "count what exists, don't restart a clock." What exists is
candidate/packet volume. The execution evidence the cost calibration needs stopped on the day the
shadow switch was thrown. Per-day / per-namespace breakdown in the export's `28_intelligence_timeline/`.

---

## V4 — 18 of 19 shared symbols have differing contract specs [MEASURED]

`trade_contract_size` differs on **every index CFD and ETHUSD**; JP225 differs in `digits`, `point` and
`trade_tick_size`; `currency_base` differs on three symbols. Field-by-field in the export's
`09_mt5_api/BROKER_SYMBOL_SPEC_COMPARISON.json`.

This gives the **FTMO-vs-redacted_account asymmetry on identical signals** (F1's owner-decision update, and
Gate G1b's fourth attribution axis) a concrete mechanism rather than a hypothesis. It also means any
cross-broker comparison assuming a shared contract size is wrong for the indices — which is a stronger
statement than `CLAUDE.md`'s existing note that the two *profiles* disagree on NAS100 (2×) and
US30_cash (0.5×). The profiles disagree **and so do the brokers**.

---

## V5 — Broker truth for all three accounts [MEASURED]

| | FTMO (account 1) | redacted_account |
|---|---:|---:|
| Balance = Equity | **107,879.56** | **96,229.28** |
| Deals / range | 269 · 2026-06-01 → 07-03 | 362 · **2026-04-26** → 07-02 |
| Commission / swap | −1,078.78 / −363.08 | −1,345.20 / −824.88 |
| **Net since inception** | **+7,879.56** | **−3,770.72** |

Both reconcile exactly to balance; **zero open positions** on either side. This is the first
authoritative broker record the analysis side has ever had, and it is the ground truth every
reconciliation claim in Phases 1, 6 and 7 should be checked against.

**Trap:** redacted_account's opening 100k deposit is **deal type 4, not type 2**. Any deal-type filter written
against FTMO's shape silently misclassifies it.

---

## V6 — Operational observations, stated not fixed

- **`TaskScheduler/Operational` log is disabled**, so "did the supervisor fire on date X" is
  unanswerable from this machine and always was.
- **`.git` is 60.9 GB, of which 60.0 GB is `.git/lfs`** against 845 MB of real objects — the VPS disk
  pressure is almost entirely dead LFS cache.
- **649 files in the packet worktree are LFS pointer stubs, not content** (all `data/ticks/*.parquet`).
  The main repo's data is real.
- `daily_pnl.json` frozen at 07-02; `LIVE_STATE.md` stale (regenerating writes to the tree, so it was
  correctly left alone).
- The packet directory is a **linked git worktree**, not a second clone — it shares `.git`.

## Two things asked for that did not land, and their status

- **The third account (FTMO #2, 100k).** Only two terminals exist on the VPS — `C:\MT5\FTMO` and
  `C:\MT5\redacted_account`. **Not a gap:** the owner confirmed 2026-07-26 that it is a fresh, unused
  account that was never part of the live system. Worth noting for Phase 7 only in that standing it up
  is a deployment step, not an existing capability. The audit's ≈304.1 k three-account total is
  arithmetic, not three live surfaces.
- **The market-data depth probe** (`VPS_EXPORT_PROMPT.md` §5). Bulk market data was correctly excluded,
  but the *inventory* — per-symbol, per-broker `copy_rates_range` / `copy_ticks_range` depth — did not
  run. **So "does FTMO serve ticks deeper than 2025-10?" is still unknown, for the second time**
  (the earlier probes were iCloud-evicted). Queued in `VPS_FOLLOWUP_PROMPT.md`.

  Sizing, measured rather than assumed: ordered tick truth is 11.8 GB for 4 symbols × 7 months, i.e.
  **≈0.42 GB per symbol-month** in export format. A full 2-year × 24-symbol pull ≈ **242 GB** (the
  plan's ~290 GB is the right magnitude); the four B7.5 campaign windows alone ≈ **40 GB**. This Mac
  has **41 GiB free on a 91 %-full disk**, so storage — not bandwidth — is the binding constraint, and
  the VPS's own 60 GB of dead LFS cache is the cheaper reclaim. MT5's cache on the VPS is only 3.3 GB
  total (390 MB of it `.tkc`), which is what the terminal downloaded, not what the server holds —
  hence the probe. **Ticks are a Phase 5 concern; nothing before it needs them.**

## Deliberately not transferred

Recorded with source SHA-256 in the export's `EXCLUDED_FROM_TRANSFER.jsonl` so a second pass is
verifiable: 18 bulk pre-live research ledgers (6.21 GB — documents kept, data dropped),
`research/science_program_2026_05` (31.7 GB), the LFS store, and all tick/bar market data. The export's
`99_inventory/` lists every file on both trees with size and mtime, so a follow-up pull can be sized
exactly.
