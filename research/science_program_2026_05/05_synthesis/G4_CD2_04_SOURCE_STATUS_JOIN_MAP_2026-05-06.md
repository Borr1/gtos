# G4 CD2-04 Source-Status Join Map - 2026-05-06

**Lane:** `G4`
**Assignment:** `CD2-04`
**Status:** `G4_CD2_04_SOURCE_STATUS_JOIN_MAP_READY`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Generated at UTC:** `2026-05-06T09:32:56Z`
**HEAD read:** `48389494 docs: record merged g0 wave 2 state`

## Purpose

This join map defines how existing G4 orderflow/depth status rows may become K55 source-status and provenance flags only. It is intentionally narrower than the orderflow feature substrate already present in local shadow rows: raw orderflow/depth values are quarantined outside CD2-04 K55 features.

## Join Boundary

| Boundary | Rule |
| --- | --- |
| Primary join keys | `candidate_id`, `decision_time_utc`, `asof_cutoff_utc`, `symbol`, `source_opportunity_id`, `trigger_id` when present |
| As-of rule | Join only rows whose source timestamp is at or before the candidate decision/as-of cutoff, or whose role is static source registry status. |
| Source refs | Preserve `row_key`, `source_line`, `schema_version`, `source_dependency_signature`, `created_at_utc`, `backfilled_at_utc`, and artifact paths in `source_refs`, not as predictive features. |
| Feature output | Only prefixed source/provenance fields from the CD2-04 contract may enter K55. |
| Label separation | Broker actual-R, synthetic path-R, lifecycle/no-fill labels, future path, and post-event orderflow stay outside the feature vector. |
| Promotion posture | `NO_PROMOTION_VERDICT`; all source contracts remain `validation_safe=false`. |

## Source-Status Inputs And Allowed K55 Flags

| Input source | Current role | Allowed K55 flags | Explicit quarantine |
| --- | --- | --- | --- |
| `shadow_logs/orderflow_primitives_status.jsonl` | G4 orderflow primitive registry/source-blocker status | `source_available__g4_orderflow_primitives_status`, `source_status_code__g4_orderflow_primitives`, `context_flag__g4_databento_live_license_blocked`, `context_flag__g4_orderflow_no_lookahead_pass`, `missing_source__g4_stacked_imbalance`, `missing_source__g4_vah_val` | Primitive raw decision fields, cached feature deltas, sign flips, outcome counts as predictive fields |
| `shadow_logs/nas100_orderflow_adverse_selection_status.jsonl` | NAS100/NQ Databento readiness and blocker status | `source_available__g4_nas100_orderflow_status`, `source_status_code__g4_nas100_databento_live`, `context_flag__g4_nas100_broker_actual_r_floor_met`, `context_flag__g4_nas100_mbp10_candidate_floor_met`, `missing_source__g4_databento_live_license` | MBO/MBP numeric depth, total-depth deltas, thin-rate values, actual-R/synthetic counts as predictive fields |
| `shadow_logs/sierra_depth_enrichment_status.jsonl` | Sierra depth enrichment lifecycle and source-readiness summary | `source_available__g4_sierra_depth_status`, `source_status_code__g4_sierra_depth_enrichment`, `context_flag__g4_sierra_file_size_guarded_queue`, `context_flag__g4_sierra_missing_feature_rows`, `missing_source__g4_no_registered_sierra_proxy` | Extracted depth measurements, symbol feature counts as predictive features, queue contents as signal |
| `shadow_logs/sierra_proxy_registry_status.jsonl` | Per-candidate Sierra proxy/parity interpretation | `source_available__g4_sierra_proxy_registry`, `source_status_code__g4_sierra_proxy_class`, `context_flag__g4_depth_interpretation_allowed`, `context_flag__g4_scid_interpretation_allowed`, `missing_source__g4_sierra_proxy_row` | Sierra tick size as signal, source symbol as strategy signal, parity status as validation-safe claim |
| `shadow_logs/sierra_depth_feature_snapshots.jsonl` | Per-candidate Sierra depth feature snapshot/status | `source_available__g4_sierra_depth_snapshot`, `source_status_code__g4_sierra_depth_feature_status`, `context_flag__g4_sierra_depth_features_present`, `context_flag__g4_sierra_depth_interpretation_allowed`, `missing_source__g4_sierra_depth_features` | `features` object values including total depth, imbalance, thinness, near/far ratio, wall fields |
| `shadow_logs/databento_live_trigger_decisions.jsonl` | Databento trigger/source blocker decision | `source_available__g4_databento_trigger_decision`, `source_status_code__g4_databento_trigger`, `context_flag__g4_databento_fetch_policy_allowed`, `missing_source__g4_databento_cache_or_live_license` | Any fetched market data values, future forensic windows, paid-fetch or trigger output as live influence |
| `research/program_control/K55_SOURCE_BUNDLE_INTEGRATION_PLAN_2026-05-06.json` | K55 source-bundle prefix/version policy | `context_flag__g4_k55_prefix_policy_present`, `context_flag__g4_k55_numeric_ready_source_bundles_zero`, `source_status_code__g4_k55_source_bundle_policy` | New source-bundle numeric feature activation |
| `research/ml_program/shadow/K55_TARGET_FEATURE_REGISTRY_2026-05-05.md` | K55 target/version/no-leak contract | `context_flag__g4_k55_target_version_match_required`, `context_flag__g4_k55_feature_bundle_version_match_required`, `context_flag__g4_k55_labels_separate` | Target labels and excluded outcome fields |
| `research/science_program_2026_05/00_control/SOURCE_CONTRACT_REGISTRY_2026-05-06.json` | G0 source-contract validation-safe state | `context_flag__g4_all_source_contracts_validation_safe_false`, `missing_source__g4_validation_safe_orderflow_source` | Any change to master source contracts or `validation_safe=true` claim |

## Status Encoding

CD2-04 status values should be encoded as one-hot or stable categorical flags, not arbitrary text embedded into a model feature.

| Source status | Suggested flag interpretation |
| --- | --- |
| `WAITING_FOR_DATABENTO_LIVE_LICENSE` | `missing_source__g4_databento_live_license = 1` |
| `OK_PRIMITIVES_REGISTERED_WITH_SOURCE_BLOCKERS` | `source_available__g4_orderflow_primitives_status = 1` and blocker flags set |
| `OK_WITH_FILE_SIZE_GUARDED_BACKGROUND_QUEUE` | `source_available__g4_sierra_depth_status = 1`, `context_flag__g4_sierra_file_size_guarded_queue = 1` |
| `FEATURE_EXTRACTION_PENDING_HEAVY_DEPTH_SCAN` | `source_available__g4_sierra_depth_snapshot = 1`, `missing_source__g4_sierra_depth_features = 1` |
| `NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL` | `missing_source__g4_sierra_proxy_row = 1` |
| `USABLE_AS_REGISTERED_NQ_DEPTH_CONTEXT` | `context_flag__g4_depth_interpretation_allowed = 1`, but still not validation-safe |
| `BLOCKED_DO_NOT_TREAT_AS_DATABENTO_EQUIVALENT` | `context_flag__g4_depth_interpretation_allowed = 0`, `missing_source__g4_databento_equivalent_depth = 1` |

## Seed-Hypothesis Join Coverage

| Seed hypothesis | Join-map coverage |
| --- | --- |
| `HYP-G9G4-K55-SOURCE-006` | K55 receives source availability, freshness, status, missing-source, and blocker flags through the allowed prefixes only. |
| `HYP-G9G4-TOOL-ORDERFLOW-005` | Tool-grounding remains a future no-action source-status channel; no runtime tool integration is added here. |
| `HYP-G11G4-SOURCE-GATED-ORDERFLOW-008` | The join requires current source-contract validation state and source-transfer/proxy blockers before any status is interpreted. |
| `HYP-G4-OFI-DEPTH-001` | Numeric OFI/depth fields are explicitly quarantined; only rows proving whether those fields exist, are missing, are blocked, or are as-of may join. |

## Required Blocker Checks

| CD2-04 blocker | Join-map answer |
| --- | --- |
| Databento/Sierra legality and timestamp provenance | Use source contract rows, trigger/status rows, source timestamps, `asof_cutoff_utc`, and `source_dependency_signature`; no legal/paid claim is inferred. |
| Feature bundle target-version match | K55 target and feature bundle versions must match the 2026-05-05 registry before any flags are consumed. |
| No source marked `validation_safe=true` | Current G0 source registry has `0` true rows; any true row would block CD2-04 until separately reviewed. |
| Tool-grounding remains approval/budget blocked | `HYP-G9G4-TOOL-ORDERFLOW-005` is mapped to future no-action source facts only; no tool activation or AI call is authorized. |

## Non-Claims

- This map does not add predictive OFI/depth features.
- This map does not validate NAS100/NQ, Sierra, Databento, GC/XAUUSD, SI/XAGUSD, 6J/USDJPY, or any other proxy for live trading.
- This map does not alter K55 inference state; current model artifact status can remain missing/disabled.
- This map does not edit master registries.
- This map does not change prompts, risk, execution, permissions, safety gates, selectors, MT5, canaries, paid data, credentials, remote pushes, or order behavior.

## NO_PROMOTION_VERDICT

This artifact is a join contract for research-only source provenance. It authorizes no promotion and no live behavior.
