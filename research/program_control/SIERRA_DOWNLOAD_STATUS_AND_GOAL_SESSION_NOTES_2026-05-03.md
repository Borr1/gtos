# Sierra Download Status And Goal Session Notes - 2026-05-03

Status: first-wave download complete
Scope: Sierra Chart data prep for expanded OOS / orderflow research
Promotion posture: `NO_PROMOTION_VERDICT`

## Snapshot

Captured from local filesystem inspection on 2026-05-03 at about 15:24 Malaysia time while Sierra Chart was open and downloading.

- Sierra process: `SierraChart_64` running.
- Main Sierra data folder: `C:\SierraChart\Data`.
- Market depth folder: `C:\SierraChart\Data\MarketDepthData`.
- `MarketDepthData` contained `175` `.depth` files totaling about `12.298 GB`.
- `C:\SierraChart\Data` was still receiving writes; latest observed depth write was `MNQM26-CME.2026-04-13.depth` at `2026-05-03 15:23:28`.
- Local free space after Claude worktree cleanup and Sierra growth was about `52.75 GB` on `C:\`.

## Active Download Evidence

Depth backfill was still active. The depth folder had grown materially during the setup window, and recent writes were concentrated in `MNQM26-CME`.

Observed depth inventory by symbol:

| Symbol | Files | Approx GB | Note |
|---|---:|---:|---|
| `MNQM26-CME` | 11 | 4.805 | Active download at snapshot time. |
| `MYMM26-CBOT` | 31 | 2.394 | Substantial depth backfill present. |
| `GCM26-COMEX` | 31 | 2.196 | Substantial depth backfill present. |
| `6EM26-CME` | 31 | 1.214 | Substantial depth backfill present. |
| `6JM26-CME` | 31 | 0.903 | Substantial depth backfill present. |
| `6BM26-CME` | 31 | 0.731 | Substantial depth backfill present. |
| `ESM26-CME` | 4 | 0.055 | Partial/minimal at snapshot time. |
| `NQM26-CME` | 3 | ~0 | Stub/minimal at snapshot time. |
| `ZNM26-CBOT` | 1 | ~0 | Stub/minimal at snapshot time. |
| `CLM26-NYMEX` | 1 | ~0 | Stub/minimal at snapshot time. |

Important interpretation: symbols with stub/minimal depth at this snapshot should not be treated as failed or unavailable yet. Sierra was still downloading sequentially.

## Fresh Goal Instructions

Before running expanded OOS or orderflow replay that depends on Sierra files:

1. Re-check `C:\SierraChart\Data\MarketDepthData` and confirm no `.depth` files have been modified for at least `10` minutes, or explicitly record that Sierra is still downloading.
2. Inventory `.scid` and `.depth` by symbol, file count, total size, latest write time, and date coverage.
3. Treat `.scid` availability and `.depth` availability separately. Intraday replay can proceed from `.scid`; heatmap/resting-liquidity research requires `.depth`.
4. Do not classify `NQM26-CME`, `ESM26-CME`, `ZNM26-CBOT`, or `CLM26-NYMEX` as missing/failed from this snapshot alone; they were incomplete while download was in progress.
5. Use exact active-contract symbols for `.depth` research. Continuous futures are useful for broad price-history context, but old continuous-contract depth is not equivalent to exact-contract depth.
6. Monitor disk. If free space falls below about `20 GB`, pause broad Sierra downloads and preserve only core liquid-contract depth needed for the next registered research questions.

## Recommended Completion Check

Run a read-only inventory similar to:

```powershell
$files = Get-ChildItem -LiteralPath 'C:\SierraChart\Data\MarketDepthData' -Filter '*.depth'
$files | Group-Object { ($_.BaseName -replace '\.\d{4}-\d{2}-\d{2}$','') } |
  ForEach-Object {
    $sum = ($_.Group | Measure-Object Length -Sum).Sum
    $latest = ($_.Group | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime
    [PSCustomObject]@{
      Symbol = $_.Name
      Files = $_.Count
      GB = [math]::Round($sum / 1GB, 3)
      Latest = $latest
    }
  } | Sort-Object GB -Descending | Format-Table -AutoSize
```

Then write the final inventory into the expanded OOS source map before opening outcome/replay slices.

## Follow-Up Inventory - 18:20 Malaysia Time

Captured from local filesystem inspection on 2026-05-03 at about 18:20 Malaysia time.

- Sierra process: `SierraChart_64` still running.
- Main data folder: `C:\SierraChart\Data`.
- Market depth folder: `C:\SierraChart\Data\MarketDepthData`.
- Depth folder total: `377` `.depth` files, about `42.202 GB`.
- Free disk on `C:\`: about `46.35 GB`.
- A 30-second depth-file write sample showed `NO_CHANGES_30S`.

Interpretation: Sierra was not actively growing files during the sample. The first-wave data is usable enough for the fresh research session, but it is not perfectly complete.

### Historical Intraday `.scid`

The recommended first-wave historical symbols are present as `.scid` files:

- `6AM26-CME`, `6BM26-CME`, `6CM26-CME`, `6EM26-CME`, `6JM26-CME`, `6SM26-CME`
- `NQM26-CME`, `MNQM26-CME`, `YMM26-CBOT`, `MYMM26-CBOT`
- `ESM26-CME`, `MESM26-CME`, `RTYM26-CME`, `M2KM26-CME`
- `GCM26-COMEX`, `MGCM26-COMEX`, `SIM26-COMEX`, `SILM26-COMEX`
- `CLM26-NYMEX`, `MCLM26-NYMEX`, `ZNM26-CBOT`, `ZBM26-CBOT`
- `VXM26-CFE`, `VXMM26-CFE`

Thin/sparse `.scid` symbols:

| Symbol | Size | Parser range | Records | Interpretation |
|---|---:|---|---:|---|
| `SIM26-COMEX` | `0.459 MB` | `2025-11-03` to `2026-05-01` | `12,028` | Present but sparse/thin. |
| `SILM26-COMEX` | `0.199 MB` | `2026-03-31` to `2026-05-01` | `5,208` | Present but sparse/thin. |
| `VXMM26-CFE` | `0.163 MB` | `2025-12-23` to `2026-05-01` | `4,278` | Present but sparse/thin. |

These are not missing, but future research should treat them as sparse-market or symbol-quality warnings rather than full liquid history.

### Forward Depth Subset

Depth is strong for most of the recommended forward subset:

| Symbol | Files | Approx MB | Status |
|---|---:|---:|---|
| `MNQM26-CME` | `31` | `17,151.8` | Present |
| `YMM26-CBOT` | `31` | `1,765.5` | Present |
| `MYMM26-CBOT` | `31` | `2,451.7` | Present |
| `GCM26-COMEX` | `31` | `2,249.0` | Present |
| `MGCM26-COMEX` | `31` | `3,639.6` | Present |
| `SIM26-COMEX` | `31` | `846.1` | Present |
| `SILM26-COMEX` | `31` | `1,009.5` | Present |
| `6JM26-CME` | `31` | `925.1` | Present |
| `6BM26-CME` | `31` | `748.7` | Present |
| `6EM26-CME` | `31` | `1,242.9` | Present |
| `ESM26-CME` | `31` | `5,800.8` | Present |
| `MESM26-CME` | `31` | `5,384.6` | Present |

Depth gaps/stubs:

| Symbol | Files | Approx MB | Status |
|---|---:|---:|---|
| `NQM26-CME` | `3` | `<1` | Stub/minimal |
| `CLM26-NYMEX` | `1` | `<1` | Stub/minimal |
| `ZNM26-CBOT` | `1` | `<1` | Stub/minimal |

The `2026-05-03` depth files for `NQM26-CME`, `CLM26-NYMEX`, and `ZNM26-CBOT` were parser-valid but contained only `CLEAR_BOOK` records and `0` non-empty batches. This is expected for Sunday/closed-market records, but the absence of meaningful older depth for `CLM26-NYMEX` and `ZNM26-CBOT`, and only tiny files for `NQM26-CME`, means those three should be marked incomplete for depth/heatmap research until a later active-session/backfill check proves otherwise.

### Active-Session Depth Sanity Sample

Large weekday files were sampled with a lightweight parser because the full parser is too slow for hundreds-of-MB to GB files. The first `200,000` records of selected `2026-04-29` files contained non-clear book updates:

| Symbol/date | File size | Records | Sample verdict |
|---|---:|---:|---|
| `MNQM26-CME.2026-04-29.depth` | `914.1 MB` | `39,936,697` | Non-clear updates present |
| `ESM26-CME.2026-04-29.depth` | `282.7 MB` | `12,352,369` | Non-clear updates present |
| `GCM26-COMEX.2026-04-29.depth` | `134.6 MB` | `5,879,070` | Non-clear updates present |
| `6EM26-CME.2026-04-29.depth` | `57.6 MB` | `2,516,538` | Non-clear updates present |
| `SIM26-COMEX.2026-04-29.depth` | `44.6 MB` | `1,947,927` | Non-clear updates present |

This supports using the present depth files for research. It is still not a promotion claim and does not prove Databento parity, broker lead/lag, or trading value.

### Updated Fresh-Session Instruction

The fresh expanded-OOS/orderflow session can proceed with Sierra data, but should mark data coverage precisely:

1. Historical intraday first wave: mostly ready.
2. Sparse historical warnings: `SIM26-COMEX`, `SILM26-COMEX`, `VXMM26-CFE`.
3. Depth ready subset: `MNQM26-CME`, `YMM26-CBOT`, `MYMM26-CBOT`, `GCM26-COMEX`, `MGCM26-COMEX`, `SIM26-COMEX`, `SILM26-COMEX`, `6JM26-CME`, `6BM26-CME`, `6EM26-CME`, `ESM26-CME`, `MESM26-CME`.
4. Depth incomplete/stub subset: `NQM26-CME`, `CLM26-NYMEX`, `ZNM26-CBOT`.
5. Do not discard the whole Sierra setup because of those gaps. Use the ready subset now and queue the three incomplete depth symbols for active-session/backfill follow-up.

## Follow-Up Inventory - 20:50 Malaysia Time

Captured from local filesystem inspection on 2026-05-03 at about 20:50 Malaysia time after the owner manually triggered additional historical depth downloads.

- Depth folder total: `465` `.depth` files, about `59.701 GB`.
- A 30-second depth-file write sample showed `NO_CHANGES_30S`.
- Free disk on `C:\`: about `38.79 GB`.
- The prior depth gaps for `NQM26-CME`, `CLM26-NYMEX`, and `ZNM26-CBOT` are resolved for the 30-day first-wave window.

Updated depth inventory for the core forward subset:

| Symbol | Files | Approx MB | Date coverage | Status |
|---|---:|---:|---|---|
| `NQM26-CME` | `31` | `10,491.103` | `2026-04-03` to `2026-05-03` | Present |
| `MNQM26-CME` | `31` | `17,151.836` | `2026-04-03` to `2026-05-03` | Present |
| `YMM26-CBOT` | `31` | `1,765.478` | `2026-04-03` to `2026-05-03` | Present |
| `MYMM26-CBOT` | `31` | `2,451.691` | `2026-04-03` to `2026-05-03` | Present |
| `GCM26-COMEX` | `31` | `2,249.025` | `2026-04-03` to `2026-05-03` | Present |
| `MGCM26-COMEX` | `31` | `3,639.616` | `2026-04-03` to `2026-05-03` | Present |
| `SIM26-COMEX` | `31` | `846.095` | `2026-04-03` to `2026-05-03` | Present |
| `SILM26-COMEX` | `31` | `1,009.488` | `2026-04-03` to `2026-05-03` | Present |
| `6JM26-CME` | `31` | `925.057` | `2026-04-03` to `2026-05-03` | Present |
| `6BM26-CME` | `31` | `748.705` | `2026-04-03` to `2026-05-03` | Present |
| `6EM26-CME` | `31` | `1,242.881` | `2026-04-03` to `2026-05-03` | Present |
| `ESM26-CME` | `31` | `5,800.825` | `2026-04-03` to `2026-05-03` | Present |
| `MESM26-CME` | `31` | `5,384.624` | `2026-04-03` to `2026-05-03` | Present |
| `CLM26-NYMEX` | `31` | `4,029.823` | `2026-04-03` to `2026-05-03` | Present |
| `ZNM26-CBOT` | `31` | `3,397.575` | `2026-04-03` to `2026-05-03` | Present |

Lightweight active-session sanity checks confirmed the previously missing symbols contain real non-clear book updates on `2026-04-29`:

| Symbol/date | File size | Records | Sample verdict |
|---|---:|---:|---|
| `NQM26-CME.2026-04-29.depth` | `586.6 MB` | `25,629,817` | Non-clear updates present |
| `CLM26-NYMEX.2026-04-29.depth` | `180.0 MB` | `7,862,787` | Non-clear updates present |
| `ZNM26-CBOT.2026-04-29.depth` | `185.0 MB` | `8,083,203` | Non-clear updates present |

Updated interpretation:

1. The recommended first-wave depth set is now ready for the fresh expanded-OOS/orderflow goal session.
2. `2026-05-03` files may remain small Sunday/closed-market files; that is not a blocker because older active-session files from the 30-day window are present and non-empty.
3. Historical intraday `.scid` still has sparse/thin warnings for `SIM26-COMEX`, `SILM26-COMEX`, and `VXMM26-CFE`. These are present files, not missing files, but research should treat them as sparse-symbol warnings.
4. No first-wave Sierra depth symbol remains missing at this checkpoint.
