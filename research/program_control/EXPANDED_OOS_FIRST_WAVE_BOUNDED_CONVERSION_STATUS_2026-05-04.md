# Expanded OOS First-Wave Bounded Conversion Status - 2026-05-04

**Scope:** research/tooling only  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Batch:** `sierra_first_wave_bounded_conversion_20260504`  
**Manifest:** `data/sierra_ohlcv_roots/sierra_first_wave_bounded_conversion_20260504/manifest.json`

## Result

The Sierra SCID-to-GTOS OHLCV converter produced first-wave M1/M5/M15/H1/D1 roots for 19 mappings over `2026-04-15T00:00:00Z` to `2026-04-18T00:00:00Z`.

- Files written: 95 CSV files plus manifest.
- Converter errors: 0.
- Opened outcomes: no.
- Databento spend: $0.
- AI/API calls: 0.

## M15 Source-Quality Table

| Output | Source | Evidence | Transform | Rows | First | Last | Gaps | Invalid |
|---|---|---|---|---:|---|---|---:|---:|
| `CL_PROXY` | `CLM26-NYMEX` | `CROSS_INSTRUMENT_TRANSFER` | identity | 268 | 2026-04-15 00:00:00 | 2026-04-17 20:45:00 | 2 | 0 |
| `EURUSD_6E` | `6EM26-CME` | `FUTURES_PROXY_TRANSFER` | identity | 268 | 2026-04-15 00:00:00 | 2026-04-17 20:45:00 | 2 | 0 |
| `EURUSD_SCID` | `EURUSD` | `SAME_MARKET_SOURCE_TRANSFER` | identity | 276 | 2026-04-15 00:00:00 | 2026-04-17 20:45:00 | 0 | 0 |
| `GBPUSD_6B` | `6BM26-CME` | `FUTURES_PROXY_TRANSFER` | identity | 268 | 2026-04-15 00:00:00 | 2026-04-17 20:45:00 | 2 | 0 |
| `NAS100_MNQ` | `MNQM26-CME` | `FUTURES_PROXY_TRANSFER` | identity | 268 | 2026-04-15 00:00:00 | 2026-04-17 20:45:00 | 2 | 0 |
| `NAS100_NQ` | `NQM26-CME` | `FUTURES_PROXY_TRANSFER` | identity | 268 | 2026-04-15 00:00:00 | 2026-04-17 20:45:00 | 2 | 0 |
| `SPX_ES` | `ESM26-CME` | `FUTURES_PROXY_TRANSFER` | identity | 268 | 2026-04-15 00:00:00 | 2026-04-17 20:45:00 | 2 | 0 |
| `SPX_MES` | `MESM26-CME` | `FUTURES_PROXY_TRANSFER` | identity | 268 | 2026-04-15 00:00:00 | 2026-04-17 20:45:00 | 2 | 0 |
| `US30_MYM` | `MYMM26-CBOT` | `FUTURES_PROXY_TRANSFER` | identity | 268 | 2026-04-15 00:00:00 | 2026-04-17 20:45:00 | 2 | 0 |
| `US30_YM` | `YMM26-CBOT` | `FUTURES_PROXY_TRANSFER` | identity | 268 | 2026-04-15 00:00:00 | 2026-04-17 20:45:00 | 2 | 0 |
| `USDJPY_6J` | `6JM26-CME` | `FUTURES_PROXY_TRANSFER` | inverse | 268 | 2026-04-15 00:00:00 | 2026-04-17 20:45:00 | 2 | 0 |
| `VIX_VXM` | `VXM26-CFE` | `CROSS_INSTRUMENT_TRANSFER` | identity | 247 | 2026-04-15 00:00:00 | 2026-04-17 20:45:00 | 17 | 0 |
| `VIX_VXMM` | `VXMM26-CFE` | `CROSS_INSTRUMENT_TRANSFER` | identity | 107 | 2026-04-15 00:00:00 | 2026-04-17 20:45:00 | 47 | 0 |
| `XAGUSD_SI` | `SIM26-COMEX` | `FUTURES_PROXY_TRANSFER` | identity | 170 | 2026-04-15 00:45:00 | 2026-04-17 20:45:00 | 42 | 0 |
| `XAGUSD_SIL` | `SILM26-COMEX` | `FUTURES_PROXY_TRANSFER` | identity | 143 | 2026-04-15 00:00:00 | 2026-04-17 20:45:00 | 52 | 0 |
| `XAUUSD_GC` | `GCM26-COMEX` | `FUTURES_PROXY_TRANSFER` | identity | 268 | 2026-04-15 00:00:00 | 2026-04-17 20:45:00 | 2 | 0 |
| `XAUUSD_MGC` | `MGCM26-COMEX` | `FUTURES_PROXY_TRANSFER` | identity | 268 | 2026-04-15 00:00:00 | 2026-04-17 20:45:00 | 2 | 0 |
| `XAUUSD_SCID` | `XAUUSD` | `SAME_MARKET_SOURCE_TRANSFER` | identity | 268 | 2026-04-15 00:00:00 | 2026-04-17 20:45:00 | 2 | 0 |
| `ZN_CONTROL` | `ZNM26-CBOT` | `CROSS_INSTRUMENT_TRANSFER` | identity | 268 | 2026-04-15 00:00:00 | 2026-04-17 20:45:00 | 2 | 0 |

## Interpretation

This closes the first adapter blocker for Sierra intraday bars: `.scid` files can now be converted into the GTOS replay root format across the first-wave source families. It does not validate futures-to-CFD proxy equivalence, does not validate cross-instrument transfer, and opened no outcome labels in this bounded status run.
