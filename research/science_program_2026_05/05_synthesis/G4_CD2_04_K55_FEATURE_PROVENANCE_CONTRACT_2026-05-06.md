# G4 CD2-04 K55 Feature Provenance Contract - 2026-05-06

**Lane:** `G4`
**Assignment:** `CD2-04`
**Status:** `G4_CD2_04_FEATURE_PROVENANCE_CONTRACT_READY`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Generated at UTC:** `2026-05-06T09:32:56Z`
**HEAD read:** `48389494 docs: record merged g0 wave 2 state`

## Purpose

This G4-owned contract answers CD2-04 only: convert orderflow/depth rows into K55 source-status and provenance flags, not validation-safe predictive orderflow features.

It does not edit master registries, open outcomes, mark any source validation-safe, run MT5, call AI/canaries/paid data, modify prompts, risk, execution, permissions, selectors, safety gates, or change order behavior.

## Controlling Inputs Read

| Input | Evidence used |
| --- | --- |
| G4 goal prompt | `research/science_program_2026_05/04_goal_prompts/G4_G4_MICROSTRUCTURE_AUCTION_GOAL_PROMPT_2026-05-06.md` |
| G0 CD2 assignment | `research/science_program_2026_05/05_synthesis/G0_CROSS_DOMAIN_SECOND_PASS_ASSIGNMENTS_2026-05-06.md` |
| G0 wave-2 reconciliation | `research/science_program_2026_05/05_synthesis/G0_WAVE2_RECONCILIATION_2026-05-06.md` |
| Master registries | `HYPOTHESIS_REGISTRY_2026-05-06.json`, `EXPERIMENT_PREREGISTRY_2026-05-06.json`, `SOURCE_CONTRACT_REGISTRY_2026-05-06.json`, `SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.json` |
| G4 orderflow science | `G4_MICROSTRUCTURE_AUCTION_SYNTHESIS_2026-05-06.md`, `G4_MICROSTRUCTURE_AUCTION_HYPOTHESES_2026-05-06.json`, `G4_MICROSTRUCTURE_AUCTION_SOURCE_CONTRACTS_2026-05-06.json` |
| G9 K55/ML science | `G9_AI_ML_SYSTEMS_SYNTHESIS_2026-05-06.md`, `G9_AI_ML_SYSTEMS_HYPOTHESES_2026-05-06.json`, `K55_TARGET_FEATURE_REGISTRY_2026-05-05.md`, `K55_SOURCE_BUNDLE_INTEGRATION_PLAN_2026-05-06.md` |
| G11 source science | `G11_DATA_SOURCES_EXPANSION_SYNTHESIS_2026-05-06.md`, `G11_DATA_SOURCES_EXPANSION_HYPOTHESES_2026-05-06.json`, `G11_DATA_SOURCES_EXPANSION_SOURCE_CONTRACTS_2026-05-06.json` |
| G1 validation science | `G1_VALIDATION_STATISTICS_SYNTHESIS_2026-05-06.md`, `SCHEMA_CONTRACTS_2026-05-06.md` |

## Seed Rows Covered

| Seed hypothesis | Contract interpretation for CD2-04 |
| --- | --- |
| `HYP-G9G4-K55-SOURCE-006` | K55 may receive G4 source provenance/status fields only after no-leak prefix checks and target/feature-bundle version matching. |
| `HYP-G9G4-TOOL-ORDERFLOW-005` | Future no-action tool outputs may expose only source availability/provenance facts; no prompt/runtime influence is authorized. |
| `HYP-G11G4-SOURCE-GATED-ORDERFLOW-008` | G11 source-contract gates must block invalid orderflow/auction feature experiments before any outcome opening. |
| `HYP-G4-OFI-DEPTH-001` | The original OFI/depth row is outcome-bearing discovery scope; CD2-04 allows only its source-status/provenance shell into K55. |

## K55 Version Gate

K55 joins are permitted only when all of these match the current registry:

| Gate | Required value |
| --- | --- |
| `target_version` | `k55_target_v1_account_history_realized_primary_synthetic_path_context_2026_05_05` |
| `feature_bundle_version` | `k55_feature_bundle_v1_lto001_020_orderflow_asof_2026_05_05` |
| `inference_version` | `k55_shadow_inference_v1_json_linear_or_disabled` |
| model artifact state | Missing or disabled is acceptable; stale K54 artifacts are rejected. |
| source bundle status | Shadow/status only; numeric-ready source bundles remain `0`. |

## Allowed K55 Provenance Feature Surface

Allowed fields must be source-status fields and must use these prefixes:

| Prefix | Allowed meaning | Example |
| --- | --- | --- |
| `source_available__` | Boolean availability of a named G4/G11/G9 source-status row as of the decision. | `source_available__g4_sierra_depth_snapshot` |
| `source_status_code__` | Stable categorical status code or one-hot code for source readiness. | `source_status_code__g4_databento_live_license_blocked` |
| `source_freshness_seconds__` | Age between `decision_time_utc` or `asof_cutoff_utc` and the source row timestamp. | `source_freshness_seconds__g4_orderflow_primitives_status` |
| `source_row_age_bars__` | Bar-age of a source-status row when bar resolution is known. | `source_row_age_bars__g4_sierra_depth_status` |
| `context_flag__` | Boolean blocker, legality, proxy, parser, or label-separation state. | `context_flag__g4_no_leak_pass_predecision_windows_only` |
| `missing_source__` | Boolean missing or blocked source indicator. | `missing_source__g4_sierra_proxy_row` |

The feature vector may not include raw orderflow/depth measurements under this CD2-04 contract. Source references such as `row_key`, `source_line`, `schema_version`, `source_dependency_signature`, `source_id`, and `artifact_path` belong in `source_refs` or audit metadata, not as predictive numeric features.

## Explicitly Forbidden For CD2-04 K55 Features

| Forbidden category | Examples |
| --- | --- |
| Outcome labels | `broker_actual_r`, `actual_r`, `path_label`, `hit_tp1`, `hit_sl`, `pnl`, `profit`, `realized_r`, `synthetic_path_r` |
| Post-decision orderflow | `post15_*`, `post60_*`, future path values, future orderflow fields |
| Raw OFI/depth values | `pre60_ofi`, `event15_ofi`, `pre60_total_depth10`, `event15_total_depth10`, `event15_median_depth10_imbalance`, pull/add/remove sizes, wall concentration |
| Validation-safe flags | Any `validation_safe=true` source flag or promoted source contract |
| Tool influence | `decision_influence_true`, prompt/tool output that changes Component 3A/3B/runtime behavior |
| Live behavior linkage | Any selector, execution, risk, safety-gate, permissions, MT5, canary, or order-routing field |

If a row contains both source status and numeric orderflow values, the K55 CD2-04 join must keep only the status shell. Numeric values remain in research/audit tables outside the K55 feature vector until a separate source-safe predictive-feature prereg and promotion dossier exist.

## Source Contract State

The current G0 source registry reports `86` source-contract rows and `0` `validation_safe=true` rows. CD2-04 preserves that state.

| Source family | Current CD2-04 status |
| --- | --- |
| Databento `GLBX.MDP3` | Existing cached/historical-credit context only; live license remains blocked; estimate/cap required before future paid historical pulls. |
| Sierra `.depth` and `.scid` | Local/source-status and shadow context only; symbol-specific parity and footprint/profile definitions remain required. |
| G4 local orderflow artifacts | Mechanism prior and source-status evidence only; not validation-safe market evidence. |
| G9 K55 local registries | Feature-contract and label-separation control references only; not market data sources. |
| G11 source contracts | Context/source-gating references only; all remain `validation_safe=false`. |

## Contract Result

CD2-04 can add G4 orderflow/depth provenance to K55 as source-status flags only. It cannot add validation-safe predictive orderflow features, cannot open outcomes, cannot activate tool grounding, and cannot change any live trading surface.

## NO_PROMOTION_VERDICT

This artifact is a research contract only. It creates no live signal, filter, source promotion, K55 model promotion, trading decision, or execution change.
