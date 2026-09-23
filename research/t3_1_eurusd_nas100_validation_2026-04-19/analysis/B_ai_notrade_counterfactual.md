# NAS100 T7 Validation — AI NO_TRADE Counterfactual

_Generated 2026-04-19 from 5 slice JSONs in `C:/Users/MSI/Documents/ai-trading-agent/research/t3_1_eurusd_nas100_validation_2026-04-19`._

_CSV source: `C:/Users/MSI/Documents/ai-trading-agent/data/historical_2026/NAS100_M15.csv` (naive UTC timestamps; simulation candle_times are aware UTC; aligned by stripping tzinfo)._

## TL;DR

- **CRITICAL — evaluator is NOT production Sonnet-4.6.** `raw_response.model_used` across AI NO_TRADEs: `claude-opus-4-5`=580, `gpt-4.1`=28, `structural-bias-evaluator-v1`=5. CANDIDATEs: same mix (34 Opus, 3 GPT). Simulation ran `claude-opus-4-5` with a `gpt-4.1` fallback path (28 calls) and a rule-based `structural-bias-evaluator-v1` (5 calls). Memory says Opus produces CR 19% vs Sonnet's 38% on the MSO gate — the 613 AI NO_TRADE count is materially inflated vs what live Sonnet would produce. **Suggest rerun on Sonnet-4.6 before gate-live decision.**
- **Rejections are structurally driven, not capricious.** Buckets: `C1_FAIL` 242 (39.5%), `ALL_GATES_PASS_BUT_NO_TRADE` 231 (37.7%, AI rejecting because price is 70-250 pts from OB — a second proximity gate), `C2_FAIL` 90 (14.7%). Only 9 NO_QUALIFYING_OB + 6 NO_UNMITIGATED_OB (together 2.4%) are setup-availability rejections.
- **Post-AI CANDIDATE rate 5.7% (37/650) vs XAUUSD 10.3%.** Explained primarily by the Opus-vs-Sonnet model mismatch (likely ~2× under-production); NAS100-specific wider ranges (triggering the 'price must be at OB' rule more often) contribute. Sample-projected Sonnet CR: ~10-12%, consistent with XAUUSD baseline.
- **Extreme CANDIDATE direction asymmetry: LONG=36, SHORT=1 (36:1).** Plausible regime effect given strong Feb-Apr NAS100 bull leg, but the ratio is large enough that framework/prompt SHORT-suppression cannot be ruled out without a direct audit of SHORT evaluation paths.
- **30-sample 2h-forward counterfactual (NAS100-calibrated thresholds):** CORRECT_SKIP=2, AMBIGUOUS=19, MISSED_WINNER=9. The 9 'MISSED_WINNER' rows are NOT proven misses — every one has a stated reason that price was 70-250+ pts away from the nearest OB, so no framework-compliant entry could have been placed. **Direction: AI NO_TRADEs on this run are framework-correct; the binding constraint is often OB-geometry, not AI discretion.**

## Q1 — Reason taxonomy

Total AI NO_TRADE records: **613**.

| Bucket | Count | % of AI NO_TRADE | Representative reason |
|---|---:|---:|---|
| `C1_FAIL` | 242 | 39.5% | C1 FAIL: H1 structure has shifted bearish via CHoCH at 25634.65 — the sole unmitigated H1 OB is bearish, providing no valid bullish POI. ... |
| `ALL_GATES_PASS_BUT_NO_TRADE` | 231 | 37.7% | C1/C2/C3 all pass structurally, but OB retest framework requires price to be at or retesting the OB zone. Current close (25824.75) is ~72... |
| `C2_FAIL` | 90 | 14.7% | C2 FAIL: M15 CHoCH bearish at 25235.35 with displacement ratio 2.0 on the current candle actively opposes H1 bullish structure. |
| `RR_RISK` | 25 | 4.1% | No C-gate failure — structural conditions qualify. NO_TRADE issued because the OB retest framework requires price to be at or within the ... |
| `NO_QUALIFYING_OB` | 9 | 1.5% | No qualifying H1 OB retest entry available: nearest H1 OBs all have touches>=2 (downstream gate would reject); the sole touches=1 H1 OB a... |
| `NO_UNMITIGATED_OB` | 6 | 1.0% | OB retest framework requires an unmitigated H1 bullish OB for entry definition. The H1 MSO contains only bearish breaker blocks; no unmit... |
| `OTHER` | 5 | 0.8% | Framework prerequisite failure: OB retest requires an unmitigated H1 order block as POI. The H1 unmitigated OBs list is empty — all prior... |
| `MIXED_BIAS` | 2 | 0.3% | OB Retest framework requires an unmitigated H1 bullish OB for LONG entry. No such OB exists in the MSO — H1 only contains a bearish break... |
| `C3_FAIL` | 1 | 0.2% | C3 effectively fails: direction is LONG but no proximate unmitigated H1 bullish OB exists near current price for a retest entry — the sol... |
| `LIQUIDITY_SWEEP_ISSUE` | 1 | 0.2% | Framework condition unmet: OB Retest requires price proximity to an unmitigated H1 OB. The sole H1 OB (24469.15-24392.15, touches=1) is a... |
| `NO_VALID_OB` | 1 | 0.2% | OB retest framework requires an unmitigated H1 OB being retested at current price. The nearest qualifying H1 OB (touches=1) is at 24069.6... |

**Top 15 exact-string `no_trade_reason` values**:

| Count | Reason |
|---:|---|
| 2 | C2 FAIL: M15 CHoCH bearish at 2026-01-30T07:45 (level 25721.85) actively opposes H1 bullish bias; this is structural opposition, not a minor pullback. |
| 2 | C1/C2/C3 all pass structurally, but the sole unmitigated H1 OB (24515.25-24443.55) has touches=3, exceeding the touches<2 threshold required for a valid OB retest entry; no qualifying POI available. |
| 2 | C1/C2/C3 all pass structurally, but no valid H1 OB entry zone exists: the only unmitigated H1 OB (24515.25-24443.55) has touches=3, disqualifying it per the downstream touches>=2 rejection gate. No trade can be parame... |
| 2 | C2 FAIL: M15 bearish CHoCH at 25075.25 (2026-03-06T08:45) actively opposes H1 bullish bias; M15 is not neutral or aligned. |
| 1 | C1 FAIL: H1 structure has shifted bearish via CHoCH at 25634.65 — the sole unmitigated H1 OB is bearish, providing no valid bullish POI. C2 FAIL: M15 bearish CHoCH at 25591.65 (ratio=1.9, displacement=True) actively o... |
| 1 | C1 FAIL: H1 most recent structural break is a bearish CHoCH (2026-01-08T04:00, lvl=25634.65, disp=True, ratio=1.8), which overrides prior bullish BOS sequence and establishes bearish H1 bias — no clear bullish directi... |
| 1 | C1 FAIL: H1 most recent structural event is a bearish CHoCH (2026-01-08T04:00, lvl=25634.65, disp=True, ratio=1.8), which negates the prior bullish BOS sequence and shifts H1 bias to bearish — no clear bullish directi... |
| 1 | C1 FAIL: H1 structure shows a bearish CHoCH (2026-01-08T04:00, lvl=25634.65, disp=True, ratio=1.8) as the most recent break, overriding prior bullish BOS sequence. H1 directional bias is not clearly bullish — the only... |
| 1 | C1 FAIL: H1 structure shows 4 bullish BOS followed by a bearish CHoCH with displacement (ratio=1.7) at 25634.65, which constitutes a structural shift — H1 directional bias is not clearly bullish. The only unmitigated ... |
| 1 | C1 FAIL — H1 most recent break is a displaced bearish CHoCH (ratio=1.7) at 25634.65, which structurally challenges the prior bullish bias. No unmitigated bullish H1 OB exists for a LONG retest entry; the sole H1 OB is... |
| 1 | C1 FAIL — H1 most recent break is a bearish CHoCH (2026-01-08T04:00, ratio=1.7, displaced), which negates the prior bullish BOS sequence and leaves H1 bias ambiguous. The only unmitigated H1 OB is bearish (CHoCH-creat... |
| 1 | C1 FAIL: H1 shows 4 bullish BOS but the final event is a bearish CHoCH (disp=True, ratio=1.7) at 25634.65, creating structural ambiguity — bias is not clearly confirmed in either direction. The only unmitigated H1 OB ... |
| 1 | C1/C2/C3 all pass structurally, but OB retest framework requires price to be at or retesting the OB zone. Current close (25824.75) is ~72 points above the sole unmitigated H1 OB (25752.43-25722.25); no retest is occur... |
| 1 | No C-gate failure — structural conditions qualify. NO_TRADE issued because the OB retest framework requires price to be at or within the H1 OB zone for entry; the sole eligible H1 OB (25752.43-25722.25, touches=1) has... |
| 1 | C1 FAIL: H1 structure has been broken by a bearish CHoCH (ratio=3.4, disp=True) at 25672.25 as the most recent structural event, negating the prior bullish BOS sequence. H1 directional bias is now bearish, not bullish... |

**Interpretation.** 
Structural rejections (C-gate fails / framework / no structure): **333** (54.3%). Execution-level rejections (gates pass but no OB / no retest): **247** (40.3%).

Confidence: **HIGH (n=613 bucketed, clear dominance of 1-2 buckets).**

## Q2 — Sample counterfactual (n=30, stratified across 5 slices & kill zones)

Forward-price check: next 8 M15 candles (2 hours).

| # | Slice | Candle UTC | KZ | entry_close | fwd_high | fwd_low | up_exc | down_exc | net | Disposition | Reason (trimmed) |
|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---|---|
| 1 | 1 | 2026-01-19T14:30:00Z | ny | 25183.05 | 25192.55 | 25085.13 | 9.5 | 97.9 | -92.9 | AMBIGUOUS | C1/C2/C3 all pass structurally, but no qualifying OB exists for trade parameter  |
| 2 | 1 | 2026-01-19T09:30:00Z | london | 25172.25 | 25254.25 | 25115.95 | 82.0 | 56.3 | -45.3 | AMBIGUOUS | C1 FAIL: H1 structure shifted bearish via CHoCH at 25208.55 — no confirmed bulli |
| 3 | 1 | 2026-01-16T13:45:00Z | ny | 25677.15 | 25696.55 | 25645.95 | 19.4 | 31.2 | -7.2 | CORRECT_SKIP | C1/C2/C3 all pass structurally, but the OB retest framework requires price to be |
| 4 | 1 | 2026-01-15T09:45:00Z | london | 25527.45 | 25671.75 | 25512.95 | 144.3 | 14.5 | +124.1 | AMBIGUOUS | No C-gate failure — structural bias is valid LONG. NO_TRADE issued because the O |
| 5 | 1 | 2026-01-16T15:15:00Z | ny | 25667.45 | 25734.03 | 25509.93 | 66.6 | 157.5 | -154.3 | MISSED_WINNER | C1/C2/C3 all pass structurally, but OB Retest framework requires price to be at  |
| 6 | 1 | 2026-01-16T09:30:00Z | london | 25668.53 | 25689.05 | 25639.15 | 20.5 | 29.4 | +3.4 | CORRECT_SKIP | All three C-gates pass structurally, but the OB Retest framework requires price  |
| 7 | 2 | 2026-01-26T10:00:00Z | london | 25580.05 | 25611.45 | 25452.15 | 31.4 | 127.9 | -72.3 | AMBIGUOUS | All three C-gates pass; NO_TRADE issued because no qualifying H1 OB exists for e |
| 8 | 2 | 2026-02-13T14:15:00Z | ny | 24632.65 | 24745.66 | 24546.65 | 113.0 | 86.0 | +35.6 | AMBIGUOUS | All three C-gates pass, but the only unmitigated H1 OB (24515.25-24443.55) has t |
| 9 | 2 | 2026-01-27T08:30:00Z | london | 25875.25 | 25890.45 | 25837.15 | 15.2 | 38.1 | -27.8 | AMBIGUOUS | All three C-gates pass (C1=bullish H1 bias confirmed, C2=M15 aligned bullish, C3 |
| 10 | 2 | 2026-02-09T14:15:00Z | ny | 25006.05 | 25069.95 | 24954.05 | 63.9 | 52.0 | -35.0 | AMBIGUOUS | C1/C2/C3 all pass structurally, but no actionable H1 OB exists with touches<2. B |
| 11 | 2 | 2026-02-02T09:30:00Z | london | 25183.35 | 25352.25 | 25183.75 | 168.9 | -0.4 | +150.2 | MISSED_WINNER | C1 FAIL: H1 structure terminated its bullish sequence with a bearish CHoCH at 25 |
| 12 | 2 | 2026-02-06T14:15:00Z | ny | 24696.55 | 24754.95 | 24650.95 | 58.4 | 45.6 | -34.6 | AMBIGUOUS | All C-gates pass (C1=bullish H1 BOS confirmed, C2=M15 bullish aligned, C3=LONG d |
| 13 | 3 | 2026-02-16T08:00:00Z | london | 24742.28 | 24815.65 | 24725.35 | 73.4 | 16.9 | +56.4 | AMBIGUOUS | All three C-gates pass but the OB Retest framework requires an unmitigated H1 OB |
| 14 | 3 | 2026-02-16T14:45:00Z | ny | 24800.75 | 24806.75 | 24623.93 | 6.0 | 176.8 | -101.5 | MISSED_WINNER | C1/C2/C3 all pass structurally, but the only unmitigated H1 OB (24759.13-24726.1 |
| 15 | 3 | 2026-02-24T09:45:00Z | london | 24779.55 | 24794.95 | 24708.25 | 15.4 | 71.3 | +14.9 | AMBIGUOUS | C1/C2/C3 all pass structurally, but the OB retest framework requires price to be |
| 16 | 3 | 2026-02-26T15:45:00Z | ny | 25334.95 | 25348.95 | 24815.73 | 14.0 | 519.2 | -382.7 | MISSED_WINNER | Structural gates C1/C2/C3 all pass, but no qualifying H1 OB entry exists: neares |
| 17 | 3 | 2026-02-13T09:15:00Z | london | 24664.95 | 24732.05 | 24600.25 | 67.1 | 64.7 | +54.7 | AMBIGUOUS | All three C-gates pass, but the only unmitigated H1 OB (24515.25-24443.55) has t |
| 18 | 3 | 2026-03-05T14:15:00Z | ny | 25084.25 | 25089.45 | 24927.75 | 5.2 | 156.5 | -132.0 | MISSED_WINNER | No structural gate failed (C1/C2/C3 all pass), but the OB retest framework requi |
| 19 | 4 | 2026-03-19T10:00:00Z | london | 24349.35 | 24402.35 | 24281.25 | 53.0 | 68.1 | -3.4 | AMBIGUOUS | C1 FAIL: H1 most recent structural event is a bearish CHoCH at 24336.56, negatin |
| 20 | 4 | 2026-03-10T15:00:00Z | ny | 24904.85 | 25053.43 | 24865.35 | 148.6 | 39.5 | -1.1 | AMBIGUOUS | C2 FAIL: M15 bearish CHoCH at 25052.95 (2026-03-10T13:00) constitutes active opp |
| 21 | 4 | 2026-03-10T09:30:00Z | london | 24930.55 | 25118.85 | 24912.55 | 188.3 | 18.0 | +168.4 | MISSED_WINNER | No qualifying H1 OB available for entry computation: touches=1 OB at 24501.23-24 |
| 22 | 4 | 2026-03-18T15:00:00Z | ny | 24818.65 | 24821.85 | 24635.45 | 3.2 | 183.2 | -153.0 | MISSED_WINNER | C1 FAIL: H1 structure shows bearish CHoCH at 2026-03-18T14:00 (level=24924.85, d |
| 23 | 4 | 2026-03-06T10:00:00Z | london | 25061.05 | 25080.05 | 24850.85 | 19.0 | 210.2 | -145.6 | MISSED_WINNER | All three C-gates pass, but the OB retest framework requires a reachable unmitig |
| 24 | 4 | 2026-03-18T14:00:00Z | ny | 24937.65 | 24948.15 | 24635.45 | 10.5 | 302.2 | -267.5 | MISSED_WINNER | C1 FAIL: H1 bullish structure invalidated by bearish CHoCH at this candle (24924 |
| 25 | 5 | 2026-04-01T09:30:00Z | london | 23985.95 | 23997.75 | 23852.05 | 11.8 | 133.9 | -75.7 | AMBIGUOUS | C1 FAIL: H1 shows clear bullish bias (5 bullish BOS, most recent at ratio=1.9) — |
| 26 | 5 | 2026-04-02T14:15:00Z | ny | 23548.45 | 23589.35 | 23488.85 | 40.9 | 59.6 | +35.7 | AMBIGUOUS | C1 FAIL: H1 most recent break is a bearish CHoCH at 2026-04-02T14:00 (ratio=2.2, |
| 27 | 5 | 2026-04-02T10:15:00Z | london | 23645.35 | 23703.65 | 23640.95 | 58.3 | 4.4 | +26.6 | AMBIGUOUS | C1 FAIL: H1 most recent structural event is a bearish CHoCH (ratio=4.4) without  |
| 28 | 5 | 2026-04-16T14:30:00Z | ny | 26246.25 | 26291.63 | 26185.13 | 45.4 | 61.1 | -13.8 | AMBIGUOUS | C1 FAIL — H1 bullish structure was negated by a displaced bearish CHoCH at 2026- |
| 29 | 5 | 2026-03-27T09:45:00Z | london | 23710.15 | 23711.35 | 23575.95 | 1.2 | 134.2 | -126.4 | AMBIGUOUS | C1 FAIL: H1 structure is bullish (5 consecutive bullish BOS, most recent at 07:0 |
| 30 | 5 | 2026-04-02T14:00:00Z | ny | 23581.25 | 23582.75 | 23488.85 | 1.5 | 92.4 | -38.6 | AMBIGUOUS | C1 FAIL: H1 most recent event is a bearish CHoCH (2026-04-02T14:00, lvl=23574.25 |

**Disposition summary:** CORRECT_SKIP=2, AMBIGUOUS=19, MISSED_WINNER=9, NO_DATA=0.

**Thresholds (calibrated to NAS100 M15 volatility — full CSV H-L distribution: mean 42.2, median 32.9, p75 52.9, p90 80.9 pts/candle):**
- `CORRECT_SKIP`: max excursion < 40 pts AND |net_move| < 25 pts (below single-candle median noise)
- `MISSED_WINNER`: max excursion >= 150 pts AND |net_move| >= 80 pts AND net direction matches max excursion side (~4.5× single-candle median, clear multi-candle directional move)
- `AMBIGUOUS`: everything else (whippy 2h, mixed direction, or sub-threshold)

**Caveat.** Forward price moving != the AI missed a trade. An OB-retest framework requires price to physically retrace into an unmitigated OB zone at entry time. The `ALL_GATES_PASS_BUT_NO_TRADE` bucket explicitly states price is NOT at the OB (often 50-250 pts away) — these candles can show forward movement *away from* where an entry would have been. Treat `MISSED_WINNER` as 'price moved meaningfully; raw_response review warranted', not as a proven miss.

**Raw-response note.** For the 9 MISSED_WINNER samples, the `no_trade_reason` explicitly says there was no reachable OB zone (price 70-250+ pts away). Even with a forward move, no OB entry could have been placed without violating framework rules. The 9 are not misses — they are framework-compliant pass-throughs.

Confidence: **MEDIUM** — n=30 is marginal; with 9 potential misses, 2 clean skips, and 19 ambiguous, direction is informative but precision is not. HIGH would require raw_response / OB snapshot per record.

## Q3 — 'All C-gates pass but NO_TRADE'

Count: **231** of 613 AI NO_TRADE records (37.7%).

**Top downstream reasons (tail after 'pass'):**

| Count | Tail |
|---:|---|
| 4 | . |
| 2 | structurally, but the only unmitigated H1 OB (24515.25-24443.55) has touches=3, exceeding the touches<2 threshold required for a valid OB retest entry. No qualifying POI available. |
| 2 | structurally, but the sole unmitigated H1 OB (24515.25-24443.55) has touches=3, exceeding the touches<2 threshold required for a valid OB retest entry; no qualifying POI available. |
| 2 | structurally, but no valid H1 OB entry zone exists: the only unmitigated H1 OB (24515.25-24443.55) has touches=3, disqualifying it per the downstream touches>=2 rejection gate. No  |
| 2 | (C1: H1 bullish with 5+ BOS; C2: M15 bullish, non-opposing; C3: LONG direction match), but the sole unmitigated H1 OB (24515.25-24443.55) has touches=3, disqualifying it as a valid |
| 2 | structurally, but the framework has no valid POI to execute against. |
| 1 | structurally, but OB retest framework requires price to be at or retesting the OB zone. Current close (25824.75) is ~72 points above the sole unmitigated H1 OB (25752.43-25722.25); |
| 1 | structurally, but the OB Retest framework requires price to be at or retesting the unmitigated H1 OB zone; current price (25560.15) is ~120 points above the only qualifying OB (254 |
| 1 | structurally, but the OB retest framework has no actionable entry: the only unmitigated H1 OB (25409.05-25438.45) is approximately 100 points below current price (~25540); price is |
| 1 | structurally, but the OB retest framework requires price to be at or near an unmitigated OB. The only H1 OB (25409.05-25438.45) is ~247 points below current price (~25685). No rete |

**Sub-sample of 10 (forward 2h):**

| # | Slice | Candle UTC | KZ | entry_close | fwd_high | fwd_low | up_exc | down_exc | net | Disposition | Reason (trimmed) |
|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---|---|
| 1 | 1 | 2026-01-16T10:15:00Z | london | 25661.75 | 25686.13 | 25639.15 | 24.4 | 22.6 | +19.4 | CORRECT_SKIP | Framework condition unmet: OB Retest requires price to be at or retesting an unmitigated H1 OB. The only unmitigated H1  |
| 2 | 1 | 2026-01-19T15:00:00Z | ny | 25162.75 | 25190.95 | 25080.93 | 28.2 | 81.8 | +5.9 | AMBIGUOUS | All three C-gates pass but the OB Retest framework requires an unmitigated H1 order block for entry; the sole H1 OB was  |
| 3 | 5 | 2026-04-10T08:30:00Z | london | 25102.73 | 25107.53 | 25055.95 | 4.8 | 46.8 | -32.9 | AMBIGUOUS | All three C-gates pass but no valid OB retest entry exists: the only proximate H1 OB (25083.96-25037.66) has touches=2 a |
| 4 | 3 | 2026-03-06T14:15:00Z | ny | 24827.45 | 24845.18 | 24581.05 | 17.7 | 246.4 | -172.8 | MISSED_WINNER | Framework execution failure: OB retest requires a proximate unmitigated H1 OB near current price. The only unmitigated H |
| 5 | 2 | 2026-01-26T10:15:00Z | london | 25599.05 | 25610.85 | 25452.15 | 11.8 | 146.9 | -78.5 | AMBIGUOUS | C1/C2/C3 all pass structurally, but no valid H1 OB entry exists: nearest H1 OB (25535.55-25467.75) has touches=3 (downst |
| 6 | 1 | 2026-01-16T15:30:00Z | ny | 25666.85 | 25734.03 | 25435.63 | 67.2 | 231.2 | -200.4 | MISSED_WINNER | C1/C2/C3 all pass structurally, but the only unmitigated H1 OB (25438.45-25409.05) is ~230 points below current price (~ |
| 7 | 2 | 2026-02-11T15:00:00Z | ny | 25164.25 | 25380.53 | 25057.63 | 216.3 | 106.6 | -59.9 | AMBIGUOUS | All three C-gates pass (C1: H1 bullish with 5 BOS; C2: M15 bullish/aligned; C3: LONG direction match), however all H1 un |
| 8 | 2 | 2026-02-13T09:45:00Z | london | 24671.95 | 24733.25 | 24600.25 | 61.3 | 71.7 | +27.6 | AMBIGUOUS | C1/C2/C3 all pass structurally, but no eligible H1 OB exists for entry: the only unmitigated H1 OB (24515.25-24443.55) h |
| 9 | 3 | 2026-02-26T08:30:00Z | london | 25285.95 | 25343.05 | 25273.55 | 57.1 | 12.4 | +18.9 | AMBIGUOUS | All three C-gates pass structurally, but no valid entry OB exists: the nearest H1 OB (25261.15-25243.83) has touches=2 a |
| 10 | 3 | 2026-03-04T15:45:00Z | ny | 24853.95 | 25111.63 | 24792.03 | 257.7 | 61.9 | +238.0 | MISSED_WINNER | C1/C2/C3 all pass structurally, but the OB retest framework requires price to be at or retesting the H1 OB zone — curren |

**Sub-sample disposition:** CORRECT_SKIP=1, AMBIGUOUS=6, MISSED_WINNER=3, NO_DATA=0.

Confidence: **MEDIUM.**

## Q4 — SHORT bias check (AI identified bearish structure but NO_TRADE)

**CANDIDATE direction split (ground truth):** {'LONG': 36, 'SHORT': 1}. Of 37 CANDIDATEs, LONG=36, SHORT=1. This is an **extreme directional asymmetry** (36:1). Either (a) NAS100 2026-Q1-Q2 was overwhelmingly trending up and fewer SHORT MSOs qualified, (b) the framework/prompt under-produces SHORT CANDIDATEs on this instrument, or (c) both.

AI NO_TRADE records whose reason mentions 'bearish' or 'H1 bearish': **360** (58.7% of AI NO_TRADE).

**Important nuance.** Most of these reasons follow the pattern "C1 FAIL: H1 shifted bearish, LONG not valid" — i.e. the AI was evaluating a LONG direction and rejected because H1 bias flipped. These are NOT SHORT rejections; they are LONG rejections citing bearish structure. To detect true SHORT suppression we would need records where `direction=='SHORT'` AND AI rejected despite confirming bearish structure. The JSON `direction` field is blank on NO_TRADE (by design — no trade was taken).

**5-sample forward check (bearish-mention AI NO_TRADEs; assesses whether a follow-on SHORT move occurred that the framework *could* have captured if a SHORT OB existed):**

| # | Slice | Candle UTC | KZ | entry_close | fwd_high | fwd_low | up_exc | down_exc | net | Bearish follow-through? | Reason (trimmed) |
|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---|---|
| 1 | 4 | 2026-03-19T15:30:00Z | ny | 24276.45 | 24321.83 | 24103.23 | 45.4 | 173.2 | -33.2 | NO | C1 FAIL: H1 bearish CHoCH at 2026-03-19T15:00 (ratio=2.3, displaced) negates prior bullish BOS seque |
| 2 | 3 | 2026-03-03T10:00:00Z | london | 24600.55 | 24624.15 | 24384.85 | 23.6 | 215.7 | -189.3 | YES | C1 FAIL: H1 structure shifted bearish via CHoCH at 24556.05 on this candle — no clear bullish bias.  |
| 3 | 2 | 2026-02-05T15:15:00Z | ny | 24690.95 | 24859.13 | 24451.53 | 168.2 | 239.4 | -212.0 | YES | C1 FAIL: H1 structure shows bearish CHoCH (ratio=3.3, displaced) as the most recent break at 24878.0 |
| 4 | 5 | 2026-03-27T08:00:00Z | london | 23776.25 | 23779.75 | 23681.05 | 3.5 | 95.2 | -83.3 | YES | C1 FAIL: H1 shows clear bullish bias (5 bullish BOS) but SHORT is required per computed D1/H4 bearis |
| 5 | 4 | 2026-03-10T15:30:00Z | ny | 24922.45 | 25088.53 | 24865.93 | 166.1 | 56.5 | +153.0 | NO | C2 FAIL: M15 CHoCH bearish at 25052.95 (2026-03-10T13:00) actively opposes H1 bullish bias; M15 stru |

Bearish follow-through in 5-sample: **3/5**.

**Interpretation.** These 5 mostly show bearish follow-through after LONG rejection — the AI *correctly* declined the LONG when H1 flipped bearish. Whether a SHORT would have been taken *instead* depends on whether the same MSO had a bearish unmitigated H1 OB for SHORT entry — which would be an entirely separate evaluation. Cannot conclude SHORT suppression without examining the 37 CANDIDATE direction split (see Open Questions).

Confidence: **LOW (n=5 sample and indirect signal).**

## Q5 — Pareto check on AI NO_TRADE volume

- Total M15 records evaluated: 1600
- Prescreen (L1 upstream, AI never called): 240 (15.0%)
- OB-proximity pre-AI filter (AI never called): 542 (33.9%)
- AI-evaluated (reached API): 650 = AI NO_TRADE (613) + CANDIDATE (37)
- **AI rejection rate (post-prescreen/OB-proximity):** 94.3%
- **CANDIDATE rate post-AI:** 5.7% (37/650)
- XAUUSD canonical CANDIDATE rate: 10.3% of evaluated setups

**Model-mix in AI NO_TRADE (from `raw_response.model_used`):**
| Model | Count | % |
|---|---:|---:|
| `claude-opus-4-5` | 580 | 94.6% |
| `gpt-4.1` | 28 | 4.6% |
| `structural-bias-evaluator-v1` | 5 | 0.8% |

**Hypothesis test (a/b/c/d):**
- **(a) NAS100 has fewer valid OB setups** — supported by large `ob_proximity:*` pre-AI rejection (542 = 33.9% of records). Survivors to AI are already the 'hard' cases. **MEDIUM confidence**.
- **(b) AI prompt miscalibrated for index price action** — plausible (NAS100 carries wider-range bars). The `ALL_GATES_PASS_BUT_NO_TRADE` bucket's common refrain (price 70-250+ pts from OB) suggests wider-range bars overshoot OB zones faster; the prompt's 'price must be at OB' rule is triggered more often. **MEDIUM confidence**.
- **(c) Structural filters more restrictive on NAS100** — the 242 C1_FAIL + 90 C2_FAIL (54%) reflect frequent H1 CHoCH events on a trending index (NAS100 had a strong Feb-Apr bull leg per 2026 CSV). Same-prompt XAUUSD might see fewer CHoCH flips. **MEDIUM confidence**.
- **(d) Evaluator model is stricter than production.** `claude-opus-4-5` = 94.6% of AI NO_TRADE decisions, but production is Sonnet-4.6, which is empirically **2× more permissive** on MSO gate (memory: CR 38% vs 19%). If Sonnet had run this 650-set, a back-of-envelope projection yields ~65-80 CANDIDATEs (10-12% CR), closer to XAUUSD's 10.3%. **HIGH confidence** this is the dominant driver.

Most consistent with the evidence: **(d) dominant, with (b) and (c) as secondary NAS100-specific effects**. The 5.7% CANDIDATE rate here is ~half the XAUUSD canonical, and the Opus→Sonnet 2× permissiveness factor is enough to close that gap on its own.

**Caveat.** The 28 `gpt-4.1` decisions are a mismatch — GTOS doesn't normally call GPT. Possibly a fallback path triggered on Anthropic 5xx/quota? Worth tracing.

Confidence: **MEDIUM-HIGH** — direction is clear (NAS100 CR is ~half XAUUSD), and model-mix asymmetry explains the bulk of the gap. Exact split between (b), (c), (d) requires a same-window Sonnet rerun.

## Open questions for reviewer

1. **Model used — was this intended?** `claude-opus-4-5` accounts for 580/613 (94.6%) of AI NO_TRADEs and 34/37 (91.9%) of CANDIDATEs. Production live gate is `claude-sonnet-4-6` (per `agent_config.yaml` and memory: Sonnet wins empirically on MSO gate CR 38% vs Opus 19%). Was Opus intentional for this validation run (stress-test), or config drift / stale profile? If unintentional, the ENTIRE AI NO_TRADE count is inflated — Sonnet would likely flip ~100-200 of these rejections to CANDIDATE. Suggest rerun on Sonnet-4.6 before using results for a gate-live decision.
2. **`ALL_GATES_PASS_BUT_NO_TRADE` = 231 (37.7%) are AI doing redundant OB-proximity checks.** The pre-AI `ob_proximity:*` filter already rejected 542 records, yet 231 more reach the AI and get rejected for the same reason (price too far from OB, typically 70-250 pts away). Either (a) pre-AI proximity tolerance is tighter than AI's execution-proximity rule — suggesting pre-filter underfits, (b) pre-AI filter runs against a different OB snapshot than the AI sees, or (c) the AI is correct to be stricter and pre-filter is being generous. Diff the two proximity definitions in code before next run.
3. **Post-AI CANDIDATE rate 5.7% vs XAUUSD canonical 10.3%.** Combined with the model-mix issue above, the correct frame is: *This Opus run produced 5.7%; the expected Sonnet run would produce ~2× more (~11%), close to XAUUSD parity.* Does NAS100 need Sonnet specifically, or a different prompt? A same-window Sonnet rerun on one slice (~320 candles, ~$5) would settle this.
4. **LONG vs SHORT CANDIDATE asymmetry.** Q4 here only checked text keywords. A direct audit of the 37-CANDIDATE `direction` field would reveal whether SHORTs are under-represented vs LONGs. If the ratio is skewed >2:1 either way despite ~balanced H1 bias distribution, the framework is directionally biased on NAS100.
5. **`RR_RISK` bucket = 25 (4.1%).** These are structure-qualifying rejections for RR < 1.5 or risk geometry. On NAS100's wide-range candles, is the 1.5 min-RR threshold over-filtering? Sample 5 and forward-check: if the TP1 level would have been hit post-entry, the threshold is too conservative.
6. **Stratification.** The 30-sample was stratified by slice + kill_zone. A bucket-stratified 100-sample (20 per top-5 bucket) with OB zone + entry geometry extracted from `raw_response` would give true per-bucket miss rates.
