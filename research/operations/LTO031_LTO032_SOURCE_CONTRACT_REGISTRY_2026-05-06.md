# LTO031 / LTO032 Source Contract Registry Result - 2026-05-06

**Status:** `SOURCE_CONTRACT_REGISTRY_READY_RESEARCH_ONLY`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Schema:** `lto031_lto032_source_contract_registry_v1`

## Result

P0 source-contract registry is built for all current LTO-031/LTO-032 source families. Every row now has URL/vendor, legal/access status, cache schema, publication timestamp rule, cost policy, allowed feature role, and validation-safety blockers.

No source is marked validation-safe. That is intentional: this artifact precedes ingest, as-of cache creation, parser tests, and candidate joins.

## Counts

- Source contracts: `11`
- By LTO: `{'LTO-031': 7, 'LTO-032': 4}`
- Source readiness: `{'BLOCKED_BIS_TABLE_SELECTION_REQUIRED': 1, 'BLOCKED_FORMULA_AND_SOURCE_CONTRACT_REQUIRED': 1, 'BLOCKED_FX_CONTRACT_MAPPING_REQUIRED': 1, 'BLOCKED_LEGAL_BENCHMARK_SOURCE_OR_PROXY_REQUIRED': 1, 'BLOCKED_LOCAL_OR_PROVIDER_COVERAGE_REQUIRED': 1, 'BLOCKED_PAID_OR_LICENSE_REQUIRED': 1, 'BLOCKED_SOURCE_DISCOVERY_REQUIRED': 1, 'PARTIAL_EXISTING_FREE_PUBLIC_REGISTRY_REQUIRED': 1, 'PARTIAL_PUBLIC_VOL_INDEX_SOURCE_READY_VIX1D_BLOCKED': 1, 'PLANNED_EXISTING_CREDITS_ONLY_ESTIMATE_FIRST': 1, 'READY_FORWARD_CONTEXT_ONLY_NOT_HISTORICAL_VALIDATION': 1}`
- Validation-safe rows: `{'false': 11}`
- Validation issues: `[]`

## Source-Safety Decisions

- Free/public candidates remain planning-ready only until raw evidence and normalized point-in-time rows exist.
- FlashAlpha Basic remains forward-context only, not historical gamma/VRP validation evidence.
- Databento remains existing-credit-only and estimate-before-fetch.
- Paid or licensed gamma sources remain blocked pending a separate future owner approval.
- Sierra and Databento are not substitutes for COT, BIS, Fed/FRED, or official options/gamma source contracts.

## Validation Blockers

`{'fx_cot': ['ASOF_JOIN_TESTS_NOT_RUN', 'FX_FUTURES_CONTRACT_MAPPING_NOT_REGISTERED', 'NORMALIZED_POINT_IN_TIME_ROWS_NOT_BUILT', 'RAW_SOURCE_EVIDENCE_NOT_CACHED', 'SOURCE_CONTRACT_NOT_COMPLETE'], 'bis_macro': ['ASOF_JOIN_TESTS_NOT_RUN', 'BIS_TABLE_AND_RELEASE_METADATA_SELECTION_NOT_REGISTERED', 'NORMALIZED_POINT_IN_TIME_ROWS_NOT_BUILT', 'RAW_SOURCE_EVIDENCE_NOT_CACHED', 'SOURCE_CONTRACT_NOT_COMPLETE'], 'fed_fred_research': ['ALFRED_VINTAGE_OR_AVAILABILITY_LIMITATION_NOT_RESOLVED', 'ASOF_JOIN_TESTS_NOT_RUN', 'NORMALIZED_POINT_IN_TIME_ROWS_NOT_BUILT', 'RAW_SOURCE_EVIDENCE_NOT_CACHED'], 'kmw_fx_fix': ['ASOF_JOIN_TESTS_NOT_RUN', 'LEGAL_FIX_BENCHMARK_OR_PROXY_NOT_REGISTERED', 'NORMALIZED_POINT_IN_TIME_ROWS_NOT_BUILT', 'RAW_SOURCE_EVIDENCE_NOT_CACHED', 'SOURCE_CONTRACT_NOT_COMPLETE'], 'hkm_intermediary_capital': ['ASOF_JOIN_TESTS_NOT_RUN', 'H_K_M_FACTOR_OR_OFFICIAL_PROXY_NOT_REGISTERED', 'NORMALIZED_POINT_IN_TIME_ROWS_NOT_BUILT', 'RAW_SOURCE_EVIDENCE_NOT_CACHED', 'SOURCE_CONTRACT_NOT_COMPLETE'], 'pre_2024_tick_lob': ['ASOF_JOIN_TESTS_NOT_RUN', 'DATABENTO_REQUEST_MANIFEST_AND_COST_ESTIMATE_NOT_BUILT', 'NORMALIZED_POINT_IN_TIME_ROWS_NOT_BUILT', 'RAW_SOURCE_EVIDENCE_NOT_CACHED'], 'pre_2022_ohlcv': ['ASOF_JOIN_TESTS_NOT_RUN', 'LOCAL_OR_PROVIDER_COVERAGE_NOT_ESTABLISHED', 'NORMALIZED_POINT_IN_TIME_ROWS_NOT_BUILT', 'RAW_SOURCE_EVIDENCE_NOT_CACHED', 'SOURCE_CONTRACT_NOT_COMPLETE'], 'flashalpha_basic_gex_forward_proxy': ['ASOF_JOIN_TESTS_NOT_RUN', 'FORWARD_PROXY_ONLY_NO_HISTORICAL_GAMMA_RECONSTRUCTION', 'NORMALIZED_POINT_IN_TIME_ROWS_NOT_BUILT', 'RAW_SOURCE_EVIDENCE_NOT_CACHED'], 'vix_vix9d_gvz_vvix_vix1d': ['ASOF_JOIN_TESTS_NOT_RUN', 'NORMALIZED_POINT_IN_TIME_ROWS_NOT_BUILT', 'RAW_SOURCE_EVIDENCE_NOT_CACHED', 'SOURCE_CONTRACT_NOT_COMPLETE', 'VIX1D_PUBLIC_HISTORY_SOURCE_NOT_CONFIRMED'], 'official_or_historical_aggregate_gex': ['ASOF_JOIN_TESTS_NOT_RUN', 'LEGAL_TIMESTAMPED_HISTORICAL_GEX_SOURCE_NOT_CONTRACTED', 'NORMALIZED_POINT_IN_TIME_ROWS_NOT_BUILT', 'RAW_SOURCE_EVIDENCE_NOT_CACHED', 'SOURCE_CONTRACT_NOT_COMPLETE'], 'vrp_delta': ['ASOF_JOIN_TESTS_NOT_RUN', 'NORMALIZED_POINT_IN_TIME_ROWS_NOT_BUILT', 'RAW_SOURCE_EVIDENCE_NOT_CACHED', 'SOURCE_CONTRACT_NOT_COMPLETE', 'VRP_FORMULA_AND_IMPLIED_SOURCE_NOT_FROZEN']}`

## Verification

- `python -m py_compile src/research_infra/lto_source_contract_registry.py scripts/build_lto031_lto032_source_contract_registry.py`
- `python -m pytest tests/test_lto_source_contract_registry.py tests/test_lto031_lto032_source_unblocking_plan.py -q -p no:cacheprovider --basetemp C:\tmp\pytest_phase3_lto_source_registry`

## NO_PROMOTION_VERDICT

This is research/source-readiness control work only. No live trading behavior changed.
