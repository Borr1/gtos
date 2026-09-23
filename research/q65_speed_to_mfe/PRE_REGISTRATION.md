# Q-6.5 Speed-to-MFE Pre-Registration

**Dispatched:** 2026-04-18
**Author:** research sub-agent (B5 / Q-6.5)
**Status:** Hypothesis committed BEFORE any time-to-MFE calculation is performed.

---

## Primary Hypothesis (H1)
Trades that reach an intermediate MFE level quickly have a higher TP-hit rate (or a higher WIN rate, where WIN := `r_multiple > 0` as a fallback if TP-hit is not separately coded) than trades that reach the same MFE level slowly or never reach it.

Operationally, for each (speed_threshold, MFE_level) pair:

- **Fast cohort:** trades whose time-to-MFE-level (in M15 bars after entry) is `<= speed_threshold`.
- **Slow/never cohort:** all other trades (either time-to-MFE > threshold, or MFE never reached before trade close).
- **Primary metric:** `p_TP(fast) - p_TP(slow_or_never)` in percentage points.

## Null Hypothesis (H0)
No difference in TP-hit rate between fast and slow cohorts at any tested (speed_threshold, MFE_level) combination.

## Speed Thresholds
- 3 bars (~45 min on M15)
- 5 bars (~75 min)
- 10 bars (~2.5 h)
- 20 bars (~5 h)

## MFE Levels
- +0.5R
- +1.0R

## Comparison Grid (8 cells)
4 speed thresholds x 2 MFE levels = 8 two-proportion z-tests.

## Sample Thresholds
- n >= 30 per cohort to report a p-value for that cell.
- n >= 100 overall to report any verdict.
- Cells failing either threshold are marked `underpowered` and excluded from the verdict decision.

## Significance
- Raw alpha = 0.05 (two-sided z-test).
- Bonferroni-corrected alpha = 0.05 / 8 = **0.00625** per cell.
- A cell counts as "SIGNIFICANT" only if raw p < 0.00625.

## Verdict Rules (committed before seeing data)
- **SIGNAL FOUND** if at least one cell has raw p < 0.00625 AND effect size >= 10pp AND the direction is "fast > slow" (TP-hit rate higher for fast cohort).
- **NULL** if no cell has raw p < 0.00625.
- **UNDERPOWERED** if >= 4 of 8 cells fail the sample threshold, regardless of p-values elsewhere.
- If at least one cell hits p < 0.00625 but the best direction is reversed ("slow > fast"), report as **REVERSE SIGNAL** — not the pre-registered hypothesis but noted for completeness.

## Outcome Definition
- `TP-hit`: `r_multiple >= 1.0` (stand-in for "trade hit TP", since current system min_rr=1.5 but some legacy trades logged planned_rr between 1.0 and 3.0; we use >=1.0 as the "made it to at least 1R profit" threshold, which is the most comparable across the dataset).
- If a trade has `exit_substate == "CLOSED_TP1"` OR `r_multiple >= 0.9` we treat it as a "TP-hit" to tolerate microscopic slippage on limit fills.
- Primary analysis uses `r_multiple >= 0.9` as the TP-hit proxy. A secondary column reports results under the WIN proxy `r_multiple > 0` for sensitivity.

## Data Sources
- Universe: union of `knowledge_base_backtest/batch_api/*_results.json` (parsed CANDIDATE entries), `knowledge_base_backtest/analysis/unified_trades_v2_20260331.json` (110 XAUUSD trades with entry/SL), `knowledge_base_backtest/analysis/phase1_all_trades_merged.json` (18 XAUUSD trades with r_path), and per-symbol session files (`knowledge_base_backtest/sessions/{SYMBOL}/*_session.json`) for multi-instrument coverage.
- Time-to-MFE reconstruction: scan M15 bars in `data/historical/{SYMBOL}_M15.csv` starting from entry bar exclusive (entry price assumed filled at entry_bar close / limit level at its natural bar) and counting each subsequent M15 bar whose `high` (for LONG) or `low` (for SHORT) crosses the MFE R-level.
- A bar index of 0 means "the first bar AFTER entry crossed the level" — following the session-trade convention (`hold_time_candles` already counts post-entry bars).

## What Bars Qualify?
- Entry bar timestamp taken from `candle_time` (the bar that produced the CANDIDATE decision).
- Entry fill is modelled as a limit fill at `entry_price` — a bar qualifies as the "entry fill bar" only if its high/low range contains `entry_price`.
- Scanning for MFE starts from the FILL bar and includes that bar (because the fill and continuation can occur intra-bar, and the current system's `mfe_r`/`hold_time_candles` counts from fill forward).
- Maximum scan horizon: until `hold_time_candles` exhausted (trade closed) or MFE level reached, whichever first.
- If `hold_time_candles` is missing, we cap scan at 100 M15 bars.
- If MFE level never reached within scan, time-to-MFE = `None` and the trade falls into the "slow/never" cohort.

## Fail-Loud Conditions (do NOT fabricate)
- If a trade has no `entry_price` OR no `stop_loss` OR no `direction`, SKIP with reason "missing parameters".
- If the trade's `candle_time` does not exist in the historical M15 CSV, SKIP with reason "no M15 bar for entry time".
- If the entry_price is never reached within the first 20 bars after `candle_time` (limit never filled), SKIP with reason "limit never filled in window".
- Report the final accepted N alongside skipped counts with reasons.

## Pre-Commit Decision
If SIGNAL FOUND per the rules above, recommend shipping a **shadow logger** (observation-only, no trading impact) that records time-to-+0.5R and time-to-+1.0R per live trade, with a 30-trade observation budget before promoting to live use.

If NULL or UNDERPOWERED, recommend parking the question and moving on.
