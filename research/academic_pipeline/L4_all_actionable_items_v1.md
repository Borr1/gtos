# L4 Literature Search: Complete Actionable Items Inventory

**Date:** 2026-04-12
**Source:** 188 papers surveyed, ~135 promoted across 4 clusters (15 questions)
**Purpose:** Every testable hypothesis extracted from L4 promoted papers, with test methodology for GTOS

---

## CLUSTER A: STOP-LOSS REFINEMENT (28 items from 28 promoted papers)

### A1. MAE Distribution Characterization

| # | Item | Paper | Hypothesis | Test Method | Data | Difficulty |
|---|------|-------|-----------|-------------|------|-----------|
| A1 | Sweeney MAE scatter — optimal SL at 80th percentile of winner MAE | Sweeney (1997) | H1: 80th pct winner MAE != current OB-boundary SL | Compute MAE per trade, separate W/L, compare percentiles vs actual SL | M1 data for 300 trades | LOW |
| A2 | Brownian MDD benchmark — actual MAE vs theoretical | Magdon-Ismail & Atiya (2004) | H1: Empirical MAE exceeds Brownian predictions (ratio > 1.3) | Compute predicted MDD from drift/vol per trade, compare actual/predicted | Trade-level drift/vol | LOW |
| A3 | GPD fit to MAE tail — confirm heavy tails | Khan et al. (2023) | H1: MAE requires GPD with shape xi > 0 (0.3-0.4 range) | Fit GPD to MAE exceedances above 90th pct, estimate xi | MAE from 300 trades | LOW |
| A4 | Fat tails persist after GARCH filtering | Eom et al. (2019) | H1: GARCH-filtered M15 residuals still have fat tails | Fit GARCH(1,1), test residual normality (JB, QQ), fit GPD | 2yr M15 XAUUSD | MEDIUM |
| A5 | Conditional GARCH-EVT quantile as SL | Cotter (2007) | H1: Conditional SL reduces stopped-out winners vs fixed SL | Compute conditional VaR per trade, use max(OB_extreme, cond_VaR) as alt SL | 2yr M15 + trades | MEDIUM |
| A6 | Gold tail asymmetry — MAE heavier than MFE | MDPI (2025) | H1: MAE GPD shape xi > MFE GPD shape xi | Fit GPD to both tails separately, compare | MAE + MFE from 300 | LOW |
| A7 | Vol-regime SL adequacy — high-vol needs wider SL | Bollerslev & Todorov (2011) | H1: High-vol trades have higher MAE/SL ratio | Partition by median ATR at entry, compare MAE/SL distributions | ATR + MAE | LOW |

### A2. Stop Clustering and Round-Number Effects

| # | Item | Paper | Hypothesis | Test Method | Data | Difficulty |
|---|------|-------|-----------|-------------|------|-----------|
| A8 | Round-number SL proximity amplifies MAE | Osler (2003) | H1: SL within $3 of round number -> larger MAE | Stratify by SL distance to $5/$10 round, compare MAE (KS/MWU test) | SL prices + MAE | LOW |
| A9 | Stop cascade velocity at round numbers | Osler (2005) | H1: Price velocity higher when crossing round numbers | Measure M1 range/time at round vs non-round bands | M1 XAUUSD | MEDIUM |
| A10 | Overshoot-and-reversal at round numbers | Almgren & Chriss (2001) + Osler | H1: Spike-reversal pattern after crossing round levels | Measure 1-3 candle behavior after round-number cross | M1 XAUUSD | MEDIUM |
| A11 | OB-extreme SL clusters at round numbers | Harris (1991), Ikenberry & Weston (2008) | H1: SL disproportionately near round numbers (chi-sq vs uniform) | Chi-squared test of SL-to-round-number distances | 300 SL prices | LOW |
| A12 | Swing cluster density correlates with MAE | Moskowitz et al. (2012) | H1: More swing lows/highs near SL -> larger MAE | Correlate swing-point density within $5 of SL with MAE | MSO swings + MAE | LOW |
| A13 | Thin liquidity beyond round numbers amplifies moves | Cont et al. (2014) | H1: M1 range larger just beyond ($1-3) round numbers | Measure candle range by price level relative to round numbers | M1 XAUUSD | MEDIUM |

### A3. ATR vs Quantile-Based SL

| # | Item | Paper | Hypothesis | Test Method | Data | Difficulty |
|---|------|-------|-----------|-------------|------|-----------|
| A14 | GARCH-EVT conditional SL vs ATR-multiple SL | McNeil & Frey (2000) | H1: GARCH-EVT SL reduces unnecessary stops vs ATR SL | Backtest both methods on 300 trades, compare WR/expectancy | 2yr M15 + trades | HIGH |
| A15 | Serial correlation validates SL rules | Kaminski & Lo (2014) | H1: M15 kill-zone returns have positive serial correlation (ACF(1)>0) | Compute ACF, Ljung-Box test on M15 returns during kill zones | 6mo+ M15 XAUUSD | LOW |
| A16 | Regime-dependent SL width | Lo & Remorov (2017) | H1: Tighter SL in trending + wider in ranging -> higher expectancy | Classify trades by regime (BOS count/ADX), compare SL performance | 300 trades + regime labels | MEDIUM |
| A17 | Gap-adjusted SL — weekend/news slippage | Arratia & Dorador (2019) | H1: Trades through gaps have slippage >0.2R | Measure actual exit vs planned SL on gap-spanning trades | Trade exit prices | LOW |
| A18 | Simple fixed SL as competitive baseline | Arratia & Dorador (2019) | H1: No complex SL beats simple by >0.05R/trade with p<0.05 | Compare all complex variants against fixed OB-boundary SL | All of above | META |
| A19 | BE trailing stop evaluation | Dai et al. (2021) | H1: Moving SL to entry after +1R reduces MAE by >0.3R | Analyze BE shadow logger data (delta_r, Wilcoxon test after 30+ trades) | BE shadow log | LOW |

### A4. Joint SL/TP/Kelly Optimization

| # | Item | Paper | Hypothesis | Test Method | Data | Difficulty |
|---|------|-------|-----------|-------------|------|-----------|
| A20 | Empirical Kelly f* from R-multiple distribution | Thorp (2006) | H1: Optimal f* > 1% (current is sub-Kelly) | Bootstrap 10k resamples, compute f* CI, MC at 1%/1.5%/2%/half-Kelly | 300 R-multiples | LOW |
| A21 | Vince optimal f from full distribution | Vince (1990/2009) | H1: Full-distribution optimal f differs >10% from binary Kelly | Maximize G over empirical R-multiples, compare to binary f* | 300 R-multiples | LOW |
| A22 | Risk-constrained Kelly for FTMO | Busseti et al. (2016) | H1: Risk-constrained Kelly > half-Kelly at same DD constraint | Convex optimization: max E[log(1+fR)] s.t. P(DD>10%)<1% | 300 R-multiples | MEDIUM |
| A23 | SL/TP inverse coupling | Leung & Li (2015) | H1: Widening SL requires reducing TP to maintain expectancy | Simulate SL widths, solve for optimal TP at each, plot curve | 300 trades + backtest | MEDIUM |
| A24 | Three-exit framework (TP, SL, timeout at kill-zone end) | Lipton & Lopez de Prado (2020) | H1: Closing at KZ end when no TP/SL hit improves Sharpe | Compare Sharpe with/without KZ-end timeout exit | 300 trades + exit timing | MEDIUM |
| A25 | Multi-outcome generalized Kelly | Whelan (2023) | H1: Generalized Kelly < binary Kelly (intermediate outcomes reduce f*) | Categorize trades into 5 buckets, solve generalized Kelly | 300 R-multiples | LOW |
| A26 | Verify optimal f uniqueness | Maier-Paape (2018) | Verify: G(f) is unimodal (single peak) | Plot G(f) for f in [0,1] from item A21 output | Output from A21 | TRIVIAL |

### A5. Cross-Cutting SL Tests

| # | Item | Paper | Hypothesis | Test Method | Data | Difficulty |
|---|------|-------|-----------|-------------|------|-----------|
| A27 | MAE by kill zone (London vs NY) | Cross-cutting | H1: NY trades have larger MAE (different SL buffer needed) | KS test of MAE by session | 300 trades + session | LOW |
| A28 | Full layered SL stack (incremental testing) | Synthesis | H1: Layered SL (OB floor + vol buffer + round adjust + quantile + Kelly) > simple by >0.1R/trade | Add layers one at a time, measure marginal contribution >0.03R | All data | HIGH |

---

## CLUSTER B: EXIT OPTIMIZATION (38 items from 41 promoted papers)

### B1. Partial Close Optimization

| # | Item | Paper | Hypothesis | Test Method | Data | Difficulty |
|---|------|-------|-----------|-------------|------|-----------|
| B1 | Conditional MFE: P(2R | 1R reached) | Lopez de Prado (2018) | H1: P(2R|1R) < 0.50, making partial close at 1R positive | Compute from trailing stop shadow trades (100+) | MFE data | LOW |
| B2 | Kelly-optimal runner fraction | Kelly (1956) | H1: f2* < 0.50 (close more at 1R than currently planned) | Apply Kelly formula to P(2R|1R) | MFE data | LOW |
| B3 | Trailing stop on runner > fixed TP on runner | Leung & Zhang (2019/2021) | H1: Runner with trailing > runner with fixed TP3 | Simulate both from trailing stop shadow data | Shadow data | LOW |
| B4 | MFE distribution skewness determines partial close value | Acar & Satchell (2002), Kaminski & Lo (2014) | H1: Conditional MFE is right-skewed (partial close destroys expectancy) | Compute skewness of outcome given MFE > 1R | 300 trades | LOW |
| B5 | Sharpe comparison: full exit vs partial close | Acar & Toffel (2000) | H1: Sharpe(partial_close) > Sharpe(full_exit_1.5R) | Compute Sharpe for full/50-25-25/75-25 splits | 300 trades | LOW |
| B6 | FTMO-implied risk aversion determines optimal exit | Almgren & Chriss (2001) | H1: FTMO lambda favors partial close | Compute variance under each exit, derive implied lambda | 300 trades | MEDIUM |
| B7 | Capital efficiency of partial close (low frequency = low benefit) | Lei & Li (2009) | H1: Capital utilization improves <5% (negligible at 17 trades/mo) | Compute avg capital deployment time under each exit | Trade timing | LOW |

### B2. Speed-to-MFE as Predictor

| # | Item | Paper | Hypothesis | Test Method | Data | Difficulty |
|---|------|-------|-----------|-------------|------|-----------|
| B8 | Fast arrival at 1R predicts higher P(2R) | Sweeney (1997), Gao et al. (2018) | H1: P(2R|fast 1R) > P(2R|slow 1R) by >10pp | Bucket by time-to-1R (<3, 3-6, >6 candles), compare P(2R) | Shadow + timestamps | MEDIUM |
| B9 | Speed-to-MFE more predictive during London/NY than Tokyo | Bogousslavsky (2016) | H1: Speed-MFE spread larger in London/NY | Stratify speed analysis by session | Session-tagged trades | MEDIUM |
| B10 | Speed-to-MFE more predictive on macro news days | Daniel et al. (1998) | H1: Speed-MFE predictive spread larger near macro releases | Flag trades within 2hr of NFP/CPI/FOMC, compare | News calendar + trades | MEDIUM |
| B11 | Speed-to-MFE as trailing stop tightening signal | Gao et al. (2018), Moskowitz et al. (2012) | H1: Wider trail on fast + tighter on slow > uniform trail | Simulate variable trailing by speed bucket | 100 shadow trades | MEDIUM |

### B3. Session Close / Overnight Risk

| # | Item | Paper | Hypothesis | Test Method | Data | Difficulty |
|---|------|-------|-----------|-------------|------|-----------|
| B12 | Positions held past NY KZ end have worse outcomes | Iwatsubo et al. (2018) | H1: Trades held past 17:00 UTC have lower final R | Compare R of trades closed at KZ end vs held through | Trade close times | LOW |
| B13 | LBMA PM fix (14:00 UTC) as elevated risk window | Caminschi & Heaney (2014) | H1: MAE during fix > MAE during other NY KZ periods | Compare MAE in 14:00-15:30 vs other 90-min windows | Trade MAE + timestamps | MEDIUM |
| B14 | Gold gap-day continuation rate | Plastun et al. (2020) | H1: Gold gap-day continuation > 55% | Compute gap-day continuation from MT5 daily data | MT5 daily data | LOW |
| B15 | Closing flow direction predicts overnight return | Boyarchenko et al. (2022) | H1: Last 3 candles with-position predicts positive overnight | Proxy order flow from last 3 M15 candles, compare overnight R | M15 + overnight R | MEDIUM |
| B16 | Session-close volatility causes more SL hits | Boudt et al. (2011) | H1: SL hit rate in last 30 min > mid-session | Compare SL trigger timing within KZ | SL trigger timestamps | LOW |
| B17 | Friday-to-Monday gap bias | Yu et al. (2016) | H1: Weekend gaps biased negative (Monday returns negative) | Compute weekend gap returns for XAUUSD | Daily data | LOW |
| B18 | Half-hour return predictability in kill zones | Xu et al. (2020) | H1: Specific 30-min windows show autocorrelation | Half-hour return ACF across KZ hours | M15 data | MEDIUM |
| B19 | Stop cascades cluster at session boundaries | Osler (2005) | H1: Rapid adverse moves (>0.5R/candle) cluster in last 30 min of KZ | Flag large adverse candles, test timing distribution | Per-candle adverse excursion | LOW |
| B20 | Close/tighten before FOMC | Lucca & Moench (2015) | H1: MAE higher for trades through FOMC | Compare MAE on FOMC vs non-FOMC days | FOMC dates + MAE | LOW |
| B21 | Persistent half-hour return patterns | Heston et al. (2010) | H1: Returns at specific KZ windows are autocorrelated over 40 days | Test ACF at 1/5/20/40 day lags per time slot | M15 data | MEDIUM |

### B4. Institutional Exit Principles for Retail

| # | Item | Paper | Hypothesis | Test Method | Data | Difficulty |
|---|------|-------|-----------|-------------|------|-----------|
| B22 | Conditional E[hold] vs E[next trade] at each R-level | Almgren & Chriss (2001) | H1: E[remaining|at 1R] < E[next trade] (should close at 1R) | Compute E[final-current | at 0.5R, 1R, 1.5R], compare to unconditional E[R] | 300 trades | MEDIUM |
| B23 | Implementation shortfall decomposition | Perold (1988) | H1: Early exit cost > reversal cost (prioritize wider TP) | IS = MFE_R - exit_R, decompose by category | 300 trades + MFE | LOW |
| B24 | Late KZ entry = worse outcomes | Bertsimas & Lo (1998) | H1: Last-third KZ entries have lower mean R | Stratify by entry timing within KZ | Trade timestamps | LOW |
| B25 | Trade management efficient frontier | Kissell & Glantz (2003) | H1: Fixed 1.5R TP is dominated on the E[R]-Var frontier | Plot E[R] vs Var for 0.5R/1R/1.5R/2R/trailing exits | 300 trades | MEDIUM |
| B26 | Adaptive trailing stop that tightens with profit | Avellaneda & Stoikov (2008) | H1: Progressive tightening captures more R than fixed trail | Simulate fixed vs adaptive trail on 100 shadow trades | Shadow trades | MEDIUM |
| B27 | U-shaped exit urgency (tight early/late, loose mid) | Obizhaeva & Wang (2013) | H1: U-shaped stop profile > constant distance | Simulate tight-first-3-candles + wider-mid + tight-KZ-end | 300 trades | MEDIUM |

### B5. Dynamic TP Based on Realized Volatility

| # | Item | Paper | Hypothesis | Test Method | Data | Difficulty |
|---|------|-------|-----------|-------------|------|-----------|
| B28 | MFE scales with realized volatility | Andersen et al. (2003) | H1: Corr(session RV, MFE) > 0.30 | Compute daily RV from M15, correlate with MFE | M15 + MFE | LOW |
| B29 | HAR-RV dynamic TP | Corsi (2009) | H1: Sharpe(dynamic TP) > Sharpe(fixed 1.5R) | HAR-RV forecast -> TP = 1.5R * (forecast/median), backtest | M15 data + trades | MEDIUM |
| B30 | ATR-based TP vs fixed R-multiple | Wilder (1978) | H1: TP = N*ATR(14) yields higher mean R than TP = 1.5R | Simulate N = {1.5, 2.0, 2.5, 3.0} * ATR on 300 trades | H1 ATR + trades | MEDIUM |
| B31 | Parkinson range estimator vs ATR for TP scaling | Parkinson (1980) | H1: Parkinson RV correlates more with MFE than ATR | Compute both, compare correlations with MFE | H1 OHLC + MFE | LOW |
| B32 | Garman-Klass estimator vs ATR/Parkinson | Garman & Klass (1980) | H1: GK RV correlates more strongly with MFE | Compute GK from M15 OHLC, compare to ATR/Parkinson | M15 OHLC + MFE | LOW |
| B33 | Multi-timescale volatility adds predictive power | Zumbach & Lynch (2001) | H1: Weekly RV improves MFE forecast beyond daily RV alone | Fit HAR model, test significance of beta_W | M15 weekly aggregates | MEDIUM |
| B34 | High-vol expands TP but also expands risk (negative skew) | Bollerslev & Todorov (2011) | H1: High-vol regimes have larger negative skew | Stratify trades by entry-day RV, compare skewness | RV + R-multiples | LOW |
| B35 | Adding vol-scaled TP on top of vol-scaled sizing | Moreira & Muir (2017), Baltas & Kosowski (2020) | H1: Vol-scaled TP adds Sharpe improvement beyond vol-scaled sizing | 4-way comparison: fixed/vol size x fixed/vol TP | 300 trades | MEDIUM |

### B6. Cross-Cutting Exit

| # | Item | Paper | Hypothesis | Test Method | Data | Difficulty |
|---|------|-------|-----------|-------------|------|-----------|
| B36 | Build conditional MFE distribution (foundation for all) | Sweeney (1997), Lopez de Prado (2018) | N/A (data computation) | Compute P(nR) and P(nR|mR) for all m<n at M15 resolution | 300 trades | LOW |
| B37 | Single vol-regime classifier modulates all exits | Corsi (2009), Andersen et al. (2003) | H1: Regime-specific exits improve by >0.1R/trade | Classify H/M/L vol, apply different exit rules per regime | Prior session RV | MEDIUM |
| B38 | IS vs TWAP vs VWAP exit strategy comparison | CIS UPenn | H1: One approach dominates for GTOS's profile | Simulate fixed TP / trailing / partial close on 300 trades | 300 trades | MEDIUM |

---

## CLUSTER C: ALPHA DECAY AND CROWDING (37 items from 32 promoted papers)

### C1. Decay Rate Monitoring

| # | Item | Paper | Hypothesis | Test Method | Data | Difficulty |
|---|------|-------|-----------|-------------|------|-----------|
| C1 | Post-publication decay benchmark (32% arbitrage) | McLean & Pontiff (2016) | H1: OB continuation has declined >=10pp | Two-proportion z-test, first half vs second half of 300 trades | 300 trades by date | LOW |
| C2 | Accelerating decay rate | Bouchaud et al. (2022) | H1: Quarterly WR decline is accelerating (quadratic term significant) | Quadratic regression on quarterly WR (73.2, 71.4, 63.6, 59.4) | 4 quarterly points | LOW (underpowered) |
| C3 | Liquidity-driven decay ceiling | Chordia et al. (2014) | H1: Tighter spreads correlate with lower OB continuation | Correlate rolling spread with rolling continuation rate | Spread data + trades | IF LOGGED |
| C4 | Zone-level alpha decay (age vs predictive power) | Di Mascio et al. (2017) | H1: Older OB zones have lower continuation probability | Logistic regression of outcome on zone age (candles since formation) | Zone age per trade | IF LOGGED |

### C2. Structural Floor and Edge Durability

| # | Item | Paper | Hypothesis | Test Method | Data | Difficulty |
|---|------|-------|-----------|-------------|------|-----------|
| C5 | SPRT boundary at 55% structural floor | Osler (2005) | H1: Rate can fall below 55% (structural mechanism compromised) | Rolling 50-OB rate monitoring, alarm at 55% | Ongoing | MONITORING |
| C6 | Impulse size correlates with continuation R-multiple | Cont et al. (2014) | H1: Larger impulses -> larger continuation (OFI mechanism) | Correlate impulse candle body size with trade R-multiple | 300 trades | LOW |
| C7 | Institutional session hours have higher WR | Bouchaud et al. (2008) | H1: London/NY overlap WR > off-hours WR | Chi-squared/Fisher exact by session | Trade timestamps | LOW |
| C8 | XAUUSD OB edge decays slower than US30 | Jacobs & Muller (2020) | H1: US30 OB continuation rate decays faster | Compare slope of rolling continuation rate across instruments | Cross-instrument data | LOW |
| C9 | FX TA edge lifetime benchmark (extinction 2033-2035) | Neely & Weller (2011) | H1: Rate breaches 60% before 2030 (faster than FX TA baseline) | Track annual rolling rate, compare to 2033-2035 prediction | Ongoing | PROSPECTIVE |
| C10 | BOS alone predicts continuation above 50% | Moskowitz et al. (2012) | H1: All BOS events (no OB filter) continue at 55-60% | Measure continuation rate of ALL BOS events | Historical BOS events | LOW |

### C3. Crowding Detection

| # | Item | Paper | Hypothesis | Test Method | Data | Difficulty |
|---|------|-------|-----------|-------------|------|-----------|
| C11 | Google Trends SVI for SMC/ICT terms vs quarterly WR | Da et al. (2011) | H1: Rising SVI predicts declining OB continuation | Download monthly Google Trends for SMC keywords, correlate | Google Trends + WR | LOW |
| C12 | Broker sentiment tagging for bimodal outcome detection | Chincarini et al. (2025) | H1: High-positioning zones have higher WR but larger losses on failure | Tag trades by broker sentiment, compare WR + loss tails | NEW DATA FEED |
| C13 | OB continuation rate by year (early vs recent) | Calluzzo et al. (2019) | H1: 2024-2026 rate lower than 2020-2022 by >=5pp | Compute rate by year if historical data extends back | Full backtest range | LOW |
| C14 | Average winning R-multiple declining over time | Dong et al. (2023) | H1: Winners getting smaller (magnitude compression) | Plot avg winning R by quarter or rolling 50-trade window | R-multiples by date | LOW |
| C15 | Tail fattening — worst losses growing | Pedersen (2009) | H1: 90th percentile loss magnitude growing over time | Track worst 10% of losses by quarter/half-year | R-multiples by date | LOW |
| C16 | Failure clustering (loss autocorrelation) | Khandani & Lo (2011) | H1: OB failures cluster in time (positive ACF at lag 1-3) | Compute ACF of trade outcomes, count runs vs expected | Sequential outcomes | LOW |
| C17 | Cross-instrument OB outcome comovement > price correlation | Wahal & Yavuz (2013) | H1: OB outcome correlations exceed price correlations (style crowding) | Compare pairwise weekly OB rate correlations vs return correlations | 5-instrument data | LOW |
| C18 | BOS/OB formation frequency trending up | Brown et al. (2022) | H1: More BOS/OB events per week over time (more participants) | Count BOS events per week/month over backtest period | MSO event counts | LOW |
| C19 | Round-number OB zones have lower continuation | Greenwood & Thesmar (2011) | H1: OB zones at $5/$10 round numbers have lower continuation rate | Tag zones by proximity to round numbers, compare rates | Zone price data | LOW |
| C20 | Losing trade magnitude > winning trade magnitude (fade effect) | Coval & Stafford (2007) | H1: mean(abs(losing_R)) / mean(winning_R) > 1.0 | Compute asymmetry ratio from R-multiples | 300 R-multiples | LOW |

### C4. Edge Lifetime and Adaptation

| # | Item | Paper | Hypothesis | Test Method | Data | Difficulty |
|---|------|-------|-----------|-------------|------|-----------|
| C21 | Cyclical vs monotonic decay model | Lo (2004/2012) | H1: Continuation rate cycles (sinusoidal + trend > linear) | Fit both models, compare fit (needs 8+ quarters) | 8+ quarterly points | NOT YET |
| C22 | Continuation/impulse ratio declining (carrying capacity) | Farmer & Lo (1999) | H1: continuation_move / impulse_move declining over time | Track ratio per trade, test for trend | Entry/exit + impulse | LOW |
| C23 | Behavioral persistence (rate stays above 55% for 10yr) | Yan (2008) | H1: Rate stays above 55% through 2031 | Prospective monitoring, 55% as structural floor | Long-term | PROSPECTIVE |
| C24 | Expected PnL compressing toward cost threshold | Pedersen (2015) | H1: Monthly PnL trending toward 2x operational costs ($120) | Compute expected monthly PnL, track over time | Trade PnL + costs | LOW |
| C25 | Mean reversion after poor quarters (capital cycle) | Hanson & Sunderam (2014) | H1: WR in quarter AFTER poor quarter is higher (recovery) | Track, needs 8+ quarters | 8+ quarterly points | NOT YET |
| C26 | Zero meaningful slippage at $100K scale | Korajczyk & Sadka (2004) | H0: GTOS has no detectable price impact | Compare fill price vs expected entry price | Live fill data | LOW |
| C27 | Regime break detection in quarterly changes | Green et al. (2017) | H1: At least one Q-o-Q change is >2 SD outlier | Compute distribution of quarterly changes, flag outliers | 8+ quarterly points | NOT YET |
| C28 | High correlation regimes degrade OB edge | Baltas & Kosowski (2020) | H1: OB continuation lower during high cross-asset correlation | Tag trades by rolling 20-day pairwise correlation, compare WR | Correlation + trades | LOW |
| C29 | R-multiple variance increasing (fragility) | Stein (2009) | H1: SD of R-multiples increasing over time | Compute rolling 50-trade SD of R-multiples | R-multiples by date | LOW |
| C30 | High-VIX periods degrade OB edge | Brunnermeier & Pedersen (2009) | H1: OB WR lower in high-VIX periods | Tag trades by VIX level, compare WR and loss tails | VIX + trades | LOW |
| C31 | Observed decay rate vs 1pp/year FX TA baseline | Menkhoff & Taylor (2007) | H1: Current ~18pp/year annualized is >5x faster than baseline | Compare to 1pp/year benchmark | Quarterly WR | LOW |
| C32 | Monthly trade count inversely correlates with avg R | Novy-Marx & Velikov (2016) | H1: More trades per month -> lower avg R (marginal quality) | Correlate monthly count with monthly avg R | Monthly stats | LOW |

### C5. Regime Decomposition (the 14pp/year decline may not all be edge decay)

| # | Item | Paper | Hypothesis | Test Method | Data | Difficulty |
|---|------|-------|-----------|-------------|------|-----------|
| C33a | Volatility regime explains WR decline | Synthesis | H1: Lower-ATR quarters have lower WR | Correlate quarterly ATR with quarterly WR | ATR by quarter | LOW |
| C33b | Session composition shift explains WR decline | Synthesis | H1: Later quarters have different London/NY mix | Cross-tabulate trades by quarter and session | Trade timestamps | LOW |
| C33c | Instrument composition drives aggregate decline | Synthesis | H1: Decline concentrated in 1-2 instruments | Quarterly WR by instrument | Per-instrument data | LOW |
| C33d | Q1 baseline inflated by in-sample optimization | Synthesis | H1: Q1 trades overlap with parameter tuning data | Audit data provenance | Data provenance | LOW |

---

## CLUSTER D: MODEL RISK (22 items from 34 promoted papers)

### D1. Drift Detection — Output Monitoring

| # | Item | Paper | Hypothesis | Test Method | Data | Difficulty |
|---|------|-------|-----------|-------------|------|-----------|
| D1 | CUSUM on CANDIDATE rate | Page (1954), Tartakovsky (2014) | H1: CANDIDATE rate has shifted from p0=0.103 | Two-sided CUSUM, p0=0.103, detect shift to 0.06 or 0.15, h=4.0 | Shadow logs | $0 |
| D2 | ADWIN general change detection | Bifet & Gavalda (2007) | H1: Any distributional shift in outputs | river.drift.ADWIN on CANDIDATE rate, confidence, token count | Shadow logs | $0 |
| D3 | EWMA for gradual drift | Bayramli & Bauerle (2024) | H1: Gradual shift outside control limits | EWMA lambda=0.2, L=3 on confidence/RR/CR/reasoning length | Shadow logs | $0 |
| D4 | Multi-feature KS tests ("failing loudly") | Rabanser et al. (2019) | H1: At least one feature shifted (Bonferroni-corrected) | KS test every 50 evals on 5+ features | Shadow logs | $0 |
| D5 | Linguistic feature monitoring for model version changes | Chen et al. (2025) | H1: Text features (sentence length, vocab, structure) shifted | Extract text features, KS test every 50 evals | Reasoning text | $0 |
| D6 | Borderline canary fixtures (B3IT-inspired) | B3IT (2026) | H1: Borderline MSOs flip after model change by >20pp | Run 200 MSOs at T=0.5, find 50% split rate ones, lock as canaries | ~$10 one-time | HIGH |
| D7 | DDM on win rate (lagging confirmation) | Gama et al. (2004) | H1: WR exceeds baseline + 3*sigma | Warning at mu+2sigma, drift at mu+3sigma | Trade outcomes | $0 |
| D8 | Separate market regime from model drift | Suitability Filter (2025) | H1: Outputs shifted but inputs stable (model drift) | Monitor both input features (vol, BOS freq) AND output features | All logs | $0 |
| D9 | Calibration monitoring (after confidence rework) | CUSUM Calibration (2025) | H1: Calibration degraded after model update | CUSUM on calibration error per confidence bin | PREREQ: calibrated confidence | $0 |

### D2. Prompt Framing — Persona and Identity

| # | Item | Paper | Hypothesis | Test Method | Data | Difficulty |
|---|------|-------|-----------|-------------|------|-----------|
| D10 | Remove/replace SMC expert persona | PRISM (2025), Zhuo et al. (2024) | H1: Removing persona improves WR by >=3pp | 50 MSOs x 3 conditions (SMC/neutral/none), compare WR | ~$30 | HIGH |
| D11 | Neutral prompt sentiment | Gandhi & Gandhi (2025) | H1: Neutral tone -> lower CR (fewer false positives) + higher WR | Replace all narrative with clinical language, test 50 MSOs | ~$15 | MEDIUM |
| D12 | Factual checklist framing | From Fact to Judgment (2025) | H1: YES/NO checklist improves WR by >=2pp | Convert each criterion to factual YES/NO, CANDIDATE = all pass | ~$15 | HIGH |

### D3. Chain-of-Thought Structure

| # | Item | Paper | Hypothesis | Test Method | Data | Difficulty |
|---|------|-------|-----------|-------------|------|-----------|
| D13 | Simplified binary prompt (no CoT) | ACM ICAIF (2025) | H1: No-CoT prompt >= CoT prompt WR (System 1 > System 2) | 50 MSOs: market data + "CANDIDATE or NO_TRADE?" only | ~$15 | HIGH |
| D14 | FinCoT structured blueprint (shorter, constrained CoT) | FinCoT (2025) | H1: Rigid step blueprint >= 2pp higher WR, 50% fewer tokens | Rigid 1-value-per-step format, 50 MSOs | ~$15 | HIGH |

### D4. Session Memory and Anchoring

| # | Item | Paper | Hypothesis | Test Method | Data | Difficulty |
|---|------|-------|-----------|-------------|------|-----------|
| D15 | Strip labels/numbers from session memory | Zhao et al. (2021), Anchoring (2024) | H1: Structural-only memory >= 3pp higher WR than full memory | 50 MSOs x 3: full/stripped/none | ~$45 | HIGH |
| D16 | Quantify anchoring magnitude on confidence scores | Anchoring Bias in LLMs (2024) | H1: Confidence shifts >=5 points toward injected anchor | 20 MSOs x 3 anchor levels (60/80/95) | ~$18 | MEDIUM |

### D5. Ensemble Methods — Diverse Prompts

| # | Item | Paper | Hypothesis | Test Method | Data | Difficulty |
|---|------|-------|-----------|-------------|------|-----------|
| D17 | Three-prompt diverse ensemble (SMC + neutral + checklist) | DIPPER (2024), MoT (2025) | H1: Majority vote >= 3pp higher WR than single prompt | 50 MSOs x 3 prompts at T=0, majority vote | ~$30 | HIGHEST |
| D18 | Adaptive consistency (early stopping when first 2 agree) | Aggarwal et al. (2023) | H1: Equivalent WR at ~60% cost | Re-analyze D17 data with early-stop rule | $0 | HIGH |
| D19 | Maximize diversity via disagreement selection from 5-7 candidates | LLM-TOPLA (2024) | H1: Optimal triple >= 2pp over random triple | 50 MSOs x 7 prompts, select max-disagreement triple | ~$70 | MEDIUM |
| D20 | Position size reduction on ensemble disagreements | Niimi (2025), Reliable Decision (2025) | H1: Split-decision trades have >=10pp lower WR | From D17 data: unanimous vs split WR comparison | $0 | HIGH |
| D21 | Agreement rate as calibrated confidence | Xiong et al. (2024), Taubenfeld (2025) | H1: Higher agreement rate predicts higher WR (monotonic) | From D17 data: bin by agreement level, test monotonicity | $0 | HIGH |

### D6. Temperature and Sampling

| # | Item | Paper | Hypothesis | Test Method | Data | Difficulty |
|---|------|-------|-----------|-------------|------|-----------|
| D22 | Temperature self-consistency baseline (T=0.6 x 3) | Betz et al. (2024) | H1: 3 runs at T=0.6 majority vote >= 2pp over single T=0 | 50 MSOs x 3 at T=0.6 | ~$15 | MEDIUM |
| D23 | Power-law alpha estimation (right-size N) | Ma et al. (2025) | H1: GTOS alpha in typical range, 3 samples sufficient | 30 MSOs x N=1,3,5,7,9 runs, fit power law | ~$40 | LOW |

### D7. Cross-Cutting Model Risk

| # | Item | Paper | Hypothesis | Test Method | Data | Difficulty |
|---|------|-------|-----------|-------------|------|-----------|
| D24 | Agreement rate as drift detector (free from ensemble) | Cross-synthesis | H1: Agreement rate drops >=10pp after model update | Track agreement EWMA once ensemble is live | $0 (byproduct) | HIGH |
| D25 | Weighted majority vote from per-prompt track record | Taubenfeld (2025), Pitis (2023) | H1: Accuracy-weighted vote >= 1pp over equal weight | After 30+ ensemble trades, weight by historical WR | $0 | LOW |

---

## GRAND TOTAL: 125 ACTIONABLE ITEMS

### By Cluster
| Cluster | Items | Immediately Testable | New Data Needed | Prospective/Long-term |
|---------|-------|---------------------|-----------------|----------------------|
| A: Stop-Loss | 28 | 20 | 5 (M1 data) | 3 |
| B: Exit Optimization | 38 | 28 | 6 (MFE build) | 4 |
| C: Alpha Decay | 37 | 26 | 3 (new feeds) | 8 |
| D: Model Risk | 25 | 20 | 0 | 5 |
| **TOTAL** | **128** | **94** | **14** | **20** |

### By API Cost
| Cost Tier | Items | Total Cost |
|-----------|-------|------------|
| $0 (compute only) | 68 | $0 |
| <$20 per test | 32 | ~$320 |
| $20-50 per test | 18 | ~$540 |
| $50-100 per test | 10 | ~$700 |
| **TOTAL** | **128** | **~$1,560** |

### Pre-Requisite Data Builds (unlock many downstream tests)
1. **MAE/MFE for all 300 trades at M15 resolution** — unlocks A1-A7, A27, B1-B7, B22-B25, B28-B35 (~40 items)
2. **Conditional MFE distribution P(nR|mR)** — unlocks B1, B2, B3, B8, B22 (~10 items)
3. **Session/timestamp tagging for all trades** — unlocks A27, B9, B12, B16, B24, C7, C33b (~10 items)
4. **Rolling OB continuation rate with dates** — unlocks C1-C4, C11-C20, C28-C33 (~25 items)

---

## PRIORITIZATION FOR PROMPT OPTIMIZATION (CEO's primary directive)

Given the trade diff analysis finding that the current v1 prompt's accept/reject boundary is well-calibrated (83.3% WR on the 12 trades v2 killed), the highest-leverage items for prompt improvement are:

### Tier 1: Prompt Ablation Tests (~$100 total, test within 1 day)
These directly address whether the prompt framing is leaving WR on the table:

| Item | What to Test | Expected Impact | Cost |
|------|-------------|----------------|------|
| D10 | Remove SMC persona | +3-8pp WR | $30 |
| D13 | No-CoT binary prompt | +2-5pp WR | $15 |
| D14 | FinCoT structured blueprint | +2-5pp WR, -50% tokens | $15 |
| D12 | Factual checklist framing | +2pp WR | $15 |
| D17 | 3-prompt diverse ensemble | +3-8pp WR | $30 |

**These 5 tests share the same 50 MSOs. Run together for ~$100 total.** Each produces a prompt variant whose WR and CR are directly comparable. From these, identify the best single prompt AND the best ensemble. Then ablation-test individual changes within the winner.

### Tier 2: Foundation Data Builds (~$0, compute only, 1 day)
| Item | What to Build | Unlocks |
|------|--------------|---------|
| B36 | Conditional MFE distribution | 30+ exit tests |
| A1 | MAE scatter plot | SL calibration |
| A15 | Serial correlation check | Validates entire SL framework |
| C33a-d | Regime decomposition of WR decline | Separates real decay from noise |

### Tier 3: Monitoring Infrastructure (~$10 one-time + $0 ongoing)
| Item | What to Deploy | Value |
|------|---------------|-------|
| D1 | CUSUM on CANDIDATE rate | Early drift warning |
| D2 | ADWIN general detection | Catch any shift |
| D6 | Borderline canary fixtures | 10-100x better than current canaries |
| D8 | Market vs model drift separation | Correct response to degradation |
