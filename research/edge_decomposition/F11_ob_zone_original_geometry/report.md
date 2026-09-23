# F11 — OB-zone Advantage Re-test with ORIGINAL Test A Geometry

_Generated: 2026-04-26T18:09:50.222267+00:00_
_Harness: F11-v1_

## Overview

F4 (`research/edge_decomposition/F4_ob_zone_fresh_test_a/`, commit `48395e2`) re-extracted BOS events fresh from H1 OHLCV and reported a **DECAYED_FRESH** verdict on H2-2026: delta = +0.9pp (corrected p = 1.0, n=480). That contrasts sharply with the original Test A's +17pp (Fisher p = 0.003, n=219 from `.context/03_analysis/test_a_rerun_real_bos_results.md`). F4 changed two things at once relative to the original:

1. **Baseline geometry**: 50%-Fibonacci of `anchor → BOS close` (F4) vs 80%-of-impulse-range retrace from origin (original).
2. **Statistical test**: pooled-z (F4, K52-comparable) vs Fisher exact (original Test A).

F11 re-runs F4's analysis on the SAME freshly-extracted population but with the original Test A's baseline geometry (deeper, closer to the impulse origin) AND BOTH Fisher exact + pooled-z reported. This isolates methodology drift as the explanatory variable.

## OB-zone advantage on H2-2026: methodology comparison

| Method | Baseline | Test | n_paired | OB WR | Baseline WR | Δpp | p (raw) | p (corrected) |
|---|---|---|---|---|---|---|---|---|
| F4 published | 50% Fib retrace | pooled-z | 480 | 57.59% | 56.64% | +0.9 | 0.8341 | 1.0000 |
| F11 (original geometry) | 80% impulse retrace | Fisher | 343 | 57.59% | 52.94% | +4.6pp | 0.4256 | 1.0000 |
| F11 (original geometry) | 80% impulse retrace | pooled-z | 343 | 57.59% | 52.94% | +4.6pp | 0.4091 | 1.0000 |
| Original Test A | 80% impulse retrace | Fisher | 219 | 70.50% | 53.70% | +16.8 | 0.0029 | 0.0145 |

## Verdict

- F4's "DECAYED_FRESH" verdict is: **METHODOLOGY_DRIFT**
- Reasoning: delta = +4.6pp within ±5pp AND no significant p (Fisher = 1, z = 1). Restoring the original baseline geometry did NOT recover the +16.8pp advantage. F4's DECAYED_FRESH verdict is supported — the OB-zone advantage has genuinely decayed on H2-2026 data, NOT explained away by methodology. Note: F11 still shifted the H2 delta by +3.7pp vs F4 — methodology DID contribute, but the residual decay (+12.2pp vs original) dominates. Methodology shift (F11 − F4) = +3.7pp; remaining decay vs original +16.8pp = +12.2pp.
- Decomposition: F4 H2 delta = +0.9pp; F11 H2 delta = +4.6pp; original Test A = +16.8pp.
  - Methodology shift (F11 − F4) = +3.7pp
  - Residual decay (original − F11) = +12.2pp

## Strategic implication

- Restoring the original Test A baseline geometry shifted the H2-2026 delta from F4's +0.9pp to +4.6pp — methodology DID contribute (+3.7pp), but the residual gap to the original +16.8pp (+12.2pp) is real decay. Both effects are present, but DECAY DOMINATES — the OB-zone advantage on H2-2026 data is materially smaller than the original +17pp regardless of methodology. Move the +17pp Validated Number to a 'historical / decayed on H2-2026' footnote with the methodology caveat; keep K52 SURVIVES tied to the pre-2026 sample.

## Cross-period context

- Full window: delta = +8.3pp (Fisher corrected p = 0.2493, z corrected p = 0.2095)
- H1-2026: delta = +12.1pp (Fisher corrected p = 0.2329, z corrected p = 0.1883)
- H2-2026: delta = +4.6pp (Fisher corrected p = 1.0000, z corrected p = 1.0000)

## Per-period detail

### Full window — PARTIAL

- BOS events: 645
- OB retest: 250 / 439 = 56.95% (filled = 516)
- Original-80%-origin baseline: 112 / 230 = 48.70% (filled = 382)
- Delta: +8.3pp
- Fisher exact: raw p = 0.0499, corrected p = 0.2493 (× 5)
- Pooled-z: raw p = 0.0419, corrected p = 0.2095 (× 5)
- Notes: delta = +8.3pp ≥ +5pp BUT no corrected p < α (0.05) — Fisher = 0.2493, z = 0.2095. Direction matches original Test A but not significant under family-size 5 correction; sample-size limited. Methodology shift (F11 − F4) = +7.3pp; remaining decay vs original +16.8pp = +8.5pp.

### H1-2026 — PARTIAL

- BOS events: 332
- OB retest: 121 / 215 = 56.28% (filled = 251)
- Original-80%-origin baseline: 49 / 111 = 44.14% (filled = 187)
- Delta: +12.1pp
- Fisher exact: raw p = 0.0466, corrected p = 0.2329 (× 5)
- Pooled-z: raw p = 0.0377, corrected p = 0.1883 (× 5)
- Notes: delta = +12.1pp ≥ +5pp BUT no corrected p < α (0.05) — Fisher = 0.2329, z = 0.1883. Direction matches original Test A but not significant under family-size 5 correction; sample-size limited. Methodology shift (F11 − F4) = +11.2pp; remaining decay vs original +16.8pp = +4.7pp.

### H2-2026 — METHODOLOGY_DRIFT

- BOS events: 313
- OB retest: 129 / 224 = 57.59% (filled = 265)
- Original-80%-origin baseline: 63 / 119 = 52.94% (filled = 195)
- Delta: +4.6pp
- Fisher exact: raw p = 0.4256, corrected p = 1.0000 (× 5)
- Pooled-z: raw p = 0.4091, corrected p = 1.0000 (× 5)
- Notes: delta = +4.6pp within ±5pp AND no significant p (Fisher = 1, z = 1). Restoring the original baseline geometry did NOT recover the +16.8pp advantage. F4's DECAYED_FRESH verdict is supported — the OB-zone advantage has genuinely decayed on H2-2026 data, NOT explained away by methodology. Note: F11 still shifted the H2 delta by +3.7pp vs F4 — methodology DID contribute, but the residual decay (+12.2pp vs original) dominates. Methodology shift (F11 − F4) = +3.7pp; remaining decay vs original +16.8pp = +12.2pp.

## Per-instrument detail (full window)

| Instrument | n_bos | OB WR | Baseline WR | Δpp | Fisher p | z p | Verdict |
|---|---|---|---|---|---|---|---|
| XAUUSD | 88 | 70.37% (38/54) | 64.29% (18/28) | +6.1pp | 1.0000 | 1.0000 | INCONCLUSIVE_FRESH_SAMPLE |
| GBPUSD | 91 | 55.88% (38/68) | 42.11% (16/38) | +13.8pp | 1.0000 | 0.8681 | PARTIAL |
| USDJPY | 106 | 55.41% (41/74) | 46.15% (18/39) | +9.3pp | 1.0000 | 1.0000 | PARTIAL |
| GBPJPY | 89 | 56.06% (37/66) | 56.76% (21/37) | -0.7pp | 1.0000 | 1.0000 | METHODOLOGY_DRIFT |
| US30_cash | 100 | 48.48% (32/66) | 41.18% (14/34) | +7.3pp | 1.0000 | 1.0000 | PARTIAL |
| XAGUSD | 87 | 59.26% (32/54) | 47.83% (11/23) | +11.4pp | 1.0000 | 1.0000 | INCONCLUSIVE_FRESH_SAMPLE |
| NAS100 | 84 | 56.14% (32/57) | 45.16% (14/31) | +11.0pp | 1.0000 | 1.0000 | PARTIAL |

## Methodology

**Population source**: `f4_jsonl` (loaded 645 BOS from `C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-a5b6dca64c9f969b1\research\edge_decomposition\F4_ob_zone_fresh_test_a\population.jsonl`)

**OB retest entry** (identical to F4):

- OB = last opposing-side candle within 10 bars before BOS.
- Entry = `OB.low + 0.80 × (OB.high - OB.low)` for LONG; mirrored for SHORT.
- SL = beyond the OB extreme by `max(0.25 × ATR_14, 5 × tick_size)`.
- TP = `entry + 1.5 × |entry - SL|`.

**Original-geometry baseline entry** (the F11 contribution):

- Anchor = swing low (LONG) or swing high (SHORT) before the BOS.
- Impulse range = `bos_close - anchor_swing_price` (signed).
- Entry = `anchor + (1 - 0.80) × impulse_range = anchor + 0.20 × impulse_range` — i.e. **80% retracement back from BOS close toward the anchor swing**, equivalent to a 20%-from-anchor entry. This matches the original Test A (`.context/03_analysis/test_a_rerun_real_bos_results.md` Q2).
- SL = beyond the anchor swing extreme by the same buffer formula as F4's `generic_50pct` arm.
- TP = `entry ± 1.5 × |entry - SL|`.

**Geometric note**: F4 used a 50%-Fibonacci entry (`anchor + 0.50 × impulse_range`); F11 uses a 20%-of-range entry (`anchor + 0.20 × impulse_range`). F11's entry is therefore **closer to the impulse origin** (deeper pullback) — this is the geometry that produced the original +17pp finding and is the geometry F4 implicitly drifted away from.

**Outcome resolution**: walk-forward on M15 OHLCV via `src.research_infra.dumb_baseline.resolve_mechanical_outcome` — bit-identical semantics to F4. Two-stage walk: limit-order fill then TP/SL with SL-first conservative rule. Hard 24h hold ceiling (96 M15 bars).

**Statistical tests**:

- **Fisher exact** (matches original Test A): pure-Python two-tailed hypergeometric tail enumeration, no scipy dependency. Bonferroni × 5.
- **Pooled-variance two-proportion z-test** (matches K52 / F4): identical implementation. Bonferroni × 5.

**Verdict decision rule** (applied to H2-2026 row):

- **CONFIRMED** — delta_pp ≥ +12pp AND ≥ 1 corrected p < α = 0.05.
- **PARTIAL** — delta_pp ∈ [+5pp, +12pp); methodology + decay both contribute.
- **METHODOLOGY_DRIFT** — |delta_pp| < 5pp AND no corrected p < α; F4's DECAYED_FRESH is real decay.
- **INCONCLUSIVE_FRESH_SAMPLE** — n_resolved < 30 per arm.

## Caveats

- **Same population guarantee.** When loaded from F4's `population.jsonl` (the default path), F11 scores the SAME BOS events F4 scored — only the baseline geometry and statistical test differ. This isolates methodology drift as the explanatory variable.
- **F4 OB-retest counts may differ trivially.** F4 logged OB-retest outcomes; F11 re-resolves them via the same code path (`find_ob_retest_outcome`). On the same population the counts are bit-identical; we re-run them to keep F11 self-contained.
- **Fisher exact symmetry convention.** This implementation uses the symmetric-around-mean two-tailed convention (matching `scipy.stats.fisher_exact(alternative='two-sided')`). Verified against scipy on (122/173, 73/136), (50/100, 50/100), and (8/10, 1/10) — exact agreement to 6 decimal places.
- **Bonferroni family size.** F11 uses the K52-canonical family size of 5 so corrected p is directly comparable to K52's SURVIVES verdict and F4's DECAYED_FRESH.
- **Geometry stricter than F4 baseline.** F11's entry (`anchor + 0.20 × impulse_range`) sits closer to the impulse origin than F4's (`anchor + 0.50 × impulse_range`). The original Test A's 80%-retrace baseline is THIS deeper level — F11 restores it. A `CONFIRMED` verdict here is a strong recovery of the original advantage.
- **Period split: H1_2026_END = 2026-03-01.** Matches F4 + CLAUDE.md unresolved item #4 (XAUUSD H1→H2 2026 WR decay framing).
- **No simulation calibration.** Both arms use identical M15 walk-forward; calibration cancels in the delta. Same caveat as F4.

## Run parameters

- Output: `research\edge_decomposition\F11_ob_zone_original_geometry`
- OHLCV: `C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-a5b6dca64c9f969b1\data\historical_2026`
- F4 population path: `C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-a5b6dca64c9f969b1\research\edge_decomposition\F4_ob_zone_fresh_test_a\population.jsonl`
- Use F4 population: yes
- Instruments: XAUUSD,GBPUSD,USDJPY,GBPJPY,US30_cash,XAGUSD,NAS100
- Window: 2026-01-01 → 2026-04-24
- Family size: 5
- α = 0.05
- n_min (per arm): 30
- Δpp partial floor / ceiling: +5pp / +12pp

