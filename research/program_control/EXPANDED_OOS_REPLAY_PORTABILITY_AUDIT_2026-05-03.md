# Expanded OOS Replay Portability Audit

Date: 2026-05-03
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Summary

| Metric | Value |
| --- | --- |
| tools audited | 8 |
| CLI contract present | 8 |
| partial CLI contract | 0 |
| missing tools | 0 |
| outcome batches opened | 0 |

## Tool Matrix

| Tool | Role | Readiness | Portability | Candidates | Evidence classes | Missing args | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SRC-MT5-OHLCV-EXPORT | MT5 OHLCV source exporter | CLI_CONTRACT_PRESENT | PORTABLE_SOURCE_ADAPTER | source_inventory | TRUE_TEMPORAL_OOS, CROSS_INSTRUMENT_TRANSFER, REGIME_TRANSFER |  | n/a |
| SRC-SIERRA-SCID | Sierra .scid inventory/exporter | CLI_CONTRACT_PRESENT | PORTABLE_EXTRACTION_PARTIAL_REPLAY_ADAPTER | source_inventory, source_transfer | SAME_MARKET_SOURCE_TRANSFER, FUTURES_PROXY_TRANSFER, CROSS_INSTRUMENT_TRANSFER |  | Bulk Sierra .scid to GTOS OHLCV data-root conversion is not implemented in this audit. |
| REPLAY-V2-STRUCTURAL | V2/J46 structural path replay runner | CLI_CONTRACT_PRESENT | PORTABLE_WITH_SPEC_AND_SYMBOL_GUARDS | CAND-001-J46-J49-LIVE-BASELINE, CAND-002-V2-OB-BOUNDARY, CAND-003-V2-FVG-PATH | TRUE_TEMPORAL_OOS, REGIME_TRANSFER, CROSS_INSTRUMENT_TRANSFER |  | Arbitrary new symbols require replay-spec/cohort/config support and GTOS-compatible OHLCV file naming. It cannot consume Sierra .scid or depth files directly. |
| ANALYZE-V2-CONFLUENCE | V2 OB/FVG/Swing/Composite event-log analyzer | CLI_CONTRACT_PRESENT | EVENT_LOG_PORTABLE | CAND-002-V2-OB-BOUNDARY, CAND-003-V2-FVG-PATH | DISCOVERY_ONLY, REGIME_TRANSFER |  | Requires a compatible V2 structural event log generated first. |
| EVAL-V2B-PROSPECTIVE | V2b OB-boundary prospective evaluator | CLI_CONTRACT_PRESENT | EVENT_LOG_PORTABLE_WITH_CUTOFF | CAND-002-V2-OB-BOUNDARY | TRUE_TEMPORAL_OOS, FORWARD_SHADOW |  | Needs resolved post-cutoff OB-boundary/J46 pairs; current goal must not call unresolved or same-slice rows validation. |
| PREFILL-PATH-COVERAGE | Pre-fill path coverage harness | CLI_CONTRACT_PRESENT | PORTABLE_WITH_OHLCV_ROOTS | CAND-004-V3-FVG-ONLY-RESCUE, execution_lifecycle_research | DISCOVERY_ONLY, FORWARD_SHADOW |  | Original POI bounds and true broker lifecycle states are still absent. |
| REPLAY-V3-RISK-BANK | V3 reentry/risk-bank exploratory replay | CLI_CONTRACT_PRESENT | EVENT_LOG_AND_OHLCV_PORTABLE_DISCOVERY_ONLY | CAND-004-V3-FVG-ONLY-RESCUE | DISCOVERY_ONLY, TRUE_TEMPORAL_OOS |  | Depends on V2 structural lock metadata; no direct arbitrary-symbol runner without V2 event generation first. |
| ORDERFLOW-NAS100-CACHED | NAS100 cached MBO/MBP-10 feature stability analyzer | CLI_CONTRACT_PRESENT | NAS100_CACHED_ONLY_NOT_ARBITRARY | CAND-005-NAS100-DEPTH-THINNESS | FUTURES_PROXY_TRANSFER, DISCOVERY_ONLY |  | Not portable to Sierra depth files or other symbols until a Sierra/Databento parity feature extractor exists. |

## Blocker Ledger

| Tool | Blocker | Trigger / next adapter |
| --- | --- | --- |
| SRC-SIERRA-SCID | Bulk Sierra .scid to GTOS OHLCV data-root conversion is not implemented in this audit. | Add a bulk converter only after the first registered Sierra replay batch names symbol/date/timeframe slices. |
| REPLAY-V2-STRUCTURAL | Arbitrary new symbols require replay-spec/cohort/config support and GTOS-compatible OHLCV file naming. It cannot consume Sierra .scid or depth files directly. | For first batch, use existing MT5 CSV roots; defer Sierra replay until CSV conversion is registered. |
| ANALYZE-V2-CONFLUENCE | Requires a compatible V2 structural event log generated first. | Run only after a registered V2 event log exists for a new batch. |
| EVAL-V2B-PROSPECTIVE | Needs resolved post-cutoff OB-boundary/J46 pairs; current goal must not call unresolved or same-slice rows validation. | For every new batch, write opened/burned slice metadata and cutoff before evaluating. |
| PREFILL-PATH-COVERAGE | Original POI bounds and true broker lifecycle states are still absent. | Use as coverage support only; do not score delivery-leg logic without lifecycle telemetry. |
| REPLAY-V3-RISK-BANK | Depends on V2 structural lock metadata; no direct arbitrary-symbol runner without V2 event generation first. | After V2 batch generation, run only frozen V3_FVG_ONLY_RESCUE first; keep other V3 variants diagnostic. |
| ORDERFLOW-NAS100-CACHED | Not portable to Sierra depth files or other symbols until a Sierra/Databento parity feature extractor exists. | Build Sierra depth parity extractor for one registered NQ/MNQ window before broad first-wave depth claims. |

## First Batch Recommendation

Use MT5 CSV roots first for same-source temporal/regime replay because V2/J46 tools already consume OHLCV data roots. Defer Sierra .scid/.depth outcome replay until a named converter/parity adapter is registered.

Do not start with:

- broad Sierra depth replay without parity extractor
- cross-instrument transfer framed as validation
- V3 directly on Sierra/depth without V2 event logs
- Component 3B or AI replay

## Interpretation

- Existing V2/J46 and V3 tooling is portable across compatible OHLCV roots and V2 event logs, not directly across every source format.
- Sierra .scid and .depth are source-ready, but Sierra outcome replay needs a registered conversion/parity adapter before claims.
- NAS100 orderflow remains diagnostic and source/proxy-transfer only; actual broker-R coverage remains the promotion blocker.
- This audit opened no outcome slice and does not alter live trading behavior.
