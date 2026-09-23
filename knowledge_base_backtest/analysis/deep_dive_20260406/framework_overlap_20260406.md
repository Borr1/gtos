# Phase 6: Per-Record Analyses — 2026-04-04 10:23

## 6A: Retracement Depth Curve
- N retested: 805 | N with data: 805
- Overall continuation rate: 0.728
- Mean retracement: 89.9% | Median: 91.4%

### Bin Results
| Bin | N | Cont Rate |
|-----|---|-----------|
| 50-70% | 9 | 0.2222 |
| 70-80% | 35 | 0.5429 |
| 80-85% | 101 | 0.6337 |
| 85-90% | 202 | 0.7871 |
| 90-95% | 328 | 0.7439 |
| 95-100% | 130 | 0.7538 |

Chi-squared across bins: p=0.0001
Median split Fisher p: 0.1322

## 6B: Impulse Character
{
  "impulse_candle_count": {
    "type": "continuous",
    "correlation": -0.3066,
    "p_value": 0.0
  },
  "impulse_atr_multiple": {
    "type": "continuous",
    "correlation": 0.0015,
    "p_value": 0.96564
  },
  "impulse_body_ratio_avg": {
    "type": "continuous",
    "correlation": 0.0545,
    "p_value": 0.11905
  },
  "impulse_created_fvg": {
    "type": "categorical",
    "rates": {
      "True": {
        "n": 751,
        "cont_rate": 0.7111
      },
      "False": {
        "n": 69

## 6C: Framework Overlap
- FVG-only dates: 179
- OB-only dates: 67
- Both: 200
- Neither: 65
- FVG increases trading frequency by 67.0%
- >30% increase: YES — strong recommendation to implement

## 6D: FVG Deep Dive
- Records: 1661 | Overall cont: 0.5587

### Fill Depth Bins
| Bin | N | Cont Rate |
|-----|---|----------|
| 0-10% | 125 | 0.2 |
| 10-20% | 22 | 0.2727 |
| 20-30% | 28 | 0.3929 |
| 30-40% | 44 | 0.25 |
| 40-50% | 53 | 0.283 |
| 50-60% | 56 | 0.3571 |
| 60-70% | 67 | 0.4627 |
| 70-80% | 73 | 0.5068 |
| 80-100% | 168 | 0.7143 |
| 100-200% | 1025 | 0.6361 |

### FVG Size Quintiles
| Q | N | Cont Rate | Size Range |
|---|---|-----------|------------|
| Q1 | 327 | 0.5841 | 0.45 to 1.66 |
| Q2 | 335 | 0.591 | 1.68 to 2.82 |
| Q3 | 334 | 0.515 | 2.83 to 4.71 |
| Q4 | 332 | 0.5331 | 4.72 to 8.72 |
| Q5 | 333 | 0.5706 | 8.74 to 179.96 |

## 6E: Calendar Analysis
Status: N/A

## 6F: GBPUSD Analysis
- XAUUSD FVG cont: 55.9% (n=1661)
- GBPUSD FVG cont: 38.9% (n=18)
- Gap: 17.0pp
