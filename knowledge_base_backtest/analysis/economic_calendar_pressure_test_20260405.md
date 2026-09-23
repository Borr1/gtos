# Economic Calendar Pressure Test Report

**Date:** 2026-04-05
**Module:** `src/utils/economic_calendar.py`
**Integration:** `src/components/orchestrator.py`
**Config:** `config/agent_config.yaml` → `economic_calendar` section

---

## Summary

```
=== ECONOMIC CALENDAR PRESSURE TEST ===
Test 1 (Calendar Data):            PASS — 31 events, 21 USD, 10 GBP
Test 2 (Blocking Logic):           PASS — before/after/clear all correct
Test 3 (Currency Filtering):       PASS — gold ignores GBP, GBPUSD sees GBP
Test 4 (Orchestrator Integration): PASS — 2 check points, loaded once at init
Test 5 (Trade Record):             PASS — BLOCKED_CALENDAR saves and loads correctly
Test 6 (Disabled Config):          PASS — disabled = never blocks, missing section = no crash
Test 7 (Edge Cases):               PASS — empty, malformed, exact time, two events
Test 8 (Regression):               PASS — 562 tests passing (13 new calendar tests)
```

**Overall: 8/8 PASS**

---

## Test 1: Calendar Data Quality

- **Total events:** 31
- **By currency:** USD=21, GBP=10
- **April 2026:** USD=14, GBP=6 (exceeds minimums of 5/3)
- **Estimated events:** 31/31 (all marked estimated) — startup warning fires correctly
- **Date format:** All valid YYYY-MM-DD HH:MM
- **Duplicates:** None found

**Note:** All 31 events are marked `estimated=true`. The system correctly logs a warning:
> "Calendar contains estimated dates — verify against real calendar (ForexFactory, Fed schedule, BOE schedule) before live trading"

---

## Test 2: Blocking Logic

Tested against US ISM Manufacturing PMI at 2026-04-01 12:30 UTC:

| Scenario | Expected | Actual | Result |
|----------|----------|--------|--------|
| 90min before event | BLOCKED | blocked=True, "in 90 minutes" | PASS |
| 3h before event | CLEAR | blocked=False | PASS |
| 15min after event | BLOCKED | blocked=True, "was 15 minutes ago" | PASS |
| 45min after event | CLEAR | blocked=False | PASS |

Pre-block window: 120 minutes (config). Post-block window: 30 minutes (config).

---

## Test 3: Currency Filtering

Tested against UK GDP (Monthly) at 2026-04-07 07:00 UTC:

| Symbol | Expected | Actual | Result |
|--------|----------|--------|--------|
| XAUUSD (gold) | NOT blocked by GBP event | blocked=False | PASS |
| GBPUSD | BLOCKED by GBP event | blocked=True, "UK GDP (Monthly) in 60 minutes" | PASS |

Currency map correctly routes:
- `XAUUSD → ["USD"]` — ignores GBP events
- `GBPUSD → ["USD", "GBP"]` — sees both

---

## Test 4: Orchestrator Integration

### Check Points (2 found — correct)

1. **Line 276:** Before API call (saves tokens)
   - Uses `datetime.now(timezone.utc)` ✓
   - Uses `self._calendar` (loaded once) ✓
   - Uses `self._symbol` for currency filtering ✓

2. **Line 408:** Before execution (safety net — event may enter window during AI eval)
   - Uses `datetime.now(timezone.utc)` ✓ (NOT `datetime.utcnow()`)
   - Uses `self._calendar` ✓
   - Uses `self._symbol` ✓
   - Saves `BLOCKED_CALENDAR` to trade record before returning ✓

### Initialization

- **Line 111:** `self._calendar = self._load_economic_calendar()` — loaded ONCE at `__init__` ✓
- **Line 1014-1028:** `_load_economic_calendar()` has try/except, returns `[]` on failure ✓
- **Line 1017:** Checks `enabled` flag, returns `[]` if disabled ✓
- **Line 49:** `load_calendar()` checks file existence, returns `[]` if missing ✓

### Fault Tolerance

- Missing file: returns `[]`, logs warning, no crash ✓
- Malformed file: outer try/except returns `[]` ✓
- Disabled config: returns `[]` at load time ✓

---

## Test 5: Trade Record Compatibility

- Created mock record with `final_outcome = "BLOCKED_CALENDAR"`
- `save_trade_record()` succeeded → `/XAUUSD/2026-04-03_ny_1200.json`
- `load_trade_record()` round-tripped correctly
- `save_trade_record` does NOT validate outcome values — any string is accepted

---

## Test 6: Disabled Config

| Scenario | Expected | Actual | Result |
|----------|----------|--------|--------|
| `enabled: false` + empty calendar | NOT blocked | blocked=False | PASS |
| Empty calendar + any time | NOT blocked | blocked=False | PASS |
| Missing `economic_calendar` section entirely | No crash | No crash (uses defaults) | PASS |

---

## Test 7: Edge Cases

| Scenario | Expected | Actual | Result |
|----------|----------|--------|--------|
| Empty CSV (headers only) | 0 events, no block | 0 events, blocked=False | PASS |
| Malformed row in CSV | Skipped, others load | 2/3 loaded, warning logged | PASS |
| Event at exact current time | Blocked, "NOW" | blocked=True, "happening NOW" | PASS |
| Two events 4h apart, test at midpoint (clear) | NOT blocked | blocked=False | PASS |
| Two events 4h apart, test 90min before second | Blocked by second | blocked=True, "Event B in 90 minutes" | PASS |

---

## Test 8: Regression

```
562 passed, 19 warnings in 51.83s
```

- All pre-existing tests pass (549+ from before)
- 13 new economic calendar tests pass
- No regressions introduced

---

## Architecture Notes

1. **`should_block_trading()` is stateless** — it does not check the `enabled` flag itself. The orchestrator handles enablement at load time by passing an empty calendar when disabled. This is clean separation of concerns.

2. **Reason string quality** — includes event name + relative timing ("NFP in 47 minutes", "FOMC was 12 minutes ago", "NFP happening NOW"). Good for logs and debugging.

3. **Known limitation documented** — module docstring explicitly states the calendar blocks NEW entries only, not existing positions. Gap risk through SL is acknowledged.

4. **All dates estimated** — the entire calendar is marked `estimated=true` because these are projected dates for April/May 2026. The warning system works correctly. Before live trading, dates should be verified against ForexFactory/Fed/BOE schedules.
