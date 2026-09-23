# Pressure Test — Extended Kill Zone Implementation

**Date:** 2026-04-03
**Status:** COMPLETE
**Tested:** Extended KZ implementation across 6 files

---

## Results Summary

```
=== PRESSURE TEST RESULTS ===
Test 1  (Gold Regression):       [PASS] — London 10/day unchanged, NY 16/day (extended)
Test 2  (GBPUSD London Count):   [PASS] — 20 London candles/day (was 10)
Test 3  (NAS100/XAGUSD NY):      [PASS*] — Config verified; data not in historical/ dir (pre-existing)
Test 4  (Prompt KZ Display):     [PASS] — All instruments show correct KZ times
Test 5  (Boundary Candles):      [PASS] — 09:30/12:00/15:30/17:00 boundaries all correct
Test 6  (Session Timeout):       [PASS] — Timeout derived from config KZ end, not hardcoded
Test 7  (Session Memory):        [PASS] — Memory spans full extended window, no reset at old boundary
Test 8  (Extended Trade):        [PASS] — 10 extended candles (09:45-12:00) confirmed in GBPUSD batch
Test 9  (API Cost):              [PASS] — Cost increase proportional to candle count increase
Test 10 (No Hardcoded Times):    [PASS] — Zero hardcoded times in critical paths
Test 11 (All Extensions):       [PASS] — All 5 instruments have correct KZ times

Errors found: 0
Warnings: 1 (backward compatibility note)
Impact: None — ready for batch testing
```

---

## Test 1: Gold Regression — PASS

### With `--symbol XAUUSD` (new behavior)
```
Date range: 2025-03-01 to 2025-03-07 (5 weekdays, 2 pass pre-screen)
London: 20 candles = 10/day × 2 days — UNCHANGED
NY:     32 candles = 16/day × 2 days — EXTENDED (was 10/day)
Total:  52 candles (was 40)
```

### Without `--symbol` (backward compatibility)
```
London: 20 candles = 10/day × 2 days — UNCHANGED
NY:     20 candles = 10/day × 2 days — UNCHANGED (base config used)
Total:  40 candles — IDENTICAL to before
```

**Critical finding:** When `--symbol` is not passed, the base config is used (no overrides applied). This means ALL existing batch runs that don't pass `--symbol XAUUSD` will use the original KZ times. This is correct backward-compatible behavior — extensions are opt-in via `--symbol`.

**Warning:** Users must pass `--symbol XAUUSD` to get the NY extension. Running without `--symbol` defaults to the conservative base config. This is by design but worth documenting.

---

## Test 2: GBPUSD Extended London — PASS

```
Date range: 2025-03-01 to 2025-03-07 (5 weekdays, 5 pass pre-screen)
London: 100 candles = 20/day × 5 days — EXTENDED (was 10/day)
NY:      50 candles = 10/day × 5 days — UNCHANGED
Total:  150 candles (was 100)
```

Detailed candle listing for 2025-03-03 confirmed:
- 10 core candles: 07:15, 07:30, ... 09:30 (unchanged)
- 10 extended candles: 09:45, 10:00, 10:15, 10:30, 10:45, 11:00, 11:15, 11:30, 11:45, 12:00 (new)
- All labeled as `london` KZ (not a separate window)
- Custom IDs: `2025-03-03_london_0945`, `2025-03-03_london_1000`, etc.

---

## Test 3: NAS100/XAGUSD — PASS* (config verified, data layout pre-existing)

Config merge verified programmatically for all 5 instruments:

| Instrument | London End | NY End | Status |
|-----------|-----------|--------|--------|
| XAUUSD | 09:30 | 17:00 | OK |
| GBPUSD | 12:00 | 15:30 | OK |
| EURUSD | 12:00 | 15:30 | OK |
| NAS100 | 09:30 | 17:00 | OK |
| XAGUSD | 09:30 | 17:00 | OK |

NAS100/XAGUSD/EURUSD CSVs exist in `data/` but not `data/historical/`. The batch script reads from `data/historical/`. This is a pre-existing data layout issue unrelated to the KZ extension. To run batch tests on these instruments, symlink or copy data to `data/historical/`.

---

## Test 4: Prompt KZ Display — PASS

| Instrument | Prompt London | Prompt NY |
|-----------|-------------|---------|
| XAUUSD | `07:00-09:30 UTC` | `13:00-17:00 UTC` |
| GBPUSD | `07:00-12:00 UTC` | `13:00-15:30 UTC` |
| EURUSD | `07:00-12:00 UTC` | `13:00-15:30 UTC` |
| NAS100 | `07:00-09:30 UTC` | `13:00-17:00 UTC` |
| Default (no --symbol) | `07:00-09:30 UTC` | `13:00-15:30 UTC` |

All correctly generated from config. The AI sees the extended window times and evaluates candles within those windows.

---

## Test 5: Boundary Candles — PASS

### GBPUSD Extended London (07:00-12:00)
- First candle: 07:15 (close time)
- Last candle: 12:00 (close time)
- 09:30 (old last candle): Now middle of window — included
- 09:45 (first extended candle): Included
- 12:00 (new last candle): Included
- Count: 20 candles

### Extended NY (13:00-17:00)
- First candle: 13:15
- Last candle: 17:00
- 15:30 (old last candle): Now middle of window — included
- 15:45 (first extended candle): Included
- 17:00 (new last candle): Included
- Count: 16 candles

### Standard windows (unchanged instruments)
- London 07:00-09:30: 10 candles (07:15..09:30) — unchanged
- NY 13:00-15:30: 10 candles (13:15..15:30) — unchanged

---

## Test 6: Session Timeout — PASS

The orchestrator's `_is_after_all_kz()` method computes timeout as:
```python
ny_e = self._ny_end[0] * 60 + self._ny_end[1]
return t >= ny_e + TIMEOUT_TRAIL_MINUTES  # +120 minutes
```

Since `_ny_end` is read from config:
- XAUUSD: NY ends 17:00 → timeout at 19:00 (was 17:30 with old 15:30 end)
- GBPUSD: NY ends 15:30 → timeout at 17:30 (unchanged)
- NAS100: NY ends 17:00 → timeout at 19:00

No hardcoded timeout values. Correctly derived from config.

For the "between KZ" gap (`_is_between_kz`):
- GBPUSD: London ends 12:00, NY starts 13:00 → 1-hour gap (was 3.5h gap)
- XAUUSD: London ends 09:30, NY starts 13:00 → 3.5h gap (unchanged)

---

## Test 7: Session Memory — PASS

### Live system (orchestrator)
Session memory uses `kill_zone` string ("london"/"ny") as key. Extended candles use the SAME key as core candles. Memory from 08:00 is available to 10:30 — they're both "london".

The memory window is 6 entries per KZ. With 20 London candles instead of 10, the window will slide — only the last 6 evaluations are retained. This is correct behavior.

### Batch system
`collect_prompts` calls `pa.reset_session_cache()` once per KZ per date. All 20 London candles share the same session cache. No reset at 09:30.

---

## Test 8: Extended Trade Evaluation — PASS

Confirmed GBPUSD batch output for 2025-03-03 includes 10 extended candles:

```
2025-03-03_london_0945  time=09:45 ← EXTENDED
2025-03-03_london_1000  time=10:00 ← EXTENDED
2025-03-03_london_1015  time=10:15 ← EXTENDED
2025-03-03_london_1030  time=10:30 ← EXTENDED
2025-03-03_london_1045  time=10:45 ← EXTENDED
2025-03-03_london_1100  time=11:00 ← EXTENDED
2025-03-03_london_1115  time=11:15 ← EXTENDED
2025-03-03_london_1130  time=11:30 ← EXTENDED
2025-03-03_london_1145  time=11:45 ← EXTENDED
2025-03-03_london_1200  time=12:00 ← EXTENDED
```

Each gets a full PA prompt with MSO data current to that timestamp. The AI will evaluate these candles identically to core candles — same framework, same criteria, same safety checks.

Whether a CANDIDATE is found depends on the price action on those specific dates. A submitted batch test will determine this.

---

## Test 9: API Cost — PASS

| Config | Candles | Batch Cost | Per-Candle |
|--------|---------|-----------|-----------|
| Gold (no --symbol) | 40 | $0.39 | $0.0097 |
| Gold (--symbol XAUUSD) | 52 | $0.50 | $0.0096 |
| GBPUSD (--symbol GBPUSD) | 150 | $1.44 | $0.0096 |

Per-candle cost is stable at ~$0.0096. Cost increase is exactly proportional to candle count increase:
- XAUUSD: 52/40 = 1.30× candles → $0.50/$0.39 = 1.29× cost
- GBPUSD: 150/100 = 1.50× candles → $1.44/$0.96 ≈ 1.50× cost

---

## Test 10: No Hardcoded Times — PASS

```bash
grep -n "'09:30'\|'15:30'" scripts/batch_backtest.py | grep -v "config\|#\|yaml\|default\|get("
# (no results)

grep -n "'09:30'\|'15:30'" scripts/backtest_runner.py | grep -v "config\|#\|yaml\|default\|get("
# (no results)

grep -n "'09:30'\|'15:30'" scripts/historical_data_loader.py | grep -v "config\|#\|yaml\|default\|test"
# (no results)

grep -n "07:00.*09:30\|13:00.*15:30" scripts/batch_backtest.py | grep -v "#\|comment\|yaml"
# (no results)
```

Zero hardcoded KZ times in critical paths. The only time references remaining are:
- Default fallback values in `replay_kill_zone()` function signature (`kz_start="07:00"`, `kz_end="09:30"`)
- Module-level constants in `historical_data_loader.py` (`LONDON_OPEN_END`, `NY_OPEN_END`) used by the legacy `replay_london_open`/`replay_ny_open` functions (kept for backward compatibility)
- Config file values (correct)
- Test assertions (correct)

---

## Test 11: All Extensions Verified — PASS

Programmatic verification of all 5 instruments via `apply_instrument_overrides()`:

```
XAUUSD: London=09:30 (exp 09:30) OK, NY=17:00 (exp 17:00) OK
GBPUSD: London=12:00 (exp 12:00) OK, NY=15:30 (exp 15:30) OK
EURUSD: London=12:00 (exp 12:00) OK, NY=15:30 (exp 15:30) OK
NAS100: London=09:30 (exp 09:30) OK, NY=17:00 (exp 17:00) OK
XAGUSD: London=09:30 (exp 09:30) OK, NY=17:00 (exp 17:00) OK
```

`core_end_utc` values confirmed for extended windows:
- XAUUSD NY: core_end=15:30, end=17:00
- GBPUSD London: core_end=09:30, end=12:00

---

## Additional Finding: `apply_instrument_overrides` Fix

During implementation, discovered that the original `apply_instrument_overrides()` skipped overrides when `symbol == base_symbol` (XAUUSD). Since XAUUSD now has an `instruments.XAUUSD` override section (for the NY extension), this was fixed. The function now applies overrides for any symbol that has an entry in the `instruments` section, regardless of whether it matches the base symbol.

This fix in `src/utils/config.py` is tested and passing (465 tests).

---

## Errors Found: 0

No errors detected. All 11 tests pass.

---

## Warnings: 1

**Backward compatibility note:** Running `batch_backtest.py` without `--symbol` uses base config (no extensions). Users must explicitly pass `--symbol XAUUSD` to get the NY extension for gold. This is by design — extensions are opt-in — but existing scripts/commands that don't pass `--symbol` will silently use old KZ times.

---

## Impact

No changes needed. Implementation is ready for batch testing. Recommended next steps:

1. Copy NAS100/XAGUSD/EURUSD data to `data/historical/` for full batch testing
2. Run batch test on GBPUSD extended London: `python3 scripts/batch_backtest.py --symbol GBPUSD --start 2024-06-01 --end 2025-03-31`
3. Run batch test on XAUUSD extended NY: `python3 scripts/batch_backtest.py --symbol XAUUSD --start 2024-06-01 --end 2025-03-31`
4. Compare extended window trade rate and quality against core window baseline
