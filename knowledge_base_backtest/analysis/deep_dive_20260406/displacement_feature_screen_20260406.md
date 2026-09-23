# Phase 2: Displacement DB Feature Screen — 2026-04-04 10:17

## 2-PREREQ: Version Verification
- CSV records: 7496 (prior analyses used 6,641)
- Discovery: 3748 | Validation: 3748
- Consistency checks: SOME FAILED
- **INVESTIGATE: inconsistent p-values**

## 2A: Comprehensive Feature Screen
- Tested: 64 predictor fields
- Bonferroni threshold: 0.000781

### CONFIRMED Features (survive Bonferroni)
| Field | Type | p-value | Effect Size | N |
|-------|------|---------|-------------|---|
| direction | categorical | 0.000000 | 0.0864 | 7496 |
| creates_fvg | boolean | 0.000000 | 0.1105 | 7496 |
| align | categorical | 0.000000 | 0.1412 | 7496 |
| origin_revisited | boolean | 0.000000 | 0.5409 | 7496 |
| fvg_pct | continuous | 0.000003 | 0.086 | 4558 |
| at_ob | boolean | 0.000011 | 0.056 | 7496 |
| ct | boolean | 0.000472 | 0.0515 | 7496 |

### SUGGESTIVE Features (p < 0.01)
| Field | Type | p-value | Effect Size | N |
|-------|------|---------|-------------|---|

### NULL Features: 57 fields with p >= 0.01

### Pairwise Correlations (Confirmed + Suggestive)
| Pair | Correlation |
|------|-------------|
| align × origin_revisited | -0.3611 |
| align × ct | -0.3063 |
| creates_fvg × origin_revisited | -0.1693 |
| origin_revisited × ct | 0.1187 |
| origin_revisited × fvg_pct | -0.1124 |
| origin_revisited × at_ob | 0.0312 |
| align × at_ob | -0.0287 |
| fvg_pct × ct | -0.0157 |
| fvg_pct × at_ob | 0.0125 |
| creates_fvg × align | 0.011 |

## 2B: H4 Alignment Deep Dive
- h4_dir × cont_3h: p=0.764477
  - insufficient_data: n=159, cont_rate=0.5094
  - bearish: n=226, cont_rate=0.4867
  - bullish: n=7079, cont_rate=0.491
  - transitional: n=32, cont_rate=0.4062

## 2C: Untested Features
| Feature | p-value | N | Notes |
|---------|---------|---|-------|
| align | 0.0 | 7496 | |
| crosses_rn | 0.564378 | 7496 | |
| first_kz | 0.584093 | 7496 | |
| liq_depth | 0.609716 | 7496 | |
| m15_aligned | 0.673087 | 7496 | |
| levels_swept | 0.692515 | 7496 | |
| mss | 0.69924 | 7496 | |
| exhaust | 0.818261 | 7496 | |
| strength | 0.898458 | 7496 | |
| kz_min | 0.998296 | 1640 | |

## 2D: Failed Origin Revisit
- Revisited: 6287
- Success (continued): 3643 (57.9%)
- Failure: 2644

| Feature | p-value | Type | Success vs Failure |
|---------|---------|------|-------------------|
| align | 0.000002 | continuous | S:1.3409 vs F:1.2008 |
| at_ob | 0.000005 | boolean | S:0.28 vs F:0.33 |
| ob_dist | 0.003585 | continuous | S:0.8009 vs F:0.7288 |
| mss | 0.041987 | continuous | S:203.8073 vs F:198.6706 |
| seq | 0.051683 | continuous | S:1.9827 vs F:1.9266 |
| ct | 0.061889 | boolean | S:0.21 vs F:0.23 |
| creates_fvg | 0.066808 | boolean | S:0.58 vs F:0.56 |
| rn_level | 0.070180 | continuous | S:3696.0149 vs F:3606.0940 |
| exhaust | 0.073487 | boolean | S:0.12 vs F:0.10 |
| pdl | 0.198292 | continuous | S:3100.0060 vs F:3071.8198 |

## 2E: Body Ratio + FVG Creation
### Body Ratio Quintiles
| Quintile | N | Cont Rate | Range |
|----------|---|-----------|-------|
| Q1 | 1467 | 0.4915 | 2.0000 to 2.2100 |
| Q2 | 1523 | 0.5121 | 2.2200 to 2.5100 |
| Q3 | 1494 | 0.4719 | 2.5200 to 2.9700 |
| Q4 | 1506 | 0.4847 | 2.9800 to 3.8100 |
| Q5 | 1506 | 0.494 | 3.8200 to 32.6400 |

Optimal threshold: None (rate diff: 0)

### FVG Creation
p-value: 0.0
- True: n=4558, rate=0.5342
- False: n=2938, rate=0.4238
