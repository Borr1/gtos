# REPLAY vs BATCH COMPARISON
==================================================

Dates replayed: 64
Candles evaluated: 1102 (with session memory)
API calls: 941
API cost: $17.66

## OVERALL
  Batch:  0 trades, 0% WR, +0R total, 0R exp
  Replay: 36 trades, 52.8% WR, +12.07R total, 0.34R exp

## TRADE-BY-TRADE DIFF (same dates)
  Both took same trade, same outcome: 0
  Both took same trade, different outcome: 0
  Batch traded, replay didn't: 0 (session memory caused skip?)
  Replay traded, batch didn't: 36 (session memory found opportunity?)

### Differences:
  2025-04-17 ny: replay traded (LOSS), batch DID NOT trade
  2025-05-05 london: replay traded (WIN), batch DID NOT trade
  2025-06-10 ny: replay traded (LOSS), batch DID NOT trade
  2025-06-26 ny: replay traded (LOSS), batch DID NOT trade
  2025-09-16 london: replay traded (WIN), batch DID NOT trade
  2025-09-17 ny: replay traded (LOSS), batch DID NOT trade
  2025-09-18 ny: replay traded (LOSS), batch DID NOT trade
  2025-09-25 london: replay traded (LOSS), batch DID NOT trade
  2025-10-03 ny: replay traded (WIN), batch DID NOT trade
  2025-10-07 ny: replay traded (WIN), batch DID NOT trade
  2025-10-08 london: replay traded (WIN), batch DID NOT trade
  2025-10-09 london: replay traded (LOSS), batch DID NOT trade
  2025-10-09 ny: replay traded (LOSS), batch DID NOT trade
  2025-10-14 london: replay traded (LOSS), batch DID NOT trade
  2025-10-16 ny: replay traded (WIN), batch DID NOT trade
  2025-12-17 ny: replay traded (WIN), batch DID NOT trade
  2025-12-18 ny: replay traded (WIN), batch DID NOT trade
  2025-12-19 ny: replay traded (WIN), batch DID NOT trade
  2025-12-23 ny: replay traded (WIN), batch DID NOT trade
  2025-12-26 london: replay traded (WIN), batch DID NOT trade
  2025-12-30 ny: replay traded (LOSS), batch DID NOT trade
  2026-01-05 london: replay traded (WIN), batch DID NOT trade
  2026-01-06 london: replay traded (WIN), batch DID NOT trade
  2026-01-09 london: replay traded (WIN), batch DID NOT trade
  2026-01-09 ny: replay traded (WIN), batch DID NOT trade
  2026-01-13 london: replay traded (LOSS), batch DID NOT trade
  2026-01-13 ny: replay traded (WIN), batch DID NOT trade
  2026-01-15 london: replay traded (WIN), batch DID NOT trade
  2026-01-16 london: replay traded (LOSS), batch DID NOT trade
  2026-01-19 london: replay traded (BREAKEVEN), batch DID NOT trade
  2026-01-19 ny: replay traded (WIN), batch DID NOT trade
  2026-01-21 london: replay traded (LOSS), batch DID NOT trade
  2026-01-21 ny: replay traded (LOSS), batch DID NOT trade
  2026-01-29 london: replay traded (LOSS), batch DID NOT trade
  2026-03-06 ny: replay traded (WIN), batch DID NOT trade
  2026-03-12 london: replay traded (LOSS), batch DID NOT trade

## SESSION MEMORY ANALYSIS
  Trades where session memory had context: 36
  Average memory entries at CANDIDATE time: 4.4

## CONFIDENCE SCORE COMPARISON
  Batch avg confidence: 0.0
  Replay avg confidence: 78.3
  Replay confidence std dev: 2.4

## FRAMEWORK BREAKDOWN (Replay)
  breaker_retest: 1 trades, 0.0% WR, -1.0R exp
  ob_retest: 35 trades, 54.3% WR, 0.37R exp
