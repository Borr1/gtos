# Level 2 Candidate Verification — Implementation Record
**Date**: 2026-04-04
**Status**: Implemented and tested

---

## What Was Built

### New file: `src/components/verification.py`

A deterministic verification module with 6 checks that validate the AI's CANDIDATE output against the Market State Object (MSO) source data.

#### The 6 Checks

| # | Check Name | What It Catches | Status on Fail |
|---|-----------|----------------|----------------|
| 1 | `m15_choch_exists` | AI claims M15 CHoCH but none exists in MSO with correct direction + displacement | FAIL |
| 2 | `displacement_ratio` | M15 displacement ratio below 1.5 threshold (catches the 2024-03-01 loss) | FAIL |
| 3 | `h1_poi_exists` | AI cites H1 OB/breaker at a price where none exists in MSO (catches the 2024-03-15 loss) | FAIL |
| 4 | `ob_zone` | OB in wrong premium/discount zone for trade direction | WARN (configurable to FAIL) |
| 5 | `entry_in_ob` | Entry price placed outside the matched OB/breaker zone | FAIL |
| 6 | `sl_beyond_ob` | Stop loss not beyond OB extreme (inside the zone where it would get triggered) | FAIL |

#### Key Design Decisions

- **Check 1 accepts both CHoCH and BOS**: Some valid setups have BOS instead of CHoCH on M15. Both are accepted as long as they have displacement in the correct direction.
- **Check 3 handles both frameworks**: For `ob_retest` it checks order blocks; for `breaker_retest` it checks breaker blocks. Falls back to checking both if framework is ambiguous.
- **Check 4 is soft by default**: Zone mismatch produces WARN (doesn't block). Set `strict_zone_check: true` in config to make it FAIL.
- **Tolerance is config-driven**: `ob_price_tolerance_pct: 0.002` (0.2%) works for gold (~$6 at $3000) and forex (~2.5 pips for GBPUSD at 1.2500).

### Integration Point

Inserted into `orchestrator.py:_process_candle()` between the CANDIDATE check (line ~262) and confidence scoring (line ~274):

```python
# 6a. Level 2 verification — check AI claims against MSO
verification = verify_candidate(analysis, mso, self.config)
if not verification.passed:
    self._log_candle("REJECTED_L2", f"{verification.blocked_by}: ...", kill_zone)
    return
```

### Configuration

Added to `config/agent_config.yaml`:

```yaml
verification:
  enabled: true
  ob_price_tolerance_pct: 0.002
  strict_zone_check: false
  log_warnings: true
```

Displacement threshold is read from existing `model_a.displacement_min_ratio: 1.5`.

---

## Test Results

**24 tests in `tests/test_verification.py`**, all passing:

| Test | What It Verifies |
|------|-----------------|
| `test_all_pass` | Valid CANDIDATE + matching MSO → all 6 checks PASS |
| `test_no_m15_choch` | No M15 events → Check 1 FAIL |
| `test_choch_wrong_direction` | CHoCH in wrong direction → Check 1 FAIL |
| `test_displacement_below_threshold` | 0.4x displacement → blocked (2024-03-01 case) |
| `test_displacement_present_but_ratio_low` | 1.2x ratio → Check 2 FAIL |
| `test_no_h1_ob` | Zero unmitigated H1 OBs → Check 3 FAIL (2024-03-15 case) |
| `test_h1_ob_price_mismatch` | OB exists but far from AI's cited price → Check 3 FAIL |
| `test_ob_wrong_zone_warn` | OB in premium for LONG → Check 4 WARN (doesn't block) |
| `test_ob_wrong_zone_strict` | Same but strict mode → Check 4 FAIL |
| `test_entry_outside_ob` | Entry far from OB → Check 5 FAIL |
| `test_sl_inside_ob` | SL inside OB → Check 6 FAIL |
| `test_sl_exactly_at_ob_low_fails` | SL at boundary → Check 6 FAIL |
| `test_breaker_retest_framework` | Breaker framework checks breaker_blocks |
| `test_no_trade_parameters` | Null trade_params → graceful FAIL |
| `test_poi_price_zero` | POI price = 0 → FAIL |
| `test_poi_not_identified` | poi_identified=False → FAIL |
| `test_tolerance_allows_near_match` | Price within tolerance → PASS |
| `test_tighter_tolerance_rejects` | Tight tolerance → FAIL |
| `test_verification_rejects_in_orchestrator` | Mock rejection flows correctly |
| `test_verification_passes_through` | Pass-through works |
| `test_disabled_skips_all_checks` | Disabled config → SKIP |
| `test_short_all_pass` | SHORT direction works |
| `test_short_sl_below_ob_high_fails` | SHORT SL validation |
| `test_bos_accepted_for_m15` | BOS accepted alongside CHoCH |

**Full suite: 509 tests passed, 0 failed.**

---

## What This Would Have Caught

Based on the pressure test (5 sampled losses):

1. **2024-03-15 (Structure Misread)**: Check 3 (`h1_poi_exists`) would have caught this. The AI cited an H1 POI but no unmitigated H1 OB existed near that price. **Prevented: -1.0R loss.**

2. **2024-03-01 (Threshold Violation)**: Check 2 (`displacement_ratio`) would have caught this. MSO had displacement_ratio = 0.4, below the 1.5 threshold. **Prevented: -1.0R loss.**

3. **Phase 1C CHoCH bug**: Check 1 (`m15_choch_exists`) provides a deterministic backup for the prompt-level rule that AI must set choch_detected=True for CANDIDATE. If the AI ignores the rule, this check catches it.

---

## What This Does NOT Check (by design)

- Grade/confidence (subjective AI judgment)
- Sweep quality (subjective)
- Direction match, RR, SL floor, ATR (Gate 1 already handles these)
- No API calls — purely deterministic MSO field checks

---

## Files Changed

| File | Change |
|------|--------|
| `src/components/verification.py` | **NEW** — 6-check verification module |
| `tests/test_verification.py` | **NEW** — 24 tests |
| `src/components/orchestrator.py` | Added import + 8-line verification block at insertion point |
| `config/agent_config.yaml` | Added `verification:` section (4 lines) |
