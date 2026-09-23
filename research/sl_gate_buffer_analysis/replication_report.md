# sl_too_tight Buffer Distribution — Independent Replication

**Date:** 2026-04-18
**Replicator:** Opus 4.7 (independent — parallel to primary analyst, no shared output)
**Script:** [`replication_analysis.py`](./replication_analysis.py)
**Enriched CSV:** [`enriched_retest_with_m15_atr.csv`](./enriched_retest_with_m15_atr.csv)
**Results JSON:** [`results.json`](./results.json)

---

## Data Verification

| Dataset | Path | Rows | Columns usable for gate |
|---|---|---|---|
| Retest CSV | `research/retest_geometry/outputs/a2_v2_validation/combined_retests.csv` | 726 | symbol, side, retest_entry_price, h1_atr_at_retest, sl_a_price, outcome_a, continuation_r_a, penetration_a_pips |
| Unified batch v2 | `knowledge_base_backtest/analysis/unified_trades_v2_20260331.json` | **111** (prompt said 129) | No OB edges, no M15 ATR → **cannot compute buffer** |
| Enriched index | `knowledge_base_backtest/analysis/deep_dive_20260406/trade_index_enriched.json` | 129 | No entry_price, no stop_loss, no OB → **cannot compute buffer** |
| M15 historical | `data/historical_2026/{SYMBOL}_M15.csv` | 6,420–6,818 per symbol | OK (Jan 2 – Apr 10/13 2026) |

After joining the 726 retest rows with M15 ATR(14) at `retest_ts`:
- **725 enriched** (1 skipped — retest at 2026-04-17 for GBPJPY is past M15 corpus end).
- **6 degenerate** — SL is on the wrong side of entry (entry above SL for a LONG, or below for a SHORT). Happens when the OB is narrow enough that `entry = close within OB`, and `ob_edge ± 0.5 × H1_ATR` lands past entry. These produce spurious multi-R winners. **Excluded from scoring.**
- **719 clean rows** used for the gate analysis.

**Sample ATR verification (sanity checked by hand on 3 rows):** `buffer / H1_ATR ≡ 0.5000` for every row (as expected by construction). `buffer / M15_ATR` varies in [0.4, 1.95], median ~1.0. M15 ATR computation uses Wilder smoothing, independently implemented in numpy.

---

## Methodology Audit (CRITICAL)

### 1. Circular outcome labeling — **FAIL (loudly)**

The CSV outcome labels `outcome_a` and R-multiples `continuation_r_a` were computed against `sl_a = ob_edge ± 0.5 × H1_ATR` — the SAME SL whose buffer is being used in every config-admission test. This is tautological at the buffer level: gate admission is based on `buffer / M15_ATR`, but the realized outcome is *conditional on trading with that specific SL*.

**Concrete implication:** A row with `sl_distance = 0.8 × M15_ATR` (tight) is admitted by current-live (buffer ≥ 0.3), gets its `outcome_a` from walking forward against that tight SL. If the CEO were to deploy Option C (buffer ≤ 0.5 × M15_ATR) with an AI that places the SL *at a different distance*, outcomes could differ.

**Partial mitigation:** Switching buffer units from H1 to M15 breaks the strict tautology (the gate threshold is not identically equal to the construction), so relative admit-counts across configs are informative — but WR/Exp comparisons between configurations remain contaminated whenever any config admits rows with different effective SLs. This is not the case here (every admitted row in every config uses the same Geom-A SL), so **WR/Exp are comparing different *slices* of the same dataset, not different SL policies.**

**Loud flag:** Configuration-level WR differences in this CSV describe *which trades fall in each band*, not *what happens when you change the SL policy*. This is a fundamentally limited answer to the CEO's question.

### 2. Direction convention — **PASS**

`side ∈ {long, short}`. For LONG → `sl_a = ob_low - 0.5 × H1_ATR` (below OB); SL ≤ ob_low = ob_edge ⇒ `sl_beyond_edge = True`. For SHORT → `sl_a = ob_high + 0.5 × H1_ATR` (above OB); SL ≥ ob_high ⇒ `sl_beyond_edge = True`. Matches `_compute_structural_sl_metrics()` in `src/components/permissions.py:210-213`. By construction every row in the retest CSV has `sl_beyond_edge = True`.

### 3. OB_edge inference — **PASS**

`permissions.py:298-302` maps LONG → `ob.low`, SHORT → `ob.high`. `A2_v2_validation.py:573,584` constructs `sl_a = ob_low ∓ 0.5 × H1_ATR` matching that exact convention. Inferred `ob_edge = sl_a ± 0.5 × H1_ATR` is exact (verified zero residual on 5 random rows).

### 4. Off-by-one — **PASS** (3-row hand check)

```
XAUUSD long  entry=4356.45000 sl_a=4337.25250 ob_edge=4344.61000 buffer=7.35750  H1_ATR=14.7150  ratio=0.5000
XAUUSD long  entry=4374.54000 sl_a=4366.39643 ob_edge=4373.36000 buffer=6.96357  H1_ATR=13.9271  ratio=0.5000
XAUUSD short entry=4387.03000 sl_a=4408.12714 ob_edge=4398.26000 buffer=9.86714  H1_ATR=19.7343  ratio=0.5000
```

Signs and magnitudes check out.

### 5. Outcome units

`continuation_r_a = |target - entry| / |entry - sl_a|` when CONTINUED, `-1.0` when REVERSED (`A2_v2_validation.py:691-699`). R-multiples in the CSV are computed **against the admission (Geom-A) SL**. Swapping SL policy would require re-simulating walk-forward. Because Geom-A targets are OB-body-relative (fixed in price terms), a tighter SL mechanically produces **larger R winners and also smaller R losers** — an R-multiple ratio artifact that currently inflates the current-live configuration's expectancy.

### 6. Selection effect in retest CSV — **YES (CRITICAL)**

`buffer_a / H1_ATR ≡ 0.5` for all 726 rows by construction (`A2_v2_validation.py:573, 584`). The retest dataset tests exactly one buffer-placement policy. In M15-ATR units it varies (because the H1/M15 ATR ratio varies across time and symbols), distribution:

```
[0.40, 0.50)   n=   4
[0.50, 0.75)  n=  19 ### (buffer/M15_ATR)
[0.75, 1.00)  n= 231 ####################################
[1.00, 1.50)  n= 428 ############################################################
[1.50, 2.00)  n=  22 ##
[< 0.30 or < 0.40)    n=   0  (empty bins)
```

**No row has `buffer/M15_ATR < 0.3`** — so Option D (`buffer ≤ 0.3 × M15_ATR`) admits ZERO rows beyond baseline, and Option E (band `[0.3, 0.5]`) admits only the same 2 rows as Option C. The retest CSV is blind to Option D by construction.

**Impact:** The batch JSON would be the instrument for observing AI-chosen tight-SL trades, but it lacks OB edges and M15 ATR columns (see Data Verification). Without those columns, we cannot classify those trades by buffer band. **The answer to the CEO's question is substantially undetermined by these datasets.**

---

## Gate Results

### Retest dataset — all symbols (719 good rows, 6 degenerate excluded)

| Config | Admitted | Classifiable | WR | Expectancy (R) | Sweep Events |
|---|---:|---:|---:|---:|---:|
| 1. Baseline (no bypass) | 641 | 622 | 78.62% | +0.006 | 131 |
| 2. Current-live (≥ 0.3 × ATR) | **719** | 700 | 74.86% | +0.020 | 174 |
| 3. Option C (≤ 0.5 × ATR) | 643 | 624 | 78.53% | +0.005 | 132 |
| 4. Option D (≤ 0.3 × ATR) | 641 | 622 | 78.62% | +0.006 | 131 |
| 5. Option E (0.3–0.5 band) | 643 | 624 | 78.53% | +0.005 | 132 |

Configurations 1/4 are identical (Option D admits 0 incremental rows). Configurations 3/5 are identical (Option E admits only the 2 rows in the `0.3-0.5` band, all of which also satisfy `≤ 0.5`).

### Delta view — the cohort that matters

The 78 tight-SL rows (`sl_distance < 1.5 × M15_ATR`) are the *only* rows that the bypass rule acts on. Their performance by cell:

| Configuration applied to tight cohort | Admitted | Wins | Losses | WR | Expectancy |
|---|---:|---:|---:|---:|---:|
| Current-live (buffer ≥ 0.3) | **78** | 35 | 43 | **44.9%** | +0.129 R\* |
| Option C (buffer ≤ 0.5) | 2 | 1 | 1 | 50% | -0.283 R |
| Option D (buffer ≤ 0.3) | 0 | — | — | — | — |
| Option E (band 0.3–0.5) | 2 | 1 | 1 | 50% | -0.283 R |

\* Expectancy on tight cohort is inflated by the R-multiple ratio artifact (Section 5 of audit). The "winning R" for a tight-SL trade is `target_distance / sl_distance` — small denominators produce large R even when the target isn't exceptional. Read +0.129R with heavy skepticism.

**Key observation:** On the 78 rows that the base 1.5-ATR rule would reject, the current-live policy admits ALL of them and WR drops from the overall 78.6% to **44.9%** — a 34-point WR cliff.

### Per-symbol (719 good rows, current-live config only)

| Symbol | Admit | WR | Exp(R) | Δ Admit vs Baseline |
|---|---:|---:|---:|---:|
| GBPJPY | 148 | 79.3% | +0.138 | +13 |
| GBPUSD | 150 | 71.7% | -0.056 | +23 |
| US30_cash | 142 | 74.6% | +0.001 | +19 |
| USDJPY | 133 | 76.7% | +0.063 | +11 |
| XAUUSD | 146 | 72.0% | -0.048 | +12 |

The 34-pp WR gap on tight trades shows up across symbols; XAUUSD is worst (current-live gives 72.0% vs baseline 74.8%).

### Batch JSON (AI-chosen SLs)

| Config | Admitted | WR | Expectancy (R) | Sweep Events |
|---|---|---|---|---|
| All | **N/A** | **N/A** | **N/A** | **N/A** |

The `unified_trades_v2_20260331.json` has 111 records with `entry_price` and `stop_loss` but **no `ob_high`/`ob_low`/`m15_atr` columns**. Cannot compute `buffer` or `buffer/M15_ATR`. Cannot answer the gate question from this data without a full pipeline replay that joins OB detection (Component 2) against pre-existing MSO states — a separate, multi-day exercise. The `trade_index_enriched` JSON (n=129) has even fewer usable columns.

**Correction vs prompt:** Prompt said "129 XAUUSD AI-chosen SLs" — the 129-row file is multi-symbol and contains no price columns; the price-bearing file has 111 rows mixed across ob_retest/session_sweep frameworks.

---

## Buffer Distribution

### All good retest rows (n=719), winners vs losers on Geom-A outcomes

| buffer/M15_ATR | n | W | L | WR |
|---|---:|---:|---:|---:|
| [0.40, 0.50) | 4 | 3 | 1 | 75.0% |
| [0.50, 0.75) | 19 | 13 | 6 | 68.4% |
| [0.75, 1.00) | 231 | 184 | 47 | 79.7% |
| [1.00, 1.50) | 428 | 308 | 120 | 72.0% |
| [1.50, 2.00) | 22 | 18 | 4 | 81.8% |

Best WR bands: [0.75, 1.0) and [1.5, 2.0). The 0.4–0.5 band (the Option C / E zone) has very thin support (n=4). **Any conclusion about the 0.3–0.5 band is statistically weak from this dataset.**

### sl_distance / M15_ATR — who gets rejected by baseline?

| sl_dist/M15_ATR | n | Effect of 1.5-ATR rule |
|---|---:|---|
| [0.0, 0.5) | 15 | REJECTED |
| [0.5, 1.0) | 18 | REJECTED |
| [1.0, 1.5) | 50 | REJECTED |
| [1.5, 2.0) | 83 | admitted |
| [2.0, 3.0) | 255 | admitted |
| [3.0, 5.0) | 247 | admitted |
| [5.0, 20.0) | 57 | admitted |

78 of the 83 tight rows are non-degenerate; those 78 are precisely the rows the bypass rule affects.

---

## Divergence Risks — What a Primary Analyst Might Get Wrong

1. **Trusting the retest CSV's outcome labels as policy-invariant.** If the primary reports "WR 74.9% at buffer ≥ 0.3" as evidence for current-live, they are ignoring that outcomes were generated using the Geom-A SL. Different SL policies would produce different outcome labels. The retest CSV cannot distinguish gate policies in causal terms — only in admission-count terms.

2. **Missing the degenerate-row inflation.** 6 rows have SL on the wrong side of entry; one winner is labeled +77.25R because the "SL" cannot be touched. If the primary doesn't filter these, current-live's expectancy jumps from +0.020R to +0.131R — a 6.5x inflation. I strongly suspect any analyst using pandas `mean(r_multiple)` without outlier inspection will report the inflated number.

3. **Reading Option D as "same as baseline" as a neutral equivalence.** Option D admits zero rows beyond baseline only because *this simulated dataset has no rows at buffer < 0.3 × M15_ATR*. In production, Apr 16 XAUUSD had buffer = 0.12 × M15_ATR — that trade IS representative of the case Option D rejects and current-live admits. The retest CSV contains no analogue.

4. **Mixing outcome_a (Geom-A) with outcome_b (tight SL) without labeling.** A primary that reports Geom-B numbers alongside A without distinguishing will show apples-to-oranges WR.

5. **Using H1 ATR as if it were M15 ATR.** The CSV gives `h1_atr_at_retest`. If the primary computes `buffer/ATR` using that column directly, they are computing `buffer / H1_ATR ≡ 0.5` for every row — a degenerate answer. The gate operates on M15 ATR.

6. **Claiming the batch JSON answered the question.** The 111-record v2 JSON lacks the columns needed. A primary may silently skip the batch analysis or fabricate it.

---

## My Recommendation (independent of primary)

**Empirically this CSV cannot discriminate among Options C / D / E with adequate statistical support, and the "current-live vs baseline" delta is dominated by the tautology-to-outcome-label issue plus the R-multiple ratio artifact.** The only defensible statistical observation from the retest data is that the tight-SL cohort (n=78) has WR 44.9% vs the overall 78.6% — **a 34-point cliff that applies regardless of which bypass rule we pick**, because all bypass rules admit some fraction of those 78 rows. Admitting more of them makes the average worse.

Given:
- ADR 003's Youden cut at 0.53 × M15_ATR (from MAE distributions of winners p90=1.06 vs losers p10=0.87);
- Apr 16 XAUUSD at buffer = 0.12 × M15_ATR → swept → -1R (real evidence of the "too-tight" failure mode at the low end);
- Retest cohort shows no rows in [0, 0.3 × M15_ATR) (not testable with this data);
- Tight-SL cohort WR cliff at 44.9% when the base rule is bypassed;

**Recommendation: Option E (hybrid band 0.3 ≤ buffer/M15_ATR ≤ 0.5).** Rationale:
- Honors the committed Apr 16 floor at 0.3 (rejects the failure mode observed live);
- Respects ADR 003's upper bound at 0.5 (rejects wide-buffer "pseudo-structural" SLs that really are discretionary);
- Current-live is too permissive — admits the full 78-row tight cohort with 44.9% WR;
- Option C is too permissive at the low end (admits buffer < 0.3, the Apr 16 regime);
- Option D is too conservative at the upper end (rejects buffers at 0.4–0.5 where WR is 75% and the structural rationale is strongest).

**Confidence:** LOW on numeric precision (the datasets can't cleanly answer), MEDIUM on the direction of the recommendation (the qualitative argument is the live Apr 16 trade + ADR 003 + WR cliff in the tight cohort — the CSV is confirmatory, not primary evidence). I would weight the CEO's hand-picked Option E intuition higher than anything this replication produces.

**Alternative framing:** if we were confident in rigorous buffer variation on the live books, the right answer is likely in [0.3, 0.5] not at either endpoint — Option E is the hedge that says "I don't know which endpoint matters more, lock the middle."

---

## Script

See [`replication_analysis.py`](./replication_analysis.py). Run with:

```bash
python research/sl_gate_buffer_analysis/replication_analysis.py
```

Outputs:
- `enriched_retest_with_m15_atr.csv` — per-row enriched data (725 rows)
- `results.json` — machine-readable results
- stdout — full gate / distribution tables

**Word count: ~1,920.**
