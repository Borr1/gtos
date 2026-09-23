# REPLAY vs BATCH COMPARISON
==================================================

Dates replayed: 55
Candles evaluated: 1088 (with session memory)
API calls: 287
API cost: $5.19

## OVERALL
  Batch:  0 trades, 0% WR, +0R total, 0R exp
  Replay: 4 trades, 0.0% WR, +-3.16R total, -0.79R exp

## TRADE-BY-TRADE DIFF (same dates)
  Both took same trade, same outcome: 0
  Both took same trade, different outcome: 0
  Batch traded, replay didn't: 0 (session memory caused skip?)
  Replay traded, batch didn't: 4 (session memory found opportunity?)

### Differences:
  2025-01-24 ny: replay traded (LOSS), batch DID NOT trade
  2025-04-04 ny: replay traded (LOSS), batch DID NOT trade
  2025-12-05 london: replay traded (LOSS), batch DID NOT trade
  2025-12-05 ny: replay traded (LOSS), batch DID NOT trade

## SESSION MEMORY ANALYSIS
  Trades where session memory had context: 4
  Average memory entries at CANDIDATE time: 4.8

## CONFIDENCE SCORE COMPARISON
  Batch avg confidence: 0.0
  Replay avg confidence: 80.0
  Replay confidence std dev: 4.1

## FRAMEWORK BREAKDOWN (Replay)
  ob_retest: 4 trades, 0.0% WR, -0.79R exp
