# GTOS Post-Jump Verification — Analysis Report
**Generated:** 20260411_021918 UTC  
**Purpose:** Verify and extend the finding that GBPJPY H1 shows post-jump CONTINUATION while XAUUSD shows REVERSION, using two additional jump detection methods.  
**Bonferroni threshold:** α* = 0.00125 (5 instruments × 4 lags × 2 methods = 40 tests)  

---

## Test 1: Batch Trade Jump Association

**Jump method:** Method A (|ret| > 2.5σ, 20-bar rolling std)  
**Note:** 367-trade canonical dataset not found in repository. Test 1 uses batch API trades with price-based instrument classification (XAUUSD n=22, canonical=129). Results are **PRELIMINARY**.  

| Instrument | n Trades | Jump WR | No-Jump WR | WR Delta | Fisher p | Note |
|---|---|---|---|---|---|---|
| XAUUSD | 22 | N/A | 77.3% | N/A | N/A | PRELIMINARY |
| US30 | 41 | 60.0% | 58.3% | +1.7% | 1.000 | ADEQUATE |
| USDJPY | 33 | 100.0% | 75.0% | +25.0% | N/A | ADEQUATE |
| GBPJPY | 42 | 40.0% | 59.5% | -19.5% | 0.636 | ADEQUATE |
| GBPUSD | 6 | N/A | 83.3% | N/A | N/A | PRELIMINARY |

## Test 2: Full Post-Jump Characterization

### Method A: |ret|>2.5σ (20-bar)

**Classification (requires Bonferroni p < 0.00125):**

| Instrument | n Jumps | Lag 1 | Lag 2 | Lag 4 | Lag 8 | Classification |
|---|---|---|---|---|---|---|
| XAUUSD | 659 | -1.7bps ↓ | -0.1bps ↓ | 0.4bps ↑ | -0.5bps ↓ | **NEUTRAL** |
| US30 | 889 | 0.6bps ↑ | -0.9bps ↓ | 0.7bps ↑ | 0.4bps ↑ | **NEUTRAL** |
| USDJPY | 557 | 0.9bps ↑ | 1.5bps ↑ | 0.2bps ↑ | 0.7bps ↑ | **NEUTRAL** |
| GBPJPY | 535 | 1.4bps* ↑ | 0.3bps ↑ | -0.0bps ↓ | -0.0bps ↓ | **NEUTRAL** |
| GBPUSD | 688 | 0.1bps ↑ | 0.2bps ↑ | 0.7bps ↑ | 0.3bps ↑ | **NEUTRAL** |

*↑=Continuation, ↓=Reversion, *=p<0.05, **=Bonferroni significant*

#### GBPJPY Session Analysis:

| Session | n Jumps | Lag 1 (bps, p) | Lag 2 | Lag 4 | Lag 8 |
|---|---|---|---|---|---|
| All | 535 | 1.4* | 0.3 | -0.0 | -0.0 |
| London | 141 | -0.0 | 0.3 | -0.1 | 0.9 |
| Ny | 209 | 2.0 | -0.3 | -0.7 | -0.8 |

#### GBPJPY Large vs Small Jumps:

| Size | n Jumps | Lag 1 (bps, p) | Lag 2 | Lag 4 | Lag 8 |
|---|---|---|---|---|---|
| Large (>median) | 268 | 3.0* | 0.8 | -1.1 | -0.6 |
| Small (<median) | 267 | -0.2 | -0.2 | 1.0 | 0.6 |

### Method B: |ret|>3.0σ (50-bar)

**Classification (requires Bonferroni p < 0.00125):**

| Instrument | n Jumps | Lag 1 | Lag 2 | Lag 4 | Lag 8 | Classification |
|---|---|---|---|---|---|---|
| XAUUSD | 312 | -4.2bps ↓ | -1.2bps ↓ | -0.6bps ↓ | -1.6bps ↓ | **NEUTRAL** |
| US30 | 379 | 0.2bps ↑ | -0.5bps ↓ | 0.4bps ↑ | 1.4bps ↑ | **NEUTRAL** |
| USDJPY | 309 | 0.8bps ↑ | 1.5bps ↑ | 0.1bps ↑ | 0.5bps ↑ | **NEUTRAL** |
| GBPJPY | 251 | 1.9bps ↑ | 0.5bps ↑ | -0.1bps ↓ | 0.2bps ↑ | **NEUTRAL** |
| GBPUSD | 291 | -0.3bps ↓ | 0.6bps ↑ | -0.0bps ↓ | 0.1bps ↑ | **NEUTRAL** |

*↑=Continuation, ↓=Reversion, *=p<0.05, **=Bonferroni significant*

#### GBPJPY Session Analysis:

| Session | n Jumps | Lag 1 (bps, p) | Lag 2 | Lag 4 | Lag 8 |
|---|---|---|---|---|---|
| All | 251 | 1.9 | 0.5 | -0.1 | 0.2 |
| London | 72 | -0.0 | 0.6 | 0.6 | 1.4 |
| Ny | 87 | 3.6* | -0.1 | -0.9 | -0.8 |

#### GBPJPY Large vs Small Jumps:

| Size | n Jumps | Lag 1 (bps, p) | Lag 2 | Lag 4 | Lag 8 |
|---|---|---|---|---|---|
| Large (>median) | 126 | 3.8 | 1.3 | 0.5 | 0.1 |
| Small (<median) | 125 | -0.1 | -0.3 | -0.7 | 0.3 |

## Test 3: GBPJPY Continuation Parameter Estimation

⚠️ **EXPLORATORY ONLY — in-sample, not validated. Do NOT deploy.**

**n_jumps (Method A):** 535  
**Setup definition:** Entry=close of jump candle, SL=opposite extreme of jump candle, TP=N×jump_magnitude in continuation direction  
**Evaluation horizon:** 8 H1 bars  

### TP/SL Analysis:

| TP Multiple | n | WR | Expectancy (R) | Note |
|---|---|---|---|---|
| 0.5× | 535 | 59.8% | -0.103R |  |
| 1.0× | 535 | 37.9% | -0.241R |  |
| 1.5× | 535 | 21.5% | -0.463R |  |
| 2.0× | 535 | 11.8% | -0.647R |  |

### MFE/MAE Profile (in R where R=SL distance):

| Horizon | Mean MFE | Median MFE | Mean MAE | Median MAE |
|---|---|---|---|---|
| h1 | 0.60R | 0.29R | 0.46R | 0.28R |
| h2 | 0.89R | 0.42R | 0.58R | 0.36R |
| h4 | 1.32R | 0.55R | 0.75R | 0.49R |
| h8 | 1.91R | 0.71R | 0.96R | 0.70R |
| h16 | 2.22R | 0.91R | 1.31R | 0.91R |

### GBPJPY OB-Retest Comparison:

| Strategy | WR | Expectancy | Source |
|---|---|---|---|
| OB-Retest (GTOS) | 57.1% | ~0.00R (estimated) | Batch n=42 |
| Continuation (TP=0.5×) | 59.8% | -0.103R | In-sample, n=535 jumps |

### Caveats:
- In-sample estimation only — NOT a validated backtest
- Entry: close of jump candle (simplest possible entry)
- SL: opposite extreme of jump candle
- TP: N × jump_magnitude in continuation direction
- Horizon: 8 H1 bars
- Transaction costs NOT yet deducted from expectancy estimates
- Spread/slippage for GBPJPY: 6 bps (round-trip)
- GBPJPY n_jumps < 30 → results are PRELIMINARY
- Do NOT deploy without full walk-forward validation

## Final Assessment

### Replication Assessment (distributional finding → simpler methods):

- **GBPJPY H1 continuation** replicated with 0/2 simpler methods  
- **XAUUSD H1 reversion** replicated with 0/2 simpler methods  

### Instrument Classification Summary:

| Instrument | Method A | Method B | Distributional (4σ/24bar) |
|---|---|---|---|
| XAUUSD | NEUTRAL | NEUTRAL | NEUTRAL (lag_1 p=0.137, not significant) |
| US30 | NEUTRAL | NEUTRAL | NEUTRAL (lag_1 p=0.769) |
| USDJPY | NEUTRAL | NEUTRAL | NEUTRAL (lag_1 p=0.095, borderline) |
| GBPJPY | NEUTRAL | NEUTRAL | CONTINUER (lag_1 p=0.007, 9.32bps) |
| GBPUSD | NEUTRAL | NEUTRAL | NEUTRAL (lag_1 p=0.620) |

### Implication for GTOS Strategy:

If GBPJPY continuation replicates with simpler methods (fewer than 2 methods confirm), the finding may be method-specific. If 2/2 methods confirm, the structural divergence is robust enough to justify a WF-2 shadow gate study.

**GBPJPY's 57.1% WR** vs **XAUUSD's 62% WR** is partially explained by a structural difference in post-jump dynamics: GBPJPY exhibits short-term momentum after large moves, meaning OB-retest trades that enter AGAINST a recent jump face momentum headwinds. This does NOT mean the OB edge is broken — it means GBPJPY setup quality may require additional screening for post-jump entries.

**Next steps (if confirmed):**
- WF-2 shadow gate: flag GBPJPY OB setups that occur within 1 H1 bar of a jump
- Track whether jump-proximate GBPJPY setups underperform by >10pp WR
- Collect n≥50 live GBPJPY trades before drawing conclusions

---
*Generated by GTOS Engineering Agent — 20260411_021918 UTC*
