# Expanded OOS XAUUSD SCID Replay Registry - 2026-05-04

**Scope:** research/tooling only  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Batch ID:** `sierra_xauusd_scid_to_xauusd_pilot_20260504`  

This registry is written before opening a same-market Sierra `XAUUSD.scid` replay slice. It reuses the frozen 2026-05-03 candidate registry and introduces no new strategy rule.

## Registered Batch

| Field | Value |
| --- | --- |
| Family | XAUUSD same-market Sierra SCID |
| Source | `C:\SierraChart\Data\XAUUSD.scid` |
| Output file symbol | `XAUUSD` |
| Evidence class | `SAME_MARKET_SOURCE_TRANSFER` |
| Price transform | `identity` |
| Conversion timeframes | `M1`, `M5`, `M15`, `H1`, `D1` |
| Conversion slice | Full local file for lookback; not outcome-opened by conversion alone |
| Replay opened slice | `2026-04-15T13:00:00Z` to `2026-04-17T17:00:00Z` |
| Reserved holdout | `2026-04-20T00:00:00Z` to `2026-05-01T21:00:00Z` |

Planned commands:

```powershell
python scripts\convert_sierra_scid_to_ohlcv.py --batch-id sierra_xauusd_scid_to_xauusd_pilot_20260504 --mapping XAUUSD=XAUUSD:SAME_MARKET_SOURCE_TRANSFER --timeframe M1 --timeframe M5 --timeframe M15 --timeframe H1 --timeframe D1 --quiet
python scripts\run_raw_ohlc_prequential_replay.py --data-dir data\sierra_ohlcv_roots\sierra_xauusd_scid_to_xauusd_pilot_20260504 --start 2026-04-15T13:00:00Z --end 2026-04-17T17:00:00Z --include-blocked-controls --max-events 500 --write --quiet
```

Boundary: Sierra XAUUSD is same-market source-transfer evidence, not MT5 broker execution truth. Any result remains `NO_PROMOTION_VERDICT`.
