# F4 — Fresh OB-zone Test A Re-test on H2-2026 Data

**Module:** `src/research_infra/ob_zone_test.py`
**Driver:** `scripts/research/run_f4_ob_zone_fresh.py`
**Tests:** `tests/research_infra/test_ob_zone_test.py`
**Output:** `research/edge_decomposition/F4_ob_zone_fresh_test_a/{population.jsonl, results.json, report.md}`
**Family size (Bonferroni):** 5 (matches K52 canonical)

---

## Why this exists

K52 (`research/edge_decomposition/K52_survival/report.md`, commit `7a68d1b`,
2026-04-26) re-tested the five Bonferroni-surviving baseline findings from
CLAUDE.md against the current 2-year dataset. The "OB zone advantage +17pp"
finding produced verdict `SURVIVES` (corrected p = 0.0116).

But K52 reused the **cached** Test A inputs literally from
`.context/03_analysis/test_a_rerun_real_bos_results.md`:

```
TEST_A_RERUN_OB_WINS = 122
TEST_A_RERUN_OB_N    = 173
TEST_A_RERUN_BASE_WINS = 73
TEST_A_RERUN_BASE_N  = 136
```

Those numbers come from a 2024-04 → 2026-03-13 batch of 219 BOS events
(174 trading days). The K52 verdict tells us: *under K52's standardised
pooled-z test, that historical 219-event population still rejects H0*.
It does NOT tell us whether the OB-zone advantage **still holds on a
freshly extracted H2-2026 population**, which is the strategic question
behind the open CLAUDE.md unresolved item #4 (XAUUSD H1→H2 2026 WR decay).

F4 closes that gap.

## What F4 does

For the 2026-01-01 → 2026-04-24 window (the H2-2026 data we have available
under `data/historical_2026/`), per instrument:

1. **Re-derive BOS events from raw H1 OHLCV** — no cached inputs. Uses
   the same swing detection + structure classifier + BOS rule as
   `src/components/market_state.py`:
   - Swings: fractal high/low requiring strict dominance over 2 bars
     each side.
   - Structure: rolling classifier on the most-recent 4 swings (HH+HL
     vs LH+LL net score, with bull/bear ≥ 2 net required to leave
     transitional).
   - BOS: candle close exceeds the most-recent same-direction swing.
     Each level consumed once.
2. **Compute mechanical OB-retest entry** at each BOS:
   - OB = last opposing-side candle within 10 bars before the BOS.
   - Entry = 80% retrace into the OB (canonical).
   - SL = beyond the OB extreme by `max(0.25 × ATR_14, 5 × tick_size)`.
   - TP = `entry + 1.5 × |entry - SL|` (min_rr floor).
3. **Compute mechanical generic-pullback entry** at the same BOS:
   - Entry = 50% Fibonacci retrace of the impulse (`anchor_swing →
     bos_close`).
   - SL = beyond the impulse anchor by the same buffer formula.
   - TP = `entry + 1.5 × |entry - SL|`.
4. **Resolve outcomes via M15 walk-forward** through
   `src.research_infra.dumb_baseline.resolve_mechanical_outcome`:
   - Two-stage: wait for fill (limit-order semantics), then watch for
     TP / SL.
   - SL-first conservative rule on both-hit bars.
   - Same-bar fill+TP/SL → `SAME_BAR`, excluded from WR (no
     microstructure visibility).
   - Hard 24h hold ceiling (96 M15 bars).
5. **Aggregate per-period**: Full window / H1-2026 (Jan-Feb) /
   H2-2026 (Mar-Apr) / per-instrument.
6. **Apply pooled-variance two-proportion z-test** + Bonferroni at
   family size 5 to each period.
7. **Emit verdict** for the H2-2026 row.

## Comparison to original Test A baseline + K52 cached re-test

| Source | Population | n | OB WR | Baseline WR | Δpp | Raw p | Corrected p (k=5) |
|---|---|---|---|---|---|---|---|
| Original Test A (2024) | 2024-04 → 2026-03 batch | 219 BOS | 70.5% (122/173) | 53.7% (73/136) at 80% retrace | +16.8pp | 0.003 (Fisher) | 0.015 |
| K52 cached re-test (2026-04-26) | SAME 219 BOS | 309 (counts) | 70.5% (122/173) | 53.7% (73/136) | +16.8pp | 0.0023 (pooled-z) | **0.0116** |
| **F4 fresh (this module)** | 2026-01-01 → 2026-04-24 raw H1 | TBD | TBD | TBD (50% Fibonacci) | TBD | TBD | TBD |

Differences vs original Test A worth flagging:

- **Test geometry — 80% vs 50% retrace baseline.** The original Test A
  used "80% retrace" where the *entry* was 80% of the impulse range from
  the impulse origin (a SHALLOW entry from origin = deep retrace from
  the impulse end). F4 uses 50% Fibonacci retrace of the impulse anchor
  → BOS close, which is a more standard SMC definition. The
  "generic deep pullback" concept is preserved, but the absolute baseline
  WR may differ. CLAIM: F4 is a stricter test (deeper, more standard
  baseline), so a SURVIVES_FRESH verdict here is *stronger* than the
  original.
- **Fisher exact vs pooled-z.** F4 uses pooled-variance two-proportion
  z-test for direct comparability with K52. Fisher exact and pooled-z
  agree well at n > 30; small-n cases may diverge.
- **No simulation-calibration adjustment.** The original Test A reported
  a +12.6pp "simulation gap" (real WR < sim WR by ~13pp because the
  H1 sim was too generous). F4 does NOT calibrate because both arms
  use identical M15 walk-forward — the calibration cancels in the
  delta.

## Verdict format

The F4 report.md emits this block:

```
## Fresh OB-zone Test A (H2-2026 data, post-7d48001 main)

| Period | n_bos | OB retest WR | Generic pullback WR | Δpp | corrected p |
| Full | ... | ... | ... | ... | ... |
| H1-2026 only | ... | ... | ... | ... | ... |
| H2-2026 only | ... | ... | ... | ... | ... |

## Strategic verdict
- Original Test A: +17pp (corrected p=0.003, n=219)
- K52 cached re-test: +16.8pp (corrected p=0.0116, n=309 — SAME population as Test A)
- F4 fresh H2-2026: <pp> (corrected p=<p>, n=<n>)
- Status: <SURVIVES_FRESH | DECAYED_FRESH | INCONCLUSIVE_FRESH_SAMPLE>
- Reasoning: <2-4 sentences>
```

Status decision rule (applied to the H2-2026 row):

- `SURVIVES_FRESH` — corrected p < 0.05 AND `delta_pp ≥ +5pp` AND
  per-arm n ≥ 30.
- `DECAYED_FRESH` — corrected p ≥ 0.05 OR `delta_pp < +5pp`, with n
  above the floor.
- `INCONCLUSIVE_FRESH_SAMPLE` — per-arm n < 30 (insufficient sample
  for a verdict).

## K52 update implications

| F4 status | What CLAUDE.md should say | What K52 narrative should add |
|---|---|---|
| `SURVIVES_FRESH` | OB zone advantage holds on fresh H2-2026 data — keep "+17pp survives Bonferroni" in Validated Numbers | K52 cached SURVIVES re-confirmed by F4 fresh re-extract; +17pp is durable, not sample-bound |
| `DECAYED_FRESH` | Move "OB zone advantage" to "DECAYED on H2-2026" footnote — keep the original +17pp claim with quarterly-decay caveat | K52's cached SURVIVES reflects pre-2026 sample; the original signal has decayed in current regime |
| `INCONCLUSIVE_FRESH_SAMPLE` | No CLAUDE.md change yet — the H2-2026 sample is too small to update Validated Numbers | Re-run F4 quarterly as new data accumulates |

A `DECAYED_FRESH` outcome would NOT invalidate K52 — K52 honestly tested
the cached population. F4 + K52 together describe a richer story: "the
historical OB-zone signal was real (K52 SURVIVES on the population that
minted it); whether it has decayed on current data is F4's business."

## Out of scope

- **Multi-framework comparison.** F4 specifically re-tests the OB-zone
  advantage finding (the canonical Test A Q2). FVG / breaker / etc.
  comparisons live in K50 / B-track research.
- **Pre-2026 fresh re-extract.** The 2024-2025 portion of K52's cached
  numbers is already covered. F4 focuses on the H2-2026 decay window.
- **Realised AI-R join.** F4 is mechanical-vs-mechanical (OB vs generic)
  — same as the original Test A Q2. AI-vs-mechanical comparison is
  A1 / B12 / K50 territory.

## How to run

```bash
# Default (all 7 instruments, full 2026 window, write to canonical dir)
python scripts/research/run_f4_ob_zone_fresh.py

# Filter
python scripts/research/run_f4_ob_zone_fresh.py \
    --output-dir /tmp/f4 \
    --instruments XAUUSD,GBPUSD \
    --start 2026-03-01 --end 2026-04-24

# Dry-run (no writes; prints plan)
python scripts/research/run_f4_ob_zone_fresh.py \
    --output-dir /tmp/scratch --dry-run
```

No API calls. No environment variables required. Phase 1 = $0.

## Test contract

`tests/research_infra/test_ob_zone_test.py` — 12+ tests covering:

1. BOS detection on synthetic bullish OHLCV (sanity: no exception, field
   shape).
2. BOS detection on inverted OHLCV (mirror — non-LONG breaks).
3. Flat OHLCV → no BOS.
4. Missing CSV → empty list.
5. OB retest TP-hit on hand-priced LONG synthetic M15.
6. OB retest SL-hit on hand-priced LONG synthetic M15.
7. Generic pullback entry geometry (50% Fibonacci) + TP-hit.
8. Generic pullback degenerate-impulse skip.
9. Generic pullback inverted-impulse skip.
10. End-to-end `run_test_a_fresh` on synthetic two-instrument fixture.
11. Period-status classification (INCONCLUSIVE / DECAYED / SURVIVES) on
    crafted outcome lists.
12. Serialization NaN replacement + JSON round-trip.
13. Bonferroni correction caps at 1.0; NaN pass-through.
14. CLI `--dry-run` exits 0 without writes.

All tests use `tmp_path` for isolation; no production paths touched.
