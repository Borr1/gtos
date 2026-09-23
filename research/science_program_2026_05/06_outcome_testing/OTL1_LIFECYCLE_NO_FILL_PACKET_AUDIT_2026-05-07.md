# OTL1 Lifecycle/No-Fill Packet Audit - 2026-05-07

**Lane:** `OTL1`  
**Scope:** lifecycle/no-fill existing-data packet audit only  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Outcome tests run:** `false`  
**R/result values read:** `false`  
**Final audit status:** `COMPLETE_ALL_10_PACKETS_BLOCKED_WITH_EXACT_FIELDS`

## Objective Restated

Audit the `10` OTG0 lifecycle/no-fill existing-data packets from `OTG0_FROZEN_COHORT_PACKET_MANIFEST_2026-05-07.json` before any outcome implementation. The audit must verify packet file existence, lifecycle state readiness, fill/no-fill denominator rules, cancel/expiry/wrong-side reason coverage, `decision_asof_utc`, `source_capture_utc`, `duplicate_group_id`, no-leak fields, label-family separation, source contracts, stale context, missing fields, and hidden assumptions.

This is a packet-readiness audit. It does not run lifecycle outcome tests, replay outcomes, inspect R values, open result files, change source validation flags, or touch live trading behavior.

## Evidence Read

Mandatory GTOS preflight was completed:

- Ran `python scripts/generate_live_state.py`.
- Read `.context/LIVE_STATE.md`, latest handoff `SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md`, `.context/00_core/quick_reference_card.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/research_current_state.md`, and `.context/00_READING_ORDER.md`.
- Verified branch `otl1-lifecycle`.

Controlling OTG0/G12 inputs read:

- `OTG0_FROZEN_COHORT_PACKET_MANIFEST_2026-05-07.json` / `.md`
- `OTG0_OUTCOME_TESTING_CONTROL_RULES_2026-05-07.md`
- `OTG0_PREREG_CLASSIFICATION_LEDGER_2026-05-07.json` / `.md`
- `OTG0_FOLLOWUP_GOAL_PROMPTS_2026-05-07.md`
- `G0_G12_OWNER_FULL_RESEARCH_REVIEW_2026-05-06.md`
- `G12_RED_TEAM_REVIEW_2026-05-06.md`
- `G12_SOURCE_VALIDITY_REVIEW_2026-05-06.md`
- `G12_LABEL_SEPARATION_REVIEW_2026-05-06.md`
- `G12_DUPLICATE_COUNTING_REVIEW_2026-05-06.md`

Lifecycle/source/shadow artifacts inspected for file existence, schemas, row counts, field names, and lifecycle-state metadata only:

- `SOURCE_CONTRACT_REGISTRY_2026-05-06.json`
- `RAW_OHLC_PREFILL_DELIVERY_PATH_COVERAGE_2026-05-03.json`
- `PREFILL_DELIVERY_PATH_CAPTURE_READINESS_2026-05-04.json`
- `G10_CD2_06_PREFILL_PATH_MISSING_FIELD_AUDIT_2026-05-06.md`
- `G8_CD2_02_SHORT_VOL_EXECUTION_MISSING_SOURCE_LEDGER_2026-05-06.md`
- `PENDING_LIMIT_LIFECYCLE_FORWARD_STATUS_2026-05-04.json`
- `BROKER_R_RECONCILIATION_COVERAGE_2026-05-05.json`
- `COST_SLIPPAGE_EXIT_ACCOUNTING_COVERAGE_2026-05-05.json`
- `shadow_logs/pending_limit_lifecycle*.jsonl`
- `shadow_logs/prefill_delivery_path*.jsonl`
- `shadow_logs/opportunity_lifecycle_audit.jsonl`
- `shadow_logs/trade_index_lifecycle_audit.jsonl`
- `shadow_logs/slippage.jsonl`
- `shadow_logs/shadow_observer*.jsonl`
- `data/news_calendar.json`
- cached G7/G8 raw source files under `research/science_program_2026_05/01_domain_syntheses/raw/`

## Global Verdict

No OTL1 packet is ready for test implementation. All `10/10` packets are `BLOCKED_WITH_EXACT_FIELDS`.

The frozen manifest is valid as a control artifact, but it is not a concrete row packet. All `10` packet `result_quarantine_path` directories are absent, which is expected because no result lane has opened. The current candidate/lifecycle/shadow logs are useful source evidence, but they do not provide a packet-specific table with every OTL1 required field under exact names and with source/as-of/duplicate/label boundaries proven before outcome review.

## Cross-Packet Blockers

| Blocker | Evidence | Required resolution |
|---|---|---|
| Packet row files absent | All `10` OTL1 `result_quarantine_path` directories are absent. Existing evidence lives in generic shadow/research logs, not packet-specific frozen row files. | Build packet-specific pre-outcome row files or a deterministic packet builder that emits the exact required fields without opening result metrics. |
| Exact OTL1 field contract not met | Existing logs use aliases such as `candidate_id`, `decision_time_utc`, `asof_cutoff_utc`, `created_at_utc`, `pending_created_time_utc`, `fill_no_fill_label`, `cancel_reason`, `opportunity_id`, and `source_dependency_signature`. They do not expose the full exact class contract: `setup_id_or_candidate_id`, `decision_asof_utc`, `source_capture_utc`, `pending_created_utc_if_applicable`, `lifecycle_event_id`, `lifecycle_state`, `fill_or_no_fill_state`, `cancel_expiry_or_wrong_side_reason`, and `duplicate_group_id` in one packet table. | Add a strict packet schema or mapping layer with explicit alias-to-contract tests. |
| Source contracts remain validation-unsafe | G12 source review reports `86` source contracts and `0` `validation_safe=true`; this audit did not flip any source. | Keep `validation_safe=false`; require source-specific legal/cache/parser/publication/as-of/no-lookahead dossiers before any validation use. |
| Label-family drift risk | `pending_limit_lifecycle.jsonl` contains `actual_r` and `synthetic_path_r` field names, and `trade_index_lifecycle_audit.jsonl` contains `actual_r`. This audit did not inspect values, but field presence means these files cannot be consumed as primary lifecycle packets without exclusion or separation. | OTL1 packet builder must drop or physically separate `broker_actual_r`, `synthetic_path_r`, `win_loss`, and `outcome_r` from primary lifecycle rows. |
| Duplicate denominator not packet-safe | `opportunity_lifecycle_audit.jsonl` gives duplicate-state evidence, but no packet exposes `duplicate_group_id`. G12 also warns CD2-06 raw counts are not inference-safe. | Emit stable `duplicate_group_id` and independent-unit status for every row; report raw rows, child rows, countable rows, and effective-N separately. |
| Lifecycle reason taxonomy is not normalized | Some files provide `fill_no_fill_label`, `broker_fill_state`, `cancel_reason`, `wrong_side_abort`, `pending_limit_final_state`, or complex `fill_state`; none provides the required `fill_or_no_fill_state` plus `cancel_expiry_or_wrong_side_reason` consistently. | Define and test one lifecycle taxonomy covering filled, still pending, cancelled, expired, wrong-side, tick-missing, same-bar/path ambiguity, and unresolved states. |
| Stale/source path assumptions remain | `.context/LIVE_STATE.md` flagged `research_current_state.md` stale versus `edb04ba6`. The G5 source contract references `data/news/forexfactory_calendar.json`, which is absent; the actual configured file is `data/news_calendar.json`. | Use direct artifacts, update research state, and repair source-contract path mismatch before any G5/G7 packet use. |

## Source And Schema Observations

| Evidence | Audit observation |
|---|---|
| `shadow_logs/pending_limit_lifecycle.jsonl` | `174` rows. Lifecycle labels exist: `no_fill_still_pending=167`, `no_fill_cancelled=4`, `no_fill_cancelled_wrong_side=3`. Exact required packet fields present only for `symbol`, `session`, and `side`; required timestamp/identity/duplicate fields are missing under exact names. `actual_r` and `synthetic_path_r` field names are present and must be excluded from primary lifecycle packets. |
| `shadow_logs/pending_limit_lifecycle_audit.jsonl` | `49` rows. `final_state` shows `PENDING_LIFECYCLE_GROUP_MISSING=41`, `NO_FILL_STILL_PENDING=5`, `NO_FILL_CANCELLED_WRONG_SIDE=2`, `NO_FILL_CANCELLED_SYSTEM_OR_MANUAL=1`. Useful blocker evidence, not a ready packet. |
| `shadow_logs/prefill_delivery_path.jsonl` | `86` rows. Decision-time rows have `candidate_id`, `decision_time_utc`, `asof_cutoff_utc`, `original_poi_bounds`, and `cancel_expiry_abort_reason`. They lack `source_hash`, `source_symbol`, exact `source_capture_utc`, exact lifecycle fields, and `trade_id` for most rows. |
| `shadow_logs/prefill_delivery_path_audit.jsonl` | `1454` rows. Duplicate-aware status exists, but current evidence is duplicate-heavy: `DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE=1111`, `COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY=286`, `BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP=56`. This supports blocker documentation, not inference. |
| `RAW_OHLC_PREFILL_DELIVERY_PATH_COVERAGE_2026-05-03.json` | Coverage-only report. `12831` reconstructed rows, `0` rows with broker lifecycle state, `0` rows with original POI bounds, and explicit missing fields: `original_poi_type_and_bounds`, `broker_pending_lifecycle_state`, `true_pending_limit_created_utc`, `intrabar_order_inside_fill_row`. |
| `G10_CD2_06_PREFILL_PATH_MISSING_FIELD_AUDIT_2026-05-06.md` | Already records CD2-06 blockers: missing `source_hash`, `source_symbol`, ordered prefill candles/ticks, pending/native broker fields, spread/tick, and most trade IDs. Current OTL1 evidence agrees. |
| `data/news_calendar.json` | Exists with `updated_at=2026-05-01T00:30:00Z` and `29` events. The source contract path `data/news/forexfactory_calendar.json` is absent, so G5/G7 packet implementation would be using a path mismatch unless corrected. |
| `SRC-G7-FED-FOMC-001` cache | `fed_fomc_calendars.html` exists, but source contract still blocks parser, stale-source tests, frozen event-window cohort labels, and surprise/text fields. |
| `SRC-G8-CBOE-VOL-CSV-001` cache | Cboe CSV files exist for VIX, VIX1D, VIX9D, VIX3M, GVZ, and VVIX, but publication timing, parser tests, legal review, and no-lookahead joins remain blocked. |

## Packet Decisions

| Packet | Experiment | Decision | Exact blocker fields or questions |
|---|---|---|---|
| `OTG0-PKT-011` | `G10-EXP-PREFILL-003` | `BLOCKED_WITH_EXACT_FIELDS` | Existing prefill and pending logs are useful but not a packet. Missing or non-normalized: `setup_id_or_candidate_id`, `decision_asof_utc`, `source_capture_utc`, `lifecycle_event_id`, `fill_or_no_fill_state`, `cancel_expiry_or_wrong_side_reason`, `duplicate_group_id`, source hashes, source symbols, ordered prefill candles/ticks, pending/native broker state, spread/tick at arm/trigger, and most `trade_id` joins. Historical coverage has `0` broker lifecycle rows and `0` original POI-bound rows. |
| `OTG0-PKT-016` | `EXP-G11-FRICTION-GATE-007` | `BLOCKED_WITH_EXACT_FIELDS` | No registered source contract in the frozen packet. G11 no-leak fields are semantic-inversion blockers (`future_return`, `actual_r`, `post_entry_path`, `trade_result`). Need a concrete source contract/cache, decision-time friction fields, allowed as-of no-leak whitelist, duplicate group, lifecycle denominator, and exact packet fields. |
| `OTG0-PKT-017` | `EXP-G11-OBSERVER-EXPANSION-006` | `BLOCKED_WITH_EXACT_FIELDS` | No registered source contract in the frozen packet. G11 no-leak fields are forbidden outcome/post-signal names (`actual_r`, `win_loss`, `post_signal_path`, `tp_sl_hit`). Existing `shadow_observer_status` rows are observer status, not lifecycle packets, and lack required `session`, `side`, exact as-of/source-capture, lifecycle, and duplicate fields. |
| `OTG0-PKT-025` | `EXP-G2-GARCH-LIFECYCLE-002` | `BLOCKED_WITH_EXACT_FIELDS` | No registered source contract in the frozen packet. Current `session_volatility_log.csv` has only session-volatility context and no candidate lifecycle join packet. Need source contract for realized-vol and vol-of-vol fields, `realized_vol_*_asof` features, exact lifecycle fields, duplicate group, and source/as-of proof. |
| `OTG0-PKT-029` | `EXP-G2-SURVIVAL-PATH-006` | `BLOCKED_WITH_EXACT_FIELDS` | No registered source contract in the frozen packet. Current lifecycle logs contain partial aliases but not cause-specific survival packet rows. Need normalized event-time fields, censoring state, exact `pending_created_utc_if_applicable`, `lifecycle_event_id`, `fill_or_no_fill_state`, `cancel_expiry_or_wrong_side_reason`, `duplicate_group_id`, and source-capture proof. |
| `OTG0-PKT-045` | `EXP-G4-XAUUSD-FOOTPRINT-ABSORB-003` | `BLOCKED_WITH_EXACT_FIELDS` | No registered source contract in the frozen packet. Current G4/orderflow artifacts are source-status and context only; packet needs XAUUSD footprint/absorption source contract, predecision flow fields, source hash/symbol, POI bounds, lifecycle truth, and label-family separation from broker actual-R. |
| `OTG0-PKT-055` | `EXP-G5-NEWS-005` | `BLOCKED_WITH_EXACT_FIELDS` | One local calendar source contract exists, but its path is stale: `data/news/forexfactory_calendar.json` is absent while configured `data/news_calendar.json` exists. Unresolved `LIT-G5-*` refs remain. Need source-path cleanup, event/source cache timestamps, event IDs/window classes, stale-calendar rule, matched-control duplicate groups, and exact lifecycle packet rows. |
| `OTG0-PKT-059` | `EXP-G5-XG7-MACRO-ATTN-009` | `BLOCKED_WITH_EXACT_FIELDS` | Same G5 calendar path mismatch and unresolved `LIT-G5-*` refs as `OTG0-PKT-055`. Also needs G7 macro labels committed before outcome review, a canonical G5/G7 interaction denominator, event/month clustering, and exact lifecycle packet rows. |
| `OTG0-PKT-071` | `EXP-G7-FOMC-ATTN-003` | `BLOCKED_WITH_EXACT_FIELDS` | Fed/FOMC cached HTML exists, but parser, stale-source tests, frozen event-window labels, and no-lookahead checks are missing. The G5 local calendar source path mismatch also affects this packet. Need `event_id`, `event_time_utc`, `event_source_cache_time_utc`, `window_class`, `source_capture_utc`, exact lifecycle labels, and duplicate/event-cluster IDs. |
| `OTG0-PKT-079` | `EXP-G8-CD2-02-SHORTVOL-LIFECYCLE-001` | `BLOCKED_WITH_EXACT_FIELDS` | Cboe raw CSVs exist, but publication-as-of, parser/cache hashes, legal review, and no-lookahead tests are unresolved. Current lifecycle rows are not normalized to the required packet schema and do not expose `duplicate_group_id`. This packet shares hypothesis family `HYP-G8-VIX1D9D-STRESS-002` with `EXP-G8-VIX1D9D-STRESS-002`, so denominator policy must prevent duplicate route counting. |

## Required Next Questions

1. What packet builder will emit one OTL1 row table per experiment with the exact class-required field names?
2. Which source-specific cleanup lane resolves `data/news/forexfactory_calendar.json` versus `data/news_calendar.json` without changing live news-filter behavior?
3. Which G11 cleanup artifact replaces forbidden outcome/post-signal `no_leak_fields` with allowed as-of feature names?
4. What canonical lifecycle taxonomy maps existing aliases into `lifecycle_state`, `fill_or_no_fill_state`, and `cancel_expiry_or_wrong_side_reason`?
5. What duplicate policy emits stable `duplicate_group_id` across setup, pending-intent, event-window, and child-attempt rows?
6. For `EXP-G8-CD2-02-SHORTVOL-LIFECYCLE-001`, what source dossier proves Cboe VIX1D/VIX9D daily rows were available before each candidate decision?
7. For prefill/path packets, where will ordered M1/tick sequences, source hashes, source symbols, and pending/native broker-state fields be stored?

## Prompt-To-Artifact Completion Checklist

| Requirement | Evidence | Status |
|---|---|---|
| Run from `C:\tmp\gtos_otl\OTL1` on branch `otl1-lifecycle` | `git status --short --branch` reported `## otl1-lifecycle`. | `DONE` |
| Complete mandatory GTOS preflight | `generate_live_state.py` succeeded; mandatory context files and latest handoff were read. | `DONE` |
| Use named OTG0/G12 controlling inputs | Listed in Evidence Read section; packet extraction came from the frozen manifest JSON. | `DONE` |
| Audit all `10` lifecycle/no-fill packets | Packet Decisions table covers `OTG0-PKT-011`, `016`, `017`, `025`, `029`, `045`, `055`, `059`, `071`, and `079`. | `DONE` |
| Do not run outcome tests | No replay/test implementation command was run; only file/schema/source inspection commands were used. | `DONE` |
| Do not read R results | This audit inspected field names and label-boundary presence only; it did not inspect or report R values. | `DONE` |
| Lifecycle state and fill/no-fill denominator | Reviewed pending/pre-fill/opportunity lifecycle schema and G12 duplicate review; all packets remain blocked until normalized lifecycle and duplicate fields exist. | `DONE` |
| Cancel/expiry/wrong-side reason | Reviewed existing aliases and documented missing normalized `cancel_expiry_or_wrong_side_reason`. | `DONE` |
| `decision_asof_utc` and `source_capture_utc` | Existing aliases exist but exact required packet fields are absent; listed as blockers. | `DONE` |
| `duplicate_group_id` | No packet-ready duplicate field exists; duplicate policy blockers listed. | `DONE` |
| No-leak fields | G11 semantic inversion and cross-packet as-of field gaps recorded. | `DONE` |
| Label-family separation | Primary lifecycle packet cannot consume files containing R fields without exclusion/separation; blockers recorded. | `DONE` |
| Source contracts and stale context | Source registry, G12 source review, cached source files, and G5 path mismatch inspected; blockers recorded. | `DONE` |
| Packet file existence | All `10` quarantine packet paths checked and absent; existing logs classified as source evidence, not ready packets. | `DONE` |
| Stop only after each packet is ready or blocked | All `10` packets are `BLOCKED_WITH_EXACT_FIELDS`; `0` packets are pass-ready. | `DONE` |

## Final Status

`OTL1` packet audit is complete. The correct next lane is blocker clearing, not outcome implementation. No lifecycle/no-fill packet may advance to quarantined result testing until its exact fields, source/as-of contract, duplicate denominator, no-leak whitelist, and label-family separation are proven in a packet-specific artifact.

