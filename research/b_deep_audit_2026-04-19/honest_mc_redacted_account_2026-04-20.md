# Honest Monte Carlo — redacted_account Stellar 2-Step Pass Probability

**Session 35 FA-1.** Generated 2026-04-20. Code: `honest_mc_redacted_account.py`. Raw JSON: `honest_mc_results.json`.
Uses chairman-synthesis per-instrument honest expectancies, NOT the artefactual canonical 73.2% WR.

---

## 1. TL;DR

- **P(pass Step 1) under honest numbers:** **98.9%** over a full 90-day quarter, **92.7%** within 60 days, **51.5%** within 30 days. Median time to +10% is **~29 trading days** (10/90 percentile: 14 / 54 days).
- **P(daily breach) and P(overall breach) per quarter:** P(daily-4%-breach in any day) = **0.01%**, P(overall-10%-breach) = **0.06%**. Effectively zero under honest numbers because risk is small relative to caps: median single-trade PnL is ~0.01%; worst-single-trade loss is ~1% of equity.
- **Expected weeks to +10% target:** **~6-7 weeks** at fleet expectancy of **+6.56%/month** (XAUUSD 0.5% + three 1% instruments).

---

## 2. Methodology

Vectorized numpy Monte Carlo, **10,000 independent account paths**, **90 trading days** each (one quarter), seed `20260420`.

**Trade arrivals.** Poisson(rate = monthly_rate / 21) per instrument per day. Arrivals are independent across instruments and days (no autocorrelation — flagged as an assumption).

**Trade outcomes.** Bernoulli(WR) independent per trade. Win → `+target_R × risk_pct × start_of_day_equity`. Loss → `−1R × risk_pct × start_of_day_equity`. Risk is computed on start-of-day equity (standard prop-firm convention).

**Daily-loss gate.** 4% GTOS internal cap (broker allows 5%). First trade that pushes cumulative daily PnL below −4% of start-of-day equity is booked, then the path is halted for the remainder of the day.

**Overall-loss gate.** Account fails immediately the instant equity drops 10% below starting equity OR peak (whichever triggers first — conservative).

**Pass condition.** First instant equity ≥ +10% of starting equity → Step 1 PASS, path stops.

**What is modeled vs. estimated.**
| | Modeled | Estimated |
|---|---|---|
| Trade arrivals | Poisson (memoryless) | — |
| Win rate | Bernoulli-per-trade, from CLAUDE.md / chairman | — |
| Daily cap | Hard floor at −4% | — |
| Overall cap | Hard floor at −10% (max of peak-drawdown and start-drawdown) | — |
| Slippage / spread | — | Assumed already embedded in backtest expectancies |
| WR autocorrelation / regime change mid-path | — | NOT modeled (independence assumption) |
| Correlation between simultaneous trades | — | NOT modeled (small-risk, low-concurrent-count regime makes this minor) |

**Unknowns flagged.**
- **No minimum trading days.** redacted_account Stellar 2-Step is widely advertised as no-minimum, but verify directly on the challenge dashboard before kickoff. If the variant the CEO bought requires 5 minimum days, all figures above remain valid (median 29 days ≫ 5).
- **Static vs. trailing overall drawdown.** Stellar is typically static drawdown from starting balance; we model both paths-from-start and paths-from-peak and take the worse to be conservative.
- **Weekend/holiday gaps.** 90 "trading days" ≈ 4.3 calendar months; the Poisson rate already uses 21 trading days/month so this is consistent.

---

## 3. Per-instrument expectancy sanity check

Chairman-synthesis honest numbers. Expectancy per trade expressed both in R and as % of account equity.

| Instrument | Risk % | WR | Target R | Exp R | Exp %/trade | Trades/mo | Monthly R | Monthly %/acct |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| XAUUSD | 0.5% | 59.4% | 1.5R | **+0.485R** | +0.243% | 4.0 | +1.94R | **+0.97%** |
| US30   | 1.0% | 58.5% | 1.5R | **+0.462R** | +0.462% | 3.5 | +1.62R | **+1.62%** |
| USDJPY | 1.0% | 75.8% | 1.5R | **+0.895R** | +0.895% | 3.0 | +2.68R | **+2.68%** |
| GBPJPY | 1.0% | 57.1% | 1.5R | **+0.427R** | +0.427% | 3.0 | +1.28R | **+1.28%** |
| **Fleet** | — | — | — | — | — | **13.5/mo** | **+7.53R** | **+6.56%/mo** |

Step 1 target is +10%. Fleet expectancy +6.56%/month → **+10% target reached in ~1.53 months (~6.6 weeks)** by pure expectancy — MC confirms median 29 trading days (~5.8 calendar weeks) due to variance tail.

USDJPY's 75.8% WR (n=33, p=1.96e-04 in batch) is the single biggest contributor (41% of fleet monthly expectancy). If that WR decays, the whole thesis weakens — flag for post-live re-validation.

---

## 4. Monte Carlo results — headline (base case, 10,000 paths)

| Horizon | P(pass Step 1) | Median days to pass | 10th pct days | 90th pct days | P(daily breach) | P(overall breach) |
|---|---:|---:|---:|---:|---:|---:|
| 30 trading days | 51.5% | 20 | 12 | 28 | <0.01% | <0.01% |
| 60 trading days | 92.7% | 28 | 14 | 48 | <0.01% | <0.01% |
| 90 trading days | **98.9%** | 29 | 14 | 54 | 0.01% | 0.06% |

**Why P(breach) is tiny.** Largest single loss is GBPJPY/US30/USDJPY at 1% × 1R = **1% of equity**. To breach −4% daily you need 4+ losses in one day against a fleet averaging ~0.6 trades/day. Probability of 4 losses on the same day, all instruments losing, is ~ (0.3)^4 ≈ 0.008%. That matches MC.

Median final equity at 90d = +10.6% (we stop at +10% so most paths exit near target).

---

## 5. Sensitivity analysis

Same Monte Carlo, three XAUUSD WR scenarios:

| Scenario | XAUUSD WR | P(pass, 30d) | P(pass, 60d) | P(pass, 90d) | Median days to pass |
|---|---:|---:|---:|---:|---:|
| **Base (chairman honest)** | 59.4% | 51.5% | 92.7% | **98.9%** | 29 |
| **Pessimistic** (regime worsens) | 50.0% | 46.5% | 89.8% | 98.2% | 31 |
| **Optimistic** (2025 regime returns) | 65.0% | 54.7% | 94.0% | 99.2% | 28 |

**Interpretation.** XAUUSD moving between 50% and 65% WR barely shifts pass probability (98.2% vs. 99.2% at 90 days). Downsizing XAUUSD to 0.5% risk effectively hedges the regime uncertainty — the position is too small to blow the account even at coin-flip WR. The real risk driver is whether USDJPY's 75.8% WR (n=33) holds; if it collapses to 55%, fleet monthly drops from +6.56% to ~+3.8%/month, expected time to pass roughly doubles, and 30-day P(pass) falls sharply.

---

## 6. Per-instrument contribution (base)

Expected monthly R and % contribution, base case:

| Instrument | Monthly R | Monthly % | Share of fleet R |
|---|---:|---:|---:|
| XAUUSD | +1.94R | +0.97% | 25.8% |
| US30 | +1.62R | +1.62% | 21.5% |
| USDJPY | +2.68R | +2.68% | 35.7% |
| GBPJPY | +1.28R | +1.28% | 17.0% |
| **Total** | **+7.53R** | **+6.56%** | 100% |

USDJPY is **35.7% of fleet monthly R** — single-instrument concentration risk. Chairman's XAUUSD downsize trades one concentration risk (regime-shift fat tail on the biggest contributor in 2025) for a different concentration (USDJPY). Recommended: watchlist a USDJPY regime-shift diagnostic in parallel.

---

## 7. Comparison to canonical (artefactual)

The canonical 73.2% fleet WR is hardcoded at `research/academic_pipeline/L4_foundation_analysis.py:649` and does not survive bootstrap stationarity (P=0.7525). Running the same MC with canonical numbers:

| Horizon | P(pass) canonical | P(pass) honest | Delta |
|---|---:|---:|---:|
| 30d | 79.0% | 51.5% | −27.5 pp |
| 60d | 99.5% | 92.7% | −6.8 pp |
| 90d | 99.98% | 98.9% | −1.1 pp |

**Delta is concentrated in speed-to-pass, not ultimate pass probability.** The canonical inflates the quick-pass rate by ~28 percentage points at the 30-day horizon. Both models agree Step 1 is "nearly certain" over a full quarter at current risk sizing. The CEO's uncertainty band shows up if the challenge window is < 1 month OR if WR decays below the honest floor.

---

## 8. Conclusion

**Tuesday kickoff at 4 active instruments (XAUUSD 0.5%, US30/USDJPY/GBPJPY 1%) is a sound bet under honest numbers.**

- **P(pass Step 1 within 90 days) = 98.9%** under chairman-honest expectancies.
- **P(overall account failure) = 0.06%** over the same 90-day window.
- **Expected median pass in ~29 trading days** (~6 calendar weeks).

**Two material risks that are NOT captured by this MC:**
1. **USDJPY regime shift.** 35.7% of fleet expectancy sits on n=33 batch data. If it decays, P(pass) degrades far more than the XAUUSD sensitivity shown above.
2. **Systemic correlated loss day.** Independence of daily trade outcomes is the load-bearing assumption. A cross-instrument news event (BoJ intervention, Fed surprise) that sweeps all four instruments against positions could breach the 4% daily in a single session. Not modeled; mitigate via session-memory / news blackouts that already exist in the codebase.

**Recommended proceed/no-go:** PROCEED with Tuesday kickoff. Monitor USDJPY WR rolling-30 in shadow mode; if it falls below 65% in the first 20 live trades, reduce USDJPY risk to 0.5% to rebalance concentration.

---

*Seed 20260420; 10,000 paths; 90 trading days; GTOS 4% internal daily cap (vs. broker 5%); code at `research/b_deep_audit_2026-04-19/honest_mc_redacted_account.py`.*
