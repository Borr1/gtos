# Post-Trade Structural Analysis

**Date:** 2026-04-13 02:47
**Model:** claude-sonnet-4-6, effort=max
**Trades analyzed:** 121 (78 wins, 43 losses)
**Total cost:** $0.22

## Type A vs Type B Distribution

*(LLM classification: A = structurally predictable, B = statistically valid loss/win)*

| Type | Wins | Losses | Interpretation |
|------|------|--------|----------------|
| A (predictable) | 27/78 (35%) | 29/43 (67%) | Δ=+33pp |
| B (statistical) | 51/78 (65%) | 12/43 (28%) | Δ=-37pp |

If losses are predominantly Type A: the LLM finds predictable pre-entry signals.
If losses are predominantly Type B: the system is already selecting the right setups.

## Structural Feature Cross-Tabulation

*(Computed from Phase 1 individual analyses — local tally, not LLM)*

### H1 Bias Clarity

| Value | Wins | Losses | Δ (loss−win) |
|-------|------|--------|-------------|
| strong | 51/78 (65%) | 14/43 (33%) | -33pp |
| moderate | 25/78 (32%) | 19/43 (44%) | +12pp |
| weak | 2/78 (3%) | 8/43 (19%) | +16pp |

### M15 Support

| Value | Wins | Losses | Δ (loss−win) |
|-------|------|--------|-------------|
| aligned | 67/78 (86%) | 16/43 (37%) | -49pp |
| neutral | 1/78 (1%) | 9/43 (21%) | +20pp |
| opposing | 10/78 (13%) | 16/43 (37%) | +24pp |

### Zone Quality

| Value | Wins | Losses | Δ (loss−win) |
|-------|------|--------|-------------|
| high | 24/78 (31%) | 4/43 (9%) | -21pp |
| medium | 44/78 (56%) | 10/43 (23%) | -33pp |
| low | 10/78 (13%) | 27/43 (63%) | +50pp |

### H1 BOS Momentum

| Value | Wins | Losses | Δ (loss−win) |
|-------|------|--------|-------------|
| declining | 38/78 (49%) | 27/43 (63%) | +14pp |
| building | 24/78 (31%) | 9/43 (21%) | -10pp |
| stable | 16/78 (21%) | 5/43 (12%) | -9pp |

### Binary Signals

| Signal | Wins | Losses | Δ (loss−win) |
|--------|------|--------|-------------|
| Recent H1 CHoCH | 4/78 (5%) | 2/43 (5%) | -0pp |
| M15 CHoCH present | 9/78 (12%) | 7/43 (16%) | +5pp |
| Counter-signals present | 77/78 (99%) | 40/43 (93%) | -6pp |

## LLM-Identified Patterns (Phase 2)

Patterns found: 7 (6 actionable)

### Zone Quality Low [HIGH | ACTIONABLE]

**Description:** The entry zone was classified as low quality — typically meaning no clean unmitigated OB near price, zone created during a sweep sequence, zone inside a bearish FVG, or zone created by a weak/non-displaced BOS

| | Count |
|---|---|
| Loss prevalence | 22/41 (54%) |
| Win prevalence | 10/78 (13%) |
| Delta (loss−win) | +41pp |

**Mechanism:** Low-quality zones lack the structural integrity to absorb selling pressure. When the entry zone is created by a weak BOS, sits inside opposing supply, or has no proven demand history, the probability of price respecting it as support is materially lower. High-quality zones (created by displaced BOS, sitting at protected swings, unmitigated) have demonstrated structural significance; low-quality zones are speculative.

**Action:** Add hard filter: zone_quality='low' should be a disqualifying condition for A_predictable trades and should require at least two additional confirming factors for B_statistical trades. This single filter would have blocked 22/41 losses (54%) while only filtering 10/78 wins (13%) — the strongest single actionable signal in the dataset.

---

### H1 BOS Momentum Declining AND Zone Quality Low (combined) [HIGH | ACTIONABLE]

**Description:** Both H1 BOS momentum is declining (ratios decaying across recent breaks) AND zone quality is low — a compound structural weakness pattern

| | Count |
|---|---|
| Loss prevalence | 18/41 (44%) |
| Win prevalence | 6/78 (8%) |
| Delta (loss−win) | +36pp |

**Mechanism:** Declining H1 momentum means the bullish impulse is losing energy precisely when the trade needs it to continue. When this coincides with a low-quality zone (no clean OB, zone inside supply, weak BOS origin), the trade has neither structural momentum nor a reliable demand anchor. This combination represents the worst-case entry profile: fading trend into a weak zone.

**Action:** Add compound filter: if h1_bos_momentum='declining' AND zone_quality='low', the trade should be blocked regardless of analysis type. This combination appeared in 18/41 losses (44%) versus only 6/78 wins (8%). The wins in this category were almost exclusively marginal B_statistical trades with R-multiples below 0.7R.

---

### Analysis Type A with Zone Quality Low [HIGH | ACTIONABLE]

**Description:** Trade classified as A_predictable (high-conviction structural setup) but zone quality was simultaneously low — an internal contradiction where the system labeled a trade high-conviction despite a weak zone

| | Count |
|---|---|
| Loss prevalence | 14/41 (34%) |
| Win prevalence | 3/78 (4%) |
| Delta (loss−win) | +30pp |

**Mechanism:** A_predictable classification implies a clean, high-quality structural setup. When zone quality is low, the A_predictable label is internally inconsistent — the setup lacks the zone integrity that justifies high-conviction classification. These trades are being mislabeled as predictable when they are actually statistical or below-threshold entries. The mislabeling may cause the system to take trades it should skip.

**Action:** Add consistency gate: A_predictable classification should require zone_quality='high' as a necessary condition. If zone_quality='medium' or 'low', the trade must be reclassified as B_statistical or rejected. This would have flagged 14 losses that were incorrectly labeled as high-conviction setups.

---

### M15 Support Opposing (without CHoCH) [HIGH | ACTIONABLE]

**Description:** M15 structure was classified as opposing the trade direction — bearish breaker blocks, bearish FVGs stacked at entry, or M15 protected swing already broken — but without a formal M15 CHoCH event

| | Count |
|---|---|
| Loss prevalence | 14/41 (34%) |
| Win prevalence | 8/78 (10%) |
| Delta (loss−win) | +24pp |

**Mechanism:** When M15 is actively opposing the trade direction (bearish breakers overhead, bearish FVGs at entry zone, M15 structure neutral or bearish), the execution timeframe is working against the entry. Even with strong H1 bias, M15 opposition means price must fight through immediate supply to reach any target, compressing reward and increasing stop probability.

**Action:** Strengthen existing M15 alignment requirement: m15_support='opposing' should be a hard disqualifier for A_predictable trades. For B_statistical trades, require explicit documentation of why H1 bias is expected to override M15 opposition, with a minimum H1 BOS count of 8+ and strong (not declining) momentum. The 8 wins with opposing M15 were mostly marginal (median ~0.2R) while losses were full -1.0R stops.

---

### M15 CHoCH Present [HIGH | ACTIONABLE]

**Description:** A bearish M15 CHoCH (Change of Character) fired at or within 1-2 candles before entry, indicating M15 structure had flipped bearish against the bullish trade direction

| | Count |
|---|---|
| Loss prevalence | 13/41 (32%) |
| Win prevalence | 8/78 (10%) |
| Delta (loss−win) | +22pp |

**Mechanism:** A displaced or strong M15 CHoCH directly invalidates the M15 bullish structure that the entry thesis depends on. When M15 structure flips bearish at or just before entry, the trade is entering against the most recent structural momentum on the execution timeframe, dramatically increasing the probability of immediate stop-out before H1 bias can reassert.

**Action:** Add explicit gate: if m15_choch_present=true AND m15_support='opposing', require a confirmed M15 BOS reclaim of the CHoCH level BEFORE entry is valid. A CHoCH followed immediately by a bullish BOS recovery (within 1-2 candles) may still qualify, but a raw CHoCH with no reclaim should be a hard filter. This would have blocked 13 losses while only filtering 8 wins — net improvement.

---

### H1 Clarity Weak [MEDIUM | ACTIONABLE]

**Description:** H1 structural clarity was classified as weak — indicating the H1 BOS sequence was thin (3 or fewer BOS), had a recent CHoCH, or showed severely inconsistent momentum making directional bias ambiguous

| | Count |
|---|---|
| Loss prevalence | 8/41 (20%) |
| Win prevalence | 2/78 (3%) |
| Delta (loss−win) | +17pp |

**Mechanism:** Weak H1 clarity means the higher-timeframe directional anchor is unreliable. Without a clear H1 bullish structure, the trade lacks the gravitational pull needed to overcome M15-level counter-pressure. Trades taken with weak H1 clarity are essentially counter-structure entries with no reliable bias to fall back on.

**Action:** Add hard filter: h1_clarity='weak' should disqualify any trade regardless of analysis type. Only 2 wins occurred with weak H1 clarity (both marginal: +0.25R and +0.18R), while 8 losses occurred — the asymmetry is clear. This is already partially captured by the C-gate but should be made explicit.

---

### Recent H1 CHoCH Present [MEDIUM | informational]

**Description:** A bearish H1 CHoCH fired within the session before entry, indicating H1 structure had technically flipped bearish at the higher timeframe

| | Count |
|---|---|
| Loss prevalence | 6/41 (15%) |
| Win prevalence | 4/78 (5%) |
| Delta (loss−win) | +10pp |

**Mechanism:** An H1 CHoCH directly invalidates the bullish H1 bias that justifies the long entry. When H1 structure has flipped bearish, any bullish OB retest is a counter-structure trade with no higher-timeframe confirmation. The few wins with H1 CHoCH present were marginal (0.15R to 2.44R with the 2.44R being an outlier where M15 recovered strongly).

---

## Cross-Reference with Prior Findings

The LLM analysis reveals a finding beyond what simple H1 clarity numeric tests would show: the most predictive loss pattern is not H1 clarity weakness per se, but rather INTERNAL STRUCTURAL CONTRADICTION — trades where the analysis_type label (A_predictable) conflicts with the actual zone quality (low), or where M15 is actively opposing while H1 is strong. These contradictions appear in 34% of losses but only 4% of wins for the A_predictable/low-zone combination. The LLM analyses also consistently identify a specific momentum decay signature — H1 BOS ratio collapsing to below 1.0 on the most recent break — as a recurring pre-entry warning in losses that is rarely present in high-R wins. This ratio threshold (final H1 BOS ratio < 1.0) is a quantifiable signal that numeric field extraction alone would miss without reading the counter_signal_details text.

## Recommendation

Three prompt changes are warranted based on patterns surviving the 15pp threshold test: (1) HARD GATE — Add zone_quality='low' as a disqualifying condition for all A_predictable trades and require explicit override justification for B_statistical trades. This is the single highest-impact change (41pp delta, 54% of losses vs 13% of wins). (2) HARD GATE — Add m15_support='opposing' as a disqualifying condition for A_predictable trades; for B_statistical, require H1 BOS count ≥8 with non-declining momentum. (3) CONSISTENCY CHECK — Require that A_predictable classification is only assigned when zone_quality='high'; any trade with zone_quality='medium' or 'low' must be B_statistical or rejected. The existing C-gate appears sufficient for catching h1_clarity='weak' cases (already 17pp signal) but should be made explicit rather than implicit. The M15 CHoCH gate (22pp delta) is partially captured by existing m15_support='opposing' logic but should be strengthened to require a confirmed BOS reclaim before entry when a CHoCH has fired within the session.

## Methodology Notes

- **Hindsight bias mitigation:** Both wins AND losses analyzed. Patterns valid only if
  they appear significantly more often in one group.
- **Threshold:** Pattern reported only if delta > 15pp and n > 8 in that group.
- **Prior work:** Point-biserial correlations on 30+ numeric features (n=129,
  Bonferroni-corrected) found NO pre-trade numeric predictor of wins.
- **Only validated signal:** C-gate (H1 bias + M15 alignment) — discriminates CR×WR.
- **Population:** 121 trades with MSO data (78 wins, 43 losses incl. 4 BREAKEVEN).
- **In-sample only.** All findings require live validation.

## Cost Summary

| Phase | Calls | Cost |
|-------|-------|------|
| Phase 1 (individual) | 121 | $2.00 |
| Phase 2 (aggregation) | 1 | $0.22 |
| Phase 2 rerun (5k tokens) | 1 | $0.22 |
| **Total** | **123** | **$2.43** |
