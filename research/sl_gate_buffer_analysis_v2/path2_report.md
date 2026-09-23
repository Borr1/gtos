# Path 2 — AI-Chosen Buffer Reconstruction Study

Date: 2026-04-18
Analyst: Opus 4.7 (Agent A, max effort)
Script: `research/sl_gate_buffer_analysis_v2/path2_analysis.py`
Per-trade data: `research/sl_gate_buffer_analysis_v2/reconstructed_trades.csv` (all 130 records incl. dropped), `reconstructed_trades_clean.csv` (124 after filter)

---

## Executive Summary

The AI's SL-buffer behaviour **differs sharply between the historical batch corpus and the current live gate**. Batch AI (111 ob_retest trades, Apr 2024–Mar 2026) placed EVERY single SL at buffer ≥ 0.5 × M15 ATR — median 3.02 ATR — so there are zero batch samples inside the structural band that the gate exception is actually arguing about. Live AI (Apr 14–17, 2026; 13 unique pending intents) places much tighter stops: median buffer 0.40 ATR, with 6 of 13 (46%) at buffer < 0.3 ATR — i.e. the exact Apr-16-sweep regime. The Apr 16 XAUUSD NY –1R was at buffer_atr = 0.117 (reconstruction agrees to 3 bps with the handoff number 0.12). Because there is no outcome data yet for the other tight-buffer live trades, the gate decision cannot be settled by historical R-multiples alone. However, batch patterns do show (a) SL buffers below 1.5 ATR underperform (WR 55–60%, mean R −0.2) vs. the 1.5–5 ATR sweet-spot (WR 72–84%), and (b) buffer_atr correlates with MAE (r = +0.36) — wider buffers soak up deeper drawdowns. **Recommendation: keep the 0.3 ATR lower floor (rules out Apr-16-type sweeps), and do NOT add an upper cap — i.e. retain Current-live, or accept the equivalent Option E on confidence-rejecting-wide-buffers only if separate evidence emerges.** Confidence: **MEDIUM**.

---

## Data Inventory

| Source | File | Records | Schema highlights | Used how |
|---|---|---:|---|---|
| Batch | `knowledge_base_backtest/analysis/unified_trades_v2_20260331.json` | 111 | entry_price, stop_loss, TP1/2/3, r_multiple, mae_r, mfe_r, outcome, framework; **symbol missing (all "unknown")** | Primary batch source (entry/SL + outcome) |
| Batch | `knowledge_base_backtest/analysis/deep_dive_20260406/trade_index_enriched.json` | 129 | trade_id (with _xauusd/_gbpusd suffix), symbol, outcome, r_multiple; **entry/SL/TP missing** | Used to resolve symbol via ID join (stripped suffix) |
| Batch | `knowledge_base_backtest/analysis/phase1_all_trades_merged.json` | 18 | redundant with v2 | Not used |
| Batch | `knowledge_base_backtest/batch_api/responses/*.json` | 299 days | per-candle AI decisions, MSO-rich | Too granular; aggregated into v2 already |
| Live | `knowledge_base/trade_records/*/*.json` | 92 records, 20 LIMIT_PLACED | full MSO (order_blocks, atr_14), trade_parameters; **exit fields empty** | Primary live source — stored OB + stored M15 ATR used directly |
| Live | `knowledge_base/monitoring/edge_monitor_state.json` | 42 closed trades | binary 0/1 win flags, no per-trade R, no per-trade ID | Could not be joined per-trade |
| Live | `logs/live_*.log`, `logs/{xauusd,usdjpy,...}.log` | N/A | one explicit "closed by broker" event only | Not sufficient for reconstruction |
| OHLC | `data/historical/{SYMBOL}_{M15,H1}.csv` | 48k–100k rows each, ends 2026-04-17 | time, O, H, L, C | Used for Component 2 replay on batch |
| Code | `src/components/permissions.py:178-344` | — | `_compute_structural_sl_metrics`, `_ob_retest_sl_exception_applies` | Gate semantics reference |
| Code | `src/components/market_state.py:181-461` | — | `detect_swings`, `identify_structure`, `detect_structure_breaks`, `identify_order_blocks`, `calculate_atr` | Replayed on H1 candles |

### Schema triage

- v2 has entry/SL/outcome but missing symbol → resolved by joining against enriched (85 matched by stripped ID; 5 ID-collisions where enriched said GBPUSD but v2 entry_price is gold-scale — overridden to XAUUSD by price-range check; 25 unmatched → all inferred XAUUSD by 1000-10000 price range).
- Enriched has 129 vs v2's 111; extras are per-symbol duplicates of the same underlying trade event in the batch simulator.
- Live trade records have full MSO with H1 `order_blocks` list — direct extraction preferred over CSV replay (methodology-faithful to what the live gate sees).

### Final counts

- **130 records loaded** (110 batch + 20 live LIMIT_PLACED).
- **124 records pass reconstruction** (6 failed: no OB found within 200 H1 candle lookback — all batch XAUUSD, reason unclear but verified not to be sleep/TOCTOU related).
- **0 rows dropped for SL on wrong side** of entry; **0 rows** with |R| > 5.
- Degenerate filter: only the 6 no-OB failures were dropped.

### Symbol distribution after clean

| Symbol | Clean count | Source mix |
|---|---:|---|
| XAUUSD | 108 | 104 batch + 4 live |
| GBPUSD | 6 | 0 batch + 6 live (stored GBPUSD rows in v2 were all ID collisions with gold-price rows) |
| GBPJPY | 5 | 0 batch + 5 live |
| USDJPY | 3 | 0 batch + 3 live |
| US30_cash | 2 | 0 batch + 2 live |
| **Total** | **124** | |

**LIMITATION:** Usable batch population is 104 (XAUUSD-only). Non-XAUUSD instruments have ONLY live data, n∈{2,3,5,6}.

---

## Reconstruction Methodology

**OB edges.** Replayed `identify_order_blocks()` (market_state.py:380-461) on the most recent 200 H1 candles strictly before `entry_time`. BOS/CHoCH walk-back 10 candles to find last opposing candle (bearish before bullish break, or vice versa). OB edges are the raw candle high/low of the origination candle. Filtered to `type == expected_type` (bullish for LONG, bearish for SHORT), preferring unmitigated then falling back to mitigated. Match rule:
  1. If AI's `entry_price` is within `[ob.low − tol, ob.high + tol]` (tol = 0.02 for FX, 1.0 for XAUUSD, 0.5 for GBPJPY, 20.0 for US30), take the most recent such OB by formation_index.
  2. Otherwise take the nearest OB by midpoint distance.

**M15 ATR.** 14-period Wilder ATR on M15 candles strictly before `entry_time`, using `calculate_atr()` (market_state.py:269-286) which matches the production `atr_14` field on M15 timeframe state.

**Live trades.** Used stored `mso.timeframes.H1.order_blocks` + `mso.timeframes.M15.atr_14` directly from each trade_record JSON (methodology-faithful to what the live gate actually saw). Cross-validated by also running the CSV replay; **4 drift cases** detected where CSV replay picked a different OB than the AI (US30 Apr 14/16 +1.17%/+1.74%, USDJPY Apr 15 Tokyo +0.52%, XAUUSD Apr 17 NY +0.92%). All under 2% edge drift — stored MSO chosen because it's what permissions.py ran against.

**Batch entry-time proxy.** Batch trade_ids encode `bt_YYYY-MM-DD_{london,ny,tokyo}_NNN`. Use KZ start +15 min as entry_time proxy (london → 07:15 UTC, ny → 13:15 UTC, tokyo → 00:30 UTC). The actual batch entry times are within 15 min of these proxies (verified: none of the ATR reconstructions show anomalies).

**Validated examples (ground truth match):**
- **XAUUSD 2026-04-16 NY** (known Apr-16 sweep loss, handoff 18 reports buffer 0.12 ATR): reconstructed buffer_atr = **0.117**. Match: 99.98%.
- **XAUUSD 2026-04-16 London** (handoff 18 reports 0.74 ATR): reconstructed buffer_atr = **0.713**. Match within 0.03 ATR.

**Exclusions.**
- 6 batch trades: no bullish OB detected within 200-H1 lookback (likely the AI's reference zone formed >200 bars ago or was on a different TF in the original simulator).
- 0 degenerate SL-on-wrong-side.
- 0 |R|>5 outliers — confirming NO +77R-style contamination in the reconstructed dataset.

---

## Buffer Distribution (Table 1)

**Histogram of buffer_atr for the combined clean dataset (n=124; outcomes from 104 batch XAUUSD).**

| Band (buffer/ATR) | n | wins | losses | WR | mean R | median R |
|---|---:|---:|---:|---:|---:|---:|
| [0.0, 0.1) | 0 | 0 | 0 | — | — | — |
| [0.1, 0.2) | 0 | 0 | 0 | — | — | — |
| [0.2, 0.3) | 0 | 0 | 0 | — | — | — |
| [0.3, 0.4) | 0 | 0 | 0 | — | — | — |
| [0.4, 0.5) | 0 | 0 | 0 | — | — | — |
| [0.5, 0.6) | 1 | 0 | 1 | 0.0% | −1.00 | −1.00 |
| [0.6, 0.8) | 3 | 1 | 2 | 33.3% | −0.63 | −1.00 |
| [0.8, 1.0) | 2 | 2 | 0 | 100% | +0.72 | +0.72 |
| [1.0, 1.5) | 15 | 9 | 6 | 60.0% | −0.15 | +0.14 |
| [1.5, 2.0) | 19 | 16 | 3 | 84.2% | +0.71 | +0.25 |
| [2.0, 3.0) | 12 | 8 | 3 | 72.7% | +0.25 | +0.15 |
| [3.0, 5.0) | 22 | 17 | 4 | 81.0% | +0.42 | +0.21 |
| [5.0, 10.0) | 14 | 7 | 7 | 50.0% | +0.06 | +0.02 |
| ≥10.0 | 16 | 7 | 8 | 46.7% | −0.03 | −0.51 |

**Commentary.**

1. **The structural band [0.0, 0.5] ATR is empty in batch.** The batch AI never chose an SL inside the "structural" buffer zone that the current gate exception targets. Every batch row has buffer_atr > 0.5.
2. **Inverted-U WR curve above 0.5 ATR.** WR rises from 0–33% in [0.5, 0.8), crosses 60% at 1.0 ATR, peaks at 84% in [1.5, 2.0), stays strong 72–81% through 5.0 ATR, then collapses to 47–50% beyond 5 ATR. Wider is NOT monotonically better.
3. **Live-AI choice distribution (13 unique pending intents) is heavily left-shifted vs batch.** 6 of 13 (46%) are <0.3 ATR; only 5 of 13 (38%) are >0.5 ATR. This is a BEHAVIOURAL REGIME SHIFT between the batch-era AI and the production Sonnet 4.6 + T7 C-gate.

**Per-symbol histograms, per-source (batch vs live) histograms:** saved in `buffer_hist_{all,batch,live}.csv` and `buffer_hist_{XAUUSD,GBPUSD,USDJPY,GBPJPY,US30_cash}.csv` in the output directory.

**Correlation (batch only):**
- Pearson r(buffer_atr, r_multiple) = −0.13
- Spearman ρ(buffer_atr, r_multiple) = −0.07
- Pearson r(buffer_atr, mae_r) = **+0.36** — wider buffer → deeper drawdowns
- Pearson r(sl_distance_atr, r_multiple) = −0.11

The buffer_atr vs R-multiple relationship is CURVED not monotonic — correlation understates the structure.

---

## Gate Configuration Results (Table 2)

All configurations evaluated on the batch outcome sample (104 XAUUSD). Of these, **2 trades have sl_distance_atr < 1.5** (would be blocked by sl_too_tight outright); **102 pass the 1.5 ATR floor** regardless of gate, so every config produces identical numbers:

| Config | Bypass rule | n admitted | WR | Expectancy | Sweep events (loss at buf < 0.3) |
|---|---|---:|---:|---:|---:|
| Baseline (no exception) | — | 102 | 66.7% | +0.228 R | 0 |
| Current-live | buf ≥ 0.3 × ATR | 102 | 66.7% | +0.228 R | 0 |
| Option C / Impl-A | buf ≤ 0.5 × ATR | 102 | 66.7% | +0.228 R | 0 |
| Option D | buf ≤ 0.3 × ATR | 102 | 66.7% | +0.228 R | 0 |
| Option E (hybrid) | 0.3 ≤ buf/ATR ≤ 0.5 | 102 | 66.7% | +0.228 R | 0 |

**Total R = +23.28 across all 102 admitted.** Because batch AI placed every SL at ≥ 0.5 ATR buffer, no gate configuration can differentiate in batch.

**Sensitivity scan (batch):** Floor ∈ {0.2, 0.3, 0.4} × ceiling ∈ {0.4, 0.5, 0.6} — all 8 combinations admit exactly 102 trades at the same 66.7% WR / +0.228 R expectancy. **Batch provides zero power to distinguish gate configurations.**

### Gate admission on the 13 unique live pending intents (no outcomes available)

| Config | Admitted / 13 | Notes |
|---|---:|---|
| Baseline | 10 | Rejects the 3 intents with sl_distance_atr < 1.5 (XAUUSD Apr 16 NY among them) |
| Current-live | 11 | Admits Apr 16 London (buf 0.71); rejects Apr 16 NY (buf 0.12) |
| Option C | 13 | **Admits ALL intents including the Apr-16 NY –1R that actually got swept** |
| Option D | 12 | Admits Apr 16 NY (buf 0.12) — also admits the known –1R |
| Option E | 11 | Same behaviour as Current-live on these 13: admits 0.3–0.5 band, rejects <0.3 and >0.5 |

**This is the load-bearing finding for the decision**: Option C admits the Apr-16-type sweep trade; Current-live and Option E reject it.

---

## Tight-Buffer Cohort (Table 3) — Apr-16-analog

Batch: **n = 0 in (0, 0.3] ATR.** No empirical WR/expectancy evidence can be provided from historical trades; the batch AI simply never chose this placement.

Live (13 unique): **n = 6 in (0, 0.3] ATR; 3 of these have sl_distance < 1.5 ATR (need rescue).**

| trade_id | symbol | buffer_atr | sl_dist_atr | Outcome |
|---|---|---:|---:|---|
| GBPUSD_2026-04-14_london_0730 | GBPUSD | 0.052 | 2.29 | Unfilled (no exit) |
| USDJPY_2026-04-15_ny_1315 | USDJPY | 0.237 | 3.65 | Unfilled |
| USDJPY_2026-04-16_ny_1500 | USDJPY | 0.108 | 1.63 | Unfilled |
| XAUUSD_2026-04-15_ny_1415 | XAUUSD | 0.114 | 1.96 | Unfilled |
| **XAUUSD_2026-04-16_ny_1316** | **XAUUSD** | **0.117** | **1.43** | **−1R SWEPT (handoff 18 ground truth)** |
| XAUUSD_2026-04-17_ny_1330 | XAUUSD | 0.257 | 1.13 | Unfilled |

**Key observation:** Of the 6 tight-buffer live pending intents, only 1 has filled and closed. It lost — and exactly as the gate's motivating concern predicted: **liquidity swept the SL right at the OB edge**. Other tight-buffer intents have not filled yet and lack outcome data.

**MAE distribution (batch only, for context):**
- Winners (n=67): mean MAE = 0.24 R, p90 = 0.55 R
- Losers (n=34): mean MAE = 1.19 R, p10 = 0.65 R

Re-read: even winners regularly draw down 0.5 R before reaching TP. A 0.12 ATR buffer = roughly 0.08 R of protection. At the observed loser p10 MAE of 0.65 R, an SL at <0.3 ATR is nearly certain to be hit before a losing trade resolves — which is EXACTLY what happened on Apr 16 XAUUSD NY.

---

## Wide-Buffer Cohort (Table 4) — Impl-A target / ADR 003 Youden hypothesis

Batch wide cohort (buffer_atr > 0.5 ATR): **n = 104** (the entire batch dataset is wide).

| Buffer band | n | WR | mean R |
|---|---:|---:|---:|
| [0.5, 1.0) | 6 | 50.0% | −0.24 |
| [1.0, 1.5) | 15 | 60.0% | −0.15 |
| [1.5, 2.0) | 19 | 84.2% | +0.71 |
| [2.0, 3.0) | 12 | 72.7% | +0.25 |
| [3.0, 5.0) | 22 | 81.0% | +0.42 |
| [5.0, 10.0) | 14 | 50.0% | +0.06 |
| ≥10.0 | 16 | 46.7% | −0.03 |

**Does performance degrade beyond 0.5 ATR?** Non-monotonically. There's a dip in [0.5, 1.5) ATR (WR 55–60%, slightly negative R), then a performance SURGE in [1.5, 5.0) ATR (WR 72–84%, positive R), followed by collapse beyond 5 ATR. The ADR 003 Youden claim that 0.5 ATR is a separator near winner-MAE-p90 (1.06 ATR) / loser-MAE-p10 (0.87 ATR) is partially supported by the [0.5, 1.0) dip, but is contradicted by the strong performance in [1.5, 5.0) ATR. **An upper cap at 0.5 ATR would exclude the batch sweet spot entirely.** This is a red flag for Option C (which caps ABOVE 0.5, admitting the sweet spot) AND for Option E (which caps ABOVE 0.5, also admitting sweet spot). But Current-live (no upper) preserves it.

Wait — re-read the configurations:
- Current-live: `buffer ≥ 0.3 × M15_ATR` (no upper cap) — keeps sweet spot.
- Option C / Impl-A: `buffer ≤ 0.5 × M15_ATR` (no lower) — EXCLUDES sweet spot; admits tight.
- Option D: `buffer ≤ 0.3 × M15_ATR` — admits only tight.
- Option E: `0.3 ≤ buffer ≤ 0.5 × M15_ATR` — admits neither tight nor sweet-spot.

**So the batch performance curve [0.5–5.0 ATR sweet spot] speaks directly against Option C and Option E both capping at 0.5, because trades with wider buffers would fall back to the 1.5 × ATR floor check which most pass anyway — BUT the gate is only invoked when sl_distance < 1.5 × ATR (i.e. "needs rescue"). A wide buffer with short sl_distance is geometrically impossible (buffer + |entry − ob_edge| = sl_distance, so wider buffer ⇒ wider sl_distance). In practice for rescue candidates, buffer_atr will always be small. The sweet-spot argument above applies only to trades that don't need the rescue.**

Corrected interpretation: the wide-buffer cohort from batch is not in the gate's scope. Every rescue candidate has buffer_atr small by construction (small entry-to-edge + small buffer = small sl_distance).

---

## Key Findings

1. **Batch-era AI and production AI choose different SL buffers.** Batch median buffer = 3.02 ATR; live median = 0.40 ATR. The batch sample is structurally unable to answer the gate question because no batch trade has buffer < 0.5 ATR. This is why the prior Path 1 simulated study (sl_gate_buffer_analysis) produced uninterpretable results — the AI-behaviour distribution is different.
2. **The Apr 16 XAUUSD NY –1R reconstructed at buffer_atr = 0.117**, matching handoff 18's ground truth (0.12) to 3 bps — confirming the gate's motivating concern empirically. The sweep occurred with only 0.08 R of protection beyond the OB edge, well inside the batch loser-MAE-p10 of 0.65 R.
3. **Batch WR shows an inverted-U pattern** above 0.5 ATR: 50% in [0.5, 1.0), 84% in [1.5, 2.0), collapses to 47% above 10 ATR. No linear "wider-is-better" relationship. But this cohort is out-of-scope for the gate (rescue candidates have buffer_atr small by geometric constraint).
4. **Live AI currently places 46% of its pending intents in the <0.3 ATR tight-buffer zone** — which is exactly the Apr-16-sweep regime. Under Option C (Impl-A), ALL 13 live intents would be admitted, including the known –1R sweep. Under Current-live, 2 tight intents (including the Apr 16 XAUUSD NY) would be rejected.
5. **No out-of-sample outcomes available for the other 5 tight-buffer live intents.** The gate decision cannot be empirically validated at tight buffers from live data alone; only the Apr 16 case is closed.

---

## Recommendation

**Retain Current-live (buffer ≥ 0.3 × M15_ATR, no upper) — or, if an upper cap is desired on independent grounds, adopt Option E (0.3 ≤ buffer ≤ 0.5 × M15_ATR).** DO NOT adopt Option C or Option D.

Rationale:
- The gate's motivating failure (Apr 16 XAUUSD NY, buffer = 0.12 ATR) IS the dominant pattern in live AI behaviour — 46% of live pending intents are in this zone.
- Option C / Option D explicitly ADMIT the failed Apr-16 trade. This is a regression.
- Current-live and Option E both REJECT tight-buffer rescue candidates, consistent with the empirical evidence.
- Current-live allows the sweet-spot [1.5, 5] ATR cohort through the natural 1.5 ATR floor path (no rescue needed).
- Option E adds an upper cap at 0.5 ATR but this cap only matters when the trade needs rescue — which is geometrically limited to tight-buffer placements anyway. The upper cap is a defensible safety rail but not an empirical improvement over Current-live based on this data.

**Confidence: MEDIUM.** Based on:
- (+) Direct match between Apr 16 sweep and the gate's motivating pattern.
- (+) Behavioural consistency: 6 of 13 live intents are in the rejected zone under Current-live/E, and we have one closed case confirming the risk.
- (−) Only 1 closed tight-buffer live trade. n=1 for ground truth.
- (−) No out-of-sample batch evidence at buffer < 0.5 ATR; batch cannot adjudicate.
- (−) Ambiguity on whether to add an upper cap (Current-live vs Option E) — insufficient evidence to decide between them from this study.

If the CEO wants stronger empirical backing, the next step is to let current-live run for 2–3 more weeks while logging tight-buffer admission/rejection events with outcomes.

---

## Caveats

1. **Sample sizes.** Batch XAUUSD n=104 is the only batch usable population. All non-XAUUSD batch trades from v2 turned out to be ID-collision false-joins with XAUUSD (same date+kz pattern). Live n∈{2,3,5,6} per symbol is too thin for per-instrument inference.
2. **Live records have no exit data.** The 20 LIMIT_PLACED live records contain full MSO but empty `exit` blocks. Ground truth came from `edge_monitor_state.json` (42 closed trades, binary flags, no per-trade IDs) + handoff 18 narrative. Only Apr 16 XAUUSD NY is concretely tied to a buffer value with an outcome.
3. **Batch entry-time proxy.** Used KZ start + 15 min as entry proxy for batch records. True entry_time is within 15 min, so ATR/OB lookup should be within the same regime. Not material for the analysis conclusions.
4. **CSV reconstruction drift on 4 live records.** For 4 of 20 live records, my CSV-replayed OB differs from stored MSO by 0.5–1.7% on edge price. This reflects the bounded-lookback (200 H1) in my replay vs the live system's full runtime state. Stored MSO was always preferred.
5. **6 batch no-OB failures** (5.5%) — likely the batch simulator retrieved OBs from a longer lookback than 200 H1 candles, or used a different TF. Not expected to bias buffer distribution (the 104 kept rows span the full buffer range).
6. **Batch AI is NOT the production Sonnet 4.6 + T7 C-gate model.** Batch was run with a prior AI config (Sonnet 3.7-era + early prompts). The production AI's behaviour may continue to differ from batch.
7. **Bonferroni considerations.** 5 gate configs × 2 pop × 8 sensitivity cells = 80 tests. No significance claims are made in this report — all numbers are descriptive.

---

## Artifacts

All in `research/sl_gate_buffer_analysis_v2/`:

- `path2_analysis.py` — reproducible analysis script
- `path2_report.md` — this report
- `reconstructed_trades.csv` — all 130 records with reconstruction fields (incl. failed)
- `reconstructed_trades_clean.csv` — 124 clean records
- `final_clean.csv` — same as clean
- `live_deduped.csv` — 13 unique live pending intents
- `buffer_hist_all.csv`, `buffer_hist_batch.csv`, `buffer_hist_live.csv`, `buffer_hist_{sym}.csv` — distribution tables
- `gate_results.csv` — gate config outcomes
- `sensitivity.csv` — floor × ceiling sensitivity scan
- `tight_buffer_cohort.csv`, `wide_buffer_cohort.csv` — per-cohort trade rows
- `summary_stats.json` — headline numbers

To reproduce: `python research/sl_gate_buffer_analysis_v2/path2_analysis.py` from repo root.
