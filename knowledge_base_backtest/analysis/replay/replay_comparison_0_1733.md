# REPLAY vs BATCH COMPARISON
==================================================

Dates replayed: 59
Candles evaluated: 745 (with session memory)
API calls: 149
API cost: $2.64

## OVERALL
  Batch:  0 trades, 0% WR, +0R total, 0R exp
  Replay: 2 trades, 0.0% WR, +-2.0R total, -1.0R exp

## TRADE-BY-TRADE DIFF (same dates)
  Both took same trade, same outcome: 0
  Both took same trade, different outcome: 0
  Batch traded, replay didn't: 0 (session memory caused skip?)
  Replay traded, batch didn't: 2 (session memory found opportunity?)

### Differences:
  2024-04-08 ny: replay traded (LOSS), batch DID NOT trade
  2024-04-18 ny: replay traded (LOSS), batch DID NOT trade

## SESSION MEMORY ANALYSIS
  Trades where session memory had context: 2
  Average memory entries at CANDIDATE time: 1.5

## CONFIDENCE SCORE COMPARISON
  Batch avg confidence: 0.0
  Replay avg confidence: 80.0
  Replay confidence std dev: 0.0

## FRAMEWORK BREAKDOWN (Replay)
  ob_retest: 2 trades, 0.0% WR, -1.0R exp
