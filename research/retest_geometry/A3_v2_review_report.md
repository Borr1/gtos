# A3_v2 Cold Methodology Review

## Summary verdict

**SOUND with caveats.** A1_v2 correctly fixes the catastrophic v1 timing bug. All 121 emitted rows satisfy the strict temporal-ordering invariant `retest_ts > bos_confirm_ts` (min delta = 15 min). BOS-confirm derivation from production `OrderBlock.causing_bos_index` is correct: `causing_bos_index` is the H1 candle whose CLOSE confirmed the BOS (assigned in `src/components/market_state.py:430,455`), and `bos_confirm_ts = H1_open + 1h` correctly computes the H1 close. The classifier asserts the invariant before row creation (study.py:792-795) so a violating row cannot be silently emitted. Geometry B parameters extracted from `scripts/ob_retest_comprehensive.py` (XAUUSD `0.001*ob_low`, others `0.00015` absolute, target `1.5*sl_distance`, window 12) match Test A verbatim. 95 tests pass. Geom A combined 70.0% lands inside Test A's expected band (65-75%) — the v1 92.9% phantom signal is gone. The ONE residual issue is a survivorship-bias filter inherited from v1 (mitigation check uses EOD H1 lookahead) that silently drops 53-64% of unique OBs per symbol; this is the same bias Test A has, so v2 is internally consistent with Test A's baseline but is NOT a bias-free measurement. Live-period 0-alignment is a real artifact (off-by-one between live system's `candle_time` semantic and v2's `retest_ts`), not a coding error.

## Audit findings

### 1. Temporal-ordering enforcement — PASS

Verified empirically: 121/121 rows in `combined_retests.csv` satisfy `retest_ts > bos_confirm_ts`. Min delta = 15.0 min (=1 M15 candle), max = 5940 min, zero exact-equal rows, zero rows reversed. (See `scratch/a3_v2_check_temporal_ordering.py`.)

The assert fires in the classifier `_classify_and_measure` at study.py:792-795, BEFORE the dataclass is constructed and BEFORE `write_retest_csv` runs. AssertionError aborts the run. No silent emission path exists. If `bos_confirm_ts` is None, the row never reaches the classifier — `_detect_first_retest` would raise on `_parse_candle_time(None)` (caught by `except ValueError` returning None at study.py:518), or `detect_fresh_obs_on_date` skips OBs with `bos_idx is None` defensively (study.py:395). `OrderBlock.causing_bos_index` is typed `int` (non-optional) in `src/models/market_state_models.py:53`, so the None case is dead code in production.

The v2 invariant test at study.py:792 is reinforced by two unit tests (`test_temporal_invariant_rejects_retest_equal_to_bos_confirm`, `test_temporal_invariant_rejects_retest_before_bos_confirm`) plus a full-CSV invariant test (`test_output_csv_temporal_ordering_invariant_on_written_rows`). All pass.

### 2. BOS detection correctness — PASS

`identify_order_blocks` (src/components/market_state.py:380-461) assigns `causing_bos_index = break_idx`, where `break_idx` is the index of the H1 candle whose close confirmed the structure break (set in `detect_structure_breaks` line 333, `candle_index=i` for the candle being iterated whose `c["close"] > recent_high.price` for bullish). So `causing_bos_index` correctly points to the H1 that first closed beyond the swing.

For bullish OBs (last bearish H1 before upward BOS), the BOS H1 is the one whose close > prior swing high. v2's `bos_confirm_ts = h1_slice[bos_idx]["time"] + 1h` is the correct close timestamp. For bearish OBs the mirror holds (close < prior swing low). H1 candle "time" field comes from `parse_tradingview_csv` and is the OPEN time (verified by `test_bos_confirm_ts_is_h1_close_not_open` which asserts the delta from formation to bos_confirm is a multiple of 1 hour — open + 1h).

Since `60 = 4 * 15`, every H1 close lands on an M15 boundary — no off-by-one possible. v2's strict `>` then skips the M15 candle whose open equals the H1 close (correctly identifying it as the impulse-continuation candle, not a retest).

`OrderBlock.causing_bos_index` is set unconditionally in `identify_order_blocks` lines 430 and 455. Test `test_production_ob_exposes_causing_bos_index` confirms every detected OB has the attribute. The defensive `None` check in `detect_fresh_obs_on_date` is dead code in practice.

### 3. Detector strict `>` (not `>=`) — PASS

The decision is correct and ADR-compliant despite being SLIGHTLY stricter than ADR 003's literal "open >= bos_confirm_ts" wording.

ADR 003's spec said `open >= bos_confirm_ts`. A1_v2 strengthened to strict `>` because every H1 close lands on an M15 boundary, so an M15 with `open == bos_confirm_ts` is the very first candle of the BOS-impulse continuation. From a live-orchestrator perspective: when the system observes the BOS H1 close, the next decision point is the M15 that closes 15 min later. A1_v2's choice eliminates exactly one M15 candle per OB — semantically the right cut.

US30_cash 2026-04-01 worked example verified in `combined_retests.csv` row: `bos_confirm_ts=2026-04-01T00:00:00Z`, `retest_ts=2026-04-01T00:15:00Z`. Strict `>` skipped 00:00 (impulse continuation) and accepted 00:15 (first true retest opportunity). 8 rows in the CSV have `retest = bos + exactly 15 min`, confirming the strict cut is engaged on real data.

Caveat: this DOES skip retests where price re-entered the OB during the BOS-close M15 candle itself. Defensible (live-aligned), but a known data-loss point worth disclosing in the report. The current geometry_report.md mentions strict invariant in the trailing notes; consider adding a 1-line callout in the methodology section.

### 4. Twin-geometry invariant weakening — PASS (correctly weakened)

Empirical check (`scratch/a3_v2_twin_geom_sanity.py`):
- Geom A CONT, Geom B REV: 10 rows (Geom B's tighter SL hit before Geom A's wider SL)
- Geom A REV, Geom B CONT: 1 row (paradoxical at first glance)
- Geom A CONT, Geom B UNRESOLVED: 35 rows (Geom A's longer 12h horizon, Geom B's 3h ran out)
- Geom A UNRESOLVED, Geom B CONT: 0

The Geom A CONT + Geom B UNR cases (35) account for the bulk of the 70%/48.5% headline gap. The 10 A=CONT/B=REV cases are explained by Geom B's tighter SL.

The 1 paradox row is GBPUSD 2026-04-13T13:45:00Z: entry=1.34346, sl_b=1.34331, target_b=1.34369, mae_b=5.2 pips at j=0. The MAE > SL distance on the entry candle, but Test A's skip-entry-candle convention (`if j >= 1` at study.py:678, mirroring `for j in range(1, 13)` at ob_retest_comprehensive.py:537) means SL hits on the entry candle don't classify. By j=1 the high reached target_b. Geom A then walked 12h forward and eventually hit its wider SL. Self-consistent under both geometries' own rules. ADR 003's hypothetical "Geom A REV → Geom B REV" invariant fails because Geom A and Geom B have different SLs AND different windows; A1_v2's weakening is correct.

### 5. Geom B parameters — exact match with Test A — PASS

Verified line-by-line against `scripts/ob_retest_comprehensive.py`:
- XAUUSD bullish SL: `ob_low - 0.001 * ob_low` (line 433) ↔ study.py:607
- XAUUSD bearish SL: `ob_high + 0.001 * ob_high` (line 463) ↔ study.py:611
- Other bullish SL: `ob_low - 0.00015` (line 435) ↔ study.py:608
- Other bearish SL: `ob_high + 0.00015` (line 465) ↔ study.py:612
- Target: `1.5 * sl_distance` (line 531) ↔ study.py:817-819
- Window: `for j in range(1, 13)` = 12 candles (line 537) ↔ RESOLUTION_HORIZON_B=12

All match exactly. The `0.00015` absolute buffer IS implausibly tight for JPY pairs and US30 (mean SL_B distances on the dataset: USDJPY 20 pips, US30 151 pips, GBPUSD 1.5 pips with extreme outliers). These tight SLs cause MANY j=0 instant-SL situations that get classified by the next 12 candles. This is faithful Test A reproduction; the report flags it appropriately. The 48.5% combined Geom B rate IS partially driven by this quirk (e.g., 2 GBPUSD rows have SL_B distance < 0.3 pip, essentially instant-stopouts unless the entry-candle skip rule recovers them). Worth elevating this caveat in the report's interpretation section.

### 6. Per-date EOD mitigation filter — FAIL (residual survivorship bias)

v2 RETAINS the per-date EOD-slice mitigation filter at study.py:392. `production identify_order_blocks` computes `mitigated = any(candles[k] for k in range(break_idx+1, len(candles)))` over the FULL 168-H1 lookback ending at EOD of `target_date` — including H1 candles AFTER the BOS that haven't been observed at the moment the OB was structurally created.

Empirical impact (`scratch/a3_v2_check_survivorship_v2.py`, full 2026 window):

| symbol    | total unique OBs | ever-fresh | always-mitigated (silently dropped) | drop rate |
|-----------|------------------|------------|-------------------------------------|-----------|
| XAUUSD    | 101              | 43         | 58                                  | 57.4%     |
| US30_cash | 97               | 45         | 52                                  | 53.6%     |
| USDJPY    | 122              | 52         | 70                                  | 57.4%     |
| GBPJPY    | 109              | 40         | 69                                  | 63.3%     |
| GBPUSD    | 103              | 37         | 66                                  | 64.1%     |

53-64% of OBs that production EVER detected get silently excluded from the v2 dataset — they were touched same-day as they formed, so on every per-date pass production marks them mitigated and v2 filters them out (study.py:392).

**Why this biases:** OBs that get touched same-day are by definition the FASTEST-reverting OBs. Excluding them removes the worst-performing population, pushing measured continuation rate UP. v2's 70% Geom A rate is consistent with Test A's baseline because Test A has the SAME bias — both studies use EOD per-date mitigation filtering. v2 is therefore consistent with Test A's prior, not bias-free.

A clean fix requires per-OB lookback windowing (mitigation checked only against H1 candles whose close ≤ `current_candidate_time`), or accepting all OBs and reporting fresh-at-retest vs touched-already separately. ADR 002 punted this to the rerun ("A3 said this part is sound and avoids look-ahead in OB detection itself; keep it"); A3 (v1) actually flagged it as fail (recommendation #2). It remains unaddressed in v2.

### 7. Live-period 0-alignment anomaly — CAVEAT (off-by-one between systems)

13 retests in live period (post-2026-04-07). 86 CANDIDATEs in live evaluations. Zero (sym, M15-bucket) intersections (`scratch/a3_v2_check_live_alignment.py`).

But: looking at the CANDIDATE buckets vs retest buckets manually:
- USDJPY: retest at 01:00:00Z, CANDIDATE at 01:15:00Z (15 min apart — same OB?)
- GBPUSD: retest at 13:45:00Z, CANDIDATE at 14:00:00Z (15 min apart)

These pairs are exactly one M15 bucket apart. The likely explanation: the live orchestrator runs at M15 close → it sees candle N as the most recent CLOSED candle, then logs a CANDIDATE evaluation tagged with `candle_time` = candle N. v2 considers the FIRST candle that enters the OB zone the retest. If candle N is the entering candle, the orchestrator's evaluation tagged with candle_time=N would in principle align with retest_ts=N. But if the live system's `candle_time` semantic is "the candle whose close JUST triggered the eval, used as the basis for the next decision" (i.e., decision applies starting at candle N+1), then there's a structural off-by-one — and the orchestrator wouldn't fire CANDIDATE on candle N entering the zone, but on candle N's close evaluation FOR candle N+1.

Either way: the join key is mechanically correct (same UTC M15 bucket), the format is read correctly, no timezone issues. This is a SEMANTIC mismatch between live system and study, not a coding bug. 

**Interpretive flag for main thread:** the live T7 C-gate is fundamentally a different predicate than mechanical OB-retest. T7 evaluates "H1 has bias / M15 not opposing / direction matches" on a per-M15-close basis during KZ — a CANDIDATE could fire on a M15 that has no relationship to a "first retest after BOS" event in the v2 sense. The absence of alignment is therefore not surprising and not informative about v2's correctness. The live-period report's "0 alignment" headline may be misread as v2 missing live signals; recommend reframing as "v2 mechanical retests and live T7 CANDIDATEs are semantically different events; the alignment exercise validates only that the bucket-join works."

### 8. Per-symbol rate spread — PASS (real n-noise + symbol structure)

Spread (Geom A): GBPUSD 35.3% (n=19), GBPJPY 83.3% (n=19), US30_cash 52.2% (n=28), USDJPY 93.5% (n=33), XAUUSD 71.4% (n=22).

Wilson 95% CIs are very wide for these n's. GBPUSD 35.3% n=19 → CI ≈ [17%, 59%]. USDJPY 93.5% n=33 → CI ≈ [80%, 98%]. The spread is consistent with binomial sampling noise on small populations, not a methodology artifact. Cross-checked individual rows for GBPUSD and USDJPY:
- USDJPY rows (5 spot-checked): SL_A distances 14-87 pips (3-10 pips), reasonable for the symbol's volatility. Outcomes match walk-forward inspection. The 93.5% rate is real — USDJPY had a strong directional regime in this window with many fast continuation moves.
- GBPUSD rows: 35% reflects observer-status of this symbol (per project notes, GBPUSD has lower edge). 8 of 19 are off-KZ (Tokyo/None) where mechanical retests behave differently than during active sessions. No SL/sign bug found.

Spread is real distributional variance, not artifact.

### 9. Test robustness — PASS

95 tests pass cleanly (0.37s). Spot-checked 10 NEW tests (per ADR 003 additions):
- `test_temporal_invariant_rejects_retest_equal_to_bos_confirm` — meaningful, would have caught v1 bug
- `test_temporal_invariant_rejects_retest_before_bos_confirm` — meaningful
- `test_bos_confirm_ts_is_h1_close_not_open` — meaningful, asserts delta is multiple of 1h
- `test_detect_first_retest_enforces_strict_greater_than_on_body_entry` — meaningful, codifies the strict-> decision
- `test_retest_walker_records_bos_confirm_on_output` — meaningful
- `test_output_csv_temporal_ordering_invariant_on_written_rows` — full-CSV invariant test (ADR 003 mandate)
- `test_geometry_b_sl_xauusd_bullish_formula` — pinned to Test A's literal `0.001 * ob_low`
- `test_geometry_b_sl_other_symbols_absolute_offset` — pinned to Test A's `0.00015`
- `test_geometry_b_target_is_1_5x_sl_distance` — pinned to Test A's multiplier
- `test_geometry_b_window_is_12_candles` — pinned to Test A's `range(1, 13)`

These are NOT rubber stamps. They directly assert ADR 003 specification properties and would catch regressions. Twin-geometry tests (`test_geometry_a_and_b_outcomes_both_populated`, `test_geometry_a_and_b_sl_prices_computed_independently`, `test_twin_geometry_unresolved_differs_by_horizon`) verify the dual classification is independent. Quality is high.

### 10. Uncaught look-ahead — PASS for v2's retest classification, FAIL for OB population (item #6)

- `_find_h1_atr_at` (study.py:467-488) uses `ct < target_time` strictly — only H1 candles BEFORE the retest contribute to ATR. No look-ahead. Correct anchored-ATR.
- `_walk_and_classify` (study.py:626-763) uses `m15_candles[entry_idx : entry_idx + horizon + 1]` and breaks on first SL/TP hit. No peeking past horizon. MAE/penetration only over the window. Correct.
- `continuation_r_a/b` is computed at the moment of TP hit (study.py:691, 706). Uses only the candle that hit. Correct.
- `causing_bos_index` is assigned at OB creation time using `break_idx = event.candle_index` — the BOS event is the candle whose CLOSE crossed the swing. Not look-ahead in the structural sense (price actually closed past the swing at that candle). The mitigation check that `identify_order_blocks` uses (`for k in range(break_idx+1, len(candles))`) IS look-ahead — see finding #6.

The retest CLASSIFICATION pipeline in v2 is free of look-ahead. The OB POPULATION fed into the pipeline has the survivorship bias from finding #6.

## Recommendations

### MUST-FIX (blocks publication)

None. v2 is publishable as-is, conditional on the SHOULD-FIX items being explicitly disclosed in the report.

### SHOULD-FIX (strong pre-sign-off recommendation)

1. **Disclose mitigation-filter survivorship bias in the report.** v2's geometry_report.md does not mention that 53-64% of unique OBs are silently dropped via the EOD-mitigation filter. Add a "Population Selection" section noting:
   - The dataset is the subset of OBs that survived same-day mitigation
   - This biases continuation rate UPWARD (fastest-reverting OBs excluded)
   - Test A has the same bias; v2's consistency with Test A reflects shared methodology, not independent confirmation
   - Numbers from `scratch/a3_v2_check_survivorship_v2.py` (or a re-run inside the build pipeline)

2. **Reframe the live-period 0-alignment finding.** Current report risks misreading. Recommend a callout: "v2 mechanical retest events and live T7 CANDIDATE evaluations are semantically distinct (different predicates, different cadences). Lack of alignment is expected, not a defect of either system."

3. **Disclose the strict-`>` decision in the methodology section, not just the trailing notes.** It silently eliminates a class of retests (those occurring during the BOS-impulse continuation candle). Document the rationale in the main body so a reader understands the cut.

4. **Add a section on Geom B's instant-SL artifacts.** 2+ GBPUSD rows and several USDJPY rows have SL_B distances < 1 pip due to the tight `0.00015` absolute buffer. Combined with the j=0-skip convention these get classified as continuation/reversal based on the post-entry walk. This is faithful Test A reproduction but a known execution-pathological edge. Suggest noting in the Geom B section: "Geom B's combined 48.5% includes instant-SL situations (~5-10% of rows on JPY pairs and GBPUSD) where the 0.00015 absolute buffer is microscopic relative to spread; this is faithful Test A reproduction, not a recommended live geometry."

### NICE-TO-HAVE (future)

5. Future rerun: implement per-OB-time-windowed mitigation check (per-OB lookback to retest_ts only). This eliminates the survivorship bias and would let us measure OB continuation under proper walk-forward discipline. Likely yields a LOWER number than 70%; deviation from Test A would itself be informative.

6. Add per-symbol entropy/volatility regime context to the report so per-symbol rate variance is interpretable.

7. Live-period join enrichment: distinguish "no eval (out of KZ)" from "eval exists but NO_TRADE" from "eval exists with CANDIDATE on adjacent bucket" so the off-by-one CANDIDATE adjacency observation isn't lost.

## Confidence in v2 publication-readiness

**85% confidence.** v2 correctly fixes the v1 timing bug and produces numbers that are internally consistent and externally consistent with Test A. The 70% Geom A combined rate is meaningful and matches the prior. The infrastructure is solid (95 tests, deterministic, ADR-compliant, write-guard discipline). The 15% gap is the residual EOD-mitigation survivorship bias inherited from Test A — v2 doesn't introduce a new problem here, but it doesn't fix one either. With the SHOULD-FIX disclosures added to the report (estimated 30-min edit), v2 is shippable as a faithful Test A consistency study. To make v2 a bias-free OB retest geometry characterization, the survivorship filter would need to be replaced — that's a rerun, not a documentation fix.

**Key dependencies:**
- Survivorship caveat disclosed in `geometry_report.md` (SHOULD-FIX #1)
- Live-period reframing applied to `live_period/geometry_report.md` (SHOULD-FIX #2)
- Strict-`>` cut documented (SHOULD-FIX #3)
- Geom B instant-SL artifact callout (SHOULD-FIX #4)
- No code changes required; doc edits only

**Did A1_v2's fix fully eliminate the v1 bug?** YES for the look-ahead in retest classification (the catastrophic v1 bug). The 92.9% phantom signal is gone. Residual look-ahead in OB-population selection (mitigation filter) persists from v1 via Test A but is a smaller effect and shared with the comparison baseline. v2 is safe to publish with disclosures.
