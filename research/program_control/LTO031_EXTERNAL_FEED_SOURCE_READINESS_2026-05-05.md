# LTO031 External Feed Source Readiness - 2026-05-05

**Schema:** `lto031_external_feed_source_readiness_v1`
**Created:** `2026-06-01T23:38:59.724295+00:00`
**LTO:** `LTO-031`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

External feed blockers are now explicit source-readiness rows; none are validated from unavailable sources.

## Source Status

| Source | Status | Legal/access path | Cache/schema | Expected use |
|---|---|---|---|---|
| `pre_2024_tick_lob` | `BLOCKED` | NOT_REGISTERED | tick_lob_history_v1_required_before_ingest | older tick/depth coverage for source-period expansion and decay checks |
| `pre_2022_ohlcv` | `BLOCKED` | NOT_REGISTERED | ohlcv_history_v1_required_before_replay | older all-symbol OHLCV expansion with source-period bias flags |
| `fx_cot` | `BLOCKED_SOURCE_MAPPING_REQUIRED` | OFFICIAL_PUBLIC_SOURCE_EXPECTED_BUT_FX_MAPPING_NOT_REGISTERED | cftc_fx_cot_v1_required | FX positioning context for USDJPY/GBPJPY/GBPUSD regimes |
| `kmw_fx_fix` | `BLOCKED` | NOT_REGISTERED | fx_fix_calendar_and_window_v1_required | FX fix-window W-shape context for USDJPY/GBPJPY/GBPUSD |
| `hkm_intermediary_capital` | `BLOCKED` | NOT_REGISTERED | hkm_intermediary_capital_v1_required | cross-asset intermediary-capital regime feature |
| `bis_macro` | `BLOCKED` | NOT_REGISTERED | bis_macro_tables_v1_required | JPY carry, macro, and cross-asset risk context |
| `fed_research_feed` | `BLOCKED_SOURCE_UNSPECIFIED` | NOT_REGISTERED | fed_research_feed_v1_required | research/event context only after source is specified |

## Boundary

- No unavailable source is used for validation, replay, ML labels, or live decisions.

## NO_PROMOTION_VERDICT

This artifact is blocker/readiness evidence only. It does not validate, promote, wire, or alter live trading behavior.
