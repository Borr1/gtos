# VPS follow-up — depth probe and disk reclaim

Short second prompt for the **same** VPS session, still warm from the export. Copy between the markers.

---

--- BEGIN ---

Your export verified clean on the Mac: **29,784 of 29,784 manifest rows, 0 mismatches, 0 missing.**
(The two "failures" I hit first were both bugs in my verifier — I appended `.gz` to paths that already
had it, then trusted the file suffix instead of your `gzipped_in_export` flag, which broke the 61 files
that were already gzipped at source. Your manifest was right. Also: good catch on the BOM.)

**You can clear `C:\gtos_export_20260725T230714Z\` whenever you like.**

Three small things left. Same rules as before — **read-only, change nothing, don't restart anything,
don't touch flags or git.**

## 1. The market-data depth probe (the one thing from §5 that didn't land)

Metadata only, **no bulk export** — the Mac has 41 GiB free on a 91%-full disk, so a pull is not
happening until it is sized. This probe is what sizes it.

For each of the 24 traded symbols, on **each** broker, report:

- earliest and latest timestamp `copy_rates_range` actually returns, for M1, M15, H4, D1;
- earliest and latest `copy_ticks_range` returns, and whether ticks are **real** (`COPY_TICKS_ALL`
  with genuine bid/ask flags) or **synthesised** from bars;
- approximate tick rows per month, sampled — one or two representative months is plenty, do not walk
  the whole history.

**The question this exists to answer: does FTMO serve ticks deeper than 2025-10?** Current ordered-tick
truth covers 4 of 24 symbols × 7 months and nobody knows whether more is even obtainable. It has been
unknown twice now because the earlier probes were lost, so please land the numbers this time.

Probe with small windows. One JSON is the whole deliverable.

## 2. Size the LFS reclaim precisely

You found `.git` at 60.9 GB with 60.0 GB in `.git/lfs` against 845 MB of real objects. Before anything
is deleted I want the decision to be arithmetic rather than vibes:

- exact reclaimable bytes, and how you measured them;
- whether **anything on that box still reads from the LFS store** — the packet worktree has 649 pointer
  stubs, so say plainly whether hydrating those would need the cache or a re-fetch;
- what would break if it were cleared, and whether that is recoverable from the remote.

**Report it, do not delete it.** Disk on that machine is not urgent; being wrong about it would be.

## 3. Anything you noticed but did not report

Your last report's most useful section was the one I hadn't asked for — the dead execution ledgers, the
594-row capture channel that only records the request side, the contract-spec divergence. If there is
more of that, this is the moment.

Send the probe JSON and the LFS note over host-mesh. That is all.

--- END ---

---

## Why this is worth running (context for the Mac side, not the prompt)

- Ticks are a **Phase 5** concern; Phase 1 needs none, Phase 2 runs on sealed January's own byte copies,
  and Phase 6's cost calibration uses `slippage.jsonl` (192 fills) and `pending_limit_lifecycle.jsonl`
  (877 rows), not ticks. So this is not urgent — it is cheap insurance against a Phase-5 guess.
- Measured basis for the size question: 11.8 GB for 4 symbols × 7 months ≈ **0.42 GB per symbol-month**
  in export format. Full 2-yr × 24-sym ≈ 242 GB (the audit's ~290 GB is the right magnitude); the four
  B7.5 campaign windows only ≈ 40 GB. Against **41 GiB free**, even the small number needs the disk
  problem solved first.
- MT5's own cache on the VPS is **3.3 GB total, only 390 MB of it `.tkc` tick cache** — that is what the
  terminal has downloaded, not what the server holds, which is precisely why the probe is the only way
  to know.
