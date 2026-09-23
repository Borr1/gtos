# REPLAY vs BATCH COMPARISON
==================================================

Dates replayed: 104
Candles evaluated: 2062 (with session memory)
API calls: 250
API cost: $4.51

## OVERALL
  Batch:  0 trades, 0% WR, +0R total, 0R exp
  Replay: 5 trades, 60.0% WR, +2.33R total, 0.47R exp

## TRADE-BY-TRADE DIFF (same dates)
  Both took same trade, same outcome: 0
  Both took same trade, different outcome: 0
  Batch traded, replay didn't: 0 (session memory caused skip?)
  Replay traded, batch didn't: 5 (session memory found opportunity?)

### Differences:
  2024-05-31 ny: replay traded (LOSS), batch DID NOT trade
  2025-02-18 ny: replay traded (WIN), batch DID NOT trade
  2025-05-08 london: replay traded (LOSS), batch DID NOT trade
  2025-11-04 ny: replay traded (WIN), batch DID NOT trade
  2026-01-12 ny: replay traded (WIN), batch DID NOT trade

## SESSION MEMORY ANALYSIS
  Trades where session memory had context: 5
  Average memory entries at CANDIDATE time: 5.0

## CONFIDENCE SCORE COMPARISON
  Batch avg confidence: 0.0
  Replay avg confidence: 81.0
  Replay confidence std dev: 4.2

## FRAMEWORK BREAKDOWN (Replay)
  breaker_retest: 1 trades, 0.0% WR, -1.0R exp
  ob_retest: 4 trades, 75.0% WR, 0.83R exp
