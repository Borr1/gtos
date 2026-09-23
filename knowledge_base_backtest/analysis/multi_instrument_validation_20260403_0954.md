# Multi-Instrument Validation Report
**Generated:** 20260403_0954
**Total scan time:** 21s

## Executive Summary

- **5** instruments scanned with the same displacement methodology
- **GREEN:** None
- **YELLOW:** XAUUSD, EURUSD, GBPUSD, NAS100, XAGUSD
- **RED:** None
- **Best candidate for investigation:** XAUUSD (score=18.4)

## Section 1: Data Inventory

| Instrument | D1 | H4 | H1 | M15 | M5 | Data Range | Trading Days |
|-----------|-----|-----|-----|------|-----|------------|-------------|
| XAUUSD | Y | Y | Y | Y | Y | 2024-01-02 to 2026-04-02 | 582 |
| EURUSD | Y | Y | Y | Y | Y | 2024-01-02 to 2026-04-03 | 586 |
| GBPUSD | Y | Y | Y | Y | Y | 2024-01-02 to 2026-04-03 | 586 |
| NAS100 | Y | Y | Y | Y | Y | 2024-01-02 to 2026-04-02 | 545 |
| XAGUSD | Y | Y | Y | Y | Y | 2024-01-02 to 2026-04-02 | 583 |

### Basic Statistics

| Instrument | ADR (native) | ADR (pips/pts) | M15 ATR (median) | Avg M15 Body | Equal Tolerance |
|-----------|-----------|----------------|------------------|-------------|-----------------|
| XAUUSD | 60.59555 | 6059.6 $ | 3.530000 | 2.742504 | 1.371252 |
| EURUSD | 0.00727 | 72.7 pips | 0.000520 | 0.000332 | 0.000166 |
| GBPUSD | 0.00877 | 87.7 pips | 0.000660 | 0.000402 | 0.000201 |
| NAS100 | 358.35932 | 3583.6 pts | 20.800000 | 15.738677 | 7.869338 |
| XAGUSD | 1.75228 | 1752.3 $ | 0.075000 | 0.078606 | 0.039303 |

## Section 2: Master Ranking Table

| Metric | XAUUSD (ref) | EURUSD | GBPUSD | NAS100 | XAGUSD |
|--------|-------------|--------|--------|--------|--------|
| Total displacements | 7,496 | 7,859 | 7,828 | 6,953 | 7,695 |
| Disps/month | 298 | 297 | 296 | 298 | 302 |
| Baseline 3h continuation | 48.2% | 48.6% | 48.7% | 47.4% | 48.8% |
| FVG creation rate | 60.8% | 57.1% | 57.8% | 59.7% | 54.2% |
| OB retest (disc) | 84.4% | 87.3% | 86.7% | 84.9% | 85.8% |
| OB retest (val) | 83.3% | 86.1% | 86.0% | 85.0% | 85.8% |
| KZ displacements (%) | 21.9% | 20.8% | 22.3% | 22.5% | 20.7% |
| Replicated patterns | 4 | 0 | 0 | 0 | 0 |
| Candidate edges | 3 | 0 | 0 | 3 | 3 |
| Pullback rate | 69.5% | 76.0% | 75.1% | 71.7% | 72.7% |
| Pullback timing (min) | 36 | 34 | 33 | 33 | 33 |
| Pullback depth | 62% | 59% | 61% | 58% | 62% |
| Pre-screen pass rate | 5% | 5% | 4% | 8% | 5% |
| Direction balance | 96.4/3.6 | 46.4/53.6 | 45.5/54.5 | 88.9/11.1 | 82.1/17.9 |
| **VERDICT** | **YELLOW** | **YELLOW** | **YELLOW** | **YELLOW** | **YELLOW** |
| Score | 18.4 | 10.7 | 10.7 | 10.5 | 10.6 |

## EURUSD Deep Dive (YELLOW)

**Verdict:** YELLOW — 0 patterns replicated, OB retest 87%
**Score:** 10.7

### Displacement Summary
- Total: 7,859 (297/month)
- Baseline 3h continuation: 48.6%
- FVG creation rate: 57.1%
- KZ displacements: 20.8%
- Direction: 3926 bull / 3933 bear

### Session Continuation Rates
| Session | 3h Cont |
|---------|---------|
| asian | 48.1% |
| late | 41.6% |
| london | 49.9% |
| ny | 48.4% |

### Combination Results
| Pattern | Disc n | Disc 3h | Val n | Val 3h | Replicated? |
|---------|--------|---------|-------|--------|-------------|
| FVG+LowWick+Align>=2 | 134 | 57.5% | 142 | 54.2% | no |
| 1st+KZ+Align>=2 | 57 | 50.9% | 47 | 44.7% | no |
| Sweep+1st+Align>=2 | 183 | 50.8% | 191 | 47.1% | no |
| Sweep+FVG+KZ | 422 | 48.3% | 470 | 52.1% | no |
| Sweep+FVG+Align>=3 | 22 | 45.5% | 26 | 50.0% | no |
| FVG+Align>=3 | 22 | 45.5% | 27 | 51.9% | no |
| Sweep+Align>=3 | 44 | 45.5% | 49 | 51.0% | no |
| KZ+Align>=3 | 11 | 0.0% | 7 | 0.0% | no |

### OB Retest
- Pullback rate (continuing disps): 76.0%
- Avg timing: 34 min
- Avg depth: 59%
- OB retest rate: disc=87.3%, val=86.1%

### Pre-Screen Calibration
- Pass rate: 5% (28/586 weekdays)
- Direction: 46.4/53.6 (bull/bear)
- Fail: D1 unclear=409, H4 mismatch=140

### Asian Sweep Validity
- Asian level sweeps in London: 913
- Continuation rate after Asian sweep: 50.2%

### Exhaustion Pattern
| Position | n | 3h Cont |
|----------|---|---------|
| 1st | 1735 | 48.2% |
| 2nd | 1153 | 48.8% |
| 3rd+ | 1080 | 48.9% |

### Recommended Parameters
- Equal tolerance: 0.000166 (1.7 pips)
- Round number step: 0.01
- M15 ATR median: 0.000520 (5.2 pips)

## GBPUSD Analysis (YELLOW)

**Verdict:** YELLOW — 0 patterns replicated, OB retest 87%
**Score:** 10.7

### Displacement Summary
- Total: 7,828 (296/month)
- Baseline 3h continuation: 48.7%
- FVG creation rate: 57.8%
- KZ displacements: 22.3%
- Direction: 3952 bull / 3876 bear

### Session Continuation Rates
| Session | 3h Cont |
|---------|---------|
| asian | 47.2% |
| late | 36.9% |
| london | 51.2% |
| ny | 48.7% |

### Combination Results
| Pattern | Disc n | Disc 3h | Val n | Val 3h | Replicated? |
|---------|--------|---------|-------|--------|-------------|
| Sweep+FVG+KZ | 482 | 54.1% | 506 | 54.2% | no |
| FVG+LowWick+Align>=2 | 137 | 48.2% | 151 | 51.7% | no |
| Sweep+1st+Align>=2 | 201 | 43.8% | 221 | 45.7% | no |
| 1st+KZ+Align>=2 | 67 | 41.8% | 68 | 42.6% | no |
| Sweep+FVG+Align>=3 | 6 | 0.0% | 18 | 0.0% | no |
| FVG+Align>=3 | 7 | 0.0% | 20 | 40.0% | no |
| Sweep+Align>=3 | 12 | 0.0% | 32 | 37.5% | no |
| KZ+Align>=3 | 3 | 0.0% | 12 | 0.0% | no |

### OB Retest
- Pullback rate (continuing disps): 75.1%
- Avg timing: 33 min
- Avg depth: 61%
- OB retest rate: disc=86.7%, val=86.0%

### Pre-Screen Calibration
- Pass rate: 4% (22/586 weekdays)
- Direction: 45.5/54.5 (bull/bear)
- Fail: D1 unclear=412, H4 mismatch=143

### Asian Sweep Validity
- Asian level sweeps in London: 925
- Continuation rate after Asian sweep: 52.3%

### Exhaustion Pattern
| Position | n | 3h Cont |
|----------|---|---------|
| 1st | 1710 | 47.3% |
| 2nd | 1142 | 49.5% |
| 3rd+ | 1027 | 50.1% |

### Recommended Parameters
- Equal tolerance: 0.000201 (2.0 pips)
- Round number step: 0.01
- M15 ATR median: 0.000660 (6.6 pips)

## NAS100 Analysis (YELLOW)

**Verdict:** YELLOW — 0 patterns replicated, OB retest 85%
**Score:** 10.5

### Displacement Summary
- Total: 6,953 (298/month)
- Baseline 3h continuation: 47.4%
- FVG creation rate: 59.7%
- KZ displacements: 22.5%
- Direction: 3471 bull / 3482 bear

### Session Continuation Rates
| Session | 3h Cont |
|---------|---------|
| asian | 44.1% |
| late | 44.9% |
| london | 48.2% |
| ny | 48.2% |

### Combination Results
| Pattern | Disc n | Disc 3h | Val n | Val 3h | Replicated? |
|---------|--------|---------|-------|--------|-------------|
| FVG+Align>=3 | 28 | 60.7% | 56 | 44.6% | no |
| Sweep+FVG+Align>=3 | 27 | 59.3% | 53 | 45.3% | no |
| Sweep+Align>=3 | 34 | 58.8% | 86 | 45.3% | no |
| Sweep+FVG+KZ | 469 | 54.6% | 474 | 50.4% | no |
| FVG+LowWick+Align>=2 | 184 | 50.0% | 189 | 57.7% | no |
| Sweep+1st+Align>=2 | 177 | 49.2% | 251 | 53.8% | no |
| 1st+KZ+Align>=2 | 68 | 48.5% | 85 | 52.9% | no |
| KZ+Align>=3 | 8 | 0.0% | 13 | 0.0% | no |

### OB Retest
- Pullback rate (continuing disps): 71.7%
- Avg timing: 33 min
- Avg depth: 58%
- OB retest rate: disc=84.9%, val=85.0%

### Pre-Screen Calibration
- Pass rate: 8% (45/545 weekdays)
- Direction: 88.9/11.1 (bull/bear)
- Fail: D1 unclear=361, H4 mismatch=130

### Asian Sweep Validity
- Asian level sweeps in London: 619
- Continuation rate after Asian sweep: 50.6%

### Exhaustion Pattern
| Position | n | 3h Cont |
|----------|---|---------|
| 1st | 1423 | 46.8% |
| 2nd | 940 | 47.8% |
| 3rd+ | 1116 | 47.8% |

### Recommended Parameters
- Equal tolerance: 7.869338 (78.7 pts)
- Round number step: 100.0
- M15 ATR median: 20.800000 (208.0 pts)

## XAGUSD Analysis (YELLOW)

**Verdict:** YELLOW — 0 patterns replicated, OB retest 86%
**Score:** 10.6

### Displacement Summary
- Total: 7,695 (302/month)
- Baseline 3h continuation: 48.8%
- FVG creation rate: 54.2%
- KZ displacements: 20.7%
- Direction: 3814 bull / 3881 bear

### Session Continuation Rates
| Session | 3h Cont |
|---------|---------|
| asian | 47.2% |
| late | 51.5% |
| london | 49.0% |
| ny | 49.7% |

### Combination Results
| Pattern | Disc n | Disc 3h | Val n | Val 3h | Replicated? |
|---------|--------|---------|-------|--------|-------------|
| FVG+Align>=3 | 39 | 69.2% | 20 | 55.0% | no |
| Sweep+FVG+Align>=3 | 36 | 66.7% | 19 | 0.0% | no |
| FVG+LowWick+Align>=2 | 153 | 59.5% | 123 | 56.9% | no |
| Sweep+Align>=3 | 68 | 55.9% | 32 | 59.4% | no |
| Sweep+FVG+KZ | 438 | 53.4% | 398 | 52.8% | no |
| Sweep+1st+Align>=2 | 217 | 52.1% | 185 | 54.1% | no |
| 1st+KZ+Align>=2 | 75 | 49.3% | 65 | 50.8% | no |
| KZ+Align>=3 | 14 | 0.0% | 5 | 0.0% | no |

### OB Retest
- Pullback rate (continuing disps): 72.7%
- Avg timing: 33 min
- Avg depth: 62%
- OB retest rate: disc=85.8%, val=85.8%

### Pre-Screen Calibration
- Pass rate: 5% (28/583 weekdays)
- Direction: 82.1/17.9 (bull/bear)
- Fail: D1 unclear=405, H4 mismatch=141

### Asian Sweep Validity
- Asian level sweeps in London: 481
- Continuation rate after Asian sweep: 52.0%

### Exhaustion Pattern
| Position | n | 3h Cont |
|----------|---|---------|
| 1st | 1649 | 48.3% |
| 2nd | 1133 | 48.8% |
| 3rd+ | 1088 | 49.5% |

### Recommended Parameters
- Equal tolerance: 0.039303 (39.3 $)
- Round number step: 0.5
- M15 ATR median: 0.075000 (75.0 $)

## Correlation Matrix

| Pair | Correlation | Note |
|------|------------|------|
| EURUSD-GBPUSD | +0.795 | HIGH — reduce combined position |
| EURUSD-NAS100 | +0.064 | Low — good diversification |
| EURUSD-XAGUSD | +0.287 |  |
| GBPUSD-NAS100 | +0.207 |  |
| GBPUSD-XAGUSD | +0.324 |  |
| NAS100-XAGUSD | +0.273 |  |
| XAUUSD-EURUSD | +0.354 |  |
| XAUUSD-GBPUSD | +0.366 |  |
| XAUUSD-NAS100 | +0.159 | Low — good diversification |
| XAUUSD-XAGUSD | +0.765 | HIGH — reduce combined position |

## Expansion Plan

### Recommended Order of Deployment
1. **EURUSD** (YELLOW, score=10.7) — 0 patterns replicated, OB retest 87%
2. **GBPUSD** (YELLOW, score=10.7) — 0 patterns replicated, OB retest 87%
3. **XAGUSD** (YELLOW, score=10.6) — 0 patterns replicated, OB retest 86%
4. **NAS100** (YELLOW, score=10.5) — 0 patterns replicated, OB retest 85%

### Estimated Trade Frequency
| Instrument | Disps/month | KZ Disps/month | Est. Qualifying | Est. AI Trades/month |
|-----------|-------------|----------------|-----------------|---------------------|
| XAUUSD (LIVE) | 298 | 65 | 33 | 6.5 |
| EURUSD (YELLOW) | 297 | 62 | 31 | 6.2 |
| GBPUSD (YELLOW) | 296 | 66 | 33 | 6.6 |
| NAS100 (YELLOW) | 298 | 67 | 34 | 6.7 |
| XAGUSD (YELLOW) | 302 | 63 | 31 | 6.3 |

**Total estimated trades/month (GREEN+LIVE):** ~32
**Time to 20 demo trades:** ~1 months
