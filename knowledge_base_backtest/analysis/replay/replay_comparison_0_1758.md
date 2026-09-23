# REPLAY vs BATCH COMPARISON
==================================================

Dates replayed: 59
Candles evaluated: 748 (with session memory)
API calls: 259
API cost: $4.70

## OVERALL
  Batch:  0 trades, 0% WR, +0R total, 0R exp
  Replay: 3 trades, 33.3% WR, +2.66R total, 0.89R exp

## TRADE-BY-TRADE DIFF (same dates)
  Both took same trade, same outcome: 0
  Both took same trade, different outcome: 0
  Batch traded, replay didn't: 0 (session memory caused skip?)
  Replay traded, batch didn't: 3 (session memory found opportunity?)

### Differences:
  2025-03-25 london: replay traded (BREAKEVEN), batch DID NOT trade
  2025-03-25 ny: replay traded (WIN), batch DID NOT trade
  2025-05-07 ny: replay traded (LOSS), batch DID NOT trade

## SESSION MEMORY ANALYSIS
  Trades where session memory had context: 3
  Average memory entries at CANDIDATE time: 2.7

## CONFIDENCE SCORE COMPARISON
  Batch avg confidence: 0.0
  Replay avg confidence: 76.7
  Replay confidence std dev: 2.9

## FRAMEWORK BREAKDOWN (Replay)
  ob_retest: 3 trades, 33.3% WR, 0.89R exp
