# LTO031 / LTO032 Sierra SCID Footprint Profile Result - 2026-05-06

**Status:** `SIERRA_SCID_FOOTPRINT_PROFILE_PLAN_READY_SHADOW_ONLY`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Result

P3 Sierra `.scid` footprint/profile contracts are registered. Bid/ask volume and delta are first; POC/HVN/LVN wait for a frozen bin rule; stacked imbalance and VAH/VAL remain blocked/deferred.

## Counts

- Sierra converted-root manifests: `7`
- Sierra converted CSV files: `125`
- Bid/ask-capable CSV files: `125`
- Feature status counts: `{'BLOCKED_PRICE_LEVEL_BID_ASK_VOLUME_REQUIRED': 1, 'BLOCKED_VALUE_AREA_DEFINITION_NOT_FROZEN': 1, 'CONTRACT_READY_BIN_RULE_REQUIRED': 1, 'READY_FROM_CONVERTED_SCID_OHLCV': 2}`
- Blocked symbol count: `3`

## Boundaries

- SI/XAGUSD remains source-depth-definition blocked.
- USDJPY/6J and GBPUSD/6B remain proxy/alignment blocked.
- VAH/VAL is deferred until value-area percentage, session boundary, and tie-break rules are frozen.
- No live behavior changed.

## Verification

- `python -m py_compile src/research_infra/lto_sierra_scid_footprint_profile_plan.py scripts/build_lto031_lto032_sierra_scid_footprint_profile_plan.py`
- `python -m pytest tests/test_lto_sierra_scid_footprint_profile_plan.py -q -p no:cacheprovider --basetemp C:\tmp\pytest_phase3_lto_sierra_scid_plan`

## NO_PROMOTION_VERDICT

This is Sierra feature planning/inventory only.
