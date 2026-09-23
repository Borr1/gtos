# REPLAY vs BATCH COMPARISON
==================================================

Dates replayed: 58
Candles evaluated: 915 (with session memory)
API calls: 230
API cost: $4.26

## OVERALL
  Batch:  0 trades, 0% WR, +0R total, 0R exp
  Replay: 4 trades, 75.0% WR, +4.43R total, 1.11R exp

## TRADE-BY-TRADE DIFF (same dates)
  Both took same trade, same outcome: 0
  Both took same trade, different outcome: 0
  Batch traded, replay didn't: 0 (session memory caused skip?)
  Replay traded, batch didn't: 4 (session memory found opportunity?)

### Differences:
  2025-12-22 london: replay traded (WIN), batch DID NOT trade
  2025-12-22 ny: replay traded (WIN), batch DID NOT trade
  2026-01-14 london: replay traded (LOSS), batch DID NOT trade
  2026-01-27 london: replay traded (WIN), batch DID NOT trade

## SESSION MEMORY ANALYSIS
  Trades where session memory had context: 4
  Average memory entries at CANDIDATE time: 4.8

## CONFIDENCE SCORE COMPARISON
  Batch avg confidence: 0.0
  Replay avg confidence: 81.2
  Replay confidence std dev: 2.5

## FRAMEWORK BREAKDOWN (Replay)
  ob_retest: 4 trades, 75.0% WR, 1.11R exp
