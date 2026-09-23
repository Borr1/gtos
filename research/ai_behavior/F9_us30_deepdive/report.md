# F9 — US30_cash Hallucination Deep-Dive

Harness: F9=`F9-v1` consuming B7=`B7-v1` · tolerance_ticks: 5

US30_cash evaluations: 49 · classifications: 265 · hallucination%: 23.4%

Per B7 baseline: US30_cash 23.4% hallucination, 5x cleanest (USDJPY 4.3%). This document decomposes that rate.

## US30_cash hallucination decomposition

### Per-field (top 5 by hallucinated%)

| Field | n | hallucinated% | accurate% | misattributed% | contribution% |
|---|---:|---:|---:|---:|---:|
| breaker_high | 1 | 100.0% | 0.0% | 0.0% | 1.6% |
| breaker_low | 1 | 100.0% | 0.0% | 0.0% | 1.6% |
| take_profit | 26 | 96.2% | 3.8% | 0.0% | 40.3% |
| current_price | 9 | 44.4% | 55.6% | 0.0% | 6.5% |
| ob_mid | 26 | 38.5% | 57.7% | 3.8% | 16.1% |

### Per-month

| Month | n_evals | n_prices | hallucination rate |
|---|---:|---:|---:|
| 2026-04 | 49 | 265 | 23.4% |

### Per-session (kill zone)

| Session | n_evals | n_prices | hallucination rate |
|---|---:|---:|---:|
| london | 26 | 154 | 24.0% |
| ny | 23 | 111 | 22.5% |

### Per-CAND-type (final outcome)

| Final outcome | n_evals | n_prices | hallucination rate |
|---|---:|---:|---:|
| EXECUTION_FAILED | 1 | 8 | 25.0% |
| LIMIT_PLACED | 2 | 18 | 22.2% |
| REJECTED_L2 | 20 | 164 | 26.2% |
| REJECTED_L2_POST_M5 | 3 | 24 | 29.2% |
| live_eval_CANDIDATE | 4 | 8 | 0.0% |
| live_eval_NO_TRADE | 8 | 13 | 30.8% |
| unknown | 11 | 30 | 6.7% |

## Sampled top-hallucination CANDs (top 10)

### 1. 2026-04-13T08:30:53.887714+00:00 (london, REJECTED_L2)

Decision: CANDIDATE · framework: ob_retest · hallucinated: 4 · misattributed: 0 · score: 4.0

**AI-cited prices:**

| role | value | classification | matched_mso_field | matched_mso_value | delta_ticks |
|---|---:|---|---|---:|---:|
| entry_price | 47677.51 | hallucinated | `—` | — | — |
| stop_loss | 47515.51 | accurate | `timeframes.H1.swings[41].price(low)` | 47515.51 | 0.0 |
| take_profit | 47920.51 | hallucinated | `—` | — | — |
| ob_mid | 47539.56 | hallucinated | `—` | — | — |
| ob_high | 47555.51 | accurate | `timeframes.H1.order_blocks[6].high` | 47555.51 | 0.0 |
| ob_low | 47524.51 | accurate | `timeframes.H1.order_blocks[6].low` | 47524.51 | 0.0 |
| protected_swing | 47515.51 | accurate | `timeframes.H1.swings[41].price(low)` | 47515.51 | 0.0 |
| sweep_price | 47631.61 | hallucinated | `—` | — | — |

**MSO key levels (top 3 per block):**

- **D1** last close=None (O=None H=None L=None)
  - FVGs: 48093.91-48212.01 (bearish), 47275.18-47430.9 (bearish), 47122.2-47173.5 (bearish)
  - Swings: 44813.18 (low), 46843.11 (high), 48326.0 (high)
- **H1** last close=None (O=None H=None L=None)
  - OBs: 45887.71-46087.21 (bullish), 46360.31-46429.81 (bullish), 46449.6-46622.05 (bullish)
  - FVGs: 46242.11-46521.11 (bearish), 46055.71-46098.71 (bullish), 45974.71-46021.21 (bearish)
  - Breakers: 46360.31-46429.81 (None), 46449.6-46622.05 (None), 47429.41-47559.41 (None)
  - Swings: 47326.28 (low), 47564.91 (high), 47515.51 (low)
- **H4** last close=None (O=None H=None L=None)
  - OBs: 45061.55-45449.6 (bullish), 46388.41-46597.41 (bullish), 46197.7-46605.2 (bullish)
  - FVGs: 46219.31-46243.71 (bearish), 45987.81-46041.71 (bearish), 45776.81-45931.81 (bearish)
  - Breakers: 47703.31-47877.81 (None)
  - Swings: 48326.0 (high), 48285.8 (high), 47326.28 (low)
- **M15** last close=None (O=None H=None L=None)
  - OBs: 46526.61-46568.11 (bullish), 46005.71-46055.71 (bullish), 45879.4-46020.4 (bullish)
  - FVGs: 46687.25-46738.8 (bearish), 46649.8-46674.3 (bearish), 46602.28-46616.3 (bearish)
  - Breakers: 46526.61-46568.11 (None), 46005.71-46055.71 (None), 46430.6-46493.65 (None)
  - Swings: 47515.51 (low), 47678.01 (high), 47648.51 (low)

  - Session levels: asian_high=0.0, asian_low=0.0, pdh=48326.0, pdl=47694.5, session_high=47726.51, session_low=47326.28

### 2. 2026-04-13T08:15:54.549732+00:00 (london, REJECTED_L2)

Decision: CANDIDATE · framework: ob_retest · hallucinated: 3 · misattributed: 1 · score: 3.5

**AI-cited prices:**

| role | value | classification | matched_mso_field | matched_mso_value | delta_ticks |
|---|---:|---|---|---:|---:|
| entry_price | 47677.51 | hallucinated | `—` | — | — |
| stop_loss | 47515.51 | accurate | `timeframes.H1.swings[41].price(low)` | 47515.51 | 0.0 |
| take_profit | 47920.26 | hallucinated | `—` | — | — |
| ob_mid | 47539.56 | hallucinated | `—` | — | — |
| ob_high | 47555.51 | accurate | `timeframes.H1.order_blocks[6].high` | 47555.51 | 0.0 |
| ob_low | 47524.51 | accurate | `timeframes.H1.order_blocks[6].low` | 47524.51 | 0.0 |
| protected_swing | 47515.51 | accurate | `timeframes.H1.swings[41].price(low)` | 47515.51 | 0.0 |
| sweep_price | 47619.41 | misattributed | `timeframes.H1.fair_value_gaps[29].top` | 47619.41 | 0.0 |

**MSO key levels (top 3 per block):**

- **D1** last close=None (O=None H=None L=None)
  - FVGs: 48093.91-48212.01 (bearish), 47275.18-47430.9 (bearish), 47122.2-47173.5 (bearish)
  - Swings: 44813.18 (low), 46843.11 (high), 48326.0 (high)
- **H1** last close=None (O=None H=None L=None)
  - OBs: 45887.71-46087.21 (bullish), 46360.31-46429.81 (bullish), 46449.6-46622.05 (bullish)
  - FVGs: 46242.11-46521.11 (bearish), 46055.71-46098.71 (bullish), 45974.71-46021.21 (bearish)
  - Breakers: 46360.31-46429.81 (None), 46449.6-46622.05 (None), 47429.41-47559.41 (None)
  - Swings: 47326.28 (low), 47564.91 (high), 47515.51 (low)
- **H4** last close=None (O=None H=None L=None)
  - OBs: 45061.55-45449.6 (bullish), 46388.41-46597.41 (bullish), 46197.7-46605.2 (bullish)
  - FVGs: 46219.31-46243.71 (bearish), 45987.81-46041.71 (bearish), 45776.81-45931.81 (bearish)
  - Breakers: 47703.31-47877.81 (None)
  - Swings: 48326.0 (high), 48285.8 (high), 47326.28 (low)
- **M15** last close=None (O=None H=None L=None)
  - OBs: 46526.61-46568.11 (bullish), 46005.71-46055.71 (bullish), 45879.4-46020.4 (bullish)
  - FVGs: 46687.25-46738.8 (bearish), 46649.8-46674.3 (bearish), 46602.28-46616.3 (bearish)
  - Breakers: 46526.61-46568.11 (None), 46005.71-46055.71 (None), 46430.6-46493.65 (None)
  - Swings: 47515.51 (low), 47678.01 (high), 47648.51 (low)

  - Session levels: asian_high=0.0, asian_low=0.0, pdh=48326.0, pdl=47694.5, session_high=47706.51, session_low=47326.28

### 3. 2026-04-13T09:00:05.011541+00:00 (london, REJECTED_L2)

Decision: CANDIDATE · framework: ob_retest · hallucinated: 3 · misattributed: 1 · score: 3.5

**AI-cited prices:**

| role | value | classification | matched_mso_field | matched_mso_value | delta_ticks |
|---|---:|---|---|---:|---:|
| entry_price | 47687.01 | hallucinated | `—` | — | — |
| stop_loss | 47326.28 | accurate | `timeframes.H4.swings[23].price(low)` | 47326.28 | 0.0 |
| take_profit | 48228.13 | hallucinated | `—` | — | — |
| ob_mid | 47539.56 | hallucinated | `—` | — | — |
| ob_high | 47555.51 | accurate | `timeframes.H1.order_blocks[6].high` | 47555.51 | 0.0 |
| ob_low | 47524.51 | accurate | `timeframes.H1.order_blocks[6].low` | 47524.51 | 0.0 |
| protected_swing | 47515.51 | accurate | `timeframes.H1.swings[41].price(low)` | 47515.51 | 0.0 |
| sweep_price | 47636.01 | misattributed | `timeframes.M15.fair_value_gaps[68].top` | 47636.01 | 0.0 |

**MSO key levels (top 3 per block):**

- **D1** last close=None (O=None H=None L=None)
  - FVGs: 48093.91-48212.01 (bearish), 47275.18-47430.9 (bearish), 47122.2-47173.5 (bearish)
  - Swings: 44813.18 (low), 46843.11 (high), 48326.0 (high)
- **H1** last close=None (O=None H=None L=None)
  - OBs: 45887.71-46087.21 (bullish), 46360.31-46429.81 (bullish), 46449.6-46622.05 (bullish)
  - FVGs: 46242.11-46521.11 (bearish), 46055.71-46098.71 (bullish), 45974.71-46021.21 (bearish)
  - Breakers: 46360.31-46429.81 (None), 46449.6-46622.05 (None), 47429.41-47559.41 (None)
  - Swings: 47326.28 (low), 47564.91 (high), 47515.51 (low)
- **H4** last close=None (O=None H=None L=None)
  - OBs: 45061.55-45449.6 (bullish), 46388.41-46597.41 (bullish), 46197.7-46605.2 (bullish)
  - FVGs: 46219.31-46243.71 (bearish), 45987.81-46041.71 (bearish), 45776.81-45931.81 (bearish)
  - Breakers: 47703.31-47877.81 (None)
  - Swings: 48326.0 (high), 48285.8 (high), 47326.28 (low)
- **M15** last close=None (O=None H=None L=None)
  - OBs: 46526.61-46568.11 (bullish), 46005.71-46055.71 (bullish), 45879.4-46020.4 (bullish)
  - FVGs: 46687.25-46738.8 (bearish), 46649.8-46674.3 (bearish), 46602.28-46616.3 (bearish)
  - Breakers: 46526.61-46568.11 (None), 46005.71-46055.71 (None), 46430.6-46493.65 (None)
  - Swings: 47648.51 (low), 47726.51 (high), 47646.01 (low)

  - Session levels: asian_high=0.0, asian_low=0.0, london_high=47461.78, london_low=47414.78, pdh=48326.0, pdl=47694.5, session_high=47726.51, session_low=47326.28

### 4. 2026-04-14T15:00:05.009432+00:00 (ny, REJECTED_L2_POST_M5)

Decision: CANDIDATE · framework: ob_retest · hallucinated: 3 · misattributed: 0 · score: 3.0

**AI-cited prices:**

| role | value | classification | matched_mso_field | matched_mso_value | delta_ticks |
|---|---:|---|---|---:|---:|
| entry_price | 48280.71 | accurate | `timeframes.M15.swings[174].price(high)` | 48280.71 | 0.0 |
| stop_loss | 48107.21 | hallucinated | `—` | — | — |
| take_profit | 48540.96 | hallucinated | `—` | — | — |
| ob_mid | 48207.46 | accurate | `timeframes.H1.order_blocks[8].midpoint` | 48207.46 | 0.0 |
| ob_high | 48280.71 | accurate | `timeframes.H1.order_blocks[8].high` | 48280.71 | 0.0 |
| ob_low | 48134.21 | accurate | `timeframes.H1.order_blocks[8].low` | 48134.21 | 0.0 |
| protected_swing | 48134.21 | accurate | `timeframes.H1.swings[43].price(low)` | 48134.21 | 0.0 |
| sweep_price | 48261.81 | hallucinated | `—` | — | — |

**MSO key levels (top 3 per block):**

- **D1** last close=None (O=None H=None L=None)
  - FVGs: 48093.91-48212.01 (bearish), 47275.18-47430.9 (bearish), 47122.2-47173.5 (bearish)
  - Swings: 44813.18 (low), 46843.11 (high), 48326.0 (high)
- **H1** last close=None (O=None H=None L=None)
  - OBs: 46360.31-46429.81 (bullish), 46449.6-46622.05 (bullish), 46266.05-46521.1 (bullish)
  - FVGs: 46268.18-46357.41 (bearish), 46275.31-46363.91 (bearish), 46275.31-46340.81 (bullish)
  - Breakers: 46360.31-46429.81 (None), 46449.6-46622.05 (None), 47429.41-47559.41 (None)
  - Swings: 48181.9 (low), 48323.81 (high), 48134.21 (low)
- **H4** last close=None (O=None H=None L=None)
  - OBs: 45061.55-45449.6 (bullish), 46388.41-46597.41 (bullish), 46197.7-46605.2 (bullish)
  - FVGs: 45987.81-46041.71 (bearish), 45776.81-45931.81 (bearish), 45563.5-45729.31 (bearish)
  - Breakers: 47703.31-47877.81 (None)
  - Swings: 48285.8 (high), 47326.28 (low), 47407.01 (low)
- **M15** last close=None (O=None H=None L=None)
  - OBs: 46422.01-46446.01 (bullish), 46364.11-46406.1 (bullish), 46201.41-46227.81 (bullish)
  - FVGs: 46449.81-46477.01 (bearish), 46443.6-46449.91 (bearish), 46410.51-46427.1 (bearish)
  - Breakers: 46422.01-46446.01 (None), 46364.11-46406.1 (None), 46282.81-46340.81 (None)
  - Swings: 48291.5 (high), 48179.9 (low), 48495.85 (high)

  - Session levels: asian_high=48225.15, asian_low=47477.01, london_high=48247.31, london_low=48183.11, pdh=47777.51, pdl=47326.28, session_high=48323.81, session_low=48134.21

### 5. 2026-04-17T15:45:05.007059+00:00 (ny, REJECTED_L2)

Decision: CANDIDATE · framework: ob_retest · hallucinated: 3 · misattributed: 0 · score: 3.0

**AI-cited prices:**

| role | value | classification | matched_mso_field | matched_mso_value | delta_ticks |
|---|---:|---|---|---:|---:|
| entry_price | 47735.2 | accurate | `timeframes.H1.fair_value_gaps[13].bottom` | 47735.2 | 0.0 |
| stop_loss | 47593.2 | hallucinated | `—` | — | — |
| take_profit | 47948.2 | hallucinated | `—` | — | — |
| ob_mid | 48531.325 | accurate | `timeframes.H1.order_blocks[7].midpoint` | 48531.325 | 0.0 |
| protected_swing | 48629.71 | accurate | `timeframes.H1.swings[43].price(low)` | 48629.71 | 0.0 |
| sweep_price | 49314.8 | hallucinated | `—` | — | — |

**MSO key levels (top 3 per block):**

- **D1** last close=None (O=None H=None L=None)
  - FVGs: 47275.18-47430.9 (bearish), 47122.2-47173.5 (bearish), 46302.61-46678.31 (bearish)
  - Swings: 46843.11 (high), 48326.0 (high), 47326.28 (low)
- **H1** last close=None (O=None H=None L=None)
  - OBs: 47742.5-47872.5 (bullish), 47524.51-47555.51 (bullish), 47620.2-47735.2 (bullish)
  - FVGs: 47767.31-47794.31 (bearish), 47872.5-48068.5 (bullish), 48073.5-48225.0 (bullish)
  - Breakers: 47742.5-47872.5 (None), 47524.51-47555.51 (None), 48184.31-48208.81 (None)
  - Swings: 48590.3 (high), 48679.71 (high), 48629.71 (low)
- **H4** last close=None (O=None H=None L=None)
  - OBs: 46388.41-46597.41 (bullish), 46197.7-46605.2 (bullish), 47703.31-47877.81 (bullish)
  - FVGs: 45820.01-46054.2 (bullish), 46182.71-46521.11 (bearish), 46162.71-46305.95 (bullish)
  - Breakers: 47703.31-47877.81 (None)
  - Swings: 48701.5 (high), 48275.0 (low), 48331.05 (low)
- **M15** last close=None (O=None H=None L=None)
  - OBs: 47738.41-47783.41 (bullish), 47782.91-47850.41 (bullish), 47746.65-47827.65 (bullish)
  - FVGs: 47785.41-47798.41 (bullish), 47829.91-47860.41 (bullish), 47861.41-47874.6 (bullish)
  - Breakers: 47738.41-47783.41 (None), 47782.91-47850.41 (None), 47746.65-47827.65 (None)
  - Swings: 49058.3 (low), 49661.85 (high), 49514.85 (low)

  - Session levels: asian_high=48672.0, asian_low=48331.05, london_high=48679.71, london_low=48564.27, pdh=48701.5, pdl=48275.0, session_high=49147.61, session_low=48564.27

### 6. 2026-04-21T10:30:05.012140+00:00 (london, REJECTED_L2)

Decision: CANDIDATE · framework: ob_retest · hallucinated: 3 · misattributed: 0 · score: 3.0

**AI-cited prices:**

| role | value | classification | matched_mso_field | matched_mso_value | delta_ticks |
|---|---:|---|---|---:|---:|
| entry_price | 49551.81 | accurate | `timeframes.M15.swings[173].price(high)` | 49551.81 | 0.0 |
| stop_loss | 49449.43 | hallucinated | `—` | — | — |
| take_profit | 49705.58 | hallucinated | `—` | — | — |
| ob_mid | 49511.31 | accurate | `timeframes.H1.order_blocks[10].midpoint` | 49511.31 | 0.0 |
| ob_high | 49551.81 | accurate | `timeframes.H1.order_blocks[10].high` | 49551.81 | 0.0 |
| ob_low | 49470.81 | accurate | `timeframes.H1.order_blocks[10].low` | 49470.81 | 0.0 |
| protected_swing | 49470.81 | accurate | `timeframes.H1.swings[45].price(low)` | 49470.81 | 0.0 |
| sweep_price | 49556.41 | hallucinated | `—` | — | — |

**MSO key levels (top 3 per block):**

- **D1** last close=None (O=None H=None L=None)
  - FVGs: 47122.2-47173.5 (bearish), 46302.61-46678.31 (bearish), 45669.41-45896.98 (bearish)
  - Swings: 46843.11 (high), 48326.0 (high), 47326.28 (low)
- **H1** last close=None (O=None H=None L=None)
  - OBs: 47524.51-47555.51 (bullish), 47620.2-47735.2 (bullish), 48184.31-48208.81 (bullish)
  - FVGs: 48124.2-48158.61 (bearish), 47961.2-47981.7 (bearish), 47461.78-47860.9 (bearish)
  - Breakers: 47524.51-47555.51 (None), 48184.31-48208.81 (None), 48456.81-48545.41 (None)
  - Swings: 49479.21 (low), 49572.31 (high), 49470.81 (low)
- **H4** last close=None (O=None H=None L=None)
  - OBs: 46388.41-46597.41 (bullish), 46197.7-46605.2 (bullish), 47703.31-47877.81 (bullish)
  - FVGs: 46162.71-46305.95 (bullish), 46470.01-46485.28 (bearish), 46711.28-47492.41 (bullish)
  - Breakers: 47703.31-47877.81 (None)
  - Swings: 48331.05 (low), 49723.3 (high), 48939.61 (low)
- **M15** last close=None (O=None H=None L=None)
  - OBs: 48104.01-48127.71 (bullish), 47524.51-47539.61 (bullish), 47644.51-47668.7 (bullish)
  - FVGs: 48123.7-48132.61 (bearish), 48127.71-48139.61 (bullish), 48100.11-48122.7 (bearish)
  - Breakers: 48104.01-48127.71 (None), 47524.51-47539.61 (None), 47644.51-47668.7 (None)
  - Swings: 49559.81 (high), 49515.31 (low), 49736.81 (high)

  - Session levels: asian_high=49553.41, asian_low=49459.81, london_high=49572.31, london_low=49470.81, pdh=49529.78, pdl=48939.61, session_high=49736.81, session_low=49470.81

### 7. 2026-04-23T09:00:05.025706+00:00 (london, REJECTED_L2)

Decision: CANDIDATE · framework: ob_retest · hallucinated: 3 · misattributed: 0 · score: 3.0

**AI-cited prices:**

| role | value | classification | matched_mso_field | matched_mso_value | delta_ticks |
|---|---:|---|---|---:|---:|
| entry_price | 49175.21 | accurate | `timeframes.M15.fair_value_gaps[105].bottom` | 49175.21 | 0.0 |
| stop_loss | 49140.46 | hallucinated | `—` | — | — |
| take_profit | 49227.34 | hallucinated | `—` | — | — |
| ob_mid | 49531.305 | hallucinated | `—` | — | — |
| ob_high | 48645.71 | accurate | `timeframes.H1.order_blocks[4].high` | 48645.71 | 0.0 |
| ob_low | 48629.71 | accurate | `timeframes.H1.order_blocks[4].low` | 48629.71 | 0.0 |
| ob_high | 49175.21 | accurate | `timeframes.M15.order_blocks[34].high` | 49175.21 | 0.0 |
| ob_low | 49144.21 | accurate | `timeframes.M15.order_blocks[34].low` | 49144.21 | 0.0 |
| protected_swing | 49107.21 | accurate | `timeframes.H1.swings[44].price(low)` | 49107.21 | 0.0 |
| sweep_price | 49188.0 | accurate | `timeframes.M15.swings[183].price(low)` | 49188.0 | 0.0 |

**MSO key levels (top 3 per block):**

- **D1** last close=None (O=None H=None L=None)
  - FVGs: 46302.61-46678.31 (bearish), 45669.41-45896.98 (bearish), 45669.41-46274.38 (bullish)
  - Swings: 48326.0 (high), 47326.28 (low), 49847.0 (high)
- **H1** last close=None (O=None H=None L=None)
  - OBs: 48134.21-48280.71 (bullish), 48456.81-48545.41 (bullish), 48465.5-48495.05 (bullish)
  - FVGs: 48231.9-48253.21 (bullish), 48291.5-48368.85 (bullish), 48461.55-48514.31 (bearish)
  - Breakers: 48456.81-48545.41 (None), 48465.5-48495.05 (None), 49335.6-49427.1 (None)
  - Swings: 49237.38 (low), 48953.21 (low), 49107.21 (low)
- **H4** last close=None (O=None H=None L=None)
  - OBs: 46197.7-46605.2 (bullish), 47703.31-47877.81 (bullish), 48199.81-48244.31 (bullish)
  - FVGs: 46711.28-47492.41 (bullish), 47601.41-47618.41 (bullish), 47787.81-47816.81 (bearish)
  - Breakers: 47703.31-47877.81 (None)
  - Swings: 49039.3 (low), 49623.15 (high), 48953.21 (low)
- **M15** last close=None (O=None H=None L=None)
  - OBs: 48187.9-48199.9 (bullish), 48250.21-48282.21 (bullish), 48226.21-48301.71 (bullish)
  - FVGs: 48221.81-48230.81 (bearish), 48213.81-48218.81 (bearish), 48225.9-48250.21 (bullish)
  - Breakers: 48187.9-48199.9 (None), 48250.21-48282.21 (None), 48433.85-48506.4 (None)
  - Swings: 49228.41 (high), 49188.0 (low), 49278.31 (high)

  - Session levels: asian_high=49326.78, asian_low=48953.21, london_high=49214.81, london_low=49121.21, pdh=49623.15, pdl=49237.38, session_high=49278.31, session_low=49121.21

### 8. 2026-04-13T08:45:05.008213+00:00 (london, REJECTED_L2)

Decision: CANDIDATE · framework: ob_retest · hallucinated: 2 · misattributed: 1 · score: 2.5

**AI-cited prices:**

| role | value | classification | matched_mso_field | matched_mso_value | delta_ticks |
|---|---:|---|---|---:|---:|
| entry_price | 47726.51 | accurate | `timeframes.M15.swings[176].price(high)` | 47726.51 | 0.0 |
| stop_loss | 47515.51 | accurate | `timeframes.H1.swings[41].price(low)` | 47515.51 | 0.0 |
| take_profit | 48043.01 | hallucinated | `—` | — | — |
| ob_mid | 47539.51 | hallucinated | `—` | — | — |
| ob_high | 47555.51 | accurate | `timeframes.H1.order_blocks[6].high` | 47555.51 | 0.0 |
| ob_low | 47524.51 | accurate | `timeframes.H1.order_blocks[6].low` | 47524.51 | 0.0 |
| protected_swing | 47515.51 | accurate | `timeframes.H1.swings[41].price(low)` | 47515.51 | 0.0 |
| sweep_price | 47644.51 | misattributed | `timeframes.M15.order_blocks[32].low` | 47644.51 | 0.0 |

**MSO key levels (top 3 per block):**

- **D1** last close=None (O=None H=None L=None)
  - FVGs: 48093.91-48212.01 (bearish), 47275.18-47430.9 (bearish), 47122.2-47173.5 (bearish)
  - Swings: 44813.18 (low), 46843.11 (high), 48326.0 (high)
- **H1** last close=None (O=None H=None L=None)
  - OBs: 45887.71-46087.21 (bullish), 46360.31-46429.81 (bullish), 46449.6-46622.05 (bullish)
  - FVGs: 46242.11-46521.11 (bearish), 46055.71-46098.71 (bullish), 45974.71-46021.21 (bearish)
  - Breakers: 46360.31-46429.81 (None), 46449.6-46622.05 (None), 47429.41-47559.41 (None)
  - Swings: 47326.28 (low), 47564.91 (high), 47515.51 (low)
- **H4** last close=None (O=None H=None L=None)
  - OBs: 45061.55-45449.6 (bullish), 46388.41-46597.41 (bullish), 46197.7-46605.2 (bullish)
  - FVGs: 46219.31-46243.71 (bearish), 45987.81-46041.71 (bearish), 45776.81-45931.81 (bearish)
  - Breakers: 47703.31-47877.81 (None)
  - Swings: 48326.0 (high), 48285.8 (high), 47326.28 (low)
- **M15** last close=None (O=None H=None L=None)
  - OBs: 46526.61-46568.11 (bullish), 46005.71-46055.71 (bullish), 45879.4-46020.4 (bullish)
  - FVGs: 46687.25-46738.8 (bearish), 46649.8-46674.3 (bearish), 46602.28-46616.3 (bearish)
  - Breakers: 46526.61-46568.11 (None), 46005.71-46055.71 (None), 46430.6-46493.65 (None)
  - Swings: 47678.01 (high), 47648.51 (low), 47726.51 (high)

  - Session levels: asian_high=0.0, asian_low=0.0, pdh=48326.0, pdl=47694.5, session_high=47726.51, session_low=47326.28

### 9. 2026-04-23T08:16:11.665587+00:00 (london, REJECTED_L2)

Decision: CANDIDATE · framework: ob_retest · hallucinated: 2 · misattributed: 1 · score: 2.5

**AI-cited prices:**

| role | value | classification | matched_mso_field | matched_mso_value | delta_ticks |
|---|---:|---|---|---:|---:|
| entry_price | 49175.21 | accurate | `timeframes.M15.fair_value_gaps[105].bottom` | 49175.21 | 0.0 |
| stop_loss | 49118.71 | accurate | `equal_lows[45].price` | 49118.71 | 0.0 |
| take_profit | 49260.46 | hallucinated | `—` | — | — |
| ob_mid | 49531.305 | hallucinated | `—` | — | — |
| ob_high | 49175.21 | accurate | `timeframes.M15.order_blocks[34].high` | 49175.21 | 0.0 |
| ob_low | 49144.21 | accurate | `timeframes.M15.order_blocks[34].low` | 49144.21 | 0.0 |
| protected_swing | 49107.21 | accurate | `timeframes.H1.swings[44].price(low)` | 49107.21 | 0.0 |
| sweep_price | 49189.21 | misattributed | `timeframes.M15.fair_value_gaps[105].top` | 49189.21 | 0.0 |

**MSO key levels (top 3 per block):**

- **D1** last close=None (O=None H=None L=None)
  - FVGs: 46302.61-46678.31 (bearish), 45669.41-45896.98 (bearish), 45669.41-46274.38 (bullish)
  - Swings: 48326.0 (high), 47326.28 (low), 49847.0 (high)
- **H1** last close=None (O=None H=None L=None)
  - OBs: 48134.21-48280.71 (bullish), 48456.81-48545.41 (bullish), 48465.5-48495.05 (bullish)
  - FVGs: 48231.9-48253.21 (bullish), 48291.5-48368.85 (bullish), 48461.55-48514.31 (bearish)
  - Breakers: 48456.81-48545.41 (None), 48465.5-48495.05 (None), 49335.6-49427.1 (None)
  - Swings: 49237.38 (low), 48953.21 (low), 49107.21 (low)
- **H4** last close=None (O=None H=None L=None)
  - OBs: 46197.7-46605.2 (bullish), 47703.31-47877.81 (bullish), 48199.81-48244.31 (bullish)
  - FVGs: 46711.28-47492.41 (bullish), 47601.41-47618.41 (bullish), 47787.81-47816.81 (bearish)
  - Breakers: 47703.31-47877.81 (None)
  - Swings: 49039.3 (low), 49623.15 (high), 48953.21 (low)
- **M15** last close=None (O=None H=None L=None)
  - OBs: 48187.9-48199.9 (bullish), 48250.21-48282.21 (bullish), 48226.21-48301.71 (bullish)
  - FVGs: 48221.81-48230.81 (bearish), 48213.81-48218.81 (bearish), 48225.9-48250.21 (bullish)
  - Breakers: 48187.9-48199.9 (None), 48250.21-48282.21 (None), 48433.85-48506.4 (None)
  - Swings: 49228.41 (high), 49188.0 (low), 49269.31 (high)

  - Session levels: asian_high=49326.78, asian_low=48953.21, london_high=49186.21, london_low=49121.21, pdh=49623.15, pdl=49237.38, session_high=49269.31, session_low=49121.21

### 10. 2026-04-23T08:45:05.012106+00:00 (london, REJECTED_L2)

Decision: CANDIDATE · framework: ob_retest · hallucinated: 2 · misattributed: 1 · score: 2.5

**AI-cited prices:**

| role | value | classification | matched_mso_field | matched_mso_value | delta_ticks |
|---|---:|---|---|---:|---:|
| entry_price | 49175.21 | accurate | `timeframes.M15.fair_value_gaps[105].bottom` | 49175.21 | 0.0 |
| stop_loss | 49118.46 | hallucinated | `—` | — | — |
| take_profit | 49260.44 | hallucinated | `—` | — | — |
| ob_mid | 49175.21 | misattributed | `timeframes.M15.fair_value_gaps[105].bottom` | 49175.21 | 0.0 |
| ob_high | 49175.21 | accurate | `timeframes.M15.order_blocks[34].high` | 49175.21 | 0.0 |
| ob_low | 49144.21 | accurate | `timeframes.M15.order_blocks[34].low` | 49144.21 | 0.0 |
| protected_swing | 49107.21 | accurate | `timeframes.H1.swings[44].price(low)` | 49107.21 | 0.0 |
| sweep_price | 49188.0 | accurate | `timeframes.M15.swings[183].price(low)` | 49188.0 | 0.0 |

**MSO key levels (top 3 per block):**

- **D1** last close=None (O=None H=None L=None)
  - FVGs: 46302.61-46678.31 (bearish), 45669.41-45896.98 (bearish), 45669.41-46274.38 (bullish)
  - Swings: 48326.0 (high), 47326.28 (low), 49847.0 (high)
- **H1** last close=None (O=None H=None L=None)
  - OBs: 48134.21-48280.71 (bullish), 48456.81-48545.41 (bullish), 48465.5-48495.05 (bullish)
  - FVGs: 48231.9-48253.21 (bullish), 48291.5-48368.85 (bullish), 48461.55-48514.31 (bearish)
  - Breakers: 48456.81-48545.41 (None), 48465.5-48495.05 (None), 49335.6-49427.1 (None)
  - Swings: 49237.38 (low), 48953.21 (low), 49107.21 (low)
- **H4** last close=None (O=None H=None L=None)
  - OBs: 46197.7-46605.2 (bullish), 47703.31-47877.81 (bullish), 48199.81-48244.31 (bullish)
  - FVGs: 46711.28-47492.41 (bullish), 47601.41-47618.41 (bullish), 47787.81-47816.81 (bearish)
  - Breakers: 47703.31-47877.81 (None)
  - Swings: 49039.3 (low), 49623.15 (high), 48953.21 (low)
- **M15** last close=None (O=None H=None L=None)
  - OBs: 48187.9-48199.9 (bullish), 48250.21-48282.21 (bullish), 48226.21-48301.71 (bullish)
  - FVGs: 48221.81-48230.81 (bearish), 48213.81-48218.81 (bearish), 48225.9-48250.21 (bullish)
  - Breakers: 48187.9-48199.9 (None), 48250.21-48282.21 (None), 48433.85-48506.4 (None)
  - Swings: 49228.41 (high), 49188.0 (low), 49278.31 (high)

  - Session levels: asian_high=49326.78, asian_low=48953.21, london_high=49191.21, london_low=49121.21, pdh=49623.15, pdl=49237.38, session_high=49278.31, session_low=49121.21

---

See ``root_cause_hypotheses.md`` (sibling) for the candidate root-cause inventory derived from these inspections.
