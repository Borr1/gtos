# Tick/Sierra Source Contract

Generated UTC: `2026-05-15T15:50:54Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: source contract and primitive schema only. No edge, R/PnL, validation, live-readiness, or promotion verdict.

## Counts

- Tick parquet files: `114`
- Tick schema-ok files: `114`
- Tick symbols: `7` (GBPJPY, GBPUSD, NAS100, US30_cash, USDJPY, XAGUSD, XAUUSD)
- Tick rows total from parquet metadata: `39003954`
- Sierra files: `262`
- Sierra `.scid`: `33`
- Sierra `.depth`: `227`
- Primitive schema rows: `6`

## Boundary

- MT5 tick aggressor is a proxy on this broker because last/volume/buy-sell flags are not authoritative.
- Sierra files are metadata-only until a binary parser and timestamp contract are audited.
- Route C has started, but no primitive has been scored yet.
