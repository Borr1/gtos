# LTO031 / LTO032 Sierra SCID Footprint Profile Plan - 2026-05-06

**Schema:** `lto031_lto032_sierra_scid_footprint_profile_plan_v1`
**Generated:** `2026-05-06T00:26:49.188850+00:00`
**Status:** `SIERRA_SCID_FOOTPRINT_PROFILE_PLAN_READY_SHADOW_ONLY`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Purpose

P3 Sierra `.scid` footprint/profile plan. This registers feature contracts for bid/ask volume, delta, POC/HVN/LVN, stacked imbalance, and VAH/VAL without wiring any live behavior.

## Local Converted-Root Inventory

- Manifests: `7`
- CSV files: `125`
- CSV rows: `676901`
- Bid/ask-capable CSV files: `125`
- Files by timeframe: `{'D1': 25, 'H1': 25, 'M1': 25, 'M15': 25, 'M5': 25}`

## Feature Contracts

| Feature | Status | Allowed role | Validation safe | Blockers |
| --- | --- | --- | --- | --- |
| scid_bid_ask_volume_v1 | READY_FROM_CONVERTED_SCID_OHLCV | FOOTPRINT_CONTEXT_SHADOW_ONLY | false | CANDIDATE_ASOF_JOIN_NOT_BUILT, BROKER_ACTUAL_R_JOIN_SEPARATE |
| scid_delta_v1 | READY_FROM_CONVERTED_SCID_OHLCV | FOOTPRINT_CONTEXT_SHADOW_ONLY | false | CANDIDATE_ASOF_JOIN_NOT_BUILT, SOURCE_TRANSFER_CAVEATS_BY_SYMBOL |
| scid_profile_poc_hvn_lvn_v1 | CONTRACT_READY_BIN_RULE_REQUIRED | VOLUME_PROFILE_CONTEXT_SHADOW_ONLY | false | PRICE_BIN_RULE_NOT_FROZEN, BAR_PROFILE_IS_APPROX_NOT_PRICE_LEVEL_VOLUME |
| scid_stacked_imbalance_v1 | BLOCKED_PRICE_LEVEL_BID_ASK_VOLUME_REQUIRED | BLOCKED_SOURCE_DEFINITION | false | PRICE_LEVEL_FOOTPRINT_NOT_CAPTURED_IN_CURRENT_SCID_OHLCV_ROOT |
| scid_vah_val_v1 | BLOCKED_VALUE_AREA_DEFINITION_NOT_FROZEN | DEFERRED_SOURCE_DEFINITION | false | VALUE_AREA_PERCENT_NOT_FROZEN, SESSION_BOUNDARY_NOT_FROZEN, TIE_BREAK_RULE_NOT_FROZEN |

## Symbol Source Status

| GTOS | Sierra sources | Status | Blocked |
| --- | --- | --- | --- |
| NAS100 | NQM26-CME, MNQM26-CME | USABLE_FUTURES_PROXY_CONTEXT_WITH_CAVEATS | false |
| US30 | YMM26-CBOT, MYMM26-CBOT | USABLE_FUTURES_PROXY_CONTEXT_WITH_CAVEATS | false |
| XAUUSD | XAUUSD, GCM26-COMEX, MGCM26-COMEX | SAME_MARKET_OR_NEAR_MARKET_CONTEXT_WITH_CAVEATS | false |
| XAGUSD | SIM26-COMEX, SILM26-COMEX | BLOCKED_SOURCE_DEPTH_DEFINITION_SI | true |
| USDJPY | 6JM26-CME | BLOCKED_INVERSE_TRANSFER_REVIEW_OPEN | true |
| GBPUSD | 6BM26-CME | BLOCKED_COMMON_SECOND_ALIGNMENT_REQUIRED | true |

## Validation

- Validation issues: `[]`
- Blocked symbol count: `3`

## Safety Counters

- AI calls: `0`
- Order calls: `0`
- Paid data calls: `0`

## NO_PROMOTION_VERDICT

Sierra `.scid` features remain context/shadow only and are not validation-safe.
