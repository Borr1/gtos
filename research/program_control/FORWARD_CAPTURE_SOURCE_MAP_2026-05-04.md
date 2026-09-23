# Forward Capture Source Map - 2026-05-04

**Status:** `RESEARCH_ARTIFACT_DONE`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Sources

| Source | Evidence | Blocker |
| --- | --- | --- |
| MT5 broker OHLCV/ticks | BROKER_ACTUAL_R,FORWARD_SHADOW | older tick retention and missing canonical deal-history export |
| Sierra .scid/.depth | SAME_MARKET_SOURCE_TRANSFER,FUTURES_PROXY_TRANSFER | Codex can inspect local files only; missing/stale symbols require Sierra chart/operator capture. |
| Databento cached/declared forward windows | FUTURES_PROXY_TRANSFER,FORWARD_SHADOW | new paid/network pulls require declared manifest, approval, and cost cap. |
| Forward shadow logs | INTERNAL_LIMIT_LIFECYCLE,FORWARD_SHADOW,CONTROL_ONLY | requires future live/forward candidate events. |

## Persistent Constraints

- pre-2024 tick/LOB remains blocked without external archive/provider
- pre-2022 all-symbol OHLCV remains blocked without alternate source
- futures proxy labels are not broker account truth
- source-period flags must be preserved for D-11 supplements and old labels
