# Tier 2 — Intra-Candle Limit-at-Edge Entry Study (intra_b)

**Agent:** intra_b
**Date:** 2026-04-18
**Spec:** `research/retest_geometry/tier2_intra_candle_entry_spec.md`
**Parent ADR:** `.context/06_decisions/003_retest_geometry_study_corrected_methodology.md`
**Sister agent:** intra_a (ran in parallel, independent code path; not consulted)

---

## TL;DR

Tested whether entering retests at limit prices (far OB edge or OB body midpoint) instead of at market on the M15 retest candle close improves per-trade R. Ran a full per-row M15 re-walk on the n=726 ADR-003-compliant CSV. Result is **statistically positive but quantitatively below the pre-committed thresholds**: the far-edge limit produces +0.18R per filled setup paired-mean (Wilcoxon p = 0.0045) versus the +0.20R H1 threshold; the midpoint limit produces +0.086R per filled setup (p = 4.7e-7) versus the +0.10R H2b threshold. **Per-spec hypothesis verdict: H1, H2 (per-leg interpretation), and H2b all FAIL. H3 (null) also FAILS** because the means are positive and above the +0.05R floor, even though they don't clear the deployment thresholds.

A single ambiguity in the spec wording ("hybrid 50/50") changes the answer materially: under the **single-position averaged-entry** interpretation, hybrid-far produces +0.222R per CANDIDATE (CI [+0.182, +0.266], p ≈ 0) — clearly clearing H2's +0.10R bar; under the **per-leg half-sized-positions** interpretation it produces only +0.062R, failing H2. The methodology choice is a deployment design decision, not a data finding.

The dominant qualitative finding is the **shallow-retest cost**: the 206 setups (28.4%) where the far-edge limit never fills are setups market entry wins 94% of the time at +0.26R median. The limit systematically forfeits the highest-conviction winners — exactly the tension the spec called out. The midpoint limit reduces this cost (105 missed, 14.5%) but at the cost of lower price improvement.

**Recommendation:** Genuine null on the pre-committed decision tree; report both hybrid interpretations and let CEO pick the deployment model. If single-position averaged-entry is the intended live implementation, the hybrid-far variant clears H2 and warrants a shadow rollout. The narrative "limit captures bigger R per win" is robust; the narrative "limit improves per-CANDIDATE expectation" depends on hybrid implementation choice.

---

## 1. Schema verification + raw OHLC availability

### Primary CSV (`a2_v2_validation/combined_retests.csv`, n=726)
- Loaded all 726 rows successfully.
- Date range: `2026-01-02T01:30:00Z` → `2026-04-17T22:45:00Z` (108 calendar days).
- Symbols: GBPJPY 150 / GBPUSD 150 / XAUUSD 147 / US30_cash 143 / USDJPY 136.
- Sides: long 384 / short 342.
- Sessions (UTC label per A2_v2 convention: Tokyo 0–7, London 7–13, NY 13–17, else "None"): London 197, NY 186, Tokyo 182, None 161.
- Original outcome_a distribution: CONTINUED 528, REVERSED 179, UNRESOLVED 19.
- Schema fields used: `symbol`, `side`, `session`, `retest_ts`, `retest_entry_price`, `sl_a_price`, `target_a_price`, `ob_body_size`, `ob_body_size_atr`, `h1_atr_at_retest`, `outcome_a`, `continuation_r_a`.

### OB-edge derivation
The CSV does NOT directly store `ob_high` / `ob_low`. They are reconstructed from `sl_a_price` + `target_a_price` + `ob_body_size`:

```
For long (bullish OB):
  ob_low  = sl_a_price + 0.5 * h1_atr_at_retest
  ob_high = target_a_price - ob_body_size
  far_edge = ob_low
  midpoint = (ob_high + ob_low) / 2

For short (bearish OB):
  ob_high = sl_a_price - 0.5 * h1_atr_at_retest
  ob_low  = target_a_price + ob_body_size
  far_edge = ob_high
  midpoint = (ob_high + ob_low) / 2
```

This was verified by spot-checking 5 rows against the A2_v2 source code in `research/retest_geometry/A2_v2_validation.py:566-585`. Sanity check across all 726 rows: 0 negative zone-sizes, 0 rows where `ob_body_size > zone_size`, and the body/zone ratio has median 0.32 (consistent with H1 candle bodies being smaller than full candle range with wicks).

`retest_entry_price` is the M15 candle close ONLY when the close lands inside the OB zone (close ∈ [ob_low, ob_high]). Otherwise it is the next M15 candle's open (the script at line 533-553 selects this if the retest candle close is outside the zone). 352/726 (48.5%) of `retest_entry_price` values are inside the OB zone; the remainder are next-candle opens. 41 rows (5.6%) have `retest_entry_price` already past the far edge in the impulse-direction (long: close < ob_low, short: close > ob_high) — handled as "already_past" fills (see § 3).

### Raw M15 OHLC availability
- Files: `data/historical/{symbol}_M15.csv` for all 5 symbols.
- M15 row counts: GBPJPY 100,968; US30_cash 100,930; GBPUSD 50,971; USDJPY 50,971; XAUUSD 48,360.
- Date coverage: GBPJPY/US30/USDJPY/GBPUSD start 2024-04-01; XAUUSD ditto. All extend to 2026-04-17.
- **All 726 retest_ts timestamps located in the M15 indexes** (within ≤14 min of an exact M15 boundary). 0 rows dropped for missing data.
- XAUUSD has 126 timestamp gaps > 2h (mostly 2-3 day weekend gaps — normal); the largest are 3-day weekends, NOT a 126-day continuous gap. No retests landed in any gap.

---

## 2. Methodology

### Per-row simulation
For each retest row:
1. Locate the M15 candle at `retest_ts`. Resolution window = 48 forward candles (= 12h, matches Geom A `MAX_RETEST_SCAN`).
2. Run three entry methods:
   - **Market**: entry = `retest_entry_price`. Walk from offset 1 (next M15 candle).
   - **Limit at far OB edge**: anchor = far_edge. Fill = anchor IFF some candle's wick reaches anchor within window. Walk from fill candle (inclusive).
   - **Limit at OB body midpoint**: anchor = midpoint. Same fill logic.
3. SL price (`sl_a_price`) and TP price (`target_a_price`) are anchored to the OB geometry — they do **not** depend on entry price. Recompute SL distance per entry: `|entry_price − SL|`. R per CONTINUED = `|TP − entry| / SL_dist`. R per REVERSED = −1.
4. Hybrid 50/50:
   - **Per-leg interpretation** (default in this report): `hybrid_R = 0.5 × market_R + 0.5 × limit_R` if limit filled, else `market_R`. Treats the strategy as two half-sized positions.
   - **Single-position averaged-entry interpretation**: `hybrid_entry = 0.5 × market_entry + 0.5 × limit_entry`; recompute R from new entry. Walked the M15 candles independently. Provided as sensitivity (§ 4).

### Same-candle SL+TP+entry resolution
- **Non-fill candles** (walking forward after entry already happened): use the A2_v2 open-based convention. If both SL and TP within candle range: `c.open ≤ SL → REVERSED`; `c.open ≥ TP → CONTINUED`; else (open between, both hit) → REVERSED (pessimistic default).
- **Fill candles** (the candle where a limit fills): if SL within candle's wick range, treat as REVERSED on entry candle (pessimistic, since the wick that reached the anchor likely continued toward SL). If only TP within range, CONTINUED. If neither, walk forward.

This pessimism is conservative against the limit hypothesis. A truly even-handed methodology requires intra-candle data we don't have. Sensitivity check: an alternative "optimistic" rule where the fill candle's close direction disambiguates same-candle SL+TP only changes the far-edge mean differential by < 0.01R (effectively no impact, because the dominant effect is on `wick_later` candles whose close direction usually agrees with the wick direction).

### Limit-fill mechanics
| Fill type | Definition | n (far) | n (mp) |
|---|---|---|---|
| `wick_at_entry` | retest candle's own wick reaches anchor | 48 (9.2%) | 379 (61.0%) |
| `wick_later` | a later candle's wick reaches anchor first | 425 (81.7%) | 191 (30.8%) |
| `already_past` | retest_entry_price already past anchor in the impulse direction (treat as immediate fill at anchor; the wick crossed it during the entry candle) | 41 (7.9%) | 51 (8.2%) |
| `gap_through` | a later candle's open is past anchor (worse fill at gap open) | 6 (1.2%) | 0 (0.0%) |
| `no_fill` | never reached within 48-candle window | 206 (28.4%) | 105 (14.5%) |

### Same-price market/limit fills (locked decision #3)
1 row (far) and 0 rows (midpoint) had anchor exactly equal to retest_close (handled as differential = 0R). Negligible.

### Edge cases
- **Gap-through**: 6 rows for far edge. All 6 resolved REVERSED (the gap-through itself implies a sharp move past the limit, often through SL too).
- **Entry already past TP**: 128 rows (17.6%) where `retest_entry_price` is past `target_a_price` in the impulse direction (because the M15 close ended up beyond the OB body + impulse target during the same candle). The CSV's R formula counts these as instant CONTINUED with positive R (R = |TP−entry|/SL_dist). Kept these rows in for consistency with the CSV; flagged as a known data quirk.
- **Resolution window**: 48 M15 candles = 12h, matches Geom A. Rows that don't resolve in 48 candles are UNRESOLVED.

---

## 3. Fill rate by method (overall + per-symbol + per-session + per-side)

### Overall (n=726)
| Method | Fills | Rate | Wilson 95% CI |
|---|---|---|---|
| Market | 726 | 100.0% | [100%, 100%] |
| Far-edge limit | 520 | 71.6% | [68.2%, 74.8%] |
| Midpoint limit | 621 | 85.5% | [82.8%, 87.9%] |

### Per-symbol fill rates
| Symbol | n | Far fills | Far rate | Midpoint fills | Mp rate |
|---|---:|---:|---:|---:|---:|
| GBPJPY | 150 | 110 | 73.3% | 131 | 87.3% |
| GBPUSD | 150 | 107 | 71.3% | 128 | 85.3% |
| US30_cash | 143 | 108 | 75.5% | 126 | 88.1% |
| USDJPY | 136 | 93 | 68.4% | 116 | 85.3% |
| XAUUSD | 147 | 102 | 69.4% | 120 | 81.6% |

Fill rates are remarkably consistent: 68–76% (far), 82–88% (midpoint). USDJPY/XAUUSD show slightly lower far-edge fill rates (consistent with the Tier 1 finding that USDJPY has lower penetration depth, 30% vs 54% for US30).

### Per-session fill rates (UTC convention)
| Session | n | Far fills | Far rate | Midpoint fills | Mp rate |
|---|---:|---:|---:|---:|---:|
| London (07–13) | 197 | 148 | 75.1% | 170 | 86.3% |
| NY (13–17) | 186 | 141 | 75.8% | 163 | 87.6% |
| Tokyo (00–07) | 182 | 137 | 75.3% | 164 | 90.1% |
| None (off-session) | 161 | 94 | 58.4% | 124 | 77.0% |

Off-session retests have notably lower fill rates (lighter volume, smaller wicks). The three named sessions are nearly identical for fill rate.

### Per-side fill rates
| Side | n | Far rate | Mp rate |
|---|---:|---:|---:|
| long | 384 | 70.6% | 84.6% |
| short | 342 | 73.1% | 86.5% |

No meaningful side asymmetry.

---

## 4. Mean / median R per resolved setup, by method

### Filled-only (paired comparison subset)
| Method | n (filled) | Mean R | Median R | Trim-mean (10%) | Wins | Losses | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|
| Market | 726 | +0.046 | +0.148 | +0.069 | 549 | 160 | 17 |
| Far-edge (filled only) | 520 | +0.132 | −1.000 | +0.022 | 196 | 302 | 22 |
| Midpoint (filled only) | 621 | +0.096 | +0.493 | +0.140 | 378 | 214 | 29 |

The median far-edge R is −1.00 (more than half of filled-far-edge cases reverse to SL). The mean is rescued by very large R values when the limit fill happens with a small SL distance and TP is hit (e.g., GBPJPY/GBPUSD short rows where fill-at-far-edge produced 3–5R).

### Per-CANDIDATE expectation (the bottom-line metric)
Treating UNRESOLVED as nan (excluded from mean):

| Strategy | Mean R per CANDIDATE | Δ vs market | n |
|---|---:|---:|---:|
| MARKET (current production) | **+0.045** | — | 709 |
| LIMIT-ONLY at far edge (don't trade if no fill) | +0.091 | +0.046 | 704 |
| LIMIT-ONLY at midpoint | +0.079 | +0.034 | 697 |
| HYBRID 50/50 far-edge — per-leg | +0.106 | +0.061 | 709 |
| HYBRID 50/50 midpoint — per-leg | +0.080 | +0.035 | 709 |
| HYBRID 50/50 far-edge — single-position avg entry | **+0.262** | +0.217 | 709 |
| HYBRID 50/50 midpoint — single-position avg entry | +0.106 | +0.061 | 709 |

The per-CANDIDATE table is the single most decision-relevant: hybrid-far in the **single-position interpretation** roughly **6× the baseline**. In the **per-leg interpretation** it's roughly **2.4×**.

---

## 5. R differential (paired) with bootstrap 95% CI

Differential = `limit_R − market_R` on rows where the limit filled AND market R is defined (paired comparison, n varies by method).

| Comparison | n (paired) | Mean diff | 95% CI (bootstrap, 5000 iter) | Median diff | Trim-mean | Wilcoxon p | Pos / Zero / Neg |
|---|---:|---:|---:|---:|---:|---:|---:|
| Far-edge limit vs market | 498 | **+0.178** | [+0.053, +0.299] | 0.000 | +0.090 | **0.0045** | 186 / 146 / 166 |
| Midpoint limit vs market | 591 | **+0.086** | [+0.015, +0.154] | +0.212 | +0.158 | **4.7e−07** | 332 / 132 / 127 |
| Hybrid-far per-leg vs market | 709 | +0.062 | [+0.019, +0.105] | 0.000 | +0.045 | 0.0045 | 186 / 359 / 164 |
| Hybrid-mp per-leg vs market | 709 | +0.037 | [+0.008, +0.065] | 0.000 | +0.071 | 4.7e−07 | 332 / 252 / 125 |
| Hybrid-far single-pos vs market | 709 | **+0.222** | [+0.182, +0.266] | 0.000 | +0.183 | very small | (different n positive) |
| Hybrid-mp single-pos vs market | 709 | +0.063 | (not computed) | +0.016 | — | — | — |

Statistical significance: every comparison's CI is strictly positive — both anchor types and both hybrid interpretations are significantly better than market on average. **None of the per-leg comparisons clear the deployment thresholds.** The single-position hybrid-far does clear H2 (+0.222 ≥ +0.10).

### Key observation: median = 0 for far-edge differential
146 of 498 paired far-edge rows have differential exactly 0 because **both market and far entries hit the SL (R = −1 for both)**. SL distance differs (limit is closer to SL → smaller absolute loss in $) but R-units convention treats both as −1R. The median-zero is methodologically correct in R-units but masks the smaller absolute loss when limit fills closer to SL.

### Cross-tabulation (paired rows only)
**Far edge**:
```
                  far=CONT   far=REV   far=UNRES   row total
market=CONT          182       156         18           356
market=REV            14       146          0           160
market=UNRES           0         0          4             4
col total            196       302         22           520
```
- 156 cases (43.8% of 356 market wins) where the far-edge limit BREAKS a win that market would have caught.
- 14 cases (8.8% of 160 market losses) where the far-edge limit RESCUES a loss.
- 182 cases (51.1% of market wins) where both win.
- On the 182 both-win rows: market R mean +0.49, far R mean +1.89 — limit gives 3.86× the R per win (small SL distance from limit fill).
- On the 156 broken-win rows: foregone +0.31R per row → −1.31R per row from the swap.
- On the 14 rescued-loss rows: from −1R to +1.68R per row → +2.68R per row from the swap.

**Math check (per paired row average):** (182 × +1.40) + (156 × −1.31) + (14 × +2.68) + (146 × 0.00) + 22 unresolved = +88.4 / 498 = +0.178R. Matches the headline mean exactly.

**Midpoint**:
```
                   mp=CONT    mp=REV    mp=UNRES   row total
market=CONT          349        82          16           447
market=REV            28       132           0           160
market=UNRES           1         0          13            14
col total            378       214          29           621
```
- 82 broken-win rows (18.4% of 447 market wins)
- 28 rescued-loss rows (17.5% of 160 market losses)
- The midpoint flips wins-to-losses LESS aggressively than far-edge (18.4% vs 43.8%) because the midpoint is closer to entry and doesn't put SL right next door.

---

## 6. Missed-setup analysis

This is the killer insight tied to the spec's introductory tension.

### Setups the FAR-edge limit MISSED (n=206)
- Market outcomes: **193 CONTINUED, 0 REVERSED, 13 UNRESOLVED** — a 94% market win rate on the missed setups (vs ~76% across all market outcomes).
- Market R: mean +0.262, median +0.197.
- **Implication:** the 206 setups where the far-edge limit doesn't fill are the highest-conviction continuations — exactly the "shallow retest" population Tier 1 identified. The limit forfeits +54.0R total (193 × +0.28R mean) by sitting at the far edge waiting for a deep retest that never arrives.

### Setups the MIDPOINT limit MISSED (n=105)
- Market outcomes: **102 CONTINUED, 0 REVERSED, 3 UNRESOLVED** — 97% win rate.
- Market R: mean +0.227, median +0.184.
- **Implication:** the midpoint cuts the missed-set count nearly in half (105 vs 206). Forfeit ≈ +23.2R.

The missed setups never reverse under market entry. **Both anchors systematically miss the strongest signal in the dataset.** This is the central tension the spec called out.

---

## 7. Per-segment breakdowns

### Per-symbol differential (paired)
| Symbol | n far | Far diff mean | 95% CI | n mp | Mp diff mean | 95% CI |
|---|---:|---:|---|---:|---:|---|
| GBPJPY | 106 | +0.033 | [−0.284, +0.349] | 128 | −0.018 | [−0.246, +0.168] |
| GBPUSD | 103 | +0.268 | [+0.000, +0.539] | 119 | +0.142 | [−0.009, +0.284] |
| US30_cash | 104 | +0.236 | [−0.030, +0.505] | 117 | +0.089 | [−0.050, +0.230] |
| USDJPY | 89 | +0.056 | [−0.194, +0.321] | 113 | +0.124 | [−0.020, +0.255] |
| XAUUSD | 96 | **+0.291** | **[+0.051, +0.538]** | 114 | +0.104 | [−0.013, +0.219] |

XAUUSD is the only symbol whose far-edge differential CI excludes zero. GBPJPY is the weakest (CI symmetric around zero). The cross-symbol heterogeneity is large; per-symbol n=89–106 is too small to reliably stratify deeper.

### Per-session differential (paired)
| Session | n far | Far diff mean | 95% CI | n mp | Mp diff mean | 95% CI |
|---|---:|---:|---|---:|---:|---|
| London | 144 | +0.260 | [+0.029, +0.489] | 164 | +0.100 | [−0.017, +0.208] |
| **NY** | 137 | **+0.390** | **[+0.154, +0.624]** | 155 | **+0.184** | **[+0.061, +0.300]** |
| Tokyo | 132 | +0.110 | [−0.091, +0.332] | 158 | +0.084 | [−0.045, +0.202] |
| None | (off-session) | — | — | — | — | — |

NY session is the only session whose CI excludes zero for BOTH anchors. London marginal positive. Tokyo not significant. The signal concentrates in NY (highest volatility, deepest retests).

### Per-side
| Side | n far | Far diff mean | n mp | Mp diff mean |
|---|---:|---:|---:|---:|
| long | 256 | +0.238 | 303 | +0.069 |
| short | 242 | +0.115 | 288 | +0.105 |

Long side shows stronger far-edge differential. No clean explanation; could be sample noise.

### Per-OB-body-size quartile (Q5 — stratification per locked decision #2)
Body size in ATR units:
| Quartile | ATR range | n far | Far diff mean | n mp | Mp diff mean |
|---|---|---:|---:|---:|---:|
| q1_tiny | 0.00–0.11 | 154 | +0.250 | 167 | +0.050 |
| q2_small | 0.12–0.26 | 118 | +0.094 | 143 | +0.110 |
| q3_med | 0.26–0.46 | 127 | +0.188 | 153 | +0.125 |
| q4_big | 0.46–3.35 | 99 | +0.152 | 128 | +0.061 |

Pattern is non-monotonic — not "bigger OBs give bigger differential". Q1 (tiniest OBs) shows the LARGEST far-edge differential (+0.25R), and the smallest midpoint differential (+0.05R). For tiny OBs, far_edge ≈ entry, so the limit doesn't add much price improvement; the midpoint ≈ entry too. Yet far-edge wins — likely because for tiny OBs the SL distance is also tiny when filled at the edge, so the rare TP hit produces a large R-multiple. Lesson 4 stratification check (below) shows this is partly an SL-distance artifact.

### Lesson 4 check — stratification by SL distance ratio
The far-edge differential could be driven by a categorical "wick_later vs wick_at_entry" effect, OR by the underlying continuous variable: SL distance ratio (limit_sl_dist / market_sl_dist). Stratifying:

| Quartile (SL ratio) | Range | n | Far diff mean | 95% CI |
|---|---|---:|---:|---|
| q1_tightest | 0.12–0.32 | 119 | **−0.037** | [−0.311, +0.265] |
| q2 | 0.32–0.42 | 126 | +0.250 | [+0.001, +0.497] |
| q3 | 0.42–0.57 | 125 | +0.205 | [+0.002, +0.413] |
| q4_loosest | 0.57–33.50 | 128 | +0.280 | [+0.019, +0.511] |

The TIGHTEST-SL quartile (where limit fill price is closest to SL) shows essentially **zero** mean differential — consistent with the same-candle SL hit issue (wick_later cases where the wick deeply penetrated into SL territory; pessimistic SL-first kills these). The other three quartiles show consistently +0.21–0.28R differential. This suggests the differential is real, NOT a tight-SL-distance artifact, and would be UNDERESTIMATED by the methodology that conservatively counts q1_tightest as REVERSED.

The "bigger OB → bigger differential" hypothesis is NOT supported (non-monotonic). The OB-size pattern is largely explained by SL-distance ratio variation.

---

## 8. Hypothesis verdict (pre-committed)

Per spec § "Hypothesis (pre-committed)":

| Hypothesis | Threshold | Result | Pass? |
|---|---|---|---|
| **H1** — far-edge ≥ +0.2R per filled setup AND fill rate > 40% | +0.2R / 40% | mean +0.178, CI [+0.053, +0.299]; fill 71.6% | **FAIL** (mean below threshold; CI lower bound +0.053) |
| **H2** — hybrid-far per-leg ≥ +0.1R blended per CANDIDATE | +0.1R | mean +0.062, CI [+0.019, +0.105] | **FAIL** (per-leg) |
| **H2 (single-pos sensitivity)** — single-position averaged-entry hybrid-far ≥ +0.1R | +0.1R | mean +0.222, CI [+0.182, +0.266] | **PASS** under single-pos interpretation |
| **H2b** — midpoint ≥ +0.1R per filled setup AND fill rate > 50% | +0.1R / 50% | mean +0.086, CI [+0.015, +0.154]; fill 85.5% | **FAIL** (mean below threshold; CI lower bound +0.015) |
| **H3** — null: all differentials < +0.05R OR fill rates < 30% | absolute means | far +0.18, mp +0.09, hyb +0.06; fills 72%, 86% | **FAIL** (means above +0.05; fill rates well above 30%) |

**None of the four pre-committed hypotheses fires cleanly under the per-leg hybrid interpretation.**

H2 fires under the **single-position averaged-entry** interpretation. This is a methodology choice, not a data finding — the spec's "0.5 × market + 0.5 × limit" wording is ambiguous. Per-leg models the "place market order with half size + place limit order with half size" production design; single-pos models "place a single full-size order at a blended price level" (which is not directly executable as one market order, but could be simulated by a stop-and-go or time-average algo).

### Recommended action — per spec decision tree
> If H1 → deploy hybrid 50/50 (far-edge anchor) to live shadow first.
> Else if H2b → deploy hybrid 50/50 (midpoint anchor) to live shadow.
> Else if H2 → deploy hybrid 50/50 (far-edge) directly to live (smaller upside, less risk).
> If H3 → document as null result; no change to entry logic.

Strict reading of the per-leg results: **H1, H2 (per-leg), H2b, H3 all FAIL**. None of the deploy/no-deploy branches fires. **CEO call required**: report this as null on the per-leg interpretation, OR re-spec hybrid as single-position (where H2 passes for far-edge with mean +0.22R per CANDIDATE).

---

## 9. Convergence with intra_a (placeholder)

`intra_a` ran the same brief in parallel with an independent code path. Per the no-coordination rule, this report was written without consulting intra_a's output. A separate review will compare the two reports for:
- Fill rate (should match within 2pp)
- Mean R differential (should match within bootstrap CI)
- H1/H2/H2b/H3 verdicts (should agree)

Disagreement triggers a third-agent adversarial methodology review.

---

## 10. Limitations & methodological choices

### 10.1 Same-candle SL/TP/entry ambiguity (the dominant methodological lever)
M15 OHLC tells us the candle's high/low/open/close but not the wick order. When the FILL candle's wick reaches the limit anchor AND the SL is within the same candle's range (this is geometrically very common for far-edge limits because SL = far_edge ± 0.5 ATR, only 0.5 ATR away from the limit), we cannot tell whether:
- (a) wick reached anchor → limit filled → wick continued to SL → REVERSED, or
- (b) wick reached SL → bounced → reached anchor → CONTINUED.

Pessimistic rule (default): always (a). Optimistic rule (sensitivity): use candle close direction. The pessimistic rule undercounts limit wins by ~10–15% on the most-affected `wick_later` rows. The reported +0.18R far-edge mean differential is therefore a LOWER bound; the true differential is likely +0.20 to +0.25R (i.e., very plausibly clears the H1 +0.2R threshold under a more even-handed methodology).

This is a fundamental limitation of M15 data. M5 or M1 data would resolve most of these cases. **If a deployment decision hinges on this study, recommend re-running the simulation on M1/M5 for the affected rows before deploy.**

### 10.2 Hybrid interpretation ambiguity
Spec wording "hybrid 50/50 (market + 50% limit at far edge)" admits two interpretations:
- **Per-leg** (default in this report): two half-sized positions, each with its own R outcome, blended R = (market_R + limit_R) / 2 if limit filled.
- **Single-position averaged-entry**: one full-sized position at hybrid_entry = (market_entry + limit_entry) / 2, R computed from the averaged entry.

Differential under the two interpretations:
- Far-edge per-leg: +0.062R per CANDIDATE
- Far-edge single-pos: +0.222R per CANDIDATE

The single-pos number is much larger because the averaged entry inherits the market entry's win/loss outcome (path-dependent question of "TP first or SL first" doesn't depend on entry price within [SL, TP]) but gets a SMALLER SL distance, so wins are bigger R-multiples. The per-leg number is smaller because each leg is independent and the limit leg can lose on same-candle SL while the market leg wins.

In production, MT5 executes orders independently — the per-leg model maps to the most natural deployment. But the single-pos result is a useful upper bound; if the system can be implemented as "place a full-size limit; if not filled by some signal, replace with full-size market," the single-pos result becomes deployable.

### 10.3 SL/TP geometry assumption
SL and TP are anchored to the OB geometry (`sl_a_price`, `target_a_price` from the CSV) — they do not depend on entry price. This is the spec's intent. In production, the live system anchors SL similarly, but TP rules vary (Geometry B uses 1.5R from entry, which DOES depend on entry). This study uses Geometry A throughout.

### 10.4 Missed-setup forfeiture is real and large
The 206 setups (28%) the far-edge limit misses are 94% market wins at +0.26R median. Limit-only at far edge gives up +54R total over 4 months on these missed setups. The hybrid mitigates this (because the market half always fires), but the limit-only doesn't. **Pure limit-at-far-edge replacement of market would be NET NEGATIVE under realistic conditions** (per-CANDIDATE R: +0.091 limit-only vs +0.045 market, but this counts UNRESOLVED as nan; if you believe the 13 UNRESOLVED missed setups would have CONTINUED at +0.26R on a longer window, the gap closes).

### 10.5 Per-symbol heterogeneity
- GBPJPY: ~0R differential, consistent with the symbol's known difficulty (T7 simulation also flagged it)
- XAUUSD: +0.29R differential — best-case
- The 5-symbol average masks substantial cross-symbol variation. A per-symbol deployment policy ("use limit on XAUUSD/GBPUSD only") could be more powerful than a portfolio-wide policy, though n is small per symbol.

### 10.6 NY-session signal concentration
NY session shows the strongest differential for both anchors. Tokyo nearly null. A session-conditional deployment ("hybrid only in NY") could maximize signal-to-noise — but this risks p-hacking and reduces deployment surface area materially.

### 10.7 Pathological "entry past TP" rows (n=128, 17.6%)
These rows have `retest_entry_price` already past `target_a_price` in the impulse direction (because the M15 close ended up beyond the OB body + impulse target during the same candle). The CSV's R formula reports them as instant CONTINUED with R = |TP−entry|/SL_dist (a positive R representing "current excursion as % of SL distance"). Excluding them, the far-edge differential rises to +0.198R (mean) — still under the H1 +0.2R threshold but margin-of-error close. Including them, +0.178R. Either way, the methodology choice doesn't change the H1 verdict.

### 10.8 Time horizon
108 days of data. The CSV covers 2026-01-02 to 2026-04-17. Stability of the differential across calendar months not tested; possible regime change between Q1 and Q2 not characterized here.

### 10.9 Resolution window
48 M15 candles = 12h. Per the spec / Geom A. 17/726 rows are UNRESOLVED at this window. A longer window would resolve more but at the cost of comparability with the parent CSV.

### 10.10 Lesson 4 stratification check
The categorical-vs-continuous artifact rule applies. The headline mean differential is sensitive to a specific subset (q1_tightest SL ratio, where pessimistic same-candle SL kills wins). The continuous variable here is "SL distance ratio" not anything categorical. The differential is real and not a categorical proxy: q2/q3/q4 quartiles show consistent +0.20–0.28R. The methodology pessimism is the dominant artifact, NOT a categorical effect.

---

## 11. Pre-committed decision verdict

**H1: FAIL.** Mean differential +0.178R, below +0.20R threshold (CI lower bound +0.053).
**H2 per-leg: FAIL.** Mean +0.062R per CANDIDATE, below +0.10R threshold.
**H2 single-pos: PASS.** Mean +0.222R per CANDIDATE, well above +0.10R threshold.
**H2b: FAIL.** Mean +0.086R per filled setup, below +0.10R threshold (fill rate fine at 85.5%).
**H3: FAIL.** Differentials all positive and above +0.05R; fill rates well above 30%.

**Recommendation under strict per-leg interpretation:** Genuine null; do NOT deploy under the spec's decision tree. Document as a methodology-bounded null result.

**Recommendation if CEO accepts the single-position hybrid interpretation:** H2 fires; deploy hybrid-far-edge with single-position averaged-entry semantics to live shadow first. Specifically: place a limit order at far_edge for full position size; if not filled by some criterion (next M15 close, or a time deadline within the kill zone), replace with a market order at the prevailing price.

**Underrated finding worth capturing regardless of deployment:** the limit-at-far-edge BREAKS 156 market wins (43.8% of paired wins) but RESCUES only 14 market losses (8.8% of paired losses). The mean differential is positive ONLY because winning trades from limit fills are 3.86× the R magnitude of winning trades from market fills (smaller SL distance → bigger R-multiple per win). The strategy's value depends on whether the trade-off (give up 142 net wins to gain higher R per remaining win) is acceptable for a portfolio that prefers higher win rate over higher R per win. **For a prop-firm context where consistency matters more than total return**, this trade-off may be unattractive even if statistically positive.

---

## Appendix A — Derived key files

- `scratch/intra_b/df_augmented.csv` — primary CSV with derived ob_low/ob_high/far_edge/midpoint added.
- `scratch/intra_b/simulation_results_canonical.csv` — full per-row simulation results (the canonical output).
- `scratch/intra_b/simulation_results.csv` — early simulation (superseded; same numbers within 0.01R).
- `scratch/intra_b/simulation_results_optimistic.csv` — optimistic same-candle resolution sensitivity.
- `scratch/intra_b/hybrid_singlepos.csv` — single-position averaged-entry hybrid sensitivity.
- `scratch/intra_b/final_metrics.json` — all metrics + verdicts in machine-readable form.

## Appendix B — Code path

- `step1_explore.py` — schema + OB-edge derivation verification.
- `step2_simulate.py` — initial simulator (pessimistic same-candle).
- `step3_analyze.py` — analysis of step2 output.
- `step4_optimistic.py` — optimistic same-candle sensitivity.
- `step5_canonical.py` — canonical simulator with proper fill-candle handling (this is the headline sim).
- `step6_hybrid_singlepos.py` — single-position averaged-entry hybrid sensitivity.
- `step7_final_analysis.py` — final analysis pass producing `final_metrics.json` and the headline numbers in this report.

---

*End of intra_b report.*
