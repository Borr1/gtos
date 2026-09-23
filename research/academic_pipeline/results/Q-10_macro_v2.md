# Q-10.1 / Q-10.2 - Macro Factor Re-test (v2 - circularity fix)

*Analysis date: 2026-04-17*
*Trade population: 111 XAUUSD batch trades, 2024-04-01 to 2026-03-13*

## v2 change log

**Wave 1 reviewer issue (Issue 3):** The v1 proxy-sanity-check computed `corr(USDJPY, 0.5*USDJPY + 0.5*inv_GBPUSD) = 0.913`, but USDJPY appears on **both sides** of that correlation. Any non-trivial r is guaranteed by construction, so the v1 number does not measure proxy quality.

**v2 replaces the sanity check with two separate numbers:**

1. `r(USDJPY, inv-GBPUSD)` - the **non-circular** cross-correlation between two independent USD-base daily-return series. This is the real proxy-quality number.
2. `r(USDJPY, 0.5*USDJPY + 0.5*inv-GBPUSD)` - reproduced from v1 and explicitly labelled as circular. Its algebraic identity to the non-circular number is also verified numerically (ensures we understand why the number is large even when proxy quality is weak).

Everything else (Q-10.1 alignment test, Q-10.2 data-gap declaration, seed use) is unchanged from v1.

## Hypothesis (pre-data)

**Q-10.1:** USD strength (USDJPY up-day T-1) should preferentially support SHORT XAUUSD trades and undermine LONG XAUUSD trades. Expected alignment WR advantage ~5-10pp. H0 = independence.

**Q-10.2:** High-impact news proximity should reduce WR in the -12h..0 window and may increase WR in the 0..+2h window. H0 = independence.

## Data

- Trade file: `knowledge_base_backtest/analysis/unified_trades_v2_20260331.json` (n=111, all inferred XAUUSD from price range)
- Historical OHLCV: `data/historical_2026/` covers 2026-01-02 to 2026-04-13 (NO DXY file; USDJPY used as proxy)
- Economic calendar: `data/economic_calendar.csv`, n=31 HIGH events, range 2026-04-01 to 2026-05-27

### Data gaps (unchanged from v1)

1. **No DXY feed.** Q-10.1 falls back to USDJPY proxy.
2. **No trade `symbol` field.** All 111 trades inferred as XAUUSD by price level.
3. **Calendar/trade date mismatch.** Calendar 2026-04-01+, trades end 2026-03-13.
4. **USDJPY proxy available window.** n with T-1 bar = **28** of 111.

## Q-10.1 DXY-gold (USDJPY proxy)

### Proxy quality - non-circular analysis (v2)

DXY is approximately 57.6% EUR, 13.6% JPY, 11.9% GBP, 9.1% CAD, 4.2% SEK, 3.6% CHF. Only USDJPY (JPY, 13.6%) and inverse-GBPUSD (GBP, 11.9%) are available in the local historical data. No EUR pair. No CAD pair. JPY+GBP together capture ~25.5% of DXY directly. Good proxy quality would show that these two USD-base pairs co-move, even without a third anchor, because both respond to broad USD factors that also drive DXY.

#### Non-circular cross-pair correlation

- **r(USDJPY daily return, inverse-GBPUSD daily return) = 0.633** (n=71 days, 2026-01-02 to 2026-04-13).

USDJPY is on the left side only; inverse-GBPUSD is on the right side only. No shared variable. This number *does* measure proxy quality.

- Proxy quality: **STRONG - two independent USD-base pairs move together**.

#### v1 circular number (reproduced for audit)

- `r(USDJPY, 0.5*USDJPY + 0.5*inv-GBPUSD) = 0.913` (v1 number reproduced).
- Algebraic identity prediction from r_off above: **0.913** (match vs observed: True).

The circular number is inflated by the USDJPY-on-both-sides construction. Even if r_off were exactly 0, the circular number would still be approximately sd_USDJPY / sqrt(sd_USDJPY^2 + sd_invGBPUSD^2) = 0.740 by construction. Do not interpret the circular number as a measure of proxy quality.

### Per-class WR

| USD_class (USDJPY T-1 daily return) | n | wins | WR | avg R |
|---|---|---|---|---|
| USD_up (ret >+0.1%) | 11 | 6 | 0.545 | 0.243 |
| USD_down (ret <-0.1%) | 7 | 7 | 1.000 | 0.281 |
| USD_flat (ret in [-0.1%,+0.1%]) | 10 | 4 | 0.400 | -0.074 |

### Directional alignment test

Aligned = (USD_up & SHORT gold) or (USD_down & LONG gold). Mis-aligned = opposite.

| Group | wins | losses | WR |
|---|---|---|---|
| Aligned | 7 | 1 | 0.875 |
| Mis-aligned | 6 | 4 | 0.600 |
| Flat (excluded) | 4 | 6 | - |

- **Fisher's exact p = 0.314** (chi^2 = 1.675, chi^2 p = 0.196).

### Recommendation (Q-10.1)

- Verdict: **INCONCLUSIVE / NEEDS MORE DATA** - effect size is large (>=10pp) but sample too small to reject H0.. Aligned WR - Misaligned WR = 27.500pp (n_aligned=8, n_mis=10, n_total with proxy = 28).

## Q-10.2 Economic calendar

### Calendar data coverage

- File: `data/economic_calendar.csv`, 31 HIGH-impact events.
- Calendar date range: **2026-04-01 to 2026-05-27**.
- Trade date range: 2024-04-01 to 2026-03-13.
- **Trades inside calendar window: 0**.

**DATA GAP - analysis stopped before computing statistics.**

Economic calendar covers 2026-04-01..2026-05-27, trade data ends 2026-03-13. Trades within calendar window = 0. Insufficient overlap to perform legitimate event-proximity analysis.

### Recommendation (Q-10.2)

- Verdict: **NEEDS MORE DATA**. Acquire a back-dated ForexFactory HIGH-impact feed for 2024-04 through 2026-03.

## Overall recommendations

- **Q-10.1 (USD proxy):** **INCONCLUSIVE / NEEDS MORE DATA** - effect size is large (>=10pp) but sample too small to reject H0..
- **Q-10.2 (calendar):** **DATA GAP**. Do not re-kill and do not promote.

### Data acquisitions needed

1. **DXY (USD Index) daily OHLCV** - a true DXY feed removes the proxy question entirely.
2. **EUR/USD daily OHLCV** - would raise the non-circular proxy to the ~70% DXY-weight level.
3. **Back-dated HIGH-impact macro calendar 2024-04 through 2026-03** - for Q-10.2.
4. **Symbol tag on trade records.**

## Caveats

- **Q-10.1 proxy quality (v2).** Non-circular r(USDJPY, inv-GBPUSD) = 0.633. This is the number to trust. JPY+GBP together are ~25.5% of DXY weight. A strong EUR move absent in either USDJPY or GBPUSD could be missed entirely.
- **Q-10.1 sample size.** Only 28 of 111 trades have USDJPY T-1.
- **v1 circular number.** The 0.913 reported in v1 is algebraically inflated; do not use it to argue proxy quality. See 'v1 circular number (reproduced for audit)' above.
- **Q-10.2 calendar sparsity.** 32 HIGH events forward-populated, no overlap with trades.
- **Look-ahead hygiene.** USDJPY T-1 close is knowable at open of day T; no look-ahead.

## Next steps (unchanged from v1)

1. Acquire DXY D1 feed; re-run analysis with true DXY rather than USDJPY proxy.
2. Acquire back-dated calendar 2024-04..2026-03; Q-10.2 branch auto-executes.
3. If DXY Q-10.1 shows >=5pp alignment effect at p<0.05, promote to shadow.
4. If DXY Q-10.1 shows no effect at n>=60, kill the hypothesis for real.
