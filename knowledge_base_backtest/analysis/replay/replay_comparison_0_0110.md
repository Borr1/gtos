# REPLAY vs BATCH COMPARISON
==================================================

Dates replayed: 64
Candles evaluated: 1084 (with session memory)
API calls: 930
API cost: $16.95

## OVERALL
  Batch:  0 trades, 0% WR, +0R total, 0R exp
  Replay: 38 trades, 57.9% WR, +18.76R total, 0.49R exp

## TRADE-BY-TRADE DIFF (same dates)
  Both took same trade, same outcome: 0
  Both took same trade, different outcome: 0
  Batch traded, replay didn't: 0 (session memory caused skip?)
  Replay traded, batch didn't: 38 (session memory found opportunity?)

### Differences:
  2025-04-17 ny: replay traded (LOSS), batch DID NOT trade
  2025-05-05 london: replay traded (WIN), batch DID NOT trade
  2025-06-10 london: replay traded (WIN), batch DID NOT trade
  2025-06-10 ny: replay traded (LOSS), batch DID NOT trade
  2025-06-26 ny: replay traded (LOSS), batch DID NOT trade
  2025-09-16 london: replay traded (WIN), batch DID NOT trade
  2025-09-18 ny: replay traded (LOSS), batch DID NOT trade
  2025-09-25 london: replay traded (LOSS), batch DID NOT trade
  2025-09-26 london: replay traded (WIN), batch DID NOT trade
  2025-09-29 london: replay traded (WIN), batch DID NOT trade
  2025-10-01 london: replay traded (WIN), batch DID NOT trade
  2025-10-03 ny: replay traded (WIN), batch DID NOT trade
  2025-10-08 london: replay traded (WIN), batch DID NOT trade
  2025-10-09 london: replay traded (LOSS), batch DID NOT trade
  2025-10-09 ny: replay traded (LOSS), batch DID NOT trade
  2025-10-16 ny: replay traded (WIN), batch DID NOT trade
  2025-12-18 ny: replay traded (WIN), batch DID NOT trade
  2025-12-19 ny: replay traded (WIN), batch DID NOT trade
  2025-12-23 ny: replay traded (WIN), batch DID NOT trade
  2025-12-26 london: replay traded (WIN), batch DID NOT trade
  2025-12-30 ny: replay traded (LOSS), batch DID NOT trade
  2026-01-06 london: replay traded (WIN), batch DID NOT trade
  2026-01-06 ny: replay traded (WIN), batch DID NOT trade
  2026-01-09 london: replay traded (WIN), batch DID NOT trade
  2026-01-09 ny: replay traded (WIN), batch DID NOT trade
  2026-01-13 london: replay traded (LOSS), batch DID NOT trade
  2026-01-13 ny: replay traded (BREAKEVEN), batch DID NOT trade
  2026-01-15 london: replay traded (WIN), batch DID NOT trade
  2026-01-16 london: replay traded (LOSS), batch DID NOT trade
  2026-01-19 london: replay traded (WIN), batch DID NOT trade
  2026-01-19 ny: replay traded (WIN), batch DID NOT trade
  2026-01-21 ny: replay traded (LOSS), batch DID NOT trade
  2026-01-28 london: replay traded (WIN), batch DID NOT trade
  2026-01-29 london: replay traded (LOSS), batch DID NOT trade
  2026-02-05 london: replay traded (LOSS), batch DID NOT trade
  2026-02-05 ny: replay traded (LOSS), batch DID NOT trade
  2026-03-09 london: replay traded (WIN), batch DID NOT trade
  2026-03-12 london: replay traded (LOSS), batch DID NOT trade

## SESSION MEMORY ANALYSIS
  Trades where session memory had context: 38
  Average memory entries at CANDIDATE time: 4.2

## CONFIDENCE SCORE COMPARISON
  Batch avg confidence: 0.0
  Replay avg confidence: 78.4
  Replay confidence std dev: 2.4

## FRAMEWORK BREAKDOWN (Replay)
  breaker_retest: 3 trades, 33.3% WR, 0.58R exp
  ob_retest: 35 trades, 60.0% WR, 0.49R exp
