# Entry Scenario Analysis — XAUUSD Jan 2 – Apr 10, 2026

**Analysis date:** 2026-04-13  
**Source:** `research/t7_live_simulation/all_results_jan_apr10.json`  
**Price data:** `data/historical_2026/XAUUSD_M15.csv`  
**Total entry_in_ob rejections analyzed:** 557  
**Directions:** All LONG (0 SHORT in dataset)  

---

## Validation Checks

1. **Count check:** 557 records extracted (expected 557) — PASS
2. **M15 date range:** 2026-01-02 01:00:00 → 2026-04-10 23:45:00 — PASS
3. **First rejection timestamp:** 2026-01-07 09:45:00 (Jan 7, 2026) — PASS
4. **Scenario A/C fill consistency:** A=59.6%, C=59.6% → C ≤ A — PASS
5. **Scenario D micro-risk vs A zone-risk:** D avg=61.52pts vs A avg=25.24pts → ANOMALY: D >= A (see explanation in Section 3)

### Spot-check (records at indices 0, 278, 556 of 557-record list)

**[index=0]** candle_time=2026-01-07T09:45:00Z, direction=LONG, entry_price=4460.26, ob_low=4405.55, ob_high=4421.39, zone_entry=4421.39, M15_idx=311, fwd_candle=EXISTS  
**[index=278]** candle_time=2026-02-12T15:15:00Z, direction=LONG, entry_price=5061.03, ob_low=4936.53, ob_high=4958.88, zone_entry=4958.88, M15_idx=2715, fwd_candle=EXISTS  
**[index=556]** candle_time=2026-04-10T16:45:00Z, direction=LONG, entry_price=4774.95, ob_low=4730.36, ob_high=4753.09, zone_entry=4753.09, M15_idx=6391, fwd_candle=EXISTS  

---

## 1. Scenario Comparison Summary Table

```
SCENARIO COMPARISON — XAUUSD Jan 2 – Apr 10, 2026
Total entry_in_ob rejections analyzed: 557

Scenario                             | Fill/Execute     | WR (filled)  | Avg R   | Total R  | No-fill/Expire
------------------------------------------------------------------------------------------------------------
A: OB limit (proactive)              | 59.6% (332)      | 45.5% (148/325) | 0.138   | 45.00    | 40.4% (225)   
B: Market at C-gate                  | 100% (557)       | 40.4% (224/555) | 0.009   | 5.00     | 0% (always fills)
C: Zone touch entry                  | 59.6% (332)      | 45.5% (148/325) | 0.138   | 45.00    | 40.4% (225)   
D: M15 CHoCH at zone                 | 59.2% (330)      | 28.8% (74/257) | -0.280  | -72.00   | zone_touch=59.6%, no_choch=2
```

**OPEN trades note:** Records near Apr 10 may have <192 forward candles. Truncated windows: 44. OPEN trades excluded from WR calculation but included in fill rate counts.

---

## 2. Time-to-Fill Distribution (Scenarios A and C)

**Scenario A: OB Limit** (n=332, median=41 candles, avg=62.8 candles)

| Bucket | Count | % of fills |
|--------|-------|------------|
| <4 candles (< 1h) | 29 | 8.7% |
| 4–15 candles (1h–4h) | 58 | 17.5% |
| 16–47 candles (4h–12h) | 90 | 27.1% |
| 48–95 candles (12h–24h) | 48 | 14.5% |
| 96–191 candles (24h–48h) | 107 | 32.2% |

**Scenario C: Zone Touch Entry** (n=332, median=41 candles, avg=63.1 candles)

| Bucket | Count | % of fills |
|--------|-------|------------|
| <4 candles (< 1h) | 28 | 8.4% |
| 4–15 candles (1h–4h) | 58 | 17.5% |
| 16–47 candles (4h–12h) | 90 | 27.1% |
| 48–95 candles (12h–24h) | 48 | 14.5% |
| 96–191 candles (24h–48h) | 108 | 32.5% |

---

## 3. Risk Analysis

**Gap: current price to OB zone entry at C-gate fire time**
- Avg gap: 1.563% of current price
- Min gap: -1.558%
- Max gap: 6.550%

**Zone risk sizing**
- Scenario A avg zone_risk: 25.24 pts (OB high – OB low × 0.999)
- Scenario D avg micro_risk: 61.52 pts (micro-CHoCH candle close – swing low × 0.999)
- Scenario B avg SL distance: 0.515% of entry price (AI-quoted SL)

**Scenario D anomaly explanation (D avg micro-risk > A avg zone-risk)**
The Scenario D algorithm tracks `swing_low` across all candles from zone touch through the CHoCH window. When price touches the OB zone late (touch_idx >= 100 candles ≈ 25+ hours after C-gate fire), market structure has completely changed. In some cases price dips far below `ob_low` establishing a deep `swing_low`, then recovers and fires a CHoCH with `entry` well above `ob_high`. Example: ob_zone=5156–5179 (28pt zone), micro_risk=175pt (swing_low=5103, entry=5272). This is algorithmically correct per spec — the algorithm does not constrain `swing_low >= ob_low`. However it means Scenario D creates operationally wider risk than the OB zone itself in ~14% of cases (47/330 trades have micro_risk > 100pt). The negative total R for D (−72.00) is partly attributable to this oversized risk on losing trades.

**Scenario A: 3R potential**
- Trades that hit 3R target: 71/332 = 21.4%

---

## 4. Monthly Breakdown — Scenario A

| Month | Rejected (n) | Filled | Resolved | WR | Total R |
|-------|-------------|--------|----------|----|---------|
| 2026-01 | 173 | 73 | 73 | 49.3% | 17.00 |
| 2026-02 | 211 | 152 | 151 | 47.7% | 29.00 |
| 2026-03 | 98 | 87 | 87 | 33.3% | -14.50 |
| 2026-04 | 75 | 20 | 14 | 78.6% | 13.50 |

---

## 5. Key Findings

- **F1 — All 557 rejections are LONG.** Zero SHORT entries in the dataset for this period. This reflects the sustained bullish H1 bias across Jan–Apr 2026 XAUUSD.

- **F2 — Scenario A fill rate: 59.6%.** Of 557 trades where price was above the OB zone at C-gate fire, 332 eventually returned to the OB zone within 48 hours. 225 never did (expired).

- **F3 — Scenario A WR: 45.5% on 325 resolved trades.** Avg R = 0.138, Total R = 45.00. This is below the 50% breakeven threshold.

- **F4 — Scenario B (market order) produced 40.4% WR** on 555 resolved trades, Total R = 5.00. Entering at market price when price is already above the OB zone uses the AI's native SL/TP (avg SL distance 0.515%).

- **F5 — Scenarios A and C are effectively identical in this dataset.** Both produce fill rate 59.6% (332/557), WR 45.5%, Total R +45.00. The close-above-SL guard in Scenario C produced zero additional filtering across 557 records — in all 332 fills the fill candle closed above zone_sl. The one edge case (Feb 17 08:45) where the first touch candle closed below zone_sl had C find a valid fill 116 candles later with the same outcome (LOSS). This means the "wick blow-through" scenario (touching zone top then closing through the entire zone in one 15-min bar) did not occur in XAUUSD during this period — likely because the avg zone width (25 pts) is large relative to typical 15-min candle ranges.

- **F6 — Scenario D (micro-CHoCH) executed 330 trades (59.2%).** WR = 28.8% on 257 resolved, Total R = -72.00. Avg micro-risk = 61.52 pts vs zone risk 25.24 pts (wider entry). Zone touch rate = 59.6%, CHoCH found of touches = 99.4%.

- **F7 — Gap from current price to OB zone:** avg 1.563% (range -1.558%–6.550%). These are genuine OB misses — price is materially above the identified zone, not marginal overshoot.


---

*Generated by `research/academic_pipeline/scripts/entry_scenario_analysis.py`*
