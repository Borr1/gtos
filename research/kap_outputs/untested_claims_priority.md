# Untested Claims Priority Analysis
**Date:** 2026-04-07
**Analyst:** Salma (Operations)
**Purpose:** CEO directive to prioritize untested high-confidence claims

## Total Claims by Category

- **RULE**: 85 claims (35.4%)
- **STATISTICAL**: 69 claims (28.7%)
- **OTHER**: 52 claims (21.7%)
- **CORRELATION**: 29 claims (12.1%)
- **CORRELATION_CLAIM**: 5 claims (2.1%)

**Total Claims Analyzed:** 240

**Testable Claims:** 181 (75.4%)
**Untested Testable Claims:** 181

## Top 10 Highest-Confidence Untested Claims

### 1. STATISTICAL - Confidence: 6.0
**Source:** video_01_claims.json | **Credibility:** DATA | **Relevance:** DIRECT

**Claim:** Backtesting 100 order blocks on EURUSD H1 with a mechanical 1:2 RR setup yielded a 43% win rate (31 wins, 41 losses, 28 untriggered)

**Test Method:** Can replicate 100-OB backtest on EURUSD H1 with same criteria (FVG + BOS + unmitigated, entry at OB open, SL at OB end, TP at 2x SL)

**Context:** Speaker presents results of backtesting 100 OBs using Trader Edge software on EURUSD H1

---

### 2. STATISTICAL - Confidence: 6.0
**Source:** video_01_claims.json | **Credibility:** DATA | **Relevance:** DIRECT

**Claim:** A 43% win rate with 1:2 risk-reward grew a $10,000 account by 47% (2% risk per trade targeting 4%)

**Test Method:** Pure math verification: 31 wins × 4% − 41 losses × 2% = 124% − 82% = 42% (close to 47% with compounding)

**Context:** Speaker showing account growth from the 100-trade OB backtest

---

### 3. STATISTICAL - Confidence: 6.0
**Source:** video_01_claims.json | **Credibility:** DATA | **Relevance:** DIRECT

**Claim:** Maximum drawdown was 10% during the 100-trade OB backtest on EURUSD H1

**Test Method:** Can replicate and track equity curve drawdown during the same backtest

**Context:** Speaker reporting drawdown from backtesting results

---

### 4. STATISTICAL - Confidence: 6.0
**Source:** video_01_claims.json | **Credibility:** DATA | **Relevance:** DIRECT

**Claim:** 28 out of 100 order blocks were never triggered by price (untriggered rate of 28%)

**Test Method:** Can count untriggered OBs in own backtest — relevant for position sizing (not every OB becomes a trade)

**Context:** Speaker breaking down results showing a significant portion of OBs never get tested

---

### 5. CORRELATION - Confidence: 6.0
**Source:** video_01_claims.json | **Credibility:** DATA | **Relevance:** DIRECT

**Claim:** Most winning OB trades happen on highly volatile midweek days; Monday and Friday (low liquidity days) produce more losing trades

**Test Method:** Can segment OB trade results by day-of-week and compare WR for Mon/Fri vs Tue-Thu

**Context:** Speaker analyzing when winning OB trades cluster in backtest results

---

### 6. RULE - Confidence: 6.0
**Source:** video_01_claims.json | **Credibility:** DATA | **Relevance:** DIRECT

**Claim:** Recently printed (fresh) order blocks have higher win rates than older ones — market changes direction and old OBs lose relevance

**Test Method:** Can measure OB hold rate as a function of age (candles since formation) — expect inverse correlation

**Context:** Speaker observing that stale OBs underperform in backtest results

---

### 7. RULE - Confidence: 6.0
**Source:** video_01_claims.json | **Credibility:** DATA | **Relevance:** DIRECT

**Claim:** A valid order block requires three conditions: must create inefficiency (FVG), must lead to BOS or CHoCH, and must be unmitigated (first touch only)

**Test Method:** Can test each condition individually: OBs with FVG vs without, with BOS vs without, first touch vs second touch

**Context:** Speaker defining the three OB validation rules used in the 100-trade backtest

---

### 8. STATISTICAL - Confidence: 6.0
**Source:** video_01_claims_test.json | **Credibility:** DATA | **Relevance:** DIRECT

**Claim:** Out of 100 order blocks backtested on EURUSD 1H, 28 were not triggered, 41 lost, and 31 won, giving a 43% win rate (31/72 triggered trades)

**Test Method:** Can replicate by backtesting 100 OB setups on EURUSD 1H with the same entry/SL/TP rules and comparing win rate

**Context:** Speaker presented backtesting results from 100 OB trades using Trader Edge software on EURUSD 1H

---

### 9. STATISTICAL - Confidence: 6.0
**Source:** video_01_claims_test.json | **Credibility:** DATA | **Relevance:** DIRECT

**Claim:** The basic OB strategy (1:2 RR, 43% WR) grew a $10,000 account by 47% over the 100-trade backtest with a maximum drawdown of 10%

**Test Method:** Can verify via Monte Carlo simulation: 72 triggered trades at 43% WR, 2% risk, 1:2 RR should produce ~47% return; max DD verifiable

**Context:** Speaker showed equity curve results from 100 OB backtest on EURUSD 1H

---

### 10. STATISTICAL - Confidence: 6.0
**Source:** video_02_claims.json | **Credibility:** DATA | **Relevance:** DIRECT

**Claim:** Over 5 years of data and 800 trades across 1,250 days of price action, two OB patterns consistently separate winning from losing order blocks: the Sweep Shift and the Continuation Trap

**Test Method:** Can replicate by classifying OBs into Sweep Shift vs Continuation Trap vs other and comparing hold rates across 5 years

**Context:** Speaker claims verified data from 800 trades identifying two reliable OB patterns

---
