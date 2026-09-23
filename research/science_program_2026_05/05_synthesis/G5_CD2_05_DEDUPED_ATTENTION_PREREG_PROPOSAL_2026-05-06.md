# G5 CD2-05 Deduped Attention Prereg Proposal - 2026-05-06

**Owner lane:** `G5`  
**Assignment:** `CD2-05 - Macro attention and behavioral attention interaction`  
**Status:** `G5_OWNED_PROPOSAL_ONLY_NOT_MASTER_REGISTRY_EDIT`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Scope

This artifact resolves the duplicated macro/news attention preregistration shape created by these rows:

- `HYP-G7-XG5-MACRO-ATTN-010`
- `HYP-G5-XG7-MACRO-ATTN-009`
- `HYP-G7-FOMC-ATTN-003`
- `HYP-G5-NEWS-005`

It is a G5-owned proposal only. It does not edit the master mechanism, hypothesis, prereg, source, or status registries. It does not change the live news filter, live trading prompts, risk, execution, permissions, safety gates, selectors, MT5, canaries, paid data, credentials, remote state, or order behavior.

## Controlling Inputs Read

- `research/science_program_2026_05/04_goal_prompts/G5_G5_BEHAVIORAL_GAME_GOAL_PROMPT_2026-05-06.md`
- `research/science_program_2026_05/05_synthesis/G0_CROSS_DOMAIN_SECOND_PASS_ASSIGNMENTS_2026-05-06.md`
- `research/science_program_2026_05/05_synthesis/SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.md`
- `research/science_program_2026_05/05_synthesis/G0_WAVE2_RECONCILIATION_2026-05-06.md`
- G5 source/hypothesis/prereg/synthesis artifacts for `HYP-G5-NEWS-005` and `HYP-G5-XG7-MACRO-ATTN-009`
- G7 source/hypothesis/prereg/synthesis artifacts for `HYP-G7-FOMC-ATTN-003` and `HYP-G7-XG5-MACRO-ATTN-010`
- G1 validation/statistics artifacts for label separation, duplicate policy, effective-N, DSR/PBO limits, and no-leak source-contract gates

## Duplicate Resolution

The two cross-domain rows are duplicates at the prereg level:

| Existing row | Lane intent | CD2-05 resolution |
| --- | --- | --- |
| `HYP-G5-XG7-MACRO-ATTN-009` | G5 asks whether G7 macro regimes interact with G5 attention/news labels. | Superseded by one G5-owned lifecycle-only interaction prereg proposal. |
| `HYP-G7-XG5-MACRO-ATTN-010` | G7 asks whether macro event labels interact with G5 attention labels. | Superseded by the same proposed interaction prereg; keep as upstream dependency evidence. |
| `HYP-G5-NEWS-005` | G5 local high-impact news/event attention window. | Parent source/cohort row for local calendar and stale-calendar handling. |
| `HYP-G7-FOMC-ATTN-003` | G7 Fed/FOMC scheduled macro event windows. | Parent source/cohort row for official Fed event-window handling. |

Proposed canonical ID for future G0/G12 review:

- Hypothesis proposal: `HYP-G5-CD2-05-MACRO-BEHAVIORAL-ATTN-001`
- Experiment proposal: `EXP-G5-CD2-05-MACRO-BEHAVIORAL-ATTN-001`

These IDs are not inserted into any registry by this pass.

## Proposed Hypothesis Contract

| Field | Proposed value |
| --- | --- |
| `hypothesis_id` | `HYP-G5-CD2-05-MACRO-BEHAVIORAL-ATTN-001` |
| `mechanism_id` | `G5-MECH-NEWSATTN-005` plus G7 parent mechanism `G7-MECH-FOMC-ATTENTION-002` as dependency evidence |
| `null` | Scheduled macro/FOMC event windows and G5 behavioral/news attention labels do not change GTOS lifecycle/no-fill states versus matched non-event controls after stale-calendar and event-publication gates. |
| `alternative` | Source-safe macro event windows with source-safe G5 attention/news labels have different lifecycle/no-fill or pending-intent resolution behavior than macro-only, attention-only, and matched non-event controls. Direction is intentionally not pre-claimed. |
| `symbols` | `XAUUSD`, `XAGUSD`, `NAS100`, `US30`, `GBPUSD`, `USDJPY`, `GBPJPY` when each symbol has the required lifecycle rows and source-safe event labels. |
| `timeframes` | `M15`, `H1`, predeclared event windows. |
| `entry_or_filter_or_exit_role` | `cross_domain_research_context_only` |
| `label_class` | `lifecycle_no_fill` |
| `no_leak_fields` | `decision_timestamp_utc`, `event_time_utc`, `event_source_cache_time_utc`, `calendar_updated_at_utc`, `event_publication_timestamp_utc`, `event_window_class`, `source_hash`, `attention_source_timestamp_utc`, `source_freshness_state_asof` |
| `sample_floor` | At least `150` event-window lifecycle observations and `150` matched non-event lifecycle observations after duplicate clustering, stale-calendar exclusion, and source-contract clearance. Report effective-N by event cluster, symbol, session, month, and attention-window group before interpreting any direction. |
| `test_method` | Freeze source-safe event labels before outcome review; join only decision-time labels to GTOS candidate/pending lifecycle rows; compare macro-only, attention-only, macro-plus-attention, and matched controls using lifecycle/no-fill states only. |
| `promotion_blockers` | All source contracts remain `validation_safe=false`; local calendar path/freshness must be resolved; official Fed parser/stale-source tests are missing; no post-release surprise source is contracted; G5 attention proxy sources are not validation-safe; live news filter must remain untouched. |
| `promotion_verdict` | `NO_PROMOTION_VERDICT` |

## Proposed Experiment Prereg Contract

| Field | Proposed value |
| --- | --- |
| `experiment_id` | `EXP-G5-CD2-05-MACRO-BEHAVIORAL-ATTN-001` |
| `hypothesis_id` | `HYP-G5-CD2-05-MACRO-BEHAVIORAL-ATTN-001` |
| `frozen_at_utc` | `2026-05-06T09:33:02Z` |
| `outcome_review_opened` | `false` |
| `metric` | Primary: lifecycle/no-fill state distribution and pending-intent resolution rate by event-window class. Secondary descriptive fields may include cancellation/expiry/touch ordering only if already lifecycle labels, not R outcomes. |
| `cohort` | Future GTOS candidate or pending-intent lifecycle rows with source-safe scheduled macro/event labels and source-safe G5 attention/news labels available at or before `decision_timestamp_utc`. |
| `exclusions` | Calendar file missing; source contract path mismatch unresolved; calendar `updated_at` or source cache timestamp after decision; calendar stale beyond the predeclared threshold at decision time; event added or modified after decision without as-of proof; rows using actual/forecast/surprise/revision/text/minutes fields without a separate source contract; rows without stable `setup_id`, `event_id`, `source_hash`, or lifecycle label; matched controls inside another high-impact event window. |
| `duplicate_policy` | One countable lifecycle observation per `setup_id` x `event_id` x `event_window_class` x `symbol` x UTC date. Cluster repeated rows by `event_id`, `attention_window_id`, symbol, session, and month for sample-floor and effective-N reporting. Keep earliest decision row in each duplicate cluster. |
| `cost_slippage_assumptions` | Lifecycle-only research. No order, risk, live news-filter, execution, prompt, permissions, safety-gate, selector, MT5, canary, paid-data, or credential behavior changes. Cost/slippage and R labels are out of scope unless a separate prereg is frozen. |
| `dsr_pbo_effective_n_policy` | DSR/PBO are `not_applicable_lifecycle_only` for this proposal. Effective-N and concentration are mandatory descriptive blockers. Any future synthetic path-R or broker actual-R extension requires a separate prereg, frozen variant ledger, and G1 promotion-statistics gates. |
| `label_separation_policy` | `macro_event_context`, `g5_attention_context`, `lifecycle_no_fill`, `synthetic_path_r`, and `broker_actual_r` must remain separate. This proposal may not pool lifecycle/no-fill rows with executed trade performance or synthetic path-R. |
| `reproducibility_key` | `EXP-G5-CD2-05-MACRO-BEHAVIORAL-ATTN-001|parents=HYP-G5-NEWS-005,HYP-G7-FOMC-ATTN-003,HYP-G5-XG7-MACRO-ATTN-009,HYP-G7-XG5-MACRO-ATTN-010|frozen=2026-05-06T09:33:02Z` |
| `promotion_verdict` | `NO_PROMOTION_VERDICT` |

## Event-Window Gate

The deduped prereg should use window labels only after the source gates below pass:

| Window class | Proposed definition | Allowed use |
| --- | --- | --- |
| `macro_anticipation` | `event_time_utc - 120m <= decision_timestamp_utc < event_time_utc - 15m` | Lifecycle context only. |
| `live_filter_block_window` | `event_time_utc - 15m <= decision_timestamp_utc <= event_time_utc + 2m` | Lifecycle context only; no change to the current live filter. |
| `post_release_digest` | `event_time_utc + 2m < decision_timestamp_utc <= event_time_utc + 60m` | Lifecycle context only; no surprise/text/minutes fields unless separately source-contracted and publication-safe. |
| `matched_non_event` | Same symbol/session/month/day-of-week class, with no high-impact mapped event in the surrounding event window. | Control lifecycle context only. |

These windows are research labels, not a no-trade recommendation and not a live filter proposal.

## Stale-Calendar Gate

Before any outcome review opens, each event label must prove:

1. `event_time_utc`, event name, currency, impact, source path, source hash, and source cache timestamp are recorded.
2. `event_source_cache_time_utc <= decision_timestamp_utc`.
3. Local calendar `updated_at` is present and not after the decision.
4. Calendar age at decision time is within the predeclared stale threshold, or the row is excluded from the primary cohort and counted only in a stale-source diagnostic.
5. Event additions or modifications after the decision are excluded unless an earlier cache proves the same event label existed as-of the decision.
6. Source-contract cache paths resolve to real files before rows can become validation-safe.

Current local evidence remains blocker-level only: `data/news_calendar.json` exists with `updated_at=2026-05-01T00:30:00Z`, `29` events, and SHA256 `569EE7742E395740DF0E5DDCBF3FCEAD19BF26CA2B93ED55D004BFAA263B105D`; however the existing source-contract row references `data/news/forexfactory_calendar.json`, which is not present in this worktree.

## Event-Publication Gate

The lifecycle-only prereg may use scheduled event metadata only:

- event name
- event time
- currency
- impact level
- source/cache timestamp
- source hash
- event-window class

It may not use the following unless a separate source contract, parser, cache, publication timestamp, and no-lookahead test are added:

- actual/forecast/previous values
- surprise fields
- revised data
- FOMC statement, minutes, press-conference text, or sentiment
- post-release news narrative labels
- realized volatility or outcome-derived event severity

## Proposed Master-Registry Cleanup For Later G0/G12 Review

Do not edit registries in this pass. If G0/G12 later accepts the proposal, the intended cleanup is:

1. Keep `HYP-G5-NEWS-005` and `HYP-G7-FOMC-ATTN-003` as parent source/cohort contracts.
2. Replace the two duplicated interaction preregs, `EXP-G5-XG7-MACRO-ATTN-009` and `EXP-G7-XG5-MACRO-ATTN-010`, with one canonical CD2-05 interaction prereg.
3. Move `HYP-G5-XG7-MACRO-ATTN-009` out of any `source_ids` list and into a neighbor-dependency or evidence-reference field.
4. Keep all relevant source contracts `validation_safe=false` until parser/cache/no-lookahead tests pass.

## Final Boundary

This proposal is a research-control artifact only. It produces no validation result, no promotion, no source-safe feature, and no live trading change.

Promotion verdict: `NO_PROMOTION_VERDICT`
