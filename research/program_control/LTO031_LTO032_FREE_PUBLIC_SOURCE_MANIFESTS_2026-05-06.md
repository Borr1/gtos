# LTO031 / LTO032 Free Public Source Manifests - 2026-05-06

**Schema:** `lto031_lto032_free_public_source_manifests_v1`
**Generated:** `2026-05-06T00:26:49.181985+00:00`
**Status:** `FREE_PUBLIC_SOURCE_MANIFESTS_READY_NO_FETCH`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Purpose

P1 manifests for free/public and existing feed lanes: FX COT, BIS, Fed/FRED, public Cboe volatility indices, and existing FlashAlpha forward GEX proxy. This is source-index and cache-contract work only.

No public feed was fetched by this builder, no paid data was used, and no live trading behavior changed.

## Manifest Summary

- Manifest count: `5`
- Status counts: `{'EXISTING_FORWARD_CONTEXT_CACHE_PRESENT': 1, 'PARTIAL_FRED_VOL_CACHE_PRESENT_CBOE_RAW_REQUIRED': 1, 'PARTIAL_LOCAL_CACHE_PRESENT_FRED_REGISTRY_REQUIRED': 1, 'PARTIAL_LOCAL_CACHE_PRESENT_FX_MAPPING_REQUIRED': 1, 'SOURCE_MANIFEST_READY_NO_LOCAL_BIS_CACHE': 1}`
- Source-index rows with local normalized cache evidence: `4`
- Validation-safe rows: `{'false': 5, 'true': 0}`

## Source Rows

| Source | Status | Local source | Raw files | Normalized files | Rows | Validation safe |
| --- | --- | --- | --- | --- | --- | --- |
| fx_cot | PARTIAL_LOCAL_CACHE_PRESENT_FX_MAPPING_REQUIRED | cftc_cot | 6 | 3 | 410 | false |
| bis_macro | SOURCE_MANIFEST_READY_NO_LOCAL_BIS_CACHE | - | 0 | 0 | 0 | false |
| fed_fred_research | PARTIAL_LOCAL_CACHE_PRESENT_FRED_REGISTRY_REQUIRED | fred | 30 | 15 | 15809 | false |
| vix_vix9d_gvz_vvix_vix1d | PARTIAL_FRED_VOL_CACHE_PRESENT_CBOE_RAW_REQUIRED | fred | 30 | 15 | 15809 | false |
| flashalpha_basic_gex_forward_proxy | EXISTING_FORWARD_CONTEXT_CACHE_PRESENT | flashalpha_gex | 30 | 15 | 15 | false |

## Blockers Before Fetch

- BIS: exact data sets and series keys not selected.
- FX COT: FX contract mappings not registered.
- Cboe vol: Cboe raw CSV source index/parser not built; FRED VIX/GVZ mirrors are not Cboe raw evidence.
- FlashAlpha: existing forward proxy only; historical gamma and VRP validation blocked.

## No-Lookahead Rules

- All source features join by candidate_id, decision_time_utc, asof_cutoff_utc, and publication/availability timestamp.
- Observation dates are not availability timestamps.
- Forward context snapshots cannot be used to reconstruct earlier historical states.
- Broker actual-R, synthetic path-R, and source/context labels remain separated.

## Safety Counters

- AI calls: `0`
- Canary calls: `0`
- Order calls: `0`
- Paid data calls: `0`
- Paid fetch attempted: `False`

## NO_PROMOTION_VERDICT

These manifests are context/shadow-only inputs. No source is validation-safe or promoted.
