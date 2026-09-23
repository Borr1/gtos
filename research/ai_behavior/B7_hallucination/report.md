# B7 — Hallucination Rate Systematic Measurement

Harness: `B7-v1` · tolerance_ticks: 5 · records scanned: 1390 · records with classifications: 316

## Hallucination rate matrix (per instrument)

| Instrument | n_evals | n_prices | accurate% | hallucinated% | misattributed% |
|---|---:|---:|---:|---:|---:|
| GBPJPY | 73 | 356 | 83.1% | 10.7% | 6.2% |
| GBPUSD | 52 | 265 | 95.8% | 2.3% | 1.9% |
| US30_cash | 49 | 265 | 73.6% | 23.4% | 3.0% |
| USDJPY | 111 | 492 | 95.1% | 4.3% | 0.6% |
| XAUUSD | 31 | 153 | 86.3% | 13.1% | 0.7% |

## Hallucination rate matrix (instrument × half-year)

| Instrument | Period | n_evals | n_prices | accurate% | hallucinated% | misattributed% |
|---|---|---:|---:|---:|---:|---:|
| GBPJPY | H1-2026 | 73 | 356 | 83.1% | 10.7% | 6.2% |
| GBPUSD | H1-2026 | 52 | 265 | 95.8% | 2.3% | 1.9% |
| US30_cash | H1-2026 | 49 | 265 | 73.6% | 23.4% | 3.0% |
| USDJPY | H1-2026 | 111 | 492 | 95.1% | 4.3% | 0.6% |
| XAUUSD | H1-2026 | 31 | 153 | 86.3% | 13.1% | 0.7% |

## Hallucination rate matrix (instrument × month)

| Instrument | Month | n_evals | n_prices | accurate% | hallucinated% | misattributed% |
|---|---|---:|---:|---:|---:|---:|
| GBPJPY | 2026-04 | 73 | 356 | 83.1% | 10.7% | 6.2% |
| GBPUSD | 2026-04 | 52 | 265 | 95.8% | 2.3% | 1.9% |
| US30_cash | 2026-04 | 49 | 265 | 73.6% | 23.4% | 3.0% |
| USDJPY | 2026-04 | 111 | 492 | 95.1% | 4.3% | 0.6% |
| XAUUSD | 2026-04 | 31 | 153 | 86.3% | 13.1% | 0.7% |

## Hallucination rate matrix (instrument × framework)

| Instrument | Framework | n_evals | n_prices | accurate% | hallucinated% | misattributed% |
|---|---|---:|---:|---:|---:|---:|
| GBPJPY | none | 34 | 45 | 71.1% | 28.9% | 0.0% |
| GBPJPY | ob_retest | 39 | 311 | 84.9% | 8.0% | 7.1% |
| GBPUSD | none | 20 | 35 | 97.1% | 2.9% | 0.0% |
| GBPUSD | ob_retest | 32 | 230 | 95.7% | 2.2% | 2.2% |
| US30_cash | none | 19 | 43 | 86.0% | 14.0% | 0.0% |
| US30_cash | ob_retest | 30 | 222 | 71.2% | 25.2% | 3.6% |
| USDJPY | none | 60 | 126 | 90.5% | 9.5% | 0.0% |
| USDJPY | ob_retest | 51 | 366 | 96.7% | 2.5% | 0.8% |
| XAUUSD | none | 11 | 26 | 84.6% | 15.4% | 0.0% |
| XAUUSD | ob_retest | 20 | 127 | 86.6% | 12.6% | 0.8% |

## Hallucination rate by role (which price field decays the most)

| Role | n_prices | accurate% | hallucinated% | misattributed% |
|---|---:|---:|---:|---:|
| breaker_high | 9 | 44.4% | 55.6% | 0.0% |
| breaker_low | 9 | 55.6% | 44.4% | 0.0% |
| take_profit | 148 | 61.5% | 38.5% | 0.0% |
| current_price | 131 | 78.6% | 20.6% | 0.8% |
| stop_loss | 148 | 83.1% | 16.9% | 0.0% |
| sweep_price | 140 | 77.1% | 9.3% | 13.6% |
| ob_mid | 145 | 80.7% | 7.6% | 11.7% |
| entry_price | 148 | 96.6% | 3.4% | 0.0% |
| equilibrium | 4 | 100.0% | 0.0% | 0.0% |
| fvg_high | 16 | 100.0% | 0.0% | 0.0% |
| fvg_low | 16 | 100.0% | 0.0% | 0.0% |
| ob_high | 235 | 99.6% | 0.0% | 0.4% |
| ob_low | 235 | 99.6% | 0.0% | 0.4% |
| protected_swing | 147 | 100.0% | 0.0% | 0.0% |

## Strategic verdict

H1→H2 hallucination delta: **NOT COMPUTABLE** — one or both halves have no classifications. Coverage gap (live_evaluations spans only April 2026; trade_records is April-only). Can be filled later by running on H1-2026 simulator/replay outputs.

Most-hallucinated price field: **breaker_high** (55.6% of 9 prices)

Reasoning:

- Top hallucination instrument: **US30_cash** at 23.4% (n_prices=265).
- Lowest hallucination instrument: **GBPUSD** at 2.3% (n_prices=265).
- Coverage caveat: trade_records dataset is April-2026-only (CANDIDATEs); live_evaluations dataset is also April-2026 only. The H1-2026 baseline is missing on disk in this codebase. The number is informational at this stage; K54 handoff should add a backfill task to extract the H1-2026 evaluation stream (from logs/agent_*.log or batch_sessions if available).

## Appendix — methodology summary

- See `src/research_infra/docs/B7_hallucination.md` for the full methodology, tolerance choice, classification rules, and K54 handoff.
- Inputs: `knowledge_base/trade_records/{SYMBOL}/*.json` (precise: paired MSO+AI), `knowledge_base/live_evaluations/{SYMBOL}/*.jsonl` (coarse: text + OHLCV), `data/historical_2026/{SYMBOL}_H1.csv` (OHLCV stand-in).
- Tolerance default: 5 ticks (per-instrument, see TICK_SIZE table in the module).
- Classification: ACCURATE (same role match within tol), MISATTRIBUTED (price exists in MSO but at different role), HALLUCINATED (no MSO match).
- Out of scope: re-running AI on historical CANDs (Phase 2 A4); modifying production code; proposing system changes (K54 handoff).
