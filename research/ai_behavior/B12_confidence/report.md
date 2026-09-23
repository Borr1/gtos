# B12 — Confidence Scorer Deep Autopsy

_Generated: 2026-04-26T16:49:13+00:00_

## Confidence distribution

- n trades evaluated: 312
- Trades scanned (loader): 338
- Mean: 76.19
- Mode: 72 (frequency 36.2%)
- At confidence=80: 21.5%

### Histogram

| Confidence | Count |
| --- | --- |
| 68 | 1 |
| 72 | 113 |
| 75 | 35 |
| 78 | 77 |
| 80 | 67 |
| 82 | 13 |
| 85 | 6 |

## Predictive conditionals (|rho| >= 0.20 AND p_corrected < 0.05 AND n >= 20)

_No stratum met all three thresholds._

## Family + methodology

- Stratification axes: symbol, regime, kill_zone, framework, setup_grade
- Strata tested (Bonferroni family): 8
- Total strata observed: 21
- min_n = 20
- alpha (after Bonferroni) = 0.05
- |rho| threshold = 0.2
- Permutation count = 1000 (seed=1)

## Strategic verdict

Predictive conditionals found: 0
Most predictive: n/a

Reasoning: zero strata cleared the predictive bar after Bonferroni correction across the tested family. This corroborates the headline CLAUDE.md finding that the AI's `confidence_score` is a rubber stamp — its variance across strata is too small to discriminate winners from losers. `confidence_filter_mode: shadow` should remain in shadow, and any future hard filter on the scorer requires a fresh data collection (not a re-stratification of the same trades). K54 feature engineering should treat confidence_score as a noise feature.

## All tested strata

| Stratum | n | rho | raw p | corrected p | flag |
| --- | --- | --- | --- | --- | --- |
| framework=ob_retest | kill_zone=None | regime=None | setup_grade=a+ | symbol=xauusd | 58 | -0.002 | 0.9950 | 1.0000 | NOT_PREDICTIVE |
| framework=ob_retest | kill_zone=ny | regime=None | setup_grade=a+ | symbol=xauusd | 25 | +0.078 | 0.7872 | 1.0000 | NOT_PREDICTIVE |
| framework=ob_retest | kill_zone=london | regime=None | setup_grade=a+ | symbol=xauusd | 23 | -0.408 | 0.0829 | 0.6633 | NOT_PREDICTIVE |
| framework=ob_retest | kill_zone=london | regime=None | setup_grade=a+ | symbol=xagusd | 22 | -0.207 | 0.4106 | 1.0000 | NOT_PREDICTIVE |
| framework=ob_retest | kill_zone=None | regime=None | setup_grade=a | symbol=xauusd | 22 | +0.124 | 0.5804 | 1.0000 | NOT_PREDICTIVE |
| framework=ob_retest | kill_zone=ny | regime=None | setup_grade=a+ | symbol=xagusd | 22 | +0.040 | 0.8711 | 1.0000 | NOT_PREDICTIVE |
| framework=ob_retest | kill_zone=ny | regime=None | setup_grade=a+ | symbol=ger40 | 21 | +0.262 | 0.2607 | 1.0000 | NOT_PREDICTIVE |
| framework=ob_retest | kill_zone=london | regime=None | setup_grade=a+ | symbol=ger40 | 20 | +0.064 | 0.7942 | 1.0000 | NOT_PREDICTIVE |

