# Q-10.1 / Q-10.2 - Macro Factor Re-test

*Analysis date: 2026-04-17*
*Trade population: 111 XAUUSD batch trades, 2024-04-01 to 2026-03-13*

## Hypothesis (pre-data)

**Q-10.1 (stated before looking at alignment data):** USD strength (USDJPY up-day T-1) should preferentially support SHORT XAUUSD trades and undermine LONG XAUUSD trades. Expected directional-alignment WR advantage ~5-10pp if the macro signal is live. H0 = independence.

**Q-10.2 (stated before looking at calendar overlap):** High-impact news proximity should reduce WR in the -12h..0 window (pre-event risk) and may increase WR in the 0..+2h window (post-release directional follow-through). H0 = independence.

## Data

- Trade file: `knowledge_base_backtest/analysis/unified_trades_v2_20260331.json` (n=111, no `symbol` field — all inferred XAUUSD from price range $2254-$5580)
- Historical OHLCV: `data/historical_2026/` covers 2026-01-02 to 2026-04-13 (NO DXY file; USDJPY used as proxy)
- Economic calendar: `data/economic_calendar.csv`, n=31 HIGH events, range 2026-04-01 to 2026-05-27

### Data gaps

1. **No DXY feed.** Neither `data/historical_2026/` nor `data/` contains a DXY time series. Q-10.1 falls back to USDJPY proxy with stated correlation caveat.
2. **No trade `symbol` field.** The 111 trades were inferred as XAUUSD by price level ($2254-$5580 — far above any other instrument's range). If the batch is ever extended to include non-XAUUSD trades, this inference breaks.
3. **Calendar/trade date mismatch.** Calendar starts 2026-04-01, trade data ends 2026-03-13. **Zero overlap.** This kills Q-10.2 until a back-dated calendar feed is obtained.
4. **USDJPY proxy available window.** USDJPY D1 starts 2026-01-02, so only trades after that date have a T-1 bar. n_trades with USDJPY T-1 available = **28** (out of 111). Skipped: 82 ({'trade_before_USDJPY_data_start': 81, 'no_T-2_bar_for_return': 1}).

## Q-10.1 DXY-gold (USDJPY proxy)

### Proxy justification

DXY is approximately 57.6% EUR, 13.6% JPY, 11.9% GBP, 9.1% CAD, 4.2% SEK, 3.6% CHF. USDJPY alone captures only ~14% of the DXY basket directly, but the empirical correlation between USDJPY daily returns and DXY daily returns runs ~0.70-0.80 in most years because JPY is highly sensitive to US yields (the same macro driver that moves DXY). We do NOT have DXY data in this repo to measure the correlation directly; we report it as a literature-based assumption and verify internal consistency against a synthetic basket (0.5 USDJPY + 0.5 inverse GBPUSD) computed from available data.

- USDJPY vs synthetic USD-basket (0.5 USDJPY + 0.5 inv-GBPUSD) daily-return correlation over 2026-01-02..2026-04-13: **r = 0.913** (n=71 days). 
- Interpretation: USDJPY explains most of the variance of the synthetic basket, which is consistent with the literature claim that USDJPY tracks DXY. Proxy is defensible but imperfect; EUR weight (the largest DXY component) is unobserved here.

### Results table

| USD_class (USDJPY T-1 daily return) | n | wins | WR | avg R |
|---|---|---|---|---|
| USD_up (ret >+0.1%) | 11 | 6 | 0.545 | 0.243 |
| USD_down (ret <-0.1%) | 7 | 7 | 1.000 | 0.281 |
| USD_flat (ret in [-0.1%,+0.1%]) | 10 | 4 | 0.400 | -0.074 |

### Directional alignment test

Aligned = (USD_up & SHORT gold) or (USD_down & LONG gold). Mis-aligned = opposite. USD_flat trades excluded from this 2x2.

| Group | wins | losses | WR |
|---|---|---|---|
| Aligned | 7 | 1 | 0.875 |
| Mis-aligned | 6 | 4 | 0.600 |
| Flat (excluded) | 4 | 6 | - |

- **Fisher's exact p = 0.314** (chi^2 = 1.675, chi^2 p = 0.196).

### Recommendation (Q-10.1)

- Verdict: **INCONCLUSIVE / NEEDS MORE DATA** - effect size is large (>=10pp) but sample too small to reject H0. Do not kill; acquire DXY feed + extend batch window and re-test.. Aligned WR - Misaligned WR = 27.500pp (n_aligned=8, n_mis=10, n_total with proxy = 28).

## Q-10.2 Economic calendar

### Calendar data coverage

- File: `data/economic_calendar.csv`, 31 HIGH-impact events listed.
- Calendar date range: **2026-04-01 to 2026-05-27**.
- Trade date range: 2024-04-01 to 2026-03-13.
- **Trades inside calendar window: 0**.
- **Calendar events inside trade window: 0**.

### Results / data-gap declaration

**DATA GAP — analysis stopped before computing statistics.**

Economic calendar covers 2026-04-01..2026-05-27, trade data ends 2026-03-13. Trades within calendar window = 0. Insufficient overlap to perform legitimate event-proximity analysis.

The calendar begins 2026-04-01 and the batch ends 2026-03-13, so there is no historical trade overlapping any listed high-impact event. Running a news-proximity analysis against zero events would fabricate structure where none exists in the data.

### Recommendation (Q-10.2)

- Verdict: **NEEDS MORE DATA**. The current calendar file was forward-populated (Apr-May 2026) and does not cover the historical batch. Acquire a back-dated ForexFactory or Econoday HIGH-impact feed for 2024-04 through 2026-03, then re-run this script — it is data-driven and will produce a legitimate result the moment the input covers the window.

## Overall recommendations

- **Q-10.1 (USD proxy):** **INCONCLUSIVE / NEEDS MORE DATA** - effect size is large (>=10pp) but sample too small to reject H0. Do not kill; acquire DXY feed + extend batch window and re-test.. Effect size = 27.500pp.
- **Q-10.2 (calendar):** **DATA GAP**. Do not re-kill and do not promote. The prior 'kill' verdict on this hypothesis during Phase 1-2 was reached with a confounded trading system; re-examination requires back-dated high-impact calendar data that covers the batch window.

### Data acquisitions needed to properly run these tests

1. **DXY (USD Index) daily OHLCV** — e.g. `DXY_D1.csv` exported from MT5 (`mt5_real.copy_rates_range('DXY', TIMEFRAME_D1, ...)`), or ICE/Bloomberg feed. Minimum 2024-04-01 to present to cover the full batch window. Current USDJPY proxy captures ~one DXY component out of six.
2. **Back-dated HIGH-impact macro calendar 2024-04 through 2026-03** — ForexFactory CSV export or Econoday dump. Schema needed: `date, time_utc, event, impact, currency` (schema already matches current `data/economic_calendar.csv`). Once loaded, this script runs unchanged.
3. **Symbol tag on trade records.** Today's inference (all XAUUSD by price magnitude) will silently break the moment non-XAUUSD trades enter the batch. Add an explicit `symbol` field at ingest.
4. **Optional: EUR/USD and USD/CAD D1** to build a better DXY-approximation basket (weighted 0.576 EUR + 0.136 JPY + 0.119 GBP + 0.091 CAD + 0.078 misc) if a true DXY feed is not obtainable.

## Caveats

- **Q-10.1 proxy quality.** USDJPY-to-basket r = 0.913 on 2026-01 to 2026-04 window (n=71 days). JPY-only captures ~14% of DXY; a strong EUR move that is not reflected in USDJPY could be missed. Any positive Q-10.1 signal should be re-validated against true DXY before promotion.
- **Q-10.1 sample size.** Only 28 of 111 trades have a USDJPY T-1 bar (the rest predate the 2026-01-02 historical data start). Even a real alignment effect may not reach significance at this n.
- **Q-10.2 calendar sparsity.** 32-line calendar, forward-populated, impact=HIGH only. No medium-impact events, no central-bank speeches outside the listed ones, no earnings. Even if the window did overlap, the event list is probably incomplete.
- **Look-ahead hygiene.** Q-10.1 uses USDJPY return on T-1 (the trading day strictly before the trade date). D1 bars in MT5 close at 00:00 server time, so the T-1 close is knowable at the open of day T. No look-ahead.

## Next steps

1. Acquire DXY D1 feed (MT5 export is the zero-cost path). Re-run `q_10_macro.py` with `HIST_DIR / 'DXY_D1.csv'` instead of USDJPY; the code path is already structured as a drop-in swap.
2. Acquire back-dated ForexFactory HIGH-impact CSV for 2024-04 through 2026-03. Append to `data/economic_calendar.csv`. Re-run `q_10_macro.py`; Q-10.2 branch will auto-execute the event-proximity binning (code present but behind the overlap guard).
3. If Q-10.1 DXY result shows a >=5pp alignment effect at p<0.05, promote to the proximity shadow logger as a new DXY-alignment gate (shadow-only, n=30 trades before any live gate).
4. If Q-10.1 DXY result shows no effect at n>=60, **kill the hypothesis for real** — the Phase 1-2 kill was confounded by prompt bugs; a re-test against a clean trading system validates the kill.
