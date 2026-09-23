# Historical OHLC GTOS Target/Stop NA Binding Repair

Generated UTC: 2026-05-16T06:07:50Z

## Boundary

Historical OHLC GTOS target/stop NA binding repair only. Rows prove whether TARGETSTOP_NA_NA entry-level repair branches can be bound to existing partial/source-recheck signature-scope target/stop contracts; no validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior change is claimed.

## Counts

- TARGETSTOP_NA_NA branch rows: 2
- Binding candidate rows: 128
- Contract summary rows: 32
- Question rows: 4

## Repair Finding

The two NA rows are entry-level repair summaries. Existing signature-scope rows already bind both entries across all 16 target/stop contracts, so the repair is to use those signature-scope rows for path/outcome interpretation and preserve the NA rows only as entry-level provenance.
