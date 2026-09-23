# G7 CD2-01 Macro Vol Source Freshness Compatibility Ledger - 2026-05-06

**Lane:** `G7`  
**Assignment:** `CD2-01 - Macro-vol-source freshness triad`  
**Primary owner:** `G7`  
**Status:** `SOURCE_FRESHNESS_RULES_FROZEN_RESEARCH_ONLY`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`

This is a G7-owned second-pass ledger for `HYP-G7-XG8-VOL-MACRO-011`, `HYP-G7-XG11-SOURCE-FRESH-012`, `HYP-G11-PUBLIC-LAG-004`, and `HYP-G8-VRP-004`. It freezes source-freshness and publication/as-of compatibility rules only. It is not a validation result, source promotion, parser implementation, master-registry edit, live selector, live prompt change, risk change, execution change, MT5 action, paid-data action, or order-behavior change.

## Controlling Inputs Read

| Input | Role |
|---|---|
| `.context/LIVE_STATE.md` | Regenerated in this worktree; current HEAD is `48389494`. |
| `.context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md` | Research-only and no-promotion discipline. |
| `.context/00_core/quick_reference_card.md` | Live-surface guardrails; no trading changes. |
| `.context/00_core/research_operating_doctrine.md` | Source evidence protocol and strict-promotion boundary. |
| `.context/00_core/research_current_state.md` | Current science-program map; all rows remain `NO_PROMOTION_VERDICT`. |
| `.context/00_READING_ORDER.md` | Deep-work routing. |
| `research/science_program_2026_05/04_goal_prompts/G7_G7_MACRO_CROSS_ASSET_GOAL_PROMPT_2026-05-06.md` | G7 lane rules and forbidden surfaces. |
| `research/science_program_2026_05/05_synthesis/G0_CROSS_DOMAIN_SECOND_PASS_ASSIGNMENTS_2026-05-06.md` | CD2-01 objective, seed rows, blocker checks, stop output. |
| `research/science_program_2026_05/05_synthesis/SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.*` | Master state; G7/G8/G11 placeholders and all sources `validation_safe=false`. |
| `research/science_program_2026_05/05_synthesis/G0_WAVE2_RECONCILIATION_2026-05-06.*` | Wave-2 reconciliation; `8` no-leak semantic blockers and second-pass assignment rationale. |
| G7/G8/G11/G1 lane artifacts listed below | Seed-row definitions, source contracts, source indexes, preregs, and validation-control rules. |

## Relevant Lane Evidence

| Evidence | CD2-01 use |
|---|---|
| `research/science_program_2026_05/02_hypothesis_registry/G7_MACRO_CROSS_ASSET_HYPOTHESIS_ROWS_2026-05-06.json` | G7 cross-domain placeholder rows `HYP-G7-XG8-VOL-MACRO-011` and `HYP-G7-XG11-SOURCE-FRESH-012`. |
| `research/science_program_2026_05/03_experiment_specs/G7_MACRO_CROSS_ASSET_EXPERIMENT_PREREG_SPECS_2026-05-06.json` | Existing G7 preregs remain outcomes-closed and blocked pending G8/G11 rows. |
| `research/science_program_2026_05/02_hypothesis_registry/G8_OPTIONS_VOL_HYPOTHESIS_ROWS_2026-05-06.json` | `HYP-G8-VRP-004` requires formula, implied source timing, and realized variance no-lookahead freeze. |
| `research/science_program_2026_05/03_experiment_specs/G8_OPTIONS_VOL_EXPERIMENT_PREREGS_2026-05-06.json` | `EXP-G8-VRP-004` is formula/source audit first, not outcome review. |
| `research/science_program_2026_05/02_hypothesis_registry/G11_DATA_SOURCES_EXPANSION_HYPOTHESES_2026-05-06.json` | `HYP-G11-PUBLIC-LAG-004` targets observation-date versus release-aware contamination. |
| `research/science_program_2026_05/03_experiment_specs/G11_DATA_SOURCES_EXPANSION_EXPERIMENT_PREREGS_2026-05-06.json` | `EXP-G11-PUBLIC-LAG-004` compares feature-table timing only and must not read trade outcomes. |
| `research/science_program_2026_05/01_domain_syntheses/G7_SOURCE_INDEX_2026-05-06.md` | G7 macro source status: COT/BIS/Fed/LBMA/WGC/ICE cached; FRED refresh failed; all validation-safe false. |
| `research/science_program_2026_05/00_control/G8_OPTIONS_VOL_SOURCE_INDEX_2026-05-06.md` | Cboe VIX/VIX1D/VIX9D/GVZ/VVIX/VIX3M CSVs cached through `2026-05-05`; publication timestamp unresolved. |
| `research/science_program_2026_05/00_control/G11_DATA_SOURCES_EXPANSION_SOURCE_INDEX_2026-05-06.md` | G11 source-governance rows require release-aware joins and all remain validation-safe false. |
| `research/science_program_2026_05/01_domain_syntheses/G1_VALIDATION_STATISTICS_SYNTHESIS_2026-05-06.md` | G1 no-leak/source-contract gate: feature availability must be proven before outcome review. |

## Universal CD2-01 As-Of Rule

For any future row that joins macro, vol-index, or source-freshness context to a GTOS candidate:

```text
feature_asof_utc = max(
  source_publication_timestamp_utc,
  source_cache_time_utc,
  source_bar_or_observation_close_time_utc when applicable
)

feature_asof_utc <= candidate_decision_timestamp_utc
```

If any component of `feature_asof_utc` is unknown, date-only, revised without a vintage, or missing a cache/hash, the row is not decision-time safe. It must be excluded before outcome review and counted in a source-freshness blocker bucket.

## Compatibility Ledger

| Source family | Cached evidence | Frozen publication/as-of rule | Leakage/freshness risk | Compatible seed rows | Current blocker status |
|---|---|---|---|---|---|
| CFTC COT | G7/G11 cached CFTC COT pages. Raw CFTC page says COT data are Tuesday positions generally released Friday afternoon, with COT FAQ noting Friday 3:30 pm US Eastern and holiday schedule exceptions. | `report_date` or Tuesday position date is never enough. First usable time is the official release timestamp from the CFTC release schedule, converted from US Eastern to UTC, then gated by cache time/hash. Holiday weeks must use the release schedule, not a Friday default. | Observation-date joins leak unreleased Tuesday positioning. FX mapping and contract-roll mapping remain unresolved. | `HYP-G11-PUBLIC-LAG-004`, `HYP-G7-XG11-SOURCE-FRESH-012`, possible macro side of `HYP-G7-XG8-VOL-MACRO-011`. | `validation_safe=false`; parser/cache/no-lookahead tests missing; direct gold COT alpha route remains killed. |
| FRED / Fed macro-rates | G7 FRED refresh failed; G11 cached FRED API docs show release calendar, release endpoints, series observations, series updates, and vintage-date endpoint concepts. | For economic releases, use FRED release/vintage timestamp or ALFRED vintage availability, plus cache time/hash. For daily market/rate series, same-day intraday joins are blocked unless an update timestamp proves availability before the decision; otherwise use a conservative next-day availability rule. | Revised values and daily close values can leak into intraday decisions. A FRED observation date is not a publication/as-of timestamp. | `HYP-G7-XG8-VOL-MACRO-011`, `HYP-G7-XG11-SOURCE-FRESH-012`, `HYP-G11-PUBLIC-LAG-004`. | `validation_safe=false`; G7 has no raw FRED cache; normalized point-in-time cache and vintage tests missing. |
| BIS macro / global liquidity | G7 cached BIS statistics index; G11 cached BIS Data Portal with release-calendar data embedded and public releases link. | Exact BIS dataflow/table/series must be selected first. Use BIS `release_date` plus revision/vintage state and cache time/hash. If only a date is available, no same-day intraday GTOS decision may use it; first eligible decision is after the full release date has passed unless exact timestamp is proven. | BIS date-only or revised series can leak slow macro state into historical decisions. Broad table selection can create post-hoc source mining. | `HYP-G7-XG11-SOURCE-FRESH-012`, `HYP-G11-PUBLIC-LAG-004`, macro side of `HYP-G7-XG8-VOL-MACRO-011`. | `validation_safe=false`; exact table, SDMX/bulk parser, release/vintage rule, and no-lookahead tests missing. |
| Cboe public volatility-index CSVs | G8 cached VIX, VIX1D, VIX9D, GVZ, VVIX, VIX3M CSVs with date/OHLC columns through `2026-05-05`; source index says publication timestamp unknown. | Treat daily CSV rows as unavailable for same-day intraday decisions until Cboe publication timing is documented. Conservative default: first usable at the next US exchange business day 00:00 America/New_York, then gated by cache time/hash. | Same-day VIX1D/VIX9D/GVZ/VIX rows can leak daily close values into earlier M15/H1 decisions. License and parser state are unresolved. | Vol side of `HYP-G7-XG8-VOL-MACRO-011`, implied input for `HYP-G8-VRP-004`, G11 options/vol source gate. | `validation_safe=false`; license review, publication timestamp, parser, source-registry, and no-lookahead join tests missing. |
| VRP implied-minus-realized construction | G8 `HYP-G8-VRP-004` and source contract `SRC-G8-VRP-FORMULA-005` define only a candidate formula family; no derived VRP cache exists. | Implied-vol component must pass the Cboe as-of rule above. Realized-variance window must end strictly before `candidate_decision_timestamp_utc`; it cannot include the decision bar, later bars, or same-day daily close unknown at decision time. Annualization and tenor mapping must be frozen before any outcome review. | Realized variance can silently include future bars; implied source timing can leak daily closes; formula selection after outcomes would be data mining. | `HYP-G8-VRP-004`, vol side of `HYP-G7-XG8-VOL-MACRO-011`. | `validation_safe=false`; formula, tenor, annualization, realized estimator, implied source as-of, and parser tests missing. |
| G11 source-freshness governance | G11 source contracts include `SRC-G11-PUBLIC-CFTC-FRED-BIS` and `SRC-G11-CBOE-OPTIONS-VOL`; all are validation-safe false. | G11 compatibility checks are source-governance labels only: source ID, source version, legal state, publication timestamp rule, cache path/hash, parser version, no-lookahead test status, and decision-time eligibility. | G11 no-leak fields currently contain forbidden outcome/future fields in several rows; G0 flagged this for red-team cleanup. | `HYP-G7-XG11-SOURCE-FRESH-012`, `HYP-G11-PUBLIC-LAG-004`, CD2-01 as a whole. | `validation_safe=false`; G11 field semantics need cleanup before any master-row edit. |
| G1 validation-control gate | G1 `SCI-G1-HYP-004` and `SCI-G1-EXP-004` require 100% no-leak source-contract pass before outcome review. | CD2-01 must treat source-freshness ledger rows as `context_only` or `observation_only` until every source passes source-contract tests. | Passing a timestamp check does not prove semantic availability if source publication convention is wrong. | All four seed rows. | Validation gate only; no outcome review opened. |

## Seed-Row Compatibility Conclusions

| Seed row | CD2-01 compatibility decision |
|---|---|
| `HYP-G7-XG8-VOL-MACRO-011` | Replace the old "blocked until G8 commits rows" placeholder with "blocked until both G7 macro source rows and G8 volatility rows pass this publication/as-of ledger." Interaction cohorts may be preregistered, but no outcome review can open while FRED/BIS/COT/Cboe source timing is unresolved. |
| `HYP-G7-XG11-SOURCE-FRESH-012` | Now compatible as a source-governance audit using actual G11 rows, not `future_G11_source_governance_rows`. The metric remains retained/excluded source-row counts and blocker taxonomy only. No trade outcomes or path-R labels are permitted. |
| `HYP-G11-PUBLIC-LAG-004` | Mechanism is essential for CD2-01, but the current `no_leak_fields` list is semantically wrong because it lists forbidden outcome/future fields. Proposed replacement is in the prereg update proposal; master registry must not be edited by G7. |
| `HYP-G8-VRP-004` | Compatible only as formula/source audit. Cboe daily CSV rows and realized variance can feed a future VRP context row only after implied-source as-of timing, realized-window boundaries, tenor mapping, annualization, parser, cache, and no-lookahead tests are frozen. |

## Frozen Exclusion Buckets

Future CD2-01 source-freshness audits should classify every rejected row into exactly one primary exclusion bucket:

| Exclusion bucket | Definition |
|---|---|
| `OBSERVATION_DATE_ONLY` | Source row has a report/observation date but no release/as-of timestamp. |
| `SOURCE_RELEASE_AFTER_DECISION` | Publication/as-of timestamp is later than the GTOS decision timestamp. |
| `CACHE_AFTER_DECISION` | Raw or normalized cache was created after the decision and no independent historical as-of proof exists. |
| `VINTAGE_OR_REVISION_MISSING` | FRED/BIS or similar series may revise and no vintage/realtime rule is present. |
| `CBOE_DAILY_SAME_DAY_BLOCKED` | Cboe daily volatility-index row is being joined to same-day intraday decisions without proven publication time. |
| `VRP_REALIZED_WINDOW_OVERLAP` | Realized-variance window includes the decision bar or later bars. |
| `SOURCE_ID_UNRESOLVED` | Source ID is a placeholder, literature reference, or non-`source_contract_v2` reference. |
| `LEGAL_OR_LICENSE_UNRESOLVED` | Source terms, paid status, scraping/API rights, or redistribution/use rights are unresolved. |
| `PARSER_OR_HASH_MISSING` | Parser version, raw cache path, cache hash, or normalized row manifest is missing. |

## Required Tests Before Any Outcome Review

These are proposal gates only; this ledger does not implement them.

| Gate | Required proof |
|---|---|
| Parser determinism | Raw cache path, source hash, parser version, schema version, and normalized row count are stable. |
| Publication/as-of join | Every normalized source row has `source_publication_timestamp_utc`, `source_cache_time_utc`, `feature_asof_utc`, and `decision_timestamp_utc`; all eligible rows satisfy the universal as-of rule. |
| Revision/vintage handling | FRED/BIS rows use release/vintage metadata; revised values are never joined as if available historically. |
| Cboe same-day safety | Either official Cboe publication timing is documented and tested, or same-day intraday rows stay blocked by the conservative next-business-day rule. |
| VRP no-lookahead | Realized-variance windows end strictly before decision time; implied-vol rows satisfy Cboe as-of rules; formula and annualization are frozen before outcomes. |
| Source contract status | All source contracts remain `validation_safe=false` until the above tests pass and a G0/G12 review explicitly clears blockers. |

## Non-Actions

- No source contract was marked `validation_safe=true`.
- No experiment prereg `outcome_review_opened` value was changed.
- No master registry, source registry, or goal-status registry was edited.
- No validation result, performance number, source promotion, live trading prompt change, risk change, execution change, permission/safety-gate change, selector change, MT5 call, canary call, paid data call, credential change, remote push, or order-behavior change was made.

## NO_PROMOTION_VERDICT

CD2-01 remains source-governance research only. All four seed rows stay blocked from validation and promotion until parser/cache/no-lookahead/source-contract tests exist and a separate G0/G12-controlled registry update or promotion dossier is explicitly authorized.
