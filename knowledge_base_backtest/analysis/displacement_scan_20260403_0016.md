# Displacement Scanner — Edge Discovery Report
**Generated:** 20260403_0016
**Data:** 2024-04-01 01:00:00 to 2026-03-30 18:00:00 (47,142 M15 candles)
**Split:** 2025-03-28 08:00:00
**Scan time:** 4s

## Executive Summary

- **6,641** displacements detected (standard=4,041, strong=1,437, extreme=1,163)
- Discovery: 3,329 | Validation: 3,312
- Baseline 3h continuation rate: **48.7%**
- **0** candidate edges found in discovery
- **5** patterns replicated on validation data
- OB retest captures **84%** of displacements; **16%** never pull back
- Monthly displacement rate: ~298/month

## Section 1: Displacement Census

**Session:** ny=2722, asian=2040, london=1514, late=365
**Direction:** bullish=3423, bearish=3218
**Strength:** standard=4041, strong=1437, extreme=1163
**Day:** Wednesday=1373, Tuesday=1352, Friday=1344, Thursday=1299, Monday=1273

**D1 Aligned:** 1000 (15.1%)
**In Kill Zone:** 1416 (21.3%)

## Section 2: Single-Factor Results (Discovery)

Baseline 3h cont: 48.7%

### Flagged Factors
| Factor | Value | n | 1h | 3h | Sess | MFE$ | MAE$ | MFE/MAE | Effect |
|--------|-------|---|----|----|------|------|------|---------|--------|
| origin_revisited | False | 530 | 87.9% | 94.5% | 92.5% | $10.8 | $1.8 | 6.0x | +45.9% |
| nc_dir | continuation | 1072 | 72.7% | 63.2% | 59.8% | $9.4 | $4.3 | 2.1x | +14.6% |
| align | 3 | 31 | 64.5% | 61.3% | 64.5% | $10.2 | $7.4 | 1.4x | +12.6% |
| nc_dir | reversal | 1162 | 24.1% | 36.7% | 39.5% | $4.5 | $9.0 | 0.5x | -11.9% |

### All Factors

**align:** (baseline=48.7%)
| Value | n | 3h | MFE | MAE | Effect |
|-------|---|----|----|-------|--------|
| 0 | 1537 | 50.9% | $7.0 | $6.5 | +2.2% |
| 1 | 1404 | 46.3% | $6.6 | $7.1 | -2.4% |
| 2 | 357 | 47.3% | $6.3 | $7.2 | -1.3% |
| 3 * | 31 | 61.3% | $10.2 | $7.4 | +12.6% |

**asian_range_bkt:** (baseline=48.7%)
| Value | n | 3h | MFE | MAE | Effect |
|-------|---|----|----|-------|--------|
| 30-50% | 1383 | 48.3% | $6.3 | $6.6 | -0.4% |
| <30% | 1264 | 47.2% | $6.2 | $6.4 | -1.4% |
| 50-80% | 513 | 53.0% | $8.6 | $7.7 | +4.4% |
| >80% | 169 | 49.1% | $10.2 | $9.0 | +0.4% |

**body_ratio_bkt:** (baseline=48.7%)
| Value | n | 3h | MFE | MAE | Effect |
|-------|---|----|----|-------|--------|
| 2-3x | 2012 | 48.5% | $6.5 | $6.6 | -0.2% |
| 3-4x | 725 | 49.7% | $6.7 | $6.7 | +1.0% |
| >4x | 592 | 48.1% | $7.9 | $7.8 | -0.5% |

**consol_bucket:** (baseline=48.7%)
| Value | n | 3h | MFE | MAE | Effect |
|-------|---|----|----|-------|--------|
| >0.8 | 3329 | 48.7% | $6.8 | $6.8 | +0.0% |

**creates_fvg:** (baseline=48.7%)
| Value | n | 3h | MFE | MAE | Effect |
|-------|---|----|----|-------|--------|
| True | 2017 | 53.2% | $7.7 | $6.0 | +4.5% |
| False | 1312 | 41.7% | $5.4 | $8.1 | -7.0% |

**crosses_rn:** (baseline=48.7%)
| Value | n | 3h | MFE | MAE | Effect |
|-------|---|----|----|-------|--------|
| False | 2804 | 48.1% | $6.6 | $6.6 | -0.6% |
| True | 525 | 51.6% | $8.0 | $8.0 | +3.0% |

**ct:** (baseline=48.7%)
| Value | n | 3h | MFE | MAE | Effect |
|-------|---|----|----|-------|--------|
| False | 2944 | 48.6% | $6.7 | $6.8 | -0.1% |
| True | 385 | 49.1% | $7.4 | $6.8 | +0.4% |

**d1_aligned:** (baseline=48.7%)
| Value | n | 3h | MFE | MAE | Effect |
|-------|---|----|----|-------|--------|
| False | 2928 | 48.5% | $6.8 | $6.8 | -0.1% |
| True | 401 | 49.6% | $6.8 | $6.8 | +1.0% |

**dow:** (baseline=48.7%)
| Value | n | 3h | MFE | MAE | Effect |
|-------|---|----|----|-------|--------|
| Friday | 693 | 50.8% | $7.6 | $7.3 | +2.1% |
| Wednesday | 679 | 44.6% | $6.6 | $7.1 | -4.0% |
| Thursday | 666 | 49.1% | $6.8 | $6.5 | +0.4% |
| Tuesday | 665 | 48.0% | $6.2 | $6.7 | -0.7% |
| Monday | 626 | 51.0% | $6.8 | $6.4 | +2.3% |

**exhaust:** (baseline=48.7%)
| Value | n | 3h | MFE | MAE | Effect |
|-------|---|----|----|-------|--------|
| False | 2957 | 48.6% | $6.8 | $6.8 | -0.1% |
| True | 372 | 49.2% | $6.9 | $7.1 | +0.5% |

**h4_aligned_d1:** (baseline=48.7%)
| Value | n | 3h | MFE | MAE | Effect |
|-------|---|----|----|-------|--------|
| True | 1790 | 49.3% | $6.8 | $6.7 | +0.7% |
| False | 1539 | 47.9% | $6.8 | $7.0 | -0.8% |

**in_disc:** (baseline=48.7%)
| Value | n | 3h | MFE | MAE | Effect |
|-------|---|----|----|-------|--------|
| False | 2022 | 48.5% | $6.7 | $6.7 | -0.2% |
| True | 1307 | 49.0% | $7.0 | $7.0 | +0.3% |

**in_ote:** (baseline=48.7%)
| Value | n | 3h | MFE | MAE | Effect |
|-------|---|----|----|-------|--------|
| False | 2922 | 48.6% | $6.8 | $6.8 | -0.1% |
| True | 407 | 49.4% | $6.5 | $6.9 | +0.7% |

**in_prem:** (baseline=48.7%)
| Value | n | 3h | MFE | MAE | Effect |
|-------|---|----|----|-------|--------|
| True | 2022 | 48.5% | $6.7 | $6.7 | -0.2% |
| False | 1307 | 49.0% | $7.0 | $7.0 | +0.3% |

**kz:** (baseline=48.7%)
| Value | n | 3h | MFE | MAE | Effect |
|-------|---|----|----|-------|--------|
| False | 2609 | 48.7% | $6.4 | $6.5 | +0.0% |
| True | 720 | 48.6% | $8.1 | $8.0 | -0.1% |

**liq_depth_bkt:** (baseline=48.7%)
| Value | n | 3h | MFE | MAE | Effect |
|-------|---|----|----|-------|--------|
| 4+ | 2130 | 48.8% | $6.1 | $6.2 | +0.2% |
| 2-3 | 1005 | 48.2% | $7.9 | $7.6 | -0.5% |
| 0-1 | 194 | 49.5% | $8.5 | $9.8 | +0.8% |

**nc_dir:** (baseline=48.7%)
| Value | n | 3h | MFE | MAE | Effect |
|-------|---|----|----|-------|--------|
| reversal * | 1162 | 36.7% | $4.5 | $9.0 | -11.9% |
| doji | 1095 | 47.0% | $6.7 | $6.9 | -1.6% |
| continuation * | 1072 | 63.2% | $9.4 | $4.3 | +14.6% |

**origin_revisited:** (baseline=48.7%)
| Value | n | 3h | MFE | MAE | Effect |
|-------|---|----|----|-------|--------|
| True | 2799 | 40.0% | $6.0 | $7.8 | -8.7% |
| False * | 530 | 94.5% | $10.8 | $1.8 | +45.9% |

**p5_char:** (baseline=48.7%)
| Value | n | 3h | MFE | MAE | Effect |
|-------|---|----|----|-------|--------|
| trending_with | 1444 | 48.0% | $6.9 | $6.9 | -0.7% |
| trending_against | 1348 | 49.5% | $6.8 | $6.7 | +0.8% |
| choppy | 537 | 48.4% | $6.4 | $6.9 | -0.2% |

**pd_rva_bkt:** (baseline=48.7%)
| Value | n | 3h | MFE | MAE | Effect |
|-------|---|----|----|-------|--------|
| 0.5-1.0 | 1849 | 49.2% | $6.9 | $6.8 | +0.5% |
| >1.0 | 1343 | 47.7% | $6.8 | $6.9 | -1.0% |
| <0.5 | 137 | 51.8% | $6.1 | $6.0 | +3.2% |

**seq_bkt:** (baseline=48.7%)
| Value | n | 3h | MFE | MAE | Effect |
|-------|---|----|----|-------|--------|
| 1st | 1473 | 47.8% | $6.6 | $6.6 | -0.9% |
| 2nd | 965 | 50.4% | $7.0 | $6.8 | +1.7% |
| 3rd+ | 891 | 48.3% | $6.9 | $7.2 | -0.4% |

**session:** (baseline=48.7%)
| Value | n | 3h | MFE | MAE | Effect |
|-------|---|----|----|-------|--------|
| ny | 1367 | 48.7% | $8.7 | $8.8 | +0.1% |
| asian | 1000 | 49.6% | $5.2 | $5.4 | +0.9% |
| london | 814 | 47.9% | $5.7 | $5.4 | -0.8% |
| late | 148 | 45.9% | $6.0 | $5.7 | -2.7% |

**sweep:** (baseline=48.7%)
| Value | n | 3h | MFE | MAE | Effect |
|-------|---|----|----|-------|--------|
| True | 2915 | 48.4% | $7.0 | $7.1 | -0.3% |
| False | 414 | 50.7% | $5.3 | $5.1 | +2.1% |

**sweep_level:** (baseline=48.7%)
| Value | n | 3h | MFE | MAE | Effect |
|-------|---|----|----|-------|--------|
| asian_high | 987 | 48.3% | $7.2 | $7.6 | -0.3% |
| asian_low | 730 | 48.6% | $8.2 | $7.4 | -0.0% |
| session_high | 373 | 51.2% | $5.7 | $5.7 | +2.5% |
| session_low | 372 | 42.5% | $6.1 | $7.1 | -6.2% |
| pdh | 326 | 52.8% | $6.6 | $6.0 | +4.1% |
| pdl | 127 | 44.9% | $5.9 | $7.2 | -3.8% |

**sweep_quality:** (baseline=48.7%)
| Value | n | 3h | MFE | MAE | Effect |
|-------|---|----|----|-------|--------|
| run | 2495 | 48.1% | $7.0 | $7.2 | -0.6% |
| clean | 420 | 50.2% | $6.8 | $6.6 | +1.6% |

**tight_bkt:** (baseline=48.7%)
| Value | n | 3h | MFE | MAE | Effect |
|-------|---|----|----|-------|--------|
| >0.5 | 3328 | 48.7% | $6.8 | $6.8 | +0.0% |

**wick_ratio_bkt:** (baseline=48.7%)
| Value | n | 3h | MFE | MAE | Effect |
|-------|---|----|----|-------|--------|
| <0.3 | 1641 | 48.0% | $6.7 | $6.7 | -0.6% |
| >0.5 | 860 | 49.9% | $7.0 | $7.2 | +1.2% |
| 0.3-0.5 | 828 | 48.7% | $6.8 | $6.7 | +0.0% |

## Section 3: Combination Results (Discovery)

| Combination | n | 3h | MFE | MAE | MFE/MAE | Candidate? |
|-------------|---|----|-----|-----|---------|------------|
| FVG+Align>=3 | 25 | 64.0% | $11.2 | $6.8 | 1.6x | no |
| Sweep+FVG+Align>=3 | 22 | 63.6% | $12.0 | $6.9 | 1.7x | no |
| Sweep+Align>=3 | 28 | 60.7% | $10.8 | $7.6 | 1.4x | no |
| CT+3rd+Exhaust | 40 | 55.0% | $7.5 | $5.6 | 1.3x | no |
| Sweep+1st+Align>=2 | 170 | 54.7% | $6.9 | $6.6 | 1.1x | no |
| FVG+LowWick+Align>=2 | 127 | 54.3% | $7.0 | $6.1 | 1.1x | no |
| 1st+KZ+Align>=2 | 60 | 51.7% | $8.2 | $7.2 | 1.1x | no |
| 1st+FVG | 879 | 51.4% | $7.6 | $5.9 | 1.3x | no |
| Sweep+FVG+KZ | 446 | 51.3% | $8.8 | $7.3 | 1.2x | no |
| Sweep+KZ | 680 | 47.8% | $8.1 | $8.1 | 1.0x | no |
| 1st+Sweep+Zone | 591 | 46.0% | $6.5 | $6.9 | 0.9x | no |
| Tight+KZ+Align>=2 | 0 | — | — | — | — | insuf |
| Quiet+KZ+Align>=3 | 0 | — | — | — | — | insuf |
| Align>=3+KZ+Consol | 0 | — | — | — | — | insuf |
| KZ+Align>=3 | 8 | — | — | — | — | insuf |

## Section 4: Entry Timing & OB Retest

- Pullback rate (continuing disps): **69.1%**
- Avg pullback timing: 2.6 candles (39 min)
- Avg pullback depth: 62% of body

**OB Retest Study:**
- All disps that revisit origin: **84.1%** (2799/3329)
- Deep retest (50%+): 57.0%
- OTE retest (62-79%): 4.5%
- Revisit→continued: **57.1%**
- Avg MFE from retest: **$11.5**
- Avg MFE from close (no retest): $10.8
- **Opportunity cost: 16% of displacements never pull back**

## Section 5: Structural Patterns

### Exhaustion (Discovery)
| Pos | n | 3h | MFE | MAE |
|-----|---|----|-----|-----|
| 1st | 1473 | 47.8% | $6.6 | $6.6 |
| 2nd | 965 | 50.4% | $7.0 | $6.8 |
| 3rd+ | 891 | 48.3% | $6.9 | $7.2 |

### Counter-Trend (Discovery)
- Total: 385
- Reversed within 1h: 53.8%
- Continued at 3h: 49.1%

## Section 6: Validation

### Combination Validation
| Pattern | Disc n | Disc 3h | Val n | Val 3h | Verdict |
|---------|--------|---------|-------|--------|---------|
| FVG+Align>=3 | 25 | 64.0% | 43 | 67.4% | **REPLICATED** |
| Sweep+FVG+Align>=3 | 22 | 63.6% | 42 | 69.0% | **REPLICATED** |
| Sweep+Align>=3 | 28 | 60.7% | 75 | 64.0% | **REPLICATED** |
| CT+3rd+Exhaust | 40 | 55.0% | 47 | 42.6% | not rep |
| Sweep+1st+Align>=2 | 170 | 54.7% | 217 | 57.1% | **REPLICATED** |
| FVG+LowWick+Align>=2 | 127 | 54.3% | 189 | 62.4% | **REPLICATED** |
| 1st+KZ+Align>=2 | 60 | 51.7% | 67 | 58.2% | not rep |
| 1st+FVG | 879 | 51.4% | 932 | 53.3% | not rep |
| Sweep+FVG+KZ | 446 | 51.3% | 413 | 54.7% | not rep |
| Sweep+KZ | 680 | 47.8% | 637 | 49.6% | not rep |
| 1st+Sweep+Zone | 591 | 46.0% | 588 | 50.2% | not rep |
| Tight+KZ+Align>=2 | 0 | 0.0% | 0 | 0.0% | not rep |
| Quiet+KZ+Align>=3 | 0 | 0.0% | 0 | 0.0% | not rep |
| Align>=3+KZ+Consol | 0 | 0.0% | 0 | 0.0% | not rep |
| KZ+Align>=3 | 8 | 0.0% | 12 | 0.0% | not rep |

### Structural Validation
- OB retest rate: disc=84.1%, val=83.4%
- Exhaustion 1st: disc=47.8%, val=49.9%
- Exhaustion 2nd: disc=50.4%, val=50.4%
- Exhaustion 3rd+: disc=48.3%, val=49.2%
- Counter-trend reversal 1h: disc=53.8%, val=54.8%

## Section 7: Implications

### Replicated Patterns (actionable)
- **Sweep+FVG+Align>=3**: disc 63.6% -> val 69.0% (n=42)
- **Sweep+1st+Align>=2**: disc 54.7% -> val 57.1% (n=217)
- **FVG+LowWick+Align>=2**: disc 54.3% -> val 62.4% (n=189)
- **FVG+Align>=3**: disc 64.0% -> val 67.4% (n=43)
- **Sweep+Align>=3**: disc 60.7% -> val 64.0% (n=75)

### Key Takeaways
1. **OB retest works well:** 84% of displacements do pull back.
2. **No clear exhaustion:** Performance similar across sequence positions.
3. **Counter-trend disps mostly fail:** 54% reverse within 1h — tradeable as trend continuation signal.
4. **Monthly frequency:** ~298 displacements/month across all types.
