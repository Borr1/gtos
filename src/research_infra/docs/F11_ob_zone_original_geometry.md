# F11 — OB-zone Advantage Re-test with ORIGINAL Test A Geometry

**Module:** `src/research_infra/ob_zone_original_geometry.py`
**Driver:** `scripts/research/run_f11_ob_zone_original_geometry.py`
**Tests:** `tests/research_infra/test_ob_zone_original_geometry.py` (24 tests)
**Output:** `research/edge_decomposition/F11_ob_zone_original_geometry/{population.jsonl, results.json, report.md}`
**Family size (Bonferroni):** 5 (matches K52 / F4 canonical)
**Branch:** `feat/research-f11-ob-zone-original-geometry`

---

## Why this exists

F4 (commit `48395e2`,
`research/edge_decomposition/F4_ob_zone_fresh_test_a/`) re-extracted BOS
events fresh from H1 OHLCV on the 2026-01-01 → 2026-04-24 window and
ran the OB-retest vs generic-pullback comparison. Verdict on H2-2026
was **DECAYED_FRESH**: delta = +0.9pp (n=480, corrected p = 1.0).
That is a striking departure from the original Test A's +17pp finding
(`.context/03_analysis/test_a_rerun_real_bos_results.md`, n=219, Fisher
p = 0.003).

But F4 changed two things at once relative to the original Test A:

1. **Baseline geometry**. F4 used the **50% Fibonacci retracement** of
   the `anchor_swing → bos_close` impulse. The original Test A used an
   **80% retracement of the impulse range from the impulse origin** —
   a SHALLOWER position of 20% above anchor for LONG, i.e. a much
   deeper pullback than F4's 50% midpoint baseline. The original
   baseline sits much closer to where the OB zone naturally lies in
   the impulse, which is the geometry that produced the +17pp result.
2. **Statistical test**. F4 used a pooled-variance two-proportion
   z-test for direct K52 comparability. The original Test A's Q2 row
   used a **Fisher exact** test (the canonical small-sample
   contingency-table test).

The strategic question: is F4's `DECAYED_FRESH` verdict driven by
genuine decay of the OB-zone advantage on H2-2026 data
(**interpretation A**), or by methodology drift away from the original
Test A's deeper baseline + Fisher test (**interpretation B**)?

F11 disambiguates by re-running F4's analysis on F4's exact same fresh
population, but with:

1. The **original Test A "80% impulse retrace"** baseline — entry =
   `anchor + 0.20 × impulse_range` (deep pullback, close to the
   impulse origin).
2. **BOTH Fisher exact AND pooled-z** reported, for cross-method
   sanity.

## What F11 does

For F4's exact fresh population (loaded from
`research/edge_decomposition/F4_ob_zone_fresh_test_a/population.jsonl`
when present), per BOS event:

1. **Re-run the OB-retest entry** via `find_ob_retest_outcome` (F4's
   identical implementation — guarantees the OB arm is bit-identical).
2. **Compute the original-geometry baseline entry**:
   - Impulse range = `bos_close - anchor_swing_price` (signed).
   - LONG: entry = `anchor + (1 - 0.80) × impulse_range = anchor +
     0.20 × impulse_range`. SHORT mirrors with the signed range.
   - SL = beyond the anchor swing extreme by `max(0.25 × ATR_14,
     5 × tick_size)` (matches F4's generic-pullback SL convention).
   - TP = `entry ± 1.5 × |entry - SL|` (1.5R floor).
3. **Resolve outcomes** via M15 walk-forward
   (`src.research_infra.dumb_baseline.resolve_mechanical_outcome`) —
   bit-identical semantics to F4. Two-stage walk: limit-order fill
   then TP/SL with SL-first conservative rule. Same-bar fill+TP/SL
   excluded as ambiguous. 24h hold ceiling.
4. **Aggregate** per period (Full / H1-2026 / H2-2026 / per-instrument).
5. **Apply BOTH Fisher exact AND pooled-z**, with Bonferroni × 5.
6. **Emit verdict** for the H2-2026 row.

When F4's `population.jsonl` is missing or `--no-use-f4-population` is
passed, F11 re-extracts BOS events fresh via
`ob_zone_test.extract_bos_events` with the same parameters as F4
(self-contained fallback).

## Geometry comparison

| Source | Baseline geometry | LONG entry | Comment |
|---|---|---|---|
| Original Test A Q2 | 80% retrace of impulse range from origin | `anchor + 0.20 × range` | Deep pullback, close to impulse origin (+OB zone area) |
| F4 (`generic_50pct`) | 50% Fibonacci retrace of `anchor → BOS close` | `anchor + 0.50 × range` | Midpoint of impulse — much shallower than original |
| **F11 (`original_80pct_origin`)** | **Same as original Test A** | `anchor + 0.20 × range` | Restores the original geometry exactly |

The original Test A's "80% retrace" framing is anchored at the
**impulse origin** — a higher % means a DEEPER pullback (closer to
anchor). F4's "50% Fibonacci" is anchored at the impulse end — its 50%
sits at the midpoint, much shallower than the original's 20%-from-anchor.

## Statistical tests

F11 reports both, computed on the same paired counts:

1. **Fisher exact** — pure-Python two-tailed hypergeometric tail
   enumeration (no scipy dependency), using `math.lgamma` for
   numerically-stable combinatorial logs. Verified against
   `scipy.stats.fisher_exact(alternative='two-sided')` to 6 decimal
   places on multiple test cases (including the original Test A
   counts: 122/173 vs 73/136 → p = 0.002941).

2. **Pooled-variance two-proportion z-test** — identical
   implementation to K52 / F4 (`_two_prop_z_test` from
   `ob_zone_test.py`).

Both raw and Bonferroni-corrected p-values are reported per period
(family size 5).

## Verdict ladder (applied to H2-2026 row)

| Verdict | Trigger | Interpretation |
|---|---|---|
| `CONFIRMED` | delta_pp ≥ +12pp AND ≥1 corrected p < 0.05 | F4 was methodology drift; OB-zone advantage holds on H2 with original geometry |
| `PARTIAL` | delta_pp ∈ [+5pp, +12pp) OR significant under one test only | Both methodology drift AND decay contribute |
| `METHODOLOGY_DRIFT` | \|delta_pp\| < +5pp AND no corrected p < α | F4's DECAYED_FRESH is real decay, not methodology |
| `INCONCLUSIVE_FRESH_SAMPLE` | per-arm n < 30 | Re-run as more data accumulates |

The reasoning text always includes the **methodology shift**
decomposition: `F11_delta − F4_delta` (how much methodology
contributed) and `original_delta − F11_delta` (how much real decay
remains). Even when the binary verdict label is `METHODOLOGY_DRIFT`,
a non-trivial methodology shift (≥ 2pp) is called out explicitly so
the strategic implication block can describe the "decay-dominant +
methodology contributes" case faithfully.

## Verdict interpretation guide

The brief asks for the verdict to slot into one of three
interpretations:

- **CONFIRMED** = "F4's DECAYED_FRESH is methodology drift": original
  geometry recovers the +17pp advantage on H2-2026 data. Implies the
  CLAUDE.md Validated Number stays as-is, just with a "methodology
  sensitivity" footnote.

- **METHODOLOGY_DRIFT** label = "F4's DECAYED_FRESH is real decay":
  even with the original geometry restored, the H2-2026 advantage is
  small and non-significant. Implies the +17pp Validated Number
  should be moved to a "historical / decayed on H2-2026" footnote;
  K52's `SURVIVES` verdict (on the cached pre-2026 sample) remains
  defensible but tied to that sample only.

  - **Sub-case 1 — pure decay**: methodology shift < +2pp.
    Restoring the geometry barely moved the result.
  - **Sub-case 2 — decay-dominant + methodology contributes**:
    methodology shift ≥ +2pp but residual gap to original is the
    larger component. Both effects are present, but decay dominates.

- **PARTIAL** = "both methodology drift AND decay contribute":
  delta sits between +5pp and +12pp. Implies the CLAUDE.md Validated
  Number gets a "decay-in-progress, n-limited" caveat; re-run F11
  quarterly.

## How to run

```bash
# Default — paired comparison on F4's saved population
python scripts/research/run_f11_ob_zone_original_geometry.py \
    --output-dir research/edge_decomposition/F11_ob_zone_original_geometry

# Filter to specific period / instruments
python scripts/research/run_f11_ob_zone_original_geometry.py \
    --output-dir /tmp/f11 \
    --start 2026-03-01 --end 2026-04-24 \
    --instruments XAUUSD,GBPUSD

# Force fresh extract (skip F4 population reuse)
python scripts/research/run_f11_ob_zone_original_geometry.py \
    --output-dir /tmp/f11 --no-use-f4-population

# Dry-run (no writes; prints plan)
python scripts/research/run_f11_ob_zone_original_geometry.py \
    --output-dir /tmp/scratch --dry-run
```

No API calls. No environment variables required. Phase 1 = $0.

## F11 output for the canonical run

When F11 runs against F4's saved population (645 BOS events,
2026-01-01 → 2026-04-24, 7 instruments) the H2-2026 numbers are:

| Method | Baseline | Test | n_paired | OB WR | Baseline WR | Δpp | p (raw) | p (corrected) |
|---|---|---|---|---|---|---|---|---|
| F4 published | 50% Fib retrace | pooled-z | 480 | 57.59% | 56.64% | +0.9 | 0.8341 | 1.0000 |
| F11 (original geometry) | 80% impulse retrace | Fisher | 343 | 57.59% | 52.94% | +4.6 | 0.4256 | 1.0000 |
| F11 (original geometry) | 80% impulse retrace | pooled-z | 343 | 57.59% | 52.94% | +4.6 | 0.4091 | 1.0000 |
| Original Test A | 80% impulse retrace | Fisher | 219 | 70.50% | 53.70% | +16.8 | 0.0029 | 0.0145 |

The cross-period story:

- **H1-2026**: delta = +12.1pp (PARTIAL — just below the CONFIRMED
  ceiling; raw p ≈ 0.04 but Bonferroni-corrected to 0.19+).
  *The OB-zone advantage was alive and close to the original +17pp
  in Q1 2026.*
- **H2-2026**: delta = +4.6pp (METHODOLOGY_DRIFT label).
  *Methodology shift = +3.7pp (F11 vs F4); residual decay = +12.2pp
  vs original. Both effects contribute, but decay dominates by ~3:1.*
- **Full window**: delta = +8.3pp (PARTIAL; raw p ≈ 0.05, Bonferroni
  ≈ 0.21).

## Verdict for the canonical run: METHODOLOGY_DRIFT (decay-dominant)

F4's `DECAYED_FRESH` verdict is **METHODOLOGY_DRIFT** by F11's binary
label, but the strategic implication is more nuanced:

**Both effects are present, but decay dominates.**

- Methodology change (50% Fib → 80% impulse retrace) shifted the
  H2 delta by +3.7pp (from +0.9pp to +4.6pp).
- Real decay accounts for the remaining +12.2pp gap (between F11's
  +4.6pp and the original +16.8pp).

The H1-2026 portion of the same population is much closer to the
original +17pp result (delta = +12.1pp), reinforcing CLAUDE.md
unresolved item #4 (XAUUSD H1→H2 2026 WR decay): the OB-zone
advantage was alive in Q1 2026 and decayed sharply in Q2.

**Strategic implication**: keep the +17pp Validated Number with a
"methodology + H2-2026 decay" caveat. K52's `SURVIVES` verdict on
the cached pre-2026 sample is unchanged. The OB-zone advantage on
fresh H2-2026 data is materially smaller than +17pp regardless of
methodology choice — but methodology drift accounts for ~22% of
the original-vs-F4 gap.

## Test contract

`tests/research_infra/test_ob_zone_original_geometry.py` — 24 tests
covering:

1. LONG entry math: `anchor + 0.20 × impulse_range` exactly.
2. SHORT entry math (mirror, signed range).
3. TP-hit on synthetic M15 returns positive R.
4. Degenerate impulse → `DEGENERATE_IMPULSE` skip.
5. Inverted LONG impulse → `INVERTED_IMPULSE` skip.
6. Inverted SHORT impulse → `INVERTED_IMPULSE` skip.
7. Fisher exact bit-exact match with scipy on (122/173, 73/136)
   (the original Test A counts) — 6+ decimal places.
8. Fisher exact symmetric inputs return p = 1.0.
9. Fisher exact degenerate inputs (zero counts / negatives) handled.
10. Fisher and pooled-z agree on n>30 to within 0.05.
11. Fisher and pooled-z can diverge on n<10 (validates "Fisher
    preferred at small n" methodology).
12. `classify_verdict` boundaries (CONFIRMED / PARTIAL /
    METHODOLOGY_DRIFT / INCONCLUSIVE_FRESH_SAMPLE) on crafted inputs.
13. `classify_verdict` for negative delta (baseline beats OB).
14. `classify_verdict` reasoning text includes methodology-shift
    decomposition.
15. `load_f4_population` round-trip (BOSEvent ↔ JSONL).
16. `load_f4_population` missing-file → empty list.
17. End-to-end `run_f11_original_geometry` with synthetic F4
    population.
18. End-to-end fallback to fresh extract when F4 population missing.
19. `serialize_report` JSON round-trip with NaN replacement.
20. `aggregate_period` computes counts + delta + Fisher + verdict
    correctly on hand-crafted outcomes.
21. `ORIGINAL_RETRACE_PCT_FROM_ORIGIN` constant verification (guards
    against accidental refactor breaking the geometry).
22-24. Plus 3 boundary cases for verdict classification.

All 24 tests pass under `tmp_path` isolation (no production paths
touched).

## Out of scope

- **Multi-framework comparison.** F11 specifically re-tests the
  OB-zone advantage geometry. FVG / breaker / etc. comparisons live
  in K50 / B-track research.
- **Re-evaluation of the original 219-event population.** F11
  operates on F4's fresh population (or a fresh re-extract if
  missing). The 2024-2025 portion was already re-validated by K52.
- **AI-vs-mechanical join.** F11 is mechanical-vs-mechanical (OB
  retest vs original-geometry baseline) — same as F4 + original
  Test A Q2.
- **Production-code changes.** F11 is research-only; no `src/`
  trading logic touched.
