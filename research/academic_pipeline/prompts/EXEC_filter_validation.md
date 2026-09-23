# EXEC — Filter Validation: Gap Ceiling + Touch-1 on Scenario A
# XAUUSD Jan 2 – Apr 10, 2026

**For:** Fresh Claude Code terminal (Sonnet, effort=max)  
**Task type:** $0 pure computation — no API calls, read-only + write output files  
**Output files:**
- `research/academic_pipeline/results/filter_validation_v1.md`
- `research/academic_pipeline/data/filter_validation_summary.json`

---

## Context

A prior analysis (entry_scenario_analysis_v1.md) showed that placing limit orders at OB zones on 557 rejected XAUUSD setups produces +45.0R over Jan–Apr 2026 at 45.5% WR on 325 resolved trades (Scenario A). Two concerns:

1. **WR = 45.5% is fragile** — above the 40% breakeven for a 1.5R system, but March alone dropped to 33.3% (below breakeven)
2. **Two filters are hypothesized to improve WR** based on separate research:
   - **Gap ceiling**: reject setups where current price is too far above the OB zone (staleness proxy)
   - **Touch-1 only**: only take OBs on their first retest (touch-1 = 72.7% WR, touch-2+ = 31.7% WR, from Q-2.2 zone age analysis)

This script validates whether those filters actually improve WR in the data before any production change is recommended. The baseline must reproduce the already-verified numbers exactly.

---

## Data Sources

- **Simulation records:** `research/t7_live_simulation/all_results_jan_apr10.json`
  - Access: `data = json.load(f); all_records = data['results']`
  - Extract: `rejected = [r for r in all_records if r.get('decision')=='REJECTED_L2' and 'entry_in_ob' in str(r.get('l2_reason',''))]`
  - Expected count: exactly 557

- **M15 price data:** `data/historical_2026/XAUUSD_M15.csv`
  - Columns: `time, open, high, low, close, volume`
  - Time format: `2026-01-07 09:45:00`
  - Build index: `{time_str: idx}` for fast lookup

---

## Filter Definitions

### Filter 1: Gap Ceiling
```
gap_pct = (entry_price - ob_high) / ob_high * 100
```
Where `ob_high` is parsed from `l2_reason` (format: "Entry X is outside OB zone {ob_low}-{ob_high}").

Run analysis at three thresholds: **1.5%, 2.0%, 2.5%**

Records where `entry_price < ob_high` (gap <= 0) are already inside the zone — include them in all gap-filtered sets (they pass any ceiling).

### Filter 2: Touch-1 (Prior Zone Entry Count)
For each record:
1. Parse `ob_high` from `l2_reason`
2. Find `M15_idx` = index of record's `candle_time` in the M15 CSV
   - Convert: `2026-01-07T09:45:00Z` → `2026-01-07 09:45:00`
3. Scan M15 candles from index 0 up to (but NOT including) `M15_idx`
4. Count candles where `candle['low'] <= ob_high` → this is `prior_touch_count`
5. **Touch-1** = `prior_touch_count == 0` (price has never previously entered this OB zone in our dataset)

**Definition note:** A "prior touch" means price physically entered the zone top (low reached ob_high or lower). If `prior_touch_count == 0`, the eventual limit fill would be the FIRST time price enters this zone — the Q-2.2 touch-1 scenario with 72.7% continuation. If `prior_touch_count >= 1`, the zone has already been entered at least once — the touch-2+ scenario (31.7% continuation).

---

## Scenario A Algorithm (reuse from existing analysis)

```python
def scenario_a(forward_candles_192, direction, zone_entry, zone_sl, zone_tp_1r5):
    """
    forward_candles_192: up to 192 M15 candles after candle_time (48 hours)
    direction: always LONG in this dataset
    zone_entry: ob_high (for LONG)
    zone_sl: ob_low * 0.999
    zone_tp_1r5: zone_entry + (zone_entry - zone_sl) * 1.5

    Returns: {'fill': bool, 'outcome': 'WIN'|'LOSS'|'OPEN'|None}
    """
    fill_idx = None
    for i, c in enumerate(forward_candles_192):
        if c['low'] <= zone_entry:   # LONG: filled when candle touches zone top
            fill_idx = i
            break

    if fill_idx is None:
        return {'fill': False, 'outcome': None}  # expired

    # Scan candles from fill onward for outcome
    after_fill = forward_candles_192[fill_idx + 1:]
    for c in after_fill:
        tp_hit = c['high'] >= zone_tp_1r5
        sl_hit = c['low'] <= zone_sl
        if tp_hit and sl_hit:
            # Same-candle: bullish close = TP first (LONG)
            outcome = 'WIN' if c['close'] > c['open'] else 'LOSS'
            return {'fill': True, 'outcome': outcome}
        elif tp_hit:
            return {'fill': True, 'outcome': 'WIN'}
        elif sl_hit:
            return {'fill': True, 'outcome': 'LOSS'}

    # Also check fill candle itself for immediate TP/SL
    fill_c = forward_candles_192[fill_idx]
    if fill_c['high'] >= zone_tp_1r5 and fill_c['low'] <= zone_sl:
        outcome = 'WIN' if fill_c['close'] > fill_c['open'] else 'LOSS'
        return {'fill': True, 'outcome': outcome}
    elif fill_c['high'] >= zone_tp_1r5:
        return {'fill': True, 'outcome': 'WIN'}
    elif fill_c['low'] <= zone_sl:
        return {'fill': True, 'outcome': 'LOSS'}

    return {'fill': True, 'outcome': 'OPEN'}   # filled but no resolution in window
```

Zone parameters for every LONG record:
```python
ob_low, ob_high = parse_ob_zone(record['l2_reason'])
zone_entry = ob_high
zone_sl = ob_low * 0.999
zone_risk = zone_entry - zone_sl
zone_tp_1r5 = zone_entry + zone_risk * 1.5
```

---

## Analyses to Run

### Part 1: Filter Population Counts
Report how many of 557 records pass each filter, before running any trade simulation:

| Filter | Records | % of 557 |
|--------|---------|-----------|
| No filter (baseline) | 557 | 100% |
| Gap ≤ 1.5% | ? | ? |
| Gap ≤ 2.0% | ? | ? |
| Gap ≤ 2.5% | ? | ? |
| Touch-1 only | ? | ? |
| Gap ≤ 2.0% + Touch-1 | ? | ? |

### Part 2: Scenario A Performance by Filter
Run Scenario A on each filtered subset. For each: fill rate, WR on resolved, Total R.

| Filter | N setups | Fills | Resolved | WR | Total R |
|--------|----------|-------|----------|----|---------|
| Baseline (no filter) | 557 | ? | ? | ? | ? |
| Gap ≤ 1.5% only | ? | ? | ? | ? | ? |
| Gap ≤ 2.0% only | ? | ? | ? | ? | ? |
| Gap ≤ 2.5% only | ? | ? | ? | ? | ? |
| Touch-1 only | ? | ? | ? | ? | ? |
| Gap ≤ 2.0% + Touch-1 | ? | ? | ? | ? | ? |

**Baseline must reproduce exactly:** 332 fills (59.6%), 148W / 177L on 325 resolved, WR = 45.5%, Total R = +45.0. If baseline fails to reproduce, stop and report the discrepancy before proceeding.

### Part 3: Monthly Breakdown — Gap ≤ 2.0% + Touch-1 Combined
Same table format as the original monthly breakdown:

| Month | N setups (filtered) | Filled | Resolved | WR | Total R |
|-------|---------------------|--------|----------|----|---------|
| 2026-01 | ? | ? | ? | ? | ? |
| 2026-02 | ? | ? | ? | ? | ? |
| 2026-03 | ? | ? | ? | ? | ? |
| 2026-04 | ? | ? | ? | ? | ? |

### Part 4: Touch Distribution Analysis
For all 557 records, report the distribution of `prior_touch_count`:

| Prior touches | Count | % | Scenario A WR (if run) |
|--------------|-------|---|----------------------|
| 0 (touch-1) | ? | ? | ? |
| 1 | ? | ? | ? |
| 2 | ? | ? | ? |
| 3–5 | ? | ? | ? |
| 6–10 | ? | ? | ? |
| 11+ | ? | ? | ? |

Run Scenario A on each bucket separately and report WR. This validates whether the touch degradation pattern (72.7% → 31.7%) holds in this dataset.

---

## Validation Checks

Before writing final output, verify:

1. **Baseline count:** 557 records extracted (PASS/FAIL)
2. **Baseline fill rate:** 332/557 = 59.6% (±1 rounding) (PASS/FAIL)
3. **Baseline WR:** 148/325 = 45.5% (PASS/FAIL)
4. **Baseline Total R:** +45.0 (PASS/FAIL — computed as wins×1.5 - losses×1)
5. **M15 index alignment:** First record (2026-01-07T09:45:00Z) maps to a valid M15 candle (PASS/FAIL)
6. **Touch-1 count plausibility:** Touch-1 records should be a material subset of 557 — if result is <10 or >500, flag as suspicious before proceeding
7. **No M15 lookup misses:** Report how many records had no M15 match (expected: 0)

---

## Output Format

### Markdown report: `research/academic_pipeline/results/filter_validation_v1.md`

```
# Filter Validation — Gap Ceiling + Touch-1
# XAUUSD Jan 2 – Apr 10, 2026

**Analysis date:** 2026-04-13
**Source:** research/t7_live_simulation/all_results_jan_apr10.json
**Baseline:** 557 entry_in_ob rejections, Scenario A: +45.0R / 45.5% WR

## Validation Checks
[all 7 checks with PASS/FAIL]

## 1. Filter Population Counts
[table]

## 2. Scenario A Performance by Filter
[table]

## 3. Monthly Breakdown — Gap ≤ 2.0% + Touch-1 Combined
[table]

## 4. Touch Distribution Analysis
[table — prior touch count buckets with per-bucket WR]

## 5. Key Findings
[numbered F1, F2, ... — factual observations only, no recommendations]
[Include: does touch degradation hold? which gap ceiling has best R? does March still fail?]
```

### JSON summary: `research/academic_pipeline/data/filter_validation_summary.json`
```json
{
  "analysis_date": "2026-04-13",
  "baseline": {"n": 557, "fills": 332, "wr": 0.4554, "total_r": 45.0},
  "gap_filter": {
    "1.5pct": {"n": ?, "fills": ?, "resolved": ?, "wr": ?, "total_r": ?},
    "2.0pct": {"n": ?, "fills": ?, "resolved": ?, "wr": ?, "total_r": ?},
    "2.5pct": {"n": ?, "fills": ?, "resolved": ?, "wr": ?, "total_r": ?}
  },
  "touch1_filter": {"n": ?, "fills": ?, "resolved": ?, "wr": ?, "total_r": ?},
  "combined_2pct_touch1": {
    "n": ?, "fills": ?, "resolved": ?, "wr": ?, "total_r": ?,
    "monthly": {
      "2026-01": {"n": ?, "fills": ?, "resolved": ?, "wr": ?, "total_r": ?},
      "2026-02": {"n": ?, "fills": ?, "resolved": ?, "wr": ?, "total_r": ?},
      "2026-03": {"n": ?, "fills": ?, "resolved": ?, "wr": ?, "total_r": ?},
      "2026-04": {"n": ?, "fills": ?, "resolved": ?, "wr": ?, "total_r": ?}
    }
  },
  "touch_distribution": [
    {"prior_touches": 0, "n": ?, "fills": ?, "resolved": ?, "wr": ?, "total_r": ?},
    {"prior_touches": 1, "n": ?, "fills": ?, "resolved": ?, "wr": ?, "total_r": ?},
    ...
  ]
}
```

---

## Script Location
Write and execute: `research/academic_pipeline/scripts/filter_validation.py`

The script must be self-contained — do not import from `entry_scenario_analysis.py`. Copy the shared helpers directly. Use `BASE_DIR = '/Users/borr/Documents/trading/gold-agent'`.

---

## Done Checklist
- [ ] 557 records extracted and validated
- [ ] M15 loaded, time index built
- [ ] `prior_touch_count` computed for all 557 records
- [ ] `gap_pct` computed for all 557 records
- [ ] Baseline Scenario A reproduced (all 4 validation checks pass)
- [ ] All 6 filter variants run
- [ ] Monthly breakdown for combined filter computed
- [ ] Touch distribution by bucket with per-bucket WR computed
- [ ] `filter_validation_v1.md` written
- [ ] `filter_validation_summary.json` written
- [ ] No fabricated numbers — every figure traces to data
