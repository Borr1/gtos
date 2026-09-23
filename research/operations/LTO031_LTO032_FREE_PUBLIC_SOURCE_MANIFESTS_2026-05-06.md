# LTO031 / LTO032 Free Public Source Manifest Result - 2026-05-06

**Status:** `FREE_PUBLIC_SOURCE_MANIFESTS_READY_NO_FETCH`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Result

P1 source manifests are built for FX COT, BIS, Fed/FRED, public Cboe volatility indices, and existing FlashAlpha. The artifact inventories existing local cache evidence and keeps each lane context/shadow-only.

## Counts

- Manifest count: `5`
- Status counts: `{'EXISTING_FORWARD_CONTEXT_CACHE_PRESENT': 1, 'PARTIAL_FRED_VOL_CACHE_PRESENT_CBOE_RAW_REQUIRED': 1, 'PARTIAL_LOCAL_CACHE_PRESENT_FRED_REGISTRY_REQUIRED': 1, 'PARTIAL_LOCAL_CACHE_PRESENT_FX_MAPPING_REQUIRED': 1, 'SOURCE_MANIFEST_READY_NO_LOCAL_BIS_CACHE': 1}`
- Local source-index rows: `4`
- Validation-safe rows: `{'false': 5, 'true': 0}`

## Interpretation

- Existing cache evidence is present for CFTC COT, FRED, and FlashAlpha.
- CFTC evidence is currently gold-centric; FX contract mappings remain required.
- FRED evidence is partial macro/rates/vol context; vintage-perfect claims need ALFRED/availability handling.
- Cboe volatility work needs a Cboe raw source index before FRED VIX/GVZ mirror rows are treated as Cboe evidence.
- BIS remains source-selected but locally uncached until exact tables/series are registered.

## Verification

- `python -m py_compile src/research_infra/lto_free_public_feed_manifests.py scripts/build_lto031_lto032_free_public_source_manifests.py`
- `python -m pytest tests/test_lto_free_public_feed_manifests.py tests/test_lto_source_contract_registry.py -q -p no:cacheprovider --basetemp C:\tmp\pytest_phase3_lto_free_public_manifests`

## NO_PROMOTION_VERDICT

No feed was fetched, no paid data was used, and no live trading behavior changed.
