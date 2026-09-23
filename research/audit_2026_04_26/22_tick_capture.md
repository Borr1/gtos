# AUDIT 22: TICK-CAPTURE (daemon completeness)

## Code 100% complete + tested
- 58/58 tests pass

## Daemon NEVER STARTED
- `data/ticks/` empty except README

## Pipeline
daemon → parquet → tick_features (12 per M15 bar) → data_ingestion fail-open → `raw_data["tick_features"]` attached → **NOT serialized into prompt** (D.1 follow-up)

## Watchdog supervision wired
- Lines 324-384 in watchdog.ps1
- 5 per-symbol blocks

## Lee-Ready aggressor classifier
With broker flag fallback (60-80% accuracy on this broker).

## State persistence
Atomic.

## Storage budget
- 6-12 MB/day fleet
- 2-3 GB/year

## Will daemons start Monday?
YES — watchdog launches at 07:45 local, expected first parquet 1-3 min later.

## CRITICAL gap
Prompt does not consume `tick_features`.

## D.1 next-session task
~4h to wire features into prompt + canary regression.

## Status
Shadow-only Monday, full integration deferred.
