# LTO013 Sierra Source/Parity Registry - 2026-05-05

**Status:** `OK_WITH_BLOCKED_PROXY_ROWS`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Summary

Every candidate can now carry an explicit Sierra proxy class, parity status, allowed-use boundary, and no-promotion status independent of depth feature extraction.

## Counts

| Metric | Value |
| --- | --- |
| candidate_rows | 538 |
| status_rows_to_backfill | 538 |
| usable_depth_context_rows | 116 |
| blocked_or_no_proxy_rows | 331 |
| registered_registry_symbols | 14 |

## Proxy Class Counts

| Proxy class | Count |
| --- | --- |
| FUTURES_PROXY_TRANSFER | 61 |
| NO_REGISTERED_PROXY | 271 |
| SAME_MARKET_SOURCE_TRANSFER | 30 |
| SOURCE_DEFINITION_BLOCKED | 60 |
| VALIDATED_PROXY | 116 |

## Registry

| Symbol | Sierra root | Futures | Class | Allowed use | Depth allowed |
| --- | --- | --- | --- | --- | --- |
| CL | CLM26-NYMEX | CL.v.0 | CONTROL_ONLY | macro_liquidity_control_only | false |
| EURUSD | 6EM26-CME | 6E.v.0 | FUTURES_PROXY_TRANSFER | euro_futures_context_only_until_transfer_validated | false |
| GBPJPY | - | - | NO_REGISTERED_PROXY | no_sierra_orderflow_use | false |
| GBPUSD | 6BM26-CME | 6B.v.0 | FUTURES_PROXY_TRANSFER | gbp_futures_context_only_with_common_second_alignment | false |
| GER40 | - | - | NO_REGISTERED_PROXY | no_sierra_orderflow_use | false |
| NAS100 | NQM26-CME | NQ.v.0 | VALIDATED_PROXY | predecision_nq_mbp10_depth_context_shadow_only | true |
| UK100 | - | - | NO_REGISTERED_PROXY | no_sierra_orderflow_use | false |
| US30 | YMM26-CBOT | YM.v.0 | VALIDATED_PROXY | predecision_ym_mbp10_depth_context_shadow_only | true |
| US30_cash | YMM26-CBOT | YM.v.0 | VALIDATED_PROXY | predecision_ym_mbp10_depth_context_shadow_only | true |
| USDJPY | 6JM26-CME | 6J.v.0 | FUTURES_PROXY_TRANSFER | yen_futures_context_only_until_transfer_validated | false |
| VXM | VXM26-CFE | VX.v.0 | CONTROL_ONLY | volatility_control_only | false |
| XAGUSD | SIM26-COMEX | SI.v.0 | SOURCE_DEFINITION_BLOCKED | source_status_only_until_si_depth_definition_is_registered | false |
| XAUUSD | GCM26-COMEX | GC.v.0 | SAME_MARKET_SOURCE_TRANSFER | gold_futures_market_condition_context_shadow_only | false |
| ZN | ZNM26-CBOT | ZN.v.0 | CONTROL_ONLY | rates_liquidity_control_only | false |

## Boundary

- Registry rows are shadow/source metadata only.
- This audit made zero Sierra depth scans and zero Databento calls.
- This does not create a live filter, signal, entry rule, risk modifier, or promotion dossier.

## Next Action

Use this lane to separate immediately usable NQ/YM depth context from caution, control-only, source-definition-blocked, and no-proxy rows before any outcome analysis.
