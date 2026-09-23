# F4 — Fresh OB-zone Test A Re-test (H2-2026 Data)

_Generated: 2026-04-26T17:50:25.601838+00:00_
_Harness: F4-v1_

## Overview

K52 (commit `7a68d1b`, 2026-04-26) re-tested the +17pp OB-zone advantage finding from CLAUDE.md but reused the **cached** Test A inputs (n=219 BOS events from a 2024-04 → 2026-03 batch). The corrected p remained 0.0116 — but the population was unchanged. F4 closes that gap by re-deriving the BOS-event population fresh from raw H1 OHLCV on the H2-2026 decay window and re-running the Q2 comparison.

## Fresh OB-zone Test A (H2-2026 data, post-7d48001 main)

| Period | n_bos | OB retest WR | Generic pullback WR | Δpp | corrected p |
|---|---|---|---|---|---|
| Full | 645 | 56.95% (250/439) | 56.37% (283/502) | +0.6pp | 1.0000 |
| H1-2026 only | 332 | 56.28% (121/215) | 56.10% (138/246) | +0.2pp | 1.0000 |
| H2-2026 only | 313 | 57.59% (129/224) | 56.64% (145/256) | +0.9pp | 1.0000 |

## Strategic verdict

- Original Test A: +17pp (corrected p=0.003, n=219)
- K52 cached re-test: +16.8pp (corrected p=0.0116, n=309 — SAME population as Test A)
- F4 fresh H2-2026: +0.9pp (corrected p=1.0000, n=480)
- Status: DECAYED_FRESH
- Reasoning: OB-zone advantage has DECAYED on freshly-extracted H2-2026 data: delta = +0.9pp (corrected p = 1.0000, n_ob=224, n_gen=256) — either p-value is no longer significant under family size 5 or the delta has dropped below the +5pp floor. H1-2026 baseline delta = +0.2pp; full-window delta = +0.6pp. K52's cached SURVIVES verdict no longer holds on fresh H2 data — the +17pp OB-zone advantage is sample-bound to the pre-2026 batch.

## Per-period detail

### Full window — DECAYED_FRESH

- BOS events: 645
- OB retest: 250 / 439 = 56.95% (filled = 516)
- Generic 50% pullback: 283 / 502 = 56.37% (filled = 532)
- Delta: +0.6pp
- Raw p = 0.8595; corrected p = 1.0000 (Bonferroni × 5)
- Notes: Corrected p = 1 ≥ α = 0.05 AND delta = 0.6pp < floor +5.0pp.

### H1-2026 — DECAYED_FRESH

- BOS events: 332
- OB retest: 121 / 215 = 56.28% (filled = 251)
- Generic 50% pullback: 138 / 246 = 56.10% (filled = 262)
- Delta: +0.2pp
- Raw p = 0.9687; corrected p = 1.0000 (Bonferroni × 5)
- Notes: Corrected p = 1 ≥ α = 0.05 AND delta = 0.2pp < floor +5.0pp.

### H2-2026 — DECAYED_FRESH

- BOS events: 313
- OB retest: 129 / 224 = 57.59% (filled = 265)
- Generic 50% pullback: 145 / 256 = 56.64% (filled = 270)
- Delta: +0.9pp
- Raw p = 0.8341; corrected p = 1.0000 (Bonferroni × 5)
- Notes: Corrected p = 1 ≥ α = 0.05 AND delta = 0.9pp < floor +5.0pp.

## Per-instrument detail (full window)

| Instrument | n_bos | OB WR | Generic WR | Δpp | corrected p | Status |
|---|---|---|---|---|---|---|
| XAUUSD | 88 | 70.37% (38/54) | 65.67% (44/67) | +4.7pp | 1.0000 | DECAYED_FRESH |
| GBPUSD | 91 | 55.88% (38/68) | 51.35% (38/74) | +4.5pp | 1.0000 | DECAYED_FRESH |
| USDJPY | 106 | 55.41% (41/74) | 53.75% (43/80) | +1.7pp | 1.0000 | DECAYED_FRESH |
| GBPJPY | 89 | 56.06% (37/66) | 64.18% (43/67) | -8.1pp | 1.0000 | DECAYED_FRESH |
| US30_cash | 100 | 48.48% (32/66) | 48.15% (39/81) | +0.3pp | 1.0000 | DECAYED_FRESH |
| XAGUSD | 87 | 59.26% (32/54) | 63.08% (41/65) | -3.8pp | 1.0000 | DECAYED_FRESH |
| NAS100 | 84 | 56.14% (32/57) | 51.47% (35/68) | +4.7pp | 1.0000 | DECAYED_FRESH |

## Methodology

**BOS detection** (per instrument H1 OHLCV; mirrors `src/components/market_state.py`):

- Swings: fractal high/low requiring strict dominance over 2 bars on each side.
- Structure direction: rolling classifier on the most-recent 4 swings (HH+HL vs LH+LL net score).
- BOS event: candle close exceeds the most-recent swing in the structural direction. Each swing level consumed at most once.

**OB retest entry** (canonical 80% retrace into OB):

- OB = last opposing-side candle within 10 bars before the BOS (mirrors production `identify_order_blocks`).
- Entry = OB.low + 0.80 × (OB.high - OB.low) for LONG; OB.high - 0.80 × (OB.high - OB.low) for SHORT.
- SL buffer = max(0.25 × ATR_14, 5 × tick_size); SL = OB.low - buffer (LONG) / OB.high + buffer (SHORT).
- TP = entry ± 1.5 × |entry - SL| (min_rr floor).

**Generic pullback entry** (50% Fibonacci retrace):

- Entry = anchor swing price + 0.50 × (BOS close - anchor) for LONG; anchor + 0.50 × (BOS close - anchor) for SHORT (signed).
- SL = anchor swing price - buffer (LONG) / + buffer (SHORT). SL beyond the impulse origin matches the 'generic deep pullback' interpretation.
- TP = entry ± 1.5 × |entry - SL|.

**Outcome resolution**: walk-forward on M15 OHLCV via `src.research_infra.dumb_baseline.resolve_mechanical_outcome`. Two-stage walk: wait for fill (limit-order semantics), then watch for TP/SL with SL-first conservative rule. Same-bar fill+TP/SL excluded as ambiguous (no microstructure).

**Statistical test**: pooled-variance two-proportion z-test on (OB_wins / OB_resolved) vs (Generic_wins / Generic_resolved). Bonferroni at family size 5.

**Status decision rule**:

- `SURVIVES_FRESH` — corrected p < α = 0.05 AND delta_pp ≥ +5pp on H2-2026 (n_min per arm ≥ 30).
- `DECAYED_FRESH` — corrected p ≥ α OR delta_pp < +5pp.
- `INCONCLUSIVE_FRESH_SAMPLE` — n < n_min on H2-2026.

## Caveats

- **Different test from original Test A.** The original Test A (2024) used Fisher exact on a pre-AI sample. F4 uses pooled-z for direct K52 comparability; Fisher exact and pooled-z agree well at n > 30 but can disagree on small samples.
- **Different baseline geometry.** The original Test A (`.context/03_analysis/test_a_rerun_real_bos_results.md`) tested OB vs 80% retrace of the *impulse range estimated from entry / SL / Fibonacci %*. F4 tests OB vs 50% Fibonacci retracement of the *swing-anchor → BOS close* impulse — a more standard SMC definition. The 50% level is arithmetically deeper than 80% on the impulse range (because 80% retrace = 20% remaining = a shallower entry from the impulse origin); the 'generic deep pullback' framing is preserved.
- **No simulation calibration.** The original Test A reported a +12.6pp simulation gap (real WR < sim WR by ~13pp). F4 does not calibrate against AI-selected real fills because it tests a DIFFERENT comparison (OB vs generic pullback, both mechanical), where the calibration cancels.
- **n=309 in K52 cached vs F4 fresh n.** K52's n=309 came from the per-record OB structural backtest, not a re-extracted BOS-event tally. F4's n is the freshly-derived BOS count; compare to the original Test A n=219 (closer to the same geometry).
- **No realised-AI-R join.** F4 is mechanical-vs-mechanical (OB vs generic) — same as the original Test A Q2. The AI-vs-mechanical comparison lives in A1 dumb_baseline / B12 / K50; do not conflate.
- **Family size 5 is the K52 canonical.** F4's corrected p uses the same divisor so the verdict slots into the K52 narrative directly.
- **Period split: Jan-Feb 2026 = H1; Mar-Apr 2026 = H2.** Matches CLAUDE.md unresolved item #4 (XAUUSD H1→H2 2026 WR decay framing). H1_2026_END = 2026-03-01.

## Run parameters

- Output: `research\edge_decomposition\F4_ob_zone_fresh_test_a`
- OHLCV: `C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-a9ff98bca513a2483\data\historical_2026`
- Instruments: XAUUSD,GBPUSD,USDJPY,GBPJPY,US30_cash,XAGUSD,NAS100
- Window: 2026-01-01 → 2026-04-24
- Family size: 5
- α = 0.05
- n_min (per arm): 30
- Δpp floor: +5pp

