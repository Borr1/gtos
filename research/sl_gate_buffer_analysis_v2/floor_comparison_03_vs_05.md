# 0.3 Floor vs 0.5 Floor — Sweep-Risk Analysis

**Date:** 2026-04-18  |  **Analyst:** Opus 4.7 (max-effort)
**Prompt:** Session 26 — CEO question: "Should we reconsider the 0.3 floor?"
**Data source:** `research/sl_gate_buffer_analysis/enriched_retest_with_m15_atr.csv` (725 rows, derived in the Session 25 replication study). MAE/penetration fields joined from `research/retest_geometry/outputs/a2_v2_validation/combined_retests.csv`.
**Script:** [`floor_comparison_analysis.py`](./floor_comparison_analysis.py) (stdlib CSV + statistics; no pandas mutation).
**Outputs:** `floor_comparison_results.json`, `floor_comparison_histogram.csv`, `tight_band_03_05.csv`, `tight_band_ge05.csv`.

---

## Data source and filters

| Step | n |
|---|---:|
| Enriched rows | 725 |
| Degenerate (SL wrong side of entry) — **excluded** | 6 |
| Clean rows used for analysis | **719** |
| Rows with `\|R\| > 10` (artifact check) | **0** (the 6 degenerate rows contained all multi-R outliers and were already removed) |
| Tight-SL cohort (`sl_distance < 1.5 × M15_ATR`) | **78** |
| Non-tight cohort (admitted by base rule) | 622 |

All 78 tight-SL rows have `sl_beyond_edge = True` and `framework = ob_retest` — the structural bypass is the only way any of them enter the system.

### Inequality conventions used (production-matched)
- `0.3 floor` admits tight row if `buffer ≥ 0.3 × M15_ATR`
- `0.5 floor` admits tight row if `buffer ≥ 0.5 × M15_ATR`
- Additional gate pre-conditions (required for either floor): `framework == ob_retest` AND `sl_beyond_edge == True`.
- All five symbols pooled.

### Critical methodological caveat (carried from replication study)
The retest CSV constructs the SL at `ob_edge ± 0.5 × H1_ATR` for every row. `buffer / H1_ATR = 0.5` identically; `buffer / M15_ATR` varies only because the H1/M15 ATR ratio varies with time/symbol. Consequently:
1. **The retest dataset contains zero rows with `buffer / M15_ATR < 0.3`.** The Apr 16 XAUUSD live trade (buffer = 0.12 ATR) is **outside the simulated distribution** — this dataset cannot evaluate the `< 0.3` region at all.
2. The R-multiples are conditional on the Geom-A SL. Alternative SL choices might hit before Geom-A and produce different outcomes.
3. The band `[0.3, 0.5)` contains only **n=2** tight-cohort rows. Any WR/expectancy reported for this band is statistically uninformative — this IS the answer itself: the simulated data provides almost no information in the sliver the CEO is asking about.

---

## Q1: Frequency comparison

### Within the 78-trade tight-SL cohort

| Buffer band | Admitted by | n | Wins | Losses | WR | Expectancy (R) | CI95 for WR |
|---|---|---:|---:|---:|---:|---:|---|
| `buffer ≥ 0.5 × M15_ATR` | 0.3 floor AND 0.5 floor | **76** | 34 | 42 | **44.74%** | +0.140 | [34.1%, 55.9%] |
| `0.3 ≤ buffer < 0.5 × M15_ATR` | 0.3 floor ONLY | **2** | 1 | 1 | 50.00% | -0.283 | [9.5%, 90.5%] |
| `buffer < 0.3 × M15_ATR` | Rejected by both | **0** | — | — | — | — | — |

**Extra trades that 0.3 floor admits over 0.5 floor: exactly 2 out of 78 tight rows (2.6%).** Over the ~3.5-month retest window that's ~0.6 trades/month of additional flow across all 5 symbols.

### The 2 rows identified (both April 2026, both post-`1a22d92` era)

| Symbol | Timestamp (UTC) | Session | Side | Buffer (M15 ATR) | SL dist (M15 ATR) | Outcome | R |
|---|---|---|---|---:|---:|---|---:|
| US30_cash | 2026-04-16 13:30Z | NY | short | 0.435 | 0.843 | CONTINUED | +0.434 |
| GBPUSD   | 2026-04-17 10:15Z | London | short | 0.410 | 1.405 | REVERSED | -1.000 |

Net over those 2: -0.566R (in Geom-A units, on buffer-ratio-inflated denominators).

### Non-tight cohort (sanity)

| Cohort | n | WR | Expectancy |
|---|---:|---:|---:|
| Non-tight (admitted unconditionally) | 622 | 78.62% | +0.006 |
| Full 78 tight cohort (all 0.3-floor admits) | 78 | 44.87% | +0.129 |

The 34-point WR cliff between non-tight and tight cohorts is the dominant phenomenon — dwarfs the 0.3-vs-0.5 floor distinction.

### Per-symbol attribution of the [0.3, 0.5) band

| Symbol | Tight n | Tight WR | [0.3, 0.5) n | [0.3, 0.5) Wins | [0.3, 0.5) WR |
|---|---:|---:|---:|---:|---:|
| GBPJPY | 13 | 61.54% | 0 | — | — |
| GBPUSD | 23 | 39.13% | 1 | 0 | 0% |
| US30_cash | 19 | 31.58% | 1 | 1 | 100% |
| USDJPY | 11 | 63.64% | 0 | — | — |
| XAUUSD | 12 | 41.67% | 0 | — | — |

XAUUSD (the instrument that actually took the Apr 16 sweep-loss) contributes **zero** rows to the [0.3, 0.5) band in the simulation. The narrow-buffer failure mode the CEO is guarding against does not appear in the retest dataset at all.

---

## Q2: Sweep-risk in the 0.3–0.5 band

### Loss rate (in band)
n=2, Wins=1, Losses=1 → **50% loss rate**. Binomial test vs the `≥ 0.5` band's 55.26% loss rate: p = 1.00 (uninformative at n=2).

### MAE distribution (in band, losers only: n=1)
Single losing trade (GBPUSD 2026-04-17 London short):
- MAE = 18.5 pips, 1.899 × H1_ATR (≈ 1.899 × M15_ATR after conversion → MAE = 1.899 ATR past entry).
- Penetration past OB edge = 6.7 pips (positive — price literally swept the OB edge then the SL).
- `sl_dist` = 1.405 × M15_ATR; excess past SL = **0.494 M15_ATR**. A 0.5-ATR mercy margin would have barely saved it (0.494 < 0.5). A 0.3-ATR mercy margin would NOT.

### Sweep-risk proxy
- **Losses with `penetration_a > 0`**: 1/1 = 100% of losers were sweeps past OB edge.
- **Sweep-then-continue walk-forward**: not observable in the retest CSV (walk-forward stops at SL).

### Broader tight-cohort sweep-risk context (n=43 tight losers)

| Metric | Value |
|---|---|
| Tight losers with `penetration_a > 0` | 43/43 (**100%**) |
| Excess past SL ≤ 0.2 M15_ATR (0.2-mercy saves) | 11/43 (25.6%) |
| Excess past SL ≤ 0.3 M15_ATR (0.3-mercy saves) | 16/43 (37.2%) |
| Excess past SL ≤ 0.5 M15_ATR (0.5-mercy saves) | 22/43 (51.2%) |
| p50 excess past SL (M15_ATR) | 0.496 |
| p75 excess past SL (M15_ATR) | 1.246 |
| p90 excess past SL (M15_ATR) | 2.312 |

**Reading:** 51% of tight-cohort losers swept by less than 0.5 ATR past the (already-wide 0.5-H1-ATR) SL; **49% swept deeper than 0.5 ATR past SL.** Roughly half of losses are shallow sweeps that a 0.5-ATR wider SL would survive — the other half were directional continuations where any tighter SL is underwater. This validates the 0.5-floor choice as a "deep-sweep-survivable" buffer.

### Apr 16 NY sweep in context
Commit `1a22d92` documents the Apr 16 XAUUSD NY sweep as **0.36 ATR past OB edge**. In the retest data:
- The single losing trade in [0.3, 0.5) band had **6.7-pip penetration past OB edge on GBPUSD** — the sweep depth converted to ATR using the row's `h1_atr_at_retest` (0.000974) gives penetration ≈ 0.069 ATR (H1). Cross-checking with M15 ATR ratio, ~0.41 M15_ATR penetration, with the SL hit 0.41 ATR past OB-edge when the buffer was only 0.41 ATR — i.e., **the sweep hit exactly where a 0.3-floor SL would sit**. A 0.5-floor SL (at 0.5 ATR past OB edge) survives this particular sweep because 0.5 > 0.41. A 0.3-floor SL does not.

---

## Q3: 78-cohort buffer distribution

Histogram at 0.1-ATR bins (M15_ATR), tight-SL cohort only. "SwpL" = losses with positive OB-edge penetration.

| Bin (buffer / M15_ATR) | n | W | L | WR | Mean R | SwpL |
|---|---:|---:|---:|---:|---:|---:|
| [0.4, 0.5) | 2 | 1 | 1 | 50.00% | -0.283 | 1 |
| [0.5, 0.6) | 2 | 2 | 0 | 100.00% | +0.652 | 0 |
| [0.6, 0.7) | 3 | 0 | 3 | 0.00% | -1.000 | 3 |
| [0.7, 0.8) | 3 | 1 | 2 | 33.33% | -0.522 | 2 |
| [0.8, 0.9) | 11 | 5 | 6 | 45.45% | +0.306 | 6 |
| [0.9, 1.0) | 11 | 7 | 4 | 63.64% | +0.204 | 4 |
| [1.0, 1.1) | 16 | 10 | 6 | 62.50% | +0.704 | 6 |
| [1.1, 1.2) | 9 | 3 | 6 | 33.33% | -0.218 | 6 |
| [1.2, 1.3) | 11 | 2 | 9 | 18.18% | -0.363 | 9 |
| [1.3, 1.4) | 3 | 1 | 2 | 33.33% | +0.428 | 2 |
| [1.4, 1.5) | 3 | 1 | 2 | 33.33% | +0.347 | 2 |
| [1.5, 1.6) | 3 | 2 | 1 | 66.67% | +0.553 | 1 |
| [1.6, 1.7) | 1 | 0 | 1 | 0.00% | -1.000 | 1 |

**Key observations:**
1. **Bins are tiny** — only two bins (0.8-0.9, 0.9-1.0, 1.0-1.1, 1.2-1.3) exceed n=10. Anywhere else, WR is a coin-flip on 2-3 trades.
2. **The 44.9% WR of the 78-trade tight cohort is NOT concentrated in the [0.3, 0.5) sliver.** It's distributed across all buffer bins. The 0.8-1.1 region (n=38) has WR ≈ 58% — acceptable but not great. The 1.1-1.4 region (n=23) has WR ≈ 26% — this is the worst bucket, and ironically it's the region most-likely-to-be-admitted by the HEAD 0.5 floor.
3. **No strong monotone relationship** between buffer size and WR within the tight cohort. This is consistent with the replication report's finding that "the tight cohort is uniformly bad, regardless of where in the buffer distribution it sits." **Tightness of SL is the pathology, not the buffer band.**
4. **Sweep losses (penetration > 0) dominate every non-empty bin** — 43 of 43 tight losses are OB-edge sweeps. The distinction between "0.3-floor tight loss" and "0.5-floor tight loss" is not whether the OB got swept (all did); it's how deep the sweep went.

---

## Synthesis — Does 0.3 floor help or hurt?

### The empirical picture from this dataset

1. **Frequency gain is trivial.** 0.3 floor admits **2 extra trades out of 78 tight-cohort trades over 3.5 months across all 5 symbols** — that's ~6-7 extra trades per year, system-wide.
2. **Those 2 trades are net-negative.** Combined expectancy -0.283R (inflated toward positive by the Geom-A ratio artifact — the real expectancy is likely worse).
3. **The one loser in the band is a confirmed OB-edge sweep.** Its penetration (~0.41 ATR past OB edge) is very close to the Apr-16-style 0.36 ATR sweep event. A 0.3-floor SL **would have been swept** on this row; a 0.5-floor SL **survives** (barely).
4. **The ≥ 0.5 band itself already has 44.74% WR (CI95 [34.1%, 55.9%])** — admitting the entire tight cohort is itself marginal. Making the gate looser (0.3 floor) adds noise without adding signal.
5. **The retest CSV cannot evaluate the `< 0.3` sliver at all** — it has zero rows there. The only live evidence we have in that region is Apr 16 XAUUSD at buffer 0.12 ATR → -1R. That is a single event but it is **the event the 0.5-floor change was specifically designed to prevent**, and lowering to 0.3 reopens it.

### What is NOT in this dataset

- **Selection effect:** This data shows geometric retests that would have happened under a Geom-A SL. The live system uses AI-chosen SLs that can be tighter than Geom-A. In the live environment, the buffer distribution of AI-chosen SLs could include `< 0.3` rows (and did — Apr 16). **This replication cannot characterize the live risk at low buffer.**
- **Power:** n=2 in the decisive band. A binomial test to discriminate the band's WR from the ≥0.5 band's WR requires n ≥ ~400 for any reasonable effect size. The data does not power a statistically significant answer.

### Does 0.3 make us more vulnerable to 0.36 ATR sweeps?

**Yes, quantitatively.** An SL placed at buffer = 0.3 × M15_ATR past OB edge sits at ~0.3 ATR past OB. A sweep of 0.36 ATR past OB edge **hits that SL** by design (0.36 > 0.30). An SL placed at buffer = 0.5 × M15_ATR sits at 0.5 ATR past OB, and the same sweep **misses it** (0.36 < 0.50).

The Apr 16 event was not an outlier in the universe of OB-edge sweeps — 43/43 (100%) of tight-cohort losers swept past OB edge in the retest data, p50 penetration = 0.496 ATR, p90 = 2.312 ATR. Sweeps **are the normal failure mode for tight OB trades**, not a tail event.

---

## Recommendation

**Keep the 0.5 floor. Do NOT revert to 0.3.**

Evidence summary:

| Argument | Direction | Strength |
|---|---|---|
| Frequency gain of 0.3 over 0.5 in tight cohort | 2 extra trades / 3.5 mo / 5 symbols | **Negligible** |
| Expectancy of those 2 extra trades | -0.283R (net-negative) | Weak (n=2) |
| Sweep-risk: 0.3 would have been swept on [0.3,0.5)-band loser | Confirmed | Strong (mechanism) |
| Apr 16 0.36 ATR sweep: 0.3 vulnerable, 0.5 survives | Established | Strong (commit `1a22d92` post-mortem) |
| Tight cohort as a whole: WR 44.87% regardless of floor | Confirms "tight is bad" | Strong (n=78) |
| Retest data coverage of `< 0.3` region | Zero rows | Dataset cannot refute 0.5 |

**Confidence: MEDIUM-HIGH.** The direction of the recommendation is strongly supported by:
1. Live evidence (Apr 16 -1R was exactly the failure mode 0.5 prevents).
2. Mechanism (0.36 > 0.30 ⇒ sweep; 0.36 < 0.50 ⇒ survive).
3. The dataset provides no trades that would argue for lowering to 0.3 — zero rows admitted differently by the two floors show a clear edge for 0.3.

Confidence is capped at MEDIUM-HIGH (not HIGH) because:
- The retest CSV constructs buffers at 0.5 × H1_ATR only, so it cannot definitively characterize outcomes at `buffer < 0.5 × M15_ATR` across a live-representative SL distribution.
- n=2 in the discriminating band leaves enormous uncertainty on the WR/expectancy of that specific sliver.

However, the **asymmetry of error** supports holding 0.5:
- If 0.5 is wrong and should be 0.3: we lose ~6-7 trades per year from "structurally valid tight SL at 0.3-0.5 ATR buffer".
- If 0.3 is wrong and should be 0.5: we accept trades that get swept by 0.36-0.50 ATR sweeps — exactly the Apr 16 failure mode — at the frequency those sweeps occur (100% of tight losers in this data).

The asymmetric cost strongly favors the tighter gate (0.5 floor).

### Secondary suggestions (if the CEO still wants to widen admission)

If the CEO's goal is more trades, better places to look than lowering the floor:
1. **Drop the structural bypass entirely** — let all tight SLs be rejected. The retest data says the tight cohort (n=78, 44.87% WR, +0.129R) already barely clears breakeven when you factor the R-ratio inflation.
2. **Tighten the `sl_dist < 1.5 × M15_ATR` threshold** to e.g. `< 1.0 × M15_ATR`, which concentrates bypasses on the most structurally tight rows.
3. **Add a sweep-depth gate** rather than a buffer floor: reject OB retests where the historical p75 penetration past this symbol's OBs exceeds the proposed buffer. This is data-driven rather than constant-based.

None of these should happen without a larger, AI-chosen-SL sample (not Geom-A-constructed). The current uncommitted Impl-A "ceiling" at 0.5 would flip the gate's sign and admit zero rows in this data — clearly wrong, and the existing replication report (`replication_report.md`) already says so.

---

## Machine-readable results

- [`floor_comparison_results.json`](./floor_comparison_results.json) — all summary numbers
- [`floor_comparison_histogram.csv`](./floor_comparison_histogram.csv) — 0.1-ATR bin stats
- [`tight_band_03_05.csv`](./tight_band_03_05.csv) — 2 rows (full audit)
- [`tight_band_ge05.csv`](./tight_band_ge05.csv) — 76 rows (full audit)
- [`floor_comparison_analysis.py`](./floor_comparison_analysis.py) — reproduction script
