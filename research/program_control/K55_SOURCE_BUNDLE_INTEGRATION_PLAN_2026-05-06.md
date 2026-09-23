# K55 Source Bundle Integration Plan - 2026-05-06

**Schema:** `k55_source_bundle_integration_plan_v1`
**Generated:** `2026-05-06T00:26:53.769201+00:00`
**Status:** `K55_SOURCE_BUNDLE_INTEGRATION_PLAN_READY_SHADOW_ONLY`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Purpose

P5 K55 source-bundle plan for LTO-031/LTO-032 artifacts. It defines the source-bundle whitelist, as-of provenance rules, freshness gates, and stale-K54 rejection policy before any external context becomes a K55 numeric feature.

No inference, retrain, model selection, live selector, prompt, risk, execution, or order behavior changed.

## Source Bundles

| Bundle | Phase | Artifact status | K55 status | Provenance flags | Numeric feature |
| --- | --- | --- | --- | --- | --- |
| p0_source_contract_registry | P0 | SOURCE_CONTRACT_REGISTRY_READY_RESEARCH_ONLY | SOURCE_BUNDLE_PLAN_READY_NOT_NUMERIC_FEATURES | true | false |
| p1_free_public_existing_feeds | P1 | FREE_PUBLIC_SOURCE_MANIFESTS_READY_NO_FETCH | SOURCE_BUNDLE_PLAN_READY_ASOF_JOIN_ROWS_REQUIRED | true | false |
| p2_databento_credit_replay | P2 | DATABENTO_CREDIT_REPLAY_MANIFESTS_READY_ESTIMATE_REQUIRED | SOURCE_BUNDLE_BLOCKED_ESTIMATE_AND_FETCH_REQUIRED | true | false |
| p3_sierra_scid_footprint_profile | P3 | SIERRA_SCID_FOOTPRINT_PROFILE_PLAN_READY_SHADOW_ONLY | SOURCE_BUNDLE_PLAN_READY_EXTRACTOR_ROWS_REQUIRED | true | false |
| p4_options_gamma_vrp | P4 | OPTIONS_GAMMA_VRP_SOURCE_MANIFESTS_READY_NO_FETCH | SOURCE_BUNDLE_PLAN_READY_HISTORICAL_SOURCE_BLOCKED | true | false |

## Feature Key Policy

- Whitelisted prefixes: `['source_available__', 'source_freshness_seconds__', 'source_status_code__', 'source_row_age_bars__', 'context_numeric__', 'context_flag__', 'missing_source__']`
- Allowed examples: `['source_available__p1_free_public_existing_feeds', 'source_freshness_seconds__flashalpha_basic_gex_forward_proxy', 'context_flag__vix1d_vix9d_missing_required_terms', 'missing_source__official_or_historical_aggregate_gex']`
- Rejected examples: `['broker_actual_r__p1_free_public_existing_feeds', 'context_numeric__future_outcome_r', 'path_label__databento_replay', 'source_available_unprefixed']`

## Stale Artifact Policy

| Artifact family | Reuse allowed | Status | Reason |
| --- | --- | --- | --- |
| k54_v2 | false | REJECTED_STALE_K54_ARTIFACT_NOT_K55_COMPATIBLE | Archived K54 evidence is not a matching K55 target/feature-bundle artifact. |
| k54_v3 | false | REJECTED_STALE_K54_ARTIFACT_NOT_K55_COMPATIBLE | K54 v3 failed current promotion gates and its offline feature catalog is not the live K55 bundle. |
| k54_v4 | false | REJECTED_STALE_K54_ARTIFACT_NOT_K55_COMPATIBLE | K54 v4 architectures failed and cannot be silently reused for K55 inference. |
| k55_json_linear | true | ALLOWED_ONLY_IF_TARGET_AND_FEATURE_BUNDLE_MATCH | K55 inference requires matching target_version, feature_bundle_version, numeric weights, threshold, and no-leak keys. |

## Integration Rules

- External context features must join by candidate_id, decision_time_utc/asof_cutoff_utc, source publication timestamp, and source dependency signature.
- Missing or blocked sources are encoded as availability/provenance flags, not fabricated numeric values.
- Post-decision labels, broker actual-R, synthetic path-R, path labels, PnL, and outcome fields are excluded from feature vectors.
- No stale K54 artifact can be reused unless converted into a K55 artifact with matching target and feature-bundle versions.
- K55 remains shadow-only until a separate promotion dossier exists.

## Validation

- Validation issues: `[]`
- Numeric-ready source bundles: `0`

## Safety Counters

- AI calls: `0`
- Canary calls: `0`
- Order calls: `0`
- Paid data calls: `0`

## NO_PROMOTION_VERDICT

This is a K55 shadow-source integration plan only.
