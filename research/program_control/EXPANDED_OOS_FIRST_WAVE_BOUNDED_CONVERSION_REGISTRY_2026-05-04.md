# Expanded OOS First-Wave Bounded Conversion Registry - 2026-05-04

**Scope:** research/tooling only  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Batch ID:** `sierra_first_wave_bounded_conversion_20260504`  

This registry is written before broad first-wave Sierra conversion. It opens no candidate outcome replay and makes no validation claim. The purpose is to test adapter portability and source quality across the required first-wave families after the NQ pilot path proved the converter/replay path.

## Registered Slice

| Field | Value |
| --- | --- |
| Source system | `sierra_scid` |
| Start UTC | `2026-04-15T00:00:00Z` |
| End UTC | `2026-04-18T00:00:00Z` |
| Timeframes | `M1`, `M5`, `M15`, `H1`, `D1` |
| Candidate outcomes opened | `0` |
| AI/API calls | `0` |
| Databento calls declared | none |

## Family Mappings

| Family | Source | Output symbol | Evidence class | Transform | Warning |
| --- | --- | --- | --- | --- | --- |
| NAS100/NDX100 | `NQM26-CME` | `NAS100_NQ` | `FUTURES_PROXY_TRANSFER` | `identity` |  |
| NAS100/NDX100 | `MNQM26-CME` | `NAS100_MNQ` | `FUTURES_PROXY_TRANSFER` | `identity` |  |
| US30/US30_cash | `YMM26-CBOT` | `US30_YM` | `FUTURES_PROXY_TRANSFER` | `identity` |  |
| US30/US30_cash | `MYMM26-CBOT` | `US30_MYM` | `FUTURES_PROXY_TRANSFER` | `identity` |  |
| XAUUSD | `XAUUSD` | `XAUUSD_SCID` | `SAME_MARKET_SOURCE_TRANSFER` | `identity` |  |
| XAUUSD | `GCM26-COMEX` | `XAUUSD_GC` | `FUTURES_PROXY_TRANSFER` | `identity` |  |
| XAUUSD | `MGCM26-COMEX` | `XAUUSD_MGC` | `FUTURES_PROXY_TRANSFER` | `identity` |  |
| XAGUSD | `SIM26-COMEX` | `XAGUSD_SI` | `FUTURES_PROXY_TRANSFER` | `identity` | known sparse SCID |
| XAGUSD | `SILM26-COMEX` | `XAGUSD_SIL` | `FUTURES_PROXY_TRANSFER` | `identity` | known sparse SCID |
| USDJPY | `6JM26-CME` | `USDJPY_6J` | `FUTURES_PROXY_TRANSFER` | `inverse` | proxy mapping caution, not activated |
| GBPUSD | `6BM26-CME` | `GBPUSD_6B` | `FUTURES_PROXY_TRANSFER` | `identity` |  |
| EURUSD | `EURUSD` | `EURUSD_SCID` | `SAME_MARKET_SOURCE_TRANSFER` | `identity` |  |
| EURUSD | `6EM26-CME` | `EURUSD_6E` | `FUTURES_PROXY_TRANSFER` | `identity` |  |
| S&P | `ESM26-CME` | `SPX_ES` | `FUTURES_PROXY_TRANSFER` | `identity` |  |
| S&P | `MESM26-CME` | `SPX_MES` | `FUTURES_PROXY_TRANSFER` | `identity` |  |
| CL macro/liquidity proxy/control | `CLM26-NYMEX` | `CL_PROXY` | `CROSS_INSTRUMENT_TRANSFER` | `identity` |  |
| ZN macro/rates proxy/control | `ZNM26-CBOT` | `ZN_CONTROL` | `CROSS_INSTRUMENT_TRANSFER` | `identity` |  |
| VIX/VXM controls | `VXM26-CFE` | `VIX_VXM` | `CROSS_INSTRUMENT_TRANSFER` | `identity` |  |
| VIX/VXM controls | `VXMM26-CFE` | `VIX_VXMM` | `CROSS_INSTRUMENT_TRANSFER` | `identity` | known sparse SCID |

## Boundary

Converted source rows are not validation by themselves. This batch is adapter/source-quality evidence only until a frozen replay or label join reads a registered slice for candidate scoring.
