# LTO032 Options Gamma VRP Source Manifests - 2026-05-06

**Schema:** `lto032_options_gamma_vrp_source_manifests_v1`
**Generated:** `2026-05-06T00:26:49.186417+00:00`
**Status:** `OPTIONS_GAMMA_VRP_SOURCE_MANIFESTS_READY_NO_FETCH`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Purpose

P4 options/gamma/VRP source manifests. This artifact keeps FlashAlpha Basic forward-context only and records the source blockers for historical aggregate GEX, VIX1D/VIX9D, and VRP.

No source was fetched, no paid data was used, and no live trading behavior changed.

## Source Rows

| Manifest | Status | Role | Historical validation | Forward context | Validation safe |
| --- | --- | --- | --- | --- | --- |
| flashalpha_basic_gex_forward_proxy | READY_FORWARD_CONTEXT_ONLY_EXISTING_CACHE | single-expiry forward gamma proxy | false | true | false |
| official_or_historical_aggregate_gex | BLOCKED_LEGAL_TIMESTAMPED_HISTORICAL_GEX_REQUIRED | official or licensed historical aggregate gamma | false | false | false |
| vix1d_vix9d_spread | BLOCKED_VIX1D_VIX9D_SOURCE_REQUIRED | short-vol/dealer-gamma public volatility proxy | false | false | false |
| vrp_delta | BLOCKED_VRP_CONSTRUCTION_PREREGISTRATION_REQUIRED | volatility-risk-premium regime/context feature | false | false | false |

## Counts

- Source rows: `4`
- Status counts: `{'BLOCKED_LEGAL_TIMESTAMPED_HISTORICAL_GEX_REQUIRED': 1, 'BLOCKED_VIX1D_VIX9D_SOURCE_REQUIRED': 1, 'BLOCKED_VRP_CONSTRUCTION_PREREGISTRATION_REQUIRED': 1, 'READY_FORWARD_CONTEXT_ONLY_EXISTING_CACHE': 1}`
- Validation-safe rows: `{'false': 4, 'true': 0}`
- Historical-validation-allowed rows: `{'false': 4, 'true': 0}`
- Validation issues: `[]`

## Blocked Before Validation

- FlashAlpha Basic is not official/historical aggregate GEX.
- Official/historical aggregate GEX source and schema are not registered.
- VIX1D/VIX9D legal/public source index is incomplete.
- VRP formula, implied-vol source, realized-vol estimator, and instrument mappings are not frozen.

## No-Lookahead Rules

- Forward FlashAlpha snapshots join only at or after snapshot as_of_utc/publication timestamp.
- Historical GEX requires legal timestamped source rows before validation.
- VIX1D/VIX9D spread requires both terms plus source availability timestamps.
- VRP realized-vol lookback must end at or before decision_time_utc.

## Safety Counters

- AI calls: `0`
- Canary calls: `0`
- Order calls: `0`
- Paid data calls: `0`
- Paid fetch attempted: `False`

## NO_PROMOTION_VERDICT

No options/gamma/VRP source is validation-safe or promoted.
