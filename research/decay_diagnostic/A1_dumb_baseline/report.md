# A1 — Full Historical Dumb-Baseline Replay

Harness version: `A1-v1` — mechanical 80%-retrace OB-pullback baseline. No AI calls; pure OHLCV replay.

## Coverage

| Symbol | CANDs replayed | Mechanical fired | Matched (AI+mech R) |
|---|---:|---:|---:|
| GBPJPY | 81 | 43 | 19 |
| GBPUSD | 53 | 32 | 2 |
| NZDUSD | 17 | 11 | 8 |
| US30_cash | 67 | 43 | 14 |
| USDJPY | 76 | 51 | 14 |
| XAUUSD | 133 | 40 | 22 |

## Per-month per-instrument

| Month | Symbol | CAND n | AI n | AI mean R | AI WR | Mech n | Mech mean R | Mech WR | Matched | Gap (AI-Mech) R |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2024-03 | GBPUSD | 1 | 1 | -1.000 | 0.0% | 0 | — | — | 0 | — |
| 2024-04 | XAUUSD | 7 | 7 | +0.340 | 71.4% | 0 | — | — | 0 | — |
| 2024-05 | GBPUSD | 1 | 1 | -1.000 | 0.0% | 0 | — | — | 0 | — |
| 2024-06 | GBPUSD | 1 | 1 | -1.000 | 0.0% | 0 | — | — | 0 | — |
| 2024-06 | XAUUSD | 1 | 1 | +0.920 | 100.0% | 0 | — | — | 0 | — |
| 2024-07 | XAUUSD | 5 | 5 | +1.232 | 100.0% | 0 | — | — | 0 | — |
| 2024-08 | XAUUSD | 2 | 2 | +0.455 | 100.0% | 0 | — | — | 0 | — |
| 2024-09 | XAUUSD | 3 | 3 | -0.173 | 33.3% | 0 | — | — | 0 | — |
| 2024-10 | XAUUSD | 2 | 2 | -1.000 | 0.0% | 0 | — | — | 0 | — |
| 2024-12 | XAUUSD | 4 | 4 | +0.938 | 75.0% | 0 | — | — | 0 | — |
| 2025-01 | XAUUSD | 8 | 8 | +0.535 | 62.5% | 0 | — | — | 0 | — |
| 2025-02 | GBPUSD | 2 | 2 | +0.215 | 50.0% | 0 | — | — | 0 | — |
| 2025-02 | XAUUSD | 15 | 15 | -0.071 | 66.7% | 0 | — | — | 0 | — |
| 2025-03 | GBPUSD | 7 | 7 | +1.389 | 100.0% | 0 | — | — | 0 | — |
| 2025-03 | XAUUSD | 11 | 11 | +0.227 | 72.7% | 0 | — | — | 0 | — |
| 2025-04 | XAUUSD | 2 | 2 | +1.990 | 100.0% | 0 | — | — | 0 | — |
| 2025-05 | GBPUSD | 1 | 1 | +1.810 | 100.0% | 0 | — | — | 0 | — |
| 2025-05 | XAUUSD | 1 | 1 | +2.130 | 100.0% | 0 | — | — | 0 | — |
| 2025-06 | GBPUSD | 5 | 5 | +0.740 | 80.0% | 0 | — | — | 0 | — |
| 2025-06 | XAUUSD | 4 | 4 | -0.092 | 50.0% | 0 | — | — | 0 | — |
| 2025-07 | XAUUSD | 1 | 1 | +0.750 | 100.0% | 0 | — | — | 0 | — |
| 2025-08 | XAUUSD | 3 | 3 | +1.137 | 100.0% | 0 | — | — | 0 | — |
| 2025-09 | XAUUSD | 3 | 3 | -0.813 | 0.0% | 0 | — | — | 0 | — |
| 2025-10 | GBPJPY | 6 | 6 | +1.125 | 83.3% | 0 | — | — | 0 | — |
| 2025-10 | US30_cash | 9 | 9 | +0.349 | 77.8% | 0 | — | — | 0 | — |
| 2025-10 | USDJPY | 6 | 6 | +0.828 | 100.0% | 0 | — | — | 0 | — |
| 2025-10 | XAUUSD | 6 | 6 | +0.070 | 66.7% | 0 | — | — | 0 | — |
| 2025-11 | GBPJPY | 4 | 4 | +0.170 | 75.0% | 0 | — | — | 0 | — |
| 2025-11 | NZDUSD | 1 | 1 | -1.000 | 0.0% | 0 | — | — | 0 | — |
| 2025-11 | US30_cash | 2 | 2 | -0.125 | 50.0% | 0 | — | — | 0 | — |
| 2025-11 | USDJPY | 5 | 5 | -0.050 | 40.0% | 0 | — | — | 0 | — |
| 2025-12 | GBPJPY | 10 | 10 | +0.182 | 60.0% | 0 | — | — | 0 | — |
| 2025-12 | GBPUSD | 3 | 3 | +1.067 | 66.7% | 0 | — | — | 0 | — |
| 2025-12 | NZDUSD | 5 | 5 | -0.440 | 20.0% | 0 | — | — | 0 | — |
| 2025-12 | US30_cash | 12 | 12 | +0.677 | 66.7% | 0 | — | — | 0 | — |
| 2025-12 | USDJPY | 4 | 4 | +0.443 | 75.0% | 0 | — | — | 0 | — |
| 2025-12 | XAUUSD | 10 | 10 | +0.582 | 70.0% | 0 | — | — | 0 | — |
| 2026-01 | GBPJPY | 10 | 10 | -0.182 | 40.0% | 8 | +0.272 | 62.5% | 8 | -0.571 |
| 2026-01 | GBPUSD | 2 | 2 | -0.010 | 50.0% | 2 | +1.500 | 100.0% | 2 | -1.510 |
| 2026-01 | NZDUSD | 5 | 5 | -0.274 | 20.0% | 4 | +0.034 | 75.0% | 4 | -0.321 |
| 2026-01 | US30_cash | 8 | 8 | +1.021 | 75.0% | 6 | -0.583 | 16.7% | 6 | +1.918 |
| 2026-01 | USDJPY | 7 | 7 | +0.611 | 100.0% | 5 | -0.260 | 20.0% | 5 | +0.832 |
| 2026-01 | XAUUSD | 21 | 21 | +0.041 | 57.1% | 15 | +0.286 | 53.3% | 15 | -0.078 |
| 2026-02 | GBPJPY | 6 | 6 | +0.690 | 83.3% | 5 | +1.000 | 80.0% | 5 | -0.594 |
| 2026-02 | GBPUSD | 2 | 2 | +0.990 | 100.0% | 0 | — | — | 0 | — |
| 2026-02 | US30_cash | 6 | 6 | +0.225 | 50.0% | 4 | -0.265 | 25.0% | 4 | +0.102 |
| 2026-02 | USDJPY | 5 | 5 | +0.920 | 80.0% | 4 | +0.024 | 50.0% | 4 | +0.526 |
| 2026-02 | XAUUSD | 7 | 7 | +0.423 | 71.4% | 5 | +0.372 | 60.0% | 5 | -0.480 |
| 2026-03 | GBPJPY | 6 | 6 | -0.405 | 50.0% | 6 | -0.544 | 33.3% | 6 | +0.140 |
| 2026-03 | NZDUSD | 6 | 6 | +0.073 | 66.7% | 4 | -0.005 | 50.0% | 4 | +0.027 |
| 2026-03 | US30_cash | 4 | 4 | -0.708 | 0.0% | 4 | +0.883 | 75.0% | 4 | -1.591 |
| 2026-03 | USDJPY | 6 | 6 | +0.367 | 50.0% | 5 | +0.500 | 60.0% | 5 | +0.140 |
| 2026-03 | XAUUSD | 5 | 5 | +0.282 | 60.0% | 2 | -1.000 | 0.0% | 2 | +0.615 |
| 2026-04 | GBPJPY | 39 | 0 | — | — | 1 | +1.500 | 100.0% | 0 | — |
| 2026-04 | GBPUSD | 28 | 0 | — | — | 1 | +1.500 | 100.0% | 0 | — |
| 2026-04 | US30_cash | 26 | 0 | — | — | 1 | +1.500 | 100.0% | 0 | — |
| 2026-04 | USDJPY | 43 | 0 | — | — | 19 | +1.500 | 100.0% | 0 | — |
| 2026-04 | XAUUSD | 12 | 0 | — | — | 2 | +1.500 | 100.0% | 0 | — |

## H1 vs H2 — matched-pair comparison

| Half | n | AI mean R | AI WR | Mech mean R | Mech WR | Gap (AI-Mech) R | Gap WR pp |
|---|---:|---:|---:|---:|---:|---:|---:|
| H1 | 58 | +0.232 | 58.6% | +0.184 | 51.7% | +0.048 | +6.90pp |
| H2 | 21 | -0.131 | 42.9% | +0.036 | 47.6% | -0.166 | -4.76pp |

## Strategic verdict

- AI vs mechanical gap H1-2026: +6.90pp
- AI vs mechanical gap H2-2026: -4.76pp
- Gap delta H1→H2: -11.66pp
- Gap stability across months: +42.29pp (stddev)

Diagnosis: SYSTEM_DECAY
Reasoning: AI-vs-mechanical gap eroded H1->H2 (WR pp gap: +6.9 -> -4.8; delta -11.7pp). Mechanical mean R: +0.184 -> +0.036. AI lost selectivity that the market continues to reward.

## Caveats

* This replay tests only the OB-pullback canonical rule. Multi-framework   comparisons (`fvg_fill`, `breaker_re_entry`) are out of scope.
* The mechanical arm uses the AI's recorded `direction` so we test the   same setup the AI looked at — we do NOT also opine on whether mechanical   picks a different side.
* Realized AI R is joined per L56/L58 contract `(symbol, candle_close_time,   side)`. CANDs without a recorded R are excluded from the pair-aggregates.
* `INCONCLUSIVE` verdict at low n is a research-discipline guard — do NOT   treat it as a recommendation either way.
