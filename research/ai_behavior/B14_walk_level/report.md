# B14 — Walk-Level vs Realized-R Systematic Study

_Generated: 2026-04-26T16:48:16+00:00_

**n_trades_total = 382** | **family_size = 8** (tested signals — Bonferroni denominator)

Memory `feedback_walk_level_evidence_not_predictive` recorded that walk-level statistical evidence does NOT translate into realized-R differences. B14 stress-tests the inverse: across the full family of walk-level signals, is there ANY where the walk-level partition ALSO partitions realized R AND the direction matches?

## Walk-level signal evaluation

| Signal | strata | min n | KW p (raw) | KW p (Bonferroni) | direction-consistent | status |
| --- | --- | --- | --- | --- | --- | --- |
| `ob_retest_distance_atr` | 1 | 1 | n/a | n/a | n/a | INSUFFICIENT_N |
| `fvg_overlap_pct` | 0 | 0 | n/a | n/a | n/a | INSUFFICIENT_N |
| `liquidity_proximity_atr` | 0 | 0 | n/a | n/a | n/a | INSUFFICIENT_N |
| `displacement_quality_score` | 0 | 0 | n/a | n/a | n/a | INSUFFICIENT_N |
| `bias_alignment` | 0 | 0 | n/a | n/a | n/a | INSUFFICIENT_N |
| `framework_id` | 1 | 1 | n/a | n/a | n/a | INSUFFICIENT_N |
| `regime_tag` | 1 | 75 | n/a | n/a | n/a | INSUFFICIENT_N |
| `touch_count` | 3 | 14 | 0.706 | 1 | **no** | NON_PREDICTIVE |
| `touch_count_max_mso` | 3 | 14 | 0.5719 | 1 | **no** | NON_PREDICTIVE |
| `session_id` | 3 | 23 | 0.6971 | 1 | n/a | NON_PREDICTIVE |
| `setup_grade` | 2 | 2 | 0.4774 | 1 | **no** | NON_PREDICTIVE |
| `h1_fvg_unfilled_count` | 2 | 4 | 0.9682 | 1 | yes | NON_PREDICTIVE |
| `m15_clv_current` | 3 | 18 | 0.13 | 1 | n/a | NON_PREDICTIVE |
| `m15_buy_fraction` | 3 | 15 | 0.08891 | 0.7112 | n/a | NON_PREDICTIVE |
| `unmitigated_ob_count` | 2 | 22 | 0.9572 | 1 | yes | NON_PREDICTIVE |

## Strategic verdict

Survivor signals: **0 / 15**

Most-predictive (smallest p): `m15_buy_fraction` (KW p_bonferroni = 0.7112, direction-consistent = n/a)

Reasoning: NO walk-level signal in this family survived the realized-R cross-check (KW p_bonferroni < 0.05 AND direction-consistent). Memory `feedback_walk_level_evidence_not_predictive` is REINFORCED — walk-level evidence remains a misleading prior for realized R. K54 (ML classifier training pipeline) should NOT use these walk-level signals as direct features without first validating on out-of-sample realized R.

## Per-signal stratum detail

### `ob_retest_distance_atr` — INSUFFICIENT_N

_only 1 stratum/strata with n>=10; observed: {'>=1.0': 10, '<0.3': 6, '0.3-0.6': 4, '0.6-1.0': 1}_

Walk-level ranking (best→worst): `0.3-0.6` → `<0.3` → `0.6-1.0` → `>=1.0`
Realized-R ranking (best→worst): `0.6-1.0` → `<0.3` → `>=1.0` → `0.3-0.6`

| Stratum | n | mean R | median R | WR | WR 95% CI | total R | rank (walk) | rank (real) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `0.6-1.0` | 1 | +1.500 | +1.500 | 100.0% | [0.21, 1.00] | +1.50 | 3 | 1 |
| `<0.3` | 6 | +0.667 | +1.500 | 66.7% | [0.30, 0.90] | +4.00 | 2 | 2 |
| `>=1.0` | 10 | +0.250 | +0.250 | 50.0% | [0.24, 0.76] | +2.50 | 4 | 3 |
| `0.3-0.6` | 4 | -1.000 | -1.000 | 0.0% | [0.00, 0.49] | -4.00 | 1 | 4 |

### `fvg_overlap_pct` — INSUFFICIENT_N

_only 0 stratum/strata with n>=10; observed: {}_

### `liquidity_proximity_atr` — INSUFFICIENT_N

_only 0 stratum/strata with n>=10; observed: {}_

### `displacement_quality_score` — INSUFFICIENT_N

_only 0 stratum/strata with n>=10; observed: {}_

### `bias_alignment` — INSUFFICIENT_N

_only 0 stratum/strata with n>=10; observed: {}_

### `framework_id` — INSUFFICIENT_N

_only 1 stratum/strata with n>=10; observed: {'ob_retest': 159, 'session_sweep': 1}_

Realized-R ranking (best→worst): `session_sweep` → `ob_retest`

| Stratum | n | mean R | median R | WR | WR 95% CI | total R | rank (walk) | rank (real) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `session_sweep` | 1 | +3.030 | +3.030 | 100.0% | [0.21, 1.00] | +3.03 | — | 1 |
| `ob_retest` | 159 | +0.474 | +0.320 | 65.4% | [0.58, 0.72] | +75.29 | — | 2 |

### `regime_tag` — INSUFFICIENT_N

_only 1 stratum/strata with n>=10; observed: {'bullish': 75}_

Realized-R ranking (best→worst): `bullish`

| Stratum | n | mean R | median R | WR | WR 95% CI | total R | rank (walk) | rank (real) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `bullish` | 75 | +0.134 | -1.000 | 45.3% | [0.35, 0.57] | +10.02 | — | 1 |

### `touch_count` — NON_PREDICTIVE

_rank flip: walk['1'] vs realized['2']_

Walk-level ranking (best→worst): `1` → `2` → `>=3`
Realized-R ranking (best→worst): `2` → `>=3` → `1`

| Stratum | n | mean R | median R | WR | WR 95% CI | total R | rank (walk) | rank (real) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `2` | 25 | +0.300 | +1.500 | 52.0% | [0.33, 0.70] | +7.50 | 2 | 1 |
| `>=3` | 14 | +0.073 | -1.000 | 42.9% | [0.21, 0.67] | +1.02 | 3 | 2 |
| `1` | 32 | +0.016 | -1.000 | 40.6% | [0.26, 0.58] | +0.50 | 1 | 3 |

### `touch_count_max_mso` — NON_PREDICTIVE

_rank flip: walk['2'] vs realized['>=3']_

Walk-level ranking (best→worst): `1` → `2` → `>=3`
Realized-R ranking (best→worst): `1` → `>=3` → `2`

| Stratum | n | mean R | median R | WR | WR 95% CI | total R | rank (walk) | rank (real) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `1` | 14 | +0.429 | +1.500 | 57.1% | [0.33, 0.79] | +6.00 | 1 | 1 |
| `>=3` | 24 | +0.147 | -1.000 | 45.8% | [0.28, 0.65] | +3.52 | 3 | 2 |
| `2` | 37 | +0.014 | -1.000 | 40.5% | [0.26, 0.57] | +0.50 | 2 | 3 |

### `session_id` — NON_PREDICTIVE

_no a-priori walk-level direction_

Realized-R ranking (best→worst): `ny` → `london` → `tokyo`

| Stratum | n | mean R | median R | WR | WR 95% CI | total R | rank (walk) | rank (real) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ny` | 173 | +0.436 | +0.600 | 59.0% | [0.52, 0.66] | +75.50 | — | 1 |
| `london` | 186 | +0.403 | +0.365 | 60.2% | [0.53, 0.67] | +74.99 | — | 2 |
| `tokyo` | 23 | +0.196 | -1.000 | 47.8% | [0.29, 0.67] | +4.50 | — | 3 |

### `setup_grade` — NON_PREDICTIVE

_rank flip: walk['A+'] vs realized['A']_

Walk-level ranking (best→worst): `A+` → `A` → `B` → `C`
Realized-R ranking (best→worst): `A` → `A+`

| Stratum | n | mean R | median R | WR | WR 95% CI | total R | rank (walk) | rank (real) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `A` | 35 | +0.631 | +0.470 | 71.4% | [0.55, 0.84] | +22.10 | 2 | 1 |
| `A+` | 345 | +0.391 | +0.520 | 58.0% | [0.53, 0.63] | +134.89 | 1 | 2 |
| `B` | 2 | -1.000 | -1.000 | 0.0% | [0.00, 0.66] | -2.00 | 3 | 3 |

### `h1_fvg_unfilled_count` — NON_PREDICTIVE

Walk-level ranking (best→worst): `>=7` → `3-6` → `0-2`
Realized-R ranking (best→worst): `>=7` → `3-6`

| Stratum | n | mean R | median R | WR | WR 95% CI | total R | rank (walk) | rank (real) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `>=7` | 32 | +0.172 | -1.000 | 46.9% | [0.31, 0.64] | +5.50 | 1 | 1 |
| `3-6` | 39 | +0.154 | -1.000 | 46.2% | [0.32, 0.61] | +6.02 | 2 | 2 |
| `0-2` | 4 | -0.375 | -1.000 | 25.0% | [0.05, 0.70] | -1.50 | 3 | 3 |

### `m15_clv_current` — NON_PREDICTIVE

_no a-priori walk-level direction_

Realized-R ranking (best→worst): `mid` → `lower-third` → `upper-third`

| Stratum | n | mean R | median R | WR | WR 95% CI | total R | rank (walk) | rank (real) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `mid` | 25 | +0.501 | +1.500 | 60.0% | [0.41, 0.77] | +12.52 | — | 1 |
| `lower-third` | 18 | +0.111 | -1.000 | 44.4% | [0.25, 0.66] | +2.00 | — | 2 |
| `upper-third` | 32 | -0.141 | -1.000 | 34.4% | [0.20, 0.52] | -4.50 | — | 3 |

### `m15_buy_fraction` — NON_PREDICTIVE

_no a-priori walk-level direction_

Realized-R ranking (best→worst): `bear` → `bull` → `balanced`

| Stratum | n | mean R | median R | WR | WR 95% CI | total R | rank (walk) | rank (real) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `bear` | 21 | +0.310 | +1.500 | 52.4% | [0.32, 0.72] | +6.50 | — | 1 |
| `bull` | 39 | +0.283 | +1.500 | 51.3% | [0.36, 0.66] | +11.02 | — | 2 |
| `balanced` | 15 | -0.500 | -1.000 | 20.0% | [0.07, 0.45] | -7.50 | — | 3 |

### `unmitigated_ob_count` — NON_PREDICTIVE

Walk-level ranking (best→worst): `>=3` → `1-2` → `0`
Realized-R ranking (best→worst): `>=3` → `1-2`

| Stratum | n | mean R | median R | WR | WR 95% CI | total R | rank (walk) | rank (real) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `>=3` | 22 | +0.136 | -1.000 | 45.5% | [0.27, 0.65] | +3.00 | 1 | 1 |
| `1-2` | 53 | +0.132 | -1.000 | 45.3% | [0.33, 0.59] | +7.02 | 2 | 2 |

## K54 handoff

No survivors. K54 should NOT add these walk-level signals as direct features without first validating against out-of-sample realized R (per memory `feedback_walk_level_evidence_not_predictive`).

