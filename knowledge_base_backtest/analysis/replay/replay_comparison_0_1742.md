# REPLAY vs BATCH COMPARISON
==================================================

Dates replayed: 58
Candles evaluated: 791 (with session memory)
API calls: 175
API cost: $3.27

## OVERALL
  Batch:  0 trades, 0% WR, +0R total, 0R exp
  Replay: 3 trades, 33.3% WR, +-0.52R total, -0.17R exp

## TRADE-BY-TRADE DIFF (same dates)
  Both took same trade, same outcome: 0
  Both took same trade, different outcome: 0
  Batch traded, replay didn't: 0 (session memory caused skip?)
  Replay traded, batch didn't: 3 (session memory found opportunity?)

### Differences:
  2025-06-25 london: replay traded (LOSS), batch DID NOT trade
  2025-09-23 ny: replay traded (LOSS), batch DID NOT trade
  2025-10-13 london: replay traded (WIN), batch DID NOT trade

## SESSION MEMORY ANALYSIS
  Trades where session memory had context: 3
  Average memory entries at CANDIDATE time: 5.0

## CONFIDENCE SCORE COMPARISON
  Batch avg confidence: 0.0
  Replay avg confidence: 78.3
  Replay confidence std dev: 2.9

## FRAMEWORK BREAKDOWN (Replay)
  ob_retest: 3 trades, 33.3% WR, -0.17R exp
