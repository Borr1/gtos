# Per-Record Extraction Summary — 2026-04-06

## What Was Done

Extracted per-record data from the OB and FVG comprehensive analyses. The comprehensive scripts only saved aggregate statistics (chi-squared, group rates). This extraction saves every individual OB and FVG with all features, enabling:

- Continuous retracement depth curve (via `retracement_pct`)
- Impulse leg character analysis
- FVG/OB date and spatial overlap analysis
- Custom filtering and cross-referencing

## Files Produced

| File | Records | Description |
|------|---------|-------------|
| `ob_per_record_xauusd.json` | 820 | Every H1 OB with 35+ features |
| `ob_per_record_xauusd.csv` | 820 | Same data, CSV format |
| `ob_per_record_gbpusd.json` | 5 | GBPUSD OBs (limited data) |
| `fvg_per_record_xauusd.json` | 1,661 | Every filled H1 FVG with features |
| `fvg_per_record_xauusd.csv` | 1,661 | Same data, CSV format |
| `fvg_per_record_gbpusd.json` | 18 | GBPUSD FVGs (limited data) |
| `framework_date_overlap.json` | — | Date and spatial overlap analysis |
| `extraction_summary.json` | — | Machine-readable summary |

## OB Per-Record Key Stats

- **Total XAUUSD OBs:** 820 (exact match with comprehensive)
- **Date range:** 2024-04-01 to 2026-03-27 (516 trading days)
- **Retest rate:** 98.2% (805 of 820 retested within 48h)
- **Continuation rate:** 72.8% of retested (1.5R target in 3h)
- **BOS vs CHoCH:** 787 BOS, 33 CHoCH

### Retracement % Distribution (NEW — most important field)

| Stat | Value |
|------|-------|
| Min | 0.5212 |
| Q1 | 0.8678 |
| Median | 0.9143 |
| Q3 | 0.9430 |
| Max | 0.9798 |
| Mean | 0.8990 |

**Key insight:** ALL OBs have retracement_pct > 52%. The median is 91.4%, meaning the typical OB sits at a very deep retracement of its impulse leg. The OTE zone (61.8-78.6%) captures only a small fraction of where OBs actually form — most are DEEPER than OTE. This is expected: the OB is the candle that *precedes* the displacement, so it's near the origin of the impulse.

### Body Range Ratio

| Stat | Value |
|------|-------|
| Min | 0.0033 |
| Median | 0.3917 |
| Max | 0.9202 |

## FVG Per-Record Key Stats

- **Total XAUUSD FVGs:** 1,661 (vs ~1,783 in comprehensive, 7% diff due to date boundary handling)
- **Date range:** 2024-04-01 to 2026-03-30
- **Fill rate:** 100% (script only saves filled FVGs)
- **Continuation rate:** 55.9% of filled FVGs (1.5R target in 3h)

### Fill Percentage Distribution

| Stat | Value |
|------|-------|
| Min | 0.0000 |
| Q1 | 0.7343 |
| Median | 1.2390 |
| Q3 | 2.0000 |
| Max | 2.0000 |

## Date Overlap Analysis

How often do OB retests and FVG fills happen on the SAME trading day (during kill zones)?

| Category | Days | % of total |
|----------|------|-----------|
| Both OB retest + FVG fill (KZ) | 200 | 39.1% |
| OB retest only (KZ) | 67 | 13.1% |
| FVG fill only (KZ) | 179 | 35.0% |
| Neither | 65 | 12.7% |
| **Total trading days** | **511** | |

**FVG additive value:** 179 dates (35.0%) have KZ FVG fills but NO KZ OB retest — FVGs provide genuinely additive signal on a substantial number of days.

## Spatial Overlap Analysis

For same-date OBs and FVGs, how often do their price zones physically overlap?

| Metric | Value |
|--------|-------|
| Dates with both OBs and FVGs | 366 |
| OBs with FVG spatial overlap | 205 (25.7%) |
| OBs without FVG spatial overlap | 593 (74.3%) |
| Total OB-FVG overlap pairs | 354 |

**Note:** Only 25.7% of OBs have a same-day FVG overlapping their price zone. This is informational — the KILLED finding was about FVG overlap as an OB quality predictor (which reversed in validation), not about the spatial relationship itself.

## GBPUSD Status

Limited data available (only 5 trading days, symlinks point to small test files). GBPUSD per-record extraction requires the full Windows candle re-download for meaningful analysis.

## Fields Available Per OB Record

`date`, `formation_time`, `symbol`, `timeframe`, `ob_type`, `ob_price_top`, `ob_price_bottom`, `ob_midpoint`, `ob_open`, `ob_close`, `causing_event_type`, `d1_direction`, `h4_direction`, `h4_aligned`, `d1_aligned`, `body_range_ratio`, `width_pct_atr`, `displacement_ratio_at_formation`, `retracement_pct`, `premium_discount_zone`, `in_ote`, `session`, `hour_of_formation`, `day_of_week`, `nearby_ob_count`, `ob_sequence_number`, `fvg_overlap`, `impulse_created_fvg`, `impulse_candle_count`, `impulse_atr_multiple`, `impulse_body_ratio_avg`, `asian_range_pct_adr`, `h1_atr`, `retested`, `continuation`, `kz_at_retest`, `time_of_retest`, `freshness_candles`, `outcome_hit_target_3h`, `outcome_mfe_r`, `outcome_mae_r`, `outcome_m15_displacement_at_retest`, `outcome_m15_displacement_ratio`, `period`

## Fields Available Per FVG Record

`date`, `formation_time`, `symbol`, `timeframe`, `fvg_type`, `fvg_top`, `fvg_bottom`, `fvg_midpoint`, `fvg_size`, `width_pct_atr`, `creation_displacement_ratio`, `d1_direction`, `h4_direction`, `d1_aligned`, `h4_aligned`, `session`, `kz`, `premium_discount_zone`, `ob_overlap`, `filled`, `fill_percentage`, `fill_time`, `max_fill_depth`, `freshness_candles`, `continuation_3h`, `outcome_mfe_r`, `outcome_mae_r`, `period`
