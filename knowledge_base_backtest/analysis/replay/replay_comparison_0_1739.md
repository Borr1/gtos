# REPLAY vs BATCH COMPARISON
==================================================

Dates replayed: 59
Candles evaluated: 946 (with session memory)
API calls: 179
API cost: $3.16

## OVERALL
  Batch:  0 trades, 0% WR, +0R total, 0R exp
  Replay: 1 trades, 100.0% WR, +0.36R total, 0.36R exp

## TRADE-BY-TRADE DIFF (same dates)
  Both took same trade, same outcome: 0
  Both took same trade, different outcome: 0
  Batch traded, replay didn't: 0 (session memory caused skip?)
  Replay traded, batch didn't: 1 (session memory found opportunity?)

### Differences:
  2024-10-03 ny: replay traded (WIN), batch DID NOT trade

## SESSION MEMORY ANALYSIS
  Trades where session memory had context: 1
  Average memory entries at CANDIDATE time: 6.0

## CONFIDENCE SCORE COMPARISON
  Batch avg confidence: 0.0
  Replay avg confidence: 75.0


## FRAMEWORK BREAKDOWN (Replay)
  ob_retest: 1 trades, 100.0% WR, 0.36R exp
