# Analysis 1: R-Multiple Decomposition

## Overall Stats

| Metric | Value |
|---|---|
| Total trades | 111 |
| Wins | 72 (64.9%) |
| Losses | 36 (32.4%) |
| Breakeven | 3 (2.7%) |
| **Overall expectancy** | **0.200R** per trade |
| Avg winner R | +0.719R |
| Avg loser R | -0.822R |
| Best trade | +3.77R |
| Worst trade | -1.00R |
| Profit factor | 1.75 |

## Exit Type Distribution

| Exit Type | Count | % | Avg R | WR |
|---|---|---|---|---|
| CLOSED_BE | 33 | 29.7% | +0.226R | 100.0% |
| CLOSED_SESSION_TIMEOUT | 40 | 36.0% | +0.810R | 70.0% |
| CLOSED_SL | 27 | 24.3% | -1.000R | 0.0% |
| CLOSED_TP3_RUNNER | 7 | 6.3% | +0.960R | 100.0% |
| CLOSED_TRAIL | 4 | 3.6% | +0.650R | 100.0% |

## By AI Setup Grade

| Grade | Count | WR | Avg R | Expectancy |
|---|---|---|---|---|
| A | 18 | 72.2% | +0.225R | +0.225R |
| A+ | 90 | 67.8% | +0.222R | +0.222R |
| unknown | 3 | 33.3% | -0.613R | -0.613R |

## By Kill Zone

| Kill Zone | Count | WR | Avg R | Expectancy |
|---|---|---|---|---|
| london | 58 | 74.1% | +0.194R | +0.194R |
| ny | 53 | 60.4% | +0.206R | +0.206R |

## By Confidence Score

| Confidence Bucket | Count | WR | Avg R |
|---|---|---|---|
| 80-84 | 106 | 67.9% | +0.217R |
| unknown | 3 | 33.3% | -0.613R |

## By Framework

| Framework | Count | WR | Avg R |
|---|---|---|---|
| ob_retest | 101 | 72.3% | +0.235R |
| session_sweep | 10 | 20.0% | -0.152R |

## MFE/MAE Analysis

- **Max Favorable Excursion (MFE)**: median 0.51R, mean 0.97R
- **Max Adverse Excursion (MAE)**: median 0.37R, mean 0.55R
- Trades reaching ≥1.0R MFE: 37/111 (33.3%)
- Trades reaching ≥1.5R MFE: 23/111 (20.7%)

## Unfiltered OB Expectancy Estimate

If all 219 OB retest events were traded with fixed TP structure:
- At 70.5% sim WR (from Task 1 rerun)
- TP1 at 1.5 ATR (50% close), TP2 at 2.5 ATR (25% close), TP3 at 4.0 ATR (25% close)
- SL at -1.0R

- Using actual avg winner (+0.719R) and avg loser (-0.822R):
- **Unfiltered expectancy**: 70.5% × 0.719 - 29.5% × 0.822 = **+0.264R per trade**
- **AI-selected expectancy**: +0.200R per trade
- Delta: -0.065R per trade

## Does AI Produce Better R Through Smarter TP Placement?

The AI-selected trades average **+0.200R** per trade.
With the actual win distribution and avg winner of +0.719R,
the system is capturing partial profits (BE stops, trailing) that reduce
average winner R but protect against reversals.

- Trades ≥1.5R: 10, avg confidence: 80
- All trades avg confidence: 80

## Key Findings

1. **+0.200R expectancy is real but thin.** Profit factor 1.75 is viable but leaves little margin for error.
2. **Session timeouts are the dominant exit** (36%) with 70% WR and +0.81R avg — these are the best performers. The system is profitable BECAUSE it lets winners run into session close.
3. **BE stops fire frequently** (30%) with only +0.226R avg — these recover small amounts. The BE mechanism protects capital but leaves a lot of R on the table.
4. **Only 33% of trades reach 1.0R MFE.** Two-thirds of trades never even touch their first target. This is why avg winner is only +0.72R despite 1.5:1 configured RR.
5. **session_sweep framework is a net loser** (20% WR, -0.15R). These 10 trades destroy value and should be evaluated for removal.
6. **London > NY** by 14pp WR (74.1% vs 60.4%) but similar expectancy (+0.19R vs +0.21R) because NY winners are bigger.
7. **A+ and A grades have identical performance.** The grade distinction adds zero information.
8. **Unfiltered OB entries would produce +0.264R vs AI's +0.200R** — the AI filtering actually REDUCES expectancy by 0.065R per trade, consistent with the Q1 finding from Task 1 rerun.